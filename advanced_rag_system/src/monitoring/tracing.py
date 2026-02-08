"""Distributed tracing support for Advanced RAG System.

Provides OpenTelemetry integration for distributed tracing with:
- OpenTelemetry integration
- Trace decorators for async functions
- Context propagation
- Jaeger exporter configuration

Example:
    ```python
    from src.monitoring.tracing import tracer, trace_span, get_current_span

    # Automatic tracing via decorator
    @trace_span("process_query")
    async def process_query(query: str):
        # Get current span to add custom attributes
        span = get_current_span()
        span.set_attribute("query.length", len(query))
        return await do_processing(query)

    # Manual span creation
    with tracer.start_span("custom_operation") as span:
        span.set_attribute("custom.attribute", "value")
        result = perform_operation()
    ```
"""

from __future__ import annotations

import functools
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from src.core.config import Settings, get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Try to import OpenTelemetry packages
try:
    from opentelemetry import trace
    from opentelemetry.context import Context
    from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import SpanKind, Status, StatusCode
    from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logger.warning("opentelemetry_not_available", message="OpenTelemetry packages not installed")

# Try to import Jaeger exporter
try:
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter

    JAEGER_AVAILABLE = True
except ImportError:
    JAEGER_AVAILABLE = False

# Try to import OTLP exporter
try:
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    OTLP_AVAILABLE = True
except ImportError:
    OTLP_AVAILABLE = False


