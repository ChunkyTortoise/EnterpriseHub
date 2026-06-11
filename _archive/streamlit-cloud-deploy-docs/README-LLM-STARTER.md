# LLM Integration Starter Deployment Guide

## Quick Deploy to Streamlit Cloud

**App**: LLM Integration Starter  
**Repo**: `llm-integration-starter`  
**Entry Point**: `app.py`  
**Streamlit Cloud URL**: `ct-llm-starter.streamlit.app`

---

## Deployment Steps

1. **Go to Streamlit Cloud**
   - Navigate to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **Connect Repository**
   - Select GitHub as your repository provider
   - Search for and select `chunkytortoise/llm-integration-starter`
   - Alternatively, use the full repo URL: `https://github.com/chunkytortoise/llm-integration-starter`

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
   - App will be live at `ct-llm-starter.streamlit.app`

---

## Features

- **Quick Start Templates**: Ready-to-use LLM integration patterns
- **Provider Switching**: Swap between Claude, GPT, Gemini easily
- **Streaming Support**: Real-time response streaming
- **Function Calling**: Easy function calling abstraction
- **Demo Mode**: Works without API keys

---

## Local Development

```bash
git clone https://github.com/chunkytortoise/llm-integration-starter
cd llm-integration-starter
pip install -r requirements.txt
streamlit run app.py
```

---

## CLI Tool

This repo includes a CLI for quick LLM integration:

```bash
pip install -e .
llm-starter --help
```

---

## Gumroad Product Listing

This app is a companion starter kit for LLM integrations:
- **Suggested Price**: $19-29
- **Tagline**: "Production-ready LLM integrations in minutes"
- **Use Case**: Developers building AI features
- **Live Demo**: https://ct-llm-starter.streamlit.app
