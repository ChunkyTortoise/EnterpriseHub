# Portal API Advanced Demo Enhancement Spec

Date: 2026-02-10  
Repository: `/Users/cave/Documents/New project/enterprisehub`  
Owner: Candidate  
Audience: Hiring manager + technical interview panel

## 1) Objective

Elevate the current Portal API interview demo from "reliable and deterministic" to "senior-level production thinking" by adding three targeted proof points:

1. Tenant isolation proof (zero cross-tenant leakage)
2. Performance metrics with pass/fail SLO gates
3. Multi-language detection demo readiness

This spec is intentionally built on top of the already-completed hardening baseline from 2026-02-10 (`7/7` deterministic checks, request-id propagation, auth/idempotency/error envelope, OpenAPI snapshot lock).

## 2) Why This Increases Hiring Signal

Interview concern -> Demo proof:

1. Multi-tenant safety -> deterministic isolation test with explicit zero-leak assertions
2. Production operability -> repeatable latency table + threshold gates, not anecdotal speed claims
3. Multilingual roadmap -> working detection endpoint + test-backed examples (`en`, `es`, `he`)

The key value is not extra features alone. It is demonstrating disciplined engineering under product constraints.

## 3) Scope

In scope:

1. Extend Portal API surface and scripts to include tenant-isolation verification, performance validation, and language detection
2. Add/extend tests and OpenAPI snapshot locks for all new contracts
3. Upgrade demo script from `7/7` to `10/10` deterministic checks
4. Update evidence + README talk track for interview usage

Out of scope:

1. Full production i18n pipeline (translation memory, locale packs, fallback chains)
2. Full multi-tenant persistent storage architecture (RLS/schema-per-tenant/shared DB migration)
3. Full APM/metrics backend deployment (Prometheus/Grafana/Datadog)

## 4) Baseline Assumptions (Locked)

Current assets already exist and remain the base:

1. `scripts/portal_api_interview_demo.sh` (`7/7`)
2. `scripts/portal_api_latency_sanity.py`
3. `scripts/portal_api_validate.sh`
4. Request-id middleware and stable error envelope in `portal_api/app.py` and `portal_api/models.py`
5. Portal API test suite and OpenAPI snapshot lock under `portal_api/tests/`

## 5) Architecture Additions

## A) Tenant Context

Canonical tenant source:

1. Header `X-Tenant-ID` (preferred)
2. Body field `location_id` fallback where applicable
3. Default `tenant_default` for backward compatibility

Rules:

1. All mutating operations must record the effective tenant id
2. Read operations must be tenant-scoped by effective tenant id
3. State endpoints must support tenant-scoped views without breaking current default behavior

## B) Performance Validation

Add deterministic measurement harness that:

1. Executes repeated calls against selected endpoints
2. Reports `avg`, `p95`, `max` latency
3. Applies configurable thresholds and exits non-zero on breach
4. Produces interview-friendly output table + pass/fail line items

## C) Language Detection

Add lightweight deterministic detector surface for demo:

1. Endpoint: `POST /language/detect`
2. Input text -> language code + confidence + detection strategy label
3. Initial supported languages: English (`en`), Spanish (`es`), Hebrew (`he`)
4. Deterministic rule-based baseline, structured for later ML-backed replacement

## 6) Data Model and API Contract Changes

## A) Models (`portal_api/models.py`)

Add:

1. `TenantContext` model:
   - `tenant_id: str`
   - `source: Literal["header", "payload", "default"]`
2. `LanguageDetectRequest` model:
   - `text: str` (min length 1)
3. `LanguageDetectResponse` model:
   - `language: Literal["en", "es", "he", "unknown"]`
   - `confidence: float`
   - `strategy: str`
4. Optional tenant fields in detailed snapshots where useful for traceability

## B) New/Updated Routes

1. `GET /portal/deck`
   - Accept optional tenant header and scope seen interactions by tenant
2. `POST /portal/swipe`
   - Persist interaction with effective tenant
3. `GET /system/state`
4. `GET /system/state/details`
   - Return tenant-scoped counters by default; optional aggregate mode via query flag is allowed but not required for this phase
5. `POST /language/detect` (new)

OpenAPI lock updates required via snapshot refresh script.

## 7) Workstreams

## Workstream 1: Tenant Isolation Proof

Target files:

1. `/Users/cave/Documents/New project/enterprisehub/portal_api/dependencies.py`
2. `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/portal.py`
3. `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/admin.py`
4. `/Users/cave/Documents/New project/enterprisehub/modules/inventory_manager.py`
5. `/Users/cave/Documents/New project/enterprisehub/modules/ghl_sync.py`
6. `/Users/cave/Documents/New project/enterprisehub/modules/appointment_manager.py`
7. `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`

Implementation tasks:

1. Add dependency helper to resolve effective tenant context
2. Partition in-memory interactions/actions/bookings by tenant id
3. Keep lead/property seed data shared unless explicit tenant seed is needed
4. Ensure deck filtering only considers interactions for the same tenant
5. Ensure state counters/details are tenant-scoped
6. Add tests to prove no cross-tenant data leakage

Required test cases:

1. Swipe in `tenant_a`, fetch deck in `tenant_b` -> liked property still visible
2. `tenant_a` state counters unchanged by `tenant_b` activity
3. Default tenant behavior remains backward compatible when no header is provided

Acceptance criteria:

1. Zero cross-tenant interaction leakage in deterministic tests
2. Existing non-tenant flows continue passing

## Workstream 2: Performance Metrics With Thresholds

Target files:

