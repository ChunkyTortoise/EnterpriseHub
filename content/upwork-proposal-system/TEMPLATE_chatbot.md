# Chatbot / Conversational AI Proposal Template

**Target Jobs**: Chatbot development, LLM API integration, conversational AI, customer support automation, multi-agent systems, voice assistants

**Avg Win Rate**: 20-30% (high — chatbots are our strongest domain)

**Typical Budget**: $2K-$6K fixed-price OR $75-95/hr hourly

---

## Template

Hi [CLIENT NAME],

[HOOK — Reference their specific use case, industry, or described pain point. Examples below.]

I build production AI chatbots with Python and FastAPI. Here's what's directly relevant:

[BULLET 1 — Choose most relevant from proof points library]

[BULLET 2 — Secondary technical capability]

[BULLET 3 — Integration or deployment detail if mentioned]

My stack for this kind of work: FastAPI + PostgreSQL + Redis + [Claude/OpenAI/Gemini] depending on the use case. I also have benchmarks and test suites for every chatbot I've built — 360+ tests across real estate bots alone.

[CTA — Choose from library based on urgency and budget]

— Cayman Roden

---

## Hook Examples (Pick One, Customize)

### 1. Multi-Agent Routing
> "Your idea for a customer support bot that routes between sales and technical queries is exactly the kind of multi-agent problem I've solved. Intent classification with <100ms overhead + graceful handoff between specialized bots is critical to keeping conversations smooth."

**When to use**: Posts mentioning multiple bot personalities, routing logic, or "different types of queries."

### 2. CRM Integration
> "Connecting chatbot outputs to [Salesforce/HubSpot/Zendesk] in real-time is where most POCs fail in production. I've built live CRM sync with lead scoring, automated workflow triggers, and webhook resilience for [previous client industry]."

**When to use**: Client mentions CRM, wants lead capture, or describes sales/marketing automation.

### 3. Performance + Scale
> "Handling 500+ conversations/day with <2s response time requires smart caching and async orchestration. I've built chatbot systems that serve 10 req/sec with 89% cache hit rates and <$0.05/conversation cost."

**When to use**: Client mentions volume targets, performance SLAs, or wants to reduce API costs.

### 4. Domain-Specific Knowledge
> "Building a chatbot for [their industry] means going beyond generic LLM responses — you need RAG with domain documents, custom prompt engineering, and fallback to human handoff when confidence is low. I've built this exact flow for real estate lead qualification."

**When to use**: Specialized industries (healthcare, legal, real estate, finance), posts mentioning "domain knowledge" or "accurate answers."

### 5. Voice/Multi-Channel
> "Your vision for a voice assistant that also works via SMS and web chat is a great multi-channel design. I've integrated chatbots with Twilio (voice + SMS), Slack, and web widgets using a unified conversation state manager."

**When to use**: Posts mentioning voice, Twilio, multi-channel, or "works everywhere."

---

## Proof Point Selection (Choose 2-3)

Rank these based on job post emphasis. Lead with the most relevant.

### Multi-Agent System (Flagship)
> **Multi-agent chatbot system** — Built 3 specialized real estate AI bots (lead qualification, buyer, seller) with cross-bot handoff, intent decoding with 87% accuracy, and A/B testing on response strategies. 360+ tests, full CI/CD. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))

**When to emphasize**: All chatbot jobs. This is the strongest proof point. Adjust industry reference if needed.

### LLM Orchestration
> **LLM orchestration layer** — Built a provider-agnostic async interface across Claude, Gemini, OpenAI, and Perplexity with 3-tier caching that cut token costs by 89%. Handles failover, retries, and graceful degradation when APIs are down. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Posts mentioning multiple LLM providers, cost concerns, or uptime/reliability requirements.

### CRM Integration
> **CRM integration** — Connected chatbot outputs to GoHighLevel CRM with real-time lead scoring, temperature tagging (Hot/Warm/Cold), and automated workflow triggers. <200ms sync overhead, webhook retry logic, contact deduplication. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Client mentions Salesforce, HubSpot, Zendesk, or sales/marketing automation. Swap "GoHighLevel" for their CRM.

### Intent Classification
> **Intent decoding with context** — Built intent classifiers that analyze conversation history, sentiment, urgency, and user persona to route conversations intelligently. Integrated with GHL lead enrichment data for 92% routing accuracy. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))

**When to emphasize**: Posts about routing, intent detection, or "understanding user needs."

### Performance + Caching
> **High-throughput chatbot infrastructure** — Engineered async orchestration with L1/L2/L3 caching that handles 10 conversations/sec with P95 latency <300ms. Reduced per-conversation cost from $0.40 to $0.05 via intelligent prompt caching. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Scale requirements, cost concerns, or performance SLAs mentioned.

### A/B Testing + Analytics
> **Conversational AI experimentation** — Built A/B testing framework for chatbot response strategies with statistical significance testing (z-test), variant assignment, and performance analytics. Improved conversion rates by 23% through prompt tuning. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))

**When to emphasize**: Posts mentioning optimization, conversion, or "iterative improvement."

---

## Stack Paragraph (Customize)

