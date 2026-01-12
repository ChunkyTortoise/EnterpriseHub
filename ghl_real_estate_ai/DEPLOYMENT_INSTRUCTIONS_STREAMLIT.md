# 🚀 Streamlit Deployment Guide

Complete instructions for deploying the GHL Real Estate AI Streamlit application to various platforms.

---

## 📋 Table of Contents

1. [Local Development](#local-development)
2. [Streamlit Cloud (Recommended)](#streamlit-cloud)
3. [Railway](#railway)
4. [Heroku](#heroku)
5. [Docker](#docker)
6. [AWS/GCP/Azure](#cloud-platforms)
7. [Troubleshooting](#troubleshooting)

---

## 🏠 Local Development

### Prerequisites
- Python 3.8+
- pip or conda

### Setup

```bash
# Navigate to project
cd ghl-real-estate-ai

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_demo/app.py
```

**Access:** http://localhost:8501

### Custom Port
```bash
streamlit run streamlit_demo/app.py --server.port 8501
```

### Development Mode
```bash
# Enable auto-reload on file changes
streamlit run streamlit_demo/app.py --server.runOnSave true
```

---

## ☁️ Streamlit Cloud

**Best for:** Quick deployment, free hosting, automatic updates

### Step 1: Prepare Repository

1. Ensure your code is on GitHub, GitLab, or Bitbucket
2. Verify `requirements.txt` is up-to-date:

```txt
streamlit>=1.28.0
plotly>=5.17.0
pandas>=2.0.0
anthropic>=0.7.0
chromadb>=0.4.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.4.0
python-dotenv>=1.0.0
```

3. Create `.streamlit/config.toml` in project root:

```toml
[theme]
primaryColor="#667eea"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true
```

### Step 2: Deploy

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub/GitLab/Bitbucket
3. Click "New app"
4. Configure:
   - **Repository:** your-username/ghl-real-estate-ai
   - **Branch:** main
   - **Main file path:** ghl-real-estate-ai/streamlit_demo/app.py
5. Click "Deploy!"

### Step 3: Configure Secrets

In Streamlit Cloud dashboard, add secrets:

```toml
# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "your-api-key"
GHL_API_KEY = "your-ghl-key"
DATABASE_URL = "your-database-url"
```

### Custom Domain

1. Go to app settings
2. Click "Custom domain"
3. Follow DNS configuration instructions
4. Add CNAME record pointing to your Streamlit app

---

## 🚂 Railway

**Best for:** Simple deployment with database support

### Step 1: Install Railway CLI

```bash
npm i -g @railway/cli
```

### Step 2: Create Railway Project

```bash
cd ghl-real-estate-ai
railway login
railway init
```

### Step 3: Create `railway.json`

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "streamlit run streamlit_demo/app.py --server.port $PORT --server.address 0.0.0.0",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Create `Procfile`

```
web: streamlit run streamlit_demo/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
```

### Step 5: Deploy

```bash
railway up
```

### Step 6: Set Environment Variables

```bash
railway variables set ANTHROPIC_API_KEY=your-key
railway variables set GHL_API_KEY=your-key
```

### Custom Domain

```bash
railway domain
```

---

## 🟣 Heroku

**Best for:** Enterprise-grade hosting with add-ons

### Step 1: Install Heroku CLI

```bash
# macOS
brew install heroku/brew/heroku

# Windows
# Download from heroku.com/downloads

# Linux
curl https://cli-assets.heroku.com/install.sh | sh
```

### Step 2: Create Heroku App

```bash
cd ghl-real-estate-ai
heroku login
heroku create your-app-name
```

### Step 3: Create `Procfile`

```
web: sh setup.sh && streamlit run streamlit_demo/app.py
```

### Step 4: Create `setup.sh`

```bash
mkdir -p ~/.streamlit/

echo "\
[general]\n\
email = \"your-email@domain.com\"\n\
" > ~/.streamlit/credentials.toml

echo "\
[server]\n\
headless = true\n\
enableCORS=false\n\
port = $PORT\n\
" > ~/.streamlit/config.toml
```

### Step 5: Create `runtime.txt`

```
python-3.11.6
```

### Step 6: Deploy

```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### Step 7: Configure Environment Variables

```bash
heroku config:set ANTHROPIC_API_KEY=your-key
heroku config:set GHL_API_KEY=your-key
```

### Step 8: Scale Dynos

```bash
# Free tier
heroku ps:scale web=1

# Upgrade for better performance
heroku ps:type hobby
```

---

## 🐳 Docker

**Best for:** Containerized deployment, cloud-agnostic

### Step 1: Create `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the application
ENTRYPOINT ["streamlit", "run", "streamlit_demo/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Create `.dockerignore`

```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.git
.gitignore
.streamlit/secrets.toml
*.md
.DS_Store
```

### Step 3: Build and Run

```bash
# Build image
docker build -t ghl-streamlit-app .

# Run container
docker run -p 8501:8501 \
  -e ANTHROPIC_API_KEY=your-key \
  -e GHL_API_KEY=your-key \
  ghl-streamlit-app
```

### Step 4: Docker Compose (with database)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  streamlit:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GHL_API_KEY=${GHL_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/ghl_db
    depends_on:
      - db
    volumes:
      - ./data:/app/data

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=ghl_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose up -d
```

---

## ☁️ Cloud Platforms

### AWS (Elastic Beanstalk)

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 ghl-streamlit

# Create environment
eb create ghl-streamlit-env

# Deploy
eb deploy

# Set environment variables
eb setenv ANTHROPIC_API_KEY=your-key GHL_API_KEY=your-key
```

### Google Cloud Platform (Cloud Run)

```bash
# Build and push to Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/ghl-streamlit

# Deploy to Cloud Run
gcloud run deploy ghl-streamlit \
  --image gcr.io/PROJECT_ID/ghl-streamlit \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=your-key,GHL_API_KEY=your-key
```

### Azure (App Service)

```bash
# Login
az login

# Create resource group
az group create --name ghl-rg --location eastus

# Create app service plan
az appservice plan create --name ghl-plan --resource-group ghl-rg --sku B1 --is-linux

# Create web app
az webapp create --resource-group ghl-rg --plan ghl-plan --name ghl-streamlit --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set --resource-group ghl-rg --name ghl-streamlit --startup-file "streamlit run streamlit_demo/app.py --server.port 8000 --server.address 0.0.0.0"

# Deploy
az webapp up --name ghl-streamlit --resource-group ghl-rg
```

---

## 🔧 Troubleshooting

### Port Issues

**Problem:** Port already in use  
**Solution:**
```bash
streamlit run streamlit_demo/app.py --server.port 8501
```

### Memory Issues

**Problem:** App crashes due to memory  
**Solution:** Add to `.streamlit/config.toml`:
```toml
[server]
maxUploadSize = 200
maxMessageSize = 200

[runner]
fastReruns = true
```

### Slow Loading

**Problem:** Charts/data load slowly  
**Solution:** Implement caching:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    # Your data loading code
    pass
```

### Import Errors

**Problem:** Module not found  
**Solution:**
```bash
pip install -r requirements.txt --upgrade
```

### Authentication Issues

**Problem:** API keys not working  
**Solution:** Check environment variables:
```bash
# Local
echo $ANTHROPIC_API_KEY

# Heroku
heroku config:get ANTHROPIC_API_KEY

# Railway
railway variables
```

### Database Connection

**Problem:** Can't connect to database  
**Solution:** Check connection string format:
```python
# PostgreSQL
DATABASE_URL = "postgresql://user:password@host:port/database"

# Make sure to handle SSL
DATABASE_URL = "postgresql://user:password@host:port/database?sslmode=require"
```

### CORS Errors

**Problem:** Cross-origin issues  
**Solution:** Update `.streamlit/config.toml`:
```toml
[server]
enableCORS = false
enableXsrfProtection = true
```

---

## 📊 Performance Optimization

### 1. Enable Caching

```python
# Cache data
@st.cache_data(ttl=3600)
def load_data():
    return expensive_operation()

# Cache resources (DB connections, ML models)
@st.cache_resource
def get_database_connection():
    return create_connection()
```

### 2. Optimize Charts

```python
# Limit data points
df_sample = df.sample(n=1000)  # Instead of full dataset

# Use efficient chart types
fig = px.scatter(df_sample)  # Faster than complex charts
```

### 3. Use Session State Wisely

```python
# Initialize once
if 'data' not in st.session_state:
    st.session_state.data = load_data()
```

### 4. Lazy Loading

```python
# Load only when needed
with st.expander("View Details"):
    detailed_data = load_detailed_data()  # Only loads when expanded
```

---

## 🔐 Security Best Practices

### 1. Environment Variables

Never commit secrets to Git:
```bash
# Add to .gitignore
.env
.streamlit/secrets.toml
```

### 2. API Key Management

```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANTHROPIC_API_KEY")
```

### 3. Input Validation

```python
def validate_input(user_input):
    if not user_input or len(user_input) > 1000:
        raise ValueError("Invalid input")
    return sanitize(user_input)
```

### 4. Rate Limiting

```python
from functools import lru_cache
from time import time

@lru_cache(maxsize=100)
def rate_limited_function(user_id, timestamp):
    # Your code here
    pass

# Call with current time bucket (e.g., every 60 seconds)
rate_limited_function(user_id, int(time() / 60))
```

---

## 📱 Mobile Optimization

Add to `.streamlit/config.toml`:

```toml
[theme]
base = "light"
primaryColor = "#667eea"

[server]
enableStaticServing = true

[client]
showErrorDetails = false
```

Add responsive CSS in your pages:

```python
st.markdown("""
<style>
@media (max-width: 768px) {
    .stMetric { font-size: 0.9em; }
    .stPlotlyChart { height: 300px !important; }
}
</style>
""", unsafe_allow_html=True)
```

---

## 🎯 Deployment Checklist

Before deploying to production:

- [ ] Update `requirements.txt`
- [ ] Set all environment variables
- [ ] Configure `.streamlit/config.toml`
- [ ] Test all pages locally
- [ ] Remove debug/print statements
- [ ] Enable caching where appropriate
- [ ] Set up error monitoring
- [ ] Configure custom domain (if needed)
- [ ] Set up SSL certificate
- [ ] Test on mobile devices
- [ ] Set up backups (if using database)
- [ ] Document deployment process
- [ ] Create rollback plan

---

## 📞 Support Resources

- **Streamlit Docs:** https://docs.streamlit.io
- **Streamlit Forum:** https://discuss.streamlit.io
- **Railway Docs:** https://docs.railway.app
- **Heroku Docs:** https://devcenter.heroku.com
- **Docker Docs:** https://docs.docker.com

---

## 🚀 Quick Deploy Commands

### Streamlit Cloud
```bash
# Push to GitHub, then deploy via web interface
git push origin main
```

### Railway
```bash
railway up
```

### Heroku
```bash
git push heroku main
```

### Docker
```bash
docker build -t ghl-app . && docker run -p 8501:8501 ghl-app
```

---

**Deployment Status:** Ready for production ✅  
**Last Updated:** January 4, 2026
