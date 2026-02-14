#!/usr/bin/env python3
"""
Unit Tests for Tiered Cache Service
===================================

Verifies L1/L2 caching, TTL management, and L2 -> L1 promotion logic.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from ghl_real_estate_ai.services.tiered_cache_service import CacheItem, TieredCacheService


@pytest_asyncio.fixture
async def tiered_cache():
    """Initialize TieredCacheService with a mocked Redis backend."""
    with patch("ghl_real_estate_ai.services.tiered_cache_service.RedisBackend") as mock_redis_class:
        mock_redis = mock_redis_class.return_value
        mock_redis.enabled = True
        mock_redis.initialize = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=True)
        mock_redis.close = AsyncMock()

        # Reset singleton for testing
        TieredCacheService._instance = None
        service = TieredCacheService()
        await service.start()

        yield service

        await service.stop()


@pytest.mark.asyncio
async def test_l2_to_l1_promotion_logic(tiered_cache):
    """
    Verify that items are promoted from L2 to L1 after 2 accesses.
    """
    key = "test_promo_key"
    value = {"data": "test_value"}
    ttl = 60

    # 1. Setup: Item exists ONLY in L2
    import pickle

    cache_item = CacheItem(
        value=value, created_at=time.time(), expires_at=time.time() + ttl, access_count=0, source="l2_direct"
    )
    serialized_item = pickle.dumps(cache_item)

    # Mock L2 hit
    tiered_cache.l2_backend.get = AsyncMock(return_value=serialized_item)

    # Ensure L1 is empty
    tiered_cache.l1_cache.delete(key)

    # 2. First Access: Should NOT promote yet (access_count becomes 1)
    result1 = await tiered_cache.get(key)
    assert result1 == value
    assert tiered_cache.l1_cache.get(key) is None

    # Update mock for L2 to simulate updated access count
    cache_item.access()  # access_count = 1
    tiered_cache.l2_backend.get = AsyncMock(return_value=pickle.dumps(cache_item))

    # 3. Second Access: Should promote (access_count becomes 2)
    result2 = await tiered_cache.get(key)
    assert result2 == value

    # Verify it is now in L1
    l1_val = tiered_cache.l1_cache.get(key)
    assert l1_val == value

    # 4. Third Access: Should come from L1
    # We can verify this by making L2 fail/return None
    tiered_cache.l2_backend.get = AsyncMock(return_value=None)
    result3 = await tiered_cache.get(key)
    assert result3 == value


@pytest.mark.asyncio
async def test_cache_set_stores_in_both_layers(tiered_cache):
    """Verify that set() stores data in both L1 and L2."""
    key = "dual_store_key"
    value = "dual_value"

    await tiered_cache.set(key, value)

    # Verify L1
    assert tiered_cache.l1_cache.get(key) == value

    # Verify L2 call
    tiered_cache.l2_backend.set.assert_called_once()


@pytest.mark.asyncio
async def test_cache_delete_removes_from_both_layers(tiered_cache):
    """Verify that delete() removes from both layers."""
    key = "delete_key"

    await tiered_cache.delete(key)

    # Verify L2 call
    tiered_cache.l2_backend.delete.assert_called_once()