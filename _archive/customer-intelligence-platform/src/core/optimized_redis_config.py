"""
Optimized Redis Configuration for Customer Intelligence Platform.

High-performance Redis setup for:
- Conversation context management
- Event streaming
- Caching layers
- Session management
- Real-time analytics
"""

import asyncio
import logging
import json
import pickle
import gzip
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, AsyncGenerator
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
import os

import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

@dataclass
class RedisPerformanceMetrics:
    """Redis performance metrics tracking."""
    operation: str
    duration_ms: float
    key: str
    data_size_bytes: int
    timestamp: datetime
    cache_hit: Optional[bool] = None
    error: Optional[str] = None

class OptimizedRedisManager:
    """High-performance Redis manager with advanced features."""

    def __init__(
        self,
        redis_url: str,
        pool_size: int = 50,
        retry_times: int = 3,
        enable_compression: bool = True,
        enable_metrics: bool = True,
        cluster_mode: bool = False
    ):
        self.redis_url = redis_url
        self.pool_size = pool_size
        self.enable_compression = enable_compression
        self.enable_metrics = enable_metrics
        self.cluster_mode = cluster_mode

        # Performance metrics
        self.metrics: List[RedisPerformanceMetrics] = []
        self.cache_hit_rate = 0.0

        # Connection pools for different workloads
        self.pools = {}
        self.clients = {}

        # Lua scripts for atomic operations
        self.lua_scripts = {}

    async def initialize(self):
        """Initialize Redis connections and load Lua scripts."""
        # Create optimized connection pools
        await self._create_connection_pools()

        # Load Lua scripts
        await self._load_lua_scripts()

        # Warm up connections
        await self._warmup_connections()

        logger.info("OptimizedRedisManager initialized successfully")

    async def _create_connection_pools(self):
        """Create specialized connection pools for different workloads."""

        # Main pool for general operations
        self.pools['main'] = ConnectionPool.from_url(
            self.redis_url,
            max_connections=self.pool_size,
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(), retries=3),
            socket_keepalive=True,
            socket_keepalive_options={},
            socket_connect_timeout=5,
            socket_timeout=5,
            decode_responses=False,  # We handle encoding ourselves for optimization
        )

        # High-frequency pool for caching
        self.pools['cache'] = ConnectionPool.from_url(
            self.redis_url,
            max_connections=min(self.pool_size * 2, 100),  # More connections for cache operations
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(), retries=1),  # Faster failure for cache misses
            socket_keepalive=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=False,
        )

        # Pub/Sub pool for event streaming
        self.pools['pubsub'] = ConnectionPool.from_url(
            self.redis_url,
            max_connections=10,  # Fewer connections needed for pub/sub
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(), retries=5),
            socket_keepalive=True,
            socket_connect_timeout=10,
            socket_timeout=30,  # Longer timeout for streaming
            decode_responses=True,  # Text-based for pub/sub
        )

        # Create clients
        for pool_name, pool in self.pools.items():
            self.clients[pool_name] = redis.Redis(connection_pool=pool)

    async def _load_lua_scripts(self):
        """Load optimized Lua scripts for atomic operations."""

        # Script for atomic conversation context update
        conversation_update_script = """
        local key = KEYS[1]
        local data = ARGV[1]
        local ttl = tonumber(ARGV[2])
        local max_history = tonumber(ARGV[3])

        -- Get existing context
        local existing = redis.call('GET', key)
        local context = {}

        if existing then
            context = cjson.decode(existing)
        else
            context = {
                conversation_history = {},
                extracted_preferences = {},
                created_at = ARGV[4],
                session_count = 0,
                total_messages = 0
            }
        end

        -- Merge new data
        local new_data = cjson.decode(data)
        if new_data.conversation_history then
            for i, msg in ipairs(new_data.conversation_history) do
                table.insert(context.conversation_history, msg)
            end

            -- Trim history if needed
            if #context.conversation_history > max_history then
                local start_idx = #context.conversation_history - max_history + 1
                local trimmed = {}
                for i = start_idx, #context.conversation_history do
                    table.insert(trimmed, context.conversation_history[i])
                end
                context.conversation_history = trimmed
            end
        end

        -- Update metadata
        context.last_interaction_at = new_data.last_interaction_at or context.last_interaction_at
        context.total_messages = (context.total_messages or 0) + (new_data.message_count or 0)

        -- Merge preferences
        if new_data.extracted_preferences then
            if not context.extracted_preferences then
                context.extracted_preferences = {}
            end
            for k, v in pairs(new_data.extracted_preferences) do
                context.extracted_preferences[k] = v
            end
        end

        -- Store updated context
        redis.call('SETEX', key, ttl, cjson.encode(context))

        return context.total_messages
        """

        # Script for batch context retrieval
        batch_get_script = """
        local keys = KEYS
        local results = {}

        for i, key in ipairs(keys) do
            local value = redis.call('GET', key)
            if value then
                results[key] = value
                -- Update access time
                redis.call('EXPIRE', key, ARGV[1])
            else
                results[key] = false
            end
        end

        return cjson.encode(results)
        """

        # Script for analytics aggregation
        analytics_aggregate_script = """
        local pattern = ARGV[1]
        local cursor = 0
        local stats = {
            total_contexts = 0,
            total_messages = 0,
            active_conversations = 0,
            departments = {}
        }

        repeat
            local result = redis.call('SCAN', cursor, 'MATCH', pattern, 'COUNT', 100)
            cursor = tonumber(result[1])
            local keys = result[2]

            for i, key in ipairs(keys) do
                local context = redis.call('GET', key)
                if context then
                    local data = cjson.decode(context)
                    stats.total_contexts = stats.total_contexts + 1
                    stats.total_messages = stats.total_messages + (data.total_messages or 0)

                    -- Check if active (interacted in last hour)
                    if data.last_interaction_at then
                        local last_interaction = data.last_interaction_at
                        -- Simplified activity check
                        stats.active_conversations = stats.active_conversations + 1
                    end

                    -- Department aggregation
                    local dept = data.department_id or 'default'
                    if not stats.departments[dept] then
                        stats.departments[dept] = 0
                    end
                    stats.departments[dept] = stats.departments[dept] + 1
                end
            end
        until cursor == 0

        return cjson.encode(stats)
        """

        # Register scripts
        main_client = self.clients['main']

        self.lua_scripts['conversation_update'] = main_client.register_script(conversation_update_script)
        self.lua_scripts['batch_get'] = main_client.register_script(batch_get_script)
        self.lua_scripts['analytics_aggregate'] = main_client.register_script(analytics_aggregate_script)

        logger.info("Lua scripts loaded successfully")

    async def _warmup_connections(self):
        """Warm up connection pools."""
        tasks = []
        for pool_name, client in self.clients.items():
            tasks.append(self._warmup_pool(client, pool_name))

        await asyncio.gather(*tasks)
        logger.info("Connection pools warmed up")

    async def _warmup_pool(self, client: redis.Redis, pool_name: str):
        """Warm up individual connection pool."""
        try:
            # Test basic operations
            await client.ping()
            await client.set(f"warmup_{pool_name}", "test", ex=10)
            await client.get(f"warmup_{pool_name}")
            await client.delete(f"warmup_{pool_name}")
        except Exception as e:
            logger.error(f"Failed to warm up {pool_name} pool: {e}")

    def _serialize_data(self, data: Any) -> bytes:
        """Optimize data serialization with compression."""
        if self.enable_compression:
            # Use pickle for complex objects, compress if beneficial
            serialized = pickle.dumps(data)
            if len(serialized) > 1024:  # Compress larger objects
                compressed = gzip.compress(serialized)
                if len(compressed) < len(serialized) * 0.8:  # Only if >20% reduction
                    return b'gzip:' + compressed
            return b'pickle:' + serialized
        else:
            # Fast JSON serialization for simple objects
            try:
                return json.dumps(data, default=str).encode('utf-8')
            except (TypeError, ValueError):
                # Fallback to pickle for complex objects
                return b'pickle:' + pickle.dumps(data)

    def _deserialize_data(self, data: bytes) -> Any:
        """Optimize data deserialization."""
        if data.startswith(b'gzip:'):
            compressed_data = data[5:]  # Remove 'gzip:' prefix
            return pickle.loads(gzip.decompress(compressed_data))
        elif data.startswith(b'pickle:'):
            return pickle.loads(data[7:])  # Remove 'pickle:' prefix
        else:
            # Assume JSON
            return json.loads(data.decode('utf-8'))

    async def _record_metrics(self, operation: str, key: str, duration_ms: float,
                             data_size: int = 0, cache_hit: Optional[bool] = None,
                             error: Optional[str] = None):
        """Record performance metrics."""
        if not self.enable_metrics:
            return

        metric = RedisPerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            key=key,
            data_size_bytes=data_size,
            timestamp=datetime.utcnow(),
            cache_hit=cache_hit,
            error=error
        )

        self.metrics.append(metric)

        # Keep only recent metrics (last 10000)
        if len(self.metrics) > 10000:
            self.metrics = self.metrics[-10000:]

        # Update cache hit rate
        if cache_hit is not None:
            recent_cache_ops = [m for m in self.metrics[-1000:] if m.cache_hit is not None]
            if recent_cache_ops:
                hits = sum(1 for m in recent_cache_ops if m.cache_hit)
                self.cache_hit_rate = hits / len(recent_cache_ops)

    async def set_with_optimization(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        pool: str = 'cache'
    ) -> bool:
        """Optimized SET operation with metrics and compression."""
        start_time = asyncio.get_event_loop().time()
        client = self.clients[pool]

        try:
            # Serialize data
            serialized_data = self._serialize_data(value)
            data_size = len(serialized_data)

            # Execute SET
            if ttl:
                result = await client.setex(key, ttl, serialized_data)
            else:
                result = await client.set(key, serialized_data)

            # Record metrics
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('SET', key, duration, data_size)

            return bool(result)

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('SET', key, duration, error=str(e))
            raise

    async def get_with_optimization(
        self,
        key: str,
        pool: str = 'cache'
    ) -> Optional[Any]:
        """Optimized GET operation with metrics and decompression."""
        start_time = asyncio.get_event_loop().time()
        client = self.clients[pool]

        try:
            # Execute GET
            result = await client.get(key)

            # Record metrics
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            cache_hit = result is not None
            data_size = len(result) if result else 0

            await self._record_metrics('GET', key, duration, data_size, cache_hit)

            if result:
                return self._deserialize_data(result)
            return None

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('GET', key, duration, cache_hit=False, error=str(e))
            raise

    async def mget_optimized(self, keys: List[str], pool: str = 'cache') -> Dict[str, Any]:
        """Optimized batch GET operation."""
        if not keys:
            return {}

        start_time = asyncio.get_event_loop().time()
        client = self.clients[pool]

        try:
            # Use Lua script for batch operations with TTL refresh
            result_json = await self.lua_scripts['batch_get'](
                keys=keys,
                args=[3600]  # Default TTL refresh
            )

            results = json.loads(result_json)
            parsed_results = {}

            cache_hits = 0
            total_size = 0

            for key, value in results.items():
                if value:
                    parsed_results[key] = self._deserialize_data(value.encode('latin-1'))
                    cache_hits += 1
                    total_size += len(value)
                else:
                    parsed_results[key] = None

            # Record metrics
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            cache_hit_rate = cache_hits / len(keys) if keys else 0

            await self._record_metrics(
                'MGET',
                f"batch_{len(keys)}_keys",
                duration,
                total_size,
                cache_hit_rate > 0.5
            )

            return parsed_results

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('MGET', f"batch_{len(keys)}_keys", duration, error=str(e))
            raise

    async def update_conversation_context_atomic(
        self,
        key: str,
        new_messages: List[Dict[str, Any]],
        extracted_preferences: Optional[Dict[str, Any]] = None,
        ttl: int = 7 * 24 * 3600,  # 7 days
        max_history: int = 50
    ) -> int:
        """Atomically update conversation context using Lua script."""

        update_data = {
            "conversation_history": new_messages,
            "extracted_preferences": extracted_preferences or {},
            "last_interaction_at": datetime.utcnow().isoformat(),
            "message_count": len(new_messages)
        }

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute atomic update
            total_messages = await self.lua_scripts['conversation_update'](
                keys=[key],
                args=[
                    json.dumps(update_data, default=str),
                    ttl,
                    max_history,
                    datetime.utcnow().isoformat()
                ]
            )

            # Record metrics
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('CONVERSATION_UPDATE', key, duration)

            return int(total_messages)

        except Exception as e:
            duration = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_metrics('CONVERSATION_UPDATE', key, duration, error=str(e))
            raise

    async def stream_events(
        self,
        channel: str,
        handler: callable,
        pool: str = 'pubsub'
    ) -> None:
        """High-performance event streaming with Redis Streams."""
        client = self.clients[pool]

        try:
            # Create consumer group if it doesn't exist
            try:
                await client.xgroup_create(channel, "processors", id='0', mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            # Process events
            consumer_name = f"consumer_{os.getpid()}_{id(self)}"

            while True:
                try:
                    # Read from stream
                    messages = await client.xreadgroup(
                        "processors",
                        consumer_name,
                        {channel: '>'},
                        count=10,  # Batch size
                        block=1000  # 1 second timeout
                    )

                    for stream, msgs in messages:
                        for msg_id, fields in msgs:
                            try:
                                # Process event
                                await handler(fields)

                                # Acknowledge message
                                await client.xack(channel, "processors", msg_id)

                            except Exception as e:
                                logger.error(f"Error processing event {msg_id}: {e}")
                                # Could implement dead letter queue here

                except redis.exceptions.ResponseError:
                    # Handle connection issues
                    await asyncio.sleep(1)
                    continue

        except Exception as e:
            logger.error(f"Event streaming error: {e}")
            raise

    async def publish_event(self, channel: str, event_data: Dict[str, Any]) -> str:
        """Publish event to Redis Stream."""
        client = self.clients['pubsub']

        # Add timestamp
        event_data['timestamp'] = datetime.utcnow().isoformat()

        # Publish to stream
        message_id = await client.xadd(channel, event_data)

        return message_id

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get Redis performance metrics."""
        if not self.metrics:
            return {"message": "No metrics available"}

        # Calculate metrics
        recent_metrics = self.metrics[-1000:]  # Last 1000 operations

        avg_duration = sum(m.duration_ms for m in recent_metrics) / len(recent_metrics)
        slow_operations = [m for m in recent_metrics if m.duration_ms > 50]  # >50ms

        operations_by_type = {}
        for metric in recent_metrics:
            op = metric.operation
            if op not in operations_by_type:
                operations_by_type[op] = []
            operations_by_type[op].append(metric.duration_ms)

        op_stats = {}
        for op, durations in operations_by_type.items():
            op_stats[op] = {
                "count": len(durations),
                "avg_duration_ms": sum(durations) / len(durations),
                "max_duration_ms": max(durations),
                "min_duration_ms": min(durations)
            }

        return {
            "cache_hit_rate": self.cache_hit_rate,
            "avg_operation_duration_ms": avg_duration,
            "slow_operations_count": len(slow_operations),
            "total_operations": len(recent_metrics),
            "operations_by_type": op_stats,
            "pool_info": await self._get_pool_info()
        }

    async def _get_pool_info(self) -> Dict[str, Any]:
        """Get connection pool information."""
        pool_info = {}

        for pool_name, client in self.clients.items():
            try:
                info = await client.info()
                pool_info[pool_name] = {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human", "unknown"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                }
            except Exception as e:
                pool_info[pool_name] = {"error": str(e)}

        return pool_info

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all Redis pools."""
        health_status = {
            "overall_status": "healthy",
            "pools": {},
            "timestamp": datetime.utcnow().isoformat()
        }

        for pool_name, client in self.clients.items():
            try:
                start_time = asyncio.get_event_loop().time()

                # Test basic operations
                await client.ping()
                test_key = f"health_check_{pool_name}_{int(datetime.utcnow().timestamp())}"
                await client.set(test_key, "test", ex=10)
                result = await client.get(test_key)
                await client.delete(test_key)

                duration = (asyncio.get_event_loop().time() - start_time) * 1000

                health_status["pools"][pool_name] = {
                    "status": "healthy",
                    "response_time_ms": duration,
                    "test_result": result == b"test"
                }

            except Exception as e:
                health_status["pools"][pool_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["overall_status"] = "degraded"

        return health_status

    async def close(self):
        """Close all Redis connections."""
        for client in self.clients.values():
            await client.close()

        for pool in self.pools.values():
            await pool.disconnect()

        logger.info("Redis connections closed")

# Factory function for easy initialization
async def create_optimized_redis_manager(
    redis_url: str,
    **kwargs
) -> OptimizedRedisManager:
    """Create and initialize optimized Redis manager."""
    manager = OptimizedRedisManager(redis_url, **kwargs)
    await manager.initialize()
    return manager