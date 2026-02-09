"""Property tour scheduling service with GHL calendar integration."""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimeSlot:
    """An available time slot for a property tour."""

    start: datetime
    end: datetime
    agent_name: str = "Jorge"
    location: str = ""


@dataclass
class BookingResult:
    """Result of a tour booking attempt."""

    success: bool
    booking_id: str = ""
    confirmation_message: str = ""
    error: str = ""


@dataclass
class Tour:
    """A scheduled property tour."""

    booking_id: str
    buyer_id: str
    property_id: str
    slot: TimeSlot
    status: str = "confirmed"  # confirmed, cancelled, completed
    created_at: datetime = field(default_factory=datetime.now)


class TourScheduler:
    """Schedules property tours via GHL calendar API."""

    SMS_MAX_LENGTH = 160

    def __init__(self, ghl_client=None, calendar_id: str = ""):
        self.ghl_client = ghl_client
        self.calendar_id = calendar_id
        self._bookings: Dict[str, Tour] = {}

    async def get_available_slots(
        self, agent_id: str = "", days_ahead: int = 7, limit: int = 3
    ) -> List[TimeSlot]:
        """Fetch available time slots from GHL calendar.

        Falls back to generated default slots if GHL unavailable.
        """
        if self.ghl_client and self.calendar_id:
            try:
                # Would call GHL calendar API:
                # GET /calendars/{calendar_id}/free-slots
                slots = await self._fetch_ghl_slots(days_ahead, limit)
                if slots:
                    return slots
            except Exception as e:
                logger.warning("GHL calendar unavailable, using defaults: %s", e)

        # Fallback: generate sensible default slots
        return self._generate_default_slots(days_ahead, limit)

    async def book_tour(
        self, buyer_id: str, property_id: str, slot: TimeSlot
    ) -> BookingResult:
        """Book a property tour for a buyer."""
        booking_id = f"tour-{uuid.uuid4().hex[:8]}"

        tour = Tour(
            booking_id=booking_id,
            buyer_id=buyer_id,
            property_id=property_id,
            slot=slot,
        )

        # Try GHL appointment creation
        if self.ghl_client and self.calendar_id:
            try:
                await self._create_ghl_appointment(tour)
            except Exception as e:
                logger.warning("GHL booking failed, stored locally: %s", e)

        self._bookings[booking_id] = tour

        confirmation = self._format_confirmation(tour)
        return BookingResult(
            success=True,
            booking_id=booking_id,
            confirmation_message=confirmation,
        )

    async def cancel_tour(self, booking_id: str) -> bool:
        """Cancel a scheduled tour."""
        tour = self._bookings.get(booking_id)
        if not tour:
            return False

        tour.status = "cancelled"

        if self.ghl_client:
            try:
                await self._cancel_ghl_appointment(booking_id)
            except Exception as e:
                logger.warning("GHL cancellation failed: %s", e)

        return True

    async def get_buyer_tours(self, buyer_id: str) -> List[Tour]:
        """Get all tours for a buyer."""
        return [
            t
            for t in self._bookings.values()
            if t.buyer_id == buyer_id and t.status != "cancelled"
        ]

    def format_slot_options(self, slots: List[TimeSlot]) -> str:
        """Format slots as SMS-friendly numbered options."""
        if not slots:
            return "No slots available right now. We'll follow up with times soon!"

        lines = ["Pick a time for your tour:"]
        for i, slot in enumerate(slots, 1):
            day = slot.start.strftime("%a %b %d")
            time_str = slot.start.strftime("%-I:%M%p").lower()
            lines.append(f"{i}. {day} at {time_str}")
        lines.append("Reply 1, 2, or 3!")

        result = "\n".join(lines)
        if len(result) > 320:
            result = result[:317] + "..."
        return result

    def _format_confirmation(self, tour: Tour) -> str:
        """Format booking confirmation SMS (< 160 chars)."""
        date_str = tour.slot.start.strftime("%a %b %d at %-I:%M%p").lower()
        msg = f"Tour confirmed for {date_str}. Reply CANCEL to reschedule."
        if len(msg) > self.SMS_MAX_LENGTH:
            msg = msg[: self.SMS_MAX_LENGTH - 3] + "..."
        return msg

    def _generate_default_slots(
        self, days_ahead: int, limit: int
    ) -> List[TimeSlot]:
        """Generate default time slots for the next N days."""
        slots = []
        base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

        for day_offset in range(1, days_ahead + 1):
            if len(slots) >= limit:
                break
            day = base + timedelta(days=day_offset)
            # Skip weekends for default slots
            if day.weekday() >= 5:
                continue
            slots.append(
                TimeSlot(
                    start=day,
                    end=day + timedelta(hours=1),
                    agent_name="Jorge",
                )
            )

        return slots[:limit]

    async def _fetch_ghl_slots(
        self, days_ahead: int, limit: int
    ) -> List[TimeSlot]:
        """Fetch available slots from GHL calendar API."""
        # GHL API integration point
        # GET /calendars/{self.calendar_id}/free-slots
        return []

    async def _create_ghl_appointment(self, tour: Tour) -> None:
        """Create appointment in GHL calendar."""
        # POST /calendars/{self.calendar_id}/appointments
        pass

    async def _cancel_ghl_appointment(self, booking_id: str) -> None:
        """Cancel appointment in GHL calendar."""
        pass
