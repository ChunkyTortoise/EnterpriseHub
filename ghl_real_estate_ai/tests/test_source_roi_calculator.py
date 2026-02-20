"""
Tests for Source ROI Calculator

Tests ROI calculations, optimization recommendations, and source comparisons.
"""

from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.source_roi_calculator import (
    SourceROICalculator,
    get_roi_calculator,
)
from ghl_real_estate_ai.services.jorge.source_tracker import SourceTracker


class MockSourceTracker:
    """Mock source tracker for testing."""

    async def get_source_metrics(self, source_name=None, days=30):
        """Mock get_source_metrics."""
        if source_name:
            return {
                "source_name": source_name,
                "total_contacts": 100,
                "qualified_leads": 50,
                "appointments": 30,
                "showings": 20,
                "offers": 10,
                "closed_deals": 5,
                "total_revenue": 500000.0,
                "avg_deal_value": 100000.0,
                "conversion_rate": 5.0,
            }
        return {
            "sources": [
                {
                    "source_name": "Facebook Ads",
                    "total_contacts": 100,
                    "qualified_leads": 50,
                    "appointments": 30,
                    "showings": 20,
                    "offers": 10,
                    "closed_deals": 10,
                    "total_revenue": 1000000.0,
                    "avg_deal_value": 100000.0,
                    "conversion_rate": 10.0,
                },
                {
                    "source_name": "Google Ads",
                    "total_contacts": 80,
                    "qualified_leads": 40,
                    "appointments": 25,
                    "showings": 15,
                    "offers": 8,
                    "closed_deals": 5,
                    "total_revenue": 500000.0,
                    "avg_deal_value": 100000.0,
                    "conversion_rate": 6.25,
                },
            ]
        }


class MockDBService:
    """Mock database service."""

    async def fetchrow(self, query: str, *args):
        """Mock fetchrow."""
        return {"total_cost": 10000.0}


@pytest.fixture
def mock_tracker():
    """Create mock source tracker."""
    return MockSourceTracker()


@pytest.fixture
def mock_db():
    """Create mock DB service."""
    return MockDBService()


@pytest.fixture
def calculator(mock_tracker, mock_db):
    """Create ROI calculator with mocks."""
    return SourceROICalculator(source_tracker=mock_tracker, db_service=mock_db)


@pytest.mark.asyncio
async def test_calculate_source_roi(calculator):
    """Test calculating ROI for a source."""
    roi_data = await calculator.calculate_source_roi(
        source_name="Facebook Ads",
        cost=20000.0,
        days=30,
    )

    assert roi_data["source_name"] == "Facebook Ads"
    assert roi_data["cost"] == 20000.0
    assert roi_data["revenue"] == 500000.0
    assert roi_data["profit"] == 480000.0
    assert roi_data["roi"] > 0  # Positive ROI
    assert roi_data["roi_ratio"] == 25.0  # 500k / 20k
    assert roi_data["conversion_rate"] == 5.0


@pytest.mark.asyncio
async def test_calculate_roi_with_zero_cost(calculator):
    """Test ROI calculation with zero cost."""
    roi_data = await calculator.calculate_source_roi(
        source_name="Referral",
        cost=0.0,
        days=30,
    )

    assert roi_data["cost"] == 0.0
    assert roi_data["roi"] == 0.0
    assert roi_data["roi_ratio"] == 0.0


@pytest.mark.asyncio
async def test_calculate_roi_negative(calculator):
    """Test ROI calculation with loss."""
    roi_data = await calculator.calculate_source_roi(
        source_name="Facebook Ads",
        cost=600000.0,  # Higher than revenue
        days=30,
    )

    assert roi_data["roi"] < 0  # Negative ROI
    assert roi_data["profit"] < 0  # Loss


@pytest.mark.asyncio
async def test_get_all_source_roi(calculator):
    """Test getting ROI for all sources."""
    all_roi = await calculator.get_all_source_roi(days=30)

    assert len(all_roi) == 2
    assert all_roi[0]["source_name"] == "Facebook Ads"
    assert all_roi[1]["source_name"] == "Google Ads"


@pytest.mark.asyncio
async def test_get_optimization_recommendations(calculator):
    """Test generating optimization recommendations."""
    recommendations = await calculator.get_optimization_recommendations(
        days=30,
        budget_shift_percent=20.0,
    )

    assert "top_performers" in recommendations
    assert "underperformers" in recommendations
    assert "recommendations" in recommendations
    assert "projected_impact" in recommendations

    assert len(recommendations["top_performers"]) > 0
    assert len(recommendations["recommendations"]) > 0


