# Proposal 1: Senior GenAI Engineer for Semantic RAG and Word-Sense Disambiguation

**Job**: Senior GenAI Engineer for Semantic RAG and Word-Sense Disambiguation
**Bid**: $65/hr | **Fit**: 9/10 | **Connects**: 12-16
**Status**: Ready when funded — no Connects available

---

## Cover Letter

You need a retrieval pipeline that returns the *correct* meaning of a phrase, not just the most semantically adjacent chunk — and standard cosine similarity can't do that for word-sense disambiguation.

My docqa-engine solves this: BM25 + dense embeddings with reciprocal rank fusion, validated across 94 automated retrieval scenarios measuring precision@k, recall@k, and MRR at every pipeline stage. That hybrid approach is what separates "returns similar text" from "returns correct meaning." Live demo: https://ct-prompt-lab.streamlit.app/

For your ASR-to-gesture disambiguation pipeline, my approach would be:

1. **Embedding strategy for short, ambiguous phrases** — standard 512-token chunking destroys context for 3-5 word ASR outputs; I'd use sliding-window embeddings tuned to short-phrase semantics
2. **Confidence-gated LLM calls** — my EnterpriseHub system routes rules-vs-LLM per request using a 0.7 confidence threshold; noisy ASR input never reaches expensive model calls unless it clears that gate
3. **Sub-50ms FAISS lookup** — I benchmark P50/P95/P99 latency across every retrieval pipeline; you'll have measured latency targets from day one

My EnterpriseHub platform (~5,100 tests) runs JSON-only LLM outputs with multi-strategy parsing and explicit fallback chains — the same deterministic control your gesture system needs.

Available for a 15-minute call this week — or I can send a working prototype of the confidence-gated retrieval layer if that's more useful.

**GitHub**: https://github.com/ChunkyTortoise

---

## Rewrite Notes
- Key change: Replaced third-person portfolio table with direct address to the client's specific technical problem (WSD + ASR pipeline); proposal now opens by naming their exact need rather than describing my background
- Hook used: "You need a retrieval pipeline that returns the *correct* meaning of a phrase, not just the most semantically adjacent chunk — and standard cosine similarity can't do that for word-sense disambiguation."
- Demo linked: https://ct-prompt-lab.streamlit.app/
- Estimated conversion lift: Original opened with "The distinction you draw..." which is a compliment; rewrite opens by diagnosing the problem. Specific mention of ASR short-phrase embedding failure mode shows the proposal was read carefully. The prototype CTA is lower-friction than a call for technical buyers.
