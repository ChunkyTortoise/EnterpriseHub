"""
Performance Monitor Service - Comprehensive System Performance Tracking

Provides real-time monitoring and alerting for:
- API response times (P50, P95, P99)
- Cache hit rates
- Database query performance
- AI service latency
- Concurrent user capacity
- Memory and resource usage

Performance Targets:
- API P95 Response Time: <100ms
- Cache Hit Rate: >90%
- Database Query P95: <50ms
- Concurrent User Capacity: 1000+ users

Author: EnterpriseHub AI Performance Engineering
Version: 1.0.0
Last Updated: 2026-01-18
"""

import asyncio
import time
import logging
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import statistics
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics being tracked"""
    API_LATENCY = "api_latency"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    DB_QUERY = "db_query"
    AI_REQUEST = "ai_request"
    CONCURRENT_USERS = "concurrent_users"
    MEMORY_USAGE = "memory_usage"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


class AlertSeverity(Enum):
    """Severity levels for alerts"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class PerformanceThresholds:
    """Performance thresholds for alerting"""
    # API Performance
    api_p50_ms: float = 50.0
    api_p95_ms: float = 100.0
    api_p99_ms: float = 200.0

    # Cache Performance
    cache_hit_rate_warning: float = 0.80
    cache_hit_rate_critical: float = 0.60

    # Database Performance
    db_p50_ms: float = 20.0
    db_p95_ms: float = 50.0
    db_p99_ms: float = 100.0

    # AI Performance
    ai_p50_ms: float = 500.0
    ai_p95_ms: float = 1000.0
    ai_p99_ms: float = 2000.0

    # Capacity
    max_concurrent_users: int = 1000
    concurrent_users_warning: float = 0.80  # 80% of max

    # Error Rate
    error_rate_warning: float = 0.01  # 1%
    error_rate_critical: float = 0.05  # 5%


@dataclass
class Alert:
    """Performance alert"""
    alert_id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    current_value: float
    threshold_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "metric_type": self.metric_type.value,
            "message": self.message,
            "current_value": self.current_value,
            "threshold_value": self.threshold_value,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


@dataclass
class PerformanceSnapshot:
    """Point-in-time performance snapshot"""
    timestamp: datetime

    # API Metrics
    api_p50_ms: float = 0.0
    api_p95_ms: float = 0.0
    api_p99_ms: float = 0.0
    api_request_count: int = 0
    api_error_count: int = 0

    # Cache Metrics
    cache_hit_rate: float = 0.0
    cache_total_requests: int = 0

    # Database Metrics
    db_p50_ms: float = 0.0
    db_p95_ms: float = 0.0
    db_p99_ms: float = 0.0
    db_query_count: int = 0

    # AI Metrics
    ai_p50_ms: float = 0.0
    ai_p95_ms: float = 0.0
    ai_p99_ms: float = 0.0
    ai_request_count: int = 0

    # Capacity Metrics
    concurrent_users: int = 0
    peak_concurrent_users: int = 0

    # Resource Metrics
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "api": {
                "p50_ms": round(self.api_p50_ms, 2),
                "p95_ms": round(self.api_p95_ms, 2),
                "p99_ms": round(self.api_p99_ms, 2),
                "request_count": self.api_request_count,
                "error_count": self.api_error_count,
                "error_rate": round(self.api_error_count / max(self.api_request_count, 1), 4),
            },
            "cache": {
                "hit_rate": round(self.cache_hit_rate, 4),
                "total_requests": self.cache_total_requests,
            },
            "database": {
                "p50_ms": round(self.db_p50_ms, 2),
                "p95_ms": round(self.db_p95_ms, 2),
                "p99_ms": round(self.db_p99_ms, 2),
                "query_count": self.db_query_count,
            },
            "ai": {
                "p50_ms": round(self.ai_p50_ms, 2),
                "p95_ms": round(self.ai_p95_ms, 2),
                "p99_ms": round(self.ai_p99_ms, 2),
                "request_count": self.ai_request_count,
            },
            "capacity": {
                "concurrent_users": self.concurrent_users,
                "peak_concurrent_users": self.peak_concurrent_users,
            },
            "resources": {
                "memory_usage_mb": round(self.memory_usage_mb, 2),
                "cpu_usage_percent": round(self.cpu_usage_percent, 2),
            },
        }


