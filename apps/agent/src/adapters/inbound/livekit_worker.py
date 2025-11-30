"""LiveKit Agent Worker - Inbound adapter for voice interactions.

This module implements the LiveKit Agents integration, serving as the
inbound adapter in the hexagonal architecture. It handles:
- Agent session lifecycle
- Real-time voice interaction
- AI pipeline orchestration (STT -> LLM -> TTS)
- Session and message persistence
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from dataclasses import field
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Any

from livekit.agents import Agent
from livekit.agents import AgentServer
from livekit.agents import AgentSession
from livekit.agents import CloseEvent
from livekit.agents import ConversationItemAddedEvent
from livekit.agents import JobContext
from livekit.agents import metrics
from livekit.plugins import aws
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from opentelemetry import trace

from src.adapters.outbound import Database
from src.adapters.outbound import PostgresSessionRepository
from src.config.settings import get_settings
from src.domain.entities import Message
from src.domain.entities import MessageRole
from src.domain.entities import Session

if TYPE_CHECKING:
    from livekit.agents.voice import MetricsCollectedEvent

    from src.config.settings import Settings

# Service name for custom spans
_SERVICE_NAME = "echo-sphere-agent"

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Container for session-related state during entrypoint execution."""

    db: Database | None
    is_console_mode: bool
    background_tasks: set[asyncio.Task[None]] = field(default_factory=set)
    domain_session: Session | None = None


@lru_cache
def get_database() -> Database:
    """Get or create the database instance.

    Returns:
        Database instance.
    """
    settings = get_settings()
    return Database(settings.database_url)


class EchoSphereAssistant(Agent):
    """EchoSphere voice assistant agent.

    This agent handles real-time voice conversations with users,
    providing helpful responses in Japanese by default.

    Attributes:
        instructions: The system prompt for the agent.
        greeting_prompt: The prompt for generating the initial greeting.
    """

    def __init__(
        self,
        instructions: str | None = None,
        greeting_prompt: str | None = None,
    ) -> None:
        """Initialize the EchoSphere assistant.

        Args:
            instructions: Custom instructions for the agent.
                Defaults to settings value or a helpful Japanese assistant prompt.
            greeting_prompt: Prompt for generating initial greeting.
                Defaults to settings value.
        """
        settings = get_settings()
        self._greeting_prompt = greeting_prompt or settings.agent_greeting_prompt

        super().__init__(
            instructions=instructions or settings.agent_instructions,
        )

    async def on_enter(self) -> None:
        """Called when the agent enters a session.

        Generates an initial greeting for the user.
        """
        self.session.generate_reply(instructions=self._greeting_prompt)


def create_session(settings: Settings | None = None) -> AgentSession[Any]:
    """Create an AgentSession with AWS AI services.

    Args:
        settings: Application settings. If None, loads from environment.

    Returns:
        Configured AgentSession with STT, LLM, TTS, and VAD.
    """
    if settings is None:
        settings = get_settings()

    return AgentSession(
        # AWS AI Services for Japanese support
        stt=aws.STT(
            language=settings.stt_language,
        ),
        llm=aws.LLM(
            model=settings.llm_model,
            region=settings.aws_region,
        ),
        tts=aws.TTS(
            voice=settings.tts_voice,
            language=settings.tts_language,
            speech_engine="neural",
        ),
        # Voice activity detection
        vad=silero.VAD.load(),
        # Turn detection for natural conversation
        turn_detection=MultilingualModel(),
    )


async def _resolve_room_sid(ctx: JobContext) -> str:
    """Resolve the room SID from job context.

    Handles both real LiveKit rooms and console mode mock rooms.

    Args:
        ctx: The job context containing room information.

    Returns:
        Room SID string, or a fallback for console mode.
    """
    try:
        sid_coro = ctx.room.sid
        if hasattr(sid_coro, "__await__"):
            return await sid_coro
        # Console mode: use room name as fallback
        return f"console-{ctx.room.name}"
    except (TypeError, AttributeError):
        # Fallback for mock objects
        return f"console-{ctx.room.name}"


async def _save_session_safe(
    session_ctx: SessionContext,
    operation: str,
) -> None:
    """Save session to database with error handling.

    Args:
        session_ctx: The session context containing db and domain_session.
        operation: Description of the operation for logging.
    """
    if session_ctx.db is None or session_ctx.domain_session is None:
        return

    try:
        async with session_ctx.db.get_session() as db_session:
            repo = PostgresSessionRepository(db_session)
            await repo.save_session(session_ctx.domain_session)
        logger.debug(
            "Session saved",
            extra={
                "operation": operation,
                "session_id": str(session_ctx.domain_session.id),
                "status": session_ctx.domain_session.status.value,
            },
        )
    except Exception as e:
        logger.warning(
            "Failed to save session",
            extra={
                "operation": operation,
                "error": str(e),
                "session_id": str(session_ctx.domain_session.id),
            },
        )


