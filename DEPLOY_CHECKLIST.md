# ✅ Railway Deployment Checklist - Quick Reference

**Date**: January 6, 2026  
**For**: Jorge's GHL System  
**Full Guide**: See `RAILWAY_DEPLOY_GUIDE_FINAL.md`

---

## 🎯 Quick Deploy Steps

### PART 1: Backend API (20 mins)

1. [ ] Go to https://railway.app/dashboard
2. [ ] New Project → Deploy from GitHub → `ChunkyTortoise/enterprisehub`
3. [ ] Service name: `ghl-backend-api`
4. [ ] Settings → Root Directory → `ghl_real_estate_ai`
5. [ ] Variables → Add all backend env vars (see below)
6. [ ] Wait for deploy (~5-10 mins)
7. [ ] Settings → Networking → Generate Domain
8. [ ] **Test**: `curl https://YOUR-BACKEND-URL/health`
9. [ ] **SAVE BACKEND URL**: `_______________________________`

### PART 2: Frontend (15 mins)

10. [ ] Same project → + New → Service → Same repo
11. [ ] Service name: `ghl-frontend-streamlit`
12. [ ] Settings → Root Directory → `ghl_real_estate_ai/streamlit_demo`
13. [ ] Variables → Add all frontend env vars (INCLUDE BACKEND URL!)
14. [ ] Wait for deploy (~5-10 mins)
15. [ ] Settings → Networking → Generate Domain
16. [ ] **Test**: Open frontend URL in browser
17. [ ] **SAVE FRONTEND URL**: `_______________________________`

### PART 3: Verify (5 mins)

18. [ ] Backend health check returns `{"status":"healthy"}`
19. [ ] Frontend loads all 5 hubs
20. [ ] No CORS errors in browser console (F12)
21. [ ] Update email to Jorge with URLs
22. [ ] Send to: realtorjorgesalas@gmail.com

---

## 🔑 Environment Variables (Copy-Paste Ready)

### Backend Variables
```
GHL_LOCATION_ID=3xt4qayAh35BlDLaUv7P
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjN4dDRxYXlBaDM1QmxETGFVdjdQIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUzODYxMTU4OTk3LCJzdWIiOiJPcjRJbVNVeFVhclBKUXlhd0E1VyJ9._2BeC7R5a1X3R05N40iDcxLhy8Kz8L1vBydudDLL_As
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
PORT=8000
PYTHON_VERSION=3.11
APP_ENV=production
```

### Frontend Variables
```
GHL_BACKEND_URL=https://YOUR-BACKEND-URL-FROM-STEP-9.up.railway.app
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE
GHL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjN4dDRxYXlBaDM1QmxETGFVdjdQIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUzODYxMTU4OTk3LCJzdWIiOiJPcjRJbVNVeFVhclBKUXlhd0E1VyJ9._2BeC7R5a1X3R05N40iDcxLhy8Kz8L1vBydudDLL_As
GHL_LOCATION_ID=3xt4qayAh35BlDLaUv7P
PORT=8501
PYTHON_VERSION=3.11
```

**⚠️ CRITICAL**: Replace `YOUR-BACKEND-URL-FROM-STEP-9` with actual backend URL!

---

## 🚨 Quick Troubleshooting

**Backend won't start?**
- Check logs for errors
- Verify root directory is `ghl_real_estate_ai`
- Ensure all env vars are set

**Frontend won't connect?**
- Check `GHL_BACKEND_URL` is correct (with `https://`)
- Verify backend is running first
- Check for CORS errors in browser console

**Build fails?**
- Settings → Reset Build Cache
- Check Python version is 3.11
- Verify requirements.txt exists

---

## ✅ Success Criteria

✅ Backend: `curl https://backend-url/health` returns `{"status":"healthy"}`  
✅ Backend: Can access Swagger docs at `https://backend-url/docs`  
✅ Frontend: Loads in browser without errors  
✅ Frontend: All 5 hubs accessible  
✅ No CORS errors in browser console  

---

## 📧 Final Step

**Email Jorge**: realtorjorgesalas@gmail.com

Subject: 🚀 Your GHL 5-Hub System is LIVE!

Hi Jorge,

Your enhanced GHL Real Estate AI system is now deployed and ready!

**Access Your Dashboard**: [FRONTEND_URL]  
**API Documentation**: [BACKEND_URL]/docs

**Your 5 Command Centers**:
1. 🏢 Executive Command Center
2. 🧠 Lead Intelligence Hub  
3. 🤖 Automation Studio
4. 💰 Sales Copilot
5. 📈 Ops & Optimization

Let's schedule a walkthrough demo!

Best,
[Your Name]

---

**Total Time**: ~40 minutes  
**Cost**: ~$10-15/month on Railway

🚀 **Ready? Start with Step 1!**
