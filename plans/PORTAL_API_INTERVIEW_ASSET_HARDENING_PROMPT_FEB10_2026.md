# Prompt: Execute Portal API Interview Asset Hardening

You are continuing work in:
`/Users/cave/Documents/New project/enterprisehub`

Read and execute this spec first:
`/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_ASSET_HARDENING_SPEC_FEB10_2026.md`

## Mission

Complete the hardening plan for interview readiness end-to-end with deterministic scripts, stronger contracts, improved CI signal quality, and updated evidence artifacts.

## Hard constraints

1. Do not touch unrelated existing local work:
   - `streamlit_cloud/app.py`
   - `tests/conftest.py`
   - `tests/test_app_structure.py`
   - `enterprise-ui/`
   - `plans/CLIENT_SHOWCASE_*`
2. Stage only files explicitly changed for this hardening effort.
3. Keep runtime behavior backward compatible unless the spec explicitly requires a contract change.
4. Keep edits concise and production-minded; avoid unnecessary refactors.

## Execution order

1. Implement P0 workstreams completely.
2. Implement P1 workstreams.
3. Implement P2 only if time remains and risk is low.
4. After each workstream, run relevant local checks.
5. At the end, run full validation bundle from spec section 6.
6. Commit in logical chunks with clear messages.
7. Push to `origin/main`.
8. Verify GitHub Actions `portal-api-phase1` workflow is green.
9. Update evidence files with final commit hashes, workflow run IDs/URLs, and timings.
10. Create and push tag: `portal-api-interview-ready-2026-02-10`.

## Expected output in final report

Provide:

1. What was implemented per workstream (P0/P1/P2).
2. Exact files changed.
3. Validation command results (ruff, compile, pytest, demo script).
4. Final commit list and tag.
5. GitHub Actions run URL and status.
6. Residual risks or deferred items.

## Quality bar

- Deterministic execution, no ambiguous “manual” steps.
- Test-backed API contract guarantees.
- Interviewer can reproduce everything from scripts and docs only.
