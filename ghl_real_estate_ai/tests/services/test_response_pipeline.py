"""Tests for the Jorge response post-processing pipeline.

Covers all 6 stages individually and the full pipeline integration:
1. LanguageMirrorProcessor — language detection, context enrichment
2. TCPAOptOutProcessor — opt-out keyword detection, short-circuit
3. ComplianceCheckProcessor — FHA/RESPA enforcement
4. AIDisclosureProcessor — SB 243 AI disclosure footer
5. SMSTruncationProcessor — 320-char SMS truncation
6. ConversationRepairProcessor — breakdown detection & repair
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.models.language_preferences import LanguageDetection
from ghl_real_estate_ai.services.jorge.response_pipeline.factory import (
    create_default_pipeline,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ComplianceFlagSeverity,
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.pipeline import (
    ResponsePostProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.ai_disclosure import (
    AIDisclosureProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.compliance_check import (
    _SAFE_FALLBACKS,
    ComplianceCheckProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.conversation_repair import (
    ConversationRepairProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror import (
    LanguageMirrorProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.sms_truncation import (
    SMS_MAX_CHARS,
    SMSTruncationProcessor,
)
from ghl_real_estate_ai.services.jorge.response_pipeline.stages.tcpa_opt_out import (
    OPT_OUT_PHRASES,
    OPT_OUT_RESPONSE_EN,
    OPT_OUT_RESPONSE_ES,
    TCPAOptOutProcessor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(message: str = "Hello!", **ctx_kwargs) -> tuple:
    """Create a ProcessedResponse and ProcessingContext pair for testing."""
    ctx = ProcessingContext(**ctx_kwargs)
    resp = ProcessedResponse(message=message, original_message=message, context=ctx)
    return resp, ctx


def _mock_language_detection(language: str = "en", confidence: float = 0.95):
    """Return a real LanguageDetection dataclass instance (needed for asdict)."""
    return LanguageDetection(
        language=language,
        confidence=confidence,
        is_code_switching=False,
        secondary_language=None,
    )


# ===========================================================================
# 1. TCPAOptOutProcessor
# ===========================================================================


class TestTCPAOptOutProcessor:
    """TCPA opt-out keyword detection and short-circuit behavior."""

    @pytest.fixture
    def stage(self):
        return TCPAOptOutProcessor()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_msg",
        [
            "stop",
            "STOP",
            "Stop",
            "unsubscribe",
            "UNSUBSCRIBE",
            "opt out",
            "remove me",
            "cancel",
            "not interested",
            "parar",
            "cancelar",
            "no más",
        ],
    )
    async def test_opt_out_exact_keywords(self, stage, user_msg):
        """Each opt-out phrase triggers short-circuit."""
        resp, ctx = _make_response(user_message=user_msg)
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert ctx.is_opt_out is True
        assert any(a["tag"] == "TCPA-Opt-Out" for a in result.actions)
        assert any(a["tag"] == "AI-Off" for a in result.actions)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_msg",
        [
            "Stop please",
            "I want to stop",
            "Please unsubscribe me",
            "I'd like to opt out of these messages",
            "remove me from the list",
            "please cancel this",
        ],
    )
    async def test_opt_out_phrases_in_longer_messages(self, stage, user_msg):
        """Opt-out phrases embedded in longer messages still trigger."""
        resp, ctx = _make_response(user_message=user_msg)
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert ctx.is_opt_out is True

    @pytest.mark.asyncio
    async def test_opt_out_english_response(self, stage):
        """English opt-out yields English acknowledgement."""
        resp, ctx = _make_response(user_message="stop", detected_language="en")
        result = await stage.process(resp, ctx)
        assert result.message == OPT_OUT_RESPONSE_EN

    @pytest.mark.asyncio
    async def test_opt_out_spanish_response(self, stage):
        """Spanish opt-out yields Spanish acknowledgement."""
        resp, ctx = _make_response(user_message="parar", detected_language="es")
        result = await stage.process(resp, ctx)
        assert result.message == OPT_OUT_RESPONSE_ES

    @pytest.mark.asyncio
    async def test_no_opt_out_passes_through(self, stage):
        """Normal messages pass through without modification."""
        resp, ctx = _make_response(
            message="I'm interested in a home",
            user_message="Tell me about the property",
        )
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.PASS
        assert result.message == "I'm interested in a home"
        assert ctx.is_opt_out is False

    @pytest.mark.asyncio
    async def test_opt_out_compliance_flag(self, stage):
        """Opt-out detection adds a compliance flag."""
        resp, ctx = _make_response(user_message="stop", contact_id="c_123")
        result = await stage.process(resp, ctx)

        assert len(result.compliance_flags) == 1
        flag = result.compliance_flags[0]
        assert flag.category == "tcpa"
        assert flag.severity == ComplianceFlagSeverity.INFO
        assert "c_123" in flag.description


# ===========================================================================
# 2. AIDisclosureProcessor
# ===========================================================================


class TestAIDisclosureProcessor:
    """SB 243 AI disclosure footer tests."""

    @pytest.fixture
    def stage(self):
        return AIDisclosureProcessor()

    @pytest.mark.asyncio
    async def test_disclosure_not_added(self, stage):
        """Messages pass through unchanged — no footer added."""
        resp, ctx = _make_response(message="Great property!", detected_language="en")
        result = await stage.process(resp, ctx)

        assert result.message == "Great property!"
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_no_disclosure_spanish(self, stage):
        """Spanish messages also pass through unchanged."""
        resp, ctx = _make_response(message="Buena propiedad!", detected_language="es")
        result = await stage.process(resp, ctx)

        assert result.message == "Buena propiedad!"

    @pytest.mark.asyncio
    async def test_no_footer_on_any_message(self, stage):
        """No AI disclosure footer appended to any message."""
        resp, ctx = _make_response(message="Hello!")
        result = await stage.process(resp, ctx)

        assert "[AI-assisted message]" not in result.message

    @pytest.mark.asyncio
    async def test_short_circuit_passes_through(self, stage):
        """SHORT_CIRCUIT messages pass through unchanged."""
        resp, ctx = _make_response(message=OPT_OUT_RESPONSE_EN)
        resp.action = ProcessingAction.SHORT_CIRCUIT
        result = await stage.process(resp, ctx)

        assert result.message == OPT_OUT_RESPONSE_EN

    @pytest.mark.asyncio
    async def test_block_passes_through(self, stage):
        """BLOCKED messages pass through unchanged."""
        resp, ctx = _make_response(message="Safe fallback")
        resp.action = ProcessingAction.BLOCK
        result = await stage.process(resp, ctx)

        assert "[AI-assisted message]" not in result.message


# ===========================================================================
# 3. SMSTruncationProcessor
# ===========================================================================


class TestSMSTruncationProcessor:
    """SMS truncation at sentence boundaries."""

    @pytest.fixture
    def stage(self):
        return SMSTruncationProcessor()

    @pytest.mark.asyncio
    async def test_short_message_unchanged(self, stage):
        """Messages under 320 chars pass through."""
        msg = "A" * 319
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)
        assert result.message == msg
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_exact_limit_unchanged(self, stage):
        """Messages exactly at 320 chars pass through."""
        msg = "A" * 320
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)
        assert result.message == msg

    @pytest.mark.asyncio
    async def test_over_limit_truncated(self, stage):
        """Messages over 320 chars get truncated."""
        msg = "A" * 321
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)
        assert len(result.message) <= SMS_MAX_CHARS
        assert result.action == ProcessingAction.MODIFY

    @pytest.mark.asyncio
    async def test_truncation_at_sentence_boundary(self, stage):
        """Truncation prefers sentence boundaries when available."""
        # Build a message: 200 chars of sentence, then ". ", then more text
        sentence_1 = "A" * 198 + ". "  # 200 chars
        sentence_2 = "B" * 200  # pushes total to 400
        msg = sentence_1 + sentence_2
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)

        # Should truncate at the sentence boundary (". " at position 199)
        assert result.message.endswith("A.")
        assert len(result.message) <= SMS_MAX_CHARS

    @pytest.mark.asyncio
    async def test_truncation_preserves_question_mark(self, stage):
        """Sentence ending with ? is a valid truncation boundary."""
        sentence_1 = "A" * 197 + "? "  # 199 chars
        sentence_2 = "B" * 200
        msg = sentence_1 + sentence_2
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)
        assert "?" in result.message

    @pytest.mark.asyncio
    async def test_non_sms_channel_skipped(self, stage):
        """Non-SMS channels are not truncated."""
        msg = "A" * 500
        resp, ctx = _make_response(message=msg, channel="email")
        result = await stage.process(resp, ctx)
        assert result.message == msg
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_160_char_message(self, stage):
        """160-char message (single SMS segment) is not truncated."""
        msg = "A" * 160
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)
        assert result.message == msg

    @pytest.mark.asyncio
    async def test_custom_max_chars(self):
        """Custom max_chars override works."""
        custom_stage = SMSTruncationProcessor(max_chars=160)
        msg = "A" * 161
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await custom_stage.process(resp, ctx)
        assert len(result.message) <= 160


# ===========================================================================
# 4. ComplianceCheckProcessor
# ===========================================================================


class TestComplianceCheckProcessor:
    """FHA/RESPA compliance enforcement."""

    @pytest.fixture
    def stage(self):
        return ComplianceCheckProcessor()

    @pytest.mark.asyncio
    async def test_blocked_message_replaced_with_fallback(self, stage):
        """BLOCKED compliance result replaces message with safe fallback."""
        mock_status = MagicMock()
        mock_result = MagicMock()
        mock_result.status = mock_status.BLOCKED
        mock_result.reason = "Discriminatory language detected"
        mock_result.risk_score = 0.95
        mock_result.violations = [
            MagicMock(
                category=MagicMock(value="fha"),
                severity=MagicMock(value="critical"),
                matched_text="no families",
            )
        ]
        mock_result.respa_disclosures_needed = []

        mock_middleware = AsyncMock()
        mock_middleware.enforce = AsyncMock(return_value=mock_result)

        mock_get_mw = MagicMock(return_value=mock_middleware)

        with patch.dict(
            "sys.modules",
            {
                "ghl_real_estate_ai.services.compliance_middleware": MagicMock(
                    get_compliance_middleware=mock_get_mw,
                ),
                "ghl_real_estate_ai.services.compliance_guard": MagicMock(
                    ComplianceStatus=mock_status,
                ),
            },
        ):
            resp, ctx = _make_response(
                message="No families allowed in this area",
                bot_mode="buyer",
                contact_id="c_456",
            )
            result = await stage.process(resp, ctx)

        assert result.message == _SAFE_FALLBACKS["buyer"]
        assert result.action == ProcessingAction.BLOCK
        assert any(a["tag"] == "Compliance-Alert" for a in result.actions)
        assert len(result.compliance_flags) >= 1
        assert result.compliance_flags[0].severity == ComplianceFlagSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_flagged_message_adds_warning(self, stage):
        """FLAGGED compliance result adds a warning flag but does not replace."""
        mock_status = MagicMock()
        mock_result = MagicMock()
        mock_result.status = mock_status.FLAGGED
        mock_result.reason = "Potential steering language"
        mock_result.risk_score = 0.5
        mock_result.violations = []
        mock_result.respa_disclosures_needed = []

        mock_middleware = AsyncMock()
        mock_middleware.enforce = AsyncMock(return_value=mock_result)

        mock_get_mw = MagicMock(return_value=mock_middleware)

        with patch.dict(
            "sys.modules",
            {
                "ghl_real_estate_ai.services.compliance_middleware": MagicMock(
                    get_compliance_middleware=mock_get_mw,
                ),
                "ghl_real_estate_ai.services.compliance_guard": MagicMock(
                    ComplianceStatus=mock_status,
                ),
            },
        ):
            resp, ctx = _make_response(message="This neighborhood is quiet")
            result = await stage.process(resp, ctx)

        assert result.message == "This neighborhood is quiet"
        assert len(result.compliance_flags) == 1
        assert result.compliance_flags[0].severity == ComplianceFlagSeverity.WARNING

    @pytest.mark.asyncio
    async def test_import_error_gracefully_skips(self, stage):
        """If compliance_middleware not available, stage is skipped."""
        # The stage imports lazily inside process() with try/except ImportError.
        # Setting sys.modules entry to None causes ImportError on import.
        with patch.dict(
            "sys.modules",
            {
                "ghl_real_estate_ai.services.compliance_middleware": None,
            },
        ):
            resp, ctx = _make_response(message="Hello")
            result = await stage.process(resp, ctx)
            assert result.message == "Hello"

    @pytest.mark.asyncio
    async def test_safe_fallback_per_bot_mode(self, stage):
        """Each bot mode has its own safe fallback message."""
        for mode in ("lead", "buyer", "seller", "general"):
            assert mode in _SAFE_FALLBACKS
            assert len(_SAFE_FALLBACKS[mode]) > 10  # non-trivial message


# ===========================================================================
# 5. ConversationRepairProcessor
# ===========================================================================


class TestConversationRepairProcessor:
    """Conversation breakdown detection and graduated repair."""

    @pytest.fixture
    def stage(self):
        return ConversationRepairProcessor()

    @pytest.mark.asyncio
    async def test_normal_message_no_repair(self, stage):
        """Normal message with high confidence passes through."""
        resp, ctx = _make_response(
            message="Here's a great property for you!",
            user_message="What properties are available?",
            contact_id="c_1",
        )
        ctx.metadata["bot_confidence"] = 0.9
        result = await stage.process(resp, ctx)
        assert result.message == "Here's a great property for you!"

    @pytest.mark.asyncio
    async def test_low_confidence_triggers_repair(self, stage):
        """Low bot confidence triggers clarification repair."""
        resp, ctx = _make_response(
            message="Some response",
            user_message="asdfghjkl",
            contact_id="c_2",
        )
        ctx.metadata["bot_confidence"] = 0.2
        result = await stage.process(resp, ctx)

        assert result.action == ProcessingAction.MODIFY
        assert ctx.metadata.get("repair_triggered") is True
        assert ctx.metadata.get("repair_trigger") == "low_confidence"

    @pytest.mark.asyncio
    async def test_repeated_question_triggers_rephrase(self, stage):
        """Repeating the same question triggers a rephrase repair."""
        ctx = ProcessingContext(contact_id="c_3", user_message="What is the price?")

        # First message — stores in state
        resp1 = ProcessedResponse(
            message="The price is $500k",
            original_message="The price is $500k",
            context=ctx,
        )
        await stage.process(resp1, ctx)

        # Same question again
        ctx.user_message = "What is the price?"
        resp2 = ProcessedResponse(
            message="The price is $500k",
            original_message="The price is $500k",
            context=ctx,
        )
        result = await stage.process(resp2, ctx)

        assert result.action == ProcessingAction.MODIFY
        assert ctx.metadata.get("repair_trigger") == "repeated_question"

    @pytest.mark.asyncio
    async def test_contradiction_triggers_clarification(self, stage):
        """User contradiction triggers clarification repair."""
        ctx = ProcessingContext(contact_id="c_4", user_message="Tell me the price")

        # First exchange to set last_bot_response
        resp1 = ProcessedResponse(
            message="The price is $500k",
            original_message="The price is $500k",
            context=ctx,
        )
        await stage.process(resp1, ctx)

        # User contradicts
        ctx.user_message = "that's not right"
        resp2 = ProcessedResponse(
            message="I apologize",
            original_message="I apologize",
            context=ctx,
        )
        result = await stage.process(resp2, ctx)

        assert result.action == ProcessingAction.MODIFY
        assert ctx.metadata.get("repair_trigger") == "contradiction"

    @pytest.mark.asyncio
    async def test_skipped_on_short_circuit(self, stage):
        """Repair is skipped when response is already short-circuited."""
        resp, ctx = _make_response(
            message=OPT_OUT_RESPONSE_EN,
            user_message="stop",
            contact_id="c_5",
        )
        resp.action = ProcessingAction.SHORT_CIRCUIT
        ctx.metadata["bot_confidence"] = 0.1  # would normally trigger repair

        result = await stage.process(resp, ctx)
        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert result.message == OPT_OUT_RESPONSE_EN

    @pytest.mark.asyncio
    async def test_escalation_to_human(self, stage):
        """After multiple repairs, escalation to human is triggered."""
        ctx = ProcessingContext(contact_id="c_6", user_message="gibberish")
        ctx.metadata["bot_confidence"] = 0.1

        # Run through several repair cycles to escalate
        for i in range(5):
            ctx.user_message = f"gibberish nonsense {i}"
            ctx.metadata["bot_confidence"] = 0.1
            resp = ProcessedResponse(
                message=f"response {i}",
                original_message=f"response {i}",
                context=ctx,
            )
            result = await stage.process(resp, ctx)

        # After enough escalations, should see human escalation tag
        has_escalation = any(a.get("tag") == "Human-Escalation-Needed" for a in result.actions)
        # The escalation happens when escalation_level >= 2 and repair_count >= 3
        # and a trigger is detected, mapping to NO_PROGRESS
        assert has_escalation or ctx.metadata.get("repair_trigger") == "no_progress"


# ===========================================================================
# 6. LanguageMirrorProcessor
# ===========================================================================


class TestLanguageMirrorProcessor:
    """Language detection and context enrichment."""

    @pytest.fixture
    def stage(self):
        return LanguageMirrorProcessor()

    @pytest.mark.asyncio
    async def test_english_detection(self, stage):
        """English message sets detected_language to 'en'."""
        mock_detection = _mock_language_detection("en", 0.98)
        mock_service = MagicMock()
        mock_service.detect = MagicMock(return_value=mock_detection)

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
            return_value=mock_service,
        ):
            resp, ctx = _make_response(
                message="Hello!",
                user_message="I want to buy a house",
                contact_id="c_en",
            )
            result = await stage.process(resp, ctx)

        assert ctx.detected_language == "en"
        assert "language_detection" in ctx.metadata
        # Message should not be modified by language mirror
        assert result.message == "Hello!"

    @pytest.mark.asyncio
    async def test_spanish_detection(self, stage):
        """Spanish message sets detected_language to 'es'."""
        mock_detection = _mock_language_detection("es", 0.95)
        mock_service = MagicMock()
        mock_service.detect = MagicMock(return_value=mock_detection)

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
            return_value=mock_service,
        ):
            resp, ctx = _make_response(
                message="Hola!",
                user_message="Quiero comprar una casa",
                contact_id="c_es",
            )
            result = await stage.process(resp, ctx)

        assert ctx.detected_language == "es"

    @pytest.mark.asyncio
    async def test_message_not_modified(self, stage):
        """Language mirror never modifies the response message."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_service = MagicMock()
        mock_service.detect = MagicMock(return_value=mock_detection)

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
            return_value=mock_service,
        ):
            original_msg = "Some bot response here"
            resp, ctx = _make_response(message=original_msg, user_message="Hi")
            result = await stage.process(resp, ctx)

        assert result.message == original_msg


