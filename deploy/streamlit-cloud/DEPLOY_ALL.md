# Streamlit Cloud Deployment Guide

**Status**: Ready for Deployment | **Apps**: 3 | **Est. Time**: 15 minutes

---

## Overview

This guide covers deployment of 3 Streamlit apps to Streamlit Cloud. All apps support **DEMO_MODE** which allows them to run without API keys for testing purposes.

### Apps to Deploy

| # | App Name | Repo | Entry Point | Target URL |
|---|----------|------|------------|------------|
| 1 | AgentForge | `ai-orchestrator` | `app.py` | `ct-agentforge.streamlit.app` |
| 2 | Prompt Lab | `prompt-engineering-lab` | `app.py` | `ct-prompt-lab.streamlit.app` |
| 3 | LLM Starter | `llm-integration-starter` | `app.py` | `ct-llm-starter.streamlit.app` |

---

## Prerequisites

- [ ] GitHub account with access to the repos
- [ ] Streamlit Cloud account (sign up at [share.streamlit.io](https://share.streamlit.io))
- [ ] GitHub repository URLs ready

### Repository URLs

```
AgentForge:     https://github.com/chunkytortoise/ai-orchestrator
Prompt Lab:     https://github.com/chunkytortoise/prompt-engineering-lab
LLM Starter:    https://github.com/chunkytortoise/llm-integration-starter
```

---

## Step-by-Step Deployment Process

### Phase 1: Prepare Your Streamlit Cloud Account

1. **Navigate to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "Sign in with GitHub"

2. **Verify Repository Access**
   - Ensure your GitHub account has access to `chunkytortoise` org
   - All three repos should be visible when connecting

---

### Phase 2: Deploy AgentForge (Priority 1)

1. **Create New App**
   - Click "New app" in Streamlit Cloud

2. **Connect Repository**
   - Repository: `chunkytortoise/ai-orchestrator`
   - Branch: `main` (or `master`)

3. **Configure Settings**
   ```
   Main file path: app.py
   Python version: 3.11
   Requirements file: requirements.txt
   ```

4. **Add Environment Variables**
   ```
   DEMO_MODE = true
   ```
   
   Optional (for production):
   ```
   OPENAI_API_KEY = (your key)
   ANTHROPIC_API_KEY = (your key)
   GOOGLE_API_KEY = (your key)
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait ~2-3 minutes for build
   - App URL: `ct-agentforge.streamlit.app`

---

### Phase 3: Deploy Prompt Lab (Priority 2)

1. **Create New App**
   - Click "New app" in Streamlit Cloud

2. **Connect Repository**
   - Repository: `chunkytortoise/prompt-engineering-lab`
   - Branch: `main`

3. **Configure Settings**
   ```
   Main file path: app.py
   Python version: 3.11
   Requirements file: requirements.txt
   ```

4. **Add Environment Variables**
   ```
   DEMO_MODE = true
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait ~2-3 minutes for build
   - App URL: `ct-prompt-lab.streamlit.app`

---

### Phase 4: Deploy LLM Starter (Priority 3)

1. **Create New App**
   - Click "New app" in Streamlit Cloud

2. **Connect Repository**
   - Repository: `chunkytortoise/llm-integration-starter`
   - Branch: `main`

3. **Configure Settings**
   ```
   Main file path: app.py
   Python version: 3.11
   Requirements file: requirements.txt
   ```

4. **Add Environment Variables**
   ```
   DEMO_MODE = true
   ```

5. **Deploy**
   - Click "Deploy"
   - Wait ~2-3 minutes for build
   - App URL: `ct-llm-starter.streamlit.app`

---

## Environment Variables Reference

### DEMO_MODE

Setting `DEMO_MODE=true` enables demo mode for all apps:

| App | Behavior in DEMO_MODE |
|-----|----------------------|
| AgentForge | Uses mock LLM provider with simulated responses |
| Prompt Lab | Mock LLM responses for prompt testing |
| LLM Starter | Mock responses, no API calls required |

### Production API Keys

For production use, add these environment variables:

| Variable | Provider | Required For |
|----------|----------|--------------|
| `OPENAI_API_KEY` | OpenAI | GPT-4, GPT-3.5 models |
| `ANTHROPIC_API_KEY` | Anthropic | Claude models |
| `GOOGLE_API_KEY` | Google | Gemini models |

---

## Troubleshooting

### Build Failures

1. **Python version mismatch**
   - Ensure Python 3.11 is selected
   - Check `requirements.txt` for version conflicts

2. **Missing dependencies**
   - Verify all packages are in `requirements.txt`
   - Some packages may need specific versions

3. **Import errors**
   - Check that the main file path is correct
   - Verify import paths match repo structure

### Runtime Errors

1. **API key errors**
   - Verify keys are set in Streamlit Cloud secrets
   - Keys are set per-app, not globally

2. **DEMO_MODE not working**
   - Confirm `DEMO_MODE=true` is set
   - Check app logs in Streamlit Cloud dashboard

---

## Post-Deployment Checklist

- [ ] All 3 apps are live and responding
- [ ] Test each app in DEMO_MODE
- [ ] Update Gumroad listings with live demo URLs
- [ ] Update portfolio site with new demo links
- [ ] Take screenshots for documentation

---

## Quick Reference

### Streamlit Cloud Dashboard
- URL: [share.streamlit.io](https://share.streamlit.io)
- Apps management: Click on app name → Settings

### App URLs (After Deployment)
```
AgentForge:     https://ct-agentforge.streamlit.app
Prompt Lab:     https://ct-prompt-lab.streamlit.app
LLM Starter:    https://ct-llm-starter.streamlit.app
```

---

## Next Steps

After deployment, update your monetization channels:

1. **Gumroad**: Add/update product listings with live demo links
2. **Portfolio Site**: Update test counts and demo URLs
3. **Cold Outreach**: Include demo links in email templates
4. **Reddit/HN**: Post Show HN with AgentForge demo link

---

*Last Updated: 2026-02-09*
