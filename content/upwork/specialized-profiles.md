# Upwork Specialized Profiles
Generated: 2026-02-17

---

## Specialized Profile 1: RAG & Document AI Systems

### Headline Options

```
Option A: RAG Engineer | Document AI & Semantic Search Systems | Python, FastAPI (72 chars)
Option B: Build RAG Systems That Actually Work — Hybrid Search, No Hallucinations (78 chars)
Option C: Document Q&A & Knowledge Base Engineer | BM25 + Semantic RAG | Python (75 chars)

RECOMMENDATION: Option B — leads with the client's pain point (hallucinating chatbots) and the
outcome (systems that actually work), which directly mirrors the language used in job postings
for this niche. More likely to stop the scroll in search results.
```

### Overview (Ready to Paste)

Most document AI systems fail in production the same way: they hallucinate answers, miss relevant
chunks, or collapse when the document set scales. I build RAG pipelines engineered to avoid all
three failure modes — and I have the test coverage to prove it.

My specialty is hybrid retrieval: combining BM25 keyword matching with dense semantic embeddings,
then layering re-ranking on top. This approach consistently outperforms pure vector search on
recall and precision, especially on domain-specific corpora where exact terminology matters
(legal documents, technical manuals, real estate contracts, internal knowledge bases).

**What I build for you:**

- Document Q&A systems with citation tracking — every answer links back to the source chunk
- Enterprise knowledge bases with multi-format ingestion (PDF, DOCX, HTML, plain text)
- Hybrid BM25 + semantic retrieval pipelines with configurable re-ranking
- RAG evaluation frameworks — automated tests to catch retrieval regressions before they hit users
- LLM cost optimization via semantic caching (up to 89% cost reduction at 88% cache hit rate)

**Technical proof:**

My docqa-engine project demonstrates the full stack: BM25 + TF-IDF + semantic search with
ChromaDB and FAISS backends, automated evaluation against ground-truth Q&A pairs, citation
tracking to source documents, and 500+ tests covering retrieval quality under adversarial inputs.
P95 latency stays under 200ms even as the corpus scales.

I have also built domain-specific RAG for real estate — a buyer/seller document assistant that
processes MLS listings, disclosure packets, and contract templates to answer agent and client
questions without hallucination.

**Tech stack for RAG work:**

LLMs: Claude API, GPT-4, Gemini | Retrieval: BM25, TF-IDF, ChromaDB, FAISS, pgvector |
Backend: FastAPI (async), Python 3.11+ | Caching: Redis 3-tier | Testing: pytest, 80%+ coverage
standard | Infra: Docker, GitHub Actions

**Ready to see it in action?**

I have a live Prompt Lab demo at https://ct-prompt-lab.streamlit.app/ and a public docqa-engine
repo on GitHub (ChunkyTortoise/docqa-engine). If you describe your document set and use case,
I can tell you within one conversation whether your retrieval approach will hold up at scale — and
what it will cost to run.

### Skills (10 tags, ordered)

```
1. Retrieval-Augmented Generation (RAG)
2. Large Language Models (LLM)
3. Python
4. FastAPI
5. Vector Database
6. Semantic Search
7. Natural Language Processing (NLP)
8. ChatGPT API / Claude API
9. PostgreSQL
10. AI Chatbot Development

RATIONALE: Ordered by search volume in the document AI niche — RAG and LLM first because those
are the exact terms clients type into Upwork search, followed by implementation stack terms that
validate technical credibility.
```

### Portfolio Item Description

**docqa-engine — Hybrid RAG Document Q&A System**

**Problem solved**: Enterprise teams waste hours manually searching large document sets; standard
vector search returns plausible-sounding but wrong answers when terminology is ambiguous.

**What I built**: A production-grade document Q&A engine combining BM25 keyword retrieval, TF-IDF
scoring, and dense semantic embeddings into a hybrid retrieval pipeline. The system ingests
multi-format documents (PDF, DOCX, plain text), chunks and indexes them, retrieves candidate
passages using all three methods, re-ranks results, and generates answers with full citation
tracking — every response links to the exact source chunk. An automated evaluation framework runs
recall and precision benchmarks against ground-truth Q&A pairs on every CI build, so retrieval
regressions are caught before they reach users. Redis semantic caching cuts repeat-query LLM
costs by up to 89%.

