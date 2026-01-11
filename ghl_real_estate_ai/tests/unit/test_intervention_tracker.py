"""
Unit Tests for Intervention Tracking System

Comprehensive test coverage for intervention lifecycle tracking, success rate analytics,
business impact measurement, and real-time monitoring.

Test Coverage:
- Intervention lifecycle tracking (initiation → delivery → engagement → outcome)
- Success rate calculation by stage, channel, and segment
- Business impact measurement (churn reduction, revenue protection, ROI)
- Manager escalation tracking and resolution
- Performance analytics generation
- Real-time updates and broadcasting
- Historical data analysis
- Data persistence and caching

Author: EnterpriseHub AI Platform
Last Updated: 2026-01-10
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.intervention_tracker import (
    InterventionTracker,
    InterventionOutcome,
    TrackingStatus,
    SuccessMetric,
    InterventionRecord,
    InterventionAnalytics,
    BusinessImpactReport,
    ChannelPerformance,
    StagePerformance,
    get_intervention_tracker
)
from ghl_real_estate_ai.services.proactive_churn_prevention_orchestrator import (
    InterventionStage,
    InterventionChannel,
    InterventionAction,
    ChurnRiskAssessment,
    InterventionPriority,
    InterventionType as ChurnInterventionType
)
from ghl_real_estate_ai.services.multi_channel_notification_service import (
    NotificationChannel,
    NotificationResult,
    DeliveryStatus,
    ChannelDeliveryResult
)
from ghl_real_estate_ai.services.churn_prediction_service import (
    ChurnRiskLevel,
    ChurnPrediction
)


@pytest.fixture
def sample_intervention_action():
    """Create sample intervention action for testing"""
    return InterventionAction(
        action_id="action_test123",
        lead_id="lead_test456",
        tenant_id="tenant_test789",
        stage=InterventionStage.ACTIVE_RISK,
        channel=InterventionChannel.EMAIL,
        action_type=ChurnInterventionType.PERSONALIZED_EMAIL,
        priority=InterventionPriority.HIGH,
        title="Re-engagement Email",
        message_template="Test template",
        personalization_data={},
        scheduled_time=datetime.now(),
        execution_deadline=datetime.now() + timedelta(hours=24),
        expected_success_rate=0.6,
        intervention_cost=5.0,
        roi_score=10.0
    )


@pytest.fixture
def sample_risk_assessment():
    """Create sample churn risk assessment for testing"""
    return ChurnRiskAssessment(
        lead_id="lead_test456",
        tenant_id="tenant_test789",
        assessment_id="assess_test123",
        timestamp=datetime.now(),
        churn_probability=0.65,
        risk_level=ChurnRiskLevel.HIGH,
        intervention_stage=InterventionStage.ACTIVE_RISK,
        confidence_score=0.85,
        prediction=None,
        time_to_churn_days=14,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=35.0,
        assessment_time_ms=50.0
    )


@pytest.fixture
def sample_notification_result():
    """Create sample notification result for testing"""
    return NotificationResult(
        request_id="req_test123",
        notification_id="notif_test456",
        overall_status=DeliveryStatus.DELIVERED,
        successful_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        failed_channels=[],
        channel_results={
            NotificationChannel.EMAIL: ChannelDeliveryResult(
                channel=NotificationChannel.EMAIL,
                status=DeliveryStatus.DELIVERED,
                delivery_time_ms=120.0,
                provider="sendgrid",
                attempts=1
            ),
            NotificationChannel.SMS: ChannelDeliveryResult(
                channel=NotificationChannel.SMS,
                status=DeliveryStatus.DELIVERED,
                delivery_time_ms=80.0,
                provider="twilio",
                attempts=1
            )
        },
        total_delivery_time_ms=250.0,
        parallel_delivery=True,
        requested_at=datetime.now(),
        completed_at=datetime.now()
    )


@pytest.fixture
async def intervention_tracker():
    """Create intervention tracker instance for testing"""
    # Mock dependencies
    mock_orchestrator = AsyncMock()
    mock_notification_service = AsyncMock()
    mock_websocket_manager = AsyncMock()
    mock_websocket_manager.websocket_hub = AsyncMock()
    mock_churn_service = AsyncMock()

    tracker = InterventionTracker(
        orchestrator=mock_orchestrator,
        notification_service=mock_notification_service,
        websocket_manager=mock_websocket_manager,
        churn_service=mock_churn_service
    )

    # Mock cache manager
    with patch('ghl_real_estate_ai.services.intervention_tracker.get_cache_manager'):
        with patch.object(tracker.redis_client, 'initialize', new_callable=AsyncMock):
            with patch.object(tracker, '_load_historical_data', new_callable=AsyncMock):
                with patch.object(tracker, '_start_background_workers', new_callable=AsyncMock):
                    await tracker.initialize()

    yield tracker


class TestInterventionLifecycleTracking:
    """Test intervention lifecycle tracking"""

    @pytest.mark.asyncio
    async def test_track_intervention_start(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking intervention initiation"""
        # Track intervention start
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Verify tracking ID created
        assert tracking_id is not None
        assert tracking_id.startswith("track_")

        # Verify record created
        assert tracking_id in intervention_tracker._active_interventions

        # Verify record details
        record = intervention_tracker._active_interventions[tracking_id]
        assert record.lead_id == sample_intervention_action.lead_id
        assert record.stage == InterventionStage.ACTIVE_RISK
        assert record.tracking_status == TrackingStatus.INITIATED
        assert record.churn_probability == 0.65

    @pytest.mark.asyncio
    async def test_track_intervention_delivery(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment,
        sample_notification_result
    ):
        """Test tracking intervention delivery"""
        # Start tracking
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track delivery
        await intervention_tracker.track_intervention_delivery(
            tracking_id,
            sample_notification_result
        )

        # Verify delivery tracked
        record = intervention_tracker._active_interventions[tracking_id]
        assert record.tracking_status == TrackingStatus.DELIVERED
        assert record.delivered_at is not None
        assert len(record.channels_successful) == 2
        assert NotificationChannel.EMAIL in record.channels_successful
        assert record.success_metrics[SuccessMetric.DELIVERY_SUCCESS] is True

    @pytest.mark.asyncio
    async def test_track_intervention_engagement(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking lead engagement with intervention"""
        # Start tracking
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track engagement
        engagement_data = {
            "channel": "email",
            "opened_at": datetime.now().isoformat(),
            "device": "mobile"
        }

        await intervention_tracker.track_intervention_engagement(
            tracking_id,
            "opened",
            engagement_data
        )

        # Verify engagement tracked
        record = intervention_tracker._active_interventions[tracking_id]
        assert record.tracking_status == TrackingStatus.ENGAGED
        assert record.engaged_at is not None
        assert len(record.engagement_events) == 1
        assert record.success_metrics[SuccessMetric.ENGAGEMENT_SUCCESS] is True

    @pytest.mark.asyncio
    async def test_track_intervention_outcome_re_engaged(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking successful re-engagement outcome"""
        # Start tracking
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track outcome
        success_metrics = await intervention_tracker.track_intervention_outcome(
            tracking_id,
            InterventionOutcome.RE_ENGAGED,
            "Lead responded positively to email"
        )

        # Verify outcome tracked
        assert tracking_id not in intervention_tracker._active_interventions  # Moved to history
        assert "success_score" in success_metrics
        assert success_metrics["churn_prevented"] is True
        assert success_metrics["revenue_protected"] == 50000.0

    @pytest.mark.asyncio
    async def test_track_intervention_outcome_churned(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking churn outcome"""
        # Start tracking
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track churn outcome
        success_metrics = await intervention_tracker.track_intervention_outcome(
            tracking_id,
            InterventionOutcome.CHURNED,
            "Lead unsubscribed from all communications"
        )

        # Verify churn tracked
        assert success_metrics["churn_prevented"] is False
        assert success_metrics["revenue_protected"] == 0.0


class TestSuccessRateCalculation:
    """Test success rate calculation and analytics"""

    @pytest.mark.asyncio
    async def test_calculate_success_score(self, intervention_tracker):
        """Test composite success score calculation"""
        # Create test record
        record = InterventionRecord(
            tracking_id="test_123",
            intervention_id="int_123",
            lead_id="lead_123",
            tenant_id="tenant_123",
            stage=InterventionStage.ACTIVE_RISK,
            churn_probability=0.65,
            risk_level=ChurnRiskLevel.HIGH,
            initiated_at=datetime.now()
        )

        # Set success metrics
        record.success_metrics[SuccessMetric.DELIVERY_SUCCESS] = True
        record.success_metrics[SuccessMetric.ENGAGEMENT_SUCCESS] = True
        record.success_metrics[SuccessMetric.RESPONSE_SUCCESS] = True
        record.success_metrics[SuccessMetric.CHURN_PREVENTED] = True

        # Calculate score
        score = intervention_tracker._calculate_success_score(record)

        # Verify score (all metrics achieved = 1.0)
        assert score == 1.0

    @pytest.mark.asyncio
    async def test_stage_performance_calculation(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test stage-specific performance calculation"""
        # Create multiple interventions for same stage
        tracking_ids = []
        for i in range(5):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            tracking_ids.append(tracking_id)

        # Track outcomes: 3 successful, 2 churned
        for i, tracking_id in enumerate(tracking_ids):
            outcome = InterventionOutcome.RE_ENGAGED if i < 3 else InterventionOutcome.CHURNED
            await intervention_tracker.track_intervention_outcome(tracking_id, outcome)

        # Get interventions
        interventions = list(intervention_tracker._intervention_history)

        # Calculate stage performance
        stage_performance = intervention_tracker._calculate_stage_performance(interventions)

        # Verify Active Risk stage performance
        active_risk_perf = stage_performance.get(InterventionStage.ACTIVE_RISK)
        assert active_risk_perf is not None
        assert active_risk_perf.interventions_attempted == 5
        assert active_risk_perf.re_engaged_count == 3
        assert active_risk_perf.churned_count == 2
        assert active_risk_perf.overall_success_rate == 0.6  # 3/5 = 60%

    @pytest.mark.asyncio
    async def test_channel_performance_calculation(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment,
        sample_notification_result
    ):
        """Test channel-specific performance calculation"""
        # Create intervention
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track delivery
        await intervention_tracker.track_intervention_delivery(
            tracking_id,
            sample_notification_result
        )

        # Complete intervention
        await intervention_tracker.track_intervention_outcome(
            tracking_id,
            InterventionOutcome.RE_ENGAGED
        )

        # Get interventions
        interventions = list(intervention_tracker._intervention_history)

        # Calculate channel performance
        channel_performance = intervention_tracker._calculate_channel_performance(interventions)

        # Verify email channel performance
        email_perf = channel_performance.get(NotificationChannel.EMAIL)
        assert email_perf is not None
        assert email_perf.deliveries_successful > 0
        assert email_perf.success_rate == 1.0  # All successful


class TestBusinessImpactMeasurement:
    """Test business impact measurement and ROI calculation"""

    @pytest.mark.asyncio
    async def test_generate_business_impact_report(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test business impact report generation"""
        # Create successful interventions
        for i in range(10):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            # 7 successful, 3 churned
            outcome = InterventionOutcome.RE_ENGAGED if i < 7 else InterventionOutcome.CHURNED
            await intervention_tracker.track_intervention_outcome(tracking_id, outcome)

        # Generate report
        report = await intervention_tracker.generate_business_impact_report(time_period_days=30)

        # Verify report metrics
        assert report.total_interventions == 10
        assert report.successful_interventions == 7
        assert report.intervention_success_rate == 0.7
        assert report.leads_saved == 7
        assert report.total_revenue_protected == 350000.0  # 7 * $50K
        assert report.roi_multiplier > 0  # Should have positive ROI

    @pytest.mark.asyncio
    async def test_churn_reduction_calculation(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test churn reduction calculation"""
        # Create interventions with known churn rate
        for i in range(20):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            # 16 successful, 4 churned = 20% churn rate (vs 35% baseline)
            outcome = InterventionOutcome.RE_ENGAGED if i < 16 else InterventionOutcome.CHURNED
            await intervention_tracker.track_intervention_outcome(tracking_id, outcome)

        # Generate report
        report = await intervention_tracker.generate_business_impact_report(time_period_days=30)

        # Verify churn reduction
        # Current: 20% (4/20), Baseline: 35%, Reduction: (35-20)/35 = 42.9%
        assert report.current_churn_rate == 0.20
        assert abs(report.churn_reduction - 0.429) < 0.01  # ~43% reduction
        assert report.on_target is True  # Below 20% target

    @pytest.mark.asyncio
    async def test_roi_calculation(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test ROI calculation"""
        # Create 10 successful interventions
        for i in range(10):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            await intervention_tracker.track_intervention_outcome(
                tracking_id,
                InterventionOutcome.RE_ENGAGED
            )

        # Generate report
        report = await intervention_tracker.generate_business_impact_report(time_period_days=30)

        # Verify ROI
        # Revenue: 10 * $50K = $500K
        # Cost: 10 * $5 = $50
        # ROI: $500K / $50 = 10,000x
        assert report.total_revenue_protected == 500000.0
        assert report.total_intervention_cost == 50.0
        assert report.roi_multiplier == 10000.0


class TestManagerEscalationTracking:
    """Test manager escalation tracking and resolution"""

    @pytest.mark.asyncio
    async def test_track_manager_escalation(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking manager escalation"""
        # Create intervention
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Track escalation
        escalation_id = "esc_test123"
        await intervention_tracker.track_manager_escalation(tracking_id, escalation_id)

        # Verify escalation tracked
        record = intervention_tracker._active_interventions[tracking_id]
        assert record.escalated is True
        assert record.escalation_id == escalation_id

    @pytest.mark.asyncio
    async def test_track_escalation_resolution(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test tracking escalation resolution"""
        # Create and escalate intervention
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )
        await intervention_tracker.track_manager_escalation(tracking_id, "esc_test123")

        # Track resolution
        await intervention_tracker.track_escalation_resolution(
            tracking_id,
            InterventionOutcome.RE_ENGAGED,
            "Manager personally contacted lead and resolved concerns"
        )

        # Verify resolution tracked
        record = intervention_tracker._active_interventions[tracking_id]
        assert record.escalation_resolved is True
        assert record.escalation_resolution_time_hours is not None


class TestAnalyticsGeneration:
    """Test analytics generation and reporting"""

    @pytest.mark.asyncio
    async def test_generate_success_analytics(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test comprehensive analytics generation"""
        # Create diverse interventions
        for i in range(15):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            # Mix of outcomes
            if i < 10:
                outcome = InterventionOutcome.RE_ENGAGED
            elif i < 13:
                outcome = InterventionOutcome.CONVERTED
            else:
                outcome = InterventionOutcome.CHURNED

            await intervention_tracker.track_intervention_outcome(tracking_id, outcome)

        # Generate analytics
        analytics = await intervention_tracker.generate_success_analytics("7d")

        # Verify analytics
        assert analytics.total_interventions == 15
        assert analytics.successful_interventions == 13  # 10 re-engaged + 3 converted
        assert analytics.overall_success_rate == pytest.approx(13/15, rel=0.01)
        assert analytics.total_churn_prevented == 13
        assert analytics.total_revenue_protected == 650000.0  # 13 * $50K

    @pytest.mark.asyncio
    async def test_analytics_time_period_filtering(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test analytics filtering by time period"""
        # Create intervention with custom timestamp
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Modify timestamp to be older
        record = intervention_tracker._active_interventions[tracking_id]
        record.initiated_at = datetime.now() - timedelta(days=10)

        await intervention_tracker.track_intervention_outcome(
            tracking_id,
            InterventionOutcome.RE_ENGAGED
        )

        # Generate 7-day analytics (should exclude this intervention)
        analytics_7d = await intervention_tracker.generate_success_analytics("7d")
        assert analytics_7d.total_interventions == 0

        # Generate 30-day analytics (should include this intervention)
        analytics_30d = await intervention_tracker.generate_success_analytics("30d")
        assert analytics_30d.total_interventions == 1


class TestRealTimeUpdates:
    """Test real-time updates and broadcasting"""

    @pytest.mark.asyncio
    async def test_broadcast_tracking_event(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test real-time tracking event broadcasting"""
        # Enable broadcasting
        intervention_tracker.real_time_broadcast_enabled = True

        # Start tracking (should trigger broadcast)
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Verify broadcast was called
        assert intervention_tracker.websocket_manager.websocket_hub.broadcast_to_tenant.called

    @pytest.mark.asyncio
    async def test_real_time_analytics_update(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test real-time analytics status"""
        # Create active intervention
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Generate analytics
        analytics = await intervention_tracker.generate_success_analytics("7d")

        # Verify real-time status
        assert analytics.active_interventions == 1
        assert analytics.pending_responses >= 0


class TestDataPersistence:
    """Test data persistence and caching"""

    @pytest.mark.asyncio
    async def test_get_intervention_by_tracking_id(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test retrieving intervention by tracking ID"""
        # Create intervention
        tracking_id = await intervention_tracker.track_intervention_start(
            sample_intervention_action,
            sample_risk_assessment
        )

        # Retrieve by tracking ID
        record = await intervention_tracker.get_intervention_by_tracking_id(tracking_id)

        # Verify retrieval
        assert record is not None
        assert record.tracking_id == tracking_id
        assert record.lead_id == sample_intervention_action.lead_id

    @pytest.mark.asyncio
    async def test_get_lead_interventions(
        self,
        intervention_tracker,
        sample_intervention_action,
        sample_risk_assessment
    ):
        """Test retrieving all interventions for a lead"""
        lead_id = sample_intervention_action.lead_id

        # Create multiple interventions for same lead
        for i in range(3):
            tracking_id = await intervention_tracker.track_intervention_start(
                sample_intervention_action,
                sample_risk_assessment
            )
            if i < 2:  # Complete first 2
                await intervention_tracker.track_intervention_outcome(
                    tracking_id,
                    InterventionOutcome.RE_ENGAGED
                )

        # Retrieve all interventions for lead
        interventions = await intervention_tracker.get_lead_interventions(lead_id)

        # Verify retrieval
        assert len(interventions) == 3
        assert all(i.lead_id == lead_id for i in interventions)


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_track_delivery_for_nonexistent_tracking_id(self, intervention_tracker, sample_notification_result):
        """Test tracking delivery for non-existent tracking ID"""
        # Should not raise exception
        await intervention_tracker.track_intervention_delivery(
            "nonexistent_id",
            sample_notification_result
        )

    @pytest.mark.asyncio
    async def test_track_outcome_for_nonexistent_tracking_id(self, intervention_tracker):
        """Test tracking outcome for non-existent tracking ID"""
        # Should return empty dict
        result = await intervention_tracker.track_intervention_outcome(
            "nonexistent_id",
            InterventionOutcome.RE_ENGAGED
        )
        assert result == {}

    @pytest.mark.asyncio
    async def test_analytics_with_no_data(self, intervention_tracker):
        """Test analytics generation with no intervention data"""
        analytics = await intervention_tracker.generate_success_analytics("7d")

        assert analytics.total_interventions == 0
        assert analytics.overall_success_rate == 0.0

    @pytest.mark.asyncio
    async def test_business_impact_with_no_data(self, intervention_tracker):
        """Test business impact report with no data"""
        report = await intervention_tracker.generate_business_impact_report(time_period_days=30)

        assert report.total_interventions == 0
        assert report.total_revenue_protected == 0.0


@pytest.mark.asyncio
async def test_complete_intervention_lifecycle():
    """Integration test for complete intervention lifecycle"""
    # Create tracker
    tracker = InterventionTracker()

    with patch('ghl_real_estate_ai.services.intervention_tracker.get_cache_manager'):
        with patch.object(tracker.redis_client, 'initialize', new_callable=AsyncMock):
            with patch.object(tracker, '_load_historical_data', new_callable=AsyncMock):
                with patch.object(tracker, '_start_background_workers', new_callable=AsyncMock):
                    await tracker.initialize()

    # Create test data
    intervention_action = InterventionAction(
        action_id="action_integration",
        lead_id="lead_integration",
        tenant_id="tenant_integration",
        stage=InterventionStage.CRITICAL_RISK,
        channel=InterventionChannel.PHONE,
        action_type=ChurnInterventionType.IMMEDIATE_CALL,
        priority=InterventionPriority.URGENT,
        title="Critical Intervention",
        message_template="Test",
        personalization_data={},
        scheduled_time=datetime.now(),
        execution_deadline=datetime.now() + timedelta(hours=2),
        expected_success_rate=0.7,
        intervention_cost=10.0,
        roi_score=50.0
    )

    risk_assessment = ChurnRiskAssessment(
        lead_id="lead_integration",
        tenant_id="tenant_integration",
        assessment_id="assess_integration",
        timestamp=datetime.now(),
        churn_probability=0.85,
        risk_level=ChurnRiskLevel.CRITICAL,
        intervention_stage=InterventionStage.CRITICAL_RISK,
        confidence_score=0.9,
        prediction=None,
        time_to_churn_days=7,
        behavioral_signals={},
        recent_engagement={},
        detection_latency_ms=30.0,
        assessment_time_ms=45.0
    )

    # Complete lifecycle
    # 1. Track start
    tracking_id = await tracker.track_intervention_start(intervention_action, risk_assessment)
    assert tracking_id is not None

    # 2. Track delivery
    notification_result = NotificationResult(
        request_id="req_integration",
        notification_id="notif_integration",
        overall_status=DeliveryStatus.DELIVERED,
        successful_channels=[NotificationChannel.PHONE],
        failed_channels=[],
        channel_results={},
        total_delivery_time_ms=300.0,
        parallel_delivery=False,
        requested_at=datetime.now(),
        completed_at=datetime.now()
    )
    await tracker.track_intervention_delivery(tracking_id, notification_result)

    # 3. Track engagement
    await tracker.track_intervention_engagement(
        tracking_id,
        "responded",
        {"response_time_seconds": 120, "sentiment": "positive"}
    )

    # 4. Track outcome
    success_metrics = await tracker.track_intervention_outcome(
        tracking_id,
        InterventionOutcome.CONVERTED,
        "Lead scheduled property viewing and signed contract"
    )

    # Verify complete lifecycle
    assert success_metrics["churn_prevented"] is True
    assert success_metrics["success_score"] > 0.5
    assert tracking_id not in tracker._active_interventions  # Moved to history

    # Generate analytics
    analytics = await tracker.generate_success_analytics("7d")
    assert analytics.total_interventions == 1
    assert analytics.successful_interventions == 1

    # Generate business impact
    report = await tracker.generate_business_impact_report(30)
    assert report.leads_saved == 1
    assert report.total_revenue_protected == 50000.0
    assert report.roi_multiplier > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
