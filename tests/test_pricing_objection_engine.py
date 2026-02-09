import pytest
pytestmark = pytest.mark.integration

"""Tests for the pricing objection engine.

Covers detection of all five objection types, graduated response escalation,
template filling, edge cases, and state management.
"""
import pytest

from ghl_real_estate_ai.services.jorge.pricing_objection_engine import (

@pytest.mark.unit
    ObjectionDetection,
    ObjectionType,
    PricingObjectionEngine,
    ResponseGraduation,
    RESPONSE_TEMPLATES,
    _SafeFormatDict,
)


@pytest.fixture
def engine():
    """Fresh engine instance for each test."""
    return PricingObjectionEngine()


# ── Detection: one test per objection type ────────────────────────────


class TestDetectLossAversion:
    def test_cant_sell_for_less(self, engine):
        result = engine.detect_objection("I can't sell for less than what I paid")
        assert result.detected is True
        assert result.objection_type == ObjectionType.LOSS_AVERSION
        assert result.confidence >= 0.8

    def test_lose_money(self, engine):
        result = engine.detect_objection("I don't want to lose money on this sale")
        assert result.detected is True
        assert result.objection_type == ObjectionType.LOSS_AVERSION

    def test_owe_more(self, engine):
        result = engine.detect_objection("We owe more than the house is worth")
        assert result.detected is True
        assert result.objection_type == ObjectionType.LOSS_AVERSION
        assert result.confidence == 0.9


class TestDetectAnchoring:
    def test_zillow(self, engine):
        result = engine.detect_objection("But Zillow says my home is worth $600K")
        assert result.detected is True
        assert result.objection_type == ObjectionType.ANCHORING
        assert result.confidence >= 0.8

    def test_zestimate(self, engine):
        result = engine.detect_objection("The Zestimate shows a higher value")
        assert result.detected is True
        assert result.objection_type == ObjectionType.ANCHORING
        assert result.confidence == 0.9

    def test_redfin(self, engine):
        result = engine.detect_objection("Redfin has it listed higher")
        assert result.detected is True
        assert result.objection_type == ObjectionType.ANCHORING


class TestDetectNeighborComp:
    def test_neighbor_sold(self, engine):
        result = engine.detect_objection("My neighbor sold their house for $700K")
        assert result.detected is True
        assert result.objection_type == ObjectionType.NEIGHBOR_COMP
        assert result.confidence >= 0.8

    def test_down_the_street(self, engine):
        result = engine.detect_objection("The house down the street sold for more")
        assert result.detected is True
        assert result.objection_type == ObjectionType.NEIGHBOR_COMP


class TestDetectMarketDenial:
    def test_market_will_bounce_back(self, engine):
        result = engine.detect_objection("The market will bounce back soon")
        assert result.detected is True
        assert result.objection_type == ObjectionType.MARKET_DENIAL
        assert result.confidence == 0.9

    def test_wait_for_market(self, engine):
        result = engine.detect_objection("I'd rather wait for the market to improve")
        assert result.detected is True
        assert result.objection_type == ObjectionType.MARKET_DENIAL

    def test_prices_will_go_up(self, engine):
        result = engine.detect_objection("Prices will go up next year for sure")
        assert result.detected is True
        assert result.objection_type == ObjectionType.MARKET_DENIAL


class TestDetectImprovementOvervalue:
    def test_put_money_into(self, engine):
        result = engine.detect_objection("I put $50K into the kitchen remodel")
        assert result.detected is True
        assert result.objection_type == ObjectionType.IMPROVEMENT_OVERVALUE
        assert result.confidence >= 0.8

    def test_spent_on_upgrades(self, engine):
        result = engine.detect_objection("We spent $30,000 on a new bathroom")
        assert result.detected is True
        assert result.objection_type == ObjectionType.IMPROVEMENT_OVERVALUE

    def test_new_kitchen(self, engine):
        result = engine.detect_objection("We just installed a new kitchen last year")
        assert result.detected is True
        assert result.objection_type == ObjectionType.IMPROVEMENT_OVERVALUE