# ===========================================================================
# 7. Pipeline Integration
# ===========================================================================


class TestPipelineIntegration:
    """Full pipeline integration tests."""

    @pytest.mark.asyncio
    async def test_normal_message_through_pipeline(self):
        """Normal English SMS message passes through all stages."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        with (
            patch(
                "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
                return_value=mock_lang_service,
            ),
            patch.dict(
                "sys.modules",
                {
                    "ghl_real_estate_ai.services.compliance_middleware": None,
                },
            ),
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_int_1",
                channel="sms",
                user_message="What homes are available?",
            )
            result = await pipeline.process("Here are some great options!", ctx)

        assert "[AI-assisted message]" not in result.message
        assert result.message.startswith("Here are some great options!")
        assert len(result.stage_log) == 6  # all 6 stages ran

    @pytest.mark.asyncio
    async def test_opt_out_short_circuits_pipeline(self):
        """TCPA opt-out stops pipeline after TCPAOptOutProcessor."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
            return_value=mock_lang_service,
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_int_2",
                channel="sms",
                user_message="STOP",
            )
            result = await pipeline.process("Some bot response", ctx)

        assert result.action == ProcessingAction.SHORT_CIRCUIT
        assert result.message == OPT_OUT_RESPONSE_EN
        assert "[AI-assisted message]" not in result.message
        # Pipeline short-circuited: language_mirror ran, tcpa_opt_out short-circuited
        assert len(result.stage_log) == 2

    @pytest.mark.asyncio
    async def test_spanish_opt_out_gets_spanish_response(self):
        """Spanish user saying 'parar' gets Spanish opt-out ack."""
        mock_detection = _mock_language_detection("es", 0.95)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        with patch(
            "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
            return_value=mock_lang_service,
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_int_3",
                channel="sms",
                user_message="parar",
            )
            result = await pipeline.process("Alguna respuesta", ctx)

        assert result.message == OPT_OUT_RESPONSE_ES
        assert result.action == ProcessingAction.SHORT_CIRCUIT

    @pytest.mark.asyncio
    async def test_long_sms_truncated_after_disclosure(self):
        """Long SMS gets disclosure added then truncated to 320 chars."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        # 300-char message + disclosure = over 320
        long_msg = "A" * 300

        with (
            patch(
                "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
                return_value=mock_lang_service,
            ),
            patch.dict(
                "sys.modules",
                {
                    "ghl_real_estate_ai.services.compliance_middleware": None,
                },
            ),
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_int_4",
                channel="sms",
                user_message="Hi",
            )
            result = await pipeline.process(long_msg, ctx)

        assert len(result.message) <= SMS_MAX_CHARS

    @pytest.mark.asyncio
    async def test_email_channel_no_truncation(self):
        """Email channel skips SMS truncation even for long messages."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        long_msg = "A" * 500

        with (
            patch(
                "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
                return_value=mock_lang_service,
            ),
            patch.dict(
                "sys.modules",
                {
                    "ghl_real_estate_ai.services.compliance_middleware": None,
                },
            ),
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_int_5",
                channel="email",
                user_message="Hi",
            )
            result = await pipeline.process(long_msg, ctx)

        # Email channel: no truncation, message passes through at full length
        assert len(result.message) == 500

    @pytest.mark.asyncio
    async def test_stage_exception_does_not_break_pipeline(self):
        """If a stage raises, pipeline continues with remaining stages."""

        class BrokenStage(AIDisclosureProcessor):
            @property
            def name(self):
                return "broken"

            async def process(self, response, context):
                raise RuntimeError("Boom!")

        pipeline = ResponsePostProcessor(
            stages=[
                BrokenStage(),
                SMSTruncationProcessor(),
            ]
        )
        ctx = ProcessingContext(channel="sms", user_message="Hi")
        result = await pipeline.process("Hello!", ctx)

        # Broken stage logged as error, sms_truncation still ran
        assert "broken:error" in result.stage_log
        assert any("sms_truncation" in entry for entry in result.stage_log)

    @pytest.mark.asyncio
    async def test_stage_log_records_all_stages(self):
        """Stage log records every stage that ran."""
        mock_detection = _mock_language_detection("en", 0.99)
        mock_lang_service = MagicMock()
        mock_lang_service.detect = MagicMock(return_value=mock_detection)

        with (
            patch(
                "ghl_real_estate_ai.services.jorge.response_pipeline.stages.language_mirror.get_language_detection_service",
                return_value=mock_lang_service,
            ),
            patch.dict(
                "sys.modules",
                {
                    "ghl_real_estate_ai.services.compliance_middleware": None,
                },
            ),
        ):
            pipeline = create_default_pipeline()
            ctx = ProcessingContext(
                contact_id="c_log",
                channel="sms",
                user_message="Hello",
            )
            result = await pipeline.process("Hi there!", ctx)

        stage_names = [entry.split(":")[0] for entry in result.stage_log]
        assert "language_mirror" in stage_names
        assert "tcpa_opt_out" in stage_names
        assert "compliance_check" in stage_names
        assert "ai_disclosure" in stage_names
        assert "sms_truncation" in stage_names


