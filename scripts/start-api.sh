#!/bin/bash
# =========================================================================
# Startup Script for Jorge's Real Estate AI FastAPI Backend
# Includes Socket.IO integration for horizontal scaling
# =========================================================================

set -e  # Exit on any error

echo "🚀 Starting Jorge's Real Estate AI Backend API..."
echo "Instance ID: ${INSTANCE_ID:-api-unknown}"
echo "Worker ID: ${WORKER_ID:-1}/${TOTAL_WORKERS:-1}"
echo "Environment: ${ENVIRONMENT:-development}"

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL database..."
while ! pg_isready -h $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/') -p $(echo $DATABASE_URL | sed 's/.*:\([0-9]*\).*/\1/') -U $(echo $DATABASE_URL | sed 's/.*\/\/\([^:]*\).*/\1/'); do
    echo "Database not ready, waiting 2 seconds..."
    sleep 2
done
echo "✅ Database connection confirmed"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis cache..."
REDIS_HOST=$(echo $REDIS_URL | sed 's/redis:\/\/\([^:]*\).*/\1/')
REDIS_PORT=$(echo $REDIS_URL | sed 's/.*:\([0-9]*\).*/\1/')
until redis-cli -h $REDIS_HOST -p $REDIS_PORT ping; do
    echo "Redis not ready, waiting 2 seconds..."
    sleep 2
done
echo "✅ Redis connection confirmed"

# Run database migrations (only on worker 1)
if [ "${WORKER_ID:-1}" = "1" ]; then
    echo "🔧 Running database migrations..."
    cd /app && alembic upgrade head
    echo "✅ Database migrations completed"
fi

# Install additional Socket.IO dependencies if not already present
echo "🔌 Ensuring Socket.IO dependencies are available..."
pip install --no-cache-dir python-socketio[asyncio-client] redis aioredis

echo "🚀 Starting FastAPI application with Socket.IO support..."

# Start the application with Socket.IO integration
exec uvicorn ghl_real_estate_ai.api.main:socketio_app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --loop asyncio \
    --log-level ${LOG_LEVEL:-info} \
    --access-log \
    --use-colors \
    --proxy-headers \
    --forwarded-allow-ips="*"