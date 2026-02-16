# Optimized Product Portfolio Specification

> **Version**: 1.0 | **Date**: 2026-02-16 | **Products**: 5 | **Total Hours**: ~395
> **Purpose**: Definitive build spec for agent execution. All code blocks are implementation-ready.
> **Companion**: See `agent-execution-plan.md` for parallel workstream assignments.

---

## Section 0: Shared Contracts & Infrastructure

All products in this portfolio share a common foundation of schemas, services, and deployment templates. Build these once; import everywhere.

### 0.1 Pydantic Schemas

#### 0.1.1 Tenant Schema

```python
# shared_schemas/tenant.py
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class TenantBase(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=256)
    slug: str = Field(..., max_length=128)
    status: TenantStatus = TenantStatus.TRIAL
    stripe_customer_id: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    settings: dict = Field(default_factory=dict)


class TenantCreate(BaseModel):
    name: str
    slug: str
    email: str
    plan: str = "free"


class TenantResponse(TenantBase):
    usage_this_period: dict = Field(default_factory=dict)
```

#### 0.1.2 Auth Schema

```python
# shared_schemas/auth.py
from pydantic import BaseModel
from uuid import UUID


class APIKeySchema(BaseModel):
    id: UUID
    tenant_id: UUID
    key_prefix: str  # first 8 chars for identification
    hashed_key: str
    name: str
    scopes: list[str] = ["read", "write"]
    rate_limit: int = 100  # requests per minute
    is_active: bool = True


class JWTPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    scopes: list[str]
    exp: int
```

#### 0.1.3 Billing Schema

```python
# shared_schemas/billing.py
from pydantic import BaseModel
from enum import Enum


class UsageEventType(str, Enum):
    VOICE_MINUTE = "voice_minute"
    RAG_QUERY = "rag_query"
    SCRAPE_REQUEST = "scrape_request"
    PROMPT_EVALUATION = "prompt_evaluation"
    AGENT_INVOCATION = "agent_invocation"


class UsageEvent(BaseModel):
    tenant_id: str
    event_type: UsageEventType
    quantity: float
    metadata: dict = {}
    timestamp: str | None = None  # ISO 8601; Stripe uses Unix


class BillingPlan(BaseModel):
    name: str
    stripe_price_id: str
    features: dict
    limits: dict  # e.g., {"voice_minutes": 500, "rag_queries": 10000}
```

### 0.2 Shared Infrastructure Services

#### 0.2.1 Stripe Billing Service

Wraps Stripe metered billing. Every product reports usage through this single service.

```python
# shared_infra/stripe_billing.py
import stripe
from shared_schemas.billing import UsageEvent


class StripeBillingService:
    """Wraps Stripe metered billing -- reuse across ALL products."""

    def __init__(self, api_key: str):
        stripe.api_key = api_key

    async def report_usage(self, event: UsageEvent) -> dict:
        """Report a usage event to Stripe's metering system."""
        return stripe.billing.MeterEvent.create(
            event_name=event.event_type.value,
            payload={
                "stripe_customer_id": event.tenant_id,
                "value": str(int(event.quantity)),
            },
        )

    async def create_subscription(self, customer_id: str, price_id: str) -> dict:
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
        )

    async def create_checkout_session(
        self, customer_id: str, price_id: str, success_url: str, cancel_url: str
    ) -> str:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url
```

#### 0.2.2 Auth Middleware

```python
# shared_infra/auth_middleware.py
import json
import hashlib
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader, HTTPBearer
from redis import asyncio as aioredis

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER = HTTPBearer(auto_error=False)


class AuthMiddleware:
    def __init__(self, redis: aioredis.Redis, db_session_factory):
        self.redis = redis
        self.db = db_session_factory

    async def verify_api_key(self, api_key: str = Security(API_KEY_HEADER)):
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        hashed = hashlib.sha256(api_key.encode()).hexdigest()
        cached = await self.redis.get(f"apikey:{hashed}")
        if cached:
            return json.loads(cached)
        # Fallback: query database, cache result for 5 min
        async with self.db() as session:
            key_record = await session.execute(
                "SELECT * FROM api_keys WHERE hashed_key = :h AND is_active = true",
                {"h": hashed},
            )
            row = key_record.fetchone()
            if not row:
                raise HTTPException(status_code=401, detail="Invalid API key")
            payload = {"tenant_id": str(row.tenant_id), "scopes": row.scopes}
            await self.redis.setex(f"apikey:{hashed}", 300, json.dumps(payload))
            return payload

    async def rate_limit(self, tenant_id: str, limit: int = 100):
        key = f"ratelimit:{tenant_id}"
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 60)
        if current > limit:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
```

### 0.3 Docker Compose Base Template

All products extend this base. Each product adds its own service definitions.

```yaml
# docker-compose.base.yml
version: "3.9"
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

### 0.4 CI/CD Template

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: pytest --cov --cov-report=xml -v
      - uses: codecov/codecov-action@v4

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy src/
```

### 0.5 Dependency Versions

All products pin to these versions for consistency.

| Package | Version | Purpose |
|---------|---------|---------|
| python | 3.11+ | Runtime |
| fastapi | 0.115.x | API framework |
| pydantic | 2.10.x | Schema validation |
| sqlalchemy | 2.0.x | ORM |
| alembic | 1.14.x | Migrations |
| redis | 5.2.x | Caching (async) |
| stripe | 11.x | Billing |
| streamlit | 1.41.x | Dashboards |
| httpx | 0.28.x | HTTP client (async) |
| pytest | 8.3.x | Testing |
| pytest-asyncio | 0.24.x | Async test support |
| docker | 7.x | Container SDK |
| mcp | 1.7.x | MCP SDK |
| deepgram-sdk | 3.x | STT/TTS |
| elevenlabs | 1.x | TTS |
| twilio | 9.x | Voice/SMS |
| pipecat-ai | 0.0.x | Voice pipeline framework |
| presidio-analyzer | 2.x | PII detection |

### 0.6 A2A Protocol Compatibility Note

Google's Agent-to-Agent (A2A) protocol is an emerging standard alongside MCP. The shared infrastructure is designed with protocol-agnostic service boundaries so that:

- **MCP servers** (Section 2) can expose A2A-compatible agent cards via a thin adapter layer.
- **Voice AI agents** (Section 1) can participate in A2A task routing by publishing an `/.well-known/agent.json` descriptor.
- **No hard dependency on A2A** is introduced at this time. The adapter pattern means A2A support can be added per-product in <8 hours when market adoption warrants it.

The key architectural constraint: all inter-service communication uses typed Pydantic models (the schemas in 0.1) so serialization to A2A's JSON-LD task format or MCP's tool-call format is a mapping exercise, not a rewrite.

---

## Section 1: Voice AI Agent Platform (160 hours)

### 1.1 Product Overview

A real-time conversational voice AI platform purpose-built for real estate. Connects Twilio phone lines to EnterpriseHub's Jorge bot engine (LeadBot, BuyerBot, SellerBot) through a streaming voice pipeline. Deployed at the edge via Fly.io for sub-500ms latency. Includes white-label packaging for GoHighLevel agencies.

**Target customers**: Real estate teams, GHL agencies, property management firms.

### 1.2 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VOICE AI PLATFORM                       │
├─────────────────────────────────────────────────────────────┤
│  Phone (Twilio) ←→ WebSocket ←→ Voice Pipeline Service      │
│                                    │                         │
│                          ┌─────────┼──────────┐             │
│                          ▼         ▼          ▼             │
│                     Deepgram    Claude/    ElevenLabs        │
│                     STT        GPT         TTS              │
│                    (Nova-3)  (Intent)    (Flash)            │
│                          │         │          │             │
│                          └─────────┼──────────┘             │
│                                    ▼                         │
│                     EnterpriseHub APIs                       │
│                     ├── LeadBot Engine                       │
│                     ├── GHL CRM Client                      │
│                     ├── Calendar Booking                     │
│                     ├── Handoff Orchestrator                 │
│                     └── Performance Tracker                  │
│                          ┌─────────┼──────────┐             │
│                          ▼         ▼          ▼             │
│                     PostgreSQL   Redis     Stripe            │
│                    (transcripts) (cache)  (billing)          │
│  Streamlit Dashboard ←── Insight Engine Components           │
└─────────────────────────────────────────────────────────────┘
```

**Two pipeline options** are supported:

1. **Pipecat Pipeline** (primary): Full control over each stage. STT, LLM, and TTS are orchestrated as discrete processors in a Pipecat DAG. Best for custom logic, multi-bot handoff, and deep EnterpriseHub integration.

2. **Deepgram Voice Agent API** (alternative): All-in-one at $4.50/hr. Deepgram handles STT + LLM orchestration + TTS in a single WebSocket. Lower implementation cost but less control over mid-call routing. Suitable for simpler deployments or as a rapid-launch option.

### 1.3 Pricing Model

Pure per-minute pricing. All infrastructure costs (STT, LLM, TTS, telephony) are bundled into a single rate.

| Tier | Rate | Commitment | Target Customer |
|------|------|-----------|-----------------|
| **Pay-as-you-go** | $0.20/min | None | Solo agents, testing |
| **Growth** | $0.15/min | 2,000 min/mo ($300/mo) | Small teams (5-20 agents) |
| **Enterprise** | $0.12/min | 10,000 min/mo ($1,200/mo) | Brokerages, call centers |
| **White-label** | $0.10/min + $2,997/mo platform fee | 10,000 min/mo included | GHL agencies reselling |

#### 1.3.1 Cost Analysis (Per-Minute Economics)

| Component | Cost/min | Source |
|-----------|----------|--------|
| Deepgram STT (Nova-3) | $0.0077 | Growth plan, per-second billing |
| ElevenLabs TTS (Flash) | ~$0.012 | ~150 chars/min agent speech at $0.08/1K chars |
| Claude LLM | ~$0.025 | ~500 input + 200 output tokens/min, Sonnet pricing |
| Twilio telephony | $0.014 | Outbound rate (blended avg) |
| Infrastructure (Fly.io + DB) | ~$0.005 | Amortized at scale |
| **Total COGS** | **~$0.064/min** | |

| Tier | Revenue/min | COGS/min | Gross Margin |
|------|------------|----------|-------------|
| Pay-as-you-go | $0.20 | $0.064 | 68% |
| Growth | $0.15 | $0.064 | 57% |
| Enterprise | $0.12 | $0.064 | 47% |
| White-label | $0.10 + platform fee amortized | $0.064 | 36% + platform fee |

#### 1.3.2 Competitive Positioning

| Competitor | Price/min | Notes |
|-----------|----------|-------|
| Vapi | $0.25-$0.33 | Plus per-component charges |
| Retell AI | $0.14 | Enterprise pricing opaque |
| Bland.ai | $0.11-$0.13 | Limited customization |
| Synthflow | $0.08-$0.12 | Template-based |
| Ringg AI | $0.08 | India-focused |
| **Ours (PAYG)** | **$0.20** | **Full EnterpriseHub integration, real estate specialized** |
| **Ours (Growth)** | **$0.15** | **Competitive with Retell, more features** |

### 1.4 Repository Structure

```
voice-ai-platform/
├── src/
│   ├── voice_ai/
│   │   ├── __init__.py
│   │   ├── config.py                 # Settings via pydantic-settings
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── calls.py              # POST /calls/initiate, GET /calls/{id}
│   │   │   ├── agents.py             # CRUD voice agent personas
│   │   │   ├── transcripts.py        # GET /transcripts
│   │   │   ├── analytics.py          # GET /analytics/calls
│   │   │   ├── webhooks.py           # Twilio status callbacks
│   │   │   └── tenants.py            # Multi-tenant management
│   │   ├── pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── voice_pipeline.py     # Pipecat pipeline orchestration
│   │   │   ├── deepgram_agent.py     # Deepgram Voice Agent API (alternative)
│   │   │   ├── stt_processor.py      # Deepgram STT integration
│   │   │   ├── tts_processor.py      # ElevenLabs TTS integration
│   │   │   ├── llm_processor.py      # Claude/GPT intent + response
│   │   │   ├── leadbot_adapter.py    # Wraps EnterpriseHub LeadBot
│   │   │   ├── buyerbot_adapter.py   # Wraps EnterpriseHub BuyerBot
│   │   │   ├── sellerbot_adapter.py  # Wraps EnterpriseHub SellerBot
│   │   │   └── handoff_manager.py    # Bot handoff (reuse orchestrator)
│   │   ├── telephony/
│   │   │   ├── __init__.py
│   │   │   ├── twilio_handler.py     # Twilio WebSocket media streams
│   │   │   ├── call_manager.py       # Call lifecycle management
│   │   │   └── recording.py          # Recording + consent handling
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── call.py               # SQLAlchemy: Call, CallTranscript
│   │   │   ├── agent_persona.py      # Voice agent configuration
│   │   │   └── call_analytics.py     # Analytics aggregation models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ghl_sync.py           # GHL CRM sync (reuse client)
│   │   │   ├── calendar_booking.py   # Appointment booking (reuse)
│   │   │   ├── sentiment_tracker.py  # Real-time sentiment analysis
│   │   │   ├── pii_detector.py       # Presidio PII scanning (embedded)
│   │   │   └── billing_service.py    # Per-minute Stripe billing
│   │   └── dashboard/
│   │       ├── __init__.py
│   │       └── call_analytics_app.py # Streamlit dashboard
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/
├── Dockerfile
├── fly.toml                           # Fly.io edge deployment
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── alembic/
```

### 1.5 Data Models

#### 1.5.1 Call Model

```python
# models/call.py
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum


class CallStatus(str, enum.Enum):
    INITIATED = "initiated"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"


class Call(Base):
    __tablename__ = "calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    twilio_call_sid = Column(String(64), unique=True, index=True)
    direction = Column(String(10))  # "inbound" | "outbound"
    from_number = Column(String(20))
    to_number = Column(String(20))
    status = Column(Enum(CallStatus), default=CallStatus.INITIATED)
    bot_type = Column(String(20))  # "lead" | "buyer" | "seller"
    duration_seconds = Column(Float, default=0)
    recording_url = Column(String(512), nullable=True)
    consent_given = Column(String(10), default="pending")  # "pending" | "yes" | "no"
    sentiment_scores = Column(JSON, default=dict)
    lead_score = Column(Float, nullable=True)
    ghl_contact_id = Column(String(64), nullable=True)
    appointment_booked = Column(String(10), default="false")

    # Cost tracking (per-call granularity)
    cost_stt = Column(Float, default=0)
    cost_tts = Column(Float, default=0)
    cost_llm = Column(Float, default=0)
    cost_telephony = Column(Float, default=0)

    # PII detection results
    pii_detected = Column(Boolean, default=False)
    pii_types_found = Column(JSON, default=list)  # e.g., ["SSN", "credit_card"]

    created_at = Column(DateTime, server_default="now()")
    ended_at = Column(DateTime, nullable=True)

    transcripts = relationship("CallTranscript", back_populates="call", lazy="selectin")


class CallTranscript(Base):
    __tablename__ = "call_transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("calls.id"), index=True)
    speaker = Column(String(10))  # "agent" | "caller"
    text = Column(String)
    timestamp_ms = Column(Float)
    confidence = Column(Float)
    is_final = Column(String(5), default="true")

    call = relationship("Call", back_populates="transcripts")
```

#### 1.5.2 Agent Persona Model

```python
# models/agent_persona.py
from sqlalchemy import Column, String, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid


class AgentPersona(Base):
    __tablename__ = "agent_personas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    bot_type = Column(String(20), nullable=False)  # "lead" | "buyer" | "seller"
    voice_id = Column(String(64))  # ElevenLabs voice ID
    language = Column(String(10), default="en")
    system_prompt_override = Column(String, nullable=True)
    greeting_message = Column(String(512), nullable=True)
    transfer_number = Column(String(20), nullable=True)  # Human fallback
    settings = Column(JSON, default=dict)  # silence_threshold, interruption_handling, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default="now()")
```

### 1.6 API Design

| Method | Path | Auth | Request | Response | Description |
|--------|------|------|---------|----------|-------------|
| POST | `/api/v1/calls/inbound` | Twilio signature | TwiML webhook | TwiML | Handle inbound call |
| POST | `/api/v1/calls/outbound` | API Key | `{to_number, bot_type, context}` | `{call_id, status}` | Initiate outbound call |
| GET | `/api/v1/calls/{call_id}` | API Key | - | `Call` | Get call details |
| GET | `/api/v1/calls/{call_id}/transcript` | API Key | - | `[CallTranscript]` | Get full transcript |
| GET | `/api/v1/calls` | API Key | `?status=&from=&to=&page=&size=` | `Paginated[Call]` | List calls with filters |
| DELETE | `/api/v1/calls/{call_id}` | API Key | - | `204` | Soft-delete call record |
| GET | `/api/v1/analytics/calls` | API Key | `?period=7d&group_by=bot_type` | `CallAnalytics` | Aggregated analytics |
| POST | `/api/v1/agents` | API Key | `AgentPersonaCreate` | `AgentPersona` | Create voice persona |
| GET | `/api/v1/agents` | API Key | - | `[AgentPersona]` | List personas |
| PUT | `/api/v1/agents/{id}` | API Key | `AgentPersonaUpdate` | `AgentPersona` | Update persona |
| DELETE | `/api/v1/agents/{id}` | API Key | - | `204` | Delete persona |
| WS | `/api/v1/voice/ws` | Twilio token | Audio frames (mulaw 8kHz) | Audio frames | Real-time voice stream |
| POST | `/api/v1/webhooks/twilio/status` | Twilio signature | Status callback | `200` | Call status updates |

### 1.7 Service Integration Specifications

#### 1.7.1 Deepgram STT (Nova-3)

```python
# pipeline/stt_processor.py
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions

class DeepgramSTTProcessor:
    """Real-time speech-to-text via Deepgram WebSocket."""

    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)

    async def create_live_connection(self, on_transcript_callback):
        options = LiveOptions(
            model="nova-3",
            encoding="linear16",
            sample_rate=16000,
            punctuate=True,
            interim_results=True,
            utterance_end_ms=1000,
            vad_events=True,
            smart_format=True,
            language="en-US",
        )
        connection = self.client.listen.asyncwebsocket.v("1")
        connection.on(LiveTranscriptionEvents.Transcript, on_transcript_callback)
        await connection.start(options)
        return connection
```

- **WebSocket URL**: `wss://api.deepgram.com/v1/listen`
- **Pricing**: $0.0077/min (Growth), per-second billing
- **Rate limits**: Up to 225 concurrent WebSocket connections on Growth plan
- **Key features**: Interim results for low-latency LLM feeding, VAD for silence detection

#### 1.7.2 ElevenLabs TTS (Flash v2.5)

```python
# pipeline/tts_processor.py
from elevenlabs.client import AsyncElevenLabs

class ElevenLabsTTSProcessor:
    """Streaming text-to-speech via ElevenLabs WebSocket."""

    def __init__(self, api_key: str, voice_id: str = "default"):
        self.client = AsyncElevenLabs(api_key=api_key)
        self.voice_id = voice_id

    async def stream_text_to_speech(self, text_chunks):
        """Stream text chunks to TTS, yield audio chunks."""
        async for audio_chunk in self.client.text_to_speech.stream(
            voice_id=self.voice_id,
            text=text_chunks,
            model_id="eleven_flash_v2_5",
            output_format="pcm_16000",
        ):
            yield audio_chunk
```

- **WebSocket URL**: `wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_flash_v2_5`
- **Pricing**: Flash at $0.08/1K chars (~75ms latency), Multilingual v2 at $0.17/1K chars (~250ms latency)
- **Model selection**: Use Flash for real-time calls (latency-sensitive), Multilingual v2 for pre-recorded/non-real-time

#### 1.7.3 Twilio Voice

