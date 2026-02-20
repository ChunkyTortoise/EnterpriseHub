"""Voice-triggered calendar booking via GHL."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CalendarBookingService:
    """Books appointments via GHL calendar during voice calls."""

    api_key: str
    calendar_id: str
    location_id: str
    base_url: str = "https://services.leadconnectorhq.com"

    async def get_available_slots(
        self, date: str, timezone: str = "America/Los_Angeles"
    ) -> list[dict[str, str]]:
        """Get available calendar slots for a given date."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/calendars/{self.calendar_id}/free-slots",
                headers=headers,
                params={"startDate": date, "endDate": date, "timezone": timezone},
            )
            resp.raise_for_status()
            return resp.json().get("slots", [])

    async def book_appointment(
        self,
        contact_id: str,
        slot_time: str,
        title: str = "Voice AI Consultation",
        notes: str = "",
    ) -> dict[str, Any]:
        """Book an appointment for a contact."""
        import httpx

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Version": "2021-07-28",
        }

        payload = {
            "calendarId": self.calendar_id,
            "locationId": self.location_id,
            "contactId": contact_id,
            "startTime": slot_time,
            "title": title,
            "appointmentStatus": "confirmed",
            "notes": notes,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/calendars/events/appointments",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        logger.info("Appointment booked for contact %s at %s", contact_id, slot_time)
        return data
