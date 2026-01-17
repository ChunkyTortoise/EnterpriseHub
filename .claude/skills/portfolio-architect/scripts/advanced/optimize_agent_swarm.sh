#!/bin/bash

# Agent Swarm Optimization for Portfolio Development
# Usage: ./optimize_agent_swarm.sh {project_name} {agent_count} {tier}
# Example: ./optimize_agent_swarm.sh "saas-portfolio" 5 enterprise

PROJECT_NAME="$1"
AGENT_COUNT="$2"
PROJECT_TIER="$3"

if [ -z "$PROJECT_NAME" ] || [ -z "$AGENT_COUNT" ]; then
    echo "Usage: $0 {project_name} {agent_count} [tier]"
    echo "Agent Count: 3, 5, 7 (recommended: 5)"
    echo "Tiers: basic, professional, enterprise"
    exit 1
fi

# Set defaults
PROJECT_TIER=${PROJECT_TIER:-professional}
MEMORY_ROOT=".claude/memory/portfolio-projects"
PROJECT_PATH="$MEMORY_ROOT/$PROJECT_NAME"

if [ ! -d "$PROJECT_PATH" ]; then
    echo "❌ Project memory not found: $PROJECT_PATH"
    echo "Run initialize_enhanced_memory.sh first"
    exit 1
fi

echo "🤖 Optimizing Agent Swarm Configuration"
echo "Project: $PROJECT_NAME"
echo "Agents: $AGENT_COUNT"
echo "Tier: $PROJECT_TIER"

# Define agent configurations based on count and tier
configure_agents() {
    local count=$1
    local tier=$2

    case $count in
        3)
            AGENTS=("market-intelligence" "technical-architecture" "client-materials")
            ;;
        5)
            AGENTS=("market-intelligence" "technical-architecture" "security-compliance" "performance-optimization" "client-materials")
            ;;
        7)
            AGENTS=("market-intelligence" "technical-architecture" "security-compliance" "performance-optimization" "ui-ux-design" "integration-architecture" "client-materials")
            ;;
        *)
            echo "❌ Unsupported agent count: $count"
            echo "Supported: 3, 5, 7"
            exit 1
            ;;
    esac
}

# Configure model selection based on tier
configure_models() {
    local tier=$1

    case $tier in
        basic)
            MODEL_MARKET="sonnet"
            MODEL_TECHNICAL="sonnet"
            MODEL_SECURITY="haiku"
            MODEL_PERFORMANCE="haiku"
            MODEL_UIUX="sonnet"
            MODEL_INTEGRATION="sonnet"
            MODEL_CLIENT="sonnet"
            ;;
        professional)
            MODEL_MARKET="sonnet"
            MODEL_TECHNICAL="opus"
            MODEL_SECURITY="sonnet"
            MODEL_PERFORMANCE="sonnet"
            MODEL_UIUX="opus"
            MODEL_INTEGRATION="sonnet"
            MODEL_CLIENT="opus"
            ;;
        enterprise)
            MODEL_MARKET="opus"
            MODEL_TECHNICAL="opus"
            MODEL_SECURITY="opus"
            MODEL_PERFORMANCE="opus"
            MODEL_UIUX="opus"
            MODEL_INTEGRATION="opus"
            MODEL_CLIENT="opus"
            ;;
    esac
}

configure_agents $AGENT_COUNT $PROJECT_TIER
configure_models $PROJECT_TIER

# Create agent swarm configuration
cat > "$PROJECT_PATH/agent-swarm-config.yaml" << EOF
# Agent Swarm Configuration for $PROJECT_NAME
# Generated: $(date)

project:
  name: "$PROJECT_NAME"
  tier: "$PROJECT_TIER"
  agent_count: $AGENT_COUNT

coordination:
  parallel_processing: true
  context_forking: true
  synchronization_points:
    - discovery_synthesis
    - architecture_review
    - quality_gates
    - final_integration

agents:
EOF

