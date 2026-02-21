import pytest

pytestmark = pytest.mark.integration

"""
Integration tests for Jorge Seller Bot

Covers:
- Factory method creation (standard, progressive, enterprise)
- Feature config wiring (flags on/off)
- Seller intent classification (pricing inquiry, timeline, motivation, objection)
- CMA / pricing discussion handling
- Confrontational qualification flow
- PCS score calculation via intent decoder
- Temperature assessment (hot / warm / cold seller)
- Error handling (Claude API failures, missing data)
- Edge cases (empty messages, very long messages)

Uses unittest.mock for all external services (Claude API, GHL client, event publisher,
ML analytics engine). Follows patterns from test_buyer_bot.py.
"""

import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import (
    AdaptiveQuestionEngine,
    ConversationMemory,
    JorgeFeatureConfig,
    JorgeSellerBot,
    QualificationResult,
    get_jorge_seller_bot,
)
from ghl_real_estate_ai.models.lead_scoring import (
    ConditionRealism,
    FinancialReadinessScore,
    LeadIntentProfile,
    MotivationSignals,
    PriceResponsiveness,
    PsychologicalCommitmentScore,
    TimelineCommitment,
)

# ---------------------------------------------------------------------------
# Helpers to build mock intent profiles at various temperature levels
# ---------------------------------------------------------------------------


def _make_frs(total: float, classification: str) -> FinancialReadinessScore:
    return FinancialReadinessScore(
        total_score=total,
        motivation=MotivationSignals(score=int(total), detected_markers=[], category="Mixed Intent"),
        timeline=TimelineCommitment(score=int(total), category="Flexible"),
        condition=ConditionRealism(score=int(total), category="Negotiable"),
        price=PriceResponsiveness(score=int(total), zestimate_mentioned=False, category="Price-Flexible"),
        classification=classification,
    )


def _make_pcs(total: float) -> PsychologicalCommitmentScore:
    return PsychologicalCommitmentScore(
        total_score=total,
        response_velocity_score=int(total * 0.2),
        message_length_score=int(total * 0.2),
        question_depth_score=int(total * 0.2),
        objection_handling_score=int(total * 0.2),
        call_acceptance_score=int(total * 0.2),
    )


def _make_profile(
    lead_id: str = "seller_001",
    frs_total: float = 50.0,
    pcs_total: float = 50.0,
    classification: str = "Warm Lead",
) -> LeadIntentProfile:
    return LeadIntentProfile(
        lead_id=lead_id,
        frs=_make_frs(frs_total, classification),
        pcs=_make_pcs(pcs_total),
        lead_type="seller",
        next_best_action="Send Soft Check-in SMS",
    )


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_dependencies():
    """Patch core external service constructors so JorgeSellerBot can instantiate."""
    with (
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder") as mock_intent,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant") as mock_claude,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher") as mock_events,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine") as mock_ml,
    ):
        mock_intent_instance = MagicMock()
        mock_intent.return_value = mock_intent_instance

        mock_claude_instance = MagicMock()
        mock_claude_instance.analyze_with_context = AsyncMock(
            return_value={"content": "Jorge says hello, how can I help you today?"}
        )
        mock_claude.return_value = mock_claude_instance

        mock_events_instance = MagicMock()
        mock_events_instance.publish_bot_status_update = AsyncMock()
        mock_events_instance.publish_jorge_qualification_progress = AsyncMock()
        mock_events_instance.publish_conversation_update = AsyncMock()
        mock_events.return_value = mock_events_instance

        mock_ml_instance = MagicMock()
        mock_ml.return_value = mock_ml_instance

        yield {
            "intent_decoder_cls": mock_intent,
            "intent_decoder": mock_intent_instance,
            "claude_cls": mock_claude,
            "claude": mock_claude_instance,
            "event_publisher": mock_events_instance,
            "ml_analytics": mock_ml_instance,
        }


@pytest.fixture
def disabled_config():
    """Feature config with all optional features turned off."""
    return JorgeFeatureConfig(
        enable_progressive_skills=False,
        enable_agent_mesh=False,
        enable_mcp_integration=False,
        enable_adaptive_questioning=False,
        enable_track3_intelligence=False,
        enable_bot_intelligence=False,
    )


@pytest.fixture
def seller_state_warm():
    """A warm-seller JorgeSellerState dict for workflow node tests."""
    return {
        "lead_id": "seller_001",
        "lead_name": "Jane Smith",
        "property_address": "123 Main St, Rancho Cucamonga, CA",
        "conversation_history": [
            {"role": "user", "content": "I need to sell my home quickly, relocating in 30 days"},
            {"role": "assistant", "content": "I understand the urgency. What price range are you thinking?"},
            {"role": "user", "content": "I saw the zestimate is around $750k. Is that realistic?"},
        ],
        "intent_profile": None,
        "current_tone": "direct",
        "stall_detected": False,
        "detected_stall_type": None,
        "next_action": "respond",
        "response_content": "",
        "psychological_commitment": 0.0,
        "is_qualified": False,
        "current_journey_stage": "qualification",
        "follow_up_count": 0,
        "last_action_timestamp": None,
        "seller_temperature": "cold",
    }


# =========================================================================
# 1. Factory method creation
# =========================================================================


