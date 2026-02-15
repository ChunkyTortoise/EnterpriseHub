# LinkedIn Content Calendar: February 17 — March 14, 2026

**Cadence**: 3 posts/week (Mon, Wed, Fri) + daily engagement
**Goal**: Establish authority in AI/ML engineering, drive inbound leads, build network
**Tone**: Technical but accessible, results-focused, no hype

---

## Week 1: February 17-21

### Monday, Feb 17 — Portfolio Showcase
**Type**: Carousel / long-form post
**Topic**: "I built 11 production repos with 8,500+ tests. Here's what I learned about shipping AI systems that actually work."
**Content Angles**:
- Why test counts matter more than demo videos
- The gap between "it works on my laptop" and production RAG
- 3 patterns that saved every project: hybrid retrieval, confidence gating, 3-tier caching
**CTA**: "What's the hardest part of getting your AI system to production? Drop a comment."
**Hashtags**: #AIEngineering #RAG #ProductionAI #Python #SoftwareEngineering

### Wednesday, Feb 19 — Industry Insight
**Type**: Text post with single stat
**Topic**: "89% LLM cost reduction isn't magic — it's caching done right."
**Content Angles**:
- L1 (in-memory) catches repeated queries within a session
- L2 (Redis) catches repeated queries across users
- L3 (persistent) catches repeated queries across deployments
- Most teams skip L2 and L3, paying full price for every call
**CTA**: "Are you caching your LLM calls? What's your hit rate?"
**Hashtags**: #LLM #CostOptimization #Redis #AIInfrastructure

### Friday, Feb 21 — Case Study Snippet
**Type**: Before/after post
**Topic**: "Before: Pure semantic search returned 'similar' but wrong chunks. After: Hybrid BM25 + dense retrieval with RRF."
**Content Angles**:
- The precision vs. similarity problem in RAG
- Why keyword search still matters in 2026
- Reciprocal rank fusion as the practical middle ground
- Measurable improvement: precision@k gains from docqa-engine
**CTA**: "Anyone else found that pure embeddings aren't enough for production RAG?"
**Hashtags**: #RAG #InformationRetrieval #NLP #MachineLearning

---

## Week 2: February 24-28

### Monday, Feb 24 — Portfolio Showcase
**Type**: Long-form post
**Topic**: "I wrote 33 Architecture Decision Records across 10 repos. Here's why ADRs are the most underrated engineering practice."
**Content Angles**:
- ADRs capture the *why*, not just the *what*
- 6 months from now, you won't remember why you chose FAISS over Pinecone
- Template: Context, Decision, Consequences, Alternatives Considered
- Real example: choosing BM25 + dense hybrid over pure semantic search
**CTA**: "Does your team write ADRs? What format do you use?"
**Hashtags**: #SoftwareArchitecture #EngineeringPractices #Documentation #TechLeadership

### Wednesday, Feb 26 — Industry Insight
**Type**: Text post
**Topic**: "The real cost of AI isn't the API calls — it's the re-work when your 'quick prototype' becomes production."
**Content Angles**:
- Prototypes that skip tests cost 3-5x more to fix later
- Docker from day 1 saves weeks of "works on my machine" debugging
- CI/CD isn't overhead — it's insurance against shipping broken code
- The best time to add tests is before the first deployment
**CTA**: "What's the most expensive shortcut you've seen in AI projects?"
**Hashtags**: #AIEngineering #TechnicalDebt #DevOps #SoftwareQuality

