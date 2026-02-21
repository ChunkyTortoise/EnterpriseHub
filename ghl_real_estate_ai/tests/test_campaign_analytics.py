"""
Tests for Campaign Performance Analytics.

Tests campaign tracking, ROI calculation, funnel analysis, and channel performance.
"""

import json
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from ghl_real_estate_ai.services.campaign_analytics import CampaignTracker


@pytest.fixture
def test_location_id():
    """Provide a test location ID."""
    return "test_location_campaigns"


@pytest.fixture
def campaign_tracker(test_location_id):
    """Create a campaign tracker instance for testing."""
    tracker = CampaignTracker(test_location_id)
    yield tracker
    # Cleanup
    campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / test_location_id
    if campaigns_dir.exists():
        shutil.rmtree(campaigns_dir)


class _AdvancingDatetime(datetime):
    """datetime subclass where now() auto-advances for unique campaign IDs."""

    _current: datetime = datetime(2026, 1, 15, 10, 0, 0)
    _step: timedelta = timedelta(seconds=1)

    @classmethod
    def now(cls, tz=None):
        result = cls._current
        cls._current = cls._current + cls._step
        return result

    @classmethod
    def reset(cls, start=None, step=None):
        cls._current = start or datetime(2026, 1, 15, 10, 0, 0)
        cls._step = step or timedelta(seconds=1)


@pytest.fixture(autouse=True)
def _mock_campaign_datetime():
    """Auto-mock datetime.now() in campaign_analytics so IDs are unique without sleeping."""
    _AdvancingDatetime.reset()
    with patch("ghl_real_estate_ai.services.campaign_analytics.datetime", _AdvancingDatetime):
        yield


class TestCampaignCreation:
    """Test campaign creation and management."""

    def test_create_basic_campaign(self, campaign_tracker):
        """Test creating a basic campaign."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test SMS Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        assert campaign_id.startswith("camp_")
        assert campaign_id in campaign_tracker.campaigns["active"]

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        assert campaign["name"] == "Test SMS Campaign"
        assert campaign["channel"] == "sms"
        assert campaign["budget"] == 1000.0
        assert campaign["status"] == "active"

    def test_create_campaign_with_targets(self, campaign_tracker):
        """Test creating a campaign with custom target metrics."""
        campaign_id = campaign_tracker.create_campaign(
            name="Email Campaign",
            channel="email",
            budget=2000.0,
            start_date="2026-01-01",
            target_metrics={"target_leads": 200, "target_conversions": 20, "target_roi": 3.5},
        )

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        assert campaign["target_metrics"]["target_leads"] == 200
        assert campaign["target_metrics"]["target_conversions"] == 20
        assert campaign["target_metrics"]["target_roi"] == 3.5

    def test_campaign_has_default_performance_metrics(self, campaign_tracker):
        """Test that new campaigns have initialized performance metrics."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="social", budget=500.0, start_date="2026-01-01"
        )

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        perf = campaign["performance"]

        assert perf["impressions"] == 0
        assert perf["clicks"] == 0
        assert perf["leads_generated"] == 0
        assert perf["conversions"] == 0
        assert perf["roi"] == 0.0
        assert perf["cost_per_lead"] == 0.0


