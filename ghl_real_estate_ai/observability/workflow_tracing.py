"""
OpenTelemetry Distributed Tracing for LangGraph Workflows

Provides decorators and context managers for instrumenting LangGraph workflow nodes
with OpenTelemetry spans. Supports:
- Automatic span creation for workflow nodes
- Cross-bot correlation via trace context propagation
- Rich span attributes (bot type, contact ID, node name, etc.)
- Manual span management for complex workflows

Usage:
    from ghl_real_estate_ai.observability.workflow_tracing import trace_workflow_node

    @trace_workflow_node("lead_bot", "analyze_intent")
    async def analyze_intent(state: Dict) -> Dict:
        # Workflow logic
        return updated_state

    # Manual span creation:
    from ghl_real_estate_ai.observability.workflow_tracing import workflow_span

    async with workflow_span("seller_bot", "qualify", contact_id=contact_id) as span:
        span.set_attribute("seller.frs_score", 85.5)
        # Processing logic
"""

import functools
import inspect
import logging
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# ── Detect OpenTelemetry availability ─────────────────────────────────

_otel_available = False
_tracer = None

try:
    from opentelemetry import trace as otel_trace
    from opentelemetry.trace import Status, StatusCode

    _otel_available = True
    _tracer = otel_trace.get_tracer("jorge-workflows", "1.0.0")
    logger.info("OpenTelemetry SDK detected — workflow tracing enabled")
except ImportError:
    logger.debug("OpenTelemetry SDK not installed — workflow tracing disabled")


# ── No-op span stub ───────────────────────────────────────────────────


class _NoOpSpan:
    """Minimal span stub that silently accepts all span operations."""

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


# ── Span Context Managers ─────────────────────────────────────────────


@contextmanager
def workflow_span(
    bot_type: str,
    node_name: str,
    contact_id: Optional[str] = None,
    **attributes: Any,
):
    """Create a synchronous span for a workflow node.

    Args:
        bot_type: Bot type ("lead_bot", "buyer_bot", "seller_bot").
        node_name: Node name (e.g., "analyze_intent", "generate_response").
        contact_id: Optional contact/lead ID for correlation.
        **attributes: Additional attributes to set on the span.

    Yields:
        A span object (real OTel span or no-op stub).
    """
    if not _otel_available or _tracer is None:
        yield _NOOP_SPAN
        return

    span_name = f"{bot_type}.{node_name}"
    with _tracer.start_as_current_span(span_name) as span:
        # Set standard workflow attributes
        span.set_attribute("workflow.bot_type", bot_type)
        span.set_attribute("workflow.node_name", node_name)
        if contact_id:
            span.set_attribute("workflow.contact_id", contact_id)

        # Set custom attributes
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(f"workflow.{key}", value)

        start = time.perf_counter()
        try:
            yield span
            span.set_attribute("workflow.success", True)
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_attribute("workflow.success", False)
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            span.set_attribute("workflow.duration_ms", round(elapsed_ms, 2))


@asynccontextmanager
async def async_workflow_span(
    bot_type: str,
    node_name: str,
    contact_id: Optional[str] = None,
    **attributes: Any,
):
    """Create an async span for a workflow node.

    Args:
        bot_type: Bot type ("lead_bot", "buyer_bot", "seller_bot").
        node_name: Node name (e.g., "analyze_intent", "generate_response").
        contact_id: Optional contact/lead ID for correlation.
        **attributes: Additional attributes to set on the span.

    Yields:
        A span object (real OTel span or no-op stub).
    """
    if not _otel_available or _tracer is None:
        yield _NOOP_SPAN
        return

    span_name = f"{bot_type}.{node_name}"
    with _tracer.start_as_current_span(span_name) as span:
        # Set standard workflow attributes
        span.set_attribute("workflow.bot_type", bot_type)
        span.set_attribute("workflow.node_name", node_name)
        if contact_id:
            span.set_attribute("workflow.contact_id", contact_id)

        # Set custom attributes
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(f"workflow.{key}", value)

        start = time.perf_counter()
        try:
            yield span
            span.set_attribute("workflow.success", True)
            span.set_status(Status(StatusCode.OK))
        except Exception as exc:
            span.set_attribute("workflow.success", False)
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            span.set_attribute("workflow.duration_ms", round(elapsed_ms, 2))


# ── Decorator for Workflow Nodes ──────────────────────────────────────


