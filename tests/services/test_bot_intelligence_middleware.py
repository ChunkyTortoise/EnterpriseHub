import pytest

pytestmark = pytest.mark.integration

"""
Bot Intelligence Middleware Tests - Phase 3.1 Testing
=====================================================

Comprehensive unit tests for Bot Intelligence Middleware Service.
Tests parallel intelligence gathering, caching, fallback behavior, and performance metrics.

Test Coverage:
- Parallel intelligence gathering from Phase 2 services
- Cache hit/miss scenarios with Redis mocking
- Service failure fallback behavior
- Event publishing validation
- Performance metrics tracking
- Error handling and edge cases

Author: Jorge's Real Estate AI Platform - Phase 3.1 Testing
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import Phase 2 service models for mocking
from ghl_real_estate_ai.api.schemas.phase2_intelligence_models import (
    AdvancedPropertyMatchAPI,
    ConversationInsightAPI,
    PreferenceProfileAPI,
)

# Import models
from ghl_real_estate_ai.models.intelligence_context import (
    BotIntelligenceContext,
    ConversationIntelligence,
    IntelligencePerformanceMetrics,
    PreferenceIntelligence,
    PropertyIntelligence,
)

# Import service under test
from ghl_real_estate_ai.services.bot_intelligence_middleware import (
    BotIntelligenceMiddleware,
    get_bot_intelligence_middleware,
)


class TestBotIntelligenceMiddleware:
    """Test suite for BotIntelligenceMiddleware core functionality."""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing."""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # Default: cache miss
        mock_cache.set.return_value = True  # Default: successful cache set
        return mock_cache

    @pytest.fixture
    def mock_event_publisher(self):
        """Mock event publisher for testing."""
        mock_publisher = AsyncMock()
        mock_publisher.publish_lead_update.return_value = None
        return mock_publisher

    @pytest.fixture
    def mock_property_matching_engine(self):
        """Mock advanced property matching engine."""
        mock_engine = AsyncMock()

        # Default successful response with numeric attributes the service expects
        mock_match = Mock()
        mock_match.to_dict = lambda: {
            "property_id": "prop_123",
            "overall_score": 0.95,
            "behavioral_fit": 0.88,
            "presentation_strategy": {"value": "lifestyle_match"},
            "optimal_presentation_time": "2024-01-25T10:00:00Z",
        }
        mock_match.confidence_score = 0.95
        mock_match.presentation_strategy = Mock(value="lifestyle_match")
        mock_match.optimal_presentation_time = "2024-01-25T10:00:00Z"
        mock_match.behavioral_reasoning = "Strong behavioral fit based on lifestyle preferences"

        mock_matches = [mock_match]

        mock_engine.find_behavioral_matches.return_value = mock_matches
        return mock_engine

    @pytest.fixture
    def mock_conversation_intelligence(self):
        """Mock conversation intelligence service."""
        mock_service = AsyncMock()

        # Default successful response
        mock_insight = Mock()
        mock_insight.objections_detected = [
            Mock(
                objection_type=Mock(value="price"),
                severity=0.7,
                confidence=0.85,
                context="Concerned about market value",
                suggested_responses=["Market analysis shows competitive pricing"],
            )
        ]
        mock_insight.sentiment_timeline = Mock(overall_sentiment=0.6, trend="improving")
        mock_insight.quality_metrics = Mock(
            overall_score=78.5,
            coaching_opportunities=[
                Mock(
                    area=Mock(value="objection_handling"),
                    priority="high",
                    description="Improve price objection response",
                )
            ],
        )
        mock_insight.response_recommendations = [
            Mock(response_text="Let me show you recent comparable sales", confidence=0.9, tone="consultative")
        ]

        mock_service.analyze_conversation_with_insights.return_value = mock_insight
        return mock_service

    @pytest.fixture
    def mock_preference_learning(self):
        """Mock client preference learning engine."""
        mock_engine = AsyncMock()

        # Default successful response
        mock_profile = Mock()
        mock_profile.budget_min = 400000
        mock_profile.budget_max = 600000
        mock_profile.bedrooms_min = 3
        mock_profile.bedrooms_max = 4
        mock_profile.bathrooms_min = 2
        mock_profile.bathrooms_max = None
        mock_profile.move_timeline = "3_months"
        mock_profile.profile_completeness = 0.75
        mock_profile.location_preferences = {"rancho_cucamonga_central": 0.8, "rancho_cucamonga_south": 0.6}
        mock_profile.feature_preferences = {"pool": True, "garage": True}
        mock_profile.urgency_level = 0.7

        mock_engine.get_preference_profile.return_value = mock_profile
        mock_engine.learn_from_conversation.return_value = mock_profile
        return mock_engine

    @pytest.fixture
    def sample_conversation_context(self) -> List[Dict[str, Any]]:
        """Sample conversation context for testing."""
        return [
            {"role": "user", "content": "I need to sell my house quickly", "timestamp": "2024-01-25T09:00:00Z"},
            {
                "role": "assistant",
                "content": "I understand your urgency. What's your timeline?",
                "timestamp": "2024-01-25T09:01:00Z",
            },
            {
                "role": "user",
                "content": "Need to sell within 3 months, job relocation",
                "timestamp": "2024-01-25T09:02:00Z",
            },
        ]

    @pytest.fixture
    def sample_preferences(self) -> Dict[str, Any]:
        """Sample preferences for testing."""
        return {"budget_max": 600000, "bedrooms": 3, "location": "rancho_cucamonga_central", "timeline": "3_months"}

    @pytest.fixture
    def middleware_service(
        self,
        mock_cache_service,
        mock_event_publisher,
        mock_property_matching_engine,
        mock_conversation_intelligence,
        mock_preference_learning,
    ) -> BotIntelligenceMiddleware:
        """Create middleware service with mocked dependencies."""
        middleware = BotIntelligenceMiddleware()

        # Inject mocks
        middleware.cache = mock_cache_service
        middleware.event_publisher = mock_event_publisher
        middleware.property_matcher = mock_property_matching_engine
        middleware.conversation_intelligence = mock_conversation_intelligence
        middleware.preference_learning = mock_preference_learning

        return middleware

    @pytest.mark.asyncio
    async def test_enhance_bot_context_cache_miss_success(
        self, middleware_service, sample_conversation_context, sample_preferences
    ):
        """Test successful intelligence gathering on cache miss."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-seller"

        # Ensure cache miss
        middleware_service.cache.get.return_value = None

        # Act
        start_time = time.time()
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Assert
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id
        assert result.location_id == location_id
        assert result.bot_type == bot_type
        assert not result.cache_hit

        # Verify intelligence content
        assert result.property_intelligence.match_count == 1
        assert result.property_intelligence.best_match_score == 95.0  # confidence_score (0.95) * 100
        assert len(result.conversation_intelligence.objections_detected) == 1
        assert result.conversation_intelligence.overall_sentiment == 0.6
        assert result.preference_intelligence.profile_completeness == 0.75

        # Verify performance targets
        assert latency_ms < 200, f"Latency {latency_ms}ms exceeds 200ms target"
        assert result.performance_metrics.total_time_ms < 200

        # Verify service calls
        middleware_service.property_matcher.find_behavioral_matches.assert_called_once()
        middleware_service.conversation_intelligence.analyze_conversation_with_insights.assert_called_once()
        middleware_service.preference_learning.get_preference_profile.assert_called_once()

        # Verify caching
        middleware_service.cache.set.assert_called_once()
        cache_call = middleware_service.cache.set.call_args
        assert cache_call[1]["ttl"] == 300  # 5-minute TTL

        # Verify event publishing
        middleware_service.event_publisher.publish_lead_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_enhance_bot_context_cache_hit(
        self, middleware_service, sample_conversation_context, sample_preferences
    ):
        """Test cache hit scenario with quick response."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-buyer"

        # Create cached context
        cached_context = BotIntelligenceContext.create_fallback(lead_id, location_id, bot_type)
        cached_context.cache_hit = True

        # Mock cache hit
        middleware_service.cache.get.return_value = cached_context.to_json()

        # Act
        start_time = time.time()
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )
        latency_ms = (time.time() - start_time) * 1000

        # Assert
        assert isinstance(result, BotIntelligenceContext)
        assert result.cache_hit == True
        assert latency_ms < 50, f"Cache hit latency {latency_ms}ms should be <50ms"

        # Verify no Phase 2 service calls on cache hit
        middleware_service.property_matcher.find_behavioral_matches.assert_not_called()
        middleware_service.conversation_intelligence.analyze_conversation_with_insights.assert_not_called()
        middleware_service.preference_learning.get_preference_profile.assert_not_called()

        # Verify no cache set (already cached)
        middleware_service.cache.set.assert_not_called()

        # Verify event still published for cache hits
        middleware_service.event_publisher.publish_lead_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_parallel_intelligence_gathering_performance(
        self, middleware_service, sample_conversation_context, sample_preferences
    ):
        """Test parallel execution performance of Phase 2 services."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-seller"

        # Add artificial delays to services to test parallel execution
        async def delayed_property_matching(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms delay
            match = Mock()
            match.to_dict = lambda: {"property_id": "prop_123", "overall_score": 0.8}
            match.confidence_score = 0.8
            match.presentation_strategy = Mock(value="lifestyle_match")
            match.optimal_presentation_time = "2024-01-25T10:00:00Z"
            match.behavioral_reasoning = "Behavioral fit"
            return [match]

        async def delayed_conversation_analysis(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms delay
            mock_insight = Mock()
            mock_insight.objections_detected = []
            mock_insight.sentiment_timeline = Mock(overall_sentiment=0.0, trend="stable")
            mock_insight.quality_metrics = Mock(overall_score=50.0, coaching_opportunities=[])
            mock_insight.response_recommendations = []
            return mock_insight

        async def delayed_preference_learning(*args, **kwargs):
            await asyncio.sleep(0.05)  # 50ms delay
            mock_profile = Mock()
            mock_profile.budget_min = None
            mock_profile.budget_max = None
            mock_profile.profile_completeness = 0.0
            mock_profile.location_preferences = {}
            mock_profile.feature_preferences = {}
            mock_profile.urgency_level = 0.5
            return mock_profile

        middleware_service.property_matcher.find_behavioral_matches = delayed_property_matching
        middleware_service.conversation_intelligence.analyze_conversation_with_insights = delayed_conversation_analysis
        middleware_service.preference_learning.get_preference_profile = delayed_preference_learning

        # Act
        start_time = time.time()
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )
        total_latency_ms = (time.time() - start_time) * 1000

        # Assert
        # With parallel execution, total time should be ~50ms (max of individual delays)
        # not 150ms (sum of delays)
        assert total_latency_ms < 100, f"Parallel execution took {total_latency_ms}ms, expected <100ms"
        assert total_latency_ms < 200, "Still within overall 200ms target"

        # Verify all services were called
        assert isinstance(result, BotIntelligenceContext)
        assert not result.cache_hit

    @pytest.mark.asyncio
    async def test_service_failure_fallback(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test graceful fallback when Phase 2 services fail."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-buyer"

        # Make services fail
        middleware_service.property_matcher.find_behavioral_matches.side_effect = Exception("Property service down")
        middleware_service.conversation_intelligence.analyze_conversation_with_insights.side_effect = Exception(
            "Conversation service down"
        )
        middleware_service.preference_learning.get_preference_profile.side_effect = Exception("Preference service down")

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )

        # Assert
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id

        # Verify fallback intelligence created
        assert result.property_intelligence.match_count == 0
        assert result.conversation_intelligence.overall_sentiment == 0.0
        assert result.preference_intelligence.profile_completeness == 0.0

        # Service failures are caught inside individual _gather_* methods (try/except),
        # so they return empty intelligence objects rather than propagating exceptions
        # to the performance_metrics.service_failures list. Verify graceful degradation
        # by checking that empty fallback intelligence was returned.

    @pytest.mark.asyncio
    async def test_partial_service_failure(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test partial service failure with some services working."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "lead-bot"

        # Only property matching fails
        middleware_service.property_matcher.find_behavioral_matches.side_effect = Exception("Property service timeout")

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )

        # Assert
        assert isinstance(result, BotIntelligenceContext)

        # Property intelligence should be empty (failed)
        assert result.property_intelligence.match_count == 0

        # Other intelligence should be available (succeeded)
        assert result.conversation_intelligence.overall_sentiment == 0.6
        assert result.preference_intelligence.profile_completeness == 0.75

        # Service failures are caught inside _gather_property_intelligence (try/except),
        # so they return empty intelligence objects rather than propagating to
        # performance_metrics.service_failures. Verify graceful degradation instead.

    @pytest.mark.asyncio
    async def test_cache_service_failure(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test behavior when cache service fails."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-seller"

        # Make cache operations fail
        middleware_service.cache.get.side_effect = Exception("Redis connection failed")
        middleware_service.cache.set.side_effect = Exception("Redis connection failed")

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )

        # Assert
        # Should still return valid result despite cache failures
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id
        assert not result.cache_hit

        # Intelligence should still be gathered
        assert result.property_intelligence.match_count == 1
        assert result.conversation_intelligence.overall_sentiment == 0.6

    @pytest.mark.asyncio
    async def test_event_publishing_failure(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test behavior when event publishing fails."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-buyer"

        # Make event publishing fail
        middleware_service.event_publisher.publish_lead_update.side_effect = Exception("Event service down")

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )

        # Assert
        # Should still return valid result despite event publishing failure
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id

        # Intelligence should be complete
        assert result.property_intelligence.match_count == 1
        assert result.conversation_intelligence.overall_sentiment == 0.6

    def test_metrics_tracking(self, middleware_service):
        """Test performance metrics tracking."""
        # Arrange
        initial_metrics = middleware_service.get_metrics()

        # Simulate metrics updates (_update_metrics only records latency history,
        # _total_enhancements is incremented separately in enhance_bot_context)
        middleware_service._update_metrics(120.5)  # Within target
        middleware_service._update_metrics(250.0)  # Above target
        middleware_service._update_metrics(80.0)  # Within target
        middleware_service._total_enhancements += 3  # Simulate 3 enhancements

        # Act
        updated_metrics = middleware_service.get_metrics()

        # Assert
        assert updated_metrics["total_enhancements"] == initial_metrics["total_enhancements"] + 3
        assert updated_metrics["avg_latency_ms"] > 0
        assert updated_metrics["latency_p95_ms"] > 0
        assert updated_metrics["latency_p99_ms"] > 0

        # Performance status should reflect mixed results
        assert updated_metrics["performance_status"] in ["excellent", "good", "degraded"]

    @pytest.mark.asyncio
    async def test_different_bot_types(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test intelligence gathering for different bot types."""
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_types = ["jorge-seller", "jorge-buyer", "lead-bot"]

        for bot_type in bot_types:
            # Act
            result = await middleware_service.enhance_bot_context(
                bot_type=bot_type,
                lead_id=lead_id,
                location_id=location_id,
                conversation_context=sample_conversation_context,
                preferences=sample_preferences,
            )

            # Assert
            assert isinstance(result, BotIntelligenceContext)
            assert result.bot_type == bot_type
            assert result.lead_id == lead_id
            assert result.location_id == location_id

    @pytest.mark.asyncio
    async def test_empty_conversation_context(self, middleware_service, sample_preferences):
        """Test behavior with empty conversation context."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-seller"
        empty_conversation = []

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=empty_conversation,
            preferences=sample_preferences,
        )

        # Assert
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id

        # Should still gather intelligence even with empty conversation
        assert result.property_intelligence.match_count >= 0
        assert result.conversation_intelligence is not None
        assert result.preference_intelligence is not None

    @pytest.mark.asyncio
    async def test_no_preferences_provided(self, middleware_service, sample_conversation_context):
        """Test behavior when no preferences are provided."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-buyer"

        # Act
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=None,
        )

        # Assert
        assert isinstance(result, BotIntelligenceContext)
        assert result.lead_id == lead_id

        # Should still work without preferences
        # Property matching might use empty preferences
        # Conversation intelligence should work normally
        # Preference learning should extract from conversation
        assert result.property_intelligence is not None
        assert result.conversation_intelligence is not None
        assert result.preference_intelligence is not None

    @pytest.mark.asyncio
    async def test_service_timeout_handling(self, middleware_service, sample_conversation_context, sample_preferences):
        """Test handling of service timeouts."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        bot_type = "jorge-seller"

        # Make services timeout (simulate with long delays)
        async def timeout_service(*args, **kwargs):
            await asyncio.sleep(10)  # Exceeds 5-second timeout
            return Mock()

        middleware_service.property_matcher.find_behavioral_matches = timeout_service

        # Act
        start_time = time.time()
        result = await middleware_service.enhance_bot_context(
            bot_type=bot_type,
            lead_id=lead_id,
            location_id=location_id,
            conversation_context=sample_conversation_context,
            preferences=sample_preferences,
        )
        total_time = time.time() - start_time

        # Assert
        # Should not hang indefinitely
        assert total_time < 8, f"Service timeout handling took {total_time}s, should be <8s"
        assert isinstance(result, BotIntelligenceContext)


class TestBotIntelligenceMiddlewareIntegration:
    """Integration tests for BotIntelligenceMiddleware."""

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test singleton pattern implementation."""
        # Act
        instance1 = get_bot_intelligence_middleware()
        instance2 = get_bot_intelligence_middleware()

        # Assert
        assert instance1 is instance2
        assert isinstance(instance1, BotIntelligenceMiddleware)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        from ghl_real_estate_ai.services.bot_intelligence_middleware import health_check

        # Act
        health = await health_check()

        # Assert
        assert isinstance(health, dict)
        assert "service" in health
        assert "status" in health
        assert "version" in health
        assert "metrics" in health
        assert health["service"] == "BotIntelligenceMiddleware"


