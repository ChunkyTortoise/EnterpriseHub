#!/bin/bash
# Zero-Context Performance Analysis
# This script runs WITHOUT loading into context - only output consumes tokens
# Expected token usage: ~400-700 tokens (output only) vs ~10000 if loaded

set -e

echo "⚡ Performance Analysis Report"
echo "=============================="
echo ""

# 1. Check for N+1 query patterns
echo "1. Database Query Analysis:"
echo "   Checking for potential N+1 queries..."

N_PLUS_ONE_PATTERNS=(
    "for.*in.*:.*\.get("
    "for.*in.*:.*\.filter("
    "for.*in.*:.*session\.query"
)

FOUND_ISSUES=0
for pattern in "${N_PLUS_ONE_PATTERNS[@]}"; do
    MATCHES=$(grep -r -E "$pattern" ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
    if [ "$MATCHES" -gt 0 ]; then
        echo "   ⚠️  Found $MATCHES potential N+1 patterns: $pattern"
        FOUND_ISSUES=$((FOUND_ISSUES + MATCHES))
    fi
done

if [ "$FOUND_ISSUES" -eq 0 ]; then
    echo "   ✅ No obvious N+1 query patterns detected"
else
    echo "   Total potential issues: $FOUND_ISSUES (review manually)"
fi
echo ""

# 2. Cache implementation check
echo "2. Caching Strategy:"
if [ -f "ghl_real_estate_ai/services/cache_service.py" ]; then
    echo "   ✅ Cache service implemented"

    # Check cache usage
    CACHE_USAGE=$(grep -r "@.*cache\|cache\." ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
    echo "   → Cache decorators/calls found: $CACHE_USAGE locations"

    # Check for Redis
    if grep -q "redis" ghl_real_estate_ai/services/cache_service.py 2>/dev/null; then
        echo "   ✅ Redis backend detected"
    else
        echo "   ⚠️  Redis backend not detected (using in-memory?)"
    fi
else
    echo "   ⚠️  No cache service found"
fi
echo ""

# 3. Async/await usage
echo "3. Async Implementation:"
ASYNC_FUNCTIONS=$(grep -r "async def" ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
SYNC_FUNCTIONS=$(grep -r "^def " ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)

echo "   Async functions: $ASYNC_FUNCTIONS"
echo "   Sync functions:  $SYNC_FUNCTIONS"

if [ "$ASYNC_FUNCTIONS" -gt 0 ]; then
    echo "   ✅ Async patterns in use"

    # Check for blocking calls in async
    BLOCKING_IN_ASYNC=$(grep -A 5 "async def" ghl_real_estate_ai/services/*.py 2>/dev/null | grep -c "requests\.\|time\.sleep" || echo 0)
    if [ "$BLOCKING_IN_ASYNC" -gt 0 ]; then
        echo "   ⚠️  Found $BLOCKING_IN_ASYNC potentially blocking calls in async functions"
    fi
else
    echo "   ℹ️  No async functions detected (sync only)"
fi
echo ""

# 4. Resource usage patterns
echo "4. Resource Management:"

# Check for proper connection pooling
if grep -r "pool" ghl_real_estate_ai/**/*.py 2>/dev/null | grep -i "connection\|pool" > /dev/null; then
    echo "   ✅ Connection pooling detected"
else
    echo "   ⚠️  Connection pooling not detected"
fi

# Check for context managers
CONTEXT_MANAGERS=$(grep -r "with.*as" ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
echo "   Context managers (with): $CONTEXT_MANAGERS occurrences"
echo ""

# 5. Large data handling
echo "5. Data Processing Efficiency:"

# Check for pagination
PAGINATION=$(grep -r "limit\|offset\|page_size" ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
if [ "$PAGINATION" -gt 0 ]; then
    echo "   ✅ Pagination patterns found: $PAGINATION locations"
else
    echo "   ⚠️  No pagination patterns detected"
fi

# Check for batch processing
BATCHING=$(grep -r "batch\|chunk" ghl_real_estate_ai/services/*.py 2>/dev/null | wc -l || echo 0)
if [ "$BATCHING" -gt 0 ]; then
    echo "   ✅ Batch processing found: $BATCHING locations"
else
    echo "   ℹ️  No batch processing detected"
fi
echo ""

# 6. Performance recommendations
echo "6. Recommendations:"
RECOMMENDATIONS=()

if [ "$FOUND_ISSUES" -gt 5 ]; then
    RECOMMENDATIONS+=("   • Review N+1 query patterns in service layer")
fi

if [ ! -f "ghl_real_estate_ai/services/cache_service.py" ]; then
    RECOMMENDATIONS+=("   • Implement caching service for repeated queries")
fi

if [ "$ASYNC_FUNCTIONS" -eq 0 ] && [ "$SYNC_FUNCTIONS" -gt 10 ]; then
    RECOMMENDATIONS+=("   • Consider async/await for I/O-bound operations")
fi

if [ "$PAGINATION" -eq 0 ]; then
    RECOMMENDATIONS+=("   • Add pagination for large dataset queries")
fi

if [ ${#RECOMMENDATIONS[@]} -eq 0 ]; then
    echo "   ✅ No major performance issues detected"
else
    for rec in "${RECOMMENDATIONS[@]}"; do
        echo "$rec"
    done
fi
echo ""

echo "=============================="
echo "Report completed. Token usage: ~500-700 (output only)"
