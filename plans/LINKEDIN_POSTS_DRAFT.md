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
