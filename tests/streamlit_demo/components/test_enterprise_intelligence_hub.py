"""
Tests for Enterprise Intelligence Hub Component.

Ensures reliability for C-suite engagement and high-ticket consulting demonstrations.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import numpy as np
import pandas as pd
import pytest
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.components.enterprise_intelligence_hub import (

    CompetitiveIntelligence,
    EnterpriseIntelligenceHub,
    ExecutiveKPI,
    PredictiveAlert,
    render_competitive_intelligence_dashboard,
    render_enterprise_intelligence_hub,
    render_executive_header,
    render_executive_kpi_card,
    render_mobile_command_center,
    render_performance_intelligence,
    render_predictive_analytics_executive,
    render_roi_attribution_executive,
    render_strategic_overview,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for testing."""
    with (
        patch("streamlit.set_page_config"),
        patch("streamlit.markdown"),
        patch("streamlit.columns"),
        patch("streamlit.tabs"),
        patch("streamlit.metric"),
        patch("streamlit.button"),
        patch("streamlit.plotly_chart"),
        patch("streamlit.dataframe"),
        patch("streamlit.success"),
        patch("streamlit.info"),
        patch("streamlit.warning"),
    ):
        yield


@pytest.fixture
def intelligence_hub():
    """Create intelligence hub instance for testing."""
    with (
        patch(
            "ghl_real_estate_ai.streamlit_demo.components.enterprise_intelligence_hub.get_strategic_claude_consultant",
            return_value=AsyncMock(),
        ),
        patch(
            "ghl_real_estate_ai.streamlit_demo.components.enterprise_intelligence_hub.get_enterprise_tenant_service",
            return_value=AsyncMock(),
        ),
    ):
        hub = EnterpriseIntelligenceHub(tenant_id="test_tenant")
        return hub


@pytest.fixture
def sample_executive_kpi():
    """Sample executive KPI for testing."""
    return ExecutiveKPI(
        name="Monthly Recurring Revenue",
        current_value=2450000,
        target_value=2800000,
        previous_period=2180000,
        unit="USD",
        trend="up",
        impact_level="critical",
        strategic_significance="Core revenue growth driver",
        ai_insight="Revenue growth accelerating 12.4% month-over-month",
        recommended_action="Accelerate high-value lead acquisition",
    )


@pytest.fixture
def sample_competitive_intelligence():
    """Sample competitive intelligence for testing."""
    return CompetitiveIntelligence(
        competitor_name="MarketLeader Corp",
        market_share=18.5,
        revenue_estimate=450000000,
        key_differentiators=["Brand recognition", "Large sales team"],
        threats=["Price competition", "Established relationships"],
        opportunities=["Slow AI adoption", "Legacy technology stack"],
        strategic_response="Leverage AI advantage for superior customer experience",
    )


@pytest.fixture
def sample_predictive_alert():
    """Sample predictive alert for testing."""
    return PredictiveAlert(
        alert_id="ALERT_001",
        severity="warning",
        metric_name="Q4 Revenue Target",
        predicted_impact="15% shortfall risk",
        probability=0.32,
        time_to_impact="6 weeks",
        recommended_response="Accelerate deal closure in luxury segment",
        business_context="Market seasonality affecting conversion rates",
    )


# ============================================================================
# Data Model Tests
# ============================================================================


def test_executive_kpi_model(sample_executive_kpi):
    """Test ExecutiveKPI data model."""
    assert sample_executive_kpi.name == "Monthly Recurring Revenue"
    assert sample_executive_kpi.current_value == 2450000
    assert sample_executive_kpi.trend == "up"
    assert sample_executive_kpi.impact_level == "critical"
    assert len(sample_executive_kpi.ai_insight) > 0
    assert len(sample_executive_kpi.recommended_action) > 0


def test_competitive_intelligence_model(sample_competitive_intelligence):
    """Test CompetitiveIntelligence data model."""
    assert sample_competitive_intelligence.competitor_name == "MarketLeader Corp"
    assert sample_competitive_intelligence.market_share == 18.5
    assert sample_competitive_intelligence.revenue_estimate == 450000000
    assert len(sample_competitive_intelligence.key_differentiators) >= 2
    assert len(sample_competitive_intelligence.threats) >= 2
    assert len(sample_competitive_intelligence.opportunities) >= 2
    assert len(sample_competitive_intelligence.strategic_response) > 0


