# Canonical Metrics Reference

**Source**: `benchmarks/RESULTS.md` (2026-02-14, Python 3.14.2, 1K/10K iterations, seed 42)
**Rule**: ALL marketing, case studies, specs, and video scripts MUST use ONLY these numbers.

## Cache Tier Performance

| Tier | P50 (ms) | P95 (ms) | P99 (ms) | Hit Rate |
|------|----------|----------|----------|----------|
| L1 (In-Memory) | 0.30 | 0.49 | 0.60 | 59.1% |
| L2 (Redis) | 2.50 | 3.47 | 3.93 | 20.5% |
| L3 (PostgreSQL) | 11.06 | 14.11 | 16.06 | 8.5% |
| **Overall** | **0.41** | **14.36** | **16.50** | **88.1%** |

## Orchestration Overhead

| Phase | P50 (ms) | P95 (ms) | P99 (ms) |
|-------|----------|----------|----------|
| Routing | 0.0029 | 0.0031 | 0.0038 |
| Cache Key | 0.0022 | 0.0023 | 0.0050 |
| Parsing | 0.0017 | 0.0031 | 0.0038 |
| **Total** | **0.0070** | **0.0086** | **0.0122** |

Target: <200ms total P99 — **PASS** (0.012ms actual)

## API Response Times

| Endpoint | P50 (ms) | P95 (ms) | P99 (ms) | Target P99 |
|----------|----------|----------|----------|-----------|
| GET /health | 1.32 | 1.97 | 2.44 | <50ms |
| POST /leads/qualify | 671.87 | 1,224.79 | 1,387.81 | <2,000ms |
| POST /contacts/sync | 183.88 | 339.87 | 365.90 | <500ms |

## Test Coverage

- **Total tests**: 8,500+ (across all repositories in portfolio)
- **EnterpriseHub tests**: Per pytest collection at time of benchmark

## Important Disclaimers

- Benchmarks use **modeled latency distributions**, not live network I/O
- LLM calls, Redis, and PostgreSQL are **simulated** (deterministic distributions)
- Results represent **system overhead and algorithmic performance**, not end-to-end production latency
- Competitive comparisons should cite sources or be labeled as estimates

---

*Generated from benchmarks/RESULTS.md | Last updated: 2026-02-14*
