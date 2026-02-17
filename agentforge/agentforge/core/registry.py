"""Agent and tool registry for AgentForge.

This module provides a central registry for discovering and managing
agents and tools. Supports both programmatic and declarative registration.

TODO: Implement full registry functionality including:
- Agent discovery and registration
- Tool registration and lookup
- Namespace support
- Plugin loading
"""

from collections.abc import Callable
from typing import Any, Optional

from agentforge.core.agent import BaseAgent


class Registry:
    """Central registry for agents and tools.

    Provides a single point of discovery for all registered agents
    and tools in an AgentForge application.

    Attributes:
        agents: Registered agent classes by name.
        tools: Registered tool functions by name.
        instances: Cached agent instances by ID.
    """

    _instance: Optional["Registry"] = None

    def __new__(cls) -> "Registry":
        """Singleton pattern for global registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: dict[str, type[BaseAgent]] = {}
            cls._instance._tools: dict[str, Callable] = {}
            cls._instance._instances: dict[str, BaseAgent] = {}
        return cls._instance

    @classmethod
    def get_instance(cls) -> "Registry":
        """Get the global registry instance."""
        return cls()

    def register_agent(
        self,
        name: str | None = None,
        agent_class: type[BaseAgent] | None = None,
    ) -> Callable:
        """Register an agent class.

        Can be used as a decorator or called directly.

        Args:
            name: Optional name for the agent (defaults to class name).
            agent_class: The agent class to register.

        Returns:
            Decorator function or the registered class.

        Example:
            @registry.register_agent("my_agent")
            class MyAgent(BaseAgent):
                ...
        """
        def decorator(cls: type[BaseAgent]) -> type[BaseAgent]:
            agent_name = name or cls.__name__
            self._agents[agent_name] = cls
            return cls

        if agent_class is not None:
            return decorator(agent_class)
        return decorator

    def register_tool(
        self,
        name: str | None = None,
        func: Callable | None = None,
    ) -> Callable:
        """Register a tool function.

        Can be used as a decorator or called directly.

        Args:
            name: Optional name for the tool (defaults to function name).
            func: The tool function to register.

        Returns:
            Decorator function or the registered function.

        Example:
            @registry.register_tool("search")
            def search_tool(query: str) -> str:
                ...
        """
        def decorator(f: Callable) -> Callable:
            tool_name = name or f.__name__
            self._tools[tool_name] = f
            return f

        if func is not None:
            return decorator(func)
        return decorator

    def get_agent_class(self, name: str) -> type[BaseAgent] | None:
        """Get a registered agent class by name.

        Args:
            name: The agent name.

        Returns:
            The agent class if found, None otherwise.
        """
        return self._agents.get(name)

    def get_tool(self, name: str) -> Callable | None:
        """Get a registered tool function by name.

        Args:
            name: The tool name.

        Returns:
            The tool function if found, None otherwise.
        """
        return self._tools.get(name)

    def list_agents(self) -> list[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def create_agent(
        self,
        name: str,
        **kwargs: Any,
    ) -> BaseAgent | None:
        """Create an instance of a registered agent.

        Args:
            name: The agent name.
            **kwargs: Arguments to pass to the agent constructor.

        Returns:
            A new agent instance, or None if not found.
        """
        agent_class = self.get_agent_class(name)
        if agent_class is None:
            return None
        return agent_class(**kwargs)

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._agents.clear()
        self._tools.clear()
        self._instances.clear()


# Global registry instance
registry = Registry()


__all__ = ["Registry", "registry"]
