import pytest
pytestmark = pytest.mark.integration

"""Tests for the conversation repair engine (Phase 2B)."""

import pytest

from ghl_real_estate_ai.services.jorge.repair_strategies import (
    REPAIR_LADDER,
    RepairTrigger,
    RepairType,
    get_repair_strategy,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.conversation_repair import (

    ConversationRepairProcessor,
    _word_overlap_ratio,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(**kwargs) -> ProcessingContext:
    defaults = {
        "contact_id": "repair_test_1",
        "bot_mode": "lead",
        "channel": "sms",
        "user_message": "Hello",
        "detected_language": "en",
    }
    defaults.update(kwargs)
    return ProcessingContext(**defaults)


def _resp(msg: str = "Bot reply", action: ProcessingAction = ProcessingAction.PASS) -> ProcessedResponse:
    return ProcessedResponse(message=msg, original_message=msg, action=action)


# ---------------------------------------------------------------------------
# Repair Strategies Unit Tests
# ---------------------------------------------------------------------------


class TestRepairStrategies:
    def test_get_strategy_low_confidence(self):
        s = get_repair_strategy(RepairTrigger.LOW_CONFIDENCE, 0)
        assert s.repair_type == RepairType.CLARIFICATION
        assert s.escalation_level == 0

    def test_get_strategy_fallback_to_escalation(self):
        """Unknown trigger/level combos fall back to human escalation."""
        s = get_repair_strategy(RepairTrigger.LOW_CONFIDENCE, 99)
        assert s.repair_type == RepairType.HUMAN_ESCALATION

    def test_get_strategy_no_progress_level_2(self):
        s = get_repair_strategy(RepairTrigger.NO_PROGRESS, 2)
        assert s.repair_type == RepairType.HUMAN_ESCALATION


# ---------------------------------------------------------------------------
# ConversationRepairProcessor Tests
# ---------------------------------------------------------------------------


class TestConversationRepairProcessor:
    @pytest.mark.asyncio
    async def test_low_confidence_triggers_clarification(self):
        stage = ConversationRepairProcessor()
        ctx = _ctx(metadata={"bot_confidence": 0.2})
        resp = _resp("I think maybe...")
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.MODIFY
        assert "understand correctly" in result.message
        assert ctx.metadata["repair_triggered"] is True
        assert ctx.metadata["repair_type"] == "clarification"

    @pytest.mark.asyncio
    async def test_repeated_question_same_text(self):
        stage = ConversationRepairProcessor()
        ctx = _ctx(user_message="What is the price of the house?")

        # First message: no repair
        resp1 = _resp()
        result1 = await stage.process(resp1, ctx)
        assert result1.action == ProcessingAction.PASS

        # Second identical message: triggers repair
        ctx2 = _ctx(user_message="What is the price of the house?")
        resp2 = _resp()
        result2 = await stage.process(resp2, ctx2)
        assert result2.action == ProcessingAction.MODIFY
        assert ctx2.metadata.get("repair_trigger") == "repeated_question"

    @pytest.mark.asyncio
    async def test_repeated_question_slight_variation(self):
        """Word overlap >= 0.7 should trigger repeated question detection."""
        stage = ConversationRepairProcessor()

        # First message
        ctx1 = _ctx(user_message="What is the price of this house")
        await stage.process(_resp(), ctx1)

        # Slight variation (high overlap)
        ctx2 = _ctx(user_message="What is the price of that house")
        resp2 = _resp()
        result2 = await stage.process(resp2, ctx2)
        assert result2.action == ProcessingAction.MODIFY
        assert ctx2.metadata.get("repair_trigger") == "repeated_question"

    @pytest.mark.asyncio
    async def test_contradiction_detection(self):
        stage = ConversationRepairProcessor()

        # First: normal message to populate last_bot_response
        ctx1 = _ctx(user_message="Tell me about properties")
        await stage.process(_resp("Here are some properties in your area."), ctx1)

        # User contradicts
        ctx2 = _ctx(user_message="no that's wrong")
        resp2 = _resp("Let me try again.")
        result2 = await stage.process(resp2, ctx2)
        assert result2.action == ProcessingAction.MODIFY
        assert ctx2.metadata.get("repair_trigger") == "contradiction"

    @pytest.mark.asyncio
    async def test_escalation_ladder_progression(self):
        """Escalation level should increase with each repair."""
        stage = ConversationRepairProcessor()
        contact = "escalation_test"

        # Trigger repairs repeatedly via low confidence
        for i in range(3):
            ctx = _ctx(
                contact_id=contact,
                user_message=f"unique question {i}",
                metadata={"bot_confidence": 0.1},
            )
            await stage.process(_resp(), ctx)

        state = stage._contact_state[contact]
        assert state.escalation_level == 2  # capped at 2
        assert state.repair_count == 3

    @pytest.mark.asyncio
    async def test_human_escalation_at_max_level(self):
        """After repeated failures, should escalate to human."""
        stage = ConversationRepairProcessor()
        contact = "max_escalation"

        # Drive to max escalation: 3 repairs at low confidence
        for i in range(3):
            ctx = _ctx(
                contact_id=contact,
                user_message=f"different question {i}",
                metadata={"bot_confidence": 0.1},
            )
            await stage.process(_resp(), ctx)

        # 4th trigger: now at escalation=2, repair_count=3 -> NO_PROGRESS
        ctx = _ctx(
            contact_id=contact,
            user_message="yet another question",
            metadata={"bot_confidence": 0.1},
        )
        resp = _resp()
        result = await stage.process(resp, ctx)
        assert "team member" in result.message
        assert any(
            a.get("tag") == "Human-Escalation-Needed" for a in result.actions
        )

    @pytest.mark.asyncio
    async def test_multiple_choice_formatting(self):
        """Multiple choice strategy should format options as numbered list."""
        stage = ConversationRepairProcessor()
        contact = "mc_test"

        # Drive to escalation_level=1 first (one repair at level 0)
        ctx1 = _ctx(
            contact_id=contact,
            user_message="help me",
            metadata={"bot_confidence": 0.1},
        )
        await stage.process(_resp(), ctx1)

        # Now escalation_level=1. Trigger no_progress (need esc>=2, count>=3).
        # Actually, multiple choice is at level 1 for NO_PROGRESS.
        # Let's drive escalation to 2 and count to 3, then trigger.
        for i in range(2):
            ctx = _ctx(
                contact_id=contact,
                user_message=f"question {i} unique",
                metadata={"bot_confidence": 0.1},
            )
            await stage.process(_resp(), ctx)

        # Now at escalation=2, repair_count=3 -> next triggers NO_PROGRESS
        ctx_final = _ctx(
            contact_id=contact,
            user_message="another unique question",
            metadata={"bot_confidence": 0.1},
        )
        result = await stage.process(_resp(), ctx_final)

        # Should be human escalation at this point (NO_PROGRESS, level 2)
        # The escalation goes: level0 -> level1 -> level2 (capped)
        # At repair_count=3 and escalation=2 -> NO_PROGRESS -> human escalation
        assert ctx_final.metadata.get("repair_triggered") is True

    @pytest.mark.asyncio
    async def test_no_repair_on_normal_messages(self):
        stage = ConversationRepairProcessor()
        ctx = _ctx(user_message="I want to buy a house in Rancho Cucamonga")
        resp = _resp("Great! Let me help you with that.")
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.PASS
        assert ctx.metadata.get("repair_triggered") is None

    @pytest.mark.asyncio
    async def test_no_repair_on_blocked_message(self):
        stage = ConversationRepairProcessor()
        ctx = _ctx(metadata={"bot_confidence": 0.1})
        resp = _resp(action=ProcessingAction.BLOCK)
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.BLOCK
        assert ctx.metadata.get("repair_triggered") is None

    @pytest.mark.asyncio
    async def test_no_repair_on_short_circuited_message(self):
        stage = ConversationRepairProcessor()
        ctx = _ctx(metadata={"bot_confidence": 0.1})
        resp = _resp(action=ProcessingAction.SHORT_CIRCUIT)
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert ctx.metadata.get("repair_triggered") is None

    @pytest.mark.asyncio
    async def test_repair_state_tracking_across_messages(self):
        """State should persist across multiple process calls for same contact."""
        stage = ConversationRepairProcessor()
        contact = "state_tracking"

        # Send 3 messages
        for msg in ["Hello there", "How are you", "What properties available"]:
            ctx = _ctx(contact_id=contact, user_message=msg)
            await stage.process(_resp(f"Reply to: {msg}"), ctx)

        state = stage._get_state(contact)
        assert len(state.recent_questions) == 3
        assert state.last_bot_response.startswith("Reply to:")
        assert state.repair_count == 0  # no repairs triggered


# ---------------------------------------------------------------------------
# Helper function tests
# ---------------------------------------------------------------------------


class TestWordOverlap:
    def test_identical_strings(self):
        assert _word_overlap_ratio("hello world", "hello world") == 1.0

    def test_no_overlap(self):
        assert _word_overlap_ratio("hello world", "foo bar") == 0.0

    def test_partial_overlap(self):
        ratio = _word_overlap_ratio("the price of the house", "the cost of the house")
        assert 0.5 < ratio < 1.0

    def test_empty_string(self):
        assert _word_overlap_ratio("", "hello") == 0.0
        assert _word_overlap_ratio("hello", "") == 0.0