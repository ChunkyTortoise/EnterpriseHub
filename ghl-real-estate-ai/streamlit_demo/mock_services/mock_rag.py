"""
Mock RAG Service - Property matching simulation.
"""
import json
import os
from typing import List, Dict


class MockRAGService:
    """Simulates property retrieval and matching."""

    def __init__(self, knowledge_base_path: str = None):
        # Load actual property data
        if knowledge_base_path is None:
            # Default path relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            knowledge_base_path = os.path.join(base_dir, "data", "knowledge_base", "property_listings.json")

        with open(knowledge_base_path, 'r') as f:
            data = json.load(f)
            self.properties = data.get('listings', [])

    def search_properties(
        self,
        preferences: Dict,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find properties matching user preferences.

        Simulates semantic search with scoring.
        """
        results = []

        for prop in self.properties:
            score = self._calculate_match_score(prop, preferences)
            if score > 0:
                results.append({
                    **prop,
                    'match_score': score
                })

        # Sort by score, return top K
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:top_k]

    def _calculate_match_score(self, property: Dict, preferences: Dict) -> float:
        """Calculate how well property matches preferences (0-100)."""
        score = 70  # Base score

        # Budget match
        budget = preferences.get('budget')
        if budget:
            price = property.get('price', 0)
            if price <= budget:
                score += 15
            elif price <= budget * 1.1:  # Within 10%
                score += 8
            else:
                score -= 10

        # Bedroom match
        bedrooms = preferences.get('bedrooms')
        if bedrooms and property.get('bedrooms') == bedrooms:
            score += 10

        # Location match
        location = preferences.get('location', '').lower()
        prop_neighborhood = property.get('address', {}).get('neighborhood', '').lower()
        if location and location in prop_neighborhood:
            score += 15

        return max(0, min(100, score))
