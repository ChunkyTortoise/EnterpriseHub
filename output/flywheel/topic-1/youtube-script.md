# YouTube Script: How I Cut LLM Costs by 89%

**Topic**: LLM Cost Optimization with 3-Tier Caching
**Format**: 5-8 minute video script with timestamps
**Target**: AI engineers, ML practitioners, startup founders
**Style**: Screen recording with code walkthrough + talking head segments

---

## Video Title Options

- "How I Cut My LLM Costs by 89% (3-Tier Caching Architecture)"
- "$12K to $1.3K/Month: The Caching Strategy Every AI Engineer Needs"
- "Stop Overpaying for LLM APIs: 3-Tier Cache Architecture Tutorial"

## Thumbnail Text

"89% COST CUT" with a downward arrow and dollar signs. Before/After split: $12K | $1.3K

---

## Script

### [0:00 - 0:30] Hook

"Our AI platform was burning $12,000 a month on Claude API calls. We had three chatbots qualifying real estate leads, and every single conversation turn was hitting the API -- scoring, intent analysis, response generation, memory retrieval. Seven thousand tokens per interaction, six thousand interactions per day.

In 30 days, we cut that to $1,300. Same features. Same quality. Actually better conversion rates.

The fix wasn't switching models, fine-tuning, or prompt engineering. It was caching. Let me show you exactly how."

### [0:30 - 1:30] The Problem (Screen: Cost Dashboard)

"Here's the breakdown of where the money was going.

[Show diagram of the 4 API calls per interaction]

Every message from a lead triggers four API calls:
- Lead scoring: 2,000 tokens
- Intent classification: 1,500 tokens
- Response generation: 3,000 tokens
- Memory retrieval: 1,000 tokens

That's 7,500 tokens per interaction. Multiply by 5,000 daily interactions, and you're looking at 37.5 million tokens per day. At Claude's pricing, that's $400 a day, $12K a month.

And here's the problem -- it scales linearly. Double the leads, double the cost. There's no economy of scale."

### [1:30 - 2:30] The Insight (Screen: Query Log Analysis)

"Before I started building anything, I did something simple -- I logged every single memory query for a week. Ten thousand queries.

[Show the bar chart]

74% of queries referenced the last 10 messages. Another 14% referenced the last 100 messages. Only 12% needed a full semantic search of the conversation history.

The pattern was obvious: users ask 'what did you just say?' They rarely ask 'what have we discussed over three weeks?'

This meant 90% of our expensive API calls were answering questions we already knew the answer to. That's a caching problem."

### [2:30 - 4:30] The Architecture (Screen: Code Walkthrough)

"So we built a 3-tier cache. Let me walk you through each layer.

[Show architecture diagram]

**L1: In-Process Cache.** This is the simplest layer. Each FastAPI worker keeps the last 10 messages per user in an OrderedDict with LRU eviction. TTL is 5 minutes. Retrieval time: under 1 millisecond. This catches 74% of all queries.

[Show L1 code]

**L2: Redis Shared Cache.** This is the most important layer. It's shared across all worker processes, so when Worker A scores a lead, Workers B and C can use that result. We store the last 100 messages per user with a 15-minute TTL. Retrieval time: under 5 milliseconds. Catches another 14%.

[Show L2 code]

**L3: Postgres with pgvector.** The fallback layer for the 12% of queries that need semantic search. When a message comes in that doesn't match any exact cache key, we generate an embedding and search for similar queries with cosine similarity above 0.92.

[Show L3 code]

This is what catches 'What's my home worth?' matching to 'Can you give me a home valuation?' -- different words, same intent, same scoring outcome.

The magic is in the unified interface. Check L1, miss? Check L2, miss? Fall through to L3. And on every L3 hit, we backfill L2 and L1 so the same query pattern won't hit the database again."

### [4:30 - 5:30] Results (Screen: Metrics Dashboard)

"Here are the production numbers after 30 days.

[Show results table]

- Monthly cost: $12,000 down to $1,300. That's 89%.
- Cost per lead: $24 down to $2.60.
- P95 latency: 180ms down to 4.8ms. That's a 97% improvement.
- Overall cache hit rate: 88%.

And here's the surprising one -- lead conversion improved by 7%. We went from 4.2% to 4.5%.

Why? Because sub-200ms SMS response times feel instant. At 1.2 seconds, there's a perceptible delay that tells the user 'you're talking to a bot.' That 1-second difference mattered more than any prompt engineering we'd done."

### [5:30 - 6:30] Lessons Learned (Talking Head)

"Three things I wish someone had told me before I built this.

Number one: Start with Redis, not in-memory. L1 was easy to build but only matters in single-worker deployments. L2 -- Redis -- delivered 80% of the value because it's shared across workers. If you can only build one tier, build L2.

Number two: Monitor cache freshness, not just hit rates. We had a 95% hit rate in week one and celebrated. Then we found stale cached scores that were miscategorizing leads. A high hit rate is worthless if the data is wrong.

Number three: Cache components, not full responses. Instead of caching the entire API response, we cache individual scoring components -- Financial Readiness Score, Psychological Commitment Score, intent signals. This lets us recompose results without full recomputation and pushed our hit rate from 75% to 89%."

### [6:30 - 7:00] When NOT to Do This (Talking Head)

"Quick reality check. You probably don't need this if:
- You have fewer than 100 queries per day. Just send full history.
- Your conversations are short, under 20 messages. The overhead is negligible.
- You have a generous budget and the complexity isn't worth the savings.

This architecture makes sense when you have thousands of conversations per day, long message threads, and you're cost-sensitive."

### [7:00 - 7:30] CTA

"The full implementation is open source. Link in the description to the GitHub repo. You can clone it, run docker compose up, and run the benchmark suite to see the cache hit rates yourself.

If you found this useful, hit subscribe -- I'm doing a series on production AI architectures. Next video: how we built the 3-bot handoff system that routes leads between specialized agents without losing context.

Thanks for watching."

---

## Description

How I reduced LLM API costs by 89% ($12K -> $1.3K/month) with a 3-tier caching architecture (in-process / Redis / Postgres+pgvector).

Full source code: https://github.com/ChunkyTortoise/EnterpriseHub

Timestamps:
0:00 - The $12K/month problem
0:30 - Breaking down token costs
1:30 - Analyzing query patterns
2:30 - 3-tier cache architecture
4:30 - Production results
5:30 - Lessons learned
6:30 - When NOT to cache
7:00 - Open source code

#AIEngineering #LLMOps #Python #Redis #CostOptimization

---

## Tags

LLM cost optimization, AI cost reduction, 3-tier caching, Redis caching, pgvector, Python, AI engineering, Claude API, production AI, agent memory, semantic caching
