# Railway Deployment Guide - GHL Real Estate AI

Complete step-by-step guide to deploy your GHL Real Estate AI to Railway.

## Why Railway?

- **Free tier**: 500 hours/month ($0 cost for small projects)
- **Auto-scaling**: Handles traffic spikes automatically
- **PostgreSQL + Redis included**: No separate hosting needed
- **GitHub integration**: Auto-deploy on git push
- **Zero DevOps**: No Docker knowledge required

---

## Prerequisites

- [ ] Railway account (https://railway.app/)
- [ ] GitHub repository (push your code first)
- [ ] Anthropic API key
- [ ] GHL API key + Location ID

---

## Step 1: Install Railway CLI

### Mac/Linux:
```bash
npm install -g @railway/cli
# Or with Homebrew:
brew install railway
```

### Windows:
```bash
npm install -g @railway/cli
```

### Verify Installation:
```bash
railway --version
```

---

## Step 2: Login to Railway

```bash
railway login
```

This opens your browser to authenticate. Once logged in, return to terminal.

---

## Step 3: Create New Railway Project

### Option A: From Existing Git Repo (Recommended)

```bash
cd /path/to/ghl-real-estate-ai
railway init
```

Railway will ask:
- **"Create a new project or link existing?"** → Select "Create new project"
- **"Project name?"** → Enter `ghl-real-estate-ai`
- **"Environment?"** → Select `production`

### Option B: From Railway Dashboard

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Click "Deploy Now"

---

## Step 4: Add PostgreSQL Database

### Via CLI:
```bash
railway add --database postgresql
```

### Via Dashboard:
1. Go to your project dashboard
2. Click "+ New" button
3. Select "Database" → "PostgreSQL"
4. Railway auto-provisions a database

**Important:** Railway automatically sets `DATABASE_URL` environment variable. You don't need to configure this manually!

---

## Step 5: Add Redis

### Via CLI:
```bash
railway add --database redis
```

### Via Dashboard:
1. Click "+ New" button
2. Select "Database" → "Redis"
3. Railway auto-provisions Redis

**Important:** Railway automatically sets `REDIS_URL` environment variable.

---

## Step 6: Configure Environment Variables

### Via CLI:
```bash
# Set Anthropic API key
railway variables set ANTHROPIC_API_KEY=sk-ant-your-key-here

# Set GHL credentials
railway variables set GHL_API_KEY=your-ghl-api-key
railway variables set GHL_LOCATION_ID=your-location-id

# Set environment
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=info

# Set agent details
railway variables set DEFAULT_AGENT_NAME="Sarah Johnson"
railway variables set DEFAULT_AGENT_PHONE="+15125551234"
railway variables set DEFAULT_AGENT_EMAIL="agent@example.com"

# Set thresholds
railway variables set HOT_LEAD_THRESHOLD=70
railway variables set WARM_LEAD_THRESHOLD=40
```

### Via Dashboard:
1. Go to your project
2. Click on your service (e.g., "ghl-real-estate-ai")
3. Go to "Variables" tab
4. Click "New Variable"
5. Add each variable from above

**Complete list of variables:**
```
ANTHROPIC_API_KEY=sk-ant-xxxxx
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
ENVIRONMENT=production
LOG_LEVEL=info
DEFAULT_AGENT_NAME=Sarah Johnson
DEFAULT_AGENT_PHONE=+15125551234
DEFAULT_AGENT_EMAIL=agent@example.com
HOT_LEAD_THRESHOLD=70
WARM_LEAD_THRESHOLD=40
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_CONTACT=100
RATE_LIMIT_GLOBAL=1000
```

**Note:** `DATABASE_URL` and `REDIS_URL` are auto-set by Railway when you add those databases. Don't override them!

---

## Step 7: Create railway.json Config

Create `railway.json` in your project root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**What this does:**
- `builder: NIXPACKS` → Railway auto-detects Python and builds correctly
- `buildCommand` → Installs dependencies
- `startCommand` → Runs FastAPI server (Railway sets `$PORT` automatically)
- `healthcheckPath` → Railway pings `/health` to verify service is up
- `restartPolicy` → Auto-restart on crashes (max 10 retries)

---

## Step 8: Create Procfile (Alternative to railway.json)

If you prefer Procfile format, create `Procfile`:

```
web: uvicorn api.main:app --host 0.0.0.0 --port $PORT
worker: celery -A core.celery_app worker --loglevel=info
```

**Note:** Use `railway.json` for simpler deployments. Use `Procfile` if you need Celery workers.

---

## Step 9: Deploy

### Option A: Deploy from CLI

```bash
# Push code to Railway
railway up
```

Railway will:
1. Build your application
2. Install dependencies
3. Start the server
4. Provide a deployment URL

### Option B: Deploy from GitHub (Auto-Deploy)

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "feat: initial deployment"
   git push origin main
   ```

2. Railway auto-deploys on every push to `main` branch

---

## Step 10: Get Your Deployment URL

### Via CLI:
```bash
railway domain
```

Output:
```
https://ghl-real-estate-ai-production.up.railway.app
```

### Via Dashboard:
1. Go to your project
2. Click on your service
3. Go to "Settings" tab
4. Under "Domains", click "Generate Domain"
5. Railway provides a URL like: `https://your-app.railway.app`

**Copy this URL for the next step!**

---

## Step 11: Run Database Migrations

After first deployment, initialize the database:

```bash
# Connect to Railway service
railway run bash

# Inside Railway environment, run migrations
alembic upgrade head

# Exit
exit
```

**Alternative (one-liner):**
```bash
railway run alembic upgrade head
```

---

## Step 12: Load Knowledge Base to Production

```bash
# Load FAQ and property listings
railway run python scripts/load_knowledge_base.py
```

This populates the Chroma vector database with:
- 20 real estate FAQs
- 10 sample property listings
- Agent objection handling scripts

---

## Step 13: Configure GHL Webhook

1. Login to GoHighLevel
2. Go to **Settings** > **Integrations** > **Webhooks**
3. Click "Add Webhook"
4. Enter webhook URL:
   ```
   https://your-app.railway.app/api/ghl/webhook
   ```
5. Select event type: **InboundMessage**
6. Click "Save"

---

## Step 14: Test End-to-End

### 1. Check Health Endpoint
```bash
curl https://your-app.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-02T10:00:00Z",
  "services": {
    "claude": "connected",
    "database": "connected",
    "redis": "connected"
  }
}
```

### 2. Send Test SMS to GHL Number
Text your GHL number:
```
"Hi, I'm looking for a 3-bedroom house in Austin under $400k"
```

**Expected:**
- AI responds within 2-3 seconds
- Response is human-like and relevant
- Lead is tagged in GHL (check GHL dashboard)

### 3. Check Railway Logs
```bash
railway logs --tail
```

You should see:
```
INFO: Received webhook for contact: contact_abc123
INFO: Generated response in 1.8s
INFO: Lead score: 35/100
INFO: Tagged contact with: AI-Engaged, Budget-Under-400k
```

---

## Step 15: Monitor Deployment

### View Real-Time Logs
```bash
railway logs --tail
```

### View Metrics (Dashboard)
1. Go to Railway dashboard
2. Click on your service
3. Go to "Metrics" tab
4. Monitor:
   - CPU usage
   - Memory usage
   - Request count
   - Response time

### Set Up Alerts (Optional)
1. Go to "Settings" > "Notifications"
2. Enable:
   - Deployment failures
   - High error rate
   - High latency

---

## Troubleshooting

### Issue: Build Fails

**Error:** `No module named 'anthropic'`

**Fix:**
1. Verify `requirements.txt` includes `anthropic==0.18.1`
2. Redeploy:
   ```bash
   railway up --force
   ```

### Issue: Database Connection Errors

**Error:** `could not connect to database`

**Fix:**
1. Verify PostgreSQL is running:
   ```bash
   railway logs --service postgresql
   ```
2. Check `DATABASE_URL` is set:
   ```bash
   railway variables get DATABASE_URL
   ```
3. Restart service:
   ```bash
   railway restart
   ```

### Issue: Webhook Not Receiving Messages

**Check:**
1. GHL webhook URL is HTTPS (Railway provides this automatically)
2. Health check passes: `curl https://your-app.railway.app/health`
3. Railway service is running (check dashboard status)

**Debug:**
```bash
# Test webhook locally
curl -X POST https://your-app.railway.app/api/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "InboundMessage",
    "contactId": "test_123",
    "message": {"type": "SMS", "body": "test"},
    "contact": {"firstName": "Test"}
  }'
```

### Issue: High Response Latency

**Symptom:** AI takes 5+ seconds to respond

**Diagnose:**
```bash
railway logs --tail | grep "response time"
```

**Common causes & fixes:**
- Vector search slow → Reduce `top_k` from 5 to 3 in code
- Claude API slow → Set `max_tokens=300` instead of 1000
- Cold start → Railway free tier sleeps after inactivity (upgrade to Pro for always-on)

---

## Cost Management

### Free Tier Limits
- **500 execution hours/month** (enough for ~720 hours if always-on)
- **1GB PostgreSQL** (holds 10k+ conversations)
- **100MB Redis** (session state for 1k+ concurrent users)

### Monitor Usage
```bash
railway status
```

Output:
```
Usage this month:
- Execution hours: 87 / 500 (17%)
- PostgreSQL: 234MB / 1GB (23%)
- Redis: 12MB / 100MB (12%)
```

### Upgrade to Pro ($5/month)
Benefits:
- 8GB RAM per service (vs 512MB free)
- Always-on (no cold starts)
- Priority support

**Upgrade:**
```bash
railway upgrade
```

---

## Auto-Scaling Configuration

Railway auto-scales based on traffic. To configure:

### Via Dashboard:
1. Go to service settings
2. Under "Resources", set:
   - **Min instances:** 1 (always-on)
   - **Max instances:** 3 (scale to 3 during traffic spikes)
   - **CPU limit:** 1 vCPU
   - **Memory limit:** 512MB

### Via railway.toml:
Create `railway.toml`:
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10

[resources]
cpu = 1
memory = 512
replicas = { min = 1, max = 3 }
```

---

## Continuous Deployment (CI/CD)

### Automatic Deploys on Git Push

Railway auto-deploys when you push to GitHub:

```bash
git add .
git commit -m "feat: improved lead scoring algorithm"
git push origin main
```

Railway will:
1. Detect push
2. Build new version
3. Run health check
4. Deploy if health check passes
5. Keep old version running until new one is healthy (zero-downtime)

### Manual Deploy from CLI

```bash
railway up
```

### Rollback to Previous Version

```bash
railway rollback
```

Or via dashboard:
1. Go to "Deployments" tab
2. Click on previous successful deployment
3. Click "Rollback to this version"

---

## Environment-Specific Deployments

### Create Staging Environment

```bash
# Create staging environment
railway environment create staging

# Switch to staging
railway environment switch staging

# Deploy to staging
railway up
```

### Promote Staging to Production

After testing in staging:
```bash
railway environment switch production
railway promote staging
```

---

## Security Best Practices

### 1. Rotate API Keys Regularly
```bash
# Update Anthropic key
railway variables set ANTHROPIC_API_KEY=new-key-here

# Railway auto-restarts service with new key
```

### 2. Enable Rate Limiting
Already set in `.env`:
```bash
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_CONTACT=100
RATE_LIMIT_GLOBAL=1000
```

### 3. Use Private Networking (Pro Plan)
Prevent public access to databases:
1. Go to PostgreSQL service
2. Settings > Networking
3. Enable "Private Networking"
4. Only your Railway services can access DB

### 4. Enable HTTPS Only
Railway provides SSL automatically. Enforce HTTPS in code:

```python
# In api/main.py
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
```

---

## Backup & Disaster Recovery

### Database Backups (Automatic)

Railway Pro plan includes:
- Automatic daily backups (retained for 7 days)
- Point-in-time recovery

### Manual Backup
```bash
# Dump PostgreSQL database
railway run pg_dump $DATABASE_URL > backup.sql

# Restore from backup
railway run psql $DATABASE_URL < backup.sql
```

### Redis Backup
```bash
# Export Redis data
railway run redis-cli --rdb /tmp/dump.rdb
```

---

## Performance Optimization

### 1. Enable Caching

Update `api/main.py`:
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis_url = os.getenv("REDIS_URL")
    FastAPICache.init(RedisBackend(redis_url), prefix="fastapi-cache")
```

### 2. Use Connection Pooling

Update `core/database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

### 3. Optimize Vector Search

Reduce `top_k` in RAG queries:
```python
# Instead of top_k=5
relevant_docs = rag_engine.search(query, top_k=3)
```

---

## Next Steps After Deployment

- [ ] Monitor logs for first 24 hours: `railway logs --tail`
- [ ] Test with real leads (send 10+ test SMS messages)
- [ ] Review lead scoring accuracy (check GHL tags)
- [ ] Adjust prompts based on conversation quality
- [ ] Set up Sentry for error tracking (optional)
- [ ] Schedule weekly backup of knowledge base

---

## Support

**Railway Issues:**
- Discord: https://discord.gg/railway
- Docs: https://docs.railway.app/

**Project Issues:**
- Check logs: `railway logs --tail`
- Restart service: `railway restart`
- Email: your-email@example.com

---

**Deployment Checklist:**

- [ ] Railway account created
- [ ] PostgreSQL added
- [ ] Redis added
- [ ] All environment variables set
- [ ] Code deployed (`railway up`)
- [ ] Database migrated (`railway run alembic upgrade head`)
- [ ] Knowledge base loaded
- [ ] GHL webhook configured
- [ ] End-to-end test passed
- [ ] Monitoring set up

**You're live!** 🚀
