"""
Mock RAG Service - Property matching simulation.
"""
import json
import os
from typing import List, Dict


class MockRAGService:
    """Simulates property retrieval and matching."""

    def __init__(self, knowledge_base_path: str = None):
        if knowledge_base_path is None:
            # Priority 1: Check local data folder (Deployment / Streamlit Cloud)
            # .../streamlit_demo/mock_services/mock_rag.py -> .../streamlit_demo/data/...
            local_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "knowledge_base", "property_listings.json"
            )

            # Priority 2: Check project root (Development)
            # enterprisehub/ghl_real_estate_ai/streamlit_demo/mock_services/mock_rag.py
            # -> enterprisehub/data/knowledge_base/property_listings.json
            project_root_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "data", "knowledge_base", "property_listings.json"
            )
            
            # Priority 3: Check ghl_real_estate_ai root (Intermediate)
            ghl_root_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "data", "knowledge_base", "property_listings.json"
            )

            if os.path.exists(local_path):
                knowledge_base_path = local_path
            elif os.path.exists(ghl_root_path):
                knowledge_base_path = ghl_root_path
            else:
                knowledge_base_path = project_root_path

        # Load actual property data
        with open(knowledge_base_path, 'r') as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                self.properties = data
            else:
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
        
        # Extract neighborhood from nested address if necessary
        prop_neighborhood = property.get('neighborhood', '')
        if not prop_neighborhood:
            address = property.get('address', {})
            if isinstance(address, dict):
                prop_neighborhood = address.get('neighborhood', '')
            elif isinstance(address, str):
                prop_neighborhood = address
        
        prop_neighborhood = str(prop_neighborhood).lower()
            
        if location and location in prop_neighborhood:
            score += 15

        return max(0, min(100, score))