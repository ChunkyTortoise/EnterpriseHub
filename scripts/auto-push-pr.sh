#!/bin/bash

# EnterpriseHub Auto-Push-PR Script
# Automates branch creation, push, and PR creation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BRANCH="main"

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

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh) is not installed. Install with: brew install gh"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)

# If on main/master, create a new branch
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    log_warning "Currently on $CURRENT_BRANCH. Creating feature branch..."

    echo "Select branch type:"
    echo "1) feature/"
    echo "2) fix/"
    echo "3) docs/"
    echo "4) refactor/"
    echo "5) chore/"

    read -p "Enter choice (1-5): " choice

    case $choice in
        1) BRANCH_PREFIX="feature" ;;
        2) BRANCH_PREFIX="fix" ;;
        3) BRANCH_PREFIX="docs" ;;
        4) BRANCH_PREFIX="refactor" ;;
        5) BRANCH_PREFIX="chore" ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    read -p "Enter branch name (e.g., user-authentication): " branch_name

    if [ -z "$branch_name" ]; then
        log_error "Branch name cannot be empty"
        exit 1
    fi

    NEW_BRANCH="$BRANCH_PREFIX/$branch_name"

    log_info "Creating branch: $NEW_BRANCH"
    git checkout -b "$NEW_BRANCH"
    CURRENT_BRANCH="$NEW_BRANCH"
fi

# Check if there are commits to push
if git diff --quiet "$DEFAULT_BRANCH" HEAD; then
    log_warning "No new commits to push"
    exit 0
fi

# Push branch
log_info "Pushing branch: $CURRENT_BRANCH"
if ! git push -u origin "$CURRENT_BRANCH" 2>/dev/null; then
    # Branch might already exist, try regular push
    git push origin "$CURRENT_BRANCH"
fi
log_success "Branch pushed successfully"

# Get PR title and body from recent commits
RECENT_COMMITS=$(git log --oneline "$DEFAULT_BRANCH"..HEAD)
COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)

if [ $COMMIT_COUNT -eq 1 ]; then
    # Single commit - use commit message as PR title
    COMMIT_MSG=$(git log -1 --pretty=format:"%s")
    PR_TITLE="$COMMIT_MSG"
else
    # Multiple commits - ask for PR title
    read -p "Enter PR title: " PR_TITLE
    if [ -z "$PR_TITLE" ]; then
        PR_TITLE="$CURRENT_BRANCH changes"
    fi
fi

# Create PR body with commit list
PR_BODY="## Summary
$(echo "$RECENT_COMMITS" | sed 's/^[a-f0-9]* /- /')

## Test Plan
- [ ] Verify all tests pass
- [ ] Check code follows project standards
- [ ] Validate functionality works as expected

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

# Create PR
log_info "Creating pull request..."
PR_URL=$(gh pr create --title "$PR_TITLE" --body "$PR_BODY")

if [ $? -eq 0 ]; then
    log_success "Pull request created: $PR_URL"

    # Open PR in browser
    read -p "Open PR in browser? (y/N): " open_browser
    if [[ "$open_browser" =~ ^[Yy]$ ]]; then
        gh pr view --web
    fi
else
    log_error "Failed to create pull request"
    exit 1
fi