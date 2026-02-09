# Streamlit Cloud Deployment Guide

**EnterpriseHub / ChunkyTortoise Projects - Reddit Marketing Campaign**

---

## Overview

This guide covers deploying three Streamlit Cloud applications for the Reddit marketing campaign live demos:

1. **EnterpriseHub** - Real Estate AI Platform BI Dashboard
2. **Advanced RAG System** - Enterprise-Grade RAG Demo
3. **AgentForge** - Multi-Agent Orchestration Demo

---

## 1. Repository Preparation Checklist

### 1.1 Requirements Files

Each deployment requires a `requirements.txt` file in the project root. Streamlit Cloud automatically detects and installs dependencies from this file.

#### EnterpriseHub (`ghl_real_estate_ai/streamlit_demo/requirements.txt`)

```txt
streamlit==1.50.0
streamlit-chat==0.1.1
plotly==6.5.0
anthropic==0.40.0
chromadb==0.5.23
sentence-transformers==3.3.1
python-dotenv==1.0.1
scikit-learn>=1.3.2
pandas>=2.1.3
numpy>=1.26.2
redis>=5.0.0
pydantic>=2.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
websockets>=12.0
websocket-client>=1.6.0
asyncio>=3.4.3
aioredis>=2.0.0
networkx>=3.1
```

#### Advanced RAG System (`advanced_rag_system/requirements.txt`)

```txt
# Core Framework
pydantic>=2.5.0
pydantic-settings>=2.1.0

# OpenAI SDK
openai>=1.6.0

# Vector Store
chromadb>=0.4.18
numpy<2  # Required for ChromaDB compatibility

# Caching
redis>=5.0.0

# Async Support
aiohttp>=3.9.0

# Type Hints & Validation
typing-extensions>=4.9.0

# Logging & Observability
structlog>=23.2.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Sparse Retrieval
rank-bm25>=0.2.2
scikit-learn>=1.3.0

# Re-ranking
sentence-transformers>=2.2.2
cohere>=4.0.0
```

### 1.2 Streamlit Configuration (`.streamlit/config.toml`)

Create `.streamlit/config.toml` in each project root:

```toml
[server]
headless = true
port = 8501
address = "0.0.0.0"

[client]
toolbarMode = "viewer"

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[runner]
fastReruns = true
```

### 1.3 App Entry Point Files

#### EnterpriseHub Main File
- **Path**: `ghl_real_estate_ai/streamlit_demo/dashboard_app.py`
- **Run Command**: `streamlit run ghl_real_estate_ai/streamlit_demo/dashboard_app.py`

#### Advanced RAG System Main File
- **Path**: `advanced_rag_system/src/demo_app.py` (to be created)
- **Run Command**: `streamlit run advanced_rag_system/src/demo_app.py`

#### AgentForge Main File
- **Path**: `advanced_rag_system/src/agent_forge_demo.py` (to be created)
- **Run Command**: `streamlit run advanced_rag_system/src/agent_forge_demo.py`

### 1.4 Secrets Configuration (`.streamlit/secrets.toml`)

Streamlit Cloud supports secrets via the dashboard. For local development, create `.streamlit/secrets.toml`:

```toml
# EnterpriseHub Secrets
ANTHROPIC_API_KEY = "your-anthropic-api-key"
GHL_API_KEY = "your-ghl-api-key"
GHL_LOCATION_ID = "your-location-id"
DEMO_MODE = "true"

# Advanced RAG Secrets
OPENAI_API_KEY = "your-openai-api-key"
CHROMA_PERSIST_DIR = "/tmp/chroma"

# AgentForge Secrets
ANTHROPIC_API_KEY = "your-anthropic-api-key"
OPENAI_API_KEY = "your-openai-api-key"
```

---

## 2. Streamlit Cloud Deployment Steps

### 2.1 Connect GitHub Repository

1. **Access Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub

2. **New App**
   - Click "New app"
   - Select your GitHub repository
   - Choose the branch (usually `main`)

