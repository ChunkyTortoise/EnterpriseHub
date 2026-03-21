# Performance & Observability Analysis

**Codebase**: EnterpriseHub — GHL Real Estate AI Platform
**Date**: 2026-03-19
**Scope**: `ghl_real_estate_ai/` — observability infrastructure, cache design, rate limiting, health endpoints, deployment config

---

## What's Actually Implemented

### OpenTelemetry Tracing

Three files constitute the tracing layer:

- `/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/observability/otel_config.py` — `setup_observability()` initializes a `TracerProvider`, wires up a `BatchSpanProcessor`, and auto-instruments FastAPI, httpx, asyncpg, and Redis. All four auto-instrumentation calls are guarded by `try/except ImportError`, so they degrade silently to no-ops if the SDK packages are absent.
- `/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/observability/workflow_tracing.py` — `workflow_span` / `async_workflow_span` context managers and a `@trace_workflow_node` decorator for LangGraph nodes. A `_NoOpSpan` stub ensures zero-cost operation when OTel is absent. `create_handoff_span` provides cross-bot trace correlation.
- `/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/observability/__init__.py` — re-exports `setup_observability` as the public surface.

`setup_observability()` is called during `app.lifespan` in `api/main.py`. It is **opt-in via env var** (`OTEL_ENABLED=true`). The default is `false`, meaning **tracing is disabled in every current deployment** (render.yaml does not set `OTEL_ENABLED`).

The `@trace_workflow_node` decorator is defined but grep confirms **zero call-sites outside the observability module itself** — it has not been applied to any actual bot workflow nodes.

### Prometheus Metrics

`/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/observability/prometheus_exporter.py` defines `JorgePrometheusExporter` with:
- `Gauge`: `jorge_cache_hit_rate` (by layer), `jorge_response_latency_p95` (by bot), `jorge_error_rate` (by bot)
- `Counter`: `jorge_handoff_total` (source/target), `jorge_lead_temperature`
- `Histogram`: `jorge_frs_score`, `jorge_pcs_score` (buckets at 0/20/40/60/80/100)

The exporter is a singleton accessed via `get_prometheus_exporter()`. Grep confirms it is imported and instantiated in exactly **two files**: `prometheus_exporter.py` itself and `jorge_handoff_service.py`. The handoff service calls `inc_handoff()` at one point. **No other production code calls `set_cache_hit_rate`, `observe_frs_score`, `set_response_latency_p95`, or `inc_lead_temperature`**, making the Prometheus schema largely unpopulated in practice.

A `/health/prometheus` route exists in `api/routes/health.py` (line 757) that calls `prometheus_client.generate_latest()` — but since no code is feeding the gauges or histograms, it would return mostly empty metrics.

### Two Prometheus Config Files (Neither Wired)

- `/Users/cave/Projects/EnterpriseHub/monitoring/prometheus.yml` — references `kubernetes_sd_configs` with namespace `jorge-revenue-platform`. This is aspirational Kubernetes infrastructure, not the current Docker Compose deployment.
- `/Users/cave/Projects/EnterpriseHub/observability/prometheus.yml` — references `host.docker.internal:8000` and Jaeger. This is the development-intent config but requires manual `docker-compose --profile monitoring up`.

Neither config is referenced by the primary `docker-compose.yml` (the `monitoring` profile is opt-in and commented out of the default run command).

### Health Check Endpoints

`/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/api/routes/health.py` implements a robust hierarchy:

| Endpoint | Auth Required | Checks |
|---|---|---|
| `GET /health/ping` | No | Process liveness only (no dependencies) |
| `GET /health/` | No (DB + Cache injected) | PostgreSQL + Redis round-trip |
| `GET /health/live` | No | Uptime counter only |
| `GET /health/ready` | Yes (enterprise user) | DB + Redis + JWT generation |
| `GET /health/deep` | Yes | All external APIs (Apollo, Twilio, SendGrid, GHL) + psutil system metrics |
| `GET /health/metrics` | Yes | MonitoringService summary + SLA compliance + DB stats |
| `GET /health/dependencies` | Yes | Per-dependency status table |
| `GET /health/circuit-breakers` | Yes | CircuitBreaker states + recommendations |
| `GET /health/prometheus` | No | Prometheus exposition format |

