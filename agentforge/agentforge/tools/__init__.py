"""Tools module for AgentForge.

This module provides tool definitions and utilities:
- BaseTool: Abstract base class for tools
- @tool decorator: Easy function-to-tool conversion
- FunctionTool: Automatic schema generation from functions
- ToolRegistry: Central registry for managing tools
- Schema utilities: JSON Schema generation and validation
- MCP integration: Connect to MCP servers and use their tools

Example:
    ```python
    from agentforge.tools import tool, ToolRegistry

    @tool(description="Search for information")
    async def search(query: str, limit: int = 10) -> str:
        '''Search for information on the web.'''
        return f"Results for: {query}"

    # Use with registry
    registry = ToolRegistry()
    registry.register(search)

    # Export for LLM providers
    openai_tools = registry.to_openai_tools()
    anthropic_tools = registry.to_anthropic_tools()

    # Execute
    result = await registry.execute("search", query="hello")
    ```

MCP Example:
    ```python
    from agentforge.tools import MCPToolRegistry, MCPConfig

    registry = MCPToolRegistry()
    tools = await registry.register_mcp_server(
        config=MCPConfig(command="python", args=["-m", "my_mcp_server"]),
        prefix="mcp"
    )
    ```

MCP Server Exporter Example:
    ```python
    from agentforge.tools import MCPServerExporter, create_mcp_server

    # Create and run an MCP server exposing agents
    server = create_mcp_server(agents=[my_agent], name="my-server")
    server.run_stdio()
    ```
"""

# Base classes and decorator
from agentforge.tools.base import (
    BaseTool,
    FunctionTool,
    ToolConfig,
    ToolExecutionError,
    ToolMeta,
    ToolSchema,
    tool,
)

# Schema generation utilities
from agentforge.tools.function import (
    create_pydantic_model_from_function,
    generate_tool_schema,
    merge_schemas,
    python_type_to_json_schema,
    validate_tool_input,
)

# MCP integration
from agentforge.tools.mcp import (
    # Server exporter
    AgentWrapperTool,
    MCPConfig,
    MCPServerExporter,
    MCPTool,
    MCPToolAdapter,
    MCPToolRegistry,
    create_mcp_server,
    discover_mcp_tools,
    register_mcp_tools,
    run_mcp_server,
)

# Registry
from agentforge.tools.registry import (
    ToolNotFoundError,
    ToolRegistry,
    clear_global_registry,
    get_global_registry,
    get_tool,
    register_tool,
    unregister_tool,
)

__all__ = [
    # Base classes
    "BaseTool",
    "FunctionTool",
    "ToolMeta",
    "ToolConfig",
    "ToolSchema",
    "ToolExecutionError",
    # Decorator
    "tool",
    # Schema utilities
    "python_type_to_json_schema",
    "generate_tool_schema",
    "create_pydantic_model_from_function",
    "validate_tool_input",
    "merge_schemas",
    # Registry
    "ToolRegistry",
    "ToolNotFoundError",
    "register_tool",
    "unregister_tool",
    "get_tool",
    "get_global_registry",
    "clear_global_registry",
    # MCP integration
    "MCPConfig",
    "MCPTool",
    "MCPToolAdapter",
    "MCPToolRegistry",
    "discover_mcp_tools",
    "register_mcp_tools",
    # MCP server exporter
    "AgentWrapperTool",
    "MCPServerExporter",
    "create_mcp_server",
    "run_mcp_server",
]
