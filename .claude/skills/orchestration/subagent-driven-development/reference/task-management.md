# Task Management and Workflow State

Complete task and workflow state management for multi-agent orchestration.

## Task Data Structure

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum


class Priority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str
    title: str
    description: str
    agent_type: AgentType
    priority: Priority
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
    deadline: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'agent_type': self.agent_type.value,
            'priority': self.priority.value,
            'input_data': self.input_data,
            'dependencies': self.dependencies,
            'estimated_duration': self.estimated_duration.total_seconds() if self.estimated_duration else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'status': self.status,
            'assigned_agent': self.assigned_agent,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error,
            'metadata': self.metadata
        }
```

## Workflow State Management

```python
@dataclass
class WorkflowState:
    """Represents the current state of a multi-agent workflow."""
    workflow_id: str
    name: str
    description: str
    tasks: List[Task]
    active_agents: Dict[str, AgentStatus]
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    workflow_status: str = "initialized"
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready = []
        for task in self.tasks:
            if (task.status == "pending" and
                all(dep in self.completed_tasks for dep in task.dependencies)):
                ready.append(task)
        return ready

    def get_critical_path(self) -> List[str]:
        """Calculate the critical path for workflow completion."""
        task_graph = {}
        for task in self.tasks:
            task_graph[task.id] = {
                'duration': task.estimated_duration.total_seconds() if task.estimated_duration else 3600,
                'dependencies': task.dependencies
            }

        # Return tasks in dependency order (simplified critical path)
        return [task.id for task in sorted(self.tasks, key=lambda t: len(t.dependencies))]
```

## Task Creation Patterns

### Simple Task

```python
task = Task(
    id="task_001",
    title="Implement API Endpoint",
    description="Implement REST API endpoint for user authentication",
    agent_type=AgentType.DEVELOPER,
    priority=Priority.HIGH,
    input_data={
        'endpoint': '/api/v1/auth',
        'method': 'POST',
        'framework': 'FastAPI'
    },
    metadata={'complexity': 2.5}
)
```

### Task with Dependencies

```python
design_task = Task(
    id="arch_001",
    title="Design System Architecture",
    description="Design scalable architecture for the feature",
    agent_type=AgentType.ARCHITECT,
    priority=Priority.HIGH,
    input_data={'requirements': {...}},
    metadata={'task_type': 'system_design'}
)

implementation_task = Task(
    id="dev_001",
    title="Implement Feature",
    description="Implement the designed feature",
    agent_type=AgentType.DEVELOPER,
    priority=Priority.HIGH,
    input_data={'specification': {...}},
    dependencies=["arch_001"],  # Depends on design task
    metadata={'task_type': 'implementation'}
)
```

### High-Priority Task with Deadline

```python
critical_task = Task(
    id="security_001",
    title="Security Vulnerability Fix",
    description="Fix critical security vulnerability in authentication",
    agent_type=AgentType.SECURITY,
    priority=Priority.CRITICAL,
    input_data={'vulnerability': 'CVE-2024-XXXX'},
    deadline=datetime.now() + timedelta(hours=4),
    max_retries=1,  # No retries for security fixes
    metadata={'severity': 'critical'}
)
```

## Dependency Management

### Creating Task Graphs

```python
def create_feature_task_graph():
    """Create a task graph for feature development."""
    tasks = [
        # Phase 1: Design
        Task(
            id="arch_001",
            title="Design Feature Architecture",
            agent_type=AgentType.ARCHITECT,
            priority=Priority.HIGH,
            input_data={...}
        ),

        # Phase 2: Implementation (depends on design)
        Task(
            id="dev_001",
            title="Implement Core Logic",
            agent_type=AgentType.DEVELOPER,
            priority=Priority.HIGH,
            dependencies=["arch_001"],
            input_data={...}
        ),

        Task(
            id="dev_002",
            title="Implement API Endpoints",
            agent_type=AgentType.DEVELOPER,
            priority=Priority.HIGH,
            dependencies=["arch_001"],
            input_data={...}
        ),

        # Phase 3: Testing (depends on implementation)
        Task(
            id="test_001",
            title="Create Test Suite",
            agent_type=AgentType.TESTER,
            priority=Priority.MEDIUM,
            dependencies=["dev_001", "dev_002"],
            input_data={...}
        ),

        # Phase 4: Quality Gate (depends on testing)
        Task(
            id="qa_001",
            title="Quality Gate Validation",
            agent_type=AgentType.QUALITY_GATE,
            priority=Priority.HIGH,
            dependencies=["test_001"],
            input_data={...}
        )
    ]

    return tasks
```

## Status Tracking

### Task Status Progression

```
pending → assigned → in_progress → completed/failed/retrying
```

### Monitoring Task Progress

```python
def monitor_workflow_progress(workflow: WorkflowState):
    """Monitor and report workflow progress."""
    total_tasks = len(workflow.tasks)
    completed = len(workflow.completed_tasks)
    failed = len(workflow.failed_tasks)
    in_progress = sum(1 for task in workflow.tasks if task.status == "in_progress")
    pending = sum(1 for task in workflow.tasks if task.status == "pending")

    return {
        'total': total_tasks,
        'completed': completed,
        'failed': failed,
        'in_progress': in_progress,
        'pending': pending,
        'completion_percentage': (completed / total_tasks) * 100 if total_tasks > 0 else 0
    }
```

## Best Practices

1. **Task Granularity**: Keep tasks focused and achievable (2-8 hours each)
2. **Dependency Clarity**: Explicitly define all dependencies
3. **Priority Assignment**: Use priority levels appropriately
4. **Deadline Management**: Set realistic deadlines with buffer
5. **Error Handling**: Define retry strategies per task type
6. **Metadata Usage**: Store task-specific context in metadata
7. **Status Updates**: Update task status at every state change

## See Also

- `agent-taxonomy.md` - Agent types and capabilities
- `orchestration-patterns.md` - Coordination patterns
- `../examples/workflow-creation.py` - Complete workflow examples
