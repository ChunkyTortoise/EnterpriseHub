"""
Tests for SellerIntentDecoder - seller-specific intent analysis.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.agents.seller_intent_decoder import SellerIntentDecoder
from ghl_real_estate_ai.models.lead_scoring import SellerIntentProfile


class TestSellerIntentDecoder:
    """Test suite for SellerIntentDecoder."""

    @pytest.fixture
    def decoder(self):
        return SellerIntentDecoder()

    def test_analyze_high_motivation_seller(self, decoder):
        """Test analysis of highly motivated seller."""
        history = [
            {"role": "user", "content": "I must sell my house, relocating for work next month"},
            {"role": "assistant", "content": "I understand. Let me help."},
            {"role": "user", "content": "Need to sell now, already bought a new place"},
        ]
        profile = decoder.analyze_seller("seller_001", history)
        assert isinstance(profile, SellerIntentProfile)
        assert profile.motivation_strength > 50
        assert profile.listing_urgency > 50
        assert profile.seller_temperature in ("hot", "warm")

    def test_analyze_cold_seller(self, decoder):
        """Test analysis of cold/browsing seller."""
        history = [
            {"role": "user", "content": "just curious about the market, no rush at all"},
            {"role": "assistant", "content": "Happy to share info."},
            {"role": "user", "content": "exploring options, maybe someday"},
        ]
        profile = decoder.analyze_seller("seller_002", history)
        assert profile.motivation_strength < 50
        assert profile.listing_urgency < 50
        assert profile.seller_temperature in ("cold", "ice_cold", "lukewarm")

    def test_condition_anxiety_scoring(self, decoder):
        """Test condition anxiety detection from conversation."""
        history = [
            {"role": "user", "content": "My house needs work, the roof is old and there are foundation issues"},
        ]
        profile = decoder.analyze_seller("seller_003", history)
        assert profile.condition_anxiety > 50

    def test_move_in_ready_low_anxiety(self, decoder):
        """Test low anxiety for move-in ready property."""
        history = [
            {"role": "user", "content": "The house is move-in ready, recently renovated and updated"},
        ]
        profile = decoder.analyze_seller("seller_004", history)
        assert profile.condition_anxiety < 30

    def test_valuation_confidence_with_appraisal(self, decoder):
        """Test high valuation confidence when appraisal mentioned."""
        history = [
            {"role": "user", "content": "I had it appraised last month for $850,000"},
        ]
        profile = decoder.analyze_seller("seller_005", history)
        assert profile.valuation_confidence > 50

    def test_price_flexibility_scoring(self, decoder):
        """Test price flexibility detection."""
        history = [
            {"role": "user", "content": "I'm flexible on price, open to offers, just want to sell"},
        ]
        profile = decoder.analyze_seller("seller_006", history)
        assert profile.price_flexibility > 60

    def test_next_qualification_step_motivation(self, decoder):
        """Test next step is motivation when motivation is low."""
        history = [
            {"role": "user", "content": "just seeing what it's worth"},
        ]
        profile = decoder.analyze_seller("seller_007", history)
        assert profile.next_qualification_step == "motivation"

    def test_key_insights_extraction(self, decoder):
        """Test key insights are properly extracted."""
        history = [
            {"role": "user", "content": "I need to sell now, house needs work, had it appraised"},
        ]
        profile = decoder.analyze_seller("seller_008", history)
        assert profile.key_insights.get("shows_urgency") is True
        assert profile.key_insights.get("mentions_condition") is True
        assert profile.key_insights.get("has_valuation_source") is True

    def test_empty_conversation_returns_default(self, decoder):
        """Test empty conversation returns default cold profile."""
        profile = decoder.analyze_seller("seller_009", [])
        assert profile.seller_temperature in ("cold", "lukewarm")
        assert profile.confidence_level == 0.0

    @pytest.mark.asyncio
    async def test_analyze_seller_with_ghl_no_client(self, decoder):
        """Test GHL analysis falls back without client."""
        history = [
            {"role": "user", "content": "I want to sell my house"},
        ]
        profile = await decoder.analyze_seller_with_ghl("contact_001", history)
        assert isinstance(profile, SellerIntentProfile)

    @pytest.mark.asyncio
    async def test_analyze_seller_with_ghl_boosts(self):
        """Test GHL tag boosts are applied."""
        mock_client = AsyncMock()
        mock_contact = MagicMock()
        mock_contact.tags = ["Hot-Seller", "Motivated-Seller"]
        mock_contact.custom_fields = {"property_condition": "good"}
        mock_contact.source = "website"
        mock_contact.created_at = None
        mock_contact.last_activity_at = None
        mock_contact.updated_at = None
        mock_client.get_contact.return_value = mock_contact

        decoder = SellerIntentDecoder(ghl_client=mock_client)
        history = [
            {"role": "user", "content": "I want to sell my house"},
        ]
        profile = await decoder.analyze_seller_with_ghl(
            "contact_002", history, ghl_contact=mock_contact
        )
        assert isinstance(profile, SellerIntentProfile)
        # GHL boosts should increase urgency and motivation
        base_profile = decoder.analyze_seller("contact_002", history)
        assert profile.listing_urgency >= base_profile.listing_urgency
        assert profile.motivation_strength >= base_profile.motivation_strength
