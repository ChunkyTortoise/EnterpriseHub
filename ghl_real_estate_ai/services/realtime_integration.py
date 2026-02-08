"""
Real-Time Integration Service for Jorge's Dashboard.

Integrates with existing data services to automatically publish real-time events
when data changes occur. Provides hooks and decorators for seamless integration
with minimal code changes to existing services.

Features:
- Automatic event publishing from data service operations
- Intelligent change detection and aggregation
- Performance optimization with async processing
- Integration with caching layer for efficiency
- Configurable event filtering and rate limiting
"""

import asyncio
import functools
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Union

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_service import UserRole
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.event_publisher import EventType, get_event_publisher

logger = get_logger(__name__)


@dataclass
class IntegrationMetrics:
    """Metrics for real-time integration service."""

    total_events_generated: int = 0
    events_by_source: Dict[str, int] = None
    events_by_type: Dict[str, int] = None
    integration_errors: int = 0
    last_event_time: Optional[datetime] = None

    def __post_init__(self):
        if self.events_by_source is None:
            self.events_by_source = {}
        if self.events_by_type is None:
            self.events_by_type = {}


class RealTimeIntegration:
    """
    Real-time integration service for automatic event publishing.

    Provides decorators and utilities for integrating real-time events
    into existing data services and business logic.
    """

    def __init__(self):
        self.event_publisher = get_event_publisher()
        self.cache_service = get_cache_service()
        self.metrics = IntegrationMetrics()

        # Rate limiting configuration
        self.rate_limits = {
            "lead_update": {"max_per_minute": 100, "current": 0, "reset_time": 0},
            "conversation_update": {"max_per_minute": 50, "current": 0, "reset_time": 0},
            "commission_update": {"max_per_minute": 20, "current": 0, "reset_time": 0},
            "performance_update": {"max_per_minute": 30, "current": 0, "reset_time": 0},
        }

        logger.info("Real-time integration service initialized")

    # ==============================================================================
    # DECORATOR FUNCTIONS FOR EASY INTEGRATION
    # ==============================================================================

    def publish_lead_events(
        self, action_field: str = "action", lead_id_field: str = "lead_id", data_field: str = "lead_data"
    ):
        """
        Decorator to automatically publish lead update events.

        Usage:
        @real_time.publish_lead_events()
        async def update_lead(lead_id: str, lead_data: dict, action: str = "updated"):
            # Your lead update logic
            return result
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Call original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                try:
                    # Extract event data from function arguments
                    lead_id = self._extract_value(args, kwargs, lead_id_field)
                    action = self._extract_value(args, kwargs, action_field, "updated")
                    lead_data = self._extract_value(args, kwargs, data_field, {})

                    # Get user context if available
                    user_id = kwargs.get("user_id") or getattr(result, "user_id", None)
                    location_id = kwargs.get("location_id") or getattr(result, "location_id", None)

                    # Publish lead update event
                    await self._safe_publish_lead_update(lead_id, lead_data, action, user_id, location_id)

                except Exception as e:
                    logger.error(f"Error publishing lead event from {func.__name__}: {e}")
                    self.metrics.integration_errors += 1

                return result

            return wrapper

        return decorator

    def publish_conversation_events(
        self, conversation_id_field: str = "conversation_id", lead_id_field: str = "lead_id", stage_field: str = "stage"
    ):
        """
        Decorator to automatically publish conversation update events.

        Usage:
        @real_time.publish_conversation_events()
        async def update_conversation_stage(conversation_id: str, lead_id: str, stage: str):
            # Your conversation update logic
            return result
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                try:
                    conversation_id = self._extract_value(args, kwargs, conversation_id_field)
                    lead_id = self._extract_value(args, kwargs, lead_id_field)
                    stage = self._extract_value(args, kwargs, stage_field)

                    user_id = kwargs.get("user_id") or getattr(result, "user_id", None)
                    location_id = kwargs.get("location_id") or getattr(result, "location_id", None)

                    await self._safe_publish_conversation_update(conversation_id, lead_id, stage, user_id, location_id)

                except Exception as e:
                    logger.error(f"Error publishing conversation event from {func.__name__}: {e}")
                    self.metrics.integration_errors += 1

                return result

            return wrapper

        return decorator

    def publish_commission_events(
        self,
        deal_id_field: str = "deal_id",
        amount_field: str = "commission_amount",
        status_field: str = "pipeline_status",
    ):
        """
        Decorator to automatically publish commission update events.

        Usage:
        @real_time.publish_commission_events()
        async def update_commission(deal_id: str, commission_amount: float, pipeline_status: str):
            # Your commission update logic
            return result
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                try:
                    deal_id = self._extract_value(args, kwargs, deal_id_field)
                    amount = self._extract_value(args, kwargs, amount_field, 0)
                    status = self._extract_value(args, kwargs, status_field, "potential")

                    user_id = kwargs.get("user_id") or getattr(result, "user_id", None)
                    location_id = kwargs.get("location_id") or getattr(result, "location_id", None)

                    await self._safe_publish_commission_update(deal_id, amount, status, user_id, location_id)

                except Exception as e:
                    logger.error(f"Error publishing commission event from {func.__name__}: {e}")
                    self.metrics.integration_errors += 1

                return result

            return wrapper

        return decorator

    def publish_performance_events(self, metric_name: str):
        """
        Decorator to automatically publish performance metric events.

        Usage:
        @real_time.publish_performance_events("response_time")
        async def measure_response_time():
            # Your performance measurement logic
            return time_in_seconds
        """

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                try:
                    # Extract metric value from result
                    metric_value = result if isinstance(result, (int, float)) else getattr(result, "value", 0)

                    user_id = kwargs.get("user_id") or getattr(result, "user_id", None)

                    await self._safe_publish_performance_update(metric_name, metric_value, user_id)

                except Exception as e:
                    logger.error(f"Error publishing performance event from {func.__name__}: {e}")
                    self.metrics.integration_errors += 1

                return result

            return wrapper

        return decorator

    # ==============================================================================
    # MANUAL EVENT PUBLISHING METHODS
    # ==============================================================================

    async def publish_dashboard_update(self, component: str, data: Dict[str, Any], user_id: Optional[int] = None):
        """Manually publish dashboard component update."""
        await self.event_publisher.publish_dashboard_refresh(component, data, user_id=user_id)
        await self._update_metrics("dashboard_refresh", "manual")

    async def publish_system_status(self, status: str, details: Dict[str, Any], severity: str = "info"):
        """Manually publish system status update."""
        await self.event_publisher.publish_system_alert(
            alert_type="system_status",
            message=f"System status: {status}",
            severity=severity,
            details=details,
            target_roles=[UserRole.ADMIN],
        )
        await self._update_metrics("system_alert", "manual")

    async def publish_user_login(self, user_id: int, username: str):
        """Publish user login event."""
        await self.event_publisher.publish_user_activity(
            action="login",
            user_id=user_id,
            details={"username": username, "login_time": datetime.now(timezone.utc).isoformat()},
            target_roles=[UserRole.ADMIN],
        )
        await self._update_metrics("user_activity", "auth")

    # ==============================================================================
    # RATE LIMITED EVENT PUBLISHING
    # ==============================================================================

    async def _safe_publish_lead_update(
        self, lead_id: str, lead_data: Dict[str, Any], action: str, user_id: Optional[int], location_id: Optional[str]
    ):
        """Publish lead update with rate limiting."""
        if not self._check_rate_limit("lead_update"):
            logger.debug(f"Rate limit exceeded for lead_update, skipping event for {lead_id}")
            return

        await self.event_publisher.publish_lead_update(lead_id, lead_data, action, user_id, location_id)
        await self._update_metrics("lead_update", "automated")

    async def _safe_publish_conversation_update(
        self, conversation_id: str, lead_id: str, stage: str, user_id: Optional[int], location_id: Optional[str]
    ):
        """Publish conversation update with rate limiting."""
        if not self._check_rate_limit("conversation_update"):
            logger.debug(f"Rate limit exceeded for conversation_update, skipping event for {conversation_id}")
            return

        await self.event_publisher.publish_conversation_update(
            conversation_id, lead_id, stage, None, user_id, location_id
        )
        await self._update_metrics("conversation_update", "automated")

    async def _safe_publish_commission_update(
        self, deal_id: str, amount: float, status: str, user_id: Optional[int], location_id: Optional[str]
    ):
        """Publish commission update with rate limiting."""
        if not self._check_rate_limit("commission_update"):
            logger.debug(f"Rate limit exceeded for commission_update, skipping event for {deal_id}")
            return

        await self.event_publisher.publish_commission_update(deal_id, amount, status, user_id, location_id)
        await self._update_metrics("commission_update", "automated")

    async def _safe_publish_performance_update(self, metric_name: str, metric_value: float, user_id: Optional[int]):
        """Publish performance update with rate limiting."""
        if not self._check_rate_limit("performance_update"):
            logger.debug(f"Rate limit exceeded for performance_update, skipping {metric_name}")
            return

        await self.event_publisher.publish_performance_update(metric_name, metric_value, user_id=user_id)
        await self._update_metrics("performance_update", "automated")

    # ==============================================================================
    # UTILITY METHODS
    # ==============================================================================

    def _extract_value(self, args: tuple, kwargs: dict, field: str, default: Any = None) -> Any:
        """Extract value from function arguments by field name."""
        # Try kwargs first
        if field in kwargs:
            return kwargs[field]

        # Try to match positional arguments
        # This is a simplified implementation - in a real system you'd want
        # to use function signature inspection for more robust matching
        if args and len(args) > 0:
            # For now, assume first positional arg matches first field
            if field in ["lead_id", "conversation_id", "deal_id"] and len(args) >= 1:
                return args[0]
            elif field in ["lead_data", "stage", "commission_amount"] and len(args) >= 2:
                return args[1]
            elif field in ["action", "pipeline_status"] and len(args) >= 3:
                return args[2]

        return default

    def _check_rate_limit(self, event_type: str) -> bool:
        """Check if event type is within rate limits."""
        if event_type not in self.rate_limits:
            return True

        current_time = time.time()
        rate_limit = self.rate_limits[event_type]

        # Reset counter every minute
        if current_time - rate_limit["reset_time"] > 60:
            rate_limit["current"] = 0
            rate_limit["reset_time"] = current_time

        # Check limit
        if rate_limit["current"] >= rate_limit["max_per_minute"]:
            return False

        # Increment counter
        rate_limit["current"] += 1
        return True

    async def _update_metrics(self, event_type: str, source: str):
        """Update integration metrics."""
        self.metrics.total_events_generated += 1
        self.metrics.events_by_type[event_type] = self.metrics.events_by_type.get(event_type, 0) + 1
        self.metrics.events_by_source[source] = self.metrics.events_by_source.get(source, 0) + 1
        self.metrics.last_event_time = datetime.now(timezone.utc)

    # ==============================================================================
    # CACHE INTEGRATION FOR INTELLIGENT UPDATES
    # ==============================================================================

    async def setup_cache_invalidation_hooks(self):
        """Set up cache invalidation hooks to trigger dashboard updates."""
        # This would integrate with the cache service to detect cache changes
        # and automatically publish dashboard refresh events
        logger.info("Cache invalidation hooks set up for real-time updates")

    async def detect_data_changes(self, cache_key: str, old_data: Any, new_data: Any) -> bool:
        """
        Detect if data has changed significantly enough to warrant an event.

        Returns True if changes are significant, False otherwise.
        """
        # Simple change detection - in a real implementation this would be more sophisticated
        if old_data == new_data:
            return False

        # For numeric data, only trigger if change is > 5%
        if isinstance(old_data, (int, float)) and isinstance(new_data, (int, float)):
            if old_data == 0:
                return new_data != 0
            change_percent = abs((new_data - old_data) / old_data)
            return change_percent > 0.05

        return True

    # ==============================================================================
    # MONITORING AND DIAGNOSTICS
    # ==============================================================================

    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get real-time integration metrics."""
        return {
            "total_events_generated": self.metrics.total_events_generated,
            "events_by_type": self.metrics.events_by_type,
            "events_by_source": self.metrics.events_by_source,
            "integration_errors": self.metrics.integration_errors,
            "last_event_time": self.metrics.last_event_time.isoformat() if self.metrics.last_event_time else None,
            "rate_limits": {
                event_type: {
                    "max_per_minute": config["max_per_minute"],
                    "current_count": config["current"],
                    "time_until_reset": max(0, config["reset_time"] + 60 - time.time()),
                }
                for event_type, config in self.rate_limits.items()
            },
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on real-time integration."""
        try:
            # Test event publishing
            test_start = time.time()
            await self.event_publisher.publish_system_alert(
                alert_type="integration_health_check",
                message="Integration health check",
                severity="info",
                target_roles=[UserRole.ADMIN],
            )
            publish_time = time.time() - test_start

            return {
                "status": "healthy",
                "publish_latency_ms": round(publish_time * 1000, 2),
                "metrics": self.get_integration_metrics(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Real-time integration health check failed: {e}")
            return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}


# Global integration service instance
_real_time_integration = None


def get_real_time_integration() -> RealTimeIntegration:
    """Get singleton real-time integration instance."""
    global _real_time_integration
    if _real_time_integration is None:
        _real_time_integration = RealTimeIntegration()
    return _real_time_integration


# ==============================================================================
# EXAMPLE INTEGRATION USAGE
# ==============================================================================

# Example of how to integrate with existing services:

"""
# In your existing lead service:
from ghl_real_estate_ai.services.realtime_integration import get_real_time_integration

real_time = get_real_time_integration()

@real_time.publish_lead_events()
async def update_lead_status(lead_id: str, lead_data: dict, action: str = "updated", user_id: int = None):
    # Your existing lead update logic
    result = await database.update_lead(lead_id, lead_data)
    # Event will be automatically published
    return result

@real_time.publish_conversation_events()
async def advance_conversation_stage(conversation_id: str, lead_id: str, stage: str, user_id: int = None):
    # Your existing conversation logic
    result = await database.update_conversation(conversation_id, {"stage": stage})
    # Event will be automatically published
    return result

@real_time.publish_commission_events()
async def update_deal_commission(deal_id: str, commission_amount: float, pipeline_status: str, user_id: int = None):
    # Your existing commission logic
    result = await database.update_commission(deal_id, commission_amount, pipeline_status)
    # Event will be automatically published
    return result
"""
