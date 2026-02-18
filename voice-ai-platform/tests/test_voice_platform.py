"""Comprehensive tests for voice-ai-platform — covers bot adapters, handoff manager,
config, LLM processor, pipeline states, and API schemas.

These tests fill the coverage gap for modules not exercised by existing unit tests.
All external dependencies (Deepgram, ElevenLabs, Twilio, Anthropic, Stripe) are mocked.
"""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from voice_ai.api.agents import (
    AgentPersonaCreate,
    AgentPersonaUpdate,
)
from voice_ai.api.calls import (
    OutboundCallRequest,
    PaginatedCallsResponse,
)
from voice_ai.config import Settings, get_settings
from voice_ai.pipeline.buyerbot_adapter import BuyerBotAdapter
from voice_ai.pipeline.handoff_manager import (
    HANDOFF_CONFIDENCE_THRESHOLD,
    HandoffDecision,
    HandoffManager,
)
from voice_ai.pipeline.leadbot_adapter import LeadBotAdapter
from voice_ai.pipeline.llm_processor import ConversationTurn, LLMProcessor
from voice_ai.pipeline.sellerbot_adapter import SellerBotAdapter
from voice_ai.pipeline.stt_processor import DeepgramSTTProcessor, TranscriptResult
from voice_ai.pipeline.tts_processor import ElevenLabsTTSProcessor
from voice_ai.pipeline.voice_pipeline import PipelineMetrics, PipelineState
from voice_ai.telephony.recording import (
    TWO_PARTY_CONSENT_STATES,
    RecordingConsent,
)

# ---------------------------------------------------------------------------
# Bot Adapter Tests
# ---------------------------------------------------------------------------


class TestLeadBotAdapter:
    """Test LeadBotAdapter — system prompt, greeting, handoff signals."""

    def test_default_system_prompt(self):
        adapter = LeadBotAdapter()
        prompt = adapter.get_system_prompt()
        assert "Jorge" in prompt
        assert "qualify" in prompt.lower()

    def test_persona_override(self):
        adapter = LeadBotAdapter()
        custom = "You are a custom persona."
        assert adapter.get_system_prompt(persona_override=custom) == custom

    def test_greeting_includes_agency(self):
        adapter = LeadBotAdapter(agency_name="Acme Realty")
        greeting = adapter.get_greeting()
        assert "Acme Realty" in greeting
        assert "Jorge" in greeting

    def test_default_greeting(self):
        adapter = LeadBotAdapter()
        greeting = adapter.get_greeting()
        assert "real estate" in greeting.lower()

    @pytest.mark.asyncio
    async def test_process_message_returns_structured_dict(self):
        adapter = LeadBotAdapter()
        result = await adapter.process_message("I want to buy a house")
        assert result["bot_type"] == "lead"
        assert "handoff_signals" in result
        assert "lead_score" in result

    def test_extract_handoff_signals_buyer_keywords(self):
        adapter = LeadBotAdapter()
        history = [
            {"role": "user", "content": "I want to buy a home and I'm pre-approved for a mortgage"},
        ]
        signals = adapter.extract_handoff_signals(history)
        assert "buyer" in signals
        assert "seller" in signals
        assert signals["buyer"] > 0

    def test_extract_handoff_signals_seller_keywords(self):
        adapter = LeadBotAdapter()
        history = [
            {"role": "user", "content": "I want to sell my house and get a CMA"},
        ]
        signals = adapter.extract_handoff_signals(history)
        assert signals["seller"] > 0

    def test_extract_handoff_signals_no_keywords(self):
        adapter = LeadBotAdapter()
        history = [
            {"role": "user", "content": "Hello, how are you today?"},
        ]
        signals = adapter.extract_handoff_signals(history)
        assert signals["buyer"] == 0
        assert signals["seller"] == 0

    def test_extract_handoff_signals_ignores_agent_messages(self):
        adapter = LeadBotAdapter()
        history = [
            {"role": "agent", "content": "Would you like to buy or sell?"},
            {"role": "user", "content": "Just browsing."},
        ]
        signals = adapter.extract_handoff_signals(history)
        # The agent message mentions buy and sell, but those should not count
        assert signals["buyer"] == 0

    def test_handoff_score_capped_at_one(self):
        adapter = LeadBotAdapter()
        # Stuff all buyer keywords into a single message
        history = [
            {"role": "user", "content": "buy purchase pre-approved budget mortgage home loan"},
        ]
        signals = adapter.extract_handoff_signals(history)
        assert signals["buyer"] <= 1.0


