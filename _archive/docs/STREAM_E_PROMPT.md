# Stream E: Documentation & Deployment
**Chat Purpose**: Create deployment documentation and operational guides  
**Duration**: 2-3 hours  
**Priority**: MEDIUM (runs after A-D)  
**Status**: Ready to begin

---

## Your Mission

Create comprehensive documentation for deploying Jorge bots to production. This includes:
1. API specification (OpenAPI/Swagger)
2. Deployment runbooks (staging + production)
3. Monitoring & alerting setup
4. Troubleshooting guides
5. Feature flag documentation
6. Operational runbooks

This ensures the system is production-grade and maintainable.

**Files You'll Create**:
- `docs/API_SPEC.md` (NEW - OpenAPI documentation)
- `docs/DEPLOYMENT.md` (Enhancement - runbooks)
- `docs/MONITORING.md` (NEW - alerts + dashboards)
- `docs/TROUBLESHOOTING.md` (NEW - common issues)
- `docs/FEATURE_FLAGS.md` (NEW - feature management)
- `.env.example` (Configuration template)

---

## 1. API Specification

**Purpose**: Document all endpoints, parameters, responses for developers and integrators

**File**: `docs/API_SPEC.md`

**Sections to Include**:

### 1.1 Authentication
```markdown
## Authentication

### API Key Authentication
All requests require an API key in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.enterprise-hub.com/v1/...
```

### JWT Token
For interactive sessions, use JWT tokens:

```bash
POST /v1/auth/token
{
  "api_key": "YOUR_API_KEY",
  "expires_in": 3600
}

Response:
{
  "token": "eyJhbGc...",
  "expires_at": "2026-02-02T15:30:00Z"
}
```

### Rate Limiting
- 100 requests/minute per API key
- 1,000 requests/minute per organization
- Burst: 10 requests/second

Headers:
- `X-RateLimit-Limit`: 100
- `X-RateLimit-Remaining`: 85
- `X-RateLimit-Reset`: 1643820600
```

### 1.2 Lead Qualification Endpoints

```markdown
## Lead Qualification

### POST /v1/leads/qualify
Initiate lead qualification flow

**Request**:
```json
{
  "lead_id": "string",
  "name": "string",
  "phone": "+1-555-0100",
  "email": "lead@example.com",
  "message": "I'm interested in buying",
  "property_address": "string (optional)"
}
```

**Response** (201 Created):
```json
{
  "qualification_id": "qual-abc123",
  "lead_id": "lead-001",
  "status": "in_progress",
  "intent": "buyer_intent",
  "temperature": "hot",
  "next_action": "Schedule showing",
  "schedule_showing_url": "https://...",
  "created_at": "2026-02-02T10:00:00Z",
  "expires_at": "2026-02-09T10:00:00Z"
}
```

**Error Responses**:
- 400 Bad Request: Invalid phone format
- 409 Conflict: Lead already in qualification
- 429 Too Many Requests: Rate limit exceeded
- 500 Internal Server Error: Service error

### GET /v1/leads/{lead_id}/qualification
Get qualification status

**Response**:
```json
{
  "qualification_id": "qual-abc123",
  "status": "completed",
  "result": {
    "intent": "buyer_intent",
    "temperature": "hot",
    "financial_readiness": {
      "pre_approved": true,
      "budget_min": 600000,
      "budget_max": 800000,
      "confidence": 0.95
    },
    "property_preferences": {
      "bedrooms": 3,
      "neighborhood": "Victoria",
      "price_range": "600k-800k"
    }
  },
  "recommended_properties": [
    {
      "id": "prop-001",
      "address": "123 Main St, RC, CA",
      "price": 725000,
      "beds": 3,
      "match_score": 0.92
    }
  ]
}
```
```

### 1.3 Buyer Matching Endpoints

```markdown
## Buyer Matching

### POST /v1/buyers/match-properties
Find properties matching buyer preferences

**Request**:
```json
{
  "buyer_id": "buyer-001",
  "budget_min": 600000,
  "budget_max": 800000,
  "bedrooms": [3, 4],
  "neighborhoods": ["Victoria", "Haven"],
  "sort_by": "relevance"  // or "price", "distance"
}
```

