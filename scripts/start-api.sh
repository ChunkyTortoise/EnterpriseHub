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

# Ensure required env vars exist
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is not set"
    exit 1
fi
if [ -z "$REDIS_URL" ]; then
    echo "❌ REDIS_URL is not set"
    exit 1
fi

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL database..."
while ! pg_isready -h $(echo $DATABASE_URL | sed 's/.*@\([^:]*\).*/\1/') -p $(echo $DATABASE_URL | sed 's/.*:\([0-9]*\).*/\1/') -U $(echo $DATABASE_URL | sed 's/.*\/\/\([^:]*\).*/\1/'); do
    echo "Database not ready, waiting 2 seconds..."
    sleep 2
done
echo "✅ Database connection confirmed"

# Wait for Redis to be ready
echo "⏳ Waiting for Redis cache..."
REDIS_HOST=$(python - <<'PY'
from urllib.parse import urlparse
import os
u = urlparse(os.environ["REDIS_URL"])
print(u.hostname or "")
PY
)
REDIS_PORT=$(python - <<'PY'
from urllib.parse import urlparse
import os
u = urlparse(os.environ["REDIS_URL"])
print(u.port or 6379)
PY
)
REDIS_PASSWORD=$(python - <<'PY'
from urllib.parse import urlparse
import os
u = urlparse(os.environ["REDIS_URL"])
print(u.password or "")
PY
)
if [ -n "$REDIS_PASSWORD" ]; then
    REDIS_AUTH="-a $REDIS_PASSWORD"
else
    REDIS_AUTH=""
fi
until redis-cli -h $REDIS_HOST -p $REDIS_PORT $REDIS_AUTH ping; do
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
