#!/bin/bash
# Initialize portfolio project memory system
# Zero-context execution - creates project memory structure

set -e

PROJECT_NAME=${1:-"portfolio-project"}
PROJECT_TYPE=${2:-"saas"}

echo "🧠 Portfolio Project Memory Initialization"
echo "=========================================="
echo "Project: ${PROJECT_NAME}"
echo "Type: ${PROJECT_TYPE}"
echo ""

# Create memory directory structure
MEMORY_DIR=".claude/memory/portfolio-projects"
mkdir -p "${MEMORY_DIR}/${PROJECT_NAME}"

# Create project memory files
cat > "${MEMORY_DIR}/${PROJECT_NAME}/project-context.md" << EOF
# Portfolio Project Memory: ${PROJECT_NAME}

**Project Type**: ${PROJECT_TYPE}
**Created**: $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Status**: Discovery Phase

## Strategic Context
- **Service Area**: [To be defined]
- **Target Client Type**: [To be defined]
- **Current Project Range**: [To be defined]
- **Target Project Range**: [To be defined]
- **Key Expertise**: [To be defined]

## Business Objectives
- **Revenue Goal**: [To be defined]
- **Market Positioning**: [To be defined]
- **Competitive Advantage**: [To be defined]

## Technical Specifications
- **Technology Stack**: [To be defined]
- **Core Features**: [To be defined]
- **Integration Requirements**: [To be defined]

## Progress Tracking
- [ ] Discovery Phase Complete
- [ ] Architecture Design Complete
- [ ] Scope Refinement Complete
- [ ] Auto Claude Handoff Generated
- [ ] Development Started
- [ ] MVP Complete
- [ ] Demo Environment Ready
- [ ] Client Presentation Materials Created

## Key Decisions
[Decision log will be updated throughout project]

## Lessons Learned
[Insights will be captured throughout development]

## Success Metrics
- **Target ROI**: [To be calculated]
- **Timeline**: [To be defined]
- **Quality Gates**: [To be defined]

EOF

# Create session log
cat > "${MEMORY_DIR}/${PROJECT_NAME}/session-log.md" << EOF
# Session Log: ${PROJECT_NAME}

## Session 1 - $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Phase**: Project Initialization
**Activities**:
- Memory system initialized
- Project structure created

**Next Steps**:
- Begin strategic discovery
- Define business objectives
- Establish technical requirements

EOF

# Create progress tracker
cat > "${MEMORY_DIR}/${PROJECT_NAME}/progress.json" << EOF
{
  "project_name": "${PROJECT_NAME}",
  "project_type": "${PROJECT_TYPE}",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "current_phase": "discovery",
  "completion_percentage": 0,
  "phases": {
    "discovery": {
      "status": "in_progress",
      "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
      "completion": 10
    },
    "architecture": {
      "status": "pending",
      "started_at": null,
      "completion": 0
    },
    "scope_refinement": {
      "status": "pending",
      "started_at": null,
      "completion": 0
    },
    "handoff_generation": {
      "status": "pending",
      "started_at": null,
      "completion": 0
    }
  },
  "key_metrics": {
    "estimated_investment": null,
    "projected_roi": null,
    "target_project_value": null,
    "timeline_weeks": null
  }
}
EOF

# Create configuration file for Claude integration
cat > "${MEMORY_DIR}/${PROJECT_NAME}/claude-config.yaml" << EOF
# Claude Code configuration for ${PROJECT_NAME}
project_memory:
  enabled: true
  auto_load: true
  context_files:
    - project-context.md
    - session-log.md

agent_preferences:
  primary_model: opus
  thinking_mode: harder
  parallel_agents: true

quality_gates:
  code_coverage: 90
  security_scan: true
  performance_check: true
  documentation_required: true

skills:
  - portfolio-project-architect
  - test-driven-development
  - security-first-design
  - performance-optimization

hooks:
  pre_commit: portfolio-quality-check
  post_phase: update-memory
  session_end: save-progress

EOF

echo "✅ Project Memory Initialized Successfully"
echo ""
echo "📁 Memory Structure Created:"
echo "  ${MEMORY_DIR}/${PROJECT_NAME}/"
echo "  ├── project-context.md (Strategic and technical context)"
echo "  ├── session-log.md (Session history and activities)"
echo "  ├── progress.json (Automated progress tracking)"
echo "  └── claude-config.yaml (Claude Code configuration)"
echo ""
echo "🎯 Next Steps:"
echo "  1. Load project memory: Use 'load portfolio memory ${PROJECT_NAME}'"
echo "  2. Begin discovery: Use portfolio-project-architect skill"
echo "  3. Update context: Memory will auto-update throughout project"
echo ""
echo "💡 Memory Features:"
echo "  • Cross-session context preservation"
echo "  • Automatic progress tracking"
echo "  • Decision and lesson capture"
echo "  • Claude Code integration"