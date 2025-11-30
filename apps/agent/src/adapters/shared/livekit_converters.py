"""LiveKit protocol conversion utilities.

This module provides shared conversion functions for transforming
LiveKit protocol objects into domain value objects.
"""

from datetime import UTC
from datetime import datetime

from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo
from livekit.protocol.egress import EgressStatus as LiveKitEgressStatus

from src.domain.value_objects import EgressInfo
from src.domain.value_objects import EgressStatus


def convert_egress_info(
    lk_info: LiveKitEgressInfo,
    room_name: str | None = None,
) -> EgressInfo:
    """Convert LiveKit EgressInfo to domain EgressInfo.

    Args:
        lk_info: LiveKit protocol EgressInfo.
        room_name: Optional room name override. If not provided,
            uses the room_name from lk_info.

    Returns:
        Domain EgressInfo value object.
    """
    status = convert_egress_status(lk_info.status)

    # Convert timestamps from nanoseconds to datetime
    started_at = None
    if lk_info.started_at:
        started_at = datetime.fromtimestamp(lk_info.started_at / 1e9, tz=UTC)

    ended_at = None
    if lk_info.ended_at:
        ended_at = datetime.fromtimestamp(lk_info.ended_at / 1e9, tz=UTC)

    # Extract playlist URL from segment outputs
    file_path = None
    if lk_info.segment_results:
        for segment in lk_info.segment_results:
            if segment.playlist_location:
                file_path = segment.playlist_location
                break

    # Calculate file size from segment results
    file_size_bytes = None
    if lk_info.segment_results:
        file_size_bytes = sum(segment.size for segment in lk_info.segment_results if segment.size)

    # Get duration from the egress info (convert to int)
    duration_seconds = None
    if lk_info.segment_results:
        for segment in lk_info.segment_results:
            if segment.duration:
                duration_seconds = int(segment.duration / 1e9)  # nanoseconds to seconds
                break

    return EgressInfo(
        egress_id=lk_info.egress_id,
        room_name=room_name or lk_info.room_name,
        status=status,
        started_at=started_at,
        ended_at=ended_at,
        error=lk_info.error if lk_info.error else None,
        file_path=file_path,
        duration_seconds=duration_seconds,
        file_size_bytes=file_size_bytes,
    )


def convert_egress_status(lk_status: LiveKitEgressStatus) -> EgressStatus:
    """Convert LiveKit EgressStatus to domain EgressStatus.

    Args:
        lk_status: LiveKit protocol EgressStatus.

    Returns:
        Domain EgressStatus enum value.
    """
    status_map = {
        LiveKitEgressStatus.EGRESS_STARTING: EgressStatus.STARTING,
        LiveKitEgressStatus.EGRESS_ACTIVE: EgressStatus.ACTIVE,
        LiveKitEgressStatus.EGRESS_ENDING: EgressStatus.ENDING,
        LiveKitEgressStatus.EGRESS_COMPLETE: EgressStatus.COMPLETE,
        LiveKitEgressStatus.EGRESS_FAILED: EgressStatus.FAILED,
        LiveKitEgressStatus.EGRESS_ABORTED: EgressStatus.FAILED,
        LiveKitEgressStatus.EGRESS_LIMIT_REACHED: EgressStatus.FAILED,
    }
    return status_map.get(lk_status, EgressStatus.STARTING)
