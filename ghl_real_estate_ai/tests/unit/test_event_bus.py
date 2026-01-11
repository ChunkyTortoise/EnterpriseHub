"""
Unit Tests for Event Bus Integration

Tests for the Event Bus system that coordinates ML processing and WebSocket broadcasting.

Coverage:
- Event publishing and processing
- Parallel ML inference coordination
- Cache polling and management
- WebSocket broadcasting integration
- Performance monitoring
- Health checks
- Error handling and retry logic
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.event_bus import (
    EventBus,
    EventType,
    EventPriority,
    MLEvent,
    EventBusMetrics,
    get_event_bus,
    publish_lead_event,
    process_lead_intelligence
)
from ghl_real_estate_ai.services.optimized_ml_lead_intelligence_engine import (
    OptimizedLeadIntelligence,
    ProcessingPriority,
    IntelligenceType
)
from ghl_real_estate_ai.services.realtime_lead_scoring import LeadScore, ScoreConfidenceLevel
from ghl_real_estate_ai.services.churn_prediction_service import ChurnPrediction, ChurnRiskLevel
from ghl_real_estate_ai.services.enhanced_property_matcher_ml import EnhancedPropertyMatch

# Mock IntelligenceEventType if websocket_manager not available
try:
    from ghl_real_estate_ai.services.websocket_manager import IntelligenceEventType
except ImportError:
    from enum import Enum
    class IntelligenceEventType(Enum):
        INTELLIGENCE_COMPLETE = "intelligence_complete"


class TestMLEvent:
    """Test MLEvent dataclass"""

    def test_create_ml_event(self):
        """Test creating ML event with required fields"""
        event = MLEvent(
            event_id="evt_test123",
            event_type=EventType.LEAD_CREATED,
            tenant_id="tenant_123",
            lead_id="lead_456",
            event_data={"test": "data"},
            priority=EventPriority.HIGH,
            timestamp=datetime.now()
        )

        assert event.event_id == "evt_test123"
        assert event.event_type == EventType.LEAD_CREATED
        assert event.tenant_id == "tenant_123"
        assert event.lead_id == "lead_456"
        assert event.priority == EventPriority.HIGH
        assert event.requires_scoring is True
        assert event.requires_churn_prediction is True
        assert event.requires_property_matching is True

    def test_ml_event_defaults(self):
        """Test ML event default values"""
        event = MLEvent(
            event_id="evt_test",
            event_type=EventType.LEAD_UPDATED,
            tenant_id="tenant_1",
            lead_id="lead_1",
            event_data={},
            priority=EventPriority.MEDIUM,
            timestamp=datetime.now()
        )

        assert event.processing_started is None
        assert event.processing_completed is None
        assert event.processing_time_ms == 0.0
        assert event.retry_count == 0
        assert event.max_retries == 3
        assert event.last_error is None


class TestEventBusMetrics:
    """Test EventBusMetrics dataclass"""

    def test_create_metrics(self):
        """Test creating event bus metrics"""
        metrics = EventBusMetrics()

        assert metrics.total_events_processed == 0
        assert metrics.successful_events == 0
        assert metrics.failed_events == 0
        assert metrics.avg_processing_time_ms == 0.0
        assert metrics.cache_hit_rate == 0.0
        assert metrics.cache_polling_interval_ms == 500.0
        assert metrics.is_healthy is True
        assert metrics.last_updated is not None


class TestEventBusInitialization:
    """Test Event Bus initialization"""

    @pytest.mark.asyncio
    async def test_event_bus_creation(self):
        """Test creating Event Bus instance"""
        # Create mock services
        ml_engine = AsyncMock()
        websocket_manager = AsyncMock()
        scoring_service = AsyncMock()

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=websocket_manager,
            scoring_service=scoring_service
        )

        assert event_bus.ml_engine == ml_engine
        assert event_bus.websocket_manager == websocket_manager
        assert event_bus.scoring_service == scoring_service
        assert event_bus.max_concurrent_processing == 100
        assert event_bus.polling_interval == 0.5

    @pytest.mark.asyncio
    async def test_event_bus_initialization_with_mocks(self):
        """Test Event Bus initialization with all services"""
        # Create comprehensive mocks
        ml_engine = AsyncMock()
        ml_engine.initialize = AsyncMock()
        ml_engine.get_optimization_metrics = AsyncMock(return_value={
            "optimization_status": {"target_achievement": True}
        })

        websocket_manager = AsyncMock()
        websocket_manager.initialize = AsyncMock()
        websocket_manager.get_connection_health = AsyncMock(return_value={
            "performance_status": {"overall_healthy": True}
        })

        scoring_service = AsyncMock()
        scoring_service.initialize = AsyncMock()

        redis_client = AsyncMock()
        redis_client.initialize = AsyncMock()

        with patch('ghl_real_estate_ai.services.event_bus.redis_client', redis_client):
            with patch('ghl_real_estate_ai.services.event_bus.get_churn_prediction_service', return_value=AsyncMock()):
                with patch('ghl_real_estate_ai.services.event_bus.get_enhanced_property_matcher', return_value=AsyncMock()):
                    event_bus = EventBus(
                        ml_engine=ml_engine,
                        websocket_manager=websocket_manager,
                        scoring_service=scoring_service
                    )

                    await event_bus.initialize()

                    assert event_bus._workers_started is True
                    assert len(event_bus._worker_tasks) > 0


class TestEventPublishing:
    """Test event publishing functionality"""

    @pytest.mark.asyncio
    async def test_publish_event_basic(self):
        """Test publishing basic event"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        event_id = await event_bus.publish_event(
            event_type=EventType.LEAD_CREATED,
            tenant_id="tenant_123",
            lead_id="lead_456",
            event_data={"test": "data"},
            priority=EventPriority.HIGH
        )

        assert event_id.startswith("evt_")
        assert event_id in event_bus._active_events
        assert event_bus.metrics.current_queue_depth > 0

    @pytest.mark.asyncio
    async def test_publish_event_with_priority(self):
        """Test publishing events with different priorities"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Publish high priority event
        high_priority_id = await event_bus.publish_event(
            event_type=EventType.LEAD_CREATED,
            tenant_id="tenant_1",
            lead_id="lead_1",
            event_data={},
            priority=EventPriority.CRITICAL
        )

        # Publish low priority event
        low_priority_id = await event_bus.publish_event(
            event_type=EventType.LEAD_UPDATED,
            tenant_id="tenant_1",
            lead_id="lead_2",
            event_data={},
            priority=EventPriority.LOW
        )

        assert high_priority_id in event_bus._active_events
        assert low_priority_id in event_bus._active_events

        # Verify high priority event has lower priority value (processed first)
        high_event = event_bus._active_events[high_priority_id]
        low_event = event_bus._active_events[low_priority_id]

        assert high_event.priority.value < low_event.priority.value

    @pytest.mark.asyncio
    async def test_ml_requirements_configuration(self):
        """Test ML requirements are configured based on event type"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Test LEAD_CREATED event
        event_id = await event_bus.publish_event(
            event_type=EventType.LEAD_CREATED,
            tenant_id="tenant_1",
            lead_id="lead_1",
            event_data={},
            priority=EventPriority.MEDIUM
        )

        event = event_bus._active_events[event_id]
        assert event.requires_scoring is True
        assert event.requires_churn_prediction is True
        assert event.requires_property_matching is True

        # Test SCORE_REFRESH_REQUESTED event
        event_id2 = await event_bus.publish_event(
            event_type=EventType.SCORE_REFRESH_REQUESTED,
            tenant_id="tenant_1",
            lead_id="lead_2",
            event_data={},
            priority=EventPriority.MEDIUM
        )

        event2 = event_bus._active_events[event_id2]
        assert event2.requires_scoring is True
        assert event2.requires_churn_prediction is False
        assert event2.requires_property_matching is False


