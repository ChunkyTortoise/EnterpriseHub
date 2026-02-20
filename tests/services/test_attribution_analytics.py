import pytest

pytestmark = pytest.mark.integration

"""
Tests for AttributionAnalytics service.

Comprehensive test suite for attribution reporting, analytics, and optimization recommendations.
"""

import asyncio
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.attribution_analytics import (
    AlertType,
    AttributionAnalytics,
    AttributionModel,
    AttributionReport,
    ChannelForecast,
    CohortAnalysis,
    PerformanceAlert,
    ReportPeriod,
)
from ghl_real_estate_ai.services.lead_source_tracker import LeadSource, SourcePerformance


class TestAttributionAnalytics:
    """Test suite for AttributionAnalytics class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.analytics = AttributionAnalytics()

    @pytest.mark.asyncio
    async def test_generate_attribution_report_basic(self):
        """Test basic attribution report generation."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        # Mock source performance data
        mock_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=start_date,
                period_end=end_date,
                total_leads=50,
                qualified_leads=20,
                total_revenue=100000.0,
                cost_per_lead=25.0,
                roi=3.0,
            ),
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS,
                period_start=start_date,
                period_end=end_date,
                total_leads=80,
                qualified_leads=25,
                total_revenue=75000.0,
                cost_per_lead=20.0,
                roi=1.8,
            ),
        ]

        with patch.object(self.analytics.source_tracker, "get_all_source_performance", return_value=mock_performances):
            report = await self.analytics.generate_attribution_report(
                start_date, end_date, include_forecasts=False, include_cohorts=False
            )

            assert report.period_start == start_date
            assert report.period_end == end_date
            assert report.total_leads == 130  # 50 + 80
            assert report.total_qualified_leads == 45  # 20 + 25
            assert report.total_revenue == 175000.0  # 100k + 75k
            assert len(report.source_performance) == 2
            assert report.overall_roi > 0

    @pytest.mark.asyncio
    async def test_generate_performance_alerts(self):
        """Test performance alert generation."""
        # Current performance
        current_performances = [
            SourcePerformance(
                source=LeadSource.GOOGLE_ADS,
                period_start=datetime.utcnow() - timedelta(days=7),
                period_end=datetime.utcnow(),
                total_leads=20,
                roi=-0.3,  # Negative ROI - should trigger alert
                qualification_rate=0.15,
            ),
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=7),
                period_end=datetime.utcnow(),
                total_leads=5,  # Low volume
                roi=2.0,
                qualification_rate=0.8,
            ),
        ]

        # Previous performance (better)
        previous_performances = [
            SourcePerformance(
                source=LeadSource.GOOGLE_ADS,
                period_start=datetime.utcnow() - timedelta(days=14),
                period_end=datetime.utcnow() - timedelta(days=7),
                total_leads=30,
                roi=1.5,  # Was profitable
                qualification_rate=0.25,
            )
        ]

        # Mock getting previous period performance
        async def mock_get_previous_performance(source, start, end):
            for perf in previous_performances:
                if perf.source == source:
                    return perf
            return None

        with patch.object(
            self.analytics, "_get_previous_period_performance", side_effect=mock_get_previous_performance
        ):
            alerts = await self.analytics._generate_performance_alerts(current_performances)

            # Should generate alerts for ROI drop and quality drop
            assert len(alerts) > 0

            alert_types = [alert.alert_type for alert in alerts]
            assert AlertType.ROI_DROP in alert_types

            # Check ROI drop alert details
            roi_alert = next(alert for alert in alerts if alert.alert_type == AlertType.ROI_DROP)
            assert roi_alert.source == LeadSource.GOOGLE_ADS
            assert roi_alert.severity in ["high", "medium"]
            assert len(roi_alert.recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_optimization_recommendations(self):
        """Test optimization recommendation generation."""
        # Mock performance data with clear optimization opportunities
        source_performances = [
            # High ROI, high volume - good performer
            SourcePerformance(
                source=LeadSource.AGENT_REFERRAL,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=30,
                roi=5.0,
                qualification_rate=0.8,
            ),
            # Low ROI, high volume - needs optimization
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=100,
                roi=0.1,  # Very low ROI
                qualification_rate=0.15,
            ),
            # Good ROI, low volume - scale opportunity
            SourcePerformance(
                source=LeadSource.GOOGLE_ADS,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=15,  # Low volume
                roi=2.5,
                qualification_rate=0.6,
            ),
        ]

        # Mock alerts
        mock_alerts = [
            PerformanceAlert(
                alert_type=AlertType.ROI_DROP,
                source=LeadSource.FACEBOOK_ADS,
                severity="high",
                title="ROI Drop",
                description="ROI dropped significantly",
                current_value=0.1,
                previous_value=0.8,
                threshold=-0.2,
                change_percentage=-0.875,
                recommendations=["Review targeting"],
                created_at=datetime.utcnow(),
            )
        ]

        recommendations = await self.analytics._generate_optimization_recommendations(source_performances, mock_alerts)

        assert len(recommendations) > 0

        # Should recommend budget reallocation
        rec_types = [r["type"] for r in recommendations]
        assert "budget_reallocation" in rec_types or "scale_winners" in rec_types

        # Should identify urgent actions based on alerts
        assert any(r["type"] == "urgent_action_required" for r in recommendations)

    @pytest.mark.asyncio
    async def test_track_daily_metrics(self):
        """Test daily metrics tracking."""
        source = LeadSource.ZILLOW
        leads = 5
        revenue = 10000.0
        cost = 500.0

        with (
            patch.object(
                self.analytics.cache, "get", return_value={"leads": 0, "revenue": 0.0, "cost": 0.0}
            ) as mock_get,
            patch.object(self.analytics.cache, "set") as mock_set,
        ):
            await self.analytics.track_daily_metrics(source, leads, revenue, cost)

            # Verify cache operations
            mock_get.assert_called_once()
            mock_set.assert_called_once()

            # Verify the data structure passed to cache
            call_args = mock_set.call_args
            updated_data = call_args[0][1]  # Second argument is the data

            assert updated_data["leads"] == leads
            assert updated_data["revenue"] == revenue
            assert updated_data["cost"] == cost

    @pytest.mark.asyncio
    async def test_get_weekly_summary(self):
        """Test weekly summary generation."""
        # Mock current week performance
        current_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=7),
                period_end=datetime.utcnow(),
                total_leads=25,
                qualified_leads=10,
                total_revenue=50000.0,
                roi=2.0,
            ),
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS,
                period_start=datetime.utcnow() - timedelta(days=7),
                period_end=datetime.utcnow(),
                total_leads=40,
                qualified_leads=12,
                total_revenue=30000.0,
                roi=1.2,
            ),
        ]

        # Mock previous week performance
        previous_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=14),
                period_end=datetime.utcnow() - timedelta(days=7),
                total_leads=20,
                qualified_leads=8,
                total_revenue=40000.0,
                roi=1.8,
            )
        ]

        async def mock_get_all_performance(start_date, end_date):
            if start_date > datetime.utcnow() - timedelta(days=8):
                return current_performances
            else:
                return previous_performances

        with (
            patch.object(
                self.analytics.source_tracker, "get_all_source_performance", side_effect=mock_get_all_performance
            ),
            patch.object(self.analytics, "_generate_performance_alerts", return_value=[]),
        ):
            summary = await self.analytics.get_weekly_summary()

            assert "totals" in summary
            assert summary["totals"]["leads"] == 65  # 25 + 40
            assert summary["totals"]["qualified_leads"] == 22  # 10 + 12
            assert summary["totals"]["revenue"] == 80000.0  # 50k + 30k

            # Should have top sources
            assert "top_sources" in summary
            assert len(summary["top_sources"]) > 0

            # Should calculate changes from previous week
            assert "biggest_changes" in summary
            assert summary["alerts_count"] == 0

    @pytest.mark.asyncio
    async def test_get_monthly_trends(self):
        """Test monthly trend analysis."""

        # Mock monthly performance data
        def mock_get_performance(start_date, end_date):
            # Return different data based on the month
            month_diff = (datetime.utcnow() - start_date).days // 30
            base_leads = 100 + (month_diff * 10)  # Growing trend

            return [
                SourcePerformance(
                    source=LeadSource.ZILLOW,
                    period_start=start_date,
                    period_end=end_date,
                    total_leads=base_leads,
                    total_revenue=base_leads * 1000,
                    cost_per_lead=20.0,
                )
            ]

        with patch.object(
            self.analytics.source_tracker, "get_all_source_performance", side_effect=mock_get_performance
        ):
            trends = await self.analytics.get_monthly_trends()

            assert "monthly_performance" in trends
            assert len(trends["monthly_performance"]) == 6  # 6 months of data

            # Should calculate growth rates
            assert "growth_rates" in trends
            assert "leads" in trends["growth_rates"]
            assert "revenue" in trends["growth_rates"]

            # Verify data structure
            for month_data in trends["monthly_performance"]:
                assert "month" in month_data
                assert "total_leads" in month_data
                assert "total_revenue" in month_data
                assert "roi" in month_data

    @pytest.mark.asyncio
    async def test_forecast_channel_performance(self):
        """Test channel performance forecasting."""
        # Mock performance data
        performance = SourcePerformance(
            source=LeadSource.GOOGLE_ADS,
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            total_leads=100,
            qualification_rate=0.3,
            total_revenue=50000.0,
        )

        # Mock historical data points
        historical_data = [
            {
                "date": date.today() - timedelta(days=i),
                "leads": 3 + i % 5,
                "revenue": (3 + i % 5) * 500,
                "cost": (3 + i % 5) * 20,
            }
            for i in range(30)
        ]

        with patch.object(self.analytics, "_get_historical_data_points", return_value=historical_data):
            forecast = await self.analytics._forecast_channel_performance(performance)

            assert forecast is not None
            assert forecast.source == LeadSource.GOOGLE_ADS
            assert forecast.predicted_leads > 0
            assert forecast.predicted_revenue > 0
            assert forecast.predicted_qualified_leads > 0
            assert forecast.confidence_level > 0
            assert forecast.leads_lower_bound <= forecast.predicted_leads <= forecast.leads_upper_bound

    @pytest.mark.asyncio
    async def test_compare_attribution_models(self):
        """Test attribution model comparison."""
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        # Mock source performances
        mock_performances = [
            SourcePerformance(
                source=LeadSource.AGENT_REFERRAL, period_start=start_date, period_end=end_date, total_revenue=50000.0
            ),
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS, period_start=start_date, period_end=end_date, total_revenue=30000.0
            ),
        ]

        with patch.object(self.analytics.source_tracker, "get_all_source_performance", return_value=mock_performances):
            comparison = await self.analytics._compare_attribution_models(start_date, end_date)

            # Should have data for different models
            assert AttributionModel.LAST_TOUCH.value in comparison
            assert AttributionModel.FIRST_TOUCH.value in comparison
            assert AttributionModel.LINEAR.value in comparison

            # Each model should have revenue attribution for sources
            for model_data in comparison.values():
                assert LeadSource.AGENT_REFERRAL.value in model_data
                assert LeadSource.FACEBOOK_ADS.value in model_data

    def test_calculate_trend(self):
        """Test trend calculation algorithm."""
        # Test positive trend
        data_points = [1, 2, 3, 4, 5]
        trend = self.analytics._calculate_trend(data_points)
        assert trend > 0  # Should detect upward trend

        # Test negative trend
        data_points = [5, 4, 3, 2, 1]
        trend = self.analytics._calculate_trend(data_points)
        assert trend < 0  # Should detect downward trend

        # Test flat trend
        data_points = [3, 3, 3, 3, 3]
        trend = self.analytics._calculate_trend(data_points)
        assert abs(trend) < 0.1  # Should be close to zero

        # Test edge cases
        assert self.analytics._calculate_trend([]) == 0.0
        assert self.analytics._calculate_trend([1]) == 0.0

    @pytest.mark.asyncio
    async def test_get_historical_data_points(self):
        """Test historical data point retrieval."""
        source = LeadSource.ZILLOW
        days = 30

        # Mock cache data
        cache_data = {"leads": 5, "revenue": 10000.0, "cost": 200.0}

        with patch.object(self.analytics.cache, "get", return_value=cache_data):
            data_points = await self.analytics._get_historical_data_points(source, days)

            assert len(data_points) == days + 1  # Inclusive of end date

            # Each data point should have required fields
            for point in data_points:
                assert "date" in point
                assert "leads" in point
                assert "revenue" in point
                assert "cost" in point

    @pytest.mark.asyncio
    async def test_analyze_source_cohort(self):
        """Test source cohort analysis."""
        source = LeadSource.FACEBOOK_ADS
        cohort_date = date.today() - timedelta(days=30)

        # Mock cohort data
        cohort_data = {
            "cohort_size": 100,
            "day_1_conversions": 2,
            "day_7_conversions": 8,
            "day_30_conversions": 15,
            "day_1_revenue": 4000.0,
            "day_7_revenue": 16000.0,
            "day_30_revenue": 30000.0,
            "avg_lead_score": 4.5,
            "qualification_rate": 0.25,
            "avg_response_time": 45.0,
        }

        with patch.object(self.analytics.cache, "get", return_value=cohort_data):
            cohort = await self.analytics._analyze_source_cohort(source, cohort_date)

            assert cohort is not None
            assert cohort.source == source
            assert cohort.cohort_date == cohort_date
            assert cohort.cohort_size == 100
            assert cohort.day_1_conversion == 0.02  # 2/100
            assert cohort.day_7_conversion == 0.08  # 8/100
            assert cohort.day_30_conversion == 0.15  # 15/100

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in analytics operations."""
        # Test with source tracker failures that propagate to analytics
        with patch.object(
            self.analytics.source_tracker, "get_all_source_performance", side_effect=Exception("Source tracker error")
        ):
            # Should handle errors gracefully
            summary = await self.analytics.get_weekly_summary()
            assert "error" in summary

            trends = await self.analytics.get_monthly_trends()
            assert "error" in trends

        # Test with invalid date ranges
        future_date = datetime.utcnow() + timedelta(days=30)
        past_date = datetime.utcnow() - timedelta(days=30)

        # Should handle gracefully (future end date)
        report = await self.analytics.generate_attribution_report(start_date=past_date, end_date=future_date)
        assert report.period_start == past_date
        assert report.period_end == future_date

    def test_alert_threshold_configuration(self):
        """Test alert threshold configuration."""
        thresholds = self.analytics.alert_thresholds

        assert AlertType.ROI_DROP in thresholds
        assert AlertType.COST_SPIKE in thresholds
        assert AlertType.VOLUME_DROP in thresholds
        assert AlertType.QUALITY_DROP in thresholds
        assert AlertType.CONVERSION_DROP in thresholds

        # Thresholds should be reasonable negative values for drops
        assert thresholds[AlertType.ROI_DROP] < 0
        assert thresholds[AlertType.VOLUME_DROP] < 0
        assert thresholds[AlertType.QUALITY_DROP] < 0
        assert thresholds[AlertType.CONVERSION_DROP] < 0

        # Cost spike should be positive
        assert thresholds[AlertType.COST_SPIKE] > 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent analytics operations."""
        # Test multiple operations running concurrently
        tasks = [
            self.analytics.get_weekly_summary(),
            self.analytics.get_monthly_trends(),
            self.analytics.track_daily_metrics(LeadSource.ZILLOW, 1, 0.0, 0.0),
            self.analytics.track_daily_metrics(LeadSource.FACEBOOK_ADS, 2, 0.0, 0.0),
        ]

        with (
            patch.object(self.analytics.source_tracker, "get_all_source_performance", return_value=[]),
            patch.object(self.analytics.cache, "get", return_value={}),
            patch.object(self.analytics.cache, "set", return_value=True),
        ):
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All operations should complete without exceptions
            for result in results:
                assert not isinstance(result, Exception)