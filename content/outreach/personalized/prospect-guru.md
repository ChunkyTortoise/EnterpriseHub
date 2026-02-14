# Prospect: Guru

**Segment**: SaaS CTO | **Template**: Template 3
**Priority**: Batch 2, Week 2

---

## Company Research

Guru is an AI-powered knowledge management and sales enablement platform co-founded by Rick Nucci (CEO) and Mitchell Stewart, headquartered in Philadelphia, PA. Rick previously founded Boomi (first cloud integration PaaS, acquired by Dell in 2010). Raised $70M in total funding (Series C led by Accel, with FirstMark and Emergence Capital). Revenue reached $63M in 2023. The platform serves as an "AI Source of Truth" connecting company knowledge across tools to deliver trusted, cited answers.

## Why They're a Fit

Guru's knowledge management platform uses RAG patterns for retrieval and citation. Their "AI Source of Truth" positioning means accuracy and trust are critical -- the same priorities as the EnterpriseHub DocQA Engine. At $63M revenue, they're scaling AI operations and likely dealing with cost optimization challenges. Rick's Boomi background (integration platform) means he values clean architecture.

## Personalization Hooks

- Rick's Boomi background (acquired by Dell) shows appreciation for platform architecture
- $63M revenue means operating at significant scale
- "AI Source of Truth" positioning demands accuracy -- citation faithfulness matters
- Knowledge management has highly repetitive queries -- perfect for caching
- 10-year company anniversary shows longevity and commitment

---

## Email Sequence

### Day 1: Initial Outreach

**Subject**: Your AI pipeline is costing you 40-80% more than it should

Hi Rick,

Congrats on Guru turning 10. Building an "AI Source of Truth" that companies actually trust is a hard problem, and Guru has clearly cracked it.

Here's a thought on scaling that truth engine: knowledge management queries are among the most cacheable workloads in AI. "How does our expense policy work?" gets asked hundreds of times with slight variations. My systems exploit this pattern:

- **88% cache hit rate** via 3-tier caching (L1 in-memory, L2 Redis, L3 semantic)
- **89% LLM cost reduction** -- critical at $63M revenue where margins matter
- **Citation faithfulness: 0.88** -- every answer traceable to source documents

With your Boomi background, I think you'd appreciate the architectural approach. My $2,500 Architecture Audit scores AI systems across six dimensions with P50/P95/P99 benchmarks.

Worth a 30-minute discovery call?

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com | (310) 982-0492

### Day 4: Follow-Up

**Subject**: Re: Your AI pipeline is costing you 40-80% more than it should

Hi Rick,

Follow-up with a specific example. In knowledge management, the semantic cache layer is the biggest win:

"What's our PTO policy?" and "How many vacation days do I get?" are semantically identical but lexically different. My L3 cache detects this overlap and serves cached results. For a platform like Guru with thousands of companies, the pattern overlap across organizations is even higher.

15 minutes to discuss the caching architecture?

Cayman

### Day 8: Final Touch

**Subject**: Knowledge management AI caching architecture

I documented the 3-tier caching system that achieves 88% hit rate on knowledge queries. Directly relevant to Guru's workload. Reply "send it" if useful.

Cayman

---

## LinkedIn Messages

### Connection Request

Hi Rick -- Fellow platform builder here. Your journey from Boomi to Guru shows deep commitment to enterprise knowledge infrastructure. I build AI caching and orchestration systems (89% cost reduction). Would love to connect.

### Follow-Up Message

Thanks for connecting, Rick. Knowledge management queries are among the most cacheable AI workloads. My 3-tier system (88% hit rate) could be directly relevant to Guru's AI infrastructure. At $63M revenue, even 30-40% cost reduction on LLM operations is material. Open to a 30-minute architecture chat?