```python
# telephony/twilio_handler.py
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect

class TwilioHandler:
    """Manages Twilio call lifecycle and media streams."""

    def __init__(self, account_sid: str, auth_token: str, base_url: str):
        self.client = Client(account_sid, auth_token)
        self.base_url = base_url

    def generate_stream_twiml(self, call_id: str) -> str:
        """Generate TwiML to connect call to our WebSocket."""
        response = VoiceResponse()
        connect = Connect()
        connect.stream(
            url=f"wss://{self.base_url}/api/v1/voice/ws",
            track="both_tracks",
        )
        response.append(connect)
        return str(response)

    async def initiate_outbound(self, to_number: str, from_number: str, call_id: str):
        return self.client.calls.create(
            to=to_number,
            from_=from_number,
            twiml=self.generate_stream_twiml(call_id),
            status_callback=f"https://{self.base_url}/api/v1/webhooks/twilio/status",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
            record=False,  # We handle recording after consent
        )
```

- **Media Streams**: WebSocket via `<Stream>` TwiML verb; mulaw audio at 8kHz
- **Pricing**: Inbound $0.0085/min, Outbound $0.0140/min, phone number $2.00/mo
- **Key constraint**: Audio arrives as mulaw 8kHz; must convert to linear16 16kHz for Deepgram

#### 1.7.4 Deepgram Voice Agent API (Alternative Pipeline)

```python
# pipeline/deepgram_agent.py
from deepgram import DeepgramClient

class DeepgramVoiceAgent:
    """All-in-one voice agent via Deepgram's Voice Agent API.

    Handles STT + LLM orchestration + TTS in a single WebSocket.
    Trade-off: less control, lower implementation cost.
    Pricing: ~$4.50/hr all-in ($0.075/min).
    """

    def __init__(self, api_key: str):
        self.client = DeepgramClient(api_key)

    async def create_agent_session(self, system_prompt: str, voice: str = "aura-asteria"):
        """Create a Deepgram Voice Agent session."""
        options = {
            "model": "nova-3",
            "voice": voice,
            "system_prompt": system_prompt,
            "tools": [],  # Function calling for CRM integration
        }
        connection = self.client.agent.asyncwebsocket.v("1")
        await connection.start(options)
        return connection
```

**When to use Deepgram Voice Agent API vs Pipecat**:
- Deepgram API: Rapid prototyping, simple use cases, cost-sensitive deployments
- Pipecat: Multi-bot handoff, custom LLM routing, deep EnterpriseHub integration, white-label

### 1.8 PII Detection (Presidio)

Embedded as a real-time call feature. Runs on every final transcript segment.

```python
# services/pii_detector.py
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine


class PIIDetector:
    """Real-time PII detection on call transcripts using Microsoft Presidio."""

    ENTITIES = [
        "CREDIT_CARD", "CRYPTO", "EMAIL_ADDRESS", "IBAN_CODE",
        "IP_ADDRESS", "PHONE_NUMBER", "US_SSN", "US_BANK_NUMBER",
        "PERSON", "LOCATION",
    ]

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    def detect(self, text: str, language: str = "en") -> list[RecognizerResult]:
        """Detect PII entities in transcript text."""
        return self.analyzer.analyze(
            text=text,
            entities=self.ENTITIES,
            language=language,
            score_threshold=0.7,
        )

    def redact(self, text: str, language: str = "en") -> str:
        """Redact PII from text for safe storage/logging."""
        results = self.detect(text, language)
        anonymized = self.anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized.text

    def has_sensitive_pii(self, text: str) -> tuple[bool, list[str]]:
        """Check if text contains high-risk PII (SSN, credit card, bank)."""
        high_risk = {"US_SSN", "CREDIT_CARD", "US_BANK_NUMBER", "IBAN_CODE"}
        results = self.detect(text)
        found = [r.entity_type for r in results if r.entity_type in high_risk]
        return bool(found), found
```

**Integration points**:
- Transcript storage: PII-redacted version stored by default; raw version encrypted at rest
- Real-time alerts: If SSN/credit card detected mid-call, flag for supervisor review
- Call record: `pii_detected` and `pii_types_found` fields on the Call model

### 1.9 Compliance Requirements

#### 1.9.1 Recording Consent

11 US states require two-party consent for recording (California included). The platform handles this automatically:

```python
# telephony/recording.py
CONSENT_STATES = {
    "CA", "CT", "FL", "IL", "MD", "MA", "MI", "MT", "NH", "PA", "WA"
}

CONSENT_PROMPT = (
    "This call may be recorded for quality assurance and training purposes. "
    "Do you consent to being recorded?"
)

AI_DISCLOSURE = (
    "Hi, this is Jorge, an AI assistant with {agency_name}. "
    "I'm here to help you with your real estate needs. "
)
```

- Consent prompt plays at call start before any recording begins
- AI disclosure is mandatory per TCPA for outbound calls
- Consent status tracked on `Call.consent_given` field
- If consent denied: call proceeds without recording, `consent_given = "no"`

#### 1.9.2 TCPA Compliance (Outbound)

- Prior express consent required before outbound AI calls
- AI must identify itself as artificial at call start
- Do-not-call list checking before outbound initiation
- Time-of-day restrictions: no calls before 8am or after 9pm local time

### 1.10 Latency Architecture

**Target**: < 500ms end-to-end (caller speaks -> agent responds)

```
Caller speaks          STT (streaming)       LLM (streaming)       TTS (streaming)
    │                      │                      │                      │
    ├──audio chunks──────► │                      │                      │
    │                      ├──partial transcript─► │                      │
    │                      │                      ├──token stream───────► │
    │                      │                      │                      ├──audio──► Caller hears
    │                      │                      │                      │
    │◄─────────────────────┼──────────────────────┼──────────────────────┤
    │                    ~150ms                  ~200ms                ~75ms
    │                                    Total: ~425ms (p50)
```

**Optimization strategies**:
- Pre-opened WebSocket connections to all three services (STT, LLM, TTS)
- Persistent connections reused across utterances within a call
- STT interim results fed to LLM before final transcript (speculative processing)
- Adaptive silence thresholds: 100-400ms based on conversation context
- TTS streaming starts as soon as first LLM tokens arrive
- Fly.io edge deployment: server in same region as Twilio media server

### 1.11 Fly.io Deployment

```toml
# fly.toml
app = "voice-ai-platform"
primary_region = "lax"   # Los Angeles (close to Rancho Cucamonga)

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  ENVIRONMENT = "production"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false    # Voice calls need always-on
  auto_start_machines = true
  min_machines_running = 2      # HA minimum

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

  [[services.ports]]
    port = 80
    handlers = ["http"]

[checks]
  [checks.health]
    type = "http"
    port = 8000
    path = "/health"
    interval = "10s"
    timeout = "5s"

[[vm]]
  size = "performance-2x"     # 2 vCPU, 4GB RAM
  memory = "4gb"
  cpus = 2
```

**Why Fly.io over AWS/GCP**:
- Edge deployment with <10ms to Twilio's media servers
- WebSocket-native (no ALB configuration)
- Simple scaling: `fly scale count 4` for peak hours
- Cost: ~$60/mo for 2 always-on machines vs ~$150/mo for equivalent ECS/GKE

### 1.12 White-Label for GHL Agencies

GoHighLevel agencies can resell the voice AI platform under their own brand.

#### 1.12.1 White-Label Features

| Feature | Description |
|---------|-------------|
| Custom branding | Agency logo, colors, domain on dashboard |
| Sub-account provisioning | Each agency client gets isolated tenant |
| Custom voice personas | Agency-specific voice IDs and scripts |
| Markup pricing | Agency sets their own per-minute rate to clients |
| API key management | Agency manages their clients' API keys |
| Usage dashboard | Agency sees all sub-account usage |
| GHL native integration | Direct webhook/workflow triggers in GHL |

#### 1.12.2 White-Label Pricing

