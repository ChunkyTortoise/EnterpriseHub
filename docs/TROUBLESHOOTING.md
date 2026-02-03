# EnterpriseHub Troubleshooting Guide

**Version**: 1.0
**Last Updated**: February 2, 2026

---

## Table of Contents

1. [High Error Rate (>5%)](#issue-1-high-error-rate-5)
2. [Slow Response Times (>500ms)](#issue-2-slow-response-times-500ms)
3. [Database Connection Errors](#issue-3-database-connection-errors)
4. [GHL CRM Sync Failing](#issue-4-ghl-crm-sync-failing)
5. [Memory Leak / OOM Errors](#issue-5-memory-leak--oom-errors)
6. [Feature Flag Not Working](#issue-6-feature-flag-not-working)
7. [Claude API Failures](#issue-7-claude-api-failures)
8. [WebSocket/Socket.IO Disconnections](#issue-8-websocketsocketio-disconnections)
9. [Lead Scheduler Not Running](#issue-9-lead-scheduler-not-running)
10. [Application Fails to Start in Production](#issue-10-application-fails-to-start-in-production)

---

## Issue 1: High Error Rate (>5%)

**Symptoms**: Many API requests failing, Prometheus alerts firing, Slack notifications

### Investigation

```bash
# Check logs for error patterns
kubectl logs -n production -l app=jorge-api --tail=200 | grep ERROR

# Check error monitoring dashboard
curl -H "Authorization: Bearer $API_KEY" \
  https://api.enterprise-hub.com/api/error-monitoring/dashboard

# Check if recent deployment caused it
kubectl rollout history deployment/jorge-api -n production

# Check database connectivity
psql $PROD_DB_URL -c "SELECT NOW()"

# Check Claude API availability
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/messages \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"ping"}]}'

# Check GHL API availability
curl -H "Authorization: Bearer $GHL_API_KEY" \
  https://services.leadconnectorhq.com/contacts/?locationId=$GHL_LOCATION_ID&limit=1
```

### Solutions

| Cause | Solution |
|-------|----------|
| Recent deployment | Rollback: `kubectl patch service jorge-api -p '{"spec":{"selector":{"deployment":"blue"}}}'` |
| Database unreachable | Restart DB pod, check connection pool config |
| Claude API down | Check Anthropic status page, enable circuit breaker fallback |
| GHL API down | Check GHL status, queue failed syncs for retry |
| Code bug | Deploy hotfix, run tests first |

---

## Issue 2: Slow Response Times (>500ms)

**Symptoms**: p95 latency high, users experiencing delays, `X-Performance: slow` header on responses

### Investigation

```bash
# Check database query performance
kubectl exec -it postgres-pod -- psql -c \
  "SELECT query, mean_exec_time, calls FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check cache hit rate (built-in metrics)
kubectl logs -n production -l app=jorge-api | grep "cache_hit_rate"

# Check Claude API response times
kubectl logs -n production -l app=jorge-api | grep "claude_api_duration"

# Check for slow request warnings (auto-logged >500ms)
kubectl logs -n production -l app=jorge-api | grep "Performance alert: Slow request"

# Check per-request timing
curl -v https://api.enterprise-hub.com/api/health 2>&1 | grep "X-Process-Time"
```

### Solutions

| Cause | Solution |
|-------|----------|
| Database slow queries | Add indexes, optimize queries, increase `DB_POOL_SIZE` |
| Low cache hit rate | Increase `SEMANTIC_CACHE_TTL`, increase cache size |
| Claude API slow | Check rate limits, use Haiku model for non-critical queries |
| High concurrent load | Scale pods horizontally, enable async optimization (`ENABLE_ASYNC_OPTIMIZATION=true`) |
| Large response payloads | Verify GZip compression is active (middleware enabled at level 6) |

---

## Issue 3: Database Connection Errors

**Symptoms**: "Connection refused", "Connection timeout", "pool exhausted" in logs

### Investigation

```bash
# Check database pod status
kubectl get pods -n production | grep postgres

# Check database logs
kubectl logs postgres-pod -n production --tail=100

# Check connection pool status
kubectl logs -n production -l app=jorge-api | grep "pool.*exhaust"

# Test connectivity from app pod
kubectl exec -it app-pod -n production -- nc -zv postgres 5432

# Check active connections
psql $PROD_DB_URL -c "SELECT count(*) FROM pg_stat_activity;"
psql $PROD_DB_URL -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
```

### Solutions

| Cause | Solution |
|-------|----------|
| Database pod down | `kubectl rollout restart sts/postgres -n production` |
| Pool exhausted | Increase `DB_POOL_SIZE` (default: 20) and `DB_MAX_OVERFLOW` (default: 10) |
| Idle connection buildup | Kill idle: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < NOW() - interval '5 minutes';` |
| Network partition | Check k8s network policies, DNS resolution |
| Enable connection pooling | Set `ENABLE_DATABASE_CONNECTION_POOLING=true` |

---

## Issue 4: GHL CRM Sync Failing

**Symptoms**: Leads not appearing in GoHighLevel, webhook errors in logs

### Investigation

```bash
# Check webhook processing logs
kubectl logs -n production -l app=jorge-api | grep -i "webhook\|ghl"

# Check GHL API rate limiting (10 req/sec limit)
kubectl logs -n production -l app=jorge-api | grep "rate_limit"

# Verify GHL API key validity
curl -H "Authorization: Bearer $GHL_API_KEY" \
  "https://services.leadconnectorhq.com/locations/$GHL_LOCATION_ID"

# Check webhook signature verification
kubectl logs -n production -l app=jorge-api | grep "signature"

# Verify GHL webhook URL is accessible from the internet
curl -X POST https://api.enterprise-hub.com/api/webhooks/ghl \
  -H "Content-Type: application/json" \
  -d '{"type":"test"}'
```

### Solutions

| Cause | Solution |
|-------|----------|
| Invalid API key | Regenerate in GHL > Settings > API, update `GHL_API_KEY` |
| Rate limited | Reduce request rate, implement exponential backoff (already built into `enhanced_ghl_client.py`) |
| Webhook URL unreachable | Verify DNS, check ingress/nginx config, test with `curl` |
| Webhook signature mismatch | Verify `GHL_WEBHOOK_SECRET` matches GHL config |
| GHL API outage | Check GHL status page, queue failed operations for retry |

---

## Issue 5: Memory Leak / OOM Errors

**Symptoms**: Memory usage climbing over time, pods restarting with OOMKilled status

### Investigation

```bash
# Check current memory usage
kubectl top pods -n production --containers | grep jorge-api

# Check for OOM events
kubectl get events -n production --field-selector reason=OOMKilled

# Check cache sizes in logs
kubectl logs -n production -l app=jorge-api | grep "cache.*size\|memory\|evict"

# Check conversation history buildup
kubectl logs -n production -l app=jorge-api | grep "conversation_history_length"

# Profile memory (development only)
python -m memory_profiler ghl_real_estate_ai/api/main.py
```

### Solutions

| Cause | Solution |
|-------|----------|
| Cache unbounded growth | Adjust LRU eviction threshold (50MB/1000 items configured) |
| Conversation history | Reduce `MAX_CONVERSATION_HISTORY_LENGTH` (default: 20) |
| Pod memory too low | Increase pod memory limits in deployment spec |
| Connection object leaks | Ensure all DB/Redis connections use context managers |
| Enable semantic caching | Set `ENABLE_SEMANTIC_RESPONSE_CACHING=true` to reduce duplicate processing |

---

## Issue 6: Feature Flag Not Working

**Symptoms**: Feature enabled in env vars but behavior unchanged

### Investigation

```bash
# Verify environment variable is set in the running pod
kubectl exec -it jorge-api-pod -n production -- env | grep ENABLE_

# Check if pods picked up the new env vars (restart may be needed)
kubectl describe deployment jorge-api -n production | grep -A5 "Environment"

# Check feature flag code path in logs
kubectl logs -n production -l app=jorge-api | grep "feature_flag\|enable_"

# Verify the config.py loaded the value
kubectl exec -it jorge-api-pod -n production -- python -c \
  "from ghl_real_estate_ai.ghl_utils.config import settings; print(settings.enable_semantic_response_caching)"
```

### Solutions

| Cause | Solution |
|-------|----------|
| Env var not set | `kubectl set env deployment/jorge-api ENABLE_FEATURE=true -n production` |
| Pods not restarted | `kubectl rollout restart deployment/jorge-api -n production` |
| Config caching | Settings are loaded once at import; restart required for changes |
| Typo in env var name | Check exact name in `config.py` (case-insensitive via Pydantic) |
| Feature has dependencies | Check if dependent services (Redis, etc.) are configured |

---

## Issue 7: Claude API Failures

**Symptoms**: Bot responses failing, "Anthropic API error" in logs, lead qualification stalling

### Investigation

```bash
# Check Claude API errors
kubectl logs -n production -l app=jorge-api | grep -i "anthropic\|claude.*error"

# Check rate limiting
kubectl logs -n production -l app=jorge-api | grep "rate_limit\|429"

# Check token usage (may have hit budget)
kubectl logs -n production -l app=jorge-api | grep "token.*budget\|token.*usage"

# Verify API key
kubectl exec -it jorge-api-pod -- python -c \
  "from ghl_real_estate_ai.ghl_utils.config import settings; print(settings.anthropic_api_key[:10])"

# Test API directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

### Solutions

| Cause | Solution |
|-------|----------|
| Rate limited (429) | Implement backoff, reduce concurrent requests, use Haiku for simple tasks |
| API key invalid | Regenerate at console.anthropic.com, update `ANTHROPIC_API_KEY` |
| Token budget exceeded | Increase budget (`TOKEN_BUDGET_DEFAULT_MONTHLY`), or enable progressive skills (`ENABLE_PROGRESSIVE_SKILLS=true` for 68% reduction) |
| Model not available | Fall back to alternative model, check `claude_sonnet_model` vs `claude_haiku_model` |
| Network timeout | Increase `CLAUDE_TIMEOUT` (default: 30s), check DNS resolution |

---

## Issue 8: WebSocket/Socket.IO Disconnections

**Symptoms**: BI dashboard loses real-time updates, reconnection warnings in browser console

### Investigation

```bash
# Check WebSocket service status
kubectl logs -n production -l app=jorge-api | grep -i "websocket\|socket.io"

# Check connection counts
curl -H "Authorization: Bearer $API_KEY" \
  https://api.enterprise-hub.com/api/websocket/performance

# Check nginx/ingress WebSocket config
kubectl get ingress -n production -o yaml | grep -i "websocket\|upgrade"

# Check for connection limit exhaustion
kubectl logs -n production -l app=jorge-api | grep "max_connections\|connection.*limit"
```

### Solutions

| Cause | Solution |
|-------|----------|
| Nginx not forwarding upgrades | Add `proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";` |
| Load balancer timeout | Set WebSocket idle timeout to >60s on LB |
| Too many connections | Increase `WEBSOCKET_MAX_QUEUE` (default: 32) |
| Client reconnection failing | Check `WEBSOCKET_RECONNECT_ATTEMPTS` (default: 5) and `WEBSOCKET_RECONNECT_DELAY` (default: 2s) |
| Fallback not working | Enable `WEBSOCKET_FALLBACK_TO_POLLING=true` for polling fallback |

---

## Issue 9: Lead Scheduler Not Running

**Symptoms**: 3-7-30 day follow-up sequences not executing, no automated touchpoints

### Investigation

```bash
# Check scheduler startup logs
kubectl logs -n production -l app=jorge-api | grep -i "scheduler\|sequence"

# Look for startup errors
kubectl logs -n production -l app=jorge-api | grep "Lead Sequence Scheduler"

# Check if scheduler was initialized
kubectl logs -n production -l app=jorge-api | grep "initialize_lead_scheduler"
```

### Solutions

| Cause | Solution |
|-------|----------|
| Startup exception | Check `scheduler_startup.py` logs, fix initialization error |
| Database not available at startup | Ensure DB is ready before app starts (use k8s init containers) |
| Missing Twilio/SendGrid config | Set `TWILIO_ACCOUNT_SID`, `SENDGRID_API_KEY` for SMS/email sequences |
| Scheduler silently failed | Restart pod; scheduler initializes during FastAPI lifespan startup |

---

## Issue 10: Application Fails to Start in Production

**Symptoms**: Pod in CrashLoopBackOff, application exits immediately

### Investigation

```bash
# Check pod status and events
kubectl describe pod jorge-api-xxx -n production

# Check application logs before crash
kubectl logs jorge-api-xxx -n production --previous

# Look for security validation failures
kubectl logs jorge-api-xxx -n production --previous | grep "CRITICAL SECURITY ERROR"
```

### Common Causes

The application performs strict validation in production mode (`ENVIRONMENT=production`):

1. **Missing JWT_SECRET_KEY** -> App exits with:
   ```
   CRITICAL SECURITY ERROR: JWT_SECRET_KEY is required in production
   ```
   Fix: `export JWT_SECRET_KEY=$(openssl rand -hex 32)`

2. **Weak JWT_SECRET_KEY** (<32 chars) -> App exits with:
   ```
   CRITICAL SECURITY ERROR: JWT_SECRET_KEY is too weak
   ```
   Fix: Generate a longer key with `openssl rand -hex 32`

3. **Missing GHL_WEBHOOK_SECRET** -> App exits with:
   ```
   SECURITY ERROR: GHL_WEBHOOK_SECRET is required in production
   ```
   Fix: `export GHL_WEBHOOK_SECRET=$(openssl rand -hex 32)`

4. **Missing REDIS_PASSWORD** -> App exits with:
   ```
   SECURITY ERROR: REDIS_PASSWORD is required in production
   ```
   Fix: Set Redis password to match your Redis server config

5. **Invalid ANTHROPIC_API_KEY format** -> Warning but continues:
   ```
   WARNING: Anthropic API key should start with 'sk-ant-'
   ```

6. **Missing required env vars** -> Pydantic validation error:
   ```
   ValidationError: anthropic_api_key / ghl_api_key / ghl_location_id field required
   ```
   Fix: Ensure all required variables from `.env.example` are set

---

## General Debugging Commands

```bash
# Pod status and events
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
kubectl get events -n production --sort-by='.lastTimestamp'

# Logs (current and previous crash)
kubectl logs <pod-name> -n production
kubectl logs <pod-name> -n production --previous

# Interactive shell in pod
kubectl exec -it <pod-name> -n production -- /bin/bash

# Port-forward for local debugging
kubectl port-forward svc/jorge-api 8000:8000 -n production

# Resource usage
kubectl top pods -n production
kubectl top nodes
```

---

**Version**: 1.0 | **Last Updated**: February 2, 2026