class MetricCollector:
    """Collects and stores time-series metric data"""

    def __init__(self, window_size: int = 1000, retention_minutes: int = 60):
        self.window_size = window_size
        self.retention_seconds = retention_minutes * 60

        # Metric storage - uses deque for efficient rolling window
        self._metrics: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=window_size)
            for metric_type in MetricType
        }

        # Lock for thread safety
        self._lock = threading.RLock()

        # Counter metrics
        self._counters: Dict[str, int] = defaultdict(int)

    def record(self, metric_type: MetricType, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        with self._lock:
            timestamp = time.time()
            self._metrics[metric_type].append((timestamp, value, tags or {}))

    def record_count(self, counter_name: str, increment: int = 1):
        """Record a counter increment"""
        with self._lock:
            self._counters[counter_name] += increment

    def get_count(self, counter_name: str) -> int:
        """Get counter value"""
        with self._lock:
            return self._counters.get(counter_name, 0)

    def reset_count(self, counter_name: str):
        """Reset a counter"""
        with self._lock:
            self._counters[counter_name] = 0

    def get_values(self, metric_type: MetricType, since_seconds: Optional[int] = None) -> List[float]:
        """Get metric values, optionally filtered by time"""
        with self._lock:
            metrics = self._metrics[metric_type]
            if not metrics:
                return []

            if since_seconds is None:
                return [m[1] for m in metrics]

            cutoff = time.time() - since_seconds
            return [m[1] for m in metrics if m[0] >= cutoff]

    def get_percentile(self, metric_type: MetricType, percentile: float, since_seconds: Optional[int] = None) -> float:
        """Calculate percentile for a metric"""
        values = self.get_values(metric_type, since_seconds)
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    def get_statistics(self, metric_type: MetricType, since_seconds: Optional[int] = None) -> Dict[str, float]:
        """Get comprehensive statistics for a metric"""
        values = self.get_values(metric_type, since_seconds)
        if not values:
            return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0, "stddev": 0}

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stddev": statistics.stdev(values) if len(values) > 1 else 0,
            "p50": self.get_percentile(metric_type, 50, since_seconds),
            "p95": self.get_percentile(metric_type, 95, since_seconds),
            "p99": self.get_percentile(metric_type, 99, since_seconds),
        }

    def clear(self, metric_type: Optional[MetricType] = None):
        """Clear metrics"""
        with self._lock:
            if metric_type:
                self._metrics[metric_type].clear()
            else:
                for deq in self._metrics.values():
                    deq.clear()
                self._counters.clear()


