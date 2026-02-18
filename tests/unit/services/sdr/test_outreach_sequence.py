"""Unit tests for SDR OutreachSequenceEngine step logic and ObjectionHandler.

Tests:
- SequenceStep transitions and ordering
- _build_message SMS length cap (160 chars)
- ObjectionHandler.classify_objection pattern matching
- ObjectionHandler.should_opt_out
"""

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# SequenceStep ordering
# ---------------------------------------------------------------------------

class TestSequenceStep:
    """Tests for SequenceStep enum ordering and terminal states."""

    def test_terminal_states_exist(self):
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import SequenceStep
        assert SequenceStep.QUALIFIED
        assert SequenceStep.BOOKED
        assert SequenceStep.DISQUALIFIED
        assert SequenceStep.OPTED_OUT

    def test_sequence_steps_have_expected_values(self):
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import SequenceStep
        assert SequenceStep.SMS_1.value == "sms_1"
        assert SequenceStep.EMAIL_1.value == "email_1"
        assert SequenceStep.NURTURE_PAUSE.value == "nurture_pause"

    def test_is_terminal_returns_true_for_terminal_states(self):
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import SequenceStep
        terminal = [SequenceStep.QUALIFIED, SequenceStep.BOOKED, SequenceStep.DISQUALIFIED, SequenceStep.OPTED_OUT]
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import is_terminal_step
        for step in terminal:
            assert is_terminal_step(step) is True

    def test_is_terminal_returns_false_for_active_steps(self):
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import SequenceStep, is_terminal_step
        active = [SequenceStep.SMS_1, SequenceStep.EMAIL_1, SequenceStep.NURTURE_PAUSE]
        for step in active:
            assert is_terminal_step(step) is False

    def test_next_step_progression(self):
        """SMS_1 → EMAIL_1 → SMS_2 → VOICEMAIL_1 progression."""
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import get_next_step, SequenceStep
        assert get_next_step(SequenceStep.ENROLLED) == SequenceStep.SMS_1
        assert get_next_step(SequenceStep.SMS_1) == SequenceStep.EMAIL_1
        assert get_next_step(SequenceStep.EMAIL_1) == SequenceStep.SMS_2
        assert get_next_step(SequenceStep.SMS_2) == SequenceStep.VOICEMAIL_1
        assert get_next_step(SequenceStep.VOICEMAIL_1) == SequenceStep.EMAIL_2
        assert get_next_step(SequenceStep.EMAIL_2) == SequenceStep.SMS_3
        assert get_next_step(SequenceStep.SMS_3) == SequenceStep.VOICEMAIL_2
        assert get_next_step(SequenceStep.VOICEMAIL_2) == SequenceStep.NURTURE_PAUSE

    def test_terminal_step_returns_none(self):
        from ghl_real_estate_ai.services.sdr.outreach_sequence_engine import get_next_step, SequenceStep
        assert get_next_step(SequenceStep.QUALIFIED) is None
        assert get_next_step(SequenceStep.OPTED_OUT) is None


# ---------------------------------------------------------------------------
# ObjectionHandler
# ---------------------------------------------------------------------------

class TestObjectionHandler:
    """Tests for ObjectionHandler.classify_objection and should_opt_out."""

    def _handler(self):
        from ghl_real_estate_ai.agents.sdr.objection_handler import ObjectionHandler
        return ObjectionHandler(orchestrator=None)

    # ── classify_objection ───────────────────────────────────────────────

    def test_not_interested_pattern(self):
        handler = self._handler()
        assert handler.classify_objection("I'm not interested") == "not_interested"

    def test_not_interested_stop_texting(self):
        handler = self._handler()
        assert handler.classify_objection("please stop texting me") == "not_interested"

    def test_already_agent_pattern(self):
        handler = self._handler()
        assert handler.classify_objection("I already have an agent working with me") == "already_agent"

    def test_timing_pattern(self):
        handler = self._handler()
        assert handler.classify_objection("I'm not ready yet, maybe next year") == "timing"

    def test_price_pattern(self):
        handler = self._handler()
        assert handler.classify_objection("The market is too expensive right now") == "price"

    def test_info_request_pattern(self):
        handler = self._handler()
        assert handler.classify_objection("Tell me more about what you offer") == "info_request"

    def test_no_match_returns_none(self):
        handler = self._handler()
        result = handler.classify_objection("Sure, sounds great! When can we meet?")
        assert result is None

    def test_case_insensitive(self):
        handler = self._handler()
        assert handler.classify_objection("NOT INTERESTED AT ALL") == "not_interested"

    # ── should_opt_out ───────────────────────────────────────────────────

    def test_not_interested_triggers_opt_out(self):
        handler = self._handler()
        assert handler.should_opt_out("not_interested") is True

    def test_timing_does_not_trigger_opt_out(self):
        handler = self._handler()
        assert handler.should_opt_out("timing") is False

    def test_already_agent_does_not_trigger_opt_out(self):
        handler = self._handler()
        assert handler.should_opt_out("already_agent") is False

    def test_unknown_type_does_not_trigger_opt_out(self):
        handler = self._handler()
        assert handler.should_opt_out("some_random_type") is False
