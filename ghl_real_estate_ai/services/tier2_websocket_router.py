"""
Tier 2 WebSocket Event Router

Coordinates real-time events between all Tier 2 services and integrates
with existing WebSocket infrastructure for seamless data flow.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import redis
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Tier 2 event types for WebSocket routing."""

    # Intelligent Nurturing Events
    NURTURING_CAMPAIGN_STARTED = "nurturing_campaign_started"
    NURTURING_MESSAGE_SENT = "nurturing_message_sent"
    NURTURING_RESPONSE_RECEIVED = "nurturing_response_received"
    NURTURING_CAMPAIGN_COMPLETED = "nurturing_campaign_completed"

    # Predictive Routing Events
    LEAD_ROUTED = "lead_routed"
    AGENT_ASSIGNED = "agent_assigned"
    ROUTING_OPTIMIZATION = "routing_optimization"
    AGENT_CAPACITY_UPDATED = "agent_capacity_updated"

    # Conversational Intelligence Events
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ANALYZED = "conversation_analyzed"
    COACHING_SUGGESTION_GENERATED = "coaching_suggestion_generated"
    SENTIMENT_UPDATED = "sentiment_updated"

    # Performance Gamification Events
    CHALLENGE_CREATED = "challenge_created"
    CHALLENGE_COMPLETED = "challenge_completed"
    ACHIEVEMENT_EARNED = "achievement_earned"
    LEADERBOARD_UPDATED = "leaderboard_updated"

    # Market Intelligence Events
    MARKET_REPORT_GENERATED = "market_report_generated"
    PRICE_ALERT_TRIGGERED = "price_alert_triggered"
    INVESTMENT_OPPORTUNITY_DETECTED = "investment_opportunity_detected"
    COMPETITIVE_UPDATE = "competitive_update"

    # Mobile Intelligence Events
    MOBILE_NOTIFICATION_SENT = "mobile_notification_sent"
    VOICE_NOTE_PROCESSED = "voice_note_processed"
    AGENT_LOCATION_UPDATED = "agent_location_updated"
    OFFLINE_SYNC_COMPLETED = "offline_sync_completed"

    # Cross-service Integration Events
    LEAD_SCORE_UPDATED = "lead_score_updated"
    AGENT_PERFORMANCE_UPDATED = "agent_performance_updated"
    SYSTEM_HEALTH_CHECK = "system_health_check"
    DATA_SYNC_EVENT = "data_sync_event"


@dataclass
class Tier2Event:
    """Standardized event structure for Tier 2 services."""

    event_id: str
    event_type: EventType
    service_source: str
    timestamp: datetime
    tenant_id: str
    user_id: Optional[str]
    agent_id: Optional[str]
    lead_id: Optional[str]
    data: Dict[str, Any]
    priority: int = 3  # 1=low, 2=medium, 3=high, 4=critical
    requires_response: bool = False
    correlation_id: Optional[str] = None


class EventSubscriptionManager:
    """Manages event subscriptions for different services and dashboard components."""

    def __init__(self):
        self.subscriptions: Dict[str, Dict[EventType, List[Callable]]] = {}
        self.websocket_connections: Dict[str, Any] = {}

    def subscribe(self, subscriber_id: str, event_type: EventType, callback: Callable):
        """Subscribe to specific event types."""
        if subscriber_id not in self.subscriptions:
            self.subscriptions[subscriber_id] = {}

        if event_type not in self.subscriptions[subscriber_id]:
            self.subscriptions[subscriber_id][event_type] = []

        self.subscriptions[subscriber_id][event_type].append(callback)
        logger.info(f"Subscriber {subscriber_id} registered for {event_type.value}")

    def unsubscribe(self, subscriber_id: str, event_type: Optional[EventType] = None):
        """Unsubscribe from events."""
        if subscriber_id in self.subscriptions:
            if event_type:
                self.subscriptions[subscriber_id].pop(event_type, None)
            else:
                del self.subscriptions[subscriber_id]

    def register_websocket(self, connection_id: str, websocket):
        """Register WebSocket connection for real-time updates."""
        self.websocket_connections[connection_id] = websocket
        logger.info(f"WebSocket connection {connection_id} registered")

    def unregister_websocket(self, connection_id: str):
        """Unregister WebSocket connection."""
        self.websocket_connections.pop(connection_id, None)
        logger.info(f"WebSocket connection {connection_id} unregistered")


