from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    MessageDirection,
    MessageType,
)


def _ws3_event(message_body: str = "1") -> GHLWebhookEvent:
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId="contact_ws3_001",
        locationId="loc_ws3_001",
        message=GHLMessage(type=MessageType.SMS, body=message_body, direction=MessageDirection.INBOUND),
        contact=GHLContact(
            contactId="contact_ws3_001",
            firstName="Alex",
            lastName="Seller",
            phone="+15555550111",
            email="alex@example.com",
            tags=["Needs Qualifying"],
            customFields={},
        ),
    )


@pytest.mark.asyncio
async def test_ws3_pending_hot_seller_strict_type_guard_falls_back_manual():
    from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook
    from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType

    event = _ws3_event("1")
    context = {
        "pending_appointment": {
            "status": "awaiting_selection",
            "flow": "hot_seller_consultation_30min",
            "options": [
                {
                    "label": "1",
                    "display": "Tuesday, February 17 at 10:00 AM PT",
                    "start_time": "2026-02-17T10:00:00-08:00",
                    "end_time": "2026-02-17T10:30:00-08:00",
                    "appointment_type": "listing_appointment",
                }
            ],
            "attempts": 0,
            "expires_at": datetime.utcnow().isoformat(),
        },
        "seller_preferences": {"questions_answered": 4},
    }

    mock_bg = MagicMock()
    mock_bg.add_task = MagicMock()
    mock_cm = MagicMock()
    mock_cm.get_context = AsyncMock(return_value=context)
    mock_cm.memory_service = MagicMock()
    mock_cm.memory_service.save_context = AsyncMock()
    mock_scheduler = MagicMock()
    mock_scheduler.HOT_SELLER_APPOINTMENT_TYPE = AppointmentType.SELLER_CONSULTATION
    mock_scheduler.get_manual_scheduling_message.return_value = "Manual fallback"
    mock_scheduler.book_appointment = AsyncMock()

    mock_settings = MagicMock()
    mock_settings.activation_tags = ["Needs Qualifying"]
    mock_settings.deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot"]
    mock_settings.manual_scheduling_workflow_id = "wf_ws3_manual"

    with (
        patch("ghl_real_estate_ai.api.routes.webhook.settings", mock_settings),
        patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())),
        patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_cm),
        patch("ghl_real_estate_ai.api.routes.webhook.tenant_service", MagicMock(get_tenant_config=AsyncMock(return_value=None))),
        patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", MagicMock()),
        patch("ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler", return_value=mock_scheduler),
    ):
        response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, mock_bg)

    assert response.success is True
    assert response.message == "Manual fallback"
    tags = [a.tag for a in response.actions if a.type == ActionType.ADD_TAG]
    workflows = [a.workflow_id for a in response.actions if a.type == ActionType.TRIGGER_WORKFLOW]
    assert "Needs-Manual-Scheduling" in tags
    assert "High-Priority-Lead" in tags
    assert workflows == ["wf_ws3_manual"]
    mock_scheduler.book_appointment.assert_not_awaited()


@pytest.mark.asyncio
async def test_ws3_pending_hot_seller_valid_slot_books_with_consult_type():
    from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook
    from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType

    event = _ws3_event("1")
    context = {
        "pending_appointment": {
            "status": "awaiting_selection",
            "flow": "hot_seller_consultation_30min",
            "options": [
                {
                    "label": "1",
                    "display": "Tuesday, February 17 at 10:00 AM PT",
                    "start_time": "2026-02-17T10:00:00-08:00",
                    "end_time": "2026-02-17T10:30:00-08:00",
                    "appointment_type": "seller_consultation",
                }
            ],
            "attempts": 0,
            "expires_at": datetime.utcnow().isoformat(),
        },
        "seller_preferences": {"questions_answered": 4},
    }

    mock_bg = MagicMock()
    mock_bg.add_task = MagicMock()
    mock_cm = MagicMock()
    mock_cm.get_context = AsyncMock(return_value=context)
    mock_cm.memory_service = MagicMock()
    mock_cm.memory_service.save_context = AsyncMock()
    mock_scheduler = MagicMock()
    mock_scheduler.HOT_SELLER_APPOINTMENT_TYPE = AppointmentType.SELLER_CONSULTATION
    mock_scheduler.get_manual_scheduling_message.return_value = "Manual fallback"
    mock_scheduler.book_appointment = AsyncMock(
        return_value=SimpleNamespace(
            success=True,
            confirmation_actions=[GHLAction(type=ActionType.ADD_TAG, tag="Appointment-Seller_Consultation")],
        )
    )

    mock_settings = MagicMock()
    mock_settings.activation_tags = ["Needs Qualifying"]
    mock_settings.deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot"]
    mock_settings.manual_scheduling_workflow_id = "wf_ws3_manual"

    with (
        patch("ghl_real_estate_ai.api.routes.webhook.settings", mock_settings),
        patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())),
        patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_cm),
        patch("ghl_real_estate_ai.api.routes.webhook.tenant_service", MagicMock(get_tenant_config=AsyncMock(return_value=None))),
        patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", MagicMock()),
        patch("ghl_real_estate_ai.services.calendar_scheduler.get_smart_scheduler", return_value=mock_scheduler),
    ):
        response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, mock_bg)

    assert response.success is True
    assert "confirmation text and email" in response.message.lower()
    assert any(a.type == ActionType.ADD_TAG and a.tag == "Appointment-Seller_Consultation" for a in response.actions)
    mock_scheduler.book_appointment.assert_awaited_once()

