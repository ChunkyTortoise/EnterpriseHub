# Agent Taxonomy and Role Definitions

Complete taxonomy of specialized agents in the multi-agent development ecosystem.

## Agent Types

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import timedelta


class AgentType(Enum):
    """Types of specialized agents in the development ecosystem."""
    ARCHITECT = "architect"           # System design and architecture
    DEVELOPER = "developer"           # Code implementation
    TESTER = "tester"                # Testing and quality assurance
    REVIEWER = "reviewer"             # Code review and analysis
    SECURITY = "security"             # Security analysis and hardening
    PERFORMANCE = "performance"       # Performance optimization
    DOCUMENTATION = "documentation"   # Documentation creation
    DEVOPS = "devops"                # Deployment and infrastructure
    UI_UX = "ui_ux"                  # User interface and experience
    DATA = "data"                    # Data analysis and processing
    COORDINATOR = "coordinator"       # Workflow coordination
    QUALITY_GATE = "quality_gate"    # Quality gatekeeper


class AgentStatus(Enum):
    """Status states for agents during execution."""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    BLOCKED = "blocked"


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5
```

## Agent Capabilities

```python
@dataclass
class AgentCapability:
    """Defines a specific capability an agent possesses."""
    name: str
    description: str
    expertise_level: int  # 1-10 scale
    prerequisites: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
```

## Agent Role Specifications

### Architect Agent
- **Primary Focus**: System design, architecture patterns, scalability planning
- **Capabilities**: Architecture design, technology selection, pattern recommendation
- **Expertise Level**: 8-10
- **Outputs**: Architecture diagrams, technology recommendations, design documents

### Developer Agent
- **Primary Focus**: Code implementation, feature development, bug fixes
- **Capabilities**: Code generation, refactoring, debugging, API development
- **Expertise Level**: 7-9
- **Outputs**: Source code, unit tests, implementation documentation

### Tester Agent
- **Primary Focus**: Quality assurance, test coverage, validation
- **Capabilities**: Test generation, execution, coverage analysis, regression testing
- **Expertise Level**: 7-9
- **Outputs**: Test suites, coverage reports, quality metrics

### Reviewer Agent
- **Primary Focus**: Code review, quality validation, best practices enforcement
- **Capabilities**: Static analysis, code review, refactoring suggestions
- **Expertise Level**: 8-10
- **Outputs**: Review comments, improvement suggestions, approval/rejection

### Security Agent
- **Primary Focus**: Security analysis, vulnerability detection, hardening
- **Capabilities**: Security scanning, threat modeling, compliance validation
- **Expertise Level**: 9-10
- **Outputs**: Security reports, vulnerability assessments, remediation plans

### Performance Agent
- **Primary Focus**: Performance optimization, profiling, bottleneck identification
- **Capabilities**: Performance analysis, optimization recommendations, benchmarking
- **Expertise Level**: 8-9
- **Outputs**: Performance reports, optimization plans, benchmarks

### Coordinator Agent
- **Primary Focus**: Workflow orchestration, task scheduling, dependency management
- **Capabilities**: Task routing, dependency resolution, progress monitoring
- **Expertise Level**: 9-10
- **Outputs**: Workflow status, task assignments, completion reports

### Quality Gate Agent
- **Primary Focus**: Quality validation, standards enforcement, approval gates
- **Capabilities**: Quality validation, standards checking, approval decisions
- **Expertise Level**: 9-10
- **Outputs**: Quality reports, approval/rejection decisions, improvement recommendations

## Usage Patterns

### Selecting Agent Type for Task

```python
def select_agent_for_task(task_type: str, complexity: float) -> AgentType:
    """
    Select appropriate agent type based on task characteristics.

    Args:
        task_type: Type of work (design, implementation, testing, etc.)
        complexity: Task complexity (1.0-10.0 scale)

    Returns:
        Appropriate AgentType for the task
    """
    if task_type == "system_design":
        return AgentType.ARCHITECT if complexity > 5.0 else AgentType.DEVELOPER
    elif task_type in ["api_implementation", "feature_development"]:
        return AgentType.DEVELOPER
    elif task_type in ["testing", "quality_assurance"]:
        return AgentType.TESTER
    elif task_type == "security_analysis":
        return AgentType.SECURITY
    elif task_type == "performance_optimization":
        return AgentType.PERFORMANCE
    elif task_type == "code_review":
        return AgentType.REVIEWER
    elif task_type == "workflow_coordination":
        return AgentType.COORDINATOR
    else:
        return AgentType.DEVELOPER  # Default
```

## Best Practices

1. **Assign tasks to agents matching their expertise level**
2. **Use Coordinator agents for complex multi-agent workflows**
3. **Always include Quality Gate agents for critical paths**
4. **Security agents mandatory for production deployments**
5. **Performance agents for high-traffic features**

## See Also

- `orchestration-patterns.md` - Coordination patterns
- `task-management.md` - Task creation and dependency management
