"""LiveKit webhook handler for egress events.

This module handles incoming LiveKit webhook events, particularly
egress_ended and egress_started events for updating recording status.
"""

from datetime import UTC
from datetime import datetime

import structlog
from fastapi import HTTPException
from fastapi import status
from livekit.api import TokenVerifier
from livekit.api import WebhookReceiver
from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo
from livekit.protocol.egress import EgressStatus as LiveKitEgressStatus

from src.application.use_cases.recording_service import RecordingService
from src.domain.value_objects import EgressInfo
from src.domain.value_objects import EgressStatus

logger = structlog.get_logger()


def create_webhook_receiver(
    api_key: str,
    api_secret: str,
) -> WebhookReceiver:
    """Create a LiveKit WebhookReceiver for token verification.

    Args:
        api_key: LiveKit API key.
        api_secret: LiveKit API secret.

    Returns:
        Configured WebhookReceiver instance.
    """
    token_verifier = TokenVerifier(api_key=api_key, api_secret=api_secret)
    return WebhookReceiver(token_verifier)


class WebhookHandler:
    """Handler for LiveKit webhook events.

    Processes egress events and updates recording status via RecordingService.
    """

    def __init__(self, webhook_receiver: WebhookReceiver) -> None:
        """Initialize the webhook handler.

        Args:
            webhook_receiver: LiveKit webhook receiver for verification.
        """
        self._webhook_receiver = webhook_receiver

    async def handle_webhook(
        self,
        body: str,
        auth_token: str,
        recording_service: RecordingService,
    ) -> dict[str, str]:
        """Handle incoming LiveKit webhook.

        Args:
            body: Raw request body.
            auth_token: Authorization token from header.
            recording_service: Service for recording operations.

        Returns:
            Response indicating success.

        Raises:
            HTTPException: If verification fails or event processing errors.
        """
        try:
            # Verify and parse the webhook
            event = self._webhook_receiver.receive(body, auth_token)

            logger.info(
                "webhook_received",
                event_type=event.event,
                event_id=event.id,
            )

            # Handle egress events
            if event.event in ("egress_started", "egress_ended"):
                await self._handle_egress_event(event.egress_info, recording_service)

            return {"status": "ok"}

        except Exception as e:
            logger.error(
                "webhook_processing_failed",
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Webhook processing failed: {e}",
            ) from e

    async def _handle_egress_event(
        self,
        lk_egress_info: LiveKitEgressInfo,
        recording_service: RecordingService,
    ) -> None:
        """Handle egress webhook event.

        Args:
            lk_egress_info: LiveKit egress information.
            recording_service: Service for recording operations.
        """
        # Convert to domain EgressInfo
        egress_info = _convert_egress_info(lk_egress_info)

        logger.info(
            "processing_egress_event",
            egress_id=egress_info.egress_id,
            status=egress_info.status.value,
        )

        # Delegate to recording service
        await recording_service.handle_egress_event(egress_info)


def _convert_egress_info(lk_info: LiveKitEgressInfo) -> EgressInfo:
    """Convert LiveKit EgressInfo to domain EgressInfo.

    Args:
        lk_info: LiveKit protocol EgressInfo.

    Returns:
        Domain EgressInfo value object.
    """
    egress_status = _convert_status(lk_info.status)

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
        file_size_bytes = sum(
            segment.size for segment in lk_info.segment_results if segment.size
        )

    # Get duration from the egress info (convert to int)
    duration_seconds = None
    if lk_info.segment_results:
        for segment in lk_info.segment_results:
            if segment.duration:
                duration_seconds = int(segment.duration / 1e9)  # nanoseconds to seconds
                break

    return EgressInfo(
        egress_id=lk_info.egress_id,
        room_name=lk_info.room_name,
        status=egress_status,
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
