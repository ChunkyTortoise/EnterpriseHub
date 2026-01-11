# Railway & Vercel Deployment Guide

**Version:** 4.0.0
**Last Updated:** January 10, 2026
**Status:** Production Ready
**Coverage:** Complete deployment for AI-Enhanced Operations platform

---

## Table of Contents

1. [Overview](#overview)
2. [Railway Backend Deployment](#railway-backend-deployment)
3. [Vercel Frontend Deployment](#vercel-frontend-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Database & Storage Setup](#database--storage-setup)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Continuous Deployment](#continuous-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Security & Best Practices](#security--best-practices)

---

## Overview

The EnterpriseHub platform is deployed across two complementary services:

- **Railway**: AI/ML backend services (Python, FastAPI, async workers)
- **Vercel**: Frontend applications (Streamlit demos, React dashboards)

### Architecture Diagram

```
User Request
    ↓
[Vercel Frontend]
  (Streamlit, React)
    ↓
[API Gateway]
    ↓
[Railway Backend Services]
  ├─→ ML Services (Lead Scoring, Property Matching)
  ├─→ GHL Integration (Webhooks, API Sync)
  ├─→ Real-time Scoring
  └─→ Worker Services (Async Tasks, Retraining)
    ↓
[PostgreSQL Database]
[Redis Cache]
[S3 Model Storage]
```

### Key Features

- **Zero-downtime deployments** with rolling updates
- **Automatic scaling** based on traffic
- **Health monitoring** with automated alerts
- **Continuous deployment** from GitHub
- **Environment management** with secret management
- **Performance monitoring** with real-time dashboards

---

## Railway Backend Deployment

### Prerequisites

1. Railway account (https://railway.app)
2. GitHub repository with code
3. Docker configured locally
4. GitHub CLI installed

### Step 1: Initial Setup

#### 1.1 Connect GitHub Repository

```bash
# Login to Railway CLI
railway login

# Link project directory to Railway
cd /Users/cave/enterprisehub
railway link

# Verify connection
railway status
```

#### 1.2 Create Railway Project

Via Railway Dashboard:
1. Go to https://railway.app/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Choose `enterprisehub` repository
5. Configure settings:
   - Project name: `enterprisehub-prod`
   - Environment: `production`
   - Auto-deploy: Enabled

### Step 2: Configure Services

#### 2.1 Backend Service (API Server)

Create `railway.json` in project root:

```json
{
  "services": [
    {
      "name": "ml-api",
      "dockerfile": "./docker/Dockerfile.api",
      "port": 8000,
      "healthCheck": "/health",
      "environment": [
        "PYTHON_VERSION=3.11",
        "ENVIRONMENT=production"
      ],
      "scaling": {
        "minInstances": 2,
        "maxInstances": 10,
        "cpuThreshold": 70,
        "memoryThreshold": 80
      }
    },
    {
      "name": "worker",
      "dockerfile": "./docker/Dockerfile.worker",
      "command": "celery -A tasks worker --concurrency=4",
      "scaling": {
        "minInstances": 1,
        "maxInstances": 5
      }
    }
  ]
}
```

#### 2.2 Create Dockerfile for API

`docker/Dockerfile.api`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2.3 Create Dockerfile for Worker

`docker/Dockerfile.worker`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

CMD ["celery", "-A", "tasks", "worker", "--concurrency=4", "--loglevel=info"]
```

### Step 3: Environment Variables

#### 3.1 Set Production Variables in Railway Dashboard

Navigate to: Project → Variables → Add Variable

**Critical Variables:**

```bash
# Database
DATABASE_URL=postgresql://user:password@prod-db:5432/enterprisehub
REDIS_URL=redis://prod-redis:6379/0

# AI/ML Services
OPENAI_API_KEY=sk-xxx...
ML_MODEL_STORAGE=s3://enterprisehub-models-prod/

# Real Estate APIs
MLS_API_KEY=xxx...
REAL_ESTATE_API_KEY=xxx...

# GHL Integration
GHL_API_KEY=ghl_xxx...
GHL_LOCATION_ID=xxx...
GHL_WEBHOOK_SECRET=xxx...

# Infrastructure
ENVIRONMENT=production
LOG_LEVEL=info
SENTRY_DSN=https://xxx@sentry.io/xxx
```

#### 3.2 Add via CLI

```bash
# Create .env.railway file
cat > .env.railway << 'EOF'
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
GHL_API_KEY=ghl_...
# ... rest of variables
EOF

# Deploy variables
railway variables set --from-file .env.railway
```

### Step 4: Database Setup

#### 4.1 Add PostgreSQL Plugin

In Railway Dashboard:
1. Project → + Add
2. Search "PostgreSQL"
3. Create new plugin
4. Auto-fill DATABASE_URL

#### 4.2 Initialize Database

```bash
# Connect to database
railway psql

# Run migrations
python scripts/migrate.py

# Seed initial data
python scripts/seed_data.py
```

#### 4.3 Add Redis Plugin

In Railway Dashboard:
1. Project → + Add
2. Search "Redis"
3. Create new plugin
4. Auto-fill REDIS_URL

### Step 5: Deploy

#### 5.1 Manual Deployment

```bash
# Deploy from CLI
railway deploy

# Check deployment status
railway status

# View logs
railway logs

# Watch live logs
railway logs --follow
```

#### 5.2 Automatic Deployment from GitHub

Railway auto-deploys on push to main:

```bash
# Configure auto-deploy
railway service update ml-api --auto-deploy=true

# View deployments
railway deployments

# Rollback if needed
railway deployments rollback [deployment-id]
```

### Step 6: Configure Domain & SSL

#### 6.1 Add Custom Domain

In Railway Dashboard:
1. Project → ml-api service → Settings
2. Add Domain: `api.enterprisehub.com`
3. Configure DNS records (auto-provided)
4. Enable SSL (automatic)

#### 6.2 Health Check Configuration

```python
# in main.py
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "4.0.0"
    }

@app.get("/health/deep")
async def deep_health_check():
    # Check database
    db_status = await check_database_connection()
    # Check Redis
    redis_status = await check_redis_connection()
    # Check ML models
    models_status = check_model_availability()

    return {
        "status": "healthy" if all([db_status, redis_status, models_status]) else "degraded",
        "database": db_status,
        "redis": redis_status,
        "models": models_status
    }
```

---

## Vercel Frontend Deployment

### Prerequisites

1. Vercel account (https://vercel.com)
2. GitHub repository with frontend code
3. Node.js 18+ installed

### Step 1: Initial Setup

#### 1.1 Connect GitHub to Vercel

Via Vercel Dashboard:
1. Create new project
2. Select "Import Git Repository"
3. Choose `enterprisehub` repository
4. Configure project:
   - Framework: Other (Streamlit)
   - Root directory: `/` (or `./streamlit_demo/` for React)

#### 1.2 Install Vercel CLI

```bash
npm install -g vercel

# Login to Vercel
vercel login

# Link project
cd /Users/cave/enterprisehub
vercel link
```

### Step 2: Configure Build & Deploy

#### 2.1 Vercel Configuration

Create `vercel.json`:

```json
{
  "buildCommand": "pip install -r requirements.txt && streamlit export-testdata",
  "outputDirectory": "public",
  "env": {
    "STREAMLIT_SERVER_HEADLESS": "true",
    "STREAMLIT_SERVER_PORT": "8501",
    "STREAMLIT_SERVER_ENABLEXSRFPROTECTION": "false"
  },
  "regions": ["sfo1"],
  "functions": {
    "api/**": {
      "memory": 3008,
      "maxDuration": 60
    }
  }
}
```

#### 2.2 Streamlit Configuration

Create `.streamlit/config.toml`:

```toml
[global]
# Environment
environment = "production"

[logger]
level = "error"

[client]
showErrorDetails = false
showWarningOnDirectExecution = false

[server]
headless = true
port = 8501
enableXsrfProtection = false
enableCORS = false

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#0066cc"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Step 3: Environment Variables

#### 3.1 Set Variables in Vercel Dashboard

Project → Settings → Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.enterprisehub.com
API_KEY=xxx...

# Feature Flags
NEXT_PUBLIC_ENABLE_DEMOS=true
NEXT_PUBLIC_ENABLE_ADVANCED_FEATURES=true

# Analytics
NEXT_PUBLIC_ANALYTICS_ID=xxx...

# Sentry
NEXT_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

#### 3.2 Production vs Preview

Set separate values for:
- Production (main branch)
- Preview (PR branches)
- Development

### Step 4: Deploy

#### 4.1 Manual Deploy

```bash
# Deploy to preview
vercel --prod=false

# Deploy to production
vercel --prod

# View deployment
vercel list
```

#### 4.2 Automatic Deployments

Vercel auto-deploys on:
- Push to main → Production
- Push to other branches → Preview
- PRs → Preview (auto-comments)

### Step 5: Configure Performance

#### 5.1 Enable Caching

In vercel.json:

```json
{
  "headers": [
    {
      "source": "/static/:path*",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    },
    {
      "source": "/api/:path*",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "max-age=0, s-maxage=86400"
        }
      ]
    }
  ]
}
```

#### 5.2 Configure ISR (Incremental Static Regeneration)

For React components:

```jsx
export async function getStaticProps() {
  const data = await fetchData();
  return {
    props: { data },
    revalidate: 3600 // Revalidate every hour
  };
}
```

### Step 6: Monitor & Optimize

#### 6.1 Vercel Analytics

Enable in Project Settings:
- Web Vitals monitoring
- Real user monitoring
- Performance analytics

#### 6.2 Check Performance

```bash
# Analyze bundle size
npm run build --analyze

# Test performance
vercel --scope=enterprisehub list
```

---

## Environment Configuration

### Configuration Hierarchy

```
1. Environment Variables (Railway/Vercel)
   ↓
2. .env.production (local override)
   ↓
3. .env.staging
   ↓
4. .env (development default)
```

### Multi-Environment Setup

#### Production Environment

```bash
# Railway
export ENVIRONMENT=production
export LOG_LEVEL=error
export ENABLE_DEBUG=false
export CACHE_TTL=3600
```

#### Staging Environment

```bash
# Railway (separate project)
export ENVIRONMENT=staging
export LOG_LEVEL=warning
export ENABLE_DEBUG=false
export CACHE_TTL=1800
```

#### Development Environment

```bash
# Local
export ENVIRONMENT=development
export LOG_LEVEL=debug
export ENABLE_DEBUG=true
export CACHE_TTL=300
```

---

## Database & Storage Setup

### PostgreSQL Configuration

```sql
-- Create production database
CREATE DATABASE enterprisehub_prod;

-- Create user
CREATE USER hub_api WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE enterprisehub_prod TO hub_api;

-- Enable extensions
\c enterprisehub_prod
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "hstore";
```

### Redis Configuration

```bash
# Connection pooling (Railway auto-configured)
# Max connections: 50
# Timeout: 5 seconds

# Key patterns for caching
redis:
  lead-scores:{lead_id} → TTL 24h
  property-matches:{lead_id} → TTL 6h
  market-data:{location} → TTL 1h
  user-sessions:{user_id} → TTL 7 days
```

### S3 Model Storage

```bash
# Configure S3 bucket
aws s3 mb s3://enterprisehub-models-prod

# Set up versioning
aws s3api put-bucket-versioning \
  --bucket enterprisehub-models-prod \
  --versioning-configuration Status=Enabled

# Set encryption
aws s3api put-bucket-encryption \
  --bucket enterprisehub-models-prod \
  --server-side-encryption-configuration '{...}'
```

---

## Monitoring & Health Checks

### Health Check Endpoints

```python
# API Health
GET /health → { status: "healthy" }

# Deep Health Check
GET /health/deep → {
  status: "healthy",
  database: true,
  redis: true,
  models: true
}

# Service Status
GET /status/services → {
  ml_api: "operational",
  ghl_sync: "operational",
  webhooks: "operational"
}
```

### Metrics to Monitor

```bash
# Request metrics
- Response time (P50, P95, P99)
- Error rate
- Request volume
- Concurrent connections

# Business metrics
- Lead scores processed
- Properties matched
- Churn predictions
- Model accuracy

# Infrastructure metrics
- CPU usage
- Memory usage
- Database connections
- Cache hit rate
```

### Setup Monitoring

#### 1. Sentry for Error Tracking

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1
)
```

#### 2. Datadog for Metrics

```python
from datadog import initialize, api

options = {
    'api_key': 'xxx',
    'app_key': 'xxx'
}
initialize(**options)

# Track metrics
api.Metric.send(
    metric="enterprise_hub.leads.scored",
    points=100,
    tags=["env:prod"]
)
```

---

## Continuous Deployment

### GitHub Actions Workflow

`.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov

  deploy-railway:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: railway-app/railway-action@v1
        with:
          token: ${{ secrets.RAILWAY_TOKEN }}
          service: ml-api
          command: "railway deploy"

  deploy-vercel:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: vercel/action@master
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          production: true

  notify:
    needs: [deploy-railway, deploy-vercel]
    runs-on: ubuntu-latest
    steps:
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK }}
          payload: |
            {
              "text": "Deployment complete to production ✅"
            }
