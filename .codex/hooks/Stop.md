---
name: Session Summary (Non-Blocking)
description: Summarize accomplishments and learnings - never blocks completion
events: [Stop]
async: true
timeout_ms: 3000
---

# Session Summary Hook (Async - Never Blocks)

## Philosophy: Reflect and Learn

This hook runs when a task is marked complete. It never blocks completion or deployment.
The goal is to document accomplishments, capture learnings, and suggest improvements.

## What We Summarize

### 1. Accomplishments
- Files created/modified
- Features implemented
- Tests written
- Issues resolved

### 2. Warnings Given
- How many warnings were issued
- Which warnings were most common
- Whether warnings led to improvements

### 3. Patterns Learned
- New patterns discovered
- Effective workflows used
- Time/token savings achieved

### 4. Suggestions for Next Time
- Process improvements
- Tool usage optimizations
- Skill recommendations

## Summary Format

Stored in `.claude/metrics/session-summaries.jsonl`:

```json
{
  "session_id": "2026-01-16-abc123",
  "timestamp": "2026-01-16T10:45:00Z",
  "duration_minutes": 23,
  "accomplishments": {
    "files_modified": 5,
    "tests_added": 12,
    "features_completed": ["user-auth", "rate-limiting"]
  },
  "warnings_issued": {
    "csv_access": 2,
    "large_file_access": 1,
    "sudo_command": 0
  },
  "patterns_captured": [
    "Used TDD skill effectively for auth feature",
    "Grep before Read pattern saved ~15K tokens",
    "Parallel agent coordination reduced time by 40%"
  ],
  "suggestions": [
    "Consider using defense-in-depth skill for auth code review",
    "CSV files could be moved to data/analytics/ for better organization"
  ],
  "metrics": {
    "total_tools_used": 47,
    "successful_operations": 45,
    "warnings": 3,
    "blocks": 0,
    "estimated_tokens_saved": 15000
  }
}
```

## Weekly Rollup

Every Monday, generate summary report:
- Most productive workflows
- Most effective skills
- Common warnings (patterns to address)
- Suggested process improvements

## Integration with Metrics

Feeds into:
- `.claude/metrics/weekly-summary.md` - Human-readable report
- `.claude/metrics/skill-effectiveness.json` - Skill usage analytics
- `.claude/metrics/continuous-improvement.json` - Improvement suggestions

## Output to User

Optional summary message (can be disabled):

```
✅ Session Complete
- 5 files modified, 12 tests added
- 2 features implemented
- 3 warnings (all allowed)
- ~15K tokens saved through efficient workflows

See .claude/metrics/session-summaries.jsonl for details
```

## Performance Target

- Async execution: runs after completion signal sent
- Max duration: 3000ms
- No impact on user workflow

## Privacy & Security

- No sensitive data in summaries
- Aggregated metrics only
- Optional summary message (can be silenced)
