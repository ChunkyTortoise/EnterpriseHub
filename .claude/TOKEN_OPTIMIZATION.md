# Token Optimization Strategy

**Implementation Date**: 2026-01-16
**Target Savings**: 15-25% token reduction
**Status**: Active

## Overview

This document outlines the token optimization strategy for the EnterpriseHub project, designed to maximize available context while maintaining development efficiency.

## Current Token Budget Analysis

### 200K Context Window Breakdown

```
┌─ Total Context Window ───────────────────────────────┐
│ Total Available:         200,000 tokens              │
├──────────────────────────────────────────────────────┤
│ System Prompt:           ~15,000 tokens (7.5%)       │
│ MCP Servers (all):       ~12,000 tokens (6.0%)       │
│   - Serena:              ~4,000 tokens               │
│   - Context7:            ~3,000 tokens               │
│   - Playwright:          ~3,000 tokens               │
│   - Greptile:            ~2,000 tokens               │
│ CLAUDE.md (original):    ~8,000 tokens (4.0%)        │
│ Auto-Compact Buffer:     32,000 tokens (16.0%)       │
├──────────────────────────────────────────────────────┤
│ Total Overhead:          ~67,000 tokens (33.5%)      │
│ Available for Code:      ~133,000 tokens (66.5%)     │
└──────────────────────────────────────────────────────┘
```

### After Optimization

```
┌─ Optimized Token Budget ─────────────────────────────┐
│ Total Available:         200,000 tokens              │
├──────────────────────────────────────────────────────┤
│ System Prompt:           ~15,000 tokens (7.5%)       │
│ MCP Servers (minimal):   ~4,000 tokens (2.0%)        │
│   - Serena only          ~4,000 tokens               │
│ CLAUDE.md (optimized):   ~6,000 tokens (3.0%)        │
│ Auto-Compact Buffer:     32,000 tokens (16.0%)       │
├──────────────────────────────────────────────────────┤
│ Total Overhead:          ~57,000 tokens (28.5%)      │
│ Available for Code:      ~143,000 tokens (71.5%)     │
│                                                       │
│ IMPROVEMENT:             +10,000 tokens (+5%)        │
└──────────────────────────────────────────────────────┘
```

## Optimization Components

### 1. MCP Profile Optimization

**Location**: `.claude/mcp-profiles/`

#### minimal-context.json
**Purpose**: Default profile for routine development
**Savings**: ~8,000 tokens (4% context reclaimed)
**Enabled**: Serena only (code navigation)
**Disabled**: Context7, Playwright, Greptile

**Use Cases**:
- Code refactoring
- Bug fixes
- Simple feature implementation
- Code navigation and exploration

**Switch Command**:
```bash
export CLAUDE_PROFILE=minimal-context
# or in settings.json: "active_profile": "minimal-context"
```

#### research.json
**Purpose**: Documentation and library research
**Savings**: ~10,000 tokens (5% context reclaimed)
**Enabled**: Context7 only (documentation)
**Disabled**: Serena, Playwright, Greptile

**Use Cases**:
- API documentation lookup
- Learning new libraries
- Exploring design patterns
- Code example discovery

**Workflow**:
1. Switch to research profile
2. Use Context7 for documentation queries
3. Switch back to minimal-context for implementation

### 2. Zero-Context Validation Scripts

**Location**: `.claude/scripts/zero-context/`

These scripts execute WITHOUT loading into context. Only their output consumes tokens.

#### validate-ghl-integration.sh
**Function**: Validate GoHighLevel API integration
**Token Usage**: ~300-500 tokens (output only) vs ~5,000 if loaded
**Savings**: ~90% reduction

**Checks**:
- Environment variable configuration
- Service implementation presence
- Test coverage existence
- Rate limiting implementation
- Error handling patterns

**Usage**:
```bash
./.claude/scripts/zero-context/validate-ghl-integration.sh
```

#### check-test-coverage.sh
**Function**: Analyze test coverage
**Token Usage**: ~400-600 tokens (output only) vs ~8,000 if loaded
**Savings**: ~93% reduction

**Reports**:
- Overall coverage percentage
- Coverage by file
- Files below threshold
- Test execution summary

**Usage**:
```bash
./.claude/scripts/zero-context/check-test-coverage.sh
```

#### analyze-performance.sh
**Function**: Performance and optimization analysis
**Token Usage**: ~500-700 tokens (output only) vs ~10,000 if loaded
**Savings**: ~93% reduction

**Analyzes**:
- N+1 query patterns
- Caching strategy implementation
- Async/await usage
- Resource management
- Pagination implementation

**Usage**:
```bash
./.claude/scripts/zero-context/analyze-performance.sh
```

### 3. Reference Documentation (Progressive Disclosure)

**Location**: `.claude/reference/`

Detailed content moved out of CLAUDE.md, loaded only when needed.

#### security.md
**Token Budget**: ~3-4k tokens (load on-demand)
**Content**:
- OWASP Top 10 quick reference
- Authentication patterns (JWT, session management)
- Encryption and secrets management
- Access control (RBAC) implementation
- API security checklist
- Cryptographic standards

**Load Trigger**: When implementing authentication, API endpoints, or security-sensitive features

#### api-patterns.md
**Token Budget**: ~3-4k tokens (load on-demand)
**Content**:
- REST API design principles
- HTTP status codes
- Pagination patterns (offset and cursor-based)
- Error response formats
- Versioning strategies
- Filtering and searching
- HATEOAS patterns
- Async API patterns

**Load Trigger**: When designing REST/GraphQL endpoints or implementing pagination

#### testing.md
**Token Budget**: ~3-4k tokens (load on-demand)
**Content**:
- Test organization patterns
- Fixture and factory patterns
- Async testing
- Mocking and patching
- Coverage configuration
- Test performance optimization
- Anti-patterns to avoid

