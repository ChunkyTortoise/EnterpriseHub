#!/bin/bash
# Jorge's Real Estate AI Platform - Production Docker Entrypoint
# Handles both API and Worker modes with proper initialization
# Author: Jorge Platform DevOps Team

set -euo pipefail

# Configuration
MODE="${1:-api}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
WORKERS="${WORKERS:-1}"
PORT="${PORT:-8000}"
TIMEOUT="${TIMEOUT:-120}"
KEEP_ALIVE="${KEEP_ALIVE:-5}"
MAX_REQUESTS="${MAX_REQUESTS:-1000}"
MAX_REQUESTS_JITTER="${MAX_REQUESTS_JITTER:-50}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[ENTRYPOINT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

# Wait for service to be ready
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local timeout="${3:-60}"
    local count=0

    log "Waiting for $service_name to be ready..."

    while ! eval "$check_command" &>/dev/null; do
        count=$((count + 1))
        if [[ $count -gt $timeout ]]; then
            error "$service_name is not ready after ${timeout}s"
            return 1
        fi
        log "Waiting for $service_name... (${count}s)"
        sleep 1
    done

    log "$service_name is ready!"
    return 0
}

# Initialize application
initialize_app() {
    log "Initializing Jorge Platform in $MODE mode..."

    # Set environment-specific variables
    export PYTHONPATH="/app:${PYTHONPATH:-}"
    export ENVIRONMENT="${ENVIRONMENT:-production}"

    # Validate required environment variables
    local required_vars=()

    case $MODE in
        "api"|"worker")
            required_vars+=(
                "DATABASE_URL"
                "REDIS_URL"
                "ANTHROPIC_API_KEY"
            )
            ;;
    esac

    # Check required environment variables
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done

    log "Environment validation completed"
}

# Wait for dependencies
wait_for_dependencies() {
    log "Checking dependencies..."

    # Extract database host and port from DATABASE_URL
    if [[ -n "${DATABASE_URL:-}" ]]; then
        local db_host db_port
        db_host=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\).*/\1/p')
        db_port=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

        if [[ -n "$db_host" && -n "$db_port" ]]; then
            wait_for_service "PostgreSQL" "nc -z $db_host $db_port" 60
        fi
    fi

    # Extract Redis host and port from REDIS_URL
    if [[ -n "${REDIS_URL:-}" ]]; then
        local redis_host redis_port
        redis_host=$(echo "$REDIS_URL" | sed -n 's/.*@\([^:]*\).*/\1/p' || echo "localhost")
        redis_port=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\).*/\1/p' || echo "6379")

        # Handle URLs without @ symbol
        if [[ "$redis_host" == "localhost" ]]; then
            redis_host=$(echo "$REDIS_URL" | sed -n 's/redis:\/\/\([^:]*\).*/\1/p' || echo "localhost")
        fi

        wait_for_service "Redis" "nc -z $redis_host $redis_port" 60
    fi

    log "All dependencies are ready"
}

# Run database migrations
run_migrations() {
    if [[ "$MODE" == "api" || "$MODE" == "migrate" ]]; then
        log "Running database migrations..."

        # Only run migrations if this is the primary worker
        if [[ "${WORKER_ID:-1}" == "1" || "$MODE" == "migrate" ]]; then
            cd /app
            if python -m alembic upgrade head; then
                log "Database migrations completed successfully"
            else
                error "Database migrations failed"
                exit 1
            fi
        else
            log "Skipping migrations (not primary worker)"
        fi
    fi
}

# Start API server
start_api() {
    log "Starting Jorge Platform API server..."

    # Validate API configuration
    if [[ ! -f "/app/app.py" && ! -f "/app/ghl_real_estate_ai/app.py" ]]; then
        error "FastAPI application file not found"
        exit 1
    fi

    # Determine the app module
    local app_module="app:app"
    if [[ -f "/app/ghl_real_estate_ai/app.py" ]]; then
        app_module="ghl_real_estate_ai.app:app"
    fi

    # Configure Gunicorn settings
    local gunicorn_config="/app/gunicorn.conf.py"

    # Create Gunicorn configuration if it doesn't exist
    if [[ ! -f "$gunicorn_config" ]]; then
        cat > "$gunicorn_config" << EOF
# Gunicorn configuration for Jorge Platform API

# Server socket
bind = "0.0.0.0:${PORT}"
backlog = 2048

# Worker processes
workers = ${WORKERS}
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = ${MAX_REQUESTS}
max_requests_jitter = ${MAX_REQUESTS_JITTER}
timeout = ${TIMEOUT}
keepalive = ${KEEP_ALIVE}

# Application
module = "${app_module}"

# Logging
loglevel = "${LOG_LEVEL,,}"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "jorge-api"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Performance
preload_app = True
enable_stdio_inheritance = True
EOF
    fi

    log "Starting Gunicorn with configuration:"
    log "  Workers: $WORKERS"
    log "  Port: $PORT"
    log "  Timeout: $TIMEOUT"
    log "  Log Level: $LOG_LEVEL"

    exec gunicorn -c "$gunicorn_config"
}

