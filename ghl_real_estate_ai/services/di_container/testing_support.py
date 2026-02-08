"""
Testing Framework Integration for DI Container

Provides comprehensive testing utilities including mocking, test container setup,
and integration test helpers for the dependency injection system.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Type, Union
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from .container import DIContainer, ServiceLifetime
from .pattern_integration import RealEstateServiceOrchestrator
from .service_registration import ServiceRegistrar, YamlConfigurationProvider

logger = logging.getLogger(__name__)


class TestDIContainer(DIContainer):
    """
    Test-specific DI container with enhanced testing features.

    Provides additional methods for test setup, mocking, and verification.
    """

    def __init__(self, name: str = "test_container"):
        super().__init__(name, enable_monitoring=True)
        self._test_mocks: Dict[str, Mock] = {}
        self._test_overrides: Dict[str, Any] = {}
        self._test_call_counts: Dict[str, int] = {}

    def register_mock(
        self, service_type: Type, mock_instance: Mock = None, name: Optional[str] = None, **mock_kwargs
    ) -> "TestDIContainer":
        """Register a mock service for testing"""
        service_name = name or self._get_service_name(service_type)

        if mock_instance is None:
            # Create appropriate mock based on type
            if asyncio.iscoroutinefunction(getattr(service_type, "__init__", None)):
                mock_instance = AsyncMock(spec=service_type, **mock_kwargs)
            else:
                mock_instance = Mock(spec=service_type, **mock_kwargs)

        self._test_mocks[service_name] = mock_instance

        # Register as singleton
        self.register_instance(service_type, mock_instance, name)

        return self

    def register_test_override(
        self, service_type: Type, instance: Any, name: Optional[str] = None
    ) -> "TestDIContainer":
        """Register a test-specific service override"""
        service_name = name or self._get_service_name(service_type)
        self._test_overrides[service_name] = instance
        self.register_instance(service_type, instance, name)
        return self

    def get_mock(self, service_type: Type, name: Optional[str] = None) -> Mock:
        """Get registered mock for verification"""
        service_name = name or self._get_service_name(service_type)
        if service_name not in self._test_mocks:
            raise ValueError(f"No mock registered for {service_name}")
        return self._test_mocks[service_name]

    def verify_service_calls(self, service_type: Type, expected_calls: int, name: Optional[str] = None) -> bool:
        """Verify number of calls to a service"""
        service_name = name or self._get_service_name(service_type)
        actual_calls = self._test_call_counts.get(service_name, 0)
        return actual_calls == expected_calls

    def reset_test_state(self):
        """Reset all test-specific state"""
        for mock in self._test_mocks.values():
            mock.reset_mock()

        self._test_call_counts.clear()

    async def get_service_async(
        self, service_type: Type, name: Optional[str] = None, scope_id: Optional[str] = None, **kwargs
    ):
        """Override to track service calls in tests"""
        service_name = name or self._get_service_name(service_type)
        self._test_call_counts[service_name] = self._test_call_counts.get(service_name, 0) + 1

        return await super().get_service_async(service_type, name, scope_id, **kwargs)


class MockServiceFactory:
    """Factory for creating standardized mock services"""

    @staticmethod
    def create_mock_repository() -> Mock:
        """Create mock property repository"""
        mock_repo = AsyncMock()

        # Mock repository interface
        mock_repo.name = "MockRepository"
        mock_repo.is_connected = True
        mock_repo.connect.return_value = True
        mock_repo.disconnect.return_value = None

        # Mock query methods
        from ..repositories.interfaces import RepositoryMetadata, RepositoryResult

        mock_result = RepositoryResult(
            data=[
                {
                    "id": "test_prop_1",
                    "address": "123 Test St",
                    "price": 500000,
                    "bedrooms": 3,
                    "bathrooms": 2.5,
                    "sqft": 2100,
                    "neighborhood": "Test Area",
                }
            ],
            total_count=1,
            metadata=RepositoryMetadata(source="MockRepository", query_time_ms=10.0),
            success=True,
        )

        mock_repo.find_properties.return_value = mock_result
        mock_repo.get_property_by_id.return_value = mock_result.data[0]
        mock_repo.count_properties.return_value = 1
        mock_repo.health_check.return_value = {"healthy": True}
        mock_repo.get_supported_filters.return_value = ["price", "bedrooms", "location"]
        mock_repo.get_performance_metrics.return_value = {"avg_query_time": 10.0}

        return mock_repo

    @staticmethod
    def create_mock_data_service() -> Mock:
        """Create mock property data service"""
        mock_service = AsyncMock()

        # Mock data loading methods
        mock_properties = [
            {
                "id": "test_prop_1",
                "address": "123 Test St",
                "price": 500000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2100,
                "neighborhood": "Test Area",
                "amenities": ["garage", "pool"],
                "_source": "mock",
            }
        ]

        mock_service.load_properties_for_strategy_pattern.return_value = mock_properties
        mock_service.get_performance_metrics.return_value = {
            "total_queries": 10,
            "avg_response_time": 50.0,
            "cache_hit_rate": 0.8,
        }

        return mock_service

    @staticmethod
    def create_mock_scoring_factory() -> Mock:
        """Create mock scoring factory"""
        mock_factory = Mock()

        # Mock scorer
        mock_scorer = Mock()
        mock_scorer.score_property.return_value = 85.0

        mock_factory.create_scorer.return_value = mock_scorer
        mock_factory.get_available_strategies.return_value = ["basic", "enhanced", "mock"]

        return mock_factory

    @staticmethod
    def create_mock_cache_backend() -> Mock:
        """Create mock cache backend"""
        mock_cache = Mock()

        # Mock cache operations
        mock_cache.get.return_value = None  # Cache miss by default
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True
        mock_cache.clear.return_value = True
        mock_cache.get_stats.return_value = {"hits": 100, "misses": 25, "hit_rate": 0.8}

        return mock_cache


class TestScenarioBuilder:
    """Builder for creating complex test scenarios"""

    def __init__(self, container: TestDIContainer):
        self.container = container
        self._scenario_config = {}

    def with_repository_scenario(self, scenario: str) -> "TestScenarioBuilder":
        """Configure repository test scenario"""
        scenarios = {
            "empty_results": {"find_properties.return_value.data": [], "count_properties.return_value": 0},
            "connection_failure": {"is_connected": False, "connect.side_effect": ConnectionError("Failed to connect")},
            "slow_responses": {"find_properties.return_value.metadata.query_time_ms": 5000.0},
            "error_results": {"find_properties.side_effect": Exception("Repository error")},
        }

        if scenario in scenarios:
            self._scenario_config["repository"] = scenarios[scenario]

        return self

    def with_caching_scenario(self, scenario: str) -> "TestScenarioBuilder":
        """Configure caching test scenario"""
        scenarios = {
            "cache_hit": {"get.return_value": {"cached": True, "data": "test_data"}},
            "cache_miss": {"get.return_value": None},
            "cache_failure": {
                "get.side_effect": Exception("Cache connection failed"),
                "set.side_effect": Exception("Cache connection failed"),
            },
        }

        if scenario in scenarios:
            self._scenario_config["cache"] = scenarios[scenario]

        return self

    def with_scoring_scenario(self, scenario: str) -> "TestScenarioBuilder":
        """Configure scoring test scenario"""
        scenarios = {
            "high_scores": {"create_scorer.return_value.score_property.return_value": 95.0},
            "low_scores": {"create_scorer.return_value.score_property.return_value": 25.0},
            "scoring_failure": {"create_scorer.side_effect": Exception("Scoring failed")},
        }

        if scenario in scenarios:
            self._scenario_config["scoring"] = scenarios[scenario]

        return self

    def build(self) -> None:
        """Apply scenario configuration to container mocks"""
        for service_type, config in self._scenario_config.items():
            try:
                if service_type == "repository":
                    mock = self.container.get_mock("IPropertyRepository")
                elif service_type == "cache":
                    mock = self.container.get_mock("MemoryCacheBackend")
                elif service_type == "scoring":
                    mock = self.container.get_mock("ScoringFactory")
                else:
                    continue

                self._apply_mock_config(mock, config)

            except ValueError:
                # Mock not registered
                pass

    def _apply_mock_config(self, mock: Mock, config: Dict[str, Any]) -> None:
        """Apply configuration to mock object"""
        for attr_path, value in config.items():
            self._set_nested_mock_attribute(mock, attr_path, value)

    def _set_nested_mock_attribute(self, mock: Mock, attr_path: str, value: Any) -> None:
        """Set nested attribute on mock object"""
        parts = attr_path.split(".")
        current = mock

        for part in parts[:-1]:
            if not hasattr(current, part):
                setattr(current, part, Mock())
            current = getattr(current, part)

        setattr(current, parts[-1], value)


@pytest.fixture
async def test_container():
    """Pytest fixture for test DI container"""
    container = TestDIContainer("test_container")

    # Register common mocks
    container.register_mock("IPropertyRepository", MockServiceFactory.create_mock_repository())
    container.register_mock("PropertyDataService", MockServiceFactory.create_mock_data_service())
    container.register_mock("ScoringFactory", MockServiceFactory.create_mock_scoring_factory())
    container.register_mock("MemoryCacheBackend", MockServiceFactory.create_mock_cache_backend())

    yield container

    await container.dispose_async()


@pytest.fixture
def scenario_builder(test_container):
    """Pytest fixture for test scenario builder"""
    return TestScenarioBuilder(test_container)


class IntegrationTestHelper:
    """Helper for integration tests"""

    @staticmethod
    async def create_test_orchestrator(config: Dict[str, Any] = None) -> RealEstateServiceOrchestrator:
        """Create orchestrator for integration testing"""
        container = TestDIContainer("integration_test")

        config = config or {
            "repositories": {
                "test_repo": {"type": "json", "config": {"data_paths": ["./test_data/sample_properties.json"]}}
            },
            "strategies": {"scoring": {"strategies": {"basic": {"enabled": True}, "enhanced": {"enabled": True}}}},
        }

        orchestrator = RealEstateServiceOrchestrator(container)
        await orchestrator.initialize(config)

        return orchestrator

    @staticmethod
    @asynccontextmanager
    async def property_search_test_context(config: Dict[str, Any] = None):
        """Context manager for property search integration tests"""
        orchestrator = await IntegrationTestHelper.create_test_orchestrator(config)

        try:
            context = await orchestrator.create_property_search_context()
            yield context
        finally:
            await orchestrator.container.dispose_async()


class PerformanceTestHelper:
    """Helper for performance testing of DI container"""

    @staticmethod
    async def measure_service_resolution_time(
        container: DIContainer, service_type: Type, iterations: int = 1000
    ) -> Dict[str, float]:
        """Measure service resolution performance"""
        import time

        times = []

        for _ in range(iterations):
            start = time.perf_counter()
            await container.get_service_async(service_type)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to milliseconds

        return {
            "avg_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "total_time_ms": sum(times),
            "iterations": iterations,
        }

    @staticmethod
    async def stress_test_container(
        container: DIContainer, service_types: List[Type], concurrent_requests: int = 100, duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """Stress test container with concurrent requests"""
        import random
        import time

        start_time = time.time()
        end_time = start_time + duration_seconds
        request_count = 0
        error_count = 0
        results = []

        async def make_request():
            nonlocal request_count, error_count
            try:
                service_type = random.choice(service_types)
                start = time.perf_counter()
                await container.get_service_async(service_type)
                end = time.perf_counter()
                results.append((end - start) * 1000)
                request_count += 1
            except Exception:
                error_count += 1

        # Run concurrent requests
        while time.time() < end_time:
            tasks = [make_request() for _ in range(concurrent_requests)]
            await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "duration_seconds": duration_seconds,
            "total_requests": request_count,
            "error_count": error_count,
            "success_rate": (request_count - error_count) / request_count if request_count > 0 else 0,
            "avg_response_time_ms": sum(results) / len(results) if results else 0,
            "requests_per_second": request_count / duration_seconds,
        }


# Test utilities for common assertions
def assert_service_registered(container: DIContainer, service_type: Type, name: str = None):
    """Assert that a service is properly registered"""
    assert container.is_registered(service_type, name), f"Service {service_type.__name__} not registered"


def assert_mock_called(mock: Mock, method: str, times: int = None):
    """Assert that mock method was called"""
    mock_method = getattr(mock, method)
    if times is not None:
        assert mock_method.call_count == times, f"Expected {times} calls, got {mock_method.call_count}"
    else:
        assert mock_method.called, f"Method {method} was not called"


async def assert_service_healthy(container: DIContainer, service_type: Type, name: str = None):
    """Assert that a service is healthy"""
    service = await container.get_service_async(service_type, name)

    # Try to get health status if available
    if hasattr(service, "health_check"):
        health = (
            await service.health_check()
            if asyncio.iscoroutinefunction(service.health_check)
            else service.health_check()
        )
        assert health.get("healthy", True), f"Service {service_type.__name__} is unhealthy: {health}"


# Export main testing utilities
__all__ = [
    "TestDIContainer",
    "MockServiceFactory",
    "TestScenarioBuilder",
    "IntegrationTestHelper",
    "PerformanceTestHelper",
    "test_container",
    "scenario_builder",
    "assert_service_registered",
    "assert_mock_called",
    "assert_service_healthy",
]
