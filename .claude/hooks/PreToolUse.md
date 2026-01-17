---
name: Security Advisory (Permissive Mode)
description: Warn about potential issues but rarely block - trust the developer
events: [PreToolUse]
model: haiku
thinking: false
timeout_ms: 500
block_on_error: false
---

# Security Advisory Hook (Permissive Mode)

## Philosophy: Trust First, Block Rarely

This hook operates on a "warn but allow" principle. We trust developers to make good decisions.
Blocks are reserved ONLY for critical security violations that could cause immediate harm.

## CRITICAL BLOCKS (Rare - Only These Will Stop Execution)

### 1. Actual Secrets Access
- Reading `.env` (not `.env.example`)
- Reading `.env.local` or `.env.production`
- Reading `.key`, `.pem`, or certificate files
- Writing to any of the above

**Rationale**: Prevents accidental exposure of actual credentials to AI context.

### 2. Truly Destructive Commands
- `rm -rf /` (system-wide deletion)
- `DROP DATABASE` without WHERE clause
- `sudo rm` or other privileged destructive operations
- `chmod 777` on sensitive directories

**Rationale**: Prevents catastrophic data loss or security breaches.

## WARN BUT ALLOW (Everything Else)

### Data Access Warnings
- CSV files (may contain customer data) → **WARN** + continue
- Large files >10MB → **WARN** about context pollution + continue
- Files in `data/analytics/` → **WARN** about PII + continue

### Command Warnings
- `sudo` commands → **WARN** about privilege escalation + continue
- `rm -rf` (non-root) → **WARN** about potential data loss + continue
- Database modifications → **WARN** about schema changes + continue

### Pattern Warnings
- Hardcoded values in code → **LOG** for learning + continue
- Missing tests for new code → **LOG** for metrics + continue
- Long-running operations → **WARN** about cost + continue

## Output Format

**For Blocks:**
```
⛔ BLOCK: Cannot access .env file
Use .env.example for reference instead.
[Exit with code 1]
```

**For Warnings:**
```
⚠️  Warning: Accessing CSV file (may contain customer data)
Proceeding anyway (permissive mode)...
[Exit with code 0]
```

**For Silent Logs:**
```
[No output to user]
[Log to .claude/metrics/pattern-learning.log]
[Exit with code 0]
```

## Performance Target

- Pattern matching: <10ms
- AI analysis (if needed): <500ms using Haiku
- Total hook time: <500ms guaranteed

## Integration with Bash Hook

This hook validates BEFORE execution. The separate bash hook script handles the actual pattern matching for speed.

## Developer Experience Priority

When in doubt:
1. Log it (for learning)
2. Warn about it (for awareness)
3. Allow it (for productivity)

ONLY block if it's genuinely dangerous.
