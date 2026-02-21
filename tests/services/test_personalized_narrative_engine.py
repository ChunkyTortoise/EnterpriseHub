import pytest

pytestmark = pytest.mark.integration

"""
Unit tests for PersonalizedNarrativeEngine.

Tests narrative generation, caching, fallbacks, and performance optimization.
Follows project TDD patterns with comprehensive coverage.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse
from ghl_real_estate_ai.models.matching_models import (
    CommuteScore,
    LifestyleScores,
    SafetyScore,
    SchoolScore,
    WalkabilityScore,
)
from ghl_real_estate_ai.services.personalized_narrative_engine import (
    NarrativeComponent,
    NarrativeLength,
    NarrativeStyle,
    PersonalizedNarrative,
    PersonalizedNarrativeEngine,
    get_narrative_engine,
)


class TestPersonalizedNarrativeEngine:
    """Test suite for PersonalizedNarrativeEngine."""

    @pytest.fixture
    def sample_property_data(self) -> Dict[str, Any]:
        """Sample property data for testing."""
        return {
            "id": "prop_123",
            "address": "123 Hill Country Dr, Rancho Cucamonga, CA",
            "price": 485000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 2100,
            "neighborhood": "Westlake Hills",
            "features": ["pool", "deck", "garage"],
            "lot_size": 0.25,
        }

    @pytest.fixture
    def sample_lead_data(self) -> Dict[str, Any]:
        """Sample lead data for testing."""
        return {
            "lead_id": "lead_456",
            "lead_name": "Sarah Chen",
            "family_status": "family_with_kids",
            "workplace": "Apple",
            "budget_max": 500000,
            "lifestyle_priorities": ["schools", "commute", "safety"],
            "location_id": "loc_789",
        }

    @pytest.fixture
    def sample_lifestyle_scores(self) -> LifestyleScores:
        """Sample lifestyle scores for testing."""
        return LifestyleScores(
            schools=SchoolScore(
                elementary_rating=9.0,
                middle_rating=8.5,
                high_rating=9.2,
                average_rating=8.9,
                distance_penalty=0.1,
                overall_score=8.8,
                top_school_name="Westlake Elementary",
                reasoning="Excellent school district with top ratings",
            ),
            commute=CommuteScore(
                to_downtown_minutes=25,
                to_workplace_minutes=15,
                public_transit_access=0.7,
                highway_access=0.9,
                overall_score=8.5,
                reasoning="Quick access to major employers",
            ),
            walkability=WalkabilityScore(
                walk_score=65,
                nearby_amenities_count=12,
                grocery_distance_miles=0.8,
                restaurant_density=0.7,
                park_access=0.9,
                overall_score=7.5,
                reasoning="Good walkability with parks nearby",
            ),
            safety=SafetyScore(
                crime_rate_per_1000=2.1,
                neighborhood_safety_rating=9.0,
                police_response_time=4,
                overall_score=9.0,
                reasoning="Very safe neighborhood",
            ),
            amenities_proximity=8.0,
            overall_score=8.4,
        )

    @pytest.fixture
    def mock_llm_response(self) -> LLMResponse:
        """Mock Claude response for testing."""
        return LLMResponse(
            content="This isn't just a house - it's where your Rancho Cucamonga story begins. Wake up to Hill Country views from the master bedroom, walk your golden retriever down tree-lined streets where neighbors wave hello. Your kids bike safely to top-rated Westlake Elementary 4 blocks away. The outdoor kitchen becomes your weekend gathering spot while friends relax around the pool. Our AI predicts 15% appreciation as downtown Rancho Cucamonga expands westward. At $485,000, this represents exceptional value in one of Rancho Cucamonga's most coveted communities. Schedule your tour today and experience what could be your family's forever home.",
            provider=LLMProvider.CLAUDE,
            model="claude-3-5-sonnet",
            input_tokens=450,
            output_tokens=120,
            finish_reason="stop",
        )

    @pytest.fixture
    def engine(self) -> PersonalizedNarrativeEngine:
        """PersonalizedNarrativeEngine instance for testing."""
        with patch("ghl_real_estate_ai.services.personalized_narrative_engine.get_cache_service") as mock_cache_service:
            mock_cache_service.return_value = AsyncMock()
            return PersonalizedNarrativeEngine(enable_caching=True)

    @pytest.mark.asyncio
    async def test_generate_personalized_narrative_success(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
        sample_lifestyle_scores: LifestyleScores,
        mock_llm_response: LLMResponse,
    ):
        """Test successful narrative generation."""
        # Mock Claude client
        with patch.object(engine.llm_client, "agenerate", return_value=mock_llm_response):
            # Mock cache miss
            engine.cache_service.get = AsyncMock(return_value=None)
            engine.cache_service.set = AsyncMock(return_value=True)

            # Mock analytics
            engine.analytics.track_event = AsyncMock()
            engine.analytics.track_llm_usage = AsyncMock()

            narrative = await engine.generate_personalized_narrative(
                property_data=sample_property_data,
                lead_data=sample_lead_data,
                lifestyle_scores=sample_lifestyle_scores,
                style=NarrativeStyle.EMOTIONAL,
                length=NarrativeLength.MEDIUM,
            )

            # Verify narrative structure
            assert narrative.property_id == "prop_123"
            assert narrative.lead_id == "lead_456"
            assert narrative.style == NarrativeStyle.EMOTIONAL
            assert narrative.length == NarrativeLength.MEDIUM
            assert len(narrative.narrative_text) > 200
            assert "Hill Country views" in narrative.narrative_text
            assert not narrative.cached
            assert not narrative.fallback_used
            assert "claude" in narrative.model_used

            # Verify analytics tracking
            engine.analytics.track_event.assert_called_once()
            engine.analytics.track_llm_usage.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_narrative_with_cache_hit(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ):
        """Test narrative retrieval from cache."""
        # Create cached narrative
        cached_narrative = PersonalizedNarrative(
            property_id="prop_123",
            lead_id="lead_456",
            narrative_text="Cached narrative content",
            style=NarrativeStyle.EMOTIONAL,
            length=NarrativeLength.MEDIUM,
            cached=True,
        )

        # Mock cache hit
        engine.cache_service.get = AsyncMock(return_value=cached_narrative)

        narrative = await engine.generate_personalized_narrative(
            property_data=sample_property_data, lead_data=sample_lead_data
        )

        assert narrative.cached
        assert narrative.narrative_text == "Cached narrative content"
        assert engine._cache_hits == 1

    @pytest.mark.asyncio
    async def test_generate_narrative_fallback_on_claude_error(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ):
        """Test fallback narrative when Claude fails."""
        # Mock Claude failure
        with patch.object(engine.llm_client, "agenerate", side_effect=Exception("Claude API error")):
            # Mock cache miss
            engine.cache_service.get = AsyncMock(return_value=None)

            narrative = await engine.generate_personalized_narrative(
                property_data=sample_property_data, lead_data=sample_lead_data, style=NarrativeStyle.PROFESSIONAL
            )

            assert narrative.fallback_used
            assert narrative.model_used == "template"
            assert "Westlake Hills" in narrative.narrative_text
            assert "$485,000" in narrative.narrative_text
            assert engine._fallback_count == 1

    @pytest.mark.asyncio
    async def test_generate_batch_narratives(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
        mock_llm_response: LLMResponse,
    ):
        """Test batch narrative generation."""
        # Create multiple property-lead pairs
        property_lead_pairs = [
            (sample_property_data, sample_lead_data),
            ({**sample_property_data, "id": "prop_124"}, {**sample_lead_data, "lead_id": "lead_457"}),
            ({**sample_property_data, "id": "prop_125"}, {**sample_lead_data, "lead_id": "lead_458"}),
        ]

        # Mock Claude responses
        with patch.object(engine.llm_client, "agenerate", return_value=mock_llm_response):
            # Mock cache misses
            engine.cache_service.get = AsyncMock(return_value=None)
            engine.cache_service.set = AsyncMock(return_value=True)
            engine.analytics.track_event = AsyncMock()
            engine.analytics.track_llm_usage = AsyncMock()

            narratives = await engine.generate_batch_narratives(
                property_lead_pairs, style=NarrativeStyle.LIFESTYLE, length=NarrativeLength.SHORT, max_concurrent=2
            )

            assert len(narratives) == 3
            assert all(isinstance(n, PersonalizedNarrative) for n in narratives)
            assert narratives[0].property_id == "prop_123"
            assert narratives[1].property_id == "prop_124"
            assert narratives[2].property_id == "prop_125"

    @pytest.mark.asyncio
    async def test_different_narrative_styles(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ):
        """Test different narrative styles generate appropriate content."""
        # Mock cache misses and analytics
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.analytics.track_event = AsyncMock()

        styles_to_test = [
            NarrativeStyle.EMOTIONAL,
            NarrativeStyle.PROFESSIONAL,
            NarrativeStyle.INVESTMENT,
            NarrativeStyle.LUXURY,
        ]

        for style in styles_to_test:
            narrative = await engine.generate_personalized_narrative(
                property_data=sample_property_data,
                lead_data=sample_lead_data,
                style=style,
                length=NarrativeLength.MEDIUM,
            )

            assert narrative.style == style
            assert len(narrative.narrative_text) > 100

            # Verify style-appropriate content
            if style == NarrativeStyle.INVESTMENT:
                assert any(
                    word in narrative.narrative_text.lower()
                    for word in ["investment", "return", "appreciate", "portfolio"]
                )
            elif style == NarrativeStyle.LUXURY:
                assert any(
                    word in narrative.narrative_text.lower()
                    for word in ["luxury", "premium", "sophisticated", "exceptional"]
                )

    @pytest.mark.asyncio
    async def test_different_narrative_lengths(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
    ):
        """Test different narrative lengths produce appropriate content."""
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.analytics.track_event = AsyncMock()

        lengths = [NarrativeLength.SHORT, NarrativeLength.MEDIUM, NarrativeLength.LONG]

        for length in lengths:
            narrative = await engine.generate_personalized_narrative(
                property_data=sample_property_data, lead_data=sample_lead_data, length=length
            )

            assert narrative.length == length

            # Verify appropriate length ranges (using fallback templates)
            if length == NarrativeLength.SHORT:
                assert 20 <= len(narrative.narrative_text.split()) <= 200
            elif length == NarrativeLength.MEDIUM:
                assert 40 <= len(narrative.narrative_text.split()) <= 400
            else:  # LONG
                assert 60 <= len(narrative.narrative_text.split()) <= 700

    @pytest.mark.asyncio
    async def test_cache_key_generation(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
        sample_lifestyle_scores: LifestyleScores,
    ):
        """Test cache key generation includes all relevant parameters."""
        key1 = engine._build_cache_key(
            sample_property_data,
            sample_lead_data,
            sample_lifestyle_scores,
            NarrativeStyle.EMOTIONAL,
            NarrativeLength.MEDIUM,
        )

        key2 = engine._build_cache_key(
            sample_property_data,
            sample_lead_data,
            sample_lifestyle_scores,
            NarrativeStyle.PROFESSIONAL,  # Different style
            NarrativeLength.MEDIUM,
        )

        # Keys should be different for different styles
        assert key1 != key2
        assert "prop_123" in key1
        assert "lead_456" in key1
        assert "emotional" in key1
        assert "professional" in key2

    @pytest.mark.asyncio
    async def test_performance_metrics(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
        mock_llm_response: LLMResponse,
    ):
        """Test performance metrics tracking."""
        # Mock various scenarios
        engine.cache_service.get = AsyncMock(return_value=None)
        engine.cache_service.set = AsyncMock(return_value=True)
        engine.analytics.track_event = AsyncMock()
        engine.analytics.track_llm_usage = AsyncMock()

        # Successful generation
        with patch.object(engine.llm_client, "agenerate", return_value=mock_llm_response):
            await engine.generate_personalized_narrative(sample_property_data, sample_lead_data)

        # Cache hit
        cached_narrative = PersonalizedNarrative(
            property_id="prop_123",
            lead_id="lead_456",
            narrative_text="Cached content",
            style=NarrativeStyle.EMOTIONAL,
            length=NarrativeLength.MEDIUM,
            cached=True,
        )
        engine.cache_service.get = AsyncMock(return_value=cached_narrative)
        await engine.generate_personalized_narrative(sample_property_data, sample_lead_data)

        # Fallback
        with patch.object(engine.llm_client, "agenerate", side_effect=Exception("API error")):
            engine.cache_service.get = AsyncMock(return_value=None)
            await engine.generate_personalized_narrative(sample_property_data, sample_lead_data)

        metrics = engine.get_performance_metrics()

        assert metrics["total_generations"] == 2  # 2 new generations
        assert metrics["cache_hits"] == 1
        assert metrics["fallback_count"] == 1
        assert metrics["cache_hit_rate_percent"] > 0
        assert metrics["fallback_rate_percent"] > 0

    @pytest.mark.asyncio
    async def test_narrative_with_conversation_history(
        self,
        engine: PersonalizedNarrativeEngine,
        sample_property_data: Dict[str, Any],
        sample_lead_data: Dict[str, Any],
        mock_llm_response: LLMResponse,
    ):
        """Test narrative generation with conversation history."""
        conversation_history = [
            {"role": "user", "content": "Looking for family-friendly areas with good schools"},
            {"role": "assistant", "content": "I have some great options in Westlake Hills"},
            {"role": "user", "content": "What about commute times to Apple campus?"},
        ]

        with patch.object(engine.llm_client, "agenerate", return_value=mock_llm_response) as mock_generate:
            engine.cache_service.get = AsyncMock(return_value=None)
            engine.cache_service.set = AsyncMock(return_value=True)
            engine.analytics.track_event = AsyncMock()
            engine.analytics.track_llm_usage = AsyncMock()

            narrative = await engine.generate_personalized_narrative(
                property_data=sample_property_data,
                lead_data=sample_lead_data,
                conversation_history=conversation_history,
            )

            # Verify conversation history was included in prompt
            call_args = mock_generate.call_args
            prompt = call_args[1]["prompt"]
            assert "CONVERSATION CONTEXT" in prompt
            assert "good schools" in prompt

    def test_factory_function(self):
        """Test factory function returns engine instance."""
        with patch("ghl_real_estate_ai.services.personalized_narrative_engine.get_cache_service"):
            engine = get_narrative_engine()
            assert isinstance(engine, PersonalizedNarrativeEngine)

    @pytest.mark.asyncio
    async def test_error_handling_with_invalid_data(self, engine: PersonalizedNarrativeEngine):
        """Test error handling with invalid or missing data."""
        invalid_property = {"id": "test"}  # Missing required fields
        invalid_lead = {"lead_id": "test"}  # Missing required fields

        engine.cache_service.get = AsyncMock(return_value=None)
        engine.analytics.track_event = AsyncMock()

        # Should still generate narrative using fallback
        narrative = await engine.generate_personalized_narrative(property_data=invalid_property, lead_data=invalid_lead)

        assert narrative is not None
        assert narrative.fallback_used
        assert len(narrative.narrative_text) > 0


class TestNarrativeDataModels:
    """Test narrative data models."""

    def test_personalized_narrative_creation(self):
        """Test PersonalizedNarrative model creation."""
        narrative = PersonalizedNarrative(
            property_id="prop_123",
            lead_id="lead_456",
            narrative_text="Sample narrative",
            style=NarrativeStyle.EMOTIONAL,
            length=NarrativeLength.MEDIUM,
        )

        assert narrative.property_id == "prop_123"
        assert narrative.lead_id == "lead_456"
        assert narrative.style == NarrativeStyle.EMOTIONAL
        assert narrative.length == NarrativeLength.MEDIUM
        assert isinstance(narrative.generated_at, datetime)
        assert not narrative.cached
        assert not narrative.fallback_used

    def test_narrative_component_creation(self):
        """Test NarrativeComponent model creation."""
        component = NarrativeComponent(
            element_type="schools",
            score=0.85,
            description="Excellent school district",
            emotional_hooks=["top-rated", "award-winning"],
            data_points={"elementary_rating": 9.0, "distance": 0.5},
        )

        assert component.element_type == "schools"
        assert component.score == 0.85
        assert len(component.emotional_hooks) == 2
        assert component.data_points["elementary_rating"] == 9.0

    def test_narrative_styles_enum(self):
        """Test NarrativeStyle enum values."""
        assert NarrativeStyle.EMOTIONAL.value == "emotional"
        assert NarrativeStyle.PROFESSIONAL.value == "professional"
        assert NarrativeStyle.INVESTMENT.value == "investment"
        assert NarrativeStyle.LUXURY.value == "luxury"
        assert NarrativeStyle.LIFESTYLE.value == "lifestyle"

    def test_narrative_lengths_enum(self):
        """Test NarrativeLength enum values."""
        assert NarrativeLength.SHORT.value == "short"
        assert NarrativeLength.MEDIUM.value == "medium"
        assert NarrativeLength.LONG.value == "long"
