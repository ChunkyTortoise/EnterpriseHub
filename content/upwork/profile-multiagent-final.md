# Multi-Agent Systems Specialist — READY TO PASTE

Generated: 2026-02-18

---

## Headline (62/70 chars)
```
Multi-Agent AI Systems Engineer | 4.3M Dispatches/sec | Python
```

## Overview (2700/5000 chars)
```
Building a single LLM call is straightforward. Building a system where ten agents coordinate, share state, recover from failures, stay within budget, and produce auditable results — that is an engineering problem most AI developers have not solved at scale. I have.

AgentForge, my open-source multi-agent orchestration engine, processes 4.3 million tool dispatches per second with P99 latency of 0.095ms. That number is not a benchmark artifact — it reflects a design built around zero-copy dispatch, lock-free coordination, and agent isolation that prevents one failing tool from cascading to the rest of the pipeline. The framework supports 4 LLM providers (Claude, OpenAI, Gemini, Ollama) through a unified API with automatic failover and cost tracking.

What I build for engineering teams:

- Multi-agent orchestrators with ReAct loop, planning, reflection, and tool-use patterns
- Agent mesh architectures with role specialization, shared memory, and result aggregation
- LLM cost optimization: 3-tier Redis semantic caching (89% cost reduction at 88% hit rate), circuit breakers, fallback chains, streaming with token budget enforcement
- A2A (Agent-to-Agent) protocol bridges for cross-system agent communication
- Evaluation frameworks for non-deterministic agent behavior — the part most teams skip

Why testing-first matters for AI agents:

Non-deterministic systems fail in non-deterministic ways. I write evaluation harnesses before writing agent logic — adversarial inputs, edge cases, latency regression tests, cost budget assertions. AgentForge alone carries 540+ automated tests. Across my full portfolio: 8,500+ tests, all CI green, with 33 Architecture Decision Records documenting every non-obvious design choice.

Technical depth:

I implement ReAct (Reasoning + Acting) loops, chain-of-thought with reflection, tool calling via FastMCP v2 (my published PyPI package: mcp-server-toolkit), token cost tracking per agent, and circuit breaker patterns on all external LLM calls. I have built production agent systems on Claude API, GPT-4, Gemini, and local Ollama models — and I know exactly where each model breaks under pressure.

Tech stack for agent work:

LLMs: Claude API, GPT-4, Gemini, Ollama | Orchestration: custom ReAct, FastMCP v2, A2A protocol | Backend: FastAPI (async), Python 3.11+ | Caching: Redis (L1/L2/L3 semantic cache) | Testing: pytest, TDD, 80%+ coverage | Infra: Docker, GitHub Actions | Published: mcp-server-toolkit on PyPI

Want to see it run?

Live demo: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/ — watch the dispatch throughput and agent coordination in real time. Describe your pipeline and I can sketch the architecture in one message.
```

## Skills Tags (14)
```
1. Python
2. Multi-Agent Systems
3. LLM Integration
4. FastAPI
5. Redis
6. Agent Orchestration
7. Claude API
8. OpenAI API
9. Gemini API
10. AI Architecture
11. Distributed Systems
12. Real-Time Processing
13. Performance Optimization
14. API Development
```

## Hourly Rate
$125-$175/hr

## Character Counts
- Headline: 62 chars
- Overview: 2700 chars
