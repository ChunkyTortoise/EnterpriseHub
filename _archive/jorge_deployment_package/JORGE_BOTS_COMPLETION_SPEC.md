# Jorge Bots Completion Spec
**Status**: Draft for Execution  
**Date**: February 10, 2026  
**Version**: 1.0  
**Scope**: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package`

---

## 1. Purpose

This spec defines the end-to-end implementation plan to complete the remaining hardening and growth work for Jorge's bots. It converts the identified gaps into concrete engineering work with acceptance criteria, testing gates, and rollout requirements.

This plan prioritizes production reliability first, then growth features.

---

## 2. Objectives

1. Fix runtime defects that currently break persistence and external integrations.
2. Enforce webhook security and replay safety.
3. Replace placeholder observability with real telemetry.
4. Upgrade test and CI quality so failures are surfaced, not masked.
5. Align docs and onboarding scripts with actual repository state.
6. Define post-hardening growth features with measurable business outcomes.

---

## 3. Out of Scope

1. Full rewrite of the bot architecture.
2. Migration from file storage to a new database platform in this phase.
3. New UI redesign for dashboard visuals.
4. Multi-tenant backend redesign.

---

## 4. Current-State Findings (Evidence)

1. Context persistence fails at runtime because optimized engines call `update_context` with an invalid signature.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_engines_optimized.py:374`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_engines_optimized.py:733`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/conversation_manager.py:54`

2. FastAPI lead service calls undefined GHL client methods.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py:416`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py:428`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/ghl_client.py:25`

3. Webhook server uses undefined SMS method.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_webhook_server.py:383`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/ghl_client.py:25`

4. Lead webhook lacks signature verification and replay/idempotency controls.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py:261`

5. Health/perf endpoints return placeholders instead of runtime metrics.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py:156`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py:191`

6. README references setup files/scripts that are missing.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/README.md:25`
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/README.md:26`

7. Existing standalone test script can report success while runtime logs include critical errors.
Path: `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/test_standalone.py:1`

---

## 5. Target Architecture Changes

1. Keep `ConversationManager` API as the canonical interface and adapt optimized engines to it.
2. Standardize `GHLClient` surface area used by all services.
3. Add webhook authenticity and replay protection in lead webhook entrypoint.
4. Add in-process metrics registry with counters/histograms and expose truthful `/health` and `/performance`.
5. Replace permissive smoke script with assertive tests and wire minimal CI for this package.

---

## 6. Workstreams

## Workstream A: Conversation State Persistence Fix

### Problem
Optimized engines call `update_context(contact_id, location_id, context_update)`, but the function expects `contact_id`, `user_message`, `ai_response`, `extracted_data`, and `location_id`.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_engines_optimized.py`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/conversation_manager.py`

### Implementation
1. Update optimized engine callers to pass valid arguments.
2. Ensure both seller and lead paths save `conversation_history` entries.
3. Add a compatibility helper in `ConversationManager` only if needed:
`update_context_compact(contact_id, location_id, context_update, user_message="", ai_response="")`.
4. Preserve backward compatibility for existing callers in `jorge_engines.py`.

### Acceptance Criteria
1. No `update_context` signature errors during seller or lead flow.
2. New JSON entries are written under `data/conversations/`.
3. `seller_questions_answered` and `lead_temperature` persist across turns.

### Tests
1. Unit test for seller context update.
2. Unit test for lead context update.
3. Integration test: two-turn seller conversation increments question count.

---

## Workstream B: GHL Client Contract Alignment

