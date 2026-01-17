#!/bin/bash

# Comprehensive Verification Before Completion Script
# Implements quality gates for production-ready code

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
VERBOSE=false
EXIT_ON_FIRST_FAILURE=false
RESULTS_FILE="verification-results.json"

# Gate results tracking
declare -A GATE_RESULTS
TOTAL_GATES=0
PASSED_GATES=0

# Help function
show_help() {
    echo "Comprehensive Verification Before Completion"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --coverage-threshold NUM  Coverage threshold (default: 80)"
    echo "  --skip-security          Skip security scans"
    echo "  --skip-build             Skip build verification"
    echo "  --exit-on-failure        Exit on first gate failure"
    echo "  --verbose                Verbose output"
    echo "  --results-file FILE      Save results to JSON file"
    echo "  -h, --help               Show this help"
    echo ""
    echo "Quality Gates:"
    echo "  1. Dependencies - Install and verify dependencies"
    echo "  2. Formatting - Code style and formatting"
    echo "  3. Linting - Code quality and best practices"
    echo "  4. Type Checking - Type safety validation"
    echo "  5. Testing - Unit and integration tests"
    echo "  6. Coverage - Test coverage requirements"
    echo "  7. Security - Vulnerability scanning"
    echo "  8. Build - Production build verification"
    echo "  9. Documentation - Code documentation check"
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
        --exit-on-failure)
            EXIT_ON_FIRST_FAILURE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --results-file)
            RESULTS_FILE="$2"
            shift 2
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
        "DEBUG")
            if [[ $VERBOSE == true ]]; then
                echo -e "${BLUE}[${timestamp}] 🔍 ${message}${NC}"
            fi
            ;;
    esac
}

# Run command with error handling
run_command() {
    local gate_name="$1"
    local command="$2"
    local description="$3"

    TOTAL_GATES=$((TOTAL_GATES + 1))
    log "INFO" "Gate ${TOTAL_GATES}: ${gate_name} - ${description}"

    if [[ $VERBOSE == true ]]; then
        log "DEBUG" "Running: $command"
    fi

    local start_time=$(date +%s)

    if eval "$command" >/dev/null 2>&1; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        GATE_RESULTS[$gate_name]="PASSED"
        PASSED_GATES=$((PASSED_GATES + 1))
        log "SUCCESS" "$gate_name passed (${duration}s)"
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        GATE_RESULTS[$gate_name]="FAILED"
        log "ERROR" "$gate_name failed (${duration}s)"

        if [[ $EXIT_ON_FIRST_FAILURE == true ]]; then
            log "ERROR" "Exiting due to --exit-on-failure flag"
            exit 1
        fi
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
    elif [[ -f "go.mod" ]]; then
        PROJECT_TYPE="go"
        log "INFO" "Detected Go project"
    elif [[ -f "Cargo.toml" ]]; then
        PROJECT_TYPE="rust"
        log "INFO" "Detected Rust project"
    else
        log "ERROR" "Unable to detect project type"
        echo "Supported project types:"
        echo "  - JavaScript/TypeScript (package.json)"
        echo "  - Python (pyproject.toml, requirements.txt, setup.py)"
        echo "  - Go (go.mod)"
        echo "  - Rust (Cargo.toml)"
        exit 1
    fi
}

