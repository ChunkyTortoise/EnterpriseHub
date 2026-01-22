"""
Compliance Platform - Redis Pub/Sub Event System

Production-ready event publishing and subscription system for real-time
compliance monitoring using Redis pub/sub channels.

Features:
- Async Redis with redis.asyncio
- Channel-based routing (compliance.violations, compliance.scores, etc.)
- Event serialization/deserialization with Pydantic
- Multiple handler support per event type
- Graceful shutdown with connection cleanup
- Connection pooling for high throughput
- Automatic reconnection on failure
- Comprehensive logging throughout
- Fallback behavior when Redis is unavailable
"""

import asyncio
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from uuid import uuid4
import weakref

from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class ComplianceEventType(str, Enum):
    """Compliance event types for pub/sub channels"""
    MODEL_REGISTERED = "compliance.model.registered"
    MODEL_UPDATED = "compliance.model.updated"
    ASSESSMENT_COMPLETED = "compliance.assessment.completed"
    VIOLATION_DETECTED = "compliance.violation.detected"
    VIOLATION_RESOLVED = "compliance.violation.resolved"
    SCORE_CHANGED = "compliance.score.changed"
    RISK_LEVEL_CHANGED = "compliance.risk.changed"
    REMEDIATION_STARTED = "compliance.remediation.started"
    REMEDIATION_COMPLETED = "compliance.remediation.completed"
    THRESHOLD_BREACH = "compliance.threshold.breach"
    CERTIFICATION_EXPIRING = "compliance.certification.expiring"


