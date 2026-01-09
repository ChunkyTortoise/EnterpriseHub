# 🤖 Backend Stabilization Prompt for Claude

**Role:** Senior Backend Engineer / DevOps Specialist  
**Mission:** Transform the GHL Real Estate AI demo from mock-mode to production-ready  
**Priority:** P0 - Critical for Jorge's client delivery

---

## 📋 Context

The frontend demo is **visually perfect** and ready for screenshots, but the backend is **fundamentally broken**:

1. **All data is mocked** - No real GHL API integration
2. **Dependency hell** - `chromadb` conflicts with `onnxruntime`, causing import failures
3. **No environment isolation** - "Works on my machine" syndrome
4. **RAG engine non-functional** - Vector DB crashes on startup

### Current State (As of Jan 8, 2026):
```
✅ Streamlit app runs in demo mode
✅ Mock data displays correctly
✅ All 5 hubs render properly
❌ Cannot connect to real GHL API
❌ chromadb import fails in production
❌ No Docker containerization
❌ Dependency versions conflict
```

---

## 🎯 Your Mission: 3 Critical Fixes

### **Task 1: Resolve Dependency Conflicts (P0)**

#### Problem:
`ghl_real_estate_ai/requirements.txt` line 14:
```
chromadb>=0.4.22,<0.6.0
```

This causes:
- Import errors with `onnxruntime`
- Conflicts with `sentence-transformers>=2.3.0`
- Python 3.14 incompatibility (user's local environment)

#### Your Task:
1. **Pin exact working versions** for:
   - chromadb
   - sentence-transformers
   - onnxruntime (or onnxruntime-silicon for M1/M2 Macs)
   
2. **Create `requirements-lock.txt`** with tested, frozen versions

3. **Add conditional dependencies** for different platforms:
   ```python
   # requirements.txt
   chromadb==0.4.24
   onnxruntime==1.16.3; sys_platform != 'darwin'
   onnxruntime-silicon==1.16.3; sys_platform == 'darwin' and platform_machine == 'arm64'
   ```

4. **Test the fix**:
   ```bash
   cd ghl_real_estate_ai
   python -m venv test_env
   source test_env/bin/activate
   pip install -r requirements.txt
   python -c "import chromadb; print('✅ chromadb works')"
   ```

**Deliverable:** Updated `requirements.txt` that installs cleanly on Python 3.10, 3.11, and 3.14.

---

### **Task 2: Dockerize the Application (P0)**

#### Problem:
The app runs inconsistently across environments. Jorge needs a **one-click deployment** for Railway/Render.

#### Your Task:
Create a production-ready Docker setup:

**File 1: `ghl_real_estate_ai/Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for chromadb
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run streamlit
CMD ["streamlit", "run", "streamlit_demo/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**File 2: `ghl_real_estate_ai/docker-compose.yml`**
```yaml
version: '3.8'

services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - GHL_API_KEY=${GHL_API_KEY:-demo_mode}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
      - ENVIRONMENT=${ENVIRONMENT:-demo}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

**File 3: `.dockerignore`**
```
__pycache__
*.pyc
.venv
.env
*.log
.chroma_db
.coverage*
```

**Test the Docker build:**
```bash
cd ghl_real_estate_ai
docker build -t ghl-ai-demo .
docker run -p 8501:8501 ghl-ai-demo
# Verify: http://localhost:8501 loads without errors
```

**Deliverable:** Working Dockerfile that Jorge can `docker build && docker run` with zero configuration.

---

### **Task 3: Implement Real GHL API Mode (P1)**

#### Problem:
Lines 62-67 in `app.py` use `load_mock_data()` exclusively. There's no way to switch to real GHL API.

#### Your Task:

**Step 3.1: Create Environment Detection**

Add to `ghl_real_estate_ai/ghl_utils/config.py`:
```python
import os
from enum import Enum

class EnvironmentMode(Enum):
    DEMO = "demo"      # Mock data, no API calls
    STAGING = "staging" # Real API, test account
    PRODUCTION = "production" # Real API, Jorge's account

def get_environment() -> EnvironmentMode:
    """Detect environment based on GHL_API_KEY presence"""
    api_key = os.getenv("GHL_API_KEY", "")
    
    if not api_key or api_key == "demo_mode":
        return EnvironmentMode.DEMO
    elif api_key.startswith("test_"):
        return EnvironmentMode.STAGING
    else:
        return EnvironmentMode.PRODUCTION

def is_mock_mode() -> bool:
    """Returns True if we should use mock data"""
    return get_environment() == EnvironmentMode.DEMO
```

**Step 3.2: Update `app.py` to Auto-Switch**

Replace line 120 in `app.py`:
```python
# OLD:
mock_data = load_mock_data()

# NEW:
from ghl_utils.config import is_mock_mode

if is_mock_mode():
    mock_data = load_mock_data()
    st.info("🎭 **Demo Mode** - Using sample data. Set GHL_API_KEY to enable live sync.")
else:
    # Load real data from GHL API
    from services.ghl_client import GHLClient
    ghl_client = GHLClient()
    mock_data = ghl_client.fetch_dashboard_data()
    st.success("✅ **Live Mode** - Connected to GoHighLevel")
```

**Step 3.3: Implement Real GHL Client**

Ensure `ghl_real_estate_ai/services/ghl_client.py` has:
```python
def fetch_dashboard_data(self) -> dict:
    """Fetch real data from GHL API"""
    try:
        # Get conversations
        conversations = self.get_conversations(limit=50)
        
        # Get opportunities
        opportunities = self.get_opportunities()
        
        # Calculate metrics
        return {
            "conversations": conversations,
            "opportunities": opportunities,
            "system_health": self._calculate_health_metrics()
        }
    except Exception as e:
        logger.error(f"GHL API fetch failed: {e}")
        # Fallback to mock data
        return load_mock_data()
```

**Deliverable:** App that automatically detects environment and switches between mock/live data.

---

## 🧪 Acceptance Criteria

Before marking this complete, verify:

### ✅ Dependency Fix
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] `import chromadb` works in Python 3.10, 3.11, 3.14
- [ ] No version conflicts shown by `pip check`

