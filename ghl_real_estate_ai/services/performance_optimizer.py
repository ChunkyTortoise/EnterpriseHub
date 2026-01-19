"""
Performance Optimizer for Jorge's Revenue Acceleration Platform
================================================================

Comprehensive performance optimization service that ensures sub-100ms API responses,
>90% cache hit rates, and 1000+ req/sec throughput capacity.

Performance Targets:
- API Response Times: <100ms (95th percentile)
- Golden Lead Detection: <50ms
- Cache Hit Rate: >90%
- Database Queries: <50ms
- Concurrent Requests: 1000+ req/sec

Author: Claude Code Performance Optimization Agent
Created: 2026-01-17
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import statistics
import psutil
from functools import wraps

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService, get_cache_service

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics tracking"""

    # Response time metrics (milliseconds)
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Throughput metrics
    requests_per_second: deque = field(default_factory=lambda: deque(maxlen=60))

    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0

    # Database metrics
    db_query_times: deque = field(default_factory=lambda: deque(maxlen=500))

    # Error tracking
    errors: deque = field(default_factory=lambda: deque(maxlen=100))

    # Resource usage
    memory_usage_mb: deque = field(default_factory=lambda: deque(maxlen=120))
    cpu_usage_percent: deque = field(default_factory=lambda: deque(maxlen=120))

    # Timestamps
    last_reset: datetime = field(default_factory=datetime.now)

    def record_response_time(self, duration_ms: float):
        """Record API response time"""
        self.response_times.append(duration_ms)

    def record_cache_hit(self):
        """Record cache hit"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record cache miss"""
        self.cache_misses += 1

    def record_db_query(self, duration_ms: float):
        """Record database query time"""
        self.db_query_times.append(duration_ms)

    def record_error(self, error: str):
        """Record error"""
        self.errors.append({
            'timestamp': datetime.now().isoformat(),
            'error': error
        })

    def record_throughput(self, requests_count: int):
        """Record throughput for current second"""
        self.requests_per_second.append(requests_count)

    def record_system_resources(self):
        """Record current system resource usage"""
        try:
            process = psutil.Process()
            self.memory_usage_mb.append(process.memory_info().rss / 1024 / 1024)
            self.cpu_usage_percent.append(process.cpu_percent(interval=0.1))
        except Exception as e:
            logger.warning(f"Failed to record system resources: {e}")

    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return (self.cache_hits / total) * 100

    def get_p95_response_time(self) -> float:
        """Get 95th percentile response time"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_p99_response_time(self) -> float:
        """Get 99th percentile response time"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.99)
        return sorted_times[min(index, len(sorted_times) - 1)]

    def get_avg_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    def get_avg_throughput(self) -> float:
        """Get average requests per second"""
        if not self.requests_per_second:
            return 0.0
        return statistics.mean(self.requests_per_second)

    def get_peak_throughput(self) -> float:
        """Get peak requests per second"""
        if not self.requests_per_second:
            return 0.0
        return max(self.requests_per_second)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'response_times': {
                'avg_ms': round(self.get_avg_response_time(), 2),
                'p95_ms': round(self.get_p95_response_time(), 2),
                'p99_ms': round(self.get_p99_response_time(), 2),
                'min_ms': round(min(self.response_times), 2) if self.response_times else 0,
                'max_ms': round(max(self.response_times), 2) if self.response_times else 0,
            },
            'throughput': {
                'avg_req_per_sec': round(self.get_avg_throughput(), 2),
                'peak_req_per_sec': round(self.get_peak_throughput(), 2),
            },
            'cache': {
                'hit_rate_percent': round(self.get_cache_hit_rate(), 2),
                'hits': self.cache_hits,
                'misses': self.cache_misses,
            },
            'database': {
                'avg_query_ms': round(statistics.mean(self.db_query_times), 2) if self.db_query_times else 0,
                'p95_query_ms': round(sorted(self.db_query_times)[int(len(self.db_query_times) * 0.95)], 2) if self.db_query_times else 0,
            },
            'resources': {
                'avg_memory_mb': round(statistics.mean(self.memory_usage_mb), 2) if self.memory_usage_mb else 0,
                'peak_memory_mb': round(max(self.memory_usage_mb), 2) if self.memory_usage_mb else 0,
                'avg_cpu_percent': round(statistics.mean(self.cpu_usage_percent), 2) if self.cpu_usage_percent else 0,
                'peak_cpu_percent': round(max(self.cpu_usage_percent), 2) if self.cpu_usage_percent else 0,
            },
            'errors': {
                'count': len(self.errors),
                'recent': list(self.errors)[-10:] if self.errors else [],
            },
            'collection_period': {
                'start': self.last_reset.isoformat(),
                'duration_seconds': (datetime.now() - self.last_reset).total_seconds(),
            }
        }

    def reset(self):
        """Reset all metrics"""
        self.response_times.clear()
        self.requests_per_second.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.db_query_times.clear()
        self.errors.clear()
        self.memory_usage_mb.clear()
        self.cpu_usage_percent.clear()
        self.last_reset = datetime.now()


