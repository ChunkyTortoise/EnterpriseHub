import pytest
pytestmark = pytest.mark.integration

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.api.routes import webhook as webhook_module
from ghl_real_estate_ai.api.schemas.ghl import GHLContact, GHLTagWebhookEvent

@pytest.mark.integration


@pytest.mark.asyncio
async def test_tag_webhook_sends_initial_outreach():
    event = GHLTagWebhookEvent(
        type="ContactTagAdded",
        contactId="contact_123",
        locationId="location_456",
        tag="Needs Qualifying",
        contact=GHLContact(
            id="contact_123",
            firstName="Maria",
            lastName="Lopez",
            phone="+19095551234",
            email="maria@example.com",
            tags=["Needs Qualifying"],
            customFields={},
        ),
    )

    request = Mock()
    background_tasks = Mock()
    background_tasks.add_task = Mock()

    with (
        patch(
            "ghl_real_estate_ai.services.security_framework.SecurityFramework.verify_webhook_signature",
            new=AsyncMock(return_value=True),
        ),
        patch("ghl_real_estate_ai.services.security_framework.SecurityFramework._audit_log", new=AsyncMock()),
        patch.object(webhook_module, "_get_tenant_ghl_client", new=AsyncMock(return_value=Mock())),
        patch.object(webhook_module, "conversation_manager") as mock_cm,
        patch.object(webhook_module, "analytics_service") as mock_analytics,
    ):
        mock_cm.get_context = AsyncMock(return_value={"conversation_history": []})
        mock_cm.memory_service.save_context = AsyncMock()
        mock_analytics.track_event = AsyncMock()

        response = await webhook_module.handle_ghl_tag_webhook.__wrapped__(request, event, background_tasks)

        assert response.success is True
        assert "Jorge" in response.message or "jorge" in response.message.lower()
        background_tasks.add_task.assert_called()
        mock_cm.memory_service.save_context.assert_called()


@pytest.mark.asyncio
async def test_tag_webhook_no_outreach_if_history_exists():
    event = GHLTagWebhookEvent(
        type="ContactTagAdded",
        contactId="contact_789",
        locationId="location_456",
        tag="Needs Qualifying",
        contact=GHLContact(
            id="contact_789",
            firstName="James",
            lastName="Wilson",
            phone="+19095559876",
            email="james@example.com",
            tags=["Needs Qualifying"],
            customFields={},
        ),
    )

    request = Mock()
    background_tasks = Mock()
    background_tasks.add_task = Mock()

    with (
        patch(
            "ghl_real_estate_ai.services.security_framework.SecurityFramework.verify_webhook_signature",
            new=AsyncMock(return_value=True),
        ),
        patch("ghl_real_estate_ai.services.security_framework.SecurityFramework._audit_log", new=AsyncMock()),
        patch.object(webhook_module, "_get_tenant_ghl_client", new=AsyncMock(return_value=Mock())),
        patch.object(webhook_module, "conversation_manager") as mock_cm,
    ):
        mock_cm.get_context = AsyncMock(return_value={"conversation_history": [{"role": "user", "content": "hi"}]})

        response = await webhook_module.handle_ghl_tag_webhook.__wrapped__(request, event, background_tasks)

        assert response.success is True
        assert response.message == "Conversation already started"
        background_tasks.add_task.assert_not_called()