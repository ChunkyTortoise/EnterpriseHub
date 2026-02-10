from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional


class AppointmentManager:
    """Minimal appointment service used by Vapi tool endpoints."""

    def __init__(self) -> None:
        self.reset()

    @property
    def booking_count(self) -> int:
        return len(self._bookings)

    def reset(self) -> None:
        self._bookings: List[Dict[str, Any]] = []

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

    def book_tour(self, contact_id: Optional[str], slot_time: Optional[str], property_addr: str) -> Dict[str, Any]:
        if not contact_id:
            return {"status": "error", "message": "contact_id is required"}
        if not slot_time:
            return {"status": "error", "message": "slot_time is required"}

        booking = {
            "contact_id": contact_id,
            "slot_time": slot_time,
            "property_address": property_addr,
        }
        self._bookings.append(booking)
        return {"status": "success", "booking": booking}

    def get_recent_bookings(self, limit: int = 5) -> List[Dict[str, Any]]:
        if limit <= 0:
            return []
        return deepcopy(self._bookings[-limit:])

    def get_state_snapshot(self, recent_limit: int = 5) -> Dict[str, Any]:
        return {
            "booking_count": self.booking_count,
            "recent_bookings": self.get_recent_bookings(recent_limit),
        }