```

### Rollback Procedure

```bash
# Via Railway CLI
railway deployments
railway deployments rollback [deployment-id]

# Via Vercel
vercel rollback [deployment-id]

# Verify rollback
railway logs --follow
```

---

## Troubleshooting

### Deployment Issues

#### Issue: Build Fails

```bash
# Check logs
railway logs --service=ml-api --follow

# Rebuild from scratch
railway deploy --force

# Check Docker image
docker build -t enterprise-hub:latest .
docker run -it enterprise-hub:latest /bin/bash
```

#### Issue: Database Connection Failed

```bash
# Check connection string
railway variables | grep DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Run migrations
python scripts/migrate.py --check
```

#### Issue: Memory/CPU Issues

```bash
# Check resource usage
railway service list

# Increase resources
railway service update ml-api --memory=2048 --cpu=1024

# Scale instances
railway service update ml-api --minInstances=2 --maxInstances=10
```

### Performance Issues

#### Slow API Responses

```bash
# Check database query performance
EXPLAIN ANALYZE SELECT * FROM leads WHERE score > 0.8;

# Check cache hit rate
redis-cli INFO stats | grep hit_ratio

# Monitor slow queries
railway logs --follow | grep "duration"
```

#### High Memory Usage

```bash
# Check memory profile
python -m memory_profiler scripts/profile.py

