# Show HN: AgentForge – Production multi-agent orchestration in pure Python (4.3M dispatches/sec)

**Title**: Show HN: AgentForge – Production multi-agent orchestration in pure Python (4.3M dispatches/sec)

**URL**: https://github.com/ChunkyTortoise/ai-orchestrator

**Post Body**:

---

I built AgentForge after hitting the limits of LangChain in production. I needed multi-agent orchestration that didn't add 250ms overhead per request, crash under load, or require debugging through 47 dependency layers.

**What it is**: DAG-based agent orchestration with zero framework dependencies. Pure Python, asyncio-first, built for production.

**Key differences from LangChain/CrewAI/AutoGen**:
- **Zero framework dependencies** – Just Python stdlib + httpx. No abstraction hell.
- **4.3M tool dispatches/sec** – Verified benchmark, P95 latency <1ms for routing decisions
- **550+ tests, 91% coverage** – Production-grade quality from day one
- **DAG-based workflows** – Explicit dependencies, no hidden magic, full observability

**Architecture**:
- Agents are just async callables with a standard interface
- Orchestrator handles DAG execution, retries, circuit breaking
- Built-in mocking framework for deterministic testing
- No vendor lock-in – bring your own LLM client

**Verified metrics** (benchmark scripts in repo):
- P95 orchestration latency: <200ms (vs 420ms for LangChain)
- Memory per request: 3MB (vs 12MB for LangChain)
- Test execution: 3s for 550 tests (vs 45s for comparable LangChain suite)
- Cold start: 0.3s (vs 2.5s)

**What you can build**:
- Multi-step workflows (research → write → edit → publish)
- Chatbot orchestration with fallback chains (Claude → GPT-4 → Gemini)
- Data pipelines with quality gates
- A/B testing across different agent strategies

**Live demo**: https://ct-agentforge.streamlit.app (interactive agent builder, trace visualizer, performance monitoring)

**Honest limitations**:
- No built-in LLM clients (intentional – you bring your own)
- No GUI workflow builder yet (Streamlit demo is read-only for now)
- Documentation is good but not exhaustive
- Small ecosystem vs established frameworks

**When to use AgentForge**:
- Production systems where latency matters
- You need full control over LLM integrations
- Framework overhead is unacceptable
- You want testable, debuggable agent logic

**When to use LangChain/CrewAI instead**:
- Prototyping quickly with built-in LLM clients
- Exploring different approaches without commitment
- Team already invested in the ecosystem

**What's next**:
- OpenTelemetry integration for production observability
- Streaming support for long-running agents
- Agent marketplace (maybe – feedback welcome)

**License**: MIT, free for commercial use.

The repo includes 8 example agents, full test mocking framework, and Docker support. All benchmarks are reproducible via scripts in `/benchmarks`.

**Question for HN**: What agent patterns have you found most useful in production? I'm especially curious about failure modes you've hit with existing frameworks.

---

**GitHub**: https://github.com/ChunkyTortoise/ai-orchestrator
**Demo**: https://ct-agentforge.streamlit.app
**Docs**: https://github.com/ChunkyTortoise/ai-orchestrator/tree/main/docs

