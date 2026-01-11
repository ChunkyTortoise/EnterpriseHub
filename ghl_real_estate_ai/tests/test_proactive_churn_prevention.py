"""
Comprehensive Tests for Proactive Churn Prevention Orchestrator

Tests the 3-Stage Intervention Framework with focus on:
- Real-time churn monitoring (<30s latency)
- Stage-appropriate intervention selection
- Multi-channel delivery coordination
- Manager escalation protocols
- Performance metrics and business impact

Author: EnterpriseHub AI Platform
Last Updated: 2026-01-10
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from ghl_real_estate_ai.services.proactive_churn_prevention_orchestrator import (
    ProactiveChurnPreventionOrchestrator,
    InterventionStage,
    InterventionChannel,
    InterventionOutcome,
    ChurnRiskAssessment,
    InterventionAction,
    InterventionResult,
    EscalationResult,
    ProactivePreventionMetrics
)
from ghl_real_estate_ai.services.churn_prediction_service import (
    ChurnPrediction,
    ChurnRiskLevel,
    InterventionType as ChurnInterventionType,
    InterventionPriority,
    InterventionAction as ChurnInterventionAction,
    ChurnFactorExplanation
)
from ghl_real_estate_ai.models.lead_behavioral_features import LeadBehavioralFeatures


@pytest.fixture
def mock_churn_service():
    """Mock ChurnPredictionService"""
    service = AsyncMock()

    # Mock churn prediction
    service.predict_churn_risk = AsyncMock(return_value=ChurnPrediction(
        lead_id="test_lead_123",
        churn_probability=0.75,
        risk_level=ChurnRiskLevel.HIGH,
        confidence_score=0.85,
        model_version="v2.1.0",
        timestamp=datetime.now(),
        risk_factors=[
            ChurnFactorExplanation(
                factor_name="days_since_last_activity",
                contribution=0.3,
                current_value=14,
                healthy_range=(0, 7),
                explanation="No activity for 14 days",
                severity="high"
            )
        ],
        protective_factors=[],
        key_insights=["Lead engagement declining"],
        recommended_actions=[
            ChurnInterventionAction(
                action_type=ChurnInterventionType.PERSONALIZED_EMAIL,
                priority=InterventionPriority.HIGH,
                title="Send Market Update",
                description="Personalized market insights",
                expected_impact=0.6,
                effort_level="low",
                recommended_timing="Within 24 hours"
            )
        ],
        intervention_priority=InterventionPriority.HIGH,
        prediction_confidence=0.85,
        feature_quality=0.9,
        inference_time_ms=35.0,
        estimated_time_to_churn=10
    ))

    return service


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocketManager"""
    manager = AsyncMock()
    manager.websocket_hub = AsyncMock()
    manager.websocket_hub.broadcast_to_tenant = AsyncMock(return_value=MagicMock(
        connections_successful=5,
        connections_targeted=5,
        broadcast_time_ms=47.3
    ))
    return manager


@pytest.fixture
def mock_behavioral_engine():
    """Mock BehavioralWeightingEngine"""
    engine = Mock()
    return engine


@pytest.fixture
async def orchestrator(mock_churn_service, mock_websocket_manager, mock_behavioral_engine):
    """Create ProactiveChurnPreventionOrchestrator with mocked dependencies"""
    orch = ProactiveChurnPreventionOrchestrator(
        churn_service=mock_churn_service,
        websocket_manager=mock_websocket_manager,
        behavioral_engine=mock_behavioral_engine
    )

    # Mock cache manager
    orch.cache_manager = AsyncMock()
    orch.cache_manager.get = AsyncMock(return_value=None)
    orch.cache_manager.set = AsyncMock()

    # Don't start background workers for tests
    orch._workers_started = True

    return orch


# Test: Churn Risk Monitoring


@pytest.mark.asyncio
async def test_monitor_churn_risk_early_warning(orchestrator, mock_churn_service):
    """Test churn risk monitoring for early warning stage (>0.3 probability)"""
    # Update mock to return early warning level
    mock_churn_service.predict_churn_risk.return_value.churn_probability = 0.4
    mock_churn_service.predict_churn_risk.return_value.risk_level = ChurnRiskLevel.MEDIUM

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_123",
        tenant_id="tenant_001"
    )

    # Verify assessment
    assert assessment.lead_id == "test_lead_123"
    assert assessment.tenant_id == "tenant_001"
    assert assessment.churn_probability == 0.4
    assert assessment.intervention_stage == InterventionStage.EARLY_WARNING
    assert assessment.detection_latency_ms > 0

    # Verify metrics updated
    assert orchestrator.metrics.total_assessments == 1
    assert orchestrator.metrics.early_warning_count == 1


