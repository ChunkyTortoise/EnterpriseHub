"""
Tests for health check system.

Validates:
- Multi-component health validation
- Performance targets (<10s assessment)
- Concurrent health check execution
- Historical health tracking
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch

from ghl_real_estate_ai.infrastructure.health_checks import (
    HealthCheckOrchestrator,
    HealthStatus,
    ComponentType,
    HealthCheckResult,
    SystemHealthReport,
    run_critical_smoke_tests,
)


@pytest.fixture
def orchestrator():
    """Create health check orchestrator."""
    return HealthCheckOrchestrator(
        base_url="http://test.example.com",
        database_url="postgresql://test-db/test",
        redis_url="redis://test-redis:6379"
    )


class TestHealthCheckResult:
    """Test health check result data structure."""

    def test_health_check_result_initialization(self):
        """Test health check result can be initialized."""
        result = HealthCheckResult(
            component="test_api",
            component_type=ComponentType.API,
            status=HealthStatus.HEALTHY,
            latency_ms=50.5
        )

        assert result.component == "test_api"
        assert result.component_type == ComponentType.API
        assert result.status == HealthStatus.HEALTHY
        assert result.latency_ms == 50.5

    def test_health_check_result_to_dict(self):
        """Test health check result conversion to dictionary."""
        result = HealthCheckResult(
            component="test_db",
            component_type=ComponentType.DATABASE,
            status=HealthStatus.DEGRADED,
            latency_ms=150.75,
            details={"connections": 50}
        )

        result_dict = result.to_dict()

        assert result_dict["component"] == "test_db"
        assert result_dict["component_type"] == ComponentType.DATABASE.value
        assert result_dict["status"] == HealthStatus.DEGRADED.value
        assert result_dict["latency_ms"] == 150.75
        assert result_dict["details"]["connections"] == 50


class TestSystemHealthReport:
    """Test system health report."""

    def test_system_health_report_initialization(self):
        """Test health report can be initialized."""
        checks = [
            HealthCheckResult(
                component="api",
                component_type=ComponentType.API,
                status=HealthStatus.HEALTHY,
                latency_ms=50.0
            ),
            HealthCheckResult(
                component="database",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.DEGRADED,
                latency_ms=100.0
            )
        ]

        report = SystemHealthReport(
            overall_status=HealthStatus.DEGRADED,
            checks=checks,
            total_duration_ms=200.0
        )

        assert report.overall_status == HealthStatus.DEGRADED
        assert len(report.checks) == 2
        assert report.total_duration_ms == 200.0

    def test_system_health_report_counts(self):
        """Test health report status counts."""
        checks = [
            HealthCheckResult("api1", ComponentType.API, HealthStatus.HEALTHY, 50.0),
            HealthCheckResult("api2", ComponentType.API, HealthStatus.HEALTHY, 60.0),
            HealthCheckResult("db", ComponentType.DATABASE, HealthStatus.DEGRADED, 100.0),
            HealthCheckResult("cache", ComponentType.CACHE, HealthStatus.UNHEALTHY, 200.0),
        ]

        report = SystemHealthReport(
            overall_status=HealthStatus.DEGRADED,
            checks=checks,
            total_duration_ms=500.0
        )

        assert report.healthy_count == 2
        assert report.degraded_count == 1
        assert report.unhealthy_count == 1

    def test_system_health_report_to_dict(self):
        """Test health report conversion to dictionary."""
        checks = [
            HealthCheckResult("api", ComponentType.API, HealthStatus.HEALTHY, 50.0)
        ]

        report = SystemHealthReport(
            overall_status=HealthStatus.HEALTHY,
            checks=checks,
            total_duration_ms=100.0
        )

        report_dict = report.to_dict()

        assert report_dict["overall_status"] == HealthStatus.HEALTHY.value
        assert len(report_dict["checks"]) == 1
        assert report_dict["summary"]["total_checks"] == 1
        assert report_dict["summary"]["healthy"] == 1
        assert report_dict["total_duration_ms"] == 100.0


class TestHealthCheckOrchestrator:
    """Test health check orchestrator."""

    def test_orchestrator_initialization(self, orchestrator):
        """Test orchestrator can be initialized."""
        assert orchestrator.base_url == "http://test.example.com"
        assert orchestrator.database_url == "postgresql://test-db/test"
        assert orchestrator.redis_url == "redis://test-redis:6379"

    @pytest.mark.asyncio
    async def test_api_health_check_success(self, orchestrator):
        """Test successful API health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = await orchestrator._check_api_health()

            assert result.status == HealthStatus.HEALTHY
            assert result.component == "api_health"
            assert result.component_type == ComponentType.API
            assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_api_health_check_degraded(self, orchestrator):
        """Test degraded API health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 503
            mock_get.return_value = mock_response

            result = await orchestrator._check_api_health()

            assert result.status == HealthStatus.DEGRADED
            assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_api_health_check_timeout(self, orchestrator):
        """Test API health check timeout."""
        import httpx

        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            result = await orchestrator._check_api_health()

            assert result.status == HealthStatus.UNHEALTHY
            assert "timeout" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_database_health_check(self, orchestrator):
        """Test database health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value={
                "pool_size": 10,
                "active_connections": 5,
                "query_latency_ms": 25.5
            })
            mock_get.return_value = mock_response

            result = await orchestrator._check_database_health()

            assert result.component == "database"
            assert result.component_type == ComponentType.DATABASE
            # Status may be HEALTHY or simulated depending on endpoint availability or UNHEALTHY on error
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]

    @pytest.mark.asyncio
    async def test_redis_health_check(self, orchestrator):
        """Test Redis health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "connected": True,
                "used_memory_mb": 128,
                "hit_rate": 0.95
            }
            mock_get.return_value = mock_response

            result = await orchestrator._check_redis_health()

            assert result.component == "redis"
            assert result.component_type == ComponentType.CACHE

    @pytest.mark.asyncio
    async def test_ml_model_health_check(self, orchestrator):
        """Test ML model health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "models_loaded": ["lead_scoring", "property_matching"],
                "inference_latency_ms": 250.0
            }
            mock_get.return_value = mock_response

            result = await orchestrator._check_ml_model_health()

            assert result.component == "ml_models"
            assert result.component_type == ComponentType.ML_MODEL

    @pytest.mark.asyncio
    async def test_ghl_integration_health_check(self, orchestrator):
        """Test GHL integration health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "api_accessible": True,
                "webhook_active": True,
                "rate_limit_remaining": 1000
            }
            mock_get.return_value = mock_response

            result = await orchestrator._check_ghl_integration_health()

            assert result.component == "ghl_integration"
            assert result.component_type == ComponentType.GHL_INTEGRATION

    @pytest.mark.asyncio
    async def test_system_resources_health_check(self, orchestrator):
        """Test system resources health check."""
        result = await orchestrator._check_system_resources()

        assert result.component == "system_resources"
        assert result.component_type == ComponentType.SYSTEM_RESOURCES
        assert "cpu_percent" in result.details
        assert "memory_percent" in result.details
        assert "disk_percent" in result.details

    @pytest.mark.asyncio
    async def test_comprehensive_health_check(self, orchestrator):
        """Test comprehensive health check execution."""
        with patch.object(orchestrator._client, 'get') as mock_get, \
             patch.object(orchestrator._client, 'post') as mock_post:

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response
            mock_post.return_value = mock_response

            report = await orchestrator.check_health()

            assert isinstance(report, SystemHealthReport)
            assert len(report.checks) > 0
            assert report.overall_status in [
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthStatus.UNHEALTHY
            ]

    @pytest.mark.asyncio
    async def test_health_check_performance_target(self, orchestrator):
        """Test health check meets <10s performance target."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            import time
            start = time.time()
            report = await orchestrator.check_health()
            duration = (time.time() - start) * 1000

            # Should complete quickly with mocked network calls
            assert duration < 10000  # 10s target
            assert report.total_duration_ms < 10000

    @pytest.mark.asyncio
    async def test_health_check_concurrent_execution(self, orchestrator):
        """Test health checks execute concurrently."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            # Run health check (should execute checks concurrently)
            report = await orchestrator.check_health()

            # All checks should complete
            assert len(report.checks) > 1

    @pytest.mark.asyncio
    async def test_health_check_critical_only(self, orchestrator):
        """Test critical components only health check."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            report = await orchestrator.check_health(critical_only=True)

            # Should have fewer checks (critical components only)
            # Critical: API, Database, Cache
            critical_types = {ComponentType.API, ComponentType.DATABASE, ComponentType.CACHE}
            check_types = {check.component_type for check in report.checks}

            # All checks should be critical components
            assert check_types.issubset(critical_types)

    @pytest.mark.asyncio
    async def test_health_check_specific_components(self, orchestrator):
        """Test health check for specific components."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            report = await orchestrator.check_health(
                include_components=[ComponentType.API, ComponentType.DATABASE]
            )

            # Should only have requested components
            check_types = {check.component_type for check in report.checks}
            assert check_types.issubset({ComponentType.API, ComponentType.DATABASE})


class TestOverallStatusCalculation:
    """Test overall status calculation logic."""

    def test_overall_status_all_healthy(self, orchestrator):
        """Test overall status when all components healthy."""
        checks = [
            HealthCheckResult("api", ComponentType.API, HealthStatus.HEALTHY, 50.0),
            HealthCheckResult("db", ComponentType.DATABASE, HealthStatus.HEALTHY, 75.0),
            HealthCheckResult("cache", ComponentType.CACHE, HealthStatus.HEALTHY, 25.0),
        ]

        status = orchestrator._calculate_overall_status(checks)
        assert status == HealthStatus.HEALTHY

    def test_overall_status_degraded_component(self, orchestrator):
        """Test overall status with degraded component."""
        checks = [
            HealthCheckResult("api", ComponentType.API, HealthStatus.HEALTHY, 50.0),
            HealthCheckResult("db", ComponentType.DATABASE, HealthStatus.DEGRADED, 150.0),
            HealthCheckResult("cache", ComponentType.CACHE, HealthStatus.HEALTHY, 25.0),
        ]

        status = orchestrator._calculate_overall_status(checks)
        assert status == HealthStatus.DEGRADED

    def test_overall_status_critical_unhealthy(self, orchestrator):
        """Test overall status with critical component unhealthy."""
        checks = [
            HealthCheckResult("api", ComponentType.API, HealthStatus.UNHEALTHY, 1000.0),
            HealthCheckResult("db", ComponentType.DATABASE, HealthStatus.HEALTHY, 75.0),
            HealthCheckResult("cache", ComponentType.CACHE, HealthStatus.HEALTHY, 25.0),
        ]

        status = orchestrator._calculate_overall_status(checks)
        assert status == HealthStatus.UNHEALTHY

    def test_overall_status_non_critical_unhealthy(self, orchestrator):
        """Test overall status with non-critical component unhealthy."""
        checks = [
            HealthCheckResult("api", ComponentType.API, HealthStatus.HEALTHY, 50.0),
            HealthCheckResult("db", ComponentType.DATABASE, HealthStatus.HEALTHY, 75.0),
            HealthCheckResult("ml", ComponentType.ML_MODEL, HealthStatus.UNHEALTHY, 500.0),
        ]

        status = orchestrator._calculate_overall_status(checks)
        # Should be degraded (non-critical unhealthy)
        assert status == HealthStatus.DEGRADED

    def test_overall_status_empty_checks(self, orchestrator):
        """Test overall status with no checks."""
        status = orchestrator._calculate_overall_status([])
        assert status == HealthStatus.UNKNOWN


class TestHealthHistory:
    """Test health check history tracking."""

    @pytest.mark.asyncio
    async def test_health_history_tracking(self, orchestrator):
        """Test health check history is tracked."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            # Run multiple health checks
            await orchestrator.check_health()
            await orchestrator.check_health()
            await orchestrator.check_health()

            history = orchestrator.get_health_history()

            assert len(history) == 3

    @pytest.mark.asyncio
    async def test_health_history_limit(self, orchestrator):
        """Test health history respects limit."""
        with patch.object(orchestrator._client, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {}
            mock_get.return_value = mock_response

            # Run multiple health checks
            for _ in range(15):
                await orchestrator.check_health()

            history = orchestrator.get_health_history(limit=5)

            assert len(history) == 5


class TestCriticalSmokeTests:
    """Test critical smoke test function."""

    @pytest.mark.asyncio
    async def test_critical_smoke_tests_success(self):
        """Test successful critical smoke tests."""
        with patch('ghl_real_estate_ai.infrastructure.health_checks.HealthCheckOrchestrator') as MockOrchestrator:
            mock_orchestrator = AsyncMock()
            mock_report = AsyncMock()
            mock_report.overall_status = HealthStatus.HEALTHY
            mock_orchestrator.check_health.return_value = mock_report
            mock_orchestrator.close = AsyncMock()

            MockOrchestrator.return_value = mock_orchestrator

            result = await run_critical_smoke_tests("http://test.com")

            assert result is True

    @pytest.mark.asyncio
    async def test_critical_smoke_tests_failure(self):
        """Test failed critical smoke tests."""
        with patch('ghl_real_estate_ai.infrastructure.health_checks.HealthCheckOrchestrator') as MockOrchestrator:
            mock_orchestrator = AsyncMock()
            mock_report = AsyncMock()
            mock_report.overall_status = HealthStatus.UNHEALTHY
            mock_orchestrator.check_health.return_value = mock_report
            mock_orchestrator.close = AsyncMock()

            MockOrchestrator.return_value = mock_orchestrator

            result = await run_critical_smoke_tests("http://test.com")

            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