### Friday, Feb 28 — Engagement Question
**Type**: Poll or question post
**Topic**: "For RAG systems in production: what's your biggest bottleneck?"
**Options** (if poll):
- Retrieval quality (wrong chunks)
- Latency (too slow)
- Cost (too expensive)
- Evaluation (can't measure quality)
**Follow-up**: Share relevant experience for whichever option wins
**Hashtags**: #RAG #AIEngineering #Poll #MachineLearning

---

## Week 3: March 3-7

### Monday, Mar 3 — Portfolio Showcase
**Type**: Technical walkthrough
**Topic**: "How I built a 3-bot handoff system that knows when to escalate vs. when to answer."
**Content Angles**:
- The confidence threshold problem: too low = wrong answers, too high = unnecessary escalations
- Pattern learning from outcome history (min 10 data points before adjusting)
- Circular prevention and rate limiting to stop handoff loops
- Real metrics from jorge_real_estate_bots (360+ tests)
**CTA**: "How do you handle the 'confident but wrong' problem in your chatbots?"
**Hashtags**: #Chatbot #AIAgents #ConversationalAI #NLP

### Wednesday, Mar 5 — Industry Insight
**Type**: Contrarian take
**Topic**: "Stop building AI agents. Start building AI systems with clear boundaries."
**Content Angles**:
- "Autonomous agents" sound impressive but are hard to debug, test, and trust
- Explicit confidence thresholds > implicit "the model will figure it out"
- JSON-only outputs with enum-based routing > free-form text parsing
- The most reliable AI systems I've built are the ones with the most constraints
**CTA**: "Agree or disagree? Where do you draw the line between autonomy and control?"
**Hashtags**: #AIAgents #SystemDesign #AIEngineering #LLM

### Friday, Mar 7 — Case Study Snippet
**Type**: Results post
**Topic**: "4.3M tool dispatches per second. Here's how AgentForge's async architecture handles scale."
**Content Angles**:
- Async-first design with httpx and asyncio
- Provider abstraction so switching models is a config change
- Built-in observability: every dispatch is tracked, measured, alertable
- Why benchmarks in every repo keep you honest about performance
**CTA**: "What's your approach to benchmarking AI systems? Synthetic tests or production metrics?"
**Hashtags**: #Performance #AsyncPython #AIInfrastructure #Benchmarking

---

## Week 4: March 10-14

### Monday, Mar 10 — Portfolio Showcase
**Type**: Lessons learned post
**Topic**: "Lessons from building 5 CRM integrations: GoHighLevel, HubSpot, Salesforce, and the pattern that made them all easy."
**Content Angles**:
- Abstract Base Class CRM protocol — implement once, integrate anywhere
- Rate limiting per provider (10 req/s for GHL, different for others)
- Real-time sync vs. batch sync tradeoffs
- Why I test CRM adapters with 80%+ coverage (APIs change without warning)
**CTA**: "What's the most painful CRM integration you've dealt with?"
**Hashtags**: #CRM #APIIntegration #Python #SoftwareArchitecture

### Wednesday, Mar 12 — Industry Insight
**Type**: Data-backed post
**Topic**: "Fiverr RAG projects go for $300-$1,200. Upwork custom RAG is $100-$300/hr. The market is telling you something about AI engineering value."
**Content Angles**:
- AI engineering is still undersupplied relative to demand
- Production RAG (not tutorial RAG) commands premium rates
- The differentiator: tests, benchmarks, and documented architecture
- Why "I have a working demo" beats "I read the documentation"
**CTA**: "Are you pricing your AI skills based on market rate or imposter syndrome?"
**Hashtags**: #Freelancing #AIEngineering #CareerGrowth #TechCareers

### Friday, Mar 14 — Engagement / Recap
**Type**: Reflection post
**Topic**: "One month of building in public. Here's what worked, what didn't, and what I'm building next."
**Content Angles**:
- Recap top-performing posts and why they resonated
- What I learned about LinkedIn engagement as a technical creator
- Preview of upcoming projects or launches
- Thank the community for engagement and feedback
**CTA**: "What topic should I cover next? AI costs, RAG patterns, or agent architecture?"
**Hashtags**: #BuildInPublic #AIEngineering #ContentCreation #TechCommunity

---

## Daily Engagement Targets

| Activity | Target | Time |
|----------|--------|------|
| Comment on AI/ML posts | 5-7 thoughtful comments | 15 min |
| React to network posts | 10-15 reactions | 5 min |
| Connection requests (targeted) | 3-5 per day | 5 min |
| Reply to comments on own posts | All, within 4 hours | 5 min |
| **Total daily time** | | **~30 min** |

### Engagement Guidelines

- **Comments should add value**: Share a specific experience, ask a follow-up question, or respectfully disagree with reasoning
- **Target audience for connections**: AI/ML engineers, startup CTOs, tech leads at companies hiring for AI roles, RAG/LLM practitioners
- **Avoid**: Generic "Great post!" comments, mass connection requests without personalization, engagement pods
- **Reply strategy**: Always reply to comments on your posts within 4 hours — LinkedIn's algorithm rewards active threads

### Content Repurposing

| LinkedIn Post | Repurpose To |
|--------------|-------------|
| Week 1 Mon (8,500 tests) | Dev.to article (expanded) |
| Week 2 Wed (prototype to production) | Twitter/X thread |
| Week 3 Wed (agents vs. systems) | Hacker News discussion |
| Week 4 Wed (market rates) | Reddit r/ExperiencedDevs |

---

## Metrics to Track

| Metric | Week 1 Target | Month 1 Target |
|--------|--------------|----------------|
| Post impressions | 500+ per post | 1,000+ per post |
| Engagement rate | 3-5% | 5-8% |
| Profile views | 50+ per week | 100+ per week |
| Connection requests received | 5+ per week | 15+ per week |
| DMs / inbound inquiries | 1-2 | 5-10 |
| New connections (net) | 20+ | 80+ |
