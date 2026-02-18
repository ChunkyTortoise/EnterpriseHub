# Jorge Bots Completion Execution Spec (Lead + Seller + Buyer)

Version: 1.0  
Date: 2026-02-16  
Status: Execution-ready  
Primary Goal: Complete production-grade value optimization for Jorge’s Lead, Seller, and Buyer bots with measurable KPI lift and stable operations.

---

## 1. Purpose

This spec defines the complete execution path to finish the Jorge bots program from current state through full rollout, including:

1. Remaining architecture hardening.
2. Appointment and lifecycle policy completion.
3. Tone and compliance lock.
4. Metrics and optimization loop finalization.
5. Staged rollout with explicit rollback gates.

---

## 2. Success Criteria (30-day post-rollout window)

1. Qualification completion rate: >= 70%.
2. HOT seller to appointment conversion: +25% relative lift.
3. Appointment show rate: +15% relative lift.
4. Median seller messages to qualification: <= 10.
5. Required seller canonical field completeness at qualification: >= 95%.
6. Opt-out rate: <= 3.5%.
7. Manual intervention rate: <= 10%.

---

## 3. Current State and Gap Summary

### 3.1 Implemented Baseline (already in progress)

1. Expanded seller intake and canonical data model scaffolding.
2. Non-null merge write policy for seller context updates.
3. Canonical mapping validation utilities.
4. Phase env templates extended with canonical seller field placeholders.
5. Initial tests added for canonical gates and mapping validation.

### 3.2 Remaining Gaps to Close

1. Mapping validation is warning-based; production needs hard-gate behavior.
2. Seller custom-field persistence is broad-write; needs change-only writes.
3. HOT appointment flow must enforce strict 30-minute consult type and dual confirmation fallback.
4. Follow-up cadence must be fully lifecycle-driven (HOT daily, WARM weekly, COLD monthly).
5. Cross-bot opt-out suppression must be globally deterministic (`AI-Off` + `Do-Not-Contact` + automation tag cleanup).
6. KPI dashboards and A/B safety loop need completion and operational runbook.

---

## 4. Scope

### In Scope

1. Epics A through G completion across seller, buyer, and lead runtime paths.
2. Canonical seller contract enforcement and operational validation.
3. Appointment engine and lifecycle scheduler completion.
4. Compliance and tone guardrail completion.
5. Metrics schema, dashboards, and controlled experiment rollout.

### Out of Scope

1. Net-new channel additions (voice-only redesigns, social DM expansion).
2. CRM migration or GHL account restructuring.
3. Non-Jorge tenant behavior redesign.

---

## 5. Workstreams and Deliverables

## WS-1: Routing + Contract Hardening (Epic A completion)

Objectives:
1. Standardize contract handling across seller/buyer/lead routes.
2. Enforce canonical contract gate before seller writes.
3. Normalize response/action payload shape for downstream handling.

Primary files:
1. `ghl_real_estate_ai/api/routes/webhook.py`
2. `ghl_real_estate_ai/agents/lead_bot.py`
3. `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
4. `ghl_real_estate_ai/ghl_utils/jorge_config.py`

Acceptance:
1. Seller mode blocks canonical write path when required mappings are missing (configurable fail-open/fail-closed flag).
2. All bot actions emitted in deterministic schema and processed identically.
3. Routing priority remains seller -> buyer -> lead -> fallback without regressions.

## WS-2: Seller Qualification and Persistence Hardening (Epic B/C completion)

Objectives:
1. Keep expanded intake flow deterministic and auditable.
2. Persist only changed canonical fields each turn.
3. Preserve “never erase known non-null unless user-corrected” behavior.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
2. `ghl_real_estate_ai/core/conversation_manager.py`
3. `ghl_real_estate_ai/ghl_utils/jorge_config.py`

Acceptance:
1. Expanded progression reliably asks next missing field.
2. Diff-based custom-field writes reduce redundant updates.
3. Provenance remains accurate per field (`extracted`, `inferred`, `user_confirmed`).

## WS-3: Appointment Engine Optimization (Epic D)

Objectives:
1. Enforce HOT seller booking on strict 30-minute consultation type.
2. Offer exactly 3 valid slots with timezone/business-hour safety.
3. Confirm appointment through SMS + email with fallback queueing.

Primary files:
1. `ghl_real_estate_ai/services/calendar_scheduler.py`
2. `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py`
3. `ghl_real_estate_ai/api/routes/webhook.py`

Acceptance:
1. HOT sellers receive 3 slot options only.
2. Appointment type is always 30-minute consult for this flow.
3. Booking failures tag and enqueue manual scheduler action with user-safe message.

## WS-4: Follow-up Lifecycle Redesign (Epic E)

Objectives:
1. Implement cadence policy: HOT daily, WARM weekly, COLD monthly.
2. Add pause/stop semantics and escalation windows.
3. Add retry ceilings and de-escalation logic for non-response.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py`
2. `ghl_real_estate_ai/services/jorge/jorge_followup_scheduler.py`
3. `ghl_real_estate_ai/ghl_utils/jorge_config.py`

Acceptance:
1. Scheduler outputs cadence aligned with policy and state.
2. Pause/opt-out always suppresses pending follow-ups.
3. Escalation tags/events fire at configured thresholds.

## WS-5: Tone and Compliance Lock (Epic F)

Objectives:
1. Enforce consultative/friendly tone across all outbound templates.
2. Expand compliance fallback coverage and test matrix.
3. Remove aggressive or confrontational wording drift.

