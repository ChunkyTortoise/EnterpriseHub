import pytest

pytestmark = pytest.mark.integration

"""Tests for TourScheduler — property tour scheduling with GHL calendar integration."""

from datetime import datetime, timedelta

import pytest

from ghl_real_estate_ai.services.tour_scheduler import (
    BookingResult,
    TimeSlot,
    Tour,
    TourScheduler,
)


@pytest.fixture
def scheduler():
    """TourScheduler with no GHL client (uses default slot generation)."""
    return TourScheduler()


@pytest.fixture
def sample_slot():
    """A sample time slot for booking tests."""
    start = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return TimeSlot(
        start=start,
        end=start + timedelta(hours=1),
        agent_name="Jorge",
        location="123 Main St, Rancho Cucamonga, CA",
    )


class TestTourScheduler:
    """Tests for TourScheduler service."""

    @pytest.mark.asyncio
    async def test_get_available_slots_returns_within_range(self, scheduler):
        """Default slots generated, count <= limit."""
        slots = await scheduler.get_available_slots(days_ahead=7, limit=3)
        assert len(slots) <= 3
        assert len(slots) > 0
        for slot in slots:
            assert isinstance(slot, TimeSlot)
            assert slot.end > slot.start

    @pytest.mark.asyncio
    async def test_book_tour_creates_appointment(self, scheduler, sample_slot):
        """Booking returns success=True with a booking_id."""
        result = await scheduler.book_tour(
            buyer_id="buyer_001",
            property_id="prop_abc",
            slot=sample_slot,
        )
        assert isinstance(result, BookingResult)
        assert result.success is True
        assert result.booking_id.startswith("tour-")
        assert len(result.booking_id) > 5

    @pytest.mark.asyncio
    async def test_book_tour_sends_confirmation_sms(self, scheduler, sample_slot):
        """Confirmation message is non-empty after booking."""
        result = await scheduler.book_tour(
            buyer_id="buyer_002",
            property_id="prop_def",
            slot=sample_slot,
        )
        assert result.confirmation_message
        assert "confirmed" in result.confirmation_message.lower()

    @pytest.mark.asyncio
    async def test_cancel_tour_removes_appointment(self, scheduler, sample_slot):
        """Cancelled tour status is 'cancelled'."""
        result = await scheduler.book_tour(
            buyer_id="buyer_003",
            property_id="prop_ghi",
            slot=sample_slot,
        )
        cancelled = await scheduler.cancel_tour(result.booking_id)
        assert cancelled is True

        tour = scheduler._bookings[result.booking_id]
        assert tour.status == "cancelled"

    @pytest.mark.asyncio
    async def test_sms_confirmation_under_160_chars(self, scheduler, sample_slot):
        """Confirmation message respects SMS 160-char limit."""
        result = await scheduler.book_tour(
            buyer_id="buyer_004",
            property_id="prop_jkl",
            slot=sample_slot,
        )
        assert len(result.confirmation_message) <= TourScheduler.SMS_MAX_LENGTH

    @pytest.mark.asyncio
    async def test_no_slots_available_returns_empty(self, scheduler):
        """days_ahead=0 returns empty list (no future days to generate)."""
        slots = await scheduler.get_available_slots(days_ahead=0, limit=3)
        assert slots == []

    @pytest.mark.asyncio
    async def test_format_slot_options_numbered(self, scheduler):
        """3 slots produce '1.', '2.', '3.' in formatted output."""
        base = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        slots = [TimeSlot(start=base + timedelta(days=i), end=base + timedelta(days=i, hours=1)) for i in range(1, 4)]
        formatted = scheduler.format_slot_options(slots)
        assert "1." in formatted
        assert "2." in formatted
        assert "3." in formatted
        assert "Reply 1, 2, or 3!" in formatted

    @pytest.mark.asyncio
    async def test_get_buyer_tours_excludes_cancelled(self, scheduler, sample_slot):
        """Cancelled tours are not returned by get_buyer_tours."""
        buyer_id = "buyer_005"

        result1 = await scheduler.book_tour(buyer_id=buyer_id, property_id="prop_a", slot=sample_slot)
        result2 = await scheduler.book_tour(buyer_id=buyer_id, property_id="prop_b", slot=sample_slot)

        # Cancel the first tour
        await scheduler.cancel_tour(result1.booking_id)

        tours = await scheduler.get_buyer_tours(buyer_id)
        assert len(tours) == 1
        assert tours[0].booking_id == result2.booking_id