3. **Repository Selection**
   - For EnterpriseHub: Select `EnterpriseHub` repo, branch `main`
   - Path: `ghl_real_estate_ai/streamlit_demo/`

### 2.2 Configure Build and Run Commands

#### EnterpriseHub Configuration

| Setting | Value |
|---------|-------|
| **Main file path** | `ghl_real_estate_ai/streamlit_demo/dashboard_app.py` |
| **Requirements file** | `ghl_real_estate_ai/streamlit_demo/requirements.txt` |
| **Python version** | 3.11 |
| **Build command** | `pip install -r ghl_real_estate_ai/streamlit_demo/requirements.txt` |
| **Run command** | `streamlit run ghl_real_estate_ai/streamlit_demo/dashboard_app.py --server.port $PORT --server.address 0.0.0.0` |

#### Advanced RAG System Configuration

| Setting | Value |
|---------|-------|
| **Main file path** | `advanced_rag_system/src/demo_app.py` |
| **Requirements file** | `advanced_rag_system/requirements.txt` |
| **Python version** | 3.11 |
| **Build command** | `pip install -r advanced_rag_system/requirements.txt` |
| **Run command** | `streamlit run advanced_rag_system/src/demo_app.py --server.port $PORT --server.address 0.0.0.0` |

#### AgentForge Configuration

| Setting | Value |
|---------|-------|
| **Main file path** | `advanced_rag_system/src/agent_forge_demo.py` |
| **Requirements file** | `advanced_rag_system/requirements.txt` |
| **Python version** | 3.11 |
| **Build command** | `pip install -r advanced_rag_system/requirements.txt` |
| **Run command** | `streamlit run advanced_rag_system/src/agent_forge_demo.py --server.port $PORT --server.address 0.0.0.0` |

### 2.3 Add Secrets/Environment Variables

In Streamlit Cloud dashboard, go to **Settings → Secrets** and add:

```toml
# EnterpriseHub
ANTHROPIC_API_KEY = "sk-ant-api03-..."
GHL_API_KEY = "ghl_api_key_here"
GHL_LOCATION_ID = "location_id"
DEMO_MODE = "true"

# Advanced RAG
OPENAI_API_KEY = "sk-..."
CHROMA_PERSIST_DIR = "/tmp/chroma"
DEMO_MODE = "true"
```

### 2.4 Deploy Workflow

```
1. Push code to GitHub
   ↓
2. Streamlit Cloud detects changes
   ↓
3. Build starts (pip install dependencies)
   ↓
4. App deploys (1-3 minutes)
   ↓
5. Check deployment logs for errors
   ↓
6. Verify app loads correctly
```

---

## 3. Per-Repo Deployment Instructions

### 3.1 EnterpriseHub - Real Estate AI Platform BI Dashboard

**Repository URL**: `https://github.com/ChunkyTortoise/EnterpriseHub`

**Main File Path**: `ghl_real_estate_ai/streamlit_demo/dashboard_app.py`

**Requirements File**: `ghl_real_estate_ai/streamlit_demo/requirements.txt`

**Required Secrets**:
| Secret | Description | Required |
|--------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |
| `GHL_API_KEY` | GoHighLevel API key | Optional |
| `GHL_LOCATION_ID` | GHL Location ID | Optional |
| `DEMO_MODE` | Set to "true" for demo without API keys | No |

**Optional Custom Domain**:
- Configure in **Settings → Custom domain**
- Example: `enterprisehub-demo.streamlit.app`

**Deployment Notes**:
- App includes DEMO_MODE that works without external dependencies
- All features gracefully degrade when API keys are missing
- Recommended to deploy with DEMO_MODE="true" for initial demo

### 3.2 Advanced RAG System Demo

**Repository URL**: `https://github.com/ChunkyTortoise/EnterpriseHub`

**Main File Path**: `advanced_rag_system/src/demo_app.py` (create if not exists)

**Requirements File**: `advanced_rag_system/requirements.txt`

**Required Secrets**:
| Secret | Description | Required |
|--------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for embeddings/LLM | Yes |
| `ANTHROPIC_API_KEY` | Anthropic API key (alternative) | Optional |
| `DEMO_MODE` | Set to "true" for offline demo | No |