class ComplianceEvent(BaseModel):
    """Compliance event model for pub/sub messaging"""
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: ComplianceEventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str  # Service that generated the event
    model_id: Optional[str] = None
    model_name: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize event to JSON string"""
        data = self.model_dump()
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "ComplianceEvent":
        """Deserialize event from JSON string"""
        data = json.loads(json_str)
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['event_type'] = ComplianceEventType(data['event_type'])
        return cls(**data)

    def get_channel(self, prefix: str = "compliance") -> str:
        """Get the Redis channel for this event type"""
        # Map event types to specific channels
        channel_mapping = {
            ComplianceEventType.MODEL_REGISTERED: "models",
            ComplianceEventType.MODEL_UPDATED: "models",
            ComplianceEventType.ASSESSMENT_COMPLETED: "assessments",
            ComplianceEventType.VIOLATION_DETECTED: "violations",
            ComplianceEventType.VIOLATION_RESOLVED: "violations",
            ComplianceEventType.SCORE_CHANGED: "scores",
            ComplianceEventType.RISK_LEVEL_CHANGED: "risk",
            ComplianceEventType.REMEDIATION_STARTED: "remediations",
            ComplianceEventType.REMEDIATION_COMPLETED: "remediations",
            ComplianceEventType.THRESHOLD_BREACH: "alerts",
            ComplianceEventType.CERTIFICATION_EXPIRING: "certifications",
        }
        channel_suffix = channel_mapping.get(self.event_type, "general")
        return f"{prefix}:{channel_suffix}"


class ComplianceEventPublisher:
    """
    Publishes compliance events to Redis pub/sub channels.

    Handles connection management, event serialization, and provides
    convenience methods for common event types.
    """

    def __init__(
        self,
        redis_url: str = None,
        channel_prefix: str = "compliance",
        max_connections: int = 10,
        socket_timeout: float = 2.0,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
    ):
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379')
        self.channel_prefix = channel_prefix
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._redis: Optional[Any] = None
        self._connection_pool: Optional[Any] = None
        self._connected: bool = False
        self._lock = asyncio.Lock()

        # Metrics tracking
        self._metrics = {
            'events_published': 0,
            'events_failed': 0,
            'reconnections': 0,
            'last_published_at': None,
        }

        logger.info(
            f"ComplianceEventPublisher initialized with redis_url={self.redis_url}, "
            f"channel_prefix={self.channel_prefix}"
        )

    async def connect(self) -> bool:
        """
        Establish Redis connection with connection pooling.

        Returns:
            bool: True if connection successful, False otherwise
        """
        if self._connected and self._redis:
            return True

        async with self._lock:
            if self._connected and self._redis:
                return True

            try:
                import redis.asyncio as redis
                from redis.asyncio.connection import ConnectionPool

                self._connection_pool = ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_timeout,
                    socket_keepalive=True,
                    health_check_interval=30,
                    retry_on_timeout=True,
                    decode_responses=True,
                )

                self._redis = redis.Redis(connection_pool=self._connection_pool)

                # Test connection
                await self._redis.ping()

                self._connected = True
                logger.info(f"ComplianceEventPublisher connected to Redis at {self.redis_url}")
                return True

            except ImportError:
                logger.error(
                    "redis.asyncio not available. Install with 'pip install redis'. "
                    "Publisher will operate in fallback mode (logging only)."
                )
                self._connected = False
                return False

            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}. "
                    "Publisher will operate in fallback mode (logging only)."
                )
                self._connected = False
                return False

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup resources."""
        async with self._lock:
            if self._redis:
                try:
                    await self._redis.close()
                    logger.info("ComplianceEventPublisher disconnected from Redis")
                except Exception as e:
                    logger.warning(f"Error during Redis disconnect: {e}")
                finally:
                    self._redis = None

            if self._connection_pool:
                try:
                    await self._connection_pool.disconnect()
                except Exception as e:
                    logger.warning(f"Error during connection pool disconnect: {e}")
                finally:
                    self._connection_pool = None

            self._connected = False

    async def _ensure_connected(self) -> bool:
        """Ensure Redis connection is active, reconnect if needed."""
        if not self._connected or not self._redis:
            return await self.connect()

        try:
            await self._redis.ping()
            return True
        except Exception:
            self._connected = False
            self._metrics['reconnections'] += 1
            logger.info("Redis connection lost, attempting reconnection...")
            return await self.connect()

    async def publish(self, event: ComplianceEvent) -> int:
        """
        Publish event to appropriate Redis channel.

        Args:
            event: The compliance event to publish

        Returns:
            int: Number of subscribers that received the message (0 if failed)
        """
        channel = event.get_channel(self.channel_prefix)
        message = event.to_json()

        # Log event regardless of Redis availability
        logger.info(
            f"Publishing event: type={event.event_type.value}, "
            f"event_id={event.event_id}, channel={channel}, "
            f"model_id={event.model_id}"
        )

        # Fallback mode if Redis not available
        if not await self._ensure_connected():
            logger.warning(
                f"Redis unavailable, event logged but not published: {event.event_id}"
            )
            self._metrics['events_failed'] += 1
            return 0

        # Retry loop for publish
        for attempt in range(self.retry_attempts):
            try:
                subscriber_count = await self._redis.publish(channel, message)

                # Also publish to the "all" channel for subscribers listening to everything
                await self._redis.publish(f"{self.channel_prefix}:all", message)

                self._metrics['events_published'] += 1
                self._metrics['last_published_at'] = datetime.now(timezone.utc)

                logger.debug(
                    f"Event published successfully: event_id={event.event_id}, "
                    f"channel={channel}, subscribers={subscriber_count}"
                )
                return subscriber_count

            except Exception as e:
                logger.warning(
                    f"Publish attempt {attempt + 1}/{self.retry_attempts} failed: {e}"
                )
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay)
                    await self._ensure_connected()

        self._metrics['events_failed'] += 1
        logger.error(f"Failed to publish event after {self.retry_attempts} attempts: {event.event_id}")
        return 0

    async def publish_violation(
        self,
        model_id: str,
        model_name: str,
        violation_data: Dict[str, Any],
        source: str = "compliance_engine",
    ) -> ComplianceEvent:
        """
        Convenience method for publishing violation detected events.

        Args:
            model_id: ID of the model with violation
            model_name: Name of the model
            violation_data: Dictionary containing violation details
            source: Service that detected the violation

        Returns:
            ComplianceEvent: The published event
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.VIOLATION_DETECTED,
            source=source,
            model_id=model_id,
            model_name=model_name,
            payload=violation_data,
            metadata={
                'severity': violation_data.get('severity', 'unknown'),
                'regulation': violation_data.get('regulation', 'unknown'),
            },
        )
        await self.publish(event)
        return event

    async def publish_score_change(
        self,
        model_id: str,
        model_name: str,
        old_score: float,
        new_score: float,
        source: str = "compliance_engine",
    ) -> ComplianceEvent:
        """
        Convenience method for publishing score change events.

        Args:
            model_id: ID of the model
            model_name: Name of the model
            old_score: Previous compliance score
            new_score: New compliance score
            source: Service that detected the change

        Returns:
            ComplianceEvent: The published event
        """
        score_change = new_score - old_score
        direction = "improved" if score_change > 0 else "declined"

        event = ComplianceEvent(
            event_type=ComplianceEventType.SCORE_CHANGED,
            source=source,
            model_id=model_id,
            model_name=model_name,
            payload={
                'old_score': old_score,
                'new_score': new_score,
                'change': score_change,
                'direction': direction,
            },
            metadata={
                'significant_change': abs(score_change) >= 5.0,
                'threshold_crossed': (old_score >= 70 and new_score < 70) or
                                     (old_score < 70 and new_score >= 70),
            },
        )
        await self.publish(event)
        return event

    async def publish_threshold_breach(
        self,
        model_id: str,
        model_name: str,
        metric: str,
        value: float,
        threshold: float,
        source: str = "compliance_engine",
    ) -> ComplianceEvent:
        """
        Convenience method for publishing threshold breach events.

        Args:
            model_id: ID of the model
            model_name: Name of the model
            metric: Name of the metric that breached threshold
            value: Current value of the metric
            threshold: Threshold that was breached
            source: Service that detected the breach

        Returns:
            ComplianceEvent: The published event
        """
        breach_percentage = ((value - threshold) / threshold) * 100 if threshold != 0 else 0

        event = ComplianceEvent(
            event_type=ComplianceEventType.THRESHOLD_BREACH,
            source=source,
            model_id=model_id,
            model_name=model_name,
            payload={
                'metric': metric,
                'value': value,
                'threshold': threshold,
                'breach_amount': value - threshold,
                'breach_percentage': breach_percentage,
            },
            metadata={
                'critical': breach_percentage >= 20.0,
                'requires_immediate_action': value < 50.0 if threshold >= 70.0 else False,
            },
        )
        await self.publish(event)
        return event

    async def publish_remediation_started(
        self,
        model_id: str,
        model_name: str,
        violation_id: str,
        remediation_plan: Dict[str, Any],
        source: str = "compliance_engine",
    ) -> ComplianceEvent:
        """
        Convenience method for publishing remediation started events.

        Args:
            model_id: ID of the model being remediated
            model_name: Name of the model
            violation_id: ID of the violation being remediated
            remediation_plan: Dictionary containing remediation details
            source: Service initiating remediation

        Returns:
            ComplianceEvent: The published event
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.REMEDIATION_STARTED,
            source=source,
            model_id=model_id,
            model_name=model_name,
            payload={
                'violation_id': violation_id,
                'remediation_plan': remediation_plan,
                'estimated_completion': remediation_plan.get('estimated_completion'),
                'assigned_to': remediation_plan.get('assigned_to'),
            },
            metadata={
                'priority': remediation_plan.get('priority', 'medium'),
                'auto_remediation': remediation_plan.get('auto_remediation', False),
            },
        )
        await self.publish(event)
        return event

    async def publish_certification_expiring(
        self,
        model_id: str,
        model_name: str,
        certification_id: str,
        expiry_date: datetime,
        days_until_expiry: int,
        source: str = "compliance_engine",
    ) -> ComplianceEvent:
        """
        Convenience method for publishing certification expiring events.

        Args:
            model_id: ID of the model
            model_name: Name of the model
            certification_id: ID of the expiring certification
            expiry_date: Date when certification expires
            days_until_expiry: Number of days until expiry
            source: Service that detected the expiring certification

        Returns:
            ComplianceEvent: The published event
        """
        event = ComplianceEvent(
            event_type=ComplianceEventType.CERTIFICATION_EXPIRING,
            source=source,
            model_id=model_id,
            model_name=model_name,
            payload={
                'certification_id': certification_id,
                'expiry_date': expiry_date.isoformat(),
                'days_until_expiry': days_until_expiry,
            },
            metadata={
                'urgency': 'critical' if days_until_expiry <= 7 else
                          'high' if days_until_expiry <= 30 else
                          'medium' if days_until_expiry <= 60 else 'low',
            },
        )
        await self.publish(event)
        return event

    def get_metrics(self) -> Dict[str, Any]:
        """Get publisher metrics"""
        return {
            **self._metrics,
            'connected': self._connected,
            'redis_url': self.redis_url,
        }


