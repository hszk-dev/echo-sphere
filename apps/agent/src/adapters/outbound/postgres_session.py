"""PostgreSQL implementation of SessionRepositoryPort."""

from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.adapters.outbound.database import MessageModel
from src.adapters.outbound.database import SessionModel
from src.application.ports import SessionRepositoryPort
from src.domain.entities import Message
from src.domain.entities import MessageRole
from src.domain.entities import Session
from src.domain.entities import SessionStatus

logger = structlog.get_logger()


class PostgresSessionRepository(SessionRepositoryPort):
    """PostgreSQL implementation of session repository.

    This adapter handles persistence of sessions and messages to PostgreSQL.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with a database session.

        Args:
            session: SQLAlchemy async session.
        """
        self._session = session

    async def save_session(self, session: Session) -> None:
        """Save or update a session.

        Args:
            session: The session to save.
        """
        model = await self._session.get(SessionModel, session.id)
        if model is None:
            model = SessionModel(
                id=session.id,
                room_name=session.room_name,
                user_id=session.user_id,
                status=session.status.value,
                created_at=session.created_at,
                started_at=session.started_at,
                ended_at=session.ended_at,
            )
            self._session.add(model)
        else:
            model.status = session.status.value
            model.started_at = session.started_at
            model.ended_at = session.ended_at

        await self._session.commit()
        logger.debug("session_saved", session_id=str(session.id), status=session.status.value)

    async def get_session(self, session_id: UUID) -> Session | None:
        """Retrieve a session by ID.

        Args:
            session_id: The session ID to look up.

        Returns:
            The session if found, None otherwise.
        """
        model = await self._session.get(SessionModel, session_id)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def get_session_by_room(self, room_name: str) -> Session | None:
        """Retrieve a session by room name.

        Args:
            room_name: The LiveKit room name.

        Returns:
            The session if found, None otherwise.
        """
        stmt = (
            select(SessionModel)
            .where(SessionModel.room_name == room_name)
            .order_by(SessionModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._model_to_entity(model)

    async def save_message(self, message: Message) -> None:
        """Save a message to a session.

        Args:
            message: The message to save.
        """
        model = MessageModel(
            id=message.id,
            session_id=message.session_id,
            role=message.role.value,
            content=message.content,
            created_at=message.created_at,
        )
        self._session.add(model)
        await self._session.commit()
        logger.debug(
            "message_saved",
            message_id=str(message.id),
            session_id=str(message.session_id),
            role=message.role.value,
        )

    async def get_messages(self, session_id: UUID) -> list[Message]:
        """Retrieve all messages for a session.

        Args:
            session_id: The session ID.

        Returns:
            List of messages ordered by creation time.
        """
        stmt = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._message_model_to_entity(m) for m in models]

    def _model_to_entity(self, model: SessionModel) -> Session:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: The SQLAlchemy session model.

        Returns:
            The domain Session entity.
        """
        session = Session(
            room_name=model.room_name,
            user_id=model.user_id,
            id=model.id,
            status=SessionStatus(model.status),
            created_at=model.created_at,
            started_at=model.started_at,
            ended_at=model.ended_at,
        )
        return session

    def _message_model_to_entity(self, model: MessageModel) -> Message:
        """Convert SQLAlchemy model to domain entity.

        Args:
            model: The SQLAlchemy message model.

        Returns:
            The domain Message entity.
        """
        return Message(
            session_id=model.session_id,
            role=MessageRole(model.role),
            content=model.content,
            id=model.id,
            created_at=model.created_at,
        )
