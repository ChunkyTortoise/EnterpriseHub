"""
Calendar Scheduler Service for Jorge's Lead Bot.

Smart appointment scheduling system that:
- Connects to GHL calendar API and external calendar services
- Retrieves real-time availability slots
- Automatically books qualified leads (score ≥5) into Jorge's calendar
- Handles timezone conversion for Austin market
- Sends confirmation SMS to leads
- Prevents double-booking with buffer management
- 40% faster lead→appointment conversion target

Integration Points:
- GHL Calendar API for availability and booking
- Lead Scorer for qualification thresholds
- SMS service for confirmations
- Timezone handling for Austin business hours

Security Features:
- Input validation and sanitization
- Rate limiting for booking requests
- Audit logging for all appointments
- Fallback to manual scheduling if API fails
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pytz
from pydantic import BaseModel, ConfigDict, Field, field_validator

from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction, MessageType
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_client import GHLClient

logger = get_logger(__name__)

# Rancho Cucamonga timezone for Jorge's business
RC_TZ = pytz.timezone("America/Los_Angeles")
# Backward compatibility
AUSTIN_TZ = RC_TZ
UTC_TZ = pytz.UTC


class AppointmentType(str, Enum):
    """Jorge's appointment types for real estate business."""

    BUYER_CONSULTATION = "buyer_consultation"
    LISTING_APPOINTMENT = "listing_appointment"
    SELLER_CONSULTATION = "seller_consultation"
    INVESTOR_MEETING = "investor_meeting"
    PROPERTY_SHOWING = "property_showing"
    FOLLOW_UP_CALL = "follow_up_call"


class AppointmentDuration(int, Enum):
    """Standard appointment durations in minutes."""

    BUYER_CONSULTATION = 60  # 1 hour buyer consultation
    LISTING_APPOINTMENT = 90  # 1.5 hours listing presentation
    SELLER_CONSULTATION = 30  # 30 min seller consultation (WS-3 HOT flow)
    INVESTOR_MEETING = 45  # 45 min investor meeting
    PROPERTY_SHOWING = 30  # 30 min property showing
    FOLLOW_UP_CALL = 15  # 15 min follow-up call


class TimeSlot(BaseModel):
    """Available time slot for appointment booking."""

    start_time: datetime
    end_time: datetime
    duration_minutes: int
    appointment_type: AppointmentType
    timezone: str = "America/Los_Angeles"
    is_available: bool = True

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone_aware(cls, v):
        """Ensure all datetime objects are timezone-aware."""
        if v.tzinfo is None:
            raise ValueError("DateTime must be timezone-aware")
        return v

    def to_austin_time(self) -> datetime:
        """Convert start_time to Austin timezone for display."""
        if self.start_time.tzinfo != AUSTIN_TZ:
            return self.start_time.astimezone(AUSTIN_TZ)
        return self.start_time

    def format_for_lead(self) -> str:
        """Format time slot for display to leads."""
        local_time = self.start_time.astimezone(RC_TZ)
        return local_time.strftime("%A, %B %d at %I:%M %p PT")


class AppointmentBooking(BaseModel):
    """Appointment booking request and confirmation."""

    booking_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    contact_id: str
    lead_score: int
    appointment_type: AppointmentType
    time_slot: TimeSlot
    contact_info: Dict[str, Any]
    booking_timestamp: datetime = Field(default_factory=datetime.utcnow)
    confirmation_sent: bool = False
    calendar_event_id: Optional[str] = None

    @field_validator("lead_score")
    @classmethod
    def validate_score_threshold(cls, v):
        """Ensure lead score meets booking threshold."""
        if v < 5:  # 70% threshold = 5 questions answered
            raise ValueError(f"Lead score {v} below booking threshold (5)")
        return v


