"""
Service Registration Patterns and Configuration

Provides configuration-driven service registration with support for
environment-specific configurations and automatic service discovery.
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Type, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import importlib
import inspect
import logging

from .container import DIContainer, ServiceLifetime

logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Configuration for a single service"""
    name: str
    service_type: str  # Full class path or interface name
    implementation: Optional[str] = None  # Full class path
    lifetime: str = "singleton"  # singleton, transient, scoped, thread_local
    factory: Optional[str] = None  # Factory function path
    tags: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    health_check: Optional[str] = None  # Health check function path
    dependencies: List[str] = field(default_factory=list)
    condition: Optional[str] = None  # Conditional registration


@dataclass
class EnvironmentConfig:
    """Environment-specific configuration"""
    name: str
    services: List[ServiceConfig] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    imports: List[str] = field(default_factory=list)
    extends: Optional[str] = None  # Base configuration to extend


class IServiceConfigurationProvider(ABC):
    """Interface for service configuration providers"""

    @abstractmethod
    async def load_configuration(self, environment: str = "development") -> EnvironmentConfig:
        """Load service configuration for environment"""
        pass


class YamlConfigurationProvider(IServiceConfigurationProvider):
    """YAML-based configuration provider"""

    def __init__(self, config_path: Union[str, Path]):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

    async def load_configuration(self, environment: str = "development") -> EnvironmentConfig:
        """Load YAML configuration"""
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        # Load environment-specific config
        env_config = config_data.get('environments', {}).get(environment, {})

        # Load base configuration
        base_config = config_data.get('base', {})

        # Merge configurations
        merged_config = self._merge_configs(base_config, env_config)

        return self._parse_environment_config(environment, merged_config)

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge base and environment configurations"""
        merged = base.copy()

        for key, value in override.items():
            if key == 'services':
                # Merge service lists
                merged_services = {s['name']: s for s in merged.get('services', [])}
                for service in value:
                    if service['name'] in merged_services:
                        # Update existing service
                        merged_services[service['name']].update(service)
                    else:
                        # Add new service
                        merged_services[service['name']] = service
                merged['services'] = list(merged_services.values())
            elif isinstance(value, dict) and key in merged:
                # Merge dictionaries recursively
                merged[key] = self._merge_configs(merged[key], value)
            else:
                # Override value
                merged[key] = value

        return merged

    def _parse_environment_config(self, environment: str, config_data: Dict[str, Any]) -> EnvironmentConfig:
        """Parse configuration data into EnvironmentConfig"""
        services = []
        for service_data in config_data.get('services', []):
            service_config = ServiceConfig(
                name=service_data['name'],
                service_type=service_data['service_type'],
                implementation=service_data.get('implementation'),
                lifetime=service_data.get('lifetime', 'singleton'),
                factory=service_data.get('factory'),
                tags=service_data.get('tags', []),
                configuration=service_data.get('configuration', {}),
                health_check=service_data.get('health_check'),
                dependencies=service_data.get('dependencies', []),
                condition=service_data.get('condition')
            )
            services.append(service_config)

        return EnvironmentConfig(
            name=environment,
            services=services,
            variables=config_data.get('variables', {}),
            imports=config_data.get('imports', []),
            extends=config_data.get('extends')
        )


class JsonConfigurationProvider(IServiceConfigurationProvider):
    """JSON-based configuration provider"""

    def __init__(self, config_path: Union[str, Path]):
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

    async def load_configuration(self, environment: str = "development") -> EnvironmentConfig:
        """Load JSON configuration"""
        with open(self.config_path, 'r') as f:
            config_data = json.load(f)

        env_config = config_data.get('environments', {}).get(environment, config_data)
        return self._parse_environment_config(environment, env_config)

    def _parse_environment_config(self, environment: str, config_data: Dict[str, Any]) -> EnvironmentConfig:
        """Parse JSON configuration"""
        services = []
        for service_data in config_data.get('services', []):
            service_config = ServiceConfig(**service_data)
            services.append(service_config)

        return EnvironmentConfig(
            name=environment,
            services=services,
            variables=config_data.get('variables', {}),
            imports=config_data.get('imports', [])
        )


class EnvironmentVariableProvider(IServiceConfigurationProvider):
    """Environment variable-based configuration provider"""

    def __init__(self, prefix: str = "DI_"):
        self.prefix = prefix

    async def load_configuration(self, environment: str = "development") -> EnvironmentConfig:
        """Load configuration from environment variables"""
        services = []
        variables = {}

        # Parse environment variables
        for key, value in os.environ.items():
            if key.startswith(self.prefix):
                clean_key = key[len(self.prefix):].lower()

                if clean_key.startswith('service_'):
                    # Service configuration
                    service_name = clean_key.split('_', 1)[1]
                    service_config = self._parse_service_env_var(service_name, value)
                    if service_config:
                        services.append(service_config)
                else:
                    # General variable
                    variables[clean_key] = value

        return EnvironmentConfig(
            name=environment,
            services=services,
            variables=variables
        )

    def _parse_service_env_var(self, service_name: str, config_value: str) -> Optional[ServiceConfig]:
        """Parse service configuration from environment variable"""
        try:
            config_data = json.loads(config_value)
            return ServiceConfig(
                name=service_name,
                **config_data
            )
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Invalid service configuration for {service_name}: {config_value}")
            return None


class ServiceRegistrar:
    """Handles automatic service registration from configuration"""

    def __init__(self, container: DIContainer):
        self.container = container
        self._loaded_modules = set()

    async def register_from_config(self, config_provider: IServiceConfigurationProvider,
                                  environment: str = "development") -> None:
        """Register services from configuration"""
        config = await config_provider.load_configuration(environment)

        # Load required imports
        for import_path in config.imports:
            self._load_module(import_path)

        # Register services
        for service_config in config.services:
            await self._register_service_from_config(service_config, config.variables)

        logger.info(f"Registered {len(config.services)} services for environment '{environment}'")

    async def _register_service_from_config(self, config: ServiceConfig, variables: Dict[str, Any]) -> None:
        """Register single service from configuration"""

        # Check condition
        if config.condition and not self._evaluate_condition(config.condition, variables):
            logger.debug(f"Skipping service '{config.name}' due to condition: {config.condition}")
            return

        # Resolve service type
        service_type = self._resolve_type(config.service_type)

        # Resolve implementation
        implementation = None
        if config.implementation:
            implementation = self._resolve_type(config.implementation)

        # Resolve factory
        factory = None
        if config.factory:
            factory = self._resolve_callable(config.factory)

        # Resolve health check
        health_check = None
        if config.health_check:
            health_check = self._resolve_callable(config.health_check)

        # Parse lifetime
        lifetime = ServiceLifetime(config.lifetime)

        # Substitute variables in configuration
        resolved_config = self._substitute_variables(config.configuration, variables)

        # Register service
        self.container._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime,
            name=config.name,
            factory=factory,
            tags=config.tags,
            configuration=resolved_config,
            health_check=health_check
        )

        logger.debug(f"Registered service '{config.name}' of type {service_type.__name__}")

    def _load_module(self, import_path: str) -> None:
        """Load module by import path"""
        if import_path in self._loaded_modules:
            return

        try:
            importlib.import_module(import_path)
            self._loaded_modules.add(import_path)
            logger.debug(f"Loaded module: {import_path}")
        except ImportError as e:
            logger.error(f"Failed to import module '{import_path}': {e}")
            raise

    def _resolve_type(self, type_path: str) -> Type:
        """Resolve type from string path"""
        module_path, class_name = type_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)

    def _resolve_callable(self, callable_path: str) -> Callable:
        """Resolve callable from string path"""
        module_path, func_name = callable_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    def _evaluate_condition(self, condition: str, variables: Dict[str, Any]) -> bool:
        """Evaluate registration condition"""
        # Simple condition evaluation
        # In production, use a more sophisticated expression evaluator
        try:
            # Replace variables in condition
            for key, value in variables.items():
                condition = condition.replace(f"${{{key}}}", repr(value))

            # Evaluate expression
            return bool(eval(condition))
        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False

    def _substitute_variables(self, config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variables in configuration"""
        result = {}

        for key, value in config.items():
            if isinstance(value, str):
                # Substitute variables
                substituted = value
                for var_name, var_value in variables.items():
                    substituted = substituted.replace(f"${{{var_name}}}", str(var_value))
                result[key] = substituted
            elif isinstance(value, dict):
                result[key] = self._substitute_variables(value, variables)
            elif isinstance(value, list):
                result[key] = [
                    self._substitute_variables(item, variables) if isinstance(item, dict)
                    else item for item in value
                ]
            else:
                result[key] = value

        return result


