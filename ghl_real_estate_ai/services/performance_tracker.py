"""
Enterprise Performance Tracking and Metrics Collection
Provides comprehensive monitoring for Service 6 scalability targets
"""

import asyncio
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Core performance metrics structure"""

    timestamp: datetime = field(default_factory=datetime.now)

    # Response time metrics (target: <30s lead processing)
    avg_response_time_ms: float = 0
    p95_response_time_ms: float = 0
    p99_response_time_ms: float = 0
    max_response_time_ms: float = 0

    # Throughput metrics (target: 100+ leads/hour)
    requests_per_second: float = 0
    leads_processed_per_hour: int = 0
    concurrent_requests: int = 0

    # Resource utilization
    cpu_usage_percent: float = 0
    memory_usage_percent: float = 0
    disk_io_mb_per_sec: float = 0
    network_io_mb_per_sec: float = 0

    # Cache performance
    cache_hit_rate: float = 0
    cache_miss_rate: float = 0
    cache_eviction_rate: float = 0

    # Error tracking
    error_rate: float = 0
    timeout_rate: float = 0
    circuit_breaker_opens: int = 0

    # Business metrics
    hot_lead_percentage: float = 0
    ai_scoring_accuracy: float = 0
    property_match_success_rate: float = 0


@dataclass
class RequestMetrics:
    """Individual request tracking"""

    request_id: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    endpoint: str = ""
    status: str = "pending"  # pending, success, error, timeout
    lead_id: Optional[str] = None
    error_type: Optional[str] = None


class MetricsCollector:
    """
    High-performance metrics collection with minimal overhead
    """

    def __init__(self, collection_interval: float = 1.0, retention_hours: int = 24):
        self.collection_interval = collection_interval
        self.retention_hours = retention_hours

        # Ring buffers for time-series data
        max_samples = int(retention_hours * 3600 / collection_interval)
        self.metrics_history: deque = deque(maxlen=max_samples)
        self.response_times: deque = deque(maxlen=10000)  # Last 10k requests
        self.active_requests: Dict[str, RequestMetrics] = {}

        # Counters and accumulators
        self.total_requests = 0
        self.total_errors = 0
        self.total_timeouts = 0
        self.leads_processed = 0

        # Performance tracking
        self._lock: Optional[asyncio.Lock] = None
        self._collecting = False
        self._collection_task: Optional[asyncio.Task] = None

        # Custom metrics registry
        self.custom_metrics: Dict[str, Any] = {}
        self.metric_callbacks: List[Callable[[], Dict[str, Any]]] = []

    async def start_collection(self):
        """Start automatic metrics collection"""
        if self._collecting:
            return

        self._collecting = True
        self._collection_task = asyncio.create_task(self._collection_loop())
        logger.info("Performance metrics collection started")

    async def stop_collection(self):
        """Stop metrics collection"""
        self._collecting = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance metrics collection stopped")

    async def _collection_loop(self):
        """Main collection loop"""
        while self._collecting:
            try:
                metrics = await self._collect_current_metrics()
                self.metrics_history.append(metrics)

                # Log warnings for performance targets
                await self._check_performance_targets(metrics)

                await asyncio.sleep(self.collection_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)

    async def _collect_current_metrics(self) -> PerformanceMetrics:
        """Collect current system and application metrics"""

        # Calculate response time percentiles
        response_times_ms = list(self.response_times)
        avg_response_time = sum(response_times_ms) / max(len(response_times_ms), 1)

        p95_response_time = 0
        p99_response_time = 0
        max_response_time = 0

        if response_times_ms:
            sorted_times = sorted(response_times_ms)
            p95_idx = int(0.95 * len(sorted_times))
            p99_idx = int(0.99 * len(sorted_times))

            p95_response_time = sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0
            p99_response_time = sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0
            max_response_time = max(sorted_times)

        # Calculate throughput
        current_time = time.time()
        recent_requests = [
            rt
            for rt in response_times_ms
            if current_time - (rt / 1000) < 1.0  # Last second
        ]
        requests_per_second = len(recent_requests)

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Network and disk I/O
        psutil.disk_io_counters()
        psutil.net_io_counters()

        # Calculate rates (simplified for demo)
        disk_io_mb_per_sec = 0  # Would calculate from previous sample
        network_io_mb_per_sec = 0  # Would calculate from previous sample

        # Get cache metrics from cache service
        cache_metrics = await self._get_cache_metrics()

        # Calculate error rates
        total_ops = max(self.total_requests, 1)
        error_rate = self.total_errors / total_ops
        timeout_rate = self.total_timeouts / total_ops

        # Business metrics from custom callbacks
        business_metrics = await self._collect_business_metrics()

        return PerformanceMetrics(
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            max_response_time_ms=max_response_time,
            requests_per_second=requests_per_second,
            leads_processed_per_hour=self._calculate_leads_per_hour(),
            concurrent_requests=len(self.active_requests),
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory_percent,
            disk_io_mb_per_sec=disk_io_mb_per_sec,
            network_io_mb_per_sec=network_io_mb_per_sec,
            cache_hit_rate=cache_metrics.get("hit_rate", 0),
            cache_miss_rate=cache_metrics.get("miss_rate", 0),
            error_rate=error_rate,
            timeout_rate=timeout_rate,
            hot_lead_percentage=business_metrics.get("hot_lead_percentage", 0),
            ai_scoring_accuracy=business_metrics.get("ai_scoring_accuracy", 0),
            property_match_success_rate=business_metrics.get("property_match_success_rate", 0),
        )

    async def _get_cache_metrics(self) -> Dict[str, float]:
        """Get cache performance metrics"""
        try:
            from ghl_real_estate_ai.services.optimized_cache_service import get_optimized_cache_service

            cache_service = get_optimized_cache_service()
            stats = cache_service.get_performance_stats()

            cache_stats = stats.get("cache_stats", {})
            return {
                "hit_rate": cache_stats.get("overall_hit_rate", 0),
                "miss_rate": 1 - cache_stats.get("overall_hit_rate", 0),
            }
        except Exception as e:
            logger.warning(f"Could not get cache metrics: {e}")
            return {"hit_rate": 0, "miss_rate": 1}

    async def _collect_business_metrics(self) -> Dict[str, float]:
        """Collect business-specific metrics"""
        metrics = {}

        for callback in self.metric_callbacks:
            try:
                custom_metrics = await self._run_callback(callback)
                metrics.update(custom_metrics)
            except Exception as e:
                logger.warning(f"Custom metrics callback failed: {e}")

        return metrics

    async def _run_callback(self, callback: Callable) -> Dict[str, Any]:
        """Run metric callback handling both sync and async"""
        if asyncio.iscoroutinefunction(callback):
            return await callback()
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, callback)

    def _calculate_leads_per_hour(self) -> int:
        """Calculate leads processed per hour"""
        current_time = time.time()
        current_time - 3600

        # Count leads processed in last hour (simplified)
        # In production, this would query from database or event stream
        return self.leads_processed

    async def _check_performance_targets(self, metrics: PerformanceMetrics):
        """Check if performance targets are being met"""
        warnings = []

        # Target: <30s response times
        if metrics.p95_response_time_ms > 30000:
            warnings.append(f"P95 response time {metrics.p95_response_time_ms:.0f}ms exceeds 30s target")

        # Target: 100+ leads/hour
        if metrics.leads_processed_per_hour < 100:
            warnings.append(f"Lead processing rate {metrics.leads_processed_per_hour}/hour below 100/hour target")

        # Target: <5% error rate
        if metrics.error_rate > 0.05:
            warnings.append(f"Error rate {metrics.error_rate:.1%} exceeds 5% target")

        # Target: >90% uptime (implied by low error rates)
        if metrics.timeout_rate > 0.01:
            warnings.append(f"Timeout rate {metrics.timeout_rate:.1%} exceeds 1% target")

        for warning in warnings:
            logger.warning(f"Performance target missed: {warning}")

    @asynccontextmanager
    async def track_request(self, request_id: str, endpoint: str = "", lead_id: Optional[str] = None):
        """Context manager to track individual request performance"""
        if self._lock is None:
            self._lock = asyncio.Lock()

        request_metrics = RequestMetrics(
            request_id=request_id, start_time=time.time(), endpoint=endpoint, lead_id=lead_id
        )

        async with self._lock:
            self.active_requests[request_id] = request_metrics
            self.total_requests += 1

        try:
            yield request_metrics
            # Success
            request_metrics.status = "success"

        except asyncio.TimeoutError:
            request_metrics.status = "timeout"
            request_metrics.error_type = "timeout"
            self.total_timeouts += 1
            raise

        except Exception as e:
            request_metrics.status = "error"
            request_metrics.error_type = type(e).__name__
            self.total_errors += 1
            raise

        finally:
            # Record completion
            request_metrics.end_time = time.time()
            request_metrics.duration_ms = (request_metrics.end_time - request_metrics.start_time) * 1000

            # Add to response times for percentile calculation
            if request_metrics.duration_ms is not None:
                self.response_times.append(request_metrics.duration_ms)

            # Track lead processing
            if lead_id:
                self.leads_processed += 1

            async with self._lock:
                self.active_requests.pop(request_id, None)

    def register_metric_callback(self, callback: Callable[[], Dict[str, Any]]):
        """Register callback for custom business metrics"""
        self.metric_callbacks.append(callback)

    def set_custom_metric(self, name: str, value: Any):
        """Set custom metric value"""
        self.custom_metrics[name] = value

    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get latest collected metrics"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_history(self, hours: int = 1) -> List[PerformanceMetrics]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if not self.metrics_history:
            return {"error": "No metrics collected yet"}

        latest = self.metrics_history[-1]
        last_hour = self.get_metrics_history(1)

        # Calculate averages over last hour
        if last_hour:
            avg_response_time = sum(m.avg_response_time_ms for m in last_hour) / len(last_hour)
            avg_throughput = sum(m.requests_per_second for m in last_hour) / len(last_hour)
            avg_cpu = sum(m.cpu_usage_percent for m in last_hour) / len(last_hour)
            avg_memory = sum(m.memory_usage_percent for m in last_hour) / len(last_hour)
        else:
            avg_response_time = latest.avg_response_time_ms
            avg_throughput = latest.requests_per_second
            avg_cpu = latest.cpu_usage_percent
            avg_memory = latest.memory_usage_percent

        # Performance target assessment
        targets_met = {
            "response_time_target": latest.p95_response_time_ms < 30000,
            "throughput_target": latest.leads_processed_per_hour >= 100,
            "uptime_target": latest.error_rate < 0.05,
            "resource_utilization_healthy": avg_cpu < 80 and avg_memory < 80,
        }

        overall_health = "healthy" if all(targets_met.values()) else "degraded"

        return {
            "timestamp": latest.timestamp.isoformat(),
            "overall_health": overall_health,
            "performance_targets": targets_met,
            "current_metrics": asdict(latest),
            "hourly_averages": {
                "avg_response_time_ms": avg_response_time,
                "avg_throughput_rps": avg_throughput,
                "avg_cpu_percent": avg_cpu,
                "avg_memory_percent": avg_memory,
            },
            "active_requests": len(self.active_requests),
            "total_requests": self.total_requests,
            "uptime_stats": {
                "error_rate": latest.error_rate,
                "timeout_rate": latest.timeout_rate,
                "success_rate": 1 - latest.error_rate - latest.timeout_rate,
            },
        }

    def export_prometheus_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        if not self.metrics_history:
            return ""

        latest = self.metrics_history[-1]
        timestamp = int(latest.timestamp.timestamp() * 1000)

        metrics_lines = [
            f"# HELP lead_intelligence_response_time_ms Average response time in milliseconds",
            f"# TYPE lead_intelligence_response_time_ms gauge",
            f"lead_intelligence_response_time_ms {latest.avg_response_time_ms} {timestamp}",
            f"# HELP lead_intelligence_throughput_rps Requests per second",
            f"# TYPE lead_intelligence_throughput_rps gauge",
            f"lead_intelligence_throughput_rps {latest.requests_per_second} {timestamp}",
            f"# HELP lead_intelligence_leads_per_hour Leads processed per hour",
            f"# TYPE lead_intelligence_leads_per_hour gauge",
            f"lead_intelligence_leads_per_hour {latest.leads_processed_per_hour} {timestamp}",
            f"# HELP lead_intelligence_error_rate Error rate percentage",
            f"# TYPE lead_intelligence_error_rate gauge",
            f"lead_intelligence_error_rate {latest.error_rate} {timestamp}",
            f"# HELP lead_intelligence_cache_hit_rate Cache hit rate percentage",
            f"# TYPE lead_intelligence_cache_hit_rate gauge",
            f"lead_intelligence_cache_hit_rate {latest.cache_hit_rate} {timestamp}",
            f"# HELP lead_intelligence_cpu_usage CPU usage percentage",
            f"# TYPE lead_intelligence_cpu_usage gauge",
            f"lead_intelligence_cpu_usage {latest.cpu_usage_percent} {timestamp}",
            f"# HELP lead_intelligence_memory_usage Memory usage percentage",
            f"# TYPE lead_intelligence_memory_usage gauge",
            f"lead_intelligence_memory_usage {latest.memory_usage_percent} {timestamp}",
        ]

        return "\n".join(metrics_lines)


# Global performance tracker instance
_performance_tracker = None


def get_performance_tracker() -> MetricsCollector:
    """Get global performance tracker instance"""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = MetricsCollector()
    return _performance_tracker


# Decorator for automatic request tracking
def track_performance(endpoint: str = ""):
    """Decorator to automatically track function performance"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracker = get_performance_tracker()
            request_id = f"{func.__name__}_{int(time.time() * 1000000)}"

            async with tracker.track_request(request_id, endpoint):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, func, *args, **kwargs)

        return wrapper

    return decorator
