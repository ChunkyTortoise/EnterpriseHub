"""OpenTelemetry configuration for EnterpriseHub.

Supports three exporter types via OTEL_EXPORTER_TYPE env var:
- otlp (default): OpenTelemetry Protocol to OTEL_ENDPOINT
- jaeger: Jaeger-compatible OTLP export
- console: stdout for debugging

Auto-instruments:
- FastAPI (requests, middleware)
- httpx (outbound HTTP calls)
- asyncpg (PostgreSQL queries)
- redis (cache operations)

All instrumentation is optional -- missing packages are silently skipped.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def setup_observability(
    service_name: Optional[str] = None,
    enabled: Optional[bool] = None,
    exporter_type: Optional[str] = None,
    endpoint: Optional[str] = None,
) -> bool:
    """Initialize OpenTelemetry tracing for the application.

    Reads configuration from environment variables unless overridden:
    - OTEL_ENABLED (default: false)
    - OTEL_EXPORTER_TYPE (default: otlp) -- otlp|jaeger|console
    - OTEL_ENDPOINT (default: http://localhost:4317)
    - OTEL_SERVICE_NAME (default: enterprisehub)

    Returns:
        True if OTel was successfully configured, False otherwise.
    """
    _enabled = (
        enabled
        if enabled is not None
        else os.getenv("OTEL_ENABLED", "false").lower() == "true"
    )
    if not _enabled:
        logger.info("OpenTelemetry disabled (OTEL_ENABLED != true)")
        return False

    _service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "enterprisehub")
    _exporter_type = exporter_type or os.getenv("OTEL_EXPORTER_TYPE", "otlp")
    _endpoint = endpoint or os.getenv("OTEL_ENDPOINT", "http://localhost:4317")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import (
            BatchSpanProcessor,
            ConsoleSpanExporter,
        )
    except ImportError:
        logger.warning(
            "OpenTelemetry SDK not installed -- skipping configuration"
        )
        return False

    # Create resource with service metadata
    resource = Resource.create(
        {
            "service.name": _service_name,
            "service.version": "1.0.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure exporter
    exporter = _create_exporter(_exporter_type, _endpoint)
    if exporter is None:
        logger.warning(
            "Failed to create %s exporter, falling back to console",
            _exporter_type,
        )
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    # Auto-instrument libraries
    _auto_instrument_fastapi()
    _auto_instrument_httpx()
    _auto_instrument_asyncpg()
    _auto_instrument_redis()

    logger.info(
        "OpenTelemetry configured: service=%s, exporter=%s, endpoint=%s",
        _service_name,
        _exporter_type,
        _endpoint,
    )
    return True


def _create_exporter(exporter_type: str, endpoint: str):
    """Create the appropriate span exporter.

    Args:
        exporter_type: One of "otlp", "jaeger", or "console".
        endpoint: gRPC endpoint for OTLP/Jaeger exporters.

    Returns:
        A span exporter instance, or None if creation failed.
    """
    if exporter_type == "console":
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        return ConsoleSpanExporter()

    if exporter_type in ("otlp", "jaeger"):
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
                OTLPSpanExporter,
            )

            return OTLPSpanExporter(endpoint=endpoint, insecure=True)
        except ImportError:
            logger.warning("OTLP gRPC exporter not available, trying HTTP")
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                    OTLPSpanExporter as HTTPExporter,
                )

                http_endpoint = (
                    endpoint.replace(":4317", ":4318") + "/v1/traces"
                )
                return HTTPExporter(endpoint=http_endpoint)
            except ImportError:
                logger.warning("No OTLP exporter available")
                return None

    logger.warning("Unknown exporter type: %s", exporter_type)
    return None


def _auto_instrument_fastapi():
    """Auto-instrument FastAPI if available."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument()
        logger.info("FastAPI auto-instrumentation enabled")
    except ImportError:
        logger.debug("FastAPI instrumentation not available")
    except Exception as exc:
        logger.debug("FastAPI instrumentation failed: %s", exc)


def _auto_instrument_httpx():
    """Auto-instrument httpx if available."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument()
        logger.info("httpx auto-instrumentation enabled")
    except ImportError:
        logger.debug("httpx instrumentation not available")
    except Exception as exc:
        logger.debug("httpx instrumentation failed: %s", exc)


def _auto_instrument_asyncpg():
    """Auto-instrument asyncpg if available."""
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor

        AsyncPGInstrumentor().instrument()
        logger.info("asyncpg auto-instrumentation enabled")
    except ImportError:
        logger.debug("asyncpg instrumentation not available")
    except Exception as exc:
        logger.debug("asyncpg instrumentation failed: %s", exc)


def _auto_instrument_redis():
    """Auto-instrument Redis if available."""
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor

        RedisInstrumentor().instrument()
        logger.info("Redis auto-instrumentation enabled")
    except ImportError:
        logger.debug("Redis instrumentation not available")
    except Exception as exc:
        logger.debug("Redis instrumentation failed: %s", exc)