The depth is genuine — circuit breaker status, psutil CPU/memory/disk, external API connectivity. However, the `render.yaml` `healthCheckPath` is set to `/health` (the root basic health), which maps to the dependency-injected basic check rather than the simpler `/health/ping`. This means Render's health check itself has a DB/Redis dependency, creating a potential catch-22 on cold start.

### Rate Limiting

`/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/api/middleware/rate_limiter.py` implements:
- Token-bucket algorithm with `asyncio.Lock`
- Unauthenticated: 100 req/min, burst of 20
- Authenticated: 1000 req/min
- WebSocket: 10 concurrent connections per IP
- `ThreatDetector`: blocks IPs after 50 requests in 10 seconds or repeated violations; 15-minute block duration
- Bot detection via User-Agent substring match
- Health check paths (`/health`, `/api/health`, `/ping`) bypass the limiter
- Adds `Retry-After` and `X-Rate-Limit-*` response headers

Rate limiting is **in-process and in-memory only** — state lives in a Python `dict`. On Render's free plan (single instance), this is acceptable. Under horizontal scaling, each replica has independent state, meaning a coordinated attack could hit N×100 req/min. No Redis-backed rate limiter (e.g., `slowapi` with Redis) is implemented.

### Performance Tracker

`/Users/cave/Projects/EnterpriseHub/ghl_real_estate_ai/services/jorge/performance_tracker.py` is the most complete observability component:
- In-memory rolling windows: 1h, 24h, 7d
- P50/P95/P99 latency via `statistics.quantiles`
- SLA targets defined per-bot per-operation (e.g., lead bot full qualification: P95 < 2000ms)
- `track_async_operation` async context manager for automated timing
- Thread-safe via `threading.Lock`

It is a standalone service used by the Jorge bot subsystem. It is **not connected to Prometheus** — stats live only in-memory and are accessible via API calls to the performance tracker object, not scraped by any external collector.

---

## Cache Architecture Assessment

### What the Code Claims

CLAUDE.md describes: "Redis cache (L1/L2/L3)" and "88% hit rate" is referenced in some project documentation.

### What the Code Actually Does

The orchestrator (`claude_orchestrator.py`, lines 171-179) defines a single in-process response cache:

```python
self._memory_context_cache: Dict[str, Any] = {}   # in-process memory context
self._response_cache: Dict[str, Tuple[Any, float]] = {}  # (response, expiry)
self._response_cache_ttl = 300  # 5 minutes
self._response_cache_hits = 0
self._response_cache_misses = 0
```

Cache key generation uses SHA-256 of `task_type + prompt + context`, truncated to 16 hex chars. Cache is checked on non-streaming, non-tool requests. Expired entries are evicted lazily on miss.

**This is a single-tier, single-process, in-memory LRU substitute.** There is no L2 (Redis) or L3 (database-backed) layer implemented in this file.

The `JorgePrometheusExporter` defines a `jorge_cache_hit_rate` gauge with a `layer` label, implying L1/L2/L3 were intended — but `set_cache_hit_rate` is never called from production code, and the orchestrator does not increment the Prometheus gauge from its `_response_cache_hits` counter.

**The 88% cache hit rate claim is aspirational, not measured.** The hit/miss counters (`_response_cache_hits`, `_response_cache_misses`) are Python integers on an object instance — they reset on every process restart, are never exported, and are only visible via `logger.debug` statements.

A separate `CacheService` (injected into health routes) wraps Redis. That is a real L2 cache, but it handles health check probe writes, not AI response caching. Whether any service layer uses `CacheService` for response caching would require additional investigation of individual service files.

### True Cache Architecture (As Built)

| Layer | Implementation | Status |
|---|---|---|
| L1 | In-process `_response_cache` dict in `ClaudeOrchestrator` | Implemented, not measured |
| L2 | Redis (`CacheService`) | Infrastructure present, extent of usage unclear |
| L3 | PostgreSQL (implied by architecture diagram) | No evidence in orchestrator code |

---

## Observability Gaps

### Critical Gaps

