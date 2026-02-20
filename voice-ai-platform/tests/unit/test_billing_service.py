"""Unit tests for BillingService — real code paths, no placeholders."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from voice_ai.services.billing_service import BillingService, BillingTier


class TestBillingTierRates:
    """Test tier rate lookups."""

    def test_payg_rate(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.get_rate(BillingTier.PAYG) == 0.20

    def test_growth_rate(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.get_rate(BillingTier.GROWTH) == 0.15

    def test_enterprise_rate(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.get_rate(BillingTier.ENTERPRISE) == 0.12

    def test_whitelabel_rate(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.get_rate(BillingTier.WHITELABEL) == 0.10


class TestCalculateMinutes:
    """Test billable minutes calculation (ceil rounding)."""

    def test_zero_seconds(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(0) == 0

    def test_negative_seconds(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(-5) == 0

    def test_one_second_rounds_to_one_minute(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(1) == 1

    def test_60_seconds_equals_one_minute(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(60) == 1

    def test_61_seconds_rounds_to_two_minutes(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(61) == 2

    def test_5_minutes_exact(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(300) == 5

    def test_fractional_seconds(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_minutes(90.5) == 2


class TestCalculateCost:
    """Test cost calculation with various tiers and durations."""

    def test_payg_5_minutes(self):
        bs = BillingService(stripe_billing=AsyncMock())
        # 300 seconds = 5 minutes * $0.20 = $1.00
        assert bs.calculate_cost(300, BillingTier.PAYG) == 1.0

    def test_growth_10_minutes(self):
        bs = BillingService(stripe_billing=AsyncMock())
        # 600 seconds = 10 minutes * $0.15 = $1.50
        assert bs.calculate_cost(600, BillingTier.GROWTH) == 1.5

    def test_zero_duration_zero_cost(self):
        bs = BillingService(stripe_billing=AsyncMock())
        assert bs.calculate_cost(0, BillingTier.PAYG) == 0

    def test_partial_minute_rounds_up(self):
        bs = BillingService(stripe_billing=AsyncMock())
        # 61 seconds = 2 minutes * $0.20 = $0.40
        assert bs.calculate_cost(61, BillingTier.PAYG) == 0.40

    def test_whitelabel_long_call(self):
        bs = BillingService(stripe_billing=AsyncMock())
        # 3600 seconds = 60 minutes * $0.10 = $6.00
        assert bs.calculate_cost(3600, BillingTier.WHITELABEL) == 6.0


class TestReportCallUsage:
    """Test Stripe usage reporting."""

    @pytest.mark.asyncio
    async def test_reports_usage_to_stripe(self):
        mock_stripe = AsyncMock()
        mock_stripe.report_usage.return_value = {"id": "evt_123"}
        bs = BillingService(stripe_billing=mock_stripe)

        result = await bs.report_call_usage("tenant_1", 300, BillingTier.PAYG, "call_1")

        assert result == {"id": "evt_123"}
        mock_stripe.report_usage.assert_called_once()
        event = mock_stripe.report_usage.call_args[0][0]
        assert event.quantity == 5.0  # 5 minutes

    @pytest.mark.asyncio
    async def test_zero_duration_skips_billing(self):
        mock_stripe = AsyncMock()
        bs = BillingService(stripe_billing=mock_stripe)

        result = await bs.report_call_usage("tenant_1", 0)

        assert result == {}
        mock_stripe.report_usage.assert_not_called()

    @pytest.mark.asyncio
    async def test_reports_correct_tier_metadata(self):
        mock_stripe = AsyncMock()
        mock_stripe.report_usage.return_value = {}
        bs = BillingService(stripe_billing=mock_stripe)

        await bs.report_call_usage("t1", 120, BillingTier.ENTERPRISE, "c1")

        event = mock_stripe.report_usage.call_args[0][0]
        assert event.metadata["tier"] == "enterprise"
        assert event.metadata["rate_per_minute"] == 0.12


class TestCostBreakdown:
    """Test full cost breakdown calculation."""

    def test_breakdown_with_all_costs(self):
        bs = BillingService(stripe_billing=AsyncMock())
        bd = bs.get_cost_breakdown(
            duration_seconds=300,
            cost_stt=0.05,
            cost_tts=0.10,
            cost_llm=0.15,
            cost_telephony=0.02,
            tier=BillingTier.PAYG,
        )

        assert bd["revenue"] == 1.0  # 5 min * $0.20
        assert bd["cogs"]["stt"] == 0.05
        assert bd["cogs"]["tts"] == 0.10
        assert bd["cogs"]["llm"] == 0.15
        assert bd["cogs"]["telephony"] == 0.02
        assert bd["cogs"]["total"] == pytest.approx(0.32, abs=1e-4)
        assert bd["gross_profit"] == pytest.approx(0.68, abs=1e-4)
        assert bd["gross_margin"] == pytest.approx(0.68, abs=1e-4)

    def test_breakdown_zero_duration(self):
        bs = BillingService(stripe_billing=AsyncMock())
        bd = bs.get_cost_breakdown(duration_seconds=0)

        assert bd["revenue"] == 0
        assert bd["gross_margin"] == 0

    def test_breakdown_loss_scenario(self):
        bs = BillingService(stripe_billing=AsyncMock())
        bd = bs.get_cost_breakdown(
            duration_seconds=60,  # 1 min = $0.20 revenue
            cost_stt=0.10,
            cost_tts=0.10,
            cost_llm=0.10,
            tier=BillingTier.PAYG,
        )

        assert bd["gross_profit"] < 0  # Loss
        assert bd["gross_margin"] < 0
