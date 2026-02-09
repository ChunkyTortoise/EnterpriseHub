"""Health check endpoints for Advanced RAG System.

Provides Kubernetes-compatible health checks with the following endpoints:
- /health - Overall health status
- /ready - Readiness probe (dependencies up)
- /live - Liveness probe (app running)

Supports health check registry pattern with checks for:
- Vector store connectivity
- Cache connectivity
- OpenAI API connectivity

Example:
    ```python
    from src.monitoring.health import health_checker, HealthStatus

    # Register custom health check
    async def check_database():
        # Perform database check
        return HealthStatus.healthy("Database connected")

    health_checker.register("database", check_database)

    # Get health status
    health = await health_checker.check()
    ```
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from src.core.config import Settings, get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration following Kubernetes standards.

    Attributes:
        HEALTHY: Service is healthy
        DEGRADED: Service is functional but degraded
        UNHEALTHY: Service is unhealthy
    """

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthResult:
    """Result of a health check.

    Attributes:
        status: Health status
        message: Human-readable status message
        details: Additional details about the check
        timestamp: When the check was performed
        response_time_ms: Response time in milliseconds
    """

    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    response_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format.

        Returns:
            Dictionary representation of health result
        """
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
            "response_time_ms": round(self.response_time_ms, 2),
        }

    @classmethod
    def healthy(
        cls,
        message: str = "OK",
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: float = 0.0,
    ) -> "HealthResult":
        """Create a healthy result.

        Args:
            message: Status message
            details: Additional details
            response_time_ms: Response time in milliseconds

        Returns:
            Healthy HealthResult
        """
        return cls(
            status=HealthStatus.HEALTHY,
            message=message,
            details=details or {},
            response_time_ms=response_time_ms,
        )

    @classmethod
    def degraded(
        cls,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: float = 0.0,
    ) -> "HealthResult":
        """Create a degraded result.

        Args:
            message: Status message
            details: Additional details
            response_time_ms: Response time in milliseconds

        Returns:
            Degraded HealthResult
        """
        return cls(
            status=HealthStatus.DEGRADED,
            message=message,
            details=details or {},
            response_time_ms=response_time_ms,
        )

    @classmethod
    def unhealthy(
        cls,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        response_time_ms: float = 0.0,
    ) -> "HealthResult":
        """Create an unhealthy result.

        Args:
            message: Status message
            details: Additional details
            response_time_ms: Response time in milliseconds

        Returns:
            Unhealthy HealthResult
        """
        return cls(
            status=HealthStatus.UNHEALTHY,
            message=message,
            details=details or {},
            response_time_ms=response_time_ms,
        )


@dataclass
class AggregatedHealth:
    """Aggregated health status from multiple checks.

    Attributes:
        status: Overall health status
        checks: Individual check results
        timestamp: When the aggregation was performed
    """

    status: HealthStatus
    checks: Dict[str, HealthResult]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for JSON response.

        Returns:
            Dictionary representation following Kubernetes standards
        """
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "checks": {name: result.to_dict() for name, result in self.checks.items()},
        }

    def is_healthy(self) -> bool:
        """Check if overall status is healthy.

        Returns:
            True if status is healthy
        """
        return self.status == HealthStatus.HEALTHY

    def is_ready(self) -> bool:
        """Check if service is ready (healthy or degraded).

        Returns:
            True if status is healthy or degraded
        """
        return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


# Type alias for health check functions
HealthCheckFunc = Callable[[], Coroutine[Any, Any, HealthResult]]