class ServiceDiscovery:
    """Automatic service discovery and registration"""

    def __init__(self, container: DIContainer):
        self.container = container

    async def discover_and_register(self, packages: List[str],
                                   service_marker: str = "__service__",
                                   auto_register: bool = True) -> List[str]:
        """Discover and register services from packages"""
        discovered_services = []

        for package in packages:
            services = await self._discover_services_in_package(package, service_marker)
            discovered_services.extend(services)

            if auto_register:
                for service_info in services:
                    await self._auto_register_service(service_info)

        logger.info(f"Discovered {len(discovered_services)} services")
        return discovered_services

    async def _discover_services_in_package(self, package: str, marker: str) -> List[Dict[str, Any]]:
        """Discover services in package"""
        services = []

        try:
            module = importlib.import_module(package)

            # Scan module for services
            for name in dir(module):
                obj = getattr(module, name)

                if inspect.isclass(obj) and hasattr(obj, marker):
                    service_info = getattr(obj, marker)
                    if isinstance(service_info, dict):
                        service_info['implementation'] = obj
                        service_info['name'] = service_info.get('name', name)
                        services.append(service_info)

        except ImportError as e:
            logger.warning(f"Failed to discover services in package '{package}': {e}")

        return services

    async def _auto_register_service(self, service_info: Dict[str, Any]) -> None:
        """Auto-register discovered service"""
        implementation = service_info['implementation']
        name = service_info['name']

        # Determine service type (use first interface or implementation itself)
        service_type = implementation

        # Get base classes that look like interfaces
        for base in implementation.__mro__[1:]:  # Skip self
            if base.__name__.startswith('I') and hasattr(base, '__abstractmethods__'):
                service_type = base
                break

        # Register service
        self.container.register_singleton(
            service_type=service_type,
            implementation=implementation,
            name=name,
            tags=service_info.get('tags', []),
            configuration=service_info.get('configuration', {})
        )

        logger.debug(f"Auto-registered service '{name}' of type {service_type.__name__}")


