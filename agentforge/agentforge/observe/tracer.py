"""OpenTelemetry tracing for AgentForge.

This module provides OpenTelemetry-based tracing for agent executions,
following the Agent Observability Standard (AOS) mapped to OTel concepts.

Supports:
- Agent execution spans
- Tool call spans
- LLM call spans with token usage
- DAG execution spans
- Optional OTLP export for production observability
"""

import functools
import inspect
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from pydantic import BaseModel

# Handle optional OpenTelemetry dependency
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    TracerProvider = None
    SimpleSpanProcessor = None
    ConsoleSpanExporter = None
    Resource = None


class TracerConfig(BaseModel):
    """Configuration for tracing.

    Attributes:
        service_name: Name of the service for tracing.
        service_version: Version of the service.
        export_console: Whether to export traces to console.
        export_otlp: Whether to export traces via OTLP.
        otlp_endpoint: OTLP endpoint URL (e.g., "http://localhost:4317").
    """
    service_name: str = "agentforge"
    service_version: str = "0.2.0"
    export_console: bool = True
    export_otlp: bool = False
    otlp_endpoint: str | None = None


class TracerNotAvailableError(Exception):
    """Raised when OpenTelemetry is not installed."""
    pass


class AgentTracer:
    """OpenTelemetry tracer for AgentForge.

    Provides context managers for tracing different types of operations:
    - Agent executions
    - Tool calls
    - LLM calls
    - DAG executions

    Example:
        ```python
        tracer = AgentTracer(TracerConfig(service_name="my-app"))

        with tracer.trace_agent("my-agent") as span:
            # Agent execution
            tracer.record_llm_usage(span, 100, 50, 0.002)
        ```
    """

    def __init__(self, config: TracerConfig | None = None):
        """Initialize the tracer.

        Args:
            config: Tracer configuration. Uses defaults if not provided.

        Raises:
            TracerNotAvailableError: If OpenTelemetry is not installed.
        """
        self.config = config or TracerConfig()
        self._tracer = None

        if OPENTELEMETRY_AVAILABLE:
            self._setup_tracer()
        else:
            # Create a no-op tracer for graceful degradation
            self._tracer = _NoOpTracer()

    def _setup_tracer(self) -> None:
        """Set up OpenTelemetry tracer with configured exporters."""
        resource = Resource.create({
            "service.name": self.config.service_name,
            "service.version": self.config.service_version,
        })
        provider = TracerProvider(resource=resource)

        if self.config.export_console:
            provider.add_span_processor(
                SimpleSpanProcessor(ConsoleSpanExporter())
            )

        if self.config.export_otlp and self.config.otlp_endpoint:
            # OTLP exporter (optional)
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                provider.add_span_processor(
                    SimpleSpanProcessor(OTLPSpanExporter(endpoint=self.config.otlp_endpoint))
                )
            except ImportError:
                pass  # OTLP exporter not installed, skip

        trace.set_tracer_provider(provider)
        self._tracer = trace.get_tracer("agentforge")

    @property
    def tracer(self):
        """Get the underlying tracer."""
        return self._tracer

    @contextmanager
    def trace_agent(self, agent_name: str):
        """Context manager for tracing agent execution.

        Args:
            agent_name: Name of the agent being executed.

        Yields:
            The span for the agent execution.

        Example:
            ```python
            with tracer.trace_agent("lead-bot") as span:
                result = await agent.execute(input)
                span.set_attribute("agentforge.result.status", "success")
            ```
        """
        with self._tracer.start_as_current_span(
            f"agent.{agent_name}",
            attributes={
                "agentforge.agent.name": agent_name,
                "agentforge.type": "agent",
            }
        ) as span:
            yield span

    @contextmanager
    def trace_tool_call(self, tool_name: str, agent_name: str):
        """Context manager for tracing tool calls.

        Args:
            tool_name: Name of the tool being called.
            agent_name: Name of the agent calling the tool.

        Yields:
            The span for the tool call.

        Example:
            ```python
            with tracer.trace_tool_call("search", "lead-bot") as span:
                result = tool.execute(params)
                span.set_attribute("agentforge.tool.result_size", len(result))
            ```
        """
        with self._tracer.start_as_current_span(
            f"tool.{tool_name}",
            attributes={
                "agentforge.tool.name": tool_name,
                "agentforge.agent.name": agent_name,
                "agentforge.type": "tool",
            }
        ) as span:
            yield span

    @contextmanager
    def trace_llm_call(self, model: str, provider: str = "unknown"):
        """Context manager for tracing LLM calls.

        Args:
            model: Name of the LLM model (e.g., "gpt-4o", "claude-3-opus").
            provider: Name of the LLM provider (e.g., "openai", "anthropic").

        Yields:
            The span for the LLM call.

        Example:
            ```python
            with tracer.trace_llm_call("gpt-4o", "openai") as span:
                response = await llm.complete(messages)
                tracer.record_llm_usage(span, response.usage.prompt_tokens,
                                        response.usage.completion_tokens)
            ```
        """
        with self._tracer.start_as_current_span(
            f"llm.{model}",
            attributes={
                "gen_ai.model": model,
                "gen_ai.provider": provider,
                "agentforge.type": "llm",
            }
        ) as span:
            yield span

    @contextmanager
    def trace_dag_execution(self, dag_name: str, node_count: int):
        """Context manager for tracing DAG execution.

        Args:
            dag_name: Name of the DAG being executed.
            node_count: Number of nodes in the DAG.

        Yields:
            The span for the DAG execution.

        Example:
            ```python
            with tracer.trace_dag_execution("lead-workflow", 5) as span:
                result = await engine.execute(dag)
                span.set_attribute("agentforge.dag.success", True)
            ```
        """
        with self._tracer.start_as_current_span(
            f"dag.{dag_name}",
            attributes={
                "agentforge.dag.name": dag_name,
                "agentforge.dag.node_count": node_count,
                "agentforge.type": "dag",
            }
        ) as span:
            yield span

    def record_llm_usage(
        self,
        span,
        prompt_tokens: int,
        completion_tokens: int,
        cost: float = 0.0
    ) -> None:
        """Record LLM token usage on a span.

        Args:
            span: The span to record usage on.
            prompt_tokens: Number of prompt tokens used.
            completion_tokens: Number of completion tokens generated.
            cost: Cost in USD for this LLM call.
        """
        if span is None:
            return
        span.set_attributes({
            "gen_ai.usage.prompt_tokens": prompt_tokens,
            "gen_ai.usage.completion_tokens": completion_tokens,
            "agentforge.cost.usd": cost,
        })

    def record_error(self, span, error: Exception) -> None:
        """Record an error on a span.

        Args:
            span: The span to record the error on.
            error: The exception that occurred.
        """
        if span is None or not OPENTELEMETRY_AVAILABLE:
            return
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
        span.record_exception(error)

    def trace_function(self, name: str | None = None):
        """Decorator for tracing functions.

        Args:
            name: Optional name for the span. Uses function name if not provided.

        Returns:
            Decorator that wraps the function with tracing.

        Example:
            ```python
            @tracer.trace_function("process_lead")
            async def process_lead(lead_id: str) -> dict:
                # Processing logic
                return {"status": "qualified"}
            ```
        """
        def decorator(func: Callable) -> Callable:
            trace_name = name or func.__name__

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self._tracer.start_as_current_span(trace_name):
                    return await func(*args, **kwargs)

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self._tracer.start_as_current_span(trace_name):
                    return func(*args, **kwargs)

            if inspect.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