@pytest.mark.asyncio
async def test_monitor_churn_risk_active_risk(orchestrator, mock_churn_service):
    """Test churn risk monitoring for active risk stage (>0.6 probability)"""
    # Update mock to return active risk level
    mock_churn_service.predict_churn_risk.return_value.churn_probability = 0.7
    mock_churn_service.predict_churn_risk.return_value.risk_level = ChurnRiskLevel.HIGH

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_456",
        tenant_id="tenant_001"
    )

    assert assessment.churn_probability == 0.7
    assert assessment.intervention_stage == InterventionStage.ACTIVE_RISK
    assert orchestrator.metrics.active_risk_count == 1


@pytest.mark.asyncio
async def test_monitor_churn_risk_critical_risk(orchestrator, mock_churn_service):
    """Test churn risk monitoring for critical risk stage (>0.8 probability)"""
    # Update mock to return critical risk level
    mock_churn_service.predict_churn_risk.return_value.churn_probability = 0.85
    mock_churn_service.predict_churn_risk.return_value.risk_level = ChurnRiskLevel.CRITICAL

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_789",
        tenant_id="tenant_001"
    )

    assert assessment.churn_probability == 0.85
    assert assessment.intervention_stage == InterventionStage.CRITICAL_RISK
    assert orchestrator.metrics.critical_risk_count == 1


@pytest.mark.asyncio
async def test_monitor_churn_risk_caching(orchestrator):
    """Test churn risk assessment caching"""
    # First call - cache miss
    assessment1 = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_cache",
        tenant_id="tenant_001"
    )

    # Mock cache to return assessment
    orchestrator.cache_manager.get.return_value = assessment1

    # Second call - should use cache
    assessment2 = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_cache",
        tenant_id="tenant_001"
    )

    # Cache should have been checked
    assert orchestrator.cache_manager.get.called


@pytest.mark.asyncio
async def test_monitor_churn_risk_latency_target(orchestrator):
    """Test that churn risk detection meets <30s latency target"""
    start_time = asyncio.get_event_loop().time()

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_latency",
        tenant_id="tenant_001"
    )

    total_latency_seconds = asyncio.get_event_loop().time() - start_time

    # Verify latency targets
    assert assessment.detection_latency_ms < 100  # ML inference should be <100ms
    assert assessment.assessment_time_ms < 200   # Total assessment <200ms
    assert total_latency_seconds < 1.0           # Total time <1s (well under 30s target)


# Test: Intervention Triggering


@pytest.mark.asyncio
async def test_trigger_intervention_early_warning(orchestrator):
    """Test intervention triggering for early warning stage"""
    # First create assessment
    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_lead_intervention",
        tenant_id="tenant_001"
    )

    # Trigger intervention
    result = await orchestrator.trigger_intervention(
        lead_id="test_lead_intervention",
        tenant_id="tenant_001",
        stage=InterventionStage.EARLY_WARNING
    )

    # Verify result
    assert result.lead_id == "test_lead_intervention"
    assert result.outcome in [InterventionOutcome.DELIVERED, InterventionOutcome.PENDING]
    assert result.total_latency_ms > 0

    # Verify metrics
    assert orchestrator.metrics.total_interventions > 0


@pytest.mark.asyncio
async def test_trigger_intervention_active_risk_multi_channel(orchestrator):
    """Test active risk intervention with multi-channel delivery"""
    # Create active risk assessment
    orchestrator._monitored_leads["test_lead_multi"] = ChurnRiskAssessment(
        lead_id="test_lead_multi",
        tenant_id="tenant_001",
        assessment_id="assess_001",
        timestamp=datetime.now(),
        churn_probability=0.7,
        risk_level=ChurnRiskLevel.HIGH,
        intervention_stage=InterventionStage.ACTIVE_RISK,
        confidence_score=0.85,
        prediction=orchestrator.churn_service.predict_churn_risk.return_value,
        time_to_churn_days=7,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )

    result = await orchestrator.trigger_intervention(
        lead_id="test_lead_multi",
        tenant_id="tenant_001",
        stage=InterventionStage.ACTIVE_RISK
    )

    # Verify multi-channel execution
    assert result.outcome != InterventionOutcome.FAILED
    assert orchestrator.metrics.total_interventions > 0