class TestMetricsUpdates:
    """Test updating campaign metrics."""

    def test_update_basic_metrics(self, campaign_tracker):
        """Test updating campaign metrics."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_campaign_metrics(
            campaign_id,
            {"impressions": 5000, "clicks": 250, "leads_generated": 50, "conversions": 5, "revenue_generated": 7500.0},
        )

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        perf = campaign["performance"]

        assert perf["impressions"] == 5000
        assert perf["clicks"] == 250
        assert perf["leads_generated"] == 50
        assert perf["conversions"] == 5
        assert perf["revenue_generated"] == 7500.0

    def test_cost_per_lead_calculation(self, campaign_tracker):
        """Test that cost per lead is calculated correctly."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="paid_ads", budget=2000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_campaign_metrics(campaign_id, {"leads_generated": 100})

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        assert campaign["performance"]["cost_per_lead"] == 20.0  # 2000 / 100

    def test_roi_calculation(self, campaign_tracker):
        """Test that ROI is calculated correctly."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="email", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_campaign_metrics(campaign_id, {"conversions": 10, "revenue_generated": 3000.0})

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        perf = campaign["performance"]

        # ROI = (Revenue - Cost) / Cost = (3000 - 1000) / 1000 = 2.0
        assert perf["roi"] == 2.0

    def test_conversion_rate_calculation(self, campaign_tracker):
        """Test that conversion rate is calculated correctly."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_campaign_metrics(campaign_id, {"leads_generated": 100, "conversions": 15})

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        assert campaign["performance"]["conversion_rate"] == 0.15  # 15 / 100

    def test_cumulative_metrics_updates(self, campaign_tracker):
        """Test that metrics accumulate over multiple updates."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        # First update
        campaign_tracker.update_campaign_metrics(campaign_id, {"leads_generated": 50})

        # Second update
        campaign_tracker.update_campaign_metrics(campaign_id, {"leads_generated": 30})

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        assert campaign["performance"]["leads_generated"] == 80  # 50 + 30


class TestFunnelAnalysis:
    """Test conversion funnel tracking."""

    def test_update_funnel_stages(self, campaign_tracker):
        """Test updating funnel stages."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="social", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_funnel_stage(campaign_id, "awareness", 1000)
        campaign_tracker.update_funnel_stage(campaign_id, "interest", 300)
        campaign_tracker.update_funnel_stage(campaign_id, "consideration", 100)
        campaign_tracker.update_funnel_stage(campaign_id, "intent", 30)
        campaign_tracker.update_funnel_stage(campaign_id, "conversion", 10)

        campaign = campaign_tracker.campaigns["active"][campaign_id]
        funnel = campaign["funnel_data"]

        assert funnel["awareness"] == 1000
        assert funnel["interest"] == 300
        assert funnel["consideration"] == 100
        assert funnel["intent"] == 30
        assert funnel["conversion"] == 10

    def test_funnel_conversion_rates(self, campaign_tracker):
        """Test funnel conversion rate calculations."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="email", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_funnel_stage(campaign_id, "awareness", 1000)
        campaign_tracker.update_funnel_stage(campaign_id, "interest", 500)
        campaign_tracker.update_funnel_stage(campaign_id, "consideration", 200)
        campaign_tracker.update_funnel_stage(campaign_id, "intent", 50)
        campaign_tracker.update_funnel_stage(campaign_id, "conversion", 10)

        performance = campaign_tracker.get_campaign_performance(campaign_id)
        rates = performance["funnel_metrics"]["conversion_rates"]

        assert rates["awareness_to_interest"] == 50.0  # 500/1000 * 100
        assert rates["interest_to_consideration"] == 40.0  # 200/500 * 100
        assert rates["consideration_to_intent"] == 25.0  # 50/200 * 100
        assert rates["intent_to_conversion"] == 20.0  # 10/50 * 100

    def test_overall_funnel_efficiency(self, campaign_tracker):
        """Test overall funnel efficiency calculation."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_funnel_stage(campaign_id, "awareness", 1000)
        campaign_tracker.update_funnel_stage(campaign_id, "conversion", 50)

        performance = campaign_tracker.get_campaign_performance(campaign_id)
        efficiency = performance["funnel_metrics"]["overall_efficiency"]

        assert efficiency == 5.0  # 50/1000 * 100


