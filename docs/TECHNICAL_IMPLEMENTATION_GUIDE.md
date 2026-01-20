# 🔧 Customer Intelligence Platform - Technical Implementation Guide

**Complete technical reference for enterprise deployment and configuration**

---

## 📊 System Requirements & Architecture

### Minimum System Requirements

#### Production Environment
```yaml
Hardware Requirements:
  CPU: 4 cores (8 recommended)
  RAM: 8GB (16GB recommended)
  Storage: 100GB SSD (500GB recommended)
  Network: 1Gbps connection

Software Requirements:
  OS: Ubuntu 20.04+ / RHEL 8+ / CentOS 8+
  Docker: 20.10+
  Docker Compose: 2.0+
  Python: 3.11+
  PostgreSQL: 15+
  Redis: 7+
```

#### Development Environment
```yaml
Hardware Requirements:
  CPU: 2 cores minimum
  RAM: 4GB minimum
  Storage: 50GB available
  Network: Stable internet connection

Software Requirements:
  Docker Desktop: Latest stable
  Git: 2.30+
  Code Editor: VS Code / PyCharm recommended
```

### Architecture Overview

```mermaid
graph TB
    A[Load Balancer/Nginx] --> B[Streamlit App]
    B --> C[FastAPI Services]
    C --> D[Redis Cache]
    C --> E[PostgreSQL DB]
    C --> F[Claude AI API]
    
    B --> G[Customer Intelligence]
    G --> H[Real-time Analytics]
    G --> I[Segmentation Engine]
    G --> J[Journey Mapping]
    G --> K[Enterprise Tenant]
    
    L[GHL Integration] --> C
    M[External APIs] --> C
    
    subgraph "Data Layer"
        D
        E
        N[File Storage]
    end
    
    subgraph "AI Services"
        F
        O[Anthropic SDK]
        P[ML Pipeline]
    end
```

---

## 🛠 Docker Compose Deployment

### Core Infrastructure Stack

#### docker-compose.yml
```yaml
version: '3.8'

services:
  # Main Application
  customer-intelligence:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: customer-intelligence-app
    ports:
      - "${STREAMLIT_SERVER_PORT:-8501}:8501"
      - "8000:8000"  # FastAPI
    environment:
      - PYTHONUNBUFFERED=1
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: customer-intelligence-redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: customer-intelligence-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-enterprisehub}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
      - ./database/backups:/backups
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 3

  # Nginx Reverse Proxy (Production)
  nginx:
    image: nginx:alpine
    container_name: customer-intelligence-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - customer-intelligence
    restart: unless-stopped
    profiles:
      - production

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    container_name: customer-intelligence-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped
    profiles:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: customer-intelligence-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    restart: unless-stopped
    profiles:
      - monitoring

volumes:
  redis_data:
    driver: local
  postgres_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

networks:
  default:
    name: customer-intelligence-network
    driver: bridge
```

#### Production Override (docker-compose.production.yml)
```yaml
version: '3.8'

services:
  customer-intelligence:
    environment:
      - DEBUG_MODE=false
      - USE_DEMO_DATA=false
      - LOG_LEVEL=INFO
    volumes:
      - /opt/customer-intelligence/data:/app/data
      - /var/log/customer-intelligence:/app/logs
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G

  redis:
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G

  postgres:
    environment:
      - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

---

## 🔐 Environment Configuration

### Environment Variables Reference

#### Core Application Settings
```bash
# Application Configuration
ENVIRONMENT=production                    # development, staging, production
DEBUG_MODE=false                         # Enable debug logging
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
STREAMLIT_SERVER_PORT=8501              # Main app port
USE_DEMO_DATA=false                     # Use demo data for development

# Security Configuration
JWT_SECRET_KEY=your-secure-32-char-key   # JWT signing key
GHL_WEBHOOK_SECRET=webhook-secret        # GHL webhook validation
SESSION_TIMEOUT=3600                     # Session timeout in seconds
CORS_ORIGINS=*                          # CORS allowed origins

