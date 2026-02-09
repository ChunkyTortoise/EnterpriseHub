import pytest
pytestmark = pytest.mark.integration

"""
Comprehensive Webhook Routing Tests — Phase 5

Tests all three bot modes (seller, buyer, lead) through the webhook handler
with shared fixtures covering priority routing, deactivation, opt-out,
error fallback, and compliance enforcement.

All external services are mocked. No real API calls.
"""

import os

# Set required env vars BEFORE any application imports trigger singleton init
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    GHLWebhookResponse,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_webhook_event(
    message_body: str,
    contact_id: str = "contact_routing_001",
    location_id: str = "loc_routing_456",
    tags: list[str] | None = None,
    direction: MessageDirection = MessageDirection.INBOUND,
    first_name: str = "TestUser",
) -> GHLWebhookEvent:
    """Build a GHLWebhookEvent for routing tests."""
    return GHLWebhookEvent(
        type="InboundMessage",
        contactId=contact_id,
        locationId=location_id,
        message=GHLMessage(type=MessageType.SMS, body=message_body, direction=direction),
        contact=GHLContact(
            contactId=contact_id,
            firstName=first_name,
            lastName="Routing",
            phone="+19095550001",
            email="routing@test.com",
            tags=tags or [],
            customFields={},
        ),
    )


def _action_tags(response: GHLWebhookResponse) -> list[str]:
    """Extract ADD_TAG tag names from a response."""
    return [a.tag for a in response.actions if a.type == ActionType.ADD_TAG]


def _remove_tags(response: GHLWebhookResponse) -> list[str]:
    """Extract REMOVE_TAG tag names from a response."""
    return [a.tag for a in response.actions if a.type == ActionType.REMOVE_TAG]


# ---------------------------------------------------------------------------
# Shared all-mode patch context manager
# ---------------------------------------------------------------------------


