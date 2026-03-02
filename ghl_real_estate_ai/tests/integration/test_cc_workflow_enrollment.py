"""
Integration tests for CC DTS campaign workflow enrollment.
Tests that _build_cc_workflow_actions() enrolls contacts in the correct
CC-patterned workflows based on sentiment, temperature, lead status, and ghost state.
Also tests that handle_ghl_tag_webhook triggers CC_AI_TAG_WORKFLOW_ID on activation tags.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.routes.webhook import _build_cc_workflow_actions, _detect_negative_sentiment, _detect_rejected_offer, handle_ghl_tag_webhook
from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLContact, GHLTagWebhookEvent
from ghl_real_estate_ai.services.ghost_followup_engine import GhostFollowUpEngine, GhostState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cc_settings():
    """Minimal JorgeEnvironmentSettings-like object with CC workflow IDs set."""
    s = MagicMock()
    s.cc_negative_convo_workflow_id = "70524142-fdea-457d-97c6-aeaa9b8a7b85"
    s.cc_ghosting_workflow_id = "7174d3dc-2c95-418c-8bad-3dcedb0ba5fa"
    s.cc_cold_campaign_workflow_id = "f66c0661-80b9-4aa4-97e7-95063df72f79"
    s.cc_10dih_workflow_id = "c946fc0d-29ca-4d3d-b3a0-33e5df9a8681"
    s.cc_inbound_seller_workflow_id = "bec3f293-665f-4b30-a524-5964620dd75c"
    s.cc_rejected_offer_workflow_id = "42a36bf2-fbec-478b-a0ee-af63e8b16d7e"
    s.cc_unstale_lead_workflow_id = "f81f593f-8cff-4309-8864-b1fa4d779574"
    s.cc_seller_dispo_workflow_id = "57884662-61e8-4b56-bd1d-4eda63600bea"
    s.cc_ai_tag_workflow_id = "47fc0922-dae1-48d1-863f-a62bbc0c4e60"
    s.cc_ai_off_tag_workflow_id = "bb7cb261-70ab-43d6-8094-ba82e2d4ac6b"
    return s


@pytest.fixture
def empty_settings():
    """Settings with no CC workflow IDs configured."""
    s = MagicMock()
    s.cc_negative_convo_workflow_id = None
    s.cc_ghosting_workflow_id = None
    s.cc_cold_campaign_workflow_id = None
    s.cc_10dih_workflow_id = None
    s.cc_inbound_seller_workflow_id = None
    s.cc_rejected_offer_workflow_id = None
    s.cc_unstale_lead_workflow_id = None
    s.cc_seller_dispo_workflow_id = None
    s.cc_ai_tag_workflow_id = None
    s.cc_ai_off_tag_workflow_id = None
    return s


def _make_cache(existing_keys: set[str] | None = None):
    """Return a mock cache that behaves like get_cache_service()."""
    keys = existing_keys or set()
    cache = AsyncMock()
    cache.get = AsyncMock(side_effect=lambda k: "1" if k in keys else None)
    cache.set = AsyncMock(return_value=True)
    return cache


# ---------------------------------------------------------------------------
# _detect_negative_sentiment unit tests
# ---------------------------------------------------------------------------

class TestDetectNegativeSentiment:
    def test_angry_keyword(self):
        assert _detect_negative_sentiment("I'm angry about this") is True

    def test_frustrated_keyword(self):
        assert _detect_negative_sentiment("I feel frustrated") is True

    def test_disappointed_keyword(self):
        assert _detect_negative_sentiment("Very disappointed with the service") is True

    def test_positive_message(self):
        assert _detect_negative_sentiment("Sounds great, when can we talk?") is False

    def test_neutral_message(self):
        assert _detect_negative_sentiment("What's my home worth?") is False

    def test_case_insensitive(self):
        assert _detect_negative_sentiment("I AM FRUSTRATED") is True


# ---------------------------------------------------------------------------
# _build_cc_workflow_actions integration tests
# ---------------------------------------------------------------------------

class TestBuildCCWorkflowActions:

    @pytest.mark.asyncio
    async def test_negative_sentiment_triggers_cc_workflow(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="I'm so frustrated with this process",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_001",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_negative_convo_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_cold_seller_triggers_dts_cold_and_10dih(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "cold"},
                user_message="Sure I'll think about it",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_002",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_cold_campaign_workflow_id in triggered_ids
        assert cc_settings.cc_10dih_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_hot_seller_triggers_dispo_workflow(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "hot"},
                user_message="Yes let's move forward",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_003",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_seller_dispo_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_new_inbound_triggers_email_campaign(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="Hi, I'm thinking about selling",
                settings=cc_settings,
                is_new_lead=True,
                contact_id="contact_004",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_inbound_seller_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_ghosted_contact_re_engage_triggers_unstale(self, cc_settings):
        ghost_key = "ghost_state:contact_005"
        cache = _make_cache(existing_keys={ghost_key})
        cache.get = AsyncMock(side_effect=lambda k: "ghosted" if k == ghost_key else None)

        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=cache):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="Hey still interested",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_005",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_unstale_lead_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_no_duplicate_enrollment_same_workflow(self, cc_settings):
        # Simulate that cold campaign is already enrolled (dedup key present)
        wf_short = cc_settings.cc_cold_campaign_workflow_id[:8]
        dedup_key = f"cc_wf_enrolled:contact_006:{wf_short}"
        cache = _make_cache(existing_keys={dedup_key})

        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=cache):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "cold"},
                user_message="Hmm maybe later",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_006",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_cold_campaign_workflow_id not in triggered_ids

    @pytest.mark.asyncio
    async def test_missing_env_var_skips_gracefully(self, empty_settings):
        """When all CC workflow IDs are None, no error should be raised."""
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "cold"},
                user_message="I'm so frustrated",
                settings=empty_settings,
                is_new_lead=True,
                contact_id="contact_007",
            )

        assert actions == []

    @pytest.mark.asyncio
    async def test_warm_seller_no_cold_workflows(self, cc_settings):
        """Warm seller should NOT trigger cold campaign workflows."""
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="I might be interested soon",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_008",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_cold_campaign_workflow_id not in triggered_ids
        assert cc_settings.cc_10dih_workflow_id not in triggered_ids

    @pytest.mark.asyncio
    async def test_rejected_offer_triggers_cc_workflow(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="The offer was rejected, they won't accept anything below asking",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_009",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_rejected_offer_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_rejected_offer_keyword_lowball(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "cold"},
                user_message="They said it was a lowball offer and walked away",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_010",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_rejected_offer_workflow_id in triggered_ids

    @pytest.mark.asyncio
    async def test_non_rejection_message_no_trigger(self, cc_settings):
        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=_make_cache()):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="We are still reviewing our options and will be in touch soon",
                settings=cc_settings,
                is_new_lead=False,
                contact_id="contact_011",
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert cc_settings.cc_rejected_offer_workflow_id not in triggered_ids


# ---------------------------------------------------------------------------
# handle_ghl_tag_webhook — CC_AI_TAG_WORKFLOW_ID enrollment tests
# ---------------------------------------------------------------------------

def _make_tag_event(contact_id: str = "tag_contact_001", tag: str = "Needs Qualifying") -> GHLTagWebhookEvent:
    """Build a minimal GHLTagWebhookEvent for an activation tag."""
    return GHLTagWebhookEvent(
        contactId=contact_id,
        locationId="location_test",
        tag=tag,
        contact=GHLContact(
            id=contact_id,
            first_name="Test",
            last_name="User",
            tags=[tag],
        ),
    )


class TestTagWebhookCCAIWorkflowEnrollment:
    """Tests that handle_ghl_tag_webhook wires CC_AI_TAG_WORKFLOW_ID on activation tags."""

    @pytest.mark.asyncio
    async def test_ai_activation_tag_triggers_cc_ai_tag_workflow(self):
        """Receiving an activation tag ('Needs Qualifying') fires cc_ai_tag_workflow_id."""
        ai_tag_wf_id = "47fc0922-dae1-48d1-863f-a62bbc0c4e60"
        contact_id = "tag_contact_001"
        event = _make_tag_event(contact_id=contact_id, tag="Needs Qualifying")

        mock_context = {}
        mock_conv_manager = AsyncMock()
        mock_conv_manager.get_context = AsyncMock(return_value=mock_context)
        mock_conv_manager.memory_service = AsyncMock()
        mock_conv_manager.memory_service.save_context = AsyncMock()

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)  # not yet enrolled
        mock_cache.set = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.LEAD_ACTIVATION_TAG = "Needs Qualifying"
        mock_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
        mock_settings.JORGE_SELLER_MODE = False
        mock_settings.JORGE_BUYER_MODE = False
        mock_settings.cc_ai_tag_workflow_id = ai_tag_wf_id

        mock_request = MagicMock()
        mock_background = MagicMock()
        mock_background.add_task = MagicMock()
        mock_tenant_service = AsyncMock()
        mock_tenant_service.get_tenant_config = AsyncMock(return_value=None)
        mock_ghl_client = AsyncMock()
        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=mock_cache),
        ):
            response = await handle_ghl_tag_webhook.__wrapped__(
                request=mock_request,
                event=event,
                background_tasks=mock_background,
                conversation_manager=mock_conv_manager,
                tenant_service=mock_tenant_service,
                ghl_client_default=mock_ghl_client,
                analytics_service=mock_analytics,
            )

        triggered_ids = [a.workflow_id for a in response.actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert ai_tag_wf_id in triggered_ids, (
            f"Expected cc_ai_tag_workflow_id {ai_tag_wf_id} to be triggered, got: {triggered_ids}"
        )

    @pytest.mark.asyncio
    async def test_ai_tag_dedup_prevents_double_enrollment(self):
        """Same activation tag event received twice only triggers workflow once (Redis dedup)."""
        ai_tag_wf_id = "47fc0922-dae1-48d1-863f-a62bbc0c4e60"
        contact_id = "tag_contact_dedup"
        dedup_key = f"cc_wf_enrolled:{contact_id}:{ai_tag_wf_id[:8]}"
        event = _make_tag_event(contact_id=contact_id, tag="Needs Qualifying")

        mock_context = {}
        mock_conv_manager = AsyncMock()
        mock_conv_manager.get_context = AsyncMock(return_value=mock_context)
        mock_conv_manager.memory_service = AsyncMock()
        mock_conv_manager.memory_service.save_context = AsyncMock()

        # Dedup key already exists — simulates second call after first enrollment
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=lambda k: "1" if k == dedup_key else None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.LEAD_ACTIVATION_TAG = "Needs Qualifying"
        mock_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
        mock_settings.JORGE_SELLER_MODE = False
        mock_settings.JORGE_BUYER_MODE = False
        mock_settings.cc_ai_tag_workflow_id = ai_tag_wf_id

        mock_request = MagicMock()
        mock_background = MagicMock()
        mock_background.add_task = MagicMock()
        mock_tenant_service = AsyncMock()
        mock_tenant_service.get_tenant_config = AsyncMock(return_value=None)
        mock_ghl_client = AsyncMock()
        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=mock_cache),
        ):
            response = await handle_ghl_tag_webhook.__wrapped__(
                request=mock_request,
                event=event,
                background_tasks=mock_background,
                conversation_manager=mock_conv_manager,
                tenant_service=mock_tenant_service,
                ghl_client_default=mock_ghl_client,
                analytics_service=mock_analytics,
            )

        triggered_ids = [a.workflow_id for a in response.actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert ai_tag_wf_id not in triggered_ids, (
            f"Expected dedup to suppress cc_ai_tag_workflow_id, but it appeared in: {triggered_ids}"
        )
        # set() should not have been called again since key already exists
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_needs_qualifying_tag_on_buyer_lead_contact_sends_buyer_outreach(self):
        """
        When GHL Bot Activation workflow fires on Buyer-Lead and then adds Needs Qualifying,
        a second tag-webhook fires with tag='Needs Qualifying'.  The contact already holds
        Buyer-Lead, so we must send buyer-style outreach — NOT seller outreach.
        """
        contact_id = "buyer_contact_nq_override"
        # The incoming tag is seller-routing, but the contact also has Buyer-Lead.
        event = GHLTagWebhookEvent(
            contactId=contact_id,
            locationId="location_test",
            tag="Needs Qualifying",
            contact=GHLContact(
                id=contact_id,
                first_name="Maria",
                last_name="Lopez",
                tags=["Buyer-Lead", "Needs Qualifying"],
            ),
        )

        mock_context = {}
        mock_conv_manager = AsyncMock()
        mock_conv_manager.get_context = AsyncMock(return_value=mock_context)
        mock_conv_manager.memory_service = AsyncMock()
        mock_conv_manager.memory_service.save_context = AsyncMock()

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.LEAD_ACTIVATION_TAG = "lead-bot"
        mock_settings.BUYER_ACTIVATION_TAG = "Buyer-Lead"
        mock_settings.JORGE_SELLER_MODE = True
        mock_settings.JORGE_BUYER_MODE = True
        mock_settings.cc_ai_tag_workflow_id = None

        mock_request = MagicMock()
        mock_background = MagicMock()
        mock_background.add_task = MagicMock()
        mock_tenant_service = AsyncMock()
        mock_tenant_service.get_tenant_config = AsyncMock(return_value=None)
        mock_ghl_client = AsyncMock()
        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()

        mock_rancho = MagicMock()
        mock_rancho.BUYER_INITIAL_OUTREACH_MESSAGES = ["Hi {name}, glad you reached out! Still searching?"]
        mock_rancho.INITIAL_OUTREACH_MESSAGES = ["Hi {name}, thinking about selling?"]

        sent_messages: list[str] = []

        def capture_add_task(fn, *args, **kwargs):
            if fn.__name__ == "safe_send_message" or (hasattr(fn, "__self__") and hasattr(fn, "send_message")):
                sent_messages.append(kwargs.get("message") or (args[2] if len(args) > 2 else ""))

        mock_background.add_task.side_effect = capture_add_task

        with (
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings", mock_settings),
            patch("ghl_real_estate_ai.api.routes.webhook.rancho_config", mock_rancho),
            patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=mock_cache),
        ):
            response = await handle_ghl_tag_webhook.__wrapped__(
                request=mock_request,
                event=event,
                background_tasks=mock_background,
                conversation_manager=mock_conv_manager,
                tenant_service=mock_tenant_service,
                ghl_client_default=mock_ghl_client,
                analytics_service=mock_analytics,
            )

        # Response message must be buyer-style, not seller-style
        assert response.success is True
        assert "selling" not in response.message.lower(), (
            f"Seller outreach sent to buyer contact: {response.message!r}"
        )
        assert "searching" in response.message.lower() or "glad" in response.message.lower(), (
            f"Expected buyer-style outreach, got: {response.message!r}"
        )


# ---------------------------------------------------------------------------
# GhostFollowUpEngine — CC_GHOSTING_WORKFLOW_ID pipeline tests
# ---------------------------------------------------------------------------

_CC_GHOSTING_WF_ID = "7174d3dc-2c95-418c-8bad-3dcedb0ba5fa"
_CC_UNSTALE_WF_ID = "f81f593f-8cff-4309-8864-b1fa4d779574"


class TestGhostingSetRedisKey:
    """Part 1: ghost engine writes ghost_state Redis key when marking contact ghosted."""

    @pytest.mark.asyncio
    async def test_ghosting_sets_redis_key(self):
        """mark_as_ghosted() writes ghost_state:{contact_id}='ghosted' to Redis with 30-day TTL."""
        contact_id = "ghost_contact_r001"
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_settings = MagicMock()
        mock_settings.cc_ghosting_workflow_id = None  # no workflow — only Redis write tested

        engine = GhostFollowUpEngine()

        with (
            patch("ghl_real_estate_ai.services.ghost_followup_engine.get_cache_service", return_value=mock_cache),
            patch("ghl_real_estate_ai.ghl_utils.jorge_config.settings", mock_settings),
        ):
            await engine.mark_as_ghosted(contact_id)

        ghost_key = f"ghost_state:{contact_id}"
        set_calls = [(c.args[0], c.args[1]) for c in mock_cache.set.call_args_list if c.args]
        assert (ghost_key, "ghosted") in set_calls, (
            f"Expected cache.set('{ghost_key}', 'ghosted', ...) to be called. Got: {set_calls}"
        )


class TestCCGhostingWorkflowTriggeredOnGhost:
    """Part 2: CC_GHOSTING_WORKFLOW_ID fires via ghl_client when ghost engine marks contact ghosted."""

    @pytest.mark.asyncio
    async def test_cc_ghosting_workflow_triggered_on_ghost(self):
        """When mark_as_ghosted() is called with a ghl_client, CC_GHOSTING_WORKFLOW_ID is triggered."""
        contact_id = "ghost_contact_r002"
        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(return_value=None)  # dedup key absent
        mock_cache.set = AsyncMock(return_value=True)

        mock_ghl = AsyncMock()
        mock_ghl.trigger_workflow = AsyncMock(return_value={"status": "ok"})

        mock_settings = MagicMock()
        mock_settings.cc_ghosting_workflow_id = _CC_GHOSTING_WF_ID

        engine = GhostFollowUpEngine(ghl_client=mock_ghl)

        with (
            patch("ghl_real_estate_ai.services.ghost_followup_engine.get_cache_service", return_value=mock_cache),
            patch("ghl_real_estate_ai.ghl_utils.jorge_config.settings", mock_settings),
        ):
            await engine.mark_as_ghosted(contact_id)

        mock_ghl.trigger_workflow.assert_awaited_once_with(contact_id, _CC_GHOSTING_WF_ID)

    @pytest.mark.asyncio
    async def test_cc_ghosting_workflow_not_triggered_twice(self):
        """Dedup key prevents CC_GHOSTING_WORKFLOW_ID from firing a second time for same contact."""
        contact_id = "ghost_contact_r003"
        dedup_key = f"cc_wf_enrolled:{contact_id}:{_CC_GHOSTING_WF_ID[:8]}"

        mock_cache = AsyncMock()
        mock_cache.get = AsyncMock(side_effect=lambda k: "1" if k == dedup_key else None)
        mock_cache.set = AsyncMock(return_value=True)

        mock_ghl = AsyncMock()
        mock_ghl.trigger_workflow = AsyncMock(return_value={"status": "ok"})

        mock_settings = MagicMock()
        mock_settings.cc_ghosting_workflow_id = _CC_GHOSTING_WF_ID

        engine = GhostFollowUpEngine(ghl_client=mock_ghl)

        with (
            patch("ghl_real_estate_ai.services.ghost_followup_engine.get_cache_service", return_value=mock_cache),
            patch("ghl_real_estate_ai.ghl_utils.jorge_config.settings", mock_settings),
        ):
            await engine.mark_as_ghosted(contact_id)

        mock_ghl.trigger_workflow.assert_not_awaited()


class TestUnstaleFiresWhenGhostedContactMessages:
    """Part 3: Existing ghost_state='ghosted' + inbound message in webhook → cc_unstale fires."""

    @pytest.mark.asyncio
    async def test_unstale_fires_when_ghosted_contact_messages(self, cc_settings):
        """Ghosted contact re-engaging (new inbound message) triggers cc_unstale_lead_workflow_id."""
        contact_id = "ghost_contact_r004"
        ghost_key = f"ghost_state:{contact_id}"

        cache = _make_cache()
        cache.get = AsyncMock(side_effect=lambda k: "ghosted" if k == ghost_key else None)
        cache.set = AsyncMock(return_value=True)

        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=cache):
            actions = await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="Hey I'm back, still interested in selling",
                settings=cc_settings,
                is_new_lead=False,
                contact_id=contact_id,
            )

        triggered_ids = [a.workflow_id for a in actions if a.type == ActionType.TRIGGER_WORKFLOW]
        assert _CC_UNSTALE_WF_ID in triggered_ids, (
            f"Expected cc_unstale_lead_workflow_id to fire when ghosted contact sends new message. "
            f"Got: {triggered_ids}"
        )

    @pytest.mark.asyncio
    async def test_unstale_resets_ghost_state_to_active(self, cc_settings):
        """After unstale fires, ghost_state key is updated to 'active' (30-day TTL) to prevent re-trigger."""
        contact_id = "ghost_contact_r005"
        ghost_key = f"ghost_state:{contact_id}"

        cache = _make_cache()
        cache.get = AsyncMock(side_effect=lambda k: "ghosted" if k == ghost_key else None)
        cache.set = AsyncMock(return_value=True)

        with patch("ghl_real_estate_ai.api.routes.webhook.get_cache_service", return_value=cache):
            await _build_cc_workflow_actions(
                seller_result={"temperature": "warm"},
                user_message="I'm back and ready to sell",
                settings=cc_settings,
                is_new_lead=False,
                contact_id=contact_id,
            )

        set_calls = [(c.args[0], c.args[1]) for c in cache.set.call_args_list if len(c.args) >= 2]
        assert (ghost_key, "active") in set_calls, (
            f"Expected ghost_state key to be reset to 'active' after unstale. Set calls: {set_calls}"
        )