# ===========================================================================
# 8. Pipeline Infrastructure
# ===========================================================================


class TestPipelineInfrastructure:
    """Pipeline construction, chaining, factory tests."""

    def test_create_default_pipeline_has_6_stages(self):
        """Default pipeline has all 6 stages in correct order."""
        pipeline = create_default_pipeline()
        names = [s.name for s in pipeline.stages]
        assert names == [
            "language_mirror",
            "tcpa_opt_out",
            "compliance_check",
            "ai_disclosure",
            "response_translation",
            "sms_truncation",
        ]

    def test_add_stage_chaining(self):
        """add_stage returns self for fluent chaining."""
        pipeline = ResponsePostProcessor()
        result = pipeline.add_stage(TCPAOptOutProcessor())
        assert result is pipeline
        assert len(pipeline.stages) == 1

    @pytest.mark.asyncio
    async def test_empty_pipeline(self):
        """Empty pipeline returns response unchanged."""
        pipeline = ResponsePostProcessor()
        ctx = ProcessingContext()
        result = await pipeline.process("Hello!", ctx)
        assert result.message == "Hello!"
        assert result.original_message == "Hello!"
        assert result.stage_log == []

    def test_processing_context_defaults(self):
        """ProcessingContext has sensible defaults."""
        ctx = ProcessingContext()
        assert ctx.channel == "sms"
        assert ctx.bot_mode == "general"
        assert ctx.detected_language == "en"
        assert ctx.is_opt_out is False
        assert ctx.contact_id == ""

    def test_processed_response_defaults(self):
        """ProcessedResponse has sensible defaults."""
        resp = ProcessedResponse(message="Hi", original_message="Hi")
        assert resp.action == ProcessingAction.PASS
        assert resp.compliance_flags == []
        assert resp.actions == []
        assert resp.stage_log == []

    def test_processing_context_is_first_message_default(self):
        """ProcessingContext.is_first_message defaults to False."""
        ctx = ProcessingContext()
        assert ctx.is_first_message is False


