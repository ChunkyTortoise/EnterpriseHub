"""
Enterprise Dependency Injection Container

Production-ready DI Container with full lifecycle management, type safety,
and performance optimization for the GHL Real Estate AI system.
"""

import asyncio
import inspect
import logging
import threading
import weakref
from collections import defaultdict
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    Union,
)

T = TypeVar("T")
logger = logging.getLogger(__name__)


class ServiceLifetime(Enum):
    """Service lifetime management options"""

    SINGLETON = "singleton"  # Single instance for container lifetime
    TRANSIENT = "transient"  # New instance every resolution
    SCOPED = "scoped"  # Single instance per scope/request
    THREAD_LOCAL = "thread_local"  # One instance per thread


class ServiceState(Enum):
    """Service registration state"""

    REGISTERED = "registered"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    DISPOSED = "disposed"


@dataclass
class ServiceMetadata:
    """Metadata about registered services"""

    name: str
    service_type: Type
    implementation: Optional[Type] = None
    lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    factory: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    configuration: Dict[str, Any] = field(default_factory=dict)
    health_check: Optional[Callable] = None
    state: ServiceState = ServiceState.REGISTERED
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    access_count: int = 0


@dataclass
class ResolverContext:
    """Context for service resolution"""

    container: "DIContainer"
    scope_id: Optional[str] = None
    resolution_stack: List[str] = field(default_factory=list)
    configuration_overrides: Dict[str, Any] = field(default_factory=dict)

    def with_override(self, service_name: str, config: Dict[str, Any]) -> "ResolverContext":
        """Create context with configuration override"""
        new_overrides = self.configuration_overrides.copy()
        new_overrides[service_name] = config
        return ResolverContext(
            container=self.container,
            scope_id=self.scope_id,
            resolution_stack=self.resolution_stack.copy(),
            configuration_overrides=new_overrides,
        )


