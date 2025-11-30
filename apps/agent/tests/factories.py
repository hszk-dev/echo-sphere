"""Test data factories using Polyfactory.

Provides factory classes for generating test data consistently
across all tests. Uses Polyfactory for automatic data generation.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Any
from uuid import UUID
from uuid import uuid4

from polyfactory.factories import DataclassFactory

from src.domain.entities import Recording
from src.domain.entities import RecordingStatus
from src.domain.value_objects import EgressInfo
from src.domain.value_objects import EgressStatus


class RecordingFactory(DataclassFactory[Recording]):
    """Factory for creating Recording test instances."""

    __model__ = Recording

    @classmethod
    def session_id(cls) -> UUID:
        """Generate a unique session ID."""
        return uuid4()

    @classmethod
    def egress_id(cls) -> str:
        """Generate a unique egress ID."""
        return f"egress-{uuid4().hex[:12]}"

    @classmethod
    def storage_bucket(cls) -> str:
        """Return default test bucket."""
        return "test-bucket"

    @classmethod
    def storage_path(cls) -> str:
        """Generate a storage path."""
        return f"recordings/{uuid4().hex[:8]}"

    @classmethod
    def status(cls) -> RecordingStatus:
        """Return default STARTING status."""
        return RecordingStatus.STARTING

    @classmethod
    def created_at(cls) -> datetime:
        """Return current UTC time."""
        return datetime.now(UTC)

    @classmethod
    def updated_at(cls) -> datetime:
        """Return current UTC time."""
        return datetime.now(UTC)

    @classmethod
    def build_starting(cls, **kwargs: Any) -> Recording:
        """Build a recording in STARTING state."""
        return cls.build(status=RecordingStatus.STARTING, **kwargs)

    @classmethod
    def build_active(cls, **kwargs: Any) -> Recording:
        """Build a recording in ACTIVE state."""
        recording = cls.build(status=RecordingStatus.STARTING, **kwargs)
        recording.activate()
        return recording

    @classmethod
    def build_processing(cls, **kwargs: Any) -> Recording:
        """Build a recording in PROCESSING state."""
        recording = cls.build_active(**kwargs)
        recording.start_processing()
        return recording

    @classmethod
    def build_completed(cls, **kwargs: Any) -> Recording:
        """Build a recording in COMPLETED state."""
        recording = cls.build_processing(**kwargs)
        recording.complete(
            playlist_url="https://cdn.example.com/playlist.m3u8",
            duration_seconds=120,
            file_size_bytes=1024000,
        )
        return recording

    @classmethod
    def build_failed(cls, error_message: str = "Test error", **kwargs: Any) -> Recording:
        """Build a recording in FAILED state."""
        recording = cls.build(status=RecordingStatus.STARTING, **kwargs)
        recording.fail(error_message)
        return recording


class EgressInfoFactory(DataclassFactory[EgressInfo]):
    """Factory for creating EgressInfo test instances."""

    __model__ = EgressInfo

    @classmethod
    def egress_id(cls) -> str:
        """Generate a unique egress ID."""
        return f"egress-{uuid4().hex[:12]}"

    @classmethod
    def room_name(cls) -> str:
        """Generate a room name."""
        return f"room-{uuid4().hex[:8]}"

    @classmethod
    def status(cls) -> EgressStatus:
        """Return default STARTING status."""
        return EgressStatus.STARTING

    @classmethod
    def build_starting(cls, **kwargs: Any) -> EgressInfo:
        """Build an egress info in STARTING state."""
        return cls.build(status=EgressStatus.STARTING, **kwargs)

    @classmethod
    def build_active(cls, **kwargs: Any) -> EgressInfo:
        """Build an egress info in ACTIVE state."""
        return cls.build(
            status=EgressStatus.ACTIVE,
            started_at=datetime.now(UTC),
            **kwargs,
        )

    @classmethod
    def build_complete(cls, **kwargs: Any) -> EgressInfo:
        """Build an egress info in COMPLETE state."""
        now = datetime.now(UTC)
        return cls.build(
            status=EgressStatus.COMPLETE,
            started_at=now - timedelta(minutes=5),
            ended_at=now,
            file_path="s3://test-bucket/recordings/test/index.m3u8",
            duration_seconds=300,
            file_size_bytes=5000000,
            **kwargs,
        )

    @classmethod
    def build_failed(cls, error: str = "Egress failed", **kwargs: Any) -> EgressInfo:
        """Build an egress info in FAILED state."""
        return cls.build(
            status=EgressStatus.FAILED,
            error=error,
            **kwargs,
        )


def create_test_session_id() -> UUID:
    """Create a new test session ID."""
    return uuid4()


def create_test_recording(
    session_id: UUID | None = None,
    status: RecordingStatus = RecordingStatus.STARTING,
    **kwargs: Any,
) -> Recording:
    """Create a test recording with optional overrides.

    Args:
        session_id: Optional session ID, generates one if not provided.
        status: Recording status to use.
        **kwargs: Additional overrides for the factory.

    Returns:
        A Recording instance in the specified state.
    """
    if session_id is None:
        session_id = uuid4()

    if status == RecordingStatus.STARTING:
        return RecordingFactory.build_starting(session_id=session_id, **kwargs)
    elif status == RecordingStatus.ACTIVE:
        return RecordingFactory.build_active(session_id=session_id, **kwargs)
    elif status == RecordingStatus.PROCESSING:
        return RecordingFactory.build_processing(session_id=session_id, **kwargs)
    elif status == RecordingStatus.COMPLETED:
        return RecordingFactory.build_completed(session_id=session_id, **kwargs)
    else:  # RecordingStatus.FAILED
        return RecordingFactory.build_failed(session_id=session_id, **kwargs)


def create_test_egress_info(
    egress_id: str | None = None,
    room_name: str | None = None,
    status: EgressStatus = EgressStatus.STARTING,
) -> EgressInfo:
    """Create a test egress info with optional overrides.

    Args:
        egress_id: Optional egress ID, generates one if not provided.
        room_name: Optional room name, generates one if not provided.
        status: Egress status to use.

    Returns:
        An EgressInfo instance in the specified state.
    """
    kwargs: dict[str, Any] = {}
    if egress_id:
        kwargs["egress_id"] = egress_id
    if room_name:
        kwargs["room_name"] = room_name

    if status == EgressStatus.STARTING:
        return EgressInfoFactory.build_starting(**kwargs)
    elif status == EgressStatus.ACTIVE:
        return EgressInfoFactory.build_active(**kwargs)
    elif status == EgressStatus.COMPLETE:
        return EgressInfoFactory.build_complete(**kwargs)
    elif status == EgressStatus.FAILED:
        return EgressInfoFactory.build_failed(**kwargs)
    else:
        return EgressInfoFactory.build(status=status, **kwargs)
