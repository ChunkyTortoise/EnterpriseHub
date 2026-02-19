"""Tests for human escalation triggers in JorgeHandoffService.

Covers 4 trigger types:
1. Explicit human request ("talk to Jorge", "real person")
2. Financial/legal keywords ("foreclosure", "attorney")
3. Unproductive loop detection (loop_count >= 3)
4. Hot lead with all questions answered
"""

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService


@pytest.fixture
def service():
    return JorgeHandoffService()


class TestHumanEscalation:
    """Human escalation trigger evaluation."""

    @pytest.mark.asyncio
    async def test_explicit_human_request_talk_to_jorge(self, service):
        """'Talk to Jorge' triggers human escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_1",
            user_message="Can I talk to Jorge directly?",
        )
        assert result is not None
        assert result.target_bot == "human"
        assert result.reason == "explicit_human_request"

    @pytest.mark.asyncio
    async def test_explicit_human_request_real_person(self, service):
        """'Real person' triggers human escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_2",
            user_message="I want to speak with a real person",
        )
        assert result is not None
        assert result.reason == "explicit_human_request"

    @pytest.mark.asyncio
    async def test_explicit_human_request_not_a_bot(self, service):
        """'Not a bot' triggers human escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_3",
            user_message="Are you not a bot? Let me talk to someone",
        )
        assert result is not None
        assert result.reason == "explicit_human_request"

    @pytest.mark.asyncio
    async def test_legal_keyword_foreclosure(self, service):
        """'Foreclosure' triggers legal/financial escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_4",
            user_message="My house is in foreclosure, what can I do?",
        )
        assert result is not None
        assert result.reason == "legal_financial_topic"

    @pytest.mark.asyncio
    async def test_legal_keyword_attorney(self, service):
        """'Attorney' triggers legal/financial escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_5",
            user_message="I need to talk to my attorney first about this",
        )
        assert result is not None
        assert result.reason == "legal_financial_topic"

    @pytest.mark.asyncio
    async def test_legal_keyword_bankruptcy(self, service):
        """'Bankruptcy' triggers legal/financial escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_6",
            user_message="We're going through bankruptcy proceedings",
        )
        assert result is not None
        assert result.reason == "legal_financial_topic"

    @pytest.mark.asyncio
    async def test_unproductive_loop_trigger(self, service):
        """Loop count >= 3 triggers unproductive loop escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_7",
            user_message="I already told you that",
            loop_count=3,
        )
        assert result is not None
        assert result.reason == "unproductive_loop"

    @pytest.mark.asyncio
    async def test_loop_count_below_threshold_no_trigger(self, service):
        """Loop count < 3 does not trigger by itself."""
        result = await service.evaluate_human_escalation(
            contact_id="c_8",
            user_message="I already told you that",
            loop_count=2,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hot_lead_qualified(self, service):
        """Hot lead with all questions answered triggers escalation."""
        result = await service.evaluate_human_escalation(
            contact_id="c_9",
            user_message="Sounds great, what's next?",
            temperature="hot",
            questions_answered=4,
            total_questions=4,
        )
        assert result is not None
        assert result.reason == "hot_lead_qualified"

    @pytest.mark.asyncio
    async def test_warm_lead_all_questions_no_trigger(self, service):
        """Warm lead with all questions answered does not trigger."""
        result = await service.evaluate_human_escalation(
            contact_id="c_10",
            user_message="Sounds good",
            temperature="warm",
            questions_answered=4,
            total_questions=4,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_hot_lead_incomplete_no_trigger(self, service):
        """Hot lead with incomplete questions does not trigger."""
        result = await service.evaluate_human_escalation(
            contact_id="c_11",
            user_message="OK",
            temperature="hot",
            questions_answered=3,
            total_questions=4,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_normal_message_no_escalation(self, service):
        """Normal message with no triggers returns None."""
        result = await service.evaluate_human_escalation(
            contact_id="c_12",
            user_message="I'm thinking about selling in about 3 months",
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_escalation_context_includes_metadata(self, service):
        """Escalation decision includes useful metadata in context."""
        result = await service.evaluate_human_escalation(
            contact_id="c_13",
            user_message="I need to speak with my attorney",
            temperature="warm",
            loop_count=1,
            questions_answered=2,
        )
        assert result is not None
        assert result.context["contact_id"] == "c_13"
        assert result.context["temperature"] == "warm"
        assert result.context["trigger"] == "legal_financial_topic"
        assert result.context["loop_count"] == 1
        assert result.context["questions_answered"] == 2

    @pytest.mark.asyncio
    async def test_escalation_confidence_is_one(self, service):
        """Human escalation always has confidence 1.0."""
        result = await service.evaluate_human_escalation(
            contact_id="c_14",
            user_message="Let me talk to Jorge please",
        )
        assert result is not None
        assert result.confidence == 1.0
