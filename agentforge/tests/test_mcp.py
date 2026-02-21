"""Tests for AgentForge MCP integration.

This module tests:
- MCPConfig validation
- MCPTool creation and execution
- MCPToolAdapter connection handling
- MCPToolRegistry operations
- Tool conversion from MCP to AgentForge format
- Error handling for MCP operations
"""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from agentforge.core.exceptions import MCPError
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
from agentforge.tools.registry import ToolRegistry

# =============================================================================
# Test Fixtures
# =============================================================================


@dataclass
class MockMCPTool:
    """Mock MCP tool for testing."""

    name: str
    description: str
    inputSchema: dict[str, Any]  # noqa: N815


@dataclass
class MockToolListResponse:
    """Mock response from list_tools."""

    tools: list[MockMCPTool]


@dataclass
class MockContentItem:
    """Mock content item in tool result."""

    text: str


@dataclass
class MockToolResult:
    """Mock result from call_tool."""

    content: list[MockContentItem]


@pytest.fixture
def mock_mcp_tool():
    """Create a mock MCP tool definition."""
    return MockMCPTool(
        name="test_tool",
        description="A test tool",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    )


@pytest.fixture
def mock_session(mock_mcp_tool):
    """Create a mock MCP client session."""
    session = AsyncMock()
    session.list_tools = AsyncMock(return_value=MockToolListResponse(tools=[mock_mcp_tool]))
    session.call_tool = AsyncMock(
        return_value=MockToolResult(content=[MockContentItem(text="result")])
    )
    session.initialize = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    return session


@pytest.fixture
def stdio_config():
    """Create a stdio MCP config."""
    return MCPConfig(
        command="python",
        args=["-m", "test_server"],
        timeout=30.0,
    )


@pytest.fixture
def http_config():
    """Create an HTTP MCP config."""
    return MCPConfig(
        server_url="http://localhost:8080/mcp",
        timeout=60.0,
    )


# =============================================================================
# Test MCPConfig
# =============================================================================


class TestMCPConfig:
    """Tests for MCPConfig validation."""

    def test_stdio_config_creation(self):
        """Test creating a stdio config."""
        config = MCPConfig(
            command="python",
            args=["-m", "server"],
            env={"DEBUG": "1"},
        )

        assert config.command == "python"
        assert config.args == ["-m", "server"]
        assert config.env == {"DEBUG": "1"}
        assert config.timeout == 30.0

    def test_http_config_creation(self):
        """Test creating an HTTP config."""
        config = MCPConfig(
            server_url="http://localhost:8080/mcp",
            timeout=60.0,
        )

        assert config.server_url == "http://localhost:8080/mcp"
        assert config.timeout == 60.0

    def test_default_timeout(self):
        """Test default timeout value."""
        config = MCPConfig(command="python")
        assert config.timeout == 30.0

    def test_timeout_validation(self):
        """Test timeout must be between 0.1 and 3600."""
        # Valid timeouts
        MCPConfig(command="python", timeout=0.1)
        MCPConfig(command="python", timeout=3600.0)

        # Invalid timeouts
        with pytest.raises(ValidationError):
            MCPConfig(command="python", timeout=0.0)

        with pytest.raises(ValidationError):
            MCPConfig(command="python", timeout=4000.0)

    def test_get_server_identifier_stdio(self):
        """Test server identifier for stdio config."""
        config = MCPConfig(command="python", args=["-m", "server"])
        assert config.get_server_identifier() == "python -m server"

    def test_get_server_identifier_http(self):
        """Test server identifier for HTTP config."""
        config = MCPConfig(server_url="http://localhost:8080/mcp")
        assert config.get_server_identifier() == "http://localhost:8080/mcp"

    def test_get_server_identifier_empty(self):
        """Test server identifier with no connection info."""
        config = MCPConfig()
        assert config.get_server_identifier() == "unknown"

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden."""
        with pytest.raises(ValidationError):
            MCPConfig(command="python", unknown_field="value")


# =============================================================================
# Test MCPTool
# =============================================================================


class TestMCPTool:
    """Tests for MCPTool class."""

    def test_mcp_tool_creation(self, stdio_config):
        """Test creating an MCPTool instance."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            parameters_schema={"type": "object"},
            adapter=adapter,
        )

        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.get_parameters_schema() == {"type": "object"}

    def test_to_openai_tool(self, stdio_config):
        """Test converting to OpenAI tool format."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="search",
            description="Search for items",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            adapter=adapter,
        )

        openai_tool = tool.to_openai_tool()

        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "search"
        assert openai_tool["function"]["description"] == "Search for items"
        assert "properties" in openai_tool["function"]["parameters"]

    def test_to_anthropic_tool(self, stdio_config):
        """Test converting to Anthropic tool format."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="search",
            description="Search for items",
            parameters_schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
            },
            adapter=adapter,
        )

        anthropic_tool = tool.to_anthropic_tool()

        assert anthropic_tool["name"] == "search"
        assert anthropic_tool["description"] == "Search for items"
        assert "input_schema" in anthropic_tool

    @pytest.mark.asyncio
    async def test_execute_calls_adapter(self, stdio_config):
        """Test that execute calls the adapter's call_tool method."""
        adapter = MCPToolAdapter(stdio_config)
        adapter.call_tool = AsyncMock(return_value="result")

        tool = MCPTool(
            name="test_tool",
            description="Test",
            parameters_schema={},
            adapter=adapter,
        )

        result = await tool.execute(query="hello", limit=5)

        adapter.call_tool.assert_called_once_with("test_tool", {"query": "hello", "limit": 5})
        assert result == "result"


