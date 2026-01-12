# 🚀 Railway Quick-Deploy Guide (Single-Service)

**Date**: January 11, 2026  
**Objective**: Deploy the complete "Elite v4.0" Dashboard in 5 minutes.

---

## ⚡ Quick-Start Instructions

### Step 1: Create Railway Project
1. Go to [Railway Dashboard](https://railway.app/dashboard).
2. Click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Select your repository.

### Step 2: Configure Service
1. Click the newly created service.
2. Go to **Settings** -> **General** -> **Service Name**: Change to `ghl-real-estate-ai`.
3. Go to **Settings** -> **Build** -> **Root Directory**: Leave as `/` (root).

### Step 3: Set Environment Variables
Go to **Variables** tab and add:

```bash
# GHL Credentials
GHL_LOCATION_ID=your_location_id
GHL_API_KEY=your_api_key

# AI Engine
ANTHROPIC_API_KEY=sk-ant-xxx

# App Config
PYTHON_VERSION=3.11
PYTHONPATH=.
PORT=8501
```

### Step 4: Verify Start Command
Railway will automatically pick up the `railway.json` in the root. The command used is:
`export PYTHONPATH=$PYTHONPATH:. && streamlit run ghl_real_estate_ai/streamlit_demo/app.py --server.port $PORT --server.address 0.0.0.0`

### Step 5: Generate Domain
1. Go to **Settings** -> **Networking**.
2. Click **"Generate Domain"**.
3. Copy the URL (e.g., `https://ghl-real-estate-ai-production.up.railway.app`).

---

## ✅ Post-Deployment Check
1. Open the URL.
2. Verify all 5 Hubs load correctly.
3. Check **Lead Intelligence Hub** -> **Property Matcher** to see the new 15-factor engine in action.

---

## 🚨 Local vs Cloud
- **Local (Port 8515)**: Best for rapid testing and dev.
- **Cloud (Railway)**: Best for sharing with Jorge and clients.