- **Platform fee**: $2,997/mo (covers dashboard, support, infrastructure)
- **Per-minute rate**: $0.10/min (agency's cost)
- **Included minutes**: 10,000/min per month ($1,000 value at PAYG)
- **Agency markup**: Agencies typically resell at $0.25-$0.40/min to their clients
- **Revenue share example**: Agency with 50 clients using 500 min/mo each = 25,000 min/mo
  - Agency cost: $2,997 + (15,000 overage x $0.10) = $4,497/mo
  - Agency revenue at $0.30/min: $7,500/mo
  - Agency profit: $3,003/mo (40% margin)

#### 1.12.3 GHL Integration Points

```python
# services/ghl_sync.py (white-label extension)
class GHLWhiteLabelSync:
    """Sync voice call outcomes to GHL sub-accounts."""

    async def on_call_completed(self, call: Call):
        """Push call results to GHL contact and trigger workflows."""
        # 1. Update contact with call outcome
        await self.ghl_client.update_contact(
            contact_id=call.ghl_contact_id,
            custom_fields={
                "last_voice_call_date": call.ended_at.isoformat(),
                "voice_lead_score": call.lead_score,
                "voice_sentiment": call.sentiment_scores.get("overall"),
                "voice_appointment_booked": call.appointment_booked,
            },
        )
        # 2. Apply temperature tag based on lead score
        tag = "Hot-Lead" if call.lead_score >= 80 else "Warm-Lead" if call.lead_score >= 40 else "Cold-Lead"
        await self.ghl_client.add_tag(call.ghl_contact_id, tag)

        # 3. Trigger GHL workflow if appointment booked
        if call.appointment_booked == "true":
            await self.ghl_client.trigger_workflow(
                workflow_id="voice_appointment_booked",
                contact_id=call.ghl_contact_id,
            )
```

### 1.13 Per-Minute Billing Service

```python
# services/billing_service.py
from shared_infra.stripe_billing import StripeBillingService
from shared_schemas.billing import UsageEvent, UsageEventType


class VoiceBillingService:
    """Tracks and reports per-minute voice usage to Stripe."""

    def __init__(self, stripe_service: StripeBillingService):
        self.stripe = stripe_service

    async def report_call_usage(self, call: "Call"):
        """Report completed call minutes to Stripe metered billing."""
        minutes = call.duration_seconds / 60.0
        # Round up to nearest 0.1 minute (6-second increments)
        billable_minutes = round(minutes + 0.05, 1)

        event = UsageEvent(
            tenant_id=call.tenant_id,
            event_type=UsageEventType.VOICE_MINUTE,
            quantity=billable_minutes,
            metadata={
                "call_id": str(call.id),
                "direction": call.direction,
                "bot_type": call.bot_type,
                "duration_seconds": call.duration_seconds,
                "cost_breakdown": {
                    "stt": call.cost_stt,
                    "tts": call.cost_tts,
                    "llm": call.cost_llm,
                    "telephony": call.cost_telephony,
                },
            },
        )
        return await self.stripe.report_usage(event)
```

### 1.14 Testing Strategy

| Layer | Tool | Coverage Target | Focus |
|-------|------|----------------|-------|
| Unit | pytest + pytest-asyncio | 80% | Pipeline processors, PII detection, billing math |
| Integration | pytest + Docker services | 70% | Twilio webhook handling, DB operations, GHL sync |
| Load | locust | N/A | Concurrent call capacity, WebSocket stability |
| E2E | Playwright + Twilio test numbers | Key flows | Full call lifecycle: dial -> converse -> hangup -> billing |

**Critical test scenarios**:
1. Inbound call -> consent -> LeadBot conversation -> appointment booked -> GHL sync
2. Outbound call -> no answer -> status callback -> call record updated
3. Mid-call handoff: LeadBot -> BuyerBot (via handoff_manager)
4. PII detected mid-call -> redacted transcript stored
5. Concurrent calls: 50 simultaneous WebSocket streams
6. Billing accuracy: call duration matches Stripe usage report

---

## Section 2: MCP Server Toolkit & Marketplace (60 hours)

### 2.1 Product Overview

A collection of 7 production-ready MCP servers packaged for individual sale (Gumroad), subscription access, and consulting services. Built on an enhanced framework (`EnhancedMCP`) that adds caching, rate limiting, telemetry, and auth to the standard FastMCP base class.

**Target customers**: AI developers, agencies building AI tools, enterprise teams adopting MCP.

### 2.2 Pricing Model

| Channel | Price | Description |
|---------|-------|-------------|
| **Individual servers** (Gumroad) | $49-$149 each | One-time purchase, source code + docs |
| **All-access subscription** | $29/mo | All 7 servers + framework + updates |
| **Custom integration services** | $200-$350/hr | Setup, customization, new server development |
| **Bundle: Full toolkit** | $399 (one-time) | All 7 servers + framework (33% discount vs individual) |

**Individual server pricing**:

| Server | Price | Rationale |
|--------|-------|-----------|
| Database Query (NL to SQL) | $149 | Highest value, saves weeks of dev |
| Web Scraping | $99 | Complex anti-detection logic |
| CRM (GoHighLevel) | $149 | Niche, high-value integration |
| File Processing | $79 | PDF/CSV/Excel parsing |
| Email (IMAP/SMTP) | $79 | Standard but production-ready |
| Calendar/Scheduling | $49 | Simpler scope |
| Analytics Dashboard | $99 | Query engine + visualization |

### 2.3 Architecture

```
mcp-server-toolkit/
├── mcp_toolkit/
│   ├── framework/
│   │   ├── __init__.py
│   │   ├── base_server.py       # EnhancedMCP: FastMCP + caching + telemetry
│   │   ├── auth.py              # OAuth 2.0 + API key auth patterns
│   │   ├── caching.py           # Response caching layer (Redis-backed)
│   │   ├── rate_limiter.py      # Per-tool rate limiting
│   │   ├── telemetry.py         # OpenTelemetry instrumentation
│   │   ├── testing.py           # Test utilities for MCP servers
│   │   └── a2a_adapter.py       # A2A protocol compatibility layer
│   └── servers/
│       ├── database_query/      # Server 1: NL → SQL
│       │   ├── server.py
│       │   ├── sql_generator.py
│       │   ├── schema_inspector.py
│       │   └── tests/
│       ├── web_scraping/        # Server 2: Agent-driven scraping
│       │   ├── server.py
│       │   ├── browser_pool.py
│       │   ├── extractors.py
│       │   └── tests/
│       ├── crm_ghl/             # Server 3: GoHighLevel CRM
│       │   ├── server.py
│       │   ├── ghl_client.py
│       │   ├── contact_tools.py
│       │   └── tests/
│       ├── file_processing/     # Server 4: PDF/CSV/Excel
│       │   ├── server.py
│       │   ├── parsers.py
│       │   └── tests/
│       ├── email/               # Server 5: IMAP/SMTP
│       │   ├── server.py
│       │   ├── imap_client.py
│       │   ├── smtp_client.py
│       │   └── tests/
│       ├── calendar/            # Server 6: Booking/scheduling
│       │   ├── server.py
│       │   ├── providers/       # Google Calendar, GHL, Calendly
│       │   └── tests/
│       └── analytics/           # Server 7: Dashboard queries
│           ├── server.py
│           ├── query_engine.py
│           └── tests/
├── tests/
│   ├── framework/
│   └── integration/
├── docs/
│   ├── quickstart.md
│   ├── framework-guide.md
│   └── server-guides/          # Per-server documentation
├── pyproject.toml
├── docker-compose.yml
└── Makefile
```

### 2.4 Framework: EnhancedMCP

The core value proposition. Every server inherits from `EnhancedMCP` which adds production features to the base `FastMCP`.

```python
# framework/base_server.py
from mcp.server.fastmcp import FastMCP
from mcp_toolkit.framework.caching import CacheLayer
from mcp_toolkit.framework.rate_limiter import RateLimiter
from mcp_toolkit.framework.telemetry import TelemetryProvider


class EnhancedMCP(FastMCP):
    """Enhanced FastMCP with caching, rate limiting, and telemetry.

    All MCP servers in the toolkit inherit from this class to get
    production-grade features out of the box.
    """

    def __init__(self, name: str, **kwargs):
        super().__init__(name, **kwargs)
        self._cache = CacheLayer()
        self._rate_limiter = RateLimiter()
        self._telemetry = TelemetryProvider(name)
        self._setup_telemetry()
        self._setup_caching()

    def _setup_telemetry(self):
        """Initialize OpenTelemetry tracing and metrics."""
        self._telemetry.initialize()

    def _setup_caching(self):
        """Initialize Redis-backed response cache."""
        self._cache.initialize()

    def cached_tool(self, ttl: int = 300):
        """Decorator for tools with automatic response caching."""
        def decorator(func):
            @self.tool()
            async def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
                cached = await self._cache.get(cache_key)
                if cached:
                    return cached
                result = await func(*args, **kwargs)
                await self._cache.set(cache_key, result, ex=ttl)
                return result
            return wrapper
        return decorator

    def rate_limited_tool(self, max_calls: int = 100, window_seconds: int = 60):
        """Decorator for tools with per-caller rate limiting."""
        def decorator(func):
            @self.tool()
            async def wrapper(*args, ctx=None, **kwargs):
                caller_id = ctx.request_context.caller_id if ctx else "anonymous"
                allowed = await self._rate_limiter.check(
                    key=f"{func.__name__}:{caller_id}",
                    max_calls=max_calls,
                    window=window_seconds,
                )
                if not allowed:
                    return {"error": "Rate limit exceeded", "retry_after_seconds": window_seconds}
                return await func(*args, ctx=ctx, **kwargs)
            return wrapper
        return decorator
```

### 2.5 Server Implementations

#### 2.5.1 Server 1: Database Query (NL to SQL)

```python
# servers/database_query/server.py
from mcp.server.fastmcp import Context
from mcp_toolkit.framework.base_server import EnhancedMCP
import sqlglot

mcp = EnhancedMCP("database-query", dependencies=["sqlalchemy", "sqlglot"])


@mcp.tool()
async def query_database(
    question: str,
    database_url: str | None = None,
    ctx: Context = None,
) -> str:
    """Convert natural language to SQL and execute against connected database.

    Args:
        question: Natural language question (e.g., "How many users signed up last week?")
        database_url: Optional database URL override. Uses configured default if not provided.

    Returns:
        Formatted query results as markdown table.
    """
    db_url = database_url or ctx.request_context.lifespan_context.db_url
    schema = await get_database_schema(db_url)
    sql = await generate_sql(question, schema)
    # Validate and sanitize SQL (prevent injection, enforce read-only)
    validated = sqlglot.transpile(sql, read="postgres", write="postgres")
    if not all(stmt.strip().upper().startswith("SELECT") for stmt in validated):
        return "Error: Only SELECT queries are allowed for safety."
    results = await execute_query(validated[0], db_url)
    return format_results(results)


@mcp.tool()
async def explain_query(question: str, ctx: Context = None) -> str:
    """Generate SQL from natural language and explain the query plan without executing."""
    schema = await get_database_schema(ctx.request_context.lifespan_context.db_url)
    sql = await generate_sql(question, schema)
    plan = await get_query_plan(sql, ctx.request_context.lifespan_context.db_url)
    return f"**Generated SQL:**\n```sql\n{sql}\n```\n\n**Query Plan:**\n{plan}"


@mcp.resource("schema://tables")
async def get_schema() -> str:
    """Get database schema for context. Agents use this to understand available tables."""
    return await get_database_schema()


@mcp.resource("schema://tables/{table_name}")
async def get_table_schema(table_name: str) -> str:
    """Get schema for a specific table including columns, types, and relationships."""
    return await get_table_details(table_name)
```

#### 2.5.2 Server 3: CRM GoHighLevel

```python
# servers/crm_ghl/server.py
from mcp_toolkit.framework.base_server import EnhancedMCP

mcp = EnhancedMCP("crm-ghl", dependencies=["httpx"])


@mcp.tool()
async def search_contacts(
    query: str,
    limit: int = 20,
    filters: dict | None = None,
) -> str:
    """Search GHL contacts by name, email, phone, or custom fields.

    Args:
        query: Search term
        limit: Max results (default 20, max 100)
        filters: Optional filters like {"tag": "Hot-Lead", "pipeline_stage": "qualified"}
    """
    results = await ghl_client.search_contacts(query, limit=limit, filters=filters)
    return format_contacts(results)


@mcp.tool()
async def create_contact(
    first_name: str,
    last_name: str,
    email: str | None = None,
    phone: str | None = None,
    tags: list[str] | None = None,
    custom_fields: dict | None = None,
) -> str:
    """Create a new contact in GoHighLevel CRM."""
    contact = await ghl_client.create_contact(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        tags=tags or [],
        custom_fields=custom_fields or {},
    )
    return f"Contact created: {contact['id']} ({first_name} {last_name})"


@mcp.tool()
async def get_pipeline_summary(pipeline_id: str | None = None) -> str:
    """Get summary of deals/opportunities across pipeline stages."""
    summary = await ghl_client.get_pipeline_summary(pipeline_id)
    return format_pipeline(summary)
```

### 2.6 A2A Protocol Compatibility Layer

Google's Agent-to-Agent (A2A) protocol enables agents to discover and communicate with each other. The adapter layer allows MCP servers to optionally expose themselves as A2A-compatible agents.

```python
# framework/a2a_adapter.py
from dataclasses import dataclass, field
from typing import Any


@dataclass
class A2AAgentCard:
    """Agent card descriptor per A2A spec (/.well-known/agent.json)."""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: list[str] = field(default_factory=list)
    skills: list[dict[str, Any]] = field(default_factory=list)
    authentication: dict = field(default_factory=lambda: {"schemes": ["bearer"]})

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": True,
            },
            "skills": self.skills,
            "authentication": self.authentication,
        }


class A2AAdapter:
    """Wraps an EnhancedMCP server to expose A2A-compatible endpoints.

    This is an optional adapter -- MCP servers work without it.
    Enable when A2A interop is needed (e.g., multi-vendor agent ecosystems).
    """

    def __init__(self, mcp_server: "EnhancedMCP"):
        self.server = mcp_server
        self.agent_card = self._build_card()

    def _build_card(self) -> A2AAgentCard:
        """Auto-generate A2A agent card from MCP server metadata."""
        tools = self.server.list_tools()
        skills = [
            {
                "id": tool.name,
                "name": tool.name,
                "description": tool.description,
                "inputModes": ["text"],
                "outputModes": ["text"],
            }
            for tool in tools
        ]
        return A2AAgentCard(
            name=self.server.name,
            description=f"MCP server: {self.server.name}",
            url=f"https://{self.server.name}.example.com",
            skills=skills,
        )

    def get_agent_card(self) -> dict:
        """Return the /.well-known/agent.json response."""
        return self.agent_card.to_dict()
```

**Implementation scope**: The adapter is a read-only bridge. MCP remains the primary protocol for tool execution. A2A support is limited to agent discovery (agent cards) and task status reporting. Full A2A task execution is deferred until the protocol stabilizes further.

### 2.7 Testing Strategy

```python
# framework/testing.py
from mcp_toolkit.framework.base_server import EnhancedMCP
from unittest.mock import AsyncMock


class MCPTestClient:
    """Test client for MCP servers. Simulates tool calls without network."""

    def __init__(self, server: EnhancedMCP):
        self.server = server

    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """Call a tool by name with keyword arguments."""
        tool = self.server.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return await tool.fn(**kwargs)

    async def get_resource(self, uri: str) -> str:
        """Fetch a resource by URI."""
        resource = self.server.get_resource(uri)
        if not resource:
            raise ValueError(f"Resource '{uri}' not found")
        return await resource.fn()


# Example test
async def test_database_query_rejects_write():
    """Verify that write queries are blocked."""
    from servers.database_query.server import mcp as db_server

    client = MCPTestClient(db_server)
    result = await client.call_tool(
        "query_database",
        question="Delete all users",
        database_url="postgresql://test:test@localhost/test_db",
    )
    assert "Only SELECT queries are allowed" in result
```

**Coverage targets per server**:

| Server | Unit | Integration | Notes |
|--------|------|-------------|-------|
| Database Query | 85% | 70% | SQL injection prevention critical |
| Web Scraping | 75% | 60% | Mock external sites |
| CRM GHL | 80% | 65% | Mock GHL API responses |
| File Processing | 85% | 70% | Test with real PDF/CSV/Excel fixtures |
| Email | 80% | 60% | Mock IMAP/SMTP servers |
| Calendar | 80% | 65% | Mock provider APIs |
| Analytics | 80% | 70% | Test query aggregation logic |

### 2.8 Marketplace & Distribution

| Channel | Format | Delivery |
|---------|--------|----------|
| **Gumroad** | ZIP with source + docs | Individual servers or full bundle |
| **GitHub** | Private repo access | Subscription customers get repo invite |
| **MCP Registry** | Published server entries | Free discovery, links to Gumroad for purchase |
| **Consulting** | Custom engagement | Hourly billing via Stripe |

**Gumroad product structure** (per server):
```
database-query-mcp-server.zip
├── README.md              # Quick start guide
├── src/
│   └── (server source)
├── tests/
├── docker-compose.yml     # One-command local setup
├── .env.example
└── LICENSE                # Commercial license
```

### 2.9 MCP Protocol Compatibility

Built against the 2025-06-18 MCP specification. Key features used:

| Feature | Status | Usage |
|---------|--------|-------|
| Streamable HTTP transport | Implemented | Replaces SSE for all servers |
| Structured tool output | Implemented | Rich JSON responses with metadata |
| Resource links | Implemented | Schema discovery, documentation |
| OAuth 2.0 server auth | Implemented | For servers accessing protected APIs (GHL, email) |
| Elicitation | Planned | Interactive multi-step tool workflows |

**SDK**: `mcp` 1.7.x (Python). Uses `FastMCP` class with decorators for tool/resource registration.

---
# SECTION 3: AI DevOps Suite

**Effort**: 55 hours | **Type**: Merged Micro-SaaS Product | **Revenue Model**: Subscription + Usage

Combines three originally separate products into a single, unified platform:
- Agent Monitoring Dashboard (from insight-engine + AgentForge)
- Web Data Pipeline API (from scrape-and-serve)
- Prompt Registry (from prompt-engineering-lab)

Single repo. Single deployment. Unified auth. One subscription.

## 3.1 Pricing

| Tier | Price | Agents | Pipelines | Prompts | Retention | Support |
|------|-------|--------|-----------|---------|-----------|---------|
| **Starter** | $49/mo | 5 | 3 | 50 | 7 days | Email |
| **Pro** | $99/mo | 25 | 15 | 500 | 30 days | Priority email |
| **Team** | $199/mo | Unlimited | Unlimited | Unlimited | 90 days | Slack + SLA |

All tiers include: unified dashboard, API access, webhook integrations, basic alerting.

**Add-ons** (Pro and Team only):
- Extended retention (1 year): +$29/mo
- PII redaction on pipeline data: +$19/mo
- Custom anomaly detection models: +$49/mo
- SSO/SAML: +$49/mo (Team only)

**Free trial**: 14 days, Pro tier, no credit card required.

## 3.2 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Unified Dashboard (Streamlit)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Agent Monitor │  │ Data Pipeline│  │Prompt Registry│  │
│  │   Panels      │  │   Panels     │  │   Panels      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
└─────────┼──────────────────┼──────────────────┼─────────┘
          │                  │                  │
┌─────────▼──────────────────▼──────────────────▼─────────┐
│                   FastAPI Backend                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ /api/monitor  │  │ /api/pipeline│  │ /api/prompts  │  │
│  │  - ingest     │  │  - jobs      │  │  - versions   │  │
│  │  - metrics    │  │  - schedules │  │  - experiments│  │
│  │  - alerts     │  │  - extract   │  │  - analytics  │  │
│  │  - dashboards │  │  - webhooks  │  │  - teams      │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └──────────────────┼──────────────────┘         │
│                    ┌───────▼────────┐                    │
│                    │  Shared Layer   │                    │
│                    │ - Auth (JWT)    │                    │
│                    │ - Billing       │                    │
│                    │ - Rate Limiting │                    │
│                    │ - Audit Log     │                    │
│                    └───────┬────────┘                    │
└────────────────────────────┼────────────────────────────┘
                     ┌───────▼────────┐
                     │ PostgreSQL     │
                     │ + Redis Cache  │
                     └────────────────┘
```

## 3.3 Repository Structure

```
ai-devops-suite/
├── src/
│   ├── devops_suite/
│   │   ├── __init__.py
│   │   ├── config.py                 # Unified configuration
│   │   ├── main.py                   # FastAPI entrypoint
│   │   │
│   │   ├── auth/
│   │   │   ├── jwt_handler.py        # JWT issuance + validation
│   │   │   ├── api_keys.py           # API key management
│   │   │   ├── rbac.py               # Role-based access control
│   │   │   └── middleware.py          # Auth middleware
│   │   │
│   │   ├── monitor/                   # === Agent Monitoring ===
│   │   │   ├── api/
│   │   │   │   ├── ingest.py         # POST /events (telemetry ingestion)
│   │   │   │   ├── dashboards.py     # GET /dashboards, /metrics
│   │   │   │   └── alerts.py         # Alert configuration CRUD
│   │   │   ├── core/
│   │   │   │   ├── metrics.py        # Metric aggregation (reuse perf tracker)
│   │   │   │   ├── anomaly.py        # Anomaly detection (reuse insight-engine)
│   │   │   │   └── alerts.py         # Threshold + anomaly alerting engine
│   │   │   └── models.py             # AgentEvent, MetricSeries, AlertRule
│   │   │
│   │   ├── pipeline/                  # === Web Data Pipeline ===
│   │   │   ├── api/
│   │   │   │   ├── jobs.py           # CRUD scraping jobs
│   │   │   │   ├── schedules.py      # Cron scheduling
│   │   │   │   ├── extractions.py    # LLM extraction configs
│   │   │   │   └── webhooks.py       # Delivery webhooks
│   │   │   ├── core/
│   │   │   │   ├── scraper.py        # Reuse scrape-and-serve framework
│   │   │   │   ├── extractor.py      # LLM structured extraction
│   │   │   │   ├── scheduler.py      # APScheduler or Celery Beat
│   │   │   │   └── quality.py        # Data quality checks (reuse)
│   │   │   └── models.py             # Job, Schedule, Extraction, Webhook
│   │   │
│   │   ├── prompts/                   # === Prompt Registry ===
│   │   │   ├── api/
│   │   │   │   ├── prompts.py        # CRUD prompts with versioning
│   │   │   │   ├── experiments.py    # A/B test configuration
│   │   │   │   ├── analytics.py      # Usage analytics
│   │   │   │   └── teams.py          # Team management
│   │   │   ├── core/
│   │   │   │   ├── versioning.py     # Git-like prompt versioning (reuse)
│   │   │   │   ├── ab_testing.py     # A/B testing service (reuse)
│   │   │   │   ├── safety.py         # Safety checker (reuse)
│   │   │   │   └── templates.py      # Template management (reuse)
│   │   │   └── models.py             # Prompt, Version, Experiment, Team
│   │   │
│   │   ├── billing/
│   │   │   ├── stripe_service.py     # Subscription + usage metering
│   │   │   └── usage_tracker.py      # Per-feature usage tracking
│   │   │
│   │   ├── shared/
│   │   │   ├── database.py           # SQLAlchemy setup + migrations
│   │   │   ├── cache.py              # Redis caching layer
│   │   │   ├── rate_limiter.py       # Token bucket rate limiting
│   │   │   └── audit_log.py          # Unified audit trail
│   │   │
│   │   └── dashboard/
│   │       ├── app.py                # Streamlit main app
│   │       ├── pages/
│   │       │   ├── agent_overview.py  # Agent health + latency panels
│   │       │   ├── pipeline_status.py # Job runs + data quality
│   │       │   ├── prompt_lab.py      # Prompt versions + experiments
│   │       │   └── settings.py        # Billing, API keys, team mgmt
│   │       └── components/
│   │           ├── metric_card.py
│   │           ├── time_series.py
│   │           └── alert_feed.py
│   │
├── tests/
│   ├── test_monitor/
│   ├── test_pipeline/
│   ├── test_prompts/
│   ├── test_auth/
│   ├── test_billing/
│   └── conftest.py
├── alembic/
│   └── versions/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 3.4 Key Metrics (Agent Monitoring Module)

| Metric | Aggregation | Retention |
|--------|-------------|-----------|
| Agent latency P50/P95/P99 | 1min, 5min, 1hr buckets | Per plan |
| Token usage per agent | Per-request, daily rollup | Per plan |
| Cost per agent (USD) | Daily, weekly, monthly | Per plan |
| Success rate | Rolling 5min, 1hr, 24hr | Per plan |
| Error categorization | By type, agent, model | Per plan |
| Model usage distribution | Per agent, global | Per plan |

### Telemetry Ingestion API

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class EventType(str, Enum):
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_ERROR = "agent.error"
    LLM_CALL = "llm.call"
    TOOL_CALL = "tool.call"
    TOKEN_USAGE = "token.usage"

class AgentEvent(BaseModel):
    event_type: EventType
    agent_id: str
    trace_id: str
    timestamp: datetime
    duration_ms: float | None = None
    model: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost_usd: float | None = None
    status: str | None = None  # "success", "error", "timeout"
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict | None = None

# Ingestion endpoint — batched for efficiency
@router.post("/api/monitor/events")
async def ingest_events(
    events: list[AgentEvent],
    api_key: str = Depends(verify_api_key),
):
    """Ingest up to 1000 events per batch. Rate limit: 100 req/s."""
    if len(events) > 1000:
        raise HTTPException(400, "Max 1000 events per batch")

    await metrics_service.process_events(events, tenant_id=api_key.tenant_id)
    return {"accepted": len(events)}
```

### Anomaly Detection

```python
class AnomalyDetector:
    """Reuses insight-engine statistical methods."""

    def __init__(self, sensitivity: float = 2.0):
        self.sensitivity = sensitivity  # Std deviations for threshold

    def detect(
        self, metric_name: str, current_value: float, history: list[float]
    ) -> AnomalyResult:
        mean = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 0

        z_score = (current_value - mean) / stdev if stdev > 0 else 0
        is_anomaly = abs(z_score) > self.sensitivity

        return AnomalyResult(
            metric=metric_name,
            value=current_value,
            expected=mean,
            z_score=z_score,
            is_anomaly=is_anomaly,
            severity="critical" if abs(z_score) > 3 else "warning",
        )
```

## 3.5 Web Data Pipeline Module

### Job Configuration

```python
class ScrapingJob(BaseModel):
    name: str
    url_pattern: str                    # URL or pattern with {page} placeholders
    extraction_schema: dict             # JSON Schema for structured output
    llm_model: str = "gpt-4o-mini"     # Model for extraction
    schedule: str | None = None         # Cron expression
    webhook_url: str | None = None      # Delivery endpoint
    retry_policy: RetryPolicy = RetryPolicy()
    quality_checks: list[QualityCheck] = []

class RetryPolicy(BaseModel):
    max_retries: int = 3
    backoff_seconds: int = 60
    retry_on: list[str] = ["timeout", "rate_limit", "server_error"]

class QualityCheck(BaseModel):
    field: str
    check: str  # "not_null", "regex", "range", "unique"
    params: dict = {}
```

### Pipeline API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/pipeline/jobs` | Create scraping job |
| GET | `/api/pipeline/jobs` | List jobs |
| GET | `/api/pipeline/jobs/{id}` | Get job details + run history |
| POST | `/api/pipeline/jobs/{id}/run` | Trigger manual run |
| PUT | `/api/pipeline/jobs/{id}` | Update job config |
| DELETE | `/api/pipeline/jobs/{id}` | Delete job |
| GET | `/api/pipeline/jobs/{id}/results` | Get extraction results |
| POST | `/api/pipeline/schedules` | Create cron schedule |
| GET | `/api/pipeline/schedules` | List schedules |
| DELETE | `/api/pipeline/schedules/{id}` | Delete schedule |
| POST | `/api/pipeline/webhooks` | Register delivery webhook |
| GET | `/api/pipeline/webhooks` | List webhooks |

## 3.6 Prompt Registry Module

### Prompt Versioning

```python
class PromptVersion(BaseModel):
    prompt_id: str
    version: int               # Auto-incrementing
    content: str               # The prompt template
    variables: list[str]       # Extracted template variables
    model_hint: str | None     # Recommended model
    tags: list[str] = []
    created_by: str
    created_at: datetime
    parent_version: int | None  # For branching support
    changelog: str | None

class PromptExperiment(BaseModel):
    experiment_id: str
    prompt_id: str
    variants: list[ExperimentVariant]  # Each with version_id + traffic %
    metric: str                         # "latency", "quality_score", "cost"
    status: str                         # "draft", "running", "completed"
    significance_threshold: float = 0.95
    min_samples: int = 100
    started_at: datetime | None
    completed_at: datetime | None

class ExperimentVariant(BaseModel):
    name: str                   # "control", "variant_a", "variant_b"
    version_id: int
    traffic_percentage: float   # 0.0-1.0, all variants must sum to 1.0
    samples: int = 0
    metric_values: list[float] = []
```

### Prompt API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/prompts/` | Create prompt |
| GET | `/api/prompts/` | List prompts (with search) |
| GET | `/api/prompts/{id}` | Get prompt (latest version) |
| GET | `/api/prompts/{id}/versions` | List all versions |
| GET | `/api/prompts/{id}/versions/{v}` | Get specific version |
| POST | `/api/prompts/{id}/versions` | Create new version |
| POST | `/api/prompts/{id}/render` | Render template with variables |
| POST | `/api/prompts/experiments` | Create A/B experiment |
| GET | `/api/prompts/experiments/{id}` | Get experiment results |
| POST | `/api/prompts/experiments/{id}/resolve` | Pick winner + promote |
| GET | `/api/prompts/analytics` | Usage analytics (by prompt, model, cost) |
| POST | `/api/prompts/teams` | Create team |
| POST | `/api/prompts/teams/{id}/invite` | Invite member |

## 3.7 Unified Auth and Billing

```python
# Shared auth middleware — all three modules use the same JWT + API key system

class TierLimits:
    STARTER = {
        "agents": 5,
        "pipelines": 3,
        "prompts": 50,
        "events_per_day": 10_000,
        "pipeline_runs_per_day": 50,
        "prompt_renders_per_day": 500,
        "retention_days": 7,
    }
    PRO = {
        "agents": 25,
        "pipelines": 15,
        "prompts": 500,
        "events_per_day": 100_000,
        "pipeline_runs_per_day": 500,
        "prompt_renders_per_day": 5_000,
        "retention_days": 30,
    }
    TEAM = {
        "agents": None,  # Unlimited
        "pipelines": None,
        "prompts": None,
        "events_per_day": 1_000_000,
        "pipeline_runs_per_day": None,
        "prompt_renders_per_day": None,
        "retention_days": 90,
    }
```

### Stripe Integration

```python
STRIPE_PRODUCTS = {
    "starter": {
        "price_id": "price_starter_monthly",
        "amount": 4900,  # $49.00
        "interval": "month",
    },
    "pro": {
        "price_id": "price_pro_monthly",
        "amount": 9900,  # $99.00
        "interval": "month",
    },
    "team": {
        "price_id": "price_team_monthly",
        "amount": 19900,  # $199.00
        "interval": "month",
    },
}
```

## 3.8 Deployment

**Target**: Render (MVP) | Railway (scale)

| Component | Render Service | Cost/mo |
|-----------|---------------|---------|
| FastAPI backend | Web Service (starter) | $7 |
| Streamlit dashboard | Web Service (starter) | $7 |
| PostgreSQL | Managed DB (starter) | $7 |
| Redis | Managed Redis (starter) | $10 |
| Background workers | Background Worker | $7 |
| **Total MVP** | | **$38/mo** |

At 20 Starter customers ($980/mo revenue) the margin is 96%.

## 3.9 Implementation Phases

| Phase | Hours | Deliverable |
|-------|-------|-------------|
| 1. Scaffold + Auth | 8h | Repo, FastAPI skeleton, JWT + API keys, DB models |
| 2. Agent Monitoring | 12h | Ingestion, metrics aggregation, alerting, dashboard panels |
| 3. Data Pipeline | 15h | Scraper framework, LLM extraction, scheduling, webhooks |
| 4. Prompt Registry | 10h | Versioning, A/B testing, analytics, team management |
| 5. Billing + Polish | 5h | Stripe integration, usage metering, tier enforcement |
| 6. Testing + Docs | 5h | 80%+ coverage, API docs, onboarding guide |
| **Total** | **55h** | |

## 3.10 Competitive Positioning

| Feature | Langfuse | Helicone | AI DevOps Suite |
|---------|----------|----------|-----------------|
| Agent monitoring | Yes | Yes | Yes |
| Data pipelines | No | No | Yes |
| Prompt registry | Basic | No | Full (versioning + A/B) |
| Unified platform | No | No | Yes |
| Self-hostable | Yes | Yes | Yes |
| Starting price | $59/mo | $50/mo | $49/mo |

**Key differentiator**: Only platform combining agent observability, data pipeline management, and prompt engineering in a single product. Competitors require 2-3 separate tools.

---

# SECTION 4: Cohort Course — "Production AI Systems"

**Effort**: 40 hours | **Type**: Education / High-Touch Training | **Revenue Model**: Cohort-based + Self-paced

A 6-week live cohort course teaching engineers how to build production-grade AI systems, using the actual portfolio repos as curriculum material. Students ship real code to real infrastructure.

## 4.1 Pricing

### Live Cohort (6 weeks, 2x/week sessions)

| Tier | Price | Includes |
|------|-------|----------|
| **Beta (Cohort 1 only)** | $797 | All sessions, Discord, labs, certificate |
| **Standard** | $1,297 | All sessions, Discord, labs, certificate, 1 office hour |
| **Premium** | $1,997 | Everything in Standard + 3 private 1:1s, code review, LinkedIn recommendation |

### Post-Cohort Products

| Product | Price | Channel | Availability |
|---------|-------|---------|--------------|
| **Self-Paced** | $397 | Gumroad | After Cohort 1 completes |
| **Corporate Training** | $5,000-$15,000 | Direct sales | 5-10 seats, custom schedule |
| **Team License** | $3,997 | Direct sales | 5 seats, Standard tier |

### Revenue Projections

| Scenario | Students | Avg Price | Revenue/Cohort | Cohorts/Year | Annual |
|----------|----------|-----------|----------------|--------------|--------|
| Conservative | 15 | $997 | $14,955 | 3 | $44,865 |
| Target | 25 | $1,297 | $32,425 | 4 | $129,700 |
| Optimistic | 35 | $1,497 | $52,395 | 4 | $209,580 |

Self-paced add-on (post Cohort 1): 10-20 sales/month at $397 = $47,640-$95,280/year.

## 4.2 Platform Stack

| Function | Tool | Rationale |
|----------|------|-----------|
| Course hosting (launch) | **Maven** | Built for cohort courses, handles payments, calendar |
| Course hosting (scale) | **Circle** | Lower platform fees at scale, community-native |
| Community | **Discord** | Free, unlimited history, voice channels, bot ecosystem |
| Waitlist + Email | **ConvertKit** | Creator-focused, automation sequences, landing pages |
| Live sessions | **Zoom** | Maven-integrated, breakout rooms, recording |
| Certificates | **Certifier** | Automated issuance, LinkedIn integration, verification URL |
| Labs | **GitHub Classroom** | Auto-provisioning, autograding, private repos per student |
| Dev environment | **GitHub Codespaces** | Zero-setup, consistent env, 60hr/mo free tier |

## 4.3 Curriculum

### Week-by-Week Breakdown

| Week | Topic | Lab Repo | Key Deliverable |
|------|-------|----------|-----------------|
| 1 | Agent Architecture | AgentForge | Build a multi-tool agent with structured output |
| 2 | RAG Systems | DocQA-Insight | Implement hybrid search (BM25 + vector) |
| 3 | MCP + Tool Integration | EnterpriseHub | Connect agent to 3+ external tools via MCP |
| 4 | Production Hardening | EnterpriseHub | Add caching, rate limiting, error handling |
| 5 | Observability + Testing | Insight Engine | Instrument agent with metrics, write 50+ tests |
| 6 | Deployment + Operations | Student Project | Deploy full stack to Render/Railway with CI/CD |

### Session Format (2x per week, 90 minutes each)

```
Session A (Tuesday): Concept + Live Coding (90 min)
  - 15 min: Concept introduction
  - 45 min: Live coding walkthrough
  - 15 min: Lab assignment introduction
  - 15 min: Q&A

Session B (Thursday): Lab Review + Deep Dive (90 min)
  - 20 min: Lab solution review (common patterns/mistakes)
  - 40 min: Advanced topic deep-dive
  - 20 min: Guest speaker or case study
  - 10 min: Next week preview
```

### Lab Environment Setup

```yaml
# .devcontainer/devcontainer.json (per lab repo)
{
  "name": "Production AI Lab",
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {},
    "ghcr.io/devcontainers/features/node:1": {}
  },
  "postCreateCommand": "pip install -e '.[dev]' && pre-commit install",
  "forwardPorts": [8000, 8501, 5432, 6379],
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff"
      ]
    }
  }
}
```

## 4.4 Pre-Launch Email Sequence

| Day | Email | Subject Line | Content |
|-----|-------|-------------|---------|
| D-30 | Waitlist welcome | "You're in. Here's what we're building." | Problem statement, instructor credibility, portfolio stats (8,500+ tests, $50M pipeline) |
| D-21 | Social proof | "This is what production AI code looks like" | Preview of repo architecture, test counts, real metrics screenshots |
| D-14 | Value deep-dive | "Free lesson: Why 90% of AI demos fail in production" | Free sample lesson (Week 4 preview on caching/error handling), early testimonials |
| D-7 | Early bird open | "Enrollment is open. 30 seats. Beta pricing." | Limited seats, beta pricing ($797 vs $1,297 standard), bonus 1:1 session |
| D-3 | Scarcity | "{X} seats remaining for Cohort 1" | Countdown, FAQ, student profile ("who this is for") |
| D-1 | Final reminder | "Last call: Enrollment closes tomorrow" | Urgency, recap of what's included, refund policy |
| D-0 | Cart close | "Enrollment closed. Here's what happens next." | Welcome to enrolled, waitlist for Cohort 2 to non-enrolled |

### ConvertKit Automation Rules

```
Trigger: Tag "waitlist" added
  → Enter sequence "Pre-Launch" (D-30 through D-0)
  → Tag "cohort-1-prospect"

Trigger: Purchase completed (via Maven webhook)
  → Remove from "Pre-Launch" sequence
  → Add tag "cohort-1-enrolled"
  → Enter sequence "Onboarding" (Discord invite, lab setup, pre-work)

Trigger: D+1 after cohort start
  → Remove tag "cohort-1-prospect" from non-purchasers
  → Add tag "cohort-2-waitlist"
  → Enter sequence "Cohort 2 Nurture"
```

## 4.5 Infrastructure

```
course-infrastructure/
├── platform/
│   ├── maven_setup.md            # Maven course config, pricing tiers
│   └── circle_migration.md       # Migration plan for Cohort 3+
├── community/
│   ├── discord_setup.md           # Server structure
│   ├── bot_config/
│   │   ├── welcome_bot.py         # Auto-role, DM onboarding
│   │   └── lab_bot.py             # /submit command, progress tracking
│   └── channel_structure.md
├── marketing/
│   ├── convertkit_sequences/
│   │   ├── pre_launch.json        # D-30 to D-0
│   │   ├── onboarding.json        # Post-purchase
│   │   └── cohort2_nurture.json   # Waitlist for next cohort
│   ├── landing_page/
│   │   ├── index.html             # ConvertKit landing page template
│   │   └── assets/
│   └── social_templates/
│       ├── twitter_thread.md
│       ├── linkedin_post.md
│       └── reddit_post.md
├── labs/
│   ├── week1_agentforge/
│   │   ├── starter/               # Student starting point
│   │   ├── solution/              # Reference solution
│   │   ├── tests/                 # Autograding tests
│   │   └── README.md              # Lab instructions
│   ├── week2_docqa/
│   ├── week3_mcp/
│   ├── week4_enterprisehub/
│   ├── week5_insight_engine/
│   └── week6_deployment/
├── certificates/
│   └── certifier_template.json    # Certificate design + fields
└── infrastructure/
    ├── github_classroom/
    │   ├── classroom_config.yml   # Auto-provisioning settings
    │   └── autograder/            # GitHub Actions grading workflows
    └── codespace_config/
        └── devcontainer.json      # Shared dev environment config
```

### Discord Channel Structure

```
Production AI Systems (Server)
├── #announcements          (read-only, instructor posts)
├── #general                (open discussion)
├── #introductions          (new student intros)
│
├── COURSE
│   ├── #week-1-agents
│   ├── #week-2-rag
│   ├── #week-3-mcp
│   ├── #week-4-production
│   ├── #week-5-observability
│   └── #week-6-deployment
│
├── LABS
│   ├── #lab-help            (TA + peer support)
│   ├── #lab-submissions     (bot-tracked submissions)
│   └── #showcase            (completed projects)
│
├── COMMUNITY
│   ├── #jobs-and-gigs       (job postings, freelance leads)
│   ├── #resources           (links, articles, tools)
│   └── #off-topic
│
└── VOICE
    ├── Office Hours         (scheduled instructor sessions)
    ├── Study Group 1
    └── Study Group 2
```

## 4.6 Certificate Configuration

```json
{
  "template_id": "production-ai-systems",
  "design": {
    "background": "minimal-tech",
    "logo_url": "https://assets.example.com/course-logo.png",
    "accent_color": "#2563EB"
  },
  "fields": {
    "recipient_name": "{{ student.name }}",
    "course_name": "Production AI Systems",
    "completion_date": "{{ completion_date }}",
    "cohort": "{{ cohort_number }}",
    "instructor": "Cave",
    "credential_id": "{{ uuid }}",
    "skills": [
      "AI Agent Architecture",
      "RAG Systems",
      "MCP Integration",
      "Production Deployment",
      "AI Observability",
      "TDD for AI Systems"
    ]
  },
  "verification_url": "https://certifier.io/verify/{{ credential_id }}",
  "linkedin_integration": true
}
```

## 4.7 Corporate Training Variant

For companies wanting to upskill engineering teams (5-10 seats).

| Feature | Standard Corporate | Premium Corporate |
|---------|-------------------|-------------------|
| **Price** | $5,000 (5 seats) | $15,000 (10 seats) |
| **Schedule** | Flexible (weekday or evening) | Custom schedule |
| **Content** | Standard curriculum | Custom modules for their stack |
| **Labs** | Standard labs | Custom labs using their codebase |
| **Support** | Group Slack channel | Dedicated Slack + weekly check-ins |
| **Certificate** | Standard | Co-branded with company |
| **Post-course** | 30 days Discord access | 90 days + 1 consulting session |

## 4.8 Implementation Phases

| Phase | Hours | Deliverable |
|-------|-------|-------------|
| 1. Curriculum development | 15h | 6 weeks of lesson plans, slides, code walkthroughs |
| 2. Lab creation | 10h | 6 lab repos with starter code, solutions, autograding |
| 3. Platform setup | 5h | Maven course page, ConvertKit sequences, Discord server |
| 4. Marketing assets | 5h | Landing page, email copy, social templates |
| 5. Infrastructure | 3h | GitHub Classroom, Codespaces config, Certifier template |
| 6. Dry run + polish | 2h | Test full student journey end-to-end |
| **Total** | **40h** | |

---

# SECTION 5: RAG-as-a-Service

**Effort**: 80 hours | **Type**: Multi-Tenant SaaS Platform | **Revenue Model**: Subscription + Usage-Based

A fully managed RAG platform where customers upload documents, create collections, and query them via API or web UI. Multi-tenant with schema-per-tenant PostgreSQL isolation using pgvector.

## 5.1 Pricing

### Subscription Tiers

| Tier | Price | Documents | Queries/mo | Collections | Storage | Team Members |
|------|-------|-----------|------------|-------------|---------|--------------|
| **Starter** | $99/mo | 500 | 5,000 | 5 | 1 GB | 1 |
| **Pro** | $299/mo | 5,000 | 50,000 | 25 | 10 GB | 5 |
| **Business** | $999/mo | Unlimited | 500,000 | Unlimited | 100 GB | 25 |

### Overage Pricing

| Resource | Overage Rate | Applies To |
|----------|-------------|------------|
| Queries | $0.005/query | All tiers |
| Documents | $0.02/document | Starter + Pro |
| Storage | $0.10/GB/mo | All tiers |
| Embedding reprocessing | $0.001/document | All tiers |

### Premium Add-Ons (Pro and Business only)

| Add-On | Price | Description |
|--------|-------|-------------|
| PII Detection + Redaction | +$49/mo | Presidio-powered, scans on ingest |
| Audit Logging | +$29/mo | Full query/document audit trail, 1-year retention |
| Custom Embeddings | +$99/mo | Bring your own embedding model |
| SSO/SAML | +$99/mo | Enterprise auth (Business only) |
| SLA (99.9%) | +$199/mo | Guaranteed uptime with credits (Business only) |

### Revenue Projections

| Scale | Customers | Mix | MRR | ARR | Margin |
|-------|-----------|-----|-----|-----|--------|
| 10 | 7S + 2P + 1B | Early | $2,591 | $31,092 | 88% |
| 50 | 30S + 15P + 5B | Growth | $12,420 | $149,040 | 91% |
| 200 | 100S + 70P + 30B | Scale | $60,800 | $729,600 | 90% |

## 5.2 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Web UI (Next.js)                      │
│  Document upload, collection mgmt, query playground       │
└──────────────────────┬───────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                          │
│                                                           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐ │
│  │ Auth    │ │ Documents│ │ Queries  │ │ Collections │ │
│  │ (JWT +  │ │ (Upload, │ │ (Search, │ │ (CRUD,      │ │
│  │ API Key)│ │  Process)│ │  Stream) │ │  Organize)  │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬──────┘ │
│       └───────────┼────────────┼───────────────┘        │
│              ┌────▼────────────▼──────┐                  │
│              │     RAG Engine         │                  │
│              │  - Document Processor  │                  │
│              │  - Embedding Service   │                  │
│              │  - Hybrid Retriever    │                  │
│              │  - Query Expander      │                  │
│              │  - Reranker            │                  │
│              └────────┬──────────────┘                  │
│              ┌────────▼──────────────┐                  │
│              │   Multi-Tenant Layer  │                  │
│              │  - Tenant Router      │                  │
│              │  - Schema Manager     │                  │
│              │  - Isolation Guard    │                  │
│              └────────┬──────────────┘                  │
│              ┌────────▼──────────────┐                  │
│              │   Premium Features    │                  │
│              │  - PII Detector       │                  │
│              │  - Audit Logger       │                  │
│              └───────────────────────┘                  │
│                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌───────────────┐  │
│  │ Billing      │  │ Usage       │  │ Admin         │  │
│  │ (Stripe)     │  │ Tracker     │  │ Dashboard     │  │
│  └──────────────┘  └─────────────┘  └───────────────┘  │
└──────────────────────┬───────────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │PostgreSQL│ │  Redis   │ │ Object   │
   │+ pgvector│ │  Cache   │ │ Storage  │
   │(per-     │ │          │ │ (S3/R2)  │
   │ tenant   │ │          │ │          │
   │ schemas) │ │          │ │          │
   └──────────┘ └──────────┘ └──────────┘
```

## 5.3 Repository Structure

```
rag-as-a-service/
├── src/
│   ├── rag_service/
│   │   ├── __init__.py
│   │   ├── config.py                  # Environment-based configuration
│   │   ├── main.py                    # FastAPI entrypoint
│   │   │
│   │   ├── api/
│   │   │   ├── documents.py           # Upload, list, delete documents
│   │   │   ├── queries.py             # Query + streaming query (SSE)
│   │   │   ├── collections.py         # Collection CRUD
│   │   │   ├── tenants.py             # Tenant provisioning
│   │   │   ├── auth.py                # JWT + API key management
│   │   │   ├── billing.py             # Subscription + usage endpoints
│   │   │   └── teams.py               # Team member management
│   │   │
│   │   ├── core/
│   │   │   ├── rag_engine.py          # Orchestrates full RAG pipeline
│   │   │   ├── document_processor.py  # Chunking, metadata extraction
│   │   │   ├── embedding_service.py   # OpenAI/Cohere/local embeddings
│   │   │   ├── retriever.py           # Hybrid search (BM25 + vector)
│   │   │   ├── query_expander.py      # HyDE, multi-query expansion
│   │   │   └── reranker.py            # Cross-encoder reranking
│   │   │
│   │   ├── multi_tenant/
│   │   │   ├── tenant_router.py       # Route requests to tenant schema
│   │   │   ├── schema_manager.py      # Create/migrate/drop tenant schemas
│   │   │   └── isolation.py           # Enforce tenant data isolation
│   │   │
│   │   ├── premium/
│   │   │   ├── pii_detector.py        # Presidio-based PII scanning
│   │   │   └── audit_logger.py        # Query + document audit trail
│   │   │
│   │   ├── models/
│   │   │   ├── shared.py              # Tenant, User, Subscription (public schema)
│   │   │   └── tenant_models.py       # Document, Chunk, Collection (per-tenant)
│   │   │
│   │   ├── billing/
│   │   │   ├── stripe_service.py      # Subscription lifecycle
│   │   │   └── usage_tracker.py       # Metered billing events
│   │   │
│   │   └── dashboard/
│   │       └── admin_app.py           # Streamlit admin dashboard
│   │
├── web_ui/                             # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── dashboard/
│   │   │   ├── documents/
│   │   │   ├── playground/            # Interactive query testing
│   │   │   └── settings/
│   │   └── components/
│   └── package.json
│
├── tests/
│   ├── test_api/
│   ├── test_core/
│   ├── test_multi_tenant/
│   ├── test_premium/
│   ├── test_billing/
│   └── conftest.py
├── alembic/
│   └── versions/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 5.4 Multi-Tenant Isolation

### Schema-Per-Tenant (correct for <1,000 tenants)

```python
from contextlib import contextmanager
from sqlalchemy import event
from sqlalchemy.orm import Session

@contextmanager
def tenant_session(tenant_schema: str):
    """Create a database session scoped to a specific tenant's schema.

    Uses PostgreSQL schema_translate_map for transparent query routing.
    All queries within this context execute against the tenant's isolated schema.
    """
    schema_map = {"tenant": tenant_schema} if tenant_schema else None
    connectable = engine.execution_options(schema_translate_map=schema_map)
    db = Session(autocommit=False, autoflush=False, bind=connectable)
    try:
        yield db
    finally:
        db.close()


class SchemaManager:
    """Manages tenant schema lifecycle."""

    async def provision_tenant(self, tenant_id: str) -> str:
        """Create isolated schema for new tenant."""
        schema_name = f"tenant_{tenant_id}"

        async with self.engine.begin() as conn:
            # Create schema
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            # Run tenant-specific migrations
            await self._run_tenant_migrations(conn, schema_name)

            # Create pgvector extension in schema
            await conn.execute(text(
                f"CREATE EXTENSION IF NOT EXISTS vector SCHEMA {schema_name}"
            ))

        return schema_name

    async def deprovision_tenant(self, tenant_id: str):
        """Drop tenant schema and all data. IRREVERSIBLE."""
        schema_name = f"tenant_{tenant_id}"
        async with self.engine.begin() as conn:
            await conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))

    async def _run_tenant_migrations(self, conn, schema_name: str):
        """Apply tenant-specific table definitions."""
        await conn.execute(text(f"SET search_path TO {schema_name}"))

        # Documents table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                collection_id UUID REFERENCES collections(id),
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size_bytes BIGINT NOT NULL,
                chunk_count INT DEFAULT 0,
                metadata JSONB DEFAULT '{}',
                storage_key TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Chunks table with vector column
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                embedding vector(1536),
                chunk_index INT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Vector similarity index
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunks_embedding
            ON chunks USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100)
        """))

        # Collections table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS collections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name TEXT NOT NULL,
                description TEXT,
                document_count INT DEFAULT 0,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
```

### Tenant Isolation Middleware

```python
from fastapi import Request, HTTPException

class TenantIsolationMiddleware:
    """Ensures every request is scoped to exactly one tenant."""

    async def __call__(self, request: Request, call_next):
        # Extract tenant from JWT or API key
        tenant_id = await self._resolve_tenant(request)

        if not tenant_id:
            raise HTTPException(401, "Tenant context required")

        # Inject tenant context into request state
        request.state.tenant_id = tenant_id
        request.state.tenant_schema = f"tenant_{tenant_id}"

        response = await call_next(request)
        return response

    async def _resolve_tenant(self, request: Request) -> str | None:
        # From API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return await self._tenant_from_api_key(api_key)

        # From JWT token
        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            return await self._tenant_from_jwt(token)

        return None
```

## 5.5 API Design

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/documents` | API Key | Upload document (multipart) |
| GET | `/api/v1/documents` | API Key | List documents (paginated, filterable) |
| GET | `/api/v1/documents/{id}` | API Key | Get document metadata |
| DELETE | `/api/v1/documents/{id}` | API Key | Delete document + chunks |
| POST | `/api/v1/query` | API Key | Query documents (returns top-k results) |
| POST | `/api/v1/query/stream` | API Key | Streaming query response (SSE) |
| POST | `/api/v1/collections` | API Key | Create collection |
| GET | `/api/v1/collections` | API Key | List collections |
| PUT | `/api/v1/collections/{id}` | API Key | Update collection |
| DELETE | `/api/v1/collections/{id}` | API Key | Delete collection |
| GET | `/api/v1/usage` | API Key | Get usage stats (queries, documents, storage) |
| POST | `/api/v1/auth/keys` | JWT | Create API key |
| GET | `/api/v1/auth/keys` | JWT | List API keys |
| DELETE | `/api/v1/auth/keys/{id}` | JWT | Revoke API key |
| POST | `/api/v1/teams/invite` | JWT | Invite team member |
| GET | `/api/v1/teams/members` | JWT | List team members |
| DELETE | `/api/v1/teams/members/{id}` | JWT | Remove team member |

### Query Endpoint Detail

```python
class QueryRequest(BaseModel):
    query: str
    collection_ids: list[str] | None = None  # None = search all
    top_k: int = 5
    min_score: float = 0.7
    rerank: bool = True
    expand_query: bool = False  # HyDE expansion
    filters: dict | None = None  # Metadata filters
    include_sources: bool = True

class QueryResult(BaseModel):
    answer: str
    sources: list[Source]
    usage: QueryUsage
    latency_ms: float

class Source(BaseModel):
    document_id: str
    document_name: str
    chunk_id: str
    content: str
    score: float
    metadata: dict

class QueryUsage(BaseModel):
    embedding_tokens: int
    llm_tokens_input: int
    llm_tokens_output: int
    total_cost_usd: float


@router.post("/api/v1/query")
async def query_documents(
    request: QueryRequest,
    tenant: TenantContext = Depends(get_tenant),
):
    # Track usage
    await usage_tracker.increment(tenant.id, "queries", 1)

    # Check tier limits
    await enforce_limits(tenant, "queries")

    with tenant_session(tenant.schema) as db:
        result = await rag_engine.query(
            db=db,
            query=request.query,
            collection_ids=request.collection_ids,
            top_k=request.top_k,
            min_score=request.min_score,
            rerank=request.rerank,
            expand_query=request.expand_query,
            filters=request.filters,
        )

    # Report to Stripe for usage-based billing
    if tenant.has_overage:
        await billing_service.report_query_usage(tenant.stripe_customer_id)

    return result
```

### Streaming Query (SSE)

```python
@router.post("/api/v1/query/stream")
async def stream_query(
    request: QueryRequest,
    tenant: TenantContext = Depends(get_tenant),
):
    async def event_generator():
        # First, send retrieved sources
        sources = await rag_engine.retrieve(
            tenant.schema, request.query, request.top_k
        )
        yield {"event": "sources", "data": json.dumps([s.dict() for s in sources])}

        # Then stream the generated answer
        async for chunk in rag_engine.generate_stream(request.query, sources):
            yield {"event": "answer", "data": chunk}

        # Finally, send usage stats
        usage = await rag_engine.get_last_usage()
        yield {"event": "usage", "data": json.dumps(usage.dict())}
        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())