**Results/metrics:**
- P95 retrieval latency: under 200ms
- 500+ automated tests (retrieval quality, edge cases, adversarial inputs)
- Hybrid search outperforms pure vector search on domain-specific corpora
- 89% LLM cost reduction via 3-tier Redis caching (88% cache hit rate)

**Tech used:** Python, FastAPI, ChromaDB, FAISS, BM25, TF-IDF, Claude API, GPT-4, Redis,
PostgreSQL, Docker, pytest

**Repo:** github.com/ChunkyTortoise/docqa-engine

---

## Specialized Profile 2: AI Chatbot & CRM Integration

### Headline Options

```
Option A: AI Chatbot Developer | GoHighLevel, HubSpot & Salesforce Integration | Python (82 chars)
Option B: CRM-Native AI Chatbots — Qualify Leads, Log to GHL/HubSpot, Trigger Workflows (85 chars)
Option C: GPT-4 & Claude Chatbots That Write Back to Your CRM | GHL, HubSpot, Salesforce (86 chars)

RECOMMENDATION: Option C — uniquely specific. "Write back to your CRM" is the exact capability
most CRM chatbot clients are actually searching for, and naming all three major platforms in 86
characters captures keyword density without feeling like a list. Clients running GHL agencies
will recognize this immediately.
```

### Overview (Ready to Paste)

Your CRM has thousands of leads. Your team cannot call all of them — and a generic chatbot that
just collects a name and email and then goes silent is worse than no chatbot at all. The gap is
not AI capability; it is CRM integration. Most chatbot developers build the conversation layer and
stop there. I build the full loop: qualify the lead, log the outcome to your CRM, tag the contact,
trigger the next workflow step, and hand off to a human agent when the lead is hot.

**What this looks like in practice:**

- A GoHighLevel AI chatbot that qualifies leads via SMS, applies temperature tags (Hot/Warm/Cold)
  in GHL, triggers your existing nurture sequences, and notifies your team when a lead scores high
- A HubSpot or Salesforce assistant that answers inbound questions, updates contact properties in
  real time, and creates follow-up tasks without any manual data entry
- A buyer or seller bot for real estate that collects financial readiness signals, runs intent
  scoring, and books a calendar slot directly in GHL when confidence crosses threshold

**Verified case: EnterpriseHub + Jorge Bots**

I built a unified CRM integration layer (EnterpriseHub) supporting GoHighLevel, HubSpot, and
Salesforce through a single adapter protocol — swap the CRM without rewriting the bot logic. On
top of that, I built three production AI bots for a real estate client (jorge_real_estate_bots):
a Lead Bot for initial qualification, a Buyer Bot for purchase-readiness assessment, and a Seller
Bot for listing qualification. All three run on GHL, log structured data on every conversation,
and handle cross-bot handoffs with rate limiting and circular-handoff prevention. The system runs
157 passing tests in CI.

**Tech stack for CRM chatbot work:**

LLMs: Claude API, GPT-4, Gemini | CRMs: GoHighLevel, HubSpot, Salesforce | Backend: FastAPI
(async), Python 3.11+ | DB: PostgreSQL, Redis | Testing: pytest, TDD | Infra: Docker, GitHub
Actions

**Want to see it live?**

I have a live demo at https://ct-llm-starter.streamlit.app/ and public repos on GitHub
(ChunkyTortoise). Send me a message describing your CRM and what you want the bot to do — I can
scope a working prototype in one conversation.

### Skills (10 tags, ordered)

```
1. AI Chatbot Development
2. GoHighLevel (GHL)
3. ChatGPT API / Claude API
4. CRM Integration
5. Python
6. FastAPI
7. HubSpot
8. Salesforce
9. Large Language Models (LLM)
10. API Development

RATIONALE: Leads with the outcome (chatbot) and the most searched CRM platform (GHL), then
stacks the technical stack terms that validate expertise — ordered to capture both the agency
owner searching "GoHighLevel AI" and the SaaS founder searching "CRM chatbot developer."
```

