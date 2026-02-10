# Jorge Day 2 Execution Board

Date: 2026-02-10  
Scope: Day 2 of 10-day parallel sprint from `JORGE_AGENT_TEAM_PARALLEL_SPEC.md`  
Coordinator: A0  
Inputs required: Day 1 artifacts in `docs/handoffs/day1_*` and `docs/handoffs/day1_execution_digest.md`

## 1) Day 2 Goals

- Close all Day 1 starter slices into merge-ready PRs or explicit carry-over.
- Complete Days 1-2 sprint objectives from the base plan.
- Freeze cross-stream contracts before end-of-day integration checks.

## 2) Day 2 Entry Gate (Must Pass by 09:30)

- E2-1: A0 confirms Day 1 execution digest is published.
- E2-2: Any unresolved Day 1 blocker has owner + ETA.
- E2-3: WS2/WS3 schema baseline and WS4/WS6 telemetry contract are marked stable for Day 2.
- E2-4: A5 baseline regression scaffold is available for all agents.

If any entry gate fails, A0 runs a 60-minute recovery lane before parallel work begins.

## 3) Agent-by-Agent Queue

## A0 Coordinator (Program Control)

- Q0.4 (Priority P0): Validate Day 1 carry-over and republish dependency map for Day 2.
  - Output: `docs/handoffs/day2_dependency_map.md`
  - Depends on: Day 1 execution digest
  - Handoff: all agents
- Q0.5 (Priority P0): Approve Day 2 contract freeze window (schema/routing/KPI telemetry).
  - Output: `docs/handoffs/day2_contract_freeze.md`
  - Depends on: Q0.4
  - Handoff: A2, A3, A4, A6, A5
- Q0.6 (Priority P0): Publish Day 2 EOD merge candidate list.
  - Output: `docs/handoffs/day2_merge_candidates.md`
  - Depends on: Q0.5
  - Handoff: all agents

## A1 Tenant Provisioning (WS1)

- Q1.3 (Task T1.2 completion): Complete duplicate-safe idempotent tenant registration behavior.
  - Output: PR ready on `codex/a1-t1.2`
  - Files: `ghl_real_estate_ai/services/tenant_service.py`
  - Depends on: Day 1 Q1.2 draft
  - Verification: duplicate create/update/no-op behavior tests all pass
- Q1.4 (Task T1.3 start): Generate tenant-specific onboarding checklist artifact.
  - Output: draft PR on `codex/a1-t1.3`
  - Files: `scripts/tenant_bootstrap.py`, `docs/tenant_onboarding/*`
  - Depends on: Q1.3
  - Verification: checklist artifact emitted on successful bootstrap run

## A2 Data Quality (WS2)

- Q2.3 (Task T2.1 completion): Finalize required-field completeness validator and enforcement point.
  - Output: merge-ready PR on `codex/a2-t2.1`
  - Files: `ghl_real_estate_ai/core/conversation_manager.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
  - Depends on: Q0.5
  - Verification: completeness tests include seller-turn edge cases
- Q2.4 (Task T2.2 progression): Expand numeric parser repair with bounded retries and failure classification.
  - Output: PR on `codex/a2-t2.2`
  - Files: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
  - Depends on: Q2.3
  - Verification: retry + unrecoverable-path tests pass

## A3 Handoff Intelligence (WS3)

- Q3.3 (Task T3.1 completion): Finalize handoff confidence schema integration across routing surfaces.
  - Output: merge-ready PR on `codex/a3-t3.1`
  - Files: `ghl_real_estate_ai/api/routes/webhook.py`, `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`, `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
  - Depends on: Q0.5
  - Verification: schema event snapshot tests pass
- Q3.4 (Task T3.2 progression): Tune seller/buyer/lead confidence thresholds with deterministic conflict handling.
  - Output: PR on `codex/a3-t3.2`
  - Files: same as Q3.3
  - Depends on: Q3.3
  - Verification: conflict-tag routing matrix passes with stable outcomes

