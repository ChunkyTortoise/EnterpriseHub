# Audit C — Observability & Performance
**Agent**: Audit Agent C | **Date**: 2026-04-27 | **Scope**: Claim/evidence gap, trace export wiring, P50/P95/P99 provenance, cost dashboard, cache hit rate

---

## Executive Verdict

The claim/evidence gap is real and structurally significant, but it is closable in Wave 1. The OTel SDK is wired correctly (`api/main.py:177`), Prometheus metric shapes are defined (`observability/prometheus_exporter.py`), and the benchmark runner produces P50/P95/P99 output — but every headline number in BENCHMARK_VALIDATION_REPORT.md either derives from synthetic simulation inputs (not observed outputs), cites a tool ("locust") whose scripts do not exist in the repo, or is backed by `random.seed(42)` demo data. No k6 or Locust scripts exist anywhere in the repository. A hiring manager who traces any claim to source code hits a dead end within two hops.

**Wave 1 estimate**: 3–5 engineering days closes all three credibility gaps simultaneously.

---

## Inventory: Instrumented vs. Collected vs. Exported vs. Published

| Layer | Status | Evidence |
|---|---|---|
| Span decorator (`@trace_operation`) | Instrumented | `services/jorge/telemetry.py:129` |
| FastAPI auto-instrumentation | Wired, gated | `observability/otel_config.py:87` — fires only if `OTEL_ENABLED=true` |
| Prometheus metric shapes | Defined | `observability/prometheus_exporter.py:57–139` — cache hit rate, latency histograms, LLM token counters |
| `/metrics` HTTP endpoint | Wired | `api/main.py:678` |
| `setup_observability()` call | Wired | `api/main.py:177` — reads `OTEL_ENABLED` env var, defaults `false` |
| OTLP gRPC exporter | Code exists, broken | `otel_config.py:118–122` — `insecure=True`, no auth headers; Honeycomb/Grafana Cloud will reject |
| OTel Collector config | **Missing** | `docker-compose.observability.yml:40` mounts `./otel-collector-config.yaml` which does not exist — `docker compose up otel-collector` fails today |
| Jaeger/Honeycomb live wiring | **Not wired** | `HONEYCOMB_API_KEY` env var documented in `DISTRIBUTED_TRACING_GUIDE.md:265` is read by nothing in `otel_config.py` |
| Grafana dashboard | Exists | `grafana/dashboards/enterprisehub-overview.json` — local only, no live data source |
| k6 / Locust load test scripts | **Do not exist** | No files anywhere in repo matching `k6`, `locust`, `load_test` patterns |
| LLM cost dashboard | Exists, **synthetic** | `streamlit_demo/pages/25_LLM_Cost_Analytics.py:8–31` — `random.seed(42)`, comment on line 29 admits "production would read from llm_cost_log table" |

---

## P0/P1 Findings

### P0-C1: "150 req/s, 500 concurrent" — no backing evidence
**Source of claim**: `BENCHMARK_VALIDATION_REPORT.md:88–89`
**Methodology cited**: `BENCHMARK_VALIDATION_REPORT.md:149` — "locust — Load testing"
**Actual evidence**: No Locust scripts exist in the repository. Zero files match `locust` or `load_test` patterns. The numbers appear in the report but have no test artifact backing them.

### P0-C2: "88% cache hit rate" is a simulation input, not a measured output
**Source of claim**: `BENCHMARK_VALIDATION_REPORT.md:48`, `benchmarks/RESULTS.md:17`
**Root cause**: `benchmarks/bench_cache.py` hardcodes the hit distribution as "L1 60%, L2 20%, L3 8%, miss 12%". That arithmetic sums to exactly 88.1%. The benchmark then samples from those fixed probabilities and reports back the same number it was given. There is no mechanism by which the benchmark could produce a different hit rate; the "validated 88%" is a tautology of the simulation parameters.

### P0-C3: `otel-collector-config.yaml` is mounted but does not exist
**File**: `docker-compose.observability.yml:40`
**Impact**: `docker compose -f docker-compose.observability.yml up otel-collector` fails at startup. The entire local observability stack (Jaeger + Collector + Grafana) cannot be used without this file.

### P1-C4: Honeycomb auth header is never passed to the OTLP exporter
**File**: `ghl_real_estate_ai/observability/otel_config.py:122`
`OTLPSpanExporter(endpoint=endpoint, insecure=True)` — the `insecure=True` flag and absence of a `headers` parameter means traces will be rejected by any managed backend. `DISTRIBUTED_TRACING_GUIDE.md:265` documents `HONEYCOMB_API_KEY` but nothing in `otel_config.py` reads or passes that value.

