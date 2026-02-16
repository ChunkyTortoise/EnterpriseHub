---
title: "DocQA Engine: Production RAG in Hours, Not Weeks"
duration: "2:00"
target_audience: "Developers building document Q&A, teams replacing legacy search, startups needing RAG"
key_metrics:
  - "500+ automated tests"
  - "5 chunking strategies"
  - "Hybrid retrieval (BM25 + vector)"
  - "$0/month hosting (self-hosted)"
  - "Confidence-scored citations"
github_url: "https://github.com/ChunkyTortoise/docqa-engine"
gumroad_tiers: "Starter $59 | Pro $249 | Enterprise $1,499"
---

# DocQA Engine: 2-Minute Product Demo Script

**Total Duration:** 2:00
**Pace:** ~2.5 words/sec (conversational)
**Word Target:** 300 words

---

## Act 1: Hook [0:00-0:20]

### Visual
- Title card: "DocQA Engine" with tagline "Your Documents. Instant Answers. Cited Sources."
- Split screen: frustrated user searching docs manually vs. DocQA returning precise answers

### Audio
"Custom RAG systems cost $300 to $1,200 on Fiverr. Monthly SaaS bills for hosted solutions run $50 to $500. Or you could spend weeks building one from scratch with LangChain.

DocQA Engine gives you a production-ready RAG pipeline you own forever. Zero monthly fees. 500 tests. Deploy in hours."

---

## Act 2: Demo [0:20-1:20]

### Visual
- Terminal: `docker-compose up` starting FastAPI + Streamlit
- Streamlit UI: upload a PDF document
- Type a question, show answer with citation scores
- Show chunking strategy selector (5 options)

### Audio
"I start with Docker Compose. API and UI come up in under a minute.

Here is the Streamlit interface. I upload a technical document -- this is a 40-page engineering spec. Now I ask: 'What are the latency requirements for the API layer?'

Watch the answer panel. DocQA returns a precise answer with three source citations. Each citation has a confidence score -- 0.92, 0.87, 0.71. Your users see exactly where the answer came from and how confident the system is.

The retrieval is hybrid -- BM25 for keyword matching plus dense vector search for semantic understanding. This handles both exact terms and natural language queries without compromise.

Now look at the chunking options. Five strategies: fixed-size for structured docs, sentence-based for natural text, paragraph for preserving structure, recursive for complex documents, and semantic chunking for highest quality. Pick the one that fits your data."

*[Switch chunking strategy, re-query, show different results]*

"Same question, semantic chunking. Notice the citation scores improved -- 0.95, 0.91. The right chunking strategy matters."

---

## Act 3: CTA [1:20-2:00]

### Visual
- FastAPI docs page showing REST API endpoints
- GitHub repo with green CI badge
- Gumroad pricing tiers

### Audio
"The REST API has JWT auth, rate limiting at 100 requests per minute, and usage metering built in. Deploy behind your load balancer today.

Everything is in the repo: 500 tests, 4 architecture decision records, benchmark results, and full Docker support.

Starter is $59 on Gumroad. Pro adds a RAG optimization guide, three domain case studies, and a 30-minute expert consultation for $249. Enterprise includes custom domain tuning and white-label rights for $1,499.

Stop paying monthly for RAG. Own the pipeline. Deploy your document Q&A system in one afternoon -- link in the description."

---

## Key Moments

| Timestamp | Moment | Purpose |
|-----------|--------|---------|
| 0:03 | "$300-$1,200 on Fiverr" | Price anchoring |
| 0:15 | "Zero monthly fees" | Value proposition |
| 0:35 | PDF upload + query | Live product demo |
| 0:50 | Citation confidence scores | Trust/compliance angle |
| 1:00 | Hybrid retrieval explanation | Technical depth |
| 1:15 | Chunking strategy comparison | Shows configurability |
| 1:50 | Pricing tiers | Conversion |

## File References
- GitHub: https://github.com/ChunkyTortoise/docqa-engine
- Gumroad Listing: `content/gumroad/docqa-starter-LISTING.md`
