# Enterprise Dependency Injection Container for GHL Real Estate AI

A comprehensive, production-ready dependency injection system specifically designed for real estate applications with Strategy and Repository patterns.

## Features

- **Multiple Service Lifetimes**: Singleton, Transient, Scoped, and Thread-local
- **Automatic Dependency Resolution**: Type hint-based dependency injection
- **Configuration-Driven Setup**: YAML/JSON configuration support
- **Pattern Integration**: Seamless Strategy and Repository pattern integration
- **Performance Monitoring**: Built-in performance tracking and optimization
- **Testing Support**: Comprehensive mocking and testing utilities
- **Health Checks**: Automatic service health monitoring
- **Real Estate Domain**: Pre-configured for real estate services

## Quick Start

### Basic Container Usage

```python
import asyncio
from ghl_real_estate_ai.services.di_container import DIContainer

async def main():
    # Create container
    container = DIContainer("my_app")

    # Register services
    container.register_singleton(IPropertyRepository, JsonPropertyRepository)
    container.register_transient(PropertyQueryBuilder)

    # Get services
    repo = await container.get_service_async(IPropertyRepository)
    builder = await container.get_service_async(PropertyQueryBuilder)

    await container.dispose_async()

asyncio.run(main())
```

### Real Estate Orchestrator

```python
from ghl_real_estate_ai.services.di_container import (
    RealEstateServiceOrchestrator, DIContainer
)

async def setup_real_estate_services():
    container = DIContainer("real_estate")
    orchestrator = RealEstateServiceOrchestrator(container)

    config = {
        'repositories': {
            'PropertyRepository': {
                'type': 'json',
                'config': {
                    'data_paths': ['./data/properties.json']
                }
            }
        },
        'strategies': {
            'scoring': {
                'strategies': {
                    'enhanced': {'enabled': True}
                }
            }
        }
    }

    await orchestrator.initialize(config)

    # Create property search context
    context = await orchestrator.create_property_search_context()

    return context
```

## Configuration

### YAML Configuration

Create `config/services.yml`:

```yaml
base:
  variables:
    data_dir: "${DATA_DIR:./data/knowledge_base}"
    redis_url: "${REDIS_URL:redis://localhost:6379}"

  services:
    - name: "PropertyRepository"
      service_type: "ghl_real_estate_ai.services.repositories.interfaces.IPropertyRepository"
      factory: "ghl_real_estate_ai.services.di_container.factories.create_json_repository"
      lifetime: "singleton"
      configuration:
        data_paths:
          - "${data_dir}/austin_market_demo_data.json"

environments:
  development:
    variables:
      log_level: "DEBUG"

  production:
    variables:
      log_level: "WARNING"
      cache_ttl: 1800
```

### Load from Configuration

```python
from ghl_real_estate_ai.services.di_container import (
    ServiceRegistrar, YamlConfigurationProvider
)

container = DIContainer("config_app")
registrar = ServiceRegistrar(container)

config_provider = YamlConfigurationProvider("config/services.yml")
await registrar.register_from_config(config_provider, "development")
```

## Service Registration Patterns

### Manual Registration

```python
# Singleton
container.register_singleton(IPropertyRepository, JsonPropertyRepository)

# Transient
container.register_transient(PropertyQueryBuilder)

# Scoped (per request/operation)
container.register_scoped(PropertyMatcherContext)

# Factory function
container.register_singleton(
    IPropertyRepository,
    factory=lambda factory: create_custom_repository(factory),
    name="CustomRepository"
)

# Instance registration
repo_instance = JsonPropertyRepository(config)
container.register_instance(IPropertyRepository, repo_instance)
```

### Decorator-Based Registration

```python
from ghl_real_estate_ai.services.di_container import singleton, transient

@singleton(name="PropertyService", tags=["repository", "primary"])
class PropertyService:
    def __init__(self, repo: IPropertyRepository):
        self.repo = repo

@transient(tags=["query", "builder"])
class PropertyQueryBuilder:
    def __init__(self, config: ConfigurationService):
        self.config = config
```

