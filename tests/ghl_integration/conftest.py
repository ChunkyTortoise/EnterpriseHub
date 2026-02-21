"""
GHL Integration Test Suite

Tests for the unified GHL webhook infrastructure.
"""

import hashlib
import hmac
import json

# Fixtures path
import os
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "ghl_webhooks")


def load_fixture(filename: str) -> dict:
    """Load a webhook fixture file"""
    with open(os.path.join(FIXTURES_DIR, filename)) as f:
        return json.load(f)


@pytest.fixture
def contact_create_payload():
    return load_fixture("contact_create.json")


@pytest.fixture
def contact_update_payload():
    return load_fixture("contact_update.json")


@pytest.fixture
def conversation_message_payload():
    return load_fixture("conversation_message.json")


@pytest.fixture
def opportunity_create_payload():
    return load_fixture("opportunity_create.json")


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing"""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.zadd = AsyncMock(return_value=True)
    cache.zrem = AsyncMock(return_value=True)
    cache.zrangebyscore = AsyncMock(return_value=[])
    cache.lpush = AsyncMock(return_value=True)
    cache.lrem = AsyncMock(return_value=True)
    cache.lrange = AsyncMock(return_value=[])
    cache.zcard = AsyncMock(return_value=0)
    cache.llen = AsyncMock(return_value=0)
    return cache


@pytest.fixture
def mock_ghl_client():
    """Mock GHL API client"""
    client = Mock()
    client.get_contact = AsyncMock(
        return_value={
            "success": True,
            "data": {"id": "contact_abc123", "name": "John Smith", "email": "john@example.com"},
        }
    )
    client.update_contact = AsyncMock(return_value={"success": True})
    client.send_message = AsyncMock(return_value={"success": True})
    return client
