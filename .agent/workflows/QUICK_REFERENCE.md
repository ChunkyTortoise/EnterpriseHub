# Claude Skills - Quick Reference Card

## Your Organized Skills (18 total)

### 🔥 Core Development (9 skills)
Daily workflow for software development

- `test-driven-development` - Write test first, then implement
- `systematic-debugging` - 4-phase root cause analysis
- `brainstorming` - Refine ideas before coding
- `writing-plans` - Create detailed implementation tasks
- `executing-plans` - Execute plans in controlled batches
- `requesting-code-review` - Pre-review checklist
- `receiving-code-review` - Handle feedback effectively
- `finishing-a-development-branch` - Merge/PR workflow
- `verification-before-completion` - Validate before claiming done

### 📄 Documents (5 skills)
Professional document manipulation

- `docx` - Word docs with tracked changes
- `pdf` - Extract, merge, annotate PDFs
- `pptx` - Create/edit presentations
- `xlsx` - Spreadsheets with formulas
- `doc-coauthoring` - Collaborative writing workflow

### ✍️ Content & Writing (2 skills)
Research and write quality content

- `content-research-writer` - Research, citations, voice preservation
- `internal-comms` - Company communications (3P updates, newsletters)

### 🛠️ Tools (2 skills)
Productivity utilities

- `skill-creator` - Create new custom skills
- `file-organizer` - Intelligently organize files

## How to Use Skills

Skills are auto-discovered from `~/.claude/skills/`. Claude will automatically use them when relevant.

## Quick Stats

- **Before**: 62 skills across 3 scattered directories
- **After**: 18 essential skills in 4 organized categories
- **Duplicates removed**: 12
- **Storage**: All 62 skills still available in `.agent/workflows/`

## Full Documentation

- **Complete catalog**: `SKILLS_CATALOG.md` (all 50 unique skills)
- **Cleanup details**: `CLEANUP_PLAN.md`
- **This reference**: `QUICK_REFERENCE.md`

## Add More Skills

```bash
# Example: Add subagent-driven-development to core
ln -sf /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows/superpowers/skills/subagent-driven-development ~/.claude/skills/core/

# Example: Add web-artifacts-builder to tools
ln -sf /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows/skills/skills/web-artifacts-builder ~/.claude/skills/tools/
```

## About Text Humanization

**No dedicated skill found**, but you can:
1. **Ask me directly** - I excel at humanizing text naturally
2. **Use prompts** - See the web search results for effective prompts
3. **Create custom skill** - Use `skill-creator` to build one

Just paste any text and ask me to "make it more human" or "write this in a conversational tone".
