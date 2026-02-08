"""
Enterprise Event Streaming Service
Implements Kafka-based event-driven architecture for real-time lead processing
"""

import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for lead processing pipeline"""

    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    LEAD_SCORED = "lead.scored"
    PROPERTY_MATCHED = "property.matched"
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_UPDATED = "conversation.updated"
    ACTION_TRIGGERED = "action.triggered"
    FOLLOWUP_SCHEDULED = "followup.scheduled"
    ERROR_OCCURRED = "error.occurred"


class Priority(Enum):
    """Event processing priority levels"""

    HIGH = 1  # Hot leads, immediate actions
    MEDIUM = 2  # Warm leads, scheduled actions
    LOW = 3  # Cold leads, batch processing


@dataclass
class StreamEvent:
    """Standard event structure for the streaming platform"""

    id: str
    type: EventType
    timestamp: str
    source_service: str
    priority: Priority
    data: Dict[str, Any]
    correlation_id: str
    retry_count: int = 0
    max_retries: int = 3

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "timestamp": self.timestamp,
            "source_service": self.source_service,
            "priority": self.priority.value,
            "data": self.data,
            "correlation_id": self.correlation_id,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamEvent":
        return cls(
            id=data["id"],
            type=EventType(data["type"]),
            timestamp=data["timestamp"],
            source_service=data["source_service"],
            priority=Priority(data["priority"]),
            data=data["data"],
            correlation_id=data["correlation_id"],
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )


class EventStreamingService:
    """
    Enterprise Event Streaming Service using Kafka
    Provides real-time event processing with fault tolerance
    """

    def __init__(self):
        self.producer = None
        self.consumer = None
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False
        self.stats = {"events_published": 0, "events_consumed": 0, "errors": 0, "retries": 0}

    async def initialize(self, kafka_config: Dict[str, Any]):
        """Initialize Kafka producer and consumer with optimal settings"""
        try:
            from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
            from aiokafka.errors import KafkaError

            # Producer optimized for high throughput
            self.producer = AIOKafkaProducer(
                bootstrap_servers=kafka_config.get("bootstrap_servers", "localhost:9092"),
                value_serializer=lambda x: json.dumps(x).encode("utf-8"),
                compression_type="snappy",  # Fast compression
                batch_size=16384,  # 16KB batches for efficiency
                linger_ms=10,  # Small delay to allow batching
                acks="1",  # Wait for leader acknowledgment only
                retries=3,
                enable_idempotence=True,
            )

            # Consumer optimized for low latency
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=kafka_config.get("bootstrap_servers", "localhost:9092"),
                group_id="lead-intelligence-group",
                value_deserializer=lambda x: json.loads(x.decode("utf-8")),
                auto_offset_reset="latest",
                enable_auto_commit=False,  # Manual commit for reliability
                fetch_max_wait_ms=100,  # Low latency
                fetch_min_bytes=1,
                max_poll_records=50,  # Process in small batches
            )

            await self.producer.start()
            await self.consumer.start()

            logger.info("Event streaming service initialized successfully")

        except Exception as e:
            logger.critical(
                f"INFRASTRUCTURE FAILURE: Kafka unavailable - {e}",
                extra={"alert": True, "component": "kafka", "severity": "critical"},
            )
            # IMPORTANT: This fallback masks infrastructure issues
            # Operations should be alerted to fix Kafka before performance degrades
            await self._initialize_memory_fallback()

            # Emit alert event for monitoring systems
            await self._emit_infrastructure_alert(
                "kafka_failure",
                {"error": str(e), "fallback_mode": True, "impact": "Limited event queue capacity, potential data loss"},
            )

    async def _initialize_memory_fallback(self):
        """Fallback in-memory event system when Kafka unavailable"""
        self.memory_events = asyncio.Queue(maxsize=10000)
        self.fallback_mode = True
        logger.info("Using in-memory event fallback")

    async def publish_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        correlation_id: Optional[str] = None,
    ) -> str:
        """
        Publish event to appropriate topic based on priority
        Returns event ID for tracking
        """
        event = StreamEvent(
            id=str(uuid.uuid4()),
            type=event_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            source_service="lead-intelligence",
            priority=priority,
            data=data,
            correlation_id=correlation_id or str(uuid.uuid4()),
        )

        try:
            if hasattr(self, "fallback_mode"):
                await self.memory_events.put(event)
            else:
                topic = self._get_topic_for_priority(priority)
                await self.producer.send_and_wait(topic, event.to_dict())

            self.stats["events_published"] += 1
            logger.debug(f"Published event {event.id} of type {event_type.value}")
            return event.id

        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            self.stats["errors"] += 1
            raise

    def _get_topic_for_priority(self, priority: Priority) -> str:
        """Route events to priority-specific topics for parallel processing"""
        topic_map = {
            Priority.HIGH: "leads-high-priority",
            Priority.MEDIUM: "leads-medium-priority",
            Priority.LOW: "leads-low-priority",
        }
        return topic_map[priority]

    def register_handler(self, event_type: EventType, handler: Callable):
        """Register event handler for specific event type"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def start_consuming(self):
        """Start consuming events from all priority topics"""
        self.running = True

        if hasattr(self, "fallback_mode"):
            asyncio.create_task(self._consume_memory_events())
        else:
            # Subscribe to all priority topics
            topics = ["leads-high-priority", "leads-medium-priority", "leads-low-priority"]
            self.consumer.subscribe(topics)
            asyncio.create_task(self._consume_kafka_events())

        logger.info("Started event consumption")

    async def _consume_kafka_events(self):
        """Consume events from Kafka topics"""
        try:
            async for message in self.consumer:
                if not self.running:
                    break

                try:
                    event_data = message.value
                    event = StreamEvent.from_dict(event_data)

                    # Process event with timeout
                    await asyncio.wait_for(
                        self._process_event(event),
                        timeout=30.0,  # 30-second processing timeout
                    )

                    # Commit offset after successful processing
                    await self.consumer.commit()

                except asyncio.TimeoutError:
                    logger.error(f"Event processing timeout for {event.id}")
                    await self._handle_failed_event(event, "timeout")
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    await self._handle_failed_event(event, str(e))

        except Exception as e:
            logger.error(f"Consumer error: {e}")

    async def _consume_memory_events(self):
        """Consume events from in-memory queue (fallback mode)"""
        while self.running:
            try:
                event = await asyncio.wait_for(self.memory_events.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Memory event processing error: {e}")

    async def _process_event(self, event: StreamEvent):
        """Process individual event through registered handlers"""
        try:
            handlers = self.event_handlers.get(event.type, [])

            if not handlers:
                logger.warning(f"No handlers registered for event type {event.type.value}")
                return

            # Execute all handlers concurrently
            handler_tasks = [handler(event) for handler in handlers]
            await asyncio.gather(*handler_tasks, return_exceptions=True)

            self.stats["events_consumed"] += 1
            logger.debug(f"Processed event {event.id}")

        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            raise

    async def _handle_failed_event(self, event: StreamEvent, error: str):
        """Handle failed event processing with retry logic"""
        if event.retry_count < event.max_retries:
            event.retry_count += 1
            # Exponential backoff
            delay = 2**event.retry_count
            await asyncio.sleep(delay)

            # Re-queue for retry
            await self.publish_event(event.type, event.data, event.priority, event.correlation_id)
            self.stats["retries"] += 1
        else:
            # Send to dead letter queue
            await self._send_to_dlq(event, error)

    async def _send_to_dlq(self, event: StreamEvent, error: str):
        """Send failed events to dead letter queue for manual review"""
        dlq_event = {
            "original_event": event.to_dict(),
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            if hasattr(self, "fallback_mode"):
                logger.error(f"DLQ: {dlq_event}")
            else:
                await self.producer.send_and_wait("leads-dead-letter", dlq_event)
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")

    async def stop(self):
        """Gracefully stop event streaming service"""
        self.running = False

        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()

        logger.info("Event streaming service stopped")

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming service statistics"""
        return {
            **self.stats,
            "handlers_registered": sum(len(handlers) for handlers in self.event_handlers.values()),
            "running": self.running,
        }

    async def _emit_infrastructure_alert(self, alert_type: str, details: Dict[str, Any]):
        """Emit infrastructure failure alerts for monitoring systems."""
        alert_event = StreamEvent(
            event_type=EventType.SYSTEM_ALERT,
            data={
                "alert_type": alert_type,
                "severity": "critical",
                "component": "event_streaming",
                "timestamp": time.time(),
                "details": details,
                "requires_immediate_attention": True,
            },
            priority=StreamPriority.HIGH,
        )

        # Log the alert prominently
        logger.critical(
            f"INFRASTRUCTURE ALERT: {alert_type}", extra={"alert_data": details, "requires_ops_intervention": True}
        )

        # Try to send alert through backup channels if available
        try:
            # In a real implementation, this would:
            # 1. Send to PagerDuty/OpsGenie
            # 2. Post to Slack #alerts channel
            # 3. Send email to ops team
            # 4. Update status page
            logger.warning("Infrastructure alert emitted - ops team should be notified")
        except Exception as e:
            logger.error(f"Failed to emit infrastructure alert: {e}")


# Singleton instance
_event_streaming_service = None


async def get_event_streaming_service() -> EventStreamingService:
    """Get singleton event streaming service instance"""
    global _event_streaming_service
    if _event_streaming_service is None:
        _event_streaming_service = EventStreamingService()

        # Initialize with default config (override via environment)
        kafka_config = {"bootstrap_servers": "localhost:9092"}
        await _event_streaming_service.initialize(kafka_config)

    return _event_streaming_service


# Event handler decorators for easy registration
def event_handler(event_type: EventType):
    """Decorator to register event handlers"""

    def decorator(func):
        async def wrapper():
            service = await get_event_streaming_service()
            service.register_handler(event_type, func)

        # Register immediately
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(wrapper())
        except RuntimeError:
            # No loop running, cannot register handler immediately
            pass
        return func

    return decorator
