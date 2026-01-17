#!/bin/bash
# Permissive Security Advisory - RARELY BLOCKS
# Philosophy: Trust the developer, block only critical security violations

set -euo pipefail

TOOL_NAME=$1
TOOL_PARAMS=${2:-"{}"}

# Helper function for logging (silent, for metrics)
log_pattern() {
    local pattern=$1
    local severity=$2
    mkdir -p .claude/metrics
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)|$severity|$pattern" >> .claude/metrics/pattern-learning.log
}

# Helper function for warnings (visible to user)
warn() {
    echo "⚠️  Warning: $1"
    echo "Proceeding anyway (permissive mode)..."
}

# Helper function for blocks (rare)
block() {
    echo "⛔ BLOCK: $1"
    echo "$2"
    exit 1
}

# ============================================================================
# CRITICAL BLOCKS ONLY (Actual Secrets and Truly Destructive Commands)
# ============================================================================

case $TOOL_NAME in
  "Read"|"Write"|"Edit")
    FILE_PATH=$(echo "$TOOL_PARAMS" | jq -r '.file_path // .path // ""' 2>/dev/null || echo "")

    # BLOCK: Actual secrets files
    if [[ $FILE_PATH =~ ^\.env$ ]]; then
      block "Cannot access .env file" "Use .env.example for reference instead."
    fi

    if [[ $FILE_PATH =~ ^\.env\.local$ ]] || [[ $FILE_PATH =~ ^\.env\.production$ ]]; then
      block "Cannot access environment secrets file: $FILE_PATH" "Use .env.example for reference instead."
    fi

    if [[ $FILE_PATH =~ \.(key|pem|crt)$ ]]; then
      block "Cannot access certificate/key file: $FILE_PATH" "These files contain sensitive cryptographic material."
    fi

    if [[ $FILE_PATH =~ ^secrets/ ]]; then
      block "Cannot access secrets directory: $FILE_PATH" "This directory contains sensitive credentials."
    fi

    # WARN: CSV files (may contain customer data)
    if [[ $FILE_PATH =~ \.csv$ ]]; then
      warn "Accessing CSV file: $FILE_PATH (may contain customer data)"
      log_pattern "csv_access:$FILE_PATH" "warning"
    fi

    # WARN: Analytics data directory
    if [[ $FILE_PATH =~ ^data/analytics/ ]]; then
      warn "Accessing analytics data: $FILE_PATH (may contain PII)"
      log_pattern "analytics_access:$FILE_PATH" "warning"
    fi

    # WARN: Large files (>10MB context pollution)
    if [[ -f $FILE_PATH ]] && [[ $(stat -f%z "$FILE_PATH" 2>/dev/null || echo 0) -gt 10485760 ]]; then
      warn "Large file access: $FILE_PATH (may pollute context)"
      log_pattern "large_file_access:$FILE_PATH" "warning"
    fi
    ;;

  "Bash")
    COMMAND=$(echo "$TOOL_PARAMS" | jq -r '.command // ""' 2>/dev/null || echo "")

    # BLOCK: Truly destructive commands (system-wide)
    if [[ $COMMAND =~ rm[[:space:]]+-[^[:space:]]*rf[^[:space:]]*[[:space:]]+/ ]] || [[ $COMMAND =~ ^rm[[:space:]]+-rf[[:space:]]/$ ]]; then
      block "Extremely destructive command blocked: $COMMAND" "This would delete the entire filesystem. Please be more specific."
    fi

    if [[ $COMMAND =~ DROP[[:space:]]+DATABASE ]] && ! [[ $COMMAND =~ WHERE ]]; then
      block "Unqualified DROP DATABASE blocked: $COMMAND" "Add WHERE clause or specify database name explicitly."
    fi

    if [[ $COMMAND =~ ^sudo[[:space:]]+rm ]]; then
      block "Privileged deletion blocked: $COMMAND" "This requires manual confirmation outside of automation."
    fi

    # WARN: Potentially risky commands (but allow)
    if [[ $COMMAND =~ rm[[:space:]]+-rf ]] && ! [[ $COMMAND =~ rm[[:space:]]+-rf[[:space:]]+/ ]]; then
      warn "Potentially risky deletion: $COMMAND"
      log_pattern "risky_rm:$COMMAND" "warning"
    fi

    if [[ $COMMAND =~ ^sudo ]] && ! [[ $COMMAND =~ ^sudo[[:space:]]+rm ]]; then
      warn "Privileged command: $COMMAND"
      log_pattern "sudo_command:$COMMAND" "warning"
    fi

    if [[ $COMMAND =~ chmod[[:space:]]+777 ]]; then
      warn "Insecure permissions: $COMMAND (chmod 777 is overly permissive)"
      log_pattern "chmod_777:$COMMAND" "warning"
    fi

    if [[ $COMMAND =~ (ALTER|DROP|TRUNCATE)[[:space:]]+TABLE ]]; then
      warn "Database schema modification: $COMMAND"
      log_pattern "schema_change:$COMMAND" "warning"
    fi
    ;;
esac

# ============================================================================
# SILENT LOGGING (Learning Patterns - No User Output)
# ============================================================================

# Log tool usage for metrics (silent)
log_pattern "tool_use:$TOOL_NAME" "info"

# Detect patterns for learning (silent)
case $TOOL_NAME in
  "Write")
    CONTENT=$(echo "$TOOL_PARAMS" | jq -r '.content // ""' 2>/dev/null || echo "")

    # Log hardcoded values (for learning, not blocking)
    if echo "$CONTENT" | grep -qE '(API_KEY|SECRET|PASSWORD|TOKEN)[[:space:]]*=[[:space:]]*["\047][^"\047]+["\047]'; then
      log_pattern "hardcoded_value_detected" "info"
    fi
    ;;

  "Edit")
    # Log successful edit patterns
    log_pattern "edit_operation:successful" "info"
    ;;
esac

# ============================================================================
# DEFAULT: ALLOW
# ============================================================================

# If we made it here, allow the operation
exit 0