class TestBuyerBotAdapter:
    """Test BuyerBotAdapter — system prompt, greeting, process_message."""

    def test_default_system_prompt(self):
        adapter = BuyerBotAdapter()
        prompt = adapter.get_system_prompt()
        assert "buyer" in prompt.lower()

    def test_persona_override(self):
        adapter = BuyerBotAdapter()
        custom = "Custom buyer prompt"
        assert adapter.get_system_prompt(persona_override=custom) == custom

    def test_greeting_mentions_home(self):
        adapter = BuyerBotAdapter()
        greeting = adapter.get_greeting()
        assert "home" in greeting.lower()

    @pytest.mark.asyncio
    async def test_process_message_returns_buyer_type(self):
        adapter = BuyerBotAdapter()
        result = await adapter.process_message("What homes are available?")
        assert result["bot_type"] == "buyer"
        assert "financial_readiness" in result


class TestSellerBotAdapter:
    """Test SellerBotAdapter — system prompt, greeting, process_message."""

    def test_default_system_prompt(self):
        adapter = SellerBotAdapter()
        prompt = adapter.get_system_prompt()
        assert "seller" in prompt.lower()

    def test_persona_override(self):
        adapter = SellerBotAdapter()
        custom = "Custom seller prompt"
        assert adapter.get_system_prompt(persona_override=custom) == custom

    def test_greeting_mentions_selling(self):
        adapter = SellerBotAdapter()
        greeting = adapter.get_greeting()
        assert "sell" in greeting.lower()

    @pytest.mark.asyncio
    async def test_process_message_returns_seller_type(self):
        adapter = SellerBotAdapter()
        result = await adapter.process_message("How much is my home worth?")
        assert result["bot_type"] == "seller"
        assert "frs_score" in result
        assert "pcs_score" in result


# ---------------------------------------------------------------------------
# Handoff Manager Tests
# ---------------------------------------------------------------------------


class TestHandoffDecision:
    """Test HandoffDecision dataclass."""

    def test_default_no_handoff(self):
        decision = HandoffDecision(should_handoff=False)
        assert decision.should_handoff is False
        assert decision.target_bot is None
        assert decision.confidence == 0.0
        assert decision.reason == ""

    def test_handoff_with_target(self):
        decision = HandoffDecision(
            should_handoff=True,
            target_bot="buyer",
            confidence=0.85,
            reason="Strong buyer intent",
        )
        assert decision.should_handoff is True
        assert decision.target_bot == "buyer"
        assert decision.confidence == 0.85


