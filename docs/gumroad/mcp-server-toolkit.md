# MCP Server Toolkit

## Headline

**Production MCP Server Framework -- Caching, Rate Limiting, Telemetry + 3 Pre-built Servers**

Build and deploy Model Context Protocol servers with enterprise features baked in. Published on PyPI. 190 tests.

---

## Value Proposition

The MCP ecosystem is growing fast, but building production-ready servers means adding caching, rate limiting, telemetry, and error handling yourself. This toolkit gives you an `EnhancedMCP` base class with all of that, plus three pre-built servers for database queries, web scraping, and file processing.

Already live on PyPI: `pip install mcp-server-toolkit`

---

## Features

### EnhancedMCP Framework
- **Decorator-based tools**: `@mcp.tool()`, `@mcp.cached_tool()`, `@mcp.rate_limited_tool()`
- **Built-in caching**: TTL-based result caching with configurable expiry
- **Rate limiting**: Per-tool call limits with sliding windows
- **Telemetry**: Request/response logging, latency tracking, error rates
- **Error handling**: Structured error responses with retry hints
- **Test utilities**: `MCPTestClient` for unit testing your tools

### Pre-built Servers

| Server | Description |
|--------|-------------|
| **Database Query** | Natural language to SQL with sqlglot validation |
| **Web Scraping** | Agent-driven scraping with LLM extraction |
| **File Processing** | PDF/CSV/Excel/TXT parsing + RAG chunking |

### Modular Installation
```bash
pip install mcp-server-toolkit          # Core framework
pip install mcp-server-toolkit[database] # + Database Query
pip install mcp-server-toolkit[web]      # + Web Scraping
pip install mcp-server-toolkit[files]    # + File Processing
pip install mcp-server-toolkit[all]      # Everything
```

---

## Technical Specs

| Spec | Detail |
|------|--------|
| Language | Python 3.11+ |
| Protocol | Model Context Protocol (MCP) |
| Framework | EnhancedMCP base class |
| Caching | TTL-based with configurable expiry |
| Rate Limiting | Sliding window per-tool |
| SQL Validation | sqlglot |
| File Parsing | PDF, CSV, Excel, TXT |
| Tests | 190 automated tests |
| Distribution | PyPI (`mcp-server-toolkit`) |
| CI/CD | GitHub Actions |

---

## What You Get

### Starter -- $129

- Full source code (framework + 3 servers)
- README + API documentation
- PyPI package access
- 190 passing tests
- Example server implementations
- Community support (GitHub Issues)

### Pro -- $199

Everything in Starter, plus:

- **Custom server development guide** (build your own MCP tools)
- **Claude Desktop integration guide** (connect to Claude)
- **Deployment guide** (Docker + systemd + cloud)
- **Security hardening checklist** (input validation, auth)
- **1-hour setup call** via Zoom
- Priority email support (48hr response)

### Enterprise -- $399

Everything in Pro, plus:

- **Custom MCP server development** (1 server built to your spec)
- **Integration with your existing infrastructure** (databases, APIs)
- **Multi-server orchestration setup**
- **Architecture review** of your MCP deployment
- **30-day dedicated support** via Slack channel
- **SLA**: 24hr response, 72hr bug fix

---

## Who This Is For

- **AI developers** building Claude/LLM tool integrations
- **Platform teams** standardizing MCP server infrastructure
- **Agencies** deploying MCP servers for clients
- **Open-source contributors** who want a production-grade starting point

---

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
    """Cached for 5 minutes."""
    return await run_query(query)

@mcp.rate_limited_tool(max_calls=10, window_seconds=60)
async def limited_action(action: str) -> str:
    """Max 10 calls per minute."""
    return await perform_action(action)
```

---

## Proof

- 190 automated tests, all passing
- Live on PyPI: `pip install mcp-server-toolkit`
- 3 production-ready servers included
- Part of an 8,500+ test portfolio across 11 production repos
- Built by an engineer with 4.3M tool dispatches/sec in production
