"""OpenTelemetry tracing configuration.

Provides distributed tracing for observability across services.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

if TYPE_CHECKING:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)

# Default service name for tracer
_SERVICE_NAME = "echo-sphere-agent"


def setup_tracing(settings: Settings) -> None:
    """Configure OpenTelemetry tracing.

    Args:
        settings: Application settings containing OTEL configuration.
    """
    if not settings.otel_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return

    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
            "service.version": "1.0.0",
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure OTLP exporter
    exporter = OTLPSpanExporter(
        endpoint=settings.otel_exporter_otlp_endpoint,
        insecure=True,  # Use insecure for local development
    )

    # Add batch processor for efficient export
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    logger.info(
        "OpenTelemetry tracing initialized",
        extra={
            "service_name": settings.otel_service_name,
            "endpoint": settings.otel_exporter_otlp_endpoint,
        },
    )


def get_tracer(name: str | None = None) -> trace.Tracer:
    """Get the configured tracer instance.

    Args:
        name: Optional tracer name. Defaults to service name.

    Returns:
        Tracer: OpenTelemetry tracer instance.
            Returns a no-op tracer if tracing is not initialized.
    """
    return trace.get_tracer(name or _SERVICE_NAME)


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush pending spans."""
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.shutdown()
        logger.info("OpenTelemetry tracing shutdown complete")
