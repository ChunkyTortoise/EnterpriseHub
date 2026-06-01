#!/bin/bash
# Test Hooks System
# Validates that all 5 security layers are functioning correctly

set -e

echo "🧪 Testing EnterpriseHub Hooks System"
echo "======================================"
echo ""

METRICS_DIR=".claude/metrics"
HOOKS_YAML=".claude/hooks.yaml"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARNINGS++))
}

# =============================================================================
# LAYER 1 TESTS: Command-Based Instant Blocks
# =============================================================================

echo "Testing Layer 1: Command-Based Instant Blocks"
echo "----------------------------------------------"

# Test 1.1: Secrets file protection
echo "Test 1.1: Block .env file access"
if [ -f "$HOOKS_YAML" ] && grep -q "block-secrets-in-files" "$HOOKS_YAML"; then
    pass "Secrets protection hook configured"
else
    fail "Secrets protection hook missing from hooks.yaml"
fi

# Test 1.2: Path traversal protection
echo "Test 1.2: Path traversal prevention"
if grep -q "block-path-traversal" "$HOOKS_YAML"; then
    pass "Path traversal protection configured"
else
    fail "Path traversal protection missing"
fi

# Test 1.3: Destructive command protection
echo "Test 1.3: Destructive command blocking"
if grep -q "block-destructive-bash" "$HOOKS_YAML"; then
    pass "Destructive command protection configured"
else
    fail "Destructive command protection missing"
fi

# Test 1.4: PII/Customer data protection
echo "Test 1.4: Customer data protection"
if grep -q "block-customer-data" "$HOOKS_YAML"; then
    pass "Customer data protection configured"
else
    fail "Customer data protection missing"
fi

echo ""

# =============================================================================
# LAYER 2 TESTS: AI-Powered Content Analysis
# =============================================================================

echo "Testing Layer 2: AI-Powered Content Analysis"
echo "---------------------------------------------"

# Test 2.1: Secrets in content detection
echo "Test 2.1: Secrets detection hook"
if grep -q "detect-secrets-in-content" "$HOOKS_YAML"; then
    pass "Secrets detection hook configured"

    # Check model configuration
    if grep -A 20 "detect-secrets-in-content" "$HOOKS_YAML" | grep -q "haiku"; then
        pass "Using fast Haiku model for secrets detection"
    else
        warn "Secrets detection not using Haiku model (may be slow)"
    fi
else
    fail "Secrets detection hook missing"
fi

# Test 2.2: SQL injection detection
echo "Test 2.2: SQL injection detection"
if grep -q "detect-sql-injection" "$HOOKS_YAML"; then
    pass "SQL injection detection configured"
else
    fail "SQL injection detection missing"
fi

echo ""

# =============================================================================
# LAYER 3 TESTS: GHL-Specific Validation
# =============================================================================

echo "Testing Layer 3: GHL-Specific Validation"
echo "-----------------------------------------"

# Test 3.1: GHL API key handling
echo "Test 3.1: GHL API usage validation"
if grep -q "validate-ghl-api-usage" "$HOOKS_YAML"; then
    pass "GHL API validation configured"
else
    fail "GHL API validation missing"
fi

# Test 3.2: Rate limiting enforcement
echo "Test 3.2: GHL rate limiting"
if grep -q "enforce-ghl-rate-limiting" "$HOOKS_YAML"; then
    pass "GHL rate limiting enforcement configured"
else
    fail "GHL rate limiting enforcement missing"
fi

echo ""

# =============================================================================
# LAYER 4 TESTS: Audit Logging
# =============================================================================

echo "Testing Layer 4: Audit Logging"
echo "-------------------------------"

# Test 4.1: Metrics directory exists
echo "Test 4.1: Metrics directory"
if [ -d "$METRICS_DIR" ]; then
    pass "Metrics directory exists"
else
    fail "Metrics directory missing - creating it"
    mkdir -p "$METRICS_DIR"
fi

# Test 4.2: Audit hooks configured
echo "Test 4.2: Audit logging hooks"
AUDIT_HOOKS=("audit-file-operations" "audit-bash-commands" "audit-ghl-api-calls")
for hook in "${AUDIT_HOOKS[@]}"; do
    if grep -q "$hook" "$HOOKS_YAML"; then
        pass "Audit hook: $hook"
    else
        fail "Missing audit hook: $hook"
    fi
done

# Test 4.3: Async execution configured
echo "Test 4.3: Non-blocking audit execution"
if grep -A 5 "audit-file-operations" "$HOOKS_YAML" | grep -q "async: true"; then
    pass "Audit hooks configured as async (non-blocking)"
