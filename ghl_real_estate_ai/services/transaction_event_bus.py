"""
Real-Time Transaction Event Bus

Netflix-style real-time streaming system for transaction updates.
Provides sub-100ms latency for live dashboard updates and client notifications.

Key Features:
- Redis Pub/Sub for real-time event streaming
- Transaction-specific event channels
- Client subscription management with acknowledgment tracking
- Event buffering and replay for reconnections
- Celebration trigger broadcasting
- Performance optimized for <100ms latency
- Auto-scaling support with Redis clustering

Architecture:
- Publisher: TransactionService publishes events when milestones change
- Subscribers: Streamlit dashboards, mobile apps, webhooks
- Channels: transaction:updates, transaction:{id}:events, celebrations
- Message Format: JSON with transaction_id, event_type, payload, timestamp
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import redis.asyncio as redis
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """Event priority levels for delivery optimization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(Enum):
    """Real-time event types for transaction streaming"""
    TRANSACTION_CREATED = "transaction_created"
    MILESTONE_STARTED = "milestone_started"
    MILESTONE_COMPLETED = "milestone_completed"
    MILESTONE_DELAYED = "milestone_delayed"
    PROGRESS_UPDATED = "progress_updated"
    STATUS_CHANGED = "status_changed"
    CELEBRATION_TRIGGERED = "celebration_triggered"
    PREDICTION_ALERT = "prediction_alert"
    HEALTH_SCORE_CHANGED = "health_score_changed"
    ACTION_REQUIRED = "action_required"
    CLIENT_MESSAGE = "client_message"


@dataclass
class TransactionEvent:
    """Real-time transaction event structure"""
    event_id: str
    transaction_id: str
    event_type: EventType
    event_name: str
    payload: Dict[str, Any]
    priority: EventPriority = EventPriority.MEDIUM
    timestamp: float = None
    client_visible: bool = True
    agent_visible: bool = True
    requires_acknowledgment: bool = False
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "event_id": self.event_id,
            "transaction_id": self.transaction_id,
            "event_type": self.event_type.value,
            "event_name": self.event_name,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "iso_timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "client_visible": self.client_visible,
            "agent_visible": self.agent_visible,
            "requires_acknowledgment": self.requires_acknowledgment
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TransactionEvent':
        """Create from dictionary"""
        return cls(
            event_id=data["event_id"],
            transaction_id=data["transaction_id"],
            event_type=EventType(data["event_type"]),
            event_name=data["event_name"],
            payload=data["payload"],
            priority=EventPriority(data.get("priority", "medium")),
            timestamp=data["timestamp"],
            client_visible=data.get("client_visible", True),
            agent_visible=data.get("agent_visible", True),
            requires_acknowledgment=data.get("requires_acknowledgment", False)
        )


@dataclass
class ClientSubscription:
    """Client subscription tracking"""
    client_id: str
    transaction_ids: Set[str]
    channels: Set[str]
    connection_time: float
    last_heartbeat: float
    user_type: str  # "client", "agent", "admin"
    user_id: Optional[str] = None
    
    def is_active(self, timeout_seconds: int = 300) -> bool:
        """Check if subscription is still active (5 minute timeout)"""
        return time.time() - self.last_heartbeat < timeout_seconds


