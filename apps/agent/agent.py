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

# Import the server from the inbound adapter
from src.adapters.inbound.livekit_worker import server  # noqa: E402

if __name__ == "__main__":
    agents.cli.run_app(server)
