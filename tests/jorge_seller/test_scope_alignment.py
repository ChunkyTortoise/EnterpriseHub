from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.routes.webhook import (
    _apply_outbound_tone_guardrails,
    handle_ghl_webhook,
    safe_apply_actions,
    safe_send_message,
)
from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction, GHLWebhookEvent, MessageType
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus
from ghl_real_estate_ai.services.calendar_scheduler import (
    AppointmentBooking,
    BookingResult,
    CalendarScheduler,
    AppointmentDuration,
    AppointmentType,
    TimeSlot,
)
from ghl_real_estate_ai.services.jorge.jorge_followup_engine import (
    FollowUpType,
    JorgeFollowUpEngine,
)
from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine


@pytest.fixture
def seller_engine():
    return JorgeSellerEngine(AsyncMock(), AsyncMock())


def test_tone_guardrails_remove_forbidden_phrases():
    guarded = _apply_outbound_tone_guardrails(
        "You are on our hit list and you're lying about the timeline."
    )
    lowered = guarded.lower()
    assert "hit list" not in lowered
    assert "you are lying" not in lowered
    assert "you're lying" not in lowered
    assert "priority list" in lowered


def test_hot_seller_consultation_duration_is_30_minutes():
    assert AppointmentType.SELLER_CONSULTATION.value == "seller_consultation"
    assert AppointmentDuration.SELLER_CONSULTATION.value == 30


@pytest.mark.asyncio
async def test_confirmation_strategy_sms_only_sends_only_sms():
    scheduler = CalendarScheduler(AsyncMock())
    start_time = datetime.now(timezone.utc)
    slot = TimeSlot(
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        duration_minutes=30,
        appointment_type=AppointmentType.SELLER_CONSULTATION,
    )
    booking = AppointmentBooking(
        contact_id="contact_sms_only",
        lead_score=5,
        appointment_type=AppointmentType.SELLER_CONSULTATION,
        time_slot=slot,
        contact_info={"first_name": "Ava", "email": "ava@example.com"},
    )

    with patch(
        "ghl_real_estate_ai.services.calendar_scheduler.jorge_settings.appointment_confirmation_strategy",
        "sms_only",
    ):
        actions = await scheduler._generate_confirmation_actions(
            booking=booking,
            contact_info={"first_name": "Ava", "email": "ava@example.com"},
            extracted_data={},
        )

    send_actions = [a for a in actions if a.type == ActionType.SEND_MESSAGE]
    assert len(send_actions) == 1
    assert send_actions[0].channel == MessageType.SMS


@pytest.mark.asyncio
async def test_confirmation_strategy_sms_and_email_sends_both_channels():
    scheduler = CalendarScheduler(AsyncMock())
    start_time = datetime.now(timezone.utc)
    slot = TimeSlot(
        start_time=start_time,
        end_time=start_time + timedelta(minutes=30),
        duration_minutes=30,
        appointment_type=AppointmentType.SELLER_CONSULTATION,
    )
    booking = AppointmentBooking(
        contact_id="contact_sms_email",
        lead_score=5,
        appointment_type=AppointmentType.SELLER_CONSULTATION,
        time_slot=slot,
        contact_info={"first_name": "Lia", "email": "lia@example.com"},
    )

    with patch(
        "ghl_real_estate_ai.services.calendar_scheduler.jorge_settings.appointment_confirmation_strategy",
        "sms_and_email",
    ):
        actions = await scheduler._generate_confirmation_actions(
            booking=booking,
            contact_info={"first_name": "Lia", "email": "lia@example.com"},
            extracted_data={},
        )

    channels = {a.channel for a in actions if a.type == ActionType.SEND_MESSAGE}
    assert MessageType.SMS in channels
    assert MessageType.EMAIL in channels


