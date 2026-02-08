# Jorge Bot Deployment Checklist

**Version:** 8.3
**Date:** February 8, 2026
**Scope:** Production Deployment of Jorge Bot Services

---

## Pre-Deployment Checklist

### Environment Variables

| Variable | Required | Description | Status |
|----------|----------|-------------|--------|
| `DATABASE_URL` | Yes | PostgreSQL connection string | ☐ |
| `REDIS_URL` | Yes | Redis connection string | ☐ |
| `GHL_API_KEY` | Yes | GoHighLevel API key | ☐ |
| `GHL_LOCATION_ID` | Yes | GHL location ID | ☐ |
| `CLAUDE_API_KEY` | Yes | Claude API key | ☐ |
| `ALERTING_ENABLED` | Yes | Enable/disable alerting | ☐ |
| `ALERT_EMAIL_SMTP_HOST` | Yes* | SMTP server host | ☐ |
| `ALERT_EMAIL_SMTP_PORT` | Yes* | SMTP server port | ☐ |
| `ALERT_EMAIL_SMTP_USER` | Yes* | SMTP username | ☐ |
| `ALERT_EMAIL_SMTP_PASSWORD` | Yes* | SMTP password | ☐ |
| `ALERT_EMAIL_FROM` | Yes* | From email address | ☐ |
| `ALERT_EMAIL_TO` | Yes* | Comma-separated recipients | ☐ |
| `ALERT_SLACK_WEBHOOK_URL` | Yes* | Slack webhook URL | ☐ |
| `ALERT_WEBHOOK_URL` | No | Custom webhook URL | ☐ |
| `AB_TESTING_ENABLED` | Yes | Enable/disable A/B testing | ☐ |
| `PERFORMANCE_TRACKING_ENABLED` | Yes | Enable performance tracking | ☐ |
| `BOT_METRICS_ENABLED` | Yes | Enable bot metrics | ☐ |

*Required if alerting is enabled

### Database Preparation

- [ ] PostgreSQL database created
- [ ] Redis instance running
- [ ] Database migrations applied:
  ```bash
  alembic upgrade head
  ```
- [ ] A/B testing tables created
- [ ] Database connection verified:
  ```bash
  python -c "from ghl_real_estate_ai.database import get_db; print('OK')"
  ```

### Code Readiness

- [ ] All tests passing:
  ```bash
  pytest ghl_real_estate_ai/tests/ -v --tb=short
  ```
- [ ] Test coverage >85%:
  ```bash
  pytest --cov=ghl_real_estate_ai --cov-report=term-missing
  ```
- [ ] No linting errors:
  ```bash
  flake8 ghl_real_estate_ai/services/jorge/
  ```
- [ ] Type checking passed:
  ```bash
  mypy ghl_real_estate_ai/services/jorge/
  ```

### Alert Channel Configuration

- [ ] Email alerts configured and tested
- [ ] Slack webhook configured and tested
- [ ] Custom webhook configured (if used)
- [ ] Alert channels verified:
  ```bash
  python ghl_real_estate_ai/tests/jorge/test_all_channels.py --mock
  ```

### Monitoring Setup

- [ ] Grafana dashboards imported
- [x] Alert rules configured in AlertingService (7 rules, P5 complete)
- [ ] On-call rotation established
- [x] Escalation policy documented (3-level, see [On-Call Runbook](JORGE_BOT_ON_CALL_RUNBOOK.md))

---

## Deployment Steps

### Step 1: Staging Deployment

```bash
# 1. Checkout staging branch
git checkout staging

# 2. Pull latest changes
git pull origin staging

# 3. Deploy containers
docker-compose -f docker-compose.staging.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.staging.yml exec app alembic upgrade head

# 5. Verify health
curl https://staging.enterprisehub.com/health
```

### Step 2: Smoke Tests

```bash
# Run smoke tests
pytest ghl_real_estate_ai/tests/smoke/ -v

# Verify specific services
pytest ghl_real_estate_ai/tests/jorge/ -v -k "handoff or alert"
```

### Step 3: Production Deployment

```bash
# 1. Create deployment branch
git checkout -b deploy/jorge-v8.2-$(date +%Y%m%d)

# 2. Tag release
git tag -a v8.2.0 -m "Jorge Bot v8.2 - Production Ready"

# 3. Deploy to production
docker-compose -f docker-compose.production.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.production.yml exec app alembic upgrade head

# 5. Verify health
curl https://enterprisehub.com/health
```

---

## Post-Deployment Verification

### Service Health Checks

```bash
# Check all containers running
docker ps --filter "name=jorge" --format "table {{.Names}}\t{{.Status}}"

# Verify API endpoints
curl -s https://enterprisehub.com/api/v1/jorge/health | jq '.status'
```

