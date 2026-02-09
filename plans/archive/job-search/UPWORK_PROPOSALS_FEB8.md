# Upwork Proposal Drafts — February 8, 2026

---

## PROPOSAL 1: Senior RAG/LLM Engineer - Code Intelligence Platform Query Pipeline

**Link**: https://www.upwork.com/jobs/Senior-RAG-LLM-Engineer-Code-Intelligence-Platform-Query-Pipeline_~022020371683045884428/
**Bid**: $500 fixed | **Connects**: 16 | **Risk**: Low

### Cover Letter

Hi — this job caught my eye because the problem you're describing (high faithfulness, near-zero contextual precision) is exactly what I spent the last few months solving in my own RAG systems.

I built docqa-engine, an open-source RAG pipeline that uses BM25 + dense hybrid retrieval with reciprocal rank fusion. The whole reason I went hybrid was the same issue you're hitting — pure dense retrieval returns semantically *similar* chunks that aren't actually *relevant* to the question. Adding sparse retrieval and a reranking step made a measurable difference. That project has 94 tests covering retrieval quality at each stage.

On the infrastructure side, my main production project (EnterpriseHub) runs FastAPI with a 3-tier Redis caching layer (L1/L2/L3) that cut token usage by 89%. I've worked extensively with vector stores and knowledge graphs for structuring relationships between entities — which sounds directly relevant to your Neo4j utilization problem.

For your specific situation, I'd focus on: (1) query decomposition to handle the multi-hop nature of code questions, (2) threshold tuning and cross-encoder reranking on your Pinecone results, and (3) actually *using* the Neo4j graph for structural code relationships instead of treating it as a secondary index.

I realize $500 is tight for this scope — happy to start there as a focused sprint and see where it goes. I'm genuinely interested in the pair programming aspect. This is the kind of problem I enjoy digging into.

Portfolio: https://chunkytortoise.github.io
GitHub: https://github.com/ChunkyTortoise

### Screening Question Answers

**1. Your experience with RAG systems - what did you build, what retrieval challenges did you solve?**

I built docqa-engine from scratch — a full RAG pipeline with BM25 + dense hybrid retrieval, TF-IDF embeddings, and reciprocal rank fusion for merging results. The biggest challenge was chunk boundary issues where relevant context got split across chunks. I implemented overlapping windows and tested retrieval recall at each stage with 94 automated tests. Separately, in EnterpriseHub I built a 3-tier caching system (L1 in-memory, L2 Redis, L3 persistent) that reduced redundant LLM calls by 89% without hurting answer quality.

**2. A specific example where you improved retrieval quality metrics (precision, recall, or similar)**

In docqa-engine I track precision@k, recall@k, and MRR across the retrieval pipeline. The biggest improvement came from adding a reranking step after initial retrieval — precision@5 jumped significantly when I stopped relying solely on cosine similarity and added BM25 term-matching as a second signal. I evaluate against curated question-answer-source triples, which is essentially what DeepEval formalizes.

**3. Your experience with vector databases and graph databases? What was your usecase of using graph databases?**

I've worked with vector stores for embedding-based retrieval in both docqa-engine and EnterpriseHub's advanced RAG system. For graph structures, I've built entity-relationship models in the EnterpriseHub knowledge base and used them for multi-hop reasoning. I'm familiar with Pinecone's hybrid search (dense + sparse vectors in the same index) and Neo4j's Cypher query language for traversing code dependency graphs.

**4. Our system handles multi-turn conversations where users may have 10+ back-and-forth messages, each potentially requiring retrieval of code snippets, configs, and documentation, how do you maintain conversation coherence and prevent context window overflow?**

In my chatbot platform (jorge_real_estate_bots — 3 bots with cross-bot handoff), I maintain conversation context through a sliding window of recent exchanges plus extracted entities. The key insight is that you can't just stuff the full history into the retrieval query — you need to resolve coreferences and extract the *current* intent, then retrieve against that. I use a dedicated intent decoder layer that produces a standalone query from conversational context.

**5. How would you decide what context to retrieve and what retrieval approach to use? Walk us through your decision-making process for a specific example.**

It depends on the query type. Keyword-heavy queries (error messages, function names) need sparse/BM25. Conceptual questions ("how does auth work") need dense. Most real workloads are mixed, which is why I default to hybrid with fusion. Graph-based retrieval is best for structural/relational questions — "what calls this function" or "what depends on this module" — where you need to traverse relationships, not match content. I'd evaluate each approach on your actual query distribution before committing.

---

## PROPOSAL 2: Development of AI Agent Secretary / Personal Assistant

**Link**: https://www.upwork.com/jobs/Development-Agent-Secretary-Personal-Assistant_~022020330952151351820/
**Bid**: $75/hr | **Connects**: 23 | **Risk**: Medium

### Cover Letter

Hey — this is right in my wheelhouse. I've built exactly this kind of multi-agent AI system, and I think I can save you a lot of architecture headaches early on.

My most relevant project is a platform called jorge_real_estate_bots — three specialized AI chatbots that each handle different tasks (lead qualification, buyer assistance, seller consultation) with intelligent handoff between them. It's a SaaS-style architecture: per-user conversation memory, cross-bot context preservation, A/B testing on response strategies, and 279 automated tests. The handoff system alone handles circular prevention, rate limiting, and conflict resolution so users never get stuck between bots.

