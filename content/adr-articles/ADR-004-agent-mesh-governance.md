# Building a Self-Governing AI Agent Mesh: Lessons from 4.3M Dispatches/sec

**Architecture Decision Record | LinkedIn Article Draft**

---

When your agents are dispatching 4.3 million messages per second, governance is not optional. It is the difference between a coordinated system and a chaotic one. Here is how we built an AI agent mesh that governs itself -- routing, scaling, auditing, and rate-limiting without human intervention.

## Why Agent Mesh

Our real estate AI platform started simple: one chatbot, one API, one database. Then it grew. Three specialized bots (Lead, Buyer, Seller). A Claude orchestrator coordinating AI calls. A BI dashboard pulling analytics. A CRM integration pushing data to GoHighLevel. A memory service tracking conversation context. A market intelligence module injecting local pricing data.

Each service needed to talk to multiple others. The Lead Bot needed the intent decoder, the handoff service, the CRM client, and the response pipeline. The orchestrator needed the memory service, the market injector, and the scoring engine. Without structure, we were heading toward a fully connected graph where every service called every other service directly.

That is an anti-pattern. **N services with direct connections means N*(N-1)/2 potential call paths.** At 12 services, that is 66 potential connections to monitor, debug, and secure. We needed a mesh.

## The Architecture

The Agent Mesh Coordinator sits at the center of all inter-service communication. Every agent registers with the mesh, declares its capabilities, and communicates through the mesh's dispatch system.

```
                    ┌──────────────────────┐
                    │   Agent Mesh         │
                    │   Coordinator        │
                    │                      │
                    │  - Routing           │
                    │  - Governance        │
                    │  - Auto-scaling      │
                    │  - Audit trails      │
                    └──────────┬───────────┘
           ┌───────────┬──────┴──────┬───────────┐
           ▼           ▼             ▼           ▼
    ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
    │ Lead    │  │ Buyer    │  │ Seller  │  │ Claude   │
    │ Bot     │  │ Bot      │  │ Bot     │  │ Orch.    │
    └─────────┘  └──────────┘  └─────────┘  └──────────┘
```

Agents never call each other directly. Every interaction is a message dispatched through the mesh. The mesh decides where it goes, tracks that it arrived, and records what happened.

## The Governance Model

Governance means rules that agents must follow and the mesh enforces. We implemented four governance layers:

### Layer 1: Capability Registration

Every agent declares what it can do and what it needs:

```python
mesh.register_agent(
    agent_id="jorge_lead_bot",
    capabilities=["lead_qualification", "temperature_scoring", "intent_routing"],
    dependencies=["intent_decoder", "handoff_service", "ghl_client"],
    max_concurrent=50,
    sla_p95_ms=500,
)
```

If an agent tries to invoke a capability it did not register as a dependency, the mesh rejects the dispatch. This prevents scope creep -- the Lead Bot cannot suddenly start calling the billing service because someone added a convenience function.

### Layer 2: Rate Limiting and Quotas

Each agent has dispatch quotas based on its role and the resources it consumes:

- **Bot agents**: 100 dispatches/second (covers all message processing)
- **Orchestrator**: 200 dispatches/second (coordinates across multiple services)
- **Analytics**: 50 dispatches/second (batch-oriented, lower priority)
- **CRM sync**: 10 dispatches/second (GHL API rate limit: 10 req/s)

When an agent exceeds its quota, dispatches are queued, not dropped. The mesh applies backpressure, and the agent receives a signal to slow down. This prevents cascade failures where one overloaded agent overwhelms its dependencies.

### Layer 3: Priority-Based Routing

Not all dispatches are equal. A live SMS conversation has higher priority than a batch analytics job. The mesh enforces a priority system:

| Priority | Use Case | Max Latency |
|----------|----------|-------------|
| P0 (Critical) | Active lead conversation | 200ms |
| P1 (High) | Handoff decision | 500ms |
| P2 (Normal) | CRM sync, tag updates | 2,000ms |
| P3 (Low) | Analytics, reporting | 10,000ms |

When the system is under load, P3 dispatches are deferred to protect P0 response times. A lead asking "What's my home worth?" always gets answered before a dashboard refreshes its charts.

### Layer 4: Circuit Breaking