class Tier2WebSocketRouter:
    """Main WebSocket router for coordinating Tier 2 service events."""

    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_client = redis.Redis.from_url(redis_url)
        self.subscription_manager = EventSubscriptionManager()
        self.running = False
        self.event_queue = asyncio.Queue()
        self.metrics = {
            "events_processed": 0,
            "events_routed": 0,
            "active_subscriptions": 0,
            "websocket_connections": 0,
            "last_activity": None
        }

        # Initialize service integration
        self._initialize_service_integrations()

    def _initialize_service_integrations(self):
        """Initialize integrations with all Tier 2 services."""

        # Register for existing real-time scoring events
        self.subscribe_to_tier1_events()

        # Set up cross-service event routing
        self._setup_cross_service_routing()

    def subscribe_to_tier1_events(self):
        """Subscribe to existing Tier 1 real-time events for integration."""
        tier1_events = [
            "lead_scored",
            "property_matched",
            "prediction_generated",
            "dashboard_update"
        ]

        for event in tier1_events:
            self.subscription_manager.subscribe(
                "tier1_integration",
                EventType.DATA_SYNC_EVENT,
                self._handle_tier1_event
            )

    def _setup_cross_service_routing(self):
        """Set up event routing between Tier 2 services."""

        # Nurturing -> Routing integration
        self.subscription_manager.subscribe(
            "routing_service",
            EventType.LEAD_ROUTED,
            self._trigger_nurturing_campaign
        )

        # Conversation -> Scoring integration
        self.subscription_manager.subscribe(
            "scoring_service",
            EventType.CONVERSATION_ANALYZED,
            self._update_lead_score
        )

        # Performance -> Gamification integration
        self.subscription_manager.subscribe(
            "gamification_service",
            EventType.AGENT_PERFORMANCE_UPDATED,
            self._update_challenges
        )

        # Market -> All services integration
        self.subscription_manager.subscribe(
            "all_services",
            EventType.MARKET_REPORT_GENERATED,
            self._broadcast_market_intelligence
        )

    async def start(self):
        """Start the WebSocket router."""
        self.running = True
        logger.info("Tier 2 WebSocket Router starting...")

        # Start event processing task
        asyncio.create_task(self._process_event_queue())

        # Start Redis pub/sub listener
        asyncio.create_task(self._listen_redis_events())

        # Start health check task
        asyncio.create_task(self._health_check_loop())

        logger.info("Tier 2 WebSocket Router started successfully")

    async def stop(self):
        """Stop the WebSocket router."""
        self.running = False
        logger.info("Tier 2 WebSocket Router stopped")

    async def publish_event(self, event: Tier2Event):
        """Publish an event to the routing system."""

        # Add to processing queue
        await self.event_queue.put(event)

        # Publish to Redis for persistence and cross-service communication
        await self._publish_to_redis(event)

        # Update metrics
        self.metrics["events_processed"] += 1
        self.metrics["last_activity"] = datetime.now()

        logger.info(f"Event published: {event.event_type.value} from {event.service_source}")

    async def _process_event_queue(self):
        """Process events from the queue."""
        while self.running:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._route_event(event)
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _route_event(self, event: Tier2Event):
        """Route event to appropriate subscribers."""

        # Route to specific service subscriptions
        for subscriber_id, subscriptions in self.subscription_manager.subscriptions.items():
            if event.event_type in subscriptions:
                for callback in subscriptions[event.event_type]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in callback for {subscriber_id}: {e}")

        # Route to WebSocket connections
        await self._broadcast_to_websockets(event)

        # Update routing metrics
        self.metrics["events_routed"] += 1

    async def _broadcast_to_websockets(self, event: Tier2Event):
        """Broadcast event to all WebSocket connections."""

        if not self.subscription_manager.websocket_connections:
            return

        # Serialize event for WebSocket transmission
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "service_source": event.service_source,
            "timestamp": event.timestamp.isoformat(),
            "tenant_id": event.tenant_id,
            "data": event.data,
            "priority": event.priority
        }

        # Broadcast to all connections
        disconnected_connections = []

        for connection_id, websocket in self.subscription_manager.websocket_connections.items():
            try:
                await websocket.send(json.dumps(event_data))
            except Exception as e:
                logger.error(f"Failed to send to WebSocket {connection_id}: {e}")
                disconnected_connections.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected_connections:
            self.subscription_manager.unregister_websocket(connection_id)

    async def _publish_to_redis(self, event: Tier2Event):
        """Publish event to Redis for persistence and cross-service communication."""
        try:
            event_data = asdict(event)
            event_data["timestamp"] = event.timestamp.isoformat()
            event_data["event_type"] = event.event_type.value

            # Publish to general Tier 2 channel
            self.redis_client.publish("tier2_events", json.dumps(event_data))

            # Publish to service-specific channel
            service_channel = f"tier2_{event.service_source}_events"
            self.redis_client.publish(service_channel, json.dumps(event_data))

            # Store event for replay/debugging
            self.redis_client.lpush("tier2_event_log", json.dumps(event_data))
            self.redis_client.ltrim("tier2_event_log", 0, 1000)  # Keep last 1000 events

        except Exception as e:
            logger.error(f"Failed to publish to Redis: {e}")

    async def _listen_redis_events(self):
        """Listen for events from Redis pub/sub."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe("tier2_events")

        while self.running:
            try:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    event_data = json.loads(message["data"])
                    event = self._deserialize_event(event_data)
                    await self.event_queue.put(event)
            except Exception as e:
                logger.error(f"Error listening to Redis events: {e}")
                await asyncio.sleep(1)

    def _deserialize_event(self, event_data: Dict[str, Any]) -> Tier2Event:
        """Deserialize event data from Redis."""
        return Tier2Event(
            event_id=event_data["event_id"],
            event_type=EventType(event_data["event_type"]),
            service_source=event_data["service_source"],
            timestamp=datetime.fromisoformat(event_data["timestamp"]),
            tenant_id=event_data["tenant_id"],
            user_id=event_data.get("user_id"),
            agent_id=event_data.get("agent_id"),
            lead_id=event_data.get("lead_id"),
            data=event_data["data"],
            priority=event_data.get("priority", 3),
            requires_response=event_data.get("requires_response", False),
            correlation_id=event_data.get("correlation_id")
        )

    async def _health_check_loop(self):
        """Periodic health check and metrics update."""
        while self.running:
            try:
                # Update metrics
                self.metrics["active_subscriptions"] = len(self.subscription_manager.subscriptions)
                self.metrics["websocket_connections"] = len(self.subscription_manager.websocket_connections)

                # Publish health check event
                health_event = Tier2Event(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.SYSTEM_HEALTH_CHECK,
                    service_source="tier2_router",
                    timestamp=datetime.now(),
                    tenant_id="system",
                    user_id=None,
                    agent_id=None,
                    lead_id=None,
                    data=self.metrics.copy(),
                    priority=1
                )

                await self.publish_event(health_event)

                # Wait for next health check
                await asyncio.sleep(60)  # Every minute

            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(60)

    # Event handler methods for cross-service integration

    async def _handle_tier1_event(self, event: Tier2Event):
        """Handle events from Tier 1 services for integration."""
        logger.info(f"Integrating Tier 1 event: {event.event_type.value}")

        # Trigger relevant Tier 2 services based on Tier 1 events
        if "lead_scored" in event.data:
            # Trigger routing and nurturing
            await self._trigger_lead_routing(event)
            await self._trigger_nurturing_campaign(event)

    async def _trigger_nurturing_campaign(self, event: Tier2Event):
        """Trigger nurturing campaign based on routing event."""
        nurturing_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.NURTURING_CAMPAIGN_STARTED,
            service_source="intelligent_nurturing",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            agent_id=event.agent_id,
            lead_id=event.lead_id,
            data={"triggered_by": "routing", "campaign_type": "auto"},
            priority=3,
            correlation_id=event.event_id
        )

        await self.publish_event(nurturing_event)

    async def _trigger_lead_routing(self, event: Tier2Event):
        """Trigger lead routing based on score update."""
        routing_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LEAD_ROUTED,
            service_source="predictive_routing",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            agent_id=None,  # To be assigned by routing
            lead_id=event.lead_id,
            data={"routing_reason": "score_update", "score": event.data.get("score")},
            priority=4,  # High priority for lead routing
            correlation_id=event.event_id
        )

        await self.publish_event(routing_event)

    async def _update_lead_score(self, event: Tier2Event):
        """Update lead score based on conversation analysis."""
        score_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LEAD_SCORE_UPDATED,
            service_source="real_time_scoring",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            agent_id=event.agent_id,
            lead_id=event.lead_id,
            data={
                "score_adjustment": event.data.get("sentiment_impact", 0),
                "reason": "conversation_analysis",
                "sentiment": event.data.get("sentiment")
            },
            priority=3,
            correlation_id=event.event_id
        )

        await self.publish_event(score_event)

    async def _update_challenges(self, event: Tier2Event):
        """Update gamification challenges based on performance."""
        challenge_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.LEADERBOARD_UPDATED,
            service_source="performance_gamification",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=event.user_id,
            agent_id=event.agent_id,
            lead_id=None,
            data={"performance_metrics": event.data},
            priority=2,
            correlation_id=event.event_id
        )

        await self.publish_event(challenge_event)

    async def _broadcast_market_intelligence(self, event: Tier2Event):
        """Broadcast market intelligence to all relevant services."""
        # Send to nurturing for market-aware messaging
        nurturing_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.NURTURING_CAMPAIGN_STARTED,
            service_source="intelligent_nurturing",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=None,
            agent_id=None,
            lead_id=None,
            data={"market_update": event.data, "campaign_type": "market_alert"},
            priority=2,
            correlation_id=event.event_id
        )

        await self.publish_event(nurturing_event)

        # Send to mobile for push notifications
        mobile_event = Tier2Event(
            event_id=str(uuid.uuid4()),
            event_type=EventType.MOBILE_NOTIFICATION_SENT,
            service_source="mobile_intelligence",
            timestamp=datetime.now(),
            tenant_id=event.tenant_id,
            user_id=None,
            agent_id=None,
            lead_id=None,
            data={"notification_type": "market_alert", "market_data": event.data},
            priority=2,
            correlation_id=event.event_id
        )

        await self.publish_event(mobile_event)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current router metrics."""
        return self.metrics.copy()

    def get_event_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent event log from Redis."""
        try:
            event_logs = self.redis_client.lrange("tier2_event_log", 0, limit - 1)
            return [json.loads(log) for log in event_logs]
        except Exception as e:
            logger.error(f"Failed to get event log: {e}")
            return []


# Singleton instance
tier2_router = None

def get_tier2_websocket_router() -> Tier2WebSocketRouter:
    """Get singleton Tier 2 WebSocket router instance."""
    global tier2_router

    if tier2_router is None:
        tier2_router = Tier2WebSocketRouter()

    return tier2_router


# Helper functions for services to use

async def publish_tier2_event(
    event_type: EventType,
    service_source: str,
    tenant_id: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    lead_id: Optional[str] = None,
    priority: int = 3
):
    """Helper function for services to publish events."""

    router = get_tier2_websocket_router()

    event = Tier2Event(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        service_source=service_source,
        timestamp=datetime.now(),
        tenant_id=tenant_id,
        user_id=user_id,
        agent_id=agent_id,
        lead_id=lead_id,
        data=data,
        priority=priority
    )

    await router.publish_event(event)


def subscribe_to_tier2_events(
    subscriber_id: str,
    event_type: EventType,
    callback: Callable[[Tier2Event], None]
):
    """Helper function for services to subscribe to events."""
    router = get_tier2_websocket_router()
    router.subscription_manager.subscribe(subscriber_id, event_type, callback)


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def example_usage():
        router = get_tier2_websocket_router()
        await router.start()

        # Example event publishing
        await publish_tier2_event(
            event_type=EventType.LEAD_ROUTED,
            service_source="predictive_routing",
            tenant_id="test_tenant",
            data={"lead_id": "123", "agent_id": "agent_456"},
            priority=4
        )

        # Let it run for a bit
        await asyncio.sleep(5)
        await router.stop()

    asyncio.run(example_usage())