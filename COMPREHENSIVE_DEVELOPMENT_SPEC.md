# EnterpriseHub: Phase 2 — Production Scaling & Market Dominance (2026)
## Comprehensive Development Specification — Parallel Agent Team Execution

**Date:** February 20, 2026
**Status:** DRAFT — Parallel Execution Model (Post-Audit)
**Target:** 100% Production Readiness & $50K+ Monthly Recurring Revenue (MRR)
**Execution Model:** 1 Orchestrator + 6 Specialist Agents running simultaneously
**Timeline:** 6 weeks (vs. 12 sequential) at 2× effective throughput

---

## 1. Executive Summary

EnterpriseHub Phase 1 delivered a functional multi-agent real estate lead qualification system with 8,340+ automated tests and 89% cost reduction. Phase 1 remains a "developer-centric" prototype with 766 TODOs, 82 mock data placeholders, and outdated infrastructure (Python 3.10).

**Phase 2 changes that:**

| Objective | Owner Track | Target |
|-----------|------------|--------|
| Modernize infrastructure (Python 3.12, Pydantic v2, CI) | `infra-agent` | Week 1 |
| Replace all 82 mock data items with production DB/API logic | All tracks | Week 1–4 |
| Complete service catalog S17–S24 | `advanced-services-agent` | Week 4–5 |
| Polished showcase + "Deploy in 5 Minutes" | `showcase-agent` | Week 5–6 |
| 95%+ test coverage, DoD checklist green | All tracks + orchestrator | Week 6 |

**Why parallel?** The 82 ROADMAP items span 26 independent files across orthogonal work tracks (billing, prediction, bot management, SMS compliance, services, showcase). These tracks share no runtime dependencies and can be executed simultaneously by specialized agents, compressing the calendar from 12 → 6 weeks.

---

## 2. Parallel Team Architecture

### 2.1 Team: `enterprise-hub-phase2`

```
[Orchestrator — Claude Code]
         │
         ├── [infra-agent]              subagent_type: devops-infrastructure
         │     Python 3.12 · CI/CD · Pydantic v2 · Ruff
         │     UNBLOCKS: all other tracks
         │
         ├── [billing-predict-agent]    subagent_type: database-migration
         │     ROADMAP-001–015 (billing, prediction, revenue analytics)
         │
         ├── [bot-journey-agent]        subagent_type: handoff-orchestrator-enhanced
         │     ROADMAP-016–035 (bot management, agent lifecycle, customer journey)
         │
         ├── [sms-compliance-agent]     subagent_type: compliance-risk-enhanced
         │     ROADMAP-036–047 (SMS compliance, security events, golden leads)
         │
         ├── [services-agent]           subagent_type: integration-test-workflow
         │     ROADMAP-048–073 (swarm, offline sync, mobile, voice AI, Streamlit)
         │
         ├── [advanced-services-agent]  subagent_type: ml-pipeline
         │     ROADMAP-074–082 + S17–S24 (ML models, LLMOps, strategy dashboard)
         │
         └── [showcase-agent]           subagent_type: dashboard-design-specialist
               Interactive explorer · setup.sh · README ROI tables
```

**Coordination protocol:**
- Orchestrator creates all tasks, assigns owners, monitors via `TaskList`
- Agents send `SendMessage` to orchestrator on blocker or track completion
- Orchestrator runs quality gates at end of Weeks 2, 4, 6 before marking milestones
- `infra-agent` sends explicit "infra-complete" message before showcase work begins

---

## 3. Agent Track Specifications

### Track 1 — `infra-agent`
**subagent_type**: `devops-infrastructure`
**Estimated effort**: 20h
**Dependency**: None — start immediately
**Unblocks**: All other tracks depend on the shared infrastructure baseline

**Files in scope:**
- `.github/workflows/ci.yml`
- `pyproject.toml` (root + `ghl_real_estate_ai/`, `advanced_rag_system/`, `insight_engine/`, `rag-as-a-service/`)
- All `Dockerfile`s in the monorepo
- `requirements.txt` and `requirements-dev.txt` across sub-projects

**Tasks:**

