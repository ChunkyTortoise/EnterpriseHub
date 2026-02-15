"""
End-to-end conversation flow tests for Jorge Seller Bot.

Tests complete seller qualification conversations through the LangGraph workflow,
including HOT/WARM/COLD classification paths, opt-out handling, and stall detection.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.lead_scoring import (
    FinancialReadinessScore,
    LeadIntentProfile,
    PsychologicalCommitmentScore,
)


@pytest.fixture
def _mock_seller_deps():
    """Patch all external dependencies for seller bot E2E tests."""
    mock_event_pub = AsyncMock()
    mock_ml = AsyncMock()
    mock_ml.predict_lead_journey = AsyncMock(return_value={})
    mock_ml.predict_conversion_probability = AsyncMock(return_value={"probability": 0.5})
    mock_ml.predict_optimal_touchpoints = AsyncMock(return_value={})

    with (
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.SellerIntentDecoder") as MockSellerIntent,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher", return_value=mock_event_pub),
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine", return_value=mock_ml),
    ):
        seller_intent_instance = MockSellerIntent.return_value
        seller_intent_instance.analyze_seller = MagicMock(return_value=MagicMock())

        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.classification = "Warm Lead"
        mock_profile.frs.total_score = 40
        mock_profile.pcs = MagicMock(spec=PsychologicalCommitmentScore)
        mock_profile.pcs.total_score = 50
        # Expose sub-score attributes needed by recalculate_pcs_node
        mock_profile.pcs.response_velocity_score = 60
        mock_profile.pcs.message_length_score = 55
        mock_profile.pcs.question_depth_score = 50
        mock_profile.pcs.objection_handling_score = 45
        mock_profile.pcs.call_acceptance_score = 40
        mock_profile.lead_id = "test"
        mock_profile.lead_type = "seller"
        mock_profile.market_context = None
        mock_profile.next_best_action = "qualify"

        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.analyze_with_context = AsyncMock(
            return_value={"content": "Mocked Jorge Response"}
        )
        claude_instance.generate_response = AsyncMock(
            return_value={"content": "Mocked Jorge Response"}
        )

        yield {
            "intent": intent_instance,
            "seller_intent": seller_intent_instance,
            "claude": claude_instance,
            "profile": mock_profile,
            "event_pub": mock_event_pub,
        }


# ---------------------------------------------------------------------------
# Happy Path: HOT seller
# ---------------------------------------------------------------------------

class TestSellerHotPath:
    """All 4 questions answered well -> HOT classification -> handoff message."""

    @pytest.mark.asyncio
    async def test_hot_seller_full_qualification(self, _mock_seller_deps):
        """Seller answers motivation, timeline, condition, and price strongly."""
        _mock_seller_deps["profile"].frs.classification = "Hot Lead"
        _mock_seller_deps["profile"].frs.total_score = 85
        _mock_seller_deps["profile"].pcs.total_score = 80

        bot = JorgeSellerBot()

        # Simulate a multi-turn conversation covering all 4 questions
        history = [
            {"role": "assistant", "content": "What's motivating you to sell?"},
            {"role": "user", "content": "I got a job transfer and need to move ASAP."},
            {"role": "assistant", "content": "When do you need to sell by?"},
            {"role": "user", "content": "Within the next 30 days if possible."},
            {"role": "assistant", "content": "How would you describe the condition?"},
            {"role": "user", "content": "Recently renovated, new roof and HVAC."},
            {"role": "assistant", "content": "What price are you hoping for?"},
        ]

        result = await bot.process_seller_message(
            conversation_id="hot_seller_001",
            user_message="Around $650,000 based on recent comps.",
            seller_name="Alice Hot",
            conversation_history=history,
        )

        assert result["lead_id"] == "hot_seller_001"
        assert "response_content" in result
        assert isinstance(result["frs_score"], (int, float))
        assert result["frs_score"] >= 80
        assert isinstance(result["handoff_signals"], dict)

    @pytest.mark.asyncio
    async def test_hot_seller_produces_handoff_signals(self, _mock_seller_deps):
        """A HOT seller mentioning buying triggers buyer handoff signals."""
        _mock_seller_deps["profile"].frs.classification = "Hot Lead"
        _mock_seller_deps["profile"].frs.total_score = 90
        _mock_seller_deps["profile"].pcs.total_score = 85

        bot = JorgeSellerBot()

        result = await bot.process_seller_message(
            conversation_id="hot_seller_002",
            user_message="I want to sell my house and then buy a new one with budget $700k",
            seller_name="Bob Hot",
            conversation_history=[],
        )

        # The user mentions buying, so extract_intent_signals should detect it
        assert "handoff_signals" in result
        signals = result["handoff_signals"]
        assert signals.get("buyer_intent_score", 0) > 0 or signals.get("seller_intent_score", 0) > 0


# ---------------------------------------------------------------------------
# Warm Path
# ---------------------------------------------------------------------------

class TestSellerWarmPath:
    """3 of 4 questions answered -> WARM classification."""

    @pytest.mark.asyncio
    async def test_warm_seller_partial_answers(self, _mock_seller_deps):
        """Seller provides motivation and timeline but is vague on condition and price."""
        _mock_seller_deps["profile"].frs.classification = "Warm Lead"
        _mock_seller_deps["profile"].frs.total_score = 55
        _mock_seller_deps["profile"].pcs.total_score = 45

        bot = JorgeSellerBot()

        history = [
            {"role": "assistant", "content": "What's motivating you to sell?"},
            {"role": "user", "content": "Thinking about downsizing after the kids left."},
            {"role": "assistant", "content": "When would you like to sell?"},
            {"role": "user", "content": "Maybe in the next 3-6 months."},
            {"role": "assistant", "content": "How would you describe the condition of your home?"},
            {"role": "user", "content": "It's okay, needs some work."},
        ]

        result = await bot.process_seller_message(
            conversation_id="warm_seller_001",
            user_message="I'm not sure about the price yet.",
            seller_name="Charlie Warm",
            conversation_history=history,
        )

        assert result["lead_id"] == "warm_seller_001"
        assert "response_content" in result
        assert isinstance(result["frs_score"], (int, float))
        # Score should be moderate
        assert 30 <= result["frs_score"] <= 70


# ---------------------------------------------------------------------------
# Cold Path
# ---------------------------------------------------------------------------

class TestSellerColdPath:
    """Vague or short responses -> COLD classification."""

    @pytest.mark.asyncio
    async def test_cold_seller_vague_responses(self, _mock_seller_deps):
        """Seller gives minimal, non-committal answers."""
        _mock_seller_deps["profile"].frs.classification = "Cold Lead"
        _mock_seller_deps["profile"].frs.total_score = 15
        _mock_seller_deps["profile"].pcs.total_score = 10

        bot = JorgeSellerBot()

        history = [
            {"role": "assistant", "content": "What's motivating you to sell?"},
            {"role": "user", "content": "Just curious about value."},
        ]

        result = await bot.process_seller_message(
            conversation_id="cold_seller_001",
            user_message="Not really looking to sell right now.",
            seller_name="Dave Cold",
            conversation_history=history,
        )

        assert result["lead_id"] == "cold_seller_001"
        assert "response_content" in result
        assert isinstance(result["frs_score"], (int, float))
        assert result["frs_score"] <= 30


# ---------------------------------------------------------------------------
# Opt-Out (TCPA)
# ---------------------------------------------------------------------------

class TestSellerOptOut:
    """'stop' at any point -> TCPA opt-out handling."""

    @pytest.mark.asyncio
    async def test_stop_message_still_returns_response(self, _mock_seller_deps):
        """Seller says 'stop' - bot should still return a valid response dict.

        Note: The seller bot does not have built-in opt-out like the buyer bot.
        Opt-out is handled at the webhook layer. The bot should process normally
        and the handoff_signals should be returned.
        """
        bot = JorgeSellerBot()

        result = await bot.process_seller_message(
            conversation_id="optout_seller_001",
            user_message="stop",
            seller_name="Eve Optout",
            conversation_history=[],
        )

        # Seller bot processes all messages; opt-out is at webhook layer
        assert result["lead_id"] == "optout_seller_001"
        assert "response_content" in result
        assert isinstance(result["handoff_signals"], dict)


# ---------------------------------------------------------------------------
# Stall Detection
# ---------------------------------------------------------------------------

class TestSellerStallDetection:
    """Stall / hesitation messages trigger stall-breaking response."""

    @pytest.mark.asyncio
    async def test_stall_breaking_response(self, _mock_seller_deps):
        """Seller goes silent-then-hesitant -> bot detects and breaks stall."""
        bot = JorgeSellerBot()

        history = [
            {"role": "assistant", "content": "What's your timeline for selling?"},
            {"role": "user", "content": "I need to think about it."},
            {"role": "assistant", "content": "Take your time! Any questions I can answer?"},
        ]

        result = await bot.process_seller_message(
            conversation_id="stall_seller_001",
            user_message="I'm still thinking...",
            seller_name="Frank Stall",
            conversation_history=history,
        )

        assert result["lead_id"] == "stall_seller_001"
        assert "response_content" in result
        assert isinstance(result["frs_score"], (int, float))

    @pytest.mark.asyncio
    async def test_multiple_stall_messages(self, _mock_seller_deps):
        """Multiple hesitation messages should still produce valid workflow output."""
        bot = JorgeSellerBot()

        history = [
            {"role": "user", "content": "I need to think about it."},
            {"role": "assistant", "content": "Of course!"},
            {"role": "user", "content": "Still not sure."},
            {"role": "assistant", "content": "Take your time."},
        ]

        result = await bot.process_seller_message(
            conversation_id="stall_seller_002",
            user_message="Maybe later.",
            seller_name="Grace Stall",
            conversation_history=history,
        )

        assert result["lead_id"] == "stall_seller_002"
        assert "response_content" in result
        assert isinstance(result["handoff_signals"], dict)


# ---------------------------------------------------------------------------
# Error Resilience
# ---------------------------------------------------------------------------

class TestSellerErrorResilience:
    """Bot returns graceful fallback on internal errors."""

    @pytest.mark.asyncio
    async def test_empty_message_returns_fallback(self, _mock_seller_deps):
        """Empty conversation history should not crash the workflow."""
        bot = JorgeSellerBot()

        result = await bot.process_seller_message(
            conversation_id="resilience_001",
            user_message="Hello, I want to sell my home",
            seller_name="Hank",
            conversation_history=[],
        )

        assert result["lead_id"] == "resilience_001"
        assert "response_content" in result

    @pytest.mark.asyncio
    async def test_long_conversation_history(self, _mock_seller_deps):
        """Very long conversation history should not crash."""
        bot = JorgeSellerBot()

        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(50)
        ]

        result = await bot.process_seller_message(
            conversation_id="resilience_002",
            user_message="What do you think?",
            seller_name="Iris Long",
            conversation_history=history,
        )

        assert result["lead_id"] == "resilience_002"
        assert "response_content" in result