### Portfolio Item Description

**EnterpriseHub + Jorge Real Estate Bots — CRM-Native AI Chatbot System**

**Problem solved**: Real estate agencies using GoHighLevel had no way to automate lead
qualification via AI while keeping CRM data synchronized — conversations happened in one place,
lead data lived in another.

**What I built**: A two-part system. EnterpriseHub provides a unified CRM adapter layer
supporting GoHighLevel, HubSpot, and Salesforce through a single protocol — a bot built on this
layer works across all three CRMs without code changes. Jorge Real Estate Bots layers three
specialized AI personalities on top: a Lead Bot that qualifies inbound leads via SMS and applies
GHL temperature tags, a Buyer Bot that assesses financial readiness and pre-approval status, and a
Seller Bot that scores listing motivation and books calendar appointments when a seller is hot.
All three bots share a handoff service with rate limiting (3 handoffs per hour, 10 per day per
contact), circular-handoff prevention, and performance-based routing. Every conversation logs
structured data to PostgreSQL and syncs to GHL in real time.

**Results/metrics:**
- 3 CRM adapters: GoHighLevel, HubSpot, Salesforce (unified protocol)
- 157 passing tests on jorge_real_estate_bots; ~5,100 tests across EnterpriseHub
- Cross-bot handoff with 0.7 confidence threshold and circular prevention
- Redis 3-tier caching, P95 latency under 300ms at 10 req/sec

**Tech used:** Python, FastAPI, GoHighLevel API, HubSpot API, Salesforce API, Claude API,
PostgreSQL, Redis, Docker, pytest, GitHub Actions

**Repo:** github.com/ChunkyTortoise/EnterpriseHub

---

## Specialized Profile 3: Multi-Agent AI Systems & LLM Orchestration

### Headline Options

```
Option A: Multi-Agent AI System Developer | LLM Orchestration, ReAct, 4.3M ops/sec | Python (89 chars)
Option B: Build AI Agent Pipelines That Scale — 4.3M Dispatches/sec, Testing-First (79 chars)
Option C: LLM Orchestration & AI Agent Developer | AutoGen Alternative, Production-Ready (85 chars)

RECOMMENDATION: Option A — includes the benchmark number (4.3M dispatches/sec) which is unusual
enough to stop a technical reader. Also hits the keyword set directly: "Multi-Agent", "LLM
Orchestration", "ReAct", "Python" — all high-volume search terms in this niche. The 89-char
length fits within the 100-char limit.
```

### Overview (Ready to Paste)

Building a single LLM call is straightforward. Building a system where ten agents coordinate,
share state, recover from failures, stay within budget, and produce auditable results — that is
an engineering problem most AI developers have not solved at scale. I have.

AgentForge, my multi-agent orchestration engine, processes 4.3 million tool dispatches per second
with under 200ms orchestration overhead (P99: 0.095ms). That number is not a benchmark artifact;
it reflects a design built around zero-copy dispatch, lock-free coordination, and agent isolation
that prevents one failing tool from cascading to the rest of the pipeline. You can try it live:
https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

**What I build for engineering teams:**

- Agent orchestrators with ReAct loop, planning, reflection, and tool-use patterns
- Multi-agent meshes with role specialization, shared memory, and result aggregation
- LLM cost optimization: 3-tier Redis semantic caching (89% cost reduction at 88% hit rate),
  circuit breakers, fallback chains, streaming with token budget enforcement
- Evaluation frameworks for non-deterministic agent behavior — the part most teams skip
- Autonomous pipelines: content generation, data processing, research, code review workflows

**Why testing-first matters for AI agents:**

Non-deterministic systems fail in non-deterministic ways. I write evaluation harnesses before
writing agent logic — adversarial inputs, edge cases, latency regression tests, cost budget
assertions. The result: 8,500+ automated tests across my portfolio, all CI green, with 33
Architecture Decision Records documenting every non-obvious design choice. When something breaks
at 2am, there is a test pointing at exactly why.