def _all_mode_patches(
    jorge_seller_mode: bool = True,
    jorge_buyer_mode: bool = True,
    jorge_lead_mode: bool = True,
    seller_raises: bool = False,
    buyer_raises: bool = False,
    lead_raises: bool = False,
    compliance_status: ComplianceStatus = ComplianceStatus.PASSED,
):
    """Context manager that configures all three bot modes simultaneously.

    Args:
        jorge_seller_mode: Enable/disable seller mode.
        jorge_buyer_mode: Enable/disable buyer mode.
        jorge_lead_mode: Enable/disable lead mode.
        seller_raises: If True, seller engine raises RuntimeError.
        buyer_raises: If True, buyer bot raises RuntimeError.
        lead_raises: If True, lead conversation_manager raises RuntimeError.
        compliance_status: Compliance audit result for all modes.
    """

    @contextmanager
    def _patches():
        # --- Jorge settings ---
        mock_jorge_settings = MagicMock()
        mock_jorge_settings.JORGE_SELLER_MODE = jorge_seller_mode
        mock_jorge_settings.JORGE_BUYER_MODE = jorge_buyer_mode
        mock_jorge_settings.JORGE_LEAD_MODE = jorge_lead_mode
        mock_jorge_settings.LEAD_ACTIVATION_TAG = "Needs Qualifying"
        mock_jorge_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"

        # --- Main config settings ---
        mock_config_settings = MagicMock()
        mock_config_settings.activation_tags = ["Needs Qualifying"]
        mock_config_settings.deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot", "AI-Qualified"]
        mock_config_settings.auto_deactivate_threshold = 70
        mock_config_settings.notify_agent_workflow_id = None
        mock_config_settings.custom_field_lead_score = None
        mock_config_settings.custom_field_budget = None
        mock_config_settings.custom_field_location = None
        mock_config_settings.custom_field_timeline = None
        mock_config_settings.appointment_auto_booking_enabled = False

        # --- Seller engine ---
        mock_seller_engine_instance = MagicMock()
        if seller_raises:
            mock_seller_engine_instance.process_seller_response = AsyncMock(
                side_effect=RuntimeError("Seller engine error")
            )
        else:
            mock_seller_engine_instance.process_seller_response = AsyncMock(
                return_value={
                    "temperature": "warm",
                    "message": "What price would incentivize you to sell?",
                    "questions_answered": 2,
                    "actions": [{"type": "add_tag", "tag": "Warm-Seller"}],
                }
            )

        # --- Buyer bot ---
        mock_buyer_bot_instance = MagicMock()
        if buyer_raises:
            mock_buyer_bot_instance.process_buyer_conversation = AsyncMock(side_effect=RuntimeError("Buyer bot error"))
        else:
            mock_buyer_bot_instance.process_buyer_conversation = AsyncMock(
                return_value={
                    "buyer_temperature": "warm",
                    "is_qualified": False,
                    "financial_readiness_score": 55,
                    "response_content": "What area in Rancho Cucamonga interests you most?",
                }
            )

        # --- Lead (ConversationManager) ---
        mock_ai_response = MagicMock()
        mock_ai_response.message = "Thanks for reaching out! Tell me more about what you need."
        mock_ai_response.lead_score = 3
        mock_ai_response.extracted_data = {}

        mock_conv_mgr = MagicMock()
        if lead_raises:
            mock_conv_mgr.generate_response = AsyncMock(side_effect=RuntimeError("Lead processing error"))
        else:
            mock_conv_mgr.generate_response = AsyncMock(return_value=mock_ai_response)
        mock_conv_mgr.get_context = AsyncMock(return_value={})
        mock_conv_mgr.update_context = AsyncMock()
        mock_conv_mgr.get_conversation_history = AsyncMock(return_value=[])

        # --- Compliance ---
        mock_compliance = MagicMock()
        mock_compliance.audit_message = AsyncMock(
            return_value=(
                compliance_status,
                "test_reason" if compliance_status == ComplianceStatus.BLOCKED else "",
                ["violation"] if compliance_status == ComplianceStatus.BLOCKED else [],
            )
        )

        # --- Other deps ---
        mock_tenant = MagicMock()
        mock_tenant.get_tenant_config = AsyncMock(return_value=None)

        mock_lead_scorer = MagicMock()
        mock_lead_scorer.classify.return_value = "warm"
        mock_lead_scorer.get_percentage_score.return_value = 42
        mock_lead_scorer._is_urgent_timeline.return_value = False

        mock_ghl_client = MagicMock(
            send_message=AsyncMock(),
            apply_actions=AsyncMock(),
            add_tags=AsyncMock(),
        )

        mock_lead_source_tracker = MagicMock()
        mock_lead_source_tracker.analyze_lead_source = AsyncMock(side_effect=Exception("test skip"))

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", MagicMock(track_event=AsyncMock())),
            patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", mock_ghl_client),
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_jorge_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.settings", mock_config_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.compliance_guard", mock_compliance),
            patch("ghl_real_estate_ai.api.routes.webhook.tenant_service", mock_tenant),
            patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conv_mgr),
            patch("ghl_real_estate_ai.api.routes.webhook._get_lead_scorer", return_value=mock_lead_scorer),
            patch("ghl_real_estate_ai.api.routes.webhook.lead_source_tracker", mock_lead_source_tracker),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.attribution_analytics",
                MagicMock(track_daily_metrics=AsyncMock()),
            ),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.pricing_optimizer", MagicMock(calculate_lead_price=AsyncMock())
            ),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.subscription_manager",
                MagicMock(get_active_subscription=AsyncMock(return_value=None)),
            ),
            patch("ghl_real_estate_ai.api.routes.webhook.calendar_scheduler", MagicMock()),
            patch(
                "ghl_real_estate_ai.api.routes.webhook.handoff_service",
                MagicMock(
                    evaluate_handoff=AsyncMock(return_value=None),
                    execute_handoff=AsyncMock(return_value=[]),
                ),
            ),
            patch(
                "ghl_real_estate_ai.services.jorge.jorge_seller_engine.JorgeSellerEngine",
                return_value=mock_seller_engine_instance,
            ),
            patch("ghl_real_estate_ai.agents.jorge_buyer_bot.JorgeBuyerBot", return_value=mock_buyer_bot_instance),
        ):
            yield {
                "jorge_settings": mock_jorge_settings,
                "config_settings": mock_config_settings,
                "seller_engine": mock_seller_engine_instance,
                "buyer_bot": mock_buyer_bot_instance,
                "conversation_manager": mock_conv_mgr,
                "compliance": mock_compliance,
                "ghl_client": mock_ghl_client,
                "ai_response": mock_ai_response,
                "lead_scorer": mock_lead_scorer,
            }

    return _patches()


# ===========================================================================
# Comprehensive Webhook Routing Tests
# ===========================================================================


