#!/bin/bash
# Jorge's Real Estate AI Platform - Health Check Script
# Validates deployment health and service availability
# Used in CI/CD pipeline and monitoring

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
HEALTH_LOG="/tmp/jorge-platform-health-$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="production"
TIMEOUT=300
MAX_RETRIES=5
RETRY_DELAY=10
VERBOSE=false
QUICK_CHECK=false
FULL_VALIDATION=false
OUTPUT_FORMAT="console"  # console, json, prometheus

# Service configuration
declare -A SERVICES
SERVICES=(
    ["jorge-api"]="http://localhost:8000"
    ["jorge-frontend"]="http://localhost:3000"
    ["redis"]="redis://localhost:6379"
    ["postgres"]="postgresql://localhost:5432"
)

declare -A API_ENDPOINTS
API_ENDPOINTS=(
    ["/health"]="System health status"
    ["/api/jorge-seller/health"]="Jorge Seller Bot health"
    ["/api/lead-bot/health"]="Lead Bot health"
    ["/api/intent-decoder/health"]="Intent Decoder health"
    ["/api/v1/ml/health"]="ML Analytics Engine health"
    ["/api/webhooks/ghl/health"]="GHL Integration health"
)

declare -A CRITICAL_ENDPOINTS
CRITICAL_ENDPOINTS=(
    ["/api/jorge-seller/quick-qualify"]="Jorge qualification endpoint"
    ["/api/lead-bot/process-lead"]="Lead processing endpoint"
    ["/api/intent-decoder/analyze"]="Intent analysis endpoint"
    ["/api/v1/ml/score-lead"]="ML scoring endpoint"
)

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$HEALTH_LOG"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$HEALTH_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$HEALTH_LOG"
            ;;
        "DEBUG")
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$HEALTH_LOG"
            fi
            ;;
        *)
            echo "$timestamp - $message" | tee -a "$HEALTH_LOG"
            ;;
    esac
}

# Help function
show_help() {
    cat << EOF
Jorge Platform Health Check Script

Usage: $0 [OPTIONS]

Options:
    --environment ENV       Environment to check (staging|production) [default: production]
    --timeout SECONDS       Overall timeout in seconds [default: 300]
    --max-retries COUNT     Maximum retries per check [default: 5]
    --retry-delay SECONDS   Delay between retries [default: 10]
    --quick                 Quick health check (basic endpoints only)
    --full                  Full validation including performance tests
    --verbose               Verbose output with debug information
    --output FORMAT         Output format (console|json|prometheus) [default: console]
    --help                  Show this help message

Examples:
    # Quick production health check
    $0 --quick --environment production

    # Full validation with verbose output
    $0 --full --verbose --environment staging

    # Health check for monitoring (JSON output)
    $0 --output json --timeout 60

Environment Variables:
    JORGE_API_BASE_URL      Base URL for API endpoints [default: http://localhost:8000]
    JORGE_FRONTEND_URL      Frontend URL [default: http://localhost:3000]
    HEALTH_CHECK_TOKEN      Optional token for authenticated endpoints

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --max-retries)
                MAX_RETRIES="$2"
                shift 2
                ;;
            --retry-delay)
                RETRY_DELAY="$2"
                shift 2
                ;;
            --quick)
                QUICK_CHECK=true
                shift
                ;;
            --full)
                FULL_VALIDATION=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --output)
                OUTPUT_FORMAT="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Initialize environment-specific URLs
init_environment() {
    case $ENVIRONMENT in
        "staging")
            SERVICES["jorge-api"]="http://localhost:8000"
            SERVICES["jorge-frontend"]="http://localhost:3000"
            ;;
        "production")
            SERVICES["jorge-api"]="${JORGE_API_BASE_URL:-https://api.jorge-platform.com}"
            SERVICES["jorge-frontend"]="${JORGE_FRONTEND_URL:-https://jorge-platform.com}"
            SERVICES["redis"]="redis://localhost:6379"
            SERVICES["postgres"]="postgresql://localhost:5432"
            ;;
        *)
            log "ERROR" "Invalid environment: $ENVIRONMENT"
            exit 1
            ;;
    esac

    log "INFO" "Initialized environment: $ENVIRONMENT"
    log "DEBUG" "API Base URL: ${SERVICES["jorge-api"]}"
    log "DEBUG" "Frontend URL: ${SERVICES["jorge-frontend"]}"
}

