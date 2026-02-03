# EnterpriseHub Monitoring & Alerting Guide

**Version**: 1.0
**Last Updated**: February 2, 2026

---

## Table of Contents

1. [Key Metrics](#key-metrics)
2. [Prometheus Queries](#prometheus-queries)
3. [Grafana Dashboard](#grafana-dashboard)
4. [Alert Rules](#alert-rules)
5. [Alert Response Playbooks](#alert-response-playbooks)
6. [Built-in Application Monitoring](#built-in-application-monitoring)

---

## Key Metrics

### Application Health

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Error rate (5m) | <1% | >3% | >5% |
| Response time p95 | <200ms | >300ms | >500ms |
| Response time p99 | <500ms | >750ms | >1000ms |
| Request throughput | >100 req/sec | <50 req/sec | <10 req/sec |
| WebSocket connections | Stable | >1000 | >2000 |

### Database

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Query time p95 | <50ms | >100ms | >200ms |
| Connection pool usage | <60% | >80% | >90% |
| Active queries | <20 | >40 | >60 |
| Long-running queries (>5s) | 0 | >2 | >5 |
| Pool size | 20 (configured) | - | Pool exhausted |

### Cache (Redis + Application)

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Cache hit rate | >70% | <60% | <40% |
| Redis memory usage | <60% | >80% | >90% |
| Eviction rate | <0.5% | >1% | >2% |
| Redis connection latency | <5ms | >10ms | >50ms |

### External Services

| Service | Target Availability | Warning | Critical |
|---------|-------------------|---------|----------|
| Claude API (Anthropic) | >99% | <99% | <98% |
| GHL CRM API | >99.5% | <99% | <98% |
| PostgreSQL | >99.9% | <99.8% | <99.5% |
| Redis | >99.9% | <99.8% | <99.5% |

### Jorge Bot Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Bot response accuracy | >90% | <85% | <75% |
| Escalation rate | <15% | >20% | >30% |
| Avg qualification time | <5 min | >8 min | >15 min |
| Lead score accuracy | >85% | <80% | <70% |

### Business Metrics

| Metric | Daily Target | Description |
|--------|-------------|-------------|
| Leads qualified | >100 | Total leads through qualification |
| Buyers matched | >50 | Successful property matches |
| Sellers analyzed | >20 | CMA analyses completed |
| Conversion rate | >15% | Lead to qualified conversion |
| Revenue attributed | Tracked | Dollar value of bot-assisted deals |

---

## Prometheus Queries

### Error Rate (5-minute window)

```promql
rate(jorge_api_errors_total[5m]) / rate(jorge_api_requests_total[5m]) * 100
```

Alert if >5%.

### Response Time p95

```promql
histogram_quantile(0.95, rate(jorge_api_duration_seconds_bucket[5m]))
```

Alert if >0.2s (200ms).

### Response Time p99

```promql
histogram_quantile(0.99, rate(jorge_api_duration_seconds_bucket[5m]))
```

Alert if >0.5s (500ms).

### Request Throughput

```promql
sum(rate(jorge_api_requests_total[5m]))
```

Alert if <50 req/sec during business hours.

### Cache Hit Rate

```promql
rate(jorge_cache_hits_total[5m]) / (rate(jorge_cache_hits_total[5m]) + rate(jorge_cache_misses_total[5m])) * 100
```

Alert if <60%.

### Database Connection Pool Usage

```promql
jorge_db_pool_active_connections / jorge_db_pool_max_connections * 100
```

Alert if >80%.

### Claude API Latency

```promql
histogram_quantile(0.95, rate(jorge_claude_api_duration_seconds_bucket[5m]))
```

Alert if >2s.

### GHL API Error Rate

```promql
rate(jorge_ghl_api_errors_total[5m]) / rate(jorge_ghl_api_requests_total[5m]) * 100
```

Alert if >5%.

### WebSocket Active Connections

```promql
jorge_websocket_active_connections
```

Alert if >2000 (capacity concern).

### Token Usage (Cost Monitoring)

```promql
sum(increase(jorge_token_usage_total[24h])) by (model)
```

Track daily token consumption by model.

---

## Grafana Dashboard

### Dashboard: "Jorge Bots Production"

Configure the following panels:

### Row 1: Overview

| Panel | Type | Query | Alert |
|-------|------|-------|-------|
| Error Rate | Gauge | 5-min error rate | >5% red |
| Response Time | Time series | p50, p95, p99 | >300ms shaded |
| Throughput | Time series | req/sec | <50 red zone |
| Uptime | Stat | Last 30 days | <99.9% red |

### Row 2: Infrastructure

| Panel | Type | Query | Alert |
|-------|------|-------|-------|
| Cache Hit Rate | Gauge | Hit rate % | <60% red |
| DB Connections | Gauge | Pool usage % | >80% yellow |
| Redis Memory | Gauge | Memory usage | >80% yellow |
| CPU/Memory | Time series | Pod resources | >80% yellow |

### Row 3: External Services

| Panel | Type | Query | Alert |
|-------|------|-------|-------|
| Claude API | Status | Availability + latency | <99% red |
| GHL CRM | Status | Availability + latency | <99% red |
| Database | Status | Connection state | Down = red |
| Redis | Status | Connection state | Down = red |

### Row 4: Business Metrics

| Panel | Type | Query | Alert |
|-------|------|-------|-------|
| Leads Qualified | Counter | Today's total | - |
| Buyers Matched | Counter | Today's total | - |
| Sellers Analyzed | Counter | Today's total | - |
| Bot Accuracy | Gauge | Rolling accuracy | <85% yellow |

### Row 5: Alerts

| Panel | Type | Description |
|-------|------|-------------|
| Active Alerts | Table | Severity, message, triggered time |
| Alert History | Time series | Alert frequency over 7 days |

---

## Alert Rules

### Critical Alerts (Immediate Response Required)

```yaml
# High Error Rate
- alert: HighErrorRate
  expr: rate(jorge_api_errors_total[5m]) / rate(jorge_api_requests_total[5m]) > 0.05
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "API error rate above 5%"
    description: "Error rate is {{ $value | humanizePercentage }}"

# Database Down
- alert: DatabaseDown
  expr: jorge_db_up == 0
  for: 30s
  labels:
    severity: critical
  annotations:
    summary: "PostgreSQL database is unreachable"

# Redis Down
- alert: RedisDown
  expr: jorge_redis_up == 0
  for: 30s
  labels:
    severity: critical
  annotations:
    summary: "Redis cache is unreachable"

# Claude API Down
- alert: ClaudeAPIDown
  expr: jorge_claude_api_up == 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Claude API is unreachable - all bot responses affected"
```

### Warning Alerts

```yaml
# Slow Response Times
- alert: SlowResponseTime
  expr: histogram_quantile(0.95, rate(jorge_api_duration_seconds_bucket[5m])) > 0.3
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "API p95 response time above 300ms"

# High DB Connection Pool Usage
- alert: HighDBPoolUsage
  expr: jorge_db_pool_active_connections / jorge_db_pool_max_connections > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Database connection pool above 80%"

# Low Cache Hit Rate
- alert: LowCacheHitRate
  expr: |
    rate(jorge_cache_hits_total[5m]) /
    (rate(jorge_cache_hits_total[5m]) + rate(jorge_cache_misses_total[5m])) < 0.6
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 60%"

# High Memory Usage
- alert: HighMemoryUsage
  expr: jorge_memory_usage_bytes / jorge_memory_limit_bytes > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Memory usage above 80%"

# Low Bot Accuracy
- alert: LowBotAccuracy
  expr: jorge_bot_accuracy_rate < 0.85
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Bot accuracy below 85%"
```

### Info Alerts

```yaml
# High Token Usage
- alert: HighTokenUsage
  expr: increase(jorge_token_usage_total[24h]) > 80000
  labels:
    severity: info
  annotations:
    summary: "Daily token usage approaching budget (80k/100k)"

# Cache Evictions
- alert: CacheEvictions
  expr: rate(jorge_cache_evictions_total[5m]) > 0
  for: 5m
  labels:
    severity: info
  annotations:
    summary: "Cache evictions occurring - consider increasing cache size"
```

### Alert Notification Channels

| Severity | Channel | Response Time |
|----------|---------|---------------|
| Critical | Slack #alerts + PagerDuty | Immediate |
| Warning | Slack #monitoring | Within 1 hour |
| Info | Slack #monitoring | Next business day |

Configure in environment:
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
PAGERDUTY_API_KEY=your-pagerduty-key
```

---

## Alert Response Playbooks

### High Error Rate (>5%)

1. Check logs: `kubectl logs -n production -l app=jorge-api | grep ERROR`
2. Check if recent deployment: `kubectl rollout history deployment/jorge-api`
3. Check external services: Claude API, GHL CRM, PostgreSQL
4. If deployment-related: Rollback (`docs/DEPLOYMENT.md` > Rollback)
5. If external service: Check provider status pages, enable circuit breakers

### Slow Response Times (>300ms p95)

1. Check database query performance in Grafana
2. Check cache hit rate (low cache = slow queries hitting DB)
3. Check Claude API response times
4. If DB: Add indexes, optimize queries, scale read replicas
5. If cache: Increase TTL, increase cache size
6. If Claude: Check rate limits, switch to Haiku for non-critical

### Database Connection Exhaustion (>80%)

1. Check for connection leaks: long-running idle connections
2. Kill idle connections: `SELECT pg_terminate_backend(pid)` for idle >300s
3. Increase pool: Update `DB_POOL_SIZE` and `DB_MAX_OVERFLOW`
4. Check for N+1 queries causing excess connections

### Memory Issues (>80%)

1. Check cache sizes: LRU eviction may need lower threshold
2. Check for memory leaks with `memory_profiler`
3. Restart pods to force garbage collection
4. Increase pod memory limits if justified

---

## Built-in Application Monitoring

The FastAPI application includes built-in monitoring capabilities:

### Performance Middleware

Every request is tracked with headers (see `ghl_real_estate_ai/api/main.py`):

- `X-Process-Time`: Processing duration in seconds
- `X-Performance`: Tier classification (`excellent` <100ms, `good` <300ms, `acceptable` <500ms, `slow` >500ms)
- `X-Avg-Response-Time`: Rolling average response time

### Slow Request Logging

Requests exceeding thresholds are automatically logged:

- **>500ms**: `WARNING` level with full context
- **>300ms**: `INFO` level with path and timing
- **Every 100 requests**: Aggregate metrics logged (avg time, cache rate, compression rate)

### System Health Monitor

The `system_health_monitor` service runs continuous background checks on:

- Database connectivity
- Redis connectivity
- WebSocket server status
- Event publisher status

### Error Monitoring Service

The `error_monitoring_service` provides:

- Real-time error aggregation
- Error rate calculation
- Top error type tracking
- Dashboard API at `GET /api/error-monitoring/dashboard`

### WebSocket Performance

Monitor WebSocket health at `GET /api/websocket/performance`:

- Active connection count
- Message throughput
- Connection latency
- Reconnection rate

---

**Version**: 1.0 | **Last Updated**: February 2, 2026