**Technical depth:**

I implement ReAct (Reasoning + Acting) loops, chain-of-thought with reflection, tool calling via
FastMCP v2 (my published PyPI package: mcp-server-toolkit), token cost tracking per agent, and
circuit breaker patterns on all external LLM calls. I have built agent systems on top of Claude
API, GPT-4, and Gemini, and I know exactly where each model breaks under pressure.

**Tech stack for agent work:**

LLMs: Claude API, GPT-4, Gemini | Orchestration: custom ReAct, FastMCP v2 | Backend: FastAPI
(async), Python 3.11+ | Caching: Redis (L1/L2/L3 semantic cache) | Testing: pytest, TDD, 80%+
coverage | Infra: Docker, GitHub Actions | Published: mcp-server-toolkit on PyPI

**Want to see it run?**

Live demo: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/ — watch the dispatch
throughput and agent coordination in real time. Describe your pipeline and I can sketch the
architecture in one message.

### Skills (10 tags, ordered)

```
1. AI Agent Development
2. Large Language Models (LLM)
3. Python
4. LLM Orchestration
5. FastAPI
6. ChatGPT API / Claude API
7. Multi-Agent Systems
8. Prompt Engineering
9. API Development
10. Machine Learning

RATIONALE: Leads with the exact role title clients search ("AI Agent Development"), then the
broadest category term (LLM), then implementation language (Python), then the differentiating
specialty (LLM Orchestration) — ordered to capture both high-volume broad searches and the
more specific niche searches from technical teams.
```

### Portfolio Item Description

**AgentForge — Production Multi-Agent AI Orchestration Engine**

**Problem solved**: Teams building multi-agent AI pipelines face a common wall: prototype agents
work in notebooks but fail in production under load, with no observability into why, no cost
controls, and no way to test non-deterministic behavior reliably.

**What I built**: AgentForge is a production-grade multi-agent orchestration engine implementing
the ReAct (Reasoning + Acting) loop pattern with role-specialized agents, shared state
management, and zero-copy tool dispatch. The core dispatch engine processes 4.3 million tool
calls per second with P99 orchestration overhead of 0.095ms — measured under sustained load, not
burst. The system includes: a 3-tier Redis semantic cache that cuts LLM costs by 89% at an 88%
cache hit rate; circuit breakers on all external model calls with configurable fallback chains;
token budget enforcement per agent run; and an evaluation framework that tests agent behavior
against adversarial inputs and regression benchmarks on every CI push. The published FastMCP v2
toolkit (mcp-server-toolkit on PyPI) handles tool registration and dispatch across the agent
mesh.

**Results/metrics:**
- 4.3M tool dispatches/sec, P99 latency 0.095ms
- 89% LLM cost reduction via semantic caching (88% hit rate)
- 8,500+ automated tests across portfolio, all CI green
- Published PyPI package: mcp-server-toolkit (FastMCP v2)
- Live interactive demo available

**Tech used:** Python, FastAPI, Claude API, GPT-4, Gemini, Redis, FastMCP v2, PostgreSQL, Docker,
pytest, GitHub Actions

**Live demo:** https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
**Repo:** github.com/ChunkyTortoise/ai-orchestrator

---

## Human Action Checklist
- [ ] Go to Upwork > Profile > Specialized Profiles > Create New
- [ ] Create Profile 1: RAG & Document AI Systems — paste headline (Option B recommended),
      overview, and 10 skills in order listed
- [ ] Create Profile 2: AI Chatbot & CRM Integration — paste headline (Option C recommended),
      overview, and 10 skills in order listed
- [ ] Create Profile 3: Multi-Agent AI Systems & LLM Orchestration — paste headline (Option A
      recommended), overview, and 10 skills in order listed
- [ ] Add portfolio item to each specialized profile using the descriptions above
- [ ] Set hourly rate on each specialized profile (can match main profile or adjust per niche)
- [ ] Add live demo URLs as external links on each specialized profile where the field exists
