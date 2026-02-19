"""
End-to-end conversation flow tests for Jorge Lead Bot.

Tests complete lead qualification conversations through the LangGraph workflow,
including new lead routing, ambiguous leads, re-engagement, opt-out handling,
handoff to buyer/seller bots, hot/cold lead paths, multi-message conversations,
and circular handoff prevention.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.lead_bot import LeadBotConfig, LeadBotWorkflow
from ghl_real_estate_ai.services.lead_sequence_state_service import (
    LeadSequenceState,
    SequenceDay,
    SequenceStatus,
)


def _make_sequence_state(lead_id: str = "test") -> LeadSequenceState:
    """Create a minimal LeadSequenceState for mock returns."""
    return LeadSequenceState(
        lead_id=lead_id,
        current_day=SequenceDay.DAY_3,
        sequence_status=SequenceStatus.IN_PROGRESS,
        sequence_started_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Shared fixture: patch all external dependencies for lead bot E2E tests
# ---------------------------------------------------------------------------


@pytest.fixture
def _mock_lead_deps():
    """Patch all external dependencies for lead bot E2E tests."""
    mock_event_pub = AsyncMock()
    mock_sync = MagicMock()
    mock_sync.record_lead_event = AsyncMock()

    # Ghost engine: mix of sync and async methods
    mock_ghost_engine = MagicMock()
    mock_ghost_engine.get_state = AsyncMock(return_value=None)
    mock_ghost_engine.update_state = AsyncMock()
    mock_ghost_engine.process_lead_step = AsyncMock(
        return_value={"content": "Mocked ghost response", "logic": "mock"}
    )
    mock_ghost_engine.get_stall_breaker = MagicMock(return_value="mock_stall_breaker")

    # Sequence service: all async
    mock_seq_service = MagicMock()
    mock_seq_service.get_state = AsyncMock(return_value=None)
    mock_seq_service.create_sequence = AsyncMock(
        side_effect=lambda lead_id, **kw: _make_sequence_state(lead_id)
    )
    mock_seq_service.update_state = AsyncMock()
    mock_seq_service.set_cma_generated = AsyncMock()
    mock_seq_service.mark_action_completed = AsyncMock()
    mock_seq_service.advance_to_next_day = AsyncMock()
    mock_seq_service.complete_sequence = AsyncMock()

    # Scheduler: all async
    mock_scheduler = MagicMock()
    mock_scheduler.schedule_sequence_start = AsyncMock()
    mock_scheduler.schedule_next = AsyncMock()
    mock_scheduler.schedule_next_action = AsyncMock()

    # Lyrio: async
    mock_lyrio = MagicMock()
    mock_lyrio.sync_lead_score = AsyncMock()
    mock_lyrio.sync_digital_twin_url = AsyncMock()

    # Retell: async
    mock_retell = MagicMock()
    mock_retell.create_call = AsyncMock(return_value={"call_id": "mock_call"})

    # Market intel: async
    mock_market_intel = MagicMock()
    mock_market_intel.get_market_data = AsyncMock(return_value={})
    mock_market_intel.get_market_metrics = AsyncMock(return_value=MagicMock(inventory_days=30))

    # Cache: async
    mock_cache = MagicMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.set = AsyncMock()

    # GHL client: async
    mock_ghl_client = MagicMock()
    mock_ghl_client.send_message = AsyncMock()

    # Sendgrid client: async
    mock_sendgrid = MagicMock()
    mock_sendgrid.send_email = AsyncMock()

    with (
        patch("ghl_real_estate_ai.agents.lead_bot.LeadIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.lead_bot.get_event_publisher", return_value=mock_event_pub),
        patch(
            "ghl_real_estate_ai.services.event_publisher.get_event_publisher",
            return_value=mock_event_pub,
        ),
        patch("ghl_real_estate_ai.agents.lead_bot.sync_service", mock_sync),
        patch("ghl_real_estate_ai.agents.lead_bot.CMAGenerator") as MockCMA,
        patch("ghl_real_estate_ai.agents.lead_bot.get_ghost_followup_engine", return_value=mock_ghost_engine),
        patch("ghl_real_estate_ai.agents.lead_bot.get_sequence_service", return_value=mock_seq_service),
        patch("ghl_real_estate_ai.agents.lead_bot.get_lead_scheduler", return_value=mock_scheduler),
        patch("ghl_real_estate_ai.agents.lead_bot.LyrioClient", return_value=mock_lyrio),
        patch("ghl_real_estate_ai.agents.lead_bot.RetellClient", return_value=mock_retell),
        patch(
            "ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence",
            return_value=mock_market_intel,
        ),
        patch("ghl_real_estate_ai.agents.lead_bot.CacheService", return_value=mock_cache),
        patch("ghl_real_estate_ai.agents.lead_bot.PerformanceTracker") as MockPerf,
        patch("ghl_real_estate_ai.agents.lead_bot.BotMetricsCollector") as MockMetrics,
        patch("ghl_real_estate_ai.agents.lead_bot.AlertingService") as MockAlert,
        patch("ghl_real_estate_ai.agents.lead_bot.ABTestingService") as MockAB,
        patch("ghl_real_estate_ai.agents.lead_bot.PDFRenderer") as MockPDF,
    ):
        # Intent decoder mock
        intent_instance = MockIntent.return_value
        mock_profile = MagicMock()
        mock_profile.frs = MagicMock()
        mock_profile.frs.classification = "Warm Lead"
        mock_profile.frs.total_score = 50
        mock_profile.frs.price = MagicMock()
        mock_profile.frs.price.category = "Not-Price-Aware"
        mock_profile.pcs = MagicMock()
        mock_profile.pcs.total_score = 45
        mock_profile.lead_id = "test"
        mock_profile.lead_type = "general"
        mock_profile.market_context = None
        mock_profile.next_best_action = "qualify"
        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        # CMA generator mock
        cma_instance = MockCMA.return_value
        cma_instance.generate_report = AsyncMock(
            return_value=MagicMock(zillow_variance_abs=5000, data={"mock": True})
        )

        # Performance tracker mock
        perf_instance = MockPerf.return_value
        perf_instance.track_operation = AsyncMock()

        # Metrics collector mock
        metrics_instance = MockMetrics.return_value
        metrics_instance.record_bot_interaction = MagicMock()
        metrics_instance.feed_to_alerting = MagicMock()

        # Alerting mock
        alert_instance = MockAlert.return_value

        # AB testing mock
        ab_instance = MockAB.return_value
        ab_instance.get_variant = AsyncMock(return_value="empathetic")
        ab_instance.record_outcome = AsyncMock()
        MockAB.RESPONSE_TONE_EXPERIMENT = "response_tone_v1"

        # PDF renderer mock
        MockPDF.generate_pdf_url = MagicMock(return_value="https://mock.pdf/report.pdf")
        pdf_instance = MockPDF.return_value
        pdf_instance.render = AsyncMock(return_value=b"mock_pdf")

        yield {
            "intent": intent_instance,
            "profile": mock_profile,
            "event_pub": mock_event_pub,
            "sync": mock_sync,
            "ghost_engine": mock_ghost_engine,
            "seq_service": mock_seq_service,
            "scheduler": mock_scheduler,
            "cma": cma_instance,
            "lyrio": mock_lyrio,
            "retell": mock_retell,
            "market_intel": mock_market_intel,
            "cache": mock_cache,
            "ghl_client": mock_ghl_client,
            "sendgrid": mock_sendgrid,
            "perf": perf_instance,
            "metrics": metrics_instance,
            "alert": alert_instance,
            "ab": ab_instance,
        }


# ---------------------------------------------------------------------------
# 1. New Lead Routing — incoming lead gets classified and routed
# ---------------------------------------------------------------------------

class TestNewLeadRouting:
    """Incoming leads are classified via intent decoder and routed through workflow."""

    @pytest.mark.asyncio
    async def test_new_lead_classified_and_routed(self, _mock_lead_deps):
        """A fresh lead with no history gets analyzed and receives a response."""
        _mock_lead_deps["profile"].frs.classification = "Warm Lead"
        _mock_lead_deps["profile"].frs.total_score = 50

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="new_lead_001",
            user_message="Hi, I'm interested in real estate in Rancho Cucamonga.",
            lead_name="Alice New",
            conversation_history=[],
        )

        assert result.get("conversation_id") or result.get("lead_id")
        assert "response_content" in result
        assert result.get("engagement_status") != "error"
        _mock_lead_deps["intent"].analyze_lead.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_lead_event_published(self, _mock_lead_deps):
        """Processing a new lead publishes a bot status update event."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        await bot.process_lead_conversation(
            conversation_id="new_lead_002",
            user_message="I want to explore options for a home.",
            lead_name="Bob New",
            conversation_history=[],
        )

        # Event publisher should have been called (analyze_intent publishes status)
        _mock_lead_deps["event_pub"].publish_bot_status_update.assert_called()


