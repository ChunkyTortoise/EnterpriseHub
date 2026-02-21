import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.models.buyer_persona import BuyerPersonaType
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile


@pytest.fixture
def mock_buyer_deps():
    with (
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher") as MockEvent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher") as MockMatcher,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLClient") as MockGhlClient,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLWorkflowService") as MockWorkflowService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ChurnDetectionService") as MockChurnService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.LeadScoringIntegration") as MockLeadScoring,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.SentimentAnalysisService") as MockSentiment,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerPersonaService") as MockPersonaService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_buyer_conversation_memory") as MockConversationMemory,
    ):
        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=BuyerIntentProfile)
        mock_profile.buyer_temperature = "warm"
        mock_profile.financial_readiness = 75.0
        mock_profile.urgency_score = 80.0
        mock_profile.confidence_level = 90.0
        mock_profile.financing_status_score = 80.0
        mock_profile.budget_clarity = 85.0
        mock_profile.preference_clarity = 70.0
        mock_profile.next_qualification_step = "property_search"
        intent_instance.analyze_buyer = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.generate_response = AsyncMock(return_value={"content": "Mocked Buyer Response"})

        matcher_instance = MockMatcher.return_value
        matcher_instance.find_matches = AsyncMock(
            return_value=[
                {"address": "123 Main St", "match_score": 95.0},
                {"address": "456 Oak Ave", "match_score": 88.0},
            ]
        )

        event_instance = MockEvent.return_value
        event_instance.publish_bot_status_update = AsyncMock()
        event_instance.publish_buyer_intent_analysis = AsyncMock()
        event_instance.publish_property_match_update = AsyncMock()
        event_instance.publish_buyer_follow_up_scheduled = AsyncMock()
        event_instance.publish_buyer_qualification_complete = AsyncMock()

        workflow_instance = MockWorkflowService.return_value
        workflow_instance.apply_auto_tags = AsyncMock(return_value={"success": True})

        lead_scoring_instance = MockLeadScoring.return_value
        lead_scoring_instance.calculate_and_store_composite_score = AsyncMock(
            return_value={"composite_score_data": {"total_score": 72.0}}
        )

        churn_instance = MockChurnService.return_value
        churn_instance.assess_churn_risk = AsyncMock(
            return_value=SimpleNamespace(
                risk_score=18.0,
                risk_level=SimpleNamespace(value="low"),
                recommended_action=SimpleNamespace(value="value_reminder"),
            )
        )

        sentiment_instance = MockSentiment.return_value
        sentiment_instance.analyze_sentiment = AsyncMock(
            return_value=SimpleNamespace(
                sentiment=SimpleNamespace(value="neutral"),
                confidence=0.8,
                escalation_required=SimpleNamespace(value="none"),
            )
        )
        sentiment_instance.get_response_tone_adjustment = MagicMock(
            return_value={"tone": "professional", "pace": "normal"}
        )

        persona_instance = MockPersonaService.return_value
        persona_instance.classify_buyer_type = AsyncMock(
            return_value=SimpleNamespace(persona_type=BuyerPersonaType.UNKNOWN, confidence=0.5, detected_signals=[])
        )
        persona_instance.get_persona_insights = AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda: {"tone": "friendly", "content_focus": "general"})
        )

        ghl_client_instance = MockGhlClient.return_value
        ghl_client_instance.add_contact_tags = AsyncMock()
        ghl_client_instance.add_contact_note = AsyncMock()
        ghl_client_instance.send_message = AsyncMock()

        conversation_memory = MockConversationMemory.return_value
        conversation_memory.enabled = False
        conversation_memory.load_state = AsyncMock(return_value=None)
        conversation_memory.save_state = AsyncMock()

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "matcher": matcher_instance,
            "event": event_instance,
            "profile": mock_profile,
            "workflow": workflow_instance,
        }


@pytest.mark.asyncio
async def test_jorge_buyer_bot_qualification_flow(mock_buyer_deps):
    """Test the complete buyer qualification workflow."""
    bot = JorgeBuyerBot(enable_bot_intelligence=False)

    history = [{"role": "user", "content": "I want to buy a house in Rancho Cucamonga for $700k. I am pre-approved."}]

    result = await bot.process_buyer_conversation(
        conversation_id="buyer_123",
        user_message="I want to buy a house in Rancho Cucamonga for $700k. I am pre-approved.",
        buyer_name="Jane Doe",
        conversation_history=history,
    )

    assert result["lead_id"] == "buyer_123"
    assert "response_content" in result
    assert "is_qualified" in result
    assert "financial_readiness_score" in result or "financial_readiness" in result
    assert isinstance(result.get("handoff_signals", {}), dict)

    # Verify buyer qualification complete event was published
    mock_buyer_deps["event"].publish_buyer_qualification_complete.assert_called_once()
    mock_buyer_deps["workflow"].apply_auto_tags.assert_awaited_once()


