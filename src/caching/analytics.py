"""
Cache Analytics Module
======================

Cache hit/miss analytics, performance monitoring, and reporting.

Features:
    - Comprehensive cache metrics collection
    - Hit/miss ratio tracking and analysis
    - Performance trend analysis
    - Cost savings estimation
    - Configurable alerting thresholds
    - Export to multiple formats (JSON, CSV, Prometheus)

Example:
    >>> from src.caching import CacheAnalytics, CacheMetrics
    >>>
    >>> analytics = CacheAnalytics(redis_client=redis)
    >>>
    >>> # Record cache operations
    >>> await analytics.record_hit("query_cache", response_time_ms=5.2)
    >>> await analytics.record_miss("query_cache", computation_time_ms=150.0)
    >>>
    >>> # Get performance report
    >>> report = await analytics.generate_report(timeframe="1h")
    >>> print(f"Hit rate: {report.hit_rate:.2%}")
    >>> print(f"Cost savings: ${report.estimated_cost_savings:.2f}")

Classes:
    CacheAnalytics: Main analytics engine
    CacheMetrics: Data class for cache metrics
    HitMissRatio: Hit/miss ratio calculations
    PerformanceReport: Comprehensive performance report
"""

import asyncio
import csv
import inspect
import io
import json
import logging
import statistics
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

