# 🚀 Railway Deployment - Simple Guide

## Quick Deploy (5 Steps)

### Step 1: Create Railway Project (2 min)

```bash
# Go to Railway
https://railway.app

# Click "New Project"
# Select "Deploy from GitHub repo"
# Connect your GitHub account
# Select: your-username/enterprisehub
```

### Step 2: Configure Build (1 min)

In Railway dashboard:
- **Root Directory**: `enterprisehub/ghl_real_estate_ai`
- **Build Command**: `pip install -r ../requirements.txt`
- **Start Command**: `streamlit run streamlit_demo/app.py --server.port $PORT --server.address 0.0.0.0`

### Step 3: Add Environment Variables (2 min)

Add these in Railway Settings → Variables:

```bash
# Required
PORT=8501
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Optional (for full features)
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### Step 4: Deploy (5 min)

Click "Deploy" - Railway will:
1. Clone your repo
2. Install dependencies
3. Start the app
4. Give you a public URL

### Step 5: Verify (1 min)

Visit your Railway URL:
- Check homepage loads
- Test AI Lead Scoring page (page 25)
- Verify demo mode works

## Done! 🎉

Your app is now live at: `your-app.railway.app`

---

## Troubleshooting

**Build fails?**
- Check requirements.txt path
- Verify Python version (3.9+)

**App won't start?**
- Check PORT variable is set
- Verify start command is correct

**Pages not loading?**
- Clear browser cache
- Check Railway logs for errors

---

## Next Steps

1. **Custom Domain**: Add in Railway settings
2. **SSL**: Automatic with Railway
3. **Monitoring**: Check Railway metrics
4. **Scale**: Upgrade plan if needed

Total time: ~10-15 minutes
