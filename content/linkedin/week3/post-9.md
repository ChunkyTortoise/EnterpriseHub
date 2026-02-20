# LinkedIn Post #9 — RAG Bottleneck Poll

**Publish Date**: Friday, February 28, 2026 @ 8:30am PT
**Topic**: Engagement Question — RAG Systems in Production
**Goal**: Drive high engagement through poll format, gather market intelligence, position as RAG expert with follow-up value

---

## Post Content

For RAG systems in production: what's your biggest bottleneck?

I've been building retrieval-augmented generation pipelines for the past year. 11 repos. 8,500+ tests. 3 Streamlit apps in production.

And the question I keep coming back to is: where does it actually break?

Not in demos. Not in notebooks. In production, with real users, at scale.

Here's what I've hit across my projects:

**Retrieval quality (wrong chunks)**
Pure semantic search sounds great until your user searches "FHA loan limits 2026" and gets back chunks about "VA loan benefits." Semantically similar. Factually useless. I switched to hybrid BM25 + dense retrieval with Reciprocal Rank Fusion. Precision@5 improved 34%. But it added index maintenance overhead and 12ms extra latency.

**Latency (too slow)**
Users expect sub-second responses. My orchestration layer hits P99 of 0.095ms for tool dispatch (4.3M dispatches/sec in benchmarks). But end-to-end RAG latency is a different story — embedding generation, vector search, re-ranking, and LLM generation all add up. Caching helps (88% hit rate on my L1/L2/L3 architecture), but cold queries still take 2-4 seconds.

**Cost (too expensive)**
Before caching: $847/month in LLM calls. After 3-tier caching: $93/month. That's an 89% reduction. But most teams I talk to haven't implemented caching beyond basic prompt deduplication. They're paying full price for every query, even repeat ones.

**Evaluation (can't measure quality)**
This is the one that keeps me up at night. How do you know your RAG system is actually getting better? I use human-labeled test sets, precision@k metrics, and hallucination rate tracking. But building evaluation datasets is expensive and maintaining them as your data changes is a full-time job.

**Poll:**
- Retrieval quality (wrong chunks)
- Latency (too slow)
- Cost (too expensive)
- Evaluation (can't measure quality)

Vote and drop a comment about what you've tried. I'll share specific solutions for whichever option wins.

Live demo of my RAG pipeline: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

#RAG #AIEngineering #Poll #MachineLearning #NLP

---

## Engagement Strategy

**CTA**: Poll vote + comment for follow-up solutions
**Expected Replies**: 70-100 (polls drive high engagement, topic resonates broadly)
**Response Time**: <1 hour for all comments
**Follow-Up Commitment**: Post a detailed follow-up on Monday (Week 3, Post 10) addressing the winning poll option

**Prepared Responses**:

**If "Retrieval quality" wins:**
A: This is the most common one I see. Three things that made the biggest difference for me: (1) Hybrid retrieval — BM25 handles keyword-exact queries that embeddings miss. (2) Chunk size tuning — I went from 512 tokens to 256 with 50-token overlap. Smaller chunks = more precise matches. (3) Metadata filtering — before vector search even runs, filter by document type, date range, or category. Cuts the search space and improves relevance. Full implementation in my docqa-engine repo: github.com/ChunkyTortoise/docqa-engine

**If "Latency" wins:**
A: Latency is death by a thousand cuts in RAG. Here's my stack for keeping it under 2 seconds: (1) Pre-compute embeddings at ingestion, not query time. (2) L1/L2/L3 caching — 88% of queries never touch the vector store. (3) Async everything — embedding generation and vector search run in parallel, not sequentially. (4) Model routing — simple queries go to Gemini (0.9s P95), complex ones go to Claude (1.2s P95). My orchestrator handles 4.3M dispatches/sec with P99 of 0.095ms.

**If "Cost" wins:**
A: Cost optimization is where engineering skill has the highest ROI. My 89% reduction came from three layers: L1 (in-memory) catches repeated queries within a session. L2 (Redis) catches repeats across users. L3 (persistent) catches repeats across deployments. Combined hit rate: 88%. Beyond caching, model routing matters — I use Claude for 20% of queries (complex intent), Gemini for 60% (simple classification), and GPT-4 for 20% (fallback). That multi-provider strategy cut per-query costs by another 42%.

**If "Evaluation" wins:**
A: This is the hardest problem in RAG and honestly, nobody has a perfect solution. What's worked for me: (1) Human-labeled test sets — expensive but necessary. I label 500 queries per domain with expected chunks and expected answers. (2) Automated regression testing — every PR runs the test set and flags precision@k drops. (3) Hallucination detection — I compare generated answers against source chunks and flag claims that don't appear in the retrieved context. It's not perfect, but it catches the worst failures before they reach users.

**Q: "What about GraphRAG or knowledge graphs?"**
A: I've experimented with graph-based retrieval for entity relationship queries (e.g., "which properties did this buyer view?"). It's powerful for structured relationships but adds significant complexity. For most RAG use cases, hybrid BM25 + dense retrieval with good chunking gets you 90% of the way there. I'd only add a knowledge graph if your queries are fundamentally about relationships between entities, not document retrieval.

---

## Follow-Up Actions

- [ ] 8:30am PT: Publish post (use LinkedIn poll format if available, otherwise text with options)
- [ ] 8:35am: Comment on 5 RAG / information retrieval posts
- [ ] Throughout day: Reply to all comments within 1 hour
- [ ] Saturday: Tally poll results, draft follow-up post addressing the winning option
- [ ] Send 5 connection requests to engaged commenters (target: ML engineers, RAG practitioners)
- [ ] Track metrics: impressions, engagement rate, poll participation, demo link clicks
- [ ] Note: This post is also a market research tool — poll results inform future content priorities
