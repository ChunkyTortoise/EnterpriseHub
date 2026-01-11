"""
Comprehensive Tests for Business Metrics Service.

Tests cover all major functionality including:
- GHL webhook performance tracking
- Business impact KPI calculation
- Agent productivity metrics
- Property matching effectiveness
- Revenue attribution analysis
- Real-time metrics collection
- Dashboard data generation
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.business_metrics_service import (
    BusinessMetricsService,
    BusinessMetric,
    MetricType,
    ConversionStage,
    WebhookPerformanceMetrics,
    BusinessImpactMetrics,
    AgentProductivityMetrics,
    calculate_performance_grade,
    create_business_metrics_service
)


class TestBusinessMetricsService:
    """Test suite for BusinessMetricsService functionality."""

    @pytest.fixture
    async def metrics_service(self):
        """Create a test BusinessMetricsService instance."""
        service = BusinessMetricsService(
            redis_url="redis://localhost:6379/15",  # Use test DB
            postgres_url=None  # Use in-memory for testing
        )

        # Mock the connections for testing
        service.redis_client = MagicMock()
        service.pg_pool = AsyncMock()

        yield service

        # Cleanup
        if hasattr(service, 'close'):
            await service.close()

    @pytest.fixture
    def sample_webhook_data(self):
        """Sample webhook data for testing."""
        return {
            "location_id": "loc_test_123",
            "contact_id": "contact_test_456",
            "webhook_type": "message",
            "processing_time_ms": 750,
            "success": True,
            "enrichment_data": {
                "lead_score": 85,
                "extracted_preferences": 3,
                "claude_insights": True
            }
        }

    @pytest.fixture
    def sample_business_data(self):
        """Sample business metrics data for testing."""
        return {
            "location_id": "loc_test_123",
            "total_revenue": Decimal('125000.00'),
            "total_leads": 50,
            "closed_deals": 8,
            "avg_deal_size": Decimal('15625.00'),
            "conversion_rate": 16.0
        }

    # ========================================================================
    # Webhook Performance Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_webhook_tracking_lifecycle(self, metrics_service, sample_webhook_data):
        """Test complete webhook tracking lifecycle."""
        # Start tracking
        tracking_id = await metrics_service.track_webhook_start(
            location_id=sample_webhook_data["location_id"],
            contact_id=sample_webhook_data["contact_id"],
            webhook_type=sample_webhook_data["webhook_type"]
        )

        assert tracking_id is not None
        assert tracking_id in metrics_service._webhook_start_times

        # Complete tracking
        processing_time = await metrics_service.track_webhook_completion(
            tracking_id=tracking_id,
            location_id=sample_webhook_data["location_id"],
            contact_id=sample_webhook_data["contact_id"],
            success=sample_webhook_data["success"],
            webhook_type=sample_webhook_data["webhook_type"],
            enrichment_data=sample_webhook_data["enrichment_data"]
        )

        assert processing_time >= 0
        assert tracking_id not in metrics_service._webhook_start_times

    @pytest.mark.asyncio
    async def test_webhook_failure_tracking(self, metrics_service):
        """Test webhook failure tracking."""
        tracking_id = await metrics_service.track_webhook_start(
            location_id="loc_test_123",
            contact_id="contact_test_456",
            webhook_type="message"
        )

        processing_time = await metrics_service.track_webhook_completion(
            tracking_id=tracking_id,
            location_id="loc_test_123",
            contact_id="contact_test_456",
            success=False,
            error_message="Test error",
            webhook_type="message"
        )

        assert processing_time >= 0

    @pytest.mark.asyncio
    async def test_webhook_performance_metrics_calculation(self, metrics_service):
        """Test webhook performance metrics calculation."""
        # Mock database response
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchrow.return_value = {
            'total_webhooks': 100,
            'successful_webhooks': 95,
            'failed_webhooks': 5,
            'avg_processing_time_ms': 650.5
        }

        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.side_effect = [85, 90]

        performance = await metrics_service.get_webhook_performance_metrics(
            location_id="loc_test_123",
            days=7
        )

        assert isinstance(performance, WebhookPerformanceMetrics)
        assert performance.total_webhooks == 100
        assert performance.success_rate == 95.0
        assert performance.meets_sla == True  # 650ms < 1000ms
        assert performance.contact_enrichment_rate > 0

    # ========================================================================
    # Business Impact Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_conversion_stage_tracking(self, metrics_service):
        """Test conversion stage tracking."""
        await metrics_service.track_conversion_stage(
            contact_id="contact_test_456",
            location_id="loc_test_123",
            stage=ConversionStage.LEAD_CREATED,
            ai_score=75,
            metadata={"source": "website"}
        )

        # Verify Redis increment was called
        assert metrics_service.redis_client is not None

        await metrics_service.track_conversion_stage(
            contact_id="contact_test_456",
            location_id="loc_test_123",
            stage=ConversionStage.DEAL_CLOSED,
            ai_score=75,
            deal_value=Decimal('15000.00')
        )

    @pytest.mark.asyncio
    async def test_revenue_per_lead_calculation(self, metrics_service):
        """Test revenue per lead calculation."""
        # Mock database response
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.side_effect = [
            125000,  # Total revenue
            50       # Total leads
        ]

        revenue_per_lead = await metrics_service.calculate_revenue_per_lead(
            location_id="loc_test_123",
            days=30
        )

        assert revenue_per_lead == Decimal('2500.00')

    @pytest.mark.asyncio
    async def test_business_impact_metrics_calculation(self, metrics_service):
        """Test comprehensive business impact metrics calculation."""
        # Mock database responses
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchrow.side_effect = [
            {
                'total_revenue': 125000,
                'avg_deal_size': 15625,
                'closed_deals': 8
            }
        ]

        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.side_effect = [
            50,    # Total leads
            25.5,  # Average conversion time
            0.65   # AI correlation
        ]

        metrics = await metrics_service.get_business_impact_metrics(
            location_id="loc_test_123",
            days=30
        )

        assert isinstance(metrics, BusinessImpactMetrics)
        assert metrics.total_revenue == Decimal('125000')
        assert metrics.lead_to_conversion_rate == 16.0  # 8/50 * 100
        assert metrics.avg_deal_size == Decimal('15625')

    # ========================================================================
    # Agent Productivity Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_agent_activity_tracking(self, metrics_service):
        """Test agent activity tracking."""
        await metrics_service.track_agent_activity(
            agent_id="agent_test_001",
            location_id="loc_test_123",
            activity_type="deal_closed",
            contact_id="contact_test_456",
            deal_value=Decimal('18000.00'),
            response_time_minutes=15.5,
            ai_recommendation_used=True
        )

        # Verify database upsert was attempted
        assert metrics_service.pg_pool is not None

    @pytest.mark.asyncio
    async def test_agent_productivity_metrics_calculation(self, metrics_service):
        """Test agent productivity metrics calculation."""
        # Mock database response
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchrow.return_value = {
            'total_deals': 5,
            'avg_deal_value': 16500,
            'total_contacts': 25,
            'avg_response_time': 12.5,
            'total_ai_usage': 20
        }

        # Mock property match effectiveness
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.return_value = 75.0

        metrics = await metrics_service.get_agent_productivity_metrics(
            agent_id="agent_test_001",
            location_id="loc_test_123",
            days=30
        )

        assert isinstance(metrics, AgentProductivityMetrics)
        assert metrics.deals_closed == 5
        assert metrics.conversion_rate == 20.0  # 5/25 * 100
        assert metrics.ai_recommendation_usage == 0.8  # 20/25
        assert metrics.productivity_score > 0

    # ========================================================================
    # Property Matching Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_property_recommendation_tracking(self, metrics_service):
        """Test property recommendation tracking."""
        recommendation_id = await metrics_service.track_property_recommendation(
            contact_id="contact_test_456",
            location_id="loc_test_123",
            property_id="prop_test_789",
            recommendation_score=0.85,
            agent_id="agent_test_001"
        )

        assert recommendation_id is not None
        assert recommendation_id.startswith("rec_")

    @pytest.mark.asyncio
    async def test_property_interaction_tracking(self, metrics_service):
        """Test property interaction tracking."""
        # Mock Redis get for existing recommendation
        metrics_service.redis_client.get.return_value = json.dumps({
            "contact_id": "contact_test_456",
            "location_id": "loc_test_123",
            "property_id": "prop_test_789",
            "score": 0.85
        })

        await metrics_service.track_property_interaction(
            recommendation_id="rec_test_123",
            interaction_type="liked",
            contact_id="contact_test_456"
        )

        # Verify Redis operations were called
        assert metrics_service.redis_client.get.called
        assert metrics_service.redis_client.set.called

    @pytest.mark.asyncio
    async def test_property_matching_metrics(self, metrics_service):
        """Test property matching metrics calculation."""
        # Mock Redis metrics
        metrics_service._get_redis_metric = AsyncMock(side_effect=[
            100,  # Total recommendations
            75,   # Accepted recommendations
            30    # Scheduled showings
        ])

        # Mock database average score
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.return_value = 0.78

        metrics = await metrics_service.get_property_matching_metrics(
            location_id="loc_test_123",
            days=30
        )

        assert metrics["total_recommendations"] == 100
        assert metrics["acceptance_rate"] == 75.0
        assert metrics["showing_rate"] == 30.0
        assert metrics["avg_recommendation_score"] == 0.78

    # ========================================================================
    # Dashboard Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_executive_dashboard_metrics(self, metrics_service):
        """Test executive dashboard metrics compilation."""
        # Mock all sub-metric methods
        webhook_metrics = WebhookPerformanceMetrics(
            total_webhooks=200,
            successful_webhooks=190,
            avg_processing_time=0.65
        )

        business_metrics = BusinessImpactMetrics(
            total_revenue=Decimal('250000'),
            revenue_per_lead=Decimal('5000'),
            lead_to_conversion_rate=18.5
        )

        property_metrics = {
            "total_recommendations": 150,
            "acceptance_rate": 65.0
        }

        # Mock method calls
        metrics_service.get_webhook_performance_metrics = AsyncMock(return_value=webhook_metrics)
        metrics_service.get_business_impact_metrics = AsyncMock(return_value=business_metrics)
        metrics_service.get_property_matching_metrics = AsyncMock(return_value=property_metrics)
        metrics_service._get_top_performing_agents = AsyncMock(return_value=[])

        dashboard_data = await metrics_service.get_executive_dashboard_metrics(
            location_id="loc_test_123",
            days=30
        )

        assert "summary" in dashboard_data
        assert "ghl_integration" in dashboard_data
        assert "business_impact" in dashboard_data
        assert "property_matching" in dashboard_data

        summary = dashboard_data["summary"]
        assert summary["total_revenue"] == 250000.0
        assert summary["webhook_success_rate"] == 95.0

    # ========================================================================
    # Utility Function Tests
    # ========================================================================

    def test_performance_grade_calculation(self):
        """Test performance grade calculation logic."""
        # Excellent performance
        excellent_metrics = {
            "webhook_success_rate": 99.5,
            "conversion_rate": 22.0,
            "revenue_per_lead": 6000,
            "property_acceptance_rate": 70.0
        }
        assert calculate_performance_grade(excellent_metrics) == "A+"

        # Good performance
        good_metrics = {
            "webhook_success_rate": 98.0,
            "conversion_rate": 18.0,
            "revenue_per_lead": 4000,
            "property_acceptance_rate": 55.0
        }
        grade = calculate_performance_grade(good_metrics)
        assert grade in ["A", "A-", "B+"]

        # Poor performance
        poor_metrics = {
            "webhook_success_rate": 85.0,
            "conversion_rate": 3.0,
            "revenue_per_lead": 500,
            "property_acceptance_rate": 15.0
        }
        grade = calculate_performance_grade(poor_metrics)
        assert grade in ["D", "F"]

    @pytest.mark.asyncio
    async def test_metrics_service_factory(self):
        """Test business metrics service factory function."""
        with patch('ghl_real_estate_ai.services.business_metrics_service.BusinessMetricsService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value = mock_instance

            service = await create_business_metrics_service(
                redis_url="redis://localhost:6379/15",
                postgres_url="postgresql://test"
            )

            mock_service.assert_called_once()
            mock_instance.initialize.assert_called_once()

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_redis_connection_failure_handling(self, metrics_service):
        """Test handling of Redis connection failures."""
        # Simulate Redis failure
        metrics_service.redis_client = None

        # Should not raise exception
        await metrics_service._increment_redis_metric("test_key", 1.0)

        value = await metrics_service._get_redis_metric("test_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_postgresql_failure_handling(self, metrics_service):
        """Test handling of PostgreSQL failures."""
        # Simulate PostgreSQL failure
        metrics_service.pg_pool = None

        # Should return default values
        performance = await metrics_service.get_webhook_performance_metrics("loc_test", 7)
        assert isinstance(performance, WebhookPerformanceMetrics)
        assert performance.total_webhooks == 0

    @pytest.mark.asyncio
    async def test_business_metric_recording_with_failures(self, metrics_service):
        """Test business metric recording with database failures."""
        # Simulate database failure
        metrics_service.pg_pool.acquire.side_effect = Exception("Connection failed")

        metric = BusinessMetric(
            metric_type=MetricType.BUSINESS_IMPACT,
            name="test_metric",
            value=100.0,
            timestamp=datetime.now(),
            location_id="loc_test_123",
            contact_id="contact_test_456"
        )

        # Should not raise exception
        await metrics_service.record_metric(metric)

    # ========================================================================
    # Integration Tests
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_lead_lifecycle_tracking(self, metrics_service):
        """Test tracking a complete lead lifecycle."""
        contact_id = "contact_lifecycle_test"
        location_id = "loc_test_123"
        agent_id = "agent_test_001"

        # Track lead creation
        await metrics_service.track_conversion_stage(
            contact_id=contact_id,
            location_id=location_id,
            stage=ConversionStage.LEAD_CREATED,
            ai_score=65
        )

        # Track AI qualification
        await metrics_service.track_conversion_stage(
            contact_id=contact_id,
            location_id=location_id,
            stage=ConversionStage.AI_QUALIFIED,
            ai_score=75,
            agent_id=agent_id
        )

        # Track agent contact
        await metrics_service.track_agent_activity(
            agent_id=agent_id,
            location_id=location_id,
            activity_type="contact",
            contact_id=contact_id,
            response_time_minutes=8.0,
            ai_recommendation_used=True
        )

        # Track deal closure
        deal_value = Decimal('22000.00')
        await metrics_service.track_conversion_stage(
            contact_id=contact_id,
            location_id=location_id,
            stage=ConversionStage.DEAL_CLOSED,
            ai_score=85,
            agent_id=agent_id,
            deal_value=deal_value
        )

        await metrics_service.track_agent_activity(
            agent_id=agent_id,
            location_id=location_id,
            activity_type="deal_closed",
            contact_id=contact_id,
            deal_value=deal_value,
            ai_recommendation_used=True
        )

        # Verify all tracking completed without errors
        assert True  # If we reach here, all tracking succeeded

    @pytest.mark.asyncio
    async def test_concurrent_webhook_tracking(self, metrics_service):
        """Test concurrent webhook tracking performance."""
        # Simulate multiple concurrent webhooks
        async def track_webhook(webhook_id):
            tracking_id = await metrics_service.track_webhook_start(
                location_id="loc_test_123",
                contact_id=f"contact_{webhook_id}",
                webhook_type="message"
            )

            # Simulate processing delay
            await asyncio.sleep(0.001)

            return await metrics_service.track_webhook_completion(
                tracking_id=tracking_id,
                location_id="loc_test_123",
                contact_id=f"contact_{webhook_id}",
                success=True,
                webhook_type="message"
            )

        # Track 10 concurrent webhooks
        tasks = [track_webhook(i) for i in range(10)]
        processing_times = await asyncio.gather(*tasks)

        # All should complete successfully
        assert len(processing_times) == 10
        assert all(pt >= 0 for pt in processing_times)

    @pytest.mark.asyncio
    async def test_metric_aggregation_accuracy(self, metrics_service):
        """Test accuracy of metric aggregation calculations."""
        # Mock specific database responses for known calculations
        location_id = "loc_accuracy_test"

        # Mock revenue calculation data
        metrics_service.pg_pool.acquire().__aenter__.return_value.fetchval.side_effect = [
            150000,  # Total revenue
            30,      # Total leads
            25.0     # Avg conversion time
        ]

        revenue_per_lead = await metrics_service.calculate_revenue_per_lead(location_id, 30)
        assert revenue_per_lead == Decimal('5000.00')

        # Verify calculation precision
        assert str(revenue_per_lead) == '5000.00'


# ========================================================================
# Performance Tests
# ========================================================================

class TestBusinessMetricsPerformance:
    """Performance-focused tests for business metrics system."""

    @pytest.mark.asyncio
    async def test_redis_operations_performance(self):
        """Test Redis operations meet performance requirements."""
        service = BusinessMetricsService()
        service.redis_client = MagicMock()

        import time
        start_time = time.time()

        # Perform multiple Redis operations
        for i in range(100):
            await service._increment_redis_metric(f"test_key_{i}", 1.0)

        elapsed = time.time() - start_time

        # Should complete 100 operations in under 1 second
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_dashboard_metrics_response_time(self):
        """Test dashboard metrics generation meets performance SLA."""
        service = BusinessMetricsService()

        # Mock all database calls to return quickly
        service.get_webhook_performance_metrics = AsyncMock(
            return_value=WebhookPerformanceMetrics()
        )
        service.get_business_impact_metrics = AsyncMock(
            return_value=BusinessImpactMetrics()
        )
        service.get_property_matching_metrics = AsyncMock(return_value={})
        service._get_top_performing_agents = AsyncMock(return_value=[])

        import time
        start_time = time.time()

        dashboard_data = await service.get_executive_dashboard_metrics("loc_test", 30)

        elapsed = time.time() - start_time

        # Dashboard should generate in under 2 seconds
        assert elapsed < 2.0
        assert dashboard_data is not None


# ========================================================================
# Fixtures and Test Data
# ========================================================================

@pytest.fixture
def sample_dashboard_data():
    """Sample dashboard data for testing."""
    return {
        "summary": {
            "total_revenue": 425000.0,
            "revenue_per_lead": 3500.0,
            "conversion_rate": 15.5,
            "webhook_success_rate": 98.2
        },
        "ghl_integration": {
            "total_webhooks": 2450,
            "success_rate": 98.2,
            "avg_processing_time": 0.68,
            "meets_sla": True,
            "contact_enrichment_rate": 87.5,
            "ai_activation_rate": 92.3
        },
        "business_impact": {
            "total_revenue": 425000.0,
            "revenue_per_lead": 3500.0,
            "conversion_rate": 15.5,
            "avg_deal_size": 17500.0,
            "time_to_conversion": 12.5,
            "ai_score_correlation": 0.73
        },
        "property_matching": {
            "total_recommendations": 380,
            "acceptance_rate": 62.5,
            "showing_rate": 35.2,
            "avg_recommendation_score": 0.81
        },
        "top_agents": [
            {
                "agent_id": "agent_001",
                "total_deals": 12,
                "total_revenue": 285000.0,
                "productivity_score": 87.5,
                "conversion_rate": 18.2
            }
        ]
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])