"""
Repository Factory Implementation

Provides factory methods for creating and configuring property repositories.
Supports dependency injection and configuration-based repository selection.
"""

import os
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type

try:
    from .caching_repository import CachingRepository, MemoryCacheBackend, RedisCacheBackend
    from .interfaces import IPropertyRepository, RepositoryConfig, RepositoryRegistry
    from .json_repository import JsonPropertyRepository
    from .mls_repository import MLSAPIRepository
    from .rag_repository import RAGPropertyRepository
except ImportError:
    from caching_repository import CachingRepository, MemoryCacheBackend, RedisCacheBackend
    from interfaces import IPropertyRepository, RepositoryConfig, RepositoryRegistry
    from json_repository import JsonPropertyRepository
    from mls_repository import MLSAPIRepository
    from rag_repository import RAGPropertyRepository


class RepositoryFactory:
    """
    Factory for creating property repositories with various configurations.

    Supports:
    - Configuration-driven repository creation
    - Automatic caching layer injection
    - Multiple repository chaining (composite pattern)
    - Environment-based configuration
    """

    def __init__(self):
        """Initialize repository factory with default registry"""
        self._registry: RepositoryRegistry = {
            "json": JsonPropertyRepository,
            "mls": MLSAPIRepository,
            "rag": RAGPropertyRepository,
        }

        self._default_configs: Dict[str, Dict[str, Any]] = {}

    def register_repository(self, name: str, repository_class: Type[IPropertyRepository]):
        """Register a new repository type"""
        self._registry[name] = repository_class

    def set_default_config(self, repository_type: str, config: RepositoryConfig):
        """Set default configuration for repository type"""
        self._default_configs[repository_type] = config

    async def create(
        self,
        repository_type: str,
        config: Optional[RepositoryConfig] = None,
        enable_caching: bool = True,
        cache_config: Optional[Dict[str, Any]] = None,
    ) -> IPropertyRepository:
        """
        Create repository instance.

        Args:
            repository_type: Type of repository ('json', 'mls', 'rag')
            config: Repository-specific configuration
            enable_caching: Whether to wrap with caching layer
            cache_config: Caching configuration

        Returns:
            Configured repository instance
        """
        if repository_type not in self._registry:
            raise ValueError(f"Unknown repository type: {repository_type}")

        # Merge configurations
        final_config = self._default_configs.get(repository_type, {}).copy()
        if config:
            final_config.update(config)

        # Create base repository
        repository_class = self._registry[repository_type]
        repository = repository_class(final_config)

        # Add caching layer if requested
        if enable_caching:
            cache_backend = self._create_cache_backend(cache_config or {})
            repository = CachingRepository(repository, cache_backend)

        return repository

    async def create_composite(
        self, repositories: List[Dict[str, Any]], strategy: str = "first_success"
    ) -> IPropertyRepository:
        """
        Create composite repository from multiple sources.

        Args:
            repositories: List of repository configurations
            strategy: Composite strategy ('first_success', 'merge_results', 'parallel')

        Returns:
            Composite repository instance
        """
        repo_instances = []

        for repo_config in repositories:
            repo_type = repo_config.get("type")
            repo_config_dict = repo_config.get("config", {})
            enable_cache = repo_config.get("enable_caching", True)

            if repo_type:
                repo = await self.create(repo_type, repo_config_dict, enable_cache)
                repo_instances.append(repo)

        if not repo_instances:
            raise ValueError("No valid repositories configured")

        # For now, return the first repository
        # In a full implementation, you'd create a CompositeRepository
        return repo_instances[0]

    def _create_cache_backend(self, cache_config: Dict[str, Any]):
        """Create cache backend based on configuration"""
        backend_type = cache_config.get("backend", "memory")

        if backend_type == "memory":
            max_size = cache_config.get("max_size", 1000)
            return MemoryCacheBackend(max_size=max_size)

        elif backend_type == "redis":
            redis_url = cache_config.get("redis_url", "redis://localhost:6379")
            key_prefix = cache_config.get("key_prefix", "prop_cache:")
            return RedisCacheBackend(redis_url=redis_url, key_prefix=key_prefix)

        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")


