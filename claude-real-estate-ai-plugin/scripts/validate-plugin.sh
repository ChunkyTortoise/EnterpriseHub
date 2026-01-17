#!/bin/bash
# validate-plugin.sh
# Validates Claude Code plugin structure, syntax, and metadata

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0
CHECKS=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
    ((CHECKS++))
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}❌${NC} $1"
    ((ERRORS++))
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Validate plugin.json
validate_plugin_json() {
    log_info "Validating .claude-plugin/plugin.json..."

    if [ ! -f ".claude-plugin/plugin.json" ]; then
        log_error "plugin.json not found"
        return 1
    fi

    # Check JSON syntax
    if ! jq empty .claude-plugin/plugin.json 2>/dev/null; then
        log_error "plugin.json has invalid JSON syntax"
        return 1
    fi

    # Check required fields
    local required_fields=("name" "version" "description" "license" "requires")
    for field in "${required_fields[@]}"; do
        if ! jq -e ".$field" .claude-plugin/plugin.json >/dev/null 2>&1; then
            log_error "plugin.json missing required field: $field"
        else
            log_success "plugin.json has field: $field"
        fi
    done

    # Validate version format (semver)
    local version=$(jq -r '.version' .claude-plugin/plugin.json)
    if ! [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        log_error "Invalid version format: $version (expected semver: X.Y.Z)"
    else
        log_success "Valid version format: $version"
    fi

    # Check keyword count (recommended 5-15)
    local keyword_count=$(jq -r '.keywords | length' .claude-plugin/plugin.json)
    if [ "$keyword_count" -lt 5 ]; then
        log_warning "Only $keyword_count keywords (recommended: 5-15)"
    elif [ "$keyword_count" -gt 15 ]; then
        log_warning "Too many keywords: $keyword_count (recommended: 5-15)"
    else
        log_success "Good keyword count: $keyword_count"
    fi

    return 0
}

# Validate skill structure
validate_skill() {
    local skill_path=$1
    local skill_name=$(basename "$skill_path")

    log_info "Validating skill: $skill_name"

    # Check for SKILL.md
    if [ ! -f "$skill_path/SKILL.md" ]; then
        log_error "$skill_name: Missing SKILL.md"
        return 1
    fi

    # Validate SKILL.md frontmatter
    if ! head -1 "$skill_path/SKILL.md" | grep -q "^---$"; then
        log_error "$skill_name: SKILL.md missing YAML frontmatter"
        return 1
    fi

    # Extract frontmatter
    local frontmatter=$(sed -n '/^---$/,/^---$/p' "$skill_path/SKILL.md" | sed '1d;$d')

    # Check required frontmatter fields
    local required_fields=("name" "description" "trigger" "model" "tools")
    for field in "${required_fields[@]}"; do
        if ! echo "$frontmatter" | grep -q "^$field:"; then
            log_error "$skill_name: Missing frontmatter field: $field"
        fi
    done

    # Check token budget (SKILL.md should be under 1000 tokens ~4000 chars)
    local skill_size=$(wc -c < "$skill_path/SKILL.md")
    if [ "$skill_size" -gt 4000 ]; then
        log_warning "$skill_name: SKILL.md is large ($skill_size bytes, recommend <4000)"
    else
        log_success "$skill_name: SKILL.md size OK ($skill_size bytes)"
    fi

    # Check for scripts directory
    if [ -d "$skill_path/scripts" ]; then
        local script_count=$(find "$skill_path/scripts" -type f -name "*.sh" -o -name "*.py" | wc -l)
        log_success "$skill_name: Has $script_count script(s)"

        # Validate script permissions
        find "$skill_path/scripts" -type f -name "*.sh" | while read script; do
            if [ ! -x "$script" ]; then
                log_warning "$skill_name: Script not executable: $(basename $script)"
            fi
        done
    fi

    # Check for reference directory
    if [ -d "$skill_path/reference" ]; then
        local ref_count=$(find "$skill_path/reference" -type f -name "*.md" | wc -l)
        log_success "$skill_name: Has $ref_count reference file(s)"
    fi

    # Check for examples
    if [ ! -f "$skill_path/README.md" ]; then
        log_warning "$skill_name: Missing README.md"
    fi

    return 0
}

# Validate all skills
validate_skills() {
    log_info "Validating skills..."

    if [ ! -d "skills" ]; then
        log_error "skills/ directory not found"
        return 1
    fi

    local skill_count=0
    find skills -mindepth 2 -maxdepth 2 -type d | while read skill_dir; do
        validate_skill "$skill_dir"
        ((skill_count++))
    done

    log_success "Validated skills in skills/ directory"
    return 0
}

# Validate agent definitions
validate_agent() {
    local agent_path=$1
    local agent_name=$(basename "$agent_path" .md)

    log_info "Validating agent: $agent_name"

    # Check frontmatter
    if ! head -1 "$agent_path" | grep -q "^---$"; then
        log_error "$agent_name: Missing YAML frontmatter"
        return 1
    fi

    # Extract frontmatter
    local frontmatter=$(sed -n '/^---$/,/^---$/p' "$agent_path" | sed '1d;$d')

    # Check required fields
    local required_fields=("name" "description" "tools" "model")
    for field in "${required_fields[@]}"; do
        if ! echo "$frontmatter" | grep -q "^$field:"; then
            log_error "$agent_name: Missing frontmatter field: $field"
        fi
    done

    log_success "$agent_name: Valid agent definition"
    return 0
}

# Validate all agents
validate_agents() {
    log_info "Validating agents..."

    if [ ! -d "agents" ]; then
        log_warning "agents/ directory not found (optional)"
        return 0
    fi

    find agents -type f -name "*.md" | while read agent_file; do
        validate_agent "$agent_file"
    done

    log_success "Validated agents in agents/ directory"
    return 0
}

# Validate hooks
validate_hooks() {
    log_info "Validating hooks..."

    if [ ! -d "hooks" ]; then
        log_warning "hooks/ directory not found (optional)"
        return 0
    fi

    # Check for hooks.yaml if it exists
    if [ -f "hooks/hooks.yaml" ]; then
        # Validate YAML syntax
        if command_exists yamllint; then
            if yamllint hooks/hooks.yaml >/dev/null 2>&1; then
                log_success "hooks.yaml has valid YAML syntax"
            else
                log_error "hooks.yaml has invalid YAML syntax"
            fi
        else
            log_warning "yamllint not installed, skipping YAML validation"
        fi
    fi

    # Check hook scripts are executable
    find hooks -type f -name "*.sh" | while read hook_script; do
        if [ ! -x "$hook_script" ]; then
            log_warning "Hook script not executable: $(basename $hook_script)"
        else
            log_success "Hook script executable: $(basename $hook_script)"
        fi
    done

    return 0
}

# Validate MCP profiles
validate_mcp_profiles() {
    log_info "Validating MCP profiles..."

    if [ ! -d "mcp-profiles" ]; then
        log_warning "mcp-profiles/ directory not found (optional)"
        return 0
    fi

    find mcp-profiles -type f -name "*.json" | while read profile; do
        if jq empty "$profile" 2>/dev/null; then
            log_success "Valid MCP profile: $(basename $profile)"
        else
            log_error "Invalid JSON in MCP profile: $(basename $profile)"
        fi
    done

    return 0
}

# Validate documentation
validate_documentation() {
    log_info "Validating documentation..."

    # Check required docs
    local required_docs=("README.md" "CONTRIBUTING.md" "LICENSE")
    for doc in "${required_docs[@]}"; do
        if [ ! -f "$doc" ]; then
            log_error "Missing required documentation: $doc"
        else
            log_success "Found required documentation: $doc"
        fi
    done

    # Check README completeness
    if [ -f "README.md" ]; then
        local readme_sections=("Overview" "Installation" "Quick Start" "Examples")
        for section in "${readme_sections[@]}"; do
            if grep -q "## $section" README.md; then
                log_success "README.md has section: $section"
            else
                log_warning "README.md missing recommended section: $section"
            fi
        done
    fi

    return 0
}

# Validate examples
validate_examples() {
    log_info "Validating examples..."

    if [ ! -d "examples" ]; then
        log_warning "examples/ directory not found (recommended)"
        return 0
    fi

    local example_count=$(find examples -type f -name "*.md" | wc -l)
    if [ "$example_count" -eq 0 ]; then
        log_warning "No example files found in examples/"
    else
        log_success "Found $example_count example file(s)"
    fi

    return 0
}

# Main validation
main() {
    echo "======================================"
    echo "Claude Code Plugin Validation"
    echo "======================================"
    echo ""

    # Change to plugin directory if specified
    if [ $# -gt 0 ]; then
        cd "$1"
        log_info "Validating plugin in: $(pwd)"
    fi

    # Check required commands
    if ! command_exists jq; then
        log_error "jq is required but not installed"
        exit 1
    fi

    # Run validations
    validate_plugin_json
    validate_skills
    validate_agents
    validate_hooks
    validate_mcp_profiles
    validate_documentation
    validate_examples

    # Summary
    echo ""
    echo "======================================"
    echo "Validation Summary"
    echo "======================================"
    echo -e "${GREEN}✅ Checks passed: $CHECKS${NC}"
    echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
    echo -e "${RED}❌ Errors: $ERRORS${NC}"
    echo ""

    # Exit code
    if [ "$ERRORS" -gt 0 ]; then
        echo -e "${RED}Validation failed with $ERRORS error(s)${NC}"
        exit 1
    elif [ "$WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}Validation passed with $WARNINGS warning(s)${NC}"
        exit 0
    else
        echo -e "${GREEN}Validation passed successfully!${NC}"
        exit 0
    fi
}

# Run main
main "$@"
