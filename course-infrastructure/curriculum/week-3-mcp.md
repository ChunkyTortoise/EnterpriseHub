# Week 3: MCP + Tool Integration (MCP Server Toolkit)

## Overview

This week covers the Model Context Protocol — the standard for connecting AI agents to external tools. Students build 2 custom MCP servers and connect them to an AI agent.

**Repo**: MCP Server Toolkit
**Lab**: Build 2 custom MCP servers (database query + web scraping)

## Learning Objectives

By the end of this week, students will be able to:
1. Explain the MCP protocol: server, client, transport, and tool definitions
2. Build an MCP server that exposes tools with typed schemas
3. Implement authentication and authorization for MCP servers
4. Handle errors and rate limiting across MCP boundaries
5. Connect multiple MCP servers to a single AI agent

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: MCP Protocol Fundamentals (15 min)

**What is MCP?**
- Model Context Protocol: a standard for AI tool integration
- Server: exposes tools (your code)
- Client: consumes tools (the AI agent / IDE)
- Transport: stdio, HTTP/SSE, WebSocket

**Why MCP matters:**
- Before MCP: every AI app reinvents tool integration
- After MCP: one protocol, any tool, any agent
- Ecosystem: Claude Desktop, VS Code, Cursor, custom clients

**Protocol flow:**
```
Client → initialize → Server
Client → tools/list → Server (returns tool definitions)
Client → tools/call(name, args) → Server (executes tool, returns result)
```

### Part 2: Live Coding — Build an MCP Server (45 min)

1. **Server scaffolding** (10 min)
   - Project structure: server.py, tools/, config
   - MCP SDK setup: `@mcp.tool()` decorator
   - Tool definition: name, description, input schema (JSON Schema)

2. **Database query tool** (15 min)
   - Tool: `query_database` — accepts SQL, returns results
   - Input validation: prevent SQL injection, limit result size
   - Schema definition with Pydantic models
   - Error handling: connection errors, query timeouts, invalid SQL

3. **Web scraping tool** (10 min)
   - Tool: `scrape_webpage` — accepts URL, returns structured content
   - Content extraction: HTML to markdown
   - Rate limiting: respect robots.txt, throttle requests
   - Error handling: timeouts, blocked requests, malformed HTML

4. **Running and testing** (10 min)
   - Start server in stdio mode
   - Connect from Claude Desktop
   - Test tool execution end-to-end
   - Debug common issues: schema mismatches, serialization errors

### Part 3: Lab Introduction (15 min)

- Lab 3 README walkthrough
- Two servers to build: database query + web scraping
- Autograder tests: tool listing, tool execution, error handling
- Bonus: connect both servers to a single agent

### Part 4: Q&A (15 min)

## Session B: Lab Review + Deep Dive (Thursday)

### Part 1: Lab Solution Review (20 min)

Common patterns and mistakes:
- Missing input validation (accepting arbitrary SQL without sanitization)
- Not handling tool execution errors (crashing the server)
- Schema definitions that don't match actual tool behavior
- Transport confusion (stdio vs HTTP for different clients)

### Part 2: Deep Dive — Production MCP Patterns (40 min)

**Authentication:**
- API key authentication for MCP servers
- OAuth2 integration for accessing protected resources
- Per-tool permission scoping (read-only vs read-write)

**Rate limiting:**
- Rate limiting at the MCP server level
- Propagating rate limit errors to the AI agent
- Backoff strategies when downstream services are throttled

**Error handling:**
- MCP error codes and messages
- Distinguishing tool errors from server errors
- Retry logic for transient failures
- Graceful degradation when tools are unavailable

**Testing MCP servers:**
- Unit tests: test tool logic independently
- Integration tests: test via MCP client
- `MCPTestClient` pattern: programmatic tool invocation
- Snapshot testing: verify tool output format stability

**Multi-server architecture:**
- Connecting multiple MCP servers to one agent
- Tool naming conventions to avoid collisions
- Server discovery and dynamic tool loading

### Part 3: Case Study (20 min)

EnterpriseHub's MCP integration:
- 5 MCP servers (memory, postgres, redis, stripe, playwright)
- How the agent mesh routes to the right server
- Error propagation from MCP server to user-facing response
- Monitoring MCP server health and latency

### Part 4: Week 4 Preview (10 min)

## Key Takeaways

1. MCP standardizes tool integration — build once, connect anywhere
2. Input validation is critical: AI agents will send unexpected inputs
3. Always handle errors gracefully — the agent needs useful error messages
4. Rate limiting at the MCP boundary protects downstream services
5. Test MCP servers programmatically, not just via Claude Desktop

## Resources

- MCP specification: modelcontextprotocol.io
- MCP Server Toolkit repository
- MCP Python SDK documentation
- Claude Desktop MCP configuration guide
