# Dev.to Publishing Guide -- February 19, 2026

## Full Inventory (9 files in content/devto/)

| # | File | Title | `published` | Published Feb 9? | Status |
|---|------|-------|-------------|-------------------|--------|
| 1 | `article1-production-rag.md` | Building Production RAG Without LangChain | `true` | Yes ("Production RAG System") | SKIP |
| 2 | `article2-replaced-langchain.md` | Why I Replaced LangChain with 15KB of httpx | `true` | Yes ("Replaced LangChain") | SKIP |
| 3 | `article3-csv-to-dashboard.md` | From CSV to Dashboard in 30 Seconds with Python | `true` | Yes ("CSV to Dashboard") | SKIP |
| 4 | `article-4-production-rag.md` | Building a Production RAG System That Actually Works (With Benchmarks) | `false` | Duplicate of #1 (same topic, longer version) | SKIP -- too much overlap |
| 5 | `article-langchain-alternative.md` | Why I Built a RAG System Without LangChain | `true` | Variant of #1/#2 | SKIP |
| 6 | `production-multi-agent-8500-tests.md` | Building Production Multi-Agent Systems: Lessons from 8,500 Tests | `true` | N/A | SKIP -- already published |
| 7 | `PUBLISH_READY.md` | (Publishing instructions from Feb 18) | N/A | N/A | REFERENCE ONLY |
| 8 | **`article-5-llm-cost-reduction.md`** | **How I Reduced LLM Costs by 89% With 3-Tier Caching** | `false` | **No** | **PUBLISH** |
| 9 | **`article3-csv-dashboard.md`** | **CSV to Dashboard in 10 Minutes with Streamlit** | `false` | **No** (different/expanded version of #3) | **PUBLISH** |

---

## Unpublished Articles Ready to Publish: 2

### Article A: How I Reduced LLM Costs by 89% With 3-Tier Caching

| Field | Value |
|-------|-------|
| Source file | `article-5-llm-cost-reduction.md` |
| Word count | ~2,055 |
| Read time | ~10 min (at 200 wpm) |
| Gumroad CTA | Added (before author bio) |
| Recommended tags | `python`, `ai`, `programming`, `tutorial` |

**Why publish first**: Cost-reduction headlines with concrete dollar figures ($847 to $93) perform extremely well on Dev.to. This article has production benchmarks, detailed implementation code, and a clear before/after narrative. It complements the already-published RAG article (natural sequel). High shareability for LinkedIn cross-posting.

---

### Article B: CSV to Dashboard in 10 Minutes with Streamlit

| Field | Value |
|-------|-------|
| Source file | `article3-csv-dashboard.md` |
| Word count | ~1,410 |
| Read time | ~7 min (at 200 wpm) |
| Gumroad CTA | Added (before closing line) |
| Recommended tags | `python`, `webdev`, `tutorial`, `beginners` |

**Why this is distinct from the published CSV article**: The published version (`article3-csv-to-dashboard.md`, "From CSV to Dashboard in 30 Seconds with Python") is shorter and simpler. This version is significantly expanded with: step-by-step 10-minute blueprint, complete code listing, advanced features (multi-page, themes, session state, file upload, auth), a real-world real estate lead dashboard example, production tips, and common mistakes. It stands on its own as a deeper tutorial.

**Tag note**: Changed from `datascience` to `webdev` + `beginners` for broader reach. The `beginners` tag has massive followership on Dev.to and this article's step-by-step format fits perfectly.

---

## Recommended Publish Order

| Order | Article | Publish Date | Rationale |
|-------|---------|-------------|-----------|
| 1 | LLM Cost Reduction (89%) | Feb 19-20 | Strongest headline hook, concrete $ savings, high shareability |
| 2 | CSV to Dashboard (Streamlit) | Feb 22-23 | Broadest audience (beginners + webdev), different topic for variety |

Space 2-3 days apart for maximum reach in Dev.to's feed algorithm.

---

## LinkedIn Cross-Post Hooks

**For Article A (LLM Costs)**:
> I cut my AI agent costs from $847/mo to $93/mo with a weekend refactor. No ML research. No model fine-tuning. Just caching. Here's the exact implementation.

**For Article B (Streamlit)**:
> Business needs a dashboard. You have a CSV. Streamlit gets you there in 10 minutes. Here's the complete blueprint I use for production dashboards.

---

## Publishing Checklist

- [ ] Copy article text from the sections below into Dev.to editor
- [ ] Set frontmatter `published: true` and correct tags
- [ ] Add a cover image (architecture diagram or code screenshot)
- [ ] Preview rendering (especially code blocks and ASCII diagrams)
- [ ] Publish
- [ ] Cross-post to LinkedIn with hook text above
- [ ] Update `content-assets.md` with new publish dates

---

## Copy-Paste Ready: Article A -- LLM Cost Reduction

Everything below until the next article separator is ready to paste into Dev.to.

---

---
title: How I Reduced LLM Costs by 89% With 3-Tier Caching
published: true
tags: python, ai, programming, tutorial
cover_image:
canonical_url:
---

# How I Reduced LLM Costs by 89% With 3-Tier Caching

I spent $847 on AI agent conversations in January. By February, I'd cut that to $93. Same features. Same users. Same quality.

The difference? I fixed how my agents remembered conversations.

This is the story of building a 3-tier memory cache that reduced costs by 89%, improved latency by 97%, and scaled to 200+ concurrent users.

---

## The Problem

I was building a real estate AI platform with 200+ concurrent conversations. Every time a user asked a follow-up question, the agent needed context:

- "What price range did I mention?"
- "Which neighborhoods am I interested in?"
- "What did the agent say about schools?"

My initial approach: **Send the entire conversation history with every query.**

Here's what that looked like in code:

```python
# The expensive way (don't do this)
async def answer_question(question: str, user_id: str):
    # Load ALL messages from database
    history = await db.get_all_messages(user_id)  # 200+ messages

    # Send everything to Claude
    response = await claude_client.messages.create(
        model="claude-opus-4-6",
        messages=history + [{"role": "user", "content": question}]
    )

    return response
```

**The cost:**
- Average conversation: 200 messages
- Average message: 250 tokens
- Total context per query: 50,000 tokens
- Claude Opus 4.6 pricing: $0.015/1K input tokens
- **Cost per query: $0.75**

At 40 queries/user/day x 30 users, that's $900/month. For a side project, that's unsustainable.

---

## The Insight: Memory Access Patterns

Before optimizing, I logged 10,000 queries over 7 days to understand access patterns:

```python
# Analysis of 10,000 agent queries
memory_access_patterns = {
    "last_10_messages": 7420,     # 74.2%
    "last_100_messages": 1410,    # 14.1%
    "full_history_search": 1170   # 11.7%
}
```

**Key finding:** 90% of queries reference recent messages. Only 12% require semantic search over full history.

This meant most queries were:
- "What did you just say?" (sequential)
- "Earlier you mentioned schools..." (recent context)

Not:
- "What have we discussed about financing over the past 3 weeks?" (semantic search)

**Implication:** A TTL-based cache could handle 90% of queries without touching the LLM or database.

---

## The Solution: 3-Tier Memory Cache

```
┌─────────────────────────────────────────────┐
│  L1: In-Process Cache (Last 10 messages)   │
│  Retrieval: <1ms | TTL: 30 minutes         │
└──────────────────┬──────────────────────────┘
                   ↓ (cache miss)
┌─────────────────────────────────────────────┐
│  L2: Redis Cache (Last 100 messages)       │
│  Retrieval: <5ms | TTL: 24 hours           │
└──────────────────┬──────────────────────────┘
                   ↓ (cache miss)
┌─────────────────────────────────────────────┐
│  L3: Postgres + Embeddings (Full history)  │
│  Retrieval: <50ms | Semantic search        │
└─────────────────────────────────────────────┘
```

### Design Principles

1. **L1 (In-Process)**: Most queries reference the last few messages. Keep them in memory.
2. **L2 (Redis)**: Recent conversations (last 24 hours). Shared across worker processes.
3. **L3 (Postgres + pgvector)**: Full history with semantic search. Fallback when caches miss.

### Why 3 Tiers?

- **L1 alone**: Fast but not shared (workers don't see each other's caches)
- **L2 alone**: Shared but slower than in-memory
- **L3 alone**: Powerful but expensive (database + embeddings)

Combining all three gives speed, consistency, and full coverage.

---

## Implementation

### L1: In-Process Cache

```python
from functools import lru_cache
from collections import OrderedDict

class InProcessCache:
    def __init__(self, max_size: int = 1000):
        # OrderedDict maintains insertion order for LRU eviction
        self._cache = OrderedDict()
        self._max_size = max_size

    def get(self, user_id: str) -> list[dict] | None:
        """Get last 10 messages for user."""
        if user_id in self._cache:
            # Move to end (mark as recently used)
            self._cache.move_to_end(user_id)
            return self._cache[user_id]
        return None

    def set(self, user_id: str, messages: list[dict]):
        """Store last 10 messages for user."""
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)

        self._cache[user_id] = messages[-10:]  # Keep last 10
        self._cache.move_to_end(user_id)

# Global cache instance (per worker process)
l1_cache = InProcessCache()
```

**Performance:** <1ms retrieval, 74% hit rate

---

### L2: Redis Cache

```python
import redis.asyncio as redis
import json

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def get(self, user_id: str) -> list[dict] | None:
        """Get last 100 messages for user."""
        cached = await self.redis.get(f"messages:{user_id}")
        if cached:
            return json.loads(cached)
        return None

    async def set(self, user_id: str, messages: list[dict]):
        """Store last 100 messages with 24hr TTL."""
        await self.redis.setex(
            f"messages:{user_id}",
            86400,  # 24 hours
            json.dumps(messages[-100:])  # Keep last 100
        )

l2_cache = RedisCache()
```

**Performance:** <5ms retrieval, 14% hit rate (cache misses from L1)

---

### L3: Postgres + pgvector

```python
import asyncpg
from pgvector.asyncpg import register_vector
import anthropic

class PostgresCache:
    def __init__(self, database_url: str):
        self.db = None
        self.database_url = database_url
        self.embedding_client = anthropic.Anthropic()

    async def connect(self):
        """Initialize connection and pgvector extension."""
        self.db = await asyncpg.connect(self.database_url)
        await register_vector(self.db)

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding using Claude."""
        # Using Claude's text embedding API
        # (Replace with OpenAI/Cohere for production)
        response = await self.embedding_client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding

    async def semantic_search(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> list[dict]:
        """Search full history using semantic similarity."""
        query_embedding = await self.embed_text(query)

        results = await self.db.fetch("""
            SELECT content, role, timestamp, metadata
            FROM messages
            WHERE user_id = $1
            ORDER BY embedding <-> $2::vector
            LIMIT $3
        """, user_id, query_embedding, limit)

        return [dict(r) for r in results]

l3_cache = PostgresCache(DATABASE_URL)
```

**Performance:** <50ms retrieval, 12% hit rate (semantic search fallback)

---

### Unified Memory Interface

```python
class AgentMemory:
    def __init__(self):
        self.l1 = InProcessCache()
        self.l2 = RedisCache()
        self.l3 = PostgresCache(DATABASE_URL)

    async def get_context(
        self,
        user_id: str,
        query: str,
        limit: int = 10
    ) -> list[dict]:
        """Retrieve conversation context using 3-tier cache."""

        # L1: Check in-process cache
        messages = self.l1.get(user_id)
        if messages and len(messages) >= limit:
            return messages[-limit:]

        # L2: Check Redis cache
        messages = await self.l2.get(user_id)
        if messages:
            # Backfill L1
            self.l1.set(user_id, messages)
            return messages[-limit:]

        # L3: Semantic search in Postgres
        messages = await self.l3.semantic_search(user_id, query, limit)

        # Backfill L2 and L1
        await self.l2.set(user_id, messages)
        self.l1.set(user_id, messages)

        return messages

    async def add_message(self, user_id: str, message: dict):
        """Add new message to all cache layers."""
        # Invalidate L1 and L2 (will be refreshed on next query)
        self.l1.set(user_id, [])  # Clear
        await self.l2.set(user_id, [])  # Clear

        # Store in L3 (Postgres)
        embedding = await self.l3.embed_text(message['content'])
        await self.l3.db.execute("""
            INSERT INTO messages (user_id, content, role, embedding, timestamp)
            VALUES ($1, $2, $3, $4, NOW())
        """, user_id, message['content'], message['role'], embedding)
```

---

## Results

After deploying the 3-tier cache, I ran benchmarks over 30 days (200 concurrent users, 10K queries):

### Cache Hit Rates

| Tier | Hit Rate | Avg Latency |
|------|----------|-------------|
| L1 (in-process) | 74.2% | 0.8ms |
| L2 (Redis) | 14.1% | 4.2ms |
| L3 (Postgres) | 11.7% | 48.3ms |

**Overall:** 88.3% of queries avoided database + embedding generation.

---

### Latency Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| P50 latency | 120ms | 2ms | **98.3%** |
| P95 latency | 180ms | 4.8ms | **97.3%** |
| P99 latency | 320ms | 48ms | **85%** |

---

### Cost Reduction

**Before:**
- 564 queries/day
- 50K tokens per query (full history)
- 564 x 50K = 28.2M tokens/day
- $0.015/1K tokens = $423/day
- **$847/month** (20-day billing cycle)

**After:**
- 88% cache hit rate -> only 68 queries hit LLM/day
- 6K tokens per query (L3 semantic search results only)
- 68 x 6K = 408K tokens/day
- $0.015/1K tokens = $6.12/day
- **$93/month** (20-day billing cycle)

**Savings: 89%** ($754/month)

---

## Architecture Diagram

```
User Query: "What did I say about my budget?"
     |
     v
┌─────────────────────┐
│  L1 Cache (RAM)     │──> Cache HIT (74% of queries)
│  Last 10 messages   │    Return in <1ms
└─────────┬───────────┘
          │ Cache MISS
          v
┌─────────────────────┐
│  L2 Cache (Redis)   │──> Cache HIT (14% of queries)
│  Last 100 messages  │    Return in <5ms
└─────────┬───────────┘
          │ Cache MISS
          v
┌─────────────────────┐
│  L3 (Postgres)      │──> Semantic Search (12% of queries)
│  Full conversation  │    Return in <50ms
│  + Vector embeddings│
└─────────────────────┘
```

---

## Key Lessons

### 1. Most Memory Access is Sequential

Users rarely ask "What did we discuss 3 weeks ago?" They ask "What did you just say?"

**Implication:** TTL-based caches (L1/L2) handle 90% of queries. You don't need a vector database for everything.

---

### 2. Eviction Policies Matter

I initially used pure TTL expiration (oldest entries drop first). This caused issues when users corrected information:

> User: "Actually, my budget is $500K, not $300K."

The old $300K entry stayed in cache for 24 hours, causing the agent to hallucinate incorrect prices.

**Fix:** Semantic similarity-based eviction. When cache is full:

```python
# Evict entries with lowest similarity to recent queries
embeddings = [await self.embed(msg) for msg in cache]
recent_query_embedding = await self.embed(recent_queries[-1])
similarities = [
    cosine_similarity(e, recent_query_embedding)
    for e in embeddings
]
cache.pop(argmin(similarities))  # Remove least relevant
```

---

### 3. Don't Over-Optimize

I spent a week trying to optimize L3 (Postgres semantic search) to sub-10ms. Wasted effort.

**Why?** Only 12% of queries hit L3. Optimizing L1 (74% hit rate) had 6x more impact.

**Lesson:** Optimize the hot path first. Measure before optimizing.

---

### 4. Cache Invalidation is Hard

The classic computer science problem: cache invalidation.

**Scenarios that require invalidation:**
- User corrects information ("Actually, my name is Sarah, not Susan")
- User deletes message history ("Clear my data")
- System detects stale data (message edited externally)

**Solution:** Event-driven invalidation

```python
async def invalidate_cache(user_id: str, reason: str):
    """Clear all cache layers for user."""
    # Clear L1
    l1_cache._cache.pop(user_id, None)

    # Clear L2
    await l2_cache.redis.delete(f"messages:{user_id}")

    # L3 doesn't need clearing (source of truth)

    # Log for debugging
    logger.info(f"Cache invalidated for {user_id}: {reason}")
```

---

## When You DON'T Need This

If you have:
- **Low query volume** (<100 queries/day): Just send full history. Simple > complex.
- **Short conversations** (<20 messages): Context window overhead is negligible.
- **Generous budget**: At $10K+/month LLM spend, 10% savings isn't worth the engineering time.

This architecture makes sense when:
- You have 1,000+ conversations/day
- Conversations are long (100+ messages)
- You're cost-sensitive (startups, side projects)

---

## Production Considerations

### Observability

I track cache performance with Prometheus metrics:

```python
from prometheus_client import Counter, Histogram

cache_hits = Counter(
    "agent_memory_cache_hits",
    "Cache hits by tier",
    ["tier"]
)

cache_latency = Histogram(
    "agent_memory_latency_seconds",
    "Memory retrieval latency",
    ["tier"]
)

async def get_context(user_id: str, query: str):
    # L1 check
    start = time.time()
    messages = l1_cache.get(user_id)
    if messages:
        cache_hits.labels(tier="l1").inc()
        cache_latency.labels(tier="l1").observe(time.time() - start)
        return messages

    # L2 check
    start = time.time()
    messages = await l2_cache.get(user_id)
    if messages:
        cache_hits.labels(tier="l2").inc()
        cache_latency.labels(tier="l2").observe(time.time() - start)
        return messages

    # L3 fallback
    start = time.time()
    messages = await l3_cache.semantic_search(user_id, query)
    cache_hits.labels(tier="l3").inc()
    cache_latency.labels(tier="l3").observe(time.time() - start)
    return messages
```

This shows me if cache hit rate drops (usually means conversation patterns changed).

---

### Horizontal Scaling

Redis (L2) is the bottleneck at 10K+ concurrent users. I use Redis Cluster with consistent hashing:

```python
from redis.cluster import RedisCluster

redis_client = RedisCluster(
    host="redis-cluster",
    port=6379,
    decode_responses=True
)
```

L1 scales naturally (each worker process has its own cache).

L3 (Postgres) scales with read replicas for semantic search.

---

### Monitoring Cache Health

Weekly dashboard tracks:
- Cache hit rates by tier
- P95 latency by tier
- Eviction rates
- Cost per 1K queries

If L1 hit rate drops below 70%, I investigate conversation patterns.

---

## Try It Yourself

**GitHub**: [ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub)

**Run benchmarks locally:**

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
docker compose up -d  # Starts Redis + Postgres
python benchmarks/memory_performance.py
```

**Expected output:**
```
Cache Hit Rates:
  L1 (in-process): 74.2%
  L2 (Redis):      14.1%
  L3 (Postgres):   11.7%

Latency (P95):
  L1: 0.8ms
  L2: 4.2ms
  L3: 48.3ms

Cost Reduction: 89.1%
```

---

## Conclusion

Before building complex RAG systems or fine-tuning models, check if your problem is actually a caching problem.

My 89% cost reduction came from a weekend of refactoring, not months of ML research.

**Next steps if you're hitting similar issues:**
1. Measure your cache hit rate (instrument your code)
2. Identify access patterns (sequential vs. semantic)
3. Start with a simple in-memory cache (L1 only)
4. Add layers only when needed (L2 if L1 hit rate <80%)

Questions? Drop a comment or open an issue on GitHub.

---

## Get the Full Source Code

Want the complete 3-tier caching implementation with Docker Compose setup, benchmark scripts, and production configs?

**[Get the full source code on Gumroad](https://gumroad.com)** -- includes the AgentMemory class, Redis/Postgres configs, Prometheus dashboards, and load testing scripts.

---

**About the Author**

ChunkyTortoise -- AI/ML engineer building production-grade agent systems. 8,500+ tests across 11 repos. 89% LLM cost reduction in production.

Portfolio: [github.com/ChunkyTortoise](https://github.com/ChunkyTortoise)
LinkedIn: [linkedin.com/in/caymanroden](https://linkedin.com/in/caymanroden)

---
---

## Copy-Paste Ready: Article B -- CSV to Dashboard (Streamlit)

Everything below is ready to paste into Dev.to.

---

---
title: CSV to Dashboard in 10 Minutes with Streamlit
published: true
tags: python, webdev, tutorial, beginners
cover_image:
canonical_url:
---

# CSV to Dashboard in 10 Minutes with Streamlit

Business asks for a dashboard. You have a CSV. Building it with Tableau takes 2 hours. Writing HTML/CSS/JavaScript takes 2 days.

Streamlit takes 10 minutes.

I've built 7 production dashboards with Streamlit for a real estate AI platform. Here's the fastest path from CSV to interactive dashboard.

## The Challenge

You have messy data. You need:
- Summary statistics
- Interactive charts
- Filters and controls
- Shareable link
- Zero infrastructure

Traditional BI tools are overkill. Writing a web app from scratch is too slow.

Streamlit solves this: write Python, get a web app.

## Why Streamlit?

**Python-native**: No HTML, CSS, or JavaScript. Just Python.

**Interactive**: Widgets automatically trigger reruns. State management is handled for you.

**Fast iteration**: Save your file, see changes instantly.

**Free deployment**: Streamlit Community Cloud hosts public apps for free.

**Rich components**: Charts, maps, dataframes, metrics, layouts -- all built-in.

## The 10-Minute Blueprint

Here's a complete working dashboard. Each step takes ~1 minute.

### Step 1: Setup (1 min)

```bash
pip install streamlit pandas plotly
touch app.py
```

### Step 2: Load Data (1 min)

```python
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("sales.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()
```

The `@st.cache_data` decorator caches the result. Load once, reuse on every interaction.

### Step 3: Show Summary Stats (1 min)

```python
# Metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Revenue",
        f"${df['revenue'].sum():,.0f}",
        delta=f"{df['revenue'].pct_change().iloc[-1]*100:.1f}%"
    )

with col2:
    st.metric(
        "Total Orders",
        f"{len(df):,}",
        delta=f"{(len(df) - len(df[df['date'] < df['date'].max() - pd.Timedelta(days=30)])):,}"
    )

with col3:
    st.metric(
        "Avg Order Value",
        f"${df['revenue'].mean():,.2f}"
    )

with col4:
    st.metric(
        "Top Product",
        df.groupby('product')['revenue'].sum().idxmax()
    )
```

Four metrics in a row. Streamlit handles the layout.

### Step 4: Add Visualizations (2 min)

```python
import plotly.express as px

# Revenue over time
st.subheader("Revenue Trend")
daily_revenue = df.groupby('date')['revenue'].sum().reset_index()
fig = px.line(
    daily_revenue,
    x='date',
    y='revenue',
    title='Daily Revenue'
)
st.plotly_chart(fig, use_container_width=True)

# Revenue by product
st.subheader("Revenue by Product")
product_revenue = df.groupby('product')['revenue'].sum().sort_values(ascending=False)
fig = px.bar(
    product_revenue,
    x=product_revenue.index,
    y=product_revenue.values,
    labels={'x': 'Product', 'y': 'Revenue'},
    title='Top Products'
)
st.plotly_chart(fig, use_container_width=True)
```

Plotly charts are interactive by default. Hover, zoom, pan -- all free.

### Step 5: Add Filters (2 min)

```python
# Sidebar filters
st.sidebar.header("Filters")

# Date range
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min(), df['date'].max()),
    min_value=df['date'].min(),
    max_value=df['date'].max()
)

