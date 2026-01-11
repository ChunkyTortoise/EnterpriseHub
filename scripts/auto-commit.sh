#!/bin/bash

# EnterpriseHub Auto-Commit Script
# Automates the commit process with proper message formatting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BRANCH="main"
CO_AUTHORED_BY="Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"

# Functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log_error "Not in a git repository"
    exit 1
fi

# Check for uncommitted changes
if git diff-index --quiet HEAD --; then
    log_warning "No changes to commit"
    exit 0
fi

# Get commit type from user input
echo "Select commit type:"
echo "1) feat: New feature"
echo "2) fix: Bug fix"
echo "3) docs: Documentation"
echo "4) refactor: Code refactoring"
echo "5) test: Add tests"
echo "6) chore: Maintenance"

read -p "Enter choice (1-6): " choice

case $choice in
    1) COMMIT_TYPE="feat" ;;
    2) COMMIT_TYPE="fix" ;;
    3) COMMIT_TYPE="docs" ;;
    4) COMMIT_TYPE="refactor" ;;
    5) COMMIT_TYPE="test" ;;
    6) COMMIT_TYPE="chore" ;;
    *)
        log_error "Invalid choice"
        exit 1
        ;;
esac

# Get commit message
read -p "Enter brief description: " description

if [ -z "$description" ]; then
    log_error "Description cannot be empty"
    exit 1
fi

# Optional detailed description
read -p "Enter detailed description (optional): " detailed_description

# Run pre-commit checks if available
if [ -f "scripts/pre-commit-check.sh" ]; then
    log_info "Running pre-commit checks..."
    if ! ./scripts/pre-commit-check.sh; then
        log_error "Pre-commit checks failed"
        exit 1
    fi
    log_success "Pre-commit checks passed"
fi

# Create commit message
COMMIT_MSG="$COMMIT_TYPE: $description"

if [ ! -z "$detailed_description" ]; then
    COMMIT_MSG="$COMMIT_MSG

$detailed_description"
fi

COMMIT_MSG="$COMMIT_MSG

$CO_AUTHORED_BY"

# Stage all changes
log_info "Staging changes..."
git add .

# Create commit
log_info "Creating commit..."
git commit -m "$COMMIT_MSG"

log_success "Commit created successfully"
log_info "Commit: $COMMIT_TYPE: $description"

# Show commit info
echo ""
git log --oneline -1