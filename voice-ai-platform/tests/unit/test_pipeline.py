"""Unit tests for voice pipeline components (STT, TTS, LLM, VoicePipeline)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_ai.pipeline.stt_processor import DeepgramSTTProcessor, TranscriptResult
from voice_ai.pipeline.tts_processor import ElevenLabsTTSProcessor
from voice_ai.pipeline.llm_processor import LLMProcessor
from voice_ai.pipeline.voice_pipeline import VoicePipeline, PipelineState


@pytest.fixture
def mock_deepgram_client():
    """Mock Deepgram client — patches the library imports used inside connect()."""
    with (
        patch("deepgram.DeepgramClient") as mock,
        patch("deepgram.LiveOptions", create=True),
        patch("deepgram.LiveTranscriptionEvents", create=True),
    ):
        yield mock


@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs client — patches the library import inside initialize()."""
    with patch("elevenlabs.client.AsyncElevenLabs") as mock:
        yield mock


class TestDeepgramSTTProcessor:
    """Test Deepgram STT processor."""

    @pytest.mark.asyncio
    async def test_connect_establishes_websocket(self, mock_deepgram_client):
        """Test that connect() establishes a WebSocket connection."""
        mock_connection = AsyncMock()
        mock_deepgram_client.return_value.listen.asyncwebsocket.v.return_value = mock_connection

        stt = DeepgramSTTProcessor(api_key="test_key")
        await stt.connect()

        assert stt._connection is not None

    @pytest.mark.asyncio
    async def test_send_audio_sends_to_websocket(self, mock_deepgram_client):
        """Test that send_audio() sends audio bytes to the WebSocket."""
        mock_connection = AsyncMock()

        stt = DeepgramSTTProcessor(api_key="test_key")
        stt._connection = mock_connection

        audio_data = b"fake_audio_bytes"
        await stt.send_audio(audio_data)

        mock_connection.send.assert_called_once_with(audio_data)

    @pytest.mark.asyncio
    async def test_transcript_callback_invoked_on_final_result(self, mock_deepgram_client):
        """Test that the transcript callback is invoked for final transcripts."""
        callback = AsyncMock()
        stt = DeepgramSTTProcessor(api_key="test_key")
        stt.on_transcript(callback)

        # Simulate receiving a final transcript
        result = TranscriptResult(
            text="Hello world",
            is_final=True,
            confidence=0.95,
            speech_final=True,
            timestamp_ms=1234.5,
        )

        # Manually invoke callbacks (in real code, this happens in the event handler)
        for cb in stt._callbacks:
            await cb(result)

        callback.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_close_shuts_down_connection(self, mock_deepgram_client):
        """Test that close() shuts down the WebSocket connection."""
        mock_connection = AsyncMock()
        stt = DeepgramSTTProcessor(api_key="test_key")
        stt._connection = mock_connection

        await stt.close()

        assert stt._connection is None


class TestElevenLabsTTSProcessor:
    """Test ElevenLabs TTS processor."""

    @pytest.mark.asyncio
    async def test_initialize_sets_up_client(self, mock_elevenlabs_client):
        """Test that initialize() sets up the ElevenLabs client."""
        tts = ElevenLabsTTSProcessor(api_key="test_key", voice_id="test_voice")
        await tts.initialize()

        # Client should be created
        assert tts._client is not None

    @pytest.mark.asyncio
    async def test_synthesize_yields_audio_chunks(self, mock_elevenlabs_client):
        """Test that synthesize() yields audio chunks."""
        mock_client = MagicMock()
        fake_audio = [b"chunk1", b"chunk2", b"chunk3"]

        async def fake_stream(*args, **kwargs):
            for chunk in fake_audio:
                yield chunk

        mock_client.text_to_speech.convert.return_value = fake_stream()

        tts = ElevenLabsTTSProcessor(api_key="test_key", voice_id="test_voice")
        tts._client = mock_client

        chunks = []
        async for chunk in tts.synthesize("Hello world"):
            chunks.append(chunk)

        assert chunks == fake_audio

    @pytest.mark.asyncio
    async def test_close_cleans_up_resources(self, mock_elevenlabs_client):
        """Test that close() cleans up resources."""
        tts = ElevenLabsTTSProcessor(api_key="test_key", voice_id="test_voice")
        tts._client = MagicMock()

        await tts.close()

        # Client should be cleaned up
        assert tts._client is None


