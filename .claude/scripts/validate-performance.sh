#!/bin/bash
# CLAUDE.md Performance Validation Script v2.0.0
# Monitors optimization thresholds and provides recommendations

set -e

# Configuration
CLAUDE_FILE="CLAUDE.md"
THRESHOLD_CRITICAL=40000
THRESHOLD_WARNING=35000
THRESHOLD_OPTIMAL=15000
METRICS_DIR=".claude/metrics"

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create metrics directory if it doesn't exist
mkdir -p "$METRICS_DIR"

# Functions
log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'),$1,$2,$3,$4" >> "$METRICS_DIR/performance-history.csv"
}

check_file_size() {
    if [[ ! -f "$CLAUDE_FILE" ]]; then
        echo -e "${RED}❌ ERROR: $CLAUDE_FILE not found${NC}"
        return 1
    fi

    FILE_SIZE=$(wc -c < "$CLAUDE_FILE")
    echo "Current file size: $FILE_SIZE characters"

    # Log metric
    log_metric "$FILE_SIZE" "size_check" "automated" "$(date +%s)"

    if [[ $FILE_SIZE -gt $THRESHOLD_CRITICAL ]]; then
        echo -e "${RED}🚨 CRITICAL: File exceeds 40k threshold ($FILE_SIZE chars)${NC}"
        echo "  Action required: Extract content to reference files"
        return 2
    elif [[ $FILE_SIZE -gt $THRESHOLD_WARNING ]]; then
        echo -e "${YELLOW}⚠️  WARNING: File approaching critical threshold ($FILE_SIZE chars)${NC}"
        echo "  Recommendation: Consider optimization"
        return 1
    elif [[ $FILE_SIZE -gt $THRESHOLD_OPTIMAL ]]; then
        echo -e "${BLUE}ℹ️  INFO: File size acceptable but could be optimized ($FILE_SIZE chars)${NC}"
        return 0
    else
        echo -e "${GREEN}✅ OPTIMAL: File size within recommended range ($FILE_SIZE chars)${NC}"
        return 0
    fi
}

check_progressive_disclosure() {
    echo ""
    echo "=== Progressive Disclosure Analysis ==="

    # Count reference links
    REFERENCE_COUNT=$(grep -o "@reference/" "$CLAUDE_FILE" | wc -l || echo "0")

    # Count total sections
    SECTION_COUNT=$(grep -c "^##" "$CLAUDE_FILE" || echo "1")

    # Calculate progressive disclosure ratio
    if [[ $SECTION_COUNT -gt 0 ]]; then
        DISCLOSURE_RATIO=$(echo "scale=1; $REFERENCE_COUNT * 100 / $SECTION_COUNT" | bc -l 2>/dev/null || echo "0")
    else
        DISCLOSURE_RATIO=0
    fi

    echo "Reference links: $REFERENCE_COUNT"
    echo "Total sections: $SECTION_COUNT"
    echo "Progressive disclosure ratio: ${DISCLOSURE_RATIO}%"

    if (( $(echo "$DISCLOSURE_RATIO >= 70" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${GREEN}✅ GOOD: High progressive disclosure ratio${NC}"
    elif (( $(echo "$DISCLOSURE_RATIO >= 50" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${YELLOW}⚠️  MODERATE: Consider adding more references${NC}"
    else
        echo -e "${RED}❌ LOW: Poor progressive disclosure - extract more content${NC}"
    fi
}

validate_references() {
    echo ""
    echo "=== Reference Validation ==="

    BROKEN_COUNT=0

    while IFS= read -r ref; do
        if [[ -n "$ref" ]]; then
            file_path=".claude/${ref#@}"
            if [[ ! -f "$file_path" ]]; then
                echo -e "${RED}❌ BROKEN: $ref -> $file_path${NC}"
                BROKEN_COUNT=$((BROKEN_COUNT + 1))
            fi
        fi
    done < <(grep -o "@reference/[^)]*" "$CLAUDE_FILE" 2>/dev/null || true)

    if [[ $BROKEN_COUNT -eq 0 ]]; then
        echo -e "${GREEN}✅ All reference links are valid${NC}"
    else
        echo -e "${RED}❌ Found $BROKEN_COUNT broken references${NC}"
        return 1
    fi
}

estimate_context_usage() {
    echo ""
    echo "=== Context Usage Analysis ==="

    # Estimate tokens (rough approximation: 4 chars per token)
    ESTIMATED_TOKENS=$(($(wc -c < "$CLAUDE_FILE") / 4))

    # Context window estimation (128k tokens available)
    CONTEXT_USAGE=$(echo "scale=1; $ESTIMATED_TOKENS * 100 / 32000" | bc -l 2>/dev/null || echo "0")

    echo "Estimated tokens: $ESTIMATED_TOKENS"
    echo "Context usage: ${CONTEXT_USAGE}% (assuming 32k auto-compact threshold)"

    if (( $(echo "$CONTEXT_USAGE <= 20" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${GREEN}✅ OPTIMAL: Low context usage${NC}"
    elif (( $(echo "$CONTEXT_USAGE <= 30" | bc -l 2>/dev/null || echo "0") )); then
        echo -e "${YELLOW}⚠️  MODERATE: Consider optimization${NC}"
    else
        echo -e "${RED}❌ HIGH: Optimize to reduce context usage${NC}"
    fi
}

generate_recommendations() {
    echo ""
    echo "=== Optimization Recommendations ==="

    FILE_SIZE=$(wc -c < "$CLAUDE_FILE")

    if [[ $FILE_SIZE -gt $THRESHOLD_WARNING ]]; then
        echo "📝 Extract large sections to reference files:"

        # Find large sections
        awk '/^##/{section=$0; chars=0} {chars+=length($0)} /^##/{if(chars>1000) print "   - " section": " chars " chars"}' "$CLAUDE_FILE"

        echo ""
        echo "🔧 Suggested actions:"
        echo "   1. Move detailed examples to @reference/examples.md"
        echo "   2. Extract code patterns to @reference/patterns.md"
        echo "   3. Move troubleshooting to @reference/troubleshooting.md"
    fi

    # Check for optimization opportunities
    CODE_BLOCKS=$(grep -c '^```' "$CLAUDE_FILE" || echo "0")
    if [[ $CODE_BLOCKS -gt 10 ]]; then
        echo "   4. Consider extracting $CODE_BLOCKS code blocks to reference files"
    fi
}

# Main execution
main() {
    echo "=== CLAUDE.md Performance Validation ==="
    echo "Timestamp: $(date)"
    echo ""

    # Check if help requested
    if [[ "$1" == "--help" || "$1" == "-h" ]]; then
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --report        Generate detailed report"
        echo "  --alert         Exit with error code if thresholds exceeded"
        echo "  --metrics       Show performance metrics only"
        echo "  --help          Show this help message"
        exit 0
    fi

    EXIT_CODE=0

    # Perform checks
    check_file_size || EXIT_CODE=$?
    check_progressive_disclosure
    validate_references || EXIT_CODE=$?
    estimate_context_usage

    if [[ "$1" == "--report" ]]; then
        generate_recommendations
    fi

    if [[ "$1" == "--alert" && $EXIT_CODE -ne 0 ]]; then
        echo ""
        echo -e "${RED}🚨 Performance validation failed${NC}"
        exit $EXIT_CODE
    fi

    echo ""
    echo -e "${GREEN}✅ Performance validation complete${NC}"
    exit 0
}

# Error handling
trap 'echo -e "\n${RED}❌ Error occurred during validation${NC}"; exit 1' ERR

# Execute main function
main "$@"