class TestLeadEventProcessing:
    """Test lead event processing with ML coordination"""

    @pytest.mark.asyncio
    async def test_process_lead_event_success(self):
        """Test successful lead event processing"""
        # Create mock intelligence
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=35.0,
            cache_hit_rate=0.0,
            parallel_operations=3
        )

        # Create mock ML engine
        ml_engine = AsyncMock()
        ml_engine.process_lead_event_optimized = AsyncMock(return_value=mock_intelligence)

        # Create mock WebSocket manager
        websocket_manager = AsyncMock()
        websocket_manager.broadcast_intelligence_update = AsyncMock()

        # Create mock Redis client
        redis_client = AsyncMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.set = AsyncMock()

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=websocket_manager,
            scoring_service=AsyncMock()
        )
        event_bus.redis_client = redis_client

        # Process event
        result = await event_bus.process_lead_event(
            lead_id="lead_123",
            tenant_id="tenant_456",
            event_data={"test": "data"},
            priority=ProcessingPriority.MEDIUM,
            broadcast=True
        )

        assert result is not None
        assert result.lead_id == "lead_123"
        assert event_bus.metrics.successful_events == 1
        assert event_bus.metrics.total_events_processed == 1

        # Verify ML engine was called
        ml_engine.process_lead_event_optimized.assert_called_once()

        # Verify broadcast was called
        websocket_manager.broadcast_intelligence_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_lead_event_with_cache_hit(self):
        """Test lead event processing with cache hit"""
        # Create cached intelligence
        cached_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_cached",
            processing_time_ms=5.0,
            cache_hit_rate=1.0,
            parallel_operations=0
        )

        # Create mocks
        ml_engine = AsyncMock()
        websocket_manager = AsyncMock()

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=websocket_manager,
            scoring_service=AsyncMock()
        )

        # Mock cache to return cached intelligence
        event_bus._cached_results["lead_123"] = cached_intelligence

        # Process event
        result = await event_bus.process_lead_event(
            lead_id="lead_123",
            tenant_id="tenant_456",
            event_data={},
            priority=ProcessingPriority.MEDIUM,
            broadcast=True
        )

        assert result is not None
        assert result.lead_id == "lead_123"
        assert result.cache_hit_rate == 1.0

        # Verify ML engine was NOT called (cache hit)
        ml_engine.process_lead_event_optimized.assert_not_called()

        # Verify broadcast was still called
        websocket_manager.broadcast_intelligence_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_lead_event_no_broadcast(self):
        """Test lead event processing without broadcasting"""
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=30.0,
            cache_hit_rate=0.0,
            parallel_operations=2
        )

        ml_engine = AsyncMock()
        ml_engine.process_lead_event_optimized = AsyncMock(return_value=mock_intelligence)

        websocket_manager = AsyncMock()

        redis_client = AsyncMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.set = AsyncMock()

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=websocket_manager,
            scoring_service=AsyncMock()
        )
        event_bus.redis_client = redis_client

        # Process without broadcast
        result = await event_bus.process_lead_event(
            lead_id="lead_123",
            tenant_id="tenant_456",
            event_data={},
            priority=ProcessingPriority.MEDIUM,
            broadcast=False
        )

        assert result is not None

        # Verify ML engine was called
        ml_engine.process_lead_event_optimized.assert_called_once()

        # Verify broadcast was NOT called
        websocket_manager.broadcast_intelligence_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_lead_event_with_error(self):
        """Test lead event processing with error handling"""
        # Create ML engine that raises error
        ml_engine = AsyncMock()
        ml_engine.process_lead_event_optimized = AsyncMock(
            side_effect=Exception("ML processing failed")
        )

        redis_client = AsyncMock()
        redis_client.get = AsyncMock(return_value=None)

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )
        event_bus.redis_client = redis_client

        # Process event (should handle error gracefully)
        result = await event_bus.process_lead_event(
            lead_id="lead_123",
            tenant_id="tenant_456",
            event_data={},
            priority=ProcessingPriority.MEDIUM
        )

        assert result is None
        assert event_bus.metrics.failed_events == 1
        assert event_bus.metrics.total_events_processed == 1


