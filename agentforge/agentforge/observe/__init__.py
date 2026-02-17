"""Observability module for AgentForge.

This module provides OpenTelemetry-based tracing, metrics collection,
and ASCII dashboard for monitoring agent executions.

Components:
- Tracer: OpenTelemetry tracing for agents, tools, LLM calls, and DAGs
- Metrics: Token usage, cost tracking, and latency statistics
- Dashboard: ASCII-based monitoring display

Example:
    ```python
    from agentforge.observe import (
        AgentTracer,
        TracerConfig,
        MetricsCollector,
        TokenUsage,
        ASCIIDashboard,
        get_tracer,
        get_metrics,
    )

    # Set up tracing
    tracer = get_tracer(TracerConfig(service_name="my-app"))

    # Set up metrics
    metrics = get_metrics()

    # Trace an agent execution
    with tracer.trace_agent("lead-bot") as span:
        result = await agent.execute(input)
        metrics.record_tokens("lead-bot", TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        ))

    # Display dashboard
    dashboard = ASCIIDashboard()
    dashboard.attach(metrics)
    dashboard.print()
    ```
"""

# Tracer exports
# Dashboard exports
from agentforge.observe.dashboard import (
    ASCIIDashboard,
    Dashboard,
    DashboardConfig,
    StructuredLogger,
    create_dashboard,
)

# Metrics exports
from agentforge.observe.metrics import (
    CostRecord,
    LatencyStats,
    MetricsCollector,
    TokenUsage,
    get_metrics,
    reset_metrics,
)
from agentforge.observe.tracer import (
    OPENTELEMETRY_AVAILABLE,
    AgentTracer,
    TracerConfig,
    TracerNotAvailableError,
    get_tracer,
    reset_tracer,
)

__all__ = [
    # Tracer
    "TracerConfig",
    "AgentTracer",
    "TracerNotAvailableError",
    "get_tracer",
    "reset_tracer",
    "OPENTELEMETRY_AVAILABLE",
    # Metrics
    "TokenUsage",
    "CostRecord",
    "LatencyStats",
    "MetricsCollector",
    "get_metrics",
    "reset_metrics",
    # Dashboard
    "Dashboard",
    "DashboardConfig",
    "ASCIIDashboard",
    "StructuredLogger",
    "create_dashboard",
]
