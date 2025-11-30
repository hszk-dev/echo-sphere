"""Recording entity representing a session recording."""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from uuid import UUID
from uuid import uuid4


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class RecordingStatus(StrEnum):
    """Status of a recording.

    State machine:
        STARTING -> ACTIVE -> PROCESSING -> COMPLETED
            |          |           |
            v          v           v
          FAILED     FAILED     FAILED
    """

    STARTING = "starting"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Valid state transitions
_VALID_TRANSITIONS: dict[RecordingStatus, set[RecordingStatus]] = {
    RecordingStatus.STARTING: {RecordingStatus.ACTIVE, RecordingStatus.FAILED},
    RecordingStatus.ACTIVE: {RecordingStatus.PROCESSING, RecordingStatus.FAILED},
    RecordingStatus.PROCESSING: {RecordingStatus.COMPLETED, RecordingStatus.FAILED},
    RecordingStatus.COMPLETED: set(),
    RecordingStatus.FAILED: set(),
}


@dataclass
class Recording:
    """A recording of a voice interaction session.

    Attributes:
        id: Unique recording identifier.
        session_id: Associated session ID.
        egress_id: LiveKit egress ID.
        status: Current recording status.
        storage_bucket: S3 bucket name for storage.
        storage_path: Path within the bucket.
        playlist_url: HLS playlist URL (set after processing).
        duration_seconds: Recording duration in seconds.
        file_size_bytes: Total file size in bytes.
        error_message: Error message if recording failed.
        created_at: Recording creation timestamp.
        started_at: Recording start timestamp.
        ended_at: Recording end timestamp.
    """

    session_id: UUID
    egress_id: str
    storage_bucket: str
    storage_path: str
    id: UUID = field(default_factory=uuid4)
    status: RecordingStatus = RecordingStatus.STARTING
    playlist_url: str | None = None
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    created_at: datetime = field(default_factory=_utc_now)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    def _can_transition_to(self, new_status: RecordingStatus) -> bool:
        """Check if transition to new status is valid.

        Args:
            new_status: The target status.

        Returns:
            True if transition is valid.
        """
        return new_status in _VALID_TRANSITIONS.get(self.status, set())

    def _transition_to(self, new_status: RecordingStatus) -> None:
        """Transition to a new status.

        Args:
            new_status: The target status.

        Raises:
            ValueError: If the transition is not valid.
        """
        if not self._can_transition_to(new_status):
            msg = f"Cannot transition from {self.status} to {new_status}"
            raise ValueError(msg)
        self.status = new_status

    def activate(self) -> None:
        """Mark recording as active (egress started).

        Raises:
            ValueError: If recording is not in STARTING status.
        """
        self._transition_to(RecordingStatus.ACTIVE)
        self.started_at = _utc_now()

    def start_processing(self) -> None:
        """Mark recording as processing (egress stopped, transcoding started).

        Raises:
            ValueError: If recording is not in ACTIVE status.
        """
        self._transition_to(RecordingStatus.PROCESSING)

    def complete(
        self,
        playlist_url: str,
        duration_seconds: int,
        file_size_bytes: int,
    ) -> None:
        """Mark recording as completed.

        Args:
            playlist_url: HLS playlist URL.
            duration_seconds: Recording duration.
            file_size_bytes: Total file size.

        Raises:
            ValueError: If recording is not in PROCESSING status.
        """
        self._transition_to(RecordingStatus.COMPLETED)
        self.playlist_url = playlist_url
        self.duration_seconds = duration_seconds
        self.file_size_bytes = file_size_bytes
        self.ended_at = _utc_now()

    def fail(self, error_message: str) -> None:
        """Mark recording as failed.

        Can be called from STARTING, ACTIVE, or PROCESSING states.

        Args:
            error_message: Description of the failure.

        Raises:
            ValueError: If recording is already in a terminal state.
        """
        if self.status in {RecordingStatus.COMPLETED, RecordingStatus.FAILED}:
            msg = f"Cannot fail recording in {self.status} status"
            raise ValueError(msg)
        self.status = RecordingStatus.FAILED
        self.error_message = error_message
        self.ended_at = _utc_now()

    @property
    def is_terminal(self) -> bool:
        """Check if recording is in a terminal state.

        Returns:
            True if recording is COMPLETED or FAILED.
        """
        return self.status in {RecordingStatus.COMPLETED, RecordingStatus.FAILED}

    @property
    def is_active(self) -> bool:
        """Check if recording is currently active.

        Returns:
            True if recording is STARTING or ACTIVE.
        """
        return self.status in {RecordingStatus.STARTING, RecordingStatus.ACTIVE}
