# Streamlit Apps Deployment Guide

## Apps to Deploy

1. **ROI Calculator** (`roi-calculator/app.py`)
2. **Jorge Bot Command Center** (from `ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py`)
3. **BI Dashboard** (from `ghl_real_estate_ai/streamlit_demo/dashboard_app.py`)

---

## Quick Deploy: ROI Calculator (5 minutes)

### Step 1: Login to Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "Sign in" → "Continue with GitHub"
3. Authorize Streamlit Cloud

### Step 2: Deploy App
1. Click "New app" button (top right)
2. Fill in the form:
   - **Repository**: `ChunkyTortoise/EnterpriseHub`
   - **Branch**: `main`
   - **Main file path**: `deployment/streamlit-apps/roi-calculator/app.py`
   - **App URL** (custom): `enterprisehub-roi` (or your choice)
3. Click "Deploy!"

### Step 3: Verify
- App should load within 2-3 minutes
- Test the calculator with sample inputs
- Copy the live URL: `https://enterprisehub-roi.streamlit.app` (or similar)

---

## Jorge Bot Command Center (10 minutes)

**Note**: This app requires environment variables for GHL integration.

### Step 1: Prepare Environment Variables
You'll need these from your `.env` file:
```
GHL_API_KEY=your_ghl_key
CLAUDE_API_KEY=your_claude_key
DATABASE_URL=your_postgres_url (if using prod)
REDIS_URL=your_redis_url (if using prod)
```

### Step 2: Deploy
1. Click "New app" on Streamlit Cloud
2. Repository: `ChunkyTortoise/EnterpriseHub`
3. Branch: `main`
4. Main file path: `ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py`
5. **Advanced settings** → Add secrets:
   ```toml
   GHL_API_KEY = "your_key_here"
   CLAUDE_API_KEY = "your_key_here"
   DATABASE_URL = "postgresql://..."
   REDIS_URL = "redis://..."
   ```
6. Click "Deploy!"

### Step 3: Test
- App loads Jorge Bot controls
- Can view bot metrics
- Can trigger test conversations

---

## BI Dashboard (10 minutes)

Similar process to Jorge Bot Command Center.

### Main file path
`ghl_real_estate_ai/streamlit_demo/dashboard_app.py`

### Required secrets
Same as Jorge Bot (GHL, Claude, DB, Redis)

---

## Troubleshooting

**App won't start**:
- Check `requirements.txt` includes all dependencies
- Verify file path is correct
- Check Streamlit Cloud logs for import errors

**Environment variables not working**:
- Use Streamlit Secrets (TOML format), not .env files
- Secrets are case-sensitive
- Restart app after adding secrets

**Import errors**:
- Streamlit Cloud uses Python 3.11 by default
- Add any missing packages to requirements.txt
- Check for relative import issues

---

## Live URLs (After Deployment)

Track your deployed apps:

| App | URL | Status |
|-----|-----|--------|
| ROI Calculator | `https://enterprisehub-roi.streamlit.app` | 🟡 Pending |
| Jorge Bot | `https://jorge-bot-command.streamlit.app` | 🟡 Pending |
| BI Dashboard | `https://enterprisehub-dashboard.streamlit.app` | 🟡 Pending |

Update this table with actual URLs after deployment.

---

## Next Steps After Deployment

1. **Test all apps** with real data
2. **Add URLs to:**
   - GitHub README
   - Gumroad product descriptions
   - Upwork portfolio
   - LinkedIn profile
3. **Monitor usage** via Streamlit Cloud analytics
4. **Set up custom domains** (optional, paid feature)
