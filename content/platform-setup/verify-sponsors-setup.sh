#!/bin/bash
# GitHub Sponsors Setup Verification Script
# Run this after completing manual setup to verify everything is configured correctly

set -e

GITHUB_USER="ChunkyTortoise"
SPONSORS_URL="https://github.com/sponsors/$GITHUB_USER"
PROFILE_API="https://api.github.com/users/$GITHUB_USER"

echo "================================================"
echo "GitHub Sponsors Setup Verification"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: Verify GitHub profile exists
echo "1. Checking GitHub profile..."
if curl -s "$PROFILE_API" | grep -q "\"login\":\"$GITHUB_USER\""; then
    echo -e "${GREEN}✓${NC} GitHub profile found: $GITHUB_USER"
else
    echo -e "${RED}✗${NC} GitHub profile not found: $GITHUB_USER"
    exit 1
fi
echo ""

# Check 2: Check if Sponsors page is accessible
echo "2. Checking Sponsors page accessibility..."
SPONSORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$SPONSORS_URL")
if [ "$SPONSORS_STATUS" = "200" ]; then
    echo -e "${GREEN}✓${NC} Sponsors page is live: $SPONSORS_URL"
elif [ "$SPONSORS_STATUS" = "404" ]; then
    echo -e "${YELLOW}⚠${NC} Sponsors page not yet published (404)"
    echo "  Complete manual setup at: https://github.com/sponsors"
else
    echo -e "${YELLOW}⚠${NC} Sponsors page status: $SPONSORS_STATUS"
fi
echo ""

# Check 3: Verify FUNDING.yml exists in target repos
echo "3. Checking FUNDING.yml in repositories..."
REPOS=("ai-orchestrator" "docqa-engine" "insight-engine" "EnterpriseHub")
FUNDING_FOUND=0

for repo in "${REPOS[@]}"; do
    REPO_PATH="../../../$repo"
    if [ -d "$REPO_PATH" ]; then
        if [ -f "$REPO_PATH/.github/FUNDING.yml" ]; then
            if grep -q "github: $GITHUB_USER" "$REPO_PATH/.github/FUNDING.yml"; then
                echo -e "  ${GREEN}✓${NC} $repo has FUNDING.yml"
                ((FUNDING_FOUND++))
            else
                echo -e "  ${YELLOW}⚠${NC} $repo FUNDING.yml exists but missing 'github: $GITHUB_USER'"
            fi
        else
            echo -e "  ${RED}✗${NC} $repo missing .github/FUNDING.yml"
            echo "     Run: mkdir -p $REPO_PATH/.github && cp FUNDING.yml $REPO_PATH/.github/"
        fi
    else
        echo -e "  ${YELLOW}⚠${NC} $repo not found at $REPO_PATH (may be in different location)"
    fi
done
echo ""

# Check 4: Verify SPONSORS.md exists in target repos
echo "4. Checking SPONSORS.md in repositories..."
SPONSORS_MD_FOUND=0

for repo in "${REPOS[@]}"; do
    REPO_PATH="../../../$repo"
    if [ -d "$REPO_PATH" ]; then
        if [ -f "$REPO_PATH/SPONSORS.md" ]; then
            echo -e "  ${GREEN}✓${NC} $repo has SPONSORS.md"
            ((SPONSORS_MD_FOUND++))
        else
            echo -e "  ${RED}✗${NC} $repo missing SPONSORS.md"
            echo "     Run: cp SPONSORS.md $REPO_PATH/"
        fi
    fi
done
echo ""

# Check 5: Check README.md for sponsor badges
echo "5. Checking README.md for sponsor badges..."
BADGE_FOUND=0

for repo in "${REPOS[@]}"; do
    REPO_PATH="../../../$repo"
    if [ -d "$REPO_PATH" ] && [ -f "$REPO_PATH/README.md" ]; then
        if grep -q "github.com/sponsors/$GITHUB_USER" "$REPO_PATH/README.md"; then
            echo -e "  ${GREEN}✓${NC} $repo README has sponsor badge"
            ((BADGE_FOUND++))
        else
            echo -e "  ${YELLOW}⚠${NC} $repo README missing sponsor badge"
            echo "     Add: [![Sponsor](https://img.shields.io/badge/Sponsor-$GITHUB_USER-blue?logo=github-sponsors)](https://github.com/sponsors/$GITHUB_USER)"
        fi
    fi
done
echo ""

# Summary
echo "================================================"
echo "Verification Summary"
echo "================================================"
echo -e "Sponsors page accessible: $([ "$SPONSORS_STATUS" = "200" ] && echo -e "${GREEN}YES${NC}" || echo -e "${RED}NO${NC}")"
echo -e "FUNDING.yml files: $FUNDING_FOUND / ${#REPOS[@]}"
echo -e "SPONSORS.md files: $SPONSORS_MD_FOUND / ${#REPOS[@]}"
echo -e "README badges: $BADGE_FOUND / ${#REPOS[@]}"
echo ""

# Next steps
echo "================================================"
echo "Next Steps"
echo "================================================"

if [ "$SPONSORS_STATUS" != "200" ]; then
    echo "1. Complete GitHub Sponsors setup:"
    echo "   → Follow: github-sponsors-setup-guide.md"
    echo "   → URL: https://github.com/sponsors"
fi

if [ $FUNDING_FOUND -lt ${#REPOS[@]} ]; then
    echo "2. Add FUNDING.yml to repositories:"
    echo "   → cp FUNDING.yml <repo>/.github/FUNDING.yml"
fi

if [ $SPONSORS_MD_FOUND -lt ${#REPOS[@]} ]; then
    echo "3. Add SPONSORS.md to repositories:"
    echo "   → cp SPONSORS.md <repo>/SPONSORS.md"
fi

if [ $BADGE_FOUND -lt ${#REPOS[@]} ]; then
    echo "4. Add sponsor badges to README files"
    echo "   → See: github-sponsors-assets.md"
fi

echo ""
echo "5. Announce launch:"
echo "   → LinkedIn (see github-sponsors-assets.md)"
echo "   → Twitter/X"
echo "   → Dev.to article"
echo ""

echo "For full setup instructions, see:"
echo "  github-sponsors-setup-guide.md"
echo ""
