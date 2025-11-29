"""EchoSphere Voice Agent.

This is the entry point for the LiveKit Agents CLI.
Run with: uv run agent.py [console|dev|start|download-files]
"""

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, JobContext
from livekit.plugins import aws, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables
load_dotenv()
load_dotenv(".env.local")


class VoiceAssistant(Agent):
    """EchoSphere voice assistant agent."""

    def __init__(self) -> None:
        super().__init__(
            instructions="""You are a helpful voice AI assistant for EchoSphere.
You assist users with their questions in a friendly and professional manner.
Your responses are concise, clear, and natural for spoken conversation.
You speak Japanese unless the user speaks in another language.""",
        )


server = AgentServer()


@server.rtc_session()
async def entrypoint(ctx: JobContext) -> None:
    """Agent session entrypoint.

    This function is called when a new session is created.
    """
    session = AgentSession(
        # AWS AI Services for Japanese support
        stt=aws.STT(
            language="ja-JP",
        ),
        llm=aws.LLM(
            model="apac.anthropic.claude-sonnet-4-5-20250929-v1:0",
            region="ap-northeast-1",
        ),
        tts=aws.TTS(
            voice="Kazuha",
            language="ja-JP",
            speech_engine="neural",
        ),
        # Voice activity detection
        vad=silero.VAD.load(),
        # Turn detection for natural conversation
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=VoiceAssistant(),
    )

    await session.generate_reply(
        instructions="Greet the user warmly in Japanese and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
