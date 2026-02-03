#!/usr/bin/env bash
# =============================================================================
# Jorge Bots Deployment - End-to-End Smoke Test
# =============================================================================
# Validates core webhook flows against a running EnterpriseHub API.
#
# Usage:
#   ./scripts/smoke_test.sh [BASE_URL]
#
# Environment variables:
#   RAILWAY_URL         - Base URL (fallback if no positional arg)
#   GHL_WEBHOOK_SECRET  - HMAC-SHA256 signing secret for webhook payloads
#
# Exit codes:
#   0 - all tests passed
#   1 - one or more tests failed
# =============================================================================

set -uo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL="${1:-${RAILWAY_URL:-http://localhost:8000}}"
# Strip trailing slash
BASE_URL="${BASE_URL%/}"

WEBHOOK_SECRET="${GHL_WEBHOOK_SECRET:-}"

PASS=0
FAIL=0
SKIP=0

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
banner() {
    echo ""
    echo -e "${CYAN}${BOLD}=======================================${NC}"
    echo -e "${CYAN}${BOLD}  Jorge Bots - Deployment Smoke Test${NC}"
    echo -e "${CYAN}${BOLD}=======================================${NC}"
    echo -e "  Target : ${BOLD}${BASE_URL}${NC}"
    echo -e "  Secret : ${BOLD}${WEBHOOK_SECRET:+configured}${WEBHOOK_SECRET:-NOT SET}${NC}"
    echo -e "  Date   : $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    echo -e "${CYAN}${BOLD}=======================================${NC}"
    echo ""
}

pass() {
    echo -e "  ${GREEN}PASS${NC}  $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "  ${RED}FAIL${NC}  $1"
    FAIL=$((FAIL + 1))
}

skip() {
    echo -e "  ${YELLOW}SKIP${NC}  $1"
    SKIP=$((SKIP + 1))
}

info() {
    echo -e "  ${CYAN}INFO${NC}  $1"
}

# Compute HMAC-SHA256 hex digest of a string using the webhook secret.
# Usage: sign_payload "$payload_string"
sign_payload() {
    local payload="$1"
    printf '%s' "$payload" | openssl dgst -sha256 -hmac "$WEBHOOK_SECRET" | awk '{print $NF}'
}

# POST a JSON payload to the webhook endpoint with the correct signature.
# Usage: post_webhook "$payload_json"
# Prints: HTTP_STATUS<TAB>RESPONSE_BODY
post_webhook() {
    local payload="$1"
    local signature
    signature="$(sign_payload "$payload")"

    curl -s -w "\n%{http_code}" \
        -X POST "${BASE_URL}/api/ghl/webhook" \
        -H "Content-Type: application/json" \
        -H "X-GHL-Signature: ${signature}" \
        -d "$payload" \
        --max-time 30
}

# ---------------------------------------------------------------------------
# Connectivity check
# ---------------------------------------------------------------------------
check_server_reachable() {
    echo -e "${BOLD}[0/5] Checking server connectivity...${NC}"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${BASE_URL}/api/health/live" 2>/dev/null || echo "000")

    if [[ "$http_code" == "000" ]]; then
        echo ""
        fail "Server unreachable at ${BASE_URL}"
        echo -e "       ${RED}Could not connect. Ensure the API is running and the URL is correct.${NC}"
        echo ""
        summary
        exit 1
    fi
    info "Server responded with HTTP ${http_code}"
    echo ""
}

