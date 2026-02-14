# Streamlit Cloud Deployment Guide

**Status**: Ready for deployment (all pre-flight checks passed)  
**Apps**: 3 repos → 3 cloud deployments  
**Time to deploy**: < 5 minutes total  
**Deployment URL**: https://share.streamlit.io

---

## Pre-Flight Checklist ✅

All verified on 2026-02-14:

- ✅ `requirements.txt` cleaned (removed `-e .` editable installs)
- ✅ `.streamlit/config.toml` configured with theme + server settings
- ✅ Entry point files exist and syntax-validated
- ✅ No hardcoded secrets found
- ✅ Python 3.11 compatibility confirmed
- ✅ All repos on `main` branch

---

## App 1: AgentForge Flow Visualizer

**Repository**: `ai-orchestrator`  
**GitHub URL**: https://github.com/ChunkyTortoise/ai-orchestrator  
**Target URL**: https://ct-agentforge.streamlit.app  

### Deployment Steps

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Configure:
   - **Repository**: ChunkyTortoise/ai-orchestrator
   - **Branch**: main
   - **Main file path**: `streamlit_app.py`
   - **App URL**: ct-agentforge (or choose custom subdomain)
4. **Advanced settings** (optional):
   - Python version: 3.11
   - No secrets needed (runs with mock LLM)
5. Click **Deploy**

### Features Available

- Multi-provider LLM orchestration visualization
- Cost tracking dashboard
- Rate limiting simulator
- Provider comparison
- Trace visualization

### Environment Variables (Optional)

For live API integration (not required for demo):

```
GOOGLE_API_KEY=your_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
```

---

## App 2: Prompt Engineering Lab

**Repository**: `prompt-engineering-lab`  
**GitHub URL**: https://github.com/ChunkyTortoise/prompt-engineering-lab  
**Target URL**: https://ct-prompt-lab.streamlit.app  

### Deployment Steps

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Configure:
   - **Repository**: ChunkyTortoise/prompt-engineering-lab
   - **Branch**: main
   - **Main file path**: `app.py`
   - **App URL**: ct-prompt-lab (or choose custom subdomain)
4. **Advanced settings** (optional):
   - Python version: 3.11
   - No secrets needed (pure prompt engineering toolkit)
5. Click **Deploy**

### Features Available

- 📚 Pattern Library (20+ prompt patterns)
- 📊 Prompt Evaluator (ROUGE, faithfulness, relevance)
- ⚖️ A/B Comparison
- 🏆 Benchmarking

### Environment Variables

**None required** — fully functional without API keys (uses local pattern evaluation)

---

## App 3: LLM Integration Starter

**Repository**: `llm-integration-starter`  
**GitHub URL**: https://github.com/ChunkyTortoise/llm-integration-starter  
**Target URL**: https://ct-llm-starter.streamlit.app  

### Deployment Steps

1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Configure:
   - **Repository**: ChunkyTortoise/llm-integration-starter
   - **Branch**: main
   - **Main file path**: `app.py`
   - **App URL**: ct-llm-starter (or choose custom subdomain)
4. **Advanced settings** (optional):
   - Python version: 3.11
   - No secrets needed (runs with MockLLM)
5. Click **Deploy**

### Features Available

- Basic completion
- SSE streaming
- Function calling
- RAG pipeline
- Cost & latency dashboard

### Environment Variables (Optional)

For live API integration (not required for demo):

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
DEFAULT_PROVIDER=claude
DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

---

## Troubleshooting

### Build Fails: "No module named 'xxx'"

**Cause**: Missing dependency in `requirements.txt`  
**Fix**: Check `/Users/cave/Documents/GitHub/<repo>/requirements.txt` and verify all imports in `app.py` have matching packages

### App Crashes on Startup

**Cause**: Entry point file not found  
**Fix**: Verify "Main file path" matches actual file:
- ai-orchestrator: `streamlit_app.py` (not `app.py`)
- prompt-engineering-lab: `app.py`
- llm-integration-starter: `app.py`

### Theme Not Applied

**Cause**: `.streamlit/config.toml` not found  
**Fix**: All repos have this file — check deployment logs

### ImportError: "No module named 'agentforge'"

**Cause**: Code tries to import local package as installed package  
**Fix**: Ensure all imports use relative paths or fully qualified names within the repo structure:
- ai-orchestrator: `from agentforge.xxx import yyy` → code is in `/agentforge/` directory
- prompt-engineering-lab: `from prompt_lab.xxx import yyy` → code is in `/prompt_lab/` directory
- llm-integration-starter: `from llm_starter.xxx import yyy` → code is in `/llm_starter/` directory

### Secrets Not Working

**Cause**: Streamlit Cloud secrets syntax differs from `.env`  
**Fix**: In Streamlit Cloud UI:
1. Click "Settings" → "Secrets"
2. Use TOML format:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
OPENAI_API_KEY = "sk-..."
```

---

## Post-Deployment Verification

After deployment, test each app:

### AgentForge
1. Select a prompt from dropdown
2. Click "Run Flow"
3. Verify trace visualization renders
4. Check cost tracker updates

### Prompt Engineering Lab
1. Navigate to "Pattern Library" tab
2. Select a pattern, verify example renders
3. Go to "Evaluate" tab
4. Enter test prompt, click "Evaluate"
5. Verify metrics display (faithfulness, relevance, etc.)

### LLM Integration Starter
1. Navigate to "Completion" tab
2. Enter prompt, click "Complete"
3. Verify mock response appears
4. Check "Dashboard" tab for cost/latency metrics

---

## Expected URLs After Deployment

| App | Expected URL | Status |
|-----|-------------|--------|
| AgentForge | https://ct-agentforge.streamlit.app | Pending deployment |
| Prompt Lab | https://ct-prompt-lab.streamlit.app | Pending deployment |
| LLM Starter | https://ct-llm-starter.streamlit.app | Pending deployment |

---

## Files Modified for Deployment

### ai-orchestrator
- `/Users/cave/Documents/GitHub/ai-orchestrator/requirements.txt` — Removed `-e .`, added all dependencies from `pyproject.toml`

### prompt-engineering-lab
- `/Users/cave/Documents/GitHub/prompt-engineering-lab/requirements.txt` — Removed `-e .`, added `click>=8.0`

### llm-integration-starter
- `/Users/cave/Documents/GitHub/llm-integration-starter/requirements.txt` — Removed `-e .`, kept explicit dependencies

---

## Deployment Architecture

```
GitHub Repos (main branch)
    ↓
Streamlit Cloud Build
    ↓
requirements.txt → pip install
    ↓
Entry point file (app.py / streamlit_app.py)
    ↓
Live app at *.streamlit.app
```

---

## Quick Deploy Commands

After pushing changes to GitHub:

```bash
# Verify all changes committed
cd /Users/cave/Documents/GitHub/ai-orchestrator && git status
cd /Users/cave/Documents/GitHub/prompt-engineering-lab && git status
cd /Users/cave/Documents/GitHub/llm-integration-starter && git status

# If uncommitted changes, commit them
git add requirements.txt
git commit -m "fix: Update requirements.txt for Streamlit Cloud compatibility"
git push origin main
```

Then deploy via https://share.streamlit.io UI (steps above).

---

**Version**: 1.0  
**Last Updated**: 2026-02-14  
**Author**: DevOps Infrastructure Agent  
**Next Steps**: Push `requirements.txt` changes to GitHub, then deploy via Streamlit Cloud UI
