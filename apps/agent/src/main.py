"""Main entry point for EchoSphere Agent.

This module initializes and runs the LiveKit agent worker.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import structlog

from src.config.logging import get_logger
from src.config.logging import setup_logging
from src.config.settings import get_settings

# Shutdown event for graceful termination
_shutdown_event: asyncio.Event | None = None


async def main() -> None:
    """Initialize and run the agent."""
    global _shutdown_event  # noqa: PLW0603
    _shutdown_event = asyncio.Event()

    settings = get_settings()
    setup_logging(log_level=settings.log_level, json_logs=not settings.debug)

    logger: structlog.stdlib.BoundLogger = get_logger(__name__)
    logger.info(
        "starting_agent",
        app_name=settings.app_name,
        livekit_url=settings.livekit_url,
    )

    # TODO: Initialize LiveKit agent worker
    # This will be implemented in Phase 1

    logger.info("agent_ready")

    # Wait for shutdown signal
    await _shutdown_event.wait()
    logger.info("agent_shutdown")


if __name__ == "__main__":
    asyncio.run(main())
