"""Session repository port interface."""

from abc import ABC
from abc import abstractmethod
from uuid import UUID

from src.domain.entities import Message
from src.domain.entities import Session


class SessionRepositoryPort(ABC):
    """Port interface for session persistence.

    Implementations should handle storage and retrieval of sessions and messages.
    """

    @abstractmethod
    async def save_session(self, session: Session) -> None:
        """Save or update a session.

        Args:
            session: The session to save.

        Raises:
            RepositoryError: If the save operation fails.
        """
        ...

    @abstractmethod
    async def get_session(self, session_id: UUID) -> Session | None:
        """Retrieve a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...

    @abstractmethod
    async def get_session_by_room(self, room_name: str) -> Session | None:
        """Retrieve a session by room name.

        Args:
            room_name: The LiveKit room name.

        Returns:
            The session if found, None otherwise.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...

    @abstractmethod
    async def save_message(self, message: Message) -> None:
        """Save a message to a session.

        Args:
            message: The message to save.

        Raises:
            RepositoryError: If the save operation fails.
        """
        ...

    @abstractmethod
    async def get_messages(self, session_id: UUID) -> list[Message]:
        """Retrieve all messages for a session.

        Args:
            session_id: The session ID.

        Returns:
            List of messages ordered by creation time.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...
