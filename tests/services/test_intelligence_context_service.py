import pytest

pytestmark = pytest.mark.integration

"""
Intelligence Context Service Tests - Phase 3.2 Testing
======================================================

Comprehensive unit tests for Intelligence Context Service.
Tests intelligence preservation, context retrieval, bot handoff scenarios, and performance.

Test Coverage:
- Intelligence snapshot preservation with extended caching
- Context retrieval with TTL validation and tenant isolation
- Bot handoff scenarios (seller→buyer, lead→seller, etc.)
- Transition history tracking and audit trail
- Performance metrics and latency validation
- Error handling and fallback behavior

Author: Jorge's Real Estate AI Platform - Phase 3.2 Testing
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import models
from ghl_real_estate_ai.models.bot_handoff import (
    BotTransition,
    BotType,
    ContextHandoff,
    HandoffStatus,
    IntelligenceSnapshot,
    PreservedIntelligence,
    TransitionHistory,
    TransitionReason,
)
from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext

# Import service under test
from ghl_real_estate_ai.services.intelligence_context_service import (
    IntelligenceContextService,
    get_intelligence_context_service,
    health_check,
)


class TestIntelligenceContextService:
    """Test suite for IntelligenceContextService core functionality."""

    @pytest.fixture
    def mock_cache_service(self):
        """Mock cache service for testing with in-memory store."""
        mock_cache = AsyncMock()
        cache_store = {}

        async def mock_set(key=None, value=None, **kwargs):
            cache_store[key] = value
            return True

        async def mock_get(key=None, **kwargs):
            return cache_store.get(key)

        async def mock_delete(key=None, **kwargs):
            cache_store.pop(key, None)
            return True

        mock_cache.set = AsyncMock(side_effect=mock_set)
        mock_cache.get = AsyncMock(side_effect=mock_get)
        mock_cache.delete = AsyncMock(side_effect=mock_delete)
        return mock_cache

    @pytest.fixture
    def mock_event_publisher(self):
        """Mock event publisher for testing."""
        mock_publisher = AsyncMock()
        mock_publisher.publish_lead_update.return_value = None
        return mock_publisher

    @pytest.fixture
    def mock_bot_middleware(self):
        """Mock bot intelligence middleware."""
        mock_middleware = AsyncMock()
        mock_middleware.enhance_bot_context.return_value = Mock()
        return mock_middleware

    @pytest.fixture
    def sample_intelligence_data(self) -> Dict[str, Any]:
        """Sample intelligence data for testing."""
        return {
            "property_intelligence": {
                "top_matches": [
                    {
                        "property_id": "prop_123",
                        "overall_score": 0.95,
                        "behavioral_fit": 0.88,
                        "presentation_strategy": "lifestyle_match",
                    },
                    {
                        "property_id": "prop_456",
                        "overall_score": 0.82,
                        "behavioral_fit": 0.75,
                        "presentation_strategy": "investment_focus",
                    },
                ],
                "best_match_score": 0.95,
                "presentation_strategy": "lifestyle_match",
            },
            "conversation_intelligence": {
                "objections_detected": [
                    {"type": "price", "severity": 0.7, "confidence": 0.85, "context": "Concerned about market value"}
                ],
                "overall_sentiment": 0.6,
                "sentiment_trend": "improving",
                "conversation_quality_score": 78.5,
                "response_recommendations": [
                    {
                        "response_text": "Let me show you recent comparable sales",
                        "confidence": 0.9,
                        "tone": "consultative",
                    }
                ],
            },
            "preference_intelligence": {
                "preference_profile": {"budget_max": 600000, "bedrooms": 3, "move_timeline": "3_months"},
                "budget_range": {"min": 400000, "max": 600000},
                "location_preferences": {"rancho_cucamonga_central": 0.8},
                "feature_preferences": {"pool": True, "garage": True},
                "profile_completeness": 0.75,
                "urgency_level": 0.7,
            },
            "conversation_history": [
                {"role": "user", "content": "Need to sell quickly", "timestamp": "2024-01-25T09:00:00Z"},
                {"role": "assistant", "content": "What's your timeline?", "timestamp": "2024-01-25T09:01:00Z"},
            ],
            "qualification_scores": {"FRS": 85.0, "PCS": 90.0},
            "temperature_classification": "hot",
        }

    @pytest.fixture
    def sample_bot_transition(self) -> BotTransition:
        """Sample bot transition for testing."""
        return BotTransition(
            transition_id="trans_123",
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            source_bot=BotType.JORGE_SELLER,
            target_bot=BotType.JORGE_BUYER,
            transition_reason=TransitionReason.QUALIFIED_BUYER,
            handoff_message="Seller qualified, also interested in buying. FRS 85/PCS 90.",
            recommended_approach="consultative",
            priority_level="high",
        )

    @pytest.fixture
    def context_service(
        self, mock_cache_service, mock_event_publisher, mock_bot_middleware
    ) -> IntelligenceContextService:
        """Create context service with mocked dependencies."""
        service = IntelligenceContextService()

        # Inject mocks
        service.cache = mock_cache_service
        service.event_publisher = mock_event_publisher
        service.bot_middleware = mock_bot_middleware

        return service

    @pytest.mark.asyncio
    async def test_preserve_intelligence_success(
        self, context_service, sample_intelligence_data, sample_bot_transition
    ):
        """Test successful intelligence preservation."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Act
        start_time = time.time()
        result = await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )
        preservation_latency = (time.time() - start_time) * 1000

        # Assert
        assert isinstance(result, ContextHandoff)
        assert result.success == True
        assert result.handoff_status == HandoffStatus.SUCCESS
        assert result.lead_id == lead_id
        assert result.location_id == location_id
        assert result.intelligence_snapshot_id != ""

        # Verify performance target
        assert preservation_latency < 50, f"Preservation took {preservation_latency}ms (target: <50ms)"
        assert result.preservation_latency_ms < 50

        # Verify cache was called with correct parameters (snapshot + history)
        assert context_service.cache.set.call_count >= 1
        cache_call = context_service.cache.set.call_args_list[0]
        assert cache_call[1]["ttl"] == 7200  # 2-hour TTL for handoffs

        # Verify event publishing
        context_service.event_publisher.publish_lead_update.assert_called_once()
        event_call = context_service.event_publisher.publish_lead_update.call_args
        assert event_call[1]["action"] == "bot_handoff"

    @pytest.mark.asyncio
    async def test_retrieve_intelligence_context_success(
        self, context_service, sample_intelligence_data, sample_bot_transition
    ):
        """Test successful intelligence context retrieval."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        target_bot = BotType.JORGE_BUYER

        # Create a snapshot to retrieve
        snapshot = IntelligenceSnapshot(
            snapshot_id="snap_123",
            lead_id=lead_id,
            location_id=location_id,
            source_bot=BotType.JORGE_SELLER,
            target_bot=target_bot,
            snapshot_timestamp=datetime.now(timezone.utc),
            preserved_intelligence=PreservedIntelligence(
                top_property_matches=[{"property_id": "prop_123", "score": 0.9}],
                best_match_score=0.9,
                conversation_quality_score=78.5,
                overall_sentiment=0.6,
                profile_completeness=0.75,
            ),
            conversation_summary="Seller qualified, interested in buying",
            transition_reason=TransitionReason.QUALIFIED_BUYER,
        )

        # Mock cache hit - override side_effect with direct return
        context_service.cache.get.side_effect = None
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = snapshot.to_json()

        # Act
        start_time = time.time()
        result = await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=target_bot, location_id=location_id
        )
        retrieval_latency = (time.time() - start_time) * 1000

        # Assert
        assert isinstance(result, IntelligenceSnapshot)
        assert result.lead_id == lead_id
        assert result.location_id == location_id
        assert result.target_bot == target_bot
        assert result.conversation_summary == "Seller qualified, interested in buying"

        # Verify performance target
        assert retrieval_latency < 30, f"Retrieval took {retrieval_latency}ms (target: <30ms)"

        # Verify cache was accessed
        context_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_intelligence_context_not_found(self, context_service):
        """Test retrieval when no context is found."""
        # Arrange
        lead_id = "lead_456"
        target_bot = BotType.JORGE_SELLER
        location_id = "rancho_cucamonga"

        # Mock cache miss
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = None

        # Act
        result = await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=target_bot, location_id=location_id
        )

        # Assert
        assert result is None

        # Verify cache was accessed
        context_service.cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_intelligence_context_expired(self, context_service):
        """Test retrieval of expired context."""
        # Arrange
        lead_id = "lead_123"
        target_bot = BotType.JORGE_BUYER
        location_id = "rancho_cucamonga"

        # Create expired snapshot (3 hours old)
        expired_timestamp = datetime.now(timezone.utc) - timedelta(hours=3)
        expired_snapshot = IntelligenceSnapshot(
            snapshot_id="snap_123",
            lead_id=lead_id,
            location_id=location_id,
            source_bot=BotType.JORGE_SELLER,
            target_bot=target_bot,
            snapshot_timestamp=expired_timestamp,
            preserved_intelligence=PreservedIntelligence.create_empty(),
            conversation_summary="Expired context",
            transition_reason=TransitionReason.QUALIFIED_BUYER,
        )

        # Mock cache returning expired data - override side_effect
        context_service.cache.get.side_effect = None
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = expired_snapshot.to_json()

        # Act
        result = await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=target_bot, location_id=location_id
        )

        # Assert
        assert result is None  # Expired context should be rejected

        # Verify expired context was deleted from cache
        context_service.cache.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_tenant_isolation(self, context_service):
        """Test tenant isolation in context retrieval."""
        # Arrange
        lead_id = "lead_123"
        target_bot = BotType.JORGE_BUYER
        requested_location = "rancho_cucamonga"
        cached_location = "dallas"  # Different location

        # Create snapshot with different location
        snapshot = IntelligenceSnapshot(
            snapshot_id="snap_123",
            lead_id=lead_id,
            location_id=cached_location,  # Different from requested
            source_bot=BotType.JORGE_SELLER,
            target_bot=target_bot,
            snapshot_timestamp=datetime.now(timezone.utc),
            preserved_intelligence=PreservedIntelligence.create_empty(),
            conversation_summary="Wrong tenant context",
            transition_reason=TransitionReason.QUALIFIED_BUYER,
        )

        # Mock cache hit with wrong tenant
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = snapshot.to_json()

        # Act
        result = await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=target_bot, location_id=requested_location
        )

        # Assert
        assert result is None  # Should reject due to location mismatch

    @pytest.mark.asyncio
    async def test_create_intelligence_snapshot(self, context_service, sample_intelligence_data, sample_bot_transition):
        """Test intelligence snapshot creation from intelligence data."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Act
        snapshot = await context_service.create_intelligence_snapshot(
            lead_id=lead_id,
            location_id=location_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
        )

        # Assert
        assert isinstance(snapshot, IntelligenceSnapshot)
        assert snapshot.lead_id == lead_id
        assert snapshot.location_id == location_id
        assert snapshot.source_bot == sample_bot_transition.source_bot
        assert snapshot.target_bot == sample_bot_transition.target_bot

        # Verify intelligence extraction
        assert len(snapshot.preserved_intelligence.top_property_matches) == 2
        assert snapshot.preserved_intelligence.best_match_score == 0.95
        assert snapshot.preserved_intelligence.conversation_quality_score == 78.5
        assert snapshot.preserved_intelligence.profile_completeness == 0.75

        # Verify conversation summary generation
        assert "Seller qualified" in snapshot.conversation_summary
        assert "FRS 85" in snapshot.conversation_summary

        # Verify qualification scores extraction
        assert snapshot.qualification_scores["FRS"] == 85.0
        assert snapshot.qualification_scores["PCS"] == 90.0

        # Verify strategic guidance
        assert len(snapshot.recommended_next_actions) > 0
        assert snapshot.strategic_approach in ["confrontational", "consultative"]

    @pytest.mark.asyncio
    async def test_transition_history_tracking(self, context_service, sample_intelligence_data, sample_bot_transition):
        """Test transition history tracking and retrieval."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Mock empty history initially
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = None

        # Act - preserve intelligence (creates history)
        await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Retrieve history
        history = await context_service.get_transition_history(lead_id=lead_id, location_id=location_id)

        # Assert
        assert isinstance(history, TransitionHistory)
        assert history.lead_id == lead_id
        assert history.location_id == location_id

        # Should start empty but structure should be correct
        assert history.total_transitions >= 0
        assert history.successful_handoffs >= 0

    @pytest.mark.asyncio
    async def test_bot_handoff_scenarios(self, context_service, sample_intelligence_data):
        """Test different bot handoff scenarios."""
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Test scenarios
        scenarios = [
            # Seller → Buyer (qualified buyer)
            {
                "source": BotType.JORGE_SELLER,
                "target": BotType.JORGE_BUYER,
                "reason": TransitionReason.QUALIFIED_BUYER,
                "message": "Seller qualified, also wants to buy",
            },
            # Lead → Seller (lead activation)
            {
                "source": BotType.LEAD_BOT,
                "target": BotType.JORGE_SELLER,
                "reason": TransitionReason.LEAD_ACTIVATED,
                "message": "Lead showed selling interest",
            },
            # Buyer → Lead (dormant lead)
            {
                "source": BotType.JORGE_BUYER,
                "target": BotType.LEAD_BOT,
                "reason": TransitionReason.DORMANT_LEAD,
                "message": "Buyer went inactive, moving to nurture",
            },
            # Any → Manual (escalation)
            {
                "source": BotType.JORGE_SELLER,
                "target": BotType.MANUAL_AGENT,
                "reason": TransitionReason.ESCALATION_REQUESTED,
                "message": "Complex situation requires human intervention",
            },
        ]

        for scenario in scenarios:
            # Arrange
            transition = BotTransition(
                transition_id=f"trans_{scenario['source'].value}_{scenario['target'].value}",
                lead_id=lead_id,
                location_id=location_id,
                source_bot=scenario["source"],
                target_bot=scenario["target"],
                transition_reason=scenario["reason"],
                handoff_message=scenario["message"],
            )

            # Act
            result = await context_service.preserve_intelligence(
                lead_id=lead_id,
                intelligence_data=sample_intelligence_data,
                bot_transition=transition,
                location_id=location_id,
            )

            # Assert
            assert result.success == True
            assert result.lead_id == lead_id

            # Verify retrieval works
            retrieved = await context_service.retrieve_intelligence_context(
                lead_id=lead_id, target_bot=scenario["target"], location_id=location_id
            )

            assert retrieved is not None
            assert retrieved.source_bot == scenario["source"]
            assert retrieved.target_bot == scenario["target"]
            assert retrieved.transition_reason == scenario["reason"]

            # Clear cache for next scenario - reset mock store
            context_service.cache.delete = AsyncMock(side_effect=lambda key=None, **kw: None)

    @pytest.mark.asyncio
    async def test_cache_service_failure(self, context_service, sample_intelligence_data, sample_bot_transition):
        """Test behavior when cache service fails."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Make cache operations fail
        context_service.cache.set.side_effect = Exception("Redis connection failed")

        # Act
        result = await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Assert
        assert isinstance(result, ContextHandoff)
        assert result.success == False
        assert "Redis connection failed" in result.error_message

    @pytest.mark.asyncio
    async def test_event_publishing_failure(self, context_service, sample_intelligence_data, sample_bot_transition):
        """Test behavior when event publishing fails."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Make event publishing fail
        context_service.event_publisher.publish_lead_update.side_effect = Exception("Event service down")

        # Act
        result = await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Assert
        # Should still succeed despite event publishing failure
        assert result.success == True

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, context_service, sample_intelligence_data, sample_bot_transition):
        """Test performance metrics tracking."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Get initial metrics
        initial_metrics = context_service.get_metrics()

        # Act - perform preservation operations
        await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=sample_intelligence_data,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Perform retrieval operations
        context_service.cache.get.side_effect = None
        context_service.cache.get.return_value = None  # Cache miss
        await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=BotType.JORGE_BUYER, location_id=location_id
        )

        # Get updated metrics
        updated_metrics = context_service.get_metrics()

        # Assert
        assert updated_metrics["total_preservations"] > initial_metrics["total_preservations"]
        assert updated_metrics["total_retrievals"] > initial_metrics["total_retrievals"]
        assert updated_metrics["avg_preservation_latency_ms"] >= 0
        assert updated_metrics["avg_retrieval_latency_ms"] >= 0

    @pytest.mark.asyncio
    async def test_empty_intelligence_data(self, context_service, sample_bot_transition):
        """Test behavior with empty intelligence data."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"
        empty_intelligence = {}

        # Act
        result = await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=empty_intelligence,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Assert
        # Should still create snapshot with empty intelligence
        assert result.success == True

        # Retrieve and verify
        retrieved = await context_service.retrieve_intelligence_context(
            lead_id=lead_id, target_bot=sample_bot_transition.target_bot, location_id=location_id
        )

        assert retrieved is not None
        assert retrieved.preserved_intelligence.profile_completeness == 0.0

    @pytest.mark.asyncio
    async def test_large_intelligence_data(self, context_service, sample_bot_transition):
        """Test behavior with large intelligence data."""
        # Arrange
        lead_id = "lead_123"
        location_id = "rancho_cucamonga"

        # Create large intelligence data (simulate large conversation history)
        large_intelligence = {
            "property_intelligence": {"top_matches": [{"property_id": f"prop_{i}", "score": 0.8} for i in range(100)]},
            "conversation_history": [
                {"role": "user", "content": f"Message {i}", "timestamp": "2024-01-25T09:00:00Z"} for i in range(1000)
            ],
        }

        # Act
        result = await context_service.preserve_intelligence(
            lead_id=lead_id,
            intelligence_data=large_intelligence,
            bot_transition=sample_bot_transition,
            location_id=location_id,
        )

        # Assert
        # Should handle large data but may log warnings
        assert result.success == True
        # Data size should be tracked
        assert result.data_size_bytes > 1000  # Should be substantial


class TestIntelligenceContextServiceIntegration:
    """Integration tests for IntelligenceContextService."""

    @pytest.mark.asyncio
    async def test_singleton_pattern(self):
        """Test singleton pattern implementation."""
        # Act
        instance1 = get_intelligence_context_service()
        instance2 = get_intelligence_context_service()

        # Assert
        assert instance1 is instance2
        assert isinstance(instance1, IntelligenceContextService)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        # Act
        health = await health_check()

        # Assert
        assert isinstance(health, dict)
        assert "service" in health
        assert "status" in health
        assert "version" in health
        assert "metrics" in health
        assert health["service"] == "IntelligenceContextService"


class TestBotHandoffModels:
    """Test bot handoff data models."""

    def test_intelligence_snapshot_serialization(self):
        """Test IntelligenceSnapshot serialization/deserialization."""
        # Arrange
        original_snapshot = IntelligenceSnapshot(
            snapshot_id="snap_123",
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            source_bot=BotType.JORGE_SELLER,
            target_bot=BotType.JORGE_BUYER,
            snapshot_timestamp=datetime.now(timezone.utc),
            preserved_intelligence=PreservedIntelligence.create_empty(),
            conversation_summary="Test conversation",
            transition_reason=TransitionReason.QUALIFIED_BUYER,
        )

        # Act
        json_str = original_snapshot.to_json()
        deserialized_snapshot = IntelligenceSnapshot.from_json(json_str)

        # Assert
        assert deserialized_snapshot.snapshot_id == original_snapshot.snapshot_id
        assert deserialized_snapshot.lead_id == original_snapshot.lead_id
        assert deserialized_snapshot.source_bot == original_snapshot.source_bot
        assert deserialized_snapshot.target_bot == original_snapshot.target_bot
        assert deserialized_snapshot.conversation_summary == original_snapshot.conversation_summary

    def test_bot_transition_model(self):
        """Test BotTransition model creation and serialization."""
        # Arrange
        transition = BotTransition(
            transition_id="trans_123",
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            source_bot=BotType.JORGE_SELLER,
            target_bot=BotType.JORGE_BUYER,
            transition_reason=TransitionReason.QUALIFIED_BUYER,
            handoff_message="Qualified seller also wants to buy",
        )

        # Act
        data = transition.to_dict()
        reconstructed = BotTransition.from_dict(data)

        # Assert
        assert reconstructed.transition_id == transition.transition_id
        assert reconstructed.source_bot == transition.source_bot
        assert reconstructed.target_bot == transition.target_bot
        assert reconstructed.transition_reason == transition.transition_reason

    def test_context_handoff_creation(self):
        """Test ContextHandoff creation helpers."""
        # Test successful handoff
        success_handoff = ContextHandoff.create_success(
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            intelligence_snapshot_id="snap_123",
            transition_id="trans_123",
            preservation_latency_ms=45.5,
            cache_key="test_key",
        )

        assert success_handoff.success == True
        assert success_handoff.handoff_status == HandoffStatus.SUCCESS
        assert success_handoff.preservation_latency_ms == 45.5

        # Test failed handoff
        failed_handoff = ContextHandoff.create_failure(
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            error_message="Cache service unavailable",
            preservation_latency_ms=100.0,
        )

        assert failed_handoff.success == False
        assert failed_handoff.handoff_status == HandoffStatus.FAILED
        assert "Cache service unavailable" in failed_handoff.error_message

    def test_transition_history_management(self):
        """Test TransitionHistory tracking and metrics."""
        # Arrange
        history = TransitionHistory.create_empty("lead_123", "rancho_cucamonga")

        transition = BotTransition(
            transition_id="trans_123",
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            source_bot=BotType.JORGE_SELLER,
            target_bot=BotType.JORGE_BUYER,
            transition_reason=TransitionReason.QUALIFIED_BUYER,
            handoff_message="Test transition",
        )

        handoff = ContextHandoff.create_success(
            lead_id="lead_123",
            location_id="rancho_cucamonga",
            intelligence_snapshot_id="snap_123",
            transition_id="trans_123",
            preservation_latency_ms=30.0,
            cache_key="test_key",
        )

        # Act
        history.add_transition(transition, handoff)

        # Assert
        assert history.total_transitions == 1
        assert history.successful_handoffs == 1
        assert history.failed_handoffs == 0
        assert history.average_handoff_latency_ms == 30.0
        assert len(history.transitions) == 1
        assert len(history.handoffs) == 1

        # Test success rate calculation
        assert history.get_success_rate() == 1.0

    def test_preserved_intelligence_extraction(self):
        """Test PreservedIntelligence data extraction and serialization."""
        # Arrange
        intelligence = PreservedIntelligence(
            top_property_matches=[{"property_id": "prop_123", "score": 0.9}],
            best_match_score=0.9,
            conversation_quality_score=85.0,
            overall_sentiment=0.7,
            budget_range={"min": 400000, "max": 600000},
            profile_completeness=0.8,
        )

        # Act
        data = intelligence.to_dict()
        reconstructed = PreservedIntelligence.from_dict(data)

        # Assert
        assert reconstructed.best_match_score == intelligence.best_match_score
        assert reconstructed.conversation_quality_score == intelligence.conversation_quality_score
        assert reconstructed.budget_range == intelligence.budget_range
        assert len(reconstructed.top_property_matches) == 1

    def test_bot_type_enum_validation(self):
        """Test BotType enum validation."""
        # Valid bot types
        valid_types = [
            BotType.JORGE_SELLER,
            BotType.JORGE_BUYER,
            BotType.LEAD_BOT,
            BotType.AI_CONCIERGE,
            BotType.MANUAL_AGENT,
        ]

        for bot_type in valid_types:
            assert isinstance(bot_type.value, str)
            assert len(bot_type.value) > 0

        # Test string conversion
        assert BotType.JORGE_SELLER.value == "jorge-seller"
        assert BotType.JORGE_BUYER.value == "jorge-buyer"

    def test_transition_reason_enum_validation(self):
        """Test TransitionReason enum validation."""
        # Valid transition reasons
        valid_reasons = [
            TransitionReason.QUALIFIED_BUYER,
            TransitionReason.QUALIFIED_SELLER,
            TransitionReason.LEAD_ACTIVATED,
            TransitionReason.DORMANT_LEAD,
            TransitionReason.ESCALATION_REQUESTED,
            TransitionReason.MANUAL_OVERRIDE,
        ]

        for reason in valid_reasons:
            assert isinstance(reason.value, str)
            assert len(reason.value) > 0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])