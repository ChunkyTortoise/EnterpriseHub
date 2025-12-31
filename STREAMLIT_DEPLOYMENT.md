# Streamlit Cloud Deployment Guide

## Deploy Market Pulse Demo in 5 Minutes

### Step 1: Go to Streamlit Cloud
1. Visit: https://share.streamlit.io/
2. Sign in with your GitHub account

### Step 2: Create New App
1. Click **"New app"** button
2. Select repository: **ChunkyTortoise/EnterpriseHub**
3. Select branch: **main**
4. Main file path: **demo_app.py**
5. App URL (custom): **enterprisehub-market-pulse** (or any name you want)

### Step 3: Advanced Settings (Optional)
- Python version: **3.10** (recommended)
- Leave other settings as default

### Step 4: Deploy!
1. Click **"Deploy"** button
2. Wait 2-3 minutes for initial deployment
3. Your app will be live at: `https://[your-app-name].streamlit.app`

---

## What Happens Next?

✅ **Auto-deployment**: Every git push to main branch will auto-deploy
✅ **Free tier**: Unlimited public apps (with resource limits)
✅ **Custom domain**: Can add later in settings

---

## Expected Demo URL

Your demo will be live at something like:
```
https://enterprisehub-market-pulse-[random].streamlit.app
```

Copy this URL - you'll need it for:
1. Portfolio page update
2. LinkedIn posts
3. Upwork proposals

---

## Troubleshooting

### "ModuleNotFoundError"
- Make sure `requirements.txt` is in the repository root
- Check that all dependencies are listed

### "App not loading"
- Check Streamlit Cloud logs (click "Manage app" → "Logs")
- Verify `demo_app.py` imports work locally first

### "Out of resources"
- Free tier has limits: 1GB RAM, 1 CPU
- Market Pulse module should work fine within limits
- If issues, reduce data caching TTL

---

## After Deployment

1. **Test the live app** - Try different stock tickers
2. **Copy the URL** - Save it somewhere safe
3. **Update portfolio** - Add live demo link
4. **Share it** - LinkedIn, Upwork proposals, etc.

---

## Next Steps

Once your demo is live:
1. Update `portfolio/index.html` with the live demo URL
2. Add demo link to LinkedIn profile
3. Include in all Upwork proposals
4. Post on LinkedIn showcasing the live demo

**The demo URL is your #1 selling tool** - it lets clients see your work instantly!
