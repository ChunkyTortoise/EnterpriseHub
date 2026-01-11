"""
Tests for Phase 3 Business Impact Measurement System
===================================================

Test coverage for:
- Feature flag management
- Business metrics tracking
- ROI calculations
- A/B test statistical analysis
- Progressive rollout logic

Author: EnterpriseHub Development Team
Created: January 2026
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from ghl_real_estate_ai.services.feature_flag_manager import (
    FeatureFlagManager,
    FeatureFlag,
    RolloutStage,
    FeatureStatus,
    RollbackReason
)
from ghl_real_estate_ai.services.phase3_business_impact_tracker import (
    Phase3BusinessImpactTracker,
    BusinessMetric,
    MetricType,
    FeatureROI,
    ABTestResult
)


# ========================================================================
# Feature Flag Manager Tests
# ========================================================================

@pytest.mark.asyncio
class TestFeatureFlagManager:
    """Test feature flag management functionality."""

    async def test_flag_creation(self):
        """Test creating feature flag."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="test_feature",
            name="Test Feature",
            description="Test feature for unit testing",
            rollout_stage=RolloutStage.BETA_10,
            percentage=10.0
        )

        result = await manager.create_flag(flag)
        assert result is True

        # Verify flag can be retrieved
        retrieved = await manager.get_flag("test_feature")
        assert retrieved is not None
        assert retrieved.feature_id == "test_feature"
        assert retrieved.percentage == 10.0

    async def test_feature_enabled_by_percentage(self):
        """Test percentage-based feature enablement."""
        manager = FeatureFlagManager()
        await manager.initialize()

        # Create flag with 50% rollout
        flag = FeatureFlag(
            feature_id="test_50_percent",
            name="50% Test",
            description="Test",
            rollout_stage=RolloutStage.BETA_50,
            percentage=50.0
        )

        await manager.create_flag(flag)

        # Test multiple users - should get ~50% enabled
        enabled_count = 0
        total_tests = 100

        for i in range(total_tests):
            enabled = await manager.is_enabled(
                "test_50_percent",
                "tenant_1",
                f"user_{i}"
            )
            if enabled:
                enabled_count += 1

        # Should be roughly 50% (within 20% tolerance)
        assert 30 <= enabled_count <= 70

    async def test_whitelist_override(self):
        """Test whitelist overrides percentage rollout."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="whitelist_test",
            name="Whitelist Test",
            description="Test",
            rollout_stage=RolloutStage.BETA_10,
            percentage=10.0,
            tenant_whitelist=["whitelisted_tenant"]
        )

        await manager.create_flag(flag)

        # Whitelisted tenant should always be enabled
        enabled = await manager.is_enabled(
            "whitelist_test",
            "whitelisted_tenant",
            "any_user"
        )
        assert enabled is True

    async def test_blacklist_blocks_access(self):
        """Test blacklist blocks access regardless of percentage."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="blacklist_test",
            name="Blacklist Test",
            description="Test",
            rollout_stage=RolloutStage.GA,  # 100% rollout
            percentage=100.0,
            tenant_blacklist=["blocked_tenant"]
        )

        await manager.create_flag(flag)

        # Blacklisted tenant should be blocked even at 100%
        enabled = await manager.is_enabled(
            "blacklist_test",
            "blocked_tenant",
            "any_user"
        )
        assert enabled is False

    async def test_user_bucketing_consistency(self):
        """Test user bucketing is consistent across calls."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="bucketing_test",
            name="Bucketing Test",
            description="Test",
            rollout_stage=RolloutStage.BETA_50,
            percentage=50.0
        )

        await manager.create_flag(flag)

        # Get variant multiple times
        variant1 = await manager.get_variant(
            "bucketing_test",
            "tenant_1",
            "user_123"
        )

        variant2 = await manager.get_variant(
            "bucketing_test",
            "tenant_1",
            "user_123"
        )

        # Should be consistent
        assert variant1 == variant2

    async def test_rollout_stage_update(self):
        """Test updating rollout stage."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="stage_test",
            name="Stage Test",
            description="Test",
            rollout_stage=RolloutStage.BETA_10
        )

        await manager.create_flag(flag)

        # Update to 50%
        result = await manager.update_rollout_stage(
            "stage_test",
            RolloutStage.BETA_50
        )

        assert result is True

        # Verify update
        updated = await manager.get_flag("stage_test")
        assert updated.rollout_stage == RolloutStage.BETA_50
        assert updated.percentage == 50.0

    async def test_feature_rollback(self):
        """Test feature rollback."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="rollback_test",
            name="Rollback Test",
            description="Test",
            rollout_stage=RolloutStage.GA,
            status=FeatureStatus.ACTIVE
        )

        await manager.create_flag(flag)

        # Rollback feature
        result = await manager.rollback_feature(
            "rollback_test",
            RollbackReason.ERROR_RATE_SPIKE,
            "Error rate exceeded threshold"
        )

        assert result is True

        # Verify rollback
        rolled_back = await manager.get_flag("rollback_test")
        assert rolled_back.status == FeatureStatus.ROLLED_BACK
        assert rolled_back.rollout_stage == RolloutStage.DISABLED

    async def test_flag_lookup_performance(self):
        """Test flag lookup performance (<1ms target)."""
        manager = FeatureFlagManager()
        await manager.initialize()

        flag = FeatureFlag(
            feature_id="perf_test",
            name="Performance Test",
            description="Test",
            rollout_stage=RolloutStage.GA
        )

        await manager.create_flag(flag)

        # Warm up cache
        await manager.get_flag("perf_test")

        # Measure lookup time
        import time
        start = time.time()

        for _ in range(1000):
            await manager.get_flag("perf_test")

        elapsed = (time.time() - start) * 1000  # Convert to ms

        # Average should be <1ms
        avg_time = elapsed / 1000
        assert avg_time < 1.0


# ========================================================================
# Business Impact Tracker Tests
# ========================================================================

@pytest.mark.asyncio
class TestBusinessImpactTracker:
    """Test business impact tracking and ROI calculation."""

    async def test_metric_recording(self):
        """Test recording business metrics."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        metric = BusinessMetric(
            metric_type=MetricType.RESPONSE_TIME,
            feature_id="realtime_intelligence",
            tenant_id="tenant_1",
            user_id="user_1",
            value=25.0,  # 25 seconds
            variant="treatment"
        )

        result = await tracker.record_metric(metric)
        assert result is True

    async def test_realtime_intelligence_tracking(self):
        """Test real-time intelligence event tracking."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        await tracker.track_realtime_intelligence_event(
            tenant_id="tenant_1",
            user_id="user_1",
            response_time_seconds=30.0,
            lead_id="lead_123"
        )

        # Verify metric was recorded
        assert len(tracker.metric_buffer) > 0

    async def test_roi_calculation_realtime_intelligence(self):
        """Test ROI calculation for real-time intelligence."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Record multiple events
        for i in range(50):
            await tracker.track_realtime_intelligence_event(
                tenant_id="tenant_1",
                user_id=f"user_{i}",
                response_time_seconds=30.0,  # Target: 30 seconds vs baseline 900
                lead_id=f"lead_{i}"
            )

        # Calculate ROI
        roi = await tracker.calculate_feature_roi(
            "realtime_intelligence",
            days=7
        )

        assert roi is not None
        assert roi.cost_savings > 0  # Should have cost savings from time reduction
        assert roi.roi_percentage > 0

    async def test_property_intelligence_satisfaction_tracking(self):
        """Test property matching satisfaction tracking."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # High satisfaction score
        await tracker.track_property_match_satisfaction(
            tenant_id="tenant_1",
            user_id="user_1",
            lead_id="lead_1",
            satisfaction_score=95.0,  # 95%
            property_id="prop_1"
        )

        # Verify metric
        assert len(tracker.metric_buffer) > 0

    async def test_churn_prevention_tracking(self):
        """Test churn prevention intervention tracking."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Successful intervention (no churn)
        await tracker.track_churn_prevention_intervention(
            tenant_id="tenant_1",
            user_id="user_1",
            lead_id="lead_1",
            intervention_stage=2,
            churned=False
        )

        # Verify metric
        assert len(tracker.metric_buffer) > 0
        last_metric = tracker.metric_buffer[-1]
        assert last_metric.value == 0.0  # No churn

    async def test_ai_coaching_tracking(self):
        """Test AI coaching session tracking."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        await tracker.track_ai_coaching_session(
            tenant_id="tenant_1",
            agent_id="agent_1",
            session_duration_minutes=20.0,  # Reduced from 40
            productivity_score=85.0
        )

        # Should have 2 metrics: training time + productivity
        assert len(tracker.metric_buffer) >= 2

    async def test_ab_test_statistical_analysis(self):
        """Test A/B test statistical analysis."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Record control group metrics
        for i in range(100):
            metric = BusinessMetric(
                metric_type=MetricType.RESPONSE_TIME,
                feature_id="realtime_intelligence",
                tenant_id="tenant_1",
                user_id=f"user_{i}",
                value=900.0,  # Baseline: 15 minutes
                variant="control"
            )
            await tracker.record_metric(metric)

        # Record treatment group metrics (improved)
        for i in range(100):
            metric = BusinessMetric(
                metric_type=MetricType.RESPONSE_TIME,
                feature_id="realtime_intelligence",
                tenant_id="tenant_1",
                user_id=f"user_{i + 100}",
                value=30.0,  # Treatment: 30 seconds
                variant="treatment"
            )
            await tracker.record_metric(metric)

        # Run A/B test
        result = await tracker.run_ab_test_analysis(
            "realtime_intelligence",
            MetricType.RESPONSE_TIME,
            days=7
        )

        assert result is not None
        assert result.treatment_mean < result.control_mean  # Treatment should be faster
        assert result.lift_percentage < 0  # Negative lift = improvement for response time
        assert result.is_significant is True  # Should be statistically significant

    async def test_daily_summary_calculation(self):
        """Test daily summary calculation."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Record some metrics
        for feature_id in ['realtime_intelligence', 'property_intelligence']:
            for i in range(10):
                metric = BusinessMetric(
                    metric_type=MetricType.REVENUE,
                    feature_id=feature_id,
                    tenant_id="tenant_1",
                    user_id=f"user_{i}",
                    value=1000.0,
                    variant="treatment"
                )
                await tracker.record_metric(metric)

        # Get daily summary
        summary = await tracker.get_daily_summary()

        assert summary is not None
        assert 'total_revenue_impact' in summary
        assert 'total_cost_savings' in summary
        assert 'features' in summary

    async def test_insufficient_data_handling(self):
        """Test A/B test with insufficient data."""
        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Record only a few metrics
        for i in range(5):
            metric = BusinessMetric(
                metric_type=MetricType.RESPONSE_TIME,
                feature_id="realtime_intelligence",
                tenant_id="tenant_1",
                user_id=f"user_{i}",
                value=30.0,
                variant="treatment"
            )
            await tracker.record_metric(metric)

        # Run A/B test
        result = await tracker.run_ab_test_analysis(
            "realtime_intelligence",
            MetricType.RESPONSE_TIME,
            days=7
        )

        assert result is not None
        assert result.recommended_action == "insufficient_data"


# ========================================================================
# Integration Tests
# ========================================================================

@pytest.mark.asyncio
class TestIntegration:
    """Test integration between feature flags and business tracking."""

    async def test_progressive_rollout_workflow(self):
        """Test complete progressive rollout workflow."""
        # Initialize both systems
        flag_manager = FeatureFlagManager()
        await flag_manager.initialize()

        tracker = Phase3BusinessImpactTracker()
        await tracker.initialize()

        # Create feature flag at 10%
        flag = FeatureFlag(
            feature_id="integration_test",
            name="Integration Test Feature",
            description="Test",
            rollout_stage=RolloutStage.BETA_10,
            percentage=10.0
        )

        await flag_manager.create_flag(flag)

        # Simulate user traffic and metric collection
        for i in range(100):
            tenant_id = "tenant_1"
            user_id = f"user_{i}"

            # Check if enabled
            enabled = await flag_manager.is_enabled(
                "integration_test",
                tenant_id,
                user_id
            )

            # Get variant
            variant = await flag_manager.get_variant(
                "integration_test",
                tenant_id,
                user_id
            ) if enabled else "control"

            # Record metric
            metric = BusinessMetric(
                metric_type=MetricType.CONVERSION_RATE,
                feature_id="integration_test",
                tenant_id=tenant_id,
                user_id=user_id,
                value=0.2 if variant == "treatment" else 0.15,  # 20% vs 15%
                variant=variant
            )

            await tracker.record_metric(metric)

        # Run A/B test
        result = await tracker.run_ab_test_analysis(
            "integration_test",
            MetricType.CONVERSION_RATE,
            days=1
        )

        # If positive, progress rollout
        if result and result.lift_percentage > 0:
            await flag_manager.update_rollout_stage(
                "integration_test",
                RolloutStage.BETA_25
            )

            updated_flag = await flag_manager.get_flag("integration_test")
            assert updated_flag.percentage == 25.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
