"""
Performance Integration Module

Central integration point for all performance optimization components.
Provides a unified API for:
- Optimized caching with L1+L2 architecture
- AI request batching and deduplication
- Performance monitoring and metrics
- Database connection pooling
- Health checks and alerting

Use this module to integrate performance optimizations into existing services.

Author: EnterpriseHub AI Performance Engineering
Version: 1.0.0
Last Updated: 2026-01-18
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from .ai_request_batcher import (
    AIRequestBatcher,
    RequestPriority,
    get_ai_request_batcher,
)

# Import optimized services
from .optimized_cache_service import (
    EnhancedCacheService,
    get_enhanced_cache_service,
)
from .performance_monitor import (
    PerformanceMonitor,
    get_performance_monitor,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PerformanceStatus:
    """Current system performance status"""

    status: str  # healthy, warning, critical
    cache_hit_rate: float
    api_p95_ms: float
    db_p95_ms: float
    concurrent_users: int
    active_alerts: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "cache_hit_rate": round(self.cache_hit_rate, 4),
            "api_p95_ms": round(self.api_p95_ms, 2),
            "db_p95_ms": round(self.db_p95_ms, 2),
            "concurrent_users": self.concurrent_users,
            "active_alerts": self.active_alerts,
            "timestamp": self.timestamp.isoformat(),
        }


class PerformanceIntegration:
    """
    Central performance integration service

    This class provides a unified interface for all performance optimizations.
    Use it to:
    - Initialize all performance services at startup
    - Get performance status and health checks
    - Record metrics across the application
    - Manage cache warming and invalidation

    Example usage:
        perf = PerformanceIntegration()
        await perf.initialize()

        # Use cached AI calls
        response = await perf.cached_ai_query("Analyze this lead", lead_id)

        # Get performance status
        status = await perf.get_status()

        # On shutdown
        await perf.shutdown()
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceIntegration, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.cache: Optional[EnhancedCacheService] = None
        self.ai_batcher: Optional[AIRequestBatcher] = None
        self.monitor: Optional[PerformanceMonitor] = None
        self._startup_time: Optional[datetime] = None

        self._initialized = True
        logger.info("PerformanceIntegration instance created")

    async def initialize(self, anthropic_client=None) -> bool:
        """
        Initialize all performance services

        Args:
            anthropic_client: Optional Anthropic client for AI batching

        Returns:
            bool: True if initialization successful
        """
        try:
            logger.info("Initializing performance services...")

            # Initialize cache service
            self.cache = get_enhanced_cache_service()
            await self.cache.warm_default_data()
            logger.info("Cache service initialized and warmed")

            # Initialize AI batcher
            self.ai_batcher = get_ai_request_batcher(anthropic_client)
            await self.ai_batcher.start_background_processor()
            logger.info("AI request batcher initialized")

            # Initialize performance monitor
            self.monitor = get_performance_monitor()
            await self.monitor.start_monitoring()
            logger.info("Performance monitor initialized")

            self._startup_time = datetime.now()
            logger.info("All performance services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize performance services: {e}")
            return False

    async def shutdown(self):
        """Shutdown all performance services gracefully"""
        logger.info("Shutting down performance services...")

        if self.ai_batcher:
            await self.ai_batcher.stop_background_processor()

        if self.monitor:
            await self.monitor.stop_monitoring()

        logger.info("Performance services shut down")

    # ========================================================================
    # CACHING METHODS
    # ========================================================================

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache:
            return None
        value = await self.cache.get(key)
        if value is not None:
            self.monitor.record_cache_operation(hit=True)
        else:
            self.monitor.record_cache_operation(hit=False)
        return value

    async def cache_set(self, key: str, value: Any, ttl: int = 300, priority: str = "normal") -> bool:
        """Set value in cache with priority-based TTL"""
        if not self.cache:
            return False
        return await self.cache.set_with_priority(key, value, ttl, priority)

    async def cache_get_or_compute(
        self, key: str, compute_func: Callable, ttl: int = 300, priority: str = "normal"
    ) -> Any:
        """
        Get from cache or compute and cache the result

        This is the recommended way to cache expensive operations.
        """
        if not self.cache:
            if asyncio.iscoroutinefunction(compute_func):
                return await compute_func()
            return compute_func()

        return await self.cache.get_or_compute(key, compute_func, ttl, priority)

    async def cache_invalidate(self, key: str) -> bool:
        """Invalidate a cache key"""
        if not self.cache:
            return False
        return await self.cache.delete(key)

    async def cache_warm(self, items: Dict[str, tuple]) -> Dict[str, bool]:
        """
        Warm cache with multiple items

        Args:
            items: Dict mapping key -> (value, ttl, priority)

        Returns:
            Dict mapping key -> success status
        """
        if not self.cache:
            return {}

        results = {}
        for key, (value, ttl, priority) in items.items():
            results[key] = await self.cache.set_with_priority(key, value, ttl, priority)
        return results

    # ========================================================================
    # AI REQUEST METHODS
    # ========================================================================

    async def ai_query(
        self,
        prompt: str,
        priority: RequestPriority = RequestPriority.NORMAL,
        max_tokens: int = 1024,
        skip_cache: bool = False,
    ) -> str:
        """
        Submit AI query with automatic batching and caching

        Args:
            prompt: The prompt to send to Claude
            priority: Request priority (CRITICAL, HIGH, NORMAL, LOW, BATCH)
            max_tokens: Maximum tokens in response
            skip_cache: Skip response cache

        Returns:
            AI response content string
        """
        if not self.ai_batcher:
            raise RuntimeError("AI batcher not initialized")

        response = await self.ai_batcher.submit(
            prompt=prompt,
            priority=priority,
            max_tokens=max_tokens,
            skip_cache=skip_cache,
        )

        # Record AI request latency
        self.monitor.record_ai_request(response.latency_ms)

        return response.content

    async def cached_ai_query(self, prompt: str, context_id: str, ttl: int = 3600) -> str:
        """
        AI query with additional L1/L2 caching by context

        Useful when the same query might be made multiple times
        for the same lead/property/context.
        """
        cache_key = f"ai_response:{context_id}:{hash(prompt) % 100000}"

        # Check L1/L2 cache first
        cached = await self.cache_get(cache_key)
        if cached:
            return cached

        # Execute AI query
        response = await self.ai_query(prompt, priority=RequestPriority.NORMAL)

        # Cache the response
        await self.cache_set(cache_key, response, ttl=ttl, priority="high")

        return response

    # ========================================================================
    # MONITORING METHODS
    # ========================================================================

    def record_api_latency(self, latency_ms: float, endpoint: str = "", success: bool = True):
        """Record API endpoint latency"""
        if self.monitor:
            self.monitor.record_api_latency(latency_ms, endpoint, success)

    def record_db_query(self, latency_ms: float, query_type: str = ""):
        """Record database query latency"""
        if self.monitor:
            self.monitor.record_db_query(latency_ms, query_type)

    def record_user_activity(self, user_id: str, active: bool = True):
        """Record user activity for capacity tracking"""
        if self.monitor:
            self.monitor.record_user_activity(user_id, active)

    async def get_status(self) -> PerformanceStatus:
        """Get current performance status"""
        if not self.monitor:
            return PerformanceStatus(
                status="unknown",
                cache_hit_rate=0.0,
                api_p95_ms=0.0,
                db_p95_ms=0.0,
                concurrent_users=0,
                active_alerts=0,
                timestamp=datetime.now(),
            )

        health = self.monitor.get_health_report()
        metrics = health["metrics"]

        return PerformanceStatus(
            status=health["status"],
            cache_hit_rate=metrics["cache"]["hit_rate"],
            api_p95_ms=metrics["api"]["p95_ms"],
            db_p95_ms=metrics["database"]["p95_ms"],
            concurrent_users=metrics["capacity"]["concurrent_users"],
            active_alerts=health["active_alerts"],
            timestamp=datetime.now(),
        )

    async def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report"""
        if not self.monitor:
            return {"status": "unknown", "error": "Monitor not initialized"}

        report = self.monitor.get_health_report()

        # Add cache metrics
        if self.cache:
            report["cache"] = self.cache.get_performance_stats()

        # Add AI batcher metrics
        if self.ai_batcher:
            report["ai_batcher"] = self.ai_batcher.get_metrics()

        # Add uptime
        if self._startup_time:
            uptime = datetime.now() - self._startup_time
            report["uptime_seconds"] = uptime.total_seconds()

        return report

    def check_thresholds(self) -> List[Any]:
        """Check performance thresholds and return any alerts"""
        if not self.monitor:
            return []
        return self.monitor.check_thresholds()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_perf_integration: Optional[PerformanceIntegration] = None


def get_performance_integration() -> PerformanceIntegration:
    """Get singleton performance integration instance"""
    global _perf_integration
    if _perf_integration is None:
        _perf_integration = PerformanceIntegration()
    return _perf_integration


async def initialize_performance_services(anthropic_client=None) -> bool:
    """Initialize all performance services (call at application startup)"""
    integration = get_performance_integration()
    return await integration.initialize(anthropic_client)


async def shutdown_performance_services():
    """Shutdown all performance services (call at application shutdown)"""
    integration = get_performance_integration()
    await integration.shutdown()


# ============================================================================
# DECORATORS FOR EASY SERVICE INTEGRATION
# ============================================================================


def optimized_endpoint(endpoint_name: str = ""):
    """
    Decorator for optimizing API endpoints with caching and monitoring

    Usage:
        @optimized_endpoint("get_lead")
        async def get_lead(lead_id: str):
            # Your endpoint logic
            pass
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            integration = get_performance_integration()
            start_time = asyncio.get_event_loop().time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                integration.record_api_latency(latency_ms, endpoint_name, success)

        return wrapper

    return decorator


