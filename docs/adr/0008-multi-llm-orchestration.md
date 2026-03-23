# ADR 0008: Multi-LLM Orchestration Strategy

## Status

Accepted

## Context

The Jorge bot system requires different AI capabilities at different points in a lead qualification conversation:

- **Conversational response generation**: Requires nuanced, instruction-following output that mirrors the lead's communication style and adheres to the compliance pipeline. Quality is paramount.
- **Market research and property data**: Requires real-time web search access and synthesis of current listings, comparables, and neighborhood data.
- **Analytical tasks**: Batch processing of lead segments, churn prediction, and conversion rate analysis. Favors throughput over latency.
- **Fallback continuity**: If the primary provider is rate-limited, down, or too slow, conversations must continue without visible degradation.

Using a single LLM provider creates concentration risk: a single provider outage would halt all bot conversations. It also forces a suboptimal provider choice — the best conversational model is not necessarily the best analytical model.

## Decision

Implement a multi-LLM orchestration layer in `services/claude_orchestrator.py` with provider-specific routing:

| Provider | Role | Justification |
|----------|------|---------------|
| **Claude (Anthropic)** | Primary conversational response generation | Best instruction-following for compliance constraints; native support for long context windows needed for conversation history |
| **Gemini (Google)** | Batch analysis, churn prediction, lead segmentation | Superior throughput on structured analytical tasks; lower cost per token for high-volume batch jobs |
| **Perplexity** | Real-time market research, property data synthesis | Web search integration provides current listing data without a separate API integration layer |
| **OpenRouter** | Fallback for any tier | Multi-provider routing handles provider outages transparently; routes to the highest-available quality model from a configurable provider list |

**Routing logic:**

- Requests tagged `task_type=conversation` go to Claude
- Requests tagged `task_type=analysis` or `task_type=batch` go to Gemini
- Requests tagged `task_type=research` go to Perplexity
- Any provider returning HTTP 429 (rate limit) or 503 triggers automatic fallback to OpenRouter
- All responses pass through the three-tier cache (ADR-0001) before provider invocation

**Cost governance:**

The `AgentMeshCoordinator` enforces per-conversation cost budgets. Each provider call records model, token count, and cost in `LLMTrace`. The `ObservabilityDashboard` computes P50/P95/P99 latency and cost-per-interaction. Budget overruns trigger a downgrade to Haiku (Claude) or Flash (Gemini) for the remainder of the conversation.

## Consequences

### Positive
- No single-provider dependency; provider outages affect at most one task type
- Task-appropriate model selection reduces cost without sacrificing quality on critical paths
- Cost governance prevents runaway expenses during traffic spikes
- Perplexity integration eliminates a separate real estate data API subscription

### Negative
- Orchestration complexity: bugs can manifest as incorrect provider routing, producing unexpected output quality
- Provider contract management across three vendors with different pricing models, rate limits, and API versions
- OpenRouter fallback introduces a fourth pricing layer and a potential second point of failure
- Testing requires mocking four distinct provider APIs; test suite must cover all fallback paths
