"""
Performance Optimization for DI Container

Provides performance monitoring, optimization strategies, and caching
mechanisms for the dependency injection container.
"""

import asyncio
import logging
import threading
import time
import weakref
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class PerformanceMetrics:
    """Performance metrics for service resolution"""

    service_name: str
    total_resolutions: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float("inf")
    max_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    recent_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_accessed: Optional[datetime] = None
    error_count: int = 0

    def update(self, resolution_time_ms: float, was_cached: bool = False, error: bool = False):
        """Update metrics with new resolution"""
        if error:
            self.error_count += 1
            return

        self.total_resolutions += 1
        self.total_time_ms += resolution_time_ms
        self.min_time_ms = min(self.min_time_ms, resolution_time_ms)
        self.max_time_ms = max(self.max_time_ms, resolution_time_ms)
        self.avg_time_ms = self.total_time_ms / self.total_resolutions
        self.recent_times.append(resolution_time_ms)
        self.last_accessed = datetime.utcnow()

        if was_cached:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0

    @property
    def recent_avg_time_ms(self) -> float:
        """Calculate average time for recent resolutions"""
        return sum(self.recent_times) / len(self.recent_times) if self.recent_times else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "service_name": self.service_name,
            "total_resolutions": self.total_resolutions,
            "avg_time_ms": self.avg_time_ms,
            "min_time_ms": self.min_time_ms if self.min_time_ms != float("inf") else 0.0,
            "max_time_ms": self.max_time_ms,
            "recent_avg_time_ms": self.recent_avg_time_ms,
            "cache_hit_rate": self.cache_hit_rate,
            "error_count": self.error_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }


class PerformanceMonitor:
    """Performance monitoring for DI container operations"""

    def __init__(self, enabled: bool = True, max_history: int = 1000):
        self.enabled = enabled
        self.max_history = max_history
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.global_metrics = {"total_resolutions": 0, "total_time_ms": 0.0, "start_time": datetime.utcnow()}
        self._lock = threading.Lock()

    def record_resolution(
        self, service_name: str, resolution_time_ms: float, was_cached: bool = False, error: bool = False
    ):
        """Record service resolution metrics"""
        if not self.enabled:
            return

        with self._lock:
            if service_name not in self.metrics:
                self.metrics[service_name] = PerformanceMetrics(service_name)

            self.metrics[service_name].update(resolution_time_ms, was_cached, error)

            if not error:
                self.global_metrics["total_resolutions"] += 1
                self.global_metrics["total_time_ms"] += resolution_time_ms

    def get_metrics(self, service_name: str = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if not self.enabled:
            return {"monitoring_disabled": True}

        with self._lock:
            if service_name:
                return self.metrics.get(service_name, PerformanceMetrics(service_name)).to_dict()

            # Return all metrics
            result = {
                "global": {
                    **self.global_metrics,
                    "avg_resolution_time_ms": (
                        self.global_metrics["total_time_ms"] / self.global_metrics["total_resolutions"]
                        if self.global_metrics["total_resolutions"] > 0
                        else 0.0
                    ),
                    "uptime_seconds": (datetime.utcnow() - self.global_metrics["start_time"]).total_seconds(),
                },
                "services": {name: metrics.to_dict() for name, metrics in self.metrics.items()},
                "summary": {
                    "total_services": len(self.metrics),
                    "avg_cache_hit_rate": sum(m.cache_hit_rate for m in self.metrics.values()) / len(self.metrics)
                    if self.metrics
                    else 0.0,
                    "slowest_service": max(self.metrics.values(), key=lambda m: m.avg_time_ms).service_name
                    if self.metrics
                    else None,
                    "most_used_service": max(self.metrics.values(), key=lambda m: m.total_resolutions).service_name
                    if self.metrics
                    else None,
                },
            }

            return result

    def get_slow_services(self, threshold_ms: float = 100.0) -> List[str]:
        """Get services that are slower than threshold"""
        with self._lock:
            return [name for name, metrics in self.metrics.items() if metrics.avg_time_ms > threshold_ms]

    def get_frequently_used_services(self, min_usage: int = 100) -> List[str]:
        """Get services used more than minimum threshold"""
        with self._lock:
            return [name for name, metrics in self.metrics.items() if metrics.total_resolutions >= min_usage]

    def reset_metrics(self):
        """Reset all performance metrics"""
        with self._lock:
            self.metrics.clear()
            self.global_metrics = {"total_resolutions": 0, "total_time_ms": 0.0, "start_time": datetime.utcnow()}


class ServiceCache:
    """Advanced caching for service instances"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get cached service instance"""
        with self._lock:
            if key not in self._cache:
                return None

            cache_entry = self._cache[key]
            now = time.time()

            # Check TTL
            if cache_entry["expires_at"] < now:
                del self._cache[key]
                del self._access_times[key]
                return None

            # Update access time
            self._access_times[key] = now
            return cache_entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Cache service instance"""
        with self._lock:
            # Evict if cache is full
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            ttl = ttl or self.default_ttl
            now = time.time()

            self._cache[key] = {"value": value, "created_at": now, "expires_at": now + ttl}
            self._access_times[key] = now

    def delete(self, key: str) -> bool:
        """Delete cached service instance"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._access_times[key]
                return True
            return False

    def clear(self) -> None:
        """Clear all cached instances"""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()

    def _evict_lru(self) -> None:
        """Evict least recently used item"""
        if not self._access_times:
            return

        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        del self._cache[lru_key]
        del self._access_times[lru_key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            now = time.time()
            expired_count = sum(1 for entry in self._cache.values() if entry["expires_at"] < now)

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "expired_entries": expired_count,
                "utilization": len(self._cache) / self.max_size,
            }


class OptimizedDIContainer:
    """
    Performance-optimized version of DIContainer with advanced caching
    and monitoring capabilities.
    """

    def __init__(self, base_container, enable_caching: bool = True, enable_monitoring: bool = True):
        self.base_container = base_container
        self.enable_caching = enable_caching
        self.enable_monitoring = enable_monitoring

        self.performance_monitor = PerformanceMonitor(enable_monitoring)
        self.service_cache = ServiceCache() if enable_caching else None

        # Optimization settings
        self._fast_path_services: set = set()  # Services that can use fast resolution path
        self._dependency_graph: Dict[str, List[str]] = {}  # Cached dependency graph
        self._warm_services: set = set()  # Services to warm up on startup

    def register_fast_path_service(self, service_name: str):
        """Register service for fast-path resolution"""
        self._fast_path_services.add(service_name)

    def register_warm_service(self, service_name: str):
        """Register service for warm-up on container start"""
        self._warm_services.add(service_name)

    async def warm_up_services(self):
        """Warm up frequently used services"""
        logger.info("Warming up services...")

        warm_up_tasks = []
        for service_name in self._warm_services:
            task = asyncio.create_task(self._warm_up_service(service_name))
            warm_up_tasks.append(task)

        if warm_up_tasks:
            await asyncio.gather(*warm_up_tasks, return_exceptions=True)

        logger.info(f"Warmed up {len(self._warm_services)} services")

    async def _warm_up_service(self, service_name: str):
        """Warm up individual service"""
        try:
            # Find service metadata
            if service_name in self.base_container._services:
                metadata = self.base_container._services[service_name]
                # Pre-resolve service
                await self.base_container.get_service_async(metadata.service_type, service_name)
                logger.debug(f"Warmed up service: {service_name}")
        except Exception as e:
            logger.warning(f"Failed to warm up service {service_name}: {e}")

    async def get_service_async(self, service_type: type, name: str = None, scope_id: str = None, **kwargs) -> Any:
        """Optimized service resolution with caching and monitoring"""
        service_name = name or self.base_container._get_service_name(service_type)

        start_time = time.perf_counter()
        cached_instance = None
        error = False

        try:
            # Check cache first
            if self.service_cache:
                cache_key = f"{service_name}:{scope_id or 'default'}"
                cached_instance = self.service_cache.get(cache_key)

                if cached_instance:
                    resolution_time_ms = (time.perf_counter() - start_time) * 1000
                    if self.enable_monitoring:
                        self.performance_monitor.record_resolution(service_name, resolution_time_ms, was_cached=True)
                    return cached_instance

            # Use fast path if available
            if service_name in self._fast_path_services:
                instance = await self._fast_path_resolution(service_type, service_name, scope_id, **kwargs)
            else:
                instance = await self.base_container.get_service_async(service_type, name, scope_id, **kwargs)

            # Cache the result if appropriate
            if self.service_cache and scope_id is None:  # Don't cache scoped services
                metadata = self.base_container._services.get(service_name)
                if metadata and metadata.lifetime.value == "singleton":
                    cache_key = f"{service_name}:default"
                    self.service_cache.set(cache_key, instance)

            return instance

        except Exception as e:
            error = True
            raise
        finally:
            # Record metrics
            if self.enable_monitoring:
                resolution_time_ms = (time.perf_counter() - start_time) * 1000
                self.performance_monitor.record_resolution(
                    service_name, resolution_time_ms, was_cached=cached_instance is not None, error=error
                )

    async def _fast_path_resolution(self, service_type: type, service_name: str, scope_id: str = None, **kwargs) -> Any:
        """Fast path resolution for simple services"""
        # This would implement optimized resolution logic for services
        # that don't have complex dependencies
        return await self.base_container.get_service_async(service_type, service_name, scope_id, **kwargs)

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        report = {
            "container_performance": self.performance_monitor.get_metrics(),
            "optimization_settings": {
                "caching_enabled": self.enable_caching,
                "monitoring_enabled": self.enable_monitoring,
                "fast_path_services": list(self._fast_path_services),
                "warm_services": list(self._warm_services),
            },
        }

        if self.service_cache:
            report["cache_stats"] = self.service_cache.get_stats()

        # Performance recommendations
        report["recommendations"] = self._generate_performance_recommendations()

        return report

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        if self.enable_monitoring:
            slow_services = self.performance_monitor.get_slow_services(threshold_ms=50.0)
            if slow_services:
                recommendations.append(f"Consider optimizing slow services: {', '.join(slow_services)}")

            frequent_services = self.performance_monitor.get_frequently_used_services(min_usage=50)
            non_warm_frequent = set(frequent_services) - self._warm_services
            if non_warm_frequent:
                recommendations.append(f"Consider warming up frequently used services: {', '.join(non_warm_frequent)}")

        if self.service_cache:
            stats = self.service_cache.get_stats()
            if stats["utilization"] > 0.8:
                recommendations.append("Consider increasing cache size")

        return recommendations


# Real Estate Domain Performance Optimizations
class RealEstatePerformanceOptimizer:
    """Performance optimization specifically for real estate services"""

    @staticmethod
    def configure_container_for_real_estate(container: OptimizedDIContainer):
        """Configure container with real estate-specific optimizations"""

        # Fast-path services (simple, frequently used)
        fast_path_services = ["PropertyQueryBuilder", "ConfigurationService", "PerformanceMonitor"]

        for service in fast_path_services:
            container.register_fast_path_service(service)

        # Warm-up services (expensive to create, frequently used)
        warm_services = ["PropertyRepository", "PropertyDataService", "ScoringFactory", "MemoryCacheBackend"]

        for service in warm_services:
            container.register_warm_service(service)

    @staticmethod
    def get_performance_configuration() -> Dict[str, Any]:
        """Get recommended performance configuration for real estate services"""
        return {
            "caching": {
                "max_size": 2000,  # Higher cache size for property data
                "default_ttl": 1800,  # 30 minutes for real estate data
                "property_cache_ttl": 3600,  # 1 hour for individual properties
                "search_cache_ttl": 900,  # 15 minutes for search results
            },
            "monitoring": {"enabled": True, "slow_service_threshold_ms": 100.0, "frequent_use_threshold": 25},
            "optimization": {
                "enable_query_optimization": True,
                "enable_result_caching": True,
                "enable_repository_pooling": True,
                "max_concurrent_queries": 10,
            },
        }

    @staticmethod
    async def benchmark_property_operations(container: OptimizedDIContainer, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark common property operations"""
        from ..repositories.interfaces import PropertyQuery

        results = {}

        # Benchmark property search
        search_times = []
        for _ in range(iterations):
            start = time.perf_counter()

            try:
                repo = await container.get_service_async("IPropertyRepository")
                query = PropertyQuery()
                query.add_price_range(300000, 800000)
                query.pagination.limit = 10

                await repo.find_properties(query)
                end = time.perf_counter()
                search_times.append((end - start) * 1000)
            except Exception:
                pass

        if search_times:
            results["property_search"] = {
                "avg_time_ms": sum(search_times) / len(search_times),
                "min_time_ms": min(search_times),
                "max_time_ms": max(search_times),
                "success_rate": len(search_times) / iterations,
            }

        # Benchmark scoring operations
        scoring_times = []
        for _ in range(iterations):
            start = time.perf_counter()

            try:
                scoring_factory = await container.get_service_async("ScoringFactory")
                scorer = scoring_factory.create_scorer("basic")

                property_data = {"price": 500000, "bedrooms": 3, "bathrooms": 2.5, "location": "Austin"}

                preferences = {"budget": 600000, "bedrooms": 3, "location": "Austin"}

                scorer.score_property(property_data, preferences)
                end = time.perf_counter()
                scoring_times.append((end - start) * 1000)
            except Exception:
                pass

        if scoring_times:
            results["property_scoring"] = {
                "avg_time_ms": sum(scoring_times) / len(scoring_times),
                "min_time_ms": min(scoring_times),
                "max_time_ms": max(scoring_times),
                "success_rate": len(scoring_times) / iterations,
            }

        return results
