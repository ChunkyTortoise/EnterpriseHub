"""
Integration tests for CalendarBookingService.

Covers the 8 required scenarios:
1. No calendar ID configured -> graceful fallback
2. Available slots formatting (human-readable)
3. No availability -> user-friendly fallback message
4. Valid booking flow
5. Invalid slot index -> error handling
6. No pending offer -> appropriate response
7. API failure -> graceful degradation
8. Slot time formatting correctness
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

# Ensure test env vars before importing production code
for _k, _v in {
    "ANTHROPIC_API_KEY": "sk-ant-test-fake",
    "GHL_API_KEY": "test_ghl_api_key",
    "GHL_LOCATION_ID": "test_location_id",
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing-only-minimum-32-chars",
}.items():
    if _k not in os.environ:
        os.environ[_k] = _v

from ghl_real_estate_ai.services.jorge.calendar_booking_service import (
    FALLBACK_MESSAGE,
    CalendarBookingService,
)

MOCK_SLOTS = [
    {
        "date": "2026-02-20",
        "start": "2026-02-20T09:00:00-08:00",
        "end": "2026-02-20T09:30:00-08:00",
    },
    {
        "date": "2026-02-20",
        "start": "2026-02-20T11:00:00-08:00",
        "end": "2026-02-20T11:30:00-08:00",
    },
    {
        "date": "2026-02-21",
        "start": "2026-02-21T14:00:00-08:00",
        "end": "2026-02-21T14:30:00-08:00",
    },
]


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client with calendar methods."""
    client = AsyncMock()
    client.get_free_slots = AsyncMock(return_value=MOCK_SLOTS)
    client.create_appointment = AsyncMock(
        return_value={"id": "appt_456", "status": "confirmed"}
    )
    return client


@pytest.fixture
def service_with_calendar(mock_ghl_client):
    """CalendarBookingService with calendar ID configured."""
    with patch.dict("os.environ", {"JORGE_CALENDAR_ID": "cal_test_123"}):
        svc = CalendarBookingService(mock_ghl_client)
    return svc


@pytest.fixture
def service_no_calendar(mock_ghl_client):
    """CalendarBookingService without calendar ID."""
    with patch.dict("os.environ", {}, clear=True):
        svc = CalendarBookingService(mock_ghl_client)
        svc.calendar_id = ""
    return svc


# ============================================================================
# Test 1: No calendar ID configured -> graceful fallback
# ============================================================================
class TestNoCalendarIdFallback:
    @pytest.mark.asyncio
    async def test_no_calendar_id_returns_fallback(self, service_no_calendar):
        """When JORGE_CALENDAR_ID is not set, should return fallback message
        without calling the GHL API."""
        result = await service_no_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is True
        assert result["message"] == FALLBACK_MESSAGE
        assert result["slots"] == []
        # GHL client should NOT be called at all
        service_no_calendar.ghl_client.get_free_slots.assert_not_awaited()


# ============================================================================
# Test 2: Available slots formatting (human-readable)
# ============================================================================
class TestSlotsFormatting:
    @pytest.mark.asyncio
    async def test_slots_formatted_as_numbered_options(self, service_with_calendar):
        """Offered slots should be numbered and human-readable."""
        result = await service_with_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is False
        msg = result["message"]
        # Should contain numbered options
        assert "1." in msg
        assert "2." in msg
        assert "3." in msg
        # Should contain friendly call-to-action
        assert "reply with the number" in msg.lower()


# ============================================================================
# Test 3: No availability -> user-friendly fallback message
# ============================================================================
class TestNoAvailability:
    @pytest.mark.asyncio
    async def test_empty_slots_returns_fallback(
        self, service_with_calendar, mock_ghl_client
    ):
        """When API returns zero slots, should return fallback message."""
        mock_ghl_client.get_free_slots.return_value = []

        result = await service_with_calendar.offer_appointment_slots("contact_1")

        assert result["fallback"] is True
        assert result["message"] == FALLBACK_MESSAGE
        assert result["slots"] == []


