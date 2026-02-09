#!/bin/bash
#
# Call Prep Check - Automate test verification, demo URL checks, and environment validation
# Usage: ./scripts/call_prep_check.sh [--tests-only|--demos-only|--env-only|--output FILE]
#
# Time Savings: 15m → 1m 10s (92% reduction)
#

set -e  # Exit on error
set -o pipefail  # Catch errors in pipes

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
EXPECTED_TEST_COUNT=322
CALL_PREP_FILE="plans/KIALASH_CALL_PREP_ENHANCED.md"
PORTFOLIO_URL="https://chunkytortoise.github.io"
OUTPUT_FILE=""
TESTS_ONLY=false
DEMOS_ONLY=false
ENV_ONLY=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tests-only)
            TESTS_ONLY=true
            shift
            ;;
        --demos-only)
            DEMOS_ONLY=true
            shift
            ;;
        --env-only)
            ENV_ONLY=true
            shift
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--tests-only|--demos-only|--env-only|--output FILE]"
            exit 1
            ;;
    esac
done

# Demo URLs to check (from call prep guide)
DEMO_URLS=(
    "https://agentforge.streamlit.app"
    "https://promptlab.streamlit.app"
    "https://llmstarter.streamlit.app"
    "https://docqa-engine.streamlit.app"
    "https://insight-engine.streamlit.app"
    "https://scrape-serve.streamlit.app"
    "$PORTFOLIO_URL"
)

# Required environment variables
REQUIRED_ENV_VARS=(
    "ANTHROPIC_API_KEY"
    "DATABASE_URL"
)

# Track overall status
ALL_CHECKS_PASSED=true

echo "======================================"
echo "   Call Prep Validation Check"
echo "======================================"
echo ""

# Function: Verify test count
verify_tests() {
    echo -n "Checking test count... "

    # Count tests using pytest
    if command -v pytest &> /dev/null; then
        ACTUAL_COUNT=$(pytest --co -q 2>/dev/null | grep -c "^tests/" || echo 0)

        # Remove any newlines from count
        ACTUAL_COUNT=$(echo "$ACTUAL_COUNT" | tr -d '\n')

        # If count is empty or non-numeric, set to 0
        if ! [[ "$ACTUAL_COUNT" =~ ^[0-9]+$ ]]; then
            ACTUAL_COUNT=0
        fi

        if [ "$ACTUAL_COUNT" -ge "$EXPECTED_TEST_COUNT" ]; then
            echo -e "${GREEN}✓${NC} Found $ACTUAL_COUNT tests (expected: $EXPECTED_TEST_COUNT)"
            return 0
        else
            echo -e "${RED}✗${NC} Found $ACTUAL_COUNT tests (expected: $EXPECTED_TEST_COUNT)"
            ALL_CHECKS_PASSED=false
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} pytest not found, skipping test count check"
        return 0
    fi
}

