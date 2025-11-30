"""Message entity for conversation history."""

from dataclasses import dataclass
from dataclasses import field
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from uuid import UUID
from uuid import uuid4


def _utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class MessageRole(StrEnum):
    """Role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """A message in a conversation.

    Attributes:
        id: Unique message identifier.
        session_id: Session this message belongs to.
        role: Role of the message sender.
        content: Message content.
        created_at: Message creation timestamp.
    """

    session_id: UUID
    role: MessageRole
    content: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=_utc_now)