# Start worker processes
start_worker() {
    log "Starting Jorge Platform background worker..."

    # Validate worker configuration
    if [[ ! -f "/app/ghl_real_estate_ai/services/celery_app.py" ]]; then
        error "Celery worker configuration not found"
        exit 1
    fi

    # Set worker-specific environment
    export CELERY_WORKER_ID="${WORKER_ID:-1}"

    # Start Celery worker
    log "Starting Celery worker with configuration:"
    log "  Worker ID: ${CELERY_WORKER_ID}"
    log "  Concurrency: ${CELERY_CONCURRENCY:-4}"
    log "  Log Level: $LOG_LEVEL"

    cd /app
    exec celery -A ghl_real_estate_ai.services.celery_app worker \
        --loglevel="$LOG_LEVEL" \
        --concurrency="${CELERY_CONCURRENCY:-4}" \
        --hostname="jorge-worker-${CELERY_WORKER_ID}@%h" \
        --queues="${CELERY_QUEUES:-default,property_alerts,ml_processing}"
}

# Start worker scheduler (Celery Beat)
start_scheduler() {
    log "Starting Jorge Platform task scheduler..."

    # Only one scheduler should run
    if [[ "${SCHEDULER_ID:-1}" != "1" ]]; then
        error "Only one scheduler instance should run (SCHEDULER_ID=1)"
        exit 1
    fi

    cd /app
    exec celery -A ghl_real_estate_ai.services.celery_app beat \
        --loglevel="$LOG_LEVEL" \
        --schedule="/app/data/celerybeat-schedule"
}

# Health check function
health_check() {
    log "Running health check..."

    case $MODE in
        "api")
            curl -f "http://localhost:${PORT}/health" || exit 1
            ;;
        "worker")
            # Check if Celery worker is responsive
            celery -A ghl_real_estate_ai.services.celery_app inspect active || exit 1
            ;;
        *)
            log "Health check not implemented for mode: $MODE"
            ;;
    esac

    log "Health check passed"
}

# Graceful shutdown handler
shutdown() {
    local pid=$1
    log "Received shutdown signal, gracefully stopping..."

    # Send SIGTERM to the main process
    kill -TERM "$pid" 2>/dev/null || true

    # Wait for graceful shutdown
    local count=0
    while kill -0 "$pid" 2>/dev/null && [[ $count -lt 30 ]]; do
        count=$((count + 1))
        sleep 1
    done

    # Force kill if still running
    if kill -0 "$pid" 2>/dev/null; then
        warn "Process did not stop gracefully, forcing shutdown..."
        kill -KILL "$pid" 2>/dev/null || true
    fi

    log "Shutdown completed"
    exit 0
}

# Main execution
main() {
    log "Jorge Platform Docker Entrypoint"
    log "Mode: $MODE"
    log "Environment: ${ENVIRONMENT:-production}"

    # Set up signal handlers for graceful shutdown
    trap 'shutdown $$' SIGTERM SIGINT

    case $MODE in
        "api")
            initialize_app
            wait_for_dependencies
            run_migrations
            start_api
            ;;
        "worker")
            initialize_app
            wait_for_dependencies
            start_worker
            ;;
        "scheduler"|"beat")
            initialize_app
            wait_for_dependencies
            start_scheduler
            ;;
        "migrate")
            initialize_app
            wait_for_dependencies
            run_migrations
            log "Migrations completed, exiting"
            exit 0
            ;;
        "health")
            health_check
            exit 0
            ;;
        "shell")
            log "Starting interactive shell..."
            initialize_app
            exec /bin/bash
            ;;
        *)
            error "Unknown mode: $MODE"
            echo "Available modes: api, worker, scheduler, migrate, health, shell"
            exit 1
            ;;
    esac
}

# Execute main function
main "$@"