### P1-C5: LLM cost dashboard uses `random.seed(42)` — not live data
**File**: `streamlit_demo/pages/25_LLM_Cost_Analytics.py:8–31`
The 30-day cost chart, model breakdown, and cache savings figures are all synthesized from `random.randint()` calls with a fixed seed. The file's own comment on line 29 acknowledges that "production would read from llm_cost_log table." As deployed, a viewer sees a convincing-looking cost chart that shares no information with actual LLM spend.

### P1-C6: Orchestration overhead "P99 = 0.0122ms" is non-credible
**File**: `benchmarks/RESULTS.md:28`
The orchestration benchmark reports a P99 total of 0.012ms. This is the overhead of simulated SHA-256 hashing and dict lookups — not FastAPI middleware, not JWT validation, not structured logging. The real <200ms overhead claim from `BENCHMARK_VALIDATION_REPORT.md:78` is architecturally plausible but not measured.

---

## Wave 1 Build Spec: k6 Load Test Scripts

Three scripts, each runnable standalone, covering the headline claim scenarios. Target location: `/Users/cave/Projects/EnterpriseHub/load_tests/`

**`load_tests/k6_qualification_flow.js`**
Tests the primary lead qualification path (`POST /api/leads/qualify`) with realistic payload. 50 virtual users ramping over 30s to steady state. Captures P50/P95/P99 per request. This is the scenario that produces a real "150 req/s, 500 concurrent" answer or reveals the actual ceiling. Thresholds: `http_req_duration p(95) < 2000`, `http_req_failed rate < 0.01`.

**`load_tests/k6_burst_test.js`**
Spike test: 10 users → 500 users in 15s → back to 10. Tests the "500 concurrent users" claim specifically. Records error rate and latency degradation at peak. Should expose whether 500 concurrent is actual headroom or aspirational.

**`load_tests/k6_sustained_throughput.js`**
10-minute constant-load test at 150 req/s targeting `/api/leads/qualify` and `/api/contacts/sync`. Captures throughput stability, latency percentiles over time, and error budget consumption. This is the script that produces numbers for the blog post and case study.

Each script must run against a locally started app (or staging) and export results to `load_tests/results/` as JSON for archiving.

---

## Wave 1+2 Build Spec: OTLP Exporter

### Wave 1 — Missing collector config (P0, ~half day)

Create `/Users/cave/Projects/EnterpriseHub/otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 512

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  logging:
    verbosity: normal

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, logging]
```

This unblocks local tracing immediately.

### Wave 2 — Honeycomb auth wiring (~1 day)

In `ghl_real_estate_ai/observability/otel_config.py`, replace the `_create_exporter` function's OTLP branch with an `_otlp_headers()` helper that reads `HONEYCOMB_API_KEY` and passes `headers={"x-honeycomb-team": key}` with `insecure=False`. Without this, Honeycomb will reject every export request with a 401.

Add to `.env.example`:
```
HONEYCOMB_API_KEY=
OTEL_ENABLED=false
OTEL_EXPORTER_TYPE=otlp
OTEL_ENDPOINT=https://api.honeycomb.io:443
```

---

## Compounding Leverage: Blog Post and Case Study

The Wave 1 k6 scripts and a single live query against `llm_cost_log` produce the numbers that power two content pieces simultaneously:

**Blog post 1: "3-tier cache cut LLM bill 89%"**
The 89% figure in `BENCHMARK_VALIDATION_REPORT.md:60–62` ("93K → 7.8K tokens per 100 queries") has no source query attached to it. Running `k6_sustained_throughput.js` while querying `SELECT sum(tokens_saved), sum(cost_saved_usd) FROM llm_cost_log WHERE created_at > now() - interval '24 hours'` produces the real number — which may be higher or lower than 89%. Either outcome is usable: confirmed 89% is the headline, actual 74% with "conservative validated number" is more credible. The Streamlit page at `25_LLM_Cost_Analytics.py` already has the right chart structure; it just needs the `random.seed(42)` block replaced with a real DB read.

**Case study refresh**
The P50/P95/P99 table in `BENCHMARK_VALIDATION_REPORT.md:70–75` shows latencies for lead qualification, buyer bot, and seller bot. These are asserted, not measured. The k6 qualification flow test plus PerformanceTracker (`services/jorge/performance_tracker.py`) running against a live bot session produces the same table with real data. One Wave 1 sprint produces numbers for the blog post, case study, and the BENCHMARK_VALIDATION_REPORT refresh at the same time.