| Task | Description |
|------|-------------|
| **[infra-001]** Python 3.12 CI matrix | Update `ci.yml` `python-version` matrix from `["3.10", "3.11"]` to `["3.12"]`. Update `pyproject.toml` `requires-python` to `>=3.12`. Update `Dockerfile` `FROM python:3.11-slim` → `python:3.12-slim`. |
| **[infra-002]** Pydantic v2 migration | Remove all `from pydantic.v1 import ...` and `class Config:` (v1 compat shims). Replace with `model_config = ConfigDict(...)`. Run full test suite to confirm zero regressions. |
| **[infra-003]** Dependency audit | Pin all `requirements.txt` entries to latest stable. Remove unused packages (`pip-autoremove`). Run `ruff check .` — zero errors required. |
| **[infra-004]** Verify 8,340 tests on 3.12 | Run `pytest --tb=short` against the 3.12 matrix. Log any Python version–specific failures and fix. |

**Definition of Done:** CI pipeline shows green on Python 3.12 across all sub-projects; `ruff check .` passes; no Pydantic v1 compat imports remain.

---

### Track 2 — `billing-predict-agent`
**subagent_type**: `database-migration`
**Estimated effort**: 53h
**Dependency**: `infra-agent` (Python version must be stable before DB migrations)

**Files in scope:**
- `api/routes/billing.py`
- `api/routes/prediction.py`

**Tasks (ROADMAP-001–015 + ROADMAP-006–007):**

| ROADMAP ID | Task | Blocked By |
|-----------|------|-----------|
| ROADMAP-008 | Subscription DB lookup — replace Stripe placeholder with actual `SELECT` on `subscriptions` table using `customer_id` | — |
| ROADMAP-009 | Payment method listing — DB join to retrieve stored payment methods; cancellation endpoint hits Stripe `DELETE` + updates local `subscriptions.status` | ROADMAP-008 |
| ROADMAP-010 | DB validation before Stripe cancel — check `subscriptions.status != 'cancelled'` before calling Stripe to prevent double-cancel errors | ROADMAP-008 |
| ROADMAP-011 | Usage records table insert — on each API call, `INSERT INTO usage_records (location_id, endpoint, tokens_used, timestamp)` | — |
| ROADMAP-012 | Location ID from customer — resolve `customer_id → location_id` via `customers` table join | ROADMAP-008 |
| ROADMAP-013 | Revenue analytics from real data — query `usage_records + subscriptions` for MRR, churn, and ARPU calculations | ROADMAP-008, ROADMAP-011 |
| ROADMAP-001 | Prediction engine — wire interaction history (`SELECT` from `lead_interactions` for last 90 days) | — |
| ROADMAP-002 | Prediction engine — wire deal data (`SELECT` from `deals` with price, days_on_market, outcome) | — |
| ROADMAP-003 | Prediction engine — wire target markets (replace hardcoded `["NYC","LA","Chicago"]` with `user_settings` or `business_profile` table query) | — |
| ROADMAP-004 | Prediction engine — wire team data (replace hardcoded `team_size=8` with `team_management` or `user_settings` table query) | — |
| ROADMAP-005 | Prediction engine — wire expansion plans (replace hardcoded territories with `territory_planning` or `user_settings` table query) | — |
| ROADMAP-006 | Real-time market monitoring — replace placeholder sleep timer with market data feed integration + change detection algorithm (P3) | ROADMAP-001, ROADMAP-002 |
| ROADMAP-007 | Continuous prediction monitoring — background job for market/client/deal/business monitoring (P3) | ROADMAP-001, ROADMAP-002, ROADMAP-006 |
| ROADMAP-014 | Analytics service integration — send billing events (subscription_created, payment_processed, etc.) to Segment/Mixpanel or custom analytics pipeline (P3) | — |
| ROADMAP-015 | Webhook event DB storage — persist all inbound Stripe webhook events to `billing_events` table for audit and replay | — |

**Definition of Done:** All 17 ROADMAP items replaced with real DB/API logic; zero mocked return values in `billing.py` and `prediction.py`; integration tests cover each route with test DB fixtures.

---

### Track 3 — `bot-journey-agent`
**subagent_type**: `handoff-orchestrator-enhanced`
**Estimated effort**: 82h
**Dependency**: None — start immediately

**Files in scope:**
- `api/routes/bot_management.py`
- `api/routes/agent_ecosystem.py`
- `api/routes/customer_journey.py`
- `api/routes/property_intelligence.py`
- `services/jorge/jorge_handoff_service.py`

**Tasks (ROADMAP-016–035):**

