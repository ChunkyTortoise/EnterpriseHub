"""Tests for Real-Time Market Intelligence Service."""

import pytest

from ghl_real_estate_ai.services.real_time_market_intelligence import (
    AlertSeverity,
    MarketCondition,
    Neighborhood,
    RealTimeMarketIntelligence,
    TrendDirection,
)


@pytest.fixture
def intel():
    return RealTimeMarketIntelligence()


# -------------------------------------------------------------------------
# Market snapshots
# -------------------------------------------------------------------------


class TestMarketSnapshot:
    @pytest.mark.asyncio
    async def test_victoria_snapshot(self, intel):
        snap = await intel.get_market_snapshot("victoria")
        assert snap.neighborhood == "victoria"
        assert snap.median_price > 0
        assert snap.avg_days_on_market > 0
        assert snap.active_inventory > 0

    @pytest.mark.asyncio
    async def test_etiwanda_sellers_market(self, intel):
        snap = await intel.get_market_snapshot("etiwanda")
        assert snap.market_condition == MarketCondition.SELLERS
        assert snap.buyer_competition_index > 0.5

    @pytest.mark.asyncio
    async def test_central_park_balanced_or_buyers(self, intel):
        snap = await intel.get_market_snapshot("central_park")
        assert snap.market_condition in (MarketCondition.BALANCED, MarketCondition.BUYERS)

    @pytest.mark.asyncio
    async def test_unknown_neighborhood_defaults(self, intel):
        snap = await intel.get_market_snapshot("nonexistent")
        assert snap.neighborhood == "central_park"

    @pytest.mark.asyncio
    async def test_competition_index_bounded(self, intel):
        for nb in Neighborhood:
            snap = await intel.get_market_snapshot(nb.value)
            assert 0 <= snap.buyer_competition_index <= 1


# -------------------------------------------------------------------------
# Price trends
# -------------------------------------------------------------------------


class TestPriceTrends:
    @pytest.mark.asyncio
    async def test_rising_trend_for_appreciating_area(self, intel):
        trend = await intel.get_price_trends("etiwanda", days=90)
        assert trend.direction == TrendDirection.RISING
        assert trend.price_change_pct > 0

    @pytest.mark.asyncio
    async def test_support_below_resistance(self, intel):
        trend = await intel.get_price_trends("haven", days=90)
        assert trend.support_level < trend.resistance_level

    @pytest.mark.asyncio
    async def test_momentum_bounded(self, intel):
        trend = await intel.get_price_trends("victoria", days=90)
        assert -1 <= trend.momentum <= 1

    @pytest.mark.asyncio
    async def test_confidence_bounded(self, intel):
        trend = await intel.get_price_trends("terra_vista", days=30)
        assert 0 <= trend.confidence <= 1

    @pytest.mark.asyncio
    async def test_forecast_positive_for_rising(self, intel):
        trend = await intel.get_price_trends("etiwanda", days=90)
        assert trend.forecast_30d_pct > 0


# -------------------------------------------------------------------------
# Opportunity detection
# -------------------------------------------------------------------------


class TestOpportunityDetection:
    @pytest.mark.asyncio
    async def test_detects_hot_zone(self, intel):
        opps = await intel.detect_opportunities(min_score=0.3)
        hot_zones = [o for o in opps if o.opportunity_type == "hot_zone"]
        assert len(hot_zones) > 0

    @pytest.mark.asyncio
    async def test_opportunities_sorted_by_score(self, intel):
        opps = await intel.detect_opportunities(min_score=0.1)
        if len(opps) >= 2:
            assert opps[0].score >= opps[1].score

    @pytest.mark.asyncio
    async def test_high_threshold_fewer_opportunities(self, intel):
        low = await intel.detect_opportunities(min_score=0.1)
        high = await intel.detect_opportunities(min_score=0.9)
        assert len(high) <= len(low)

    @pytest.mark.asyncio
    async def test_opportunity_has_action(self, intel):
        opps = await intel.detect_opportunities(min_score=0.3)
        for opp in opps:
            assert opp.recommended_action
            assert opp.time_sensitivity


# -------------------------------------------------------------------------
# Alerts
# -------------------------------------------------------------------------


class TestAlerts:
    @pytest.mark.asyncio
    async def test_low_inventory_alert(self, intel):
        alerts = await intel.check_alerts({"inventory_low": 35, "appreciation_warning": 0.08})
        inv_alerts = [a for a in alerts if a.metric_name == "inventory"]
        assert len(inv_alerts) > 0
        assert inv_alerts[0].severity == AlertSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_appreciation_warning(self, intel):
        alerts = await intel.check_alerts({"appreciation_warning": 0.07, "inventory_low": 20})
        app_alerts = [a for a in alerts if a.metric_name == "appreciation_1yr"]
        assert len(app_alerts) > 0

    @pytest.mark.asyncio
    async def test_no_alerts_with_high_thresholds(self, intel):
        alerts = await intel.check_alerts({"appreciation_warning": 0.99, "inventory_low": 1})
        assert len(alerts) == 0


# -------------------------------------------------------------------------
# Neighborhood comparison
# -------------------------------------------------------------------------


class TestComparison:
    @pytest.mark.asyncio
    async def test_comparison_returns_all_neighborhoods(self, intel):
        comp = await intel.get_neighborhood_comparison()
        assert len(comp) >= 4  # At least 4 unique neighborhoods

    @pytest.mark.asyncio
    async def test_comparison_sorted_by_appreciation(self, intel):
        comp = await intel.get_neighborhood_comparison()
        if len(comp) >= 2:
            assert comp[0]["appreciation"] >= comp[1]["appreciation"]


# -------------------------------------------------------------------------
# Price ingestion
# -------------------------------------------------------------------------


class TestPriceIngestion:
    def test_ingest_adds_to_history(self, intel):
        intel.ingest_price_update("victoria", 850_000)
        history = intel._price_history.get("victoria", [])
        assert len(history) >= 2  # baseline + new
        assert history[-1]["price"] == 850_000
