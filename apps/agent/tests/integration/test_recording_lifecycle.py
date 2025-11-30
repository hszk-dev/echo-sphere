"""End-to-end tests for the recording lifecycle.

Tests the full recording flow from start to completion/failure,
integrating the service layer, repository, and API endpoints.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.adapters.outbound.postgres_recording import PostgresRecordingRepository
from src.application.ports import EgressInfo
from src.application.ports import EgressStatus
from src.application.ports import ObjectInfo
from src.application.use_cases import RecordingService
from src.domain.entities import RecordingStatus


class TestSuccessfulRecordingLifecycle:
    """Tests for successful recording flow: Start -> Active -> Complete."""

    @pytest.mark.asyncio
    async def test_full_recording_lifecycle(
        self,
        recording_service: RecordingService,
        recording_repository: PostgresRecordingRepository,
        mock_egress_port: AsyncMock,
        mock_storage_port: AsyncMock,
    ) -> None:
        """Complete lifecycle: start -> activate -> process -> complete.

        This test simulates the full recording flow:
        1. Start recording (creates STARTING recording)
        2. Receive egress_started webhook (transitions to ACTIVE)
        3. Stop recording (transitions to PROCESSING)
        4. Receive egress_ended webhook (transitions to COMPLETED)
        """
        session_id = uuid4()
        egress_id = "egress-lifecycle-test"

        # Step 1: Start recording
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        recording = await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        assert recording.status == RecordingStatus.STARTING
        assert recording.egress_id == egress_id

        # Verify recording is in database
        saved = await recording_repository.get_by_id(recording.id)
        assert saved is not None
        assert saved.status == RecordingStatus.STARTING

        # Step 2: Simulate egress_started webhook
        active_egress_info = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.ACTIVE,
        )

        updated = await recording_service.handle_egress_event(active_egress_info)

        assert updated is not None
        assert updated.status == RecordingStatus.ACTIVE
        assert updated.started_at is not None

        # Step 3: Stop recording
        mock_egress_port.stop_egress.return_value = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.ENDING,
        )

        stopped = await recording_service.stop_recording(session_id)

        assert stopped.status == RecordingStatus.PROCESSING

        # Step 4: Simulate egress_ended webhook with completion
        mock_storage_port.generate_presigned_url.return_value = (
            "https://cdn.example.com/playlist.m3u8"
        )
        mock_storage_port.get_object_info.return_value = ObjectInfo(
            bucket="test-bucket",
            key="recordings/test/index.m3u8",
            size_bytes=1024,
        )

        complete_egress_info = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.COMPLETE,
            file_path="s3://test-bucket/recordings/test/index.m3u8",
            duration_seconds=120,
            file_size_bytes=5000000,
        )

        completed = await recording_service.handle_egress_event(complete_egress_info)

        assert completed is not None
        assert completed.status == RecordingStatus.COMPLETED
        assert completed.playlist_url is not None
        assert completed.duration_seconds == 120
        assert completed.ended_at is not None

        # Verify final state in database
        final = await recording_repository.get_by_id(recording.id)
        assert final is not None
        assert final.status == RecordingStatus.COMPLETED


class TestFailedRecordingLifecycle:
    """Tests for recording failure scenarios."""

    @pytest.mark.asyncio
    async def test_recording_fails_on_egress_error(
        self,
        recording_service: RecordingService,
        recording_repository: PostgresRecordingRepository,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Recording should fail when egress reports an error."""
        session_id = uuid4()
        egress_id = "egress-fail-test"

        # Start recording
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        recording = await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        # Activate recording
        active_info = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.ACTIVE,
        )
        await recording_service.handle_egress_event(active_info)

        # Simulate egress failure
        failed_info = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.FAILED,
            error="Network connection lost",
        )

        failed = await recording_service.handle_egress_event(failed_info)

        assert failed is not None
        assert failed.status == RecordingStatus.FAILED
        assert "Network connection lost" in (failed.error_message or "")

        # Verify in database
        saved = await recording_repository.get_by_id(recording.id)
        assert saved is not None
        assert saved.status == RecordingStatus.FAILED

    @pytest.mark.asyncio
    async def test_recording_fails_when_stopped_before_active(
        self,
        recording_service: RecordingService,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Recording should fail if stopped before becoming active."""
        session_id = uuid4()

        # Start recording (stays in STARTING)
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-early-stop",
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        # Try to stop before it becomes active
        stopped = await recording_service.stop_recording(session_id)

        assert stopped.status == RecordingStatus.FAILED
        assert "before egress started" in (stopped.error_message or "").lower()


class TestRecordingApiIntegration:
    """Integration tests combining API and recording lifecycle."""

    @pytest.mark.asyncio
    async def test_list_recordings_shows_lifecycle_progress(
        self,
        test_client: AsyncClient,
        recording_service: RecordingService,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Recording list should reflect lifecycle state changes."""
        session_id = uuid4()

        # Start a recording
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-api-test",
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        # Check via API - should show STARTING
        response = await test_client.get("/api/v1/recordings")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "starting"

        # Activate recording
        await recording_service.handle_egress_event(
            EgressInfo(
                egress_id="egress-api-test",
                room_name="test-room",
                status=EgressStatus.ACTIVE,
            )
        )

        # Check via API - should show ACTIVE
        response = await test_client.get("/api/v1/recordings?status=active")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "active"

    @pytest.mark.asyncio
    async def test_playback_url_only_available_after_completion(
        self,
        test_client: AsyncClient,
        recording_service: RecordingService,
        mock_egress_port: AsyncMock,
        mock_storage_port: AsyncMock,
    ) -> None:
        """Playback URL should only be available for completed recordings."""
        session_id = uuid4()
        egress_id = "egress-playback-test"

        # Start and activate recording
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        recording = await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        await recording_service.handle_egress_event(
            EgressInfo(
                egress_id=egress_id,
                room_name="test-room",
                status=EgressStatus.ACTIVE,
            )
        )

        # Try to get playback URL while ACTIVE - should fail
        response = await test_client.get(f"/api/v1/recordings/{recording.id}/playback-url")
        assert response.status_code == 400

        # Stop and complete recording
        mock_egress_port.stop_egress.return_value = EgressInfo(
            egress_id=egress_id,
            room_name="test-room",
            status=EgressStatus.ENDING,
        )
        await recording_service.stop_recording(session_id)

        mock_storage_port.generate_presigned_url.return_value = (
            "https://cdn.example.com/playlist.m3u8"
        )
        mock_storage_port.get_object_info.return_value = ObjectInfo(
            bucket="test-bucket",
            key="recordings/test/index.m3u8",
            size_bytes=1024,
        )

        await recording_service.handle_egress_event(
            EgressInfo(
                egress_id=egress_id,
                room_name="test-room",
                status=EgressStatus.COMPLETE,
                file_path="s3://test-bucket/recordings/test/index.m3u8",
                duration_seconds=120,
                file_size_bytes=5000000,
            )
        )

        # Now playback URL should work
        response = await test_client.get(f"/api/v1/recordings/{recording.id}/playback-url")
        assert response.status_code == 200
        data = response.json()
        assert "playback_url" in data


class TestConcurrentRecordings:
    """Tests for handling multiple concurrent recordings."""

    @pytest.mark.asyncio
    async def test_multiple_sessions_can_record_simultaneously(
        self,
        recording_service: RecordingService,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Multiple sessions should be able to record at the same time."""
        session1_id = uuid4()
        session2_id = uuid4()

        # Start two recordings
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-1",
            room_name="room-1",
            status=EgressStatus.STARTING,
        )
        rec1 = await recording_service.start_recording(session1_id, "room-1")

        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-2",
            room_name="room-2",
            status=EgressStatus.STARTING,
        )
        rec2 = await recording_service.start_recording(session2_id, "room-2")

        # Both should be in STARTING state
        assert rec1.status == RecordingStatus.STARTING
        assert rec2.status == RecordingStatus.STARTING

        # Activate both
        await recording_service.handle_egress_event(
            EgressInfo(egress_id="egress-1", room_name="room-1", status=EgressStatus.ACTIVE)
        )
        await recording_service.handle_egress_event(
            EgressInfo(egress_id="egress-2", room_name="room-2", status=EgressStatus.ACTIVE)
        )

        # Verify both are active
        r1 = await recording_service.get_recording(rec1.id)
        r2 = await recording_service.get_recording(rec2.id)

        assert r1 is not None and r1.status == RecordingStatus.ACTIVE
        assert r2 is not None and r2.status == RecordingStatus.ACTIVE
