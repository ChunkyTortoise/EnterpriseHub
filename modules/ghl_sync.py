from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


class GHLSyncService:
    """Lightweight GHL adapter used by the showcase API endpoints."""

    field_property_interest = "property_interest"

    def __init__(self) -> None:
        self.reset()

    @property
    def action_count(self) -> int:
        return len(self._actions)

    def reset(self) -> None:
        self._actions: List[Dict[str, Any]] = []

    def add_tag_to_contact(self, contact_id: str, tag: str) -> None:
        self._actions.append({"type": "tag", "contact_id": contact_id, "tag": tag})

    def update_contact_field(self, contact_id: str, field_id: str, value: Any) -> None:
        self._actions.append(
            {"type": "field_update", "contact_id": contact_id, "field_id": field_id, "value": value}
        )

    def trigger_match_webhook(self, contact_id: str, payload: Dict[str, Any]) -> bool:
        self._actions.append({"type": "match_webhook", "contact_id": contact_id, "payload": payload})
        return True

    def sync_contacts_from_ghl(self) -> int:
        # Deterministic demo return value for local runs/tests.
        return 2

    def inspect_custom_fields(self) -> Dict[str, Any]:
        return {
            "fields": [
                {"id": self.field_property_interest, "name": "Property Interest", "type": "text"},
            ]
        }

    def get_recent_actions(self, limit: int = 5) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        return deepcopy(self._actions[-limit:])

    def get_state_snapshot(self, recent_limit: int = 5) -> Dict[str, Any]:
        return {
            "action_count": self.action_count,
            "recent_actions": self.get_recent_actions(recent_limit),
        }
