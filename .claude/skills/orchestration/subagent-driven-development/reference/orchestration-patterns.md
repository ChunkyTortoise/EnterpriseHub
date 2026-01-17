# Orchestration Patterns for Multi-Agent Workflows

Advanced patterns for coordinating multiple specialized agents in complex development workflows.

## Core Orchestration Patterns

### 1. Sequential Pipeline

Agents execute in strict sequence, each depending on the previous agent's output.

```
Architect → Developer → Tester → Reviewer → Quality Gate
```

**Use Case**: Linear workflows with clear dependencies (feature development, bug fixes)

**Implementation**:
```python
tasks = [
    Task(id="1", agent_type=AgentType.ARCHITECT, ...),
    Task(id="2", agent_type=AgentType.DEVELOPER, dependencies=["1"], ...),
    Task(id="3", agent_type=AgentType.TESTER, dependencies=["2"], ...),
    Task(id="4", agent_type=AgentType.REVIEWER, dependencies=["3"], ...),
    Task(id="5", agent_type=AgentType.QUALITY_GATE, dependencies=["4"], ...)
]
```

### 2. Parallel Fan-Out

Multiple agents work independently on different aspects simultaneously.

```
                 ┌─> Developer A (Frontend)
Architect ──────┼─> Developer B (Backend)
                 └─> Developer C (Database)
                           ↓
                      [Merge Point]
```

**Use Case**: Independent components that can be developed in parallel

**Implementation**:
```python
tasks = [
    Task(id="arch_001", agent_type=AgentType.ARCHITECT, ...),
    Task(id="dev_frontend", agent_type=AgentType.DEVELOPER, dependencies=["arch_001"], ...),
    Task(id="dev_backend", agent_type=AgentType.DEVELOPER, dependencies=["arch_001"], ...),
    Task(id="dev_database", agent_type=AgentType.DEVELOPER, dependencies=["arch_001"], ...),
    Task(id="integration", agent_type=AgentType.DEVELOPER,
         dependencies=["dev_frontend", "dev_backend", "dev_database"], ...)
]
```

### 3. Quality Gate Pattern

Critical validation checkpoints at key workflow stages.

```
Developer → Tester → Quality Gate → [Approved/Rejected]
                          ↓ (if rejected)
                     [Back to Developer]
```

**Use Case**: Production deployments, critical features, security-sensitive code

**Implementation**:
```python
async def quality_gate_workflow():
    while True:
        dev_result = await developer.execute_task(dev_task)
        test_result = await tester.execute_task(test_task)

        gate_result = await quality_gate.execute_task(gate_task)

        if gate_result['approved']:
            break  # Proceed to next phase
        else:
            # Return to developer with feedback
            dev_task.input_data['feedback'] = gate_result['issues']
            dev_task.retry_count += 1
```

### 4. Multi-Stage Review

Multiple specialized reviewers provide different perspectives.

```
Developer → [Security Reviewer, Performance Reviewer, Code Reviewer] → Approval
```

**Use Case**: High-stakes features, production deployments, architectural changes

**Implementation**:
```python
tasks = [
    Task(id="dev_001", agent_type=AgentType.DEVELOPER, ...),
    Task(id="security_review", agent_type=AgentType.SECURITY, dependencies=["dev_001"], ...),
    Task(id="perf_review", agent_type=AgentType.PERFORMANCE, dependencies=["dev_001"], ...),
    Task(id="code_review", agent_type=AgentType.REVIEWER, dependencies=["dev_001"], ...),
    Task(id="final_approval", agent_type=AgentType.QUALITY_GATE,
         dependencies=["security_review", "perf_review", "code_review"], ...)
]
```

### 5. Iterative Refinement

Agent outputs are progressively refined through feedback loops.

```
Developer → Reviewer → [Feedback] → Developer → Reviewer → [Approved]
```

**Use Case**: Complex features, optimization tasks, design iterations

**Implementation**:
```python
async def iterative_refinement(initial_task, max_iterations=3):
    current_result = None

    for iteration in range(max_iterations):
        dev_task = create_dev_task(initial_task, feedback=current_result)
        dev_result = await developer.execute_task(dev_task)

        review_result = await reviewer.execute_task(
            create_review_task(dev_result)
        )

        if review_result['approved']:
            return dev_result

        current_result = review_result['feedback']

    raise Exception("Max iterations reached without approval")
```

### 6. Emergency Fast-Track

Expedited workflow for critical issues with parallel execution and minimal gates.

```
[Critical Issue] → [Security + Developer in Parallel] → Minimal Testing → Deploy
```

**Use Case**: Security vulnerabilities, production outages, critical bugs

**Implementation**:
```python
emergency_tasks = [
    Task(
        id="emergency_analysis",
        agent_type=AgentType.SECURITY,
        priority=Priority.EMERGENCY,
        max_retries=0,  # No retries in emergency
        ...
    ),
    Task(
        id="emergency_fix",
        agent_type=AgentType.DEVELOPER,
        priority=Priority.EMERGENCY,
        dependencies=["emergency_analysis"],
        ...
    ),
    Task(
        id="smoke_test",
        agent_type=AgentType.TESTER,
        priority=Priority.EMERGENCY,
        dependencies=["emergency_fix"],
        input_data={'test_type': 'smoke_only'},
        ...
    )
]
```

