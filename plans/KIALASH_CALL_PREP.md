# Kialash Persad Call Prep -- Architecture Walkthrough
**Date**: Tuesday, February 10, 2026, 4:00 PM EST
**Role**: Senior AI Agent Systems Engineer (Multilingual, Multi-Channel, Multi-Tenant)
**Format**: 5-minute architecture walkthrough, then Q&A

---

## Opening Pitch (30 seconds)

> "I'm Cayman Roden, an AI engineer who builds production multi-agent systems. EnterpriseHub is my flagship project -- a real estate AI platform with 3 specialized conversational bots that hand off conversations to each other in real time, coordinated by a centralized orchestration layer with confidence-threshold routing, tiered caching, and full observability. It's backed by 5,000+ tests in the main repo, 7,800+ across 11 repos, all CI green. Let me walk you through the architecture."

---

## Architecture Diagram

```
                           ┌──────────────────────────────────────────┐
                           │          Inbound Message (SMS/Web/Voice) │
                           └──────────────────┬───────────────────────┘
                                              │
                                   ┌──────────▼──────────┐
                                   │  Tag-Based Router    │
                                   │  (GHL CRM Webhooks)  │
                                   └──────┬───┬───┬───────┘
                                          │   │   │
                    ┌─────────────────────┘   │   └──────────────────────┐
                    │                         │                          │
          ┌─────────▼──────────┐  ┌──────────▼──────────┐  ┌───────────▼──────────┐
          │   Lead Bot         │  │   Buyer Bot          │  │   Seller Bot          │
          │ (LeadBotWorkflow)  │  │ (JorgeBuyerBot)      │  │ (JorgeSellerBot)      │
          │                    │  │                      │  │                       │
          │ - 3-7-30 day seq   │  │ - Financial readiness│  │ - FRS/PCS scoring     │
          │ - Ghost re-engage  │  │ - Property matching  │  │ - CMA generation      │
          │ - Intent decoding  │  │ - Buyer intent decode│  │ - Listing strategy    │
          │ - LangGraph FSM    │  │ - GHL tag integration│  │ - GHL tag integration │
          └────────┬───────────┘  └──────────┬───────────┘  └───────────┬───────────┘
                   │                         │                          │
                   └─────────────┬───────────┘──────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  JorgeHandoffService      │
                    │                           │
                    │  - Confidence thresholds   │
                    │    (0.6 - 0.8 per route)  │
                    │  - Circular prevention     │
                    │    (30-min window)         │
                    │  - Rate limiting           │
                    │    (3/hr, 10/day)          │
                    │  - Contact-level locking   │
                    │  - Pattern learning        │
                    │    (min 10 samples)        │
                    │  - EnrichedHandoffContext  │
                    └────────────┬──────────────┘
                                 │
          ┌──────────────────────┼───────────────────────────┐
          │                      │                           │
┌─────────▼──────────┐  ┌───────▼────────────┐  ┌──────────▼────────────┐
│  ClaudeOrchestrator │  │  AgentMeshCoord    │  │  Observability Stack  │
│                     │  │                    │  │                       │
│ - Multi-strategy    │  │ - Agent registry   │  │ - PerformanceTracker  │
│   response parsing  │  │ - SLA enforcement  │  │   (P50/P95/P99)      │
│ - L1/L2/L3 cache    │  │ - Cost governance  │  │ - BotMetricsCollector │
│ - Memory context    │  │   ($50/hr budget)  │  │ - AlertingService     │
│ - Specialist handoff│  │ - Multi-criteria   │  │   (7 default rules)  │
│ - Tool orchestration│  │   agent scoring    │  │ - 3-level escalation  │
│   (5-turn loop)     │  │ - Health monitors  │  │ - OTel tracing        │
└─────────────────────┘  └────────────────────┘  └───────────────────────┘
          │                      │                           │
          └──────────────────────┼───────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │  PostgreSQL + Redis       │
                    │  + GoHighLevel CRM        │
                    └──────────────────────────┘
```

---

## Section 1: Multi-Agent Handoff Architecture (1 min)

### Key Talking Points