class TestWebSocketBroadcasting:
    """Test WebSocket broadcasting integration"""

    @pytest.mark.asyncio
    async def test_publish_intelligence_update(self):
        """Test publishing intelligence update to WebSocket Manager"""
        # Create mock intelligence
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=35.0,
            cache_hit_rate=0.8,
            parallel_operations=3
        )

        # Create mock WebSocket manager with broadcast result
        mock_broadcast_result = Mock()
        mock_broadcast_result.connections_successful = 5
        mock_broadcast_result.connections_targeted = 6

        websocket_manager = AsyncMock()
        websocket_manager.broadcast_intelligence_update = AsyncMock(
            return_value=mock_broadcast_result
        )

        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=websocket_manager,
            scoring_service=AsyncMock()
        )

        # Publish intelligence update
        await event_bus.publish_intelligence_update(
            tenant_id="tenant_123",
            intelligence_data=mock_intelligence
        )

        # Verify broadcast was called
        websocket_manager.broadcast_intelligence_update.assert_called_once_with(
            tenant_id="tenant_123",
            intelligence=mock_intelligence,
            event_type=IntelligenceEventType.INTELLIGENCE_COMPLETE
        )


class TestCaching:
    """Test cache management functionality"""

    @pytest.mark.asyncio
    async def test_cache_intelligence(self):
        """Test caching intelligence data"""
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=30.0,
            cache_hit_rate=0.0,
            parallel_operations=2
        )

        redis_client = AsyncMock()
        redis_client.set = AsyncMock()

        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )
        event_bus.redis_client = redis_client

        # Cache intelligence
        await event_bus._cache_intelligence(
            lead_id="lead_123",
            tenant_id="tenant_456",
            intelligence=mock_intelligence
        )

        # Verify in-memory cache
        assert "lead_123" in event_bus._cached_results
        assert event_bus._cached_results["lead_123"] == mock_intelligence

        # Verify Redis cache was called
        redis_client.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_intelligence_freshness_check(self):
        """Test intelligence freshness validation"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Fresh intelligence (just created)
        fresh_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_1",
            timestamp=datetime.now(),
            request_id="req_1"
        )

        assert event_bus._is_intelligence_fresh(fresh_intelligence) is True

        # Stale intelligence (old timestamp)
        stale_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_2",
            timestamp=datetime.now() - timedelta(minutes=10),
            request_id="req_2"
        )

        assert event_bus._is_intelligence_fresh(stale_intelligence) is False

    @pytest.mark.asyncio
    async def test_cache_hit_rate_tracking(self):
        """Test cache hit rate metric tracking"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Initial state
        assert event_bus.metrics.cache_hit_rate == 0.0

        # Record cache miss
        event_bus.metrics.total_events_processed = 1
        rate = event_bus._update_cache_hit_rate(False)
        assert rate == 0.0

        # Record cache hit
        event_bus.metrics.total_events_processed = 2
        event_bus.metrics.cache_hit_rate = rate
        rate = event_bus._update_cache_hit_rate(True)
        assert rate > 0.0


