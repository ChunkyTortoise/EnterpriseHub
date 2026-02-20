# AgentForge vs. The Alternatives

A feature-by-feature comparison of AgentForge against the most popular multi-agent frameworks.

## Feature Matrix

| Feature | AgentForge | CrewAI | AutoGPT | Haystack | LangGraph |
|---------|:----------:|:------:|:-------:|:--------:|:---------:|
| **Core Architecture** | | | | | |
| Zero external dependencies | ✅ (Pydantic only) | ❌ | ❌ | ❌ | ❌ |
| DAG-first execution model | ✅ | ❌ | ❌ | ✅ | ✅ |
| MCP (Model Context Protocol) native | ✅ | ⚠️ | ❌ | ❌ | ⚠️ |
| Async/await throughout | ✅ | ⚠️ | ❌ | ⚠️ | ✅ |
| Agent-to-Agent protocol | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Developer Experience** | | | | | |
| PyPI published | ✅ | ✅ | ✅ | ✅ | ✅ |
| Interactive Streamlit demo | ✅ | ❌ | ❌ | ❌ | ❌ |
| Built-in trace viewer (OTel) | ✅ | ⚠️ | ❌ | ✅ | ✅ |
| Benchmark suite included | ✅ | ❌ | ❌ | ⚠️ | ❌ |
| YAML pipeline definition | ✅ | ❌ | ❌ | ✅ | ❌ |
| Plugin architecture (entry points) | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Performance** | | | | | |
| Dispatch throughput | See benchmark artifact | ~50K/sec | ~10K/sec | ~100K/sec | ~200K/sec |
| P99 framework overhead | See benchmark artifact | ~380ms | ~500ms | ~180ms | ~140ms |
| P95 framework overhead | See benchmark artifact | ~250ms | ~400ms | ~120ms | ~95ms |
| **Dependencies** | | | | | |
| Dependency count (base) | **1** (Pydantic) | 47 | 89 | 112 | 23 |
| Python version support | 3.11+ | 3.10+ | 3.10+ | 3.8+ | 3.9+ |
| **Testing** | | | | | |
| Test count | **680+** | ~200 | ~150 | ~400 | ~300 |
| Coverage | 80%+ | Unknown | Unknown | ~75% | ~70% |

*AgentForge benchmark evidence: `evidence/benchmarks/2026-02-20.json`. Competitor values are approximate public/community estimates.*

## When to Choose AgentForge

**Choose AgentForge when:**
- You need reproducible benchmarked performance with evidence artifacts
- You're building MCP-first pipelines using Claude's native tool protocol
- Dependency hygiene matters -- no transitive dependency risks (1 dep vs. 47-112)
- You want built-in observability (OpenTelemetry), tracing, and an ASCII dashboard out of the box
- You're shipping to Streamlit Cloud or lightweight deployment targets
- You need YAML-defined pipelines with programmatic builders (`PipelineBuilder.from_yaml`)

## When to Choose Alternatives

| Alternative | Choose when... |
|-------------|----------------|
| **CrewAI** | Your team prefers role-based agent abstractions and "crew" mental model |
| **AutoGPT** | You want autonomous goal-seeking behavior with broad internet access |
| **Haystack** | Building pure RAG/document pipelines with Elasticsearch or OpenSearch |
| **LangGraph** | You prefer explicit graph-based state machines within the LangChain ecosystem |

## Quick Start Comparison

```python
# AgentForge -- minimal, explicit
from agentforge import Agent, DAG, ExecutionEngine

researcher = Agent(name="researcher", instructions="Research the topic thoroughly.")
writer = Agent(name="writer", instructions="Write a clear summary.")

dag = DAG(name="content-pipeline")
dag.add_node("researcher", researcher)
dag.add_node("writer", writer)
dag.add_edge("researcher", "writer")

result = await ExecutionEngine().execute(dag)

# CrewAI -- role-heavy, verbose
from crewai import Agent, Task, Crew
planner = Agent(role="Planner", goal="Plan tasks", backstory="You are an expert planner...")
task = Task(description="Research market trends", agent=planner)
crew = Crew(agents=[planner], tasks=[task])
# ... 20+ more lines of setup before execution
```

## Architecture Comparison

| Concept | AgentForge | CrewAI | LangGraph |
|---------|-----------|--------|-----------|
| Workflow model | DAG (topological sort) | Sequential/hierarchical | State machine |
| Agent definition | `Agent` class + `@tool` decorator | Role + backstory + goal | Node functions |
| Communication | MessageBus (pub/sub, req/resp, delegation) | Shared memory | State passing |
| Tool integration | `@tool` decorator + MCP registry | LangChain tools | LangChain tools |
| Persistence | Working/Session/File memory + checkpoints | Shared memory | Checkpointer |

## Resources

- [AgentForge README](../README.md)
- [Benchmarks](../README.md#performance-benchmarks)
- [Benchmark Evidence](../evidence/benchmarks/README.md)
- [Examples](../README.md#usage-examples)
- [API Reference](../README.md#api-reference)