**Response**:
```json
{
  "match_session_id": "match-xyz789",
  "buyer_id": "buyer-001",
  "total_matches": 12,
  "matches": [
    {
      "rank": 1,
      "property": {...},
      "match_score": 0.95,
      "explanation": "Perfect match: 3BR, $725k, Victoria"
    }
  ],
  "next_actions": ["Schedule showing", "Request CMA"]
}
```

### GET /v1/buyers/{buyer_id}/preferences
Get stored buyer preferences

### PUT /v1/buyers/{buyer_id}/preferences
Update buyer preferences
```

### 1.4 Seller Analysis Endpoints

```markdown
## Seller Analysis

### POST /v1/sellers/analyze
Analyze property and generate CMA

**Request**:
```json
{
  "seller_id": "seller-001",
  "property_address": "456 Oak Ave, Rancho Cucamonga, CA",
  "bedrooms": 4,
  "bathrooms": 2.5,
  "square_feet": 2500,
  "condition": "good",
  "list_price": 850000
}
```

**Response**:
```json
{
  "analysis_id": "anal-001",
  "cma": {
    "market_analysis": {...},
    "comparable_properties": [...],
    "price_recommendation": {
      "low": 820000,
      "mid": 850000,
      "high": 880000,
      "confidence": 0.92
    }
  },
  "market_conditions": "Strong buyer market",
  "recommendations": [...]
}
```

### POST /v1/sellers/{seller_id}/schedule-consultation
Schedule seller consultation
```

### 1.5 Webhook Endpoints

```markdown
## Webhooks

### Register Webhook
POST /v1/webhooks/register

**Request**:
```json
{
  "url": "https://your-domain.com/webhooks/jorge",
  "events": ["lead.qualified", "buyer.matched", "seller.analyzed"],
  "secret": "your-webhook-secret"
}
```

### Webhook Events

#### lead.qualified
Fired when lead qualification completes

```json
{
  "event": "lead.qualified",
  "timestamp": "2026-02-02T10:00:00Z",
  "data": {
    "lead_id": "lead-001",
    "qualification_id": "qual-001",
    "intent": "buyer_intent",
    "temperature": "hot"
  }
}
```

#### buyer.matched
Fired when properties matched to buyer

#### seller.analyzed
Fired when seller analysis completes
```

### 1.6 Rate Limits & Quotas

```markdown
## Rate Limits

### Per API Key
- 100 requests/minute (burst: 10/sec)
- 10,000 requests/day

### Per Organization
- 1,000 requests/minute
- 100,000 requests/day

### Per Endpoint
- Lead qualification: 1,000/day
- Buyer matching: 5,000/day
- Seller analysis: 1,000/day

### Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1643820600
```

When rate limited (429):
```json
{
  "error": "rate_limit_exceeded",
  "message": "100 requests per minute limit exceeded",
  "retry_after": 30
}
```
```

---

## 2. Deployment Runbook

**Purpose**: Step-by-step guide for deploying to staging and production

**File**: `docs/DEPLOYMENT.md`

**Sections**:

### 2.1 Pre-Deployment Checklist

```markdown
## Pre-Deployment Checklist

### Code Readiness
- [ ] All tests passing (pytest tests/ -v)
- [ ] Code review approved
- [ ] No critical security issues
- [ ] No secrets in code (.env only)
- [ ] Lint passes (flake8, mypy)

### Configuration
- [ ] Environment variables configured
- [ ] API keys set (Claude, GHL, Stripe, etc.)
- [ ] Database migrations ready
- [ ] Feature flags reviewed
- [ ] Monitoring alerts configured

### Testing
- [ ] Unit tests: 20/20 passing
- [ ] Integration tests: All passing
- [ ] Load test: 100 users, <5% error
- [ ] Smoke test: Basic flows work
- [ ] API endpoints responding

### Documentation
- [ ] API spec updated
- [ ] Changelog updated
- [ ] Deployment notes prepared
- [ ] Rollback plan documented
```

### 2.2 Staging Deployment

```markdown
## Staging Deployment (Non-Production)

### Prerequisites
```bash
# Ensure clean working directory
git status  # Should be clean

