from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class InventoryManager:
    """Simple in-memory inventory service for demo and test flows."""

    def __init__(self) -> None:
        self.reset()

    @property
    def interaction_count(self) -> int:
        return len(self._interactions)

    @property
    def lead_count(self) -> int:
        return len(self._leads)

    @property
    def property_count(self) -> int:
        return len(self._properties)

    def reset(self) -> None:
        self._leads: Dict[str, Dict[str, Any]] = {
            "lead_001": {"id": "lead_001", "name": "Alex Johnson", "phone": "+15551234567"},
            "lead_002": {"id": "lead_002", "name": "Morgan Lee", "phone": "+15557654321"},
        }
        self._properties: Dict[str, Dict[str, Any]] = {
            "prop_001": {"id": "prop_001", "address": "123 Palm Ave", "price": 585000, "beds": 3, "baths": 2},
            "prop_002": {"id": "prop_002", "address": "47 Cypress Ln", "price": 615000, "beds": 4, "baths": 3},
            "prop_003": {"id": "prop_003", "address": "9 Meadow Ct", "price": 542000, "beds": 3, "baths": 2},
        }
        self._interactions: List[Dict[str, Any]] = []

    def log_interaction(
        self,
        lead_id: str,
        property_id: str,
        action: str,
        feedback: Optional[Dict[str, Any]] = None,
        time_on_card: Optional[float] = None,
    ) -> None:
        self._interactions.append(
            {
                "lead_id": lead_id,
                "property_id": property_id,
                "action": action,
                "feedback": feedback or {},
                "time_on_card": time_on_card,
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            }
        )

    def get_smart_deck(self, contact_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        seen = {row["property_id"] for row in self._interactions if row["lead_id"] == contact_id}
        deck = [deepcopy(prop) for prop_id, prop in self._properties.items() if prop_id not in seen]
        return deck[:limit]

    def get_property(self, property_id: str) -> Optional[Dict[str, Any]]:
        prop = self._properties.get(property_id)
        return deepcopy(prop) if prop else None

    def get_lead(self, contact_id: str) -> Optional[Dict[str, Any]]:
        lead = self._leads.get(contact_id)
        return deepcopy(lead) if lead else None

    def get_recent_interactions(self, limit: int = 5) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        return deepcopy(self._interactions[-limit:])

    def get_state_snapshot(self, recent_limit: int = 5) -> Dict[str, Any]:
        return {
            "lead_count": self.lead_count,
            "property_count": self.property_count,
            "interaction_count": self.interaction_count,
            "recent_interactions": self.get_recent_interactions(recent_limit),
        }
