"""Unit tests for Recording Service."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.application.ports import EgressConfig
from src.application.ports import EgressInfo
from src.application.ports import EgressStatus
from src.application.ports import StorageObject
from src.application.use_cases import RecordingAlreadyExistsError
from src.application.use_cases import RecordingNotFoundError
from src.application.use_cases import RecordingService
from src.application.use_cases import RecordingServiceError
from src.domain.entities import Recording
from src.domain.entities import RecordingStatus


@pytest.fixture
def mock_recording_repo() -> AsyncMock:
    """Create mock recording repository."""
    return AsyncMock()


@pytest.fixture
def mock_egress_port() -> AsyncMock:
    """Create mock egress port."""
    return AsyncMock()


@pytest.fixture
def mock_storage_port() -> AsyncMock:
    """Create mock storage port."""
    return AsyncMock()


@pytest.fixture
def recording_service(
    mock_recording_repo: AsyncMock,
    mock_egress_port: AsyncMock,
    mock_storage_port: AsyncMock,
) -> RecordingService:
    """Create recording service with mocked dependencies."""
    return RecordingService(
        recording_repository=mock_recording_repo,
        egress_port=mock_egress_port,
        storage_port=mock_storage_port,
        default_bucket="test-bucket",
        default_width=1280,
        default_height=720,
        default_segment_duration=4,
        presigned_url_expiry=3600,
    )


class TestStartRecording:
    """Tests for start_recording method."""

    @pytest.mark.asyncio
    async def test_start_recording_creates_entity(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Starting recording should create Recording in STARTING status."""
        session_id = uuid4()
        mock_recording_repo.get_by_session_id.return_value = None
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        recording = await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        assert recording.session_id == session_id
        assert recording.egress_id == "egress-123"
        assert recording.storage_bucket == "test-bucket"
        assert recording.status == RecordingStatus.STARTING
        mock_recording_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_recording_calls_egress(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Starting recording should call EgressPort.start_room_composite."""
        session_id = uuid4()
        mock_recording_repo.get_by_session_id.return_value = None
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        mock_egress_port.start_room_composite.assert_called_once()
        call_args = mock_egress_port.start_room_composite.call_args[0][0]
        assert isinstance(call_args, EgressConfig)
        assert call_args.room_name == "test-room"
        assert call_args.output_bucket == "test-bucket"

    @pytest.mark.asyncio
    async def test_start_recording_with_existing_active_raises(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """Starting recording when active recording exists should raise."""
        session_id = uuid4()
        existing_recording = Recording(
            session_id=session_id,
            egress_id="existing-egress",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
            status=RecordingStatus.ACTIVE,
        )
        mock_recording_repo.get_by_session_id.return_value = existing_recording

        with pytest.raises(RecordingAlreadyExistsError):
            await recording_service.start_recording(
                session_id=session_id,
                room_name="test-room",
            )

    @pytest.mark.asyncio
    async def test_start_recording_allows_after_completed(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Starting recording should be allowed if previous recording is completed."""
        session_id = uuid4()
        existing_recording = MagicMock()
        existing_recording.is_terminal = True
        mock_recording_repo.get_by_session_id.return_value = existing_recording
        mock_egress_port.start_room_composite.return_value = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.STARTING,
        )

        recording = await recording_service.start_recording(
            session_id=session_id,
            room_name="test-room",
        )

        assert recording is not None


