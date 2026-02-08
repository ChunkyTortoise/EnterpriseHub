"""Production monitoring infrastructure for Advanced RAG System.

This module provides comprehensive monitoring capabilities including:
- Prometheus metrics collection
- Kubernetes-compatible health checks
- Distributed tracing with OpenTelemetry

Example:
    ```python
    from src.monitoring import metrics_collector, track_latency
    from src.monitoring import health_checker, HealthStatus
    from src.monitoring import tracer, trace_span

    # Metrics
    @track_latency(operation="search")
    async def search(query: str):
        return await perform_search(query)

    # Health checks
    health_checker.register("vector_store", check_vector_store)
    status = await health_checker.check()

    # Tracing
    @trace_span("process_query")
    async def process_query(query: str):
        return await process(query)
    ```
"""

from src.monitoring.health import (
    HealthChecker,
    HealthResult,
    HealthStatus,
    health_checker,
)
from src.monitoring.metrics import (
    MetricsCollector,
    count_tokens,
    increment_errors,
    increment_requests,
    metrics_collector,
    record_accuracy,
    track_latency,
)
from src.monitoring.tracing import (
    Tracer,
    get_current_span,
    set_span_attribute,
    trace_span,
    tracer,
)

__all__ = [
    # Metrics
    "MetricsCollector",
    "metrics_collector",
    "track_latency",
    "count_tokens",
    "record_accuracy",
    "increment_errors",
    "increment_requests",
    # Health
    "HealthChecker",
    "HealthStatus",
    "HealthResult",
    "health_checker",
    # Tracing
    "Tracer",
    "tracer",
    "trace_span",
    "get_current_span",
    "set_span_attribute",
]
