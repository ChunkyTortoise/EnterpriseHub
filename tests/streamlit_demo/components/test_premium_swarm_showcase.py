"""
Tests for Premium Multi-Agent Swarm Showcase Component.

Ensures reliability for high-ticket consulting demonstrations ($25K-$100K).
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest
import streamlit as st

from ghl_real_estate_ai.streamlit_demo.components.premium_swarm_showcase import (
    AgentReasoningStep,
    ConsensusVisualization,
    PremiumSwarmMetrics,
    PremiumSwarmShowcase,
    generate_agent_insight,
    render_agent_consensus_visualization,
    render_live_swarm_analysis,
    render_premium_swarm_showcase,
    render_roi_attribution_dashboard,
    render_swarm_configuration,
    render_swarm_performance_metrics,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit components for testing."""
    with (
        patch("streamlit.markdown"),
        patch("streamlit.columns"),
        patch("streamlit.tabs"),
        patch("streamlit.selectbox"),
        patch("streamlit.button"),
        patch("streamlit.progress"),
        patch("streamlit.empty"),
        patch("streamlit.metric"),
        patch("streamlit.expander"),
        patch("streamlit.plotly_chart"),
        patch("streamlit.dataframe"),
        patch("streamlit.slider"),
        patch("streamlit.number_input"),
        patch("streamlit.multiselect"),
        patch("streamlit.checkbox"),
        patch("streamlit.success"),
        patch("streamlit.info"),
    ):
        yield


@pytest.fixture
def premium_showcase():
    """Create premium showcase instance for testing."""
    with (
        patch.object(PremiumSwarmShowcase, "_get_swarm_service", return_value=None),
        patch.object(PremiumSwarmShowcase, "_get_lead_swarm", return_value=None),
    ):
        showcase = PremiumSwarmShowcase()
        return showcase


@pytest.fixture
def sample_agent():
    """Sample agent data for testing."""
    return {"name": "Test Agent", "specialty": "Test Analysis", "accuracy": 92.5, "confidence": 0.89}


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "demographics": {"age": 35, "income": 150000, "location": "Rancho Cucamonga, CA", "job": "Engineer"},
        "behavior": {"engagement_score": 85, "urgency": "High", "decision_style": "Data-Driven"},
        "intent": {"timeline": "30 days", "budget": "500K-700K", "motivation": "Upgrade"},
        "risk_score": 20,
        "roi_potential": 450000,
    }


# ============================================================================
# Data Model Tests
# ============================================================================


def test_premium_swarm_metrics():
    """Test PremiumSwarmMetrics data model."""
    metrics = PremiumSwarmMetrics(
        total_agents=10,
        active_analyses=5,
        consensus_accuracy=94.2,
        processing_time_ms=2300,
        confidence_score=0.91,
        uncertainty_level=0.09,
        business_impact_score=85.5,
        roi_attribution=485000.0,
    )

    assert metrics.total_agents == 10
    assert metrics.consensus_accuracy == 94.2
    assert metrics.roi_attribution == 485000.0


def test_agent_reasoning_step():
    """Test AgentReasoningStep data model."""
    step = AgentReasoningStep(
        agent_name="Behavioral Profiler",
        step_description="Analyzing engagement patterns",
        confidence=0.87,
        data_sources=["CRM", "Website Analytics", "Email Engagement"],
        psychological_insight="High urgency indicates emotional buying state",
        business_impact="Increase communication frequency by 40%",
    )

    assert step.agent_name == "Behavioral Profiler"
    assert step.confidence == 0.87
    assert len(step.data_sources) == 3
    assert step.psychological_insight is not None


