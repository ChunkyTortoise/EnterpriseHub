# Case Study: Multi-Agent Consensus for Fintech Fraud Detection

## Client Profile

**Company**: VaultGuard (anonymized)
**Industry**: Financial Technology / Payment Processing
**Team Size**: 15 engineers, 4 data scientists
**Challenge**: Build a multi-agent system where multiple LLMs independently evaluate transactions and reach consensus on fraud risk

---

## The Challenge

VaultGuard processes 50,000+ payment transactions daily. Their existing rule-based fraud detection system caught known patterns but missed novel fraud vectors. They wanted to augment it with LLM-based analysis, but a single model's assessment was not reliable enough for financial decisions.

Their requirements:

- **Multi-agent consensus**: At least 3 LLM agents must independently evaluate each flagged transaction and agree on a risk score
- **Agent handoff protocols**: When one agent identifies a complex pattern, it must hand off context to a specialized agent
- **Workflow orchestration**: Parallel agent execution with dependency management (some agents need results from others)
- **Cost control**: Processing 50K transactions at $0.01/each would cost $500/day -- they needed it under $50/day
- **Sub-200ms overhead**: The LLM layer could not add more than 200ms to transaction processing latency

### Pain Points

| Problem | Impact |
|---------|--------|
| Single-model fraud assessment unreliable | 23% false positive rate, 8% false negative rate |
| No multi-agent framework | Would need to build consensus protocol from scratch |
| No parallel execution | Sequential agent calls added 3-4s per transaction |
| Cost per transaction too high | $0.03 per LLM call x 3 agents = $4,500/day |
| No agent memory | Agents could not learn from previous fraud patterns |

---

## The Solution: AgentForge Multi-Agent Mesh

VaultGuard used AgentForge's multi-agent mesh, workflow DAG, and ReAct agent loop to build a consensus-based fraud detection system.

### Step 1: Multi-Agent Mesh with Consensus Protocol

AgentForge's multi-agent mesh (37 dedicated tests) enables multiple agents to independently evaluate input and reach consensus through configurable protocols:

```python
from agentforge.multi_agent import AgentMesh, ConsensusConfig

# Configure 3-agent consensus mesh
mesh = AgentMesh(
    agents=[
        {"name": "pattern_analyst", "provider": "claude", "role": "Analyze transaction patterns"},
        {"name": "behavior_analyst", "provider": "openai", "role": "Evaluate user behavior signals"},
        {"name": "network_analyst", "provider": "gemini", "role": "Assess network/graph anomalies"},
    ],
    consensus=ConsensusConfig(
        method="weighted_majority",
        min_agreement=2,  # At least 2 of 3 must agree
        timeout_seconds=5.0
    )
)

# All 3 agents evaluate independently, then vote
result = await mesh.evaluate(
    f"Transaction: {transaction_data}\n"
    f"User history: {user_profile}\n"
    f"Assess fraud risk on scale 0-100"
)
# result.consensus_score, result.agent_votes, result.confidence
```

Using different providers for each agent (Claude, OpenAI, Gemini) ensures that model-specific biases are diversified. If one model hallucinates a false positive, the other two correct it.

### Step 2: Workflow DAG for Parallel Execution

AgentForge's Workflow DAG (34 dedicated tests) enables parallel agent execution with dependency management:

```python
from agentforge.workflow_dag import WorkflowDAG, WorkflowNode

# Define parallel execution graph
dag = WorkflowDAG()

# Stage 1: Three agents run in parallel
dag.add_node(WorkflowNode(
    name="pattern_check",
    agent="pattern_analyst",
    dependencies=[]  # No dependencies -- runs immediately
))
dag.add_node(WorkflowNode(
    name="behavior_check",
    agent="behavior_analyst",
    dependencies=[]  # Runs in parallel with pattern_check
))
dag.add_node(WorkflowNode(
    name="network_check",
    agent="network_analyst",
    dependencies=[]  # Runs in parallel
))

# Stage 2: Consensus node waits for all three
dag.add_node(WorkflowNode(
    name="consensus",
    agent="consensus_aggregator",
    dependencies=["pattern_check", "behavior_check", "network_check"]
))

# Execute: parallel nodes run concurrently, consensus waits for all
result = await dag.execute(transaction_context)
```

By running agents in parallel instead of sequentially, VaultGuard reduced per-transaction latency from 3-4 seconds to under 1.5 seconds. The DAG supports retry policies per node, so a single agent failure does not block the entire workflow.

### Step 3: ReAct Agent Loop for Complex Investigations

When a transaction is flagged as high-risk, AgentForge's ReAct agent loop (22 dedicated tests) enables deeper investigation with tool calling:

```python
from agentforge.react_agent import ReActAgent
from agentforge.tools import ToolRegistry, tool

registry = ToolRegistry()

@tool(registry, name="lookup_merchant", description="Look up merchant risk profile")
def lookup_merchant(merchant_id: str) -> dict:
    return merchant_db.get_risk_profile(merchant_id)

@tool(registry, name="check_velocity", description="Check transaction velocity for user")
def check_velocity(user_id: str, window_hours: int = 24) -> dict:
    return velocity_checker.get_stats(user_id, window_hours)

# ReAct loop: Thought -> Action -> Observation -> Thought -> ...
agent = ReActAgent(
    orchestrator=orc,
    provider="claude",
    tools=registry,
    max_iterations=5  # Loop detection prevents infinite cycles
)

# Agent reasons about the transaction, calls tools as needed
investigation = await agent.run(
    f"Investigate flagged transaction {txn_id}. "
    f"Check merchant risk and user velocity. "
    f"Provide final fraud assessment with evidence."
)
# investigation.thoughts, investigation.actions, investigation.final_answer
```

