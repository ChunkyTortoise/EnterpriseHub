# How to Use Your Claude Skills

## Current Setup Status

✅ **Your skills ARE set up correctly!**

You have 18 skills organized in `~/.claude/skills/`:
```
~/.claude/skills/
├── core/           (9 development workflow skills)
├── documents/      (5 document processing skills)
├── content/        (2 writing skills)
└── tools/          (2 utility skills)
```

## How Skills Work

### Automatic Discovery
Claude **automatically discovers and loads** skills from `~/.claude/skills/`. You don't need to manually activate them.

### When Skills Activate
Skills activate **automatically based on context**. Claude reads each skill's `description` field to determine when to use it.

For example:
- **test-driven-development** - Activates "when implementing any feature or bugfix"
- **docx** - Activates "when Claude needs to work with Word documents"
- **content-research-writer** - Activates "when writing high-quality content"

### How to Use Skills

**Method 1: Just ask naturally**
```
"Create a Word document with our Q4 report"
→ Claude automatically uses the 'docx' skill

"Let's implement the login feature using TDD"
→ Claude automatically uses 'test-driven-development' skill

"Help me write a blog post about AI trends"
→ Claude automatically uses 'content-research-writer' skill
```

**Method 2: Explicitly mention the skill**
```
"Use the systematic-debugging skill to help me fix this error"
"Apply the brainstorming skill to this feature design"
"Use the pdf skill to extract tables from report.pdf"
```

## Alternative: Plugin Installation (Recommended for Superpowers)

Your current setup works, but for **obra/superpowers** specifically, the plugin method provides additional benefits:

### Install Superpowers as Plugin

```bash
# Add the marketplace
/plugin marketplace add obra/superpowers-marketplace

# Install superpowers
/plugin install superpowers@superpowers-marketplace

# Verify
/help
# Should show: /superpowers:brainstorm, /superpowers:write-plan, etc.
```

### Benefits of Plugin Installation
- Slash commands (like `/superpowers:brainstorm`)
- Automatic workflow integration
- Better coordination between related skills
- Updates via `/plugin update`

### Install Anthropic Skills as Plugin

```bash
# Add marketplace
/plugin marketplace add anthropics/skills

# Install document skills
/plugin install document-skills@anthropic-agent-skills

# Or install example skills
/plugin install example-skills@anthropic-agent-skills
```

## Current Setup vs Plugin Installation

| Method | Your Current Setup | Plugin Installation |
|--------|-------------------|---------------------|
| **Skills location** | `~/.claude/skills/` symlinks | Managed by plugin system |
| **Discovery** | Automatic | Automatic |
| **Usage** | Natural language or mention | Natural language + slash commands |
| **Updates** | Manual (git pull) | `/plugin update` |
| **Coordination** | Individual skills | Workflow integration |
| **Best for** | Individual skills, flexibility | Complete workflows, convenience |

## Recommendation

**Keep your current setup** for now, but consider:

1. **For superpowers**: Install as plugin for the complete workflow experience
   ```bash
   /plugin install superpowers@superpowers-marketplace
   ```

2. **For anthropics skills**: Your symlinks work fine, or install as plugin for easier updates

3. **For awesome-claude-skills**: Keep as symlinks (they're individual utility skills)

## Testing Your Skills

Try these commands to verify skills are working:

```bash
# Test TDD skill
"I need to add a new calculateTotal function. Let's use TDD."

# Test docx skill
"Create a Word document with a title page"

# Test content-research-writer skill
"Help me write a blog post about Python type hints"

# Test brainstorming skill
"I want to build a feature that lets users export data. Help me brainstorm the design."
```

Claude should automatically recognize the context and activate the appropriate skill.

## Checking What Skills Are Loaded

Unfortunately, there's no built-in command to list loaded skills, but you can:

```bash
# List your installed skills
ls -1 ~/.claude/skills/*/ | grep "/$" | sed 's|.*/||' | sed 's|/||'

# Check a specific skill
cat ~/.claude/skills/core/test-driven-development/SKILL.md | head -20
```

## Adding More Skills

To add any of the other 32 skills from your repos:

```bash
# Example: Add root-cause-tracing to core
ln -sf /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows/superpowers/skills/root-cause-tracing ~/.claude/skills/core/

# Example: Add web-artifacts-builder to tools
ln -sf /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows/skills/skills/web-artifacts-builder ~/.claude/skills/tools/
```

## Troubleshooting

### Skills Not Activating?
1. **Be explicit**: Mention the skill name directly
2. **Check context**: Skills activate based on their description triggers
3. **Verify installation**: Ensure SKILL.md exists in the skill directory

### Want to Remove a Skill?
```bash
# Just remove the symlink
rm ~/.claude/skills/core/skill-name
```

### Want to Update Skills?
```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/.agent/workflows
cd superpowers && git pull && cd ..
cd skills && git pull && cd ..
cd awesome-claude-skills && git pull && cd ..
```

## Summary

✅ **Your setup works** - skills are automatically discovered from `~/.claude/skills/`
✅ **No special commands needed** - just mention what you want to do
✅ **18 essential skills ready** - organized by category
🔄 **Optional upgrade** - install superpowers as plugin for enhanced workflow
