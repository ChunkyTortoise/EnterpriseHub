"""
Lead-Property Matcher Service
Uses multi-dimensional scoring to identify the 'Perfect Match' property for a given contact.
"""

from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class LeadScoringService:
    def __init__(self):
        pass

    def match_leads_to_property(self, property_data: Dict[str, Any], leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Score leads based on how well they match a property.
        
        Scoring Criteria:
        - Budget Match (0-50 points)
        - Location Match (0-30 points)
        - Property Type/Tag Match (0-20 points)
        """
        matches = []
        
        # Extract property attributes
        prop_price = property_data.get("price") or property_data.get("valuation", {}).get("estimated_value", 0)
        prop_market = property_data.get("market", "").lower()
        prop_tags = [t.lower() for t in property_data.get("tags", [])]
        
        # Add common tags if they are in the address/description
        address = property_data.get("address", "").lower()
        if "austin" in address: prop_market = "austin"
        
        for lead in leads:
            score = 0
            
            # 1. Budget match (Up to 50 points)
            lead_budget = lead.get("budget", 0)
            if lead_budget >= prop_price:
                score += 50
            elif lead_budget >= prop_price * 0.8:
                score += 30
            elif lead_budget >= prop_price * 0.5:
                score += 10
                
            # 2. Location match (Up to 30 points)
            lead_prefs = [p.lower() for p in lead.get("preferences", [])]
            if prop_market in lead_prefs:
                score += 30
                
            # 3. Tag/Type match (Up to 20 points)
            overlap = set(lead_prefs).intersection(set(prop_tags))
            score += min(len(overlap) * 10, 20)
            
            if score >= 20: # Only include decent matches
                lead_copy = lead.copy()
                lead_copy["match_score"] = score
                lead_copy["match_reasons"] = self._get_match_reasons(lead, property_data, score)
                matches.append(lead_copy)
        
        # Sort by score descending
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return matches

    def _get_match_reasons(self, lead: Dict[str, Any], property_data: Dict[str, Any], score: int) -> List[str]:
        reasons = []
        if score >= 50: reasons.append("Strong budget alignment")
        
        prop_market = property_data.get("market", "").lower()
        lead_prefs = [p.lower() for p in lead.get("preferences", [])]
        if prop_market in lead_prefs:
            reasons.append(f"Preferred location: {prop_market.title()}")
            
        return reasons

lead_scoring_service = LeadScoringService()
