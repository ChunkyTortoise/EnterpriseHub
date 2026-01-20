"""
Production Monitoring Service - Enterprise Observability and Alerting

This service provides comprehensive production monitoring for Jorge's Revenue Acceleration Platform:

- Application performance monitoring (APM)
- Business metrics tracking and KPI dashboards
- System health and uptime monitoring
- AI model performance tracking
- Revenue attribution monitoring
- Real-time alerting and incident management
- SLA compliance tracking

Critical Missing Component: 10% monitoring implementation identified in audit.
This service enables validation of 99.9% uptime and performance claims.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import psutil
import aiohttp
from decimal import Decimal

from ghl_real_estate_ai.services.database_service import get_database, DatabaseService
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class MetricType(Enum):
    """Types of metrics tracked"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"

@dataclass
class Metric:
    """Performance metric data point"""
    name: str
    value: Union[float, int]
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None
    unit: Optional[str] = None

@dataclass
class Alert:
    """Alert/incident data"""
    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    service: str
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    triggered_at: datetime = None
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None

@dataclass
class ServiceHealth:
    """Service health status"""
    service_name: str
    status: ServiceStatus
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    availability_percentage: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class ProductionMonitoringService:
    """Production-ready monitoring and alerting service"""

    def __init__(self):
        self.cache = get_cache_service()
        self.db: Optional[DatabaseService] = None

        # Monitoring configuration
        self.metric_retention_days = 90
        self.health_check_interval = 30  # seconds
        self.performance_sample_rate = 1.0  # 100% sampling

        # Alert thresholds
        self.alert_thresholds = {
            # Performance Thresholds
            "response_time_p95_ms": {"high": 2000, "critical": 5000},
            "response_time_p99_ms": {"high": 5000, "critical": 10000},
            "error_rate_percentage": {"medium": 1.0, "high": 5.0, "critical": 10.0},
            "throughput_requests_per_second": {"medium": 10, "high": 5, "critical": 1},

            # Business Metrics Thresholds
            "lead_conversion_rate": {"medium": 2.0, "high": 1.5, "critical": 1.0},
            "daily_revenue": {"medium": 5000, "high": 2000, "critical": 1000},
            "ai_attribution_confidence": {"medium": 0.7, "high": 0.6, "critical": 0.5},

            # System Health Thresholds
            "cpu_usage_percentage": {"medium": 70, "high": 85, "critical": 95},
            "memory_usage_percentage": {"medium": 75, "high": 90, "critical": 95},
            "disk_usage_percentage": {"medium": 80, "high": 90, "critical": 95},
            "database_connections": {"medium": 15, "high": 18, "critical": 20},

            # AI Model Performance Thresholds
            "model_accuracy": {"medium": 0.85, "high": 0.80, "critical": 0.75},
            "model_latency_ms": {"medium": 200, "high": 500, "critical": 1000},
            "model_error_rate": {"medium": 0.02, "high": 0.05, "critical": 0.10}
        }

        # Service endpoints for health checks
        self.service_endpoints = {
            "claude_assistant": "http://localhost:8000/health/claude",
            "real_estate_pipeline": "http://localhost:8000/health/data_pipeline",
            "revenue_attribution": "http://localhost:8000/health/attribution",
            "autonomous_followup": "http://localhost:8000/health/followup",
            "behavioral_triggers": "http://localhost:8000/health/behavioral",
            "streamlit_dashboard": "http://localhost:8501/health",
            "database": "internal_check",
            "redis_cache": "internal_check"
        }

        # Active alerts
        self.active_alerts: Dict[str, Alert] = {}

        # Alert handlers
        self.alert_handlers: List[Callable] = []

        logger.info("Initialized Production Monitoring Service")

    async def initialize(self):
        """Initialize monitoring service"""
        self.db = await get_database()

        # Start background monitoring tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._performance_monitoring_loop())
        asyncio.create_task(self._business_metrics_loop())

        logger.info("Production Monitoring Service initialized and background tasks started")

    # ============================================================================
    # METRIC COLLECTION
    # ============================================================================

    async def record_metric(
        self,
        name: str,
        value: Union[float, int],
        metric_type: MetricType,
        tags: Dict[str, str] = None,
        unit: str = None
    ):
        """Record a performance metric"""

        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            tags=tags or {},
            unit=unit
        )

        # Store metric
        await self._store_metric(metric)

        # Check alert thresholds
        await self._check_alert_thresholds(metric)

        # Update real-time dashboards
        await self._update_realtime_dashboard(metric)

    async def record_response_time(
        self,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        method: str = "GET"
    ):
        """Record API response time"""

        tags = {
            "endpoint": endpoint,
            "status_code": str(status_code),
            "method": method,
            "status_class": f"{status_code // 100}xx"
        }

        await self.record_metric(
            "http_response_time",
            response_time_ms,
            MetricType.HISTOGRAM,
            tags=tags,
            unit="milliseconds"
        )

        # Track error rate
        is_error = status_code >= 400
        await self.record_metric(
            "http_request_total",
            1,
            MetricType.COUNTER,
            tags=tags
        )

        if is_error:
            await self.record_metric(
                "http_errors_total",
                1,
                MetricType.COUNTER,
                tags=tags
            )

    async def record_business_metric(
        self,
        metric_name: str,
        value: Union[float, int, Decimal],
        business_context: Dict[str, Any] = None
    ):
        """Record business/revenue metrics"""

        if isinstance(value, Decimal):
            value = float(value)

        tags = {"metric_category": "business"}
        if business_context:
            tags.update({k: str(v) for k, v in business_context.items()})

        await self.record_metric(
            f"business_{metric_name}",
            value,
            MetricType.GAUGE,
            tags=tags,
            unit=self._get_business_metric_unit(metric_name)
        )

    async def record_ai_model_performance(
        self,
        model_name: str,
        accuracy: float,
        latency_ms: float,
        predictions_count: int,
        error_count: int = 0
    ):
        """Record AI model performance metrics"""

        tags = {"model": model_name}

        # Accuracy
        await self.record_metric(
            "ai_model_accuracy",
            accuracy,
            MetricType.GAUGE,
            tags=tags,
            unit="ratio"
        )

        # Latency
        await self.record_metric(
            "ai_model_latency",
            latency_ms,
            MetricType.HISTOGRAM,
            tags=tags,
            unit="milliseconds"
        )

        # Throughput
        await self.record_metric(
            "ai_model_predictions",
            predictions_count,
            MetricType.COUNTER,
            tags=tags
        )

        # Error rate
        if predictions_count > 0:
            error_rate = error_count / predictions_count
            await self.record_metric(
                "ai_model_error_rate",
                error_rate,
                MetricType.GAUGE,
                tags=tags,
                unit="ratio"
            )

    async def record_revenue_attribution(
        self,
        attributed_revenue: Decimal,
        confidence: float,
        ai_system: str,
        conversion_id: str
    ):
        """Record revenue attribution metrics"""

        tags = {
            "ai_system": ai_system,
            "conversion_id": conversion_id
        }

        await self.record_metric(
            "revenue_attributed",
            float(attributed_revenue),
            MetricType.COUNTER,
            tags=tags,
            unit="dollars"
        )

        await self.record_metric(
            "attribution_confidence",
            confidence,
            MetricType.GAUGE,
            tags=tags,
            unit="ratio"
        )

    # ============================================================================
    # HEALTH MONITORING
    # ============================================================================

    async def check_service_health(self, service_name: str) -> ServiceHealth:
        """Check health of a specific service"""

        start_time = time.time()

        try:
            if service_name == "database":
                health_data = await self._check_database_health()
            elif service_name == "redis_cache":
                health_data = await self._check_cache_health()
            else:
                health_data = await self._check_http_service_health(service_name)

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            return ServiceHealth(
                service_name=service_name,
                status=health_data.get("status", ServiceStatus.UNHEALTHY),
                last_check=datetime.utcnow(),
                response_time_ms=response_time,
                error_rate=health_data.get("error_rate"),
                availability_percentage=health_data.get("availability_percentage"),
                details=health_data.get("details")
            )

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return ServiceHealth(
                service_name=service_name,
                status=ServiceStatus.DOWN,
                last_check=datetime.utcnow(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )

    async def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        if not self.db:
            await self.initialize()

        health_data = await self.db.health_check()

        if health_data.get("status") == "healthy":
            status = ServiceStatus.HEALTHY
        else:
            status = ServiceStatus.UNHEALTHY

        return {
            "status": status,
            "details": health_data
        }

    async def _check_cache_health(self) -> Dict[str, Any]:
        """Check Redis cache health"""
        try:
            # Test cache operation
            test_key = "health_check_test"
            await self.cache.set(test_key, "ok", ttl=10)
            result = await self.cache.get(test_key)

            if result == "ok":
                return {
                    "status": ServiceStatus.HEALTHY,
                    "details": {"cache_responsive": True}
                }
            else:
                return {
                    "status": ServiceStatus.UNHEALTHY,
                    "details": {"cache_responsive": False, "error": "Cache read/write failed"}
                }

        except Exception as e:
            return {
                "status": ServiceStatus.DOWN,
                "details": {"error": str(e)}
            }

    async def _check_http_service_health(self, service_name: str) -> Dict[str, Any]:
        """Check HTTP service health"""
        endpoint = self.service_endpoints.get(service_name)
        if not endpoint:
            return {
                "status": ServiceStatus.UNHEALTHY,
                "details": {"error": "No health check endpoint configured"}
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(endpoint, timeout=5) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return {
                            "status": ServiceStatus.HEALTHY,
                            "details": response_data
                        }
                    else:
                        return {
                            "status": ServiceStatus.DEGRADED,
                            "details": {"http_status": response.status}
                        }

        except asyncio.TimeoutError:
            return {
                "status": ServiceStatus.DOWN,
                "details": {"error": "Health check timeout"}
            }
        except Exception as e:
            return {
                "status": ServiceStatus.DOWN,
                "details": {"error": str(e)}
            }

    async def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system health overview"""

        # Check all services
        service_health = {}
        for service_name in self.service_endpoints.keys():
            health = await self.check_service_health(service_name)
            service_health[service_name] = asdict(health)

        # System resource usage
        system_metrics = await self._get_system_metrics()

        # Recent performance metrics
        performance_summary = await self._get_performance_summary()

        # Active alerts
        active_alerts = [asdict(alert) for alert in self.active_alerts.values()]

        # Calculate overall health score
        healthy_services = sum(1 for h in service_health.values() if h["status"] == "healthy")
        total_services = len(service_health)
        overall_health_score = (healthy_services / total_services) * 100 if total_services > 0 else 0

        return {
            "overall_health_score": overall_health_score,
            "overall_status": self._calculate_overall_status(service_health),
            "service_health": service_health,
            "system_metrics": system_metrics,
            "performance_summary": performance_summary,
            "active_alerts": active_alerts,
            "last_updated": datetime.utcnow().isoformat()
        }

    # ============================================================================
    # ALERTING SYSTEM
    # ============================================================================

    async def _check_alert_thresholds(self, metric: Metric):
        """Check if metric value exceeds alert thresholds"""

        threshold_config = self.alert_thresholds.get(metric.name)
        if not threshold_config:
            return

        current_value = metric.value
        alert_triggered = False
        severity = None

        # Check thresholds in order of severity
        for level in ["critical", "high", "medium", "low"]:
            if level in threshold_config:
                threshold = threshold_config[level]

                # Handle different comparison types
                if metric.name.endswith("_percentage") or metric.name.endswith("_rate"):
                    # Higher values are bad for rates and percentages
                    if current_value >= threshold:
                        severity = AlertSeverity(level)
                        alert_triggered = True
                        break
                elif "latency" in metric.name or "response_time" in metric.name:
                    # Higher values are bad for latency/response time
                    if current_value >= threshold:
                        severity = AlertSeverity(level)
                        alert_triggered = True
                        break
                elif "accuracy" in metric.name or "confidence" in metric.name:
                    # Lower values are bad for accuracy/confidence
                    if current_value <= threshold:
                        severity = AlertSeverity(level)
                        alert_triggered = True
                        break

        if alert_triggered:
            await self._trigger_alert(
                metric_name=metric.name,
                current_value=current_value,
                threshold_value=threshold_config.get(severity.value),
                severity=severity,
                metric_tags=metric.tags
            )
        else:
            # Check if we should resolve any existing alerts for this metric
            await self._check_alert_resolution(metric)

    async def _trigger_alert(
        self,
        metric_name: str,
        current_value: float,
        threshold_value: float,
        severity: AlertSeverity,
        metric_tags: Dict[str, str] = None
    ):
        """Trigger an alert"""

        alert_id = f"alert_{metric_name}_{int(time.time())}"
        service = metric_tags.get("service", "unknown") if metric_tags else "unknown"

        alert = Alert(
            alert_id=alert_id,
            severity=severity,
            title=f"{metric_name.replace('_', ' ').title()} Threshold Exceeded",
            description=f"{metric_name} value {current_value} exceeds {severity.value} threshold {threshold_value}",
            service=service,
            metric_name=metric_name,
            threshold_value=threshold_value,
            current_value=current_value,
            triggered_at=datetime.utcnow()
        )

        # Store alert
        self.active_alerts[alert_id] = alert
        await self._store_alert(alert)

        # Execute alert handlers
        await self._execute_alert_handlers(alert)

        logger.warning(f"ALERT TRIGGERED: {alert.title} - {alert.description}")

    async def _check_alert_resolution(self, metric: Metric):
        """Check if any alerts can be resolved based on current metric value"""

        alerts_to_resolve = []

        for alert in self.active_alerts.values():
            if alert.metric_name == metric.name and not alert.resolved_at:
                threshold_config = self.alert_thresholds.get(metric.name, {})
                threshold_value = threshold_config.get(alert.severity.value)

                if threshold_value:
                    # Check if metric has returned to healthy range
                    is_resolved = False

                    if metric.name.endswith("_percentage") or metric.name.endswith("_rate"):
                        is_resolved = metric.value < threshold_value * 0.9  # 10% buffer
                    elif "latency" in metric.name or "response_time" in metric.name:
                        is_resolved = metric.value < threshold_value * 0.9
                    elif "accuracy" in metric.name or "confidence" in metric.name:
                        is_resolved = metric.value > threshold_value * 1.1  # 10% buffer above threshold

                    if is_resolved:
                        alerts_to_resolve.append(alert.alert_id)

        # Resolve alerts
        for alert_id in alerts_to_resolve:
            await self.resolve_alert(alert_id, auto_resolved=True)

    async def resolve_alert(self, alert_id: str, resolved_by: str = "system", auto_resolved: bool = False):
        """Resolve an active alert"""

        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.utcnow()

            # Remove from active alerts
            del self.active_alerts[alert_id]

            # Update stored alert
            await self._update_alert_status(alert)

            logger.info(f"Alert resolved: {alert.title} - Resolved by: {resolved_by}")

    async def add_alert_handler(self, handler: Callable):
        """Add custom alert handler"""
        self.alert_handlers.append(handler)

    async def _execute_alert_handlers(self, alert: Alert):
        """Execute all registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler failed: {e}")

    # ============================================================================
    # BACKGROUND MONITORING LOOPS
    # ============================================================================

    async def _health_check_loop(self):
        """Background loop for health checks"""
        while True:
            try:
                # Check all services
                for service_name in self.service_endpoints.keys():
                    health = await self.check_service_health(service_name)

                    # Record health metrics
                    status_value = 1 if health.status == ServiceStatus.HEALTHY else 0
                    await self.record_metric(
                        "service_health",
                        status_value,
                        MetricType.GAUGE,
                        tags={"service": service_name}
                    )

                    if health.response_time_ms:
                        await self.record_metric(
                            "service_response_time",
                            health.response_time_ms,
                            MetricType.HISTOGRAM,
                            tags={"service": service_name},
                            unit="milliseconds"
                        )

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on errors

    async def _performance_monitoring_loop(self):
        """Background loop for performance monitoring"""
        while True:
            try:
                # Collect system metrics
                system_metrics = await self._get_system_metrics()

                for metric_name, value in system_metrics.items():
                    await self.record_metric(
                        metric_name,
                        value,
                        MetricType.GAUGE,
                        tags={"component": "system"}
                    )

                await asyncio.sleep(60)  # Collect system metrics every minute

            except Exception as e:
                logger.error(f"Performance monitoring loop error: {e}")
                await asyncio.sleep(60)

    async def _business_metrics_loop(self):
        """Background loop for business metrics collection"""
        while True:
            try:
                # Collect business metrics
                business_metrics = await self._get_business_metrics()

                for metric_name, value in business_metrics.items():
                    await self.record_business_metric(metric_name, value)

                await asyncio.sleep(300)  # Collect business metrics every 5 minutes

            except Exception as e:
                logger.error(f"Business metrics loop error: {e}")
                await asyncio.sleep(300)

    # ============================================================================
    # METRIC STORAGE AND RETRIEVAL
    # ============================================================================

    async def _store_metric(self, metric: Metric):
        """Store metric in database and cache"""

        # Store in cache for real-time access
        cache_key = f"metric:{metric.name}:{int(metric.timestamp.timestamp())}"
        await self.cache.set(cache_key, asdict(metric), ttl=86400)  # 24 hours

        # Store aggregated metrics in database
        await self._store_aggregated_metric(metric)

        # Update recent metrics cache
        await self._update_recent_metrics_cache(metric)

    async def _store_aggregated_metric(self, metric: Metric):
        """Store aggregated metric in database for long-term storage"""
        if not self.db:
            await self.initialize()

        # This would require a metrics table - for now store in communication logs
        comm_data = {
            "lead_id": "system",
            "channel": "monitoring",
            "direction": "metric",
            "content": f"Metric: {metric.name} = {metric.value}",
            "status": "recorded",
            "metadata": {
                "metric_data": asdict(metric),
                "metric_name": metric.name,
                "metric_value": metric.value,
                "metric_type": metric.metric_type.value,
                "tags": metric.tags
            }
        }

        await self.db.log_communication(comm_data)

    async def _update_recent_metrics_cache(self, metric: Metric):
        """Update cache with recent metrics for dashboard"""
        cache_key = f"recent_metrics:{metric.name}"
        recent_metrics = await self.cache.get(cache_key) or []

        # Add new metric
        recent_metrics.append({
            "timestamp": metric.timestamp.isoformat(),
            "value": metric.value,
            "tags": metric.tags
        })

        # Keep last 100 data points
        if len(recent_metrics) > 100:
            recent_metrics = recent_metrics[-100:]

        await self.cache.set(cache_key, recent_metrics, ttl=3600)  # 1 hour

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        if not self.db:
            await self.initialize()

        comm_data = {
            "lead_id": "system",
            "channel": "alerting",
            "direction": "alert",
            "content": f"Alert: {alert.title}",
            "status": "triggered",
            "metadata": {
                "alert_data": asdict(alert),
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "service": alert.service
            }
        }

        await self.db.log_communication(comm_data)

    async def _update_alert_status(self, alert: Alert):
        """Update alert status in database"""
        # In a full implementation, you'd update the alert record
        # For now, log the resolution
        if not self.db:
            await self.initialize()

        comm_data = {
            "lead_id": "system",
            "channel": "alerting",
            "direction": "alert_resolved",
            "content": f"Alert Resolved: {alert.title}",
            "status": "resolved",
            "metadata": {
                "alert_id": alert.alert_id,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            }
        }

        await self.db.log_communication(comm_data)

    # ============================================================================
    # METRICS CALCULATION AND ANALYSIS
    # ============================================================================

    async def _get_system_metrics(self) -> Dict[str, float]:
        """Get current system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            # Network I/O
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv

            return {
                "cpu_usage_percentage": cpu_percent,
                "memory_usage_percentage": memory_percent,
                "disk_usage_percentage": disk_percent,
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_received": network_bytes_recv
            }

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {}

    async def _get_business_metrics(self) -> Dict[str, float]:
        """Get current business KPI metrics"""
        try:
            # This would query your business data
            # For now, return sample metrics
            return {
                "daily_revenue": 15000.0,
                "daily_conversions": 12,
                "lead_conversion_rate": 3.2,
                "ai_attribution_percentage": 68.5,
                "customer_satisfaction_score": 4.7
            }

        except Exception as e:
            logger.error(f"Failed to get business metrics: {e}")
            return {}

    async def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard"""
        # Get recent metrics from cache
        try:
            performance_metrics = ["response_time_p95_ms", "error_rate_percentage", "throughput_requests_per_second"]
            summary = {}

            for metric_name in performance_metrics:
                recent_data = await self.cache.get(f"recent_metrics:{metric_name}")
                if recent_data:
                    latest_value = recent_data[-1]["value"]
                    summary[metric_name] = latest_value

            return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {}

    async def _update_realtime_dashboard(self, metric: Metric):
        """Update real-time dashboard with new metric"""
        # Push metric to dashboard cache
        dashboard_key = "realtime_dashboard"
        dashboard_data = await self.cache.get(dashboard_key) or {}

        dashboard_data[metric.name] = {
            "value": metric.value,
            "timestamp": metric.timestamp.isoformat(),
            "unit": metric.unit,
            "tags": metric.tags
        }

        await self.cache.set(dashboard_key, dashboard_data, ttl=300)  # 5 minutes

    def _calculate_overall_status(self, service_health: Dict[str, Any]) -> str:
        """Calculate overall system status from individual service health"""
        if not service_health:
            return "unknown"

        status_counts = {}
        for health_data in service_health.values():
            status = health_data["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        total_services = len(service_health)

        # Determine overall status
        if status_counts.get("down", 0) > 0:
            return "down"
        elif status_counts.get("unhealthy", 0) > total_services * 0.3:  # >30% unhealthy
            return "unhealthy"
        elif status_counts.get("degraded", 0) > total_services * 0.5:  # >50% degraded
            return "degraded"
        else:
            return "healthy"

    def _get_business_metric_unit(self, metric_name: str) -> str:
        """Get appropriate unit for business metric"""
        if "revenue" in metric_name or "cost" in metric_name:
            return "dollars"
        elif "rate" in metric_name or "percentage" in metric_name:
            return "percentage"
        elif "score" in metric_name:
            return "score"
        elif "count" in metric_name:
            return "count"
        else:
            return "value"

# ============================================================================
# SERVICE FACTORY AND HELPERS
# ============================================================================

_monitoring_service: Optional[ProductionMonitoringService] = None

async def get_monitoring_service() -> ProductionMonitoringService:
    """Get global monitoring service instance"""
    global _monitoring_service

    if _monitoring_service is None:
        _monitoring_service = ProductionMonitoringService()
        await _monitoring_service.initialize()

    return _monitoring_service

# Convenience functions for common monitoring operations
async def track_performance(endpoint: str, response_time_ms: float, status_code: int):
    """Convenience function to track API performance"""
    service = await get_monitoring_service()
    await service.record_response_time(endpoint, response_time_ms, status_code)

async def track_business_kpi(metric_name: str, value: Union[float, Decimal]):
    """Convenience function to track business KPIs"""
    service = await get_monitoring_service()
    await service.record_business_metric(metric_name, value)

async def track_ai_performance(model_name: str, accuracy: float, latency_ms: float, predictions: int):
    """Convenience function to track AI model performance"""
    service = await get_monitoring_service()
    await service.record_ai_model_performance(model_name, accuracy, latency_ms, predictions)

async def get_system_health() -> Dict[str, Any]:
    """Convenience function to get system health overview"""
    service = await get_monitoring_service()
    return await service.get_system_overview()

# Performance monitoring decorator
def monitor_performance(endpoint_name: str = None):
    """Decorator to automatically monitor function performance"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint = endpoint_name or func.__name__

            try:
                result = await func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000
                await track_performance(endpoint, response_time, 200)
                return result

            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                await track_performance(endpoint, response_time, 500)
                raise

        return wrapper
    return decorator

if __name__ == "__main__":
    async def test_monitoring_service():
        """Test monitoring service functionality"""
        service = ProductionMonitoringService()
        await service.initialize()

        # Test metric recording
        await service.record_response_time("api/leads", 150.0, 200)
        await service.record_business_metric("daily_revenue", 12500.00)
        await service.record_ai_model_performance("neural_property_matcher", 0.92, 89.5, 100, 2)

        # Test health checks
        health_overview = await service.get_system_overview()
        print(f"System Health Overview: {health_overview}")

        # Test alerting
        await service.record_metric(
            "response_time_p95_ms",
            6000,  # Above critical threshold
            MetricType.GAUGE
        )

        print("Monitoring service test completed")

    asyncio.run(test_monitoring_service())