from src.caching.redis_client import BaseRedisClient, RedisClient

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be recorded."""

    HIT = "hit"
    MISS = "miss"
    EVICTION = "eviction"
    EXPIRATION = "expiration"
    ERROR = "error"
    LATENCY = "latency"
    SIZE = "size"


class TimeWindow(Enum):
    """Time windows for metrics aggregation."""

    MINUTE_1 = 60
    MINUTE_5 = 300
    MINUTE_15 = 900
    HOUR_1 = 3600
    HOUR_6 = 21600
    HOUR_24 = 86400


@dataclass
class CacheMetrics:
    """
    Core cache metrics for a specific time period.

    Attributes:
        timestamp: When metrics were recorded
        cache_name: Name of the cache
        hits: Number of cache hits
        misses: Number of cache misses
        evictions: Number of evictions
        expirations: Number of expirations
        total_latency_ms: Total latency in milliseconds
        avg_latency_ms: Average latency
        p50_latency_ms: 50th percentile latency
        p95_latency_ms: 95th percentile latency
        p99_latency_ms: 99th percentile latency
        size_bytes: Cache size in bytes
        entry_count: Number of entries
        errors: Number of errors
    """

    timestamp: datetime = field(default_factory=datetime.now)
    cache_name: str = "default"
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    latencies_ms: List[float] = field(default_factory=list)
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    size_bytes: int = 0
    entry_count: int = 0
    errors: int = 0

    def __post_init__(self):
        """Calculate derived metrics."""
        if self.latencies_ms:
            self.total_latency_ms = sum(self.latencies_ms)
            self.avg_latency_ms = statistics.mean(self.latencies_ms)
            sorted_latencies = sorted(self.latencies_ms)
            self.p50_latency_ms = self._percentile(sorted_latencies, 50)
            self.p95_latency_ms = self._percentile(sorted_latencies, 95)
            self.p99_latency_ms = self._percentile(sorted_latencies, 99)

    @staticmethod
    def _percentile(sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    @property
    def total_requests(self) -> int:
        """Total number of requests."""
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Cache hit rate (0-1)."""
        total = self.total_requests
        return self.hits / total if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Cache miss rate (0-1)."""
        total = self.total_requests
        return self.misses / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cache_name": self.cache_name,
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_latency_ms": self.total_latency_ms,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "size_bytes": self.size_bytes,
            "entry_count": self.entry_count,
            "errors": self.errors,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
        }


@dataclass
class HitMissRatio:
    """
    Detailed hit/miss ratio analysis.

    Attributes:
        hits: Number of hits
        misses: Number of misses
        timeframe: Time period analyzed
    """

    hits: int
    misses: int
    timeframe: str = "1h"

    @property
    def total(self) -> int:
        """Total operations."""
        return self.hits + self.misses

    @property
    def ratio(self) -> float:
        """Hit/miss ratio (hits per miss)."""
        return self.hits / self.misses if self.misses > 0 else float("inf")

    @property
    def hit_rate(self) -> float:
        """Hit rate as percentage."""
        return (self.hits / self.total * 100) if self.total > 0 else 0.0

    def __str__(self) -> str:
        return f"Hit/Miss: {self.hits}/{self.misses} ({self.hit_rate:.1f}% hit rate)"


@dataclass
class CostAnalysis:
    """
    Cost analysis for cache operations.

    Attributes:
        hits: Number of cache hits
        misses: Number of cache misses
        cost_per_hit: Cost of cache hit (infrastructure)
        cost_per_miss: Cost of cache miss (computation)
    """

    hits: int
    misses: int
    cost_per_hit: float = 0.0001  # $0.0001 per hit (infrastructure)
    cost_per_miss: float = 0.01  # $0.01 per miss (API call)

    @property
    def total_hits_cost(self) -> float:
        """Total cost of hits."""
        return self.hits * self.cost_per_hit

    @property
    def total_misses_cost(self) -> float:
        """Total cost of misses."""
        return self.misses * self.cost_per_miss

    @property
    def total_cost(self) -> float:
        """Total cost."""
        return self.total_hits_cost + self.total_misses_cost

    @property
    def cost_without_cache(self) -> float:
        """What cost would be without any caching."""
        return (self.hits + self.misses) * self.cost_per_miss

    @property
    def cost_savings(self) -> float:
        """Cost savings from caching."""
        return self.cost_without_cache - self.total_cost

    @property
    def savings_percentage(self) -> float:
        """Savings as percentage."""
        if self.cost_without_cache > 0:
            return (self.cost_savings / self.cost_without_cache) * 100
        return 0.0


@dataclass
class PerformanceReport:
    """
    Comprehensive cache performance report.

    Attributes:
        generated_at: When report was generated
        timeframe: Time period covered
        cache_names: List of caches analyzed
        metrics: Aggregated metrics
        hit_miss_ratio: Hit/miss analysis
        cost_analysis: Cost analysis
        recommendations: List of recommendations
    """

    generated_at: datetime = field(default_factory=datetime.now)
    timeframe: str = "1h"
    cache_names: List[str] = field(default_factory=list)
    metrics: Dict[str, CacheMetrics] = field(default_factory=dict)
    hit_miss_ratio: Optional[HitMissRatio] = None
    cost_analysis: Optional[CostAnalysis] = None
    recommendations: List[str] = field(default_factory=list)
    trends: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "timeframe": self.timeframe,
            "cache_names": self.cache_names,
            "metrics": {k: v.to_dict() for k, v in self.metrics.items()},
            "hit_miss_ratio": asdict(self.hit_miss_ratio) if self.hit_miss_ratio else None,
            "cost_analysis": asdict(self.cost_analysis) if self.cost_analysis else None,
            "recommendations": self.recommendations,
            "trends": self.trends,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_csv(self) -> str:
        """Export metrics as CSV."""
        output = io.StringIO()
        if self.metrics:
            fieldnames = ["cache_name", "hits", "misses", "hit_rate", "avg_latency_ms", "p95_latency_ms", "entry_count"]
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for name, metrics in self.metrics.items():
                writer.writerow(
                    {
                        "cache_name": name,
                        "hits": metrics.hits,
                        "misses": metrics.misses,
                        "hit_rate": f"{metrics.hit_rate:.2%}",
                        "avg_latency_ms": f"{metrics.avg_latency_ms:.2f}",
                        "p95_latency_ms": f"{metrics.p95_latency_ms:.2f}",
                        "entry_count": metrics.entry_count,
                    }
                )
        return output.getvalue()

    def to_prometheus_metrics(self) -> str:
        """Export as Prometheus metrics format."""
        lines = []
        for name, metrics in self.metrics.items():
            prefix = f"cache_{name}"
            lines.append(f"# HELP {prefix}_hits Total cache hits")
            lines.append(f"# TYPE {prefix}_hits counter")
            lines.append(f'{prefix}_hits{{cache="{name}"}} {metrics.hits}')

            lines.append(f"# HELP {prefix}_misses Total cache misses")
            lines.append(f"# TYPE {prefix}_misses counter")
            lines.append(f'{prefix}_misses{{cache="{name}"}} {metrics.misses}')

            lines.append(f"# HELP {prefix}_hit_rate Cache hit rate")
            lines.append(f"# TYPE {prefix}_hit_rate gauge")
            lines.append(f'{prefix}_hit_rate{{cache="{name}"}} {metrics.hit_rate}')

            lines.append(f"# HELP {prefix}_latency_ms Average latency in ms")
            lines.append(f"# TYPE {prefix}_latency_ms gauge")
            lines.append(f'{prefix}_latency_ms{{cache="{name}"}} {metrics.avg_latency_ms}')

        return "\n".join(lines)


class MetricsExporter(ABC):
    """Abstract base class for metrics exporters."""

    @abstractmethod
    async def export(self, report: PerformanceReport) -> bool:
        """Export a performance report."""
        pass


class JSONMetricsExporter(MetricsExporter):
    """Export metrics to JSON file."""

    def __init__(self, filepath: str):
        self.filepath = filepath

    async def export(self, report: PerformanceReport) -> bool:
        """Export to JSON file."""
        try:
            with open(self.filepath, "w") as f:
                f.write(report.to_json())
            return True
        except Exception as e:
            logger.error(f"Failed to export metrics to {self.filepath}: {e}")
            return False


class PrometheusMetricsExporter(MetricsExporter):
    """Export metrics in Prometheus format."""

    def __init__(self, filepath: str = "/tmp/cache_metrics.prom"):
        self.filepath = filepath

    async def export(self, report: PerformanceReport) -> bool:
        """Export to Prometheus metrics file."""
        try:
            with open(self.filepath, "w") as f:
                f.write(report.to_prometheus_metrics())
            return True
        except Exception as e:
            logger.error(f"Failed to export Prometheus metrics: {e}")
            return False


class CacheAnalytics:
    """
    Analytics engine for cache performance monitoring.

    Features:
        - Real-time metrics collection
        - Configurable retention windows
        - Automatic aggregation
        - Cost analysis
        - Trend detection
        - Alerting thresholds

    Args:
        redis_client: Redis client for persistence
        retention_minutes: How long to keep raw metrics
        aggregation_windows: List of aggregation windows
        enable_persistence: Whether to persist metrics
    """

    def __init__(
        self,
        redis_client: Optional[BaseRedisClient] = None,
        retention_minutes: int = 60,
        aggregation_windows: Optional[List[TimeWindow]] = None,
        enable_persistence: bool = True,
        key_prefix: str = "analytics",
    ):
        self.redis = redis_client
        self.retention_minutes = retention_minutes
        self.aggregation_windows = aggregation_windows or [
            TimeWindow.MINUTE_1,
            TimeWindow.MINUTE_15,
            TimeWindow.HOUR_1,
        ]
        self.enable_persistence = enable_persistence and redis_client is not None
        self.key_prefix = key_prefix

        # In-memory metrics storage
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._aggregated_metrics: Dict[str, Dict[TimeWindow, List[CacheMetrics]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Cost configuration
        self.cost_per_hit = 0.0001
        self.cost_per_miss = 0.01

        # Alerting thresholds
        self.alert_thresholds = {
            "hit_rate_min": 0.5,
            "latency_max_ms": 100,
            "error_rate_max": 0.01,
        }

        # Callbacks for alerts
        self._alert_callbacks: List[Callable[[str, Any], None]] = []

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def record_hit(self, cache_name: str, response_time_ms: float = 0.0, size_bytes: int = 0) -> None:
        """Record a cache hit."""
        await self._record_event(cache_name, MetricType.HIT, response_time_ms, size_bytes)

    async def record_miss(self, cache_name: str, computation_time_ms: float = 0.0) -> None:
        """Record a cache miss."""
        await self._record_event(cache_name, MetricType.MISS, computation_time_ms, 0)

    async def record_eviction(self, cache_name: str, size_bytes: int = 0) -> None:
        """Record a cache eviction."""
        await self._record_event(cache_name, MetricType.EVICTION, 0, size_bytes)

    async def record_error(self, cache_name: str, error: Exception) -> None:
        """Record a cache error."""
        await self._record_event(cache_name, MetricType.ERROR, 0, 0, error=str(error))

    async def record_latency(self, cache_name: str, latency_ms: float) -> None:
        """Record operation latency."""
        await self._record_event(cache_name, MetricType.LATENCY, latency_ms, 0)

    async def _record_event(
        self, cache_name: str, metric_type: MetricType, latency_ms: float, size_bytes: int, error: Optional[str] = None
    ) -> None:
        """Record a metric event."""
        timestamp = datetime.now()

        event = {
            "timestamp": timestamp,
            "type": metric_type.value,
            "cache_name": cache_name,
            "latency_ms": latency_ms,
            "size_bytes": size_bytes,
            "error": error,
        }

        async with self._lock:
            # Store in memory
            self._metrics[cache_name].append(event)

            # Persist if enabled
            if self.enable_persistence:
                await self._persist_event(cache_name, event)

            # Check alert thresholds
            await self._check_thresholds(cache_name, metric_type)

    async def _persist_event(self, cache_name: str, event: Dict[str, Any]) -> None:
        """Persist event to Redis."""
        if not self.redis:
            return

        try:
            key = f"{self.key_prefix}:{cache_name}:events"
            # Use Redis list with expiration
            await self.redis.redis.lpush(key, json.dumps(event, default=str))
            await self.redis.redis.expire(key, self.retention_minutes * 60)
        except Exception as e:
            logger.error(f"Failed to persist event: {e}")

    async def _check_thresholds(self, cache_name: str, metric_type: MetricType) -> None:
        """Check if any alert thresholds are breached."""
        # Get recent metrics for this cache
        recent_metrics = await self._get_recent_metrics(cache_name, minutes=5)

        if metric_type in (MetricType.HIT, MetricType.MISS):
            hit_rate = recent_metrics.hit_rate
            if hit_rate < self.alert_thresholds["hit_rate_min"]:
                await self._trigger_alert(
                    "low_hit_rate",
                    {
                        "cache_name": cache_name,
                        "hit_rate": hit_rate,
                        "threshold": self.alert_thresholds["hit_rate_min"],
                    },
                )

        elif metric_type == MetricType.LATENCY:
            avg_latency = recent_metrics.avg_latency_ms
            if avg_latency > self.alert_thresholds["latency_max_ms"]:
                await self._trigger_alert(
                    "high_latency",
                    {
                        "cache_name": cache_name,
                        "avg_latency_ms": avg_latency,
                        "threshold": self.alert_thresholds["latency_max_ms"],
                    },
                )

        elif metric_type == MetricType.ERROR:
            total = recent_metrics.hits + recent_metrics.misses + recent_metrics.errors
            error_rate = recent_metrics.errors / total if total > 0 else 0
            if error_rate > self.alert_thresholds["error_rate_max"]:
                await self._trigger_alert(
                    "high_error_rate",
                    {
                        "cache_name": cache_name,
                        "error_rate": error_rate,
                        "threshold": self.alert_thresholds["error_rate_max"],
                    },
                )

    async def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                if inspect.iscoroutinefunction(callback):
                    await callback(alert_type, data)
                else:
                    callback(alert_type, data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def register_alert_callback(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for alerts."""
        self._alert_callbacks.append(callback)

    async def get_metrics(
        self, cache_name: Optional[str] = None, timeframe: str = "1h"
    ) -> Union[CacheMetrics, Dict[str, CacheMetrics]]:
        """
        Get metrics for a specific cache or all caches.

        Args:
            cache_name: Specific cache name (None for all)
            timeframe: Time period (e.g., "1h", "24h", "7d")

        Returns:
            CacheMetrics or dict of cache_name -> CacheMetrics
        """
        minutes = self._parse_timeframe(timeframe)

        if cache_name:
            return await self._get_recent_metrics(cache_name, minutes)
        else:
            result = {}
            for name in self._metrics.keys():
                result[name] = await self._get_recent_metrics(name, minutes)
            return result

    async def _get_recent_metrics(self, cache_name: str, minutes: int) -> CacheMetrics:
        """Get metrics for a cache over recent time period."""
        cutoff = datetime.now() - timedelta(minutes=minutes)

        events = [e for e in self._metrics[cache_name] if e["timestamp"] > cutoff]

        hits = sum(1 for e in events if e["type"] == MetricType.HIT.value)
        misses = sum(1 for e in events if e["type"] == MetricType.MISS.value)
        evictions = sum(1 for e in events if e["type"] == MetricType.EVICTION.value)
        errors = sum(1 for e in events if e["type"] == MetricType.ERROR.value)

        latencies = [e["latency_ms"] for e in events if e["latency_ms"] > 0]

        return CacheMetrics(
            timestamp=datetime.now(),
            cache_name=cache_name,
            hits=hits,
            misses=misses,
            evictions=evictions,
            errors=errors,
            latencies_ms=latencies,
        )

    async def get_hit_miss_ratio(self, cache_name: str, timeframe: str = "1h") -> HitMissRatio:
        """Get hit/miss ratio for a cache."""
        metrics = await self.get_metrics(cache_name, timeframe)
        return HitMissRatio(hits=metrics.hits, misses=metrics.misses, timeframe=timeframe)

    async def get_cost_analysis(self, cache_name: str, timeframe: str = "1h") -> CostAnalysis:
        """Get cost analysis for a cache."""
        metrics = await self.get_metrics(cache_name, timeframe)
        return CostAnalysis(
            hits=metrics.hits, misses=metrics.misses, cost_per_hit=self.cost_per_hit, cost_per_miss=self.cost_per_miss
        )

    async def generate_report(
        self, cache_names: Optional[List[str]] = None, timeframe: str = "1h"
    ) -> PerformanceReport:
        """
        Generate comprehensive performance report.

        Args:
            cache_names: List of cache names (None for all)
            timeframe: Time period for analysis

        Returns:
            PerformanceReport with metrics and recommendations
        """
        if cache_names is None:
            cache_names = list(self._metrics.keys())

        # Collect metrics
        metrics = {}
        total_hits = 0
        total_misses = 0

        for name in cache_names:
            cache_metrics = await self.get_metrics(name, timeframe)
            metrics[name] = cache_metrics
            total_hits += cache_metrics.hits
            total_misses += cache_metrics.misses

        # Calculate overall hit/miss ratio
        hit_miss_ratio = HitMissRatio(hits=total_hits, misses=total_misses, timeframe=timeframe)

        # Cost analysis
        cost_analysis = CostAnalysis(
            hits=total_hits, misses=total_misses, cost_per_hit=self.cost_per_hit, cost_per_miss=self.cost_per_miss
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics)

        # Calculate trends
        trends = await self._calculate_trends(cache_names, timeframe)

        return PerformanceReport(
            timeframe=timeframe,
            cache_names=cache_names,
            metrics=metrics,
            hit_miss_ratio=hit_miss_ratio,
            cost_analysis=cost_analysis,
            recommendations=recommendations,
            trends=trends,
        )

    def _generate_recommendations(self, metrics: Dict[str, CacheMetrics]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []

        for name, cache_metrics in metrics.items():
            # Check hit rate
            if cache_metrics.hit_rate < 0.5:
                recommendations.append(
                    f"{name}: Low hit rate ({cache_metrics.hit_rate:.1%}). Consider increasing TTL or cache size."
                )
            elif cache_metrics.hit_rate > 0.95:
                recommendations.append(
                    f"{name}: Very high hit rate ({cache_metrics.hit_rate:.1%}). Cache may be oversized."
                )

            # Check latency
            if cache_metrics.p95_latency_ms > 100:
                recommendations.append(
                    f"{name}: High P95 latency ({cache_metrics.p95_latency_ms:.1f}ms). "
                    "Consider Redis optimization or network improvements."
                )

            # Check eviction rate
            total_ops = cache_metrics.hits + cache_metrics.misses
            if total_ops > 0:
                eviction_rate = cache_metrics.evictions / total_ops
                if eviction_rate > 0.1:
                    recommendations.append(
                        f"{name}: High eviction rate ({eviction_rate:.1%}). Consider increasing cache capacity."
                    )

        return recommendations

    async def _calculate_trends(self, cache_names: List[str], timeframe: str) -> Dict[str, Any]:
        """Calculate performance trends."""
        trends = {}

        # Compare with previous period
        current_minutes = self._parse_timeframe(timeframe)
        previous_minutes = current_minutes * 2

        for name in cache_names:
            current = await self._get_recent_metrics(name, current_minutes)
            previous = await self._get_recent_metrics(name, previous_minutes)

            # Skip if no previous data
            if previous.total_requests == 0:
                continue

            # Calculate trend
            hit_rate_change = current.hit_rate - previous.hit_rate
            latency_change = current.avg_latency_ms - previous.avg_latency_ms

            trends[name] = {
                "hit_rate_change": hit_rate_change,
                "hit_rate_trend": "improving" if hit_rate_change > 0 else "declining",
                "latency_change_ms": latency_change,
                "latency_trend": "improving" if latency_change < 0 else "increasing",
            }

        return trends

    def _parse_timeframe(self, timeframe: str) -> int:
        """Parse timeframe string to minutes."""
        unit = timeframe[-1].lower()
        value = int(timeframe[:-1])

        multipliers = {
            "m": 1,
            "h": 60,
            "d": 60 * 24,
        }

        return value * multipliers.get(unit, 60)

    async def export_report(
        self, report: PerformanceReport, format: str = "json", filepath: Optional[str] = None
    ) -> str:
        """
        Export report to file.

        Args:
            report: PerformanceReport to export
            format: "json", "csv", or "prometheus"
            filepath: Output file path (None for auto-generated)

        Returns:
            Path to exported file
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"/tmp/cache_report_{timestamp}.{format}"

        if format == "json":
            content = report.to_json()
        elif format == "csv":
            content = report.to_csv()
        elif format == "prometheus":
            content = report.to_prometheus_metrics()
        else:
            raise ValueError(f"Unknown format: {format}")

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    async def clear_metrics(self, cache_name: Optional[str] = None) -> None:
        """Clear stored metrics."""
        async with self._lock:
            if cache_name:
                self._metrics[cache_name].clear()
                self._aggregated_metrics[cache_name].clear()
            else:
                self._metrics.clear()
                self._aggregated_metrics.clear()


# Factory function
async def create_cache_analytics(redis_url: Optional[str] = None, **kwargs) -> CacheAnalytics:
    """
    Factory function to create CacheAnalytics instance.

    Args:
        redis_url: Redis URL for persistence
        **kwargs: Additional configuration options

    Returns:
        Configured CacheAnalytics instance
    """
    redis_client = None
    if redis_url:
        redis_client = RedisClient(redis_url)
        await redis_client.connect()

    return CacheAnalytics(redis_client=redis_client, **kwargs)
