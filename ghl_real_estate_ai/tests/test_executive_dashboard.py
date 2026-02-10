"""
Tests for Executive Dashboard Service
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

@pytest.mark.unit

try:
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService, calculate_roi
except ImportError:
    pytest.skip("executive_dashboard imports unavailable", allow_module_level=True)


@pytest.fixture
def mock_data_dir(tmp_path):
    """Create a temporary data directory with mock analytics data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    mock_analytics = {
        "conversations": [
            {
                "contact_id": "c1",
                "timestamp": datetime.now().isoformat(),
                "lead_score": 85,
                "response_time_minutes": 1.5,
                "appointment_set": True,
            },
            {
                "contact_id": "c2",
                "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
                "lead_score": 45,
                "response_time_minutes": 2.5,
                "appointment_set": False,
            },
            {
                "contact_id": "c3",
                "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                "lead_score": 20,
                "response_time_minutes": 1.0,
                "appointment_set": False,
            },
        ]
    }

    with open(data_dir / "mock_analytics.json", "w") as f:
        json.dump(mock_analytics, f)

    return data_dir


class TestExecutiveDashboardService:
    def test_get_executive_summary(self, mock_data_dir):
        service = ExecutiveDashboardService(data_dir=mock_data_dir)
        summary = service.get_executive_summary("test_loc", days=7)

        assert "metrics" in summary
        assert "insights" in summary
        assert "action_items" in summary
        assert "trends" in summary

        metrics = summary["metrics"]
        assert metrics["conversations"]["total"] == 3
        assert metrics["lead_quality"]["hot_leads"] == 1
        assert metrics["response_time"]["average_minutes"] == 1.7
        assert metrics["conversion"]["appointments_set"] == 1

    def test_calculate_roi(self):
        roi_data = calculate_roi(
            system_cost_monthly=200, conversations_per_month=100, conversion_rate=0.1, avg_commission=10000
        )

        # 100 convos * 0.1 rate = 10 appointments
        # 10 appointments * 0.5 closing rate = 5 deals
        # 5 deals * 10000 commission = 50000 revenue
        # (50000 - 200) / 200 * 100 = 24900% ROI

        assert roi_data["results"]["deals_closed"] == 5
        assert roi_data["results"]["revenue_generated"] == 50000
        assert roi_data["roi"]["percentage"] == 24900.0
        assert roi_data["roi"]["net_profit_monthly"] == 49800