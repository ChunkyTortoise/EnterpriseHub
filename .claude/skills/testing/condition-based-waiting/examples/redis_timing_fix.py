"""
Example: Fixing Redis timing issues in tests
Before/After comparison showing proper condition-based waiting
"""

import asyncio
import pytest
import redis.asyncio as redis
from typing import Callable


# ❌ BEFORE: Flaky test with fixed delays
class FlakytRedisTest:
    @pytest.mark.asyncio
    async def test_redis_operations_flaky(self):
        """This test fails intermittently due to Redis startup timing."""
        # Bad: Fixed delay doesn't guarantee Redis is ready
        await asyncio.sleep(2)

        client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # This might fail if Redis isn't ready yet
        await client.set("test_key", "test_value")
        result = await client.get("test_key")

        assert result == "test_value"
        await client.close()


# ✅ AFTER: Robust test with condition waiting
class RobustRedisTest:
    async def wait_for_condition(
        self,
        condition: Callable[[], bool],
        timeout: float = 10.0,
        poll_interval: float = 0.1,
        error_message: str = "Condition not met"
    ) -> None:
        """Wait for a condition to become true within timeout."""
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                if await condition():
                    return
            except Exception:
                pass  # Condition check failed, continue waiting

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(error_message)

            await asyncio.sleep(poll_interval)

    async def ping_redis(self, client: redis.Redis) -> bool:
        """Check if Redis is responsive."""
        try:
            result = await client.ping()
            return result is True
        except Exception:
            return False

    @pytest.fixture
    async def redis_client(self):
        """Redis client with proper readiness waiting."""
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)

        # Wait for Redis to be ready
        await self.wait_for_condition(
            condition=lambda: self.ping_redis(client),
            timeout=30.0,
            error_message="Redis not available within 30 seconds"
        )

        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_redis_operations_robust(self, redis_client):
        """This test is reliable because it waits for actual Redis readiness."""
        # Redis is guaranteed to be ready
        await redis_client.set("test_key", "test_value")
        result = await redis_client.get("test_key")

        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_redis_pubsub_robust(self, redis_client):
        """Test Redis pub/sub with proper synchronization."""
        # Create publisher and subscriber
        pubsub = redis_client.pubsub()
        await pubsub.subscribe("test_channel")

        # Wait for subscription to be active
        await self.wait_for_condition(
            condition=lambda: self._check_subscription_active(pubsub),
            timeout=5.0,
            error_message="Subscription not active"
        )

        # Publish message
        await redis_client.publish("test_channel", "hello")

        # Wait for message to arrive
        message_received = False
        async def check_message():
            nonlocal message_received
            try:
                message = await pubsub.get_message(timeout=0.1)
                if message and message['type'] == 'message':
                    message_received = True
                    return True
            except Exception:
                pass
            return False

        await self.wait_for_condition(
            condition=check_message,
            timeout=5.0,
            error_message="Message not received"
        )

        assert message_received
        await pubsub.close()

    async def _check_subscription_active(self, pubsub) -> bool:
        """Check if pubsub subscription is active."""
        try:
            # Check if we get subscription confirmation
            message = await pubsub.get_message(timeout=0.1)
            return message is not None and message['type'] == 'subscribe'
        except Exception:
            return False


# ✅ Advanced pattern: Redis cluster/sentinel testing
class RedisHighAvailabilityTest:
    """Example of testing Redis in HA configurations."""

    async def wait_for_redis_cluster_ready(
        self,
        nodes: list,
        timeout: float = 30.0
    ) -> None:
        """Wait for Redis cluster to be ready."""
        async def check_cluster():
            try:
                # Check if at least majority of nodes are responsive
                responsive_count = 0
                for node_config in nodes:
                    client = redis.Redis(**node_config, decode_responses=True)
                    try:
                        await client.ping()
                        responsive_count += 1
                    except Exception:
                        pass
                    finally:
                        await client.close()

                # Majority must be responsive for cluster operation
                return responsive_count >= (len(nodes) + 1) // 2
            except Exception:
                return False

        await self.wait_for_condition(
            condition=check_cluster,
            timeout=timeout,
            error_message="Redis cluster not ready"
        )

    @pytest.mark.asyncio
    async def test_redis_failover(self):
        """Test Redis failover scenarios."""
        nodes = [
            {'host': 'localhost', 'port': 6379},
            {'host': 'localhost', 'port': 6380},
            {'host': 'localhost', 'port': 6381}
        ]

        await self.wait_for_redis_cluster_ready(nodes, timeout=60.0)

        # Test operations continue working even during failover
        # (This would integrate with actual failover simulation)
        pass


# ✅ Real-world example: Testing with Docker containers
class RedisDockerTest:
    """Example of testing Redis in Docker containers."""

    async def wait_for_docker_redis(
        self,
        container_name: str,
        port: int = 6379,
        timeout: float = 30.0
    ) -> redis.Redis:
        """Wait for Redis container to be ready and return client."""
        client = redis.Redis(host='localhost', port=port, decode_responses=True)

        async def check_docker_redis():
            try:
                # Also check that container is actually running
                import docker
                docker_client = docker.from_env()
                container = docker_client.containers.get(container_name)
                if container.status != 'running':
                    return False

                # Check Redis responsiveness
                await client.ping()
                return True
            except Exception:
                return False

        await self.wait_for_condition(
            condition=check_docker_redis,
            timeout=timeout,
            error_message=f"Redis container {container_name} not ready"
        )

        return client

    @pytest.mark.asyncio
    async def test_with_docker_redis(self):
        """Test with Redis running in Docker."""
        client = await self.wait_for_docker_redis(
            container_name='test-redis',
            timeout=60.0
        )

        try:
            await client.set("docker_test", "works")
            result = await client.get("docker_test")
            assert result == "works"
        finally:
            await client.close()