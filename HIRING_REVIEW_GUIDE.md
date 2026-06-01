# EnterpriseHub Hiring Review Guide

EnterpriseHub is best reviewed as an AI backend engineering portfolio project: a real estate lead-qualification platform with FastAPI APIs, multi-bot orchestration, LLM caching, compliance checks, CRM sync, evals, and observability-oriented infrastructure.

This guide is intentionally short. It points reviewers to the strongest evidence first and separates proven artifacts from roadmap items.

## 60-Second Read

- **Problem:** real estate teams need fast, compliant lead qualification across inbound SMS/web leads.
- **Backend system:** FastAPI services coordinate lead, buyer, and seller bot workflows with CRM persistence and webhook handling.
- **AI system:** prompt registry, golden dataset, deterministic checks, LLM-as-judge harness, adversarial tests, and nightly eval workflow.
- **Production judgment:** ADRs, security scanning, structured logging, health checks, Docker/Compose deploy paths, Redis/Postgres cache design, and CI gates.
- **Current caveat:** throughput, uptime, and dollar savings should not be quoted without fresh generated evidence. A first live L1 cache snapshot now exists (90.8% L1 hit rate on a synthetic workload, Redis L2 not exercised; `benchmarks/results/cache_live_2026-05-27.json`); treat it as L1-only, not production.

## 5-Minute Review Path

1. Read the top of [README.md](README.md) through "For Hiring Managers".
2. Read [CASE_STUDY.md](CASE_STUDY.md), especially "Honest Production Metrics".
3. Inspect the eval surface in [evals/README.md](evals/README.md), [evals/judge.py](evals/judge.py), and [tests/test_eval_harness.py](tests/test_eval_harness.py).
4. Skim the architecture decisions in [docs/adr](docs/adr) (now 12, including ADR-0011 on mesh scaffold status and ADR-0012 on ML-engine stubs).
5. Read the hiring audit findings in [docs/HIRING_CONVERSION_AUDIT.md](docs/HIRING_CONVERSION_AUDIT.md).
6. Use [docs/HIRING_ROADMAP_2026-05-23.md](docs/HIRING_ROADMAP_2026-05-23.md) for the current ranked work plan.

## 30-Minute Technical Review Path

1. **LLM orchestration:** [ghl_real_estate_ai/services/claude_orchestrator.py](ghl_real_estate_ai/services/claude_orchestrator.py)
2. **Agent routing and governance:** [ghl_real_estate_ai/services/agent_mesh_coordinator.py](ghl_real_estate_ai/services/agent_mesh_coordinator.py)
3. **Webhook and CRM boundary:** [ghl_real_estate_ai/api/routes/webhook.py](ghl_real_estate_ai/api/routes/webhook.py)
4. **Compliance pipeline:** [ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py](ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py)
5. **Eval harness:** [evals/judge.py](evals/judge.py), [evals/golden_dataset.json](evals/golden_dataset.json), [evals/baseline.json](evals/baseline.json)

## Local Verification Commands

These commands were audited on May 23, 2026. Start with the compact smoke path, then use the individual commands if you want to inspect a specific proof area.

```bash
make reviewer-smoke
python3 -m pytest --collect-only --override-ini='addopts=' -q
```

`make reviewer-smoke` runs lint, format check, compile check, eval harness, health routes, webhook signatures, Claude orchestrator tests, and SQL-safety tests.

## Known Review Caveats

- Full-repo mypy is still too broad for a reviewer path; create a bounded type-check command for the flagship API/services before making type-safety claims.
- `pytest --collect-only --override-ini='addopts=' -q` currently collects 7,665 tests on 2026-05-23; public test-count claims should use this reproducible count.
- FastAPI route metadata is uneven: an AST scan found 707 route decorators, 431 without `response_model`, and 682 without explicit `status_code`.
- Full-suite collection still emits noisy import-time logs; use `make reviewer-smoke` for the first verification pass.
- The strongest proof is not "big repo size"; it is the combination of orchestration, compliance, eval discipline, and honest production tradeoffs.
