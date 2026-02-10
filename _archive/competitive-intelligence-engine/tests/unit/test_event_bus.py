"""
Test suite for the Enhanced Competitive Intelligence Engine Event Bus.

Tests the central event coordination system and its integration with
the competitive intelligence pipeline.

Author: Claude
Date: January 2026
"""

import asyncio
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.event_bus import (

@pytest.mark.integration
    Event, EventType, EventPriority, EventHandler, EventBus,
    get_event_bus, publish_intelligence_insight, publish_alert_event
)


class TestEvent:
    """Test Event class functionality."""
    
    def test_event_creation(self):
        """Test event creation and serialization."""
        timestamp = datetime.now(timezone.utc)
        data = {"test": "data"}
        
        event = Event(
            id="test-123",
            type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            priority=EventPriority.HIGH,
            timestamp=timestamp,
            source_system="test_system",
            data=data,
            correlation_id="corr-123"
        )
        
        assert event.id == "test-123"
        assert event.type == EventType.INTELLIGENCE_INSIGHT_CREATED
        assert event.priority == EventPriority.HIGH
        assert event.timestamp == timestamp
        assert event.source_system == "test_system"
        assert event.data == data
        assert event.correlation_id == "corr-123"
    
    def test_event_serialization(self):
        """Test event to/from dict conversion."""
        timestamp = datetime.now(timezone.utc)
        data = {"competitor_id": "comp-123", "insight": "test insight"}
        
        event = Event(
            id="test-123",
            type=EventType.PREDICTION_GENERATED,
            priority=EventPriority.MEDIUM,
            timestamp=timestamp,
            source_system="test_system",
            data=data
        )
        
        # Test to_dict
        event_dict = event.to_dict()
        
        assert event_dict["id"] == "test-123"
        assert event_dict["type"] == "PREDICTION_GENERATED"
        assert event_dict["priority"] == "medium"
        assert event_dict["timestamp"] == timestamp.isoformat()
        assert event_dict["source_system"] == "test_system"
        assert event_dict["data"] == data
        
        # Test from_dict
        reconstructed_event = Event.from_dict(event_dict)
        
        assert reconstructed_event.id == event.id
        assert reconstructed_event.type == event.type
        assert reconstructed_event.priority == event.priority
        assert reconstructed_event.timestamp == event.timestamp
        assert reconstructed_event.source_system == event.source_system
        assert reconstructed_event.data == event.data


class MockEventHandler(EventHandler):
    """Mock event handler for testing."""
    
    def __init__(self, name: str, event_types=None):
        super().__init__(
            name=name,
            event_types=event_types or [EventType.INTELLIGENCE_INSIGHT_CREATED]
        )
        self.handled_events = []
        self.should_fail = False
        self.handle_delay = 0
    
    async def handle(self, event: Event) -> bool:
        """Handle event for testing."""
        if self.handle_delay:
            await asyncio.sleep(self.handle_delay)
        
        self.handled_events.append(event)
        
        if self.should_fail:
            raise Exception("Mock handler failure")
        
        return True


@pytest.fixture
async def event_bus():
    """Create a test event bus instance."""
    # Use a test Redis URL or mock Redis
    bus = EventBus(redis_url="redis://localhost:6379/15")  # Test database
    return bus


@pytest.fixture
async def started_event_bus(event_bus):
    """Create and start an event bus for testing."""
    try:
        # Mock Redis for testing
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_pubsub = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.pubsub.return_value = mock_pubsub
            mock_redis.return_value = mock_client
            
            # Mock pubsub listen to avoid blocking
            async def mock_listen():
                # Yield some test messages then stop
                yield {"type": "subscribe"}
                await asyncio.sleep(0.1)  # Small delay
            
            mock_pubsub.listen.return_value = mock_listen()
            
            await event_bus.start()
            yield event_bus
    finally:
        try:
            await event_bus.stop()
        except:
            pass


