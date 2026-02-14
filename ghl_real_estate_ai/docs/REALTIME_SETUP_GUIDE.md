# Real-time Features Setup Guide

## WebSocket and Redis Configuration for GHL Real Estate AI

This guide covers the complete setup of WebSocket and Redis infrastructure for real-time features including live dashboards, instant notifications, and real-time data synchronization.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Streamlit     │◄──►│  WebSocket   │◄──►│  Redis Cache    │
│   Dashboard     │    │   Server     │    │   & Sessions   │
└─────────────────┘    └──────────────┘    └─────────────────┘
         │                       │                    │
         ▼                       ▼                    ▼
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Real-time     │    │  Event       │    │  Lead Scoring   │
│   Data Service  │    │  Processing  │    │  & Analytics    │
└─────────────────┘    └──────────────┘    └─────────────────┘
```

### Key Components

- **WebSocket Server**: Real-time bidirectional communication
- **Redis**: Caching, session storage, and message queuing
- **Real-time Data Service**: Event processing and distribution
- **Streamlit Integration**: Dashboard updates and notifications

---

## 📋 Prerequisites

### Required Dependencies

The system uses the following packages for real-time functionality:

```bash
# Core real-time dependencies
redis>=5.0.0              # Redis client
websockets>=12.0           # WebSocket client/server
websocket-client>=1.6.0    # Alternative WebSocket client
aioredis>=2.0.1           # Async Redis client

# Supporting libraries
asyncio>=3.4.3            # Async programming support
pydantic>=2.0.0           # Configuration validation
```

### System Requirements

- **Redis Server**: Version 6.0+ (local or cloud)
- **Python**: 3.10+ with asyncio support
- **Network**: Port 6379 (Redis), Port 8765 (WebSocket)

---

## 🔧 Environment Configuration

### 1. Copy Environment Template

```bash
# Copy the environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

### 2. Core Configuration Variables

#### Redis Configuration
```bash
# Redis Connection (Required for real-time features)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password-if-required
REDIS_DB=0

# Redis Connection Pool Settings
REDIS_MAX_CONNECTIONS=20
REDIS_SOCKET_TIMEOUT=30
REDIS_SOCKET_CONNECT_TIMEOUT=30
REDIS_RETRY_ON_TIMEOUT=true
REDIS_HEALTH_CHECK_INTERVAL=30
```

#### WebSocket Configuration
```bash
# WebSocket Server Settings
WEBSOCKET_HOST=localhost
WEBSOCKET_PORT=8765
WEBSOCKET_PATH=/ws
WEBSOCKET_PROTOCOL=ws

# Production WebSocket Settings (use wss:// for HTTPS)
WEBSOCKET_SECURE=false
WEBSOCKET_ORIGINS=localhost:8501,127.0.0.1:8501

# Connection Settings
WEBSOCKET_PING_INTERVAL=20
WEBSOCKET_PING_TIMEOUT=10
WEBSOCKET_CLOSE_TIMEOUT=10
WEBSOCKET_MAX_SIZE=1048576
WEBSOCKET_MAX_QUEUE=32

# Reconnection Settings
WEBSOCKET_RECONNECT_ATTEMPTS=5
WEBSOCKET_RECONNECT_DELAY=2
WEBSOCKET_FALLBACK_TO_POLLING=true
```

#### Real-time Service Configuration
```bash
# Real-time Data Service Settings
REALTIME_ENABLED=true
REALTIME_USE_WEBSOCKET=true
REALTIME_POLL_INTERVAL=2
REALTIME_MAX_EVENTS=1000
REALTIME_CACHE_TTL=3600

# Event Processing Settings
REALTIME_EVENT_DEDUP_WINDOW=30
REALTIME_HIGH_PRIORITY_THRESHOLD=3
REALTIME_BATCH_SIZE=50
```

---

## 🚀 Development Setup

### 1. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Or install specific real-time packages
pip install redis>=5.0.0 websockets>=12.0 aioredis>=2.0.1
```

### 2. Start Redis Server

#### Option A: Local Redis Installation
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# Windows (using WSL)
sudo apt-get install redis-server
redis-server
```

#### Option B: Docker Redis
```bash
# Start Redis in Docker
docker run --name redis-realtime -p 6379:6379 -d redis:7-alpine

# With persistent storage
docker run --name redis-realtime -p 6379:6379 -v redis-data:/data -d redis:7-alpine
```

#### Option C: Railway Redis (Production)
```bash
# Railway automatically provides REDIS_URL
# No additional setup required
railway add --database redis
```

### 3. Validate Configuration

