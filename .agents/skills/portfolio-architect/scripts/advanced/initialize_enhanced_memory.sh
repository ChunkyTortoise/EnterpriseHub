#!/bin/bash

# Enhanced Memory Initialization for Portfolio Projects
# Usage: ./initialize_enhanced_memory.sh {project_name} {type} {tier}
# Example: ./initialize_enhanced_memory.sh "saas-portfolio" saas enterprise

PROJECT_NAME="$1"
PROJECT_TYPE="$2"
PROJECT_TIER="$3"

if [ -z "$PROJECT_NAME" ] || [ -z "$PROJECT_TYPE" ]; then
    echo "Usage: $0 {project_name} {type} [tier]"
    echo "Types: saas, enterprise, consulting, framework"
    echo "Tiers: basic, professional, enterprise"
    exit 1
fi

# Set defaults
PROJECT_TIER=${PROJECT_TIER:-professional}
MEMORY_ROOT=".claude/memory/portfolio-projects"
PROJECT_PATH="$MEMORY_ROOT/$PROJECT_NAME"

echo "🚀 Initializing Enhanced Portfolio Memory System"
echo "Project: $PROJECT_NAME"
echo "Type: $PROJECT_TYPE"
echo "Tier: $PROJECT_TIER"
echo "Path: $PROJECT_PATH"

# Create enhanced directory structure
mkdir -p "$PROJECT_PATH"/{agent-findings,quality-gates,handoff-history,client-materials/{presentations,roi-analysis,technical-docs,demo-scripts}}

# Initialize core memory files
cat > "$PROJECT_PATH/project-context.md" << EOF
# $PROJECT_NAME - Project Context

## Project Overview
- **Name**: $PROJECT_NAME
- **Type**: $PROJECT_TYPE
- **Tier**: $PROJECT_TIER
- **Created**: $(date)
- **Status**: Initialized

## Strategic Context
- **Target Market**: TBD
- **Value Proposition**: TBD
- **Competitive Advantages**: TBD
- **Success Criteria**: TBD

## Technical Requirements
- **Technology Stack**: TBD
- **Architecture Pattern**: TBD
- **Quality Standards**: $PROJECT_TIER level
- **Performance Targets**: TBD

## Business Objectives
- **Revenue Target**: TBD
- **ROI Projection**: TBD
- **Client Profile**: TBD
- **Timeline**: TBD

## Memory Updates
- $(date): Project initialized with enhanced memory structure
EOF

# Initialize session log
cat > "$PROJECT_PATH/session-log.md" << EOF
# $PROJECT_NAME - Session Activity Log

## Session History

### $(date) - Project Initialization
- Enhanced memory structure created
- Project type: $PROJECT_TYPE
- Project tier: $PROJECT_TIER
- Agent coordination: Enabled
- Quality gates: Configured

EOF

# Initialize progress tracking
cat > "$PROJECT_PATH/progress.json" << EOF
{
  "project_name": "$PROJECT_NAME",
  "project_type": "$PROJECT_TYPE",
  "project_tier": "$PROJECT_TIER",
  "created_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "initialized",
  "phase": "planning",
  "phases": {
    "discovery": {"status": "pending", "progress": 0},
    "architecture": {"status": "pending", "progress": 0},
    "refinement": {"status": "pending", "progress": 0},
    "generation": {"status": "pending", "progress": 0}
  },
  "quality_gates": {
    "code_coverage": 0,
    "security_score": 0,
    "performance_score": 0,
    "documentation_score": 0
  },
  "roi_tracking": {
    "target_roi": null,
    "projected_revenue": null,
    "investment_estimate": null,
    "payback_months": null
  },
  "agent_coordination": {
    "enabled": true,
    "agents_deployed": 0,
    "parallel_streams": 0,
    "context_forking": true
  }
}
EOF

# Initialize Claude configuration for the project
cat > "$PROJECT_PATH/claude-config.yaml" << EOF
# Claude Code Configuration for $PROJECT_NAME

project:
  name: "$PROJECT_NAME"
  type: "$PROJECT_TYPE"
  tier: "$PROJECT_TIER"

agents:
  coordination: enabled
  parallel_processing: true
  context_forking: true
  max_agents: 5

memory:
  persistence: enabled
  cross_session: true
  auto_save: true
  synthesis: enabled

quality_gates:
  enabled: true
  automated_validation: true
  standards_level: "$PROJECT_TIER"
  continuous_monitoring: true

hooks:
  pre_tool_use:
    - validate-portfolio-standards
    - check-memory-context
  post_tool_use:
    - update-memory-auto
    - quality-gate-check
  stop:
    - compile-deliverables
    - generate-handoff

skills:
  hot_reload: true
  progressive_disclosure: true
  context_optimization: true

deliverables:
  professional_materials: true
  roi_analysis: true
  client_presentations: true
  technical_documentation: true
EOF

# Create agent findings structure
mkdir -p "$PROJECT_PATH/agent-findings"
touch "$PROJECT_PATH/agent-findings/synthesis.md"
touch "$PROJECT_PATH/agent-findings/market-intelligence.md"
touch "$PROJECT_PATH/agent-findings/technical-architecture.md"
touch "$PROJECT_PATH/agent-findings/security-compliance.md"
touch "$PROJECT_PATH/agent-findings/performance-optimization.md"
touch "$PROJECT_PATH/agent-findings/client-materials.md"

# Initialize quality gates log
cat > "$PROJECT_PATH/quality-gates.log" << EOF
# Quality Gates Log for $PROJECT_NAME

## Quality Standards: $PROJECT_TIER Level

$(date): Quality gates initialized
- Code coverage target: 90%+
- Security scan: Zero critical vulnerabilities
- Performance: <2-second load times
- Documentation: Comprehensive and validated
- Business readiness: Client-presentation quality

EOF

echo "✅ Enhanced memory system initialized successfully!"
echo ""
echo "📁 Memory Structure Created:"
echo "├── project-context.md (Strategic context and decisions)"
echo "├── session-log.md (Complete activity history)"
echo "├── progress.json (Real-time metrics and coordination)"
echo "├── claude-config.yaml (Project-specific Claude settings)"
echo "├── agent-findings/ (Multi-agent research synthesis)"
echo "├── quality-gates.log (Automated validation results)"
echo "├── client-materials/ (Professional deliverables)"
echo "└── handoff-history/ (Generated Auto Claude prompts)"
echo ""
echo "🔄 Next Steps:"
echo "1. Load project context: ./load_project_context.sh $PROJECT_NAME"
echo "2. Deploy agent swarm: ./optimize_agent_swarm.sh $PROJECT_NAME 5 $PROJECT_TIER"
echo "3. Begin discovery: Trigger 'portfolio advanced $PROJECT_NAME'"