# ============================================================================
# Test 4: Valid booking flow
# ============================================================================
class TestValidBookingFlow:
    @pytest.mark.asyncio
    async def test_successful_booking_returns_confirmation(
        self, service_with_calendar, mock_ghl_client
    ):
        """Full flow: offer slots -> select slot 0 -> get confirmation."""
        # Step 1: Offer slots
        await service_with_calendar.offer_appointment_slots("contact_1")

        # Step 2: Book slot index 0
        result = await service_with_calendar.book_appointment("contact_1", slot_index=0)

        assert result["success"] is True
        assert result["appointment"]["id"] == "appt_456"
        assert "booked" in result["message"].lower() or "all set" in result["message"].lower()

        # Verify correct slot was sent to GHL
        mock_ghl_client.create_appointment.assert_awaited_once_with(
            calendar_id="cal_test_123",
            contact_id="contact_1",
            start_time="2026-02-20T09:00:00-08:00",
            end_time="2026-02-20T09:30:00-08:00",
            title="Seller Consultation",
        )


# ============================================================================
# Test 5: Invalid slot index -> error handling
# ============================================================================
class TestInvalidSlotIndex:
    @pytest.mark.asyncio
    async def test_out_of_range_index_returns_error(self, service_with_calendar):
        """Selecting an out-of-range slot should fail gracefully."""
        await service_with_calendar.offer_appointment_slots("contact_1")

        result = await service_with_calendar.book_appointment("contact_1", slot_index=10)

        assert result["success"] is False
        assert result["appointment"] is None
        assert "valid option" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_negative_index_returns_error(self, service_with_calendar):
        """Negative slot index should fail gracefully."""
        await service_with_calendar.offer_appointment_slots("contact_1")

        result = await service_with_calendar.book_appointment("contact_1", slot_index=-1)

        assert result["success"] is False
        assert result["appointment"] is None


# ============================================================================
# Test 6: No pending offer -> appropriate response
# ============================================================================
class TestNoPendingOffer:
    @pytest.mark.asyncio
    async def test_booking_without_offer_returns_no_pending(self, service_with_calendar):
        """Attempting to book without first offering slots should fail with
        a helpful message."""
        result = await service_with_calendar.book_appointment(
            "unknown_contact", slot_index=0
        )

        assert result["success"] is False
        assert result["appointment"] is None
        assert "no pending slots" in result["message"].lower()


# ============================================================================
# Test 7: API failure -> graceful degradation
# ============================================================================
class TestAPIFailure:
    @pytest.mark.asyncio
    async def test_create_appointment_returns_none_on_failure(
        self, service_with_calendar, mock_ghl_client
    ):
        """When GHL create_appointment returns None (API error),
        should fail gracefully with a retry-friendly message."""
        await service_with_calendar.offer_appointment_slots("contact_1")
        mock_ghl_client.create_appointment.return_value = None

        result = await service_with_calendar.book_appointment("contact_1", slot_index=0)

        assert result["success"] is False
        assert result["appointment"] is None
        assert "wasn't able to book" in result["message"].lower()


# ============================================================================
# Test 8: Slot time formatting correctness
# ============================================================================
class TestSlotTimeFormatting:
    def test_iso_datetime_formatted_correctly(self, service_with_calendar):
        """ISO datetime should be formatted as 'Weekday, Month DD at HH:MM AM/PM'."""
        slot = {"start": "2026-02-20T09:00:00-08:00"}
        formatted = service_with_calendar._format_slot_time(slot)

        assert "February" in formatted
        assert "20" in formatted
        assert "09:00 AM" in formatted

    def test_invalid_datetime_falls_back_to_raw(self, service_with_calendar):
        """Invalid datetime strings should be returned as-is."""
        slot = {"start": "not-a-valid-date"}
        formatted = service_with_calendar._format_slot_time(slot)
        assert formatted == "not-a-valid-date"

    def test_empty_start_returns_empty(self, service_with_calendar):
        """Slot with empty start should return empty string."""
        slot = {"start": ""}
        formatted = service_with_calendar._format_slot_time(slot)
        assert formatted == ""
