# Quick Start: Gemini CLI + Claude Code (EnterpriseHub)

**Setup Date**: January 9, 2026
**Status**: ✅ Ready to Use

---

## Installation Check

```bash
# Verify both tools are installed
which gemini  # Should show: /usr/local/bin/gemini or similar
which claude  # Should show: ~/.antigravity/extensions/.../claude

# Check versions
gemini --version  # 0.23.0+
claude --version  # 2.1.3+
```

---

## Configuration Files Created

✅ **Gemini CLI**
- `.gemini/settings.json` - Full configuration with hooks, MCP, telemetry
- `.gemini/GEMINI.md` - EnterpriseHub context (extends CLAUDE.md)
- `.geminiignore` - Excludes large files from context

✅ **Shell Aliases**
- `~/.zshrc` - 20+ aliases for hybrid workflow

✅ **Documentation**
- `GEMINI_CLI_COMPREHENSIVE_RESEARCH.md` - 54-page deep dive
- `GEMINI_CLAUDE_HYBRID_WORKFLOW.md` - Complete workflow guide
- `AI_CLI_YOLO_MODE.md` - YOLO mode reference
- This file - Quick start guide

---

## Activate Configuration

```bash
# Reload shell to activate aliases
source ~/.zshrc

# Verify aliases loaded
alias | grep -E "(claude|gemini|hub|ml|ghl|ui)"
```

---

## Quick Reference: When to Use Which Tool

### Use Gemini CLI For:

```bash
# ✅ Exploration (free tier + 1M context)
gemini -m exploration "analyze entire services/ directory"

# ✅ Prototyping (free tier + fast iteration)
gemini -m fast "prototype lead scoring dashboard"

# ✅ Documentation (free tier + large context)
gemini "generate comprehensive API documentation"

# ✅ ML Design (precise mode + good at ML)
gemini -m precise "design churn prediction algorithm"

# ✅ Large-scale analysis (1M context window)
gemini "review all 650+ tests and identify gaps"
```

### Use Claude Code For:

```bash
# ✅ Production code (superior quality)
claude-auto "implement behavioral lead scoring"

# ✅ Critical bugs (precision required)
claude "fix GHL webhook timeout issue"

# ✅ Complex refactoring (maintains quality)
claude-auto "refactor services using Strategy Pattern"

# ✅ Skills automation (32 EnterpriseHub skills)
claude "invoke rapid-feature-prototyping for lead-scoring-dashboard"

# ✅ GHL integration (mission-critical)
claude-auto "implement GHL opportunity.updated webhook"
```

---

## EnterpriseHub Quick Commands

### Development Cycle

```bash
# 1. Explore with Gemini (free, 1M context)
hub-explore "what features are in services/lead_scorer.py?"

# 2. Prototype with Gemini (free, fast)
hub-prototype "create quick prototype for behavioral scoring"

# 3. Implement with Claude (quality, skills)
hub-implement "implement production behavioral scoring"

# 4. Test with Claude (comprehensive)
hub-test  # Runs all tests and fixes failures
```

### ML Development

```bash
# 1. Explore ML models
ml-explore  # Analyzes all ML models and suggests improvements

# 2. Implement ML feature
ml-implement "implement gradient boosting for churn prediction"

# 3. Validate ML model
ml-validate  # Runs validation suite
```

### GHL Integration

```bash
# 1. Analyze GHL patterns
ghl-explore  # Reviews all GHL integration code

# 2. Implement GHL feature
ghl-implement  # Creates webhook with error handling
```

### UI Development

```bash
# 1. Analyze UI components
ui-explore  # Reviews all Streamlit components

# 2. Implement UI feature
ui-implement  # Uses frontend-design skill
```

### Quick Navigation

```bash
cdh   # ~/enterprisehub
cds   # ~/enterprisehub/ghl_real_estate_ai/services
cdt   # ~/enterprisehub/ghl_real_estate_ai/tests
cdu   # ~/enterprisehub/ghl_real_estate_ai/streamlit_demo
```

---

## First Time Setup (One-Time Only)

### Step 1: Set Environment Variables

```bash
# Edit .env file (copy from .env.example if needed)
nano .env

# Add your API keys:
GEMINI_API_KEY=your_gemini_api_key_here
CLAUDE_API_KEY=your_claude_api_key_here  # If using API directly
GITHUB_TOKEN=your_github_token_here
```

### Step 2: Verify Gemini CLI Configuration

```bash
# Navigate to EnterpriseHub
cd ~/enterprisehub

# Start Gemini CLI
gemini

# In session, verify configuration
/memory show

# You should see:
# - GEMINI.md loaded
# - CLAUDE.md referenced
# - All services/ directories included
```

### Step 3: Verify Claude Code Configuration

```bash
# Start Claude Code
claude

# Verify context loaded
# Should see CLAUDE.md and skills system active
```

### Step 4: Test Hybrid Workflow

```bash
# Quick test - Gemini exploration
gemini "list all services in ghl_real_estate_ai/services/"

# Quick test - Claude implementation
claude "what skills are available?"

# Should see 32 EnterpriseHub skills
```

---

## Common Workflows

### Workflow 1: New Feature Development

```bash
# Terminal 1: Exploration (Gemini)
gemini -m exploration
> "analyze lead scoring feature requirements"
> "suggest behavioral learning approach"
> "identify integration points"

# Terminal 2: Implementation (Claude)
claude-auto
> "implement behavioral lead scoring based on Gemini analysis"
> "run tests"
> "create documentation"
```

