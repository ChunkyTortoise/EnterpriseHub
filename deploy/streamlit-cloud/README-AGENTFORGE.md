# AgentForge Deployment Guide

## Quick Deploy to Streamlit Cloud

**App**: AgentForge — Multi-LLM Orchestrator  
**Repo**: `ai-orchestrator`  
**Entry Point**: `app.py`  
**Streamlit Cloud URL**: `ct-agentforge.streamlit.app`

---

## Deployment Steps

1. **Go to Streamlit Cloud**
   - Navigate to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **Connect Repository**
   - Select GitHub as your repository provider
   - Search for and select `chunkytortoise/ai-orchestrator`
   - Alternatively, use the full repo URL: `https://github.com/chunkytortoise/ai-orchestrator`

3. **Configure Settings**
   - **Main file path**: `app.py`
   - **Python version**: `3.11`
   - **Requirements file**: `requirements.txt` (or `pyproject.toml` if present)

4. **Environment Variables**
   
   | Variable | Value | Required |
   |----------|-------|----------|
   | `DEMO_MODE` | `true` | No (enables demo mode without API keys) |
   | `OPENAI_API_KEY` | Your key | No (for production) |
   | `ANTHROPIC_API_KEY` | Your key | No (for production) |
   | `GOOGLE_API_KEY` | Your key | No (for production) |

   Set `DEMO_MODE=true` to run with mock providers.

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - App will be live at `ct-agentforge.streamlit.app`

---

## Features

- **Multi-Provider Support**: Claude, GPT-4, Gemini, Perplexity
- **Token-Aware Rate Limiting**: Avoid rate limit errors
- **Cost Tracking**: Per-request cost breakdown
- **Mock Provider**: Test without API keys

---

## Local Development

```bash
git clone https://github.com/chunkytortoise/ai-orchestrator
cd ai-orchestrator
pip install -r requirements.txt
streamlit run app.py
```

---

## Gumroad Product Listing

This app is associated with the **AgentForge** product on Gumroad:
- **Price**: $39
- **Tagline**: "One interface for Claude, GPT, Gemini, and Perplexity"
- **Live Demo**: https://ct-agentforge.streamlit.app
