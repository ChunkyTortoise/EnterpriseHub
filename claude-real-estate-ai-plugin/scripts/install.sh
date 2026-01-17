#!/bin/bash
# Claude Real Estate AI Accelerator - Installation Script
# Version: 4.0.0
# Last Updated: 2026-01-16

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Version requirements
MIN_PYTHON_VERSION="3.11"
MIN_NODE_VERSION="18.0.0"
MIN_CLAUDE_CODE_VERSION="2.1.0"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Claude Real Estate AI Accelerator - Installation         ║${NC}"
echo -e "${BLUE}║  Version 4.0.0                                             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to compare versions
version_gt() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1";
}

# Check Python version
echo -e "${YELLOW}[1/7]${NC} Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "      Found Python ${PYTHON_VERSION}"

    if version_gt $MIN_PYTHON_VERSION $PYTHON_VERSION; then
        echo -e "${RED}✗${NC} Python ${MIN_PYTHON_VERSION}+ required, found ${PYTHON_VERSION}"
        exit 1
    else
        echo -e "${GREEN}✓${NC} Python version OK"
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found. Please install Python ${MIN_PYTHON_VERSION}+"
    exit 1
fi

# Check Node.js version (optional but recommended)
echo -e "${YELLOW}[2/7]${NC} Checking Node.js version (optional)..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo -e "      Found Node.js ${NODE_VERSION}"

    if version_gt $MIN_NODE_VERSION $NODE_VERSION; then
        echo -e "${YELLOW}⚠${NC}  Node.js ${MIN_NODE_VERSION}+ recommended, found ${NODE_VERSION}"
    else
        echo -e "${GREEN}✓${NC} Node.js version OK"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Node.js not found (optional for some features)"
fi

# Check Claude Code CLI
echo -e "${YELLOW}[3/7]${NC} Checking Claude Code CLI..."
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || echo "unknown")
    echo -e "      Found Claude Code ${CLAUDE_VERSION}"

    if [ "$CLAUDE_VERSION" != "unknown" ]; then
        if version_gt $MIN_CLAUDE_CODE_VERSION $CLAUDE_VERSION; then
            echo -e "${RED}✗${NC} Claude Code ${MIN_CLAUDE_CODE_VERSION}+ required, found ${CLAUDE_VERSION}"
            echo -e "      Update with: npm install -g @anthropic/claude-code"
            exit 1
        else
            echo -e "${GREEN}✓${NC} Claude Code version OK"
        fi
    else
        echo -e "${YELLOW}⚠${NC}  Could not determine Claude Code version"
    fi
else
    echo -e "${RED}✗${NC} Claude Code CLI not found"
    echo -e "      Install with: npm install -g @anthropic/claude-code"
    exit 1
fi

# Install Python dependencies
echo -e "${YELLOW}[4/7]${NC} Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet || {
        echo -e "${RED}✗${NC} Failed to install Python dependencies"
        exit 1
    }
    echo -e "${GREEN}✓${NC} Python dependencies installed"
else
    echo -e "${YELLOW}⚠${NC}  No requirements.txt found (skipping)"
fi

# Create necessary directories
echo -e "${YELLOW}[5/7]${NC} Creating plugin directories..."
mkdir -p .claude/metrics
mkdir -p .claude/logs
chmod +x hooks/test-hooks.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
echo -e "${GREEN}✓${NC} Directories created"

# Validate plugin structure
echo -e "${YELLOW}[6/7]${NC} Validating plugin structure..."

# Check for required files
REQUIRED_FILES=(
    ".claude-plugin/plugin.json"
    "README.md"
    "LICENSE"
    "CHANGELOG.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗${NC} Required file missing: $file"
        exit 1
    fi
done

# Count components
SKILL_COUNT=$(find skills -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
AGENT_COUNT=$(find agents -name "*.md" -not -name "README.md" 2>/dev/null | wc -l | tr -d ' ')
HOOK_COUNT=$(grep -c "^  - name:" hooks/hooks.yaml 2>/dev/null || echo "0")

echo -e "      Skills: ${SKILL_COUNT}"
echo -e "      Agents: ${AGENT_COUNT}"
echo -e "      Hooks: ${HOOK_COUNT}"

if [ "$SKILL_COUNT" -lt 20 ]; then
    echo -e "${YELLOW}⚠${NC}  Expected 27+ skills, found ${SKILL_COUNT}"
fi

echo -e "${GREEN}✓${NC} Plugin structure validated"

# Run validation script
echo -e "${YELLOW}[7/7]${NC} Running comprehensive validation..."
if [ -f "scripts/validate-plugin.sh" ]; then
    chmod +x scripts/validate-plugin.sh
    if ./scripts/validate-plugin.sh --quiet; then
        echo -e "${GREEN}✓${NC} Plugin validation passed"
    else
        echo -e "${YELLOW}⚠${NC}  Some validation warnings (plugin should still work)"
    fi
else
    echo -e "${YELLOW}⚠${NC}  Validation script not found (skipping)"
fi

# Installation summary
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Installation Complete!                                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Plugin Stats:${NC}"
echo -e "  • Skills:        ${SKILL_COUNT}"
echo -e "  • Agents:        ${AGENT_COUNT}"
echo -e "  • Hooks:         ${HOOK_COUNT}"
echo -e "  • MCP Profiles:  3"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Review README.md for usage instructions"
echo -e "  2. Check examples/ directory for code samples"
echo -e "  3. Activate a skill: ${GREEN}invoke test-driven-development${NC}"
echo -e "  4. View skill catalog: ${GREEN}cat skills/MANIFEST.yaml${NC}"
echo ""
echo -e "${BLUE}Quick Start Examples:${NC}"
echo -e "  • TDD Workflow:       ${GREEN}invoke test-driven-development${NC}"
echo -e "  • Deploy to Railway:  ${GREEN}invoke railway-deploy${NC}"
echo -e "  • Create UI Component:${GREEN}invoke streamlit-component-builder${NC}"
echo -e "  • Optimize Costs:     ${GREEN}invoke cost-optimization-analyzer${NC}"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo -e "  • Plugin README:      ${GREEN}README.md${NC}"
echo -e "  • Skill Reference:    ${GREEN}skills/README.md${NC}"
echo -e "  • Agent Reference:    ${GREEN}agents/README.md${NC}"
echo -e "  • Hooks Guide:        ${GREEN}hooks/README.md${NC}"
echo ""
echo -e "${YELLOW}Support:${NC}"
echo -e "  • Issues:  https://github.com/enterprisehub/claude-real-estate-ai-plugin/issues"
echo -e "  • Discord: https://discord.gg/real-estate-ai-devs"
echo ""
echo -e "${GREEN}Happy coding with Claude! 🚀${NC}"