### Problem
Callers expect methods absent from `GHLClient`.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/ghl_client.py`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py`
3. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_webhook_server.py`

### Implementation
1. Add methods to `GHLClient`:
`send_sms(phone, message)`, `update_contact_custom_fields(contact_id, updates)`, `add_contact_tags(contact_id, tags)`.
2. Implement these methods via existing primitives (`send_message`, `update_contact`, `add_tag`).
3. Normalize return contracts.
`True/False` for mutation success, payload dict for read endpoints.
4. Enforce httpx timeout defaults and retry policy for transient failures.
5. Add structured logs with request operation name and status code.

### Acceptance Criteria
1. No `AttributeError` for GHL methods in lead API and webhook server.
2. Failed API operations are surfaced as explicit `False` with logs.
3. No silent pass on malformed update payloads.

### Tests
1. Unit test for each new method with mocked `httpx.AsyncClient`.
2. Integration test ensuring lead analysis endpoint triggers GHL updates without method errors.

---

## Workstream C: Webhook Security and Idempotency

### Problem
Lead webhook currently trusts request payload by default and can process duplicate events.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/config_settings.py`
3. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/conversation_manager.py` or new idempotency module

### Implementation
1. Add HMAC verification using `X-GHL-Signature` and `GHL_WEBHOOK_SECRET`.
2. Fail closed in production if signature missing/invalid.
3. Add idempotency key extraction.
Use provider event id if present, else deterministic hash of contact id + timestamp + type.
4. Add replay store with TTL (file-backed for current scope).
5. Return idempotent acknowledgment for duplicate events.
6. Emit audit log fields: `webhook_id`, `signature_valid`, `duplicate`.

### Acceptance Criteria
1. Invalid signatures are rejected with 403.
2. Duplicate webhook payloads do not trigger duplicate side effects.
3. Valid signed webhook remains under response SLA.

### Tests
1. Signature-valid/invalid/missing tests.
2. Duplicate-event test verifies one update execution.
3. Replay TTL expiry behavior test.

---

## Workstream D: Real Health and Performance Telemetry

### Problem
Performance and health endpoints include placeholders, which hides real system condition.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_fastapi_lead_bot.py`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/jorge_claude_intelligence.py`
3. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/ghl_client.py`
4. New file: metrics utility

### Implementation
1. Add in-process metrics registry with:
`request_count`, `error_count`, `avg_response_ms`, `p95_response_ms`, `cache_hit_rate`, `ghl_success_rate`, `webhook_duplicate_count`.
2. Update middleware to write latency histogram and status-code counters.
3. Use real compliance values in `/performance`.
4. Update `/health` to include:
GHL API health probe, Claude availability mode, file storage writability.
5. Add `/metrics` endpoint for machine-readable export (JSON format is acceptable for this phase).

### Acceptance Criteria
1. `/health` reflects real dependency status.
2. `/performance` values change with traffic and errors.
3. Slow requests and 5-minute violations are measurable and queryable.

### Tests
1. Middleware test validates metrics increment.
2. Endpoint test validates non-placeholder values after synthetic requests.

---

## Workstream E: Test Quality and CI Coverage

### Problem
Current validation script does not fail on critical runtime defects.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/test_standalone.py`
2. New tests under `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/tests/`
3. New local CI config for package-level tests

### Implementation
1. Refactor `test_standalone.py` into assertive checks.
2. Add `pytest` suite:
`test_context_persistence.py`
`test_ghl_client_contract.py`
`test_webhook_security.py`
`test_observability.py`
3. Mock outbound network calls by default.
4. Add one optional integration marker for real API environments.
5. Add a package-local `pytest.ini` with strict settings:
`-q`, `-ra`, fail on warnings for test package.

### Acceptance Criteria
1. Regression from Workstreams A-D fails tests.
2. No hard dependency on live credentials for default test run.
3. Test output clearly identifies failing domain.

---

## Workstream F: Documentation and Onboarding Correction

### Problem
README and quick start are inconsistent with actual files and commands.

### Files
1. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/README.md`
2. `/Users/cave/Documents/New project/enterprisehub/jorge_deployment_package/QUICK_START_NEXT_SESSION.md`
3. New docs as required

### Implementation
1. Remove references to missing files unless created.
2. Either create missing scripts/docs or update README to existing workflow.
3. Add a verified startup path:
create env, install deps, run API, run dashboard, run tests.
4. Add troubleshooting section for signature failures, GHL auth errors, and missing env vars.
5. Add versioned "known limitations" section.

### Acceptance Criteria
1. Fresh clone can follow README without dead links.
2. Every command in quick start executes or is explicitly flagged optional.

---

## Workstream G: Growth Features (Post-Hardening)

### Objective
Ship business growth improvements only after reliability gates pass.

### Candidate Features
1. Lead-source attribution and conversion feedback loop.
2. Adaptive follow-up timing by engagement score.
3. A/B response style testing with per-segment reporting.
4. SLA-based human handoff thresholds.

### Implementation Notes
1. Introduce feature flags for each capability.
2. Add telemetry per feature before enabling default behavior.
3. Roll out behind canary mode for one lead source first.

### Success Metrics
1. +10% relative improvement in appointment-booked rate.
2. -15% response-to-handoff median time for hot leads.
3. No increase in opt-out rate.

