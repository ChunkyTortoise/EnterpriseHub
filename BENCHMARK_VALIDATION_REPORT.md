# Benchmark Validation Report

**Original report date:** February 11, 2026  
**Credibility audit update:** May 23, 2026  
**Current status:** historical benchmark artifact, not a blanket production-certification document

This report used to state that all performance metrics were validated and operational. That wording is too broad for a hiring-facing hero repo. The current source of truth is:

- [docs/CLAIM_LEDGER.md](docs/CLAIM_LEDGER.md) for public claim wording
- [BENCHMARKS.md](BENCHMARKS.md) for synthetic benchmark methodology
- [docs/HIRING_CONVERSION_AUDIT.md](docs/HIRING_CONVERSION_AUDIT.md) for current verification results

## Current Evidence Summary

| Claim area | Current evidence | Public wording guidance |
|---|---|---|
| Test surface | `pytest --collect-only --override-ini='addopts=' -q` collected 7,665 tests on May 23, 2026. | Quote the current collectible count, not older 8,212/7,721 counts. |
| Eval harness | `pytest tests/test_eval_harness.py --override-ini='addopts=' -q` passed 14/14 on May 23, 2026. | Strong claim: deterministic checks and LLM-as-judge harness exist and are tested. |
| Orchestrator/sql safety | `pytest tests/unit/test_claude_orchestrator.py tests/unit/test_sql_safety.py --override-ini='addopts=' -q` passed 123/123 on May 23, 2026. | Strong targeted backend/security proof. |
| Cache hit rate | `BENCHMARKS.md` models a 60% / 20% / 8% L1/L2/L3 distribution. | Present as synthetic benchmark/design target unless fresh live counters are published. |
| Token savings | `BENCHMARKS.md` models a 93K to 7.8K token reduction for a synthetic workload. | Present as projection/model, not measured billing savings. |
| Latency/throughput | Older P50/P95/P99 values in this report are not backed by a committed reproducible run. k6 scripts are in `benchmarks/`; `benchmarks/results/2026-W17/README.md` says "results pending." | Do not quote any latency/throughput number until a JSON result is committed to `benchmarks/results/`. |
| Health routes | `pytest tests/api/test_health_routes.py --override-ini='addopts=' -q` passed 14/14 on May 23, 2026. | Good reviewer-smoke proof; still avoid broader uptime claims without deployed telemetry. |
| Webhook security tests | `pytest tests/security/test_webhook_signatures.py --override-ini='addopts=' -q` passed 36/36 on May 23, 2026. | Strong targeted webhook-auth proof. |
| Lint/format/compile | `ruff check .`, `ruff format --check .`, and `python3 scripts/ci/compile_check.py` are part of `make reviewer-smoke`. | Treat `make reviewer-smoke` as the hiring-review gate. |

## Synthetic Benchmark Methodology

The cache, orchestration, and API benchmark figures belong in the synthetic-benchmark category. They are useful because they validate architecture assumptions and latency budgets without external services, but they are not equivalent to live production measurements.

Synthetic benchmark claims should be worded like this:

> The 3-tier cache benchmark models a workload with L1/L2/L3 hits at 60% / 20% / 8%, targeting roughly 88% cache effectiveness and a modeled token reduction from 93K to 7.8K tokens per 100-query workload.

Avoid wording like this until fresh live evidence is added:

> EnterpriseHub measured 89% live token savings and 87% production cache hit rate.

## Next Validation Work

1. Keep `make reviewer-smoke` green as the first reviewer-facing gate.
2. Add a command-backed eval scorecard whenever the golden dataset changes.
3. Keep synthetic cache benchmark output under `benchmarks/results/`, clearly labeled as a model.
4. Run `benchmarks/bench_cache_live.py` against a real Redis-backed environment and commit the output before quoting any live hit-rate numbers.
5. Update README metrics only from generated artifacts or the claim ledger.
