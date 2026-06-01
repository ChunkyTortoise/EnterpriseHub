---
name: Pattern Learning (Non-Blocking)
description: Capture successful patterns and learnings - never blocks
events: [PostToolUse]
async: true
timeout_ms: 2000
---

# Pattern Learning Hook (Async - Never Blocks)

## Philosophy: Learn From Success

This hook runs AFTER tool execution completes. It never blocks or interrupts workflow.
The goal is to capture what works well for future reference and continuous improvement.

## What We Capture

### 1. Successful Patterns
- Effective tool usage (e.g., "Used Edit with regex mode successfully")
- Time-saving shortcuts (e.g., "Grep before Read reduced context by 80%")
- Common solutions (e.g., "Fixed race condition with pytest-timeout")

### 2. Workflow Insights
- Which skills were invoked and their outcomes
- Sequential tool patterns (e.g., "Grep → Read → Edit" workflow)
- Parallel operations that worked well

### 3. Performance Metrics
- Tool execution time
- Context efficiency (tokens saved)
- Success/failure rates by tool

### 4. Error Recovery Patterns
- How errors were resolved
- Alternative approaches that worked
- Lessons learned from failures

## Storage Location

All learnings are stored asynchronously in:
- `.claude/metrics/successful-patterns.log` - Human-readable patterns
- `.claude/metrics/tool-usage.jsonl` - Structured metrics for analysis
- `.claude/metrics/workflow-insights.jsonl` - Workflow patterns

## Output Format

No output to user. All logging is silent and async.

Example log entry:
```json
{
  "timestamp": "2026-01-16T10:30:45Z",
  "tool": "Edit",
  "operation": "regex_replace",
  "files_affected": 1,
  "success": true,
  "duration_ms": 45,
  "context_saved": "Used regex to avoid quoting large code block",
  "pattern": "Edit with regex mode for multi-line changes"
}
```

## Analysis Features

These logs enable:
- Weekly pattern analysis reports
- Tool effectiveness dashboards
- Workflow optimization suggestions
- Skill improvement recommendations

## Performance Target

- Async execution: doesn't block main workflow
- Max duration: 2000ms (runs in background)
- No user-facing impact

## Integration with Skills

Metrics feed back into skill effectiveness tracking:
- Which skills are used most?
- Which skills have highest success rates?
- Which skills save the most time/tokens?

## Privacy

No sensitive data captured:
- File contents NOT logged
- Command outputs NOT logged
- Only metadata and patterns logged