# Type alias for event handlers
EventHandler = Callable[[ComplianceEvent], Any]


class ComplianceEventSubscriber:
    """
    Subscribes to compliance events from Redis pub/sub channels.

    Supports multiple handlers per event type and provides both
    selective and catch-all subscription modes.
    """

    def __init__(
        self,
        redis_url: str = None,
        channel_prefix: str = "compliance",
        max_connections: int = 10,
        socket_timeout: float = 5.0,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 30.0,
    ):
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379')
        self.channel_prefix = channel_prefix
        self.max_connections = max_connections
        self.socket_timeout = socket_timeout
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay

        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._connection_pool: Optional[Any] = None
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._all_handlers: List[EventHandler] = []
        self._running: bool = False
        self._listener_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._subscribed_channels: Set[str] = set()

        # Metrics tracking
        self._metrics = {
            'events_received': 0,
            'events_processed': 0,
            'events_failed': 0,
            'handler_errors': 0,
            'reconnections': 0,
            'last_received_at': None,
        }

        logger.info(
            f"ComplianceEventSubscriber initialized with redis_url={self.redis_url}, "
            f"channel_prefix={self.channel_prefix}"
        )

    async def connect(self) -> bool:
        """
        Establish Redis connection and create pubsub instance.

        Returns:
            bool: True if connection successful, False otherwise
        """
        async with self._lock:
            if self._redis and self._pubsub:
                return True

            try:
                import redis.asyncio as redis
                from redis.asyncio.connection import ConnectionPool

                self._connection_pool = ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    socket_timeout=self.socket_timeout,
                    socket_connect_timeout=self.socket_timeout,
                    socket_keepalive=True,
                    health_check_interval=30,
                    retry_on_timeout=True,
                    decode_responses=True,
                )

                self._redis = redis.Redis(connection_pool=self._connection_pool)

                # Test connection
                await self._redis.ping()

                # Create pubsub instance
                self._pubsub = self._redis.pubsub()

                logger.info(f"ComplianceEventSubscriber connected to Redis at {self.redis_url}")
                return True

            except ImportError:
                logger.error(
                    "redis.asyncio not available. Install with 'pip install redis'. "
                    "Subscriber cannot operate without Redis."
                )
                return False

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return False

    async def disconnect(self) -> None:
        """Close connections and cleanup resources."""
        await self.stop_listening()

        async with self._lock:
            if self._pubsub:
                try:
                    await self._pubsub.unsubscribe()
                    await self._pubsub.close()
                    logger.info("PubSub unsubscribed and closed")
                except Exception as e:
                    logger.warning(f"Error during pubsub cleanup: {e}")
                finally:
                    self._pubsub = None

            if self._redis:
                try:
                    await self._redis.close()
                except Exception as e:
                    logger.warning(f"Error during Redis disconnect: {e}")
                finally:
                    self._redis = None

            if self._connection_pool:
                try:
                    await self._connection_pool.disconnect()
                except Exception as e:
                    logger.warning(f"Error during connection pool disconnect: {e}")
                finally:
                    self._connection_pool = None

            self._subscribed_channels.clear()
            logger.info("ComplianceEventSubscriber disconnected")

    def _get_channel_for_event_type(self, event_type: ComplianceEventType) -> str:
        """Get Redis channel name for an event type."""
        # Create a temporary event to get the channel
        temp_event = ComplianceEvent(
            event_type=event_type,
            source="temp",
        )
        return temp_event.get_channel(self.channel_prefix)

    async def subscribe(
        self,
        event_types: List[ComplianceEventType],
        handler: EventHandler,
    ) -> bool:
        """
        Subscribe to specific event types with a handler callback.

        Args:
            event_types: List of event types to subscribe to
            handler: Callback function to handle events

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not await self.connect():
            logger.error("Cannot subscribe: Redis connection failed")
            return False

        async with self._lock:
            try:
                channels_to_subscribe = set()

                for event_type in event_types:
                    channel = self._get_channel_for_event_type(event_type)

                    # Register handler for this event type
                    event_key = event_type.value
                    if event_key not in self._handlers:
                        self._handlers[event_key] = []
                    if handler not in self._handlers[event_key]:
                        self._handlers[event_key].append(handler)

                    # Track channel for subscription
                    if channel not in self._subscribed_channels:
                        channels_to_subscribe.add(channel)
                        self._subscribed_channels.add(channel)

                # Subscribe to new channels
                if channels_to_subscribe:
                    await self._pubsub.subscribe(*channels_to_subscribe)
                    logger.info(f"Subscribed to channels: {channels_to_subscribe}")

                return True

            except Exception as e:
                logger.error(f"Failed to subscribe: {e}")
                return False

    async def subscribe_all(self, handler: EventHandler) -> bool:
        """
        Subscribe to all compliance events.

        Args:
            handler: Callback function to handle all events

        Returns:
            bool: True if subscription successful, False otherwise
        """
        if not await self.connect():
            logger.error("Cannot subscribe: Redis connection failed")
            return False

        async with self._lock:
            try:
                if handler not in self._all_handlers:
                    self._all_handlers.append(handler)

                # Subscribe to the "all" channel
                all_channel = f"{self.channel_prefix}:all"
                if all_channel not in self._subscribed_channels:
                    await self._pubsub.subscribe(all_channel)
                    self._subscribed_channels.add(all_channel)
                    logger.info(f"Subscribed to all events channel: {all_channel}")

                return True

            except Exception as e:
                logger.error(f"Failed to subscribe to all events: {e}")
                return False

    async def unsubscribe(
        self,
        event_types: Optional[List[ComplianceEventType]] = None,
        handler: Optional[EventHandler] = None,
    ) -> None:
        """
        Unsubscribe from specific event types or remove a handler.

        Args:
            event_types: Event types to unsubscribe from (None = all)
            handler: Specific handler to remove (None = all handlers)
        """
        async with self._lock:
            if event_types is None:
                # Unsubscribe from all
                if handler:
                    # Remove specific handler from all event types
                    for handlers in self._handlers.values():
                        if handler in handlers:
                            handlers.remove(handler)
                    if handler in self._all_handlers:
                        self._all_handlers.remove(handler)
                else:
                    # Clear all handlers
                    self._handlers.clear()
                    self._all_handlers.clear()
                    if self._pubsub:
                        await self._pubsub.unsubscribe()
                    self._subscribed_channels.clear()
            else:
                # Unsubscribe from specific event types
                for event_type in event_types:
                    event_key = event_type.value
                    if handler and event_key in self._handlers:
                        if handler in self._handlers[event_key]:
                            self._handlers[event_key].remove(handler)
                    elif event_key in self._handlers:
                        del self._handlers[event_key]

    async def start_listening(self) -> None:
        """
        Start listening for events (non-blocking, runs in background).

        This method starts the listener task and returns immediately.
        Use stop_listening() to stop the listener.
        """
        if self._running:
            logger.warning("Listener is already running")
            return

        if not await self.connect():
            logger.error("Cannot start listening: Redis connection failed")
            return

        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        logger.info("Event listener started")

    async def stop_listening(self) -> None:
        """Stop the event listener."""
        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass
            self._listener_task = None

        logger.info("Event listener stopped")

    async def _listen_loop(self) -> None:
        """Main listening loop with automatic reconnection."""
        reconnect_delay = self.reconnect_delay

        while self._running:
            try:
                async for message in self._pubsub.listen():
                    if not self._running:
                        break

                    if message['type'] == 'message':
                        await self._process_message(message)

                # Reset reconnect delay on successful operation
                reconnect_delay = self.reconnect_delay

            except asyncio.CancelledError:
                raise

            except Exception as e:
                if not self._running:
                    break

                logger.error(f"Error in listen loop: {e}")
                self._metrics['reconnections'] += 1

                # Exponential backoff for reconnection
                logger.info(f"Attempting reconnection in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, self.max_reconnect_delay)

                # Attempt to reconnect
                self._pubsub = None
                self._redis = None
                self._connection_pool = None

                if await self.connect():
                    # Re-subscribe to all channels
                    if self._subscribed_channels:
                        try:
                            await self._pubsub.subscribe(*self._subscribed_channels)
                            logger.info(f"Resubscribed to channels: {self._subscribed_channels}")
                        except Exception as sub_error:
                            logger.error(f"Failed to resubscribe: {sub_error}")

    async def _process_message(self, message: Dict[str, Any]) -> None:
        """
        Process an incoming pub/sub message.

        Args:
            message: Raw Redis pubsub message
        """
        self._metrics['events_received'] += 1

        try:
            # Parse the event from the message data
            data = message.get('data')
            if isinstance(data, bytes):
                data = data.decode('utf-8')

            event = ComplianceEvent.from_json(data)
            self._metrics['last_received_at'] = datetime.now(timezone.utc)

            logger.debug(
                f"Processing event: type={event.event_type.value}, "
                f"event_id={event.event_id}, model_id={event.model_id}"
            )

            # Find and execute handlers
            handlers_executed = 0

            # Execute specific handlers for this event type
            event_key = event.event_type.value
            if event_key in self._handlers:
                for handler in self._handlers[event_key]:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            await result
                        handlers_executed += 1
                    except Exception as handler_error:
                        logger.error(
                            f"Handler error for event {event.event_id}: {handler_error}"
                        )
                        self._metrics['handler_errors'] += 1

            # Execute "all" handlers
            for handler in self._all_handlers:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        await result
                    handlers_executed += 1
                except Exception as handler_error:
                    logger.error(
                        f"All-handler error for event {event.event_id}: {handler_error}"
                    )
                    self._metrics['handler_errors'] += 1

            if handlers_executed > 0:
                self._metrics['events_processed'] += 1
                logger.debug(
                    f"Event processed: event_id={event.event_id}, "
                    f"handlers_executed={handlers_executed}"
                )
            else:
                logger.debug(f"No handlers for event: {event.event_id}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse event JSON: {e}")
            self._metrics['events_failed'] += 1

        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            self._metrics['events_failed'] += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get subscriber metrics"""
        return {
            **self._metrics,
            'running': self._running,
            'subscribed_channels': list(self._subscribed_channels),
            'handler_count': sum(len(h) for h in self._handlers.values()) + len(self._all_handlers),
            'redis_url': self.redis_url,
        }


