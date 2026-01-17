#!/bin/bash

# Simple Verification Before Completion Script
# Compatible with older bash versions (macOS default)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_TYPE=""
COVERAGE_THRESHOLD=80
SKIP_SECURITY=false
SKIP_BUILD=false

# Gate results tracking
TOTAL_GATES=0
PASSED_GATES=0

# Help function
show_help() {
    echo "Simple Verification Before Completion"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --coverage-threshold NUM  Coverage threshold (default: 80)"
    echo "  --skip-security          Skip security scans"
    echo "  --skip-build             Skip build verification"
    echo "  -h, --help               Show this help"
    echo ""
    echo "Quality Gates:"
    echo "  1. Dependencies - Install and verify dependencies"
    echo "  2. Formatting - Code style and formatting"
    echo "  3. Linting - Code quality and best practices"
    echo "  4. Type Checking - Type safety validation"
    echo "  5. Testing - Unit and integration tests"
    echo "  6. Security - Vulnerability scanning"
    echo "  7. Build - Production build verification"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage-threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        --skip-security)
            SKIP_SECURITY=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Log function
log() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")
            echo -e "${CYAN}[${timestamp}] ℹ️  ${message}${NC}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}] ✅ ${message}${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[${timestamp}] ⚠️  ${message}${NC}"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ❌ ${message}${NC}"
            ;;
    esac
}

# Run command with error handling
run_gate() {
    local gate_name="$1"
    local command="$2"
    local description="$3"

    TOTAL_GATES=$((TOTAL_GATES + 1))
    log "INFO" "Gate ${TOTAL_GATES}: ${gate_name} - ${description}"

    local start_time=$(date +%s)

    if eval "$command" >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        PASSED_GATES=$((PASSED_GATES + 1))
        log "SUCCESS" "$gate_name passed (${duration}s)"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        log "ERROR" "$gate_name failed (${duration}s)"
        return 1
    fi
}

# Detect project type
detect_project_type() {
    log "INFO" "Detecting project type..."

    if [[ -f "package.json" ]]; then
        PROJECT_TYPE="javascript"
        log "INFO" "Detected JavaScript/TypeScript project"
    elif [[ -f "pyproject.toml" ]] || [[ -f "requirements.txt" ]] || [[ -f "setup.py" ]]; then
        PROJECT_TYPE="python"
        log "INFO" "Detected Python project"
    else
        log "ERROR" "Unable to detect project type"
        echo "Supported project types:"
        echo "  - JavaScript/TypeScript (package.json)"
        echo "  - Python (pyproject.toml, requirements.txt, setup.py)"
        exit 1
    fi
}

# JavaScript/TypeScript verification
verify_javascript() {
    log "INFO" "Starting JavaScript/TypeScript verification..."

    # Gate 1: Dependencies
    run_gate "Dependencies" "npm install" "Install dependencies"

    # Gate 2: Formatting (if prettier config exists)
    if [[ -f ".prettierrc" ]] || [[ -f ".prettierrc.json" ]]; then
        run_gate "Formatting" "npx prettier --check ." "Check code formatting"
    else
        log "WARNING" "No Prettier configuration found, skipping formatting check"
    fi

    # Gate 3: Linting (if eslint config exists)
    if [[ -f ".eslintrc.js" ]] || [[ -f ".eslintrc.json" ]]; then
        run_gate "Linting" "npx eslint src/ --max-warnings 0" "Run ESLint checks"
    else
        log "WARNING" "No ESLint configuration found, skipping linting"
    fi

    # Gate 4: Type Checking (if TypeScript)
    if [[ -f "tsconfig.json" ]]; then
        run_gate "Type_Checking" "npx tsc --noEmit" "TypeScript compilation check"
    fi

    # Gate 5: Testing
    if grep -q "test" package.json; then
        run_gate "Testing" "npm test" "Run tests"
    else
        log "WARNING" "No test script found in package.json"
    fi

    # Gate 6: Security
    if [[ $SKIP_SECURITY == false ]]; then
        run_gate "Security" "npm audit --audit-level moderate" "Security vulnerability scan"
    fi

    # Gate 7: Build
    if [[ $SKIP_BUILD == false ]] && grep -q "build" package.json; then
        run_gate "Build" "npm run build" "Production build"
    fi
}

# Python verification
verify_python() {
    log "INFO" "Starting Python verification..."

    # Gate 1: Dependencies
    if [[ -f "requirements.txt" ]]; then
        run_gate "Dependencies" "pip install -r requirements.txt" "Install requirements"
    fi

    # Gate 2: Testing
    if command -v pytest &> /dev/null; then
        run_gate "Testing" "pytest" "Run pytest tests"
    elif [[ -f "test*.py" ]] || [[ -d "tests/" ]]; then
        run_gate "Testing" "python -m unittest discover" "Run unittest tests"
    else
        log "WARNING" "No tests found"
    fi

    # Gate 3: Linting (if available)
    if command -v flake8 &> /dev/null; then
        run_gate "Linting" "flake8 --max-line-length=88 ." "Run flake8 linting"
    elif command -v pylint &> /dev/null; then
        run_gate "Linting" "pylint src/" "Run pylint checks"
    else
        log "WARNING" "No Python linter found"
    fi

    # Gate 4: Formatting (if black is available)
    if command -v black &> /dev/null; then
        run_gate "Formatting" "black --check ." "Check code formatting with Black"
    else
        log "WARNING" "Black formatter not found"
    fi

    # Gate 5: Security (if available)
    if [[ $SKIP_SECURITY == false ]]; then
        if command -v bandit &> /dev/null; then
            run_gate "Security" "bandit -r ." "Security scan with bandit"
        else
            log "WARNING" "Security scanner not available"
        fi
    fi
}

# Generate final report
generate_report() {
    local start_time="$1"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    echo "================================================"
    echo -e "${CYAN}🏁 Verification Complete${NC}"
    echo "================================================"
    echo "Project Type: $PROJECT_TYPE"
    echo "Duration: ${duration}s"
    echo "Gates Passed: $PASSED_GATES/$TOTAL_GATES"

    if [[ $TOTAL_GATES -gt 0 ]]; then
        local success_rate=$((PASSED_GATES * 100 / TOTAL_GATES))
        echo "Success Rate: $success_rate%"
    fi

    echo ""

    # Final verdict
    if [[ $PASSED_GATES -eq $TOTAL_GATES ]]; then
        echo -e "${GREEN}🎉 All quality gates passed! Code is ready for production.${NC}"
        return 0
    else
        echo -e "${RED}💥 Some quality gates failed. Please address the issues before proceeding.${NC}"
        return 1
    fi
}

# Main execution
main() {
    local start_time=$(date +%s)

    echo -e "${CYAN}🚀 Starting Verification Before Completion${NC}"
    echo -e "${CYAN}===========================================${NC}"
    echo "Coverage Threshold: $COVERAGE_THRESHOLD%"
    echo "Skip Security: $SKIP_SECURITY"
    echo "Skip Build: $SKIP_BUILD"
    echo ""

    # Detect project type and run appropriate verification
    detect_project_type

    case $PROJECT_TYPE in
        "javascript")
            verify_javascript
            ;;
        "python")
            verify_python
            ;;
        *)
            log "ERROR" "Unsupported project type: $PROJECT_TYPE"
            exit 1
            ;;
    esac

    # Generate final report
    generate_report "$start_time"
}

# Script execution
main