**Three specialized bots with distinct workflows:**
- `LeadBotWorkflow` (`lead_bot.py:631`) -- LangGraph state machine, 3-7-30 day follow-up, ghost re-engagement. Accepts an `IndustryConfig` for domain-agnostic operation.
- `JorgeBuyerBot` (`jorge_buyer_bot.py:183`) -- Financial readiness scoring, property matching, buyer intent decoding.
- `JorgeSellerBot` (`jorge_seller_bot.py:264`) -- FRS/PCS scoring, CMA generation, listing strategy.

**Confidence-threshold routing via `JorgeHandoffService`:**
- Each route has its own threshold (not one-size-fits-all):
  ```python
  THRESHOLDS = {
      ("lead", "buyer"):  0.7,
      ("lead", "seller"): 0.7,
      ("buyer", "seller"): 0.8,  # Higher -- cross-intent is harder
      ("seller", "buyer"): 0.6,  # Lower -- sell-first-then-buy is natural
  }
  ```
- Thresholds are **dynamically adjusted** via pattern learning from historical outcomes (`get_learned_adjustments()`): if success rate > 80%, threshold drops by 0.05; if < 50%, it rises by 0.1. Requires minimum 10 data points.
- Intent signals extracted from last 5 messages via regex patterns (8 buyer patterns, 8 seller patterns), blended 50% with current conversation scores.

**Safeguards (production-critical for multi-tenant):**
- **Circular prevention**: Two-layer check -- (1) same source->target within 30-min window, (2) full chain cycle detection.
- **Rate limiting**: 3 handoffs/hour, 10/day per contact. Class: `_check_rate_limit()`.
- **Contact-level locking**: `_acquire_handoff_lock()` with 30s timeout prevents concurrent handoffs for the same contact.
- **Enriched context transfer**: `EnrichedHandoffContext` dataclass carries qualification score, temperature, budget range, property address, CMA summary, conversation summary, key insights, and urgency level -- so the receiving bot never re-asks what the previous bot already knows.

**Relevant code reference:**
- `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py` -- `evaluate_handoff()` (line 611), `execute_handoff()` (line 701)
- Tag-based routing via GHL CRM: remove source tag, add target tag, add tracking tag (e.g., `Handoff-Lead-to-Buyer`)

---

## Section 2: Orchestration Layer (1 min)

### Key Talking Points

**`ClaudeOrchestrator` (`claude_orchestrator.py:80`) -- Unified AI Intelligence Layer:**
- Single entry point: `process_request(ClaudeRequest) -> ClaudeResponse`
- 11 task types (enum `ClaudeTaskType`): chat, lead analysis, report synthesis, script generation, intervention strategy, behavioral insight, omnipotent assistant, persona optimization, executive briefing, revenue projection, research query
- **Multi-strategy response parsing** (handles messy LLM output):
  - `_extract_json_block()` -- 3 strategies: markdown code blocks, generic code blocks, balanced-bracket JSON extraction
  - `_parse_confidence_score()` -- 4 strategies: JSON field, percentage text, decimal text, qualitative mapping ("high confidence" -> 0.9)
  - `_parse_recommended_actions()` -- JSON extraction or markdown section parsing with auto-priority/timing classification
- **Tool orchestration loop** (5-turn max): calls MCP tools in parallel (`asyncio.gather`), with specialist handoff prompts that switch the system prompt based on tool category (Discovery, Analysis, Strategy, Action, Governance)
- **Memory context injection**: In-process cache + Graphiti semantic memory. Lead context enhanced with scoring, churn analysis (ML + sentiment drift + psychographic profiling), all run in parallel with `asyncio.gather` + 7s timeout.

**`AgentMeshCoordinator` (`agent_mesh_coordinator.py:139`) -- Enterprise Governance:**
- Dynamic agent registration with health check validation
- Multi-criteria agent scoring (40% performance, 25% availability, 20% cost efficiency, 15% response time) with priority boost for emergency tasks (1.5x)
- Budget controls: $50/hr max, $100 emergency shutdown threshold, per-user quotas (20 tasks/hr)
- 4 background monitors: health (30s), cost (5min), performance (2min), cleanup (1hr)
- Auto-scale trigger when average queue time > 30s; rebalance when load imbalance > 30%