### Workflow 2: Bug Investigation & Fix

```bash
# Investigation (Gemini - free)
gemini "investigate webhook timeout errors in services/ghl/"

# Implementation (Claude - precision)
claude-auto "fix webhook timeout with async processing and retry logic"

# Verification (Claude)
claude-yolo "run integration tests"
```

### Workflow 3: ML Model Development

```bash
# Research (Gemini)
ml-explore

# Design (Gemini precise mode)
gemini -m precise "design churn prediction model using gradient boosting"

# Implementation (Claude)
claude-auto "implement production churn prediction service"

# Validation (Claude)
ml-validate
```

---

## Keyboard Shortcuts

### Gemini CLI (In-Session)

| Shortcut | Action |
|----------|--------|
| `Ctrl+Y` | Toggle YOLO mode |
| `Shift+Tab` | Toggle Auto-Edit mode |
| `/` | Session browser |
| `/memory refresh` | Reload context |
| `/memory show` | Display context |
| `/resume` | Session picker |

### Shell Aliases

| Alias | Full Command |
|-------|--------------|
| `gemini-yolo` | `gemini --yolo` |
| `gemini-auto` | `gemini --approval-mode auto_edit` |
| `claude-yolo` | `claude --permission-mode bypassPermissions` |
| `claude-auto` | `claude --permission-mode acceptEdits` |

---

## Model Selection Guide (Gemini CLI)

```bash
# Fast mode (default) - General development
gemini
gemini -m fast

# Precise mode - ML tasks, complex logic
gemini -m precise

# Exploration mode - Large codebase analysis
gemini -m exploration
```

**Configured models:**
- `fast`: gemini-2.5-flash (temp 0.7) - Prototyping, general tasks
- `precise`: gemini-2.5-pro (temp 0.3) - ML, complex logic
- `exploration`: gemini-2.5-flash (temp 0.9) - Creative, analysis

---

## Troubleshooting

### Issue: "gemini: command not found"

```bash
# Install Gemini CLI
npm install -g @google/generative-ai-cli

# Or via Homebrew
brew install gemini-cli
```

### Issue: Configuration not loading

```bash
# Verify files exist
ls -la .gemini/
ls -la .gemini/settings.json
ls -la .gemini/GEMINI.md

# Force reload
gemini
/memory refresh
```

### Issue: Aliases not working

```bash
# Reload shell config
source ~/.zshrc

# Verify aliases
alias | grep hub
```

### Issue: API key not found

```bash
# Check .env file
cat .env | grep GEMINI_API_KEY

# If missing, add it
echo "GEMINI_API_KEY=your_key_here" >> .env
```

---

## Session Management

### List Sessions

```bash
# Gemini sessions
gemini --list-sessions

# Claude sessions
claude --list-sessions
```

### Resume Work

```bash
# Resume latest
gemini --resume
claude --resume

# Resume specific session
gemini --resume 5
claude --resume <session-id>
```

### Delete Old Sessions

```bash
# Gemini (auto-cleanup configured: 30 days, 100 max)
gemini --delete-session 10

# Claude
claude --delete-session <session-id>
```

---

## Cost Tracking

### Gemini CLI (Free Tier)

```bash
# View usage telemetry
cat /tmp/gemini-enterprisehub-telemetry.json | jq '.usage'

# Count requests today
cat /tmp/gemini-enterprisehub-telemetry.json | jq '.sessions[] | select(.date == "2026-01-09") | .requests' | wc -l

# Free tier limit: 1,000 requests/day
```

### Claude Code

```bash
# Pro Plan: $20/month unlimited
# ROI: $362,600+ annually from 32 skills
# Payback: < 1 day
```

---

## Next Steps

1. **Try first exploration:**
   ```bash
   gemini -m exploration "analyze EnterpriseHub architecture"
   ```

2. **Implement first feature:**
   ```bash
   claude-auto "implement simple utility function"
   ```

3. **Test hybrid workflow:**
   ```bash
   hub-explore "what should I build?"
   # Then use hub-implement, hub-test
   ```

4. **Review documentation:**
   - Read `GEMINI_CLAUDE_HYBRID_WORKFLOW.md` for complete patterns
   - Check `GEMINI_CLI_COMPREHENSIVE_RESEARCH.md` for deep dive
   - Reference `AI_CLI_YOLO_MODE.md` for safety guidelines

---

## Support Resources

**Documentation:**
- [GEMINI_CLAUDE_HYBRID_WORKFLOW.md](GEMINI_CLAUDE_HYBRID_WORKFLOW.md) - Complete workflow guide
- [GEMINI_CLI_COMPREHENSIVE_RESEARCH.md](GEMINI_CLI_COMPREHENSIVE_RESEARCH.md) - 54-page research
- [AI_CLI_YOLO_MODE.md](AI_CLI_YOLO_MODE.md) - YOLO mode reference

**Configuration:**
- `.gemini/settings.json` - Gemini CLI config
- `.gemini/GEMINI.md` - EnterpriseHub context
- `CLAUDE.md` - Claude Code config

**Quick Help:**
```bash
gemini --help
claude --help
alias | grep -E "(hub|ml|ghl|ui)"  # List all EnterpriseHub aliases
```

---

**🚀 You're ready to go! Start with `hub-explore` and see the magic happen.**

**Last Updated**: January 9, 2026 | **Version**: 1.0.0 | **Status**: Production Ready