class TestFactoryMethods:
    """Verify the three factory methods produce bots with correct configs."""

    def test_create_standard_jorge(self, mock_dependencies):
        bot = JorgeSellerBot.create_standard_jorge(tenant_id="test_std")
        assert bot.tenant_id == "test_std"
        assert bot.config.enable_track3_intelligence is True
        assert bot.config.friendly_approach_enabled is True
        assert bot.config.enable_progressive_skills is False
        assert bot.config.enable_agent_mesh is False
        assert bot.config.enable_mcp_integration is False
        assert bot.config.enable_adaptive_questioning is False

    def test_create_progressive_jorge(self, mock_dependencies):
        bot = JorgeSellerBot.create_progressive_jorge(tenant_id="test_prog")
        assert bot.tenant_id == "test_prog"
        assert bot.config.enable_track3_intelligence is True
        assert bot.config.enable_progressive_skills is True
        assert bot.config.enable_bot_intelligence is True

    def test_create_enterprise_jorge(self, mock_dependencies):
        bot = JorgeSellerBot.create_enterprise_jorge(tenant_id="test_ent")
        assert bot.tenant_id == "test_ent"
        assert bot.config.enable_track3_intelligence is True
        assert bot.config.enable_progressive_skills is True
        assert bot.config.enable_agent_mesh is True
        assert bot.config.enable_mcp_integration is True
        assert bot.config.enable_adaptive_questioning is True
        assert bot.config.enable_bot_intelligence is True

    def test_get_jorge_seller_bot_standard(self, mock_dependencies):
        bot = get_jorge_seller_bot("standard")
        assert bot.config.enable_progressive_skills is False

    @patch.dict("os.environ", {"ENABLE_PROGRESSIVE_SKILLS": "true"}, clear=False)
    def test_get_jorge_seller_bot_progressive(self, mock_dependencies):
        """get_jorge_seller_bot loads from env vars, so set the env flag."""
        bot = get_jorge_seller_bot("progressive")
        assert bot.config.enable_progressive_skills is True

    @patch.dict(
        "os.environ",
        {
            "ENABLE_PROGRESSIVE_SKILLS": "true",
            "ENABLE_AGENT_MESH": "true",
            "ENABLE_MCP_INTEGRATION": "true",
            "ENABLE_ADAPTIVE_QUESTIONING": "true",
        },
        clear=False,
    )
    def test_get_jorge_seller_bot_enterprise(self, mock_dependencies):
        """get_jorge_seller_bot loads from env vars, so set all flags."""
        bot = get_jorge_seller_bot("enterprise")
        assert bot.config.enable_adaptive_questioning is True


# =========================================================================
# 2. Feature config dataclass wiring
# =========================================================================