class Tracer:
    """Distributed tracing manager for RAG system.

    Provides OpenTelemetry integration with support for multiple exporters
    including Jaeger and OTLP.

    Attributes:
        provider: OpenTelemetry TracerProvider
        tracer: OpenTelemetry tracer instance
        propagator: Context propagator for distributed tracing
        settings: Application settings
    """

    def __init__(
        self,
        service_name: Optional[str] = None,
        service_version: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initialize the tracer.

        Args:
            service_name: Name of the service
            service_version: Service version
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self.service_name = service_name or self.settings.app_name
        self.service_version = service_version or self.settings.app_version
        self._initialized = False
        self._tracer: Optional[Any] = None
        self._propagator: Optional[Any] = None

        if OPENTELEMETRY_AVAILABLE:
            self._initialize_opentelemetry()
        else:
            logger.warning("tracer_noop_mode", message="Running in noop mode without OpenTelemetry")

    def _initialize_opentelemetry(self) -> None:
        """Initialize OpenTelemetry tracer."""
        try:
            # Create resource
            resource = Resource.create(
                {
                    SERVICE_NAME: self.service_name,
                    SERVICE_VERSION: self.service_version,
                }
            )

            # Create provider
            provider = TracerProvider(resource=resource)

            # Configure exporters
            self._configure_exporters(provider)

            # Set global provider
            trace.set_tracer_provider(provider)

            # Create tracer
            self._tracer = trace.get_tracer(self.service_name, self.service_version)

            # Create propagator
            self._propagator = TraceContextTextMapPropagator()

            self._initialized = True
            logger.info("tracer_initialized", service=self.service_name)

        except Exception as e:
            logger.error("tracer_initialization_failed", error=str(e))
            self._tracer = None
            self._propagator = None

    def _configure_exporters(self, provider: TracerProvider) -> None:
        """Configure span exporters based on environment.

        Args:
            provider: TracerProvider to configure
        """
        exporters_configured = False

        # Check for Jaeger configuration
        jaeger_endpoint = self._get_jaeger_endpoint()
        if jaeger_endpoint and JAEGER_AVAILABLE:
            try:
                jaeger_exporter = JaegerExporter(
                    agent_host_name=jaeger_endpoint.get("host", "localhost"),
                    agent_port=jaeger_endpoint.get("port", 6831),
                )
                provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
                exporters_configured = True
                logger.info("jaeger_exporter_configured", endpoint=jaeger_endpoint)
            except Exception as e:
                logger.error("jaeger_exporter_failed", error=str(e))

        # Check for OTLP configuration
        otlp_endpoint = self._get_otlp_endpoint()
        if otlp_endpoint and OTLP_AVAILABLE:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                exporters_configured = True
                logger.info("otlp_exporter_configured", endpoint=otlp_endpoint)
            except Exception as e:
                logger.error("otlp_exporter_failed", error=str(e))

        # Fallback to console exporter in debug mode
        if not exporters_configured and self.settings.debug:
            try:
                from opentelemetry.sdk.trace.export import ConsoleSpanExporter

                provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
                logger.info("console_exporter_configured")
            except Exception as e:
                logger.error("console_exporter_failed", error=str(e))

    def _get_jaeger_endpoint(self) -> Optional[Dict[str, Any]]:
        """Get Jaeger endpoint from environment.

        Returns:
            Dictionary with host and port, or None
        """
        import os

        jaeger_host = os.getenv("JAEGER_AGENT_HOST")
        jaeger_port = os.getenv("JAEGER_AGENT_PORT")

        if jaeger_host:
            return {
                "host": jaeger_host,
                "port": int(jaeger_port) if jaeger_port else 6831,
            }
        return None

    def _get_otlp_endpoint(self) -> Optional[str]:
        """Get OTLP endpoint from environment.

        Returns:
            OTLP endpoint URL, or None
        """
        import os

        return os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    @contextmanager
    def start_span(
        self,
        name: str,
        kind: str = "internal",
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """Start a new span context.

        Args:
            name: Span name
            kind: Span kind (internal, server, client, producer, consumer)
            attributes: Optional span attributes

        Yields:
            Span context
        """
        if not self._initialized or self._tracer is None:
            # Return a noop span
            class NoopSpan:
                def set_attribute(self, key: str, value: Any) -> None:
                    pass

                def set_status(self, status: Any) -> None:
                    pass

                def record_exception(self, exception: Exception) -> None:
                    pass

                def end(self) -> None:
                    pass

            yield NoopSpan()
            return

        # Map kind string to SpanKind
        kind_map = {
            "internal": SpanKind.INTERNAL,
            "server": SpanKind.SERVER,
            "client": SpanKind.CLIENT,
            "producer": SpanKind.PRODUCER,
            "consumer": SpanKind.CONSUMER,
        }
        span_kind = kind_map.get(kind, SpanKind.INTERNAL)

        with self._tracer.start_as_current_span(name, kind=span_kind) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span

    def get_current_span(self) -> Any:
        """Get the current active span.

        Returns:
            Current span or noop span
        """
        if not self._initialized or self._tracer is None:

            class NoopSpan:
                def set_attribute(self, key: str, value: Any) -> None:
                    pass

                def set_status(self, status: Any) -> None:
                    pass

                def record_exception(self, exception: Exception) -> None:
                    pass

            return NoopSpan()

        return trace.get_current_span()

    def set_span_attribute(self, key: str, value: Any) -> None:
        """Set an attribute on the current span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        span = self.get_current_span()
        if span:
            span.set_attribute(key, value)

    def set_span_status(self, status: str, description: Optional[str] = None) -> None:
        """Set the status of the current span.

        Args:
            status: Status code (ok, error, unset)
            description: Optional status description
        """
        if not self._initialized:
            return

        span = self.get_current_span()
        if span:
            status_code = getattr(StatusCode, status.upper(), StatusCode.UNSET)
            span.set_status(Status(status_code, description))

    def record_exception(self, exception: Exception) -> None:
        """Record an exception on the current span.

        Args:
            exception: Exception to record
        """
        span = self.get_current_span()
        if span and hasattr(span, "record_exception"):
            span.record_exception(exception)

    def inject_context(self, carrier: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into carrier.

        Args:
            carrier: Dictionary to inject context into

        Returns:
            Carrier with injected context
        """
        if not self._initialized or self._propagator is None:
            return carrier

        self._propagator.inject(carrier)
        return carrier

    def extract_context(self, carrier: Dict[str, str]) -> Any:
        """Extract trace context from carrier.

        Args:
            carrier: Dictionary containing context

        Returns:
            Extracted context
        """
        if not self._initialized or self._propagator is None:
            from opentelemetry.context import Context

            return Context()

        return self._propagator.extract(carrier)

    def is_initialized(self) -> bool:
        """Check if tracer is initialized.

        Returns:
            True if initialized
        """
        return self._initialized


# Global tracer instance
tracer = Tracer()


def trace_span(
    name: Optional[str] = None,
    kind: str = "internal",
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """Decorator for tracing function execution.

    Automatically creates a span for the decorated function.

    Args:
        name: Span name (defaults to function name)
        kind: Span kind
        attributes: Additional span attributes

    Returns:
        Decorated function

    Example:
        ```python
        @trace_span("process_query", kind="server")
        async def process_query(query: str):
            return await do_processing(query)
        ```
    """

    def decorator(func: F) -> F:
        span_name = name or func.__name__
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            # Merge default attributes with provided
            span_attrs = {
                "function.name": func.__name__,
                "function.module": func.__module__,
            }
            if attributes:
                span_attrs.update(attributes)

            # Add argument info (be careful with sensitive data)
            if args:
                span_attrs["function.args_count"] = len(args)
            if kwargs:
                span_attrs["function.kwargs_keys"] = list(kwargs.keys())

            with tracer.start_span(span_name, kind=kind, attributes=span_attrs) as span:
                try:
                    result = await func(*args, **kwargs)
                    tracer.set_span_status("ok")
                    return result
                except Exception as e:
                    tracer.set_span_status("error", str(e))
                    tracer.record_exception(e)
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            span_attrs = {
                "function.name": func.__name__,
                "function.module": func.__module__,
            }
            if attributes:
                span_attrs.update(attributes)

            if args:
                span_attrs["function.args_count"] = len(args)
            if kwargs:
                span_attrs["function.kwargs_keys"] = list(kwargs.keys())

            with tracer.start_span(span_name, kind=kind, attributes=span_attrs) as span:
                try:
                    result = func(*args, **kwargs)
                    tracer.set_span_status("ok")
                    return result
                except Exception as e:
                    tracer.set_span_status("error", str(e))
                    tracer.record_exception(e)
                    raise

        return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]

    return decorator


def get_current_span() -> Any:
    """Get the current active span.

    Returns:
        Current span instance
    """
    return tracer.get_current_span()


def set_span_attribute(key: str, value: Any) -> None:
    """Set an attribute on the current span.

    Args:
        key: Attribute key
        value: Attribute value
    """
    tracer.set_span_attribute(key, value)


def set_span_status(status: str, description: Optional[str] = None) -> None:
    """Set the status of the current span.

    Args:
        status: Status code (ok, error, unset)
        description: Optional description
    """
    tracer.set_span_status(status, description)


def record_exception(exception: Exception) -> None:
    """Record an exception on the current span.

    Args:
        exception: Exception to record
    """
    tracer.record_exception(exception)


@contextmanager
def span_context(
    name: str,
    kind: str = "internal",
    attributes: Optional[Dict[str, Any]] = None,
):
    """Context manager for creating spans.

    Args:
        name: Span name
        kind: Span kind
        attributes: Span attributes

    Example:
        ```python
        with span_context("custom_operation", attributes={"key": "value"}) as span:
            span.set_attribute("result", "success")
            perform_operation()
        ```
    """
    with tracer.start_span(name, kind=kind, attributes=attributes) as span:
        yield span


def inject_trace_context(carrier: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Inject trace context into a carrier for distributed tracing.

    Args:
        carrier: Optional carrier dictionary (creates new if None)

    Returns:
        Carrier with injected context
    """
    carrier = carrier or {}
    return tracer.inject_context(carrier)


def extract_trace_context(carrier: Dict[str, str]) -> Any:
    """Extract trace context from a carrier.

    Args:
        carrier: Carrier containing trace context

    Returns:
        Extracted context
    """
    return tracer.extract_context(carrier)


# Import asyncio here to avoid circular import issues
import asyncio