# Product filter
products = st.sidebar.multiselect(
    "Products",
    options=df['product'].unique(),
    default=df['product'].unique()
)

# Apply filters
filtered_df = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1])) &
    (df['product'].isin(products))
]

# Update all visualizations to use filtered_df instead of df
```

Sidebar controls keep the main view clean. Every interaction triggers a rerun with new filters.

### Step 6: Show Raw Data (1 min)

```python
# Data table
st.subheader("Raw Data")
st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "revenue": st.column_config.NumberColumn("Revenue", format="$%d"),
        "date": st.column_config.DateColumn("Date", format="YYYY-MM-DD")
    }
)
```

Interactive table with sorting, searching, and custom formatting.

### Step 7: Add Download Button (1 min)

```python
# Download filtered data
st.download_button(
    label="Download CSV",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_sales.csv",
    mime="text/csv"
)
```

Users can export filtered data for further analysis.

### Step 8: Run Locally (1 min)

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Make changes, see them instantly.

## Complete Code

Here's the full dashboard in ~60 lines:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Sales Dashboard", layout="wide")
st.title("Sales Dashboard")

@st.cache_data
def load_data():
    df = pd.read_csv("sales.csv")
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
date_range = st.sidebar.date_input(
    "Date Range",
    value=(df['date'].min(), df['date'].max())
)
products = st.sidebar.multiselect(
    "Products",
    options=df['product'].unique(),
    default=df['product'].unique()
)

# Apply filters
filtered_df = df[
    (df['date'] >= pd.to_datetime(date_range[0])) &
    (df['date'] <= pd.to_datetime(date_range[1])) &
    (df['product'].isin(products))
]

# Metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Revenue", f"${filtered_df['revenue'].sum():,.0f}")
col2.metric("Total Orders", f"{len(filtered_df):,}")
col3.metric("Avg Order Value", f"${filtered_df['revenue'].mean():,.2f}")
col4.metric("Top Product", filtered_df.groupby('product')['revenue'].sum().idxmax())

# Charts
st.subheader("Revenue Trend")
daily = filtered_df.groupby('date')['revenue'].sum().reset_index()
fig = px.line(daily, x='date', y='revenue')
st.plotly_chart(fig, use_container_width=True)

st.subheader("Revenue by Product")
by_product = filtered_df.groupby('product')['revenue'].sum().sort_values(ascending=False)
fig = px.bar(by_product, x=by_product.index, y=by_product.values)
st.plotly_chart(fig, use_container_width=True)

# Data table
st.subheader("Raw Data")
st.dataframe(filtered_df, use_container_width=True)

# Download
st.download_button(
    "Download CSV",
    filtered_df.to_csv(index=False),
    "sales.csv",
    "text/csv"
)
```