# HTTP request with retry logic
http_request() {
    local url=$1
    local expected_status=${2:-200}
    local method=${3:-GET}
    local timeout=${4:-30}
    local retry=0

    while [[ $retry -lt $MAX_RETRIES ]]; do
        log "DEBUG" "HTTP $method request to $url (attempt $((retry + 1))/$MAX_RETRIES)"

        local response_code
        local response_time
        local start_time=$(date +%s.%N)

        if response_code=$(curl -s -o /dev/null -w "%{http_code}" \
                               -X "$method" \
                               -m "$timeout" \
                               --connect-timeout 10 \
                               "$url"); then

            local end_time=$(date +%s.%N)
            response_time=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0")

            if [[ "$response_code" == "$expected_status" ]]; then
                log "DEBUG" "HTTP $method $url: $response_code (${response_time}s)"
                return 0
            else
                log "WARN" "HTTP $method $url: Expected $expected_status, got $response_code"
            fi
        else
            log "WARN" "HTTP $method $url: Request failed"
        fi

        ((retry++))
        if [[ $retry -lt $MAX_RETRIES ]]; then
            log "DEBUG" "Retrying in ${RETRY_DELAY}s..."
            sleep "$RETRY_DELAY"
        fi
    done

    log "ERROR" "HTTP $method $url: Failed after $MAX_RETRIES attempts"
    return 1
}

