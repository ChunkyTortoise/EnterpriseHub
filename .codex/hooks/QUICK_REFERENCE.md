# Hooks System Quick Reference

## 🚀 Quick Start

```bash
# Test the hooks system
./.claude/hooks/test-hooks.sh

# View current metrics
python .claude/scripts/update-skill-metrics.py --report

# Export metrics to CSV
python .claude/scripts/update-skill-metrics.py --export=metrics.csv
```

## 🛡️ Security Layers

### Layer 1: Instant Blocks (<10ms)
```yaml
❌ .env files          # Secrets protection
❌ ../ paths           # Path traversal
❌ rm -rf /           # Destructive commands
❌ data/analytics/**   # PII protection
```

### Layer 2: AI Analysis (<500ms, Haiku)
```yaml
🔍 API keys in code    # sk_*, pk_*, Bearer
🔍 SQL injection      # String concatenation
🔍 Credentials        # Hardcoded passwords
```

### Layer 3: GHL Validation (<500ms, Haiku)
```yaml
✓ API key handling    # Environment variables
✓ Rate limiting       # 100 req/60s
✓ Webhook signatures  # Verification required
✓ Location IDs        # No hardcoding
```

### Layer 4: Audit Logging (Async)
```yaml
📝 File operations    # audit-log.jsonl
📝 Bash commands      # bash-audit.jsonl
📝 GHL API calls      # ghl-api-usage.jsonl
📝 Hook performance   # hook-performance.jsonl
```

### Layer 5: Cost Control
```yaml
⚡ Subagents: 10/5min  # Rate limiting
⚡ AI hooks: 30/min    # Budget protection
⚡ Max tokens: 1000    # Per hook limit
```

## 📊 Common Commands

### Metrics & Reporting
```bash
# Daily report
python .claude/scripts/update-skill-metrics.py --report --days=1

# Weekly report
python .claude/scripts/update-skill-metrics.py --report --days=7

# Export for analysis
python .claude/scripts/update-skill-metrics.py --export=weekly.csv
```

### Rate Limit Checking
```bash
# Check subagent limit
python .claude/scripts/update-skill-metrics.py \
  --check-rate-limit=subagent_creation \
  --limit=10 \
  --window=300

# Check AI hook limit
python .claude/scripts/update-skill-metrics.py \
  --check-rate-limit=ai_hooks \
  --limit=30 \
  --window=60
```

### Audit Log Analysis
```bash
# View recent file operations
tail -20 .claude/metrics/audit-log.jsonl | jq '.'

# View bash commands today
cat .claude/metrics/bash-audit.jsonl | \
  jq 'select(.timestamp | startswith("2026-01-16"))'

# View GHL API usage
cat .claude/metrics/ghl-api-usage.jsonl | jq '.'

# Find slow hooks
cat .claude/metrics/hook-performance.jsonl | \
  jq 'select(.duration_ms > 500)'
```

## 🔧 Configuration

### Edit Hooks
```bash
# Main configuration
vim .claude/hooks.yaml

# Available models
# - claude-3-5-haiku-20241022 (fast, <500ms)
# - claude-3-5-sonnet-20241022 (deep, <2s)

# Performance targets
# - max_hook_duration_ms: 500
# - max_blocking_hooks: 3
# - async_timeout_ms: 5000
```

### Adjust Rate Limits
```yaml
# In .claude/hooks.yaml
config:
  rate_limits:
    subagent_per_5min: 10      # Subagent creation
    ai_hooks_per_minute: 30    # AI-powered hooks
    total_hooks_per_session: 100  # Overall limit
```

### Change Retention
```yaml
# In .claude/hooks.yaml
config:
  audit:
    retention_days: 90         # SOC2/HIPAA requirement
    compress_after_days: 30    # Space optimization
    encryption: true           # Security requirement
```

## 🎯 Hook Patterns

### Block Pattern
```yaml
PreToolUse:
  - name: my-security-check
    matcher:
      toolName: "Write"
      args:
        file_path:
          pattern: "dangerous-pattern"
    block: true
    message: |
      🛑 BLOCKED: Reason here
```

