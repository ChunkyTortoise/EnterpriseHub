"""
Jorge Services OpenTelemetry Stubs

Provides OpenTelemetry-compatible span/trace decorators for the Jorge
service layer.  When the ``opentelemetry`` SDK is installed, real spans
are created and exported.  When it is **not** installed, all decorators
are transparent no-ops so that the services work without an extra
dependency.

Usage:
    from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

    @trace_operation("jorge.handoff", "evaluate_handoff")
    async def evaluate_handoff(self, ...):
        ...

    # Sync functions are supported too:
    @trace_operation("jorge.metrics", "compute_summary")
    def compute_summary(self, ...):
        ...

    # Manual span context:
    with optional_span("jorge.alerting", "check_alerts") as span:
        span.set_attribute("alert_count", 3)
        ...

Attributes automatically captured on each span:
    - jorge.service: The service/component name
    - jorge.operation: The operation name
    - jorge.success: Whether the call completed without exception
    - jorge.duration_ms: Wall-clock duration in milliseconds
"""

import functools
import inspect
import logging
import time
from contextlib import contextmanager
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Detect OpenTelemetry availability ─────────────────────────────────

_otel_available = False
_tracer = None

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.trace import StatusCode as OtelStatusCode

    _otel_available = True
    _tracer = otel_trace.get_tracer("jorge-services", "1.0.0")
    logger.info("OpenTelemetry SDK detected — real tracing enabled for jorge services")
except ImportError:
    logger.debug("OpenTelemetry SDK not installed — using no-op tracing stubs")


# ── No-op helpers (used when OTel is not installed) ───────────────────


class _NoOpSpan:
    """Minimal span stub that silently accepts all OTel span operations."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any, description: Optional[str] = None) -> None:
        pass

    def record_exception(self, exception: BaseException) -> None:
        pass

    def add_event(self, name: str, attributes: Optional[dict] = None) -> None:
        pass

    def end(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


_NOOP_SPAN = _NoOpSpan()


# ── Public API ────────────────────────────────────────────────────────


@contextmanager
def optional_span(service_name: str, operation_name: str):
    """Context manager that yields a real or no-op span.

    When OpenTelemetry is available, creates and manages a real span.
    Otherwise yields a ``_NoOpSpan`` that silently drops all calls.

    Args:
        service_name: Logical service name (e.g. "jorge.alerting").
        operation_name: Operation being traced (e.g. "check_alerts").

    Yields:
        A span-like object supporting ``set_attribute``, ``set_status``,
        ``record_exception``, ``add_event``, and ``end``.
    """
    if _otel_available and _tracer is not None:
        span_name = f"{service_name}.{operation_name}"
        with _tracer.start_as_current_span(span_name) as span:
            span.set_attribute("jorge.service", service_name)
            span.set_attribute("jorge.operation", operation_name)
            start = time.perf_counter()
            try:
                yield span
                span.set_attribute("jorge.success", True)
            except Exception as exc:
                span.set_attribute("jorge.success", False)
                span.record_exception(exc)
                span.set_status(OtelStatusCode.ERROR, str(exc))
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                span.set_attribute("jorge.duration_ms", round(elapsed_ms, 2))
    else:
        yield _NOOP_SPAN


def trace_operation(service_name: str, operation_name: str):
    """Decorator that wraps a sync or async function in a trace span.

    Automatically captures:
        - ``jorge.service`` / ``jorge.operation`` attributes
        - ``jorge.success`` and ``jorge.duration_ms``
        - Exceptions as span events (re-raised after recording)

    Works transparently as a no-op when OpenTelemetry is not installed.

    Args:
        service_name: Logical service name (e.g. "jorge.metrics").
        operation_name: Operation being traced (e.g. "record_interaction").

    Returns:
        A decorator applicable to both sync and async functions.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with optional_span(service_name, operation_name) as span:
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with optional_span(service_name, operation_name) as span:
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator


def is_otel_available() -> bool:
    """Return True if the OpenTelemetry SDK is importable."""
    return _otel_available


# ── Metric Counters ──────────────────────────────────────────────────

_meter = None
_counters: dict = {}

try:
    from opentelemetry import metrics as otel_metrics

    _meter = otel_metrics.get_meter("jorge-services", "1.0.0")
    _counters = {
        "jorge.interaction.total": _meter.create_counter(
            "jorge.interaction.total",
            description="Total bot interactions processed",
            unit="1",
        ),
        "jorge.handoff.total": _meter.create_counter(
            "jorge.handoff.total",
            description="Total handoff events",
            unit="1",
        ),
        "jorge.alert.triggered": _meter.create_counter(
            "jorge.alert.triggered",
            description="Total alerts triggered",
            unit="1",
        ),
        "jorge.webhook.dedup.total": _meter.create_counter(
            "jorge.webhook.dedup.total",
            description="Total webhook dedup decisions",
            unit="1",
        ),
        "jorge.webhook.dedup.duplicate": _meter.create_counter(
            "jorge.webhook.dedup.duplicate",
            description="Duplicate webhook events ignored",
            unit="1",
        ),
        "jorge.webhook.dedup.cache_error": _meter.create_counter(
            "jorge.webhook.dedup.cache_error",
            description="Webhook dedup cache backend failures",
            unit="1",
        ),
        "jorge.webhook.dedup.fallback": _meter.create_counter(
            "jorge.webhook.dedup.fallback",
            description="Webhook dedup fallback usage without delivery header",
            unit="1",
        ),
    }
    logger.info("OTel metric counters created for jorge services")
except ImportError:
    logger.debug("OTel metrics SDK not installed — counters are no-ops")
except Exception as exc:
    logger.debug("Failed to create OTel metric counters: %s", exc)


def increment_counter(name: str, value: int = 1, **attributes: Any) -> None:
    """Increment a named OTel counter.

    No-op if OTel is not available or the counter name is not registered.

    Args:
        name: Counter name (e.g. "jorge.interaction.total").
        value: Amount to increment (default 1).
        **attributes: Additional label attributes for the counter.
    """
    counter = _counters.get(name)
    if counter is not None:
        counter.add(value, attributes)


def add_jorge_attributes(span: Any, **kwargs: Any) -> None:
    """Add common Jorge service attributes to a span.

    Safely sets attributes on both real and no-op spans.

    Args:
        span: A span-like object (real OTel span or _NoOpSpan).
        **kwargs: Key-value pairs to set as ``jorge.<key>`` attributes.
            Common keys: bot_type, contact_id, route, outcome, duration_ms.
    """
    for key, value in kwargs.items():
        span.set_attribute(f"jorge.{key}", value)
