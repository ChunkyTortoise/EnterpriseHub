# Portal API Interview Asset Hardening Spec

Date: 2026-02-10
Repository: `/Users/cave/Documents/New project/enterprisehub`
Audience: Candidate + technical interview panel

## 1) Objective

Harden the existing Portal API interview asset so it presents as deterministic, production-minded, and low-risk under live demo conditions. The goal is not feature expansion; the goal is reliability, contract stability, and clear operator ergonomics.

## 2) Current Baseline (Locked)

- Phase 1 closure: `f7109b8d`
- Phase 2 CI/OpenAPI lock: `12d2863a`
- Interview readiness completion: `5bc2455a`
- Workflow dependency fix: `6bd4d7a7`
- Interview artifact finalization: `3b87d1b8`
- Latest known green workflow: `portal-api-phase1` run `21859818555` (2026-02-10)

Current strengths already in place:

- Critical OpenAPI refs are contract-tested.
- `/ghl/sync` includes explicit `500` OpenAPI contract.
- README has a deterministic 5-minute demo flow.
- Targeted lint/compile/tests are green locally and in CI.

## 3) Improvement Targets Before Interview

## P0 (Must Complete)

1. Add single-command validation and demo scripts to eliminate manual command drift.
2. Add immutable release tag and evidence update so interview proof is frozen.
3. Remove or explicitly isolate CI noise affecting confidence (root test config coupling / warning annotation ambiguity).

## P1 (Strongly Recommended)

1. Add stable API error envelope (no raw internal exception strings in responses).
2. Add request-id middleware and response header propagation.
3. Add OpenAPI snapshot lock for whole `portal_api` surface.
4. Add minimal demo auth guard for mutating routes (toggleable by env) and document tradeoff.
5. Add typed client example and smoke proof.

## P2 (Optional, if time)

1. Add lightweight repeated-run latency sanity script and include results in evidence.
2. Add preflight script to check environment readiness before demo.

## 4) Scope and Non-Goals

In scope:

- Portal API module and related scripts/docs/workflow for interview-grade reliability.

Out of scope:

- Full production auth system (JWT/RBAC), persistent DB rewrite, distributed rate limiting, external provider hardening, full observability stack.

## 5) Workstreams

## Workstream A: Operator Ergonomics (Scripts)

### Target files

- `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_validate.sh` (new)
- `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_interview_demo.sh` (new)
- `/Users/cave/Documents/New project/enterprisehub/README.md`

### Tasks

1. Create `portal_api_validate.sh` with strict mode (`set -euo pipefail`) that runs:
   - `ruff check main.py portal_api modules`
   - compile bundle
   - `pytest -q -o addopts='' portal_api/tests/test_portal_api.py`
2. Create `portal_api_interview_demo.sh` with deterministic sequence:
   - reset
   - deck fetch
   - valid swipe
   - book tour
   - aggregate + detailed state
   - invalid swipe (`save`) 422 proof
3. Add clear stdout markers (`[STEP]`, `[PASS]`, `[FAIL]`) and non-zero exit on failed expectations.
4. Update README to reference scripts as preferred interview flow.

### Acceptance criteria

- Both scripts run successfully from repo root on macOS/Linux shell.
- Demo script fails fast if any expected status/body condition fails.
- README references script-based flow instead of manual copy/paste only.

## Workstream B: CI Signal Clarity

### Target files

