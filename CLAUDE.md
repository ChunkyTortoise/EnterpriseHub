# EnterpriseHub: Real Estate AI & BI Platform

**Purpose**: This document provides AI agents (Claude, Gemini, Perplexity) with the technical context needed to understand and work with the EnterpriseHub codebase.

**Domain**: Rancho Cucamonga real estate market with AI-powered lead qualification, chatbot orchestration, and BI dashboards.

**References**:
- `.claude/reference/domain-context.md` (market, terminology, bots)
- `.claude/reference/quality-standards.md` (perf targets, testing, KPIs)
- [`AGENTS.md`](AGENTS.md) (human agent personas and workflows)

---

## Architecture

**Stack**: FastAPI (async) | Streamlit BI | PostgreSQL + Alembic | Redis cache (L1/L2/L3) | Claude + Gemini + Perplexity AI | GoHighLevel CRM | Stripe | Docker Compose

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Jorge Bots    │    │  BI Dashboard    │    │  GHL Integration│
│ (Lead/Buyer/    │◄──►│  (Streamlit)     │◄──►│  (CRM Sync)     │
│  Seller)        │    │                  │    │                 │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         └──────────────────────┼───────────────────────┘
                    ┌───────────▼──────────┐
                    │    FastAPI Core      │
                    │  (Orchestration)     │
                    └───────────┬──────────┘
                    ┌───────────▼──────────┐
                    │   PostgreSQL + Redis │
                    └──────────────────────┘