**Relevant code reference:**
- `ClaudeOrchestrator.__init__()` initializes 5 MCP intelligence servers (Lead, Property, Market, Negotiation, Analytics)
- `_calculate_agent_score()` at line 301 of `agent_mesh_coordinator.py`

---

## Section 3: Caching and Performance (1 min)

### Key Talking Points

**Redis L1/L2/L3 Caching Strategy:**
- L1: In-process `TTLLRUCache` (lead_bot.py:106) -- thread-safe, max 1000 entries, 60-min TTL, LRU eviction, hit/miss/eviction stats
- L2: Redis (shared across instances) -- parameterized by tenant_id in `ClaudeOrchestrator`
- L3: PostgreSQL-backed (cold storage for semantic memory context)
- Target: <200ms overhead for orchestration layer

**`PerformanceTracker` (Singleton, `performance_tracker.py:102`):**
- Tracks P50/P95/P99 latency per bot per operation
- Rolling windows: 1h, 24h, 7d (configurable in `WINDOWS` dict)
- Thread-safe with `threading.Lock`, deque-backed (max 10,000 entries per window)
- SLA targets from audit spec:
  ```
  Lead Bot:   P50 < 500ms,  P95 < 2000ms, P99 < 3000ms
  Buyer Bot:  P50 < 800ms,  P95 < 2500ms, P99 < 3500ms
  Seller Bot: P50 < 700ms,  P95 < 2500ms, P99 < 3500ms
  Handoff:    P50 < 100ms,  P95 < 500ms,  P99 < 800ms
  ```
- `check_sla_compliance()` returns per-bot/per-operation compliance with violation details
- Async context manager: `async with tracker.track_async_operation("lead_bot", "process")` for zero-boilerplate timing
- Decorator: `@track_performance("lead_bot", "qualify")` for function-level tracking
- Optional PostgreSQL persistence via `set_repository()` for write-through

**`BotMetricsCollector` (Singleton, `bot_metrics_collector.py:63`):**
- Records bot interactions and handoff events inline (minimal overhead)
- `feed_to_alerting()` pushes 7 aggregated metrics to AlertingService for threshold evaluation
- Thread-safe, DB persistence via repository pattern

**`AlertingService` (`alerting_service.py:234`):**
- 7 default alert rules aligned with audit spec (SLA violation, high error rate, low cache hit rate, handoff failure, bot unresponsive, circular handoff spike, rate limit breach)
- Multi-channel notifications: email (SMTP), Slack (webhook), generic webhook, PagerDuty (Events API v2), Opsgenie
- 3-level escalation policy: Level 1 (0s) immediate, Level 2 (5min) re-send unacknowledged to all channels, Level 3 (15min) escalate to PagerDuty/Opsgenie
- Cooldown periods to prevent alert spam (5-10 min per rule)
- Alert acknowledgment with time-to-ack tracking

---

## Section 4: Testing Infrastructure (30 sec)

### Key Talking Points

**7,800+ tests across 11 repositories, all CI green:**
- EnterpriseHub alone: ~5,000 tests
- TDD workflow: red-green-refactor cycle enforced
- CI/CD: GitHub Actions, pre-commit hooks (ruff auto-fix), pyright type checking
- Singletons all have `reset()` classmethod for test isolation (`PerformanceTracker.reset()`, `AlertingService.reset()`, `BotMetricsCollector.reset()`)
- Every service has a `set_repository()` pattern for dependency injection -- tests use mocks, production uses PostgreSQL
- OpenTelemetry tracing via `@trace_operation()` decorator across all Jorge services (handoff, performance, alerting, metrics)

**Key test patterns:**
- Thread-safety tests for all singleton services
- Rolling window edge cases (empty windows, boundary conditions)
- Handoff chain cycle detection (A->B->C->A blocked)
- Rate limit boundary tests (exactly at limit vs. over)
- Alert cooldown and escalation timing tests

---

## Section 5: Multi-Tenant / Multi-Channel Readiness (30 sec)

### Key Talking Points

