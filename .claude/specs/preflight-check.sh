#!/bin/bash

# Content Development Sprint - Pre-Flight Checklist
# Run this before starting Session 1 to validate environment
# Usage: bash .claude/specs/preflight-check.sh

set -e  # Exit on any error

echo "═══════════════════════════════════════════════════════"
echo "  Content Development Sprint - Pre-Flight Check"
echo "═══════════════════════════════════════════════════════"
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
CHECKS=0
PASSED=0
WARNINGS=0
FAILED=0

# Check function
check() {
    CHECKS=$((CHECKS + 1))
    printf "[%02d] %-50s " "$CHECKS" "$1"
}

pass() {
    PASSED=$((PASSED + 1))
    echo -e "${GREEN}✓ PASS${NC}"
}

warn() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠ WARN${NC} - $1"
}

fail() {
    FAILED=$((FAILED + 1))
    echo -e "${RED}✗ FAIL${NC} - $1"
}

# Check 1: Working directory
check "Working directory is EnterpriseHub"
if [[ $(basename "$PWD") == "EnterpriseHub" ]]; then
    pass
else
    fail "Current directory: $PWD (expected: */EnterpriseHub)"
fi

# Check 2: Git repository
check "Git repository initialized"
if git rev-parse --git-dir > /dev/null 2>&1; then
    pass
else
    fail "Not a git repository. Run: git init"
fi

# Check 3: Git status
check "Git working directory is clean"
if [[ -z $(git status --porcelain) ]]; then
    pass
else
    UNCOMMITTED=$(git status --porcelain | wc -l | tr -d ' ')
    warn "$UNCOMMITTED uncommitted changes. Commit or stash before sprint."
fi

# Check 4: Git remote
check "Git remote configured"
if git remote -v | grep -q "origin"; then
    pass
else
    warn "No 'origin' remote. Set up with: git remote add origin <url>"
fi

# Check 5: Beads installed
check "Beads command available"
if command -v bd &> /dev/null; then
    pass
else
    fail "Beads not found. Install from: https://github.com/beadsinc/beads"
fi

# Check 6: Beads working
check "Beads repository initialized"
if bd stats &> /dev/null; then
    pass
else
    warn "Beads not initialized. Run: bd init"
fi

# Check 7: Output directories
check "Output directories exist"
if [[ -d "content" ]]; then
    pass
else
    warn "Creating content/ directories..."
    mkdir -p content/{video,visual,business,case-studies}
    echo -e "${YELLOW}    Created: content/video, content/visual, content/business, content/case-studies${NC}"
fi

# Check 8: Spec files
check "Spec files exist"
if [[ -f ".claude/specs/CONTENT_DEV_TEAM_SPEC.md" ]]; then
    pass
else
    fail "Spec not found at: .claude/specs/CONTENT_DEV_TEAM_SPEC.md"
fi

# Check 9: Runbook exists
check "Runbook exists"
if [[ -f ".claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md" ]]; then
    pass
else
    fail "Runbook not found at: .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md"
fi

# Check 10: Portfolio audit reports
check "Portfolio audit reports accessible"
if [[ -d "$HOME/.claude/teams/portfolio-dev-team" ]]; then
    AUDIT_COUNT=$(ls -1 "$HOME/.claude/teams/portfolio-dev-team/audit-"*.md 2>/dev/null | wc -l | tr -d ' ')
    if [[ $AUDIT_COUNT -gt 0 ]]; then
        pass
        echo -e "    ${BLUE}Found $AUDIT_COUNT audit reports${NC}"
    else
        warn "No audit reports found in ~/.claude/teams/portfolio-dev-team/"
    fi
else
    warn "Audit directory not found: ~/.claude/teams/portfolio-dev-team/"
fi

# Check 11: Reference files
check "Freelance reference files exist"
if [[ -f "$HOME/.claude/reference/freelance/portfolio-repos.md" ]]; then
    pass
else
    warn "portfolio-repos.md not found at: ~/.claude/reference/freelance/"
fi

# Check 12: Disk space
check "Adequate disk space available"
AVAIL_GB=$(df -h . | awk 'NR==2 {print $4}' | sed 's/Gi*//')
if [[ ${AVAIL_GB%%.*} -gt 1 ]]; then
    pass
    echo -e "    ${BLUE}Available: ${AVAIL_GB}${NC}"
else
    warn "Low disk space: ${AVAIL_GB}"
fi

# Check 13: Repo access (sample repos)
check "AI Orchestrator repo exists"
if [[ -d "$HOME/Documents/GitHub/ai-orchestrator" ]]; then
    pass
else
    warn "ai-orchestrator repo not found at ~/Documents/GitHub/"
fi

check "DocQA Engine repo exists"
if [[ -d "$HOME/Documents/GitHub/docqa-engine" ]]; then
    pass
else
    warn "docqa-engine repo not found at ~/Documents/GitHub/"
fi

# Check 14: No existing team
check "No existing content-dev-team"
if [[ ! -d "$HOME/.claude/teams/content-dev-team" ]]; then
    pass
else
    warn "Team already exists. Delete with: rm -rf ~/.claude/teams/content-dev-team"
fi

# Check 15: Time availability
echo ""
echo -e "${BLUE}[MANUAL CHECK]${NC} Time Availability:"
echo "    Session 1 requires a 4-hour uninterrupted block."
echo "    Do you have this time available now? [y/N]"
read -r TIME_AVAIL
if [[ $TIME_AVAIL =~ ^[Yy]$ ]]; then
    PASSED=$((PASSED + 1))
    echo -e "    ${GREEN}✓ Time confirmed${NC}"
else
    WARNINGS=$((WARNINGS + 1))
    echo -e "    ${YELLOW}⚠ Schedule a 4-hour block before starting${NC}"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Pre-Flight Check Summary"
echo "═══════════════════════════════════════════════════════"
echo ""
printf "Total Checks: %2d\n" "$CHECKS"
printf "${GREEN}✓ Passed:     %2d${NC}\n" "$PASSED"
printf "${YELLOW}⚠ Warnings:   %2d${NC}\n" "$WARNINGS"
printf "${RED}✗ Failed:     %2d${NC}\n" "$FAILED"
echo ""

# Final verdict
if [[ $FAILED -gt 0 ]]; then
    echo -e "${RED}❌ PRE-FLIGHT FAILED${NC}"
    echo "Fix the failed checks before starting the sprint."
    echo ""
    echo "Need help? See: .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md"
    exit 1
elif [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  PRE-FLIGHT PASSED WITH WARNINGS${NC}"
    echo "Review warnings above. You can proceed, but address warnings if possible."
    echo ""
    echo -e "${BLUE}Next Step:${NC} Open .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md"
    echo "           Start with Session 1, Step 1.1"
    exit 0
else
    echo -e "${GREEN}✅ PRE-FLIGHT PASSED${NC}"
    echo "All checks passed! You're ready to start the sprint."
    echo ""
    echo -e "${BLUE}Next Step:${NC} Open .claude/specs/CONTENT_DEV_EXECUTION_RUNBOOK.md"
    echo "           Start with Session 1, Step 1.1"
    echo ""
    echo "Or use the Quick Reference: .claude/specs/CONTENT_DEV_QUICK_REFERENCE.md"
    exit 0
fi