- `/Users/cave/Documents/New project/enterprisehub/.github/workflows/portal-api-phase1.yml`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py` (if needed)

### Tasks

1. Decouple Portal API tests from root-level `conftest.py` side effects:
   - prefer `pytest --confcutdir=portal_api/tests ...` for workflow and script, or
   - provide a local `portal_api/tests/conftest.py` and ensure no root fixture import requirement.
2. Re-run workflow and verify job output is clean and understandable.
3. If a non-blocking GitHub checkout annotation persists, document root cause and benign impact in evidence file.

### Acceptance criteria

- `portal-api-phase1` run passes after changes.
- No test import failures from unrelated root fixtures.
- CI output is interview-defensible with a concise explanation.

## Workstream C: Error Envelope + Request ID

### Target files

- `/Users/cave/Documents/New project/enterprisehub/portal_api/models.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/app.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`

### Tasks

1. Introduce stable error model(s), for example:
   - `ApiErrorDetail { code, message, request_id }`
   - `ApiErrorResponse { error: ApiErrorDetail }`
2. Add request-id middleware:
   - accept inbound `X-Request-ID` if present, else generate UUID
   - attach request id to request state
   - return `X-Request-ID` response header
3. Replace raw exception detail leakage on `/ghl/sync` with stable message + code.
4. Add tests:
   - response includes `X-Request-ID`
   - failure shape conforms to envelope
   - OpenAPI `500` binds to new error model.

### Acceptance criteria

- No internal exception strings are returned for unexpected failures.
- Every response includes traceable request id header.
- Error contracts remain OpenAPI-locked.

## Workstream D: OpenAPI Snapshot Lock

### Target files

- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/openapi_snapshot.json` (new)
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api_openapi_snapshot.py` (new)
- `/Users/cave/Documents/New project/enterprisehub/scripts/refresh_portal_openapi_snapshot.py` (new)

### Tasks

1. Add deterministic OpenAPI snapshot file (sorted keys, stable formatting).
2. Add snapshot assertion test comparing runtime schema vs tracked snapshot.
3. Add refresh script for intentional schema changes.
4. Document snapshot update procedure in README.

### Acceptance criteria

- Unintended OpenAPI drift fails tests.
- Intentional changes are easy to update via one refresh command.

## Workstream E: Minimal Demo Auth Guard

### Target files

- `/Users/cave/Documents/New project/enterprisehub/portal_api/dependencies.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/portal.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/vapi.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/admin.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`
- `/Users/cave/Documents/New project/enterprisehub/README.md`

### Tasks

1. Add env-gated demo auth dependency for mutating endpoints (e.g., `POST` routes):
   - if `PORTAL_API_DEMO_KEY` unset, auth check disabled (backward compatible demo mode)
   - if set, require `X-API-Key` header match
2. Add explicit OpenAPI `401` response contracts where applied.
3. Add tests for enabled/disabled modes.
4. Document exact usage in README.

### Acceptance criteria

- Safe demo default remains available.
- Interview can show “security-minded extension path” without major complexity.

## Workstream F: Typed Client Example + Evidence Finalization

### Target files

- `/Users/cave/Documents/New project/enterprisehub/scripts/portal_api_client_example.py` (new)
- `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_EVIDENCE_FEB10_2026.md`
- `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_COMPLETION_SPEC_FEB10_2026.md`

### Tasks

1. Add small typed Python client example invoking:
   - `/portal/swipe`
   - `/system/state/details`
2. Include request-id echo and auth header support.
3. Update evidence file with:
   - latest commit hashes
   - current green workflow URL
   - script outputs
   - optional latency sample table
4. Add immutable tag:
   - `portal-api-interview-ready-2026-02-10`

### Acceptance criteria

- Interviewer can see both API and client-consumer viewpoint.
- Evidence file is self-contained and reproducible.
- Tag exists locally and on remote.

## 6) Final Validation Bundle

Run from repo root:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh

ruff check main.py portal_api modules scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh

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
  modules/inventory_manager.py \
  modules/ghl_sync.py \
  modules/appointment_manager.py \
  modules/voice_trigger.py \
  scripts/refresh_portal_openapi_snapshot.py \
  scripts/portal_api_client_example.py

pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests

bash scripts/portal_api_interview_demo.sh
```

CI verification:

- Push branch/commit.
- Confirm latest `portal-api-phase1` run is green in GitHub Actions.

## 7) Interview Narrative Upgrade (Talk Track)

1. Reliability: one-command validate + one-command demo.
2. Contract safety: route-level assertions + full OpenAPI snapshot lock.
3. Operational visibility: request-id end-to-end.
4. Security posture: optional API key guard for mutable actions.
5. Tradeoff clarity: intentionally lightweight controls for demo scope.

## 8) Risks and Mitigations

- Risk: over-hardening introduces regressions before interview.
  - Mitigation: P0 first, small commits, run full bundle after each workstream.
- Risk: snapshot introduces brittle failures from nondeterministic fields.
  - Mitigation: canonical serialization and field normalization in refresh script.
- Risk: auth guard breaks current demo flow.
  - Mitigation: env-gated default disabled mode + explicit tests.
- Risk: unrelated repo churn pollutes commits.
  - Mitigation: stage explicit file lists only.

## 9) Deliverables

1. Updated code and tests for all approved workstreams.
2. Two executable scripts (`validate`, `demo`).
3. OpenAPI snapshot + refresh tooling.
4. Updated README and evidence files.
5. Immutable release tag.
6. Green GitHub workflow run link.

## 10) Definition of Done

All are true:

1. P0 completed and verified locally + remotely.
2. Selected P1 items implemented with tests and docs.
3. Demo runs successfully via one script in under 5 minutes.
4. Validation runs successfully via one script.
5. Evidence doc contains exact commit hashes, run IDs, and commands.
6. Interview-ready tag is created and pushed.
