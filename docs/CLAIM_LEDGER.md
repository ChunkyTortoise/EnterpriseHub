# EnterpriseHub Claim Ledger

Last audited: 2026-05-06

Use this ledger to keep public claims credible. Recommended language should replace or constrain README, case-study, benchmark, and interview claims until stronger evidence is added.

| Public claim | Current evidence | Confidence | Recommended wording |
|---|---|---:|---|
| EnterpriseHub is a real estate AI lead qualification platform. | README, CASE_STUDY, `ghl_real_estate_ai/`, bot and CRM routes. | Strong | "Real estate AI lead-qualification platform with Lead, Buyer, and Seller bot workflows." |
| Built with FastAPI, PostgreSQL, Redis, Claude, GoHighLevel, Streamlit, Docker, and GitHub Actions. | Root README, requirements, Docker files, CI workflows, service modules. | Strong | Keep as stack claim. |
| Production run lasted about 3 months and processed 500+ leads. | CASE_STUDY states this, but repo artifact does not include raw CRM export. | Credible but needs context | "Case-study-reported production run: about 3 months and 500+ CRM leads; raw client CRM data is not public." |
| 50 golden eval cases cover seller qualification, buyer scheduling, lead intake, edge cases, and compliance. | `evals/golden_dataset.json`, `evals/README.md`. | Strong | Keep. |
| Evals include deterministic checks and LLM-as-judge scoring. | `evals/judge.py`, `tests/test_eval_harness.py`; targeted test passed 14/14 locally. | Strong | Keep, and include command output in proof docs. |
| Prompt versions are tracked. | `PROMPT_CHANGELOG.md`. | Strong | "Prompt versions and rationale are tracked in `PROMPT_CHANGELOG.md`." |
| Nightly eval regression is wired in CI. | `.github/workflows/nightly-eval.yml` exists and compares JSON report to `evals/baseline.json`. | Strong | "Nightly eval workflow is configured; latest public run status should be checked in GitHub Actions." |
| CI runs lint, unit, integration, security, type-check, eval, and build jobs. | `.github/workflows/ci.yml`. | Strong | Keep, but distinguish advisory `continue-on-error` jobs. |
| Security scanning runs bandit, pip-audit, and SQL-injection grep. | `.github/workflows/security-scan.yml`, `.github/workflows/ci.yml`. | Strong | Keep, but note pip-audit is advisory where configured. |
| 3-tier cache uses in-memory, Redis, and Postgres layers. | README, ADR-0001, cache/orchestrator service modules. | Strong | Keep architectural claim. |
| 87-89% cache hit/token reduction was measured live. | README and benchmark report claim this; CASE_STUDY explicitly corrects some numbers as design targets/projections. | Weak | "Designed and benchmarked a 3-tier cache targeting roughly 88% hit rate; live hit-rate evidence should be regenerated before quoting as measured." |
| Dollar savings such as $240K annual savings or $38K yearly LLM savings are production-measured. | Older README and benchmark language contained quantified claims; current README and benchmark report now frame these as projections/models. | Weak | "Projected savings based on workflow assumptions; do not present as measured production savings without raw billing/CRM evidence." |
| Historical larger test-count claims are collectible/passing. | Local `pytest --collect-only --override-ini='addopts=' -q` collected 7,669 tests on 2026-05-06. Targeted eval/orchestrator tests pass; some targeted health/security suites historically needed repair. | Credible but needs context | "Large test suite: 7,669 tests collected locally on 2026-05-06; publish the exact command and date with any count." |
| The Streamlit demo is publicly accessible. | README links to Streamlit Cloud, but viewer access may require allowlist depending on deployment settings. Local/API demo credentials are synthetic demo-auth values covered by `docs/security/env-and-secret-policy.md`. | Credible but needs context | "Streamlit Cloud demo exists; access status is documented in `docs/evidence/demo-evidence-pack.md` and may require allowlist." |
| Reviewer checks require production secrets. | `make verify-public` and `make verify-focused` are documented as secret-free reviewer checks, and `scripts/ci/tracked_artifact_policy.py` guards against tracked secret-shaped artifacts. | Strong | "Reviewer checks do not require production secrets; deeper local integrations use private env vars or untracked `.env` files." |
| All systems validated and operational. | Older `BENCHMARK_VALIDATION_REPORT.md` wording said this; the report now explicitly marks itself as a historical artifact, and current local lint/format/security/health checks fail. | Remove | Replace with a dated, command-backed verification table. |
| FastAPI endpoints follow production standards. | AST scan found 702 route decorators, 427 missing `response_model`, 677 missing explicit `status_code`. | Credible but needs context | "Core routes are implemented, but endpoint metadata needs a focused cleanup pass to meet portfolio standards." |
| Webhook authentication is production-grade. | README/security docs and webhook modules indicate serious design; targeted `tests/security/test_webhook_signatures.py` failed 17/36 locally due to route/constant drift and 404s. | Credible but needs context | "Webhook signature verification is implemented, but the public test suite needs repair before this should be a headline claim." |
| Health checks are fully production verified. | Health modules exist; targeted `tests/api/test_health_routes.py` failed 7/14 locally with DB/env assumptions and 500s. | Credible but needs context | "Health endpoints exist; local test fixtures and fail-closed behavior need tightening." |
| ADRs document non-obvious decisions. | `docs/adr/0001` through `0010`; README currently says 10. CASE_STUDY says 13. | Strong with correction | "10 ADRs currently in `docs/adr`." |

## Claim Policy

- **Measured:** backed by raw command output, CI run, production export, or generated report with reproducible input.
- **Synthetic benchmark:** backed by a script and environment description, not described as production behavior.
- **Design target:** architecture goal or model assumption; never present as observed behavior.
- **Projection:** business or cost estimate; include formula and assumptions.