---

## 7. Delivery Plan and Sequence

## Phase 1: Hardening Foundation (Days 1-3)
1. Workstream A
2. Workstream B
3. Workstream C

## Phase 2: Visibility and Quality (Days 4-5)
1. Workstream D
2. Workstream E
3. Workstream F

## Phase 3: Growth Experiments (Days 6-10)
1. Workstream G behind flags
2. Controlled rollout and measurement

---

## 8. Detailed Acceptance Gates

## Gate 1: Runtime Integrity
1. No context update signature errors in logs for lead/seller paths.
2. No undefined GHL method errors in logs.

## Gate 2: Security Integrity
1. Webhook rejects invalid signatures.
2. Duplicate event replay is suppressed.

## Gate 3: Observability Integrity
1. `/health` and `/performance` are data-driven.
2. 24-hour run shows non-zero real counters.

## Gate 4: Quality Integrity
1. Package tests pass locally without live credentials.
2. Failing regression in A-D is detectable by test suite.

## Gate 5: Operational Integrity
1. README quick start succeeds on clean environment.
2. Missing-file references resolved.

---

## 9. Technical Design Details

## 9.1 Idempotency Store
1. Backing file: `data/webhook_idempotency.json`.
2. Record shape:
`{ "event_id": "...", "seen_at": "...", "expires_at": "...", "status": "processed" }`.
3. TTL default: 24 hours.
4. Cleanup strategy: purge expired entries on insert/read.

## 9.2 Metrics Data Model
1. Rolling windows:
1-minute, 5-minute, 24-hour.
2. Fields:
`requests_total`, `errors_total`, `latency_ms_sum`, `latency_ms_count`, `latency_ms_p95`, `ghl_calls_total`, `ghl_calls_failed`, `cache_hits`, `cache_misses`, `signature_failures`, `duplicate_webhooks`.

## 9.3 Error Handling Policy
1. Network 5xx/timeout: retry with exponential backoff.
2. 4xx non-rate-limit: no retry, surface failure.
3. Rate-limit 429: bounded retry with jitter.
4. All fallback paths must include explicit log marker `fallback_used=true`.

---

## 10. Test Strategy Matrix

| Domain | Test Type | Required Cases |
|---|---|---|
| Context persistence | Unit + integration | valid update, malformed input, multi-turn progression |
| GHL client contract | Unit | each method success, 401, 429, 500 |
| Webhook security | Unit | valid signature, invalid signature, missing signature, replay |
| Observability | Unit + integration | metric increments, health degradation, performance aggregation |
| Docs onboarding | Manual check script | command existence, file existence, quick start dry run |

---

## 11. Rollout and Backout

## Rollout
1. Deploy with security checks in warn mode for 24 hours in staging.
2. Switch to enforce mode in staging after zero false rejects.
3. Deploy to production with canary traffic.
4. Enable growth features one by one after hardening gates pass.

## Backout
1. Feature flag disable for each new module.
2. Revert to previous webhook processing path if signature mismatch rates spike.
3. Preserve idempotency store snapshots for incident analysis.

---

## 12. Risks and Mitigations

1. Risk: False-negative signature validation due to provider payload differences.
Mitigation: canonical signing string tests and staged warn mode.

2. Risk: Increased latency from metrics and idempotency checks.
Mitigation: O(1) in-memory cache layer with batched file flush.

3. Risk: Existing callers rely on old GHL semantics.
Mitigation: compatibility wrappers and deprecation logs.

4. Risk: File-based stores can corrupt on abrupt process termination.
Mitigation: atomic writes using temp file + rename.

---

## 13. Definition of Done

1. Workstreams A-F completed and accepted.
2. All acceptance gates pass.
3. Package-level tests pass in CI and local.
4. Updated docs validated from clean environment.
5. Production readiness sign-off with one-page release note.

---

## 14. Optional Deliverables (If Time Allows)

1. Replace file-backed conversation store with pluggable Redis adapter.
2. Add OpenTelemetry exporter for traces.
3. Add synthetic monitor hitting `/health` and `/performance` every minute.

---

## 15. Execution Checklist

1. Implement Workstream A and commit.
2. Implement Workstream B and commit.
3. Implement Workstream C and commit.
4. Implement Workstream D and commit.
5. Implement Workstream E and commit.
6. Implement Workstream F and commit.
7. Run full validation.
8. Start Workstream G only after A-F pass.