```bash
# Test real-time configuration
python -m ghl_real_estate_ai.services.realtime_config

# Expected output:
# === Real-time Configuration Test ===
# Redis Available: True
# WebSocket Available: True
# Configuration Valid: True
# Connection Test Results:
# Redis: Redis connection successful
# WebSocket: WebSocket connected but no response (server may not echo)
# Overall Ready: True
```

### 4. Start Development Services

```bash
# Terminal 1: Start Streamlit app
streamlit run streamlit_demo/app.py

# Terminal 2: Start WebSocket server (if needed)
python -m ghl_real_estate_ai.services.websocket_server

# Terminal 3: Monitor Redis (optional)
redis-cli monitor
```

---

## 🏭 Production Deployment

### Railway Platform Setup

#### 1. Add Redis Database
```bash
# Add Redis to your Railway project
railway add --database redis

# Railway automatically sets REDIS_URL environment variable
```

#### 2. Configure Environment Variables
```bash
# Set production environment variables in Railway dashboard
ENVIRONMENT=production
REALTIME_ENABLED=true
WEBSOCKET_SECURE=true
WEBSOCKET_ORIGINS=your-ontario_mills.com

# Redis settings (auto-provided by Railway)
REDIS_URL=redis://default:password@host:port
```

#### 3. Enable WebSocket Support
```bash
# Update railway.toml for WebSocket support
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
restartPolicyType = "on_failure"

[experimental]
configFilePath = "railway.toml"
```

### Docker Deployment

#### 1. Multi-container Setup
```dockerfile
# docker-compose.yml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - REDIS_URL=redis://redis:6379
      - WEBSOCKET_HOST=0.0.0.0
      - REALTIME_ENABLED=true
    depends_on:
      - redis

volumes:
  redis_data:
```

#### 2. Build and Deploy
```bash
# Build and start services
docker-compose up --build -d

# Check logs
docker-compose logs -f app
```

---

## 🔍 Testing & Validation

### 1. Configuration Validation

```python
from ghl_real_estate_ai.services.realtime_config import validate_realtime_setup
import asyncio

# Validate complete setup
async def test_setup():
    result = await validate_realtime_setup()

    if result["ready_for_production"]:
        print("✅ Real-time setup ready for production")
    else:
        print("❌ Configuration issues found:")
        for error in result["validation"]["errors"]:
            print(f"  - {error}")

asyncio.run(test_setup())
```

### 2. Connection Testing

```python
from ghl_real_estate_ai.services.realtime_config import get_config_manager
import asyncio

# Test connections
async def test_connections():
    manager = get_config_manager()
    results = await manager.test_all_connections()

    print(f"Redis: {results['redis']['message']}")
    print(f"WebSocket: {results['websocket']['message']}")
    print(f"Overall Ready: {results['overall']['ready']}")

asyncio.run(test_connections())
```

### 3. Real-time Service Testing

```python
from ghl_real_estate_ai.streamlit_demo.services.realtime_data_service import get_realtime_service

# Test real-time data service
service = get_realtime_service(use_websocket=True)
service.start()

# Emit test event
service.emit_event("test_event", {"message": "Hello real-time!"})

# Check metrics
metrics = service.get_metrics()
print(f"Events processed: {metrics['events_processed']}")
print(f"Queue size: {metrics['queue_size']}")
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Redis Connection Failed
```bash
# Check Redis server status
redis-cli ping
# Expected: PONG

# Check connection from Python
python -c "import redis; r=redis.Redis(); print(r.ping())"
# Expected: True

# Check firewall/network
telnet localhost 6379
```

#### 2. WebSocket Connection Refused
```bash
# Check if WebSocket server is running
netstat -an | grep 8765

# Test WebSocket connection
python -c "
import asyncio
import websockets

async def test():
    try:
        async with websockets.connect('ws://localhost:8765/ws') as ws:
            print('WebSocket connected successfully')
    except Exception as e:
        print(f'WebSocket failed: {e}')

asyncio.run(test())
"
```

#### 3. Streamlit Real-time Updates Not Working
```python
# Check Streamlit session state
import streamlit as st

# In your Streamlit app, add debug info
if 'realtime_service' in st.session_state:
    service = st.session_state.realtime_service
    st.write("Service metrics:", service.get_metrics())
else:
    st.error("Real-time service not initialized")
```

#### 4. High Memory/CPU Usage
```bash
# Check Redis memory usage
redis-cli info memory

# Check WebSocket connections
ss -tuln | grep 8765

