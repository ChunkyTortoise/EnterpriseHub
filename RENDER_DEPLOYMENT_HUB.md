# 🚀 Render Deployment Guide: Enterprise Hub (Consolidated)

This guide explains how to deploy the entire **Enterprise Hub** platform (including the consolidated GHL Real Estate AI module) to Render.com.

## 🎯 Overview
We are deploying the **Streamlit Dashboard** as the primary interface. The GHL Real Estate services are integrated directly into the dashboard modules.

## 🛠️ Step 1: Prepare Environment Variables
You will need the following keys for full functionality:
- `ANTHROPIC_API_KEY`: For ARETE-Architect and Content Engine.
- `GHL_API_KEY`: For GHL Real Estate integrations.
- `APP_ENV`: Set to `production`.
- `PYTHON_VERSION`: `3.11.4` (recommended).

## 🚀 Step 2: Deployment via Render Blueprint
1. Log in to [Render.com](https://render.com).
2. Click **"New +"** and select **"Blueprint"**.
3. Connect your GitHub repository: `ChunkyTortoise/EnterpriseHub`.
4. Render will detect the `render.yaml` file in the root directory.

## 📝 Step 3: Root render.yaml Configuration
Create a `render.yaml` in the root directory with the following content:

```yaml
services:
  - type: web
    name: enterprise-hub-platform
    env: python
    region: oregon
    plan: free
    branch: main
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
    envVars:
      - key: APP_ENV
        value: production
      - key: DEBUG
        value: false
      - key: ANTHROPIC_API_KEY
        sync: false
      - key: GHL_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.4
```

## 🔄 Step 4: GHL Webhook Support (Optional)
If you need the FastAPI webhook server to remain active for real-time GHL lead processing:
1. The `render.yaml` can be updated to include a second service, or
2. You can run a background thread in `app.py` (not recommended for production), or
3. Deploy the `ghl_real_estate_ai` directory as a separate Web Service on Render.

**Recommended:** Deploy the Dashboard first. If webhook processing is required, deploy the API as a second service using `ghl_real_estate_ai/render.yaml`.

## ✅ Verification
Once deployed, verify:
1. **ARETE-Architect**: Send a test message to ensure Claude API is connected.
2. **Real Estate AI**: Check the "Dashboard" tab to ensure mock/real data loads.
3. **ROI Calculators**: Verify interactive sliders and charts.