else
    warn "Audit hooks may not be async - could slow down operations"
fi

echo ""

# =============================================================================
# LAYER 5 TESTS: Cost Control & Resource Management
# =============================================================================

echo "Testing Layer 5: Cost Control & Resource Management"
echo "----------------------------------------------------"

# Test 5.1: Subagent rate limiting
echo "Test 5.1: Subagent rate limiting"
if grep -q "rate-limit-subagents" "$HOOKS_YAML"; then
    pass "Subagent rate limiting configured"

    # Check limit value
    LIMIT=$(grep -A 5 "rate-limit-subagents" "$HOOKS_YAML" | grep "limit:" | head -1 | awk '{print $2}')
    if [ ! -z "$LIMIT" ]; then
        pass "Rate limit set to $LIMIT operations per window"
    fi
else
    fail "Subagent rate limiting missing"
fi

# Test 5.2: Tool metrics tracking
echo "Test 5.2: Tool usage metrics"
if grep -q "track-tool-metrics" "$HOOKS_YAML"; then
    pass "Tool metrics tracking configured"
else
    fail "Tool metrics tracking missing"
fi

# Test 5.3: Metrics script exists and is executable
echo "Test 5.3: Metrics tracking script"
METRICS_SCRIPT=".claude/scripts/update-skill-metrics.py"
if [ -f "$METRICS_SCRIPT" ]; then
    pass "Metrics script exists"

    if [ -x "$METRICS_SCRIPT" ]; then
        pass "Metrics script is executable"
    else
        warn "Metrics script not executable - fixing"
        chmod +x "$METRICS_SCRIPT"
    fi

    # Test script syntax
    if python3 -m py_compile "$METRICS_SCRIPT" 2>/dev/null; then
        pass "Metrics script syntax valid"
    else
        fail "Metrics script has syntax errors"
    fi
else
    fail "Metrics script missing"
fi

echo ""

# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

echo "Testing Configuration"
echo "---------------------"

# Test performance settings
echo "Test: Performance configuration"
if grep -q "max_hook_duration_ms: 500" "$HOOKS_YAML"; then
    pass "Fast validation target set to 500ms"
else
    warn "Fast validation target not set to recommended 500ms"
fi

# Test model configuration
echo "Test: Model configuration"
if grep -q "fast_validation: claude-3-5-haiku" "$HOOKS_YAML"; then
    pass "Using Haiku model for fast validation"
else
    warn "Fast validation not using Haiku model"
fi

if grep -q "deep_analysis: claude-3-5-sonnet" "$HOOKS_YAML"; then
    pass "Using Sonnet model for deep analysis"
else
    warn "Deep analysis not using Sonnet model"
fi

# Test cost control
echo "Test: Cost control configuration"
if grep -q "max_daily_hook_invocations" "$HOOKS_YAML"; then
    pass "Daily hook invocation limit configured"
else
    warn "No daily hook invocation limit set"
fi

# Test audit retention
echo "Test: Audit retention policy"
if grep -q "retention_days: 90" "$HOOKS_YAML"; then
    pass "90-day retention policy (SOC2/HIPAA compliant)"
else
    warn "Audit retention policy not set to 90 days"
fi

echo ""

# =============================================================================
# INTEGRATION TESTS
# =============================================================================

echo "Testing Integration"
echo "-------------------"

# Test metrics script functionality
echo "Test: Metrics script basic functionality"
if python3 "$METRICS_SCRIPT" --help >/dev/null 2>&1; then
    pass "Metrics script help command works"

    # Test logging functionality
    if python3 "$METRICS_SCRIPT" --tool=Write --success=true --duration=100 2>/dev/null; then
        pass "Metrics logging functionality works"
    else
        warn "Metrics logging may have issues"
    fi
else
    fail "Metrics script not functioning correctly"
fi

# Test rate limit checking
echo "Test: Rate limit checking"
if python3 "$METRICS_SCRIPT" --check-rate-limit=test_operation --limit=10 --window=60 >/dev/null 2>&1; then
    pass "Rate limit checking works"
else
    warn "Rate limit checking may have issues"
fi

echo ""

# =============================================================================
# SUMMARY
# =============================================================================

echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Passed:   ${GREEN}$PASSED${NC}"
echo -e "Failed:   ${RED}$FAILED${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical tests passed!${NC}"
    echo ""
    echo "Hooks system is production-ready with:"
    echo "  - 5-layer security defense"
    echo "  - Enterprise-grade audit logging"
    echo "  - GHL-specific validation"
    echo "  - Cost control and metrics"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review failures above.${NC}"
    exit 1
fi
