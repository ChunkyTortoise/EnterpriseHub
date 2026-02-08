"""
Enterprise Dependency Injection Container for GHL Real Estate AI

A comprehensive, production-ready dependency injection system specifically
designed for real estate applications with Strategy and Repository patterns.

Features:
- Multiple service lifetimes (Singleton, Transient, Scoped, Thread-local)
- Automatic dependency resolution with type hints
- Configuration-driven service registration
- Strategy and Repository pattern integration
- Performance monitoring and optimization
- Comprehensive testing support
- Real estate domain-specific services

Quick Start:
    ```python
    from ghl_real_estate_ai.services.di_container import (
        DIContainer, RealEstateServiceOrchestrator
    )

    # Create container
    container = DIContainer("my_app")

    # Register services
    container.register_singleton(IPropertyRepository, JsonPropertyRepository)

    # Get service
    repo = await container.get_service_async(IPropertyRepository)

    # Or use orchestrator for complete setup
    orchestrator = RealEstateServiceOrchestrator(container)
    await orchestrator.initialize(config)
    ```

For more examples, see examples.py and the documentation.
"""

from .container import (
    CircularDependencyError,
    DIContainer,
    IServiceProvider,
    ResolverContext,
    ServiceConfigurationError,
    ServiceLifetime,
    ServiceMetadata,
    ServiceNotFoundError,
    ServiceState,
)
from .examples import RealEstateServiceComposer, run_development_example, run_testing_example
from .factories import (
    FACTORY_REGISTRY,
    create_configuration_service,
    create_hybrid_repository,
    create_json_repository,
    create_mls_repository,
    create_mock_repository,
    create_performance_monitor,
    create_property_matcher_context,
    create_property_repository,
    create_rag_repository,
    create_repository_property_matcher,
    create_scoring_factory,
    get_factory,
)
from .health_checks import (
    cache_backend_health_check,
    configuration_service_health_check,
    container_health_check,
    data_service_health_check,
    get_health_check,
    repository_health_check,
    scoring_service_health_check,
)
from .pattern_integration import (
    RealEstateServiceOrchestrator,
    RepositoryPatternIntegration,
    StrategyPatternIntegration,
    initialize_real_estate_services,
)
from .performance import (
    OptimizedDIContainer,
    PerformanceMetrics,
    PerformanceMonitor,
    RealEstatePerformanceOptimizer,
    ServiceCache,
)
from .service_registration import (
    EnvironmentConfig,
    EnvironmentVariableProvider,
    IServiceConfigurationProvider,
    JsonConfigurationProvider,
    RealEstateServiceRegistrar,
    ServiceConfig,
    ServiceRegistrar,
    YamlConfigurationProvider,
    scoped,
    service,
    singleton,
    transient,
)
from .testing_support import (
    IntegrationTestHelper,
    MockServiceFactory,
    PerformanceTestHelper,
    TestDIContainer,
    TestScenarioBuilder,
    assert_mock_called,
    assert_service_healthy,
    assert_service_registered,
    scenario_builder,
    test_container,
)

# Version information
__version__ = "1.0.0"
__author__ = "GHL Real Estate AI Team"

# Main exports for easy importing
__all__ = [
    # Core container
    "DIContainer",
    "ServiceLifetime",
    "ServiceState",
    "ServiceMetadata",
    "IServiceProvider",
    # Exceptions
    "CircularDependencyError",
    "ServiceNotFoundError",
    "ServiceConfigurationError",
    # Service registration
    "ServiceRegistrar",
    "YamlConfigurationProvider",
    "JsonConfigurationProvider",
    "EnvironmentVariableProvider",
    "RealEstateServiceRegistrar",
    # Decorators
    "service",
    "singleton",
    "transient",
    "scoped",
    # Pattern integration
    "RealEstateServiceOrchestrator",
    "RepositoryPatternIntegration",
    "StrategyPatternIntegration",
    "initialize_real_estate_services",
    # Performance
    "OptimizedDIContainer",
    "PerformanceMonitor",
    "RealEstatePerformanceOptimizer",
    # Testing
    "TestDIContainer",
    "MockServiceFactory",
    "TestScenarioBuilder",
    "IntegrationTestHelper",
    "PerformanceTestHelper",
    # Health checks
    "repository_health_check",
    "container_health_check",
    "get_health_check",
    # Factories
    "create_property_repository",
    "create_json_repository",
    "create_mls_repository",
    "get_factory",
    # Examples
    "RealEstateServiceComposer",
    "run_development_example",
    "run_testing_example",
    # Fixtures for pytest
    "test_container",
    "scenario_builder",
    # Assertions for testing
    "assert_service_registered",
    "assert_mock_called",
    "assert_service_healthy",
]


def get_version():
    """Get DI container version"""
    return __version__


def create_real_estate_container(name: str = "real_estate", enable_monitoring: bool = True) -> DIContainer:
    """
    Create a DI container pre-configured for real estate applications.

    Args:
        name: Container name
        enable_monitoring: Enable performance monitoring

    Returns:
        Configured DIContainer
    """
    container = DIContainer(name, enable_monitoring)

    # Pre-register common real estate interfaces
    # Note: Implementations would be registered later via configuration

    return container


def create_optimized_real_estate_container(base_container: DIContainer) -> OptimizedDIContainer:
    """
    Create optimized container wrapper for real estate services.

    Args:
        base_container: Base DI container

    Returns:
        OptimizedDIContainer with real estate optimizations
    """
    optimized = OptimizedDIContainer(base_container, enable_caching=True, enable_monitoring=True)

    # Apply real estate optimizations
    RealEstatePerformanceOptimizer.configure_container_for_real_estate(optimized)

    return optimized


# Configuration helpers
DEFAULT_DEVELOPMENT_CONFIG = {
    "repositories": {
        "JsonRepository": {
            "type": "json",
            "config": {"data_paths": ["./data/knowledge_base/austin_market_demo_data.json"], "cache_ttl": 300},
            "enable_caching": True,
        }
    },
    "strategies": {"scoring": {"strategies": {"basic": {"enabled": True}, "enhanced": {"enabled": True}}}},
    "monitoring": {"enabled": True},
}

DEFAULT_PRODUCTION_CONFIG = {
    "repositories": {
        "MLSRepository": {
            "type": "mls",
            "config": {"rate_limit": 10, "timeout": 30, "retry_attempts": 3},
            "enable_caching": True,
            "cache_config": {"backend": "redis", "ttl": 1800},
        }
    },
    "strategies": {"scoring": {"strategies": {"enhanced": {"enabled": True}}}},
    "caching": {"redis": {"enabled": True, "key_prefix": "ghl_prod_cache:"}},
    "monitoring": {"enabled": True, "slow_service_threshold_ms": 50.0},
}

DEFAULT_TESTING_CONFIG = {
    "repositories": {"MockRepository": {"type": "mock", "config": {"mock_data_count": 100, "seed": 12345}}},
    "strategies": {"scoring": {"strategies": {"mock": {"enabled": True}}}},
    "monitoring": {"enabled": False},
}


def get_default_config(environment: str = "development") -> dict:
    """
    Get default configuration for specified environment.

    Args:
        environment: Environment name (development, production, testing)

    Returns:
        Default configuration dictionary
    """
    configs = {
        "development": DEFAULT_DEVELOPMENT_CONFIG,
        "production": DEFAULT_PRODUCTION_CONFIG,
        "testing": DEFAULT_TESTING_CONFIG,
    }

    return configs.get(environment, DEFAULT_DEVELOPMENT_CONFIG).copy()
