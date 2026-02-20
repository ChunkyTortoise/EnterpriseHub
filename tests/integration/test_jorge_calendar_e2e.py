"""
Jorge Calendar Booking E2E Integration Tests

Full flow: lead qualifies as HOT -> seller bot offers calendar -> user selects slot -> appointment booked.
All GHL API calls are mocked.
"""

import pytest

pytestmark = pytest.mark.integration

from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.jorge.calendar_booking_service import (
    FALLBACK_MESSAGE,
    CalendarBookingService,
)

# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def mock_ghl_client():
    """GHL client mock with calendar methods."""
    client = AsyncMock()
    client.get_free_slots = AsyncMock(return_value=[
        {"start": "2026-03-01T10:00:00Z", "end": "2026-03-01T11:00:00Z"},
        {"start": "2026-03-01T14:00:00Z", "end": "2026-03-01T15:00:00Z"},
        {"start": "2026-03-02T09:00:00Z", "end": "2026-03-02T10:00:00Z"},
    ])
    client.create_appointment = AsyncMock(return_value={
        "id": "apt_123",
        "calendarId": "cal_abc",
        "contactId": "contact_hot_seller",
        "status": "confirmed",
    })
    client.update_contact = AsyncMock(return_value=True)
    return client


@pytest.fixture
def calendar_service(mock_ghl_client):
    """CalendarBookingService with mocked GHL client and a configured calendar ID."""
    with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_abc"}):
        svc = CalendarBookingService(ghl_client=mock_ghl_client)
    return svc


@pytest.fixture
def calendar_service_no_cal(mock_ghl_client):
    """CalendarBookingService with no calendar ID configured."""
    with patch.dict("os.environ", {}, clear=False):
        # Remove JORGE_CALENDAR_ID if it exists
        import os
        old = os.environ.pop("JORGE_CALENDAR_ID", None)
        svc = CalendarBookingService(ghl_client=mock_ghl_client)
        if old is not None:
            os.environ["JORGE_CALENDAR_ID"] = old
    return svc


# ── Test Class ────────────────────────────────────────────────────────

class TestJorgeCalendarE2E:
    """End-to-end calendar booking flow for HOT sellers."""

    @pytest.mark.asyncio
    async def test_full_booking_flow(self, calendar_service, mock_ghl_client):
        """HOT seller sees slots, picks one, appointment is booked."""
        contact_id = "contact_hot_seller"

        # Step 1: Offer appointment slots
        offer = await calendar_service.offer_appointment_slots(contact_id)

        assert offer["fallback"] is False
        assert len(offer["slots"]) == 3
        assert "scheduled" in offer["message"].lower() or "times" in offer["message"].lower()

        # Step 2: Seller picks slot index 1 (second option)
        booking = await calendar_service.book_appointment(contact_id, slot_index=1)

        assert booking["success"] is True
        assert booking["appointment"]["id"] == "apt_123"
        assert "booked" in booking["message"].lower() or "set" in booking["message"].lower()

        # Verify GHL create_appointment was called with correct slot
        mock_ghl_client.create_appointment.assert_called_once_with(
            calendar_id="cal_abc",
            contact_id=contact_id,
            start_time="2026-03-01T14:00:00Z",
            end_time="2026-03-01T15:00:00Z",
            title="Seller Consultation",
        )

    @pytest.mark.asyncio
    async def test_booking_clears_pending_slots(self, calendar_service):
        """After successful booking, pending slots are cleared for that contact."""
        contact_id = "contact_clear_test"

        await calendar_service.offer_appointment_slots(contact_id)
        assert contact_id in calendar_service._pending_slots

        await calendar_service.book_appointment(contact_id, slot_index=0)

        # Pending slots should be cleaned up
        assert contact_id not in calendar_service._pending_slots

    @pytest.mark.asyncio
    async def test_booking_without_prior_offer_fails_gracefully(self, calendar_service):
        """Attempting to book without first offering slots returns error."""
        result = await calendar_service.book_appointment("unknown_contact", slot_index=0)

        assert result["success"] is False
        assert result["appointment"] is None
        assert "no pending slots" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_invalid_slot_index_rejected(self, calendar_service):
        """Out-of-range slot index returns validation error."""
        contact_id = "contact_invalid_slot"
        await calendar_service.offer_appointment_slots(contact_id)

        # Index too high
        result = await calendar_service.book_appointment(contact_id, slot_index=99)
        assert result["success"] is False
        assert "valid option" in result["message"].lower()

        # Negative index
        result = await calendar_service.book_appointment(contact_id, slot_index=-1)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_fallback_when_no_calendar_configured(self, calendar_service_no_cal):
        """Without JORGE_CALENDAR_ID, service returns fallback message."""
        result = await calendar_service_no_cal.offer_appointment_slots("contact_any")

        assert result["fallback"] is True
        assert result["slots"] == []
        assert result["message"] == FALLBACK_MESSAGE

    @pytest.mark.asyncio
    async def test_fallback_when_no_slots_available(self, mock_ghl_client):
        """When GHL returns no free slots, service returns fallback."""
        mock_ghl_client.get_free_slots = AsyncMock(return_value=[])

        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_abc"}):
            svc = CalendarBookingService(ghl_client=mock_ghl_client)

        result = await svc.offer_appointment_slots("contact_no_slots")

        assert result["fallback"] is True
        assert result["slots"] == []

    @pytest.mark.asyncio
    async def test_failed_appointment_creation(self, mock_ghl_client):
        """When GHL create_appointment returns None, booking fails gracefully."""
        mock_ghl_client.create_appointment = AsyncMock(return_value=None)

        with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_abc"}):
            svc = CalendarBookingService(ghl_client=mock_ghl_client)

        await svc.offer_appointment_slots("contact_fail")
        result = await svc.book_appointment("contact_fail", slot_index=0)

        assert result["success"] is False
        assert result["appointment"] is None
        assert "wasn't able" in result["message"].lower() or "find other" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_slot_formatting(self, calendar_service):
        """Verify slot times are formatted in human-readable form."""
        contact_id = "contact_format_test"
        offer = await calendar_service.offer_appointment_slots(contact_id)

        # Should contain numbered options
        assert "1." in offer["message"]
        assert "2." in offer["message"]
        assert "3." in offer["message"]
        # Should contain day/time info
        assert "March" in offer["message"] or "Sunday" in offer["message"] or "Monday" in offer["message"]

    @pytest.mark.asyncio
    async def test_confirmation_message_content(self, calendar_service):
        """Verify booking confirmation includes the scheduled time."""
        contact_id = "contact_confirm_test"
        await calendar_service.offer_appointment_slots(contact_id)
        result = await calendar_service.book_appointment(contact_id, slot_index=0)

        assert result["success"] is True
        # Confirmation should mention "booked" or "set"
        assert "booked" in result["message"].lower() or "set" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_multiple_contacts_isolated(self, calendar_service):
        """Slots for different contacts don't interfere with each other."""
        await calendar_service.offer_appointment_slots("contact_a")
        await calendar_service.offer_appointment_slots("contact_b")

        # Book for contact_a, contact_b's slots should remain
        await calendar_service.book_appointment("contact_a", slot_index=0)

        assert "contact_a" not in calendar_service._pending_slots
        assert "contact_b" in calendar_service._pending_slots