```

## 5.6 PII Detection (Premium Feature)

```python
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine

class PIIDetector:
    """Presidio-powered PII detection and redaction.

    Premium feature: scans documents on ingest and optionally redacts
    before embedding. Available on Pro and Business tiers.
    """

    def __init__(self, entities: list[str] | None = None):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self.default_entities = entities or [
            "PHONE_NUMBER", "EMAIL_ADDRESS", "PERSON",
            "CREDIT_CARD", "US_SSN", "IP_ADDRESS",
            "LOCATION", "DATE_TIME",
        ]

    def scan(self, text: str, language: str = "en") -> list[PIIFinding]:
        """Scan text for PII entities. Returns findings above 0.7 confidence."""
        results = self.analyzer.analyze(
            text=text, language=language, entities=self.default_entities
        )
        return [
            PIIFinding(
                entity_type=r.entity_type,
                start=r.start,
                end=r.end,
                score=r.score,
                text=text[r.start:r.end],
            )
            for r in results
            if r.score >= 0.7
        ]

    def redact(self, text: str, language: str = "en") -> str:
        """Redact all detected PII from text."""
        results = self.analyzer.analyze(
            text=text, language=language, entities=self.default_entities
        )
        return self.anonymizer.anonymize(text=text, analyzer_results=results).text

    async def scan_document(self, document_id: str, chunks: list[str]) -> PIIReport:
        """Scan all chunks of a document for PII.

        Returns a report with findings per chunk and an overall risk score.
        """
        findings = []
        for i, chunk in enumerate(chunks):
            chunk_findings = self.scan(chunk)
            for f in chunk_findings:
                f.chunk_index = i
                findings.append(f)

        risk_score = self._calculate_risk(findings)

        return PIIReport(
            document_id=document_id,
            total_findings=len(findings),
            findings=findings,
            risk_score=risk_score,  # 0-100
            risk_level="high" if risk_score > 70 else "medium" if risk_score > 30 else "low",
            entity_summary={
                entity: len([f for f in findings if f.entity_type == entity])
                for entity in set(f.entity_type for f in findings)
            },
        )

    def _calculate_risk(self, findings: list[PIIFinding]) -> float:
        """Weight risk by entity sensitivity."""
        weights = {
            "US_SSN": 10.0,
            "CREDIT_CARD": 10.0,
            "PHONE_NUMBER": 3.0,
            "EMAIL_ADDRESS": 3.0,
            "PERSON": 2.0,
            "IP_ADDRESS": 2.0,
            "LOCATION": 1.0,
            "DATE_TIME": 0.5,
        }
        if not findings:
            return 0.0
        total_weight = sum(weights.get(f.entity_type, 1.0) for f in findings)
        return min(100.0, total_weight * 5)  # Scale to 0-100