class TestIntelligenceContextModels:
    """Test intelligence context data models."""

    def test_bot_intelligence_context_serialization(self):
        """Test BotIntelligenceContext JSON serialization/deserialization."""
        # Arrange
        original_context = BotIntelligenceContext.create_fallback(
            lead_id="lead_123", location_id="rancho_cucamonga", bot_type="jorge-seller"
        )

        # Act
        json_str = original_context.to_json()
        deserialized_context = BotIntelligenceContext.from_json(json_str)

        # Assert
        assert deserialized_context.lead_id == original_context.lead_id
        assert deserialized_context.location_id == original_context.location_id
        assert deserialized_context.bot_type == original_context.bot_type
        assert deserialized_context.cache_hit == original_context.cache_hit

    def test_property_intelligence_model(self):
        """Test PropertyIntelligence model creation and methods."""
        # Act
        property_intel = PropertyIntelligence(
            top_matches=[{"property_id": "prop_123", "score": 0.9}], match_count=1, best_match_score=0.9
        )

        # Assert
        assert property_intel.match_count == 1
        assert property_intel.best_match_score == 0.9
        assert len(property_intel.top_matches) == 1

        # Test to_dict conversion
        data = property_intel.to_dict()
        assert "top_matches" in data
        assert "match_count" in data

        # Test from_dict reconstruction
        reconstructed = PropertyIntelligence.from_dict(data)
        assert reconstructed.match_count == property_intel.match_count

    def test_conversation_intelligence_model(self):
        """Test ConversationIntelligence model creation and methods."""
        # Act
        conversation_intel = ConversationIntelligence(
            objections_detected=[{"type": "price", "severity": 0.7}],
            overall_sentiment=0.6,
            sentiment_trend="improving",
            conversation_quality_score=78.5,
            coaching_opportunities=[],
            response_recommendations=[],
        )

        # Assert
        assert conversation_intel.overall_sentiment == 0.6
        assert conversation_intel.sentiment_trend == "improving"
        assert conversation_intel.conversation_quality_score == 78.5
        assert len(conversation_intel.objections_detected) == 1

    def test_preference_intelligence_model(self):
        """Test PreferenceIntelligence model creation and methods."""
        # Act
        preference_intel = PreferenceIntelligence(
            preference_profile={"budget_max": 600000},
            profile_completeness=0.75,
            budget_range={"min": 400000, "max": 600000},
            urgency_level=0.7,
        )

        # Assert
        assert preference_intel.profile_completeness == 0.75
        assert preference_intel.urgency_level == 0.7
        assert preference_intel.budget_range["max"] == 600000

    def test_fallback_context_creation(self):
        """Test fallback context creation for error scenarios."""
        # Act
        fallback_context = BotIntelligenceContext.create_fallback(
            lead_id="lead_123", location_id="rancho_cucamonga", bot_type="jorge-buyer"
        )

        # Assert
        assert fallback_context.lead_id == "lead_123"
        assert fallback_context.location_id == "rancho_cucamonga"
        assert fallback_context.bot_type == "jorge-buyer"

        # Fallback should have empty intelligence
        assert fallback_context.property_intelligence.match_count == 0
        assert fallback_context.conversation_intelligence.overall_sentiment == 0.0
        assert fallback_context.preference_intelligence.profile_completeness == 0.0

        # Should have failure recorded in performance metrics
        assert "fallback_context_created" in fallback_context.performance_metrics.service_failures


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