# JavaScript/TypeScript verification
verify_javascript() {
    log "INFO" "Starting JavaScript/TypeScript verification..."

    # Gate 1: Dependencies
    if [[ -f "package-lock.json" ]]; then
        run_command "Dependencies" "npm ci" "Install dependencies from lockfile"
    elif [[ -f "yarn.lock" ]]; then
        run_command "Dependencies" "yarn install --frozen-lockfile" "Install dependencies from lockfile"
    else
        run_command "Dependencies" "npm install" "Install dependencies"
    fi

    # Gate 2: Formatting
    if [[ -f ".prettierrc" ]] || [[ -f ".prettierrc.json" ]] || [[ -f ".prettierrc.js" ]]; then
        run_command "Formatting" "npx prettier --check ." "Check code formatting"
    else
        log "WARNING" "No Prettier configuration found, skipping formatting check"
    fi

    # Gate 3: Linting
    if [[ -f ".eslintrc.js" ]] || [[ -f ".eslintrc.json" ]] || [[ -f "eslint.config.js" ]]; then
        run_command "Linting" "npx eslint src/ --max-warnings 0" "Run ESLint checks"
    else
        log "WARNING" "No ESLint configuration found, skipping linting"
    fi

    # Gate 4: Type Checking
    if [[ -f "tsconfig.json" ]]; then
        run_command "Type_Checking" "npx tsc --noEmit" "TypeScript compilation check"
    else
        log "INFO" "No TypeScript configuration found, skipping type checking"
    fi

    # Gate 5: Testing
    if [[ -f "jest.config.js" ]] || grep -q "jest" package.json; then
        run_command "Testing" "npm test -- --watchAll=false" "Run Jest tests"
    elif grep -q "vitest" package.json; then
        run_command "Testing" "npx vitest run" "Run Vitest tests"
    else
        log "WARNING" "No test framework configuration found"
    fi

    # Gate 6: Coverage
    if [[ -f "jest.config.js" ]] || grep -q "jest" package.json; then
        run_command "Coverage" "npm test -- --coverage --watchAll=false --coverageThreshold='{\"global\":{\"lines\":${COVERAGE_THRESHOLD}}}'" "Check test coverage"
    fi

    # Gate 7: Security
    if [[ $SKIP_SECURITY == false ]]; then
        run_command "Security" "npm audit --audit-level moderate" "Security vulnerability scan"
    fi

    # Gate 8: Build
    if [[ $SKIP_BUILD == false ]] && grep -q "build" package.json; then
        run_command "Build" "npm run build" "Production build"
    fi

    # Gate 9: Documentation
    check_documentation_js
}

# Python verification
verify_python() {
    log "INFO" "Starting Python verification..."

    # Check if virtual environment is active
    if [[ -z "$VIRTUAL_ENV" ]]; then
        log "WARNING" "No virtual environment detected. Consider using venv or conda."
    fi

    # Gate 1: Dependencies
    if [[ -f "requirements.txt" ]]; then
        run_command "Dependencies" "pip install -r requirements.txt" "Install requirements"
    elif [[ -f "pyproject.toml" ]]; then
        run_command "Dependencies" "pip install -e ." "Install package with dependencies"
    fi

    # Gate 2: Formatting
    if command -v black &> /dev/null; then
        run_command "Formatting" "black --check --diff src/ tests/" "Check code formatting with Black"
    else
        log "WARNING" "Black formatter not found, skipping formatting check"
    fi

    # Gate 3: Import Sorting
    if command -v isort &> /dev/null; then
        run_command "Import_Sorting" "isort --check-only --diff src/ tests/" "Check import sorting"
    fi

    # Gate 4: Linting
    if command -v flake8 &> /dev/null; then
        run_command "Linting" "flake8 src/ tests/" "Run flake8 linting"
    elif command -v pylint &> /dev/null; then
        run_command "Linting" "pylint src/" "Run pylint checks"
    else
        log "WARNING" "No Python linter found"
    fi

    # Gate 5: Type Checking
    if command -v mypy &> /dev/null; then
        run_command "Type_Checking" "mypy src/" "Run mypy type checking"
    else
        log "WARNING" "mypy not found, skipping type checking"
    fi

    # Gate 6: Testing with Coverage
    if command -v pytest &> /dev/null; then
        run_command "Testing" "pytest tests/ -v" "Run pytest tests"
        if command -v coverage &> /dev/null; then
            run_command "Coverage" "pytest --cov=src --cov-report=term-missing --cov-fail-under=${COVERAGE_THRESHOLD} tests/" "Check test coverage"
        fi
    elif [[ -f "test*.py" ]] || [[ -d "tests/" ]]; then
        run_command "Testing" "python -m unittest discover" "Run unittest tests"
    else
        log "WARNING" "No tests found"
    fi

    # Gate 7: Security
    if [[ $SKIP_SECURITY == false ]]; then
        if command -v bandit &> /dev/null; then
            run_command "Security" "bandit -r src/" "Security scan with bandit"
        fi
        if command -v safety &> /dev/null; then
            run_command "Dependency_Security" "safety check" "Check dependencies for vulnerabilities"
        fi
    fi

    # Gate 8: Documentation
    check_documentation_python
}