```

### PII Integration with Document Ingest

```python
class DocumentProcessor:
    async def process_document(
        self,
        file: UploadFile,
        collection_id: str,
        tenant: TenantContext,
        redact_pii: bool = False,
    ) -> ProcessedDocument:
        # 1. Extract text
        raw_text = await self._extract_text(file)

        # 2. Chunk text
        chunks = self._chunk_text(raw_text)

        # 3. PII scan (if tenant has premium feature)
        pii_report = None
        if tenant.features.pii_detection:
            pii_report = await self.pii_detector.scan_document(
                document_id=file.filename, chunks=chunks
            )

            # Optionally redact PII before embedding
            if redact_pii:
                chunks = [self.pii_detector.redact(chunk) for chunk in chunks]

        # 4. Generate embeddings
        embeddings = await self.embedding_service.embed_batch(chunks)

        # 5. Store
        document = await self._store_document(
            tenant.schema, file, chunks, embeddings, pii_report
        )

        return document
```

## 5.7 Audit Logging (Premium Feature)

```python
class AuditLogger:
    """Comprehensive audit trail for compliance-sensitive deployments.

    Logs every document upload, deletion, query, and admin action
    with full context. 1-year retention for premium subscribers.
    """

    async def log_event(
        self,
        tenant_id: str,
        event_type: AuditEventType,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        details: dict | None = None,
        ip_address: str | None = None,
    ):
        event = AuditEvent(
            id=uuid4(),
            tenant_id=tenant_id,
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
        )

        # Write to audit table (append-only, no updates/deletes)
        async with self._get_session() as db:
            db.add(event)
            await db.commit()

    async def query_audit_log(
        self,
        tenant_id: str,
        event_types: list[AuditEventType] | None = None,
        actor_id: str | None = None,
        resource_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit log with filters. Returns newest first."""
        ...


class AuditEventType(str, Enum):
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_DELETED = "document.deleted"
    QUERY_EXECUTED = "query.executed"
    COLLECTION_CREATED = "collection.created"
    COLLECTION_DELETED = "collection.deleted"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    TEAM_MEMBER_INVITED = "team.member_invited"
    TEAM_MEMBER_REMOVED = "team.member_removed"
    PII_DETECTED = "pii.detected"
    PII_REDACTED = "pii.redacted"
    SETTINGS_CHANGED = "settings.changed"
```

## 5.8 Billing Integration

```python
class RAGBillingService:
    """Stripe integration for subscriptions + usage-based metering."""

    METER_NAME = "rag_queries"

    PLANS = {
        "starter": {
            "price_id": "price_rag_starter_monthly",
            "amount": 9900,   # $99.00
            "query_limit": 5_000,
            "document_limit": 500,
            "storage_gb": 1,
        },
        "pro": {
            "price_id": "price_rag_pro_monthly",
            "amount": 29900,  # $299.00
            "query_limit": 50_000,
            "document_limit": 5_000,
            "storage_gb": 10,
        },
        "business": {
            "price_id": "price_rag_business_monthly",
            "amount": 99900,  # $999.00
            "query_limit": 500_000,
            "document_limit": None,  # Unlimited
            "storage_gb": 100,
        },
    }

    def __init__(self, api_key: str):
        stripe.api_key = api_key

    async def create_subscription(
        self, customer_id: str, plan: str
    ) -> stripe.Subscription:
        """Create subscription with usage-based overage metering."""
        return stripe.Subscription.create(
            customer=customer_id,
            items=[
                {"price": self.PLANS[plan]["price_id"]},
                {"price": "price_rag_query_overage"},  # $0.005/query
            ],
        )

    async def report_query_usage(
        self, stripe_customer_id: str, query_count: int = 1
    ):
        """Report query usage to Stripe for metered billing."""
        stripe.billing.MeterEvent.create(
            event_name=self.METER_NAME,
            payload={
                "stripe_customer_id": stripe_customer_id,
                "value": str(query_count),
            },
        )

    async def check_limits(self, tenant_id: str, resource: str) -> bool:
        """Check if tenant is within their plan limits."""
        usage = await self.usage_tracker.get_current_period(tenant_id)
        plan = await self._get_tenant_plan(tenant_id)
        limit = self.PLANS[plan].get(f"{resource}_limit")

        if limit is None:  # Unlimited
            return True

        return usage.get(resource, 0) < limit


class UsageTracker:
    """Track per-tenant resource usage with Redis for real-time + Postgres for billing."""

    async def increment(self, tenant_id: str, resource: str, count: int = 1):
        """Increment usage counter. Uses Redis for speed, flushes to Postgres."""
        key = f"usage:{tenant_id}:{resource}:{self._current_period()}"

        # Atomic increment in Redis
        new_value = await self.redis.incrby(key, count)

        # Set expiry (35 days to cover billing period + buffer)
        if new_value == count:
            await self.redis.expire(key, 35 * 86400)

        # Async flush to Postgres every 100 increments
        if new_value % 100 == 0:
            await self._flush_to_postgres(tenant_id, resource, new_value)

    async def get_current_period(self, tenant_id: str) -> dict:
        """Get all usage metrics for current billing period."""
        period = self._current_period()
        resources = ["queries", "documents", "storage_bytes"]

        usage = {}
        for resource in resources:
            key = f"usage:{tenant_id}:{resource}:{period}"
            value = await self.redis.get(key)
            usage[resource] = int(value) if value else 0

        return usage
```

## 5.9 Deployment

### MVP: Render ($24-42/month infrastructure)

| Component | Render Service | Plan | Cost/mo |
|-----------|---------------|------|---------|
| FastAPI backend | Web Service | Starter | $7 |
| Background worker | Background Worker | Starter | $7 |
| PostgreSQL + pgvector | Managed Database | Starter | $7 |
| Redis | Managed Redis | Starter | $10 |
| Object storage | Cloudflare R2 | Free tier | $0 |
| **Total** | | | **$31/mo** |

### Scale: Railway ($200-1,000/month infrastructure)

| Component | Config | Cost/mo |
|-----------|--------|---------|
| FastAPI (2 replicas) | 2 vCPU, 4GB RAM | $60 |
| Background workers (2) | 1 vCPU, 2GB RAM | $30 |
| PostgreSQL | 4 vCPU, 8GB RAM, 100GB | $80 |
| Redis | 2GB RAM | $20 |
| Object storage (R2) | 100GB | $5 |
| **Total** | | **$195/mo** |

### Cost Analysis at Scale

| Scale | Customers | Infra/mo | Embedding API | LLM API | Total Cost | Revenue | Margin |
|-------|-----------|----------|---------------|---------|------------|---------|--------|
| 10 | Startups | $40 | $5 | $15 | $60 | $500 | 88% |
| 100 | SMBs | $200 | $50 | $150 | $400 | $5,000 | 92% |
| 1,000 | Scale | $1,000 | $500 | $1,500 | $3,000 | $30,000 | 90% |

## 5.10 RAG Engine Core

```python
class RAGEngine:
    """Core retrieval-augmented generation pipeline."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        retriever: HybridRetriever,
        reranker: Reranker,
        query_expander: QueryExpander,
        llm_client: LLMClient,
    ):
        self.embedding_service = embedding_service
        self.retriever = retriever
        self.reranker = reranker
        self.query_expander = query_expander
        self.llm_client = llm_client

    async def query(
        self,
        db: Session,
        query: str,
        collection_ids: list[str] | None = None,
        top_k: int = 5,
        min_score: float = 0.7,
        rerank: bool = True,
        expand_query: bool = False,
        filters: dict | None = None,
    ) -> QueryResult:
        start = time.monotonic()

        # 1. Query expansion (optional)
        queries = [query]
        if expand_query:
            queries = await self.query_expander.expand(query)

        # 2. Hybrid retrieval (BM25 + vector)
        candidates = []
        for q in queries:
            embedding = await self.embedding_service.embed(q)
            results = await self.retriever.search(
                db=db,
                query_text=q,
                query_embedding=embedding,
                collection_ids=collection_ids,
                top_k=top_k * 3,  # Over-fetch for reranking
                filters=filters,
            )
            candidates.extend(results)

        # 3. Deduplicate
        seen = set()
        unique_candidates = []
        for c in candidates:
            if c.chunk_id not in seen:
                seen.add(c.chunk_id)
                unique_candidates.append(c)

        # 4. Rerank (optional)
        if rerank and len(unique_candidates) > top_k:
            ranked = await self.reranker.rerank(query, unique_candidates)
            sources = [s for s in ranked[:top_k] if s.score >= min_score]
        else:
            sources = sorted(
                unique_candidates, key=lambda x: x.score, reverse=True
            )[:top_k]
            sources = [s for s in sources if s.score >= min_score]

        # 5. Generate answer
        context = "\n\n".join(
            f"[Source: {s.document_name}]\n{s.content}" for s in sources
        )
        answer = await self.llm_client.generate(
            system="Answer the question based on the provided context. "
                   "Cite sources when possible. If the context doesn't "
                   "contain enough information, say so.",
            user=f"Context:\n{context}\n\nQuestion: {query}",
        )

        latency = (time.monotonic() - start) * 1000

        return QueryResult(
            answer=answer.text,
            sources=[Source.from_retrieval(s) for s in sources],
            usage=QueryUsage(
                embedding_tokens=answer.usage.embedding_tokens,
                llm_tokens_input=answer.usage.input_tokens,
                llm_tokens_output=answer.usage.output_tokens,
                total_cost_usd=answer.usage.total_cost,
            ),
            latency_ms=latency,
        )
```

## 5.11 Competitive Positioning

| Feature | Vectara | Pinecone Canopy | RAG-as-a-Service |
|---------|---------|-----------------|------------------|
| Managed RAG | Yes | Partial | Yes |
| Multi-tenant | Enterprise only | No | Built-in |
| PII detection | No | No | Yes (premium) |
| Audit logging | Enterprise | No | Yes (premium) |
| Hybrid search | Yes | Vector only | Yes (BM25 + vector) |
| Streaming | Yes | No | Yes (SSE) |
| Self-hostable | No | No | Yes (Docker) |
| Starting price | $100K+/yr | Free + compute | $99/mo |
| Target market | Enterprise | Developers | SMB + Startups |

**Key differentiator**: The only managed RAG platform targeting the SMB gap between free open-source tools (LangChain, LlamaIndex) and enterprise solutions (Vectara $100K+/yr). Full multi-tenancy, PII compliance, and audit logging at $99-$999/mo.

## 5.12 Implementation Phases

| Phase | Hours | Deliverable |
|-------|-------|-------------|
| 1. Core scaffold + multi-tenant | 15h | Repo, FastAPI, schema-per-tenant, tenant provisioning |
| 2. RAG engine | 20h | Document processor, embedding service, hybrid retriever, reranker |
| 3. API layer | 10h | All REST endpoints, streaming query, auth middleware |
| 4. Billing + usage | 8h | Stripe subscriptions, usage metering, tier enforcement |
| 5. Premium features | 8h | PII detector (Presidio), audit logger |
| 6. Web UI | 10h | Next.js dashboard, document upload, query playground |
| 7. Testing + hardening | 5h | 80%+ coverage, load testing, security review |
| 8. Deployment + docs | 4h | Docker, Render config, API docs, onboarding guide |
| **Total** | **80h** | |

---
# SECTION 6: Revenue Multipliers

Beyond SaaS subscriptions and course sales, these multipliers create layered, recurring revenue streams that compound over time. Each multiplier is designed for a solo developer to activate incrementally without requiring new codebases.

---

## 6.1 White-Label Voice AI Program

Offer GHL consultants and agencies a fully managed voice AI agent under their own brand. They sell to their clients; you handle the infrastructure.

### Structure

```
┌─────────────────────────┐
│   GHL Agency / Reseller │  ← Sells to SMBs at $300-$800/mo
│   (White-Label Partner) │
└───────────┬─────────────┘
            │ Pays $99-$299/mo per client
┌───────────▼─────────────┐
│   Your Voice AI Platform│  ← Provisioning, monitoring, billing
│   (Multi-Tenant Infra)  │
└───────────┬─────────────┘
            │ Pays cost (~$0.04-$0.06/min)