| ROADMAP ID | Task | Blocked By |
|-----------|------|-----------|
| ROADMAP-016 | Question progress tracking — persist current question index and answers to `bot_sessions` table | — |
| ROADMAP-017 | Stall detection algorithm — flag sessions where `last_message_at` > configured threshold (default 24h) with no response | — |
| ROADMAP-018 | Effectiveness score — calculate per-session score from question completion rate + response latency; store in `bot_sessions.effectiveness_score` | ROADMAP-017 |
| ROADMAP-019 | Handoff logic via `JorgeHandoffService` — wire `bot_management.py` handoff endpoint to call `evaluate_handoff()` and persist result | — |
| ROADMAP-020 | Coordination event schema — define `CoordinationEvent` Pydantic model; emit events on handoff, stall, and completion | ROADMAP-019 |
| ROADMAP-021 | Agent status update interface — `AgentController.update_status(agent_id, new_status)` backed by `agent_registry` table; publishes status-change event | — |
| ROADMAP-022 | Handoff coordination engine — integrate `agent_ecosystem.py` handoff endpoint with `AgentMeshCoordinator`; implement context preservation, rollback capability, and timeout handling | — |
| ROADMAP-023 | Agent pause lifecycle — call `agent.pause()` to stop processing new requests while finishing in-flight work; state: `PAUSED` | ROADMAP-021 |
| ROADMAP-024 | Agent resume lifecycle — call `agent.resume()` with state verification (must be in `PAUSED` before resuming) | ROADMAP-023 |
| ROADMAP-025 | Agent restart with graceful shutdown — drain in-flight requests → stop → start → health check; 30s graceful / 5s forceful timeout; notify ops on failed restart | ROADMAP-023, ROADMAP-024 |
| ROADMAP-026 | Customer journey create — `POST /journeys` inserts into `customer_journeys` table with step definitions | — |
| ROADMAP-027 | Customer journey read — `GET /journeys/{id}` returns journey + all steps with completion status | — |
| ROADMAP-028 | Customer journey update — `PATCH /journeys/{id}` allows step reordering and metadata updates | — |
| ROADMAP-029 | Customer journey delete — `DELETE /journeys/{id}` soft-deletes (sets `deleted_at`) to preserve audit trail | — |
| ROADMAP-030 | Step completion — `POST /journeys/{id}/steps/{step_id}/complete` marks step done, evaluates next step trigger | — |
| ROADMAP-031 | Property intelligence agent integration — initialize agent, fetch MLS data, run AI analysis, cache results (replacing mock analysis generation) | — |
| ROADMAP-032 | Property analysis DB/cache retrieval — Redis L1 cache (1hr TTL) → DB query → async analysis job fallback; replace per-request mock generation | ROADMAP-031 |
| ROADMAP-033 | Property analysis DB update — validate access, update `property_analyses` table, invalidate cache, store version history | ROADMAP-032 |
| ROADMAP-034 | Property analysis deletion with cleanup — soft-delete (`deleted_at`), remove from Redis, archive history, cascade to comparisons table | ROADMAP-032, ROADMAP-033 |
| ROADMAP-035 | Property comparison logic — fetch multiple analyses, calculate weighted scores, rank by criteria, generate AI recommendations (replacing mock comparison data) | ROADMAP-032 |

**Definition of Done:** All 20 ROADMAP items implemented; handoff logic routes through `JorgeHandoffService`; customer journey CRUD passes integration tests; cache hit rate > 80% on property lookups.

---

### Track 4 — `sms-compliance-agent`
**subagent_type**: `compliance-risk-enhanced`
**Estimated effort**: 60h
**Dependency**: None — start immediately

**Files in scope:**
- `api/routes/sms_compliance.py`
- `api/routes/compliance.py`
- `api/routes/claude_concierge_integration.py`
- `api/routes/golden_lead_detection.py`
- `api/routes/market_intelligence_v2.py`

**Tasks (ROADMAP-036–047):**

