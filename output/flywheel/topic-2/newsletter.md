# Newsletter Edition: The Multi-Agent Handoff Problem Nobody Talks About

**Topic**: Multi-Agent Orchestration
**Format**: Email newsletter (800-1,200 words)
**Subject line options**:
- "My chatbots kept arguing with each other (here's the fix)"
- "The engineering problem harder than building the AI itself"
- "3 bots, 1 pipeline, 0 context loss -- here's how"

---

Hey,

I built three chatbots. They work great individually. Put them together and everything broke.

This is the story of building a multi-agent handoff system -- the coordination layer that decides which bot should talk to which lead, when to transfer a conversation, and how to do it without losing context.

Spoiler: the handoff system has more code and more tests than any individual bot.

---

## The Setup

We have three specialized bots for real estate lead qualification:
- **Lead Bot**: Initial qualification, temperature scoring
- **Buyer Bot**: Financial readiness, property preferences
- **Seller Bot**: Home valuation motivation, timeline assessment

Each bot is good at its job. The problem is transitions. When a lead says "I'm thinking about selling" during a buyer flow, something needs to catch that, package the context, and route to the right bot.

## Three Things That Broke

**1. The infinite loop.** A lead said "I want to sell my house and buy a new one." Lead Bot handed off to Seller Bot. Seller Bot detected buyer intent, handed off to Buyer Bot. Buyer Bot detected seller intent... you get the picture.

Fix: 30-minute cooldown window for same source-target pairs, plus a 3-handoff depth limit before forcing human escalation.

**2. Context wipe.** After a handoff, the Seller Bot would re-ask questions the lead had already answered. "What's your timeline?" -- they just told the Lead Bot it was 3 months.

Fix: Enriched context transfer. Every extracted data point (budget, timeline, preferences, scores) is packaged and stored in CRM custom fields with a 24-hour TTL. The receiving bot reads the context before its first message.

**3. Race condition.** Two messages arrived simultaneously. Both triggered different handoffs. The contact ended up in two conversations.

Fix: Contact-level locking with a Redis mutex. One handoff per contact at a time.

## The Architecture That Works

The handoff service evaluates every message against a 0.7 confidence threshold. Below 0.7, the lead stays with the current bot. Above 0.7, the system checks rate limits (3/hour, 10/day), circular prevention, and target bot health before executing the transfer.

The key insight: **performance-based routing**. If the target bot's P95 latency exceeds 120% of its SLA threshold or its error rate exceeds 10%, handoffs are deferred. Better to keep a lead in a slightly wrong conversation than hand them to a struggling bot.

After 10+ handoff outcomes for a specific pattern, the system learns. If "budget" mentions consistently lead to successful Buyer Bot handoffs, the confidence threshold drops from 0.7 to 0.65 for that pattern.

## The Numbers

After 6 months in production:
- Context loss: 0%
- Orchestration overhead: <200ms (P99: 0.095ms)
- Handoff success rate: 94.7%
- Tests: 5,100+ (the handoff service alone has 205)
- Pipeline managed: $50M+

## The Lesson

Coordination is harder than conversation. Building 3 individual bots took 3 weeks. Building the handoff system took 5. The safety mechanisms (circular prevention, rate limiting, locking, performance routing) are not optional -- every failure mode I listed happened in production within the first month.

If you're building multi-agent systems, budget more time for the coordination layer than for any individual agent.

The full system is open source: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

Reply if you're building multi-agent systems -- I'd love to compare notes.

Cayman

---

*P.S. We're launching AgentForge next week -- a lightweight multi-LLM orchestration framework that makes building systems like this much easier. If you want early access, reply to this email.*
