"""Tests for LiveKit webhook handler.

Tests the webhook processing logic including egress events
and recording status updates.
"""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo
from livekit.protocol.egress import EgressStatus as LiveKitEgressStatus
from livekit.protocol.webhook import WebhookEvent

from src.adapters.inbound.webhook_handler import WebhookHandler
from src.adapters.inbound.webhook_handler import create_webhook_receiver
from src.application.use_cases import RecordingService
from src.domain.value_objects import EgressStatus
from tests.factories import RecordingFactory


class TestWebhookHandler:
    """Tests for WebhookHandler class."""

    @pytest.fixture
    def mock_webhook_receiver(self) -> MagicMock:
        """Create a mock webhook receiver."""
        return MagicMock()

    @pytest.fixture
    def webhook_handler(self, mock_webhook_receiver: MagicMock) -> WebhookHandler:
        """Create a WebhookHandler with mocked receiver."""
        return WebhookHandler(mock_webhook_receiver)

    @pytest.fixture
    def mock_recording_service(self) -> AsyncMock:
        """Create a mock recording service."""
        return AsyncMock(spec=RecordingService)

    def _create_mock_webhook_event(
        self,
        event_type: str,
        egress_id: str = "egress-123",
        egress_status: LiveKitEgressStatus = LiveKitEgressStatus.EGRESS_ACTIVE,
    ) -> MagicMock:
        """Create a mock webhook event."""
        event = MagicMock(spec=WebhookEvent)
        event.event = event_type
        event.id = f"event-{uuid4().hex[:8]}"

        egress_info = MagicMock(spec=LiveKitEgressInfo)
        egress_info.egress_id = egress_id
        egress_info.room_name = "test-room"
        egress_info.status = egress_status
        egress_info.started_at = 1700000000000000000  # nanoseconds
        egress_info.ended_at = 0
        egress_info.error = ""
        egress_info.segment_results = []

        event.egress_info = egress_info
        return event

    @pytest.mark.asyncio
    async def test_handle_webhook_egress_started(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """egress_started event should update recording to ACTIVE."""
        event = self._create_mock_webhook_event(
            "egress_started",
            egress_status=LiveKitEgressStatus.EGRESS_ACTIVE,
        )
        mock_webhook_receiver.receive.return_value = event

        # Create a recording to return from service
        recording = RecordingFactory.build_active(egress_id="egress-123")
        mock_recording_service.handle_egress_event.return_value = recording

        result = await webhook_handler.handle_webhook(
            body='{"event": "egress_started"}',
            auth_token="test-token",
            recording_service=mock_recording_service,
        )

        assert result == {"status": "ok"}
        mock_recording_service.handle_egress_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_egress_ended_complete(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """egress_ended event with COMPLETE status should finalize recording."""
        event = self._create_mock_webhook_event(
            "egress_ended",
            egress_status=LiveKitEgressStatus.EGRESS_COMPLETE,
        )
        mock_webhook_receiver.receive.return_value = event

        recording = RecordingFactory.build_completed(egress_id="egress-123")
        mock_recording_service.handle_egress_event.return_value = recording

        result = await webhook_handler.handle_webhook(
            body='{"event": "egress_ended"}',
            auth_token="test-token",
            recording_service=mock_recording_service,
        )

        assert result == {"status": "ok"}
        mock_recording_service.handle_egress_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_egress_ended_failed(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """egress_ended event with FAILED status should mark recording as failed."""
        event = self._create_mock_webhook_event(
            "egress_ended",
            egress_status=LiveKitEgressStatus.EGRESS_FAILED,
        )
        event.egress_info.error = "Network error"
        mock_webhook_receiver.receive.return_value = event

        recording = RecordingFactory.build_failed(egress_id="egress-123")
        mock_recording_service.handle_egress_event.return_value = recording

        result = await webhook_handler.handle_webhook(
            body='{"event": "egress_ended"}',
            auth_token="test-token",
            recording_service=mock_recording_service,
        )

        assert result == {"status": "ok"}
        mock_recording_service.handle_egress_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_webhook_non_egress_event(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """Non-egress events should be acknowledged but not processed."""
        event = MagicMock()
        event.event = "room_started"
        event.id = "event-123"
        mock_webhook_receiver.receive.return_value = event

        result = await webhook_handler.handle_webhook(
            body='{"event": "room_started"}',
            auth_token="test-token",
            recording_service=mock_recording_service,
        )

        assert result == {"status": "ok"}
        mock_recording_service.handle_egress_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_webhook_verification_failure(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """Invalid webhook should raise HTTPException."""
        mock_webhook_receiver.receive.side_effect = Exception("Invalid signature")

        with pytest.raises(HTTPException) as exc_info:
            await webhook_handler.handle_webhook(
                body="invalid",
                auth_token="bad-token",
                recording_service=mock_recording_service,
            )

        assert exc_info.value.status_code == 400
        assert "Webhook processing failed" in exc_info.value.detail


class TestWebhookReceiverCreation:
    """Tests for webhook receiver factory function."""

    def test_create_webhook_receiver(self) -> None:
        """Should create a properly configured WebhookReceiver."""
        receiver = create_webhook_receiver(
            api_key="test-api-key",
            api_secret="test-api-secret",
        )

        # Verify receiver was created (it's a LiveKit SDK object)
        assert receiver is not None


class TestEgressStatusMapping:
    """Tests for egress status to recording status mapping."""

    @pytest.fixture
    def mock_webhook_receiver(self) -> MagicMock:
        """Create a mock webhook receiver."""
        return MagicMock()

    @pytest.fixture
    def webhook_handler(self, mock_webhook_receiver: MagicMock) -> WebhookHandler:
        """Create a WebhookHandler with mocked receiver."""
        return WebhookHandler(mock_webhook_receiver)

    @pytest.fixture
    def mock_recording_service(self) -> AsyncMock:
        """Create a mock recording service."""
        return AsyncMock(spec=RecordingService)

    @pytest.mark.asyncio
    async def test_egress_aborted_maps_to_failed(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """EGRESS_ABORTED status should map to FAILED."""
        event = MagicMock()
        event.event = "egress_ended"
        event.id = "event-123"

        egress_info = MagicMock(spec=LiveKitEgressInfo)
        egress_info.egress_id = "egress-123"
        egress_info.room_name = "test-room"
        egress_info.status = LiveKitEgressStatus.EGRESS_ABORTED
        egress_info.started_at = 0
        egress_info.ended_at = 0
        egress_info.error = "User aborted"
        egress_info.segment_results = []
        event.egress_info = egress_info

        mock_webhook_receiver.receive.return_value = event
        mock_recording_service.handle_egress_event.return_value = RecordingFactory.build_failed()

        await webhook_handler.handle_webhook(
            body="{}",
            auth_token="token",
            recording_service=mock_recording_service,
        )

        # Verify the egress_info passed to service has FAILED status
        call_args = mock_recording_service.handle_egress_event.call_args[0][0]
        assert call_args.status == EgressStatus.FAILED

    @pytest.mark.asyncio
    async def test_egress_limit_reached_maps_to_failed(
        self,
        webhook_handler: WebhookHandler,
        mock_webhook_receiver: MagicMock,
        mock_recording_service: AsyncMock,
    ) -> None:
        """EGRESS_LIMIT_REACHED status should map to FAILED."""
        event = MagicMock()
        event.event = "egress_ended"
        event.id = "event-123"

        egress_info = MagicMock(spec=LiveKitEgressInfo)
        egress_info.egress_id = "egress-123"
        egress_info.room_name = "test-room"
        egress_info.status = LiveKitEgressStatus.EGRESS_LIMIT_REACHED
        egress_info.started_at = 0
        egress_info.ended_at = 0
        egress_info.error = "Limit reached"
        egress_info.segment_results = []
        event.egress_info = egress_info

        mock_webhook_receiver.receive.return_value = event
        mock_recording_service.handle_egress_event.return_value = RecordingFactory.build_failed()

        await webhook_handler.handle_webhook(
            body="{}",
            auth_token="token",
            recording_service=mock_recording_service,
        )

        call_args = mock_recording_service.handle_egress_event.call_args[0][0]
        assert call_args.status == EgressStatus.FAILED
