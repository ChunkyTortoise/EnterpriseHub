# LinkedIn Post Drafts — February 2026

Guidelines from spec: 3-5 hashtags max, no AI-generated feel, 60% value / 30% insights / 10% self-promotion, reply to every comment within 1 hour.

---

## Post 1: The Problem-Solution (Token Cost Reduction)

**Best day to post**: Tuesday or Wednesday, 8-10am PT

```
Most teams waste 40%+ of their LLM token budget on every API call.

I know because I was doing the same thing -- 93K tokens per workflow, burning through credits like they were free.

Here's what changed it:

1. Three-tier caching (L1 in-memory, L2 Redis, L3 PostgreSQL). Most LLM calls are repetitive. If the same prompt hit the system twice, the second call cost zero tokens.

2. Context window optimization. Instead of dumping the full conversation history into every call, I built a sliding window that keeps only what the model actually needs. 2.3x more efficient context usage.

3. Multi-provider routing. Not every query needs Claude Opus. Simple classification tasks go to Haiku. Complex reasoning goes to Opus. The router decides in <50ms.

Result: 93K tokens down to 7.8K per workflow. 89% reduction.

The savings compound fast. At scale, this is the difference between a viable product and one that bleeds money.

What's your biggest LLM cost challenge? Curious what others are seeing.

#LLMOps #AIEngineering #TokenOptimization #Python #BuildInPublic
```

**Why this works**: Opens with a pain point most AI engineers relate to. Specific numbers build credibility. Ends with engagement question.

---

## Post 2: Behind-the-Scenes (Multi-Agent Chatbot Handoff)

**Best day to post**: Thursday, 8-10am PT

```
I just shipped a cross-bot handoff system for 3 AI chatbots that talk to each other.

Here's what the problem looked like:

A real estate platform needs 3 specialized bots -- one qualifies leads, one helps buyers, one advises sellers. A lead says "I want to buy a house" to the lead bot. That conversation needs to seamlessly transfer to the buyer bot with full context.

Sounds simple. It wasn't.

The hard parts:
- Circular handoffs. Bot A sends to Bot B, Bot B sends back to Bot A. Had to build a 30-minute window tracker to prevent loops.
- Rate limiting. One aggressive user triggered 14 handoffs in an hour. Now capped at 3/hr, 10/day per contact.
- Confidence thresholds. Too low = false handoffs. Too high = missed transfers. Landed on 0.7 after testing against 200+ conversation transcripts.
- Concurrent conflicts. Two bots trying to claim the same contact simultaneously. Built contact-level locking to prevent race conditions.

The system now handles handoffs with pattern learning -- it adjusts thresholds dynamically based on outcome history.

What's the hardest multi-agent coordination problem you've dealt with?

#MultiAgentAI #AIArchitecture #ChatbotDevelopment #Python #FastAPI
```

**Why this works**: Specific technical challenges show depth. Real numbers (0.7 threshold, 3/hr limit) signal production experience, not tutorial-level knowledge.

---

## Post 3: Hot Take (Build Your Own AI Infrastructure)

**Best day to post**: Monday, 9-11am PT

```
Unpopular opinion: Most teams should build their own LLM orchestration layer instead of using LangChain.

Here's why:

1. You'll understand your failure modes. When a chain breaks at 2am, "somewhere in LangChain's abstraction" isn't a useful error. With your own orchestration, the stack trace points to YOUR code.

2. You control the caching. LangChain's caching is generic. Your data has specific patterns. I built a 3-tier cache (memory, Redis, Postgres) tuned to my actual query distribution. Generic caching left 60% of savings on the table.

3. Token costs are YOUR problem. No framework will optimize your specific prompt patterns. I wrote a custom router that sends simple tasks to Haiku and complex reasoning to Opus. Saved 89% on tokens. No framework did that for me.

4. Abstractions hide costs. Every "convenient" wrapper adds latency. My orchestrator adds <200ms overhead. I've seen LangChain chains add 800ms+ of pure abstraction tax.

I'm not saying LangChain is bad. It's great for prototyping. But for production systems handling real traffic, you need to own the stack.

Built an AI system that handles real load? I'd love to hear how you approached orchestration.

#AIEngineering #LLMOps #SoftwareArchitecture #Python #TechLeadership
```