**Multi-tenant foundations already in place:**
1. **`IndustryConfig` (`config/industry_config.py`)** -- YAML-driven config decouples domain from logic:
   - `BotPersonality`: name, role, approach, core values, Jinja2 system prompt templates
   - `IntentMarkers`: high/medium/low confidence signal lists
   - `IntentConfig`: patterns, weights, thresholds
   - `HandoffConfig`: buyer/seller intent patterns, threshold overrides per route
   - `IndustryConfig.default_real_estate()` factory method; swap YAML file for dental, HVAC, etc.
   - Already wired into `LeadBotWorkflow.__init__()`, `LeadIntentDecoder`, `JorgeHandoffService`

2. **Multi-tenant compliance platform** (`compliance_platform/multitenancy/models.py`):
   - `SubscriptionTier` enum: Free, Starter, Professional, Enterprise (with hierarchy levels)
   - `OrganizationStatus` lifecycle: Active, Suspended, Trial, Cancelled, Pending Activation
   - RBAC permissions, tenant context for request isolation, audit logging
   - Middleware for per-request tenant scoping

3. **`tenant_id` threading throughout:**
   - `ClaudeRequest` has `tenant_id: Optional[str]` field
   - `ClaudeOrchestrator.process_request()` passes `tenant_id` through to LLM client
   - `AgentMeshCoordinator` tracks per-user quotas (extensible to per-tenant)

**Multi-channel:**
- Current: SMS (GHL), Email (SendGrid), Voice (Retell AI), Web (Streamlit)
- Architecture is channel-agnostic: bots receive message dicts, not channel-specific payloads
- `MessageType` enum in API schemas normalizes channel inputs
- `AlertChannelConfig` supports email, Slack, webhook, PagerDuty, Opsgenie

**CRM-agnostic adapter layer:**
- `CRMProtocol` ABC with `CRMContact` model -- vendor-independent interface
- `GHLAdapter` (GoHighLevel) and `HubSpotAdapter` -- two production adapters proving portability
- `services/crm/protocol.py`, `ghl_adapter.py`, `hubspot_adapter.py` -- clean separation
- Adding a new CRM = implement 5 async methods (get, create, update, search, sync_lead)

**Broader portfolio (11 repos, 7,800+ tests):**
- `ai-orchestrator (AgentForge)` (423 tests): Multi-provider orchestrator with ReAct agent loop, tool chaining, agent memory, multi-agent mesh, evaluation framework, model registry, cost tracking, tracing, REST API
- `docqa-engine` (501 tests): RAG pipeline with hybrid BM25+dense retrieval, cross-encoder re-ranking, query expansion, answer quality scoring, conversation manager, document relationship graph, REST API
- `insight-engine` (521 tests): BI analytics with statistical testing, KPI framework, advanced anomaly detection (Isolation Forest, LOF, Mahalanobis), regression diagnostics, dimensionality reduction, forecasting, clustering
- `llm-integration-starter` (220 tests): Multi-provider LLM client with guardrails engine (injection detection, PII redaction), circuit breaker, fallback chains, streaming, caching
- All repos have CI/CD, typed Python, comprehensive tests

**What's needed to go full multi-tenant:**
- Tenant-scoped Redis cache keys (prefix with tenant_id)
- Per-tenant SLA targets in PerformanceTracker
- Per-tenant IndustryConfig loading (already wired, just needs a config store)
- Database row-level security or schema-per-tenant

---

## Questions to Ask Him

### About His System
1. "How many agents are in your current system, and what's the handoff model -- hub-and-spoke or peer-to-peer?"
2. "What languages are you supporting, and are conversations mixed-language within a single session or per-session?"
3. "What's your current latency target for agent responses? What percentile do you measure (P95, P99)?"
4. "How do you handle tenant isolation -- shared database with RLS, schema-per-tenant, or separate instances?"
5. "What's your agent orchestration stack -- LangGraph, AutoGen, custom state machines, or something else?"

### About the Role
6. "What does the first 30-day deliverable look like for this role?"
7. "How large is the engineering team, and would I be building the agent framework or extending an existing one?"
8. "What's the production scale -- conversations per day, number of tenants, geographic distribution?"
9. "Are you using a single LLM provider or multi-provider with fallback? What's the token budget strategy?"

### Technical Deep-Dive (If Time)
10. "How do you evaluate agent quality -- automated eval sets per language, human review, or both?"
11. "What's the deployment model -- Kubernetes, serverless, or managed services?"
12. "Is there an existing observability stack (Datadog, Grafana, custom), or is that part of the build?"