def test_consensus_visualization():
    """Test ConsensusVisualization data model."""
    visualization = ConsensusVisualization(
        agent_positions={"Agent1": 85.2, "Agent2": 91.7, "Agent3": 78.9},
        consensus_strength=88.6,
        convergence_timeline=[("10:00", 0.65), ("10:05", 0.82), ("10:10", 0.91)],
        conflict_areas=["Timeline Assessment", "Risk Evaluation"],
        resolution_strategy="Weighted confidence averaging",
    )

    assert len(visualization.agent_positions) == 3
    assert visualization.consensus_strength == 88.6
    assert len(visualization.conflict_areas) == 2


# ============================================================================
# PremiumSwarmShowcase Class Tests
# ============================================================================


def test_premium_showcase_initialization(premium_showcase):
    """Test proper initialization of PremiumSwarmShowcase."""
    assert premium_showcase is not None
    assert hasattr(premium_showcase, "demo_agents")
    assert hasattr(premium_showcase, "demo_leads")
    assert len(premium_showcase.demo_agents) == 10
    assert len(premium_showcase.demo_leads) == 3


def test_demo_agents_structure(premium_showcase):
    """Test demo agents have required structure and data."""
    for agent in premium_showcase.demo_agents:
        assert "name" in agent
        assert "specialty" in agent
        assert "accuracy" in agent
        assert "confidence" in agent
        assert isinstance(agent["accuracy"], (int, float))
        assert 0.0 <= agent["confidence"] <= 1.0
        assert agent["accuracy"] > 80  # All agents should have high accuracy


def test_demo_leads_structure(premium_showcase):
    """Test demo leads have comprehensive data structure."""
    for lead_name, lead_data in premium_showcase.demo_leads.items():
        assert "demographics" in lead_data
        assert "behavior" in lead_data
        assert "intent" in lead_data
        assert "risk_score" in lead_data
        assert "roi_potential" in lead_data

        # Demographics validation
        demo = lead_data["demographics"]
        assert "age" in demo
        assert "income" in demo
        assert "location" in demo
        assert demo["age"] > 18
        assert demo["income"] > 0

        # Business metrics validation
        assert 0 <= lead_data["risk_score"] <= 100
        assert lead_data["roi_potential"] > 0


# ============================================================================
# Agent Insight Generation Tests
# ============================================================================


