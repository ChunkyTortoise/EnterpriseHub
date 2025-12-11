# Skills Cleanup & Organization Plan

## Problem

You currently have:
- 62 total skills across 3 repos
- 12 duplicate skills (same skill in 2 repos)
- Skills scattered across 3 directories
- No clear way to know which skills to use

## Solution

Consolidate into a single, organized structure with no duplicates.

## Step 1: Remove Duplicate Skills

Delete these 12 duplicate skills from `awesome-claude-skills` (keep the official `anthropics/skills` version):

```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows/awesome-claude-skills

# Remove duplicates
rm -rf brand-guidelines
rm -rf canvas-design
rm -rf document-skills/docx
rm -rf internal-comms
rm -rf mcp-builder
rm -rf document-skills/pdf
rm -rf document-skills/pptx
rm -rf skill-creator
rm -rf slack-gif-creator
rm -rf theme-factory
rm -rf webapp-testing
rm -rf document-skills/xlsx
```

After cleanup: **50 unique skills** (27 → 15 in awesome-claude-skills)

## Step 2: Create Organized Structure

Create a new consolidated skills directory:

```
~/.claude/skills/                    # Personal skills (auto-discovered)
├── core/                            # Essential daily-use skills
│   ├── test-driven-development@     # symlink to superpowers
│   ├── systematic-debugging@
│   ├── brainstorming@
│   ├── writing-plans@
│   └── executing-plans@
├── documents/                       # Document processing
│   ├── docx@                        # symlink to anthropics/skills
│   ├── pdf@
│   ├── pptx@
│   ├── xlsx@
│   └── doc-coauthoring@
├── content/                         # Writing & content
│   ├── content-research-writer@     # symlink to awesome-claude-skills
│   └── internal-comms@
└── tools/                           # Utilities
    ├── skill-creator@
    └── file-organizer@
```

## Step 3: Create Symlink Script

```bash
#!/bin/bash
# symlink-essential-skills.sh

WORKFLOWS="/Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows"
SKILLS_HOME="$HOME/.claude/skills"

# Create directory structure
mkdir -p "$SKILLS_HOME"/{core,documents,content,tools}

# Core development skills (obra/superpowers)
ln -sf "$WORKFLOWS/superpowers/skills/test-driven-development" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/systematic-debugging" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/brainstorming" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/writing-plans" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/executing-plans" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/requesting-code-review" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/receiving-code-review" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/finishing-a-development-branch" "$SKILLS_HOME/core/"
ln -sf "$WORKFLOWS/superpowers/skills/verification-before-completion" "$SKILLS_HOME/core/"

# Document processing (anthropics/skills)
ln -sf "$WORKFLOWS/skills/skills/docx" "$SKILLS_HOME/documents/"
ln -sf "$WORKFLOWS/skills/skills/pdf" "$SKILLS_HOME/documents/"
ln -sf "$WORKFLOWS/skills/skills/pptx" "$SKILLS_HOME/documents/"
ln -sf "$WORKFLOWS/skills/skills/xlsx" "$SKILLS_HOME/documents/"
ln -sf "$WORKFLOWS/skills/skills/doc-coauthoring" "$SKILLS_HOME/documents/"

# Content & writing
ln -sf "$WORKFLOWS/awesome-claude-skills/content-research-writer" "$SKILLS_HOME/content/"
ln -sf "$WORKFLOWS/skills/skills/internal-comms" "$SKILLS_HOME/content/"

# Tools
ln -sf "$WORKFLOWS/skills/skills/skill-creator" "$SKILLS_HOME/tools/"
ln -sf "$WORKFLOWS/awesome-claude-skills/file-organizer" "$SKILLS_HOME/tools/"

echo "✓ Created ~/.claude/skills/ with 19 essential skills"
```

## Step 4: Verification

After running the script:

```bash
# Check structure
tree -L 2 ~/.claude/skills/

# Should show:
# ~/.claude/skills/
# ├── core/                (9 skills)
# ├── documents/           (5 skills)
# ├── content/             (2 skills)
# └── tools/               (2 skills)
```

## Benefits

1. **No duplicates** - Clean, single source of truth
2. **Auto-discovery** - Claude finds skills in `~/.claude/skills/`
3. **Easy to manage** - Symlinks keep original repos intact
4. **Organized** - Clear categories for different use cases
5. **Minimal** - Only 19 essential skills (not 62)
6. **Scalable** - Easy to add more skills as needed

## Storage Savings

- **Before**: 62 skills across 3 scattered directories
- **After**: 19 symlinks organized in 4 categories
- **Reduction**: 69% fewer skills to manage

## What About the Other Skills?

All 62 skills remain in `.agent/workflows/` for reference. You can:
- Browse the full catalog in `SKILLS_CATALOG.md`
- Add more symlinks when needed
- Use skills without symlinking (just reference the path)

## Next Action

Run the cleanup and symlink script:

```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows
bash CLEANUP_PLAN.md  # Extract and run the commands
```
