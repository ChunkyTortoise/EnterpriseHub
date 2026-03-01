"""
Integration tests for CC DTS campaign workflow enrollment.
Tests that _build_cc_workflow_actions() enrolls contacts in the correct
CC-patterned workflows based on sentiment, temperature, lead status, and ghost state.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.routes.webhook import _build_cc_workflow_actions, _detect_negative_sentiment
from ghl_real_estate_ai.api.schemas.ghl import ActionType


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
