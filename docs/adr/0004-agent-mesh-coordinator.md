# ADR 0004: Agent Mesh Coordinator

## Status

Accepted

## Context

The platform relies on 22 specialized agents for tasks ranging from security auditing to performance optimization and compliance monitoring. Initially, agent dispatch was handled by direct imports and manual routing — the calling code needed to know which agent to invoke for each task type.

This created several scaling problems:
- Adding a new agent required updating routing logic in every service that might use it
- No visibility into which agents were active, their resource consumption, or failure rates
- No governance over agent interactions (e.g., a security audit agent should not be dispatched during a performance-critical window without approval)
- Agent capabilities overlapped, making it unclear which agent should handle ambiguous requests

## Decision

Implement a centralized `AgentMeshCoordinator` that provides:

**Capability-Based Routing**: Each agent registers its capabilities as a structured manifest (task types, resource requirements, estimated duration). When a service requests an agent for a task, the mesh coordinator matches the task against registered capabilities and selects the best-fit agent.

**Governance Layer**: Configurable policies control agent dispatch:
- Priority classes (critical, standard, background) determine scheduling order
- Resource quotas prevent any single agent type from monopolizing compute
- Approval workflows for sensitive operations (e.g., database migrations require human confirmation)

**Auto-Scaling Triggers**: The coordinator monitors queue depth per agent type and triggers scaling events when backlogs exceed configurable thresholds. This integrates with the existing Docker Compose infrastructure for local development and Kubernetes HPA for production.

**Audit Trails**: Every agent dispatch, completion, and failure is logged with full context (requesting service, task parameters, duration, outcome). This feeds into the BI dashboard for operational visibility.

**Health Monitoring**: Periodic heartbeat checks detect unresponsive agents. Failed agents are removed from the routing table and their queued tasks are redistributed to capable peers.

## Consequences

### Positive
- Any agent can be added or removed by updating its capability manifest, with zero changes to routing logic
- Full audit trail enables cost attribution, performance analysis, and compliance reporting
- Governance policies prevent resource contention and enforce operational controls
- Health monitoring ensures failed agents don't create silent black holes for tasks
- Capability matching eliminates ambiguity in agent selection for overlapping task types

### Negative
- Mesh coordinator overhead adds ~50ms per agent dispatch (acceptable for async tasks, noticeable for synchronous chains)
- Single point of coordination: mesh coordinator failure requires fallback to direct dispatch mode
- Capability manifests must be maintained alongside agent code; stale manifests cause misrouting
- Auto-scaling configuration requires tuning per deployment environment (local Docker vs. production K8s)
- Governance policies add complexity for simple, low-risk agent tasks that previously required no approval