@pytest.mark.asyncio
async def test_tenant_usage_attribution_check_recovers_send_client():
    wrong_client = AsyncMock()
    wrong_client.location_id = "wrong_location"
    tenant_client = AsyncMock()
    tenant_client.location_id = "loc_scope"

    with patch(
        "ghl_real_estate_ai.api.routes.webhook.analytics_service.track_event",
        new=AsyncMock(),
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook._get_tenant_ghl_client",
        new=AsyncMock(return_value=tenant_client),
    ):
        await safe_send_message(
            ghl_client=wrong_client,
            contact_id="contact_scope",
            message="Checking in on your timeline.",
            channel=MessageType.SMS,
            location_id="loc_scope",
        )

    wrong_client.send_message.assert_not_called()
    tenant_client.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_tenant_usage_attribution_check_recovers_apply_client():
    wrong_client = AsyncMock()
    wrong_client.location_id = "wrong_location"
    tenant_client = AsyncMock()
    tenant_client.location_id = "loc_scope"
    actions = [GHLAction(type=ActionType.ADD_TAG, tag="Hot-Seller")]

    with patch(
        "ghl_real_estate_ai.api.routes.webhook.analytics_service.track_event",
        new=AsyncMock(),
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook._get_tenant_ghl_client",
        new=AsyncMock(return_value=tenant_client),
    ):
        await safe_apply_actions(
            ghl_client=wrong_client,
            contact_id="contact_scope",
            actions=actions,
            location_id="loc_scope",
        )

    wrong_client.apply_actions.assert_not_called()
    tenant_client.apply_actions.assert_awaited_once()


@pytest.mark.asyncio
async def test_scope_fields_are_written_for_seller_actions(seller_engine):
    seller_data = {
        "motivation": "relocation",
        "timeline_acceptable": True,
        "timeline_urgency": "45 days",
        "property_condition": "Needs Work",
        "price_expectation": 450000,
        "mortgage_balance": 220000,
        "repair_estimate": 35000,
        "questions_answered": 4,
    }

    actions = await seller_engine._create_seller_actions(
        contact_id="contact_scope_1",
        location_id="loc_scope_1",
        temperature="warm",
        seller_data=seller_data,
        pricing_result=None,
        persona_data={},
    )

    update_actions = [a for a in actions if a["type"] == "update_custom_field"]
    by_field = {a["field"]: a["value"] for a in update_actions}

    assert by_field["seller_temperature"] == "WARM"
    assert by_field["seller_motivation"] == "relocation"
    assert by_field["asking_price"] == "450000"
    assert by_field["qualification_complete"] == "Yes"
    assert by_field["lead_value_tier"] == "B"
    assert by_field["timeline_days"] == "30"
    assert by_field["mortgage_balance"] == "220000"
    assert by_field["repair_estimate"] == "35000"
    assert "last_bot_interaction" in by_field


@pytest.mark.asyncio
async def test_scope_followup_cadence_daily_weekly_monthly():
    engine = JorgeFollowUpEngine(AsyncMock(), AsyncMock())
    base_config = {
        "type": FollowUpType.INITIAL_NURTURE,
        "position": 1,
        "days_since_contact": 1,
        "temperature": "hot",
    }

    hot_next = await engine._schedule_next_follow_up(
        {"seller_temperature": "hot", "questions_answered": 4},
        base_config,
    )
    warm_next = await engine._schedule_next_follow_up(
        {"seller_temperature": "warm", "questions_answered": 4},
        {**base_config, "temperature": "warm"},
    )
    cold_next = await engine._schedule_next_follow_up(
        {"seller_temperature": "cold", "questions_answered": 4},
        {**base_config, "temperature": "cold"},
    )

    now = datetime.now()
    hot_days = (datetime.fromisoformat(hot_next["scheduled_date"]) - now).total_seconds() / 86400
    warm_days = (datetime.fromisoformat(warm_next["scheduled_date"]) - now).total_seconds() / 86400
    cold_days = (datetime.fromisoformat(cold_next["scheduled_date"]) - now).total_seconds() / 86400

    assert 0.9 <= hot_days <= 1.2
    assert 6.8 <= warm_days <= 7.2
    assert 29.8 <= cold_days <= 30.2


