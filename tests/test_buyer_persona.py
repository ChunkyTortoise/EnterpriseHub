"""
Tests for Buyer Persona Classification (Phase 1.4)

Tests the BuyerPersonaService for classifying buyers into persona types
and providing personalized communication recommendations.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.models.buyer_persona import (
    BuyerPersonaClassification,
    BuyerPersonaInsights,
    BuyerPersonaType,
)
from ghl_real_estate_ai.services.buyer_persona_service import BuyerPersonaService


@pytest.fixture
def persona_service():
    """Create a BuyerPersonaService instance for testing."""
    return BuyerPersonaService()


class TestBuyerPersonaClassification:
    """Test buyer persona classification functionality."""

    @pytest.mark.asyncio
    async def test_first_time_buyer_detection(self, persona_service):
        """Test detection of first-time buyer persona."""
        conversation = [
            {"role": "user", "content": "I'm looking to buy my first home, never done this before"},
            {"role": "assistant", "content": "Congratulations! Here's how buying works..."},
            {"role": "user", "content": "What do I need to know about down payments?"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.FIRST_TIME
        assert result.confidence >= 0.6
        assert "first home" in result.detected_signals or "never owned" in result.detected_signals

    @pytest.mark.asyncio
    async def test_upsizer_detection(self, persona_service):
        """Test detection of upsizer persona."""
        conversation = [
            {"role": "user", "content": "We need more space for our growing family"},
            {"role": "assistant", "content": "I can help with that..."},
            {"role": "user", "content": "We've outgrown our current place and need an additional bedroom"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.UPSIZER
        assert result.confidence >= 0.6
        assert any(
            signal in result.detected_signals
            for signal in ["more space", "growing family", "outgrown", "additional bedroom"]
        )

    @pytest.mark.asyncio
    async def test_downsizer_detection(self, persona_service):
        """Test detection of downsizer persona."""
        conversation = [
            {"role": "user", "content": "Our house is too much space now that the kids are gone"},
            {"role": "assistant", "content": "I understand..."},
            {"role": "user", "content": "We want to downsize and have less maintenance to worry about"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.DOWNSIZER
        assert result.confidence >= 0.6
        assert any(
            signal in result.detected_signals for signal in ["too much space", "downsize", "maintenance", "empty nest"]
        )

    @pytest.mark.asyncio
    async def test_investor_detection(self, persona_service):
        """Test detection of investor persona."""
        conversation = [
            {"role": "user", "content": "I'm looking for rental properties with good cash flow"},
            {"role": "assistant", "content": "Great, let's find some investment properties..."},
            {"role": "user", "content": "What's the ROI on multi-family properties in this area?"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.INVESTOR
        assert result.confidence >= 0.6
        assert any(
            signal in result.detected_signals
            for signal in ["rental", "rental income", "roi", "cash flow", "investment"]
        )

    @pytest.mark.asyncio
    async def test_relocator_detection(self, persona_service):
        """Test detection of relocator persona."""
        conversation = [
            {"role": "user", "content": "I'm relocating to the area for a new job"},
            {"role": "assistant", "content": "Welcome to the area!"},
            {"role": "user", "content": "I'm moving from a different city and need to find a place quickly"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.RELOCATOR
        assert result.confidence >= 0.6
        assert any(
            signal in result.detected_signals for signal in ["relocating", "new job", "moving to", "different city"]
        )

    @pytest.mark.asyncio
    async def test_luxury_buyer_detection(self, persona_service):
        """Test detection of luxury buyer persona."""
        conversation = [
            {"role": "user", "content": "I'm looking for high-end properties with premium amenities"},
            {"role": "assistant", "content": "I can show you some luxury options..."},
            {"role": "user", "content": "I need a custom home with a great view and executive features"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.LUXURY
        assert result.confidence >= 0.6
        assert any(
            signal in result.detected_signals
            for signal in ["high-end", "premium", "amenities", "view", "custom", "executive"]
        )

    @pytest.mark.asyncio
    async def test_unknown_persona_no_signals(self, persona_service):
        """Test classification when no clear signals are present."""
        conversation = [
            {"role": "user", "content": "I'm looking for a house"},
            {"role": "assistant", "content": "What kind of house?"},
            {"role": "user", "content": "Something nice"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.UNKNOWN
        assert result.confidence <= 0.5

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, persona_service):
        """Test confidence scoring based on signal strength."""
        # Strong signals should yield higher confidence
        strong_conversation = [
            {
                "role": "user",
                "content": "I'm a first-time buyer looking for my first home. Never owned before and excited but nervous about how buying works.",
            },
        ]

        weak_conversation = [
            {"role": "user", "content": "I might buy a home someday"},
        ]

        strong_result = await persona_service.classify_buyer_type(strong_conversation)
        weak_result = await persona_service.classify_buyer_type(weak_conversation)

        assert strong_result.confidence > weak_result.confidence

    @pytest.mark.asyncio
    async def test_behavioral_signals_analysis(self, persona_service):
        """Test behavioral signal analysis."""
        conversation = [
            {"role": "user", "content": "What's the process? How does it work? What do I need?"},
            {"role": "assistant", "content": "Here's how it works..."},
            {"role": "user", "content": "What about down payments? And closing costs?"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        # Should have behavioral signals
        assert "question_pattern" in result.behavioral_signals
        assert "response_length" in result.behavioral_signals
        assert "timeline_urgency" in result.behavioral_signals
        assert "budget_openness" in result.behavioral_signals
        assert "feature_priority" in result.behavioral_signals

        # Question pattern should be high (lots of questions)
        assert result.behavioral_signals["question_pattern"] >= 0.5

    @pytest.mark.asyncio
    async def test_primary_and_secondary_indicators(self, persona_service):
        """Test classification of primary and secondary indicators."""
        conversation = [
            {"role": "user", "content": "I'm looking for rental properties with good ROI and cash flow"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        # Should have primary indicators (direct keyword matches)
        assert len(result.primary_indicators) > 0

        # Should have secondary indicators (behavioral signals)
        assert len(result.secondary_indicators) >= 0


class TestBuyerPersonaInsights:
    """Test buyer persona insights and recommendations."""

    @pytest.mark.asyncio
    async def test_first_time_buyer_insights(self, persona_service):
        """Test insights for first-time buyer persona."""
        insights = await persona_service.get_persona_insights(BuyerPersonaType.FIRST_TIME)

        assert isinstance(insights, BuyerPersonaInsights)
        assert "encouraging" in insights.tone.lower()
        assert "educational" in insights.content_focus.lower()
        assert insights.urgency_level == "Moderate"
        assert len(insights.key_messages) > 0
        assert len(insights.recommended_questions) > 0

    @pytest.mark.asyncio
    async def test_investor_insights(self, persona_service):
        """Test insights for investor persona."""
        insights = await persona_service.get_persona_insights(BuyerPersonaType.INVESTOR)

        assert isinstance(insights, BuyerPersonaInsights)
        assert "professional" in insights.tone.lower() or "data-driven" in insights.tone.lower()
        assert "roi" in insights.content_focus.lower() or "cash flow" in insights.content_focus.lower()
        assert len(insights.key_messages) > 0
        assert len(insights.recommended_questions) > 0

    @pytest.mark.asyncio
    async def test_luxury_buyer_insights(self, persona_service):
        """Test insights for luxury buyer persona."""
        insights = await persona_service.get_persona_insights(BuyerPersonaType.LUXURY)

        assert isinstance(insights, BuyerPersonaInsights)
        assert "sophisticated" in insights.tone.lower() or "exclusive" in insights.tone.lower()
        assert "amenities" in insights.content_focus.lower() or "lifestyle" in insights.content_focus.lower()
        assert insights.urgency_level == "Low"
        assert len(insights.key_messages) > 0

    @pytest.mark.asyncio
    async def test_all_persona_types_have_insights(self, persona_service):
        """Test that all persona types have insights defined."""
        for persona_type in BuyerPersonaType:
            if persona_type == BuyerPersonaType.UNKNOWN:
                continue

            insights = await persona_service.get_persona_insights(persona_type)

            assert isinstance(insights, BuyerPersonaInsights)
            assert insights.tone
            assert insights.content_focus
            assert insights.urgency_level
            assert len(insights.key_messages) > 0
            assert len(insights.recommended_questions) > 0


class TestBuyerPersonaUpdate:
    """Test buyer persona update functionality."""

    @pytest.mark.asyncio
    async def test_update_persona_with_new_conversation(self, persona_service):
        """Test updating persona with new conversation data."""
        initial_conversation = [
            {"role": "user", "content": "I'm looking for a house"},
        ]

        updated_conversation = [
            {"role": "user", "content": "I'm looking for a house"},
            {"role": "assistant", "content": "What kind?"},
            {"role": "user", "content": "I'm a first-time buyer looking for my first home"},
        ]

        # Get initial classification
        initial_result = await persona_service.classify_buyer_type(initial_conversation)

        # Update with new conversation
        updated_result = await persona_service.update_persona(
            lead_id="test-lead-123",
            new_conversation=updated_conversation,
        )

        # Updated result should have higher confidence for first-time buyer
        assert updated_result.persona_type == BuyerPersonaType.FIRST_TIME
        assert updated_result.confidence >= initial_result.confidence

    @pytest.mark.asyncio
    async def test_persona_change_detection(self, persona_service):
        """Test detection of persona change as conversation progresses."""
        initial_conversation = [
            {"role": "user", "content": "I'm looking for a house to live in"},
        ]

        updated_conversation = [
            {"role": "user", "content": "I'm looking for a house to live in"},
            {"role": "assistant", "content": "What kind?"},
            {"role": "user", "content": "Actually, I want rental properties for investment income"},
        ]

        # Get initial classification
        initial_result = await persona_service.classify_buyer_type(initial_conversation)

        # Update with new conversation
        updated_result = await persona_service.update_persona(
            lead_id="test-lead-456",
            new_conversation=updated_conversation,
        )

        # Persona should change to investor
        assert updated_result.persona_type == BuyerPersonaType.INVESTOR
        # Initial should be unknown or different
        assert initial_result.persona_type != BuyerPersonaType.INVESTOR


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_conversation(self, persona_service):
        """Test classification with empty conversation history."""
        result = await persona_service.classify_buyer_type([])

        assert result.persona_type == BuyerPersonaType.UNKNOWN
        assert result.confidence == 0.5  # Default confidence for unknown

    @pytest.mark.asyncio
    async def test_conversation_with_only_assistant_messages(self, persona_service):
        """Test classification with only assistant messages."""
        conversation = [
            {"role": "assistant", "content": "Hello! How can I help you?"},
            {"role": "assistant", "content": "I'm here to assist you."},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        assert result.persona_type == BuyerPersonaType.UNKNOWN

    @pytest.mark.asyncio
    async def test_mixed_persona_signals(self, persona_service):
        """Test classification when multiple persona signals are present."""
        conversation = [
            {"role": "user", "content": "I'm a first-time buyer looking for rental properties"},
        ]

        result = await persona_service.classify_buyer_type(conversation)

        # Should classify based on strongest signal
        assert result.persona_type in [BuyerPersonaType.FIRST_TIME, BuyerPersonaType.INVESTOR]
        assert result.confidence >= 0.3

    @pytest.mark.asyncio
    async def test_case_insensitive_keyword_matching(self, persona_service):
        """Test that keyword matching is case-insensitive."""
        conversation_lower = [
            {"role": "user", "content": "i'm looking for rental properties"},
        ]

        conversation_upper = [
            {"role": "user", "content": "I'M LOOKING FOR RENTAL PROPERTIES"},
        ]

        result_lower = await persona_service.classify_buyer_type(conversation_lower)
        result_upper = await persona_service.classify_buyer_type(conversation_upper)

        # Both should detect investor persona
        assert result_lower.persona_type == BuyerPersonaType.INVESTOR
        assert result_upper.persona_type == BuyerPersonaType.INVESTOR


class TestBuyerPersonaLlmJsonRegression:
    """Regression tests for JSON parsing and serialization in LLM persona path."""

    @pytest.mark.asyncio
    async def test_llm_persona_json_round_trip(self):
        """Regression: LLM JSON prompt/parse path should classify persona without NameError."""
        llm_client = MagicMock()
        llm_client.agenerate = AsyncMock(
            return_value=SimpleNamespace(
                content=(
                    "```json\n"
                    '{"persona":"investor","confidence":0.86,'
                    '"signals":["rental","roi"],'
                    '"behavioral_insights":{"urgency":0.4,"data_focus":0.9,"emotional_engagement":0.2},'
                    '"reasoning":"User repeatedly focuses on ROI and rental yield."}'
                    "\n```"
                )
            )
        )

        service = BuyerPersonaService(llm_client=llm_client)
        result = await service._classify_persona_llm(
            conversation_history=[{"role": "user", "content": "I'm focused on rental ROI."}],
            lead_data={"budget": 700000},
        )

        assert result is not None
        assert result.persona_type == BuyerPersonaType.INVESTOR
        assert result.confidence == 0.86