| ROADMAP ID | Task | Blocked By |
|-----------|------|-----------|
| ROADMAP-036 | SMS compliance reporting dashboard — replace all-zeros placeholder with real queries: opt-out count, frequency violations, score, recommendations from `sms_opt_outs` + `sms_message_log` | — |
| ROADMAP-037 | SMS opt-out count query — `SELECT COUNT(*) FROM sms_opt_outs WHERE location_id = ? AND date >= ?` | — |
| ROADMAP-038 | SMS frequency violations query — group `sms_message_log` by `contact_id`, count messages per day, flag contacts exceeding daily limit | — |
| ROADMAP-039 | SMS compliance score calculation — formula: `100 - (violations * 10) - (opt_out_rate * 20)`, clamped 0–100 | ROADMAP-037, ROADMAP-038 |
| ROADMAP-040 | SMS compliance recommendations — rule engine: violations > 5 → "Reduce frequency"; opt_out_rate > 2% → "Review content" | ROADMAP-039 |
| ROADMAP-041 | Real-time compliance monitoring — replace 5-minute sleep placeholder with continuous scanner for DRE, Fair Housing, and TCPA violations; check configurable thresholds | — |
| ROADMAP-042 | Security event monitoring — implement anomaly detection: monitor access patterns, detect PII anomalies, track auth failures → persist to `security_events` | ROADMAP-041 |
| ROADMAP-043 | Privacy request processing — poll `privacy_requests` table; process deletions (30-day SLA) and exports (7-day SLA) per GDPR/CCPA | — |
| ROADMAP-044 | Audit trail updates — aggregate compliance events, archive records > 90 days, generate auditor reports | ROADMAP-041, ROADMAP-042, ROADMAP-043 |
| ROADMAP-045 | Suggestion dismissal with ML feedback — store dismissed suggestions with reason in `suggestion_feedback`; use as training signal for score thresholds | ROADMAP-040 |
| ROADMAP-046 | Golden lead filtering from DB — replace mock list with `SELECT ... WHERE lead_score >= 80 AND last_activity >= NOW() - INTERVAL '7 days'` with Redis pagination | — |
| ROADMAP-047 | AI-powered property recommendations via Claude — wire `market_intelligence_v2.py` to call Claude API with property + buyer persona context; stream results via SSE | — |

**Definition of Done:** All 12 ROADMAP items implemented; real-time compliance score endpoint returns sub-200ms; SSE stream tested with integration tests; golden lead filtering benchmarked with Redis pagination.

---

### Track 5 — `services-agent`
**subagent_type**: `integration-test-workflow`
**Estimated effort**: 120h
**Dependency**: None — start immediately

**Files in scope:**
- `agents/swarm_orchestrator.py`
- `services/offline_sync_service.py`
- `services/mobile_notification_service.py`
- `services/voice_ai_integration.py`
- `streamlit_demo/` (GA integration + UI components)

**Tasks (ROADMAP-048–073):**

| ROADMAP ID | Task | Blocked By |
|-----------|------|-----------|
| ROADMAP-048 | Swarm task execution engine — implement `execute_task(task_def)` to dispatch to worker pool | — |
| ROADMAP-049 | Parallel concurrency control — `asyncio.Semaphore(N)` with configurable `MAX_SWARM_CONCURRENCY` env var | ROADMAP-048 |
| ROADMAP-050 | Swarm tool registry — dict of registered tool callables; `register_tool(name, fn)` + `dispatch_tool(name, args)` | — |
| ROADMAP-051 | Swarm result aggregation — collect worker results into `SwarmResult` with per-task status and error capture | ROADMAP-048, ROADMAP-049 |
| ROADMAP-052 | Offline property ops queue — `SQLiteQueue` for create/update/delete operations when GHL is unreachable | — |
| ROADMAP-053 | Offline note ops queue — same pattern for agent notes with `note_id` + `contact_id` | — |
| ROADMAP-054 | Server update sync — on reconnect, drain queue and POST batch to GHL with idempotency keys | ROADMAP-052, ROADMAP-053 |
| ROADMAP-055 | Change tracking — `ETag`-based change detection per contact; only sync if server `ETag` differs | — |
| ROADMAP-056 | Checksum verification — SHA-256 checksum of sync payload; log mismatch to `sync_errors` | ROADMAP-054 |
| ROADMAP-057 | Conflict resolution — Last Write Wins with `updated_at` timestamp comparison; log all conflicts | ROADMAP-054 |
| ROADMAP-058 | FCM push notifications — `google.oauth2` + FCM v1 API for Android device tokens | — |
| ROADMAP-059 | APNS push notifications — `httpx` + APNS2 with JWT auth for iOS device tokens | — |
| ROADMAP-060 | Device token registry — `device_tokens` table with `platform`, `token`, `contact_id`, `active` columns | ROADMAP-058, ROADMAP-059 |
| ROADMAP-061 | Quiet hours enforcement — `DO NOT DISTURB` schedule per contact stored in `notification_preferences` | ROADMAP-058, ROADMAP-059 |
| ROADMAP-062 | Notification delivery receipts — callback endpoint for FCM/APNS delivery confirmations; persist to `notification_log` | ROADMAP-060 |
| ROADMAP-063 | Language detection for voice — integrate `langdetect` or Vapi language hint on call start | — |
| ROADMAP-064 | Interruption detection — parse Vapi webhook `speech_detected_while_speaking` events into `interruption_events` | — |
| ROADMAP-065 | Silence detection — flag call segments with > 8s silence from Vapi `silence_detected` events | — |
| ROADMAP-066 | Voice performance scoring — composite score from interruption rate, silence rate, and call outcome | ROADMAP-064, ROADMAP-065 |
| ROADMAP-067 | Voice analytics storage — persist per-call analytics to `voice_call_analytics` table | ROADMAP-066 |
| ROADMAP-068 | Voice AI summary — generate Claude-powered call summary from transcript; store with analytics | ROADMAP-067 |
| ROADMAP-069 | Google Analytics 4 integration — fire GA4 events on key Streamlit user actions via `gtag()` | — |
| ROADMAP-070 | Live handoff card — Streamlit component showing current active handoffs with status badges | — |
| ROADMAP-071 | Button primitives — reusable `action_button(label, icon, color)` Streamlit component | — |
| ROADMAP-072 | Badge primitives — reusable `status_badge(text, severity)` Streamlit component | — |
| ROADMAP-073 | Form submission tracking — emit GA4 `form_submit` event with field completion percentage on submit | ROADMAP-069 |

