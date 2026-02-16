"""Shared pytest fixtures for Voice AI Platform tests."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def tenant_id():
    """Return a test tenant ID."""
    return uuid.uuid4()


@pytest.fixture
def call_id():
    """Return a test call ID."""
    return uuid.uuid4()


@pytest.fixture
def mock_db_session():
    """Mock async database session for testing."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()
    return db


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for caching tests."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.exists = AsyncMock(return_value=False)
    redis.expire = AsyncMock()
    return redis


@pytest.fixture
def sample_call_data():
    """Sample call data for testing."""
    return {
        "direction": "inbound",
        "from_number": "+15551234567",
        "to_number": "+15559876543",
        "bot_type": "lead",
        "twilio_call_sid": "CA123456",
    }


@pytest.fixture
def sample_transcript():
    """Sample transcript data for testing."""
    return [
        {"speaker": "agent", "text": "Hi, this is Jorge. How can I help you today?"},
        {"speaker": "caller", "text": "I'm interested in buying a home in Rancho Cucamonga."},
        {"speaker": "agent", "text": "Great! What's your budget and timeline?"},
        {"speaker": "caller", "text": "Around $500k, and we're hoping to buy in 3 months."},
    ]


@pytest.fixture
def mock_twilio_handler():
    """Mock Twilio handler for testing."""
    handler = MagicMock()
    handler.account_sid = "test_sid"
    handler.auth_token = "test_token"
    handler.phone_number = "+15551234567"
    handler.base_url = "test.example.com"
    handler.generate_stream_twiml = MagicMock(
        return_value='<?xml version="1.0"?><Response><Connect><Stream url="wss://test.com/ws" /></Connect></Response>'
    )
    handler.initiate_outbound_call = AsyncMock(
        return_value={"call_sid": "CA123456", "status": "initiated"}
    )
    handler.validate_twilio_signature = MagicMock(return_value=True)
    return handler


@pytest.fixture
def mock_deepgram_client():
    """Mock Deepgram STT client."""
    client = AsyncMock()
    client.listen.asyncwebsocket.v = MagicMock()
    return client


@pytest.fixture
def mock_elevenlabs_client():
    """Mock ElevenLabs TTS client."""
    client = MagicMock()

    async def mock_stream(*args, **kwargs):
        yield b"audio_chunk_1"
        yield b"audio_chunk_2"

    client.text_to_speech.convert = MagicMock(return_value=mock_stream())
    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic (Claude) LLM client."""
    client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="This is a test response from Claude.")]
    client.messages.create = MagicMock(return_value=mock_message)
    return client


@pytest.fixture
def mock_stripe_client():
    """Mock Stripe client for billing tests."""
    client = MagicMock()
    client.SubscriptionItem.create_usage_record = MagicMock(
        return_value={"id": "ur_test123", "quantity": 5}
    )
    return client