@pytest.mark.integration
class TestWebhookRoutingComprehensive:
    """Phase 5: All three bot modes in a single suite with shared fixtures."""

    @pytest.mark.asyncio
    async def test_all_three_modes_concurrent(self):
        """Three contacts, each with different tags, all routed to correct bot."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        # Contact 1: Seller (Needs Qualifying + seller mode)
        seller_event = _make_webhook_event(
            "I want to sell my house",
            contact_id="seller_001",
            tags=["Needs Qualifying"],
        )
        # Contact 2: Buyer (Buyer-Lead tag)
        buyer_event = _make_webhook_event(
            "Looking for a 3BR in Victoria",
            contact_id="buyer_001",
            tags=["Buyer-Lead"],
        )
        # Contact 3: Lead (Needs Qualifying, no seller mode since seller already handled)
        lead_event = _make_webhook_event(
            "I am interested in real estate",
            contact_id="lead_001",
            tags=["Needs Qualifying"],
        )

        # Seller contact
        with _all_mode_patches() as mocks:
            seller_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), seller_event, MagicMock())
        assert seller_resp.success is True
        assert "price" in seller_resp.message.lower() or "sell" in seller_resp.message.lower()

        # Buyer contact
        with _all_mode_patches() as mocks:
            buyer_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), buyer_event, MagicMock())
        assert buyer_resp.success is True
        mocks["buyer_bot"].process_buyer_conversation.assert_awaited_once()

        # Lead contact (seller mode off so lead routes correctly)
        with _all_mode_patches(jorge_seller_mode=False) as mocks:
            lead_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), lead_event, MagicMock())
        assert lead_resp.success is True
        mocks["conversation_manager"].generate_response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_priority_seller_over_lead(self):
        """'Needs Qualifying' + SELLER_MODE=true routes to seller, not lead."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "Tell me about selling",
            tags=["Needs Qualifying"],
        )

        with _all_mode_patches(jorge_seller_mode=True, jorge_lead_mode=True) as mocks:
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.success is True
        mocks["seller_engine"].process_seller_response.assert_awaited_once()
        mocks["conversation_manager"].generate_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_priority_buyer_over_lead(self):
        """'Buyer-Lead' tag routes to buyer bot, not lead bot."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "I want to buy a house",
            tags=["Buyer-Lead"],
        )

        with _all_mode_patches(jorge_buyer_mode=True, jorge_lead_mode=True) as mocks:
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.success is True
        mocks["buyer_bot"].process_buyer_conversation.assert_awaited_once()
        mocks["conversation_manager"].generate_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_priority_seller_over_buyer(self):
        """Both 'Needs Qualifying' and 'Buyer-Lead' tags present: seller wins."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "I have a property question",
            tags=["Needs Qualifying", "Buyer-Lead"],
        )

        with _all_mode_patches(jorge_seller_mode=True, jorge_buyer_mode=True) as mocks:
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.success is True
        mocks["seller_engine"].process_seller_response.assert_awaited_once()
        mocks["buyer_bot"].process_buyer_conversation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_deactivation_blocks_all_modes(self):
        """'AI-Off' tag stops seller, buyer, AND lead routing."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        for tag_set in [
            ["Needs Qualifying", "AI-Off"],
            ["Buyer-Lead", "AI-Off"],
            ["Needs Qualifying", "Buyer-Lead", "AI-Off"],
        ]:
            event = _make_webhook_event(
                "Hello",
                tags=tag_set,
            )
            with _all_mode_patches() as mocks:
                response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

            assert response.success is True
            assert "deactivated" in response.message.lower()
            mocks["seller_engine"].process_seller_response.assert_not_awaited()
            mocks["buyer_bot"].process_buyer_conversation.assert_not_awaited()
            mocks["conversation_manager"].generate_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_opt_out_from_any_mode(self):
        """'stop' message deactivates AI regardless of which bot mode is active."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        for tag_set in [
            ["Needs Qualifying"],
            ["Buyer-Lead"],
        ]:
            event = _make_webhook_event(
                "stop",
                tags=tag_set,
            )
            with _all_mode_patches() as mocks:
                response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

            assert response.success is True
            assert "AI-Off" in _action_tags(response)
            # No bot should have processed
            mocks["seller_engine"].process_seller_response.assert_not_awaited()
            mocks["buyer_bot"].process_buyer_conversation.assert_not_awaited()
            mocks["conversation_manager"].generate_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_mode_flags_disable_correctly(self):
        """All three mode flags=false results in raw fallback response."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "Hello",
            tags=["Needs Qualifying"],
        )

        with _all_mode_patches(
            jorge_seller_mode=False,
            jorge_buyer_mode=False,
            jorge_lead_mode=False,
        ) as mocks:
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.success is True
        # Raw fallback
        assert "reaching out" in response.message.lower() or "help" in response.message.lower()
        mocks["seller_engine"].process_seller_response.assert_not_awaited()
        mocks["buyer_bot"].process_buyer_conversation.assert_not_awaited()
        mocks["conversation_manager"].generate_response.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_error_in_seller_falls_to_buyer(self):
        """Seller error + buyer tag present = buyer bot processes instead."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "I have a property question",
            tags=["Needs Qualifying", "Buyer-Lead"],
        )

        with _all_mode_patches(
            jorge_seller_mode=True,
            jorge_buyer_mode=True,
            seller_raises=True,
        ) as mocks:
            response = await handle_ghl_webhook.__wrapped__(MagicMock(), event, MagicMock())

        assert response.success is True
        # Seller raised, should fall through to buyer
        mocks["buyer_bot"].process_buyer_conversation.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_error_in_all_bots_returns_fallback(self):
        """All bots error results in safe fallback response (via error handler)."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        event = _make_webhook_event(
            "Hello there",
            tags=["Needs Qualifying"],
        )

        mock_bg_tasks = MagicMock()

        with _all_mode_patches(
            jorge_seller_mode=True,
            jorge_buyer_mode=False,
            jorge_lead_mode=True,
            seller_raises=True,
            lead_raises=True,
        ) as mocks:
            try:
                await handle_ghl_webhook.__wrapped__(MagicMock(), event, mock_bg_tasks)
            except Exception:
                # HTTPException from error handler is expected
                pass

            # Fallback message should have been queued via background_tasks.add_task
            add_task_calls = mock_bg_tasks.add_task.call_args_list
            send_message_queued = any(
                args and args[0] is mocks["ghl_client"].send_message for args, kwargs in [c for c in add_task_calls]
            )
            assert send_message_queued, "Expected fallback send_message to be queued in background_tasks"

    @pytest.mark.asyncio
    async def test_compliance_enforced_all_modes(self):
        """Blocked compliance status replaces messages in all three bot paths."""
        from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook

        # Test seller compliance
        seller_event = _make_webhook_event(
            "Sell my house",
            contact_id="compliance_seller",
            tags=["Needs Qualifying"],
        )
        with _all_mode_patches(
            jorge_seller_mode=True,
            compliance_status=ComplianceStatus.BLOCKED,
        ) as mocks:
            seller_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), seller_event, MagicMock())

        assert seller_resp.success is True
        assert "Compliance-Alert" in _action_tags(seller_resp)
        # Seller fallback replaces blocked message
        assert "property" in seller_resp.message.lower() or "price" in seller_resp.message.lower()

        # Test buyer compliance
        buyer_event = _make_webhook_event(
            "Buy a house",
            contact_id="compliance_buyer",
            tags=["Buyer-Lead"],
        )
        with _all_mode_patches(
            jorge_seller_mode=False,
            jorge_buyer_mode=True,
            compliance_status=ComplianceStatus.BLOCKED,
        ) as mocks:
            buyer_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), buyer_event, MagicMock())

        assert buyer_resp.success is True
        assert "Compliance-Alert" in _action_tags(buyer_resp)
        assert "home" in buyer_resp.message.lower() or "property" in buyer_resp.message.lower()

        # Test lead compliance
        lead_event = _make_webhook_event(
            "Tell me about real estate",
            contact_id="compliance_lead",
            tags=["Needs Qualifying"],
        )
        with _all_mode_patches(
            jorge_seller_mode=False,
            jorge_buyer_mode=False,
            jorge_lead_mode=True,
            compliance_status=ComplianceStatus.BLOCKED,
        ) as mocks:
            lead_resp = await handle_ghl_webhook.__wrapped__(MagicMock(), lead_event, MagicMock())

        assert lead_resp.success is True
        assert "Compliance-Alert" in _action_tags(lead_resp)
        assert "love to help" in lead_resp.message.lower() or "help" in lead_resp.message.lower()