## Performance Optimization

### Optimized Container

```python
from ghl_real_estate_ai.services.di_container import (
    OptimizedDIContainer, RealEstatePerformanceOptimizer
)

# Create optimized container
optimized = OptimizedDIContainer(
    base_container,
    enable_caching=True,
    enable_monitoring=True
)

# Configure for real estate
RealEstatePerformanceOptimizer.configure_container_for_real_estate(optimized)

# Warm up services
await optimized.warm_up_services()

# Get performance report
report = optimized.get_performance_report()
```

### Performance Monitoring

```python
# Get metrics for specific service
metrics = monitor.get_metrics("PropertyRepository")

# Get slow services
slow_services = monitor.get_slow_services(threshold_ms=100.0)

# Get frequently used services
frequent = monitor.get_frequently_used_services(min_usage=50)
```

## Testing Support

### Test Container

```python
import pytest
from ghl_real_estate_ai.services.di_container import TestDIContainer, MockServiceFactory

@pytest.fixture
async def test_container():
    container = TestDIContainer("test")

    # Register mocks
    container.register_mock(
        IPropertyRepository,
        MockServiceFactory.create_mock_repository()
    )

    yield container
    await container.dispose_async()

async def test_property_search(test_container):
    repo = await test_container.get_service_async(IPropertyRepository)

    # Perform test
    result = await repo.find_properties(PropertyQuery())

    # Verify mock calls
    mock = test_container.get_mock(IPropertyRepository)
    assert mock.find_properties.called
```

### Test Scenarios

```python
from ghl_real_estate_ai.services.di_container import TestScenarioBuilder

def test_repository_failure(test_container, scenario_builder):
    # Configure failure scenario
    scenario_builder.with_repository_scenario('connection_failure').build()

    # Test error handling
    repo = await test_container.get_service_async(IPropertyRepository)
    with pytest.raises(ConnectionError):
        await repo.connect()
```

### Integration Testing

```python
from ghl_real_estate_ai.services.di_container import IntegrationTestHelper

async def test_property_search_integration():
    async with IntegrationTestHelper.property_search_test_context() as context:
        # Test with real services
        repo = context['repository']
        matcher = context['repository_matcher']

        # Perform integration test
        properties = await repo.find_properties(PropertyQuery())
        scores = await matcher.score_properties_with_repository(preferences)

        assert len(properties) > 0
        assert len(scores) > 0
```

## Health Checks

### Built-in Health Checks

```python
# Container health check
health = await container_health_check(container)
print(f"Container healthy: {health['healthy']}")

# Repository health check
repo_health = await repository_health_check(repository)
print(f"Repository healthy: {repo_health['healthy']}")

# Get comprehensive health status
orchestrator = RealEstateServiceOrchestrator(container)
health_status = await orchestrator.get_health_status()
```

### Custom Health Checks

```python
async def custom_health_check(service_instance):
    """Custom health check function"""
    try:
        # Perform health check logic
        await service_instance.ping()
        return {'healthy': True, 'message': 'Service responding'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}

# Register service with health check
container.register_singleton(
    MyService,
    health_check=custom_health_check
)
```

## Real Estate Domain Integration

### Property Search Workflow

```python
async def property_search_example():
    orchestrator = RealEstateServiceOrchestrator(container)
    await orchestrator.initialize(config)

    # Create search context
    async with orchestrator.container.create_scope_async() as scope:
        context = await orchestrator.create_property_search_context(scope)

        # Define search criteria
        lead_preferences = {
            'budget': 650000,
            'location': 'downtown',
            'bedrooms': 3,
            'must_haves': ['garage', 'yard']
        }

        # Execute search with injected services
        data_service = context['data_service']
        repository_matcher = context['repository_matcher']

        # Load and score properties
        properties = await data_service.load_properties_for_strategy_pattern(lead_preferences)
        scored_properties = await repository_matcher.score_properties_with_repository(
            lead_preferences=lead_preferences,
            max_properties=20
        )

        return scored_properties[:5]  # Top 5 matches
```

