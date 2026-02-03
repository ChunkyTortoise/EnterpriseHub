# EnterpriseHub Deployment Guide

**Last Updated**: February 2, 2026
**Version**: 2.0

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Staging Deployment](#staging-deployment)
5. [Production Deployment](#production-deployment)
6. [Rollback Procedures](#rollback-procedures)
7. [Database Migrations](#database-migrations)
8. [Post-Deployment Verification](#post-deployment-verification)

---

## Pre-Deployment Checklist

Complete all items before deploying to any environment.

### Code Readiness

- [ ] All tests passing: `pytest tests/ -v`
- [ ] No critical security issues
- [ ] No secrets in code (`.env` only, validated by `config.py`)
- [ ] Lint passes: `flake8 ghl_real_estate_ai/`
- [ ] Type checks pass: `mypy ghl_real_estate_ai/`
- [ ] Code review approved (PR merged to `main`)

### Configuration

- [ ] Environment variables configured (see `.env.example`)
- [ ] API keys set: `ANTHROPIC_API_KEY`, `GHL_API_KEY`, `GHL_LOCATION_ID`
- [ ] Database URL configured: `DATABASE_URL`
- [ ] Redis configured: `REDIS_URL`, `REDIS_PASSWORD`
- [ ] JWT secret set: `JWT_SECRET_KEY` (32+ characters, validated at startup)
- [ ] Webhook secret set: `GHL_WEBHOOK_SECRET` (32+ characters)
- [ ] Feature flags reviewed (see `docs/FEATURE_FLAGS.md`)
- [ ] Monitoring alerts configured

### Testing

- [ ] Unit tests passing: `pytest tests/agents/ -v`
- [ ] Integration tests passing: `pytest tests/integration/test_full_jorge_flow.py -v` (18/18)
- [ ] Performance baselines: `pytest tests/performance/test_response_times.py -v`
- [ ] Load test: `pytest tests/load/test_concurrent_load.py -v` (100 concurrent users, <5% error rate)
- [ ] Smoke test: Core flows (lead qualification, buyer matching, seller analysis)
- [ ] API endpoints responding: `/api/health/` returns 200
- [ ] Full Stream D validation: `pytest tests/load/ tests/performance/test_response_times.py tests/integration/test_full_jorge_flow.py -v`

### Documentation

- [ ] API spec updated (`docs/API_SPEC.md`)
- [ ] Changelog updated
- [ ] Deployment notes prepared
- [ ] Rollback plan documented

---

## Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start

```bash
# Clone repository
git clone https://github.com/ChunkyTortoise/enterprise-hub.git
cd enterprise-hub

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Start services (PostgreSQL + Redis)
docker-compose up -d postgres redis

# Apply database migrations
alembic upgrade head

# Start FastAPI backend (port 8000)
uvicorn ghl_real_estate_ai.api.main:socketio_app \
  --host 0.0.0.0 --port 8000 --reload

# Start Streamlit BI dashboard (port 8501) in another terminal
streamlit run admin_dashboard.py --server.port 8501
```

### Environment Modes

The application auto-detects its environment mode:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Demo** | No API key or `ENVIRONMENT=demo` | Mock data, no external calls |
| **Staging** | Test API key or `ENVIRONMENT=staging` | Real APIs, test accounts |
| **Production** | Real API key + `ENVIRONMENT=production` | Full validation, HTTPS enforced |

---

## Docker Deployment

### Build Image

```bash
docker build -t enterprise-hub:latest .
```

### Docker Compose (Full Stack)

```bash
# Development with all services
docker-compose up -d

# Production profile with monitoring
docker-compose --profile production --profile monitoring up -d
```

### Services Started

| Service | Port | Description |
|---------|------|-------------|
| `jorge-api` | 8000 | FastAPI + Socket.IO backend |
| `streamlit` | 8501 | BI Dashboard |
| `postgres` | 5432 | PostgreSQL database |
| `redis` | 6379 | Cache and sessions |
| `nginx` | 80/443 | Reverse proxy (production) |

---

## Staging Deployment

### Prerequisites

```bash
# Ensure clean working directory
git status  # Should be clean

# Pull latest main
git pull origin main

# Create release branch
git checkout -b deploy/staging-$(date +%Y-%m-%d)
```

### Build & Deploy

```bash
# Step 1: Build Docker image
docker build -t enterprise-hub:staging-$(date +%s) .

# Step 2: Push to container registry
docker tag enterprise-hub:staging registry.example.com/enterprise-hub:staging
docker push registry.example.com/enterprise-hub:staging

# Step 3: Deploy to staging
kubectl set image deployment/jorge-api \
  jorge-api=registry.example.com/enterprise-hub:staging \
  -n staging

# Step 4: Monitor rollout
kubectl rollout status deployment/jorge-api -n staging --timeout=300s

# Step 5: Run smoke tests
./scripts/smoke_test.sh staging

# Step 6: Check Grafana for errors and latency
```

### Staging Verification

```bash
# Check pods are running
kubectl get pods -n staging

# View logs
kubectl logs -n staging -l app=jorge-api --tail=100

# Test health endpoint
curl -H "Authorization: Bearer $STAGING_API_KEY" \
  https://staging-api.enterprise-hub.com/api/health

# Verify database migrations applied
psql $STAGING_DB_URL -c "\dt"

# Test lead qualification flow
curl -X POST https://staging-api.enterprise-hub.com/api/leads \
  -H "Authorization: Bearer $STAGING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Lead", "phone": "+15550100"}'
```

### Staging Validation Checklist

- [ ] API endpoints responding (200)
- [ ] Database queries working
- [ ] Claude API integration working
- [ ] GHL CRM sync working
- [ ] WebSocket/Socket.IO connections active
- [ ] Lead scheduler running
- [ ] Performance: <200ms p95
- [ ] Error rate: <1%
- [ ] No critical errors in logs

---

## Production Deployment

### Blue-Green Strategy

**Blue** = Current production (stable)
**Green** = New deployment (being tested)

### Prerequisites

- [ ] Staging deployment stable for 4+ hours
- [ ] No critical issues found in staging
- [ ] Team approval obtained
- [ ] On-call support ready
- [ ] Rollback tested in staging

### Deployment Steps

```bash
# Step 1: Tag the release
git tag v1.x.x
git push origin v1.x.x

# Step 2: Build production image
docker build -t enterprise-hub:v1.x.x .
docker push registry.example.com/enterprise-hub:v1.x.x

# Step 3: Create green deployment
kubectl create deployment jorge-api-green \
  --image=registry.example.com/enterprise-hub:v1.x.x \
  -n production

# Step 4: Wait for rollout
kubectl rollout status deployment/jorge-api-green -n production

# Step 5: Run smoke tests against green
./scripts/smoke_test.sh green

# Step 6: Canary - Route 5% traffic to green
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"deployment":"green"}}}'

# Monitor for 10 minutes:
# - Error rate should be <1%
# - Latency should be <200ms p95
# - Check logs for issues

# Step 7: Full cutover (if canary OK)
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"version":"v1.x.x"}}}'

# Step 8: Monitor green for 30 minutes
watch -n 5 'kubectl get pods -n production'

# Step 9: If stable, remove blue deployment
kubectl label deployment jorge-api-blue \
  deprecated=true -n production
```

### Production Monitoring (Post-Deploy)

```bash
# Real-time log monitoring
kubectl logs -n production -l app=jorge-api --tail=50 -f

# Metrics dashboard
open https://grafana.example.com/d/jorge-bots

# Watch for critical alerts:
# - Error rate > 5%
# - Response time > 500ms p95
# - API key failures
# - Database connection errors
```

### Security Validations (Automatic at Startup)

The application enforces these in production (`ENVIRONMENT=production`):

1. **JWT_SECRET_KEY**: Must be 32+ characters, app exits if missing
2. **GHL_WEBHOOK_SECRET**: Must be set, app exits if missing
3. **REDIS_PASSWORD**: Must be set, app exits if missing
4. **HTTPS**: Enforced via `HTTPSRedirectMiddleware`
5. **CORS**: Localhost origins stripped automatically
6. **Rate Limiting**: 100 req/min unauthenticated, IP blocking enabled

---

## Rollback Procedures

### Immediate Rollback (Blue-Green)

```bash
# Switch traffic back to blue (previous stable deployment)
kubectl patch service jorge-api \
  -p '{"spec":{"selector":{"deployment":"blue"}}}'

# Verify traffic routed to blue
kubectl get endpoints jorge-api -n production

# Monitor logs for stability
kubectl logs -n production -l deployment=blue --tail=50 -f

# Investigate green deployment
kubectl logs deployment/jorge-api-green -n production

# Delete failed green deployment
kubectl delete deployment jorge-api-green -n production
```

### Database Rollback

```bash
# If migration caused issues, rollback one step
alembic downgrade -1

# Or rollback to a specific revision
alembic downgrade <revision_id>

# Verify database state
alembic current
```

### Feature Flag Rollback

If a feature flag is causing issues, disable it without redeployment:

```bash
# Disable specific feature
kubectl set env deployment/jorge-api \
  ENABLE_SEMANTIC_RESPONSE_CACHING=false \
  -n production

# Restart pods to pick up change
kubectl rollout restart deployment/jorge-api -n production
```

---

## Database Migrations

### Create a New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "add_seller_temperature_field"

# Review the generated migration in alembic/versions/
# Verify both upgrade() and downgrade() are correct
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply to a specific revision
alembic upgrade <revision_id>

# Check current migration state
alembic current

# View migration history
alembic history
```

### Migration Safety

- Always review auto-generated migrations before applying
- Test migrations on staging first
- Ensure `downgrade()` functions are correct
- Never drop columns in production without a deprecation period
- Use `alembic stamp` to mark manual schema changes

---

## Post-Deployment Verification

### Automated Smoke Tests

```bash
# Run the full verification suite
python3 production_readiness_checklist.py

# Validate environment configuration
python3 validate_environment.py
```

### Manual Verification

1. **Health Check**: `GET /api/health` returns all services `connected`
2. **Lead Flow**: Submit a test lead, verify qualification starts
3. **Bot Response**: Send a message, verify Jorge responds within 500ms
4. **CRM Sync**: Verify lead appears in GHL
5. **WebSocket**: Open BI dashboard, verify real-time updates
6. **Scheduler**: Check lead sequence scheduler is running

### Performance Baselines (from `docs/PERFORMANCE_BASELINE.md`)

| Metric | Target | Measured (Stream D) | Alert Threshold |
|--------|--------|---------------------|-----------------|
| API p95 response time | <200ms | 14.67ms @ 100 users | >300ms |
| API throughput | >1,000 req/s | 5,118 req/s | <50 req/s |
| Buyer bot p95 | <400ms | 179ms @ 50 concurrent | >400ms |
| Seller bot p95 | <500ms | 139ms @ 50 concurrent | >600ms |
| Memory under load | <2GB | 294 MB peak | >1.5GB |
| Error rate | <1% | 0.00% | >5% |
| Cache hit rate | >70% | >70% | <60% |

---

**Quick Reference**:

```bash
# Deploy to staging
git checkout -b deploy/staging && git push origin deploy/staging

# Deploy to production
git tag v1.x.x && git push origin v1.x.x

# Rollback production
kubectl patch service jorge-api -p '{"spec":{"selector":{"deployment":"blue"}}}'

# Check status
kubectl get deployments -n production
open https://grafana.example.com/d/jorge-bots
```

---

**Version**: 2.1 | **Last Updated**: February 2, 2026