# Go verification
verify_go() {
    log "INFO" "Starting Go verification..."

    # Gate 1: Dependencies
    run_command "Dependencies" "go mod tidy" "Tidy dependencies"
    run_command "Dependency_Verification" "go mod verify" "Verify dependencies"

    # Gate 2: Formatting
    run_command "Formatting" "gofmt -l . | wc -l | grep -q '^0$'" "Check go fmt"

    # Gate 3: Linting
    if command -v golangci-lint &> /dev/null; then
        run_command "Linting" "golangci-lint run" "Run golangci-lint"
    else
        run_command "Vet" "go vet ./..." "Run go vet"
    fi

    # Gate 4: Testing
    run_command "Testing" "go test ./..." "Run tests"

    # Gate 5: Coverage
    run_command "Coverage" "go test -coverprofile=coverage.out ./... && go tool cover -func=coverage.out | grep total | awk '{print \$3}' | sed 's/%//' | awk -v threshold=${COVERAGE_THRESHOLD} '\$1 >= threshold'" "Check test coverage"

    # Gate 6: Security
    if [[ $SKIP_SECURITY == false ]] && command -v gosec &> /dev/null; then
        run_command "Security" "gosec ./..." "Security scan with gosec"
    fi

    # Gate 7: Build
    if [[ $SKIP_BUILD == false ]]; then
        run_command "Build" "go build ./..." "Build project"
    fi
}

# Rust verification
verify_rust() {
    log "INFO" "Starting Rust verification..."

    # Gate 1: Dependencies
    run_command "Dependencies" "cargo check" "Check dependencies and compilation"

    # Gate 2: Formatting
    run_command "Formatting" "cargo fmt -- --check" "Check rustfmt formatting"

    # Gate 3: Linting
    run_command "Linting" "cargo clippy -- -D warnings" "Run Clippy lints"

    # Gate 4: Testing
    run_command "Testing" "cargo test" "Run tests"

    # Gate 5: Documentation
    run_command "Documentation" "cargo doc --no-deps" "Generate documentation"

    # Gate 6: Security
    if [[ $SKIP_SECURITY == false ]] && command -v cargo-audit &> /dev/null; then
        run_command "Security" "cargo audit" "Security vulnerability scan"
    fi

    # Gate 7: Build
    if [[ $SKIP_BUILD == false ]]; then
        run_command "Build" "cargo build --release" "Release build"
    fi
}

# Check documentation for JavaScript/TypeScript
check_documentation_js() {
    local has_readme=false
    local has_jsdoc=false

    if [[ -f "README.md" ]] || [[ -f "readme.md" ]]; then
        has_readme=true
    fi

    if grep -r "@param\|@returns\|@description" src/ &> /dev/null; then
        has_jsdoc=true
    fi

    if [[ $has_readme == true ]]; then
        log "SUCCESS" "README.md found"
    else
        log "WARNING" "No README.md found"
    fi

    if [[ $has_jsdoc == true ]]; then
        log "SUCCESS" "JSDoc comments found"
    else
        log "WARNING" "No JSDoc comments found"
    fi

    # Check for TypeScript declaration files if applicable
    if [[ -f "tsconfig.json" ]]; then
        if find src/ -name "*.d.ts" | grep -q "."; then
            log "SUCCESS" "TypeScript declarations found"
        fi
    fi
}

