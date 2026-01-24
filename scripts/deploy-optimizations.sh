#!/bin/bash

# Jorge Platform - Complete Optimization Deployment Script
# Generated from 8-track optimization consolidation analysis

set -e

echo "🚀 Deploying Jorge Platform Optimizations..."
echo "=================================="

# Phase 1: Infrastructure
echo "📦 Phase 1: Deploying Infrastructure..."
docker-compose -f docker-compose.scale.yml up -d postgres-master postgres-replica-1 redis-master
docker-compose -f docker-compose.scale.yml up -d prometheus grafana elasticsearch kibana
docker-compose -f docker-compose.scale.yml up -d nginx

# Phase 2: Performance Services
echo "⚡ Phase 2: Deploying Performance Services..."
docker-compose -f docker-compose.scale.yml restart api-instance-1 api-instance-2 celery-worker-1 celery-worker-2
sleep 10

# Phase 3: WebSocket Integration
echo "🔗 Phase 3: Deploying WebSocket Integration..."
curl -f http://localhost:8000/api/websocket/health || exit 1

# Phase 4: Frontend Optimizations
echo "📱 Phase 4: Deploying Frontend Optimizations..."
npm run build --prod
docker-compose restart frontend-1 frontend-2 frontend-3

# Phase 5: Validation
echo "🧪 Phase 5: Validating Deployment..."
./scripts/health-check.sh --full

echo "✅ Jorge Platform Optimizations Deployed Successfully!"
echo "📊 Performance Dashboard: http://localhost:3001"
echo "🎯 Jorge Command Center: http://localhost:3000/jorge"