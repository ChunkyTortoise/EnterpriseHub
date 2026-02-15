Proposal 13: Freelance AI Developer — Custom RAG Chatbot with LLMs

Job: Freelance AI Developer — Build a Custom Retrieval-Augmented Generation (RAG) Chatbot with LLMs
Bid: $65/hr | Fit: 9/10 | Connects: TBD
Status: Submitting

---

Cover Letter:

I've built two production RAG systems, not just prototypes. Happy to share the repos.

docqa-engine (500+ tests) is a hybrid retrieval pipeline using BM25 + dense embeddings with reciprocal rank fusion. It has 94 automated retrieval quality tests that measure precision@k, recall@k, and MRR at every pipeline stage. The system includes cross-encoder re-ranking, query expansion, and multi-hop reasoning for complex document relationships. I measure retrieval quality because without metrics you're just guessing whether your chatbot is actually finding the right information.

EnterpriseHub (around 5,100 tests) runs production RAG for real estate lead qualification. It processes natural language queries like "3-bedroom house near good schools under $800K" and retrieves relevant listings, market data, and neighborhood analytics. The caching layer cuts LLM API costs by 89% with an 88% cache hit rate. Most RAG queries cluster around similar topics, so smart caching makes a massive difference on your API bill.

For your chatbot specifically, I'd start with your data format and retrieval requirements, then build the pipeline in stages: document ingestion and chunking strategy tuned to your content, hybrid retrieval with fusion weights optimized against test queries, re-ranking to push the most relevant chunks to the top, and a conversational layer with context window management so multi-turn conversations stay coherent.

I work in weekly sprint cycles with concrete deliverables each week. Everything comes with tests, Docker support, and CI/CD. Available under 30 hours/week and can start this week.

Portfolio: https://chunkytortoise.github.io
GitHub: https://github.com/ChunkyTortoise

---

Screening Question:

Q1: Describe your recent experience with similar projects
A1: I built two production RAG systems in the past year. docqa-engine is a hybrid retrieval pipeline (BM25 + dense embeddings + reciprocal rank fusion) with 500+ tests including 94 automated retrieval quality scenarios measuring precision@k, recall@k, and MRR. It includes cross-encoder re-ranking, query expansion, and multi-hop reasoning. EnterpriseHub runs production RAG for real estate lead qualification processing natural language property queries across listings, market data, and neighborhood analytics. The caching layer achieved 89% cost reduction on LLM API calls. Both repos are Docker-ready with full CI/CD pipelines.
