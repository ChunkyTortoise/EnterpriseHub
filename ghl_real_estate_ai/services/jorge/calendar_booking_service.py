"""
Calendar booking service for Jorge HOT seller appointments.

Integrates with GHL Calendar API to offer and book appointment slots
when a seller is classified as HOT.
"""

import os
from datetime import datetime
from typing import Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Fallback message when calendar is not configured
FALLBACK_MESSAGE = (
    "I'd love to schedule a time to discuss your options in detail. "
    "What would work better for you, morning or afternoon?"
)


class CalendarBookingService:
    """Service for offering and booking GHL calendar appointments for HOT sellers."""

    def __init__(self, ghl_client):
        """Initialize with an EnhancedGHLClient instance.

        Args:
            ghl_client: An EnhancedGHLClient (or compatible) instance.
        """
        self.ghl_client = ghl_client
        self.calendar_id = os.getenv("JORGE_CALENDAR_ID", "")
        self._pending_slots: Dict[str, List[Dict]] = {}

    async def offer_appointment_slots(self, contact_id: str) -> Dict:
        """Get free slots and format a message offering appointment options.

        Args:
            contact_id: GHL contact ID for the HOT seller.

        Returns:
            Dict with keys:
                - message: str — formatted message to send to the seller
                - slots: list — the raw slot data (empty if fallback)
                - fallback: bool — True if calendar is not configured
        """
        if not self.calendar_id:
            logger.warning("JORGE_CALENDAR_ID not configured, using fallback message")
            return {"message": FALLBACK_MESSAGE, "slots": [], "fallback": True}

        slots = await self.ghl_client.get_free_slots(self.calendar_id)

        if not slots:
            logger.info(f"No available slots for contact {contact_id}")
            return {"message": FALLBACK_MESSAGE, "slots": [], "fallback": True}

        # Cache slots for this contact so book_appointment can reference by index
        self._pending_slots[contact_id] = slots

        message = self._format_slot_options(slots)
        return {"message": message, "slots": slots, "fallback": False}

    async def book_appointment(self, contact_id: str, slot_index: int) -> Dict:
        """Book an appointment for the selected slot.

        Args:
            contact_id: GHL contact ID.
            slot_index: 0-based index of the slot the seller chose.

        Returns:
            Dict with keys:
                - success: bool
                - appointment: dict or None
                - message: str — confirmation or error message
        """
        slots = self._pending_slots.get(contact_id)
        if not slots:
            return {
                "success": False,
                "appointment": None,
                "message": "No pending slots found. Let me get fresh availability for you.",
            }

        if slot_index < 0 or slot_index >= len(slots):
            return {
                "success": False,
                "appointment": None,
                "message": f"Please choose a valid option (1-{len(slots)}).",
            }

        slot = slots[slot_index]
        appointment = await self.ghl_client.create_appointment(
            calendar_id=self.calendar_id,
            contact_id=contact_id,
            start_time=slot["start"],
            end_time=slot["end"],
            title="Seller Consultation",
        )

        if appointment:
            # Clean up pending slots
            self._pending_slots.pop(contact_id, None)
            return {
                "success": True,
                "appointment": appointment,
                "message": self._format_confirmation(slot),
            }

        return {
            "success": False,
            "appointment": None,
            "message": "I wasn't able to book that slot. Let me find other times for you.",
        }

    def _format_slot_options(self, slots: List[Dict]) -> str:
        """Format slots into a friendly message for the seller."""
        lines = ["Great news! Here are a few times I can get you scheduled:\n"]
        for i, slot in enumerate(slots, 1):
            formatted = self._format_slot_time(slot)
            lines.append(f"  {i}. {formatted}")
        lines.append("\nJust reply with the number that works best for you!")
        return "\n".join(lines)

    def _format_confirmation(self, slot: Dict) -> str:
        """Format a booking confirmation message."""
        formatted = self._format_slot_time(slot)
        return f"You're all set! Your consultation is booked for {formatted}. Looking forward to it!"

    @staticmethod
    def _format_slot_time(slot: Dict) -> str:
        """Format a single slot's start time for display."""
        start = slot.get("start", "")
        try:
            dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            return dt.strftime("%A, %B %d at %I:%M %p")
        except (ValueError, AttributeError):
            return start
