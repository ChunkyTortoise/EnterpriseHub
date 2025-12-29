#!/bin/bash
#
# EnterpriseHub Custom Pre-Commit Check Script
# =============================================
#
# INSTALLATION:
#   Option 1: Add to .git/hooks/pre-commit
#   Option 2: Run manually: ./scripts/pre-commit-check.sh
#   Option 3: Add to .pre-commit-config.yaml as local hook
#
# CHECKS:
#   1. Secrets detection (BLOCKING)
#   2. Cross-module import check (BLOCKING)
#   3. Large file warning
#   4. Test file existence warning
#   5. Session state initialization warning
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LARGE_FILE_THRESHOLD=512000  # 500KB

# Colors
if [ -t 1 ] && command -v tput &>/dev/null; then
    RED=$(tput setaf 1); GREEN=$(tput setaf 2); YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4); BOLD=$(tput bold); RESET=$(tput sgr0)
else
    RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; RESET=""
fi

info()    { echo "${BLUE}[INFO]${RESET} $*"; }
success() { echo "${GREEN}[OK]${RESET} $*"; }
warning() { echo "${YELLOW}[WARN]${RESET} $*"; }
error()   { echo "${RED}[FAIL]${RESET} $*"; }
header()  { echo ""; echo "${BOLD}=== $* ===${RESET}"; }

show_help() {
    cat << EOF
EnterpriseHub Pre-Commit Check Script

USAGE: $(basename "$0") [OPTIONS]

OPTIONS:
    -h, --help      Show this help
    -v, --verbose   Verbose output
    -q, --quiet     Suppress non-essential output
    --no-color      Disable colors

CHECKS:
    1. Secrets Detection - Scans for API keys, passwords, tokens
    2. Cross-Module Imports - No 'from modules.X import Y'
    3. Large Files - Warning for files > 500KB
    4. Test Files - Warning if module lacks tests
    5. Session State - Check for proper initialization
EOF
}

# Parse arguments
VERBOSE=false; QUIET=false
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help) show_help; exit 0 ;;
        -v|--verbose) VERBOSE=true; shift ;;
        -q|--quiet) QUIET=true; shift ;;
        --no-color) RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; RESET=""; shift ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

get_staged_files() { git diff --cached --name-only --diff-filter=ACM 2>/dev/null || true; }
get_staged_python_files() { get_staged_files | grep -E '\.py$' || true; }
get_staged_module_files() { get_staged_files | grep -E '^modules/[^/]+\.py$' | grep -v '__init__' || true; }

# Check 1: Secrets Detection
check_secrets() {
    header "Secrets Detection"
    local has_secrets=false
    local staged_files=$(get_staged_files)
    [[ -z "$staged_files" ]] && { [[ "$QUIET" != "true" ]] && info "No staged files"; return 0; }

    # Check for sensitive files
    if echo "$staged_files" | grep -qE '\.env($|\.)'; then
        error "Environment file (.env) staged for commit!"
        has_secrets=true
    fi
    if echo "$staged_files" | grep -qiE 'credentials|secrets\.json|\.pem$|\.key$'; then
        error "Credentials/key file staged for commit!"
        has_secrets=true
    fi

    # Check for secret patterns in content
    for file in $staged_files; do
        [[ ! -f "$REPO_ROOT/$file" ]] && continue
        case "$file" in *.md|*.txt|*.png|*.jpg|*.ico|*.svg|LICENSE*) continue ;; esac

        local content=$(git show ":$file" 2>/dev/null || true)
        [[ -z "$content" ]] && continue

        if echo "$content" | grep -qE 'sk-[a-zA-Z0-9]{32,}'; then
            error "$file: Potential OpenAI API key detected"
            has_secrets=true
        fi
        if echo "$content" | grep -qE 'sk-ant-[a-zA-Z0-9-]{32,}'; then
            error "$file: Potential Anthropic API key detected"
            has_secrets=true
        fi
        if echo "$content" | grep -qE 'AKIA[0-9A-Z]{16}'; then
            error "$file: Potential AWS Access Key detected"
            has_secrets=true
        fi
        if echo "$content" | grep -qE 'ghp_[a-zA-Z0-9]{36}'; then
            error "$file: Potential GitHub token detected"
            has_secrets=true
        fi
    done

    if [[ "$has_secrets" == "true" ]]; then
        error "Secrets detected. Remove them before committing."
        return 1
    fi
    success "No secrets detected"
    return 0
}

