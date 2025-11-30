"""OpenTelemetry tracing configuration using LiveKit's official API.

Provides distributed tracing for observability across services,
integrating with LiveKit's internal tracer for STT/LLM/TTS spans.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from livekit.agents.telemetry import set_tracer_provider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from opentelemetry.util.types import AttributeValue

    from src.config.settings import Settings

logger = logging.getLogger(__name__)

# Module-level tracer provider instance
_tracer_provider: TracerProvider | None = None


def setup_tracing(
    settings: Settings,
    *,
    metadata: dict[str, AttributeValue] | None = None,
) -> TracerProvider | None:
    """Configure OpenTelemetry tracing using LiveKit's official API.

    This function sets up tracing that integrates with LiveKit's internal
    tracer, enabling automatic spans for STT, LLM, and TTS operations.

    Args:
        settings: Application settings containing OTEL configuration.
        metadata: Optional metadata to attach to all spans.

    Returns:
        TracerProvider if tracing is enabled, None otherwise.
    """
    global _tracer_provider  # noqa: PLW0603

    if not settings.otel_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return None

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
        }
    )

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,  # Use insecure for local development
    )

    # Add batch processor for efficient export
    processor = BatchSpanProcessor(exporter)
    _tracer_provider.add_span_processor(processor)

    # Register with LiveKit's internal tracer
    # This enables automatic spans for STT, LLM, and TTS operations
    set_tracer_provider(_tracer_provider, metadata=metadata)

    logger.info(
        "OpenTelemetry tracing initialized (LiveKit integration)",
        extra={
            "service_name": settings.otel_service_name,
            "endpoint": settings.otel_exporter_otlp_endpoint,
        },
    )

    return _tracer_provider


def get_tracer_provider() -> TracerProvider | None:
    """Get the configured tracer provider instance.

    Returns:
        TracerProvider if tracing is enabled, None otherwise.
    """
    return _tracer_provider


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush pending spans."""
    global _tracer_provider  # noqa: PLW0603

    if _tracer_provider is not None:
        _tracer_provider.force_flush()
        _tracer_provider.shutdown()
        logger.info("OpenTelemetry tracing shutdown complete")
        _tracer_provider = None
