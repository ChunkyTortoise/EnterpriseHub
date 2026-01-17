# Agent Communication Protocol

**Version**: 1.0.0
**Purpose**: Standardized communication and coordination between Claude Code agents
**Category**: System Infrastructure

## Overview
This protocol defines how agents communicate, share context, coordinate workflows, and maintain consistency across the development process. It enables seamless multi-agent orchestration while preventing conflicts and ensuring knowledge flow.

## Communication Architecture

### **Message Bus System**
```
.claude/communication/
├── message_queue/
│   ├── pending_messages.jsonl
│   ├── processed_messages.jsonl
│   └── failed_messages.jsonl
├── shared_state/
│   ├── current_workflow.json
│   ├── active_agents.json
│   └── resource_locks.json
└── coordination/
    ├── agent_registry.json
    ├── workflow_definitions.json
    └── escalation_rules.json
```

### **Agent Registry**
```json
{
  "agents": {
    "architecture-sentinel": {
      "id": "arch-001",
      "status": "active",
      "capabilities": ["code_analysis", "pattern_detection", "architecture_review"],
      "tool_permissions": ["Read", "Grep", "Glob", "WebSearch"],
      "current_tasks": [],
      "priority": 8,
      "last_active": "2026-01-09T15:30:00Z"
    },
    "tdd-guardian": {
      "id": "tdd-001",
      "status": "active",
      "capabilities": ["test_enforcement", "coverage_analysis", "tdd_validation"],
      "tool_permissions": ["Read", "Write", "Edit", "Bash", "Grep"],
      "current_tasks": ["monitoring_test_coverage"],
      "priority": 9,
      "last_active": "2026-01-09T15:32:00Z"
    },
    "context-memory": {
      "id": "mem-001",
      "status": "active",
      "capabilities": ["knowledge_storage", "pattern_learning", "context_synthesis"],
      "tool_permissions": ["Read", "Write", "Grep", "WebSearch"],
      "current_tasks": ["session_context_synthesis"],
      "priority": 7,
      "last_active": "2026-01-09T15:31:00Z"
    }
  }
}
```

## Message Format Standard

### **Base Message Structure**
```json
{
  "id": "msg-{uuid}",
  "timestamp": "2026-01-09T15:30:00Z",
  "from": "architecture-sentinel",
  "to": "tdd-guardian",
  "message_type": "delegation",
  "priority": "high",
  "correlation_id": "workflow-123",
  "payload": {
    "action": "validate_test_coverage",
    "context": {
      "files_changed": ["src/services/PropertyMatcher.ts"],
      "architecture_analysis": "Strategy pattern implementation requires comprehensive testing"
    },
    "requirements": {
      "coverage_threshold": 85,
      "test_types": ["unit", "integration"],
      "edge_cases": ["null_inputs", "boundary_values"]
    }
  },
  "response_required": true,
  "timeout": "300s",
  "retry_policy": {
    "max_retries": 3,
    "backoff": "exponential"
  }
}
```

### **Message Types**

#### **1. Delegation Messages**
```json
{
  "message_type": "delegation",
  "payload": {
    "action": "review_security_implications",
    "delegating_reason": "Security expertise required for authentication changes",
    "context": "User authentication system refactoring",
    "deliverables": ["security_assessment", "vulnerability_report"],
    "deadline": "2026-01-09T18:00:00Z"
  }
}
```

#### **2. Information Sharing**
```json
{
  "message_type": "information",
  "payload": {
    "type": "architectural_decision",
    "content": {
      "decision": "Adopt Repository pattern for data access",
      "rationale": "Improved testability and separation of concerns",
      "impact": "All data access layers need refactoring"
    },
    "relevant_agents": ["tdd-guardian", "security-auditor"]
  }
}
```

#### **3. Coordination Requests**
```json
{
  "message_type": "coordination",
  "payload": {
    "type": "resource_lock",
    "resource": "src/services/LeadService.ts",
    "operation": "refactoring",
    "estimated_duration": "30m",
    "blocking_operations": ["test_execution", "security_scan"]
  }
}
```

#### **4. Status Updates**
```json
{
  "message_type": "status",
  "payload": {
    "task_id": "task-456",
    "status": "completed",
    "results": {
      "coverage_achieved": 92,
      "tests_added": 15,
      "issues_found": 0
    },
    "next_actions": ["refactor_phase_ready"]
  }
}
```