1. `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_latency_sanity.py` (extend)  
or  
2. `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_performance_demo.py` (new)
3. `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_interview_demo.sh`
4. `/Users/cave/Documents/New project/enterprisehub/README.md`
5. `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_EVIDENCE_FEB10_2026.md`

Implementation tasks:

1. Add endpoint probes for:
   - `/health`
   - `/portal/deck?contact_id=lead_001`
   - `/portal/swipe` (with safe deterministic payload + optional reset cadence)
2. Add configurable thresholds:
   - health p95 < 50ms
   - deck p95 < 200ms
   - swipe p95 < 100ms
3. Print per-endpoint table and pass/fail lines
4. Return non-zero exit code if any threshold fails

Acceptance criteria:

1. Script output is deterministic and interview-readable
2. Demo script can gate success on performance checks

## Workstream 3: Multi-Language Detection Demo

Target files:

1. `/Users/cave/Documents/New project/enterprisehub/portal_api/models.py`
2. `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/language.py` (new)
3. `/Users/cave/Documents/New project/enterprisehub/portal_api/app.py`
4. `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`
5. `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_interview_demo.sh`
6. `/Users/cave/Documents/New project/enterprisehub/README.md`

Implementation tasks:

1. Implement deterministic detector helper:
   - Hebrew by Unicode range
   - Spanish via accent + stopword heuristic
   - English via ASCII + stopword heuristic
2. Return confidence score with bounded values (`0.0-1.0`)
3. Add endpoint and OpenAPI response models
4. Add tests for known fixtures:
   - English sentence -> `en`
   - Spanish sentence -> `es`
   - Hebrew sentence -> `he`

Acceptance criteria:

1. All three fixture languages detect correctly in tests and demo
2. Unknown/ambiguous text returns `unknown` with lower confidence

## Workstream 4: Demo Script Upgrade (10/10)

Target file:

1. `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_interview_demo.sh`

Upgrade steps:

1. Keep current `1/7` through `7/7` unchanged
2. Add `8/10` tenant isolation proof block:
   - reset
   - swipe as `tenant_a`
   - verify `tenant_b` deck still contains liked property
   - verify tenant-specific state counts
3. Add `9/10` performance validation block:
   - invoke latency script with thresholds
   - assert pass
4. Add `10/10` language detection block:
   - call `/language/detect` for English/Spanish/Hebrew fixtures
   - assert expected language + minimum confidence

Expected interview-facing output shape:

1. `[STEP] 8/10 tenant isolation proof`
2. `[PASS] tenant_a and tenant_b are fully isolated`
3. `[STEP] 9/10 performance validation`
4. `[PASS] p95 thresholds met`
5. `[STEP] 10/10 multi-language detection`
6. `[PASS] multilingual readiness verified (en/es/he)`
7. `[PASS] interview demo flow completed (10/10)`

## Workstream 5: Documentation + Evidence Refresh

Target files:

1. `/Users/cave/Documents/New project/enterprisehub/README.md`
2. `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_EVIDENCE_FEB10_2026.md`
3. `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_COMPLETION_SPEC_FEB10_2026.md`

Tasks:

1. Update README section to show advanced demo mode and optional flags
2. Add measured latency table and tenant isolation evidence snippets
3. Add updated pass count and any new commit hashes
4. Record exact command bundle used for validation

## 8) Validation Bundle (Required)

Run from repo root:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh

ruff check main.py portal_api modules scripts/portal_api_client_example.py scripts/portal_api_latency_sanity.py

python3 -m py_compile \
  main.py \
  portal_api/app.py \
  portal_api/dependencies.py \
  portal_api/models.py \
  portal_api/routers/root.py \
  portal_api/routers/vapi.py \
  portal_api/routers/portal.py \
  portal_api/routers/ghl.py \
  portal_api/routers/admin.py \
  portal_api/routers/language.py \
  modules/inventory_manager.py \
  modules/ghl_sync.py \
  modules/appointment_manager.py \
  modules/voice_trigger.py \
  scripts/portal_api_client_example.py \
  scripts/portal_api_latency_sanity.py

pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests

bash scripts/portal_api_interview_demo.sh
```

If OpenAPI changed intentionally:

```bash
python3 scripts/refresh_portal_openapi_snapshot.py
pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests
```

## 9) Completion Criteria

All must be true:

1. Demo script passes `10/10` deterministic checks
2. Tenant isolation proof test(s) pass with explicit zero-leak assertions
3. Performance script passes configured p95 thresholds
4. Language detection endpoint contract + tests pass (`en`, `es`, `he`)
5. OpenAPI snapshot remains green after intentional updates
6. README and evidence docs reflect the new advanced flow

## 10) Risk Register + Mitigations

Risk: tenant scoping breaks existing default demo flow  
Mitigation: default to `tenant_default`; preserve current paths and payload compatibility

Risk: latency variance causes flaky pass/fail in noisy environments  
Mitigation: warm-up runs + configurable thresholds + documented local baseline

Risk: heuristic language detector misclassifies edge inputs  
Mitigation: keep detector scope explicit (`en/es/he demo baseline`) and return `unknown` for ambiguous text

Risk: scope creep before interview  
Mitigation: lock to three workstreams; reject unrelated feature requests until demo evidence is complete

## 11) Suggested Execution Order (Fastest Path)

1. Implement tenant context and isolation tests
2. Implement language detection endpoint and tests
3. Extend performance script with threshold gates
4. Upgrade demo script to `10/10`
5. Refresh OpenAPI snapshot and docs/evidence
6. Run full validation bundle and freeze evidence

## 12) Timebox

Estimated implementation time:

1. Core implementation + tests: 45-60 minutes
2. Docs/evidence/final polish: 20-30 minutes
3. Total: 65-90 minutes for interview-ready confidence

