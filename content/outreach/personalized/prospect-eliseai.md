# Prospect: EliseAI

**Segment**: PropTech Founder | **Template**: Template 2
**Priority**: Batch 1, Week 1

---

## Company Research

EliseAI is the industry-leading AI platform for housing and healthcare, founded by Minna Song (CEO) and Tony Stoyanov (CTO) in 2017. Headquartered in New York City with offices in San Francisco, Boston, and Chicago. Raised $384M in total funding (Series E at $250M) with a $2.2B valuation. Over 150 employees. They automate property management communications including tours, scheduling, maintenance, renewals, and reporting.

## Why They're a Fit

EliseAI is at massive scale and likely dealing with LLM cost challenges. Their multi-channel AI (email, text, chat, phone) creates complex orchestration needs. They could benefit from production-grade caching, multi-model orchestration, and cost optimization expertise. The fractional CTO retainer or architecture audit could identify significant savings at their scale.

## Personalization Hooks

- $2.2B valuation means they're operating at enterprise scale with enterprise costs
- Multi-channel communication (email, text, chat, phone) requires sophisticated orchestration
- Series E funding means they're focused on efficiency and profitability now
- Housing + healthcare expansion creates new AI challenges

---

## Email Sequence

### Day 1: Initial Outreach

**Subject**: Your AI pipeline is costing you 40-80% more than it should

Hi Minna,

Congrats on EliseAI's Series E -- $250M is a strong signal of the market's confidence in AI for housing.

At your scale (multi-channel AI across email, text, chat, and phone), LLM orchestration costs can become a significant line item. I've worked on this exact problem.

I built a multi-LLM orchestration system for a real estate platform that achieved:

- **89% LLM cost reduction** via 3-tier caching (88% hit rate)
- **P99 latency: 0.095ms** for multi-agent coordination
- **Zero context loss** during agent-to-agent handoffs

At EliseAI's scale, even a 30% cost reduction on LLM operations could save millions annually. My $2,500 Architecture Audit would give you a scored assessment across six categories with specific cost reduction projections.

Worth a 30-minute discovery call to see if there's a fit?

Cayman Roden
Python/AI Engineer | Fractional AI CTO
caymanroden@gmail.com | (310) 982-0492

### Day 4: Follow-Up

**Subject**: Re: Your AI pipeline is costing you 40-80% more than it should

Hi Minna,

Quick follow-up with a concrete example. In my system, the 3-tier caching strategy works like this:

- L1 (in-process): Exact match, <1ms response
- L2 (Redis): Pattern match, <5ms response
- L3 (semantic): Similar query detection, <50ms response

88% of queries hit one of these layers before touching the LLM. At EliseAI's conversation volume, the savings compound fast.

Happy to walk through the architecture in 30 minutes.

Cayman

### Day 8: Final Touch

**Subject**: Quick resource on AI cost optimization at scale

Hi Minna,

Last note. I've documented the caching architecture that achieved 89% LLM cost reduction in a production system handling a $50M+ pipeline. Happy to share the technical brief -- just reply "send it."

Cayman

---

## LinkedIn Messages

### Connection Request

Hi Minna -- Congrats on EliseAI's Series E. I build multi-LLM orchestration systems for real estate AI (89% cost reduction on my last project). Would love to connect and share notes on AI cost optimization at scale.

### Follow-Up Message

Thanks for connecting, Minna. At EliseAI's scale, LLM costs are likely a significant line item. I built a 3-tier caching system that achieved 88% cache hit rate and 89% cost reduction for a $50M+ real estate pipeline. My $2,500 Architecture Audit identifies specific savings for AI teams. Worth a quick chat?
