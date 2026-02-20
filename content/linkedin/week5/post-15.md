# LinkedIn Post #15 — One Month of Building in Public

**Publish Date**: Friday, March 14, 2026 @ 8:30am PT
**Topic**: Engagement / Recap — Reflection Post
**Goal**: Celebrate one month milestone, recap top-performing content, build community loyalty, preview upcoming launches, drive engagement through gratitude and forward momentum

---

## Post Content

One month of building in public. Here's what worked, what didn't, and what I'm building next.

On February 9, I published my first LinkedIn post. "I built 11 production repos with 8,500+ tests. Here's what I learned about shipping AI systems that actually work."

I had no audience. No strategy beyond "share what I know and see what happens."

Four weeks and 15 posts later, here's the honest recap.

**What worked:**

**1. Technical depth beats surface-level takes.**

My highest-engagement posts weren't the ones with the broadest appeal. They were the ones that went deep on a specific problem.

The 3-bot handoff system post — 0.7 confidence thresholds, circular prevention, rate limiting — resonated because it solved a real problem that conversational AI engineers actually face. Generic "AI is changing everything" posts get scrolled past. "Here's exactly how I prevent handoff loops with a 30-minute window block" gets saved and shared.

**2. Contrarian takes spark conversation.**

"Stop building AI agents" was a deliberate provocation. In March 2026, when every company is shipping autonomous agents, arguing for more constraints felt risky. But the post hit because it gave people permission to question the hype. The engineers who agreed shared it. The engineers who disagreed commented. Both drove engagement.

**3. Numbers create credibility.**

Every post that performed well had specific numbers:
- 89% LLM cost reduction
- 88% cache hit rate
- P99 0.095ms dispatch latency
- 4.3M tool dispatches per second
- 360+ tests on the handoff system
- 5 CRM integrations

"I built a fast system" is forgettable. "P99 0.095ms" is memorable. Specificity signals that you actually measured it, not that you're guessing.

**What didn't work:**

**1. Posting without a clear hook.**

My weakest posts were the ones that started with context instead of a claim. "I've been working on CRM integrations..." loses people in the first line. "Five CRM integrations. One abstract base class. Zero rewrites." stops the scroll.

I learned to write the hook first, then build the post around it.

**2. Underestimating comment responses.**

Early on, I'd reply to comments with one-liners. Waste of an opportunity. Thoughtful replies that add new information turn one engagement into a thread. Threads signal value to the algorithm. The posts where I wrote detailed replies outperformed the ones where I didn't.

**The numbers after one month:**

- 15 posts published (Mon/Wed/Fri cadence, never missed)
- 11 repos referenced, all open source
- 8,500+ tests across the portfolio
- 3 Fiverr gigs live (RAG $300-$1,200, Chatbot $400-$1,500, Dashboard $200-$800)
- All CI pipelines green

**What I learned about LinkedIn as a technical creator:**

This platform rewards specificity. It rewards consistency. And it rewards people who share real work instead of opinions about other people's work.

Every post I wrote was backed by code I could link to. Every metric I cited was from a benchmark I could reproduce. That's not a content strategy — it's just how engineers should communicate. Show the work.

**What's next:**

**AgentForge launch.** My open-source AI agent framework is ready for its public launch. 4.3M dispatches/sec, async-first architecture, built-in observability. I've been teasing the architecture — now it's time to ship the full release with documentation, quickstart guides, and benchmark reproducibility scripts.

**Deeper technical series.** The posts that worked best went deep. So I'm going deeper. Upcoming series on production RAG patterns, LLM cost optimization playbooks, and real-world agent architecture case studies.

**Community building.** The best part of this month wasn't the impressions or the engagement rate. It was connecting with engineers who are solving the same problems. If you've been following along, thank you. If you've commented, shared, or sent a DM — you've shaped what I write next.

GitHub: github.com/ChunkyTortoise | Portfolio: chunkytortoise.github.io
Live demo: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

**What topic should I cover next? AI costs, RAG patterns, or agent architecture?**

#BuildInPublic #AIEngineering #ContentCreation #TechCommunity #OpenSource

---

## Engagement Strategy

**CTA**: Multiple-choice question to drive easy engagement
**Expected Replies**: 70-100 (recap posts drive loyalty engagement, the question format lowers the barrier to commenting)
**Response Time**: <1 hour for all comments

**Prepared Responses**:

**Q: "AI costs — how do you actually achieve 89% cost reduction?"**
A: Great pick. The short version: 3-tier caching. L1 (in-memory) catches repeated queries within a session — that's your cheapest win. L2 (Redis) catches repeated queries across users — this is where the big savings come from because many users ask similar questions. L3 (persistent) catches repeated queries across deployments — model updates don't invalidate your cache. The 89% reduction comes from an 88% cache hit rate on L2. I'll do a full deep-dive post on the architecture with actual cost comparisons.

**Q: "RAG patterns — what's the biggest mistake people make?"**
A: Pure semantic search. Everyone starts with embeddings because the tutorials use embeddings. But embeddings find "similar" documents, not "relevant" documents. When a user asks about "Section 4.2 of the compliance policy," semantic search returns sections that talk about compliance in general. BM25 keyword search finds Section 4.2. Hybrid retrieval with reciprocal rank fusion gives you both. That's always my starting point for production RAG.

**Q: "Agent architecture — how do you handle multi-agent coordination at scale?"**
A: The key insight from my 3-bot system: coordination is a service, not a feature of the agents. Each bot is independent — it handles its own conversation flow, scoring, and responses. The handoff service is a separate layer that evaluates when to route between bots. This separation means I can deploy, test, and iterate on each bot independently. The coordination layer has its own test suite (360+ tests) and its own monitoring. When something breaks, I know immediately whether it's a bot problem or a routing problem.

**Q: "How do you stay consistent with 3 posts a week?"**
A: Two things. First, I write from work I've already done. Every post references code I've already built and metrics I've already measured. I'm not creating content — I'm documenting engineering. That removes writer's block because the material already exists. Second, I batch-write. Sunday evening I draft all three posts for the week. Monday, Wednesday, Friday I publish and focus on engagement. The writing and the publishing are separate workflows.

---

## Follow-Up Actions

- [ ] 8:30am PT: Publish post
- [ ] 8:35am: Comment on 5 build-in-public / tech content creator posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Send 5 connection requests to engaged commenters (target: technical content creators, AI engineers, community builders)
- [ ] Track metrics: impressions, engagement rate, profile views, GitHub clicks, follower growth
- [ ] Weekend: Compile full Month 1 analytics report, plan Week 5+ strategy
- [ ] Begin AgentForge launch content preparation
