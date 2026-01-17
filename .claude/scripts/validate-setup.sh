#!/bin/bash
# Claude Code Setup Validation Script
# Verifies optimized configuration is correctly installed

set -euo pipefail

echo "🔍 Validating Claude Code Setup..."
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    WARN=$((WARN + 1))
}

# ============================================================================
# CHECK 1: Core CLAUDE.md Files
# ============================================================================

echo "## Check 1: Core CLAUDE.md Files"
echo ""

# Global CLAUDE.md
if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    SIZE=$(wc -w < "$HOME/.claude/CLAUDE.md")
    if [ "$SIZE" -lt 1500 ]; then
        pass "Global CLAUDE.md exists and is optimized (< 1500 words)"
    else
        warn "Global CLAUDE.md exists but may be too large ($SIZE words)"
    fi
else
    fail "Global CLAUDE.md not found at ~/.claude/CLAUDE.md"
fi

# Project CLAUDE.md
if [ -f "CLAUDE.md" ]; then
    SIZE=$(wc -w < "CLAUDE.md")
    if [ "$SIZE" -lt 1000 ]; then
        pass "Project CLAUDE.md exists and is optimized (< 1000 words)"
    else
        warn "Project CLAUDE.md exists but may be too large ($SIZE words)"
    fi
else
    fail "Project CLAUDE.md not found"
fi

echo ""

# ============================================================================
# CHECK 2: Reference Files
# ============================================================================

echo "## Check 2: Reference Files"
echo ""

REFERENCE_DIR="$HOME/.claude/reference"

if [ ! -d "$REFERENCE_DIR" ]; then
    fail "Reference directory not found: $REFERENCE_DIR"
else
    pass "Reference directory exists"

    # Check for required reference files
    REQUIRED_FILES=(
        "hooks-architecture.md"
        "token-optimization.md"
        "mcp-ecosystem.md"
        "advanced-workflows.md"
        "language-specific-standards.md"
        "security-implementation-guide.md"
        "testing-standards-guide.md"
    )

    for file in "${REQUIRED_FILES[@]}"; do
        if [ -f "$REFERENCE_DIR/$file" ]; then
            pass "Reference file exists: $file"
        else
            warn "Reference file missing: $file"
        fi
    done
fi

echo ""

# ============================================================================
# CHECK 3: Hooks System
# ============================================================================

echo "## Check 3: Hooks System"
echo ""

# Check hook files
HOOK_DIR=".claude/hooks"

if [ ! -d "$HOOK_DIR" ]; then
    warn "Hooks directory not found: $HOOK_DIR"
else
    pass "Hooks directory exists"

    # Check for hook definitions
    HOOK_FILES=("PreToolUse.md" "PostToolUse.md" "Stop.md")

    for file in "${HOOK_FILES[@]}"; do
        if [ -f "$HOOK_DIR/$file" ]; then
            pass "Hook definition exists: $file"
        else
            warn "Hook definition missing: $file"
        fi
    done
fi

# Check hook scripts
HOOK_SCRIPTS_DIR=".claude/scripts/hooks"

if [ ! -d "$HOOK_SCRIPTS_DIR" ]; then
    warn "Hook scripts directory not found: $HOOK_SCRIPTS_DIR"
else
    pass "Hook scripts directory exists"

    # Check for hook scripts
    HOOK_SCRIPTS=("pre-tool-use.sh" "post-tool-use.sh" "stop.sh")

    for script in "${HOOK_SCRIPTS[@]}"; do
        if [ -f "$HOOK_SCRIPTS_DIR/$script" ]; then
            # Check if executable
            if [ -x "$HOOK_SCRIPTS_DIR/$script" ]; then
                pass "Hook script exists and is executable: $script"
            else
                warn "Hook script exists but not executable: $script"
                echo "   Fix with: chmod +x $HOOK_SCRIPTS_DIR/$script"
            fi
        else
            warn "Hook script missing: $script"
        fi
    done
fi

echo ""

# ============================================================================
# CHECK 4: MCP Configuration
# ============================================================================

echo "## Check 4: MCP Configuration"
echo ""

MCP_CONFIG=".claude/settings.json"

