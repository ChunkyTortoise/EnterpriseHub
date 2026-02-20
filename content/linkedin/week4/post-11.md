# LinkedIn Post #11 — Stop Building AI Agents

**Publish Date**: Wednesday, March 5, 2026 @ 9:00am PT
**Topic**: Industry Insight — Contrarian Take
**Goal**: Spark debate, position as pragmatic engineer against hype cycle, drive high engagement through disagreement, repurpose to Hacker News

---

## Post Content

Stop building AI agents. Start building AI systems with clear boundaries.

I know this is an unpopular opinion in March 2026. Everyone is shipping "autonomous agents" that can "reason" and "plan" and "execute." The demos look incredible.

Then you try to debug one in production.

**I've built 11 AI repositories with 8,500+ automated tests. The most reliable systems I've shipped are the ones with the most constraints.**

Here's what I mean:

**"The model will figure it out" is not an architecture.**

I've seen teams ship agents that parse free-form text responses to decide what to do next. The model outputs "I think we should transfer this to the buyer team," and a regex tries to extract the intent.

My approach: JSON-only outputs with enum-based routing. The model returns `{"intent": "HANDOFF_BUYER", "confidence": 0.85}`, and a deterministic router handles the rest.

No regex. No "I think." No ambiguity.

**Explicit confidence thresholds beat implicit trust.**

My 3-bot handoff system uses a 0.7 confidence threshold. Below that, the conversation stays with the current bot. Above it, the handoff executes.

That number isn't arbitrary. It comes from pattern learning across real conversations — the system tracks outcomes and adjusts thresholds after 10+ data points.

Compare that to "let the agent decide when to hand off." How do you test that? How do you debug a bad handoff when the agent's reasoning is a 2,000-token chain-of-thought you can't reproduce?

**Constraints make systems testable.**

My handoff service has 360+ tests. I can write those tests because the system has clear inputs and outputs. Contact sends message, system evaluates confidence, system routes to bot or stays.

Try writing 360 tests for an autonomous agent that "reasons about the best course of action." You can't. The outputs are non-deterministic. The reasoning paths are infinite. You end up testing vibes instead of behavior.

**The best AI systems I've built look boring.**

- Rate limiting: 3 handoffs per hour, 10 per day
- Circular prevention: same route blocked within 30 minutes
- Performance gates: defer handoffs when target bot is degraded
- Compliance checks: TCPA, FHA, Fair Housing on every response

None of that is sexy. All of it is what keeps the system running at 2am when nobody is watching.

**I'm not saying AI can't be autonomous. I'm saying autonomy should be earned, not assumed.**

Start with constraints. Prove each constraint is unnecessary with data. Then — and only then — loosen it.

The alternative is shipping an "autonomous agent" and spending the next 6 months adding the constraints you should have started with.

Live demo of what constrained AI looks like in production: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

**Agree or disagree? Where do you draw the line between autonomy and control?**

#AIAgents #SystemDesign #AIEngineering #LLM #SoftwareArchitecture

---

## Engagement Strategy

**CTA**: Polarizing agree/disagree question to maximize comment depth
**Expected Replies**: 80-120 (contrarian takes drive high engagement, AI agents topic is polarizing in 2026)
**Response Time**: <30 minutes for first 2 hours, <1 hour after
**Repurpose**: Hacker News discussion (per content calendar)

**Prepared Responses**:

**Q: "This is a straw man. Good agent frameworks have guardrails built in."**
A: Fair point, and frameworks are getting better. But there's a difference between guardrails the framework provides and constraints you design into your system architecture. Framework guardrails handle generic safety (content filtering, token limits). Domain-specific constraints — like "never hand off a seller lead to the buyer bot twice in 30 minutes" — are architecture decisions that no framework can make for you. My argument is that most teams rely too heavily on framework guardrails and not enough on domain-specific constraints.

**Q: "Aren't you just describing good software engineering? This isn't specific to AI."**
A: Exactly. That's my entire point. The AI agent hype has convinced people that AI systems need different engineering principles. They don't. Clear interfaces, deterministic routing, explicit error handling, comprehensive tests — these aren't constraints that hold AI back. They're what make AI systems production-ready. The fact that this take is "contrarian" in 2026 tells you how far the hype has drifted from good engineering.

**Q: "But LLMs are non-deterministic by nature. You can't fully constrain them."**
A: You can't constrain the generation, but you can constrain the decision layer around it. The LLM generates a response — that's non-deterministic. But the routing decision (which bot handles this?), the confidence evaluation (is this score above threshold?), and the safety checks (does this response violate compliance?) are all deterministic. I use AI for what it's good at (natural language understanding) and deterministic code for what it's good at (reliable decision-making).

**Q: "What about complex tasks that genuinely need multi-step reasoning?"**
A: Break them into constrained steps. My lead qualification is a multi-step process: detect intent, evaluate confidence, route to specialist bot, qualify, score, book appointment. Each step has clear inputs, outputs, and tests. The "reasoning" happens within each step, but the orchestration between steps is deterministic. You get the benefit of AI understanding without the risk of AI deciding.

---

## Follow-Up Actions

- [ ] 9:00am PT: Publish post
- [ ] 9:05am: Comment on 5 AI agent / LLM engineering posts (preferably pro-agent posts for respectful counterpoint visibility)
- [ ] Throughout day: Reply to all comments within 30 minutes for first 2 hours, then within 1 hour
- [ ] Prepare Hacker News version (shorter, more technical, remove self-promotion)
- [ ] Send 5 connection requests to engaged commenters (target: AI engineers, system architects, CTOs)
- [ ] Track metrics: impressions, engagement rate, comment depth, share count (contrarian posts get shared more)