## Coordination Strategies

### Dynamic Task Routing

```python
class DynamicRouter:
    """Routes tasks to available agents based on workload and expertise."""

    async def route_task(self, task: Task, available_agents: List[BaseAgent]):
        # Find agents capable of handling the task
        capable_agents = [
            agent for agent in available_agents
            if await agent.can_handle_task(task)
        ]

        if not capable_agents:
            raise NoCapableAgentError(f"No agent can handle task {task.id}")

        # Select agent with lowest current workload
        selected_agent = min(
            capable_agents,
            key=lambda agent: agent.current_workload_score()
        )

        return selected_agent
```

### Dependency Resolution

```python
class DependencyResolver:
    """Resolves task dependencies and determines execution order."""

    def get_execution_order(self, tasks: List[Task]) -> List[List[Task]]:
        """Return tasks grouped by execution wave (parallel-executable tasks)."""
        execution_waves = []
        completed = set()
        remaining = tasks.copy()

        while remaining:
            # Find tasks with satisfied dependencies
            ready = [
                task for task in remaining
                if all(dep in completed for dep in task.dependencies)
            ]

            if not ready:
                raise CircularDependencyError("Circular dependency detected")

            execution_waves.append(ready)

            for task in ready:
                completed.add(task.id)
                remaining.remove(task)

        return execution_waves
```

### Load Balancing

```python
class LoadBalancer:
    """Balances work across multiple agent instances."""

    def __init__(self):
        self.agent_workloads = {}

    async def assign_task(self, task: Task, agent_pool: List[BaseAgent]):
        # Calculate current workload for each agent
        workloads = {
            agent.agent_id: await self.calculate_workload(agent)
            for agent in agent_pool
        }

        # Assign to agent with lowest workload
        selected_agent = min(workloads.items(), key=lambda x: x[1])[0]

        return next(agent for agent in agent_pool if agent.agent_id == selected_agent)

    async def calculate_workload(self, agent: BaseAgent) -> float:
        """Calculate agent's current workload score."""
        if agent.status == AgentStatus.IDLE:
            return 0.0
        elif agent.status in [AgentStatus.WORKING, AgentStatus.THINKING]:
            return 1.0
        else:
            return 0.5  # WAITING or other states
```

## Error Handling Patterns

### Retry with Exponential Backoff

```python
async def execute_with_retry(agent, task, max_retries=3):
    """Execute task with exponential backoff retry strategy."""
    for attempt in range(max_retries):
        try:
            result = await agent.execute_task(task)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff: 1s, 2s, 4s, 8s, etc.
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)

            task.retry_count += 1
```

### Fallback Agent Strategy

```python
async def execute_with_fallback(task, primary_agent, fallback_agents):
    """Try primary agent, fall back to alternatives if needed."""
    try:
        return await primary_agent.execute_task(task)
    except Exception as e:
        logger.warning(f"Primary agent failed: {e}, trying fallbacks")

        for fallback in fallback_agents:
            try:
                if await fallback.can_handle_task(task):
                    return await fallback.execute_task(task)
            except Exception as fallback_error:
                logger.warning(f"Fallback agent failed: {fallback_error}")
                continue

        raise AllAgentsFailedError("All agents failed to execute task")
```

### Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Prevent cascading failures by breaking the circuit after threshold."""

    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    async def execute(self, agent, task):
        if self.state == "OPEN":
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit breaker is OPEN")

        try:
            result = await agent.execute_task(task)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
```

## Monitoring and Observability

### Workflow Progress Tracking

```python
class WorkflowMonitor:
    """Monitor workflow execution and provide real-time status."""

    def get_workflow_metrics(self, workflow: WorkflowState) -> Dict[str, Any]:
        total_tasks = len(workflow.tasks)
        completed_tasks = len(workflow.completed_tasks)
        failed_tasks = len(workflow.failed_tasks)
        in_progress = sum(1 for task in workflow.tasks if task.status == "in_progress")

        return {
            'workflow_id': workflow.workflow_id,
            'status': workflow.workflow_status,
            'progress': {
                'total': total_tasks,
                'completed': completed_tasks,
                'failed': failed_tasks,
                'in_progress': in_progress,
                'percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            },
            'active_agents': len(workflow.active_agents),
            'estimated_completion': self.estimate_completion_time(workflow)
        }
```

## Best Practices

1. **Pattern Selection**: Choose pattern based on task dependencies and parallelization opportunities
2. **Quality Gates**: Always include quality gates for production-bound code
3. **Error Handling**: Implement robust retry and fallback strategies
4. **Load Distribution**: Balance work across available agent instances
5. **Monitoring**: Track workflow progress and agent health
6. **Dependency Management**: Clearly define and validate task dependencies
7. **Emergency Protocols**: Have fast-track patterns for critical issues

## See Also

- `agent-taxonomy.md` - Agent types and specializations
- `task-management.md` - Task creation and dependency management
- `../examples/real-estate-workflow.py` - Complete workflow example
