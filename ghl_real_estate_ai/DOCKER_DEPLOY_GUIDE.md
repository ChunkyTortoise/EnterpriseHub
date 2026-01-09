# 🐳 Docker Deployment Guide

**GHL Real Estate AI - Production Deployment**

This guide covers Docker deployment for the GHL Real Estate AI application with automatic environment detection.

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose v2.0+ (included with Docker Desktop)

### 1. Clone & Setup

```bash
cd ghl_real_estate_ai
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file:

```bash
# Demo Mode (default - uses mock data)
ENVIRONMENT=demo
GHL_API_KEY=demo_mode

# OR Live Mode (connect to real GHL)
# ENVIRONMENT=production
# GHL_API_KEY=your_actual_ghl_api_key_here
# ANTHROPIC_API_KEY=your_claude_api_key_here
```

### 3. Launch

```bash
docker-compose up --build
```

### 4. Access

Open browser to: **http://localhost:8501**

---

## 📋 Environment Modes

The app automatically detects which mode to run in:

| Mode | Trigger | Description | API Calls |
|------|---------|-------------|-----------|
| **Demo** | `ENVIRONMENT=demo` or `GHL_API_KEY=demo_mode` | Uses mock data, perfect for screenshots | None ❌ |
| **Staging** | `ENVIRONMENT=staging` or `GHL_API_KEY=test_*` | Connects to test GHL account | Test API ✅ |
| **Production** | `ENVIRONMENT=production` + valid API key | Live production data | Production API ✅ |

### Visual Indicators

The app shows a banner at the top:

- 🎭 **Demo Mode** (Orange) - "Using sample data"
- 🧪 **Staging Mode** (Blue) - "Connected to test environment"
- ✅ **Live Mode** (Green) - "Connected to GoHighLevel production"

---

## 🛠️ Docker Commands

### Build & Run
```bash
# Build and start in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop containers
docker-compose down

# Restart
docker-compose restart
```

### Development Mode

Mount local code for live editing:

```yaml
# Uncomment in docker-compose.yml:
volumes:
  - ./streamlit_demo:/app/streamlit_demo
```

Then:
```bash
docker-compose up
# Changes to app.py will trigger Streamlit auto-reload
```

---

## 🔧 Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs ghl-ai-demo
```

**Common issues:**
- Port 8501 already in use → Change in `docker-compose.yml`
- Missing .env file → Copy from `.env.example`

### Health Check Failing

```bash
# Check container health
docker ps

# Manual health check
docker exec ghl-real-estate-ai curl http://localhost:8501/_stcore/health
```

### Dependency Errors

**Problem:** `ModuleNotFoundError: No module named 'chromadb'`

**Solution:**
```bash
# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### Permission Issues (Linux)

```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/ .chroma_db/
```

---

## 🌐 Production Deployment

### Railway

1. **Create new project** on [Railway.app](https://railway.app)

2. **Connect GitHub repo**

3. **Set environment variables:**
   ```
   ENVIRONMENT=production
   GHL_API_KEY=your_actual_key
   ANTHROPIC_API_KEY=your_claude_key
   ```

4. **Deploy:**
   Railway will auto-detect Dockerfile and build

5. **Access:** Railway provides public URL

### Render.com

1. **Create new Web Service**

2. **Connect repo** and select `ghl_real_estate_ai` directory

3. **Configure:**
   - Build Command: `docker build -t ghl-ai .`
   - Start Command: `docker run -p $PORT:8501 ghl-ai`

4. **Set environment variables** in Render dashboard

### DigitalOcean App Platform

```bash
# Push to Docker Hub first
docker build -t yourusername/ghl-ai:latest .
docker push yourusername/ghl-ai:latest
```

Then create App from Docker Hub image.

---

## 📊 Monitoring

### Health Check Endpoint

```bash
curl http://localhost:8501/_stcore/health
```

**Response:** `{"status": "ok"}`

### Container Stats

```bash
# Real-time resource usage
docker stats ghl-real-estate-ai