# Pull latest
git pull origin main

# Create release branch
git checkout -b deploy/staging-2026-02-02
```

### Build & Deploy

```bash
# Step 1: Build Docker image
docker build -t enterprise-hub:staging-$(date +%s) .

# Step 2: Push to registry
docker push registry.example.com/enterprise-hub:staging

# Step 3: Deploy to staging
kubectl set image deployment/jorge-api \
  jorge-api=registry.example.com/enterprise-hub:staging \
  -n staging

# Step 4: Monitor rollout
kubectl rollout status deployment/jorge-api -n staging

# Step 5: Run smoke tests
./scripts/smoke_test.sh staging

# Step 6: Monitor metrics
# Check Grafana dashboard for errors, latency
```

### Post-Deployment Verification

```bash
# Check deployment status
kubectl get pods -n staging

# View logs
kubectl logs -n staging -l app=jorge-api --tail=100

# Test API endpoints
curl -H "Authorization: Bearer $STAGING_API_KEY" \
  https://staging-api.enterprise-hub.com/v1/health

# Verify database migrations
psql $STAGING_DB_URL -c "\dt"  # Check tables exist

# Confirm features working
curl -X POST https://staging-api.enterprise-hub.com/v1/leads/qualify \
  -H "Authorization: Bearer $STAGING_API_KEY" \
  -d '{"lead_id": "test", ...}'
```

### Staging Validation (2-4 hours)

- [ ] API endpoints responding (200)
- [ ] Database queries working
- [ ] Claude API integration working
- [ ] GHL CRM sync working
- [ ] WebSockets (if applicable) working
- [ ] Performance: <200ms p95
- [ ] Error rate: <1%
- [ ] No critical errors in logs
```

### 2.3 Production Deployment

```markdown
## Production Deployment (High Availability)

### Blue-Green Strategy

**Blue** = Current production (stable)
**Green** = New deployment (being tested)

### Prerequisites
- [ ] Staging deployment stable for 4+ hours
- [ ] No critical issues found
- [ ] Team approval obtained
- [ ] On-call support ready
- [ ] Rollback tested

### Deployment Steps

```bash
# Step 1: Create green deployment
kubectl create deployment jorge-api-green \
  --image=registry.example.com/enterprise-hub:v1.0.0 \
  -n production

# Step 2: Wait for rollout
kubectl rollout status deployment/jorge-api-green -n production

# Step 3: Run smoke tests on green
./scripts/smoke_test.sh green

# Step 4: Canary: Route 5% traffic to green
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"deployment":"green"}}}'
  
# Monitor for 10 minutes
# - Check error rate (should be <1%)
# - Check latency (should be <200ms p95)
# - Check logs for issues

# Step 5: Full cutover (if canary OK)
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"version":"v1.0.0"}}}'

# Step 6: Monitor green for 30 minutes
watch -n 5 'kubectl get pods -n production'

# Step 7: If stable, mark blue as old
kubectl label deployment jorge-api-blue \
  deprecated=true -n production
```

### Production Monitoring (Post-Deploy)

```bash
# Real-time monitoring
watch 'kubectl logs -n production -l app=jorge-api --tail=50'

# Metrics dashboard
open https://grafana.example.com/d/jorge-bots

# Alert on critical metrics
# - Error rate > 5%
# - Response time > 500ms p95
# - API key failures
# - Database connection errors
```

### Rollback Procedure (If Issues)

```bash
# Immediate rollback to blue
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"deployment":"blue"}}}'

# Verify traffic routed to blue
kubectl get endpoints jorge-api

# Monitor logs
kubectl logs -n production -f

# Investigate green deployment
kubectl logs deployment/jorge-api-green -n production

# Delete failed green deployment
kubectl delete deployment jorge-api-green -n production
```
```

---

## 3. Monitoring & Alerting

**File**: `docs/MONITORING.md`

### 3.1 Key Metrics

