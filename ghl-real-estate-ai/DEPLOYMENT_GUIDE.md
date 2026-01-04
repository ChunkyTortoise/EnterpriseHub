# GHL Real Estate AI - Railway Deployment Guide
**Date:** January 3, 2026
**Status:** Ready for Production Deployment
**Estimated Time:** 10-15 minutes

---

## Prerequisites

✅ Railway CLI installed (v4.16.1)
✅ All tests passing (31/31)
✅ Project configured with `railway.json`

---

## Step 1: Authenticate with Railway (2 minutes)

Run the following command in your terminal:

```bash
railway login
```

**What happens:**
- A browser window will open
- Log in with your Railway account (or create one if needed)
- Once authenticated, return to the terminal

**Troubleshooting:**
- If the browser doesn't open automatically, copy the URL from the terminal
- If you don't have a Railway account, sign up at https://railway.app

---

## Step 2: Create/Link Railway Project (3 minutes)

### Option A: Create New Project (Recommended)

```bash
railway init
```

When prompted:
- **Project name:** Enter `ghl-real-estate-ai` or your preferred name
- **Template:** Select "Empty Project"

### Option B: Link to Existing Project

If you already have a Railway project:

```bash
railway link
```

Then select your project from the list.

---

## Step 3: Configure Environment Variables (5 minutes)

**CRITICAL:** Set these environment variables before deploying:

```bash
# Required Variables
railway variables set ANTHROPIC_API_KEY="your_anthropic_api_key_here"
railway variables set GHL_API_KEY="your_ghl_api_key_here"
railway variables set GHL_LOCATION_ID="your_ghl_location_id_here"

# Optional (for multi-tenant agency access)
railway variables set GHL_AGENCY_API_KEY="your_agency_master_key_here"

# Optional (if you have a calendar configured)
railway variables set GHL_CALENDAR_ID="your_calendar_id_here"
```

**Alternative: Use Railway Dashboard**

1. Go to https://railway.app/dashboard
2. Select your project
3. Click "Variables" tab
4. Add each variable with its value

**Required Variables:**
| Variable | Description | Where to Find |
|----------|-------------|---------------|
| `ANTHROPIC_API_KEY` | Your Claude API key | https://console.anthropic.com/settings/keys |
| `GHL_API_KEY` | GHL API key for your location | GHL Settings → API → Create API Key |
| `GHL_LOCATION_ID` | Your GHL location ID | GHL Settings → Business Profile (Location ID) |

**Optional Variables:**
| Variable | Description | When to Use |
|----------|-------------|-------------|
| `GHL_AGENCY_API_KEY` | Agency-level master key | If managing multiple sub-accounts |
| `GHL_CALENDAR_ID` | Calendar ID for hot lead scheduling | If using calendar integration |

---

## Step 4: Deploy to Railway (2 minutes)

```bash
railway up
```

**What happens:**
1. Railway will build your project using Nixpacks
2. Install dependencies from `requirements.txt`
3. Start the FastAPI server with `uvicorn`
4. Health check endpoint will be monitored at `/health`

**Expected output:**
```
Building...
 ✓ Build successful
Deploying...
 ✓ Deployment successful
Service is live at: https://your-app.railway.app
```

---

## Step 5: Get Your Deployment URL (1 minute)

```bash
railway domain
```

**Output:**
```
https://ghl-real-estate-ai-production.railway.app
```

**Save this URL** - you'll need it for the GHL webhook configuration.

---

## Step 6: Verify Deployment Health (1 minute)

Test the health check endpoint:

```bash
curl https://your-deployment-url.railway.app/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "service": "ghl-real-estate-ai",
  "version": "1.0.0"
}
```

---

## Step 7: Connect GHL Webhook (5 minutes)

### In GoHighLevel:

1. **Go to Workflows/Automations**
2. **Create New Workflow:**
   - **Name:** "AI Lead Qualifier"
   - **Trigger:** Tag Added → "Needs Qualifying"