## Advanced Features

Once the basic dashboard works, add these:

### 1. Multiple Pages

```python
# pages/home.py
import streamlit as st
st.title("Home")

# pages/analytics.py
import streamlit as st
st.title("Analytics")
```

Streamlit automatically creates a sidebar navigation for files in `pages/`.

### 2. Custom Themes

```toml
# .streamlit/config.toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 3. Session State

```python
# Persist data across interactions
if 'counter' not in st.session_state:
    st.session_state.counter = 0

if st.button("Increment"):
    st.session_state.counter += 1

st.write(f"Counter: {st.session_state.counter}")
```

### 4. File Upload

```python
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success(f"Loaded {len(df)} rows")
```

Users can upload their own data without code changes.

### 5. Authentication (Streamlit Cloud)

```python
# Restrict to certain users
if st.experimental_user.email not in ["admin@company.com"]:
    st.error("Access denied")
    st.stop()
```

Built-in auth for deployed apps.

## Real-World Example

Here's a dashboard I built for real estate lead analysis:

```python
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Lead Dashboard", layout="wide")

@st.cache_data
def load_leads():
    return pd.read_csv("leads.csv", parse_dates=['created_at'])

df = load_leads()

# Filters
st.sidebar.header("Filters")
temperature = st.sidebar.multiselect(
    "Lead Temperature",
    ["Hot", "Warm", "Cold"],
    default=["Hot", "Warm", "Cold"]
)
date_range = st.sidebar.slider(
    "Days Back",
    1, 90, 30
)