class ComplianceEventBus:
    """
    High-level event bus combining publisher and subscriber functionality.

    Provides a unified interface for both publishing and subscribing to
    compliance events within a single service.
    """

    def __init__(
        self,
        redis_url: str = None,
        channel_prefix: str = "compliance",
        service_name: str = "compliance_service",
    ):
        self.service_name = service_name
        self._publisher = ComplianceEventPublisher(
            redis_url=redis_url,
            channel_prefix=channel_prefix,
        )
        self._subscriber = ComplianceEventSubscriber(
            redis_url=redis_url,
            channel_prefix=channel_prefix,
        )

        logger.info(f"ComplianceEventBus initialized for service: {service_name}")

    async def start(self) -> bool:
        """Start the event bus (connect publisher and start subscriber)."""
        publisher_ok = await self._publisher.connect()
        await self._subscriber.start_listening()
        return publisher_ok

    async def stop(self) -> None:
        """Stop the event bus and cleanup resources."""
        await self._subscriber.disconnect()
        await self._publisher.disconnect()

    async def publish(self, event: ComplianceEvent) -> int:
        """Publish an event."""
        if not event.source:
            event.source = self.service_name
        return await self._publisher.publish(event)

    async def subscribe(
        self,
        event_types: List[ComplianceEventType],
        handler: EventHandler,
    ) -> bool:
        """Subscribe to specific event types."""
        return await self._subscriber.subscribe(event_types, handler)

    async def subscribe_all(self, handler: EventHandler) -> bool:
        """Subscribe to all events."""
        return await self._subscriber.subscribe_all(handler)

    # Convenience methods from publisher
    async def publish_violation(self, *args, **kwargs) -> ComplianceEvent:
        """Publish a violation detected event."""
        kwargs.setdefault('source', self.service_name)
        return await self._publisher.publish_violation(*args, **kwargs)

    async def publish_score_change(self, *args, **kwargs) -> ComplianceEvent:
        """Publish a score change event."""
        kwargs.setdefault('source', self.service_name)
        return await self._publisher.publish_score_change(*args, **kwargs)

    async def publish_threshold_breach(self, *args, **kwargs) -> ComplianceEvent:
        """Publish a threshold breach event."""
        kwargs.setdefault('source', self.service_name)
        return await self._publisher.publish_threshold_breach(*args, **kwargs)

    def get_metrics(self) -> Dict[str, Any]:
        """Get combined metrics from publisher and subscriber."""
        return {
            'service_name': self.service_name,
            'publisher': self._publisher.get_metrics(),
            'subscriber': self._subscriber.get_metrics(),
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