@pytest.mark.asyncio
async def test_compare_sources(calculator):
    """Test comparing two sources."""
    comparison = await calculator.compare_sources(
        source_a="Facebook Ads",
        source_b="Google Ads",
        days=30,
    )

    assert "source_a" in comparison
    assert "source_b" in comparison
    assert "winners" in comparison
    assert "recommendation" in comparison

    assert comparison["source_a"]["source_name"] == "Facebook Ads"
    assert comparison["source_b"]["source_name"] == "Google Ads"


@pytest.mark.asyncio
async def test_empty_roi_data():
    """Test empty ROI data structure."""
    calculator = SourceROICalculator()
    empty = calculator._empty_roi_data("Test Source")

    assert empty["source_name"] == "Test Source"
    assert empty["cost"] == 0.0
    assert empty["revenue"] == 0.0
    assert empty["roi"] == 0.0
    assert empty["total_contacts"] == 0


@pytest.mark.asyncio
async def test_cost_per_lead_calculations(calculator):
    """Test cost per lead metrics."""
    roi_data = await calculator.calculate_source_roi(
        source_name="Facebook Ads",
        cost=10000.0,
        days=30,
    )

    assert roi_data["cost_per_lead"] == 100.0  # 10000 / 100 contacts
    assert roi_data["cost_per_qualified_lead"] == 200.0  # 10000 / 50 qualified
    assert roi_data["cost_per_close"] == 2000.0  # 10000 / 5 closed


@pytest.mark.asyncio
async def test_recommendations_with_negative_roi(mock_tracker, mock_db):
    """Test recommendations when sources have negative ROI."""
    # Mock tracker with negative ROI source
    async def mock_get_metrics(source_name=None, days=30):
        if source_name:
            return {
                "source_name": source_name,
                "total_contacts": 100,
                "qualified_leads": 50,
                "appointments": 30,
                "showings": 20,
                "offers": 10,
                "closed_deals": 5,
                "total_revenue": 100000.0,
                "avg_deal_value": 20000.0,
                "conversion_rate": 5.0,
            }
        return {
            "sources": [
                {
                    "source_name": "Good Source",
                    "total_contacts": 100,
                    "qualified_leads": 50,
                    "appointments": 30,
                    "showings": 20,
                    "offers": 10,
                    "closed_deals": 10,
                    "total_revenue": 1000000.0,
                    "avg_deal_value": 100000.0,
                    "conversion_rate": 10.0,
                },
                {
                    "source_name": "Bad Source",
                    "total_contacts": 50,
                    "qualified_leads": 10,
                    "appointments": 5,
                    "showings": 2,
                    "offers": 1,
                    "closed_deals": 0,
                    "total_revenue": 0.0,
                    "avg_deal_value": 0.0,
                    "conversion_rate": 0.0,
                },
            ]
        }

    mock_tracker.get_source_metrics = mock_get_metrics
    calculator = SourceROICalculator(source_tracker=mock_tracker, db_service=mock_db)

    # Create ROI data with costs that result in negative ROI
    recommendations = await calculator.get_optimization_recommendations(days=30)

    # Should recommend pausing negative ROI sources
    rec_text = " ".join(recommendations["recommendations"])
    assert len(recommendations["recommendations"]) > 0


def test_get_roi_calculator_singleton():
    """Test singleton pattern."""
    calc1 = get_roi_calculator()
    calc2 = get_roi_calculator()

    assert calc1 is calc2


@pytest.mark.asyncio
async def test_generate_comparison_recommendation():
    """Test comparison recommendation generation."""
    calculator = SourceROICalculator()

    roi_a = {
        "source_name": "Facebook",
        "roi": 300.0,
        "conversion_rate": 15.0,
        "cost_per_qualified_lead": 50.0,
    }

    roi_b = {
        "source_name": "Google",
        "roi": 150.0,
        "conversion_rate": 10.0,
        "cost_per_qualified_lead": 80.0,
    }

    rec = calculator._generate_comparison_recommendation(roi_a, roi_b)

    assert isinstance(rec, str)
    assert len(rec) > 0
    assert "Facebook" in rec or "Google" in rec