# Decorators for service marking
def service(name: Optional[str] = None, lifetime: str = "singleton",
           tags: Optional[List[str]] = None, configuration: Optional[Dict[str, Any]] = None):
    """Decorator to mark class as a service"""
    def decorator(cls):
        cls.__service__ = {
            'name': name or cls.__name__,
            'lifetime': lifetime,
            'tags': tags or [],
            'configuration': configuration or {}
        }
        return cls
    return decorator


def singleton(name: Optional[str] = None, tags: Optional[List[str]] = None,
             configuration: Optional[Dict[str, Any]] = None):
    """Mark class as singleton service"""
    return service(name, "singleton", tags, configuration)


def transient(name: Optional[str] = None, tags: Optional[List[str]] = None,
             configuration: Optional[Dict[str, Any]] = None):
    """Mark class as transient service"""
    return service(name, "transient", tags, configuration)


def scoped(name: Optional[str] = None, tags: Optional[List[str]] = None,
          configuration: Optional[Dict[str, Any]] = None):
    """Mark class as scoped service"""
    return service(name, "scoped", tags, configuration)


# Real Estate Specific Service Registration Helpers
class RealEstateServiceRegistrar:
    """Real estate domain-specific service registration helpers"""

    def __init__(self, container: DIContainer):
        self.container = container

    async def register_property_services(self, config: Dict[str, Any]) -> None:
        """Register all property-related services"""

        # Register repositories based on configuration
        await self._register_repositories(config.get('repositories', {}))

        # Register scoring services
        await self._register_scoring_services(config.get('scoring', {}))

        # Register caching services
        await self._register_caching_services(config.get('caching', {}))

        # Register monitoring services
        await self._register_monitoring_services(config.get('monitoring', {}))

    async def _register_repositories(self, config: Dict[str, Any]) -> None:
        """Register repository services"""
        from ..repositories.interfaces import IPropertyRepository
        from ..repositories.repository_factory import RepositoryFactory

        # Register repository factory as singleton
        self.container.register_singleton(
            RepositoryFactory,
            name="RepositoryFactory",
            tags=["repository", "factory"]
        )

        # Register specific repositories based on config
        for repo_name, repo_config in config.items():
            await self._register_single_repository(repo_name, repo_config)

    async def _register_single_repository(self, name: str, config: Dict[str, Any]) -> None:
        """Register single repository service"""
        from ..repositories.interfaces import IPropertyRepository

        def repository_factory(factory: 'RepositoryFactory') -> IPropertyRepository:
            import asyncio
            return asyncio.run(factory.create(
                repository_type=config['type'],
                config=config.get('config', {}),
                enable_caching=config.get('enable_caching', True),
                cache_config=config.get('cache_config', {})
            ))

        self.container.register_singleton(
            IPropertyRepository,
            name=name,
            factory=repository_factory,
            tags=["repository", config.get('type', 'unknown')],
            configuration=config
        )

    async def _register_scoring_services(self, config: Dict[str, Any]) -> None:
        """Register scoring strategy services"""
        # Implementation would register Strategy Pattern services
        pass

    async def _register_caching_services(self, config: Dict[str, Any]) -> None:
        """Register caching services"""
        # Register cache backends
        if config.get('redis', {}).get('enabled', False):
            from ..repositories.caching_repository import RedisCacheBackend

            redis_config = config['redis']
            self.container.register_singleton(
                RedisCacheBackend,
                name="RedisCacheBackend",
                tags=["cache", "redis"],
                configuration=redis_config
            )

    async def _register_monitoring_services(self, config: Dict[str, Any]) -> None:
        """Register monitoring and health check services"""
        # Implementation would register monitoring services
        pass