#!/bin/bash
set -e

WORKFLOWS="/Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows"
SKILLS_HOME="$HOME/.claude/skills"

echo "========================================="
echo "Claude Skills Organization Script"
echo "========================================="
echo ""

# Step 1: Remove duplicates from awesome-claude-skills
echo "Step 1: Removing duplicate skills from awesome-claude-skills..."
cd "$WORKFLOWS/awesome-claude-skills"

rm -rf brand-guidelines 2>/dev/null || true
rm -rf canvas-design 2>/dev/null || true
rm -rf document-skills/docx 2>/dev/null || true
rm -rf internal-comms 2>/dev/null || true
rm -rf mcp-builder 2>/dev/null || true
rm -rf document-skills/pdf 2>/dev/null || true
rm -rf document-skills/pptx 2>/dev/null || true
rm -rf skill-creator 2>/dev/null || true
rm -rf slack-gif-creator 2>/dev/null || true
rm -rf theme-factory 2>/dev/null || true
rm -rf webapp-testing 2>/dev/null || true
rm -rf document-skills/xlsx 2>/dev/null || true

echo "✓ Removed 12 duplicate skills"
echo ""

# Step 2: Create organized directory structure
echo "Step 2: Creating organized skill directories..."
mkdir -p "$SKILLS_HOME"/{core,documents,content,tools}
echo "✓ Created ~/.claude/skills/ directory structure"
echo ""

# Step 3: Symlink essential skills
echo "Step 3: Symlinking essential skills..."

# Core development skills (obra/superpowers)
echo "  - Linking core development skills (9)..."
ln -sf "$WORKFLOWS/superpowers/skills/test-driven-development" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/systematic-debugging" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/brainstorming" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/writing-plans" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/executing-plans" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/requesting-code-review" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/receiving-code-review" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/finishing-a-development-branch" "$SKILLS_HOME/core/" 2>/dev/null || true
ln -sf "$WORKFLOWS/superpowers/skills/verification-before-completion" "$SKILLS_HOME/core/" 2>/dev/null || true

# Document processing (anthropics/skills)
echo "  - Linking document processing skills (5)..."
ln -sf "$WORKFLOWS/skills/skills/docx" "$SKILLS_HOME/documents/" 2>/dev/null || true
ln -sf "$WORKFLOWS/skills/skills/pdf" "$SKILLS_HOME/documents/" 2>/dev/null || true
ln -sf "$WORKFLOWS/skills/skills/pptx" "$SKILLS_HOME/documents/" 2>/dev/null || true
ln -sf "$WORKFLOWS/skills/skills/xlsx" "$SKILLS_HOME/documents/" 2>/dev/null || true
ln -sf "$WORKFLOWS/skills/skills/doc-coauthoring" "$SKILLS_HOME/documents/" 2>/dev/null || true

# Content & writing
echo "  - Linking content & writing skills (2)..."
ln -sf "$WORKFLOWS/awesome-claude-skills/content-research-writer" "$SKILLS_HOME/content/" 2>/dev/null || true
ln -sf "$WORKFLOWS/skills/skills/internal-comms" "$SKILLS_HOME/content/" 2>/dev/null || true

# Tools
echo "  - Linking productivity tools (2)..."
ln -sf "$WORKFLOWS/skills/skills/skill-creator" "$SKILLS_HOME/tools/" 2>/dev/null || true
ln -sf "$WORKFLOWS/awesome-claude-skills/file-organizer" "$SKILLS_HOME/tools/" 2>/dev/null || true

echo "✓ Created 18 symlinks"
echo ""

# Step 4: Verification
echo "Step 4: Verifying installation..."
echo ""
echo "Skill count by category:"
echo "  - Core development: $(ls -1 "$SKILLS_HOME/core" 2>/dev/null | wc -l | xargs)"
echo "  - Document processing: $(ls -1 "$SKILLS_HOME/documents" 2>/dev/null | wc -l | xargs)"
echo "  - Content & writing: $(ls -1 "$SKILLS_HOME/content" 2>/dev/null | wc -l | xargs)"
echo "  - Productivity tools: $(ls -1 "$SKILLS_HOME/tools" 2>/dev/null | wc -l | xargs)"
echo ""

TOTAL=$(find "$SKILLS_HOME" -maxdepth 2 -type l 2>/dev/null | wc -l | xargs)
echo "Total skills installed: $TOTAL"
echo ""

echo "========================================="
echo "✓ Skills organization complete!"
echo "========================================="
echo ""
echo "Skills are now available in: ~/.claude/skills/"
echo ""
echo "View the full catalog:"
echo "  cat $WORKFLOWS/SKILLS_CATALOG.md"
echo ""
echo "To add more skills, edit this script or create symlinks manually:"
echo "  ln -sf $WORKFLOWS/superpowers/skills/<skill-name> ~/.claude/skills/core/"