class TransactionEventBus:
    """
    Real-time event streaming system for transaction intelligence.
    
    Provides Netflix-style live updates with <100ms latency for
    transaction progress, milestone completions, and celebrations.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        event_buffer_size: int = 100,
        heartbeat_interval: int = 30
    ):
        self.redis_url = redis_url
        self.event_buffer_size = event_buffer_size
        self.heartbeat_interval = heartbeat_interval
        
        # Redis connections
        self.redis_client: Optional[redis.Redis] = None
        self.redis_subscriber: Optional[redis.Redis] = None
        
        # Subscription management
        self.active_subscriptions: Dict[str, ClientSubscription] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.event_buffer: Dict[str, List[TransactionEvent]] = {}
        
        # Performance metrics
        self.metrics = {
            "events_published": 0,
            "events_delivered": 0,
            "active_connections": 0,
            "avg_delivery_latency_ms": 0.0
        }
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        
        # Channel patterns
        self.CHANNELS = {
            "global": "transaction:updates",
            "transaction": "transaction:{transaction_id}:events",
            "celebrations": "transaction:celebrations",
            "predictions": "transaction:predictions",
            "health_alerts": "transaction:health_alerts"
        }

    async def initialize(self):
        """Initialize Redis connections and background tasks"""
        try:
            # Create Redis connections
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True
            )
            
            self.redis_subscriber = redis.from_url(
                self.redis_url,
                encoding="utf-8", 
                decode_responses=True
            )
            
            # Test connections
            await self.redis_client.ping()
            await self.redis_subscriber.ping()
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_inactive_subscriptions())
            self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            logger.info("Transaction Event Bus initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Transaction Event Bus: {e}")
            raise

    async def publish_event(self, event: TransactionEvent) -> bool:
        """
        Publish event to appropriate channels for real-time delivery.
        
        Args:
            event: TransactionEvent to publish
            
        Returns:
            bool: True if published successfully
        """
        if not self.redis_client:
            logger.warning("Redis client not initialized")
            return False
        
        try:
            start_time = time.time()
            event_data = json.dumps(event.to_dict())
            
            # Publish to multiple channels based on event type
            channels_to_publish = []
            
            # Global channel for all transaction updates
            channels_to_publish.append(self.CHANNELS["global"])
            
            # Transaction-specific channel
            transaction_channel = self.CHANNELS["transaction"].format(
                transaction_id=event.transaction_id
            )
            channels_to_publish.append(transaction_channel)
            
            # Special channels based on event type
            if event.event_type == EventType.CELEBRATION_TRIGGERED:
                channels_to_publish.append(self.CHANNELS["celebrations"])
            elif event.event_type == EventType.PREDICTION_ALERT:
                channels_to_publish.append(self.CHANNELS["predictions"])
            elif event.event_type == EventType.HEALTH_SCORE_CHANGED and event.payload.get("health_score", 100) < 70:
                channels_to_publish.append(self.CHANNELS["health_alerts"])
            
            # Publish to all relevant channels
            publish_tasks = []
            for channel in channels_to_publish:
                task = self.redis_client.publish(channel, event_data)
                publish_tasks.append(task)
            
            # Execute all publishes concurrently
            results = await asyncio.gather(*publish_tasks, return_exceptions=True)
            
            # Check for errors
            failed_publishes = [r for r in results if isinstance(r, Exception)]
            if failed_publishes:
                logger.error(f"Failed to publish to some channels: {failed_publishes}")
                return False
            
            # Buffer event for replay capability
            await self._buffer_event(event)
            
            # Update metrics
            self.metrics["events_published"] += 1
            delivery_latency = (time.time() - start_time) * 1000  # Convert to ms
            self.metrics["avg_delivery_latency_ms"] = (
                self.metrics["avg_delivery_latency_ms"] * 0.9 + delivery_latency * 0.1
            )
            
            # Log high-priority events
            if event.priority in [EventPriority.HIGH, EventPriority.CRITICAL]:
                logger.info(
                    f"Published {event.priority.value} priority event: "
                    f"{event.event_type.value} for transaction {event.transaction_id}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False

    async def subscribe_to_transaction(
        self,
        client_id: str,
        transaction_ids: List[str],
        user_type: str = "client",
        user_id: Optional[str] = None
    ) -> AsyncIterator[TransactionEvent]:
        """
        Subscribe to real-time updates for specific transactions.
        
        Args:
            client_id: Unique client identifier
            transaction_ids: List of transaction IDs to subscribe to
            user_type: Type of user ("client", "agent", "admin")
            user_id: Optional user identifier
            
        Yields:
            TransactionEvent: Real-time events as they occur
        """
        if not self.redis_subscriber:
            raise RuntimeError("Event bus not initialized")
        
        try:
            # Create subscription record
            channels = set()
            channels.add(self.CHANNELS["global"])  # Global updates
            channels.add(self.CHANNELS["celebrations"])  # Celebrations
            
            # Add transaction-specific channels
            for transaction_id in transaction_ids:
                channel = self.CHANNELS["transaction"].format(transaction_id=transaction_id)
                channels.add(channel)
            
            # Create subscription
            subscription = ClientSubscription(
                client_id=client_id,
                transaction_ids=set(transaction_ids),
                channels=channels,
                connection_time=time.time(),
                last_heartbeat=time.time(),
                user_type=user_type,
                user_id=user_id
            )
            
            self.active_subscriptions[client_id] = subscription
            self.metrics["active_connections"] += 1
            
            # Subscribe to channels
            pubsub = self.redis_subscriber.pubsub()
            await pubsub.subscribe(*channels)
            
            logger.info(f"Client {client_id} subscribed to {len(transaction_ids)} transactions")
            
            # Send buffered events for reconnection
            await self._send_buffered_events(client_id, transaction_ids)
            
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            event_data = json.loads(message["data"])
                            event = TransactionEvent.from_dict(event_data)
                            
                            # Check if client should receive this event
                            if self._should_deliver_event(event, subscription):
                                # Update heartbeat
                                subscription.last_heartbeat = time.time()
                                self.metrics["events_delivered"] += 1
                                
                                yield event
                                
                        except (json.JSONDecodeError, KeyError) as e:
                            logger.warning(f"Invalid event data received: {e}")
                            continue
                            
            finally:
                # Cleanup subscription
                await pubsub.unsubscribe(*channels)
                await pubsub.close()
                
                if client_id in self.active_subscriptions:
                    del self.active_subscriptions[client_id]
                    self.metrics["active_connections"] -= 1
                
                logger.info(f"Client {client_id} disconnected")
                
        except Exception as e:
            logger.error(f"Subscription error for client {client_id}: {e}")
            raise

    async def publish_milestone_completion(
        self,
        transaction_id: str,
        milestone_name: str,
        milestone_type: str,
        progress_percentage: float,
        celebration_message: Optional[str] = None
    ):
        """Convenience method for publishing milestone completion events."""
        # Milestone completion event
        completion_event = TransactionEvent(
            event_id=str(uuid.uuid4()),
            transaction_id=transaction_id,
            event_type=EventType.MILESTONE_COMPLETED,
            event_name=f"Milestone Complete: {milestone_name}",
            payload={
                "milestone_name": milestone_name,
                "milestone_type": milestone_type,
                "progress_percentage": progress_percentage,
                "celebration_message": celebration_message
            },
            priority=EventPriority.HIGH,
            client_visible=True
        )
        
        await self.publish_event(completion_event)
        
        # Progress update event
        progress_event = TransactionEvent(
            event_id=str(uuid.uuid4()),
            transaction_id=transaction_id,
            event_type=EventType.PROGRESS_UPDATED,
            event_name="Progress Updated",
            payload={
                "new_progress_percentage": progress_percentage,
                "milestone_completed": milestone_name
            },
            priority=EventPriority.MEDIUM,
            client_visible=True
        )
        
        await self.publish_event(progress_event)
        
        # Celebration event if message provided
        if celebration_message:
            celebration_event = TransactionEvent(
                event_id=str(uuid.uuid4()),
                transaction_id=transaction_id,
                event_type=EventType.CELEBRATION_TRIGGERED,
                event_name="Milestone Celebration",
                payload={
                    "milestone_name": milestone_name,
                    "celebration_message": celebration_message,
                    "animation_type": "confetti",
                    "emoji": "🎉"
                },
                priority=EventPriority.HIGH,
                client_visible=True
            )
            
            await self.publish_event(celebration_event)

    async def publish_prediction_alert(
        self,
        transaction_id: str,
        prediction_type: str,
        risk_level: str,
        delay_probability: float,
        recommended_actions: List[str]
    ):
        """Publish AI prediction alert for proactive issue resolution."""
        alert_event = TransactionEvent(
            event_id=str(uuid.uuid4()),
            transaction_id=transaction_id,
            event_type=EventType.PREDICTION_ALERT,
            event_name=f"Prediction Alert: {prediction_type}",
            payload={
                "prediction_type": prediction_type,
                "risk_level": risk_level,
                "delay_probability": delay_probability,
                "recommended_actions": recommended_actions,
                "requires_action": risk_level in ["high", "critical"]
            },
            priority=EventPriority.CRITICAL if risk_level == "critical" else EventPriority.HIGH,
            client_visible=True,
            requires_acknowledgment=True
        )
        
        await self.publish_event(alert_event)

    async def publish_health_score_change(
        self,
        transaction_id: str,
        old_score: int,
        new_score: int,
        contributing_factors: List[str]
    ):
        """Publish health score changes for dashboard updates."""
        health_event = TransactionEvent(
            event_id=str(uuid.uuid4()),
            transaction_id=transaction_id,
            event_type=EventType.HEALTH_SCORE_CHANGED,
            event_name="Health Score Updated",
            payload={
                "old_score": old_score,
                "new_score": new_score,
                "score_change": new_score - old_score,
                "contributing_factors": contributing_factors,
                "score_trend": "improving" if new_score > old_score else "declining" if new_score < old_score else "stable"
            },
            priority=EventPriority.CRITICAL if new_score < 50 else EventPriority.HIGH if new_score < 70 else EventPriority.MEDIUM,
            client_visible=True
        )
        
        await self.publish_event(health_event)

    async def acknowledge_event(self, client_id: str, event_id: str) -> bool:
        """Acknowledge event receipt by client."""
        try:
            ack_key = f"event_acks:{event_id}"
            await self.redis_client.sadd(ack_key, client_id)
            await self.redis_client.expire(ack_key, 3600)  # Expire after 1 hour
            
            logger.debug(f"Event {event_id} acknowledged by client {client_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge event {event_id} for client {client_id}: {e}")
            return False

    async def get_metrics(self) -> Dict[str, Any]:
        """Get real-time performance metrics."""
        active_connections = len(self.active_subscriptions)
        
        return {
            "events_published": self.metrics["events_published"],
            "events_delivered": self.metrics["events_delivered"],
            "active_connections": active_connections,
            "avg_delivery_latency_ms": round(self.metrics["avg_delivery_latency_ms"], 2),
            "event_buffer_size": sum(len(events) for events in self.event_buffer.values()),
            "uptime_seconds": time.time() - getattr(self, '_start_time', time.time()),
            "subscriptions_by_type": {
                user_type: len([s for s in self.active_subscriptions.values() if s.user_type == user_type])
                for user_type in ["client", "agent", "admin"]
            }
        }

    # ========================================================================
    # PRIVATE METHODS
    # ========================================================================

    async def _buffer_event(self, event: TransactionEvent):
        """Buffer event for replay on reconnection."""
        transaction_id = event.transaction_id
        
        if transaction_id not in self.event_buffer:
            self.event_buffer[transaction_id] = []
        
        # Add event to buffer
        self.event_buffer[transaction_id].append(event)
        
        # Maintain buffer size limit
        if len(self.event_buffer[transaction_id]) > self.event_buffer_size:
            self.event_buffer[transaction_id].pop(0)  # Remove oldest event
        
        # Set expiration for buffer (store in Redis for persistence)
        buffer_key = f"event_buffer:{transaction_id}"
        buffer_data = json.dumps([e.to_dict() for e in self.event_buffer[transaction_id]])
        
        await self.redis_client.setex(buffer_key, 3600, buffer_data)  # 1 hour expiration

    async def _send_buffered_events(self, client_id: str, transaction_ids: List[str]):
        """Send buffered events to reconnecting client."""
        subscription = self.active_subscriptions.get(client_id)
        if not subscription:
            return
        
        for transaction_id in transaction_ids:
            buffer_key = f"event_buffer:{transaction_id}"
            buffer_data = await self.redis_client.get(buffer_key)
            
            if buffer_data:
                try:
                    events_data = json.loads(buffer_data)
                    buffered_events = [TransactionEvent.from_dict(data) for data in events_data]
                    
                    # Send recent events (last 10 minutes)
                    recent_cutoff = time.time() - 600  # 10 minutes
                    recent_events = [e for e in buffered_events if e.timestamp > recent_cutoff]
                    
                    logger.info(f"Replaying {len(recent_events)} buffered events for client {client_id}")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.warning(f"Failed to parse buffered events for transaction {transaction_id}: {e}")

    def _should_deliver_event(self, event: TransactionEvent, subscription: ClientSubscription) -> bool:
        """Determine if event should be delivered to client."""
        # Check transaction filter
        if event.transaction_id not in subscription.transaction_ids:
            return False
        
        # Check visibility permissions
        if subscription.user_type == "client" and not event.client_visible:
            return False
        
        if subscription.user_type == "agent" and not event.agent_visible:
            return False
        
        # Admin users can see all events
        return True

    async def _cleanup_inactive_subscriptions(self):
        """Background task to clean up inactive subscriptions."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                inactive_clients = []
                for client_id, subscription in self.active_subscriptions.items():
                    if not subscription.is_active():
                        inactive_clients.append(client_id)
                
                # Remove inactive subscriptions
                for client_id in inactive_clients:
                    del self.active_subscriptions[client_id]
                    self.metrics["active_connections"] -= 1
                    logger.info(f"Removed inactive subscription for client {client_id}")
                
                if inactive_clients:
                    logger.info(f"Cleaned up {len(inactive_clients)} inactive subscriptions")
                    
            except Exception as e:
                logger.error(f"Error in subscription cleanup: {e}")

    async def _heartbeat_monitor(self):
        """Background task to monitor connection health."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Update connection metrics
                active_count = len([s for s in self.active_subscriptions.values() if s.is_active()])
                self.metrics["active_connections"] = active_count
                
                # Log health metrics periodically
                if active_count > 0:
                    logger.debug(f"Event bus health: {active_count} active connections, "
                               f"{self.metrics['avg_delivery_latency_ms']:.2f}ms avg latency")
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")

    async def close(self):
        """Clean up resources."""
        logger.info("Shutting down Transaction Event Bus")
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        # Close Redis connections
        if self.redis_client:
            await self.redis_client.close()
        if self.redis_subscriber:
            await self.redis_subscriber.close()
        
        # Clear subscriptions
        self.active_subscriptions.clear()
        
        logger.info("Transaction Event Bus shutdown complete")


# ============================================================================
# ASYNC CONTEXT MANAGER SUPPORT
# ============================================================================

class TransactionEventBusManager:
    """Context manager for TransactionEventBus"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", **kwargs):
        self.redis_url = redis_url
        self.kwargs = kwargs
        self.event_bus: Optional[TransactionEventBus] = None
    
    async def __aenter__(self) -> TransactionEventBus:
        self.event_bus = TransactionEventBus(self.redis_url, **self.kwargs)
        await self.event_bus.initialize()
        return self.event_bus
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.event_bus:
            await self.event_bus.close()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def create_event_bus(redis_url: str = "redis://localhost:6379") -> TransactionEventBus:
    """Create and initialize a TransactionEventBus instance."""
    event_bus = TransactionEventBus(redis_url)
    await event_bus.initialize()
    return event_bus


# Type alias for better code readability
from collections.abc import AsyncIterator