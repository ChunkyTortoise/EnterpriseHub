#!/bin/bash
# Session Summary - NEVER BLOCKS COMPLETION
# Runs asynchronously when task is marked complete

set -euo pipefail

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
SESSION_ID=$(date +%Y-%m-%d)-$(head -c 6 /dev/urandom | base64 | tr -dc 'a-z0-9')

# Ensure metrics directory exists
mkdir -p .claude/metrics

# ============================================================================
# COLLECT SESSION METRICS (Silent)
# ============================================================================

# Count tool usage this session
TOTAL_TOOLS=$(wc -l < .claude/metrics/tool-sequence.log 2>/dev/null || echo 0)

# Count warnings issued
CSV_WARNINGS=$(grep -c "csv_access" .claude/metrics/pattern-learning.log 2>/dev/null || echo 0)
LARGE_FILE_WARNINGS=$(grep -c "large_file_access" .claude/metrics/pattern-learning.log 2>/dev/null || echo 0)
SUDO_WARNINGS=$(grep -c "sudo_command" .claude/metrics/pattern-learning.log 2>/dev/null || echo 0)
TOTAL_WARNINGS=$((CSV_WARNINGS + LARGE_FILE_WARNINGS + SUDO_WARNINGS))

# Count successful operations
SUCCESSFUL_OPS=$(wc -l < .claude/metrics/successful-patterns.log 2>/dev/null || echo 0)

# Detect workflow patterns used
GREP_BEFORE_READ=$(grep -c "grep_before_read" .claude/metrics/workflow-insights.jsonl 2>/dev/null || echo 0)
READ_THEN_EDIT=$(grep -c "read_then_edit" .claude/metrics/workflow-insights.jsonl 2>/dev/null || echo 0)

# ============================================================================
# GENERATE SESSION SUMMARY (JSONL Format)
# ============================================================================

cat >> .claude/metrics/session-summaries.jsonl <<EOF
{
  "session_id": "$SESSION_ID",
  "timestamp": "$TIMESTAMP",
  "metrics": {
    "total_tools_used": $TOTAL_TOOLS,
    "successful_operations": $SUCCESSFUL_OPS,
    "warnings": $TOTAL_WARNINGS,
    "blocks": 0
  },
  "warnings_breakdown": {
    "csv_access": $CSV_WARNINGS,
    "large_file_access": $LARGE_FILE_WARNINGS,
    "sudo_command": $SUDO_WARNINGS
  },
  "workflow_patterns": {
    "grep_before_read": $GREP_BEFORE_READ,
    "read_then_edit": $READ_THEN_EDIT
  }
}
EOF

# ============================================================================
# OPTIONAL: USER-FACING SUMMARY (Can be disabled)
# ============================================================================

# Uncomment to show summary to user
# echo ""
# echo "✅ Session Complete"
# echo "- $SUCCESSFUL_OPS successful operations"
# echo "- $TOTAL_WARNINGS warnings (all allowed)"
# echo "- 0 blocks"
# echo ""
# echo "See .claude/metrics/session-summaries.jsonl for details"

# ============================================================================
# CLEANUP FOR NEXT SESSION (Optional)
# ============================================================================

# Reset tool sequence log for next session
> .claude/metrics/tool-sequence.log

# ============================================================================
# ASYNC EXECUTION - NO BLOCKING
# ============================================================================

exit 0