# AI & ML Configuration
ANTHROPIC_API_KEY=sk-ant-api03-xxx      # Claude API key (REQUIRED)
GOOGLE_API_KEY=your-google-key          # Optional: Google AI
PERPLEXITY_API_KEY=your-perplexity-key  # Optional: Perplexity AI
AI_REQUEST_TIMEOUT=30                    # AI API timeout
AI_MAX_RETRIES=3                        # AI API retry attempts
```

#### Database & Cache Configuration
```bash
# PostgreSQL Configuration
DATABASE_URL=postgresql://user:pass@host:5432/dbname
DB_POOL_SIZE=20                         # Connection pool size
DB_MAX_OVERFLOW=30                      # Max overflow connections
DB_POOL_TIMEOUT=30                      # Pool timeout in seconds
DB_POOL_RECYCLE=3600                    # Connection recycle time

# Redis Configuration
REDIS_URL=redis://localhost:6379/0      # Redis connection
REDIS_CACHE_TTL=3600                    # Default cache TTL
REDIS_MAX_CONNECTIONS=20                # Max Redis connections
REDIS_RETRY_ON_TIMEOUT=true             # Retry on timeout
```

#### Integration Settings
```bash
# GoHighLevel Integration
GHL_API_KEY=your-ghl-api-key
GHL_BASE_URL=https://rest.gohighlevel.com/v1
LOCATION_ID=your-location-id
GHL_RATE_LIMIT=100                      # Requests per minute

# Stripe Billing
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# External APIs
SENDGRID_API_KEY=SG.xxx                 # Email service
TWILIO_ACCOUNT_SID=ACxxx                # SMS service
TWILIO_AUTH_TOKEN=xxx
```

#### Performance & Monitoring
```bash
# Performance Settings
CACHE_ENABLED=true                      # Enable caching
CACHE_DEFAULT_TTL=300                   # Default cache TTL
MAX_WORKERS=4                           # Worker processes
ASYNC_POOL_SIZE=100                     # Async pool size

# Monitoring Configuration
SENTRY_DSN=https://xxx@sentry.io/xxx    # Error tracking
PROMETHEUS_ENABLED=true                 # Metrics collection
HEALTH_CHECK_INTERVAL=30                # Health check interval
```

---

## 🗄 Database Setup & Migration

### PostgreSQL Setup

#### Initial Database Setup
```sql
-- Create database and user
CREATE DATABASE enterprisehub;
CREATE USER intelligence_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE enterprisehub TO intelligence_user;

-- Configure PostgreSQL for optimal performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Restart PostgreSQL to apply changes
SELECT pg_reload_conf();
```

#### Database Migration System
```python
# database/migrations/migration_runner.py
#!/usr/bin/env python3
"""Database migration runner for Customer Intelligence Platform."""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime

class MigrationRunner:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.migrations_dir = Path(__file__).parent / "sql"
        
    def create_migration_table(self):
        """Create migration tracking table."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self):
        """Get list of applied migrations."""
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT version FROM schema_migrations ORDER BY version"
            ))
            return [row[0] for row in result]
    
    def get_pending_migrations(self):
        """Get list of pending migrations."""
        applied = set(self.get_applied_migrations())
        all_migrations = []
        
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            version = file_path.stem
            if version not in applied:
                all_migrations.append((version, file_path))
        
        return all_migrations
    
    def apply_migration(self, version: str, file_path: Path):
        """Apply a single migration."""
        print(f"Applying migration: {version}")
        
        with open(file_path, 'r') as f:
            sql_content = f.read()
        
        with self.engine.connect() as conn:
            # Execute migration SQL
            conn.execute(text(sql_content))
            
            # Record migration
            conn.execute(text(
                "INSERT INTO schema_migrations (version, description) VALUES (:version, :desc)"
            ), {"version": version, "desc": f"Migration {version}"})
            
            conn.commit()
        
        print(f"✅ Migration {version} applied successfully")
    
    def migrate(self):
        """Run all pending migrations."""
        self.create_migration_table()
        pending = self.get_pending_migrations()
        
        if not pending:
            print("✅ No pending migrations")
            return
        
        print(f"📦 Found {len(pending)} pending migrations")
        
        for version, file_path in pending:
            try:
                self.apply_migration(version, file_path)
            except Exception as e:
                print(f"❌ Failed to apply migration {version}: {e}")
                sys.exit(1)
        
        print("🎉 All migrations applied successfully!")

if __name__ == "__main__":
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    runner = MigrationRunner(database_url)
    runner.migrate()
```

#### Core Database Schema
```sql
-- database/migrations/001_create_core_tables.sql
-- Customer Intelligence Platform Core Schema

-- Tenants table for multi-tenancy
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Users table with role-based access
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Customer data table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    name VARCHAR(255),
    data JSONB DEFAULT '{}',
    segment VARCHAR(100),
    score DECIMAL(5,2),
    lifetime_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, customer_id),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Customer interactions/events
CREATE TABLE IF NOT EXISTS customer_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255),
    source VARCHAR(100),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Analytics aggregations table
CREATE TABLE IF NOT EXISTS analytics_aggregations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    dimensions JSONB DEFAULT '{}',
    value DECIMAL(15,4),
    date_key DATE NOT NULL,
    hour_key INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, metric_name, date_key, hour_key, dimensions),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_customers_tenant_id ON customers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(tenant_id, segment);
CREATE INDEX IF NOT EXISTS idx_customers_score ON customers(tenant_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_customer_events_tenant_customer ON customer_events(tenant_id, customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_events_type_timestamp ON customer_events(tenant_id, event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_tenant_metric_date ON analytics_aggregations(tenant_id, metric_name, date_key);

-- Enable row-level security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics_aggregations ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY tenant_customers ON customers
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.tenant_id', true));

CREATE POLICY tenant_events ON customer_events
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.tenant_id', true));

CREATE POLICY tenant_analytics ON analytics_aggregations
    FOR ALL TO PUBLIC
    USING (tenant_id = current_setting('app.tenant_id', true));
```

---

## 🔄 Redis Configuration

### Redis Setup & Optimization

#### redis.conf
```conf
# Redis configuration for Customer Intelligence Platform

# Network
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 60

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""

# Memory Management
maxmemory 1gb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# AOF Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Clients
maxclients 1000

# Security
requirepass your-redis-password

# Key Expiration
notify-keyspace-events Ex

# Performance
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

#### Redis Cache Strategy
```python
# ghl_real_estate_ai/services/redis_cache_manager.py
"""Redis cache management for Customer Intelligence Platform."""

import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RedisCacheManager:
    """Advanced Redis cache manager with multi-tenant support."""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.default_ttl = default_ttl
    
    def _get_key(self, tenant_id: str, key: str) -> str:
        """Generate tenant-scoped cache key."""
        return f"tenant:{tenant_id}:{key}"
    
    def set(self, tenant_id: str, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with tenant isolation."""
        try:
            cache_key = self._get_key(tenant_id, key)
            ttl = ttl or self.default_ttl
            
            # Serialize complex objects
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = pickle.dumps(value)
            
            return self.redis_client.setex(cache_key, ttl, serialized_value)
        
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    def get(self, tenant_id: str, key: str) -> Any:
        """Get cache value with tenant isolation."""
        try:
            cache_key = self._get_key(tenant_id, key)
            cached_value = self.redis_client.get(cache_key)
            
            if cached_value is None:
                return None
            
            # Try JSON deserialization first
            try:
                return json.loads(cached_value)
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(cached_value)
        
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    def delete(self, tenant_id: str, key: str) -> bool:
        """Delete cache value."""
        try:
            cache_key = self._get_key(tenant_id, key)
            return bool(self.redis_client.delete(cache_key))
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    def clear_tenant_cache(self, tenant_id: str) -> int:
        """Clear all cache for a tenant."""
        try:
            pattern = self._get_key(tenant_id, "*")
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Clear tenant cache error: {e}")
            return 0
    
    def get_cache_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get cache statistics for tenant."""
        try:
            pattern = self._get_key(tenant_id, "*")
            keys = self.redis_client.keys(pattern)
            
            stats = {
                "total_keys": len(keys),
                "memory_usage": 0,
                "hit_rate": 0,
                "keys_by_prefix": {}
            }
            
            # Calculate memory usage
            if keys:
                pipeline = self.redis_client.pipeline()
                for key in keys:
                    pipeline.memory_usage(key)
                memory_results = pipeline.execute()
                stats["memory_usage"] = sum(m for m in memory_results if m)
            
            return stats
        
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}
```

---

## 🚀 Deployment Scripts

### Production Deployment Script
```bash
#!/bin/bash
# scripts/deploy_production.sh
# Production deployment script for Customer Intelligence Platform

set -e

# Configuration
PROJECT_NAME="customer-intelligence"
DEPLOY_DIR="/opt/${PROJECT_NAME}"
BACKUP_DIR="/backup/${PROJECT_NAME}"
LOG_FILE="/var/log/${PROJECT_NAME}/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check system requirements
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check disk space (require at least 10GB free)
    available_space=$(df / | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        error "Insufficient disk space. At least 10GB required."
    fi
    
    # Check environment file
    if [ ! -f "${DEPLOY_DIR}/.env" ]; then
        error "Environment file not found at ${DEPLOY_DIR}/.env"
    fi
    
    log "Pre-deployment checks passed ✅"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    timestamp=$(date +%Y%m%d_%H%M%S)
    backup_path="${BACKUP_DIR}/${timestamp}"
    
    mkdir -p "$backup_path"
    
    # Backup database
    if docker ps | grep -q "${PROJECT_NAME}-postgres"; then
        log "Backing up database..."
        docker exec "${PROJECT_NAME}-postgres" pg_dumpall -U postgres > "${backup_path}/database_backup.sql"
    fi
    
    # Backup Redis data
    if docker ps | grep -q "${PROJECT_NAME}-redis"; then
        log "Backing up Redis data..."
        docker exec "${PROJECT_NAME}-redis" redis-cli BGSAVE
        docker cp "${PROJECT_NAME}-redis:/data/dump.rdb" "${backup_path}/redis_backup.rdb"
    fi
    
    # Backup application data
    if [ -d "${DEPLOY_DIR}/data" ]; then
        log "Backing up application data..."
        cp -r "${DEPLOY_DIR}/data" "${backup_path}/"
    fi
    
    # Backup configuration
    cp "${DEPLOY_DIR}/.env" "${backup_path}/"
    
    log "Backup created at ${backup_path} ✅"
    echo "$backup_path" > "${DEPLOY_DIR}/.last_backup"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    cd "$DEPLOY_DIR"
    
    # Pull latest images
    log "Pulling latest Docker images..."
    docker-compose -f docker-compose.yml -f docker-compose.production.yml pull
    
    # Build application image
    log "Building application image..."
    docker-compose -f docker-compose.yml -f docker-compose.production.yml build --no-cache
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose -f docker-compose.yml -f docker-compose.production.yml run --rm customer-intelligence python database/migrations/migration_runner.py
    
    # Start services with zero-downtime deployment
    log "Starting services..."
    docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d --remove-orphans
    
    log "Application deployed ✅"
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Wait for application to start
    sleep 30
    
    max_retries=30
    retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        if curl -f http://localhost:8501/health > /dev/null 2>&1; then
            log "Application health check passed ✅"
            return 0
        fi
        
        warn "Health check failed, retrying... ($((retry_count + 1))/$max_retries)"
        sleep 10
        retry_count=$((retry_count + 1))
    done
    
    error "Application health check failed after $max_retries attempts"
}

# Post-deployment tasks
post_deployment_tasks() {
    log "Running post-deployment tasks..."
    
    # Clean up old Docker images
    log "Cleaning up old Docker images..."
    docker image prune -f
    
    # Update system monitoring
    if command -v systemctl &> /dev/null; then
        log "Restarting monitoring services..."
        systemctl restart prometheus 2>/dev/null || true
        systemctl restart grafana 2>/dev/null || true
    fi
    
    # Send deployment notification (if webhook configured)
    if [ -n "${DEPLOYMENT_WEBHOOK}" ]; then
        curl -X POST "${DEPLOYMENT_WEBHOOK}" \
             -H "Content-Type: application/json" \
             -d "{\"text\": \"Customer Intelligence Platform deployed successfully at $(date)\"}" \
             2>/dev/null || warn "Failed to send deployment notification"
    fi
    
    log "Post-deployment tasks completed ✅"
}

# Main deployment flow
main() {
    log "Starting Customer Intelligence Platform deployment..."
    
    # Ensure deployment directory exists
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Change to deployment directory
    cd "$DEPLOY_DIR"
    
    # Run deployment steps
    pre_deployment_checks
    create_backup
    deploy_application
    health_check
    post_deployment_tasks
    
    log "🎉 Customer Intelligence Platform deployment completed successfully!"
    log "Application is running at: http://localhost:8501"
    log "Monitoring dashboard: http://localhost:3000"
    log "Deployment log: $LOG_FILE"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Environment Setup Script
```bash
#!/bin/bash
# scripts/setup_environment.sh
# Environment setup script for Customer Intelligence Platform

set -e

# Configuration
SETUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SETUP_DIR")"

# Load environment variables
source "${PROJECT_ROOT}/.env" 2>/dev/null || true

log() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')] $1\033[0m"
}

error() {
    echo -e "\033[0;31m[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1\033[0m"
    exit 1
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    directories=(
        "data/uploads"
        "data/exports" 
        "data/backups"
        "logs/application"
        "logs/nginx"
        "config/ssl"
        "database/backups"
        "monitoring/dashboards"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "${PROJECT_ROOT}/${dir}"
        log "Created directory: ${dir}"
    done
}

# Generate SSL certificates (self-signed for development)
generate_ssl_certificates() {
    log "Generating SSL certificates..."
    
    ssl_dir="${PROJECT_ROOT}/config/ssl"
    
    if [ ! -f "${ssl_dir}/server.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "${ssl_dir}/server.key" \
            -out "${ssl_dir}/server.crt" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        
        log "SSL certificates generated ✅"
    else
        log "SSL certificates already exist ✅"
    fi
}

# Setup database
setup_database() {
    log "Setting up database..."
    
    if [ -z "$DATABASE_URL" ]; then
        warn "DATABASE_URL not set, using default PostgreSQL setup"
        
        # Start PostgreSQL container
        docker-compose up -d postgres
        
        # Wait for PostgreSQL to start
        sleep 10
        
        # Run initial setup
        docker-compose exec postgres psql -U postgres -c "
            CREATE DATABASE IF NOT EXISTS enterprisehub;
            CREATE USER IF NOT EXISTS intelligence_user WITH ENCRYPTED PASSWORD 'secure_password';
            GRANT ALL PRIVILEGES ON DATABASE enterprisehub TO intelligence_user;
        "
    fi
    
    log "Database setup completed ✅"
}

# Setup Redis
setup_redis() {
    log "Setting up Redis..."
    
    # Create Redis configuration
    redis_conf="${PROJECT_ROOT}/config/redis.conf"
    
    if [ ! -f "$redis_conf" ]; then
        cat > "$redis_conf" << 'EOF'
# Redis configuration for Customer Intelligence Platform
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
EOF
        log "Redis configuration created ✅"
    fi
    
    # Start Redis container
    docker-compose up -d redis
    
    log "Redis setup completed ✅"
}

# Initialize application data
initialize_application() {
    log "Initializing application..."
    
    # Install Python dependencies
    if [ -f "${PROJECT_ROOT}/requirements.txt" ]; then
        log "Installing Python dependencies..."
        pip install -r "${PROJECT_ROOT}/requirements.txt"
    fi
    
    # Run database migrations
    log "Running database migrations..."
    python "${PROJECT_ROOT}/database/migrations/migration_runner.py"
    
    # Create default tenant and admin user
    log "Creating default tenant and admin user..."
    python -c "
import sys
sys.path.append('${PROJECT_ROOT}')

from ghl_real_estate_ai.services.tenant_service import TenantService
from ghl_real_estate_ai.services.user_management import create_admin_user

# Create default tenant
tenant_service = TenantService()
tenant_service.create_tenant(
    tenant_id='default',
    name='Default Tenant',
    settings={'theme': 'default', 'analytics_enabled': True}
)

# Create admin user
create_admin_user(
    username='admin',
    password='admin123',
    tenant_id='default',
    email='admin@example.com'
)

print('Default tenant and admin user created successfully')
"
    
    log "Application initialization completed ✅"
}

# Main setup flow
main() {
    log "Setting up Customer Intelligence Platform environment..."
    
    cd "$PROJECT_ROOT"
    
    create_directories
    generate_ssl_certificates
    setup_database
    setup_redis
    initialize_application
    
    log "🎉 Environment setup completed successfully!"
    log ""
    log "Next steps:"
    log "1. Update .env file with your API keys"
    log "2. Run: docker-compose up -d"
    log "3. Access the application at: http://localhost:8501"
    log "4. Login with username: admin, password: admin123"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## 📊 Performance Optimization

### Application Performance Tuning

#### Streamlit Configuration
```toml
# .streamlit/config.toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
maxMessageSize = 200
enableWebsocketCompression = true

[browser]
gatherUsageStats = false
showErrorDetails = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[runner]
magicEnabled = true
installTracer = false
fixMatplotlib = true
postScriptGC = true
fastReruns = true
enforceSerializableSessionState = true

[cache]
allowOutputMutation = false
suppressCachedStmtWarning = false
maxCachedStmts = 100
```

#### FastAPI Performance Settings
```python
# app_config.py
"""FastAPI application configuration for optimal performance."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