1. **OTel disabled by default, not enabled in any deployment.** `render.yaml` does not set `OTEL_ENABLED=true`. No Jaeger or OTLP collector is provisioned in render.yaml or docker-compose.yml (only in `--profile monitoring`).

2. **`@trace_workflow_node` decorator has zero production call-sites.** The decorator infrastructure exists but was never applied to bot workflow nodes (`lead_bot.py`, `buyer_bot.py`, `seller_bot.py`). Cross-bot traces cannot be assembled because individual nodes are not instrumented.

3. **Prometheus metrics are unpopulated.** `JorgePrometheusExporter` is a complete schema but only `inc_handoff()` is called from one location. Cache hit rates, FRS/PCS score distributions, and latency gauges are never set from production code paths.

4. **Performance tracker is not exported.** `PerformanceTracker` computes real P50/P95/P99 latency but its data is inaccessible to any external system. No adapter converts tracker stats to Prometheus metrics.

5. **Rate limiter state is ephemeral and non-distributed.** IP block lists and request histories live in-process. A process restart clears all rate limit state, and multiple replicas enforce limits independently.

6. **No structured log correlation.** Logs use `logging.getLogger(__name__)` with dict `extra` fields, but no consistent `trace_id` field is injected into log records. `get_current_trace_id()` exists in `otel_config.py` but is not wired into a logging filter.

7. **No alerting pipeline for production.** `services/jorge/alerting_service.py` defines 7 default alert rules and cooldown logic, but no outbound channel (PagerDuty, Slack webhook, email) is configured in `render.yaml` or any environment variable.

8. **`render.yaml` hardcodes `TEST_MODE=true` and `DEMO_MODE=true`.** This likely suppresses real GHL API calls and may short-circuit code paths that would otherwise emit metrics. Performance observed in this environment is not representative of production load.

### Secondary Gaps

- `docker-compose.yml` mounts `./:/app` in the `app` container — this code mount is flagged with a comment "Remove code mount in production" but is present in the committed file.
- Nginx config referenced at `./nginx.conf` is not present in the Glob results, meaning the production profile would fail on startup.
- `redis-server --requirepass ${REDIS_PASSWORD:-}` — if `REDIS_PASSWORD` is unset, Redis starts without authentication.
- The deep health check re-creates `DatabaseService` inline (`db = DatabaseService(); await db.initialize()`) rather than reusing the injected instance, potentially opening duplicate connection pool entries.
- `/health/ready` requires enterprise auth — this blocks Kubernetes readiness probes from working without a service account token.

---

## Recommended Additions

### 1. Enable OTel in Render Deployment

Add to `render.yaml` under `envVars` for the API service:
```yaml
- key: OTEL_ENABLED
  value: "true"
- key: OTEL_EXPORTER_TYPE
  value: "otlp"
- key: OTEL_ENDPOINT
  value: "https://your-collector-endpoint"
```

Collector options compatible with Render free tier: **Grafana Cloud** (free tier, 50GB traces/month), **Honeycomb** (free tier), or **Jaeger** on a separate Render instance.

### 2. Wire `@trace_workflow_node` to Bot Entry Points

Apply the existing decorator to the three bot `process_*` entry points:

```python
# agents/lead_bot.py
@trace_workflow_node("lead_bot", "process_lead_conversation")
async def process_lead_conversation(self, contact_id, message, history):
    ...
```

This requires only adding the decorator — the infrastructure is complete.

### 3. Connect PerformanceTracker to Prometheus

Add a `PrometheusAdapter` that flushes tracker stats to the exporter on a background task interval:

```python
# In app lifespan or a background task
async def flush_perf_to_prometheus():
    tracker = get_performance_tracker()
    exporter = get_prometheus_exporter()
    for bot_type in ["lead_bot", "buyer_bot", "seller_bot"]:
        stats = await tracker.get_bot_stats(bot_type)
        if stats:
            exporter.set_response_latency_p95(bot_type, stats.p95_latency_ms)
            exporter.set_error_rate(bot_type, stats.error_rate)
```

### 4. Export Cache Hit Counters