# ── No detection on clean message ─────────────────────────────────────


class TestNoDetection:
    def test_clean_message(self, engine):
        result = engine.detect_objection("What is the process for listing my home?")
        assert result.detected is False
        assert result.objection_type is None
        assert result.confidence == 0.0
        assert result.matched_text == ""

    def test_empty_message(self, engine):
        result = engine.detect_objection("")
        assert result.detected is False


# ── Graduation escalation ─────────────────────────────────────────────


class TestGraduationEscalation:
    def test_four_level_escalation(self, engine):
        """First call = VALIDATE, second = DATA, third = SOCIAL_PROOF, fourth = MARKET_TEST."""
        contact_id = "contact_001"
        message = "I can't sell for less than I paid"

        expected_levels = [
            ResponseGraduation.VALIDATE,
            ResponseGraduation.DATA,
            ResponseGraduation.SOCIAL_PROOF,
            ResponseGraduation.MARKET_TEST,
        ]

        for expected_level in expected_levels:
            objection = engine.detect_objection(message)
            response = engine.generate_response(objection, contact_id)
            assert response is not None
            assert response.graduation_level == expected_level
            assert response.objection_type == ObjectionType.LOSS_AVERSION

    def test_stays_at_max_level(self, engine):
        """After reaching MARKET_TEST, subsequent calls stay there."""
        contact_id = "contact_002"
        message = "Zillow says it's worth more"

        # Exhaust all levels
        for _ in range(4):
            obj = engine.detect_objection(message)
            engine.generate_response(obj, contact_id)

        # Fifth call should still be MARKET_TEST
        obj = engine.detect_objection(message)
        response = engine.generate_response(obj, contact_id)
        assert response is not None
        assert response.graduation_level == ResponseGraduation.MARKET_TEST

    def test_next_graduation_field(self, engine):
        """next_graduation points to the upcoming level, or None at max."""
        contact_id = "contact_003"
        message = "The market will bounce back"

        obj = engine.detect_objection(message)
        resp1 = engine.generate_response(obj, contact_id)
        assert resp1 is not None
        assert resp1.next_graduation == ResponseGraduation.DATA

        obj = engine.detect_objection(message)
        resp2 = engine.generate_response(obj, contact_id)
        assert resp2 is not None
        assert resp2.next_graduation == ResponseGraduation.SOCIAL_PROOF

        obj = engine.detect_objection(message)
        resp3 = engine.generate_response(obj, contact_id)
        assert resp3 is not None
        assert resp3.next_graduation == ResponseGraduation.MARKET_TEST

        obj = engine.detect_objection(message)
        resp4 = engine.generate_response(obj, contact_id)
        assert resp4 is not None
        assert resp4.next_graduation is None  # Already at max

    def test_different_contacts_independent(self, engine):
        """Graduation state is tracked per contact."""
        message = "I can't sell for less than I paid"

        obj = engine.detect_objection(message)
        resp_a = engine.generate_response(obj, "contact_A")
        assert resp_a is not None
        assert resp_a.graduation_level == ResponseGraduation.VALIDATE

        # Advance contact_A to DATA
        obj = engine.detect_objection(message)
        resp_a2 = engine.generate_response(obj, "contact_A")
        assert resp_a2 is not None
        assert resp_a2.graduation_level == ResponseGraduation.DATA

        # contact_B should still start at VALIDATE
        obj = engine.detect_objection(message)
        resp_b = engine.generate_response(obj, "contact_B")
        assert resp_b is not None
        assert resp_b.graduation_level == ResponseGraduation.VALIDATE


# ── Template filling with market data ─────────────────────────────────


