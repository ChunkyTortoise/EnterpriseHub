#!/bin/bash
# ==============================================================================
# Service 6 Production Startup Script
# ==============================================================================
#
# Optimized startup script for Service 6 Lead Recovery & Nurture Engine
# with proper health checks, graceful shutdown, and monitoring integration
# ==============================================================================

set -euo pipefail

# Configuration
export ENVIRONMENT="${ENVIRONMENT:-production}"
export DEBUG="${DEBUG:-false}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export MAX_WORKERS="${MAX_WORKERS:-4}"
export WORKER_TIMEOUT="${WORKER_TIMEOUT:-30}"
export KEEPALIVE="${KEEPALIVE:-2}"

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for Service 6 to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:8000/health/live > /dev/null 2>&1; then
            echo "Service 6 is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: Service 6 not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "Service 6 failed to start within expected time"
    return 1
}

# Graceful shutdown handler
shutdown_handler() {
    echo "Received shutdown signal, gracefully stopping Service 6..."
    if [ ! -z "${GUNICORN_PID:-}" ]; then
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true
        wait "$GUNICORN_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# Validate environment
echo "Starting Service 6 Lead Recovery & Nurture Engine..."
echo "Environment: $ENVIRONMENT"
echo "Debug mode: $DEBUG"
echo "Log level: $LOG_LEVEL"
echo "Max workers: $MAX_WORKERS"

# Database migration (if needed)
if [ "$ENVIRONMENT" = "production" ] && [ -f "alembic.ini" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || {
        echo "Database migration failed"
        exit 1
    }
fi

# Start the application
if [ "$ENVIRONMENT" = "development" ]; then
    echo "Starting in development mode with hot reloading..."
    exec uvicorn service6_app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --reload-dir /app \
        --log-level debug
else
    echo "Starting in production mode with Gunicorn..."
    exec python -m gunicorn service6_app:app \
        --bind 0.0.0.0:8000 \
        --worker-class uvicorn.workers.UvicornWorker \
        --workers "$MAX_WORKERS" \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout "$WORKER_TIMEOUT" \
        --keepalive "$KEEPALIVE" \
        --preload \
        --access-logfile - \
        --error-logfile - \
        --log-level info \
        --capture-output \
        --enable-stdio-inheritance &
    
    GUNICORN_PID=$!
    
    # Wait for startup and run health check
    sleep 5
    health_check
    
    # Wait for the process to finish
    wait "$GUNICORN_PID"
fi