# Configure each agent
for agent in "${AGENTS[@]}"; do
    case $agent in
        market-intelligence)
            model_var="MODEL_MARKET"
            tools='["WebSearch", "Read", "Write"]'
            focus="competitive_analysis_market_trends"
            specialization="Market research, competitive intelligence, trend analysis"
            ;;
        technical-architecture)
            model_var="MODEL_TECHNICAL"
            tools='["Read", "Write", "Task"]'
            focus="system_design_optimization"
            specialization="Enterprise architecture, scalability planning, technology optimization"
            ;;
        security-compliance)
            model_var="MODEL_SECURITY"
            tools='["Read", "Bash"]'
            focus="security_vulnerability_compliance"
            specialization="Security assessment, compliance validation, enterprise standards"
            ;;
        performance-optimization)
            model_var="MODEL_PERFORMANCE"
            tools='["Read", "Bash"]'
            focus="scalability_performance_benchmarking"
            specialization="Performance analysis, load testing, optimization strategies"
            ;;
        ui-ux-design)
            model_var="MODEL_UIUX"
            tools='["Write", "Read", "Task"]'
            focus="user_experience_interface_design"
            specialization="UI/UX design, user research, interface optimization"
            ;;
        integration-architecture)
            model_var="MODEL_INTEGRATION"
            tools='["Read", "Write", "Task"]'
            focus="system_integration_connectivity"
            specialization="Enterprise integration, API design, data flow optimization"
            ;;
        client-materials)
            model_var="MODEL_CLIENT"
            tools='["Write", "Read"]'
            focus="presentation_materials_roi_calculation"
            specialization="Professional deliverables, ROI analysis, client presentations"
            ;;
    esac

    # Get model for this agent
    model_value=$(eval echo \$$model_var)

    cat >> "$PROJECT_PATH/agent-swarm-config.yaml" << EOF
  $agent:
    type: "general-purpose"
    model: "$model_value"
    context: "fork"
    tools: $tools
    focus: "$focus"
    priority: "high"
    specialization: "$specialization"
    output_file: "agent-findings/${agent}.md"
EOF
done

# Add coordination patterns
cat >> "$PROJECT_PATH/agent-swarm-config.yaml" << EOF

coordination_patterns:
  parallel_research:
    agents: ["market-intelligence", "technical-architecture"]
    duration: "3-5 days"
    synchronization: "findings_synthesis"

  sequential_analysis:
    agents: ["technical-architecture", "security-compliance", "performance-optimization"]
    mode: "sequential"
    duration: "5-7 days"
    dependencies: true

  integrated_synthesis:
    agents: "all"
    mode: "collaborative"
    duration: "2-3 days"
    output: "comprehensive_recommendations"

quality_gates:
  agent_validation:
    - consistency_checks
    - gap_analysis
    - integration_validation
    - business_alignment
  automated_hooks:
    - agent_startup_validation
    - progress_checkpoints
    - quality_gate_enforcement
    - completion_validation

resource_optimization:
  cost_management: true
  model_selection: "tier_based"
  parallel_execution: true
  context_efficiency: true
EOF

# Update progress tracking
jq --arg count "$AGENT_COUNT" '.agent_coordination.agents_deployed = ($count | tonumber) | .agent_coordination.parallel_streams = ($count | tonumber)' "$PROJECT_PATH/progress.json" > "$PROJECT_PATH/progress.tmp" && mv "$PROJECT_PATH/progress.tmp" "$PROJECT_PATH/progress.json"

# Log agent swarm deployment
echo "$(date): Agent swarm optimized - $AGENT_COUNT agents configured for $PROJECT_TIER tier" >> "$PROJECT_PATH/session-log.md"

echo "✅ Agent Swarm Configuration Complete!"
echo ""
echo "🤖 Deployed Agents ($AGENT_COUNT):"
for agent in "${AGENTS[@]}"; do
    model_var_name="MODEL_${agent^^}"
    model_var_name=${model_var_name//-/_}
    model_value=$(eval echo \$$model_var_name)
    echo "├── $agent ($model_value)"
done
echo ""
echo "⚡ Coordination Features:"
echo "├── Parallel processing: Enabled"
echo "├── Context forking: Enabled"
echo "├── Synchronization points: 4 configured"
echo "└── Quality gates: Automated"
echo ""
echo "📊 Performance Optimization:"
echo "├── Tier: $PROJECT_TIER"
echo "├── Model selection: Optimized for tier"
echo "├── Resource management: Enabled"
echo "└── Cost optimization: Active"
echo ""
echo "🔄 Next Steps:"
echo "1. Monitor agent status: ./monitor_agent_status.sh $PROJECT_NAME"
echo "2. Begin discovery phase with agent coordination"
echo "3. Quality validation: ./validate_quality_gates.sh $PROJECT_NAME"