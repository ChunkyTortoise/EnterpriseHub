import pytest

pytestmark = pytest.mark.integration

"""
Unit Tests for ROI Logic
Verifies the math behind the Professional Services Catalog ROI models.
"""

import pytest

from utils.roi_logic import (
    calculate_automation_roi,
    calculate_data_roi,
    calculate_marketing_roi,
    calculate_strategic_roi,
)


def test_automation_roi():
    # Scenario: 200 leads/day, 2 hrs/lead, $50/hr, 85% automation
    leads_day = 200
    hours_per_lead = 2.0
    hourly_rate = 50
    automation_pct = 85

    results = calculate_automation_roi(leads_day, hours_per_lead, hourly_rate, automation_pct)

    assert results["total_weekly_hours"] == 2000  # (200 * 5) * 2
    assert results["hours_saved"] == 1700  # 2000 * 0.85
    assert results["weekly_savings"] == 85000  # 1700 * 50
    assert results["annual_savings"] == 85000 * 52


def test_data_roi():
    # Scenario: $5M ARR, 12% churn, 20% AI reduction
    arr_m = 5.0
    churn_rate = 12
    ai_reduction = 20

    results = calculate_data_roi(arr_m, churn_rate, ai_reduction)

    assert results["arr"] == 5_000_000
    assert results["churn_loss"] == 600_000  # 5M * 0.12
    assert results["recovered_revenue"] == 120_000  # 600K * 0.20


def test_marketing_roi():
    # Scenario: 200 posts, 100 traffic/post, 0.5% conv, $2000 LTV
    posts_count = 200
    traffic_per_post = 100
    conv_rate = 0.5
    ltv = 2000

    results = calculate_marketing_roi(posts_count, traffic_per_post, conv_rate, ltv)

    assert results["total_traffic"] == 20000  # 200 * 100
    assert results["conversions"] == 100  # 20000 * 0.005
    assert results["monthly_value"] == 200000  # 100 * 2000
    assert results["annualized_value"] == 2_400_000


def test_strategic_roi():
    # Scenario: $300k budget, 30% waste
    budget = 300_000
    waste_pct = 30

    results = calculate_strategic_roi(budget, waste_pct)

    assert results["prevented_waste"] == 90_000  # 300K * 0.30