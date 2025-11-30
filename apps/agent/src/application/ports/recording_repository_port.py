"""Recording repository port interface."""

from abc import ABC
from abc import abstractmethod
from uuid import UUID

from src.domain.entities import Recording


class RecordingRepositoryPort(ABC):
    """Port interface for recording persistence.

    Implementations should handle storage and retrieval of recordings.
    """

    @abstractmethod
    async def save(self, recording: Recording) -> None:
        """Save or update a recording.

        Args:
            recording: The recording to save.

        Raises:
            RepositoryError: If the save operation fails.
        """
        ...

    @abstractmethod
    async def get_by_id(self, recording_id: UUID) -> Recording | None:
        """Retrieve a recording by ID.

        Args:
            recording_id: The recording ID to look up.

        Returns:
            The recording if found, None otherwise.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...

    @abstractmethod
    async def get_by_session_id(self, session_id: UUID) -> Recording | None:
        """Retrieve a recording by session ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The recording if found, None otherwise.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...

    @abstractmethod
    async def get_by_egress_id(self, egress_id: str) -> Recording | None:
        """Retrieve a recording by egress ID.

        Args:
            egress_id: The LiveKit egress ID.

        Returns:
            The recording if found, None otherwise.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...

    @abstractmethod
    async def list_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recording]:
        """List recordings by status.

        Args:
            status: The recording status to filter by.
            limit: Maximum number of recordings to return.
            offset: Number of recordings to skip.

        Returns:
            List of recordings with the specified status.

        Raises:
            RepositoryError: If the retrieval fails.
        """
        ...
