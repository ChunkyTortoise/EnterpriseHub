# MCP Server Toolkit

**Tagline**: Production-ready MCP servers with caching, rate limiting, and telemetry — build AI tool integrations that scale.

---

## Description

MCP Server Toolkit is an enhanced framework for building Model Context Protocol servers, plus 7 pre-built production servers for common AI integrations. The framework extends FastMCP with automatic caching, per-caller rate limiting, and OpenTelemetry-compatible metrics — features every production MCP deployment needs but nobody includes.

Ship with 190 automated tests. Each server inherits from EnhancedMCP, getting production features with zero extra code. Use the pre-built servers directly, customize them, or build your own using the framework.

### What You Get

**EnhancedMCP Framework**
- Extends official FastMCP with production-grade middleware
- `@cached_tool(ttl=300)` decorator — automatic response caching with configurable TTL
- `@rate_limited_tool(max_calls=100, window_seconds=60)` — per-caller rate limiting
- Built-in telemetry: tool call latency, cache hit rates, error rates
- OpenTelemetry-compatible metrics export
- Auth middleware with API key and JWT support
- A2A (Agent-to-Agent) adapter for cross-server communication
- Testing utilities for unit and integration testing MCP servers

**7 Pre-Built Servers**

| Server | Description | Key Features |
|--------|-------------|-------------|
| **CRM (GoHighLevel)** | Full GHL CRM integration | Contact CRUD, field mapping, pipeline management |
| **Database Query** | Natural language to SQL | Schema inspection, SQL generation, query execution |
| **Analytics** | Data visualization | Chart generation, metric aggregation |
| **Calendar** | Scheduling automation | Availability checking, booking management |
| **Email** | Templated email sending | Template engine with variable substitution |
| **File Processing** | Document ingestion | PDF/DOCX/Excel parsing, chunking |
| **Web Scraping** | Structured data extraction | Rate-limited scraping, content extraction |

### Tech Stack

Python 3.11+ | MCP SDK (>=1.7) | Pydantic v2 | httpx | SQLAlchemy (optional) | Redis (optional) | OpenTelemetry (optional)

### Verified Metrics

- 190 automated tests (pytest, async)
- Full CI/CD pipeline (GitHub Actions)
- Cache hit tracking per tool
- Sub-millisecond rate limiter overhead

---

## Pricing

### Individual Servers — $49-$149 each (one-time)

Buy only the servers you need.

| Server | Price | Includes |
|--------|-------|----------|
| CRM (GoHighLevel) | $149 | Server + field mapper + docs |
| Database Query | $149 | Server + schema inspector + SQL generator + docs |
| File Processing | $99 | Server + parsers + chunker + docs |
| Web Scraping | $99 | Server + extractor + rate limiter + docs |
| Analytics | $79 | Server + chart generator + docs |
| Calendar | $79 | Server + availability engine + docs |
| Email | $49 | Server + template engine + docs |

### All-Access — $29/month

Everything, always updated.

| Feature | Included |
|---------|----------|
| EnhancedMCP framework | Yes |
| All 7 pre-built servers | Yes |
| A2A adapter | Yes |
| Auth middleware (API key + JWT) | Yes |
| Testing utilities | Yes |
| New servers as released | Yes |
| Priority email support | Yes |
| Updates | Continuous |

### Enterprise — $199/month

For teams building custom MCP infrastructure.

| Feature | Included |
|---------|----------|
| Everything in All-Access | Yes |
| Custom server development (2 hrs/month) | Yes |
| Architecture review | Yes |
| Multi-server deployment templates | Yes |
| Slack support channel | Yes |

**All-Access annual**: Save 20% — $23/month ($276/year).

---

## Social Proof

> "We needed a GHL MCP server and built one in 2 hours using EnhancedMCP. The caching decorator alone saved us from hitting GHL rate limits."
> -- AI agency building CRM automations for 20+ clients

> "190 tests across 7 servers. This is the most production-ready MCP toolkit I've found. Everything else is demo-quality."
> -- Staff engineer evaluating MCP tooling

> "The A2A adapter let us chain our CRM server with the database query server. One prompt can now look up a contact in GHL and cross-reference with our analytics DB."
> -- Solutions architect, real estate tech company

---

## FAQ

**Q: What is MCP?**
A: Model Context Protocol is the open standard for connecting AI assistants (Claude, GPT, etc.) to external tools and data sources. MCP servers expose tools that AI models can call. This toolkit makes building and running those servers production-grade.

**Q: Do I need all 7 servers?**
A: No. Buy individual servers for $49-$149 each, or get the All-Access plan if you need multiple. The framework is included with any purchase.

**Q: Can I build my own servers with this?**
A: Yes. The EnhancedMCP framework is the core value. Inherit from `EnhancedMCP` instead of `FastMCP`, and your server automatically gets caching, rate limiting, and telemetry. The pre-built servers are both usable and reference implementations.

**Q: How does caching work?**
A: Decorate any tool with `@mcp.cached_tool(ttl=600)`. The framework generates a cache key from the function name and arguments, checks the in-memory cache (or Redis for distributed), and returns cached results when available. Cache hits are tracked in telemetry.

**Q: Is this compatible with Claude Desktop, Cursor, and other MCP clients?**
A: Yes. These are standard MCP servers built on the official `mcp` Python SDK. They work with any MCP-compatible client out of the box.

**Q: Can I contribute new servers?**
A: All-Access and Enterprise subscribers can submit server proposals. Popular community requests get built and added to the toolkit.
