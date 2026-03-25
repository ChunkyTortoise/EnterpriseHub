"""
SimulatedMLSFeed — generates realistic MLS listing data for portfolio demos.

Provides expired and FSBO listings scoped to the Rancho Cucamonga market area.
In production, this would be replaced by a real MLS/IDX API integration.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class MLSListing:
    """A single MLS listing record."""

    mls_number: str
    address: str
    city: str
    state: str
    zip_code: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    dom: int  # days on market
    listing_status: str  # "expired" | "fsbo" | "active"
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None
    owner_email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_list_date: Optional[datetime] = None
    property_type: str = "single_family"
    notes: Optional[str] = None
    lot_sqft: Optional[int] = None
    year_built: Optional[int] = None
    expired_at: Optional[datetime] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Simulated data pools (Rancho Cucamonga area)
# ---------------------------------------------------------------------------

_STREETS = [
    "Baseline Rd",
    "Foothill Blvd",
    "Haven Ave",
    "Archibald Ave",
    "Carnelian St",
    "Hermosa Ave",
    "Sapphire St",
    "Amethyst Ave",
    "Rochester Ave",
    "Milliken Ave",
    "Church St",
    "Vineyard Ave",
    "Banyan St",
    "Terra Vista Pkwy",
    "Wilson Ave",
    "Lemon Ave",
]

_CITIES = ["Rancho Cucamonga", "Upland", "Fontana", "Ontario", "Claremont"]

_FIRST_NAMES = [
    "Maria",
    "James",
    "Linda",
    "Robert",
    "Patricia",
    "Michael",
    "Jennifer",
    "David",
    "Elizabeth",
    "Carlos",
    "Rosa",
    "William",
]

_LAST_NAMES = [
    "Garcia",
    "Smith",
    "Johnson",
    "Rodriguez",
    "Martinez",
    "Williams",
    "Brown",
    "Davis",
    "Lopez",
    "Wilson",
    "Anderson",
    "Thomas",
]

_PROPERTY_TYPES = ["single_family", "condo", "townhouse"]


def _seeded_random(seed: str) -> random.Random:
    """Deterministic random from a string seed for reproducible demo data."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    return random.Random(h)


# ---------------------------------------------------------------------------
# SimulatedMLSFeed
# ---------------------------------------------------------------------------


class SimulatedMLSFeed:
    """
    Generates realistic MLS listing data for demos.

    Each call produces deterministic-ish data seeded by location_id so that
    successive calls for the same location return consistent listings.
    """

    async def fetch_expired_listings(
        self,
        location_id: str,
        limit: int = 20,
    ) -> List[MLSListing]:
        """
        Return simulated expired MLS listings for the given location.

        Args:
            location_id: GHL location ID (used as random seed)
            limit: max listings to return

        Returns:
            List of MLSListing with status="expired"
        """
        rng = _seeded_random(f"expired-{location_id}")
        listings = []
        for i in range(min(limit, 50)):
            listings.append(_generate_listing(rng, i, "expired", location_id))

        logger.info(f"[MLS] Fetched {len(listings)} expired listings for location={location_id}")
        return listings

    async def fetch_fsbo_listings(
        self,
        location_id: str,
        limit: int = 20,
    ) -> List[MLSListing]:
        """
        Return simulated FSBO (For Sale By Owner) listings.

        Args:
            location_id: GHL location ID (used as random seed)
            limit: max listings to return

        Returns:
            List of MLSListing with status="fsbo"
        """
        rng = _seeded_random(f"fsbo-{location_id}")
        listings = []
        for i in range(min(limit, 30)):
            listings.append(_generate_listing(rng, i, "fsbo", location_id))

        logger.info(f"[MLS] Fetched {len(listings)} FSBO listings for location={location_id}")
        return listings


# ---------------------------------------------------------------------------
# Generator helper
# ---------------------------------------------------------------------------


def _generate_listing(rng: random.Random, index: int, status: str, location_id: str) -> MLSListing:
    """Build a single realistic MLSListing."""
    street_num = rng.randint(1000, 19999)
    street = rng.choice(_STREETS)
    city = rng.choice(_CITIES)
    zip_code = str(rng.randint(91701, 91739))

    bedrooms = rng.choice([2, 3, 3, 4, 4, 5])
    bathrooms = rng.choice([1.0, 1.5, 2.0, 2.0, 2.5, 3.0])
    sqft = rng.randint(900, 3500)
    price = round(rng.uniform(450_000, 850_000), -3)
    dom = rng.randint(30, 180) if status == "expired" else rng.randint(7, 90)
    year_built = rng.randint(1960, 2020)
    prop_type = rng.choice(_PROPERTY_TYPES)

    # Rancho Cucamonga approximate lat/long range
    latitude = round(rng.uniform(34.08, 34.16), 6)
    longitude = round(rng.uniform(-117.63, -117.53), 6)

    now = datetime.now(timezone.utc)
    last_list_date = now - timedelta(days=dom + rng.randint(0, 30))
    expired_at = now - timedelta(days=rng.randint(1, 14)) if status == "expired" else None

    first = rng.choice(_FIRST_NAMES)
    last = rng.choice(_LAST_NAMES)
    phone_area = rng.choice(["909", "626", "951"])
    phone = f"({phone_area}) {rng.randint(200, 999)}-{rng.randint(1000, 9999)}"

    mls_prefix = "EXP" if status == "expired" else "FSBO"
    mls_number = f"{mls_prefix}-{location_id[:4].upper()}-{index:04d}"

    notes = f"Expired after {dom} DOM" if status == "expired" else "FSBO — no agent representation"

    return MLSListing(
        mls_number=mls_number,
        address=f"{street_num} {street}",
        city=city,
        state="CA",
        zip_code=zip_code,
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        sqft=sqft,
        dom=dom,
        listing_status=status,
        owner_name=f"{first} {last}",
        owner_phone=phone,
        owner_email=f"{first.lower()}.{last.lower()}@example.com",
        latitude=latitude,
        longitude=longitude,
        last_list_date=last_list_date,
        property_type=prop_type,
        notes=notes,
        lot_sqft=rng.randint(3000, 12000),
        year_built=year_built,
        expired_at=expired_at,
        raw_data={"simulated": True, "seed": f"{status}-{location_id}-{index}"},
    )