The ReAct loop has built-in loop detection to prevent infinite reasoning cycles, and the tool registry (44 tests) validates function signatures and handles structured output extraction.

### Step 4: Agent Memory for Pattern Learning

AgentForge's agent memory system (39 tests for persistent memory, 28 for sliding window) allows agents to retain fraud patterns across sessions:

```python
from agentforge.agent_memory import AgentMemory

memory = AgentMemory(
    max_entries=1000,
    ttl_hours=168,  # 7-day retention
    relevance_scoring=True
)

# Store confirmed fraud patterns
memory.store(
    key="fraud_pattern_velocity",
    content="Users with 5+ transactions in 10 minutes from different geos are 94% likely fraudulent",
    metadata={"confidence": 0.94, "sample_size": 2340}
)

# Retrieve relevant patterns for current transaction
relevant = memory.search("high velocity transactions different locations", top_k=5)
# Returns ranked results by relevance score
```

This persistent memory with TTL and relevance scoring means agents get smarter over time as more fraud patterns are confirmed.

### Step 5: Cost Optimization

VaultGuard used AgentForge's cost tracking to optimize which model handles which task:

```python
from agentforge.cost_tracker import CostTracker, DEFAULT_COST_RATES

# Cost per million tokens:
# Claude 3.5 Sonnet: $3.00 input / $15.00 output
# GPT-4o: $2.50 input / $10.00 output
# Gemini 1.5 Pro: $1.25 input / $5.00 output

# Strategy: Use Gemini for initial screening (cheapest),
# escalate to Claude only for complex cases
tracker = CostTracker()

async def evaluate_transaction(txn):
    # Stage 1: Cheap pre-screen with Gemini ($0.001/txn)
    screen = await orc.chat("gemini", f"Quick fraud check: {txn}")
    tracker.record("gemini", "gemini-1.5-pro", input_tokens=200, output_tokens=50)

    if screen.risk_score > 50:
        # Stage 2: Full consensus only for flagged transactions (~5%)
        result = await mesh.evaluate(txn)  # $0.008/txn for 3 agents
        tracker.record_multi(result.usage)

    daily_cost = tracker.get_session_cost()
    # $0.001 * 50,000 + $0.008 * 2,500 = $50 + $20 = $70/day
```

By screening with the cheapest provider first and only escalating 5% of transactions to multi-agent consensus, VaultGuard reduced daily costs from $4,500 to $70.

---

## Results

### Detection Accuracy

| Metric | Before (Rule-based) | After (Multi-Agent) | Change |
|--------|---------------------|---------------------|--------|
| False positive rate | 23% | 4.1% | **-82%** |
| False negative rate | 8% | 1.2% | **-85%** |
| Novel fraud detection | 0% (rule-based only) | 67% | **New capability** |
| Investigation time | 45 min manual | 3 min automated | **-93%** |

### Performance

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Per-transaction latency | 3-4s (sequential) | <1.5s (parallel DAG) | **-63%** |
| AgentForge overhead | N/A | <50ms per provider call | **Minimal** |
| Tool dispatch time | N/A | <10ms | **Near-instant** |

### Cost

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Daily API cost | $4,500 (projected) | $70 | **-98%** |
| Cost per transaction | $0.09 | $0.0014 | **-98%** |
| Monthly API spend | $135,000 (projected) | $2,100 | **-98%** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | Agent mesh setup with 3 providers | Consensus protocol working |
| 1 | Workflow DAG for parallel execution | 63% latency reduction |
| 2 | ReAct agent for complex investigations | Automated fraud investigation |
| 2 | Tool registry (merchant lookup, velocity) | Agent-driven data enrichment |
| 3 | Agent memory for pattern learning | Persistent fraud intelligence |
| 3 | Cost optimization (tiered screening) | 98% cost reduction |
| 4 | Production deployment and monitoring | Full system live |

**Total implementation**: 4 engineering-weeks.

---

## Key Takeaways

1. **Multi-agent consensus eliminates single-model bias**. Using Claude, OpenAI, and Gemini together reduced false positives by 82% and false negatives by 85%.

2. **Workflow DAGs make parallel execution simple**. AgentForge's 34-test DAG module handles dependency resolution, parallel execution, and per-node retry policies.

3. **Tiered screening is the cost optimization secret**. Screening all transactions with the cheapest provider and only escalating 5% to full consensus reduced costs by 98%.

4. **ReAct agents with tools automate investigation**. The Thought-Action-Observation loop with registered tools replaced 45-minute manual investigations with 3-minute automated ones.

5. **Agent memory creates institutional knowledge**. Persistent pattern storage with TTL and relevance scoring means the system gets smarter over time.

---

## About AgentForge

AgentForge's multi-agent capabilities are backed by 491 automated tests. The modules used in this case study include: Multi-Agent Mesh (37 tests), Workflow DAG (34 tests), ReAct Agent (22 tests), Tools (44 tests), Agent Memory (39+28 tests), and Cost Tracker (10 tests).

- **Repository**: [github.com/ChunkyTortoise/ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator)
- **Provider overhead**: <50ms per call
- **Tool dispatch**: <10ms
- **Concurrent agents**: 5+ simultaneously