# Global factory instance
_factory = RepositoryFactory()


def create_repository(
    repository_type: str,
    config: Optional[RepositoryConfig] = None,
    enable_caching: bool = True,
    cache_config: Optional[Dict[str, Any]] = None,
) -> IPropertyRepository:
    """
    Convenience function to create repository using global factory.

    Args:
        repository_type: Type of repository ('json', 'mls', 'rag')
        config: Repository-specific configuration
        enable_caching: Whether to enable caching
        cache_config: Caching configuration

    Returns:
        Configured repository instance
    """
    import asyncio

    return asyncio.run(_factory.create(repository_type, config, enable_caching, cache_config))


def create_from_config(config_dict: Dict[str, Any]) -> IPropertyRepository:
    """
    Create repository from configuration dictionary.

    Expected config format:
    {
        "type": "json",
        "config": {...},
        "caching": {
            "enabled": true,
            "backend": "memory",
            "ttl": 900
        }
    }
    """
    repo_type = config_dict.get("type")
    repo_config = config_dict.get("config", {})

    caching_config = config_dict.get("caching", {})
    enable_caching = caching_config.get("enabled", True)
    cache_backend_config = {
        "backend": caching_config.get("backend", "memory"),
        "max_size": caching_config.get("max_size", 1000),
        "redis_url": caching_config.get("redis_url"),
        "key_prefix": caching_config.get("key_prefix", "prop_cache:"),
    }

    return create_repository(repo_type, repo_config, enable_caching, cache_backend_config)


def create_from_environment() -> IPropertyRepository:
    """
    Create repository from environment variables.

    Environment variables:
    - PROPERTY_REPO_TYPE: Repository type
    - PROPERTY_REPO_CONFIG: JSON config string
    - PROPERTY_CACHE_ENABLED: Enable caching (true/false)
    - PROPERTY_CACHE_BACKEND: Cache backend type
    """
    repo_type = os.getenv("PROPERTY_REPO_TYPE", "json")

    # Parse repository config from environment
    import json

    config_str = os.getenv("PROPERTY_REPO_CONFIG", "{}")
    try:
        repo_config = json.loads(config_str)
    except json.JSONDecodeError:
        repo_config = {}

    # Parse caching config
    enable_caching = os.getenv("PROPERTY_CACHE_ENABLED", "true").lower() == "true"
    cache_config = {
        "backend": os.getenv("PROPERTY_CACHE_BACKEND", "memory"),
        "redis_url": os.getenv("PROPERTY_CACHE_REDIS_URL", "redis://localhost:6379"),
        "max_size": int(os.getenv("PROPERTY_CACHE_MAX_SIZE", "1000")),
    }

    return create_repository(repo_type, repo_config, enable_caching, cache_config)


