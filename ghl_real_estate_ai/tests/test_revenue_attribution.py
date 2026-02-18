"""
Tests for Revenue Attribution System
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine



@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary data directory with mock analytics data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # We need enough data to trigger the attribution logic
    mock_analytics = {
        "conversations": [
            {"contact_id": "c1", "timestamp": datetime.now().isoformat(), "lead_score": 85, "appointment_set": True}
            for _ in range(10)
        ]
    }

    with open(data_dir / "mock_analytics.json", "w") as f:
        json.dump(mock_analytics, f)

    return data_dir


class TestRevenueAttributionEngine:
    def test_get_full_attribution_report(self, mock_data_dir):
        engine = RevenueAttributionEngine(data_dir=mock_data_dir)
        report = engine.get_full_attribution_report("test_loc")

        assert report["location_id"] == "test_loc"
        assert "summary" in report
        assert "channel_performance" in report
        assert "conversion_funnel" in report

        summary = report["summary"]
        # With 10 hot leads/appointments:
        # properties_shown = 10 * 0.65 = 6
        # offers_made = 6 * 0.55 = 3
        # deals_closed = 3 * 0.50 = 1
        # revenue = 1 * 12500 = 12500

        assert summary["total_deals"] == 1
        assert summary["total_revenue"] == 12500
        assert len(report["channel_performance"]) == 4