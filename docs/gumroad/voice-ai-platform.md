# Voice AI Platform

## Headline

**Production Voice AI Agent Platform -- Twilio + Deepgram + ElevenLabs + Claude**

Build real-time AI voice agents that qualify leads, book appointments, and sync with your CRM -- out of the box.

---

## Value Proposition

Stop building voice AI from scratch. This platform gives you a production-ready voice pipeline with real-time STT/TTS, multi-bot orchestration, CRM integration, and Stripe billing -- backed by 66 automated tests and Docker deployment.

Most teams spend 3-6 months building voice AI infrastructure. Ship yours this week.

---

## Features

- **Real-time voice conversations** via Twilio WebSocket media streams
- **Speech-to-Text**: Deepgram with sub-200ms latency
- **Text-to-Speech**: ElevenLabs natural voice synthesis
- **LLM Intelligence**: Claude Sonnet 4.5 conversation engine
- **Multi-bot architecture**: Lead, Buyer, and Seller qualification bots
- **Multi-tenant isolation**: PostgreSQL schema-per-tenant
- **GHL CRM sync**: Auto-sync contacts, tags, workflows, appointments
- **Stripe metered billing**: Per-call usage tracking
- **PII detection**: Automated redaction for compliance
- **Sentiment analysis**: Real-time caller sentiment scoring
- **Cost tracking**: Per-call cost breakdown (STT + TTS + LLM)
- **BI Dashboard**: Streamlit analytics with call metrics and trends

---

## Technical Specs

| Spec | Detail |
|------|--------|
| Language | Python 3.11+ |
| Framework | FastAPI (async) + SQLAlchemy |
| Voice Pipeline | Pipecat (STT-LLM-TTS orchestration) |
| STT Provider | Deepgram |
| TTS Provider | ElevenLabs |
| LLM Provider | Anthropic Claude |
| Telephony | Twilio (inbound/outbound) |
| Database | PostgreSQL 14+ |
| Cache | Redis 7+ |
| Billing | Stripe |
| Dashboard | Streamlit |
| Tests | 66 automated tests |
| Deployment | Docker + docker-compose |
| CI/CD | GitHub Actions |

---

## What You Get

### Starter -- $149

- Full source code (voice pipeline, bots, API)
- README + architecture docs
- .env.example with all config vars
- Docker deployment files
- 66 passing tests
- Community support (GitHub Issues)

### Pro -- $249

Everything in Starter, plus:

- **Deployment guide** with Twilio + Deepgram + ElevenLabs setup walkthrough
- **GHL integration guide** (custom fields, workflows, calendar sync)
- **Cost optimization playbook** (reduce per-call costs by 40-60%)
- **1-hour setup call** via Zoom
- Priority email support (48hr response)

### Enterprise -- $499

Everything in Pro, plus:

- **Custom bot personality development** (your brand voice)
- **Multi-tenant configuration** for your client base
- **Stripe billing integration** tailored to your pricing model
- **Architecture review** of your deployment
- **30-day dedicated support** via Slack channel
- **SLA**: 24hr response, 72hr bug fix

---

## Who This Is For

- **Real estate brokerages** automating lead qualification calls
- **SaaS companies** building AI phone support
- **AI agencies** delivering voice solutions to clients
- **Developers** who need production voice AI infrastructure fast

---

## FAQ

**Q: Can I swap out Deepgram/ElevenLabs for other providers?**
A: Yes. The Pipecat pipeline is provider-agnostic. Swap STT/TTS with a config change.

**Q: Does it handle concurrent calls?**
A: Yes. FastAPI async + WebSocket streams handle multiple simultaneous calls.

**Q: What about HIPAA/compliance?**
A: PII detection is built in. For HIPAA, you need BAAs with Twilio/Deepgram/ElevenLabs separately.

---

## Proof

- 66 automated tests, all passing
- Docker-ready deployment
- Built by an engineer managing $50M+ real estate pipelines with AI
- Part of an 8,500+ test portfolio across 11 production repos
