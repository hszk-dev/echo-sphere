"""PostgreSQL implementation of RecordingRepositoryPort."""

from uuid import UUID

import structlog
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.outbound.database import RecordingModel
from src.application.ports import RecordingRepositoryPort
from src.domain.entities import Recording
from src.domain.entities import RecordingStatus

logger = structlog.get_logger()


class PostgresRecordingRepository(RecordingRepositoryPort):
    """PostgreSQL implementation of recording repository.

    This adapter handles persistence of recordings to PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save(self, recording: Recording) -> None:
        """Save or update a recording.

        Args:
            recording: The recording to save.
        """
        model = await self._session.get(RecordingModel, recording.id)
        if model is None:
            model = RecordingModel(
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
                created_at=recording.created_at,
                updated_at=recording.updated_at,
                started_at=recording.started_at,
                ended_at=recording.ended_at,
            )
            self._session.add(model)
        else:
            model.status = recording.status.value
            model.playlist_url = recording.playlist_url
            model.duration_seconds = recording.duration_seconds
            model.file_size_bytes = recording.file_size_bytes
            model.error_message = recording.error_message
            model.updated_at = recording.updated_at
            model.started_at = recording.started_at
            model.ended_at = recording.ended_at

        await self._session.commit()
        logger.debug(
            "recording_saved",
            recording_id=str(recording.id),
            status=recording.status.value,
        )

    async def get_by_id(self, recording_id: UUID) -> Recording | None:
        """Retrieve a recording by ID.

        Args:
            recording_id: The recording ID to look up.

        Returns:
            The recording if found, None otherwise.
        """
        model = await self._session.get(RecordingModel, recording_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_session_id(self, session_id: UUID) -> Recording | None:
        """Retrieve a recording by session ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The recording if found, None otherwise.
        """
        stmt = (
            select(RecordingModel)
            .where(RecordingModel.session_id == session_id)
            .order_by(RecordingModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_by_egress_id(self, egress_id: str) -> Recording | None:
        """Retrieve a recording by egress ID.

        Args:
            egress_id: The LiveKit egress ID.

        Returns:
            The recording if found, None otherwise.
        """
        stmt = select(RecordingModel).where(RecordingModel.egress_id == egress_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recording]:
        """List recordings by status.

        Args:
            status: The recording status to filter by.
            limit: Maximum number of recordings to return.
            offset: Number of recordings to skip.

        Returns:
            List of recordings with the specified status.
        """
        stmt = (
            select(RecordingModel)
            .where(RecordingModel.status == status)
            .order_by(RecordingModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Recording], int]:
        """List all recordings with pagination.

        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.

        Returns:
            Tuple of (recordings list, total count).
        """
        # Count query
        count_stmt = select(func.count()).select_from(RecordingModel)
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Data query with pagination
        offset = (page - 1) * page_size
        stmt = (
            select(RecordingModel)
            .order_by(RecordingModel.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models], total

    def _model_to_entity(self, model: RecordingModel) -> Recording:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: The SQLAlchemy recording model.

        Returns:
            The domain Recording entity.
        """
        return Recording(
            id=model.id,
            session_id=model.session_id,
            egress_id=model.egress_id,
            status=RecordingStatus(model.status),
            storage_bucket=model.storage_bucket,
            storage_path=model.storage_path,
            playlist_url=model.playlist_url,
            duration_seconds=model.duration_seconds,
            file_size_bytes=model.file_size_bytes,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
            started_at=model.started_at,
            ended_at=model.ended_at,
        )
