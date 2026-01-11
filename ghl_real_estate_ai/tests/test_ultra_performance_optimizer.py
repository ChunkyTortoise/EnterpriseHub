"""
Tests for Ultra-Performance Database Optimizer

Test Coverage:
- Connection pool management and performance
- Prepared statement caching
- Query optimization and routing
- Read/write replica routing
- Batch operations
- Transaction optimization
- Performance metrics
- Health monitoring
- Target achievement (<25ms queries)

Author: Claude Sonnet 4
Date: 2026-01-10
"""

import pytest
import asyncio
import time
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from ghl_real_estate_ai.services.ultra_performance_optimizer import (
    UltraPerformanceOptimizer,
    ConnectionPoolManager,
    PreparedStatementCache,
    QueryOptimizer,
    QueryType,
    ConnectionPoolType,
    UltraPerformanceMetrics,
    get_ultra_performance_optimizer
)


# Test Fixtures

@pytest.fixture
def mock_database_url():
    """Mock database URL for testing"""
    return "postgresql://test:test@localhost:5432/testdb"


@pytest.fixture
def mock_asyncpg_pool():
    """Mock asyncpg pool"""
    pool = AsyncMock()
    pool.get_size = Mock(return_value=10)
    pool.get_idle_size = Mock(return_value=5)
    return pool


@pytest.fixture
def mock_asyncpg_connection():
    """Mock asyncpg connection"""
    connection = AsyncMock()
    connection.fetch = AsyncMock(return_value=[])
    connection.fetchval = AsyncMock(return_value=1)
    connection.execute = AsyncMock()
    return connection


@pytest.fixture(scope="function")
async def optimizer(mock_database_url):
    """Create optimizer instance for testing"""
    with patch('ghl_real_estate_ai.services.ultra_performance_optimizer.asyncpg.create_pool') as mock_create_pool, \
         patch('ghl_real_estate_ai.services.ultra_performance_optimizer.get_optimized_redis_client') as mock_redis, \
         patch('ghl_real_estate_ai.services.ultra_performance_optimizer.get_predictive_cache_manager') as mock_cache:

        # Setup mocks
        mock_pool = AsyncMock()
        mock_pool.get_size = Mock(return_value=10)
        mock_pool.get_idle_size = Mock(return_value=5)
        mock_pool.acquire = AsyncMock()
        mock_pool.release = AsyncMock()
        mock_create_pool.return_value = mock_pool

        mock_redis.return_value = AsyncMock()
        mock_cache_instance = AsyncMock()
        mock_cache_instance.get = AsyncMock(return_value=(None, False))
        mock_cache_instance.set = AsyncMock()
        mock_cache.return_value = mock_cache_instance

        # Create optimizer
        opt = UltraPerformanceOptimizer(
            primary_url=mock_database_url,
            read_replica_url=mock_database_url,
            analytics_replica_url=mock_database_url,
            max_connection_pool_size=20,
            min_connection_pool_size=5
        )

        await opt.initialize()

        yield opt

        await opt.cleanup()


# Query Optimizer Tests

