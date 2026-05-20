# EnterpriseHub Hiring Review Guide

EnterpriseHub is best reviewed as an AI backend engineering portfolio project: a real estate lead-qualification platform with FastAPI APIs, multi-bot orchestration, LLM caching, compliance checks, CRM sync, evals, and observability-oriented infrastructure.

This guide is intentionally short. It points reviewers to the strongest evidence first and separates proven artifacts from roadmap items.

## 60-Second Read

- **Problem:** real estate teams need fast, compliant lead qualification across inbound SMS/web leads.
- **Backend system:** FastAPI services coordinate lead, buyer, and seller bot workflows with CRM persistence and webhook handling.
- **AI system:** prompt registry, golden dataset, deterministic checks, LLM-as-judge harness, adversarial tests, and nightly eval workflow.
- **Production judgment:** ADRs, security scanning, structured logging, health checks, Docker/Compose deploy paths, Redis/Postgres cache design, and CI gates.
- **Current caveat:** public claims need stricter provenance. Some README/benchmark/case-study metrics mix measured results, design targets, and projections.

## 5-Minute Review Path

1. Read the top of [README.md](README.md) through "For Hiring Managers".
2. Read [CASE_STUDY.md](CASE_STUDY.md), especially "Honest Production Metrics".
3. Inspect the eval surface in [evals/README.md](evals/README.md), [evals/judge.py](evals/judge.py), and [tests/test_eval_harness.py](tests/test_eval_harness.py).
4. Skim the architecture decisions in [docs/adr](docs/adr).
5. Read the hiring audit findings in [docs/HIRING_CONVERSION_AUDIT.md](docs/HIRING_CONVERSION_AUDIT.md).

## 30-Minute Technical Review Path

1. **LLM orchestration:** [ghl_real_estate_ai/services/claude_orchestrator.py](ghl_real_estate_ai/services/claude_orchestrator.py)
2. **Agent routing and governance:** [ghl_real_estate_ai/services/agent_mesh_coordinator.py](ghl_real_estate_ai/services/agent_mesh_coordinator.py)
3. **Webhook and CRM boundary:** [ghl_real_estate_ai/api/routes/webhook.py](ghl_real_estate_ai/api/routes/webhook.py)
4. **Compliance pipeline:** [ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py](ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py)
5. **Eval harness:** [evals/judge.py](evals/judge.py), [evals/golden_dataset.json](evals/golden_dataset.json), [evals/baseline.json](evals/baseline.json)

## Local Verification Commands

These commands were audited on April 29, 2026. Some fail today; that is useful signal for the next development phase.

```bash
ruff check .
ruff format --check .
mypy ghl_real_estate_ai src utils advanced_rag_system
pytest --collect-only --override-ini='addopts='
pytest tests/test_eval_harness.py --override-ini='addopts=' -q
pytest tests/unit/test_claude_orchestrator.py tests/unit/test_sql_safety.py --override-ini='addopts=' -q
pytest tests/api/test_health_routes.py --override-ini='addopts=' -q
pytest tests/security/test_webhook_signatures.py --override-ini='addopts=' -q
```

## Known Review Caveats

- Global lint and format checks currently fail because of parse errors and formatting drift, concentrated heavily in `advanced_rag_system`.
- Full-repo mypy did not complete locally during the audit; create a bounded type-check command for the flagship API/services.
- `pytest --collect-only --override-ini='addopts='` currently collects 7,665 tests on 2026-05-19; public test-count claims should use the current reproducible count.
- FastAPI route metadata is uneven: an AST scan found 702 route decorators, 427 without `response_model`, and 677 without explicit `status_code`.
- Some security/health targeted tests fail locally, indicating either test drift, route drift, or environment assumptions that need tightening.
- The strongest proof is not "big repo size"; it is the combination of orchestration, compliance, eval discipline, and honest production tradeoffs.
