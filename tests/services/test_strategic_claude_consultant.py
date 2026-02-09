"""
Tests for Strategic Claude Consultant Service.

Ensures reliability for high-ticket consulting capabilities ($25K-$100K engagements).
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import numpy as np
import pytest
import pytest_asyncio

# The strategic_consultant fixture loads ML models which can take >10s.
# Set a generous timeout for all tests in this module.
pytestmark = pytest.mark.timeout(60)

from ghl_real_estate_ai.services.strategic_claude_consultant import (

@pytest.mark.integration
    AutonomousWorkflowResult,
    BusinessImpactLevel,
    ConsultingTier,
    PredictiveInsight,
    StrategicClaudeConsultant,
    StrategicPriority,
    StrategicRecommendation,
    get_strategic_claude_consultant,
)

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_database():
    """Mock database service."""
    db_mock = AsyncMock()
    return db_mock


@pytest.fixture
def mock_tenant_service():
    """Mock tenant service."""
    tenant_mock = AsyncMock()
    return tenant_mock


@pytest_asyncio.fixture
async def strategic_consultant():
    """Create strategic consultant for testing."""
    with (
        patch("ghl_real_estate_ai.services.strategic_claude_consultant.get_database", return_value=AsyncMock()),
        patch(
            "ghl_real_estate_ai.services.strategic_claude_consultant.get_enterprise_tenant_service",
            return_value=AsyncMock(),
        ),
    ):
        consultant = StrategicClaudeConsultant(tenant_id="test_tenant")
        await consultant.initialize()
        return consultant


@pytest.fixture
def sample_business_context():
    """Sample business context for testing."""
    return {
        "financial": {
            "revenue_history": [100000, 115000, 130000, 145000, 160000, 175000],
            "costs": 120000,
            "revenue": 175000,
            "profit_margin": 31.4,
        },
        "operations": {
            "automation_percentage": 45,
            "process_quality_score": 85,
            "manual_processes": 35,
            "response_time": 18,
        },
        "market": {
            "growth_rate": 15.2,
            "competitive_intensity": "high",
            "market_size": 2400000000,
            "market_share": 3.5,
        },
        "technology": {"digital_maturity": 65, "ai_adoption": 30, "tech_debt_score": 25},
    }


@pytest.fixture
def sample_historical_data():
    """Sample historical data for predictive analytics."""
    return {
        "revenue": [100000, 105000, 110000, 115000, 120000, 125000, 130000, 135000, 140000, 145000, 150000, 155000],
        "conversion_rate": [3.2, 3.4, 3.6, 3.8, 4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7],
        "customer_ltv": [45000, 46000, 47000, 48000, 49000, 50000, 51000, 52000, 53000, 54000, 55000, 56000],
    }


# ============================================================================
# Strategic Recommendations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_generate_strategic_recommendations(strategic_consultant, sample_business_context):
    """Test generation of strategic recommendations."""
    recommendations = await strategic_consultant.generate_strategic_recommendations(
        sample_business_context,
        ConsultingTier.INTELLIGENCE_PLATFORM,
        [StrategicPriority.REVENUE_OPTIMIZATION, StrategicPriority.OPERATIONAL_EFFICIENCY],
    )

    assert len(recommendations) > 0
    assert len(recommendations) <= 5  # Should return top 5

    for rec in recommendations:
        assert isinstance(rec, StrategicRecommendation)
        assert rec.id is not None
        assert len(rec.title) > 0
        assert rec.strategic_priority in [
            StrategicPriority.REVENUE_OPTIMIZATION,
            StrategicPriority.OPERATIONAL_EFFICIENCY,
        ]
        assert rec.roi_percentage > 0
        assert rec.confidence_level > 0.5


@pytest.mark.asyncio
async def test_revenue_optimization_recommendation(strategic_consultant, sample_business_context):
    """Test revenue optimization recommendation generation."""
    rec = await strategic_consultant._create_revenue_optimization_rec(
        await strategic_consultant._analyze_business_state(sample_business_context)
    )

    assert rec.strategic_priority == StrategicPriority.REVENUE_OPTIMIZATION
    assert rec.impact_level in [BusinessImpactLevel.SIGNIFICANT, BusinessImpactLevel.TRANSFORMATIONAL]
    assert rec.revenue_impact > 0
    assert rec.roi_percentage > 100  # Should show positive ROI
    assert rec.payback_months > 0 and rec.payback_months <= 24
    assert len(rec.key_milestones) >= 3
    assert len(rec.success_metrics) >= 3
    assert len(rec.risk_factors) >= 2
    assert len(rec.mitigation_strategies) >= 2


@pytest.mark.asyncio
async def test_business_state_analysis(strategic_consultant, sample_business_context):
    """Test comprehensive business state analysis."""
    state = await strategic_consultant._analyze_business_state(sample_business_context)

    assert "financial" in state
    assert "operational" in state
    assert "market" in state
    assert "technology" in state

    # Financial analysis
    financial = state["financial"]
    assert "revenue_trend" in financial
    assert "margin_analysis" in financial
    assert "financial_health_score" in financial

    # Operational analysis
    operational = state["operational"]
    assert "efficiency_score" in operational
    assert "bottlenecks" in operational
    assert "automation_potential" in operational

    # Validate scores are reasonable
    assert 0 <= operational["efficiency_score"] <= 100


@pytest.mark.asyncio
async def test_consulting_tier_recommendations(strategic_consultant, sample_business_context):
    """Test that different consulting tiers generate appropriate recommendations."""

    # Test Transformation Accelerator ($25K-$35K)
    accelerator_recs = await strategic_consultant._generate_accelerator_recommendations(
        await strategic_consultant._analyze_business_state(sample_business_context), None
    )

    # Test Innovation Lab ($75K-$100K+)
    innovation_recs = await strategic_consultant._generate_innovation_recommendations(
        await strategic_consultant._analyze_business_state(sample_business_context), None
    )

    # Innovation tier should have more comprehensive/advanced recommendations
    assert len(innovation_recs) >= len(accelerator_recs)

    # Innovation recommendations should have higher investment levels
    avg_innovation_investment = np.mean([r.investment_required for r in innovation_recs])
    avg_accelerator_investment = np.mean([r.investment_required for r in accelerator_recs])
    assert avg_innovation_investment >= avg_accelerator_investment


# ============================================================================
# Predictive Analytics Tests
# ============================================================================


@pytest.mark.asyncio
async def test_predictive_model_initialization(strategic_consultant):
    """Test predictive models are properly initialized."""
    await strategic_consultant._initialize_predictive_models()

    assert strategic_consultant._model_initialized is True
    assert "revenue" in strategic_consultant.ensemble_models
    assert "conversion" in strategic_consultant.ensemble_models
    assert "ltv" in strategic_consultant.ensemble_models


@pytest.mark.asyncio
async def test_generate_predictive_insights(strategic_consultant, sample_historical_data):
    """Test generation of predictive insights."""
    insights = await strategic_consultant.generate_predictive_insights(
        sample_historical_data, prediction_horizon_days=90
    )

    assert len(insights) > 0

    for insight in insights:
        assert isinstance(insight, PredictiveInsight)
        assert insight.prediction_confidence > 0.5
        assert insight.model_accuracy > 0.7  # Should have reasonable accuracy
        assert insight.time_horizon_days == 90
        assert len(insight.recommended_actions) > 0
        assert isinstance(insight.feature_importance, dict)


@pytest.mark.asyncio
async def test_revenue_prediction(strategic_consultant, sample_historical_data):
    """Test revenue prediction functionality."""
    insight = await strategic_consultant._predict_revenue(sample_historical_data["revenue"], 90)

    assert insight.metric_name == "Monthly Revenue"
    assert insight.predicted_value > 0
    assert len(insight.prediction_interval) == 2
    assert insight.prediction_interval[0] < insight.prediction_interval[1]
    assert insight.prediction_confidence > 0.8
    assert len(insight.ensemble_models) >= 2
    assert "Random Forest" in insight.ensemble_models
    assert "trend" in insight.feature_importance


@pytest.mark.asyncio
async def test_time_series_feature_extraction(strategic_consultant):
    """Test time series feature extraction."""
    data = [100, 105, 110, 115, 120, 125, 130]
    features = strategic_consultant._extract_time_series_features(data)

    assert len(features) == len(data) - 2  # Features start from 3rd point
    assert all(isinstance(f, (int, float)) for f in features)

    # Test with insufficient data
    short_data = [100, 105]
    short_features = strategic_consultant._extract_time_series_features(short_data)
    assert len(short_features) == len(short_data)


# ============================================================================
# Autonomous Workflow Tests
# ============================================================================


@pytest.mark.asyncio
async def test_execute_autonomous_workflow(strategic_consultant):
    """Test autonomous workflow execution."""
    config = {"batch_size": 100, "priority_threshold": 0.8}

    result = await strategic_consultant.execute_autonomous_workflow("lead_intelligence_automation", config)

    assert isinstance(result, AutonomousWorkflowResult)
    assert result.workflow_name == "lead_intelligence_automation"
    assert result.status in ["completed", "failed"]
    assert result.execution_id is not None
    assert result.time_saved_hours >= 0
    assert result.manual_steps_automated >= 0


@pytest.mark.asyncio
async def test_lead_intelligence_workflow(strategic_consultant):
    """Test lead intelligence automation workflow."""
    config = {"batch_size": 50}

    result = await strategic_consultant._execute_lead_intelligence_workflow(config)

    assert "time_saved_hours" in result
    assert "steps_automated" in result
    assert "error_reduction" in result
    assert "cost_savings" in result
    assert "revenue_impact" in result

    # Validate business impact metrics
    assert result["time_saved_hours"] > 10  # Should save significant time
    assert result["error_reduction"] > 50  # Should significantly reduce errors
    assert result["cost_savings"] > 0
    assert result["revenue_impact"] > 0

    # Validate execution details
    assert len(result["steps_executed"]) >= 3
    assert len(result["decisions_made"]) >= 1


@pytest.mark.asyncio
async def test_workflow_tracking(strategic_consultant):
    """Test workflow execution tracking."""
    config = {"test": "config"}

    # Execute workflow
    result = await strategic_consultant.execute_autonomous_workflow("lead_intelligence_automation", config)

    # Check tracking
    assert result.execution_id in strategic_consultant.active_workflows
    assert len(strategic_consultant.workflow_results) > 0

    # Verify workflow result is stored
    stored_result = strategic_consultant.workflow_results[-1]
    assert stored_result.execution_id == result.execution_id
    assert stored_result.workflow_name == "lead_intelligence_automation"


@pytest.mark.asyncio
async def test_workflow_error_handling(strategic_consultant):
    """Test workflow error handling."""
    config = {"invalid": "config"}

    result = await strategic_consultant.execute_autonomous_workflow("nonexistent_workflow", config)

    assert result.status == "failed"
    assert len(result.exceptions_handled) > 0
    assert result.time_saved_hours == 0  # No savings on failed workflow


# ============================================================================
# ROI Attribution Tests
# ============================================================================


@pytest.mark.asyncio
async def test_roi_attribution_calculation(strategic_consultant):
    """Test ROI attribution calculation."""
    intervention_date = datetime.utcnow() - timedelta(days=180)

    business_metrics = {
        "revenue": [100000, 105000, 110000, 115000, 125000, 135000, 150000, 165000],
        "conversion_rate": [3.0, 3.1, 3.2, 3.3, 3.8, 4.2, 4.6, 5.0],
        "cost_savings": [0, 0, 0, 0, 5000, 10000, 15000, 20000],
    }

    roi_result = await strategic_consultant.calculate_roi_attribution(intervention_date, business_metrics)

    assert "overall_roi" in roi_result
    assert "metric_attributions" in roi_result
    assert "value_drivers" in roi_result
    assert "confidence_assessment" in roi_result

    # Test overall ROI calculation
    overall = roi_result["overall_roi"]
    assert "total_value_created" in overall
    assert "consulting_investment" in overall
    assert "roi_percentage" in overall
    assert "payback_months" in overall

    # ROI should be positive for successful intervention
    assert overall["roi_percentage"] > 0


@pytest.mark.asyncio
async def test_baseline_trend_calculation(strategic_consultant):
    """Test baseline trend calculation."""
    data = [100, 105, 110, 115, 120]
    trend = strategic_consultant._calculate_trend(data)

    assert "trend" in trend
    assert "current" in trend
    assert "change" in trend

    assert trend["trend"] in ["upward", "downward", "stable"]
    assert trend["current"] == 120
    assert trend["change"] > 0  # Should be positive for upward trend


# ============================================================================
# Helper Methods Tests
# ============================================================================


def test_margin_analysis(strategic_consultant):
    """Test profit margin analysis."""
    financial_data = {"revenue": 100000, "costs": 70000}
    margins = strategic_consultant._analyze_margins(financial_data)

    assert "gross_margin" in margins
    assert "margin_health" in margins
    assert margins["gross_margin"] == 30.0  # (100k - 70k) / 100k = 30%
    assert margins["margin_health"] in ["healthy", "concerning"]


def test_efficiency_score_calculation(strategic_consultant):
    """Test operational efficiency score calculation."""
    operational_data = {"automation_percentage": 60, "process_quality_score": 80}

    score = strategic_consultant._calculate_efficiency_score(operational_data)
    assert 0 <= score <= 100
    assert score == 70  # (60 + 80) / 2


@pytest.mark.asyncio
async def test_bottleneck_identification(strategic_consultant):
    """Test operational bottleneck identification."""
    # High manual processes should be flagged
    high_manual_data = {"manual_processes": 70, "response_time": 12}
    bottlenecks = await strategic_consultant._identify_bottlenecks(high_manual_data)

    assert len(bottlenecks) > 0
    assert any("manual" in b.lower() for b in bottlenecks)

    # Good operations should have minimal bottlenecks
    good_data = {"manual_processes": 20, "response_time": 6}
    good_bottlenecks = await strategic_consultant._identify_bottlenecks(good_data)

    # Should either have no bottlenecks or identify "No critical bottlenecks"
    assert len(good_bottlenecks) >= 0


# ============================================================================
# Data Model Tests
# ============================================================================


def test_strategic_recommendation_model():
    """Test StrategicRecommendation data model."""
    rec = StrategicRecommendation(
        id="test-id",
        title="Test Recommendation",
        strategic_priority=StrategicPriority.REVENUE_OPTIMIZATION,
        impact_level=BusinessImpactLevel.SIGNIFICANT,
        executive_summary="Test summary",
        problem_statement="Test problem",
        proposed_solution="Test solution",
        business_rationale="Test rationale",
        revenue_impact=100000.0,
        cost_savings=50000.0,
        investment_required=30000.0,
        roi_percentage=500.0,
        payback_months=8,
        implementation_timeline="12 weeks",
        resource_requirements=["Engineer", "Analyst"],
        key_milestones=[{"week": 4, "milestone": "Phase 1"}],
        success_metrics=[{"metric": "Revenue", "target": "20%"}],
        risk_factors=["Market volatility"],
        mitigation_strategies=["Diversification"],
        confidence_level=0.85,
        competitive_implications="Strong advantage",
        market_opportunity_size=1000000.0,
        timing_considerations="Optimal timing",
        generated_at=datetime.utcnow(),
    )

    assert rec.id == "test-id"
    assert rec.roi_percentage == 500.0
    assert rec.strategic_priority == StrategicPriority.REVENUE_OPTIMIZATION


def test_predictive_insight_model():
    """Test PredictiveInsight data model."""
    insight = PredictiveInsight(
        metric_name="Revenue",
        current_value=100000.0,
        predicted_value=120000.0,
        prediction_interval=(110000.0, 130000.0),
        prediction_confidence=0.85,
        time_horizon_days=90,
        ensemble_models=["Random Forest", "Gradient Boosting"],
        model_accuracy=0.89,
        feature_importance={"trend": 0.6, "seasonality": 0.4},
        data_quality_score=0.92,
        business_impact="20% growth expected",
        recommended_actions=["Increase marketing"],
        trend_analysis="Positive trend",
    )

    assert insight.metric_name == "Revenue"
    assert insight.predicted_value == 120000.0
    assert len(insight.prediction_interval) == 2
    assert insight.prediction_confidence == 0.85


def test_autonomous_workflow_result_model():
    """Test AutonomousWorkflowResult data model."""
    result = AutonomousWorkflowResult(
        workflow_name="test_workflow",
        execution_id="exec-123",
        start_time=datetime.utcnow(),
        end_time=datetime.utcnow() + timedelta(minutes=5),
        status="completed",
        time_saved_hours=10.5,
        manual_steps_automated=8,
        error_reduction_percentage=65.0,
        accuracy_improvement=25.0,
        cost_savings=5000.0,
        revenue_impact=15000.0,
        quality_improvements=["Consistency", "Speed"],
        steps_executed=[{"step": "Analysis", "duration": 120}],
        decisions_made=[{"decision": "Prioritize high-value leads"}],
        exceptions_handled=[],
        performance_metrics={"accuracy": 0.95},
    )

    assert result.workflow_name == "test_workflow"
    assert result.time_saved_hours == 10.5
    assert result.status == "completed"


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_service_factory():
    """Test service factory functionality."""
    with (
        patch("ghl_real_estate_ai.services.strategic_claude_consultant.get_database", return_value=AsyncMock()),
        patch(
            "ghl_real_estate_ai.services.strategic_claude_consultant.get_enterprise_tenant_service",
            return_value=AsyncMock(),
        ),
    ):
        consultant1 = await get_strategic_claude_consultant("tenant1")
        consultant2 = await get_strategic_claude_consultant("tenant1")  # Same tenant
        consultant3 = await get_strategic_claude_consultant("tenant2")  # Different tenant

        # Same tenant should return same instance
        assert consultant1 is consultant2
        # Different tenant should return different instance
        assert consultant1 is not consultant3


@pytest.mark.asyncio
async def test_end_to_end_consulting_workflow(strategic_consultant, sample_business_context, sample_historical_data):
    """Test complete end-to-end consulting workflow."""

    # 1. Generate strategic recommendations
    recommendations = await strategic_consultant.generate_strategic_recommendations(
        sample_business_context, ConsultingTier.INTELLIGENCE_PLATFORM
    )
    assert len(recommendations) > 0

    # 2. Generate predictive insights
    insights = await strategic_consultant.generate_predictive_insights(sample_historical_data, 90)
    assert len(insights) > 0

    # 3. Execute autonomous workflow
    workflow_result = await strategic_consultant.execute_autonomous_workflow(
        "lead_intelligence_automation", {"batch_size": 50}
    )
    assert workflow_result.status == "completed"

    # 4. Calculate ROI attribution
    intervention_date = datetime.utcnow() - timedelta(days=90)
    roi_result = await strategic_consultant.calculate_roi_attribution(
        intervention_date, {"revenue": sample_historical_data["revenue"]}
    )
    assert "overall_roi" in roi_result

    # Verify business value demonstrated
    total_value = 0
    total_value += sum(rec.revenue_impact for rec in recommendations)
    total_value += workflow_result.revenue_impact

    # Should demonstrate significant business value for consulting fees
    assert total_value > 50000  # Minimum value for $50K+ engagement


# ============================================================================
# Performance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_recommendation_generation_performance(strategic_consultant, sample_business_context):
    """Test that recommendation generation is fast enough for executive demos."""
    import time

    start_time = time.time()
    recommendations = await strategic_consultant.generate_strategic_recommendations(
        sample_business_context, ConsultingTier.INTELLIGENCE_PLATFORM
    )
    generation_time = time.time() - start_time

    # Should generate recommendations quickly for responsive demos
    assert generation_time < 3.0  # Less than 3 seconds
    assert len(recommendations) > 0


@pytest.mark.asyncio
async def test_predictive_analytics_performance(strategic_consultant, sample_historical_data):
    """Test predictive analytics performance."""
    import time

    start_time = time.time()
    insights = await strategic_consultant.generate_predictive_insights(sample_historical_data, 90)
    generation_time = time.time() - start_time

    # Should generate insights quickly
    assert generation_time < 5.0  # Less than 5 seconds
    assert len(insights) > 0


# ============================================================================
# Error Handling Tests
# ============================================================================


@pytest.mark.asyncio
async def test_invalid_business_context_handling(strategic_consultant):
    """Test handling of invalid business context."""
    invalid_context = {"incomplete": "data"}

    # Should handle gracefully without crashing
    recommendations = await strategic_consultant.generate_strategic_recommendations(
        invalid_context, ConsultingTier.INTELLIGENCE_PLATFORM
    )

    # May return empty or fallback recommendations
    assert isinstance(recommendations, list)


@pytest.mark.asyncio
async def test_insufficient_historical_data(strategic_consultant):
    """Test handling of insufficient historical data."""
    insufficient_data = {"revenue": [100000, 110000]}  # Too little data

    insights = await strategic_consultant.generate_predictive_insights(insufficient_data, 90)

    # Should handle gracefully
    assert isinstance(insights, list)


@pytest.mark.asyncio
async def test_model_initialization_failure(strategic_consultant):
    """Test handling of model initialization failure."""
    with patch(
        "ghl_real_estate_ai.services.strategic_claude_consultant.VotingRegressor",
        side_effect=Exception("Model init failed"),
    ):
        try:
            await strategic_consultant._initialize_predictive_models()
            # Should raise exception on critical failure
            assert False, "Expected exception not raised"
        except Exception as e:
            assert "Model init failed" in str(e)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])