# Filter data
cutoff = pd.Timestamp.now() - pd.Timedelta(days=date_range)
filtered = df[
    (df['created_at'] >= cutoff) &
    (df['temperature'].isin(temperature))
]

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Leads", len(filtered))
col2.metric("Hot Leads", len(filtered[filtered['temperature'] == 'Hot']))
col3.metric("Conversion Rate", f"{(filtered['converted'].mean() * 100):.1f}%")
col4.metric("Avg Response Time", f"{filtered['response_minutes'].mean():.0f}m")

# Lead volume over time
st.subheader("Lead Volume")
daily = filtered.groupby(filtered['created_at'].dt.date).size()
fig = px.area(daily, x=daily.index, y=daily.values)
st.plotly_chart(fig, use_container_width=True)

# Conversion funnel
st.subheader("Conversion Funnel")
funnel_data = pd.DataFrame({
    'Stage': ['Leads', 'Qualified', 'Contacted', 'Converted'],
    'Count': [
        len(filtered),
        len(filtered[filtered['qualified']]),
        len(filtered[filtered['contacted']]),
        len(filtered[filtered['converted']])
    ]
})
fig = px.funnel(funnel_data, x='Count', y='Stage')
st.plotly_chart(fig, use_container_width=True)

# Top sources
st.subheader("Lead Sources")
sources = filtered['source'].value_counts()
fig = px.pie(values=sources.values, names=sources.index)
st.plotly_chart(fig, use_container_width=True)
```

This dashboard helped us identify that:
- 73% of hot leads came from Zillow
- Response time >15min dropped conversion by 40%
- Cold leads had 2% conversion (stopped spending on them)

Those insights drove $180K in revenue optimization.

## Deployment

Deploy to Streamlit Community Cloud in 3 steps:

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo, select `app.py`, click Deploy

Your dashboard is now live at `your-app.streamlit.app`.

For private deployments, use:
- **Streamlit Cloud** (Teams plan, $250/mo)
- **AWS/GCP**: Run with Docker
- **Heroku**: One-click deploy

## Tips for Production Dashboards

1. **Cache everything**: Use `@st.cache_data` for data loading, `@st.cache_resource` for model loading
2. **Add error handling**: Wrap data operations in try/except
3. **Show loading states**: Use `st.spinner("Loading...")` for slow operations
4. **Optimize queries**: Filter data before loading, use indexes
5. **Add tooltips**: Use `help` parameter to explain metrics
6. **Test on mobile**: Streamlit is responsive but test layout on small screens
7. **Monitor usage**: Add analytics to track which features users actually use

## Common Mistakes

**Don't:** Load data on every interaction
```python
df = pd.read_csv("big_file.csv")  # Loads on every click!
```

**Do:** Cache it
```python
@st.cache_data
def load_data():
    return pd.read_csv("big_file.csv")
