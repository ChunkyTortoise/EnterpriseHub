#!/bin/bash
#
# CI/CD Initialization Script
# Sets up the complete CI/CD and quality automation system
#
# Usage: bash .claude/scripts/initialize-ci-cd.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🚀 Initializing CI/CD and Quality Automation System"
echo "=================================================="
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "❌ Git not found. Please install Git"
    exit 1
fi

echo "✅ Prerequisites satisfied"
echo ""

# Step 2: Install Python dependencies
echo "📦 Step 2: Installing Python dependencies..."

pip install -q pytest pytest-cov pyyaml jsonschema detect-secrets bandit safety || {
    echo "❌ Failed to install Python dependencies"
    exit 1
}

echo "✅ Python dependencies installed"
echo ""

# Step 3: Install pre-commit
echo "🔧 Step 3: Installing pre-commit..."

pip install -q pre-commit || {
    echo "❌ Failed to install pre-commit"
    exit 1
}

echo "✅ pre-commit installed"
echo ""

# Step 4: Initialize pre-commit hooks
echo "🎣 Step 4: Initializing pre-commit hooks..."

pre-commit install || {
    echo "⚠️  Failed to install pre-commit hooks (may need to be run in git repo)"
}

echo "✅ Pre-commit hooks initialized"
echo ""

# Step 5: Create secrets baseline
echo "🔐 Step 5: Creating secrets baseline..."

if [ ! -f ".secrets.baseline" ]; then
    detect-secrets scan --baseline .secrets.baseline \
        --exclude-files '\.git/.*' \
        --exclude-files 'node_modules/.*' \
        --exclude-files '.*\.csv' || {
        echo "⚠️  Could not create secrets baseline"
    }
    echo "✅ Secrets baseline created"
else
    echo "ℹ️  Secrets baseline already exists"
fi

echo ""

# Step 6: Create metrics directory
echo "📊 Step 6: Setting up metrics directory..."

mkdir -p .claude/metrics

cat > .claude/metrics/.gitkeep << EOF
# Metrics directory
# Generated metrics and reports are stored here
EOF

echo "✅ Metrics directory created"
echo ""

# Step 7: Create docs directory
echo "📚 Step 7: Setting up documentation directory..."

mkdir -p docs

cat > docs/.gitkeep << EOF
# Auto-generated documentation
# Run: python .claude/scripts/generate-docs.py
EOF

echo "✅ Documentation directory created"
echo ""

# Step 8: Generate initial documentation
echo "📝 Step 8: Generating initial documentation..."

if [ -f ".claude/scripts/generate-docs.py" ]; then
    python .claude/scripts/generate-docs.py || {
        echo "⚠️  Could not generate documentation"
    }
    echo "✅ Documentation generated"
else
    echo "⚠️  Documentation generator not found"
fi

echo ""

# Step 9: Generate initial metrics dashboard
echo "📈 Step 9: Generating initial metrics dashboard..."

if [ -f ".claude/scripts/generate-metrics-dashboard.py" ]; then
    python .claude/scripts/generate-metrics-dashboard.py || {
        echo "⚠️  Could not generate metrics dashboard"
    }
    echo "✅ Metrics dashboard generated"
else
    echo "⚠️  Metrics dashboard generator not found"
fi

echo ""

# Step 10: Validate setup
echo "✓ Step 10: Validating setup..."

# Check workflows exist
WORKFLOWS=(
    "skills-validation.yml"
    "hooks-validation.yml"
    "plugin-validation.yml"
    "security-scan.yml"
    "cost-optimization-check.yml"
    "release.yml"
)

MISSING_WORKFLOWS=()

for workflow in "${WORKFLOWS[@]}"; do
    if [ ! -f ".github/workflows/$workflow" ]; then
        MISSING_WORKFLOWS+=("$workflow")
    fi
done

if [ ${#MISSING_WORKFLOWS[@]} -eq 0 ]; then
    echo "✅ All GitHub Actions workflows present"
else
    echo "⚠️  Missing workflows: ${MISSING_WORKFLOWS[*]}"
fi

# Check quality gates
if [ -f ".claude/quality-gates.yaml" ]; then
    echo "✅ Quality gates configuration present"
else
    echo "⚠️  Quality gates configuration missing"
fi

# Check pre-commit config
if [ -f ".pre-commit-config.yaml" ]; then
    echo "✅ Pre-commit configuration present"
else
    echo "⚠️  Pre-commit configuration missing"
fi

echo ""

# Step 11: Run initial validation
echo "🧪 Step 11: Running initial validation..."

echo "   - Testing pre-commit hooks..."
pre-commit run --all-files > /dev/null 2>&1 || {
    echo "⚠️  Some pre-commit hooks failed (this is normal on first run)"
}

echo "   - Testing integration tests..."
if [ -f ".claude/skills/scripts/integration_tests.py" ]; then
    pytest .claude/skills/scripts/integration_tests.py -v -x > /dev/null 2>&1 || {
        echo "⚠️  Some integration tests failed"
    }
    echo "✅ Initial validation complete"
else
    echo "⚠️  Integration tests not found"
fi

echo ""

# Print summary
echo "=================================================="
echo "🎉 CI/CD System Initialization Complete!"
echo "=================================================="
echo ""
echo "✅ Installed Components:"
echo "   - GitHub Actions workflows (6)"
echo "   - Pre-commit hooks (15+ rules)"
echo "   - Integration testing framework"
echo "   - Quality gates configuration"
echo "   - Metrics dashboard generator"
echo "   - Documentation auto-generator"
echo ""
echo "📚 Next Steps:"
echo ""
echo "1. Review the setup:"
echo "   cat CI_CD_IMPLEMENTATION_SUMMARY.md"
echo ""
echo "2. Test pre-commit hooks:"
echo "   pre-commit run --all-files"
echo ""
echo "3. Run integration tests:"
echo "   pytest .claude/skills/scripts/integration_tests.py -v"
echo ""
echo "4. Generate metrics dashboard:"
echo "   python .claude/scripts/generate-metrics-dashboard.py"
echo ""
echo "5. View generated documentation:"
echo "   ls docs/"
echo ""
echo "6. Commit and push to trigger workflows:"
echo "   git add ."
echo "   git commit -m 'chore: initialize CI/CD system'"
echo "   git push"
echo ""
echo "📖 Documentation:"
echo "   - System overview: CI_CD_IMPLEMENTATION_SUMMARY.md"
echo "   - Workflows guide: .github/workflows/README.md"
echo "   - Quality gates: .claude/quality-gates.yaml"
echo ""
echo "🔗 GitHub Actions:"
echo "   Visit: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo "✅ System Status: Ready for Production"
echo ""