**Definition of Done:** All 26 ROADMAP items implemented; swarm handles 10 concurrent tasks without deadlock; offline sync round-trip tested with simulated GHL outage; FCM + APNS integration tested with mock device tokens.

---

### Track 6 — `advanced-services-agent`
**subagent_type**: `ml-pipeline`
**Estimated effort**: 95h
**Dependency**: None — start immediately

**Files in scope:**
- `services/white_label_mobile_service.py`
- `services/jorge/ab_auto_promote.py`
- `services/market_sentiment_radar.py`
- `services/revenue_attribution_system.py`
- `services/ai_negotiation_partner.py`
- `services/autonomous_followup_engine.py`
- `services/database_sharding.py`
- `services/win_probability_predictor.py`
- `services/performance_monitor.py`

**Tasks (ROADMAP-074–082 + Service Catalog S17–S24):**

| ID | Task | Blocked By |
|----|------|-----------|
| ROADMAP-074 | White label mobile app pipeline — build config-driven white-labeling: app name, color scheme, logo injected via `WhiteLabelConfig`; output Docker build args | — |
| ROADMAP-075 | A/B test auto-promotion — if `winner_variant` z-score > 2.0 for > 100 observations, auto-promote to 100% traffic and archive loser | — |
| ROADMAP-076 | Market sentiment radar — replace mock data with Perplexity API queries for local market news; parse sentiment from response | — |
| ROADMAP-077 | Revenue attribution tracking — trace each closed deal back to originating lead source via `UTM` params in `lead_sources` table | — |
| ROADMAP-078 | AI negotiation partner completion — implement `generate_counter_offer(offer, market_comps)` using Claude with chain-of-thought; return structured `NegotiationStrategy` | — |
| ROADMAP-079 | Autonomous follow-up ML enhancement — replace static schedule with ML-predicted optimal send time from `InteractionTimePredictor` model | — |
| ROADMAP-080 | Database sharding implementation — implement consistent hashing ring for `location_id`-based shard routing; `ShardRouter.get_shard(key)` | — |
| ROADMAP-081 | Win probability ML model — logistic regression on `deals` table features (price, days_on_market, lead_score, market_temp); `scikit-learn` pipeline with `joblib` serialization | — |
| ROADMAP-082 | Performance monitor alerting integration — wire `PerformanceMonitor.check_thresholds()` to `AlertingService.fire_alert()`; map P95 > 120% SLA → `SLA_BREACH` alert type | — |
| **S17** | LLMOps dashboard — Streamlit page showing model routing decisions (Gemini vs Claude), token spend by route, L1/L2/L3 cache hit rates; goal: 92%+ cost reduction | ROADMAP-082 |
| **S18** | API documentation portal — deploy Redoc on GitHub Pages; auto-generate from FastAPI `/openapi.json`; GitHub Actions publish step | — |
| **S21** | AI system audit — populate `AUDIT_MANIFEST.md` with: PII encryption verification (Fernet), bias detection results, GDPR/CCPA compliance log entries | — |
| **S24** | Strategy dashboard — Streamlit page for agencies: ROI vs baseline, lead conversion uplift (bot vs human), bot performance percentile ranking | ROADMAP-081 |

**Definition of Done:** All 13 items implemented; win probability model achieves AUC > 0.70 on holdout set; LLMOps dashboard shows live cache metrics; `AUDIT_MANIFEST.md` fully populated; API docs portal URL in root `README.md`.

---

### Track 7 — `showcase-agent`
**subagent_type**: `dashboard-design-specialist`
**Estimated effort**: 30h
**Dependency**: `infra-agent` complete (Docker config must be finalized before `setup.sh`)

