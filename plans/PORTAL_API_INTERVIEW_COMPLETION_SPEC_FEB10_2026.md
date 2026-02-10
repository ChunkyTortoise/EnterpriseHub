# Portal API Interview Completion Spec

Date: 2026-02-10
Repository: `/Users/cave/Documents/New project/enterprisehub`
Owner: Candidate
Primary audience: Interview panel + technical reviewer

## 1) Objective

Complete interview hardening for the Portal API with deterministic operator flows, stronger contracts, cleaner CI signal, and evidence artifacts that are reproducible.

## 2) Final Execution Summary

P0 (must complete):

- [x] Deterministic scripts added:
  - `scripts/portal_api_validate.sh`
  - `scripts/portal_api_interview_demo.sh`
- [x] Workflow test signal hardened:
  - `.github/workflows/portal-api-phase1.yml` uses `--confcutdir=portal_api/tests`
  - local `portal_api/tests/conftest.py` isolates import path from root test fixtures
- [x] CI result verified green for latest hardening head:
  - run `21860614337` (success)

P1 (strongly recommended):

- [x] Stable API error envelope models added (`ApiErrorDetail`, `ApiErrorResponse`)
- [x] Request-id middleware added (`X-Request-ID` propagate/generate)
- [x] `/ghl/sync` 500 leakage removed; returns stable envelope
- [x] Demo auth guard added for mutating routes, env-gated by `PORTAL_API_DEMO_KEY`
- [x] OpenAPI snapshot lock implemented (snapshot + assertion + refresh script)
- [x] Typed Python client example added (`scripts/portal_api_client_example.py`)
- [x] README updated to script-first flow + auth/snapshot/client usage

P2 (optional):

- [x] Preflight helper added (`scripts/portal_api_preflight.sh`)
- [x] Repeated-run latency sanity helper added (`scripts/portal_api_latency_sanity.py`)

## 3) Commits Produced

- `516bbbba` - deterministic validate/demo scripts + workflow isolation
- `8497529f` - core hardening (request-id, auth guard, envelope, snapshot lock, client, docs, optional scripts)
- `54715c82` - cross-version snapshot normalization fix

## 4) CI Outcome

Workflow: `portal-api-phase1`

- Failing run during hardening (fixed): `21860545437`
- Final passing run: `21860614337`
- URL: `https://github.com/ChunkyTortoise/EnterpriseHub/actions/runs/21860614337`

## 5) Final Validation Bundle (Executed)

From repo root:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh

ruff check main.py portal_api modules scripts/refresh_portal_openapi_snapshot.py scripts/portal_api_client_example.py scripts/portal_api_latency_sanity.py

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

Observed summary:

- Ruff: pass
- Compile: pass
- Pytest: `30 passed`
- Demo script: pass (`7/7` deterministic checks)

## 6) Scope Guard Confirmation

Unrelated local work was not edited/staged in hardening commits:

- `streamlit_cloud/app.py`
- `tests/conftest.py`
- `tests/test_app_structure.py`
- `enterprise-ui/`
- `plans/CLIENT_SHOWCASE_*`

## 7) Release Tag

Release tag target: `portal-api-interview-ready-2026-02-10`

(Managed after evidence update + final push.)
