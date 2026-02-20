"""
Tests for Lead Source Tracker

Tests source tracking, conversion funnel monitoring, and metrics aggregation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.source_tracker import (
    ConversionStage,
    SourceTracker,
    get_source_tracker,
)


class MockDBService:
    """Mock database service for testing."""

    def __init__(self):
        self.execute_calls = []
        self.fetch_calls = []
        self.data = []

    async def execute(self, query: str, *args):
        """Mock execute method."""
        self.execute_calls.append((query, args))

    async def fetch(self, query: str, *args):
        """Mock fetch method."""
        self.fetch_calls.append((query, args))
        return self.data

    async def fetchrow(self, query: str, *args):
        """Mock fetchrow method."""
        self.fetch_calls.append((query, args))
        return self.data[0] if self.data else None


@pytest.fixture
def mock_db():
    """Create mock database service."""
    return MockDBService()


@pytest.fixture
def tracker(mock_db):
    """Create source tracker with mock DB."""
    return SourceTracker(db_service=mock_db)


@pytest.mark.asyncio
async def test_track_contact(tracker, mock_db):
    """Test tracking a new contact."""
    await tracker.track_contact(
        contact_id="contact_123",
        source="Facebook Ads",
        tags=["hot-lead"],
        custom_fields={"budget": "500k"},
    )

    assert len(mock_db.execute_calls) == 1
    query, args = mock_db.execute_calls[0]
    assert "lead_source_contacts" in query
    assert args[0] == "contact_123"
    assert args[1] == "Facebook"  # Normalized from "Facebook Ads"


@pytest.mark.asyncio
async def test_track_conversion(tracker, mock_db):
    """Test tracking a conversion event."""
    await tracker.track_conversion(
        contact_id="contact_123",
        stage=ConversionStage.QUALIFIED,
        metadata={"score": 85},
    )

    assert len(mock_db.execute_calls) == 2  # UPDATE + INSERT
    update_query = mock_db.execute_calls[0][0]
    insert_query = mock_db.execute_calls[1][0]

    assert "UPDATE lead_source_contacts" in update_query
    assert "INSERT INTO lead_source_conversions" in insert_query


@pytest.mark.asyncio
async def test_get_source_metrics(tracker, mock_db):
    """Test fetching source metrics."""
    # Mock data
    mock_db.data = [
        {
            "source_name": "Facebook Ads",
            "total_contacts": 100,
            "qualified_leads": 50,
            "appointments": 30,
            "showings": 20,
            "offers": 10,
            "closed_deals": 5,
            "total_revenue": 500000.0,
            "avg_deal_value": 100000.0,
        }
    ]

    metrics = await tracker.get_source_metrics(source_name="Facebook Ads", days=30)

    assert metrics["source_name"] == "Facebook Ads"
    assert metrics["total_contacts"] == 100
    assert metrics["closed_deals"] == 5
    assert metrics["conversion_rate"] == 5.0  # 5/100 * 100
    assert metrics["total_revenue"] == 500000.0


@pytest.mark.asyncio
async def test_get_top_sources(tracker, mock_db):
    """Test getting top sources."""
    mock_db.data = [
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
        },
    ]

    top_sources = await tracker.get_top_sources(by="conversion_rate", limit=10)

    assert len(top_sources) <= 10
    # Should be sorted by conversion rate
    assert top_sources[0]["conversion_rate"] >= top_sources[1]["conversion_rate"]


@pytest.mark.asyncio
async def test_normalize_source():
    """Test source name normalization."""
    tracker = SourceTracker()

    assert tracker._normalize_source("fb ads") == "Facebook"
    assert tracker._normalize_source("Facebook Ads") == "Facebook"
    assert tracker._normalize_source("google ads") == "Google"
    assert tracker._normalize_source("referral") == "Referral"
    assert tracker._normalize_source(None) == "Unknown"
    assert tracker._normalize_source("") == "Unknown"


@pytest.mark.asyncio
async def test_update_source_metrics_table(tracker, mock_db):
    """Test updating aggregated metrics table."""
    mock_db.data = [
        {
            "source_name": "Facebook Ads",
            "total_contacts": 100,
            "qualified_leads": 50,
            "appointments": 30,
            "showings": 20,
            "offers": 10,
            "closed_deals": 5,
            "total_revenue": 500000.0,
            "avg_deal_value": 100000.0,
        }
    ]

    await tracker.update_source_metrics_table()

    # Should have executed INSERT ON CONFLICT for metrics table
    assert len(mock_db.execute_calls) > 0
    last_query = mock_db.execute_calls[-1][0]
    assert "lead_source_metrics" in last_query


def test_get_source_tracker_singleton():
    """Test singleton pattern."""
    tracker1 = get_source_tracker()
    tracker2 = get_source_tracker()

    assert tracker1 is tracker2


@pytest.mark.asyncio
async def test_track_contact_no_db():
    """Test tracking without DB service."""
    tracker = SourceTracker(db_service=None)

    # Should not raise exception
    await tracker.track_contact(
        contact_id="contact_123",
        source="Facebook Ads",
    )


@pytest.mark.asyncio
async def test_get_source_metrics_no_db():
    """Test getting metrics without DB service."""
    tracker = SourceTracker(db_service=None)

    metrics = await tracker.get_source_metrics(source_name="Facebook Ads")

    # Should return mock metrics
    assert metrics["source_name"] == "Unknown"
    assert metrics["total_contacts"] == 0


@pytest.mark.asyncio
async def test_conversion_stages():
    """Test conversion stage constants."""
    assert ConversionStage.CONTACT == "contact"
    assert ConversionStage.QUALIFIED == "qualified"
    assert ConversionStage.APPOINTMENT == "appointment"
    assert ConversionStage.SHOWING == "showing"
    assert ConversionStage.OFFER == "offer"
    assert ConversionStage.CLOSE == "close"