class HealthChecker:
    """Health check registry and aggregator.

    Manages health checks for various components and provides
    aggregated health status for Kubernetes probes.

    Attributes:
        checks: Registered health check functions
        settings: Application settings
        timeout_seconds: Timeout for individual health checks
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        """Initialize the health checker.

        Args:
            settings: Application settings
            timeout_seconds: Timeout for health checks
        """
        self.checks: Dict[str, HealthCheckFunc] = {}
        self.settings = settings or get_settings()
        self.timeout_seconds = timeout_seconds
        self._initialized = False

    def register(
        self,
        name: str,
        check_func: HealthCheckFunc,
    ) -> None:
        """Register a health check.

        Args:
            name: Name of the health check
            check_func: Async function that returns HealthResult
        """
        self.checks[name] = check_func
        logger.debug("health_check_registered", name=name)

    def unregister(self, name: str) -> None:
        """Unregister a health check.

        Args:
            name: Name of the health check to remove
        """
        if name in self.checks:
            del self.checks[name]
            logger.debug("health_check_unregistered", name=name)

    async def check(self, check_names: Optional[List[str]] = None) -> AggregatedHealth:
        """Run all or specified health checks.

        Args:
            check_names: Optional list of specific checks to run

        Returns:
            Aggregated health status
        """
        checks_to_run = (
            {name: self.checks[name] for name in check_names if name in self.checks} if check_names else self.checks
        )

        if not checks_to_run:
            return AggregatedHealth(
                status=HealthStatus.HEALTHY,
                checks={},
            )

        # Run all checks concurrently with timeout
        results: Dict[str, HealthResult] = {}
        tasks = []

        for name, check_func in checks_to_run.items():
            task = self._run_check_with_timeout(name, check_func)
            tasks.append((name, task))

        # Wait for all tasks
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
            except Exception as e:
                logger.error("health_check_failed", name=name, error=str(e))
                results[name] = HealthResult.unhealthy(
                    message=f"Check failed: {str(e)}",
                    details={"error": str(e)},
                )

        # Aggregate status
        overall_status = self._aggregate_status(results)

        return AggregatedHealth(
            status=overall_status,
            checks=results,
        )

    async def _run_check_with_timeout(
        self,
        name: str,
        check_func: HealthCheckFunc,
    ) -> HealthResult:
        """Run a single health check with timeout.

        Args:
            name: Check name
            check_func: Health check function

        Returns:
            Health result
        """
        start_time = time.perf_counter()
        try:
            result = await asyncio.wait_for(
                check_func(),
                timeout=self.timeout_seconds,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result.response_time_ms = elapsed_ms
            return result
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.warning("health_check_timeout", name=name, timeout=self.timeout_seconds)
            return HealthResult.unhealthy(
                message=f"Health check timed out after {self.timeout_seconds}s",
                details={"timeout_seconds": self.timeout_seconds},
                response_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error("health_check_exception", name=name, error=str(e))
            return HealthResult.unhealthy(
                message=f"Health check exception: {str(e)}",
                details={"error": str(e)},
                response_time_ms=elapsed_ms,
            )

    def _aggregate_status(self, results: Dict[str, HealthResult]) -> HealthStatus:
        """Aggregate individual check statuses.

        Rules:
        - If any check is unhealthy, overall is unhealthy
        - If any check is degraded and none unhealthy, overall is degraded
        - Otherwise, healthy

        Args:
            results: Individual check results

        Returns:
            Aggregated health status
        """
        statuses = [r.status for r in results.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    async def health(self) -> AggregatedHealth:
        """Get overall health status.

        Returns:
            Aggregated health status for /health endpoint
        """
        return await self.check()

    async def ready(self) -> AggregatedHealth:
        """Get readiness status.

        Returns:
            Aggregated health status for /ready endpoint
        """
        return await self.check()

    async def live(self) -> HealthResult:
        """Get liveness status.

        Returns:
            Health result for /live endpoint
        """
        return HealthResult.healthy("Application is running")


# Global health checker instance
health_checker = HealthChecker()


# Built-in health check implementations


async def check_vector_store() -> HealthResult:
    """Check vector store connectivity.

    Returns:
        Health result for vector store
    """
    start_time = time.perf_counter()
    try:
        from src.vector_store.chroma_store import ChromaVectorStore

        settings = get_settings()

        # Create a temporary store instance to check connectivity
        store = ChromaVectorStore(
            collection_name=settings.vector_store_collection,
            persist_directory=settings.vector_store_path,
        )

        # Try to get collection info
        await store.initialize()
        count = await store.count()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return HealthResult.healthy(
            message="Vector store is accessible",
            details={
                "type": settings.vector_store_type,
                "collection": settings.vector_store_collection,
                "document_count": count,
            },
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return HealthResult.unhealthy(
            message=f"Vector store check failed: {str(e)}",
            details={"error": str(e)},
            response_time_ms=elapsed_ms,
        )


async def check_cache() -> HealthResult:
    """Check cache connectivity.

    Returns:
        Health result for cache
    """
    start_time = time.perf_counter()
    try:
        settings = get_settings()

        if not settings.cache_enabled:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return HealthResult.healthy(
                message="Cache is disabled",
                details={"enabled": False},
                response_time_ms=elapsed_ms,
            )

        if settings.cache_type == "redis" and settings.redis_url:
            # Check Redis connectivity
            import redis.asyncio as redis

            client = redis.from_url(settings.redis_url)
            await client.ping()
            await client.close()

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return HealthResult.healthy(
                message="Redis cache is accessible",
                details={
                    "type": "redis",
                    "url": settings.redis_url.replace("://", "://***@"),  # Mask credentials
                },
                response_time_ms=elapsed_ms,
            )
        else:
            # Memory cache is always available if enabled
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            return HealthResult.healthy(
                message="Memory cache is available",
                details={"type": "memory"},
                response_time_ms=elapsed_ms,
            )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return HealthResult.unhealthy(
            message=f"Cache check failed: {str(e)}",
            details={"error": str(e)},
            response_time_ms=elapsed_ms,
        )


async def check_openai_api() -> HealthResult:
    """Check OpenAI API connectivity.

    Returns:
        Health result for OpenAI API
    """
    start_time = time.perf_counter()
    try:
        import openai

        settings = get_settings()
        api_key = settings.get_openai_api_key()

        client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url=settings.openai_base_url,
        )

        # Make a lightweight API call to verify connectivity
        # List models is a lightweight operation
        await client.models.list()

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return HealthResult.healthy(
            message="OpenAI API is accessible",
            details={
                "base_url": settings.openai_base_url or "https://api.openai.com",
                "timeout": settings.openai_timeout,
            },
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return HealthResult.unhealthy(
            message=f"OpenAI API check failed: {str(e)}",
            details={"error": str(e)},
            response_time_ms=elapsed_ms,
        )


async def check_embeddings_provider() -> HealthResult:
    """Check embeddings provider connectivity.

    Returns:
        Health result for embeddings provider
    """
    start_time = time.perf_counter()
    try:
        from src.embeddings.openai_provider import OpenAIEmbeddingProvider

        settings = get_settings()
        provider = OpenAIEmbeddingProvider(
            model=settings.openai_embedding_model,
            api_key=settings.get_openai_api_key(),
        )

        # Try to generate a test embedding
        test_text = "health check"
        await provider.embed(test_text)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return HealthResult.healthy(
            message="Embeddings provider is accessible",
            details={
                "model": settings.openai_embedding_model,
                "dimensions": settings.openai_embedding_dimensions,
            },
            response_time_ms=elapsed_ms,
        )
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return HealthResult.unhealthy(
            message=f"Embeddings provider check failed: {str(e)}",
            details={"error": str(e)},
            response_time_ms=elapsed_ms,
        )


def initialize_default_checks() -> None:
    """Register default health checks."""
    health_checker.register("vector_store", check_vector_store)
    health_checker.register("cache", check_cache)
    health_checker.register("openai_api", check_openai_api)
    health_checker.register("embeddings", check_embeddings_provider)
    logger.info("default_health_checks_registered")
