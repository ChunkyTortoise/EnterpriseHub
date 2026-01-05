# Render.com Deployment Guide - Phase 2

**Quick deployment to Render.com free tier**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Sign Up for Render
1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Authorize Render to access your repositories

### Step 2: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `ChunkyTortoise/EnterpriseHub`
3. Select the `ghl-real-estate-ai` directory (or configure root directory)

### Step 3: Configure Service

**Basic Settings:**
- **Name:** `ghl-real-estate-ai`
- **Region:** Oregon (US West) - or closest to you
- **Branch:** `main`
- **Runtime:** Python 3

**Build & Deploy:**
- **Root Directory:** `ghl-real-estate-ai` (if deploying from subdirectory)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Plan:**
- Select **"Free"** tier

### Step 4: Set Environment Variables

Click **"Environment"** tab and add:

```
ANTHROPIC_API_KEY=<your_claude_api_key>
GHL_API_KEY=<your_ghl_api_key>
ENVIRONMENT=production
PYTHON_VERSION=3.9.18
```

### Step 5: Deploy!

1. Click **"Create Web Service"**
2. Render will automatically:
   - Pull your code from GitHub
   - Install dependencies
   - Start the server
   - Assign a URL: `https://ghl-real-estate-ai.onrender.com`

**Deployment time:** ~5-10 minutes

---

## ✅ Post-Deployment Verification

### Test 1: Health Check
```bash
curl https://your-app.onrender.com/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "GHL Real Estate AI",
  "version": "1.0.0"
}
```

### Test 2: Phase 2 Analytics
```bash
curl https://your-app.onrender.com/api/analytics/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "analytics",
  "timestamp": "..."
}
```

### Test 3: Create A/B Test
```bash
curl -X POST "https://your-app.onrender.com/api/analytics/experiments?location_id=demo" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test",
    "variant_a": {"msg": "Hi"},
    "variant_b": {"msg": "Hello"},
    "metric": "conversion_rate"
  }'
```

---

## 📊 Render.com Features

**Free Tier Includes:**
- ✅ 750 hours/month (enough for one service 24/7)
- ✅ 512 MB RAM
- ✅ Auto-deploy on git push
- ✅ Free SSL certificate
- ✅ Custom domain support
- ⚠️ Spins down after 15 mins of inactivity (cold starts ~30 seconds)

**Paid Tier ($7/month):**
- ✅ No spin-down (always on)
- ✅ 1 GB RAM
- ✅ Better performance

---

## 🔧 Automatic Deployment

Once configured, Render auto-deploys on every push to main:

```bash
cd ghl-real-estate-ai
git add .
git commit -m "Update feature"
git push origin main
# Render automatically deploys in ~5 mins
```

---

## 🐛 Troubleshooting

### Issue: Build Fails
**Solution:** Check build logs in Render dashboard
- Ensure `requirements.txt` is correct
- Check Python version compatibility

### Issue: App Crashes
**Solution:** Check runtime logs
- Verify environment variables are set
- Check for missing dependencies

### Issue: Cold Starts Slow
**Solution:** Upgrade to paid tier or use Railway instead

### Issue: Can't Find Root Directory
**Solution:** In Render settings:
- Set **Root Directory** to `ghl-real-estate-ai`
- Or deploy from repository root

---

## 📁 Files for Render

### render.yaml (Optional Auto-Config)
Already created in repository. Render can auto-detect this.

### requirements.txt
Already exists with all dependencies.

---

## 🎯 Production Best Practices

### 1. Set Up Health Checks
Render automatically uses `/health` endpoint.

### 2. Configure Auto-Deploy
- Enable in Render dashboard
- Deploys on every push to main

### 3. Monitor Logs
- Access via Render dashboard
- Real-time log streaming
- Error notifications

### 4. Set Up Alerts
- Configure email notifications
- Monitor uptime
- Track deployment status

---

## 💰 Cost Comparison

**Render Free:**
- ✅ $0/month
- ⚠️ Spins down after 15 mins inactive
- Best for: Demos, testing

**Render Starter ($7/month):**
- ✅ Always on
- ✅ Better performance
- Best for: Small production use

**Railway ($5/month + usage):**
- ✅ More flexible
- ✅ Better for multiple services
- Best for: Growing projects

---

## 🚀 Alternative: Fly.io

If Render doesn't work, try Fly.io:

```bash
# Install Fly CLI
brew install flyctl

# Login
fly auth login

# Deploy
cd ghl-real-estate-ai
fly launch
fly secrets set ANTHROPIC_API_KEY=xxx GHL_API_KEY=xxx
fly deploy
```

---

## 📞 Support

**Render Docs:** https://render.com/docs  
**Community:** https://community.render.com  
**Status:** https://status.render.com

---

## ✅ Success Checklist

- [ ] Render account created
- [ ] Repository connected
- [ ] Web service created
- [ ] Environment variables set
- [ ] First deployment successful
- [ ] Health check passing
- [ ] Phase 2 endpoints tested
- [ ] Auto-deploy enabled

---

**Estimated Total Time:** 5-10 minutes

**Result:** Phase 2 live and accessible at your Render URL!

---

**Next:** Share the URL with Jorge and demo the features!
