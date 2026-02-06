# Service 6 Docker Deployment Guide

## Overview

This guide covers the deployment of Service 6 Lead Recovery & Nurture Engine using the optimized multi-stage Dockerfile (`Dockerfile.service6`) and Docker Compose configuration.

## Architecture

### Multi-Stage Build Targets

| Stage | Purpose | Use Case |
|-------|---------|----------|
| `base` | Common dependencies | Foundation for all other stages |
| `dependencies` | Python packages | Shared layer for optimization |
| `development` | Dev environment | Local development with hot reload |
| `production-base` | Security hardened base | Foundation for production |
| `production` | Production ready | Optimized for production deployment |
| `demo` | Streamlit interface | Lightweight demo/UI access |

### Security Features

- **Non-root user**: All processes run as `appuser` (UID/GID 1000)
- **Minimal attack surface**: Only necessary packages installed
- **Security hardening**: System cleanup and package removal
- **Trusted host middleware**: Configurable allowed hosts
- **CORS protection**: Environment-specific CORS policies

### Health Checks & Monitoring

- **Liveness probe**: `/health/live` - Basic service availability
- **Readiness probe**: `/health/ready` - Service ready to handle traffic
- **Status endpoint**: `/health/status` - Detailed service information
- **Prometheus metrics**: `/metrics` - Application metrics
- **Structured logging**: JSON-formatted logs with correlation IDs

## Quick Start

### Development Environment

```bash
# Start with hot reloading
docker build -f Dockerfile.service6 --target development -t service6-dev .
docker run -p 8000:8000 -v $(pwd):/app service6-dev

# Or use Docker Compose for full stack
docker-compose -f docker-compose.service6.yml --profile dev up
```

### Production Deployment

```bash
# Build production image
docker build -f Dockerfile.service6 --target production -t service6-prod .

# Run with Docker Compose (recommended)
docker-compose -f docker-compose.service6.yml up -d

# Or run standalone
docker run -d \
  --name service6-app \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e REDIS_URL="redis://host:6379/0" \
  -e CLAUDE_API_KEY="your-api-key" \
  service6-prod
```

### Demo Interface

```bash
# Build and run Streamlit demo
docker build -f Dockerfile.streamlit --target demo -t service6-demo .
docker run -p 8501:8501 service6-demo

# Or use Docker Compose
docker-compose -f docker-compose.service6.yml --profile demo up
```

## Environment Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379/0` |
| `CLAUDE_API_KEY` | Claude AI API key | `sk-ant-api...` |
| `JWT_SECRET_KEY` | JWT signing secret | 32+ character string |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Deployment environment |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Logging level |
| `MAX_WORKERS` | `4` | Gunicorn worker count |
| `WORKER_TIMEOUT` | `30` | Worker timeout (seconds) |

### External Service Integration

Service 6 integrates with multiple external services. Configure these as needed:

```bash
# GoHighLevel
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_ghl_location_id

# Apollo.io
APOLLO_API_KEY=your_apollo_api_key

# Twilio
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_SENDER_EMAIL=noreply@yourcompany.com
```

## API Endpoints

### Health Checks

- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe  
- `GET /health/status` - Detailed status

### Service 6 AI APIs

- `POST /api/v1/leads/recover` - Lead recovery using AI
- `POST /api/v1/leads/nurture` - Lead nurture automation
- `GET /metrics` - Prometheus metrics

### Example API Usage

```bash
# Check service health
curl http://localhost:8000/health/ready

# Recover leads
curl -X POST http://localhost:8000/api/v1/leads/recover \
  -H "Content-Type: application/json" \
  -d '{"lead_ids": ["123", "456"], "strategy": "ai_personalized"}'

# Nurture leads
curl -X POST http://localhost:8000/api/v1/leads/nurture \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "nurture_001", "personalization_level": "high"}'
```

## Performance Optimization

### Production Settings

The production image is optimized for:

- **Fast startup**: Preloaded dependencies and application code
- **Memory efficiency**: Minimal Python image with only required packages
- **Connection pooling**: Optimized database and Redis connections
- **Worker scaling**: Configurable Gunicorn workers based on CPU cores
- **Caching**: Multi-level caching with Redis and application-level caches

### Resource Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| CPU | 1 core | 2 cores | 4+ cores |
| Memory | 512MB | 1GB | 2GB+ |
| Storage | 1GB | 5GB | 20GB+ |
| Network | 100Mbps | 1Gbps | 10Gbps+ |

## Monitoring & Observability

### Metrics Collection

Service 6 exposes Prometheus metrics at `/metrics`:

- Request count and duration
- Active connections
- Database query performance
- Cache hit rates
- AI service response times

### Logging

Structured JSON logging includes:

- Request/response correlation IDs
- User context and session tracking
- Performance timings
- Error details with stack traces
- Security events

### Alerting

Configure alerts for:

- High error rates (>5% error rate)
- Slow responses (>2s response time)
- Resource exhaustion (>80% memory/CPU)
- External service failures
- Security violations

## Troubleshooting

### Common Issues

**Container fails to start:**
```bash
# Check logs
docker logs service6-app

# Verify environment variables
docker exec service6-app env | grep -E "(DATABASE|REDIS|CLAUDE)"

# Test connectivity
docker exec service6-app curl http://localhost:8000/health/live
```

**Database connection errors:**
```bash
# Test database connectivity
docker exec service6-app pg_isready -h postgres -p 5432 -U service6_user

# Check database logs
docker logs service6-postgres
```

**Redis connection errors:**
```bash
# Test Redis connectivity
docker exec service6-app redis-cli -h redis ping

# Check Redis logs
docker logs service6-redis
```

### Performance Debugging

**High memory usage:**
```bash
# Monitor memory in container
docker exec service6-app cat /proc/meminfo
docker stats service6-app

# Check for memory leaks
docker exec service6-app python -c "
import psutil
process = psutil.Process()
print(f'Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB')
"
```

**Slow API responses:**
```bash
# Check application metrics
curl http://localhost:8000/metrics | grep -E "(request_duration|active_connections)"

# Monitor database performance
docker exec service6-postgres psql -U service6_user -d service6_leads -c "
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;"
```

## Security Considerations

### Container Security

- Runs as non-root user (UID 1000)
- Minimal attack surface with slim base image
- No unnecessary packages or tools installed
- Security-hardened system configuration

### Network Security

- TrustedHost middleware for host validation
- CORS policies configured per environment
- Rate limiting and request validation
- Secure headers and HTTPS enforcement

### Secrets Management

- Environment variables for configuration
- No secrets in container images
- Integration with external secret managers
- Secure credential rotation support

## Backup & Recovery

### Database Backups

```bash
# Create database backup
docker exec service6-postgres pg_dump \
  -U service6_user \
  -d service6_leads \
  -f /backup/service6_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker exec -i service6-postgres psql \
  -U service6_user \
  -d service6_leads < backup.sql
```

### Redis Persistence

Redis is configured with persistence:
- AOF (Append Only File) enabled
- Snapshots every 15 minutes
- Data persisted to Docker volumes

## Scaling

### Horizontal Scaling

```bash
# Scale with Docker Compose
docker-compose -f docker-compose.service6.yml up --scale service6-app=3

# Or use Docker Swarm
docker service scale service6_service6-app=3
```

### Load Balancing

Configure nginx or another load balancer:

```nginx
upstream service6_backend {
    server service6-app-1:8000;
    server service6-app-2:8000;
    server service6-app-3:8000;
}

server {
    location / {
        proxy_pass http://service6_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Support

For technical support or deployment assistance:

1. Check the troubleshooting section above
2. Review application logs: `docker logs service6-app`
3. Verify health endpoints: `curl http://localhost:8000/health/status`
4. Contact the Service 6 development team

---

**Last Updated**: January 2026  
**Version**: 1.0.0  
**Dockerfile**: `Dockerfile.service6`  
**Docker Compose**: `docker-compose.service6.yml`
