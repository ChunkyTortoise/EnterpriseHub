# Twitter/X Thread: Multi-Agent Orchestration

**Topic**: Multi-Agent Orchestration (Bot Handoffs)
**Format**: 7-tweet thread
**CTA**: GitHub repo link

---

## Tweet 1 (Hook)

I built a system where chatbots decide which chatbot should answer.

3 bots. Real estate lead qualification. The hard part wasn't the bots -- it was the handoffs between them.

Here's what broke and how I fixed it:

[thread]

---

## Tweet 2 (The Problem)

When a lead says "I'm thinking about selling" during a buyer flow, the system needs to:

1. Detect intent shift (0.7 confidence)
2. Package conversation context
3. Route to Seller Bot
4. Prevent circular routing

Sounds simple. It's not.

---

## Tweet 3 (What Broke)

Three things broke immediately:

1. Handoff loops: "I might buy AND sell" bounced between bots forever
2. Context loss: Seller Bot re-asked questions already answered
3. Rate abuse: Fast message sequences = 10+ handoffs/hour

Each failure mode needed its own safety mechanism.

---

## Tweet 4 (The Fixes)

The fixes:

Loops -> 30-min cooldown for same source-target pairs
Context loss -> Enriched context in GHL custom fields (24h TTL)
Rate abuse -> 3 handoffs/hr, 10/day per contact
Concurrent conflicts -> Contact-level locking

Plus: performance-based routing that defers when target bot P95 > SLA.

---

## Tweet 5 (Architecture)

The full handoff architecture:

- Confidence scoring (0.7 threshold, learned from outcomes)
- Circular prevention with cooldown windows
- Contact-level locking
- Performance-based routing
- Pattern learning (min 10 data points)

Coordination is harder than conversation.

---

## Tweet 6 (Results)

Production results:

- Zero context loss on handoffs
- <200ms orchestration overhead
- P99: 0.095ms (yes, sub-millisecond)
- 5,100+ automated tests
- $50M+ pipeline managed

The handoff service has more tests than any individual bot.

---

## Tweet 7 (CTA)

The full system is open source (MIT):
github.com/ChunkyTortoise/EnterpriseHub

Includes the handoff service, all 3 bots, performance tracker, A/B testing, and alerting.

What's your approach to multi-agent coordination?