@pytest.mark.asyncio
async def test_jorge_buyer_bot_low_qualification(mock_buyer_deps):
    """Test that low scores lead to unqualified status."""
    mock_buyer_deps["profile"].financial_readiness = 20.0
    mock_buyer_deps["profile"].urgency_score = 30.0
    mock_buyer_deps["profile"].financing_status_score = 10.0
    mock_buyer_deps["profile"].budget_clarity = 10.0

    bot = JorgeBuyerBot(enable_bot_intelligence=False)

    history = [{"role": "user", "content": "Just looking around."}]

    result = await bot.process_buyer_conversation(
        conversation_id="buyer_low",
        user_message="Just looking around.",
        buyer_name="Window Shopper",
        conversation_history=history,
    )

    assert result["is_qualified"] is False
    assert result["lead_id"] == "buyer_low"
    assert isinstance(result.get("handoff_signals", {}), dict)


@pytest.mark.asyncio
async def test_gather_buyer_intelligence_calls_enhance_bot_context(mock_buyer_deps):
    """Regression: Buyer bot should call enhance_bot_context with updated middleware signature."""
    bot = JorgeBuyerBot(enable_bot_intelligence=False)

    bot.intelligence_middleware = MagicMock()
    bot.intelligence_middleware.enhance_bot_context = AsyncMock(return_value=SimpleNamespace())

    state = {
        "buyer_id": "buyer_999",
        "location_id": "rancho_cucamonga",
        "conversation_history": [{"role": "user", "content": "Budget around 700k"}],
        "property_preferences": {"beds": 3},
        "budget_range": {"max": 700000},
        "urgency_level": "high",
    }

    result = await bot.gather_buyer_intelligence(state)

    assert "intelligence_context" in result
    bot.intelligence_middleware.enhance_bot_context.assert_awaited_once_with(
        bot_type="jorge-buyer",
        lead_id="buyer_999",
        location_id="rancho_cucamonga",
        conversation_context=state["conversation_history"],
        preferences={
            "property_preferences": {"beds": 3},
            "budget_range": {"max": 700000},
            "urgency_level": "high",
        },
    )


class TestBuyerFollowUpSchedule:
    """Tests for spec day-based buyer follow-up scheduling."""

    def test_next_followup_day_from_start(self):
        from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService

        service = BuyerWorkflowService()
        assert service._get_next_buyer_followup_day(0) == 2
        assert service._get_next_buyer_followup_day(2) == 5
        assert service._get_next_buyer_followup_day(5) == 8

    def test_next_followup_day_longterm(self):
        from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService

        service = BuyerWorkflowService()
        assert service._get_next_buyer_followup_day(30) == 44  # 30 + 14

    def test_next_followup_day_at_boundary(self):
        from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService

        service = BuyerWorkflowService()
        assert service._get_next_buyer_followup_day(29) is None  # At last active day, no more active days

    @pytest.mark.asyncio
    async def test_schedule_uses_day_based_timing(self):
        from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService

        service = BuyerWorkflowService()
        state = {"financial_readiness_score": 25, "days_since_start": 0, "buyer_id": "test-buyer"}
        result = await service.schedule_next_action(state)
        # Day 0 → next day is 2 → 48 hours
        assert result["follow_up_hours"] == 48
        assert result["follow_up_scheduled"] is True


# ── UPS Buyer Skills Tests (Module 2) ─────────────────────────────────


