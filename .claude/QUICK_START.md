# Token Optimization - Quick Start Guide

**Status**: ✅ Active | **Savings**: 15-25% | **Setup Time**: 2 minutes

## Immediate Benefits

- **+10k tokens** of available context (+5%)
- **90-93% savings** on validation scripts
- **Automated monitoring** with health alerts
- **Progressive disclosure** for documentation

## 3-Step Setup

### 1. Verify Configuration (30 seconds)
```bash
# Check that minimal-context profile is active
cat .claude/settings.json | grep active_profile
# Should show: "active_profile": "minimal-context"
```

### 2. Test Session Manager (30 seconds)
```bash
# Check your current session health
python .claude/scripts/session-manager.py check

# Expected output:
# Status: ✅ HEALTHY
# Total: ~40k tokens (20%)
# Available: ~160k tokens
```

### 3. Test Zero-Context Script (1 minute)
```bash
# Run a validation (uses <1k tokens vs 8k)
./.claude/scripts/zero-context/check-test-coverage.sh

# Token savings: 93% reduction!
```

## Daily Workflow

### Morning Checklist
```bash
# 1. Check session health
python .claude/scripts/session-manager.py check

# 2. If using defaults, you're already optimized!
# minimal-context profile active by default
```

### During Development
```bash
# Run validations without context bloat
./.claude/scripts/zero-context/validate-ghl-integration.sh
./.claude/scripts/zero-context/check-test-coverage.sh
./.claude/scripts/zero-context/analyze-performance.sh

# Each script: <1k tokens vs 5-10k tokens traditional
```

### When Context High (>75%)
```bash
# Option 1: Compact conversation history
/compact

# Option 2: Clear and restart
/clear

# Option 3: Check what's loaded
python .claude/scripts/session-manager.py check
```

## MCP Profile Quick Switch

Edit `.claude/settings.json` line 41:

```json
// Routine development (default)
"active_profile": "minimal-context"  // Saves 8k tokens

// Documentation research
"active_profile": "research"  // Saves 10k tokens

// Streamlit UI work
"active_profile": "streamlit-dev"  // Full tools

// Backend development
"active_profile": "backend-services"  // Full tools

// Testing/QA work
"active_profile": "testing-qa"  // Full tools
```

## Reference Files (Load On-Demand)

**Only load when you need them** - each is 3-4k tokens

```bash
# Implementing authentication or security?
Read @.claude/reference/security.md

# Designing API endpoints?
Read @.claude/reference/api-patterns.md

# Writing or debugging tests?
Read @.claude/reference/testing.md
```

## Health Monitoring

### Session Status Indicators

| Status | Context | Iterations | What To Do |
|--------|---------|------------|------------|
| ✅ Healthy | <150k | <20 | Keep going |
| ⚠️ Warning | 150-170k | 20-30 | Run `/compact` |
| ❌ Critical | >170k | >30 | Run `/clear` or new session |

### Check Health Anytime
```bash
python .claude/scripts/session-manager.py check
```

## Token Savings Summary

| Feature | Before | After | Savings |
|---------|--------|-------|---------|
| MCP Overhead | 12k | 4k | -67% |
| Validation Scripts | 5-10k | 0.3-0.7k | -93% |
| CLAUDE.md | 8k | 6k | -25% |
| **Total Overhead** | **37.4k** | **22.4k** | **-40%** |
| **Available Context** | **66.5%** | **71.5%** | **+5%** |

## Common Commands

```bash
# Session health check
python .claude/scripts/session-manager.py check

# Increment iteration counter (optional tracking)
python .claude/scripts/session-manager.py increment

# Reset iteration counter
python .claude/scripts/session-manager.py reset

# Zero-context validations
./.claude/scripts/zero-context/validate-ghl-integration.sh
./.claude/scripts/zero-context/check-test-coverage.sh
./.claude/scripts/zero-context/analyze-performance.sh
```

## Troubleshooting

### Still seeing high context usage?
1. Check active profile in settings.json
2. Ensure minimal-context is active
3. Run session health check
4. Use `/compact` to compress history

### Scripts not executing?
1. Make them executable: `chmod +x .claude/scripts/**/*.sh`
2. Check Python3 is available: `which python3`
3. Review error output

## Full Documentation

- **Complete Guide**: `.claude/TOKEN_OPTIMIZATION.md`
- **Summary**: `.claude/OPTIMIZATION_SUMMARY.md`
- **Implementation Report**: `TOKEN_OPTIMIZATION_IMPLEMENTATION.md`

---

**You're all set!** The optimization is active and saving tokens automatically.

**Next**: Just code normally. The system handles optimization behind the scenes.

**Monitor**: Run `python .claude/scripts/session-manager.py check` every 10-15 iterations.