# Check documentation for Python
check_documentation_python() {
    local has_readme=false
    local has_docstrings=false

    if [[ -f "README.md" ]] || [[ -f "readme.md" ]]; then
        has_readme=true
    fi

    if grep -r '"""' src/ &> /dev/null; then
        has_docstrings=true
    fi

    if [[ $has_readme == true ]]; then
        log "SUCCESS" "README.md found"
    else
        log "WARNING" "No README.md found"
    fi

    if [[ $has_docstrings == true ]]; then
        log "SUCCESS" "Python docstrings found"
    else
        log "WARNING" "No Python docstrings found"
    fi
}

# Generate results report
generate_report() {
    local start_time="$1"
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    log "INFO" "Generating verification report..."

    # Calculate success rate
    local success_rate=0
    if [[ $TOTAL_GATES -gt 0 ]]; then
        success_rate=$(echo "scale=2; $PASSED_GATES * 100 / $TOTAL_GATES" | bc -l)
    fi

    # Create JSON report
    cat > "$RESULTS_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "project_type": "$PROJECT_TYPE",
    "duration_seconds": $duration,
    "total_gates": $TOTAL_GATES,
    "passed_gates": $PASSED_GATES,
    "success_rate": $success_rate,
    "coverage_threshold": $COVERAGE_THRESHOLD,
    "gates": {
EOF

    local first=true
    for gate in "${!GATE_RESULTS[@]}"; do
        if [[ $first == false ]]; then
            echo "," >> "$RESULTS_FILE"
        fi
        echo -n "        \"$gate\": \"${GATE_RESULTS[$gate]}\"" >> "$RESULTS_FILE"
        first=false
    done

    cat >> "$RESULTS_FILE" << EOF

    }
}
EOF

    # Display summary
    echo ""
    echo "================================================"
    echo -e "${CYAN}🏁 Verification Complete${NC}"
    echo "================================================"
    echo "Project Type: $PROJECT_TYPE"
    echo "Duration: ${duration}s"
    echo "Gates Passed: $PASSED_GATES/$TOTAL_GATES"
    echo "Success Rate: $success_rate%"
    echo "Results: $RESULTS_FILE"
    echo ""

    # Show gate results
    echo -e "${CYAN}Gate Results:${NC}"
    for gate in "${!GATE_RESULTS[@]}"; do
        local result="${GATE_RESULTS[$gate]}"
        if [[ $result == "PASSED" ]]; then
            echo -e "  ✅ $gate"
        else
            echo -e "  ❌ $gate"
        fi
    done

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
    echo "Exit on Failure: $EXIT_ON_FIRST_FAILURE"
    echo ""

    # Initialize results file
    mkdir -p "$(dirname "$RESULTS_FILE")"

    # Detect project type and run appropriate verification
    detect_project_type

    case $PROJECT_TYPE in
        "javascript")
            verify_javascript
            ;;
        "python")
            verify_python
            ;;
        "go")
            verify_go
            ;;
        "rust")
            verify_rust
            ;;
        *)
            log "ERROR" "Unsupported project type: $PROJECT_TYPE"
            exit 1
            ;;
    esac

    # Generate final report
    generate_report "$start_time"
}

# Check dependencies
check_dependencies() {
    local missing_deps=()

    # Check for bc (calculator)
    if ! command -v bc &> /dev/null; then
        missing_deps+=("bc")
    fi

    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log "WARNING" "Missing dependencies: ${missing_deps[*]}"
        log "INFO" "Install with: sudo apt-get install ${missing_deps[*]} (Ubuntu/Debian) or brew install ${missing_deps[*]} (macOS)"
    fi
}

# Script execution
check_dependencies
main