### Warn Pattern
```yaml
PreToolUse:
  - name: my-warning-check
    matcher:
      toolName: "Edit"
    prompt: "Analyze: {content}"
    model: claude-3-5-haiku-20241022
    block: false  # Warn only
    message: "⚠️  Warning message"
```

### Async Log Pattern
```yaml
PostToolUse:
  - name: my-audit-log
    matcher:
      toolName: "*"
    async: true
    action:
      type: log
      destination: ".claude/metrics/my-log.jsonl"
      format: |
        {"timestamp": "{timestamp}", "tool": "{tool_name}"}
```

## 🚨 Common Scenarios

### Scenario 1: Secrets Detected
```
🛑 BLOCKED: Potential secrets detected in content.

Violations:
- Line 42: API key pattern "sk_live_..."

Recommendation: Use environment variables
```
**Fix**: Move to .env.example, load at runtime

### Scenario 2: SQL Injection
```
🛑 BLOCKED: SQL injection vulnerability detected.

Finding: String concatenation in SQL
Line: query = f"SELECT * FROM users WHERE id={user_id}"

Fix: Use parameterized query
```
**Fix**: Use Prisma/SQLAlchemy parameterized queries

### Scenario 3: Rate Limit Exceeded
```
⚠️  Subagent rate limit reached (10 per 5 minutes).

Current: 10/10
Resets: 2026-01-16 15:45:00 (120 seconds)

Consider:
- Batching similar tasks
- Using parallel execution
```
**Fix**: Wait for reset or optimize task distribution

### Scenario 4: Missing Tests
```
⚠️  TDD Workflow Violation

Test file not found: src/api/auth.test.py

Recommendation: Create test first following RED-GREEN-REFACTOR
1. Write failing test
2. Implement minimal code
3. Refactor with tests passing
```
**Fix**: Create test file before implementation

## 📈 Performance Optimization

### Fast Hooks (<100ms)
- Use pattern matching (no AI)
- Simple regex validation
- File path checks

### Medium Hooks (<500ms)
- Use Haiku model
- Simple content analysis
- Single-purpose validation

### Complex Hooks (<2s)
- Use Sonnet model
- Deep code analysis
- Multi-layer validation

### Async Hooks (Non-blocking)
- All PostToolUse hooks
- Audit logging
- Metrics tracking
- Performance monitoring

## 🔍 Troubleshooting

### Hook Not Triggering
1. Check tool name is exact match (case-sensitive)
2. Verify matcher pattern in hooks.yaml
3. Review hook-performance.jsonl for errors
4. Test pattern with regex tester

### Slow Performance
1. Check hook duration in metrics
2. Consider switching to async
3. Use faster Haiku model
4. Optimize prompt length

### False Positives
1. Review prompt in hooks.yaml
2. Adjust severity threshold
3. Add exception patterns
4. Test with sample data

### Missing Metrics
1. Verify metrics directory exists
2. Check script permissions (chmod +x)
3. Test script manually
4. Review error logs

## 📚 Additional Resources

- **Full Documentation**: `.claude/hooks/README.md`
- **Implementation Guide**: `.claude/HOOKS_IMPLEMENTATION_COMPLETE.md`
- **Test Suite**: `.claude/hooks/test-hooks.sh`
- **Metrics Script**: `.claude/scripts/update-skill-metrics.py`
- **Project Guide**: `CLAUDE.md` Section 11

## 🎓 Best Practices

1. **Block at Submit, Not During Workflow**
   - Let Claude plan and explore
   - Validate before final commit

2. **Use Fast Models for Simple Checks**
   - Pattern matching: No model (instant)
   - Simple validation: Haiku (<500ms)
   - Complex analysis: Sonnet (<2s)

3. **Keep PostToolUse Async**
   - Don't block workflow
   - Log and analyze later
   - Non-blocking by default

4. **Monitor & Optimize**
   - Weekly metrics review
   - Monthly performance tuning
   - Quarterly security updates

5. **Progressive Enforcement**
   - Start with warnings
   - Monitor patterns
   - Increase strictness gradually

---

**Version**: 1.0.0
**Last Updated**: 2026-01-16
**Status**: Production-Ready
