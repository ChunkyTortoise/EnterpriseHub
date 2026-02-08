"""
Tests for Advanced Churn Recovery Dashboard Components

Test suite for the three executive dashboard components:
- Advanced Churn Recovery Dashboard
- Multi-Market Analytics View
- ROI Calculator Component

Author: EnterpriseHub AI
Last Updated: 2026-01-18
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from ghl_real_estate_ai.streamlit_demo.components.advanced_churn_recovery_dashboard import (
    ChurnKPIs,
    MarketMetrics,
    generate_campaign_performance,
    generate_geographic_data,
    generate_recovery_pipeline_data,
    load_churn_metrics,
    load_market_data,
)
from ghl_real_estate_ai.streamlit_demo.components.multi_market_analytics_view import (
    CrossMarketFlow,
    MarketPerformance,
    generate_cross_market_flows,
    generate_time_series_data,
    get_health_class,
    get_trend_class,
    load_market_performance_data,
)
from ghl_real_estate_ai.streamlit_demo.components.roi_calculator_component import (
    ChannelInvestment,
    InvestmentScenario,
    ROICalculation,
    ROICalculator,
    get_channel_investments,
    get_investment_scenarios,
)


class TestAdvancedChurnRecoveryDashboard:
    """Test suite for Advanced Churn Recovery Dashboard"""

    def test_churn_kpis_data_structure(self):
        """Test ChurnKPIs data structure integrity"""
        kpis = load_churn_metrics()

        assert isinstance(kpis, ChurnKPIs)
        assert 0 <= kpis.overall_churn_rate <= 1
        assert 0 <= kpis.recovery_rate <= 1
        assert kpis.clv_recovered >= 0
        assert kpis.active_interventions >= 0
        assert kpis.at_risk_leads >= 0
        assert 0 <= kpis.success_rate <= 1

    def test_market_metrics_data_structure(self):
        """Test MarketMetrics data structure integrity"""
        markets = load_market_data()

        assert len(markets) == 5  # Five markets as specified

        for market in markets:
            assert isinstance(market, MarketMetrics)
            assert market.name in ["Austin Metro", "San Antonio", "Houston West", "Dallas North", "Fort Worth"]
            assert 0 <= market.churn_rate <= 1
            assert 0 <= market.recovery_rate <= 1
            assert market.active_campaigns >= 0
            assert market.clv_impact >= 0
            assert market.leads_at_risk >= 0
            assert market.recovered_this_month >= 0

    def test_recovery_pipeline_data(self):
        """Test recovery pipeline data generation"""
        pipeline_data = generate_recovery_pipeline_data()

        assert isinstance(pipeline_data, pd.DataFrame)
        assert len(pipeline_data) == 5  # Five stages in pipeline
        assert all(col in pipeline_data.columns for col in ["Stage", "Count", "Conversion_Rate"])

        # Check funnel logic (counts should generally decrease)
        counts = pipeline_data["Count"].tolist()
        for i in range(len(counts) - 1):
            assert counts[i] >= counts[i + 1], "Funnel should show decreasing counts"

    def test_campaign_performance_data(self):
        """Test campaign performance data generation"""
        campaign_data = generate_campaign_performance()

        assert isinstance(campaign_data, pd.DataFrame)
        assert len(campaign_data) >= 5  # At least 5 campaign channels

        required_columns = ["Channel", "Sent", "Opened", "Responded", "Converted", "Cost_Per_Lead", "ROI"]
        assert all(col in campaign_data.columns for col in required_columns)

        # Check business logic
        for _, row in campaign_data.iterrows():
            assert row["Opened"] <= row["Sent"]
            assert row["Responded"] <= row["Opened"]
            assert row["Converted"] <= row["Responded"]
            assert row["Cost_Per_Lead"] > 0
            assert row["ROI"] >= 0

    def test_geographic_data(self):
        """Test geographic data generation"""
        geo_data = generate_geographic_data()

        assert isinstance(geo_data, pd.DataFrame)
        assert len(geo_data) == 5  # Five markets

        required_columns = ["Market", "Latitude", "Longitude", "Churn_Rate", "Recovery_Rate", "At_Risk_Count"]
        assert all(col in geo_data.columns for col in required_columns)

        # Check data ranges
        assert all(geo_data["Latitude"].between(25, 35))  # Texas latitude range
        assert all(geo_data["Longitude"].between(-105, -90))  # Texas longitude range
        assert all(geo_data["Churn_Rate"].between(0, 20))  # Reasonable churn rate range
        assert all(geo_data["Recovery_Rate"].between(50, 100))  # Recovery rate range
        assert all(geo_data["At_Risk_Count"] >= 0)


class TestMultiMarketAnalyticsView:
    """Test suite for Multi-Market Analytics View"""

    def test_market_performance_data(self):
        """Test market performance data structure"""
        markets = load_market_performance_data()

        assert len(markets) == 5  # Five markets

        for market in markets:
            assert isinstance(market, MarketPerformance)
            assert market.active_leads > 0
            assert 0 <= market.conversion_rate <= 1
            assert market.avg_deal_size > 0
            assert 0 <= market.market_share <= 1
            assert market.growth_rate >= -1  # Can be negative but not below -100%
            assert 0 <= market.health_score <= 100
            assert market.competitive_position in ["Leader", "Challenger", "Follower"]
            assert isinstance(market.attribution_sources, dict)

    def test_time_series_data_generation(self):
        """Test time series data generation"""
        time_series_data = generate_time_series_data()

        assert isinstance(time_series_data, pd.DataFrame)
        assert len(time_series_data) > 50  # Multiple weeks of data for multiple markets

        required_columns = ["Date", "Market", "Conversion_Rate", "Lead_Volume", "Revenue"]
        assert all(col in time_series_data.columns for col in required_columns)

        # Check data integrity
        assert all(time_series_data["Conversion_Rate"].between(0, 1))
        assert all(time_series_data["Lead_Volume"] > 0)
        assert all(time_series_data["Revenue"] > 0)

        # Check date range
        date_range = time_series_data["Date"].max() - time_series_data["Date"].min()
        assert date_range.days > 100  # At least 3+ months of data

    def test_cross_market_flows(self):
        """Test cross-market flow data"""
        flows = generate_cross_market_flows()

        assert len(flows) >= 5  # Multiple cross-market flows

        for flow in flows:
            assert isinstance(flow, CrossMarketFlow)
            assert flow.source_market != flow.target_market  # No self-loops
            assert flow.lead_count > 0
            assert 0 <= flow.conversion_rate <= 1
            assert flow.avg_value > 0

    def test_health_classification(self):
        """Test health score classification"""
        assert get_health_class(95) == "health-excellent"
        assert get_health_class(80) == "health-good"
        assert get_health_class(70) == "health-warning"
        assert get_health_class(50) == "health-critical"

    def test_trend_classification(self):
        """Test trend classification"""
        assert get_trend_class(0.08) == "trend-up"
        assert get_trend_class(-0.08) == "trend-down"
        assert get_trend_class(0.02) == "trend-stable"


class TestROICalculatorComponent:
    """Test suite for ROI Calculator Component"""

    def test_investment_scenarios(self):
        """Test investment scenario data"""
        scenarios = get_investment_scenarios()

        assert len(scenarios) >= 3  # At least 3 scenarios

        for scenario in scenarios:
            assert isinstance(scenario, InvestmentScenario)
            assert len(scenario.name) > 0
            assert len(scenario.description) > 0
            assert scenario.monthly_cost > 0
            assert scenario.setup_cost >= 0
            assert 0 <= scenario.expected_recovery_lift <= 1
            assert scenario.implementation_months > 0
            assert scenario.risk_level in ["Low", "Medium", "High"]

    def test_channel_investments(self):
        """Test channel investment data"""
        channels = get_channel_investments()

        assert len(channels) >= 3  # At least 3 channels

        for channel in channels:
            assert isinstance(channel, ChannelInvestment)
            assert len(channel.name) > 0
            assert channel.current_cost_per_lead > 0
            assert 0 <= channel.current_conversion_rate <= 1
            assert channel.investment_amount > 0
            assert 0 <= channel.projected_cpl_reduction <= 1
            assert 0 <= channel.projected_conversion_lift <= 1
            assert channel.roi_projection >= 0

    def test_roi_calculator_logic(self):
        """Test ROI calculation logic"""
        calculator = ROICalculator(base_clv=12500, base_churn_rate=0.08)

        scenario = InvestmentScenario(
            name="Test Scenario",
            description="Test description",
            monthly_cost=2500,
            setup_cost=5000,
            expected_recovery_lift=0.10,
            implementation_months=3,
            risk_level="Medium",
        )

        roi_calc = calculator.calculate_scenario_roi(scenario, 1000, 0.60)

        assert isinstance(roi_calc, ROICalculation)
        assert roi_calc.total_investment > 0
        assert roi_calc.projected_clv_recovery >= 0
        assert roi_calc.break_even_leads >= 0

        # If net benefit is positive, ROI should be positive
        if roi_calc.net_benefit > 0:
            assert roi_calc.roi_percentage > 0

        # Payback months should be reasonable
        if roi_calc.payback_months != float("inf"):
            assert roi_calc.payback_months > 0

    def test_roi_edge_cases(self):
        """Test ROI calculator edge cases"""
        calculator = ROICalculator(base_clv=12500, base_churn_rate=0.08)

        # Test with zero investment
        scenario = InvestmentScenario(
            name="Zero Investment",
            description="No cost scenario",
            monthly_cost=0,
            setup_cost=0,
            expected_recovery_lift=0.05,
            implementation_months=1,
            risk_level="Low",
        )

        roi_calc = calculator.calculate_scenario_roi(scenario, 1000, 0.60)

        # With zero investment, ROI calculation should handle division by zero
        assert roi_calc.total_investment == 0

        # Test with very high recovery rate
        high_recovery_scenario = InvestmentScenario(
            name="High Recovery",
            description="Very high recovery lift",
            monthly_cost=1000,
            setup_cost=1000,
            expected_recovery_lift=0.50,  # 50% lift
            implementation_months=1,
            risk_level="High",
        )

        roi_calc = calculator.calculate_scenario_roi(high_recovery_scenario, 1000, 0.60)

        # Recovery rate should be capped at 95%
        expected_max_recovery = 0.95
        at_risk_leads = 1000 * 0.08
        max_recovered = at_risk_leads * expected_max_recovery
        current_recovered = at_risk_leads * 0.60

        assert roi_calc.projected_clv_recovery <= (max_recovered - current_recovered) * 12500


class TestIntegrationTests:
    """Integration tests for all dashboard components"""

    def test_data_consistency_across_components(self):
        """Test that market data is consistent across components"""

        # Get market data from different components
        churn_markets = load_market_data()
        analytics_markets = load_market_performance_data()

        # Should have same number of markets
        assert len(churn_markets) == len(analytics_markets)

        # Market names should overlap
        churn_market_names = {m.name for m in churn_markets}
        analytics_market_names = {m.name for m in analytics_markets}

        # Should have significant overlap in market names
        overlap = churn_market_names.intersection(analytics_market_names)
        assert len(overlap) >= 3  # At least 3 markets should overlap

    def test_component_import_structure(self):
        """Test that all components can be imported without errors"""

        # This test ensures that the import structure is correct
        # and that there are no circular dependencies

        try:
            from ghl_real_estate_ai.streamlit_demo.components import (
                advanced_churn_recovery_dashboard,
                multi_market_analytics_view,
                roi_calculator_component,
            )

            # Check that main functions exist
            assert hasattr(advanced_churn_recovery_dashboard, "render_advanced_churn_recovery_dashboard")
            assert hasattr(multi_market_analytics_view, "render_multi_market_analytics_view")
            assert hasattr(roi_calculator_component, "render_roi_calculator")

        except ImportError as e:
            pytest.fail(f"Failed to import dashboard components: {e}")

    @patch("streamlit.cache_data")
    def test_caching_decorators(self, mock_cache_data):
        """Test that caching decorators are properly applied"""

        # Mock the cache decorator
        mock_cache_data.return_value = lambda func: func

        # Test that cached functions can be called
        kpis = load_churn_metrics()
        markets = load_market_data()
        performance_data = load_market_performance_data()

        assert kpis is not None
        assert markets is not None
        assert performance_data is not None


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
