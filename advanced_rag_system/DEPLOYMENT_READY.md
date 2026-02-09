# Advanced RAG System & AgentForge - Deployment Checklist

## ✅ Pre-Deployment Status

| Item | Status | Notes |
|------|--------|-------|
| RAG demo app | ✅ Ready | `src/demo_app.py` |
| AgentForge demo | ✅ Ready | `src/agent_forge_demo.py` |
| Requirements file | ✅ Ready | `requirements.txt` |
| Streamlit config | ✅ Ready | `.streamlit/config.toml` |
| Secrets template | ✅ Ready | `.streamlit/secrets.toml` |
| Demo mode support | ✅ Ready | Works without API keys |

## 📁 Deployment Files

```
advanced_rag_system/
├── src/
│   ├── demo_app.py           # Advanced RAG demo
│   └── agent_forge_demo.py   # AgentForge demo
├── requirements.txt           # Full dependencies (for production)
├── requirements_demo.txt      # Lightweight demo dependencies ⭐ RECOMMENDED
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml         # Secrets template (copy & fill)
└── DEPLOYMENT_READY.md       # This file
```

### ⭐ Recommended: Use `requirements_demo.txt`
For faster deployment on Streamlit Cloud, use the lightweight requirements file.

---

## 🚀 Deploy Advanced RAG Demo

### Step 1: Connect Repository
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `ChunkyTortoise/EnterpriseHub`
5. Branch: `main`

### Step 2: Configure App
| Setting | Value |
|---------|-------|
| Main file path | `advanced_rag_system/src/demo_app.py` |
| Requirements file | `advanced_rag_system/requirements_demo.txt` |
| Python version | 3.11 |

### Step 3: Add Secrets (Optional)
In Streamlit Cloud dashboard → Settings → Secrets, add:

```toml
OPENAI_API_KEY = "sk-your-openai-key"
DEMO_MODE = "true"
```

> **Note**: App works in DEMO_MODE without API keys

### Step 4: Deploy
- Click "Deploy"
- Wait 1-3 minutes for build
- Check deployment logs for errors

### Expected URL
`https://advanced-rag-demo.streamlit.app`

---

## 🚀 Deploy AgentForge Demo

### Step 1: Connect Repository
Same as above

### Step 2: Configure App
| Setting | Value |
|---------|-------|
| Main file path | `advanced_rag_system/src/agent_forge_demo.py` |
| Requirements file | `advanced_rag_system/requirements_demo.txt` |
| Python version | 3.11 |

### Step 3: Add Secrets (Optional)
In Streamlit Cloud dashboard → Settings → Secrets, add:

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-your-key"
DEMO_MODE = "true"
```

> **Note**: App works in DEMO_MODE without API keys

### Step 4: Deploy
- Click "Deploy"
- Wait 1-3 minutes for build
- Check deployment logs for errors

### Expected URL
`https://agentforge-demo.streamlit.app`

---

## 🧪 Local Testing

```bash
# Test Advanced RAG demo
cd advanced_rag_system
pip install -r requirements.txt
streamlit run src/demo_app.py

# Test AgentForge demo
cd advanced_rag_system
streamlit run src/agent_forge_demo.py
```

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check `requirements.txt` for conflicts |
| NumPy version issues | Use `numpy<2` as specified in requirements |
| App won't load | Verify all imports work |
| Missing dependencies | Ensure packages in `requirements.txt` |
| Slow loading | Reduce data size, use caching |

---

## ✅ Deployment Verified
Last updated: February 9, 2026