class RepositoryBuilder:
    """
    Builder pattern for creating complex repository configurations.
    """

    def __init__(self):
        self._config = {}
        self._cache_config = {}
        self._enable_caching = True

    def json_source(
        self, data_paths: List[str], cache_ttl: int = 300, auto_refresh: bool = True
    ) -> "RepositoryBuilder":
        """Configure JSON data source"""
        self._config = {
            "type": "json",
            "config": {
                "data_paths": data_paths,
                "cache_ttl": cache_ttl,
                "auto_refresh": auto_refresh,
                "normalize_data": True,
            },
        }
        return self

    def mls_source(
        self, api_base_url: str, api_key: str, provider: str = "generic", rate_limit: int = 10
    ) -> "RepositoryBuilder":
        """Configure MLS API source"""
        self._config = {
            "type": "mls",
            "config": {
                "api_base_url": api_base_url,
                "api_key": api_key,
                "provider": provider,
                "rate_limit": rate_limit,
                "timeout": 30,
                "retry_attempts": 3,
            },
        }
        return self

    def rag_source(
        self, data_paths: List[str], embedding_model: str = "all-MiniLM-L6-v2", openai_api_key: Optional[str] = None
    ) -> "RepositoryBuilder":
        """Configure RAG/semantic search source"""
        config = {
            "data_paths": data_paths,
            "embedding_model": embedding_model,
            "similarity_threshold": 0.6,
            "max_semantic_results": 100,
            "fallback_to_traditional": True,
        }

        if openai_api_key:
            config["openai_api_key"] = openai_api_key

        self._config = {"type": "rag", "config": config}
        return self

    def with_memory_cache(self, max_size: int = 1000, ttl_minutes: int = 15) -> "RepositoryBuilder":
        """Add in-memory caching"""
        self._enable_caching = True
        self._cache_config = {"backend": "memory", "max_size": max_size, "ttl": ttl_minutes * 60}
        return self

    def with_redis_cache(
        self, redis_url: str = "redis://localhost:6379", key_prefix: str = "prop_cache:", ttl_minutes: int = 15
    ) -> "RepositoryBuilder":
        """Add Redis caching"""
        self._enable_caching = True
        self._cache_config = {
            "backend": "redis",
            "redis_url": redis_url,
            "key_prefix": key_prefix,
            "ttl": ttl_minutes * 60,
        }
        return self

    def without_cache(self) -> "RepositoryBuilder":
        """Disable caching"""
        self._enable_caching = False
        self._cache_config = {}
        return self

    async def build(self) -> IPropertyRepository:
        """Build the configured repository"""
        if not self._config:
            raise ValueError("No repository source configured")

        repo_type = self._config["type"]
        repo_config = self._config["config"]

        return await _factory.create(
            repository_type=repo_type,
            config=repo_config,
            enable_caching=self._enable_caching,
            cache_config=self._cache_config,
        )


# Convenience builders
def json_repository(data_paths: List[str]) -> RepositoryBuilder:
    """Quick JSON repository builder"""
    return RepositoryBuilder().json_source(data_paths)


def mls_repository(api_base_url: str, api_key: str, provider: str = "generic") -> RepositoryBuilder:
    """Quick MLS repository builder"""
    return RepositoryBuilder().mls_source(api_base_url, api_key, provider)


def rag_repository(data_paths: List[str], embedding_model: str = "all-MiniLM-L6-v2") -> RepositoryBuilder:
    """Quick RAG repository builder"""
    return RepositoryBuilder().rag_source(data_paths, embedding_model)


# Pre-configured factories for common use cases
class ConfiguredFactories:
    """Pre-configured repository factories for common scenarios"""

    @staticmethod
    async def demo_json_repository(data_dir: str = "./data/knowledge_base") -> IPropertyRepository:
        """Create demo repository using JSON data"""
        data_path = Path(data_dir)
        json_files = list(data_path.glob("*.json"))

        if not json_files:
            raise ValueError(f"No JSON files found in {data_dir}")

        return await (
            json_repository([str(f) for f in json_files]).with_memory_cache(max_size=500, ttl_minutes=10).build()
        )

    @staticmethod
    async def production_mls_repository(api_url: str, api_key: str, provider: str = "generic") -> IPropertyRepository:
        """Create production MLS repository with Redis caching"""
        return await mls_repository(api_url, api_key, provider).with_redis_cache(ttl_minutes=30).build()

    @staticmethod
    async def hybrid_repository(json_paths: List[str], mls_config: Dict[str, Any]) -> IPropertyRepository:
        """Create hybrid repository with JSON fallback and MLS primary"""
        # For now, return MLS repository
        # In full implementation, would create composite repository
        return await (
            mls_repository(mls_config["api_url"], mls_config["api_key"], mls_config.get("provider", "generic"))
            .with_memory_cache()
            .build()
        )


# Export convenience functions
__all__ = [
    "RepositoryFactory",
    "RepositoryBuilder",
    "create_repository",
    "create_from_config",
    "create_from_environment",
    "json_repository",
    "mls_repository",
    "rag_repository",
    "ConfiguredFactories",
]
