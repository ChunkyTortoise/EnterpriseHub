"""
Integration Layer for Strategy and Repository Patterns

Provides seamless integration between the DI Container and existing
Strategy Pattern and Repository Pattern implementations.
"""

import asyncio
import logging
from typing import Any, Dict, Protocol

from .container import DIContainer

logger = logging.getLogger(__name__)


class IServiceIntegration(Protocol):
    """Protocol for service pattern integration"""

    async def initialize(self, container: DIContainer) -> None:
        """Initialize integration with DI container"""
        ...

    async def configure_services(self, config: Dict[str, Any]) -> None:
        """Configure services from configuration"""
        ...


class RepositoryPatternIntegration:
    """
    Integration layer for Repository Pattern services.

    Provides automatic registration and configuration of repository services
    with the DI container, including caching, monitoring, and health checks.
    """

    def __init__(self, container: DIContainer):
        self.container = container
        self._initialized = False

    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize repository pattern integration"""
        if self._initialized:
            return

        config = config or {}

        # Register core repository interfaces and factories
        await self._register_core_services(config)

        # Register repository implementations
        await self._register_repository_implementations(config)

        # Register caching services
        await self._register_caching_services(config)

        # Register data services
        await self._register_data_services(config)

        self._initialized = True
        logger.info("Repository pattern integration initialized")

    async def _register_core_services(self, config: Dict[str, Any]) -> None:
        """Register core repository services"""
        from ..repositories.query_builder import PropertyQueryBuilder
        from ..repositories.repository_factory import RepositoryFactory

        # Register repository factory as singleton
        self.container.register_singleton(
            RepositoryFactory, name="RepositoryFactory", tags=["repository", "factory", "core"]
        )

        # Register query builder as transient
        self.container.register_transient(
            PropertyQueryBuilder, name="PropertyQueryBuilder", tags=["repository", "query", "builder"]
        )

    async def _register_repository_implementations(self, config: Dict[str, Any]) -> None:
        """Register repository implementation services"""
        from ..repositories.interfaces import IPropertyRepository
        from .factories import (
            create_hybrid_repository,
            create_json_repository,
            create_mls_repository,
            create_rag_repository,
        )

        repo_configs = config.get("repositories", {})

        # Register repository factories based on configuration
        for repo_name, repo_config in repo_configs.items():
            repo_type = repo_config.get("type", "json")

            factory_map = {
                "json": create_json_repository,
                "mls": create_mls_repository,
                "rag": create_rag_repository,
                "hybrid": create_hybrid_repository,
            }

            factory_func = factory_map.get(repo_type)
            if factory_func:
                self.container.register_singleton(
                    IPropertyRepository,
                    name=repo_name,
                    factory=lambda factory, config=repo_config: factory_func(factory, config),
                    tags=["repository", repo_type, repo_name],
                    configuration=repo_config,
                )

        # Register primary repository
        primary_repo = config.get("primary_repository", "PropertyRepository")
        if primary_repo in repo_configs:
            self.container.register_singleton(
                IPropertyRepository,
                name="PrimaryPropertyRepository",
                factory=lambda container: container.get_service(IPropertyRepository, primary_repo),
                tags=["repository", "primary"],
            )

    async def _register_caching_services(self, config: Dict[str, Any]) -> None:
        """Register caching services"""
        from ..repositories.caching_repository import MemoryCacheBackend, RedisCacheBackend

        cache_config = config.get("caching", {})

        # Memory cache backend
        if cache_config.get("memory", {}).get("enabled", True):
            memory_config = cache_config.get("memory", {})
            self.container.register_singleton(
                MemoryCacheBackend, name="MemoryCacheBackend", tags=["cache", "memory"], configuration=memory_config
            )

        # Redis cache backend
        if cache_config.get("redis", {}).get("enabled", False):
            redis_config = cache_config.get("redis", {})
            self.container.register_singleton(
                RedisCacheBackend, name="RedisCacheBackend", tags=["cache", "redis"], configuration=redis_config
            )

    async def _register_data_services(self, config: Dict[str, Any]) -> None:
        """Register data services"""
        from ..repositories.property_data_service import PropertyDataService, PropertyDataServiceFactory

        # Register data service factory
        self.container.register_singleton(
            PropertyDataServiceFactory, name="PropertyDataServiceFactory", tags=["data", "factory"]
        )

        # Register primary data service
        data_service_config = config.get("data_service", {"type": "demo", "config": {}})

        async def create_data_service(factory: PropertyDataServiceFactory) -> PropertyDataService:
            service_type = data_service_config.get("type", "demo")
            service_config = data_service_config.get("config", {})

            if service_type == "demo":
                data_dir = service_config.get("data_dir", "./data/knowledge_base")
                return await factory.create_demo_service(data_dir)
            elif service_type == "production":
                mls_config = service_config.get("mls_config", {})
                fallback_paths = service_config.get("fallback_paths", [])
                return await factory.create_production_service(mls_config, fallback_paths)
            elif service_type == "hybrid":
                json_paths = service_config.get("json_paths", [])
                mls_config = service_config.get("mls_config")
                rag_config = service_config.get("rag_config")
                return await factory.create_hybrid_service(json_paths, mls_config, rag_config)
            else:
                raise ValueError(f"Unknown data service type: {service_type}")

        self.container.register_singleton(
            PropertyDataService,
            name="PropertyDataService",
            factory=create_data_service,
            tags=["data", "service", "primary"],
        )

    async def get_repository(self, name: str = None) -> "IPropertyRepository":
        """Get repository instance"""
        repo_name = name or "PrimaryPropertyRepository"
        return await self.container.get_service_async("IPropertyRepository", repo_name)

    async def get_data_service(self) -> "PropertyDataService":
        """Get property data service"""
        return await self.container.get_service_async("PropertyDataService")


class StrategyPatternIntegration:
    """
    Integration layer for Strategy Pattern services.

    Provides automatic registration of scoring strategies, property matchers,
    and related services with proper dependency injection.
    """

    def __init__(self, container: DIContainer):
        self.container = container
        self._initialized = False

    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """Initialize strategy pattern integration"""
        if self._initialized:
            return

        config = config or {}

        try:
            # Register scoring services
            await self._register_scoring_services(config)

            # Register property matcher services
            await self._register_property_matcher_services(config)

            # Register enhanced integration services
            await self._register_integration_services(config)

            self._initialized = True
            logger.info("Strategy pattern integration initialized")

        except ImportError as e:
            logger.warning(f"Strategy pattern modules not available: {e}")
            await self._register_fallback_services(config)

    async def _register_scoring_services(self, config: Dict[str, Any]) -> None:
        """Register scoring strategy services"""
        try:
            from ..scoring import ScoringFactory, get_scoring_factory
            from .factories import create_scoring_factory

            scoring_config = config.get("scoring", {})

            # Register scoring factory
            self.container.register_singleton(
                ScoringFactory,
                name="ScoringFactory",
                factory=lambda config=scoring_config: create_scoring_factory(config),
                tags=["scoring", "factory", "strategy"],
            )

            # Register specific scoring strategies if configured
            strategies = scoring_config.get("strategies", {})
            for strategy_name, strategy_config in strategies.items():
                await self._register_scoring_strategy(strategy_name, strategy_config)

        except ImportError:
            logger.warning("Scoring modules not available, skipping scoring service registration")

    async def _register_scoring_strategy(self, name: str, config: Dict[str, Any]) -> None:
        """Register individual scoring strategy"""
        try:
            # Dynamic strategy registration would go here
            # For now, strategies are managed by the ScoringFactory
            pass
        except Exception as e:
            logger.error(f"Failed to register scoring strategy '{name}': {e}")

    async def _register_property_matcher_services(self, config: Dict[str, Any]) -> None:
        """Register property matcher services"""
        try:
            from ..scoring import PropertyMatcherContext
            from .factories import create_property_matcher_context

            matcher_config = config.get("property_matcher", {})

            # Register property matcher context as scoped
            self.container.register_scoped(
                PropertyMatcherContext,
                name="PropertyMatcherContext",
                factory=lambda data_service, scoring_factory, config=matcher_config: create_property_matcher_context(
                    data_service, scoring_factory, config
                ),
                tags=["scoring", "matcher", "context"],
            )

        except ImportError:
            logger.warning("Property matcher modules not available")

    async def _register_integration_services(self, config: Dict[str, Any]) -> None:
        """Register integration services"""
        try:
            from ..repositories.strategy_integration import RepositoryPropertyMatcher
            from .factories import create_repository_property_matcher

            integration_config = config.get("integration", {})

            # Register repository property matcher
            self.container.register_scoped(
                RepositoryPropertyMatcher,
                name="RepositoryPropertyMatcher",
                factory=lambda container, config=integration_config: create_repository_property_matcher(
                    container, config
                ),
                tags=["integration", "repository", "strategy"],
            )

        except ImportError:
            logger.warning("Integration modules not available")

    async def _register_fallback_services(self, config: Dict[str, Any]) -> None:
        """Register fallback services when Strategy Pattern is not available"""

        # Register mock/fallback implementations
        class MockScoringFactory:
            def create_scorer(self, strategy_name: str):
                return MockScorer()

            def get_available_strategies(self):
                return ["basic", "mock"]

        class MockScorer:
            def score_property(self, property_data, preferences, context=None):
                return 75.0  # Default score

        self.container.register_singleton(
            MockScoringFactory, name="ScoringFactory", tags=["scoring", "mock", "fallback"]
        )

    async def get_scoring_factory(self) -> "ScoringFactory":
        """Get scoring factory"""
        return await self.container.get_service_async("ScoringFactory")

    async def get_property_matcher(self, scope_id: str = None) -> "PropertyMatcherContext":
        """Get property matcher context"""
        return await self.container.get_service_async("PropertyMatcherContext", scope_id=scope_id)

    async def get_repository_matcher(self, scope_id: str = None) -> "RepositoryPropertyMatcher":
        """Get repository property matcher"""
        return await self.container.get_service_async("RepositoryPropertyMatcher", scope_id=scope_id)


class RealEstateServiceOrchestrator:
    """
    High-level orchestrator for all real estate-specific services.

    Provides a unified interface for initializing and managing all
    real estate services with proper dependency injection.
    """

    def __init__(self, container: DIContainer):
        self.container = container
        self.repository_integration = RepositoryPatternIntegration(container)
        self.strategy_integration = StrategyPatternIntegration(container)
        self._initialized = False

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize all real estate services"""
        if self._initialized:
            return

        try:
            # Initialize pattern integrations
            await self.repository_integration.initialize(config.get("repositories", {}))
            await self.strategy_integration.initialize(config.get("strategies", {}))

            # Register monitoring and utility services
            await self._register_monitoring_services(config.get("monitoring", {}))

            # Register configuration service
            await self._register_configuration_service(config.get("configuration", {}))

            # Register health check services
            await self._register_health_services()

            self._initialized = True
            logger.info("Real estate service orchestrator initialized")

        except Exception as e:
            logger.error(f"Failed to initialize real estate services: {e}")
            raise

    async def _register_monitoring_services(self, config: Dict[str, Any]) -> None:
        """Register monitoring services"""
        from .factories import create_performance_monitor

        if config.get("enabled", True):
            self.container.register_singleton(
                type(None),  # Performance monitor type would be defined
                name="PerformanceMonitor",
                factory=lambda config=config: create_performance_monitor(config),
                tags=["monitoring", "performance"],
            )

    async def _register_configuration_service(self, config: Dict[str, Any]) -> None:
        """Register configuration service"""
        from .factories import create_configuration_service

        self.container.register_singleton(
            type(None),  # Configuration service type would be defined
            name="ConfigurationService",
            factory=lambda config=config: create_configuration_service(config),
            tags=["configuration", "service"],
        )

    async def _register_health_services(self) -> None:
        """Register health check services"""
        # Health checks are registered as part of service metadata
        # This method could register a centralized health check service
        pass

    async def create_property_search_context(self, scope_id: str = None) -> Dict[str, Any]:
        """
        Create a complete property search context with all required services.

        This is the main entry point for real estate operations.
        """
        scope_id = scope_id or f"search_{asyncio.get_event_loop().time()}"

        async with self.container.create_scope_async(scope_id) as scope:
            # Get all required services
            repository = await self.repository_integration.get_repository()
            data_service = await self.repository_integration.get_data_service()

            context = {
                "scope_id": scope,
                "repository": repository,
                "data_service": data_service,
                "container": self.container,
            }

            # Add strategy services if available
            try:
                scoring_factory = await self.strategy_integration.get_scoring_factory()
                property_matcher = await self.strategy_integration.get_property_matcher(scope)
                repository_matcher = await self.strategy_integration.get_repository_matcher(scope)

                context.update(
                    {
                        "scoring_factory": scoring_factory,
                        "property_matcher": property_matcher,
                        "repository_matcher": repository_matcher,
                    }
                )
            except Exception as e:
                logger.warning(f"Strategy services not available: {e}")

            # Add monitoring if available
            try:
                performance_monitor = await self.container.get_service_async("PerformanceMonitor")
                context["performance_monitor"] = performance_monitor
            except:
                pass

            return context

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status of all real estate services"""
        from .health_checks import container_health_check

        return await container_health_check(self.container)

    def is_initialized(self) -> bool:
        """Check if orchestrator is initialized"""
        return self._initialized


# Convenience function for easy integration
async def initialize_real_estate_services(
    container: DIContainer, config: Dict[str, Any]
) -> RealEstateServiceOrchestrator:
    """
    Initialize all real estate services with a single function call.

    Args:
        container: DI Container instance
        config: Configuration dictionary

    Returns:
        Configured RealEstateServiceOrchestrator
    """
    orchestrator = RealEstateServiceOrchestrator(container)
    await orchestrator.initialize(config)
    return orchestrator
