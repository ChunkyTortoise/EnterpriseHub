"""Unit tests for ProspectSourcer Phase 2 — EXPIRED_MLS + FSBO sources.

Tests MLS feed integration, ProspectProfile conversion, and error handling.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.sdr.mls_feed import MLSListing, SimulatedMLSFeed
from ghl_real_estate_ai.services.sdr.prospect_sourcer import (
    ProspectProfile,
    ProspectSource,
    ProspectSourcer,
)

pytestmark = pytest.mark.unit

LOCATION_ID = "test-loc-001"


def _mock_ghl_client() -> MagicMock:
    """Minimal mock GHL client — not used for MLS tests but required by constructor."""
    return MagicMock()


# ---- SimulatedMLSFeed standalone ----


@pytest.mark.asyncio
async def test_simulated_mls_feed_returns_expired_listings():
    feed = SimulatedMLSFeed()
    listings = await feed.fetch_expired_listings(LOCATION_ID, limit=5)

    assert len(listings) == 5
    for listing in listings:
        assert isinstance(listing, MLSListing)
        assert listing.listing_status == "expired"
        assert listing.mls_number.startswith("EXP-")
        assert listing.price > 0
        assert listing.dom >= 30


@pytest.mark.asyncio
async def test_simulated_mls_feed_returns_fsbo_listings():
    feed = SimulatedMLSFeed()
    listings = await feed.fetch_fsbo_listings(LOCATION_ID, limit=3)

    assert len(listings) == 3
    for listing in listings:
        assert listing.listing_status == "fsbo"
        assert listing.mls_number.startswith("FSBO-")
        assert listing.owner_name is not None


# ---- ProspectSourcer with MLS sources ----


@pytest.mark.asyncio
async def test_sourcer_fetches_expired_mls_prospects():
    feed = SimulatedMLSFeed()
    sourcer = ProspectSourcer(ghl_client=_mock_ghl_client(), mls_feed=feed)

    prospects = await sourcer.fetch_prospects(
        location_id=LOCATION_ID,
        sources=[ProspectSource.EXPIRED_MLS],
        max_per_source=10,
    )

    assert len(prospects) == 10
    for p in prospects:
        assert isinstance(p, ProspectProfile)
        assert p.source == ProspectSource.EXPIRED_MLS
        assert p.lead_type == "seller"
        assert p.mls_data is not None
        assert "mls_number" in p.mls_data
        assert p.contact_id.startswith("mls-")
        assert p.property_address is not None


@pytest.mark.asyncio
async def test_sourcer_fetches_fsbo_prospects():
    feed = SimulatedMLSFeed()
    sourcer = ProspectSourcer(ghl_client=_mock_ghl_client(), mls_feed=feed)

    prospects = await sourcer.fetch_prospects(
        location_id=LOCATION_ID,
        sources=[ProspectSource.FSBO],
        max_per_source=5,
    )

    assert len(prospects) == 5
    for p in prospects:
        assert p.source == ProspectSource.FSBO
        assert p.lead_type == "seller"
        assert p.mls_data["owner_name"] is not None


@pytest.mark.asyncio
async def test_sourcer_handles_mls_feed_error_gracefully():
    """If the MLS feed raises, sourcer logs and returns empty for that source."""
    feed = MagicMock(spec=SimulatedMLSFeed)
    feed.fetch_expired_listings = AsyncMock(side_effect=RuntimeError("MLS API down"))
    sourcer = ProspectSourcer(ghl_client=_mock_ghl_client(), mls_feed=feed)

    prospects = await sourcer.fetch_prospects(
        location_id=LOCATION_ID,
        sources=[ProspectSource.EXPIRED_MLS],
        max_per_source=10,
    )

    assert prospects == []
    feed.fetch_expired_listings.assert_awaited_once()


@pytest.mark.asyncio
async def test_sourcer_deduplicates_across_mls_sources():
    """Expired and FSBO listings with same contact_id should be deduplicated."""
    feed = MagicMock(spec=SimulatedMLSFeed)

    # Both sources return a listing that maps to the same contact_id
    expired_listing = MLSListing(
        mls_number="SHARED-001",
        address="123 Main",
        city="RC",
        state="CA",
        zip_code="91730",
        price=500000,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        dom=60,
        listing_status="expired",
    )
    fsbo_listing = MLSListing(
        mls_number="SHARED-001",
        address="123 Main",
        city="RC",
        state="CA",
        zip_code="91730",
        price=500000,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        dom=30,
        listing_status="fsbo",
    )
    feed.fetch_expired_listings = AsyncMock(return_value=[expired_listing])
    feed.fetch_fsbo_listings = AsyncMock(return_value=[fsbo_listing])

    sourcer = ProspectSourcer(ghl_client=_mock_ghl_client(), mls_feed=feed)
    prospects = await sourcer.fetch_prospects(
        location_id=LOCATION_ID,
        sources=[ProspectSource.EXPIRED_MLS, ProspectSource.FSBO],
        max_per_source=10,
    )

    # Same mls_number -> same contact_id -> deduped to 1
    assert len(prospects) == 1
    assert prospects[0].contact_id == "mls-SHARED-001"
