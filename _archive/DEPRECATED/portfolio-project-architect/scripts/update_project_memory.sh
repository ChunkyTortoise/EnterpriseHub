#!/bin/bash
# Update portfolio project memory with new information
# Zero-context execution - preserves project state

set -e

PROJECT_NAME=${1:-""}
UPDATE_TYPE=${2:-"progress"}
UPDATE_DATA=${3:-""}

if [ -z "$PROJECT_NAME" ]; then
    echo "❌ Project name required."
    echo "Usage: update_project_memory.sh <project_name> <update_type> [data]"
    echo ""
    echo "Update Types:"
    echo "  progress <phase> - Update current phase"
    echo "  metric <key> <value> - Update key metric"
    echo "  decision <description> - Log important decision"
    echo "  session <activity> - Log session activity"
    echo "  completion <percentage> - Update overall completion"
    exit 1
fi

MEMORY_DIR=".claude/memory/portfolio-projects"
PROJECT_DIR="${MEMORY_DIR}/${PROJECT_NAME}"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project '$PROJECT_NAME' not found in memory."
    exit 1
fi

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

echo "🔄 Updating Project Memory"
echo "========================="
echo "Project: ${PROJECT_NAME}"
echo "Type: ${UPDATE_TYPE}"
echo ""

case $UPDATE_TYPE in
    "progress")
        PHASE=${UPDATE_DATA:-"unknown"}
        echo "📈 Updating progress to phase: $PHASE"

        # Update progress.json
        jq --arg phase "$PHASE" --arg timestamp "$TIMESTAMP" '
            .current_phase = $phase |
            .phases[$phase].status = "in_progress" |
            .phases[$phase].started_at = $timestamp |
            if $phase == "discovery" then .completion_percentage = 25
            elif $phase == "architecture" then .completion_percentage = 50
            elif $phase == "scope_refinement" then .completion_percentage = 75
            elif $phase == "handoff_generation" then .completion_percentage = 90
            elif $phase == "complete" then .completion_percentage = 100
            else . end
        ' "$PROJECT_DIR/progress.json" > "$PROJECT_DIR/progress.json.tmp" && mv "$PROJECT_DIR/progress.json.tmp" "$PROJECT_DIR/progress.json"
        ;;

    "metric")
        METRIC_KEY=${UPDATE_DATA}
        METRIC_VALUE=${4:-""}
        echo "📊 Updating metric: $METRIC_KEY = $METRIC_VALUE"

        jq --arg key "$METRIC_KEY" --arg value "$METRIC_VALUE" '
            .key_metrics[$key] = $value
        ' "$PROJECT_DIR/progress.json" > "$PROJECT_DIR/progress.json.tmp" && mv "$PROJECT_DIR/progress.json.tmp" "$PROJECT_DIR/progress.json"
        ;;

    "decision")
        DECISION=${UPDATE_DATA}
        echo "🎯 Logging decision: $DECISION"

        # Append to project context
        echo "" >> "$PROJECT_DIR/project-context.md"
        echo "### Decision - $TIMESTAMP" >> "$PROJECT_DIR/project-context.md"
        echo "$DECISION" >> "$PROJECT_DIR/project-context.md"
        ;;

    "session")
        ACTIVITY=${UPDATE_DATA}
        echo "📝 Logging session activity: $ACTIVITY"

        # Append to session log
        echo "" >> "$PROJECT_DIR/session-log.md"
        echo "## Session Update - $TIMESTAMP" >> "$PROJECT_DIR/session-log.md"
        echo "**Activity**: $ACTIVITY" >> "$PROJECT_DIR/session-log.md"
        ;;

    "completion")
        PERCENTAGE=${UPDATE_DATA}
        echo "✅ Updating completion to: $PERCENTAGE%"

        jq --arg percentage "$PERCENTAGE" '
            .completion_percentage = ($percentage | tonumber)
        ' "$PROJECT_DIR/progress.json" > "$PROJECT_DIR/progress.json.tmp" && mv "$PROJECT_DIR/progress.json.tmp" "$PROJECT_DIR/progress.json"
        ;;

    "context")
        CONTEXT_UPDATE=${UPDATE_DATA}
        echo "📋 Updating project context"

        # Update specific context sections based on input
        echo "" >> "$PROJECT_DIR/project-context.md"
        echo "### Context Update - $TIMESTAMP" >> "$PROJECT_DIR/project-context.md"
        echo "$CONTEXT_UPDATE" >> "$PROJECT_DIR/project-context.md"
        ;;

    *)
        echo "❌ Unknown update type: $UPDATE_TYPE"
        echo "Available types: progress, metric, decision, session, completion, context"
        exit 1
        ;;
esac

echo "✅ Memory updated successfully"

# Display current status
if [ -f "$PROJECT_DIR/progress.json" ]; then
    current_phase=$(jq -r '.current_phase' "$PROJECT_DIR/progress.json")
    completion=$(jq -r '.completion_percentage' "$PROJECT_DIR/progress.json")
    echo ""
    echo "📊 Current Status:"
    echo "  Phase: $current_phase"
    echo "  Completion: $completion%"
fi