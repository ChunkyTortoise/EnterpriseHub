import pytest

pytestmark = pytest.mark.integration

"""
Tests for Attribution Reports API endpoints.

Comprehensive test suite for attribution reporting API endpoints and dashboard integration.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.attribution_analytics import AlertType, AttributionReport, PerformanceAlert
from ghl_real_estate_ai.services.lead_source_tracker import LeadSource, SourcePerformance, SourceQuality


class TestAttributionReportsAPI:
    """Test suite for Attribution Reports API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
        self.base_url = "/api/attribution"

    def test_get_source_performance_success(self):
        """Test successful source performance retrieval."""
        # Mock performance data
        mock_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=50,
                qualified_leads=20,
                hot_leads=10,
                conversion_rate=0.08,
                qualification_rate=0.40,
                total_revenue=100000.0,
                avg_deal_size=5000.0,
                cost_per_lead=25.0,
                cost_per_qualified_lead=62.50,
                roi=3.0,
                avg_lead_score=6.5,
                avg_budget=450000.0,
            ),
            SourcePerformance(
                source=LeadSource.FACEBOOK_ADS,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=80,
                qualified_leads=25,
                hot_leads=12,
                conversion_rate=0.06,
                qualification_rate=0.31,
                total_revenue=75000.0,
                avg_deal_size=4500.0,
                cost_per_lead=20.0,
                cost_per_qualified_lead=64.0,
                roi=1.8,
                avg_lead_score=5.2,
                avg_budget=380000.0,
            ),
        ]

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_performances)()
            )

            response = self.client.get(f"{self.base_url}/performance")

            assert response.status_code == 200
            data = response.json()

            assert len(data) == 2
            assert data[0]["source"] == "zillow"
            assert data[0]["total_leads"] == 50
            assert data[0]["roi"] == 3.0

    def test_get_source_performance_with_filters(self):
        """Test source performance with query filters."""
        mock_performance = SourcePerformance(
            source=LeadSource.ZILLOW,
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            total_leads=25,
            qualified_leads=10,
            roi=2.5,
        )

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_source_performance.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_performance)()
            )

            # Test single source filter
            response = self.client.get(
                f"{self.base_url}/performance",
                params={
                    "source": "zillow",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "sort_by": "roi",
                    "order": "desc",
                },
            )

            assert response.status_code == 200
            data = response.json()

            assert len(data) == 1
            assert data[0]["source"] == "zillow"

    def test_get_source_performance_invalid_source(self):
        """Test error handling for invalid source."""
        response = self.client.get(f"{self.base_url}/performance", params={"source": "invalid_source"})

        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]

    def test_generate_attribution_report_success(self):
        """Test successful attribution report generation."""
        # Mock report data
        mock_report = AttributionReport(
            period_start=datetime.utcnow() - timedelta(days=30),
            period_end=datetime.utcnow(),
            generated_at=datetime.utcnow(),
            total_leads=100,
            total_qualified_leads=35,
            total_revenue=175000.0,
            total_cost=5000.0,
            overall_roi=34.0,
            source_performance=[
                SourcePerformance(
                    source=LeadSource.ZILLOW,
                    period_start=datetime.utcnow() - timedelta(days=30),
                    period_end=datetime.utcnow(),
                    total_leads=50,
                    qualified_leads=20,
                    roi=3.0,
                )
            ],
            active_alerts=[
                PerformanceAlert(
                    alert_type=AlertType.ROI_DROP,
                    source=LeadSource.FACEBOOK_ADS,
                    severity="high",
                    title="ROI Drop Alert",
                    description="ROI dropped significantly",
                    current_value=0.5,
                    previous_value=2.0,
                    threshold=-0.2,
                    change_percentage=-0.75,
                    recommendations=["Review targeting", "Optimize ad creative"],
                    created_at=datetime.utcnow(),
                )
            ],
            optimization_recommendations=[
                {
                    "type": "budget_reallocation",
                    "priority": "high",
                    "title": "Reallocate Budget",
                    "description": "Move budget to higher ROI sources",
                }
            ],
        )

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.generate_attribution_report.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_report)()
            )

            response = self.client.get(f"{self.base_url}/report")

            assert response.status_code == 200
            data = response.json()

            assert data["total_leads"] == 100
            assert data["total_qualified_leads"] == 35
            assert data["overall_roi"] == 34.0
            assert len(data["source_performance"]) == 1
            assert len(data["active_alerts"]) == 1
            assert len(data["optimization_recommendations"]) == 1

    def test_generate_attribution_report_with_params(self):
        """Test attribution report with custom parameters."""
        mock_report = AttributionReport(
            period_start=datetime.utcnow() - timedelta(days=7),
            period_end=datetime.utcnow(),
            generated_at=datetime.utcnow(),
            total_leads=25,
            total_qualified_leads=10,
        )

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.generate_attribution_report.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_report)()
            )

            response = self.client.get(
                f"{self.base_url}/report",
                params={
                    "start_date": "2024-01-15",
                    "end_date": "2024-01-22",
                    "attribution_model": "first_touch",
                    "include_forecasts": "false",
                    "include_cohorts": "false",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify the report was generated
            assert "total_leads" in data
            assert "total_qualified_leads" in data

    def test_get_weekly_summary_success(self):
        """Test weekly summary retrieval."""
        mock_summary = {
            "period": {
                "start": (datetime.utcnow() - timedelta(days=7)).isoformat(),
                "end": datetime.utcnow().isoformat(),
            },
            "totals": {"leads": 75, "qualified_leads": 30, "revenue": 125000.0, "cost": 3500.0, "roi": 34.7},
            "top_sources": [
                {"source": "zillow", "leads": 25, "revenue": 60000.0, "roi": 4.2},
                {"source": "agent_referral", "leads": 15, "revenue": 45000.0, "roi": 8.0},
            ],
            "biggest_changes": [{"source": "facebook_ads", "lead_change": 0.5, "roi_change": -0.3, "magnitude": 0.8}],
            "alerts_count": 2,
        }

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.get_weekly_summary.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_summary)()
            )

            response = self.client.get(f"{self.base_url}/weekly-summary")

            assert response.status_code == 200
            data = response.json()

            assert data["totals"]["leads"] == 75
            assert data["totals"]["roi"] == 34.7
            assert len(data["top_sources"]) == 2
            assert data["alerts_count"] == 2

    def test_get_weekly_summary_with_location_filter(self):
        """Test weekly summary with location filter."""
        mock_summary = {
            "period": {"start": "2024-01-15", "end": "2024-01-22"},
            "totals": {"leads": 25, "qualified_leads": 10},
            "top_sources": [],
            "biggest_changes": [],
            "alerts_count": 0,
        }

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.get_weekly_summary.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_summary)()
            )

            response = self.client.get(f"{self.base_url}/weekly-summary", params={"location_id": "test_location_123"})

            assert response.status_code == 200

    def test_get_monthly_trends_success(self):
        """Test monthly trends retrieval."""
        mock_trends = {
            "monthly_performance": [
                {"month": "2024-01", "total_leads": 100, "total_revenue": 150000.0, "roi": 2.8},
                {"month": "2024-02", "total_leads": 120, "total_revenue": 180000.0, "roi": 3.1},
                {"month": "2024-03", "total_leads": 110, "total_revenue": 175000.0, "roi": 2.9},
            ],
            "growth_rates": {
                "leads": 0.15,  # 15% growth
                "revenue": 0.18,  # 18% growth
                "roi": 0.03,  # 3% ROI improvement
            },
        }

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.get_monthly_trends.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_trends)()
            )

            response = self.client.get(f"{self.base_url}/trends")

            assert response.status_code == 200
            data = response.json()

            assert len(data["monthly_performance"]) == 3
            assert "growth_rates" in data
            assert data["growth_rates"]["leads"] == 0.15

    def test_get_active_alerts_success(self):
        """Test active alerts retrieval."""
        mock_alerts = [
            PerformanceAlert(
                alert_type=AlertType.ROI_DROP,
                source=LeadSource.FACEBOOK_ADS,
                severity="high",
                title="Facebook Ads ROI Drop",
                description="ROI dropped from 2.5 to 0.8",
                current_value=0.8,
                previous_value=2.5,
                threshold=-0.2,
                change_percentage=-0.68,
                recommendations=["Review targeting", "Update ad creative"],
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7),
            ),
            PerformanceAlert(
                alert_type=AlertType.VOLUME_DROP,
                source=LeadSource.GOOGLE_ADS,
                severity="medium",
                title="Google Ads Volume Drop",
                description="Lead volume dropped 30%",
                current_value=20,
                previous_value=30,
                threshold=-0.25,
                change_percentage=-0.33,
                recommendations=["Check budget", "Expand targeting"],
                created_at=datetime.utcnow(),
            ),
        ]

        # Mock performance data and alert generation
        with (
            patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker,
            patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics,
        ):
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(asyncio.coroutine(lambda: [])())
            mock_analytics._generate_performance_alerts.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_alerts)()
            )

            response = self.client.get(f"{self.base_url}/alerts")

            assert response.status_code == 200
            data = response.json()

            assert len(data) == 2
            assert data[0]["alert_type"] == "roi_drop"
            assert data[0]["severity"] == "high"
            assert data[1]["alert_type"] == "volume_drop"

    def test_get_active_alerts_with_filters(self):
        """Test alerts with severity and source filters."""
        mock_alerts = [
            PerformanceAlert(
                alert_type=AlertType.ROI_DROP,
                source=LeadSource.FACEBOOK_ADS,
                severity="high",
                title="High Severity Alert",
                description="Critical issue",
                current_value=0.1,
                previous_value=2.0,
                threshold=-0.2,
                change_percentage=-0.95,
                recommendations=["Immediate action required"],
                created_at=datetime.utcnow(),
            )
        ]

        with (
            patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker,
            patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics,
        ):
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(asyncio.coroutine(lambda: [])())
            mock_analytics._generate_performance_alerts.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_alerts)()
            )

            # Test severity filter
            response = self.client.get(f"{self.base_url}/alerts", params={"severity": "high", "limit": 5})

            assert response.status_code == 200
            data = response.json()

            # Should only return high severity alerts
            for alert in data:
                assert alert["severity"] == "high"

    def test_get_optimization_recommendations_success(self):
        """Test optimization recommendations retrieval."""
        mock_recommendations = {
            "status": "success",
            "generated_at": datetime.utcnow().isoformat(),
            "total_sources_analyzed": 5,
            "recommendations": [
                {
                    "type": "scale_up",
                    "priority": "high",
                    "title": "Scale Top Performing Sources",
                    "description": "Increase investment in high-ROI sources",
                    "expected_impact": "25-50% ROI increase",
                },
                {
                    "type": "optimize_or_pause",
                    "priority": "high",
                    "title": "Optimize Underperforming Sources",
                    "description": "Review and optimize low-ROI campaigns",
                    "expected_impact": "Reduce wasted spend",
                },
            ],
            "top_performers": [
                {"source": "zillow", "roi": 300, "total_leads": 50, "conversion_rate": 8.0},
                {"source": "agent_referral", "roi": 450, "total_leads": 25, "conversion_rate": 12.0},
            ],
        }

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_source_recommendations.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_recommendations)()
            )

            response = self.client.get(f"{self.base_url}/recommendations")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "success"
            assert len(data["recommendations"]) == 2
            assert len(data["top_performers"]) == 2

    def test_get_available_sources_success(self):
        """Test available sources endpoint."""
        response = self.client.get(f"{self.base_url}/sources")

        assert response.status_code == 200
        data = response.json()

        assert "sources" in data
        assert "categories" in data

        # Should include all major source types
        source_values = [source["value"] for source in data["sources"]]
        assert "zillow" in source_values
        assert "facebook_ads" in source_values
        assert "google_ads" in source_values
        assert "agent_referral" in source_values

        # Should have proper categorization
        assert "Digital Marketing" in data["categories"]
        assert "Real Estate Platforms" in data["categories"]
        assert "Referrals" in data["categories"]

    def test_track_attribution_event_success(self):
        """Test manual event tracking endpoint."""
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.track_source_performance.return_value = asyncio.create_task(asyncio.coroutine(lambda: None)())

            response = self.client.post(
                f"{self.base_url}/track-event",
                params={"source": "zillow", "event_type": "deal_closed"},
                json={"deal_value": 8000.0, "close_time_days": 45, "agent_id": "agent_123"},
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert "Event deal_closed tracked for zillow" in data["message"]

    def test_track_attribution_event_invalid_source(self):
        """Test event tracking with invalid source."""
        response = self.client.post(
            f"{self.base_url}/track-event", params={"source": "invalid_source", "event_type": "deal_closed"}
        )

        assert response.status_code == 400
        assert "Invalid source" in response.json()["detail"]

    def test_export_performance_csv_success(self):
        """Test CSV export functionality."""
        mock_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime.utcnow() - timedelta(days=30),
                period_end=datetime.utcnow(),
                total_leads=50,
                qualified_leads=20,
                hot_leads=10,
                conversion_rate=0.08,
                qualification_rate=0.40,
                total_revenue=100000.0,
                avg_deal_size=5000.0,
                cost_per_lead=25.0,
                cost_per_qualified_lead=62.50,
                roi=3.0,
                avg_lead_score=6.5,
                avg_budget=450000.0,
            )
        ]

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_performances)()
            )

            response = self.client.get(f"{self.base_url}/export/csv")

            assert response.status_code == 200
            data = response.json()

            assert "content" in data
            assert "filename" in data
            assert "content_type" in data

            # Verify CSV content structure
            csv_content = data["content"]
            lines = csv_content.strip().split("\n")
            assert len(lines) >= 2  # Header + at least one data row

            # Verify header
            header = lines[0]
            assert "Source" in header
            assert "Total Leads" in header
            assert "ROI" in header

    def test_export_performance_csv_with_filters(self):
        """Test CSV export with date and source filters."""
        mock_performances = [
            SourcePerformance(
                source=LeadSource.ZILLOW,
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                total_leads=25,
                roi=2.5,
            )
        ]

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: mock_performances)()
            )

            response = self.client.get(
                f"{self.base_url}/export/csv",
                params={"start_date": "2024-01-01", "end_date": "2024-01-31", "sources": "zillow,facebook_ads"},
            )

            assert response.status_code == 200
            data = response.json()

            assert "content" in data
            assert "zillow" in data["content"]

    def test_error_handling_500_errors(self):
        """Test handling of internal server errors."""
        # Test report generation failure
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics:
            mock_analytics.generate_attribution_report.side_effect = Exception("Database error")

            response = self.client.get(f"{self.base_url}/report")

            assert response.status_code == 500
            assert "Failed to generate report" in response.json()["detail"]

        # Test performance data failure
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_all_source_performance.side_effect = Exception("Cache error")

            response = self.client.get(f"{self.base_url}/performance")

            assert response.status_code == 500
            assert "Failed to retrieve performance data" in response.json()["detail"]

    def test_date_parsing_edge_cases(self):
        """Test date parsing with various formats."""
        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(asyncio.coroutine(lambda: [])())

            # Test valid ISO date format
            response = self.client.get(
                f"{self.base_url}/performance", params={"start_date": "2024-01-15", "end_date": "2024-01-22"}
            )

            assert response.status_code == 200

            # Test invalid date format should still work (will be ignored)
            response = self.client.get(f"{self.base_url}/performance", params={"start_date": "invalid-date"})

            assert response.status_code in [200, 500]  # Depends on implementation

    @pytest.mark.asyncio
    async def test_async_endpoint_behavior(self):
        """Test async behavior of endpoints."""
        # Test that endpoints properly handle async operations
        mock_performances = []

        with patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker:
            # Mock async method
            async def mock_get_performance(*args, **kwargs):
                await asyncio.sleep(0.01)  # Simulate async operation
                return mock_performances

            mock_tracker.get_all_source_performance = mock_get_performance

            response = self.client.get(f"{self.base_url}/performance")

            assert response.status_code == 200

    def test_pagination_and_limits(self):
        """Test pagination and limit parameters."""
        # Create many mock alerts to test limiting
        many_alerts = [
            PerformanceAlert(
                alert_type=AlertType.ROI_DROP,
                source=LeadSource.FACEBOOK_ADS,
                severity="high",
                title=f"Alert {i}",
                description=f"Description {i}",
                current_value=0.5,
                previous_value=2.0,
                threshold=-0.2,
                change_percentage=-0.75,
                recommendations=[],
                created_at=datetime.utcnow(),
            )
            for i in range(50)
        ]

        with (
            patch("ghl_real_estate_ai.api.routes.attribution_reports.lead_source_tracker") as mock_tracker,
            patch("ghl_real_estate_ai.api.routes.attribution_reports.attribution_analytics") as mock_analytics,
        ):
            mock_tracker.get_all_source_performance.return_value = asyncio.create_task(asyncio.coroutine(lambda: [])())
            mock_analytics._generate_performance_alerts.return_value = asyncio.create_task(
                asyncio.coroutine(lambda: many_alerts)()
            )

            # Test default limit
            response = self.client.get(f"{self.base_url}/alerts")
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 20  # Default limit

            # Test custom limit
            response = self.client.get(f"{self.base_url}/alerts", params={"limit": 10})
            assert response.status_code == 200
            data = response.json()
            assert len(data) <= 10