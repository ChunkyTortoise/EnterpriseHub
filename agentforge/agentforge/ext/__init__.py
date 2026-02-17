"""Extension point for AgentForge plugins.

This module provides hooks for extending AgentForge with custom
functionality without modifying the core framework.

Extension points:
- Agent types: Register custom agent implementations
- Tool types: Register custom tool implementations
- Memory backends: Register custom storage backends
- LLM providers: Register custom LLM integrations
- Observability: Register custom tracers/metrics

Plugin System:
- AgentForgePlugin: Abstract base class for plugins
- PluginMetadata: Metadata model for plugins
- AgentForgeContext: Context for plugin registration
- PluginManager: Discovers and manages plugins via entry points

Example (Decorator-based registration):
    ```python
    from agentforge.ext import register_agent_type, register_tool_type

    @register_agent_type("custom")
    class CustomAgent(BaseAgent):
        ...

    @register_tool_type("custom")
    class CustomTool(BaseTool):
        ...
    ```

Example (Plugin-based extension):
    ```python
    from agentforge.ext import AgentForgePlugin, PluginMetadata, AgentForgeContext

    class MyPlugin(AgentForgePlugin):
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(name="my_plugin")

        def on_load(self, context: AgentForgeContext) -> None:
            context.register_tool("my_tool", my_tool_function)
    ```
"""

from collections.abc import Callable

# Base classes for plugin system
from agentforge.ext.base import (
    AgentForgeContext,
    AgentForgePlugin,
    PluginMetadata,
)

# Built-in plugins
from agentforge.ext.builtins import (
    LoggingPlugin,
    MetricsPlugin,
    TimingPlugin,
)

# Plugin manager
from agentforge.ext.manager import (
    PluginLoadError,
    PluginManager,
    PluginNotFoundError,
)

# Registry for extension types (legacy decorator-based registration)
_agent_types: dict[str, type] = {}
_tool_types: dict[str, type] = {}
_memory_backends: dict[str, type] = {}
_llm_providers: dict[str, type] = {}


def register_agent_type(name: str) -> Callable[[type], type]:
    """Decorator to register a custom agent type.

    Args:
        name: Name for this agent type.

    Returns:
        Decorator function.

    Example:
        ```python
        @register_agent_type("react")
        class ReActAgent(BaseAgent):
            ...
        ```
    """
    def decorator(cls: type) -> type:
        _agent_types[name] = cls
        return cls
    return decorator


def register_tool_type(name: str) -> Callable[[type], type]:
    """Decorator to register a custom tool type.

    Args:
        name: Name for this tool type.

    Returns:
        Decorator function.
    """
    def decorator(cls: type) -> type:
        _tool_types[name] = cls
        return cls
    return decorator


def register_memory_backend(name: str) -> Callable[[type], type]:
    """Decorator to register a custom memory backend.

    Args:
        name: Name for this backend.

    Returns:
        Decorator function.
    """
    def decorator(cls: type) -> type:
        _memory_backends[name] = cls
        return cls
    return decorator


def register_llm_provider(name: str) -> Callable[[type], type]:
    """Decorator to register a custom LLM provider.

    Args:
        name: Name for this provider.

    Returns:
        Decorator function.
    """
    def decorator(cls: type) -> type:
        _llm_providers[name] = cls
        return cls
    return decorator


def get_agent_type(name: str) -> type | None:
    """Get a registered agent type by name."""
    return _agent_types.get(name)


def get_tool_type(name: str) -> type | None:
    """Get a registered tool type by name."""
    return _tool_types.get(name)


def get_memory_backend(name: str) -> type | None:
    """Get a registered memory backend by name."""
    return _memory_backends.get(name)


def get_llm_provider(name: str) -> type | None:
    """Get a registered LLM provider by name."""
    return _llm_providers.get(name)


def list_agent_types() -> list[str]:
    """List all registered agent types."""
    return list(_agent_types.keys())


def list_tool_types() -> list[str]:
    """List all registered tool types."""
    return list(_tool_types.keys())


def list_memory_backends() -> list[str]:
    """List all registered memory backends."""
    return list(_memory_backends.keys())


def list_llm_providers() -> list[str]:
    """List all registered LLM providers."""
    return list(_llm_providers.keys())


__all__ = [
    # Plugin system base classes
    "AgentForgePlugin",
    "PluginMetadata",
    "AgentForgeContext",
    # Plugin manager
    "PluginManager",
    "PluginLoadError",
    "PluginNotFoundError",
    # Built-in plugins
    "LoggingPlugin",
    "MetricsPlugin",
    "TimingPlugin",
    # Legacy decorator-based registration
    "register_agent_type",
    "register_tool_type",
    "register_memory_backend",
    "register_llm_provider",
    # Legacy getters
    "get_agent_type",
    "get_tool_type",
    "get_memory_backend",
    "get_llm_provider",
    # Legacy listers
    "list_agent_types",
    "list_tool_types",
    "list_memory_backends",
    "list_llm_providers",
]
