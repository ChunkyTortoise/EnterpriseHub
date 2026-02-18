"""
Comprehensive Tests for Premium Service Delivery Tracker
Test suite for executive-level service delivery and quality assurance

Tests cover:
- Service deliverable creation and tracking
- Premium service standards and SLA management
- Quality assessment and client satisfaction tracking
- Service metrics and KPI calculation
- Executive reporting and ROI analysis
- White-glove service automation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.premium_service_delivery_tracker import (
    ClientServiceProfile,
    PremiumServiceDeliveryTracker,
    ServiceDeliverable,
    ServiceMetrics,
    ServiceStandard,
    ServiceStatus,
    ServiceTier,
    TouchpointType,
    create_sample_client_profiles,
)


@pytest.fixture
def service_tracker():
    """Initialize premium service delivery tracker for testing"""
    with patch.multiple(
        "ghl_real_estate_ai.services.premium_service_delivery_tracker",
        CacheService=Mock(),
        ClaudeAssistant=Mock(),
        LLMClient=Mock(),
    ):
        tracker = PremiumServiceDeliveryTracker()
        # Mock Claude responses
        tracker.claude.generate_claude_response = AsyncMock(
            return_value="Service excellence achieved through consistent delivery of premium experiences and proactive client engagement."
        )
        return tracker


@pytest.fixture
def white_glove_client():
    """Sample white-glove service client"""
    return ClientServiceProfile(
        client_id="WG-001",
        client_name="Executive Client Alpha",
        service_tier=ServiceTier.WHITE_GLOVE,
        net_worth=25_000_000,
        relationship_value=450_000,
        overall_satisfaction=96.5,
        service_score=95.8,
        nps_score=92,
        total_deliverables=32,
        on_time_delivery_rate=100.0,
        quality_average=96.2,
        response_time_average=0.3,
        privacy_requirements=98.0,
        dedicated_service_manager="Senior Executive Specialist",
    )


@pytest.fixture
def premium_client():
    """Sample premium service client"""
    return ClientServiceProfile(
        client_id="PREM-001",
        client_name="Investment Client Beta",
        service_tier=ServiceTier.PREMIUM,
        net_worth=8_000_000,
        relationship_value=180_000,
        overall_satisfaction=89.2,
        service_score=87.5,
        nps_score=75,
        total_deliverables=18,
        on_time_delivery_rate=94.4,
        quality_average=88.1,
        response_time_average=2.1,
        privacy_requirements=75.0,
    )


class TestServiceDeliverableManagement:
    """Test service deliverable creation and management"""

    @pytest.mark.asyncio
    async def test_create_service_deliverable_white_glove(self, service_tracker):
        """Test creating white-glove service deliverable"""
        deliverable = await service_tracker.create_service_deliverable(
            client_id="WG-001",
            deliverable_type=TouchpointType.INITIAL_CONSULTATION,
            service_tier=ServiceTier.WHITE_GLOVE,
            description="Executive consultation and comprehensive market analysis",
            priority="high",
        )

        assert isinstance(deliverable, ServiceDeliverable)
        assert deliverable.client_id == "WG-001"
        assert deliverable.deliverable_type == TouchpointType.INITIAL_CONSULTATION
        assert deliverable.service_tier == ServiceTier.WHITE_GLOVE
        assert deliverable.status == ServiceStatus.PENDING
        assert deliverable.priority == "high"
        assert len(deliverable.updates) > 0  # Should have initial tracking entry

    @pytest.mark.asyncio
    async def test_create_service_deliverable_premium(self, service_tracker):
        """Test creating premium service deliverable"""
        deliverable = await service_tracker.create_service_deliverable(
            client_id="PREM-001",
            deliverable_type=TouchpointType.MARKET_ANALYSIS,
            service_tier=ServiceTier.PREMIUM,
            description="Market analysis and property recommendations",
        )

        assert deliverable.service_tier == ServiceTier.PREMIUM
        assert deliverable.assigned_to is not None
        assert deliverable.due_date > deliverable.created_date

    @pytest.mark.asyncio
    async def test_create_service_deliverable_standard(self, service_tracker):
        """Test creating standard service deliverable"""
        deliverable = await service_tracker.create_service_deliverable(
            client_id="STD-001", deliverable_type=TouchpointType.PROPERTY_TOUR, service_tier=ServiceTier.STANDARD
        )

        assert deliverable.service_tier == ServiceTier.STANDARD
        # Standard service should have longer completion times
        time_diff = deliverable.due_date - deliverable.created_date
        assert time_diff.total_seconds() >= 72 * 3600  # At least 72 hours

    @pytest.mark.asyncio
    async def test_auto_assign_deliverable(self, service_tracker):
        """Test automatic deliverable assignment"""
        # White-glove deliverable should get senior assignment
        white_glove_deliverable = ServiceDeliverable(
            deliverable_id="WG-DEL-001",
            client_id="WG-001",
            deliverable_type=TouchpointType.NEGOTIATION,
            service_tier=ServiceTier.WHITE_GLOVE,
            created_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=8),
        )

        assignment = await service_tracker._auto_assign_deliverable(white_glove_deliverable)
        assert "Jorge" in assignment or "Executive" in assignment

        # Standard deliverable should get standard assignment
        standard_deliverable = ServiceDeliverable(
            deliverable_id="STD-DEL-001",
            client_id="STD-001",
            deliverable_type=TouchpointType.PROPERTY_TOUR,
            service_tier=ServiceTier.STANDARD,
            created_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=72),
        )

        standard_assignment = await service_tracker._auto_assign_deliverable(standard_deliverable)
        assert "Coordinator" in standard_assignment or "Specialist" in standard_assignment


class TestServiceStandardsAndSLA:
    """Test service standards and SLA management"""

    def test_service_standards_initialization(self, service_tracker):
        """Test that service standards are properly initialized"""
        standards = service_tracker.service_standards

        # Verify all service tiers have standards
        assert ServiceTier.STANDARD in standards
        assert ServiceTier.PREMIUM in standards
        assert ServiceTier.WHITE_GLOVE in standards
        assert ServiceTier.CONCIERGE in standards

        # Verify white-glove has strictest standards
        white_glove = standards[ServiceTier.WHITE_GLOVE]
        standard = standards[ServiceTier.STANDARD]

        assert white_glove.response_time_hours < standard.response_time_hours
        assert white_glove.completion_time_hours < standard.completion_time_hours
        assert white_glove.quality_threshold > standard.quality_threshold
        assert white_glove.client_satisfaction_target > standard.client_satisfaction_target

    def test_concierge_service_standards(self, service_tracker):
        """Test concierge service has highest standards"""
        concierge_standard = service_tracker.service_standards[ServiceTier.CONCIERGE]

        assert concierge_standard.response_time_hours <= 0.5  # 30 minutes max
        assert concierge_standard.completion_time_hours <= 4.0  # 4 hours max
        assert concierge_standard.quality_threshold >= 98.0  # 98%+ quality
        assert concierge_standard.client_satisfaction_target >= 98.0  # 98%+ satisfaction


class TestServiceStatusManagement:
    """Test service status updates and tracking"""

    @pytest.mark.asyncio
    async def test_update_deliverable_status_in_progress(self, service_tracker):
        """Test updating deliverable to in-progress"""
        result = await service_tracker.update_deliverable_status(
            deliverable_id="TEST-001",
            new_status=ServiceStatus.IN_PROGRESS,
            update_note="Started working on consultation preparation",
            automated=False,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_deliverable_status_completed(self, service_tracker):
        """Test completing a deliverable"""
        result = await service_tracker.update_deliverable_status(
            deliverable_id="TEST-002",
            new_status=ServiceStatus.COMPLETED,
            update_note="Consultation completed successfully",
            quality_score=94.5,
            automated=False,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_update_deliverable_status_escalated(self, service_tracker):
        """Test escalating a deliverable"""
        result = await service_tracker.update_deliverable_status(
            deliverable_id="TEST-003",
            new_status=ServiceStatus.ESCALATED,
            update_note="Client requirements exceeded initial scope",
            automated=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_assess_deliverable_quality_ai(self, service_tracker):
        """Test AI-powered deliverable quality assessment"""
        quality_score = await service_tracker._assess_deliverable_quality("QUAL-001")

        assert 0 <= quality_score <= 100
        assert isinstance(quality_score, float)

    @pytest.mark.asyncio
    async def test_assess_deliverable_quality_fallback(self, service_tracker):
        """Test quality assessment fallback when AI fails"""
        # Mock Claude to fail
        service_tracker.claude.generate_claude_response = AsyncMock(side_effect=Exception("AI unavailable"))

        quality_score = await service_tracker._assess_deliverable_quality("QUAL-002")

        # Should provide fallback score
        assert 0 <= quality_score <= 100
        assert quality_score >= 80  # Fallback should assume high quality


class TestClientServiceAnalysis:
    """Test client service performance analysis"""

    @pytest.mark.asyncio
    async def test_analyze_client_service_performance(self, service_tracker):
        """Test comprehensive client service analysis"""
        profile = await service_tracker.analyze_client_service_performance("CLIENT-001")

        assert isinstance(profile, ClientServiceProfile)
        assert profile.client_id == "CLIENT-001"
        assert profile.service_tier is not None
        assert profile.overall_satisfaction >= 0
        assert profile.service_score >= 0
        assert profile.total_deliverables >= 0
        assert len(profile.concierge_services_active) >= 0

    @pytest.mark.asyncio
    async def test_client_service_metrics_calculation(self, service_tracker):
        """Test client service metrics are properly calculated"""
        profile = await service_tracker.analyze_client_service_performance("METRICS-001")

        # Verify metrics are in valid ranges
        assert 0 <= profile.on_time_delivery_rate <= 100
        assert 0 <= profile.quality_average <= 100
        assert profile.response_time_average >= 0
        assert 0 <= profile.overall_satisfaction <= 100
        assert 0 <= profile.service_score <= 100
        assert -100 <= (profile.nps_score or 0) <= 100


class TestServiceExcellenceReporting:
    """Test service excellence reporting and insights"""

    @pytest.mark.asyncio
    async def test_generate_service_excellence_report(self, service_tracker):
        """Test comprehensive service excellence report generation"""
        sample_profiles = create_sample_client_profiles()
        report = await service_tracker.generate_service_excellence_report(sample_profiles)

        assert isinstance(report, dict)
        assert "summary" in report
        assert "service_tier_distribution" in report
        assert "top_performing_relationships" in report
        assert "ai_insights" in report

        # Verify summary metrics
        summary = report["summary"]
        assert "total_clients" in summary
        assert "total_relationship_value" in summary
        assert "average_satisfaction" in summary
        assert "average_service_score" in summary

    @pytest.mark.asyncio
    async def test_generate_service_excellence_empty_profiles(self, service_tracker):
        """Test service excellence report with empty profiles"""
        empty_profiles = []
        report = await service_tracker.generate_service_excellence_report(empty_profiles)

        assert report == {}

    @pytest.mark.asyncio
    async def test_generate_service_insights(self, service_tracker):
        """Test AI-powered service insights generation"""
        sample_profiles = create_sample_client_profiles()
        insights = await service_tracker._generate_service_insights(sample_profiles)

        assert isinstance(insights, str)
        assert len(insights) > 50  # Should be substantial insight

    @pytest.mark.asyncio
    async def test_generate_service_insights_fallback(self, service_tracker):
        """Test service insights fallback when AI fails"""
        # Mock Claude to fail
        service_tracker.claude.generate_claude_response = AsyncMock(side_effect=Exception("AI unavailable"))

        sample_profiles = create_sample_client_profiles()
        insights = await service_tracker._generate_service_insights(sample_profiles)

        # Should provide fallback insights
        assert isinstance(insights, str)
        assert len(insights) > 20
        assert "satisfaction" in insights.lower()

    def test_identify_service_issues(self, service_tracker):
        """Test service issue identification"""
        # Client with issues
        problematic_client = ClientServiceProfile(
            client_id="PROBLEM-001",
            client_name="Problematic Client",
            service_tier=ServiceTier.PREMIUM,
            net_worth=5_000_000,
            relationship_value=100_000,
            overall_satisfaction=65.0,  # Low satisfaction
            service_score=70.0,
            response_time_average=5.0,  # Slow response
            on_time_delivery_rate=75.0,  # Poor delivery
        )

        issues = service_tracker._identify_service_issues(problematic_client)

        assert len(issues) > 0
        assert any("satisfaction" in issue.lower() for issue in issues)
        assert any("response" in issue.lower() for issue in issues)
        assert any("delivery" in issue.lower() for issue in issues)

        # Client without issues
        excellent_client = ClientServiceProfile(
            client_id="EXCELLENT-001",
            client_name="Excellent Client",
            service_tier=ServiceTier.WHITE_GLOVE,
            net_worth=15_000_000,
            relationship_value=300_000,
            overall_satisfaction=96.0,
            service_score=95.0,
            response_time_average=0.5,
            on_time_delivery_rate=98.0,
        )

        no_issues = service_tracker._identify_service_issues(excellent_client)
        assert len(no_issues) == 0


class TestServiceROICalculation:
    """Test service ROI and business impact calculation"""

    def test_calculate_service_roi(self, service_tracker):
        """Test service ROI calculation"""
        sample_profiles = create_sample_client_profiles()
        roi_analysis = service_tracker.calculate_service_roi(sample_profiles)

        assert isinstance(roi_analysis, dict)
        assert "total_service_investment" in roi_analysis
        assert "commission_premium_generated" in roi_analysis
        assert "service_roi_percentage" in roi_analysis
        assert "relationship_value_protected" in roi_analysis

        # Verify ROI calculations are reasonable
        assert roi_analysis["total_service_investment"] > 0
        assert roi_analysis["commission_premium_generated"] >= 0
        assert roi_analysis["relationship_value_protected"] >= 0

    def test_calculate_service_roi_different_tiers(self, service_tracker):
        """Test ROI calculation with different service tiers"""
        mixed_profiles = [
            ClientServiceProfile(
                client_id=f"TIER-{tier.value}",
                client_name=f"Client {tier.value}",
                service_tier=tier,
                net_worth=10_000_000,
                relationship_value=200_000,
            )
            for tier in [ServiceTier.STANDARD, ServiceTier.PREMIUM, ServiceTier.WHITE_GLOVE, ServiceTier.CONCIERGE]
        ]

        roi_analysis = service_tracker.calculate_service_roi(mixed_profiles)

        # Higher service tiers should have higher investment costs
        assert roi_analysis["total_service_investment"] > 0


class TestServicePlanCreation:
    """Test service plan creation and management"""

    @pytest.mark.asyncio
    async def test_create_client_service_plan_white_glove(self, service_tracker):
        """Test creating white-glove service plan"""
        service_plan = await service_tracker.create_client_service_plan(
            client_id="WG-PLAN-001",
            service_tier=ServiceTier.WHITE_GLOVE,
            property_value_range=(2_000_000, 5_000_000),
            timeline_months=12,
        )

        assert isinstance(service_plan, dict)
        assert service_plan["client_id"] == "WG-PLAN-001"
        assert service_plan["service_tier"] == ServiceTier.WHITE_GLOVE.value
        assert "service_milestones" in service_plan
        assert "premium_features" in service_plan
        assert "success_metrics" in service_plan

        # White-glove should have comprehensive milestones
        milestones = service_plan["service_milestones"]
        assert len(milestones) > 0

    @pytest.mark.asyncio
    async def test_create_client_service_plan_premium(self, service_tracker):
        """Test creating premium service plan"""
        service_plan = await service_tracker.create_client_service_plan(
            client_id="PREM-PLAN-001", service_tier=ServiceTier.PREMIUM, property_value_range=(750_000, 2_000_000)
        )

        assert service_plan["service_tier"] == ServiceTier.PREMIUM.value
        assert "service_standards" in service_plan

        # Verify service standards match tier
        standards = service_plan["service_standards"]
        assert standards["response_time_hours"] <= 4.0  # Premium response time


class TestServiceKPITracking:
    """Test service KPI tracking and metrics"""

    def test_track_service_kpis(self, service_tracker):
        """Test service KPI tracking"""
        metrics = service_tracker.track_service_kpis()

        assert isinstance(metrics, ServiceMetrics)
        assert metrics.total_active_clients >= 0
        assert metrics.total_deliverables_month >= 0
        assert 0 <= metrics.overall_satisfaction_average <= 100
        assert 0 <= metrics.on_time_delivery_rate <= 100
        assert metrics.average_response_time >= 0
        assert 0 <= metrics.client_retention_rate <= 100

    def test_service_metrics_premium_focus(self, service_tracker):
        """Test service metrics with premium client focus"""
        metrics = service_tracker.track_service_kpis()

        # Premium metrics should be present
        assert metrics.white_glove_client_count >= 0
        assert 0 <= metrics.premium_client_satisfaction <= 100
        assert 0 <= metrics.concierge_service_utilization <= 100
        assert metrics.total_commission_protected >= 0
        assert 0 <= metrics.premium_rate_justified <= 100
        assert 0 <= metrics.referral_rate <= 100


class TestAutomationAndWorkflows:
    """Test service automation and workflow management"""

    @pytest.mark.asyncio
    async def test_schedule_automated_follow_ups(self, service_tracker):
        """Test automated follow-up scheduling"""
        deliverable = ServiceDeliverable(
            deliverable_id="AUTO-001",
            client_id="CLIENT-001",
            deliverable_type=TouchpointType.INITIAL_CONSULTATION,
            service_tier=ServiceTier.WHITE_GLOVE,
            created_date=datetime.now(),
            due_date=datetime.now() + timedelta(hours=8),
        )

        await service_tracker._schedule_automated_follow_ups(deliverable)

        assert len(deliverable.automated_actions) > 0
        assert any("Response check" in action for action in deliverable.automated_actions)
        assert any("Escalation" in action for action in deliverable.automated_actions)

    @pytest.mark.asyncio
    async def test_request_client_satisfaction_feedback(self, service_tracker):
        """Test automated satisfaction feedback request"""
        feedback_request = await service_tracker._request_client_satisfaction_feedback("FEEDBACK-001")

        assert isinstance(feedback_request, dict)
        assert "deliverable_id" in feedback_request
        assert "survey_type" in feedback_request
        assert feedback_request["deliverable_id"] == "FEEDBACK-001"

    @pytest.mark.asyncio
    async def test_handle_escalation(self, service_tracker):
        """Test service escalation handling"""
        escalation = await service_tracker._handle_escalation(
            "ESCALATE-001", "Client requirements exceeded scope and timeline"
        )

        assert isinstance(escalation, dict)
        assert "timestamp" in escalation
        assert "reason" in escalation
        assert "escalated_to" in escalation


class TestDataValidationAndEdgeCases:
    """Test data validation and edge case handling"""

    @pytest.mark.asyncio
    async def test_create_deliverable_invalid_client(self, service_tracker):
        """Test creating deliverable with invalid client ID"""
        deliverable = await service_tracker.create_service_deliverable(
            client_id="",  # Invalid client ID
            deliverable_type=TouchpointType.PROPERTY_TOUR,
            service_tier=ServiceTier.PREMIUM,
        )

        # Should handle gracefully
        assert isinstance(deliverable, ServiceDeliverable)
        assert deliverable.client_id == ""

    @pytest.mark.asyncio
    async def test_analyze_client_performance_nonexistent(self, service_tracker):
        """Test analyzing performance for non-existent client"""
        profile = await service_tracker.analyze_client_service_performance("NONEXISTENT-999")

        # Should return profile with default values
        assert isinstance(profile, ClientServiceProfile)
        assert profile.client_id == "NONEXISTENT-999"

    def test_calculate_roi_empty_profiles(self, service_tracker):
        """Test ROI calculation with empty client profiles"""
        empty_profiles = []
        roi_analysis = service_tracker.calculate_service_roi(empty_profiles)

        # Should handle gracefully
        assert roi_analysis["total_service_investment"] == 0
        assert roi_analysis["commission_premium_generated"] == 0


class TestIntegrationWithExistingSystems:
    """Integration tests with existing systems"""

    @pytest.mark.asyncio
    async def test_integration_with_cache_service(self, service_tracker):
        """Test integration with cache service"""
        with patch.object(service_tracker.cache, "get", return_value=None):
            with patch.object(service_tracker.cache, "set", return_value=True):
                deliverable = await service_tracker.create_service_deliverable(
                    "CACHE-001", TouchpointType.MARKET_ANALYSIS, ServiceTier.PREMIUM
                )
                assert deliverable is not None

    @pytest.mark.asyncio
    async def test_integration_with_claude_assistant(self, service_tracker):
        """Test integration with Claude assistant"""
        sample_profiles = create_sample_client_profiles()
        await service_tracker.generate_service_excellence_report(sample_profiles)

        # Verify Claude was called for insights
        assert service_tracker.claude.generate_claude_response.called


class TestPerformance:
    """Performance tests for service delivery tracking"""

    @pytest.mark.asyncio
    async def test_service_analysis_performance(self, service_tracker):
        """Test service analysis performance"""
        import time

        start_time = time.time()
        await service_tracker.analyze_client_service_performance("PERF-001")
        end_time = time.time()

        # Should complete quickly
        processing_time = end_time - start_time
        assert processing_time < 2.0  # Should be under 2 seconds

    @pytest.mark.asyncio
    async def test_batch_report_generation_performance(self, service_tracker):
        """Test performance with large client batch"""
        import time

        # Create large batch of client profiles
        large_batch = []
        for i in range(100):
            profile = ClientServiceProfile(
                client_id=f"BATCH-{i:03d}",
                client_name=f"Batch Client {i}",
                service_tier=ServiceTier.PREMIUM,
                net_worth=5_000_000,
                relationship_value=150_000,
            )
            large_batch.append(profile)

        start_time = time.time()
        report = await service_tracker.generate_service_excellence_report(large_batch)
        end_time = time.time()

        # Should handle large batch efficiently
        processing_time = end_time - start_time
        assert processing_time < 15.0  # Should complete in under 15 seconds
        assert report["summary"]["total_clients"] == 100


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
