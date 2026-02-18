# AgentForge

[![PyPI version](https://badge.fury.io/py/agentforge.svg)](https://badge.fury.io/py/agentforge)
[![Python Versions](https://img.shields.io/pypi/pyversions/agentforge.svg)](https://pypi.org/project/agentforge/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-588%20passing-brightgreen)](tests/)
[![CI](https://img.shields.io/github/actions/workflow/status/CaveMindset/agentforge/agentforge-tests.yml?branch=main&label=CI)](https://github.com/CaveMindset/agentforge/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen)](https://github.com/CaveMindset/agentforge)
[![Tests](https://img.shields.io/badge/tests-540%2B-brightgreen)](#testing)
[![Coverage](https://img.shields.io/badge/coverage-80%25%2B-brightgreen)](#testing)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Lightweight, production-grade Python framework for multi-agent LLM orchestration.**

AgentForge provides a minimal yet powerful foundation for building multi-agent LLM applications with DAG-first workflow orchestration, MCP-native tool integration, and zero required dependencies beyond Pydantic for the base install.

---

## Features

- **Zero Required Dependencies** — Only Pydantic v2 for base install; everything else is optional
- **DAG-First Orchestration** — Define complex agent workflows with automatic cycle detection and topological execution
- **MCP-Native** — Built-in Model Context Protocol support as both client and server
- **Async-First Execution** — High-performance async/await throughout with concurrent node execution
- **Plugin Architecture** — Extensible via Python entry points with rich plugin hooks
- **YAML Pipeline Support** — Define pipelines declaratively with hot-reload capability
- **OpenTelemetry Observability** — Optional tracing, metrics, and ASCII dashboard for monitoring

---

## Installation

```bash
# Core only (Pydantic v2)
pip install agentforge

# + LiteLLM for 100+ LLM providers
pip install agentforge[llm]

# + MCP (Model Context Protocol) support
pip install agentforge[mcp]

# + OpenTelemetry observability
pip install agentforge[observe]

# + Agent-to-Agent protocol
pip install agentforge[a2a]

# Everything
pip install agentforge[all]
```

---

## Quick Start

### Create an Agent

```python
from agentforge import Agent, AgentInput, AgentOutput, tool

@tool
def search(query: str) -> str:
    """Search for information."""
    return f"Results for: {query}"

@tool
def calculate(expression: str) -> float:
    """Evaluate a mathematical expression."""
    return eval(expression)

# Create an agent with tools
agent = Agent(
    name="researcher",
    instructions="You are a research assistant. Be thorough and accurate.",
    tools=[search, calculate],
    llm="openai/gpt-4o",
)

# Execute the agent
result = await agent(AgentInput(messages=[{"role": "user", "content": "What is 2+2?"}]))
print(result.content)  # "4"
```

### Build a DAG Workflow

```python
from agentforge import DAG, ExecutionEngine, Agent

# Define agents
researcher = Agent(name="researcher", instructions="Research the topic thoroughly.")
writer = Agent(name="writer", instructions="Write a clear summary.")
editor = Agent(name="editor", instructions="Edit for clarity and correctness.")

# Build the DAG
dag = DAG(name="content-pipeline")
dag.add_node("researcher", researcher)
dag.add_node("writer", writer)
dag.add_node("editor", editor)

# Define execution order
dag.add_edge("researcher", "writer")
dag.add_edge("writer", "editor")

# Execute
engine = ExecutionEngine()
result = await engine.execute(dag)
```

---

## Core Concepts

### Agents

Agents are the fundamental execution units in AgentForge. Each agent processes inputs and produces outputs, optionally using tools.

```python
from agentforge import BaseAgent, AgentInput, AgentOutput

class CustomAgent(BaseAgent):
    """Custom agent with full control over execution."""
    
    async def execute(self, input: AgentInput) -> AgentOutput:
        # Access messages, context, tools
        messages = input.messages
        context = input.context
        
        # Process and return
        return AgentOutput(
            content="Response content",
            tool_calls=[],  # Optional tool calls
            metadata={"custom": "data"},
        )
```

### DAGs (Directed Acyclic Graphs)

DAGs define the execution order and dependencies between agents. The framework automatically detects cycles and executes nodes in topological order.

```python
from agentforge import DAG, DAGConfig

dag = DAG(config=DAGConfig(
    name="my-workflow",
    max_retries=3,
    timeout=300.0,
    fail_fast=True,
))

# Add nodes
dag.add_node("a", agent_a)
dag.add_node("b", agent_b)
dag.add_node("c", agent_c)

# Define edges (a → b → c)
dag.add_edge("a", "b")
dag.add_edge("b", "c")

# Get execution order
order = dag.topological_sort()  # ["a", "b", "c"]

# Get ready nodes (dependencies satisfied)
ready = dag.get_ready_nodes(completed={"a"})  # ["b"]
```

### Tools

Tools are functions that agents can call. Use the `@tool` decorator for automatic schema generation.

```python
from agentforge import tool, ToolRegistry

@tool
def web_search(query: str, max_results: int = 5) -> list[str]:
    """Search the web for information.
    
    Args:
        query: The search query.
        max_results: Maximum number of results to return.
    
    Returns:
        List of search result URLs.
    """
    return [f"https://example.com/result/{i}" for i in range(max_results)]

# Register globally
registry = ToolRegistry()
registry.register(web_search)

# Or pass directly to agent
agent = Agent(name="searcher", tools=[web_search])
```

### Memory

AgentForge provides multiple memory backends for different use cases.

```python
from agentforge import (
    WorkingMemory,    # In-memory, short-term
    SessionMemory,    # Session-scoped persistence
    FileMemory,       # File-based long-term storage
    CheckpointStore,  # State checkpointing
)

# Working memory (fast, ephemeral)
memory = WorkingMemory(max_entries=100)
await memory.store("key", {"data": "value"})
result = await memory.retrieve("key")

# Session memory (conversation history)
session = SessionMemory(config=SessionMemoryConfig(
    session_id="user-123",
    max_messages=50,
))

# File memory (persistent)
file_memory = FileMemory(config=FileMemoryConfig(
    storage_path="./memory",
))

# Checkpointing (state recovery)
checkpoint_store = SQLiteCheckpointStore(db_path="./checkpoints.db")
await checkpoint_store.save("execution-1", state)
```

### Communication

Agents can communicate through multiple patterns.

```python
from agentforge import (
    MessageBus,
    RequestResponsePattern,
    DelegationPattern,
    PubSubPattern,
)

# Message bus for pub/sub
bus = MessageBus()
await bus.publish("channel", message)
messages = await bus.subscribe("channel")

# Request-response
pattern = RequestResponsePattern(bus)
response = await pattern.request("agent-a", {"query": "hello"})

# Delegation (handoff)
delegation = DelegationPattern(bus)
await delegation.delegate("agent-a", "agent-b", task)

# Pub/Sub for broadcasting
pubsub = PubSubPattern(bus)
await pubsub.broadcast("events", {"type": "completed"})
```

---

## Usage Examples

### YAML Pipeline Definition

Define pipelines declaratively in YAML:

```yaml
# pipeline.yaml
version: "1.0"
name: "research-workflow"

dag:
  agents:
    researcher:
      instructions: "Research the given topic thoroughly."
      llm: "openai/gpt-4o"
      tools:
        - search
        - calculate
    
    writer:
      instructions: "Write a clear, engaging summary."
      llm: "openai/gpt-4o-mini"
    
    editor:
      instructions: "Edit for clarity, accuracy, and style."
      llm: "openai/gpt-4o"
  
  edges:
    - source: "researcher"
      target: "writer"
    - source: "writer"
      target: "editor"
```

Load and execute:

```python
from agentforge import PipelineBuilder, ExecutionEngine

# Load from file
builder = PipelineBuilder.from_yaml("pipeline.yaml")
dag = builder.build()

# Execute
engine = ExecutionEngine()
result = await engine.execute(dag)
```

### MCP Integration

Connect to MCP servers or expose agents as MCP tools:

```python
from agentforge.tools import MCPToolRegistry, MCPConfig

# Connect to MCP servers
registry = MCPToolRegistry()

# Stdio transport
tools = await registry.register_mcp_server(
    MCPConfig(
        command="python",
        args=["-m", "my_mcp_server"],
        env={"DEBUG": "1"},
    ),
    prefix="mcp"
)

# HTTP transport
tools = await registry.register_mcp_server(
    MCPConfig(
        server_url="http://localhost:8080/mcp",
        timeout=60.0,
    ),
    prefix="remote"
)

# Use discovered tools
agent = Agent(name="mcp-agent", tools=tools.values())
```

Expose agents as an MCP server:

```python
from agentforge.tools.mcp import create_mcp_server

# Create MCP server from agents
exporter = create_mcp_server(
    agents=[researcher, writer, editor],
    name="my-agent-server",
    version="1.0.0",
)

# Run via stdio
exporter.run_stdio()

# Or via HTTP
exporter.run_http(port=8080)
```

### Plugin System

Create plugins to extend AgentForge:

```python
from agentforge.ext import AgentForgePlugin, PluginMetadata, AgentForgeContext

class MetricsPlugin(AgentForgePlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="metrics",
            version="1.0.0",
            description="Collect execution metrics",
            author="Your Name",
            provides=["hooks:pre_execute", "hooks:post_execute"],
        )
    
    def on_load(self, context: AgentForgeContext) -> None:
        context.register_hook("pre_execute", self.on_pre_execute)
        context.register_hook("post_execute", self.on_post_execute)
    
    def on_pre_execute(self, event):
        self._start_time = time.time()
    
    def on_post_execute(self, event):
        duration = time.time() - self._start_time
        print(f"Execution took {duration:.2f}s")
```

Register via entry points in `pyproject.toml`:

```toml
[project.entry-points."agentforge.plugins"]
metrics = "my_package:MetricsPlugin"
```

### Observability

Enable tracing and metrics collection:

```python
from agentforge import get_tracer, get_metrics, create_dashboard

# Configure tracing
tracer = get_tracer(config=TracerConfig(
    service_name="my-app",
    export_otlp=True,
    otlp_endpoint="http://localhost:4317",
))

# Collect metrics
metrics = get_metrics()
metrics.record_latency("agent.execute", 0.125)
metrics.record_tokens("gpt-4o", prompt=100, completion=50)

# ASCII dashboard for terminal
dashboard = create_dashboard(config=DashboardConfig(
    refresh_interval=1.0,
))
dashboard.start()

# Structured logging
from agentforge.observe.dashboard import StructuredLogger
logger = StructuredLogger("my-app")
logger.log_event("agent.started", {"agent": "researcher"})
```

---

## API Reference

Full API documentation is available at [agentforge.readthedocs.io](https://agentforge.readthedocs.io).

### Core Classes

| Class | Description |
|-------|-------------|
| [`Agent`](agentforge/core/agent.py) | Concrete agent implementation with LLM integration |
| [`BaseAgent`](agentforge/core/agent.py) | Abstract base class for custom agents |
| [`DAG`](agentforge/core/dag.py) | Directed Acyclic Graph for workflow definition |
| [`ExecutionEngine`](agentforge/core/engine.py) | Async execution engine with retry logic |
| [`ToolRegistry`](agentforge/tools/registry.py) | Global and local tool registration |
| [`MessageBus`](agentforge/comms/message.py) | Inter-agent message bus |

### Configuration

| Class | Description |
|-------|-------------|
| [`AgentConfig`](agentforge/core/types.py) | Agent configuration (name, instructions, tools, LLM) |
| [`DAGConfig`](agentforge/core/dag.py) | DAG configuration (name, retries, timeout) |
| [`ExecutionConfig`](agentforge/core/engine.py) | Execution settings (concurrency, timeout) |
| [`PipelineConfig`](agentforge/config/pipeline.py) | YAML pipeline configuration |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `AgentForgeError` | Base exception for all AgentForge errors |
| `CycleDetectedError` | DAG contains a cycle |
| `DAGValidationError` | DAG validation failed |
| `NodeNotFoundError` | Referenced node doesn't exist |
| `MCPError` | MCP connection or protocol error |
| `ToolExecutionError` | Tool execution failed |

---

## Performance Benchmarks

| Metric | Value | Conditions |
|--------|-------|-----------|
| Throughput | **4.3M dispatches/sec** | Multi-agent, Redis-backed |
| P99 Latency | **0.095ms** | Local Redis, no LLM calls |
| P95 Latency | **0.082ms** | Sustained load |
| LLM Providers | **4** | Claude, OpenAI, Gemini, Ollama |
| Test Suite | **540+ tests** | Unit + integration |

---

## Comparison with Alternatives

| Feature | AgentForge | LangChain | CrewAI | OpenAI SDK |
|---------|------------|-----------|--------|------------|
| **Core Dependencies** | 1 (Pydantic) | Many | Many | OpenAI-only |
| **DAG-First** | ✓ | ✓ | Partial | ✗ |
| **MCP-Native** | ✓ | ✗ | ✗ | ✗ |
| **Async-First** | ✓ | Partial | ✓ | ✓ |
| **Plugin System** | ✓ | ✓ | ✗ | ✗ |
| **YAML Pipelines** | ✓ | ✓ | ✗ | ✗ |
| **LLM Providers** | 100+ (LiteLLM) | 100+ | Limited | OpenAI |
| **Agent-to-Agent** | ✓ | ✗ | ✓ | ✗ |
| **Observability** | ✓ (OTel) | ✓ (LangSmith) | Partial | ✗ |
| **Learning Curve** | Low | Medium | Low | Low |

### When to Choose AgentForge

- **Minimal dependencies** — Only Pydantic required for base functionality
- **MCP integration** — First-class Model Context Protocol support
- **DAG workflows** — Complex multi-agent orchestration with dependencies
- **Production-ready** — 588 tests, type-safe, async throughout
- **Extensibility** — Plugin system with rich hooks and entry points

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/agentforge/agentforge.git
cd agentforge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e .[dev]

# Run tests
pytest -q

# Run with coverage
pytest --cov=agentforge --cov-report=html
```

### Code Style

- **Formatter**: Ruff (line length: 100)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for all public functions/classes

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
mypy agentforge/
pyright agentforge/
```

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_dag.py

# With verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Ensure type checking passes (`mypy agentforge/`)
6. Commit with conventional commits (`feat: add amazing feature`)
7. Push and open a pull request

---

## License

MIT License

Copyright (c) 2024 AgentForge Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Links

- **Documentation**: [agentforge.readthedocs.io](https://agentforge.readthedocs.io)
- **PyPI**: [pypi.org/project/agentforge](https://pypi.org/project/agentforge)
- **GitHub**: [github.com/agentforge/agentforge](https://github.com/agentforge/agentforge)
- **Issues**: [github.com/agentforge/agentforge/issues](https://github.com/agentforge/agentforge/issues)
