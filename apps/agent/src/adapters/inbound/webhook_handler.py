"""LiveKit webhook handler for egress events.

This module handles incoming LiveKit webhook events, particularly
egress_ended and egress_started events for updating recording status.
"""

import structlog
from fastapi import HTTPException
from fastapi import status
from livekit.api import TokenVerifier
from livekit.api import WebhookReceiver
from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo

from src.adapters.shared.livekit_converters import convert_egress_info
from src.application.use_cases.recording_service import RecordingService

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
        egress_info = convert_egress_info(lk_egress_info)

        logger.info(
            "processing_egress_event",
            egress_id=egress_info.egress_id,
            status=egress_info.status.value,
        )

        # Delegate to recording service
        await recording_service.handle_egress_event(egress_info)
