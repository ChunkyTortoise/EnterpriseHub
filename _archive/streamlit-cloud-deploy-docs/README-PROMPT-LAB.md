# Prompt Engineering Lab Deployment Guide

## Quick Deploy to Streamlit Cloud

**App**: Prompt Engineering Lab  
**Repo**: `prompt-engineering-lab`  
**Entry Point**: `app.py`  
**Streamlit Cloud URL**: `ct-prompt-lab.streamlit.app`

---

## Deployment Steps

1. **Go to Streamlit Cloud**
   - Navigate to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **Connect Repository**
   - Select GitHub as your repository provider
   - Search for and select `chunkytortoise/prompt-engineering-lab`
   - Alternatively, use the full repo URL: `https://github.com/chunkytortoise/prompt-engineering-lab`

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

   Set `DEMO_MODE=true` to run with mock LLM responses.

5. **Deploy**
   - Click "Deploy"
   - Wait 2-3 minutes for build
   - App will be live at `ct-prompt-lab.streamlit.app`

---

## Features

- **Prompt Template Management**: Create, save, and version prompts
- **A/B Testing**: Compare prompt variations with metrics
- **Temperature/Parameter Tuning**: Fine-tune response characteristics
- **Mock Mode**: Test prompts without API costs

---

## Local Development

```bash
git clone https://github.com/chunkytortoise/prompt-engineering-lab
cd prompt-engineering-lab
pip install -r requirements.txt
streamlit run app.py
```

---

## CLI Tool

This repo includes a `pel` CLI for command-line prompt management:

```bash
pip install -e .
pel --help
```

---

## Gumroad Product Listing

This app can be bundled with other AI tools or listed separately:
- **Suggested Price**: $19-29
- **Use Case**: Prompt engineering toolkit for developers
- **Live Demo**: https://ct-prompt-lab.streamlit.app
