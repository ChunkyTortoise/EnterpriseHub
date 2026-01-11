#!/bin/bash

# EnterpriseHub Complete Workflow Automation
# Handles commit, push, and PR creation in one command

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_BRANCH="main"
CO_AUTHORED_BY="Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"

# Functions
log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✅${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}❌${NC} $1"; }
log_step() { echo -e "${PURPLE}🔄${NC} $1"; }

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════╗"
    echo "║       EnterpriseHub Workflow         ║"
    echo "║    Automated Commit + Push + PR      ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

# Validate environment
validate_environment() {
    log_step "Validating environment..."

    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi

    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) not found. Install with: brew install gh"
        exit 1
    fi

    log_success "Environment validated"
}

# Check for changes
check_changes() {
    log_step "Checking for changes..."

    # Check for unstaged changes
    if ! git diff --quiet; then
        log_info "Found unstaged changes"
        git status --porcelain
        return 0
    fi

    # Check for staged changes
    if ! git diff --cached --quiet; then
        log_info "Found staged changes"
        return 0
    fi

    log_warning "No changes to commit"
    exit 0
}

# Run quality checks
run_quality_checks() {
    log_step "Running quality checks..."

    # Run pre-commit checks if available
    if [ -f "scripts/pre-commit-check.sh" ]; then
        log_info "Running pre-commit checks..."
        if ! ./scripts/pre-commit-check.sh; then
            log_error "Pre-commit checks failed"
            read -p "Continue anyway? (y/N): " continue_anyway
            if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        else
            log_success "Pre-commit checks passed"
        fi
    else
        log_warning "No pre-commit checks found"
    fi

    # Check for common issues
    if grep -r "TODO" --include="*.py" --include="*.js" --include="*.ts" . > /dev/null; then
        log_warning "Found TODO comments in code"
        read -p "Continue anyway? (y/N): " continue_anyway
        if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Create commit
create_commit() {
    log_step "Creating commit..."

    echo ""
    echo "📝 Commit Information:"
    echo "1) feat: New feature"
    echo "2) fix: Bug fix"
    echo "3) docs: Documentation"
    echo "4) refactor: Code refactoring"
    echo "5) test: Add tests"
    echo "6) chore: Maintenance"

    read -p "Select commit type (1-6): " choice

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

    read -p "Brief description: " description

    if [ -z "$description" ]; then
        log_error "Description cannot be empty"
        exit 1
    fi

    read -p "Detailed description (optional): " detailed_description

    # Build commit message
    COMMIT_MSG="$COMMIT_TYPE: $description"

    if [ ! -z "$detailed_description" ]; then
        COMMIT_MSG="$COMMIT_MSG

$detailed_description"
    fi

    COMMIT_MSG="$COMMIT_MSG

$CO_AUTHORED_BY"

    # Stage and commit
    git add .
    git commit -m "$COMMIT_MSG"

    log_success "Commit created: $COMMIT_TYPE: $description"
}

# Handle branch creation and push
handle_branch_and_push() {
    log_step "Handling branch and push..."

    CURRENT_BRANCH=$(git branch --show-current)

    # Create feature branch if on main
    if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
        log_info "On $CURRENT_BRANCH, creating feature branch..."

        echo ""
        echo "🌿 Branch Type:"
        echo "1) feature/"
        echo "2) fix/"
        echo "3) docs/"
        echo "4) refactor/"
        echo "5) chore/"

        read -p "Select branch type (1-5): " choice

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

        # Auto-generate branch name from commit message
        SUGGESTED_NAME=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')
        read -p "Branch name [$SUGGESTED_NAME]: " branch_name

        if [ -z "$branch_name" ]; then
            branch_name="$SUGGESTED_NAME"
        fi

        NEW_BRANCH="$BRANCH_PREFIX/$branch_name"

        log_info "Creating branch: $NEW_BRANCH"
        git checkout -b "$NEW_BRANCH"
        CURRENT_BRANCH="$NEW_BRANCH"
    fi

    # Push branch
    log_info "Pushing branch: $CURRENT_BRANCH"
    if ! git push -u origin "$CURRENT_BRANCH" 2>/dev/null; then
        git push origin "$CURRENT_BRANCH"
    fi
    log_success "Branch pushed successfully"

    return 0
}

# Create pull request
create_pull_request() {
    log_step "Creating pull request..."

    # Get commits for PR
    RECENT_COMMITS=$(git log --oneline "$DEFAULT_BRANCH"..HEAD)
    COMMIT_COUNT=$(echo "$RECENT_COMMITS" | wc -l)

    if [ $COMMIT_COUNT -eq 1 ]; then
        FIRST_COMMIT=$(git log -1 --pretty=format:"%s")
        PR_TITLE="$FIRST_COMMIT"
    else
        echo ""
        read -p "PR title: " PR_TITLE
        if [ -z "$PR_TITLE" ]; then
            PR_TITLE="Multiple improvements and fixes"
        fi
    fi

    # Build PR body
    PR_BODY="## Summary
$(echo "$RECENT_COMMITS" | sed 's/^[a-f0-9]* /- /')

## Changes Made
- Enhanced EnterpriseHub workflow automation
- Improved code quality and testing
- Updated documentation

## Test Plan
- [ ] All existing tests pass
- [ ] New functionality tested
- [ ] Code follows EnterpriseHub standards
- [ ] Documentation updated

## Business Impact
- Improved development velocity
- Enhanced code quality
- Better maintainability

🤖 Generated with [Claude Code](https://claude.com/claude-code)"

    # Create PR
    PR_URL=$(gh pr create --title "$PR_TITLE" --body "$PR_BODY")

    if [ $? -eq 0 ]; then
        log_success "Pull request created: $PR_URL"

        echo ""
        read -p "🌐 Open PR in browser? (y/N): " open_browser
        if [[ "$open_browser" =~ ^[Yy]$ ]]; then
            gh pr view --web
        fi

        echo ""
        read -p "📋 Copy PR URL to clipboard? (y/N): " copy_url
        if [[ "$copy_url" =~ ^[Yy]$ ]]; then
            echo "$PR_URL" | pbcopy 2>/dev/null || echo "$PR_URL" | xclip -selection clipboard 2>/dev/null || echo "Copy manually: $PR_URL"
            log_success "PR URL copied to clipboard"
        fi
    else
        log_error "Failed to create pull request"
        exit 1
    fi
}

# Main execution
main() {
    print_banner

    validate_environment
    check_changes
    run_quality_checks
    create_commit
    handle_branch_and_push
    create_pull_request

    echo ""
    log_success "🎉 Workflow completed successfully!"
    echo -e "${GREEN}Your changes are now committed, pushed, and have a pull request ready for review.${NC}"
}

# Script entry point
main "$@"