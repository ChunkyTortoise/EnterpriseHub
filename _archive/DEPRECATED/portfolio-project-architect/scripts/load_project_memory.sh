#!/bin/bash
# Load portfolio project memory into current session
# Zero-context execution - provides memory context for Claude

set -e

PROJECT_NAME=${1:-""}
MEMORY_DIR=".claude/memory/portfolio-projects"

if [ -z "$PROJECT_NAME" ]; then
    echo "📋 Available Portfolio Projects:"
    echo "==============================="
    if [ -d "$MEMORY_DIR" ]; then
        for project in "$MEMORY_DIR"/*; do
            if [ -d "$project" ]; then
                project_name=$(basename "$project")
                if [ -f "$project/progress.json" ]; then
                    phase=$(jq -r '.current_phase' "$project/progress.json" 2>/dev/null || echo "unknown")
                    completion=$(jq -r '.completion_percentage' "$project/progress.json" 2>/dev/null || echo "0")
                    echo "  📁 $project_name (Phase: $phase, Progress: $completion%)"
                else
                    echo "  📁 $project_name (Status: unknown)"
                fi
            fi
        done
    else
        echo "  No portfolio projects found. Run initialize_project_memory.sh first."
    fi
    echo ""
    echo "Usage: load_project_memory.sh <project_name>"
    exit 0
fi

PROJECT_DIR="${MEMORY_DIR}/${PROJECT_NAME}"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Project '$PROJECT_NAME' not found in memory."
    echo "Available projects:"
    for project in "$MEMORY_DIR"/*; do
        if [ -d "$project" ]; then
            echo "  - $(basename "$project")"
        fi
    done
    exit 1
fi

echo "🧠 Loading Portfolio Project Memory"
echo "=================================="
echo "Project: ${PROJECT_NAME}"
echo ""

# Load and display project context
if [ -f "$PROJECT_DIR/project-context.md" ]; then
    echo "📊 Project Context:"
    echo "=================="
    cat "$PROJECT_DIR/project-context.md"
    echo ""
fi

# Display current progress
if [ -f "$PROJECT_DIR/progress.json" ]; then
    echo "📈 Current Progress:"
    echo "==================="
    current_phase=$(jq -r '.current_phase' "$PROJECT_DIR/progress.json")
    completion=$(jq -r '.completion_percentage' "$PROJECT_DIR/progress.json")

    echo "Current Phase: $current_phase"
    echo "Overall Completion: $completion%"
    echo ""

    echo "Phase Status:"
    jq -r '.phases | to_entries[] | "  \(.key): \(.value.status) (\(.value.completion)%)"' "$PROJECT_DIR/progress.json"
    echo ""
fi

# Display recent session activities
if [ -f "$PROJECT_DIR/session-log.md" ]; then
    echo "📝 Recent Session Activity:"
    echo "=========================="
    tail -20 "$PROJECT_DIR/session-log.md"
    echo ""
fi

# Display key metrics if available
if [ -f "$PROJECT_DIR/progress.json" ]; then
    echo "🎯 Key Metrics:"
    echo "==============="
    investment=$(jq -r '.key_metrics.estimated_investment // "Not set"' "$PROJECT_DIR/progress.json")
    roi=$(jq -r '.key_metrics.projected_roi // "Not set"' "$PROJECT_DIR/progress.json")
    target_value=$(jq -r '.key_metrics.target_project_value // "Not set"' "$PROJECT_DIR/progress.json")
    timeline=$(jq -r '.key_metrics.timeline_weeks // "Not set"' "$PROJECT_DIR/progress.json")

    echo "  Estimated Investment: $investment"
    echo "  Projected ROI: $roi"
    echo "  Target Project Value: $target_value"
    echo "  Timeline (weeks): $timeline"
    echo ""
fi

# Check for Claude configuration
if [ -f "$PROJECT_DIR/claude-config.yaml" ]; then
    echo "🔧 Claude Configuration Loaded:"
    echo "==============================="
    echo "Memory auto-load: enabled"
    echo "Recommended model: $(grep 'primary_model:' "$PROJECT_DIR/claude-config.yaml" | cut -d' ' -f4)"
    echo "Thinking mode: $(grep 'thinking_mode:' "$PROJECT_DIR/claude-config.yaml" | cut -d' ' -f4)"
    echo ""
fi

echo "✅ Project Memory Loaded Successfully"
echo ""
echo "🎯 Recommended Next Actions:"
if [ "$current_phase" = "discovery" ]; then
    echo "  • Continue strategic discovery with portfolio-project-architect skill"
    echo "  • Define business objectives and target client profile"
    echo "  • Establish competitive advantage factors"
elif [ "$current_phase" = "architecture" ]; then
    echo "  • Review and approve technical architecture recommendations"
    echo "  • Select optimal Claude Code toolchain configuration"
    echo "  • Validate technology stack choices"
elif [ "$current_phase" = "scope_refinement" ]; then
    echo "  • Finalize project scope and requirements"
    echo "  • Establish success criteria and quality gates"
    echo "  • Prepare for Auto Claude handoff generation"
elif [ "$current_phase" = "handoff_generation" ]; then
    echo "  • Generate comprehensive Auto Claude handoff prompt"
    echo "  • Validate development approach and agent configuration"
    echo "  • Prepare for development phase"
else
    echo "  • Continue with current phase: $current_phase"
fi

echo ""
echo "💡 Memory Features Active:"
echo "  • Context preservation across sessions"
echo "  • Automatic progress tracking"
echo "  • Decision and lesson logging"
echo "  • Claude Code integration"