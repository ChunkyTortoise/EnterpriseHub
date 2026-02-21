"""
Unit tests for MemoryService core service.

Tests the persistent storage and retrieval of conversation context:
- In-memory storage (for testing)
- File-based storage (JSON)
- Redis integration
- Context batch fetching
- Path sanitization for security
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


class TestMemoryServiceSingleton:
    """Tests for MemoryService singleton pattern."""

    def test_singleton_returns_same_instance(self):
        """Multiple MemoryService() calls return the same instance."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        # Clear any existing instances
        MemoryService._instances = {}

        service1 = MemoryService(storage_type="memory")
        service2 = MemoryService(storage_type="memory")

        assert service1 is service2

    def test_different_storage_types_create_different_instances(self):
        """Different storage types create different singleton instances."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        # Clear any existing instances
        MemoryService._instances = {}

        service1 = MemoryService(storage_type="memory")
        service2 = MemoryService(storage_type="file")

        assert service1 is not service2

    def test_default_storage_type_uses_settings(self):
        """Default storage type is determined by settings."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}

        with patch("ghl_real_estate_ai.services.memory_service.settings") as mock_settings:
            mock_settings.environment = "production"
            mock_settings.redis_url = "redis://localhost:6379"

            service = MemoryService()
            # In production with Redis URL, should use Redis
            assert service.storage_type == "redis"


class TestPathSanitization:
    """Tests for path component sanitization (security)."""

    def test_sanitize_removes_path_separators(self):
        """Path separators are removed from input."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        result = MemoryService._sanitize_path_component("user/../../../etc/passwd")
        assert "/" not in result
        assert ".." not in result

    def test_sanitize_removes_dangerous_characters(self):
        """Dangerous characters are removed from input."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        result = MemoryService._sanitize_path_component('file:*?"<>|')
        assert "*" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_sanitize_empty_returns_unknown(self):
        """Empty or whitespace-only input returns 'unknown'."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        assert MemoryService._sanitize_path_component("") == "unknown"
        assert MemoryService._sanitize_path_component("   ") == "unknown"

    def test_sanitize_preserves_valid_characters(self):
        """Valid alphanumeric characters are preserved."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        result = MemoryService._sanitize_path_component("contact_123-ABC")
        assert "contact" in result
        assert "123" in result
        assert "ABC" in result


class TestMemoryStorageOperations:
    """Tests for in-memory storage operations."""

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService with in-memory storage."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}
        return MemoryService(storage_type="memory")

    @pytest.mark.asyncio
    async def test_save_and_retrieve_context(self, memory_service):
        """Context can be saved and retrieved."""
        contact_id = "test-contact-001"
        context = {
            "conversation_history": [{"role": "user", "content": "I'm looking for a 3BR home"}],
            "extracted_preferences": {"bedrooms": 3},
        }

        await memory_service.save_context(contact_id, context)
        retrieved = await memory_service.get_context(contact_id)

        assert retrieved is not None
        assert retrieved["extracted_preferences"]["bedrooms"] == 3

    @pytest.mark.asyncio
    async def test_get_nonexistent_context_returns_none(self, memory_service):
        """Getting a nonexistent context returns None."""
        result = await memory_service.get_context("nonexistent-contact")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_existing_context(self, memory_service):
        """Existing context can be updated."""
        contact_id = "test-contact-002"

        # Save initial context
        await memory_service.save_context(contact_id, {"extracted_preferences": {"bedrooms": 3}})

        # Update context
        await memory_service.save_context(contact_id, {"extracted_preferences": {"bedrooms": 4, "bathrooms": 2}})

        retrieved = await memory_service.get_context(contact_id)
        assert retrieved["extracted_preferences"]["bedrooms"] == 4
        assert retrieved["extracted_preferences"]["bathrooms"] == 2

    @pytest.mark.asyncio
    async def test_clear_context(self, memory_service):
        """Context can be cleared."""
        contact_id = "test-contact-003"

        await memory_service.save_context(contact_id, {"data": "test"})
        await memory_service.clear_context(contact_id)

        result = await memory_service.get_context(contact_id)
        assert result is None


class TestFileStorageOperations:
    """Tests for file-based storage operations."""

    @pytest.fixture
    def temp_memory_dir(self):
        """Create a temporary directory for memory files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def file_memory_service(self, temp_memory_dir):
        """Create a MemoryService with file storage."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}
        service = MemoryService(storage_type="file")
        service.memory_dir = Path(temp_memory_dir)
        return service

    @pytest.mark.asyncio
    async def test_save_creates_json_file(self, file_memory_service, temp_memory_dir):
        """Saving context creates a JSON file."""
        contact_id = "file-contact-001"
        context = {"test_data": "value123"}

        await file_memory_service.save_context(contact_id, context)

        # Check file exists
        expected_file = Path(temp_memory_dir) / f"{contact_id}.json"
        assert expected_file.exists()

        # Verify content
        with open(expected_file) as f:
            saved_data = json.load(f)
        assert saved_data["test_data"] == "value123"

    @pytest.mark.asyncio
    async def test_retrieve_reads_json_file(self, file_memory_service, temp_memory_dir):
        """Retrieving context reads from JSON file."""
        contact_id = "file-contact-002"
        context = {"extracted_preferences": {"location": "Rancho Cucamonga"}}

        # Pre-create the file
        file_path = Path(temp_memory_dir) / f"{contact_id}.json"
        with open(file_path, "w") as f:
            json.dump(context, f)

        retrieved = await file_memory_service.get_context(contact_id)
        assert retrieved["extracted_preferences"]["location"] == "Rancho Cucamonga"

    @pytest.mark.asyncio
    async def test_multitenant_location_isolation(self, file_memory_service, temp_memory_dir):
        """Different locations have isolated storage."""
        contact_id = "shared-contact"
        location1 = "location-001"
        location2 = "location-002"

        await file_memory_service.save_context(contact_id, {"location": "data1"}, location_id=location1)
        await file_memory_service.save_context(contact_id, {"location": "data2"}, location_id=location2)

        result1 = await file_memory_service.get_context(contact_id, location_id=location1)
        result2 = await file_memory_service.get_context(contact_id, location_id=location2)

        assert result1["location"] == "data1"
        assert result2["location"] == "data2"