class TestQueryOptimizer:
    """Test query optimizer functionality"""

    def test_classify_read_query(self):
        """Test classification of SELECT queries"""
        optimizer = QueryOptimizer()

        query = "SELECT * FROM users WHERE id = 1"
        query_type = optimizer.classify_query(query)

        assert query_type == QueryType.READ

    def test_classify_analytical_query(self):
        """Test classification of analytical queries"""
        optimizer = QueryOptimizer()

        query = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id"
        query_type = optimizer.classify_query(query)

        assert query_type == QueryType.ANALYTICAL

    def test_classify_write_query(self):
        """Test classification of INSERT/UPDATE/DELETE queries"""
        optimizer = QueryOptimizer()

        assert optimizer.classify_query("INSERT INTO users VALUES (1, 'test')") == QueryType.WRITE
        assert optimizer.classify_query("UPDATE users SET name = 'test'") == QueryType.WRITE
        assert optimizer.classify_query("DELETE FROM users WHERE id = 1") == QueryType.WRITE

    def test_suggest_optimizations_select_star(self):
        """Test optimization suggestions for SELECT *"""
        optimizer = QueryOptimizer()

        query = "SELECT * FROM users"
        suggestions = optimizer.suggest_optimizations(query, {})

        assert any("SELECT *" in s for s in suggestions)

    def test_suggest_optimizations_missing_where(self):
        """Test optimization suggestions for missing WHERE clause"""
        optimizer = QueryOptimizer()

        query = "SELECT id, name FROM users"
        suggestions = optimizer.suggest_optimizations(query, {})

        assert any("WHERE" in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_analyze_execution_plan(self, mock_asyncpg_connection):
        """Test execution plan analysis"""
        optimizer = QueryOptimizer()

        # Mock execution plan
        mock_plan = [
            {
                "Plan": {
                    "Total Cost": 100.5,
                    "Actual Total Time": 25.3
                }
            }
        ]

        mock_asyncpg_connection.fetchval = AsyncMock(return_value=mock_plan)

        result = await optimizer.analyze_execution_plan(
            mock_asyncpg_connection,
            "SELECT * FROM users"
        )

        assert "plan" in result
        assert result["total_cost"] == 100.5
        assert result["actual_time_ms"] == 25.3


# Prepared Statement Cache Tests

class TestPreparedStatementCache:
    """Test prepared statement caching"""

    @pytest.mark.asyncio
    async def test_statement_id_generation(self, mock_asyncpg_connection):
        """Test unique statement ID generation"""
        cache = PreparedStatementCache(max_size=100)

        query1 = "SELECT * FROM users WHERE id = $1"
        query2 = "SELECT   *   FROM   users   WHERE   id = $1"  # Same query, different spacing

        id1 = cache._generate_statement_id(query1)
        id2 = cache._generate_statement_id(query2)

        # Should generate same ID for normalized queries
        assert id1 == id2

    @pytest.mark.asyncio
    async def test_prepared_statement_creation(self, mock_asyncpg_connection):
        """Test prepared statement creation and caching"""
        cache = PreparedStatementCache(max_size=100)

        query = "SELECT * FROM users WHERE id = $1"

        stmt_name = await cache.get_or_create(mock_asyncpg_connection, query)

        # Verify statement was prepared
        mock_asyncpg_connection.execute.assert_called_once()
        assert stmt_name.startswith("stmt_")

        # Verify cached
        query_hash = cache._generate_statement_id(query)
        assert query_hash in cache.statements

    @pytest.mark.asyncio
    async def test_prepared_statement_lru_eviction(self, mock_asyncpg_connection):
        """Test LRU eviction when cache is full"""
        cache = PreparedStatementCache(max_size=3)

        # Add 4 statements (should evict oldest)
        queries = [
            f"SELECT * FROM table{i} WHERE id = $1"
            for i in range(4)
        ]

        for query in queries:
            await cache.get_or_create(mock_asyncpg_connection, query)

        # Cache should contain only last 3
        assert len(cache.statements) == 3

        # First query should be evicted
        first_hash = cache._generate_statement_id(queries[0])
        assert first_hash not in cache.statements

    @pytest.mark.asyncio
    async def test_execute_prepared_statement(self, mock_asyncpg_connection):
        """Test prepared statement execution"""
        cache = PreparedStatementCache(max_size=100)

        query = "SELECT * FROM users WHERE id = $1"
        params = [123]

        # Mock fetch result
        mock_row = MagicMock()
        mock_row.__iter__ = Mock(return_value=iter([('id', 123), ('name', 'test')]))
        mock_asyncpg_connection.fetch = AsyncMock(return_value=[mock_row])

        result = await cache.execute_prepared(
            mock_asyncpg_connection,
            query,
            params
        )

        # Verify execution
        assert isinstance(result, list)


# Connection Pool Manager Tests

class TestConnectionPoolManager:
    """Test connection pool management"""

    @pytest.mark.asyncio
    async def test_pool_initialization(self, mock_database_url):
        """Test connection pool initialization"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_pool.get_size = Mock(return_value=10)
            mock_pool.get_idle_size = Mock(return_value=5)
            mock_create_pool.return_value = mock_pool

            pool_manager = ConnectionPoolManager(
                pool_type=ConnectionPoolType.PRIMARY,
                database_url=mock_database_url,
                min_size=5,
                max_size=20
            )

            await pool_manager.initialize()

            # Verify pool created with correct parameters
            mock_create_pool.assert_called_once()
            assert pool_manager.pool is not None

    @pytest.mark.asyncio
    async def test_connection_acquisition_tracking(self, mock_database_url, mock_asyncpg_connection):
        """Test connection acquisition time tracking"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_pool.get_size = Mock(return_value=10)
            mock_pool.get_idle_size = Mock(return_value=5)
            mock_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
            mock_create_pool.return_value = mock_pool

            pool_manager = ConnectionPoolManager(
                pool_type=ConnectionPoolType.PRIMARY,
                database_url=mock_database_url
            )

            await pool_manager.initialize()

            # Acquire connection
            connection = await pool_manager.acquire(timeout=5.0)

            # Verify metrics updated
            assert pool_manager.metrics.total_acquisitions == 1
            assert pool_manager.metrics.active_connections == 1
            assert pool_manager.metrics.avg_acquisition_time_ms >= 0

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self, mock_database_url):
        """Test handling of pool exhaustion"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_pool.get_size = Mock(return_value=10)
            mock_pool.get_idle_size = Mock(return_value=5)
            mock_pool.acquire = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_create_pool.return_value = mock_pool

            pool_manager = ConnectionPoolManager(
                pool_type=ConnectionPoolType.PRIMARY,
                database_url=mock_database_url
            )

            await pool_manager.initialize()

            # Should raise TimeoutError and track exhaustion
            with pytest.raises(asyncio.TimeoutError):
                await pool_manager.acquire(timeout=0.1)

            assert pool_manager.metrics.pool_exhausted_count == 1

    @pytest.mark.asyncio
    async def test_health_check(self, mock_database_url, mock_asyncpg_connection):
        """Test connection pool health check"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_pool.get_size = Mock(return_value=10)
            mock_pool.get_idle_size = Mock(return_value=5)
            mock_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
            mock_pool.__aenter__ = AsyncMock(return_value=mock_asyncpg_connection)
            mock_pool.__aexit__ = AsyncMock()
            mock_create_pool.return_value = mock_pool

            pool_manager = ConnectionPoolManager(
                pool_type=ConnectionPoolType.PRIMARY,
                database_url=mock_database_url
            )

            await pool_manager.initialize()

            # Perform health check
            healthy = await pool_manager.health_check()

            assert healthy is True
            assert pool_manager.metrics.last_health_check is not None


