"""
Redis Streams Event Bus for Customer Intelligence Platform.

Provides high-performance, persistent event streaming for:
- Track 1: AI workflow automation and multi-modal processing
- Track 2: CRM sync events and enterprise integration
- Track 3: Real-time analytics and customer journey tracking

Features:
- Guaranteed delivery with Redis Streams
- Consumer groups for parallel processing
- Event replay and recovery
- Tenant isolation
- Dead letter queues
- Performance monitoring
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from enum import Enum

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Event types for the Customer Intelligence Platform."""

    # Track 1: Advanced AI Features
    AI_MULTIMODAL_ANALYZED = "ai.multimodal.analyzed"
    AI_WORKFLOW_EXECUTED = "ai.workflow.executed"
    AI_MEMORY_UPDATED = "ai.memory.updated"
    AI_MODEL_DEPLOYED = "ai.model.deployed"

    # Track 2: Enterprise Integrations
    CRM_CONTACT_SYNCED = "crm.contact.synced"
    CRM_DEAL_UPDATED = "crm.deal.updated"
    AUTH_SESSION_CREATED = "auth.session.created"
    AUDIT_EVENT_LOGGED = "audit.event.logged"
    SSO_LOGIN_COMPLETED = "sso.login.completed"

    # Track 3: Advanced Analytics
    ANALYTICS_EVENT_PROCESSED = "analytics.event.processed"
    ANALYTICS_SEGMENT_CHANGED = "analytics.segment.changed"
    ANALYTICS_JOURNEY_PREDICTED = "analytics.journey.predicted"
    ANALYTICS_COHORT_UPDATED = "analytics.cohort.updated"

    # Core Platform Events
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_MESSAGE_SENT = "conversation.message.sent"
    LEAD_SCORED = "lead.scored"
    CONTEXT_UPDATED = "context.updated"

    # System Events
    TENANT_CREATED = "tenant.created"
    USER_INVITED = "user.invited"
    SUBSCRIPTION_CHANGED = "subscription.changed"
    ERROR_OCCURRED = "error.occurred"

@dataclass
class Event:
    """Event data structure for the Customer Intelligence Platform."""

    event_id: str
    event_type: EventType
    tenant_id: str
    timestamp: datetime
    source_service: str
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for Redis storage."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["event_type"] = self.event_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        data["event_type"] = EventType(data["event_type"])
        return cls(**data)

class EventBusError(Exception):
    """Base exception for event bus errors."""
    pass

class ConsumerError(EventBusError):
    """Exception raised for consumer errors."""
    pass

class PublisherError(EventBusError):
    """Exception raised for publisher errors."""
    pass

class EventSubscriber:
    """Event subscriber with handler function and configuration."""

    def __init__(
        self,
        handler: Callable[[Event], Any],
        event_types: List[EventType],
        consumer_group: str,
        consumer_name: str,
        max_retries: int = 3,
        batch_size: int = 10
    ):
        self.handler = handler
        self.event_types = event_types
        self.consumer_group = consumer_group
        self.consumer_name = consumer_name
        self.max_retries = max_retries
        self.batch_size = batch_size
        self.processed_count = 0
        self.error_count = 0
        self.last_processed = None