class PerformanceMonitor:
    """
    Central Performance Monitoring Service

    Features:
    - Real-time metric collection
    - Percentile calculations (P50, P95, P99)
    - Automatic alerting on threshold violations
    - Historical snapshots for trend analysis
    - Integration with cache, database, and AI services
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, thresholds: Optional[PerformanceThresholds] = None):
        if self._initialized:
            return

        self.thresholds = thresholds or PerformanceThresholds()
        self.collector = MetricCollector()

        # Alert tracking
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._alert_lock = threading.RLock()

        # Snapshot history
        self._snapshots: deque = deque(maxlen=1440)  # 24 hours of minute snapshots
        self._snapshot_interval_seconds = 60

        # Active user tracking
        self._active_users: Set[str] = set()
        self._peak_users = 0
        self._users_lock = threading.RLock()

        # Background tasks
        self._snapshot_task: Optional[asyncio.Task] = None
        self._alert_check_task: Optional[asyncio.Task] = None
        self._shutdown = False

        self._initialized = True
        logger.info("PerformanceMonitor initialized with thresholds")

    # ========================================================================
    # METRIC RECORDING METHODS
    # ========================================================================

    def record_api_latency(self, latency_ms: float, endpoint: str = "", success: bool = True):
        """Record API endpoint latency"""
        self.collector.record(MetricType.API_LATENCY, latency_ms, {"endpoint": endpoint})
        if success:
            self.collector.record_count("api_requests")
        else:
            self.collector.record_count("api_errors")
            self.collector.record_count("api_requests")

    def record_cache_operation(self, hit: bool):
        """Record cache hit or miss"""
        if hit:
            self.collector.record(MetricType.CACHE_HIT, 1)
            self.collector.record_count("cache_hits")
        else:
            self.collector.record(MetricType.CACHE_MISS, 1)
            self.collector.record_count("cache_misses")

    def record_db_query(self, latency_ms: float, query_type: str = ""):
        """Record database query latency"""
        self.collector.record(MetricType.DB_QUERY, latency_ms, {"query_type": query_type})
        self.collector.record_count("db_queries")

    def record_ai_request(self, latency_ms: float, model: str = ""):
        """Record AI request latency"""
        self.collector.record(MetricType.AI_REQUEST, latency_ms, {"model": model})
        self.collector.record_count("ai_requests")

    def record_user_activity(self, user_id: str, active: bool = True):
        """Record user activity for concurrent user tracking"""
        with self._users_lock:
            if active:
                self._active_users.add(user_id)
                current_count = len(self._active_users)
                if current_count > self._peak_users:
                    self._peak_users = current_count
            else:
                self._active_users.discard(user_id)

            self.collector.record(MetricType.CONCURRENT_USERS, len(self._active_users))

    def record_error(self, error_type: str = ""):
        """Record an error occurrence"""
        self.collector.record(MetricType.ERROR_RATE, 1, {"error_type": error_type})
        self.collector.record_count("errors")

    # ========================================================================
    # METRIC RETRIEVAL METHODS
    # ========================================================================

    def get_api_metrics(self, since_seconds: int = 60) -> Dict[str, Any]:
        """Get API performance metrics"""
        stats = self.collector.get_statistics(MetricType.API_LATENCY, since_seconds)
        requests = self.collector.get_count("api_requests")
        errors = self.collector.get_count("api_errors")

        return {
            "latency": stats,
            "request_count": requests,
            "error_count": errors,
            "error_rate": errors / max(requests, 1),
            "throughput_per_second": requests / max(since_seconds, 1),
        }

    def get_cache_metrics(self, since_seconds: int = 60) -> Dict[str, Any]:
        """Get cache performance metrics"""
        hits = self.collector.get_count("cache_hits")
        misses = self.collector.get_count("cache_misses")
        total = hits + misses

        return {
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate": hits / max(total, 1),
        }

    def get_db_metrics(self, since_seconds: int = 60) -> Dict[str, Any]:
        """Get database performance metrics"""
        stats = self.collector.get_statistics(MetricType.DB_QUERY, since_seconds)
        queries = self.collector.get_count("db_queries")

        return {
            "latency": stats,
            "query_count": queries,
            "queries_per_second": queries / max(since_seconds, 1),
        }

    def get_ai_metrics(self, since_seconds: int = 60) -> Dict[str, Any]:
        """Get AI service performance metrics"""
        stats = self.collector.get_statistics(MetricType.AI_REQUEST, since_seconds)
        requests = self.collector.get_count("ai_requests")

        return {
            "latency": stats,
            "request_count": requests,
        }

    def get_capacity_metrics(self) -> Dict[str, Any]:
        """Get capacity metrics"""
        with self._users_lock:
            current = len(self._active_users)
            peak = self._peak_users

        return {
            "concurrent_users": current,
            "peak_concurrent_users": peak,
            "max_capacity": self.thresholds.max_concurrent_users,
            "utilization": current / self.thresholds.max_concurrent_users,
        }

    def get_current_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        api_metrics = self.get_api_metrics(60)
        cache_metrics = self.get_cache_metrics(60)
        db_metrics = self.get_db_metrics(60)
        ai_metrics = self.get_ai_metrics(60)
        capacity_metrics = self.get_capacity_metrics()

        return PerformanceSnapshot(
            timestamp=datetime.now(),
            api_p50_ms=api_metrics["latency"].get("p50", 0),
            api_p95_ms=api_metrics["latency"].get("p95", 0),
            api_p99_ms=api_metrics["latency"].get("p99", 0),
            api_request_count=api_metrics["request_count"],
            api_error_count=api_metrics["error_count"],
            cache_hit_rate=cache_metrics["hit_rate"],
            cache_total_requests=cache_metrics["total_requests"],
            db_p50_ms=db_metrics["latency"].get("p50", 0),
            db_p95_ms=db_metrics["latency"].get("p95", 0),
            db_p99_ms=db_metrics["latency"].get("p99", 0),
            db_query_count=db_metrics["query_count"],
            ai_p50_ms=ai_metrics["latency"].get("p50", 0),
            ai_p95_ms=ai_metrics["latency"].get("p95", 0),
            ai_p99_ms=ai_metrics["latency"].get("p99", 0),
            ai_request_count=ai_metrics["request_count"],
            concurrent_users=capacity_metrics["concurrent_users"],
            peak_concurrent_users=capacity_metrics["peak_concurrent_users"],
        )

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report with status"""
        snapshot = self.get_current_snapshot()
        snapshot_dict = snapshot.to_dict()

        # Determine overall health status
        status = "healthy"
        issues = []

        # Check API P95
        if snapshot.api_p95_ms > self.thresholds.api_p99_ms:
            status = "critical"
            issues.append(f"API P95 ({snapshot.api_p95_ms:.0f}ms) exceeds critical threshold ({self.thresholds.api_p99_ms}ms)")
        elif snapshot.api_p95_ms > self.thresholds.api_p95_ms:
            status = "warning" if status == "healthy" else status
            issues.append(f"API P95 ({snapshot.api_p95_ms:.0f}ms) exceeds warning threshold ({self.thresholds.api_p95_ms}ms)")

        # Check Cache Hit Rate
        if snapshot.cache_hit_rate < self.thresholds.cache_hit_rate_critical and snapshot.cache_total_requests > 0:
            status = "critical"
            issues.append(f"Cache hit rate ({snapshot.cache_hit_rate:.1%}) below critical threshold ({self.thresholds.cache_hit_rate_critical:.0%})")
        elif snapshot.cache_hit_rate < self.thresholds.cache_hit_rate_warning and snapshot.cache_total_requests > 0:
            status = "warning" if status == "healthy" else status
            issues.append(f"Cache hit rate ({snapshot.cache_hit_rate:.1%}) below warning threshold ({self.thresholds.cache_hit_rate_warning:.0%})")

        # Check DB P95
        if snapshot.db_p95_ms > self.thresholds.db_p99_ms:
            status = "critical"
            issues.append(f"DB P95 ({snapshot.db_p95_ms:.0f}ms) exceeds critical threshold ({self.thresholds.db_p99_ms}ms)")
        elif snapshot.db_p95_ms > self.thresholds.db_p95_ms:
            status = "warning" if status == "healthy" else status
            issues.append(f"DB P95 ({snapshot.db_p95_ms:.0f}ms) exceeds warning threshold ({self.thresholds.db_p95_ms}ms)")

        # Check capacity
        capacity_usage = snapshot.concurrent_users / self.thresholds.max_concurrent_users
        if capacity_usage > 1.0:
            status = "critical"
            issues.append(f"Concurrent users ({snapshot.concurrent_users}) exceeds max capacity ({self.thresholds.max_concurrent_users})")
        elif capacity_usage > self.thresholds.concurrent_users_warning:
            status = "warning" if status == "healthy" else status
            issues.append(f"Concurrent users at {capacity_usage:.0%} of max capacity")

        return {
            "status": status,
            "issues": issues,
            "metrics": snapshot_dict,
            "thresholds": {
                "api_p95_ms": self.thresholds.api_p95_ms,
                "cache_hit_rate_warning": self.thresholds.cache_hit_rate_warning,
                "db_p95_ms": self.thresholds.db_p95_ms,
                "max_concurrent_users": self.thresholds.max_concurrent_users,
            },
            "active_alerts": len(self._active_alerts),
            "generated_at": datetime.now().isoformat(),
        }

    # ========================================================================
    # ALERTING METHODS
    # ========================================================================

    def check_thresholds(self) -> List[Alert]:
        """Check all thresholds and generate alerts"""
        alerts = []
        snapshot = self.get_current_snapshot()

        # Check API P95
        if snapshot.api_p95_ms > self.thresholds.api_p95_ms and snapshot.api_request_count > 0:
            alert = self._create_alert(
                metric_type=MetricType.API_LATENCY,
                severity=AlertSeverity.WARNING if snapshot.api_p95_ms <= self.thresholds.api_p99_ms else AlertSeverity.CRITICAL,
                message=f"API P95 latency ({snapshot.api_p95_ms:.0f}ms) exceeds threshold",
                current_value=snapshot.api_p95_ms,
                threshold_value=self.thresholds.api_p95_ms,
            )
            if alert:
                alerts.append(alert)

        # Check Cache Hit Rate
        if snapshot.cache_hit_rate < self.thresholds.cache_hit_rate_warning and snapshot.cache_total_requests > 10:
            alert = self._create_alert(
                metric_type=MetricType.CACHE_HIT,
                severity=AlertSeverity.WARNING if snapshot.cache_hit_rate >= self.thresholds.cache_hit_rate_critical else AlertSeverity.CRITICAL,
                message=f"Cache hit rate ({snapshot.cache_hit_rate:.1%}) below threshold",
                current_value=snapshot.cache_hit_rate,
                threshold_value=self.thresholds.cache_hit_rate_warning,
            )
            if alert:
                alerts.append(alert)

        # Check DB P95
        if snapshot.db_p95_ms > self.thresholds.db_p95_ms and snapshot.db_query_count > 0:
            alert = self._create_alert(
                metric_type=MetricType.DB_QUERY,
                severity=AlertSeverity.WARNING if snapshot.db_p95_ms <= self.thresholds.db_p99_ms else AlertSeverity.CRITICAL,
                message=f"Database P95 latency ({snapshot.db_p95_ms:.0f}ms) exceeds threshold",
                current_value=snapshot.db_p95_ms,
                threshold_value=self.thresholds.db_p95_ms,
            )
            if alert:
                alerts.append(alert)

        return alerts

    def _create_alert(self,
                      metric_type: MetricType,
                      severity: AlertSeverity,
                      message: str,
                      current_value: float,
                      threshold_value: float) -> Optional[Alert]:
        """Create an alert if not already active"""
        alert_key = f"{metric_type.value}:{severity.value}"

        with self._alert_lock:
            if alert_key in self._active_alerts:
                return None  # Already alerted

            alert = Alert(
                alert_id=f"alert_{int(time.time() * 1000)}_{hash(message) % 10000}",
                severity=severity,
                metric_type=metric_type,
                message=message,
                current_value=current_value,
                threshold_value=threshold_value,
            )

            self._active_alerts[alert_key] = alert
            self._alert_history.append(alert)

            # Notify callbacks
            for callback in self._alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

            logger.warning(f"Alert generated: [{severity.value.upper()}] {message}")
            return alert

    def resolve_alert(self, alert_key: str):
        """Resolve an active alert"""
        with self._alert_lock:
            if alert_key in self._active_alerts:
                alert = self._active_alerts.pop(alert_key)
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert.message}")

    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """Register a callback for new alerts"""
        self._alert_callbacks.append(callback)

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        with self._alert_lock:
            return [alert.to_dict() for alert in self._active_alerts.values()]

    # ========================================================================
    # BACKGROUND TASKS
    # ========================================================================

    async def start_monitoring(self):
        """Start background monitoring tasks"""
        self._shutdown = False
        self._snapshot_task = asyncio.create_task(self._snapshot_loop())
        self._alert_check_task = asyncio.create_task(self._alert_check_loop())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        self._shutdown = True
        if self._snapshot_task:
            self._snapshot_task.cancel()
            try:
                await self._snapshot_task
            except asyncio.CancelledError:
                pass

        if self._alert_check_task:
            self._alert_check_task.cancel()
            try:
                await self._alert_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _snapshot_loop(self):
        """Background loop for taking periodic snapshots"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self._snapshot_interval_seconds)
                snapshot = self.get_current_snapshot()
                self._snapshots.append(snapshot)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Snapshot error: {e}")

    async def _alert_check_loop(self):
        """Background loop for checking thresholds"""
        while not self._shutdown:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                self.check_thresholds()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert check error: {e}")

    def reset_metrics(self):
        """Reset all metrics"""
        self.collector.clear()
        with self._users_lock:
            self._active_users.clear()
            self._peak_users = 0
        with self._alert_lock:
            self._active_alerts.clear()
        logger.info("Performance metrics reset")


# Singleton accessor
def get_performance_monitor() -> PerformanceMonitor:
    """Get singleton performance monitor instance"""
    return PerformanceMonitor()


# ============================================================================
# DECORATORS FOR EASY INTEGRATION
# ============================================================================

def monitor_api_latency(endpoint: str = ""):
    """Decorator to monitor API endpoint latency"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                monitor.record_api_latency(latency_ms, endpoint, success)

        def sync_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            success = True
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                success = False
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                monitor.record_api_latency(latency_ms, endpoint, success)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def monitor_db_query(query_type: str = ""):
    """Decorator to monitor database query latency"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                latency_ms = (time.time() - start_time) * 1000
                monitor.record_db_query(latency_ms, query_type)

        def sync_wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                latency_ms = (time.time() - start_time) * 1000
                monitor.record_db_query(latency_ms, query_type)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":
    async def test_performance_monitor():
        """Test the performance monitor"""
        monitor = get_performance_monitor()

        print("=" * 60)
        print("Performance Monitor Test")
        print("=" * 60)

        # Simulate API requests
        print("\n1. Simulating API requests...")
        for i in range(100):
            latency = 20 + (i % 50) + (10 if i > 90 else 0)  # Some variation
            monitor.record_api_latency(latency, "/api/leads", success=(i % 20 != 0))

        # Simulate cache operations
        print("2. Simulating cache operations...")
        for i in range(100):
            monitor.record_cache_operation(hit=(i % 10 < 9))  # 90% hit rate

        # Simulate DB queries
        print("3. Simulating database queries...")
        for i in range(50):
            latency = 10 + (i % 30)
            monitor.record_db_query(latency, "SELECT")

        # Simulate AI requests
        print("4. Simulating AI requests...")
        for i in range(20):
            latency = 200 + (i * 50)
            monitor.record_ai_request(latency, "claude-3-5-sonnet")

        # Simulate user activity
        print("5. Simulating user activity...")
        for i in range(50):
            monitor.record_user_activity(f"user_{i}", active=True)

        # Get health report
        print("\n6. Health Report:")
        health = monitor.get_health_report()
        print(f"   Status: {health['status']}")
        print(f"   Issues: {health['issues'] if health['issues'] else 'None'}")

        print("\n7. Metrics Summary:")
        print(f"   API P95: {health['metrics']['api']['p95_ms']:.1f}ms (threshold: {health['thresholds']['api_p95_ms']}ms)")
        print(f"   Cache Hit Rate: {health['metrics']['cache']['hit_rate']:.1%} (threshold: {health['thresholds']['cache_hit_rate_warning']:.0%})")
        print(f"   DB P95: {health['metrics']['database']['p95_ms']:.1f}ms (threshold: {health['thresholds']['db_p95_ms']}ms)")
        print(f"   Concurrent Users: {health['metrics']['capacity']['concurrent_users']}")

        # Check alerts
        print("\n8. Active Alerts:")
        alerts = monitor.check_thresholds()
        if alerts:
            for alert in alerts:
                print(f"   [{alert.severity.value.upper()}] {alert.message}")
        else:
            print("   No alerts generated")

        print("\n" + "=" * 60)
        print("Test completed!")

    asyncio.run(test_performance_monitor())