# Reduce batch size
export BATCH_SIZE=32  # instead of 128

# Enable memory optimization
export ML_PRECISION=float32
```

---

## Security & Best Practices

### API Security

```python
# Rate limiting
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/v1/ml/score-lead")
@limiter.limit("1000/minute")
async def score_lead(lead: LeadProfile):
    ...
```

### Secret Management

```bash
# Never commit secrets
echo ".env.local" >> .gitignore

# Use Railway/Vercel secret storage
railway variables set SECRET_KEY=xxx

# Rotate secrets regularly
# Monthly rotation recommended
```

### SSL/TLS

```bash
# Railway auto-enables
# Certificate auto-renews

# Verify SSL
openssl s_client -connect api.enterprisehub.com:443

# Force HTTPS
add_header Strict-Transport-Security "max-age=31536000" always;
```

### Database Backups

```bash
# Automated backups
# Railway: Daily automated backups
# Retention: 30 days

# Manual backup
railway exec pg_dump > backup.sql

# Restore from backup
railway exec psql < backup.sql
```

### Audit Logging

```python
# Log all API calls
from pythonjsonlogger import jsonlogger

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info("request", extra={
        "method": request.method,
        "path": request.url.path,
        "user_id": request.user.id
    })
    response = await call_next(request)
    return response
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Database migrations tested
- [ ] Environment variables configured
- [ ] Secrets stored securely
- [ ] Performance benchmarks reviewed
- [ ] Security scan passed

### Deployment

- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Check metrics
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor error rates

### Post-Deployment

- [ ] Verify API endpoints
- [ ] Check database health
- [ ] Review logs for errors
- [ ] Monitor performance metrics
- [ ] Communicate status to team
- [ ] Update deployment record

---

## Support & Resources

### Documentation
- Railway Docs: https://docs.railway.app
- Vercel Docs: https://vercel.com/docs
- FastAPI: https://fastapi.tiangolo.com
- PostgreSQL: https://www.postgresql.org/docs

### Status Pages
- Railway Status: https://status.railway.app
- Vercel Status: https://www.vercelstatus.com

### Support Channels
- Railway Support: support@railway.app
- Vercel Support: support@vercel.com
- Team Slack: #deployment-support

---

**Last Updated**: January 10, 2026
**Maintained By**: DevOps & Infrastructure Team
**Next Review**: January 17, 2026
