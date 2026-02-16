# MCP Server Toolkit

Production-ready MCP server framework with caching, rate limiting, telemetry, and pre-built servers.

## Installation

```bash
pip install mcp-server-toolkit          # Core framework
pip install mcp-server-toolkit[database] # + Database Query server
pip install mcp-server-toolkit[web]      # + Web Scraping server
pip install mcp-server-toolkit[files]    # + File Processing server
pip install mcp-server-toolkit[all]      # Everything
```

## Quick Start

```python
from mcp_toolkit import EnhancedMCP

mcp = EnhancedMCP("my-server")

@mcp.tool()
async def greet(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

@mcp.cached_tool(ttl=300)
async def expensive_query(query: str) -> str:
    """Cached tool — results stored for 5 minutes."""
    return await run_query(query)

@mcp.rate_limited_tool(max_calls=10, window_seconds=60)
async def limited_action(action: str) -> str:
    """Rate-limited tool — max 10 calls per minute."""
    return await perform_action(action)
```

## Servers

| Server | Description | Extra |
|--------|-------------|-------|
| `database_query` | Natural language to SQL with sqlglot validation | `[database]` |
| `web_scraping` | Agent-driven web scraping with LLM extraction | `[web]` |
| `file_processing` | PDF/CSV/Excel/TXT parsing + RAG chunking | `[files]` |

## Testing

```python
from mcp_toolkit import MCPTestClient

client = MCPTestClient(mcp)
result = await client.call_tool("greet", {"name": "World"})
assert result == "Hello, World!"
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
