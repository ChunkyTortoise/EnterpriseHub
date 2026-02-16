"""Deepgram STT integration — real-time speech-to-text via WebSocket."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


@dataclass
class TranscriptResult:
    """A single transcript result from Deepgram."""

    text: str
    confidence: float
    is_final: bool
    speech_final: bool
    timestamp_ms: float
    duration_ms: float = 0.0


@dataclass
class DeepgramSTTProcessor:
    """Real-time speech-to-text via Deepgram WebSocket (Nova-3)."""

    api_key: str
    model: str = "nova-3"
    language: str = "en-US"
    sample_rate: int = 16000
    encoding: str = "linear16"
    endpointing_ms: int = 300
    interim_results: bool = True
    _connection: Any = field(default=None, repr=False)
    _callbacks: list[Callable] = field(default_factory=list, repr=False)

    def on_transcript(
        self, callback: Callable[[TranscriptResult], Coroutine[Any, Any, None]]
    ) -> None:
        """Register a callback for transcript results."""
        self._callbacks.append(callback)

    async def connect(self) -> None:
        """Open a live transcription WebSocket connection to Deepgram."""
        from deepgram import DeepgramClient, LiveOptions, LiveTranscriptionEvents

        client = DeepgramClient(self.api_key)
        options = LiveOptions(
            model=self.model,
            encoding=self.encoding,
            sample_rate=self.sample_rate,
            punctuate=True,
            interim_results=self.interim_results,
            utterance_end_ms=1000,
            vad_events=True,
            smart_format=True,
            language=self.language,
            endpointing=self.endpointing_ms,
        )

        self._connection = client.listen.asyncwebsocket.v("1")

        async def _handle_transcript(connection: Any, result: Any, **kwargs: Any) -> None:
            channel = result.channel
            if not channel or not channel.alternatives:
                return
            alt = channel.alternatives[0]
            transcript_result = TranscriptResult(
                text=alt.transcript,
                confidence=alt.confidence,
                is_final=result.is_final,
                speech_final=result.speech_final,
                timestamp_ms=result.start * 1000,
                duration_ms=result.duration * 1000,
            )
            for cb in self._callbacks:
                await cb(transcript_result)

        self._connection.on(LiveTranscriptionEvents.Transcript, _handle_transcript)
        await self._connection.start(options)
        logger.info("Deepgram STT connection established (model=%s)", self.model)

    async def send_audio(self, audio_bytes: bytes) -> None:
        """Send raw audio bytes to Deepgram for transcription."""
        if self._connection is None:
            raise RuntimeError("STT connection not established. Call connect() first.")
        await self._connection.send(audio_bytes)

    async def close(self) -> None:
        """Close the Deepgram WebSocket connection."""
        if self._connection:
            await self._connection.finish()
            self._connection = None
            logger.info("Deepgram STT connection closed")