def test_generate_agent_insight_demographic(sample_agent, sample_lead_data):
    """Test demographic agent insight generation."""
    agent = {**sample_agent, "name": "Demographic Analyzer"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    assert insight["primary_finding"] is not None
    assert insight["confidence"] > 0.8
    assert len(insight["key_insights"]) >= 3
    assert "business_impact" in insight
    assert "income" in insight["primary_finding"].lower() or any(
        "income" in ki.lower() for ki in insight["key_insights"]
    )


def test_generate_agent_insight_behavioral(sample_agent, sample_lead_data):
    """Test behavioral agent insight generation."""
    agent = {**sample_agent, "name": "Behavioral Profiler"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    assert "decision style" in insight["primary_finding"].lower() or "urgency" in insight["primary_finding"].lower()
    assert insight["confidence"] > 0.8
    assert len(insight["key_insights"]) >= 3
    assert "engagement" in str(insight["key_insights"]).lower()


def test_generate_agent_insight_intent(sample_agent, sample_lead_data):
    """Test intent detection agent insight generation."""
    agent = {**sample_agent, "name": "Intent Detector"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    assert "intent" in insight["primary_finding"].lower() or "timeline" in insight["primary_finding"].lower()
    assert insight["confidence"] > 0.8
    assert "budget" in str(insight["key_insights"]).lower()


def test_generate_agent_insight_financial(sample_agent, sample_lead_data):
    """Test financial agent insight generation."""
    agent = {**sample_agent, "name": "Financial Analyzer"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    assert "financial" in insight["primary_finding"].lower() or "value" in insight["primary_finding"].lower()
    assert insight["confidence"] > 0.9  # Financial agent should have high confidence
    assert any("debt" in ki.lower() or "credit" in ki.lower() for ki in insight["key_insights"])


def test_generate_agent_insight_risk(sample_agent, sample_lead_data):
    """Test risk assessment agent insight generation."""
    agent = {**sample_agent, "name": "Risk Assessor"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    assert "risk" in insight["primary_finding"].lower()
    assert str(sample_lead_data["risk_score"]) in insight["primary_finding"]
    assert "churn" in str(insight["key_insights"]).lower() or "risk" in str(insight["key_insights"]).lower()


def test_generate_agent_insight_fallback(sample_agent, sample_lead_data):
    """Test fallback insight generation for unknown agent types."""
    agent = {**sample_agent, "name": "Unknown Agent Type"}
    insight = generate_agent_insight(agent, sample_lead_data, "Test Lead")

    # Should still return valid insight structure
    assert "primary_finding" in insight
    assert "confidence" in insight
    assert "key_insights" in insight
    assert "business_impact" in insight
    assert insight["confidence"] == sample_agent["confidence"]


# ============================================================================
# Render Function Tests
# ============================================================================


@patch("streamlit.session_state", new_callable=dict)
def test_render_premium_swarm_showcase(mock_session_state, mock_streamlit):
    """Test main render function executes without errors."""
    with patch("ghl_real_estate_ai.streamlit_demo.components.premium_swarm_showcase.PremiumSwarmShowcase"):
        try:
            render_premium_swarm_showcase()
            # If no exception raised, test passes
            assert True
        except Exception as e:
            pytest.fail(f"render_premium_swarm_showcase raised {e}")


@patch("streamlit.session_state", new_callable=dict)
def test_render_live_swarm_analysis(mock_session_state, mock_streamlit, premium_showcase):
    """Test live swarm analysis rendering."""
    with (
        patch("streamlit.selectbox", return_value="Sarah Chen - Tech Executive"),
        patch("streamlit.button", return_value=False),
    ):
        try:
            render_live_swarm_analysis(premium_showcase)
            assert True
        except Exception as e:
            pytest.fail(f"render_live_swarm_analysis raised {e}")


def test_render_agent_consensus_visualization(mock_streamlit, premium_showcase):
    """Test agent consensus visualization rendering."""
    with (
        patch("plotly.graph_objects.Figure") as mock_fig,
        patch("plotly.express.scatter") as mock_scatter,
        patch("numpy.random.uniform", return_value=np.ones((6, 6)) * 0.9),
    ):
        mock_fig.return_value.update_layout = Mock()
        mock_scatter.return_value = Mock()

        try:
            render_agent_consensus_visualization(premium_showcase)
            assert True
        except Exception as e:
            pytest.fail(f"render_agent_consensus_visualization raised {e}")


def test_render_roi_attribution_dashboard(mock_streamlit, premium_showcase):
    """Test ROI attribution dashboard rendering."""
    with patch("plotly.express.scatter") as mock_scatter, patch("plotly.graph_objects.Figure") as mock_fig:
        mock_scatter.return_value = Mock()
        mock_fig.return_value.update_layout = Mock()

        try:
            render_roi_attribution_dashboard(premium_showcase)
            assert True
        except Exception as e:
            pytest.fail(f"render_roi_attribution_dashboard raised {e}")


def test_render_swarm_performance_metrics(mock_streamlit, premium_showcase):
    """Test swarm performance metrics rendering."""
    with (
        patch("plotly.express.bar") as mock_bar,
        patch("plotly.express.line") as mock_line,
        patch("pandas.DataFrame") as mock_df,
    ):
        mock_bar.return_value.update_layout = Mock()
        mock_line.return_value.update_layout = Mock()
        mock_df.return_value = pd.DataFrame()

        try:
            render_swarm_performance_metrics(premium_showcase)
            assert True
        except Exception as e:
            pytest.fail(f"render_swarm_performance_metrics raised {e}")


def test_render_swarm_configuration(mock_streamlit, premium_showcase):
    """Test swarm configuration interface rendering."""
    with (
        patch("streamlit.tabs", return_value=[Mock(), Mock(), Mock()]),
        patch("streamlit.checkbox", return_value=True),
        patch("streamlit.slider", return_value=80),
        patch("streamlit.number_input", return_value=10),
        patch("streamlit.multiselect", return_value=["Luxury"]),
    ):
        try:
            render_swarm_configuration(premium_showcase)
            assert True
        except Exception as e:
            pytest.fail(f"render_swarm_configuration raised {e}")


# ============================================================================
# Integration Tests
# ============================================================================


@patch("streamlit.session_state", new_callable=dict)
def test_swarm_analysis_demo_execution(mock_session_state, premium_showcase):
    """Test swarm analysis demo execution flow."""
    mock_session_state["swarm_running"] = True

    with (
        patch("streamlit.progress") as mock_progress,
        patch("streamlit.empty") as mock_empty,
        patch("time.sleep"),
        patch("ghl_real_estate_ai.streamlit_demo.components.premium_swarm_showcase.display_swarm_results"),
    ):
        mock_progress_bar = Mock()
        mock_status_text = Mock()
        mock_progress.return_value = mock_progress_bar
        mock_empty.return_value = mock_status_text

        from ghl_real_estate_ai.streamlit_demo.components.premium_swarm_showcase import run_swarm_analysis_demo

        try:
            run_swarm_analysis_demo(premium_showcase, "Sarah Chen - Tech Executive")
            # Verify progress updates were called
            assert mock_progress_bar.progress.call_count >= len(premium_showcase.demo_agents)
        except Exception as e:
            pytest.fail(f"run_swarm_analysis_demo raised {e}")


# ============================================================================
# Business Logic Tests
# ============================================================================


def test_agent_insights_quality_validation():
    """Test that generated insights meet quality standards for consulting demos."""
    showcase = PremiumSwarmShowcase()

    # Test each agent type with sample data
    sample_lead = {
        "demographics": {"age": 40, "income": 200000, "location": "Rancho Cucamonga, CA", "job": "Director"},
        "behavior": {"engagement_score": 90, "urgency": "High", "decision_style": "Analytical"},
        "intent": {"timeline": "60 days", "budget": "800K-1M", "motivation": "Investment"},
        "risk_score": 15,
        "roi_potential": 650000,
    }

    key_agents = [
        "Demographic Analyzer",
        "Behavioral Profiler",
        "Intent Detector",
        "Financial Analyzer",
        "Risk Assessor",
    ]

    for agent_data in showcase.demo_agents:
        if agent_data["name"] in key_agents:
            insight = generate_agent_insight(agent_data, sample_lead, "Test Executive")

            # Quality checks
            assert len(insight["primary_finding"]) > 20  # Substantial finding
            assert len(insight["key_insights"]) >= 3  # Multiple insights
            assert insight["confidence"] > 0.8  # High confidence
            assert len(insight["business_impact"]) > 15  # Actionable impact

            # Business relevance checks
            primary_finding = insight["primary_finding"].lower()
            key_insights_text = " ".join(insight["key_insights"]).lower()

            if agent_data["name"] == "Demographic Analyzer":
                assert any(
                    term in primary_finding + key_insights_text for term in ["income", "age", "location", "demographic"]
                )
            elif agent_data["name"] == "Financial Analyzer":
                assert any(
                    term in primary_finding + key_insights_text
                    for term in ["financial", "value", "debt", "credit", "buying power"]
                )
            elif agent_data["name"] == "Risk Assessor":
                assert "risk" in primary_finding and str(sample_lead["risk_score"]) in primary_finding


def test_premium_value_demonstration():
    """Test that the showcase demonstrates sufficient value for $25K-$100K consulting."""
    showcase = PremiumSwarmShowcase()

    # Verify high-value features are present
    assert len(showcase.demo_agents) >= 10  # Sufficient agent specialization

    # Check agent specialties cover key business areas
    specialties = [agent["specialty"] for agent in showcase.demo_agents]
    specialty_text = " ".join(specialties).lower()

    required_areas = ["psychology", "financial", "risk", "negotiation", "market", "roi"]
    for area in required_areas:
        assert any(area in specialty_text for area in [area])

    # Verify high accuracy standards (justify premium pricing)
    for agent in showcase.demo_agents:
        assert agent["accuracy"] >= 85  # Minimum accuracy for enterprise
        assert agent["confidence"] >= 0.8  # High confidence levels

    # Check lead data shows high-value prospects
    for lead_name, lead_data in showcase.demo_leads.items():
        assert lead_data["roi_potential"] >= 200000  # High ROI potential
        assert lead_data["demographics"]["income"] >= 100000  # High-value prospects


def test_enterprise_grade_features():
    """Test that showcase includes enterprise-grade features."""
    showcase = PremiumSwarmShowcase()

    # Verify enterprise data quality
    assert all(isinstance(agent["accuracy"], (int, float)) for agent in showcase.demo_agents)
    assert all(agent["accuracy"] > 85 for agent in showcase.demo_agents)  # Enterprise standards

    # Check comprehensive lead profiling
    for lead_data in showcase.demo_leads.values():
        required_fields = ["demographics", "behavior", "intent", "risk_score", "roi_potential"]
        for field in required_fields:
            assert field in lead_data

        # Verify data depth
        assert len(lead_data["demographics"]) >= 4
        assert len(lead_data["behavior"]) >= 3
        assert len(lead_data["intent"]) >= 3


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_missing_lead_data_handling():
    """Test handling of missing or invalid lead data."""
    incomplete_lead = {
        "demographics": {"age": 35},  # Missing fields
        "behavior": {},  # Empty
        "intent": {"timeline": "unknown"},
        "risk_score": -1,  # Invalid
        "roi_potential": None,  # Invalid
    }

    agent = {"name": "Test Agent", "confidence": 0.85}

    # Should not crash with incomplete data
    try:
        insight = generate_agent_insight(agent, incomplete_lead, "Incomplete Lead")
        assert insight is not None
        assert "primary_finding" in insight
    except Exception as e:
        pytest.fail(f"generate_agent_insight failed with incomplete data: {e}")


def test_invalid_agent_configuration():
    """Test handling of invalid agent configurations."""
    invalid_agent = {"name": "", "confidence": 1.5}  # Invalid confidence
    valid_lead = {"demographics": {}, "behavior": {}, "intent": {}, "risk_score": 20, "roi_potential": 100000}

    try:
        insight = generate_agent_insight(invalid_agent, valid_lead, "Test Lead")
        assert insight is not None
    except Exception as e:
        pytest.fail(f"generate_agent_insight failed with invalid agent: {e}")


# ============================================================================
# Performance Tests
# ============================================================================


def test_showcase_initialization_performance():
    """Test that showcase initializes quickly for responsive UI."""
    import time

    start_time = time.time()

    with (
        patch.object(PremiumSwarmShowcase, "_get_swarm_service", return_value=None),
        patch.object(PremiumSwarmShowcase, "_get_lead_swarm", return_value=None),
    ):
        showcase = PremiumSwarmShowcase()

    initialization_time = time.time() - start_time

    # Should initialize within reasonable time for UI responsiveness
    assert initialization_time < 1.0  # Less than 1 second
    assert showcase is not None


def test_insight_generation_performance():
    """Test that insight generation is fast enough for real-time demo."""
    showcase = PremiumSwarmShowcase()
    sample_lead = showcase.demo_leads["Sarah Chen - Tech Executive"]

    import time

    start_time = time.time()

    # Generate insights for all agents
    insights = {}
    for agent in showcase.demo_agents:
        insights[agent["name"]] = generate_agent_insight(agent, sample_lead, "Performance Test")

    generation_time = time.time() - start_time

    # Should generate all insights quickly for smooth demo experience
    assert generation_time < 2.0  # Less than 2 seconds for all agents
    assert len(insights) == len(showcase.demo_agents)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])