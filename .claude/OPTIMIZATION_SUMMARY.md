# Token Optimization - Quick Reference

**Status**: Active | **Savings**: 15-25% token reduction | **Updated**: 2026-01-16

## Quick Commands

```bash
# Check session health (run every 10-15 iterations)
python .claude/scripts/session-manager.py check

# Validate GHL integration
./.claude/scripts/zero-context/validate-ghl-integration.sh

# Check test coverage
./.claude/scripts/zero-context/check-test-coverage.sh

# Analyze performance
./.claude/scripts/zero-context/analyze-performance.sh

# Switch MCP profiles
export CLAUDE_PROFILE=minimal-context  # Default, saves 8k tokens
export CLAUDE_PROFILE=research         # Docs only, saves 10k tokens
export CLAUDE_PROFILE=backend-services # Full backend tools
export CLAUDE_PROFILE=streamlit-dev    # Full UI tools
export CLAUDE_PROFILE=testing-qa       # Full testing tools
```

## MCP Profiles Decision Tree

```
Task Type?
├─ Routine Development (bug fix, refactor, simple feature)
│  └─ Use: minimal-context (Serena only, saves 8k tokens)
│
├─ Research/Documentation Lookup
│  └─ Use: research (Context7 only, saves 10k tokens)
│
├─ Streamlit/UI Work
│  └─ Use: streamlit-dev (Serena + Playwright, full tools)
│
├─ Backend/API Development
│  └─ Use: backend-services (Serena + Context7 + Greptile)
│
└─ Testing/QA Work
   └─ Use: testing-qa (All tools for comprehensive testing)
```

## Reference Files (Load On-Demand Only)

```
When implementing security features:
  → Read @.claude/reference/security.md

When designing API endpoints:
  → Read @.claude/reference/api-patterns.md

When writing/debugging tests:
  → Read @.claude/reference/testing.md
```

## Session Health Thresholds

| Status | Context Usage | Iterations | Action |
|--------|---------------|------------|--------|
| ✅ Healthy | <75% (150k) | <20 | Continue normally |
| ⚠️ Warning | 75-85% (150-170k) | 20-30 | Run `/compact` |
| ❌ Critical | >85% (170k) | >30 | Run `/clear` or new session |

## Token Savings Breakdown

| Optimization | Before | After | Savings |
|--------------|--------|-------|---------|
| MCP Servers | 12k tokens | 4k tokens | -8k (-67%) |
| CLAUDE.md | 8k tokens | 6k tokens | -2k (-25%) |
| Validation Scripts | 5-10k tokens | 0.3-0.7k tokens | -93% |
| **Total Overhead** | **37.4k tokens** | **22.4k tokens** | **-15k (-40%)** |
| **Available Context** | **81.3%** | **88.8%** | **+7.5%** |

## Best Practices

**Do** ✅:
- Start with minimal-context profile
- Run session health checks regularly
- Use zero-context scripts for validation
- Load reference docs only when needed
- Switch profiles based on task

**Don't** ❌:
- Enable all MCP servers simultaneously
- Load all reference files at once
- Ignore session health warnings
- Let iterations exceed 30
- Keep unused files in context

## Full Documentation

For complete details, see: `.claude/TOKEN_OPTIMIZATION.md`
