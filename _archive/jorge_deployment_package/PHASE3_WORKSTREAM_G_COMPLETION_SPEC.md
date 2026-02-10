# Phase 3 Workstream G Completion Spec

## Purpose
Define the remaining implementation work to complete Workstream G (growth experiments) while preserving production safety, test integrity, and fast rollback.

## Current Baseline (Already Implemented)
1. Phase 1 (A-C) complete:
   - Context persistence fix.
   - GHL client contract alignment.
   - Webhook HMAC + idempotency guard.
2. Phase 2 (D-F) complete:
   - Data-driven `/health`, `/performance`, `/metrics`.
   - Strict pytest suite + standalone runtime checks.
   - README and quick-start corrections.
3. Phase 3 (G) partial complete:
   - Feature-flag scaffolding in settings.
   - Growth telemetry counters in runtime metrics.
   - Adaptive follow-up timing (flagged + canary aware).
   - Lead-source attribution + conversion feedback metadata capture (flagged).
   - Rollout/backout writeback toggles exposed in `/metrics`.
   - Current validation:
     - `pytest -c pytest.ini` -> 22 passed
     - `python3 test_standalone.py` -> passed

## Hard Constraints
1. Never revert unrelated local edits.
2. Continue from current uncommitted workspace state.
3. Keep all tests passing after each logical change.
4. Default behavior must remain unchanged when feature flags are OFF.
5. New behavior must be canary-compatible via existing growth gate evaluator.

## Remaining Scope to Complete Workstream G
1. Feature 3: A/B response style testing with per-segment reporting.
2. Feature 4: SLA-based human handoff thresholds.
3. Conversion feedback loop closure:
   - Move from telemetry-only events to optional writeback/decision hooks.
4. Documentation and rollout guidance for production enablement.

---

## Feature 3: A/B Response Style Testing

### Goal
Assign response style variants safely (A/B) for eligible leads, capture telemetry per segment/source, and preserve current message output when disabled.

### Flag + Gate
1. Use existing flag: `FF_GROWTH_AB_RESPONSE_STYLE_TESTING_ENABLED`.
2. Evaluate via shared `_evaluate_growth_feature(feature_name="ab_response_style_testing", lead_source=...)`.
3. Respect canary mode/source restrictions automatically.

### Implementation Requirements
1. Add a style assignment helper in `jorge_fastapi_lead_bot.py`.
2. Deterministic bucketing:
   - Use stable key from `contact_id` + `lead_source` (hash modulo 100).
   - Variant mapping example: `A` for 0-49, `B` for 50-99.
3. Segment awareness:
   - Segment from lead temperature/priority (for reporting only).
4. Non-invasive behavior:
   - If feature disabled, do not alter generated response content.
   - If enabled, attach metadata to analysis context and/or follow-up metadata first.
   - Message text variation can be minimal and reversible.

### Telemetry Requirements
1. Record events before behavior mutation:
   - `ab_response_style_testing:assignment_observed`
   - `ab_response_style_testing:variant_a` or `variant_b`
   - `ab_response_style_testing:segment_<segment>`
2. Record bypass reasons:
   - `ab_response_style_testing:bypassed_flag_disabled`
   - `ab_response_style_testing:bypassed_canary_source_mismatch`
   - `ab_response_style_testing:bypassed_canary_source_missing`
3. Record apply marker:
   - `ab_response_style_testing:applied`

### Tests
1. Unit tests in `tests/test_growth_feature_flags.py`:
   - Disabled path no output mutation + bypass event.
   - Enabled path deterministic variant assignment.
   - Canary mismatch path blocked + blocked telemetry.
2. Observability test:
   - Ensure growth counters remain present and include new event keys after execution.

---

## Feature 4: SLA-Based Human Handoff Thresholds

### Goal
Escalate leads to human follow-up when SLA risk is detected, while preserving existing automation when disabled.

