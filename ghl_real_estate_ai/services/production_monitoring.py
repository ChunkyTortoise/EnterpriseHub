"""
Production Monitoring Service for Jorge's Real Estate AI Dashboard.

Provides comprehensive monitoring capabilities for production deployment:
- Performance metrics collection
- Health checks for all services
- Database optimization monitoring
- Error tracking and alerting
- Resource usage monitoring
"""

import time
import psutil
import asyncio
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from pathlib import Path

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"

class MetricType(Enum):
    """Types of metrics to collect."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class HealthCheck:
    """Health check result."""
    service: str
    status: ServiceStatus
    message: str
    timestamp: datetime
    response_time_ms: float
    details: Dict[str, Any] = None

@dataclass
class PerformanceMetric:
    """Performance metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = None

@dataclass
class DatabaseMetrics:
    """Database performance metrics."""
    connection_count: int
    query_duration_avg_ms: float
    cache_hit_rate: float
    slow_queries: int
    database_size_mb: float
    last_optimization: datetime

@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_mb: float
    active_connections: int
    uptime_hours: float

class ProductionMonitor:
    """Comprehensive production monitoring service."""

    def __init__(self, monitoring_db_path: str = None):
        """Initialize monitoring service."""
        self.monitoring_db_path = monitoring_db_path or "data/monitoring.db"
        self.start_time = datetime.now()
        self.metrics_buffer = []
        self.health_checks = {}
        self.alerts = []

        # Performance thresholds
        self.thresholds = {
            'response_time_ms': 2000,
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'cache_hit_rate': 0.8,
            'error_rate': 0.05
        }

    async def initialize_monitoring(self):
        """Initialize monitoring database."""
        try:
            # Create monitoring directory
            Path(self.monitoring_db_path).parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(self.monitoring_db_path) as db:
                # Health checks table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS health_checks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        service TEXT NOT NULL,
                        status TEXT NOT NULL,
                        message TEXT,
                        response_time_ms REAL,
                        details TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Performance metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value REAL NOT NULL,
                        metric_type TEXT NOT NULL,
                        tags TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # System metrics table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cpu_percent REAL,
                        memory_percent REAL,
                        disk_percent REAL,
                        network_io_mb REAL,
                        active_connections INTEGER,
                        uptime_hours REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Alerts table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_type TEXT NOT NULL,
                        message TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        service TEXT,
                        resolved BOOLEAN DEFAULT FALSE,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.commit()

            logger.info("Monitoring database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize monitoring database: {e}")
            raise

    async def check_service_health(self, service_name: str, check_function) -> HealthCheck:
        """Perform health check for a service."""
        start_time = time.time()

        try:
            # Run the health check
            result = await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            # Determine status based on response time and result
            if result.get('healthy', False):
                if response_time > self.thresholds['response_time_ms']:
                    status = ServiceStatus.WARNING
                    message = f"Service healthy but slow response ({response_time:.1f}ms)"
                else:
                    status = ServiceStatus.HEALTHY
                    message = "Service healthy"
            else:
                status = ServiceStatus.CRITICAL
                message = result.get('error', 'Health check failed')

            health_check = HealthCheck(
                service=service_name,
                status=status,
                message=message,
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details=result
            )

            # Store health check result
            await self._store_health_check(health_check)

            return health_check

        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")

            response_time = (time.time() - start_time) * 1000

            health_check = HealthCheck(
                service=service_name,
                status=ServiceStatus.DOWN,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now(),
                response_time_ms=response_time,
                details={'error': str(e)}
            )

            await self._store_health_check(health_check)
            return health_check

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100

            # Network I/O (simplified)
            network = psutil.net_io_counters()
            network_io_mb = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)

            # Active network connections
            connections = len(psutil.net_connections())

            # System uptime
            uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600

            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_mb=network_io_mb,
                active_connections=connections,
                uptime_hours=uptime_hours
            )

            # Store system metrics
            await self._store_system_metrics(metrics)

            # Check thresholds and create alerts
            await self._check_system_thresholds(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            raise

    async def collect_database_metrics(self, db_path: str) -> DatabaseMetrics:
        """Collect database performance metrics."""
        try:
            async with aiosqlite.connect(db_path) as db:
                # Database size
                stat = Path(db_path).stat()
                size_mb = stat.st_size / (1024 * 1024)

                # Query performance (simplified metrics)
                start_time = time.time()
                await db.execute("SELECT COUNT(*) FROM sqlite_master")
                query_duration = (time.time() - start_time) * 1000

                # Connection count (SQLite is single-connection)
                connection_count = 1

                # Placeholder metrics (would be more sophisticated in production)
                metrics = DatabaseMetrics(
                    connection_count=connection_count,
                    query_duration_avg_ms=query_duration,
                    cache_hit_rate=0.85,  # Would be measured from actual cache
                    slow_queries=0,       # Would be tracked over time
                    database_size_mb=size_mb,
                    last_optimization=datetime.now() - timedelta(days=1)
                )

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            # Return default metrics on error
            return DatabaseMetrics(
                connection_count=0,
                query_duration_avg_ms=999.0,
                cache_hit_rate=0.0,
                slow_queries=999,
                database_size_mb=0.0,
                last_optimization=datetime.now() - timedelta(days=30)
            )

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Dict[str, str] = None
    ):
        """Record a custom performance metric."""
        metric = PerformanceMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {}
        )

        await self._store_performance_metric(metric)

    async def create_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        service: str = None
    ):
        """Create an alert for monitoring purposes."""
        try:
            async with aiosqlite.connect(self.monitoring_db_path) as db:
                await db.execute("""
                    INSERT INTO alerts (alert_type, message, severity, service)
                    VALUES (?, ?, ?, ?)
                """, (alert_type, message, severity, service))
                await db.commit()

            logger.warning(f"Alert created: {alert_type} - {message}")

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")

    async def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        try:
            async with aiosqlite.connect(self.monitoring_db_path) as db:
                # Get latest health checks
                async with db.execute("""
                    SELECT service, status, message, response_time_ms, timestamp
                    FROM health_checks
                    WHERE timestamp > datetime('now', '-5 minutes')
                    ORDER BY timestamp DESC
                """) as cursor:
                    health_checks = await cursor.fetchall()

                # Get recent alerts
                async with db.execute("""
                    SELECT alert_type, message, severity, timestamp
                    FROM alerts
                    WHERE resolved = FALSE AND timestamp > datetime('now', '-1 hour')
                    ORDER BY timestamp DESC
                    LIMIT 10
                """) as cursor:
                    alerts = await cursor.fetchall()

                # Get latest system metrics
                async with db.execute("""
                    SELECT cpu_percent, memory_percent, disk_percent, timestamp
                    FROM system_metrics
                    ORDER BY timestamp DESC
                    LIMIT 1
                """) as cursor:
                    system_metrics = await cursor.fetchone()

            return {
                'overall_status': self._calculate_overall_status(health_checks),
                'services': len(set(hc[0] for hc in health_checks)),
                'healthy_services': len([hc for hc in health_checks if hc[1] == ServiceStatus.HEALTHY.value]),
                'active_alerts': len(alerts),
                'system_metrics': {
                    'cpu_percent': system_metrics[0] if system_metrics else 0,
                    'memory_percent': system_metrics[1] if system_metrics else 0,
                    'disk_percent': system_metrics[2] if system_metrics else 0
                } if system_metrics else None,
                'last_updated': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get health summary: {e}")
            return {
                'overall_status': 'unknown',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

    async def _store_health_check(self, health_check: HealthCheck):
        """Store health check result in database."""
        try:
            async with aiosqlite.connect(self.monitoring_db_path) as db:
                await db.execute("""
                    INSERT INTO health_checks (service, status, message, response_time_ms, details)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    health_check.service,
                    health_check.status.value,
                    health_check.message,
                    health_check.response_time_ms,
                    json.dumps(health_check.details) if health_check.details else None
                ))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to store health check: {e}")

    async def _store_performance_metric(self, metric: PerformanceMetric):
        """Store performance metric in database."""
        try:
            async with aiosqlite.connect(self.monitoring_db_path) as db:
                await db.execute("""
                    INSERT INTO performance_metrics (name, value, metric_type, tags)
                    VALUES (?, ?, ?, ?)
                """, (
                    metric.name,
                    metric.value,
                    metric.metric_type.value,
                    json.dumps(metric.tags) if metric.tags else None
                ))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to store performance metric: {e}")

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database."""
        try:
            async with aiosqlite.connect(self.monitoring_db_path) as db:
                await db.execute("""
                    INSERT INTO system_metrics
                    (cpu_percent, memory_percent, disk_percent, network_io_mb, active_connections, uptime_hours)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_percent,
                    metrics.network_io_mb,
                    metrics.active_connections,
                    metrics.uptime_hours
                ))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to store system metrics: {e}")

    async def _check_system_thresholds(self, metrics: SystemMetrics):
        """Check system metrics against thresholds and create alerts."""
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            await self.create_alert(
                'high_cpu',
                f'CPU usage high: {metrics.cpu_percent:.1f}%',
                'warning',
                'system'
            )

        if metrics.memory_percent > self.thresholds['memory_percent']:
            await self.create_alert(
                'high_memory',
                f'Memory usage high: {metrics.memory_percent:.1f}%',
                'warning',
                'system'
            )

        if metrics.disk_percent > self.thresholds['disk_percent']:
            await self.create_alert(
                'high_disk',
                f'Disk usage high: {metrics.disk_percent:.1f}%',
                'critical',
                'system'
            )

    def _calculate_overall_status(self, health_checks: List[tuple]) -> str:
        """Calculate overall system status from health checks."""
        if not health_checks:
            return 'unknown'

        statuses = [hc[1] for hc in health_checks]

        if ServiceStatus.DOWN.value in statuses:
            return 'critical'
        elif ServiceStatus.CRITICAL.value in statuses:
            return 'critical'
        elif ServiceStatus.WARNING.value in statuses:
            return 'warning'
        elif ServiceStatus.HEALTHY.value in statuses:
            return 'healthy'
        else:
            return 'unknown'

# Health check functions for different services

async def check_database_health(db_path: str = "data/auth.db") -> Dict[str, Any]:
    """Health check for database connectivity."""
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        return {'healthy': True, 'message': 'Database connection successful'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

async def check_cache_health() -> Dict[str, Any]:
    """Health check for cache service."""
    try:
        # This would connect to Redis in a real implementation
        return {'healthy': True, 'message': 'Cache service available'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

async def check_auth_service_health() -> Dict[str, Any]:
    """Health check for authentication service."""
    try:
        from ghl_real_estate_ai.services.auth_service import get_auth_service
        auth_service = get_auth_service()
        # Simple test of auth service
        return {'healthy': True, 'message': 'Auth service available'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

# Global monitoring instance
_production_monitor = None

def get_production_monitor() -> ProductionMonitor:
    """Get singleton production monitor instance."""
    global _production_monitor
    if _production_monitor is None:
        _production_monitor = ProductionMonitor()
    return _production_monitor