## Workflow Coordination Patterns

### **Sequential Workflow**
```json
{
  "workflow_id": "feature-implementation-001",
  "name": "New Feature Implementation",
  "type": "sequential",
  "steps": [
    {
      "step": 1,
      "agent": "architecture-sentinel",
      "action": "analyze_requirements",
      "deliverables": ["architecture_plan", "pattern_recommendations"],
      "gates": ["stakeholder_approval"]
    },
    {
      "step": 2,
      "agent": "tdd-guardian",
      "action": "create_failing_tests",
      "dependencies": ["step_1_complete"],
      "deliverables": ["test_suite", "coverage_baseline"]
    },
    {
      "step": 3,
      "agent": "claude-code",
      "action": "implement_feature",
      "dependencies": ["step_2_complete"],
      "deliverables": ["implementation", "green_tests"]
    },
    {
      "step": 4,
      "agent": "architecture-sentinel",
      "action": "review_implementation",
      "dependencies": ["step_3_complete"],
      "deliverables": ["quality_assessment", "refactor_suggestions"]
    }
  ]
}
```

### **Parallel Workflow**
```json
{
  "workflow_id": "code-review-001",
  "name": "Comprehensive Code Review",
  "type": "parallel",
  "branches": [
    {
      "branch": "architecture",
      "agent": "architecture-sentinel",
      "action": "architecture_review",
      "timeout": "15m"
    },
    {
      "branch": "security",
      "agent": "security-auditor",
      "action": "security_scan",
      "timeout": "10m"
    },
    {
      "branch": "testing",
      "agent": "tdd-guardian",
      "action": "test_validation",
      "timeout": "20m"
    }
  ],
  "consolidation": {
    "agent": "context-memory",
    "action": "aggregate_review_results",
    "wait_for": "all_branches"
  }
}
```

## Handoff Protocols

### **Architecture Sentinel → TDD Guardian**
```
Trigger: Architecture changes that require new test coverage

Message Format:
@tdd-guardian: Architecture analysis complete for [component].

Requirements:
- Test Strategy: [unit/integration/e2e]
- Coverage Target: [percentage]
- Critical Paths: [list of scenarios]
- Edge Cases: [specific conditions to test]
- Dependencies: [external services to mock]

Context: [architecture_analysis_summary]
Priority: [high/medium/low]
Deadline: [timestamp]
```

### **TDD Guardian → Architecture Sentinel**
```
Trigger: Test implementation reveals architectural issues

Message Format:
@architecture-sentinel: Test implementation exposed architectural concerns in [component].

Issues Identified:
- Tight Coupling: [specific dependencies]
- Testability Problems: [areas difficult to test]
- Design Violations: [SOLID principle violations]
- Performance Concerns: [potential bottlenecks]

Recommendations Needed:
- Refactoring Strategy: [priority]
- Pattern Applications: [suggested patterns]
- Dependency Injection: [areas needing DI]

Context: [test_analysis_summary]
```

### **Context Memory ↔ All Agents**
```
Context Memory → Agent:
"Historical context for current task:
- Previous Decisions: [relevant ADRs]
- Learned Patterns: [applicable patterns]
- Known Issues: [potential pitfalls]
- Success Strategies: [proven approaches]"

Agent → Context Memory:
"Store decision/pattern/learning:
- Type: [decision/pattern/preference]
- Context: [situation description]
- Solution: [what was implemented]
- Outcome: [results achieved]
- Lessons: [key learnings]"
```

## Conflict Resolution

### **Resource Conflicts**
```json
{
  "conflict_resolution": {
    "type": "resource_lock",
    "conflict_id": "conflict-789",
    "resource": "src/services/LeadService.ts",
    "competing_agents": [
      {
        "agent": "architecture-sentinel",
        "operation": "refactoring",
        "priority": 8,
        "estimated_duration": "45m"
      },
      {
        "agent": "tdd-guardian",
        "operation": "test_addition",
        "priority": 9,
        "estimated_duration": "30m"
      }
    ],
    "resolution_strategy": "priority_based",
    "winner": "tdd-guardian",
    "queue_position": 1,
    "rationale": "Higher priority and shorter duration"
  }
}
```

