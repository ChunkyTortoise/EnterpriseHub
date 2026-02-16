"""Main Pipecat voice pipeline orchestration — STT -> LLM -> TTS."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

from voice_ai.pipeline.stt_processor import DeepgramSTTProcessor, TranscriptResult
from voice_ai.pipeline.tts_processor import ElevenLabsTTSProcessor
from voice_ai.pipeline.llm_processor import LLMProcessor

logger = logging.getLogger(__name__)


class PipelineState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


@dataclass
class PipelineMetrics:
    """Latency and performance metrics for the pipeline."""

    stt_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    tts_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    tokens_generated: int = 0


@dataclass
class VoicePipeline:
    """Orchestrates the STT -> LLM -> TTS pipeline with barge-in support.

    This is the core real-time voice processing pipeline. It:
    1. Receives audio from Twilio via WebSocket
    2. Streams audio to Deepgram for real-time transcription
    3. Feeds final transcripts to Claude for response generation
    4. Streams Claude's response tokens to ElevenLabs for TTS
    5. Sends TTS audio back to the caller via Twilio WebSocket

    Supports barge-in: if the caller speaks while the agent is speaking,
    TTS is cancelled and the pipeline switches back to listening mode.
    """

    stt: DeepgramSTTProcessor
    llm: LLMProcessor
    tts: ElevenLabsTTSProcessor
    state: PipelineState = PipelineState.IDLE
    _audio_output_callback: Callable[[bytes], Coroutine[Any, Any, None]] | None = field(
        default=None, repr=False
    )
    _transcript_callback: Callable[[TranscriptResult], Coroutine[Any, Any, None]] | None = field(
        default=None, repr=False
    )
    _tts_task: asyncio.Task[Any] | None = field(default=None, repr=False)
    _metrics: PipelineMetrics = field(default_factory=PipelineMetrics, repr=False)

    def on_audio_output(
        self, callback: Callable[[bytes], Coroutine[Any, Any, None]]
    ) -> None:
        """Register callback for outgoing audio (to send back to caller)."""
        self._audio_output_callback = callback

    def on_transcript(
        self, callback: Callable[[TranscriptResult], Coroutine[Any, Any, None]]
    ) -> None:
        """Register callback for transcript events (for storage/analytics)."""
        self._transcript_callback = callback

    async def start(self) -> None:
        """Initialize all pipeline components and start listening."""
        self.stt.on_transcript(self._handle_transcript)
        await self.stt.connect()
        await self.tts.initialize()
        self.state = PipelineState.LISTENING
        logger.info("Voice pipeline started")

    async def stop(self) -> None:
        """Shut down all pipeline components."""
        await self._cancel_tts()
        await self.stt.close()
        await self.tts.close()
        self.state = PipelineState.IDLE
        logger.info("Voice pipeline stopped")

    async def process_audio(self, audio_bytes: bytes) -> None:
        """Process incoming audio from the caller.

        If the agent is currently speaking and we detect speech,
        this triggers barge-in (interrupts the agent).
        """
        if self.state == PipelineState.SPEAKING:
            # Barge-in: caller is speaking while agent is talking
            await self._handle_barge_in()

        await self.stt.send_audio(audio_bytes)

    async def _handle_transcript(self, result: TranscriptResult) -> None:
        """Handle transcript results from Deepgram STT."""
        if self._transcript_callback:
            await self._transcript_callback(result)

        if not result.is_final or not result.text.strip():
            return

        logger.info("Final transcript: %s (confidence=%.2f)", result.text, result.confidence)
        self.state = PipelineState.PROCESSING

        stt_done = time.monotonic()

        # Generate LLM response and stream to TTS
        self._tts_task = asyncio.create_task(
            self._generate_and_speak(result.text, stt_done)
        )

    async def _generate_and_speak(self, user_text: str, stt_done_time: float) -> None:
        """Generate LLM response and stream it through TTS."""
        try:
            self.state = PipelineState.SPEAKING
            llm_start = time.monotonic()
            first_token = True

            response_text = await self.llm.generate_response(user_text)
            llm_done = time.monotonic()
            self._metrics.llm_latency_ms = (llm_done - llm_start) * 1000

            tts_start = time.monotonic()
            async for audio_chunk in self.tts.synthesize(response_text):
                if self.state == PipelineState.INTERRUPTED:
                    logger.info("TTS interrupted by barge-in")
                    return
                if first_token:
                    self._metrics.tts_latency_ms = (time.monotonic() - tts_start) * 1000
                    self._metrics.total_latency_ms = (time.monotonic() - stt_done_time) * 1000
                    first_token = False
                if self._audio_output_callback:
                    await self._audio_output_callback(audio_chunk)

            self.state = PipelineState.LISTENING
        except asyncio.CancelledError:
            logger.info("TTS generation cancelled")
        except Exception:
            logger.exception("Error in generate_and_speak")
            self.state = PipelineState.LISTENING

    async def _handle_barge_in(self) -> None:
        """Handle barge-in: cancel current TTS and switch to listening."""
        logger.info("Barge-in detected — cancelling TTS")
        self.state = PipelineState.INTERRUPTED
        await self._cancel_tts()
        self.state = PipelineState.LISTENING

    async def _cancel_tts(self) -> None:
        """Cancel any in-progress TTS task."""
        if self._tts_task and not self._tts_task.done():
            self._tts_task.cancel()
            try:
                await self._tts_task
            except asyncio.CancelledError:
                pass
            self._tts_task = None

    @property
    def metrics(self) -> PipelineMetrics:
        """Return current pipeline metrics."""
        return self._metrics