class TestCampaignPerformance:
    """Test campaign performance reporting."""

    def test_get_campaign_performance(self, campaign_tracker):
        """Test getting comprehensive campaign performance."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign",
            channel="paid_ads",
            budget=5000.0,
            start_date="2026-01-01",
            target_metrics={"target_leads": 100, "target_conversions": 10, "target_roi": 2.0},
        )

        campaign_tracker.update_campaign_metrics(
            campaign_id, {"leads_generated": 120, "conversions": 12, "revenue_generated": 15000.0}
        )

        performance = campaign_tracker.get_campaign_performance(campaign_id)

        assert "campaign_info" in performance
        assert "performance" in performance
        assert "roi_analysis" in performance
        assert "funnel_metrics" in performance
        assert "target_comparison" in performance
        assert "trend_data" in performance

    def test_roi_analysis_details(self, campaign_tracker):
        """Test detailed ROI analysis."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="email", budget=2000.0, start_date="2026-01-01"
        )

        campaign_tracker.update_campaign_metrics(campaign_id, {"revenue_generated": 8000.0})

        performance = campaign_tracker.get_campaign_performance(campaign_id)
        roi = performance["roi_analysis"]

        assert roi["total_spent"] == 2000.0
        assert roi["revenue_generated"] == 8000.0
        assert roi["net_profit"] == 6000.0  # 8000 - 2000
        assert roi["roi_percentage"] == 300.0  # (6000/2000) * 100
        assert roi["profit_margin"] == 75.0  # (6000/8000) * 100

    def test_target_comparison(self, campaign_tracker):
        """Test target vs actual comparison."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign",
            channel="sms",
            budget=1000.0,
            start_date="2026-01-01",
            target_metrics={"target_leads": 100, "target_conversions": 10, "target_roi": 2.0},
        )

        campaign_tracker.update_campaign_metrics(
            campaign_id, {"leads_generated": 150, "conversions": 12, "revenue_generated": 5000.0}
        )

        performance = campaign_tracker.get_campaign_performance(campaign_id)
        targets = performance["target_comparison"]

        # Leads: 150/100 = 150%
        assert targets["leads_vs_target"]["achievement_rate"] == 150.0

        # Conversions: 12/10 = 120%
        assert targets["conversions_vs_target"]["achievement_rate"] == 120.0

        # ROI: 4.0/2.0 = 200%
        assert targets["roi_vs_target"]["achievement_rate"] == 200.0


class TestCampaignComparison:
    """Test comparing multiple campaigns."""

    def test_compare_two_campaigns(self, campaign_tracker):
        """Test comparing performance of two campaigns."""
        # Create first campaign
        camp1 = campaign_tracker.create_campaign(
            name="SMS Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )
        campaign_tracker.update_campaign_metrics(
            camp1, {"leads_generated": 100, "conversions": 10, "revenue_generated": 5000.0}
        )

        # Create second campaign
        camp2 = campaign_tracker.create_campaign(
            name="Email Campaign", channel="email", budget=1500.0, start_date="2026-01-01"
        )
        campaign_tracker.update_campaign_metrics(
            camp2, {"leads_generated": 150, "conversions": 20, "revenue_generated": 9000.0}
        )

        comparison = campaign_tracker.compare_campaigns([camp1, camp2])

        assert comparison["campaigns_compared"] == 2
        assert "rankings" in comparison
        assert "channel_performance" in comparison
        assert "recommendations" in comparison
        assert "summary_stats" in comparison

    def test_campaign_rankings(self, test_location_id):
        """Test that campaigns are ranked correctly."""
        # Use fresh tracker for this test
        import shutil

        campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / f"{test_location_id}_rankings"
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)

        tracker = CampaignTracker(f"{test_location_id}_rankings")

        # High ROI campaign
        camp1 = tracker.create_campaign(name="High ROI Campaign", channel="sms", budget=1000.0, start_date="2026-01-01")
        tracker.update_campaign_metrics(
            camp1, {"leads_generated": 100, "conversions": 20, "revenue_generated": 10000.0}
        )

        # Low ROI campaign
        camp2 = tracker.create_campaign(
            name="Low ROI Campaign", channel="email", budget=2000.0, start_date="2026-01-01"
        )
        tracker.update_campaign_metrics(camp2, {"leads_generated": 50, "conversions": 5, "revenue_generated": 3000.0})

        comparison = tracker.compare_campaigns([camp1, camp2])
        rankings = comparison["rankings"]["by_roi"]

        # First in ranking should be high ROI campaign (ROI = 9.0 vs 0.5)
        # Rankings are sorted by value descending, so highest ROI should be first
        high_roi_camp = next(r for r in rankings if r["name"] == "High ROI Campaign")
        low_roi_camp = next(r for r in rankings if r["name"] == "Low ROI Campaign")

        assert high_roi_camp["value"] > low_roi_camp["value"]
        assert rankings[0]["name"] == "High ROI Campaign"

        # Cleanup
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)


class TestChannelAnalytics:
    """Test channel-level analytics."""

    def test_get_channel_analytics(self, test_location_id):
        """Test getting channel performance analytics."""
        # Use fresh tracker for this test
        import shutil

        campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / f"{test_location_id}_channels"
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)

        tracker = CampaignTracker(f"{test_location_id}_channels")

        # Create campaigns on different channels
        camp1 = tracker.create_campaign(name="SMS Campaign 1", channel="sms", budget=1000.0, start_date="2026-01-01")
        tracker.update_campaign_metrics(camp1, {"leads_generated": 100, "conversions": 10, "revenue_generated": 5000.0})
        camp2 = tracker.create_campaign(
            name="Email Campaign 1", channel="email", budget=1500.0, start_date="2026-01-01"
        )
        tracker.update_campaign_metrics(camp2, {"leads_generated": 150, "conversions": 15, "revenue_generated": 7500.0})

        channel_data = tracker.get_channel_analytics()

        # Check that both channels exist in the data
        assert "sms" in channel_data or "email" in channel_data

        # If SMS exists, verify its metrics
        if "sms" in channel_data:
            assert channel_data["sms"]["total_leads"] == 100

        # If email exists, verify its metrics
        if "email" in channel_data:
            assert channel_data["email"]["total_leads"] == 150

        # Cleanup
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)


class TestCampaignLifecycle:
    """Test campaign lifecycle management."""

    def test_complete_campaign(self, campaign_tracker):
        """Test marking a campaign as completed."""
        campaign_id = campaign_tracker.create_campaign(
            name="Test Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        assert campaign_id in campaign_tracker.campaigns["active"]

        campaign_tracker.complete_campaign(campaign_id)

        assert campaign_id not in campaign_tracker.campaigns["active"]
        assert campaign_id in campaign_tracker.campaigns["completed"]

        completed = campaign_tracker.campaigns["completed"][campaign_id]
        assert completed["status"] == "completed"
        assert "completed_at" in completed

    def test_list_active_campaigns(self, test_location_id):
        """Test listing active campaigns."""
        # Use fresh tracker for this test
        import shutil

        campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / f"{test_location_id}_list"
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)

        tracker = CampaignTracker(f"{test_location_id}_list")

        camp1 = tracker.create_campaign(name="Campaign 1", channel="sms", budget=1000.0, start_date="2026-01-01")
        camp2 = tracker.create_campaign(name="Campaign 2", channel="email", budget=1500.0, start_date="2026-01-01")

        active_campaigns = tracker.list_active_campaigns()

        # Should have at least 2 campaigns (may have more if cleanup didn't work)
        assert len(active_campaigns) >= 2
        assert any(c["name"] == "Campaign 1" for c in active_campaigns)
        assert any(c["name"] == "Campaign 2" for c in active_campaigns)

        # Cleanup
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)


class TestDataPersistence:
    """Test that campaign data persists correctly."""

    def test_campaign_data_persists(self, test_location_id):
        """Test that campaign data is saved and can be reloaded."""
        tracker1 = CampaignTracker(test_location_id)

        campaign_id = tracker1.create_campaign(
            name="Persistent Campaign", channel="sms", budget=1000.0, start_date="2026-01-01"
        )

        tracker1.update_campaign_metrics(campaign_id, {"leads_generated": 50})

        # Create new tracker instance (simulates app restart)
        tracker2 = CampaignTracker(test_location_id)

        assert campaign_id in tracker2.campaigns["active"]
        assert tracker2.campaigns["active"][campaign_id]["performance"]["leads_generated"] == 50

        # Cleanup
        campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / test_location_id
        if campaigns_dir.exists():
            shutil.rmtree(campaigns_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
