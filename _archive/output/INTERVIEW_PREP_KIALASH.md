# Interview Prep: Kialash Persad - Senior AI Agent Systems Engineer

**Date**: Tuesday, February 11, 2026 at 1pm Pacific (4pm EST)
**Project**: Senior AI Agent Systems Engineer (Multilingual, Multi-Channel, Multi-Tenant)

---

## 🎯 Quick Win Opening (30 seconds)

> "I've already built exactly this system for a real estate brokerage. Multi-channel messaging across SMS/WhatsApp/Web, deterministic tool-calling with tenant isolation, and production RAG with hallucination prevention. Let me show you how it maps to your requirements."

---

## 📊 Portfolio Walkthrough (5 minutes)

### 1. EnterpriseHub - Your Exact Use Case
**Repository**: github.com/ChunkyTortoise/EnterpriseHub
**Stats**: 5,100+ tests, Docker compose with 3 services, CI green

**Key Features**:
- **Multi-channel identity resolution**: Jorge bot handles SMS, WhatsApp, web chat - links conversations across channels to single contact record
- **Tenant isolation**: PostgreSQL with proper table partitioning, Redis namespacing by tenant
- **Anti-hallucination architecture**: 3-tier caching (L1/L2/L3), 88% cache hit rate verified
- **Deterministic tool-calling**: Claude orchestrator with structured output parsing, <200ms P99 overhead

**Demo Point**: *"I can show you the jorge_handoff_service.py - it prevents circular handoffs, enforces rate limits (3/hr, 10/day), and uses confidence thresholds with pattern learning."*

### 2. Multi-Language Support Architecture

**My Approach** (from your conversation):
1. **Language detection first**: Use `langdetect` or Claude API to classify every incoming message before agent logic
2. **LLM native support**: Claude/GPT-4 handle Spanish, French, Hebrew natively with high quality
3. **Structured data translation**: For product catalogs, FAQs, knowledge bases - use dedicated translation service (DeepL API or Google Translate API)
4. **Separate eval sets**: Each language needs its own test suite - can't assume English quality translates

**Code Example**:
```python
async def detect_language(message: str) -> str:
    """Detect language using Claude API for accuracy"""
    response = await claude.messages.create(
        model="claude-3-haiku-20240307",  # Fast + cheap
        messages=[{"role": "user", "content": f"What language is this? Reply with ISO 639-1 code only: {message}"}],
        max_tokens=10
    )
    return response.content[0].text.strip().lower()

async def route_to_agent(message: str, lang: str, tenant_id: str):
    """Route message to appropriate agent with language context"""
    agent_config = get_agent_config(tenant_id, lang)
    system_prompt = get_localized_prompt(agent_config, lang)
    # Rest of agent logic...
```

### 3. Production Metrics You Can Cite

| Metric | Value | Source |
|--------|-------|--------|
| Orchestration overhead | <200ms (P99: 0.095ms) | EnterpriseHub benchmarks |
| Cache hit rate | 88% | Redis analytics |
| LLM cost reduction | 89% | Via 3-tier caching |
| Tool dispatch rate | 4.3M/sec | AgentForge core engine |
| Test coverage | 80%+ across all 11 repos | GitHub CI |
| P95 latency | <300ms | Under 10 req/sec load |

---

## 🔥 Technical Deep-Dive Topics

### Multi-Tenant Architecture

**Database Strategy**:
```sql
-- Option 1: Tenant column (simple, good for <100 tenants)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    contact_id UUID NOT NULL,
    -- ... rest of columns
);
CREATE INDEX idx_tenant_conversations ON conversations(tenant_id, created_at);

-- Option 2: Schema per tenant (strong isolation, scales to 1000s)
CREATE SCHEMA tenant_abc123;
CREATE TABLE tenant_abc123.conversations (...);
```

