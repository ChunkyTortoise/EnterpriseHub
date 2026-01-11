# AI CLI - YOLO Mode Configuration

**Status**: ✅ Configured and Active
**Last Updated**: January 9, 2026

---

## Quick Start

Your shell has been configured with convenient aliases for running Claude Code and Gemini CLI in auto-accept mode.

### YOLO Mode (Auto-Accept Everything)

```bash
# Claude Code - Bypass all permissions
claude-yolo "implement lead scoring feature"

# Gemini CLI - YOLO mode
gemini-yolo "refactor property matching service"
```

### Auto-Edit Mode (Auto-Accept Edits Only)

```bash
# Claude Code - Auto-accept file edits, prompt for other actions
claude-auto "fix type errors in services"

# Gemini CLI - Auto-accept edits only
gemini-auto "optimize database queries"
```

---

## Permission Modes Explained

### Claude Code

| Alias | Flag | Behavior |
|-------|------|----------|
| `claude-yolo` | `--permission-mode bypassPermissions` | Auto-accepts ALL actions (tools, edits, commands) |
| `claude-auto` | `--permission-mode acceptEdits` | Auto-accepts file edits, prompts for bash/tools |
| `claude` (default) | `--permission-mode default` | Prompts for all actions |

**Additional Options:**
- `--permission-mode dontAsk` - Similar to bypass, but with different behavior
- `--permission-mode plan` - Plan mode (requires approval before implementation)
- `--permission-mode delegate` - Delegates permission handling

### Gemini CLI

| Alias | Flag | Behavior |
|-------|------|----------|
| `gemini-yolo` | `--yolo` or `-y` | Auto-accepts ALL actions |
| `gemini-auto` | `--approval-mode auto_edit` | Auto-accepts edits only |
| `gemini` (default) | `--approval-mode default` | Prompts for all actions |

---

## Usage Examples

### Claude Code YOLO Mode

```bash
# Feature development - no interruptions
claude-yolo "add churn prediction dashboard to streamlit app"

# Batch refactoring
claude-yolo "update all services to use new GHL API pattern"

# Full integration testing
claude-yolo "run all tests and fix any failures"

# Deployment automation
claude-yolo "deploy to Railway and run smoke tests"
```

### Gemini CLI YOLO Mode

```bash
# Quick prototyping
gemini-yolo "create property search API endpoint"

# Code generation
gemini-yolo "generate test suite for lead scoring service"

# Documentation
gemini-yolo "add docstrings to all public methods in this file"
```

### Auto-Edit Mode (Safer Option)

```bash
# Auto-approve edits, but verify bash commands
claude-auto "implement authentication middleware"
gemini-auto "optimize ML model training pipeline"
```

---

## Combining with Other Flags

### Claude Code

```bash
# YOLO + IDE integration
claude-yolo --ide "implement feature"

# YOLO + specific session
claude-yolo --session-id <uuid> "continue work"

# YOLO + print mode (for scripting)
claude-yolo --print "generate code snippet"

# YOLO + plugin directory
claude-yolo --plugin-dir .claude/skills "use custom skills"
```

### Gemini CLI

```bash
# YOLO + specific extensions
gemini-yolo -e mcp-server "use MCP tools"

# YOLO + resume session
gemini-yolo --resume latest "continue previous work"

# YOLO + allowed tools only
gemini-yolo --allowed-tools read,write,bash "restrict to safe tools"
```

---

## Safety Considerations

### ⚠️ Use YOLO Mode When:
- ✅ Working on isolated feature branches
- ✅ Prototyping new functionality
- ✅ Running automated workflows you trust
- ✅ Working in development/staging environments
- ✅ You understand what the AI will do

### 🛑 DO NOT Use YOLO Mode When:
- ❌ Working on production branches (main/master)
- ❌ Handling sensitive data or credentials
- ❌ Making database schema changes
- ❌ Deploying to production
- ❌ Unsure about the AI's planned actions
- ❌ Working with unfamiliar codebases

### Recommended Workflow