# Check service container status
check_containers() {
    log "INFO" "Checking Docker container status..."

    local containers=("jorge-api" "jorge-worker" "redis" "postgres")
    local failed_containers=()

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            local uptime=$(docker ps --filter "name=$container" --format "{{.Status}}")
            log "INFO" "Container $container: Running ($uptime)"
        else
            log "ERROR" "Container $container: Not running or not found"
            failed_containers+=("$container")
        fi
    done

    if [[ ${#failed_containers[@]} -gt 0 ]]; then
        log "ERROR" "Failed containers: ${failed_containers[*]}"
        return 1
    fi

    log "INFO" "All containers are running"
    return 0
}

# Check basic API health endpoints
check_health_endpoints() {
    log "INFO" "Checking health endpoints..."

    local api_base="${SERVICES["jorge-api"]}"
    local failed_endpoints=()

    for endpoint in "${!API_ENDPOINTS[@]}"; do
        local description="${API_ENDPOINTS[$endpoint]}"
        local url="${api_base}${endpoint}"

        log "DEBUG" "Checking $description at $url"

        if http_request "$url" 200 GET 30; then
            log "INFO" "✅ $description: Healthy"
        else
            log "ERROR" "❌ $description: Unhealthy"
            failed_endpoints+=("$endpoint")
        fi
    done

    if [[ ${#failed_endpoints[@]} -gt 0 ]]; then
        log "ERROR" "Failed health endpoints: ${failed_endpoints[*]}"
        return 1
    fi

    log "INFO" "All health endpoints are responding"
    return 0
}

# Check critical business endpoints
check_critical_endpoints() {
    log "INFO" "Checking critical business endpoints..."

    local api_base="${SERVICES["jorge-api"]}"
    local failed_endpoints=()

    for endpoint in "${!CRITICAL_ENDPOINTS[@]}"; do
        local description="${CRITICAL_ENDPOINTS[$endpoint]}"
        local url="${api_base}${endpoint}"

        log "DEBUG" "Checking $description at $url"

        # Use HEAD request for critical endpoints to avoid side effects
        if http_request "$url" 200 HEAD 30; then
            log "INFO" "✅ $description: Available"
        else
            log "ERROR" "❌ $description: Unavailable"
            failed_endpoints+=("$endpoint")
        fi
    done

    if [[ ${#failed_endpoints[@]} -gt 0 ]]; then
        log "ERROR" "Failed critical endpoints: ${failed_endpoints[*]}"
        return 1
    fi

    log "INFO" "All critical endpoints are available"
    return 0
}

# Check database connectivity
check_database() {
    log "INFO" "Checking database connectivity..."

    # Check PostgreSQL
    if command -v psql &> /dev/null; then
        if psql "${SERVICES["postgres"]}/jorge_db" -c "SELECT 1" &> /dev/null; then
            log "INFO" "✅ PostgreSQL: Connected"
        else
            log "ERROR" "❌ PostgreSQL: Connection failed"
            return 1
        fi
    else
        log "WARN" "psql not available, skipping direct database check"
    fi

    # Check Redis
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            log "INFO" "✅ Redis: Connected"
        else
            log "ERROR" "❌ Redis: Connection failed"
            return 1
        fi
    else
        log "WARN" "redis-cli not available, skipping direct Redis check"
    fi

    return 0
}

# Check frontend application
check_frontend() {
    log "INFO" "Checking frontend application..."

    local frontend_url="${SERVICES["jorge-frontend"]}"

    # Check if frontend is accessible
    if http_request "$frontend_url" 200 GET 30; then
        log "INFO" "✅ Frontend: Accessible"
    else
        log "ERROR" "❌ Frontend: Not accessible"
        return 1
    fi

    # Check key frontend pages
    local pages=("/health" "/dashboard" "/jorge-chat")

    for page in "${pages[@]}"; do
        local url="${frontend_url}${page}"
        if http_request "$url" 200 GET 30; then
            log "INFO" "✅ Frontend page $page: Available"
        else
            log "WARN" "⚠️ Frontend page $page: May not be available"
        fi
    done

    return 0
}

# Performance testing (for full validation)
run_performance_tests() {
    log "INFO" "Running performance tests..."

    local api_base="${SERVICES["jorge-api"]}"

    # Test response times
    local endpoints=("/health" "/api/jorge-seller/health" "/api/v1/ml/health")
    local slow_endpoints=()

    for endpoint in "${endpoints[@]}"; do
        local url="${api_base}${endpoint}"
        local start_time=$(date +%s.%N)

        if http_request "$url" 200 GET 5; then
            local end_time=$(date +%s.%N)
            local response_time=$(echo "scale=3; $end_time - $start_time" | bc -l 2>/dev/null || echo "0")
            local response_time_ms=$(echo "scale=0; $response_time * 1000" | bc -l 2>/dev/null || echo "0")

            if (( $(echo "$response_time > 2.0" | bc -l 2>/dev/null || echo "0") )); then
                log "WARN" "⚠️ $endpoint: Slow response (${response_time_ms}ms)"
                slow_endpoints+=("$endpoint")
            else
                log "INFO" "✅ $endpoint: Good response time (${response_time_ms}ms)"
            fi
        else
            log "ERROR" "❌ $endpoint: Performance test failed"
            return 1
        fi
    done

    if [[ ${#slow_endpoints[@]} -gt 0 ]]; then
        log "WARN" "Slow endpoints detected: ${slow_endpoints[*]}"
    fi

    # Test concurrent requests
    log "INFO" "Testing concurrent request handling..."
    local health_url="${api_base}/health"

    # Run 5 concurrent requests
    for i in {1..5}; do
        http_request "$health_url" 200 GET 10 &
    done

    wait

    log "INFO" "Concurrent request test completed"
    return 0
}

# Check bot-specific functionality
check_bot_health() {
    log "INFO" "Checking Jorge bot ecosystem health..."

    local api_base="${SERVICES["jorge-api"]}"

    # Jorge Seller Bot health
    local jorge_health_url="${api_base}/api/jorge-seller/health"
    if http_request "$jorge_health_url" 200 GET 30; then
        log "INFO" "✅ Jorge Seller Bot: Healthy"

        # Check bot configuration
        local config_url="${api_base}/api/jorge-seller/config"
        if http_request "$config_url" 200 GET 10; then
            log "INFO" "✅ Jorge Seller Bot: Configuration accessible"
        else
            log "WARN" "⚠️ Jorge Seller Bot: Configuration check failed"
        fi
    else
        log "ERROR" "❌ Jorge Seller Bot: Health check failed"
        return 1
    fi

    # Lead Bot health
    local lead_bot_url="${api_base}/api/lead-bot/health"
    if http_request "$lead_bot_url" 200 GET 30; then
        log "INFO" "✅ Lead Bot: Healthy"
    else
        log "ERROR" "❌ Lead Bot: Health check failed"
        return 1
    fi

    # Intent Decoder health
    local intent_url="${api_base}/api/intent-decoder/health"
    if http_request "$intent_url" 200 GET 30; then
        log "INFO" "✅ Intent Decoder: Healthy"
    else
        log "ERROR" "❌ Intent Decoder: Health check failed"
        return 1
    fi

    # ML Analytics Engine health
    local ml_url="${api_base}/api/v1/ml/health"
    if http_request "$ml_url" 200 GET 30; then
        log "INFO" "✅ ML Analytics Engine: Healthy"
    else
        log "ERROR" "❌ ML Analytics Engine: Health check failed"
        return 1
    fi

    log "INFO" "All Jorge bots are healthy"
    return 0
}

# Generate output in different formats
generate_output() {
    local overall_status=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $OUTPUT_FORMAT in
        "json")
            cat << EOF
{
  "timestamp": "$timestamp",
  "environment": "$ENVIRONMENT",
  "overall_status": "$overall_status",
  "checks": {
    "containers": $([[ $CONTAINER_STATUS == "0" ]] && echo "true" || echo "false"),
    "health_endpoints": $([[ $HEALTH_ENDPOINTS_STATUS == "0" ]] && echo "true" || echo "false"),
    "critical_endpoints": $([[ $CRITICAL_ENDPOINTS_STATUS == "0" ]] && echo "true" || echo "false"),
    "database": $([[ $DATABASE_STATUS == "0" ]] && echo "true" || echo "false"),
    "frontend": $([[ $FRONTEND_STATUS == "0" ]] && echo "true" || echo "false"),
    "bots": $([[ $BOT_STATUS == "0" ]] && echo "true" || echo "false")
  },
  "services": {
    "api": "${SERVICES["jorge-api"]}",
    "frontend": "${SERVICES["jorge-frontend"]}"
  }
}
EOF
            ;;
        "prometheus")
            echo "# HELP jorge_platform_health_status Jorge Platform overall health status"
            echo "# TYPE jorge_platform_health_status gauge"
            echo "jorge_platform_health_status{environment=\"$ENVIRONMENT\"} $([[ $overall_status == "healthy" ]] && echo "1" || echo "0")"
            echo ""
            echo "# HELP jorge_platform_service_status Individual service status"
            echo "# TYPE jorge_platform_service_status gauge"
            echo "jorge_platform_service_status{service=\"containers\",environment=\"$ENVIRONMENT\"} $([[ $CONTAINER_STATUS == "0" ]] && echo "1" || echo "0")"
            echo "jorge_platform_service_status{service=\"api\",environment=\"$ENVIRONMENT\"} $([[ $HEALTH_ENDPOINTS_STATUS == "0" ]] && echo "1" || echo "0")"
            echo "jorge_platform_service_status{service=\"database\",environment=\"$ENVIRONMENT\"} $([[ $DATABASE_STATUS == "0" ]] && echo "1" || echo "0")"
            echo "jorge_platform_service_status{service=\"frontend\",environment=\"$ENVIRONMENT\"} $([[ $FRONTEND_STATUS == "0" ]] && echo "1" || echo "0")"
            echo "jorge_platform_service_status{service=\"bots\",environment=\"$ENVIRONMENT\"} $([[ $BOT_STATUS == "0" ]] && echo "1" || echo "0")"
            ;;
        "console")
            echo ""
            echo "==============================================="
            echo "🏠 JORGE PLATFORM HEALTH CHECK SUMMARY"
            echo "==============================================="
            echo "Environment: $ENVIRONMENT"
            echo "Timestamp: $timestamp"
            echo "Overall Status: $([[ $overall_status == "healthy" ]] && echo "✅ HEALTHY" || echo "❌ UNHEALTHY")"
            echo ""
            echo "Service Status:"
            echo "  Containers: $([[ $CONTAINER_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo "  API Health: $([[ $HEALTH_ENDPOINTS_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo "  Critical APIs: $([[ $CRITICAL_ENDPOINTS_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo "  Database: $([[ $DATABASE_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo "  Frontend: $([[ $FRONTEND_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo "  Jorge Bots: $([[ $BOT_STATUS == "0" ]] && echo "✅ OK" || echo "❌ FAILED")"
            echo ""
            echo "Logs: $HEALTH_LOG"
            echo "==============================================="
            ;;
    esac
}

# Main health check function
main() {
    local start_time=$(date +%s)
    local overall_status="healthy"

    log "INFO" "Starting Jorge Platform health check"
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Timeout: ${TIMEOUT}s"
    log "INFO" "Output format: $OUTPUT_FORMAT"

    parse_args "$@"
    init_environment

    # Initialize status variables
    CONTAINER_STATUS=0
    HEALTH_ENDPOINTS_STATUS=0
    CRITICAL_ENDPOINTS_STATUS=0
    DATABASE_STATUS=0
    FRONTEND_STATUS=0
    BOT_STATUS=0

    # Run health checks based on mode
    if [[ "$QUICK_CHECK" == "true" ]]; then
        log "INFO" "Running quick health check..."

        check_health_endpoints || HEALTH_ENDPOINTS_STATUS=1
        check_bot_health || BOT_STATUS=1

    elif [[ "$FULL_VALIDATION" == "true" ]]; then
        log "INFO" "Running full validation..."

        check_containers || CONTAINER_STATUS=1
        check_health_endpoints || HEALTH_ENDPOINTS_STATUS=1
        check_critical_endpoints || CRITICAL_ENDPOINTS_STATUS=1
        check_database || DATABASE_STATUS=1
        check_frontend || FRONTEND_STATUS=1
        check_bot_health || BOT_STATUS=1
        run_performance_tests || log "WARN" "Performance tests had issues"

    else
        log "INFO" "Running standard health check..."

        check_containers || CONTAINER_STATUS=1
        check_health_endpoints || HEALTH_ENDPOINTS_STATUS=1
        check_critical_endpoints || CRITICAL_ENDPOINTS_STATUS=1
        check_database || DATABASE_STATUS=1
        check_frontend || FRONTEND_STATUS=1
        check_bot_health || BOT_STATUS=1
    fi

    # Determine overall status
    if [[ $CONTAINER_STATUS -ne 0 ]] || \
       [[ $HEALTH_ENDPOINTS_STATUS -ne 0 ]] || \
       [[ $CRITICAL_ENDPOINTS_STATUS -ne 0 ]] || \
       [[ $DATABASE_STATUS -ne 0 ]] || \
       [[ $FRONTEND_STATUS -ne 0 ]] || \
       [[ $BOT_STATUS -ne 0 ]]; then
        overall_status="unhealthy"
    fi

    # Calculate execution time
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))

    log "INFO" "Health check completed in ${execution_time}s"

    # Generate output
    generate_output "$overall_status"

    # Exit with appropriate code
    if [[ "$overall_status" == "healthy" ]]; then
        log "INFO" "🎉 Jorge Platform is healthy and ready to serve customers!"
        exit 0
    else
        log "ERROR" "🚨 Jorge Platform has health issues that need attention"
        exit 1
    fi
}

# Run main function with all arguments
main "$@"