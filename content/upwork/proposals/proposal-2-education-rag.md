# Proposal 2: Education RAG Development Using Open Source Models

**Job**: Education RAG Development Using Open Source Models
**Bid**: $60/hr | **Fit**: 9/10 | **Connects**: 12-16
**Status**: Ready when funded — no Connects available

---

## Cover Letter

You need a RAG pipeline that runs on open-source models, handles textbook-style content accurately, and gives students citations they can trace — not AI answers they have to trust blindly.

I've already built this. My docqa-engine ships with BM25 + dense hybrid retrieval, reciprocal rank fusion, and a reranking step — validated across 500+ automated tests covering retrieval quality, ingestion edge cases, and faithfulness scoring. Live demo: https://ct-llm-starter.streamlit.app/

For education content specifically, three things matter that generic RAG tutorials skip:

1. **Chunking for textbook structure** — equations, figures, and section references get destroyed by fixed-size chunking; I use structure-aware splitting that preserves cross-references
2. **Citation-first prompt templates** — every answer links to the source passage so students can verify, not just accept
3. **BM25 + cross-encoder reranking for terminology-heavy queries** — keyword matching outperforms pure embeddings when students ask about specific theorems or formulas

On the open-source serving side, AgentForge (my ai-orchestrator, 550+ tests) abstracts provider differences so switching between hosted APIs and local models is a config change. Docker and CI/CD are set up across all 10 repos — you'd inherit a production-grade foundation, not a demo.

Available for a 15-minute call this week — or I can walk you through the retrieval evaluation notebook if you want to see the quality measurement approach first.

**GitHub**: https://github.com/ChunkyTortoise

---

## Rewrite Notes
- Key change: Removed the "Your tech stack reads like the bill of materials" opener (flattery) and replaced with a direct problem statement naming the three education-specific requirements clients overlook; structure-aware chunking for textbooks, citation-first prompts, and terminology-aware retrieval
- Hook used: "You need a RAG pipeline that runs on open-source models, handles textbook-style content accurately, and gives students citations they can trace — not AI answers they have to trust blindly."
- Demo linked: https://ct-llm-starter.streamlit.app/
- Estimated conversion lift: Original mentioned contract-to-hire preference, which wastes words on the freelancer's preferences. Rewrite keeps focus entirely on the client's three specific problems. The evaluation notebook CTA is more relevant than a generic architecture call for a technical education buyer.
