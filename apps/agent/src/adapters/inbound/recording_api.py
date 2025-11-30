"""Recording API endpoints.

This module provides REST API endpoints for:
- Listing recordings with pagination (#36)
- Generating playback URLs for recordings (#37)
"""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import structlog
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import status
from pydantic import BaseModel

from src.application.use_cases.recording_service import RecordingNotFoundError
from src.application.use_cases.recording_service import RecordingService
from src.application.use_cases.recording_service import RecordingServiceError
from src.domain.entities import Recording
from src.domain.entities import RecordingStatus

logger = structlog.get_logger()


class RecordingResponse(BaseModel):
    """Recording response model."""

    id: UUID
    session_id: UUID
    egress_id: str
    status: str
    storage_bucket: str
    storage_path: str
    playlist_url: str | None
    duration_seconds: int | None
    file_size_bytes: int | None
    error_message: str | None
    created_at: str
    updated_at: str

    @classmethod
    def from_entity(cls, recording: Recording) -> "RecordingResponse":
        """Create response from Recording entity.

        Args:
            recording: Recording domain entity.

        Returns:
            RecordingResponse instance.
        """
        return cls(
            id=recording.id,
            session_id=recording.session_id,
            egress_id=recording.egress_id,
            status=recording.status.value,
            storage_bucket=recording.storage_bucket,
            storage_path=recording.storage_path,
            playlist_url=recording.playlist_url,
            duration_seconds=recording.duration_seconds,
            file_size_bytes=recording.file_size_bytes,
            error_message=recording.error_message,
            created_at=recording.created_at.isoformat(),
            updated_at=recording.updated_at.isoformat(),
        )


class RecordingListResponse(BaseModel):
    """Recording list response with pagination."""

    items: list[RecordingResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PlaybackUrlResponse(BaseModel):
    """Playback URL response."""

    recording_id: UUID
    playback_url: str
    expires_in_seconds: int


def create_recording_router(
    get_recording_service: Callable[..., Any],
) -> APIRouter:
    """Create recording API router with dependency injection.

    Args:
        get_recording_service: Dependency function to get RecordingService.

    Returns:
        Configured APIRouter with recording endpoints.
    """
    router = APIRouter(prefix="/api/v1/recordings", tags=["recordings"])

    @router.get("", response_model=RecordingListResponse)
    async def list_recordings(
        page: int = Query(1, ge=1, description="Page number (1-indexed)"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        status_filter: RecordingStatus | None = Query(
            None, alias="status", description="Filter by status"
        ),
        recording_service: RecordingService = Depends(get_recording_service),
    ) -> RecordingListResponse:
        """List recordings with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status_filter: Optional status filter.
            recording_service: Injected recording service.

        Returns:
            Paginated list of recordings.
        """
        logger.debug(
            "listing_recordings",
            page=page,
            page_size=page_size,
            status=status_filter.value if status_filter else None,
        )

        try:
            # Get recordings via service method
            recordings, total = await recording_service.list_recordings(
                page=page,
                page_size=page_size,
                status=status_filter,
            )

            # Calculate pagination info
            total_pages = (total + page_size - 1) // page_size if total > 0 else 1

            return RecordingListResponse(
                items=[RecordingResponse.from_entity(r) for r in recordings],
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            )

        except Exception as e:
            logger.error("list_recordings_failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list recordings: {e}",
            ) from e

    @router.get("/session/{session_id}", response_model=RecordingResponse)
    async def get_recording_by_session(
        session_id: UUID,
        recording_service: RecordingService = Depends(get_recording_service),
    ) -> RecordingResponse:
        """Get recording by session ID.

        Args:
            session_id: The session UUID.
            recording_service: Injected recording service.

        Returns:
            Recording details.
        """
        logger.debug("getting_recording_by_session", session_id=str(session_id))

        recording = await recording_service.get_recording_by_session(session_id)
        if recording is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recording for session {session_id} not found",
            )

        return RecordingResponse.from_entity(recording)

    @router.get("/{recording_id}", response_model=RecordingResponse)
    async def get_recording(
        recording_id: UUID,
        recording_service: RecordingService = Depends(get_recording_service),
    ) -> RecordingResponse:
        """Get a single recording by ID.

        Args:
            recording_id: The recording UUID.
            recording_service: Injected recording service.

        Returns:
            Recording details.
        """
        logger.debug("getting_recording", recording_id=str(recording_id))

        recording = await recording_service.get_recording(recording_id)
        if recording is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recording {recording_id} not found",
            )

        return RecordingResponse.from_entity(recording)

    @router.get("/{recording_id}/playback-url", response_model=PlaybackUrlResponse)
    async def get_playback_url(
        recording_id: UUID,
        expiry_seconds: int = Query(
            3600, ge=60, le=86400, description="URL expiry time in seconds"
        ),
        recording_service: RecordingService = Depends(get_recording_service),
    ) -> PlaybackUrlResponse:
        """Generate presigned playback URL for a recording.

        Args:
            recording_id: The recording UUID.
            expiry_seconds: URL expiry time (60-86400 seconds).
            recording_service: Injected recording service.

        Returns:
            Playback URL with expiry information.
        """
        logger.debug(
            "generating_playback_url",
            recording_id=str(recording_id),
            expiry_seconds=expiry_seconds,
        )

        try:
            url = await recording_service.get_playback_url(
                recording_id=recording_id,
                expiry_seconds=expiry_seconds,
            )

            return PlaybackUrlResponse(
                recording_id=recording_id,
                playback_url=url,
                expires_in_seconds=expiry_seconds,
            )

        except RecordingNotFoundError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        except RecordingServiceError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            ) from e
        except Exception as e:
            logger.error(
                "playback_url_generation_failed",
                recording_id=str(recording_id),
                error=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate playback URL: {e}",
            ) from e

    return router
