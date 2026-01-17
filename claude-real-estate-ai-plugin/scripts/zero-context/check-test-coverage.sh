#!/bin/bash
# Zero-Context Test Coverage Analysis
# This script runs WITHOUT loading into context - only output consumes tokens
# Expected token usage: ~300-600 tokens (output only) vs ~8000 if loaded

set -e

echo "🧪 Test Coverage Analysis Report"
echo "================================="
echo ""

# Run pytest with coverage
echo "1. Generating coverage report..."
if command -v pytest &> /dev/null; then
    # Run with coverage and capture output
    COVERAGE_OUTPUT=$(pytest --cov=ghl_real_estate_ai \
                            --cov-report=term-missing \
                            --cov-report=json \
                            --tb=short \
                            -q 2>&1 || true)

    # Extract key metrics
    if [ -f coverage.json ]; then
        echo "   ✅ Coverage data generated"

        # Parse coverage.json for summary
        if command -v python3 &> /dev/null; then
            python3 - <<EOF
import json
import sys

try:
    with open('coverage.json', 'r') as f:
        data = json.load(f)

    totals = data.get('totals', {})

    print("\n2. Coverage Summary:")
    print(f"   Lines:      {totals.get('percent_covered', 0):.1f}%")
    print(f"   Statements: {totals.get('num_statements', 0)}")
    print(f"   Missing:    {totals.get('missing_lines', 0)}")
    print(f"   Branches:   {totals.get('percent_covered_display', 'N/A')}")

    # Check threshold
    coverage_pct = totals.get('percent_covered', 0)
    threshold = 80.0

    print(f"\n3. Coverage Status:")
    if coverage_pct >= threshold:
        print(f"   ✅ Coverage {coverage_pct:.1f}% meets {threshold}% threshold")
    else:
        print(f"   ❌ Coverage {coverage_pct:.1f}% below {threshold}% threshold")
        print(f"      Need {threshold - coverage_pct:.1f}% more coverage")

except Exception as e:
    print(f"   ⚠️  Error parsing coverage.json: {e}", file=sys.stderr)
    sys.exit(1)
EOF
        fi
    else
        echo "   ❌ Coverage data not generated"
    fi
else
    echo "   ❌ pytest not found - install with: pip install pytest pytest-cov"
fi
echo ""

# Find files with low coverage
echo "4. Files Needing Attention:"
if [ -f coverage.json ]; then
    python3 - <<EOF
import json

try:
    with open('coverage.json', 'r') as f:
        data = json.load(f)

    files = data.get('files', {})
    low_coverage = []

    for filepath, metrics in files.items():
        summary = metrics.get('summary', {})
        pct = summary.get('percent_covered', 0)

        if pct < 80 and 'test' not in filepath:
            low_coverage.append((filepath, pct))

    low_coverage.sort(key=lambda x: x[1])

    if low_coverage:
        for filepath, pct in low_coverage[:10]:  # Top 10
            short_path = filepath.replace('ghl_real_estate_ai/', '')
            print(f"   ⚠️  {short_path}: {pct:.1f}%")
    else:
        print("   ✅ All files meet coverage threshold")

except Exception as e:
    print(f"   Error: {e}")
EOF
fi
echo ""

# Test execution summary
echo "5. Test Execution Summary:"
echo "$COVERAGE_OUTPUT" | grep -E "(passed|failed|error|FAILED|ERROR)" | head -10 || echo "   No test results available"
echo ""

echo "================================="
echo "Report completed. Token usage: ~400-600 (output only)"
