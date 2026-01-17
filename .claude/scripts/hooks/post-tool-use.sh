#!/bin/bash
# Pattern Learning - NEVER BLOCKS
# Runs asynchronously after tool execution to capture successful patterns

set -euo pipefail

TOOL_NAME=$1
RESULT=${2:-"{}"}
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Ensure metrics directory exists
mkdir -p .claude/metrics

# ============================================================================
# SILENT PATTERN LOGGING (No User Output)
# ============================================================================

# Simple success log (human-readable)
echo "✅ $TIMESTAMP | $TOOL_NAME | Success" >> .claude/metrics/successful-patterns.log

# Structured metrics (machine-readable JSONL)
cat >> .claude/metrics/tool-usage.jsonl <<EOF
{"timestamp":"$TIMESTAMP","tool":"$TOOL_NAME","success":true,"async":true}
EOF

# ============================================================================
# WORKFLOW PATTERN DETECTION (Learning)
# ============================================================================

# Track sequential tool patterns
LAST_TOOL=$(tail -1 .claude/metrics/tool-sequence.log 2>/dev/null || echo "")
echo "$TOOL_NAME" >> .claude/metrics/tool-sequence.log

# Detect common workflows
if [[ $LAST_TOOL == "Grep" ]] && [[ $TOOL_NAME == "Read" ]]; then
    cat >> .claude/metrics/workflow-insights.jsonl <<EOF
{"timestamp":"$TIMESTAMP","pattern":"grep_before_read","benefit":"reduced_context_loading"}
EOF
fi

if [[ $LAST_TOOL == "Read" ]] && [[ $TOOL_NAME == "Edit" ]]; then
    cat >> .claude/metrics/workflow-insights.jsonl <<EOF
{"timestamp":"$TIMESTAMP","pattern":"read_then_edit","benefit":"targeted_modification"}
EOF
fi

# ============================================================================
# PERFORMANCE METRICS (Silent)
# ============================================================================

# Track tool usage frequency (for effectiveness analysis)
TOOL_COUNT=$(grep -c "^$TOOL_NAME$" .claude/metrics/tool-sequence.log 2>/dev/null || echo 0)

if (( TOOL_COUNT > 100 )); then
    # High-usage tool - candidate for optimization
    cat >> .claude/metrics/workflow-insights.jsonl <<EOF
{"timestamp":"$TIMESTAMP","insight":"high_tool_usage","tool":"$TOOL_NAME","count":$TOOL_COUNT}
EOF
fi

# ============================================================================
# NO USER OUTPUT - ASYNC BACKGROUND LOGGING ONLY
# ============================================================================

# Continue immediately (async execution)
exit 0
