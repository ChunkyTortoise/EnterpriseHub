"""
Unit tests for three buyer bot fixes (commit ac731f52):

1. extract_budget_range — skip plain-number amounts < 100 (bedroom counts)
2. BuyerIntentDecoder._score_urgency / _score_financial_readiness — buyer timeline
   markers loaded from real_estate_rancho.yaml so pre-approved+60-day buyer scores
   buying_motivation >= 50 (was 37.5 before the YAML fix)
3. BuyerWorkflowService.schedule_next_action — hot-path response injection when
   next_action == "schedule_property_tour" and response_content is empty
"""

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── Helpers ──────────────────────────────────────────────────────────────────


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ─────────────────────────────────────────────────────────────────────────────
# 1. extract_budget_range
# ─────────────────────────────────────────────────────────────────────────────


class TestExtractBudgetRange:
    """Tests for the bedroom-count false-positive fix in extract_budget_range."""

    @pytest.fixture
    def cfg(self):
        from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
        return BuyerBudgetConfig()

    def _run(self, history, cfg=None):
        from ghl_real_estate_ai.agents.buyer.utils import extract_budget_range
        return run(extract_budget_range(history, cfg))

    # ── regression: the bug case ─────────────────────────────────────────────

    def test_bedroom_count_not_treated_as_budget(self, cfg):
        """'3-bedroom house around 450k' must not yield min=3."""
        history = [{"role": "user", "content": "I want a 3-bedroom house around 450k"}]
        result = self._run(history, cfg)
        assert result is not None
        assert result["min"] >= 1000, f"min={result['min']} looks like a bedroom count"
        assert result["max"] == 450_000

    def test_bathroom_count_not_treated_as_budget(self, cfg):
        """'2 bath house priced around 500k' must not yield min=2."""
        history = [{"role": "user", "content": "I need a 2 bath house priced around 500k"}]
        result = self._run(history, cfg)
        assert result is not None
        assert result["min"] >= 1000

    def test_small_year_digits_skipped(self, cfg):
        """Single-digit or two-digit numbers (years, counts) should be ignored."""
        history = [{"role": "user", "content": "I've been renting for 5 years, budget $600k"}]
        result = self._run(history, cfg)
        assert result is not None
        assert result["max"] == 600_000
        assert result["min"] >= 1000

    # ── happy paths ───────────────────────────────────────────────────────────

    def test_dollar_k_suffix_parsed(self, cfg):
        history = [{"role": "user", "content": "My budget is $450k to $550k"}]
        result = self._run(history, cfg)
        assert result == {"min": 450_000, "max": 550_000}

    def test_plain_range_without_dollar(self, cfg):
        """'450 to 500' should be treated as 450k–500k (auto-multiply)."""
        history = [{"role": "user", "content": "somewhere between 450 and 500"}]
        result = self._run(history, cfg)
        assert result is not None
        assert result["min"] == 450_000
        assert result["max"] == 500_000

    def test_single_amount_creates_range(self, cfg):
        history = [{"role": "user", "content": "budget is $500k"}]
        result = self._run(history, cfg)
        assert result is not None
        assert result["max"] == 500_000
        assert result["min"] < result["max"]

    def test_empty_history_returns_none(self, cfg):
        assert self._run([], cfg) is None

    def test_no_amounts_returns_none(self, cfg):
        history = [{"role": "user", "content": "I want a nice house"}]
        assert self._run(history, cfg) is None


# ─────────────────────────────────────────────────────────────────────────────
# 2. BuyerIntentDecoder scoring with updated timeline markers
# ─────────────────────────────────────────────────────────────────────────────