**Files in scope:**
- `streamlit_demo/showcase_landing.py` (new component)
- `setup.sh` (new file)
- `README.md` in root + all 5 flagship repos

**Tasks:**

| Task | Description |
|------|-------------|
| **[showcase-001]** Interactive Architecture Explorer | Streamlit component with clickable system layer cards (Core, Clients, Data, AI). Each card expands to show live health check status, key metrics, and file paths. Use `st.expander` + custom CSS for layer depth visualization. |
| **[showcase-002]** `setup.sh` script | Shell script: (1) `docker compose up -d`, (2) wait for Postgres health check, (3) run Alembic migrations, (4) seed demo data via `python scripts/seed_demo.py`, (5) print "✅ EnterpriseHub running at http://localhost:8000". Test end-to-end in CI. |
| **[showcase-003]** ROI tables for flagship READMEs | Add `## ROI at a Glance` table to: `ghl_real_estate_ai/`, `advanced_rag_system/`, `insight_engine/`, `rag-as-a-service/`, and root `README.md`. Metrics: test count, latency P95, cost reduction %, time-to-qualify. |
| **[showcase-004]** "Deploy in 5 Minutes" section | Add step-by-step `setup.sh` walkthrough to root `README.md` with copy-paste commands. |

**Definition of Done:** `setup.sh` runs to completion in a clean Docker environment; interactive explorer renders without error; all 5 README ROI tables populated with real metrics from test suite.

---

## 4. Dependency Graph

```
infra-agent (Week 1)
    │
    └── [unblocks showcase-agent setup.sh]
    └── [recommended baseline for billing-predict-agent DB migrations]

ROADMAP-008 → ROADMAP-009, 010, 012, 013
ROADMAP-011 → ROADMAP-013
ROADMAP-013 → ROADMAP-014
ROADMAP-017 → ROADMAP-018
ROADMAP-019 → ROADMAP-020
ROADMAP-021–024 → ROADMAP-025
ROADMAP-031 → ROADMAP-032, 033, 035
ROADMAP-032, 033 → ROADMAP-034
ROADMAP-036, 037 → ROADMAP-038
ROADMAP-038 → ROADMAP-039, 040
ROADMAP-039 → ROADMAP-045
ROADMAP-040, 042 → ROADMAP-044
ROADMAP-048, 049 → ROADMAP-051
ROADMAP-052, 053 → ROADMAP-054
ROADMAP-054 → ROADMAP-056, 057
ROADMAP-058, 059 → ROADMAP-060, 062
ROADMAP-064, 065 → ROADMAP-066
ROADMAP-066 → ROADMAP-067 → ROADMAP-068
ROADMAP-081 → S24
ROADMAP-082 → S17
```

---

## 5. Revised Timeline

| Week | Active Tracks | Milestone |
|------|--------------|-----------|
| **1** | infra + bot-journey + sms-compliance + services (setup) | Python 3.12 CI green; P1 billing items (ROADMAP-008–012) done |
| **2** | All 6 tracks running | All P1 ROADMAP items complete; CI passing on Python 3.12 |
| **3** | billing-predict + bot-journey + sms + services | ROADMAP-001–047 ~75% complete |
| **4** | All remaining service tracks + advanced services | ROADMAP-001–082 100% complete |
| **5** | showcase + advanced services + quality gate | S17–S24 done; `setup.sh` working end-to-end |
| **6** | Final integration, coverage push to 95%, DoD checklist | **SHIP** |

**Timeline math:** 460h total ÷ 6 agents ≈ 77h/agent ÷ 40h/agent-week = ~2 agent-weeks with 2-week buffer for integration → **6 weeks total** (vs. 12 sequential).

---

## 6. Team Bootstrap Commands

Run once at the start of Phase 2 to initialize the team and all tasks:

```python
# ── Step 1: Create the team ────────────────────────────────────────────────
TeamCreate(
    team_name="enterprise-hub-phase2",
    description="Phase 2 parallel execution — 82 ROADMAP items + S17-S24 + showcase"
)

# ── Step 2: Create infrastructure tasks ───────────────────────────────────
t_infra_001 = TaskCreate(
    subject="[infra-001] Python 3.12 CI matrix upgrade",
    description="Update ci.yml matrix, pyproject.toml requires-python, and all Dockerfiles to Python 3.12",
    activeForm="Upgrading CI matrix to Python 3.12"
)
t_infra_002 = TaskCreate(
    subject="[infra-002] Pydantic v2 native migration",
    description="Remove all pydantic.v1 compat shims; replace class Config with ConfigDict",
    activeForm="Migrating Pydantic v1 shims to v2 native"
)
t_infra_003 = TaskCreate(
    subject="[infra-003] Dependency audit and ruff clean",
    description="Pin requirements.txt to latest stable; ruff check . must pass zero errors",
    activeForm="Auditing and updating dependencies"
)
t_infra_004 = TaskCreate(
    subject="[infra-004] Verify 8340 tests on Python 3.12",
    description="Run pytest --tb=short against 3.12 matrix; fix any version-specific failures",
    activeForm="Verifying test suite on Python 3.12"
)

# ── Step 3: Create billing/prediction tasks (ROADMAP-001–015) ──────────────
t_r008 = TaskCreate(
    subject="[ROADMAP-008] Subscription DB lookup",
    description="Replace Stripe placeholder in billing.py with SELECT on subscriptions table using customer_id",
    activeForm="Wiring subscription DB lookup"
)
t_r009 = TaskCreate(
    subject="[ROADMAP-009] Payment method + cancellation",
    description="DB join for payment methods; Stripe DELETE + subscriptions.status update on cancel",
    activeForm="Implementing payment method and cancellation"
)
TaskUpdate(taskId=t_r009.id, addBlockedBy=[t_r008.id])

t_r010 = TaskCreate(
    subject="[ROADMAP-010] DB validation before Stripe cancel",
    description="Check subscriptions.status != 'cancelled' before calling Stripe to prevent double-cancel",
    activeForm="Adding DB validation before Stripe cancel"
)
TaskUpdate(taskId=t_r010.id, addBlockedBy=[t_r008.id])

t_r011 = TaskCreate(
    subject="[ROADMAP-011] Usage records table insert",
    description="INSERT INTO usage_records on each API call with location_id, endpoint, tokens_used, timestamp",
    activeForm="Implementing usage records logging"
)
t_r012 = TaskCreate(
    subject="[ROADMAP-012] Location ID from customer",
    description="Resolve customer_id to location_id via customers table join",
    activeForm="Resolving location ID from customer"
)
TaskUpdate(taskId=t_r012.id, addBlockedBy=[t_r008.id])

t_r013 = TaskCreate(
    subject="[ROADMAP-013] Revenue analytics from real data",
    description="Query usage_records + subscriptions for MRR, churn, ARPU",
    activeForm="Wiring revenue analytics to real DB"
)
TaskUpdate(taskId=t_r013.id, addBlockedBy=[t_r008.id, t_r011.id])

# (Abbreviated — full task list covers all 82 ROADMAP items + S17-S24 + showcase)
# Continue pattern for ROADMAP-001–007, 014–015, 016–082, S17–S24, showcase-001–004

# ── Step 4: Spawn agents ───────────────────────────────────────────────────
Task(
    subagent_type="devops-infrastructure",
    team_name="enterprise-hub-phase2",
    name="infra-agent",
    prompt="You are the infra-agent for enterprise-hub-phase2. Claim and complete tasks [infra-001] through [infra-004]. Working directory: /Users/cave/Projects/EnterpriseHub_new. Send a message to orchestrator when complete."
)
Task(
    subagent_type="database-migration",
    team_name="enterprise-hub-phase2",
    name="billing-predict-agent",
    prompt="You are the billing-predict-agent. Claim and complete ROADMAP-001–015 tasks. Files: api/routes/billing.py, api/routes/prediction.py. Respect blockedBy dependencies. Working directory: /Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai."
)
Task(
    subagent_type="handoff-orchestrator-enhanced",
    team_name="enterprise-hub-phase2",
    name="bot-journey-agent",
    prompt="You are the bot-journey-agent. Claim and complete ROADMAP-016–035 tasks. Files: api/routes/bot_management.py, api/routes/agent_ecosystem.py, api/routes/customer_journey.py, services/jorge/jorge_handoff_service.py. Working directory: /Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai."
)
Task(
    subagent_type="compliance-risk-enhanced",
    team_name="enterprise-hub-phase2",
    name="sms-compliance-agent",
    prompt="You are the sms-compliance-agent. Claim and complete ROADMAP-036–047 tasks. Files: api/routes/sms_compliance.py, api/routes/compliance.py, api/routes/claude_concierge_integration.py, api/routes/golden_lead_detection.py, api/routes/market_intelligence_v2.py. Working directory: /Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai."
)
Task(
    subagent_type="integration-test-workflow",
    team_name="enterprise-hub-phase2",
    name="services-agent",
    prompt="You are the services-agent. Claim and complete ROADMAP-048–073 tasks. Files: agents/swarm_orchestrator.py, services/offline_sync_service.py, services/mobile_notification_service.py, services/voice_ai_integration.py, streamlit_demo/. Working directory: /Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai."
)
Task(
    subagent_type="ml-pipeline",
    team_name="enterprise-hub-phase2",
    name="advanced-services-agent",
    prompt="You are the advanced-services-agent. Claim and complete ROADMAP-074–082 and service catalog items S17–S24. Files: services/white_label_mobile_service.py, services/jorge/ab_auto_promote.py, services/market_sentiment_radar.py, services/revenue_attribution_system.py, services/ai_negotiation_partner.py, services/autonomous_followup_engine.py, services/database_sharding.py, services/win_probability_predictor.py, services/performance_monitor.py. Working directory: /Users/cave/Projects/EnterpriseHub_new/ghl_real_estate_ai."
)
Task(
    subagent_type="dashboard-design-specialist",
    team_name="enterprise-hub-phase2",
    name="showcase-agent",
    prompt="You are the showcase-agent. Wait for infra-agent completion message before starting setup.sh. Then claim and complete showcase-001 through showcase-004 tasks. Working directory: /Users/cave/Projects/EnterpriseHub_new."
)
```