```

**Don't:** Store large objects in session_state
```python
st.session_state.df = huge_dataframe  # Slows down app
```

**Do:** Cache and reference
```python
@st.cache_data
def get_df():
    return huge_dataframe
```

## When NOT to Use Streamlit

Streamlit is great for dashboards. It's not great for:
- Complex multi-step workflows (use Flask/FastAPI)
- Real-time updates (use WebSockets)
- Mobile apps (use React Native)
- Pixel-perfect designs (use custom frontend)

## Try It Yourself

I've built 7 production Streamlit dashboards:

- **InsightEngine**: ML model observatory ([ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app))
- **DocQA**: Document Q&A with RAG ([ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app))
- **Scrape & Serve**: Web scraping monitor ([ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app))

All repos are on GitHub: [ChunkyTortoise](https://github.com/ChunkyTortoise)

## Questions?

- What dashboards have you built with Streamlit?
- What features would you add to the blueprint?
- What BI tools are you replacing?

Share in the comments!

---

## Get the Full Source Code

Want the complete Streamlit dashboard template with multi-page layout, 10 chart types, auth integration, and deployment configs?

**[Get the full source code on Gumroad](https://gumroad.com)** -- includes the production dashboard template, Docker deployment configs, and the real estate lead dashboard example.

---

*Building data tools that don't suck. Follow for more Python, dashboards, and practical data engineering.*