If an agent's error rate exceeds 10% or its P95 latency exceeds 120% of its SLA, the mesh trips a circuit breaker:

```python
# Automatic circuit breaking
if agent_metrics.error_rate > 0.10:
    mesh.trip_circuit(agent_id, reason="error_rate_exceeded")
    # Dispatches to this agent return fallback responses
    # Alerting service notified
    # Auto-recovery check every 30 seconds
```

The circuit breaker protects the rest of the system from a struggling agent. When the handoff service is slow, the Lead Bot does not hang waiting -- it receives a graceful fallback that keeps the lead engaged while the issue resolves.

## Auto-Scaling

The mesh monitors dispatch throughput per agent and scales horizontally when sustained load exceeds capacity:

**Scale-up trigger**: Dispatch queue depth > 100 for 30 consecutive seconds.

**Scale-down trigger**: Average utilization < 30% for 5 minutes.

In practice, our scaling pattern follows lead activity. Morning hours (8-10 AM) see 3x the dispatch volume of mid-afternoon. The mesh scales bot workers from 2 to 6 instances during peak and back down by lunch.

The 4.3 million dispatches per second figure comes from our load test, not production. Production peaks at roughly 12,000 dispatches/second across all agents. But designing for 4.3M means production load never stresses the system. We run at approximately 0.3% of theoretical capacity during peak hours.

## Audit Trails

Every dispatch through the mesh is logged with:

- **Timestamp** (ms precision)
- **Source agent** and **target agent**
- **Dispatch type** (request, response, event, error)
- **Payload hash** (not the full payload -- PII protection)
- **Latency** (time from dispatch to completion)
- **Outcome** (success, failure, timeout, circuit_broken)

This creates a complete provenance trail. When a lead complains about a bad response, we can trace backward from the bot response through the orchestrator call, through the intent analysis, to the original message -- every hop visible in the audit log.

```json
{
  "dispatch_id": "d-7f3a2b1c",
  "timestamp": "2026-02-14T09:23:15.482Z",
  "source": "jorge_lead_bot",
  "target": "intent_decoder",
  "type": "request",
  "capability": "analyze_lead",
  "latency_ms": 142,
  "outcome": "success",
  "priority": "P0"
}
```

We retain 30 days of dispatch logs in Redis (hot) and archive to PostgreSQL (cold) for compliance. The DRE (California Department of Real Estate) requires audit trails for automated consumer interactions. The mesh provides that out of the box.

## Performance Numbers

After 90 days in production:

| Metric | Value |
|--------|-------|
| **Peak throughput (load test)** | 4.3M dispatches/sec |
| **Peak throughput (production)** | 12,000 dispatches/sec |
| **P50 dispatch latency** | 8ms |
| **P95 dispatch latency** | 23ms |
| **P99 dispatch latency** | 67ms |
| **Circuit breaker trips (30 days)** | 7 |
| **Auto-recovery success rate** | 100% |
| **Governance violations blocked** | 342 |
| **Audit log completeness** | 99.97% |

The 342 governance violations were mostly during development -- agents attempting to call capabilities they had not registered. In production, the number drops to single digits per month because the registration step catches configuration errors at startup.

## Lessons Learned

**1. Registration is your first line of defense.** Making agents declare capabilities and dependencies upfront catches 80% of integration errors before they hit production.

**2. Backpressure beats rejection.** Early versions of our rate limiter dropped excess dispatches. This caused data loss and inconsistent state. Queuing with backpressure is always the right default.

**3. Priority routing requires discipline.** It is tempting to mark everything as P0. We enforce that only active human-facing conversations get P0 priority. Everything else is P1 or lower.

**4. Audit trails pay for themselves.** The engineering cost of logging every dispatch is minimal (3-5% overhead). The debugging time saved is enormous. Every production incident in the last 60 days was resolved by reading the audit trail.

**5. Design for 100x, run at 1x.** Our 4.3M dispatch/sec capacity means we never worry about production load. This over-provisioning sounds wasteful but it means zero scaling-related incidents.

---

Building multi-agent AI systems? I work on agent mesh architectures, real-time CRM orchestration, and AI governance patterns. If you are wrestling with agent coordination at scale, let's connect.

[Portfolio](https://github.com/rovo-dev) | DM me on LinkedIn
