"""Unit tests for Recording entity."""

from uuid import uuid4

import pytest

from src.domain.entities.recording import Recording
from src.domain.entities.recording import RecordingStatus


class TestRecording:
    """Tests for Recording entity."""

    def test_create_recording_with_starting_status(self) -> None:
        """New recordings should start in STARTING status."""
        session_id = uuid4()
        recording = Recording(
            session_id=session_id,
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        assert recording.session_id == session_id
        assert recording.egress_id == "egress-123"
        assert recording.storage_bucket == "test-bucket"
        assert recording.storage_path == "recordings/test"
        assert recording.status == RecordingStatus.STARTING
        assert recording.playlist_url is None
        assert recording.duration_seconds is None
        assert recording.file_size_bytes is None
        assert recording.error_message is None
        assert recording.started_at is None
        assert recording.ended_at is None

    def test_transition_starting_to_active(self) -> None:
        """Recording can transition from STARTING to ACTIVE."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        recording.activate()

        assert recording.status == RecordingStatus.ACTIVE
        assert recording.started_at is not None

    def test_transition_active_to_processing(self) -> None:
        """Recording can transition from ACTIVE to PROCESSING."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()

        recording.start_processing()

        assert recording.status == RecordingStatus.PROCESSING

    def test_transition_processing_to_completed(self) -> None:
        """Recording can transition from PROCESSING to COMPLETED."""
        recording = Recording(
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

        assert recording.status == RecordingStatus.COMPLETED
        assert recording.playlist_url == "https://example.com/playlist.m3u8"
        assert recording.duration_seconds == 120
        assert recording.file_size_bytes == 1024000
        assert recording.ended_at is not None

    def test_invalid_transition_starting_to_processing(self) -> None:
        """Invalid transition from STARTING to PROCESSING should raise."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            recording.start_processing()

    def test_invalid_transition_starting_to_completed(self) -> None:
        """Invalid transition from STARTING to COMPLETED should raise."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            recording.complete(
                playlist_url="https://example.com/playlist.m3u8",
                duration_seconds=120,
                file_size_bytes=1024000,
            )

    def test_invalid_transition_active_to_completed(self) -> None:
        """Invalid transition from ACTIVE to COMPLETED should raise."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()

        with pytest.raises(ValueError, match="Cannot transition"):
            recording.complete(
                playlist_url="https://example.com/playlist.m3u8",
                duration_seconds=120,
                file_size_bytes=1024000,
            )

    def test_fail_from_starting(self) -> None:
        """Recording can fail from STARTING state."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        recording.fail("Egress failed to start")

        assert recording.status == RecordingStatus.FAILED
        assert recording.error_message == "Egress failed to start"
        assert recording.ended_at is not None

    def test_fail_from_active(self) -> None:
        """Recording can fail from ACTIVE state."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()

        recording.fail("Network error")

        assert recording.status == RecordingStatus.FAILED
        assert recording.error_message == "Network error"
        assert recording.ended_at is not None

    def test_fail_from_processing(self) -> None:
        """Recording can fail from PROCESSING state."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        recording.start_processing()

        recording.fail("Transcoding failed")

        assert recording.status == RecordingStatus.FAILED
        assert recording.error_message == "Transcoding failed"
        assert recording.ended_at is not None

    def test_fail_from_completed_raises(self) -> None:
        """Cannot fail a recording that is already completed."""
        recording = Recording(
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

        with pytest.raises(ValueError, match="Cannot fail recording"):
            recording.fail("Some error")

    def test_fail_from_failed_raises(self) -> None:
        """Cannot fail a recording that is already failed."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.fail("First error")

        with pytest.raises(ValueError, match="Cannot fail recording"):
            recording.fail("Second error")

    def test_is_terminal_completed(self) -> None:
        """Completed recording should be terminal."""
        recording = Recording(
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

        assert recording.is_terminal is True

    def test_is_terminal_failed(self) -> None:
        """Failed recording should be terminal."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.fail("Error")

        assert recording.is_terminal is True

    def test_is_terminal_active(self) -> None:
        """Active recording should not be terminal."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()

        assert recording.is_terminal is False

    def test_is_active_starting(self) -> None:
        """Starting recording should be active."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )

        assert recording.is_active is True

    def test_is_active_active(self) -> None:
        """Active recording should be active."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()

        assert recording.is_active is True

    def test_is_active_processing(self) -> None:
        """Processing recording should not be active."""
        recording = Recording(
            session_id=uuid4(),
            egress_id="egress-123",
            storage_bucket="test-bucket",
            storage_path="recordings/test",
        )
        recording.activate()
        recording.start_processing()

        assert recording.is_active is False
