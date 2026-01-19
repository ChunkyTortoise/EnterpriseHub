#!/bin/bash
# Jorge's Revenue Platform - Smoke Tests
# Quick validation tests for post-deployment health verification
# Version: 1.0.0

set -euo pipefail

ENVIRONMENT="${1:-staging}"
FAILURES=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Set API URL based on environment
if [[ "$ENVIRONMENT" == "production" ]]; then
    API_URL="https://api.jorge-revenue.example.com"
else
    API_URL="https://staging-api.jorge-revenue.example.com"
fi

echo -e "${YELLOW}Running smoke tests against: $API_URL${NC}\n"

# Test function
test_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_status=${3:-200}
    local method=${4:-GET}

    echo -n "Testing $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$API_URL$endpoint" || echo "000")

    if [[ "$response" == "$expected_status" ]]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $response)"
        FAILURES=$((FAILURES + 1))
    fi
}

# Health Checks
echo "=== Health Checks ==="
test_endpoint "Startup Health" "/health/startup" 200
test_endpoint "Liveness Health" "/health/live" 200
test_endpoint "Readiness Health" "/health/ready" 200
echo

# API Endpoints (without authentication)
echo "=== Public API Endpoints ==="
test_endpoint "API Root" "/" 200
test_endpoint "OpenAPI Docs" "/docs" 200
test_endpoint "OpenAPI Schema" "/openapi.json" 200
echo

# Pricing Endpoints (requires auth - should return 401)
echo "=== Protected Endpoints (Auth Check) ==="
test_endpoint "Pricing Endpoint Auth" "/api/pricing/calculate" 401 POST
test_endpoint "ROI Endpoint Auth" "/api/pricing/roi-report" 401 POST
test_endpoint "Analytics Endpoint Auth" "/api/analytics/usage" 401 GET
echo

# Performance Metrics
echo "=== Performance Checks ==="

# Check response time
echo -n "Checking response time... "
response_time=$(curl -s -o /dev/null -w "%{time_total}" "$API_URL/health/live")
response_time_ms=$(echo "$response_time * 1000" | bc)

if (( $(echo "$response_time < 1.0" | bc -l) )); then
    echo -e "${GREEN}✓ PASS${NC} (${response_time_ms}ms)"
else
    echo -e "${RED}✗ FAIL${NC} (${response_time_ms}ms > 1000ms)"
    FAILURES=$((FAILURES + 1))
fi

# Summary
echo
echo "========================================"
if [[ $FAILURES -eq 0 ]]; then
    echo -e "${GREEN}All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES smoke test(s) failed!${NC}"
    exit 1
fi
