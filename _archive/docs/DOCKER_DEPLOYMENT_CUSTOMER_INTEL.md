# Customer Intelligence Platform - Docker Deployment Guide

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available
- AI API key (Anthropic Claude recommended)

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd customer-intelligence-platform

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Start the Platform
```bash
# Development mode (with hot reload)
docker-compose up -d

# Production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f
```

### 3. Access Services
- **Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database**: localhost:5432 (postgres/password)
- **Redis**: localhost:6379

## 📋 Service Architecture

### Container Overview
| Service | Port | Purpose | Dependencies |
|---------|------|---------|--------------|
| `api` | 8000 | FastAPI backend | redis, postgres |
| `dashboard` | 8501 | Streamlit frontend | api |
| `nginx` | 80, 443 | Reverse proxy | api, dashboard |
| `postgres` | 5432 | Database | none |
| `redis` | 6379 | Cache | none |

### Data Volumes
- `postgres_data`: PostgreSQL database files
- `redis_data`: Redis persistent storage
- `./data`: Application data (mounted)
- `./logs`: Application logs (mounted)

## ⚙️ Configuration

### Environment Variables

#### Required Configuration
```bash
# At least one AI provider API key
ANTHROPIC_API_KEY=your_claude_api_key
GEMINI_API_KEY=your_gemini_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

#### Database Configuration
```bash
# PostgreSQL (automatic in Docker Compose)
DATABASE_URL=postgresql://postgres:password@postgres:5432/customer_intelligence

# Redis (automatic in Docker Compose)
REDIS_URL=redis://redis:6379
```

#### Optional Configuration
```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/platform.log

# Application settings
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here

# Model settings
MODEL_STORAGE_PATH=./models
CHROMA_PERSIST_DIRECTORY=./.chroma_db
```

### Custom Docker Compose Override

Create `docker-compose.override.yml` for local customizations:
```yaml
version: '3.8'

services:
  api:
    environment:
      - CUSTOM_SETTING=value
    ports:
      - "8001:8000"  # Custom port mapping

  dashboard:
    environment:
      - STREAMLIT_THEME=light
```

## 🔧 Development Setup

### Hot Reload Development
```bash
# Start in development mode
docker-compose up

# The development override provides:
# - Volume mounting for live code changes
# - Debug logging
# - Auto-reload on file changes
```

### Building Custom Images
```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build api

# Build with no cache
docker-compose build --no-cache

# Build for production
docker build --target production -t customer-intelligence-platform .
```

### Development Commands
```bash
# Enter container shell
docker-compose exec api bash
docker-compose exec dashboard bash

# Run tests
docker-compose exec api python -m pytest

# Check logs
docker-compose logs api
docker-compose logs dashboard

# Restart service
docker-compose restart api
```

## 🚀 Production Deployment

### Production Environment
Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  api:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - RELOAD=false
    restart: always
    
  dashboard:
    environment:
      - ENVIRONMENT=production
    restart: always
    
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    restart: always
```

### SSL/HTTPS Setup
```bash
# Create SSL directory
mkdir ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem

# Or copy your real certificates
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Uncomment HTTPS server block in nginx.conf
```

### Resource Limits
Add resource constraints to `docker-compose.prod.yml`:
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          memory: 512M
          
  postgres:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
```

## 📊 Monitoring and Health Checks

### Health Check Endpoints
- **Platform Health**: `GET /health`
- **Database Health**: `GET /api/v1/health`
- **Scoring Service**: `GET /api/v1/scoring/health`

### Container Health Status
```bash
# Check all container health
docker-compose ps

# Check specific service health
docker-compose exec api curl -f http://localhost:8000/health

# Monitor resource usage
docker stats
```

### Log Management
```bash
# View all logs
docker-compose logs

# Follow specific service logs
docker-compose logs -f api

# Log rotation (add to docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔒 Security Best Practices

### Production Security Checklist
- [ ] Change default passwords
- [ ] Use strong secret keys
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall rules
- [ ] Set up log monitoring
- [ ] Regular security updates
- [ ] Backup encryption

### Environment Security
```bash
# Secure .env file permissions
chmod 600 .env

# Don't commit .env to git
echo ".env" >> .gitignore

# Use Docker secrets for sensitive data
echo "my_secret_password" | docker secret create db_password -
```

### Network Security
```yaml
# Custom network configuration
networks:
  customer-intelligence:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🗃️ Data Management

### Database Backup
```bash
# Backup PostgreSQL data
docker-compose exec postgres pg_dump -U postgres customer_intelligence > backup.sql

# Restore from backup
docker-compose exec -T postgres psql -U postgres customer_intelligence < backup.sql

# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec postgres pg_dump -U postgres customer_intelligence > "backup_${DATE}.sql"
```

### Volume Management
```bash
# List volumes
docker volume ls

# Backup volume data
docker run --rm -v customer-intelligence-platform_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz -C /data .

# Restore volume data
docker run --rm -v customer-intelligence-platform_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_backup.tar.gz -C /data
```

### Data Persistence
Ensure data persistence across container restarts:
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /opt/customer-intelligence/postgres
      o: bind
```

## 🔧 Troubleshooting

### Common Issues

#### API Connection Errors
```bash
# Check API health
curl -f http://localhost:8000/health

# Check container logs
docker-compose logs api

# Verify environment variables
docker-compose exec api printenv | grep API
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U postgres

# Test database connection
docker-compose exec api python -c "
from src.utils.database_service import get_database_service
import asyncio
async def test():
    db = get_database_service()
    health = await db.health_check()
    print(health)
asyncio.run(test())
"
```

#### Memory Issues
```bash
# Check memory usage
docker stats --no-stream

# Increase Docker memory limits
# Docker Desktop: Settings > Resources > Memory
```

### Performance Optimization

#### API Performance
```yaml
api:
  environment:
    - WORKERS=4  # Multiple workers
    - WORKER_CONNECTIONS=1000
  deploy:
    replicas: 2  # Scale horizontally
```

#### Database Optimization
```yaml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    - POSTGRES_MAX_CONNECTIONS=100
    - POSTGRES_SHARED_BUFFERS=256MB
```

#### Cache Optimization
```yaml
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

## 📈 Scaling

### Horizontal Scaling
```yaml
# Scale API service
docker-compose up --scale api=3

# Load balancer configuration
nginx:
  depends_on:
    - api
  environment:
    - UPSTREAM_SERVERS=api:8000,api_2:8000,api_3:8000
```

### Resource Monitoring
```bash
# Install monitoring stack
git clone https://github.com/stefanprodan/dockprom
cd dockprom
docker-compose up -d

# Access Grafana: http://localhost:3000
# admin/admin
```

## 🚀 Cloud Deployment

### AWS ECS/Fargate
```bash
# Build and push to ECR
aws ecr create-repository --repository-name customer-intelligence-platform
docker build -t customer-intelligence-platform .
docker tag customer-intelligence-platform:latest <account>.dkr.ecr.<region>.amazonaws.com/customer-intelligence-platform:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/customer-intelligence-platform:latest
```

### Google Cloud Run
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/<project>/customer-intelligence-platform
gcloud run deploy --image gcr.io/<project>/customer-intelligence-platform --platform managed
```

### Azure Container Instances
```bash
# Create resource group and deploy
az group create --name customer-intelligence --location eastus
az container create --resource-group customer-intelligence --file docker-compose.yml
```

---

## 📞 Support

For deployment issues:
- **Documentation**: Check README.md and troubleshooting section
- **Issues**: Open GitHub issue with deployment logs
- **Security**: Report security issues privately to security@company.com

**Remember**: Always test in development before deploying to production!