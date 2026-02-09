"""Tests for the response post-processing pipeline (Phase 1)."""

import pytest

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.factory import create_default_pipeline
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ComplianceFlagSeverity,
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.pipeline import ResponsePostProcessor
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.ai_disclosure import (
    AIDisclosureProcessor,
    DISCLOSURE_EN,
    DISCLOSURE_ES,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.compliance_check import (
    ComplianceCheckProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.sms_truncation import (
    SMSTruncationProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.tcpa_opt_out import (
    TCPAOptOutProcessor,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_context(**kwargs) -> ProcessingContext:
    defaults = {
        "contact_id": "test_contact_1",
        "bot_mode": "buyer",
        "channel": "sms",
        "user_message": "Hello",
        "detected_language": "en",
    }
    defaults.update(kwargs)
    return ProcessingContext(**defaults)


# ---------------------------------------------------------------------------
# AI Disclosure Stage
# ---------------------------------------------------------------------------


class TestAIDisclosureProcessor:
    @pytest.mark.asyncio
    async def test_appends_english_disclosure(self):
        stage = AIDisclosureProcessor()
        ctx = _make_context(detected_language="en")
        resp = ProcessedResponse(message="Great property!", original_message="Great property!")
        result = await stage.process(resp, ctx)
        assert result.message.endswith("[AI-assisted message]")
        assert result.action == ProcessingAction.MODIFY

    @pytest.mark.asyncio
    async def test_appends_spanish_disclosure(self):
        stage = AIDisclosureProcessor()
        ctx = _make_context(detected_language="es")
        resp = ProcessedResponse(message="Buena propiedad!", original_message="Buena propiedad!")
        result = await stage.process(resp, ctx)
        assert result.message.endswith("[Mensaje asistido por IA]")

    @pytest.mark.asyncio
    async def test_no_duplicate_disclosure(self):
        stage = AIDisclosureProcessor()
        ctx = _make_context()
        msg = "Hello\n[AI-assisted message]"
        resp = ProcessedResponse(message=msg, original_message=msg)
        result = await stage.process(resp, ctx)
        assert result.message.count("[AI-assisted message]") == 1

    @pytest.mark.asyncio
    async def test_skips_on_short_circuit(self):
        stage = AIDisclosureProcessor()
        ctx = _make_context()
        resp = ProcessedResponse(
            message="Opted out", original_message="Opted out", action=ProcessingAction.SHORT_CIRCUIT
        )
        result = await stage.process(resp, ctx)
        assert "[AI-assisted message]" not in result.message

    @pytest.mark.asyncio
    async def test_skips_on_blocked(self):
        stage = AIDisclosureProcessor()
        ctx = _make_context()
        resp = ProcessedResponse(
            message="Safe fallback", original_message="Bad msg", action=ProcessingAction.BLOCK
        )
        result = await stage.process(resp, ctx)
        assert "[AI-assisted message]" not in result.message


# ---------------------------------------------------------------------------
# TCPA Opt-Out Stage
# ---------------------------------------------------------------------------


class TestTCPAOptOutProcessor:
    @pytest.mark.asyncio
    async def test_detects_stop(self):
        stage = TCPAOptOutProcessor()
        ctx = _make_context(user_message="STOP")
        resp = ProcessedResponse(message="bot reply", original_message="bot reply")
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert ctx.is_opt_out is True
        assert any(a["tag"] == "AI-Off" for a in result.actions)

    @pytest.mark.asyncio
    async def test_detects_unsubscribe(self):
        stage = TCPAOptOutProcessor()
        ctx = _make_context(user_message="please unsubscribe me")
        resp = ProcessedResponse(message="bot reply", original_message="bot reply")
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.SHORT_CIRCUIT

    @pytest.mark.asyncio
    async def test_detects_spanish_opt_out(self):
        stage = TCPAOptOutProcessor()
        ctx = _make_context(user_message="parar", detected_language="es")
        resp = ProcessedResponse(message="bot reply", original_message="bot reply")
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.SHORT_CIRCUIT

    @pytest.mark.asyncio
    async def test_spanish_opt_out_response(self):
        stage = TCPAOptOutProcessor()
        ctx = _make_context(user_message="cancelar", detected_language="es")
        resp = ProcessedResponse(message="bot reply", original_message="bot reply")
        result = await stage.process(resp, ctx)
        assert "dado de baja" in result.message

    @pytest.mark.asyncio
    async def test_no_opt_out_passes_through(self):
        stage = TCPAOptOutProcessor()
        ctx = _make_context(user_message="I want to buy a house")
        resp = ProcessedResponse(message="bot reply", original_message="bot reply")
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.PASS
        assert result.message == "bot reply"


# ---------------------------------------------------------------------------
# Compliance Check Stage
# ---------------------------------------------------------------------------


class TestComplianceCheckProcessor:
    @pytest.mark.asyncio
    async def test_clean_message_passes(self):
        stage = ComplianceCheckProcessor()
        ctx = _make_context()
        resp = ProcessedResponse(
            message="The property at 123 Main St has 3 bedrooms.",
            original_message="The property at 123 Main St has 3 bedrooms.",
        )
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_blocked_message_replaced(self):
        stage = ComplianceCheckProcessor()
        ctx = _make_context(bot_mode="buyer")
        # "safe area" triggers safety steering pattern
        resp = ProcessedResponse(
            message="That's a very safe area with low crime rates.",
            original_message="That's a very safe area with low crime rates.",
        )
        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.BLOCK
        assert "Compliance-Alert" in [a["tag"] for a in result.actions if a.get("tag")]
        assert any(f.severity == ComplianceFlagSeverity.CRITICAL for f in result.compliance_flags)

    @pytest.mark.asyncio
    async def test_seller_fallback_message(self):
        stage = ComplianceCheckProcessor()
        ctx = _make_context(bot_mode="seller")
        resp = ProcessedResponse(
            message="It's a safe neighborhood with low crime.",
            original_message="It's a safe neighborhood with low crime.",
        )
        result = await stage.process(resp, ctx)
        assert "facts about your property" in result.message


# ---------------------------------------------------------------------------
# SMS Truncation Stage
# ---------------------------------------------------------------------------


class TestSMSTruncationProcessor:
    @pytest.mark.asyncio
    async def test_short_message_unchanged(self):
        stage = SMSTruncationProcessor()
        ctx = _make_context(channel="sms")
        msg = "Short message."
        resp = ProcessedResponse(message=msg, original_message=msg)
        result = await stage.process(resp, ctx)
        assert result.message == msg
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_long_message_truncated(self):
        stage = SMSTruncationProcessor(max_chars=50)
        ctx = _make_context(channel="sms")
        msg = "This is a first sentence. This is a second sentence. This is way too long for SMS."
        resp = ProcessedResponse(message=msg, original_message=msg)
        result = await stage.process(resp, ctx)
        assert len(result.message) <= 50
        assert result.action == ProcessingAction.MODIFY

    @pytest.mark.asyncio
    async def test_truncates_at_sentence_boundary(self):
        stage = SMSTruncationProcessor(max_chars=50)
        ctx = _make_context(channel="sms")
        msg = "First sentence is here now. Second sentence that makes it long enough to truncate."
        resp = ProcessedResponse(message=msg, original_message=msg)
        result = await stage.process(resp, ctx)
        assert result.message.endswith(".")

    @pytest.mark.asyncio
    async def test_skips_non_sms_channel(self):
        stage = SMSTruncationProcessor(max_chars=10)
        ctx = _make_context(channel="email")
        msg = "A" * 500
        resp = ProcessedResponse(message=msg, original_message=msg)
        result = await stage.process(resp, ctx)
        assert len(result.message) == 500


# ---------------------------------------------------------------------------
# Full Pipeline Integration
# ---------------------------------------------------------------------------


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_clean_message_gets_disclosure(self):
        pipeline = create_default_pipeline()
        ctx = _make_context(contact_id="clean_1", user_message="Tell me about the house")
        result = await pipeline.process("This property features 3 bedrooms and 2 baths.", ctx)
        assert "[AI-assisted message]" in result.message
        assert result.action == ProcessingAction.MODIFY

    @pytest.mark.asyncio
    async def test_opt_out_short_circuits(self):
        pipeline = create_default_pipeline()
        ctx = _make_context(user_message="stop")
        result = await pipeline.process("Bot reply", ctx)
        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert "[AI-assisted message]" not in result.message
        assert any(a["tag"] == "AI-Off" for a in result.actions)

    @pytest.mark.asyncio
    async def test_compliance_block_no_disclosure(self):
        pipeline = create_default_pipeline()
        ctx = _make_context(user_message="Tell me about safety", bot_mode="buyer")
        result = await pipeline.process("That's a very safe area with low crime.", ctx)
        assert result.action == ProcessingAction.BLOCK
        # Blocked messages should NOT get AI disclosure
        assert "[AI-assisted message]" not in result.message

    @pytest.mark.asyncio
    async def test_stage_error_resilience(self):
        """A stage that throws doesn't crash the pipeline."""

        class BrokenStage(ResponseProcessorStage):
            @property
            def name(self):
                return "broken"

            async def process(self, response, context):
                raise RuntimeError("boom")

        pipeline = ResponsePostProcessor(
            stages=[
                BrokenStage(),
                AIDisclosureProcessor(),
            ]
        )
        ctx = _make_context()
        result = await pipeline.process("Hello", ctx)
        assert "[AI-assisted message]" in result.message
        assert "broken:error" in result.stage_log

    @pytest.mark.asyncio
    async def test_spanish_full_flow(self):
        pipeline = create_default_pipeline()
        ctx = _make_context(
            contact_id="spanish_1",
            user_message="Quiero comprar una casa",
            detected_language="es",
        )
        result = await pipeline.process("Tenemos varias opciones para usted.", ctx)
        assert "[Mensaje asistido por IA]" in result.message

    @pytest.mark.asyncio
    async def test_pipeline_stage_log(self):
        pipeline = create_default_pipeline()
        ctx = _make_context(contact_id="log_test_1", user_message="Hello")
        result = await pipeline.process("Reply", ctx)
        assert len(result.stage_log) == 5  # all 5 stages ran (incl. language_mirror)