# =============================================================================
# Test MCPToolAdapter
# =============================================================================


class TestMCPToolAdapter:
    """Tests for MCPToolAdapter class."""

    def test_adapter_creation(self, stdio_config):
        """Test creating an adapter instance."""
        adapter = MCPToolAdapter(stdio_config)

        assert adapter.config == stdio_config
        assert not adapter.is_connected
        assert adapter._session is None

    def test_is_connected_property(self, stdio_config):
        """Test is_connected property."""
        adapter = MCPToolAdapter(stdio_config)
        assert not adapter.is_connected

        adapter._connected = True
        adapter._session = MagicMock()
        assert adapter.is_connected

    @pytest.mark.asyncio
    async def test_connect_requires_command_or_url(self):
        """Test that connect requires either command or server_url."""
        config = MCPConfig()
        adapter = MCPToolAdapter(config)

        with pytest.raises(MCPError) as exc_info:
            await adapter.connect()

        assert "Either 'command' or 'server_url' must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover_tools_without_connection_raises(self, stdio_config):
        """Test that discover_tools raises when not connected."""
        adapter = MCPToolAdapter(stdio_config)

        # Mock connect to do nothing
        adapter.connect = AsyncMock()
        adapter._session = None

        with pytest.raises(MCPError) as exc_info:
            await adapter.discover_tools()

        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_discover_tools_converts_tools(self, stdio_config, mock_session, mock_mcp_tool):
        """Test that discover_tools converts MCP tools to AgentForge tools."""
        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True

        tools = await adapter.discover_tools()

        assert len(tools) == 1
        assert tools[0].name == "test_tool"
        assert tools[0].description == "A test tool"

    @pytest.mark.asyncio
    async def test_call_tool_returns_content(self, stdio_config, mock_session):
        """Test that call_tool extracts content from result."""
        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True

        result = await adapter.call_tool("test_tool", {"query": "hello"})

        assert result == "result"
        mock_session.call_tool.assert_called_once_with("test_tool", {"query": "hello"})

    @pytest.mark.asyncio
    async def test_call_tool_without_connection_raises(self, stdio_config):
        """Test that call_tool raises when not connected."""
        adapter = MCPToolAdapter(stdio_config)
        adapter.connect = AsyncMock()
        adapter._session = None

        with pytest.raises(MCPError) as exc_info:
            await adapter.call_tool("test", {})

        assert "Not connected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up(self, stdio_config, mock_session):
        """Test that disconnect cleans up resources."""
        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True
        adapter._connection_context = AsyncMock()
        adapter._connection_context.__aexit__ = AsyncMock(return_value=None)

        await adapter.disconnect()

        assert not adapter._connected
        assert adapter._session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, stdio_config, mock_session):
        """Test using adapter as async context manager."""
        adapter = MCPToolAdapter(stdio_config)

        # Mock the connect method
        adapter.connect = AsyncMock()
        adapter.disconnect = AsyncMock()

        async with adapter as a:
            assert a is adapter
            adapter.connect.assert_called_once()

        adapter.disconnect.assert_called_once()

    def test_get_tool_returns_cached_tool(self, stdio_config):
        """Test that get_tool returns cached tools."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="cached_tool",
            description="Cached",
            parameters_schema={},
            adapter=adapter,
        )
        adapter._tools["cached_tool"] = tool

        result = adapter.get_tool("cached_tool")
        assert result is tool

    def test_get_tool_returns_none_for_unknown(self, stdio_config):
        """Test that get_tool returns None for unknown tools."""
        adapter = MCPToolAdapter(stdio_config)
        assert adapter.get_tool("unknown") is None


# =============================================================================
# Test MCPToolRegistry
# =============================================================================


class TestMCPToolRegistry:
    """Tests for MCPToolRegistry class."""

    def test_registry_creation(self):
        """Test creating an MCPToolRegistry instance."""
        registry = MCPToolRegistry()

        assert len(registry) == 0
        assert len(registry._adapters) == 0

    @pytest.mark.asyncio
    async def test_register_mcp_server(self, stdio_config, mock_session, mock_mcp_tool):
        """Test registering tools from an MCP server."""
        registry = MCPToolRegistry()

        # Mock the adapter's discover_tools
        with patch.object(
            MCPToolAdapter, "discover_tools", new_callable=AsyncMock
        ) as mock_discover:
            mock_discover.return_value = [
                MCPTool(
                    name=mock_mcp_tool.name,
                    description=mock_mcp_tool.description,
                    parameters_schema=mock_mcp_tool.inputSchema,
                    adapter=MCPToolAdapter(stdio_config),
                )
            ]

            tools = await registry.register_mcp_server(stdio_config)

            assert len(tools) == 1
            assert tools[0].name == "test_tool"
            assert "test_tool" in registry

    @pytest.mark.asyncio
    async def test_register_mcp_server_with_prefix(self, stdio_config, mock_mcp_tool):
        """Test registering tools with a prefix."""
        registry = MCPToolRegistry()

        with patch.object(
            MCPToolAdapter, "discover_tools", new_callable=AsyncMock
        ) as mock_discover:
            mock_discover.return_value = [
                MCPTool(
                    name=mock_mcp_tool.name,
                    description=mock_mcp_tool.description,
                    parameters_schema=mock_mcp_tool.inputSchema,
                    adapter=MCPToolAdapter(stdio_config),
                )
            ]

            tools = await registry.register_mcp_server(stdio_config, prefix="myserver")

            assert len(tools) == 1
            assert tools[0].name == "myserver_test_tool"
            assert "myserver_test_tool" in registry

    def test_register_standalone_tool(self):
        """Test registering a standalone tool."""
        registry = MCPToolRegistry()

        # Create a mock tool
        tool = MagicMock()
        tool.name = "standalone_tool"

        registry.register(tool)

        assert "standalone_tool" in registry
        assert len(registry) == 1

    def test_list_tools(self):
        """Test listing registered tools."""
        registry = MCPToolRegistry()

        tool = MagicMock()
        tool.name = "test_tool"
        registry.register(tool)

        tools = registry.list_tools()
        assert tools == ["test_tool"]

    def test_to_openai_tools(self):
        """Test exporting to OpenAI format."""
        registry = MCPToolRegistry()

        tool = MagicMock()
        tool.to_openai_tool = MagicMock(
            return_value={"type": "function", "function": {"name": "test"}}
        )
        tool.name = "test_tool"
        registry.register(tool)

        openai_tools = registry.to_openai_tools()
        assert len(openai_tools) == 1
        assert openai_tools[0]["function"]["name"] == "test"

    def test_to_anthropic_tools(self):
        """Test exporting to Anthropic format."""
        registry = MCPToolRegistry()

        tool = MagicMock()
        tool.to_anthropic_tool = MagicMock(return_value={"name": "test", "inputSchema": {}})
        tool.name = "test_tool"
        registry.register(tool)

        anthropic_tools = registry.to_anthropic_tools()
        assert len(anthropic_tools) == 1
        assert anthropic_tools[0]["name"] == "test"

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test executing a tool through the registry."""
        registry = MCPToolRegistry()

        tool = MagicMock()
        tool.execute = AsyncMock(return_value="result")
        tool.name = "test_tool"
        registry.register(tool)

        result = await registry.execute("test_tool", query="hello")

        tool.execute.assert_called_once_with(query="hello")
        assert result == "result"

    @pytest.mark.asyncio
    async def test_disconnect_all(self, stdio_config):
        """Test disconnecting from all MCP servers."""
        registry = MCPToolRegistry()

        adapter = MCPToolAdapter(stdio_config)
        adapter.disconnect = AsyncMock()
        registry._adapters.append(adapter)

        await registry.disconnect_all()

        adapter.disconnect.assert_called_once()
        assert len(registry._adapters) == 0