def cached_operation(cache_key_prefix: str, ttl: int = 300, priority: str = "normal"):
    """
    Decorator for caching operation results

    Usage:
        @cached_operation("lead_score", ttl=600, priority="high")
        async def calculate_lead_score(lead_id: str):
            # Expensive computation
            return score
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            integration = get_performance_integration()

            # Generate cache key
            key_parts = [cache_key_prefix, func.__name__]
            if args:
                key_parts.extend(str(a) for a in args)
            cache_key = ":".join(key_parts)

            # Try cache first
            cached = await integration.cache_get(cache_key)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(*args, **kwargs)
            await integration.cache_set(cache_key, result, ttl, priority)

            return result

        return wrapper

    return decorator


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":

    async def demo_performance_integration():
        """Demonstrate performance integration usage"""

        print("=" * 60)
        print("Performance Integration Demo")
        print("=" * 60)

        # Initialize
        print("\n1. Initializing performance services...")
        success = await initialize_performance_services()
        print(f"   Initialization: {'SUCCESS' if success else 'FAILED'}")

        integration = get_performance_integration()

        # Test caching
        print("\n2. Testing cache operations...")
        await integration.cache_set("demo_key", {"value": "test"}, ttl=60, priority="high")
        result = await integration.cache_get("demo_key")
        print(f"   Cache get: {result}")

        # Test get_or_compute
        print("\n3. Testing cache get_or_compute...")

        async def expensive_operation():
            await asyncio.sleep(0.1)  # Simulate work
            return {"computed": "value"}

        result = await integration.cache_get_or_compute("computed_key", expensive_operation, ttl=300, priority="normal")
        print(f"   First call (computed): {result}")

        result = await integration.cache_get_or_compute("computed_key", expensive_operation, ttl=300, priority="normal")
        print(f"   Second call (cached): {result}")

        # Test monitoring
        print("\n4. Testing performance monitoring...")
        for i in range(10):
            integration.record_api_latency(50 + i * 5, "demo_endpoint")
            integration.record_db_query(20 + i * 2, "SELECT")

        # Get status
        print("\n5. Getting performance status...")
        status = await integration.get_status()
        print(f"   Status: {status.status}")
        print(f"   Cache Hit Rate: {status.cache_hit_rate:.1%}")
        print(f"   API P95: {status.api_p95_ms:.1f}ms")

        # Get health report
        print("\n6. Getting health report...")
        report = await integration.get_health_report()
        print(f"   Health Status: {report['status']}")
        if report.get("issues"):
            print(f"   Issues: {report['issues']}")

        # Shutdown
        print("\n7. Shutting down...")
        await shutdown_performance_services()
        print("   Shutdown complete")

        print("\n" + "=" * 60)
        print("Demo completed!")

    asyncio.run(demo_performance_integration())
