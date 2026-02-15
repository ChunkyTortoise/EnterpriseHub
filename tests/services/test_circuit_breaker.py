"""
Test Circuit Breaker Pattern Implementation

Tests circuit breaker functionality for external service calls:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure threshold tracking
- Recovery timeout behavior
- Success threshold for recovery
- Metrics collection
- Config-driven threshold loading
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_real_estate_ai.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitState,
    get_circuit_manager,
)


@pytest.fixture
def circuit_config():
    """Basic circuit breaker configuration for testing"""
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,  # 1 second for faster tests
        success_threshold=2,
        timeout=2.0,
        half_open_max_calls=2,
    )


@pytest.fixture
def circuit_breaker(circuit_config):
    """Create a circuit breaker instance for testing"""
    return CircuitBreaker("test_service", circuit_config)


@pytest.fixture
def circuit_manager():
    """Create a fresh circuit breaker manager for each test"""
    return CircuitBreakerManager()


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions"""

    @pytest.mark.asyncio
    async def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit breaker should start in CLOSED state"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_successful_calls_stay_closed(self, circuit_breaker):
        """Successful calls should keep circuit in CLOSED state"""

        async def successful_call():
            return "success"

        # Execute multiple successful calls
        for _ in range(5):
            result = await circuit_breaker.call(successful_call)
            assert result == "success"

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.stats.successful_requests == 5
        assert circuit_breaker.stats.failed_requests == 0

    @pytest.mark.asyncio
    async def test_failure_threshold_opens_circuit(self, circuit_breaker):
        """Circuit should open after exceeding failure threshold"""

        async def failing_call():
            raise Exception("Service unavailable")

        # Execute calls until failure threshold is reached
        for i in range(circuit_breaker.config.failure_threshold):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_call)

            # State should still be CLOSED until threshold
            if i < circuit_breaker.config.failure_threshold - 1:
                assert circuit_breaker.state == CircuitState.CLOSED

        # After threshold, circuit should be OPEN
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.stats.circuit_opens == 1

    @pytest.mark.asyncio
    async def test_open_circuit_blocks_requests(self, circuit_breaker):
        """OPEN circuit should block requests without calling function"""

        async def should_not_be_called():
            pytest.fail("Function should not be called when circuit is OPEN")

        # Open the circuit with a recent failure time (so recovery timeout hasn't passed)
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time()  # Use time.time() instead of event loop time

        # Attempt call should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError, match="Circuit breaker .* is OPEN"):
            await circuit_breaker.call(should_not_be_called)

    @pytest.mark.asyncio
    async def test_recovery_timeout_transitions_to_half_open(self, circuit_breaker):
        """After recovery timeout, circuit should transition to HALF_OPEN"""

        async def test_call():
            return "success"

        # Open the circuit with a failure time in the past (beyond recovery timeout)
        circuit_breaker.state = CircuitState.OPEN
        circuit_breaker.last_failure_time = time.time() - circuit_breaker.config.recovery_timeout - 1

        # Next call should transition to HALF_OPEN
        result = await circuit_breaker.call(test_call)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    @pytest.mark.asyncio
    async def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Successful calls in HALF_OPEN state should close circuit"""

        async def successful_call():
            return "success"

        # Set circuit to HALF_OPEN
        circuit_breaker.state = CircuitState.HALF_OPEN
        circuit_breaker.success_count = 0

        # Execute successful calls until success threshold
        for _ in range(circuit_breaker.config.success_threshold):
            await circuit_breaker.call(successful_call)

        # Circuit should be CLOSED
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_half_open_failure_reopens_circuit(self, circuit_breaker):
        """Failure in HALF_OPEN state should reopen circuit"""

        async def failing_call():
            raise Exception("Still failing")

        # Set circuit to HALF_OPEN
        circuit_breaker.state = CircuitState.HALF_OPEN

        # First failure should reopen circuit
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_call)

        assert circuit_breaker.state == CircuitState.OPEN


class TestCircuitBreakerMetrics:
    """Test metrics collection and statistics"""

    @pytest.mark.asyncio
    async def test_metrics_track_requests(self, circuit_breaker):
        """Metrics should accurately track all requests"""

        async def alternating_call(should_fail):
            if should_fail:
                raise Exception("Failure")
            return "success"

        # Execute mix of successes and failures
        for i in range(6):
            try:
                await circuit_breaker.call(alternating_call, i % 2 == 0)
            except Exception:
                pass

        stats = circuit_breaker.get_stats()
        assert stats["stats"]["total_requests"] == 6
        assert stats["stats"]["successful_requests"] == 3
        assert stats["stats"]["failed_requests"] == 3

    @pytest.mark.asyncio
    async def test_metrics_track_response_time(self, circuit_breaker):
        """Metrics should track average response time"""

        async def slow_call():
            await asyncio.sleep(0.1)
            return "success"

        await circuit_breaker.call(slow_call)

        stats = circuit_breaker.get_stats()
        assert stats["stats"]["avg_response_time_ms"] > 50  # At least 50ms

    @pytest.mark.asyncio
    async def test_timeout_tracking(self, circuit_breaker):
        """Timeouts should be tracked separately"""

        async def timeout_call():
            await asyncio.sleep(10)  # Longer than timeout
            return "should_not_reach"

        with pytest.raises(asyncio.TimeoutError):
            await circuit_breaker.call(timeout_call)

        stats = circuit_breaker.get_stats()
        assert stats["stats"]["timeout_requests"] == 1
        assert stats["stats"]["failed_requests"] == 1


class TestCircuitBreakerManager:
    """Test circuit breaker manager functionality"""

    def test_create_breaker(self, circuit_manager, circuit_config):
        """Manager should create and store breakers"""
        breaker = circuit_manager.create_breaker("test", circuit_config)

        assert breaker.name == "test"
        assert circuit_manager.get_breaker("test") == breaker

    def test_create_duplicate_breaker_returns_existing(self, circuit_manager, circuit_config):
        """Creating duplicate breaker should return existing instance"""
        breaker1 = circuit_manager.create_breaker("test", circuit_config)
        breaker2 = circuit_manager.create_breaker("test", circuit_config)

        assert breaker1 is breaker2

    @patch("ghl_real_estate_ai.services.circuit_breaker.get_config")
    def test_get_or_create_from_yaml(self, mock_get_config, circuit_manager):
        """Manager should create breaker from YAML config"""
        # Mock config
        mock_config = Mock()
        mock_config.circuit_breaker.enabled = True
        mock_config.circuit_breaker.defaults.failure_threshold = 5
        mock_config.circuit_breaker.defaults.timeout_seconds = 60
        mock_config.circuit_breaker.defaults.success_threshold = 3
        mock_config.circuit_breaker.defaults.half_open_max_calls = 2
        mock_config.circuit_breaker.services = {"ghl": {"failure_threshold": 3, "timeout_seconds": 30}}
        mock_get_config.return_value = mock_config

        breaker = circuit_manager.get_or_create_breaker("ghl")

        assert breaker.name == "ghl"
        assert breaker.config.failure_threshold == 3
        assert breaker.config.timeout == 30.0

    def test_get_all_stats(self, circuit_manager, circuit_config):
        """Manager should return stats for all breakers"""
        circuit_manager.create_breaker("service1", circuit_config)
        circuit_manager.create_breaker("service2", circuit_config)

        all_stats = circuit_manager.get_all_stats()

        assert "service1" in all_stats
        assert "service2" in all_stats
        assert all_stats["service1"]["name"] == "service1"

    def test_get_health_summary(self, circuit_manager, circuit_config):
        """Manager should provide health summary"""
        breaker1 = circuit_manager.create_breaker("service1", circuit_config)
        breaker2 = circuit_manager.create_breaker("service2", circuit_config)

        # Set different states
        breaker1.state = CircuitState.CLOSED
        breaker2.state = CircuitState.OPEN

        summary = circuit_manager.get_health_summary()

        assert summary["total_breakers"] == 2
        assert summary["states"]["CLOSED"] == 1
        assert summary["states"]["OPEN"] == 1

    @pytest.mark.asyncio
    async def test_reset_all(self, circuit_manager, circuit_config):
        """Manager should reset all breakers"""
        breaker1 = circuit_manager.create_breaker("service1", circuit_config)
        breaker2 = circuit_manager.create_breaker("service2", circuit_config)

        # Open both circuits
        breaker1.state = CircuitState.OPEN
        breaker2.state = CircuitState.OPEN

        # Reset all
        circuit_manager.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


class TestCircuitBreakerIntegration:
    """Integration tests with actual service patterns"""

    @pytest.mark.asyncio
    async def test_ghl_service_pattern(self, circuit_manager):
        """Test circuit breaker with GHL service pattern"""

        async def ghl_api_call():
            # Simulate GHL API call
            await asyncio.sleep(0.01)
            return {"status": "success"}

        breaker = circuit_manager.create_breaker(
            "ghl", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0, success_threshold=2, timeout=2.0)
        )

        # Successful calls
        for _ in range(5):
            result = await breaker.call(ghl_api_call)
            assert result["status"] == "success"

        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_fallback_behavior(self):
        """Test circuit breaker with fallback function"""

        async def failing_call():
            raise Exception("Service down")

        async def fallback_response():
            return {"error": "Service unavailable", "fallback": True}

        config = CircuitBreakerConfig(
            failure_threshold=2, recovery_timeout=1.0, success_threshold=2, timeout=2.0, fallback=fallback_response
        )

        breaker = CircuitBreaker("test_with_fallback", config)

        # Fail enough times to open circuit
        for _ in range(config.failure_threshold):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

        # Next call should use fallback
        result = await breaker.call(failing_call)
        assert result["fallback"] is True
        assert breaker.stats.fallback_calls == 1


def test_global_circuit_manager_singleton():
    """Global circuit manager should be singleton"""
    manager1 = get_circuit_manager()
    manager2 = get_circuit_manager()

    assert manager1 is manager2