# =============================================================================
# Test Convenience Functions
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_discover_mcp_tools(self, mock_mcp_tool):
        """Test discover_mcp_tools function."""
        # Mock the entire MCPToolAdapter to avoid actual connection
        with patch("agentforge.tools.mcp.MCPToolAdapter") as mock_adapter_class:
            mock_adapter = AsyncMock()
            mock_adapter.__aenter__ = AsyncMock(return_value=mock_adapter)
            mock_adapter.__aexit__ = AsyncMock(return_value=None)
            mock_adapter.discover_tools = AsyncMock(
                return_value=[
                    MCPTool(
                        name=mock_mcp_tool.name,
                        description=mock_mcp_tool.description,
                        parameters_schema=mock_mcp_tool.inputSchema,
                        adapter=mock_adapter,
                    )
                ]
            )
            mock_adapter_class.return_value = mock_adapter

            tools = await discover_mcp_tools(command="python3", args=["-m", "server"])

            assert len(tools) == 1
            assert tools[0].name == "test_tool"

    @pytest.mark.asyncio
    async def test_register_mcp_tools_function(self, mock_mcp_tool):
        """Test register_mcp_tools function."""
        registry = ToolRegistry()

        with patch.object(
            MCPToolAdapter, "discover_tools", new_callable=AsyncMock
        ) as mock_discover:
            mock_discover.return_value = [
                MCPTool(
                    name=mock_mcp_tool.name,
                    description=mock_mcp_tool.description,
                    parameters_schema=mock_mcp_tool.inputSchema,
                    adapter=MCPToolAdapter(MCPConfig(command="python")),
                )
            ]

            tools = await register_mcp_tools(registry=registry, command="python", prefix="mcp")

            assert len(tools) == 1
            assert tools[0].name == "mcp_test_tool"
            assert "mcp_test_tool" in registry


