# Reddit Post: Multi-Agent Handoff System

**Topic**: Multi-Agent Orchestration
**Subreddit**: r/MachineLearning
**Format**: Technical discussion with production data
**Flair**: [Project]

---

## Title

I built a multi-agent handoff system for 3 chatbots managing a $50M pipeline. Here's what broke and the architecture that fixed it.

## Body

**tl;dr**: 3 specialized bots (Lead, Buyer, Seller) for real estate qualification. The handoff system between them is more complex than any individual bot. 0.7 confidence threshold, circular prevention, contact-level locking, performance-based routing. 205 tests on the handoff service alone. Full code is open source.

---

**Context**: Real estate platform with 3 SMS chatbots that qualify leads. Each bot specializes: Lead Bot does temperature scoring, Buyer Bot assesses financial readiness, Seller Bot evaluates motivation and timeline. Leads need to flow between bots as intent shifts during conversations.

**What broke first**:

1. **Infinite loops**: Lead says "sell AND buy" -> bounces between bots forever. Fix: 30-min cooldown for same source-target pairs + 3-handoff depth limit.

2. **Context loss**: Target bot re-asks questions already answered. Fix: Enriched context transfer (budget, timeline, scores, preferences) stored in CRM custom fields with 24h TTL. Target bot reads context before first message.

3. **Race conditions**: Two simultaneous messages trigger two different handoffs for the same contact. Fix: Redis-backed contact-level mutex.

**Handoff architecture**:

```
Message -> Intent Detection -> Confidence Scoring (threshold: 0.7)
                                    |
                            [Below 0.7: Stay]
                            [Above 0.7: Check safety]
                                    |
                    Rate Limit (3/hr, 10/day) -> Circular Check (30-min cooldown)
                                    |
                    Target Health Check (P95 < 120% SLA, error < 10%)
                                    |
                    Contact Lock (Redis mutex) -> Execute Handoff
                                    |
                    Context Package -> GHL Custom Fields (24h TTL)
```

**Key design decisions**:

- **0.7 threshold**: Below 0.7 = too many false positive handoffs (users bounced unnecessarily). Above 0.8 = too many missed handoffs (users stuck in wrong bot). 0.7 balances precision/recall. We tried 0.6 and 0.8, both worse.

- **Performance-based routing**: If target bot P95 > 120% SLA or error rate > 10%, handoffs defer. Better to keep lead in slightly wrong conversation than hand to struggling bot.

- **Pattern learning**: After 10+ outcomes for a pattern (e.g., "budget" mention -> Buyer Bot), system adjusts threshold. Minimum data requirement prevents premature optimization.

- **Human escalation**: After 3 handoffs in a chain, force escalation to human agent. No automated system should bounce a lead more than 3 times.

**6-month production results**:

| Metric | Value |
|--------|-------|
| Context loss on handoffs | 0% |
| Orchestration overhead | <200ms (P99: 0.095ms) |
| Handoff success rate | 94.7% |
| False positive rate | 2.1% |
| Automated tests | 5,100+ (205 on handoff service alone) |
| Pipeline managed | $50M+ |

**Biggest lesson**: Coordination is harder than conversation. 3 bots took 3 weeks. The handoff system took 5 weeks. Every safety mechanism (circular prevention, rate limiting, locking) was added because the failure mode happened in production.

**Code**: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

Handoff service: `services/jorge/jorge_handoff_service.py`
Bot implementations: `agents/jorge_*.py`

Happy to discuss the confidence threshold tuning, pattern learning implementation, or how the context transfer works in practice.