# ===========================================================================
# 9. Proactive AI Disclosure (SB 1001)
# ===========================================================================


class TestProactiveAIDisclosure:
    """SB 1001 proactive AI disclosure on first message of conversation."""

    @pytest.fixture
    def stage(self):
        return AIDisclosureProcessor()

    @pytest.mark.asyncio
    async def test_first_message_no_proactive_disclosure(self, stage):
        """First message passes through — no 'I'm Jorge's AI assistant' prefix."""
        resp, ctx = _make_response(
            message="Welcome! What brings you here?",
            detected_language="en",
        )
        ctx.is_first_message = True
        result = await stage.process(resp, ctx)

        assert not result.message.startswith("Hi! I'm Jorge's AI assistant.")
        assert "[AI-assisted message]" not in result.message
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_first_message_spanish_no_disclosure(self, stage):
        """Spanish first message passes through unchanged."""
        resp, ctx = _make_response(
            message="Bienvenido!",
            detected_language="es",
        )
        ctx.is_first_message = True
        result = await stage.process(resp, ctx)

        assert result.message == "Bienvenido!"

    @pytest.mark.asyncio
    async def test_subsequent_messages_no_footer(self, stage):
        """Non-first messages pass through without footer."""
        resp, ctx = _make_response(
            message="Here's more info for you.",
            detected_language="en",
        )
        ctx.is_first_message = False
        result = await stage.process(resp, ctx)

        assert result.message == "Here's more info for you."

    @pytest.mark.asyncio
    async def test_message_unchanged_throughout(self, stage):
        """Any message passes through the processor unchanged."""
        original = "Hi! What's your timeline for selling?"
        resp, ctx = _make_response(message=original, detected_language="en")
        ctx.is_first_message = True
        result = await stage.process(resp, ctx)

        assert result.message == original