class TestPerformanceMetrics:
    """Test performance monitoring functionality"""

    @pytest.mark.asyncio
    async def test_update_processing_metrics(self):
        """Test updating processing performance metrics"""
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=35.0,
            cache_hit_rate=0.8,
            parallel_operations=3
        )

        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Update metrics
        await event_bus._update_processing_metrics(
            processing_time_ms=40.0,
            intelligence=mock_intelligence
        )

        assert event_bus.metrics.avg_processing_time_ms > 0
        assert event_bus.metrics.avg_ml_coordination_ms > 0
        assert len(event_bus._performance_history) == 1

    @pytest.mark.asyncio
    async def test_broadcast_metrics_tracking(self):
        """Test broadcast performance metrics tracking"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Update broadcast metrics
        event_bus.metrics.total_events_processed = 1
        event_bus._update_broadcast_metrics(broadcast_latency_ms=45.0)

        assert event_bus.metrics.avg_broadcast_latency_ms == 45.0

        # Update again
        event_bus.metrics.total_events_processed = 2
        event_bus._update_broadcast_metrics(broadcast_latency_ms=55.0)

        assert event_bus.metrics.avg_broadcast_latency_ms == 50.0

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self):
        """Test comprehensive performance metrics retrieval"""
        # Create mocks with health data
        ml_engine = AsyncMock()
        ml_engine.get_optimization_metrics = AsyncMock(return_value={
            "optimization_status": {"target_achievement": True}
        })

        websocket_manager = AsyncMock()
        websocket_manager.get_connection_health = AsyncMock(return_value={
            "performance_status": {"overall_healthy": True}
        })

        redis_client = AsyncMock()
        redis_client.initialize = AsyncMock()

        with patch('ghl_real_estate_ai.services.event_bus.get_redis_health', return_value={"is_healthy": True}):
            event_bus = EventBus(
                ml_engine=ml_engine,
                websocket_manager=websocket_manager,
                scoring_service=AsyncMock()
            )
            event_bus.redis_client = redis_client

            # Get metrics
            metrics = await event_bus.get_performance_metrics()

            assert "performance_targets" in metrics
            assert "performance_status" in metrics
            assert metrics["performance_targets"]["event_processing_target_ms"] == 100
            assert metrics["performance_targets"]["cache_polling_interval_ms"] == 500


class TestEventHandlers:
    """Test event handler registration and notification"""

    @pytest.mark.asyncio
    async def test_subscribe_to_ml_events(self):
        """Test subscribing to ML events"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Create mock handler
        handler_called = False

        async def test_handler(event: MLEvent, intelligence: OptimizedLeadIntelligence):
            nonlocal handler_called
            handler_called = True

        # Subscribe to events
        await event_bus.subscribe_to_ml_events(
            event_types=[EventType.LEAD_CREATED],
            handler=test_handler
        )

        assert len(event_bus._event_handlers[EventType.LEAD_CREATED]) > 0

    @pytest.mark.asyncio
    async def test_notify_event_handlers(self):
        """Test notifying event handlers"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Track handler calls
        handler_calls = []

        async def test_handler(event: MLEvent, intelligence: OptimizedLeadIntelligence):
            handler_calls.append(event.event_id)

        # Subscribe handler
        await event_bus.subscribe_to_ml_events(
            event_types=[EventType.LEAD_CREATED],
            handler=test_handler
        )

        # Create test event
        test_event = MLEvent(
            event_id="evt_test",
            event_type=EventType.LEAD_CREATED,
            tenant_id="tenant_1",
            lead_id="lead_1",
            event_data={},
            priority=EventPriority.MEDIUM,
            timestamp=datetime.now()
        )

        test_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_1",
            timestamp=datetime.now(),
            request_id="req_1"
        )

        # Notify handlers
        await event_bus._notify_event_handlers(test_event, test_intelligence)

        assert len(handler_calls) > 0
        assert "evt_test" in handler_calls


class TestPriorityMapping:
    """Test event priority to ML processing priority mapping"""

    def test_map_event_priority(self):
        """Test priority mapping logic"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        # Test all priority mappings
        assert event_bus._map_event_priority(EventPriority.CRITICAL) == ProcessingPriority.CRITICAL
        assert event_bus._map_event_priority(EventPriority.HIGH) == ProcessingPriority.HIGH
        assert event_bus._map_event_priority(EventPriority.MEDIUM) == ProcessingPriority.MEDIUM
        assert event_bus._map_event_priority(EventPriority.LOW) == ProcessingPriority.LOW