## A4 KPI Productization (WS4)

- Q4.3 (Task T4.1 completion): Finalize KPI export validation + tenant scoping hardening.
  - Output: merge-ready PR on `codex/a4-t4.1`
  - Files: `ghl_real_estate_ai/api/routes/kpi_export.py`, `ghl_real_estate_ai/api/routes/metrics.py`
  - Depends on: Q0.5
  - Verification: auth/tenant negative tests pass
- Q4.4 (Task T4.2 progression): Complete timeout and retry boundaries for KPI jobs.
  - Output: PR on `codex/a4-t4.2`
  - Files: KPI route/job modules touched by Q4.3
  - Depends on: Q4.3
  - Verification: timeout, retry ceiling, and failure telemetry assertions pass

## A5 QA/Resilience (WS5)

- Q5.3 (Task T5.1 expansion): Extend E2E matrix to full Day 2 scenario set.
  - Output: PR on `codex/a5-t5.1-day2`
  - Files: `tests/jorge_seller/*`, `tests/test_jorge_delivery.py`, `tests/integration/*`
  - Depends on: Q0.4
  - Verification: seller/buyer/lead + opt-out + booking matrix green
- Q5.4 (Task T5.2 prep): Build burst webhook load harness skeleton and fixture packs.
  - Output: draft PR on `codex/a5-t5.2`
  - Files: `tests/integration/*`
  - Depends on: Q5.3
  - Verification: harness executes and reports baseline timing/error output

## A6 Observability & Ops (WS6)

- Q6.3 (Task T6.1 completion): Implement alert rule for missing tenant attribution in staging config.
  - Output: PR on `codex/a6-t6.1`
  - Files: `docs/MONITORING.md`, `monitoring/*`
  - Depends on: Q0.5
  - Verification: synthetic missing-attribution scenario triggers alert
- Q6.4 (Task T6.2 completion): Implement spike alert for send/apply failures with calibrated thresholds.
  - Output: PR on `codex/a6-t6.2`
  - Files: same as Q6.3
  - Depends on: Q6.3
  - Verification: synthetic failure burst triggers alert within expected window

## 4) Day 2 Parallel Lanes

- Lane A (Core product): A1, A2, A3, A4 complete Day 1 carry-over and produce merge-ready PRs.
- Lane B (Quality): A5 expands matrix coverage and prepares burst-load track.
- Lane C (Ops): A6 converts alert specs to staging-enforced rules.
- Lane D (Control): A0 runs contract freeze and merge candidate control.

## 5) Day 2 Timeboxes (Suggested)

- 09:00-09:30: Entry gate and blocker triage (A0 + all).
- 09:30-12:30: Qx.3 execution (completion-focused).
- 12:30-14:00: Midday dependency check and rebases.
- 14:00-17:00: Qx.4 execution (progression slices).
- 17:00-18:00: Merge candidate review and Day 3 resequencing.

## 6) Required Handoff Packet (End of Day)

Each agent must post:

- Branch + PR link (`codex/<agent>-<task-id>`).
- What changed since Day 1.
- Contract delta confirmation (`none` is valid but must be explicit).
- Test evidence (commands + pass/fail summary).
- Outstanding blocker and expected Day 3 impact.

## 7) Day 2 Merge Gate Check

Do not merge without:

- Touched module unit/integration tests passing.
- `tests/test_jorge_delivery.py` passing for touched behavior.
- `tests/jorge_seller/test_scope_alignment.py` passing for touched behavior.
- No compliance/opt-out regression indicators.
- Tenant attribution checks present for outbound paths.

## 8) End-of-Day Output From A0

- `docs/handoffs/day2_execution_digest.md` including:
  - Completed and merged tasks.
  - Open PRs and blockers.
  - Contract changes approved/denied.
  - Day 3 start order for each agent.