---

## 7. Orchestrator Quality Gates

The orchestrator runs the following checks at the end of Weeks 2, 4, and 6:

### Week 2 Gate — Infrastructure + P1 Items
- [ ] `pytest --tb=short` green on Python 3.12 across all sub-projects
- [ ] `ruff check .` passes with zero errors
- [ ] ROADMAP-008–012 implemented (no mock returns in billing.py)
- [ ] Zero Pydantic v1 compat imports remain

### Week 4 Gate — Feature Complete
- [ ] All 82 ROADMAP items marked `completed` in TaskList
- [ ] Integration tests added for each ROADMAP item (minimum 1 test per item)
- [ ] Coverage report shows > 90% on modified files
- [ ] No new `TODO` comments introduced (grep for `# TODO` in changed files)

### Week 6 Gate — Ship Ready
- [ ] All DoD checklist items below are green
- [ ] `setup.sh` runs end-to-end in a clean Docker environment
- [ ] API docs portal URL committed to root `README.md`
- [ ] `AUDIT_MANIFEST.md` fully populated
- [ ] Win probability model AUC > 0.70 logged in test output

---

## 8. Definition of Done (DoD)

- [ ] Python 3.12 in CI/CD — all 8,340+ tests passing
- [ ] 100% of ROADMAP-001 to ROADMAP-082 implemented (zero mock returns)
- [ ] Service catalog S17, S18, S21, S24 delivered
- [ ] < 50 TODOs remaining (strictly backlog, none in P1/P2 files)
- [ ] `AUDIT_MANIFEST.md` fully populated (PII encryption, bias detection, GDPR/CCPA logs)
- [ ] 95%+ test coverage (verified via `coverage.xml`)
- [ ] `setup.sh` "Deploy in 5 Minutes" working and documented in root `README.md`
- [ ] Interactive Architecture Explorer live in Streamlit demo
- [ ] ROI tables in all 5 flagship repository READMEs
- [ ] API documentation portal live on GitHub Pages

---

## 9. ROADMAP Item Assignment Index

Quick-reference: which agent owns each ROADMAP item.

| Range | Agent | Track |
|-------|-------|-------|
| ROADMAP-001–007 | `billing-predict-agent` | Prediction engine DB wiring + market/prediction monitoring (006–007 are P3) |
| ROADMAP-008–015 | `billing-predict-agent` | Billing + revenue analytics |
| ROADMAP-016–035 | `bot-journey-agent` | Bot management + agent lifecycle + customer journey + property intelligence |
| ROADMAP-036–047 | `sms-compliance-agent` | SMS compliance + golden leads |
| ROADMAP-048–073 | `services-agent` | Swarm + offline + mobile + voice + Streamlit |
| ROADMAP-074–082 | `advanced-services-agent` | ML models + advanced services |
| S17, S18, S21, S24 | `advanced-services-agent` | Service catalog expansion |
| infra-001–004 | `infra-agent` | Infrastructure modernization |
| showcase-001–004 | `showcase-agent` | Interactive explorer + setup.sh + READMEs |


---

**Approved by:** Orchestrator (Claude Sonnet 4.6)
**Date:** February 20, 2026
**Execution model:** Claude Code `TeamCreate` + `TaskCreate` + `SendMessage` parallel coordination
