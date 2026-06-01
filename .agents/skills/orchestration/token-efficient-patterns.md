# Token-Efficient Agent Patterns
*Based on Advanced Agent Coordination Research (January 2026)*

## Purpose
Apply progressive loading concepts within current Claude Code limitations.

## Discovery-First Pattern

### Before: Loading Full Context
```bash
# Loads entire CLAUDE.md + project context + all skills
claude task "Review this codebase and suggest improvements"
```

### After: Tiered Discovery
```bash
# Step 1: Discovery (minimal context)
claude task --model=haiku "Analyze file structure and identify task type"

# Step 2: Targeted Loading (based on discovery)
claude task "Review Python security patterns" --skills=security/python

# Step 3: Specialized Agents (only if needed)
claude task --agent=code-reviewer "Deep security analysis"
```

## Multi-Agent Coordination Patterns

### Parallel Execution (Research Validated)
```bash
# Launch independent agents simultaneously
claude task --agent=code-reviewer "Security review" &
claude task --agent=pr-test-analyzer "Test coverage" &
claude task --agent=performance-analyzer "Performance check" &
wait
```

### Conditional Routing (Confidence-Based)
```bash
# Route based on initial assessment
initial_score=$(claude task --model=haiku "Rate code quality 1-10")
if [ $initial_score -lt 7 ]; then
    claude task --agent=code-reviewer "Comprehensive review"
else
    claude task --model=haiku "Quick validation"
fi
```

## Token Budget Patterns

### Estimation Before Execution
```bash
# Estimate tokens before running expensive operations
estimated_tokens=$(claude estimate-tokens "Complex refactoring task")
if [ $estimated_tokens -gt 50000 ]; then
    echo "High cost task detected. Use progressive approach?"
    read -p "Continue? (y/n): " confirm
fi
```

### Model Routing (Cost Optimization)
```bash
# Route simple tasks to Haiku, complex to Sonnet
task_complexity=$(claude classify-complexity "$task_description")
case $task_complexity in
    "simple") model="haiku" ;;
    "moderate") model="sonnet" ;;
    "complex") model="opus" ;;
esac

claude task --model=$model "$task_description"
```

## Workflow DAG Simulation

### Sequential with State Passing
```bash
# Simulate workflow state persistence
STATE_FILE="/tmp/workflow_state.json"

# Step 1: Analysis
claude task "Analyze codebase" > "$STATE_FILE"

# Step 2: Use previous state
claude task "Based on analysis in $STATE_FILE, suggest improvements"

# Step 3: Implementation
claude task "Implement changes based on $STATE_FILE"
```

### Dependency Management
```bash
# Simple dependency checking
if [ ! -f "analysis_complete.flag" ]; then
    claude task --agent=code-explorer "Analyze architecture"
    touch analysis_complete.flag
fi

if [ -f "analysis_complete.flag" ] && [ ! -f "review_complete.flag" ]; then
    claude task --agent=code-reviewer "Security review"
    touch review_complete.flag
fi
```

## Usage Guidelines

1. **Start with Haiku for discovery** - Classify task type and complexity
2. **Use parallel agents** - Launch independent analyses simultaneously
3. **Progressive detail** - Load additional context only when needed
4. **Model routing** - Match model capability to task complexity
5. **State persistence** - Pass results between agents via files

## Expected Benefits

- **30-50% token reduction** (vs loading everything upfront)
- **2-3x faster execution** (parallel + appropriate model selection)
- **Better cost control** - Estimation and routing
- **Improved workflows** - DAG-like coordination

## Integration with Research

These patterns implement core concepts from the research within current Claude Code:

- **Progressive Loading** → Discovery-first + targeted skills
- **Agent Mesh** → Parallel execution + coordination
- **Token Management** → Estimation + model routing
- **Workflow DAGs** → State passing + dependency management

While not as sophisticated as platform-level improvements, these patterns provide immediate benefits and align with research findings.