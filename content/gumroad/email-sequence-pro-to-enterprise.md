# Gumroad Email Sequence: Pro to Enterprise Upsell

**Trigger**: 7 days after Pro purchase
**Goal**: Convert Pro buyers to Enterprise tier
**Products**: AgentForge ($999), DocQA Engine ($1,499), Insight Engine ($999), Scrape-and-Serve ($699)

---

## Email 1: The "You're Ready for More" Email

**Send**: 7 days after Pro purchase
**Subject Line A**: {{customer_name}}, your next step after the case studies
**Subject Line B**: From framework to production system -- what Enterprise includes

**Body**:

Hi {{customer_name}},

By now you've had a week with the Pro tier. If you've gone through the case studies, you've seen how production deployments are structured at scale.

Here's the honest truth: the framework and case studies give you 80% of what you need. The last 20% -- the part that takes the longest and costs the most in debugging time -- is deployment-specific.

That's what the **Enterprise tier** is built for:

**1. Architecture Review (2-hour deep dive)**
I review your specific codebase, identify bottlenecks, and provide a written report with prioritized recommendations. Not generic advice -- specific to your stack, your data, and your scale requirements.

**2. Dedicated Slack Channel (30 days)**
Direct async access for technical questions as you build. Average response time: under 4 hours during business days. This is where most Enterprise buyers say they got the most value -- real-time troubleshooting beats documentation every time.

**3. Deployment Runbook**
A custom deployment guide for your infrastructure. Docker, Kubernetes, bare metal -- whatever you're running. Includes CI/CD pipeline templates, monitoring setup, and alerting configuration.

**4. Priority Bug Fixes**
If you hit a framework bug during your 30-day window, it gets fixed within 48 hours. Not "we'll look into it" -- fixed and shipped.

The Enterprise tier is ${{enterprise_price}}. For context, my consulting rate is $65-75/hour, and the architecture review alone is a 2-hour engagement. Most buyers recoup the cost in the first week through avoided mistakes.

**Upgrade to Enterprise**: [{{enterprise_product_url}}]

If you want to talk it through first, reply to this email and we'll set up a 15-minute call. No pitch -- just an honest assessment of whether Enterprise makes sense for your use case.

Best,
Cayman Roden
caymanroden@gmail.com | (310) 982-0492

---

## Email 2: The ROI Email

**Send**: 14 days after Pro purchase (skip if already upgraded)
**Subject Line A**: The math on Enterprise (it's simpler than you think)
**Subject Line B**: {{customer_name}}, one architecture mistake costs more than Enterprise

**Body**:

Hi {{customer_name}},

I wanted to share a quick ROI breakdown on the Enterprise tier, because I've seen the same pattern with enough Pro buyers to know the math.

**The typical scenario:**

A Pro buyer spends 2-3 weeks debugging a deployment issue that an architecture review would have caught in 30 minutes. At a developer salary of $150K-$200K/year, that's $5,000-$8,000 in time.

**What Enterprise costs:** ${{enterprise_price}}

**What it prevents:**
- 2-3 weeks of deployment debugging (saved: $5K-$8K in developer time)
- Misconfigured caching layers (saved: 40-80% in ongoing LLM costs)
- Missing observability (saved: hours of debugging per incident)

The architecture review alone typically identifies 3-5 critical improvements. The Slack channel catches the rest in real-time as you build.

One Enterprise buyer told me the caching configuration from the architecture review cut their monthly LLM bill from $2,800 to $340. That's $29,520/year in savings from a single recommendation.

**Upgrade to Enterprise**: [{{enterprise_product_url}}]

Your Pro license is permanent regardless. But if you're building for production users, Enterprise compresses months of learning into days.

Best,
Cayman

---

## Email 3: The Final Offer Email

**Send**: 21 days after Pro purchase (skip if already upgraded)
**Subject Line A**: Last Enterprise upgrade window at this price
**Subject Line B**: {{customer_name}}, your Pro-to-Enterprise window closes Sunday

**Body**:

Hi {{customer_name}},

Final note on this -- the Pro-to-Enterprise upgrade at the current differential closes this Sunday.

After that, Enterprise goes to full price with no Pro credit applied.

Quick recap of what's included:
- 2-hour architecture review (written report with recommendations)
- 30-day Slack channel (avg <4hr response time)
- Custom deployment runbook for your infrastructure
- Priority bug fixes (48-hour SLA)

**Upgrade before Sunday**: [{{enterprise_product_url}}]

If the timing doesn't work, no problem. Your Pro license has everything you need to build and deploy. Enterprise is for teams that want to move faster with expert support.

Either way, thanks for being a customer. Reply anytime if you have questions.

Best,
Cayman

---

## Sequence Configuration

| Email | Delay | Skip Condition |
|-------|-------|---------------|
| 1 | 7 days post-Pro purchase | Never skip |
| 2 | 14 days post-Pro purchase | Skip if upgraded |
| 3 | 21 days post-Pro purchase | Skip if upgraded |

**Merge Tags**:
- `{{customer_name}}` -- Gumroad buyer's first name
- `{{product_name}}` -- Product name (AgentForge, DocQA Engine, etc.)
- `{{enterprise_price}}` -- Tier-specific: $999 / $1,499 / $999 / $699
- `{{enterprise_product_url}}` -- Direct Gumroad link to Enterprise tier

**Price Reference**:

| Product | Pro Price | Enterprise Price | Upgrade Differential |
|---------|----------|-----------------|---------------------|
| AgentForge | $199 | $999 | $800 |
| DocQA Engine | $249 | $1,499 | $1,250 |
| Insight Engine | $199 | $999 | $800 |
| Scrape-and-Serve | $149 | $699 | $550 |