class TestLLMProcessor:
    """Test LLM processor (Claude API via httpx)."""

    @pytest.mark.asyncio
    async def test_generate_response_returns_text(self):
        """Test that generate_response() returns text from Claude."""
        llm = LLMProcessor(
            api_key="test_key",
            model="claude-sonnet-4-5-20250929",
        )
        llm.set_system_prompt("You are a helpful assistant.")

        # Mock the httpx client used inside generate_response
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "This is the response"}]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_class.return_value = mock_client

            response = await llm.generate_response("Hello")

        assert response == "This is the response"
        mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_to_history_maintains_conversation(self):
        """Test that messages are added to conversation history."""
        llm = LLMProcessor(
            api_key="test_key",
            model="claude-sonnet-4-5-20250929",
        )

        llm.add_turn("user", "Hello")
        llm.add_turn("assistant", "Hi there")

        history = llm.get_history()
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
        assert history[1].content == "Hi there"


class TestVoicePipeline:
    """Test the full voice pipeline orchestration."""

    @pytest.fixture
    def mock_stt(self):
        """Mock STT processor."""
        return AsyncMock(spec=DeepgramSTTProcessor)

    @pytest.fixture
    def mock_tts(self):
        """Mock TTS processor."""
        mock = AsyncMock(spec=ElevenLabsTTSProcessor)
        # Make synthesize return an async generator
        async def fake_synth(text):
            yield b"audio1"
            yield b"audio2"

        mock.synthesize = fake_synth
        return mock

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM processor."""
        mock = AsyncMock(spec=LLMProcessor)
        mock.generate_response.return_value = "This is the response"
        return mock

    @pytest.fixture
    def pipeline(self, mock_stt, mock_tts, mock_llm):
        """Create a voice pipeline with mocked components."""
        return VoicePipeline(stt=mock_stt, llm=mock_llm, tts=mock_tts)

    @pytest.mark.asyncio
    async def test_start_initializes_all_components(self, pipeline, mock_stt, mock_tts):
        """Test that start() initializes all pipeline components."""
        await pipeline.start()

        mock_stt.on_transcript.assert_called_once()
        mock_stt.connect.assert_called_once()
        mock_tts.initialize.assert_called_once()
        assert pipeline.state == PipelineState.LISTENING

    @pytest.mark.asyncio
    async def test_stop_shuts_down_all_components(self, pipeline, mock_stt, mock_tts):
        """Test that stop() shuts down all pipeline components."""
        await pipeline.stop()

        mock_stt.close.assert_called_once()
        mock_tts.close.assert_called_once()
        assert pipeline.state == PipelineState.IDLE

    @pytest.mark.asyncio
    async def test_process_audio_sends_to_stt(self, pipeline, mock_stt):
        """Test that process_audio() sends audio to STT."""
        pipeline.state = PipelineState.LISTENING
        audio_bytes = b"test_audio"

        await pipeline.process_audio(audio_bytes)

        mock_stt.send_audio.assert_called_once_with(audio_bytes)

    @pytest.mark.asyncio
    async def test_barge_in_cancels_tts(self, pipeline, mock_stt):
        """Test that barge-in cancels ongoing TTS."""
        pipeline.state = PipelineState.SPEAKING
        pipeline._tts_task = asyncio.create_task(asyncio.sleep(10))

        await pipeline.process_audio(b"interrupt")

        # After barge-in, _tts_task is set to None and state is LISTENING
        assert pipeline.state == PipelineState.LISTENING

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, pipeline):
        """Test that pipeline tracks latency metrics."""
        # Metrics should start at zero
        assert pipeline.metrics.stt_latency_ms == 0.0
        assert pipeline.metrics.llm_latency_ms == 0.0
        assert pipeline.metrics.tts_latency_ms == 0.0
        assert pipeline.metrics.total_latency_ms == 0.0

    @pytest.mark.asyncio
    async def test_audio_output_callback_invoked(self, pipeline):
        """Test that audio output callback is invoked when TTS generates audio."""
        callback = AsyncMock()
        pipeline.on_audio_output(callback)

        # Simulate TTS generating audio
        transcript = TranscriptResult(
            text="Hello",
            is_final=True,
            confidence=0.9,
            speech_final=True,
            timestamp_ms=1000,
        )

        pipeline.state = PipelineState.LISTENING
        await pipeline._handle_transcript(transcript)

        # Wait for the TTS task to complete
        if pipeline._tts_task:
            await asyncio.wait_for(pipeline._tts_task, timeout=1.0)

        # Callback should have been called with audio chunks
        assert callback.call_count >= 1