```markdown
## Key Metrics to Monitor

### Application Health
- Error rate: <5% (alert if >5%)
- Response time p95: <200ms (alert if >300ms)
- Response time p99: <500ms (alert if >750ms)
- Request throughput: >100 req/sec (alert if <50)

### Database
- Query time p95: <50ms (alert if >100ms)
- Connection pool: <80% (alert if >90%)
- Active queries: <20 (alert if >40)
- Long-running queries: 0 (alert if >3)

### Cache
- Hit rate: >70% (alert if <60%)
- Memory: <80% (alert if >85%)
- Eviction rate: <1% (alert if >2%)

### External Services
- Claude API: <99% (alert if <98%)
- GHL CRM: <99.5% (alert if <99%)
- Database: <99.9% (alert if <99.8%)

### Business Metrics
- Leads qualified: >100/day
- Buyers matched: >50/day
- Sellers analyzed: >20/day
- Conversion rate: >15%
```

### 3.2 Prometheus Queries

```markdown
## Prometheus Monitoring Queries

### Error Rate
```
rate(jorge_api_errors_total[5m]) / rate(jorge_api_requests_total[5m]) * 100
```

Alert if >5%

### Response Time p95
```
histogram_quantile(0.95, rate(jorge_api_duration_seconds_bucket[5m]))
```

Alert if >0.2s (200ms)

### Cache Hit Rate
```
rate(jorge_cache_hits_total[5m]) / (rate(jorge_cache_hits_total[5m]) + rate(jorge_cache_misses_total[5m])) * 100
```

Alert if <60%

### Database Connections
```
jorge_db_pool_active_connections / jorge_db_pool_max_connections * 100
```

Alert if >80%
```

### 3.3 Grafana Dashboard

```markdown
## Grafana Dashboard Setup

Create dashboard: "Jorge Bots Production"

Panels:
1. **Error Rate** (gauge)
   - Current 5-min error rate
   - Alert line at 5%
   
2. **Response Time** (graph)
   - p50, p95, p99 lines
   - Alert zone shaded above 300ms

3. **Throughput** (graph)
   - Requests per second
   - Alert if below 100 req/sec

4. **Cache Hit Rate** (gauge)
   - Current hit rate percentage
   - Alert if <60%

5. **Database Queries** (graph)
   - Query time distribution
   - Alert line at 100ms

6. **External Services** (status)
   - Claude API availability
   - GHL CRM availability
   - Database availability

7. **Business Metrics** (counters)
   - Leads qualified (today)
   - Buyers matched (today)
   - Sellers analyzed (today)

8. **Alerts** (table)
   - Active alerts
   - Severity level
   - Triggered time
```

---

## 4. Troubleshooting Guide

**File**: `docs/TROUBLESHOOTING.md`

### 4.1 Common Issues

```markdown
## Troubleshooting Guide

### Issue 1: High Error Rate (>5%)

**Symptoms**: Many requests failing, alerts firing

**Investigation**:
```bash
# Check logs for errors
kubectl logs -n production -l app=jorge-api | grep ERROR

# Check specific error type
kubectl logs -n production -l app=jorge-api | grep "lead qualification error"

# Check recent deployment
kubectl rollout history deployment/jorge-api -n production

# Check database connectivity
psql $PROD_DB_URL -c "SELECT NOW()"

# Check Claude API
curl -H "Authorization: Bearer $CLAUDE_API_KEY" \
  https://api.anthropic.com/v1/models
```

**Solutions**:
1. If database issue: Check connection pool, restart pods
2. If Claude API issue: Check quota, API key, rate limits
3. If recent deployment: Rollback to previous version
4. If code issue: Deploy fix, run tests first

### Issue 2: Slow Response Times (>500ms)

**Symptoms**: p95 latency high, users experiencing delays

**Investigation**:
```bash
# Check database query performance
kubectl exec -it postgres-pod -- psql -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Check cache hit rate
kubectl logs -n production | grep "cache_hit_rate"

# Check Claude API response times
kubectl logs -n production | grep "claude_api_duration"

# Profile hot paths
python -m cProfile -o profile.prof app.py
# (Run under controlled load, analyze)
```

**Solutions**:
1. If database slow: Add index, optimize query, increase replicas
2. If cache low: Increase cache size, adjust TTL
3. If Claude API slow: Check rate limits, use Progressive Skills
4. If algorithm slow: Optimize with profiling data

### Issue 3: Database Connection Errors

**Symptoms**: "Connection refused", "Connection timeout"

**Investigation**:
```bash
# Check database pod
kubectl get pods -n production | grep postgres

