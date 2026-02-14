# Prospect: Assembled

**Segment**: SaaS CTO | **Template**: Template 3
**Priority**: Batch 2, Week 2

---

## Company Research

Assembled is a workforce management platform for customer support teams, founded by Ryan Wang (CEO) and other co-founders who are Stripe alumni. Headquartered in San Francisco, CA. Raised $51M in Series B (led by New Enterprise Associates, with Emergence Capital and Basis Set Ventures). The platform manages both human agents and AI agents, helping companies optimize their support operations. Recently opened a London office for European expansion.

## Why They're a Fit

Assembled manages both human AND AI agents -- the hybrid orchestration problem is directly relevant. Their Stripe DNA means they value clean infrastructure and production-grade engineering. As they help companies manage AI agents, they need deep expertise in AI orchestration, performance monitoring, and cost optimization. The fractional AI CTO offering aligns with their need to understand AI agent performance.

## Personalization Hooks

- Stripe alumni founding team -- high engineering standards
- Manages both human and AI agents -- hybrid orchestration challenge
- Series B with $51M -- scaling rapidly
- Ryan's journey "from engineer to CEO" shows technical depth
- European expansion via London office -- growing complexity

---

## Email Sequence

### Day 1: Initial Outreach

**Subject**: Fractional AI CTO -- $150/hr vs $250K/yr hire

Hi Ryan,

Assembled's positioning on managing both human AND AI agents is exactly right. The next challenge for support ops isn't just scheduling humans -- it's orchestrating the handoffs between AI and human agents.

I built a multi-agent orchestration system that handles exactly this:
- **Confidence-scored handoffs** -- AI agents route to human agents (or other AI agents) based on confidence thresholds
- **Zero context loss** -- conversation history, qualification data, and intent signals transfer with the handoff
- **P99: 0.095ms** coordination latency between agents
- **89% LLM cost reduction** via 3-tier caching

With your Stripe background, I think you'd appreciate the engineering rigor: 8,500+ tests across 11 production repos, P50/P95/P99 benchmarks on every system, and ADRs documenting every architectural decision.

Worth a 30-minute discovery call?

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com | (310) 982-0492

### Day 4: Follow-Up

**Subject**: Re: Fractional AI CTO -- $150/hr vs $250K/yr hire

Hi Ryan,

Follow-up with a specific insight on the AI-to-human handoff problem:

Most systems lose context during handoff. My system preserves it using enriched context objects stored in CRM custom fields with 24-hour TTL. When an AI agent hands off to a human, the human sees: conversation summary, lead score, intent classification, budget, timeline, and recommended next action.

The result: human agents pick up where the AI left off, not from scratch.

15 minutes to discuss how this applies to Assembled's platform?

Cayman

### Day 8: Final Touch

**Subject**: AI-to-human handoff architecture

I documented the enriched handoff architecture that preserves full context during AI-to-human transitions. Reply "send it" if useful.

Cayman

---

## LinkedIn Messages

### Connection Request

Hi Ryan -- Fellow ex-Stripe ecosystem builder here. I build multi-agent orchestration systems with confidence-scored handoffs (89% cost reduction, P99: 0.095ms). Assembled's approach to managing AI + human agents is directly relevant. Would love to connect.

### Follow-Up Message

Thanks for connecting, Ryan. The AI-to-human handoff is the hardest part of hybrid support ops. I built a system that preserves full context during transitions (conversation history, intent, scoring) with sub-millisecond coordination. Could be valuable for Assembled's platform. Open to a 30-minute architecture walkthrough?
