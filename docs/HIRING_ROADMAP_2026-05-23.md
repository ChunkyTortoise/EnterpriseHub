# EnterpriseHub Hiring Roadmap

Date: 2026-05-23
Target lane: AI Backend / LLMOps

## Executive Summary

EnterpriseHub is strongest as a proof-heavy AI backend portfolio repo: FastAPI services, GoHighLevel webhooks, multi-bot orchestration, compliance post-processing, LLM caching, evals, and CI/security infrastructure. The highest-impact work is not another feature; it is keeping the proof path reproducible and preventing older docs from making claims stronger than the evidence.

Current score: 78/100 hiring readiness.

## Verified Proof

| Area | Current result | Evidence type |
|---|---:|---|
| Test collection | 7,665 collected | Measured local command |
| Eval harness | 14/14 passed | Measured local command |
| Health routes | 14/14 passed | Measured local command |
| Webhook signatures | 36/36 passed | Measured local command |
| Orchestrator + SQL safety | 123/123 passed | Measured local command |
| Cache model | 88.1% modeled hit rate on 10,000-op simulation | Synthetic benchmark |
| Golden eval data | 50 cases across 5 categories | Repository artifact |

Primary command:

```bash
make reviewer-smoke
```

Full collection check:

```bash
python3 -m pytest --collect-only --override-ini='addopts=' -q
```

## Ranked Roadmap

### P0: Keep The Reviewer Path Green

- Keep `make reviewer-smoke` passing and link it from README/HIRING_REVIEW_GUIDE.
- Keep README, CASE_STUDY, BENCHMARK_VALIDATION_REPORT, CLAIM_LEDGER, and HIRING_CONVERSION_AUDIT synchronized whenever proof changes.
- Triage the latest GitHub Security Scan before presenting the security badge as green; dependency and Bandit failures should be handled or clearly documented.
- Fix or quarantine `tests/security/test_jorge_webhook_security.py` before using it as security proof.

### P1: Strengthen AI Backend Signal

- Bring the selected reviewer API path to repo standards first: webhook routes, health routes, and `portal_api` routes should keep `response_model`, explicit `status_code`, typed dependencies, and focused tests.
- Add a bounded type-check target for flagship backend modules instead of full-repo mypy.
- Refresh ADR-0007 and ADR-0009 so compliance/webhook architecture docs match current router-level dependencies and disclosure behavior.
- Generate a fresh eval scorecard whenever the golden dataset changes; start from `docs/EVAL_SCORECARD_2026-05-23.md`.

### P2: Evidence And Portfolio Polish

- Publish only labeled benchmark artifacts: synthetic cache model, live cache counter run, or projection.
- Run the Next.js visual audit after frontend dependencies are installed; inspect `/` and `/portal` at desktop and mobile widths.
- Refresh screenshots only after the frontend compiles and the portal shows real or plausible property imagery.
- Reduce doc sprawl in the first reviewer path: README -> HIRING_REVIEW_GUIDE -> CASE_STUDY -> evals -> ADRs.

## Do Not Claim Yet

- Do not claim live cache hit rate, token savings, uptime, throughput, or billing savings until generated artifacts are committed.
- Do not claim the LLM judge is human-validated; current proof is eval harness discipline, not calibrated judge validity.
- Do not claim all FastAPI routes meet production metadata standards; the May 23 scan still found 707 route decorators with 431 missing `response_model` and 682 missing explicit `status_code`.
- Do not claim green security posture from the badge alone; check current GitHub Security Scan status.
- Do not claim live registered agents beyond the configured roster unless a runtime registry snapshot is generated; use "7 configured agents (~10 with auto-discovery)" for now.

## Interview Talking Points

- Why deterministic compliance checks run before any LLM call.
- How the handoff layer prevents circular bot transfers and tracks outcomes.
- Why cache hit-rate targets must be separated from live counter measurements.
- How the golden dataset and regression baseline make prompt changes reviewable.
- Why the repo now has a small reviewer-smoke path instead of asking reviewers to run the whole monorepo.

