import pytest
pytestmark = pytest.mark.integration

"""
Tests for Voice AI Service

Comprehensive test suite for Jorge's voice AI capabilities:
- Voice interaction session management
- AI response generation
- Voice analytics and insights
- Error handling and fallbacks
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ghl_real_estate_ai.services.voice_ai_service import (

    VoiceAIService,
    VoiceAnalytics,
    VoiceInteraction,
    VoiceInteractionType,
    get_voice_ai_service,
)


@pytest_asyncio.fixture
async def voice_ai_service():
    """Create a VoiceAIService instance for testing."""
    service = VoiceAIService()

    # Mock the Claude assistant to avoid actual API calls
    service.claude_assistant = MagicMock()
    service.claude_assistant.initialize = AsyncMock()
    service.claude_assistant.chat_with_claude = AsyncMock()

    # Mock cache service
    service.cache = MagicMock()
    service.cache.set = AsyncMock()
    service.cache.get = AsyncMock()

    await service.initialize()
    return service


@pytest.fixture
def sample_interaction_context():
    """Sample context for voice interaction testing."""
    return {
        "agent_id": "test_agent_001",
        "lead_id": "test_lead_123",
        "interaction_type": VoiceInteractionType.LEAD_QUALIFICATION,
        "context": {
            "lead_preferences": {"budget_max": 500000, "location": "Rancho Cucamonga, CA", "property_type": "Single Family"}
        },
    }


@pytest.mark.asyncio
class TestVoiceAIService:
    """Test cases for VoiceAIService functionality."""

    async def test_service_initialization(self, voice_ai_service):
        """Test that the voice AI service initializes correctly."""
        assert voice_ai_service._initialized is True
        assert voice_ai_service.claude_assistant is not None
        assert voice_ai_service.cache is not None
        assert isinstance(voice_ai_service.active_sessions, dict)
        assert isinstance(voice_ai_service.analytics_cache, dict)

    async def test_start_voice_interaction(self, voice_ai_service, sample_interaction_context):
        """Test starting a new voice interaction session."""
        context = sample_interaction_context

        interaction_id = await voice_ai_service.start_voice_interaction(
            agent_id=context["agent_id"],
            interaction_type=context["interaction_type"],
            lead_id=context["lead_id"],
            context=context["context"],
        )

        assert interaction_id is not None
        assert interaction_id.startswith("voice_")
        assert interaction_id in voice_ai_service.active_sessions

        # Verify interaction properties
        interaction = voice_ai_service.active_sessions[interaction_id]
        assert interaction.agent_id == context["agent_id"]
        assert interaction.lead_id == context["lead_id"]
        assert interaction.interaction_type == context["interaction_type"]
        assert interaction.start_time is not None
        assert interaction.end_time is None

        # Verify cache was called to store context
        voice_ai_service.cache.set.assert_called_once()

    async def test_process_voice_input(self, voice_ai_service, sample_interaction_context):
        """Test processing voice input and generating AI responses."""
        context = sample_interaction_context

        # Start a session first
        interaction_id = await voice_ai_service.start_voice_interaction(
            agent_id=context["agent_id"], interaction_type=context["interaction_type"], lead_id=context["lead_id"]
        )

        # Mock Claude response
        voice_ai_service.claude_assistant.chat_with_claude.return_value = (
            "I understand you're looking for a home in Rancho Cucamonga. Based on your budget of $500K, "
            "I have several great options in family-friendly neighborhoods. "
            "Would you like to see some properties with good school districts?"
        )

        test_transcript = "Hi, I'm looking for a 3-bedroom house in Rancho Cucamonga under $500k"

        # Process the voice input
        result = await voice_ai_service.process_voice_input(interaction_id=interaction_id, transcript=test_transcript)

        # Verify result structure
        assert "ai_response" in result
        assert "analytics" in result
        assert "interaction_status" in result
        assert "recommendations" in result
        assert "next_best_action" in result

        # Verify interaction was updated
        interaction = voice_ai_service.active_sessions[interaction_id]
        assert test_transcript in interaction.transcript
        assert len(interaction.ai_responses) > 0

        # Verify Claude was called for both analysis and response
        assert voice_ai_service.claude_assistant.chat_with_claude.call_count >= 1

    async def test_process_voice_input_invalid_session(self, voice_ai_service):
        """Test processing voice input with invalid session ID."""
        with pytest.raises(ValueError, match="No active session found"):
            await voice_ai_service.process_voice_input(
                interaction_id="invalid_session_id", transcript="Test transcript"
            )

    async def test_end_voice_interaction(self, voice_ai_service, sample_interaction_context):
        """Test ending a voice interaction session."""
        context = sample_interaction_context

        # Start a session
        interaction_id = await voice_ai_service.start_voice_interaction(
            agent_id=context["agent_id"], interaction_type=context["interaction_type"]
        )

        # Process some input to have conversation data
        voice_ai_service.claude_assistant.chat_with_claude.return_value = "Test response"
        await voice_ai_service.process_voice_input(interaction_id=interaction_id, transcript="Test input")

        # Mock summary generation
        voice_ai_service.claude_assistant.chat_with_claude.return_value = (
            "Client showed strong interest in properties under $500K in Rancho Cucamonga. "
            "Recommended next steps: Schedule property viewings in Cedar Park area. "
            "Conversion likelihood: High"
        )

        # End the session
        summary = await voice_ai_service.end_voice_interaction(interaction_id)

        # Verify summary structure
        assert "interaction_id" in summary
        assert "duration_seconds" in summary
        assert "interaction_type" in summary
        assert "summary" in summary
        assert "completed_at" in summary

        # Verify session was cleaned up
        assert interaction_id not in voice_ai_service.active_sessions

        # Verify cache was called to store summary
        voice_ai_service.cache.set.assert_called()

    async def test_end_voice_interaction_invalid_session(self, voice_ai_service):
        """Test ending interaction with invalid session ID."""
        with pytest.raises(ValueError, match="No active session found"):
            await voice_ai_service.end_voice_interaction("invalid_session_id")

    async def test_voice_analytics_generation(self, voice_ai_service, sample_interaction_context):
        """Test voice analytics generation and caching."""
        context = sample_interaction_context

        # Start session and process input
        interaction_id = await voice_ai_service.start_voice_interaction(
            agent_id=context["agent_id"], interaction_type=context["interaction_type"]
        )

        # Mock Claude analysis response
        voice_ai_service.claude_assistant.chat_with_claude.return_value = "Mock analysis response"

        await voice_ai_service.process_voice_input(
            interaction_id=interaction_id, transcript="I'm very excited about finding a home in Rancho Cucamonga!"
        )

        # Verify analytics were cached
        assert interaction_id in voice_ai_service.analytics_cache

        analytics = voice_ai_service.analytics_cache[interaction_id]
        assert isinstance(analytics, VoiceAnalytics)
        assert analytics.interaction_id == interaction_id
        assert 0.0 <= analytics.overall_sentiment <= 1.0
        assert 0.0 <= analytics.engagement_level <= 1.0
        assert 0.0 <= analytics.conversion_probability <= 1.0

    async def test_get_voice_analytics_dashboard(self, voice_ai_service):
        """Test getting voice analytics dashboard data."""
        dashboard_data = await voice_ai_service.get_voice_analytics_dashboard(agent_id="test_agent", days=7)

        # Verify dashboard data structure
        required_fields = [
            "total_interactions",
            "avg_duration_minutes",
            "conversion_rate",
            "avg_sentiment_score",
            "top_intents",
            "sentiment_distribution",
            "conversion_by_type",
            "ai_performance",
        ]

        for field in required_fields:
            assert field in dashboard_data

        # Verify data types
        assert isinstance(dashboard_data["total_interactions"], int)
        assert isinstance(dashboard_data["avg_duration_minutes"], (int, float))
        assert isinstance(dashboard_data["conversion_rate"], (int, float))
        assert isinstance(dashboard_data["top_intents"], list)
        assert isinstance(dashboard_data["sentiment_distribution"], dict)

    @patch("ghl_real_estate_ai.services.voice_ai_service.logger")
    async def test_error_handling_claude_failure(self, mock_logger, voice_ai_service, sample_interaction_context):
        """Test error handling when Claude AI fails."""
        context = sample_interaction_context

        interaction_id = await voice_ai_service.start_voice_interaction(
            agent_id=context["agent_id"], interaction_type=context["interaction_type"]
        )

        # Make Claude fail
        voice_ai_service.claude_assistant.chat_with_claude.side_effect = Exception("Claude API error")

        # Process voice input should still work with fallbacks
        result = await voice_ai_service.process_voice_input(interaction_id=interaction_id, transcript="Test input")

        # Verify fallback response was provided
        assert "ai_response" in result
        assert result["ai_response"] is not None

        # Verify warning was logged
        mock_logger.warning.assert_called()

    async def test_fallback_analytics(self, voice_ai_service):
        """Test fallback analytics when AI analysis fails."""
        fallback_analytics = voice_ai_service._get_fallback_analytics("test_interaction")

        assert isinstance(fallback_analytics, VoiceAnalytics)
        assert fallback_analytics.interaction_id == "test_interaction"
        assert fallback_analytics.overall_sentiment == 0.5
        assert fallback_analytics.emotional_state == "neutral"
        assert fallback_analytics.engagement_level == 0.7
        assert "continue_conversation" in fallback_analytics.recommended_actions

    def test_fallback_responses(self, voice_ai_service):
        """Test fallback responses for different interaction types."""
        for interaction_type in VoiceInteractionType:
            fallback_response = voice_ai_service._get_fallback_response(interaction_type)

            assert isinstance(fallback_response, str)
            assert len(fallback_response) > 0

    async def test_concurrent_sessions(self, voice_ai_service):
        """Test handling multiple concurrent voice sessions."""
        # Start multiple sessions
        session_ids = []
        for i in range(3):
            interaction_id = await voice_ai_service.start_voice_interaction(
                agent_id=f"agent_{i}", interaction_type=VoiceInteractionType.LEAD_QUALIFICATION
            )
            session_ids.append(interaction_id)

        # Verify all sessions are active
        assert len(voice_ai_service.active_sessions) == 3

        # Process input for each session
        voice_ai_service.claude_assistant.chat_with_claude.return_value = "Test response"

        for session_id in session_ids:
            result = await voice_ai_service.process_voice_input(
                interaction_id=session_id, transcript=f"Test input for {session_id}"
            )
            assert result["interaction_status"] == "active"

        # End all sessions
        for session_id in session_ids:
            voice_ai_service.claude_assistant.chat_with_claude.return_value = "Test summary"
            summary = await voice_ai_service.end_voice_interaction(session_id)
            assert summary["interaction_id"] == session_id

        # Verify all sessions are cleaned up
        assert len(voice_ai_service.active_sessions) == 0


class TestVoiceInteraction:
    """Test cases for VoiceInteraction data structure."""

    def test_voice_interaction_creation(self):
        """Test creating a VoiceInteraction instance."""
        interaction = VoiceInteraction(
            interaction_id="test_123",
            agent_id="agent_001",
            interaction_type=VoiceInteractionType.PROPERTY_SEARCH,
            start_time=datetime.now(),
            lead_id="lead_456",
        )

        assert interaction.interaction_id == "test_123"
        assert interaction.agent_id == "agent_001"
        assert interaction.lead_id == "lead_456"
        assert interaction.interaction_type == VoiceInteractionType.PROPERTY_SEARCH
        assert isinstance(interaction.ai_responses, list)
        assert isinstance(interaction.sentiment_scores, dict)
        assert isinstance(interaction.conversion_indicators, list)

    def test_voice_interaction_post_init(self):
        """Test VoiceInteraction post-init default values."""
        interaction = VoiceInteraction(
            interaction_id="test_123",
            agent_id="agent_001",
            lead_id=None,
            interaction_type=VoiceInteractionType.GENERAL_INQUIRY,
            start_time=datetime.now(),
        )

        assert interaction.ai_responses == []
        assert interaction.sentiment_scores == {}
        assert interaction.conversion_indicators == []
        assert interaction.transcript == ""
        assert interaction.intent_confidence == 0.0


class TestVoiceAnalytics:
    """Test cases for VoiceAnalytics data structure."""

    def test_voice_analytics_creation(self):
        """Test creating a VoiceAnalytics instance."""
        analytics = VoiceAnalytics(
            interaction_id="test_123",
            overall_sentiment=0.8,
            emotional_state="excited",
            engagement_level=0.9,
            conversion_probability=0.75,
            key_intents=["buy_property", "view_listings"],
            buying_signals=["budget_discussed", "timeline_mentioned"],
            concerns_identified=["location_concerns"],
            recommended_actions=["schedule_viewing", "send_listings"],
            call_quality_score=0.85,
            next_best_action="Schedule property viewing within 48 hours",
        )

        assert analytics.interaction_id == "test_123"
        assert analytics.overall_sentiment == 0.8
        assert analytics.emotional_state == "excited"
        assert analytics.engagement_level == 0.9
        assert analytics.conversion_probability == 0.75
        assert "buy_property" in analytics.key_intents
        assert "budget_discussed" in analytics.buying_signals
        assert "location_concerns" in analytics.concerns_identified
        assert "schedule_viewing" in analytics.recommended_actions
        assert analytics.call_quality_score == 0.85


class TestGlobalServiceInstance:
    """Test cases for global service instance management."""

    def test_get_voice_ai_service_singleton(self):
        """Test that get_voice_ai_service returns the same instance."""
        service1 = get_voice_ai_service()
        service2 = get_voice_ai_service()

        assert service1 is service2
        assert isinstance(service1, VoiceAIService)

    @patch("ghl_real_estate_ai.services.voice_ai_service._voice_ai_service", None)
    def test_get_voice_ai_service_creates_new_instance(self):
        """Test that get_voice_ai_service creates new instance when needed."""
        service = get_voice_ai_service()

        assert isinstance(service, VoiceAIService)
        assert service.active_sessions == {}
        assert service.analytics_cache == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])