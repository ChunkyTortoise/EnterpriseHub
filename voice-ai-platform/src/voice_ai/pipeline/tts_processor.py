"""ElevenLabs TTS integration — streaming text-to-speech."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ElevenLabsTTSProcessor:
    """Streaming text-to-speech via ElevenLabs WebSocket."""

    api_key: str
    voice_id: str = "21m00Tcm4TlvDq8ikWAM"
    model_id: str = "eleven_flash_v2_5"
    output_format: str = "pcm_16000"
    _client: Any = field(default=None, repr=False)

    async def initialize(self) -> None:
        """Initialize the ElevenLabs async client."""
        from elevenlabs.client import AsyncElevenLabs

        self._client = AsyncElevenLabs(api_key=self.api_key)
        logger.info("ElevenLabs TTS client initialized (voice=%s, model=%s)", self.voice_id, self.model_id)

    async def synthesize(self, text: str) -> AsyncIterator[bytes]:
        """Convert text to speech, yielding audio chunks."""
        if self._client is None:
            raise RuntimeError("TTS client not initialized. Call initialize() first.")
        async for chunk in self._client.text_to_speech.convert(
            voice_id=self.voice_id,
            text=text,
            model_id=self.model_id,
            output_format=self.output_format,
        ):
            yield chunk

    async def stream_text_to_speech(self, text_chunks: AsyncIterator[str]) -> AsyncIterator[bytes]:
        """Stream text chunks to TTS, yield audio chunks for real-time playback.

        Uses ElevenLabs input streaming for lowest latency.
        """
        if self._client is None:
            raise RuntimeError("TTS client not initialized. Call initialize() first.")

        async for audio_chunk in self._client.text_to_speech.stream(
            voice_id=self.voice_id,
            text=text_chunks,
            model_id=self.model_id,
            output_format=self.output_format,
        ):
            yield audio_chunk

    async def close(self) -> None:
        """Clean up resources."""
        self._client = None
        logger.info("ElevenLabs TTS client closed")