# Check database logs
kubectl logs postgres-pod -n production

# Check connection pool
kubectl logs -n production | grep "pool.*exhausted"

# Test connectivity
kubectl exec -it app-pod -- nc -zv postgres:5432
```

**Solutions**:
1. Restart database pod: `kubectl rollout restart sts/postgres`
2. Increase connection pool: Update config, redeploy
3. Kill idle connections: `SELECT pg_terminate_backend(pid) ...`
4. Scale database: Add read replicas

### Issue 4: GHL CRM Sync Failing

**Symptoms**: Leads not syncing to CRM, webhook errors

**Investigation**:
```bash
# Check webhook logs
kubectl logs -n production | grep "webhook"

# Check GHL API status
curl https://api.gohighlevel.com/v1/status

# Check rate limiting
kubectl logs -n production | grep "rate_limit"

# Verify credentials
grep "GHL_API_KEY" .env | wc -c  # Should be non-zero
```

**Solutions**:
1. Verify GHL API key is valid
2. Check rate limit: 10 req/sec, implement backoff
3. Verify webhook URL is accessible
4. Check GHL API status page
5. Implement retry queue: failed syncs retry with backoff

### Issue 5: Memory Leak / OOM Errors

**Symptoms**: Memory usage growing, pods crashing with OOM

**Investigation**:
```bash
# Check memory usage trend
kubectl top pods -n production --containers | grep jorge-api

# Check cache size
kubectl logs -n production | grep "cache.*size"

# Check for leaks
ps aux | grep python | grep -v grep  # Check resident memory

# Profile memory
python -m memory_profiler app.py
```

**Solutions**:
1. Restart pods: Forces garbage collection
2. Reduce cache size: Adjust LRU eviction threshold
3. Fix memory leak: Profile, identify leak, patch
4. Increase pod memory: Update deployment spec
5. Enable memory monitoring: Add memory metrics

### Issue 6: Feature Flag Not Working

**Symptoms**: Feature enabled but not activating, or causing errors

**Investigation**:
```bash
# Check environment variable
kubectl get deployment jorge-api -o yaml | grep ENABLE_

# Check feature flag code path
kubectl logs -n production | grep "feature_flag"

# Verify feature implementation
grep -r "enable_progressive_skills" ghl_real_estate_ai/

# Test feature directly
curl -X POST https://api.example.com/v1/test-feature \
  -H "Feature-Flag: progressive_skills=true"
```

**Solutions**:
1. Verify environment variable is set: `kubectl set env`
2. Restart pods to pick up new env vars
3. Check feature implementation for bugs
4. Disable feature: Set flag to false
5. Check for feature conflicts

```

---

## 5. Feature Flags Documentation

**File**: `docs/FEATURE_FLAGS.md`

```markdown
# Feature Flags Configuration

## Overview
Feature flags allow runtime control of optional features without redeployment.

## Available Flags

### ENABLE_PROGRESSIVE_SKILLS
**Status**: Recommended
**Benefit**: 68% token reduction
**Default**: false
**Performance Impact**: -30% response time, -68% token usage

Enable:
```bash
export ENABLE_PROGRESSIVE_SKILLS=true
```

### ENABLE_AGENT_MESH
**Status**: Advanced
**Benefit**: Multi-agent orchestration, cost optimization
**Default**: false
**Performance Impact**: +10% response time, -25% cost

Enable:
```bash
export ENABLE_AGENT_MESH=true
export AGENT_MESH_ROUTING=cost_aware
```

### ENABLE_MCP_INTEGRATION
**Status**: Experimental
**Benefit**: Standardized external services
**Default**: false
**Performance Impact**: None (same as direct integration)

Enable:
```bash
export ENABLE_MCP_INTEGRATION=true
```

## Environment Variables

```bash
# Core features
ENABLE_PROGRESSIVE_SKILLS=true
ENABLE_AGENT_MESH=true
ENABLE_MCP_INTEGRATION=false

# Progressive Skills config
PROGRESSIVE_SKILLS_MODEL=claude-3-5-sonnet
PROGRESSIVE_SKILLS_CACHE_TTL=3600

