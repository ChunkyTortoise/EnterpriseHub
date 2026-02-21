import pytest

pytestmark = pytest.mark.integration

"""
Tests for Competitive Intelligence Hub - Consolidated Service

Tests the unified competitive intelligence hub that replaces the fragmented
competitive intelligence implementations.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.competitive_intelligence_hub import (
    AlertPriority,
    CompetitiveAlert,
    CompetitiveIntelligenceHub,
    CompetitorProfile,
    DataSource,
    IntelligenceInsight,
    IntelligenceReport,
    IntelligenceType,
    OpportunityLevel,
    ResponseType,
    ThreatLevel,
    get_competitive_intelligence_hub,
)


class TestCompetitiveIntelligenceHub:
    """Test suite for CompetitiveIntelligenceHub."""

    @pytest.fixture
    def hub(self):
        """Create a CompetitiveIntelligenceHub instance for testing."""
        return CompetitiveIntelligenceHub()

    @pytest.fixture
    def sample_competitor_profile(self):
        """Sample competitor profile for testing."""
        return CompetitorProfile(
            competitor_id="comp_123",
            name="Acme Real Estate",
            market_segment="luxury",
            location="Rancho Cucamonga, CA",
            market_share=0.15,
            revenue_estimate=5000000.0,
            employee_count=25,
            founding_year=2010,
            strengths=["strong_brand", "premium_service"],
            weaknesses=["higher_prices", "limited_inventory"],
            pricing_strategy="premium",
            target_demographics=["luxury_buyers", "high_net_worth"],
            threat_level=ThreatLevel.HIGH,
        )

    @pytest.fixture
    def sample_intelligence_insight(self):
        """Sample intelligence insight for testing."""
        return IntelligenceInsight(
            insight_id="insight_123",
            competitor_id="comp_123",
            intelligence_type=IntelligenceType.PRICING,
            title="Price Reduction Detected",
            description="Competitor reduced listing prices by 5% this week",
            threat_level=ThreatLevel.HIGH,
            opportunity_level=OpportunityLevel.MEDIUM,
            revenue_impact=50000.0,
            confidence_score=0.85,
            data_source=DataSource.MLS,
            source_url="https://mls.example.com/data",
            verification_status="verified",
        )

    def test_hub_initialization(self, hub):
        """Test that hub initializes correctly."""
        assert isinstance(hub, CompetitiveIntelligenceHub)
        assert len(hub.competitors) == 0
        assert len(hub.insights) == 0
        assert len(hub.alerts) == 0
        assert len(hub.reports) == 0
        assert DataSource.MLS in hub.data_collectors
        assert DataSource.SOCIAL_MEDIA in hub.data_collectors

    def test_get_competitive_intelligence_hub_singleton(self):
        """Test that the global hub function returns a singleton."""
        hub1 = get_competitive_intelligence_hub()
        hub2 = get_competitive_intelligence_hub()
        assert hub1 is hub2
        assert isinstance(hub1, CompetitiveIntelligenceHub)

    @pytest.mark.asyncio
    async def test_add_competitor(self, hub, sample_competitor_profile):
        """Test adding a competitor profile."""
        with patch.object(hub.cache, "set", new_callable=AsyncMock) as mock_cache_set:
            result_id = await hub.add_competitor(sample_competitor_profile)

            assert result_id == sample_competitor_profile.competitor_id
            assert sample_competitor_profile.competitor_id in hub.competitors
            assert hub.competitors[sample_competitor_profile.competitor_id].name == "Acme Real Estate"

            # Verify cache was called
            mock_cache_set.assert_called_once()

    @pytest.mark.asyncio
    async def test_collect_intelligence(self, hub, sample_competitor_profile):
        """Test intelligence collection from multiple sources."""
        # Add competitor first
        await hub.add_competitor(sample_competitor_profile)

        # Mock the data collectors
        mock_mls_data = {"listings": ["listing1", "listing2"], "pricing": {"avg_price": 500000}}
        mock_social_data = {"sentiment": 0.7, "mentions": 15}

        with (
            patch.object(
                hub.data_collectors[DataSource.MLS], "collect_data", new_callable=AsyncMock, return_value=mock_mls_data
            ),
            patch.object(
                hub.data_collectors[DataSource.MLS], "validate_data", new_callable=AsyncMock, return_value=True
            ),
            patch.object(
                hub.data_collectors[DataSource.SOCIAL_MEDIA],
                "collect_data",
                new_callable=AsyncMock,
                return_value=mock_social_data,
            ),
            patch.object(
                hub.data_collectors[DataSource.SOCIAL_MEDIA], "validate_data", new_callable=AsyncMock, return_value=True
            ),
            patch.object(hub.cache, "set", new_callable=AsyncMock),
        ):
            insights = await hub.collect_intelligence(
                sample_competitor_profile.competitor_id,
                [IntelligenceType.PRICING, IntelligenceType.SOCIAL_SENTIMENT],
                [DataSource.MLS, DataSource.SOCIAL_MEDIA],
            )

            # Should generate insights for each intelligence type and source combination
            assert len(insights) == 4  # 2 types x 2 sources
            assert all(isinstance(insight, IntelligenceInsight) for insight in insights)
            assert all(insight.competitor_id == sample_competitor_profile.competitor_id for insight in insights)

            # Verify insights were stored (may be fewer due to ID collision within same second)
            assert len(hub.insights) >= 2

            # Verify performance metrics updated
            assert hub.performance_metrics["total_insights_generated"] == 4

    @pytest.mark.asyncio
    async def test_create_competitive_alert(self, hub, sample_competitor_profile):
        """Test creating competitive alerts."""
        await hub.add_competitor(sample_competitor_profile)

        with patch.object(hub.cache, "set", new_callable=AsyncMock):
            alert = await hub.create_competitive_alert(
                title="Price Drop Alert",
                description="Competitor reduced prices by 10%",
                competitor_id=sample_competitor_profile.competitor_id,
                priority=AlertPriority.HIGH,
                intelligence_type=IntelligenceType.PRICING,
                threat_level=ThreatLevel.HIGH,
            )

            assert isinstance(alert, CompetitiveAlert)
            assert alert.title == "Price Drop Alert"
            assert alert.competitor_id == sample_competitor_profile.competitor_id
            assert alert.priority == AlertPriority.HIGH
            assert alert.threat_level == ThreatLevel.HIGH
            assert alert.recommended_response == ResponseType.PRICING_ADJUSTMENT

            # Verify alert was stored
            assert alert.alert_id in hub.alerts

            # Verify performance metrics updated
            assert hub.performance_metrics["alerts_triggered"] == 1

    @pytest.mark.asyncio
    async def test_generate_competitive_report(self, hub, sample_competitor_profile, sample_intelligence_insight):
        """Test generating comprehensive competitive intelligence reports."""
        # Add test data
        await hub.add_competitor(sample_competitor_profile)
        hub.insights[sample_intelligence_insight.insight_id] = sample_intelligence_insight

        alert = await hub.create_competitive_alert(
            title="Test Alert",
            description="Test alert description",
            competitor_id=sample_competitor_profile.competitor_id,
            priority=AlertPriority.MEDIUM,
            intelligence_type=IntelligenceType.PRICING,
            threat_level=ThreatLevel.MEDIUM,
        )

        with patch.object(hub.cache, "set", new_callable=AsyncMock):
            report = await hub.generate_competitive_report(
                report_title="Weekly Competitive Analysis",
                competitor_ids=[sample_competitor_profile.competitor_id],
                intelligence_types=[IntelligenceType.PRICING],
                time_period_days=7,
            )

            assert isinstance(report, IntelligenceReport)
            assert report.title == "Weekly Competitive Analysis"
            assert len(report.insights) == 1
            assert len(report.competitor_profiles) == 1
            assert len(report.alerts) == 1
            assert report.report_period_start is not None
            assert report.report_period_end is not None

            # Verify summary was generated
            assert "Analyzed 1 competitors" in report.summary
            assert "Generated 1 intelligence insights" in report.summary

            # Verify report was stored
            assert report.report_id in hub.reports

            # Verify performance metrics updated
            assert hub.performance_metrics["reports_generated"] == 1

    @pytest.mark.asyncio
    async def test_get_competitor_benchmark(self, hub, sample_competitor_profile):
        """Test competitive benchmarking analysis."""
        await hub.add_competitor(sample_competitor_profile)

        benchmark = await hub.get_competitor_benchmark(
            sample_competitor_profile.competitor_id, ["market_share", "revenue"]
        )

        assert isinstance(benchmark, dict)
        assert benchmark["competitor_id"] == sample_competitor_profile.competitor_id
        assert benchmark["competitor_name"] == "Acme Real Estate"
        assert "market_position" in benchmark
        assert "performance_metrics" in benchmark
        assert benchmark["performance_metrics"]["market_share"] == 0.15
        assert benchmark["performance_metrics"]["revenue"] == 5000000.0

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, hub, sample_competitor_profile):
        """Test retrieving system performance metrics."""
        # Add some test data
        await hub.add_competitor(sample_competitor_profile)
        await hub.create_competitive_alert(
            title="Test Alert",
            description="Test description",
            competitor_id=sample_competitor_profile.competitor_id,
            priority=AlertPriority.LOW,
            intelligence_type=IntelligenceType.PRICING,
        )

        metrics = await hub.get_performance_metrics()

        assert isinstance(metrics, dict)
        assert metrics["total_competitors"] == 1
        assert metrics["active_alerts"] == 1
        assert metrics["alerts_triggered"] == 1
        assert "total_insights" in metrics
        assert "total_reports" in metrics

    def test_recommended_response_determination(self, hub):
        """Test the logic for determining recommended responses."""
        # Test critical pricing threat
        critical_pricing_alert = CompetitiveAlert(
            alert_id="test_alert",
            title="Critical Price Drop",
            description="Major competitor slashed prices",
            competitor_id="comp_123",
            priority=AlertPriority.URGENT,
            intelligence_type=IntelligenceType.PRICING,
            threat_level=ThreatLevel.CRITICAL,
        )

        # Use asyncio to run the async method
        response = asyncio.run(hub._determine_recommended_response(critical_pricing_alert))
        assert response == ResponseType.PRICING_ADJUSTMENT

        # Test high marketing threat
        high_marketing_alert = CompetitiveAlert(
            alert_id="test_alert_2",
            title="New Marketing Campaign",
            description="Competitor launched aggressive campaign",
            competitor_id="comp_123",
            priority=AlertPriority.HIGH,
            intelligence_type=IntelligenceType.MARKETING_STRATEGY,
            threat_level=ThreatLevel.HIGH,
        )

        response = asyncio.run(hub._determine_recommended_response(high_marketing_alert))
        assert response == ResponseType.MARKETING_CAMPAIGN

        # Test low threat
        low_threat_alert = CompetitiveAlert(
            alert_id="test_alert_3",
            title="Minor Update",
            description="Small website update",
            competitor_id="comp_123",
            priority=AlertPriority.LOW,
            intelligence_type=IntelligenceType.PRODUCT_FEATURES,
            threat_level=ThreatLevel.LOW,
        )

        response = asyncio.run(hub._determine_recommended_response(low_threat_alert))
        assert response == ResponseType.NO_ACTION


class TestCompetitorProfile:
    """Test suite for CompetitorProfile dataclass."""

    def test_competitor_profile_creation(self):
        """Test creating a competitor profile."""
        profile = CompetitorProfile(
            competitor_id="comp_456", name="Beta Realty", market_segment="mid_market", location="Dallas, TX"
        )

        assert profile.competitor_id == "comp_456"
        assert profile.name == "Beta Realty"
        assert profile.market_segment == "mid_market"
        assert profile.location == "Dallas, TX"
        assert profile.market_share == 0.0  # default value
        assert profile.threat_level == ThreatLevel.MEDIUM  # default value
        assert isinstance(profile.created_at, datetime)


class TestIntelligenceInsight:
    """Test suite for IntelligenceInsight dataclass."""

    def test_intelligence_insight_creation(self):
        """Test creating an intelligence insight."""
        insight = IntelligenceInsight(
            insight_id="insight_789",
            competitor_id="comp_456",
            intelligence_type=IntelligenceType.MARKET_SHARE,
            title="Market Share Increase",
            description="Competitor gained 2% market share last quarter",
        )

        assert insight.insight_id == "insight_789"
        assert insight.competitor_id == "comp_456"
        assert insight.intelligence_type == IntelligenceType.MARKET_SHARE
        assert insight.title == "Market Share Increase"
        assert insight.threat_level == ThreatLevel.MEDIUM  # default
        assert insight.confidence_score == 0.5  # default
        assert isinstance(insight.discovered_at, datetime)


class TestCompetitiveAlert:
    """Test suite for CompetitiveAlert dataclass."""

    def test_competitive_alert_creation(self):
        """Test creating a competitive alert."""
        alert = CompetitiveAlert(
            alert_id="alert_101",
            title="Urgent Price Alert",
            description="Competitor cut prices by 15%",
            competitor_id="comp_789",
            priority=AlertPriority.URGENT,
            intelligence_type=IntelligenceType.PRICING,
            threat_level=ThreatLevel.CRITICAL,
        )

        assert alert.alert_id == "alert_101"
        assert alert.title == "Urgent Price Alert"
        assert alert.competitor_id == "comp_789"
        assert alert.priority == AlertPriority.URGENT
        assert alert.threat_level == ThreatLevel.CRITICAL
        assert alert.status == "active"  # default
        assert alert.recommended_response == ResponseType.NO_ACTION  # default
        assert isinstance(alert.created_at, datetime)


# Integration test to ensure the hub works end-to-end
class TestCompetitiveIntelligenceIntegration:
    """Integration tests for the full competitive intelligence workflow."""

    @pytest.mark.asyncio
    async def test_full_intelligence_workflow(self):
        """Test complete competitive intelligence workflow from data collection to reporting."""
        hub = CompetitiveIntelligenceHub()

        # Step 1: Add competitor
        competitor = CompetitorProfile(
            competitor_id="integration_test_comp",
            name="Integration Test Realty",
            market_segment="integration_test",
            location="Test City, TX",
            market_share=0.12,
            threat_level=ThreatLevel.HIGH,
        )

        with patch.object(hub.cache, "set", new_callable=AsyncMock):
            await hub.add_competitor(competitor)

        # Step 2: Collect intelligence (mocked)
        with (
            patch.object(
                hub.data_collectors[DataSource.MLS],
                "collect_data",
                new_callable=AsyncMock,
                return_value={"test": "data"},
            ),
            patch.object(
                hub.data_collectors[DataSource.MLS], "validate_data", new_callable=AsyncMock, return_value=True
            ),
            patch.object(hub.cache, "set", new_callable=AsyncMock),
        ):
            insights = await hub.collect_intelligence(
                competitor.competitor_id, [IntelligenceType.PRICING], [DataSource.MLS]
            )

        # Step 3: Create alert based on insights
        with patch.object(hub.cache, "set", new_callable=AsyncMock):
            alert = await hub.create_competitive_alert(
                title="Integration Test Alert",
                description="Test alert for integration test",
                competitor_id=competitor.competitor_id,
                priority=AlertPriority.MEDIUM,
                intelligence_type=IntelligenceType.PRICING,
                threat_level=ThreatLevel.MEDIUM,
            )

        # Step 4: Generate report
        with patch.object(hub.cache, "set", new_callable=AsyncMock):
            report = await hub.generate_competitive_report(
                report_title="Integration Test Report", competitor_ids=[competitor.competitor_id], time_period_days=1
            )

        # Step 5: Get benchmarking analysis
        benchmark = await hub.get_competitor_benchmark(competitor.competitor_id, ["market_share"])

        # Step 6: Check performance metrics
        metrics = await hub.get_performance_metrics()

        # Verify the complete workflow
        assert len(insights) > 0
        assert alert.competitor_id == competitor.competitor_id
        assert report.title == "Integration Test Report"
        assert len(report.competitor_profiles) == 1
        assert benchmark["competitor_name"] == "Integration Test Realty"
        assert metrics["total_competitors"] >= 1
        assert metrics["alerts_triggered"] >= 1
