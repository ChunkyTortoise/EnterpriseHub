---
title: "Building a Multi-Agent Handoff System That Doesn't Lose Context"
published: false
tags: python, ai, chatbot, architecture
cover_image:
canonical_url:
---

# Building a Multi-Agent Handoff System That Doesn't Lose Context

Most multi-agent tutorials show you how to build individual agents. They skip the hard part: what happens when Agent A needs to hand off to Agent B without losing everything the user just said.

I built a 3-bot system for real estate lead qualification -- Lead Bot, Buyer Bot, Seller Bot -- that manages a $50M+ pipeline. The handoff system between them has more code, more tests, and caused more production incidents than any individual bot.

This is the technical breakdown of the handoff architecture, the failure modes we hit, and the production metrics after 6 months.

---

## Why Handoffs Are Hard

A single chatbot is a state machine. Multiple chatbots that need to coordinate are a distributed system. Distributed systems fail in distributed ways.

Consider this scenario: A lead is being qualified by the Lead Bot. Midway through, they say "Actually, I'm thinking about selling my house." The system needs to:

1. **Detect the intent shift** with high confidence (not just keyword matching)
2. **Package the conversation context** (everything extracted so far: budget, timeline, preferences)
3. **Route to the correct bot** (Seller Bot, not Buyer Bot)
4. **Transfer context** so the Seller Bot doesn't re-ask questions
5. **Prevent loops** if the lead later says "but I might also buy something"

Each step can fail independently. And failures compound.

## The Architecture

### Handoff Service

The core is a `JorgeHandoffService` that evaluates every message for handoff signals:

```python
class JorgeHandoffService:
    CONFIDENCE_THRESHOLD = 0.7
    COOLDOWN_MINUTES = 30
    MAX_HANDOFFS_PER_HOUR = 3
    MAX_HANDOFFS_PER_DAY = 10

    async def evaluate_handoff(self, contact_id, message, source_bot, conversation_history):
        # 1. Check rate limits
        if self._exceeds_rate_limit(contact_id):
            return HandoffResult(action="stay", reason="rate_limited")

        # 2. Check circular prevention
        if self._is_circular(contact_id, source_bot, target_bot):
            return HandoffResult(action="stay", reason="circular_prevention")

        # 3. Evaluate intent confidence
        confidence = await self._score_intent(message, conversation_history)
        if confidence < self.CONFIDENCE_THRESHOLD:
            return HandoffResult(action="stay", reason="low_confidence")

        # 4. Check target bot health
        if not self._target_healthy(target_bot):
            return HandoffResult(action="defer", reason="target_unhealthy")

        # 5. Execute handoff
        return await self._execute_handoff(contact_id, source_bot, target_bot, context)
```

### Safety Mechanisms

**Circular prevention**: A 30-minute cooldown window prevents the same source-target handoff pair from repeating. If Lead Bot hands off to Buyer Bot, the reverse (Buyer -> Lead) is blocked for 30 minutes.

**Rate limiting**: Maximum 3 handoffs per hour, 10 per day per contact. Rapid message sequences can't overwhelm the system.

**Contact-level locking**: Only one handoff can be in progress per contact at any time. Prevents concurrent handoffs from race conditions.

**Performance-based routing**: If the target bot's P95 latency exceeds 120% of its SLA threshold, or its error rate exceeds 10%, handoffs are deferred until health recovers.

**Pattern learning**: After accumulating 10+ handoff outcomes for a specific pattern, the system adjusts confidence thresholds. If Lead->Buyer handoffs triggered by "budget" mentions consistently succeed, the threshold drops from 0.7 to 0.65 for that pattern.

### Context Transfer

The context package sent between bots includes:

```python
@dataclass
class HandoffContext:
    contact_id: str
    source_bot: str
    target_bot: str
    conversation_summary: str
    extracted_data: dict  # budget, timeline, preferences, scores
    frs_score: float      # Financial Readiness Score
    pcs_score: float      # Psychological Commitment Score
    temperature: str      # Hot / Warm / Cold
    handoff_reason: str
    timestamp: datetime
```

This is stored in GHL custom fields with a 24-hour TTL. The target bot reads the context before its first message, so it already knows the lead's budget, timeline, and qualification progress.

## Failure Modes We Hit

### 1. The Infinite Loop (Week 1)

A lead said "I want to sell my house and buy a new one." Lead Bot detected seller intent, handed off to Seller Bot. Seller Bot detected buyer intent, handed off to Buyer Bot. Buyer Bot detected seller intent...

**Fix**: Cooldown window. Same source-target pair blocked for 30 minutes. Plus a maximum depth counter (3 handoffs in a chain before forcing human escalation).

### 2. The Context Wipe (Week 2)

When Seller Bot received a handoff, it would start fresh: "Hi! I'd love to help you sell your home. What's your timeline?" The lead had already shared their timeline with Lead Bot.

**Fix**: Enriched context transfer. Every extracted data point (budget, timeline, location, pre-approval status) is packaged and sent with the handoff. The target bot's opening message references what it already knows.

### 3. The Race Condition (Week 3)

Two messages arrived simultaneously. The first triggered a Lead -> Buyer handoff. The second triggered a Lead -> Seller handoff. Both succeeded, and the contact was now in two conversations.

**Fix**: Contact-level locking with a Redis-backed mutex. Only one handoff operation per contact at a time. Second request queues and re-evaluates after the first completes.

## Production Results

After 6 months:

| Metric | Value |
|--------|-------|
| Context loss on handoffs | 0% |
| Orchestration overhead | <200ms (P99: 0.095ms) |
| Handoff success rate | 94.7% |
| Automated tests | 5,100+ |
| Pipeline managed | $50M+ |
| False positive handoffs | 2.1% |

The handoff service alone has 205 passing tests -- more than many entire bot implementations.

## Key Takeaways

1. **Coordination is harder than conversation.** Building 3 individual bots took 3 weeks. Building the handoff system took 5 weeks. The coordination layer is the real engineering challenge.

2. **Safety mechanisms are not optional.** Every failure mode listed above happened in production. Without circular prevention, rate limiting, and locking, the system would be unusable.

3. **Threshold of 0.7 is the sweet spot.** Below 0.7, too many false positive handoffs (users get bounced unnecessarily). Above 0.8, too many missed handoffs (users stay in the wrong bot). 0.7 balances precision and recall.

4. **Pattern learning works, but slowly.** You need 10+ data points per pattern before adjustments are reliable. Don't let the system self-adjust too aggressively early on.

## Try It

Full source code: [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

The handoff service is at `services/jorge/jorge_handoff_service.py`. The bot implementations are in `agents/jorge_*.py`.

---

*Building multi-agent systems? I write about production AI architectures, cost optimization, and CRM integrations. Connect on [LinkedIn](https://linkedin.com/in/caymanroden) or check my [GitHub](https://github.com/ChunkyTortoise).*