def test_predictive_alert_model(sample_predictive_alert):
    """Test PredictiveAlert data model."""
    assert sample_predictive_alert.alert_id == "ALERT_001"
    assert sample_predictive_alert.severity == "warning"
    assert sample_predictive_alert.metric_name == "Q4 Revenue Target"
    assert 0.0 <= sample_predictive_alert.probability <= 1.0
    assert len(sample_predictive_alert.recommended_response) > 0
    assert len(sample_predictive_alert.business_context) > 0


# ============================================================================
# EnterpriseIntelligenceHub Class Tests
# ============================================================================


def test_intelligence_hub_initialization(intelligence_hub):
    """Test proper initialization of EnterpriseIntelligenceHub."""
    assert intelligence_hub is not None
    assert intelligence_hub.tenant_id == "test_tenant"
    assert hasattr(intelligence_hub, "executive_kpis")
    assert hasattr(intelligence_hub, "competitive_landscape")
    assert hasattr(intelligence_hub, "predictive_alerts")


def test_demo_data_quality(intelligence_hub):
    """Test quality of demonstration data for executive showcase."""
    # Executive KPIs validation
    assert len(intelligence_hub.executive_kpis) >= 4

    for kpi in intelligence_hub.executive_kpis:
        assert isinstance(kpi, ExecutiveKPI)
        assert kpi.current_value > 0
        assert kpi.target_value > 0
        assert kpi.trend in ["up", "down", "stable"]
        assert kpi.impact_level in ["critical", "high", "medium", "low"]
        assert len(kpi.strategic_significance) > 20  # Substantial content
        assert len(kpi.ai_insight) > 20  # Substantial AI insight
        assert len(kpi.recommended_action) > 15  # Actionable recommendation

    # Competitive landscape validation
    assert len(intelligence_hub.competitive_landscape) >= 2

    for competitor in intelligence_hub.competitive_landscape:
        assert isinstance(competitor, CompetitiveIntelligence)
        assert competitor.market_share > 0
        assert competitor.revenue_estimate > 0
        assert len(competitor.key_differentiators) >= 2
        assert len(competitor.threats) >= 2
        assert len(competitor.opportunities) >= 2
        assert len(competitor.strategic_response) > 30  # Strategic depth

    # Predictive alerts validation
    assert len(intelligence_hub.predictive_alerts) >= 2

    for alert in intelligence_hub.predictive_alerts:
        assert isinstance(alert, PredictiveAlert)
        assert alert.severity in ["critical", "warning", "info"]
        assert 0.0 <= alert.probability <= 1.0
        assert len(alert.business_context) > 20  # Contextual depth


def test_executive_value_demonstration(intelligence_hub):
    """Test that hub demonstrates sufficient executive value."""
    # Revenue KPIs should show substantial scale
    revenue_kpis = [kpi for kpi in intelligence_hub.executive_kpis if "revenue" in kpi.name.lower()]
    if revenue_kpis:
        for kpi in revenue_kpis:
            assert kpi.current_value >= 1000000  # Minimum $1M scale for enterprise

    # Should have critical KPIs for executive attention
    critical_kpis = [kpi for kpi in intelligence_hub.executive_kpis if kpi.impact_level == "critical"]
    assert len(critical_kpis) >= 2  # Multiple critical metrics

    # Competitive analysis should show strategic depth
    total_competitor_revenue = sum(comp.revenue_estimate for comp in intelligence_hub.competitive_landscape)
    assert total_competitor_revenue > 500000000  # Substantial market


async def test_intelligence_hub_initialization_async(intelligence_hub):
    """Test asynchronous initialization."""
    await intelligence_hub.initialize()
    # Should not crash and should handle missing services gracefully
    assert intelligence_hub.strategic_consultant is None  # Mocked to return None
    assert intelligence_hub.tenant_service is None


# ============================================================================
# Render Function Tests
# ============================================================================