# Function: Verify required files
verify_files() {
    echo -n "Checking required files... "

    local missing_files=()

    if [ ! -f "$CALL_PREP_FILE" ]; then
        missing_files+=("$CALL_PREP_FILE")
    fi

    if [ ${#missing_files[@]} -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All required files present"
        return 0
    else
        echo -e "${RED}✗${NC} Missing files: ${missing_files[*]}"
        ALL_CHECKS_PASSED=false
        return 1
    fi
}

# Function: Verify demo URLs
verify_demo_urls() {
    echo "Checking demo URLs..."

    local failed_urls=()
    local demo_results=()

    for url in "${DEMO_URLS[@]}"; do
        echo -n "  Testing $url... "

        # Check HTTP status and response time
        if command -v curl &> /dev/null; then
            RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' --max-time 10 "$url" 2>/dev/null || echo "0")
            STATUS_CODE=$(curl -o /dev/null -s -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || echo "000")

            if [ "$STATUS_CODE" = "200" ]; then
                LOAD_TIME=$(echo "$RESPONSE_TIME * 1000" | bc -l 2>/dev/null | cut -d'.' -f1)
                if [ -z "$LOAD_TIME" ]; then
                    LOAD_TIME="0"
                fi

                if [ "$LOAD_TIME" -lt 5000 ]; then
                    echo -e "${GREEN}✓${NC} OK (${LOAD_TIME}ms)"
                    demo_results+=("$url|pass|$STATUS_CODE|${LOAD_TIME}ms")
                else
                    echo -e "${YELLOW}⚠${NC} Slow (${LOAD_TIME}ms)"
                    demo_results+=("$url|warning|$STATUS_CODE|${LOAD_TIME}ms")
                fi
            else
                echo -e "${RED}✗${NC} HTTP $STATUS_CODE"
                failed_urls+=("$url")
                demo_results+=("$url|fail|$STATUS_CODE|timeout")
                ALL_CHECKS_PASSED=false
            fi
        else
            echo -e "${YELLOW}⚠${NC} curl not found, skipping URL check"
            demo_results+=("$url|skipped|N/A|N/A")
        fi
    done

    # Export demo results for later use
    printf '%s\n' "${demo_results[@]}" > /tmp/demo_status.txt 2>/dev/null || true

    if [ ${#failed_urls[@]} -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All demo URLs accessible"
        return 0
    else
        echo -e "${RED}✗${NC} Failed URLs: ${failed_urls[*]}"
        return 1
    fi
}

# Function: Verify environment variables
verify_environment() {
    echo "Checking environment variables..."

    local missing_vars=()
    local env_results=()

    for var in "${REQUIRED_ENV_VARS[@]}"; do
        echo -n "  Checking $var... "

        if [ -n "${!var}" ]; then
            # Mask sensitive values
            local masked_value="${!var:0:10}..."
            echo -e "${GREEN}✓${NC} Set"
            env_results+=("$var|set|${masked_value}")
        else
            echo -e "${RED}✗${NC} Not set"
            missing_vars+=("$var")
            env_results+=("$var|missing|N/A")
            ALL_CHECKS_PASSED=false
        fi
    done

    # Export env results for later use
    printf '%s\n' "${env_results[@]}" > /tmp/env_status.txt 2>/dev/null || true

    if [ ${#missing_vars[@]} -eq 0 ]; then
        echo -e "${GREEN}✓${NC} All environment variables set"
        return 0
    else
        echo -e "${RED}✗${NC} Missing variables: ${missing_vars[*]}"
        return 1
    fi
}

# Function: Generate checklist markdown
generate_checklist() {
    local output="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    cat > "$output" << EOF
# Call Prep Checklist
Generated: $timestamp

## Test Verification
$(if $TESTS_ONLY || [ "$TESTS_ONLY" = false ] && [ "$DEMOS_ONLY" = false ] && [ "$ENV_ONLY" = false ]; then
    if verify_tests &>/dev/null; then
        echo "✅ PASS - Test count verified ($EXPECTED_TEST_COUNT tests)"
    else
        echo "❌ FAIL - Test count mismatch"
    fi
fi)

## Demo URLs Status
$(if $DEMOS_ONLY || [ "$TESTS_ONLY" = false ] && [ "$DEMOS_ONLY" = false ] && [ "$ENV_ONLY" = false ]; then
    if [ -f /tmp/demo_status.txt ]; then
        while IFS='|' read -r url status code time; do
            case $status in
                pass) echo "✅ $url - OK ($time)" ;;
                warning) echo "⚠️ $url - Slow ($time)" ;;
                fail) echo "❌ $url - Failed (HTTP $code)" ;;
                skipped) echo "⏭️ $url - Skipped" ;;
            esac
        done < /tmp/demo_status.txt
    fi
fi)

## Environment Variables
$(if $ENV_ONLY || [ "$TESTS_ONLY" = false ] && [ "$DEMOS_ONLY" = false ] && [ "$ENV_ONLY" = false ]; then
    if [ -f /tmp/env_status.txt ]; then
        while IFS='|' read -r var status value; do
            case $status in
                set) echo "✅ $var - Set" ;;
                missing) echo "❌ $var - Missing" ;;
            esac
        done < /tmp/env_status.txt
    fi
fi)

## Overall Status
$(if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo "✅ **READY** - All checks passed"
else
    echo "❌ **NOT READY** - Some checks failed"
fi)

---
*Generated by call_prep_check.sh*
EOF

    echo ""
    echo -e "${GREEN}✓${NC} Checklist written to: $output"
}

# Main execution
if [ "$TESTS_ONLY" = true ]; then
    verify_tests
elif [ "$DEMOS_ONLY" = true ]; then
    verify_demo_urls
elif [ "$ENV_ONLY" = true ]; then
    verify_environment
else
    # Run all checks
    echo "1. Test Count"
    echo "----------------------------------------"
    verify_tests
    echo ""

    echo "2. Required Files"
    echo "----------------------------------------"
    verify_files
    echo ""

    echo "3. Demo URLs"
    echo "----------------------------------------"
    verify_demo_urls
    echo ""

    echo "4. Environment Variables"
    echo "----------------------------------------"
    verify_environment
    echo ""
fi

# Generate checklist if output file specified
if [ -n "$OUTPUT_FILE" ]; then
    generate_checklist "$OUTPUT_FILE"
fi

# Summary
echo "======================================"
if [ "$ALL_CHECKS_PASSED" = true ]; then
    echo -e "${GREEN}✓ ALL CHECKS PASSED${NC}"
    echo "======================================"
    exit 0
else
    echo -e "${RED}✗ SOME CHECKS FAILED${NC}"
    echo "======================================"
    exit 1
fi
