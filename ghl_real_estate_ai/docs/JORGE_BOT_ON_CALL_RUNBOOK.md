# Jorge Bot On-Call Runbook

**Version:** 1.0
**Date:** February 8, 2026
**Scope:** On-call troubleshooting procedures for Jorge Bot alert rules

---

## Quick Reference

### Escalation Policy

| Level | Delay | Channels | Condition |
|-------|-------|----------|-----------|
| **L1** | Immediate | Rule's configured channels | Alert triggered |
| **L2** | 5 min | Email + Slack + Webhook | Critical, unacknowledged |
| **L3** | 15 min | PagerDuty + Opsgenie | Critical, still unacknowledged |

### On-Call Contacts

```
Primary On-Call:   [Name / Phone / Email]
Secondary:         [Name / Phone / Email]
Engineering Lead:  [Name / Phone / Email]
Client (Jorge):    realtorjorgesales@gmail.com
```

### Service Health Check

```bash
# Quick health check — all bots
curl -s localhost:8000/health | jq '.status'

# Individual bot health
curl -s localhost:8001/health   # Lead Bot
curl -s localhost:8002/health   # Seller Bot
curl -s localhost:8003/health   # Buyer Bot

# Check container status
docker ps --filter "name=jorge" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# View recent logs
docker logs jorge-api --tail 100 --since 5m
```

---

## Alert Rule Procedures

### 1. SLA Violation (Critical)

**Rule**: `sla_violation`
**Condition**: P95 latency exceeds SLA target
**Channels**: Email, Slack, Webhook
**Cooldown**: 5 min

**SLA Targets**:

| Bot | P50 | P95 | P99 |
|-----|-----|-----|-----|
| Lead Bot (process) | 300ms | 1500ms | 2000ms |
| Buyer Bot (process) | 400ms | 1800ms | 2500ms |
| Seller Bot (process) | 400ms | 1800ms | 2500ms |
| Handoff (execute) | 100ms | 500ms | 800ms |

**Diagnosis**:

```bash
# 1. Check current latency metrics
python -c "
import asyncio
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
tracker = PerformanceTracker()
stats = asyncio.run(tracker.get_all_stats())
for bot, s in stats.items():
    print(f'{bot}: P50={s[\"p50\"]:.0f}ms  P95={s[\"p95\"]:.0f}ms  P99={s[\"p99\"]:.0f}ms')
"

# 2. Check Redis connection (cache misses cause slowdowns)
redis-cli ping
redis-cli info stats | grep keyspace

# 3. Check database connection pool
docker logs jorge-api --tail 50 | grep -i "pool\|connection\|timeout"

# 4. Check GHL API latency (external dependency)
docker logs jorge-api --tail 50 | grep -i "ghl\|goHighLevel"
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Redis down/slow | Restart Redis: `docker restart jorge-redis` |
| Database pool exhausted | Restart API: `docker restart jorge-api` |
| GHL API slow | Check GHL status page; enable fallback mode |
| High traffic spike | Scale horizontally or enable rate limiting |
| Cache cold (after deploy) | Wait 5-10 min for cache warm-up |

**Acknowledge**: Once investigating, acknowledge the alert to prevent L2/L3 escalation.

---

### 2. High Error Rate (Critical)

**Rule**: `high_error_rate`
**Condition**: Error rate > 5%
**Channels**: Email, Slack, Webhook
**Cooldown**: 5 min

**Diagnosis**:

```bash
# 1. Check error logs
docker logs jorge-api --tail 200 | grep -i "error\|exception\|traceback"

# 2. Check error rate metrics
python -c "
import asyncio
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
collector = BotMetricsCollector()
summary = asyncio.run(collector.get_system_summary())
print(f'Error rate: {summary.get(\"error_rate\", 0):.1%}')
"

# 3. Check for specific error patterns
docker logs jorge-api --tail 500 | grep -c "ERROR"
docker logs jorge-api --tail 500 | grep "ERROR" | sort | uniq -c | sort -rn | head -10
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Claude API errors | Check API key, rate limits; switch to fallback provider |
| Database errors | Check PostgreSQL connectivity; restart if needed |
| Invalid input data | Check GHL webhook payloads; validate input schemas |
| Memory exhaustion | Restart containers; check for memory leaks |
| Deployment regression | Roll back: `git checkout <previous-tag> && docker-compose up -d` |

---

### 3. Low Cache Hit Rate (Warning)

**Rule**: `low_cache_hit_rate`
**Condition**: Cache hit rate < 50%
**Channels**: Slack
**Cooldown**: 10 min

