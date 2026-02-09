"""
Property Matching Strategy Pattern.

Defines the interface and concrete strategies for matching properties
to lead preferences, allowing runtime switching between basic filtering
and advanced AI semantic search.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class PropertyMatchingStrategy(ABC):
    """
    Abstract base class for property matching strategies.
    """

    @abstractmethod
    def find_matches(
        self, listings: List[Dict[str, Any]], preferences: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find property matches based on the strategy implementation.

        Args:
            listings: List of available property listings.
            preferences: Lead's preferences (budget, location, etc.).
            limit: Max number of results.

        Returns:
            List of matching properties with 'match_score' and reasoning.
        """
        pass


class BasicFilteringStrategy(PropertyMatchingStrategy):
    """
    Standard deterministic filtering based on hard constraints
    (Budget, Beds, Location) with simple weighting.
    """

    def find_matches(
        self, listings: List[Dict[str, Any]], preferences: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:

        scored_listings = []

        for prop in listings:
            score = self._calculate_basic_score(prop, preferences)
            if score > 0.4:  # Minimum threshold
                prop_copy = prop.copy()
                prop_copy["match_score"] = round(score, 2)
                prop_copy["match_type"] = "Basic Filter"
                scored_listings.append(prop_copy)

        # Sort desc by score
        scored_listings.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_listings[:limit]

    def _calculate_basic_score(self, prop: Dict[str, Any], pref: Dict[str, Any]) -> float:
        score = 0.0

        # 1. Budget (Critical)
        budget = pref.get("budget", 0)
        price = prop.get("price", 0)
        if budget and price:
            if price <= budget:
                score += 0.4
            elif price <= budget * 1.1:  # 10% Stretch
                score += 0.2
        else:
            score += 0.2  # Neutral

        # 2. Bedrooms
        req_beds = pref.get("bedrooms", 0)
        prop_beds = prop.get("bedrooms", 0)
        if req_beds and prop_beds:
            if prop_beds >= req_beds:
                score += 0.3
            elif prop_beds == req_beds - 1:
                score += 0.1
        else:
            score += 0.15

        # 3. Location (Simple substring match)
        req_loc = pref.get("location", "").lower()
        prop_addr = str(prop.get("address", {})).lower()
        if req_loc and req_loc in prop_addr:
            score += 0.3

        return min(1.0, score)


class AISemanticSearchStrategy(PropertyMatchingStrategy):
    """
    Advanced strategy using Vector Search / Semantic Similarity.
    (Currently a Stub/Simulation for the Deep Build phase)
    """

    def find_matches(
        self, listings: List[Dict[str, Any]], preferences: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:

        # In a real implementation, this would:
        # 1. Embed the user's "natural language" preferences.
        # 2. Query a Vector DB (Chroma/Pinecone).
        # 3. Return nearest neighbors.

        # Simulation Logic:
        # Boost score if 'description' contains keywords from 'must_haves'

        scored_listings = []
        must_haves = preferences.get("must_haves", [])

        for prop in listings:
            base_score = 0.5  # Start higher for "AI" fuzziness

            # Semantic boost
            desc = prop.get("description", "").lower()
            features = [f.lower() for f in prop.get("features", [])]
            combined_text = desc + " " + " ".join(features)

            matches = 0
            for item in must_haves:
                if item.lower() in combined_text:
                    matches += 1

            if must_haves:
                boost = (matches / len(must_haves)) * 0.4
                base_score += boost

            prop_copy = prop.copy()
            prop_copy["match_score"] = round(min(0.99, base_score), 2)
            prop_copy["match_type"] = "AI Semantic"
            prop_copy["ai_reasoning"] = f"Matched {matches}/{len(must_haves)} lifestyle factors."

            scored_listings.append(prop_copy)

        scored_listings.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_listings[:limit]