if [ -f "$MCP_CONFIG" ]; then
    pass "MCP configuration exists"

    # Check for MCP servers
    if grep -q "mcp_servers" "$MCP_CONFIG"; then
        pass "MCP servers configured"

        # Count enabled servers
        ENABLED=$(grep -c '"enabled": true' "$MCP_CONFIG" || echo "0")
        echo "   Enabled servers: $ENABLED"
    else
        warn "MCP servers section not found in config"
    fi

    # Check for MCP profiles
    if [ -d ".claude/mcp-profiles" ]; then
        PROFILE_COUNT=$(ls -1 .claude/mcp-profiles/*.json 2>/dev/null | wc -l)
        if [ "$PROFILE_COUNT" -gt 0 ]; then
            pass "MCP profiles configured ($PROFILE_COUNT profiles)"
        else
            warn "MCP profiles directory exists but no profiles found"
        fi
    else
        warn "MCP profiles directory not found"
    fi
else
    warn "MCP configuration not found: $MCP_CONFIG"
fi

echo ""

# ============================================================================
# CHECK 5: Skills System
# ============================================================================

echo "## Check 5: Skills System"
echo ""

SKILLS_MANIFEST=".claude/skills/MANIFEST.yaml"

if [ -f "$SKILLS_MANIFEST" ]; then
    pass "Skills manifest exists"

    # Count skills
    SKILL_COUNT=$(grep -c "^  name:" "$SKILLS_MANIFEST" || echo "0")
    if [ "$SKILL_COUNT" -gt 0 ]; then
        pass "Skills configured ($SKILL_COUNT skills)"
    else
        warn "Skills manifest exists but no skills found"
    fi
else
    warn "Skills manifest not found: $SKILLS_MANIFEST"
fi

echo ""

# ============================================================================
# CHECK 6: Metrics Directory
# ============================================================================

echo "## Check 6: Metrics Directory"
echo ""

METRICS_DIR=".claude/metrics"

if [ ! -d "$METRICS_DIR" ]; then
    warn "Metrics directory not found, creating..."
    mkdir -p "$METRICS_DIR"
    pass "Metrics directory created"
else
    pass "Metrics directory exists"
fi

# Check for metrics files (create if missing)
METRICS_FILES=(
    "tool-sequence.log"
    "successful-patterns.log"
    "pattern-learning.log"
    "tool-usage.jsonl"
    "workflow-insights.jsonl"
    "session-summaries.jsonl"
)

for file in "${METRICS_FILES[@]}"; do
    if [ -f "$METRICS_DIR/$file" ]; then
        pass "Metrics file exists: $file"
    else
        warn "Metrics file missing, creating: $file"
        touch "$METRICS_DIR/$file"
    fi
done

echo ""

# ============================================================================
# CHECK 7: Documentation Accuracy
# ============================================================================

echo "## Check 7: Documentation Accuracy"
echo ""

if [ -f "CLAUDE.md" ]; then
    # Check for incorrect technology references
    if grep -qi "node\.js\|typescript\|pnpm\|npm install\|jest" CLAUDE.md; then
        fail "CLAUDE.md contains incorrect technology references (Node.js/TypeScript)"
        echo "   Run: cp CLAUDE-corrected.md CLAUDE.md"
    else
        pass "No incorrect technology references found"
    fi

    # Check for correct Python references
    if grep -q "Python" CLAUDE.md && grep -q "FastAPI" CLAUDE.md; then
        pass "Correct Python/FastAPI references present"
    else
        warn "Missing Python/FastAPI references"
    fi

    # Check for correct skills count
    if grep -q "31" CLAUDE.md; then
        pass "Correct skills count documented (31 skills)"
    else
        warn "Skills count may be outdated"
    fi
fi

echo ""

# ============================================================================
# CHECK 8: Forbidden Paths Configuration
# ============================================================================

echo "## Check 8: Forbidden Paths Configuration"
echo ""

if [ -f "CLAUDE.md" ]; then
    if grep -q "Forbidden Paths" CLAUDE.md || grep -q "NEVER Access" CLAUDE.md; then
        pass "Forbidden paths documented"

        # Check for critical forbidden paths
        if grep -q ".env" CLAUDE.md && grep -q "secrets/" CLAUDE.md; then
            pass "Critical forbidden paths documented (.env, secrets/)"
        else
            warn "Some critical forbidden paths may be missing"
        fi
    else
        warn "Forbidden paths not documented"
    fi
fi

echo ""

# ============================================================================
# CHECK 9: Git Configuration
# ============================================================================

echo "## Check 9: Git Configuration"
echo ""

# Check if in git repo
if [ -d ".git" ]; then
    pass "Git repository detected"

    # Check for .gitignore
    if [ -f ".gitignore" ]; then
        pass ".gitignore exists"

        # Check if .env is ignored
        if grep -q "^\.env$" .gitignore; then
            pass ".env is properly gitignored"
        else
            warn ".env should be in .gitignore"
        fi

        # Check if metrics are ignored (optional)
        if grep -q "\.claude/metrics" .gitignore; then
            pass "Metrics directory is gitignored (optional)"
        else
            warn "Consider gitignoring .claude/metrics/ (optional)"
        fi
    else
        warn ".gitignore not found"
    fi
else
    warn "Not a git repository"
fi

echo ""

# ============================================================================
# CHECK 10: Environment Variables
# ============================================================================

echo "## Check 10: Environment Variables"
echo ""

if [ -f ".env.example" ]; then
    pass ".env.example exists (good for documentation)"
else
    warn ".env.example not found"
fi

if [ -f ".env" ]; then
    pass ".env file exists (contains actual secrets)"

    # Verify it's not tracked by git
    if git check-ignore .env >/dev/null 2>&1; then
        pass ".env is properly gitignored"
    else
        fail ".env exists but is NOT gitignored - SECURITY RISK!"
        echo "   Fix with: echo '.env' >> .gitignore"
    fi
else
    warn ".env file not found (may need to create from .env.example)"
fi

echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "════════════════════════════════════════════════════════════════"
echo "## Validation Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${GREEN}✅ PASS${NC}: $PASS checks"
echo -e "${YELLOW}⚠️  WARN${NC}: $WARN checks"
echo -e "${RED}❌ FAIL${NC}: $FAIL checks"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}❌ VALIDATION FAILED${NC}: $FAIL critical issues found"
    echo "   Fix critical issues and run validation again"
    exit 1
elif [ "$WARN" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  VALIDATION PASSED WITH WARNINGS${NC}: $WARN warnings"
    echo "   Consider addressing warnings for optimal setup"
    exit 0
else
    echo -e "${GREEN}✅ VALIDATION PASSED${NC}: All checks successful!"
    echo "   Claude Code setup is correctly configured"
    exit 0
fi
