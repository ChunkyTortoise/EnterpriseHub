# Jorge Parallel Agent Team Execution Spec

Version: 1.0  
Date: 2026-02-09  
Owner: Engineering

## 1) Objective

Define an execution-ready multi-agent team structure that delivers remaining Jorge roadmap work in parallel, without breaking routing/compliance/booking behavior.

This spec assumes P0 is complete and focuses on P1 + P2 delivery throughput with strict regression gates.

## 2) Execution Model

- One coordinator agent controls backlog state, dependency resolution, and release gates.
- Specialist agents own isolated workstreams.
- All agents ship in small PR-sized increments with continuous integration checks.
- No agent merges without test evidence and observability checks.

## 3) Agent Team Topology

### A0. Coordinator Agent (Program Control)

Responsibilities:
- Own sprint board, dependency map, and daily plan.
- Resolve conflicts across parallel tracks.
- Enforce merge criteria and release gates.

Inputs:
- Task status from all agents.
- CI and staging signals.

Outputs:
- Daily execution digest.
- Go/No-Go decisions.

### A1. Tenant Provisioning Agent

Responsibilities:
- Tenant bootstrap automation and onboarding checklist flow.
- Tenant config validation and safety checks.

Primary files:
- `scripts/tenant_bootstrap.py`
- `ghl_real_estate_ai/services/tenant_service.py`
- `docs/tenant_onboarding/*`

### A2. Data Quality Agent

Responsibilities:
- Field completeness validator after seller turns.
- Numeric parser repair/retry for timeline/price/mortgage/repairs.

Primary files:
- `ghl_real_estate_ai/core/conversation_manager.py`
- `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`

### A3. Handoff Intelligence Agent

Responsibilities:
- Cross-bot handoff confidence tuning.
- Add handoff audit logs (reason, confidence, source tags, outcome).

