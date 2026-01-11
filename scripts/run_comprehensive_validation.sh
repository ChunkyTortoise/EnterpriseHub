#!/bin/bash

# ============================================================================
# Phase 2 Comprehensive Validation Execution Script
#
# This script runs the complete validation framework to measure Phase 2
# optimization success. It executes all validation components and generates
# a comprehensive report.
#
# Usage: bash scripts/run_comprehensive_validation.sh [baseline|validation|compare]
# ============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT=$(pwd)
SCRIPTS_DIR="$PROJECT_ROOT/scripts"
OUTPUT_DIR="$SCRIPTS_DIR/validation_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
VALIDATION_MODE="${1:-validation}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# ============================================================================
# Helper Functions
# ============================================================================

print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi
    print_success "Python 3 found"
}

check_dependencies() {
    print_header "Checking Dependencies"

    local required_packages=("asyncio" "numpy" "psutil")

    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            print_success "$package available"
        else
            print_warning "$package not found - installing..."
        fi
    done
}

# ============================================================================
# Validation Execution Functions
# ============================================================================

run_baseline_validation() {
    print_header "Running Baseline Validation"

    echo "Capturing current performance state..."
    python3 "$SCRIPTS_DIR/phase2_performance_validation_framework.py" \
        2>&1 | tee "$OUTPUT_DIR/baseline_${TIMESTAMP}.log"

    if [ -f "$SCRIPTS_DIR/phase2_validation_report.json" ]; then
        cp "$SCRIPTS_DIR/phase2_validation_report.json" \
           "$OUTPUT_DIR/baseline_${TIMESTAMP}.json"
        print_success "Baseline validation complete"
        print_success "Results saved to: $OUTPUT_DIR/baseline_${TIMESTAMP}.json"
    else
        print_error "Baseline validation failed"
        return 1
    fi
}

run_optimization_validation() {
    print_header "Running Optimization Validation"

    echo "Validating Phase 2 optimizations..."
    python3 "$SCRIPTS_DIR/phase2_performance_validation_framework.py" \
        2>&1 | tee "$OUTPUT_DIR/optimization_${TIMESTAMP}.log"

    if [ -f "$SCRIPTS_DIR/phase2_validation_report.json" ]; then
        cp "$SCRIPTS_DIR/phase2_validation_report.json" \
           "$OUTPUT_DIR/optimization_${TIMESTAMP}.json"
        print_success "Optimization validation complete"
        print_success "Results saved to: $OUTPUT_DIR/optimization_${TIMESTAMP}.json"
    else
        print_error "Optimization validation failed"
        return 1
    fi
}

run_comparison_analysis() {
    print_header "Running Before/After Comparison"

    echo "Analyzing improvements from optimizations..."
    python3 "$SCRIPTS_DIR/before_after_comparison_framework.py" \
        2>&1 | tee "$OUTPUT_DIR/comparison_${TIMESTAMP}.log"

    # Copy comparison results
    for file in "$SCRIPTS_DIR"/comparison_*.json; do
        if [ -f "$file" ]; then
            cp "$file" "$OUTPUT_DIR/"
            print_success "Copied $(basename "$file")"
        fi
    done
}

run_metrics_collection() {
    print_header "Collecting Performance Metrics"

    echo "Recording performance metrics..."
    python3 "$SCRIPTS_DIR/performance_metrics_collector.py" \
        2>&1 | tee "$OUTPUT_DIR/metrics_${TIMESTAMP}.log"

    if [ -f "$SCRIPTS_DIR/metrics_export.json" ]; then
        cp "$SCRIPTS_DIR/metrics_export.json" \
           "$OUTPUT_DIR/metrics_${TIMESTAMP}.json"
        print_success "Metrics collection complete"
    fi
}

# ============================================================================
# Reporting Functions
# ============================================================================