### Bot Functionality Tests

| Bot | Endpoint | Expected | Status |
|-----|----------|----------|--------|
| Lead Bot | `/api/v1/jorge/lead/health` | `ok` | ☐ |
| Buyer Bot | `/api/v1/jorge/buyer/health` | `ok` | ☐ |
| Seller Bot | `/api/v1/jorge/seller/health` | `ok` | ☐ |
| Handoff | `/api/v1/jorge/handoff/health` | `ok` | ☐ |

### A/B Testing Verification

```python
# Test experiment creation
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService

ab_service = ABTestingService()
exp_id = await ab_service.create_experiment(
    name="deployment_test",
    variants=["control", "treatment"],
    weights=[0.5, 0.5]
)
assert exp_id is not None
```

### Performance Verification

```python
# Verify SLA compliance
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

tracker = PerformanceTracker()
stats = await tracker.get_all_stats()
for bot, bot_stats in stats.items():
    assert bot_stats['p95'] < 2500, f"{bot} P95 exceeds SLA"
```

### Alert Testing

```python
# Trigger test alert
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService

alerting = AlertingService()
test_alert = alerting.create_test_alert()
await alerting.send_alert(test_alert)
# Verify email/Slack/webhook received
```

---

## Rollback Procedures

### Quick Rollback (Container Level)

```bash
# Stop current containers
docker-compose -f docker-compose.production.yml down

# Start previous version
docker-compose -f docker-compose.production.yml -f docker-compose.production.yml.backup up -d
```

### Database Rollback

```bash
# Rollback one migration
alembic downgrade -1

# Verify rollback
python -c "from ghl_real_estate_ai.models import *; print('Models OK')"
```

### Full Rollback Sequence

```bash
# 1. Stop containers
docker-compose -f docker-compose.production.yml down

# 2. Checkout previous version
git checkout v8.1.0

# 3. Rebuild containers
docker-compose -f docker-compose.production.yml build

# 4. Start containers
docker-compose -f docker-compose.production.yml up -d

# 5. Rollback database
alembic downgrade -1

# 6. Verify
curl https://enterprisehub.com/health
```

---

## Monitoring Checklist

### Real-Time Monitoring

- [ ] Grafana dashboards showing real-time metrics
- [ ] Alert firing for test conditions
- [ ] No errors in application logs

### Log Verification

```bash
# Check for errors
docker logs jorge-api --tail 100 | grep -i error

# Check for warnings
docker logs jorge-api --tail 100 | grep -i warning
```

### Performance Baselines

See [Performance Baseline Report](JORGE_BOT_PERFORMANCE_BASELINE_FEB_2026.md) for full details.

| Metric | Target | Baseline (Feb 2026) | Status |
|--------|--------|---------------------|--------|
| Lead Bot P95 | <1500ms | ~340ms | ✅ |
| Buyer Bot P95 | <1800ms | ~460ms | ✅ |
| Seller Bot P95 | <1800ms | ~460ms | ✅ |
| Handoff P95 | <500ms | ~91ms | ✅ |
| Cache Hit Rate | >70% | Tracked | ✅ |

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| DevOps | | | ☐ |
| QA | | | ☐ |
| Product | | | ☐ |
| Security | | | ☐ |

---

## Troubleshooting

For detailed troubleshooting procedures per alert rule, see the [On-Call Runbook](JORGE_BOT_ON_CALL_RUNBOOK.md).

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Containers not starting | Missing env vars | Check `.env` file |
| Database connection failed | Wrong connection string | Verify `DATABASE_URL` |
| Alerts not sending | SMTP auth failed | Check credentials |
| Handoffs blocked | Rate limit exceeded | Wait for cooldown (3/hr, 10/day) |
| High latency | Cache miss | Check Redis connection |
| Circular handoff spike | Ambiguous intent | Review decoder thresholds |
| Bot unresponsive | Container crash/OOM | `docker restart jorge-api` |

### Debug Commands

```bash
# Check container logs
docker logs jorge-api --tail 500 -f

# Check service health
curl localhost:8000/health

# Check database connectivity
python -c "from ghl_real_estate_ai.database import engine; print(engine.execute('SELECT 1'))"
```

---

**Document Version:** 8.3.0
**Last Updated:** February 8, 2026
**Related Documentation:**
- [On-Call Runbook](JORGE_BOT_ON_CALL_RUNBOOK.md)
- [Performance Baseline Report](JORGE_BOT_PERFORMANCE_BASELINE_FEB_2026.md)
- [Integration Guide](JORGE_BOT_INTEGRATION_GUIDE.md)
- [Alert Channels Deployment Guide](ALERT_CHANNELS_DEPLOYMENT_GUIDE.md)
**Next Review:** After v8.3.0 deployment
