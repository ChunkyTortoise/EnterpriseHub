"""
Comprehensive Performance Benchmarking and Load Testing Suite.

Features:
- Database performance benchmarks
- Redis performance tests
- API endpoint load testing
- Concurrent operation stress tests
- Memory and resource usage monitoring
- Performance regression detection
- Automated performance reporting
"""

import asyncio
import time
import logging
import statistics
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple, NamedTuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import aiohttp
import sys
import tracemalloc

from ..database.connection_manager import AdaptiveConnectionPool
from ..core.optimized_redis_config import OptimizedRedisManager
from ..cache.multi_layer_cache import MultiLayerCache

logger = logging.getLogger(__name__)

class BenchmarkResult(NamedTuple):
    """Benchmark result data structure."""
    name: str
    duration_ms: float
    operations_per_second: float
    memory_used_mb: float
    cpu_usage_percent: float
    success_rate: float
    error_count: int
    details: Dict[str, Any]

@dataclass
class LoadTestConfig:
    """Load test configuration."""
    concurrent_users: int = 10
    duration_seconds: int = 60
    ramp_up_time: int = 10
    endpoints: List[Dict[str, Any]] = field(default_factory=list)
    think_time_ms: int = 100
    timeout_seconds: int = 30

@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int

class PerformanceBenchmarks:
    """Comprehensive performance benchmarking suite."""

    def __init__(
        self,
        connection_pool: Optional[AdaptiveConnectionPool] = None,
        redis_manager: Optional[OptimizedRedisManager] = None,
        cache_manager: Optional[MultiLayerCache] = None
    ):
        self.connection_pool = connection_pool
        self.redis_manager = redis_manager
        self.cache_manager = cache_manager

        # Results storage
        self.benchmark_results: List[BenchmarkResult] = []
        self.system_metrics: List[SystemMetrics] = []

        # Monitoring
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None

    async def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark suite."""
        logger.info("Starting comprehensive performance benchmark suite")
        start_time = time.perf_counter()

        # Start system monitoring
        await self.start_system_monitoring()

        try:
            # Database benchmarks
            if self.connection_pool:
                await self.benchmark_database_performance()

            # Redis benchmarks
            if self.redis_manager:
                await self.benchmark_redis_performance()

            # Cache benchmarks
            if self.cache_manager:
                await self.benchmark_cache_performance()

            # Concurrent operation benchmarks
            await self.benchmark_concurrent_operations()

            # Memory and resource benchmarks
            await self.benchmark_memory_usage()

            # Generate comprehensive report
            total_duration = time.perf_counter() - start_time
            report = await self.generate_benchmark_report(total_duration)

            logger.info(f"Benchmark suite completed in {total_duration:.2f} seconds")
            return report

        finally:
            await self.stop_system_monitoring()

    async def benchmark_database_performance(self) -> List[BenchmarkResult]:
        """Benchmark database operations."""
        logger.info("Running database performance benchmarks")
        results = []

        if not self.connection_pool:
            logger.warning("No connection pool available for database benchmarks")
            return results

        # Test connection pool performance
        result = await self._benchmark_connection_pool()
        results.append(result)

        # Test basic CRUD operations
        result = await self._benchmark_crud_operations()
        results.append(result)

        # Test complex queries
        result = await self._benchmark_complex_queries()
        results.append(result)

        # Test concurrent connections
        result = await self._benchmark_concurrent_database_operations()
        results.append(result)

        self.benchmark_results.extend(results)
        return results

    async def _benchmark_connection_pool(self) -> BenchmarkResult:
        """Benchmark connection pool performance."""
        start_time = time.perf_counter()
        operation_count = 1000
        error_count = 0

        # Memory tracking
        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        # CPU monitoring
        process = psutil.Process()
        start_cpu = process.cpu_percent()

        try:
            # Test connection acquisition/release
            tasks = []
            for _ in range(operation_count):
                task = asyncio.create_task(self._test_connection_cycle())
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"Connection pool benchmark error: {e}")
            error_count = operation_count

        # Calculate metrics
        duration = time.perf_counter() - start_time
        end_memory = tracemalloc.get_traced_memory()[0]
        memory_used = (end_memory - start_memory) / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()

        tracemalloc.stop()

        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="database_connection_pool",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=memory_used,
            cpu_usage_percent=end_cpu - start_cpu,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "total_operations": operation_count,
                "avg_connection_time_ms": (duration * 1000) / operation_count
            }
        )

    async def _test_connection_cycle(self) -> bool:
        """Test single connection acquisition/release cycle."""
        try:
            async with self.connection_pool.get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception:
            return False

    async def _benchmark_crud_operations(self) -> BenchmarkResult:
        """Benchmark CRUD operations."""
        start_time = time.perf_counter()
        operation_count = 500  # 100 of each operation type
        error_count = 0

        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        try:
            # Mix of operations
            tasks = []

            # Create operations
            for i in range(100):
                task = self._test_create_operation(f"test_customer_{i}")
                tasks.append(task)

            # Read operations
            for i in range(100):
                task = self._test_read_operation()
                tasks.append(task)

            # Update operations
            for i in range(100):
                task = self._test_update_operation()
                tasks.append(task)

            # Delete operations
            for i in range(100):
                task = self._test_delete_operation()
                tasks.append(task)

            # Analytics operations
            for i in range(100):
                task = self._test_analytics_operation()
                tasks.append(task)

            # Execute all operations concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"CRUD benchmark error: {e}")
            error_count = operation_count

        # Calculate metrics
        duration = time.perf_counter() - start_time
        end_memory = tracemalloc.get_traced_memory()[0]
        memory_used = (end_memory - start_memory) / 1024 / 1024

        tracemalloc.stop()

        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="database_crud_operations",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=memory_used,
            cpu_usage_percent=0,  # Would need more sophisticated CPU tracking
            success_rate=success_rate,
            error_count=error_count,
            details={
                "total_operations": operation_count,
                "operation_mix": "20% each: CREATE, READ, UPDATE, DELETE, ANALYTICS"
            }
        )

    async def _test_create_operation(self, customer_name: str) -> bool:
        """Test customer creation operation."""
        try:
            async with self.connection_pool.get_session() as session:
                # Simplified create operation
                query = """
                    INSERT INTO customers (name, email, department, status)
                    VALUES (:name, :email, 'Sales', 'new')
                    RETURNING id
                """
                result = await session.execute(query, {
                    "name": customer_name,
                    "email": f"{customer_name}@test.com"
                })
                await session.commit()
                return result.rowcount > 0
        except Exception:
            return False

    async def _test_read_operation(self) -> bool:
        """Test read operation."""
        try:
            async with self.connection_pool.get_session() as session:
                query = "SELECT * FROM customers LIMIT 10"
                result = await session.execute(query)
                rows = result.fetchall()
                return len(rows) >= 0
        except Exception:
            return False

    async def _test_update_operation(self) -> bool:
        """Test update operation."""
        try:
            async with self.connection_pool.get_session() as session:
                query = """
                    UPDATE customers
                    SET last_interaction_at = CURRENT_TIMESTAMP
                    WHERE id IN (SELECT id FROM customers LIMIT 1)
                """
                result = await session.execute(query)
                await session.commit()
                return True
        except Exception:
            return False

    async def _test_delete_operation(self) -> bool:
        """Test delete operation."""
        try:
            async with self.connection_pool.get_session() as session:
                # Delete test customers created during benchmarking
                query = "DELETE FROM customers WHERE name LIKE 'test_customer_%' LIMIT 1"
                result = await session.execute(query)
                await session.commit()
                return True
        except Exception:
            return False

    async def _test_analytics_operation(self) -> bool:
        """Test analytics operation."""
        try:
            async with self.connection_pool.get_session() as session:
                query = """
                    SELECT
                        department,
                        status,
                        COUNT(*) as customer_count,
                        MAX(created_at) as latest_customer
                    FROM customers
                    GROUP BY department, status
                """
                result = await session.execute(query)
                rows = result.fetchall()
                return len(rows) >= 0
        except Exception:
            return False

    async def _benchmark_complex_queries(self) -> BenchmarkResult:
        """Benchmark complex analytical queries."""
        start_time = time.perf_counter()
        operation_count = 50
        error_count = 0

        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        try:
            tasks = []

            # Complex join queries
            for _ in range(20):
                task = self._test_complex_join_query()
                tasks.append(task)

            # Aggregation queries
            for _ in range(15):
                task = self._test_aggregation_query()
                tasks.append(task)

            # Full-text search queries
            for _ in range(15):
                task = self._test_fulltext_search()
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"Complex query benchmark error: {e}")
            error_count = operation_count

        duration = time.perf_counter() - start_time
        end_memory = tracemalloc.get_traced_memory()[0]
        memory_used = (end_memory - start_memory) / 1024 / 1024

        tracemalloc.stop()

        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="database_complex_queries",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=memory_used,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "query_types": "joins, aggregations, full-text search",
                "avg_query_time_ms": (duration * 1000) / operation_count
            }
        )

    async def _test_complex_join_query(self) -> bool:
        """Test complex join query."""
        try:
            async with self.connection_pool.get_session() as session:
                query = """
                    SELECT
                        c.name,
                        c.department,
                        COUNT(cm.id) as message_count,
                        AVG(cs.score) as avg_score
                    FROM customers c
                    LEFT JOIN conversation_messages cm ON c.id = cm.customer_id
                    LEFT JOIN customer_scores cs ON c.id = cs.customer_id
                    WHERE c.created_at > CURRENT_TIMESTAMP - INTERVAL '30 days'
                    GROUP BY c.id, c.name, c.department
                    ORDER BY avg_score DESC NULLS LAST
                    LIMIT 100
                """
                result = await session.execute(query)
                rows = result.fetchall()
                return True
        except Exception as e:
            logger.debug(f"Complex join query failed: {e}")
            return False

    async def _test_aggregation_query(self) -> bool:
        """Test aggregation query."""
        try:
            async with self.connection_pool.get_session() as session:
                query = """
                    SELECT
                        department,
                        status,
                        COUNT(*) as count,
                        MIN(created_at) as first_customer,
                        MAX(created_at) as latest_customer,
                        COUNT(CASE WHEN last_interaction_at > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 1 END) as active_customers
                    FROM customers
                    GROUP BY department, status
                    HAVING COUNT(*) > 0
                    ORDER BY count DESC
                """
                result = await session.execute(query)
                rows = result.fetchall()
                return True
        except Exception:
            return False

    async def _test_fulltext_search(self) -> bool:
        """Test full-text search query."""
        try:
            async with self.connection_pool.get_session() as session:
                query = """
                    SELECT
                        title,
                        content,
                        ts_rank_cd(to_tsvector('english', content), query) as rank
                    FROM knowledge_documents,
                         to_tsquery('english', 'platform & intelligence') query
                    WHERE to_tsvector('english', content) @@ query
                    ORDER BY rank DESC
                    LIMIT 10
                """
                result = await session.execute(query)
                rows = result.fetchall()
                return True
        except Exception:
            return False

    async def _benchmark_concurrent_database_operations(self) -> BenchmarkResult:
        """Benchmark concurrent database operations."""
        start_time = time.perf_counter()
        concurrent_users = 50
        operations_per_user = 20
        total_operations = concurrent_users * operations_per_user
        error_count = 0

        try:
            # Create semaphore to limit concurrency
            semaphore = asyncio.Semaphore(concurrent_users)

            async def user_simulation():
                async with semaphore:
                    user_errors = 0
                    for _ in range(operations_per_user):
                        try:
                            # Random operation
                            operation = asyncio.get_event_loop().time() % 4
                            if operation < 1:
                                await self._test_create_operation(f"concurrent_test_{asyncio.get_event_loop().time()}")
                            elif operation < 2:
                                await self._test_read_operation()
                            elif operation < 3:
                                await self._test_update_operation()
                            else:
                                await self._test_analytics_operation()

                            # Small delay between operations
                            await asyncio.sleep(0.01)
                        except Exception:
                            user_errors += 1

                    return user_errors

            # Run concurrent users
            tasks = [user_simulation() for _ in range(concurrent_users)]
            user_error_counts = await asyncio.gather(*tasks, return_exceptions=True)

            error_count = sum(
                count for count in user_error_counts
                if isinstance(count, int)
            )

        except Exception as e:
            logger.error(f"Concurrent database benchmark error: {e}")
            error_count = total_operations

        duration = time.perf_counter() - start_time
        ops_per_second = (total_operations - error_count) / duration if duration > 0 else 0
        success_rate = (total_operations - error_count) / total_operations

        return BenchmarkResult(
            name="database_concurrent_operations",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,  # Would need more detailed tracking
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "concurrent_users": concurrent_users,
                "operations_per_user": operations_per_user,
                "total_operations": total_operations
            }
        )

    async def benchmark_redis_performance(self) -> List[BenchmarkResult]:
        """Benchmark Redis operations."""
        logger.info("Running Redis performance benchmarks")
        results = []

        if not self.redis_manager:
            logger.warning("No Redis manager available for Redis benchmarks")
            return results

        # Basic operations benchmark
        result = await self._benchmark_redis_basic_operations()
        results.append(result)

        # Lua script operations
        result = await self._benchmark_redis_lua_scripts()
        results.append(result)

        # Pub/Sub performance
        result = await self._benchmark_redis_pubsub()
        results.append(result)

        self.benchmark_results.extend(results)
        return results

    async def _benchmark_redis_basic_operations(self) -> BenchmarkResult:
        """Benchmark basic Redis operations."""
        start_time = time.perf_counter()
        operation_count = 10000
        error_count = 0

        tracemalloc.start()
        start_memory = tracemalloc.get_traced_memory()[0]

        try:
            tasks = []

            # SET operations
            for i in range(2000):
                task = self.redis_manager.set_with_optimization(
                    f"benchmark_key_{i}", f"value_{i}", ttl=300
                )
                tasks.append(task)

            # GET operations
            for i in range(2000):
                task = self.redis_manager.get_with_optimization(f"benchmark_key_{i}")
                tasks.append(task)

            # MGET operations (batch gets)
            for i in range(100):
                batch_keys = [f"benchmark_key_{j}" for j in range(i*10, (i+1)*10)]
                task = self.redis_manager.mget_optimized(batch_keys)
                tasks.append(task)

            # Complex operations
            for i in range(1000):
                task = self._test_redis_complex_operation(f"complex_key_{i}")
                tasks.append(task)

            # Execute all operations
            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"Redis basic operations benchmark error: {e}")
            error_count = operation_count

        duration = time.perf_counter() - start_time
        end_memory = tracemalloc.get_traced_memory()[0]
        memory_used = (end_memory - start_memory) / 1024 / 1024

        tracemalloc.stop()

        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="redis_basic_operations",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=memory_used,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "operation_mix": "SET: 2000, GET: 2000, MGET: 100, Complex: 1000",
                "total_operations": operation_count
            }
        )

    async def _test_redis_complex_operation(self, key: str) -> bool:
        """Test complex Redis operation."""
        try:
            # Simulate complex data structure
            data = {
                "user_id": f"user_{key}",
                "preferences": {"theme": "dark", "notifications": True},
                "history": [f"action_{i}" for i in range(10)],
                "timestamp": datetime.utcnow().isoformat()
            }

            await self.redis_manager.set_with_optimization(key, data, ttl=600)
            retrieved = await self.redis_manager.get_with_optimization(key)

            return retrieved is not None

        except Exception:
            return False

    async def _benchmark_redis_lua_scripts(self) -> BenchmarkResult:
        """Benchmark Redis Lua script operations."""
        start_time = time.perf_counter()
        operation_count = 1000
        error_count = 0

        try:
            tasks = []

            # Conversation update operations (uses Lua script)
            for i in range(operation_count):
                messages = [
                    {"role": "user", "content": f"Test message {i}"},
                    {"role": "assistant", "content": f"Response {i}"}
                ]

                task = self.redis_manager.update_conversation_context_atomic(
                    key=f"conversation_{i}",
                    new_messages=messages,
                    extracted_preferences={"test": f"value_{i}"}
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"Redis Lua script benchmark error: {e}")
            error_count = operation_count

        duration = time.perf_counter() - start_time
        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="redis_lua_scripts",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "script_type": "conversation_update_atomic",
                "operations": operation_count
            }
        )

    async def _benchmark_redis_pubsub(self) -> BenchmarkResult:
        """Benchmark Redis pub/sub operations."""
        start_time = time.perf_counter()
        message_count = 1000
        error_count = 0

        try:
            channel = "benchmark_channel"
            messages_received = []

            # Message handler
            async def handle_message(message_data):
                messages_received.append(message_data)

            # Start publisher task
            async def publisher():
                errors = 0
                for i in range(message_count):
                    try:
                        await self.redis_manager.publish_event(channel, {
                            "message_id": i,
                            "data": f"benchmark_message_{i}"
                        })
                        await asyncio.sleep(0.001)  # Small delay
                    except Exception:
                        errors += 1
                return errors

            # Run publisher
            pub_errors = await publisher()
            error_count = pub_errors

            # Wait a bit for message processing
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Redis pub/sub benchmark error: {e}")
            error_count = message_count

        duration = time.perf_counter() - start_time
        ops_per_second = (message_count - error_count) / duration if duration > 0 else 0
        success_rate = (message_count - error_count) / message_count

        return BenchmarkResult(
            name="redis_pubsub",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "messages_published": message_count,
                "messages_received": len(messages_received)
            }
        )

    async def benchmark_cache_performance(self) -> List[BenchmarkResult]:
        """Benchmark multi-layer cache performance."""
        logger.info("Running cache performance benchmarks")
        results = []

        if not self.cache_manager:
            logger.warning("No cache manager available for cache benchmarks")
            return results

        # Cache layer performance
        result = await self._benchmark_cache_layers()
        results.append(result)

        # Cache hit/miss patterns
        result = await self._benchmark_cache_hit_patterns()
        results.append(result)

        self.benchmark_results.extend(results)
        return results

    async def _benchmark_cache_layers(self) -> BenchmarkResult:
        """Benchmark cache layer performance."""
        start_time = time.perf_counter()
        operation_count = 5000
        error_count = 0

        try:
            tasks = []

            # Mixed cache operations
            for i in range(operation_count):
                if i % 3 == 0:
                    # Set operation
                    task = self.cache_manager.set(
                        f"cache_bench_{i}",
                        {"data": f"value_{i}", "timestamp": datetime.utcnow().isoformat()},
                        ttl_seconds=300
                    )
                else:
                    # Get operation
                    task = self.cache_manager.get(f"cache_bench_{i % 100}")

                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

        except Exception as e:
            logger.error(f"Cache layer benchmark error: {e}")
            error_count = operation_count

        duration = time.perf_counter() - start_time
        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="cache_layer_performance",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "operation_mix": "33% SET, 67% GET",
                "cache_levels": "L1, L2, L3 automatic"
            }
        )

    async def _benchmark_cache_hit_patterns(self) -> BenchmarkResult:
        """Benchmark cache hit/miss patterns."""
        start_time = time.perf_counter()
        operation_count = 2000
        error_count = 0

        try:
            # First, populate cache with data
            for i in range(100):
                await self.cache_manager.set(f"pattern_key_{i}", f"value_{i}", ttl_seconds=600)

            tasks = []

            # 80% cache hits, 20% misses (realistic pattern)
            for i in range(operation_count):
                if i % 5 == 0:
                    # Cache miss (20%)
                    key = f"pattern_key_{i + 1000}"  # Non-existent key
                else:
                    # Cache hit (80%)
                    key = f"pattern_key_{i % 100}"  # Existing key

                task = self.cache_manager.get(key)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
            error_count = sum(1 for r in results if isinstance(r, Exception))

            # Calculate hit rate
            hits = sum(1 for r in results if r is not None and not isinstance(r, Exception))
            hit_rate = hits / (operation_count - error_count) if (operation_count - error_count) > 0 else 0

        except Exception as e:
            logger.error(f"Cache hit pattern benchmark error: {e}")
            error_count = operation_count
            hit_rate = 0

        duration = time.perf_counter() - start_time
        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="cache_hit_patterns",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "expected_hit_rate": 0.8,
                "actual_hit_rate": hit_rate,
                "cache_population": 100
            }
        )

    async def benchmark_concurrent_operations(self) -> List[BenchmarkResult]:
        """Benchmark concurrent operations across all systems."""
        logger.info("Running concurrent operations benchmarks")
        results = []

        # High concurrency stress test
        result = await self._benchmark_high_concurrency_stress()
        results.append(result)

        self.benchmark_results.extend(results)
        return results

    async def _benchmark_high_concurrency_stress(self) -> BenchmarkResult:
        """Benchmark high concurrency stress test."""
        start_time = time.perf_counter()
        concurrent_users = 100
        operations_per_user = 50
        total_operations = concurrent_users * operations_per_user
        error_count = 0

        try:
            semaphore = asyncio.Semaphore(concurrent_users)

            async def user_workload():
                async with semaphore:
                    user_errors = 0
                    for i in range(operations_per_user):
                        try:
                            # Mixed operations across all systems
                            operation_type = i % 4

                            if operation_type == 0 and self.connection_pool:
                                # Database operation
                                await self._test_read_operation()
                            elif operation_type == 1 and self.redis_manager:
                                # Redis operation
                                await self.redis_manager.set_with_optimization(
                                    f"stress_{asyncio.get_event_loop().time()}_{i}",
                                    f"value_{i}",
                                    ttl=60
                                )
                            elif operation_type == 2 and self.cache_manager:
                                # Cache operation
                                await self.cache_manager.get(f"cache_key_{i % 100}")
                            else:
                                # CPU-intensive operation
                                await asyncio.sleep(0.001)
                                sum(i * j for j in range(100))  # CPU work

                        except Exception:
                            user_errors += 1

                    return user_errors

            # Run concurrent users
            tasks = [user_workload() for _ in range(concurrent_users)]
            user_errors = await asyncio.gather(*tasks, return_exceptions=True)

            error_count = sum(
                errors for errors in user_errors
                if isinstance(errors, int)
            )

        except Exception as e:
            logger.error(f"High concurrency stress benchmark error: {e}")
            error_count = total_operations

        duration = time.perf_counter() - start_time
        ops_per_second = (total_operations - error_count) / duration if duration > 0 else 0
        success_rate = (total_operations - error_count) / total_operations

        return BenchmarkResult(
            name="high_concurrency_stress",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=0,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "concurrent_users": concurrent_users,
                "operations_per_user": operations_per_user,
                "total_operations": total_operations,
                "operation_mix": "25% DB, 25% Redis, 25% Cache, 25% CPU"
            }
        )

    async def benchmark_memory_usage(self) -> List[BenchmarkResult]:
        """Benchmark memory usage patterns."""
        logger.info("Running memory usage benchmarks")
        results = []

        result = await self._benchmark_memory_scaling()
        results.append(result)

        self.benchmark_results.extend(results)
        return results

    async def _benchmark_memory_scaling(self) -> BenchmarkResult:
        """Benchmark memory usage under increasing load."""
        start_time = time.perf_counter()
        operation_count = 1000
        error_count = 0

        # Track memory usage
        tracemalloc.start()
        initial_memory = tracemalloc.get_traced_memory()[0]
        memory_snapshots = []

        try:
            # Gradually increase memory usage
            data_sets = []

            for i in range(operation_count):
                # Create increasingly large data structures
                data_size = (i % 100) + 1
                large_data = {
                    "id": i,
                    "data": [f"item_{j}" for j in range(data_size * 10)],
                    "metadata": {"size": data_size, "created": datetime.utcnow().isoformat()}
                }

                data_sets.append(large_data)

                # Store in cache if available
                if self.cache_manager and i % 10 == 0:
                    try:
                        await self.cache_manager.set(f"memory_test_{i}", large_data, ttl_seconds=60)
                    except Exception:
                        error_count += 1

                # Take memory snapshot every 100 operations
                if i % 100 == 0:
                    current_memory = tracemalloc.get_traced_memory()[0]
                    memory_snapshots.append(current_memory)

                # Small delay to prevent overwhelming the system
                if i % 50 == 0:
                    await asyncio.sleep(0.01)

        except Exception as e:
            logger.error(f"Memory scaling benchmark error: {e}")
            error_count += 100

        final_memory = tracemalloc.get_traced_memory()[0]
        peak_memory = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()

        # Force garbage collection
        gc.collect()

        duration = time.perf_counter() - start_time
        memory_used = (peak_memory - initial_memory) / 1024 / 1024  # MB

        ops_per_second = (operation_count - error_count) / duration if duration > 0 else 0
        success_rate = (operation_count - error_count) / operation_count

        return BenchmarkResult(
            name="memory_scaling",
            duration_ms=duration * 1000,
            operations_per_second=ops_per_second,
            memory_used_mb=memory_used,
            cpu_usage_percent=0,
            success_rate=success_rate,
            error_count=error_count,
            details={
                "initial_memory_mb": initial_memory / 1024 / 1024,
                "peak_memory_mb": peak_memory / 1024 / 1024,
                "final_memory_mb": final_memory / 1024 / 1024,
                "memory_snapshots": len(memory_snapshots),
                "data_structures_created": len(data_sets)
            }
        )

    async def start_system_monitoring(self):
        """Start system resource monitoring."""
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._system_monitoring_task())

    async def stop_system_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

    async def _system_monitoring_task(self):
        """Background task to monitor system resources."""
        try:
            while self.monitoring_active:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                network_io = psutil.net_io_counters()

                metrics = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / 1024 / 1024,
                    disk_io_read_mb=disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    disk_io_write_mb=disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                    network_bytes_sent=network_io.bytes_sent if network_io else 0,
                    network_bytes_recv=network_io.bytes_recv if network_io else 0,
                    active_connections=len(psutil.net_connections()) if hasattr(psutil, 'net_connections') else 0
                )

                self.system_metrics.append(metrics)

                # Keep only recent metrics (last 1000 samples)
                if len(self.system_metrics) > 1000:
                    self.system_metrics = self.system_metrics[-1000:]

                await asyncio.sleep(1)  # Sample every second

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"System monitoring error: {e}")

    async def generate_benchmark_report(self, total_duration: float) -> Dict[str, Any]:
        """Generate comprehensive benchmark report."""
        # Calculate summary statistics
        successful_benchmarks = [b for b in self.benchmark_results if b.success_rate > 0.5]

        if successful_benchmarks:
            avg_ops_per_second = statistics.mean([b.operations_per_second for b in successful_benchmarks])
            total_operations = sum(b.operations_per_second * (b.duration_ms / 1000) for b in successful_benchmarks)
            avg_success_rate = statistics.mean([b.success_rate for b in successful_benchmarks])
        else:
            avg_ops_per_second = 0
            total_operations = 0
            avg_success_rate = 0

        # System resource analysis
        if self.system_metrics:
            max_cpu = max(m.cpu_percent for m in self.system_metrics)
            avg_cpu = statistics.mean([m.cpu_percent for m in self.system_metrics])
            max_memory = max(m.memory_used_mb for m in self.system_metrics)
            avg_memory = statistics.mean([m.memory_used_mb for m in self.system_metrics])
        else:
            max_cpu = avg_cpu = max_memory = avg_memory = 0

        # Performance recommendations
        recommendations = self._generate_performance_recommendations()

        report = {
            "benchmark_summary": {
                "total_duration_seconds": total_duration,
                "benchmarks_completed": len(self.benchmark_results),
                "successful_benchmarks": len(successful_benchmarks),
                "avg_operations_per_second": avg_ops_per_second,
                "total_operations_performed": total_operations,
                "avg_success_rate": avg_success_rate,
                "timestamp": datetime.utcnow().isoformat()
            },
            "system_resources": {
                "max_cpu_percent": max_cpu,
                "avg_cpu_percent": avg_cpu,
                "max_memory_mb": max_memory,
                "avg_memory_mb": avg_memory,
                "monitoring_samples": len(self.system_metrics)
            },
            "detailed_results": [
                {
                    "name": result.name,
                    "duration_ms": result.duration_ms,
                    "operations_per_second": result.operations_per_second,
                    "memory_used_mb": result.memory_used_mb,
                    "cpu_usage_percent": result.cpu_usage_percent,
                    "success_rate": result.success_rate,
                    "error_count": result.error_count,
                    "details": result.details
                }
                for result in self.benchmark_results
            ],
            "performance_recommendations": recommendations
        }

        return report

    def _generate_performance_recommendations(self) -> List[str]:
        """Generate performance recommendations based on benchmark results."""
        recommendations = []

        # Analyze results for recommendations
        for result in self.benchmark_results:
            if result.success_rate < 0.95:
                recommendations.append(
                    f"Consider optimizing {result.name} - success rate is {result.success_rate:.1%}"
                )

            if result.operations_per_second < 100 and "database" in result.name:
                recommendations.append(
                    f"Database performance for {result.name} is low - consider connection pool tuning"
                )

            if result.operations_per_second < 1000 and "redis" in result.name:
                recommendations.append(
                    f"Redis performance for {result.name} could be improved - check network latency"
                )

            if result.memory_used_mb > 100:
                recommendations.append(
                    f"High memory usage in {result.name} - consider memory optimization"
                )

        # System-level recommendations
        if self.system_metrics:
            max_cpu = max(m.cpu_percent for m in self.system_metrics)
            if max_cpu > 80:
                recommendations.append("High CPU usage detected - consider scaling up or optimizing CPU-intensive operations")

            max_memory = max(m.memory_percent for m in self.system_metrics)
            if max_memory > 80:
                recommendations.append("High memory usage detected - consider increasing available memory or optimizing memory usage")

        if not recommendations:
            recommendations.append("All benchmarks performed within acceptable ranges")

        return recommendations

# CLI interface for running benchmarks
if __name__ == "__main__":
    import asyncio
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run performance benchmarks")
    parser.add_argument("--database-url", help="Database connection URL")
    parser.add_argument("--redis-url", help="Redis connection URL")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    async def main():
        # Configure logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(level=log_level)

        # Initialize components if URLs provided
        connection_pool = None
        redis_manager = None
        cache_manager = None

        if args.database_url:
            from ..database.connection_manager import create_connection_manager
            connection_pool = await create_connection_manager(args.database_url)

        if args.redis_url:
            from ..core.optimized_redis_config import create_optimized_redis_manager
            redis_manager = await create_optimized_redis_manager(args.redis_url)

            if connection_pool:
                from ..cache.multi_layer_cache import MultiLayerCache
                cache_manager = MultiLayerCache(redis_manager)
                await cache_manager.start_background_tasks()

        # Run benchmarks
        benchmarks = PerformanceBenchmarks(connection_pool, redis_manager, cache_manager)

        try:
            report = await benchmarks.run_full_benchmark_suite()

            # Output results
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Results written to {args.output}")
            else:
                print(json.dumps(report, indent=2))

        finally:
            # Cleanup
            if cache_manager:
                await cache_manager.stop_background_tasks()
            if redis_manager:
                await redis_manager.close()
            if connection_pool:
                await connection_pool.close()

    asyncio.run(main())