### Strategy Pattern Integration

```python
# The DI container automatically integrates with existing Strategy Pattern
from ghl_real_estate_ai.services.repositories.strategy_integration import (
    enhanced_generate_property_matches
)

# Enhanced function uses DI container internally
lead_context = {'extracted_preferences': preferences}
matches = await enhanced_generate_property_matches(
    lead_context,
    data_sources_config={'type': 'demo'}
)
```

## Environment Configurations

### Development Environment

```python
from ghl_real_estate_ai.services.di_container import get_default_config

config = get_default_config('development')
# Uses JSON repositories, memory caching, debug logging
```

### Production Environment

```python
config = get_default_config('production')
# Uses MLS repositories, Redis caching, optimized performance
```

### Testing Environment

```python
config = get_default_config('testing')
# Uses mock repositories, no caching, detailed logging
```

## Examples and Patterns

### Complete Development Setup

```python
from ghl_real_estate_ai.services.di_container import RealEstateServiceComposer

async def main():
    composer = RealEstateServiceComposer()

    # Create development environment
    env = await composer.create_development_environment()

    # Run property search workflow
    results = await composer.demonstrate_property_search_workflow(env)

    # Monitor performance
    perf = await composer.demonstrate_performance_monitoring(env)

    print(f"Found {len(results['top_matches'])} property matches")
    print(f"Average resolution time: {perf['performance_report']['avg_time_ms']:.2f}ms")

    await composer.cleanup()

asyncio.run(main())
```

### Running Examples

```bash
# Run development example
python -m ghl_real_estate_ai.services.di_container.examples

# Or run specific examples
from ghl_real_estate_ai.services.di_container.examples import (
    run_development_example,
    run_testing_example
)

dev_results = await run_development_example()
test_results = await run_testing_example()
```

## Best Practices

### Service Design

1. **Use Interfaces**: Always register services by their interface/abstract type
2. **Minimize Dependencies**: Keep constructor dependencies focused and minimal
3. **Async-First**: Design services with async/await support
4. **Configuration**: Use configuration injection for environment-specific settings

### Lifetime Management

- **Singleton**: Database connections, caches, expensive-to-create services
- **Transient**: Query builders, short-lived operations, stateless services
- **Scoped**: Request/operation-specific state, user contexts
- **Thread-local**: Thread-specific caches, per-thread state

### Error Handling

```python
try:
    service = await container.get_service_async(IMyService)
except ServiceNotFoundError:
    # Handle missing service
    logger.error("Required service not registered")
except CircularDependencyError as e:
    # Handle circular dependency
    logger.error(f"Circular dependency: {e.dependency_chain}")
```

### Resource Cleanup

```python
# Always dispose container when done
async with DIContainer("app") as container:
    # Register and use services
    pass
# Automatic cleanup

# Or manually
container = DIContainer("app")
try:
    # Use container
    pass
finally:
    await container.dispose_async()
```

## Troubleshooting

### Common Issues

1. **Service Not Found**: Ensure service is registered before resolution
2. **Circular Dependencies**: Review service dependencies, use factory pattern
3. **Async Issues**: Ensure all service methods are properly awaited
4. **Memory Leaks**: Always dispose containers and use proper lifetimes

### Debugging

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check service registration
assert container.is_registered(IMyService)

# Get registration info
metadata = container.get_registration_info(IMyService)
print(f"Service state: {metadata.state}")

# Monitor performance
monitor = container.performance_monitor
metrics = monitor.get_metrics("MyService")
print(f"Average resolution time: {metrics['avg_time_ms']}")
```

## License

This DI container is part of the GHL Real Estate AI system and follows the project's licensing terms.

## Support

For questions and support:
- Review the examples in `examples.py`
- Check the test suite in `testing_support.py`
- Examine configuration samples in `config/services.yml`