class TestStopRecording:
    """Tests for stop_recording method."""

    @pytest.mark.asyncio
    async def test_stop_recording_transitions_to_processing(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Stopping recording should transition to PROCESSING."""
        session_id = uuid4()
        recording = Recording(
            session_id=session_id,
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        mock_recording_repo.get_by_session_id.return_value = recording
        mock_egress_port.stop_egress.return_value = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.ENDING,
        )

        result = await recording_service.stop_recording(session_id)

        assert result.status == RecordingStatus.PROCESSING
        mock_egress_port.stop_egress.assert_called_once_with("egress-123")

    @pytest.mark.asyncio
    async def test_stop_recording_not_found_raises(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """Stopping non-existent recording should raise."""
        session_id = uuid4()
        mock_recording_repo.get_by_session_id.return_value = None

        with pytest.raises(RecordingNotFoundError):
            await recording_service.stop_recording(session_id)

    @pytest.mark.asyncio
    async def test_stop_recording_already_stopped_returns(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Stopping already stopped recording should return without error."""
        session_id = uuid4()
        recording = Recording(
            session_id=session_id,
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        recording.start_processing()
        recording.complete(
            playlist_url="https://example.com/playlist.m3u8",
            duration_seconds=120,
            file_size_bytes=1024000,
        )
        mock_recording_repo.get_by_session_id.return_value = recording

        result = await recording_service.stop_recording(session_id)

        assert result.status == RecordingStatus.COMPLETED
        mock_egress_port.stop_egress.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_recording_starting_state_fails_recording(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_egress_port: AsyncMock,
    ) -> None:
        """Stopping recording in STARTING state should fail the recording."""
        session_id = uuid4()
        recording = Recording(
            session_id=session_id,
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        # Recording is in STARTING state (default)
        assert recording.status == RecordingStatus.STARTING
        mock_recording_repo.get_by_session_id.return_value = recording

        result = await recording_service.stop_recording(session_id)

        assert result.status == RecordingStatus.FAILED
        assert result.error_message == "Recording stopped before egress started"
        mock_egress_port.stop_egress.assert_not_called()
        mock_recording_repo.save.assert_called_once()


class TestHandleEgressEvent:
    """Tests for handle_egress_event method."""

    @pytest.mark.asyncio
    async def test_handle_egress_started_transitions_to_active(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """egress_started event should transition to ACTIVE."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        mock_recording_repo.get_by_egress_id.return_value = recording

        egress_info = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.ACTIVE,
        )

        result = await recording_service.handle_egress_event(egress_info)

        assert result is not None
        assert result.status == RecordingStatus.ACTIVE
        mock_recording_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_egress_ended_transitions_to_completed(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_storage_port: AsyncMock,
    ) -> None:
        """egress_ended event should transition to COMPLETED."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        mock_recording_repo.get_by_egress_id.return_value = recording
        mock_storage_port.generate_presigned_url.return_value = "https://example.com/playlist.m3u8"
        mock_storage_port.get_object_info.return_value = StorageObject(
            bucket="test-bucket",
            key="recordings/test/index.m3u8",
            size_bytes=1024,
        )

        egress_info = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.COMPLETE,
        )

        result = await recording_service.handle_egress_event(egress_info)

        assert result is not None
        assert result.status == RecordingStatus.COMPLETED
        assert result.playlist_url == "https://example.com/playlist.m3u8"

    @pytest.mark.asyncio
    async def test_handle_egress_failed_transitions_to_failed(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """egress_failed event should transition to FAILED."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        mock_recording_repo.get_by_egress_id.return_value = recording

        egress_info = EgressInfo(
            egress_id="egress-123",
            room_name="test-room",
            status=EgressStatus.FAILED,
            error="Network error",
        )

        result = await recording_service.handle_egress_event(egress_info)

        assert result is not None
        assert result.status == RecordingStatus.FAILED
        assert result.error_message == "Network error"

    @pytest.mark.asyncio
    async def test_handle_egress_event_recording_not_found(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """Event for unknown recording should return None."""
        mock_recording_repo.get_by_egress_id.return_value = None

        egress_info = EgressInfo(
            egress_id="unknown-egress",
            room_name="test-room",
            status=EgressStatus.ACTIVE,
        )

        result = await recording_service.handle_egress_event(egress_info)

        assert result is None


class TestGetPlaybackUrl:
    """Tests for get_playback_url method."""

    @pytest.mark.asyncio
    async def test_get_playback_url_success(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
        mock_storage_port: AsyncMock,
    ) -> None:
        """Should return presigned URL for completed recording."""
        recording_id = uuid4()
        recording = Recording(
            id=recording_id,
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        recording.start_processing()
        recording.complete(
            playlist_url="https://example.com/playlist.m3u8",
            duration_seconds=120,
            file_size_bytes=1024000,
        )
        mock_recording_repo.get_by_id.return_value = recording
        mock_storage_port.generate_presigned_url.return_value = (
            "https://cdn.example.com/presigned-url"
        )

        url = await recording_service.get_playback_url(recording_id)

        assert url == "https://cdn.example.com/presigned-url"
        mock_storage_port.generate_presigned_url.assert_called_once_with(
            bucket="test-bucket",
            key="recordings/test/index.m3u8",
            expiry_seconds=3600,
        )

    @pytest.mark.asyncio
    async def test_get_playback_url_not_found_raises(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """Should raise for non-existent recording."""
        recording_id = uuid4()
        mock_recording_repo.get_by_id.return_value = None

        with pytest.raises(RecordingNotFoundError):
            await recording_service.get_playback_url(recording_id)

    @pytest.mark.asyncio
    async def test_get_playback_url_not_completed_raises(
        self,
        recording_service: RecordingService,
        mock_recording_repo: AsyncMock,
    ) -> None:
        """Should raise for non-completed recording."""
        recording_id = uuid4()
        recording = Recording(
            id=recording_id,
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        mock_recording_repo.get_by_id.return_value = recording

        with pytest.raises(RecordingServiceError, match="not completed"):
            await recording_service.get_playback_url(recording_id)
