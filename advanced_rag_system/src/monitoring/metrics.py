"""Prometheus metrics integration for Advanced RAG System.

Provides comprehensive metrics collection for production monitoring including:
- Search latency histograms (p50, p95, p99)
- Token usage counters (embedding tokens, LLM tokens)
- Retrieval accuracy gauges
- Error rate counters
- Request throughput counters
- Active connections gauge

Example:
    ```python
    from src.monitoring.metrics import metrics_collector, track_latency

    # Automatic metric collection via decorator
    @track_latency(operation="search", component="retrieval")
    async def search_documents(query: str):
        return await perform_search(query)

    # Manual metric recording
    metrics_collector.count_tokens("embedding", tokens=150)
    metrics_collector.record_accuracy("retrieval", accuracy=0.95)
    metrics_collector.increment_errors(error_type="timeout")
    ```
"""

from __future__ import annotations

import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_client.core import CollectorRegistry

from src.core.config import Settings, get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class MetricsCollector:
    """Centralized metrics collector for RAG system.

    Provides Prometheus-compatible metrics for production monitoring.
    All metrics are prefixed with 'rag_' for easy identification.

    Attributes:
        registry: Prometheus CollectorRegistry instance
        settings: Application settings
    """

    def __init__(
        self,
        registry: Optional[CollectorRegistry] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initialize the metrics collector.

        Args:
            registry: Optional Prometheus registry (creates new if None)
            settings: Optional settings instance
        """
        self.registry = registry or CollectorRegistry()
        self.settings = settings or get_settings()
        self._initialized = False

        # Application info
        self._app_info = Info(
            "rag_app",
            "Application information",
            registry=self.registry,
        )

        # Search latency histogram with configurable buckets for p50, p95, p99
        self._search_latency = Histogram(
            "rag_search_latency_seconds",
            "Search operation latency in seconds",
            ["operation", "component", "status"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
            registry=self.registry,
        )

        # Token usage counters
        self._token_usage = Counter(
            "rag_tokens_total",
            "Total token usage",
            ["type", "model", "operation"],
            registry=self.registry,
        )

        # Retrieval accuracy gauge
        self._retrieval_accuracy = Gauge(
            "rag_retrieval_accuracy",
            "Retrieval accuracy score (0-1)",
            ["component", "metric_type"],
            registry=self.registry,
        )

        # Error counters
        self._errors = Counter(
            "rag_errors_total",
            "Total error count",
            ["error_type", "component", "operation"],
            registry=self.registry,
        )

        # Request throughput
        self._requests = Counter(
            "rag_requests_total",
            "Total request count",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        # Active connections gauge
        self._active_connections = Gauge(
            "rag_active_connections",
            "Number of active connections",
            ["component"],
            registry=self.registry,
        )

        # Queue size gauge
        self._queue_size = Gauge(
            "rag_queue_size",
            "Current queue size",
            ["queue_name"],
            registry=self.registry,
        )

        # Cache metrics
        self._cache_hits = Counter(
            "rag_cache_hits_total",
            "Total cache hits",
            ["cache_type"],
            registry=self.registry,
        )
        self._cache_misses = Counter(
            "rag_cache_misses_total",
            "Total cache misses",
            ["cache_type"],
            registry=self.registry,
        )

        # Embedding generation metrics
        self._embedding_generation = Histogram(
            "rag_embedding_generation_seconds",
            "Embedding generation latency",
            ["model", "batch_size"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
            registry=self.registry,
        )

        # Document processing metrics
        self._documents_processed = Counter(
            "rag_documents_processed_total",
            "Total documents processed",
            ["operation", "status"],
            registry=self.registry,
        )

        # Reranking metrics
        self._reranking_latency = Histogram(
            "rag_reranking_latency_seconds",
            "Reranking operation latency",
            ["model", "num_documents"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
            registry=self.registry,
        )

    def initialize(self) -> None:
        """Initialize metrics with application info."""
        if self._initialized:
            return

        try:
            self._app_info.info(
                {
                    "name": self.settings.app_name,
                    "version": self.settings.app_version,
                    "debug": str(self.settings.debug),
                }
            )
            self._initialized = True
            logger.info("metrics_collector_initialized")
        except Exception as e:
            logger.error("metrics_initialization_failed", error=str(e))
            raise

    def observe_search_latency(
        self,
        duration: float,
        operation: str,
        component: str = "retrieval",
        status: str = "success",
    ) -> None:
        """Record search latency observation.

        Args:
            duration: Duration in seconds
            operation: Operation name (e.g., 'dense_search', 'hybrid_search')
            component: Component name (e.g., 'retrieval', 'reranking')
            status: Operation status ('success' or 'error')
        """
        self._search_latency.labels(
            operation=operation,
            component=component,
            status=status,
        ).observe(duration)

    def count_tokens(
        self,
        token_type: str,
        tokens: int,
        model: str = "unknown",
        operation: str = "unknown",
    ) -> None:
        """Record token usage.

        Args:
            token_type: Type of tokens ('embedding' or 'llm')
            tokens: Number of tokens
            model: Model name
            operation: Operation that used the tokens
        """
        self._token_usage.labels(
            type=token_type,
            model=model,
            operation=operation,
        ).inc(tokens)

    def record_accuracy(
        self,
        component: str,
        accuracy: float,
        metric_type: str = "precision",
    ) -> None:
        """Record accuracy metric.

        Args:
            component: Component being measured (e.g., 'retrieval', 'reranking')
            accuracy: Accuracy score (0-1)
            metric_type: Type of accuracy metric (e.g., 'precision', 'recall', 'ndcg')
        """
        self._retrieval_accuracy.labels(
            component=component,
            metric_type=metric_type,
        ).set(accuracy)

    def increment_errors(
        self,
        error_type: str,
        component: str = "unknown",
        operation: str = "unknown",
    ) -> None:
        """Increment error counter.

        Args:
            error_type: Type of error (e.g., 'timeout', 'rate_limit', 'validation')
            component: Component where error occurred
            operation: Operation that failed
        """
        self._errors.labels(
            error_type=error_type,
            component=component,
            operation=operation,
        ).inc()

    def increment_requests(
        self,
        method: str,
        endpoint: str,
        status_code: int = 200,
    ) -> None:
        """Increment request counter.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            status_code: HTTP status code
        """
        self._requests.labels(
            method=method.upper(),
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()

    def set_active_connections(
        self,
        count: int,
        component: str = "api",
    ) -> None:
        """Set active connections gauge.

        Args:
            count: Number of active connections
            component: Component name
        """
        self._active_connections.labels(component=component).set(count)

    def set_queue_size(
        self,
        size: int,
        queue_name: str = "default",
    ) -> None:
        """Set queue size gauge.

        Args:
            size: Current queue size
            queue_name: Name of the queue
        """
        self._queue_size.labels(queue_name=queue_name).set(size)

    def record_cache_hit(self, cache_type: str = "memory") -> None:
        """Record cache hit.

        Args:
            cache_type: Type of cache (memory, redis)
        """
        self._cache_hits.labels(cache_type=cache_type).inc()

    def record_cache_miss(self, cache_type: str = "memory") -> None:
        """Record cache miss.

        Args:
            cache_type: Type of cache (memory, redis)
        """
        self._cache_misses.labels(cache_type=cache_type).inc()

    def observe_embedding_generation(
        self,
        duration: float,
        model: str,
        batch_size: int,
    ) -> None:
        """Record embedding generation latency.

        Args:
            duration: Duration in seconds
            model: Embedding model name
            batch_size: Number of texts in batch
        """
        self._embedding_generation.labels(
            model=model,
            batch_size=str(batch_size),
        ).observe(duration)

    def increment_documents_processed(
        self,
        operation: str,
        count: int = 1,
        status: str = "success",
    ) -> None:
        """Increment documents processed counter.

        Args:
            operation: Operation type (index, delete, update)
            count: Number of documents
            status: Processing status
        """
        self._documents_processed.labels(
            operation=operation,
            status=status,
        ).inc(count)

    def observe_reranking(
        self,
        duration: float,
        model: str,
        num_documents: int,
    ) -> None:
        """Record reranking latency.

        Args:
            duration: Duration in seconds
            model: Reranking model name
            num_documents: Number of documents reranked
        """
        # Bucket the number of documents for cardinality control
        bucket = self._bucket_documents(num_documents)
        self._reranking_latency.labels(
            model=model,
            num_documents=bucket,
        ).observe(duration)

    def _bucket_documents(self, n: int) -> str:
        """Bucket document counts for label cardinality control.

        Args:
            n: Number of documents

        Returns:
            Bucket label string
        """
        if n <= 1:
            return "1"
        elif n <= 5:
            return "5"
        elif n <= 10:
            return "10"
        elif n <= 25:
            return "25"
        elif n <= 50:
            return "50"
        elif n <= 100:
            return "100"
        else:
            return "100+"

    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus exposition format.

        Returns:
            Metrics as bytes in Prometheus format
        """
        return generate_latest(self.registry)

    def get_content_type(self) -> str:
        """Get Prometheus content type header value.

        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST


# Global metrics collector instance
metrics_collector = MetricsCollector()


def track_latency(
    operation: str,
    component: str = "retrieval",
    track_errors: bool = True,
) -> Callable[[F], F]:
    """Decorator for tracking function latency.

    Automatically records latency metrics for the decorated function.

    Args:
        operation: Operation name for the metric label
        component: Component name for the metric label
        track_errors: Whether to track errors separately

    Returns:
        Decorated function

    Example:
        ```python
        @track_latency(operation="dense_search", component="retrieval")
        async def search_documents(query: str):
            return await perform_search(query)
        ```
    """

    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                if track_errors:
                    metrics_collector.increment_errors(
                        error_type=type(e).__name__,
                        component=component,
                        operation=operation,
                    )
                raise
            finally:
                duration = time.perf_counter() - start_time
                metrics_collector.observe_search_latency(
                    duration=duration,
                    operation=operation,
                    component=component,
                    status=status,
                )

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                if track_errors:
                    metrics_collector.increment_errors(
                        error_type=type(e).__name__,
                        component=component,
                        operation=operation,
                    )
                raise
            finally:
                duration = time.perf_counter() - start_time
                metrics_collector.observe_search_latency(
                    duration=duration,
                    operation=operation,
                    component=component,
                    status=status,
                )

        return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]

    return decorator


def count_tokens(
    token_type: str,
    model: str = "unknown",
    operation: str = "unknown",
) -> Callable[[F], F]:
    """Decorator for tracking token usage.

    The decorated function should return a dict with 'tokens_used' key,
    or the decorator can infer from response object.

    Args:
        token_type: Type of tokens ('embedding' or 'llm')
        model: Model name
        operation: Operation name

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            # Try to extract token count from result
            tokens = _extract_token_count(result)
            if tokens > 0:
                metrics_collector.count_tokens(token_type, tokens, model, operation)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            tokens = _extract_token_count(result)
            if tokens > 0:
                metrics_collector.count_tokens(token_type, tokens, model, operation)
            return result

        return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]

    return decorator


