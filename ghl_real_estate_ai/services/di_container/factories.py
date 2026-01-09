"""
Factory Functions for Service Creation

Provides factory functions for creating complex services that require
dependency injection and configuration-driven initialization.
"""

import asyncio
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


async def create_property_repository(repository_factory: 'RepositoryFactory',
                                   config: Dict[str, Any]) -> 'IPropertyRepository':
    """
    Factory function to create property repository based on configuration.

    This function is used by the DI container to create repository instances
    with proper dependency injection.
    """
    from ..repositories.interfaces import IPropertyRepository

    repo_type = config.get('type', 'json')

    try:
        repository = await repository_factory.create(
            repository_type=repo_type,
            config=config.get('config', {}),
            enable_caching=config.get('enable_caching', True),
            cache_config=config.get('cache_config', {})
        )

        logger.info(f"Created property repository of type '{repo_type}'")
        return repository

    except Exception as e:
        logger.error(f"Failed to create property repository: {e}")
        raise


async def create_json_repository(repository_factory: 'RepositoryFactory',
                               config: Dict[str, Any]) -> 'IPropertyRepository':
    """Factory for JSON-based property repository"""
    from ..repositories.interfaces import IPropertyRepository

    json_config = {
        'data_paths': config.get('data_paths', []),
        'cache_ttl': config.get('cache_ttl', 300),
        'auto_refresh': config.get('auto_refresh', True),
        'normalize_data': config.get('normalize_data', True)
    }

    repository = await repository_factory.create(
        repository_type='json',
        config=json_config,
        enable_caching=config.get('enable_caching', True),
        cache_config=config.get('cache_config', {})
    )

    logger.info(f"Created JSON repository with {len(json_config['data_paths'])} data sources")
    return repository


async def create_mls_repository(repository_factory: 'RepositoryFactory',
                               config: Dict[str, Any]) -> 'IPropertyRepository':
    """Factory for MLS API repository"""
    from ..repositories.interfaces import IPropertyRepository

    mls_config = {
        'api_base_url': config.get('api_base_url'),
        'api_key': config.get('api_key'),
        'provider': config.get('provider', 'generic'),
        'rate_limit': config.get('rate_limit', 10),
        'timeout': config.get('timeout', 30),
        'retry_attempts': config.get('retry_attempts', 3)
    }

    # Validate required config
    if not mls_config['api_base_url'] or not mls_config['api_key']:
        raise ValueError("MLS repository requires api_base_url and api_key")

    repository = await repository_factory.create(
        repository_type='mls',
        config=mls_config,
        enable_caching=config.get('enable_caching', True),
        cache_config=config.get('cache_config', {})
    )

    logger.info(f"Created MLS repository for provider '{mls_config['provider']}'")
    return repository


async def create_rag_repository(repository_factory: 'RepositoryFactory',
                               config: Dict[str, Any]) -> 'IPropertyRepository':
    """Factory for RAG/semantic search repository"""
    from ..repositories.interfaces import IPropertyRepository

    rag_config = {
        'data_paths': config.get('data_paths', []),
        'embedding_model': config.get('embedding_model', 'all-MiniLM-L6-v2'),
        'similarity_threshold': config.get('similarity_threshold', 0.6),
        'max_semantic_results': config.get('max_semantic_results', 100),
        'fallback_to_traditional': config.get('fallback_to_traditional', True)
    }

    if config.get('openai_api_key'):
        rag_config['openai_api_key'] = config['openai_api_key']

    repository = await repository_factory.create(
        repository_type='rag',
        config=rag_config,
        enable_caching=config.get('enable_caching', True),
        cache_config=config.get('cache_config', {})
    )

    logger.info(f"Created RAG repository with model '{rag_config['embedding_model']}'")
    return repository


async def create_hybrid_repository(repository_factory: 'RepositoryFactory',
                                 config: Dict[str, Any]) -> 'IPropertyRepository':
    """Factory for hybrid repository (multiple data sources)"""
    from ..repositories.interfaces import IPropertyRepository

    # For now, create primary repository based on configuration
    # In full implementation, would create composite repository

    primary_source = config.get('primary_source', 'mls')

    if primary_source == 'mls' and config.get('mls_config'):
        return await create_mls_repository(repository_factory, config['mls_config'])
    elif primary_source == 'json' and config.get('json_paths'):
        json_config = {'data_paths': config['json_paths']}
        return await create_json_repository(repository_factory, json_config)
    else:
        # Fallback to JSON if available
        if config.get('json_paths'):
            json_config = {'data_paths': config['json_paths']}
            return await create_json_repository(repository_factory, json_config)
        else:
            raise ValueError("Hybrid repository requires at least one data source")


async def create_mock_repository(repository_factory: 'RepositoryFactory',
                               config: Dict[str, Any]) -> 'IPropertyRepository':
    """Factory for mock repository (testing)"""
    from ..repositories.testing.mock_repository import MockPropertyRepository

    mock_config = {
        'mock_data_count': config.get('mock_data_count', 100),
        'seed': config.get('seed', 12345),
        'response_delay_ms': config.get('response_delay_ms', 10)
    }

    repository = MockPropertyRepository("MockRepository", mock_config)
    await repository.connect()

    logger.info(f"Created mock repository with {mock_config['mock_data_count']} properties")
    return repository