class TestBuyerProgressiveSkills:
    """Tests for Unified Progressive Skills integration in buyer bot."""

    @pytest.mark.asyncio
    async def test_buyer_bot_uses_initial_discovery_skill_for_new_lead(self, mock_buyer_deps):
        """New lead (low financial readiness) should trigger InitialDiscovery skill loading."""
        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            bot = JorgeBuyerBot(enable_bot_intelligence=False)

            history = [{"role": "user", "content": "Hi, I'm looking to buy a home"}]

            result = await bot.process_buyer_conversation(
                conversation_id="test_ups_new",
                user_message="Hi, I'm looking to buy a home",
                buyer_name="Test Buyer",
                conversation_history=history,
            )
        assert "response_content" in result
        assert result["lead_id"] == "test_ups_new"

    @pytest.mark.asyncio
    async def test_buyer_bot_falls_back_to_full_model_for_high_intent_lead(self, mock_buyer_deps):
        """High-intent lead (buying_motivation >= 90) should skip progressive skills."""
        mock_buyer_deps["profile"].financial_readiness = 95.0
        mock_buyer_deps["profile"].urgency_score = 95.0
        mock_buyer_deps["profile"].financing_status_score = 95.0
        mock_buyer_deps["profile"].budget_clarity = 95.0

        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            bot = JorgeBuyerBot(enable_bot_intelligence=False)

            history = [
                {"role": "user", "content": "I'm pre-approved for $800k and ready to make an offer"},
                {"role": "assistant", "content": "Great!"},
            ]

            result = await bot.process_buyer_conversation(
                conversation_id="test_ups_high",
                user_message="I'm pre-approved for $800k and ready to make an offer",
                buyer_name="Hot Buyer",
                conversation_history=history,
            )
        assert "response_content" in result
        assert result["lead_id"] == "test_ups_high"

    @pytest.mark.asyncio
    async def test_buyer_progressive_skills_disabled_by_default(self, mock_buyer_deps):
        """Progressive skills should be disabled by default (ENABLE_BUYER_PROGRESSIVE_SKILLS not set)."""
        # Remove the env var if set
        env = {k: v for k, v in os.environ.items() if k != "ENABLE_BUYER_PROGRESSIVE_SKILLS"}
        with patch.dict(os.environ, env, clear=True):
            bot = JorgeBuyerBot(enable_bot_intelligence=False)

            history = [{"role": "user", "content": "Tell me about homes"}]

            result = await bot.process_buyer_conversation(
                conversation_id="test_ups_disabled",
                user_message="Tell me about homes",
                buyer_name="Default Buyer",
                conversation_history=history,
            )
        assert "response_content" in result
        assert result["lead_id"] == "test_ups_disabled"

    def test_load_buyer_skill_context_returns_skill_when_enabled(self):
        """Verify _load_buyer_skill_context loads the correct skill file."""
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        rg = ResponseGenerator()
        state = {
            "financial_readiness_score": 10,
            "current_qualification_step": "budget",
            "buying_motivation_score": 30,
        }
        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            content = rg._load_buyer_skill_context(state)
        assert "InitialDiscoverySkill" in content

    def test_load_buyer_skill_context_returns_empty_when_disabled(self):
        """Verify _load_buyer_skill_context returns empty string when feature is off."""
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        rg = ResponseGenerator()
        state = {"financial_readiness_score": 10}
        env = {k: v for k, v in os.environ.items() if k != "ENABLE_BUYER_PROGRESSIVE_SKILLS"}
        with patch.dict(os.environ, env, clear=True):
            content = rg._load_buyer_skill_context(state)
        assert content == ""

    def test_load_buyer_skill_context_skips_high_motivation(self):
        """High buying_motivation (>= 90) should skip progressive skills."""
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        rg = ResponseGenerator()
        state = {
            "financial_readiness_score": 95,
            "buying_motivation_score": 95,
        }
        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            content = rg._load_buyer_skill_context(state)
        assert content == ""

    def test_load_buyer_skill_context_objection_handling(self):
        """Detected objection should load objection_handling skill."""
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        rg = ResponseGenerator()
        state = {
            "financial_readiness_score": 50,
            "buying_motivation_score": 50,
            "detected_objection_type": "timing",
        }
        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            content = rg._load_buyer_skill_context(state)
        assert "ObjectionHandlingSkill" in content

    def test_load_buyer_skill_context_property_matching(self):
        """Preferences step should load property_matching skill."""
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        rg = ResponseGenerator()
        state = {
            "financial_readiness_score": 50,
            "buying_motivation_score": 50,
            "current_qualification_step": "preferences",
        }
        with patch.dict(os.environ, {"ENABLE_BUYER_PROGRESSIVE_SKILLS": "true"}):
            content = rg._load_buyer_skill_context(state)
        assert "PropertyMatchingSkill" in content