def _extract_token_count(result: Any) -> int:
    """Extract token count from various result types.

    Args:
        result: Function result

    Returns:
        Token count or 0 if not found
    """
    if isinstance(result, dict):
        # Check common token count keys
        for key in ["tokens_used", "total_tokens", "prompt_tokens", "completion_tokens"]:
            if key in result:
                return int(result[key])
    elif hasattr(result, "usage"):
        usage = result.usage
        if hasattr(usage, "total_tokens"):
            return int(usage.total_tokens)
        elif isinstance(usage, dict) and "total_tokens" in usage:
            return int(usage["total_tokens"])
    return 0


def record_accuracy(
    component: str,
    metric_type: str = "precision",
) -> Callable[[F], F]:
    """Decorator for tracking accuracy metrics.

    The decorated function should return a dict with 'accuracy' key
    or a float accuracy value.

    Args:
        component: Component being measured
        metric_type: Type of accuracy metric

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        is_async = asyncio.iscoroutinefunction(func)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await func(*args, **kwargs)
            accuracy = _extract_accuracy(result)
            if accuracy is not None:
                metrics_collector.record_accuracy(component, accuracy, metric_type)
            return result

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            accuracy = _extract_accuracy(result)
            if accuracy is not None:
                metrics_collector.record_accuracy(component, accuracy, metric_type)
            return result

        return async_wrapper if is_async else sync_wrapper  # type: ignore[return-value]

    return decorator


def _extract_accuracy(result: Any) -> Optional[float]:
    """Extract accuracy value from result.

    Args:
        result: Function result

    Returns:
        Accuracy value or None if not found
    """
    if isinstance(result, (int, float)):
        return float(result)
    elif isinstance(result, dict):
        for key in ["accuracy", "score", "precision", "recall", "ndcg", "mrr"]:
            if key in result:
                return float(result[key])
    return None


def increment_errors(
    error_type: str,
    component: str = "unknown",
    operation: str = "unknown",
) -> None:
    """Increment error counter (convenience function).

    Args:
        error_type: Type of error
        component: Component where error occurred
        operation: Operation that failed
    """
    metrics_collector.increment_errors(error_type, component, operation)


def increment_requests(
    method: str,
    endpoint: str,
    status_code: int = 200,
) -> None:
    """Increment request counter (convenience function).

    Args:
        method: HTTP method
        endpoint: API endpoint
        status_code: HTTP status code
    """
    metrics_collector.increment_requests(method, endpoint, status_code)


@contextmanager
def latency_context(
    operation: str,
    component: str = "retrieval",
) -> Any:
    """Context manager for tracking latency of arbitrary code blocks.

    Args:
        operation: Operation name
        component: Component name

    Example:
        ```python
        with latency_context("custom_operation", "processing"):
            # Your code here
            process_data()
        ```
    """
    start_time = time.perf_counter()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        duration = time.perf_counter() - start_time
        metrics_collector.observe_search_latency(
            duration=duration,
            operation=operation,
            component=component,
            status=status,
        )


# Import asyncio here to avoid circular import issues
import asyncio
