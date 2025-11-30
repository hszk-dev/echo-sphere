"""Integration tests for Recording API endpoints.

Tests the full API flow with real database (SQLite) and mocked external services.
"""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.adapters.outbound.postgres_recording import PostgresRecordingRepository
from tests.factories import RecordingFactory


class TestListRecordings:
    """Tests for GET /api/v1/recordings endpoint."""

    @pytest.mark.asyncio
    async def test_list_recordings_empty(self, test_client: AsyncClient) -> None:
        """Empty database should return empty list with pagination."""
        response = await test_client.get("/api/v1/recordings")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1

    @pytest.mark.asyncio
    async def test_list_recordings_with_data(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Should return recordings from database."""
        # Create test recordings
        recording1 = RecordingFactory.build_completed()
        recording2 = RecordingFactory.build_active()
        await recording_repository.save(recording1)
        await recording_repository.save(recording2)

        response = await test_client.get("/api/v1/recordings")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_recordings_pagination(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Pagination should limit results correctly."""
        # Create 5 test recordings
        for _ in range(5):
            recording = RecordingFactory.build_completed()
            await recording_repository.save(recording)

        response = await test_client.get("/api/v1/recordings?page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total_pages"] == 3

    @pytest.mark.asyncio
    async def test_list_recordings_filter_by_status(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Status filter should return only matching recordings."""
        # Create recordings with different statuses
        completed = RecordingFactory.build_completed()
        active = RecordingFactory.build_active()
        failed = RecordingFactory.build_failed()
        await recording_repository.save(completed)
        await recording_repository.save(active)
        await recording_repository.save(failed)

        response = await test_client.get("/api/v1/recordings?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_list_recordings_status_filter_pagination(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Status filter with pagination should return correct total count.

        This tests the bug fix for count_by_status - the total should
        reflect ALL matching records, not just the current page.
        """
        # Create 5 completed recordings and 2 active
        for _ in range(5):
            recording = RecordingFactory.build_completed()
            await recording_repository.save(recording)
        for _ in range(2):
            recording = RecordingFactory.build_active()
            await recording_repository.save(recording)

        # Request page 1 with page_size 2, filtering by completed
        response = await test_client.get("/api/v1/recordings?status=completed&page=1&page_size=2")

        assert response.status_code == 200
        data = response.json()
        # Total should be 5 (all completed), not 2 (just this page)
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3


class TestGetRecording:
    """Tests for GET /api/v1/recordings/{recording_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_recording_success(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Should return recording details by ID."""
        recording = RecordingFactory.build_completed()
        await recording_repository.save(recording)

        response = await test_client.get(f"/api/v1/recordings/{recording.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(recording.id)
        assert data["session_id"] == str(recording.session_id)
        assert data["egress_id"] == recording.egress_id
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_recording_not_found(self, test_client: AsyncClient) -> None:
        """Non-existent recording should return 404."""
        fake_id = uuid4()

        response = await test_client.get(f"/api/v1/recordings/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetRecordingBySession:
    """Tests for GET /api/v1/recordings/session/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_by_session_success(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Should return recording by session ID."""
        session_id = uuid4()
        recording = RecordingFactory.build_completed(session_id=session_id)
        await recording_repository.save(recording)

        response = await test_client.get(f"/api/v1/recordings/session/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)

    @pytest.mark.asyncio
    async def test_get_by_session_not_found(self, test_client: AsyncClient) -> None:
        """Non-existent session should return 404."""
        fake_session_id = uuid4()

        response = await test_client.get(f"/api/v1/recordings/session/{fake_session_id}")

        assert response.status_code == 404


class TestGetPlaybackUrl:
    """Tests for GET /api/v1/recordings/{recording_id}/playback-url endpoint."""

    @pytest.mark.asyncio
    async def test_get_playback_url_success(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
        mock_storage_port: AsyncMock,
    ) -> None:
        """Should return presigned URL for completed recording."""
        recording = RecordingFactory.build_completed()
        await recording_repository.save(recording)

        mock_storage_port.generate_presigned_url.return_value = (
            "https://cdn.example.com/presigned-url?token=xyz"
        )

        response = await test_client.get(f"/api/v1/recordings/{recording.id}/playback-url")

        assert response.status_code == 200
        data = response.json()
        assert data["recording_id"] == str(recording.id)
        assert "presigned-url" in data["playback_url"]
        assert data["expires_in_seconds"] == 3600

    @pytest.mark.asyncio
    async def test_get_playback_url_custom_expiry(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
        mock_storage_port: AsyncMock,
    ) -> None:
        """Should use custom expiry when provided."""
        recording = RecordingFactory.build_completed()
        await recording_repository.save(recording)

        mock_storage_port.generate_presigned_url.return_value = (
            "https://cdn.example.com/presigned-url"
        )

        response = await test_client.get(
            f"/api/v1/recordings/{recording.id}/playback-url?expiry_seconds=7200"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["expires_in_seconds"] == 7200

    @pytest.mark.asyncio
    async def test_get_playback_url_not_found(self, test_client: AsyncClient) -> None:
        """Non-existent recording should return 404."""
        fake_id = uuid4()

        response = await test_client.get(f"/api/v1/recordings/{fake_id}/playback-url")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_playback_url_not_completed(
        self,
        test_client: AsyncClient,
        recording_repository: PostgresRecordingRepository,
    ) -> None:
        """Active recording should return 400 (not ready for playback)."""
        recording = RecordingFactory.build_active()
        await recording_repository.save(recording)

        response = await test_client.get(f"/api/v1/recordings/{recording.id}/playback-url")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_playback_url_expiry_validation(self, test_client: AsyncClient) -> None:
        """Expiry outside bounds should be rejected."""
        fake_id = uuid4()

        # Too short
        response = await test_client.get(
            f"/api/v1/recordings/{fake_id}/playback-url?expiry_seconds=30"
        )
        assert response.status_code == 422

        # Too long
        response = await test_client.get(
            f"/api/v1/recordings/{fake_id}/playback-url?expiry_seconds=100000"
        )
        assert response.status_code == 422