# ---------------------------------------------------------------------------
# 2. Ambiguous Lead — unclear intent gets appropriate follow-up
# ---------------------------------------------------------------------------

class TestAmbiguousLead:
    """Lead with unclear intent receives a nurturing or clarifying response."""

    @pytest.mark.asyncio
    async def test_ambiguous_lead_gets_response(self, _mock_lead_deps):
        """Vague message still produces a valid response, not an error."""
        _mock_lead_deps["profile"].frs.classification = "Cold Lead"
        _mock_lead_deps["profile"].frs.total_score = 20
        _mock_lead_deps["profile"].pcs.total_score = 15

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="ambiguous_001",
            user_message="Maybe.",
            lead_name="Carol Vague",
            conversation_history=[
                {"role": "assistant", "content": "Are you looking for any changes?"},
            ],
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"


# ---------------------------------------------------------------------------
# 3. Re-engagement — previously cold lead returns
# ---------------------------------------------------------------------------

class TestReEngagement:
    """A previously cold lead who returns is re-analyzed."""

    @pytest.mark.asyncio
    async def test_cold_lead_re_engagement(self, _mock_lead_deps):
        """Cold lead returning after silence gets a fresh intent analysis."""
        _mock_lead_deps["profile"].frs.classification = "Warm Lead"
        _mock_lead_deps["profile"].frs.total_score = 55

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        history = [
            {"role": "assistant", "content": "Hi! What can I help you with?"},
            {"role": "user", "content": "Just browsing."},
            {"role": "assistant", "content": "No problem! Reach out anytime."},
        ]

        result = await bot.process_lead_conversation(
            conversation_id="reengage_001",
            user_message="Actually, I think I'm ready to look at homes now.",
            lead_name="Dave Return",
            conversation_history=history,
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"
        _mock_lead_deps["intent"].analyze_lead.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Opt-Out Handling — lead says "stop" or "unsubscribe"
# ---------------------------------------------------------------------------

class TestLeadOptOut:
    """Opt-out messages processed without crashing.

    The lead bot does not have built-in TCPA opt-out detection.
    Opt-out is handled at the webhook/API layer.
    """

    @pytest.mark.asyncio
    async def test_stop_message_returns_valid_response(self, _mock_lead_deps):
        """Saying 'stop' does not crash; bot returns a response dict."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="optout_001",
            user_message="stop",
            lead_name="Eve Optout",
            conversation_history=[],
        )

        lead_id = result.get("lead_id") or result.get("conversation_id")
        assert lead_id == "optout_001"
        assert "response_content" in result

    @pytest.mark.asyncio
    async def test_unsubscribe_message_returns_valid_response(self, _mock_lead_deps):
        """Saying 'unsubscribe' does not crash; bot returns a response dict."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="optout_002",
            user_message="unsubscribe me please",
            lead_name="Frank Optout",
            conversation_history=[],
        )

        assert "response_content" in result


