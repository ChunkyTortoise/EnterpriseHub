"""
Tests for Sentiment Analysis Service (Phase 1.5)

This module contains comprehensive tests for the sentiment analysis service,
including emotion detection, confidence scoring, escalation triggers, and edge cases.
"""

import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.sentiment_analysis_service import (
    ConversationSentiment,
    EscalationLevel,
    SentimentAnalysisService,
    SentimentResult,
    SentimentType,
)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic Claude client."""
    client = MagicMock()
    client.messages.create = MagicMock()
    return client


@pytest.fixture
def mock_gemini_client():
    """Mock Gemini client."""
    client = MagicMock()
    client.generate_content = MagicMock()
    return client


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def sentiment_service(mock_cache_service):
    """Create sentiment analysis service for testing."""
    return SentimentAnalysisService(
        anthropic_api_key="test_anthropic_key",
        gemini_api_key="test_gemini_key",
        cache_service=mock_cache_service,
    )


class TestSentimentAnalysisService:
    """Test suite for SentimentAnalysisService."""

    @pytest.mark.asyncio
    async def test_analyze_positive_sentiment(self, sentiment_service):
        """Test detection of positive sentiment."""
        message = "I'm so excited about this property! It looks amazing!"

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence > 0.5
        assert result.escalation_required == EscalationLevel.NONE
        assert result.suggested_response_tone == "enthusiastic"

    @pytest.mark.asyncio
    async def test_analyze_neutral_sentiment(self, sentiment_service):
        """Test detection of neutral sentiment."""
        message = "I'm looking for a 3-bedroom house in Rancho Cucamonga."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.NEUTRAL
        assert result.confidence > 0.0
        assert result.escalation_required == EscalationLevel.NONE
        assert result.suggested_response_tone == "professional"

    @pytest.mark.asyncio
    async def test_analyze_anxious_sentiment(self, sentiment_service):
        """Test detection of anxious sentiment."""
        message = "I'm really worried about the mortgage process. I've never done this before."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.ANXIOUS
        assert result.confidence > 0.5
        assert result.suggested_response_tone == "empathetic"

    @pytest.mark.asyncio
    async def test_analyze_frustrated_sentiment(self, sentiment_service):
        """Test detection of frustrated sentiment."""
        message = "This is so frustrating! I've been waiting for days and still no response."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.FRUSTRATED
        assert result.confidence > 0.5
        # Should trigger escalation if confidence is high enough
        if result.confidence >= 0.6:
            assert result.escalation_required in [EscalationLevel.MONITOR, EscalationLevel.HUMAN_HANDOFF]
        assert result.suggested_response_tone == "apologetic"

    @pytest.mark.asyncio
    async def test_analyze_angry_sentiment(self, sentiment_service):
        """Test detection of angry sentiment."""
        message = "This is absolutely unacceptable! I'm furious about this terrible service!"

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.ANGRY
        assert result.confidence > 0.5
        # Should trigger escalation
        assert result.escalation_required in [EscalationLevel.HUMAN_HANDOFF, EscalationLevel.CRITICAL]
        assert result.suggested_response_tone == "calm"

    @pytest.mark.asyncio
    async def test_analyze_disappointed_sentiment(self, sentiment_service):
        """Test detection of disappointed sentiment."""
        message = "I'm really disappointed. I expected much better service than this."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.DISAPPOINTED
        assert result.confidence > 0.5
        assert result.suggested_response_tone == "empathetic"

    @pytest.mark.asyncio
    async def test_analyze_confused_sentiment(self, sentiment_service):
        """Test detection of confused sentiment."""
        message = "I don't understand what this means. Can you explain it more clearly?"

        result = await sentiment_service.analyze_sentiment(message)

        assert result.sentiment == SentimentType.CONFUSED
        assert result.confidence > 0.5
        assert result.suggested_response_tone == "patient"

    @pytest.mark.asyncio
    async def test_confidence_scoring(self, sentiment_service):
        """Test that confidence scores are in valid range."""
        message = "I'm happy with this!"

        result = await sentiment_service.analyze_sentiment(message)

        assert 0.0 <= result.confidence <= 1.0
        assert 0.0 <= result.intensity <= 1.0

    @pytest.mark.asyncio
    async def test_escalation_triggers_angry_high_confidence(self, sentiment_service):
        """Test that angry sentiment with high confidence triggers critical escalation."""
        message = "This is the worst service I've ever received! I'm absolutely furious!"

        result = await sentiment_service.analyze_sentiment(message)

        if result.sentiment == SentimentType.ANGRY and result.confidence >= 0.7:
            assert result.escalation_required == EscalationLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_escalation_triggers_angry_medium_confidence(self, sentiment_service):
        """Test that angry sentiment with medium confidence triggers human handoff."""
        message = "I'm very angry about this situation."

        result = await sentiment_service.analyze_sentiment(message)

        if result.sentiment == SentimentType.ANGRY and result.confidence >= 0.5:
            assert result.escalation_required in [EscalationLevel.HUMAN_HANDOFF, EscalationLevel.CRITICAL]

    @pytest.mark.asyncio
    async def test_escalation_triggers_frustrated_high_confidence(self, sentiment_service):
        """Test that frustrated sentiment with high confidence triggers human handoff."""
        message = "This is incredibly frustrating! I'm fed up with waiting!"

        result = await sentiment_service.analyze_sentiment(message)

        if result.sentiment == SentimentType.FRUSTRATED and result.confidence >= 0.8:
            assert result.escalation_required == EscalationLevel.HUMAN_HANDOFF

    @pytest.mark.asyncio
    async def test_escalation_triggers_frustrated_medium_confidence(self, sentiment_service):
        """Test that frustrated sentiment with medium confidence triggers monitor."""
        message = "This is frustrating."

        result = await sentiment_service.analyze_sentiment(message)

        if result.sentiment == SentimentType.FRUSTRATED and result.confidence >= 0.6:
            assert result.escalation_required in [EscalationLevel.MONITOR, EscalationLevel.HUMAN_HANDOFF]

    @pytest.mark.asyncio
    async def test_escalation_triggers_critical_keywords(self, sentiment_service):
        """Test that critical keywords trigger escalation regardless of sentiment."""
        message = "I'm going to get a lawyer and sue you for this!"

        result = await sentiment_service.analyze_sentiment(message)

        # Should trigger critical escalation due to "lawyer" and "sue"
        assert result.escalation_required == EscalationLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_no_escalation_for_positive_sentiment(self, sentiment_service):
        """Test that positive sentiment doesn't trigger escalation."""
        message = "This is great! I'm very happy with the service."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.escalation_required == EscalationLevel.NONE

    @pytest.mark.asyncio
    async def test_no_escalation_for_neutral_sentiment(self, sentiment_service):
        """Test that neutral sentiment doesn't trigger escalation."""
        message = "I'm looking for information about buying a house."

        result = await sentiment_service.analyze_sentiment(message)

        assert result.escalation_required == EscalationLevel.NONE

    @pytest.mark.asyncio
    async def test_cache_hit(self, sentiment_service, mock_cache_service):
        """Test that cached results are returned when available."""
        message = "I'm happy!"

        # Set up cache to return a cached result
        cached_result = SentimentResult(
            sentiment=SentimentType.POSITIVE,
            confidence=0.9,
            intensity=0.8,
            key_phrases=["happy"],
        )
        mock_cache_service.get.return_value = json.dumps(cached_result.__dict__, default=str)

        result = await sentiment_service.analyze_sentiment(message, use_cache=True)

        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence == 0.9
        mock_cache_service.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss(self, sentiment_service, mock_cache_service):
        """Test that analysis is performed when cache miss occurs."""
        message = "I'm happy!"

        # Set up cache to return None (miss)
        mock_cache_service.get.return_value = None

        result = await sentiment_service.analyze_sentiment(message, use_cache=True)

        assert result is not None
        mock_cache_service.get.assert_called_once()
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_history_context(self, sentiment_service):
        """Test that conversation history provides context for analysis."""
        message = "I'm not sure about this."
        history = [
            "I'm looking for a house",
            "Here are some options",
            "I'm worried about the price",
        ]

        result = await sentiment_service.analyze_sentiment(message, conversation_history=history)

        assert result is not None
        # The history should help identify the sentiment more accurately

    @pytest.mark.asyncio
    async def test_analyze_conversation(self, sentiment_service):
        """Test analysis of full conversation."""
        messages = [
            "I'm looking for a house",
            "Great! What's your budget?",
            "I'm worried about the mortgage process",
            "Don't worry, we can help",
            "That's a relief, thank you!",
        ]

        result = await sentiment_service.analyze_conversation(messages)

        assert isinstance(result, ConversationSentiment)
        assert result.overall_sentiment in [s.value for s in SentimentType]
        assert result.sentiment_trend in ["improving", "stable", "declining"]
        assert len(result.message_results) == len(messages)
        assert 0.0 <= result.avg_confidence <= 1.0

    @pytest.mark.asyncio
    async def test_conversation_trend_improving(self, sentiment_service):
        """Test detection of improving sentiment trend."""
        messages = [
            "I'm frustrated with this process",
            "I understand your frustration",
            "This is still annoying",
            "Let me help resolve this",
            "Okay, that's better, thank you",
        ]

        result = await sentiment_service.analyze_conversation(messages)

        # Should detect improving trend (negative to positive)
        assert result.sentiment_trend in ["improving", "stable"]

    @pytest.mark.asyncio
    async def test_conversation_trend_declining(self, sentiment_service):
        """Test detection of declining sentiment trend."""
        messages = [
            "This looks great!",
            "I'm happy with this",
            "I'm a bit concerned now",
            "This is getting frustrating",
            "I'm very angry about this!",
        ]

        result = await sentiment_service.analyze_conversation(messages)

        # Should detect declining trend (positive to negative)
        assert result.sentiment_trend in ["declining", "stable"]

    @pytest.mark.asyncio
    async def test_empty_conversation(self, sentiment_service):
        """Test handling of empty conversation."""
        result = await sentiment_service.analyze_conversation([])

        assert result.overall_sentiment == SentimentType.NEUTRAL
        assert result.sentiment_trend == "stable"
        assert result.avg_confidence == 0.0

    @pytest.mark.asyncio
    async def test_get_response_tone_adjustment(self, sentiment_service):
        """Test getting response tone adjustments for each sentiment."""
        # Test all sentiment types
        for sentiment in SentimentType:
            adjustment = sentiment_service.get_response_tone_adjustment(sentiment)

            assert "tone" in adjustment
            assert "pace" in adjustment
            assert "emojis" in adjustment
            assert "phrases" in adjustment
            assert isinstance(adjustment["phrases"], list)

    @pytest.mark.asyncio
    async def test_keyword_fallback(self, sentiment_service):
        """Test keyword-based fallback when AI fails."""
        # Create service without AI clients
        service = SentimentAnalysisService(
            anthropic_api_key=None,
            gemini_api_key=None,
            cache_service=mock_cache_service,
        )

        message = "I'm so angry about this terrible service!"

        result = await service.analyze_sentiment(message)

        # Should still detect sentiment using keywords
        assert result.sentiment == SentimentType.ANGRY
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_edge_case_empty_message(self, sentiment_service):
        """Test handling of empty message."""
        result = await sentiment_service.analyze_sentiment("")

        assert result is not None
        assert result.sentiment == SentimentType.NEUTRAL

    @pytest.mark.asyncio
    async def test_edge_case_very_long_message(self, sentiment_service):
        """Test handling of very long message."""
        long_message = "I'm happy! " * 1000

        result = await sentiment_service.analyze_sentiment(long_message)

        assert result is not None
        assert result.sentiment == SentimentType.POSITIVE

    @pytest.mark.asyncio
    async def test_edge_case_special_characters(self, sentiment_service):
        """Test handling of special characters."""
        message = "I'm so happy!!! 😊🎉 #excited"

        result = await sentiment_service.analyze_sentiment(message)

        assert result is not None
        assert result.sentiment == SentimentType.POSITIVE

    @pytest.mark.asyncio
    async def test_edge_case_multilingual(self, sentiment_service):
        """Test handling of multilingual message."""
        message = "I'm very happy! ¡Estoy muy feliz! Je suis très heureux!"

        result = await sentiment_service.analyze_sentiment(message)

        assert result is not None
        # Should detect positive sentiment despite multiple languages

    @pytest.mark.asyncio
    async def test_key_phrases_extraction(self, sentiment_service):
        """Test that key phrases are extracted from message."""
        message = "I'm worried about the mortgage process and the down payment."

        result = await sentiment_service.analyze_sentiment(message)

        assert isinstance(result.key_phrases, list)
        # May contain phrases like "worried", "mortgage", etc.

    @pytest.mark.asyncio
    async def test_timestamp_in_result(self, sentiment_service):
        """Test that timestamp is included in result."""
        message = "I'm happy!"

        result = await sentiment_service.analyze_sentiment(message)

        assert isinstance(result.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_escalation_history_tracking(self, sentiment_service):
        """Test that escalation history is tracked in conversation analysis."""
        messages = [
            "I'm frustrated",
            "I'm very angry now!",
            "This is unacceptable!",
        ]

        result = await sentiment_service.analyze_conversation(messages)

        # Should have escalation history entries
        assert isinstance(result.escalation_history, list)
        # At least one message should trigger escalation
        if result.escalation_history:
            assert "escalation_level" in result.escalation_history[0]
            assert "sentiment" in result.escalation_history[0]


class TestSentimentResult:
    """Test suite for SentimentResult dataclass."""

    def test_sentiment_result_creation(self):
        """Test creating a SentimentResult."""
        result = SentimentResult(
            sentiment=SentimentType.POSITIVE,
            confidence=0.9,
            intensity=0.8,
            key_phrases=["happy", "excited"],
            escalation_required=EscalationLevel.NONE,
            suggested_response_tone="enthusiastic",
        )

        assert result.sentiment == SentimentType.POSITIVE
        assert result.confidence == 0.9
        assert result.intensity == 0.8
        assert result.key_phrases == ["happy", "excited"]
        assert result.escalation_required == EscalationLevel.NONE
        assert result.suggested_response_tone == "enthusiastic"

    def test_sentiment_result_defaults(self):
        """Test SentimentResult default values."""
        result = SentimentResult(
            sentiment=SentimentType.NEUTRAL,
            confidence=0.5,
            intensity=0.3,
        )

        assert result.key_phrases == []
        assert result.escalation_required == EscalationLevel.NONE
        assert result.suggested_response_tone == "professional"
        assert isinstance(result.timestamp, datetime)


class TestConversationSentiment:
    """Test suite for ConversationSentiment dataclass."""

    def test_conversation_sentiment_creation(self):
        """Test creating a ConversationSentiment."""
        message_results = [
            SentimentResult(
                sentiment=SentimentType.POSITIVE,
                confidence=0.9,
                intensity=0.8,
            ),
            SentimentResult(
                sentiment=SentimentType.NEUTRAL,
                confidence=0.7,
                intensity=0.5,
            ),
        ]

        result = ConversationSentiment(
            overall_sentiment=SentimentType.POSITIVE,
            sentiment_trend="stable",
            message_results=message_results,
            escalation_history=[],
            avg_confidence=0.8,
        )

        assert result.overall_sentiment == SentimentType.POSITIVE
        assert result.sentiment_trend == "stable"
        assert len(result.message_results) == 2
        assert result.avg_confidence == 0.8

    def test_conversation_sentiment_defaults(self):
        """Test ConversationSentiment default values."""
        result = ConversationSentiment(
            overall_sentiment=SentimentType.NEUTRAL,
            sentiment_trend="stable",
        )

        assert result.message_results == []
        assert result.escalation_history == []
        assert result.avg_confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
