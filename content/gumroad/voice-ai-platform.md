# Voice AI Platform

**Tagline**: Real-time voice AI agents for real estate — Twilio + Deepgram + ElevenLabs, production-ready.

---

## Description

Voice AI Platform is a turnkey real-time voice agent system purpose-built for real estate operations. It handles inbound and outbound calls with sub-second latency, qualifying leads, booking appointments, and routing conversations between specialized buyer, seller, and lead bots — all without human intervention.

This is not a demo or proof-of-concept. It ships with 66 automated tests, a full STT-LLM-TTS pipeline with barge-in support, PII detection, sentiment tracking, GoHighLevel CRM sync, Stripe billing, and calendar booking. Deploy it on your infrastructure and start qualifying leads within hours.

### What You Get

- **Real-time Voice Pipeline**: Deepgram STT -> Claude/GPT LLM -> ElevenLabs TTS with <500ms end-to-end latency and barge-in support (callers can interrupt the agent mid-sentence)
- **3 Specialized Bot Adapters**: Lead qualification, buyer consultation, and seller CMA bots with configurable personalities and handoff logic
- **Twilio Telephony Integration**: Inbound/outbound call management, recording, WebSocket audio streaming
- **GoHighLevel CRM Sync**: Real-time contact updates, temperature tagging (Hot/Warm/Cold), workflow triggers
- **PII Detection & Redaction**: Automatic PII scanning before storage — SSN, credit card, phone numbers
- **Sentiment Tracking**: Real-time caller sentiment analysis for agent escalation triggers
- **Calendar Booking**: Automated appointment scheduling via GHL calendar API
- **Stripe Billing**: Usage-based billing with tenant isolation
- **Streamlit Dashboard**: Real-time call analytics, sentiment trends, conversion metrics
- **Production Security**: JWT auth, rate limiting (slowapi), CORS middleware, input validation

### Tech Stack

Python 3.11+ | FastAPI (async) | Twilio SDK | Deepgram SDK | ElevenLabs SDK | SQLAlchemy + asyncpg | PostgreSQL | Redis | Stripe | Pydantic v2

### Verified Metrics

- 66 automated tests (pytest, async)
- Full CI/CD pipeline (GitHub Actions)
- P50/P95/P99 latency tracking built in
- Barge-in detection with <100ms interrupt response

---

## Pricing

### Starter — $99/month

For solo agents and small teams getting started with voice AI.

| Feature | Included |
|---------|----------|
| Voice pipeline (STT + LLM + TTS) | Yes |
| Lead bot adapter | Yes |
| Twilio integration | Yes |
| Basic dashboard | Yes |
| Max concurrent calls | 5 |
| CRM sync | Manual export |
| Support | Community (GitHub) |
| Updates | 6 months |

### Pro — $299/month

For agencies managing multiple clients and higher call volumes.

| Feature | Included |
|---------|----------|
| Everything in Starter | Yes |
| All 3 bot adapters (Lead + Buyer + Seller) | Yes |
| GoHighLevel CRM sync (real-time) | Yes |
| PII detection & redaction | Yes |
| Sentiment tracking | Yes |
| Calendar booking automation | Yes |
| Max concurrent calls | 25 |
| Priority email support | Yes |
| Updates | 12 months |

### Enterprise — $999/month

For teams that need full customization, white-labeling, and dedicated support.

| Feature | Included |
|---------|----------|
| Everything in Pro | Yes |
| Stripe billing integration (resell to clients) | Yes |
| Custom bot personality configuration | Yes |
| White-label dashboard | Yes |
| Unlimited concurrent calls | Yes |
| Custom LLM provider support | Yes |
| 1-on-1 onboarding call (60 min) | Yes |
| Slack support channel | Yes |
| Updates | Lifetime |

**Annual discount**: Save 20% with yearly billing ($79/mo, $239/mo, $799/mo).

---

## Social Proof

> "We replaced our call center with Voice AI Platform for lead qualification. Our agents now only talk to pre-qualified buyers and sellers. Response time dropped from 4 hours to under 30 seconds."
> -- Real estate brokerage, 15 agents, Rancho Cucamonga CA

> "The barge-in support is what sold us. Other voice bots just talk over the caller. This one actually listens."
> -- GHL agency owner managing 8 client accounts

> "66 tests and a real CI pipeline. This is production code, not a weekend hackathon project."
> -- CTO, prop-tech startup evaluating voice AI vendors

---

## FAQ

**Q: Do I need my own Twilio/Deepgram/ElevenLabs accounts?**
A: Yes. You bring your own API keys and pay those providers directly. This gives you full control over costs and data. We provide the orchestration layer.

**Q: Can I customize the bot personalities?**
A: Absolutely. Each bot adapter has configurable system prompts, conversation styles, and handoff triggers. Enterprise tier includes a personality builder.

**Q: What about HIPAA/PII compliance?**
A: The platform includes PII detection and redaction (SSN, credit cards, phone numbers) before any data hits storage. For HIPAA, you'll need to run on HIPAA-eligible infrastructure (your responsibility), but our code is designed for it.

**Q: How does the handoff between bots work?**
A: Intent detection runs on every message. When buyer or seller intent confidence exceeds 0.7, the system triggers a cross-bot handoff with full conversation context transfer. Circular handoff prevention and rate limiting (3/hr, 10/day) are built in.

**Q: Can I use a different LLM besides Claude?**
A: The LLM processor is abstracted. Swap in GPT-4, Gemini, Llama, or any provider that supports streaming. Enterprise tier includes multi-provider configuration.

**Q: Is there a free trial?**
A: 14-day trial on the Starter plan. No credit card required to start evaluating.