**Why this works**: Controversial positions drive engagement. Backed by specific evidence from personal experience. Balanced take (acknowledges LangChain's value) avoids being dismissive.

---

## Post 4: Technical Tutorial (A/B Testing AI Responses)

**Best day to post**: Wednesday, 8-10am PT

```
Here's something most AI chatbot teams skip: A/B testing their bot responses.

You A/B test landing pages. You A/B test email subject lines. But you ship the same prompt to every user and hope it works.

I built an A/B testing framework for AI chatbots. Here's how it works:

The setup:
- Each "experiment" defines variants (e.g., formal vs casual tone, short vs detailed responses)
- Users are assigned variants deterministically by hashing their contact ID -- same person always gets the same variant
- Every response is tagged with its experiment and variant

The measurement:
- Track conversion signals per variant (did the lead book a showing? did the seller request a CMA?)
- Run z-test for statistical significance -- no eyeballing, no "I think version B feels better"
- Minimum sample size enforced before declaring a winner

What we found:
- Shorter responses with one clear call-to-action outperformed detailed responses by 31% on lead-to-showing conversion
- Asking about timeline before budget increased qualification accuracy

The framework is ~200 lines of Python. No ML required. Just structured experimentation.

Are you A/B testing your AI outputs? If not, what's stopping you?

#PromptEngineering #ABTesting #AIProducts #ConversationalAI #DataDriven
```

**Why this works**: Actionable insight most teams haven't considered. Shows product thinking beyond just "build the bot." Specific results add credibility.

---

## Post 5: Project Showcase (Benchmarking LLM Providers)

**Best day to post**: Friday, 9-11am PT

```
I built a tool that benchmarks Claude vs GPT vs Gemini vs Perplexity in one command.

Why? Because every LLM provider claims they're the best, and none of them publish comparable benchmarks for YOUR use case.

AgentForge is a unified async interface. Same code, swap the provider:

  response = await agent.generate("Analyze this lead", provider="claude")
  response = await agent.generate("Analyze this lead", provider="gemini")

Then run: agentforge benchmark

You get a comparison table: latency (p50/p95/p99), token usage, cost per query, and response quality scores -- all on YOUR actual prompts.

What I learned benchmarking across 4 providers on real estate lead qualification:

- Claude: Best reasoning quality, highest cost
- Gemini: Fastest responses, occasionally misses nuance
- GPT: Most consistent, middle of the road on everything
- Perplexity: Surprisingly good for research-heavy queries

The right answer is almost never "use one provider for everything." Route based on task complexity and budget.

Tool is open source: github.com/ChunkyTortoise/ai-orchestrator

What provider mix are you running in production?

#LLM #AIEngineering #OpenSource #Claude #Python
```

**Why this works**: Practical tool that others can use. Real benchmark insights from production use. Links to open source repo for credibility. Drives traffic to GitHub.

---

## Posting Schedule (Week 1)

| Day | Post | Action After |
|-----|------|-------------|
| Mon | Post 3 (Hot Take) | Engage with comments, connect with commenters |
| Tue | Post 1 (Token Reduction) | Share in 2-3 relevant LinkedIn groups |
| Wed | -- | Comment on 5 AI/ML posts from others |
| Thu | Post 2 (Multi-Agent Handoff) | Tag @Anthropic in a comment about Claude usage |
| Fri | Post 5 (AgentForge Benchmark) | Pin to Featured section |

**Week 2**: Posts 4 (A/B Testing) + 2 new drafts based on engagement data from Week 1.

---

## Notes
- Edit these in your own voice before posting -- LinkedIn suppresses content that reads like AI-generated text
- Add a personal photo or architecture diagram to Posts 2 and 4 for higher engagement
- Reply to EVERY comment within 1 hour of posting
- After posting, immediately comment on 3-5 other posts in your feed to boost algorithmic reach

---

## Week 2 Posts

### Post 6: Case Study / Results

**Theme**: Cross-bot handoff system with measurable safeguards

**Best day/time**: Tuesday, February 10, 8:30am PT

```
3 chatbots. 1 contact. Zero dropped conversations.

Last month I shipped a cross-bot handoff system for a real estate AI platform where 3 specialized chatbots (lead qualification, buyer, seller) need to pass contacts between each other mid-conversation.

Sounds simple until you hit the edge cases:

- Contact bounces lead -> buyer -> lead in an infinite loop
- Two bots try to claim the same contact simultaneously
- A bad intent signal fires 6 handoffs in an hour

Here's what I built to stop all of that:

1. Circular prevention — same source-to-target pair blocked within a 30-min window
2. Rate limiting — 3 handoffs/hr, 10/day per contact (hard caps)
3. Contact-level locking — prevents concurrent handoff collisions
4. Pattern learning — threshold adjusts dynamically after 10+ outcome data points

The confidence threshold is 0.7 for most routes, but buyer-to-seller requires 0.8 (higher stakes) and seller-to-buyer only needs 0.6 (lower friction).

Before these safeguards: handoff loops were our #1 support complaint.
After: zero circular handoffs in production. Rate limit blocks caught 12 false-positive intent signals in the first week alone.

The lesson: the hard part of multi-agent AI isn't making the bots smart. It's making the transitions between them reliable.

What's the gnarliest edge case you've hit in a multi-agent system?

#MultiAgentAI #AIEngineering #Chatbots #Python #LLMOps
```

**Why it works**: Continues the multi-agent thread from Week 1 Post 2, but goes deeper with specific numbers (0.7 threshold, 30-min window, 3/hr limit). The before/after framing makes the outcome concrete, and the edge case details signal real production experience.

**Engagement hook**: "What's the gnarliest edge case you've hit in a multi-agent system?" -- invites war stories from engineers, which generates long comments that boost algorithmic reach.

---

### Post 7: Industry Insight / Trend

**Theme**: The real bottleneck in production AI is not model quality

**Best day/time**: Wednesday, February 11, 9:00am PT

```
Hot take from someone running 3 LLM providers in production:

The model is never the bottleneck. The plumbing is.

I maintain a platform that routes requests across Claude, Gemini, and Perplexity depending on task complexity. The actual LLM call takes 1-3 seconds. Everything else — caching, parsing, fallback logic, error handling — that's where 80% of the engineering time goes.

Here's what I mean:

Response parsing alone has multiple strategies because LLMs don't return structured data consistently. One model wraps JSON in markdown code fences. Another adds a preamble. A third sometimes returns valid JSON, sometimes doesn't.

Then there's the cache layer. We run L1 (in-memory), L2 (Redis), and L3 (persistent) caching because a single missed cache hit on a repeated query costs $0.003-0.01. Multiply that by 10,000 daily requests and you're burning $30-100/day on questions you already answered.

And SLA compliance? We track P50, P95, and P99 latency per bot, per operation type, with rolling 1h/24h/7d windows. Not because we want dashboards. Because when a seller bot's P95 crosses 2500ms, something upstream broke and we need to know in minutes, not days.

Everyone's debating which model is best.

Meanwhile, the engineers actually shipping AI products are spending their days writing cache invalidation logic and retry policies.

The model is a solved problem. The infrastructure around it is not.

What's the most underrated part of your AI stack?

#AIEngineering #LLMOps #ProductionAI #SoftwareEngineering
```

**Why it works**: This is a builder's observation, not a pundit's prediction. The specific details (L1/L2/L3 cache tiers, P50/P95/P99 tracking, $0.003-0.01 per missed cache hit) are too granular to fake and signal genuine production experience.

**Engagement hook**: "What's the most underrated part of your AI stack?" -- low-friction question that lets infrastructure engineers share their own overlooked work.

---

### Post 8: Tool/Framework Review

**Theme**: Honest review of Ruff after migrating from black + isort + flake8

**Best day/time**: Thursday, February 12, 8:30am PT

```
I replaced 3 Python tools with 1 and my CI pipeline got 10x faster.

The tools I dropped: black, isort, flake8.
The replacement: Ruff.

I've now migrated 7 repositories to Ruff (totaling 800+ Python files) and here's my honest take after 3 months.

What's great:
- Speed. Ruff lints my entire monorepo in under 2 seconds. The old stack took 20-30 seconds. In CI, that compounds fast across matrix builds.
- One config block. Instead of [tool.black], [tool.isort], [tool.flake8] scattered across pyproject.toml, it's just [tool.ruff] and [tool.ruff.lint]. Select the rule codes you want, done.
- Auto-fix. Ruff can fix most import sorting and unused import issues on save. I have it wired as a post-tool hook in my editor — every file save auto-formats.

What's not perfect:
- Rule parity isn't 100%. A few flake8 plugins I relied on (like flake8-bugbear's B950 line length) don't have exact equivalents. You adapt.
- The error messages are sometimes less descriptive than flake8's. When a rule fires that you haven't seen before, you're reading docs more often.
- If your team has muscle memory around black's opinionated formatting, Ruff's formatter makes slightly different choices in edge cases. Minor, but it can cause noisy diffs during migration.

Bottom line: I'd never go back. The speed alone justifies the switch, and consolidating 3 config sections into 1 removes a real source of drift.

If you're still running black + isort + flake8 separately, try `ruff check . --fix` on your repo. You'll feel the difference immediately.

Have you switched to Ruff yet? What held you back (or convinced you)?

#Python #DevTools #Ruff #DeveloperExperience #CodeQuality
```

**Why it works**: Tool reviews with honest pros AND cons outperform pure hype posts. The specific migration scope (7 repos, 800+ files) and concrete before/after (20-30s vs 2s) make this credible.

**Engagement hook**: "Have you switched to Ruff yet? What held you back (or convinced you)?" -- binary question with follow-up that invites explanation.

---

### Week 2 Posting Schedule

| Post | Day | Time (PT) | Theme | Content Type |
|------|-----|-----------|-------|-------------|
| 6 | Tue Feb 10 | 8:30am | Cross-bot handoff safeguards | Case Study |
| 7 | Wed Feb 11 | 9:00am | Model isn't the bottleneck, plumbing is | Industry Insight |
| 8 | Thu Feb 12 | 8:30am | Ruff replaces black+isort+flake8 | Tool Review |

### Week 2 Strategy Notes

- **Callback to Week 1**: Post 6 builds on the handoff topic from Post 2, and Post 7 references the caching strategy from Post 1. This creates continuity for repeat viewers.
- **Engagement targets**: Reply to every comment within 1 hour. For Post 8 especially, expect "what about X?" questions from flake8 plugin users.
- **Cross-promotion**: If Post 7 gains traction, reshare Post 1 (token cost reduction) in a comment as supporting evidence.
- **Comment seeding**: After posting, immediately comment on 3-5 related posts from others in the AI/Python space.