Primary files:
1. `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py`
2. `ghl_real_estate_ai/services/compliance_guard.py`
3. `ghl_real_estate_ai/agents/lead_bot.py`
4. `ghl_real_estate_ai/agents/jorge_buyer_bot.py`

Acceptance:
1. Compliance block path always returns safe fallback response.
2. Style checks pass against consultative baseline.
3. All active templates satisfy SMS constraints.

## WS-6: Metrics + Experiment Loop (Epic G)

Objectives:
1. Finalize event schema and metric persistence.
2. Ship dashboard definitions for funnel, efficiency, completeness, opt-out.
3. Add A/B guardrails with rollback thresholds.

Primary files:
1. `ghl_real_estate_ai/services/jorge/bot_metrics_collector.py`
2. `ghl_real_estate_ai/services/jorge/performance_tracker.py`
3. `ghl_real_estate_ai/services/jorge/ab_testing_service.py`

Acceptance:
1. All required events emitted with stable payload schema.
2. Dashboards expose KPI deltas vs baseline.
3. Variant auto-disable on compliance or opt-out threshold breach.

---

## 6. Canonical Seller Data Contract Policy (Production Rules)

1. Every bot turn updates `last_bot_interaction`.
2. Required fields for qualified seller:
   `seller_temperature`, `seller_motivation`, `property_condition`, `timeline_days`, `asking_price`, `ai_valuation_price`, `lead_value_tier`, `qualification_complete`.
3. Preferred fields:
   `mortgage_balance`, `repair_estimate`, `decision_maker_confirmed`, `best_contact_method`, `availability_windows`, `prior_listing_history`.
4. Write policy:
   merge non-empty values only, no null overwrite.
5. Mapping policy:
   required canonical fields must map to GHL IDs before production enablement.

---

## 7. Cross-Bot Opt-out and Suppression Standard

1. Immediate response stop.
2. Add tags: `AI-Off`, `Do-Not-Contact`.
3. Remove activation/automation tags for seller/buyer/lead.
4. Log `opt_out_detected` event with bot mode and timestamp.
5. Ensure no follow-up scheduling continues after suppression.

---

## 8. Testing Strategy (Completion)

### Unit
1. Canonical mapping gate behavior (fail-open/fail-closed).
2. Diff-based field write selection.
3. Temperature boundary logic with `timeline_days`.
4. Lifecycle scheduler cadence and retry policies.

### Integration
1. Route selection + mode transitions.
2. HOT booking path with 30-minute consult enforcement.
3. Opt-out suppression across all three bots.
4. Canonical field completeness at qualification milestone.

### E2E
1. Seller intake -> qualification_complete -> hot booking.
2. Warm/cold lifecycle follow-up transitions.
3. Failure cases: booking API failure, compliance block, timeout.

### Performance
1. Re-run Jorge baseline suites.
2. P95/P99 latency regression checks under rollout load.

---

## 9. Rollout Plan

## Phase 0: Staging Hardening (3-5 days)
1. Deploy WS-1 and WS-2 with gates enabled in staging.
2. Execute full integration and E2E suite.
3. Validate mapping completeness and suppression behavior.

## Phase 1: Seller-First Production (7+ days)
1. Enable seller appointment + lifecycle + contract hardening.
2. Daily KPI monitor: conversion, opt-out, completeness, manual interventions.
3. Rollback trigger: opt-out > 3.5% or booking failure > threshold.

## Phase 2: Seller + Buyer Production (7+ days)
1. Enable buyer parity changes and cross-bot suppression standard.
2. Validate lead->buyer and seller->buyer handoff accuracy.

## Phase 3: Full Three-Bot + Experiment Loop
1. Enable lead optimization and controlled A/B testing.
2. Weekly KPI review with named rollback authority.

---

## 10. Risk Register and Mitigation

1. Missing GHL mappings in production.
Mitigation: hard gate + preflight validator + deploy checklist.

2. Over-aggressive cadence increases opt-outs.
Mitigation: retry ceilings + de-escalation + realtime threshold monitor.

3. Booking API brittleness impacts hot conversion.
Mitigation: fallback queue + dual channel confirmation retry + alerting.

4. Style drift across templates.
Mitigation: compliance guard + template snapshot tests + audit runbook.

---

## 11. Definition of Done (Program Completion)

1. All Epics A-G accepted in production.
2. Canonical required field completeness >= 95% for qualified sellers.
3. HOT booking flow uses strict 30-minute consultation type and dual confirmation.
4. Follow-up cadence policy executes deterministically by temperature and lifecycle.
5. Opt-out suppression is deterministic across all bot modes.
6. KPI dashboards show uplift against baseline and support ongoing optimization.

---

## 12. Execution Order (Recommended)

1. WS-1 Routing/contract hardening.
2. WS-2 Seller persistence hardening.
3. WS-3 Appointment optimization.
4. WS-4 Lifecycle scheduler redesign.
5. WS-5 Tone/compliance lock.
6. WS-6 Metrics + A/B loop.
7. Phase rollout with go/no-go gates.

---

## 13. Operator Checklist Before Production Enablement

1. Fill required `CUSTOM_FIELD_*` IDs for canonical required fields in:
   `deploy/phase1_seller_only.env`, `deploy/phase2_seller_buyer.env`, `deploy/phase3_all_bots.env`.
2. Confirm fail-open/fail-closed setting for mapping gate.
3. Verify 30-minute consult appointment type ID and calendar linkage.
4. Confirm DNC tag taxonomy in GHL uses exact `Do-Not-Contact`.
5. Confirm dashboard queries and alert thresholds are configured.

