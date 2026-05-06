# FastAPI Route Metadata Baseline

Generated: 2026-05-06

Scope: `portal_api` only. This is the small reviewer-facing FastAPI surface selected for the first metadata audit pass.

Command:

```bash
python3 scripts/ci/route_metadata_audit.py portal_api
```

## Summary

| Metric | Count |
|---|---:|
| Routes scanned | 21 |
| Missing `response_model` | 0 |
| Missing explicit `status_code` | 0 |

## Interpretation

`portal_api` is now in better shape than the repo-wide historical baseline because every scanned route declares both a `response_model` and an explicit `status_code`. This keeps FastAPI defaults visible in code and makes generated OpenAPI docs and reviewer scans clearer.

Do not fix all routes across the monorepo in one pass. The next cleanup should expand this audit to the highest-signal `ghl_real_estate_ai/api/routes/` modules and address one bounded router group at a time.

## Current Route Detail

| File | Line | Method | Route | response_model | status_code |
|---|---:|---|---|---|---|
| `portal_api/app.py` | 60 | GET | `/health` | yes | yes |
| `portal_api/routers/accelerator_v2.py` | 27 | POST | `/intake/diagnose` | yes | yes |
| `portal_api/routers/accelerator_v2.py` | 43 | POST | `/workflows/bootstrap` | yes | yes |
| `portal_api/routers/accelerator_v2.py` | 68 | POST | `/reports/proof-pack` | yes | yes |
| `portal_api/routers/accelerator_v2.py` | 106 | GET | `/reports/{engagement_id}` | yes | yes |
| `portal_api/routers/admin.py` | 9 | POST | `/admin/reset` | yes | yes |
| `portal_api/routers/admin.py` | 21 | POST | `/reset` | yes | yes |
| `portal_api/routers/admin.py` | 33 | POST | `/system/reset` | yes | yes |
| `portal_api/routers/admin.py` | 49 | GET | `/admin/state` | yes | yes |
| `portal_api/routers/admin.py` | 50 | GET | `/state` | yes | yes |
| `portal_api/routers/admin.py` | 51 | GET | `/system/state` | yes | yes |
| `portal_api/routers/admin.py` | 56 | GET | `/admin/state/details` | yes | yes |
| `portal_api/routers/admin.py` | 57 | GET | `/state/details` | yes | yes |
| `portal_api/routers/admin.py` | 58 | GET | `/system/state/details` | yes | yes |
| `portal_api/routers/ghl.py` | 16 | POST | `/sync` | yes | yes |
| `portal_api/routers/ghl.py` | 44 | GET | `/fields` | yes | yes |
| `portal_api/routers/portal.py` | 9 | GET | `/deck` | yes | yes |
| `portal_api/routers/portal.py` | 15 | POST | `/swipe` | yes | yes |
| `portal_api/routers/root.py` | 10 | GET | `/` | yes | yes |
| `portal_api/routers/vapi.py` | 25 | POST | `/check-availability` | yes | yes |
| `portal_api/routers/vapi.py` | 36 | POST | `/book-tour` | yes | yes |
