# EnterpriseHub Hiring Review Guide

EnterpriseHub is best reviewed as an AI backend engineering portfolio project: a real estate lead-qualification platform with FastAPI APIs, multi-bot orchestration, LLM caching, compliance checks, CRM sync, evals, and observability-oriented infrastructure.

This guide is intentionally short. It points reviewers to the strongest evidence first and separates proven artifacts from roadmap items. For a directory-by-directory orientation, see [docs/repo-map.md](docs/repo-map.md).

## 60-Second Read

- **Problem:** real estate teams need fast, compliant lead qualification across inbound SMS/web leads.
- **Backend system:** FastAPI services coordinate lead, buyer, and seller bot workflows with CRM persistence and webhook handling.
- **AI system:** prompt registry, golden dataset, deterministic checks, LLM-as-judge harness, adversarial tests, and nightly eval workflow.
- **Production judgment:** ADRs, security scanning, structured logging, health checks, Docker/Compose deploy paths, Redis/Postgres cache design, and CI gates.
- **Current caveat:** public claims must stay tied to [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md), and secret handling follows [docs/security/env-and-secret-policy.md](docs/security/env-and-secret-policy.md). Some older benchmark, handoff, delivery, and project-status materials preserve historical or marketing language, so prefer the current README, repo map, evidence docs, and claim ledger.

## 5-Minute Review Path

1. Read the top of [README.md](README.md) through "For Hiring Managers".
2. Open [docs/repo-map.md](docs/repo-map.md) to see which directories are core, supporting, generated, or historical.
3. Check [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md) for how metrics are labeled.
4. Skim the architecture decisions in [docs/adr](docs/adr).
5. Inspect the demo evidence in [docs/evidence/demo-evidence-pack.md](docs/evidence/demo-evidence-pack.md) and secret policy in [docs/security/env-and-secret-policy.md](docs/security/env-and-secret-policy.md), then skim the eval surface in [evals/README.md](evals/README.md), [evals/judge.py](evals/judge.py), and [tests/test_eval_harness.py](tests/test_eval_harness.py).

## 15-Minute Technical Review Path

1. **Case study:** [CASE_STUDY.md](CASE_STUDY.md)
2. **Compliance pipeline:** [ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py](ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py)
3. **Agent routing:** [ghl_real_estate_ai/services/agent_mesh_coordinator.py](ghl_real_estate_ai/services/agent_mesh_coordinator.py)
4. **Eval harness:** [evals/judge.py](evals/judge.py), [evals/golden_dataset.json](evals/golden_dataset.json), [evals/baseline.json](evals/baseline.json)
5. **Demo evidence:** [docs/evidence/demo-evidence-pack.md](docs/evidence/demo-evidence-pack.md)
6. **Secret policy:** [docs/security/env-and-secret-policy.md](docs/security/env-and-secret-policy.md)
7. **Current maintainer audit:** [docs/audits/repo-maintenance/2026-05-06/maintainer-audit.md](docs/audits/repo-maintenance/2026-05-06/maintainer-audit.md)

## 45-Minute Technical Review Path

1. **LLM orchestration:** [ghl_real_estate_ai/services/claude_orchestrator.py](ghl_real_estate_ai/services/claude_orchestrator.py)
2. **Agent routing and governance:** [ghl_real_estate_ai/services/agent_mesh_coordinator.py](ghl_real_estate_ai/services/agent_mesh_coordinator.py)
3. **Webhook and CRM boundary:** [ghl_real_estate_ai/api/routes/webhook.py](ghl_real_estate_ai/api/routes/webhook.py)
4. **Compliance pipeline:** [ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py](ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py)
5. **Eval harness:** [evals/judge.py](evals/judge.py), [evals/golden_dataset.json](evals/golden_dataset.json), [evals/baseline.json](evals/baseline.json)
6. **Repo hygiene and open risks:** [docs/audits/repo-maintenance/2026-05-06/maintainer-audit.md](docs/audits/repo-maintenance/2026-05-06/maintainer-audit.md)

## Local Verification Commands

These commands are the intended reviewer path as of May 6, 2026.

```bash
make verify-public
make verify-focused
pytest --collect-only --override-ini='addopts='
pytest tests/test_eval_harness.py --override-ini='addopts=' -q
pytest tests/unit/test_claude_orchestrator.py tests/unit/test_sql_safety.py --override-ini='addopts=' -q
```

## Known Review Caveats

- `pytest --collect-only --override-ini='addopts=' -q` collected 7,669 tests on May 6, 2026; public test-count claims should use dated command output.
- Full-repo mypy is intentionally not the fast reviewer gate yet; the repo still has broad suppressions that need staged tightening.
- FastAPI route metadata is uneven: an AST scan found 702 route decorators, 427 without `response_model`, and 677 without explicit `status_code`.
- Some security/health targeted tests have historically failed locally, indicating either test drift, route drift, or environment assumptions that need tightening.
- Secret-shaped tracked files and historical generated artifacts are tracked as owner-decision items in the maintainer audit.
- Historical docs under `docs/project_status/`, `docs/handoffs/`, `docs/delivery/`, and `docs/reports/` are preserved for timeline/provenance and should not be read as current verification.
- The strongest proof is not "big repo size"; it is the combination of orchestration, compliance, eval discipline, and honest production tradeoffs.
