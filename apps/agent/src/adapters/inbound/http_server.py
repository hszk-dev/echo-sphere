"""FastAPI HTTP server for Recording API and webhooks.

This module provides the HTTP API server for:
- LiveKit webhook handling
- Recording list and playback URL APIs
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import APIRouter
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.inbound.recording_api import create_recording_router
from src.adapters.inbound.webhook_handler import WebhookHandler
from src.adapters.inbound.webhook_handler import create_webhook_receiver
from src.adapters.outbound import Database
from src.adapters.outbound import LiveKitEgressAdapter
from src.adapters.outbound import PostgresRecordingRepository
from src.adapters.outbound import S3StorageAdapter
from src.application.use_cases.recording_service import RecordingService
from src.config.settings import Settings
from src.config.settings import get_settings

logger = structlog.get_logger()


class AppState:
    """Application state holder for shared resources."""

    database: Database | None = None
    egress_adapter: LiveKitEgressAdapter | None = None
    storage_adapter: S3StorageAdapter | None = None
    settings: Settings | None = None


# Global app state instance
_app_state = AppState()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session dependency.

    Yields:
        AsyncSession for database operations.
    """
    if _app_state.database is None:
        raise RuntimeError("Database not initialized")
    async with _app_state.database.get_session() as session:
        yield session


async def get_recording_service(
    session: AsyncSession = Depends(get_db_session),
) -> RecordingService:
    """Get RecordingService dependency with per-request session.

    Args:
        session: Database session from dependency injection.

    Returns:
        RecordingService configured for this request.
    """
    if (
        _app_state.settings is None
        or _app_state.egress_adapter is None
        or _app_state.storage_adapter is None
    ):
        raise RuntimeError("Application not initialized")

    recording_repo = PostgresRecordingRepository(session)

    return RecordingService(
        recording_repository=recording_repo,
        egress_port=_app_state.egress_adapter,
        storage_port=_app_state.storage_adapter,
        default_bucket=_app_state.settings.s3_bucket_recordings,
        default_width=_app_state.settings.egress_output_width,
        default_height=_app_state.settings.egress_output_height,
        default_segment_duration=_app_state.settings.egress_segment_duration,
        presigned_url_expiry=_app_state.settings.presigned_url_expiry_seconds,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings override for testing.

    Returns:
        Configured FastAPI application.
    """
    if settings is None:
        settings = get_settings()

    # Store settings in global state
    _app_state.settings = settings

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """Manage application lifecycle."""
        logger.info("starting_http_server", host=settings.http_host, port=settings.http_port)

        # Initialize shared resources
        _app_state.database = Database(settings.database_url)
        _app_state.egress_adapter = LiveKitEgressAdapter(settings)
        _app_state.storage_adapter = S3StorageAdapter(settings)

        logger.info("http_server_started")

        yield

        # Cleanup
        logger.info("stopping_http_server")
        if _app_state.egress_adapter:
            await _app_state.egress_adapter.close()
        if _app_state.database:
            await _app_state.database.close()
        logger.info("http_server_stopped")

    app = FastAPI(
        title="EchoSphere Recording API",
        description="Recording management and webhook API for EchoSphere",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register routes
    _register_routes(app, settings)

    return app


def _register_routes(app: FastAPI, settings: Settings) -> None:
    """Register all API routes.

    Args:
        app: FastAPI application.
        settings: Application settings.
    """
    # Create webhook receiver (stateless, can be shared)
    webhook_receiver = create_webhook_receiver(
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret.get_secret_value(),
    )

    # Create webhook handler with dependency injection
    webhook_handler = WebhookHandler(webhook_receiver)

    # Register webhook routes
    webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

    @webhook_router.post("/livekit")
    async def handle_livekit_webhook(
        request: Request,
        authorization: str = Header(..., alias="Authorization"),
        recording_service: RecordingService = Depends(get_recording_service),
    ) -> dict[str, str]:
        """Handle LiveKit webhook events."""
        body = await request.body()
        return await webhook_handler.handle_webhook(
            body.decode("utf-8"),
            authorization,
            recording_service,
        )

    app.include_router(webhook_router)

    # Register recording API routes
    recording_router = create_recording_router(get_recording_service)
    app.include_router(recording_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "healthy"}


def run_server(settings: Settings | None = None) -> None:
    """Run the HTTP server.

    Args:
        settings: Optional settings override.
    """
    if settings is None:
        settings = get_settings()

    app = create_app(settings)

    uvicorn.run(
        app,
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run_server()
