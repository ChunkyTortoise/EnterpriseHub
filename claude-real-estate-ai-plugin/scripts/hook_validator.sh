#!/bin/bash
# Simplified Hook Validator for EnterpriseHub
# Uses regex and logic to avoid LLM "prompt injection" hallucinations.

TOOL_NAME="$1"
TOOL_ARGUMENTS="$2"

# 1. ALLOW everything for .md files
if [[ "$TOOL_ARGUMENTS" == *".md"* ]]; then
    echo '{"decision": "ALLOW"}'
    exit 0
fi

# 2. ALLOW everything for .claude/hooks
if [[ "$TOOL_ARGUMENTS" == *".claude/hooks"* ]]; then
    echo '{"decision": "ALLOW"}'
    exit 0
fi

# 3. BLOCK actual secrets
SECRET_PATTERN='(sk-ant-api03-[a-zA-Z0-9\-_]{93}|sk-[a-zA-Z0-9]{48}|AIza[a-zA-Z0-9]{35}|:[^@\/]+@)'
if echo "$TOOL_ARGUMENTS" | grep -E "$SECRET_PATTERN" > /dev/null; then
    echo '{"decision": "DENY", "reason": "Actual secret detected in tool arguments"}'
    exit 0
fi

# 4. BLOCK destructive bash
if [[ "$TOOL_NAME" == "Bash" ]]; then
    if [[ "$TOOL_ARGUMENTS" == *"rm -rf /"* ]] || [[ "$TOOL_ARGUMENTS" == *"rm -rf .git"* ]]; then
        echo '{"decision": "DENY", "reason": "Destructive bash command blocked"}'
        exit 0
    fi
fi

# 5. Default ALLOW
echo '{"decision": "ALLOW"}'
exit 0
