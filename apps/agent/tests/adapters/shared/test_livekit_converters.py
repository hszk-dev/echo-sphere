"""Unit tests for LiveKit converter functions.

Tests the conversion of LiveKit protocol objects to domain value objects.
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from livekit.protocol.egress import EgressInfo as LiveKitEgressInfo
from livekit.protocol.egress import EgressStatus as LiveKitEgressStatus

from src.adapters.shared.livekit_converters import convert_egress_info
from src.adapters.shared.livekit_converters import convert_egress_status
from src.domain.value_objects import EgressStatus


class TestConvertEgressStatus:
    """Tests for convert_egress_status function."""

    @pytest.mark.parametrize(
        "lk_status,expected_status",
        [
            (LiveKitEgressStatus.EGRESS_STARTING, EgressStatus.STARTING),
            (LiveKitEgressStatus.EGRESS_ACTIVE, EgressStatus.ACTIVE),
            (LiveKitEgressStatus.EGRESS_ENDING, EgressStatus.ENDING),
            (LiveKitEgressStatus.EGRESS_COMPLETE, EgressStatus.COMPLETE),
            (LiveKitEgressStatus.EGRESS_FAILED, EgressStatus.FAILED),
            (LiveKitEgressStatus.EGRESS_ABORTED, EgressStatus.FAILED),
            (LiveKitEgressStatus.EGRESS_LIMIT_REACHED, EgressStatus.FAILED),
        ],
    )
    def test_status_mapping(
        self,
        lk_status: LiveKitEgressStatus,
        expected_status: EgressStatus,
    ) -> None:
        """Each LiveKit status should map to correct domain status."""
        result = convert_egress_status(lk_status)
        assert result == expected_status

    def test_unknown_status_defaults_to_starting(self) -> None:
        """Unknown status values should default to STARTING."""
        # This tests the default case in the status map
        result = convert_egress_status(-1)  # type: ignore
        assert result == EgressStatus.STARTING


class TestConvertEgressInfo:
    """Tests for convert_egress_info function."""

    def _create_mock_egress_info(
        self,
        egress_id: str = "egress-123",
        room_name: str = "test-room",
        status: LiveKitEgressStatus = LiveKitEgressStatus.EGRESS_STARTING,
        started_at: int = 0,
        ended_at: int = 0,
        error: str = "",
        segment_results: list[Any] | None = None,
    ) -> MagicMock:
        """Create a mock LiveKit EgressInfo."""
        info = MagicMock(spec=LiveKitEgressInfo)
        info.egress_id = egress_id
        info.room_name = room_name
        info.status = status
        info.started_at = started_at
        info.ended_at = ended_at
        info.error = error
        info.segment_results = segment_results or []
        return info

    def test_basic_conversion(self) -> None:
        """Should convert basic egress info correctly."""
        lk_info = self._create_mock_egress_info(
            egress_id="egress-test",
            room_name="room-test",
            status=LiveKitEgressStatus.EGRESS_ACTIVE,
        )

        result = convert_egress_info(lk_info)

        assert result.egress_id == "egress-test"
        assert result.room_name == "room-test"
        assert result.status == EgressStatus.ACTIVE

    def test_room_name_override(self) -> None:
        """room_name parameter should override lk_info.room_name."""
        lk_info = self._create_mock_egress_info(room_name="original-room")

        result = convert_egress_info(lk_info, room_name="override-room")

        assert result.room_name == "override-room"

    def test_room_name_from_egress_info(self) -> None:
        """Should use lk_info.room_name when no override provided."""
        lk_info = self._create_mock_egress_info(room_name="original-room")

        result = convert_egress_info(lk_info)

        assert result.room_name == "original-room"

    def test_timestamp_conversion(self) -> None:
        """Nanosecond timestamps should be converted to datetime."""
        # 1700000000 seconds = 2023-11-14 22:13:20 UTC
        started_ns = 1700000000 * 1_000_000_000  # nanoseconds
        ended_ns = 1700000060 * 1_000_000_000  # 60 seconds later

        lk_info = self._create_mock_egress_info(
            started_at=started_ns,
            ended_at=ended_ns,
        )

        result = convert_egress_info(lk_info)

        assert result.started_at is not None
        assert result.ended_at is not None
        # Verify the timestamps are close to expected values
        assert result.started_at.year == 2023
        assert result.started_at.month == 11
        assert (result.ended_at - result.started_at).seconds == 60

    def test_zero_timestamps_become_none(self) -> None:
        """Zero timestamp values should be converted to None."""
        lk_info = self._create_mock_egress_info(started_at=0, ended_at=0)

        result = convert_egress_info(lk_info)

        assert result.started_at is None
        assert result.ended_at is None

    def test_error_extraction(self) -> None:
        """Error message should be extracted correctly."""
        lk_info = self._create_mock_egress_info(
            status=LiveKitEgressStatus.EGRESS_FAILED,
            error="Network timeout",
        )

        result = convert_egress_info(lk_info)

        assert result.error == "Network timeout"

    def test_empty_error_becomes_none(self) -> None:
        """Empty error string should become None."""
        lk_info = self._create_mock_egress_info(error="")

        result = convert_egress_info(lk_info)

        assert result.error is None

    def test_segment_results_file_path(self) -> None:
        """Should extract playlist location from segment results."""
        segment = MagicMock()
        segment.playlist_location = "s3://bucket/path/index.m3u8"
        segment.size = 1024
        segment.duration = 120 * 1_000_000_000  # 120 seconds in nanoseconds

        lk_info = self._create_mock_egress_info(segment_results=[segment])

        result = convert_egress_info(lk_info)

        assert result.file_path == "s3://bucket/path/index.m3u8"
        assert result.file_size_bytes == 1024
        assert result.duration_seconds == 120

    def test_multiple_segment_results(self) -> None:
        """Should sum file sizes from multiple segments."""
        segment1 = MagicMock()
        segment1.playlist_location = "s3://bucket/path/index.m3u8"
        segment1.size = 1000
        segment1.duration = 60 * 1_000_000_000

        segment2 = MagicMock()
        segment2.playlist_location = ""
        segment2.size = 500
        segment2.duration = 0

        lk_info = self._create_mock_egress_info(segment_results=[segment1, segment2])

        result = convert_egress_info(lk_info)

        assert result.file_path == "s3://bucket/path/index.m3u8"
        assert result.file_size_bytes == 1500
        assert result.duration_seconds == 60

    def test_empty_segment_results(self) -> None:
        """Empty segment results should yield None values."""
        lk_info = self._create_mock_egress_info(segment_results=[])

        result = convert_egress_info(lk_info)

        assert result.file_path is None
        assert result.file_size_bytes is None
        assert result.duration_seconds is None

    def test_complete_egress_info(self) -> None:
        """Should convert a complete egress info with all fields."""
        segment = MagicMock()
        segment.playlist_location = "s3://bucket/recordings/test/index.m3u8"
        segment.size = 5000000
        segment.duration = 300 * 1_000_000_000  # 5 minutes

        lk_info = self._create_mock_egress_info(
            egress_id="egress-complete-test",
            room_name="complete-room",
            status=LiveKitEgressStatus.EGRESS_COMPLETE,
            started_at=1700000000 * 1_000_000_000,
            ended_at=1700000300 * 1_000_000_000,
            error="",
            segment_results=[segment],
        )

        result = convert_egress_info(lk_info, room_name="override-room")

        assert result.egress_id == "egress-complete-test"
        assert result.room_name == "override-room"
        assert result.status == EgressStatus.COMPLETE
        assert result.started_at is not None
        assert result.ended_at is not None
        assert result.error is None
        assert result.file_path == "s3://bucket/recordings/test/index.m3u8"
        assert result.duration_seconds == 300
        assert result.file_size_bytes == 5000000