# Inspect container
docker inspect ghl-real-estate-ai
```

---

## 🔐 Security Best Practices

### Never Commit Secrets

✅ **Good:**
```bash
# .env (gitignored)
GHL_API_KEY=actual_secret_key
```

❌ **Bad:**
```python
# config.py (committed to git)
GHL_API_KEY = "actual_secret_key"  # NEVER DO THIS
```

### Production Checklist

- [ ] Environment variables set in hosting platform (not hardcoded)
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled on production domain
- [ ] Health checks configured
- [ ] Logs monitoring set up
- [ ] Backup strategy for data volumes

---

## 📦 What's Included

### Docker Image Contents

- **Python 3.11** (slim base)
- **All dependencies** from `requirements.txt`
- **Streamlit app** with 5 hubs
- **ChromaDB** for vector storage
- **Health check** endpoint

### Persistent Data

These directories are mounted as volumes:

```
./data/              → /app/data/
./.chroma_db/        → /app/.chroma_db/
```

**What persists:**
- Property listings
- Analytics data
- Vector embeddings
- User preferences

---

## 🧪 Testing Docker Build

### Test Script

```bash
#!/bin/bash
# test_docker.sh

echo "🧪 Testing Docker build..."

# Build
docker-compose build

# Start
docker-compose up -d

# Wait for health check
sleep 10

# Test health endpoint
if curl -f http://localhost:8501/_stcore/health; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker-compose logs
    exit 1
fi

# Test app loads
if curl -f http://localhost:8501; then
    echo "✅ App is accessible!"
else
    echo "❌ App not accessible!"
    exit 1
fi

# Cleanup
docker-compose down

echo "✅ All tests passed!"
```

Run with: `bash test_docker.sh`

---

## 📝 FAQ

### Q: Do I need to rebuild after code changes?

**A:** Yes, for production. For development, use volume mounting.

```bash
# Production: Rebuild
docker-compose up --build

# Development: Live reload with volumes
# (Uncomment volume in docker-compose.yml)
```

### Q: Can I run multiple environments?

**A:** Yes, use different compose files:

```bash
# docker-compose.dev.yml
services:
  ghl-ai-demo:
    environment:
      - ENVIRONMENT=staging
    ports:
      - "8502:8501"  # Different port

# docker-compose.prod.yml
services:
  ghl-ai-demo:
    environment:
      - ENVIRONMENT=production
    ports:
      - "8501:8501"
```

Run with:
```bash
docker-compose -f docker-compose.dev.yml up
docker-compose -f docker-compose.prod.yml up
```

### Q: How do I update dependencies?

**A:** 

1. Edit `requirements.txt`
2. Rebuild: `docker-compose build --no-cache`
3. Restart: `docker-compose up`

### Q: What if chromadb fails?

**A:** The app will fallback to mock mode. Check:

```bash
docker exec ghl-real-estate-ai python -c "import chromadb; print('✅ OK')"
```

---

## 🎯 Next Steps

After successful Docker deployment:

1. ✅ Test in Demo Mode
2. ✅ Configure GHL API keys for Live Mode
3. ✅ Deploy to Railway/Render
4. ✅ Set up monitoring
5. ✅ Configure custom domain

---

## 📞 Support

**Issues?**
- Check logs: `docker-compose logs -f`
- Health check: `curl http://localhost:8501/_stcore/health`
- Rebuild: `docker-compose up --build`

**Still stuck?**
- Check `SCREENSHOT_ANALYSIS_REPORT.md` for known issues
- See `FRONTEND_IMPROVEMENTS_COMPLETE.md` for visual fixes

---

**Last Updated:** January 8, 2026  
**Docker Version:** 24.0+  
**Compose Version:** 2.0+  
**Status:** ✅ Production Ready
