# EnterpriseHub Maintainer Audit

Generated: 2026-05-06

## Executive Summary

EnterpriseHub has strong portfolio substance: a large AI/backend codebase, eval assets, ADRs, CI workflows, security intent, and a case-study-backed product story. The main credibility risk is presentation hygiene. Reviewers could previously encounter stale test counts, tracked local artifacts, secret-shaped files, old generated wording, permissive lint/type gates, and a broken compile gate before they reached the best engineering evidence.

This pass creates a maintainer agent, fixes the fast compile gate, refreshes the reviewer guide, adds a repo map and demo evidence pack, reconciles current public test-count language, adds focused reviewer checks, prunes tracked local/generated artifacts, and applies a tracked-artifact policy for secret-shaped files and dumps.

## Scorecard

| Area | Score | Notes |
|---|---:|---|
| Presentation | 7/10 | README has strong hiring positioning, but the repo needed a map and current verification language. |
| Correctness | 7/10 | Test collection, compile check, and focused reviewer tests now pass; broader suites still need staged work. |
| Security | 8/10 | Secret-shaped artifacts and dumps were removed or converted to templates; future regressions are covered by a policy gate. |
| Testability | 8/10 | 7,669 tests collected on 2026-05-06; `make verify-focused` passes 162 targeted evidence tests. |
| Maintainability | 5/10 | Broad mypy ignores, many broad exceptions, large files, and historical packages need staged cleanup. |
| Evidence Quality | 8/10 | Claim ledger, demo evidence pack, eval assets, and current dated command output now anchor public claims. |
| Hiring Readiness | 8/10 | Reviewer path, repo map, demo limits, fast/focused verification, and secret policy are now visible; historical docs remain the next cleanup frontier. |

## Verification Snapshot

| Command | Result |
|---|---|
| `git status --short --branch` | Dirty before implementation: existing `AGENTS.md`, `README.md`, `.kilo/`, `AGENT_MEMORY_STRATEGY.md`, `uv.lock`. |
| `ruff check . --statistics --exit-zero` | No output under current Ruff config during reconnaissance. |
| `python3 scripts/ci/compile_check.py` | Failed before implementation: missing `ghl_real_estate_ai/services/learning/test_behavior_tracking.py`; passes after replacing the stale target. |
| `pytest --collect-only --override-ini='addopts=' -q` | 7,669 tests collected in 13.47s on 2026-05-06. |
| `make verify-public` | Passes after implementation: Ruff, compile check, and test collection. |
| `make verify-focused` | Passes after second wave: 162 passed, 1 pytest-asyncio deprecation warning. |
| `python3 scripts/ci/tracked_artifact_policy.py` | Passes after secret-shaped artifact cleanup. |
| `python3 scripts/ci/route_metadata_audit.py portal_api` | Passes after `portal_api` cleanup: 21 routes, 0 missing `response_model`, 0 missing explicit `status_code`. |
| Redacted secret-pattern scan | Reports test placeholders and secret-shaped fixtures; owner-decision items remain below. |
| `git ls-files .playwright-mcp advanced_rag_system/venv312 .debug_chroma data/embeddings/chroma_db` | 79 tracked generated/local artifact files before cleanup. |

## Safe Cleanup Now

- Remove tracked `.playwright-mcp/` browser screenshots and crawl artifacts.
- Remove tracked `advanced_rag_system/venv312/` virtualenv shims.
- Remove tracked `.debug_chroma/` and `data/embeddings/chroma_db/` local vector-store binaries.
- Remove tracked `data/.jwt_secret` and PostgreSQL dumps under `infrastructure/backups/*.dump`.
- Convert useful deploy/production secret examples to `.template` files with obvious placeholders.
- Update legacy `AuthService` so test collection and local imports no longer regenerate `data/.jwt_secret`.
- Keep `tests/coverage/README.md` and `tests/coverage/test_coverage_validation.py`; despite the directory name, these are source docs/tests, not generated coverage output.
- Update `.gitignore` so browser traces, debug vector stores, generated embeddings, database dumps, model binaries, product bundles, and local report files do not re-enter git accidentally.

## Needs Owner Decision

- `content/gumroad/zips/*.zip` and `models/ensemble_model.joblib`: bundled/generated artifacts may be legitimate business assets, but they add noise and should be intentionally justified or moved to release storage.
- Historical docs under `docs/project_status/` still contain older client-specific and overconfident wording. Keep as historical context or archive behind a clearer index.

## Prioritized Findings

### [P0] Broken public compile gate
- **File**: `scripts/ci/compile_check.py`
- **Evidence**: `python3 scripts/ci/compile_check.py` failed with `missing: ghl_real_estate_ai/services/learning/test_behavior_tracking.py`.
- **Impact**: A reviewer running the advertised fast gate sees an immediate failure unrelated to product behavior.
- **Recommended fix**: Replace the stale missing path with an existing production module and keep targets focused on reviewer-relevant code.
- **Verification**: `python3 scripts/ci/compile_check.py`

### [P1] Stale public test-count claims
- **File**: `README.md`, `HIRING_REVIEW_GUIDE.md`
- **Evidence**: Current collection is 7,669 tests on 2026-05-06; README previously referenced an older count from 2026-04-29.
- **Impact**: Stale numbers make good evidence feel self-certified or careless.
- **Recommended fix**: Use the latest dated count and state the exact command.
- **Verification**: `pytest --collect-only --override-ini='addopts=' -q`

### [P1] Tracked local/generated artifacts in reviewer surface
- **File**: `.playwright-mcp/`, `advanced_rag_system/venv312/`, `.debug_chroma/`, `data/embeddings/chroma_db/`
- **Evidence**: 79 tracked files across browser crawl artifacts, virtualenv shims, and vector-store binaries.
- **Impact**: These files signal weak repo hygiene and distract from real source/evidence.
- **Recommended fix**: Remove from git and strengthen `.gitignore`.
- **Verification**: `git ls-files | rg 'venv312|\\.playwright-mcp|\\.debug_chroma|data/embeddings/chroma_db'`

