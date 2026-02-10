from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

DEFAULT_TENANT_ID = "tenant_default"


class AppointmentManager:
    """Minimal appointment service used by Vapi tool endpoints."""

    def __init__(self) -> None:
        self.reset()

    @property
    def booking_count(self) -> int:
        return sum(len(rows) for rows in self._bookings_by_tenant.values())

    def reset(self) -> None:
        self._bookings_by_tenant: Dict[str, List[Dict[str, Any]]] = {}

    @staticmethod
    def _normalize_tenant_id(tenant_id: str | None) -> str:
        if tenant_id is None:
            return DEFAULT_TENANT_ID
        normalized = tenant_id.strip()
        return normalized or DEFAULT_TENANT_ID

    def _tenant_bookings(self, tenant_id: str | None, create: bool = True) -> List[Dict[str, Any]]:
        normalized = self._normalize_tenant_id(tenant_id)
        if create:
            return self._bookings_by_tenant.setdefault(normalized, [])
        return self._bookings_by_tenant.get(normalized, [])

    def get_booking_count(self, tenant_id: str = DEFAULT_TENANT_ID) -> int:
        return len(self._tenant_bookings(tenant_id=tenant_id, create=False))

    def check_calendar_availability(self, date_query: Optional[str] = None) -> Dict[str, Any]:
        if date_query:
            try:
                start_date = date.fromisoformat(date_query)
            except ValueError:
                start_date = date.today()
        else:
            start_date = date.today()

        slots = []
        for idx, hour in enumerate((10, 13, 16)):
            slot_date = start_date + timedelta(days=idx)
            slot_dt = datetime.combine(slot_date, datetime.min.time()).replace(hour=hour, minute=0, second=0)
            slots.append(slot_dt.isoformat())
        return {"status": "success", "slots": slots}

    def book_tour(
        self,
        contact_id: Optional[str],
        slot_time: Optional[str],
        property_addr: str,
        tenant_id: str = DEFAULT_TENANT_ID,
    ) -> Dict[str, Any]:
        if not contact_id:
            return {"status": "error", "message": "contact_id is required"}
        if not slot_time:
            return {"status": "error", "message": "slot_time is required"}

        booking = {
            "tenant_id": self._normalize_tenant_id(tenant_id),
            "contact_id": contact_id,
            "slot_time": slot_time,
            "property_address": property_addr,
        }
        self._tenant_bookings(tenant_id=tenant_id).append(booking)
        return {"status": "success", "booking": booking}

    def get_recent_bookings(self, tenant_id: str = DEFAULT_TENANT_ID, limit: int = 5) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        bookings = self._tenant_bookings(tenant_id=tenant_id, create=False)
        return deepcopy(bookings[-limit:])

    def get_state_snapshot(self, tenant_id: str = DEFAULT_TENANT_ID, recent_limit: int = 5) -> Dict[str, Any]:
        return {
            "tenant_id": self._normalize_tenant_id(tenant_id),
            "booking_count": self.get_booking_count(tenant_id=tenant_id),
            "recent_bookings": self.get_recent_bookings(tenant_id=tenant_id, limit=recent_limit),
        }
