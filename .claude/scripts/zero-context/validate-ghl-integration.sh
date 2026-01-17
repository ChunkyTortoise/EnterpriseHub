#!/bin/bash
# Zero-Context GHL Integration Validation
# This script runs WITHOUT loading into context - only output consumes tokens
# Expected token usage: ~200-500 tokens (output only) vs ~5000 if loaded

set -e

echo "🔍 GHL Integration Validation Report"
echo "======================================"
echo ""

# Check for required environment variables
echo "1. Environment Configuration:"
if [ -f ".env.example" ]; then
    REQUIRED_VARS=(
        "GHL_API_KEY"
        "GHL_LOCATION_ID"
        "GHL_WEBHOOK_SECRET"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env.example; then
            echo "   ✅ ${var} documented in .env.example"
        else
            echo "   ❌ ${var} MISSING from .env.example"
        fi
    done
else
    echo "   ⚠️  .env.example not found"
fi
echo ""

# Validate GHL service files exist
echo "2. Service Implementation:"
GHL_FILES=(
    "ghl_real_estate_ai/services/ghl_sync_service.py"
    "ghl_real_estate_ai/ghl_utils/config.py"
)

for file in "${GHL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file exists"
        # Check for critical patterns
        if grep -q "class.*GHL.*Service" "$file" 2>/dev/null; then
            echo "      → Service class found"
        fi
        if grep -q "async def" "$file" 2>/dev/null; then
            echo "      → Async implementation detected"
        fi
    else
        echo "   ❌ $file MISSING"
    fi
done
echo ""

# Check test coverage
echo "3. Test Coverage:"
if [ -f "tests/test_ghl_integration.py" ] || [ -f "ghl_real_estate_ai/tests/test_ghl_sync_service.py" ]; then
    echo "   ✅ GHL integration tests found"

    # Run tests if pytest available
    if command -v pytest &> /dev/null; then
        echo "   Running GHL tests..."
        pytest -v tests/test_ghl*.py ghl_real_estate_ai/tests/test_ghl*.py --tb=short 2>&1 | tail -20 || true
    fi
else
    echo "   ⚠️  No GHL integration tests found"
fi
echo ""

# Check rate limiting implementation
echo "4. Rate Limiting & Error Handling:"
if grep -r "rate.*limit" ghl_real_estate_ai/services/*ghl*.py 2>/dev/null | head -5; then
    echo "   ✅ Rate limiting logic found"
else
    echo "   ⚠️  Rate limiting not detected"
fi

if grep -r "try.*except.*GHL" ghl_real_estate_ai/services/*ghl*.py 2>/dev/null | head -3; then
    echo "   ✅ GHL-specific error handling found"
else
    echo "   ⚠️  GHL error handling not detected"
fi
echo ""

# Summary
echo "5. Integration Status:"
echo "   Documentation: $([ -f .env.example ] && echo '✅' || echo '⚠️')"
echo "   Implementation: $([ -f ghl_real_estate_ai/services/ghl_sync_service.py ] && echo '✅' || echo '❌')"
echo "   Testing: $([ -f tests/test_ghl*.py ] && echo '✅' || echo '⚠️')"
echo ""
echo "======================================"
echo "Report completed. Token usage: ~300-500 (output only)"
