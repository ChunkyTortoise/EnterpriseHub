# Prospect: Dashworks

**Segment**: SaaS CTO | **Template**: Template 3
**Priority**: Batch 3, Week 3

---

## Company Research

Dashworks is an AI knowledge assistant for teams that connects to company tools (Slack, Notion, Google Drive, Jira, etc.) and answers questions using RAG. The platform acts as an AI teammate that knows your company's institutional knowledge. YC-backed (W22 batch). Founded by Ivan Zhou. Targets engineering, support, and operations teams who waste time searching for information across fragmented tools.

## Why They're a Fit

Dashworks is building a RAG-powered knowledge assistant -- the core technology overlaps with the DocQA Engine and EnterpriseHub's knowledge retrieval systems. As a YC-backed startup, they likely have a small engineering team that could benefit from fractional AI architecture support. Their multi-tool integration (Slack, Notion, Google Drive, Jira) creates complex data ingestion and retrieval challenges.

## Personalization Hooks

- YC W22 batch -- early-stage with growth ambitions
- Multi-tool RAG integration is a complex engineering challenge
- "AI teammate" positioning aligns with multi-agent architecture
- Engineering and support team focus means they serve technical buyers
- Knowledge fragmentation across tools is the exact problem RAG solves

---

## Email Sequence

### Day 1: Initial Outreach

**Subject**: Your AI pipeline is costing you 40-80% more than it should

Hi Ivan,

Dashworks' approach to connecting company knowledge across Slack, Notion, Drive, and Jira into a single AI assistant is the right product at the right time. Knowledge fragmentation is a universal pain point.

Multi-source RAG is one of the hardest problems in AI engineering. I've built production RAG systems that handle similar complexity:

- **BM25 + semantic search + re-ranking** across multiple data sources
- **3-tier caching** with 88% hit rate (knowledge queries are highly repetitive)
- **89% LLM cost reduction** -- critical for a YC startup managing burn
- **Citation faithfulness: 0.88** -- answers traced back to source documents

At the early stage, having a fractional AI architecture advisor can accelerate development without the cost of a full-time senior hire. My $2,500 Architecture Audit identifies the highest-ROI improvements in your RAG pipeline.

Worth a 30-minute discovery call?

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com | (310) 982-0492

### Day 4: Follow-Up

**Subject**: Re: Your AI pipeline is costing you 40-80% more than it should

Hi Ivan,

Follow-up with a specific insight: cross-tool knowledge retrieval benefits enormously from semantic caching.

"How does our deployment process work?" might pull from Notion docs, Slack threads, and Jira tickets. But the answer is the same 90% of the time. A semantic cache layer catches these repeat queries and serves cached results without re-querying all data sources.

15 minutes to discuss?

Cayman

### Day 8: Final Touch

**Subject**: Multi-source RAG caching architecture

I documented the caching architecture for multi-source knowledge retrieval. Reply "send it" if useful for Dashworks.

Cayman

---

## LinkedIn Messages

### Connection Request

Hi Ivan -- I build production RAG pipelines for multi-source knowledge retrieval (89% cost reduction, 88% cache hit rate). Dashworks' approach to cross-tool AI assistance is compelling. Would love to connect.

### Follow-Up Message

Thanks for connecting, Ivan. Multi-source RAG is complex -- I've built systems with BM25 + semantic search + re-ranking across multiple data sources with 88% cache hit rate. My $2,500 Architecture Audit identifies the highest-ROI improvements for RAG pipelines. Could be valuable for Dashworks at this stage. Open to a quick chat?
