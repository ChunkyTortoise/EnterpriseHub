"""
Unit Tests for WebSocket Manager Service

Tests cover:
- WebSocket connection management and subscription handling
- Real-time ML intelligence broadcasting
- Performance targets (<100ms latency, 100+ concurrent connections)
- Redis caching integration
- Event processing and parallel ML inference
- Connection health monitoring
- Error handling and resilience
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import List

from ghl_real_estate_ai.services.websocket_manager import (
    WebSocketManager,
    IntelligenceEventType,
    SubscriptionTopic,
    IntelligenceSubscription,
    IntelligenceUpdate,
    WebSocketPerformanceMetrics,
    get_websocket_manager,
    subscribe_lead_intelligence,
    broadcast_lead_intelligence,
    process_lead_event_realtime
)
from ghl_real_estate_ai.services.optimized_ml_lead_intelligence_engine import (
    OptimizedLeadIntelligence,
    ProcessingPriority
)
from ghl_real_estate_ai.services.realtime_lead_scoring import (
    LeadScore,
    ScoreConfidenceLevel
)
from ghl_real_estate_ai.services.churn_prediction_service import (
    ChurnPrediction,
    ChurnRiskLevel
)


# Fixtures

@pytest.fixture
def mock_websocket():
    """Mock FastAPI WebSocket"""
    websocket = AsyncMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


@pytest.fixture
def mock_websocket_hub():
    """Mock RealtimeWebSocketHub"""
    hub = AsyncMock()
    hub.connect_client = AsyncMock(return_value="conn_123")
    hub.disconnect_client = AsyncMock(return_value=True)
    hub.broadcast_to_tenant = AsyncMock(return_value=Mock(
        connections_targeted=10,
        connections_successful=10,
        connections_failed=0,
        broadcast_time_ms=25.5
    ))
    hub.get_connection_health = AsyncMock(return_value={
        "connections": {"total": 10, "alive": 10}
    })
    return hub


@pytest.fixture
def mock_ml_engine():
    """Mock OptimizedMLLeadIntelligenceEngine"""
    engine = AsyncMock()

    # Create mock intelligence result
    mock_intelligence = OptimizedLeadIntelligence(
        lead_id="lead_123",
        timestamp=datetime.now(),
        request_id="req_123",
        processing_time_ms=32.5,
        cache_hit_rate=0.85,
        parallel_operations=3,
        overall_health_score=0.85,
        confidence_score=0.92
    )

    # Add mock lead score
    mock_intelligence._lead_score = LeadScore(
        lead_id="lead_123",
        score=0.87,
        confidence=ScoreConfidenceLevel.HIGH,
        model_version="v1.0.0",
        timestamp=datetime.now(),
        feature_contributions={"engagement": 0.3, "recency": 0.2},
        feature_quality=0.95,
        prediction_confidence=0.90,
        inference_time_ms=28.3,
        top_features=[("engagement", 0.3), ("recency", 0.2)],
        score_tier="hot"
    )

    engine.process_lead_event_optimized = AsyncMock(return_value=mock_intelligence)
    engine.get_optimization_metrics = AsyncMock(return_value={
        "avg_processing_time_ms": 35.2,
        "cache_hit_rate": 0.87,
        "total_requests": 1000
    })

    return engine


@pytest.fixture
def mock_scoring_service():
    """Mock RealtimeLeadScoringService"""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_redis_client():
    """Mock Redis client"""
    client = AsyncMock()
    client.initialize = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    return client


@pytest.fixture
async def websocket_manager(
    mock_websocket_hub,
    mock_ml_engine,
    mock_scoring_service,
    mock_redis_client
):
    """Create WebSocket Manager with mocked dependencies"""
    with patch('ghl_real_estate_ai.services.websocket_manager.redis_client', mock_redis_client), \
         patch('ghl_real_estate_ai.services.websocket_manager.get_redis_health', AsyncMock(return_value={"is_healthy": True})):

        manager = WebSocketManager(
            websocket_hub=mock_websocket_hub,
            ml_engine=mock_ml_engine,
            scoring_service=mock_scoring_service
        )

        # Mock supporting services
        manager.churn_service = AsyncMock()
        manager.property_matcher = AsyncMock()

        # Initialize without starting background workers
        manager._workers_started = True  # Prevent worker startup

        yield manager


# Tests

class TestWebSocketManagerInitialization:
    """Test WebSocket Manager initialization"""

    @pytest.mark.asyncio
    async def test_initialize_success(self, websocket_manager):
        """Test successful initialization"""
        # Initialization already done in fixture
        assert websocket_manager is not None
        assert websocket_manager.websocket_hub is not None
        assert websocket_manager.ml_engine is not None
        assert websocket_manager.scoring_service is not None

    @pytest.mark.asyncio
    async def test_initialize_with_defaults(self):
        """Test initialization with default singleton instances"""
        with patch('ghl_real_estate_ai.services.websocket_manager.get_realtime_websocket_hub') as mock_hub, \
             patch('ghl_real_estate_ai.services.websocket_manager.get_optimized_ml_intelligence_engine') as mock_engine, \
             patch('ghl_real_estate_ai.services.websocket_manager.get_lead_scoring_service') as mock_scoring, \
             patch('ghl_real_estate_ai.services.websocket_manager.redis_client') as mock_redis:

            mock_hub.return_value = AsyncMock()
            mock_engine.return_value = AsyncMock()
            mock_scoring.return_value = AsyncMock()
            mock_redis.initialize = AsyncMock(return_value=True)

            manager = WebSocketManager()
            manager._workers_started = True

            assert manager.websocket_hub is None  # Not initialized yet

            await manager.initialize()

            assert manager.websocket_hub is not None
            assert manager.ml_engine is not None
            assert manager.scoring_service is not None


class TestSubscriptionManagement:
    """Test WebSocket subscription management"""

    @pytest.mark.asyncio
    async def test_subscribe_to_lead_intelligence_success(
        self,
        websocket_manager,
        mock_websocket
    ):
        """Test successful subscription to lead intelligence"""
        subscription_id = await websocket_manager.subscribe_to_lead_intelligence(
            websocket=mock_websocket,
            tenant_id="tenant_123",
            user_id="user_456",
            topics=[SubscriptionTopic.LEAD_SCORING, SubscriptionTopic.CHURN_PREDICTION]
        )

        assert subscription_id is not None
        assert subscription_id.startswith("sub_")

        # Verify subscription stored
        assert subscription_id in websocket_manager._subscriptions
        subscription = websocket_manager._subscriptions[subscription_id]

        assert subscription.tenant_id == "tenant_123"
        assert subscription.connection_id == "conn_123"
        assert len(subscription.topics) == 2
        assert SubscriptionTopic.LEAD_SCORING in subscription.topics

        # Verify metrics updated
        assert websocket_manager.metrics.total_connections == 1
        assert websocket_manager.metrics.active_subscriptions == 1

    @pytest.mark.asyncio
    async def test_subscribe_with_lead_filters(
        self,
        websocket_manager,
        mock_websocket
    ):
        """Test subscription with specific lead filters"""
        lead_filters = ["lead_123", "lead_456"]

        subscription_id = await websocket_manager.subscribe_to_lead_intelligence(
            websocket=mock_websocket,
            tenant_id="tenant_123",
            user_id="user_456",
            lead_filters=lead_filters
        )

        assert subscription_id is not None

        # Verify lead filters applied
        subscription = websocket_manager._subscriptions[subscription_id]
        assert subscription.lead_filters == lead_filters

        # Verify lead-specific tracking
        assert subscription_id in websocket_manager._lead_subscriptions["lead_123"]
        assert subscription_id in websocket_manager._lead_subscriptions["lead_456"]

    @pytest.mark.asyncio
    async def test_subscribe_connection_failure(
        self,
        websocket_manager,
        mock_websocket
    ):
        """Test subscription when WebSocket connection fails"""
        websocket_manager.websocket_hub.connect_client = AsyncMock(return_value=None)

        subscription_id = await websocket_manager.subscribe_to_lead_intelligence(
            websocket=mock_websocket,
            tenant_id="tenant_123",
            user_id="user_456"
        )

        assert subscription_id is None

    @pytest.mark.asyncio
    async def test_unsubscribe_success(
        self,
        websocket_manager,
        mock_websocket
    ):
        """Test successful unsubscription"""
        # First subscribe
        subscription_id = await websocket_manager.subscribe_to_lead_intelligence(
            websocket=mock_websocket,
            tenant_id="tenant_123",
            user_id="user_456",
            lead_filters=["lead_123"]
        )

        # Then unsubscribe
        result = await websocket_manager.unsubscribe(subscription_id)

        assert result is True
        assert subscription_id not in websocket_manager._subscriptions
        assert subscription_id not in websocket_manager._tenant_subscriptions["tenant_123"]
        assert subscription_id not in websocket_manager._lead_subscriptions["lead_123"]

    @pytest.mark.asyncio
    async def test_unsubscribe_not_found(self, websocket_manager):
        """Test unsubscribe with non-existent subscription"""
        result = await websocket_manager.unsubscribe("non_existent_sub")

        assert result is False


class TestIntelligenceBroadcasting:
    """Test ML intelligence broadcasting"""

    @pytest.mark.asyncio
    async def test_broadcast_intelligence_update_success(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test successful intelligence broadcasting"""
        # Get mock intelligence from ML engine
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={"type": "lead_activity"},
            priority=ProcessingPriority.HIGH
        )

        # Broadcast
        result = await websocket_manager.broadcast_intelligence_update(
            tenant_id="tenant_123",
            intelligence=intelligence
        )

        assert result.connections_targeted == 10
        assert result.connections_successful == 10
        assert result.connections_failed == 0
        assert result.broadcast_time_ms < 100  # Performance target

        # Verify metrics updated
        assert websocket_manager.metrics.total_broadcasts > 0

    @pytest.mark.asyncio
    async def test_broadcast_performance_target(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test broadcast meets <100ms performance target"""
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        start_time = time.time()
        result = await websocket_manager.broadcast_intelligence_update(
            tenant_id="tenant_123",
            intelligence=intelligence
        )
        broadcast_time = (time.time() - start_time) * 1000

        # Should complete within 100ms target
        assert broadcast_time < 100
        assert result.broadcast_time_ms < 100

    @pytest.mark.asyncio
    async def test_broadcast_serialization(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test intelligence update serialization"""
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        # Create update
        update = IntelligenceUpdate(
            event_id="evt_123",
            event_type=IntelligenceEventType.INTELLIGENCE_COMPLETE,
            tenant_id="tenant_123",
            lead_id="lead_123",
            timestamp=datetime.now(),
            intelligence=intelligence,
            lead_score=intelligence.lead_score
        )

        # Serialize
        serialized = websocket_manager._serialize_intelligence_update(update)

        # Verify structure
        assert "event_id" in serialized
        assert "event_type" in serialized
        assert "lead_id" in serialized
        assert "lead_score" in serialized
        assert serialized["lead_score"]["score"] == 0.87
        assert serialized["lead_score"]["tier"] == "hot"


class TestMLEventHandling:
    """Test ML event processing and handling"""

    @pytest.mark.asyncio
    async def test_handle_ml_event_success(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test successful ML event handling"""
        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={"type": "lead_activity", "action": "property_view"},
            priority=ProcessingPriority.HIGH
        )

        assert intelligence is not None
        assert intelligence.lead_id == "lead_123"
        assert intelligence.processing_time_ms < 40  # ML performance target

        # Verify ML engine called
        mock_ml_engine.process_lead_event_optimized.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_ml_event_with_caching(
        self,
        websocket_manager,
        mock_ml_engine,
        mock_redis_client
    ):
        """Test ML event handling with cache hit"""
        # Mock cached intelligence
        cached_intelligence = OptimizedLeadIntelligence(
            lead_id="lead_123",
            timestamp=datetime.now(),
            request_id="req_cached",
            processing_time_ms=5.0,  # Fast cache response
            cache_hit_rate=1.0
        )

        mock_redis_client.get = AsyncMock(return_value=cached_intelligence)
        websocket_manager._is_intelligence_fresh = Mock(return_value=True)

        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={}
        )

        # Should use cached result
        assert intelligence is not None

    @pytest.mark.asyncio
    async def test_handle_ml_event_performance_target(
        self,
        websocket_manager
    ):
        """Test ML event handling meets performance targets"""
        start_time = time.time()

        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={"type": "lead_activity"}
        )

        processing_time = (time.time() - start_time) * 1000

        # Should complete within reasonable time (allowing for mocks)
        assert processing_time < 200
        assert intelligence is not None

    @pytest.mark.asyncio
    async def test_handle_ml_event_error_handling(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test error handling in ML event processing"""
        mock_ml_engine.process_lead_event_optimized = AsyncMock(
            side_effect=Exception("ML processing failed")
        )

        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={}
        )

        # Should return None on error
        assert intelligence is None


class TestConnectionHealth:
    """Test connection health monitoring"""

    @pytest.mark.asyncio
    async def test_get_connection_health_success(
        self,
        websocket_manager
    ):
        """Test getting comprehensive connection health"""
        health = await websocket_manager.get_connection_health()

        assert "websocket_manager" in health
        assert "websocket_hub" in health
        assert "redis" in health
        assert "ml_engine" in health
        assert "performance_targets" in health
        assert "performance_status" in health

        # Verify performance targets
        targets = health["performance_targets"]
        assert targets["websocket_latency_target_ms"] == 100
        assert targets["ml_inference_target_ms"] == 35
        assert targets["cache_hit_rate_target"] == 0.90

    @pytest.mark.asyncio
    async def test_health_includes_metrics(
        self,
        websocket_manager
    ):
        """Test health response includes current metrics"""
        health = await websocket_manager.get_connection_health()

        manager_health = health["websocket_manager"]

        assert "total_connections" in manager_health
        assert "active_subscriptions" in manager_health
        assert "avg_broadcast_latency_ms" in manager_health
        assert "avg_ml_processing_ms" in manager_health
        assert "cache_hit_rate" in manager_health
        assert "current_load" in manager_health


class TestPerformanceMetrics:
    """Test performance metrics tracking"""

    @pytest.mark.asyncio
    async def test_broadcast_metrics_update(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test broadcast metrics are updated correctly"""
        initial_broadcasts = websocket_manager.metrics.total_broadcasts

        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        await websocket_manager.broadcast_intelligence_update(
            tenant_id="tenant_123",
            intelligence=intelligence
        )

        # Verify metrics updated
        assert websocket_manager.metrics.total_broadcasts == initial_broadcasts + 1
        assert websocket_manager.metrics.avg_broadcast_latency_ms > 0

    @pytest.mark.asyncio
    async def test_ml_processing_metrics_update(
        self,
        websocket_manager
    ):
        """Test ML processing metrics are tracked"""
        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={}
        )

        assert intelligence is not None

        # Verify processing metrics updated
        assert websocket_manager.metrics.avg_ml_processing_ms > 0
        assert len(websocket_manager._performance_history) > 0

    @pytest.mark.asyncio
    async def test_cache_hit_rate_tracking(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test cache hit rate is tracked correctly"""
        # Create intelligence with high cache hit rate
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        websocket_manager._update_ml_processing_metrics(35.0, intelligence)

        # Cache hit rate should be updated
        assert websocket_manager.metrics.cache_hit_rate > 0


class TestConcurrentConnections:
    """Test handling of concurrent connections"""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_subscriptions(
        self,
        websocket_manager
    ):
        """Test handling 100+ concurrent subscriptions"""
        subscription_tasks = []

        for i in range(100):
            mock_ws = AsyncMock()
            task = websocket_manager.subscribe_to_lead_intelligence(
                websocket=mock_ws,
                tenant_id=f"tenant_{i % 10}",  # 10 tenants
                user_id=f"user_{i}",
                topics=[SubscriptionTopic.LEAD_INTELLIGENCE]
            )
            subscription_tasks.append(task)

        # Execute all subscriptions concurrently
        subscription_ids = await asyncio.gather(*subscription_tasks)

        # Verify all subscriptions successful
        successful = [sid for sid in subscription_ids if sid is not None]
        assert len(successful) == 100

        # Verify metrics
        assert websocket_manager.metrics.active_subscriptions == 100

    @pytest.mark.asyncio
    async def test_concurrent_broadcast_performance(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test broadcast performance with concurrent operations"""
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        # Broadcast to multiple tenants concurrently
        broadcast_tasks = []
        for i in range(50):
            task = websocket_manager.broadcast_intelligence_update(
                tenant_id=f"tenant_{i}",
                intelligence=intelligence
            )
            broadcast_tasks.append(task)

        start_time = time.time()
        results = await asyncio.gather(*broadcast_tasks)
        total_time = (time.time() - start_time) * 1000

        # All broadcasts should succeed
        assert len(results) == 50

        # Average time per broadcast should be reasonable
        avg_time = total_time / 50
        assert avg_time < 150  # Allow some overhead for parallel execution


class TestConvenienceFunctions:
    """Test convenience wrapper functions"""

    @pytest.mark.asyncio
    async def test_subscribe_lead_intelligence_wrapper(self):
        """Test subscribe_lead_intelligence convenience function"""
        with patch('ghl_real_estate_ai.services.websocket_manager.get_websocket_manager') as mock_get:
            mock_manager = AsyncMock()
            mock_manager.subscribe_to_lead_intelligence = AsyncMock(return_value="sub_123")
            mock_get.return_value = mock_manager

            mock_ws = AsyncMock()
            subscription_id = await subscribe_lead_intelligence(
                websocket=mock_ws,
                tenant_id="tenant_123",
                user_id="user_456"
            )

            assert subscription_id == "sub_123"
            mock_manager.subscribe_to_lead_intelligence.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcast_lead_intelligence_wrapper(self):
        """Test broadcast_lead_intelligence convenience function"""
        with patch('ghl_real_estate_ai.services.websocket_manager.get_websocket_manager') as mock_get:
            mock_manager = AsyncMock()
            mock_result = Mock(connections_successful=10)
            mock_manager.broadcast_intelligence_update = AsyncMock(return_value=mock_result)
            mock_get.return_value = mock_manager

            mock_intelligence = Mock()
            result = await broadcast_lead_intelligence(
                tenant_id="tenant_123",
                intelligence=mock_intelligence
            )

            assert result.connections_successful == 10
            mock_manager.broadcast_intelligence_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_lead_event_realtime_wrapper(self):
        """Test process_lead_event_realtime convenience function"""
        with patch('ghl_real_estate_ai.services.websocket_manager.get_websocket_manager') as mock_get:
            mock_manager = AsyncMock()
            mock_intelligence = Mock(lead_id="lead_123")
            mock_manager.handle_ml_event = AsyncMock(return_value=mock_intelligence)
            mock_get.return_value = mock_manager

            intelligence = await process_lead_event_realtime(
                lead_id="lead_123",
                tenant_id="tenant_123",
                event_data={"type": "activity"}
            )

            assert intelligence.lead_id == "lead_123"
            mock_manager.handle_ml_event.assert_called_once()


class TestErrorHandlingAndResilience:
    """Test error handling and resilience patterns"""

    @pytest.mark.asyncio
    async def test_redis_connection_failure_resilience(
        self,
        websocket_manager,
        mock_redis_client
    ):
        """Test resilience when Redis connection fails"""
        mock_redis_client.get = AsyncMock(side_effect=Exception("Redis connection failed"))

        # Should still process event without cache
        intelligence = await websocket_manager.handle_ml_event(
            lead_id="lead_123",
            tenant_id="tenant_123",
            event_data={}
        )

        assert intelligence is not None

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure_handling(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Test handling of partial broadcast failures"""
        # Mock partial failure
        websocket_manager.websocket_hub.broadcast_to_tenant = AsyncMock(
            return_value=Mock(
                connections_targeted=10,
                connections_successful=7,
                connections_failed=3,
                broadcast_time_ms=45.0
            )
        )

        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        result = await websocket_manager.broadcast_intelligence_update(
            tenant_id="tenant_123",
            intelligence=intelligence
        )

        # Should track partial failure
        assert result.connections_successful == 7
        assert result.connections_failed == 3


# Performance benchmarks

@pytest.mark.benchmark
class TestPerformanceBenchmarks:
    """Performance benchmark tests"""

    @pytest.mark.asyncio
    async def test_subscription_latency_benchmark(
        self,
        websocket_manager,
        mock_websocket
    ):
        """Benchmark subscription latency"""
        latencies = []

        for _ in range(100):
            start = time.time()
            await websocket_manager.subscribe_to_lead_intelligence(
                websocket=mock_websocket,
                tenant_id="tenant_123",
                user_id="user_456"
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = sorted(latencies)[94]  # 95th percentile

        # Performance targets
        assert avg_latency < 50  # Average under 50ms
        assert p95_latency < 100  # 95th percentile under 100ms

    @pytest.mark.asyncio
    async def test_broadcast_latency_benchmark(
        self,
        websocket_manager,
        mock_ml_engine
    ):
        """Benchmark broadcast latency"""
        intelligence = await mock_ml_engine.process_lead_event_optimized(
            lead_id="lead_123",
            event_data={},
            priority=ProcessingPriority.HIGH
        )

        latencies = []

        for _ in range(100):
            start = time.time()
            await websocket_manager.broadcast_intelligence_update(
                tenant_id="tenant_123",
                intelligence=intelligence
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)

        # Should meet <100ms target
        assert avg_latency < 100
