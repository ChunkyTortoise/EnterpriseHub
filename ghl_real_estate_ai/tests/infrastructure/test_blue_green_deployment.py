"""
Tests for blue-green deployment orchestration.

Validates:
- Zero-downtime deployment workflow
- Automated health checks
- Rollback capabilities
- Performance targets
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.infrastructure.blue_green_deployment import (
    BlueGreenDeploymentOrchestrator,
    DeploymentEnvironment,
    DeploymentStatus,
    EnvironmentConfig,
    TrafficSwitchPlan,
    HealthCheckResult,
)


@pytest.fixture
def blue_config():
    """Blue environment configuration."""
    return EnvironmentConfig(
        name=DeploymentEnvironment.BLUE,
        url="http://blue.test.com",
        database_url="postgresql://blue-db/test",
        redis_url="redis://blue-redis:6379"
    )


@pytest.fixture
def green_config():
    """Green environment configuration."""
    return EnvironmentConfig(
        name=DeploymentEnvironment.GREEN,
        url="http://green.test.com",
        database_url="postgresql://green-db/test",
        redis_url="redis://green-redis:6379"
    )


@pytest.fixture
def orchestrator(blue_config, green_config):
    """Create deployment orchestrator."""
    return BlueGreenDeploymentOrchestrator(
        blue_config=blue_config,
        green_config=green_config
    )


class TestEnvironmentConfig:
    """Test environment configuration."""

    def test_environment_config_initialization(self, blue_config):
        """Test environment config can be initialized."""
        assert blue_config.name == DeploymentEnvironment.BLUE
        assert blue_config.url == "http://blue.test.com"
        assert blue_config.port == 8000
        assert blue_config.health_endpoint == "/health"

    def test_environment_config_custom_thresholds(self):
        """Test custom performance thresholds."""
        config = EnvironmentConfig(
            name=DeploymentEnvironment.GREEN,
            url="http://test.com",
            database_url="postgresql://db",
            redis_url="redis://cache",
            max_response_time_ms=100,
            max_error_rate=0.005
        )

        assert config.max_response_time_ms == 100
        assert config.max_error_rate == 0.005


class TestBlueGreenDeploymentOrchestrator:
    """Test deployment orchestrator."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator can be initialized."""
        assert orchestrator.current_active == DeploymentEnvironment.BLUE
        assert orchestrator.status == DeploymentStatus.PENDING

    def test_get_inactive_environment(self, orchestrator):
        """Test inactive environment detection."""
        # Current active is BLUE
        assert orchestrator.current_active == DeploymentEnvironment.BLUE
        inactive = orchestrator._get_inactive_environment()
        assert inactive == DeploymentEnvironment.GREEN

        # Switch active to GREEN
        orchestrator.current_active = DeploymentEnvironment.GREEN
        inactive = orchestrator._get_inactive_environment()
        assert inactive == DeploymentEnvironment.BLUE

    def test_get_config(self, orchestrator, blue_config, green_config):
        """Test environment config retrieval."""
        blue = orchestrator._get_config(DeploymentEnvironment.BLUE)
        assert blue.name == DeploymentEnvironment.BLUE
        assert blue.url == blue_config.url

        green = orchestrator._get_config(DeploymentEnvironment.GREEN)
        assert green.name == DeploymentEnvironment.GREEN
        assert green.url == green_config.url


