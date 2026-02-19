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

### MCP Servers
| Server | Source | Purpose |
|--------|--------|---------|
| memory | `.mcp.json` | Knowledge graph persistence |
| ghl | `.mcp.json` | GoHighLevel CRM via `${GHL_API_KEY}` |
| gumroad | `.mcp.json` | Gumroad product/sale data (read-only) |
| upwork | `.mcp.json` | Upwork job/proposal data |
| notebooklm | `.mcp.json` (Python) | NotebookLM integration |
| obsidian | `.mcp.json` (Python) | Obsidian vault integration |
| postgres | plugin | Direct DB queries via `${DATABASE_URL}` |
| redis | plugin | Cache inspection via `${REDIS_URL}` |
| stripe | plugin | Billing management via `${STRIPE_SECRET_KEY}` |
| playwright | plugin | E2E browser testing |

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

## Bot Public APIs (Jorge Bot — Feb 2026, 205 passing tests)

All three bots have unified public API entry points. Tone: friendly/consultative.

### Seller Bot
- **Class**: `JorgeSellerBot` at `agents/jorge_seller_bot.py:146`
- **Entry point**: `process_seller_message(contact_id, message, conversation_history)` — returns response, frs_score, pcs_score, handoff_signals
- **Enhanced**: `process_seller_with_enhancements(lead_data)` — full qualification with GHL field updates
- **Objection handling**: `handle_objection(state)` — graduated objection responses
- **Config**: `JorgeSellerConfig` at `ghl_utils/jorge_config.py:21` — questions, thresholds, field mappings, mode switching (simple/full)

### Buyer Bot
- **Class**: `JorgeBuyerBot` at `agents/jorge_buyer_bot.py:114`
- **Entry point**: `process_buyer_conversation(contact_id, message, conversation_history)` — returns response, financial_readiness, handoff_signals
- **Property matching**: `qualify_property_needs(state)` — budget parsing, preference extraction
- **Objection handling**: `handle_objections(state)` — buyer-specific objection responses
- **Config**: `BuyerBotConfig` at `config/jorge_config_loader.py:319` — features, workflow, affordability, scoring

### Lead Bot
- **Class**: `LeadBotWorkflow` at `agents/lead_bot.py:125`
- **Entry point**: `process_lead_conversation(contact_id, message, conversation_history)` — returns response, temperature, handoff_signals
- **Enhanced**: `process_enhanced_lead_sequence(lead_data)` — multi-day follow-up sequences
- **Config**: `LeadBotConfig` at `agents/lead_bot.py:110` and `config/jorge_config_loader.py:254` — features, scoring weights, sequence timing
- **Predictive variant**: `PredictiveLeadBot` at `agents/predictive_lead_bot.py:283` — behavioral analytics, personality adaptation, temperature prediction

### CalendarBookingService
- **File**: `services/jorge/calendar_booking_service.py:23`
- **Key methods**:
  - `offer_appointment_slots(contact_id)` — fetches GHL free slots, formats options for SMS
  - `book_appointment(contact_id, slot_index)` — creates appointment in GHL calendar
- **Config env vars**: `JORGE_CALENDAR_ID`, `JORGE_USER_ID`, `APPOINTMENT_TIMEZONE`, `APPOINTMENT_DEFAULT_DURATION`

### ResponsePostProcessor (Pipeline)
- **File**: `services/jorge/response_pipeline/pipeline.py`
- **Factory**: `create_default_pipeline()` at `services/jorge/response_pipeline/factory.py`
- **5 default stages** (in order):
  1. `LanguageMirrorProcessor` — detects language via `LanguageDetectionService`, sets `context.detected_language`
  2. `TCPAOptOutProcessor` — detects opt-out phrases, short-circuits with ack, adds `TCPA-Opt-Out` + `AI-Off` tags
  3. `ComplianceCheckProcessor` — FHA/RESPA via `ComplianceMiddleware.enforce()`, replaces with safe fallback if BLOCKED
  4. `AIDisclosureProcessor` — SB 243 `[AI-assisted message]` footer (language-aware)
  5. `SMSTruncationProcessor` — 320-char SMS limit, truncates at sentence boundaries
- **Optional stage** (not in default pipeline): `ConversationRepairProcessor` — breakdown detection, graduated repair ladder

### HandoffService
- **File**: `services/jorge/jorge_handoff_service.py:106`
- **Key methods**:
  - `evaluate_handoff()` — confidence-based routing with circular prevention
  - `retrieve_handoff_context(contact_id)` — get preserved context for target bot
  - `get_analytics_summary()` — handoff metrics and pattern data
  - `load_from_database(since_minutes)` — hydrate state from DB
  - `seed_historical_data(records)` / `export_seed_data()` — data migration

### Config Classes
| Class | File | Purpose |
|-------|------|---------|
| `JorgeSellerConfig` | `ghl_utils/jorge_config.py:21` | Seller questions, thresholds, GHL field mapping |
| `BuyerBotConfig` | `config/jorge_config_loader.py:319` | Buyer features, workflow, affordability, scoring |
| `LeadBotConfig` | `config/jorge_config_loader.py:254` | Lead features, scoring weights, sequence timing |
| `SellerBotConfig` | `config/jorge_config_loader.py:373` | Seller features, workflow, scoring |
| `JorgeEnvironmentSettings` | `ghl_utils/jorge_config.py:505` | All Jorge env var parsing |
| `JorgeBotsConfig` | `config/jorge_config_loader.py:409` | Unified bot config loader (YAML-backed) |
| `JorgeRanchoConfig` | `ghl_utils/jorge_rancho_config.py:184` | Market-specific configuration |