def _setup_conversation_handler(
    agent_session: AgentSession[Any],
    session_ctx: SessionContext,
) -> None:
    """Set up the conversation item event handler.

    Args:
        agent_session: The LiveKit agent session.
        session_ctx: The session context for accessing state.
    """

    @agent_session.on("conversation_item_added")
    def on_conversation_item(ev: ConversationItemAddedEvent) -> None:
        """Handle conversation item added events."""
        if session_ctx.domain_session is None:
            return

        item = ev.item
        if item.type != "message":
            return

        # Determine role
        if item.role == "user":
            role = MessageRole.USER
        elif item.role == "assistant":
            role = MessageRole.ASSISTANT
        else:
            return

        # Get text content
        content = item.text_content
        if not content:
            return

        # Save message asynchronously
        async def save_message() -> None:
            if session_ctx.db is None or session_ctx.domain_session is None:
                return
            try:
                message = Message(
                    session_id=session_ctx.domain_session.id,
                    role=role,
                    content=content,
                )
                async with session_ctx.db.get_session() as db_session:
                    repo = PostgresSessionRepository(db_session)
                    await repo.save_message(message)
                logger.debug(
                    "Message saved",
                    extra={"role": role.value, "content": content[:50] if content else ""},
                )
            except Exception as e:
                logger.warning(
                    "Failed to save message",
                    extra={"error": str(e), "role": role.value},
                )

        task = asyncio.create_task(save_message())
        session_ctx.background_tasks.add(task)
        task.add_done_callback(session_ctx.background_tasks.discard)


def _setup_close_handler(
    agent_session: AgentSession[Any],
    session_ctx: SessionContext,
    close_event: asyncio.Event,
) -> None:
    """Set up the session close event handler.

    Args:
        agent_session: The LiveKit agent session.
        session_ctx: The session context for accessing state.
        close_event: Event to signal when session closes.
    """

    @agent_session.on("close")
    def on_close(ev: CloseEvent) -> None:
        """Handle session close events."""
        session_id = str(session_ctx.domain_session.id) if session_ctx.domain_session else "unknown"
        logger.info(
            "Agent session closing",
            extra={
                "reason": ev.reason.value if ev.reason else "unknown",
                "session_id": session_id,
            },
        )
        close_event.set()


def _setup_metrics_handler(agent_session: AgentSession[Any]) -> None:
    """Set up the metrics collection event handler.

    Args:
        agent_session: The LiveKit agent session.
    """

    @agent_session.on("metrics_collected")
    def on_metrics_collected(ev: MetricsCollectedEvent) -> None:
        """Log metrics for STT, LLM, and TTS operations."""
        metrics.log_metrics(ev.metrics)


async def _wait_for_background_tasks(session_ctx: SessionContext) -> None:
    """Wait for pending background tasks to complete.

    Args:
        session_ctx: The session context containing background tasks.
    """
    if not session_ctx.background_tasks:
        return

    pending = [t for t in session_ctx.background_tasks if not t.done()]
    if pending:
        logger.debug(
            "Waiting for pending background tasks",
            extra={"count": len(pending)},
        )
        await asyncio.gather(*pending, return_exceptions=True)


# Create server instance at module level for pickle compatibility
server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """Agent session entrypoint.

    This function is called when a new session is created.
    It initializes the session with AWS AI services and starts
    the EchoSphere assistant.

    Args:
        ctx: The job context containing room information.
    """
    tracer = trace.get_tracer(_SERVICE_NAME)

    with tracer.start_as_current_span(
        "agent_session",
        attributes={"room.name": ctx.room.name},
    ) as session_span:
        # Initialize session context
        is_console_mode = ctx.room.name == "mock_room"
        session_ctx = SessionContext(
            db=None if is_console_mode else get_database(),
            is_console_mode=is_console_mode,
        )

        session_span.set_attribute("session.console_mode", is_console_mode)

        logger.info(
            "Entrypoint called",
            extra={"room_name": ctx.room.name, "console_mode": is_console_mode},
        )

        if is_console_mode:
            logger.info("Console mode: database operations disabled")

        # Create agent session and close event
        with tracer.start_as_current_span("create_agent_session"):
            agent_session = create_session()
            close_event = asyncio.Event()

            # Set up event handlers
            _setup_conversation_handler(agent_session, session_ctx)
            _setup_close_handler(agent_session, session_ctx, close_event)
            _setup_metrics_handler(agent_session)

        # Start agent session
        with tracer.start_as_current_span("start_agent_session"):
            await agent_session.start(
                room=ctx.room,
                agent=EchoSphereAssistant(),
            )

            # Resolve room SID and create domain session
            room_sid = await _resolve_room_sid(ctx)

        session_span.set_attribute("room.sid", room_sid)
        logger.info(
            "Agent session started",
            extra={"room_name": ctx.room.name, "room_sid": room_sid},
        )

        # Create and initialize domain session
        session_ctx.domain_session = Session(
            room_name=ctx.room.name,
            user_id=room_sid,
        )
        session_span.set_attribute("session.id", str(session_ctx.domain_session.id))

        # Save initial session (pending status)
        await _save_session_safe(session_ctx, "create")

        # Start the session (transition to active)
        session_ctx.domain_session.start()
        await _save_session_safe(session_ctx, "start")

        # Wait for the session to close
        await close_event.wait()

        # Wait for pending background tasks before cleanup
        await _wait_for_background_tasks(session_ctx)

        # Mark session as complete and save
        session_ctx.domain_session.complete()
        await _save_session_safe(session_ctx, "complete")

        # Record session duration
        duration = session_ctx.domain_session.duration_seconds
        session_span.set_attribute("session.duration_seconds", duration or 0)
        session_span.set_status(trace.StatusCode.OK)

        logger.info(
            "Agent session completed",
            extra={
                "room_name": ctx.room.name,
                "session_id": str(session_ctx.domain_session.id),
                "duration_seconds": duration,
            },
        )