```bash
# 1. Use default mode to see what AI plans to do
claude "implement lead scoring feature"

# 2. If plan looks good, cancel and re-run with YOLO
# Press Ctrl+C to cancel
claude-yolo "implement lead scoring feature"

# 3. For critical operations, use auto-edit mode
claude-auto "update database migration"
```

---

## Troubleshooting

### Aliases Not Working

```bash
# Reload shell configuration
source ~/.zshrc

# Verify aliases exist
alias | grep -E "(claude-yolo|gemini-yolo)"

# If still not working, check ~/.zshrc for syntax errors
cat ~/.zshrc
```

### Want to Add More Aliases

Edit `~/.zshrc` and add custom aliases:

```bash
# Project-specific YOLO commands
alias hub-yolo='cd ~/enterprisehub && claude-yolo'
alias ghl-test='claude-yolo "run GHL integration tests and fix failures"'
alias ml-train='claude-yolo "retrain all ML models with latest data"'
```

Then reload: `source ~/.zshrc`

---

## Environment-Specific Configurations

### Development Environment

```bash
# ~/.zshrc
export CLAUDE_DEFAULT_MODE="bypassPermissions"  # Always YOLO in dev
export GEMINI_DEFAULT_APPROVAL="yolo"
```

### Production Environment

```bash
# ~/.zshrc_production
export CLAUDE_DEFAULT_MODE="default"  # Always prompt in prod
export GEMINI_DEFAULT_APPROVAL="default"

# Prevent accidental YOLO in production
alias claude-yolo='echo "⛔ YOLO mode disabled in production"'
alias gemini-yolo='echo "⛔ YOLO mode disabled in production"'
```

---

## Advanced: Shell Functions for Conditional YOLO

Add to `~/.zshrc`:

```bash
# Smart YOLO - only enable on non-main branches
smart-claude() {
    local current_branch=$(git branch --show-current 2>/dev/null)

    if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
        echo "⚠️  On $current_branch - using safe mode (no auto-accept)"
        claude "$@"
    else
        echo "✅ On $current_branch - YOLO mode enabled"
        claude --permission-mode bypassPermissions "$@"
    fi
}

# Smart Gemini - only enable on non-main branches
smart-gemini() {
    local current_branch=$(git branch --show-current 2>/dev/null)

    if [[ "$current_branch" == "main" || "$current_branch" == "master" ]]; then
        echo "⚠️  On $current_branch - using safe mode (no auto-accept)"
        gemini "$@"
    else
        echo "✅ On $current_branch - YOLO mode enabled"
        gemini --yolo "$@"
    fi
}
```

Usage:
```bash
# Automatically uses YOLO on feature branches, safe mode on main
smart-claude "implement feature"
smart-gemini "refactor code"
```

---

## Configuration Files

### Claude Code
- **Global config**: Not currently used for permission modes
- **Session config**: Permissions set per-session via CLI flags
- **Project config**: Can set default behavior in `.claude/config.json` (if supported)

### Gemini CLI
- **Global config**: Check `~/.config/gemini/` for persistent settings
- **Project config**: `.gemini.json` in project root (if supported)

---

## Related Documentation

- Claude Code: [Permission Modes](https://docs.anthropic.com/claude-code/permissions)
- Gemini CLI: [Approval Modes](https://github.com/gemini/cli#approval-modes)
- EnterpriseHub Security: `CLAUDE.md` Section 5 (Security Standards)

---

## Summary

**Aliases Created:**
- ✅ `claude-yolo` - Full auto-accept mode
- ✅ `claude-auto` - Auto-accept edits only
- ✅ `gemini-yolo` - Full auto-accept mode
- ✅ `gemini-auto` - Auto-accept edits only

**Configuration Location:** `~/.zshrc`
**Status:** Active (reload with `source ~/.zshrc`)

**Quick Test:**
```bash
# Verify aliases work
alias | grep yolo

# Test with simple command
claude-yolo --help
gemini-yolo --help
```

---

**⚡ Pro Tip:** For maximum safety, create a git branch before using YOLO mode, so you can easily revert if needed:

```bash
git checkout -b feature/ai-assisted-development
claude-yolo "implement feature"
git diff  # Review changes before committing
```