def create_app() -> FastAPI:
    """Create optimized FastAPI application."""
    
    app = FastAPI(
        title="Customer Intelligence Platform API",
        version="1.0.0",
        description="High-performance API for customer intelligence and analytics",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Add middleware for performance
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app

# Uvicorn configuration for production
UVICORN_CONFIG = {
    "app": "app:app",
    "host": "0.0.0.0", 
    "port": 8000,
    "workers": 4,  # Adjust based on CPU cores
    "worker_class": "uvicorn.workers.UvicornWorker",
    "worker_connections": 1000,
    "max_requests": 1000,
    "max_requests_jitter": 100,
    "preload_app": True,
    "keepalive": 2,
    "access_log": True,
    "use_colors": False,
}
```

### Database Performance Optimization

#### PostgreSQL Performance Tuning
```sql
-- Database performance optimization queries

-- Analyze table statistics
ANALYZE customers;
ANALYZE customer_events;
ANALYZE analytics_aggregations;

-- Create additional performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customer_events_timestamp_btree 
ON customer_events USING btree(timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_customers_updated_at 
ON customers USING btree(updated_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_date_metric 
ON analytics_aggregations USING btree(date_key DESC, metric_name);

-- Partition large tables by date (for customer_events)
CREATE TABLE customer_events_2026 PARTITION OF customer_events
FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Configure autovacuum for optimal performance
ALTER TABLE customer_events SET (
    autovacuum_vacuum_scale_factor = 0.1,
    autovacuum_analyze_scale_factor = 0.05
);

-- Create materialized views for common queries
CREATE MATERIALIZED VIEW customer_summary AS
SELECT 
    tenant_id,
    segment,
    COUNT(*) as customer_count,
    AVG(score) as avg_score,
    SUM(lifetime_value) as total_ltv,
    DATE_TRUNC('day', updated_at) as date_key
FROM customers 
GROUP BY tenant_id, segment, DATE_TRUNC('day', updated_at);

-- Refresh materialized view periodically
CREATE INDEX ON customer_summary (tenant_id, date_key);

-- Query optimization examples
EXPLAIN ANALYZE SELECT * FROM customers WHERE tenant_id = 'tenant1' AND score > 80;
```

---

## 🔍 Monitoring & Observability

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "rules/*.yml"

scrape_configs:
  - job_name: 'customer-intelligence'
    static_configs:
      - targets: ['customer-intelligence:8501', 'customer-intelligence:8000']
    metrics_path: /metrics
    scrape_interval: 30s
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'docker'
    static_configs:
      - targets: ['host.docker.internal:9323']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Health Check Implementation
```python
# ghl_real_estate_ai/api/routes/health.py
"""Health check endpoints for monitoring."""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import asyncio
import redis
import sqlalchemy
from typing import Dict, Any

router = APIRouter()

class HealthChecker:
    """Comprehensive health checking for all system components."""
    
    def __init__(self, database_url: str, redis_url: str):
        self.database_url = database_url
        self.redis_url = redis_url
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity and performance."""
        try:
            engine = sqlalchemy.create_engine(self.database_url)
            start_time = datetime.now()
            
            with engine.connect() as conn:
                result = conn.execute(sqlalchemy.text("SELECT 1"))
                result.fetchone()
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis connectivity and performance."""
        try:
            client = redis.from_url(self.redis_url)
            start_time = datetime.now()
            
            client.ping()
            info = client.info()
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "memory_usage": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def check_ai_services(self) -> Dict[str, Any]:
        """Check AI service availability."""
        try:
            import anthropic
            client = anthropic.Anthropic()
            
            # Simple API test
            start_time = datetime.now()
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            response_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "response_time": response_time,
                "model": "claude-3-haiku-20240307",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

health_checker = HealthChecker(
    database_url=os.getenv("DATABASE_URL"),
    redis_url=os.getenv("REDIS_URL")
)

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed") 
async def detailed_health_check():
    """Detailed health check for all components."""
    
    # Run all health checks concurrently
    results = await asyncio.gather(
        health_checker.check_database(),
        health_checker.check_redis(),
        health_checker.check_ai_services(),
        return_exceptions=True
    )
    
    database_health, redis_health, ai_health = results
    
    overall_status = "healthy"
    if any(check.get("status") == "unhealthy" 
           for check in [database_health, redis_health, ai_health]):
        overall_status = "degraded"
    
    return {
        "overall_status": overall_status,
        "components": {
            "database": database_health,
            "redis": redis_health, 
            "ai_services": ai_health
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint."""
    # Implementation would export metrics in Prometheus format
    # This is a simplified example
    
    metrics = [
        "# HELP http_requests_total Total HTTP requests",
        "# TYPE http_requests_total counter",
        "http_requests_total{method=\"GET\",endpoint=\"/health\"} 42",
        "",
        "# HELP database_connections_active Active database connections", 
        "# TYPE database_connections_active gauge",
        "database_connections_active 5"
    ]
    
    return "\n".join(metrics)
```

This Technical Implementation Guide provides comprehensive coverage of:

1. **System Architecture & Requirements** - Clear hardware/software specifications
2. **Docker Deployment** - Production-ready containerization with monitoring
3. **Database Setup** - PostgreSQL optimization, migrations, and performance tuning  
4. **Redis Configuration** - Caching strategy and performance optimization
5. **Environment Configuration** - Complete environment variable reference
6. **Deployment Automation** - Production deployment and setup scripts
7. **Performance Optimization** - Application, database, and caching optimizations
8. **Monitoring & Health Checks** - Comprehensive observability and alerting

The guide ensures smooth technical implementation with enterprise-grade deployment practices, security considerations, and performance optimization strategies.