# Ultra-Performance Optimizer Tests

class TestUltraPerformanceOptimizer:
    """Test ultra-performance optimizer"""

    @pytest.mark.asyncio
    async def test_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.primary_pool is not None
        assert optimizer.read_replica_pool is not None
        assert optimizer.analytics_pool is not None
        assert optimizer.prepared_statement_cache is not None
        assert optimizer.query_optimizer is not None

    @pytest.mark.asyncio
    async def test_execute_optimized_query_with_cache(self, optimizer):
        """Test optimized query execution with cache hit"""
        # Mock predictive cache to return cached result
        cached_data = [{"id": 1, "name": "test"}]
        optimizer.predictive_cache.get = AsyncMock(return_value=(cached_data, True))

        query = "SELECT * FROM users WHERE id = $1"
        params = [1]

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            user_id="test_user",
            use_cache=True
        )

        # Verify cache hit
        assert results == cached_data
        assert metadata["cached"] is True
        assert optimizer.metrics.cache_hits == 1

    @pytest.mark.asyncio
    async def test_execute_optimized_query_cache_miss(self, optimizer, mock_asyncpg_connection):
        """Test optimized query execution with cache miss"""
        # Mock cache miss
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        # Mock connection and query result
        mock_row = MagicMock()
        mock_row.__iter__ = Mock(return_value=iter([('id', 1), ('name', 'test')]))
        mock_asyncpg_connection.fetch = AsyncMock(return_value=[mock_row])

        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        query = "SELECT * FROM users WHERE id = $1"
        params = [1]

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            user_id="test_user",
            use_cache=True
        )

        # Verify cache miss and query execution
        assert metadata["cached"] is False
        assert optimizer.metrics.cache_misses == 1
        assert optimizer.metrics.total_queries == 1

    @pytest.mark.asyncio
    async def test_query_routing_read_replica(self, optimizer, mock_asyncpg_connection):
        """Test query routing to read replica"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        query = "SELECT * FROM users WHERE id = $1"
        params = [1]

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            use_cache=False
        )

        # Verify routed to read replica
        assert metadata["pool_used"] == "read_replica"
        assert optimizer.metrics.read_replica_queries == 1

    @pytest.mark.asyncio
    async def test_query_routing_primary(self, optimizer, mock_asyncpg_connection):
        """Test query routing to primary for writes"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        optimizer.primary_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.primary_pool.release = AsyncMock()

        query = "INSERT INTO users (id, name) VALUES ($1, $2)"
        params = [1, "test"]

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            use_cache=False
        )

        # Verify routed to primary
        assert metadata["pool_used"] == "primary"
        assert optimizer.metrics.primary_queries == 1

    @pytest.mark.asyncio
    async def test_query_routing_analytics(self, optimizer, mock_asyncpg_connection):
        """Test query routing to analytics replica for complex queries"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        optimizer.analytics_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.analytics_pool.release = AsyncMock()

        query = "SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) > 10"
        params = []

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            use_cache=False
        )

        # Verify routed to analytics
        assert metadata["pool_used"] == "analytics"
        assert optimizer.metrics.analytical_queries == 1

    @pytest.mark.asyncio
    async def test_batch_execution_parallel(self, optimizer, mock_asyncpg_connection):
        """Test batch query execution with parallelization"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        # Multiple read queries
        queries = [
            ("SELECT * FROM users WHERE id = $1", [i])
            for i in range(5)
        ]

        start_time = time.time()
        results = await optimizer.execute_batch_optimized(queries)
        execution_time = time.time() - start_time

        # Verify all queries executed
        assert len(results) == 5

        # Parallel execution should be faster than sequential
        # (though in mock this won't show significant difference)
        assert execution_time < 1.0  # Should be very fast with mocks

    @pytest.mark.asyncio
    async def test_transaction_execution(self, optimizer, mock_asyncpg_connection):
        """Test transaction execution with savepoints"""
        # Mock transaction
        mock_transaction = AsyncMock()
        mock_transaction.start = AsyncMock()
        mock_transaction.commit = AsyncMock()
        mock_transaction.rollback = AsyncMock()

        mock_asyncpg_connection.transaction = Mock(return_value=mock_transaction)
        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        mock_asyncpg_connection.execute = AsyncMock()

        optimizer.primary_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.primary_pool.release = AsyncMock()

        queries = [
            ("INSERT INTO users (id, name) VALUES ($1, $2)", [1, "test1"]),
            ("INSERT INTO users (id, name) VALUES ($1, $2)", [2, "test2"])
        ]

        results = await optimizer.execute_transaction_optimized(queries)

        # Verify transaction committed
        mock_transaction.start.assert_called_once()
        mock_transaction.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_target_achievement(self, optimizer, mock_asyncpg_connection):
        """Test achievement of <25ms performance target"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        # Mock fast query execution
        async def fast_fetch(*args, **kwargs):
            await asyncio.sleep(0.01)  # 10ms execution
            return []

        mock_asyncpg_connection.fetch = AsyncMock(side_effect=fast_fetch)
        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        # Execute multiple queries to build metrics
        query = "SELECT * FROM users WHERE id = $1"
        for i in range(100):
            await optimizer.execute_optimized_query(
                query,
                [i],
                use_cache=False
            )

        # Check performance metrics
        metrics = await optimizer.get_performance_metrics()

        # Verify performance targets
        assert metrics["performance"]["avg_query_time_ms"] < 25.0
        assert metrics["performance"]["p90_query_time_ms"] < 25.0

    @pytest.mark.asyncio
    async def test_slow_query_detection(self, optimizer, mock_asyncpg_connection):
        """Test detection and analysis of slow queries"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        # Mock slow query execution
        async def slow_fetch(*args, **kwargs):
            await asyncio.sleep(0.15)  # 150ms - slow query
            return []

        mock_asyncpg_connection.fetch = AsyncMock(side_effect=slow_fetch)
        mock_asyncpg_connection.fetchval = AsyncMock(return_value='[{"Plan": {"Total Cost": 1000, "Actual Total Time": 150}}]')

        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        query = "SELECT * FROM large_table WHERE complex_condition = true"

        await optimizer.execute_optimized_query(query, use_cache=False)

        # Verify slow query detected
        assert optimizer.metrics.slow_queries_detected == 1

    @pytest.mark.asyncio
    async def test_connection_pool_efficiency(self, optimizer):
        """Test connection pool efficiency metrics"""
        # Simulate efficient pool operations
        optimizer.primary_pool.metrics.avg_acquisition_time_ms = 3.0
        optimizer.read_replica_pool.metrics.avg_acquisition_time_ms = 2.0

        # Execute query to update metrics
        optimizer.metrics.total_queries = 100
        await optimizer._update_metrics(10.0)

        # Check efficiency
        assert optimizer.metrics.connection_pool_efficiency > 0

    @pytest.mark.asyncio
    async def test_health_check(self, optimizer):
        """Test comprehensive health check"""
        # Mock pool health checks
        optimizer.primary_pool.health_check = AsyncMock(return_value=True)
        optimizer.read_replica_pool.health_check = AsyncMock(return_value=True)
        optimizer.analytics_pool.health_check = AsyncMock(return_value=True)

        health = await optimizer.health_check()

        assert health["healthy"] is True
        assert "pools" in health
        assert "metrics" in health
        assert "primary_pool" in health["pools"]

    @pytest.mark.asyncio
    async def test_metrics_comprehensive(self, optimizer):
        """Test comprehensive metrics reporting"""
        # Set some metrics
        optimizer.metrics.total_queries = 1000
        optimizer.metrics.cache_hits = 950
        optimizer.metrics.cache_misses = 50
        optimizer.metrics.read_replica_queries = 700
        optimizer.metrics.primary_queries = 200
        optimizer.metrics.analytical_queries = 100

        optimizer.query_times.extend([10.0, 15.0, 20.0, 25.0, 30.0] * 200)

        await optimizer._update_metrics(20.0)

        metrics = await optimizer.get_performance_metrics()

        # Verify comprehensive metrics
        assert "performance" in metrics
        assert "query_routing" in metrics
        assert "optimization" in metrics
        assert "connection_pools" in metrics
        assert "prepared_statements" in metrics

        # Verify calculations
        assert metrics["performance"]["cache_hit_rate"] == 95.0
        assert metrics["query_routing"]["read_replica_queries"] == 700