class TestHandoffManager:
    """Test HandoffManager — evaluate, execute, cooldown, circular prevention."""

    def test_get_current_adapter_lead(self):
        mgr = HandoffManager(current_bot_type="lead")
        adapter = mgr.get_current_adapter()
        assert isinstance(adapter, LeadBotAdapter)

    def test_get_current_adapter_buyer(self):
        mgr = HandoffManager(current_bot_type="buyer")
        adapter = mgr.get_current_adapter()
        assert isinstance(adapter, BuyerBotAdapter)

    def test_get_current_adapter_seller(self):
        mgr = HandoffManager(current_bot_type="seller")
        adapter = mgr.get_current_adapter()
        assert isinstance(adapter, SellerBotAdapter)

    def test_get_current_adapter_unknown_defaults_to_lead(self):
        mgr = HandoffManager(current_bot_type="unknown")
        adapter = mgr.get_current_adapter()
        assert isinstance(adapter, LeadBotAdapter)

    def test_evaluate_empty_history_no_handoff(self):
        mgr = HandoffManager(current_bot_type="lead")
        decision = mgr.evaluate_handoff([])
        assert decision.should_handoff is False

    def test_evaluate_cooldown_prevents_handoff(self):
        mgr = HandoffManager(current_bot_type="lead")
        mgr._last_handoff_time = time.monotonic()  # Just happened
        history = [
            {"role": "user", "content": "I want to buy a home with a mortgage and I'm pre-approved"},
        ]
        decision = mgr.evaluate_handoff(history)
        assert decision.should_handoff is False
        assert "Cooldown" in decision.reason

    def test_evaluate_with_strong_buyer_signals(self):
        mgr = HandoffManager(current_bot_type="lead")
        mgr._last_handoff_time = 0  # No cooldown
        # Include enough keywords to exceed the threshold
        history = [
            {
                "role": "user",
                "content": (
                    "I want to buy a house, I'm pre-approved, "
                    "budget is set, got a mortgage and home loan"
                ),
            },
        ]
        decision = mgr.evaluate_handoff(history)
        # With 5/6 buyer keywords, score = 0.833 > 0.7 threshold
        assert decision.should_handoff is True
        assert decision.target_bot == "buyer"
        assert decision.confidence >= HANDOFF_CONFIDENCE_THRESHOLD

    def test_evaluate_weak_signals_no_handoff(self):
        mgr = HandoffManager(current_bot_type="lead")
        mgr._last_handoff_time = 0
        history = [
            {"role": "user", "content": "I might want to buy something maybe"},
        ]
        decision = mgr.evaluate_handoff(history)
        # Only 1/6 buyer keyword => score ~0.17 < 0.7
        assert decision.should_handoff is False

    @pytest.mark.asyncio
    async def test_execute_handoff_changes_bot_type(self):
        mock_llm = MagicMock()
        mgr = HandoffManager(current_bot_type="lead", llm=mock_llm)
        greeting = await mgr.execute_handoff("buyer", [])

        assert mgr.current_bot_type == "buyer"
        assert "home" in greeting.lower()
        mock_llm.set_system_prompt.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handoff_records_history(self):
        mgr = HandoffManager(current_bot_type="lead")
        await mgr.execute_handoff("seller", [])

        assert len(mgr._handoff_history) == 1
        assert mgr._handoff_history[0]["from"] == "lead"
        assert mgr._handoff_history[0]["to"] == "seller"

    @pytest.mark.asyncio
    async def test_execute_handoff_without_llm(self):
        mgr = HandoffManager(current_bot_type="lead", llm=None)
        greeting = await mgr.execute_handoff("buyer", [])
        assert mgr.current_bot_type == "buyer"
        assert len(greeting) > 0

    def test_confidence_threshold_value(self):
        assert HANDOFF_CONFIDENCE_THRESHOLD == 0.7


# ---------------------------------------------------------------------------
# Config Tests
# ---------------------------------------------------------------------------


