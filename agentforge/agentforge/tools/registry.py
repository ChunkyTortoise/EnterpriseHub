"""Tool registry for AgentForge.

This module provides a registry for managing tools, including registration,
lookup, and execution capabilities. Supports both OpenAI and Anthropic
tool format exports.
"""

from typing import Any

from agentforge.tools.base import BaseTool


class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found in the registry.

    Attributes:
        tool_name: Name of the tool that was not found.
    """

    def __init__(self, tool_name: str) -> None:
        """Initialize the exception.

        Args:
            tool_name: Name of the tool that was not found.
        """
        self.tool_name = tool_name
        super().__init__(f"Tool not found: {tool_name}")


class ToolRegistry:
    """Registry for managing tools.

    Provides a central location for tool registration, lookup,
    and execution. Supports exporting tools in multiple LLM
    provider formats.

    Attributes:
        _tools: Dictionary mapping tool names to tool instances.

    Example:
        ```python
        registry = ToolRegistry()

        @tool
        def search(query: str) -> str:
            '''Search for information.'''
            return f"Results for: {query}"

        registry.register(search)

        # Export for OpenAI
        openai_tools = registry.to_openai_tools()

        # Execute a tool
        result = await registry.execute("search", query="hello")
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: The tool to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry.

        Args:
            name: Name of the tool to remove.

        Raises:
            ToolNotFoundError: If the tool is not found.
        """
        if name not in self._tools:
            raise ToolNotFoundError(name)
        del self._tools[name]

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool instance, or None if not found.
        """
        return self._tools.get(name)

    def get_required(self, name: str) -> BaseTool:
        """Get a tool by name, raising an error if not found.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool instance.

        Raises:
            ToolNotFoundError: If the tool is not found.
        """
        tool = self.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        return tool

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return list(self._tools.keys())

    def list_tool_schemas(self) -> list[dict[str, Any]]:
        """List schemas for all registered tools.

        Returns:
            List of tool schema dictionaries.
        """
        return [tool.get_schema() for tool in self._tools.values()]

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Export all tools in OpenAI format.

        Returns:
            List of OpenAI-compatible tool definitions.
        """
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def to_anthropic_tools(self) -> list[dict[str, Any]]:
        """Export all tools in Anthropic format.

        Returns:
            List of Anthropic-compatible tool definitions.
        """
        return [tool.to_anthropic_tool() for tool in self._tools.values()]

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool by name with the given arguments.

        Args:
            name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool.

        Returns:
            Tool execution result.

        Raises:
            ToolNotFoundError: If the tool is not found.
            ToolExecutionError: If execution fails.
        """
        tool = self.get(name)
        if tool is None:
            raise ToolNotFoundError(name)
        return await tool.execute(**kwargs)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Name of the tool to check.

        Returns:
            True if the tool is registered, False otherwise.
        """
        return name in self._tools

    def __len__(self) -> int:
        """Get the number of registered tools.

        Returns:
            Number of registered tools.
        """
        return len(self._tools)

    def __iter__(self):
        """Iterate over registered tool names.

        Yields:
            Tool names.
        """
        return iter(self._tools)

    def items(self):
        """Iterate over tool name, tool pairs.

        Yields:
            Tuples of (name, tool).
        """
        return self._tools.items()

    def values(self):
        """Iterate over registered tools.

        Yields:
            Tool instances.
        """
        return self._tools.values()

    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()


# Global registry instance
_global_registry = ToolRegistry()


def register_tool(tool: BaseTool) -> None:
    """Register a tool in the global registry.

    Args:
        tool: The tool to register.
    """
    _global_registry.register(tool)


def unregister_tool(name: str) -> None:
    """Remove a tool from the global registry.

    Args:
        name: Name of the tool to remove.
    """
    _global_registry.unregister(name)


def get_tool(name: str) -> BaseTool | None:
    """Get a tool from the global registry.

    Args:
        name: Name of the tool to retrieve.

    Returns:
        The tool instance, or None if not found.
    """
    return _global_registry.get(name)


def get_global_registry() -> ToolRegistry:
    """Get the global tool registry.

    Returns:
        The global ToolRegistry instance.
    """
    return _global_registry


def clear_global_registry() -> None:
    """Clear all tools from the global registry."""
    _global_registry.clear()


__all__ = [
    "ToolNotFoundError",
    "ToolRegistry",
    "register_tool",
    "unregister_tool",
    "get_tool",
    "get_global_registry",
    "clear_global_registry",
]
