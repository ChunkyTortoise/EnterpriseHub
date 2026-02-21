"""MCP (Model Context Protocol) integration for AgentForge.

This module provides tools for connecting to MCP servers and using their
tools within the AgentForge framework. MCP is a protocol for connecting
AI systems to external tools and data sources.

Example:
    ```python
    from agentforge.tools.mcp import MCPToolAdapter, MCPConfig

    # Connect to an MCP server via stdio
    config = MCPConfig(command="python", args=["my_mcp_server.py"])
    adapter = MCPToolAdapter(config)
    tools = await adapter.discover_tools()

    # Use the tools
    for tool in tools:
        result = await tool.execute(param1="value1")
    ```

Server Exporter Example:
    ```python
    from agentforge.tools.mcp import MCPServerExporter, create_mcp_server

    # Create and run an MCP server exposing agents
    exporter = create_mcp_server(agents=[my_agent], name="my-server")
    exporter.run_stdio()
    ```
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from agentforge.core.exceptions import MCPError
from agentforge.tools.base import BaseTool, ToolConfig

if TYPE_CHECKING:
    from mcp import ClientSession

    from agentforge.core.agent import BaseAgent

logger = logging.getLogger(__name__)


class MCPConfig(BaseModel):
    """Configuration for MCP connection.

    Supports both stdio and HTTP transports for connecting to MCP servers.

    Attributes:
        server_url: URL for Streamable HTTP transport (e.g., "http://localhost:8080/mcp").
        command: Command to run for stdio transport (e.g., "python", "node").
        args: Arguments for the command.
        env: Environment variables to set for the subprocess.
        timeout: Timeout in seconds for operations (default: 30.0).

    Example:
        ```python
        # Stdio transport
        config = MCPConfig(
            command="python",
            args=["-m", "my_mcp_server"],
            env={"DEBUG": "1"}
        )

        # HTTP transport
        config = MCPConfig(
            server_url="http://localhost:8080/mcp",
            timeout=60.0
        )
        ```
    """

    model_config = ConfigDict(extra="forbid")

    server_url: str | None = None
    command: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    timeout: float = Field(default=30.0, ge=0.1, le=3600.0)

    def get_server_identifier(self) -> str:
        """Get a human-readable identifier for the server.

        Returns:
            Server URL or command string for identification.
        """
        if self.server_url:
            return self.server_url
        if self.command:
            cmd = self.command
            if self.args:
                cmd = f"{cmd} {' '.join(self.args)}"
            return cmd
        return "unknown"


class MCPTool(BaseTool):
    """A tool that calls an MCP server.

    Wraps an MCP server tool as an AgentForge tool, allowing seamless
    integration with the AgentForge tool system.

    Attributes:
        _name: Tool name from the MCP server.
        _description: Tool description from the MCP server.
        _schema: JSON Schema for the tool's parameters.
        _adapter: Reference to the parent adapter for making calls.
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters_schema: dict[str, Any],
        adapter: MCPToolAdapter,
    ) -> None:
        """Initialize the MCP tool.

        Args:
            name: Tool name from the MCP server.
            description: Tool description from the MCP server.
            parameters_schema: JSON Schema for the tool's parameters.
            adapter: Reference to the parent MCPToolAdapter.
        """
        self._name = name
        self._description = description
        self._schema = parameters_schema
        self._adapter = adapter

        # Create a minimal config for BaseTool
        config = ToolConfig(
            name=name,
            description=description,
            timeout=adapter.config.timeout,
        )
        # Bypass BaseTool's __init__ since we have our own setup
        self.config = config
        self._schema_cache: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self._name

    @property
    def description(self) -> str:
        """Get the tool description."""
        return self._description

    def get_parameters_schema(self) -> dict[str, Any]:
        """Get the JSON Schema for the tool's parameters.

        Returns:
            JSON Schema dictionary for the parameters.
        """
        return self._schema

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the MCP tool with the given arguments.

        Args:
            **kwargs: Arguments to pass to the MCP tool.

        Returns:
            Tool execution result from the MCP server.

        Raises:
            MCPError: If the tool execution fails.
        """
        return await self._adapter.call_tool(self._name, kwargs)

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI tool format.

        Returns:
            OpenAI-compatible tool definition.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic tool format.

        Returns:
            Anthropic-compatible tool definition.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_parameters_schema(),
        }


class MCPToolAdapter:
    """Wraps an MCP server's tools as AgentForge tools.

    Handles connection management, tool discovery, and execution for
    MCP servers. Supports both stdio and HTTP transports.

    Attributes:
        config: MCP connection configuration.
        _session: Active MCP client session (if connected).
        _tools: Cache of discovered tools.

    Example:
        ```python
        config = MCPConfig(command="python", args=["server.py"])
        adapter = MCPToolAdapter(config)

        async with adapter:
            tools = await adapter.discover_tools()
            result = await adapter.call_tool("search", {"query": "hello"})
        ```
    """

    def __init__(self, config: MCPConfig) -> None:
        """Initialize the MCP tool adapter.

        Args:
            config: MCP connection configuration.
        """
        self.config = config
        self._session: ClientSession | None = None
        self._tools: dict[str, MCPTool] = {}
        self._connection_context: Any | None = None
        self._read_stream: Any | None = None
        self._write_stream: Any | None = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Check if the adapter is connected to an MCP server."""
        return self._connected and self._session is not None

    async def connect(self) -> None:
        """Connect to the MCP server.

        Automatically chooses stdio or HTTP transport based on config.

        Raises:
            MCPError: If connection fails.
            ImportError: If the 'mcp' package is not installed.
        """
        if self._connected:
            logger.debug("Already connected to MCP server")
            return

        if self.config.command:
            await self._connect_stdio()
        elif self.config.server_url:
            await self._connect_http()
        else:
            raise MCPError(
                "Either 'command' or 'server_url' must be provided",
                server=self.config.get_server_identifier(),
            )

        self._connected = True
        logger.info(f"Connected to MCP server: {self.config.get_server_identifier()}")

    async def _connect_stdio(self) -> None:
        """Connect via stdio transport.

        Raises:
            ImportError: If the 'mcp' package is not installed.
            MCPError: If connection fails.
        """
        try:
            from mcp import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as e:
            raise ImportError(
                "MCP support requires the 'mcp' package. "
                "Install with: pip install agentforge[mcp] or pip install mcp"
            ) from e

        server_id = self.config.get_server_identifier()

        try:
            params = StdioServerParameters(
                command=self.config.command,
                args=self.config.args or [],
                env=self.config.env,
            )

            # Create the stdio client context
            self._connection_context = stdio_client(params)

            # Enter the context to get read/write streams
            self._read_stream, self._write_stream = await self._connection_context.__aenter__()

            # Create and initialize the session
            self._session = ClientSession(self._read_stream, self._write_stream)
            await self._session.__aenter__()
            await self._session.initialize()

            logger.debug(f"stdio connection established: {server_id}")

        except Exception as e:
            raise MCPError(
                f"Failed to connect via stdio: {e}",
                server=server_id,
            ) from e

    async def _connect_http(self) -> None:
        """Connect via Streamable HTTP transport.

        Raises:
            ImportError: If the 'mcp' package is not installed.
            MCPError: If connection fails.
        """
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as e:
            raise ImportError(
                "MCP support requires the 'mcp' package. "
                "Install with: pip install agentforge[mcp] or pip install mcp"
            ) from e

        if not self.config.server_url:
            raise MCPError("server_url is required for HTTP transport")

        server_id = self.config.server_url

        try:
            # Create the HTTP client context
            self._connection_context = streamablehttp_client(self.config.server_url)

            # Enter the context to get streams
            result = await self._connection_context.__aenter__()
            self._read_stream, self._write_stream, _ = result

            # Create and initialize the session
            self._session = ClientSession(self._read_stream, self._write_stream)
            await self._session.__aenter__()
            await self._session.initialize()

            logger.debug(f"HTTP connection established: {server_id}")

        except Exception as e:
            raise MCPError(
                f"Failed to connect via HTTP: {e}",
                server=server_id,
            ) from e

    async def discover_tools(self) -> list[BaseTool]:
        """Connect to MCP server and list available tools.

        Returns:
            List of MCPTool instances wrapping the server's tools.

        Raises:
            MCPError: If discovery fails.
        """
        if not self.is_connected:
            await self.connect()

        if self._session is None:
            raise MCPError(
                "Not connected to MCP server",
                server=self.config.get_server_identifier(),
            )

        try:
            tools_response = await self._session.list_tools()
            tools: list[BaseTool] = []

            for mcp_tool in tools_response.tools:
                tool = self._convert_tool(mcp_tool)
                self._tools[tool.name] = tool
                tools.append(tool)

            logger.info(f"Discovered {len(tools)} tools from {self.config.get_server_identifier()}")
            return tools

        except Exception as e:
            raise MCPError(
                f"Failed to discover tools: {e}",
                server=self.config.get_server_identifier(),
            ) from e

    def _convert_tool(self, mcp_tool: Any) -> MCPTool:
        """Convert an MCP tool definition to an AgentForge tool.

        Args:
            mcp_tool: Tool definition from the MCP server.

        Returns:
            MCPTool instance wrapping the MCP tool.
        """
        return MCPTool(
            name=mcp_tool.name,
            description=mcp_tool.description or "",
            parameters_schema=mcp_tool.inputSchema or {"type": "object"},
            adapter=self,
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool on the MCP server.

        Args:
            name: Name of the tool to call.
            arguments: Arguments to pass to the tool.

        Returns:
            Tool execution result.

        Raises:
            MCPError: If the tool call fails.
        """
        if not self.is_connected:
            await self.connect()

        if self._session is None:
            raise MCPError(
                "Not connected to MCP server",
                server=self.config.get_server_identifier(),
            )

        server_id = self.config.get_server_identifier()

        try:
            logger.debug(f"Calling tool '{name}' on {server_id}")
            result = await self._session.call_tool(name, arguments)

            # Extract content from the result
            if hasattr(result, "content"):
                # Handle different content types
                content = result.content
                if isinstance(content, list):
                    # List of content items
                    texts = []
                    for item in content:
                        if hasattr(item, "text"):
                            texts.append(item.text)
                        elif isinstance(item, str):
                            texts.append(item)
                        else:
                            texts.append(str(item))
                    return "\n".join(texts) if len(texts) == 1 else texts
                return content

            return result

        except Exception as e:
            raise MCPError(
                f"Tool '{name}' execution failed: {e}",
                server=server_id,
            ) from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        try:
            if self._session is not None:
                await self._session.__aexit__(None, None, None)
                self._session = None

            if self._connection_context is not None:
                await self._connection_context.__aexit__(None, None, None)
                self._connection_context = None

            self._read_stream = None
            self._write_stream = None
            self._connected = False

            logger.info(f"Disconnected from MCP server: {self.config.get_server_identifier()}")

        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")
            self._connected = False

    async def __aenter__(self) -> MCPToolAdapter:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    def get_tool(self, name: str) -> MCPTool | None:
        """Get a discovered tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The MCPTool instance, or None if not found.
        """
        return self._tools.get(name)


class MCPToolRegistry:
    """Tool registry that can discover and register MCP tools.

    Extends the functionality of ToolRegistry to support MCP server
    discovery and automatic tool registration.

    Attributes:
        _registry: The underlying ToolRegistry instance.
        _adapters: List of connected MCP adapters.

    Example:
        ```python
        from agentforge.tools.mcp import MCPToolRegistry, MCPConfig

        registry = MCPToolRegistry()

        # Register tools from an MCP server
        tools = await registry.register_mcp_server(
            config=MCPConfig(command="python", args=["server.py"]),
            prefix="myserver"
        )

        # Use the tools
        result = await registry.execute("myserver_search", query="hello")
        ```
    """

    def __init__(self) -> None:
        """Initialize the MCP tool registry."""
        # Import here to avoid circular imports
        from agentforge.tools.registry import ToolRegistry

        self._registry = ToolRegistry()
        self._adapters: list[MCPToolAdapter] = []

    async def register_mcp_server(
        self,
        config: MCPConfig,
        prefix: str = "",
    ) -> list[BaseTool]:
        """Discover and register all tools from an MCP server.

        Args:
            config: MCP connection configuration.
            prefix: Optional prefix to add to tool names (e.g., "myserver_").

        Returns:
            List of registered tools.

        Raises:
            MCPError: If connection or discovery fails.
        """
        adapter = MCPToolAdapter(config)
        tools = await adapter.discover_tools()

        registered: list[BaseTool] = []
        for tool in tools:
            # Optionally prefix tool names
            if prefix:
                # Create a new tool with prefixed name
                prefixed_tool = MCPTool(
                    name=f"{prefix}_{tool.name}",
                    description=tool.description,
                    parameters_schema=tool.get_parameters_schema(),
                    adapter=adapter,
                )
                self._registry.register(prefixed_tool)
                registered.append(prefixed_tool)
            else:
                self._registry.register(tool)
                registered.append(tool)

        self._adapters.append(adapter)
        return registered

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: The tool to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        self._registry.register(tool)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry.

        Args:
            name: Name of the tool to remove.
        """
        self._registry.unregister(name)

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve.

        Returns:
            The tool instance, or None if not found.
        """
        return self._registry.get(name)

    def list_tools(self) -> list[str]:
        """List all registered tool names.

        Returns:
            List of tool names.
        """
        return self._registry.list_tools()

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Export all tools in OpenAI format.

        Returns:
            List of OpenAI-compatible tool definitions.
        """
        return self._registry.to_openai_tools()

    def to_anthropic_tools(self) -> list[dict[str, Any]]:
        """Export all tools in Anthropic format.

        Returns:
            List of Anthropic-compatible tool definitions.
        """
        return self._registry.to_anthropic_tools()

    async def execute(self, name: str, **kwargs: Any) -> Any:
        """Execute a tool by name.

        Args:
            name: Name of the tool to execute.
            **kwargs: Arguments to pass to the tool.

        Returns:
            Tool execution result.
        """
        return await self._registry.execute(name, **kwargs)

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for adapter in self._adapters:
            await adapter.disconnect()
        self._adapters.clear()

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._registry

    def __len__(self) -> int:
        """Get the number of registered tools."""
        return len(self._registry)


async def discover_mcp_tools(
    command: str | None = None,
    server_url: str | None = None,
    **kwargs: Any,
) -> list[BaseTool]:
    """Discover tools from an MCP server.

    Convenience function for quickly discovering MCP tools without
    managing the adapter lifecycle.

    Args:
        command: Command for stdio transport.
        server_url: URL for HTTP transport.
        **kwargs: Additional configuration options.

    Returns:
        List of discovered tools.

    Raises:
        MCPError: If discovery fails.

    Example:
        ```python
        # Discover tools from a local server
        tools = await discover_mcp_tools(
            command="python",
            args=["-m", "my_mcp_server"]
        )

        # Discover tools from a remote server
        tools = await discover_mcp_tools(
            server_url="http://localhost:8080/mcp"
        )
        ```
    """
    config = MCPConfig(
        command=command,
        server_url=server_url,
        **kwargs,
    )

    async with MCPToolAdapter(config) as adapter:
        return await adapter.discover_tools()


async def register_mcp_tools(
    registry: Any,
    command: str | None = None,
    server_url: str | None = None,
    prefix: str = "",
    **kwargs: Any,
) -> list[BaseTool]:
    """Register MCP tools to a registry.

    Convenience function for discovering and registering MCP tools
    to an existing registry.

    Args:
        registry: ToolRegistry instance to register tools to.
        command: Command for stdio transport.
        server_url: URL for HTTP transport.
        prefix: Optional prefix for tool names.
        **kwargs: Additional configuration options.

    Returns:
        List of registered tools.

    Raises:
        MCPError: If discovery or registration fails.

    Example:
        ```python
        from agentforge.tools.registry import ToolRegistry

        registry = ToolRegistry()
        tools = await register_mcp_tools(
            registry=registry,
            command="python",
            args=["-m", "my_mcp_server"],
            prefix="mcp"
        )
        ```
    """
    config = MCPConfig(
        command=command,
        server_url=server_url,
        **kwargs,
    )

    adapter = MCPToolAdapter(config)
    tools = await adapter.discover_tools()

    registered: list[BaseTool] = []
    for tool in tools:
        if prefix:
            prefixed_tool = MCPTool(
                name=f"{prefix}_{tool.name}",
                description=tool.description,
                parameters_schema=tool.get_parameters_schema(),
                adapter=adapter,
            )
            registry.register(prefixed_tool)
            registered.append(prefixed_tool)
        else:
            registry.register(tool)
            registered.append(tool)

    return registered


# =============================================================================
# MCP Server Exporter - Expose AgentForge agents as MCP tools
# =============================================================================


class AgentWrapperTool(BaseTool):
    """Wraps a BaseAgent as a BaseTool for MCP export.

    Allows agents to be exposed as tools that can be called by other
    MCP clients. The wrapper handles input/output conversion between
    the agent interface and tool interface.

    Attributes:
        _agent: The wrapped agent instance.
        _name: Tool name (defaults to agent name).
        _description: Tool description.

    Example:
        ```python
        from agentforge.core.agent import BaseAgent
        from agentforge.tools.mcp import AgentWrapperTool

        class MyAgent(BaseAgent):
            async def execute(self, input):
                return AgentOutput(content="Hello!")

        agent = MyAgent()
        tool = AgentWrapperTool(agent, name="my_tool")
        result = await tool.execute(input="Hello")
        ```
    """

    def __init__(
        self,
        agent: BaseAgent,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the agent wrapper tool.

        Args:
            agent: The agent to wrap.
            name: Optional tool name (defaults to agent name).
            description: Optional description (defaults to auto-generated).
        """
        self._agent = agent
        self._name = name or agent.config.name
        self._description = description or f"Execute the {self._name} agent"

        # Initialize with config
        config = ToolConfig(
            name=self._name,
            description=self._description,
        )
        super().__init__(config)

    @property
    def agent(self) -> BaseAgent:
        """Get the wrapped agent."""
        return self._agent

    def get_parameters_schema(self) -> dict[str, Any]:
        """Get the JSON Schema for the tool's parameters.

        Returns:
            JSON Schema with a single 'input' string parameter.
        """
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input for the agent",
                }
            },
            "required": ["input"],
        }

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the wrapped agent.

        Args:
            **kwargs: Must contain 'input' key with the input string.

        Returns:
            The agent's response content.

        Raises:
            ToolExecutionError: If agent execution fails.
        """
        from agentforge.core.agent import AgentInput
        from agentforge.tools.base import ToolExecutionError

        try:
            input_data = AgentInput(messages=[{"role": "user", "content": kwargs.get("input", "")}])
            result = await self._agent.execute(input_data)
            return result.content
        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=str(e),
                cause=e,
            ) from e

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI tool format.

        Returns:
            OpenAI-compatible tool definition.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }


class MCPServerExporter:
    """Expose AgentForge agents as an MCP server.

    Creates an MCP server that exposes registered agents and tools
    as MCP tools that other MCP clients can discover and use.

    Attributes:
        name: Server name for identification.
        version: Server version string.
        _agents: Registered agents mapped by tool name.
        _tools: Registered tools mapped by name.
        _mcp: The underlying FastMCP server instance.

    Example:
        ```python
        from agentforge.tools.mcp import MCPServerExporter
        from agentforge.core.agent import BaseAgent

        class MyAgent(BaseAgent):
            async def execute(self, input):
                return AgentOutput(content="Hello!")

        # Create exporter and register agent
        exporter = MCPServerExporter(name="my-server")
        exporter.register_agent(MyAgent(), tool_name="greet")

        # Run the server
        exporter.run_stdio()
        ```
    """

    def __init__(self, name: str = "agentforge-server", version: str = "1.0.0") -> None:
        """Initialize the MCP server exporter.

        Args:
            name: Server name for identification.
            version: Server version string.
        """
        self.name = name
        self.version = version
        self._agents: dict[str, BaseAgent] = {}
        self._tools: dict[str, BaseTool] = {}
        self._mcp: Any | None = None

    def register_agent(self, agent: BaseAgent, tool_name: str | None = None) -> None:
        """Register an agent as an MCP tool.

        Args:
            agent: The agent to register.
            tool_name: Optional tool name (defaults to agent name).

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        name = tool_name or agent.config.name
        if name in self._agents or name in self._tools:
            raise ValueError(f"Tool or agent '{name}' is already registered")
        self._agents[name] = agent
        logger.info(f"Registered agent '{name}' as MCP tool")

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool directly.

        Args:
            tool: The tool to register.

        Raises:
            ValueError: If a tool with the same name already exists.
        """
        if tool.name in self._agents or tool.name in self._tools:
            raise ValueError(f"Tool or agent '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        logger.info(f"Registered tool '{tool.name}' as MCP tool")

    def _create_mcp_server(self) -> Any:
        """Create the MCP server with FastMCP.

        Returns:
            FastMCP server instance.

        Raises:
            ImportError: If the 'mcp' package is not installed.
        """
        try:
            from mcp.server.fastmcp import FastMCP
        except ImportError as e:
            raise ImportError(
                "MCP server support requires the 'mcp' package. "
                "Install with: pip install agentforge[mcp] or pip install mcp"
            ) from e

        self._mcp = FastMCP(self.name)

        # Register agents as tools
        for name, _agent in self._agents.items():
            self._register_agent_as_tool(name, _agent)

        # Register direct tools
        for tool in self._tools.values():
            self._register_tool(tool)

        logger.info(
            f"Created MCP server '{self.name}' with "
            f"{len(self._agents)} agents and {len(self._tools)} tools"
        )

        return self._mcp

    def _register_agent_as_tool(self, name: str, agent: BaseAgent) -> None:
        """Register an agent as an MCP tool.

        Args:
            name: Tool name for the agent.
            agent: The agent to register.
        """
        from agentforge.core.agent import AgentInput

        # Create a wrapper that calls the agent
        async def agent_tool(**kwargs: Any) -> Any:
            input_data = AgentInput(messages=[{"role": "user", "content": str(kwargs)}])
            result = await agent.execute(input_data)
            return result.content

        # Set metadata
        agent_tool.__name__ = name
        agent_tool.__doc__ = f"Execute the {name} agent"

        # Register with FastMCP
        self._mcp.tool()(agent_tool)
        logger.debug(f"Registered agent '{name}' as MCP tool")

    def _register_tool(self, tool: BaseTool) -> None:
        """Register a BaseTool with the MCP server.

        Args:
            tool: The tool to register.
        """

        async def tool_wrapper(**kwargs: Any) -> Any:
            return await tool.execute(**kwargs)

        tool_wrapper.__name__ = tool.name
        tool_wrapper.__doc__ = tool.description

        self._mcp.tool()(tool_wrapper)
        logger.debug(f"Registered tool '{tool.name}' as MCP tool")

    def run_stdio(self) -> None:
        """Run the MCP server using stdio transport.

        This is the standard way to run an MCP server for local
        communication with MCP clients.

        Raises:
            ImportError: If the 'mcp' package is not installed.
        """
        if self._mcp is None:
            self._create_mcp_server()

        logger.info(f"Starting MCP server '{self.name}' on stdio")
        self._mcp.run()

    async def run_http(self, host: str = "localhost", port: int = 8000) -> None:
        """Run the MCP server using HTTP transport.

        Args:
            host: Host address to bind to.
            port: Port number to listen on.

        Raises:
            ImportError: If required packages are not installed.
        """
        if self._mcp is None:
            self._create_mcp_server()

        # HTTP transport using SSE
        try:
            import uvicorn
            from mcp.server.sse import SseServerTransport
            from starlette.applications import Starlette
            from starlette.routing import Route
        except ImportError as e:
            raise ImportError(
                "HTTP transport requires 'uvicorn', 'starlette', and 'mcp'. "
                "Install with: pip install agentforge[mcp] uvicorn starlette"
            ) from e

        # Create SSE transport
        sse = SseServerTransport(self._mcp)

        # Create Starlette app
        app = Starlette(
            routes=[
                Route("/sse", endpoint=sse.handle_sse),
                Route("/messages", endpoint=sse.handle_post_message, methods=["POST"]),
            ]
        )

        logger.info(f"Starting MCP server '{self.name}' on http://{host}:{port}")

        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()

    def get_tools_list(self) -> list[dict[str, Any]]:
        """Get list of exposed tools for discovery.

        Returns:
            List of dictionaries with tool name, description, and type.
        """
        tools: list[dict[str, Any]] = []

        for name, _agent in self._agents.items():
            tools.append(
                {
                    "name": name,
                    "description": f"Execute the {name} agent",
                    "type": "agent",
                }
            )

        for name, tool in self._tools.items():
            tools.append(
                {
                    "name": name,
                    "description": tool.description,
                    "type": "tool",
                }
            )

        return tools

    def unregister(self, name: str) -> bool:
        """Unregister an agent or tool by name.

        Args:
            name: Name of the agent or tool to remove.

        Returns:
            True if something was removed, False otherwise.
        """
        if name in self._agents:
            del self._agents[name]
            logger.info(f"Unregistered agent '{name}'")
            return True
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool '{name}'")
            return True
        return False

    def clear(self) -> None:
        """Remove all registered agents and tools."""
        self._agents.clear()
        self._tools.clear()
        self._mcp = None
        logger.info("Cleared all registered agents and tools")


def create_mcp_server(
    agents: list[BaseAgent] | None = None,
    tools: list[BaseTool] | None = None,
    name: str = "agentforge-server",
    version: str = "1.0.0",
) -> MCPServerExporter:
    """Create an MCP server from agents and tools.

    Convenience function for quickly creating an MCP server with
    pre-registered agents and tools.

    Args:
        agents: List of agents to register.
        tools: List of tools to register.
        name: Server name for identification.
        version: Server version string.

    Returns:
        Configured MCPServerExporter instance.

    Example:
        ```python
        from agentforge.tools.mcp import create_mcp_server

        # Create server with agents
        server = create_mcp_server(
            agents=[agent1, agent2],
            tools=[tool1],
            name="my-server"
        )

        # Run the server
        server.run_stdio()
        ```
    """
    exporter = MCPServerExporter(name=name, version=version)

    for agent in agents or []:
        exporter.register_agent(agent)

    for tool in tools or []:
        exporter.register_tool(tool)

    return exporter


def run_mcp_server(
    agents: list[BaseAgent],
    name: str = "agentforge-server",
    version: str = "1.0.0",
) -> None:
    """Run an MCP server exposing the given agents.

    Convenience function for quickly starting an MCP server.
    This is a blocking call that runs the server on stdio.

    Args:
        agents: List of agents to expose.
        name: Server name for identification.
        version: Server version string.

    Example:
        ```python
        from agentforge.tools.mcp import run_mcp_server

        # This will block and run the server
        run_mcp_server(agents=[my_agent], name="my-server")
        ```
    """
    exporter = create_mcp_server(agents=agents, name=name, version=version)
    exporter.run_stdio()


__all__ = [
    "MCPConfig",
    "MCPTool",
    "MCPToolAdapter",
    "MCPToolRegistry",
    "discover_mcp_tools",
    "register_mcp_tools",
    # Server exporter
    "AgentWrapperTool",
    "MCPServerExporter",
    "create_mcp_server",
    "run_mcp_server",
]