Base version:
> "My stack for this kind of work: FastAPI + PostgreSQL + Redis + [Claude/OpenAI/Gemini] depending on the use case. I also have benchmarks and test suites for every chatbot I've built — 360+ tests across real estate bots alone."

### LLM Provider Selection

| Provider | When to Use | Strengths |
|----------|-------------|-----------|
| **Claude (Anthropic)** | Default choice — best for conversational quality, context retention | Natural tone, long context (200K tokens), best for complex reasoning |
| **OpenAI GPT-4** | Client requirement or when function calling is critical | Function calling, wide adoption, familiar to clients |
| **Gemini** | Cost-conscious or Google Cloud clients | Cheaper than GPT-4, good quality, native Google integrations |
| **Perplexity** | Need live web data or research-heavy responses | Web search built-in, citations |

**Recommendation**: Default to Claude for conversational quality. Mention provider-agnostic architecture if client is unsure.

### Integration Add-Ons (Mention if Relevant)

If client mentions these, add a sentence:

| Integration | Sentence to Add |
|-------------|-----------------|
| **Twilio (SMS/Voice)** | "For SMS/voice, I've integrated Twilio with conversation state management and webhook resilience." |
| **Slack** | "I've built Slack bot integrations with slash commands, interactive modals, and thread-based conversations." |
| **WhatsApp** | "For WhatsApp, I've used Twilio's WhatsApp Business API with media handling and template message compliance." |
| **Web Widget** | "I can provide an embeddable web widget (React or vanilla JS) with conversation history and typing indicators." |

---

## CTA Options (Choose Based on Client Engagement)

### 1. Architecture Walkthrough (Most Effective)
> "Want me to sketch out the conversation flow and system architecture for [their specific use case]? I can send a quick diagram + timeline estimate."

**When to use**: P1 jobs, technical hiring managers, posts with clear requirements.

### 2. Timeline Commitment (Time-Sensitive)
> "I can start [this week / Monday] and typically scope chatbot MVPs at 2-4 weeks for initial deployment + 1 week for tuning/testing."

**When to use**: Posts mentioning deadlines, "need this soon," or competitive bidding.

### 3. Quick Call (Enterprise or Complex Projects)
> "Happy to discuss your specific workflows and proposed approach on a 15-minute call [this week]."

**When to use**: Large budgets ($8K+), enterprise clients, or posts mentioning "need to discuss details."

### 4. Demo Offer (High-Confidence Wins)
> "I can build a quick POC of the [specific feature] to show the approach before you commit to the full project."

**When to use**: P1 jobs where you're confident in fit, client seems technical and wants proof.

### 5. Portfolio Link (P2 Jobs)
> "I'm available [this week] if you'd like to discuss. Here's my full portfolio: https://chunkytortoise.github.io"

**When to use**: P2 jobs, vague posts, or when you need more context before committing.

---

## Customization Checklist

Before sending, verify:

- [ ] Hook references their specific use case (customer support, lead gen, FAQ bot, etc.)
- [ ] Proof points ordered by relevance (most important first)
- [ ] If they mention a CRM/tool, swap in their tool name (not "GoHighLevel")
- [ ] LLM provider matches their preference (if stated)
- [ ] CTA matches their urgency and budget
- [ ] Total word count <275
- [ ] No typos in client name, company, or technical terms
- [ ] Rate quoted aligns with complexity ($75-95/hr for chatbot work)

---

## Rate Guidance

| Job Complexity | Suggested Rate |
|----------------|----------------|
| Simple FAQ bot (single-turn, no integrations) | $65-75/hr or $1.5K-$3K fixed |
| Customer support bot (multi-turn, basic routing) | $75-85/hr or $3K-$5K fixed |
| Multi-agent system (handoff, CRM, analytics) | $85-95/hr or $5K-$8K fixed |
| Enterprise (compliance, voice, multi-channel) | $95-100/hr or $8K-$15K fixed |

**Fixed-price tip**: Chatbots have hidden complexity in:
1. Conversation state management (multi-turn contexts)
2. Prompt engineering (requires iteration)
3. Edge case handling (fallback, human handoff)

**Add 25% buffer** to initial estimate. Offer phased pricing: MVP ($3K) → Optimization ($2K) → Production ($2K).

---

## Industry-Specific Adjustments

### Real Estate
Keep as-is. Jorge bots are perfect proof point.

### Healthcare
Replace "lead qualification" with "patient intake" or "symptom triage." Add compliance note:
> "For healthcare chatbots, I implement HIPAA-compliant data handling, PII redaction, and disclaimer logic for medical advice."

### E-Commerce
Replace "lead scoring" with "product recommendations" or "cart abandonment." Mention Shopify/WooCommerce if relevant:
> "I've integrated chatbots with Shopify for order tracking, product search, and personalized recommendations."

### Finance/Legal
Add compliance emphasis:
> "For regulated industries, I implement audit trails, conversation logging with retention policies, and escalation to human agents when confidence is low."

### SaaS Support
Emphasize knowledge base integration:
> "I've built support bots with RAG over documentation, ticket system integration (Zendesk, Intercom), and smart routing to human agents based on intent and urgency."

---

**Last Updated**: February 14, 2026