3. **Add Action:** Send Webhook
   - **URL:** `https://your-deployment-url.railway.app/ghl/webhook`
   - **Method:** POST
   - **Headers:**
     ```
     Content-Type: application/json
     ```
   - **Body:** (Leave as default - GHL sends contact data automatically)

4. **Save & Activate Workflow**

### Test with Real Lead:

1. Go to a test contact in GHL
2. Add tag: "Needs Qualifying"
3. Send a message from that contact: "I want to sell my house"
4. **Expected behavior:**
   - AI responds within 2-3 seconds
   - Message is under 160 characters
   - Direct tone: "Hey! Quick question: where's the property located?"

---

## Step 8: Monitor Deployment (Ongoing)

### View Logs:

```bash
railway logs
```

**Or in Railway Dashboard:**
1. Go to your project
2. Click "Deployments" tab
3. Select latest deployment
4. View logs in real-time

### Common Log Entries (Healthy System):

```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Check Deployment Status:

```bash
railway status
```

---

## Environment Variable Reference

### Complete List of Supported Variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | - | Claude API key |
| `GHL_API_KEY` | Yes | - | GHL API key for primary location |
| `GHL_LOCATION_ID` | Yes | - | Primary GHL location ID |
| `GHL_AGENCY_API_KEY` | No | - | Agency master key for multi-tenant access |
| `GHL_CALENDAR_ID` | No | - | Calendar ID for scheduling hot leads |
| `RAG_TOP_K_RESULTS` | No | 5 | Number of RAG results to return |
| `MAX_TOKENS` | No | 150 | Max tokens per AI response (SMS constraint) |
| `LOG_LEVEL` | No | info | Logging level (debug, info, warn, error) |

---

## Troubleshooting

### Issue: Deployment fails during build

**Check:**
```bash
railway logs --build
```

**Common causes:**
- Missing dependencies in `requirements.txt`
- Python version mismatch

**Fix:**
- Verify all dependencies are listed
- Railway uses Python 3.11+ by default

---

### Issue: Deployment starts but crashes

**Check:**
```bash
railway logs
```

**Common causes:**
- Missing environment variables
- Invalid API keys

**Fix:**
```bash
railway variables
```

Verify all required variables are set.

---

### Issue: Webhook not triggering

**Check:**
1. Verify webhook URL is correct in GHL workflow
2. Check Railway logs for incoming requests:
   ```bash
   railway logs --filter "webhook"
   ```

**Common causes:**
- Wrong URL in GHL workflow
- Missing "Needs Qualifying" tag
- "AI-Off" tag present (deactivates AI)

**Fix:**
- Verify tags on contact: Must have "Needs Qualifying" or "Hit List"
- Must NOT have "AI-Off", "Qualified", or "Stop-Bot"

---

### Issue: AI responses too long (>160 chars)

**This should NOT happen** - we have 3-layer enforcement:
1. Prompt instruction (system_prompts.py)
2. max_tokens=150 (config.py)
3. Runtime truncation (conversation_manager.py)

**If it occurs:**
```bash
railway logs --filter "SMS truncation"
```

Check if truncation logic is executing.

---

### Issue: Admin dashboard not accessible

**Admin dashboard is local-only** - not deployed to Railway.

**To use admin dashboard:**
```bash
streamlit run streamlit_demo/admin.py
```

This runs locally on http://localhost:8501

---

## Railway Dashboard Features

### Access Dashboard:
https://railway.app/dashboard

### Available Features:

1. **Deployments:** View deployment history, rollback if needed
2. **Variables:** Manage environment variables
3. **Metrics:** CPU, memory, network usage
4. **Logs:** Real-time and historical logs
5. **Settings:** Custom domains, health checks, restart policies

---

## Post-Deployment Checklist

- [ ] Deployment successful (green status in Railway)
- [ ] Health check endpoint responding (`/health`)
- [ ] Environment variables configured (all required vars set)
- [ ] GHL webhook connected (workflow active)
- [ ] Test contact tagged and responded to
- [ ] Logs showing successful interactions
- [ ] Lead scoring tags applied (Hot-Lead, Warm-Lead, Cold-Lead)

---

## Testing the Deployment

### Test 1: Health Check

```bash
curl https://your-deployment-url.railway.app/health
```

**Expected:** `{"status": "healthy", ...}`

---

### Test 2: Webhook Endpoint

```bash
curl -X POST https://your-deployment-url.railway.app/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "contact_id": "test123",
    "location_id": "your_location_id",
    "message": "I want to sell my house",
    "tags": ["Needs Qualifying"]
  }'
