"""Tests for tenant routing via API keys."""

import hashlib
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from rag_service.multi_tenant.tenant_router import TenantRouter


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def mock_db_factory():
    """Mock database session factory."""
    factory = MagicMock()
    return factory


@pytest.fixture
def tenant_router(mock_redis, mock_db_factory):
    """Tenant router with mocks."""
    return TenantRouter(redis=mock_redis, db_session_factory=mock_db_factory)


class TestTenantRouter:
    """Test tenant resolution from API keys."""

    async def test_resolve_tenant_from_cache(self, tenant_router, mock_redis):
        """Test resolving tenant from Redis cache."""
        # Arrange
        api_key = "test_key_12345"
        cached_data = {
            "tenant_id": "tenant-123",
            "schema_name": "tenant_acme",
            "tier": "pro",
            "scopes": ["read", "write"],
        }
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_data))

        # Act
        result = await tenant_router.resolve_tenant(api_key)

        # Assert
        assert result == cached_data
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        mock_redis.get.assert_called_once_with(f"tenant_route:{hashed}")

    async def test_resolve_tenant_from_database(
        self, tenant_router, mock_redis, mock_db_factory
    ):
        """Test resolving tenant from database when not in cache."""
        # Arrange
        api_key = "test_key_12345"
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant-123"
        mock_row.slug = "acme-corp"
        mock_row.tier = "business"
        mock_row.scopes = ["read", "write", "admin"]
        mock_row.status = "active"
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        result = await tenant_router.resolve_tenant(api_key)

        # Assert
        assert result["tenant_id"] == "tenant-123"
        assert result["schema_name"] == "tenant_acme-corp"
        assert result["tier"] == "business"
        assert result["scopes"] == ["read", "write", "admin"]

    async def test_resolve_tenant_caches_result(
        self, tenant_router, mock_redis, mock_db_factory
    ):
        """Test that database result is cached in Redis."""
        # Arrange
        api_key = "test_key_12345"
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant-123"
        mock_row.slug = "acme"
        mock_row.tier = "starter"
        mock_row.scopes = ["read"]
        mock_row.status = "active"
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        await tenant_router.resolve_tenant(api_key)

        # Assert
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == f"tenant_route:{hashed}"
        assert call_args[0][1] == 300  # 5 minute TTL

    async def test_resolve_tenant_invalid_key(
        self, tenant_router, mock_redis, mock_db_factory
    ):
        """Test resolving invalid API key returns None."""
        # Arrange
        api_key = "invalid_key"
        mock_redis.get = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=None)  # No matching key
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        result = await tenant_router.resolve_tenant(api_key)

        # Assert
        assert result is None

    async def test_resolve_tenant_suspended_account(
        self, tenant_router, mock_redis, mock_db_factory
    ):
        """Test that suspended tenants return None."""
        # Arrange
        api_key = "test_key_12345"
        mock_redis.get = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant-123"
        mock_row.slug = "suspended-tenant"
        mock_row.tier = "pro"
        mock_row.scopes = ["read"]
        mock_row.status = "suspended"  # Suspended account
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        result = await tenant_router.resolve_tenant(api_key)

        # Assert
        assert result is None

    async def test_invalidate_cache(self, tenant_router, mock_redis):
        """Test cache invalidation for an API key."""
        # Arrange
        api_key = "test_key_12345"
        hashed = hashlib.sha256(api_key.encode()).hexdigest()

        # Act
        await tenant_router.invalidate_cache(api_key)

        # Assert
        mock_redis.delete.assert_called_once_with(f"tenant_route:{hashed}")

    async def test_resolve_without_redis(self, mock_db_factory):
        """Test tenant resolution works without Redis."""
        # Arrange
        router = TenantRouter(redis=None, db_session_factory=mock_db_factory)
        api_key = "test_key"

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant-123"
        mock_row.slug = "acme"
        mock_row.tier = "starter"
        mock_row.scopes = ["read"]
        mock_row.status = "active"
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        result = await router.resolve_tenant(api_key)

        # Assert
        assert result["tenant_id"] == "tenant-123"
        # Should not attempt to cache
        assert not hasattr(router.redis, "setex")

    async def test_resolve_without_database(self, mock_redis):
        """Test tenant resolution returns None without database."""
        # Arrange
        router = TenantRouter(redis=mock_redis, db_session_factory=None)
        mock_redis.get = AsyncMock(return_value=None)

        # Act
        result = await router.resolve_tenant("test_key")

        # Assert
        assert result is None

    async def test_api_key_hashing_consistency(self):
        """Test that API key hashing is consistent."""
        # Arrange
        api_key = "test_key_12345"
        expected_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Act
        router = TenantRouter()
        actual_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Assert
        assert actual_hash == expected_hash


class TestTenantRouterIntegration:
    """Integration-style tests for tenant routing."""

    async def test_full_resolution_flow(self, tenant_router, mock_redis, mock_db_factory):
        """Test complete flow: cache miss -> DB query -> cache set."""
        # Arrange
        api_key = "full_test_key"
        mock_redis.get = AsyncMock(return_value=None)  # Cache miss

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.tenant_id = "tenant-789"
        mock_row.slug = "integration-test"
        mock_row.tier = "enterprise"
        mock_row.scopes = ["read", "write", "delete"]
        mock_row.status = "active"
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_db_factory.return_value = mock_session
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        # Act
        result1 = await tenant_router.resolve_tenant(api_key)

        # Now set up cache hit for second call
        mock_redis.get = AsyncMock(
            return_value=json.dumps(
                {
                    "tenant_id": "tenant-789",
                    "schema_name": "tenant_integration-test",
                    "tier": "enterprise",
                    "scopes": ["read", "write", "delete"],
                }
            )
        )

        result2 = await tenant_router.resolve_tenant(api_key)

        # Assert
        assert result1["tenant_id"] == "tenant-789"
        assert result2["tenant_id"] == "tenant-789"
        # First call should hit DB, second should use cache
        assert mock_session.execute.call_count == 1