class TestEventHandler:
    """Test EventHandler functionality."""
    
    def test_handler_creation(self):
        """Test event handler creation."""
        handler = MockEventHandler("test_handler")
        
        assert handler.name == "test_handler"
        assert EventType.INTELLIGENCE_INSIGHT_CREATED in handler.event_types
        assert not handler.is_running
        assert len(handler.handled_events) == 0
    
    @pytest.mark.asyncio
    async def test_handler_lifecycle(self):
        """Test handler start/stop lifecycle."""
        handler = MockEventHandler("test_handler")
        
        assert not handler.is_running
        
        await handler.start()
        assert handler.is_running
        
        await handler.stop()
        assert not handler.is_running


class TestEventBus:
    """Test EventBus functionality."""
    
    def test_eventbus_creation(self):
        """Test event bus creation."""
        bus = EventBus()
        
        assert bus.event_channel == "competitive_intelligence_events"
        assert bus.retry_channel == "competitive_intelligence_retries"
        assert not bus.is_running
        assert len(bus.handlers) == 0
    
    def test_handler_registration(self):
        """Test handler registration and unregistration."""
        bus = EventBus()
        handler = MockEventHandler("test_handler")
        
        # Test registration
        bus.register_handler(handler)
        
        assert "test_handler" in bus.handlers
        assert bus.handlers["test_handler"] == handler
        assert EventType.INTELLIGENCE_INSIGHT_CREATED in bus.event_type_handlers
        assert "test_handler" in bus.event_type_handlers[EventType.INTELLIGENCE_INSIGHT_CREATED]
        
        # Test duplicate registration
        with pytest.raises(ValueError, match="Handler .* is already registered"):
            bus.register_handler(handler)
        
        # Test unregistration
        bus.unregister_handler("test_handler")
        
        assert "test_handler" not in bus.handlers
        assert EventType.INTELLIGENCE_INSIGHT_CREATED not in bus.event_type_handlers
    
    @pytest.mark.asyncio
    async def test_event_publishing(self, started_event_bus):
        """Test event publishing."""
        bus = started_event_bus
        
        # Mock Redis publish
        bus.redis_client.publish = AsyncMock(return_value=1)
        
        event_id = await bus.publish(
            event_type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            data={"test": "data"},
            source_system="test_system",
            priority=EventPriority.HIGH,
            correlation_id="test-correlation"
        )
        
        assert event_id is not None
        assert len(event_id) > 0
        assert bus.events_published == 1
        
        # Verify Redis publish was called
        bus.redis_client.publish.assert_called_once()
        
        # Check published data
        call_args = bus.redis_client.publish.call_args
        channel, data = call_args[0]
        
        assert channel == "competitive_intelligence_events"
        
        event_data = json.loads(data)
        assert event_data["type"] == "INTELLIGENCE_INSIGHT_CREATED"
        assert event_data["priority"] == "high"
        assert event_data["source_system"] == "test_system"
        assert event_data["correlation_id"] == "test-correlation"
    
    @pytest.mark.asyncio
    async def test_event_handling(self, started_event_bus):
        """Test event handling with mock handler."""
        bus = started_event_bus
        handler = MockEventHandler("test_handler")
        
        # Register handler
        bus.register_handler(handler)
        await handler.start()
        
        # Create test event
        event = Event(
            id="test-123",
            type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(timezone.utc),
            source_system="test_system",
            data={"test": "data"}
        )
        
        # Handle event directly (simulate processing)
        await bus._handle_event(event)
        
        # Verify handler received event
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0].id == "test-123"
        assert handler.handled_events[0].type == EventType.INTELLIGENCE_INSIGHT_CREATED
    
    def test_metrics(self):
        """Test event bus metrics."""
        bus = EventBus()
        
        metrics = bus.get_metrics()
        
        assert "events_published" in metrics
        assert "events_processed" in metrics
        assert "events_failed" in metrics
        assert "events_retried" in metrics
        assert "active_handlers" in metrics
        assert "registered_handlers" in metrics
        assert "is_running" in metrics
        
        assert metrics["events_published"] == 0
        assert metrics["events_processed"] == 0
        assert metrics["is_running"] is False


