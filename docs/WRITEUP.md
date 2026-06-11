# How EnterpriseHub Works: The Narrative Version

The 13 [ADRs](adr/) record individual decisions. This page is the story a reviewer
would get in an interview: what the system does, the three design problems that
shaped it, and what I would tell you to go read.

## The product in one paragraph

A real estate team in Rancho Cucamonga gets leads from Zillow, Facebook ads, and
open houses. Most arrive as a single SMS like "thinking about selling my house."
EnterpriseHub answers those messages with three specialized bots (lead intake,
buyer, seller), qualifies the lead over a handful of texts, writes everything back
to the GoHighLevel CRM, and hands hot leads to a human agent with full context.
It ran for about three months in production and processed 500+ leads
([case study](../CASE_STUDY.md); CRM export not public).

## Problem 1: one bot can't be good at three jobs

A seller conversation needs CMA pricing talk; a buyer conversation needs
pre-approval and inventory matching; intake needs fast triage. One prompt doing
all three did none well. The split into three bots created a new problem:
conversations change type mid-stream ("actually, we'd also need to buy on the
other end"). The handoff service (`services/jorge/jorge_handoff_service.py`,
[ADR-0003](adr/0003-jorge-handoff-architecture.md)) scores intent confidence per
message and transfers the conversation only above a 0.7 threshold, with circular-
handoff prevention and per-contact rate limits (3/hr, 10/day) so two bots can't
ping-pong a confused lead. State isolation between bots is its own decision
([ADR-0013](adr/0013-handoff-state-isolation.md)).

## Problem 2: LLM costs scale with chattiness, revenue doesn't

SMS conversations are repetitive: the same objections, the same opening questions,
the same neighborhoods. The orchestrator (`services/claude_orchestrator.py`,
[ADR-0001](adr/0001-three-tier-redis-caching.md), [ADR-0008](adr/0008-multi-llm-orchestration.md))
puts a three-tier cache in front of every model call: L1 exact-match in memory,
L2 normalized-prompt in Redis, L3 semantic similarity. The measured L1 number is
90.8% on a synthetic hot-key workload ([receipts](RECEIPTS.md)); the cost model
projects a 93K-to-7.8K token reduction per 100 queries. Above the cache sits a
mesh coordinator ([ADR-0004](adr/0004-agent-mesh-coordinator.md)) that routes
tasks to the cheapest capable agent and hard-stops everything at $100/hr.
Where the coordinator's behavior is scaffolding rather than real (auto-scaling,
rebalancing), [ADR-0011](adr/0011-mesh-coordinator-scaffold-status.md) says so
explicitly; honest labels beat impressive vapor.

## Problem 3: how do you know the bots are any good?

Vibes don't survive a compliance complaint. Quality is enforced three ways:

1. **Golden dataset**: 50 hand-curated cases in [`evals/`](../evals/) covering
   qualification flows, edge cases ("can you help me write a resume?"), and
   compliance traps ("under CCPA I demand you delete my data").
2. **LLM-judge rubrics**: every case is scored on correctness, tone, safety, and
   compliance (`evals/judge.py`, `evals/rubrics.py`). Baseline: 0.90 / 0.90 /
   1.00 / 0.95.
3. **A nightly regression gate**: `.github/workflows/nightly-eval.yml` re-runs the
   harness, publishes the badge in the README, and opens an issue if the pass
   rate drops more than 10% below baseline.

Compliance is also structural, not just tested: every outbound message passes a
seven-stage response pipeline (language, TCPA, repair, compliance, disclosure,
translation, SMS formatting; [ADR-0007](adr/0007-compliance-response-pipeline.md)).

## What to read next

- 5-minute code tour: the Architecture Tour section of the [README](../README.md)
- Decision history: [docs/adr/](adr/) (13 records, all accepted)
- The numbers with caveats: [docs/RECEIPTS.md](RECEIPTS.md)
- Try it: `make demo` locally, or the live operator console linked from the README