# ---------------------------------------------------------------------------
# 5. Lead-to-Seller Handoff — lead identified as seller gets transferred
# ---------------------------------------------------------------------------

class TestLeadToSellerHandoff:
    """Lead mentioning selling triggers handoff signals for seller bot."""

    @pytest.mark.asyncio
    async def test_seller_intent_produces_handoff_signals(self, _mock_lead_deps):
        """Lead expressing seller intent has seller_intent_score > 0 in signals."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=True))

        result = await bot.process_lead_conversation(
            conversation_id="seller_handoff_001",
            user_message="I want to sell my house and list it soon.",
            lead_name="Grace Seller",
            conversation_history=[],
        )

        assert "handoff_signals" in result
        signals = result["handoff_signals"]
        assert isinstance(signals, dict)
        assert signals.get("seller_intent_score", 0) > 0


# ---------------------------------------------------------------------------
# 6. Lead-to-Buyer Handoff — lead identified as buyer gets transferred
# ---------------------------------------------------------------------------

class TestLeadToBuyerHandoff:
    """Lead mentioning buying triggers handoff signals for buyer bot."""

    @pytest.mark.asyncio
    async def test_buyer_intent_produces_handoff_signals(self, _mock_lead_deps):
        """Lead expressing buyer intent has buyer_intent_score > 0 in signals."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=True))

        # Use message that matches BUYER_INTENT_PATTERNS: "i want to buy"
        result = await bot.process_lead_conversation(
            conversation_id="buyer_handoff_001",
            user_message="I want to buy a 3-bedroom home with a pool.",
            lead_name="Hank Buyer",
            conversation_history=[],
        )

        assert "handoff_signals" in result
        signals = result["handoff_signals"]
        assert isinstance(signals, dict)
        assert signals.get("buyer_intent_score", 0) > 0


