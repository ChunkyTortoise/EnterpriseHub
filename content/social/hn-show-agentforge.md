# Hacker News Show Post

**Title:** Show HN: AgentForge – Build multi-agent AI systems with testing built-in

**URL:** https://github.com/ChunkyTortoise/ai-orchestrator

---

I built AgentForge while developing a real estate AI assistant that coordinates multiple specialized bots (lead qualifier, buyer advisor, seller consultant). The core problem: building reliable AI agents is hard because you can't test them systematically.

AgentForge makes AI agents testable, traceable, and production-ready.

## What It Does

**Orchestration**: Route tasks to specialized agents, aggregate results, handle retries and fallbacks.

**Testing**: Mock LLM responses, assert agent behavior, run deterministic tests.

**Tracing**: Track every decision, API call, and state change. Visualize execution flows.

**Production patterns**: Circuit breakers, rate limiting, caching, timeout handling, health checks.

## Why I Built It

I started with LangChain. Testing was painful—most tests mocked LangChain's internals instead of my logic. Debugging was worse—stack traces went through 15 framework layers.

I needed something simpler:
- Test agent logic without hitting APIs
- Trace decisions for debugging
- Run reliably in production
- No framework lock-in

## Example

**Define an agent:**

```python
from agentforge import Agent, Tool

class ResearchAgent(Agent):
    """Researches topics and summarizes findings."""

    def __init__(self, llm_client):
        super().__init__(name="researcher", llm_client=llm_client)

        self.add_tool(Tool(
            name="search",
            description="Search the web",
            func=self._search
        ))

    async def execute(self, task: str) -> dict:
        """Execute research task."""
        prompt = f"Research this topic and summarize: {task}"
        response = await self.llm_client.complete(prompt)

        return {
            "summary": response["content"],
            "sources": self._extract_sources(response["content"])
        }

    def _search(self, query: str) -> list[str]:
        # Search implementation
        pass
```

**Orchestrate multiple agents:**

```python
from agentforge import Orchestrator

orchestrator = Orchestrator()
orchestrator.register(ResearchAgent(llm_client))
orchestrator.register(WriterAgent(llm_client))
orchestrator.register(EditorAgent(llm_client))

result = await orchestrator.execute_workflow([
    {"agent": "researcher", "task": "AI safety regulations 2024"},
    {"agent": "writer", "task": "Write article from research"},
    {"agent": "editor", "task": "Edit for clarity"}
])
```

**Test without hitting APIs:**

```python
from agentforge.testing import MockLLMClient

def test_research_agent():
    mock_client = MockLLMClient()
    mock_client.add_response(
        prompt_contains="Research",
        response="AI safety: EU AI Act passed in 2024..."
    )

    agent = ResearchAgent(mock_client)
    result = await agent.execute("AI safety regulations")

    assert "EU AI Act" in result["summary"]
    assert len(result["sources"]) > 0
```

**Trace execution:**

```python
from agentforge.tracing import Tracer

tracer = Tracer()
orchestrator = Orchestrator(tracer=tracer)

result = await orchestrator.execute_workflow(tasks)

# Visualize flow
tracer.export_mermaid("flow.md")
tracer.export_json("trace.json")
```

## How It's Different

**vs LangChain/LlamaIndex**: No abstractions. You write Python functions. Testing doesn't require mocking framework internals.

**vs AutoGPT/AgentGPT**: Focused on building blocks, not full agents. You control the logic.

**vs CrewAI**: Simpler. No DSL to learn. Just Python classes.

The goal isn't to replace frameworks—it's to give you tools for testing and production deployment that work with any LLM client.

## Battle-Tested

4 months in production running a real estate AI platform:
- 3 specialized bots (lead, buyer, seller)
- 5K+ conversations/day
- 99.97% uptime
- <200ms orchestration overhead

The platform handles:
- Multi-bot handoffs (lead → buyer, lead → seller)
- Context persistence across conversations
- A/B testing (4 concurrent experiments)
- Performance tracking (P50/P95/P99 latency)
- Circuit breakers (prevented 3 cascading failures)

## Tech Stack

- **Core**: Python 3.11+, asyncio, dataclasses
- **HTTP**: httpx (async client)
- **Testing**: pytest, pytest-asyncio
- **Tracing**: Mermaid diagrams, JSON export
- **Production**: Docker, FastAPI integration
- **Coverage**: 214 tests, 91% coverage

## What's Next

Short-term:
- Streamlit flow visualizer (in progress)
- OpenTelemetry integration
- More test helpers (fuzzing, property-based)

Medium-term:
- Agent marketplace (share/discover agents)
- Cost optimization tools
- LLM-as-a-judge evaluation framework

I'm also job hunting—if your company is building AI products and needs someone who cares about testing and reliability, let's talk.

## Try It

**GitHub**: https://github.com/ChunkyTortoise/ai-orchestrator

**Demo**: https://ct-agentforge.streamlit.app (Streamlit dashboard—launching this week)

**Docs**: Full documentation in repo

MIT licensed. Install with `pip install agentforge`.

Feedback welcome. What would make this more useful for your AI projects?

---

P.S. If you're building AI agents and struggling with testing/reliability, I'd love to hear your war stories. What tools are you using? What's missing?
