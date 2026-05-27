# EnterpriseHub Claim Ledger

Last audited: 2026-05-23

Use this ledger to keep public claims credible. Recommended language should replace or constrain README, case-study, benchmark, and interview claims until stronger evidence is added.

| Public claim | Current evidence | Confidence | Recommended wording |
|---|---|---:|---|
| EnterpriseHub is a real estate AI lead qualification platform. | README, CASE_STUDY, `ghl_real_estate_ai/`, bot and CRM routes. | Strong | "Real estate AI lead-qualification platform with Lead, Buyer, and Seller bot workflows." |
| Built with FastAPI, PostgreSQL, Redis, Claude, GoHighLevel, Streamlit, Docker, and GitHub Actions. | Root README, requirements, Docker files, CI workflows, service modules. | Strong | Keep as stack claim. |
| Production run lasted about 3 months and processed 500+ leads. | CASE_STUDY states this, but repo artifact does not include raw CRM export. | Credible but needs context | "Case-study-reported production run: about 3 months and 500+ CRM leads; raw client CRM data is not public." |
| 50 golden eval cases cover seller qualification, buyer scheduling, lead intake, edge cases, and compliance. | `evals/golden_dataset.json`, `evals/README.md`. | Strong | Keep. |
| Evals include deterministic checks and LLM-as-judge scoring. | `evals/judge.py`, `tests/test_eval_harness.py`; targeted test passed 14/14 locally on 2026-05-23. | Strong | Keep, and include command output in proof docs. |
| Prompt versions are tracked. | `PROMPT_CHANGELOG.md`. | Strong | "Prompt versions and rationale are tracked in `PROMPT_CHANGELOG.md`." |
| Nightly eval regression is wired in CI. | `.github/workflows/nightly-eval.yml` exists and compares JSON report to `evals/baseline.json`. | Strong | "Nightly eval workflow is configured; latest public run status should be checked in GitHub Actions." |
| CI runs lint, unit, integration, security, type-check, eval, and build jobs. | `.github/workflows/ci.yml`. | Strong | Keep, but distinguish advisory `continue-on-error` jobs. |
| Security scanning runs bandit, pip-audit, and SQL-injection grep. | `.github/workflows/security-scan.yml`, `.github/workflows/ci.yml`. | Strong | Keep, but note pip-audit is advisory where configured. |
| 3-tier cache uses in-memory, Redis, and Postgres layers. | README, ADR-0001, cache/orchestrator service modules. | Strong | Keep architectural claim. |
| 87-89% cache hit/token reduction was measured live. | README and benchmark report claim this; CASE_STUDY explicitly corrects some numbers as design targets/projections. | Weak | "Designed and benchmarked a 3-tier cache targeting roughly 88% hit rate; live hit-rate evidence should be regenerated before quoting as measured." |
| Dollar savings such as $240K annual savings or $38K yearly LLM savings are production-measured. | Older README and benchmark language contained quantified claims; current README and benchmark report now frame these as projections/models. | Weak | "Projected savings based on workflow assumptions; do not present as measured production savings without raw billing/CRM evidence." |
| 8,212 tests are collectible/passing. | Local `pytest --collect-only --override-ini='addopts=' -q` collected 7,665 tests on 2026-05-23. Targeted eval, health, webhook, orchestrator, and SQL-safety suites pass locally. | Credible but needs context | "Large test suite: 7,665 tests collected locally on 2026-05-23; reviewer smoke path passes targeted eval, health, webhook, orchestrator, and SQL-safety suites." |
| All systems validated and operational. | Older `BENCHMARK_VALIDATION_REPORT.md` wording said this; the report now explicitly marks itself as a historical artifact. Current proof should be command-specific, not blanket system certification. | Remove | Replace with dated, command-backed verification tables and `make reviewer-smoke`. |
| FastAPI endpoints follow production standards. | AST scan on 2026-05-23 found 707 route decorators, 431 missing `response_model`, and 682 missing explicit `status_code`. | Credible but needs context | "The reviewer path has targeted proof, but broader endpoint metadata needs a focused cleanup pass to meet portfolio standards." |
| Webhook authentication is production-grade. | README/security docs and webhook modules indicate serious design; `pytest tests/security/test_webhook_signatures.py --override-ini='addopts=' -q` passed 36/36 locally on 2026-05-23. | Strong targeted proof | "Webhook signature verification is implemented and covered by a passing targeted test suite; deployed status should be checked in CI/live environment." |
| Health checks are production-ready. | Health modules exist; `pytest tests/api/test_health_routes.py --override-ini='addopts=' -q` passed 14/14 locally on 2026-05-23. | Strong targeted proof | "Health endpoints are covered by passing local tests; do not claim uptime/SLO performance without deployed telemetry." |
| ADRs document non-obvious decisions. | `docs/adr/0001` through `0010`; README currently says 10. CASE_STUDY says 13. | Strong with correction | "10 ADRs currently in `docs/adr`." |

## Claim Policy

- **Measured:** backed by raw command output, CI run, production export, or generated report with reproducible input.
- **Synthetic benchmark:** backed by a script and environment description, not described as production behavior.
- **Design target:** architecture goal or model assumption; never present as observed behavior.
- **Projection:** business or cost estimate; include formula and assumptions.
