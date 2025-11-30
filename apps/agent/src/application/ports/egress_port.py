"""Egress port interface for LiveKit recording egress."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class EgressStatus(StrEnum):
    """Status of an egress operation."""

    STARTING = "starting"
    ACTIVE = "active"
    ENDING = "ending"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class EgressInfo:
    """Information about an egress operation.

    Attributes:
        egress_id: LiveKit egress ID.
        room_name: Room being recorded.
        status: Current egress status.
        file_path: Output file path in storage.
        error: Error message if failed.
    """

    egress_id: str
    room_name: str
    status: EgressStatus
    file_path: str | None = None
    error: str | None = None


@dataclass
class EgressConfig:
    """Configuration for starting an egress.

    Attributes:
        room_name: Room to record.
        output_bucket: S3 bucket for output.
        output_path: Path within bucket.
        width: Video width in pixels.
        height: Video height in pixels.
        segment_duration: HLS segment duration in seconds.
    """

    room_name: str
    output_bucket: str
    output_path: str
    width: int = 1280
    height: int = 720
    segment_duration: int = 4


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
