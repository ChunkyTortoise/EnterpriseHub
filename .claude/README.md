# Claude Code Configuration

**Project**: EnterpriseHub - GHL Real Estate AI Platform
**Last Updated**: 2026-01-16
**Claude Code Version**: 2.1.0+

## Quick Start

### 1. Check Session Health
```bash
python .claude/scripts/session-manager.py check
```

### 2. Select MCP Profile
Edit `.claude/settings.json` and set `"active_profile"` to:
- `minimal-context` (default, saves 8k tokens)
- `research` (docs only, saves 10k tokens)
- `backend-services`, `streamlit-dev`, or `testing-qa`

### 3. Run Validations
```bash
./.claude/scripts/zero-context/check-test-coverage.sh
```

## Token Optimization Summary

**Savings**: 15-25% token reduction
**Before**: 37.4k overhead (66.5% available)
**After**: 22.4k overhead (71.5% available)
**Improvement**: +10k tokens (+5% context)

## Directory Structure

```
.claude/
├── mcp-profiles/          # 5 optimized profiles
├── reference/             # Progressive disclosure docs
├── scripts/               # Zero-context validators
├── skills/                # 14 production skills
└── hooks/                 # PreToolUse/PostToolUse
```

## Quick Commands

```bash
# Session health
python .claude/scripts/session-manager.py check

# Zero-context validations
./.claude/scripts/zero-context/validate-ghl-integration.sh
./.claude/scripts/zero-context/check-test-coverage.sh
./.claude/scripts/zero-context/analyze-performance.sh
```

## Documentation

- **Complete Strategy**: `.claude/TOKEN_OPTIMIZATION.md`
- **Quick Reference**: `.claude/OPTIMIZATION_SUMMARY.md`
- **Project Guide**: `CLAUDE.md` (root)