class IServiceProvider(Protocol):
    """Service provider interface for dependency injection"""

    def get_service(self, service_type: Type[T]) -> T:
        """Get service by type"""
        ...

    async def get_service_async(self, service_type: Type[T]) -> T:
        """Get service by type asynchronously"""
        ...


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected"""

    def __init__(self, dependency_chain: List[str]):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(dependency_chain)
        super().__init__(f"Circular dependency detected: {chain_str}")


class ServiceNotFoundError(Exception):
    """Raised when requested service is not registered"""

    pass


class ServiceConfigurationError(Exception):
    """Raised when service configuration is invalid"""

    pass


class DIContainer(IServiceProvider):
    """
    Enterprise-grade Dependency Injection Container

    Features:
    - Multiple service lifetimes (Singleton, Transient, Scoped, Thread-local)
    - Automatic dependency resolution with type hints
    - Circular dependency detection
    - Configuration-driven service registration
    - Performance monitoring and health checks
    - Thread-safe operations
    - Async/await support
    - Service disposal and cleanup
    """

    def __init__(self, name: str = "default", enable_monitoring: bool = True):
        self.name = name
        self.enable_monitoring = enable_monitoring

        # Service registry
        self._services: Dict[str, ServiceMetadata] = {}
        self._instances: Dict[str, Any] = {}
        self._scoped_instances: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._thread_local_storage = threading.local()

        # Locks for thread safety
        self._registration_lock = threading.RLock()
        self._resolution_lock = threading.RLock()

        # Monitoring
        self._resolution_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._health_status: Dict[str, Dict[str, Any]] = {}

        # Lifecycle management
        self._disposed = False
        self._disposable_instances: List[weakref.ReferenceType] = []

        logger.info(f"DI Container '{name}' initialized")

    def register_singleton(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        name: Optional[str] = None,
        factory: Optional[Callable[..., T]] = None,
        tags: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
        health_check: Optional[Callable] = None,
    ) -> "DIContainer":
        """Register singleton service"""
        return self._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SINGLETON,
            name=name,
            factory=factory,
            tags=tags or [],
            configuration=configuration or {},
            health_check=health_check,
        )

    def register_transient(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        name: Optional[str] = None,
        factory: Optional[Callable[..., T]] = None,
        tags: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> "DIContainer":
        """Register transient service"""
        return self._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.TRANSIENT,
            name=name,
            factory=factory,
            tags=tags or [],
            configuration=configuration or {},
        )

    def register_scoped(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        name: Optional[str] = None,
        factory: Optional[Callable[..., T]] = None,
        tags: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> "DIContainer":
        """Register scoped service"""
        return self._register_service(
            service_type=service_type,
            implementation=implementation,
            lifetime=ServiceLifetime.SCOPED,
            name=name,
            factory=factory,
            tags=tags or [],
            configuration=configuration or {},
        )

    def register_instance(
        self, service_type: Type[T], instance: T, name: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> "DIContainer":
        """Register existing instance as singleton"""
        service_name = name or self._get_service_name(service_type)

        with self._registration_lock:
            metadata = ServiceMetadata(
                name=service_name,
                service_type=service_type,
                lifetime=ServiceLifetime.SINGLETON,
                tags=tags or [],
                state=ServiceState.READY,
            )

            self._services[service_name] = metadata
            self._instances[service_name] = instance

            logger.debug(f"Registered instance '{service_name}' of type {service_type.__name__}")
            return self

    def _register_service(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
        name: Optional[str] = None,
        factory: Optional[Callable] = None,
        tags: List[str] = None,
        configuration: Dict[str, Any] = None,
        health_check: Optional[Callable] = None,
    ) -> "DIContainer":
        """Internal service registration"""

        if factory and implementation:
            raise ServiceConfigurationError("Cannot specify both factory and implementation")

        if not factory and not implementation:
            implementation = service_type

        service_name = name or self._get_service_name(service_type)

        # Analyze dependencies
        dependencies = []
        if implementation and not factory:
            dependencies = self._analyze_dependencies(implementation)
        elif factory:
            dependencies = self._analyze_dependencies(factory)

        with self._registration_lock:
            metadata = ServiceMetadata(
                name=service_name,
                service_type=service_type,
                implementation=implementation,
                lifetime=lifetime,
                factory=factory,
                tags=tags or [],
                dependencies=dependencies,
                configuration=configuration or {},
                health_check=health_check,
                state=ServiceState.REGISTERED,
            )

            self._services[service_name] = metadata
            logger.debug(f"Registered service '{service_name}' with lifetime {lifetime.value}")

            return self

    def get_service(
        self, service_type: Type[T], name: Optional[str] = None, scope_id: Optional[str] = None, **kwargs
    ) -> T:
        """Get service synchronously"""
        return asyncio.run(self.get_service_async(service_type, name, scope_id, **kwargs))

    async def get_service_async(
        self, service_type: Type[T], name: Optional[str] = None, scope_id: Optional[str] = None, **kwargs
    ) -> T:
        """Get service asynchronously"""
        if self._disposed:
            raise RuntimeError("Container has been disposed")

        service_name = name or self._get_service_name(service_type)

        context = ResolverContext(container=self, scope_id=scope_id, configuration_overrides=kwargs)

        return await self._resolve_service(service_name, context)

    async def _resolve_service(self, service_name: str, context: ResolverContext) -> Any:
        """Internal service resolution with circular dependency detection"""

        # Check for circular dependency
        if service_name in context.resolution_stack:
            context.resolution_stack.append(service_name)
            raise CircularDependencyError(context.resolution_stack)

        if service_name not in self._services:
            raise ServiceNotFoundError(f"Service '{service_name}' is not registered")

        metadata = self._services[service_name]
        context.resolution_stack.append(service_name)

        try:
            # Update access metrics
            if self.enable_monitoring:
                metadata.last_accessed = datetime.utcnow()
                metadata.access_count += 1

            # Resolve based on lifetime
            instance = await self._resolve_by_lifetime(metadata, context)

            return instance

        finally:
            context.resolution_stack.pop()

    async def _resolve_by_lifetime(self, metadata: ServiceMetadata, context: ResolverContext) -> Any:
        """Resolve service based on its lifetime"""

        if metadata.lifetime == ServiceLifetime.SINGLETON:
            return await self._resolve_singleton(metadata, context)
        elif metadata.lifetime == ServiceLifetime.TRANSIENT:
            return await self._create_instance(metadata, context)
        elif metadata.lifetime == ServiceLifetime.SCOPED:
            return await self._resolve_scoped(metadata, context)
        elif metadata.lifetime == ServiceLifetime.THREAD_LOCAL:
            return await self._resolve_thread_local(metadata, context)
        else:
            raise ServiceConfigurationError(f"Unknown lifetime: {metadata.lifetime}")

    async def _resolve_singleton(self, metadata: ServiceMetadata, context: ResolverContext) -> Any:
        """Resolve singleton service"""
        with self._resolution_lock:
            if metadata.name in self._instances:
                return self._instances[metadata.name]

            # Create new singleton instance
            instance = await self._create_instance(metadata, context)
            self._instances[metadata.name] = instance

            # Track disposable instances
            if hasattr(instance, "__del__") or hasattr(instance, "dispose"):
                self._disposable_instances.append(weakref.ref(instance))

            metadata.state = ServiceState.READY
            return instance

    async def _resolve_scoped(self, metadata: ServiceMetadata, context: ResolverContext) -> Any:
        """Resolve scoped service"""
        scope_id = context.scope_id or "default"

        if metadata.name in self._scoped_instances[scope_id]:
            return self._scoped_instances[scope_id][metadata.name]

        # Create new scoped instance
        instance = await self._create_instance(metadata, context)
        self._scoped_instances[scope_id][metadata.name] = instance

        return instance

    async def _resolve_thread_local(self, metadata: ServiceMetadata, context: ResolverContext) -> Any:
        """Resolve thread-local service"""
        thread_storage = getattr(self._thread_local_storage, "instances", None)
        if thread_storage is None:
            thread_storage = {}
            self._thread_local_storage.instances = thread_storage

        if metadata.name in thread_storage:
            return thread_storage[metadata.name]

        # Create new thread-local instance
        instance = await self._create_instance(metadata, context)
        thread_storage[metadata.name] = instance

        return instance

    async def _create_instance(self, metadata: ServiceMetadata, context: ResolverContext) -> Any:
        """Create new service instance"""
        metadata.state = ServiceState.INITIALIZING

        try:
            # Merge configuration
            config = metadata.configuration.copy()
            if metadata.name in context.configuration_overrides:
                config.update(context.configuration_overrides[metadata.name])

            if metadata.factory:
                # Use factory function
                instance = await self._invoke_factory(metadata.factory, context, config)
            else:
                # Use constructor
                instance = await self._invoke_constructor(metadata.implementation, context, config)

            # Run health check if available
            if metadata.health_check:
                health_result = await self._run_health_check(metadata.health_check, instance)
                if not health_result.get("healthy", True):
                    raise ServiceConfigurationError(f"Health check failed for {metadata.name}: {health_result}")

            metadata.state = ServiceState.READY
            return instance

        except Exception as e:
            metadata.state = ServiceState.ERROR
            logger.error(f"Failed to create instance of '{metadata.name}': {e}")
            raise

    async def _invoke_factory(self, factory: Callable, context: ResolverContext, config: Dict[str, Any]) -> Any:
        """Invoke factory function with dependency injection"""
        # Get factory signature
        sig = inspect.signature(factory)
        args = {}

        for param_name, param in sig.parameters.items():
            if param_name == "config" or param_name == "configuration":
                args[param_name] = config
            elif param.annotation != inspect.Parameter.empty:
                # Resolve dependency by type
                dependency = await self._resolve_service(self._get_service_name(param.annotation), context)
                args[param_name] = dependency

        # Invoke factory
        if asyncio.iscoroutinefunction(factory):
            return await factory(**args)
        else:
            return factory(**args)

    async def _invoke_constructor(self, implementation: Type, context: ResolverContext, config: Dict[str, Any]) -> Any:
        """Invoke constructor with dependency injection"""
        if not implementation:
            raise ServiceConfigurationError("No implementation specified")

        # Get constructor signature
        sig = inspect.signature(implementation.__init__)
        args = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            elif param_name in ["config", "configuration"]:
                args[param_name] = config
            elif param.annotation != inspect.Parameter.empty:
                # Resolve dependency by type
                dependency = await self._resolve_service(self._get_service_name(param.annotation), context)
                args[param_name] = dependency

        return implementation(**args)

    async def _run_health_check(self, health_check: Callable, instance: Any) -> Dict[str, Any]:
        """Run health check on service instance"""
        try:
            if asyncio.iscoroutinefunction(health_check):
                result = await health_check(instance)
            else:
                result = health_check(instance)

            if isinstance(result, bool):
                return {"healthy": result}
            elif isinstance(result, dict):
                return result
            else:
                return {"healthy": True, "details": str(result)}

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    def _analyze_dependencies(self, target: Union[Type, Callable]) -> List[str]:
        """Analyze dependencies from type hints"""
        dependencies = []

        try:
            if inspect.isclass(target):
                sig = inspect.signature(target.__init__)
            else:
                sig = inspect.signature(target)

            for param_name, param in sig.parameters.items():
                if param_name in ["self", "config", "configuration"]:
                    continue

                if param.annotation != inspect.Parameter.empty:
                    dep_name = self._get_service_name(param.annotation)
                    dependencies.append(dep_name)

        except Exception as e:
            logger.warning(f"Failed to analyze dependencies for {target}: {e}")

        return dependencies

    def _get_service_name(self, service_type: Type) -> str:
        """Generate service name from type"""
        if hasattr(service_type, "__name__"):
            return service_type.__name__
        else:
            return str(service_type)

    @contextmanager
    def create_scope(self, scope_id: Optional[str] = None):
        """Create dependency injection scope"""
        scope_id = scope_id or f"scope_{datetime.utcnow().timestamp()}"

        try:
            yield scope_id
        finally:
            # Cleanup scoped instances
            if scope_id in self._scoped_instances:
                for instance in self._scoped_instances[scope_id].values():
                    self._dispose_instance(instance)
                del self._scoped_instances[scope_id]

    @asynccontextmanager
    async def create_scope_async(self, scope_id: Optional[str] = None):
        """Create dependency injection scope asynchronously"""
        scope_id = scope_id or f"scope_{datetime.utcnow().timestamp()}"

        try:
            yield scope_id
        finally:
            # Cleanup scoped instances
            if scope_id in self._scoped_instances:
                for instance in self._scoped_instances[scope_id].values():
                    await self._dispose_instance_async(instance)
                del self._scoped_instances[scope_id]

    def get_services_by_tag(self, tag: str) -> List[Any]:
        """Get all services with specific tag"""
        services = []
        for metadata in self._services.values():
            if tag in metadata.tags:
                service = self.get_service(metadata.service_type, metadata.name)
                services.append(service)
        return services

    def is_registered(self, service_type: Type, name: Optional[str] = None) -> bool:
        """Check if service is registered"""
        service_name = name or self._get_service_name(service_type)
        return service_name in self._services

    def get_registration_info(self, service_type: Type, name: Optional[str] = None) -> Optional[ServiceMetadata]:
        """Get service registration metadata"""
        service_name = name or self._get_service_name(service_type)
        return self._services.get(service_name)

    def get_health_status(self) -> Dict[str, Any]:
        """Get container health status"""
        if not self.enable_monitoring:
            return {"monitoring_disabled": True}

        health_data = {
            "container_name": self.name,
            "total_services": len(self._services),
            "ready_services": sum(1 for s in self._services.values() if s.state == ServiceState.READY),
            "error_services": sum(1 for s in self._services.values() if s.state == ServiceState.ERROR),
            "singleton_instances": len(self._instances),
            "scoped_instances": sum(len(scope) for scope in self._scoped_instances.values()),
            "last_check": datetime.utcnow().isoformat(),
            "services": {},
        }

        for name, metadata in self._services.items():
            health_data["services"][name] = {
                "state": metadata.state.value,
                "lifetime": metadata.lifetime.value,
                "access_count": metadata.access_count,
                "last_accessed": metadata.last_accessed.isoformat() if metadata.last_accessed else None,
            }

        return health_data

    def _dispose_instance(self, instance: Any):
        """Dispose instance synchronously"""
        try:
            if hasattr(instance, "dispose") and callable(instance.dispose):
                instance.dispose()
            elif hasattr(instance, "__del__") and callable(instance.__del__):
                instance.__del__()
        except Exception as e:
            logger.error(f"Error disposing instance: {e}")

    async def _dispose_instance_async(self, instance: Any):
        """Dispose instance asynchronously"""
        try:
            if hasattr(instance, "dispose_async") and callable(instance.dispose_async):
                await instance.dispose_async()
            elif hasattr(instance, "dispose") and callable(instance.dispose):
                instance.dispose()
        except Exception as e:
            logger.error(f"Error disposing instance: {e}")

    def dispose(self):
        """Dispose container and all managed instances"""
        if self._disposed:
            return

        self._disposed = True

        # Dispose all instances
        for instance in self._instances.values():
            self._dispose_instance(instance)

        for scope in self._scoped_instances.values():
            for instance in scope.values():
                self._dispose_instance(instance)

        # Cleanup
        self._instances.clear()
        self._scoped_instances.clear()
        self._services.clear()

        logger.info(f"DI Container '{self.name}' disposed")

    async def dispose_async(self):
        """Dispose container asynchronously"""
        if self._disposed:
            return

        self._disposed = True

        # Dispose all instances
        for instance in self._instances.values():
            await self._dispose_instance_async(instance)

        for scope in self._scoped_instances.values():
            for instance in scope.values():
                await self._dispose_instance_async(instance)

        # Cleanup
        self._instances.clear()
        self._scoped_instances.clear()
        self._services.clear()

        logger.info(f"DI Container '{self.name}' disposed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.dispose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.dispose_async()
