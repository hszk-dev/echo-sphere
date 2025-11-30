"""Egress-related value objects.

These value objects represent immutable data structures for LiveKit Egress
configuration and status tracking.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class EgressStatus(StrEnum):
    """Status of an egress recording.

    Follows LiveKit Egress API lifecycle states:
    https://docs.livekit.io/egress/overview/#egress-status
    """

    STARTING = "starting"  # Egress is being initialized
    ACTIVE = "active"  # Recording in progress
    ENDING = "ending"  # Stop requested, finalizing
    COMPLETE = "complete"  # Successfully finished
    FAILED = "failed"  # Error occurred


@dataclass(frozen=True)
class EgressConfig:
    """Configuration for starting an egress recording.

    Attributes:
        room_name: LiveKit room name to record.
        output_bucket: S3 bucket for storing the recording.
        output_path: Path within the bucket for recording files.
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


@dataclass(frozen=True)
class EgressInfo:
    """Information about an egress recording.

    Attributes:
        egress_id: Unique identifier for the egress.
        room_name: LiveKit room name being recorded.
        status: Current status of the egress.
        started_at: Timestamp when egress started.
        ended_at: Timestamp when egress ended.
        file_path: Path to the output file (e.g., HLS playlist).
        error: Error message if egress failed.
        duration_seconds: Total duration of the recording in seconds.
        file_size_bytes: Total file size of the recording in bytes.
    """

    egress_id: str
    room_name: str
    status: EgressStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    file_path: str | None = None
    error: str | None = None
    duration_seconds: int | None = None
    file_size_bytes: int | None = None