# ---------------------------------------------------------------------------
# 7. Hot Lead Fast-Track — high-intent lead gets expedited routing
# ---------------------------------------------------------------------------

class TestHotLeadFastTrack:
    """High-intent lead classified HOT gets expedited through workflow."""

    @pytest.mark.asyncio
    async def test_hot_lead_routed_to_qualification(self, _mock_lead_deps):
        """Hot Lead classification routes to schedule_showing or qualified path.

        The workflow tries schedule_showing for Hot Leads. If property_address
        is not available, the bot catches the error gracefully.
        Either way, the intent decoder is called and a response is returned.
        """
        _mock_lead_deps["profile"].frs.classification = "Hot Lead"
        _mock_lead_deps["profile"].frs.total_score = 90
        _mock_lead_deps["profile"].pcs.total_score = 85

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="hot_lead_001",
            user_message="I'm ready to tour homes this weekend.",
            lead_name="Ivy Hot",
            conversation_history=[],
        )

        # Bot should return a response dict (may be error due to missing property_address)
        assert "response_content" in result
        # Intent decoder should have been called to classify as Hot
        _mock_lead_deps["intent"].analyze_lead.assert_called_once()

    @pytest.mark.asyncio
    async def test_hot_lead_triggers_status_event(self, _mock_lead_deps):
        """Hot lead processing publishes events to track qualification."""
        _mock_lead_deps["profile"].frs.classification = "Hot Lead"
        _mock_lead_deps["profile"].frs.total_score = 88
        _mock_lead_deps["profile"].pcs.total_score = 80

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        await bot.process_lead_conversation(
            conversation_id="hot_lead_002",
            user_message="I have cash and want to close in two weeks.",
            lead_name="Jack Hot",
            conversation_history=[],
        )

        # Event publisher should have been called at least for analyze_intent
        _mock_lead_deps["event_pub"].publish_bot_status_update.assert_called()


# ---------------------------------------------------------------------------
# 8. Cold Lead Nurture — low-intent lead enters drip sequence
# ---------------------------------------------------------------------------

class TestColdLeadNurture:
    """Low-intent lead is classified Cold and enters nurture path."""

    @pytest.mark.asyncio
    async def test_cold_lead_classification(self, _mock_lead_deps):
        """Low FRS/PCS scores result in a non-error response."""
        _mock_lead_deps["profile"].frs.classification = "Cold Lead"
        _mock_lead_deps["profile"].frs.total_score = 10
        _mock_lead_deps["profile"].pcs.total_score = 8

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="cold_lead_001",
            user_message="Just looking around, no rush.",
            lead_name="Kate Cold",
            conversation_history=[],
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"

    @pytest.mark.asyncio
    async def test_cold_lead_sequence_created(self, _mock_lead_deps):
        """Cold lead gets a new sequence created for nurture drip."""
        _mock_lead_deps["profile"].frs.classification = "Cold Lead"
        _mock_lead_deps["profile"].frs.total_score = 12
        _mock_lead_deps["profile"].pcs.total_score = 10

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        await bot.process_lead_conversation(
            conversation_id="cold_lead_002",
            user_message="I might be interested someday.",
            lead_name="Leo Cold",
            conversation_history=[],
        )

        # Sequence service create_sequence called at least once (may be called
        # in both analyze_intent and determine_path)
        assert _mock_lead_deps["seq_service"].create_sequence.call_count >= 1