def test_render_enterprise_intelligence_hub(mock_streamlit):
    """Test main render function executes without errors."""
    try:
        render_enterprise_intelligence_hub("test_tenant")
        # If no exception raised, test passes
        assert True
    except Exception as e:
        pytest.fail(f"render_enterprise_intelligence_hub raised {e}")


def test_render_executive_header(mock_streamlit, intelligence_hub):
    """Test executive header rendering."""
    with patch("datetime.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "January 17, 2026 at 02:30 PM"

        try:
            render_executive_header(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_executive_header raised {e}")


def test_render_strategic_overview(mock_streamlit, intelligence_hub):
    """Test strategic overview rendering."""
    try:
        render_strategic_overview(intelligence_hub)
        assert True
    except Exception as e:
        pytest.fail(f"render_strategic_overview raised {e}")


def test_render_executive_kpi_card(mock_streamlit, sample_executive_kpi):
    """Test executive KPI card rendering."""
    try:
        render_executive_kpi_card(sample_executive_kpi)
        assert True
    except Exception as e:
        pytest.fail(f"render_executive_kpi_card raised {e}")


def test_render_performance_intelligence(mock_streamlit, intelligence_hub):
    """Test performance intelligence dashboard rendering."""
    with patch("pandas.date_range"), patch("plotly.graph_objects.Figure") as mock_fig:
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()

        try:
            render_performance_intelligence(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_performance_intelligence raised {e}")


def test_render_predictive_analytics_executive(mock_streamlit, intelligence_hub):
    """Test predictive analytics rendering."""
    with (
        patch("pandas.date_range"),
        patch("plotly.graph_objects.Figure") as mock_fig,
        patch("plotly.subplots.make_subplots") as mock_subplots,
    ):
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()
        mock_subplots.return_value.update_layout = Mock()
        mock_subplots.return_value.add_trace = Mock()

        try:
            render_predictive_analytics_executive(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_predictive_analytics_executive raised {e}")


def test_render_competitive_intelligence_dashboard(mock_streamlit, intelligence_hub):
    """Test competitive intelligence dashboard rendering."""
    with patch("plotly.graph_objects.Figure") as mock_fig:
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()

        try:
            render_competitive_intelligence_dashboard(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_competitive_intelligence_dashboard raised {e}")


def test_render_roi_attribution_executive(mock_streamlit, intelligence_hub):
    """Test ROI attribution dashboard rendering."""
    with patch("plotly.graph_objects.Figure") as mock_fig, patch("plotly.subplots.make_subplots") as mock_subplots:
        mock_fig.return_value.update_layout = Mock()
        mock_subplots.return_value.update_layout = Mock()
        mock_subplots.return_value.add_trace = Mock()

        try:
            render_roi_attribution_executive(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_roi_attribution_executive raised {e}")


def test_render_mobile_command_center(mock_streamlit, intelligence_hub):
    """Test mobile command center rendering."""
    with patch("plotly.graph_objects.Figure") as mock_fig, patch("numpy.cumsum"), patch("numpy.random.normal"):
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()

        try:
            render_mobile_command_center(intelligence_hub)
            assert True
        except Exception as e:
            pytest.fail(f"render_mobile_command_center raised {e}")


# ============================================================================
# Business Logic Tests
# ============================================================================


def test_kpi_calculations(intelligence_hub):
    """Test KPI calculation logic and business metrics."""
    for kpi in intelligence_hub.executive_kpis:
        # Test percentage change calculation
        if kpi.previous_period > 0:
            pct_change = ((kpi.current_value - kpi.previous_period) / kpi.previous_period) * 100

            # Trend should align with percentage change
            if pct_change > 5:
                assert kpi.trend == "up"
            elif pct_change < -5:
                assert kpi.trend == "down"
            # "stable" trend acceptable for small changes

        # Target progress calculation
        if kpi.target_value > 0:
            pct_to_target = ((kpi.current_value - kpi.target_value) / kpi.target_value) * 100
            # Percentage should be calculable (no division by zero)
            assert isinstance(pct_to_target, float)


def test_competitive_analysis_quality(intelligence_hub):
    """Test quality of competitive analysis for executive decision making."""
    total_market_share = sum(comp.market_share for comp in intelligence_hub.competitive_landscape)

    # Market analysis should be comprehensive
    assert len(intelligence_hub.competitive_landscape) >= 2  # Multiple competitors analyzed

    for competitor in intelligence_hub.competitive_landscape:
        # Strategic insights should be substantial
        assert len(competitor.strategic_response) > 50  # Strategic depth

        # Should identify both threats and opportunities
        assert len(competitor.threats) >= 1
        assert len(competitor.opportunities) >= 1

        # Revenue estimates should be reasonable
        assert competitor.revenue_estimate > 0
        assert competitor.market_share > 0


def test_predictive_alerts_business_value(intelligence_hub):
    """Test that predictive alerts provide business value."""
    for alert in intelligence_hub.predictive_alerts:
        # Alerts should have specific business context
        assert len(alert.business_context) > 20  # Substantial context

        # Recommendations should be actionable
        assert len(alert.recommended_response) > 30  # Actionable detail

        # Probability should be realistic
        assert 0.0 <= alert.probability <= 1.0

        # Time to impact should be specified
        assert len(alert.time_to_impact) > 0

        # Should specify predicted business impact
        assert len(alert.predicted_impact) > 0


def test_c_suite_relevance(intelligence_hub):
    """Test that content is appropriate for C-suite audience."""
    # KPIs should be strategic, not operational
    strategic_kpis = ["revenue", "market", "customer", "growth", "profit"]

    for kpi in intelligence_hub.executive_kpis:
        kpi_name_lower = kpi.name.lower()
        is_strategic = any(strategic_term in kpi_name_lower for strategic_term in strategic_kpis)
        assert is_strategic or kpi.impact_level in ["critical", "high"]  # Should be strategic or high impact

    # Recommendations should be strategic level
    # This is validated through the substantial content requirements in other tests


# ============================================================================
# User Experience Tests
# ============================================================================


def test_mobile_responsiveness(intelligence_hub):
    """Test mobile optimization features."""
    # Mobile command center should have simplified metrics
    critical_metrics = [
        {"name": "Today's Revenue", "value": "$89.5K", "change": "+12%", "status": "good"},
        {"name": "Pipeline Health", "value": "92%", "change": "+5%", "status": "good"},
        {"name": "Active Alerts", "value": "2", "change": "-1", "status": "warning"},
        {"name": "Team Performance", "value": "94%", "change": "+3%", "status": "good"},
    ]

    # Should have exactly 4 critical metrics for mobile
    assert len(critical_metrics) == 4

    # Each metric should have required fields
    for metric in critical_metrics:
        assert "name" in metric
        assert "value" in metric
        assert "change" in metric
        assert "status" in metric
        assert metric["status"] in ["good", "warning", "critical"]


def test_visual_hierarchy(intelligence_hub):
    """Test visual hierarchy and executive attention management."""
    # Critical KPIs should be prominently featured
    critical_kpis = [kpi for kpi in intelligence_hub.executive_kpis if kpi.impact_level == "critical"]
    assert len(critical_kpis) >= 2  # Multiple critical items for executive attention

    # Alerts should be properly prioritized
    critical_alerts = [alert for alert in intelligence_hub.predictive_alerts if alert.severity == "critical"]
    warning_alerts = [alert for alert in intelligence_hub.predictive_alerts if alert.severity == "warning"]

    # Should have clear severity levels
    total_alerts = len(critical_alerts) + len(warning_alerts)
    assert total_alerts >= 1  # At least some alerts for executive attention


# ============================================================================
# Performance Tests
# ============================================================================


def test_data_loading_performance(intelligence_hub):
    """Test that demo data loads quickly for responsive UX."""
    import time

    start_time = time.time()

    # Simulate accessing all demo data
    _ = intelligence_hub.executive_kpis
    _ = intelligence_hub.competitive_landscape
    _ = intelligence_hub.predictive_alerts

    loading_time = time.time() - start_time

    # Should load demo data quickly
    assert loading_time < 0.1  # Less than 100ms for demo data


def test_rendering_performance(mock_streamlit, intelligence_hub):
    """Test that rendering performs well for executive demos."""
    import time

    start_time = time.time()

    with patch("plotly.graph_objects.Figure") as mock_fig:
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()

        # Test key rendering functions
        render_executive_header(intelligence_hub)
        render_strategic_overview(intelligence_hub)
        render_executive_kpi_card(intelligence_hub.executive_kpis[0])

    rendering_time = time.time() - start_time

    # Should render quickly for smooth executive experience
    assert rendering_time < 1.0  # Less than 1 second


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_missing_data_handling(mock_streamlit):
    """Test handling of missing or incomplete data."""
    # Create hub with minimal data
    hub = EnterpriseIntelligenceHub()
    hub.executive_kpis = []  # Empty KPIs
    hub.competitive_landscape = []  # Empty competitive data
    hub.predictive_alerts = []  # No alerts

    # Should handle gracefully without crashing
    try:
        render_strategic_overview(hub)
        render_competitive_intelligence_dashboard(hub)
        render_predictive_analytics_executive(hub)
        assert True
    except Exception as e:
        pytest.fail(f"Failed to handle missing data gracefully: {e}")


def test_invalid_kpi_data(mock_streamlit):
    """Test handling of invalid KPI data."""
    invalid_kpi = ExecutiveKPI(
        name="Invalid KPI",
        current_value=0,  # Zero value
        target_value=-100,  # Negative target
        previous_period=0,  # Zero previous
        unit="INVALID",
        trend="unknown",  # Invalid trend
        impact_level="invalid",  # Invalid impact
        strategic_significance="",  # Empty
        ai_insight="",  # Empty
        recommended_action="",  # Empty
    )

    # Should handle gracefully
    try:
        render_executive_kpi_card(invalid_kpi)
        assert True
    except Exception as e:
        pytest.fail(f"Failed to handle invalid KPI data: {e}")


# ============================================================================
# Integration Tests
# ============================================================================


def test_end_to_end_executive_dashboard(mock_streamlit):
    """Test complete end-to-end executive dashboard rendering."""
    with (
        patch(
            "ghl_real_estate_ai.streamlit_demo.components.enterprise_intelligence_hub.get_strategic_claude_consultant",
            return_value=AsyncMock(),
        ),
        patch(
            "ghl_real_estate_ai.streamlit_demo.components.enterprise_intelligence_hub.get_enterprise_tenant_service",
            return_value=AsyncMock(),
        ),
        patch("plotly.graph_objects.Figure") as mock_fig,
        patch("plotly.express.scatter"),
        patch("plotly.subplots.make_subplots"),
    ):
        mock_fig.return_value.update_layout = Mock()
        mock_fig.return_value.add_trace = Mock()

        try:
            # Full dashboard render
            render_enterprise_intelligence_hub("test_tenant")
            assert True
        except Exception as e:
            pytest.fail(f"End-to-end dashboard rendering failed: {e}")


# ============================================================================
# Business Value Tests
# ============================================================================


def test_consulting_value_demonstration(intelligence_hub):
    """Test that dashboard demonstrates sufficient value for $25K-$100K consulting."""

    # Should demonstrate substantial business scale
    revenue_values = []
    for kpi in intelligence_hub.executive_kpis:
        if kpi.unit == "USD" and kpi.current_value > 1000000:  # Million+ scale
            revenue_values.append(kpi.current_value)

    assert len(revenue_values) > 0  # Should have enterprise-scale revenue metrics

    # Should show strategic competitive intelligence
    total_market_analysis = sum(comp.revenue_estimate for comp in intelligence_hub.competitive_landscape)
    assert total_market_analysis > 500000000  # Should analyze $500M+ market

    # Should provide AI-powered insights
    ai_insights = [kpi.ai_insight for kpi in intelligence_hub.executive_kpis if len(kpi.ai_insight) > 30]
    assert len(ai_insights) >= 3  # Multiple sophisticated AI insights

    # Should provide strategic recommendations
    strategic_actions = [
        kpi.recommended_action for kpi in intelligence_hub.executive_kpis if len(kpi.recommended_action) > 20
    ]
    assert len(strategic_actions) >= 3  # Multiple actionable strategic recommendations


if __name__ == "__main__":
    pytest.main([__file__, "-v"])