**Diagnosis**:

```bash
# 1. Check Redis status
redis-cli info memory
redis-cli info keyspace
redis-cli dbsize

# 2. Check cache hit metrics
python -c "
import asyncio
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
collector = BotMetricsCollector()
summary = asyncio.run(collector.get_system_summary())
print(f'Cache hit rate: {summary.get(\"cache_hit_rate\", 0):.1%}')
"

# 3. Check Redis memory usage
redis-cli info memory | grep used_memory_human
redis-cli info stats | grep evicted_keys
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Redis restart (cold cache) | Wait 10-15 min for natural warm-up |
| Redis evicting keys | Increase `maxmemory` in redis.conf |
| TTL too short | Review cache TTL settings in config |
| New deployment | Expected — cache populates over time |
| Redis OOM | Increase container memory limit |

**Note**: This is a warning-level alert. Cache hit rate typically recovers within 15 min after a Redis restart.

---

### 4. Handoff Failure (Critical)

**Rule**: `handoff_failure`
**Condition**: Handoff success rate < 95%
**Channels**: Email, Slack
**Cooldown**: 5 min

**Diagnosis**:

```bash
# 1. Check handoff analytics
python -c "
import asyncio
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
svc = JorgeHandoffService()
analytics = svc.get_analytics()
print(f'Total: {analytics[\"total_handoffs\"]}')
print(f'Success: {analytics[\"successful_handoffs\"]}')
print(f'Blocked: {analytics[\"blocked_handoffs\"]}')
print(f'Success rate: {analytics.get(\"success_rate\", 0):.1%}')
"

# 2. Check for rate limiting issues
docker logs jorge-api --tail 100 | grep -i "rate.limit\|handoff.blocked"

# 3. Check for circular handoff blocks
docker logs jorge-api --tail 100 | grep -i "circular"
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Rate limit exceeded (3/hr) | Wait for hourly window reset |
| Circular handoff blocked | Investigate bot routing logic; check intent decoders |
| Contact lock contention | Check for stuck locks; restart if needed |
| Pattern learning drift | Reset thresholds: clear `_handoff_outcomes` |
| Intent decoder miscalibration | Review GHL data quality; check score thresholds |

**Handoff Limits**:
- 3 handoffs per hour per contact
- 10 handoffs per day per contact
- 30-minute circular prevention window
- 30-second lock timeout

---

### 5. Bot Unresponsive (Critical)

**Rule**: `bot_unresponsive`
**Condition**: No responses for 5 minutes
**Channels**: Email, Slack, Webhook
**Cooldown**: 10 min

**Diagnosis**:

```bash
# 1. Check container status
docker ps --filter "name=jorge"

# 2. Check if process is running
docker exec jorge-api ps aux | grep python

# 3. Check for OOM kills
docker inspect jorge-api --format='{{.State.OOMKilled}}'
dmesg | grep -i "oom\|killed" | tail -5

# 4. Check resource usage
docker stats jorge-api --no-stream

# 5. Check health endpoints
curl -s -o /dev/null -w "%{http_code}" localhost:8000/health
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Container crashed | `docker restart jorge-api` |
| OOM killed | Increase memory limit; check for leaks |
| Deadlocked process | `docker restart jorge-api`; review async code |
| Network partition | Check Docker networking: `docker network inspect` |
| Host resource exhaustion | Check host: `df -h`, `free -m`, `top` |

**Immediate Action**: If health endpoint returns non-200, restart immediately:
```bash
docker restart jorge-api
# Verify recovery
sleep 5 && curl -s localhost:8000/health
```

---

### 6. Circular Handoff Spike (Warning)

**Rule**: `circular_handoff_spike`
**Condition**: >10 blocked handoffs in 1 hour
**Channels**: Slack
**Cooldown**: 10 min

**Diagnosis**:

```bash
# 1. Check handoff history for circular patterns
python -c "
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
svc = JorgeHandoffService()
history = svc._handoff_history
for h in list(history)[-20:]:
    print(f'{h[\"contact_id\"]}: {h[\"source\"]} -> {h[\"target\"]} ({h[\"status\"]})')
"

# 2. Look for specific contacts cycling between bots
docker logs jorge-api --tail 500 | grep "circular" | \
  sed 's/.*contact_id=\([^ ]*\).*/\1/' | sort | uniq -c | sort -rn
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| Ambiguous intent signals | Review intent decoder thresholds (buyer vs seller) |
| GHL data conflicting | Check contact data quality in GHL |
| Threshold too aggressive | Raise confidence threshold from 0.7 to 0.8 |
| Single contact looping | Manually assign contact to correct bot in GHL |