# ---------------------------------------------------------------------------
# Test 1: Health Endpoint
# ---------------------------------------------------------------------------
test_health() {
    echo -e "${BOLD}[1/5] Health endpoint  GET /api/health/live${NC}"

    local http_code body
    body=$(curl -s -w "\n%{http_code}" --max-time 10 "${BASE_URL}/api/health/live" 2>/dev/null)
    http_code=$(echo "$body" | tail -1)
    body=$(echo "$body" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        pass "GET /api/health/live returned 200"
    else
        fail "GET /api/health/live expected 200, got ${http_code}"
    fi

    # Optionally verify JSON contains status field
    if echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('status')" 2>/dev/null; then
        pass "Response contains 'status' field"
    else
        fail "Response missing 'status' field"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Test 2: Seller Lead Qualification (Needs Qualifying tag)
# ---------------------------------------------------------------------------
test_seller_qualification() {
    echo -e "${BOLD}[2/5] Seller qualification webhook${NC}"

    if [[ -z "$WEBHOOK_SECRET" ]]; then
        skip "GHL_WEBHOOK_SECRET not set -- cannot sign payload"
        echo ""
        return
    fi

    local payload
    payload=$(cat <<'PAYLOAD_EOF'
{
  "type": "InboundMessage",
  "contactId": "smoke-test-seller-001",
  "locationId": "smoke-test-location",
  "message": {
    "type": "SMS",
    "body": "I'm looking to sell my house in Rancho Cucamonga",
    "direction": "inbound"
  },
  "contact": {
    "contactId": "smoke-test-seller-001",
    "firstName": "Smoke",
    "lastName": "TestSeller",
    "phone": "+19095550101",
    "email": "smoke-seller@test.local",
    "tags": ["Needs Qualifying"],
    "customFields": {}
  }
}
PAYLOAD_EOF
)

    local raw_response http_code response_body
    raw_response=$(post_webhook "$payload")
    http_code=$(echo "$raw_response" | tail -1)
    response_body=$(echo "$raw_response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        pass "POST /api/ghl/webhook returned 200"
    else
        fail "POST /api/ghl/webhook expected 200, got ${http_code}"
        info "Response: ${response_body}"
        echo ""
        return
    fi

    # Verify success=true
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success') is True" 2>/dev/null; then
        pass "Response success=true"
    else
        fail "Response success is not true"
        info "Body: ${response_body}"
    fi

    # Verify non-empty message
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d.get('message',''))>0" 2>/dev/null; then
        pass "Response contains non-empty message"
    else
        fail "Response message is empty"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Test 3: Buyer Mode (Buyer-Lead tag)
# ---------------------------------------------------------------------------
test_buyer_mode() {
    echo -e "${BOLD}[3/5] Buyer mode webhook${NC}"

    if [[ -z "$WEBHOOK_SECRET" ]]; then
        skip "GHL_WEBHOOK_SECRET not set -- cannot sign payload"
        echo ""
        return
    fi

    local payload
    payload=$(cat <<'PAYLOAD_EOF'
{
  "type": "InboundMessage",
  "contactId": "smoke-test-buyer-001",
  "locationId": "smoke-test-location",
  "message": {
    "type": "SMS",
    "body": "I want to buy a 3BR house near Victoria Gardens",
    "direction": "inbound"
  },
  "contact": {
    "contactId": "smoke-test-buyer-001",
    "firstName": "Smoke",
    "lastName": "TestBuyer",
    "phone": "+19095550102",
    "email": "smoke-buyer@test.local",
    "tags": ["Buyer-Lead"],
    "customFields": {}
  }
}
PAYLOAD_EOF
)

    local raw_response http_code response_body
    raw_response=$(post_webhook "$payload")
    http_code=$(echo "$raw_response" | tail -1)
    response_body=$(echo "$raw_response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        pass "POST /api/ghl/webhook returned 200"
    else
        fail "POST /api/ghl/webhook expected 200, got ${http_code}"
        info "Response: ${response_body}"
        echo ""
        return
    fi

    # Verify success=true
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success') is True" 2>/dev/null; then
        pass "Response success=true"
    else
        fail "Response success is not true"
        info "Body: ${response_body}"
    fi

    # Verify non-empty message
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d.get('message',''))>0" 2>/dev/null; then
        pass "Response contains non-empty message"
    else
        fail "Response message is empty"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Test 4: Opt-Out Detection
# ---------------------------------------------------------------------------
test_opt_out() {
    echo -e "${BOLD}[4/5] Opt-out detection${NC}"

    if [[ -z "$WEBHOOK_SECRET" ]]; then
        skip "GHL_WEBHOOK_SECRET not set -- cannot sign payload"
        echo ""
        return
    fi

    local payload
    payload=$(cat <<'PAYLOAD_EOF'
{
  "type": "InboundMessage",
  "contactId": "smoke-test-optout-001",
  "locationId": "smoke-test-location",
  "message": {
    "type": "SMS",
    "body": "stop",
    "direction": "inbound"
  },
  "contact": {
    "contactId": "smoke-test-optout-001",
    "firstName": "Smoke",
    "lastName": "TestOptOut",
    "phone": "+19095550103",
    "email": "smoke-optout@test.local",
    "tags": ["Needs Qualifying"],
    "customFields": {}
  }
}
PAYLOAD_EOF
)

    local raw_response http_code response_body
    raw_response=$(post_webhook "$payload")
    http_code=$(echo "$raw_response" | tail -1)
    response_body=$(echo "$raw_response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        pass "POST /api/ghl/webhook returned 200"
    else
        fail "POST /api/ghl/webhook expected 200, got ${http_code}"
        info "Response: ${response_body}"
        echo ""
        return
    fi

    # Verify success=true
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success') is True" 2>/dev/null; then
        pass "Response success=true"
    else
        fail "Response success is not true"
        info "Body: ${response_body}"
    fi

    # Verify AI-Off tag is present in actions
    if echo "$response_body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
actions = d.get('actions', [])
tags = [a.get('tag','') for a in actions]
assert 'AI-Off' in tags, f'AI-Off not found in action tags: {tags}'
" 2>/dev/null; then
        pass "Actions include AI-Off tag"
    else
        fail "Actions do not include AI-Off tag"
        info "Body: ${response_body}"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Test 5: Loopback Protection (Outbound message)
# ---------------------------------------------------------------------------
test_loopback_protection() {
    echo -e "${BOLD}[5/5] Loopback protection (outbound message)${NC}"

    if [[ -z "$WEBHOOK_SECRET" ]]; then
        skip "GHL_WEBHOOK_SECRET not set -- cannot sign payload"
        echo ""
        return
    fi

    local payload
    payload=$(cat <<'PAYLOAD_EOF'
{
  "type": "OutboundMessage",
  "contactId": "smoke-test-loop-001",
  "locationId": "smoke-test-location",
  "message": {
    "type": "SMS",
    "body": "This is an outbound message from the bot",
    "direction": "outbound"
  },
  "contact": {
    "contactId": "smoke-test-loop-001",
    "firstName": "Smoke",
    "lastName": "TestLoop",
    "phone": "+19095550104",
    "email": "smoke-loop@test.local",
    "tags": ["Needs Qualifying"],
    "customFields": {}
  }
}
PAYLOAD_EOF
)

    local raw_response http_code response_body
    raw_response=$(post_webhook "$payload")
    http_code=$(echo "$raw_response" | tail -1)
    response_body=$(echo "$raw_response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        pass "POST /api/ghl/webhook returned 200"
    else
        fail "POST /api/ghl/webhook expected 200, got ${http_code}"
        info "Response: ${response_body}"
        echo ""
        return
    fi

    # Verify success=true
    if echo "$response_body" | python3 -c "import sys,json; d=json.load(sys.stdin); assert d.get('success') is True" 2>/dev/null; then
        pass "Response success=true"
    else
        fail "Response success is not true"
        info "Body: ${response_body}"
    fi

    # Verify message contains "Ignoring outbound"
    if echo "$response_body" | python3 -c "
import sys, json
d = json.load(sys.stdin)
msg = d.get('message', '')
assert 'Ignoring outbound' in msg, f'Expected \"Ignoring outbound\" in message, got: {msg}'
" 2>/dev/null; then
        pass "Response message contains 'Ignoring outbound'"
    else
        fail "Response message does not contain 'Ignoring outbound'"
        info "Body: ${response_body}"
    fi
    echo ""
}

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
summary() {
    local total=$((PASS + FAIL + SKIP))
    echo -e "${CYAN}${BOLD}---------------------------------------${NC}"
    echo -e "${CYAN}${BOLD}  Results${NC}"
    echo -e "${CYAN}${BOLD}---------------------------------------${NC}"
    echo -e "  ${GREEN}PASS${NC}: ${PASS}"
    echo -e "  ${RED}FAIL${NC}: ${FAIL}"
    echo -e "  ${YELLOW}SKIP${NC}: ${SKIP}"
    echo -e "  Total : ${total}"
    echo -e "${CYAN}${BOLD}---------------------------------------${NC}"

    if [[ "$FAIL" -gt 0 ]]; then
        echo -e "  ${RED}${BOLD}SMOKE TEST FAILED${NC}"
        echo ""
        return 1
    elif [[ "$SKIP" -gt 0 && "$PASS" -eq 0 ]]; then
        echo -e "  ${YELLOW}${BOLD}ALL TESTS SKIPPED${NC}"
        echo ""
        return 1
    else
        echo -e "  ${GREEN}${BOLD}ALL TESTS PASSED${NC}"
        echo ""
        return 0
    fi
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    banner
    check_server_reachable
    test_health
    test_seller_qualification
    test_buyer_mode
    test_opt_out
    test_loopback_protection
    summary
}

main
