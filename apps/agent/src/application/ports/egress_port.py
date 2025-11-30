"""Egress port interface for LiveKit recording egress."""

from abc import ABC
from abc import abstractmethod

from src.domain.value_objects import EgressConfig
from src.domain.value_objects import EgressInfo


class EgressError(Exception):
    """Base exception for egress operations."""

    pass


class EgressNotFoundError(EgressError):
    """Raised when an egress recording is not found."""

    pass


class EgressAlreadyExistsError(EgressError):
    """Raised when trying to create a duplicate egress."""

    pass


class EgressPort(ABC):
    """Port interface for LiveKit egress operations.

    Implementations handle starting and stopping room composite egress.
    """

    @abstractmethod
    async def start_room_composite(self, config: EgressConfig) -> EgressInfo:
        """Start recording a room composite.

        Args:
            config: Egress configuration.

        Returns:
            Information about the started egress.

        Raises:
            EgressError: If starting the egress fails.
        """
        ...

    @abstractmethod
    async def stop_egress(self, egress_id: str) -> EgressInfo:
        """Stop an active egress.

        Args:
            egress_id: The egress ID to stop.

        Returns:
            Updated egress information.

        Raises:
            EgressError: If stopping the egress fails.
        """
        ...

    @abstractmethod
    async def get_egress_info(self, egress_id: str) -> EgressInfo | None:
        """Get information about an egress.

        Args:
            egress_id: The egress ID to look up.

        Returns:
            Egress information if found, None otherwise.

        Raises:
            EgressError: If the lookup fails.
        """
        ...