class TestConvenienceFunctions:
    """Test convenience functions for event publishing."""
    
    @pytest.mark.asyncio
    async def test_publish_intelligence_insight(self):
        """Test intelligence insight publishing helper."""
        with patch('src.core.event_bus.get_event_bus') as mock_get_bus:
            mock_bus = AsyncMock()
            mock_bus.publish.return_value = "insight-123"
            mock_get_bus.return_value = mock_bus
            
            insight_data = {
                "insight_id": "insight-456",
                "competitor_id": "comp-789",
                "summary": "Test insight"
            }
            
            event_id = await publish_intelligence_insight(
                insight_data=insight_data,
                source_system="test_system",
                correlation_id="corr-123"
            )
            
            assert event_id == "insight-123"
            
            # Verify correct parameters
            mock_bus.publish.assert_called_once_with(
                event_type=EventType.INTELLIGENCE_INSIGHT_CREATED,
                data=insight_data,
                source_system="test_system",
                priority=EventPriority.HIGH,
                correlation_id="corr-123"
            )
    
    @pytest.mark.asyncio
    async def test_publish_alert_event(self):
        """Test alert publishing helper."""
        with patch('src.core.event_bus.get_event_bus') as mock_get_bus:
            mock_bus = AsyncMock()
            mock_bus.publish.return_value = "alert-123"
            mock_get_bus.return_value = mock_bus
            
            alert_data = {
                "alert_id": "alert-456",
                "title": "Test Alert",
                "competitor_id": "comp-789"
            }
            
            event_id = await publish_alert_event(
                alert_data=alert_data,
                source_system="test_system",
                priority=EventPriority.CRITICAL,
                correlation_id="corr-123"
            )
            
            assert event_id == "alert-123"
            
            # Verify correct parameters
            mock_bus.publish.assert_called_once_with(
                event_type=EventType.ALERT_TRIGGERED,
                data=alert_data,
                source_system="test_system",
                priority=EventPriority.CRITICAL,
                correlation_id="corr-123",
                ttl_seconds=3600
            )


class TestIntegration:
    """Integration tests for event bus components."""
    
    @pytest.mark.asyncio
    async def test_event_flow_simulation(self, started_event_bus):
        """Test a complete event flow simulation."""
        bus = started_event_bus
        
        # Create handlers for different event types
        insight_handler = MockEventHandler("insight_handler", [EventType.INTELLIGENCE_INSIGHT_CREATED])
        alert_handler = MockEventHandler("alert_handler", [EventType.ALERT_TRIGGERED])
        prediction_handler = MockEventHandler("prediction_handler", [EventType.PREDICTION_GENERATED])
        
        # Register handlers
        bus.register_handler(insight_handler)
        bus.register_handler(alert_handler)
        bus.register_handler(prediction_handler)
        
        await insight_handler.start()
        await alert_handler.start()
        await prediction_handler.start()
        
        # Simulate insight event
        insight_event = Event(
            id="insight-123",
            type=EventType.INTELLIGENCE_INSIGHT_CREATED,
            priority=EventPriority.HIGH,
            timestamp=datetime.now(timezone.utc),
            source_system="competitor_monitor",
            data={"competitor_id": "comp-123", "insight": "pricing change detected"},
            correlation_id="session-456"
        )
        
        # Simulate alert event  
        alert_event = Event(
            id="alert-123",
            type=EventType.ALERT_TRIGGERED,
            priority=EventPriority.CRITICAL,
            timestamp=datetime.now(timezone.utc),
            source_system="competitor_monitor",
            data={"alert_id": "alert-456", "title": "Critical threat detected"},
            correlation_id="session-456"
        )
        
        # Handle events
        await bus._handle_event(insight_event)
        await bus._handle_event(alert_event)
        
        # Verify handlers processed correct events
        assert len(insight_handler.handled_events) == 1
        assert insight_handler.handled_events[0].id == "insight-123"
        
        assert len(alert_handler.handled_events) == 1
        assert alert_handler.handled_events[0].id == "alert-123"
        
        assert len(prediction_handler.handled_events) == 0  # No prediction events sent
        
        # Cleanup
        await insight_handler.stop()
        await alert_handler.stop()
        await prediction_handler.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])