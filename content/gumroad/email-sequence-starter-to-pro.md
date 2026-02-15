# Gumroad Email Sequence: Starter to Pro Upsell

**Trigger**: 3 days after Starter purchase
**Goal**: Convert Starter buyers to Pro tier
**Products**: AgentForge, DocQA Engine, Insight Engine, Scrape-and-Serve

---

## Email 1: The "What's Next" Email

**Send**: 3 days after purchase
**Subject Line A**: {{customer_name}}, here's what Starter doesn't include
**Subject Line B**: The 3 case studies that saved one team $147K/year

**Body**:

Hi {{customer_name}},

Thanks for picking up {{product_name}} Starter -- I hope you're getting value from it.

Quick question: have you started integrating it into a production project yet?

If so, you've probably hit the point where you're wondering about deployment patterns, scaling strategies, and what production-grade usage actually looks like. That's exactly what the Starter tier doesn't cover -- by design.

The **Pro tier** fills that gap with three things I wish I'd had when I first shipped:

**1. Production Case Studies (3 detailed writeups)**
Real deployments with architecture diagrams, configuration files, and lessons learned. One case study documents how a multi-agent system achieved an 89% reduction in LLM costs through 3-tier caching -- saving over $3,200/month.

**2. 30-Minute Architecture Consultation**
A one-on-one call where we review your specific use case. I've built 11 production systems with 8,500+ tests across them. I'll help you avoid the mistakes I made so you don't burn weeks on dead-end approaches.

**3. Priority Email Support (48-hour SLA)**
Skip the community queue. Direct access to me for technical questions about integration, deployment, and scaling.

The upgrade is $150 more than what you paid for Starter. Most buyers tell me the case studies alone are worth that -- they compress months of trial-and-error into a few hours of reading.

**Upgrade to Pro**: [{{pro_product_url}}]

No pressure. Starter is a complete, production-ready framework. But if you're shipping to real users, Pro will save you time.

Best,
Cayman Roden
caymanroden@gmail.com

P.S. The 30-minute consult alone would cost $75-$100 at my hourly rate. It's included free with Pro.

---

## Email 2: The Social Proof Email

**Send**: 7 days after purchase (skip if already upgraded)
**Subject Line A**: How {{product_name}} performs in production (real numbers)
**Subject Line B**: {{customer_name}}, benchmarks from a live deployment

**Body**:

Hi {{customer_name}},

Wanted to share some real production numbers from the framework you're using.

These are from a live deployment managing a $50M+ real estate pipeline:

| Metric | Result |
|--------|--------|
| Cache hit rate | 88.1% (3-tier: L1 in-memory, L2 Redis, L3 PostgreSQL) |
| LLM cost reduction | 89% ($3,600/mo down to ~$400/mo) |
| Orchestration overhead (P99) | 0.012ms |
| Automated tests | 8,500+ across the portfolio |

The Pro tier includes the detailed case studies behind these numbers -- architecture decisions, configuration files, and the specific caching strategy that delivered the 88% hit rate.

Three case studies, each 15-20 pages with code samples and diagrams.

**Get the full story**: [{{pro_product_url}}]

Building something interesting with {{product_name}}? Reply to this email -- I read every response.

Best,
Cayman

---

## Email 3: The Deadline Email

**Send**: 14 days after purchase (skip if already upgraded)
**Subject Line A**: Last call: Pro upgrade offer expires Friday
**Subject Line B**: {{customer_name}}, your Pro upgrade window is closing

**Body**:

Hi {{customer_name}},

Quick note -- the Starter-to-Pro upgrade path at the current price closes this Friday.

After that, Pro goes to full price with no Starter credit.

What you'd get:
- 3 production case studies (one documents $147K/year in savings)
- 30-minute architecture consultation (scheduled at your convenience)
- Priority email support with 48-hour SLA

**Upgrade before Friday**: [{{pro_product_url}}]

If the timing isn't right, no worries. Your Starter license is permanent and fully functional. This is just a heads-up that the upgrade pricing won't last.

Best,
Cayman

---

## Sequence Configuration

| Email | Delay | Skip Condition |
|-------|-------|---------------|
| 1 | 3 days post-purchase | Never skip |
| 2 | 7 days post-purchase | Skip if upgraded |
| 3 | 14 days post-purchase | Skip if upgraded |

**Merge Tags**:
- `{{customer_name}}` -- Gumroad buyer's first name
- `{{product_name}}` -- AgentForge / DocQA Engine / Insight Engine / Scrape-and-Serve
- `{{pro_product_url}}` -- Direct Gumroad link to Pro tier product