```

**Expected:** AI response within 2-3 seconds

---

### Test 3: Real Lead Flow

1. In GHL, select a test contact
2. Add tag: "Needs Qualifying"
3. Send message: "I'm looking to sell my property"
4. **Expected AI response:**
   ```
   Hey! Quick question: where's the property located?
   ```
5. Continue conversation:
   - User: "Austin, TX"
   - AI: "Got it. What's the condition of your home? Move-in ready, needs some work, or a fixer-upper?"

---

## Rollback Procedure (If Needed)

If deployment has issues:

```bash
railway status
```

Get the deployment ID of the previous working version, then:

```bash
railway rollback <deployment-id>
```

**Or via Dashboard:**
1. Go to Deployments
2. Find previous successful deployment
3. Click "Rollback to this deployment"

---

## Scaling (Future)

Railway auto-scales based on traffic. Default settings:
- **Min instances:** 0 (sleeps when inactive)
- **Max instances:** 1

**To increase capacity:**
1. Go to Railway Dashboard → Settings
2. Adjust "Replicas" or "Resources"

---

## Cost Estimation

**Railway Pricing (as of Jan 2026):**
- **Hobby Plan:** $5/month (500 hours execution time)
- **Pro Plan:** $20/month (unlimited execution time)

**Typical usage for Jorge's workflow:**
- ~1,000 leads/month
- ~2 seconds per lead
- **Total:** ~33 minutes/month execution time
- **Estimated cost:** $5/month (Hobby plan sufficient)

**Additional costs:**
- Anthropic API (Claude): ~$0.003 per interaction
- GHL API: Included in GHL subscription

---

## Support & Maintenance

### View Logs:
```bash
railway logs --tail 100
```

### Restart Service:
```bash
railway restart
```

### Update Code:
```bash
git push origin main
railway up  # Re-deploy
```

---

## Success Metrics to Monitor

### Week 1:
- [ ] 100% uptime (check Railway metrics)
- [ ] <3s response time (check logs)
- [ ] >90% messages under 160 chars (manual spot check)
- [ ] Lead tags applied correctly (check GHL contacts)

### Month 1:
- [ ] No deployment errors (check Railway logs)
- [ ] Lead conversion rate tracking (Hot leads → appointments)
- [ ] Jorge's feedback collected

---

## Next Steps After Deployment

1. **Monitor for 24 hours:**
   - Check logs every few hours
   - Verify AI responses match Jorge's tone
   - Ensure lead scoring tags are applied

2. **Train Jorge's team:**
   - Show them how to add/remove "Needs Qualifying" tag
   - Explain lead scoring (3+ questions = Hot)
   - Demonstrate re-engagement workflows

3. **Set up re-engagement automation:**
   - Create GHL workflow for 24h follow-up
   - Create GHL workflow for 48h follow-up
   - Use templates from `system_prompts.py` REENGAGEMENT_PROMPTS

4. **Optional enhancements (Phase 2):**
   - Analytics dashboard
   - A/B testing different tones
   - Voice integration
   - n8n workflow templates

---

## Emergency Contacts

- **Railway Status:** https://status.railway.app
- **Railway Support:** help@railway.app
- **Anthropic Status:** https://status.anthropic.com

---

**Deployment Guide Version:** 1.0.0
**Last Updated:** January 3, 2026
**Status:** Production Ready

🚀 **Ready to deploy!**

---

## Quick Reference Commands

```bash
# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set KEY=value

# Deploy
railway up

# Get deployment URL
railway domain

# View logs
railway logs

# Check status
railway status

# Restart
railway restart
```
