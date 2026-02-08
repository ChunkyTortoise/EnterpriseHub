"""
Service 6 Enhanced Lead Recovery Engine - Monitoring Orchestrator
Unified production monitoring infrastructure orchestration and management.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .service6_alerting_engine import AlertLevel, Service6AlertingEngine
from .service6_health_dashboard import Service6HealthDashboard
from .service6_metrics_collector import Service6MetricsCollector
from .service6_system_health_checker import HealthCheckStatus, Service6SystemHealthChecker

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfiguration:
    """Configuration for monitoring infrastructure."""

    metrics_collection_enabled: bool = True
    health_checks_enabled: bool = True
    alerting_enabled: bool = True
    dashboard_enabled: bool = True

    # Collection intervals (seconds)
    metrics_collection_interval: int = 30
    health_check_interval: int = 60

    # Performance settings
    max_concurrent_checks: int = 10
    metric_retention_days: int = 7

    # Alert settings
    alert_cooldown_minutes: int = 5
    max_alerts_per_hour: int = 20


class Service6MonitoringOrchestrator:
    """
    Production monitoring orchestrator for Service 6 Enhanced Lead Recovery Engine.
    Coordinates metrics collection, health checking, alerting, and dashboard services.
    """

    def __init__(self, config: Optional[MonitoringConfiguration] = None):
        self.config = config or MonitoringConfiguration()

        # Initialize monitoring components
        self.metrics_collector = Service6MetricsCollector()
        self.alerting_engine = Service6AlertingEngine()
        self.health_checker = Service6SystemHealthChecker()
        self.dashboard = Service6HealthDashboard()

        # State management
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._startup_time = None
        self._shutdown_event = asyncio.Event()

    async def start_monitoring(self) -> None:
        """Start comprehensive production monitoring infrastructure."""
        if self._running:
            logger.warning("Monitoring infrastructure already running")
            return

        logger.info("🚀 Starting Service 6 production monitoring infrastructure")
        self._startup_time = datetime.utcnow()

        try:
            # Pre-flight validation
            await self._validate_infrastructure()

            # Initialize components
            await self._initialize_components()

            # Start monitoring services
            if self.config.metrics_collection_enabled:
                await self._start_metrics_collection()

            if self.config.health_checks_enabled:
                await self._start_health_monitoring()

            if self.config.alerting_enabled:
                await self._start_alerting_service()

            # Set up signal handlers for graceful shutdown
            self._setup_signal_handlers()

            self._running = True

            # Send startup notification
            await self._send_startup_notification()

            logger.info("✅ Service 6 monitoring infrastructure started successfully")
            logger.info(f"   • Metrics collection: {'✅' if self.config.metrics_collection_enabled else '❌'}")
            logger.info(f"   • Health monitoring: {'✅' if self.config.health_checks_enabled else '❌'}")
            logger.info(f"   • Alert system: {'✅' if self.config.alerting_enabled else '❌'}")
            logger.info(f"   • Dashboard: {'✅' if self.config.dashboard_enabled else '❌'}")

        except Exception as e:
            logger.error(f"Failed to start monitoring infrastructure: {e}")
            await self.shutdown_monitoring()
            raise

    async def shutdown_monitoring(self) -> None:
        """Gracefully shutdown monitoring infrastructure."""
        if not self._running:
            logger.warning("Monitoring infrastructure not running")
            return

        logger.info("🛑 Shutting down Service 6 monitoring infrastructure")

        try:
            # Signal shutdown to all components
            self._shutdown_event.set()

            # Cancel all monitoring tasks
            for task in self._tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete with timeout
            if self._tasks:
                await asyncio.wait_for(asyncio.gather(*self._tasks, return_exceptions=True), timeout=30.0)

            # Shutdown components
            await self._shutdown_components()

            # Send shutdown notification
            await self._send_shutdown_notification()

            self._running = False
            self._tasks.clear()

            logger.info("✅ Service 6 monitoring infrastructure shutdown complete")

        except asyncio.TimeoutError:
            logger.warning("Monitoring shutdown timeout - forcing termination")
        except Exception as e:
            logger.error(f"Error during monitoring shutdown: {e}")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring infrastructure status."""
        if not self._running:
            return {
                "status": "stopped",
                "uptime_seconds": 0,
                "components": {
                    "metrics_collector": "stopped",
                    "health_checker": "stopped",
                    "alerting_engine": "stopped",
                    "dashboard": "stopped",
                },
            }

        uptime_seconds = (datetime.utcnow() - self._startup_time).total_seconds()

        # Get component statuses
        component_statuses = await self._get_component_statuses()

        return {
            "status": "running",
            "uptime_seconds": uptime_seconds,
            "startup_time": self._startup_time.isoformat(),
            "configuration": {
                "metrics_enabled": self.config.metrics_collection_enabled,
                "health_checks_enabled": self.config.health_checks_enabled,
                "alerting_enabled": self.config.alerting_enabled,
                "dashboard_enabled": self.config.dashboard_enabled,
            },
            "components": component_statuses,
            "active_tasks": len([t for t in self._tasks if not t.done()]),
            "total_tasks": len(self._tasks),
        }

    async def trigger_comprehensive_health_check(self) -> Dict[str, Any]:
        """Trigger immediate comprehensive health check."""
        logger.info("Triggering manual comprehensive health check")

        try:
            health_report = await self.health_checker.run_comprehensive_health_check()

            # Convert to serializable format
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": health_report.overall_status.value,
                "total_checks": health_report.total_checks,
                "passed_checks": health_report.passed_checks,
                "failed_checks": health_report.failed_checks,
                "warning_checks": health_report.warning_checks,
                "check_duration_seconds": health_report.check_duration_seconds,
                "recovery_actions_triggered": health_report.recovery_actions_triggered,
                "critical_issues": [
                    {"check_name": check.check_name, "status": check.status.value, "message": check.message}
                    for check in health_report.critical_checks
                    if check.status != HealthCheckStatus.PASS
                ],
            }

        except Exception as e:
            logger.error(f"Manual health check failed: {e}")
            return {"timestamp": datetime.utcnow().isoformat(), "overall_status": "error", "error_message": str(e)}

    async def _validate_infrastructure(self) -> None:
        """Validate infrastructure prerequisites before starting monitoring."""
        logger.info("Validating monitoring infrastructure prerequisites")

        # Validate database connectivity
        try:
            from ..services.database_service import DatabaseService

            db_service = DatabaseService()
            async with db_service.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            logger.info("✅ Database connectivity validated")
        except Exception as e:
            raise RuntimeError(f"Database validation failed: {e}")

        # Validate cache connectivity
        try:
            from ..services.cache_service import CacheService

            cache_service = CacheService()
            test_key = f"monitoring_test_{int(datetime.utcnow().timestamp())}"
            await cache_service.set(test_key, "test", ttl=10)
            await cache_service.delete(test_key)
            logger.info("✅ Cache connectivity validated")
        except Exception as e:
            raise RuntimeError(f"Cache validation failed: {e}")

        logger.info("✅ Infrastructure validation complete")

    async def _initialize_components(self) -> None:
        """Initialize all monitoring components."""
        logger.info("Initializing monitoring components")

        try:
            # Initialize metrics collector
            if self.config.metrics_collection_enabled:
                await self.metrics_collector.initialize()
                logger.info("✅ Metrics collector initialized")

            # Initialize alerting engine
            if self.config.alerting_enabled:
                await self.alerting_engine.initialize()
                logger.info("✅ Alerting engine initialized")

            logger.info("✅ Component initialization complete")

        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise

    async def _start_metrics_collection(self) -> None:
        """Start metrics collection service."""
        logger.info("Starting metrics collection service")

        async def metrics_collection_loop():
            """Continuous metrics collection loop."""
            while not self._shutdown_event.is_set():
                try:
                    await self.metrics_collector.collect_all_metrics()
                    await asyncio.sleep(self.config.metrics_collection_interval)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Metrics collection error: {e}")
                    await asyncio.sleep(10)  # Brief pause on error

        task = asyncio.create_task(metrics_collection_loop())
        self._tasks.append(task)

    async def _start_health_monitoring(self) -> None:
        """Start health monitoring service."""
        logger.info("Starting health monitoring service")

        async def health_monitoring_loop():
            """Continuous health monitoring loop."""
            while not self._shutdown_event.is_set():
                try:
                    health_report = await self.health_checker.run_comprehensive_health_check()

                    # Send alerts for critical issues
                    if health_report.failed_checks > 0:
                        await self._handle_health_failures(health_report)

                    await asyncio.sleep(self.config.health_check_interval)

                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    await asyncio.sleep(30)  # Longer pause on error

        task = asyncio.create_task(health_monitoring_loop())
        self._tasks.append(task)

    async def _start_alerting_service(self) -> None:
        """Start alerting service."""
        logger.info("Starting alerting service")

        # Alerting engine handles its own loop via background tasks
        # No additional loop needed here

    async def _handle_health_failures(self, health_report) -> None:
        """Handle health check failures by sending appropriate alerts."""
        try:
            if health_report.overall_status == HealthCheckStatus.FAIL:
                await self.alerting_engine.send_alert(
                    level=AlertLevel.CRITICAL,
                    title="Service 6 Critical System Failure",
                    message=f"System health check failed. {health_report.failed_checks} critical failures detected.",
                    details={
                        "failed_checks": health_report.failed_checks,
                        "warning_checks": health_report.warning_checks,
                        "recovery_actions": health_report.recovery_actions_triggered,
                    },
                )
            elif health_report.warning_checks > 2:
                await self.alerting_engine.send_alert(
                    level=AlertLevel.WARNING,
                    title="Service 6 Performance Degradation",
                    message=f"Multiple system warnings detected. {health_report.warning_checks} components showing degraded performance.",
                    details={"warning_checks": health_report.warning_checks},
                )

        except Exception as e:
            logger.error(f"Failed to send health failure alerts: {e}")

    async def _get_component_statuses(self) -> Dict[str, str]:
        """Get current status of all monitoring components."""
        statuses = {}

        try:
            # Check metrics collector
            if hasattr(self.metrics_collector, "_initialized"):
                statuses["metrics_collector"] = "running" if self.metrics_collector._initialized else "stopped"
            else:
                statuses["metrics_collector"] = "unknown"

            # Check health checker
            if hasattr(self.health_checker, "_running"):
                statuses["health_checker"] = "running" if self.health_checker._running else "stopped"
            else:
                statuses["health_checker"] = "unknown"

            # Check alerting engine
            if hasattr(self.alerting_engine, "_initialized"):
                statuses["alerting_engine"] = "running" if self.alerting_engine._initialized else "stopped"
            else:
                statuses["alerting_engine"] = "unknown"

            # Dashboard is stateless
            statuses["dashboard"] = "available" if self.config.dashboard_enabled else "disabled"

        except Exception as e:
            logger.error(f"Error getting component statuses: {e}")
            statuses = {
                "metrics_collector": "error",
                "health_checker": "error",
                "alerting_engine": "error",
                "dashboard": "error",
            }

        return statuses

    async def _shutdown_components(self) -> None:
        """Shutdown all monitoring components gracefully."""
        logger.info("Shutting down monitoring components")

        try:
            # Shutdown health checker
            if hasattr(self.health_checker, "stop_monitoring"):
                self.health_checker.stop_monitoring()

            # Shutdown metrics collector
            if hasattr(self.metrics_collector, "shutdown"):
                await self.metrics_collector.shutdown()

            # Shutdown alerting engine
            if hasattr(self.alerting_engine, "shutdown"):
                await self.alerting_engine.shutdown()

            logger.info("✅ Component shutdown complete")

        except Exception as e:
            logger.error(f"Component shutdown error: {e}")

    async def _send_startup_notification(self) -> None:
        """Send notification that monitoring infrastructure has started."""
        try:
            if self.config.alerting_enabled:
                await self.alerting_engine.send_alert(
                    level=AlertLevel.INFO,
                    title="Service 6 Monitoring Started",
                    message="Production monitoring infrastructure has been successfully started.",
                    details={"startup_time": self._startup_time.isoformat(), "configuration": self.config.__dict__},
                )
        except Exception as e:
            logger.error(f"Failed to send startup notification: {e}")

    async def _send_shutdown_notification(self) -> None:
        """Send notification that monitoring infrastructure is shutting down."""
        try:
            if self.config.alerting_enabled and self._running:
                uptime = (datetime.utcnow() - self._startup_time).total_seconds()
                await self.alerting_engine.send_alert(
                    level=AlertLevel.WARNING,
                    title="Service 6 Monitoring Shutdown",
                    message="Production monitoring infrastructure is shutting down.",
                    details={"uptime_seconds": uptime, "shutdown_time": datetime.utcnow().isoformat()},
                )
        except Exception as e:
            logger.error(f"Failed to send shutdown notification: {e}")

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown")
            # Create shutdown task
            asyncio.create_task(self.shutdown_monitoring())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    @asynccontextmanager
    async def monitoring_context(self):
        """Context manager for monitoring infrastructure lifecycle."""
        try:
            await self.start_monitoring()
            yield self
        finally:
            await self.shutdown_monitoring()


# Convenience function for quick monitoring setup
async def start_service6_monitoring(config: Optional[MonitoringConfiguration] = None) -> Service6MonitoringOrchestrator:
    """Start Service 6 monitoring infrastructure with default configuration."""
    orchestrator = Service6MonitoringOrchestrator(config)
    await orchestrator.start_monitoring()
    return orchestrator
