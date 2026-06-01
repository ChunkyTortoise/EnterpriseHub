#!/bin/bash

# TDD Cycle Automation Script
# Automates the RED → GREEN → REFACTOR workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TEST_DIR="tests"
SRC_DIR="src"
COVERAGE_THRESHOLD=80
WATCH_MODE=false
VERBOSE=false

# Help function
show_help() {
    echo "TDD Cycle Automation Script"
    echo ""
    echo "Usage: $0 [OPTIONS] [test_file]"
    echo ""
    echo "Options:"
    echo "  -w, --watch          Run in watch mode"
    echo "  -v, --verbose        Verbose output"
    echo "  -t, --threshold NUM  Coverage threshold (default: 80)"
    echo "  -h, --help           Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run full TDD cycle"
    echo "  $0 -w                        # Run in watch mode"
    echo "  $0 -v test_specific.py       # Run specific test file with verbose output"
    echo "  $0 -t 90                     # Set coverage threshold to 90%"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--threshold)
            COVERAGE_THRESHOLD="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Unknown option $1"
            show_help
            exit 1
            ;;
        *)
            TEST_FILE="$1"
            shift
            ;;
    esac
done

# Detect project type
detect_project_type() {
    if [[ -f "pyproject.toml" || -f "setup.py" || -f "requirements.txt" ]]; then
        echo "python"
    elif [[ -f "package.json" ]]; then
        echo "javascript"
    else
        echo "unknown"
    fi
}

# Run Python tests
run_python_tests() {
    local test_file=${1:-""}
    local options=""

    if [[ $VERBOSE == true ]]; then
        options="$options -v"
    fi

    if [[ -n $test_file ]]; then
        options="$options $test_file"
    fi

    echo -e "${YELLOW}Running Python tests...${NC}"

    if command -v pytest &> /dev/null; then
        pytest $options --cov=$SRC_DIR --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD
    elif command -v python -m pytest &> /dev/null; then
        python -m pytest $options --cov=$SRC_DIR --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD
    else
        echo -e "${RED}pytest not found. Installing...${NC}"
        pip install pytest pytest-cov
        python -m pytest $options --cov=$SRC_DIR --cov-report=term-missing --cov-fail-under=$COVERAGE_THRESHOLD
    fi
}

# Run JavaScript tests
run_javascript_tests() {
    local test_file=${1:-""}

    echo -e "${YELLOW}Running JavaScript tests...${NC}"

    if [[ -f "package.json" ]]; then
        if command -v npm &> /dev/null; then
            if [[ -n $test_file ]]; then
                npm test -- $test_file
            else
                npm test
            fi
        else
            echo -e "${RED}npm not found${NC}"
            exit 1
        fi
    else
        echo -e "${RED}package.json not found${NC}"
        exit 1
    fi
}

# RED Phase - Verify tests fail
red_phase() {
    echo -e "${RED}🔴 RED PHASE: Verifying tests fail...${NC}"
    echo "========================================="

    local project_type=$(detect_project_type)

    case $project_type in
        "python")
            if ! run_python_tests $TEST_FILE; then
                echo -e "${RED}✓ Tests are failing as expected${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ Warning: Tests are passing in RED phase${NC}"
                echo -e "${YELLOW}Make sure you wrote a failing test first!${NC}"
                return 1
            fi
            ;;
        "javascript")
            if ! run_javascript_tests $TEST_FILE; then
                echo -e "${RED}✓ Tests are failing as expected${NC}"
                return 0
            else
                echo -e "${YELLOW}⚠ Warning: Tests are passing in RED phase${NC}"
                echo -e "${YELLOW}Make sure you wrote a failing test first!${NC}"
                return 1
            fi
            ;;
        *)
            echo -e "${RED}Unknown project type${NC}"
            exit 1
            ;;
    esac
}

# GREEN Phase - Make tests pass
green_phase() {
    echo -e "${GREEN}🟢 GREEN PHASE: Making tests pass...${NC}"
    echo "==========================================="

    local project_type=$(detect_project_type)

    case $project_type in
        "python")
            run_python_tests $TEST_FILE
            ;;
        "javascript")
            run_javascript_tests $TEST_FILE
            ;;
    esac

    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✓ All tests passing!${NC}"
        return 0
    else
        echo -e "${RED}✗ Tests still failing${NC}"
        echo -e "${YELLOW}Continue implementing until tests pass${NC}"
        return 1
    fi
}