In `ClaudeOrchestrator._get_cached_response()`, after incrementing `_response_cache_hits`, call:
```python
# Only when prometheus_client is installed
total = self._response_cache_hits + self._response_cache_misses
if total > 0:
    get_prometheus_exporter().set_cache_hit_rate("l1", self._response_cache_hits / total)
```

### 5. Distributed Rate Limiter (Pre-Scaling)

Replace `EnhancedRateLimiter`'s in-memory buckets with Redis-backed counters using `slowapi` + `limits`:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.redis_url)
```

This is a one-time swap that makes rate limiting correct under horizontal scaling.

### 6. Log-Trace Correlation Filter

Add a `logging.Filter` subclass that reads `get_current_trace_id()` and injects it into every log record:

```python
class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_current_trace_id() or "-"
        return True
```

Wire into the root logger at startup alongside `setup_observability()`.

### 7. Alert Channel Configuration

`alerting_service.py` is production-ready. Add Slack webhook support:
```yaml
# render.yaml
- key: ALERT_SLACK_WEBHOOK_URL
  sync: false
```

Then implement a `SlackAlertChannel` that posts to the webhook when `AlertSeverity.CRITICAL` or `WARNING` rules fire.

---

## Health Check Design

The current `/health` hierarchy is well-structured. Two adjustments for production:

**Fix the Render health check path**: Change `healthCheckPath: /health` to `healthCheckPath: /health/ping`. The ping endpoint has zero dependencies and will not fail during cold start while DB connections are initializing.

**Fix `/health/ready` auth requirement**: Remove `current_user: UserDep` from the readiness probe signature. Kubernetes/Render readiness probes are infrastructure calls and must not require JWT tokens. Move auth-gated checks to `/health/deep`.

**Recommended endpoint map for production**:

| Path | Use | Auth | SLA |
|---|---|---|---|
| `GET /health/ping` | Container liveness (Render/K8s liveness probe) | None | <5ms |
| `GET /health/` | Load balancer health gate | None | <100ms |
| `GET /health/ready` | Readiness probe — remove JWT dep | None | <500ms |
| `GET /health/deep` | On-demand ops check | JWT | No SLA |
| `GET /health/prometheus` | Prometheus scrape target | None | <50ms |
| `GET /health/circuit-breakers` | Ops dashboard | JWT | No SLA |

---

## Performance Baseline Recommendations

No real performance baseline exists. The "88% cache hit rate" and "<200ms overhead" claims in CLAUDE.md are design targets, not measured values.

### Immediate Steps to Establish a Baseline

1. **Enable OTel and generate load**: Run `locust` or `k6` against the staging deployment with `OTEL_ENABLED=true` pointed at a Jaeger instance. Collect 1000+ requests across all three bot entry points.

2. **Instrument the actual Claude API call**: The `ClaudeOrchestrator.process_request()` method does not currently wrap the `self.llm.call()` invocation in a span. A single span around the LLM call would immediately surface P50/P95/P99 for the most expensive operation.

3. **Measure actual cache hit rate**: Add a Prometheus counter flush from the orchestrator's `_response_cache_hits / (_response_cache_hits + _response_cache_misses)` ratio. Observe over 24 hours of real traffic.

4. **Profile the token-bucket lock contention**: `EnhancedRateLimiter.is_allowed()` acquires `asyncio.Lock()` on every request. Under high concurrency this serializes all requests through one async lock. Profile with `py-spy` to check for event loop saturation.

5. **Establish SLA baselines before claiming compliance**: `PerformanceTracker` already defines the SLA targets (lead bot P95 < 2000ms). Wire it to actual call-sites via `track_async_operation`, then run `/health/metrics` after 24 hours to read the first real compliance report.

### Load Testing Targets (Suggested)

| Scenario | Tool | Target |
|---|---|---|
| Bot conversation throughput | `locust` | 50 concurrent users, 10-minute soak |
| Cache effectiveness | Custom script | 1000 identical queries, observe L1 hit rate |
| Rate limiter under burst | `k6` | 200 req/s for 30s, confirm 429 response |
| Health endpoint latency | `wrk` | P99 < 10ms for `/health/ping` |
| DB pool exhaustion | `pgbench` | 100 concurrent connections, monitor pool idle count |