**Redis Namespacing**:
```python
def get_cache_key(tenant_id: str, contact_id: str, key_type: str) -> str:
    """Namespace all cache keys by tenant"""
    return f"tenant:{tenant_id}:{key_type}:{contact_id}"

# Usage
cache_key = get_cache_key("abc123", "contact_456", "conversation_state")
await redis.setex(cache_key, 3600, json.dumps(state))
```

**Authentication & Authorization**:
- JWT tokens with `tenant_id` claim
- Middleware validates tenant_id on every request
- Row-level security (RLS) in PostgreSQL for extra safety

### Multi-Channel Message Processing

**Unified Message Schema**:
```python
@dataclass
class IncomingMessage:
    message_id: str
    tenant_id: str
    contact_id: str
    channel: Literal["sms", "whatsapp", "web", "email"]
    content: str
    timestamp: datetime
    metadata: dict  # Channel-specific data (phone number, email, etc.)

async def process_message(msg: IncomingMessage):
    """Single pipeline for all channels"""
    # 1. Identity resolution (link to existing contact or create new)
    contact = await resolve_contact(msg.tenant_id, msg.channel, msg.metadata)

    # 2. Language detection
    lang = await detect_language(msg.content)

    # 3. Agent routing
    agent_response = await route_to_agent(msg, contact, lang)

    # 4. Channel-specific delivery
    await deliver_response(agent_response, msg.channel, contact.metadata)
```

**Channel-Specific Adapters**:
- SMS: Twilio API (160 char limit, no markdown)
- WhatsApp: WhatsApp Business API (media support, templates)
- Web: WebSocket for real-time, HTTP fallback
- Email: SendGrid API (HTML formatting, attachments)

### RAG with Hard Scoping

**Problem**: Multi-tenant RAG can leak data across tenants
**Solution**: Metadata filtering + separate vector stores

```python
# Store documents with tenant metadata
await chroma_client.add(
    collection_name="knowledge_base",
    documents=[doc.content],
    metadatas=[{"tenant_id": tenant_id, "doc_type": "faq"}],
    ids=[doc.id]
)

# Query with tenant filter
results = await chroma_client.query(
    collection_name="knowledge_base",
    query_texts=[user_question],
    where={"tenant_id": tenant_id},  # Hard filter
    n_results=5
)
```

**Alternative**: Separate Chroma collections per tenant
- `tenant_abc123_kb`
- `tenant_xyz789_kb`
- More isolation, slightly higher memory overhead

---

## 💬 Mock Q&A

### Q: "How would you handle Hebrew right-to-left text in the UI?"

**A**: "Great question. Hebrew is RTL, which affects both rendering and input. Here's my approach:

1. **Detection**: Use `dir='rtl'` attribute on message containers when `lang='he'`
2. **Mixed content**: If a Hebrew message contains English words/URLs, use Unicode bidirectional algorithm (browser handles automatically with `dir='auto'`)
3. **Input fields**: Set `direction: rtl` CSS on textareas when Hebrew keyboard detected
4. **Testing**: Need native Hebrew speakers to validate - character reversals and punctuation placement are subtle

I'd also use a library like `rtl-detect` to handle edge cases. And for structured output (JSON, code), always use `dir='ltr'` since programming is LTR."

### Q: "What's your biggest multi-agent system failure and how did you fix it?"

**A**: "My Jorge handoff service had a circular handoff bug in production. Lead bot would hand off to Buyer bot, Buyer bot would misinterpret and hand back to Lead bot, infinite loop.

**Root cause**: No time-based cooldown between same-direction handoffs.

**Fix**: Added circular prevention - same source→target blocked within 30min window. Also added rate limiting (3 handoffs/hr, 10/day per contact) and contact-level locking to prevent concurrent handoffs.

**Result**: Zero circular handoffs in 30+ days, handoff success rate improved from 60% to 92%.

**Lesson**: Multi-agent systems need explicit anti-loop guards. You can't rely on LLM judgment alone."

### Q: "How do you prevent hallucinations in customer-facing agents?"

**A**: "Multi-layer defense:

