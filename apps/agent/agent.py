"""EchoSphere Voice Agent.

This is the entry point for the LiveKit Agents CLI.
Run with: uv run agent.py [console|dev|start|download-files]
"""

from pathlib import Path

from dotenv import load_dotenv
from livekit import agents

# Load environment variables from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")
load_dotenv(project_root / ".env.local")

# Initialize tracing before importing other modules
from src.config import get_settings  # noqa: E402
from src.config import setup_tracing  # noqa: E402

settings = get_settings()
setup_tracing(settings)

# Import the server from the inbound adapter
from src.adapters.inbound.livekit_worker import server  # noqa: E402

if __name__ == "__main__":
    agents.cli.run_app(server)
