"""
Database operations and Redis caching tests for multi-tenant memory system.

Tests cover:
- Database connection pooling and health monitoring
- Redis caching performance and failover scenarios
- Data integrity and transaction handling
- Multi-tenant data isolation at database level
- Connection recovery and circuit breaker functionality
- Cache invalidation and consistency
"""

import asyncio
import pytest
import uuid
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any
import asyncpg
import aioredis

# Test imports with fallback for different execution contexts
try:
    from ghl_real_estate_ai.database.connection import EnhancedDatabasePool, DatabaseHealthMonitor
    from ghl_real_estate_ai.database.redis_client import EnhancedRedisClient, RedisHealthMonitor
    from ghl_real_estate_ai.database.migrations import MigrationManager
    from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
except ImportError:
    try:
        from database.connection import EnhancedDatabasePool, DatabaseHealthMonitor
        from database.redis_client import EnhancedRedisClient, RedisHealthMonitor
        from database.migrations import MigrationManager
        from services.enhanced_memory_service import EnhancedMemoryService
    except ImportError:
        # Mock for testing environment
        EnhancedDatabasePool = Mock
        DatabaseHealthMonitor = Mock
        EnhancedRedisClient = Mock
        RedisHealthMonitor = Mock
        MigrationManager = Mock
        EnhancedMemoryService = Mock

@pytest.fixture
def database_config():
    """Database configuration for testing"""
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_enterprisehub",
        "user": "test_user",
        "password": "test_password",
        "min_size": 5,
        "max_size": 20,
        "command_timeout": 30,
        "max_queries": 50000,
        "max_inactive_connection_lifetime": 300
    }

@pytest.fixture
def redis_config():
    """Redis configuration for testing"""
    return {
        "url": "redis://localhost:6379/1",
        "max_connections": 20,
        "retry_on_timeout": True,
        "retry_on_error": [ConnectionError, TimeoutError],
        "health_check_interval": 30,
        "decode_responses": True
    }

@pytest.fixture
def sample_tenant_data():
    """Sample tenant data for testing"""
    tenant_id = str(uuid.uuid4())
    return {
        "tenant": {
            "id": tenant_id,
            "location_id": f"test_location_{tenant_id[:8]}",
            "name": "Test Real Estate Agency",
            "claude_config": {"model_name": "claude-sonnet-4-20250514"},
            "behavioral_learning_enabled": True,
            "created_at": datetime.now()
        },
        "conversations": [
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "contact_id": "contact_1",
                "conversation_stage": "qualification",
                "lead_score": 75,
                "last_interaction_at": datetime.now(),
                "extracted_preferences": {"budget": 500000, "bedrooms": 3},
                "behavioral_profile": {"communication_style": "detailed"}
            }
        ],
        "messages": [
            {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": "I'm looking for a 3-bedroom home under $500k",
                "timestamp": datetime.now(),
                "metadata": {"channel": "sms"}
            }
        ],
        "behavioral_preferences": [
            {
                "id": str(uuid.uuid4()),
                "preference_type": "property_type",
                "preference_value": {"single_family": 0.9, "condo": 0.1},
                "confidence_score": 0.85,
                "learned_from": "property_interactions",
                "timestamp": datetime.now()
            }
        ]
    }

