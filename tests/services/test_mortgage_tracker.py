import pytest
pytestmark = pytest.mark.integration

"""Tests for MortgageTracker — mortgage pre-qualification tracking service.

Covers readiness assessment, referral creation, CRM tag updates,
lender recommendations, buying power estimation, and conversation templates.
"""

from unittest.mock import AsyncMock

import pytest

from ghl_real_estate_ai.services.mortgage_tracker import (

@pytest.mark.integration
    MortgageReadiness,
    MortgageTracker,
    Referral,
)


@pytest.fixture
def tracker():
    """MortgageTracker with no GHL client."""
    return MortgageTracker()


class TestMortgageTracker:
    """Tests for MortgageTracker service."""

    @pytest.mark.asyncio
    async def test_assess_readiness_pre_approved(self, tracker):
        """financing_status='pre_approved' returns status='pre_approved'."""
        buyer_data = {
            "financing_status": "pre_approved",
            "budget_max": 750000,
        }
        result = await tracker.assess_readiness(buyer_data)

        assert isinstance(result, MortgageReadiness)
        assert result.status == "pre_approved"
        assert result.estimated_buying_power == 750000
        assert result.recommended_action == "Start property search"
        assert result.lender_suggestions == []

    @pytest.mark.asyncio
    async def test_assess_readiness_needs_prequalification(self, tracker):
        """Unknown financing status returns needs_prequalification with lender suggestions."""
        buyer_data = {
            "financing_status": "unknown",
            "financial_readiness_score": 20,
        }
        result = await tracker.assess_readiness(buyer_data)

        assert result.status == "needs_prequalification"
        assert result.recommended_action == "Get pre-approved with a lender"
        assert len(result.lender_suggestions) == 3
        assert "Inland Empire Mortgage" in result.lender_suggestions

    @pytest.mark.asyncio
    async def test_create_referral_stores_id(self, tracker):
        """Referral created with valid ID and stored in tracker."""
        referral = await tracker.create_prequalification_referral(
            buyer_id="buyer_100",
            lender="Inland Empire Mortgage",
        )

        assert isinstance(referral, Referral)
        assert referral.referral_id.startswith("ref-")
        assert referral.buyer_id == "buyer_100"
        assert referral.lender == "Inland Empire Mortgage"
        assert referral.status == "pending"

        # Verify stored
        status = await tracker.check_status(referral.referral_id)
        assert status == "pending"

    @pytest.mark.asyncio
    async def test_crm_tag_updated_on_referral(self):
        """Mock ghl_client.add_tags called with 'Pre-Qualification-Sent'."""
        mock_ghl = AsyncMock()
        tracker = MortgageTracker(ghl_client=mock_ghl)

        await tracker.create_prequalification_referral(
            buyer_id="buyer_200",
            lender="SoCal Home Loans",
        )

        mock_ghl.add_tags.assert_awaited_once_with(
            "buyer_200", ["Pre-Qualification-Sent"]
        )

    def test_lender_recommendation_by_profile(self, tracker):
        """Luxury budget gets different lender than standard budget."""
        standard = tracker.get_lender_recommendation({"budget_max": 500000})
        luxury = tracker.get_lender_recommendation({"budget_max": 1500000})

        assert standard == "Inland Empire Mortgage"
        assert luxury == "Pacific Premier Lending"
        assert standard != luxury

    @pytest.mark.asyncio
    async def test_buying_power_estimation(self, tracker):
        """budget_max flows through as estimated_buying_power."""
        buyer_data = {
            "financing_status": "unknown",
            "budget_max": 600000,
        }
        result = await tracker.assess_readiness(buyer_data)

        assert result.estimated_buying_power == 600000

    def test_conversation_template_not_approved(self, tracker):
        """needs_prequalification template mentions 'pre-approved'."""
        template = tracker.get_conversation_template("needs_prequalification")

        assert "pre-approved" in template.lower()
        assert "lender" in template.lower()