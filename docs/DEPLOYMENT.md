# EnterpriseHub Deployment Guide

**Last Updated:** December 21, 2025

This guide provides deployment instructions for EnterpriseHub across multiple platforms.

---

## Quick Start - Streamlit Cloud Deployment

### Prerequisites

- GitHub account
- Streamlit Cloud account (free tier available)
- Repository pushed to GitHub

### Step 1 - Prepare Repository

Ensure these files exist in your repository root:

- `requirements.txt`
- `app.py`
- `.streamlit/config.toml` (optional, for theme customization)

### Step 2 - Deploy to Streamlit Cloud

1. Visit: <https://share.streamlit.io/>
2. Click "New app"
3. Connect GitHub account
4. Select: enterprise-hub repository
5. Branch: main
6. Main file path: app.py
7. Click "Deploy!"

### Step 3 - Configure Secrets (Optional)

For AI features (Content Engine, Agent Logic, Multi-Agent Workflow, Smart Forecast):

1. Go to app settings
2. Click "Secrets"
3. Add:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-xxx..."
   ```

---

## Alternative Deployment Methods

### Local Development

```bash
# Clone repository
git clone https://github.com/ChunkyTortoise/enterprise-hub.git
cd enterprise-hub

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the application
streamlit run app.py
```

### Docker Deployment

```bash
# Build image
docker build -t enterprise-hub .

# Run container
docker run -p 8501:8501 enterprise-hub
```

### Heroku Deployment

```bash
# Login to Heroku
heroku login

# Create app
heroku create your-app-name

# Set buildpack
heroku buildpacks:set heroku/python

# Deploy
git push heroku main

# Open app
heroku open
```

---

## Environment Variables

For production deployments, configure these environment variables:

- `ANTHROPIC_API_KEY`: Required for AI features (Content Engine, Data Detective AI, Agent Logic Claude mode, Multi-Agent Workflow, Smart Forecast)

---

## Troubleshooting

### Common Issues

**Issue**: App won't start

**Solution**: Check `requirements.txt` is in repository root

**Issue**: API features not working

**Solution**: Verify API key is set in Streamlit Cloud secrets

**Issue**: Import errors

**Solution**: Ensure all dependencies are listed in `requirements.txt`

---

## Success Criteria

- Live URL accessible
- All 10 modules visible in sidebar
- No import errors
- API features work (if configured)
- Dark mode toggle functional

---

**Live Demo**: <https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/>

**GitHub Repository**: <https://github.com/ChunkyTortoise/enterprise-hub>