---

## Closing -- Mapping Experience to His Needs

> "To summarize how my experience maps to what you need:
>
> **Multi-agent**: I've built and shipped a 3-bot system with production-grade handoff, confidence routing, circular prevention, and rate limiting -- the exact patterns needed for scaling to N agents.
>
> **Multi-tenant**: I've already built the `IndustryConfig` abstraction that decouples domain knowledge from bot logic via YAML configs, plus a multi-tenant compliance platform with subscription tiers, RBAC, and tenant isolation middleware.
>
> **Multi-channel**: My bots are channel-agnostic by design -- they receive normalized message dicts and produce responses that get formatted per channel (SMS, email, voice, web).
>
> **Multilingual**: As I mentioned, my approach is language detection at the edge, leverage LLM native multilingual capabilities, structured data translation for domain terms, and per-language eval sets for quality. I'd be excited to implement that at scale.
>
> **Observability**: I've built P50/P95/P99 tracking, 7-rule alerting with 3-level escalation (PagerDuty/Opsgenie), OpenTelemetry tracing, and metrics collection -- all integrated and tested.
>
> **Testing discipline**: 7,800+ tests across 11 repos, TDD, CI/CD. This scales well for multi-tenant systems where regressions are expensive.
>
> **Agent frameworks**: I also built AgentForge -- a standalone multi-LLM orchestrator with a ReAct agent loop, tool registry, agent memory with TTL/LRU eviction, multi-agent mesh with consensus voting, evaluation framework, and model registry. 423 tests, all CI green.
>
> I'm ready to start contributing from day one."

---

## Quick Reference -- File Paths

| Component | File |
|-----------|------|
| Handoff Service | `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py` |
| Claude Orchestrator | `ghl_real_estate_ai/services/claude_orchestrator.py` |
| Agent Mesh Coordinator | `ghl_real_estate_ai/services/agent_mesh_coordinator.py` |
| Performance Tracker | `ghl_real_estate_ai/services/jorge/performance_tracker.py` |
| Alerting Service | `ghl_real_estate_ai/services/jorge/alerting_service.py` |
| Bot Metrics Collector | `ghl_real_estate_ai/services/jorge/bot_metrics_collector.py` |
| Lead Bot | `ghl_real_estate_ai/agents/lead_bot.py` (class at line 631) |
| Buyer Bot | `ghl_real_estate_ai/agents/jorge_buyer_bot.py` (class at line 183) |
| Seller Bot | `ghl_real_estate_ai/agents/jorge_seller_bot.py` (class at line 264) |
| Industry Config | `ghl_real_estate_ai/config/industry_config.py` |
| Multi-Tenant Models | `ghl_real_estate_ai/compliance_platform/multitenancy/models.py` |
| OpenTelemetry | `ghl_real_estate_ai/services/jorge/telemetry.py` |
| Agent Cost Tracker | `ghl_real_estate_ai/services/agent_cost_tracker.py` |
| RAG Decision Tracer | `advanced_rag_system/src/agents/decision_tracer.py` |

---

## Demo Talking Points (If He Wants to See Code)

If he asks to see code during the call, show these in order:
1. **`JorgeHandoffService.THRESHOLDS`** -- per-route confidence thresholds (5 lines, immediately clear)
2. **`evaluate_handoff()`** -- the full decision pipeline: signal extraction, score blending, learned adjustment, circular check
3. **`PerformanceTracker.SLA_CONFIG`** -- concrete P50/P95/P99 targets per bot
4. **`IndustryConfig` YAML** -- show how swapping one file changes the entire bot personality and intent patterns
5. **Test count** -- `pytest --co -q | tail -1` showing ~5,000 tests collected (7,800+ across portfolio)
6. **AgentForge ReAct Agent** -- `agentforge/react_agent.py` -- working Reason+Act loop with tool integration
7. **Agent Memory** -- `agentforge/agent_memory.py` -- TTL-based memory store with LRU eviction and keyword search
8. **Multi-Agent Mesh** -- `agentforge/multi_agent.py` -- agent registration, messaging, consensus voting, handoff protocol
