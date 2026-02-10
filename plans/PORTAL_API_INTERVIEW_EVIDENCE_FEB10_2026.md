# Portal API Interview Evidence Bundle

Date: 2026-02-10
Repository: `/Users/cave/Documents/New project/enterprisehub`

## 1) Baseline + Final Hardening Commits

Locked baselines:

- Phase 1 closure baseline: `f7109b8d`
- Phase 2 CI/OpenAPI baseline: `12d2863a`
- Interview finalization baseline: `3b87d1b8`

Hardening commits executed in this run:

- `516bbbba` - deterministic validate/demo scripts + workflow test isolation
- `8497529f` - request-id middleware, stable error envelope, demo auth guard, full OpenAPI snapshot lock, typed client, P2 helper scripts
- `54715c82` - cross-version OpenAPI snapshot normalization (`additionalProperties: true` normalization)

## 2) CI Verification (GitHub Actions)

Workflow: `portal-api-phase1`

- Initial post-hardening run (failed, then fixed): `21860545437`
- Final green run: `21860614337`
- Final green URL: `https://github.com/ChunkyTortoise/EnterpriseHub/actions/runs/21860614337`
- Final green job URL: `https://github.com/ChunkyTortoise/EnterpriseHub/actions/runs/21860614337/job/63088473433`

Final green run timing (UTC):

- Started: `2026-02-10T10:10:47Z`
- Completed: `2026-02-10T10:11:06Z`
- Duration: ~`19s`

## 3) Validation Bundle Results

Executed from repo root.

Shell syntax:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh
```

Lint/compile/tests:

```bash
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
```

Runtime demo:

```bash
bash scripts/portal_api_interview_demo.sh
```

Observed outcomes:

- `ruff`: `All checks passed!`
- `py_compile`: no errors
- `pytest`: `30 passed`
- `portal_api_interview_demo.sh`: all `7/7` steps passed with deterministic status/body assertions

Note on spec command adaptation:

- The spec’s `ruff check ... scripts/*.sh` form is not supported by Ruff (it parses shell scripts as Python). Validation uses `bash -n` for shell scripts plus Ruff for Python sources.

## 4) Contract Hardening Evidence

- `POST /ghl/sync` `500` now returns `ApiErrorResponse` with stable `code/message/request_id` and no raw internal exception leakage.
- Mutating routes (`/portal/swipe`, `/vapi/tools/book-tour`, `/ghl/sync`, `/system/reset`) include env-gated demo auth and explicit `401` OpenAPI contracts.
- `X-Request-ID` middleware behavior is test-locked:
  - propagates inbound request id
  - generates request id when absent
  - returns header on success and error paths
- Full OpenAPI snapshot lock in place:
  - snapshot: `portal_api/tests/openapi_snapshot.json`
  - test: `portal_api/tests/test_portal_api_openapi_snapshot.py`
  - refresh: `scripts/refresh_portal_openapi_snapshot.py`

## 5) Typed Client + Optional P2 Proof

Typed client smoke proof:

```bash
python3 scripts/portal_api_client_example.py
```

Observed sample:

- `swipe` status `200`, `request_id_sent == request_id_received`
- `state-details` status `200`, `request_id_sent == request_id_received`

Optional preflight:

```bash
bash scripts/portal_api_preflight.sh
```

Observed sample: all checks passed.

Optional repeated-run latency sanity (`10` samples):

| endpoint | runs | avg_ms | p95_ms | max_ms |
|---|---:|---:|---:|---:|
| health | 10 | 1.43 | 11.19 | 11.19 |
| state_details | 10 | 0.48 | 0.88 | 0.88 |

## 6) Interview Talk Track Anchors

1. Reliability: one-command validate (`scripts/portal_api_validate.sh`) + one-command deterministic demo (`scripts/portal_api_interview_demo.sh`).
2. Contract safety: route-level OpenAPI assertions plus full-surface snapshot lock.
3. Operational traceability: `X-Request-ID` end-to-end in responses and error envelope.
4. Security posture: env-gated API key guard for mutating actions without breaking default demo flow.
5. Tradeoff clarity: lightweight, deterministic controls for interview scope, with explicit production-next-paths.
