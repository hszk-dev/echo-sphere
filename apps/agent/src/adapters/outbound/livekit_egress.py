"""LiveKit Egress adapter implementation.

This adapter implements the EgressPort interface using the LiveKit API
for recording room composite egress with HLS output to S3.
"""

from datetime import UTC
from datetime import datetime

import structlog
from livekit.api import LiveKitAPI
from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo
from livekit.protocol.egress import EgressStatus as LiveKitEgressStatus
from livekit.protocol.egress import ListEgressRequest
from livekit.protocol.egress import RoomCompositeEgressRequest
from livekit.protocol.egress import S3Upload
from livekit.protocol.egress import SegmentedFileOutput
from livekit.protocol.egress import StopEgressRequest

from src.application.ports.egress_port import EgressError
from src.application.ports.egress_port import EgressNotFoundError
from src.application.ports.egress_port import EgressPort
from src.config.settings import Settings
from src.domain.value_objects import EgressConfig
from src.domain.value_objects import EgressInfo
from src.domain.value_objects import EgressStatus

logger = structlog.get_logger()


class LiveKitEgressAdapter(EgressPort):
    """LiveKit Egress API adapter.

    Implements room composite egress recording with HLS segments
    output to S3-compatible storage (MinIO for dev, S3 for prod).
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the adapter with settings.

        Args:
            settings: Application settings containing LiveKit credentials.
        """
        self._settings = settings
        self._api: LiveKitAPI | None = None

    async def _get_api(self) -> LiveKitAPI:
        """Get or create the LiveKit API client.

        Returns:
            Initialized LiveKitAPI client.
        """
        if self._api is None:
            self._api = LiveKitAPI(
                url=self._settings.livekit_url,
                api_key=self._settings.livekit_api_key,
                api_secret=self._settings.livekit_api_secret.get_secret_value(),
            )
        return self._api

    async def start_room_composite(self, config: EgressConfig) -> EgressInfo:
        """Start a room composite egress recording.

        Creates a composite recording of all participants in the room
        with HLS segment output to S3.

        Args:
            config: Egress configuration with room name and output settings.

        Returns:
            EgressInfo containing the egress ID and initial status.

        Raises:
            EgressError: If the egress could not be started.
        """
        try:
            api = await self._get_api()

            # Build S3 path for HLS segments
            s3_prefix = f"s3://{config.output_bucket}/{config.output_path}"

            # Configure segmented file output for HLS
            # Include S3 upload config if using custom endpoint (MinIO)
            s3_config = None
            if self._settings.s3_endpoint_url:
                s3_config = _build_s3_upload_config(self._settings)

            segment_output = SegmentedFileOutput(
                filename_prefix=s3_prefix,
                playlist_name="index.m3u8",
                segment_duration=config.segment_duration,
                s3=s3_config,
            )

            request = RoomCompositeEgressRequest(
                room_name=config.room_name,
                segment_outputs=[segment_output],
            )

            logger.info(
                "starting_room_composite_egress",
                room_name=config.room_name,
                bucket=config.output_bucket,
                path=config.output_path,
            )

            result = await api.egress.start_room_composite_egress(request)
            egress_info = _convert_egress_info(result, config.room_name)

            logger.info(
                "egress_started",
                egress_id=egress_info.egress_id,
                room_name=config.room_name,
            )

            return egress_info

        except Exception as e:
            logger.error(
                "egress_start_failed",
                room_name=config.room_name,
                error=str(e),
            )
            raise EgressError(f"Failed to start egress for room {config.room_name}: {e}") from e

    async def stop_egress(self, egress_id: str) -> EgressInfo:
        """Stop an active egress recording.

        Args:
            egress_id: The egress ID to stop.

        Returns:
            EgressInfo with updated status.

        Raises:
            EgressError: If the egress could not be stopped.
            EgressNotFoundError: If the egress ID is not found.
        """
        try:
            api = await self._get_api()

            request = StopEgressRequest(egress_id=egress_id)

            logger.info("stopping_egress", egress_id=egress_id)

            result = await api.egress.stop_egress(request)
            egress_info = _convert_egress_info(result, result.room_name)

            logger.info(
                "egress_stopped",
                egress_id=egress_id,
                status=egress_info.status,
            )

            return egress_info

        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                raise EgressNotFoundError(f"Egress {egress_id} not found") from e

            logger.error(
                "egress_stop_failed",
                egress_id=egress_id,
                error=str(e),
            )
            raise EgressError(f"Failed to stop egress {egress_id}: {e}") from e

    async def get_egress_info(self, egress_id: str) -> EgressInfo | None:
        """Get information about an egress recording.

        Args:
            egress_id: The egress ID to query.

        Returns:
            EgressInfo with current status and metadata, or None if not found.

        Raises:
            EgressError: If the lookup fails.
        """
        try:
            api = await self._get_api()

            # List egress and find the one with matching ID
            request = ListEgressRequest(egress_id=egress_id)
            response = await api.egress.list_egress(request)

            if not response.items:
                return None

            result = response.items[0]
            return _convert_egress_info(result, result.room_name)

        except Exception as e:
            logger.error(
                "egress_info_failed",
                egress_id=egress_id,
                error=str(e),
            )
            raise EgressError(f"Failed to get egress info {egress_id}: {e}") from e

    async def close(self) -> None:
        """Close the adapter and release resources."""
        if self._api is not None:
            await self._api.aclose()  # type: ignore[no-untyped-call]
            self._api = None


def _build_s3_upload_config(settings: Settings) -> S3Upload:
    """Build S3 upload configuration for MinIO/S3.

    Args:
        settings: Application settings with S3 configuration.

    Returns:
        S3Upload configuration for LiveKit.
    """
    return S3Upload(
        access_key=settings.s3_access_key,
        secret=settings.s3_secret_key.get_secret_value(),
        region=settings.s3_region,
        endpoint=settings.s3_endpoint_url,
        force_path_style=True,  # Required for MinIO
    )


def _convert_egress_info(lk_info: LiveKitEgressInfo, room_name: str) -> EgressInfo:
    """Convert LiveKit EgressInfo to domain EgressInfo.

    Args:
        lk_info: LiveKit protocol EgressInfo.
        room_name: Room name for the egress.

    Returns:
        Domain EgressInfo value object.
    """
    status = _convert_status(lk_info.status)

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


def _convert_status(lk_status: LiveKitEgressStatus) -> EgressStatus:
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
