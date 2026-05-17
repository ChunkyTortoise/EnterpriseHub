# EnterpriseHub Reviewer Scorecard

Last updated: 2026-05-17

This scorecard is the current reviewer-facing proof table. It intentionally separates measured local checks, synthetic evidence, and known limitations.

## Current Verification

| Area | Evidence | Result | Evidence type |
|---|---|---:|---|
| Secret hygiene | `python3 scripts/ci/secret_scan.py` | Repo-wide tracked text scan added | Local gate |
| Artifact hygiene | `python3 scripts/ci/tracked_artifact_policy.py` | Passing before this change | Local gate |
| Quiet reviewer gate | `make verify-reviewer` | 167 targeted tests passed; 7,740 tests collected | Local gate |
| Fast public gate | `make verify-public` | 7,740 tests collected on 2026-05-17 | Local gate |
| Focused evidence tests | `make verify-focused` | 162 passed on 2026-05-17 | Local gate |
| Portal route metadata | `python3 scripts/ci/route_metadata_audit.py portal_api --fail-on-missing` | 21 routes, 0 missing `response_model`, 0 missing `status_code` | Static audit |
| Reviewer route ratchet | `make route-metadata-reviewer` | Covers `portal_api`, auth, health, webhook, and bot-management routes | Static audit |
| Cache benchmark | `python -m benchmarks.bench_cache` | Synthetic latency simulation only | Synthetic benchmark |
| Demo/API smoke | `tests/smoke/test_reviewer_smoke.py` | Portal health and Streamlit entrypoint compile smoke | Local test |

## Known Limitations

- Full `ghl_real_estate_ai/api/routes/` route metadata remains incomplete. The current ratchet covers the highest-signal reviewer routes and can expand without false claims.
- Broad `except Exception` usage still exists in legacy service and route modules. Prioritize webhook, CRM, billing, cache, and external API boundaries before analytics-only modules.
- Historical docs remain in the repo for provenance. Reviewer-facing claims should come from `README.md`, `HIRING_REVIEW_GUIDE.md`, `docs/CLAIM_LEDGER.md`, this scorecard, and `docs/evidence/`.
- Performance documents before this scorecard should be treated as dated. Fresh numbers must state whether they are mocked, synthetic, local, staging, or production.

## Next Ratchet Targets

- Expand the route ratchet one router group at a time beyond auth, health, webhook, and bot management.
- Replace broad dictionary response models with narrower Pydantic schemas on the newly ratcheted routes.
- Repair and document webhook signature tests so webhook security can become a headline proof point.