# =============================================================================
# Test Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for error handling."""

    def test_mcp_error_with_server(self):
        """Test MCPError with server identifier."""
        error = MCPError("Connection failed", server="http://localhost:8080")

        assert error.server == "http://localhost:8080"
        assert "[http://localhost:8080] Connection failed" in str(error)

    def test_mcp_error_without_server(self):
        """Test MCPError without server identifier."""
        error = MCPError("Generic error")

        assert error.server is None
        assert "Generic error" in str(error)

    @pytest.mark.asyncio
    async def test_adapter_requires_command_or_url(self):
        """Test that adapter raises MCPError when no command or URL is provided."""
        config = MCPConfig()  # No command or server_url
        adapter = MCPToolAdapter(config)

        with pytest.raises(MCPError) as exc_info:
            await adapter.connect()

        assert "Either 'command' or 'server_url' must be provided" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_adapter_wraps_tool_errors(self, stdio_config, mock_session):
        """Test that adapter wraps tool execution errors in MCPError."""
        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True

        # Make call_tool raise an error
        mock_session.call_tool.side_effect = RuntimeError("Tool failed")

        with pytest.raises(MCPError) as exc_info:
            await adapter.call_tool("test_tool", {})

        assert "execution failed" in str(exc_info.value)


# =============================================================================
# Test Import Error Handling
# =============================================================================


class TestImportErrorHandling:
    """Tests for handling missing mcp package."""

    @pytest.mark.asyncio
    async def test_stdio_raises_import_error_without_mcp(self, stdio_config):
        """Test that stdio connection raises ImportError without mcp package."""
        adapter = MCPToolAdapter(stdio_config)

        with (
            patch.dict("sys.modules", {"mcp": None, "mcp.client.stdio": None}),
            patch("builtins.__import__", side_effect=ImportError("No module named 'mcp'")),
            pytest.raises(ImportError) as exc_info,
        ):
            await adapter._connect_stdio()

        assert "mcp" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_http_raises_import_error_without_mcp(self, http_config):
        """Test that HTTP connection raises ImportError without mcp package."""
        adapter = MCPToolAdapter(http_config)

        with (
            patch.dict("sys.modules", {"mcp": None, "mcp.client.streamable_http": None}),
            patch("builtins.__import__", side_effect=ImportError("No module named 'mcp'")),
            pytest.raises(ImportError) as exc_info,
        ):
            await adapter._connect_http()

        assert "mcp" in str(exc_info.value).lower()


