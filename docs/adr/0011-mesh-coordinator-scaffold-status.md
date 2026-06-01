# ADR 0011: AgentMeshCoordinator Scaffold Status

## Status

Accepted

## Context

ADR 0004 introduced `AgentMeshCoordinator` as a centralized governance and routing layer. Its decision section describes "Auto-Scaling Triggers" that "monitor queue depth per agent type and trigger scaling events," implying production-grade runtime behavior. ADR 0004 does include an Implementation Status section that flags several stubs, but that section is easy to overlook, and the surrounding prose still reads as a description of a working system.

Since ADR 0004 was written, two concerns have emerged:

1. External readers of the codebase (clients, reviewers, future contributors) have taken the auto-scaling and backpressure language at face value.
2. Internal documentation elsewhere (notably the `.claude/CLAUDE.md` service table, which lists "auto-scaling" as a key behavior of the mesh) reinforces that over-claim.

This ADR pins the honest implementation state as of 2026-06-01 so that all future documentation and code reviews start from a shared, accurate baseline.

## Decision

`AgentMeshCoordinator` (`ghl_real_estate_ai/services/agent_mesh_coordinator.py`) is a governance and routing scaffold. The following statements are grounded in the code at the commit this ADR is filed against.

### What is implemented and exercised

**Capability-based routing.** `_find_candidate_agents` (lines 255-280) filters registered agents by capability flags, cost ceiling, and SLA deadline. `_calculate_agent_score` (lines 299-328) applies a weighted scoring formula: performance 40%, availability 25%, cost efficiency 20%, response time 15%. This runs on every `submit_task` call.

**In-memory task lifecycle tracking.** `active_tasks` and `completed_tasks` dicts track assignment, start time, completion, and error. `_update_agent_metrics` (lines 645-661) maintains a running average response time and success/failure counts per agent.

**Budget guard on submission.** `_check_budget_constraints` (lines 624-628) sums estimated task cost against `max_total_cost_per_hour` ($50.00 default) before admitting a task. `_cost_monitor` (lines 514-530) polls every 5 minutes and calls `emergency_shutdown` if `emergency_shutdown_threshold` ($100.00) is crossed.

**Emergency shutdown.** `emergency_shutdown` (lines 475-491) cancels in-flight tasks and sets all agents to `AgentStatus.MAINTENANCE`. This is the only runtime intervention that actually mutates system state.

**Audit logging.** Every dispatch, completion, and failure emits a structured log entry via `get_logger(__name__)`.

### What is scaffolded but not implemented

The following methods exist in the file but contain only a `logger.info(...)` call or a fixed return value. They perform no actual work at runtime.

| Method | Lines | Actual behavior |
|--------|-------|-----------------|
| `_auto_scale_mesh` | 566-568 | Logs "Mesh auto-scaling triggered (stub)" |
| `_rebalance_agents` | 571-573 | Logs "Agent rebalancing triggered (stub)" |
| `_reduce_mesh_activity` | 575-577 | Logs "Budget-driven activity reduction triggered (stub)" |
| `_send_emergency_alert` | 579-580 | Logs the alert message; no external notification is sent |
| `_health_check_agent` | 630-638 | Sets `last_heartbeat = datetime.now()` and returns `True` unconditionally; no HTTP probe is made |
| `_execute_generic_task` | 423-426 | Returns `{"status": "completed", "message": "Generic task execution"}` without executing anything |

`_performance_monitor` (lines 532-551) calls `_auto_scale_mesh` and `_rebalance_agents` based on `average_queue_time` and `load_imbalance` thresholds. Because those methods are no-ops, the monitor loop produces log lines but causes no runtime effect.

There is no integration with Kubernetes HPA, Docker Compose scaling APIs, or any external orchestration system. No approval-gate or human-confirmation workflow exists in code.

### Consequences of the scaffold status

The coordinator provides a correct routing foundation: tasks submitted to the mesh are routed to registered agents that match capability, cost, and deadline constraints. The governance data structures (quotas, cost limits, SLA fields) are in place and will survive forward without rewriting.

What the coordinator does not provide: any automatic response to sustained queue buildup, uneven load distribution, or budget pressure short of hard shutdown. Under load, the only runtime backstop is the $100 emergency shutdown threshold.

## Consequences

### Positive

- The routing and scoring logic (the highest-value part of the design) is built, tested, and correct. Future work to fill in auto-scaling has a clean integration point: replace the stub method bodies.
- In-memory audit trails and metrics are accurate for single-instance deployments; they feed the BI dashboard without additional instrumentation.
- The governance data model (quotas, SLA deadlines, priority classes) is defined in a way that real backpressure and scaling logic can consume without schema changes.
- Documenting scaffold status explicitly prevents future contributors from building on an assumed capability that does not exist.

### Negative

- Under sustained load, the mesh has no automatic relief valve between normal operation and hard shutdown. Queue buildup goes unhandled until the $100 cost threshold is crossed.
- `_health_check_agent` always returns `True`, so agents that have silently failed are not removed from the routing table. Routing continues to assign tasks to dead agents until those tasks time out or error.
- `_execute_generic_task` always reports success. Any agent using the generic execution path will appear healthy in metrics regardless of actual outcome.
- Code reviewers who read only the method names in `_performance_monitor` will conclude that auto-scaling is active. The stub bodies must be read to see the no-op behavior.