# REFACTOR Phase - Improve code while keeping tests green
refactor_phase() {
    echo -e "${BLUE}🔵 REFACTOR PHASE: Verify tests still pass after refactoring...${NC}"
    echo "=================================================================="

    local project_type=$(detect_project_type)

    case $project_type in
        "python")
            run_python_tests $TEST_FILE
            ;;
        "javascript")
            run_javascript_tests $TEST_FILE
            ;;
    esac

    if [[ $? -eq 0 ]]; then
        echo -e "${BLUE}✓ Refactoring successful - all tests still pass!${NC}"
        return 0
    else
        echo -e "${RED}✗ Tests broken during refactoring${NC}"
        echo -e "${YELLOW}Fix the issues and ensure all tests pass${NC}"
        return 1
    fi
}

# Run linting and formatting
run_quality_checks() {
    echo -e "${YELLOW}Running code quality checks...${NC}"

    local project_type=$(detect_project_type)

    case $project_type in
        "python")
            # Run black formatter
            if command -v black &> /dev/null; then
                echo "Running black formatter..."
                black $SRC_DIR $TEST_DIR --check --diff
            fi

            # Run flake8 linter
            if command -v flake8 &> /dev/null; then
                echo "Running flake8 linter..."
                flake8 $SRC_DIR $TEST_DIR
            fi

            # Run mypy type checker
            if command -v mypy &> /dev/null; then
                echo "Running mypy type checker..."
                mypy $SRC_DIR
            fi
            ;;
        "javascript")
            # Run ESLint
            if command -v npx &> /dev/null && [[ -f ".eslintrc.js" || -f ".eslintrc.json" ]]; then
                echo "Running ESLint..."
                npx eslint src/ tests/ --max-warnings 0
            fi

            # Run Prettier
            if command -v npx &> /dev/null && [[ -f ".prettierrc" ]]; then
                echo "Running Prettier..."
                npx prettier --check src/ tests/
            fi
            ;;
    esac
}

# Watch mode for continuous TDD
watch_mode() {
    echo -e "${YELLOW}🔄 Watch mode enabled. File changes will trigger test runs...${NC}"

    if command -v entr &> /dev/null; then
        find $SRC_DIR $TEST_DIR -name "*.py" -o -name "*.js" -o -name "*.ts" | entr -c bash $0 $TEST_FILE
    elif command -v fswatch &> /dev/null; then
        fswatch -o $SRC_DIR $TEST_DIR | xargs -n1 -I{} bash $0 $TEST_FILE
    else
        echo -e "${RED}Watch mode requires 'entr' or 'fswatch'${NC}"
        echo "Install with: brew install entr (macOS) or apt-get install entr (Ubuntu)"
        exit 1
    fi
}

# Main TDD cycle
run_tdd_cycle() {
    echo "================================================="
    echo "🧪 TDD Cycle Automation"
    echo "================================================="
    echo "Project type: $(detect_project_type)"
    echo "Coverage threshold: ${COVERAGE_THRESHOLD}%"
    if [[ -n $TEST_FILE ]]; then
        echo "Test file: $TEST_FILE"
    fi
    echo "================================================="
    echo ""

    # Phase 1: RED
    echo "Starting TDD cycle..."
    if ! red_phase; then
        echo -e "${YELLOW}Tip: Write a failing test first, then implement the feature${NC}"
    fi

    echo ""

    # Phase 2: GREEN
    green_phase
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}TDD cycle incomplete - tests not passing${NC}"
        exit 1
    fi

    echo ""

    # Phase 3: REFACTOR
    echo -e "${BLUE}Ready for refactoring phase...${NC}"
    echo -e "${BLUE}Refactor your code, then run this script again to verify${NC}"

    # Run quality checks
    echo ""
    run_quality_checks

    echo ""
    echo -e "${GREEN}🎉 TDD cycle complete!${NC}"
    echo -e "${GREEN}✓ Tests are passing${NC}"
    echo -e "${GREEN}✓ Coverage threshold met${NC}"
    echo -e "${GREEN}✓ Code quality checks passed${NC}"
}

# Main execution
main() {
    if [[ $WATCH_MODE == true ]]; then
        watch_mode
    else
        run_tdd_cycle
    fi
}

# Script execution
main