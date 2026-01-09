# 🚂 Railway Deployment Guide - EnterpriseHub for Jorge

**Date**: January 5, 2026  
**Client**: Jorge Salas (realtorjorgesalas@gmail.com)  
**Status**: Ready to Deploy

---

## 📋 Pre-Deployment Checklist

Before starting deployment, ensure you have:

- ✅ GitHub repository: `ChunkyTortoise/enterprisehub` (public or Railway has access)
- ✅ Railway account created (https://railway.app/)
- ✅ Credit card added to Railway (required for free tier)
- 🔑 Anthropic API key ready (can add later)
- ✅ Jorge's GHL credentials documented below

---

## 🔑 Required Environment Variables

### Jorge's GoHighLevel Credentials

```bash
GHL_LOCATION_ID=REDACTED_LOCATION_ID
GHL_API_KEY=REDACTED_GHL_KEY
```

### Anthropic API Key (You'll provide)

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Get your key**: https://console.anthropic.com/settings/keys

---

## 🚀 DEPLOYMENT STEP-BY-STEP

### Phase 1: Deploy Backend (GHL Real Estate AI)

#### Step 1: Create New Project
1. Go to https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose repository: `ChunkyTortoise/enterprisehub`

#### Step 2: Configure Backend Service
1. Railway will auto-detect the repository
2. Click **"Add Service"** → **"GitHub Repo"**
3. **Service Name**: `ghl-real-estate-ai-backend`
4. **Root Directory**: Set to `ghl_real_estate_ai`
   - Click service → Settings → Root Directory → `ghl_real_estate_ai`

#### Step 3: Set Environment Variables
1. Click on your backend service
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add:

```bash
# Required immediately
GHL_LOCATION_ID=REDACTED_LOCATION_ID
GHL_API_KEY=REDACTED_GHL_KEY

# Add when you have it (service won't fully start without this)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional (Railway sets these automatically)
PORT=8000
PYTHONUNBUFFERED=1
```

#### Step 4: Verify Configuration
1. Check that `railway.json` is detected in `ghl_real_estate_ai/` folder
2. Build command should be: `pip install -r requirements.txt`
3. Start command should be: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

#### Step 5: Deploy!
1. Railway will automatically trigger deployment
2. Watch the build logs (takes ~5-10 minutes first time)
3. Once deployed, click **"Settings"** → **"Networking"** → **"Generate Domain"**
4. **Copy the backend URL** (example: `https://ghl-real-estate-ai-backend-production.up.railway.app`)

#### Step 6: Test Backend
```bash
# Test health endpoint
curl https://YOUR-BACKEND-URL.railway.app/health

# Expected response:
{"status":"healthy","timestamp":"2026-01-05T..."}
```

---

### Phase 2: Deploy Frontend (EnterpriseHub Dashboard)

#### Step 1: Add Frontend Service
1. In the same Railway project, click **"New Service"**
2. Select **"GitHub Repo"** → Choose `ChunkyTortoise/enterprisehub` again
3. **Service Name**: `enterprisehub-frontend`
4. **Root Directory**: `.` (root - leave blank or set to `/`)

#### Step 2: Set Environment Variables
1. Go to frontend service → **"Variables"** tab
2. Add these variables:

```bash
# Backend URL from Phase 1 (REQUIRED)
GHL_BACKEND_URL=https://YOUR-BACKEND-URL.railway.app

# Same as backend
ANTHROPIC_API_KEY=sk-ant-your-key-here
GHL_API_KEY=REDACTED_GHL_KEY

# Optional
PORT=8501
PYTHONUNBUFFERED=1
```

#### Step 3: Verify Configuration
1. Check that `railway.json` exists in root directory
2. Build command: `pip install -r requirements.txt`
3. Start command: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

#### Step 4: Deploy!
1. Railway auto-deploys
2. Wait ~5-10 minutes for build
3. Generate domain: **Settings** → **"Networking"** → **"Generate Domain"**
4. **Copy the frontend URL** (example: `https://enterprisehub-frontend-production.up.railway.app`)

#### Step 5: Test Frontend
1. Open the frontend URL in your browser
2. Should see EnterpriseHub dashboard load
3. Navigate to **"🏠 Real Estate AI"** in sidebar
4. Verify it connects to backend

---

## ✅ Post-Deployment Verification

### Backend Health Check
```bash
curl https://YOUR-BACKEND-URL.railway.app/health
# Expected: {"status":"healthy"}

curl https://YOUR-BACKEND-URL.railway.app/docs
# Expected: Swagger API documentation page
```

### Frontend Verification
1. ✅ Dashboard loads without errors
2. ✅ Sidebar navigation works
3. ✅ Real Estate AI module is accessible
4. ✅ No CORS errors in browser console (F12)

### Integration Test
1. Open frontend → Real Estate AI
2. Test should show analytics connecting to backend
3. Check Railway logs for both services (no errors)

---

## 🔧 Adding Anthropic API Key Later

If you don't have your API key yet:

1. Go to https://console.anthropic.com/settings/keys
2. Create new key → Copy it
3. In Railway dashboard:
   - Open **backend service** → Variables → Add/Edit `ANTHROPIC_API_KEY`
   - Open **frontend service** → Variables → Add/Edit `ANTHROPIC_API_KEY`
4. Services will auto-restart with new key

---

## 📊 Monitoring & Logs

### View Logs in Railway
1. Click on service (backend or frontend)
2. Go to **"Deployments"** tab
3. Click latest deployment → **"View Logs"**
4. Monitor for errors or performance issues

### Key Metrics to Watch
- **Build Time**: Should be 5-10 minutes (first time), 2-5 minutes (subsequent)
- **Response Time**: Backend `/health` should respond in <500ms
- **Memory Usage**: Backend ~150-300 MB, Frontend ~200-400 MB
- **Uptime**: Railway free tier = 500 hours/month (~$5 credit)

### Setting Up Alerts (Optional)
1. Railway → Project Settings → Notifications
2. Enable Slack/Discord/Email notifications
3. Get alerts for:
   - Deployment failures
   - Service crashes
   - Resource limits exceeded

---

## 🚨 Troubleshooting

### Backend won't start
**Error**: `Health check failed`

**Solutions**:
1. Check `ANTHROPIC_API_KEY` is set correctly
2. Verify `GHL_API_KEY` and `GHL_LOCATION_ID` are set
3. Check logs for import errors
4. Ensure root directory is set to `ghl_real_estate_ai`

### Frontend won't connect to backend
**Error**: `CORS policy blocked` or `Network error`

**Solutions**:
1. Verify `GHL_BACKEND_URL` is set with full URL (including `https://`)
2. Check backend is running (visit `/health` endpoint)
3. Ensure no trailing slashes in `GHL_BACKEND_URL`

### Build fails
**Error**: `ModuleNotFoundError` or dependency issues

**Solutions**:
1. Check `requirements.txt` is in correct location
2. Verify Python version (should use 3.9+)
3. Clear cache: Settings → General → Reset Build Cache

### Out of Railway credits
**Error**: Services suspended after 500 hours

**Solutions**:
1. Upgrade to Hobby plan ($5/month) for unlimited hours
2. Or add more credits to account
3. Services auto-resume when credits added

---

## 💰 Cost Breakdown

### Railway Free Tier
- **$5 credit per month** (included free)
- **500 execution hours per month**
- **1 GB memory per service**
- **100 GB bandwidth**

### For This Deployment
- **2 services** (backend + frontend)
- **Estimated usage**: ~350 hours/month (both services combined)
- **Cost**: **$0** (within free tier)

### If Scaling Needed
- **Hobby Plan**: $5/month (unlimited hours, better resources)
- **Pro Plan**: $20/month (teams, more memory, priority support)

---

## 📧 Final Step: Email Jorge

Once both services are deployed and tested:

1. Update `JORGE_HANDOFF_EMAIL.txt` with live URLs:
   - Replace `[BACKEND_URL - pending Agent 2]` with actual backend URL
   - Replace `[FRONTEND_URL - pending Agent 3]` with actual frontend URL

2. Send email to: **realtorjorgesalas@gmail.com**

3. Subject: **🚀 Your EnterpriseHub System is LIVE!**

---

## 🎯 Quick Reference

### Backend URL
```
https://ghl-real-estate-ai-backend-production.up.railway.app
```
*(Replace with your actual URL after deployment)*

### Frontend URL
```
https://enterprisehub-frontend-production.up.railway.app
```
*(Replace with your actual URL after deployment)*

### Health Endpoints
- Backend: `{BACKEND_URL}/health`
- Backend API Docs: `{BACKEND_URL}/docs`
- Frontend: `{FRONTEND_URL}` (main dashboard)

---

## ✅ Deployment Complete Checklist

Use this after deploying:

- [ ] Backend service created and running on Railway
- [ ] Frontend service created and running on Railway
- [ ] Environment variables set for both services
- [ ] Anthropic API key added (or placeholder set)
- [ ] Backend health check returns 200 OK
- [ ] Frontend loads in browser without errors
- [ ] Frontend → Real Estate AI module accessible
- [ ] No CORS errors in browser console
- [ ] URLs documented and saved
- [ ] Jorge's email updated with live URLs
- [ ] Email sent to Jorge
- [ ] Railway monitoring/alerts configured (optional)

---

## 🆘 Support & Next Steps

### If You Need Help
- **Railway Docs**: https://docs.railway.app/
- **Railway Discord**: https://discord.gg/railway
- **Support**: support@railway.app

### After Deployment
1. Monitor logs for first 24 hours
2. Respond to Jorge's questions
3. Schedule follow-up demo if needed
4. Add additional GHL sub-accounts as requested

---

**Deployment Guide Created**: January 5, 2026  
**Ready to Deploy**: ✅ YES  
**Estimated Time**: 30-45 minutes (including testing)

---

**Let's ship this! 🚀**
