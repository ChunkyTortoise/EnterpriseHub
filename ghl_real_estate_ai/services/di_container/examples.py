"""
Complete Real Estate Service Composition Examples

Demonstrates practical usage of the DI Container with real estate services,
showing complete end-to-end scenarios and integration patterns.
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from .container import DIContainer
from .service_registration import ServiceRegistrar, YamlConfigurationProvider
from .pattern_integration import RealEstateServiceOrchestrator
from .performance import OptimizedDIContainer, RealEstatePerformanceOptimizer

logger = logging.getLogger(__name__)


class RealEstateServiceComposer:
    """
    High-level composer for real estate services with DI Container.

    Provides complete examples and patterns for integrating all real estate
    services using dependency injection.
    """

    def __init__(self):
        self.container: Optional[DIContainer] = None
        self.orchestrator: Optional[RealEstateServiceOrchestrator] = None
        self.optimized_container: Optional[OptimizedDIContainer] = None

    async def create_development_environment(self) -> Dict[str, Any]:
        """
        Create complete development environment with all services.

        This example shows how to set up a full development environment
        with JSON data sources, in-memory caching, and enhanced scoring.
        """
        logger.info("Setting up development environment...")

        # Create base container
        self.container = DIContainer("development")

        # Development configuration
        config = {
            'repositories': {
                'JsonRepository': {
                    'type': 'json',
                    'config': {
                        'data_paths': [
                            '/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base/austin_market_demo_data.json',
                            '/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base/jorge_demo_scenarios.json'
                        ],
                        'cache_ttl': 300,
                        'auto_refresh': True
                    },
                    'enable_caching': True,
                    'cache_config': {
                        'backend': 'memory',
                        'max_size': 500
                    }
                }
            },
            'strategies': {
                'scoring': {
                    'strategies': {
                        'basic': {'enabled': True},
                        'enhanced': {'enabled': True, 'weight_budget': 0.4}
                    }
                },
                'property_matcher': {
                    'strategy_name': 'enhanced',
                    'fallback_strategy': 'basic',
                    'enable_monitoring': True
                },
                'integration': {
                    'strategy_name': 'enhanced',
                    'enable_monitoring': True
                }
            },
            'caching': {
                'memory': {
                    'enabled': True,
                    'max_size': 1000
                }
            },
            'monitoring': {
                'enabled': True
            },
            'configuration': {
                'environment': 'development',
                'debug': True
            }
        }

        # Initialize orchestrator
        self.orchestrator = RealEstateServiceOrchestrator(self.container)
        await self.orchestrator.initialize(config)

        # Create optimized container wrapper
        self.optimized_container = OptimizedDIContainer(
            self.container,
            enable_caching=True,
            enable_monitoring=True
        )

        # Configure performance optimizations
        RealEstatePerformanceOptimizer.configure_container_for_real_estate(
            self.optimized_container
        )

        # Warm up services
        await self.optimized_container.warm_up_services()

        logger.info("Development environment ready")

        return {
            'container': self.container,
            'orchestrator': self.orchestrator,
            'optimized_container': self.optimized_container,
            'config': config
        }

    async def create_production_environment(self, mls_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create production environment with MLS integration and Redis caching.

        This example shows production-ready setup with external data sources,
        Redis caching, and comprehensive monitoring.
        """
        logger.info("Setting up production environment...")

        # Create base container
        self.container = DIContainer("production")

        # Production configuration
        config = {
            'repositories': {
                'PrimaryMLSRepository': {
                    'type': 'mls',
                    'config': {
                        'api_base_url': mls_config['api_base_url'],
                        'api_key': mls_config['api_key'],
                        'provider': mls_config.get('provider', 'production_mls'),
                        'rate_limit': 10,
                        'timeout': 30,
                        'retry_attempts': 3
                    },
                    'enable_caching': True,
                    'cache_config': {
                        'backend': 'redis',
                        'redis_url': mls_config.get('redis_url', 'redis://localhost:6379'),
                        'ttl': 1800  # 30 minutes
                    }
                },
                'FallbackRepository': {
                    'type': 'json',
                    'config': {
                        'data_paths': [
                            '/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base/austin_market_demo_data.json'
                        ]
                    },
                    'enable_caching': True
                }
            },
            'strategies': {
                'scoring': {
                    'strategies': {
                        'enhanced': {
                            'enabled': True,
                            'weight_budget': 0.35,
                            'weight_location': 0.35,
                            'weight_features': 0.30
                        }
                    }
                },
                'property_matcher': {
                    'strategy_name': 'enhanced',
                    'enable_monitoring': True,
                    'enable_caching': True
                }
            },
            'caching': {
                'redis': {
                    'enabled': True,
                    'redis_url': mls_config.get('redis_url', 'redis://localhost:6379'),
                    'key_prefix': 'ghl_prod_cache:'
                },
                'memory': {
                    'enabled': True,
                    'max_size': 2000  # Larger cache for production
                }
            },
            'monitoring': {
                'enabled': True,
                'slow_service_threshold_ms': 50.0
            },
            'configuration': {
                'environment': 'production',
                'debug': False
            }
        }

        # Initialize orchestrator
        self.orchestrator = RealEstateServiceOrchestrator(self.container)
        await self.orchestrator.initialize(config)

        # Create optimized container
        self.optimized_container = OptimizedDIContainer(
            self.container,
            enable_caching=True,
            enable_monitoring=True
        )

        # Production-specific optimizations
        perf_config = RealEstatePerformanceOptimizer.get_performance_configuration()
        RealEstatePerformanceOptimizer.configure_container_for_real_estate(
            self.optimized_container
        )

        # Warm up critical services
        await self.optimized_container.warm_up_services()

        logger.info("Production environment ready")

        return {
            'container': self.container,
            'orchestrator': self.orchestrator,
            'optimized_container': self.optimized_container,
            'config': config,
            'performance_config': perf_config
        }

    async def demonstrate_property_search_workflow(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrate complete property search workflow using DI services.

        This example shows how to use the DI container to perform a complete
        property search with scoring, caching, and monitoring.
        """
        logger.info("Demonstrating property search workflow...")

        orchestrator = environment['orchestrator']

        # Create property search context with all services injected
        async with orchestrator.container.create_scope_async() as scope_id:
            context = await orchestrator.create_property_search_context(scope_id)

            # Example lead preferences
            lead_preferences = {
                'budget': 650000,
                'location': 'downtown',
                'bedrooms': 3,
                'bathrooms': 2.5,
                'property_type': 'Single Family',
                'must_haves': ['garage', 'yard'],
                'nice_to_haves': ['pool', 'good_schools'],
                'work_location': 'downtown',
                'has_children': True,
                'min_sqft': 2000
            }

            # Step 1: Load properties using Repository Pattern
            logger.info("Step 1: Loading properties...")
            data_service = context['data_service']
            properties = await data_service.load_properties_for_strategy_pattern(lead_preferences)
            logger.info(f"Loaded {len(properties)} properties from data service")

            # Step 2: Score properties using Strategy Pattern (if available)
            scored_properties = []
            if 'repository_matcher' in context:
                logger.info("Step 2: Scoring properties with enhanced strategy...")
                repository_matcher = context['repository_matcher']

                lead_context = {
                    'extracted_preferences': lead_preferences,
                    'lead_id': 'demo_lead_123',
                    'agent_id': 'demo_agent_456'
                }

                scored_properties = await repository_matcher.score_properties_with_repository(
                    lead_preferences=lead_preferences,
                    context=lead_context,
                    max_properties=20
                )
            else:
                logger.info("Step 2: Using basic scoring fallback...")
                # Basic scoring fallback
                for prop in properties[:10]:
                    scored_prop = prop.copy()
                    scored_prop.update({
                        'overall_score': 75.0,
                        'match_reasons': ['Property meets basic criteria'],
                        'confidence_level': 'medium'
                    })
                    scored_properties.append(scored_prop)

            # Step 3: Format results for UI
            logger.info("Step 3: Formatting results...")
            formatted_results = []
            for prop in scored_properties[:5]:  # Top 5 matches
                formatted_result = {
                    'address': prop.get('address', 'Property Address'),
                    'price': prop.get('price', 0),
                    'beds': prop.get('bedrooms', prop.get('beds', 3)),
                    'baths': prop.get('bathrooms', prop.get('baths', 2.5)),
                    'sqft': prop.get('sqft', prop.get('square_feet', 2100)),
                    'neighborhood': prop.get('neighborhood', 'Austin Area'),
                    'match_score': int(prop.get('overall_score', 75)),
                    'match_reasons': prop.get('match_reasons', []),
                    'confidence_level': prop.get('confidence_level', 'medium'),
                    'source': prop.get('_source', 'unknown')
                }
                formatted_results.append(formatted_result)

            # Step 4: Get performance metrics
            performance_metrics = {}
            if 'performance_monitor' in context:
                performance_monitor = context['performance_monitor']
                performance_metrics = performance_monitor.get_metrics()

            # Step 5: Get health status
            health_status = await orchestrator.get_health_status()

            workflow_results = {
                'lead_preferences': lead_preferences,
                'total_properties_found': len(properties),
                'scored_properties_count': len(scored_properties),
                'top_matches': formatted_results,
                'performance_metrics': performance_metrics,
                'health_status': health_status['healthy'],
                'context_services': list(context.keys())
            }

            logger.info(f"Workflow completed. Found {len(formatted_results)} top matches")
            return workflow_results

    async def demonstrate_configuration_driven_setup(self, config_file_path: str) -> Dict[str, Any]:
        """
        Demonstrate configuration-driven service setup from YAML file.

        This example shows how to use configuration files to set up
        the entire DI container and services.
        """
        logger.info(f"Setting up services from configuration file: {config_file_path}")

        # Create container and registrar
        self.container = DIContainer("config_driven")
        registrar = ServiceRegistrar(self.container)

        # Load configuration from YAML
        config_provider = YamlConfigurationProvider(config_file_path)
        await registrar.register_from_config(config_provider, environment="development")

        # Create orchestrator and initialize
        self.orchestrator = RealEstateServiceOrchestrator(self.container)

        # Get configuration for orchestrator from same file
        config_data = await config_provider.load_configuration("development")

        # Convert to orchestrator format
        orchestrator_config = {
            'repositories': {},
            'strategies': {},
            'monitoring': {'enabled': True}
        }

        # Initialize orchestrator
        await self.orchestrator.initialize(orchestrator_config)

        # Verify services are properly registered
        registered_services = list(self.container._services.keys())
        health_status = await self.orchestrator.get_health_status()

        logger.info(f"Configuration-driven setup completed. Registered {len(registered_services)} services")

        return {
            'container': self.container,
            'orchestrator': self.orchestrator,
            'registered_services': registered_services,
            'health_status': health_status,
            'config_file': config_file_path
        }

    async def demonstrate_testing_setup(self) -> Dict[str, Any]:
        """
        Demonstrate test environment setup with mocks and test data.

        This example shows how to set up a testing environment with
        mocked services for unit and integration testing.
        """
        logger.info("Setting up testing environment...")

        from .testing_support import TestDIContainer, MockServiceFactory

        # Create test container with mocks
        test_container = TestDIContainer("testing")

        # Register mock services
        test_container.register_mock(
            'IPropertyRepository',
            MockServiceFactory.create_mock_repository(),
            name="MockRepository"
        )

        test_container.register_mock(
            'PropertyDataService',
            MockServiceFactory.create_mock_data_service(),
            name="MockDataService"
        )

        test_container.register_mock(
            'ScoringFactory',
            MockServiceFactory.create_mock_scoring_factory(),
            name="MockScoringFactory"
        )

        test_container.register_mock(
            'MemoryCacheBackend',
            MockServiceFactory.create_mock_cache_backend(),
            name="MockCache"
        )

        # Create orchestrator with test configuration
        test_orchestrator = RealEstateServiceOrchestrator(test_container)

        test_config = {
            'repositories': {'test_repo': {'type': 'mock'}},
            'strategies': {'scoring': {'strategies': {'mock': {'enabled': True}}}},
            'monitoring': {'enabled': False}
        }

        await test_orchestrator.initialize(test_config)

        # Test service resolution
        repo = await test_container.get_service_async('IPropertyRepository', "MockRepository")
        data_service = await test_container.get_service_async('PropertyDataService', "MockDataService")

        # Verify mocks
        repo_mock = test_container.get_mock('IPropertyRepository', "MockRepository")
        assert repo_mock.is_connected == True

        logger.info("Testing environment setup completed")

        return {
            'test_container': test_container,
            'test_orchestrator': test_orchestrator,
            'mock_repository': repo,
            'mock_data_service': data_service,
            'registered_mocks': list(test_container._test_mocks.keys())
        }

    async def demonstrate_performance_monitoring(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Demonstrate performance monitoring and optimization features.

        This example shows how to monitor service performance and
        generate optimization recommendations.
        """
        logger.info("Demonstrating performance monitoring...")

        optimized_container = environment.get('optimized_container')
        if not optimized_container:
            # Create optimized container if not provided
            optimized_container = OptimizedDIContainer(
                environment['container'],
                enable_caching=True,
                enable_monitoring=True
            )

        # Perform multiple service resolutions to generate metrics
        for i in range(50):
            try:
                await optimized_container.get_service_async('IPropertyRepository')
                await optimized_container.get_service_async('PropertyDataService')
                if i % 10 == 0:
                    await optimized_container.get_service_async('ScoringFactory')
            except:
                pass  # Ignore errors for demo

        # Get performance report
        performance_report = optimized_container.get_performance_report()

        # Run benchmarks
        benchmark_results = await RealEstatePerformanceOptimizer.benchmark_property_operations(
            optimized_container,
            iterations=25
        )

        # Generate recommendations
        recommendations = performance_report.get('recommendations', [])

        logger.info("Performance monitoring demonstration completed")

        return {
            'performance_report': performance_report,
            'benchmark_results': benchmark_results,
            'recommendations': recommendations,
            'monitoring_enabled': True
        }

    async def cleanup(self):
        """Cleanup all created resources"""
        if self.container:
            await self.container.dispose_async()

        if self.optimized_container:
            # Optimized container cleanup is handled by base container
            pass

        logger.info("Cleanup completed")


# Example usage functions
async def run_development_example():
    """Run complete development environment example"""
    composer = RealEstateServiceComposer()

    try:
        # Setup environment
        dev_env = await composer.create_development_environment()
        print("✅ Development environment created")

        # Run property search workflow
        search_results = await composer.demonstrate_property_search_workflow(dev_env)
        print(f"✅ Property search completed. Found {len(search_results['top_matches'])} matches")

        # Monitor performance
        perf_results = await composer.demonstrate_performance_monitoring(dev_env)
        print("✅ Performance monitoring demonstrated")

        # Print summary
        print(f"\n📊 Development Environment Summary:")
        print(f"   - Services registered: {len(dev_env['container']._services)}")
        print(f"   - Health status: {'✅ Healthy' if search_results['health_status'] else '❌ Unhealthy'}")
        print(f"   - Top match score: {search_results['top_matches'][0]['match_score'] if search_results['top_matches'] else 'N/A'}")

        return {
            'environment': dev_env,
            'search_results': search_results,
            'performance_results': perf_results
        }

    finally:
        await composer.cleanup()


async def run_testing_example():
    """Run testing environment example"""
    composer = RealEstateServiceComposer()

    try:
        # Setup test environment
        test_env = await composer.demonstrate_testing_setup()
        print("✅ Testing environment created")

        # Test mock interactions
        mock_repo = test_env['mock_repository']
        from ..repositories.interfaces import PropertyQuery

        # Test query
        test_query = PropertyQuery()
        result = await mock_repo.find_properties(test_query)

        print(f"✅ Mock test completed. Result count: {result.count}")

        # Verify mock calls
        repo_mock = test_env['test_container'].get_mock('IPropertyRepository', "MockRepository")
        print(f"✅ Mock verification: find_properties called {repo_mock.find_properties.call_count} times")

        return test_env

    finally:
        await composer.cleanup()


if __name__ == "__main__":
    # Run examples
    print("🚀 Starting Real Estate DI Container Examples\n")

    print("📋 Running Development Environment Example...")
    dev_results = asyncio.run(run_development_example())

    print("\n📋 Running Testing Environment Example...")
    test_results = asyncio.run(run_testing_example())

    print("\n✅ All examples completed successfully!")