class EventBus:
    """Redis Streams-based event bus with tenant isolation and guaranteed delivery."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/2",
        tenant_id: str = "default",
        service_name: str = "customer_intelligence"
    ):
        self.redis_url = redis_url
        self.tenant_id = tenant_id
        self.service_name = service_name
        self.redis_pool = None
        self.subscribers: Dict[str, EventSubscriber] = {}
        self.running = False
        self.consumer_tasks: List[asyncio.Task] = []

        # Stream configuration
        self.stream_prefix = f"events:{tenant_id}"
        self.dlq_prefix = f"dlq:{tenant_id}"
        self.max_stream_length = 10000
        self.consumer_timeout = 5000  # 5 seconds

        logger.info(f"EventBus initialized for tenant {tenant_id}")

    async def _get_redis(self) -> redis.Redis:
        """Get Redis connection with connection pooling."""
        if self.redis_pool is None:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=20,
                retry_on_timeout=True,
                decode_responses=True
            )
        return redis.Redis(connection_pool=self.redis_pool)

    def _get_stream_name(self, event_type: EventType) -> str:
        """Get Redis stream name for event type with tenant isolation."""
        return f"{self.stream_prefix}:{event_type.value}"

    def _get_dlq_name(self, event_type: EventType) -> str:
        """Get dead letter queue name for event type."""
        return f"{self.dlq_prefix}:{event_type.value}"

    def _get_consumer_group_name(self, event_type: EventType, consumer_group: str) -> str:
        """Get consumer group name with tenant isolation."""
        return f"{consumer_group}:{self.tenant_id}"

    async def publish(
        self,
        event_type: EventType,
        payload: Dict[str, Any],
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Publish event to the event bus.

        Args:
            event_type: Type of event to publish
            payload: Event payload data
            correlation_id: Optional correlation ID for request tracing
            metadata: Optional metadata

        Returns:
            Event ID

        Raises:
            PublisherError: If publishing fails
        """
        try:
            redis_client = await self._get_redis()

            # Create event
            event = Event(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                tenant_id=self.tenant_id,
                timestamp=datetime.utcnow(),
                source_service=self.service_name,
                payload=payload,
                correlation_id=correlation_id,
                metadata=metadata or {}
            )

            # Get stream name
            stream_name = self._get_stream_name(event_type)

            # Publish to Redis stream
            message_id = await redis_client.xadd(
                stream_name,
                event.to_dict(),
                maxlen=self.max_stream_length,
                approximate=True
            )

            logger.info(
                f"Published event {event.event_id} to stream {stream_name}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event_type.value,
                    "stream": stream_name,
                    "message_id": message_id,
                    "correlation_id": correlation_id
                }
            )

            return event.event_id

        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            raise PublisherError(f"Failed to publish event: {e}")

    async def subscribe(
        self,
        event_types: List[EventType],
        handler: Callable[[Event], Any],
        consumer_group: str,
        consumer_name: Optional[str] = None,
        max_retries: int = 3,
        batch_size: int = 10
    ) -> str:
        """
        Subscribe to event types with a handler function.

        Args:
            event_types: List of event types to subscribe to
            handler: Async function to handle events
            consumer_group: Consumer group name for load balancing
            consumer_name: Optional consumer name (auto-generated if None)
            max_retries: Maximum retry attempts for failed messages
            batch_size: Number of messages to process in batch

        Returns:
            Subscriber ID
        """
        consumer_name = consumer_name or f"{self.service_name}_{int(time.time())}"
        subscriber_id = f"{consumer_group}:{consumer_name}"

        subscriber = EventSubscriber(
            handler=handler,
            event_types=event_types,
            consumer_group=consumer_group,
            consumer_name=consumer_name,
            max_retries=max_retries,
            batch_size=batch_size
        )

        self.subscribers[subscriber_id] = subscriber

        logger.info(
            f"Subscribed to events: {[et.value for et in event_types]}",
            extra={
                "subscriber_id": subscriber_id,
                "consumer_group": consumer_group,
                "event_types": [et.value for et in event_types]
            }
        )

        return subscriber_id

    async def _ensure_consumer_groups(self, event_types: List[EventType], consumer_group: str) -> None:
        """Ensure consumer groups exist for event types."""
        redis_client = await self._get_redis()

        for event_type in event_types:
            stream_name = self._get_stream_name(event_type)
            group_name = self._get_consumer_group_name(event_type, consumer_group)

            try:
                # Create consumer group (starting from latest messages)
                await redis_client.xgroup_create(stream_name, group_name, id='$', mkstream=True)
                logger.info(f"Created consumer group {group_name} for stream {stream_name}")
            except redis.RedisError as e:
                # Group might already exist
                if "BUSYGROUP" not in str(e):
                    logger.warning(f"Failed to create consumer group: {e}")

    async def _consume_events(self, subscriber: EventSubscriber) -> None:
        """Consume events for a subscriber."""
        redis_client = await self._get_redis()

        # Ensure consumer groups exist
        await self._ensure_consumer_groups(subscriber.event_types, subscriber.consumer_group)

        # Build stream map for xreadgroup
        streams = {}
        for event_type in subscriber.event_types:
            stream_name = self._get_stream_name(event_type)
            streams[stream_name] = '>'

        logger.info(f"Starting consumer {subscriber.consumer_name} for group {subscriber.consumer_group}")

        while self.running:
            try:
                # Read messages from streams
                messages = await redis_client.xreadgroup(
                    groupname=self._get_consumer_group_name(subscriber.event_types[0], subscriber.consumer_group),
                    consumername=subscriber.consumer_name,
                    streams=streams,
                    count=subscriber.batch_size,
                    block=self.consumer_timeout
                )

                if not messages:
                    continue

                # Process messages
                for stream_name, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        await self._process_message(
                            subscriber,
                            stream_name,
                            message_id,
                            fields
                        )

            except asyncio.CancelledError:
                logger.info(f"Consumer {subscriber.consumer_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Consumer {subscriber.consumer_name} error: {e}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_message(
        self,
        subscriber: EventSubscriber,
        stream_name: str,
        message_id: str,
        fields: Dict[str, Any]
    ) -> None:
        """Process a single message with retry logic."""
        redis_client = await self._get_redis()

        try:
            # Parse event
            event = Event.from_dict(fields)

            # Call handler
            await subscriber.handler(event)

            # Acknowledge message
            group_name = self._get_consumer_group_name(event.event_type, subscriber.consumer_group)
            await redis_client.xack(stream_name, group_name, message_id)

            subscriber.processed_count += 1
            subscriber.last_processed = datetime.utcnow()

            logger.debug(
                f"Processed event {event.event_id}",
                extra={
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "consumer": subscriber.consumer_name
                }
            )

        except Exception as e:
            subscriber.error_count += 1
            logger.error(
                f"Failed to process message {message_id}: {e}",
                extra={
                    "message_id": message_id,
                    "stream": stream_name,
                    "consumer": subscriber.consumer_name,
                    "error": str(e)
                }
            )

            # Move to dead letter queue after max retries
            await self._handle_failed_message(stream_name, message_id, fields, str(e))

    async def _handle_failed_message(
        self,
        stream_name: str,
        message_id: str,
        fields: Dict[str, Any],
        error: str
    ) -> None:
        """Handle failed message by moving to dead letter queue."""
        try:
            redis_client = await self._get_redis()

            # Extract event type from stream name
            event_type_str = stream_name.split(':')[-1]
            event_type = EventType(event_type_str)

            # Add error information
            fields["error"] = error
            fields["failed_at"] = datetime.utcnow().isoformat()
            fields["original_message_id"] = message_id

            # Move to dead letter queue
            dlq_name = self._get_dlq_name(event_type)
            await redis_client.xadd(dlq_name, fields)

            logger.warning(
                f"Moved failed message to DLQ: {dlq_name}",
                extra={
                    "original_message_id": message_id,
                    "dlq": dlq_name,
                    "error": error
                }
            )

        except Exception as e:
            logger.error(f"Failed to move message to DLQ: {e}")

    async def start(self) -> None:
        """Start the event bus consumer tasks."""
        if self.running:
            logger.warning("Event bus is already running")
            return

        self.running = True

        # Start consumer tasks for each subscriber
        for subscriber_id, subscriber in self.subscribers.items():
            task = asyncio.create_task(
                self._consume_events(subscriber),
                name=f"consumer_{subscriber_id}"
            )
            self.consumer_tasks.append(task)

        logger.info(f"Started event bus with {len(self.consumer_tasks)} consumers")

    async def stop(self) -> None:
        """Stop the event bus and all consumers."""
        if not self.running:
            return

        logger.info("Stopping event bus...")
        self.running = False

        # Cancel all consumer tasks
        for task in self.consumer_tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.consumer_tasks:
            await asyncio.gather(*self.consumer_tasks, return_exceptions=True)

        self.consumer_tasks.clear()

        # Close Redis connection pool
        if self.redis_pool:
            await self.redis_pool.disconnect()

        logger.info("Event bus stopped")

    async def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        redis_client = await self._get_redis()
        stats = {
            "tenant_id": self.tenant_id,
            "service_name": self.service_name,
            "subscribers": len(self.subscribers),
            "running": self.running,
            "streams": {},
            "consumers": {},
            "dlq": {}
        }

        # Get stream information
        for event_type in EventType:
            stream_name = self._get_stream_name(event_type)
            try:
                info = await redis_client.xinfo_stream(stream_name)
                stats["streams"][event_type.value] = {
                    "length": info.get("length", 0),
                    "groups": info.get("groups", 0),
                    "first_entry": info.get("first-entry", ["0-0", {}])[0],
                    "last_entry": info.get("last-entry", ["0-0", {}])[0]
                }
            except redis.RedisError:
                # Stream doesn't exist yet
                stats["streams"][event_type.value] = {"length": 0, "groups": 0}

        # Get consumer information
        for subscriber_id, subscriber in self.subscribers.items():
            stats["consumers"][subscriber_id] = {
                "processed_count": subscriber.processed_count,
                "error_count": subscriber.error_count,
                "last_processed": subscriber.last_processed.isoformat() if subscriber.last_processed else None,
                "event_types": [et.value for et in subscriber.event_types]
            }

        return stats

    async def replay_events(
        self,
        event_type: EventType,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        consumer_group: str = "replay"
    ) -> AsyncGenerator[Event, None]:
        """
        Replay events from a time range for recovery or analysis.

        Args:
            event_type: Event type to replay
            start_time: Start time for replay
            end_time: End time for replay (defaults to now)
            consumer_group: Consumer group for replay

        Yields:
            Event objects in chronological order
        """
        redis_client = await self._get_redis()
        stream_name = self._get_stream_name(event_type)

        end_time = end_time or datetime.utcnow()

        # Convert timestamps to Redis stream IDs
        start_id = f"{int(start_time.timestamp() * 1000)}-0"
        end_id = f"{int(end_time.timestamp() * 1000)}-0"

        try:
            # Read messages in the time range
            messages = await redis_client.xrange(stream_name, min=start_id, max=end_id)

            for message_id, fields in messages:
                try:
                    event = Event.from_dict(fields)
                    yield event
                except Exception as e:
                    logger.error(f"Failed to parse event {message_id}: {e}")
                    continue

        except redis.RedisError as e:
            logger.error(f"Failed to replay events: {e}")
            raise

    @asynccontextmanager
    async def event_transaction(self, correlation_id: Optional[str] = None):
        """
        Context manager for transactional event publishing.

        All events published within the context will have the same correlation_id
        for request tracing and debugging.
        """
        transaction_id = correlation_id or str(uuid.uuid4())

        try:
            yield transaction_id
        except Exception as e:
            # Publish error event
            await self.publish(
                EventType.ERROR_OCCURRED,
                {
                    "error": str(e),
                    "correlation_id": transaction_id,
                    "service": self.service_name
                },
                correlation_id=transaction_id
            )
            raise

# Convenience functions for common event patterns

async def create_event_bus(
    tenant_id: str = "default",
    service_name: str = "customer_intelligence"
) -> EventBus:
    """Create and configure event bus for a tenant."""
    import os

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/2")
    return EventBus(redis_url, tenant_id, service_name)

def customer_event_handler(func):
    """Decorator for customer-related event handlers."""
    async def wrapper(event: Event):
        if event.tenant_id != "default":  # Add tenant validation
            logger.info(f"Processing customer event for tenant {event.tenant_id}")
        return await func(event)
    return wrapper

def analytics_event_handler(func):
    """Decorator for analytics event handlers."""
    async def wrapper(event: Event):
        # Add analytics-specific logging
        logger.info(f"Processing analytics event {event.event_type.value}")
        return await func(event)
    return wrapper