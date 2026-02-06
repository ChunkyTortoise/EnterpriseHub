# 🚀 Railway Deployment Guide - GHL Real Estate AI

## Quick Deploy Steps

### 1. Link to Railway Project
```bash
cd enterprisehub/ghl_real_estate_ai/streamlit_demo
railway link
# Select: responsible-heart
```

### 2. Set Environment Variables
```bash
railway variables set ANTHROPIC_API_KEY=your_key_here
railway variables set STREAMLIT_SERVER_PORT=8501
railway variables set STREAMLIT_SERVER_HEADLESS=true
```

### 3. Deploy
```bash
railway up
```

### 4. Get Domain
```bash
railway domain
# Copy the URL: https://your-app.up.railway.app
```

## Verification

1. Visit your Railway URL
2. Check all 5 hubs load:
   - 🏢 Executive Command Center
   - 🧠 Lead Intelligence Hub
   - 🤖 Automation Studio
   - 💰 Sales Copilot
   - 📈 Ops & Optimization

## Troubleshooting

If deployment fails:
```bash
railway logs
```

Common issues:
- Missing ANTHROPIC_API_KEY → Add via Railway dashboard
- Port conflicts → Ensure PORT variable is set by Railway
- Import errors → Check requirements.txt is complete

---

**Current Status:** Ready to deploy
**Estimated Time:** 5 minutes
