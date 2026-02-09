# Streamlit Community Cloud Deployment Guide

**Purpose**: Deploy 3 portfolio demo apps to Streamlit Community Cloud for the cold outreach campaign.

**Target URLs**:
- AgentForge (ai-orchestrator) → https://ct-agentforge.streamlit.app
- Prompt Lab (prompt-engineering-lab) → https://ct-prompt-lab.streamlit.app
- LLM Starter (llm-integration-starter) → https://ct-llm-starter.streamlit.app

---

## Pre-Deployment Verification ✅

All three repositories are deployment-ready:

### Repository Status
| Repository | GitHub URL | Entry Point | Status |
|------------|-----------|-------------|--------|
| ai-orchestrator | https://github.com/ChunkyTortoise/ai-orchestrator | `app.py` | ✅ Ready |
| prompt-engineering-lab | https://github.com/ChunkyTortoise/prompt-engineering-lab | `app.py` | ✅ Ready |
| llm-integration-starter | https://github.com/ChunkyTortoise/llm-integration-starter | `app.py` | ✅ Ready |

### Dependencies Verified
Each app has:
- ✅ `requirements.txt` with pinned versions
- ✅ `.streamlit/config.toml` (dark theme configuration)
- ✅ `.streamlit/secrets.toml.example` (template only)
- ✅ Clean git status (no uncommitted changes)
- ✅ **No API keys required** (all apps use mock data)

---

## Deployment Steps

### 1. Access Streamlit Community Cloud

1. Navigate to https://share.streamlit.io/
2. Sign in with the GitHub account linked to `ChunkyTortoise` organization
3. Click "New app" for each deployment

### 2. Deploy AgentForge (ai-orchestrator)

**App Configuration**:
- **Repository**: `ChunkyTortoise/ai-orchestrator`
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL**: `ct-agentforge` (custom subdomain)

**Settings**:
- Python version: 3.11
- No secrets required (uses mock data)
- Advanced settings: Use defaults

**Post-Deploy Verification**:
```bash
curl -I https://ct-agentforge.streamlit.app
# Expected: 200 OK (after initial build completes)
```

### 3. Deploy Prompt Lab (prompt-engineering-lab)

**App Configuration**:
- **Repository**: `ChunkyTortoise/prompt-engineering-lab`
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL**: `ct-prompt-lab` (custom subdomain)

**Settings**:
- Python version: 3.11
- No secrets required
- Advanced settings: Use defaults

**Post-Deploy Verification**:
```bash
curl -I https://ct-prompt-lab.streamlit.app
# Expected: 200 OK
```

### 4. Deploy LLM Starter (llm-integration-starter)

**App Configuration**:
- **Repository**: `ChunkyTortoise/llm-integration-starter`
- **Branch**: `main`
- **Main file path**: `app.py`
- **App URL**: `ct-llm-starter` (custom subdomain)

**Settings**:
- Python version: 3.11
- No secrets required (uses MockLLM)
- Advanced settings: Use defaults

**Post-Deploy Verification**:
```bash
curl -I https://ct-llm-starter.streamlit.app
# Expected: 200 OK
```

---

## Current Status (as of Feb 9, 2026)

### URL Status Check
All three URLs are responding with HTTP 303 redirects to Streamlit auth:
```
https://ct-agentforge.streamlit.app → 303 See Other
https://ct-prompt-lab.streamlit.app → 303 See Other
https://ct-llm-starter.streamlit.app → 303 See Other
```

**Interpretation**: URLs are reserved in Streamlit Cloud but apps need to be deployed/activated via the web interface.

---

## Troubleshooting

### Issue: "App is sleeping"
**Solution**: 
- Go to Streamlit Cloud dashboard
- Click on the sleeping app
- Click "Wake up" or wait for automatic wake on first visit

### Issue: Build failure due to dependencies
**Solution**:
```bash
# Test locally first
cd /path/to/repo
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Issue: Import errors
**Check**:
- All Python packages are in `requirements.txt`
- Entry point is `app.py` (not `streamlit_app.py`)
- No relative imports outside of package structure

### Issue: "Page not found"
**Solution**:
- Verify main file path is `app.py` (not `src/app.py` or other)
- Check repository branch is correct (`main`)
- Ensure repository is public or Streamlit Cloud has access

---

## Post-Deployment Tasks

### 1. Update Portfolio Website

**File**: `/Users/cave/Documents/GitHub/chunkytortoise.github.io`

Add live URLs to portfolio projects page:

```html
<div class="project">
  <h3>AgentForge Flow Visualizer</h3>
  <p>AI orchestration tracing and visualization</p>
  <a href="https://ct-agentforge.streamlit.app" target="_blank">Live Demo</a>
  <a href="https://github.com/ChunkyTortoise/ai-orchestrator" target="_blank">GitHub</a>
</div>

<div class="project">
  <h3>Prompt Engineering Lab</h3>
  <p>Pattern library, evaluation, and A/B testing for prompts</p>
  <a href="https://ct-prompt-lab.streamlit.app" target="_blank">Live Demo</a>
  <a href="https://github.com/ChunkyTortoise/prompt-engineering-lab" target="_blank">GitHub</a>
</div>

<div class="project">
  <h3>LLM Integration Starter</h3>
  <p>Production-ready LLM integration patterns with cost tracking</p>
  <a href="https://ct-llm-starter.streamlit.app" target="_blank">Live Demo</a>
  <a href="https://github.com/ChunkyTortoise/llm-integration-starter" target="_blank">GitHub</a>
</div>
```

### 2. Verify All Apps Load

Test each app manually:
1. Visit URL in browser
2. Verify app loads without errors
3. Test core functionality:
   - **AgentForge**: Generate mock trace, view visualizations
   - **Prompt Lab**: Browse patterns, run evaluations
   - **LLM Starter**: Test completions, view cost tracking

### 3. Performance Check

Monitor Streamlit Cloud metrics:
- Build time (target: < 2 minutes)
- App load time (target: < 5 seconds)
- Resource usage (should stay within free tier limits)

---

## Deployment Checklist

- [ ] All 3 apps deployed to Streamlit Cloud
- [ ] All URLs return 200 OK status
- [ ] Apps load in browser without errors
- [ ] Core functionality tested for each app
- [ ] Portfolio website updated with live URLs
- [ ] Screenshots taken for cold outreach materials
- [ ] Deployment issues documented

---

## Next Steps for Cold Outreach Campaign

Once all apps are live:
1. Update cold outreach templates with demo URLs
2. Create screenshots/GIFs for each app
3. Prepare 1-line descriptions for LinkedIn posts
4. Add to Gumroad product listings
5. Include in Fiverr gig descriptions

**Estimated Time**: 15-20 minutes per app (initial deployment)

**Support**: If deployment issues arise, check Streamlit Cloud logs via the dashboard.

---

**Last Updated**: February 9, 2026  
**Owner**: DevOps Infrastructure Agent
