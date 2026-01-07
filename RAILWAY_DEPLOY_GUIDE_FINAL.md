# 🚀 Railway Deployment Guide - Jorge's GHL System

**Date**: January 6, 2026  
**Objective**: Deploy complete backend + frontend for Jorge  
**Time Required**: 30-45 minutes

---

## 🔑 Environment Variables Ready

```bash
# Jorge's GHL Credentials
GHL_LOCATION_ID=your_location_id_here
GHL_API_KEY=your_ghl_api_key_here

# Your Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
```

---

## 🎯 PART 1: Deploy Backend API (20 mins)

### Step 1: Create New Railway Project

1. **Go to**: https://railway.app/dashboard
2. **Click**: "New Project"
3. **Select**: "Deploy from GitHub repo"
4. **Choose**: `ChunkyTortoise/enterprisehub` (or your repo name)

### Step 2: Add Backend Service

1. Railway will show the repo
2. **Click**: "Add a service"
3. **Select**: The repository again
4. **Service Name**: `ghl-backend-api`

### Step 3: Configure Backend Root Directory

1. Click on the `ghl-backend-api` service
2. Go to **Settings** tab
3. Find **"Root Directory"** or **"Source"** section
4. **Set to**: `ghl_real_estate_ai`
5. **Save**

### Step 4: Set Backend Environment Variables

1. Still in the backend service
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** for each:

```bash
GHL_LOCATION_ID=your_location_id_here

GHL_API_KEY=your_ghl_api_key_here

ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

PORT=8000

PYTHON_VERSION=3.11

APP_ENV=production
```

### Step 5: Verify Backend Build Configuration

The `railway.json` in `ghl_real_estate_ai/` should automatically configure:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

If not, set manually in **Settings** → **Deploy**

### Step 6: Deploy Backend

1. Railway will automatically start deploying
2. **Watch the logs**: Click "View Logs" to monitor progress
3. **Wait** ~5-10 minutes for first build
4. Look for: `Uvicorn running on http://0.0.0.0:8000`

### Step 7: Generate Backend Domain

1. Once deployed successfully
2. Go to **Settings** → **Networking**
3. Click **"Generate Domain"**
4. **Copy the URL** (e.g., `https://ghl-backend-api-production.up.railway.app`)

### Step 8: Test Backend

```bash
# Replace with your actual URL
curl https://YOUR-BACKEND-URL.up.railway.app/health

# Expected response:
{"status":"healthy","timestamp":"2026-01-06T..."}
```

✅ **Backend Complete!** Save that URL - we need it for frontend.

---

## 🎨 PART 2: Deploy Frontend (Streamlit 5-Hub) (15 mins)

### Step 9: Add Frontend Service to Same Project

1. In the **same Railway project**
2. Click **"+ New"** → **"Service"**
3. **Select**: Same GitHub repo
4. **Service Name**: `ghl-frontend-streamlit`

### Step 10: Configure Frontend Root Directory

1. Click on the `ghl-frontend-streamlit` service
2. Go to **Settings** tab
3. **Root Directory**: `ghl_real_estate_ai/streamlit_demo`
4. **Save**

### Step 11: Set Frontend Environment Variables

1. Go to **"Variables"** tab
2. Add these variables:

```bash
# CRITICAL: Backend URL from Step 7
GHL_BACKEND_URL=https://YOUR-BACKEND-URL.up.railway.app

# Same credentials as backend
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

GHL_API_KEY=your_ghl_api_key_here

GHL_LOCATION_ID=your_location_id_here

PORT=8501

PYTHON_VERSION=3.11
```

**IMPORTANT**: Replace `https://YOUR-BACKEND-URL.up.railway.app` with the actual backend URL from Step 7!

### Step 12: Verify Frontend Build Configuration

The `railway.json` in `streamlit_demo/` should set:
- **Start Command**: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true`

### Step 13: Deploy Frontend

1. Railway auto-deploys after you add variables
2. **Watch the logs**: Monitor the build
3. **Wait** ~5-10 minutes for first build
4. Look for: `You can now view your Streamlit app in your browser.`

### Step 14: Generate Frontend Domain

1. Once deployed successfully
2. Go to **Settings** → **Networking**
3. Click **"Generate Domain"**
4. **Copy the URL** (e.g., `https://ghl-frontend-streamlit-production.up.railway.app`)

### Step 15: Test Frontend

1. **Open the frontend URL in your browser**
2. You should see: **5-Hub Command Center** interface
3. Check that all 5 hubs are accessible:
   - 🏢 Executive Command Center
   - 🧠 Lead Intelligence Hub
   - 🤖 Automation Studio
   - 💰 Sales Copilot
   - 📈 Ops & Optimization

---

## ✅ PART 3: Verification (5 mins)

### Backend Health Check

```bash
# Test backend
curl https://YOUR-BACKEND-URL/health

# Test API docs (should show Swagger UI)
open https://YOUR-BACKEND-URL/docs
```

### Frontend Integration Check

1. Open frontend URL in browser
2. Navigate to different hubs
3. Check browser console (F12) for errors
4. Verify data loads (mock or real)

### Check Railway Logs

1. Backend service → Deployments → View Logs
2. Frontend service → Deployments → View Logs
3. Look for any errors or warnings

---

## 📧 PART 4: Update Jorge's Email

Once both services are live, update the email:

**Backend URL**: `https://YOUR-ACTUAL-BACKEND-URL.up.railway.app`  
**Frontend URL**: `https://YOUR-ACTUAL-FRONTEND-URL.up.railway.app`

Send email to: **realtorjorgesalas@gmail.com**

---

## 🚨 Troubleshooting

### Backend Won't Start

**Issue**: Health check fails  
**Solution**:
1. Check logs for Python errors
2. Verify `requirements.txt` is in `ghl_real_estate_ai/`
3. Ensure root directory is set correctly
4. Check all environment variables are set

### Frontend Won't Connect to Backend

**Issue**: CORS errors or "Cannot connect to backend"  
**Solution**:
1. Verify `GHL_BACKEND_URL` is set correctly (with `https://`)
2. Check backend is running (visit `/health`)
3. No trailing slash in `GHL_BACKEND_URL`
4. Check frontend logs for connection errors

### Build Fails

**Issue**: Dependency errors  
**Solution**:
1. Check Python version is 3.11
2. Verify `requirements.txt` exists in correct location
3. Clear Railway build cache: Settings → Reset Build Cache

---

## 💰 Cost Estimate

**Railway Free Tier**: $5/month credit (500 hours)  
**This deployment**: 2 services × 730 hours = ~$10-15/month  
**Recommendation**: Add $10/month to cover both services

---

## 📊 Success Checklist

After deployment, verify:

- [ ] Backend service deployed and running
- [ ] Backend health endpoint returns 200 OK
- [ ] Backend API docs accessible at `/docs`
- [ ] Frontend service deployed and running
- [ ] Frontend loads in browser without errors
- [ ] All 5 hubs are accessible
- [ ] No CORS errors in browser console
- [ ] Both URLs documented
- [ ] Email to Jorge sent with URLs

---

## 🎯 Final URLs (Fill In After Deployment)

**Backend API**: `_______________________________`

**Frontend Dashboard**: `_______________________________`

**Jorge's Email**: realtorjorgesalas@gmail.com

---

**Ready to deploy? Start with Part 1 (Backend) above!** 🚀

Let me know when you complete each step and I'll help troubleshoot if needed.