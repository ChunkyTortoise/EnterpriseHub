# Jorge Day 1 Execution Board

Date: 2026-02-09  
Scope: Day 1 of 10-day parallel sprint from `JORGE_AGENT_TEAM_PARALLEL_SPEC.md`  
Coordinator: A0

## 1) Day 1 Goals

- Lock shared contracts needed for parallel work (schema + routing confidence).
- Start one shippable PR-sized increment per specialist agent.
- End Day 1 with test evidence and handoff packets for all active tracks.

## 2) Dependency Unlocks (Day 1)

- D-LOCK-1: A0 publishes baseline schema agreement for WS2 + WS3 before A2/A3 implementation merges.
- D-LOCK-2: A0 confirms KPI telemetry contract draft so A4 and A6 can align freshness/error signals.
- D-LOCK-3: A5 publishes regression scaffold interface so agents can add tests without fixture drift.

## 3) Agent-by-Agent Queue

## A0 Coordinator (Program Control)

- Q0.1 (Priority P0): Publish Day 1 contract freeze window and ownership map.
  - Output: `docs/handoffs/day1_contract_freeze.md`
  - Depends on: none
  - Handoff: all agents
- Q0.2 (Priority P0): Approve WS2/WS3 schema baseline (fields, confidence event shape).
  - Output: `docs/handoffs/day1_schema_baseline.md`
  - Depends on: Q0.1
  - Handoff: A2, A3, A5
- Q0.3 (Priority P0): Publish Day 1 EOD Go/No-Go checklist.
  - Output: `docs/handoffs/day1_gate_checklist.md`
  - Depends on: Q0.2
  - Handoff: all agents

## A1 Tenant Provisioning (WS1)

- Q1.1 (Task T1.1): Finalize bootstrap CLI contract and validation rules.
  - Output: PR on `codex/a1-t1.1`
  - Files: `scripts/tenant_bootstrap.py`, `docs/tenant_onboarding/*`
  - Depends on: Q0.1
  - Verification: CLI parse/validation tests pass
- Q1.2 (Task T1.2, starter slice): Add idempotency guard for duplicate-safe tenant registration.
  - Output: Draft PR on `codex/a1-t1.2`
  - Files: `ghl_real_estate_ai/services/tenant_service.py`
  - Depends on: Q1.1
  - Verification: duplicate registration path test added and passing

## A2 Data Quality (WS2)

- Q2.1 (Task T2.1): Implement required-field completeness validator hook after seller turn.
  - Output: PR on `codex/a2-t2.1`
  - Files: `ghl_real_estate_ai/core/conversation_manager.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
  - Depends on: Q0.2
  - Verification: validator unit tests for missing required fields
- Q2.2 (Task T2.2, starter slice): Add numeric parser retry scaffold with bounded retry constants.
  - Output: draft commit on `codex/a2-t2.2`
  - Files: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
  - Depends on: Q2.1
  - Verification: retry boundary test (max retries honored)

## A3 Handoff Intelligence (WS3)

- Q3.1 (Task T3.1): Define and wire handoff confidence schema (`mode`, `score`, `reason`, `evidence`).
  - Output: PR on `codex/a3-t3.1`
  - Files: `ghl_real_estate_ai/api/routes/webhook.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`, `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
  - Depends on: Q0.2
  - Verification: schema conformance tests for routing events
- Q3.2 (Task T3.2, starter slice): Add threshold constants and config surface for tuning.
  - Output: draft commit on `codex/a3-t3.2`
  - Files: same as Q3.1
  - Depends on: Q3.1
  - Verification: conflict-tag deterministic routing test added

## A4 KPI Productization (WS4)

- Q4.1 (Task T4.1): Harden KPI export input validation and tenant scoping.
  - Output: PR on `codex/a4-t4.1`
  - Files: `ghl_real_estate_ai/api/routes/kpi_export.py`, `ghl_real_estate_ai/api/routes/metrics.py`
  - Depends on: Q0.1
  - Verification: auth boundary + tenant filter tests pass
- Q4.2 (Task T4.2, starter slice): Add timeout/retry guardrails for KPI jobs.
  - Output: draft commit on `codex/a4-t4.2`
  - Files: KPI route/job modules touched by Q4.1
  - Depends on: Q4.1
  - Verification: timeout boundary test and retry count assertion

## A5 QA/Resilience (WS5)

- Q5.1 (Task T5.1 baseline): Build Day 1 regression scaffold for seller/buyer/lead + opt-out + booking.
  - Output: PR on `codex/a5-t5.1`
  - Files: `tests/jorge_seller/*`, `tests/test_jorge_delivery.py`, `tests/integration/*`
  - Depends on: Q0.3
  - Verification: baseline matrix tests run in CI locally
- Q5.2 (Task T5.4 seed): Define release-blocking suite preset command + marker strategy.
  - Output: draft commit on `codex/a5-t5.4`
  - Files: test config and suite selectors
  - Depends on: Q5.1
  - Verification: one-command release-blocking dry run completes

## A6 Observability & Ops (WS6)

- Q6.1 (Task T6.1): Draft alert rule spec for missing tenant attribution.
  - Output: PR on `codex/a6-t6.1`
  - Files: `docs/MONITORING.md`, `monitoring/*`
  - Depends on: Q0.1
  - Verification: synthetic scenario defined and expected signal documented
- Q6.2 (Task T6.2): Draft spike alert spec for send/apply failures.
  - Output: draft commit on `codex/a6-t6.2`
  - Files: same as Q6.1
  - Depends on: Q6.1
  - Verification: threshold and sampling window documented with test case

## 4) Day 1 Timeboxes (Suggested)

- 09:00-10:00: A0 executes Q0.1/Q0.2 to unblock A2/A3.
- 10:00-13:00: A1/A2/A3/A4/A6 execute first queue item (Qx.1).
- 13:00-15:00: A5 executes Q5.1 after A0 publishes gate checklist.
- 15:00-17:00: All agents execute Qx.2 starter slices and prepare handoff packets.
- 17:00-18:00: A0 runs Go/No-Go against merge gates for Day 1 carry-forward.

## 5) Required Handoff Packet (End of Day)

Each agent must post:

- Branch + PR link (`codex/<agent>-<task-id>`).
- Contract deltas (API/event/schema/threshold changes).
- Test evidence (commands run + pass/fail summary).
- Risks discovered + rollback notes.
- Explicit blockers for Day 2.

## 6) Day 1 Merge Gate Check

Do not merge without:

- Touched module unit/integration tests passing.
- `tests/test_jorge_delivery.py` passing for touched behavior.
- `tests/jorge_seller/test_scope_alignment.py` passing for touched behavior.
- No compliance/opt-out regression indicators.
- Tenant attribution preserved for outbound paths.

## 7) End-of-Day Output From A0

- `docs/handoffs/day1_execution_digest.md` including:
  - Completed queue items.
  - Deferred items and reasons.
  - Risks requiring Day 2 mitigation.
  - Day 2 resequencing decisions.