### **Decision Conflicts**
```json
{
  "decision_conflict": {
    "conflict_id": "decision-456",
    "issue": "Testing strategy disagreement",
    "positions": [
      {
        "agent": "tdd-guardian",
        "recommendation": "Unit tests for all service methods",
        "rationale": "Better isolation and faster feedback"
      },
      {
        "agent": "architecture-sentinel",
        "recommendation": "Integration tests for service layer",
        "rationale": "Better coverage of business logic flows"
      }
    ],
    "escalation": "context-memory",
    "resolution": "hybrid_approach",
    "outcome": "Unit tests for pure logic, integration tests for workflows"
  }
}
```

## Quality Gates and Checkpoints

### **Multi-Agent Quality Pipeline**
```yaml
quality_pipeline:
  stage_1_analysis:
    agents: [architecture-sentinel]
    gates:
      - solid_compliance: pass
      - complexity_threshold: pass
      - pattern_appropriateness: pass
    timeout: 10m

  stage_2_testing:
    agents: [tdd-guardian]
    dependencies: [stage_1_analysis]
    gates:
      - test_coverage: ">= 80%"
      - test_quality: "meaningful"
      - red_green_refactor: "followed"
    timeout: 20m

  stage_3_security:
    agents: [security-auditor]
    parallel_with: [stage_2_testing]
    gates:
      - vulnerability_scan: "clean"
      - input_validation: "present"
      - authorization: "verified"
    timeout: 15m

  stage_4_integration:
    agents: [context-memory]
    dependencies: [stage_2_testing, stage_3_security]
    actions:
      - store_decisions
      - learn_patterns
      - update_context
    timeout: 5m
```

## Error Handling and Recovery

### **Agent Failure Protocol**
```json
{
  "error_handling": {
    "agent_timeout": {
      "detection": "agent_heartbeat_missing > 5m",
      "action": "escalate_to_human",
      "fallback": "simplified_analysis"
    },
    "tool_failure": {
      "detection": "tool_error_count > 3",
      "action": "switch_to_readonly_mode",
      "retry": "exponential_backoff"
    },
    "workflow_deadlock": {
      "detection": "circular_dependency",
      "action": "break_dependency_chain",
      "escalation": "human_intervention"
    }
  }
}
```

### **Recovery Strategies**
```yaml
recovery_strategies:
  partial_failure:
    - continue_with_available_agents
    - reduce_scope_if_needed
    - document_limitations

  complete_failure:
    - rollback_to_last_checkpoint
    - notify_human_operator
    - preserve_partial_results

  data_corruption:
    - restore_from_backup
    - validate_data_integrity
    - replay_failed_operations
```

## Monitoring and Observability

### **Agent Performance Metrics**
```json
{
  "metrics": {
    "agent_performance": {
      "architecture-sentinel": {
        "avg_analysis_time": "8.5m",
        "accuracy_score": 0.92,
        "recommendations_accepted": 0.87
      },
      "tdd-guardian": {
        "coverage_improvement": "+15%",
        "test_quality_score": 0.89,
        "tdd_compliance_rate": 0.95
      }
    },
    "workflow_efficiency": {
      "avg_completion_time": "25m",
      "success_rate": 0.94,
      "human_interventions": 0.06
    }
  }
}
```

### **Communication Health**
```yaml
communication_health:
  message_latency:
    p50: 150ms
    p95: 800ms
    p99: 2s

  message_success_rate: 99.2%

  queue_depth:
    current: 3
    avg: 1.2
    max_observed: 15

  agent_availability:
    architecture-sentinel: 98.5%
    tdd-guardian: 99.1%
    context-memory: 99.8%
```

## Integration Examples

### **Real Estate AI Workflow Integration**
```json
{
  "workflow": "lead_scoring_enhancement",
  "steps": [
    {
      "agent": "architecture-sentinel",
      "action": "Analyze current lead scoring architecture",
      "output": "Recommend Strategy pattern for scoring algorithms"
    },
    {
      "agent": "tdd-guardian",
      "action": "Create failing tests for new scoring strategies",
      "input": "Strategy pattern requirements from architecture analysis"
    },
    {
      "agent": "claude-code",
      "action": "Implement scoring strategy pattern",
      "input": "Test requirements and architecture plan"
    },
    {
      "agent": "context-memory",
      "action": "Store pattern success for future lead processing features",
      "input": "Implementation results and metrics"
    }
  ]
}
```

---

*"The strength of the team is each individual member. The strength of each member is the team."*

**Last Updated**: 2026-01-09
**Version**: 1.0.0
**Dependencies**: All Claude Code agents