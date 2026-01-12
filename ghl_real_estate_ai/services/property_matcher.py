"""
Property Matcher Service for GHL Real Estate AI.

Matches lead preferences to available property listings.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class PropertyMatcher:
    """
    Service to match leads with property listings based on preferences.
    Upgraded to Agentic Reasoning in Phase 2.
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
        self.llm_client = LLMClient(
            provider="claude",
            model=settings.claude_model
        )

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

    def generate_match_reasoning(self, property: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """
        Generate the 'Why' - a human-readable reason for the match.
        """
        reasons = []
        
        # Budget
        budget = preferences.get("budget", 0)
        price = property.get("price", 0)
        if budget and price <= budget:
            savings = budget - price
            if savings > 50000:
                reasons.append(f"it's ${savings/1000:.0f}k under your budget")
            else:
                reasons.append("it fits your price range")
                
        # Location
        loc = preferences.get("location")
        if loc and isinstance(loc, str) and loc.lower() in str(property.get("address")).lower():
            reasons.append(f"it's in {loc}")
            
        # Features/Bedrooms
        beds = preferences.get("bedrooms")
        if beds and property.get("bedrooms", 0) >= beds:
            reasons.append(f"has the {beds}+ bedrooms you needed")
            
        if not reasons:
            return "it's a strong overall match for your criteria"
            
        return f"I picked this because {', and '.join(reasons)}."

    async def agentic_explain_match(self, property: Dict[str, Any], preferences: Dict[str, Any]) -> str:
        """
        🆕 Phase 2: Agentic Match Explanation
        Uses Claude to provide strategic, psychological, and financial reasoning.
        """
        prompt = f"""You are a senior Real Estate Investment Strategist. Explain why this property is a strategic match for this specific lead.

PROPERTY DATA:
{json.dumps(property, indent=2)}

LEAD PREFERENCES:
{json.dumps(preferences, indent=2)}

YOUR GOAL:
1. Provide a "Psychological Hook" (why it fits their life/goals).
2. Provide a "Financial Logic" (value, ROI, or budget fit).
3. Be professional, direct, and authoritative.
4. Keep it under 3 sentences for SMS/Chat consumption.

Example: "This South Lamar home is a strategic capture; it sits 5% below your budget while offering the modern renovation you prioritized. The high walkability score aligns with your request for an active neighborhood lifestyle."
"""
        try:
            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are an expert Real Estate Strategist. Speak with authority and precision.",
                temperature=0.7,
                max_tokens=200
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"Agentic explanation failed: {e}")
            return self.generate_match_reasoning(property, preferences)

    def format_match_for_sms(self, property: Dict[str, Any]) -> str:
        """Format a property match for an SMS message."""
        addr = property.get("address", {})
        price = property.get("price", 0)
        beds = property.get("bedrooms", 0)
        baths = property.get("bathrooms", 0)
        neighborhood = addr.get("neighborhood", addr.get("city", ""))

        return f"${price:,} in {neighborhood}: {beds}br/{baths}ba home. Check it out: {property.get('listing_url', 'N/A')}"
