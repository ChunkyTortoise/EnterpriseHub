# Receipts

One page of reproducible numbers behind the headline claims, with each number's
evidence type stated. Three labels are used throughout the repo:

- **measured**: produced by running code in this repo; artifact and repro command listed
- **modeled**: derived from a stated cost or performance model, not observed in production
- **case-study**: reported from the client engagement; raw CRM data is not public

## Cache performance

| Claim | Value | Evidence | Caveats |
|---|---|---|---|
| L1 hit rate | 90.8% (1,816/2,000 ops) | measured: [`benchmarks/results/cache_live_2026-05-27.json`](../benchmarks/results/cache_live_2026-05-27.json) | Synthetic workload (70% hot keys, seed 42), not production traffic. L2/Redis was not configured for this run, so L2 stats are absent. In-memory throughput number (1.19M ops/s) measures Python dict paths, not network round trips. |
| L2 / L3 hit rates | 62% / 31% on the demo telemetry page | modeled | Design targets from the tiered-cache architecture, labeled "modeled" wherever shown. |

Reproduce: `python benchmarks/cache_benchmark.py --seed 42` (see the JSON's `workload` block for parameters).

## Token cost model

| Claim | Value | Evidence | Caveats |
|---|---|---|---|
| Token reduction per 100-query workload | 93K to 7.8K tokens | modeled: [`BENCHMARKS.md`](../BENCHMARKS.md) | Projection from cache hit-rate targets and prompt sizes; not a live billing measurement. |

## Evals

| Claim | Value | Evidence | Caveats |
|---|---|---|---|
| Golden dataset | 50 hand-curated cases | measured: [`evals/golden_dataset.json`](../evals/golden_dataset.json) | Distribution: 15 seller, 10 buyer, 10 lead intake, 10 edge cases, 5 compliance. |
| Baseline rubric scores | correctness 0.90, tone 0.90, safety 1.00, compliance 0.95 | measured: [`evals/baseline.json`](../evals/baseline.json) | LLM-judge scoring (rubrics in `evals/rubrics.py`); judge prompts are in-repo and auditable. |
| Nightly regression gate | active | measured: [`.github/workflows/nightly-eval.yml`](../.github/workflows/nightly-eval.yml) | Fails the run and opens an issue when pass rate drops more than 10% below baseline; publishes `evals/badge.json` either way. |

Reproduce: `pytest tests/test_eval_harness.py -v --override-ini="addopts="`.

## Mesh and agents

| Claim | Value | Evidence | Caveats |
|---|---|---|---|
| Agent registry | 7 configured agents | measured: [`benchmarks/results/mesh_registry_2026-05-27.json`](../benchmarks/results/mesh_registry_2026-05-27.json) | Agents register at runtime via `mesh_agent_registry.py`; a cold process starts with zero registered. |
| Cost governance | $50/hr budget gate, $100/hr shutdown | measured in code: `services/agent_mesh_coordinator.py` | Throttling response to the $50 gate is log-only scaffolding, documented in [ADR-0011](adr/0011-mesh-coordinator-scaffold-status.md). The $100 shutdown path is implemented. |

## Production engagement

| Claim | Value | Evidence | Caveats |
|---|---|---|---|
| Production run | ~3 months, 500+ CRM leads | case-study: [`CASE_STUDY.md`](../CASE_STUDY.md) | Client CRM export is not public; treat as reported, not auditable. |