class TestSettings:
    """Test Settings model defaults and behavior."""

    def test_default_app_name(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.app_name == "Voice AI Platform"

    def test_default_debug_false(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.debug is False

    def test_default_billing_rates(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.rate_payg == 0.20
            assert settings.rate_growth == 0.15
            assert settings.rate_enterprise == 0.12
            assert settings.rate_whitelabel == 0.10

    def test_default_pipeline_settings(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert settings.stt_endpointing_ms == 300
            assert settings.tts_model == "eleven_flash_v2_5"
            assert settings.vad_silence_threshold_ms == 1000

    def test_default_llm_model(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = Settings()
            assert "claude" in settings.llm_model

    def test_get_settings_returns_cached_instance(self):
        # Reset the cached instance
        import voice_ai.config as config_mod

        config_mod._settings = None

        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

        # Clean up
        config_mod._settings = None


# ---------------------------------------------------------------------------
# LLM Processor Tests (additional coverage)
# ---------------------------------------------------------------------------


class TestLLMProcessorHistory:
    """Test LLM processor conversation history management."""

    def test_add_turn_stores_conversation(self):
        llm = LLMProcessor(api_key="test")
        llm.add_turn("user", "Hello")
        assert len(llm.get_history()) == 1
        assert llm.get_history()[0].role == "user"
        assert llm.get_history()[0].content == "Hello"

    def test_add_turn_with_timestamp(self):
        llm = LLMProcessor(api_key="test")
        llm.add_turn("user", "Hi", timestamp_ms=1234.5)
        assert llm.get_history()[0].timestamp_ms == 1234.5

    def test_history_trimmed_to_max(self):
        llm = LLMProcessor(api_key="test", max_history_turns=3)
        for i in range(5):
            llm.add_turn("user", f"Message {i}")
        history = llm.get_history()
        assert len(history) == 3
        assert history[0].content == "Message 2"
        assert history[-1].content == "Message 4"

    def test_clear_history(self):
        llm = LLMProcessor(api_key="test")
        llm.add_turn("user", "Hello")
        llm.add_turn("assistant", "Hi")
        assert len(llm.get_history()) == 2

        llm.clear_history()
        assert len(llm.get_history()) == 0

    def test_set_system_prompt(self):
        llm = LLMProcessor(api_key="test")
        llm.set_system_prompt("You are a helpful assistant.")
        assert llm._system_prompt == "You are a helpful assistant."

    def test_get_history_returns_copy(self):
        llm = LLMProcessor(api_key="test")
        llm.add_turn("user", "Hello")
        history = llm.get_history()
        history.clear()  # Modifying copy should not affect internal state
        assert len(llm.get_history()) == 1


class TestConversationTurn:
    """Test ConversationTurn dataclass."""

    def test_defaults(self):
        turn = ConversationTurn(role="user", content="Hello")
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.timestamp_ms == 0.0

    def test_with_timestamp(self):
        turn = ConversationTurn(role="assistant", content="Hi", timestamp_ms=999.9)
        assert turn.timestamp_ms == 999.9


# ---------------------------------------------------------------------------
# Pipeline States Tests
# ---------------------------------------------------------------------------


class TestPipelineState:
    """Test pipeline state enum values."""

    def test_state_values(self):
        assert PipelineState.IDLE == "idle"
        assert PipelineState.LISTENING == "listening"
        assert PipelineState.PROCESSING == "processing"
        assert PipelineState.SPEAKING == "speaking"
        assert PipelineState.INTERRUPTED == "interrupted"

    def test_all_states_present(self):
        states = {s.value for s in PipelineState}
        assert "idle" in states
        assert "listening" in states
        assert "processing" in states
        assert "speaking" in states
        assert "interrupted" in states


class TestPipelineMetrics:
    """Test pipeline metrics dataclass."""

    def test_defaults_zero(self):
        metrics = PipelineMetrics()
        assert metrics.stt_latency_ms == 0.0
        assert metrics.llm_latency_ms == 0.0
        assert metrics.tts_latency_ms == 0.0
        assert metrics.total_latency_ms == 0.0
        assert metrics.tokens_generated == 0

    def test_custom_values(self):
        metrics = PipelineMetrics(
            stt_latency_ms=50.5,
            llm_latency_ms=200.0,
            tts_latency_ms=75.3,
            total_latency_ms=325.8,
            tokens_generated=42,
        )
        assert metrics.stt_latency_ms == 50.5
        assert metrics.tokens_generated == 42


# ---------------------------------------------------------------------------
# API Schema Tests
# ---------------------------------------------------------------------------


class TestAgentPersonaSchemas:
    """Test Pydantic schemas for agent persona API."""

    def test_create_schema_defaults(self):
        schema = AgentPersonaCreate(name="Jorge Lead", bot_type="lead")
        assert schema.name == "Jorge Lead"
        assert schema.bot_type == "lead"
        assert schema.language == "en"
        assert schema.voice_id is None
        assert schema.settings == {}

    def test_create_schema_full(self):
        schema = AgentPersonaCreate(
            name="Jorge Buyer",
            bot_type="buyer",
            voice_id="voice_123",
            language="es",
            system_prompt_override="Custom prompt",
            greeting_message="Hola!",
            transfer_number="+15551234567",
            settings={"speed": 1.2},
        )
        assert schema.voice_id == "voice_123"
        assert schema.language == "es"

    def test_update_schema_all_optional(self):
        schema = AgentPersonaUpdate()
        assert schema.name is None
        assert schema.voice_id is None
        assert schema.is_active is None


class TestCallSchemas:
    """Test Pydantic schemas for call API."""

    def test_outbound_request_defaults(self):
        req = OutboundCallRequest(to_number="+15551234567")
        assert req.to_number == "+15551234567"
        assert req.bot_type == "lead"
        assert req.agent_persona_id is None
        assert req.context == {}

    def test_paginated_response(self):
        resp = PaginatedCallsResponse(items=[], total=0, page=1, size=50)
        assert resp.items == []
        assert resp.total == 0
        assert resp.page == 1
        assert resp.size == 50


# ---------------------------------------------------------------------------
# STT Processor Tests (additional coverage)
# ---------------------------------------------------------------------------


class TestTranscriptResult:
    """Test TranscriptResult dataclass."""

    def test_basic_result(self):
        result = TranscriptResult(
            text="Hello",
            confidence=0.95,
            is_final=True,
            speech_final=True,
            timestamp_ms=1000.0,
        )
        assert result.text == "Hello"
        assert result.confidence == 0.95
        assert result.duration_ms == 0.0  # default

    def test_result_with_duration(self):
        result = TranscriptResult(
            text="Hi there",
            confidence=0.88,
            is_final=False,
            speech_final=False,
            timestamp_ms=500.0,
            duration_ms=250.0,
        )
        assert result.is_final is False
        assert result.duration_ms == 250.0


class TestDeepgramSTTProcessorEdgeCases:
    """Test edge cases for STT processor."""

    @pytest.mark.asyncio
    async def test_send_audio_without_connection_raises(self):
        stt = DeepgramSTTProcessor(api_key="test_key")
        with pytest.raises(RuntimeError, match="STT connection not established"):
            await stt.send_audio(b"audio")

    @pytest.mark.asyncio
    async def test_close_with_no_connection(self):
        stt = DeepgramSTTProcessor(api_key="test_key")
        assert stt._connection is None
        await stt.close()  # Should not raise
        assert stt._connection is None

    def test_default_config_values(self):
        stt = DeepgramSTTProcessor(api_key="test_key")
        assert stt.model == "nova-3"
        assert stt.language == "en-US"
        assert stt.sample_rate == 16000
        assert stt.encoding == "linear16"
        assert stt.endpointing_ms == 300
        assert stt.interim_results is True


# ---------------------------------------------------------------------------
# TTS Processor Tests (additional coverage)
# ---------------------------------------------------------------------------


class TestElevenLabsTTSEdgeCases:
    """Test edge cases for TTS processor."""

    @pytest.mark.asyncio
    async def test_synthesize_without_init_raises(self):
        tts = ElevenLabsTTSProcessor(api_key="test_key")
        with pytest.raises(RuntimeError, match="TTS client not initialized"):
            async for _ in tts.synthesize("Hello"):
                pass

    @pytest.mark.asyncio
    async def test_stream_text_to_speech_without_init_raises(self):
        tts = ElevenLabsTTSProcessor(api_key="test_key")

        async def text_gen():
            yield "Hello"

        with pytest.raises(RuntimeError, match="TTS client not initialized"):
            async for _ in tts.stream_text_to_speech(text_gen()):
                pass

    def test_default_config_values(self):
        tts = ElevenLabsTTSProcessor(api_key="test_key")
        assert tts.voice_id == "21m00Tcm4TlvDq8ikWAM"
        assert tts.model_id == "eleven_flash_v2_5"
        assert tts.output_format == "pcm_16000"


# ---------------------------------------------------------------------------
# Recording Module Tests (additional coverage)
# ---------------------------------------------------------------------------


class TestRecordingConsent:
    """Test RecordingConsent dataclass."""

    def test_consent_given(self):
        consent = RecordingConsent(consent_given=True, needs_prompt=False)
        assert consent.consent_given is True
        assert consent.disclosure_text == ""

    def test_consent_with_disclosure(self):
        consent = RecordingConsent(
            consent_given=False, needs_prompt=True, disclosure_text="AI assistant"
        )
        assert consent.consent_given is False
        assert consent.disclosure_text == "AI assistant"


class TestTwoPartyConsentStates:
    """Test the two-party consent state list."""

    def test_california_included(self):
        assert "CA" in TWO_PARTY_CONSENT_STATES

    def test_florida_included(self):
        assert "FL" in TWO_PARTY_CONSENT_STATES

    def test_texas_not_included(self):
        assert "TX" not in TWO_PARTY_CONSENT_STATES

    def test_expected_count(self):
        # 11 two-party consent states
        assert len(TWO_PARTY_CONSENT_STATES) == 11