class _NoOpSpan:
    """No-op span for when OpenTelemetry is not available."""

    def set_attribute(self, key: str, value: Any) -> None:
        """No-op set attribute."""
        pass

    def set_attributes(self, attributes: dict) -> None:
        """No-op set attributes."""
        pass

    def record_exception(self, exception: Exception) -> None:
        """No-op record exception."""
        pass

    def set_status(self, status: Any) -> None:
        """No-op set status."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _NoOpTracer:
    """No-op tracer for when OpenTelemetry is not available."""

    @contextmanager
    def start_as_current_span(self, name: str, attributes: dict | None = None):
        """Start a no-op span."""
        yield _NoOpSpan()


# Global tracer instance
_global_tracer: AgentTracer | None = None


def get_tracer(config: TracerConfig | None = None) -> AgentTracer:
    """Get or create the global tracer.

    Args:
        config: Optional configuration. Only used on first call.

    Returns:
        The global AgentTracer instance.

    Example:
        ```python
        tracer = get_tracer(TracerConfig(service_name="my-app"))

        # Later, get the same tracer
        tracer = get_tracer()
        ```
    """
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = AgentTracer(config)
    return _global_tracer


def reset_tracer() -> None:
    """Reset the global tracer.

    Useful for testing or reconfiguring the tracer.
    """
    global _global_tracer
    _global_tracer = None


__all__ = [
    "TracerConfig",
    "AgentTracer",
    "TracerNotAvailableError",
    "get_tracer",
    "reset_tracer",
    "OPENTELEMETRY_AVAILABLE",
]