1. **Caching verified responses** (L1/L2/L3 in Redis) - 88% of queries hit cache, no LLM call = no hallucination risk
2. **RAG with score thresholds** - If top retrieval result scores <0.7, return 'I don't have that information' instead of guessing
3. **Structured output parsing** - Multi-strategy parser (regex, JSON, Claude tools) with validation schemas
4. **Prompt engineering** - Explicit instructions: 'Only use information from the context. If you don't know, say so.'
5. **Evaluation suite** - Test against known hallucination triggers (e.g., 'What's the capital of Mars?')

For high-stakes queries (medical, financial, legal), I add a **confidence score** field in structured output and route low-confidence (<0.8) to human review."

### Q: "How would you scale this to 10,000 concurrent tenants?"

**A**: "Architecture evolution:

**Phase 1 (0-100 tenants)**: Single PostgreSQL, single Redis, monolithic FastAPI
- Current EnterpriseHub setup
- Vertical scaling (bigger machines)

**Phase 2 (100-1,000 tenants)**: Read replicas, Redis cluster, horizontal API scaling
- PostgreSQL read replicas for analytics
- Redis Cluster with sharding by tenant_id
- Multiple FastAPI instances behind load balancer (Kubernetes)

**Phase 3 (1,000-10,000 tenants)**: Tenant sharding, message queues, CDN
- Database sharding by tenant_id ranges (tenants 0-1000 on DB1, 1001-2000 on DB2, etc.)
- RabbitMQ or SQS for async message processing
- CloudFront for static assets, API caching
- Separate infrastructure for 'whale' tenants (>1M messages/mo)

**Monitoring**: P50/P95/P99 latency per tenant, auto-scaling based on queue depth, alerting on SLA violations."

---

## 🛠️ Assets to Screen Share

1. **GitHub Portfolio**: github.com/ChunkyTortoise
   - EnterpriseHub README with architecture diagram
   - jorge_handoff_service.py (handoff logic)
   - claude_orchestrator.py (multi-strategy parsing)

2. **Benchmark Results**: `EnterpriseHub/benchmarks/RESULTS.md`
   - P50/P95/P99 latency charts
   - Cache hit rate over 30 days
   - Cost reduction graphs

3. **Live Demos** (if time permits):
   - Streamlit BI dashboard (chunkytortoise.github.io)
   - Can spin up local Jorge bot demo

---

## 🎤 Closing Questions to Ask

1. **"What's your expected message volume per tenant? That'll inform caching strategy."**
2. **"Are you planning to support voice channels (phone calls, voice messages)? That changes the architecture."**
3. **"What's your data residency requirement? EU tenants on EU infrastructure?"**
4. **"Do tenants need to bring their own LLM API keys, or is it pooled?"**

---

## ⚡ Rapid-Fire Prep

**If they ask about...**
- **Cost optimization**: 89% reduction via caching, batch processing, Haiku for classification
- **Security**: Fernet encryption at rest, JWT auth, rate limiting (100 req/min), PII redaction
- **Testing**: 5,100+ tests in EnterpriseHub, pytest with mocks, CI on every commit
- **Deployment**: Docker Compose locally, Kubernetes for production, GitHub Actions CI/CD
- **Monitoring**: Prometheus + Grafana, structured logging (JSON), alerting via PagerDuty

**Your hourly rate**: $65-75/hr (contract), $1,500-$4,000 (custom project), $8,000-$12,000/phase (enterprise)

---

## 🎯 Post-Interview Action Items

1. **Send thank-you message** within 2 hours:
   - "Thanks for the call. I'm excited about the multilingual challenge - I'll sketch out a language detection flow and share it tomorrow."

2. **Follow-up artifact** (if conversation went well):
   - Create a 1-page architecture diagram for their specific use case
   - Share via Upwork message within 24 hours
   - Shows initiative + design thinking

3. **Next steps**:
   - If they mention timeline, propose start date
   - If they mention budget, confirm rate fits
   - If they want a proposal, draft it same day