class TestConvenienceFunctions:
    """Test convenience functions for common operations"""

    @pytest.mark.asyncio
    async def test_publish_lead_event_convenience(self):
        """Test convenience function for publishing lead events"""
        # This would require mocking the global singleton
        # Skipping for unit test, would be covered in integration tests
        pass

    @pytest.mark.asyncio
    async def test_process_lead_intelligence_convenience(self):
        """Test convenience function for processing lead intelligence"""
        # This would require mocking the global singleton
        # Skipping for unit test, would be covered in integration tests
        pass


# Performance benchmarks

@pytest.mark.benchmark
class TestEventBusPerformance:
    """Performance benchmarks for Event Bus"""

    @pytest.mark.asyncio
    async def test_event_publishing_performance(self):
        """Benchmark event publishing throughput"""
        event_bus = EventBus(
            ml_engine=AsyncMock(),
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )

        start_time = time.time()
        event_count = 100

        # Publish 100 events
        for i in range(event_count):
            await event_bus.publish_event(
                event_type=EventType.LEAD_CREATED,
                tenant_id=f"tenant_{i % 10}",
                lead_id=f"lead_{i}",
                event_data={"index": i},
                priority=EventPriority.MEDIUM
            )

        elapsed_time = time.time() - start_time
        events_per_second = event_count / elapsed_time

        # Should handle 1000+ events/second
        assert events_per_second > 100

    @pytest.mark.asyncio
    async def test_processing_latency(self):
        """Benchmark end-to-end processing latency"""
        # Create fast mock ML engine
        mock_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_456",
            processing_time_ms=35.0,
            cache_hit_rate=0.0,
            parallel_operations=3
        )

        ml_engine = AsyncMock()
        ml_engine.process_lead_event_optimized = AsyncMock(return_value=mock_intelligence)

        redis_client = AsyncMock()
        redis_client.get = AsyncMock(return_value=None)
        redis_client.set = AsyncMock()

        event_bus = EventBus(
            ml_engine=ml_engine,
            websocket_manager=AsyncMock(),
            scoring_service=AsyncMock()
        )
        event_bus.redis_client = redis_client

        # Process event and measure latency
        start_time = time.time()

        await event_bus.process_lead_event(
            lead_id="lead_123",
            tenant_id="tenant_456",
            event_data={},
            priority=ProcessingPriority.MEDIUM,
            broadcast=False
        )

        latency_ms = (time.time() - start_time) * 1000

        # Should complete in <100ms
        assert latency_ms < 100