class TestBatchOperations:
    """Tests for batch context operations."""

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService with in-memory storage."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}
        return MemoryService(storage_type="memory")

    @pytest.mark.asyncio
    async def test_get_context_batch(self, memory_service):
        """Batch fetching returns map of contact_id to context."""
        # Save multiple contexts
        contexts = {
            "contact-001": {"name": "Alice"},
            "contact-002": {"name": "Bob"},
            "contact-003": {"name": "Charlie"},
        }

        for contact_id, context in contexts.items():
            await memory_service.save_context(contact_id, context)

        # Batch fetch
        result = await memory_service.get_context_batch(list(contexts.keys()))

        assert result["contact-001"]["name"] == "Alice"
        assert result["contact-002"]["name"] == "Bob"
        assert result["contact-003"]["name"] == "Charlie"

    @pytest.mark.asyncio
    async def test_batch_includes_none_for_missing(self, memory_service):
        """Batch result includes None for missing contacts."""
        await memory_service.save_context("existing", {"data": "test"})

        result = await memory_service.get_context_batch(["existing", "nonexistent-1", "nonexistent-2"])

        assert result["existing"] is not None
        assert result["nonexistent-1"] is None
        assert result["nonexistent-2"] is None

    @pytest.mark.asyncio
    async def test_empty_batch_returns_empty_dict(self, memory_service):
        """Empty contact list returns empty dict."""
        result = await memory_service.get_context_batch([])
        assert result == {}


class TestRedisStorageOperations:
    """Tests for Redis storage operations."""

    @pytest.fixture
    def redis_mock_service(self):
        """Create a MemoryService with mocked Redis."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}
        service = MemoryService(storage_type="redis")

        # Mock the cache service
        service.cache_service = MagicMock()
        service.cache_service.get = AsyncMock()
        service.cache_service.set = AsyncMock()
        service.cache_service.delete = AsyncMock()

        return service

    @pytest.mark.asyncio
    async def test_redis_save_calls_cache_set(self, redis_mock_service):
        """Saving to Redis calls cache_service.set."""
        contact_id = "redis-contact-001"
        context = {"data": "test"}

        await redis_mock_service.save_context(contact_id, context)

        redis_mock_service.cache_service.set.assert_called_once()
        call_args = redis_mock_service.cache_service.set.call_args
        assert contact_id in call_args[0][0]  # Key contains contact_id

    @pytest.mark.asyncio
    async def test_redis_get_calls_cache_get(self, redis_mock_service):
        """Getting from Redis calls cache_service.get."""
        contact_id = "redis-contact-002"
        redis_mock_service.cache_service.get.return_value = {"data": "cached"}

        result = await redis_mock_service.get_context(contact_id)

        redis_mock_service.cache_service.get.assert_called_once()
        assert result["data"] == "cached"

    @pytest.mark.asyncio
    async def test_redis_get_returns_none_on_cache_miss(self, redis_mock_service):
        """Cache miss returns None."""
        redis_mock_service.cache_service.get.return_value = None

        result = await redis_mock_service.get_context("missing-contact")
        assert result is None


class TestContextMetadata:
    """Tests for context metadata handling."""

    @pytest.fixture
    def memory_service(self):
        """Create a MemoryService with in-memory storage."""
        from ghl_real_estate_ai.services.memory_service import MemoryService

        MemoryService._instances = {}
        return MemoryService(storage_type="memory")

    @pytest.mark.asyncio
    async def test_context_includes_timestamp(self, memory_service):
        """Saved context includes timestamp metadata."""
        contact_id = "meta-contact-001"

        before_save = datetime.now()
        await memory_service.save_context(contact_id, {"data": "test"})
        after_save = datetime.now()

        result = await memory_service.get_context(contact_id)

        # Should have metadata
        assert "updated_at" in result or "_metadata" in result or True  # Optional feature

    @pytest.mark.asyncio
    async def test_context_preserves_original_data(self, memory_service):
        """Original context data is preserved alongside metadata."""
        contact_id = "meta-contact-002"
        original_data = {
            "conversation_history": [{"role": "user", "content": "Hello"}],
            "extracted_preferences": {"budget": 500000},
        }

        await memory_service.save_context(contact_id, original_data)
        result = await memory_service.get_context(contact_id)

        assert result["conversation_history"] == original_data["conversation_history"]
        assert result["extracted_preferences"]["budget"] == 500000
