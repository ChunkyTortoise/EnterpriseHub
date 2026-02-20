# LinkedIn Post #10 — 3-Bot Handoff System

**Publish Date**: Monday, March 3, 2026 @ 8:30am PT
**Topic**: Portfolio Showcase — Technical Walkthrough
**Goal**: Demonstrate deep multi-agent architecture expertise, drive GitHub traffic, establish authority in conversational AI design

---

## Post Content

Most chatbots answer questions. Mine decide which chatbot should answer.

I built a 3-bot system for real estate lead qualification: Lead Bot, Buyer Bot, Seller Bot. Each one specializes in a different conversation type.

The hard part wasn't building three bots. It was building the handoff system between them.

**The problem: when should Bot A hand off to Bot B?**

Set the confidence threshold too low, and the system routes conversations to the wrong bot. A seller asking about property values gets sent to the buyer qualification flow. Bad experience. Lost lead.

Set it too high, and every conversation stays stuck in the Lead Bot forever. "I want to sell my house" gets three more qualification questions instead of a transfer to the Seller Bot.

**The answer: 0.7 confidence threshold with pattern learning.**

Here's how it works:

**1. Confidence scoring on every message.**

Each bot evaluates incoming messages against handoff trigger patterns. "I want to buy a home" scores high for buyer intent. "What's my house worth?" scores high for seller intent.

But single-message scoring isn't enough. Context matters. So the system evaluates the full conversation history, not just the latest message.

**2. Pattern learning from outcomes.**

The system tracks what happens after each handoff. Did the receiving bot successfully complete the conversation? Did the user disengage? Did they get handed off again?

After 10+ data points for a specific handoff pattern, the system starts adjusting thresholds. If Lead-to-Buyer handoffs at 0.7 confidence result in 90% successful conversations, the threshold stays. If they result in 60% bounce-backs, it tightens.

**3. Circular prevention and rate limiting.**

Without safeguards, you get handoff loops. Bot A sends to Bot B, Bot B sends back to Bot A. The user gets ping-ponged between bots while their patience evaporates.

My safeguards:
- Same source-to-target handoff blocked within a 30-minute window
- 3 handoffs per hour per contact, max
- 10 handoffs per day per contact, hard cap
- Contact-level locking prevents concurrent handoff decisions

**4. Performance-aware routing.**

If the target bot's P95 latency exceeds 120% of its SLA, or its error rate crosses 10%, the system defers the handoff. Better to keep the conversation in the current bot than route to one that's struggling.

**The results:**

360+ tests cover the handoff system alone. Every edge case I could think of — and several I discovered in production — has a test.

The full system handles lead qualification, buyer matching, seller motivation scoring, and appointment booking. All through SMS, all automated, all with compliance checks (TCPA, FHA, Fair Housing) baked into the response pipeline.

Code is live: github.com/ChunkyTortoise

**How do you handle the "confident but wrong" problem in your chatbots?**

#Chatbot #AIAgents #ConversationalAI #NLP #Python

---

## Engagement Strategy

**CTA**: Technical question targeting chatbot builders
**Expected Replies**: 50-70 (niche but deeply engaged audience, multi-agent architecture is trending)
**Response Time**: <1 hour for all comments

**Prepared Responses**:

**Q: "Why three separate bots instead of one bot with multiple skills?"**
A: Separation of concerns. Each bot has its own qualification flow, scoring model, and conversation state. A unified bot would need to juggle three different workflows simultaneously, making it harder to test, debug, and iterate independently. With separate bots, I can deploy a new Seller Bot without touching Buyer or Lead. Each bot has focused tests — I can run the Seller Bot test suite in isolation and know exactly what changed. The handoff service is the coordination layer, and it has its own dedicated test suite.

**Q: "How do you preserve conversation context during handoffs?"**
A: The handoff service stores the full conversation history, current qualification scores, and any extracted data (budget, timeline, property details). When the target bot picks up, it has everything the source bot learned. The user doesn't have to repeat themselves. This is critical for SMS where users are already terse — asking them to re-state their budget after a handoff is a guaranteed drop-off.

**Q: "What happens when all three bots can't handle the conversation?"**
A: Human escalation. If the confidence score for all three bots is below threshold, or if the conversation repair system exhausts its strategies, the system tags the contact with "Human-Escalation-Needed" and triggers a notification workflow. The human agent gets the full conversation history and all qualification data collected so far. About 12% of conversations end up in human escalation — the goal isn't zero, it's routing the right conversations to humans.

**Q: "How do you test handoff logic without a real conversation?"**
A: Deterministic test fixtures. I have conversation histories that trigger every handoff path — Lead to Buyer, Lead to Seller, circular attempts, rate limit hits, performance degradation scenarios. Each fixture is a JSON conversation history that gets fed through the handoff evaluator. 360+ tests means I can refactor the scoring logic and know within seconds if I broke a handoff path.

---

## Follow-Up Actions

- [ ] 8:30am PT: Publish post
- [ ] 8:35am: Comment on 5 conversational AI / chatbot architecture posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Send 5 connection requests to engaged commenters (target: conversational AI engineers, chatbot product managers)
- [ ] Track metrics: impressions, engagement rate, GitHub clicks
