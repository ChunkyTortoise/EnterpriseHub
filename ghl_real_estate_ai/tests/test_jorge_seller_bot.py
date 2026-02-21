from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.lead_scoring import (
    FinancialReadinessScore,
    LeadIntentProfile,
    PsychologicalCommitmentScore,
)


@pytest.fixture
def mock_jorge_deps():
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
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.GHLWorkflowService") as MockWorkflowService,
    ):
        seller_intent_instance = MockSellerIntent.return_value
        seller_intent_instance.analyze_seller = MagicMock(return_value=MagicMock())

        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.classification = "Warm Lead"
        mock_profile.frs.total_score = 40
        mock_profile.pcs = MagicMock()
        mock_profile.pcs.total_score = 50
        mock_profile.pcs.response_velocity_score = 70
        mock_profile.pcs.message_length_score = 70
        mock_profile.pcs.question_depth_score = 70
        mock_profile.pcs.objection_handling_score = 70
        mock_profile.pcs.call_acceptance_score = 70
        mock_profile.lead_id = "lead_123"
        mock_profile.lead_type = "seller"
        mock_profile.market_context = "rancho_cucamonga"
        mock_profile.next_best_action = "continue_qualification"
        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.analyze_with_context = AsyncMock(return_value={"content": "Mocked Jorge Response"})
        claude_instance.generate_response = AsyncMock(return_value="Mocked Jorge Response")

        workflow_instance = MockWorkflowService.return_value
        workflow_instance.apply_auto_tags = AsyncMock(return_value={"success": True})

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "profile": mock_profile,
            "workflow": workflow_instance,
        }


@pytest.mark.asyncio
async def test_jorge_seller_bot_stall_breaking(mock_jorge_deps):
    """Test that the bot processes a stall message and returns a valid response."""
    bot = JorgeSellerBot()

    history = [{"role": "user", "content": "I need to think about it."}]

    result = await bot.process_seller_message(
        conversation_id="lead_123",
        user_message="I need to think about it.",
        seller_name="John Doe",
        conversation_history=history,
    )

    assert result["lead_id"] == "lead_123"
    assert "response_content" in result
    assert isinstance(result["frs_score"], (int, float))
    assert isinstance(result["handoff_signals"], dict)
    mock_jorge_deps["workflow"].apply_auto_tags.assert_awaited_once()


@pytest.mark.asyncio
async def test_jorge_seller_bot_educational_mode(mock_jorge_deps):
    """Test that low PCS still produces a valid response through the workflow."""
    mock_jorge_deps["profile"].pcs.total_score = 10

    bot = JorgeSellerBot()

    history = [{"role": "user", "content": "Just curious about value."}]

    result = await bot.process_seller_message(
        conversation_id="lead_low",
        user_message="Just curious about value.",
        seller_name="Tire Kicker",
        conversation_history=history,
    )

    assert result["lead_id"] == "lead_low"
    assert "response_content" in result
    assert isinstance(result["frs_score"], (int, float))
    assert isinstance(result["handoff_signals"], dict)


def test_budget_keyword_under_500_maps_to_500k(mock_jorge_deps):
    """Regression: 'under 500' should map to budget_max=500000, not 700000."""
    bot = JorgeSellerBot()
    preferences = bot._extract_preferences_from_conversation(
        [{"role": "user", "content": "I'm looking for something under 500 in this area"}]
    )

    assert preferences["budget_max"] == 500000


class TestToneEnginePersonalization:
    """Fix 11: _personalize should lowercase only the first char, not the whole message."""

    def test_handoff_preserves_casing(self):
        from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

        engine = JorgeToneEngine()
        msg = engine.generate_hot_seller_handoff(seller_name="John")
        # First char lowered: "Based on..." -> "based on..."
        assert "John, based on" in msg
        # Mid-sentence "What" must stay capitalised (old .lower() broke this)
        assert "What time" in msg


class TestClassifyOfferType:
    """Offer pathway classification derived from existing 4-question answers."""

    def test_fixer_upper_is_wholesale(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        assert JorgeSellerConfig.classify_offer_type(property_condition="needs work") == "wholesale"

    def test_inherited_property_is_wholesale(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        assert JorgeSellerConfig.classify_offer_type(seller_motivation="inherited property from parents") == "wholesale"

    def test_move_in_ready_is_listing(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        assert JorgeSellerConfig.classify_offer_type(property_condition="move-in ready") == "listing"

    def test_relocation_is_listing(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        assert JorgeSellerConfig.classify_offer_type(seller_motivation="relocating for new job") == "listing"

    def test_empty_inputs_return_unknown(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        assert JorgeSellerConfig.classify_offer_type() == "unknown"

    def test_condition_takes_priority_over_motivation(self):
        """Fixer-upper condition overrides relocation motivation → wholesale."""
        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        result = JorgeSellerConfig.classify_offer_type(
            property_condition="fixer, needs significant repairs",
            seller_motivation="relocating",
        )
        assert result == "wholesale"


# ── QBQ Discovery Loop Tests (Module 4) ────────────────────────────────


class TestQBQDiscoveryLoop:
    """Tests for QBQ (Question Behind the Question) discovery loop."""

    def test_stall_detector_surface_objection_keywords(self):
        """StallDetector should detect surface_objection keyword patterns."""
        from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector

        assert "surface_objection" in StallDetector.STALL_KEYWORDS
        assert any("zillow says" in k for k in StallDetector.STALL_KEYWORDS["surface_objection"])

    def test_is_surface_objection_true_for_zestimate_stall(self):
        from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector

        detector = StallDetector()
        state = {
            "lead_id": "test",
            "stall_detected": True,
            "detected_stall_type": "zestimate",
            "conversation_history": [],
        }
        assert detector.is_surface_objection(state) is True

    def test_is_surface_objection_true_for_surface_objection_type(self):
        from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector

        detector = StallDetector()
        state = {
            "lead_id": "test",
            "stall_detected": True,
            "detected_stall_type": "surface_objection",
            "conversation_history": [],
        }
        assert detector.is_surface_objection(state) is True

    def test_is_surface_objection_false_when_no_stall(self):
        from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector

        detector = StallDetector()
        state = {
            "lead_id": "test",
            "stall_detected": False,
            "detected_stall_type": None,
            "conversation_history": [],
        }
        assert detector.is_surface_objection(state) is False

    def test_seller_state_has_qbq_fields(self):
        """JorgeSellerState TypedDict should include QBQ fields."""
        from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState

        annotations = JorgeSellerState.__annotations__
        assert "deep_motivation" in annotations
        assert "qbq_attempted" in annotations

    @pytest.mark.asyncio
    async def test_qbq_loop_not_repeated_on_same_objection(self, mock_jorge_deps):
        """When qbq_attempted=True, negotiation_discovery node should skip Voss call."""
        bot = JorgeSellerBot()
        state = {
            "lead_id": "test_lead",
            "lead_name": "Test",
            "property_address": "123 Main St",
            "conversation_history": [{"role": "user", "content": "My Zillow estimate is $800k"}],
            "stall_detected": True,
            "detected_stall_type": "zestimate",
            "qbq_attempted": True,
            "deep_motivation": "Retiring to Florida",
        }
        result = await bot._negotiation_discovery_node(state)
        assert result.get("qbq_attempted") is True
        assert result.get("deep_motivation") == "Retiring to Florida"

    def test_stall_detector_friendly_response_for_surface_objection(self):
        """StallDetector should have a friendly response for surface_objection."""
        from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector

        detector = StallDetector()
        response = detector.get_friendly_response("surface_objection")
        assert response is not None
        assert "price" in response.lower() or "feel right" in response.lower()
