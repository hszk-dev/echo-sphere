"""Session entity representing a voice interaction session."""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import Enum
from uuid import UUID
from uuid import uuid4


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class SessionStatus(Enum):
    """Status of a voice interaction session."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Session:
    """A voice interaction session between a user and AI.

    Attributes:
        id: Unique session identifier.
        room_name: LiveKit room name.
        user_id: User identifier.
        status: Current session status.
        created_at: Session creation timestamp.
        started_at: Session start timestamp.
        ended_at: Session end timestamp.
    """

    room_name: str
    user_id: str
    id: UUID = field(default_factory=uuid4)
    status: SessionStatus = SessionStatus.PENDING
    created_at: datetime = field(default_factory=_utc_now)
    started_at: datetime | None = None
    ended_at: datetime | None = None

    def start(self) -> None:
        """Mark session as started.

        Raises:
            ValueError: If session is not in pending status.
        """
        if self.status != SessionStatus.PENDING:
            msg = f"Cannot start session in {self.status} status"
            raise ValueError(msg)
        self.status = SessionStatus.ACTIVE
        self.started_at = _utc_now()

    def complete(self) -> None:
        """Mark session as completed.

        Raises:
            ValueError: If session is not in active status.
        """
        if self.status != SessionStatus.ACTIVE:
            msg = f"Cannot complete session in {self.status} status"
            raise ValueError(msg)
        self.status = SessionStatus.COMPLETED
        self.ended_at = _utc_now()

    def fail(self) -> None:
        """Mark session as failed."""
        self.status = SessionStatus.FAILED
        self.ended_at = _utc_now()

    @property
    def duration_seconds(self) -> float | None:
        """Calculate session duration in seconds.

        Returns:
            Duration in seconds, or None if session not completed.
        """
        if self.started_at is None or self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()