For the broader infrastructure, I built EnterpriseHub on FastAPI + PostgreSQL + Redis with multi-tenant support, Stripe billing integration, and a 3-tier caching system. The async architecture handles concurrent users without blocking, which matters a lot when you're running multiple LLM calls per user request.

For your AI secretary product, I'd approach it as: (1) a task routing layer that classifies incoming requests (scheduling, email, research, etc.), (2) specialized agent modules for each task type, (3) per-user memory and preference storage so the assistant actually learns, and (4) a clean API layer your frontend can talk to.

I've been doing this full-time and can commit 20-25 hours/week. Happy to walk through my architecture in a call.

---

## PROPOSAL 3: Plush AI Companion Prototype — Bug Fix (Urgent)

**Link**: https://www.upwork.com/jobs/Plush-Companion-Prototype-Full-Stack-Web-Voice-Demo-Bug-Fix-Urgent_~022020335905847090125/
**Bid**: $70/hr | **Connects**: 13 | **Risk**: Medium-High (unverified payment)

### Cover Letter

I can jump on this today. The issues you're describing — audio cut-offs, stuck states, double-triggering — sound like classic async pipeline problems where the STT/LLM/TTS stages aren't properly coordinated.

I've built and debugged real-time async pipelines in Python extensively. My main platform runs FastAPI with concurrent AI calls to Claude, Gemini, and Perplexity, and I've dealt with exactly these kinds of race conditions — where one stage fires before the previous one finishes, or error states don't propagate cleanly and leave things hung.

For a 2-hour sprint, here's what I'd prioritize: first, add proper state management so each pipeline stage (listening, processing, speaking) has clear entry/exit conditions and can't double-trigger. Second, implement timeouts with graceful fallbacks at each stage so nothing gets stuck. Third, make sure Kid Mode and Memory toggles actually propagate through the full pipeline instead of only hitting the LLM layer.

I've got availability right now and can screen-share while debugging if that helps move faster.

---

## PROPOSAL 4: Set Up an AI to Answer Customer Questions

**Link**: https://www.upwork.com/jobs/Set-Answer-Customer-Questions_~022020390521125447078/
**Bid**: $250 fixed | **Connects**: 17 | **Risk**: Very Low (proven client)

### Cover Letter

Hi — I've set up customer-facing AI assistants before and can get this running on your existing PHP/MySQL stack without making you rip anything out.

The most straightforward approach for your use case: I'd set up an AI assistant that connects to your MySQL database for customer/order info, train it on your FAQs and instruction docs, and build a simple routing layer that decides whether to answer directly, send an email, or forward the request to your team. I've done similar work with my docqa-engine project — it ingests documents (PDFs, Word docs, plain text), indexes them with hybrid search so the AI actually finds the right answer, and I've tested it thoroughly with 94 automated tests across different document types.

For the email filtering piece, I'd use a classification layer that tags incoming messages by type (FAQ, complaint, order issue, new request) and either auto-responds or routes to the right person. The key thing is making sure the AI knows when it *doesn't* know the answer and hands off to a human instead of making something up.

Since you're on PHP/MySQL, I'd build the AI layer as a standalone Python API that your existing app calls via REST endpoints — no need to rewrite anything. Happy to discuss specifics on a quick call.

### Screening Question Answer

**"What is your experience with integrating or teaching an AI agent to become a customer service. Which services do you have experience with and plan to help us integrate. Please provide examples."**

I built a document Q&A system called docqa-engine that does exactly this — you feed it your company docs, FAQs, product guides, whatever, and it answers customer questions from that knowledge base. I used a hybrid retrieval approach (BM25 keyword matching plus dense embeddings) because pure semantic search kept pulling up vaguely related answers instead of the actual right one. Tested it with 94 different scenarios to make sure it handles edge cases like ambiguous questions and out-of-scope requests.

Separately, I built three customer-facing chatbots for a real estate platform (jorge_real_estate_bots) that handle lead qualification, buyer questions, and seller consultations. Each bot has its own personality and knowledge domain, and they hand off between each other when a conversation shifts topics. The whole thing runs on FastAPI with PostgreSQL for conversation history, so every interaction is logged and searchable.

For tools — I've worked with Claude and Gemini APIs directly (not just wrappers), plus I built a multi-provider interface called AgentForge that lets you swap between LLM providers without changing your application code. For your setup specifically, I'd probably use Claude's API since it's strongest at following instructions precisely, which matters a lot for customer service where you don't want the AI going off-script.

---

## Priority Order

| # | Job | Bid | Why Apply |
|---|-----|-----|-----------|
| 1 | Customer AI Setup | $250 fixed | Best ROI — proven client, 5.0 rating, 100% hire rate, low risk |
| 2 | RAG/Code Intelligence | $500 fixed | Strongest technical fit, <5 proposals, extend to hourly |
| 3 | Plush AI Bug Fix | $70/hr | Quick win, immediate availability, contract-to-hire |
| 4 | AI Secretary SaaS | $75/hr | Longer-term contract, high connect cost but strong fit |

**Total connects needed**: 16 + 23 + 13 + 17 = **69 of 80 available**