┌───────────▼─────────────┐
│  Deepgram / ElevenLabs  │
│  Twilio / LLM Provider  │
└─────────────────────────┘
```

### Pricing Tiers

| Tier | Monthly Fee | Included Minutes | Overage | Target Reseller |
|------|-------------|-----------------|---------|-----------------|
| Starter | $99/client | 500 min | $0.12/min | Solo GHL consultants |
| Growth | $199/client | 1,500 min | $0.10/min | Small agencies (5-20 clients) |
| Enterprise | $299/client | 5,000 min | $0.08/min | Large agencies (20+ clients) |

### Reseller Margins

| Reseller Sells At | Your Fee | Reseller Margin | Effort After Setup |
|-------------------|----------|-----------------|-------------------|
| $300/mo | $99/mo | $201/mo (67%) | Near-zero |
| $500/mo | $199/mo | $301/mo (60%) | Near-zero |
| $800/mo | $299/mo | $501/mo (63%) | Near-zero |

**Activation requirement**: White-label dashboard (Phase 2 deliverable), partner onboarding docs, Stripe Connect for automated splits.

**Revenue projection**: 5 resellers x 3 clients each x $199/mo avg = $2,985/mo by month 6. Scales to $10K+/mo with 15-20 active resellers.

---

## 6.2 Self-Paced Course (Gumroad)

After Cohort 1 wraps, convert recordings + labs into a self-paced product on Gumroad.

| Attribute | Value |
|-----------|-------|
| Price | $397 (intro), $497 (standard) |
| Platform | Gumroad (10% + $0.50/tx via direct link) |
| Content | 8 modules, 40+ video lessons, 8 hands-on labs, all repos |
| Updates | Quarterly content refreshes (2-4 hrs each) |
| Differentiator | Production repos with tests, not toy demos |
| Upsell | $97 "Office Hours" add-on (monthly group call) |

**Revenue projection**: 10-20 sales/month at $397 = $3,970-$7,940/mo passive after initial recording investment (~40 hrs).

**Funnel**: Free Week 1 preview on Gumroad -> email drip (ConvertKit) -> self-paced purchase -> office hours upsell -> cohort upsell ($797-$1,997).

---

## 6.3 Implementation Services

Hands-on build-outs for clients who want custom Voice AI, RAG, or MCP integrations but lack the engineering capacity.

### Service Packages

| Package | Scope | Price Range | Timeline | Typical Client |
|---------|-------|-------------|----------|---------------|
| Voice AI Starter | 1 bot, 1 GHL workflow, basic analytics | $5,000-$8,000 | 2-3 weeks | Single-location brokerage |
| Voice AI Pro | Multi-bot, handoff logic, custom dashboards | $8,000-$15,000 | 4-6 weeks | Multi-office agency |
| RAG Deployment | Document ingestion, API, eval pipeline | $5,000-$12,000 | 3-5 weeks | SaaS company or legal firm |
| MCP Custom Server | Custom MCP server for internal tools | $5,000-$10,000 | 2-4 weeks | Dev team with specific integration |
| Full Stack AI | Voice + RAG + MCP + dashboards | $15,000-$30,000 | 6-10 weeks | Enterprise with budget |

### Delivery Model

- **Discovery call** (30 min, free) -> **SOW** (1-2 pages) -> **50% deposit** -> **Build** -> **Demo + feedback** -> **50% final** -> **30-day support**
- All implementations use your SaaS products as the foundation, reducing custom work to 40-60% of total hours
- Clients become long-term SaaS subscribers post-implementation

**Revenue projection**: 1-2 projects/month at $7,500 avg = $7,500-$15,000/mo. Capacity-constrained as solo dev; raise rates as demand increases.

---

## 6.4 Template Marketplace

Pre-built, tested configurations that clients install in minutes. Low effort to create, high margin, evergreen.

### Template Categories

| Category | Examples | Price | Effort to Create |
|----------|---------|-------|-----------------|
| GHL Automations | Lead qualification workflow, appointment booking, follow-up sequences | $49-$99 | 2-4 hrs each |
| Voice Flow Templates | Real estate buyer qualifier, appointment setter, after-hours handler | $99-$149 | 4-8 hrs each |
| RAG Configurations | Legal doc Q&A config, real estate MLS config, support KB config | $79-$149 | 3-6 hrs each |
| MCP Server Templates | CRM connector template, database query template, API bridge template | $99-$199 | 4-8 hrs each |
| Dashboard Templates | Sales pipeline dashboard, call analytics, lead scoring board | $49-$99 | 2-4 hrs each |

### Distribution

- **Primary**: Gumroad (10% + $0.50/tx direct, 30% via Discover)
- **Secondary**: GHL Marketplace (if accepted), MCP Server Store
- **Bundled**: Include 1-2 templates free with SaaS subscription tiers to reduce churn

**Revenue projection**: 20 templates x 5 sales/month avg x $99 avg = $9,900/mo at maturity. First 5 templates launch in Phase 1 alongside products.

---

## 6.5 Consulting and Advisory

Premium hourly and retainer engagements for teams that need architecture guidance, not implementation.

### Rate Card

| Engagement Type | Rate | Minimum | Typical Scope |
|-----------------|------|---------|--------------|
| Strategy Session | $250/hr | 2 hrs | Architecture review, tech stack decisions |
| Hands-On Advisory | $300/hr | 4 hrs | Code review, performance tuning, security audit |
| Expert Consultation | $350/hr | 2 hrs | AI strategy, vendor selection, build-vs-buy |
| Monthly Retainer (Light) | $3,000/mo | 3 months | 10 hrs/mo, async Slack access, weekly sync |
| Monthly Retainer (Standard) | $5,000/mo | 3 months | 20 hrs/mo, priority Slack, bi-weekly sync |
| Monthly Retainer (Premium) | $10,000/mo | 6 months | 40 hrs/mo, dedicated Slack channel, weekly sync |

### Positioning

- Consulting is sourced from **course alumni**, **implementation clients**, and **inbound content** (LinkedIn, blog, Product Hunt visibility)
- Retainers are the highest-LTV engagement: $36K-$120K/year per client
- Cap at 2 concurrent retainers to protect product development time

**Revenue projection**: 1 retainer at $5K/mo + 8 hrs/mo ad-hoc at $300/hr = $7,400/mo.

---

## 6.6 Annual Pricing

All SaaS products offer annual billing at a 20% discount. Annual contracts reduce churn from 30-50% (monthly) to 5-10% (annual) and improve cash flow predictability.

| Product | Monthly | Annual (20% off) | Annual Savings | Cash Upfront |
|---------|---------|-------------------|---------------|-------------|
| Voice AI Starter | $99/mo | $79/mo ($948/yr) | $240 | $948 |
| Voice AI Growth | $249/mo | $199/mo ($2,388/yr) | $600 | $2,388 |
| MCP Toolkit Pro | $149/mo | $119/mo ($1,428/yr) | $360 | $1,428 |
| RAG-as-a-Service Pro | $299/mo | $239/mo ($2,868/yr) | $720 | $2,868 |
| AI DevOps Pro | $99/mo | $79/mo ($948/yr) | $240 | $948 |

**Implementation**: Stripe annual billing with prorated upgrades. Display annual as default on pricing pages (monthly as toggle). 84% of enterprise customers expect annual options (Gartner).

---

## 6.7 Affiliate and Referral Program

GHL consultants, course alumni, and content creators earn 20% recurring commission on referred SaaS subscriptions.

### Program Structure

| Attribute | Value |
|-----------|-------|
| Commission | 20% recurring (paid monthly, for life of subscription) |
| Cookie Duration | 90 days |
| Minimum Payout | $50 |
| Payment Method | PayPal or Stripe Transfer |
| Tracking | First-touch attribution via UTM + referral codes |
| Dashboard | Self-service affiliate portal (Phase 2) |

### Target Affiliates

| Segment | Why They Refer | Expected Volume |
|---------|---------------|----------------|
| GHL Consultants | Already selling to SMBs, Voice AI is natural upsell | 5-15 referrals/mo |
| Course Alumni | Trusted peers in AI community | 2-5 referrals/mo |
| Tech Bloggers | Content monetization | 1-3 referrals/mo |
| YouTube Creators | Demo content drives affiliate clicks | 3-10 referrals/mo |

**Revenue impact**: 20 referred subscribers x $150 avg/mo = $3,000/mo gross. Affiliate cost: $600/mo (20%). Net incremental: $2,400/mo with zero CAC beyond program setup.

---

## 6.8 Revenue Multiplier Summary

| Multiplier | Setup Effort | Time to First $ | Steady-State Monthly |
|------------|-------------|-----------------|---------------------|
| White-Label Voice AI | 20-30 hrs | Month 4-5 | $3K-$10K |
| Self-Paced Course | 40 hrs (post-cohort) | Month 4 | $4K-$8K |
| Implementation Services | 5 hrs (SOW templates) | Month 2 | $7.5K-$15K |
| Template Marketplace | 3-4 hrs per template | Month 2 | $5K-$10K |
| Consulting/Advisory | 2 hrs (rate card + scheduling) | Month 1 | $5K-$10K |
| Annual Pricing | 2 hrs (Stripe config) | Month 1 | +15-25% LTV uplift |
| Affiliate Program | 8-10 hrs (portal + tracking) | Month 3 | $2K-$5K net |

**Combined multiplier revenue at month 6**: $26K-$58K/mo on top of core SaaS + course revenue.

---

# SECTION 7: All-Parallel Launch Sequence and Dependency Graph

The traditional sequential approach (build Product A, then B, then C) wastes 4-6 months before diversified revenue appears. Instead, all 6 workstreams launch in Week 1 and progress in parallel, sharing a common infrastructure foundation.

---

## 7.1 Workstream Definitions

| ID | Workstream | Primary Product | Hours | Revenue Type |
|----|-----------|----------------|-------|-------------|
| WS-1 | Shared Infrastructure | Foundation (all products) | 40 | Enabling |
| WS-2 | Voice AI Platform | Voice AI Agent | 160 | SaaS + White-Label |
| WS-3 | MCP Toolkit | MCP Server Marketplace | 60 | Product + Services |
| WS-4 | Course Program | Cohort + Self-Paced | 40 | Course + Passive |
| WS-5 | RAG-as-a-Service | RAG SaaS Platform | 80 | SaaS + Usage |
| WS-6 | AI DevOps Suite | DevOps Toolkit | 55 | SaaS |

**Total**: ~395 development hours + ~40 shared infrastructure hours = ~435 hours.

---

## 7.2 Dependency Graph

```
Week 1-2: SHARED INFRASTRUCTURE (WS-1) ─── THE ONLY HARD BLOCKER
    │
    ├── Auth service (JWT + API keys)
    ├── Billing engine (Stripe metered + subscription)
    ├── Multi-tenant database schema
    ├── Deployment pipeline (Railway/Render + Docker)
    ├── Monitoring stack (Sentry + PostHog)
    └── Shared Python SDK (common models, error handling)
    │
    ▼ Unblocks ALL workstreams simultaneously
    │
    ├──► WS-2: Voice AI ──────────────────────────────────────►
    │         │
    │         ├─ Week 1-2: Deepgram/Twilio integration (CAN start before WS-1 completes)
    │         ├─ Week 3-4: GHL-native call flows ◄── Needs WS-1 auth + billing
    │         ├─ Week 5-8: Multi-tenant dashboard ◄── Needs WS-1 DB schema
    │         └─ Week 9-12: White-label provisioning ◄── Needs WS-2 dashboard
    │
    ├──► WS-3: MCP Toolkit ───────────────────────────────────►
    │         │
    │         ├─ Week 1-2: Package existing servers (CAN start before WS-1)
    │         ├─ Week 3-4: Marketplace listing + billing ◄── Needs WS-1 billing
    │         ├─ Week 5-8: Community server SDK
    │         └─ Week 9-12: Enterprise features
    │
    ├──► WS-4: Course Program ────────────────────────────────►
    │         │
    │         ├─ Week 1-2: Curriculum finalization + landing page (NO blockers)
    │         ├─ Week 3-4: Record modules 1-4 (NO blockers)
    │         ├─ Week 5-8: Record modules 5-8, launch Cohort 1
    │         └─ Week 9-12: Self-paced conversion on Gumroad
    │
    ├──► WS-5: RAG-as-a-Service ──────────────────────────────►
    │         │
    │         ├─ Week 1-2: API design + eval pipeline (CAN start before WS-1)
    │         ├─ Week 3-4: Upload + query endpoints ◄── Needs WS-1 auth + DB
    │         ├─ Week 5-8: Usage metering + dashboards ◄── Needs WS-1 billing
    │         └─ Week 9-12: Enterprise tier + SLA monitoring
    │
    └──► WS-6: AI DevOps Suite ───────────────────────────────►
              │
              ├─ Week 1-2: CLI scaffolding (CAN start before WS-1)
              ├─ Week 3-4: Core features + billing ◄── Needs WS-1 billing
              ├─ Week 5-8: CI/CD integrations
              └─ Week 9-12: Team features + enterprise
```

### Dependency Rules

1. **WS-1 is the only cross-cutting blocker**. No product can accept paid users until auth + billing are live.
2. **WS-4 (Course) has zero infrastructure dependencies**. It runs on ConvertKit, Gumroad, and Zoom -- all external. This is the fastest path to revenue.
3. **WS-2, WS-3, WS-5, WS-6 can begin API/CLI work in Week 1** before WS-1 completes. They only need WS-1 for billing integration and multi-tenant data.
4. **White-label (WS-2, Week 9-12) depends on WS-2 dashboard** being stable first. Do not attempt white-label before the core product is proven.
5. **No workstream depends on another workstream** (only on WS-1). This is by design.

---

## 7.3 Parallel Execution Model (Solo Developer)

As a solo developer, "all-parallel" means interleaving, not simultaneous coding. The weekly time allocation:

### Weekly Hour Budget: 50-60 hrs/week

| Block | Hours/Week | Activity |
|-------|-----------|----------|
| Deep Build | 30-35 | Primary product development (rotate focus weekly) |
| Content + Course | 8-10 | Recording, writing, curriculum |
| Sales + Marketing | 5-8 | Outreach, proposals, social posts |
| Ops + Support | 3-5 | Customer questions, monitoring, bug fixes |
| Planning + Review | 2-3 | Architecture decisions, progress tracking |

### Weekly Focus Rotation

| Week | Deep Build Focus | Parallel Activities |
|------|-----------------|-------------------|
| 1 | WS-1: Auth + Billing | WS-4: Curriculum finalization, WS-3: Package MCP servers |
| 2 | WS-1: DB Schema + Deploy | WS-4: Landing page, WS-6: CLI scaffolding |
| 3 | WS-2: Deepgram/Twilio | WS-4: Record modules 1-2, WS-5: API design |
| 4 | WS-2: GHL Call Flows | WS-3: Marketplace listing, WS-4: Record modules 3-4 |
| 5 | WS-5: Upload + Query API | WS-2: Bug fixes, WS-4: Record module 5 |
| 6 | WS-2: Multi-tenant dashboard | WS-5: Metering, WS-4: Record module 6 |
| 7 | WS-5: Usage dashboards | WS-6: Core features, WS-4: Record module 7 |
| 8 | WS-2: Dashboard polish | WS-5: Enterprise tier, WS-4: Record module 8 + launch Cohort 1 |
| 9 | WS-3: Community SDK | WS-2: White-label prep, WS-6: CI/CD integrations |
| 10 | WS-2: White-label provisioning | WS-3: Enterprise features, WS-5: SLA monitoring |
| 11 | WS-6: Team features | WS-2: White-label testing, WS-4: Self-paced conversion |
| 12 | Integration + polish | Launch reviews, retrospective, plan next quarter |

---

## 7.4 Milestones and Gates

### Week 4 Milestone: "First Revenue Gate"

| Workstream | Week 4 Deliverable | Revenue Status |
|------------|-------------------|---------------|
| WS-1 | Auth, billing, deploy pipeline LIVE | Enabling |
| WS-2 | Deepgram + Twilio integrated, GHL call flows working | Beta signups open |
| WS-3 | 3 MCP servers listed on Gumroad + MCP Server Store | First sales ($49-$149) |
| WS-4 | Modules 1-4 recorded, Cohort 1 pre-sales open ($797-$1,997) | Pre-sale revenue |
| WS-5 | API design complete, upload endpoint in staging | Waitlist open |
| WS-6 | CLI scaffolding + 2 core features in staging | Waitlist open |

**Gate criteria**: WS-1 must be production-ready. At least 1 product must have paying users or pre-sales.

### Week 8 Milestone: "Product-Market Signal Gate"

| Workstream | Week 8 Deliverable | Revenue Status |
|------------|-------------------|---------------|
| WS-1 | Stable, handling multi-product billing | Proven |
| WS-2 | Multi-tenant dashboard, 3-5 beta customers | $500-$2K MRR |
| WS-3 | 5+ servers listed, community SDK in beta | $1K-$3K MRR |
| WS-4 | Cohort 1 launched (Week 8), 20-40 students enrolled | $16K-$50K one-time |
| WS-5 | Upload + query + metering live, free tier available | First paid conversions |
| WS-6 | 3 core features live, free tier available | First paid conversions |

**Gate criteria**: Combined MRR > $2K (excluding course). At least 2 products have paying users. Course Cohort 1 is live.

**Decision point**: If any SaaS product has zero traction at Week 8, deprioritize it and reallocate hours to the products showing signal.

### Week 12 Milestone: "Scale Gate"

| Workstream | Week 12 Deliverable | Revenue Status |
|------------|-------------------|---------------|
| WS-1 | Auto-scaling, cost optimization | Mature |
| WS-2 | White-label ready, 10-15 customers | $3K-$8K MRR |
| WS-3 | Enterprise features, 50+ total server sales | $2K-$5K MRR |
| WS-4 | Cohort 1 complete, self-paced on Gumroad, Cohort 2 pre-sales | $4K-$8K/mo passive |
| WS-5 | Enterprise tier, SLA monitoring, 10-20 customers | $2K-$5K MRR |
| WS-6 | Team features, CI/CD integrations, 15-30 customers | $1K-$3K MRR |

**Gate criteria**: Total MRR > $10K. At least 3 products generating revenue. White-label program has 2+ resellers.

**Decision point**: Double down on top 2 revenue generators. Begin hiring first contractor for support/docs.

---

## 7.5 Critical Path Analysis

The critical path through the dependency graph:

```
WS-1 Auth (Week 1) → WS-1 Billing (Week 2) → WS-2 GHL Flows (Week 3-4) →
  WS-2 Dashboard (Week 5-8) → WS-2 White-Label (Week 9-12)
```

**Total critical path**: 12 weeks. Voice AI is the longest chain because it has the most dependencies (shared infra -> core product -> white-label layer).

**Critical path risk mitigation**:
- Start Deepgram/Twilio integration in Week 1 (before WS-1 completes) using hardcoded test credentials
- Use Stripe test mode for billing development in parallel with auth
- Ship WS-2 dashboard as "beta" in Week 6, iterate based on feedback through Week 8
- White-label can slip to Week 13-14 without impacting other revenue streams

### Parallel Paths (Non-Critical)

| Path | Duration | Slack |
|------|----------|-------|
| WS-4: Course (fully independent) | 8 weeks recording + 4 weeks conversion | Can slip 4 weeks without revenue impact |
| WS-3: MCP Toolkit | 4 weeks to first sale, 12 weeks to enterprise | 2 weeks slack |
| WS-6: AI DevOps | 4 weeks to MVP, 12 weeks to enterprise | 4 weeks slack (lowest priority SaaS) |
| WS-5: RAG SaaS | 4 weeks to API, 12 weeks to enterprise | 2 weeks slack |

---

## 7.6 Revenue Waterfall (Cumulative)

```
         Month 1    Month 2    Month 3    Month 4    Month 5    Month 6
         ────────   ────────   ────────   ────────   ────────   ────────
