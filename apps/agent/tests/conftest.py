"""Pytest configuration and shared fixtures.

This module provides:
- SQLite in-memory database for integration tests
- Transaction rollback pattern for test isolation
- Test client with dependency_overrides
- Common test fixtures and factories
"""

import asyncio
from collections.abc import AsyncIterator
from datetime import UTC
from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

from src.adapters.inbound.recording_api import create_recording_router
from src.adapters.outbound.database import Base
from src.adapters.outbound.postgres_recording import PostgresRecordingRepository
from src.application.ports import EgressPort
from src.application.ports import EgressStatus
from src.application.ports import StoragePort
from src.application.use_cases import RecordingService

# SQLite in-memory URL for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Return the default event loop policy for the session."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def test_engine() -> AsyncIterator[Any]:
    """Create a test database engine.

    Uses SQLite in-memory for fast tests without external dependencies.
    Creates all tables at start and disposes at end.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine: Any) -> AsyncIterator[AsyncSession]:
    """Create a test database session with transaction rollback.

    Each test runs in its own transaction that is rolled back at the end,
    ensuring complete test isolation without actual database changes.
    """
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
        # Roll back any changes made during the test
        await session.rollback()


@pytest.fixture
def recording_repository(db_session: AsyncSession) -> PostgresRecordingRepository:
    """Create a recording repository with the test session."""
    return PostgresRecordingRepository(db_session)


@pytest.fixture
def mock_egress_port() -> AsyncMock:
    """Create a mock egress port for tests.

    Returns a configured AsyncMock that can be used to control egress behavior
    and verify interactions in integration tests.
    """
    mock = AsyncMock(spec=EgressPort)
    return mock


@pytest.fixture
def mock_storage_port() -> AsyncMock:
    """Create a mock storage port for tests.

    Returns a configured AsyncMock for S3/storage operations.
    """
    mock = AsyncMock(spec=StoragePort)
    mock.generate_presigned_url.return_value = "https://cdn.example.com/presigned-url"
    return mock


@pytest.fixture
def recording_service(
    recording_repository: PostgresRecordingRepository,
    mock_egress_port: AsyncMock,
    mock_storage_port: AsyncMock,
) -> RecordingService:
    """Create a RecordingService with real repository and mocked external adapters.

    This provides realistic integration testing:
    - Real database operations via SQLite
    - Mocked external services (egress, storage)
    """
    return RecordingService(
        recording_repository=recording_repository,
        egress_port=mock_egress_port,
        storage_port=mock_storage_port,
        default_bucket="test-bucket",
        default_width=1280,
        default_height=720,
        default_segment_duration=4,
        presigned_url_expiry=3600,
    )


@pytest.fixture
async def test_app(recording_service: RecordingService) -> FastAPI:
    """Create a test FastAPI app with dependency overrides.

    The app uses the real RecordingService (with mocked external adapters)
    for realistic API testing.
    """
    app = FastAPI()

    def get_recording_service() -> RecordingService:
        return recording_service

    router = create_recording_router(get_recording_service)
    app.include_router(router)

    return app


@pytest.fixture
async def test_client(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Create an async test client for API testing.

    Uses HTTPX AsyncClient with ASGITransport for testing FastAPI apps.
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_egress_info() -> dict[str, Any]:
    """Provide sample egress info for testing."""
    return {
        "egress_id": "egress-test-123",
        "room_name": "test-room",
        "status": EgressStatus.STARTING,
    }


@pytest.fixture
def completed_egress_info() -> dict[str, Any]:
    """Provide completed egress info for testing."""
    return {
        "egress_id": "egress-test-123",
        "room_name": "test-room",
        "status": EgressStatus.COMPLETE,
        "started_at": datetime.now(UTC),
        "ended_at": datetime.now(UTC),
        "file_path": "s3://test-bucket/recordings/test/index.m3u8",
        "duration_seconds": 120,
        "file_size_bytes": 1024000,
    }
