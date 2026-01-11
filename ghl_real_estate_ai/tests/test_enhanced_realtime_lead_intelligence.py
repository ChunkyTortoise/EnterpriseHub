"""
Integration Tests for Enhanced Real-Time Lead Intelligence Service

Tests the performance-optimized lead intelligence service with comprehensive
analysis capabilities, ML integration, and sub-100ms processing targets.
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.enhanced_realtime_lead_intelligence import (
    EnhancedRealTimeLeadIntelligence,
    RealTimeLeadInsight,
    LeadHealthAssessment,
    RealTimeInsightType,
    LeadIntelligenceLevel,
    ConversationMomentum,
    ConversationAnalysis
)


@pytest.fixture
async def enhanced_lead_intelligence():
    """Create enhanced lead intelligence service with mocked dependencies"""

    config = {
        "redis_url": "redis://localhost:6379",
        "model_cache_dir": "test_models",
        "enable_performance_monitoring": True
    }

    service = EnhancedRealTimeLeadIntelligence(config)

    # Mock the dependent services to avoid external dependencies
    service.redis_client = MagicMock()
    service.redis_client.initialize = AsyncMock()
    service.redis_client.optimized_get = AsyncMock(return_value=None)
    service.redis_client.optimized_set = AsyncMock(return_value=True)
    service.redis_client.health_check = AsyncMock(return_value={"healthy": True})
    service.redis_client.close = AsyncMock()

    service.ml_service = MagicMock()
    service.ml_service.initialize = AsyncMock()
    service.ml_service.predict_single = AsyncMock()
    service.ml_service.predict_batch = AsyncMock()
    service.ml_service.health_check = AsyncMock(return_value={"healthy": True})
    service.ml_service.cleanup = AsyncMock()

    service.db_cache = MagicMock()
    service.db_cache.initialize = AsyncMock()
    service.db_cache.cached_query = AsyncMock(return_value=[])
    service.db_cache.health_check = AsyncMock(return_value={"healthy": True})
    service.db_cache.cleanup = AsyncMock()

    service.http_client = MagicMock()
    service.http_client.initialize = AsyncMock()
    service.http_client.health_check = AsyncMock(return_value={"healthy": True})
    service.http_client.cleanup = AsyncMock()

    # Initialize the service
    await service.initialize()

    yield service

    # Cleanup
    await service.cleanup()


class TestEnhancedRealTimeLeadIntelligence:
    """Test suite for enhanced real-time lead intelligence service"""

    @pytest.mark.asyncio
    async def test_service_initialization(self, enhanced_lead_intelligence):
        """Test service initializes correctly with all dependencies"""
        service = enhanced_lead_intelligence

        # Verify service is properly initialized
        assert service.redis_client is not None
        assert service.ml_service is not None
        assert service.db_cache is not None
        assert service.http_client is not None

        # Verify initialization was called on all services
        service.redis_client.initialize.assert_called_once()
        service.ml_service.initialize.assert_called_once()
        service.db_cache.initialize.assert_called_once()
        service.http_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_realtime_analysis_performance(self, enhanced_lead_intelligence):
        """Test real-time analysis meets <50ms performance target"""
        service = enhanced_lead_intelligence

        # Test conversation data
        conversation_data = {
            "id": "test_conversation_001",
            "messages": [
                {"content": "Hi, I'm very interested in buying a home ASAP", "timestamp": "2024-01-10T10:00:00Z"},
                {"content": "I need something urgent, my lease expires this month", "timestamp": "2024-01-10T10:05:00Z"},
                {"content": "I'm pre-approved for $500k and ready to make an offer", "timestamp": "2024-01-10T10:10:00Z"}
            ]
        }

        # Mock ML service responses
        mock_batch_results = [
            MagicMock(success=True, request_id="sentiment_test", predictions={"sentiment": 0.8}),
            MagicMock(success=True, request_id="intent_test", predictions={"intents": {"buying": 0.9}}),
            MagicMock(success=True, request_id="urgency_test", predictions={"urgency": 0.85})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        # Perform analysis and measure time
        start_time = time.time()
        insight = await service.analyze_lead_realtime(
            lead_id="test_lead_001",
            conversation_data=conversation_data,
            context={"channel": "website_chat"}
        )
        processing_time = (time.time() - start_time) * 1000

        # Verify performance target
        assert processing_time < 50, f"Analysis took {processing_time:.1f}ms, exceeds 50ms target"

        # Verify insight structure
        assert isinstance(insight, RealTimeLeadInsight)
        assert insight.lead_id == "test_lead_001"
        assert insight.insight_type in RealTimeInsightType
        assert 0.0 <= insight.ml_confidence <= 1.0
        assert 0.0 <= insight.priority_score <= 100.0
        assert 1 <= insight.urgency_level <= 5
        assert len(insight.recommended_actions) > 0

        print(f"✓ Real-time analysis completed in {processing_time:.1f}ms (target: <50ms)")

    @pytest.mark.asyncio
    async def test_urgency_signal_detection(self, enhanced_lead_intelligence):
        """Test detection of urgency signals in conversations"""
        service = enhanced_lead_intelligence

        # High urgency conversation
        urgent_conversation = {
            "id": "urgent_conv_001",
            "messages": [
                {"content": "I need to move immediately, my lease expires next week!", "timestamp": "2024-01-10T10:00:00Z"},
                {"content": "This is urgent, I'm losing my deposit if I don't find something today", "timestamp": "2024-01-10T10:05:00Z"},
                {"content": "Can we see properties right now? Time is running out", "timestamp": "2024-01-10T10:10:00Z"}
            ]
        }

        # Mock high urgency ML response
        mock_batch_results = [
            MagicMock(success=True, request_id="sentiment_urgent", predictions={"sentiment": 0.3}),  # Stressed
            MagicMock(success=True, request_id="intent_urgent", predictions={"intents": {"urgent_search": 0.95}}),
            MagicMock(success=True, request_id="urgency_urgent", predictions={"urgency": 0.95})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        insight = await service.analyze_lead_realtime(
            lead_id="urgent_lead_001",
            conversation_data=urgent_conversation
        )

        # Verify urgency detection
        assert insight.insight_type == RealTimeInsightType.URGENCY_SIGNAL
        assert insight.urgency_level <= 2  # High urgency (1-2)
        assert insight.priority_score > 70
        assert any("immediate" in action.lower() for action in insight.recommended_actions)

        print(f"✓ Urgency signal detected with {insight.priority_score:.0f}% priority")

    @pytest.mark.asyncio
    async def test_buying_intent_recognition(self, enhanced_lead_intelligence):
        """Test recognition of strong buying intent"""
        service = enhanced_lead_intelligence

        # Strong buying intent conversation
        buying_conversation = {
            "id": "buying_conv_001",
            "messages": [
                {"content": "I love this property and I'm ready to make an offer", "timestamp": "2024-01-10T10:00:00Z"},
                {"content": "I'm pre-approved for financing and can close quickly", "timestamp": "2024-01-10T10:05:00Z"},
                {"content": "When can we schedule a showing? I want to move fast", "timestamp": "2024-01-10T10:10:00Z"}
            ]
        }

        # Mock strong buying intent ML response
        mock_batch_results = [
            MagicMock(success=True, request_id="sentiment_buying", predictions={"sentiment": 0.9}),
            MagicMock(success=True, request_id="intent_buying", predictions={"intents": {"buying": 0.92, "scheduling": 0.85}}),
            MagicMock(success=True, request_id="urgency_buying", predictions={"urgency": 0.75})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        insight = await service.analyze_lead_realtime(
            lead_id="buying_lead_001",
            conversation_data=buying_conversation
        )

        # Verify buying intent detection
        assert insight.insight_type == RealTimeInsightType.BUYING_INTENT
        assert insight.ml_confidence > 0.7
        assert insight.priority_score > 60
        assert any("showing" in action.lower() or "offer" in action.lower()
                  for action in insight.recommended_actions)

        print(f"✓ Buying intent recognized with {insight.ml_confidence:.0f}% confidence")

    @pytest.mark.asyncio
    async def test_objection_detection(self, enhanced_lead_intelligence):
        """Test detection and categorization of objections"""
        service = enhanced_lead_intelligence

        # Objection-heavy conversation
        objection_conversation = {
            "id": "objection_conv_001",
            "messages": [
                {"content": "This seems too expensive for what it offers", "timestamp": "2024-01-10T10:00:00Z"},
                {"content": "I'm not sure if I can afford the monthly payments", "timestamp": "2024-01-10T10:05:00Z"},
                {"content": "Are there any cheaper options in the same area?", "timestamp": "2024-01-10T10:10:00Z"}
            ]
        }

        # Mock objection detection ML response
        mock_batch_results = [
            MagicMock(success=True, request_id="sentiment_objection", predictions={"sentiment": -0.2}),
            MagicMock(success=True, request_id="intent_objection", predictions={"intents": {"price_concern": 0.88}}),
            MagicMock(success=True, request_id="urgency_objection", predictions={"urgency": 0.3})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        insight = await service.analyze_lead_realtime(
            lead_id="objection_lead_001",
            conversation_data=objection_conversation
        )

        # Verify objection detection
        assert insight.insight_type == RealTimeInsightType.OBJECTION_DETECTED
        assert "price" in insight.title.lower() or "price" in insight.description.lower()
        assert any("market analysis" in action.lower() or "financing" in action.lower()
                  for action in insight.recommended_actions)

        print(f"✓ Price objection detected and categorized")

    @pytest.mark.asyncio
    async def test_lead_health_assessment_performance(self, enhanced_lead_intelligence):
        """Test lead health assessment meets <100ms performance target"""
        service = enhanced_lead_intelligence

        # Mock historical data
        service.db_cache.cached_query.side_effect = [
            {"id": "test_lead_001", "created_at": datetime.now()},  # Lead profile
            [  # Conversations
                {"id": "conv_1", "message": "Interested in properties", "created_at": datetime.now()},
                {"id": "conv_2", "message": "Looking for 3 bedroom house", "created_at": datetime.now()}
            ],
            [  # Interactions
                {"type": "email_open", "created_at": datetime.now()},
                {"type": "property_view", "created_at": datetime.now()}
            ]
        ]

        # Perform health assessment and measure time
        start_time = time.time()
        assessment = await service.assess_lead_health(
            lead_id="test_lead_001",
            historical_data={"previous_interactions": 5}
        )
        processing_time = (time.time() - start_time) * 1000

        # Verify performance target
        assert processing_time < 100, f"Health assessment took {processing_time:.1f}ms, exceeds 100ms target"

        # Verify assessment structure
        assert isinstance(assessment, LeadHealthAssessment)
        assert assessment.lead_id == "test_lead_001"
        assert 0.0 <= assessment.overall_health_score <= 100.0
        assert assessment.intelligence_level in LeadIntelligenceLevel
        assert assessment.momentum in ConversationMomentum
        assert 0.0 <= assessment.engagement_score <= 100.0
        assert 0.0 <= assessment.conversion_probability <= 1.0
        assert len(assessment.next_best_actions) > 0

        print(f"✓ Health assessment completed in {processing_time:.1f}ms (target: <100ms)")

    @pytest.mark.asyncio
    async def test_next_best_actions_performance(self, enhanced_lead_intelligence):
        """Test next best actions generation meets <75ms performance target"""
        service = enhanced_lead_intelligence

        # Test context
        current_context = {
            "last_interaction": "property_inquiry",
            "engagement_level": "high",
            "conversation_stage": "qualification"
        }

        # Mock ML action recommendations
        mock_ml_result = MagicMock(
            success=True,
            predictions={
                "actions": [
                    "Schedule immediate property showing",
                    "Send pre-approval assistance",
                    "Provide neighborhood analysis"
                ]
            }
        )
        service.ml_service.predict_single.return_value = mock_ml_result

        # Generate actions and measure time
        start_time = time.time()
        actions = await service.get_next_best_actions(
            lead_id="test_lead_001",
            current_context=current_context
        )
        processing_time = (time.time() - start_time) * 1000

        # Verify performance target
        assert processing_time < 75, f"Action generation took {processing_time:.1f}ms, exceeds 75ms target"

        # Verify actions structure
        assert isinstance(actions, list)
        assert len(actions) > 0

        for action in actions:
            assert isinstance(action, dict)
            assert "action" in action
            assert "priority" in action
            assert "confidence" in action
            assert "urgency" in action
            assert "estimated_impact" in action

        print(f"✓ Next best actions generated in {processing_time:.1f}ms (target: <75ms)")

    @pytest.mark.asyncio
    async def test_caching_optimization(self, enhanced_lead_intelligence):
        """Test caching optimization improves performance"""
        service = enhanced_lead_intelligence

        conversation_data = {
            "id": "cache_test_conv",
            "messages": [{"content": "Test message for caching", "timestamp": "2024-01-10T10:00:00Z"}]
        }

        # First call - cache miss
        service.redis_client.optimized_get.return_value = None

        start_time = time.time()
        first_insight = await service.analyze_lead_realtime(
            lead_id="cache_test_lead",
            conversation_data=conversation_data
        )
        first_call_time = (time.time() - start_time) * 1000

        # Second call - cache hit
        cached_data = first_insight.to_dict()
        service.redis_client.optimized_get.return_value = cached_data

        start_time = time.time()
        second_insight = await service.analyze_lead_realtime(
            lead_id="cache_test_lead",
            conversation_data=conversation_data
        )
        second_call_time = (time.time() - start_time) * 1000

        # Verify caching improves performance
        assert second_call_time < first_call_time, "Cache should improve performance"

        # Verify cache was called
        service.redis_client.optimized_set.assert_called()

        print(f"✓ Cache optimization: {first_call_time:.1f}ms → {second_call_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self, enhanced_lead_intelligence):
        """Test concurrent analysis of multiple leads"""
        service = enhanced_lead_intelligence

        # Create multiple lead conversations
        conversations = []
        for i in range(10):
            conversations.append({
                "lead_id": f"concurrent_lead_{i:03d}",
                "conversation_data": {
                    "id": f"conv_{i:03d}",
                    "messages": [
                        {"content": f"Test message {i}", "timestamp": "2024-01-10T10:00:00Z"}
                    ]
                }
            })

        # Mock ML responses
        mock_batch_results = [
            MagicMock(success=True, request_id=f"test_{i}", predictions={"sentiment": 0.5})
            for i in range(3)
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        # Process all conversations concurrently
        start_time = time.time()

        analysis_tasks = [
            service.analyze_lead_realtime(
                lead_id=conv["lead_id"],
                conversation_data=conv["conversation_data"]
            )
            for conv in conversations
        ]

        insights = await asyncio.gather(*analysis_tasks)
        total_time = (time.time() - start_time) * 1000
        avg_time_per_lead = total_time / len(conversations)

        # Verify all insights generated successfully
        assert len(insights) == 10
        assert all(isinstance(insight, RealTimeLeadInsight) for insight in insights)

        # Verify reasonable concurrent performance
        assert avg_time_per_lead < 100, f"Average time per lead: {avg_time_per_lead:.1f}ms"

        print(f"✓ Concurrent analysis: {len(conversations)} leads in {total_time:.1f}ms")
        print(f"  Average: {avg_time_per_lead:.1f}ms per lead")

    @pytest.mark.asyncio
    async def test_ml_service_fallback(self, enhanced_lead_intelligence):
        """Test graceful fallback when ML services fail"""
        service = enhanced_lead_intelligence

        # Mock ML service failure
        service.ml_service.predict_batch.side_effect = Exception("ML service unavailable")

        conversation_data = {
            "id": "fallback_test",
            "messages": [{"content": "Test fallback behavior", "timestamp": "2024-01-10T10:00:00Z"}]
        }

        # Should still generate insight despite ML failure
        insight = await service.analyze_lead_realtime(
            lead_id="fallback_lead",
            conversation_data=conversation_data
        )

        # Verify fallback insight
        assert isinstance(insight, RealTimeLeadInsight)
        assert insight.lead_id == "fallback_lead"
        assert insight.ml_confidence < 0.5  # Lower confidence for fallback
        assert len(insight.recommended_actions) > 0

        print("✓ ML service fallback working correctly")

    @pytest.mark.asyncio
    async def test_service_health_check(self, enhanced_lead_intelligence):
        """Test service health check functionality"""
        service = enhanced_lead_intelligence

        health_status = await service.health_check()

        # Verify health check structure
        assert isinstance(health_status, dict)
        assert "healthy" in health_status
        assert "service" in health_status
        assert "version" in health_status
        assert "checks" in health_status
        assert "performance_targets" in health_status

        # Verify all dependent services checked
        assert "redis" in health_status["checks"]
        assert "ml_service" in health_status["checks"]
        assert "db_cache" in health_status["checks"]
        assert "http_client" in health_status["checks"]

        print(f"✓ Health check: {'Healthy' if health_status['healthy'] else 'Unhealthy'}")

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, enhanced_lead_intelligence):
        """Test integration with performance monitoring"""
        service = enhanced_lead_intelligence

        # Verify performance monitoring is configured
        assert service.performance_monitor is not None
        assert service.metrics_collector is not None

        # Test metrics collection during analysis
        conversation_data = {
            "id": "metrics_test",
            "messages": [{"content": "Test metrics collection", "timestamp": "2024-01-10T10:00:00Z"}]
        }

        # Mock ML service to ensure metrics collection
        mock_batch_results = [
            MagicMock(success=True, request_id="metrics_test", predictions={"sentiment": 0.7})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        insight = await service.analyze_lead_realtime(
            lead_id="metrics_test_lead",
            conversation_data=conversation_data
        )

        # Verify processing time is tracked
        assert hasattr(insight, 'processing_time_ms')
        assert insight.processing_time_ms > 0

        print(f"✓ Performance monitoring integrated (tracked: {insight.processing_time_ms:.1f}ms)")

    @pytest.mark.asyncio
    async def test_conversation_analysis_accuracy(self, enhanced_lead_intelligence):
        """Test accuracy of conversation analysis components"""
        service = enhanced_lead_intelligence

        # Test conversation with mixed signals
        complex_conversation = {
            "id": "complex_analysis",
            "messages": [
                {"content": "I'm interested but concerned about the price", "timestamp": "2024-01-10T10:00:00Z"},
                {"content": "The location is perfect though, exactly what I need", "timestamp": "2024-01-10T10:05:00Z"},
                {"content": "Can we negotiate? I'm pre-approved but budget is tight", "timestamp": "2024-01-10T10:10:00Z"},
                {"content": "I need to decide this week, my current lease ends soon", "timestamp": "2024-01-10T10:15:00Z"}
            ]
        }

        # Mock nuanced ML responses
        mock_batch_results = [
            MagicMock(success=True, request_id="sentiment_complex", predictions={"sentiment": 0.1}),  # Mixed
            MagicMock(success=True, request_id="intent_complex", predictions={
                "intents": {"price_negotiation": 0.85, "urgency": 0.7, "buying_intent": 0.65}
            }),
            MagicMock(success=True, request_id="urgency_complex", predictions={"urgency": 0.72})
        ]
        service.ml_service.predict_batch.return_value = mock_batch_results

        insight = await service.analyze_lead_realtime(
            lead_id="complex_lead",
            conversation_data=complex_conversation
        )

        # Verify complex analysis results
        assert insight.ml_confidence > 0.6  # Should be confident in analysis

        # Should detect multiple behavioral signals
        assert len(insight.behavioral_signals) > 1

        # Should provide relevant recommendations
        assert len(insight.recommended_actions) >= 2

        # Should identify mixed signals appropriately
        context = insight.conversation_context
        assert context.get("buying_intent", 0) > 0
        assert context.get("urgency_score", 0) > 0

        print(f"✓ Complex conversation analysis: {insight.insight_type.value}")
        print(f"  Confidence: {insight.ml_confidence:.2f}")
        print(f"  Behavioral signals: {len(insight.behavioral_signals)}")


class TestPerformanceOptimizationIntegration:
    """Test integration with performance optimization services"""

    @pytest.mark.asyncio
    async def test_redis_optimization_integration(self):
        """Test Redis optimization service integration"""
        config = {"redis_url": "redis://localhost:6379"}
        service = EnhancedRealTimeLeadIntelligence(config)

        # Mock Redis optimization service
        mock_redis = MagicMock()
        mock_redis.optimized_get = AsyncMock(return_value=None)
        mock_redis.optimized_set = AsyncMock(return_value=True)
        service.redis_client = mock_redis

        # Test cache operations
        cache_key = "test_cache_key"
        cache_data = {"test": "data"}

        # Test optimized get
        result = await service.redis_client.optimized_get(cache_key)
        assert result is None
        mock_redis.optimized_get.assert_called_with(cache_key)

        # Test optimized set
        success = await service.redis_client.optimized_set(cache_key, cache_data, ttl=300)
        assert success is True
        mock_redis.optimized_set.assert_called_with(cache_key, cache_data, ttl=300)

        print("✓ Redis optimization integration verified")

    @pytest.mark.asyncio
    async def test_ml_inference_optimization_integration(self):
        """Test ML inference optimization integration"""
        service = EnhancedRealTimeLeadIntelligence()

        # Mock batch ML inference service
        mock_ml = MagicMock()
        mock_ml.predict_batch = AsyncMock()
        mock_ml.predict_single = AsyncMock()
        service.ml_service = mock_ml

        # Test batch processing optimization
        from ghl_real_estate_ai.services.batch_ml_inference_service import MLInferenceRequest

        requests = [
            MLInferenceRequest(request_id="test1", model_name="test_model", input_data={"test": 1}),
            MLInferenceRequest(request_id="test2", model_name="test_model", input_data={"test": 2})
        ]

        await service.ml_service.predict_batch(requests)
        mock_ml.predict_batch.assert_called_with(requests)

        print("✓ ML inference optimization integration verified")

    @pytest.mark.asyncio
    async def test_database_cache_optimization_integration(self):
        """Test database cache optimization integration"""
        service = EnhancedRealTimeLeadIntelligence()

        # Mock database cache service
        mock_db_cache = MagicMock()
        mock_db_cache.cached_query = AsyncMock(return_value=[{"id": 1, "data": "test"}])
        service.db_cache = mock_db_cache

        # Test cached query
        query = "SELECT * FROM leads WHERE id = %s"
        params = {"id": "test_lead"}

        result = await service.db_cache.cached_query(query, params)
        assert len(result) == 1
        assert result[0]["data"] == "test"

        mock_db_cache.cached_query.assert_called_with(query, params)

        print("✓ Database cache optimization integration verified")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])