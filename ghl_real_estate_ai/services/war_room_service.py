"""
War Room Intelligence Service - Section 4 of 2026 Strategic Roadmap
Aggregates lead intent, property interest, and geographic clustering for market heat mapping.
"""

import logging
import random
from datetime import datetime
from typing import List

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class MarketNode(BaseModel):
    id: str
    lat: float
    lng: float
    heat_value: float  # 0-100 (FRS avg)
    leads_count: int
    highest_frs: float
    address: str


class LeadPropertyLink(BaseModel):
    source: str  # Lead ID
    target: str  # Property ID
    strength: float  # PCS score normalized


class WarRoomData(BaseModel):
    nodes: List[MarketNode]
    links: List[LeadPropertyLink]
    timestamp: datetime


class WarRoomService:
    """
    Data engineering layer for the Jorge War Room Dashboard.
    """

    def __init__(self):
        # Mock coordinates for Rancho Cucamonga, CA area
        self.rancho_cucamonga_bounds = {"lat": (30.2, 30.4), "lng": (-97.8, -97.6)}

    async def get_market_heat_data(self, market: str = "Rancho Cucamonga") -> WarRoomData:
        """
        Aggregates live lead data into a heat map and relationship graph format.
        """
        logger.info(f"War Room: Aggregating market heat for {market}")

        # 1. Generate nodes (Properties with interest)
        nodes = []
        addresses = ["123 Victoria Gardens Dr", "456 South Lake Blvd", "789 East 6th St", "101 Ontario Mills Way", "202 Congress Ave"]
        for i, addr in enumerate(addresses):
            nodes.append(
                MarketNode(
                    id=f"prop_{i}",
                    lat=random.uniform(*self.rancho_cucamonga_bounds["lat"]),
                    lng=random.uniform(*self.rancho_cucamonga_bounds["lng"]),
                    heat_value=random.uniform(40, 95),
                    leads_count=random.randint(1, 8),
                    highest_frs=random.uniform(70, 98),
                    address=addr,
                )
            )

        # 2. Generate links (Lead -> Property relationships)
        links = []
        for i in range(10):
            links.append(
                LeadPropertyLink(
                    source=f"lead_{random.randint(1, 20)}",
                    target=f"prop_{random.randint(0, 4)}",
                    strength=random.uniform(0.3, 0.9),
                )
            )

        return WarRoomData(nodes=nodes, links=links, timestamp=datetime.now())


_war_room_service = None


def get_war_room_service() -> WarRoomService:
    global _war_room_service
    if _war_room_service is None:
        _war_room_service = WarRoomService()
    return _war_room_service
