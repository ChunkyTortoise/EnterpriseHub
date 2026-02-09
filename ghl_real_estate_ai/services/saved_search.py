"""Buyer saved search and listing alert service."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class SearchCriteria:
    """Criteria for a saved property search."""

    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    beds_min: Optional[int] = None
    baths_min: Optional[int] = None
    features: List[str] = field(default_factory=list)
    neighborhoods: List[str] = field(default_factory=list)
    max_dom: Optional[int] = None  # max days on market


@dataclass
class SavedSearch:
    """A saved search for a buyer."""

    id: str
    buyer_id: str
    criteria: SearchCriteria
    created_at: datetime = field(default_factory=datetime.now)
    last_checked: Optional[datetime] = None
    matches_sent: int = 0
    active: bool = True
    _notified_ids: Set[str] = field(default_factory=set, repr=False)


class SavedSearchService:
    """Manages saved searches and new listing alerts."""

    SMS_MAX_LENGTH = 160

    def __init__(self) -> None:
        self._searches: Dict[str, SavedSearch] = {}

    async def create_search(
        self, buyer_id: str, criteria: SearchCriteria
    ) -> SavedSearch:
        """Create a new saved search for a buyer."""
        search_id = f"search-{uuid.uuid4().hex[:8]}"
        search = SavedSearch(
            id=search_id,
            buyer_id=buyer_id,
            criteria=criteria,
        )
        self._searches[search_id] = search
        logger.info("Saved search %s created for buyer %s", search_id, buyer_id)
        return search

    async def check_new_matches(
        self, search_id: str, available_listings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Check for new listings matching a saved search.

        Returns only listings not previously notified about.
        """
        search = self._searches.get(search_id)
        if not search or not search.active:
            return []

        matches: List[Dict[str, Any]] = []
        for listing in available_listings:
            listing_id = listing.get("id", listing.get("address", ""))
            if listing_id in search._notified_ids:
                continue  # Already notified

            if self._matches_criteria(listing, search.criteria):
                matches.append(listing)

        search.last_checked = datetime.now()
        return matches

    async def notify_buyer(
        self, search: SavedSearch, new_matches: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate notification messages for new matches."""
        messages: List[str] = []
        for match in new_matches:
            listing_id = match.get("id", match.get("address", ""))
            msg = self._format_alert(match)
            messages.append(msg)
            search._notified_ids.add(listing_id)
            search.matches_sent += 1
        return messages

    async def deactivate_search(self, search_id: str) -> bool:
        """Deactivate a saved search."""
        search = self._searches.get(search_id)
        if not search:
            return False
        search.active = False
        logger.info("Search %s deactivated", search_id)
        return True

    async def get_active_searches(self, buyer_id: str) -> List[SavedSearch]:
        """Get all active searches for a buyer."""
        return [
            s
            for s in self._searches.values()
            if s.buyer_id == buyer_id and s.active
        ]

    def _matches_criteria(
        self, listing: Dict[str, Any], criteria: SearchCriteria
    ) -> bool:
        """Check if a listing matches search criteria."""
        price = listing.get("price", 0)
        if criteria.budget_max and price > criteria.budget_max:
            return False
        if criteria.budget_min and price < criteria.budget_min:
            return False

        beds = listing.get("bedrooms", 0)
        if criteria.beds_min and beds < criteria.beds_min:
            return False

        baths = listing.get("bathrooms", 0)
        if criteria.baths_min and baths < criteria.baths_min:
            return False

        if criteria.neighborhoods:
            area = listing.get("neighborhood", "").lower()
            if area and not any(
                n.lower() in area for n in criteria.neighborhoods
            ):
                return False

        if criteria.max_dom is not None:
            dom = listing.get("days_on_market", 0)
            if dom > criteria.max_dom:
                return False

        return True

    def _format_alert(self, listing: Dict[str, Any]) -> str:
        """Format a listing alert SMS (< 160 chars)."""
        address = listing.get("address", "New listing")
        price = listing.get("price", 0)
        beds = listing.get("bedrooms", "?")
        baths = listing.get("bathrooms", "?")
        area = listing.get("neighborhood", "")

        price_str = f"${price / 1000:.0f}K" if price >= 1000 else f"${price}"
        area_str = f" in {area}" if area else ""

        msg = (
            f"New listing! {address} - {price_str}, "
            f"{beds}bd/{baths}ba{area_str}. Reply INFO for details."
        )

        if len(msg) > self.SMS_MAX_LENGTH:
            msg = msg[: self.SMS_MAX_LENGTH - 3] + "..."
        return msg
