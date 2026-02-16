from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
import pytz

from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.services.calendar_scheduler import (
    AppointmentBooking,
    AppointmentType,
    CalendarScheduler,
    TimeSlot,
)


@pytest.fixture
def ws3_scheduler():
    mock_ghl_client = AsyncMock()
    with patch("ghl_real_estate_ai.services.calendar_scheduler.settings") as mock_settings:
        mock_settings.ghl_calendar_id = "cal_ws3"
        mock_settings.appointment_buffer_minutes = 15
        mock_settings.jorge_user_id = "user_ws3"
        mock_settings.manual_scheduling_workflow_id = "wf_manual_ws3"
        mock_settings.custom_field_appointment_time = None
        mock_settings.custom_field_appointment_type = None
        yield CalendarScheduler(ghl_client=mock_ghl_client), mock_ghl_client


def _slot(start: datetime, minutes: int = 30, appointment_type: AppointmentType = AppointmentType.SELLER_CONSULTATION):
    return TimeSlot(
        start_time=start,
        end_time=start + timedelta(minutes=minutes),
        duration_minutes=minutes,
        appointment_type=appointment_type,
    )


@pytest.mark.asyncio
async def test_ws3_get_hot_seller_slots_returns_exactly_three(ws3_scheduler):
    scheduler, _ = ws3_scheduler
    tz = pytz.timezone("America/Los_Angeles")
    base = tz.localize(datetime(2026, 2, 17, 10, 0))
    slots = [_slot(base + timedelta(hours=i)) for i in range(4)]
    scheduler.get_available_slots = AsyncMock(return_value=slots)

    result = await scheduler.get_hot_seller_consultation_slots(days_ahead=7)

    assert len(result) == 3
    assert all(slot.appointment_type == AppointmentType.SELLER_CONSULTATION for slot in result)


@pytest.mark.asyncio
async def test_ws3_get_hot_seller_slots_requires_three(ws3_scheduler):
    scheduler, _ = ws3_scheduler
    tz = pytz.timezone("America/Los_Angeles")
    base = tz.localize(datetime(2026, 2, 17, 10, 0))
    slots = [_slot(base + timedelta(hours=i)) for i in range(2)]
    scheduler.get_available_slots = AsyncMock(return_value=slots)

    result = await scheduler.get_hot_seller_consultation_slots(days_ahead=7)

    assert result == []


def test_ws3_manual_scheduling_actions_include_workflow(ws3_scheduler):
    scheduler, _ = ws3_scheduler

    actions = scheduler.build_manual_scheduling_actions(high_priority=True)
    action_types = [action.type.value for action in actions]
    action_tags = [action.tag for action in actions if action.tag]
    workflows = [action.workflow_id for action in actions if action.workflow_id]

    assert "add_tag" in action_types
    assert "trigger_workflow" in action_types
    assert "Needs-Manual-Scheduling" in action_tags
    assert workflows == ["wf_manual_ws3"]


@pytest.mark.asyncio
async def test_ws3_confirmation_actions_include_sms_and_email(ws3_scheduler):
    scheduler, _ = ws3_scheduler
    tz = pytz.timezone("America/Los_Angeles")
    start = tz.localize(datetime(2026, 2, 17, 11, 0))

    booking = AppointmentBooking(
        contact_id="c_ws3",
        lead_score=6,
        appointment_type=AppointmentType.SELLER_CONSULTATION,
        time_slot=_slot(start),
        contact_info={"first_name": "Morgan", "email": "morgan@example.com"},
    )
    contact_info = {"first_name": "Morgan", "email": "morgan@example.com"}

    actions = await scheduler._generate_confirmation_actions(booking, contact_info, extracted_data={})
    message_channels = [action.channel for action in actions if action.type.value == "send_message"]

    assert MessageType.SMS in message_channels
    assert MessageType.EMAIL in message_channels

