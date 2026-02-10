from __future__ import annotations

from typing import Any, Dict


def trigger_outbound_call(
    contact_phone: str, contact_name: str, property_address: str, contact_id: str
) -> Dict[str, Any]:
    """No-op placeholder for demo/test environments."""
    return {
        "status": "queued",
        "contact_phone": contact_phone,
        "contact_name": contact_name,
        "property_address": property_address,
        "contact_id": contact_id,
    }