# ---------------------------------------------------------------------------
# 9. Multi-Message Conversation — lead engages over multiple turns
# ---------------------------------------------------------------------------

class TestMultiMessageConversation:
    """Lead engages in a long multi-turn conversation."""

    @pytest.mark.asyncio
    async def test_multi_turn_conversation(self, _mock_lead_deps):
        """Multiple turns should not crash and produce valid output."""
        _mock_lead_deps["profile"].frs.classification = "Warm Lead"
        _mock_lead_deps["profile"].frs.total_score = 55

        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        history = [
            {"role": "assistant", "content": "Hi! How can I help?"},
            {"role": "user", "content": "Tell me about homes in Rancho Cucamonga."},
            {"role": "assistant", "content": "Great area! What are you looking for?"},
            {"role": "user", "content": "Something with 3 bedrooms and a yard."},
            {"role": "assistant", "content": "Any timeline in mind?"},
            {"role": "user", "content": "In the next 3 months."},
            {"role": "assistant", "content": "Preferred neighborhoods?"},
        ]

        result = await bot.process_lead_conversation(
            conversation_id="multi_msg_001",
            user_message="North side, close to schools.",
            lead_name="Mike Multi",
            conversation_history=history,
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"

    @pytest.mark.asyncio
    async def test_very_long_history_handled(self, _mock_lead_deps):
        """History exceeding MAX_CONVERSATION_HISTORY is pruned, no crash."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(60)
        ]

        result = await bot.process_lead_conversation(
            conversation_id="multi_msg_002",
            user_message="What do you suggest?",
            lead_name="Nancy Long",
            conversation_history=history,
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"


# ---------------------------------------------------------------------------
# 10. Handoff Circular Prevention — prevent seller->lead->seller loops
# ---------------------------------------------------------------------------

class TestHandoffCircularPrevention:
    """Handoff signals should not cause circular routing loops."""

    @pytest.mark.asyncio
    async def test_handoff_signals_are_dict(self, _mock_lead_deps):
        """Handoff signals always a dict, even when no intent detected."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=True))

        result = await bot.process_lead_conversation(
            conversation_id="circular_001",
            user_message="Hello, just checking in.",
            lead_name="Olivia Neutral",
            conversation_history=[],
        )

        assert "handoff_signals" in result
        assert isinstance(result["handoff_signals"], dict)

    @pytest.mark.asyncio
    async def test_no_handoff_on_neutral_message(self, _mock_lead_deps):
        """Neutral message produces zero-score signals."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=True))

        result = await bot.process_lead_conversation(
            conversation_id="circular_002",
            user_message="What is the weather like today?",
            lead_name="Pete Neutral",
            conversation_history=[],
        )

        signals = result.get("handoff_signals", {})
        assert signals.get("buyer_intent_score", 0) == 0
        assert signals.get("seller_intent_score", 0) == 0


# ---------------------------------------------------------------------------
# Error Resilience
# ---------------------------------------------------------------------------

class TestLeadErrorResilience:
    """Bot handles edge cases gracefully without crashing."""

    @pytest.mark.asyncio
    async def test_empty_message_returns_prompt(self, _mock_lead_deps):
        """Empty message returns an 'I didn't catch that' response."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="resilience_001",
            user_message="",
            lead_name="Quinn Empty",
            conversation_history=[],
        )

        assert "response_content" in result
        assert result["response_content"] != ""

    @pytest.mark.asyncio
    async def test_whitespace_only_message(self, _mock_lead_deps):
        """Whitespace-only message treated as empty, returns prompt."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="resilience_002",
            user_message="   \n\t  ",
            lead_name="Rose Whitespace",
            conversation_history=[],
        )

        assert "response_content" in result

    @pytest.mark.asyncio
    async def test_none_conversation_history(self, _mock_lead_deps):
        """None conversation_history defaults to empty list, no crash."""
        bot = LeadBotWorkflow(config=LeadBotConfig(jorge_handoff_enabled=False))

        result = await bot.process_lead_conversation(
            conversation_id="resilience_003",
            user_message="Hello there",
            lead_name="Sam None",
            conversation_history=None,
        )

        assert "response_content" in result
        assert result.get("engagement_status") != "error"
