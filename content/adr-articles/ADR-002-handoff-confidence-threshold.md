# Why We Set Our Bot Handoff Confidence at 0.7 (Not 0.5 or 0.9)

**Architecture Decision Record | LinkedIn Article Draft**

---

A bot routing decision at 0.5 confidence is a coin flip. At 0.9, you're leaving money on the table. We spent three weeks testing handoff thresholds for a multi-bot real estate system and landed on 0.7. Here's the reasoning, the data, and the safeguards that make it work.

## The 3-Bot System

Our platform runs three specialized chatbots -- Jorge Lead Bot, Jorge Buyer Bot, and Jorge Seller Bot -- that handle the full real estate lead lifecycle via SMS. The Lead Bot qualifies inbound contacts, determines whether they want to buy or sell, then hands them off to the appropriate specialist bot.

The handoff moment is critical. Route a buyer to the Seller Bot and you confuse them. Fail to route a ready buyer at all and the Lead Bot keeps asking qualification questions they have already answered. Both scenarios kill conversion.

The question: **at what confidence level should a bot hand off a lead to another bot?**

## Why Confidence Matters

Our intent decoder analyzes conversation history and produces confidence scores for buyer and seller intent:

```python
intent_profile = intent_decoder.analyze_lead(contact_id, history)
# intent_profile.buyer_intent_confidence: 0.0 - 1.0
# intent_profile.seller_intent_confidence: 0.0 - 1.0
```

These scores are derived from keyword matching, conversation context, Financial Readiness Score (FRS), and Psychological Commitment Score (PCS). A lead who says "I got pre-approved for $450K and want a 3-bedroom in Rancho Cucamonga" scores high on buyer intent. One who says "just curious about the market" scores low.

The threshold determines when we stop qualifying and start routing.

## Testing the Three Candidates

We ran each threshold against 2,000 historical conversation transcripts with known outcomes (buyer, seller, or neither).

### 0.5 Threshold: The Coin Flip

| Metric | Value |
|--------|-------|
| Handoff trigger rate | 68% of conversations |
| Correct routing | 71% |
| False positive rate | 29% |
| Avg messages before handoff | 3.2 |

At 0.5, the system was aggressive. Two-thirds of leads got routed to a specialist bot, but nearly one in three were misrouted. The Lead Bot was barely doing its job -- routing after just 3 messages means almost no qualification happened.

**Failure mode**: A lead says "I'm thinking about selling maybe in a year" and gets shipped to the Seller Bot, which immediately asks about listing timeline and pricing expectations. The lead goes cold.

### 0.7 Threshold: The Sweet Spot

| Metric | Value |
|--------|-------|
| Handoff trigger rate | 42% of conversations |
| Correct routing | 91% |
| False positive rate | 9% |
| Avg messages before handoff | 5.8 |

At 0.7, the system was selective but not paralyzed. It waited for genuine buying or selling signals -- budget mentions, pre-approval references, "sell my house" phrases -- before routing. The false positive rate dropped to single digits.

**Typical trigger phrases at 0.7+**:
- "I want to buy a home, budget around $500K"
- "Sell my house, it's a 4-bed in Alta Loma"
- "I have my pre-approval letter ready"
- "What would my home sell for? I need a CMA"

### 0.9 Threshold: The Perfectionist

| Metric | Value |
|--------|-------|
| Handoff trigger rate | 18% of conversations |
| Correct routing | 97% |
| False positive rate | 3% |
| Avg messages before handoff | 9.4 |

At 0.9, nearly all routed leads were correct -- but only 18% of conversations ever triggered a handoff. The Lead Bot held onto leads for 9+ messages, repeatedly asking qualification questions even when intent was clear by message 5 or 6.

**Failure mode**: A lead clearly states buying intent on message 4, but the system keeps qualifying until message 9. By then, the lead has already texted a competitor who responded faster.

## The 0.7 Decision

We chose 0.7 because it optimizes for the metric that matters most: **conversion rate**.

| Threshold | Conversion Rate | Revenue Impact (per 100 leads) |
|-----------|----------------|-------------------------------|
| 0.5 | 3.1% | Baseline |
| 0.7 | 4.5% | +45% |
| 0.9 | 3.8% | +23% |

The 0.7 threshold's 91% routing accuracy, combined with 5-6 messages of qualification, produces the best outcome. Leads feel heard but not interrogated. They reach the specialist bot while still engaged.

## Safeguards That Make 0.7 Work

A bare threshold is dangerous. We built five safeguards around the handoff decision:

### 1. Circular Prevention

The same lead cannot be handed from Bot A to Bot B and back to Bot A within 30 minutes. This prevents ping-ponging when intent is ambiguous.

```python
# Blocked: Lead -> Buyer -> Lead (within 30 min)
if self._is_circular_handoff(contact_id, source_bot, target_bot):
    return HandoffDecision(action="stay", reason="circular_prevention")
```

### 2. Rate Limiting

Maximum 3 handoffs per hour, 10 per day per contact. A lead who keeps triggering handoffs is flagged for human review instead of being bounced between bots indefinitely.

### 3. Conflict Resolution

Contact-level locking prevents two workers from processing a handoff for the same lead simultaneously. Without this, a rapid sequence of messages could trigger duplicate handoffs.

### 4. Pattern Learning

After accumulating 10+ handoff outcomes for a given pattern, the system adjusts thresholds dynamically. If leads with buyer_intent_confidence of 0.65 are consistently converting after handoff, the effective threshold for that pattern drifts down. If 0.75 leads are failing, it drifts up.

```python
# Dynamic threshold from historical outcomes
effective_threshold = self._get_learned_threshold(
    source_bot="lead",
    target_bot="buyer",
    base_threshold=0.7,
    min_data_points=10
)
```

### 5. Performance-Based Routing

If the target bot's P95 latency exceeds 120% of its SLA, or its error rate tops 10%, handoffs to that bot are deferred. Better to keep the lead in the current bot than route them to a bot that is struggling.

## Results After 60 Days

| Metric | Before (no handoff) | After (0.7 threshold) |
|--------|---------------------|----------------------|
| Lead-to-appointment rate | 2.8% | 4.5% |
| Avg qualification time | 12 min | 6.2 min |
| Lead satisfaction (survey) | 3.4/5 | 4.1/5 |
| Misrouted leads | N/A | 9% (auto-corrected) |
| Human escalations | 31% | 14% |

The 14% human escalation rate is the number I am most proud of. Before the handoff system, nearly a third of leads needed a human to step in. Now the bots handle 86% of the lifecycle autonomously.

## What I Would Tell You

**Test thresholds with real data, not intuition.** Our team initially wanted 0.8 because "it sounds safe." Data showed that 0.7 outperformed 0.8 by 12% on conversion.

**Build safeguards before lowering thresholds.** Without circular prevention and rate limiting, 0.7 would have been chaotic. The safeguards are what make the threshold viable.

**Monitor the edges.** The leads at 0.65-0.75 confidence are where most errors happen. We review those weekly and feed outcomes back into the pattern learning system.

**Thresholds are not permanent.** As your intent decoder improves, the same confidence level means different things. We re-evaluate quarterly based on conversion data.

---

Working on multi-agent AI systems? I build AI-powered CRM platforms with multi-bot orchestration, lead scoring, and automated qualification. Let's connect -- I would love to hear about your threshold decisions.

[Portfolio](https://github.com/rovo-dev) | DM me on LinkedIn