# ===========================================================================
# 10. Carrier Spam Guard
# ===========================================================================


class TestCarrierSpamGuard:
    """Carrier spam trigger sanitization in SMS truncation stage."""

    @pytest.fixture
    def stage(self):
        return SMSTruncationProcessor()

    @pytest.mark.asyncio
    async def test_spam_word_lowered(self, stage):
        """All-caps spam trigger words are lowercased."""
        resp, ctx = _make_response(
            message="Get a FREE home valuation today!",
            channel="sms",
        )
        result = await stage.process(resp, ctx)

        assert "FREE" not in result.message
        assert "Free" in result.message or "free" in result.message

    @pytest.mark.asyncio
    async def test_excessive_caps_converted(self, stage):
        """Messages with >30% uppercase are converted to sentence case."""
        resp, ctx = _make_response(
            message="YOUR HOME IS WORTH MORE THAN YOU THINK! CALL NOW FOR DETAILS.",
            channel="sms",
        )
        result = await stage.process(resp, ctx)

        # Should be sentence case, not all-caps
        alpha_chars = [c for c in result.message if c.isalpha()]
        upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars) if alpha_chars else 0
        assert upper_ratio < 0.30

    @pytest.mark.asyncio
    async def test_url_shortener_warning(self, stage):
        """URL shorteners are detected and logged (message unchanged)."""
        msg = "Check this out: https://bit.ly/abc123"
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)

        # Message should still contain the URL (we warn, not remove)
        assert "bit.ly" in result.message

    @pytest.mark.asyncio
    async def test_normal_message_not_modified_by_spam_guard(self, stage):
        """Normal messages without spam triggers pass through unchanged."""
        msg = "Thanks for sharing! What price would make you feel good about selling?"
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)

        assert result.message == msg
        assert result.action == ProcessingAction.PASS

    @pytest.mark.asyncio
    async def test_spam_guard_works_after_truncation(self, stage):
        """Spam guard runs after truncation on long messages."""
        # Long message with spam words that gets truncated
        msg = "A" * 200 + ". Get your FREE home valuation. " + "B" * 200
        resp, ctx = _make_response(message=msg, channel="sms")
        result = await stage.process(resp, ctx)

        assert len(result.message) <= SMS_MAX_CHARS
        # If FREE survived truncation, it should be lowercased
        if "free" in result.message.lower():
            assert "FREE" not in result.message
