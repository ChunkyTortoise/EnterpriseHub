"""
Simulated MLS Feed Service.
Provides a mock stream of market changes (price drops, new listings)
to test real-time Agent Swarm responses.
"""
import random
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class SimulatedMLSFeed:
    """
    Simulates an external MLS data source.
    """
    
    def __init__(self):
        self.active_properties = [
            {"id": "PROP_001", "price": 750000, "neighborhood": "Alta Loma"},
            {"id": "PROP_002", "price": 825000, "neighborhood": "Victoria Arbors"},
            {"id": "PROP_003", "price": 645000, "neighborhood": "Terra Vista"},
            {"id": "PROP_004", "price": 950000, "neighborhood": "North Rancho"},
            {"id": "PROP_005", "price": 525000, "neighborhood": "Central Rancho"}
        ]

    async def get_recent_changes(self, property_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Simulate getting recent market changes.
        """
        changes = []
        
        # Randomly trigger a price drop for a property of interest
        if property_ids:
            for prop_id in property_ids:
                if random.random() > 0.7: # 30% chance of a change
                    old_price = 0
                    neighborhood = "Unknown"
                    for p in self.active_properties:
                        if p["id"] == prop_id:
                            old_price = p["price"]
                            neighborhood = p["neighborhood"]
                            break
                    
                    if old_price > 0:
                        drop_percent = random.choice([3, 5, 7, 10])
                        new_price = int(old_price * (1 - drop_percent/100))
                        
                        changes.append({
                            "type": "price_drop",
                            "property_id": prop_id,
                            "neighborhood": neighborhood,
                            "old_price": old_price,
                            "new_price": new_price,
                            "amount": drop_percent,
                            "timestamp": datetime.now().isoformat()
                        })
        
        return changes

# Singleton instance
_simulated_mls = None

def get_simulated_mls() -> SimulatedMLSFeed:
    global _simulated_mls
    if _simulated_mls is None:
        _simulated_mls = SimulatedMLSFeed()
    return _simulated_mls