```

## Code Organization
```
advanced_rag_system/src/       # RAG: core/, embeddings/, vector_store/
ghl_real_estate_ai/            # Main app
├── agents/                    # Bot personalities and behaviors
├── api/                       # FastAPI routes and middleware
├── models/                    # SQLAlchemy models, Pydantic schemas
├── services/                  # Business logic, integrations
├── utils/                     # Shared utilities
└── streamlit_demo/            # BI dashboard components
```

## Conventions
- **Files/Functions**: `snake_case` | **Classes**: `PascalCase` | **Constants**: `SCREAMING_SNAKE_CASE`
- **Env vars**: `PROJECT_FEATURE_NAME` | **DB tables**: `plural_snake_case`
- **Errors**: Explicit exception types, structured JSON responses (`error`, `message`, `field`, `code`)

## Agent & MCP Landscape

### Claude Code Agents (22)
All agents are **domain-agnostic** -- they adapt to this project's domain via CLAUDE.md and reference files.

| Agent | Purpose |
|-------|---------|
| architecture-sentinel | Deep architectural analysis and design guidance |
| security-auditor | Vulnerability research and security compliance |
| performance-optimizer | Performance profiling and scalability tuning |
| integration-test-workflow | Multi-agent coordination and integration testing |
| compliance-risk | Regulatory compliance monitoring and risk assessment |
| intent-decoder | Multi-modal conversation intelligence and intent analysis |
| handoff-orchestrator | Agent-to-agent transitions and context preservation |
| conversation-design | Conversational AI architecture and dialogue quality |
| database-migration | Schema design, migrations, and data infrastructure |
| ml-pipeline | ML model quality, training pipelines, and optimization |
| predictive-analytics | Forecasting, conversion optimization, and trend analysis |
| rag-pipeline-optimizer | RAG systems engineering and information retrieval |
| api-consistency | REST API design, standardization, and governance |
| devops-infrastructure | CI/CD pipelines, containers, and deployment automation |
| cost-token-optimization | AI cost engineering and token efficiency |
| dashboard-design | Streamlit BI dashboard architecture and visualization |
| kpi-definition | Business intelligence KPI frameworks and metrics |
| feature-enhancement-guide | Incremental feature development and backward compatibility |
| repo-scaffold | Greenfield repository creation following portfolio conventions |
| test-engineering | Test architecture, TDD, coverage gap analysis |
| portfolio-coordinator | Cross-repository strategy and convention consistency |
| quality-gate | CI/CD validation and release readiness checks |

### MCP Servers (5)
| Server | Package | Purpose |
|--------|---------|---------|
| memory | `@modelcontextprotocol/server-memory` | Knowledge graph persistence |
| postgres | `@modelcontextprotocol/server-postgres` | Direct DB queries via `${DATABASE_URL}` |
| redis | `@gongrzhe/server-redis-mcp` | Cache inspection via `${REDIS_URL}` |
| stripe | `@stripe/mcp` | Billing management via `${STRIPE_SECRET_KEY}` |
| playwright | `@playwright/mcp` | E2E browser testing |

## Critical Services
| Service | File | Key Behavior |
|---------|------|-------------|
| Claude Orchestration | `services/claude_orchestrator.py` | Multi-strategy parsing, L1/L2/L3 cache, <200ms overhead |
| Agent Mesh | `services/agent_mesh_coordinator.py` | Governance, routing, auto-scaling, audit trails |
| GHL Client | `services/enhanced_ghl_client.py` | 10 req/s rate limit, real-time CRM sync |
| BI Dashboards | `streamlit_demo/components/` | Monte Carlo, sentiment, churn detection |
| **Jorge Handoff Service** | `services/jorge/jorge_handoff_service.py` | Cross-bot handoff, 0.7 confidence threshold, circular prevention, rate limiting (3/hr, 10/day), pattern learning, analytics |
| **A/B Testing** | `services/jorge/ab_testing_service.py` | Experiment management, deterministic variant assignment, z-test significance |
| **Performance Tracker** | `services/jorge/performance_tracker.py` | P50/P95/P99 latency, SLA compliance, rolling window |
| **Alerting** | `services/jorge/alerting_service.py` | Configurable rules, cooldowns, 7 default alert rules |
| **Bot Metrics** | `services/jorge/bot_metrics_collector.py` | Per-bot stats, cache hits, alerting integration |

## Bot Public APIs (Jorge Bot — Feb 2026, 157 passing tests)

All three bots have unified public API entry points. Tone: friendly/consultative.

| Bot | Method | Key Returns |
|-----|--------|------------|
| Lead | `LeadBotWorkflow.process_lead_conversation()` | response, temperature, handoff_signals |
| Buyer | `JorgeBuyerBot.process_buyer_conversation()` | response, financial_readiness, handoff_signals |
| Seller | `JorgeSellerBot.process_seller_message()` | response, frs_score, pcs_score, handoff_signals |

### Supporting Services
| Service | File | Purpose |
|---------|------|---------|
| Calendar Booking | `services/jorge/calendar_booking_service.py` | Offer/book GHL calendar slots for HOT sellers |
| Response Pipeline | `services/jorge/response_pipeline/` | 5-stage post-processing (language mirror, TCPA, compliance, AI disclosure, SMS truncation) |
| Handoff Router | `services/jorge/handoff_router.py` | Performance-based routing, auto-deferral when target bot is slow |
| GHL Setup Validation | `ghl_utils/jorge_ghl_setup.py` | Validate all custom fields, workflows, calendar IDs (`python -m ghl_real_estate_ai.ghl_utils.jorge_ghl_setup`) |

### Intent Decoders (GHL-Enhanced)
| Decoder | Standard Method | GHL Method |
|---------|----------------|------------|
| `LeadIntentDecoder` | `analyze_lead()` | `analyze_lead_with_ghl()` — tag boosts, lead age, engagement recency |
| `BuyerIntentDecoder` | `analyze_buyer()` | `analyze_buyer_with_ghl()` — pre-approval, budget, urgency from GHL |

### Handoff Safeguards
- **Circular prevention**: Same source→target blocked within 30min window
- **Rate limiting**: 3 handoffs/hr, 10/day per contact
- **Conflict resolution**: Contact-level locking prevents concurrent handoffs
- **Pattern learning**: Dynamic threshold adjustment from outcome history (min 10 data points)
- **Performance routing**: Auto-defer handoffs when target P95 > 120% SLA or error rate > 10%

### Temperature Tag Publishing
| Lead Score | Temperature Tag | Actions |
|------------|-----------------|---------|
| ≥ 80 | **Hot-Lead** | Priority workflow trigger, agent notification |
| 40-79 | **Warm-Lead** | Nurture sequence, follow-up reminder |
| < 40 | **Cold-Lead** | Educational content, periodic check-in |

### Lead Bot Handoff Integration
Cross-bot handoff via [`JorgeHandoffService.evaluate_handoff()`](ghl_real_estate_ai/services/jorge/jorge_handoff_service.py):

| Direction | Confidence Threshold | Trigger Phrases |
|-----------|---------------------|-----------------|
| Lead → Buyer | 0.7 | "I want to buy", "budget $", "pre-approval" |
| Lead → Seller | 0.7 | "Sell my house", "home worth", "CMA" |

### Deployment
See [`agents/DEPLOYMENT_CHECKLIST.md`](ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md) for full deployment guide, env var reference, smoke tests, and monitoring setup.

## API Migration Guide: Unified Intent Analysis (Feb 2026)

**Breaking Change**: Intent analysis APIs consolidated to eliminate duplicate pattern matching.

### What Changed

**Before** (deprecated as of 2026-02-15):
```python
# Separate systems with duplicate work
intent_signals = handoff_service.extract_intent_signals(message)
decision = await handoff_service.evaluate_handoff(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=history,
    intent_signals=intent_signals  # dict with buyer_intent_score, seller_intent_score
)
```

**After** (unified approach):
```python
# Single intent analysis, no duplication
intent_profile = intent_decoder.analyze_lead(contact_id, history)
# intent_profile contains:
#   - frs: FinancialReadinessScore (0-100)
#   - pcs: PsychologicalCommitmentScore (0-100)
#   - buyer_intent_confidence: float (0.0-1.0)
#   - seller_intent_confidence: float (0.0-1.0)
#   - detected_intent_phrases: List[str]

