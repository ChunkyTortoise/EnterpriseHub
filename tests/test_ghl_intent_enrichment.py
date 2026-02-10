"""
Tests for Phase 3 Loop 1: GHL Tags → Intent Enrichment.

Tests tag-based and custom field-based FRS boosting in analyze_lead_with_ghl().
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.agents.intent_decoder import (
    CUSTOM_FIELD_BOOST_MAP,
    MAX_BOOST_CAP,
    TAG_BOOST_MAP,
    LeadIntentDecoder,
)
from ghl_real_estate_ai.services.enhanced_ghl_client import GHLContact


@pytest.fixture
def decoder():
    """Create a LeadIntentDecoder instance for testing."""
    return LeadIntentDecoder(ghl_client=None, industry_config=None)


@pytest.fixture
def base_conversation():
    """Standard conversation history for testing."""
    return [
        {"role": "user", "content": "I'm thinking about selling my home soon."},
        {"role": "assistant", "content": "Great! Let's discuss your timeline."},
    ]


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client that returns configurable contact data."""
    client = MagicMock()
    client.get_contact = AsyncMock()
    return client


class TestTagBasedBoosting:
    """Test tag-based FRS boosting."""

    @pytest.mark.asyncio
    async def test_urgent_seller_tag_boost(self, decoder, base_conversation):
        """Urgent-Seller tag should boost FRS by +15."""
        contact = GHLContact(
            id="test-001",
            tags=["Urgent-Seller"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-001",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base FRS from conversation is ~50, boost by +15
        assert profile.frs.total_score >= 60, "Urgent-Seller tag should boost FRS by ~15"

    @pytest.mark.asyncio
    async def test_pre_approved_buyer_tag_boost(self, decoder, base_conversation):
        """Pre-Approved-Buyer tag should boost FRS by +20."""
        contact = GHLContact(
            id="test-002",
            tags=["Pre-Approved-Buyer"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-002",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base FRS from conversation is ~50, boost by +20
        assert profile.frs.total_score >= 65, "Pre-Approved-Buyer tag should boost FRS by ~20"

    @pytest.mark.asyncio
    async def test_hot_lead_tag_boost(self, decoder, base_conversation):
        """Hot-Lead tag should boost FRS by +15."""
        contact = GHLContact(
            id="test-003",
            tags=["Hot-Lead"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-003",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 60, "Hot-Lead tag should boost FRS by ~15"

    @pytest.mark.asyncio
    async def test_warm_lead_tag_boost(self, decoder, base_conversation):
        """Warm-Lead tag should boost FRS by +10."""
        contact = GHLContact(
            id="test-004",
            tags=["Warm-Lead"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-004",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 55, "Warm-Lead tag should boost FRS by ~10"

    @pytest.mark.asyncio
    async def test_cold_lead_tag_penalty(self, decoder, base_conversation):
        """Cold-Lead tag should reduce FRS by -5."""
        # Use old lead to avoid fresh lead boost
        contact = GHLContact(
            id="test-005",
            tags=["Cold-Lead"],
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-005",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base FRS ~50, penalty -5 (no age boost)
        assert profile.frs.total_score <= 50, "Cold-Lead tag should reduce FRS"

    @pytest.mark.asyncio
    async def test_investor_seller_tag_boost(self, decoder, base_conversation):
        """Investor-Seller tag should boost FRS by +10."""
        contact = GHLContact(
            id="test-006",
            tags=["Investor-Seller"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-006",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 55, "Investor-Seller tag should boost FRS by ~10"

    @pytest.mark.asyncio
    async def test_distressed_seller_tag_boost(self, decoder, base_conversation):
        """Distressed-Seller tag should boost FRS by +12."""
        contact = GHLContact(
            id="test-007",
            tags=["Distressed-Seller"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-007",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 58, "Distressed-Seller tag should boost FRS by ~12"

    @pytest.mark.asyncio
    async def test_do_not_contact_tag_penalty(self, decoder, base_conversation):
        """Do-Not-Contact tag should severely reduce FRS by -20."""
        # Use old lead to avoid fresh lead boost
        contact = GHLContact(
            id="test-008",
            tags=["Do-Not-Contact"],
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-008",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base FRS ~50, penalty -20 (no age boost)
        assert profile.frs.total_score <= 35, "Do-Not-Contact tag should severely reduce FRS"

    @pytest.mark.asyncio
    async def test_multiple_tags_accumulate(self, decoder, base_conversation):
        """Multiple tags should accumulate boosts."""
        contact = GHLContact(
            id="test-009",
            tags=["Hot-Lead", "Investor-Seller", "Referral"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-009",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, Hot-Lead +15, Investor-Seller +10, Referral +5 = ~80
        assert profile.frs.total_score >= 75, "Multiple tags should accumulate boosts"

    @pytest.mark.asyncio
    async def test_case_insensitive_tag_matching(self, decoder, base_conversation):
        """Tag matching should be case-insensitive."""
        contact = GHLContact(
            id="test-010",
            tags=["URGENT-SELLER", "hot-lead", "Warm-Lead"],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-010",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # All tags should be recognized despite varying case
        assert profile.frs.total_score >= 70, "Tag matching should be case-insensitive"


class TestCustomFieldBoosting:
    """Test custom field-based FRS boosting."""

    @pytest.mark.asyncio
    async def test_pre_approval_status_approved(self, decoder, base_conversation):
        """Pre-approval status 'approved' should boost FRS by +15."""
        contact = GHLContact(
            id="test-011",
            custom_fields={"pre_approval_status": "approved"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-011",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, boost +15
        assert profile.frs.total_score >= 60, "Pre-approval 'approved' should boost FRS by ~15"

    @pytest.mark.asyncio
    async def test_pre_approval_status_pre_approved(self, decoder, base_conversation):
        """Pre-approval status 'pre-approved' should boost FRS by +15."""
        contact = GHLContact(
            id="test-012",
            custom_fields={"pre_approval_status": "pre-approved"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-012",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 60, "Pre-approval 'pre-approved' should boost FRS by ~15"

    @pytest.mark.asyncio
    async def test_budget_above_threshold(self, decoder, base_conversation):
        """Budget > $500k should boost FRS by +10."""
        contact = GHLContact(
            id="test-013",
            custom_fields={"budget": "750000"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-013",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, boost +10
        assert profile.frs.total_score >= 55, "Budget > $500k should boost FRS by ~10"

    @pytest.mark.asyncio
    async def test_budget_below_threshold_no_boost(self, decoder, base_conversation):
        """Budget < $500k should not boost FRS."""
        contact = GHLContact(
            id="test-014",
            custom_fields={"budget": "300000"},
            created_at=datetime.now(timezone.utc),
        )

        profile_with_low_budget = await decoder.analyze_lead_with_ghl(
            contact_id="test-014",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Get baseline without budget field
        contact_no_budget = GHLContact(
            id="test-014-baseline",
            custom_fields={},
            created_at=datetime.now(timezone.utc),
        )
        profile_no_budget = await decoder.analyze_lead_with_ghl(
            contact_id="test-014-baseline",
            conversation_history=base_conversation,
            ghl_contact=contact_no_budget,
        )

        # Low budget should not boost beyond baseline
        assert (
            profile_with_low_budget.frs.total_score <= profile_no_budget.frs.total_score + 5
        ), "Budget < $500k should not boost FRS"

    @pytest.mark.asyncio
    async def test_timeline_immediate(self, decoder, base_conversation):
        """Timeline 'immediate' should boost FRS by +12."""
        contact = GHLContact(
            id="test-015",
            custom_fields={"timeline": "immediate"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-015",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, boost +12
        assert profile.frs.total_score >= 58, "Timeline 'immediate' should boost FRS by ~12"

    @pytest.mark.asyncio
    async def test_timeline_asap(self, decoder, base_conversation):
        """Timeline 'asap' should boost FRS by +12."""
        contact = GHLContact(
            id="test-016",
            custom_fields={"timeline": "asap"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-016",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile.frs.total_score >= 58, "Timeline 'asap' should boost FRS by ~12"

    @pytest.mark.asyncio
    async def test_property_type_investment(self, decoder, base_conversation):
        """Property type 'investment' should boost FRS by +8."""
        contact = GHLContact(
            id="test-017",
            custom_fields={"property_type": "investment"},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-017",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, boost +8
        assert profile.frs.total_score >= 55, "Property type 'investment' should boost FRS by ~8"

    @pytest.mark.asyncio
    async def test_multiple_custom_fields_accumulate(self, decoder, base_conversation):
        """Multiple custom fields should accumulate boosts."""
        contact = GHLContact(
            id="test-018",
            custom_fields={
                "pre_approval_status": "approved",
                "budget": "800000",
                "timeline": "immediate",
                "property_type": "investment",
            },
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-018",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, pre-approval +15, budget +10, timeline +12, property_type +8
        # Total expected boost: +45, but capped at +30 = ~80
        assert profile.frs.total_score >= 75, "Multiple custom fields should accumulate boosts"


class TestBoostCapping:
    """Test that boost cap prevents over-inflation."""

    @pytest.mark.asyncio
    async def test_boost_cap_enforced(self, decoder, base_conversation):
        """Total FRS boost should be capped at MAX_BOOST_CAP (+30)."""
        # Create contact with tags and fields that would exceed cap
        contact = GHLContact(
            id="test-019",
            tags=["Pre-Approved-Buyer", "Hot-Lead", "Urgent-Seller", "Investor-Seller"],
            custom_fields={
                "pre_approval_status": "approved",
                "budget": "1000000",
                "timeline": "immediate",
            },
            created_at=datetime.now(timezone.utc) - timedelta(days=2),  # Fresh lead +10
        )

        # Without conversation analysis, this would be:
        # Tags: Pre-Approved-Buyer +20, Hot-Lead +15, Urgent-Seller +15, Investor-Seller +10 = +60
        # Fields: pre_approval +15, budget +10, timeline +12 = +37
        # Age: fresh +10
        # Total uncapped: +107, should be capped to +30

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-019",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, capped boost +30 = max 80
        assert profile.frs.total_score <= 85, "FRS boost should be capped"
        assert profile.frs.total_score >= 70, "Capped boost should still be significant"

    @pytest.mark.asyncio
    async def test_no_cap_when_below_limit(self, decoder, base_conversation):
        """Boosts below cap should not be affected."""
        contact = GHLContact(
            id="test-020",
            tags=["Hot-Lead"],
            custom_fields={"timeline": "immediate"},
            created_at=datetime.now(timezone.utc),
        )

        # Hot-Lead +15, timeline +12 = +27 (below cap)
        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-020",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Should get full boost
        assert 70 <= profile.frs.total_score <= 85, "Below-cap boosts should be applied fully"


class TestLeadAgeFactors:
    """Test lead age influence on FRS."""

    @pytest.mark.asyncio
    async def test_fresh_lead_boost(self, decoder, base_conversation):
        """Lead < 7 days old should boost FRS by +10."""
        contact = GHLContact(
            id="test-021",
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-021",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, fresh lead +10
        assert profile.frs.total_score >= 55, "Fresh lead should boost FRS by ~10"

    @pytest.mark.asyncio
    async def test_stale_lead_penalty(self, decoder, base_conversation):
        """Lead > 90 days old should reduce FRS by -10."""
        contact = GHLContact(
            id="test-022",
            created_at=datetime.now(timezone.utc) - timedelta(days=120),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-022",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base ~50, stale lead -10
        assert profile.frs.total_score <= 45, "Stale lead should reduce FRS"


class TestEngagementRecency:
    """Test engagement recency influence on PCS."""

    @pytest.mark.asyncio
    async def test_recent_engagement_boost(self, decoder, base_conversation):
        """Engagement < 3 days should boost PCS by +10."""
        contact = GHLContact(
            id="test-023",
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=1),
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-023",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # Base PCS ~35, boost +10 = ~45
        assert profile.pcs.total_score >= 40, "Recent engagement should boost PCS by ~10"
        assert profile.pcs.total_score <= 55, "PCS boost should be reasonable"

    @pytest.mark.asyncio
    async def test_disengaged_penalty(self, decoder, base_conversation):
        """Engagement > 30 days should reduce PCS by -15."""
        contact = GHLContact(
            id="test-024",
            last_activity_at=datetime.now(timezone.utc) - timedelta(days=60),
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-024",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        # PCS should be reduced
        assert profile.pcs.total_score <= 50, "Disengaged lead should reduce PCS"


class TestFallbackBehavior:
    """Test fallback to conversation-only analysis when GHL data unavailable."""

    @pytest.mark.asyncio
    async def test_no_ghl_contact_fallback(self, decoder, base_conversation):
        """Should fall back to conversation-only analysis if no GHL contact."""
        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-025",
            conversation_history=base_conversation,
            ghl_contact=None,
        )

        # Should still return valid profile
        assert profile is not None
        assert profile.frs.total_score > 0
        assert profile.lead_id == "test-025"

    @pytest.mark.asyncio
    async def test_ghl_client_fetch_failure(self, decoder, base_conversation, mock_ghl_client):
        """Should fall back if GHL client fails to fetch contact."""
        mock_ghl_client.get_contact.side_effect = Exception("Network error")
        decoder.ghl_client = mock_ghl_client

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-026",
            conversation_history=base_conversation,
        )

        # Should still return valid profile
        assert profile is not None
        assert profile.frs.total_score > 0


class TestConfigurationMaps:
    """Test configuration map structure and completeness."""

    def test_tag_boost_map_structure(self):
        """TAG_BOOST_MAP should contain expected tags."""
        expected_tags = [
            "urgent-seller",
            "pre-approved-buyer",
            "hot-lead",
            "warm-lead",
            "cold-lead",
            "investor-seller",
            "distressed-seller",
            "referral",
            "do-not-contact",
            "dnc",
        ]

        for tag in expected_tags:
            assert tag in TAG_BOOST_MAP, f"TAG_BOOST_MAP missing expected tag: {tag}"
            assert isinstance(TAG_BOOST_MAP[tag], (int, float)), f"TAG_BOOST_MAP[{tag}] should be numeric"

    def test_custom_field_boost_map_structure(self):
        """CUSTOM_FIELD_BOOST_MAP should contain expected fields."""
        expected_fields = ["pre_approval_status", "budget", "timeline", "property_type"]

        for field in expected_fields:
            assert field in CUSTOM_FIELD_BOOST_MAP, f"CUSTOM_FIELD_BOOST_MAP missing expected field: {field}"
            config = CUSTOM_FIELD_BOOST_MAP[field]
            assert "boost" in config, f"Field {field} config missing 'boost' key"
            assert isinstance(config["boost"], (int, float)), f"Field {field} boost should be numeric"

    def test_max_boost_cap_defined(self):
        """MAX_BOOST_CAP should be defined and reasonable."""
        assert MAX_BOOST_CAP == 30, "MAX_BOOST_CAP should be 30 per specification"
        assert isinstance(MAX_BOOST_CAP, (int, float)), "MAX_BOOST_CAP should be numeric"


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_tags_list(self, decoder, base_conversation):
        """Empty tags list should not cause errors."""
        contact = GHLContact(
            id="test-027",
            tags=[],
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-027",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile is not None
        assert profile.frs.total_score > 0

    @pytest.mark.asyncio
    async def test_empty_custom_fields(self, decoder, base_conversation):
        """Empty custom fields should not cause errors."""
        contact = GHLContact(
            id="test-028",
            custom_fields={},
            created_at=datetime.now(timezone.utc),
        )

        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-028",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile is not None
        assert profile.frs.total_score > 0

    @pytest.mark.asyncio
    async def test_invalid_budget_value(self, decoder, base_conversation):
        """Invalid budget value should be handled gracefully."""
        contact = GHLContact(
            id="test-029",
            custom_fields={"budget": "not-a-number"},
            created_at=datetime.now(timezone.utc),
        )

        # Should not raise exception
        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-029",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile is not None

    @pytest.mark.asyncio
    async def test_missing_timestamps(self, decoder, base_conversation):
        """Missing timestamps should be handled gracefully."""
        contact = GHLContact(
            id="test-030",
            created_at=None,
            last_activity_at=None,
        )

        # Should not raise exception
        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-030",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile is not None
        assert profile.frs.total_score > 0

    @pytest.mark.asyncio
    async def test_timezone_naive_timestamps(self, decoder, base_conversation):
        """Timezone-naive timestamps should be handled by adding UTC."""
        contact = GHLContact(
            id="test-031",
            created_at=datetime.now(),  # No timezone
            last_activity_at=datetime.now(),  # No timezone
        )

        # Should not raise exception
        profile = await decoder.analyze_lead_with_ghl(
            contact_id="test-031",
            conversation_history=base_conversation,
            ghl_contact=contact,
        )

        assert profile is not None
