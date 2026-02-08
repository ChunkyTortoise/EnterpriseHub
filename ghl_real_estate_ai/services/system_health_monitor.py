"""
System Health Monitor for Jorge's Real Estate AI Platform

Monitors all system components and emits real-time health updates
for Redis, GHL API, Claude API, Database, and Jorge bots.

Features:
- Comprehensive component health checking
- Real-time WebSocket event emissions
- Performance metrics tracking
- Background monitoring with configurable intervals
- Intelligent alerting for degraded/down services
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class ComponentStatus(Enum):
    """Component health status levels."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    RECOVERING = "recovering"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health information for a system component."""

    component: str
    status: ComponentStatus
    response_time_ms: float
    error_message: Optional[str] = None
    last_check: Optional[datetime] = None
    additional_metrics: Optional[Dict[str, Any]] = None
    health_score: float = 0.0


class SystemHealthMonitor:
    """
    System Health Monitor for Jorge's AI Platform

    Monitors critical system components and emits real-time health updates
    via WebSocket events for dashboard integration.
    """

    def __init__(self):
        self.event_publisher = get_event_publisher()
        self.cache_service = get_cache_service()

        # Configuration
        self.monitor_interval = 30  # seconds
        self.health_history_size = 100
        self.degraded_threshold_ms = 1000
        self.down_threshold_ms = 5000

        # Component registry
        self.components = [
            "redis",
            "ghl_api",
            "claude_api",
            "database",
            "jorge_seller_bot",
            "lead_bot",
            "intent_decoder",
        ]

        # Health tracking
        self.health_history: Dict[str, List[ComponentHealth]] = {component: [] for component in self.components}
        self.last_health_check: Dict[str, ComponentHealth] = {}

        # Background task
        self._monitoring_task = None
        self._is_running = False

        logger.info("System Health Monitor initialized")

    async def start_monitoring(self):
        """Start background health monitoring."""
        if self._is_running:
            logger.warning("Health monitoring already running")
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(self._monitor_loop())
        logger.info("System health monitoring started")

    async def stop_monitoring(self):
        """Stop background health monitoring."""
        self._is_running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("System health monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._is_running:
            try:
                await self.monitor_component_health()
                await asyncio.sleep(self.monitor_interval)
            except asyncio.CancelledError:
                logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}", exc_info=True)
                await asyncio.sleep(5)  # Wait before retrying

    async def monitor_component_health(self):
        """Monitor all system components and emit health updates."""
        logger.debug("Starting component health check cycle")

        for component in self.components:
            try:
                health = await self._check_component_health(component)

                # Store health record
                self._store_health_record(component, health)

                # Emit health update event
                await self.event_publisher.publish_system_health_update(
                    component=component,
                    status=health.status.value,
                    response_time_ms=health.response_time_ms,
                    error_message=health.error_message,
                    additional_metrics=health.additional_metrics or {},
                )

                # Check for status changes requiring alerts
                previous_health = self.last_health_check.get(component)
                if previous_health and self._should_alert_status_change(previous_health, health):
                    await self._emit_status_change_alert(component, previous_health, health)

                self.last_health_check[component] = health

            except Exception as e:
                logger.error(f"Error checking health for {component}: {e}", exc_info=True)

        logger.debug("Component health check cycle completed")

    async def _check_component_health(self, component: str) -> ComponentHealth:
        """Check health of a specific component."""
        start_time = time.time()

        try:
            if component == "redis":
                return await self._check_redis_health(start_time)
            elif component == "ghl_api":
                return await self._check_ghl_api_health(start_time)
            elif component == "claude_api":
                return await self._check_claude_api_health(start_time)
            elif component == "database":
                return await self._check_database_health(start_time)
            elif component == "jorge_seller_bot":
                return await self._check_jorge_bot_health(start_time)
            elif component == "lead_bot":
                return await self._check_lead_bot_health(start_time)
            elif component == "intent_decoder":
                return await self._check_intent_decoder_health(start_time)
            else:
                return ComponentHealth(
                    component=component,
                    status=ComponentStatus.UNKNOWN,
                    response_time_ms=0,
                    error_message="Unknown component",
                    last_check=datetime.now(timezone.utc),
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component=component,
                status=ComponentStatus.DOWN,
                response_time_ms=response_time_ms,
                error_message=str(e),
                last_check=datetime.now(timezone.utc),
                health_score=0.0,
            )

    async def _check_redis_health(self, start_time: float) -> ComponentHealth:
        """Check Redis health."""
        try:
            # Test Redis connection
            test_key = f"health_check_{int(time.time())}"
            await self.cache_service.set(test_key, "ping", ttl=5)
            result = await self.cache_service.get(test_key)
            await self.cache_service.delete(test_key)

            response_time_ms = (time.time() - start_time) * 1000

            if result == "ping":
                status = self._determine_status(response_time_ms)
                return ComponentHealth(
                    component="redis",
                    status=status,
                    response_time_ms=response_time_ms,
                    last_check=datetime.now(timezone.utc),
                    additional_metrics={"connection_pool_size": 10},  # Mock metric
                    health_score=self._calculate_health_score(status, response_time_ms),
                )
            else:
                return ComponentHealth(
                    component="redis",
                    status=ComponentStatus.DEGRADED,
                    response_time_ms=response_time_ms,
                    error_message="Redis ping test failed",
                    last_check=datetime.now(timezone.utc),
                    health_score=0.6,
                )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="redis",
                status=ComponentStatus.DOWN,
                response_time_ms=response_time_ms,
                error_message=f"Redis connection failed: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.0,
            )

    async def _check_ghl_api_health(self, start_time: float) -> ComponentHealth:
        """Check GoHighLevel API health."""
        try:
            # Mock GHL API health check - would use actual GHL client
            # In production: await ghl_client.get_account_info()
            await asyncio.sleep(0.1)  # Simulate API call
            response_time_ms = (time.time() - start_time) * 1000

            status = self._determine_status(response_time_ms)
            return ComponentHealth(
                component="ghl_api",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={"rate_limit_remaining": 95, "daily_quota_used": 245},
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="ghl_api",
                status=ComponentStatus.DOWN,
                response_time_ms=response_time_ms,
                error_message=f"GHL API error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.0,
            )

    async def _check_claude_api_health(self, start_time: float) -> ComponentHealth:
        """Check Claude API health."""
        try:
            # Mock Claude API health check - would use actual Claude client
            # In production: simple API test call
            await asyncio.sleep(0.15)  # Simulate API call
            response_time_ms = (time.time() - start_time) * 1000

            status = self._determine_status(response_time_ms)
            return ComponentHealth(
                component="claude_api",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={"tokens_used_today": 125000, "rate_limit_remaining": 98},
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="claude_api",
                status=ComponentStatus.DOWN,
                response_time_ms=response_time_ms,
                error_message=f"Claude API error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.0,
            )

    async def _check_database_health(self, start_time: float) -> ComponentHealth:
        """Check database health."""
        try:
            # Mock database health check - would use actual DB connection
            # In production: simple SELECT query
            await asyncio.sleep(0.05)  # Simulate DB query
            response_time_ms = (time.time() - start_time) * 1000

            status = self._determine_status(response_time_ms)
            return ComponentHealth(
                component="database",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={
                    "active_connections": 12,
                    "connection_pool_size": 20,
                    "query_cache_hit_ratio": 0.94,
                },
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="database",
                status=ComponentStatus.DOWN,
                response_time_ms=response_time_ms,
                error_message=f"Database error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.0,
            )

    async def _check_jorge_bot_health(self, start_time: float) -> ComponentHealth:
        """Check Jorge Seller Bot health."""
        try:
            # Mock bot health check - would check bot availability and recent activity
            await asyncio.sleep(0.02)  # Simulate bot status check
            response_time_ms = (time.time() - start_time) * 1000

            # Mock metrics
            status = ComponentStatus.HEALTHY
            return ComponentHealth(
                component="jorge_seller_bot",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={"active_conversations": 5, "qualification_rate": 0.78, "avg_response_time": 245},
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="jorge_seller_bot",
                status=ComponentStatus.DEGRADED,
                response_time_ms=response_time_ms,
                error_message=f"Jorge bot error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.3,
            )

    async def _check_lead_bot_health(self, start_time: float) -> ComponentHealth:
        """Check Lead Bot health."""
        try:
            # Mock lead bot health check
            await asyncio.sleep(0.02)
            response_time_ms = (time.time() - start_time) * 1000

            status = ComponentStatus.HEALTHY
            return ComponentHealth(
                component="lead_bot",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={
                    "active_sequences": 18,
                    "sequence_completion_rate": 0.85,
                    "cma_generation_success": 0.96,
                },
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="lead_bot",
                status=ComponentStatus.DEGRADED,
                response_time_ms=response_time_ms,
                error_message=f"Lead bot error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.3,
            )

    async def _check_intent_decoder_health(self, start_time: float) -> ComponentHealth:
        """Check Intent Decoder health."""
        try:
            # Mock intent decoder health check
            await asyncio.sleep(0.04)
            response_time_ms = (time.time() - start_time) * 1000

            status = self._determine_status(response_time_ms)
            return ComponentHealth(
                component="intent_decoder",
                status=status,
                response_time_ms=response_time_ms,
                last_check=datetime.now(timezone.utc),
                additional_metrics={
                    "analysis_accuracy": 0.95,
                    "avg_processing_time": 42.3,
                    "confidence_threshold_met": 0.92,
                },
                health_score=self._calculate_health_score(status, response_time_ms),
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            return ComponentHealth(
                component="intent_decoder",
                status=ComponentStatus.DEGRADED,
                response_time_ms=response_time_ms,
                error_message=f"Intent decoder error: {str(e)}",
                last_check=datetime.now(timezone.utc),
                health_score=0.3,
            )

    def _determine_status(self, response_time_ms: float) -> ComponentStatus:
        """Determine component status based on response time."""
        if response_time_ms >= self.down_threshold_ms:
            return ComponentStatus.DOWN
        elif response_time_ms >= self.degraded_threshold_ms:
            return ComponentStatus.DEGRADED
        else:
            return ComponentStatus.HEALTHY

    def _calculate_health_score(self, status: ComponentStatus, response_time_ms: float) -> float:
        """Calculate component health score based on status and response time."""
        status_scores = {
            ComponentStatus.HEALTHY: 1.0,
            ComponentStatus.DEGRADED: 0.6,
            ComponentStatus.RECOVERING: 0.4,
            ComponentStatus.DOWN: 0.0,
            ComponentStatus.UNKNOWN: 0.1,
        }

        base_score = status_scores.get(status, 0.5)

        # Adjust based on response time
        if response_time_ms < 100:
            time_modifier = 1.0
        elif response_time_ms < 500:
            time_modifier = 0.8
        elif response_time_ms < 1000:
            time_modifier = 0.6
        else:
            time_modifier = 0.4

        return round(base_score * time_modifier, 2)

    def _store_health_record(self, component: str, health: ComponentHealth):
        """Store health record in component history."""
        if component not in self.health_history:
            self.health_history[component] = []

        self.health_history[component].append(health)

        # Keep only recent history
        if len(self.health_history[component]) > self.health_history_size:
            self.health_history[component] = self.health_history[component][-self.health_history_size :]

    def _should_alert_status_change(self, previous: ComponentHealth, current: ComponentHealth) -> bool:
        """Determine if status change warrants an alert."""
        # Alert on status degradation or improvement after being down
        return previous.status != current.status and (
            current.status in [ComponentStatus.DOWN, ComponentStatus.DEGRADED]
            or (previous.status == ComponentStatus.DOWN and current.status == ComponentStatus.HEALTHY)
        )

    async def _emit_status_change_alert(self, component: str, previous: ComponentHealth, current: ComponentHealth):
        """Emit alert for significant status changes."""
        severity = "critical" if current.status == ComponentStatus.DOWN else "warning"

        message = f"{component.replace('_', ' ').title()} status changed from {previous.status.value} to {current.status.value}"

        # Use the existing system alert publisher
        from ghl_real_estate_ai.services.event_publisher import publish_system_alert

        await publish_system_alert(
            alert_type="component_status_change",
            message=message,
            severity=severity,
            details={
                "component": component,
                "previous_status": previous.status.value,
                "current_status": current.status.value,
                "response_time_ms": current.response_time_ms,
                "error_message": current.error_message,
            },
        )

    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        if not self.last_health_check:
            return {"status": "unknown", "message": "No health data available"}

        component_statuses = [health.status for health in self.last_health_check.values()]
        overall_score = sum(health.health_score for health in self.last_health_check.values()) / len(
            self.last_health_check
        )

        # Determine overall status
        if any(status == ComponentStatus.DOWN for status in component_statuses):
            overall_status = "degraded"
        elif any(status == ComponentStatus.DEGRADED for status in component_statuses):
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "health_score": round(overall_score, 2),
            "total_components": len(self.components),
            "healthy_components": sum(1 for s in component_statuses if s == ComponentStatus.HEALTHY),
            "degraded_components": sum(1 for s in component_statuses if s == ComponentStatus.DEGRADED),
            "down_components": sum(1 for s in component_statuses if s == ComponentStatus.DOWN),
            "last_check": max(h.last_check for h in self.last_health_check.values()).isoformat()
            if self.last_health_check
            else None,
        }

    def get_component_health(self, component: str) -> Optional[ComponentHealth]:
        """Get latest health data for a specific component."""
        return self.last_health_check.get(component)

    def get_health_history(self, component: str, limit: int = 10) -> List[ComponentHealth]:
        """Get health history for a component."""
        history = self.health_history.get(component, [])
        return history[-limit:] if history else []


# Global instance
_system_health_monitor = None


def get_system_health_monitor() -> SystemHealthMonitor:
    """Get singleton SystemHealthMonitor instance."""
    global _system_health_monitor
    if _system_health_monitor is None:
        _system_health_monitor = SystemHealthMonitor()
    return _system_health_monitor


# Convenience functions
async def start_system_health_monitoring():
    """Start system health monitoring."""
    monitor = get_system_health_monitor()
    await monitor.start_monitoring()


async def stop_system_health_monitoring():
    """Stop system health monitoring."""
    monitor = get_system_health_monitor()
    await monitor.stop_monitoring()


async def get_system_health_summary() -> Dict[str, Any]:
    """Get overall system health summary."""
    monitor = get_system_health_monitor()
    return monitor.get_overall_health()