@pytest.mark.asyncio
async def test_opt_out_adds_do_not_contact_tag():
    event = GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_opt_out",
        locationId="loc_opt_out",
        message={"type": "SMS", "body": "stop", "direction": "inbound"},
        contact={"firstName": "Sam", "tags": ["Needs Qualifying"], "customFields": {}},
    )
    background_tasks = MagicMock()
    mock_client = AsyncMock()

    with patch(
        "ghl_real_estate_ai.api.routes.webhook._get_tenant_ghl_client",
        new=AsyncMock(return_value=mock_client),
    ):
        response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, background_tasks)

    assert response.success is True
    add_tags = {a.tag for a in response.actions if a.type.value == "add_tag"}
    remove_tags = {a.tag for a in response.actions if a.type.value == "remove_tag"}
    assert "AI-Off" in add_tags
    assert "Do Not Contact" in add_tags
    assert "Needs Qualifying" in remove_tags


@pytest.mark.asyncio
async def test_hot_seller_booking_selection_uses_30_minute_consultation_slot():
    start_time = datetime(2026, 2, 10, 18, 0, tzinfo=timezone.utc)
    end_time = start_time + timedelta(minutes=30)
    event = GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_hot_booking",
        locationId="loc_hot_booking",
        message={"type": "SMS", "body": "1", "direction": "inbound"},
        contact={
            "firstName": "Sam",
            "lastName": "Lead",
            "phone": "+19095550101",
            "email": "sam@example.com",
            "tags": ["Needs Qualifying"],
            "customFields": {},
        },
    )
    background_tasks = MagicMock()
    mock_scheduler = MagicMock()
    mock_scheduler.book_appointment = AsyncMock(
        return_value=BookingResult(success=True, confirmation_actions=[])
    )
    mock_cm = MagicMock()
    mock_cm.get_context = AsyncMock(
        return_value={
            "seller_preferences": {},
            "pending_appointment": {
                "status": "awaiting_selection",
                "options": [
                    {
                        "label": "1",
                        "display": "Tuesday, February 10 at 10:00 AM PT",
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat(),
                        "appointment_type": "seller_consultation",
                    }
                ],
                "attempts": 0,
            },
        }
    )
    mock_cm.memory_service = MagicMock()
    mock_cm.memory_service.save_context = AsyncMock()

    with patch(
        "ghl_real_estate_ai.api.routes.webhook.conversation_manager",
        mock_cm,
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook._get_tenant_ghl_client",
        new=AsyncMock(return_value=AsyncMock(location_id="loc_hot_booking")),
    ), patch(
        "ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler",
        return_value=mock_scheduler,
    ):
        response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, background_tasks)

    assert response.success is True
    booking_call = mock_scheduler.book_appointment.await_args.kwargs
    slot = booking_call["time_slot"]
    assert slot.appointment_type == AppointmentType.SELLER_CONSULTATION
    assert slot.duration_minutes == 30


@pytest.mark.asyncio
async def test_seller_route_maps_custom_field_key_correctly():
    event = GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_field_map",
        locationId="loc_field_map",
        message={"type": "SMS", "body": "Timeline is 30 days", "direction": "inbound"},
        contact={"firstName": "Lia", "tags": ["Needs Qualifying"], "customFields": {}},
    )
    background_tasks = MagicMock()
    seller_result = {
        "message": "Thanks, that helps.",
        "temperature": "warm",
        "questions_answered": 3,
        "actions": [
            {"type": "update_custom_field", "field": "seller_temperature", "value": "WARM"}
        ],
        "handoff_signals": {},
    }

    mock_engine = MagicMock()
    mock_engine.process_seller_response = AsyncMock(return_value=seller_result)

    with patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings.jorge_seller_mode", True), patch(
        "ghl_real_estate_ai.api.routes.webhook.jorge_settings.jorge_buyer_mode", False
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook.tenant_service.get_tenant_config",
        new=AsyncMock(return_value={}),
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook.MLSClient"
    ), patch(
        "ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine",
        return_value=mock_engine,
    ), patch(
        "ghl_real_estate_ai.api.routes.webhook.compliance_guard.audit_message",
        new=AsyncMock(return_value=(ComplianceStatus.PASSED, "", [])),
    ):
        response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, background_tasks)

    assert response.success is True
    assert response.actions
    assert response.actions[0].field == "seller_temperature"