# =============================================================================
# Test Multiple Tools
# =============================================================================


class TestMultipleTools:
    """Tests for handling multiple tools."""

    @pytest.mark.asyncio
    async def test_discover_multiple_tools(self, stdio_config):
        """Test discovering multiple tools from a server."""
        tools_list = [
            MockMCPTool(
                name="search",
                description="Search for items",
                inputSchema={"type": "object", "properties": {"query": {"type": "string"}}},
            ),
            MockMCPTool(
                name="create",
                description="Create an item",
                inputSchema={"type": "object", "properties": {"name": {"type": "string"}}},
            ),
            MockMCPTool(
                name="delete",
                description="Delete an item",
                inputSchema={"type": "object", "properties": {"id": {"type": "string"}}},
            ),
        ]

        mock_session = AsyncMock()
        mock_session.list_tools = AsyncMock(return_value=MockToolListResponse(tools=tools_list))
        mock_session.initialize = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True

        tools = await adapter.discover_tools()

        assert len(tools) == 3
        assert tools[0].name == "search"
        assert tools[1].name == "create"
        assert tools[2].name == "delete"

        # Check all tools are cached
        assert len(adapter._tools) == 3
        assert "search" in adapter._tools
        assert "create" in adapter._tools
        assert "delete" in adapter._tools


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_description(self, stdio_config):
        """Test tool with empty description."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="test",
            description="",
            parameters_schema={},
            adapter=adapter,
        )

        assert tool.description == ""

    def test_empty_parameters_schema(self, stdio_config):
        """Test tool with empty parameters schema."""
        adapter = MCPToolAdapter(stdio_config)
        tool = MCPTool(
            name="test",
            description="Test",
            parameters_schema={},
            adapter=adapter,
        )

        assert tool.get_parameters_schema() == {}

    @pytest.mark.asyncio
    async def test_double_connect(self, stdio_config):
        """Test that connecting twice doesn't raise an error."""
        adapter = MCPToolAdapter(stdio_config)
        adapter._connected = True

        # Should not raise, just log and return
        await adapter.connect()

        assert adapter._connected

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, stdio_config):
        """Test that disconnecting when not connected doesn't raise."""
        adapter = MCPToolAdapter(stdio_config)

        # Should not raise
        await adapter.disconnect()

        assert not adapter._connected

    @pytest.mark.asyncio
    async def test_tool_result_with_multiple_content_items(self, stdio_config):
        """Test handling tool result with multiple content items."""
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock(
            return_value=MockToolResult(
                content=[
                    MockContentItem(text="First result"),
                    MockContentItem(text="Second result"),
                ]
            )
        )

        adapter = MCPToolAdapter(stdio_config)
        adapter._session = mock_session
        adapter._connected = True

        result = await adapter.call_tool("test", {})

        # Should return a list when multiple items
        assert isinstance(result, list)
        assert len(result) == 2


# =============================================================================
# Test AgentWrapperTool
# =============================================================================