### Flag + Gate
1. Use existing flag: `FF_GROWTH_SLA_HANDOFF_THRESHOLDS_ENABLED`.
2. Gate with shared growth evaluator and canary mode.

### Implementation Requirements
1. Add SLA risk helper in `jorge_fastapi_lead_bot.py`:
   - Inputs: lead score, priority, timing bucket, elapsed processing context.
   - Output: handoff recommendation payload with reason code.
2. Integrate into webhook lead flow after analysis and before scheduling.
3. If enabled and risk high:
   - Append explicit handoff signal metadata to `analysis_result`.
   - Optionally append a `needs_handoff` tag candidate for `update_ghl_contact`.
4. If disabled:
   - Preserve current follow-up flow exactly.

### Telemetry Requirements
1. Baseline events:
   - `sla_handoff_thresholds:observed`
   - `sla_handoff_thresholds:risk_high|risk_medium|risk_low`
2. Action events:
   - `sla_handoff_thresholds:handoff_recommended`
   - `sla_handoff_thresholds:handoff_not_required`
3. Bypass event:
   - `sla_handoff_thresholds:bypassed_<reason>`

### Tests
1. Unit tests for thresholds and outcomes.
2. Integration-level webhook test path confirming no regression in default response.
3. Assert that disabled flag yields no handoff mutation.

---

## Conversion Feedback Loop Closure

### Goal
Advance from observed conversion outcomes to optional operational feedback propagation.

### Requirements
1. Keep telemetry always-on for observed status transitions.
2. Add optional writeback behavior only when toggles are ON:
   - `FF_GROWTH_CONVERSION_FEEDBACK_WRITEBACK_ENABLED`
3. Ensure no GHL field/tag writeback occurs when writeback toggle is OFF.
4. Add guardrails for unknown statuses and malformed contact payloads.

### Telemetry
1. `lead_source_attribution:conversion_feedback_observed_<outcome>`
2. `lead_source_attribution:conversion_feedback_loop_<outcome>` when active.
3. `lead_source_attribution:conversion_feedback_telemetry_only` when writeback off.

---

## Observability and API Contract

### `/metrics` Contract Must Include
1. `runtime_metrics.counters.feature_flag_evaluations_total`
2. `runtime_metrics.counters.growth_feature_events_total`
3. `growth_rollout.flags`
4. `growth_rollout.writeback_toggles`

### Optional Enhancement
1. Add a compact `growth_rollout.last_updated` timestamp if useful.

---

## Test and Validation Plan

### Required Commands
1. `pytest -c pytest.ini`
2. `python3 test_standalone.py`

### Suggested Iteration Discipline
1. Implement one feature slice.
2. Add/adjust tests.
3. Run required commands.
4. Repeat.

### Exit Criteria
1. Required commands pass.
2. New tests cover enabled/disabled/canary-blocked behavior.
3. No default-behavior regression under all flags OFF.
4. `/metrics` exposes rollout and feature telemetry consistently.

---

## Rollout / Backout Plan

### Rollout Sequence
1. Deploy with all new feature flags OFF.
2. Enable canary mode for one source.
3. Enable one feature at a time:
   - A/B style testing.
   - SLA handoff thresholds.
4. Observe metrics for 24h.
5. Enable broader rollout only if no error/compliance regression.

### Backout Sequence
1. Disable feature flag first (instant behavior rollback).
2. If needed, disable writeback toggle second.
3. Keep telemetry running for postmortem signal.

---

## Deliverables Checklist
1. Code updates in FastAPI flow for Feature 3 and Feature 4.
2. Test coverage updates in growth and observability tests.
3. Updated session handoff doc with latest status and test counts.
4. Final report listing changed files + exact command outputs.

---

## Implementation File Targets
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/config_settings.py`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/runtime_metrics.py`
3. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py`
4. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/tests/test_growth_feature_flags.py`
5. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/tests/test_observability.py`
6. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/test_standalone.py`
7. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/README.md`
8. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/QUICK_START_NEXT_SESSION.md`

