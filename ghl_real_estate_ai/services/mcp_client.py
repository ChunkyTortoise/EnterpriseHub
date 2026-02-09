"""
MCP Client for EnterpriseHub - Universal Model Context Protocol Client
Replaces custom integrations with standardized MCP server connections
"""

import asyncio
import json
import shlex
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import websockets

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class MCPTransport(Enum):
    WEBSOCKET = "websocket"
    HTTP = "http"
    STDIO = "stdio"


@dataclass
class MCPServer:
    name: str
    transport: MCPTransport
    url: str
    auth_config: Dict[str, Any]
    capabilities: List[str]
    status: str = "disconnected"


@dataclass
class MCPTool:
    name: str
    server: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]


class MCPClient:
    """
    Universal MCP client for connecting to multiple MCP servers.

    Provides standardized interface for:
    - Server discovery and connection
    - Tool execution with error handling
    - Authentication management
    - Connection health monitoring
    """

    def __init__(self, config_path: str = ".claude/mcp-servers.json"):
        self.config_path = config_path
        self.servers: Dict[str, MCPServer] = {}
        self.connections: Dict[str, Any] = {}
        self.available_tools: Dict[str, MCPTool] = {}

        # Load MCP server configurations
        self._load_server_configs()

    def _load_server_configs(self):
        """Load MCP server configurations from JSON file"""
        try:
            with open(self.config_path, "r") as f:
                config = json.load(f)

            for server_config in config.get("servers", []):
                server = MCPServer(
                    name=server_config["name"],
                    transport=MCPTransport(server_config["transport"]),
                    url=server_config["url"],
                    auth_config=server_config.get("auth", {}),
                    capabilities=server_config.get("capabilities", []),
                )
                self.servers[server.name] = server

            logger.info(f"Loaded {len(self.servers)} MCP server configurations")

        except FileNotFoundError:
            logger.warning(f"MCP config file not found: {self.config_path}")
            self.servers = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in MCP config: {e}")
            self.servers = {}

    async def connect_to_server(self, server_name: str) -> bool:
        """
        Connect to a specific MCP server

        Args:
            server_name: Name of the server to connect to

        Returns:
            True if connection successful, False otherwise
        """
        if server_name not in self.servers:
            logger.error(f"Unknown MCP server: {server_name}")
            return False

        server = self.servers[server_name]

        try:
            if server.transport == MCPTransport.WEBSOCKET:
                connection = await self._connect_websocket(server)
            elif server.transport == MCPTransport.HTTP:
                connection = await self._connect_http(server)
            elif server.transport == MCPTransport.STDIO:
                connection = await self._connect_stdio(server)
            else:
                logger.error(f"Unsupported transport: {server.transport}")
                return False

            self.connections[server_name] = connection
            server.status = "connected"

            # Discover available tools
            await self._discover_tools(server_name)

            logger.info(f"Connected to MCP server: {server_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            server.status = "error"
            return False

    async def _connect_websocket(self, server: MCPServer) -> websockets.WebSocketServerProtocol:
        """Connect to WebSocket MCP server"""
        # Add authentication headers if configured
        headers = {}
        if "token" in server.auth_config:
            headers["Authorization"] = f"Bearer {server.auth_config['token']}"

        connection = await websockets.connect(server.url, extra_headers=headers, ping_interval=30, ping_timeout=10)

        # Send MCP handshake
        await connection.send(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                    },
                }
            )
        )

        # Wait for handshake response
        response = await connection.recv()
        handshake = json.loads(response)

        if "error" in handshake:
            raise Exception(f"Handshake failed: {handshake['error']}")

        return connection

    async def _connect_http(self, server: MCPServer) -> Dict[str, Any]:
        """Connect to HTTP MCP server"""
        import aiohttp

        # Create HTTP session with authentication
        auth = None
        headers = {}

        if "token" in server.auth_config:
            headers["Authorization"] = f"Bearer {server.auth_config['token']}"
        elif "api_key" in server.auth_config:
            headers["X-API-Key"] = server.auth_config["api_key"]

        session = aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=30))

        # Test connection with capabilities request
        async with session.get(f"{server.url}/mcp/capabilities") as response:
            if response.status != 200:
                await session.close()
                raise Exception(f"HTTP connection failed: {response.status}")

        return {"session": session, "url": server.url}

    async def _connect_stdio(self, server: MCPServer) -> asyncio.subprocess.Process:
        """Connect to stdio MCP server"""
        # Start MCP server process (shlex.split handles quoting safely)
        process = await asyncio.create_subprocess_exec(
            *shlex.split(server.url),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send initialization message
        init_message = (
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {"roots": {"listChanged": True}}},
                }
            )
            + "\n"
        )

        process.stdin.write(init_message.encode())
        await process.stdin.drain()

        # Read response
        response_line = await process.stdout.readline()
        response = json.loads(response_line.decode().strip())

        if "error" in response:
            process.terminate()
            raise Exception(f"Stdio initialization failed: {response['error']}")

        return process

    async def _discover_tools(self, server_name: str):
        """Discover available tools from connected MCP server"""
        try:
            tools_response = await self.call_tool(server_name, "tools/list", {})

            if tools_response.get("tools"):
                for tool_def in tools_response["tools"]:
                    tool = MCPTool(
                        name=tool_def["name"],
                        server=server_name,
                        description=tool_def.get("description", ""),
                        parameters=tool_def.get("inputSchema", {}),
                        required_params=tool_def.get("inputSchema", {}).get("required", []),
                    )
                    self.available_tools[f"{server_name}:{tool.name}"] = tool

                logger.info(f"Discovered {len(tools_response['tools'])} tools from {server_name}")

        except Exception as e:
            logger.error(f"Tool discovery failed for {server_name}: {e}")

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the specified MCP server

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        if server_name not in self.connections:
            # Try to connect if not already connected
            if not await self.connect_to_server(server_name):
                raise Exception(f"Cannot connect to MCP server: {server_name}")

        connection = self.connections[server_name]
        server = self.servers[server_name]

        try:
            if server.transport == MCPTransport.WEBSOCKET:
                return await self._call_websocket_tool(connection, tool_name, arguments)
            elif server.transport == MCPTransport.HTTP:
                return await self._call_http_tool(connection, tool_name, arguments)
            elif server.transport == MCPTransport.STDIO:
                return await self._call_stdio_tool(connection, tool_name, arguments)

        except Exception as e:
            logger.error(f"Tool call failed: {server_name}:{tool_name} - {e}")
            raise

    async def _call_websocket_tool(self, connection, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via WebSocket MCP connection"""
        request = {
            "jsonrpc": "2.0",
            "id": int(datetime.now().timestamp() * 1000),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        await connection.send(json.dumps(request))
        response = await connection.recv()
        result = json.loads(response)

        if "error" in result:
            raise Exception(f"MCP tool error: {result['error']}")

        return result.get("result", {})

    async def _call_http_tool(
        self, connection: Dict[str, Any], tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool via HTTP MCP connection"""
        session = connection["session"]
        url = f"{connection['url']}/mcp/tools/{tool_name}"

        async with session.post(url, json=arguments) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"HTTP tool call failed: {response.status} - {error_text}")

            return await response.json()

    async def _call_stdio_tool(
        self, process: asyncio.subprocess.Process, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call tool via stdio MCP connection"""
        request = {
            "jsonrpc": "2.0",
            "id": int(datetime.now().timestamp() * 1000),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        request_line = json.dumps(request) + "\n"
        process.stdin.write(request_line.encode())
        await process.stdin.drain()

        response_line = await process.stdout.readline()
        result = json.loads(response_line.decode().strip())

        if "error" in result:
            raise Exception(f"MCP tool error: {result['error']}")

        return result.get("result", {})

    def list_available_tools(self) -> Dict[str, MCPTool]:
        """Get list of all available tools across connected servers"""
        return self.available_tools.copy()

    def get_tool_info(self, tool_identifier: str) -> Optional[MCPTool]:
        """Get information about a specific tool"""
        return self.available_tools.get(tool_identifier)

    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for server_name, connection in self.connections.items():
            try:
                server = self.servers[server_name]

                if server.transport == MCPTransport.WEBSOCKET:
                    await connection.close()
                elif server.transport == MCPTransport.HTTP:
                    await connection["session"].close()
                elif server.transport == MCPTransport.STDIO:
                    connection.terminate()
                    await connection.wait()

                server.status = "disconnected"
                logger.info(f"Disconnected from MCP server: {server_name}")

            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")

        self.connections.clear()

    async def health_check(self) -> Dict[str, str]:
        """Check health status of all configured servers"""
        health_status = {}

        for server_name, server in self.servers.items():
            try:
                if server_name in self.connections:
                    # Test with a simple tool call
                    await self.call_tool(server_name, "tools/list", {})
                    health_status[server_name] = "healthy"
                else:
                    health_status[server_name] = "disconnected"

            except Exception as e:
                health_status[server_name] = f"error: {str(e)[:100]}"
                logger.warning(f"Health check failed for {server_name}: {e}")

        return health_status


# Global instance for easy import
_mcp_client = None


def get_mcp_client() -> MCPClient:
    """Get singleton MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