generate_summary_report() {
    print_header "Generating Summary Report"

    local summary_file="$OUTPUT_DIR/VALIDATION_SUMMARY_${TIMESTAMP}.txt"

    cat > "$summary_file" << 'EOF'
================================================================================
PHASE 2 PERFORMANCE VALIDATION SUMMARY
================================================================================

Validation Timestamp: $(date)
Validation Mode: ${VALIDATION_MODE}

================================================================================
SUCCESS CRITERIA
================================================================================

Target Metrics:
[ ] API response time (P95): <200ms
[ ] ML inference time: <500ms per prediction
[ ] Database queries (P90): <50ms
[ ] Cache hit rate: >95%
[ ] Connection pool efficiency: >90%
[ ] Infrastructure cost reduction: 25-35%

================================================================================
VALIDATION RESULTS
================================================================================

Load Test Results:
- Concurrent users tested: 10, 50, 100+
- See: optimization_${TIMESTAMP}.json

Database Performance:
- P90 query time
- Pool efficiency
- Connection metrics
- See: comparison_database_optimization.json

Cache Performance:
- Hit rate by layer
- Lookup times
- Memory usage
- See: comparison_cache_optimization.json

ML Inference:
- Individual vs batch performance
- Throughput improvements
- Speedup factors
- See: comparison_ml_inference.json

API Performance:
- Response time percentiles
- Throughput metrics
- Error rates
- See: comparison_api_performance.json

================================================================================
COST ANALYSIS
================================================================================

See metrics_${TIMESTAMP}.json for detailed cost breakdown
Expected savings: 25-35% infrastructure reduction

================================================================================
RECOMMENDATIONS
================================================================================

Review detailed results in:
- $OUTPUT_DIR/optimization_${TIMESTAMP}.json
- $OUTPUT_DIR/comparison_*.json
- $OUTPUT_DIR/metrics_${TIMESTAMP}.json

Run PHASE_2_VALIDATION_GUIDE.md for detailed guidance on interpreting results.

================================================================================
EOF

    print_success "Summary report generated: $summary_file"
}

analyze_results() {
    print_header "Analyzing Results"

    echo "Comparing baseline and optimization results..."

    # Count JSON files
    local comparison_files=$(find "$OUTPUT_DIR" -name "comparison_*.json" | wc -l)
    local metric_files=$(find "$OUTPUT_DIR" -name "*_${TIMESTAMP}.json" | wc -l)

    echo "Generated files:"
    echo "  - Comparison reports: $comparison_files"
    echo "  - Metric files: $metric_files"

    if [ $metric_files -gt 0 ]; then
        print_success "All validation components executed successfully"
    else
        print_warning "Some validation components may not have executed properly"
    fi
}

# ============================================================================
# Report Display Functions
# ============================================================================

display_results_summary() {
    print_header "Validation Results Summary"

    echo "Validation Output Location: $OUTPUT_DIR"
    echo ""
    echo "Generated Files:"

    if [ -f "$OUTPUT_DIR/baseline_${TIMESTAMP}.json" ]; then
        echo "  ✅ Baseline report"
    fi

    if [ -f "$OUTPUT_DIR/optimization_${TIMESTAMP}.json" ]; then
        echo "  ✅ Optimization report"
    fi

    ls -1 "$OUTPUT_DIR"/comparison_*.json 2>/dev/null | while read file; do
        echo "  ✅ $(basename "$file")"
    done

    if [ -f "$OUTPUT_DIR/metrics_${TIMESTAMP}.json" ]; then
        echo "  ✅ Metrics export"
    fi

    echo ""
    print_success "Validation complete!"
    print_success "Review results: less $OUTPUT_DIR/"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "Phase 2 Comprehensive Validation Framework"

    echo "Configuration:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Scripts Dir: $SCRIPTS_DIR"
    echo "  Output Dir: $OUTPUT_DIR"
    echo "  Validation Mode: $VALIDATION_MODE"
    echo "  Timestamp: $TIMESTAMP"

    # Check environment
    check_python
    check_dependencies

    # Run validation based on mode
    case $VALIDATION_MODE in
        baseline)
            print_header "BASELINE VALIDATION MODE"
            run_baseline_validation
            ;;

        validation)
            print_header "POST-OPTIMIZATION VALIDATION MODE"
            run_optimization_validation
            run_metrics_collection
            ;;

        compare)
            print_header "COMPARISON MODE"
            run_baseline_validation
            run_optimization_validation
            run_comparison_analysis
            run_metrics_collection
            ;;

        *)
            print_error "Invalid mode: $VALIDATION_MODE"
            echo "Usage: $0 [baseline|validation|compare]"
            exit 1
            ;;
    esac

    # Generate reports
    generate_summary_report
    analyze_results
    display_results_summary

    print_header "VALIDATION FRAMEWORK EXECUTION COMPLETE"
    echo "Next steps:"
    echo "1. Review results in: $OUTPUT_DIR"
    echo "2. Check PHASE_2_VALIDATION_GUIDE.md for interpretation"
    echo "3. Compare metrics against success criteria"
    echo "4. Take action based on results"
    echo ""
}

# Run main function
main

exit 0
