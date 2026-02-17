"""Plugin base classes for AgentForge.

This module provides the abstract base classes and context for creating
AgentForge plugins that can be discovered and loaded via Python entry points.

Example:
    ```python
    from agentforge.ext import AgentForgePlugin, PluginMetadata, AgentForgeContext

    class MyPlugin(AgentForgePlugin):
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="my_plugin",
                version="1.0.0",
                description="My custom plugin",
            )

        def on_load(self, context: AgentForgeContext) -> None:
            context.register_tool("my_tool", my_tool_function)
    ```
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class PluginMetadata(BaseModel):
    """Metadata for a plugin.

    Attributes:
        name: Unique identifier for the plugin.
        version: Semantic version string.
        description: Human-readable description.
        author: Plugin author name.
        license: License identifier (e.g., "MIT", "Apache-2.0").
        dependencies: List of required package names.
        provides: List of capabilities this plugin provides (e.g., "tools:search").
    """

    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    license: str = "MIT"
    dependencies: list[str] = Field(default_factory=list)
    provides: list[str] = Field(default_factory=list)


class AgentForgeContext:
    """Context provided to plugins for registration.

    This class serves as the interface between plugins and the AgentForge
    framework, allowing plugins to register tools, agents, providers, and hooks.

    Attributes:
        _tools: Registry of registered tools.
        _agents: Registry of registered agents.
        _providers: Registry of registered providers.
        _hooks: Registry of event hooks.
    """

    def __init__(self) -> None:
        """Initialize the plugin context with empty registries."""
        self._tools: dict[str, Any] = {}
        self._agents: dict[str, Any] = {}
        self._providers: dict[str, Any] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def register_tool(self, name: str, tool: Any) -> None:
        """Register a tool.

        Args:
            name: Unique name for the tool.
            tool: Tool instance or callable.
        """
        self._tools[name] = tool

    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent.

        Args:
            name: Unique name for the agent.
            agent: Agent instance.
        """
        self._agents[name] = agent

    def register_provider(self, name: str, provider: Any) -> None:
        """Register a provider (LLM, memory, etc.).

        Args:
            name: Unique name for the provider.
            provider: Provider instance.
        """
        self._providers[name] = provider

    def register_hook(self, event: str, handler: Callable) -> None:
        """Register a hook for an event.

        Args:
            event: Event name (e.g., "agent.execute", "tool.execute").
            handler: Callable to handle the event.
        """
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(handler)

    def get_tool(self, name: str) -> Any | None:
        """Get a registered tool by name.

        Args:
            name: Tool name to look up.

        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)

    def get_agent(self, name: str) -> Any | None:
        """Get a registered agent by name.

        Args:
            name: Agent name to look up.

        Returns:
            Agent instance or None if not found.
        """
        return self._agents.get(name)

    def get_provider(self, name: str) -> Any | None:
        """Get a registered provider by name.

        Args:
            name: Provider name to look up.

        Returns:
            Provider instance or None if not found.
        """
        return self._providers.get(name)

    def get_hooks(self, event: str) -> list[Callable]:
        """Get hooks for an event.

        Args:
            event: Event name to get hooks for.

        Returns:
            List of registered handlers for the event.
        """
        return self._hooks.get(event, [])

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def list_agents(self) -> list[str]:
        """List all registered agent names.

        Returns:
            List of agent names.
        """
        return list(self._agents.keys())

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names.
        """
        return list(self._providers.keys())

    def list_hooks(self) -> list[str]:
        """List all registered hook events.

        Returns:
            List of event names that have hooks registered.
        """
        return list(self._hooks.keys())

    def clear(self) -> None:
        """Clear all registrations. Useful for testing."""
        self._tools.clear()
        self._agents.clear()
        self._providers.clear()
        self._hooks.clear()


class AgentForgePlugin(ABC):
    """Abstract base class for AgentForge plugins.

    All plugins must inherit from this class and implement the required
    abstract methods. Plugins are discovered via Python entry points
    and loaded by the PluginManager.

    Example:
        ```python
        class MyPlugin(AgentForgePlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(name="my_plugin")

            def on_load(self, context: AgentForgeContext) -> None:
                context.register_tool("greet", lambda: "Hello!")
        ```
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata.

        Returns:
            PluginMetadata instance with plugin information.
        """
        ...

    @abstractmethod
    def on_load(self, context: AgentForgeContext) -> None:
        """Called when the plugin is loaded.

        Plugins should register their tools, agents, providers, and hooks
        in this method.

        Args:
            context: Plugin context for registration.
        """
        ...

    def on_unload(self) -> None:
        """Called when the plugin is unloaded.

        Override this method to cleanup resources when the plugin is unloaded.
        The default implementation does nothing.
        """
        return None

    def on_config_change(self, config: dict[str, Any]) -> None:
        """Called when configuration changes.

        Override this method to handle configuration updates.

        Args:
            config: New configuration dictionary.
        """
        return None
