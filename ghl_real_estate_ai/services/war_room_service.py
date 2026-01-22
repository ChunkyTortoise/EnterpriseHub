from typing import List, Dict, Any
from datetime import datetime
import random
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class WarRoomService:
    """
    Service for generating real-time market intelligence for the Jorge War Room Dashboard.
    Aggregates lead intent scores, property interest, and geographic data.
    """

    def __init__(self):
        # Austin, TX Center
        self.center_lat = 30.2672
        self.center_lng = -97.7431

    async def get_heat_map_data(self) -> Dict[str, Any]:
        """
        Generates real-time heat map data by clustering leads around properties.
        """
        logger.info("Generating War Room heat map data")
        
        # Mock Data Generation
        # In production, this would query the DB for active leads and their target properties
        
        properties = []
        relationships = []
        
        # Generate 5 "Hot" Properties
        for i in range(5):
            # Random location around Austin
            lat_offset = random.uniform(-0.05, 0.05)
            lng_offset = random.uniform(-0.05, 0.05)
            
            prop_id = f"prop_{i+1}"
            lead_count = random.randint(3, 12)
            
            # Generate FRS scores for leads interested in this property
            frs_scores = [random.randint(60, 95) for _ in range(lead_count)]
            heat_value = sum(frs_scores) / len(frs_scores)
            highest_frs = max(frs_scores)
            
            properties.append({
                "id": prop_id,
                "address": f"{random.randint(100, 9999)} {random.choice(['Congress', 'Lamar', '6th', 'Guadalupe', 'Burnet'])} St",
                "lat": self.center_lat + lat_offset,
                "lng": self.center_lng + lng_offset,
                "heat_value": round(heat_value, 1),
                "leads_count": lead_count,
                "highest_frs": highest_frs,
                "status": "active" if heat_value > 75 else "warm"
            })
            
            # Generate relationships for the graph
            for j in range(min(lead_count, 3)): # Show top 3 relationships per property
                relationships.append({
                    "source": f"Lead_{i}_{j}", # Mock Lead ID
                    "target": prop_id,
                    "strength": frs_scores[j] / 100.0,
                    "type": "interested"
                })

        return {
            "properties": properties,
            "relationships": relationships,
            "timestamp": datetime.utcnow().isoformat(),
            "market_summary": {
                "total_active_leads": sum(p['leads_count'] for p in properties),
                "hottest_area": "South Congress",
                "avg_market_heat": 78.5,
                "moat_status": "SECURE"
            },
            "patterns": [
                {
                    "type": "🔥 SUPPLY_SQUEEZE",
                    "desc": "Inventory in South Congress down 15% while FRS scores average 85+.",
                    "priority": "HIGH"
                },
                {
                    "type": "🚀 SEASONAL_SURGE",
                    "desc": "Tech-sector relocation markers up 22% in last 14 days.",
                    "priority": "MEDIUM"
                },
                {
                    "type": "⚠️ VALUE_GAP",
                    "desc": "Zillow Variance peaking in luxury Upland properties ($50K+ gap).",
                    "priority": "HIGH"
                }
            ]
        }

    async def get_lead_clusters(self) -> List[Dict[str, Any]]:
        """
        Returns clusters of leads based on geographic preferences.
        """
        # Placeholder for more advanced clustering logic
        return []