class TestBuyerIntentDecoderScoring:
    """Urgency and motivation scoring with buyer-oriented timeline markers."""

    @pytest.fixture
    def decoder(self):
        from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
        from ghl_real_estate_ai.config.industry_config import IndustryConfig
        cfg = IndustryConfig.default_real_estate()
        return BuyerIntentDecoder(industry_config=cfg)

    # ── financial readiness ───────────────────────────────────────────────────

    def test_pre_approved_scores_50(self, decoder):
        score = decoder._score_financial_readiness("i am pre-approved for 550k")
        assert score == 50  # base 30 + 20

    def test_cash_buyer_scores_high(self, decoder):
        score = decoder._score_financial_readiness("i am a cash buyer")
        assert score >= 50

    def test_no_financing_signal_base_only(self, decoder):
        score = decoder._score_financial_readiness("i just want to see some homes")
        assert score == 30  # base only

    # ── urgency scoring ───────────────────────────────────────────────────────

    def test_within_60_days_is_immediate_urgency(self, decoder):
        """'within 60 days' must match immediate_urgency → score well above base."""
        score = decoder._score_urgency("i need to move within 60 days")
        assert score >= 50, f"Expected >=50 got {score}"

    def test_want_to_move_is_medium_urgency(self, decoder):
        """'want to move' must match medium_urgency."""
        score = decoder._score_urgency("i want to move to a bigger place")
        assert score > 25, f"Expected >25 (base) got {score}"

    def test_lease_ending_is_immediate_urgency(self, decoder):
        score = decoder._score_urgency("my lease ending next month")
        assert score >= 50

    def test_just_looking_penalises_urgency(self, decoder):
        # Avoid words in immediate_urgency (e.g. "urgent") which would boost score.
        score = decoder._score_urgency("just browsing homes, no timeline in mind")
        assert score <= 25, f"Cold-buyer urgency should stay at base; got {score}"

    def test_30_days_immediate(self, decoder):
        score = decoder._score_urgency("need to be out in 30 days")
        assert score >= 50

    # ── buying_motivation regression ─────────────────────────────────────────

    def test_preapproved_60days_motivation_above_50(self, decoder):
        """
        Regression: before fix, pre-approved + 60-day buyer scored motivation=37.5
        because 'want to move within 60 days' matched nothing in the seller-oriented
        YAML markers. Must now be >= 50 so is_qualified=True.
        """
        text = "i am pre-approved and want to move within 60 days"
        fr = decoder._score_financial_readiness(text)
        urgency = decoder._score_urgency(text)
        buying_motivation = (fr + urgency) / 2
        assert buying_motivation >= 50, (
            f"Motivation {buying_motivation} < 50 (fr={fr}, urgency={urgency}). "
            "is_qualified would be False for a hot buyer."
        )

    def test_cold_buyer_motivation_stays_low(self, decoder):
        text = "just browsing, not sure when i might buy"
        fr = decoder._score_financial_readiness(text)
        urgency = decoder._score_urgency(text)
        motivation = (fr + urgency) / 2
        assert motivation < 50


# ─────────────────────────────────────────────────────────────────────────────
# 3. BuyerWorkflowService.schedule_next_action hot-path response injection
# ─────────────────────────────────────────────────────────────────────────────


class TestHotPathAppointmentResponse:
    """schedule_next_action must inject appointment message for hot buyers."""

    @pytest.fixture
    def service(self):
        from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService
        from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig

        mock_publisher = MagicMock()
        mock_publisher.publish_buyer_follow_up_scheduled = AsyncMock()

        cfg = BuyerBudgetConfig()
        svc = BuyerWorkflowService(event_publisher=mock_publisher, budget_config=cfg)
        return svc

    def _hot_state(self, name="Alex", response_content=""):
        return {
            "buyer_id": "hot-001",
            "buyer_name": name,
            "financial_readiness_score": 80,  # >= HOT_THRESHOLD (75)
            "days_since_start": 0,
            "response_content": response_content,
        }

    def test_hot_buyer_gets_appointment_response(self, service):
        result = run(service.schedule_next_action(self._hot_state()))
        assert result["next_action"] == "schedule_property_tour"
        assert result.get("response_content"), "Hot-path must inject a response"
        assert "tours" in result["response_content"].lower() or "morning" in result["response_content"].lower()

    def test_hot_buyer_step_set_to_appointment(self, service):
        result = run(service.schedule_next_action(self._hot_state()))
        assert result.get("current_qualification_step") == "appointment"

    def test_hot_buyer_temperature_set_to_hot(self, service):
        result = run(service.schedule_next_action(self._hot_state()))
        assert result.get("buyer_temperature") == "hot"

    def test_hot_buyer_name_included_in_response(self, service):
        result = run(service.schedule_next_action(self._hot_state(name="Jordan")))
        assert "Jordan" in result["response_content"]

    def test_no_override_when_response_already_set(self, service):
        """If generate_buyer_response already set content, don't overwrite it."""
        existing = "Great, let me show you some options."
        result = run(service.schedule_next_action(self._hot_state(response_content=existing)))
        # next_action is still property_tour, but response must remain the existing one
        assert result["next_action"] == "schedule_property_tour"
        assert result.get("response_content") == existing or not result.get("response_content")

    def test_warm_buyer_no_appointment_message(self, service):
        state = {
            "buyer_id": "warm-001",
            "buyer_name": "Sam",
            "financial_readiness_score": 60,  # warm, not hot
            "days_since_start": 0,
            "response_content": "",
        }
        result = run(service.schedule_next_action(state))
        # Warm buyers get send_property_updates, not schedule_property_tour
        assert result["next_action"] == "send_property_updates"
        # No appointment injection for warm
        assert result.get("current_qualification_step") != "appointment"

    def test_follow_up_scheduled_flag_set(self, service):
        result = run(service.schedule_next_action(self._hot_state()))
        assert result.get("follow_up_scheduled") is True
