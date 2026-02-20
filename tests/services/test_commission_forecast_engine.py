import pytest

pytestmark = pytest.mark.integration

"""Tests for Commission Forecasting Engine."""

import pytest

from ghl_real_estate_ai.services.commission_forecast_engine import (
    LUXURY_COMMISSION_RATE,
    LUXURY_THRESHOLD,
    SEASONAL_FACTORS,
    CommissionForecastEngine,
    DealStage,
)


@pytest.fixture
def engine():
    return CommissionForecastEngine()


@pytest.fixture
def sample_pipeline():
    return [
        {
            "deal_id": "d1",
            "contact_name": "Sarah",
            "property_value": 800_000,
            "stage": "qualified",
            "expected_close_month": 3,
            "deal_type": "buyer",
        },
        {
            "deal_id": "d2",
            "contact_name": "Mike",
            "property_value": 650_000,
            "stage": "showing",
            "expected_close_month": 3,
            "deal_type": "seller",
        },
        {
            "deal_id": "d3",
            "contact_name": "Jen",
            "property_value": 1_300_000,
            "stage": "offer",
            "expected_close_month": 4,
            "deal_type": "buyer",
        },
        {
            "deal_id": "d4",
            "contact_name": "Tom",
            "property_value": 550_000,
            "stage": "prospect",
            "expected_close_month": 5,
            "deal_type": "seller",
        },
        {
            "deal_id": "d5",
            "contact_name": "Lisa",
            "property_value": 720_000,
            "stage": "under_contract",
            "expected_close_month": 3,
            "deal_type": "buyer",
        },
    ]


# -------------------------------------------------------------------------
# Revenue forecasting
# -------------------------------------------------------------------------


class TestRevenueForecast:
    @pytest.mark.asyncio
    async def test_forecast_returns_result(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        assert forecast.deal_count == 5
        assert forecast.total_expected > 0
        assert forecast.total_weighted > 0

    @pytest.mark.asyncio
    async def test_weighted_less_than_expected(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        # Weighted should be less since not all deals close
        assert forecast.total_weighted <= forecast.total_expected

    @pytest.mark.asyncio
    async def test_monthly_breakdown_count(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=6, current_month=1)
        assert len(forecast.monthly_forecasts) == 6

    @pytest.mark.asyncio
    async def test_seasonal_factors_applied(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        for mf in forecast.monthly_forecasts:
            assert mf.seasonal_factor == SEASONAL_FACTORS[mf.month]

    @pytest.mark.asyncio
    async def test_confidence_interval(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        for mf in forecast.monthly_forecasts:
            if mf.weighted_pipeline > 0:
                assert mf.confidence_low < mf.weighted_pipeline
                assert mf.confidence_high > mf.weighted_pipeline

    @pytest.mark.asyncio
    async def test_empty_pipeline(self, engine):
        forecast = await engine.forecast_revenue([], horizon_months=3, current_month=1)
        assert forecast.deal_count == 0
        assert forecast.total_expected == 0

    @pytest.mark.asyncio
    async def test_luxury_commission_applied(self, engine):
        luxury_pipeline = [
            {
                "deal_id": "lux",
                "contact_name": "VIP",
                "property_value": 1_500_000,
                "stage": "under_contract",
                "expected_close_month": 4,
            }
        ]
        forecast = await engine.forecast_revenue(luxury_pipeline, horizon_months=1, current_month=4)
        # Luxury rate: 3% of 1.5M = 45,000
        expected_commission = 1_500_000 * LUXURY_COMMISSION_RATE
        assert forecast.total_expected == expected_commission


# -------------------------------------------------------------------------
# Monte Carlo simulation
# -------------------------------------------------------------------------


class TestMonteCarlo:
    @pytest.mark.asyncio
    async def test_simulation_runs(self, engine, sample_pipeline):
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=500)
        assert mc.simulations == 500
        assert mc.mean_revenue > 0

    @pytest.mark.asyncio
    async def test_percentile_ordering(self, engine, sample_pipeline):
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=500)
        assert mc.worst_case <= mc.percentile_10
        assert mc.percentile_10 <= mc.percentile_25
        assert mc.percentile_25 <= mc.median_revenue
        assert mc.median_revenue <= mc.percentile_75
        assert mc.percentile_75 <= mc.percentile_90
        assert mc.percentile_90 <= mc.best_case

    @pytest.mark.asyncio
    async def test_probability_above_target(self, engine, sample_pipeline):
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=500, target_revenue=1000)
        assert 0 <= mc.probability_above_target <= 1

    @pytest.mark.asyncio
    async def test_zero_target_no_probability(self, engine, sample_pipeline):
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=100, target_revenue=0)
        assert mc.probability_above_target == 0.0

    @pytest.mark.asyncio
    async def test_std_dev_positive(self, engine, sample_pipeline):
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=500)
        assert mc.std_dev >= 0


# -------------------------------------------------------------------------
# Executive summary
# -------------------------------------------------------------------------


class TestExecutiveSummary:
    @pytest.mark.asyncio
    async def test_summary_generated(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        summary = await engine.generate_executive_summary(forecast)
        assert summary.total_pipeline_value > 0
        assert summary.forecast_confidence in ("high", "moderate", "low")
        assert summary.recommendation

    @pytest.mark.asyncio
    async def test_summary_with_monte_carlo(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        mc = await engine.monte_carlo_simulation(sample_pipeline, simulations=200)
        summary = await engine.generate_executive_summary(forecast, mc)
        assert summary.expected_commission > 0

    @pytest.mark.asyncio
    async def test_risk_factors_identified(self, engine):
        # Small pipeline with low-season months
        small = [
            {
                "deal_id": "s1",
                "contact_name": "Solo",
                "property_value": 600_000,
                "stage": "prospect",
                "expected_close_month": 12,
            }
        ]
        forecast = await engine.forecast_revenue(small, horizon_months=3, current_month=11)
        summary = await engine.generate_executive_summary(forecast)
        assert len(summary.risk_factors) > 0

    @pytest.mark.asyncio
    async def test_opportunities_for_peak_season(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        summary = await engine.generate_executive_summary(forecast)
        # March-May is peak season
        assert len(summary.opportunities) > 0

    @pytest.mark.asyncio
    async def test_monthly_breakdown(self, engine, sample_pipeline):
        forecast = await engine.forecast_revenue(sample_pipeline, horizon_months=3, current_month=3)
        summary = await engine.generate_executive_summary(forecast)
        assert len(summary.monthly_breakdown) == 3


# -------------------------------------------------------------------------
# Deal parsing
# -------------------------------------------------------------------------


class TestDealParsing:
    def test_unknown_stage_defaults_prospect(self, engine):
        deal = engine._parse_deal({"stage": "invalid", "property_value": 500_000})
        assert deal.stage == DealStage.PROSPECT

    def test_missing_fields_handled(self, engine):
        deal = engine._parse_deal({})
        assert deal.deal_id == "unknown"
        assert deal.property_value == 0
        assert deal.stage == DealStage.PROSPECT