### [P1] Reviewers need a curated path through a large monorepo
- **File**: `HIRING_REVIEW_GUIDE.md`, `docs/repo-map.md`
- **Evidence**: Root contains multiple apps/packages, reports, content assets, infra, data, and local agent tooling.
- **Impact**: Without a map, scale reads as clutter rather than breadth.
- **Recommended fix**: Provide 5-minute, 15-minute, and 45-minute review paths plus a top-level repo map.
- **Verification**: Manual review of docs links and paths.

### [P1] Demo status needed an explicit evidence boundary
- **File**: `README.md`, `HIRING_REVIEW_GUIDE.md`, `docs/evidence/demo-evidence-pack.md`
- **Evidence**: README linked a Streamlit demo and credentials, but access status and demo limits were not centralized.
- **Impact**: A reviewer could interpret demo credentials as production secrets or assume public access without checking deployment settings.
- **Recommended fix**: Document what the demo proves, what it does not prove, current access caveats, curated screenshots, and refresh checklist.
- **Verification**: Manual review of `docs/evidence/demo-evidence-pack.md`.

### [P1] Secret-shaped tracked files needed explicit policy
- **File**: `data/.jwt_secret`, `deploy/*.env`, `configs/production/secrets.production.yml`, `infrastructure/backups/*.dump`
- **Evidence**: `git ls-files` reported tracked secret-shaped files and PostgreSQL dumps.
- **Impact**: Even sanitized placeholders can trip scanners or make reviewers nervous if not clearly intentional.
- **Recommended fix**: Remove ambiguous secret/dump artifacts, convert useful examples to `.template` files, document secret setup, and add a policy gate.
- **Verification**: `python3 scripts/ci/tracked_artifact_policy.py`

### [P1] Public reviewer checks needed an artifact policy gate
- **File**: `Makefile`, `scripts/ci/tracked_artifact_policy.py`
- **Evidence**: `.gitignore` already blocked `.jwt_secret` and `*.dump`, but tracked files could still regress without a gate.
- **Impact**: A future accidental commit could reintroduce local browser traces, virtualenvs, vector stores, or secret-shaped files.
- **Recommended fix**: Add `artifact-policy-check` and include it in `make verify-public`.
- **Verification**: `make verify-public`

### [P1] Test collection regenerated a tracked JWT secret file
- **File**: `ghl_real_estate_ai/services/auth_service.py`, `tests/services/test_auth_service_secret_policy.py`
- **Evidence**: `pytest --collect-only` recreated `data/.jwt_secret` through the legacy `AuthService` import path.
- **Impact**: A green reviewer command could still leave a secret-shaped tracked file modified in the working tree.
- **Recommended fix**: Read `JWT_SECRET_KEY` from the environment when present and otherwise use a process-local development secret without writing to disk.
- **Verification**: `pytest tests/services/test_auth_service_secret_policy.py --override-ini='addopts=' -q` and `make verify-public`

### [P2] Ruff/mypy settings are too permissive to sell as strict hygiene
- **File**: `pyproject.toml`
- **Evidence**: Global mypy overrides ignore major packages; Ruff ignores many `F` and `E` classes and ignores tests broadly.
- **Impact**: "lint clean" currently means "clean under a forgiving gate." That is acceptable short term only if honestly labeled.
- **Recommended fix**: Keep `make verify-public` fast, use `make verify-focused` for curated evidence tests, then tighten one package at a time.
- **Verification**: `make verify-public` and `make verify-focused`

### [P2] Response pipeline test expectations had drifted from the documented 7-stage pipeline
- **File**: `tests/test_response_pipeline.py`
- **Evidence**: `make verify-focused` initially failed because two tests expected 6 stages when `create_default_pipeline()` and README document 7 stages including `conversation_repair`.
- **Impact**: A targeted reviewer command failed on stale test expectations, undermining otherwise strong compliance-pipeline evidence.
- **Recommended fix**: Update the stage log/order assertions to match the current 7-stage default pipeline.
- **Verification**: `make verify-focused`

### [P2] AI-code hygiene debt is visible
- **File**: repository-wide
- **Evidence**: Recon scans found old AI-authorship wording, many client-specific `Jorge` references, broad `except Exception`, and generated/historical docs.
- **Impact**: Some references are valid case-study evidence; accidental ones make the repo feel generated.
- **Recommended fix**: Maintain an allowlist for intentional client/model references and clean public-facing accidental references first.
- **Verification**: Run the reviewer-facing stale-marker scan documented in the test plan.

## Issue-Ready Backlog

1. P0: Finish fast public gate: ensure `make verify-public` passes on a clean checkout.
2. P1: Refresh live demo screenshots and record current Streamlit Cloud allowlist/public-access status in `docs/evidence/demo-evidence-pack.md`.
3. P1: Convert accidental public AI-authorship or old branding references into neutral technical language; keep intentional case-study references.
4. P2: Add stricter Ruff/mypy gates for `portal_api`, `evals`, and selected `ghl_real_estate_ai/services/jorge` modules.
5. P2: Triage broad exception handling in API/webhook/security/CRM boundaries first.
6. P2: Expand the FastAPI route metadata audit to one high-signal `ghl_real_estate_ai/api/routes/` group at a time.
7. P3: Move historical reports and old generated docs into a clearly labeled archive or index them from `docs/repo-map.md`.

## Maintainer Rule

Every new public claim must be added to `docs/CLAIM_LEDGER.md` before it is promoted into `README.md`, proposal material, or hiring-facing docs.