class TestHealthChecks:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, orchestrator, green_config):
        """Test successful health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await orchestrator._validate_health(green_config)

            assert result is True
            assert orchestrator.metrics.health_checks_passed == 1
            assert orchestrator.metrics.health_checks_failed == 0
            assert len(orchestrator._health_check_history) == 1

    @pytest.mark.asyncio
    async def test_health_check_failure(self, orchestrator, green_config):
        """Test failed health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            # Mock failed responses
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            result = await orchestrator._validate_health(green_config, max_attempts=2)

            assert result is False
            assert orchestrator.metrics.health_checks_passed == 0
            assert orchestrator.metrics.health_checks_failed == 1

    @pytest.mark.asyncio
    async def test_health_check_timeout(self, orchestrator, green_config):
        """Test health check with timeout."""
        import httpx

        with patch.object(orchestrator._client, 'get') as mock_get:
            # Mock timeout exception
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            result = await orchestrator._validate_health(green_config, max_attempts=1)

            assert result is False
            assert orchestrator.metrics.health_checks_failed == 1

    @pytest.mark.asyncio
    async def test_health_check_performance_target(self, orchestrator, green_config):
        """Test health check meets <10s performance target."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            import time
            start = time.time()
            await orchestrator._validate_health(green_config)
            duration = (time.time() - start) * 1000

            # Should complete quickly (mocked network calls)
            assert duration < 1000  # 1 second for mocked calls
            assert orchestrator.metrics.health_check_duration_ms < 10000  # 10s target


class TestSmokeTests:
    """Test smoke test functionality."""

    @pytest.mark.asyncio
    async def test_smoke_tests_success(self, orchestrator, green_config):
        """Test successful smoke tests."""
        with patch.object(orchestrator._client, 'get') as mock_get, \
             patch.object(orchestrator._client, 'post') as mock_post:

            # Mock successful responses
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            mock_post.return_value = mock_response

            result = await orchestrator._run_smoke_tests(green_config)

            assert result is True
            assert orchestrator.metrics.smoke_tests_passed > 0

    @pytest.mark.asyncio
    async def test_smoke_tests_partial_failure(self, orchestrator, green_config):
        """Test smoke tests with some failures."""
        with patch.object(orchestrator._client, 'get') as mock_get, \
             patch.object(orchestrator._client, 'post') as mock_post:

            # Mock mixed responses
            mock_success = AsyncMock()
            mock_success.status_code = 200

            mock_failure = AsyncMock()
            mock_failure.status_code = 500

            mock_get.side_effect = [mock_success, mock_failure, mock_success]
            mock_post.return_value = mock_failure

            result = await orchestrator._run_smoke_tests(green_config)

            # Should fail if success rate below threshold
            assert orchestrator.metrics.smoke_tests_failed > 0


class TestTrafficSwitching:
    """Test traffic switching functionality."""

    @pytest.mark.asyncio
    async def test_gradual_traffic_switching(self, orchestrator, blue_config, green_config):
        """Test gradual traffic migration."""
        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = True

            result = await orchestrator._switch_traffic(blue_config, green_config)

            assert result is True
            assert orchestrator.metrics.traffic_switch_duration_ms > 0

    @pytest.mark.asyncio
    async def test_traffic_switching_performance_target(self, orchestrator, blue_config, green_config):
        """Test traffic switching meets <30s target."""
        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = True

            import time
            start = time.time()
            await orchestrator._switch_traffic(blue_config, green_config)
            duration = (time.time() - start) * 1000

            # Should complete quickly (mocked operations)
            assert duration < 30000  # 30s target

    @pytest.mark.asyncio
    async def test_immediate_traffic_switch(self, orchestrator, blue_config, green_config):
        """Test immediate traffic switching."""
        orchestrator.traffic_plan.gradual_migration = False

        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = True

            result = await orchestrator._switch_traffic(blue_config, green_config)

            assert result is True


class TestRollback:
    """Test rollback functionality."""

    @pytest.mark.asyncio
    async def test_rollback_success(self, orchestrator, blue_config, green_config):
        """Test successful rollback."""
        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = True

            await orchestrator._rollback(blue_config, green_config, "Test rollback")

            assert orchestrator.metrics.rollback_triggered is True
            assert orchestrator.metrics.rollback_reason == "Test rollback"
            assert orchestrator.status == DeploymentStatus.FAILED

    @pytest.mark.asyncio
    async def test_rollback_performance_target(self, orchestrator, blue_config, green_config):
        """Test rollback meets <60s detection-to-rollback target."""
        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = True

            import time
            start = time.time()
            await orchestrator._rollback(blue_config, green_config, "Performance test")
            duration = (time.time() - start) * 1000

            # Should complete quickly (mocked operations)
            assert duration < 60000  # 60s target

    @pytest.mark.asyncio
    async def test_rollback_health_check_failure(self, orchestrator, blue_config, green_config):
        """Test rollback with failed health check."""
        with patch.object(orchestrator, '_validate_health') as mock_health:
            mock_health.return_value = False

            await orchestrator._rollback(blue_config, green_config, "Health check failed")

            assert orchestrator.status == DeploymentStatus.FAILED


class TestFullDeployment:
    """Test complete deployment workflow."""

    @pytest.mark.asyncio
    async def test_successful_deployment(self, orchestrator):
        """Test successful end-to-end deployment."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_coordinate_migration') as mock_migration, \
             patch.object(orchestrator, '_switch_traffic') as mock_traffic, \
             patch.object(orchestrator, '_final_validation') as mock_validation:

            # Mock all steps as successful
            mock_health.return_value = True
            mock_smoke.return_value = True
            mock_migration.return_value = True
            mock_traffic.return_value = True
            mock_validation.return_value = True

            result = await orchestrator.deploy()

            assert result is True
            assert orchestrator.status == DeploymentStatus.COMPLETED
            assert orchestrator.current_active == DeploymentEnvironment.GREEN

    @pytest.mark.asyncio
    async def test_deployment_health_check_failure(self, orchestrator):
        """Test deployment with health check failure."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_rollback') as mock_rollback:

            mock_health.return_value = False
            mock_rollback.return_value = None

            result = await orchestrator.deploy()

            assert result is False
            assert mock_rollback.called

    @pytest.mark.asyncio
    async def test_deployment_smoke_test_failure(self, orchestrator):
        """Test deployment with smoke test failure."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_rollback') as mock_rollback:

            mock_health.return_value = True
            mock_smoke.return_value = False
            mock_rollback.return_value = None

            result = await orchestrator.deploy()

            assert result is False
            assert mock_rollback.called

    @pytest.mark.asyncio
    async def test_deployment_skip_options(self, orchestrator):
        """Test deployment with skip options."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_coordinate_migration') as mock_migration, \
             patch.object(orchestrator, '_switch_traffic') as mock_traffic, \
             patch.object(orchestrator, '_final_validation') as mock_validation:

            mock_health.return_value = True
            mock_traffic.return_value = True
            mock_validation.return_value = True

            result = await orchestrator.deploy(
                skip_migration=True,
                skip_smoke_tests=True
            )

            assert result is True
            assert not mock_smoke.called
            assert not mock_migration.called

    @pytest.mark.asyncio
    async def test_deployment_metrics(self, orchestrator):
        """Test deployment metrics collection."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_coordinate_migration') as mock_migration, \
             patch.object(orchestrator, '_switch_traffic') as mock_traffic, \
             patch.object(orchestrator, '_final_validation') as mock_validation:

            mock_health.return_value = True
            mock_smoke.return_value = True
            mock_migration.return_value = True
            mock_traffic.return_value = True
            mock_validation.return_value = True

            await orchestrator.deploy()

            assert orchestrator.metrics.health_check_duration_ms >= 0
            assert orchestrator.metrics.smoke_test_duration_ms >= 0
            assert orchestrator.metrics.migration_duration_ms >= 0
            assert orchestrator.metrics.traffic_switch_duration_ms >= 0
            assert orchestrator.metrics.total_duration_ms >= 0

    @pytest.mark.asyncio
    async def test_deployment_status_tracking(self, orchestrator):
        """Test deployment status is tracked correctly."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_coordinate_migration') as mock_migration, \
             patch.object(orchestrator, '_switch_traffic') as mock_traffic, \
             patch.object(orchestrator, '_final_validation') as mock_validation:

            mock_health.return_value = True
            mock_smoke.return_value = True
            mock_migration.return_value = True
            mock_traffic.return_value = True
            mock_validation.return_value = True

            # Track status changes during deployment
            status_history = []

            async def track_health(*args, **kwargs):
                status_history.append(orchestrator.status)
                return True

            mock_health.side_effect = track_health

            await orchestrator.deploy()

            # Status should progress through phases
            assert DeploymentStatus.HEALTH_CHECK in status_history


class TestDeploymentStatus:
    """Test deployment status reporting."""

    @pytest.mark.asyncio
    async def test_get_deployment_status(self, orchestrator):
        """Test deployment status retrieval."""
        status = await orchestrator.get_deployment_status()

        assert "status" in status
        assert "current_active" in status
        assert "metrics" in status
        assert "health_check_history" in status

    @pytest.mark.asyncio
    async def test_deployment_status_after_deployment(self, orchestrator):
        """Test status after deployment."""
        with patch.object(orchestrator, '_validate_health') as mock_health, \
             patch.object(orchestrator, '_run_smoke_tests') as mock_smoke, \
             patch.object(orchestrator, '_coordinate_migration') as mock_migration, \
             patch.object(orchestrator, '_switch_traffic') as mock_traffic, \
             patch.object(orchestrator, '_final_validation') as mock_validation:

            mock_health.return_value = True
            mock_smoke.return_value = True
            mock_migration.return_value = True
            mock_traffic.return_value = True
            mock_validation.return_value = True

            await orchestrator.deploy()

            status = await orchestrator.get_deployment_status()

            assert status["status"] == DeploymentStatus.COMPLETED.value
            assert status["current_active"] == DeploymentEnvironment.GREEN.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