class TestFeatureConfigWiring:
    """Ensure feature flags translate into correct component initialisation."""

    def test_default_config_values(self):
        config = JorgeFeatureConfig()
        assert config.enable_progressive_skills is False
        assert config.enable_agent_mesh is False
        assert config.enable_mcp_integration is False
        assert config.enable_adaptive_questioning is False
        assert config.enable_track3_intelligence is True
        assert config.enable_bot_intelligence is True
        assert config.max_concurrent_tasks == 5
        assert config.sla_response_time == 15
        assert config.cost_per_token == 0.000015
        assert config.commission_rate == 0.06
        assert config.friendly_approach_enabled is True
        assert config.temperature_thresholds == {"hot": 75, "warm": 50, "lukewarm": 25}

    def test_custom_temperature_thresholds(self):
        config = JorgeFeatureConfig(temperature_thresholds={"hot": 90, "warm": 70, "lukewarm": 40})
        assert config.temperature_thresholds["hot"] == 90

    def test_all_disabled_produces_no_optional_services(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        assert bot.skills_manager is None
        assert bot.token_tracker is None
        assert bot.mesh_coordinator is None
        assert bot.mcp_client is None
        assert bot.conversation_memory is None
        assert bot.question_engine is None
        assert bot.ml_analytics is None
        assert bot.intelligence_middleware is None

    def test_adaptive_questioning_creates_memory_and_engine(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert isinstance(bot.conversation_memory, ConversationMemory)
        assert isinstance(bot.question_engine, AdaptiveQuestionEngine)

    def test_workflow_stats_initialised_to_zero(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        for key, val in bot.workflow_stats.items():
            assert val == 0, f"Expected 0 for workflow_stats['{key}'], got {val}"


# =========================================================================
# 3. Temperature classification
# =========================================================================


class TestTemperatureClassification:
    """Verify stall_detector.classify_temperature maps combined scores correctly."""

    def test_hot_seller_temperature(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        profile = _make_profile(frs_total=50, pcs_total=50)  # combined = 100
        assert bot.stall_detector.classify_temperature(profile) == "hot"

    def test_warm_seller_temperature(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        profile = _make_profile(frs_total=30, pcs_total=25)  # combined = 55
        assert bot.stall_detector.classify_temperature(profile) == "warm"

    def test_cold_seller_temperature(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        profile = _make_profile(frs_total=15, pcs_total=15)  # combined = 30
        assert bot.stall_detector.classify_temperature(profile) == "cold"

    def test_boundary_hot_threshold(self, mock_dependencies, disabled_config):
        """Score of exactly 75 should classify as hot."""
        bot = JorgeSellerBot(config=disabled_config)
        profile = _make_profile(frs_total=40, pcs_total=35)  # combined = 75
        assert bot.stall_detector.classify_temperature(profile) == "hot"

    def test_boundary_warm_threshold(self, mock_dependencies, disabled_config):
        """Score of exactly 50 should classify as warm."""
        bot = JorgeSellerBot(config=disabled_config)
        profile = _make_profile(frs_total=25, pcs_total=25)  # combined = 50
        assert bot.stall_detector.classify_temperature(profile) == "warm"


# =========================================================================
# 4. Stall detection node
# =========================================================================


class TestStallDetection:
    """Verify the detect_stall workflow node identifies stalling language."""

    @pytest.fixture
    def bot(self, mock_dependencies, disabled_config):
        return JorgeSellerBot(config=disabled_config)

    @pytest.mark.asyncio
    async def test_detects_thinking_stall(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = [{"role": "user", "content": "I'm still thinking about it"}]
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is True
        assert result["detected_stall_type"] == "thinking"

    @pytest.mark.asyncio
    async def test_detects_get_back_stall(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = [{"role": "user", "content": "I'll get back to you later"}]
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is True
        assert result["detected_stall_type"] == "get_back"

    @pytest.mark.asyncio
    async def test_detects_zestimate_stall(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = [
            {"role": "user", "content": "The Zestimate says my home is worth 800k"}
        ]
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is True
        assert result["detected_stall_type"] == "zestimate"

    @pytest.mark.asyncio
    async def test_detects_agent_stall(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = [{"role": "user", "content": "I already have an agent"}]
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is True
        assert result["detected_stall_type"] == "agent"

    @pytest.mark.asyncio
    async def test_no_stall_when_genuine_interest(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = [
            {"role": "user", "content": "What can you tell me about pricing in my neighborhood?"}
        ]
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is False
        assert result["detected_stall_type"] is None

    @pytest.mark.asyncio
    async def test_stall_with_empty_conversation(self, bot, seller_state_warm):
        seller_state_warm["conversation_history"] = []
        result = await bot.detect_stall(seller_state_warm)
        assert result["stall_detected"] is False


# =========================================================================
# 5. Analyze intent node
# =========================================================================


class TestAnalyzeIntent:
    """Verify the analyze_intent workflow node wires through to the decoder."""

    @pytest.mark.asyncio
    async def test_analyze_intent_returns_profile_and_temperature(
        self, mock_dependencies, disabled_config, seller_state_warm
    ):
        profile = _make_profile(frs_total=80, pcs_total=70, classification="Hot Lead")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.analyze_intent(seller_state_warm)

        assert result["intent_profile"] is profile
        assert result["psychological_commitment"] == 70.0
        assert result["is_qualified"] is True
        assert result["seller_temperature"] == "hot"
        assert result["last_action_timestamp"] is not None

    @pytest.mark.asyncio
    async def test_analyze_intent_cold_seller_not_qualified(
        self, mock_dependencies, disabled_config, seller_state_warm
    ):
        profile = _make_profile(frs_total=15, pcs_total=10, classification="Cold")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.analyze_intent(seller_state_warm)

        assert result["is_qualified"] is False
        assert result["seller_temperature"] == "cold"

    @pytest.mark.asyncio
    async def test_analyze_intent_emits_events(self, mock_dependencies, disabled_config, seller_state_warm):
        profile = _make_profile(frs_total=60, pcs_total=60, classification="Warm Lead")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        # Override event_publisher to use the test mock (base class sets its own)
        bot.event_publisher = mock_dependencies["event_publisher"]
        await bot.analyze_intent(seller_state_warm)

        mock_dependencies["event_publisher"].publish_bot_status_update.assert_called()
        mock_dependencies["event_publisher"].publish_jorge_qualification_progress.assert_called()


# =========================================================================
# 6. Strategy selection
# =========================================================================


class TestStrategySelection:
    """Verify select_strategy chooses tone based on PCS and stall state."""

    @pytest.fixture
    def bot(self, mock_dependencies, disabled_config):
        return JorgeSellerBot(config=disabled_config)

    def _state_with(self, seller_state_warm, pcs, stall=False, stall_type=None):
        s = dict(seller_state_warm)
        s["psychological_commitment"] = pcs
        s["stall_detected"] = stall
        s["detected_stall_type"] = stall_type
        s["intent_profile"] = _make_profile(pcs_total=pcs)
        return s

    @pytest.mark.asyncio
    async def test_understanding_tone_on_stall(self, bot, seller_state_warm):
        state = self._state_with(seller_state_warm, pcs=50, stall=True, stall_type="thinking")
        result = await bot.select_strategy(state)
        assert result["current_tone"] == "UNDERSTANDING"

    @pytest.mark.asyncio
    async def test_educational_tone_for_low_commitment(self, bot, seller_state_warm):
        state = self._state_with(seller_state_warm, pcs=20)
        result = await bot.select_strategy(state)
        assert result["current_tone"] == "EDUCATIONAL"

    @pytest.mark.asyncio
    async def test_enthusiastic_tone_for_high_commitment(self, bot, seller_state_warm):
        state = self._state_with(seller_state_warm, pcs=80)
        result = await bot.select_strategy(state)
        assert result["current_tone"] == "ENTHUSIASTIC"

    @pytest.mark.asyncio
    async def test_consultative_tone_for_mid_commitment(self, bot, seller_state_warm):
        state = self._state_with(seller_state_warm, pcs=50)
        result = await bot.select_strategy(state)
        assert result["current_tone"] == "CONSULTATIVE"


# =========================================================================
# 7. Generate Jorge response
# =========================================================================


class TestGenerateJorgeResponse:
    """Verify response generation calls Claude and returns content."""

    @pytest.mark.asyncio
    async def test_response_generated_from_claude(self, mock_dependencies, disabled_config, seller_state_warm):
        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["intent_profile"] = _make_profile()
        seller_state_warm["current_tone"] = "CONSULTATIVE"
        seller_state_warm["stall_detected"] = False
        seller_state_warm["detected_stall_type"] = None
        seller_state_warm["seller_temperature"] = "warm"

        result = await bot.generate_jorge_response(seller_state_warm)
        assert "response_content" in result
        assert len(result["response_content"]) > 0
        mock_dependencies["claude"].analyze_with_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_response_uses_stall_template_when_stall(self, mock_dependencies, disabled_config, seller_state_warm):
        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["intent_profile"] = _make_profile()
        seller_state_warm["current_tone"] = "UNDERSTANDING"
        seller_state_warm["stall_detected"] = True
        seller_state_warm["detected_stall_type"] = "zestimate"
        seller_state_warm["seller_temperature"] = "cold"

        await bot.generate_jorge_response(seller_state_warm)

        # The prompt sent to Claude should contain the zestimate stall template
        call_args = mock_dependencies["claude"].analyze_with_context.call_args
        prompt_text = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
        assert "zestimate" in prompt_text.lower() or "online estimates" in prompt_text.lower()

    @pytest.mark.asyncio
    async def test_response_fallback_on_claude_empty(self, mock_dependencies, disabled_config, seller_state_warm):
        """When Claude returns empty content/analysis, fallback message is used."""
        mock_dependencies["claude"].analyze_with_context = AsyncMock(return_value={})

        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["intent_profile"] = _make_profile()
        seller_state_warm["current_tone"] = "CONSULTATIVE"
        seller_state_warm["stall_detected"] = False
        seller_state_warm["detected_stall_type"] = None
        seller_state_warm["seller_temperature"] = "warm"

        result = await bot.generate_jorge_response(seller_state_warm)
        # Should fall back to the hardcoded default (friendly tone)
        assert (
            result["response_content"]
            == "Happy to help with any questions about your property. What would be most useful to know?"
        )


# =========================================================================
# 8. Execute follow-up
# =========================================================================


class TestExecuteFollowUp:
    """Verify follow-up execution increments counter and uses correct template."""

    @pytest.mark.asyncio
    async def test_follow_up_increments_count(self, mock_dependencies, disabled_config, seller_state_warm):
        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["follow_up_count"] = 2
        result = await bot.execute_follow_up(seller_state_warm)
        assert result["follow_up_count"] == 3

    @pytest.mark.asyncio
    async def test_follow_up_uses_stage_template(self, mock_dependencies, disabled_config, seller_state_warm):
        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["current_journey_stage"] = "listing_prep"
        result = await bot.execute_follow_up(seller_state_warm)
        assert "photographer" in result["response_content"].lower()


# =========================================================================
# 9. Process seller message (end-to-end workflow invocation)
# =========================================================================


class TestProcessSellerMessage:
    """Integration test: the full LangGraph workflow invocation."""

    @pytest.mark.asyncio
    async def test_process_seller_message_returns_response(self, mock_dependencies, disabled_config):
        profile = _make_profile(frs_total=60, pcs_total=55, classification="Warm Lead")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.process_seller_message(
            conversation_id="seller_001",
            user_message="I want to sell my home in Victoria",
            seller_name="Jane Smith",
        )

        assert result["response_content"]
        assert "lead_id" in result

    @pytest.mark.asyncio
    async def test_process_seller_message_with_stall(self, mock_dependencies, disabled_config):
        profile = _make_profile(frs_total=30, pcs_total=20, classification="Lukewarm")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.process_seller_message(
            conversation_id="seller_002",
            user_message="Let me think about it, I'll get back to you later",
            seller_name="Bob Jones",
        )

        assert result["response_content"]
        assert "lead_id" in result


# =========================================================================
# 10. Routing helpers
# =========================================================================


class TestRouting:
    """Verify _route_seller_action and _route_adaptive_action."""

    @pytest.fixture
    def bot(self, mock_dependencies, disabled_config):
        return JorgeSellerBot(config=disabled_config)

    def test_route_respond(self, bot):
        assert bot._route_seller_action({"next_action": "respond"}) == "respond"

    def test_route_follow_up(self, bot):
        assert bot._route_seller_action({"next_action": "follow_up"}) == "follow_up"

    def test_route_end(self, bot):
        assert bot._route_seller_action({"next_action": "end"}) == "end"

    def test_adaptive_route_fast_track(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert (
            bot._route_adaptive_action({"adaptive_mode": "calendar_focused", "next_action": "respond"}) == "fast_track"
        )

    def test_adaptive_route_end(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        assert bot._route_adaptive_action({"adaptive_mode": "standard_qualification", "next_action": "end"}) == "end"


# =========================================================================
# 11. PCS score wiring (intent decoder integration)
# =========================================================================


class TestPCSScoreCalculation:
    """Verify that PCS scores from the intent decoder propagate correctly."""

    @pytest.mark.asyncio
    async def test_high_pcs_qualifies_lead(self, mock_dependencies, disabled_config, seller_state_warm):
        profile = _make_profile(frs_total=80, pcs_total=85, classification="Hot Lead")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.analyze_intent(seller_state_warm)
        assert result["psychological_commitment"] == 85.0
        assert result["is_qualified"] is True

    @pytest.mark.asyncio
    async def test_low_pcs_does_not_qualify(self, mock_dependencies, disabled_config, seller_state_warm):
        profile = _make_profile(frs_total=10, pcs_total=5, classification="Cold")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.analyze_intent(seller_state_warm)
        assert result["psychological_commitment"] == 5.0
        assert result["is_qualified"] is False


# =========================================================================
# 12. Conversation memory (adaptive feature)
# =========================================================================


class TestConversationMemory:
    """Unit tests for the ConversationMemory helper class."""

    @pytest.mark.asyncio
    async def test_empty_context_returns_defaults(self):
        memory = ConversationMemory()
        ctx = await memory.get_context("new_convo")
        assert ctx["last_scores"] is None
        assert ctx["question_history"] == []
        assert ctx["adaptation_count"] == 0

    @pytest.mark.asyncio
    async def test_update_and_retrieve_context(self):
        memory = ConversationMemory()
        await memory.update_context("c1", {"adaptation_count": 3, "last_scores": {"frs": 80}})
        ctx = await memory.get_context("c1")
        assert ctx["adaptation_count"] == 3
        assert ctx["last_scores"]["frs"] == 80


# =========================================================================
# 13. Adaptive question engine
# =========================================================================


class TestAdaptiveQuestionEngine:
    """Unit tests for the AdaptiveQuestionEngine helper class."""

    @pytest.fixture
    def engine(self):
        return AdaptiveQuestionEngine()

    def test_core_questions_populated(self, engine):
        assert len(engine.jorge_core_questions) == 4

    def test_high_intent_accelerators_populated(self, engine):
        assert len(engine.high_intent_accelerators) > 0

    def test_supportive_clarifiers_has_keys(self, engine):
        assert "zestimate" in engine.supportive_clarifiers
        assert "thinking" in engine.supportive_clarifiers
        assert "agent" in engine.supportive_clarifiers

    @pytest.mark.asyncio
    async def test_select_standard_question_first(self, engine):
        state = {"current_question": 1, "intent_profile": _make_profile(pcs_total=30)}
        question = await engine._select_standard_question(state)
        assert question == engine.jorge_core_questions[0]

    @pytest.mark.asyncio
    async def test_select_standard_question_overflow(self, engine):
        state = {"current_question": 10, "intent_profile": _make_profile(pcs_total=30)}
        question = await engine._select_standard_question(state)
        assert "property goals" in question.lower()


# =========================================================================
# 14. Error handling
# =========================================================================


class TestErrorHandling:
    """Verify graceful degradation on external service failures."""

    @pytest.mark.asyncio
    async def test_claude_api_exception_in_response_generation(
        self, mock_dependencies, disabled_config, seller_state_warm
    ):
        mock_dependencies["claude"].analyze_with_context = AsyncMock(side_effect=Exception("Claude API rate limit"))
        bot = JorgeSellerBot(config=disabled_config)
        seller_state_warm["intent_profile"] = _make_profile()
        seller_state_warm["current_tone"] = "CONSULTATIVE"
        seller_state_warm["stall_detected"] = False
        seller_state_warm["detected_stall_type"] = None
        seller_state_warm["seller_temperature"] = "warm"

        with pytest.raises(Exception, match="Claude API rate limit"):
            await bot.generate_jorge_response(seller_state_warm)

    @pytest.mark.asyncio
    async def test_strategy_fallback_when_ml_fails(self, mock_dependencies, disabled_config, seller_state_warm):
        """When Track 3.1 ML calls fail, strategy falls back to base logic."""
        bot = JorgeSellerBot(config=disabled_config)

        # Inject a failing ML analytics mock
        ml_mock = MagicMock()
        ml_mock.predict_lead_journey = AsyncMock(side_effect=Exception("ML down"))
        bot.ml_analytics = ml_mock

        state = dict(seller_state_warm)
        state["psychological_commitment"] = 50
        state["stall_detected"] = False
        state["detected_stall_type"] = None
        state["intent_profile"] = _make_profile(pcs_total=50)

        result = await bot.select_strategy(state)
        # Should still return a valid strategy via fallback
        assert result["current_tone"] == "CONSULTATIVE"
        assert result["next_action"] == "respond"


# =========================================================================
# 15. Edge cases
# =========================================================================


class TestEdgeCases:
    """Edge cases: empty messages, very long messages, missing data."""

    @pytest.mark.asyncio
    async def test_empty_message_history(self, mock_dependencies, disabled_config):
        profile = _make_profile(frs_total=20, pcs_total=10, classification="Cold")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.process_seller_message(
            conversation_id="seller_empty",
            user_message="Hello",
            seller_name="Empty User",
        )
        assert result["response_content"]

    @pytest.mark.asyncio
    async def test_very_long_message(self, mock_dependencies, disabled_config):
        long_text = "I want to sell my house " * 500
        profile = _make_profile(frs_total=50, pcs_total=50, classification="Warm Lead")
        mock_dependencies["intent_decoder"].analyze_lead.return_value = profile

        bot = JorgeSellerBot(config=disabled_config)
        result = await bot.process_seller_message(
            conversation_id="seller_long",
            user_message=long_text,
            seller_name="Verbose User",
        )
        assert result["response_content"]

    def test_confidence_to_temperature_boundaries(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        assert bot._confidence_to_temperature(0.9) == "hot"
        assert bot._confidence_to_temperature(0.8) == "hot"
        assert bot._confidence_to_temperature(0.7) == "warm"
        assert bot._confidence_to_temperature(0.6) == "warm"
        assert bot._confidence_to_temperature(0.5) == "lukewarm"
        assert bot._confidence_to_temperature(0.4) == "lukewarm"
        assert bot._confidence_to_temperature(0.3) == "cold"
        assert bot._confidence_to_temperature(0.0) == "cold"

    def test_extract_city_from_full_address(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        assert bot._extract_city("123 Main St, Rancho Cucamonga, CA 91730") == "Rancho Cucamonga"

    def test_extract_city_fallback(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        # With fewer than 3 parts, should default to Phoenix
        assert bot._extract_city("some address") == "Phoenix"

    def test_is_rancho_cucamonga_property(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        assert bot._is_rancho_cucamonga_property("123 Main St, Rancho Cucamonga, CA") is True
        assert bot._is_rancho_cucamonga_property(None) is False
        assert bot._is_rancho_cucamonga_property("456 Oak Ave, Phoenix, AZ") is False


# =========================================================================
# 16. Health check and performance metrics
# =========================================================================


class TestHealthCheckAndMetrics:
    """Verify health check and performance metrics return valid structures."""

    @pytest.mark.asyncio
    async def test_health_check_all_disabled(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        health = await bot.health_check()
        assert health["jorge_bot"] == "healthy"
        assert health["overall_status"] == "healthy"
        assert health["track3_intelligence"] == "disabled"
        assert health["progressive_skills"] == "disabled"

    @pytest.mark.asyncio
    async def test_health_check_adaptive_healthy(self, mock_dependencies):
        config = JorgeFeatureConfig(
            enable_adaptive_questioning=True,
            enable_track3_intelligence=False,
            enable_bot_intelligence=False,
        )
        bot = JorgeSellerBot(config=config)
        health = await bot.health_check()
        assert health["adaptive_questioning"] == "healthy"

    @pytest.mark.asyncio
    async def test_performance_metrics_structure(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        metrics = await bot.get_performance_metrics()
        assert "workflow_statistics" in metrics
        assert "features_enabled" in metrics
        assert metrics["features_enabled"]["track3_intelligence"] is False

    @pytest.mark.asyncio
    async def test_shutdown_no_error(self, mock_dependencies, disabled_config):
        bot = JorgeSellerBot(config=disabled_config)
        await bot.shutdown()  # Should not raise


# =========================================================================
# 17. QualificationResult dataclass
# =========================================================================


class TestQualificationResult:
    """Verify QualificationResult defaults and post_init."""

    def test_defaults(self):
        qr = QualificationResult(
            lead_id="lead_1",
            qualification_score=80.0,
            frs_score=70.0,
            pcs_score=75.0,
            temperature="hot",
            next_actions=["call now"],
            confidence=0.9,
            tokens_used=200,
            cost_incurred=0.003,
        )
        assert qr.progressive_skills_applied is False
        assert qr.mesh_task_id is None
        assert qr.orchestrated_tasks == []
        assert qr.mcp_enrichment_applied is False
        assert qr.adaptive_questioning_used is False
        assert qr.timeline_ms == {}

    def test_custom_orchestrated_tasks(self):
        qr = QualificationResult(
            lead_id="lead_2",
            qualification_score=50.0,
            frs_score=40.0,
            pcs_score=45.0,
            temperature="warm",
            next_actions=[],
            confidence=0.6,
            tokens_used=100,
            cost_incurred=0.001,
            orchestrated_tasks=["task_1", "task_2"],
        )
        assert len(qr.orchestrated_tasks) == 2


# ---------------------------------------------------------------------------
# Phase 1+3: CMA, Market Intelligence, Listing Prep, Property Condition Tests
# ---------------------------------------------------------------------------


class TestSellerBotCMAAndMarket:
    """Test CMA generation, market analysis, and valuation defense."""

    @pytest.fixture
    def mock_seller_deps(self):
        """Patch core external service constructors so JorgeSellerBot can instantiate."""
        with (
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder") as mock_intent,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.SellerIntentDecoder") as mock_seller_intent,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant") as mock_claude,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher") as mock_events,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine") as mock_ml,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.CMAGenerator") as mock_cma,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_market_intelligence") as mock_market,
        ):
            mock_intent_instance = MagicMock()
            mock_intent_instance.analyze_lead.return_value = _make_profile()
            mock_intent.return_value = mock_intent_instance

            mock_seller_intent_instance = MagicMock()
            mock_seller_intent.return_value = mock_seller_intent_instance

            mock_claude_instance = MagicMock()
            mock_claude_instance.analyze_with_context = AsyncMock(return_value={"content": "Test response"})
            mock_claude.return_value = mock_claude_instance

            mock_events_instance = MagicMock()
            mock_events_instance.publish_bot_status_update = AsyncMock()
            mock_events_instance.publish_jorge_qualification_progress = AsyncMock()
            mock_events_instance.publish_conversation_update = AsyncMock()
            mock_events.return_value = mock_events_instance

            mock_ml_instance = MagicMock()
            mock_ml_instance.predict_lead_journey = AsyncMock(
                return_value=MagicMock(
                    conversion_probability=0.5,
                    stage_progression_velocity=0.3,
                    processing_time_ms=10,
                )
            )
            mock_ml_instance.predict_conversion_probability = AsyncMock(
                return_value=MagicMock(
                    urgency_score=50,
                    optimal_action="respond",
                    processing_time_ms=10,
                )
            )
            mock_ml_instance.predict_optimal_touchpoints = AsyncMock(
                return_value=MagicMock(
                    response_pattern="standard",
                    processing_time_ms=10,
                )
            )
            mock_ml.return_value = mock_ml_instance

            mock_cma_instance = MagicMock()
            mock_cma.return_value = mock_cma_instance

            mock_market_instance = MagicMock()
            mock_market.return_value = mock_market_instance

            yield {
                "intent": mock_intent_instance,
                "seller_intent": mock_seller_intent_instance,
                "claude": mock_claude_instance,
                "events": mock_events_instance,
                "ml": mock_ml_instance,
                "cma": mock_cma_instance,
                "market": mock_market_instance,
            }

    def _make_seller_state(self, **overrides):
        """Create a seller state dict with defaults."""
        state = {
            "lead_id": "test_seller_001",
            "lead_name": "Test Seller",
            "property_address": "123 Main St, Rancho Cucamonga, CA",
            "conversation_history": [
                {"role": "user", "content": "I want to sell my house"},
            ],
            "intent_profile": _make_profile(),
            "current_tone": "CONSULTATIVE",
            "stall_detected": False,
            "detected_stall_type": None,
            "next_action": "respond",
            "response_content": "",
            "psychological_commitment": 50.0,
            "is_qualified": True,
            "current_journey_stage": "qualification",
            "follow_up_count": 0,
            "last_action_timestamp": None,
            "tone_variant": "empathetic",
            "adaptive_mode": "standard",
            "adaptive_question_used": None,
            "adaptation_applied": False,
            "memory_updated": False,
            "cma_report": None,
            "estimated_value": None,
            "listing_price_recommendation": None,
            "zestimate": None,
            "property_condition": None,
            "repair_estimates": None,
            "staging_recommendations": None,
            "market_data": None,
            "market_trend": None,
            "comparable_properties": None,
            "seller_intent_profile": None,
        }
        state.update(overrides)
        return state

    @pytest.mark.asyncio
    async def test_generate_cma_with_address(self, mock_seller_deps):
        """Test CMA generation when address is available."""
        from datetime import date

        from ghl_real_estate_ai.models.cma import CMAProperty, CMAReport, Comparable, MarketContext

        mock_report = MagicMock()
        mock_report.estimated_value = 850000
        mock_report.value_range_low = 807500
        mock_report.value_range_high = 892500
        mock_report.confidence_score = 88
        mock_report.zillow_variance_percent = 5.0
        mock_report.zillow_explanation = "CMA shows higher value"
        mock_report.market_narrative = "Market is strong"
        mock_report.comparables = [
            MagicMock(address="456 Oak", sale_price=840000, sqft=2800, beds=4, baths=3.0, price_per_sqft=300),
        ]
        mock_report.market_context = MagicMock(
            market_name="Rancho Cucamonga, CA",
            price_trend=12.5,
            dom_average=28,
            inventory_level=1450,
        )

        mock_seller_deps["cma"].generate_report = AsyncMock(return_value=mock_report)

        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state()
        result = await bot.generate_cma(state)

        assert result.get("cma_report") is not None
        assert result["estimated_value"] == 850000
        assert len(result["comparable_properties"]) == 1
        assert result["market_data"]["dom_average"] == 28

    @pytest.mark.asyncio
    async def test_generate_cma_without_address(self, mock_seller_deps):
        """Test CMA generation skips when no address."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(property_address=None)
        result = await bot.generate_cma(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_generate_cma_handles_error(self, mock_seller_deps):
        """Test CMA gracefully handles generation errors."""
        mock_seller_deps["cma"].generate_report = AsyncMock(side_effect=Exception("CMA service unavailable"))
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state()
        result = await bot.generate_cma(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_market_conditions_sellers_market(self, mock_seller_deps):
        """Test sellers market classification (low inventory)."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            market_data={"inventory_level": 1000}  # 1000/480 ≈ 2.08 months = sellers
        )
        result = await bot.analyze_market_conditions(state)
        assert result["market_trend"] == "sellers_market"

    @pytest.mark.asyncio
    async def test_market_conditions_buyers_market(self, mock_seller_deps):
        """Test buyers market classification (high inventory)."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            market_data={"inventory_level": 4000}  # 4000/480 ≈ 8.33 months = buyers
        )
        result = await bot.analyze_market_conditions(state)
        assert result["market_trend"] == "buyers_market"

    @pytest.mark.asyncio
    async def test_market_conditions_balanced(self, mock_seller_deps):
        """Test balanced market classification."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            market_data={"inventory_level": 2000}  # 2000/480 ≈ 4.17 months = balanced
        )
        result = await bot.analyze_market_conditions(state)
        assert result["market_trend"] == "balanced"

    @pytest.mark.asyncio
    async def test_valuation_defense_with_cma(self, mock_seller_deps):
        """Test valuation defense generates response with CMA data."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            cma_report={
                "estimated_value": 850000,
                "zillow_variance_percent": 5.0,
                "zillow_explanation": "CMA shows higher value",
                "market_narrative": "Strong market",
            },
            comparable_properties=[{"address": "456 Oak"}],
        )
        result = await bot.defend_valuation(state)
        assert "response_content" in result

    @pytest.mark.asyncio
    async def test_valuation_defense_without_cma(self, mock_seller_deps):
        """Test valuation defense skips without CMA data."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state()
        result = await bot.defend_valuation(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_route_after_stall_zestimate(self, mock_seller_deps):
        """Test routing to valuation defense on Zestimate stall."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            detected_stall_type="zestimate",
            cma_report={"estimated_value": 850000},
        )
        result = bot._route_after_stall_detection(state)
        assert result == "defend_valuation"

    @pytest.mark.asyncio
    async def test_route_after_stall_no_zestimate(self, mock_seller_deps):
        """Test routing to strategy when no Zestimate stall."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(detected_stall_type="thinking")
        result = bot._route_after_stall_detection(state)
        assert result == "select_strategy"

    @pytest.mark.asyncio
    async def test_market_context_injected_into_prompt(self, mock_seller_deps):
        """Test that CMA data is injected into response generation prompt."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_seller_state(
            cma_report={"estimated_value": 850000},
            market_trend="sellers_market",
            market_data={"dom_average": 28},
            comparable_properties=[{"address": "456 Oak"}],
            stall_detected=False,
        )
        result = await bot.generate_jorge_response(state)
        assert "response_content" in result

        # Verify Claude was called with market data in prompt
        call_args = bot.claude.analyze_with_context.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
        assert "$850,000" in prompt or "850,000" in prompt

    def test_property_condition_extraction_move_in_ready(self, mock_seller_deps):
        """Test move-in ready condition extraction."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        history = [
            {"role": "user", "content": "The house is turnkey, recently renovated"},
        ]
        result = bot.stall_detector.extract_property_condition(history)
        assert result == "move_in_ready"

    def test_property_condition_extraction_needs_work(self, mock_seller_deps):
        """Test needs-work condition extraction."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        history = [
            {"role": "user", "content": "It needs work, the kitchen is dated"},
        ]
        result = bot.stall_detector.extract_property_condition(history)
        assert result == "needs_work"

    def test_property_condition_extraction_major_repairs(self, mock_seller_deps):
        """Test major repairs condition extraction."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        history = [
            {"role": "user", "content": "It's a fixer with foundation issues"},
        ]
        result = bot.stall_detector.extract_property_condition(history)
        assert result == "major_repairs"

    def test_property_condition_extraction_none(self, mock_seller_deps):
        """Test no condition extracted from generic conversation."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        history = [
            {"role": "user", "content": "I want to sell my house"},
        ]
        result = bot.stall_detector.extract_property_condition(history)
        assert result is None


class TestSellerBotListingPrep:
    """Test listing preparation node."""

    @pytest.fixture
    def mock_seller_deps(self):
        with (
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder") as mock_intent,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.SellerIntentDecoder"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher") as mock_events,
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.CMAGenerator"),
            patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_market_intelligence"),
        ):
            mock_intent.return_value = MagicMock()
            mock_events_instance = MagicMock()
            mock_events_instance.publish_bot_status_update = AsyncMock()
            mock_events.return_value = mock_events_instance
            yield

    def _make_state(self, **overrides):
        state = {
            "lead_id": "test_001",
            "lead_name": "Test",
            "property_address": "123 Main St",
            "conversation_history": [],
            "is_qualified": True,
            "property_condition": "needs_work",
            "current_journey_stage": "qualification",
        }
        state.update(overrides)
        return state

    @pytest.mark.asyncio
    async def test_listing_prep_qualified_seller(self, mock_seller_deps):
        """Test listing prep generates staging and repair recommendations."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_state()
        result = await bot.prepare_listing(state)

        assert len(result["staging_recommendations"]) > 4
        assert result["repair_estimates"]["total"] > 0
        assert result["current_journey_stage"] == "listing_prep"

    @pytest.mark.asyncio
    async def test_listing_prep_unqualified_seller(self, mock_seller_deps):
        """Test listing prep skips unqualified sellers."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_state(is_qualified=False)
        result = await bot.prepare_listing(state)
        assert result == {}

    @pytest.mark.asyncio
    async def test_listing_prep_no_address(self, mock_seller_deps):
        """Test listing prep skips without address."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_state(property_address=None)
        result = await bot.prepare_listing(state)
        assert result == {}

    def test_staging_recommendations_move_in_ready(self, mock_seller_deps):
        """Test staging recs for move-in ready property."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        recs = bot.listing_service._generate_staging_recommendations("move_in_ready")
        assert any("photography" in r.lower() for r in recs)
        assert len(recs) >= 5

    def test_staging_recommendations_needs_work(self, mock_seller_deps):
        """Test staging recs for needs-work property."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        recs = bot.listing_service._generate_staging_recommendations("needs_work")
        assert any("paint" in r.lower() for r in recs)

    def test_staging_recommendations_major_repairs(self, mock_seller_deps):
        """Test staging recs for major repairs property."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        recs = bot.listing_service._generate_staging_recommendations("major_repairs")
        assert any("inspection" in r.lower() for r in recs)

    def test_repair_estimates_move_in_ready(self, mock_seller_deps):
        """Test repair estimates for move-in ready."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        estimates = bot.listing_service._estimate_repairs("move_in_ready")
        assert estimates["total"] < 5000

    def test_repair_estimates_needs_work(self, mock_seller_deps):
        """Test repair estimates for needs-work."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        estimates = bot.listing_service._estimate_repairs("needs_work")
        assert estimates["total"] > 5000

    def test_repair_estimates_major_repairs(self, mock_seller_deps):
        """Test repair estimates for major repairs."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        estimates = bot.listing_service._estimate_repairs("major_repairs")
        assert estimates["total"] > 20000

    def test_select_strategy_listing_prep_route(self, mock_seller_deps):
        """Test strategy routes to listing_prep for qualified seller in listing_prep stage."""
        bot = JorgeSellerBot(config=JorgeFeatureConfig(enable_bot_intelligence=False))
        state = self._make_state(
            current_journey_stage="listing_prep",
            is_qualified=True,
            property_address="123 Main St",
            stall_detected=False,
            psychological_commitment=50.0,
        )
        # Test the routing logic directly
        route = bot._route_seller_action({"next_action": "listing_prep"})
        assert route == "listing_prep"
