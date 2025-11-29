"""LiveKit Agent Worker - Inbound adapter for voice interactions.

This module implements the LiveKit Agents integration, serving as the
inbound adapter in the hexagonal architecture. It handles:
- Agent session lifecycle
- Real-time voice interaction
- AI pipeline orchestration (STT → LLM → TTS)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from livekit.agents import Agent
from livekit.agents import AgentServer
from livekit.agents import AgentSession
from livekit.agents import JobContext
from livekit.agents.voice import room_io
from livekit.plugins import aws
from livekit.plugins import noise_cancellation
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


class EchoSphereAssistant(Agent):
    """EchoSphere voice assistant agent.

    This agent handles real-time voice conversations with users,
    providing helpful responses in Japanese by default.

    Attributes:
        instructions: The system prompt for the agent.
    """

    def __init__(self, instructions: str | None = None) -> None:
        """Initialize the EchoSphere assistant.

        Args:
            instructions: Custom instructions for the agent.
                Defaults to a helpful Japanese assistant prompt.
        """
        default_instructions = """You are a helpful voice AI assistant for EchoSphere.
You assist users with their questions in a friendly and professional manner.
Your responses are concise, clear, and natural for spoken conversation.
You speak Japanese unless the user speaks in another language."""

        super().__init__(
            instructions=instructions or default_instructions,
        )

    async def on_enter(self) -> None:
        """Called when the agent enters a session.

        Generates an initial greeting for the user.
        """
        self.session.generate_reply(
            instructions="Greet the user warmly in Japanese and offer your assistance."
        )


def create_session(_settings: Settings | None = None) -> AgentSession:  # type: ignore[type-arg]
    """Create an AgentSession with AWS AI services.

    Args:
        settings: Application settings. If None, uses defaults.

    Returns:
        Configured AgentSession with STT, LLM, TTS, and VAD.
    """
    # TODO: Use settings for configuration (Task 1.5)
    # For now, use hardcoded values that will be moved to settings
    aws_region = "ap-northeast-1"
    stt_language = "ja-JP"
    # Cross-region inference profile for Claude Sonnet 4.5 (Japan region)
    # See: https://aws.amazon.com/blogs/aws/introducing-claude-sonnet-4-5-in-amazon-bedrock/
    llm_model = "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"
    tts_voice = "Kazuha"
    tts_language = "ja-JP"

    return AgentSession(
        # AWS AI Services for Japanese support
        stt=aws.STT(
            language=stt_language,
        ),
        llm=aws.LLM(
            model=llm_model,
            region=aws_region,
        ),
        tts=aws.TTS(
            voice=tts_voice,
            language=tts_language,
            speech_engine="neural",
        ),
        # Voice activity detection
        vad=silero.VAD.load(),
        # Turn detection for natural conversation
        turn_detection=MultilingualModel(),
    )


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
    logger.info(
        "Starting agent session",
        extra={
            "room_name": ctx.room.name,
            "room_sid": ctx.room.sid,
        },
    )

    session = create_session()

    await session.start(
        room=ctx.room,
        agent=EchoSphereAssistant(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Background Voice Cancellation removes background noise
                # and non-primary speakers for cleaner STT
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    logger.info(
        "Agent session started",
        extra={
            "room_name": ctx.room.name,
        },
    )
