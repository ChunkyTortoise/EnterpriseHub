#!/bin/bash
#
# Pre-commit validation script for EnterpriseHub
# Runs before git commit to ensure code quality and security
#
# Usage: Called automatically by git pre-commit hook
#        Or manually: ./.claude/scripts/pre-commit-validation.sh

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}🔍 EnterpriseHub Pre-Commit Validation${NC}"
echo -e "${BLUE}======================================${NC}\n"

# Counter for checks
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Function to print status
print_check() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓${NC} $message"
        ((CHECKS_PASSED++))
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗${NC} $message"
        ((CHECKS_FAILED++))
    elif [ "$status" = "WARN" ]; then
        echo -e "${YELLOW}⚠${NC} $message"
        ((WARNINGS++))
    else
        echo -e "${BLUE}ℹ${NC} $message"
    fi
}

# Check 1: No secrets in staged files
echo -e "\n${BLUE}[1/8] Checking for secrets and credentials...${NC}"
SECRETS_FOUND=0

# Check for common secret patterns
if git diff --cached --name-only | xargs -I {} grep -Hn -E '(ANTHROPIC_API_KEY|GHL_.*API|sk-[a-zA-Z0-9]{32,}|DATABASE_URL=.*:.*@|JWT_SECRET|REDIS_PASSWORD)' {} 2>/dev/null; then
    print_check "FAIL" "Found potential secrets in staged files"
    SECRETS_FOUND=1
else
    print_check "PASS" "No secrets detected"
fi

# Check for .env files being committed
if git diff --cached --name-only | grep -E '\.env$|\.env\.local$|\.env\.prod$' >/dev/null; then
    print_check "FAIL" "Attempting to commit .env file"
    SECRETS_FOUND=1
fi

if [ $SECRETS_FOUND -eq 1 ]; then
    echo -e "${RED}🛑 SECURITY VIOLATION: Secrets detected!${NC}"
    echo -e "Remove secrets and use environment variables instead."
    exit 1
fi

# Check 2: Python syntax
echo -e "\n${BLUE}[2/8] Validating Python syntax...${NC}"
SYNTAX_ERRORS=0

for file in $(git diff --cached --name-only --diff-filter=ACM | grep '\.py$'); do
    if [ -f "$file" ]; then
        if ! python3 -m py_compile "$file" 2>/dev/null; then
            print_check "FAIL" "Syntax error in $file"
            SYNTAX_ERRORS=1
        fi
    fi
done

if [ $SYNTAX_ERRORS -eq 0 ]; then
    print_check "PASS" "All Python files have valid syntax"
else
    echo -e "${RED}Fix syntax errors before committing${NC}"
    exit 1
fi

# Check 3: Ruff linting
echo -e "\n${BLUE}[3/8] Running Ruff linter...${NC}"
if command -v ruff &> /dev/null; then
    if git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | xargs ruff check --line-length=100 2>&1 | grep -v "All checks passed"; then
        print_check "WARN" "Ruff found linting issues (fixable with: ruff check --fix)"
    else
        print_check "PASS" "Ruff linting passed"
    fi
else
    print_check "WARN" "Ruff not installed, skipping lint check"
fi

# Check 4: Type checking with mypy (if installed)
echo -e "\n${BLUE}[4/8] Type checking with mypy...${NC}"
if command -v mypy &> /dev/null; then
    MYPY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | tr '\n' ' ')
    if [ -n "$MYPY_FILES" ]; then
        if mypy --ignore-missing-imports $MYPY_FILES 2>&1 | grep -E "(error|Error)"; then
            print_check "WARN" "Type checking found issues"
        else
            print_check "PASS" "Type checking passed"
        fi
    fi
else
    print_check "WARN" "mypy not installed, skipping type check"
fi

# Check 5: Tests for modified service files
echo -e "\n${BLUE}[5/8] Checking for corresponding test files...${NC}"
MISSING_TESTS=0

for file in $(git diff --cached --name-only --diff-filter=ACM | grep 'ghl_real_estate_ai/services/.*\.py$'); do
    filename=$(basename "$file" .py)
    test_file="tests/unit/test_${filename}.py"

    if [ ! -f "$test_file" ]; then
        print_check "WARN" "Missing test file for $file"
        MISSING_TESTS=1
    fi
done

if [ $MISSING_TESTS -eq 0 ]; then
    print_check "PASS" "All services have corresponding test files"
fi

# Check 6: Large files check
echo -e "\n${BLUE}[6/8] Checking for large files...${NC}"
LARGE_FILES=0

for file in $(git diff --cached --name-only --diff-filter=ACM); do
    if [ -f "$file" ]; then
        size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        if [ "$size" -gt 1048576 ]; then  # 1MB
            print_check "WARN" "Large file detected: $file ($(($size / 1024))KB)"
            LARGE_FILES=1
        fi
    fi
done

if [ $LARGE_FILES -eq 0 ]; then
    print_check "PASS" "No large files detected"
fi

# Check 7: CSV files (may contain PII)
echo -e "\n${BLUE}[7/8] Checking for CSV files...${NC}"
if git diff --cached --name-only | grep '\.csv$' >/dev/null; then
    print_check "WARN" "CSV files detected - ensure no PII is included"
else
    print_check "PASS" "No CSV files in commit"
fi

# Check 8: Commit message validation
echo -e "\n${BLUE}[8/8] Validating commit message format...${NC}"
if [ -f ".git/COMMIT_EDITMSG" ]; then
    COMMIT_MSG=$(head -n1 .git/COMMIT_EDITMSG)
    if [[ "$COMMIT_MSG" =~ ^(feat|fix|docs|style|refactor|test|chore|perf):\ .{10,} ]]; then
        print_check "PASS" "Commit message follows convention"
    else
        print_check "WARN" "Commit message doesn't follow convention (type: description)"
        echo -e "  Expected format: ${YELLOW}type: description${NC}"
        echo -e "  Types: feat, fix, docs, style, refactor, test, chore, perf"
    fi
fi

# Summary
echo -e "\n${BLUE}======================================${NC}"
echo -e "${BLUE}Validation Summary${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✓ Passed:${NC} $CHECKS_PASSED"
echo -e "${RED}✗ Failed:${NC} $CHECKS_FAILED"
echo -e "${YELLOW}⚠ Warnings:${NC} $WARNINGS"

if [ $CHECKS_FAILED -gt 0 ]; then
    echo -e "\n${RED}❌ Pre-commit validation FAILED${NC}"
    echo -e "Fix the errors above before committing.\n"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  Pre-commit validation passed with warnings${NC}"
    echo -e "Consider addressing warnings before committing.\n"
fi

echo -e "\n${GREEN}✅ Pre-commit validation PASSED${NC}"
echo -e "Ready to commit!\n"

exit 0