Course     $0       $0        $16-50K    $4-8K/mo   $4-8K/mo   $4-8K/mo
                                (Cohort 1) (self-paced)(self-paced)(self-paced)

MCP       $500     $1.5K      $3K        $3.5K      $4K        $5K
Toolkit   (first   (growing)  (+ svc)    (+ svc)    (+ enterprise)
           sales)

Voice AI   $0       $0        $500       $2K        $4K        $8K
                              (beta)     (growing)  (+ white-   (scaling)
                                                     label)

RAG SaaS   $0       $0        $500       $1.5K      $3K        $5K
                              (free→paid)(growing)  (enterprise)(scaling)

DevOps     $0       $500      $1.5K      $2K        $2.5K      $3K
           (waitlist)(first    (growing)  (CI/CD)    (teams)    (scaling)
                     sales)

Services  $2.5K    $5K        $7.5K      $7.5K      $10K       $10K
          (consult)(consult+  (impl      (impl      (retainer  (retainer
           only)    impl)      + consult) + consult) + impl)    + impl)

Templates  $200     $800      $1.5K      $3K        $5K        $7K

TOTAL     $3.2K    $7.8K     $30-63K    $23-27K    $32-36K    $42-46K
MRR                          (+course)  /mo        /mo        /mo
```

**Cumulative revenue through Month 6**: $138K-$215K (realistic to optimistic).

---

# SECTION 8: Risk Register

Each risk is assessed on Likelihood (1-5) and Impact (1-5), producing a Risk Score (L x I). Risks scoring 15+ require active mitigation. Risks scoring 10-14 require monitoring. Risks below 10 are accepted.

---

## 8.1 Risk Matrix Overview

| ID | Risk | Likelihood | Impact | Score | Category |
|----|------|-----------|--------|-------|----------|
| R1 | Solo developer spread-thin | 5 | 4 | **20** | Operational |
| R2 | Voice AI price race to bottom | 4 | 4 | **16** | Market |
| R3 | MCP protocol instability | 3 | 5 | **15** | Technical |
| R4 | Course market saturation | 3 | 3 | **9** | Market |
| R5 | Regulatory whiplash (AI Act, state laws) | 3 | 4 | **12** | Compliance |
| R6 | Infrastructure cost overrun | 3 | 3 | **9** | Financial |
| R7 | Key dependency failure (Deepgram, Twilio) | 2 | 5 | **10** | Technical |
| R8 | Customer concentration | 3 | 3 | **9** | Business |
| R9 | Burnout and quality degradation | 4 | 4 | **16** | Operational |
| R10 | Competitor launches identical product | 3 | 3 | **9** | Market |

---

## 8.2 Detailed Risk Analyses

### R1: Solo Developer Spread-Thin (Score: 20 -- HIGHEST)

**Description**: Running 5 products, a course, implementation services, and content marketing as a single developer creates operational drag. More apps mean more tech debt, more support tickets, more context-switching. Quality drops. Shipping slows. Revenue stalls.

**Evidence**: Research confirms "operational drag is real -- more apps mean more tech debt." Solo SaaS founders who launch 3+ products simultaneously report 40-60% slower iteration cycles.

**Mitigation strategies (all required)**:

1. **Strict MVP scoping per product**. Each product's Week 4 deliverable is the absolute minimum for a paying customer. No feature creep before product-market signal.
2. **Weekly focus rotation** (Section 7.3). Deep work on one product per week, not all five every day.
3. **Automated everything**. CI/CD deploys, Sentry alerts, PostHog funnels, Stripe billing. Zero manual ops work.
4. **Kill switch at Week 8**. Any product with zero paying users at Week 8 gets shelved. No sunk-cost fallacy.
5. **Hire contractor at $10K MRR**. First hire is a part-time support/docs person ($20-$30/hr, 10-15 hrs/week) to free up 10-15 hrs/week of developer time.
6. **Template and framework reuse**. Shared infrastructure (WS-1) means each new product reuses auth, billing, monitoring, and deployment. Incremental product cost is 30-40% less than standalone.

**Residual risk after mitigation**: Moderate (Score: 12). Spread-thin is inherent to the strategy; mitigation reduces but cannot eliminate it.

**Trigger for escalation**: If Week 4 gate is missed by more than 1 week, cut one workstream immediately.

---

### R2: Voice AI Price Race to Bottom (Score: 16 -- HIGH)

**Description**: Voice AI infrastructure is commoditizing fast. Ringg AI already offers $0.08/min all-inclusive. Deepgram Voice Agent is $4.50/hr (~$0.075/min). As more providers enter, per-minute pricing collapses toward cost (~$0.04-$0.06/min), squeezing margins.

**Evidence**: Ringg AI pricing at $0.08/min all-inclusive already compresses margins for non-integrated providers. Floor pricing is converging on $0.10-$0.15/min for value-add platforms, $0.06-$0.08/min for raw infrastructure.

**Mitigation strategies**:

1. **Differentiate on GHL-native integration, not price**. Raw voice AI is commodity. Voice AI that reads GHL contacts, triggers GHL workflows, updates CRM fields, and books GHL calendar slots is not. Charge for the integration, not the minutes.
2. **Anchor pricing on value, not cost**. A real estate agent who converts one additional lead via voice AI earns $5K-$15K in commission. Price the product at 1-5% of that value ($99-$299/mo), not as a markup on Deepgram minutes.
3. **Bundle minutes into flat plans**. Customers prefer predictable billing. Flat monthly plans with included minutes have higher retention than pure per-minute pricing.
4. **Move up-market to white-label**. White-label margins ($100-$300/client/mo) are insulated from infrastructure price wars because the value is in the managed service, not the minutes.
5. **Monitor competitor pricing quarterly**. If floor drops below $0.08/min, adjust included minutes upward rather than cutting price.

**Residual risk after mitigation**: Moderate (Score: 10). GHL-native integration creates meaningful differentiation, but voice AI commoditization is a structural trend.

**Trigger for escalation**: If two or more competitors offer GHL-native voice AI at <$79/mo, reassess positioning.

---

### R3: MCP Protocol Instability (Score: 15 -- HIGH)

**Description**: MCP is a moving target. OAuth 2.1 introduced breaking changes. The spec is evolving rapidly with multiple competing interpretations. Google's A2A protocol could fragment the market. Building products on an unstable protocol risks frequent breaking changes and customer frustration.

**Evidence**: Gartner flags MCP as "a moving target" in 2026. OAuth 2.1 integration broke existing auth flows. A2A (Google) and ACP (Cisco/LangChain) represent competing agent protocol visions.

**Mitigation strategies**:

1. **Abstraction layer between products and MCP spec**. All MCP interactions go through a `mcp-adapter` module that isolates spec changes to a single file. Products never call MCP primitives directly.

   ```
   Product Code → mcp-adapter (you control) → MCP Protocol (they control)
   ```

2. **A2A compatibility layer**. Build the adapter to support both MCP and A2A from Day 1. If A2A gains traction, flip a config flag. Cost: ~8 extra hours in WS-3.
3. **Pin to stable MCP versions**. Do not track bleeding-edge spec changes. Pin to the latest stable release and upgrade quarterly after testing.
4. **Spec change monitoring**. Subscribe to MCP GitHub releases and Anthropic announcements. Allocate 4-8 hrs/quarter for protocol updates.
5. **Sell the value, not the protocol**. Marketing says "connects your AI to your tools" not "MCP-compliant server." If MCP is replaced, the product narrative survives.

**Residual risk after mitigation**: Moderate (Score: 9). Abstraction layer reduces breaking-change impact to hours, not weeks. Protocol fragmentation is the harder risk.

**Trigger for escalation**: If A2A captures >30% market share, build a full A2A product line (not just compatibility).

---

### R4: Course Market Saturation (Score: 9 -- ACCEPTED)

**Description**: Maven hosts dozens of AI/ML courses at $500-$2,500. Udemy, Coursera, and YouTube flood the market with cheaper alternatives. Standing out requires a genuine differentiator.

**Evidence**: Maven marketplace is crowded with AI courses. Average course creator earns $2K-$10K per cohort unless they have existing audience or unique positioning.

**Mitigation strategies**:

1. **"Production repos" differentiator**. Every course module includes a real, tested, deployed repository -- not a toy demo. Students leave with portfolio-ready code. This is rare in the market and addresses the #1 complaint about AI courses ("I learned concepts but can't build anything real").
2. **Lean into portfolio metrics**. 8,500+ tests, 89% cost reduction, 4.3M dispatches/sec, $50M+ pipeline managed. These are verifiable, impressive, and differentiate from instructors who teach theory.
3. **Cohort model before self-paced**. Cohorts create urgency, community, and higher prices ($797-$1,997 vs $397 self-paced). They also generate testimonials that sell future cohorts.
4. **Free Week 1 preview**. Lower the risk for buyers. If Week 1 is genuinely valuable, conversion to paid is 15-25%.

**Residual risk**: Low. The differentiator is genuine and hard to replicate. Accept the risk.

---

### R5: Regulatory Whiplash (Score: 12 -- MONITOR)

**Description**: EU AI Act high-risk rules take effect August 2026. US regulatory landscape is fragmented and uncertain. Voice AI in real estate touches Fair Housing, TCPA, CCPA, and potentially new AI disclosure laws. Compliance features may become mandatory, and requirements could change rapidly.

**Evidence**: EU AI Act classifies real estate AI as potentially high-risk (affects property access decisions). CalypsoAI ($180M acquisition by F5), Prompt Security ($250M by SentinelOne), and Lakera (acquired by Check Point) show the compliance market is consolidating around enterprise players.

**Mitigation strategies**:

1. **Embed compliance features, do not sell them standalone**. Compliance is a feature of Voice AI and RAG, not a separate product. This avoids competing with $180M-funded compliance platforms.
2. **TCPA compliance from Day 1**. All voice calls include AI disclosure ("This is Jorge, an AI assistant"). All SMS includes opt-out. These are already implemented in EnterpriseHub's response pipeline.
3. **PII handling via Presidio**. Open-source, runs locally, zero cost. All voice transcripts and RAG documents pass through PII detection before storage.
4. **Quarterly compliance review**. 2-4 hrs/quarter to review regulatory changes and update compliance features.
5. **Fair Housing guardrails**. Voice AI and Lead Bot already have Fair Housing compliance in their response pipeline (no steering, no discrimination). Document this prominently.

**Residual risk**: Moderate. Regulatory changes are unpredictable, but embedded compliance posture is the correct defensive position.

**Trigger for escalation**: If US federal AI regulation passes with specific disclosure requirements, allocate a full sprint for compliance updates.

---

### R6: Infrastructure Cost Overrun (Score: 9 -- ACCEPTED)

**Description**: Multi-product deployment on Railway/Render/Fly.io could exceed budget if usage scales faster than revenue.

**Mitigation**: Usage-based pricing passes infrastructure costs to customers. Free tiers are capped (100 queries/mo for RAG, 50 min/mo for Voice AI). Monitor cost-per-customer weekly.

**Trigger**: If infrastructure cost exceeds 30% of revenue, optimize or raise prices.

---

### R7: Key Dependency Failure (Score: 10 -- MONITOR)

**Description**: If Deepgram, Twilio, ElevenLabs, or Stripe experience extended outages or discontinue services, products are immediately impacted.

**Mitigation strategies**:

1. **Multi-provider abstraction for STT/TTS**. Deepgram is primary; add OpenAI Whisper as fallback STT, OpenAI TTS as fallback TTS. Abstraction layer makes switching a config change.
2. **Twilio alternatives pre-evaluated**. Vonage and Telnyx are drop-in replacements for SIP trunking. Document the switch process.
3. **Stripe is effectively irreplaceable**. Accept this dependency. Stripe's uptime is 99.999%+.
4. **No single dependency accounts for >40% of COGS**. Diversify infrastructure providers.

**Trigger**: If any provider has >2 outages in a month, begin active migration to backup.

---

### R8: Customer Concentration (Score: 9 -- ACCEPTED)

**Description**: Early revenue may come from 3-5 large clients (implementation services, retainers), creating concentration risk.

**Mitigation**: Prioritize SaaS and course revenue (many small customers) over services (few large customers). Target: no single customer >20% of revenue by Month 6.

---

### R9: Burnout and Quality Degradation (Score: 16 -- HIGH)

**Description**: 50-60 hrs/week across 5 products, a course, services, and marketing is unsustainable beyond 3-4 months. Burnout leads to bugs, missed deadlines, poor customer experience, and potential health consequences.

**Evidence**: Solo SaaS founders report burnout as the #1 reason for abandoning products. 60+ hr/week schedules show measurable quality decline after 8-10 weeks.

**Mitigation strategies**:

1. **Hard cap at 55 hrs/week**. No exceptions. Track hours weekly.
2. **One full day off per week**. Non-negotiable. Calendar-blocked.
3. **Week 8 kill switch** reduces scope. Dropping 1-2 underperforming products immediately reduces workload by 20-30%.
4. **Automate aggressively**. Every hour spent on automation saves 2-5 hours over the quarter. CI/CD, monitoring alerts, billing, and customer onboarding should require zero manual intervention.
5. **Contractor at $10K MRR**. First hire absorbs support, docs, and routine bug fixes.
6. **Monthly retrospective**. Check energy levels, not just revenue. If Week 6 retrospective shows declining motivation, cut scope immediately -- do not wait for Week 8.

**Residual risk after mitigation**: Moderate (Score: 10). Burnout risk is structural in a solo multi-product launch. Mitigation reduces severity but cannot eliminate it.

**Trigger for escalation**: Two consecutive weeks of missed deliverables or declining code quality (test failures, Sentry error spikes).

---

### R10: Competitor Launches Identical Product (Score: 9 -- ACCEPTED)

**Description**: Another developer or small team launches a GHL-native voice AI, MCP marketplace, or similar product.

**Mitigation**: Speed to market + production quality (8,500+ tests, verified metrics) + existing GHL integration create a 3-6 month moat. Course and content create brand moat. First-mover in GHL-native voice AI is a defensible position.

---

## 8.3 Risk Response Decision Framework

```
Risk Score 15+  →  MITIGATE (active investment in countermeasures)
Risk Score 10-14 →  MONITOR (quarterly review, trigger-based response)
Risk Score <10  →  ACCEPT (document and move on)
```

### Quarterly Risk Review Checklist

- [ ] Re-score all 10 risks based on current market conditions
- [ ] Check all trigger conditions -- has any been hit?
- [ ] Review mitigation effectiveness -- are countermeasures working?
- [ ] Identify new risks from customer feedback, competitor moves, or regulatory changes
- [ ] Update this register with findings

---

# SECTION 9: GTM Technical Requirements

Go-to-market execution requires specific technical assets per product, plus cross-cutting launch strategies and funnel metrics. This section defines what must be built, published, and measured.

---

## 9.1 Per-Product GTM Assets

### 9.1.1 Voice AI Agent Platform

| Asset | Description | Priority | Effort |
|-------|------------|----------|--------|
| Gumroad Page | Dashboard screenshots, GHL integration demo, call flow diagrams, pricing table | P0 | 3 hrs |
| Documentation Site | Quickstart guide, API reference, GHL setup guide, compliance guide (TCPA, Fair Housing) | P0 | 8 hrs |
| Demo Phone Number | Inbound demo line that prospects can call to experience the AI agent | P0 | 4 hrs |
| Video Walkthrough | 3-5 min product demo showing GHL integration, call handling, analytics | P1 | 4 hrs |
| Case Study | "How [Brokerage X] automated 60% of inbound calls" (after first customer) | P1 | 3 hrs |
| Monitoring | Sentry (errors), PostHog (product analytics), custom call metrics dashboard | P0 | 4 hrs |

### 9.1.2 MCP Server Toolkit and Marketplace

| Asset | Description | Priority | Effort |
|-------|------------|----------|--------|
| Gumroad Page | MCP Inspector screenshots, code examples, "pip install" one-liner | P0 | 2 hrs |
| PyPI Package | Published, versioned, with README and examples | P0 | 2 hrs |
| Documentation Site | Quickstart per server, framework integration guide, custom server tutorial | P0 | 6 hrs |
| `mcp dev` Command | Interactive development mode for testing servers locally | P1 | 4 hrs |
| GitHub Repo | Public repo with stars, issues, and contributor guidelines | P0 | 2 hrs |
| Monitoring | PyPI download stats, GitHub stars tracker, Gumroad sales dashboard | P0 | 2 hrs |

### 9.1.3 Cohort Course

| Asset | Description | Priority | Effort |
|-------|------------|----------|--------|
| Landing Page | Curriculum preview, instructor bio, testimonials, countdown timer | P0 | 4 hrs |
| ConvertKit Funnel | Email sequence: free preview -> nurture (5 emails) -> sales (3 emails) -> onboarding | P0 | 4 hrs |
| Maven Listing | If using Maven: course description, pricing, schedule | P1 | 2 hrs |
| Free Week 1 Preview | First module available free on Gumroad as lead magnet | P0 | 2 hrs |
| Lab Repositories | 8 GitHub repos, one per module, with tests and CI | P0 | Included in WS-4 |
| Certificate | Completion certificate via Certifier (free tier) | P2 | 1 hr |
| Monitoring | ConvertKit open/click rates, Gumroad conversion rates, completion rates (custom tracking) | P0 | 2 hrs |

### 9.1.4 RAG-as-a-Service

| Asset | Description | Priority | Effort |
|-------|------------|----------|--------|
| Gumroad Page | Upload flow screenshots, query interface demo, API playground link | P0 | 3 hrs |
| Documentation Site | Quickstart, API reference, Python SDK examples, evaluation guide | P0 | 6 hrs |
| Interactive Demo | Free tier: 100 queries/month on a sample knowledge base | P0 | 4 hrs |
| API Playground | Swagger/OpenAPI interactive docs at `/docs` endpoint | P0 | 1 hr (FastAPI built-in) |
| Video Walkthrough | 2-3 min showing document upload, querying, and eval dashboard | P1 | 3 hrs |
| Monitoring | Sentry (errors), PostHog (funnels), Stripe (revenue), custom query metrics | P0 | 3 hrs |

### 9.1.5 AI DevOps Suite

| Asset | Description | Priority | Effort |
|-------|------------|----------|--------|
| Gumroad Page | Feature list, pricing tiers, integration logos (GitHub, GitLab, Jenkins) | P0 | 2 hrs |
| Documentation Site | CLI quickstart, API docs, CI/CD integration guides | P0 | 5 hrs |
| Free Tier | Limited features, no credit card required | P0 | 2 hrs |
| CLI Demo GIF | Terminal recording showing key commands | P1 | 1 hr |
| Monitoring | Sentry (errors), usage metrics per command, Stripe revenue | P0 | 2 hrs |

---

## 9.2 Product Hunt Launch Strategy

Product Hunt is the highest-impact single-day launch event for developer tools. A top-4 ranking generates approximately 1,500 unique visitors per day during the featured period.

### Launch Plan

| Phase | Timeline | Actions |
|-------|----------|---------|
| Pre-Launch (T-30 days) | 30 days before | Build "Coming Soon" page, collect emails, recruit 5-10 hunters to upvote |
| Pre-Launch (T-7 days) | 7 days before | Finalize tagline, screenshots, maker comment, first-day offer |
| Launch Day (T+0) | 12:01 AM PST | Publish listing, post maker comment, email list, share on social |
| Launch Day (T+0 to T+12h) | First 12 hours | Respond to every comment within 30 min, share on Twitter/LinkedIn/Reddit |
| Post-Launch (T+1 to T+7) | Week after | Follow up with all signups, publish "lessons learned" blog post |

### Launch Sequence (Which Product When)

| Order | Product | Why This Order | Target Date |
|-------|---------|---------------|-------------|
| 1st | MCP Server Toolkit | Lowest risk, developer audience matches PH perfectly | Week 4-5 |
| 2nd | RAG-as-a-Service | Strong demo potential, free tier drives signups | Week 8-9 |
| 3rd | Voice AI Platform | Needs more polish, GHL audience is smaller on PH | Week 10-12 |
| 4th | AI DevOps Suite | Needs traction data before PH launch | Month 4+ |

**Rule**: Maximum one Product Hunt launch per month. Space them out for sustained visibility.

---

## 9.3 Hacker News Show HN Strategy

Hacker News "Show HN" posts drive significant developer traffic when executed correctly. Successful posts average 289 GitHub stars/week. 62% of Show HN posts are developer tools.

### Posting Playbook

| Attribute | Recommendation |
|-----------|---------------|
| Best days | Tuesday or Wednesday |
| Best time | 8:00-11:00 AM UTC (28% more engagement) |
| Title format | "Show HN: [Product Name] -- [one-line value prop]" |
| Content | Link to GitHub repo (not Gumroad). Technical details in comments. |
| First comment | Post immediately: what it does, why you built it, technical decisions, what's next |
| Engagement | Respond to every comment substantively. HN rewards depth. |

### Per-Product HN Angles

| Product | HN Title | Why It Works on HN |
|---------|----------|-------------------|
| MCP Toolkit | "Show HN: Open-source MCP servers for Postgres, Redis, and Stripe" | OSS + hot protocol + practical |
| RAG SaaS | "Show HN: RAG-as-a-Service with built-in eval pipeline" | Technical depth + eval is underserved |
| AI DevOps | "Show HN: AI-powered DevOps CLI that catches deployment issues" | Developer pain point + CLI = HN catnip |
| Voice AI | "Show HN: Voice AI agents with native GHL/CRM integration" | Less natural HN fit; save for last |

---

## 9.4 Content Marketing Engine

Technical blog content is the highest-converting channel for developer tools. Each post serves dual purpose: SEO traffic + social sharing + authority building.

### Content Calendar (First 12 Weeks)

| Week | Topic | Target Product | Distribution |
|------|-------|---------------|-------------|
| 1 | "Building Production MCP Servers: Lessons from 5 Deployments" | MCP Toolkit | Blog, HN, LinkedIn, Reddit r/MachineLearning |
| 2 | "Voice AI Cost Breakdown: What $0.10/min Actually Buys You" | Voice AI | Blog, LinkedIn, GHL Community |
| 3 | "RAG Evaluation: Why Most Benchmarks Are Lying to You" | RAG SaaS | Blog, HN, Twitter |
| 4 | "MCP vs A2A vs ACP: A Practical Comparison (Feb 2026)" | MCP Toolkit | Blog, HN, dev.to |
| 5 | "How I Automated 60% of Real Estate Calls with AI" | Voice AI | Blog, LinkedIn, BiggerPockets |
| 6 | "Building a Multi-Tenant RAG API in 80 Hours" | RAG SaaS | Blog, HN, dev.to |
| 7 | "The Solo Developer's Guide to Launching 5 AI Products" | All | Blog, HN, IndieHackers |
| 8 | "Production AI Testing: 8,500 Tests and What They Taught Me" | Course | Blog, HN, LinkedIn |
| 9 | "GHL + Voice AI: The Stack That Replaced 3 SDRs" | Voice AI | Blog, GHL Community, LinkedIn |
| 10 | "MCP Server Marketplace Economics: What Developers Will Pay" | MCP Toolkit | Blog, HN, Twitter |
| 11 | "RAG in Production: P95 Latency, Eval Pipelines, and Real Costs" | RAG SaaS | Blog, HN, dev.to |
| 12 | "Lessons from Cohort 1: Teaching AI Engineering to 30 Developers" | Course | Blog, LinkedIn, Twitter |

### Content Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Blog posts/month | 4 (1/week) | Manual count |
| Avg post views (30-day) | 500+ | PostHog |
| Email subscribers | 500 by Week 12 | ConvertKit |
| HN front page hits | 2 in 12 weeks | Manual tracking |
| Blog -> signup conversion | 3-5% | PostHog funnel |

---

## 9.5 Customer Acquisition Cost (CAC) Targets

### Per-Channel CAC Targets

| Channel | Target CAC | Expected Volume | Notes |
|---------|-----------|----------------|-------|
| Organic content (blog, HN, PH) | $0-$50 | 60% of customers | Highest ROI, slowest ramp |
| Referral/affiliate program | $50-$100 | 15% of customers | 20% recurring commission |
| LinkedIn outreach | $100-$200 | 10% of customers | Time-intensive, high conversion |
| daily.dev ads | $200-$400 | 10% of customers | 1M+ devs daily, granular targeting |
| Google Ads (branded) | $300-$600 | 5% of customers | Only after brand awareness exists |

### Blended CAC Target

| Segment | Target CAC | Target LTV | LTV:CAC Ratio |
|---------|-----------|-----------|---------------|
| Self-serve SaaS (SMB) | $300-$500 | $1,500-$3,000 | 5:1 |
| Enterprise SaaS | $500-$900 | $5,000-$15,000 | 8:1+ |
| Course (self-paced) | $50-$100 | $397-$497 | 5:1 |
| Course (cohort) | $100-$200 | $797-$1,997 | 8:1+ |
| Implementation services | $200-$500 | $5,000-$15,000 | 15:1+ |

**Industry benchmark**: SaaS average CAC is $702 for SMB segment. Target below this via organic-heavy acquisition.

---

## 9.6 Conversion Funnel Metrics

### SaaS Funnel (Target)

```
Visitor → Signup → Activation → Trial → Paid → Retained (12mo)
  100%     12%       60%         40%     18%      70%