class TestAgentWrapperTool:
    """Tests for AgentWrapperTool class."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        from agentforge.core.agent import AgentConfig, AgentOutput, BaseAgent

        class MockAgent(BaseAgent):
            def __init__(self):
                super().__init__(config=AgentConfig(name="test_agent"))
                self.execute_called = False

            async def execute(self, input):
                self.execute_called = True
                return AgentOutput(content="Agent response")

        return MockAgent()

    def test_wrapper_creation(self, mock_agent):
        """Test creating an AgentWrapperTool instance."""
        tool = AgentWrapperTool(mock_agent)

        assert tool.name == "test_agent"
        assert "test_agent" in tool.description
        assert tool.agent is mock_agent

    def test_wrapper_with_custom_name(self, mock_agent):
        """Test creating wrapper with custom name."""
        tool = AgentWrapperTool(mock_agent, name="custom_tool")

        assert tool.name == "custom_tool"
        assert "custom_tool" in tool.description

    def test_wrapper_with_custom_description(self, mock_agent):
        """Test creating wrapper with custom description."""
        tool = AgentWrapperTool(mock_agent, description="Custom description")

        assert tool.description == "Custom description"

    def test_get_parameters_schema(self, mock_agent):
        """Test getting parameters schema."""
        tool = AgentWrapperTool(mock_agent)
        schema = tool.get_parameters_schema()

        assert schema["type"] == "object"
        assert "input" in schema["properties"]
        assert schema["required"] == ["input"]

    @pytest.mark.asyncio
    async def test_execute_calls_agent(self, mock_agent):
        """Test that execute calls the wrapped agent."""
        tool = AgentWrapperTool(mock_agent)

        result = await tool.execute(input="Hello")

        assert mock_agent.execute_called
        assert result == "Agent response"

    @pytest.mark.asyncio
    async def test_execute_with_empty_input(self, mock_agent):
        """Test execute with empty input."""
        tool = AgentWrapperTool(mock_agent)

        await tool.execute()

        assert mock_agent.execute_called

    def test_to_openai_tool(self, mock_agent):
        """Test converting to OpenAI tool format."""
        tool = AgentWrapperTool(mock_agent)
        openai_tool = tool.to_openai_tool()

        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "test_agent"
        assert "parameters" in openai_tool["function"]


# =============================================================================
# Test MCPServerExporter
# =============================================================================


class TestMCPServerExporter:
    """Tests for MCPServerExporter class."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        from agentforge.core.agent import AgentConfig, AgentOutput, BaseAgent

        class MockAgent(BaseAgent):
            def __init__(self, name="test_agent"):
                super().__init__(config=AgentConfig(name=name))

            async def execute(self, input):
                return AgentOutput(content=f"Response from {self.config.name}")

        return MockAgent

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool for testing."""
        from agentforge.tools.base import BaseTool, ToolConfig

        class MockTool(BaseTool):
            def __init__(self, name="mock_tool"):
                super().__init__(ToolConfig(name=name, description="A mock tool"))

            def get_parameters_schema(self):
                return {"type": "object", "properties": {}}

            async def execute(self, **kwargs):
                return "Tool result"

        return MockTool()

    def test_exporter_creation(self):
        """Test creating an MCPServerExporter instance."""
        exporter = MCPServerExporter(name="test-server", version="2.0.0")

        assert exporter.name == "test-server"
        assert exporter.version == "2.0.0"
        assert len(exporter._agents) == 0
        assert len(exporter._tools) == 0

    def test_register_agent(self, mock_agent):
        """Test registering an agent."""
        exporter = MCPServerExporter()
        agent = mock_agent()

        exporter.register_agent(agent)

        assert "test_agent" in exporter._agents
        assert exporter._agents["test_agent"] is agent

    def test_register_agent_with_custom_name(self, mock_agent):
        """Test registering an agent with custom tool name."""
        exporter = MCPServerExporter()
        agent = mock_agent()

        exporter.register_agent(agent, tool_name="custom_name")

        assert "custom_name" in exporter._agents
        assert "test_agent" not in exporter._agents

    def test_register_agent_duplicate_raises(self, mock_agent):
        """Test that registering duplicate agent name raises."""
        exporter = MCPServerExporter()
        agent1 = mock_agent()
        agent2 = mock_agent()

        exporter.register_agent(agent1)

        with pytest.raises(ValueError) as exc_info:
            exporter.register_agent(agent2)

        assert "already registered" in str(exc_info.value)

    def test_register_tool(self, mock_tool):
        """Test registering a tool."""
        exporter = MCPServerExporter()

        exporter.register_tool(mock_tool)

        assert "mock_tool" in exporter._tools

    def test_register_tool_duplicate_raises(self, mock_tool):
        """Test that registering duplicate tool name raises."""
        exporter = MCPServerExporter()

        exporter.register_tool(mock_tool)

        with pytest.raises(ValueError):
            exporter.register_tool(mock_tool)

    def test_get_tools_list(self, mock_agent, mock_tool):
        """Test getting list of exposed tools."""
        exporter = MCPServerExporter()
        exporter.register_agent(mock_agent())
        exporter.register_tool(mock_tool)

        tools = exporter.get_tools_list()

        assert len(tools) == 2
        names = [t["name"] for t in tools]
        assert "test_agent" in names
        assert "mock_tool" in names

        # Check types
        for t in tools:
            if t["name"] == "test_agent":
                assert t["type"] == "agent"
            elif t["name"] == "mock_tool":
                assert t["type"] == "tool"

    def test_unregister_agent(self, mock_agent):
        """Test unregistering an agent."""
        exporter = MCPServerExporter()
        agent = mock_agent()

        exporter.register_agent(agent)
        result = exporter.unregister("test_agent")

        assert result is True
        assert "test_agent" not in exporter._agents

    def test_unregister_tool(self, mock_tool):
        """Test unregistering a tool."""
        exporter = MCPServerExporter()

        exporter.register_tool(mock_tool)
        result = exporter.unregister("mock_tool")

        assert result is True
        assert "mock_tool" not in exporter._tools

    def test_unregister_unknown_returns_false(self):
        """Test unregistering unknown name returns False."""
        exporter = MCPServerExporter()

        result = exporter.unregister("unknown")

        assert result is False

    def test_clear(self, mock_agent, mock_tool):
        """Test clearing all registered items."""
        exporter = MCPServerExporter()
        exporter.register_agent(mock_agent())
        exporter.register_tool(mock_tool)

        exporter.clear()

        assert len(exporter._agents) == 0
        assert len(exporter._tools) == 0
        assert exporter._mcp is None

    def test_create_mcp_server_raises_without_mcp(self, mock_agent):
        """Test that creating MCP server raises without mcp package."""
        exporter = MCPServerExporter()
        exporter.register_agent(mock_agent())

        with (
            patch.dict("sys.modules", {"mcp": None, "mcp.server.fastmcp": None}),
            patch("builtins.__import__", side_effect=ImportError("No module named 'mcp'")),
            pytest.raises(ImportError) as exc_info,
        ):
            exporter._create_mcp_server()

        assert "mcp" in str(exc_info.value).lower()


# =============================================================================
# Test Convenience Functions for Server Exporter
# =============================================================================


class TestServerExporterConvenienceFunctions:
    """Tests for server exporter convenience functions."""

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        from agentforge.core.agent import AgentConfig, AgentOutput, BaseAgent

        class MockAgent(BaseAgent):
            def __init__(self):
                super().__init__(config=AgentConfig(name="test_agent"))

            async def execute(self, input):
                return AgentOutput(content="Response")

        return MockAgent()

    @pytest.fixture
    def mock_tool(self):
        """Create a mock tool for testing."""
        from agentforge.tools.base import BaseTool, ToolConfig

        class MockTool(BaseTool):
            def __init__(self):
                super().__init__(ToolConfig(name="test_tool", description="Test"))

            def get_parameters_schema(self):
                return {"type": "object"}

            async def execute(self, **kwargs):
                return "result"

        return MockTool()

    def test_create_mcp_server_with_agents(self, mock_agent):
        """Test create_mcp_server with agents."""
        exporter = create_mcp_server(agents=[mock_agent])

        assert exporter.name == "agentforge-server"
        assert "test_agent" in exporter._agents

    def test_create_mcp_server_with_tools(self, mock_tool):
        """Test create_mcp_server with tools."""
        exporter = create_mcp_server(tools=[mock_tool])

        assert "test_tool" in exporter._tools

    def test_create_mcp_server_with_both(self, mock_agent, mock_tool):
        """Test create_mcp_server with both agents and tools."""
        exporter = create_mcp_server(agents=[mock_agent], tools=[mock_tool])

        assert "test_agent" in exporter._agents
        assert "test_tool" in exporter._tools

    def test_create_mcp_server_with_custom_name(self, mock_agent):
        """Test create_mcp_server with custom name."""
        exporter = create_mcp_server(agents=[mock_agent], name="custom-server")

        assert exporter.name == "custom-server"

    def test_create_mcp_server_with_version(self, mock_agent):
        """Test create_mcp_server with custom version."""
        exporter = create_mcp_server(agents=[mock_agent], version="2.0.0")

        assert exporter.version == "2.0.0"

    def test_run_mcp_server_creates_and_runs(self, mock_agent):
        """Test run_mcp_server creates exporter and calls run_stdio."""
        with patch("agentforge.tools.mcp.MCPServerExporter") as mock_exporter_class:
            mock_exporter = MagicMock()
            mock_exporter_class.return_value = mock_exporter

            run_mcp_server(agents=[mock_agent], name="test-server")

            # Verify exporter was created with correct name
            mock_exporter_class.assert_called_once_with(name="test-server", version="1.0.0")

            # Verify agent was registered
            mock_exporter.register_agent.assert_called_once_with(mock_agent)

            # Verify run_stdio was called
            mock_exporter.run_stdio.assert_called_once()
