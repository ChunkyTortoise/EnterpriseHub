"""
Real-Time Performance Monitoring Service for EnterpriseHub
Comprehensive performance tracking and optimization validation

Monitoring Features:
- Real-time metrics collection across all optimized services
- Performance trend analysis and alerting
- Optimization impact measurement and validation
- Resource utilization monitoring
- Auto-scaling recommendations

Target: Track 30-40% performance improvements across all services
Real-time dashboards and alerts for production monitoring
"""

import asyncio
import time
import json
import statistics
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from pathlib import Path
import psutil

from ghl_real_estate_ai.services.optimized_webhook_processor import get_optimized_webhook_processor
from ghl_real_estate_ai.services.redis_optimization_service import get_optimized_redis_client
from ghl_real_estate_ai.services.batch_ml_inference_service import get_batch_ml_service
from ghl_real_estate_ai.services.database_cache_service import get_db_cache_service
from ghl_real_estate_ai.services.async_http_client import get_async_http_client
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric with metadata."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    service: str
    category: str  # latency, throughput, error_rate, resource_usage
    target_value: Optional[float] = None
    improvement_percentage: Optional[float] = None


@dataclass
class ServiceHealthStatus:
    """Health status for individual service."""
    service_name: str
    healthy: bool
    performance_grade: str  # A+, A, B, C, D, F
    response_time_ms: float
    error_rate: float
    throughput: float
    last_check: datetime
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class SystemResourceMetrics:
    """System resource utilization metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    network_io_mbps: float
    active_connections: int
    timestamp: datetime


@dataclass
class PerformanceAlert:
    """Performance alert with severity and recommendations."""
    severity: str  # critical, warning, info
    service: str
    metric: str
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    recommendations: List[str] = field(default_factory=list)


class PerformanceMonitoringService:
    """
    Real-time performance monitoring with comprehensive optimization tracking.

    Features:
    1. Multi-service performance tracking
    2. Real-time metric collection and analysis
    3. Performance trend analysis and forecasting
    4. Automated alerting and recommendations
    5. Optimization impact validation
    6. Resource utilization monitoring
    """

    def __init__(
        self,
        monitoring_interval_seconds: int = 10,
        metric_retention_hours: int = 24,
        alert_threshold_cpu: float = 80.0,
        alert_threshold_memory: float = 85.0,
        alert_threshold_response_time: float = 200.0,
        enable_auto_alerts: bool = True
    ):
        """Initialize performance monitoring service."""

        self.monitoring_interval = monitoring_interval_seconds
        self.metric_retention_hours = metric_retention_hours
        self.alert_threshold_cpu = alert_threshold_cpu
        self.alert_threshold_memory = alert_threshold_memory
        self.alert_threshold_response_time = alert_threshold_response_time
        self.enable_auto_alerts = enable_auto_alerts

        # Performance data storage
        self._metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=int(metric_retention_hours * 360))  # 10s intervals
        )
        self._service_health: Dict[str, ServiceHealthStatus] = {}
        self._system_resources: deque = deque(maxlen=int(metric_retention_hours * 360))
        self._active_alerts: List[PerformanceAlert] = []

        # Service references (will be initialized)
        self._webhook_processor = None
        self._redis_client = None
        self._ml_service = None
        self._db_cache = None
        self._http_client = None

        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_active = False

        # Performance baselines (before optimization)
        self._performance_baselines = {
            "webhook_processing_ms": 200.0,  # Original webhook processing time
            "redis_operation_ms": 25.0,      # Original Redis operation time
            "ml_inference_ms": 500.0,        # Original ML inference time
            "db_query_ms": 100.0,            # Original database query time
            "http_request_ms": 300.0,        # Original HTTP request time
        }

        # Performance targets (after optimization)
        self._performance_targets = {
            "webhook_processing_ms": 140.0,  # 30% improvement target
            "redis_operation_ms": 15.0,      # 40% improvement target
            "ml_inference_ms": 300.0,        # 40% improvement target
            "db_query_ms": 50.0,             # 50% improvement target
            "http_request_ms": 100.0,        # 67% improvement target
        }

        logger.info(f"Performance Monitoring Service initialized with {monitoring_interval_seconds}s intervals")

    async def initialize(self) -> None:
        """Initialize monitoring service and service connections."""
        try:
            # Initialize service connections
            logger.info("Initializing service connections for monitoring...")

            try:
                self._webhook_processor = get_optimized_webhook_processor()
                logger.info("✓ Webhook processor connection established")
            except Exception as e:
                logger.warning(f"Webhook processor unavailable: {e}")

            try:
                self._redis_client = await get_optimized_redis_client()
                logger.info("✓ Redis client connection established")
            except Exception as e:
                logger.warning(f"Redis client unavailable: {e}")

            try:
                self._ml_service = get_batch_ml_service()
                logger.info("✓ ML service connection established")
            except Exception as e:
                logger.warning(f"ML service unavailable: {e}")

            try:
                self._http_client = await get_async_http_client()
                logger.info("✓ HTTP client connection established")
            except Exception as e:
                logger.warning(f"HTTP client unavailable: {e}")

            # Start monitoring task
            await self.start_monitoring()

            logger.info("Performance monitoring service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize performance monitoring: {e}")
            raise

    async def start_monitoring(self) -> None:
        """Start real-time performance monitoring."""
        if self._monitoring_active:
            logger.warning("Monitoring is already active")
            return

        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Real-time performance monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        self._monitoring_active = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Performance monitoring stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                start_time = time.time()

                # Collect metrics from all services
                await self._collect_service_metrics()

                # Collect system resource metrics
                await self._collect_system_metrics()

                # Analyze performance and generate alerts
                await self._analyze_performance()

                # Update service health status
                await self._update_service_health()

                # Clean up old data
                await self._cleanup_old_data()

                # Calculate actual monitoring time and adjust sleep
                monitoring_time = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval - monitoring_time)

                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def _collect_service_metrics(self) -> None:
        """Collect performance metrics from all optimized services."""
        current_time = datetime.now()

        # Webhook Processor Metrics
        if self._webhook_processor:
            try:
                webhook_metrics = await self._webhook_processor.get_optimization_metrics()

                await self._record_metric(PerformanceMetric(
                    name="webhook_processing_time",
                    value=webhook_metrics.get("average_total_time_ms", 0),
                    unit="ms",
                    timestamp=current_time,
                    service="webhook_processor",
                    category="latency",
                    target_value=self._performance_targets["webhook_processing_ms"]
                ))

                await self._record_metric(PerformanceMetric(
                    name="webhook_cache_hit_rate",
                    value=webhook_metrics.get("cache_status", {}).get("hit_rate", 0) * 100,
                    unit="percent",
                    timestamp=current_time,
                    service="webhook_processor",
                    category="efficiency",
                    target_value=85.0
                ))

            except Exception as e:
                logger.warning(f"Failed to collect webhook metrics: {e}")

        # Redis Optimization Metrics
        if self._redis_client:
            try:
                redis_metrics = await self._redis_client.get_performance_metrics()

                await self._record_metric(PerformanceMetric(
                    name="redis_operation_time",
                    value=redis_metrics.get("performance", {}).get("average_time_ms", 0),
                    unit="ms",
                    timestamp=current_time,
                    service="redis_client",
                    category="latency",
                    target_value=self._performance_targets["redis_operation_ms"]
                ))

                await self._record_metric(PerformanceMetric(
                    name="redis_cache_hit_rate",
                    value=redis_metrics.get("performance", {}).get("cache_hit_rate", 0) * 100,
                    unit="percent",
                    timestamp=current_time,
                    service="redis_client",
                    category="efficiency",
                    target_value=90.0
                ))

            except Exception as e:
                logger.warning(f"Failed to collect Redis metrics: {e}")

        # ML Service Metrics
        if self._ml_service:
            try:
                ml_metrics = await self._ml_service.get_performance_metrics()

                await self._record_metric(PerformanceMetric(
                    name="ml_inference_time",
                    value=ml_metrics.get("performance", {}).get("average_inference_time_ms", 0),
                    unit="ms",
                    timestamp=current_time,
                    service="ml_service",
                    category="latency",
                    target_value=self._performance_targets["ml_inference_ms"]
                ))

                await self._record_metric(PerformanceMetric(
                    name="ml_throughput",
                    value=ml_metrics.get("performance", {}).get("throughput_per_second", 0),
                    unit="ops/sec",
                    timestamp=current_time,
                    service="ml_service",
                    category="throughput",
                    target_value=100.0
                ))

                await self._record_metric(PerformanceMetric(
                    name="ml_batch_efficiency",
                    value=ml_metrics.get("performance", {}).get("average_batch_size", 1),
                    unit="requests/batch",
                    timestamp=current_time,
                    service="ml_service",
                    category="efficiency",
                    target_value=2.0
                ))

            except Exception as e:
                logger.warning(f"Failed to collect ML metrics: {e}")

        # HTTP Client Metrics
        if self._http_client:
            try:
                http_metrics = await self._http_client.get_performance_metrics()

                await self._record_metric(PerformanceMetric(
                    name="http_request_time",
                    value=http_metrics.get("performance", {}).get("average_request_time_ms", 0),
                    unit="ms",
                    timestamp=current_time,
                    service="http_client",
                    category="latency",
                    target_value=self._performance_targets["http_request_ms"]
                ))

                await self._record_metric(PerformanceMetric(
                    name="http_error_rate",
                    value=http_metrics.get("performance", {}).get("error_rate", 0) * 100,
                    unit="percent",
                    timestamp=current_time,
                    service="http_client",
                    category="error_rate",
                    target_value=5.0
                ))

            except Exception as e:
                logger.warning(f"Failed to collect HTTP metrics: {e}")

    async def _collect_system_metrics(self) -> None:
        """Collect system resource utilization metrics."""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage('/')

            # Network I/O (simplified)
            network = psutil.net_io_counters()
            network_mbps = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)

            # Active connections (estimate)
            connections = len(psutil.net_connections())

            resource_metrics = SystemResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_gb=memory.available / (1024**3),
                disk_usage_percent=disk.percent,
                network_io_mbps=network_mbps,
                active_connections=connections,
                timestamp=datetime.now()
            )

            self._system_resources.append(resource_metrics)

            # Record as individual metrics for alerting
            await self._record_metric(PerformanceMetric(
                name="system_cpu_usage",
                value=cpu_percent,
                unit="percent",
                timestamp=datetime.now(),
                service="system",
                category="resource_usage",
                target_value=80.0
            ))

            await self._record_metric(PerformanceMetric(
                name="system_memory_usage",
                value=memory.percent,
                unit="percent",
                timestamp=datetime.now(),
                service="system",
                category="resource_usage",
                target_value=85.0
            ))

        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

    async def _record_metric(self, metric: PerformanceMetric) -> None:
        """Record performance metric with automatic improvement calculation."""
        # Calculate improvement percentage if baseline exists
        baseline_key = f"{metric.name.replace('_', '_')}"
        if baseline_key in self._performance_baselines:
            baseline_value = self._performance_baselines[baseline_key]
            if baseline_value > 0:
                if metric.category == "latency":
                    # Lower is better for latency metrics
                    improvement = ((baseline_value - metric.value) / baseline_value) * 100
                else:
                    # Higher is better for throughput/efficiency metrics
                    improvement = ((metric.value - baseline_value) / baseline_value) * 100
                metric.improvement_percentage = improvement

        # Store in metrics history
        metric_key = f"{metric.service}_{metric.name}"
        self._metrics_history[metric_key].append(metric)

    async def _analyze_performance(self) -> None:
        """Analyze performance trends and generate alerts."""
        if not self.enable_auto_alerts:
            return

        current_time = datetime.now()
        new_alerts = []

        # Analyze each metric for threshold violations
        for metric_key, metrics in self._metrics_history.items():
            if not metrics:
                continue

            latest_metric = metrics[-1]

            # Check for threshold violations
            if latest_metric.target_value is not None:
                violation = False
                if latest_metric.category == "latency":
                    violation = latest_metric.value > latest_metric.target_value
                elif latest_metric.category == "error_rate":
                    violation = latest_metric.value > latest_metric.target_value
                else:
                    violation = latest_metric.value < latest_metric.target_value

                if violation:
                    severity = "critical" if latest_metric.value > latest_metric.target_value * 1.5 else "warning"

                    alert = PerformanceAlert(
                        severity=severity,
                        service=latest_metric.service,
                        metric=latest_metric.name,
                        current_value=latest_metric.value,
                        threshold_value=latest_metric.target_value,
                        message=f"{latest_metric.service} {latest_metric.name} exceeded threshold",
                        timestamp=current_time,
                        recommendations=self._get_performance_recommendations(latest_metric)
                    )
                    new_alerts.append(alert)

        # Add new alerts
        self._active_alerts.extend(new_alerts)

        # Clean up old alerts (older than 1 hour)
        cutoff_time = current_time - timedelta(hours=1)
        self._active_alerts = [
            alert for alert in self._active_alerts
            if alert.timestamp > cutoff_time
        ]

        if new_alerts:
            logger.warning(f"Generated {len(new_alerts)} performance alerts")

    def _get_performance_recommendations(self, metric: PerformanceMetric) -> List[str]:
        """Generate performance recommendations based on metric violations."""
        recommendations = []

        if metric.service == "webhook_processor" and metric.category == "latency":
            recommendations.extend([
                "Consider increasing webhook processor thread pool size",
                "Check for Redis connection issues",
                "Review circuit breaker thresholds"
            ])

        elif metric.service == "redis_client" and metric.category == "latency":
            recommendations.extend([
                "Increase Redis connection pool size",
                "Check Redis server performance",
                "Consider Redis cluster for horizontal scaling"
            ])

        elif metric.service == "ml_service" and metric.category == "latency":
            recommendations.extend([
                "Increase ML inference batch size",
                "Add more CPU thread pool workers",
                "Consider GPU acceleration for large models"
            ])

        elif metric.service == "http_client" and metric.category == "latency":
            recommendations.extend([
                "Increase HTTP connection pool size",
                "Check network connectivity",
                "Enable HTTP/2 for better performance"
            ])

        elif metric.service == "system" and metric.name == "system_cpu_usage":
            recommendations.extend([
                "Scale up CPU resources",
                "Optimize CPU-intensive operations",
                "Consider horizontal scaling"
            ])

        elif metric.service == "system" and metric.name == "system_memory_usage":
            recommendations.extend([
                "Increase available memory",
                "Review memory leaks in applications",
                "Optimize cache sizes"
            ])

        return recommendations

    async def _update_service_health(self) -> None:
        """Update health status for all monitored services."""
        current_time = datetime.now()

        services = ["webhook_processor", "redis_client", "ml_service", "http_client", "system"]

        for service in services:
            try:
                health_status = await self._calculate_service_health(service)
                self._service_health[service] = health_status
            except Exception as e:
                logger.warning(f"Failed to update health for {service}: {e}")

    async def _calculate_service_health(self, service: str) -> ServiceHealthStatus:
        """Calculate health status for a specific service."""
        current_time = datetime.now()

        # Get recent metrics for the service
        service_metrics = {}
        for metric_key, metrics in self._metrics_history.items():
            if metric_key.startswith(service) and metrics:
                latest_metric = metrics[-1]
                service_metrics[latest_metric.name] = latest_metric

        if not service_metrics:
            return ServiceHealthStatus(
                service_name=service,
                healthy=False,
                performance_grade="F",
                response_time_ms=0.0,
                error_rate=0.0,
                throughput=0.0,
                last_check=current_time,
                issues=["No metrics available"],
                recommendations=["Check service connectivity"]
            )

        # Calculate performance grade
        performance_scores = []
        issues = []
        recommendations = []

        for metric_name, metric in service_metrics.items():
            if metric.target_value is not None:
                if metric.category == "latency":
                    score = max(0, (metric.target_value - metric.value) / metric.target_value * 100)
                elif metric.category == "error_rate":
                    score = max(0, (metric.target_value - metric.value) / metric.target_value * 100)
                else:
                    score = min(100, (metric.value / metric.target_value) * 100)

                performance_scores.append(score)

                if score < 70:
                    issues.append(f"{metric_name} below target")
                    recommendations.extend(self._get_performance_recommendations(metric))

        # Calculate overall grade
        avg_score = statistics.mean(performance_scores) if performance_scores else 0

        if avg_score >= 95:
            grade = "A+"
        elif avg_score >= 90:
            grade = "A"
        elif avg_score >= 80:
            grade = "B"
        elif avg_score >= 70:
            grade = "C"
        elif avg_score >= 60:
            grade = "D"
        else:
            grade = "F"

        # Extract key metrics
        response_time = 0.0
        error_rate = 0.0
        throughput = 0.0

        for metric in service_metrics.values():
            if metric.category == "latency":
                response_time = metric.value
            elif metric.category == "error_rate":
                error_rate = metric.value
            elif metric.category == "throughput":
                throughput = metric.value

        return ServiceHealthStatus(
            service_name=service,
            healthy=avg_score >= 70,
            performance_grade=grade,
            response_time_ms=response_time,
            error_rate=error_rate,
            throughput=throughput,
            last_check=current_time,
            issues=issues[:5],  # Limit to top 5 issues
            recommendations=recommendations[:5]  # Limit to top 5 recommendations
        )

    async def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data to prevent memory leaks."""
        # Data cleanup is handled by deque maxlen, but we can do additional cleanup here
        pass

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get current real-time performance metrics."""
        current_metrics = {}

        for metric_key, metrics in self._metrics_history.items():
            if metrics:
                latest_metric = metrics[-1]
                current_metrics[metric_key] = {
                    "value": latest_metric.value,
                    "unit": latest_metric.unit,
                    "timestamp": latest_metric.timestamp.isoformat(),
                    "target": latest_metric.target_value,
                    "improvement_percentage": latest_metric.improvement_percentage
                }

        return current_metrics

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        # Calculate overall improvement
        total_improvements = []
        target_achievements = []

        for metric_key, metrics in self._metrics_history.items():
            if metrics:
                latest_metric = metrics[-1]
                if latest_metric.improvement_percentage is not None:
                    total_improvements.append(latest_metric.improvement_percentage)

                if latest_metric.target_value is not None:
                    if latest_metric.category == "latency":
                        achieved = latest_metric.value <= latest_metric.target_value
                    elif latest_metric.category == "error_rate":
                        achieved = latest_metric.value <= latest_metric.target_value
                    else:
                        achieved = latest_metric.value >= latest_metric.target_value
                    target_achievements.append(achieved)

        overall_improvement = statistics.mean(total_improvements) if total_improvements else 0
        target_achievement_rate = (sum(target_achievements) / len(target_achievements) * 100) if target_achievements else 0

        return {
            "overall_performance": {
                "improvement_percentage": round(overall_improvement, 1),
                "target_achievement_rate": round(target_achievement_rate, 1),
                "optimization_success": overall_improvement >= 30.0,  # 30% improvement target
                "grade": self._calculate_overall_grade(overall_improvement)
            },
            "service_health": {
                service: asdict(health) for service, health in self._service_health.items()
            },
            "active_alerts": [asdict(alert) for alert in self._active_alerts[-10:]],  # Latest 10 alerts
            "system_resources": asdict(self._system_resources[-1]) if self._system_resources else None,
            "monitoring_status": {
                "active": self._monitoring_active,
                "interval_seconds": self.monitoring_interval,
                "services_monitored": len(self._service_health),
                "total_metrics": sum(len(metrics) for metrics in self._metrics_history.values())
            }
        }

    def _calculate_overall_grade(self, improvement_percentage: float) -> str:
        """Calculate overall system performance grade."""
        if improvement_percentage >= 40:
            return "A+"
        elif improvement_percentage >= 30:
            return "A"
        elif improvement_percentage >= 20:
            return "B"
        elif improvement_percentage >= 10:
            return "C"
        elif improvement_percentage >= 0:
            return "D"
        else:
            return "F"

    async def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization impact report."""
        report = {
            "optimization_summary": {
                "target_improvement": "30-40%",
                "achieved_improvement": "0%",
                "optimization_success": False,
                "grade": "F"
            },
            "service_improvements": {},
            "key_achievements": [],
            "recommendations": []
        }

        # Calculate service-specific improvements
        service_improvements = defaultdict(list)

        for metric_key, metrics in self._metrics_history.items():
            if metrics:
                latest_metric = metrics[-1]
                if latest_metric.improvement_percentage is not None:
                    service_improvements[latest_metric.service].append(latest_metric.improvement_percentage)

        # Calculate average improvement per service
        for service, improvements in service_improvements.items():
            avg_improvement = statistics.mean(improvements)
            report["service_improvements"][service] = {
                "average_improvement_percentage": round(avg_improvement, 1),
                "target_met": avg_improvement >= 30.0,
                "grade": self._calculate_overall_grade(avg_improvement)
            }

        # Calculate overall improvement
        all_improvements = [imp for improvements in service_improvements.values() for imp in improvements]
        if all_improvements:
            overall_improvement = statistics.mean(all_improvements)
            report["optimization_summary"]["achieved_improvement"] = f"{overall_improvement:.1f}%"
            report["optimization_summary"]["optimization_success"] = overall_improvement >= 30.0
            report["optimization_summary"]["grade"] = self._calculate_overall_grade(overall_improvement)

            # Key achievements
            if overall_improvement >= 30.0:
                report["key_achievements"].append("✅ Achieved 30%+ performance improvement target")
            if overall_improvement >= 40.0:
                report["key_achievements"].append("🚀 Exceeded 40% performance improvement!")

            # Service-specific achievements
            for service, improvement_data in report["service_improvements"].items():
                if improvement_data["target_met"]:
                    report["key_achievements"].append(f"✅ {service} achieved target performance")

        return report

    async def export_metrics_csv(self, output_path: str) -> str:
        """Export metrics to CSV file for analysis."""
        try:
            import csv

            csv_path = Path(output_path)
            csv_path.parent.mkdir(parents=True, exist_ok=True)

            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'timestamp', 'service', 'metric_name', 'value', 'unit',
                    'category', 'target_value', 'improvement_percentage'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for metric_key, metrics in self._metrics_history.items():
                    for metric in metrics:
                        writer.writerow({
                            'timestamp': metric.timestamp.isoformat(),
                            'service': metric.service,
                            'metric_name': metric.name,
                            'value': metric.value,
                            'unit': metric.unit,
                            'category': metric.category,
                            'target_value': metric.target_value,
                            'improvement_percentage': metric.improvement_percentage
                        })

            logger.info(f"Metrics exported to {csv_path}")
            return str(csv_path)

        except Exception as e:
            logger.error(f"Failed to export metrics to CSV: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Health check for monitoring service."""
        return {
            "healthy": self._monitoring_active,
            "monitoring_active": self._monitoring_active,
            "services_monitored": len(self._service_health),
            "total_metrics_collected": sum(len(metrics) for metrics in self._metrics_history.values()),
            "active_alerts": len(self._active_alerts),
            "last_collection": datetime.now().isoformat() if self._metrics_history else None
        }

    async def cleanup(self) -> None:
        """Clean up monitoring service resources."""
        try:
            await self.stop_monitoring()

            # Clear all data
            self._metrics_history.clear()
            self._service_health.clear()
            self._system_resources.clear()
            self._active_alerts.clear()

            logger.info("Performance monitoring service cleaned up successfully")

        except Exception as e:
            logger.error(f"Monitoring cleanup failed: {e}")


# Global monitoring service instance
_monitoring_service: Optional[PerformanceMonitoringService] = None


async def get_monitoring_service(**kwargs) -> PerformanceMonitoringService:
    """Get singleton performance monitoring service."""
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = PerformanceMonitoringService(**kwargs)
        await _monitoring_service.initialize()

    return _monitoring_service


# Export main classes
__all__ = [
    "PerformanceMonitoringService",
    "PerformanceMetric",
    "ServiceHealthStatus",
    "SystemResourceMetrics",
    "PerformanceAlert",
    "get_monitoring_service"
]