# Agent Mesh config
AGENT_MESH_ROUTING=cost_aware
AGENT_MESH_LOAD_BALANCE=true

# Monitoring
LOG_FEATURE_USAGE=true
TRACK_TOKEN_SAVINGS=true
```

## Rollback Procedure

If a feature causes issues:

```bash
# Disable feature
kubectl set env deployment/jorge-api ENABLE_FEATURE_FLAG=false

# Restart pods
kubectl rollout restart deployment/jorge-api

# Monitor
kubectl logs -n production -f
```
```

---

## 6. Configuration Template

**File**: `.env.example`

```env
# === Application ===
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# === Database ===
DATABASE_URL=postgresql://user:password@db:5432/enterprise_hub
DATABASE_POOL_SIZE=20
DATABASE_ECHO_SQL=false

# === Claude API ===
ANTHROPIC_API_KEY=sk-...
CLAUDE_MODEL=claude-opus-4-5
CLAUDE_TIMEOUT=30

# === GHL CRM ===
GHL_API_KEY=...
GHL_API_URL=https://api.gohighlevel.com/v1
GHL_RATE_LIMIT=10

# === Stripe ===
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# === Redis Cache ===
REDIS_URL=redis://redis:6379
REDIS_DB=0
CACHE_TTL=3600

# === Feature Flags ===
ENABLE_PROGRESSIVE_SKILLS=false
ENABLE_AGENT_MESH=false
ENABLE_MCP_INTEGRATION=false

# === Monitoring ===
PROMETHEUS_ENABLED=true
LOG_TO_STDOUT=true
SENTRY_DSN=https://...

# === Deployment ===
API_PORT=8000
WORKERS=4
WORKERS_PER_CORE=1
```

---

## Implementation Checklist

### API Specification (1 hour)
- [ ] Document all endpoints
- [ ] Include request/response examples
- [ ] Document error codes
- [ ] Document rate limits
- [ ] Document webhooks
- [ ] Review for clarity

### Deployment Runbook (45 minutes)
- [ ] Pre-deployment checklist
- [ ] Staging deployment steps
- [ ] Production deployment (blue-green)
- [ ] Rollback procedures
- [ ] Verification steps
- [ ] Test in staging

### Monitoring (45 minutes)
- [ ] Define key metrics
- [ ] Create Prometheus queries
- [ ] Design Grafana dashboard
- [ ] Setup alerts
- [ ] Document alert responses
- [ ] Test alerts

### Troubleshooting (30 minutes)
- [ ] Document common issues
- [ ] Provide investigation steps
- [ ] Document solutions
- [ ] Create runbooks for each issue
- [ ] Test troubleshooting steps

### Configuration (15 minutes)
- [ ] Create .env.example
- [ ] Document all variables
- [ ] Document feature flags
- [ ] Create setup guide

---

## Success Criteria Checklist

- [ ] API spec complete and reviewed
- [ ] Deployment procedures documented
- [ ] Staging deployment tested successfully
- [ ] Monitoring setup complete with working alerts
- [ ] Troubleshooting guide covers 6+ common issues
- [ ] Feature flag documentation complete
- [ ] Configuration template (`.env.example`) created
- [ ] All documentation reviewed for clarity
- [ ] Runbooks tested by another team member
- [ ] Ready for production deployment

---

## Quick Reference

### Deploy to Staging
```bash
git checkout -b deploy/staging
git push origin deploy/staging
# Automated: Docker build → Push → Deploy
# Manual verification: 15 minutes
```

### Deploy to Production
```bash
git tag v1.0.0
git push origin v1.0.0
# Automated: Build → Push → Blue/Green Deploy
# Monitoring: 30 minutes post-deploy
```

### Rollback Production
```bash
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"deployment":"blue"}}}'
```

### Check Status
```bash
kubectl get deployments -n production
kubectl logs -n production -f
open https://grafana.example.com/d/jorge-bots
```

---

**Ready to start? Begin with API spec documentation!**

**Estimated completion**: 2-3 hours  
**Due by**: After Streams A-D  
**Parallel work possible**: Documentation can be written while tests run