**Investigation**: Check which contacts are causing circular handoffs. Often a single contact with ambiguous signals (e.g., "I want to sell my house and buy another") triggers repeated lead→buyer→seller→lead cycles.

---

### 7. Rate Limit Breach (Warning)

**Rule**: `rate_limit_breach`
**Condition**: Rate limit errors > 10%
**Channels**: Slack
**Cooldown**: 5 min

**Diagnosis**:

```bash
# 1. Check rate limit hits
docker logs jorge-api --tail 200 | grep -i "rate.limit"

# 2. Check GHL API rate limits (10 req/s)
docker logs jorge-api --tail 200 | grep -i "429\|too.many.requests"

# 3. Check handoff rate limits per contact
python -c "
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
svc = JorgeHandoffService()
# Check which contacts are hitting limits
for contact_id, history in svc._handoff_history.items():
    recent = [h for h in history if h.get('blocked_by') == 'rate_limit']
    if recent:
        print(f'{contact_id}: {len(recent)} rate-limited handoffs')
"
```

**Resolution**:

| Cause | Fix |
|-------|-----|
| GHL API rate limit (10 req/s) | Add request queuing; increase backoff |
| Handoff rate limit (3/hr) | Expected behavior — limits are protective |
| Traffic spike | Enable traffic shaping; add request buffering |
| Bot loop causing rapid requests | Fix circular handoff (see Rule #6) |

---

## General Procedures

### Acknowledging Alerts

Acknowledging a critical alert stops L2/L3 escalation:

```python
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService

alerting = AlertingService()
# Get active alerts
alerts = await alerting.get_active_alerts()
# Acknowledge by alert ID
for alert in alerts:
    alert.acknowledged = True
```

### Checking Escalation Status

```python
alerting = AlertingService()
escalations = alerting.escalation_policy.get_pending_escalations(
    await alerting.get_active_alerts()
)
for esc in escalations:
    print(f"Alert {esc['alert_id']} at Level {esc['level']} - {esc['channels']}")
```

### Silencing Alerts During Maintenance

```python
# Temporarily increase cooldown for all rules
alerting = AlertingService()
for rule in alerting.rules:
    rule.cooldown_seconds = 3600  # 1 hour
# Remember to reset after maintenance
```

### Post-Incident Checklist

After resolving any critical alert:

- [ ] Root cause identified and documented
- [ ] Fix applied and verified
- [ ] Alert acknowledged / resolved
- [ ] Performance metrics back to baseline
- [ ] Incident summary sent to team
- [ ] Runbook updated if new failure mode discovered

---

## Environment Variable Quick Reference

| Variable | Purpose |
|----------|---------|
| `ALERTING_ENABLED` | Master switch for all alerting |
| `ALERT_EMAIL_SMTP_HOST` | SMTP server for email alerts |
| `ALERT_EMAIL_SMTP_PORT` | SMTP port (default: 587) |
| `ALERT_EMAIL_SMTP_USER` | SMTP username |
| `ALERT_EMAIL_SMTP_PASSWORD` | SMTP password |
| `ALERT_EMAIL_FROM` | From address for email alerts |
| `ALERT_EMAIL_TO` | Comma-separated recipients |
| `ALERT_SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `ALERT_WEBHOOK_URL` | Generic webhook endpoint |
| `ALERT_WEBHOOK_PAGERDUTY_URL` | PagerDuty Events API v2 endpoint |
| `ALERT_WEBHOOK_PAGERDUTY_API_KEY` | PagerDuty integration/routing key |
| `ALERT_WEBHOOK_OPSGENIE_URL` | Opsgenie Alerts API endpoint |
| `ALERT_WEBHOOK_OPSGENIE_API_KEY` | Opsgenie GenieKey |

---

## Related Documentation

- [Deployment Checklist](JORGE_BOT_DEPLOYMENT_CHECKLIST.md)
- [Integration Guide](JORGE_BOT_INTEGRATION_GUIDE.md)
- [Alert Channels Deployment Guide](ALERT_CHANNELS_DEPLOYMENT_GUIDE.md)
- [Performance Baseline Report](JORGE_BOT_PERFORMANCE_BASELINE_FEB_2026.md)
- [Incident Response Playbook](../../docs/INCIDENT_RESPONSE_PLAYBOOK.md)

---

**Document Version:** 1.0
**Last Updated:** February 8, 2026
**Next Review:** After first production incident or within 30 days
