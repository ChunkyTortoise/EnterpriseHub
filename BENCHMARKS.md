# EnterpriseHub Synthetic Benchmarks

Synthetic benchmarks measuring internal overhead of EnterpriseHub's core subsystems. These use simulated workloads with realistic timing distributions -- no external API keys, databases, or services are required.

## How to Run

```bash
# Run all benchmarks with default iterations (1000 base, 10000 for cache)
python -m benchmarks.run_all

# Custom iteration count
python -m benchmarks.run_all --iterations 5000

# Run individual benchmarks
python -m benchmarks.bench_cache --iterations 10000
python -m benchmarks.bench_orchestration --iterations 2000
python -m benchmarks.bench_api_response --iterations 2000
```

## Methodology

All benchmarks use a **statistical latency model** (log-normal distributions calibrated to production observations) combined with **real computation** (hashing, dict lookups, JSON serialization) that exercises actual code paths. Timing is captured with `time.perf_counter_ns()` for nanosecond precision. Modeled latencies are deterministic and reproducible; real computation validates code-path correctness.

- **No external dependencies**: Standard library only (no pip packages needed)
- **Deterministic seeds**: Results are reproducible across runs (`seed=42`)
- **Statistical output**: P50, P95, P99 percentiles for every metric

These benchmarks measure **architecture correctness and latency budget validation**, not end-to-end latency with real LLM inference or database queries.

## Benchmarks

### 3-Tier Cache (`bench_cache`)

Simulates the L1 (in-memory) / L2 (Redis) / L3 (PostgreSQL) cache hierarchy used by the Claude Orchestrator.

| Metric | Target | What It Measures |
|--------|--------|-----------------|
| L1 P99 | < 1ms | In-memory dict lookup |
| L2 P99 | < 5ms | Redis network round-trip |
| L3 P99 | < 20ms | PostgreSQL query |
| Hit rate | >= 87% | Overall cache effectiveness |

Hit distribution: L1 60%, L2 20%, L3 8%, miss 12%.

### Orchestration Overhead (`bench_orchestration`)

Simulates the Claude Orchestrator's request processing pipeline without making LLM calls.

| Phase | What It Measures |
|-------|-----------------|
| Routing | Task-type classification + model selection |
| Cache key | Deterministic SHA-256 key generation |
| Parsing | Multi-strategy JSON extraction from LLM responses |
| **Total** | **< 200ms P99 target** |

### API Response Time (`bench_api_response`)

Simulates API endpoint handling including middleware stack (JWT auth, rate limiting, structured logging).

| Endpoint | Target P99 | What It Measures |
|----------|-----------|-----------------|
| `/health` | < 50ms | DB ping + uptime |
| `/api/leads/qualify` | < 2000ms | Lead scoring with simulated LLM |
| `/api/contacts/sync` | < 500ms | Batch CRM sync with GHL |

## Results Table

Results from `python -m benchmarks.run_all` (default 1000 iterations):

| Check | Target | P50 | P95 | P99 |
|-------|--------|-----|-----|-----|
| Cache L1 | < 1ms | ~0.30ms | ~0.49ms | ~0.60ms |
| Cache L2 | < 5ms | ~2.50ms | ~3.47ms | ~3.93ms |
| Cache L3 | < 20ms | ~11.06ms | ~14.11ms | ~16.06ms |
| Cache hit rate | >= 87% | ~88% | -- | -- |
| Orchestration total | < 200ms | ~0.01ms | ~0.03ms | ~0.34ms |
| API /health | < 50ms | ~1.32ms | ~1.97ms | ~2.44ms |
| API /qualify | < 2000ms | ~672ms | ~1225ms | ~1388ms |
| API /sync | < 500ms | ~184ms | ~340ms | ~366ms |

*Modeled latency values from log-normal distributions (seed=42). Results are deterministic and reproducible.*

## Exit Codes

- `0` -- All targets met
- `1` -- One or more targets missed