@pytest.mark.asyncio
async def test_trigger_intervention_critical_risk_immediate(orchestrator):
    """Test critical risk intervention with immediate execution"""
    # Create critical risk assessment
    orchestrator._monitored_leads["test_lead_critical"] = ChurnRiskAssessment(
        lead_id="test_lead_critical",
        tenant_id="tenant_001",
        assessment_id="assess_002",
        timestamp=datetime.now(),
        churn_probability=0.9,
        risk_level=ChurnRiskLevel.CRITICAL,
        intervention_stage=InterventionStage.CRITICAL_RISK,
        confidence_score=0.9,
        prediction=orchestrator.churn_service.predict_churn_risk.return_value,
        time_to_churn_days=3,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )

    start_time = asyncio.get_event_loop().time()

    result = await orchestrator.trigger_intervention(
        lead_id="test_lead_critical",
        tenant_id="tenant_001",
        stage=InterventionStage.CRITICAL_RISK
    )

    execution_time = asyncio.get_event_loop().time() - start_time

    # Verify immediate execution (no delay)
    assert execution_time < 1.0  # Should execute in <1 second
    assert result.total_latency_ms < 1000


# Test: Manager Escalation


@pytest.mark.asyncio
async def test_escalate_to_manager_critical_risk(orchestrator):
    """Test manager escalation for critical risk leads"""
    # Create critical assessment
    orchestrator._monitored_leads["test_lead_escalate"] = ChurnRiskAssessment(
        lead_id="test_lead_escalate",
        tenant_id="tenant_001",
        assessment_id="assess_003",
        timestamp=datetime.now(),
        churn_probability=0.95,
        risk_level=ChurnRiskLevel.CRITICAL,
        intervention_stage=InterventionStage.CRITICAL_RISK,
        confidence_score=0.92,
        prediction=orchestrator.churn_service.predict_churn_risk.return_value,
        time_to_churn_days=2,
        behavioral_signals={"engagement_trend": "declining"},
        recent_engagement={"last_interaction_days": 14},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )

    escalation = await orchestrator.escalate_to_manager(
        lead_id="test_lead_escalate",
        tenant_id="tenant_001",
        context={"reason": "critical_churn_risk", "urgency": "immediate"}
    )

    # Verify escalation
    assert escalation.lead_id == "test_lead_escalate"
    assert escalation.escalated_to == "manager_tenant_001"
    assert escalation.urgency_level == "immediate"
    assert len(escalation.recommended_actions) > 0
    assert "churn_probability" in escalation.churn_context

    # Verify metrics
    assert orchestrator.metrics.escalations_count == 1


@pytest.mark.asyncio
async def test_escalation_cooldown_prevention(orchestrator):
    """Test escalation cooldown prevents duplicate escalations"""
    # First escalation
    escalation1 = await orchestrator.escalate_to_manager(
        lead_id="test_lead_cooldown",
        tenant_id="tenant_001",
        context={"reason": "test"}
    )

    assert escalation1.resolution_status != "blocked"

    # Immediate second escalation - should be blocked
    escalation2 = await orchestrator.escalate_to_manager(
        lead_id="test_lead_cooldown",
        tenant_id="tenant_001",
        context={"reason": "test2"}
    )

    assert escalation2.resolution_status == "blocked"
    assert escalation2.escalation_reason == "cooldown_active"


# Test: Performance Metrics


@pytest.mark.asyncio
async def test_get_prevention_metrics(orchestrator):
    """Test prevention metrics calculation"""
    # Simulate some activity
    await orchestrator.monitor_churn_risk("lead_1", "tenant_001")
    await orchestrator.monitor_churn_risk("lead_2", "tenant_001")

    orchestrator._monitored_leads["lead_test"] = ChurnRiskAssessment(
        lead_id="lead_test",
        tenant_id="tenant_001",
        assessment_id="assess_test",
        timestamp=datetime.now(),
        churn_probability=0.7,
        risk_level=ChurnRiskLevel.HIGH,
        intervention_stage=InterventionStage.ACTIVE_RISK,
        confidence_score=0.85,
        prediction=orchestrator.churn_service.predict_churn_risk.return_value,
        time_to_churn_days=7,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )

    await orchestrator.trigger_intervention("lead_test", "tenant_001", InterventionStage.ACTIVE_RISK)

    # Get metrics
    metrics = await orchestrator.get_prevention_metrics()

    # Verify metrics
    assert metrics.total_assessments > 0
    assert metrics.total_interventions > 0
    assert metrics.avg_detection_latency_ms >= 0
    assert metrics.avg_intervention_latency_ms >= 0
    assert metrics.active_monitoring_count >= 0


