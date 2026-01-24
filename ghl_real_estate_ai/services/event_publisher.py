"""
Real-Time Event Publisher for Jorge's Real Estate AI Dashboard.

Publishes events when data changes occur to enable real-time dashboard updates.
Integrates with existing services to detect data changes and broadcast them
via the WebSocket system to connected clients.

Features:
- Automatic event detection from data service operations
- Intelligent event aggregation and batching
- Performance monitoring and metrics
- Integration with caching layer for efficiency
- Event filtering and role-based distribution
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from dataclasses import dataclass
import json

from ghl_real_estate_ai.core.logger import get_logger
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager, RealTimeEvent, EventType
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.auth_service import UserRole

logger = get_logger(__name__)

@dataclass
class EventMetrics:
    """Event publishing metrics."""
    total_events_published: int = 0
    events_by_type: Dict[str, int] = None
    last_event_time: Optional[datetime] = None
    average_processing_time_ms: float = 0.0
    failed_publishes: int = 0
    
    def __post_init__(self):
        if self.events_by_type is None:
            self.events_by_type = {}

class EventPublisher:
    """
    Real-Time Event Publisher Service.
    
    Monitors data changes and publishes real-time events to connected 
    WebSocket clients. Provides intelligent batching, filtering, and
    performance optimization.
    """
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.cache_service = get_cache_service()
        self.metrics = EventMetrics()
        
        # Event batching configuration
        self.batch_interval = 0.5  # seconds
        self.max_batch_size = 10
        self._event_batch = []
        self._batch_timer = None
        
        # Performance tracking
        self._processing_times = []
        
        logger.info("Event Publisher initialized")

    async def start(self):
        """Start the event publisher service."""
        await self.websocket_manager.start_services()
        logger.info("Event Publisher started")

    async def stop(self):
        """Stop the event publisher service."""
        if self._batch_timer:
            self._batch_timer.cancel()
        await self.websocket_manager.stop_services()
        logger.info("Event Publisher stopped")

    async def publish_lead_update(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        action: str = "updated",
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """
        Publish lead update event.
        
        Args:
            lead_id: Lead identifier
            lead_data: Lead data that was updated
            action: Type of action (created, updated, qualified, etc.)
            user_id: User who triggered the update (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.LEAD_UPDATE,
            data={
                "lead_id": lead_id,
                "action": action,
                "lead_data": lead_data,
                "updated_fields": list(lead_data.keys()),
                "summary": f"Lead {action}: {lead_data.get('name', 'Unknown')}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if action in ["created", "qualified", "hot"] else "normal"
        )
        
        await self._publish_event(event)
        logger.info(f"Published lead update event: {lead_id} ({action})")

    async def publish_conversation_update(
        self,
        conversation_id: str,
        lead_id: str,
        stage: str,
        message: Optional[str] = None,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """
        Publish conversation stage update event.
        
        Args:
            conversation_id: Conversation identifier
            lead_id: Associated lead ID
            stage: New conversation stage (Q1, Q2, Q3, Q4, etc.)
            message: Latest message content (optional)
            user_id: User associated with conversation (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.CONVERSATION_UPDATE,
            data={
                "conversation_id": conversation_id,
                "lead_id": lead_id,
                "stage": stage,
                "message_preview": message[:100] + "..." if message and len(message) > 100 else message,
                "stage_progression": self._get_stage_progression(stage),
                "summary": f"Conversation moved to {stage}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if stage in ["Q4", "hot", "ready"] else "normal"
        )
        
        await self._publish_event(event)
        logger.info(f"Published conversation update: {conversation_id} -> {stage}")

    def _get_stage_progression(self, stage: str) -> Dict[str, Any]:
        """Get conversation stage progression information."""
        stage_map = {
            "Q1": {"progress": 25, "next": "Q2", "description": "Initial Qualification"},
            "Q2": {"progress": 50, "next": "Q3", "description": "Budgeting & Timeline"},
            "Q3": {"progress": 75, "next": "Q4", "description": "Property Search"},
            "Q4": {"progress": 90, "next": "closing", "description": "Ready to Sell"},
            "closing": {"progress": 100, "next": None, "description": "Deal Closing"}
        }
        
        return stage_map.get(stage, {"progress": 0, "next": None, "description": "Unknown"})

    async def publish_commission_update(
        self,
        deal_id: str,
        commission_amount: float,
        pipeline_status: str,
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """
        Publish commission pipeline update event.
        
        Args:
            deal_id: Deal identifier
            commission_amount: Commission amount
            pipeline_status: Pipeline status (potential, confirmed, paid)
            user_id: User associated with deal (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.COMMISSION_UPDATE,
            data={
                "deal_id": deal_id,
                "commission_amount": commission_amount,
                "pipeline_status": pipeline_status,
                "formatted_amount": f"${commission_amount:,.2f}",
                "impact": "positive" if commission_amount > 0 else "neutral",
                "summary": f"Commission {pipeline_status}: ${commission_amount:,.2f}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="high" if commission_amount > 10000 else "normal"
        )
        
        await self._publish_event(event)
        logger.info(f"Published commission update: {deal_id} - ${commission_amount:,.2f} ({pipeline_status})")

    async def publish_system_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "info",
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None
    ):
        """
        Publish system alert event.
        
        Args:
            alert_type: Type of alert (performance, error, maintenance, etc.)
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            details: Additional alert details (optional)
            target_roles: Specific roles to target (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "message": message,
                "severity": severity,
                "details": details or {},
                "action_required": severity in ["error", "critical"],
                "summary": f"{severity.upper()}: {message}"
            },
            timestamp=datetime.now(timezone.utc),
            priority="critical" if severity == "critical" else "high" if severity == "error" else "normal"
        )
        
        # Target specific roles if specified
        if target_roles:
            await self.websocket_manager.broadcast_event(event, target_roles=set(target_roles))
        else:
            await self._publish_event(event)
            
        logger.info(f"Published system alert: {alert_type} ({severity}) - {message}")

    async def publish_performance_update(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = "",
        comparison: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None
    ):
        """
        Publish performance metric update event.
        
        Args:
            metric_name: Name of the metric
            metric_value: Current metric value
            metric_unit: Unit of measurement (optional)
            comparison: Comparison data (previous value, trend, etc.) (optional)
            user_id: User associated with metric (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.PERFORMANCE_UPDATE,
            data={
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metric_unit": metric_unit,
                "formatted_value": f"{metric_value:.2f}{metric_unit}",
                "comparison": comparison or {},
                "trend": self._calculate_trend(comparison) if comparison else "neutral",
                "summary": f"{metric_name}: {metric_value:.2f}{metric_unit}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low"
        )
        
        await self._publish_event(event)
        logger.debug(f"Published performance update: {metric_name} = {metric_value}{metric_unit}")

    def _calculate_trend(self, comparison: Dict[str, Any]) -> str:
        """Calculate trend direction from comparison data."""
        if "previous_value" in comparison and "current_value" in comparison:
            prev = comparison["previous_value"]
            curr = comparison["current_value"]
            
            if curr > prev * 1.05:  # 5% increase threshold
                return "up"
            elif curr < prev * 0.95:  # 5% decrease threshold
                return "down"
                
        return "stable"

    async def publish_dashboard_refresh(
        self,
        component: str,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        location_id: Optional[str] = None
    ):
        """
        Publish dashboard component refresh event.
        
        Args:
            component: Dashboard component to refresh
            data: Updated component data
            user_id: User requesting refresh (optional)
            location_id: Location/tenant ID (optional)
        """
        event = RealTimeEvent(
            event_type=EventType.DASHBOARD_REFRESH,
            data={
                "component": component,
                "data": data,
                "cache_key": f"dashboard:{component}:{location_id or 'global'}",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "summary": f"Dashboard component refreshed: {component}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            location_id=location_id,
            priority="normal"
        )
        
        await self._publish_event(event)
        logger.debug(f"Published dashboard refresh: {component}")

    async def publish_user_activity(
        self,
        action: str,
        user_id: int,
        details: Optional[Dict[str, Any]] = None,
        target_roles: Optional[List[UserRole]] = None
    ):
        """
        Publish user activity event.
        
        Args:
            action: Activity action (login, logout, view_dashboard, etc.)
            user_id: User ID performing action
            details: Additional activity details (optional)
            target_roles: Specific roles to notify (optional, defaults to admin only)
        """
        event = RealTimeEvent(
            event_type=EventType.USER_ACTIVITY,
            data={
                "action": action,
                "user_id": user_id,
                "details": details or {},
                "session_info": await self._get_session_info(user_id),
                "summary": f"User activity: {action}"
            },
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            priority="low"
        )
        
        # Default to admin-only notifications for user activity
        target_roles = target_roles or [UserRole.ADMIN]
        await self.websocket_manager.broadcast_event(event, target_roles=set(target_roles))
        logger.debug(f"Published user activity: {action} (user {user_id})")

    async def _get_session_info(self, user_id: int) -> Dict[str, Any]:
        """Get session information for user activity events."""
        # This could be enhanced to include more session details
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id
        }

    async def _publish_event(self, event: RealTimeEvent):
        """
        Publish event with performance tracking and batching.
        
        Args:
            event: Event to publish
        """
        start_time = time.time()
        
        try:
            # Add to batch
            self._event_batch.append(event)
            
            # Check if batch should be processed immediately
            should_process_immediately = (
                len(self._event_batch) >= self.max_batch_size or
                event.priority == "critical" or
                (event.priority == "high" and len(self._event_batch) >= 3)
            )
            
            if should_process_immediately:
                await self._process_event_batch()
            else:
                # Schedule batch processing if not already scheduled
                if self._batch_timer is None:
                    self._batch_timer = asyncio.create_task(self._schedule_batch_processing())
            
            # Update metrics
            processing_time = (time.time() - start_time) * 1000  # ms
            self._processing_times.append(processing_time)
            
            # Keep only recent processing times (last 100)
            if len(self._processing_times) > 100:
                self._processing_times = self._processing_times[-100:]
                
            self.metrics.average_processing_time_ms = sum(self._processing_times) / len(self._processing_times)
            self.metrics.total_events_published += 1
            self.metrics.last_event_time = datetime.now(timezone.utc)
            
            # Track events by type
            event_type_name = event.event_type.value
            self.metrics.events_by_type[event_type_name] = self.metrics.events_by_type.get(event_type_name, 0) + 1
            
        except Exception as e:
            logger.error(f"Error publishing event {event.event_type.value}: {e}")
            self.metrics.failed_publishes += 1

    async def _schedule_batch_processing(self):
        """Schedule batch processing after interval."""
        try:
            await asyncio.sleep(self.batch_interval)
            await self._process_event_batch()
        except asyncio.CancelledError:
            pass
        finally:
            self._batch_timer = None

    async def _process_event_batch(self):
        """Process the current batch of events."""
        if not self._event_batch:
            return
            
        # Cancel existing timer
        if self._batch_timer:
            self._batch_timer.cancel()
            self._batch_timer = None
        
        # Process events
        batch = self._event_batch.copy()
        self._event_batch.clear()
        
        # Group events by priority for processing order
        critical_events = [e for e in batch if e.priority == "critical"]
        high_events = [e for e in batch if e.priority == "high"]
        normal_events = [e for e in batch if e.priority in ["normal", "low"]]
        
        # Process critical events first
        for event in critical_events:
            await self.websocket_manager.publish_event(event)
            
        # Process high priority events
        for event in high_events:
            await self.websocket_manager.publish_event(event)
            
        # Batch process normal priority events
        if normal_events:
            # For normal events, we can potentially aggregate similar events
            aggregated_events = self._aggregate_similar_events(normal_events)
            for event in aggregated_events:
                await self.websocket_manager.publish_event(event)
        
        logger.debug(f"Processed event batch: {len(batch)} events ({len(critical_events)} critical, {len(high_events)} high, {len(normal_events)} normal)")

    def _aggregate_similar_events(self, events: List[RealTimeEvent]) -> List[RealTimeEvent]:
        """
        Aggregate similar events to reduce WebSocket message volume.
        
        Args:
            events: List of events to potentially aggregate
            
        Returns:
            List of events (some potentially aggregated)
        """
        # For now, return events as-is
        # In the future, we could aggregate multiple dashboard_refresh events
        # for the same component, or multiple performance_updates for the same metric
        return events

    async def create_decorator(self, event_type: EventType, **event_kwargs):
        """
        Create a decorator for automatically publishing events from function calls.
        
        Args:
            event_type: Type of event to publish
            **event_kwargs: Additional event data
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            async def wrapper(*args, **kwargs):
                # Call original function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                
                # Extract event data from function result or arguments
                event_data = {
                    "function": func.__name__,
                    "result": result if isinstance(result, dict) else {"value": result},
                    **event_kwargs
                }
                
                # Create and publish event
                event = RealTimeEvent(
                    event_type=event_type,
                    data=event_data,
                    timestamp=datetime.now(timezone.utc),
                    priority="normal"
                )
                
                await self._publish_event(event)
                return result
                
            return wrapper
        return decorator

    def get_metrics(self) -> Dict[str, Any]:
        """Get event publishing metrics."""
        return {
            "total_events_published": self.metrics.total_events_published,
            "events_by_type": self.metrics.events_by_type,
            "last_event_time": self.metrics.last_event_time.isoformat() if self.metrics.last_event_time else None,
            "average_processing_time_ms": round(self.metrics.average_processing_time_ms, 3),
            "failed_publishes": self.metrics.failed_publishes,
            "batch_queue_size": len(self._event_batch),
            "websocket_metrics": self.websocket_manager.get_metrics()
        }

# Global event publisher instance
_event_publisher = None

def get_event_publisher() -> EventPublisher:
    """Get singleton event publisher instance."""
    global _event_publisher
    if _event_publisher is None:
        _event_publisher = EventPublisher()
    return _event_publisher

# Convenience functions for common event publishing
async def publish_lead_update(lead_id: str, lead_data: Dict[str, Any], action: str = "updated", **kwargs):
    """Convenience function to publish lead update."""
    publisher = get_event_publisher()
    await publisher.publish_lead_update(lead_id, lead_data, action, **kwargs)

async def publish_conversation_update(conversation_id: str, lead_id: str, stage: str, **kwargs):
    """Convenience function to publish conversation update."""
    publisher = get_event_publisher()
    await publisher.publish_conversation_update(conversation_id, lead_id, stage, **kwargs)

async def publish_commission_update(deal_id: str, commission_amount: float, pipeline_status: str, **kwargs):
    """Convenience function to publish commission update."""
    publisher = get_event_publisher()
    await publisher.publish_commission_update(deal_id, commission_amount, pipeline_status, **kwargs)

async def publish_system_alert(alert_type: str, message: str, severity: str = "info", **kwargs):
    """Convenience function to publish system alert."""
    publisher = get_event_publisher()
    await publisher.publish_system_alert(alert_type, message, severity, **kwargs)

async def publish_performance_update(metric_name: str, metric_value: float, **kwargs):
    """Convenience function to publish performance update."""
    publisher = get_event_publisher()
    await publisher.publish_performance_update(metric_name, metric_value, **kwargs)

async def publish_dashboard_refresh(component: str, data: Dict[str, Any], **kwargs):
    """Convenience function to publish dashboard refresh.""" 
    publisher = get_event_publisher()
    await publisher.publish_dashboard_refresh(component, data, **kwargs)