**Load Trigger**: When writing tests, debugging test failures, or improving coverage

### 4. Session Health Monitoring

**Location**: `.claude/scripts/session-manager.py`

**Function**: Monitor context usage and iteration count
**Token Usage**: Zero-context execution

**Features**:
- Real-time token usage estimation
- Iteration count tracking
- Warning thresholds at 75% and 85% usage
- Proactive optimization suggestions
- Health status reporting

**Usage**:
```bash
# Check session health
python .claude/scripts/session-manager.py check

# Increment iteration count
python .claude/scripts/session-manager.py increment

# Reset iteration counter
python .claude/scripts/session-manager.py reset
```

**Thresholds**:
- **Warning**: 75% context usage (150k tokens) or 20 iterations
- **Critical**: 85% context usage (170k tokens) or 30 iterations

**Recommendations**:
- CLAUDE.md optimization if >8k tokens
- MCP profile switching if overhead >10k tokens
- `/compact` or `/clear` suggestions
- New session recommendations

## Implementation Workflow

### Daily Development Pattern

```bash
# 1. Start with minimal-context profile (default)
export CLAUDE_PROFILE=minimal-context

# 2. Check session health periodically
python .claude/scripts/session-manager.py check

# 3. Run zero-context validations as needed
./.claude/scripts/zero-context/check-test-coverage.sh
./.claude/scripts/zero-context/analyze-performance.sh

# 4. Switch profiles for specific tasks
export CLAUDE_PROFILE=research      # For documentation lookup
export CLAUDE_PROFILE=streamlit-dev # For UI work
export CLAUDE_PROFILE=backend-services # For backend work

# 5. Load reference docs only when needed
# Reference @.claude/reference/security.md when implementing auth
# Reference @.claude/reference/api-patterns.md when designing APIs
```

### Context Optimization Checklist

**Before Starting Work**:
- [ ] Activate appropriate MCP profile
- [ ] Check session health
- [ ] Review iteration count

**During Development**:
- [ ] Use zero-context scripts for validation
- [ ] Load reference docs only when triggered
- [ ] Monitor context usage periodically

**When Context High (>75%)**:
- [ ] Run `/compact` to compress history
- [ ] Consider switching to minimal-context profile
- [ ] Close unused reference files

**When Context Critical (>85%)**:
- [ ] Run `/clear` to reset context
- [ ] Start new session if needed
- [ ] Archive important context before clearing

## Performance Metrics

### Expected Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Base Overhead** | 37.4k tokens | 22.4k tokens | -15k (-40%) |
| **Available Context** | 81.3% | 88.8% | +7.5% |
| **Script Validation** | 5-10k tokens | 0.3-0.7k tokens | -93% |
| **Reference Loading** | Always loaded | On-demand | Variable |
| **MCP Overhead** | 12k tokens | 4k tokens | -8k (-67%) |

### Cost Savings Estimate

Assuming Claude API pricing and typical development session:

```
Before Optimization:
- Average context per session: 150k tokens
- Sessions per day: 10
- Daily tokens: 1.5M tokens

After Optimization:
- Average context per session: 120k tokens (20% reduction)
- Sessions per day: 10
- Daily tokens: 1.2M tokens

Savings: 300k tokens/day (20%)
Monthly savings: 9M tokens (~15-20% cost reduction)
```

## Monitoring and Continuous Improvement

### Weekly Review

1. Analyze session-manager.py reports
2. Identify high-token-usage patterns
3. Optimize CLAUDE.md if growing
4. Update reference docs if needed
5. Adjust MCP profiles based on usage

### Monthly Review

1. Evaluate profile effectiveness
2. Measure actual cost savings
3. Update token budgets if needed
4. Refine zero-context scripts
5. Audit reference documentation

## Best Practices

### Do's ✅

- **Use minimal-context profile by default**
- **Switch profiles based on task type**
- **Run zero-context scripts for validation**
- **Load reference docs only when needed**
- **Monitor session health regularly**
- **Use `/compact` proactively at 75% usage**
- **Keep CLAUDE.md concise (<6k tokens)**

### Don'ts ❌

- **Don't keep all MCP servers enabled**
- **Don't load reference files speculatively**
- **Don't ignore session health warnings**
- **Don't let CLAUDE.md grow unchecked**
- **Don't exceed 30 iterations without reset**
- **Don't load large files unnecessarily**

## Troubleshooting

### Context Still High After Optimization

1. Check active MCP profile: `echo $CLAUDE_PROFILE`
2. Verify minimal-context profile active in settings.json
3. Run session health check
4. Review loaded files
5. Clear and restart session

### Zero-Context Scripts Not Working

1. Ensure scripts are executable: `chmod +x .claude/scripts/zero-context/*.sh`
2. Check Python dependencies for session-manager.py
3. Verify project root path
4. Check script output for errors

### Reference Docs Not Loading

1. Verify file paths in `.claude/reference/`
2. Check file permissions
3. Ensure CLAUDE.md references are correct
4. Manually read files if needed

## Future Enhancements

### Planned Improvements

1. **Automatic Profile Switching**
   - Detect task type from prompt
   - Auto-switch to optimal profile

2. **Smart Reference Loading**
   - AI-driven reference file selection
   - Predictive loading based on context

3. **Advanced Session Analytics**
   - Detailed token usage tracking
   - Cost analysis and reporting
   - Optimization recommendations

4. **Integration with CI/CD**
   - Pre-commit token budget checks
   - Automated CLAUDE.md optimization
   - Reference doc validation

---

**Last Updated**: 2026-01-16
**Version**: 1.0.0
**Maintained By**: EnterpriseHub Team