Primary files:
- `ghl_real_estate_ai/api/routes/webhook.py`
- `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
- `ghl_real_estate_ai/agents/jorge_buyer_bot.py`

### A4. KPI Productization Agent

Responsibilities:
- Harden KPI export endpoints/jobs.
- Add freshness/error telemetry and tenant-level filtering.

Primary files:
- `ghl_real_estate_ai/api/routes/kpi_export.py`
- `ghl_real_estate_ai/api/routes/metrics.py`

### A5. QA/Resilience Agent

Responsibilities:
- Expand unit/integration/E2E coverage for P1/P2 features.
- Add burst/failure-path regression packs.

Primary files:
- `tests/jorge_seller/*`
- `tests/test_jorge_delivery.py`
- `tests/integration/*`

### A6. Observability & Ops Agent

Responsibilities:
- Alert rules, dashboards, and attribution integrity checks.
- Rollout readiness checklist and rollback drills.

Primary files:
- `docs/MONITORING.md`
- `monitoring/*`

## 4) Parallel Workstreams and Task IDs

## WS1: Tenant Provisioning (Owner: A1)

- T1.1: Finalize bootstrap CLI contract and validation rules.
- T1.2: Add duplicate-safe idempotent tenant registration behavior.
- T1.3: Generate tenant-specific onboarding checklist artifact.
- T1.4: Add automated tests for CLI parsing + dry-run + overwrite protection.

Exit criteria:
- Tenant setup in under 15 minutes in staging.
- Checklist artifact generated for every onboarding run.

## WS2: Data Quality (Owner: A2)

- T2.1: Implement required-field completeness validator after each seller turn.
- T2.2: Add numeric parser repair with bounded retries.
- T2.3: Emit structured warning events on unrecoverable parse/write failures.
- T2.4: Add daily completeness report output by tenant.

Exit criteria:
- 98%+ required field write success in sampled transcripts.
- <2% invalid numeric parse in sampled transcripts.

## WS3: Handoff Intelligence (Owner: A3)

- T3.1: Define handoff confidence schema (`mode`, `score`, `reason`, `evidence`).
- T3.2: Tune seller/buyer/lead routing confidence thresholds.
- T3.3: Persist handoff audit log for every routing transition.
- T3.4: Add fallback policy when confidence is ambiguous.

Exit criteria:
- Deterministic routing behavior in conflict-tag scenarios.
- Audit event present for 100% handoffs.

## WS4: KPI Hardening (Owner: A4)

- T4.1: Harden KPI export endpoint input validation and tenant scoping.
- T4.2: Add retry and timeout boundaries for KPI jobs.
- T4.3: Add freshness metadata and stale data flags.
- T4.4: Add regression tests for KPI correctness and auth boundaries.

Exit criteria:
- KPI freshness <24h.
- Report generation success >99%.

## WS5: QA & Resilience (Owner: A5)

- T5.1: Add E2E matrix covering seller/buyer/lead + opt-out + booking.
- T5.2: Add burst webhook load simulation test.
- T5.3: Add GHL transient-failure retry behavior test.
- T5.4: Add release-blocking regression suite preset.

Exit criteria:
- All release-blocking suites green.
- No regression in routing precedence or opt-out compliance.

## WS6: Observability & Rollout Ops (Owner: A6)

- T6.1: Alert for missing tenant attribution.
- T6.2: Alert for send/apply failure spikes.
- T6.3: Alert for KPI freshness SLA breach.
- T6.4: Publish rollout + rollback runbook.

Exit criteria:
- Alerts firing in staging test scenarios.
- Runbook approved by coordinator.

## 5) Dependency Graph

- WS1 is independent and can run immediately.
- WS2 and WS3 run in parallel after baseline schema agreement from A0.
- WS4 can start in parallel but final validation depends on WS6 freshness/alert instrumentation.
- WS5 starts immediately and continuously validates WS1-WS4 outputs.
- WS6 starts immediately; final rules calibrated after WS2-WS4 event contracts stabilize.

## 6) Parallel Sprint Plan (10 Working Days)

Days 1-2:
- A0: Finalize contracts and task sequencing.
- A1: Complete T1.1/T1.2.
- A2: Start T2.1.
- A3: Start T3.1.
- A4: Start T4.1.
- A5: Build regression scaffolding (T5.1 baseline).
- A6: Draft alert specs (T6.1/T6.2).

Days 3-5:
- A1: Finish T1.3/T1.4.
- A2: Finish T2.2/T2.3.
- A3: Finish T3.2/T3.3.
- A4: Finish T4.2/T4.3.
- A5: Add burst/failure tests (T5.2/T5.3).
- A6: Implement alerts in staging (T6.1-T6.3).

Days 6-8:
- A2: T2.4 reporting.
- A3: T3.4 ambiguity fallback.
- A4: T4.4 regression completion.
- A5: T5.4 release-blocking suite.
- A6: T6.4 runbook publish.

Days 9-10:
- Full integration + staging soak.
- Go/No-Go review and limited production rollout.

## 7) Work Protocol and Handoffs

Branching:
- One branch per task: `codex/<agent>-<task-id>`.

PR requirements:
- Problem statement.
- Changes and affected files.
- Test evidence (commands + pass/fail).
- Risk and rollback notes.

Handoff packet between agents:
- API/event contract changes.
- Migration or config changes.
- New tests and expected outputs.

## 8) Merge and Release Gates

No merge unless all are true:
- Unit + integration tests pass for touched modules.
- `tests/test_jorge_delivery.py` green.
- `tests/jorge_seller/test_scope_alignment.py` green.
- No unresolved compliance or opt-out regression.
- Tenant attribution checks present for outbound paths.

No production rollout unless all are true:
- Staging pass for seller HOT booking (30-min consultation).
- Staging pass for buyer and lead routing precedence.
- Observability alerts validated with synthetic failures.

## 9) KPI for Agent Team Performance

- Lead time per task (start to merged).
- PR cycle time (open to merged).
- Reopen rate after QA.
- Regression escape rate.
- Percentage of tasks completed in planned sprint window.

## 10) Risks and Controls

Risk: Parallel edits conflict in webhook routing.
- Control: A0 enforces contract freeze windows and rebases daily.

Risk: Hidden coupling between parser changes and seller classification.
- Control: A5 maintains deterministic temperature regression suite.

Risk: KPI hardening introduces latency.
- Control: A4 adds timeout boundaries and A6 monitors p95/p99.

Risk: Tenant onboarding drift across subaccounts.
- Control: A1 checklist artifact required for every onboarding.

## 11) Definition of Done (Program Level)

Program is complete when:
- WS1-WS6 exit criteria are met.
- Release-blocking suite passes in CI and staging.
- One live tenant rollout completes with no Sev1/Sev2 incident for 7 days.
- Runbook, onboarding kit, and dashboard links are published in `docs/`.
