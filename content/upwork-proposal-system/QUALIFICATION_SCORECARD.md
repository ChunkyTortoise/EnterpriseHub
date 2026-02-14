# Client Qualification Scorecard

**Purpose**: 60-second triage system to prioritize Upwork job applications

**Time Investment**: 10-15 seconds per job to score, 2-3 minutes to research P1 clients

---

## Scoring System (0-10 points)

### 1. Budget Alignment (0-3 points)

**Does the budget match our $85-100/hr target rate?**

| Score | Criteria |
|-------|----------|
| 3 | Hourly rate $80-120/hr OR project budget ≥$3K for estimated scope |
| 2 | Hourly rate $60-80/hr OR project budget $1.5K-$3K |
| 1 | Hourly rate $40-60/hr OR project budget $800-$1.5K |
| 0 | Hourly rate <$40/hr OR project budget <$800 |

**Quick check**: Fixed-price jobs → divide budget by estimated hours. If unclear, assume 30-40 hours for typical RAG/chatbot builds, 15-25 hours for dashboards.

---

### 2. Client History (0-3 points)

**Payment verified? Spending history? Reviews?**

| Score | Criteria |
|-------|----------|
| 3 | Payment verified + $10K+ spent + 4.5+ star rating (5+ reviews) |
| 2 | Payment verified + $3K-10K spent + 4.0+ star rating (3+ reviews) |
| 1 | Payment verified + $500-$3K spent OR 1-2 good reviews |
| 0 | No payment method OR no spending history OR <4.0 rating |

**Quick check**: Click client name → look for green "Payment method verified" badge, total spent, star rating in upper-right.

---

### 3. Scope Clarity (0-2 points)

**Are the requirements clear? Defined deliverables?**

| Score | Criteria |
|-------|----------|
| 2 | Specific tech stack mentioned + clear deliverables + defined success criteria |
| 1 | General description of problem + expected output, but vague on tech details |
| 0 | "Need AI expert" with no further context OR scope creep phrases ("and whatever else is needed") |

**Examples of clarity signals**:
- "Build RAG pipeline using OpenAI embeddings, pgvector, FastAPI. Deliverable: API with /query endpoint, <2s response time."
- "Chatbot for customer support using Claude API, integrate with Zendesk. Must handle 500 queries/day."

