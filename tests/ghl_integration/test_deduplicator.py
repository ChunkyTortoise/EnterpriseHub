"""
Test Event Deduplicator
"""

import pytest
import json
import hashlib
from unittest.mock import Mock, AsyncMock

from ghl_integration.deduplicator import EventDeduplicator, FuzzyDeduplicator


class TestEventDeduplicator:
    """Test suite for event deduplication"""

    @pytest.fixture
    def deduplicator(self, mock_cache_service):
        dedup = EventDeduplicator()
        dedup.cache = mock_cache_service
        return dedup

    def test_generate_key_with_event_id(self, deduplicator):
        """Test key generation with explicit event ID"""
        key = deduplicator.generate_key("evt_123", "contact.create", {})
        assert key == "ghl:dedup:evt_123"

    def test_generate_key_with_contact_id(self, deduplicator):
        """Test key generation with contact ID in payload"""
        payload = {"data": {"id": "contact_456"}}
        key = deduplicator.generate_key(None, "contact.create", payload)
        assert "contact.create" in key
        assert "contact_456" in key

    def test_generate_key_with_timestamp(self, deduplicator):
        """Test key generation with timestamp rounding"""
        payload = {
            "data": {"id": "contact_789"},
            "timestamp": "2026-02-11T10:30:45Z"
        }
        key = deduplicator.generate_key(None, "contact.create", payload)
        # Should include minute-level timestamp
        assert "202602111030" in key

    def test_generate_key_fallback_to_hash(self, deduplicator):
        """Test key generation falls back to content hash"""
        payload = {"message": "Test content without IDs"}
        key = deduplicator.generate_key(None, "custom.event", payload)
        
        assert key.startswith("ghl:dedup:custom.event:")
        # Should be a hash (32 chars after prefix)
        hash_part = key.split(":")[-1]
        assert len(hash_part) == 32  # MD5 hash length

    @pytest.mark.asyncio
    async def test_is_duplicate_new_event(self, deduplicator, mock_cache_service):
        """Test that new events are not duplicates"""
        mock_cache_service.get.return_value = None
        
        is_dup = await deduplicator.is_duplicate("ghl:dedup:evt_123")
        
        assert is_dup is False
        mock_cache_service.get.assert_called_with("ghl:dedup:evt_123")

    @pytest.mark.asyncio
    async def test_is_duplicate_existing_event(self, deduplicator, mock_cache_service):
        """Test that existing events are detected as duplicates"""
        mock_cache_service.get.return_value = "1"
        
        is_dup = await deduplicator.is_duplicate("ghl:dedup:evt_123")
        
        assert is_dup is True

    @pytest.mark.asyncio
    async def test_is_duplicate_cache_error(self, deduplicator, mock_cache_service):
        """Test that cache errors allow events through (fail open)"""
        mock_cache_service.get.side_effect = Exception("Redis error")
        
        is_dup = await deduplicator.is_duplicate("ghl:dedup:evt_123")
        
        assert is_dup is False  # Should allow through on error

    @pytest.mark.asyncio
    async def test_mark_processed_simple(self, deduplicator, mock_cache_service):
        """Test marking event as processed without metadata"""
        await deduplicator.mark_processed("ghl:dedup:evt_123")
        
        mock_cache_service.set.assert_called_with(
            "ghl:dedup:evt_123",
            "1",
            ttl=86400
        )

    @pytest.mark.asyncio
    async def test_mark_processed_with_metadata(self, deduplicator, mock_cache_service):
        """Test marking event with metadata"""
        metadata = {"processed_at": "2026-02-11T10:00:00Z", "handler": "lead_bot"}
        await deduplicator.mark_processed("ghl:dedup:evt_123", metadata)
        
        call_args = mock_cache_service.set.call_args
        assert call_args[0][0] == "ghl:dedup:evt_123"
        assert "processed_at" in call_args[0][1]
        assert call_args[1]["ttl"] == 86400

    @pytest.mark.asyncio
    async def test_get_metadata_exists(self, deduplicator, mock_cache_service):
        """Test getting metadata for processed event"""
        metadata = {"processed_at": "2026-02-11T10:00:00Z"}
        mock_cache_service.get.return_value = json.dumps(metadata)
        
        result = await deduplicator.get_metadata("ghl:dedup:evt_123")
        
        assert result == metadata

    @pytest.mark.asyncio
    async def test_get_metadata_simple_value(self, deduplicator, mock_cache_service):
        """Test getting metadata when only simple value exists"""
        mock_cache_service.get.return_value = "1"
        
        result = await deduplicator.get_metadata("ghl:dedup:evt_123")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_metadata_not_found(self, deduplicator, mock_cache_service):
        """Test getting metadata for non-existent event"""
        mock_cache_service.get.return_value = None
        
        result = await deduplicator.get_metadata("ghl:dedup:evt_123")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_clear_entry(self, deduplicator, mock_cache_service):
        """Test clearing deduplication entry"""
        await deduplicator.clear_entry("ghl:dedup:evt_123")
        
        mock_cache_service.delete.assert_called_with("ghl:dedup:evt_123")


class TestFuzzyDeduplicator:
    """Test suite for fuzzy deduplication"""

    @pytest.fixture
    def fuzzy_dedup(self):
        return FuzzyDeduplicator(similarity_threshold=0.95)

    def test_normalize_payload(self, fuzzy_dedup):
        """Test payload normalization"""
        payload = {
            "data": {
                "id": "contact_123",
                "email": "test@example.com",
                "message": "  Hello   World  ",
                "extra_field": "ignored"
            }
        }
        
        normalized = fuzzy_dedup._normalize_payload(payload)
        
        assert normalized["id"] == "contact_123"
        assert normalized["email"] == "test@example.com"
        assert normalized["message"] == "hello world"
        assert "extra_field" not in normalized

    def test_normalize_payload_text_lowercasing(self, fuzzy_dedup):
        """Test that text fields are lowercased"""
        payload = {
            "data": {
                "id": "contact_123",
                "message": "UPPERCASE MESSAGE"
            }
        }
        
        normalized = fuzzy_dedup._normalize_payload(payload)
        
        assert normalized["message"] == "uppercase message"

    def test_generate_content_hash_consistency(self, fuzzy_dedup):
        """Test that content hash is consistent for same payload"""
        payload = {"data": {"id": "123", "message": "Test"}}
        
        hash1 = fuzzy_dedup.generate_content_hash(payload)
        hash2 = fuzzy_dedup.generate_content_hash(payload)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length

    def test_generate_content_hash_different_payloads(self, fuzzy_dedup):
        """Test that different payloads produce different hashes"""
        payload1 = {"data": {"id": "123", "message": "Test A"}}
        payload2 = {"data": {"id": "123", "message": "Test B"}}
        
        hash1 = fuzzy_dedup.generate_content_hash(payload1)
        hash2 = fuzzy_dedup.generate_content_hash(payload2)
        
        assert hash1 != hash2

    def test_similar_payloads_same_hash(self, fuzzy_dedup):
        """Test that similar payloads may produce same hash after normalization"""
        # These should normalize to similar content
        payload1 = {"data": {"id": "123", "message": "  Hello   World  "}}
        payload2 = {"data": {"id": "123", "message": "hello world"}}
        
        normalized1 = fuzzy_dedup._normalize_payload(payload1)
        normalized2 = fuzzy_dedup._normalize_payload(payload2)
        
        # After normalization, they should be the same
        assert normalized1["message"] == normalized2["message"]
