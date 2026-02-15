from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List

DEFAULT_TENANT_ID = "tenant_default"


class GHLSyncService:
    """Lightweight GHL adapter used by the showcase API endpoints."""

    field_property_interest = "property_interest"

    def __init__(self) -> None:
        self.reset()

    @property
    def action_count(self) -> int:
        return sum(len(rows) for rows in self._actions_by_tenant.values())

    def reset(self) -> None:
        self._actions_by_tenant: Dict[str, List[Dict[str, Any]]] = {}

    @staticmethod
    def _normalize_tenant_id(tenant_id: str | None) -> str:
        if tenant_id is None:
            return DEFAULT_TENANT_ID
        normalized = tenant_id.strip()
        return normalized or DEFAULT_TENANT_ID

    def _tenant_actions(self, tenant_id: str | None, create: bool = True) -> List[Dict[str, Any]]:
        normalized = self._normalize_tenant_id(tenant_id)
        if create:
            return self._actions_by_tenant.setdefault(normalized, [])
        return self._actions_by_tenant.get(normalized, [])

    def get_action_count(self, tenant_id: str = DEFAULT_TENANT_ID) -> int:
        return len(self._tenant_actions(tenant_id=tenant_id, create=False))

    def add_tag_to_contact(self, contact_id: str, tag: str, tenant_id: str = DEFAULT_TENANT_ID) -> None:
        self._tenant_actions(tenant_id=tenant_id).append(
            {"type": "tag", "tenant_id": self._normalize_tenant_id(tenant_id), "contact_id": contact_id, "tag": tag}
        )

    def update_contact_field(
        self,
        contact_id: str,
        field_id: str,
        value: Any,
        tenant_id: str = DEFAULT_TENANT_ID,
    ) -> None:
        self._tenant_actions(tenant_id=tenant_id).append(
            {
                "type": "field_update",
                "tenant_id": self._normalize_tenant_id(tenant_id),
                "contact_id": contact_id,
                "field_id": field_id,
                "value": value,
            }
        )

    def trigger_match_webhook(
        self, contact_id: str, payload: Dict[str, Any], tenant_id: str = DEFAULT_TENANT_ID
    ) -> bool:
        self._tenant_actions(tenant_id=tenant_id).append(
            {
                "type": "match_webhook",
                "tenant_id": self._normalize_tenant_id(tenant_id),
                "contact_id": contact_id,
                "payload": payload,
            }
        )
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

    def get_recent_actions(self, tenant_id: str = DEFAULT_TENANT_ID, limit: int = 5) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        actions = self._tenant_actions(tenant_id=tenant_id, create=False)
        return deepcopy(actions[-limit:])

    def get_state_snapshot(self, tenant_id: str = DEFAULT_TENANT_ID, recent_limit: int = 5) -> Dict[str, Any]:
        return {
            "tenant_id": self._normalize_tenant_id(tenant_id),
            "action_count": self.get_action_count(tenant_id=tenant_id),
            "recent_actions": self.get_recent_actions(tenant_id=tenant_id, limit=recent_limit),
        }
