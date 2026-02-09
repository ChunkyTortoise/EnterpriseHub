"""
Tests for Compliance Event Publisher and Subscriber

Tests cover:
- Event creation and serialization
- Publisher connection and publish operations
- Subscriber connection and event handling
- Fallback behavior when Redis unavailable
- Convenience methods for common events
- EventBus combined functionality
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.compliance_platform.realtime.event_publisher import (
    ComplianceEvent,
    ComplianceEventBus,
    ComplianceEventPublisher,
    ComplianceEventSubscriber,
    ComplianceEventType,
)


class TestComplianceEvent:
    """Tests for ComplianceEvent model"""

    def test_event_creation_with_defaults(self):
        """Test creating an event with default values"""
        event = ComplianceEvent(
            event_type=ComplianceEventType.VIOLATION_DETECTED,
            source="test_service",
        )

        assert event.event_id is not None
        assert event.event_type == ComplianceEventType.VIOLATION_DETECTED
        assert event.source == "test_service"
        assert event.timestamp is not None
        assert event.payload == {}
        assert event.metadata == {}

    def test_event_creation_with_all_fields(self):
        """Test creating an event with all fields populated"""
        now = datetime.now(timezone.utc)
        event = ComplianceEvent(
            event_id="test-event-123",
            event_type=ComplianceEventType.SCORE_CHANGED,
            timestamp=now,
            source="compliance_engine",
            model_id="model-456",
            model_name="Lead Scoring Model",
            payload={"old_score": 85.0, "new_score": 92.0},
            metadata={"significant": True},
        )

        assert event.event_id == "test-event-123"
        assert event.event_type == ComplianceEventType.SCORE_CHANGED
        assert event.timestamp == now
        assert event.model_id == "model-456"
        assert event.model_name == "Lead Scoring Model"
        assert event.payload["old_score"] == 85.0
        assert event.metadata["significant"] is True

    def test_event_to_json_serialization(self):
        """Test event serialization to JSON"""
        event = ComplianceEvent(
            event_type=ComplianceEventType.VIOLATION_DETECTED,
            source="test_service",
            model_id="model-123",
            payload={"severity": "high"},
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_type"] == "compliance.violation.detected"
        assert data["source"] == "test_service"
        assert data["model_id"] == "model-123"
        assert data["payload"]["severity"] == "high"
        assert "timestamp" in data

    def test_event_from_json_deserialization(self):
        """Test event deserialization from JSON"""
        original = ComplianceEvent(
            event_type=ComplianceEventType.THRESHOLD_BREACH,
            source="alerting_service",
            model_id="model-789",
            payload={"metric": "accuracy", "value": 0.65},
        )

        json_str = original.to_json()
        restored = ComplianceEvent.from_json(json_str)

        assert restored.event_type == original.event_type
        assert restored.source == original.source
        assert restored.model_id == original.model_id
        assert restored.payload == original.payload

    def test_event_channel_mapping(self):
        """Test event type to channel mapping"""
        test_cases = [
            (ComplianceEventType.VIOLATION_DETECTED, "compliance:violations"),
            (ComplianceEventType.SCORE_CHANGED, "compliance:scores"),
            (ComplianceEventType.THRESHOLD_BREACH, "compliance:alerts"),
            (ComplianceEventType.MODEL_REGISTERED, "compliance:models"),
            (ComplianceEventType.REMEDIATION_STARTED, "compliance:remediations"),
            (ComplianceEventType.CERTIFICATION_EXPIRING, "compliance:certifications"),
        ]

        for event_type, expected_channel in test_cases:
            event = ComplianceEvent(
                event_type=event_type,
                source="test",
            )
            assert event.get_channel("compliance") == expected_channel


class TestComplianceEventPublisher:
    """Tests for ComplianceEventPublisher"""

    @pytest.fixture
    def publisher(self):
        """Create a publisher instance for testing"""
        return ComplianceEventPublisher(
            redis_url="redis://localhost:6379",
            channel_prefix="test_compliance",
        )

    @pytest.mark.asyncio
    async def test_publisher_initialization(self, publisher):
        """Test publisher initialization"""
        assert publisher.redis_url == "redis://localhost:6379"
        assert publisher.channel_prefix == "test_compliance"
        assert publisher._connected is False

    @pytest.mark.asyncio
    async def test_publish_fallback_when_redis_unavailable(self, publisher):
        """Test that publishing works in fallback mode when Redis is unavailable"""
        # Don't connect - simulates Redis being unavailable
        event = ComplianceEvent(
            event_type=ComplianceEventType.VIOLATION_DETECTED,
            source="test_service",
            model_id="model-123",
        )

        with patch.object(publisher, "_ensure_connected", return_value=False):
            result = await publisher.publish(event)

        # Should return 0 subscribers (fallback mode)
        assert result == 0
        assert publisher._metrics["events_failed"] == 1

    @pytest.mark.asyncio
    async def test_publish_with_mocked_redis(self, publisher):
        """Test publishing with mocked Redis connection"""
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock(return_value=2)

        publisher._redis = mock_redis
        publisher._connected = True

        event = ComplianceEvent(
            event_type=ComplianceEventType.SCORE_CHANGED,
            source="test_service",
            model_id="model-456",
        )

        with patch.object(publisher, "_ensure_connected", return_value=True):
            result = await publisher.publish(event)

        assert result == 2
        assert publisher._metrics["events_published"] == 1
        mock_redis.publish.assert_called()

    @pytest.mark.asyncio
    async def test_publish_violation_convenience_method(self, publisher):
        """Test publish_violation convenience method"""
        with patch.object(publisher, "publish", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 1

            event = await publisher.publish_violation(
                model_id="model-123",
                model_name="Test Model",
                violation_data={
                    "severity": "critical",
                    "regulation": "eu_ai_act",
                    "description": "Test violation",
                },
            )

            assert event.event_type == ComplianceEventType.VIOLATION_DETECTED
            assert event.model_id == "model-123"
            assert event.payload["severity"] == "critical"
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_score_change_convenience_method(self, publisher):
        """Test publish_score_change convenience method"""
        with patch.object(publisher, "publish", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 1

            event = await publisher.publish_score_change(
                model_id="model-123",
                model_name="Test Model",
                old_score=75.0,
                new_score=82.0,
            )

            assert event.event_type == ComplianceEventType.SCORE_CHANGED
            assert event.payload["old_score"] == 75.0
            assert event.payload["new_score"] == 82.0
            assert event.payload["direction"] == "improved"
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_threshold_breach_convenience_method(self, publisher):
        """Test publish_threshold_breach convenience method"""
        with patch.object(publisher, "publish", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 1

            event = await publisher.publish_threshold_breach(
                model_id="model-123",
                model_name="Test Model",
                metric="accuracy",
                value=0.55,
                threshold=0.70,
            )

            assert event.event_type == ComplianceEventType.THRESHOLD_BREACH
            assert event.payload["metric"] == "accuracy"
            assert event.payload["value"] == 0.55
            assert event.payload["threshold"] == 0.70
            mock_publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_metrics(self, publisher):
        """Test getting publisher metrics"""
        metrics = publisher.get_metrics()

        assert "events_published" in metrics
        assert "events_failed" in metrics
        assert "connected" in metrics
        assert metrics["connected"] is False


class TestComplianceEventSubscriber:
    """Tests for ComplianceEventSubscriber"""

    @pytest.fixture
    def subscriber(self):
        """Create a subscriber instance for testing"""
        return ComplianceEventSubscriber(
            redis_url="redis://localhost:6379",
            channel_prefix="test_compliance",
        )

    @pytest.mark.asyncio
    async def test_subscriber_initialization(self, subscriber):
        """Test subscriber initialization"""
        assert subscriber.redis_url == "redis://localhost:6379"
        assert subscriber.channel_prefix == "test_compliance"
        assert subscriber._running is False
        assert len(subscriber._handlers) == 0

    @pytest.mark.asyncio
    async def test_subscribe_registers_handler(self, subscriber):
        """Test that subscribing registers the handler"""
        handler = AsyncMock()

        # Mock the connection
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()

        subscriber._redis = mock_redis
        subscriber._pubsub = mock_pubsub

        with patch.object(subscriber, "connect", return_value=True):
            result = await subscriber.subscribe(
                [ComplianceEventType.VIOLATION_DETECTED],
                handler,
            )

        assert result is True
        assert ComplianceEventType.VIOLATION_DETECTED.value in subscriber._handlers

    @pytest.mark.asyncio
    async def test_subscribe_all_registers_handler(self, subscriber):
        """Test that subscribe_all registers a catch-all handler"""
        handler = AsyncMock()

        mock_redis = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe = AsyncMock()

        subscriber._redis = mock_redis
        subscriber._pubsub = mock_pubsub

        with patch.object(subscriber, "connect", return_value=True):
            result = await subscriber.subscribe_all(handler)

        assert result is True
        assert handler in subscriber._all_handlers

    @pytest.mark.asyncio
    async def test_process_message_calls_handlers(self, subscriber):
        """Test that processing a message calls registered handlers"""
        handler = AsyncMock()
        subscriber._handlers[ComplianceEventType.VIOLATION_DETECTED.value] = [handler]

        event = ComplianceEvent(
            event_type=ComplianceEventType.VIOLATION_DETECTED,
            source="test_service",
            model_id="model-123",
        )

        message = {
            "type": "message",
            "channel": "test_compliance:violations",
            "data": event.to_json(),
        }

        await subscriber._process_message(message)

        handler.assert_called_once()
        assert subscriber._metrics["events_received"] == 1
        assert subscriber._metrics["events_processed"] == 1

    @pytest.mark.asyncio
    async def test_process_message_handles_invalid_json(self, subscriber):
        """Test that invalid JSON is handled gracefully"""
        message = {
            "type": "message",
            "channel": "test_compliance:violations",
            "data": "invalid json {{{",
        }

        await subscriber._process_message(message)

        assert subscriber._metrics["events_received"] == 1
        assert subscriber._metrics["events_failed"] == 1

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_handler(self, subscriber):
        """Test that unsubscribing removes the handler"""
        handler = AsyncMock()
        subscriber._handlers[ComplianceEventType.VIOLATION_DETECTED.value] = [handler]

        await subscriber.unsubscribe(
            event_types=[ComplianceEventType.VIOLATION_DETECTED],
            handler=handler,
        )

        assert handler not in subscriber._handlers.get(ComplianceEventType.VIOLATION_DETECTED.value, [])

    @pytest.mark.asyncio
    async def test_get_metrics(self, subscriber):
        """Test getting subscriber metrics"""
        metrics = subscriber.get_metrics()

        assert "events_received" in metrics
        assert "events_processed" in metrics
        assert "running" in metrics
        assert metrics["running"] is False


class TestComplianceEventBus:
    """Tests for ComplianceEventBus combined functionality"""

    @pytest.fixture
    def event_bus(self):
        """Create an event bus instance for testing"""
        return ComplianceEventBus(
            redis_url="redis://localhost:6379",
            channel_prefix="test_compliance",
            service_name="test_service",
        )

    @pytest.mark.asyncio
    async def test_event_bus_initialization(self, event_bus):
        """Test event bus initialization"""
        assert event_bus.service_name == "test_service"
        assert event_bus._publisher is not None
        assert event_bus._subscriber is not None

    @pytest.mark.asyncio
    async def test_event_bus_publish(self, event_bus):
        """Test publishing through event bus"""
        with patch.object(event_bus._publisher, "publish", new_callable=AsyncMock) as mock_publish:
            mock_publish.return_value = 1

            event = ComplianceEvent(
                event_type=ComplianceEventType.MODEL_REGISTERED,
                source="",  # Empty, should be filled by event bus
                model_id="model-123",
            )

            result = await event_bus.publish(event)

            assert result == 1
            # Verify source was set to service name
            call_args = mock_publish.call_args[0][0]
            assert call_args.source == "test_service"

    @pytest.mark.asyncio
    async def test_event_bus_subscribe(self, event_bus):
        """Test subscribing through event bus"""
        handler = AsyncMock()

        with patch.object(event_bus._subscriber, "subscribe", new_callable=AsyncMock) as mock_subscribe:
            mock_subscribe.return_value = True

            result = await event_bus.subscribe(
                [ComplianceEventType.VIOLATION_DETECTED],
                handler,
            )

            assert result is True
            mock_subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_bus_context_manager(self, event_bus):
        """Test event bus as async context manager"""
        with patch.object(event_bus, "start", new_callable=AsyncMock) as mock_start:
            with patch.object(event_bus, "stop", new_callable=AsyncMock) as mock_stop:
                mock_start.return_value = True

                async with event_bus as bus:
                    assert bus is event_bus

                mock_start.assert_called_once()
                mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_bus_get_metrics(self, event_bus):
        """Test getting combined metrics"""
        metrics = event_bus.get_metrics()

        assert "service_name" in metrics
        assert "publisher" in metrics
        assert "subscriber" in metrics
        assert metrics["service_name"] == "test_service"


class TestEventTypeEnumeration:
    """Tests for ComplianceEventType enumeration"""

    def test_all_event_types_defined(self):
        """Test that all expected event types are defined"""
        expected_types = [
            "MODEL_REGISTERED",
            "MODEL_UPDATED",
            "ASSESSMENT_COMPLETED",
            "VIOLATION_DETECTED",
            "VIOLATION_RESOLVED",
            "SCORE_CHANGED",
            "RISK_LEVEL_CHANGED",
            "REMEDIATION_STARTED",
            "REMEDIATION_COMPLETED",
            "THRESHOLD_BREACH",
            "CERTIFICATION_EXPIRING",
        ]

        for type_name in expected_types:
            assert hasattr(ComplianceEventType, type_name)

    def test_event_type_values_are_namespaced(self):
        """Test that event type values follow namespace pattern"""
        for event_type in ComplianceEventType:
            assert event_type.value.startswith("compliance.")