```

| Stage | Metric | Target | Measurement |
|-------|--------|--------|-------------|
| Visitor -> Signup | Registration rate | 12% | PostHog |
| Signup -> Activation | First meaningful action within 24hrs | 60% | PostHog custom event |
| Activation -> Trial | Starts using paid features (free tier) | 40% | Product analytics |
| Trial -> Paid | Converts to paid plan (opt-in, credit card) | 18.2% | Stripe |
| Paid -> Retained (monthly) | Still paying after 30 days | 85% | Stripe |
| Paid -> Retained (annual) | Still paying after 12 months | 70% | Stripe |

**Key benchmark**: 18.2% free trial to paid (opt-in with credit card) is the industry average. Target this or higher via strong onboarding.

### Course Funnel (Target)

```
Landing Page → Email Signup → Free Preview → Cohort Purchase → Completion → Testimonial
    100%          20%            50%             15%              80%           30%
```

| Stage | Metric | Target |
|-------|--------|--------|
| Page -> Email | Email capture rate | 20% |
| Email -> Free Preview | Downloads free Week 1 | 50% |
| Preview -> Purchase | Buys cohort or self-paced | 15% |
| Purchase -> Completion | Finishes all 8 modules | 80% |
| Completion -> Testimonial | Provides written/video testimonial | 30% |

---

## 9.7 Monitoring Stack

All products share a common monitoring stack to reduce setup overhead and enable cross-product analytics.

| Layer | Tool | Purpose | Cost |
|-------|------|---------|------|
| Error Tracking | Sentry | Exception capture, performance monitoring, release tracking | Free tier (5K events/mo) |
| Product Analytics | PostHog | Funnels, session recordings, feature flags, A/B testing | Free self-hosted or $0 for <1M events |
| Revenue Analytics | Stripe Dashboard + custom | MRR, churn, LTV, cohort analysis | Free (included with Stripe) |
| Custom Dashboards | Streamlit (reuse Insight Engine) | Per-product metrics, call analytics, query volumes | Self-hosted, ~$0 |
| Email Analytics | ConvertKit | Open rates, click rates, sequence performance | Free up to 1K subscribers |
| Uptime Monitoring | UptimeRobot or Sentry | Endpoint health checks, SSL monitoring | Free tier |
| Log Aggregation | Railway/Render built-in | Application logs, deploy logs | Included with hosting |

### Per-Product Monitoring Priorities

| Product | P0 Metrics | Alert Threshold |
|---------|-----------|----------------|
| Voice AI | Call completion rate, avg latency, cost/min | Completion <90%, latency >2s, cost >$0.08/min |
| MCP Toolkit | PyPI downloads, error rate, GitHub stars | Error rate >5%, downloads declining week-over-week |
| Course | Enrollment rate, completion rate, NPS | Completion <70%, NPS <40 |
| RAG SaaS | Query latency (P95), eval scores, usage/customer | P95 >500ms, eval <0.7, usage declining |
| AI DevOps | CLI error rate, feature adoption, retention | Error rate >3%, <50% feature adoption after 30 days |

---

# SECTION 10: External Service Pricing

All pricing data as of February 2026. Infrastructure costs are the floor below which product pricing must not drop.

---

## 10.1 Speech and Voice Services

### Deepgram

| Service | Free Tier | Pay-As-You-Go Rate | Notes |
|---------|-----------|-------------------|-------|
| Nova-3 STT | $200 credit | $0.0077/min | Per-second billing, best accuracy/price ratio |
| Nova-3 STT (streaming) | Included in credit | $0.0077/min | WebSocket, <300ms first-byte |
| Voice Agent API | $200 credit | $4.50/hr all-inclusive | Integrated STT + LLM routing + TTS |
| Text-to-Speech (Aura) | Included in credit | $0.015/1K chars | Limited voices, improving |

**Key insight**: Deepgram Voice Agent at $4.50/hr ($0.075/min) is the all-in price floor for building voice AI agents. Any per-minute pricing below $0.10/min has negative margin when including LLM and TTS costs.

### ElevenLabs

| Service | Free Tier | Pay-As-You-Go Rate | Notes |
|---------|-----------|-------------------|-------|
| Flash v2 (low-latency) | 10K chars/mo | $0.08/1K chars | ~75ms latency, best for real-time |
| Multilingual v2 | 10K chars/mo | $0.17/1K chars | ~250ms latency, 29 languages |
| Turbo v2.5 | 10K chars/mo | $0.12/1K chars | Balance of speed and quality |
| Voice cloning | Included | Included with plan | Custom brand voices |

**Key insight**: ElevenLabs Flash at $0.08/1K chars is approximately $0.015-$0.025/min for typical real estate conversations (150-250 words/min). Combined with Deepgram STT, raw STT+TTS cost is ~$0.02-$0.03/min.

### Twilio

| Service | Free Tier | Rate | Notes |
|---------|-----------|------|-------|
| Inbound Voice (Local US) | None | $0.0085/min | Per-second billing |
| Outbound Voice (Local US) | None | $0.0140/min | Per-second billing |
| Phone Number (Local) | None | $2.00/mo | Per number |
| Phone Number (Toll-Free) | None | $3.00/mo | Per number |
| SIP Trunking | None | $0.007/min | Cheapest for high volume |
| SMS (Outbound) | None | $0.0079/segment | 160 chars/segment |

---

## 10.2 Cost-Per-Minute Breakdown (Voice AI)

Understanding the true cost per minute of a voice AI call is critical for pricing.

| Component | Cost/Min | % of Total |
|-----------|----------|-----------|
| Deepgram STT (Nova-3) | $0.0077 | 15% |
| ElevenLabs TTS (Flash) | $0.020 | 39% |
| Twilio Inbound | $0.0085 | 17% |
| LLM (Claude Haiku) | $0.010 | 20% |
| Infrastructure (compute) | $0.005 | 9% |
| **Total COGS/min** | **$0.051** | **100%** |

### Margin Analysis by Pricing Tier

| Customer Pays | COGS | Gross Margin | Margin % |
|--------------|------|-------------|----------|
| $0.08/min (commodity) | $0.051 | $0.029 | 36% |
| $0.10/min (budget) | $0.051 | $0.049 | 49% |
| $0.12/min (standard) | $0.051 | $0.069 | 58% |
| $0.15/min (premium) | $0.051 | $0.099 | 66% |
| $0.20/min (enterprise) | $0.051 | $0.149 | 75% |

**Minimum viable price**: $0.10/min (49% margin). Below this, margins are too thin to cover support, billing overhead, and platform costs.

**Target price**: $0.12-$0.15/min blended, achieved through flat monthly plans with included minutes.

---

## 10.3 Payment and Billing

### Stripe

| Service | Cost | Notes |
|---------|------|-------|
| Card Processing | 2.9% + $0.30/txn | Standard US rate |
| Metered Billing | Free | Usage-based billing included |
| Stripe Connect (for white-label) | 0.5% + $2/mo per connected account | Automated reseller payouts |
| Invoicing | Free up to 25/mo | For enterprise/implementation clients |
| Billing Portal | Free | Customer self-service for upgrades/cancellations |

### Gumroad (for templates, course, one-time products)

| Channel | Fee | Notes |
|---------|-----|-------|
| Direct Link | 10% + $0.50/tx | Use for all self-driven traffic |
| Discover (marketplace) | 30% | Use only for marketplace visibility |
| Affiliate Payouts | Configurable | Built-in affiliate tracking |

---

## 10.4 Deployment Platforms

### Comparison Matrix

| Platform | Starter Cost | Small App | Database | Best For |
|----------|-------------|-----------|----------|---------|
| Railway | $5/mo credit | $30/mo (1 vCPU, 1GB) | $10/mo (1GB PG) | Best DX, fast deploys |
| Render | 750 free hrs | $7-$25/mo | $7/mo (256MB PG) | Cheapest managed Postgres |
| Fly.io | ~$5/mo waived | $10.70/mo (shared-1x) | $7/mo (1GB PG) | Edge-native, global |
| Hetzner (VPS) | N/A | $4.50/mo (2 vCPU, 2GB) | Self-managed | Cheapest compute, most effort |

### Recommended Stack

| Component | Platform | Monthly Cost | Why |
|-----------|----------|-------------|-----|
| API servers (FastAPI) | Railway | $30-$60/mo (2 instances) | Best DX, instant rollback |
| PostgreSQL | Render | $7-$25/mo | Cheapest managed PG, daily backups |
| Redis | Railway or Upstash | $0-$10/mo | Upstash free tier: 10K commands/day |
| Static sites (docs) | Cloudflare Pages | $0 | Free, global CDN |
| Streamlit dashboards | Railway | $15-$30/mo | Co-located with API |

**Total infrastructure cost (startup phase)**: $52-$125/month.

**At scale (100 customers)**: $200-$400/month. Infrastructure cost should be <15% of revenue.

---

## 10.5 AI and LLM Providers

| Provider | Model | Input Cost | Output Cost | Use Case |
|----------|-------|-----------|-------------|----------|
| Anthropic | Claude Haiku 3.5 | $0.80/MTok | $4.00/MTok | Voice AI real-time responses |
| Anthropic | Claude Sonnet 4 | $3.00/MTok | $15.00/MTok | RAG complex queries |
| Anthropic | Claude Opus 4 | $15.00/MTok | $75.00/MTok | Course content, architecture |
| OpenAI | GPT-4o mini | $0.15/MTok | $0.60/MTok | Fallback, cost-sensitive tasks |
| Google | Gemini 2.0 Flash | $0.10/MTok | $0.40/MTok | High-volume, cost-sensitive |

**Key insight**: Voice AI uses Haiku for real-time (adds ~$0.01/min to call cost). RAG uses Sonnet for quality. Course uses Opus for content quality. Match model tier to use case.

---

## 10.6 Supporting Services

| Service | Free Tier | Paid Tier | Use Case |
|---------|-----------|-----------|----------|
| ConvertKit | 1K subscribers | $29+/mo (1K-5K subs) | Email marketing for course funnel |
| Certifier | Free tier available | $49+/mo | Course completion certificates |
| Maven | Free to list | 10-20% revenue share | Cohort course marketplace |
| PostHog | 1M events/mo (self-hosted unlimited) | $0 self-hosted | Product analytics |
| Sentry | 5K errors/mo | $26+/mo (50K errors) | Error tracking |
| UptimeRobot | 50 monitors | $7+/mo | Uptime monitoring |
| Presidio | Free (OSS) | $0 | PII detection, runs locally |
| GitHub | Free (public repos) | $4/mo (private) | Code hosting, CI/CD |

---

## 10.7 Monthly Cost Projection

### Phase 1 (Month 1-3): Building

| Category | Monthly Cost | Notes |
|----------|-------------|-------|
| Deployment (Railway + Render) | $52-$80 | 2 API instances + DB + Redis |
| Deepgram | $0 (credit) | $200 free credit covers ~26K min |
| ElevenLabs | $0-$22 | Free tier or Starter plan |
| Twilio | $10-$30 | 1-2 numbers + dev usage |
| Stripe | $0 | Free until processing payments |
| ConvertKit | $0 | Free under 1K subscribers |
| Sentry | $0 | Free tier |
| PostHog | $0 | Self-hosted |
| Domain + DNS | $15 | Cloudflare |
| **Total** | **$77-$147/mo** | |

### Phase 2 (Month 4-6): Growing

| Category | Monthly Cost | Notes |
|----------|-------------|-------|
| Deployment | $100-$200 | Scaling with customers |
| Deepgram | $50-$200 | Credit exhausted, usage-based |
| ElevenLabs | $22-$99 | Starter to Growth plan |
| Twilio | $30-$100 | More numbers + production calls |
| Stripe | 2.9% of revenue | Processing fees |
| ConvertKit | $0-$29 | Approaching 1K subscribers |
| Sentry | $0-$26 | May exceed free tier |
| PostHog | $0 | Self-hosted |
| **Total** | **$202-$654/mo** | |

### Phase 3 (Month 7-12): Scaling

| Category | Monthly Cost | Notes |
|----------|-------------|-------|
| Deployment | $200-$400 | Multi-instance, auto-scaling |
| Deepgram | $200-$1,000 | High volume |
| ElevenLabs | $99-$330 | Growth to Scale plan |
| Twilio | $100-$500 | 10-50 numbers, high volume |
| Stripe | 2.9% of revenue | ~$300-$1,500 at $10K-$50K MRR |
| ConvertKit | $29-$49 | 1K-5K subscribers |
| Contractor | $1,500-$3,000 | Part-time support/docs |
| **Total** | **$2,428-$6,779/mo** | |

**Healthy margin check**: At $10K MRR (Month 6 target), infrastructure + contractor costs should be $1,500-$3,000/mo, yielding 70-85% gross margin. At $30K MRR (Month 12 target), costs of $4,000-$7,000/mo yield 77-87% gross margin.

---

## 10.8 Cost Optimization Levers

When margins need protection, apply in this order:

| Priority | Lever | Savings | Effort |
|----------|-------|---------|--------|
| 1 | Switch to Deepgram Voice Agent ($4.50/hr all-in) for high-volume | 10-20% on voice costs | 8 hrs migration |
| 2 | Cache frequent RAG queries (Redis L1/L2) | 30-50% on LLM costs | Already built |
| 3 | Batch TTS generation for common phrases | 15-25% on ElevenLabs | 4 hrs |
| 4 | Move from Railway to Hetzner VPS | 60-70% on compute | 20 hrs migration |
| 5 | Negotiate annual contracts with Deepgram/ElevenLabs | 10-30% volume discount | 2 hrs (email) |
| 6 | Switch LLM from Haiku to Gemini Flash for voice | 40-60% on LLM costs | 4 hrs (test quality) |

---

*This spec (Sections 6 through 10) is structured for agent teams to execute from. Each section provides concrete numbers, decision criteria, and implementation details sufficient to begin work without additional clarification. Revenue multipliers (Section 6) layer on top of core SaaS and course revenue. The parallel launch sequence (Section 7) maximizes time-to-revenue. The risk register (Section 8) provides trigger-based escalation paths. GTM requirements (Section 9) define what must be shipped alongside each product. External pricing (Section 10) establishes the cost floor for all pricing decisions. Combine with Sections 1-5 for the complete execution plan.*