# Monitor Python processes
htop
```

### Environment-Specific Issues

#### Development
- **Port conflicts**: Change WEBSOCKET_PORT if 8765 is in use
- **Permission denied**: Use `sudo` for ports < 1024
- **Library missing**: Install with `pip install websockets redis`

#### Production (Railway)
- **Environment variables**: Verify in Railway dashboard
- **Redis timeout**: Increase REDIS_SOCKET_TIMEOUT for slower networks
- **WebSocket CORS**: Update WEBSOCKET_ORIGINS for your ontario_mills

#### Docker
- **Network isolation**: Use service names in REDIS_URL
- **Port mapping**: Ensure ports are exposed in Dockerfile
- **Volume permissions**: Check Redis data directory permissions

---

## 📊 Performance Optimization

### Redis Optimization
```bash
# Redis configuration for production
# /etc/redis/redis.conf

# Memory optimization
maxmemory 256mb
maxmemory-policy allkeys-lru

# Network optimization
tcp-keepalive 300
timeout 0

# Persistence (optional)
save 900 1
save 300 10
save 60 10000
```

### WebSocket Optimization
```python
# Production WebSocket settings
WEBSOCKET_MAX_SIZE=2097152        # 2MB
WEBSOCKET_MAX_QUEUE=100          # Higher queue for busy systems
WEBSOCKET_PING_INTERVAL=30       # Less frequent pings
WEBSOCKET_CLOSE_TIMEOUT=30       # Longer timeout for slow connections
```

### Streamlit Optimization
```python
# streamlit_demo/app.py
import streamlit as st

# Configure Streamlit for real-time updates
st.set_page_config(
    page_title="GHL Real Estate AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enable auto-refresh
if st.button("🔄 Enable Auto-refresh"):
    st.rerun()
```

---

## 📈 Monitoring & Metrics

### Health Check Endpoints
```python
# Add to your FastAPI/Streamlit app
from ghl_real_estate_ai.services.realtime_config import validate_realtime_setup

@app.get("/health/realtime")
async def realtime_health():
    result = await validate_realtime_setup()
    return {
        "status": "healthy" if result["ready_for_production"] else "unhealthy",
        "details": result
    }
```

### Key Metrics to Monitor
- **Redis**: Memory usage, connection count, command rate
- **WebSocket**: Connection count, message rate, error rate
- **Application**: Event processing rate, queue size, cache hit ratio

### Alerting
```bash
# Example monitoring script
python -c "
from ghl_real_estate_ai.services.realtime_config import get_redis_client
import sys

redis_client = get_redis_client()
if redis_client and redis_client.ping():
    print('Redis OK')
    sys.exit(0)
else:
    print('Redis FAIL')
    sys.exit(1)
"
```

---

## 🔄 Upgrade & Maintenance

### Dependency Updates
```bash
# Check for security updates
pip-audit

# Update dependencies
pip install --upgrade redis websockets aioredis

# Test after updates
python -m ghl_real_estate_ai.services.realtime_config
```

### Data Migration
```bash
# Backup Redis data
redis-cli save
cp /var/lib/redis/dump.rdb backup_$(date +%Y%m%d).rdb

# Restore Redis data
redis-cli flushall
redis-cli < backup.rdb
```

### Scaling Considerations
- **Horizontal scaling**: Use Redis Cluster for multiple instances
- **Load balancing**: Configure sticky sessions for WebSocket
- **Caching**: Implement distributed caching with Redis Sentinel

---

## 📚 Additional Resources

### Documentation
- [Redis Documentation](https://redis.io/documentation)
- [WebSockets Documentation](https://websockets.readthedocs.io/)
- [Streamlit Real-time Features](https://docs.streamlit.io/library/advanced-features/session-state)

### Examples
- Check `services/realtime_config.py` for configuration examples
- See `streamlit_demo/services/realtime_data_service.py` for implementation
- Review `tests/test_realtime_integration.py` for testing patterns

### Support
- GitHub Issues: Report bugs or feature requests
- Documentation: Update this guide for new configurations
- Community: Share best practices and optimizations

---

## ✅ Setup Checklist

### Development
- [ ] Redis server installed and running
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] Configuration validation passed
- [ ] Real-time service started
- [ ] Streamlit dashboard loading with real-time updates

### Production
- [ ] Railway Redis database added
- [ ] Production environment variables set
- [ ] WebSocket security enabled (wss://)
- [ ] Health checks configured
- [ ] Monitoring and alerting set up
- [ ] Backup procedures documented
- [ ] Performance testing completed

---

**🎉 Congratulations!** Your GHL Real Estate AI system now has full real-time capabilities with WebSocket and Redis support.