class BookingResult(BaseModel):
    """Result of appointment booking attempt."""

    success: bool
    booking: Optional[AppointmentBooking] = None
    error_message: Optional[str] = None
    fallback_to_manual: bool = False
    confirmation_actions: List[GHLAction] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class CalendarScheduler:
    """
    Smart calendar scheduler for Jorge's real estate lead bot.

    Automatically books qualified leads into Jorge's calendar with:
    - Real-time availability checking
    - Timezone conversion for Austin market
    - Double-booking prevention
    - SMS confirmations
    - Fallback to manual scheduling
    """
    HOT_SELLER_APPOINTMENT_TYPE = AppointmentType.SELLER_CONSULTATION
    HOT_SELLER_REQUIRED_SLOT_COUNT = 3

    def __init__(self, ghl_client: Optional[GHLClient] = None):
        """
        Initialize calendar scheduler.

        Args:
            ghl_client: Optional GHL client instance (defaults to configured client)
        """
        self.ghl_client = ghl_client or GHLClient()
        self.calendar_id = settings.ghl_calendar_id
        self.booking_threshold = 5  # 70% = 5 questions answered
        self.buffer_minutes = settings.appointment_buffer_minutes or 15
        self.business_hours = self._get_business_hours()

        # Rate limiting for booking attempts
        self._booking_attempts: Dict[str, List[datetime]] = {}
        self._max_attempts_per_hour = 3

        logger.info(
            f"Calendar scheduler initialized - Calendar ID: {self.calendar_id}, "
            f"Booking threshold: {self.booking_threshold}, Buffer: {self.buffer_minutes}min",
            extra={
                "calendar_id": self.calendar_id,
                "booking_threshold": self.booking_threshold,
                "buffer_minutes": self.buffer_minutes,
                "business_hours": self.business_hours,
            },
        )

    def _get_business_hours(self) -> Dict[str, Dict[str, str]]:
        """
        Get Jorge's business hours in Austin timezone.

        Returns:
            Dict mapping weekday names to start/end times
        """
        return {
            "monday": {"start": "09:00", "end": "18:00"},
            "tuesday": {"start": "09:00", "end": "18:00"},
            "wednesday": {"start": "09:00", "end": "18:00"},
            "thursday": {"start": "09:00", "end": "18:00"},
            "friday": {"start": "09:00", "end": "18:00"},
            "saturday": {"start": "10:00", "end": "16:00"},
            "sunday": {"start": "closed", "end": "closed"},
        }

    async def should_auto_book(
        self, lead_score: int, contact_info: Dict[str, Any], extracted_data: Dict[str, Any]
    ) -> Tuple[bool, str, AppointmentType]:
        """
        Determine if lead qualifies for automatic booking.

        Criteria:
        - Lead score ≥ 5 (70% threshold)
        - Valid contact information
        - Budget and location specified
        - Not already booked recently

        Args:
            lead_score: Lead qualification score (0-7)
            contact_info: Contact details (name, phone, email)
            extracted_data: Extracted preferences from conversation

        Returns:
            Tuple of (should_book, reason, appointment_type)
        """
        contact_id = contact_info.get("contact_id", "unknown")

        try:
            # Check score threshold (5 questions = 70%)
            if lead_score < self.booking_threshold:
                reason = f"Lead score {lead_score} below threshold ({self.booking_threshold})"
                logger.info(
                    f"Auto-booking declined for {contact_id}: {reason}",
                    extra={
                        "contact_id": contact_id,
                        "lead_score": lead_score,
                        "threshold": self.booking_threshold,
                        "reason": "score_too_low",
                    },
                )
                return False, reason, AppointmentType.BUYER_CONSULTATION

            # Check rate limiting
            if not self._check_rate_limit(contact_id):
                reason = "Rate limit exceeded - too many booking attempts"
                logger.warning(
                    f"Auto-booking declined for {contact_id}: {reason}",
                    extra={
                        "contact_id": contact_id,
                        "reason": "rate_limit_exceeded",
                        "security_event": "potential_booking_abuse",
                    },
                )
                return False, reason, AppointmentType.BUYER_CONSULTATION

            # Check required contact information
            if not contact_info.get("phone") and not contact_info.get("email"):
                reason = "Missing contact information (phone or email required)"
                logger.info(
                    f"Auto-booking declined for {contact_id}: {reason}",
                    extra={
                        "contact_id": contact_id,
                        "has_phone": bool(contact_info.get("phone")),
                        "has_email": bool(contact_info.get("email")),
                        "reason": "missing_contact_info",
                    },
                )
                return False, reason, AppointmentType.BUYER_CONSULTATION

            # Determine appointment type based on extracted data
            appointment_type = self._determine_appointment_type(extracted_data)

            # Check for urgent timeline
            timeline = extracted_data.get("timeline", "")
            is_urgent = self._is_urgent_timeline(timeline)

            reason = f"Qualified lead (score: {lead_score}, type: {appointment_type.value})"
            if is_urgent:
                reason += " - URGENT timeline"

            logger.info(
                f"Auto-booking approved for {contact_id}: {reason}",
                extra={
                    "contact_id": contact_id,
                    "lead_score": lead_score,
                    "appointment_type": appointment_type.value,
                    "is_urgent": is_urgent,
                    "reason": "qualified_for_booking",
                },
            )

            return True, reason, appointment_type

        except Exception as e:
            error_msg = f"Error evaluating auto-booking for {contact_id}: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "contact_id": contact_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "security_event": "auto_booking_evaluation_failure",
                },
                exc_info=True,
            )
            return False, error_msg, AppointmentType.BUYER_CONSULTATION

    def _check_rate_limit(self, contact_id: str) -> bool:
        """
        Check if contact has exceeded booking attempt rate limit.

        Args:
            contact_id: GHL contact ID

        Returns:
            True if within rate limit, False otherwise
        """
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Get recent attempts for this contact
        if contact_id not in self._booking_attempts:
            self._booking_attempts[contact_id] = []

        attempts = self._booking_attempts[contact_id]

        # Remove attempts older than 1 hour
        recent_attempts = [attempt for attempt in attempts if attempt > hour_ago]
        self._booking_attempts[contact_id] = recent_attempts

        # Check if under limit
        if len(recent_attempts) >= self._max_attempts_per_hour:
            logger.warning(
                f"Rate limit exceeded for contact {contact_id}: {len(recent_attempts)} attempts in last hour",
                extra={
                    "contact_id": contact_id,
                    "attempts_count": len(recent_attempts),
                    "max_allowed": self._max_attempts_per_hour,
                    "security_event": "rate_limit_exceeded",
                },
            )
            return False

        # Record this attempt
        self._booking_attempts[contact_id].append(now)
        return True

    def _determine_appointment_type(self, extracted_data: Dict[str, Any]) -> AppointmentType:
        """
        Determine appointment type based on extracted conversation data.

        Args:
            extracted_data: Extracted preferences and requirements

        Returns:
            AppointmentType appropriate for the lead
        """
        # Check for selling indicators
        home_condition = extracted_data.get("home_condition")
        motivation = extracted_data.get("motivation", "").lower()

        if home_condition or "sell" in motivation or "selling" in motivation:
            return AppointmentType.LISTING_APPOINTMENT

        # Check for investment indicators
        if "invest" in motivation or "rental" in motivation or "investment" in motivation:
            return AppointmentType.INVESTOR_MEETING

        # Default to buyer consultation
        return AppointmentType.BUYER_CONSULTATION

    def _is_urgent_timeline(self, timeline: str) -> bool:
        """
        Check if timeline indicates urgency requiring priority booking.

        Args:
            timeline: User's timeline preference

        Returns:
            True if urgent (< 1 month)
        """
        if not timeline:
            return False

        timeline_lower = timeline.lower()
        urgent_keywords = [
            "asap",
            "immediately",
            "urgent",
            "this month",
            "this week",
            "next week",
            "soon",
            "right away",
            "now",
            "quickly",
        ]

        return any(keyword in timeline_lower for keyword in urgent_keywords)

    async def get_available_slots(
        self, appointment_type: AppointmentType, days_ahead: int = 7, preferred_times: Optional[List[str]] = None
    ) -> List[TimeSlot]:
        """
        Get available appointment slots for the specified type.

        Args:
            appointment_type: Type of appointment to schedule
            days_ahead: Number of days to look ahead for availability
            preferred_times: Optional list of preferred times ("morning", "afternoon", "evening")

        Returns:
            List of available TimeSlot objects
        """
        if not self.calendar_id:
            logger.error(
                "Calendar ID not configured - cannot fetch availability",
                extra={
                    "calendar_id": self.calendar_id,
                    "appointment_type": appointment_type.value,
                    "security_event": "calendar_misconfiguration",
                },
            )
            return []

        try:
            # Calculate date range for availability check
            start_date = datetime.now(AUSTIN_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=days_ahead)

            # Fetch raw availability from GHL
            raw_slots = await self.ghl_client.get_available_slots(
                calendar_id=self.calendar_id,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                timezone="America/Los_Angeles",
            )

            # Process and filter slots
            available_slots = []
            duration = AppointmentDuration[appointment_type.name].value

            for slot_data in raw_slots:
                try:
                    # Parse slot time (handle different GHL formats)
                    slot_time_str = slot_data.get("start_time") or slot_data.get("startTime")
                    if not slot_time_str:
                        continue

                    # Parse ISO format datetime
                    slot_time = datetime.fromisoformat(slot_time_str.replace("Z", "+00:00"))

                    # Convert to Austin timezone
                    if slot_time.tzinfo != AUSTIN_TZ:
                        slot_time = slot_time.astimezone(AUSTIN_TZ)

                    # Check if slot window is during business hours, including booking buffer.
                    if not self._is_valid_slot_window(
                        slot_time, duration_minutes=duration + self.buffer_minutes
                    ):
                        continue

                    # Filter by preferred times if specified
                    if preferred_times and not self._matches_preferred_time(slot_time, preferred_times):
                        continue

                    # End time should represent the customer-facing appointment duration only.
                    end_time = slot_time + timedelta(minutes=duration)

                    time_slot = TimeSlot(
                        start_time=slot_time,
                        end_time=end_time,
                        duration_minutes=duration,
                        appointment_type=appointment_type,
                        timezone="America/Los_Angeles",
                    )

                    available_slots.append(time_slot)

                except (ValueError, KeyError) as e:
                    logger.warning(
                        f"Failed to parse slot data: {slot_data} - {str(e)}",
                        extra={"slot_data": slot_data, "error": str(e), "appointment_type": appointment_type.value},
                    )
                    continue

            # Sort by start time and limit to reasonable number
            available_slots.sort(key=lambda s: s.start_time)
            limited_slots = available_slots[:10]  # Limit to 10 options

            logger.info(
                f"Found {len(limited_slots)} available slots for {appointment_type.value}",
                extra={
                    "appointment_type": appointment_type.value,
                    "slots_found": len(available_slots),
                    "slots_returned": len(limited_slots),
                    "days_ahead": days_ahead,
                    "calendar_id": self.calendar_id,
                },
            )

            return limited_slots

        except Exception as e:
            error_msg = f"Failed to fetch available slots: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "calendar_id": self.calendar_id,
                    "appointment_type": appointment_type.value,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "security_event": "slot_fetch_failure",
                },
                exc_info=True,
            )
            return []

    async def get_hot_seller_consultation_slots(
        self, days_ahead: int = 7, preferred_times: Optional[List[str]] = None
    ) -> List[TimeSlot]:
        """
        Return exactly 3 slot options for HOT seller 30-minute consultations.

        Returns an empty list unless 3 valid options are available.
        """
        available_slots = await self.get_available_slots(
            appointment_type=self.HOT_SELLER_APPOINTMENT_TYPE,
            days_ahead=days_ahead,
            preferred_times=preferred_times,
        )
        if len(available_slots) < self.HOT_SELLER_REQUIRED_SLOT_COUNT:
            logger.info(
                "Insufficient HOT seller consultation slots for strict offer",
                extra={
                    "required_slots": self.HOT_SELLER_REQUIRED_SLOT_COUNT,
                    "available_slots": len(available_slots),
                    "appointment_type": self.HOT_SELLER_APPOINTMENT_TYPE.value,
                },
            )
            return []
        return available_slots[: self.HOT_SELLER_REQUIRED_SLOT_COUNT]

    def build_manual_scheduling_actions(self, high_priority: bool = True) -> List[GHLAction]:
        """Build deterministic actions to queue manual scheduling fallback."""
        actions = [GHLAction(type=ActionType.ADD_TAG, tag="Needs-Manual-Scheduling")]
        if high_priority:
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="High-Priority-Lead"))

        manual_workflow_id = getattr(settings, "manual_scheduling_workflow_id", None)
        if manual_workflow_id:
            actions.append(GHLAction(type=ActionType.TRIGGER_WORKFLOW, workflow_id=manual_workflow_id))

        return actions

    def get_manual_scheduling_message(self, booking_failed: bool = False) -> str:
        """Consultative, SMS-safe fallback message for manual scheduler handoff."""
        if booking_failed:
            return (
                "I had trouble locking that time in, but I have Jorge's team on it now. "
                "We'll follow up shortly with the best options."
            )
        return (
            "I'd love to get this scheduled for you. I have Jorge's team checking the calendar now "
            "and we'll follow up with the best options shortly."
        )

    def is_hot_seller_consultation_slot(self, time_slot: TimeSlot) -> bool:
        """Strict guard for WS-3 HOT seller booking contract."""
        duration_minutes = int((time_slot.end_time - time_slot.start_time).total_seconds() / 60)
        return (
            time_slot.appointment_type == self.HOT_SELLER_APPOINTMENT_TYPE
            and duration_minutes == AppointmentDuration.SELLER_CONSULTATION.value
        )

    def _is_during_business_hours(self, slot_time: datetime) -> bool:
        """
        Check if slot is during Jorge's business hours.

        Args:
            slot_time: Datetime in Austin timezone

        Returns:
            True if during business hours
        """
        weekday = slot_time.strftime("%A").lower()
        business_hours = self.business_hours.get(weekday, {})

        start_time_str = business_hours.get("start")
        end_time_str = business_hours.get("end")

        if not start_time_str or not end_time_str or start_time_str == "closed":
            return False

        try:
            # Parse business hours
            start_hour, start_min = map(int, start_time_str.split(":"))
            end_hour, end_min = map(int, end_time_str.split(":"))

            # Check if slot time is within business hours
            slot_minutes = slot_time.hour * 60 + slot_time.minute
            start_minutes = start_hour * 60 + start_min
            end_minutes = end_hour * 60 + end_min

            return start_minutes <= slot_minutes < end_minutes

        except (ValueError, AttributeError) as e:
            logger.warning(
                f"Failed to parse business hours: {start_time_str}-{end_time_str} - {str(e)}",
                extra={"weekday": weekday, "start_time": start_time_str, "end_time": end_time_str, "error": str(e)},
            )
            return False

    def _is_valid_slot_window(self, slot_start: datetime, duration_minutes: int) -> bool:
        """Validate start/end boundaries stay within business hours in local timezone."""
        if not self._is_during_business_hours(slot_start):
            return False

        slot_end = slot_start + timedelta(minutes=duration_minutes)
        if slot_end.date() != slot_start.date():
            return False

        # End is exclusive at close boundary, so validate final in-window minute.
        return self._is_during_business_hours(slot_end - timedelta(minutes=1))

    def _matches_preferred_time(self, slot_time: datetime, preferred_times: List[str]) -> bool:
        """
        Check if slot matches preferred time periods.

        Args:
            slot_time: Datetime to check
            preferred_times: List of preferred periods ("morning", "afternoon", "evening")

        Returns:
            True if slot matches preferences
        """
        hour = slot_time.hour

        time_periods = {
            "morning": range(8, 12),  # 8 AM - 12 PM
            "afternoon": range(12, 17),  # 12 PM - 5 PM
            "evening": range(17, 20),  # 5 PM - 8 PM
        }

        for preferred in preferred_times:
            if preferred.lower() in time_periods:
                if hour in time_periods[preferred.lower()]:
                    return True

        return False

    async def book_appointment(
        self,
        contact_id: str,
        contact_info: Dict[str, Any],
        time_slot: TimeSlot,
        lead_score: int,
        extracted_data: Dict[str, Any],
    ) -> BookingResult:
        """
        Book an appointment for a qualified lead.

        Args:
            contact_id: GHL contact ID
            contact_info: Contact details
            time_slot: Selected time slot
            lead_score: Lead qualification score
            extracted_data: Extracted conversation preferences

        Returns:
            BookingResult with success status and details
        """
        booking_id = str(uuid.uuid4())

        logger.info(
            f"Starting appointment booking for {contact_id}",
            extra={
                "booking_id": booking_id,
                "contact_id": contact_id,
                "appointment_type": time_slot.appointment_type.value,
                "appointment_time": time_slot.start_time.isoformat(),
                "lead_score": lead_score,
            },
        )

        try:
            # Create booking record
            booking = AppointmentBooking(
                booking_id=booking_id,
                contact_id=contact_id,
                lead_score=lead_score,
                appointment_type=time_slot.appointment_type,
                time_slot=time_slot,
                contact_info=contact_info,
            )

            # Create appointment in GHL calendar
            appointment_title = self._generate_appointment_title(
                contact_info, time_slot.appointment_type, extracted_data
            )

            calendar_response = await self.ghl_client.create_appointment(
                contact_id=contact_id,
                calendar_id=self.calendar_id,
                start_time=time_slot.start_time.isoformat(),
                title=appointment_title,
                assigned_user_id=settings.jorge_user_id,
            )

            # Update booking with calendar event ID
            booking.calendar_event_id = calendar_response.get("id")

            # Generate confirmation actions
            confirmation_actions = await self._generate_confirmation_actions(booking, contact_info, extracted_data)

            # Mark confirmation as sent
            booking.confirmation_sent = True

            logger.info(
                f"Successfully booked appointment {booking_id}",
                extra={
                    "booking_id": booking_id,
                    "contact_id": contact_id,
                    "calendar_event_id": booking.calendar_event_id,
                    "appointment_type": time_slot.appointment_type.value,
                    "appointment_time": time_slot.start_time.isoformat(),
                    "confirmation_actions": len(confirmation_actions),
                    "security_event": "appointment_booked_successfully",
                },
            )

            return BookingResult(success=True, booking=booking, confirmation_actions=confirmation_actions)

        except Exception as e:
            error_msg = f"Failed to book appointment: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "booking_id": booking_id,
                    "contact_id": contact_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "security_event": "appointment_booking_failure",
                },
                exc_info=True,
            )

            # Check if we should fallback to manual scheduling
            fallback_to_manual = self._should_fallback_to_manual(e)

            return BookingResult(
                success=False, error_message=error_msg, fallback_to_manual=fallback_to_manual, confirmation_actions=[]
            )

    def _generate_appointment_title(
        self, contact_info: Dict[str, Any], appointment_type: AppointmentType, extracted_data: Dict[str, Any]
    ) -> str:
        """
        Generate descriptive appointment title.

        Args:
            contact_info: Contact details
            appointment_type: Type of appointment
            extracted_data: Extracted preferences

        Returns:
            Formatted appointment title
        """
        name = f"{contact_info.get('first_name', '')} {contact_info.get('last_name', '')}".strip()
        if not name:
            name = "Lead"

        type_titles = {
            AppointmentType.BUYER_CONSULTATION: "Buyer Consultation",
            AppointmentType.LISTING_APPOINTMENT: "Listing Appointment",
            AppointmentType.SELLER_CONSULTATION: "Seller Consultation (30 min)",
            AppointmentType.INVESTOR_MEETING: "Investor Meeting",
            AppointmentType.PROPERTY_SHOWING: "Property Showing",
            AppointmentType.FOLLOW_UP_CALL: "Follow-up Call",
        }

        base_title = f"{type_titles[appointment_type]} - {name}"

        # Add relevant details
        details = []
        budget = extracted_data.get("budget")
        if budget:
            details.append(f"Budget: ${budget:,}")

        location = extracted_data.get("location")
        if location:
            if isinstance(location, list):
                details.append(f"Area: {', '.join(location[:2])}")  # Limit to 2 areas
            else:
                details.append(f"Area: {location}")

        if details:
            base_title += f" ({' | '.join(details)})"

        return base_title

    async def _generate_confirmation_actions(
        self, booking: AppointmentBooking, contact_info: Dict[str, Any], extracted_data: Dict[str, Any]
    ) -> List[GHLAction]:
        """
        Generate GHL actions for appointment confirmation.

        Args:
            booking: Appointment booking details
            contact_info: Contact information
            extracted_data: Extracted conversation data

        Returns:
            List of GHLAction objects for confirmation
        """
        actions = []

        # Generate confirmation message
        confirmation_message = self._generate_confirmation_message(booking, contact_info)

        # Send SMS confirmation
        actions.append(GHLAction(type=ActionType.SEND_MESSAGE, message=confirmation_message, channel=MessageType.SMS))

        if contact_info.get("email"):
            actions.append(
                GHLAction(
                    type=ActionType.SEND_MESSAGE,
                    message=self._generate_email_confirmation_message(booking, contact_info),
                    channel=MessageType.EMAIL,
                )
            )

        # Add appointment-related tags
        actions.append(GHLAction(type=ActionType.ADD_TAG, tag=f"Appointment-{booking.appointment_type.value.title()}"))

        actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Auto-Booked"))

        # Add urgent tag if timeline is urgent
        timeline = extracted_data.get("timeline", "")
        if self._is_urgent_timeline(timeline):
            actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Urgent-Timeline"))

        # Update appointment details in custom fields
        if settings.custom_field_appointment_time:
            formatted_time = booking.time_slot.format_for_lead()
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_appointment_time,
                    value=formatted_time,
                )
            )

        if settings.custom_field_appointment_type:
            actions.append(
                GHLAction(
                    type=ActionType.UPDATE_CUSTOM_FIELD,
                    field=settings.custom_field_appointment_type,
                    value=booking.appointment_type.value,
                )
            )

        return actions

    def _generate_confirmation_message(self, booking: AppointmentBooking, contact_info: Dict[str, Any]) -> str:
        """
        Generate SMS confirmation message for the appointment.

        Args:
            booking: Appointment booking details
            contact_info: Contact information

        Returns:
            Formatted confirmation message
        """
        name = contact_info.get("first_name", "there")
        appointment_time = booking.time_slot.format_for_lead()

        type_messages = {
            AppointmentType.BUYER_CONSULTATION: "buyer consultation",
            AppointmentType.LISTING_APPOINTMENT: "listing appointment",
            AppointmentType.SELLER_CONSULTATION: "30 minute seller consultation",
            AppointmentType.INVESTOR_MEETING: "investment discussion",
            AppointmentType.PROPERTY_SHOWING: "property showing",
            AppointmentType.FOLLOW_UP_CALL: "follow-up call",
        }

        appointment_description = type_messages[booking.appointment_type]

        message = f"""Hi {name}! 🏡

Great news - I've scheduled your {appointment_description} with Jorge for {appointment_time}.

Jorge will call you at this number to confirm details and answer any questions.

What to expect:
• Jorge will review your preferences
• Discuss next steps for your property goals
• Answer all your questions

Looking forward to helping you with your real estate needs!

- Jorge's Team
📱 Reply RESCHEDULE if you need to change the time"""

        return message

    def _generate_email_confirmation_message(self, booking: AppointmentBooking, contact_info: Dict[str, Any]) -> str:
        """Generate email confirmation copy for the booked appointment."""
        name = contact_info.get("first_name", "there")
        appointment_time = booking.time_slot.format_for_lead()

        type_messages = {
            AppointmentType.BUYER_CONSULTATION: "buyer consultation",
            AppointmentType.LISTING_APPOINTMENT: "listing appointment",
            AppointmentType.SELLER_CONSULTATION: "30 minute seller consultation",
            AppointmentType.INVESTOR_MEETING: "investment discussion",
            AppointmentType.PROPERTY_SHOWING: "property showing",
            AppointmentType.FOLLOW_UP_CALL: "follow-up call",
        }

        appointment_description = type_messages[booking.appointment_type]
        return (
            f"Hi {name}, your {appointment_description} with Jorge is confirmed for {appointment_time}. "
            "Reply RESCHEDULE if you need a different time."
        )

    def _should_fallback_to_manual(self, error: Exception) -> bool:
        """
        Determine if booking failure should trigger manual scheduling fallback.

        Args:
            error: Exception that caused booking failure

        Returns:
            True if should fallback to manual scheduling
        """
        # Fallback conditions
        fallback_errors = [
            "calendar not found",
            "no availability",
            "double booking",
            "timeout",
            "rate limit",
            "api error",
        ]

        error_str = str(error).lower()
        return any(fallback_error in error_str for fallback_error in fallback_errors)

    async def suggest_appointment_times(
        self,
        contact_id: str,
        appointment_type: AppointmentType,
        preferred_times: Optional[List[str]] = None,
        days_ahead: int = 5,
    ) -> List[str]:
        """
        Generate appointment time suggestions for AI responses.

        Args:
            contact_id: GHL contact ID
            appointment_type: Type of appointment
            preferred_times: Optional preferred time periods
            days_ahead: Days to look ahead for availability

        Returns:
            List of formatted time suggestions for AI to offer
        """
        try:
            available_slots = await self.get_available_slots(
                appointment_type=appointment_type, days_ahead=days_ahead, preferred_times=preferred_times
            )

            if not available_slots:
                logger.warning(
                    f"No available slots found for {contact_id}",
                    extra={
                        "contact_id": contact_id,
                        "appointment_type": appointment_type.value,
                        "days_ahead": days_ahead,
                    },
                )
                return ["I need to check my calendar and get back to you with available times"]

            # Format top 3 suggestions for AI to offer
            suggestions = []
            for slot in available_slots[:3]:
                formatted_time = slot.format_for_lead()
                suggestions.append(formatted_time)

            logger.info(
                f"Generated {len(suggestions)} time suggestions for {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "appointment_type": appointment_type.value,
                    "suggestions_count": len(suggestions),
                },
            )

            return suggestions

        except Exception as e:
            logger.error(
                f"Failed to generate time suggestions for {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e), "error_type": type(e).__name__},
                exc_info=True,
            )
            return ["Let me check my calendar and get back to you with some available times"]

    async def handle_appointment_request(
        self,
        contact_id: str,
        contact_info: Dict[str, Any],
        lead_score: int,
        extracted_data: Dict[str, Any],
        message_content: str,
    ) -> Tuple[bool, str, List[GHLAction]]:
        """
        Handle incoming appointment booking request from qualified lead.

        This is the main entry point for appointment scheduling logic.

        Args:
            contact_id: GHL contact ID
            contact_info: Contact details
            lead_score: Lead qualification score
            extracted_data: Extracted conversation preferences
            message_content: Latest message from lead

        Returns:
            Tuple of (booking_attempted, response_message, actions)
        """
        try:
            # Check if lead qualifies for auto-booking
            should_book, reason, appointment_type = await self.should_auto_book(
                lead_score, contact_info, extracted_data
            )

            if not should_book:
                logger.info(
                    f"Auto-booking not triggered for {contact_id}: {reason}",
                    extra={"contact_id": contact_id, "lead_score": lead_score, "reason": reason},
                )
                return False, "", []

            # Get available slots
            available_slots = await self.get_available_slots(appointment_type=appointment_type, days_ahead=7)

            if not available_slots:
                # No availability - fallback to manual scheduling
                fallback_message = self.get_manual_scheduling_message(booking_failed=False)
                fallback_actions = self.build_manual_scheduling_actions(high_priority=True)
                return True, fallback_message, fallback_actions

            # Auto-book the first available slot
            first_slot = available_slots[0]
            booking_result = await self.book_appointment(
                contact_id=contact_id,
                contact_info=contact_info,
                time_slot=first_slot,
                lead_score=lead_score,
                extracted_data=extracted_data,
            )

            if booking_result.success:
                # Successful booking
                name = contact_info.get("first_name", "there")
                appointment_time = first_slot.format_for_lead()

                confirmation_channel_text = (
                    "You'll receive a confirmation text and email shortly!"
                    if contact_info.get("email")
                    else "You'll receive a confirmation text shortly!"
                )
                response_message = (
                    f"Perfect! I've scheduled a time for Jorge to call you on {appointment_time}. "
                    f"He'll reach out to discuss your property goals and answer any questions you have. "
                    f"{confirmation_channel_text}"
                )

                return True, response_message, booking_result.confirmation_actions

            elif booking_result.fallback_to_manual:
                # Booking failed but should try manual scheduling
                response_message = self.get_manual_scheduling_message(booking_failed=True)
                fallback_actions = self.build_manual_scheduling_actions(high_priority=True)
                fallback_actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Booking-Failed-Manual-Needed"))

                return True, response_message, fallback_actions

            else:
                # Booking failed - log error but don't expose to lead
                logger.error(
                    f"Appointment booking failed for {contact_id}: {booking_result.error_message}",
                    extra={
                        "contact_id": contact_id,
                        "error": booking_result.error_message,
                        "security_event": "booking_system_failure",
                    },
                )

                response_message = self.get_manual_scheduling_message(booking_failed=True)
                fallback_actions = self.build_manual_scheduling_actions(high_priority=True)
                fallback_actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Booking-System-Error"))
                return True, response_message, fallback_actions

        except Exception as e:
            logger.error(
                f"Critical error in appointment request handling for {contact_id}: {str(e)}",
                extra={
                    "contact_id": contact_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "security_event": "appointment_handler_critical_failure",
                },
                exc_info=True,
            )

            # Graceful fallback - don't expose errors to lead
            return False, "", []


# Global instance for singleton pattern
_scheduler_instance: Optional[CalendarScheduler] = None


def get_smart_scheduler(ghl_client: Optional[GHLClient] = None) -> CalendarScheduler:
    """
    Get or create a global instance of CalendarScheduler.

    Returns:
        CalendarScheduler instance
    """
    if ghl_client is not None:
        return CalendarScheduler(ghl_client)

    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CalendarScheduler()
    return _scheduler_instance