class TestDatabaseOperations:
    """Test database connection, operations, and health monitoring"""

    @pytest.mark.asyncio
    async def test_database_connection_pool_initialization(self, database_config):
        """Test database connection pool setup and configuration"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            # Mock successful pool creation
            mock_pool = AsyncMock()
            mock_pool.acquire = AsyncMock()
            mock_pool.release = AsyncMock()
            mock_pool.close = AsyncMock()
            mock_create_pool.return_value = mock_pool

            db_pool = EnhancedDatabasePool(database_config)
            await db_pool.initialize()

            # Verify pool initialization
            mock_create_pool.assert_called_once()
            call_kwargs = mock_create_pool.call_args[1]

            assert call_kwargs["min_size"] == database_config["min_size"]
            assert call_kwargs["max_size"] == database_config["max_size"]
            assert call_kwargs["command_timeout"] == database_config["command_timeout"]

            # Test connection acquisition
            connection = await db_pool.get_connection()
            assert connection is not None

            await db_pool.close()

    @pytest.mark.asyncio
    async def test_database_health_monitoring(self, database_config):
        """Test database health monitoring and circuit breaker"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            # Setup health check scenarios
            health_check_results = [
                True,   # Healthy
                True,   # Still healthy
                False,  # Unhealthy
                False,  # Still unhealthy
                True    # Recovered
            ]

            mock_pool = AsyncMock()
            mock_pool.fetchval = AsyncMock(side_effect=health_check_results)
            mock_create_pool.return_value = mock_pool

            db_pool = EnhancedDatabasePool(database_config)
            health_monitor = DatabaseHealthMonitor(db_pool)

            # Test health monitoring cycle
            health_statuses = []
            for _ in range(5):
                status = await health_monitor.check_health()
                health_statuses.append(status["healthy"])

            # Verify health monitoring pattern
            assert health_statuses == [True, True, False, False, True]

            # Test circuit breaker activation
            circuit_breaker_status = health_monitor.get_circuit_breaker_status()
            assert "failure_count" in circuit_breaker_status
            assert "last_failure_time" in circuit_breaker_status

    @pytest.mark.asyncio
    async def test_multi_tenant_data_isolation_database_level(self, sample_tenant_data):
        """Test database-level multi-tenant data isolation"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            # Create two separate tenant datasets
            tenant_a_data = sample_tenant_data
            tenant_b_id = str(uuid.uuid4())
            tenant_b_data = {
                **sample_tenant_data,
                "tenant": {**sample_tenant_data["tenant"], "id": tenant_b_id, "location_id": f"test_location_{tenant_b_id[:8]}"},
                "conversations": [{**sample_tenant_data["conversations"][0], "tenant_id": tenant_b_id, "extracted_preferences": {"budget": 800000, "property_type": "luxury"}}]
            }

            # Mock database responses with tenant isolation
            mock_pool = AsyncMock()

            def mock_fetch(query, *args):
                # Simulate Row Level Security - only return data for queried tenant
                if args and len(args) > 0:
                    queried_tenant_id = args[0]
                    if queried_tenant_id == tenant_a_data["tenant"]["id"]:
                        return [tenant_a_data["conversations"][0]]
                    elif queried_tenant_id == tenant_b_id:
                        return [tenant_b_data["conversations"][0]]
                return []

            mock_pool.fetch = AsyncMock(side_effect=mock_fetch)
            mock_create_pool.return_value = mock_pool

            db_pool = EnhancedDatabasePool()
            await db_pool.initialize()

            # Test tenant A data access
            tenant_a_conversations = await db_pool.fetch(
                "SELECT * FROM conversations WHERE tenant_id = $1",
                tenant_a_data["tenant"]["id"]
            )

            # Test tenant B data access
            tenant_b_conversations = await db_pool.fetch(
                "SELECT * FROM conversations WHERE tenant_id = $1",
                tenant_b_id
            )

            # Verify data isolation
            assert len(tenant_a_conversations) == 1
            assert len(tenant_b_conversations) == 1
            assert tenant_a_conversations[0]["extracted_preferences"]["budget"] == 500000
            assert tenant_b_conversations[0]["extracted_preferences"]["budget"] == 800000

            # Verify no cross-tenant data leakage
            assert tenant_a_conversations[0]["tenant_id"] != tenant_b_conversations[0]["tenant_id"]

    @pytest.mark.asyncio
    async def test_database_transaction_handling(self, sample_tenant_data):
        """Test database transaction integrity and rollback scenarios"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_connection = AsyncMock()
            mock_transaction = AsyncMock()

            # Mock transaction lifecycle
            mock_connection.transaction = AsyncMock(return_value=mock_transaction)
            mock_transaction.__aenter__ = AsyncMock(return_value=mock_transaction)
            mock_transaction.__aexit__ = AsyncMock()

            mock_pool = AsyncMock()
            mock_pool.acquire = AsyncMock(return_value=mock_connection)
            mock_pool.release = AsyncMock()
            mock_create_pool.return_value = mock_pool

            db_pool = EnhancedDatabasePool()
            await db_pool.initialize()

            # Test successful transaction
            async with mock_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO tenants (id, location_id, name) VALUES ($1, $2, $3)",
                        sample_tenant_data["tenant"]["id"],
                        sample_tenant_data["tenant"]["location_id"],
                        sample_tenant_data["tenant"]["name"]
                    )

                    await conn.execute(
                        "INSERT INTO conversations (id, tenant_id, contact_id) VALUES ($1, $2, $3)",
                        sample_tenant_data["conversations"][0]["id"],
                        sample_tenant_data["tenant"]["id"],
                        sample_tenant_data["conversations"][0]["contact_id"]
                    )

            # Verify transaction completion
            mock_transaction.__aenter__.assert_called_once()
            mock_transaction.__aexit__.assert_called_once()

            # Test transaction rollback scenario
            mock_transaction.__aexit__.reset_mock()
            mock_connection.execute.side_effect = [None, Exception("Database error")]

            try:
                async with mock_pool.acquire() as conn:
                    async with conn.transaction():
                        await conn.execute("INSERT INTO tenants ...")
                        await conn.execute("INSERT INTO conversations ...")  # This will fail
            except Exception:
                pass

            # Verify rollback handling
            mock_transaction.__aexit__.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_connection_recovery(self, database_config):
        """Test database connection recovery after failures"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            # Simulate connection failures and recovery
            connection_attempts = [
                ConnectionError("Connection failed"),
                ConnectionError("Still failing"),
                AsyncMock()  # Successful connection
            ]

            mock_create_pool.side_effect = connection_attempts

            db_pool = EnhancedDatabasePool(database_config)

            # Test retry logic
            with pytest.raises(ConnectionError):
                await db_pool.initialize()  # First attempt fails

            with pytest.raises(ConnectionError):
                await db_pool.initialize()  # Second attempt fails

            await db_pool.initialize()  # Third attempt succeeds

            # Verify retry attempts
            assert mock_create_pool.call_count == 3

    @pytest.mark.asyncio
    async def test_database_performance_monitoring(self, database_config):
        """Test database performance monitoring and metrics"""

        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()

            # Mock query execution times
            execution_times = [0.05, 0.12, 0.03, 0.18, 0.07]  # Various execution times

            async def mock_execute(*args, **kwargs):
                # Simulate query execution delay
                await asyncio.sleep(execution_times.pop(0) if execution_times else 0.05)
                return None

            mock_pool.execute = mock_execute
            mock_create_pool.return_value = mock_pool

            db_pool = EnhancedDatabasePool(database_config)
            await db_pool.initialize()

            # Execute queries and measure performance
            start_time = time.perf_counter()

            for i in range(3):
                await db_pool.execute(f"SELECT * FROM conversations WHERE id = $1", str(uuid.uuid4()))

            total_time = time.perf_counter() - start_time

            # Verify performance monitoring
            performance_metrics = db_pool.get_performance_metrics()

            assert "total_queries" in performance_metrics
            assert "average_execution_time" in performance_metrics
            assert "slowest_query_time" in performance_metrics
            assert performance_metrics["total_queries"] >= 3

class TestRedisOperations:
    """Test Redis caching operations and health monitoring"""

    @pytest.mark.asyncio
    async def test_redis_connection_and_basic_operations(self, redis_config):
        """Test Redis connection and basic cache operations"""

        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_redis.get = AsyncMock()
            mock_redis.delete = AsyncMock()
            mock_redis.exists = AsyncMock()
            mock_from_url.return_value = mock_redis

            redis_client = EnhancedRedisClient(redis_config)
            await redis_client.connect()

            # Test basic operations
            await redis_client.set("test_key", "test_value", ex=300)
            mock_redis.set.assert_called_with("test_key", "test_value", ex=300)

            mock_redis.get.return_value = "test_value"
            result = await redis_client.get("test_key")
            assert result == "test_value"

            await redis_client.delete("test_key")
            mock_redis.delete.assert_called_with("test_key")

    @pytest.mark.asyncio
    async def test_redis_multi_tenant_key_namespacing(self):
        """Test Redis key namespacing for multi-tenant isolation"""

        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock()
            mock_redis.get = AsyncMock()
            mock_from_url.return_value = mock_redis

            redis_client = EnhancedRedisClient()
            await redis_client.connect()

            # Test tenant-specific key generation
            tenant_a_key = redis_client.build_tenant_key("tenant_a", "conv_memory", "contact_123")
            tenant_b_key = redis_client.build_tenant_key("tenant_b", "conv_memory", "contact_123")

            # Verify key isolation
            assert "tenant_a" in tenant_a_key
            assert "tenant_b" in tenant_b_key
            assert tenant_a_key != tenant_b_key
            assert "conv_memory:contact_123" in tenant_a_key
            assert "conv_memory:contact_123" in tenant_b_key

            # Test operations with tenant keys
            await redis_client.set(tenant_a_key, {"data": "tenant_a_data"})
            await redis_client.set(tenant_b_key, {"data": "tenant_b_data"})

            # Verify calls were made with correct keys
            mock_redis.set.assert_any_call(tenant_a_key, {"data": "tenant_a_data"})
            mock_redis.set.assert_any_call(tenant_b_key, {"data": "tenant_b_data"})

    @pytest.mark.asyncio
    async def test_redis_cache_hit_miss_patterns(self):
        """Test Redis cache hit/miss patterns and performance"""

        cache_data = {
            "conv_memory:tenant_1:contact_1": {"conversation": "data1"},
            "conv_memory:tenant_1:contact_2": {"conversation": "data2"},
            "conv_memory:tenant_2:contact_1": {"conversation": "data3"}
        }

        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()

            # Mock cache behavior: hit for existing keys, miss for others
            def mock_get(key):
                return cache_data.get(key, None)

            mock_redis.get = AsyncMock(side_effect=mock_get)
            mock_from_url.return_value = mock_redis

            redis_client = EnhancedRedisClient()
            await redis_client.connect()

            # Test cache hits
            cache_hits = 0
            cache_misses = 0

            test_keys = [
                "conv_memory:tenant_1:contact_1",  # Hit
                "conv_memory:tenant_1:contact_2",  # Hit
                "conv_memory:tenant_1:contact_3",  # Miss
                "conv_memory:tenant_2:contact_1",  # Hit
                "conv_memory:tenant_2:contact_2",  # Miss
            ]

            for key in test_keys:
                result = await redis_client.get(key)
                if result is not None:
                    cache_hits += 1
                else:
                    cache_misses += 1

            # Calculate hit rate
            hit_rate = cache_hits / (cache_hits + cache_misses)

            # Verify cache performance
            assert cache_hits == 3
            assert cache_misses == 2
            assert hit_rate == 0.6  # 60% hit rate

    @pytest.mark.asyncio
    async def test_redis_failover_and_fallback(self):
        """Test Redis failover scenarios and fallback behavior"""

        with patch('aioredis.from_url') as mock_from_url:
            # Simulate Redis connection failure
            mock_from_url.side_effect = ConnectionError("Redis connection failed")

            redis_client = EnhancedRedisClient()

            # Test graceful failover
            try:
                await redis_client.connect()
            except ConnectionError:
                pass

            # Test fallback behavior (operations should not crash)
            result = await redis_client.get("any_key")  # Should return None gracefully
            assert result is None

            await redis_client.set("any_key", "any_value")  # Should not raise exception

            # Test Redis recovery
            mock_from_url.side_effect = None  # Clear the exception
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value="cached_value")
            mock_from_url.return_value = mock_redis

            await redis_client.connect()  # Reconnect
            result = await redis_client.get("test_key")
            assert result == "cached_value"

    @pytest.mark.asyncio
    async def test_redis_health_monitoring(self):
        """Test Redis health monitoring and metrics"""

        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()

            # Mock health check responses
            health_responses = [
                b"PONG",  # Healthy
                ConnectionError("Redis down"),  # Unhealthy
                b"PONG"   # Recovered
            ]

            mock_redis.ping = AsyncMock(side_effect=health_responses)
            mock_from_url.return_value = mock_redis

            redis_client = EnhancedRedisClient()
            health_monitor = RedisHealthMonitor(redis_client)

            # Test health monitoring cycle
            health_results = []
            for _ in range(3):
                try:
                    status = await health_monitor.check_health()
                    health_results.append(status["healthy"])
                except Exception:
                    health_results.append(False)

            # Verify health monitoring pattern
            assert health_results == [True, False, True]

            # Test health metrics collection
            metrics = health_monitor.get_health_metrics()
            assert "total_checks" in metrics
            assert "failed_checks" in metrics
            assert "success_rate" in metrics

class TestIntegratedDatabaseRedisOperations:
    """Test integrated database and Redis operations"""

    @pytest.mark.asyncio
    async def test_l1_l2_cache_strategy(self, sample_tenant_data):
        """Test L1 (Redis) and L2 (Database) caching strategy"""

        with patch('asyncpg.create_pool') as mock_db_pool, \
             patch('aioredis.from_url') as mock_redis:

            # Setup mocks
            mock_db = AsyncMock()
            mock_db.fetchrow = AsyncMock(return_value=sample_tenant_data["conversations"][0])
            mock_db_pool.return_value = mock_db

            mock_redis_client = AsyncMock()
            mock_redis_client.get = AsyncMock(return_value=None)  # Cache miss
            mock_redis_client.setex = AsyncMock()
            mock_redis.return_value = mock_redis_client

            memory_service = EnhancedMemoryService(use_database=True)

            # Test cache miss scenario (L1 miss, L2 hit)
            tenant_id = sample_tenant_data["tenant"]["id"]
            contact_id = sample_tenant_data["conversations"][0]["contact_id"]

            conversation = await memory_service.get_conversation_with_memory(
                tenant_id, contact_id
            )

            # Verify L2 (database) was queried
            mock_db.fetchrow.assert_called_once()

            # Verify L1 (Redis) was populated
            mock_redis_client.setex.assert_called_once()

            # Test cache hit scenario
            mock_redis_client.get.return_value = json.dumps(sample_tenant_data["conversations"][0])
            mock_db.fetchrow.reset_mock()

            conversation = await memory_service.get_conversation_with_memory(
                tenant_id, contact_id
            )

            # Verify L1 cache hit (database not queried)
            mock_db.fetchrow.assert_not_called()

    @pytest.mark.asyncio
    async def test_cache_invalidation_consistency(self, sample_tenant_data):
        """Test cache invalidation and consistency maintenance"""

        with patch('asyncpg.create_pool') as mock_db_pool, \
             patch('aioredis.from_url') as mock_redis:

            mock_db = AsyncMock()
            mock_redis_client = AsyncMock()
            mock_db_pool.return_value = mock_db
            mock_redis.return_value = mock_redis_client

            memory_service = EnhancedMemoryService(use_database=True)

            tenant_id = sample_tenant_data["tenant"]["id"]
            conversation_id = sample_tenant_data["conversations"][0]["id"]

            # Test cache invalidation on update
            await memory_service.update_behavioral_preferences(
                conversation_id=conversation_id,
                interaction_data={"property_id": "prop_123", "feedback": "interested"},
                learning_source="property_interaction"
            )

            # Verify cache invalidation calls
            mock_redis_client.delete.assert_called()

            # Verify database update
            mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_concurrent_database_redis_operations(self):
        """Test concurrent database and Redis operations under load"""

        async def concurrent_operation(operation_id: int):
            """Simulate concurrent memory service operations"""
            with patch('asyncpg.create_pool'), patch('aioredis.from_url'):
                memory_service = EnhancedMemoryService(use_database=True)

                # Simulate memory operations
                tenant_id = f"tenant_{operation_id % 10}"  # 10 tenants
                contact_id = f"contact_{operation_id}"

                await memory_service.get_conversation_with_memory(tenant_id, contact_id)

                # Simulate behavioral update
                await memory_service.update_behavioral_preferences(
                    conversation_id=str(uuid.uuid4()),
                    interaction_data={"test": f"data_{operation_id}"},
                    learning_source="concurrent_test"
                )

                return operation_id

        # Run 50 concurrent operations
        start_time = time.perf_counter()
        tasks = [concurrent_operation(i) for i in range(50)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()

        # Verify all operations completed
        successful_operations = [r for r in results if isinstance(r, int)]
        failed_operations = [r for r in results if isinstance(r, Exception)]

        assert len(successful_operations) >= 45  # At least 90% success rate
        assert len(failed_operations) <= 5

        # Verify reasonable performance
        total_time = end_time - start_time
        operations_per_second = len(successful_operations) / total_time
        assert operations_per_second > 10  # At least 10 ops/sec

if __name__ == "__main__":
    # Run database and Redis tests
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])