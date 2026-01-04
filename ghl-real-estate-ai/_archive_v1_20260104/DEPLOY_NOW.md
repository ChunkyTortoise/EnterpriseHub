# 🚀 Deploy Now - Quick Reference

**Status:** ✅ Production Ready (31/31 tests passing)

---

## Step 1: Login (30 seconds)

```bash
railway login
```

A browser window will open. Log in to Railway.

---

## Step 2: Deploy (5 minutes)

### Option A: Automated (Recommended)

```bash
./deploy.sh
```

The script will guide you through everything.

### Option B: Manual

```bash
# Initialize project
railway init

# Set environment variables
railway variables set ANTHROPIC_API_KEY="sk-ant-..."
railway variables set GHL_API_KEY="your_ghl_key"
railway variables set GHL_LOCATION_ID="your_location_id"

# Deploy
railway up

# Get URL
railway domain
```

---

## Step 3: GHL Webhook (2 minutes)

In GoHighLevel:
1. Create Workflow
2. Trigger: Tag Added → "Needs Qualifying"
3. Action: Send Webhook → `https://your-url.railway.app/ghl/webhook`
4. Save & Activate

---

## Test

Tag a contact "Needs Qualifying" and send: "I want to sell"

Expected response: "Hey! Quick question: where's the property located?"

---

## Done!

Monitor logs: `railway logs`

Full guide: `DEPLOYMENT_GUIDE.md`

---

✅ **You're ready to go live!**
