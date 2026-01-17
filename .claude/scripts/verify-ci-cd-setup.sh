#!/bin/bash
#
# CI/CD Setup Verification Script
# Verifies all components are correctly installed and configured
#
# Usage: bash .claude/scripts/verify-ci-cd-setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "🔍 CI/CD Setup Verification"
echo "=========================="
echo ""

cd "$PROJECT_ROOT"

PASS=0
WARN=0
FAIL=0

# Helper functions
check_pass() {
    echo "✅ $1"
    ((PASS++))
}

check_warn() {
    echo "⚠️  $1"
    ((WARN++))
}

check_fail() {
    echo "❌ $1"
    ((FAIL++))
}

# 1. Check GitHub Actions workflows
echo "📋 Checking GitHub Actions Workflows..."

WORKFLOWS=(
    "skills-validation.yml"
    "hooks-validation.yml"
    "plugin-validation.yml"
    "security-scan.yml"
    "cost-optimization-check.yml"
    "release.yml"
)

for workflow in "${WORKFLOWS[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        check_pass "Workflow: $workflow"
    else
        check_fail "Missing workflow: $workflow"
    fi
done

echo ""

# 2. Check pre-commit configuration
echo "🎣 Checking Pre-commit Configuration..."

if [ -f ".pre-commit-config.yaml" ]; then
    check_pass "Pre-commit config exists"

    # Validate YAML
    if python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))" 2>/dev/null; then
        check_pass "Pre-commit config is valid YAML"
    else
        check_fail "Pre-commit config has invalid YAML"
    fi

    # Check if pre-commit is installed
    if command -v pre-commit &> /dev/null; then
        check_pass "pre-commit command available"

        # Check if hooks are installed
        if [ -f ".git/hooks/pre-commit" ]; then
            check_pass "Pre-commit hooks installed"
        else
            check_warn "Pre-commit hooks not installed (run: pre-commit install)"
        fi
    else
        check_warn "pre-commit not installed (run: pip install pre-commit)"
    fi
else
    check_fail "Pre-commit config missing"
fi

echo ""

# 3. Check quality gates
echo "🎯 Checking Quality Gates Configuration..."

if [ -f ".claude/quality-gates.yaml" ]; then
    check_pass "Quality gates file exists"

    # Validate YAML
    if python -c "import yaml; yaml.safe_load(open('.claude/quality-gates.yaml'))" 2>/dev/null; then
        check_pass "Quality gates is valid YAML"
    else
        check_fail "Quality gates has invalid YAML"
    fi
else
    check_fail "Quality gates missing"
fi

echo ""

# 4. Check skills integration tests
echo "🧪 Checking Integration Tests..."

if [ -f ".claude/skills/scripts/integration_tests.py" ]; then
    check_pass "Integration tests exist"

    # Try to import the test file
    if python -c "import sys; sys.path.insert(0, '.claude/skills/scripts'); import integration_tests" 2>/dev/null; then
        check_pass "Integration tests are valid Python"
    else
        check_warn "Integration tests may have import issues"
    fi
else
    check_fail "Integration tests missing"
fi

echo ""

# 5. Check automation scripts
echo "🔧 Checking Automation Scripts..."

SCRIPTS=(
    "generate-metrics-dashboard.py"
    "generate-docs.py"
    "initialize-ci-cd.sh"
    "verify-ci-cd-setup.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f ".claude/scripts/$script" ]; then
        if [ -x ".claude/scripts/$script" ]; then
            check_pass "Script: $script (executable)"
        else
            check_warn "Script: $script (not executable)"
        fi
    else
        check_fail "Missing script: $script"
    fi
done

echo ""

# 6. Check directory structure
echo "📁 Checking Directory Structure..."

DIRECTORIES=(
    ".github/workflows"
    ".claude/skills"
    ".claude/hooks"
    ".claude/scripts"
    ".claude/metrics"
    "docs"
)

for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Directory: $dir"
    else
        check_warn "Missing directory: $dir"
    fi
done

echo ""

# 7. Check Python dependencies
echo "🐍 Checking Python Dependencies..."

PYTHON_DEPS=(
    "pytest"
    "yaml"
    "json"
)

for dep in "${PYTHON_DEPS[@]}"; do
    if python -c "import $dep" 2>/dev/null; then
        check_pass "Python module: $dep"
    else
        check_warn "Missing Python module: $dep"
    fi
done

echo ""

# 8. Check documentation
echo "📚 Checking Documentation..."

DOCS=(
    "CI_CD_IMPLEMENTATION_SUMMARY.md"
    ".github/workflows/README.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        check_pass "Documentation: $doc"
    else
        check_warn "Missing documentation: $doc"
    fi
done

echo ""

# 9. Check generated artifacts
echo "📊 Checking Generated Artifacts..."

if [ -d "docs" ] && [ "$(ls -A docs)" ]; then
    check_pass "Documentation generated"
else
    check_warn "No generated documentation (run: python .claude/scripts/generate-docs.py)"
fi

if [ -d ".claude/metrics" ] && [ "$(ls -A .claude/metrics)" ]; then
    check_pass "Metrics directory has content"
else
    check_warn "No metrics generated (run: python .claude/scripts/generate-metrics-dashboard.py)"
fi

echo ""

# 10. Test key functionality
echo "🧪 Testing Key Functionality..."

# Test MANIFEST.yaml loading
if python -c "import yaml; yaml.safe_load(open('.claude/skills/MANIFEST.yaml'))" 2>/dev/null; then
    check_pass "MANIFEST.yaml loads correctly"
else
    check_fail "MANIFEST.yaml has issues"
fi

# Test quality-gates.yaml loading
if python -c "import yaml; yaml.safe_load(open('.claude/quality-gates.yaml'))" 2>/dev/null; then
    check_pass "quality-gates.yaml loads correctly"
else
    check_fail "quality-gates.yaml has issues"
fi

echo ""

# Print summary
echo "=================================================="
echo "📊 Verification Summary"
echo "=================================================="
echo ""
echo "✅ Passed:  $PASS"
echo "⚠️  Warnings: $WARN"
echo "❌ Failed:  $FAIL"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo "🎉 Perfect! All checks passed."
    echo ""
    echo "✅ System Status: Fully Operational"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo "✅ System Status: Operational with warnings"
    echo ""
    echo "⚠️  Please review warnings above"
    exit 0
else
    echo "⚠️  System Status: Issues detected"
    echo ""
    echo "Please fix the failed checks above"
    exit 1
fi
