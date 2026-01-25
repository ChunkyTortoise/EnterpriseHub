#!/bin/bash
# ==============================================================================
# JORGE'S BI DASHBOARD - PRODUCTION HEALTH CHECK SCRIPT
# Comprehensive health validation for production deployments
# ==============================================================================

set -e

# Configuration
PORT=${PORT:-8000}
TIMEOUT=${HEALTH_CHECK_TIMEOUT:-10}
MAX_RESPONSE_TIME=${MAX_RESPONSE_TIME_MS:-1000}

# Exit codes
EXIT_SUCCESS=0
EXIT_FAILURE=1
EXIT_WARNING=2

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[HEALTH]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[HEALTH]${NC} $1"
}

log_error() {
    echo -e "${RED}[HEALTH]${NC} $1"
}

# ==============================================================================
# BASIC CONNECTIVITY CHECK
# ==============================================================================

check_basic_health() {
    log_info "Checking basic application health..."

    local start_time=$(date +%s%N)
    local response=$(curl -f -s -w "%{http_code}" "http://localhost:$PORT/health" --max-time $TIMEOUT 2>/dev/null || echo "000")
    local end_time=$(date +%s%N)

    local response_time_ms=$(( (end_time - start_time) / 1000000 ))
    local http_code="${response: -3}"
    local response_body="${response%???}"

    if [[ "$http_code" == "200" ]]; then
        log_info "Basic health check passed (${response_time_ms}ms)"

        # Check response time
        if [[ $response_time_ms -gt $MAX_RESPONSE_TIME ]]; then
            log_warn "Response time ${response_time_ms}ms exceeds threshold ${MAX_RESPONSE_TIME}ms"
            return $EXIT_WARNING
        fi

        return $EXIT_SUCCESS
    else
        log_error "Basic health check failed - HTTP $http_code"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# DATABASE CONNECTIVITY CHECK
# ==============================================================================

check_database_health() {
    log_info "Checking database connectivity..."

    local response=$(curl -f -s "http://localhost:$PORT/health/database" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$response" ]] && echo "$response" | grep -q "healthy"; then
        log_info "Database health check passed"
        return $EXIT_SUCCESS
    else
        log_error "Database health check failed"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# CACHE CONNECTIVITY CHECK
# ==============================================================================

check_cache_health() {
    log_info "Checking cache connectivity..."

    local response=$(curl -f -s "http://localhost:$PORT/health/cache" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$response" ]] && echo "$response" | grep -q "healthy"; then
        log_info "Cache health check passed"
        return $EXIT_SUCCESS
    else
        log_error "Cache health check failed"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# BI SERVICES HEALTH CHECK
# ==============================================================================

check_bi_services_health() {
    log_info "Checking BI services health..."

    local response=$(curl -f -s "http://localhost:$PORT/api/bi/health" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$response" ]] && echo "$response" | grep -q "healthy"; then
        log_info "BI services health check passed"
        return $EXIT_SUCCESS
    else
        log_error "BI services health check failed"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# WEBSOCKET CONNECTIVITY CHECK
# ==============================================================================

check_websocket_health() {
    log_info "Checking WebSocket connectivity..."

    # Test WebSocket health endpoint
    local ws_response=$(curl -f -s "http://localhost:$PORT/ws/health" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$ws_response" ]] && echo "$ws_response" | grep -q "healthy"; then
        log_info "WebSocket health check passed"
        return $EXIT_SUCCESS
    else
        log_warn "WebSocket health check failed - may not be critical"
        return $EXIT_WARNING
    fi
}

# ==============================================================================
# METRICS ENDPOINT CHECK
# ==============================================================================

check_metrics_health() {
    log_info "Checking metrics endpoint..."

    local response=$(curl -f -s "http://localhost:$PORT/metrics" --max-time $TIMEOUT 2>/dev/null | head -n 5)

    if [[ -n "$response" ]] && echo "$response" | grep -q "# HELP"; then
        log_info "Metrics endpoint is healthy"
        return $EXIT_SUCCESS
    else
        log_warn "Metrics endpoint check failed - monitoring may be degraded"
        return $EXIT_WARNING
    fi
}

# ==============================================================================
# AI SERVICES HEALTH CHECK
# ==============================================================================

check_ai_services_health() {
    log_info "Checking AI services health..."

    local response=$(curl -f -s "http://localhost:$PORT/health/ai" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$response" ]] && echo "$response" | grep -q "healthy"; then
        log_info "AI services health check passed"
        return $EXIT_SUCCESS
    else
        log_warn "AI services health check failed - may impact advanced features"
        return $EXIT_WARNING
    fi
}

# ==============================================================================
# COMPREHENSIVE HEALTH CHECK
# ==============================================================================

run_comprehensive_check() {
    local overall_status=$EXIT_SUCCESS
    local warning_count=0
    local failure_count=0

    log_info "🏥 Running comprehensive health check for Jorge's BI Dashboard"

    # Run all health checks
    local checks=(
        "check_basic_health:critical"
        "check_database_health:critical"
        "check_cache_health:critical"
        "check_bi_services_health:critical"
        "check_websocket_health:optional"
        "check_metrics_health:optional"
        "check_ai_services_health:optional"
    )

    for check_def in "${checks[@]}"; do
        local check_func="${check_def%%:*}"
        local check_type="${check_def##*:}"

        # Execute the check function
        $check_func
        local check_result=$?

        case $check_result in
            $EXIT_SUCCESS)
                # All good, continue
                ;;
            $EXIT_WARNING)
                warning_count=$((warning_count + 1))
                if [[ "$overall_status" == "$EXIT_SUCCESS" ]]; then
                    overall_status=$EXIT_WARNING
                fi
                ;;
            $EXIT_FAILURE)
                failure_count=$((failure_count + 1))
                if [[ "$check_type" == "critical" ]]; then
                    overall_status=$EXIT_FAILURE
                    log_error "Critical health check failed: $check_func"
                else
                    log_warn "Optional health check failed: $check_func"
                    if [[ "$overall_status" == "$EXIT_SUCCESS" ]]; then
                        overall_status=$EXIT_WARNING
                    fi
                fi
                ;;
        esac
    done

    # Summary
    log_info "Health check summary:"
    log_info "  Failures: $failure_count"
    log_info "  Warnings: $warning_count"

    case $overall_status in
        $EXIT_SUCCESS)
            log_info "✅ All health checks passed - service is fully operational"
            ;;
        $EXIT_WARNING)
            log_warn "⚠️  Health check passed with warnings - service is operational but degraded"
            ;;
        $EXIT_FAILURE)
            log_error "❌ Health check failed - service is not ready"
            ;;
    esac

    return $overall_status
}

# ==============================================================================
# READINESS CHECK
# ==============================================================================

check_readiness() {
    log_info "Checking service readiness..."

    local response=$(curl -f -s "http://localhost:$PORT/ready" --max-time $TIMEOUT 2>/dev/null || echo "")

    if [[ -n "$response" ]] && echo "$response" | grep -q "ready"; then
        log_info "Service readiness check passed"
        return $EXIT_SUCCESS
    else
        log_error "Service readiness check failed"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# LIVENESS CHECK
# ==============================================================================

check_liveness() {
    log_info "Checking service liveness..."

    # Simple check to see if the process is responsive
    local response=$(curl -f -s "http://localhost:$PORT/health" --max-time 5 2>/dev/null || echo "")

    if [[ -n "$response" ]]; then
        log_info "Service liveness check passed"
        return $EXIT_SUCCESS
    else
        log_error "Service liveness check failed"
        return $EXIT_FAILURE
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

main() {
    case "${1:-comprehensive}" in
        "basic")
            check_basic_health
            exit $?
            ;;
        "database")
            check_database_health
            exit $?
            ;;
        "cache")
            check_cache_health
            exit $?
            ;;
        "bi-services")
            check_bi_services_health
            exit $?
            ;;
        "websocket")
            check_websocket_health
            exit $?
            ;;
        "ai")
            check_ai_services_health
            exit $?
            ;;
        "readiness")
            check_readiness
            exit $?
            ;;
        "liveness")
            check_liveness
            exit $?
            ;;
        "comprehensive"|"")
            run_comprehensive_check
            exit $?
            ;;
        *)
            log_error "Unknown check type: $1"
            log_info "Available checks: basic, database, cache, bi-services, websocket, ai, readiness, liveness, comprehensive"
            exit $EXIT_FAILURE
            ;;
    esac
}

# Execute main function
main "$@"