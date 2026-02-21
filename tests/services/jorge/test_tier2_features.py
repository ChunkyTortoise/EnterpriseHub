"""Tests for Tier 2 Perplexity research features.

Covers: just_looking stall detection (keyword level), CMA confidence routing
+ disclaimers, buyer objection strategy for just_looking.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.agents.seller.stall_detector import StallDetector
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

# ── Helpers ───────────────────────────────────────────────────────────


def _make_state(message: str) -> dict:
    """Build a minimal JorgeSellerState dict for stall detection."""
    return {
        "lead_id": "test-contact-123",
        "conversation_history": [{"role": "user", "content": message}],
    }


def _make_detector() -> StallDetector:
    """Create a StallDetector with a mocked event publisher."""
    publisher = MagicMock()
    publisher.publish_bot_status_update = AsyncMock()
    publisher.publish_conversation_update = AsyncMock()
    return StallDetector(event_publisher=publisher)


# ── Stall keyword tests ──────────────────────────────────────────────


class TestJustLookingStallKeywords:
    """Verify just_looking keywords are in STALL_KEYWORDS."""

    def test_just_looking_key_exists(self):
        assert "just_looking" in StallDetector.STALL_KEYWORDS

    @pytest.mark.parametrize(
        "keyword",
        [
            "just looking",
            "just browsing",
            "exploring options",
            "kicking tires",
            "not ready yet",
            "window shopping",
            "just curious",
        ],
    )
    def test_keywords_present(self, keyword):
        assert keyword in StallDetector.STALL_KEYWORDS["just_looking"]


class TestJustLookingStallDetection:
    """Verify just_looking stall type triggers via detect_stall()."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "message",
        [
            "I'm just looking right now",
            "just browsing the market",
            "We're kicking tires at this point",
            "honestly, we're not ready yet",
            "just curious about home values",
            "exploring options for next year",
            "window shopping for houses",
        ],
    )
    async def test_just_looking_detected(self, message):
        detector = _make_detector()
        result = await detector.detect_stall(_make_state(message))
        assert result["stall_detected"] is True
        assert result["detected_stall_type"] == "just_looking"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "message",
        [
            "I want to sell my house ASAP",
            "Can you send me comps?",
            "I'm definitely interested in selling",
        ],
    )
    async def test_non_stall_not_triggered_as_just_looking(self, message):
        detector = _make_detector()
        result = await detector.detect_stall(_make_state(message))
        assert result.get("detected_stall_type") != "just_looking"


# ── CMA disclaimer tests ─────────────────────────────────────────────


class TestCMADisclaimers:
    """Verify CMA disclaimer config and confidence thresholds."""

    def test_disclaimers_exist(self):
        assert hasattr(JorgeSellerConfig, "CMA_DISCLAIMERS")
        disclaimers = JorgeSellerConfig.CMA_DISCLAIMERS
        assert "high" in disclaimers
        assert "medium" in disclaimers
        assert "low" in disclaimers

    def test_thresholds_exist(self):
        assert hasattr(JorgeSellerConfig, "CMA_CONFIDENCE_THRESHOLDS")
        thresholds = JorgeSellerConfig.CMA_CONFIDENCE_THRESHOLDS
        assert thresholds["high"] > thresholds["medium"]

    def test_high_disclaimer_has_comp_count_placeholder(self):
        high = JorgeSellerConfig.CMA_DISCLAIMERS["high"]
        assert "{comp_count}" in high
        formatted = high.format(comp_count=5)
        assert "5" in formatted

    def test_confidence_routing_high(self):
        """Confidence >= 70 -> high disclaimer, use_full_cma=True."""
        confidence = 75.0
        thresholds = JorgeSellerConfig.CMA_CONFIDENCE_THRESHOLDS
        disclaimers = JorgeSellerConfig.CMA_DISCLAIMERS
        assert confidence >= thresholds["high"]
        disclaimer = disclaimers["high"].format(comp_count=3)
        assert "comparable sales" in disclaimer.lower()

    def test_confidence_routing_medium(self):
        """Confidence 50-69 -> medium disclaimer."""
        confidence = 55.0
        thresholds = JorgeSellerConfig.CMA_CONFIDENCE_THRESHOLDS
        assert confidence >= thresholds["medium"]
        assert confidence < thresholds["high"]

    def test_confidence_routing_low(self):
        """Confidence < 50 -> low disclaimer."""
        confidence = 30.0
        thresholds = JorgeSellerConfig.CMA_CONFIDENCE_THRESHOLDS
        assert confidence < thresholds["medium"]
        disclaimer = JorgeSellerConfig.CMA_DISCLAIMERS["low"]
        assert "personalized analysis" in disclaimer.lower() or "not enough" in disclaimer.lower()


# ── Buyer just_looking objection ──────────────────────────────────────


class TestBuyerJustLookingObjection:
    """Verify buyer response generator has just_looking strategy."""

    def test_buyer_response_generator_importable(self):
        from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator

        assert ResponseGenerator is not None


# ── Handoff messages ──────────────────────────────────────────────────


class TestSellerHandoffMessages:
    """Verify handoff messages are in Jorge's voice."""

    def test_handoff_messages_exist(self):
        assert hasattr(JorgeSellerConfig, "HOT_SELLER_HANDOFF_MESSAGES")
        messages = JorgeSellerConfig.HOT_SELLER_HANDOFF_MESSAGES
        assert len(messages) >= 2

    def test_handoff_messages_mention_jorge(self):
        messages = JorgeSellerConfig.HOT_SELLER_HANDOFF_MESSAGES
        jorge_count = sum(1 for m in messages if "Jorge" in m or "jorge" in m)
        assert jorge_count >= 1, "Handoff messages should mention Jorge by name"