def trace_workflow_node(bot_type: str, node_name: str):
    """Decorator that instruments a LangGraph workflow node with tracing.

    Automatically captures:
        - workflow.bot_type, workflow.node_name
        - workflow.contact_id (from state["lead_id"] or state["contact_id"])
        - workflow.success, workflow.duration_ms
        - Exceptions as span events

    Works transparently as a no-op when OpenTelemetry is not installed.

    Args:
        bot_type: Bot type ("lead_bot", "buyer_bot", "seller_bot").
        node_name: Node name (e.g., "analyze_intent").

    Returns:
        A decorator applicable to both sync and async node functions.

    Example:
        @trace_workflow_node("lead_bot", "analyze_intent")
        async def analyze_intent(state: Dict) -> Dict:
            # Node logic
            return updated_state
    """

    def decorator(func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(state: Dict, *args, **kwargs) -> Dict:
                # Extract contact ID from state
                contact_id = state.get("lead_id") or state.get("contact_id")

                async with async_workflow_span(
                    bot_type, node_name, contact_id=contact_id
                ) as span:
                    # Add state metadata to span
                    if "current_step" in state:
                        span.set_attribute("workflow.current_step", state["current_step"])
                    if "temperature" in state:
                        span.set_attribute("workflow.temperature", state["temperature"])

                    result = await func(state, *args, **kwargs)
                    return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(state: Dict, *args, **kwargs) -> Dict:
                # Extract contact ID from state
                contact_id = state.get("lead_id") or state.get("contact_id")

                with workflow_span(bot_type, node_name, contact_id=contact_id) as span:
                    # Add state metadata to span
                    if "current_step" in state:
                        span.set_attribute("workflow.current_step", state["current_step"])
                    if "temperature" in state:
                        span.set_attribute("workflow.temperature", state["temperature"])

                    result = func(state, *args, **kwargs)
                    return result

            return sync_wrapper

    return decorator


# ── Cross-Bot Handoff Correlation ─────────────────────────────────────


def create_handoff_span(
    source_bot: str,
    target_bot: str,
    contact_id: str,
    confidence: float,
    reason: str,
) -> Any:
    """Create a span for a cross-bot handoff event.

    Args:
        source_bot: Source bot name ("lead", "buyer", "seller").
        target_bot: Target bot name ("lead", "buyer", "seller").
        contact_id: Contact ID being handed off.
        confidence: Handoff confidence score (0.0-1.0).
        reason: Handoff reason description.

    Returns:
        A context manager span (use with `with` statement).

    Example:
        with create_handoff_span("lead", "buyer", contact_id, 0.85, "buyer_intent"):
            # Execute handoff
            pass
    """
    if not _otel_available or _tracer is None:
        return _NOOP_SPAN

    span_name = f"handoff.{source_bot}_to_{target_bot}"
    span = _tracer.start_span(span_name)
    span.set_attribute("handoff.source_bot", source_bot)
    span.set_attribute("handoff.target_bot", target_bot)
    span.set_attribute("handoff.contact_id", contact_id)
    span.set_attribute("handoff.confidence", confidence)
    span.set_attribute("handoff.reason", reason)

    return span


def get_trace_id() -> str:
    """Get the current trace ID for correlation.

    Returns:
        Hex string trace ID, or empty string if no active span.
    """
    if not _otel_available:
        return ""

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
        return ""
    except Exception:
        return ""


def propagate_trace_context(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Inject trace context into metadata for cross-service propagation.

    Args:
        metadata: Dictionary to inject trace context into.

    Returns:
        The metadata dict with trace context injected.
    """
    if not _otel_available:
        return metadata

    try:
        from opentelemetry.propagate import inject

        inject(metadata)
    except Exception:
        pass

    return metadata


def extract_trace_context(metadata: Dict[str, Any]) -> None:
    """Extract trace context from metadata and set as current.

    Args:
        metadata: Dictionary containing trace context headers.
    """
    if not _otel_available:
        return

    try:
        from opentelemetry.propagate import extract

        extract(metadata)
    except Exception:
        pass


# ── Utility Functions ─────────────────────────────────────────────────


def is_tracing_enabled() -> bool:
    """Return True if OpenTelemetry tracing is available and enabled."""
    return _otel_available


def add_workflow_event(event_name: str, **attributes: Any) -> None:
    """Add an event to the current span (if any).

    Args:
        event_name: Event name (e.g., "cache_hit", "intent_detected").
        **attributes: Additional attributes to attach to the event.
    """
    if not _otel_available:
        return

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span.add_event(event_name, attributes)
    except Exception:
        pass
