"""
Tests for CalendarBookingService.

Validates GHL calendar integration for HOT seller appointment booking.
"""

from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.calendar_booking_service import (
    FALLBACK_MESSAGE,
    CalendarBookingService,
)


MOCK_SLOTS = [
    {"date": "2026-02-15", "start": "2026-02-15T09:00:00-08:00", "end": "2026-02-15T09:30:00-08:00"},
    {"date": "2026-02-15", "start": "2026-02-15T10:00:00-08:00", "end": "2026-02-15T10:30:00-08:00"},
    {"date": "2026-02-16", "start": "2026-02-16T14:00:00-08:00", "end": "2026-02-16T14:30:00-08:00"},
]


@pytest.fixture
def mock_ghl_client():
    """Create a mock GHL client with calendar methods."""
    client = AsyncMock()
    client.get_free_slots = AsyncMock(return_value=MOCK_SLOTS)
    client.create_appointment = AsyncMock(return_value={"id": "appt_123", "status": "confirmed"})
    return client


@pytest.fixture
def service_with_calendar(mock_ghl_client):
    """CalendarBookingService with JORGE_CALENDAR_ID set."""
    with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_abc123"}):
        svc = CalendarBookingService(mock_ghl_client)
    return svc


@pytest.fixture
def service_no_calendar(mock_ghl_client):
    """CalendarBookingService without JORGE_CALENDAR_ID."""
    with patch.dict("os.environ", {}, clear=True):
        svc = CalendarBookingService(mock_ghl_client)
        svc.calendar_id = ""
    return svc


class TestOfferAppointmentSlots:
    """Tests for offer_appointment_slots."""

    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_calendar_id(self, service_no_calendar):
        """Should return fallback message when JORGE_CALENDAR_ID is missing."""
        result = await service_no_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is True
        assert result["message"] == FALLBACK_MESSAGE
        assert result["slots"] == []

    @pytest.mark.asyncio
    async def test_returns_slots_when_calendar_configured(self, service_with_calendar, mock_ghl_client):
        """Should return formatted slots when calendar is configured and slots available."""
        result = await service_with_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is False
        assert len(result["slots"]) == 3
        assert "1." in result["message"]
        assert "2." in result["message"]
        assert "3." in result["message"]
        mock_ghl_client.get_free_slots.assert_awaited_once_with("cal_abc123")

    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_slots_available(self, service_with_calendar, mock_ghl_client):
        """Should return fallback when API returns no slots."""
        mock_ghl_client.get_free_slots.return_value = []

        result = await service_with_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is True
        assert result["message"] == FALLBACK_MESSAGE
        assert result["slots"] == []


class TestBookAppointment:
    """Tests for book_appointment."""

    @pytest.mark.asyncio
    async def test_successful_booking(self, service_with_calendar, mock_ghl_client):
        """Should book the selected slot and return confirmation."""
        # First offer slots to populate pending
        await service_with_calendar.offer_appointment_slots("contact_1")

        result = await service_with_calendar.book_appointment("contact_1", slot_index=0)

        assert result["success"] is True
        assert result["appointment"]["id"] == "appt_123"
        assert "booked" in result["message"].lower()
        mock_ghl_client.create_appointment.assert_awaited_once_with(
            calendar_id="cal_abc123",
            contact_id="contact_1",
            start_time="2026-02-15T09:00:00-08:00",
            end_time="2026-02-15T09:30:00-08:00",
            title="Seller Consultation",
        )

    @pytest.mark.asyncio
    async def test_booking_fails_no_pending_slots(self, service_with_calendar):
        """Should fail gracefully when no pending slots exist for the contact."""
        result = await service_with_calendar.book_appointment("unknown_contact", slot_index=0)

        assert result["success"] is False
        assert result["appointment"] is None
        assert "No pending slots" in result["message"]

    @pytest.mark.asyncio
    async def test_booking_fails_invalid_slot_index(self, service_with_calendar):
        """Should fail gracefully when slot index is out of range."""
        await service_with_calendar.offer_appointment_slots("contact_1")

        result = await service_with_calendar.book_appointment("contact_1", slot_index=5)

        assert result["success"] is False
        assert "valid option" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_booking_fails_when_api_returns_none(self, service_with_calendar, mock_ghl_client):
        """Should handle API failure (returns None) gracefully."""
        await service_with_calendar.offer_appointment_slots("contact_1")
        mock_ghl_client.create_appointment.return_value = None

        result = await service_with_calendar.book_appointment("contact_1", slot_index=0)

        assert result["success"] is False
        assert "wasn't able to book" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_pending_slots_cleared_after_booking(self, service_with_calendar):
        """Should clear pending slots after successful booking."""
        await service_with_calendar.offer_appointment_slots("contact_1")
        await service_with_calendar.book_appointment("contact_1", slot_index=0)

        # Second booking attempt should fail — slots cleared
        result = await service_with_calendar.book_appointment("contact_1", slot_index=0)
        assert result["success"] is False


class TestSlotFormatting:
    """Tests for slot time formatting."""

    def test_format_slot_time_iso(self, service_with_calendar):
        """Should format ISO datetime into friendly string."""
        slot = {"start": "2026-02-15T09:00:00-08:00"}
        formatted = service_with_calendar._format_slot_time(slot)
        assert "February" in formatted
        assert "09:00 AM" in formatted

    def test_format_slot_time_fallback(self, service_with_calendar):
        """Should return raw string if parsing fails."""
        slot = {"start": "not-a-date"}
        formatted = service_with_calendar._format_slot_time(slot)
        assert formatted == "not-a-date"