class TestMarketDataTemplates:
    def test_data_fills_template(self, engine):
        contact_id = "contact_fill"
        message = "I can't sell for less than I paid"

        # Advance to DATA level
        obj = engine.detect_objection(message)
        engine.generate_response(obj, contact_id)

        # Second call at DATA level with market data
        obj = engine.detect_objection(message)
        market_data = {"median_price": "$525,000", "gap_percent": "8"}
        response = engine.generate_response(obj, contact_id, market_data)

        assert response is not None
        assert "$525,000" in response.response_text
        assert "8%" in response.response_text

    def test_missing_keys_stay_as_placeholders(self, engine):
        contact_id = "contact_partial"
        message = "I can't sell for less than I paid"

        # Advance to DATA level
        obj = engine.detect_objection(message)
        engine.generate_response(obj, contact_id)

        # Only provide partial data
        obj = engine.detect_objection(message)
        response = engine.generate_response(obj, contact_id, {"median_price": "$500K"})

        assert response is not None
        assert "$500K" in response.response_text
        # Missing key should remain as placeholder
        assert "{gap_percent}" in response.response_text


# ── _SafeFormatDict ───────────────────────────────────────────────────


class TestSafeFormatDict:
    def test_present_key(self):
        d = _SafeFormatDict({"name": "Jorge"})
        assert "Hello {name}".format_map(d) == "Hello Jorge"

    def test_missing_key(self):
        d = _SafeFormatDict({})
        assert "Hello {name}".format_map(d) == "Hello {name}"

    def test_mixed_keys(self):
        d = _SafeFormatDict({"found": "yes"})
        result = "found={found}, missing={missing}".format_map(d)
        assert result == "found=yes, missing={missing}"


# ── Highest confidence wins ───────────────────────────────────────────


class TestHighestConfidenceWins:
    def test_picks_higher_confidence(self, engine):
        """When a message matches multiple types, highest confidence wins."""
        # "zestimate" is 0.9 for ANCHORING; "renovated" is 0.7 for IMPROVEMENT
        result = engine.detect_objection(
            "The Zestimate is higher and we renovated the place"
        )
        assert result.detected is True
        assert result.objection_type == ObjectionType.ANCHORING
        assert result.confidence == 0.9


# ── reset_contact ─────────────────────────────────────────────────────


class TestResetContact:
    def test_reset_clears_graduation(self, engine):
        contact_id = "contact_reset"
        message = "Zillow says it's worth more"

        # Advance to DATA
        obj = engine.detect_objection(message)
        engine.generate_response(obj, contact_id)

        assert engine.get_graduation_level(contact_id, ObjectionType.ANCHORING) == 1

        # Reset
        engine.reset_contact(contact_id)

        assert engine.get_graduation_level(contact_id, ObjectionType.ANCHORING) == 0

        # Next response should be VALIDATE again
        obj = engine.detect_objection(message)
        response = engine.generate_response(obj, contact_id)
        assert response is not None
        assert response.graduation_level == ResponseGraduation.VALIDATE

    def test_reset_nonexistent_contact_is_safe(self, engine):
        """Resetting a contact with no state should not raise."""
        engine.reset_contact("never_seen")  # No error


# ── generate_response returns None for no objection ──────────────────


class TestGenerateResponseNoObjection:
    def test_returns_none_when_not_detected(self, engine):
        no_objection = ObjectionDetection(detected=False)
        result = engine.generate_response(no_objection, "contact_x")
        assert result is None

    def test_returns_none_when_type_is_none(self, engine):
        partial = ObjectionDetection(detected=True, objection_type=None)
        result = engine.generate_response(partial, "contact_y")
        assert result is None


# ── All templates produce non-empty text ──────────────────────────────


class TestAllTemplatesNonEmpty:
    @pytest.mark.parametrize("objection_type", list(ObjectionType))
    def test_all_graduation_levels_have_text(self, engine, objection_type):
        """Every objection type at every graduation level produces non-empty response text."""
        for level in ResponseGraduation:
            template = RESPONSE_TEMPLATES.get(objection_type, {}).get(level, "")
            assert template, (
                f"Missing template for {objection_type.value} at {level.value}"
            )
            assert len(template) > 10, (
                f"Template too short for {objection_type.value} at {level.value}"
            )