import pytest
pytestmark = pytest.mark.integration

"""
Tests for Calendar Scheduler Service.

Tests the smart appointment scheduling system for Jorge's lead bot including:
- Lead qualification for auto-booking
- Calendar integration with GHL
- Timezone handling for Rancho Cucamonga market
- SMS confirmations
- Error handling and fallbacks
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytz

from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction, MessageType
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.calendar_scheduler import (

    RC_TZ,
    AppointmentBooking,
    AppointmentDuration,
    AppointmentType,
    BookingResult,
    CalendarScheduler,
    TimeSlot,
)


@pytest.fixture
def mock_ghl_client():
    """Mock GHL client for testing."""
    client = AsyncMock()

    # Mock calendar availability
    # Times in UTC that fall within LA business hours (9-18 PT = 17:00-02:00+1 UTC in winter)
    # Jan 17, 2024 is a Wednesday
    client.get_available_slots.return_value = [
        {"start_time": "2024-01-17T18:00:00Z", "end_time": "2024-01-17T19:00:00Z"},  # 10:00 AM PT
        {"start_time": "2024-01-17T21:30:00Z", "end_time": "2024-01-17T22:30:00Z"},  # 1:30 PM PT
        {"start_time": "2024-01-18T19:00:00Z", "end_time": "2024-01-18T20:00:00Z"},  # 11:00 AM PT (Thu)
    ]

    # Mock appointment creation
    client.create_appointment.return_value = {
        "id": "apt_123456789",
        "status": "confirmed",
        "startTime": "2024-01-17T14:00:00Z",
        "contactId": "contact_123",
    }

    return client


@pytest.fixture
def calendar_scheduler(mock_ghl_client):
    """Calendar scheduler instance for testing."""
    with patch("ghl_real_estate_ai.services.calendar_scheduler.settings") as mock_settings:
        mock_settings.ghl_calendar_id = "cal_jorge_123"
        mock_settings.appointment_buffer_minutes = 15
        mock_settings.jorge_user_id = "user_jorge_456"

        scheduler = CalendarScheduler(ghl_client=mock_ghl_client)
        return scheduler


@pytest.fixture
def qualified_lead_data():
    """Sample qualified lead data for testing."""
    return {
        "contact_info": {
            "contact_id": "contact_123",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "email": "john.doe@example.com",
        },
        "extracted_data": {
            "budget": 450000,
            "location": ["Rancho Cucamonga", "Round Rock"],
            "timeline": "next month",
            "bedrooms": 3,
            "bathrooms": 2,
            "motivation": "buying first home",
            "financing": "pre-approved",
        },
        "lead_score": 6,  # Above threshold (5)
        "message_content": "I'm ready to start looking at homes",
    }


@pytest.fixture
def unqualified_lead_data():
    """Sample unqualified lead data for testing."""
    return {
        "contact_info": {
            "contact_id": "contact_456",
            "first_name": "Jane",
            "last_name": "Smith",
            "phone": "+1987654321",
            "email": "jane.smith@example.com",
        },
        "extracted_data": {"location": ["Rancho Cucamonga"]},
        "lead_score": 3,  # Below threshold (5)
        "message_content": "I'm thinking about buying",
    }


class TestCalendarScheduler:
    """Test suite for Calendar Scheduler functionality."""

    @pytest.mark.asyncio
    async def test_initialization(self, mock_ghl_client):
        """Test calendar scheduler initialization."""
        scheduler = CalendarScheduler(ghl_client=mock_ghl_client)

        assert scheduler.ghl_client == mock_ghl_client
        assert scheduler.booking_threshold == 5
        assert scheduler.buffer_minutes == 15
        assert "monday" in scheduler.business_hours
        assert scheduler.business_hours["sunday"]["start"] == "closed"

    @pytest.mark.asyncio
    async def test_should_auto_book_qualified_lead(self, calendar_scheduler, qualified_lead_data):
        """Test auto-booking logic for qualified lead."""
        should_book, reason, appointment_type = await calendar_scheduler.should_auto_book(
            lead_score=qualified_lead_data["lead_score"],
            contact_info=qualified_lead_data["contact_info"],
            extracted_data=qualified_lead_data["extracted_data"],
        )

        assert should_book is True
        assert "Qualified lead" in reason
        assert appointment_type == AppointmentType.BUYER_CONSULTATION

    @pytest.mark.asyncio
    async def test_should_auto_book_unqualified_lead(self, calendar_scheduler, unqualified_lead_data):
        """Test auto-booking logic for unqualified lead."""
        should_book, reason, appointment_type = await calendar_scheduler.should_auto_book(
            lead_score=unqualified_lead_data["lead_score"],
            contact_info=unqualified_lead_data["contact_info"],
            extracted_data=unqualified_lead_data["extracted_data"],
        )

        assert should_book is False
        assert "below threshold" in reason.lower()

    @pytest.mark.asyncio
    async def test_should_auto_book_missing_contact_info(self, calendar_scheduler):
        """Test auto-booking with missing contact information."""
        contact_info = {
            "contact_id": "contact_123",
            "first_name": "John",
            # Missing phone and email
        }

        should_book, reason, _ = await calendar_scheduler.should_auto_book(
            lead_score=6, contact_info=contact_info, extracted_data={"budget": 400000}
        )

        assert should_book is False
        assert "Missing contact information" in reason

    @pytest.mark.asyncio
    async def test_determine_appointment_type_buyer(self, calendar_scheduler):
        """Test appointment type determination for buyer."""
        extracted_data = {"motivation": "looking to buy my first home", "budget": 350000}

        appointment_type = calendar_scheduler._determine_appointment_type(extracted_data)
        assert appointment_type == AppointmentType.BUYER_CONSULTATION

    @pytest.mark.asyncio
    async def test_determine_appointment_type_seller(self, calendar_scheduler):
        """Test appointment type determination for seller."""
        extracted_data = {"motivation": "need to sell my house quickly", "home_condition": "excellent"}

        appointment_type = calendar_scheduler._determine_appointment_type(extracted_data)
        assert appointment_type == AppointmentType.LISTING_APPOINTMENT

    @pytest.mark.asyncio
    async def test_determine_appointment_type_investor(self, calendar_scheduler):
        """Test appointment type determination for investor."""
        extracted_data = {"motivation": "looking for rental investment properties", "budget": 200000}

        appointment_type = calendar_scheduler._determine_appointment_type(extracted_data)
        assert appointment_type == AppointmentType.INVESTOR_MEETING

    @pytest.mark.asyncio
    async def test_is_urgent_timeline(self, calendar_scheduler):
        """Test urgent timeline detection."""
        urgent_timelines = ["ASAP", "this month", "immediately", "next week", "urgent"]

        non_urgent_timelines = ["next year", "6 months", "eventually", "when I'm ready"]

        for timeline in urgent_timelines:
            assert calendar_scheduler._is_urgent_timeline(timeline) is True

        for timeline in non_urgent_timelines:
            assert calendar_scheduler._is_urgent_timeline(timeline) is False

    @pytest.mark.asyncio
    async def test_rate_limiting(self, calendar_scheduler):
        """Test rate limiting for booking attempts."""
        contact_id = "contact_rate_test"

        # First 3 attempts should pass
        for i in range(3):
            assert calendar_scheduler._check_rate_limit(contact_id) is True

        # 4th attempt should fail
        assert calendar_scheduler._check_rate_limit(contact_id) is False

    def test_is_during_business_hours(self, calendar_scheduler):
        """Test business hours validation."""
        # Monday 10 AM Rancho Cucamonga time (during business hours)
        monday_10am = datetime(2024, 1, 15, 10, 0, 0, tzinfo=RC_TZ)
        assert calendar_scheduler._is_during_business_hours(monday_10am) is True

        # Monday 8 AM Rancho Cucamonga time (before business hours)
        monday_8am = datetime(2024, 1, 15, 8, 0, 0, tzinfo=RC_TZ)
        assert calendar_scheduler._is_during_business_hours(monday_8am) is False

        # Sunday (closed)
        sunday_2pm = datetime(2024, 1, 14, 14, 0, 0, tzinfo=RC_TZ)
        assert calendar_scheduler._is_during_business_hours(sunday_2pm) is False

    def test_matches_preferred_time(self, calendar_scheduler):
        """Test preferred time matching."""
        # Morning time (10 AM)
        morning_time = datetime(2024, 1, 15, 10, 0, 0, tzinfo=RC_TZ)
        assert calendar_scheduler._matches_preferred_time(morning_time, ["morning"]) is True
        assert calendar_scheduler._matches_preferred_time(morning_time, ["afternoon"]) is False

        # Afternoon time (3 PM)
        afternoon_time = datetime(2024, 1, 15, 15, 0, 0, tzinfo=RC_TZ)
        assert calendar_scheduler._matches_preferred_time(afternoon_time, ["afternoon"]) is True
        assert calendar_scheduler._matches_preferred_time(afternoon_time, ["evening"]) is False

    @pytest.mark.asyncio
    async def test_get_available_slots(self, calendar_scheduler, mock_ghl_client):
        """Test fetching available appointment slots."""
        slots = await calendar_scheduler.get_available_slots(
            appointment_type=AppointmentType.BUYER_CONSULTATION, days_ahead=7
        )

        assert len(slots) > 0
        assert all(isinstance(slot, TimeSlot) for slot in slots)
        assert all(slot.appointment_type == AppointmentType.BUYER_CONSULTATION for slot in slots)

        # Verify GHL client was called
        mock_ghl_client.get_available_slots.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_slots_no_calendar_id(self, mock_ghl_client):
        """Test handling missing calendar ID."""
        with patch("ghl_real_estate_ai.services.calendar_scheduler.settings") as mock_settings:
            mock_settings.ghl_calendar_id = None

            scheduler = CalendarScheduler(ghl_client=mock_ghl_client)
            slots = await scheduler.get_available_slots(appointment_type=AppointmentType.BUYER_CONSULTATION)

            assert slots == []
            # Should not call GHL client
            mock_ghl_client.get_available_slots.assert_not_called()

    @pytest.mark.asyncio
    async def test_book_appointment_success(self, calendar_scheduler, qualified_lead_data, mock_ghl_client):
        """Test successful appointment booking."""
        # Create a time slot
        start_time = datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ)
        time_slot = TimeSlot(
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        result = await calendar_scheduler.book_appointment(
            contact_id=qualified_lead_data["contact_info"]["contact_id"],
            contact_info=qualified_lead_data["contact_info"],
            time_slot=time_slot,
            lead_score=qualified_lead_data["lead_score"],
            extracted_data=qualified_lead_data["extracted_data"],
        )

        assert result.success is True
        assert result.booking is not None
        assert result.booking.contact_id == qualified_lead_data["contact_info"]["contact_id"]
        assert result.booking.calendar_event_id == "apt_123456789"
        assert len(result.confirmation_actions) > 0

        # Verify GHL client was called
        mock_ghl_client.create_appointment.assert_called_once()

    @pytest.mark.asyncio
    async def test_book_appointment_failure(self, calendar_scheduler, qualified_lead_data, mock_ghl_client):
        """Test appointment booking failure handling."""
        # Mock GHL client to fail
        mock_ghl_client.create_appointment.side_effect = Exception("Calendar API error")

        start_time = datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ)
        time_slot = TimeSlot(
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        result = await calendar_scheduler.book_appointment(
            contact_id=qualified_lead_data["contact_info"]["contact_id"],
            contact_info=qualified_lead_data["contact_info"],
            time_slot=time_slot,
            lead_score=qualified_lead_data["lead_score"],
            extracted_data=qualified_lead_data["extracted_data"],
        )

        assert result.success is False
        assert "Calendar API error" in result.error_message
        assert result.fallback_to_manual is True  # "Calendar API error" contains "api error", triggers fallback

    def test_should_fallback_to_manual(self, calendar_scheduler):
        """Test fallback to manual scheduling logic."""
        # Errors that should trigger fallback
        fallback_errors = [
            Exception("calendar not found"),
            Exception("No availability"),
            Exception("Double booking detected"),
            Exception("Timeout error"),
            Exception("Rate limit exceeded"),
        ]

        for error in fallback_errors:
            assert calendar_scheduler._should_fallback_to_manual(error) is True

        # Error that should not trigger fallback
        non_fallback_error = Exception("Invalid contact ID")
        assert calendar_scheduler._should_fallback_to_manual(non_fallback_error) is False

    @pytest.mark.asyncio
    async def test_suggest_appointment_times(self, calendar_scheduler, mock_ghl_client):
        """Test appointment time suggestions for AI responses."""
        suggestions = await calendar_scheduler.suggest_appointment_times(
            contact_id="contact_123", appointment_type=AppointmentType.BUYER_CONSULTATION, days_ahead=5
        )

        assert len(suggestions) > 0
        assert all(isinstance(suggestion, str) for suggestion in suggestions)
        # Should include day, date, and time
        assert any("at" in suggestion for suggestion in suggestions)

    @pytest.mark.asyncio
    async def test_suggest_appointment_times_no_availability(self, calendar_scheduler, mock_ghl_client):
        """Test appointment suggestions when no slots available."""
        # Mock no availability
        mock_ghl_client.get_available_slots.return_value = []

        suggestions = await calendar_scheduler.suggest_appointment_times(
            contact_id="contact_123", appointment_type=AppointmentType.BUYER_CONSULTATION
        )

        assert len(suggestions) == 1
        assert "check my calendar" in suggestions[0]

    def test_generate_appointment_title(self, calendar_scheduler):
        """Test appointment title generation."""
        contact_info = {"first_name": "John", "last_name": "Doe"}
        extracted_data = {"budget": 450000, "location": ["Rancho Cucamonga", "Round Rock"]}

        title = calendar_scheduler._generate_appointment_title(
            contact_info, AppointmentType.BUYER_CONSULTATION, extracted_data
        )

        assert "Buyer Consultation - John Doe" in title
        assert "$450,000" in title
        assert "Rancho Cucamonga" in title

    @pytest.mark.asyncio
    async def test_generate_confirmation_actions(self, calendar_scheduler):
        """Test confirmation action generation."""
        booking = AppointmentBooking(
            contact_id="contact_123",
            lead_score=6,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ),
                end_time=datetime(2024, 1, 17, 15, 0, 0, tzinfo=RC_TZ),
                duration_minutes=60,
                appointment_type=AppointmentType.BUYER_CONSULTATION,
            ),
            contact_info={"first_name": "John", "last_name": "Doe"},
        )

        contact_info = {"first_name": "John", "last_name": "Doe"}
        extracted_data = {"timeline": "urgent"}

        actions = await calendar_scheduler._generate_confirmation_actions(booking, contact_info, extracted_data)

        assert len(actions) > 0

        # Check for SMS confirmation
        sms_actions = [a for a in actions if a.type == ActionType.SEND_MESSAGE]
        assert len(sms_actions) == 1
        assert sms_actions[0].channel == MessageType.SMS
        assert "John" in sms_actions[0].message

        # Check for tags
        tag_actions = [a for a in actions if a.type == ActionType.ADD_TAG]
        tag_names = [a.tag for a in tag_actions]
        assert "Appointment-Buyer_Consultation" in tag_names
        assert "Auto-Booked" in tag_names
        assert "Urgent-Timeline" in tag_names  # Because timeline is urgent

    def test_generate_confirmation_message(self, calendar_scheduler):
        """Test SMS confirmation message generation."""
        booking = AppointmentBooking(
            contact_id="contact_123",
            lead_score=6,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
            time_slot=TimeSlot(
                start_time=datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ),
                end_time=datetime(2024, 1, 17, 15, 0, 0, tzinfo=RC_TZ),
                duration_minutes=60,
                appointment_type=AppointmentType.BUYER_CONSULTATION,
            ),
            contact_info={"first_name": "John", "last_name": "Doe"},
        )

        contact_info = {"first_name": "John", "last_name": "Doe"}

        message = calendar_scheduler._generate_confirmation_message(booking, contact_info)

        assert "Hi John" in message
        assert "buyer consultation" in message
        assert "Jorge" in message
        assert "Wednesday, January 17" in message
        assert "2:00 PM CT" in message
        assert "RESCHEDULE" in message

    @pytest.mark.asyncio
    async def test_handle_appointment_request_qualified_lead(
        self, calendar_scheduler, qualified_lead_data, mock_ghl_client
    ):
        """Test full appointment request handling for qualified lead."""
        booking_attempted, response_message, actions = await calendar_scheduler.handle_appointment_request(
            contact_id=qualified_lead_data["contact_info"]["contact_id"],
            contact_info=qualified_lead_data["contact_info"],
            lead_score=qualified_lead_data["lead_score"],
            extracted_data=qualified_lead_data["extracted_data"],
            message_content=qualified_lead_data["message_content"],
        )

        assert booking_attempted is True
        assert "scheduled" in response_message.lower() or "check" in response_message.lower()
        assert len(actions) > 0

        # Should have called GHL client
        mock_ghl_client.get_available_slots.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_appointment_request_unqualified_lead(self, calendar_scheduler, unqualified_lead_data):
        """Test appointment request handling for unqualified lead."""
        booking_attempted, response_message, actions = await calendar_scheduler.handle_appointment_request(
            contact_id=unqualified_lead_data["contact_info"]["contact_id"],
            contact_info=unqualified_lead_data["contact_info"],
            lead_score=unqualified_lead_data["lead_score"],
            extracted_data=unqualified_lead_data["extracted_data"],
            message_content=unqualified_lead_data["message_content"],
        )

        assert booking_attempted is False
        assert response_message == ""
        assert actions == []


class TestTimeSlot:
    """Test suite for TimeSlot model."""

    def test_time_slot_creation(self):
        """Test TimeSlot creation and validation."""
        start_time = datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ)
        end_time = start_time + timedelta(minutes=60)

        slot = TimeSlot(
            start_time=start_time,
            end_time=end_time,
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        assert slot.start_time == start_time
        assert slot.end_time == end_time
        assert slot.duration_minutes == 60
        assert slot.appointment_type == AppointmentType.BUYER_CONSULTATION
        assert slot.timezone == "America/Los_Angeles"
        assert slot.is_available is True

    def test_time_slot_timezone_validation(self):
        """Test that timezone-naive datetimes are rejected."""
        with pytest.raises(ValueError, match="timezone-aware"):
            TimeSlot(
                start_time=datetime(2024, 1, 17, 14, 0, 0),  # No timezone
                end_time=datetime(2024, 1, 17, 15, 0, 0),  # No timezone
                duration_minutes=60,
                appointment_type=AppointmentType.BUYER_CONSULTATION,
            )

    def test_time_slot_to_rancho_cucamonga_time(self):
        """Test timezone conversion to Rancho Cucamonga time."""
        # UTC time
        utc_time = datetime(2024, 1, 17, 20, 0, 0, tzinfo=pytz.UTC)
        end_time = utc_time + timedelta(minutes=60)

        slot = TimeSlot(
            start_time=utc_time,
            end_time=end_time,
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        rancho_cucamonga_time = slot.to_rancho_cucamonga_time()

        # UTC 20:00 should be 12:00 PT (PST in January, -8 hours)
        assert rancho_cucamonga_time.hour == 12
        assert str(rancho_cucamonga_time.tzinfo) == str(RC_TZ)

    def test_time_slot_format_for_lead(self):
        """Test time slot formatting for lead display."""
        rancho_cucamonga_time = datetime(2024, 1, 17, 14, 30, 0, tzinfo=RC_TZ)
        end_time = rancho_cucamonga_time + timedelta(minutes=60)

        slot = TimeSlot(
            start_time=rancho_cucamonga_time,
            end_time=end_time,
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        formatted = slot.format_for_lead()

        assert "Wednesday, January 17" in formatted
        assert "2:30 PM CT" in formatted


class TestAppointmentBooking:
    """Test suite for AppointmentBooking model."""

    def test_appointment_booking_creation(self):
        """Test AppointmentBooking creation."""
        start_time = datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ)
        time_slot = TimeSlot(
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        booking = AppointmentBooking(
            contact_id="contact_123",
            lead_score=6,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
            time_slot=time_slot,
            contact_info={"first_name": "John", "last_name": "Doe"},
        )

        assert booking.contact_id == "contact_123"
        assert booking.lead_score == 6
        assert booking.appointment_type == AppointmentType.BUYER_CONSULTATION
        assert booking.time_slot == time_slot
        assert isinstance(booking.booking_id, str)
        assert booking.confirmation_sent is False

    def test_appointment_booking_score_validation(self):
        """Test lead score validation in AppointmentBooking."""
        start_time = datetime(2024, 1, 17, 14, 0, 0, tzinfo=RC_TZ)
        time_slot = TimeSlot(
            start_time=start_time,
            end_time=start_time + timedelta(minutes=60),
            duration_minutes=60,
            appointment_type=AppointmentType.BUYER_CONSULTATION,
        )

        with pytest.raises(ValueError, match="below booking threshold"):
            AppointmentBooking(
                contact_id="contact_123",
                lead_score=3,  # Below threshold
                appointment_type=AppointmentType.BUYER_CONSULTATION,
                time_slot=time_slot,
                contact_info={"first_name": "John", "last_name": "Doe"},
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])