@pytest.mark.asyncio
async def test_intervention_success_rate_calculation(orchestrator):
    """Test intervention success rate calculation"""
    # Simulate successful intervention
    orchestrator.metrics.total_interventions = 10
    orchestrator.metrics.successful_interventions = 7
    orchestrator.metrics.failed_interventions = 3

    metrics = await orchestrator.get_prevention_metrics()

    assert metrics.avg_success_rate == 0.7  # 70% success rate


@pytest.mark.asyncio
async def test_business_impact_metrics(orchestrator):
    """Test business impact metrics calculation"""
    # Simulate churn prevention
    orchestrator.metrics.churn_prevented_count = 10
    orchestrator.metrics.total_interventions = 100

    metrics = await orchestrator.get_prevention_metrics()

    # Verify business impact calculations
    assert metrics.estimated_revenue_saved > 0
    assert metrics.intervention_roi > 0


# Test: Detection-to-Intervention Latency


@pytest.mark.asyncio
async def test_end_to_end_latency_target(orchestrator):
    """Test end-to-end detection-to-intervention latency meets <30s target"""
    start_time = asyncio.get_event_loop().time()

    # Full cycle: monitor -> trigger intervention
    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_latency_e2e",
        tenant_id="tenant_001"
    )

    result = await orchestrator.trigger_intervention(
        lead_id="test_latency_e2e",
        tenant_id="tenant_001",
        stage=assessment.intervention_stage
    )

    total_latency = asyncio.get_event_loop().time() - start_time

    # Verify <30 second target (should be much faster)
    assert total_latency < 30.0
    assert result.total_latency_ms < 30000  # <30 seconds in milliseconds

    # Verify sub-second performance (realistic target)
    assert total_latency < 1.0  # Should complete in <1 second


@pytest.mark.asyncio
async def test_parallel_monitoring_performance(orchestrator):
    """Test parallel monitoring of multiple leads meets performance targets"""
    lead_ids = [f"lead_{i}" for i in range(10)]

    start_time = asyncio.get_event_loop().time()

    # Monitor multiple leads in parallel
    tasks = [
        orchestrator.monitor_churn_risk(lead_id, "tenant_001")
        for lead_id in lead_ids
    ]

    assessments = await asyncio.gather(*tasks)

    total_time = asyncio.get_event_loop().time() - start_time

    # Verify all assessments completed
    assert len(assessments) == 10

    # Verify parallel execution is faster than sequential
    # (should be <5 seconds for 10 leads, vs 10+ seconds sequential)
    assert total_time < 5.0

    # Verify average per-lead time
    avg_time_per_lead = total_time / len(lead_ids)
    assert avg_time_per_lead < 1.0


# Test: Stage Determination


def test_stage_determination_thresholds(orchestrator):
    """Test intervention stage determination based on probability thresholds"""
    # Early warning: 0.3 - 0.6
    assert orchestrator._determine_intervention_stage(0.3) == InterventionStage.EARLY_WARNING
    assert orchestrator._determine_intervention_stage(0.5) == InterventionStage.EARLY_WARNING

    # Active risk: 0.6 - 0.8
    assert orchestrator._determine_intervention_stage(0.6) == InterventionStage.ACTIVE_RISK
    assert orchestrator._determine_intervention_stage(0.75) == InterventionStage.ACTIVE_RISK

    # Critical risk: >0.8
    assert orchestrator._determine_intervention_stage(0.8) == InterventionStage.CRITICAL_RISK
    assert orchestrator._determine_intervention_stage(0.95) == InterventionStage.CRITICAL_RISK


# Test: Channel Selection