**Custom Domain**:
- Example: `advanced-rag-demo.streamlit.app`

**Pre-Deployment Steps**:
1. Create `demo_app.py` with RAG demo interface
2. Include sample document store for demo mode
3. Add interactive query interface

### 3.3 AgentForge Multi-Agent Orchestration Demo

**Repository URL**: `https://github.com/ChunkyTortoise/EnterpriseHub`

**Main File Path**: `advanced_rag_system/src/agent_forge_demo.py` (create if not exists)

**Requirements File**: `advanced_rag_system/requirements.txt`

**Required Secrets**:
| Secret | Description | Required |
|--------|-------------|----------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `DEMO_MODE` | Set to "true" for simulated agents | No |

**Custom Domain**:
- Example: `agentforge-demo.streamlit.app`

**Pre-Deployment Steps**:
1. Create `agent_forge_demo.py` showcasing multi-agent workflows
2. Include pre-defined agent personas (Researcher, Writer, Analyst)
3. Add task delegation visualization
4. Show agent communication patterns

---

## 4. Post-Deployment Verification

### 4.1 Health Check Endpoints

Streamlit Cloud apps don't have traditional health endpoints, but verify:

```python
# In app.py, add health check indicator
if st.button("Health Check"):
    st.success("✅ App is running")
    st.write(f"Session state: {st.session_state.get('initialized', False)}")
```

### 4.2 Demo URLs to Collect

| App | Expected URL |
|-----|--------------|
| EnterpriseHub | `https://enterprisehub-demo.streamlit.app` |
| Advanced RAG | `https://advanced-rag-demo.streamlit.app` |
| AgentForge | `https://agentforge-demo.streamlit.app` |

### 4.3 Update Reddit Post with Live Links

After deployment, update your Reddit marketing posts with live links:

```markdown
## Live Demos Now Available!

🚀 **EnterpriseHub - Real Estate AI Platform**
→ [View Demo](https://enterprisehub-demo.streamlit.app)
Real-time BI dashboards, lead qualification, Jorge bot orchestration

📚 **Advanced RAG System**
→ [View Demo](https://advanced-rag-demo.streamlit.app)
Hybrid retrieval, re-ranking, enterprise knowledge management

🤖 **AgentForge - Multi-Agent Orchestration**
→ [View Demo](https://agentforge-demo.streamlit.app)
Collaborative AI agents for complex workflows

*Deployed on Streamlit Cloud - Feb 2026*
```

### 4.4 Troubleshooting Checklist

| Issue | Solution |
|-------|----------|
| Build fails | Check requirements.txt for package conflicts |
| App won't load | Verify all imports work in isolation |
| Missing dependencies | Ensure packages are in requirements.txt |
| Environment variables | Add secrets in Streamlit Cloud dashboard |
| Slow loading | Reduce data size, use caching decorators |
| API errors | Check API keys in secrets, use DEMO_MODE |

### 4.5 Performance Optimization

Add caching to improve demo performance:

```python
@st.cache_data(ttl=3600)
def load_demo_data():
    # Expensive data loading
    return data

@st.cache_resource
def initialize_components():
    # Expensive component initialization
    return component
```

---

## Quick Reference Commands

```bash
# Local testing
cd ghl_real_estate_ai/streamlit_demo
pip install -r requirements.txt
streamlit run dashboard_app.py

# Deploy Advanced RAG demo
cd advanced_rag_system
pip install -r requirements.txt
streamlit run src/demo_app.py

# Deploy AgentForge demo
cd advanced_rag_system
streamlit run src/agent_forge_demo.py
```

---

## Support

- **Streamlit Cloud Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Troubleshooting Guide**: [Streamlit Forum](https://discuss.streamlit.io)
- **Issue Tracking**: Check deployment logs in Streamlit Cloud dashboard

---

**Version**: 1.0 | **Last Updated**: February 9, 2026 | **Author**: EnterpriseHub Team