# Check 2: Cross-Module Imports
check_cross_module_imports() {
    header "Cross-Module Import Check"
    local has_violations=false
    local staged_files=$(get_staged_python_files)
    [[ -z "$staged_files" ]] && { [[ "$QUIET" != "true" ]] && info "No Python files"; return 0; }

    for file in $staged_files; do
        [[ ! -f "$REPO_ROOT/$file" ]] && continue
        local content=$(git show ":$file" 2>/dev/null || true)
        [[ -z "$content" ]] && continue

        if echo "$content" | grep -qE '^\s*(from\s+modules\.[a-zA-Z_]+\s+import|import\s+modules\.[a-zA-Z_]+)'; then
            error "$file: Cross-module import detected"
            has_violations=true
        fi
    done

    if [[ "$has_violations" == "true" ]]; then
        error "Use shared utilities from utils/ instead of importing from modules/"
        return 1
    fi
    success "No cross-module imports detected"
    return 0
}

# Check 3: Large Files
check_large_files() {
    header "Large File Check"
    local staged_files=$(get_staged_files)
    [[ -z "$staged_files" ]] && { [[ "$QUIET" != "true" ]] && info "No staged files"; return 0; }

    local threshold_kb=$((LARGE_FILE_THRESHOLD / 1024))
    for file in $staged_files; do
        [[ ! -f "$REPO_ROOT/$file" ]] && continue
        local size=$(wc -c < "$REPO_ROOT/$file" | tr -d ' ')
        if [[ "$size" -gt "$LARGE_FILE_THRESHOLD" ]]; then
            warning "$file ($((size / 1024))KB) exceeds ${threshold_kb}KB"
        fi
    done
    success "Large file check complete"
    return 0
}

# Check 4: Test Files
check_test_files() {
    header "Test File Check"
    local staged_modules=$(get_staged_module_files)
    [[ -z "$staged_modules" ]] && { [[ "$QUIET" != "true" ]] && info "No module files staged"; return 0; }

    for module_file in $staged_modules; do
        local module_name=$(basename "$module_file" .py)
        local test_file="tests/unit/test_${module_name}.py"
        if [[ ! -f "$REPO_ROOT/$test_file" ]]; then
            warning "$module_file has no test file: $test_file"
        fi
    done
    success "Test file check complete"
    return 0
}

# Check 5: Session State
check_session_state() {
    header "Session State Check"
    local staged_modules=$(get_staged_module_files)
    [[ -z "$staged_modules" ]] && { [[ "$QUIET" != "true" ]] && info "No module files"; return 0; }

    for module_file in $staged_modules; do
        [[ ! -f "$REPO_ROOT/$module_file" ]] && continue
        local content=$(git show ":$module_file" 2>/dev/null || true)
        [[ -z "$content" ]] && continue

        if echo "$content" | grep -q 'st\.session_state'; then
            if ! echo "$content" | grep -qE 'if\s+["\x27].*["\x27]\s+not\s+in\s+st\.session_state'; then
                warning "$module_file: Uses session_state but no top-level init found"
            fi
        fi
    done
    success "Session state check complete"
    return 0
}

# Main
main() {
    cd "$REPO_ROOT"
    [[ "$QUIET" != "true" ]] && echo "${BOLD}EnterpriseHub Pre-Commit Checks${RESET}"

    local failed=false

    check_secrets || failed=true
    check_cross_module_imports || failed=true
    check_large_files
    check_test_files
    check_session_state

    echo ""
    if [[ "$failed" == "true" ]]; then
        error "Pre-commit checks FAILED"
        exit 1
    else
        success "All pre-commit checks passed!"
        exit 0
    fi
}

main "$@"