def create_property_matcher_context(property_data_service: 'PropertyDataService',
                                   scoring_factory: 'ScoringFactory',
                                   config: Dict[str, Any]) -> 'PropertyMatcherContext':
    """Factory for property matcher context with Strategy Pattern integration"""

    try:
        from ..scoring import PropertyMatcherContext

        context = PropertyMatcherContext(
            property_data_service=property_data_service,
            scoring_factory=scoring_factory,
            strategy_name=config.get('strategy_name', 'enhanced'),
            fallback_strategy=config.get('fallback_strategy', 'basic'),
            enable_monitoring=config.get('enable_monitoring', True),
            enable_caching=config.get('enable_caching', True)
        )

        logger.info(f"Created property matcher context with strategy '{config.get('strategy_name')}'")
        return context

    except ImportError:
        logger.warning("Strategy Pattern modules not available")
        raise


def create_scoring_factory(config: Dict[str, Any]) -> 'ScoringFactory':
    """Factory for scoring factory"""

    try:
        from ..scoring import ScoringFactory, get_scoring_factory

        factory = get_scoring_factory()

        # Configure factory based on config
        if config.get('enable_enhanced_scoring', True):
            factory.register_enhanced_strategies()

        logger.info("Created scoring factory")
        return factory

    except ImportError:
        logger.warning("Scoring modules not available")
        raise


def create_performance_monitor(config: Dict[str, Any]) -> 'PerformanceMonitor':
    """Factory for performance monitoring service"""

    class PerformanceMonitor:
        """Simple performance monitoring implementation"""

        def __init__(self, config: Dict[str, Any]):
            self.config = config
            self.metrics = {}
            self.enabled = config.get('enabled', True)

        def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
            """Record a metric"""
            if not self.enabled:
                return

            if name not in self.metrics:
                self.metrics[name] = []

            self.metrics[name].append({
                'value': value,
                'tags': tags or {},
                'timestamp': asyncio.get_event_loop().time()
            })

        def get_metrics(self) -> Dict[str, Any]:
            """Get collected metrics"""
            return self.metrics.copy()

        def health_check(self) -> Dict[str, Any]:
            """Health check for monitoring service"""
            return {
                'healthy': True,
                'metrics_count': len(self.metrics),
                'enabled': self.enabled
            }

    monitor = PerformanceMonitor(config)
    logger.info("Created performance monitor")
    return monitor


def create_configuration_service(config: Dict[str, Any]) -> 'ConfigurationService':
    """Factory for configuration service"""

    class ConfigurationService:
        """Simple configuration service implementation"""

        def __init__(self, config: Dict[str, Any]):
            self._config = config.copy()

        def get(self, key: str, default: Any = None) -> Any:
            """Get configuration value"""
            keys = key.split('.')
            value = self._config

            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default

            return value

        def set(self, key: str, value: Any):
            """Set configuration value"""
            keys = key.split('.')
            config_ref = self._config

            for k in keys[:-1]:
                if k not in config_ref:
                    config_ref[k] = {}
                config_ref = config_ref[k]

            config_ref[keys[-1]] = value

        def get_all(self) -> Dict[str, Any]:
            """Get all configuration"""
            return self._config.copy()

        def health_check(self) -> Dict[str, Any]:
            """Health check for configuration service"""
            return {
                'healthy': True,
                'config_keys': len(self._config)
            }

    service = ConfigurationService(config)
    logger.info("Created configuration service")
    return service


# Real Estate Domain-Specific Factories
async def create_repository_property_matcher(container: 'DIContainer',
                                           config: Dict[str, Any]) -> 'RepositoryPropertyMatcher':
    """Factory for repository-backed property matcher"""

    try:
        from ..repositories.strategy_integration import RepositoryPropertyMatcher

        # Get dependencies from container
        property_data_service = await container.get_service_async('PropertyDataService')

        matcher = RepositoryPropertyMatcher(
            property_data_service=property_data_service,
            strategy_name=config.get('strategy_name', 'enhanced'),
            fallback_strategy=config.get('fallback_strategy', 'basic'),
            enable_monitoring=config.get('enable_monitoring', True),
            enable_caching=config.get('enable_caching', True)
        )

        logger.info("Created repository property matcher")
        return matcher

    except ImportError as e:
        logger.error(f"Failed to create repository property matcher: {e}")
        raise


# Factory registry for dynamic factory resolution
FACTORY_REGISTRY = {
    'property_repository': create_property_repository,
    'json_repository': create_json_repository,
    'mls_repository': create_mls_repository,
    'rag_repository': create_rag_repository,
    'hybrid_repository': create_hybrid_repository,
    'mock_repository': create_mock_repository,
    'property_matcher_context': create_property_matcher_context,
    'scoring_factory': create_scoring_factory,
    'performance_monitor': create_performance_monitor,
    'configuration_service': create_configuration_service,
    'repository_property_matcher': create_repository_property_matcher,
}


def get_factory(name: str):
    """Get factory function by name"""
    if name not in FACTORY_REGISTRY:
        raise ValueError(f"Unknown factory: {name}")
    return FACTORY_REGISTRY[name]