decision = await handoff_service.evaluate_handoff_from_profile(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=history,
    intent_profile=intent_profile
)
```

### Backward Compatibility

**All existing code continues to work** — deprecated methods log warnings but remain functional.

**Deprecation Timeline**:
- **2026-02-15**: New unified API available, old API deprecated with warnings
- **2026-03-15**: Old API removed (1 month grace period)

### Migration Checklist

- [ ] Replace `extract_intent_signals()` calls with `analyze_lead()`
- [ ] Replace `evaluate_handoff()` with `evaluate_handoff_from_profile()`
- [ ] Update tests to use `LeadIntentProfile` instead of `IntentSignals` dict
- [ ] Verify handoff routing still works (confidence thresholds unchanged)

### Benefits of Migration

- **No duplicate pattern matching**: 50% faster intent analysis
- **Unified model**: FRS/PCS + handoff signals in one object
- **Richer context**: Handoffs now include qualification scores
- **Easier testing**: Single model to mock instead of separate dicts

---

## FRS/PCS Weight Calibration (Task #24 - Feb 2026)

**Status**: Config-driven weights now available via `jorge_bots.yaml`

### How It Works

All scoring weights (FRS and PCS) are now configurable and can be hot-reloaded without restart:

```python
from ghl_real_estate_ai.config.jorge_config_loader import get_config

config = get_config()

# FRS intent weights (motivation, timeline, condition, price)
frs_weights = config.lead_bot.scoring.intent_weights

# PCS weights (velocity, length, questions, objections, calls)
pcs_weights = config.lead_bot.scoring.pcs_weights
```

### Configuration Location

**File**: `/ghl_real_estate_ai/config/jorge_bots.yaml`

```yaml
lead_bot:
  scoring:
    intent_weights:
      motivation: 0.35  # 35% of FRS
      timeline: 0.30    # 30% of FRS
      condition: 0.20   # 20% of FRS
      price: 0.15       # 15% of FRS

    pcs_weights:
      response_velocity: 0.20
      message_length: 0.15
      question_depth: 0.20
      objection_handling: 0.25
      call_acceptance: 0.20

# Environment-specific calibration
environments:
  production:
    lead_bot:
      scoring:
        intent_weights:
          # Tuned from conversion data
          motivation: 0.38  # +3%
          timeline: 0.32    # +2%
          condition: 0.18   # -2%
          price: 0.12       # -3%
```

### Hot Reload (Zero Downtime)

```bash
# 1. Update weights in jorge_bots.yaml
vim ghl_real_estate_ai/config/jorge_bots.yaml

# 2. Reload config (no restart needed)
python -c "from ghl_real_estate_ai.config.jorge_config_loader import reload_config; reload_config()"

# 3. Verify new weights loaded
python -c "from ghl_real_estate_ai.config.jorge_config_loader import get_config; print(get_config().lead_bot.scoring.intent_weights)"
```

### Conversion Tracking

```python
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

decoder = LeadIntentDecoder()

# After lead converts or outcome is known
decoder.record_conversion_outcome(
    contact_id="abc123",
    frs_score=85.5,
    pcs_score=72.3,
    lead_type="buyer",
    outcome="converted",  # or "nurturing", "lost", "qualified"
    channel="sms",
    segment="hot"
)
```

### Calibration Process

**When to Calibrate**: After collecting 100+ conversion outcomes (configurable via `min_samples_for_calibration`)

**Steps**:
1. Query conversion outcomes from logs/database
2. Run logistic regression to find optimal weights
3. Update production environment weights in `jorge_bots.yaml`
4. Hot reload config
5. Monitor conversion rate improvement

**Weight Constraints**:
- All weights must sum to 1.0 (± 0.01 tolerance)
- Config loader validates on startup
- Invalid weights trigger error

### A/B Testing Weights

```yaml
# Test different weights in staging
environments:
  staging:
    lead_bot:
      scoring:
        intent_weights:
          motivation: 0.40  # Test higher motivation weight
          timeline: 0.28
          condition: 0.18
          price: 0.14
```

Monitor conversion rates in staging vs production, then promote winning weights.

---

## Security Essentials
- **PII**: Encrypted at rest (Fernet) | **API Keys**: Env vars only, never hardcoded
- **Auth**: JWT (1hr), 100 req/min rate limit | **Validation**: Pydantic on all inputs
- **Compliance**: DRE, Fair Housing, CCPA, CAN-SPAM

## Critical Files
| File | Purpose | Priority |
|------|---------|----------|
| `app.py` | FastAPI entry point | HIGH |
| `services/claude_orchestrator.py` | AI coordination | HIGH |
| `agents/jorge_*_bot.py` | Bot implementations | HIGH |
| `services/enhanced_ghl_client.py` | CRM integration | MEDIUM |
| `models/` | Data models | MEDIUM |
| `streamlit_demo/` | BI dashboard | MEDIUM |
| `.env` | Environment secrets | CRITICAL |

---

## Task Tracking
Uses **Beads** (`bd`) for task tracking. `bd ready` for available work, `bd close` when done, `bd sync` + `git push` before ending sessions. See `bd prime` for full command reference.

**Version**: 8.3 | **Last Updated**: February 14, 2026