def test_channel_selection_by_stage(orchestrator):
    """Test channel selection based on intervention stage and action type"""
    # Email for early warning
    channel = orchestrator._select_channel(
        ChurnInterventionType.PERSONALIZED_EMAIL,
        InterventionStage.EARLY_WARNING
    )
    assert channel == InterventionChannel.EMAIL

    # SMS override for active risk
    channel = orchestrator._select_channel(
        ChurnInterventionType.PERSONALIZED_EMAIL,
        InterventionStage.ACTIVE_RISK
    )
    assert channel == InterventionChannel.SMS

    # Phone for critical actions
    channel = orchestrator._select_channel(
        ChurnInterventionType.IMMEDIATE_CALL,
        InterventionStage.CRITICAL_RISK
    )
    assert channel == InterventionChannel.PHONE


# Test: Intervention Cost Estimation


def test_intervention_cost_estimation(orchestrator):
    """Test intervention cost estimation for ROI calculation"""
    # Low cost interventions
    assert orchestrator._estimate_intervention_cost(ChurnInterventionType.PERSONALIZED_EMAIL) < 1.0

    # Medium cost interventions
    assert orchestrator._estimate_intervention_cost(ChurnInterventionType.SPECIAL_OFFER) == 2.0

    # High cost interventions
    assert orchestrator._estimate_intervention_cost(ChurnInterventionType.AGENT_ESCALATION) >= 10.0


# Test: Error Handling


@pytest.mark.asyncio
async def test_monitor_churn_risk_service_failure(orchestrator, mock_churn_service):
    """Test graceful handling of churn service failure"""
    # Mock service failure
    mock_churn_service.predict_churn_risk.side_effect = Exception("Service unavailable")

    assessment = await orchestrator.monitor_churn_risk(
        lead_id="test_failure",
        tenant_id="tenant_001"
    )

    # Should return fallback assessment
    assert assessment.lead_id == "test_failure"
    assert assessment.churn_probability == 0.5  # Fallback value
    assert assessment.confidence_score == 0.3   # Low confidence


@pytest.mark.asyncio
async def test_intervention_partial_failure(orchestrator):
    """Test handling of partial intervention failure (some channels succeed)"""
    # This would test multi-channel delivery where some channels fail
    # Implementation depends on actual channel integrations
    pass


# Integration Tests


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow_early_warning_to_prevention(orchestrator):
    """Integration test: Full workflow from early warning detection to successful prevention"""
    # 1. Detect early warning
    assessment = await orchestrator.monitor_churn_risk(
        lead_id="integration_test_lead",
        tenant_id="tenant_001"
    )

    assert assessment.intervention_stage in [
        InterventionStage.EARLY_WARNING,
        InterventionStage.ACTIVE_RISK,
        InterventionStage.CRITICAL_RISK
    ]

    # 2. Trigger intervention
    result = await orchestrator.trigger_intervention(
        lead_id="integration_test_lead",
        tenant_id="tenant_001",
        stage=assessment.intervention_stage
    )

    assert result.outcome in [InterventionOutcome.DELIVERED, InterventionOutcome.PENDING]

    # 3. Verify metrics updated
    metrics = await orchestrator.get_prevention_metrics()
    assert metrics.total_assessments >= 1
    assert metrics.total_interventions >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_critical_risk_escalation_workflow(orchestrator):
    """Integration test: Critical risk detection to manager escalation"""
    # 1. Create critical risk
    orchestrator._monitored_leads["critical_integration"] = ChurnRiskAssessment(
        lead_id="critical_integration",
        tenant_id="tenant_001",
        assessment_id="int_assess",
        timestamp=datetime.now(),
        churn_probability=0.95,
        risk_level=ChurnRiskLevel.CRITICAL,
        intervention_stage=InterventionStage.CRITICAL_RISK,
        confidence_score=0.95,
        prediction=orchestrator.churn_service.predict_churn_risk.return_value,
        time_to_churn_days=1,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )

    # 2. Attempt intervention
    result = await orchestrator.trigger_intervention(
        lead_id="critical_integration",
        tenant_id="tenant_001",
        stage=InterventionStage.CRITICAL_RISK
    )

    # 3. Escalate to manager
    escalation = await orchestrator.escalate_to_manager(
        lead_id="critical_integration",
        tenant_id="tenant_001",
        context={"reason": "critical_churn_risk"}
    )

    assert escalation.lead_id == "critical_integration"
    assert escalation.urgency_level != "blocked"
    assert len(escalation.recommended_actions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