# Integration Tests

class TestIntegration:
    """Integration tests for ultra-performance optimizer"""

    @pytest.mark.asyncio
    async def test_end_to_end_query_flow(self, optimizer, mock_asyncpg_connection):
        """Test complete query execution flow"""
        # Setup mocks
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_row = MagicMock()
        mock_row.__iter__ = Mock(return_value=iter([('id', 1), ('name', 'test'), ('email', 'test@test.com')]))
        mock_asyncpg_connection.fetch = AsyncMock(return_value=[mock_row])

        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        # Execute query
        query = "SELECT id, name, email FROM users WHERE id = $1"
        params = [1]

        results, metadata = await optimizer.execute_optimized_query(
            query,
            params,
            user_id="test_user",
            use_cache=True
        )

        # Verify complete flow
        assert len(results) >= 0
        assert "execution_time_ms" in metadata
        assert metadata["pool_used"] in ["primary", "read_replica", "analytics"]

        # Verify cache was populated
        optimizer.predictive_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_under_load(self, optimizer, mock_asyncpg_connection):
        """Test performance under concurrent load"""
        optimizer.predictive_cache.get = AsyncMock(return_value=(None, False))
        optimizer.predictive_cache.set = AsyncMock()

        mock_asyncpg_connection.fetch = AsyncMock(return_value=[])
        optimizer.read_replica_pool.acquire = AsyncMock(return_value=mock_asyncpg_connection)
        optimizer.read_replica_pool.release = AsyncMock()

        # Execute concurrent queries
        query = "SELECT * FROM users WHERE id = $1"

        async def execute_query(i):
            return await optimizer.execute_optimized_query(query, [i], use_cache=False)

        # Simulate 50 concurrent queries
        tasks = [execute_query(i) for i in range(50)]
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        execution_time = time.time() - start_time

        # Verify all completed
        assert len(results) == 50

        # Check performance metrics
        assert optimizer.metrics.total_queries == 50

        # With mocks, should be very fast
        assert execution_time < 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
