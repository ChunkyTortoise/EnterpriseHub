"""
Tests for Buyer Bot Conversation Memory Service (Task #29)

Tests:
- State persistence and retrieval
- TTL expiration handling
- State compression for large conversations
- Graceful handling of missing/expired state
- Multi-session continuity scenarios
- Configuration validation
"""

import gzip
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.buyer_conversation_memory import (
    BuyerConversationMemory,
    get_buyer_conversation_memory,
    reset_buyer_conversation_memory,
)


@pytest.fixture
def mock_cache():
    """Mock CacheService for isolated testing."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_config():
    """Mock Jorge configuration."""
    config = MagicMock()
    config.buyer_bot.conversation_memory.enabled = True
    config.buyer_bot.conversation_memory.ttl_days = 30
    config.buyer_bot.conversation_memory.compress_threshold_bytes = 5120
    config.buyer_bot.conversation_memory.max_history_messages = 50
    config.buyer_bot.conversation_memory.cache_key_prefix = "buyer_conversation_memory"
    return config


@pytest.fixture
def buyer_memory(mock_cache, mock_config):
    """Create BuyerConversationMemory instance with mocks."""
    with patch(
        "ghl_real_estate_ai.services.jorge.buyer_conversation_memory.get_cache_service", return_value=mock_cache
    ):
        with patch("ghl_real_estate_ai.services.jorge.buyer_conversation_memory.get_config", return_value=mock_config):
            memory = BuyerConversationMemory()
            return memory


@pytest.fixture
def sample_state():
    """Sample conversation state for testing."""
    return {
        "conversation_history": [
            {"role": "user", "content": "I want to buy a house"},
            {"role": "assistant", "content": "Great! What's your budget?"},
            {"role": "user", "content": "$400k"},
        ],
        "financial_readiness_score": 75.0,
        "buying_motivation_score": 80.0,
        "budget_range": {"min": 350000, "max": 450000},
        "property_preferences": {
            "bedrooms_min": 3,
            "bathrooms_min": 2.0,
            "property_type": "single_family",
        },
        "urgency_level": "3_months",
        "financing_status": "pre_approved",
        "buyer_persona": "Ready-Now Buyer",
        "buyer_name": "John Doe",
        "buyer_phone": "+1234567890",
    }


class TestBuyerConversationMemory:
    """Test suite for BuyerConversationMemory."""

    @pytest.mark.asyncio
    async def test_save_state_success(self, buyer_memory, mock_cache, sample_state):
        """Test successful state persistence."""
        contact_id = "buyer_123"

        success = await buyer_memory.save_state(contact_id, sample_state)

        assert success is True
        mock_cache.set.assert_called_once()

        # Verify call arguments
        call_args = mock_cache.set.call_args
        cache_key = call_args[0][0]
        storage_data = call_args[0][1]
        ttl = call_args[1]["ttl"]

        assert cache_key == f"buyer_conversation_memory:{contact_id}"
        assert ttl == 30 * 86400  # 30 days in seconds
        assert "compressed" in storage_data
        assert "data" in storage_data

    @pytest.mark.asyncio
    async def test_save_state_disabled(self, buyer_memory, mock_cache, sample_state):
        """Test save does nothing when disabled."""
        buyer_memory.enabled = False
        contact_id = "buyer_123"

        success = await buyer_memory.save_state(contact_id, sample_state)

        assert success is False
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_state_empty_contact_id(self, buyer_memory, mock_cache, sample_state):
        """Test save fails with empty contact ID."""
        success = await buyer_memory.save_state("", sample_state)

        assert success is False
        mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_state_success(self, buyer_memory, mock_cache, sample_state):
        """Test successful state retrieval."""
        contact_id = "buyer_123"

        # Prepare saved state
        persist_state = buyer_memory._prepare_state_for_storage(sample_state)
        persist_state["last_interaction_timestamp"] = datetime.now(timezone.utc).isoformat()
        persist_state["state_version"] = "1.0"

        storage_data = {
            "compressed": False,
            "data": json.dumps(persist_state, default=str),
        }
        mock_cache.get.return_value = storage_data

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is not None
        assert loaded_state["financial_readiness_score"] == 75.0
        assert loaded_state["budget_range"]["min"] == 350000
        assert "last_interaction_timestamp" in loaded_state
        mock_cache.get.assert_called_once_with(f"buyer_conversation_memory:{contact_id}")

    @pytest.mark.asyncio
    async def test_load_state_not_found(self, buyer_memory, mock_cache):
        """Test load returns None when no saved state exists."""
        contact_id = "buyer_123"
        mock_cache.get.return_value = None

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is None
        mock_cache.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_state_disabled(self, buyer_memory, mock_cache):
        """Test load returns None when disabled."""
        buyer_memory.enabled = False
        contact_id = "buyer_123"

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is None
        mock_cache.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_state_compression(self, buyer_memory, mock_cache):
        """Test state compression for large conversation histories."""
        contact_id = "buyer_123"

        # Create large conversation history (> 5KB threshold)
        large_state = {
            "conversation_history": [{"role": "user", "content": f"Message {i}" * 50} for i in range(100)],
            "financial_readiness_score": 85.0,
        }

        await buyer_memory.save_state(contact_id, large_state)

        # Verify compression was used
        call_args = mock_cache.set.call_args[0]
        storage_data = call_args[1]

        assert storage_data["compressed"] is True
        assert "data" in storage_data

        # Verify data can be decompressed
        compressed_bytes = bytes.fromhex(storage_data["data"])
        decompressed = gzip.decompress(compressed_bytes)
        json_data = decompressed.decode("utf-8")
        parsed = json.loads(json_data)

        assert len(parsed["conversation_history"]) > 0

    @pytest.mark.asyncio
    async def test_state_decompression(self, buyer_memory, mock_cache):
        """Test decompression of compressed state."""
        contact_id = "buyer_123"

        # Create compressed storage data
        state_data = {
            "conversation_history": [{"role": "user", "content": "Test"}],
            "financial_readiness_score": 85.0,
            "state_version": "1.0",
        }
        json_bytes = json.dumps(state_data).encode("utf-8")
        compressed_bytes = gzip.compress(json_bytes)

        storage_data = {
            "compressed": True,
            "data": compressed_bytes.hex(),
        }
        mock_cache.get.return_value = storage_data

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is not None
        assert loaded_state["financial_readiness_score"] == 85.0

    @pytest.mark.asyncio
    async def test_clear_state_success(self, buyer_memory, mock_cache):
        """Test successful state deletion."""
        contact_id = "buyer_123"

        success = await buyer_memory.clear_state(contact_id)

        assert success is True
        mock_cache.delete.assert_called_once_with(f"buyer_conversation_memory:{contact_id}")

    @pytest.mark.asyncio
    async def test_clear_state_empty_contact_id(self, buyer_memory, mock_cache):
        """Test clear fails with empty contact ID."""
        success = await buyer_memory.clear_state("")

        assert success is False
        mock_cache.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_conversation_history_trimming(self, buyer_memory, sample_state):
        """Test conversation history is trimmed to max_history_messages."""
        # Set max history to 10
        buyer_memory.max_history_messages = 10

        # Create state with 50 messages
        large_history = [{"role": "user", "content": f"Message {i}"} for i in range(50)]
        sample_state["conversation_history"] = large_history

        prepared_state = buyer_memory._prepare_state_for_storage(sample_state)

        assert len(prepared_state["conversation_history"]) == 10
        # Should keep most recent messages
        assert prepared_state["conversation_history"][-1]["content"] == "Message 49"

    @pytest.mark.asyncio
    async def test_ttl_override(self, buyer_memory, mock_cache, sample_state):
        """Test TTL can be overridden per save."""
        contact_id = "buyer_123"
        custom_ttl = 3600  # 1 hour

        await buyer_memory.save_state(contact_id, sample_state, ttl_override=custom_ttl)

        call_args = mock_cache.set.call_args
        actual_ttl = call_args[1]["ttl"]

        assert actual_ttl == custom_ttl

    @pytest.mark.asyncio
    async def test_state_version_tracking(self, buyer_memory, mock_cache, sample_state):
        """Test state version is added during save."""
        contact_id = "buyer_123"

        await buyer_memory.save_state(contact_id, sample_state)

        call_args = mock_cache.set.call_args[0]
        storage_data = call_args[1]

        # Extract saved data
        json_data = storage_data["data"]
        parsed = json.loads(json_data)

        assert parsed["state_version"] == "1.0"
        assert "last_interaction_timestamp" in parsed

    @pytest.mark.asyncio
    async def test_multi_session_continuity(self, buyer_memory, mock_cache, sample_state):
        """Test multi-session conversation continuity."""
        contact_id = "buyer_123"

        # Session 1: Initial conversation
        await buyer_memory.save_state(contact_id, sample_state)

        # Simulate loading in Session 2
        saved_data = mock_cache.set.call_args[0][1]
        mock_cache.get.return_value = saved_data

        loaded_state = await buyer_memory.load_state(contact_id)

        # Verify critical context is preserved
        assert loaded_state["budget_range"]["min"] == 350000
        assert loaded_state["buyer_persona"] == "Ready-Now Buyer"
        assert loaded_state["financing_status"] == "pre_approved"
        assert len(loaded_state["conversation_history"]) == 3

    @pytest.mark.asyncio
    async def test_get_stats(self, buyer_memory):
        """Test get_stats returns configuration."""
        stats = await buyer_memory.get_stats()

        assert stats["enabled"] is True
        assert stats["ttl_days"] == 30
        assert stats["ttl_seconds"] == 30 * 86400
        assert stats["compress_threshold_bytes"] == 5120
        assert stats["max_history_messages"] == 50
        assert stats["state_version"] == "1.0"

    def test_singleton_pattern(self):
        """Test get_buyer_conversation_memory returns singleton."""
        # Reset singleton
        reset_buyer_conversation_memory()

        instance1 = get_buyer_conversation_memory()
        instance2 = get_buyer_conversation_memory()

        assert instance1 is instance2

    @pytest.mark.asyncio
    async def test_save_state_cache_error(self, buyer_memory, mock_cache, sample_state):
        """Test save handles cache errors gracefully."""
        contact_id = "buyer_123"
        mock_cache.set.side_effect = Exception("Redis connection error")

        success = await buyer_memory.save_state(contact_id, sample_state)

        assert success is False

    @pytest.mark.asyncio
    async def test_load_state_cache_error(self, buyer_memory, mock_cache):
        """Test load handles cache errors gracefully."""
        contact_id = "buyer_123"
        mock_cache.get.side_effect = Exception("Redis connection error")

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is None

    @pytest.mark.asyncio
    async def test_load_state_invalid_json(self, buyer_memory, mock_cache):
        """Test load handles corrupted data gracefully."""
        contact_id = "buyer_123"

        storage_data = {
            "compressed": False,
            "data": "invalid json {{{",
        }
        mock_cache.get.return_value = storage_data

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is None

    @pytest.mark.asyncio
    async def test_prepare_state_preserves_essential_fields(self, buyer_memory, sample_state):
        """Test _prepare_state_for_storage preserves all essential fields."""
        prepared = buyer_memory._prepare_state_for_storage(sample_state)

        # Check all expected fields are present
        assert "conversation_history" in prepared
        assert "financial_readiness_score" in prepared
        assert "buying_motivation_score" in prepared
        assert "budget_range" in prepared
        assert "property_preferences" in prepared
        assert "urgency_level" in prepared
        assert "financing_status" in prepared
        assert "buyer_name" in prepared
        assert "buyer_phone" in prepared

    @pytest.mark.asyncio
    async def test_state_version_mismatch_warning(self, buyer_memory, mock_cache, caplog):
        """Test version mismatch logs warning but still returns state."""
        contact_id = "buyer_123"

        # Create state with old version
        old_state = {
            "financial_readiness_score": 85.0,
            "state_version": "0.5",
        }
        storage_data = {
            "compressed": False,
            "data": json.dumps(old_state),
        }
        mock_cache.get.return_value = storage_data

        loaded_state = await buyer_memory.load_state(contact_id)

        assert loaded_state is not None
        assert loaded_state["financial_readiness_score"] == 85.0
        # Version mismatch should be logged (check in caplog if needed)


class TestConversationMemoryIntegration:
    """Integration tests for conversation memory with real scenarios."""

    @pytest.mark.asyncio
    async def test_returning_buyer_scenario(self, buyer_memory, mock_cache):
        """Test realistic scenario: buyer returns after 3 days."""
        contact_id = "buyer_456"

        # Day 1: Initial conversation
        day1_state = {
            "conversation_history": [
                {"role": "user", "content": "I'm looking for a home"},
                {"role": "assistant", "content": "Great! What's your budget?"},
                {"role": "user", "content": "$500k"},
            ],
            "budget_range": {"min": 450000, "max": 550000},
            "financial_readiness_score": 70.0,
        }

        await buyer_memory.save_state(contact_id, day1_state)

        # Simulate state retrieval after 3 days
        saved_data = mock_cache.set.call_args[0][1]
        mock_cache.get.return_value = saved_data

        loaded_state = await buyer_memory.load_state(contact_id)

        # Verify buyer context is restored
        assert loaded_state["budget_range"]["min"] == 450000
        assert len(loaded_state["conversation_history"]) == 3

    @pytest.mark.asyncio
    async def test_conversation_memory_disabled_fallback(self, mock_cache, mock_config):
        """Test graceful handling when memory is disabled."""
        mock_config.buyer_bot.conversation_memory.enabled = False

        with patch(
            "ghl_real_estate_ai.services.jorge.buyer_conversation_memory.get_cache_service", return_value=mock_cache
        ):
            with patch(
                "ghl_real_estate_ai.services.jorge.buyer_conversation_memory.get_config", return_value=mock_config
            ):
                memory = BuyerConversationMemory()

                # Save should be skipped
                success = await memory.save_state("buyer_123", {"test": "data"})
                assert success is False

                # Load should return None
                state = await memory.load_state("buyer_123")
                assert state is None
