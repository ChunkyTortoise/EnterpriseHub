#!/bin/bash

# Install a skill from the local awesome-claude-skills directory

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Find the correct Claude skills directory
find_claude_skills_dir() {
    local dirs=(
        "$HOME/.config/claude-code/skills"
        "$HOME/.claude/skills"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$(dirname "$dir")" ]; then
            echo "$dir"
            return 0
        fi
    done
    
    echo "$HOME/.config/claude-code/skills"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SOURCE_DIR="$SCRIPT_DIR/awesome-claude-skills"
SKILLS_TARGET_DIR="$(find_claude_skills_dir)"

if [ $# -lt 1 ]; then
    print_error "Usage: $0 <SKILL_NAME>"
    echo ""
    print_info "Available skills in awesome-claude-skills:"
    echo ""
    if [ -d "$SKILLS_SOURCE_DIR" ]; then
        for skill_dir in "$SKILLS_SOURCE_DIR"/*; do
            if [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ]; then
                skill_name=$(basename "$skill_dir")
                echo "  - $skill_name"
            fi
        done
    else
        print_error "awesome-claude-skills directory not found at: $SKILLS_SOURCE_DIR"
    fi
    exit 1
fi

SKILL_NAME="$1"
SKILL_SOURCE="$SKILLS_SOURCE_DIR/$SKILL_NAME"
SKILL_TARGET="$SKILLS_TARGET_DIR/$SKILL_NAME"

if [ ! -d "$SKILL_SOURCE" ]; then
    print_error "Skill '$SKILL_NAME' not found in $SKILLS_SOURCE_DIR"
    exit 1
fi

if [ ! -f "$SKILL_SOURCE/SKILL.md" ]; then
    print_warning "No SKILL.md found in $SKILL_SOURCE"
fi

print_info "Installing skill: $SKILL_NAME"
print_info "From: $SKILL_SOURCE"
print_info "To: $SKILL_TARGET"
echo ""

mkdir -p "$SKILLS_TARGET_DIR"

if [ -d "$SKILL_TARGET" ]; then
    print_warning "Skill already exists at $SKILL_TARGET"
    read -p "Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Installation cancelled."
        exit 0
    fi
    rm -rf "$SKILL_TARGET"
fi

cp -R "$SKILL_SOURCE" "$SKILL_TARGET"
print_info "✓ Skill installed successfully!"
echo ""
print_info "Next steps:"
echo "  1. Start Claude Code: claude"
echo "  2. The skill '$SKILL_NAME' should now be available"
echo ""






