"""Integration tests for PostgresRecordingRepository.

Tests the repository with real SQLite database for realistic behavior.
"""

import asyncio
from uuid import uuid4

import pytest

from src.adapters.outbound.postgres_recording import PostgresRecordingRepository
from src.domain.entities import RecordingStatus
from tests.factories import RecordingFactory


class TestSave:
    """Tests for save method."""

    @pytest.mark.asyncio
    async def test_save_new_recording(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should insert a new recording."""
        recording = RecordingFactory.build_starting()

        await recording_repository.save(recording)

        # Verify it was saved
        result = await recording_repository.get_by_id(recording.id)
        assert result is not None
        assert result.id == recording.id
        assert result.egress_id == recording.egress_id

    @pytest.mark.asyncio
    async def test_save_update_existing_recording(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should update an existing recording."""
        recording = RecordingFactory.build_starting()
        await recording_repository.save(recording)

        # Update the recording
        recording.activate()
        await recording_repository.save(recording)

        # Verify it was updated
        result = await recording_repository.get_by_id(recording.id)
        assert result is not None
        assert result.status == RecordingStatus.ACTIVE
        assert result.started_at is not None


class TestGetById:
    """Tests for get_by_id method."""

    @pytest.mark.asyncio
    async def test_get_by_id_exists(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return recording when it exists."""
        recording = RecordingFactory.build_completed()
        await recording_repository.save(recording)

        result = await recording_repository.get_by_id(recording.id)

        assert result is not None
        assert result.id == recording.id
        assert result.status == RecordingStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return None when recording doesn't exist."""
        result = await recording_repository.get_by_id(uuid4())

        assert result is None


class TestGetBySessionId:
    """Tests for get_by_session_id method."""

    @pytest.mark.asyncio
    async def test_get_by_session_id_exists(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return recording for the session."""
        session_id = uuid4()
        recording = RecordingFactory.build_completed(session_id=session_id)
        await recording_repository.save(recording)

        result = await recording_repository.get_by_session_id(session_id)

        assert result is not None
        assert result.session_id == session_id

    @pytest.mark.asyncio
    async def test_get_by_session_id_returns_latest(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return the most recent recording for the session."""
        session_id = uuid4()

        # Create older recording
        older = RecordingFactory.build_failed(session_id=session_id)
        await recording_repository.save(older)

        # Create newer recording
        newer = RecordingFactory.build_completed(session_id=session_id)
        await recording_repository.save(newer)

        result = await recording_repository.get_by_session_id(session_id)

        assert result is not None
        # The newer recording should be returned (most recent)
        assert result.id == newer.id

    @pytest.mark.asyncio
    async def test_get_by_session_id_not_found(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return None when no recording exists for session."""
        result = await recording_repository.get_by_session_id(uuid4())

        assert result is None


class TestGetByEgressId:
    """Tests for get_by_egress_id method."""

    @pytest.mark.asyncio
    async def test_get_by_egress_id_exists(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return recording by egress ID."""
        recording = RecordingFactory.build_active()
        await recording_repository.save(recording)

        result = await recording_repository.get_by_egress_id(recording.egress_id)

        assert result is not None
        assert result.egress_id == recording.egress_id

    @pytest.mark.asyncio
    async def test_get_by_egress_id_not_found(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return None when egress ID doesn't exist."""
        result = await recording_repository.get_by_egress_id("nonexistent-egress")

        assert result is None


class TestListByStatus:
    """Tests for list_by_status method."""

    @pytest.mark.asyncio
    async def test_list_by_status_filters_correctly(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return only recordings with matching status."""
        # Create recordings with different statuses
        completed1 = RecordingFactory.build_completed()
        completed2 = RecordingFactory.build_completed()
        active = RecordingFactory.build_active()
        failed = RecordingFactory.build_failed()

        await recording_repository.save(completed1)
        await recording_repository.save(completed2)
        await recording_repository.save(active)
        await recording_repository.save(failed)

        result = await recording_repository.list_by_status(RecordingStatus.COMPLETED)

        assert len(result) == 2
        assert all(r.status == RecordingStatus.COMPLETED for r in result)

    @pytest.mark.asyncio
    async def test_list_by_status_with_pagination(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should respect limit and offset parameters."""
        # Create 5 completed recordings
        for _ in range(5):
            recording = RecordingFactory.build_completed()
            await recording_repository.save(recording)

        result = await recording_repository.list_by_status(
            RecordingStatus.COMPLETED, limit=2, offset=2
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_list_by_status_empty(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return empty list when no matching recordings."""
        result = await recording_repository.list_by_status(RecordingStatus.COMPLETED)

        assert result == []


class TestCountByStatus:
    """Tests for count_by_status method."""

    @pytest.mark.asyncio
    async def test_count_by_status_returns_correct_count(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return correct count of recordings with status."""
        # Create 3 completed and 2 active recordings
        for _ in range(3):
            await recording_repository.save(RecordingFactory.build_completed())
        for _ in range(2):
            await recording_repository.save(RecordingFactory.build_active())

        completed_count = await recording_repository.count_by_status(RecordingStatus.COMPLETED)
        active_count = await recording_repository.count_by_status(RecordingStatus.ACTIVE)
        failed_count = await recording_repository.count_by_status(RecordingStatus.FAILED)

        assert completed_count == 3
        assert active_count == 2
        assert failed_count == 0

    @pytest.mark.asyncio
    async def test_count_by_status_empty(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return 0 when no recordings exist."""
        count = await recording_repository.count_by_status(RecordingStatus.COMPLETED)

        assert count == 0


class TestListAll:
    """Tests for list_all method."""

    @pytest.mark.asyncio
    async def test_list_all_returns_all_recordings(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return all recordings with total count."""
        # Create recordings with different statuses
        await recording_repository.save(RecordingFactory.build_completed())
        await recording_repository.save(RecordingFactory.build_active())
        await recording_repository.save(RecordingFactory.build_failed())

        recordings, total = await recording_repository.list_all()

        assert total == 3
        assert len(recordings) == 3

    @pytest.mark.asyncio
    async def test_list_all_pagination(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should paginate results correctly."""
        # Create 5 recordings
        for _ in range(5):
            await recording_repository.save(RecordingFactory.build_completed())

        recordings, total = await recording_repository.list_all(page=2, page_size=2)

        assert total == 5
        assert len(recordings) == 2

    @pytest.mark.asyncio
    async def test_list_all_empty(self, recording_repository: PostgresRecordingRepository) -> None:
        """Should return empty list with zero total when no recordings."""
        recordings, total = await recording_repository.list_all()

        assert total == 0
        assert recordings == []

    @pytest.mark.asyncio
    async def test_list_all_ordering(
        self, recording_repository: PostgresRecordingRepository
    ) -> None:
        """Should return recordings ordered by created_at descending."""
        # Create recordings with small delays to ensure different timestamps
        r1 = RecordingFactory.build_completed()
        await recording_repository.save(r1)
        await asyncio.sleep(0.01)

        r2 = RecordingFactory.build_completed()
        await recording_repository.save(r2)
        await asyncio.sleep(0.01)

        r3 = RecordingFactory.build_completed()
        await recording_repository.save(r3)

        recordings, _ = await recording_repository.list_all()

        # Most recent should be first
        assert recordings[0].id == r3.id
        assert recordings[2].id == r1.id