### ✅ Docker Setup
- [ ] `docker build` completes successfully
- [ ] `docker run` starts app on port 8501
- [ ] Health check endpoint returns 200 OK
- [ ] App works without any local dependencies

### ✅ Environment Detection
- [ ] App shows "Demo Mode" banner when `GHL_API_KEY` is unset
- [ ] App shows "Live Mode" banner when API key is present
- [ ] No crashes when switching between modes
- [ ] Mock data still works for screenshots

---

## 📦 Deliverables Checklist

When you're done, you should have created/modified:

1. ✅ `ghl_real_estate_ai/requirements.txt` - Fixed dependencies
2. ✅ `ghl_real_estate_ai/requirements-lock.txt` - Frozen versions
3. ✅ `ghl_real_estate_ai/Dockerfile` - Production container
4. ✅ `ghl_real_estate_ai/docker-compose.yml` - Easy local testing
5. ✅ `ghl_real_estate_ai/.dockerignore` - Optimized build
6. ✅ `ghl_real_estate_ai/ghl_utils/config.py` - Environment detection
7. ✅ `ghl_real_estate_ai/streamlit_demo/app.py` - Auto-switch logic
8. ✅ `ghl_real_estate_ai/services/ghl_client.py` - Real API implementation

---

## 🎯 Success Metrics

Jorge should be able to:
1. Clone the repo on a fresh machine
2. Run `docker-compose up`
3. See the demo at `localhost:8501`
4. Set `GHL_API_KEY` and get live data
5. Deploy to Railway with zero config changes

---

## 🚨 Critical Notes

- **DO NOT break the mock mode** - Screenshots still need to work
- **Maintain backward compatibility** - Frontend code shouldn't need changes
- **Test on both M1 Mac and Linux** - Docker must work everywhere
- **Document in README.md** - Add "Quick Start" with Docker instructions

---

## 📚 Reference Files

Key files to examine:
- `ghl_real_estate_ai/requirements.txt` - Current broken deps
- `ghl_real_estate_ai/streamlit_demo/app.py` - Lines 62-120 (mock data loading)
- `ghl_real_estate_ai/services/ghl_client.py` - Existing GHL API wrapper
- `ghl_real_estate_ai/ghl_utils/config.py` - Config management

---

## 💬 Questions to Resolve

Before starting, consider:
1. Should we use `chromadb` or switch to a simpler vector store (Pinecone, Weaviate)?
2. What's the minimum Python version we need to support?
3. Does Railway support Docker deployments or should we target Render?

---

**Ready to fix the backend?** 🛠️ Start with Task 1 (dependencies) and work your way through. The frontend team (me) is standing by for integration testing!

---

**Prompt Generated:** 2026-01-08 18:35 PST  
**For:** Claude (Backend Specialist)  
**Priority:** P0 - Critical Path
