"""Unit tests for Session entity."""

import pytest

from src.domain.entities.session import Session
from src.domain.entities.session import SessionStatus


class TestSession:
    """Tests for Session entity."""

    def test_create_session_with_defaults(self) -> None:
        """Session should be created with default values."""
        session = Session(room_name="test-room", user_id="user-123")

        assert session.room_name == "test-room"
        assert session.user_id == "user-123"
        assert session.status == SessionStatus.PENDING
        assert session.started_at is None
        assert session.ended_at is None

    def test_start_session(self) -> None:
        """Session should transition to active status when started."""
        session = Session(room_name="test-room", user_id="user-123")
        session.start()

        assert session.status == SessionStatus.ACTIVE
        assert session.started_at is not None

    def test_start_session_already_active_raises(self) -> None:
        """Starting an already active session should raise ValueError."""
        session = Session(room_name="test-room", user_id="user-123")
        session.start()

        with pytest.raises(ValueError, match="Cannot start session"):
            session.start()

    def test_complete_session(self) -> None:
        """Session should transition to completed status."""
        session = Session(room_name="test-room", user_id="user-123")
        session.start()
        session.complete()

        assert session.status == SessionStatus.COMPLETED
        assert session.ended_at is not None

    def test_complete_pending_session_raises(self) -> None:
        """Completing a pending session should raise ValueError."""
        session = Session(room_name="test-room", user_id="user-123")

        with pytest.raises(ValueError, match="Cannot complete session"):
            session.complete()

    def test_fail_session(self) -> None:
        """Session should transition to failed status."""
        session = Session(room_name="test-room", user_id="user-123")
        session.start()
        session.fail()

        assert session.status == SessionStatus.FAILED
        assert session.ended_at is not None

    def test_duration_seconds(self) -> None:
        """Session should calculate duration correctly."""
        session = Session(room_name="test-room", user_id="user-123")
        session.start()
        session.complete()

        duration = session.duration_seconds
        assert duration is not None
        assert duration >= 0

    def test_duration_seconds_incomplete(self) -> None:
        """Incomplete session should return None for duration."""
        session = Session(room_name="test-room", user_id="user-123")

        assert session.duration_seconds is None
