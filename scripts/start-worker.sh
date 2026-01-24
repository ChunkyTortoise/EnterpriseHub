#!/bin/bash
# =========================================================================
# Startup Script for Jorge's Real Estate AI Background Workers
# Handles Celery worker initialization and health checks
# =========================================================================

set -e  # Exit on any error

echo "🔧 Starting Jorge's Real Estate AI Background Worker..."
echo "Worker Name: ${WORKER_NAME:-worker-default}"
echo "Environment: ${ENVIRONMENT:-development}"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis broker..."
REDIS_HOST=$(echo $CELERY_BROKER_URL | sed 's/redis:\/\/\([^:]*\).*/\1/')
REDIS_PORT=$(echo $CELERY_BROKER_URL | sed 's/.*:\([0-9]*\).*/\1/')
until redis-cli -h $REDIS_HOST -p $REDIS_PORT ping; do
    echo "Redis not ready, waiting 2 seconds..."
    sleep 2
done
echo "✅ Redis broker connection confirmed"

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL database..."
while ! pg_isready -h $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/') -p $(echo $DATABASE_URL | sed 's/.*:\([0-9]*\).*/\1/') -U $(echo $DATABASE_URL | sed 's/.*\/\/\([^:]*\).*/\1/'); do
    echo "Database not ready, waiting 2 seconds..."
    sleep 2
done
echo "✅ Database connection confirmed"

echo "🚀 Starting Celery worker for background job processing..."

# Start Celery worker with optimized settings
exec celery -A ghl_real_estate_ai.services.celery_app worker \
    --loglevel=${LOG_LEVEL:-info} \
    --hostname=${WORKER_NAME:-worker}@%h \
    --concurrency=4 \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=100 \
    --time-limit=300 \
    --soft-time-limit=240 \
    --without-mingle \
    --without-gossip