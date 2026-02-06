# 🚀 DEPLOY NOW - Railway Quick Start

**Status**: Ready to deploy to Railway  
**Time Required**: 30-45 minutes  
**Date**: January 5, 2026

---

## ⚡ Quick Deploy (If You Have Everything Ready)

### Prerequisites
- ✅ Railway account: https://railway.app/
- ✅ GitHub repo connected: `ChunkyTortoise/enterprisehub`
- 🔑 Anthropic API key (can add later if needed)

### Deploy in 3 Steps

#### 1️⃣ Deploy Backend (15 mins)
```bash
# In Railway Dashboard:
1. New Project → Deploy from GitHub → enterprisehub
2. Add Service → Set root directory to: ghl_real_estate_ai
3. Add environment variables:
   - GHL_LOCATION_ID=REDACTED_LOCATION_ID
   - GHL_API_KEY=your_ghl_api_key_here
   - ANTHROPIC_API_KEY=sk-ant-YOUR-KEY (or placeholder)
4. Generate domain → Copy URL
5. Test: curl https://YOUR-URL/health
```

#### 2️⃣ Deploy Frontend (15 mins)
```bash
# In same Railway Project:
1. New Service → GitHub repo → enterprisehub
2. Root directory: . (root)
3. Add environment variables:
   - GHL_BACKEND_URL=https://YOUR-BACKEND-URL
   - ANTHROPIC_API_KEY=sk-ant-YOUR-KEY
   - GHL_API_KEY=[same as backend]
4. Generate domain → Copy URL
5. Test: Open URL in browser
```

#### 3️⃣ Verify & Send to Jorge (5 mins)
```bash
1. Test backend: curl https://backend-url/health
2. Test frontend: Open in browser, check Real Estate AI module
3. Update JORGE_HANDOFF_EMAIL.txt with live URLs
4. Send email to realtorjorgesales@gmail.com
```

---

## 🐌 Slower Step-by-Step Guide

See **RAILWAY_DEPLOYMENT_GUIDE.md** for detailed walkthrough with screenshots and troubleshooting.

---

## 🔑 If You Don't Have Anthropic API Key Yet

**No problem!** You can:

### Option A: Deploy with Placeholder (Recommended)
1. Set `ANTHROPIC_API_KEY=placeholder` for now
2. Services will deploy but won't fully work
3. Add real key later: Railway → Service → Variables → Edit
4. Services auto-restart with new key

### Option B: Wait and Deploy Later
1. Get your key: https://console.anthropic.com/settings/keys
2. Come back and run deploy steps above
3. Takes 30-45 mins total

---

## 📋 Jorge's Credentials (Already Documented)

```bash
GHL_LOCATION_ID=REDACTED_LOCATION_ID
GHL_API_KEY=your_ghl_api_key_here
Client Email: realtorjorgesales@gmail.com
```

---

## ✅ Success Criteria

Deployment is complete when:
- ✅ Backend health check returns `{"status":"healthy"}`
- ✅ Frontend loads in browser
- ✅ No CORS errors in browser console
- ✅ Jorge receives email with access details

---

## 🆘 Need Help?

**Detailed Guide**: See `RAILWAY_DEPLOYMENT_GUIDE.md`  
**Troubleshooting**: Included in guide above  
**Railway Support**: https://discord.gg/railway

---

**Ready to deploy? Follow Option A above and we'll have Jorge's system live in 30-45 minutes!** 🚀