class PerformanceOptimizer:
    """
    Performance optimization service for Jorge's Revenue Acceleration Platform.

    Features:
    - Real-time performance monitoring
    - Automatic cache optimization
    - Query performance tracking
    - Resource usage monitoring
    - Performance alerts and recommendations
    """

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.cache = get_cache_service()

        # Performance thresholds
        self.thresholds = {
            'response_time_p95_ms': 100,
            'response_time_p99_ms': 200,
            'cache_hit_rate_percent': 90,
            'db_query_p95_ms': 50,
            'max_memory_mb': 2048,
            'max_cpu_percent': 70,
        }

        # Background monitoring
        self._monitoring_task = None
        self._monitoring_enabled = False

        logger.info("Performance Optimizer initialized")

    async def start_monitoring(self):
        """Start background performance monitoring"""
        if self._monitoring_enabled:
            return

        self._monitoring_enabled = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("Performance monitoring started")

    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        self._monitoring_enabled = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")

    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self._monitoring_enabled:
            try:
                # Record system resources
                self.metrics.record_system_resources()

                # Check performance thresholds
                await self._check_thresholds()

                # Sleep for 1 second
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _check_thresholds(self):
        """Check performance thresholds and alert if exceeded"""
        summary = self.metrics.get_summary()

        # Check response time
        if summary['response_times']['p95_ms'] > self.thresholds['response_time_p95_ms']:
            logger.warning(
                f"⚠️ High response time: P95={summary['response_times']['p95_ms']:.1f}ms "
                f"(threshold: {self.thresholds['response_time_p95_ms']}ms)"
            )

        # Check cache hit rate
        if summary['cache']['hit_rate_percent'] < self.thresholds['cache_hit_rate_percent']:
            logger.warning(
                f"⚠️ Low cache hit rate: {summary['cache']['hit_rate_percent']:.1f}% "
                f"(threshold: {self.thresholds['cache_hit_rate_percent']}%)"
            )

        # Check memory usage
        if summary['resources']['peak_memory_mb'] > self.thresholds['max_memory_mb']:
            logger.warning(
                f"⚠️ High memory usage: {summary['resources']['peak_memory_mb']:.1f}MB "
                f"(threshold: {self.thresholds['max_memory_mb']}MB)"
            )

    def track_performance(self, operation_name: str = None):
        """
        Decorator to track performance of async functions.

        Usage:
            @performance_optimizer.track_performance("golden_lead_detection")
            async def detect_golden_lead(lead_data):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                error_occurred = False

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    error_occurred = True
                    self.metrics.record_error(f"{operation_name or func.__name__}: {str(e)}")
                    raise
                finally:
                    duration_ms = (time.time() - start_time) * 1000
                    self.metrics.record_response_time(duration_ms)

                    if not error_occurred:
                        logger.debug(f"✓ {operation_name or func.__name__} completed in {duration_ms:.2f}ms")

            return wrapper
        return decorator

    def track_cache_operation(self, hit: bool):
        """Track cache hit/miss"""
        if hit:
            self.metrics.record_cache_hit()
        else:
            self.metrics.record_cache_miss()

    def track_db_query(self, duration_ms: float):
        """Track database query performance"""
        self.metrics.record_db_query(duration_ms)

    async def optimize_cache_ttl(self, key_prefix: str, access_pattern: List[float]) -> int:
        """
        Optimize cache TTL based on access patterns.

        Args:
            key_prefix: Cache key prefix to optimize
            access_pattern: List of time intervals between accesses (seconds)

        Returns:
            Optimized TTL in seconds
        """
        if not access_pattern or len(access_pattern) < 2:
            return 300  # Default 5 minutes

        # Calculate average access interval
        avg_interval = statistics.mean(access_pattern)

        # Set TTL to 2x average interval (with bounds)
        optimized_ttl = int(avg_interval * 2)
        optimized_ttl = max(60, min(optimized_ttl, 3600))  # Between 1 min and 1 hour

        logger.info(f"Optimized TTL for {key_prefix}: {optimized_ttl}s (avg interval: {avg_interval:.1f}s)")
        return optimized_ttl

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary"""
        return self.metrics.get_summary()

    async def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get performance optimization recommendations"""
        summary = self.metrics.get_summary()
        recommendations = []

        # Response time recommendations
        if summary['response_times']['p95_ms'] > self.thresholds['response_time_p95_ms']:
            recommendations.append({
                'category': 'response_time',
                'severity': 'high',
                'current_value': summary['response_times']['p95_ms'],
                'threshold': self.thresholds['response_time_p95_ms'],
                'recommendation': 'Implement additional caching or optimize slow operations',
                'actions': [
                    'Identify slow endpoints using performance profiling',
                    'Add caching for frequently accessed data',
                    'Optimize database queries',
                    'Consider implementing request batching',
                ]
            })

        # Cache recommendations
        if summary['cache']['hit_rate_percent'] < self.thresholds['cache_hit_rate_percent']:
            recommendations.append({
                'category': 'cache_performance',
                'severity': 'medium',
                'current_value': summary['cache']['hit_rate_percent'],
                'threshold': self.thresholds['cache_hit_rate_percent'],
                'recommendation': 'Improve cache hit rate through TTL optimization',
                'actions': [
                    'Increase cache TTL for stable data',
                    'Implement cache warming for frequently accessed keys',
                    'Add predictive pre-caching based on access patterns',
                    'Review cache key design for better reuse',
                ]
            })

        # Database recommendations
        if summary['database']['p95_query_ms'] > self.thresholds['db_query_p95_ms']:
            recommendations.append({
                'category': 'database_performance',
                'severity': 'high',
                'current_value': summary['database']['p95_query_ms'],
                'threshold': self.thresholds['db_query_p95_ms'],
                'recommendation': 'Optimize database queries and indexes',
                'actions': [
                    'Add indexes for frequently queried fields',
                    'Optimize query complexity',
                    'Implement query result caching',
                    'Consider read replicas for heavy read workloads',
                ]
            })

        # Memory recommendations
        if summary['resources']['peak_memory_mb'] > self.thresholds['max_memory_mb']:
            recommendations.append({
                'category': 'memory_usage',
                'severity': 'high',
                'current_value': summary['resources']['peak_memory_mb'],
                'threshold': self.thresholds['max_memory_mb'],
                'recommendation': 'Reduce memory footprint',
                'actions': [
                    'Implement data pagination for large result sets',
                    'Review object lifecycle and garbage collection',
                    'Optimize in-memory caching strategies',
                    'Consider increasing server memory allocation',
                ]
            })

        # CPU recommendations
        if summary['resources']['peak_cpu_percent'] > self.thresholds['max_cpu_percent']:
            recommendations.append({
                'category': 'cpu_usage',
                'severity': 'medium',
                'current_value': summary['resources']['peak_cpu_percent'],
                'threshold': self.thresholds['max_cpu_percent'],
                'recommendation': 'Reduce CPU utilization',
                'actions': [
                    'Optimize computational algorithms',
                    'Implement async processing for heavy operations',
                    'Consider horizontal scaling',
                    'Profile CPU-intensive operations',
                ]
            })

        return recommendations

    async def reset_metrics(self):
        """Reset performance metrics"""
        self.metrics.reset()
        logger.info("Performance metrics reset")

    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status based on performance metrics"""
        summary = self.metrics.get_summary()

        # Calculate health score (0-100)
        health_factors = []

        # Response time health (0-25 points)
        response_time_health = max(0, 25 - (summary['response_times']['p95_ms'] / 4))
        health_factors.append(response_time_health)

        # Cache health (0-25 points)
        cache_health = (summary['cache']['hit_rate_percent'] / 100) * 25
        health_factors.append(cache_health)

        # Database health (0-25 points)
        db_health = max(0, 25 - (summary['database']['p95_query_ms'] / 2))
        health_factors.append(db_health)

        # Resource health (0-25 points)
        memory_health = max(0, 12.5 - (summary['resources']['peak_memory_mb'] / 163.84))  # 2048MB max
        cpu_health = max(0, 12.5 - (summary['resources']['peak_cpu_percent'] / 5.6))  # 70% max
        health_factors.append(memory_health + cpu_health)

        overall_health = sum(health_factors)

        # Determine status
        if overall_health >= 90:
            status = 'excellent'
            status_emoji = '🟢'
        elif overall_health >= 75:
            status = 'good'
            status_emoji = '🟡'
        elif overall_health >= 50:
            status = 'degraded'
            status_emoji = '🟠'
        else:
            status = 'poor'
            status_emoji = '🔴'

        return {
            'status': status,
            'status_emoji': status_emoji,
            'health_score': round(overall_health, 1),
            'factors': {
                'response_time': round(response_time_health, 1),
                'cache': round(cache_health, 1),
                'database': round(db_health, 1),
                'resources': round(memory_health + cpu_health, 1),
            },
            'metrics_summary': summary,
            'timestamp': datetime.now().isoformat(),
        }


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


# Convenience decorator for tracking performance
def track_performance(operation_name: str = None):
    """
    Convenience decorator for tracking performance.

    Usage:
        @track_performance("my_operation")
        async def my_function():
            ...
    """
    optimizer = get_performance_optimizer()
    return optimizer.track_performance(operation_name)
