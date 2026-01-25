#!/bin/bash
# ==============================================================================
# JORGE'S BI DASHBOARD - PRODUCTION ENTRYPOINT SCRIPT
# Handles application startup, migrations, and graceful shutdown
# ==============================================================================

set -e

# Color codes for logging
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_debug() {
    if [[ "${LOG_LEVEL:-INFO}" == "DEBUG" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $1"
    fi
}

# ==============================================================================
# ENVIRONMENT VALIDATION
# ==============================================================================

validate_environment() {
    log_info "Validating production environment..."

    # Check required environment variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "ANTHROPIC_API_KEY"
        "JWT_SECRET_KEY"
        "GHL_LOCATION_ID"
        "GHL_API_KEY"
    )

    local missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        exit 1
    fi

    # Validate environment setting
    if [[ "${ENVIRONMENT}" != "production" ]]; then
        log_warn "ENVIRONMENT is set to '${ENVIRONMENT}', expected 'production'"
    fi

    # Validate DEBUG setting
    if [[ "${DEBUG,,}" == "true" ]] && [[ "${ENVIRONMENT}" == "production" ]]; then
        log_error "DEBUG cannot be 'true' in production environment"
        exit 1
    fi

    log_success "Environment validation completed"
}

# ==============================================================================
# DATABASE CONNECTIVITY
# ==============================================================================

wait_for_database() {
    log_info "Waiting for database connectivity..."

    local retries=30
    local count=0

    while [ $count -lt $retries ]; do
        if python -c "
import asyncpg
import asyncio
import os
import sys

async def check_db():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        await conn.close()
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(check_db())
sys.exit(0 if result else 1)
        " 2>/dev/null; then
            log_success "Database connectivity confirmed"
            return 0
        fi

        count=$((count + 1))
        log_info "Database not ready, attempt $count/$retries. Retrying in 2 seconds..."
        sleep 2
    done

    log_error "Database failed to become ready after $retries attempts"
    exit 1
}

wait_for_redis() {
    log_info "Waiting for Redis connectivity..."

    local retries=15
    local count=0

    while [ $count -lt $retries ]; do
        if python -c "
import redis
import os
import sys

try:
    client = redis.from_url(os.getenv('REDIS_URL'))
    client.ping()
    client.close()
    sys.exit(0)
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
        " 2>/dev/null; then
            log_success "Redis connectivity confirmed"
            return 0
        fi

        count=$((count + 1))
        log_info "Redis not ready, attempt $count/$retries. Retrying in 1 second..."
        sleep 1
    done

    log_error "Redis failed to become ready after $retries attempts"
    exit 1
}

# ==============================================================================
# DATABASE MIGRATIONS
# ==============================================================================

run_migrations() {
    log_info "Running database migrations..."

    # Check if migration table exists and has pending migrations
    python -c "
import asyncio
import asyncpg
import os

async def check_migrations():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

        # Check if alembic_version table exists
        result = await conn.fetch('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'alembic_version'
            );
        ''')

        table_exists = result[0]['exists']
        await conn.close()

        print(f'Migration table exists: {table_exists}')
        return table_exists
    except Exception as e:
        print(f'Migration check failed: {e}')
        return False

result = asyncio.run(check_migrations())
    "

    # Run Alembic migrations
    if [[ -f "alembic.ini" ]]; then
        log_info "Running Alembic migrations..."
        python -m alembic upgrade head

        if [[ $? -eq 0 ]]; then
            log_success "Database migrations completed successfully"
        else
            log_error "Database migration failed"
            exit 1
        fi
    else
        log_warn "No alembic.ini found, skipping migrations"
    fi
}

# ==============================================================================
# CACHE INITIALIZATION
# ==============================================================================

initialize_cache() {
    log_info "Initializing cache systems..."

    python -c "
import asyncio
import redis
import os

async def init_redis():
    try:
        client = redis.from_url(os.getenv('REDIS_URL'))

        # Test basic operations
        client.set('jorge:bi:startup:test', 'ok', ex=60)
        result = client.get('jorge:bi:startup:test')

        if result == b'ok':
            print('Cache initialization successful')
        else:
            print('Cache test failed')
            exit(1)

        client.close()
    except Exception as e:
        print(f'Cache initialization failed: {e}')
        exit(1)

asyncio.run(init_redis())
    "

    if [[ $? -eq 0 ]]; then
        log_success "Cache systems initialized"
    else
        log_error "Cache initialization failed"
        exit 1
    fi
}

# ==============================================================================
# AI SERVICE VALIDATION
# ==============================================================================

validate_ai_services() {
    log_info "Validating AI service connectivity..."

    python -c "
import os
import sys
import anthropic
import asyncio

async def validate_anthropic():
    try:
        client = anthropic.AsyncAnthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        # Test with a minimal request
        response = await client.messages.create(
            model='claude-3-sonnet-20241022',
            max_tokens=10,
            messages=[{'role': 'user', 'content': 'Hello'}]
        )

        if response and response.content:
            print('Anthropic API validation successful')
            return True
        else:
            print('Anthropic API validation failed: No response content')
            return False

    except Exception as e:
        print(f'Anthropic API validation failed: {e}')
        return False

result = asyncio.run(validate_anthropic())
sys.exit(0 if result else 1)
    "

    if [[ $? -eq 0 ]]; then
        log_success "AI services validation completed"
    else
        log_warn "AI service validation failed - continuing with degraded functionality"
    fi
}

# ==============================================================================
# APPLICATION STARTUP
# ==============================================================================

pre_start_validation() {
    log_info "Running pre-start validation checks..."

    # Configuration validation
    if [[ -f "scripts/validate-bi-production-config.py" ]]; then
        log_info "Running configuration validation..."
        python scripts/validate-bi-production-config.py --config /dev/null 2>/dev/null || log_warn "Config validation script found issues"
    fi

    # Import validation
    python -c "
try:
    from ghl_real_estate_ai.api.main import app
    from ghl_real_estate_ai.services.bi_websocket_server import get_bi_websocket_manager
    from ghl_real_estate_ai.services.bi_cache_service import get_bi_cache_service
    print('Application imports successful')
except ImportError as e:
    print(f'Import validation failed: {e}')
    exit(1)
    "

    if [[ $? -eq 0 ]]; then
        log_success "Pre-start validation completed"
    else
        log_error "Pre-start validation failed"
        exit 1
    fi
}

start_application() {
    log_info "Starting Jorge's BI Dashboard Backend..."

    # Set default values for production
    WORKERS=${WORKERS:-4}
    PORT=${PORT:-8000}
    WORKER_CLASS=${WORKER_CLASS:-uvicorn.workers.UvicornWorker}
    MAX_REQUESTS=${MAX_REQUESTS:-1000}
    MAX_REQUESTS_JITTER=${MAX_REQUESTS_JITTER:-100}
    TIMEOUT=${TIMEOUT:-30}
    KEEPALIVE=${KEEPALIVE:-5}

    log_info "Application configuration:"
    log_info "  Workers: $WORKERS"
    log_info "  Port: $PORT"
    log_info "  Worker Class: $WORKER_CLASS"
    log_info "  Timeout: $TIMEOUT seconds"
    log_info "  Max Requests: $MAX_REQUESTS"

    # Start Gunicorn with Uvicorn workers for async support
    exec python -m gunicorn \
        --worker-class "$WORKER_CLASS" \
        --workers "$WORKERS" \
        --bind "0.0.0.0:$PORT" \
        --timeout "$TIMEOUT" \
        --keepalive "$KEEPALIVE" \
        --max-requests "$MAX_REQUESTS" \
        --max-requests-jitter "$MAX_REQUESTS_JITTER" \
        --access-logfile - \
        --error-logfile - \
        --log-level "${LOG_LEVEL:-info}" \
        --preload \
        --enable-stdio-inheritance \
        "ghl_real_estate_ai.api.main:app"
}

# ==============================================================================
# SIGNAL HANDLING FOR GRACEFUL SHUTDOWN
# ==============================================================================

graceful_shutdown() {
    log_info "Received shutdown signal, initiating graceful shutdown..."

    # Send SIGTERM to all child processes
    if [[ ! -z "$GUNICORN_PID" ]]; then
        log_info "Shutting down Gunicorn (PID: $GUNICORN_PID)..."
        kill -TERM "$GUNICORN_PID" 2>/dev/null || true

        # Wait for graceful shutdown
        local count=0
        while [[ $count -lt 30 ]] && kill -0 "$GUNICORN_PID" 2>/dev/null; do
            sleep 1
            count=$((count + 1))
        done

        # Force kill if still running
        if kill -0 "$GUNICORN_PID" 2>/dev/null; then
            log_warn "Forcing shutdown of Gunicorn..."
            kill -KILL "$GUNICORN_PID" 2>/dev/null || true
        fi
    fi

    log_success "Graceful shutdown completed"
    exit 0
}

# Set up signal handlers
trap graceful_shutdown SIGTERM SIGINT

# ==============================================================================
# HEALTH CHECK FUNCTION
# ==============================================================================

health_check() {
    log_info "Performing health check..."

    # Check if the application is responding
    if curl -f -s "http://localhost:${PORT:-8000}/health" >/dev/null; then
        log_success "Health check passed"
        return 0
    else
        log_error "Health check failed"
        return 1
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    log_info "🚀 Jorge's BI Dashboard Backend - Production Startup"
    log_info "Version: ${VERSION:-2.0.0}"
    log_info "Environment: ${ENVIRONMENT:-production}"
    log_info "Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

    # Handle special commands
    case "${1:-start}" in
        "health-check")
            health_check
            exit $?
            ;;
        "migrate")
            wait_for_database
            run_migrations
            exit 0
            ;;
        "validate")
            validate_environment
            exit 0
            ;;
        "start"|"")
            # Full startup sequence
            validate_environment
            wait_for_database
            wait_for_redis
            run_migrations
            initialize_cache
            validate_ai_services
            pre_start_validation

            log_success "🎯 All startup checks passed - launching application"
            start_application
            ;;
        *)
            log_error "Unknown command: $1"
            log_info "Available commands: start (default), health-check, migrate, validate"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"