# AgentForge — Multi-Agent Orchestration Framework Case Study

## The Challenge

Development teams building LLM-powered applications faced provider lock-in, framework bloat (LangChain's 50+ dependencies, ~50 MB install), and lack of production primitives (token-aware rate limiting, retry logic, cost tracking). Multi-agent coordination required significant custom orchestration infrastructure, and switching from Claude to Gemini to GPT-4 meant rewriting API calls and handling different response formats. Teams needed a lightweight, production-ready framework with multi-agent mesh capabilities and zero framework dependencies.

## The Solution

Built AgentForge as a unified async interface across Claude, Gemini, OpenAI, and Perplexity with **two core dependencies** (httpx, pydantic) and ~15 KB installed footprint. Provider switching requires changing a single string parameter. Implemented DAG-based workflow orchestration with consensus protocols, agent memory (sliding window + summarization), guardrails engine, and ReAct agent loop for tool-augmented reasoning. Includes Streamlit visualizer for real-time flow debugging, cost tracker per request, and token-aware rate limiter (token bucket algorithm).

## Key Results

- **4.3M tool dispatches/sec** — Benchmarked on DAG executor with 10-node workflows
- **550+ automated tests** — Unit, integration, E2E with CI/CD on every commit
- **Zero framework dependencies** — Pure Python, no LangChain/LlamaIndex bloat
- **Sub-millisecond overhead** — P99 orchestration latency of 0.095ms for agent coordination
- **Multi-provider support** — Claude, Gemini, OpenAI, Perplexity with unified interface

## Tech Stack

**Core**: Python 3.11, asyncio, httpx (async HTTP client), Pydantic validation
**Providers**: Anthropic Claude API, Google Gemini API, OpenAI API, Perplexity API
**Orchestration**: DAG executor, consensus protocols (voting, priority-based), agent mesh coordinator
**Agent Features**: ReAct loop, tool calling, memory (sliding window + summary), guardrails (PII detection, toxicity, prompt injection)
**Visualization**: Streamlit flow debugger, cost tracker, latency profiler
**Testing**: pytest, pytest-asyncio, pytest-cov (80%+ coverage)
**Deployment**: Docker Compose, GitHub Actions CI

## Timeline & Scope

**Duration**: 10 weeks (solo developer)
**Approach**: TDD with benchmark-driven optimization, feature branches with PR reviews
**Testing**: 550+ tests including provider edge cases, retry logic, rate limiting, cost calculation
**Features**: Model registry, evaluation framework, batch processor, observability collector
**Benchmarks**: 3 scripts (dispatch throughput, latency profiling, cost analysis) with RESULTS.md
**Governance**: 3 ADRs (provider abstraction, DAG execution, consensus protocols), SECURITY.md, CHANGELOG.md

---

**Want similar results?** [Schedule a free 15-minute call](mailto:caymanroden@gmail.com) | [View live demo](https://github.com/chunkytortoise/ai-orchestrator) | [GitHub Repo](https://github.com/chunkytortoise/ai-orchestrator)
