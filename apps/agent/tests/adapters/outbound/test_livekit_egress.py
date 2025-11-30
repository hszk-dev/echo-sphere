"""Unit tests for LiveKitEgressAdapter."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from livekit.protocol.egress import EgressStatus as LKStatus

from src.adapters.outbound.livekit_egress import LiveKitEgressAdapter
from src.adapters.outbound.livekit_egress import _convert_status
from src.application.ports.egress_port import EgressError
from src.application.ports.egress_port import EgressNotFoundError
from src.config.settings import Settings
from src.domain.value_objects import EgressConfig
from src.domain.value_objects import EgressStatus


@pytest.fixture
def mock_settings() -> Settings:
    """Create mock settings for testing."""
    settings = MagicMock(spec=Settings)
    settings.livekit_url = "ws://localhost:7880"
    settings.livekit_api_key = "devkey"
    settings.livekit_api_secret = MagicMock()
    settings.livekit_api_secret.get_secret_value.return_value = "secret"
    settings.s3_endpoint_url = "http://localhost:9000"
    settings.s3_access_key = "minioadmin"
    settings.s3_secret_key = MagicMock()
    settings.s3_secret_key.get_secret_value.return_value = "minioadmin"
    settings.s3_region = "us-east-1"
    return settings


@pytest.fixture
def adapter(mock_settings: Settings) -> LiveKitEgressAdapter:
    """Create LiveKitEgressAdapter instance for testing."""
    return LiveKitEgressAdapter(mock_settings)


@pytest.fixture
def egress_config() -> EgressConfig:
    """Create test egress configuration."""
    return EgressConfig(
        room_name="test-room",
        output_bucket="recordings",
        output_path="session-123",
        segment_duration=4,
    )


class TestStartRoomComposite:
    """Tests for start_room_composite method."""

    async def test_starts_egress_successfully(
        self,
        adapter: LiveKitEgressAdapter,
        egress_config: EgressConfig,
    ) -> None:
        """Should start room composite egress and return EgressInfo."""
        # Mock LiveKit API response
        mock_egress_info = MagicMock()
        mock_egress_info.egress_id = "egress-123"
        mock_egress_info.room_name = "test-room"
        mock_egress_info.status = 0  # EGRESS_STARTING
        mock_egress_info.started_at = 0
        mock_egress_info.ended_at = 0
        mock_egress_info.error = ""
        mock_egress_info.segment_results = []

        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.start_room_composite_egress.return_value = mock_egress_info
            mock_get_api.return_value = mock_api

            result = await adapter.start_room_composite(egress_config)

            assert result.egress_id == "egress-123"
            assert result.room_name == "test-room"
            assert result.status == EgressStatus.STARTING

    async def test_raises_egress_error_on_failure(
        self,
        adapter: LiveKitEgressAdapter,
        egress_config: EgressConfig,
    ) -> None:
        """Should raise EgressError when API call fails."""
        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.start_room_composite_egress.side_effect = Exception(
                "Connection failed"
            )
            mock_get_api.return_value = mock_api

            with pytest.raises(EgressError, match="Failed to start egress"):
                await adapter.start_room_composite(egress_config)


class TestStopEgress:
    """Tests for stop_egress method."""

    async def test_stops_egress_successfully(
        self, adapter: LiveKitEgressAdapter
    ) -> None:
        """Should stop egress and return updated EgressInfo."""
        mock_egress_info = MagicMock()
        mock_egress_info.egress_id = "egress-123"
        mock_egress_info.room_name = "test-room"
        mock_egress_info.status = 2  # EGRESS_ENDING
        mock_egress_info.started_at = 1000000000000000000  # 1 second in ns
        mock_egress_info.ended_at = 0
        mock_egress_info.error = ""
        mock_egress_info.segment_results = []

        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.stop_egress.return_value = mock_egress_info
            mock_get_api.return_value = mock_api

            result = await adapter.stop_egress("egress-123")

            assert result.egress_id == "egress-123"
            assert result.status == EgressStatus.ENDING

    async def test_raises_not_found_error(
        self, adapter: LiveKitEgressAdapter
    ) -> None:
        """Should raise EgressNotFoundError when egress not found."""
        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.stop_egress.side_effect = Exception(
                "egress not found"
            )
            mock_get_api.return_value = mock_api

            with pytest.raises(EgressNotFoundError, match="not found"):
                await adapter.stop_egress("missing-egress")


class TestGetEgressInfo:
    """Tests for get_egress_info method."""

    async def test_gets_egress_info_successfully(
        self, adapter: LiveKitEgressAdapter
    ) -> None:
        """Should return EgressInfo for existing egress."""
        mock_egress_info = MagicMock()
        mock_egress_info.egress_id = "egress-123"
        mock_egress_info.room_name = "test-room"
        mock_egress_info.status = 1  # EGRESS_ACTIVE
        mock_egress_info.started_at = 1000000000000000000
        mock_egress_info.ended_at = 0
        mock_egress_info.error = ""
        mock_egress_info.segment_results = []

        mock_response = MagicMock()
        mock_response.items = [mock_egress_info]

        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.list_egress.return_value = mock_response
            mock_get_api.return_value = mock_api

            result = await adapter.get_egress_info("egress-123")

            assert result is not None
            assert result.egress_id == "egress-123"
            assert result.status == EgressStatus.ACTIVE

    async def test_returns_none_when_empty_results(
        self, adapter: LiveKitEgressAdapter
    ) -> None:
        """Should return None when no results."""
        mock_response = MagicMock()
        mock_response.items = []

        with patch.object(adapter, "_get_api") as mock_get_api:
            mock_api = AsyncMock()
            mock_api.egress.list_egress.return_value = mock_response
            mock_get_api.return_value = mock_api

            result = await adapter.get_egress_info("missing-egress")
            assert result is None


class TestClose:
    """Tests for close method."""

    async def test_closes_api_client(self, adapter: LiveKitEgressAdapter) -> None:
        """Should close the API client when called."""
        mock_api = AsyncMock()
        adapter._api = mock_api

        await adapter.close()

        mock_api.aclose.assert_called_once()
        assert adapter._api is None

    async def test_handles_none_api(self, adapter: LiveKitEgressAdapter) -> None:
        """Should handle case when API was never initialized."""
        assert adapter._api is None

        # Should not raise
        await adapter.close()


class TestConvertStatus:
    """Tests for _convert_status helper function."""

    def test_converts_starting_to_starting(self) -> None:
        """EGRESS_STARTING should map to STARTING."""
        result = _convert_status(LKStatus.EGRESS_STARTING)
        assert result == EgressStatus.STARTING

    def test_converts_active_to_active(self) -> None:
        """EGRESS_ACTIVE should map to ACTIVE."""
        result = _convert_status(LKStatus.EGRESS_ACTIVE)
        assert result == EgressStatus.ACTIVE

    def test_converts_ending_to_ending(self) -> None:
        """EGRESS_ENDING should map to ENDING."""
        result = _convert_status(LKStatus.EGRESS_ENDING)
        assert result == EgressStatus.ENDING

    def test_converts_complete_to_complete(self) -> None:
        """EGRESS_COMPLETE should map to COMPLETE."""
        result = _convert_status(LKStatus.EGRESS_COMPLETE)
        assert result == EgressStatus.COMPLETE

    def test_converts_failed_to_failed(self) -> None:
        """EGRESS_FAILED should map to FAILED."""
        result = _convert_status(LKStatus.EGRESS_FAILED)
        assert result == EgressStatus.FAILED

    def test_converts_aborted_to_failed(self) -> None:
        """EGRESS_ABORTED should map to FAILED."""
        result = _convert_status(LKStatus.EGRESS_ABORTED)
        assert result == EgressStatus.FAILED
