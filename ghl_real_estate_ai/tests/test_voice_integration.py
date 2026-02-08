"""
Tests for Voice AI Integration Features (Phase 3)
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.voice_service import VoiceService


@pytest.mark.asyncio
async def test_voice_transcription():
    """Test transcribing audio to text."""
    service = VoiceService()
    # In test mode, it should return mock transcription
    text = await service.transcribe_audio(b"fake_audio")
    assert "bedroom" in text
    assert "Austin" in text


@pytest.mark.asyncio
async def test_voice_synthesis():
    """Test synthesizing text to speech."""
    service = VoiceService()
    # In test mode, it should return mock audio bytes
    audio = await service.synthesize_speech("Hello Jorge!")
    assert audio == b"mock_audio_content"


@pytest.mark.asyncio
async def test_voice_sentiment():
    """Test analyzing voice sentiment."""
    service = VoiceService()
    sentiment = service.analyze_voice_sentiment({})
    assert sentiment == "neutral"