**Red flag phrases**:
- "AI/ML expert to explore solutions"
- "Long-term partnership for various projects" (without defining first project)
- "Open to suggestions on approach" (clients who don't know what they want)

---

### 4. Tech Fit (0-2 points)

**Does it match our stack and domain expertise?**

| Score | Criteria |
|-------|----------|
| 2 | Perfect match — Python + LLM + RAG/chatbots/dashboards + tools we've built |
| 1 | Partial match — Python-adjacent (Node.js backend) OR domain-adjacent (chatbots in non-real-estate) |
| 0 | No match — Mobile dev, blockchain, game dev, pure frontend, or "AI" as buzzword with no technical depth |

**Our sweet spot**:
- **Languages**: Python (FastAPI, Streamlit), SQL
- **AI/ML**: RAG, chatbots, multi-agent systems, LLM orchestration, embeddings, sentiment analysis
- **Infra**: PostgreSQL, Redis, Docker, REST APIs, webhooks
- **Integrations**: CRMs (GHL, HubSpot, Salesforce), LLM providers (Claude, OpenAI, Gemini)

**Partial fit examples**:
- Node.js backend with Python data layer (we can do Python part)
- Chatbot in finance/legal (not real estate, but same tech)
- Django instead of FastAPI (Python, different framework)

---

### 5. Red Flags (-1 each, cumulative)

**Deduct 1 point per red flag:**

| Flag | Why It Matters |
|------|---------------|
| Unverified payment method | 40%+ chance of non-payment or disputes |
| <$1K total spent on Upwork | Likely shopping for cheapest bid, not quality |
| "Test project" for free or <$100 | Spec work disguised as audition |
| "Need it done today/this weekend" | Unrealistic expectations, likely a firefight |
| Off-platform payment mention | Upwork TOS violation, no protections |
| "Training an AI" without technical details | They don't understand scope, will be unhappy with reality |
| 10+ proposals already submitted | Either low budget or poorly written post; low win rate |

---

## Decision Thresholds

| Total Score | Priority | Action |
|------------|----------|--------|
| **8-10** | **P1** | Bid within 2 hours. Research client (LinkedIn, company site), customize proposal heavily. |
| **5-7** | **P2** | Batch for later. Send proposal within 24 hours if <5 proposals submitted. Standard template with light customization. |
| **<5** | **Skip** | Move on. Not worth the time to customize. Mark "Not Interested" to clean feed. |

**Time allocation**:
- P1: 10-15 minutes per proposal (research + customization)
- P2: 5 minutes per proposal (template + quick hook)
- Skip: 0 minutes (filter out immediately)

---

## Example Scorecards

### Example 1: RAG System for Legal Documents

**Job Post Summary**:
> "Need a document Q&A system to search 5,000+ legal contracts. Must use OpenAI embeddings, pgvector for storage, FastAPI for API. Budget: $4,000 fixed-price. Deliverable: API with /query endpoint, <2s response time, deployable via Docker."

**Scoring**:
- Budget alignment: **3** — $4K for ~40hr project = $100/hr equivalent
- Client history: **3** — Payment verified, $25K spent, 4.8 stars (12 reviews)
- Scope clarity: **2** — Tech stack specified, clear deliverables, success criteria defined
- Tech fit: **2** — Perfect match (RAG, OpenAI, pgvector, FastAPI, Docker — all in our portfolio)
- Red flags: **0** — Clean post, realistic timeline, verified client

**Total: 10/10 — P1 (Bid immediately)**

**Action**: Research client's company, check if they're in legal tech space, mention DocQA engine directly, offer to sketch architecture in proposal. Reference the exact pgvector + FastAPI setup from our repo.

---

### Example 2: Chatbot for E-Commerce Support

**Job Post Summary**:
> "Looking for someone to build a chatbot for our Shopify store. Should answer product questions and handle returns. Budget: $50/hr, 20-30 hours. We use Zendesk for support tickets."

**Scoring**:
- Budget alignment: **1** — $50/hr is below our target, but project total ~$1,250 is acceptable for portfolio
- Client history: **2** — Payment verified, $4K spent, 4.2 stars (5 reviews)
- Scope clarity: **1** — General problem description, no tech stack specified, deliverable implied but not explicit
- Tech fit: **1** — Partial match (chatbot yes, but e-commerce domain vs. real estate, Zendesk integration untested)
- Red flags: **-1** — Post says "need it done in 1 week" (rushed timeline for 20-30hr project)

**Total: 4/10 — Skip**

**Reasoning**: Budget too low + rushed timeline + domain mismatch. Would require heavy research into Shopify APIs and Zendesk integration for a low-margin project. Better to wait for higher-quality jobs.

**Exception**: If we had a Shopify chatbot in portfolio or slow week, this becomes P2 (bid at $65/hr instead of $50, see if they budge).

---

### Example 3: "AI Expert Needed for Startup"

**Job Post Summary**:
> "Stealth-mode startup looking for AI/ML expert to help build our platform. Must know Python, machine learning, chatbots. Long-term partnership potential. Budget: $30-50/hr."

**Scoring**:
- Budget alignment: **0** — $30-50/hr is well below target
- Client history: **1** — Payment verified, $800 spent, no reviews
- Scope clarity: **0** — No specific problem defined, "platform" is vague, buzzword-heavy
- Tech fit: **1** — Keywords match (Python, ML, chatbots), but no concrete deliverable
- Red flags: **-2** — "Stealth mode" (no way to research), "long-term partnership" with no Phase 1 defined

**Total: 0/10 — Skip**

**Reasoning**: Classic tire-kicker post. No clear project, low budget, unproven client, buzzwords without substance. Even if they reply, scope creep is guaranteed. Hard pass.

---

## Scorecard Template (Copy-Paste for Quick Scoring)

```
Job: [Job title]
Budget: [$/hr or fixed]
Client: [Verified? Spent? Rating?]

[ ] Budget (0-3): ___
[ ] Client (0-3): ___
[ ] Scope (0-2): ___
[ ] Tech Fit (0-2): ___
[ ] Red Flags (-1 each): ___

TOTAL: ___ / 10
Priority: [P1 / P2 / Skip]
Action: [Bid now / Batch / Pass]
```

---

## Integration with Proposal Templates

Once scored, map to templates:

| Priority | Template Strategy |
|----------|------------------|
| **P1 (8-10)** | Heavy customization. Research client, mention their industry, propose specific architecture. Use CTA: "Want me to sketch out an architecture for [specific use case]?" |
| **P2 (5-7)** | Light customization. Swap in their tech stack keywords, adjust bullets to match job type. Use CTA: "I'm available [this week] if you'd like to discuss." |
| **Skip (<5)** | No proposal sent. Mark "Not Interested" to clean feed and improve job recommendations. |

---

**Last Updated**: February 14, 2026
