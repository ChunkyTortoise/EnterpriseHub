"""
Property Matcher Service for GHL Real Estate AI.

Matches lead preferences to available property listings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class PropertyMatcher:
    """
    Service to match leads with property listings based on preferences.
    """

    def __init__(self, listings_path: Optional[str] = None):
        """
        Initialize the Property Matcher.

        Args:
            listings_path: Path to the property listings JSON file.
        """
        self.listings_path = (
            Path(listings_path)
            if listings_path
            else Path(__file__).parent.parent
            / "data"
            / "knowledge_base"
            / "property_listings.json"
        )
        self.listings = self._load_listings()

    def _load_listings(self) -> List[Dict[str, Any]]:
        """Load listings from JSON file."""
        try:
            if self.listings_path.exists():
                with open(self.listings_path, "r") as f:
                    data = json.load(f)
                    return data.get("listings", [])
            else:
                logger.warning(
                    f"Property listings file not found at {self.listings_path}"
                )
                return []
        except Exception as e:
            logger.error(f"Failed to load property listings: {e}")
            return []

    def find_matches(
        self, preferences: Dict[str, Any], limit: int = 3, min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find property listings that match lead preferences.

        Args:
            preferences: Dict containing keys like 'budget', 'location', 'bedrooms', etc.
            limit: Maximum number of matches to return.
            min_score: Minimum match score (0.0 to 1.0) to include.

        Returns:
            List of matching listings with match scores.
        """
        matches = []

        for property in self.listings:
            score = self._calculate_match_score(property, preferences)
            if score >= min_score:
                property_with_score = property.copy()
                property_with_score["match_score"] = round(score, 2)
                matches.append(property_with_score)

        # Sort by score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)

        return matches[:limit]

    def _calculate_match_score(
        self, property: Dict[str, Any], preferences: Dict[str, Any]
    ) -> float:
        """Calculate a match score between 0.0 and 1.0 for a property."""
        score = 0.0
        weights = {
            "budget": 0.4,
            "location": 0.3,
            "bedrooms": 0.2,
            "property_type": 0.1,
        }

        # 1. Budget Match (40% weight)
        budget = preferences.get("budget")
        if budget:
            prop_price = property.get("price", 0)
            if prop_price <= budget:
                score += weights["budget"]
            elif prop_price <= budget * 1.1:  # 10% stretch
                score += weights["budget"] * 0.5
        else:
            score += weights["budget"] * 0.5  # Neutral if not specified

        # 2. Location Match (30% weight)
        pref_location = preferences.get("location")
        if pref_location:
            prop_loc = property.get("address", {}).get("city", "").lower()
            prop_neighborhood = (
                property.get("address", {}).get("neighborhood", "").lower()
            )

            # Handle list or string
            locations = (
                [pref_location.lower()]
                if isinstance(pref_location, str)
                else [loc.lower() for loc in pref_location]
            )

            if any(loc in prop_loc or loc in prop_neighborhood for loc in locations):
                score += weights["location"]
        else:
            score += weights["location"] * 0.5  # Neutral

        # 3. Bedrooms Match (20% weight)
        pref_beds = preferences.get("bedrooms")
        if pref_beds:
            prop_beds = property.get("bedrooms", 0)
            if prop_beds >= pref_beds:
                score += weights["bedrooms"]
            elif prop_beds == pref_beds - 1:
                score += weights["bedrooms"] * 0.5
        else:
            score += weights["bedrooms"] * 0.5  # Neutral

        # 4. Property Type Match (10% weight)
        pref_type = preferences.get("property_type")
        if pref_type:
            prop_type = property.get("property_type", "").lower()
            if pref_type.lower() in prop_type:
                score += weights["property_type"]
        else:
            score += weights["property_type"] * 0.5  # Neutral

        return score

    def format_match_for_sms(self, property: Dict[str, Any]) -> str:
        """Format a property match for an SMS message."""
        addr = property.get("address", {})
        price = property.get("price", 0)
        beds = property.get("bedrooms", 0)
        baths = property.get("bathrooms", 0)
        neighborhood = addr.get("neighborhood", addr.get("city", ""))

        return f"${price:,} in {neighborhood}: {beds}br/{baths}ba home. Check it out: {property.get('listing_url', 'N/A')}"