### Environment Variables (Jorge-specific)
**Core bot flags**: `JORGE_SELLER_MODE`, `JORGE_BUYER_MODE`, `JORGE_LEAD_MODE`, `JORGE_SIMPLE_MODE`, `FRIENDLY_APPROACH`
**Workflows**: `HOT_SELLER_WORKFLOW_ID`, `WARM_SELLER_WORKFLOW_ID`, `HOT_BUYER_WORKFLOW_ID`, `WARM_BUYER_WORKFLOW_ID`, `NOTIFY_AGENT_WORKFLOW_ID`, `MANUAL_SCHEDULING_WORKFLOW_ID`
**Calendar**: `JORGE_CALENDAR_ID`, `JORGE_USER_ID`, `APPOINTMENT_*` (timezone, duration, buffer, max days)
**Custom fields (seller)**: `CUSTOM_FIELD_SELLER_TEMPERATURE`, `CUSTOM_FIELD_SELLER_MOTIVATION`, `CUSTOM_FIELD_TIMELINE_URGENCY`, `CUSTOM_FIELD_PROPERTY_CONDITION`, `CUSTOM_FIELD_PRICE_EXPECTATION`, `CUSTOM_FIELD_PCS_SCORE`, `CUSTOM_FIELD_SELLER_LIENS`, `CUSTOM_FIELD_SELLER_REPAIRS`, `CUSTOM_FIELD_SELLER_LISTING_HISTORY`, `CUSTOM_FIELD_SELLER_DECISION_MAKER`
**Custom fields (buyer)**: `CUSTOM_FIELD_BUYER_TEMPERATURE`, `CUSTOM_FIELD_PRE_APPROVAL_STATUS`, `CUSTOM_FIELD_PROPERTY_PREFERENCES`, `CUSTOM_FIELD_BUDGET`
**Custom fields (lead)**: `CUSTOM_FIELD_LEAD_SCORE`, `CUSTOM_FIELD_LOCATION`, `CUSTOM_FIELD_TIMELINE`
**Message**: `MAX_SMS_LENGTH` (320), `USE_WARM_LANGUAGE`, `NO_HYPHENS`
Full reference: [`agents/DEPLOYMENT_CHECKLIST.md`](ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md)

### GHL Tags
| Tag | Applied By | Trigger |
|-----|-----------|---------|
| `Needs Qualifying` | Manual/workflow | Activates lead/seller bot |
| `Buyer-Lead` | Manual/workflow | Activates buyer bot |
| `AI-Off` | TCPA opt-out | Deactivates all bots |
| `Stop-Bot` | Manual | Deactivates all bots |
| `TCPA-Opt-Out` | Pipeline | User sent STOP/unsubscribe |
| `Compliance-Alert` | Pipeline | FHA/RESPA violation blocked |
| `Human-Escalation-Needed` | Conversation repair | Automated strategies exhausted |
| `Qualified` | Bot completion | Qualification flow complete |
| `Seller-Qualified` | Seller bot | Seller qualification complete |
| `Hot-Seller` / `Warm-Seller` / `Cold-Seller` | Seller bot | Temperature classification |
| `Hot-Lead` / `Warm-Lead` / `Cold-Lead` | Lead bot | Temperature classification |

### Intent Decoders (GHL-Enhanced)
| Decoder | Standard Method | GHL Method |
|---------|----------------|------------|
| `LeadIntentDecoder` | `analyze_lead()` | `analyze_lead_with_ghl()` — tag boosts, lead age, engagement recency |
| `BuyerIntentDecoder` | `analyze_buyer()` | `analyze_buyer_with_ghl()` — pre-approval, budget, urgency from GHL |

### Handoff Safeguards
- **Circular prevention**: Same source->target blocked within 30min window
- **Rate limiting**: 3 handoffs/hr, 10/day per contact
- **Conflict resolution**: Contact-level locking prevents concurrent handoffs
- **Pattern learning**: Dynamic threshold adjustment from outcome history (min 10 data points)
- **Performance routing**: Auto-defer handoffs when target P95 > 120% SLA or error rate > 10%

### Temperature Tag Publishing
| Lead Score | Temperature Tag | Actions |
|------------|-----------------|---------|
| >= 80 | **Hot-Lead** | Priority workflow trigger, agent notification |
| 40-79 | **Warm-Lead** | Nurture sequence, follow-up reminder |
| < 40 | **Cold-Lead** | Educational content, periodic check-in |

### Lead Bot Handoff Integration
Cross-bot handoff via [`JorgeHandoffService.evaluate_handoff()`](ghl_real_estate_ai/services/jorge/jorge_handoff_service.py):

| Direction | Confidence Threshold | Trigger Phrases |
|-----------|---------------------|-----------------|
| Lead -> Buyer | 0.7 | "I want to buy", "budget $", "pre-approval" |
| Lead -> Seller | 0.7 | "Sell my house", "home worth", "CMA" |

### Deployment
See [`agents/DEPLOYMENT_CHECKLIST.md`](ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md) for full deployment guide, env var reference, smoke tests, and monitoring setup.

## API Migration: Unified Intent Analysis

**⚠️ Old API removed 2026-03-15.** Use `evaluate_handoff_from_profile()` + `analyze_lead()`.
Full details: [`.claude/reference/api-migration-intent.md`](.claude/reference/api-migration-intent.md)

## FRS/PCS Weight Calibration

Weights configurable in `ghl_real_estate_ai/config/jorge_bots.yaml`, hot-reloadable without restart.
Full details: [`.claude/reference/frs-pcs-config.md`](.claude/reference/frs-pcs-config.md)

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

**Version**: 8.5 | **Last Updated**: February 19, 2026
