# Voice AI Platform

Real-time voice AI agent platform for real estate, built on Pipecat, Deepgram, ElevenLabs, and Claude.

## Features

- **Real-time voice conversations** via Twilio + WebSocket streaming
- **Multi-bot support**: Lead qualification, Buyer, and Seller bots
- **Enterprise-grade**: Multi-tenant, cost tracking, PII detection, sentiment analysis
- **GHL CRM sync**: Auto-sync contacts, tags, workflows, and appointments
- **BI Dashboard**: Streamlit analytics with call metrics, sentiment, and cost tracking

## Tech Stack

- **Backend**: FastAPI (async) + SQLAlchemy + PostgreSQL + Redis
- **Voice Pipeline**: Pipecat (STT→LLM→TTS orchestration)
- **STT**: Deepgram (real-time speech-to-text)
- **TTS**: ElevenLabs (natural voice synthesis)
- **LLM**: Anthropic Claude Sonnet 4.5 (conversation intelligence)
- **Telephony**: Twilio (inbound/outbound calls + media streams)
- **Billing**: Stripe (usage-based billing)
- **BI**: Streamlit (analytics dashboards)

## Architecture

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Twilio  │───▶│  WebSocket│───▶│ VoicePipe│
│  Media   │◀───│  Handler  │◀───│  line    │
└──────────┘    └──────────┘    └──────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                ┌───▼────┐      ┌────▼────┐      ┌────▼────┐
                │Deepgram│      │  Claude │      │ElevenLabs│
                │  STT   │      │   LLM   │      │   TTS   │
                └────────┘      └─────────┘      └─────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Twilio account (with phone number)
- Deepgram API key
- ElevenLabs API key
- Anthropic API key

### Installation

```bash
# Clone the repository
cd voice-ai-platform

# Install dependencies
pip install -e .
pip install -e ".[dev]"  # For development

# Copy environment template
cp .env.example .env
# Edit .env with your actual API keys and credentials

# Run database migrations
alembic upgrade head

# Start the server
uvicorn voice_ai.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=voice_ai --cov-report=html

# Run specific test file
pytest tests/unit/test_pipeline.py -v

# Run integration tests only
pytest tests/integration/ -v
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current
```

## Configuration

All configuration is via environment variables (see `.env.example`):

### Required Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `DEEPGRAM_API_KEY`: Deepgram STT API key
- `ELEVENLABS_API_KEY`: ElevenLabs TTS API key
- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio auth token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number
- `STRIPE_SECRET_KEY`: Stripe API key (for billing)

### Optional Variables

- `BASE_URL`: Public domain for webhooks (default: `localhost:8000`)
- `DEBUG`: Enable debug mode (default: `false`)
- `LLM_MODEL`: Claude model to use (default: `claude-sonnet-4-5-20250929`)
- `STT_ENDPOINTING_MS`: Endpointing delay for STT (default: `300`)
- `TTS_MODEL`: ElevenLabs model (default: `eleven_flash_v2_5`)

## Deployment

### Docker Compose (Development)

```bash
docker-compose up -d
```

This starts:
- Voice AI Platform (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)

### Production (Fly.io)

```bash
# Login to Fly.io
fly auth login

# Create app
fly apps create voice-ai-platform

# Set secrets
fly secrets set \
  DATABASE_URL=your_db_url \
  DEEPGRAM_API_KEY=your_key \
  ELEVENLABS_API_KEY=your_key \
  ANTHROPIC_API_KEY=your_key \
  TWILIO_ACCOUNT_SID=your_sid \
  TWILIO_AUTH_TOKEN=your_token \
  STRIPE_SECRET_KEY=your_key

# Deploy
fly deploy
```

### Twilio Configuration

1. **Inbound calls**: Set webhook URL in Twilio console:
   ```
   https://your-domain.com/api/v1/calls/inbound
   ```

2. **Status callbacks**: Automatically configured when making outbound calls

3. **WebSocket**: Calls connect to:
   ```
   wss://your-domain.com/api/v1/voice/ws
   ```

## API Endpoints

### Calls

- `POST /api/v1/calls/outbound` - Initiate outbound call
- `POST /api/v1/calls/inbound` - Handle inbound call (Twilio webhook)
- `GET /api/v1/calls/{call_id}` - Get call details
- `GET /api/v1/calls` - List calls (paginated)

### Webhooks

- `POST /api/v1/webhooks/twilio/status` - Twilio status callback

### WebSocket

- `WS /api/v1/voice/ws` - Voice streaming (bidirectional audio)

### Health

- `GET /health` - Health check

## Bot Integration

The platform integrates with EnterpriseHub's Jorge bots:

- **LeadBotAdapter**: Wraps `ghl_real_estate_ai.agents.lead_bot.LeadBotWorkflow`
- **BuyerBotAdapter**: Wraps `ghl_real_estate_ai.agents.jorge_buyer_bot.JorgeBuyerBot`
- **SellerBotAdapter**: Wraps `ghl_real_estate_ai.agents.jorge_seller_bot.JorgeSellerBot`

Each adapter provides:
- System prompt management
- Voice-optimized response formatting
- Handoff signal detection
- GHL CRM synchronization

## Cost Tracking

All calls track costs across 4 dimensions:

- `cost_stt`: Deepgram transcription cost
- `cost_tts`: ElevenLabs synthesis cost
- `cost_llm`: Claude API cost (tokens)
- `cost_telephony`: Twilio per-minute cost

Costs are calculated in real-time and stored in the `calls` table.

## PII Detection & Redaction

Transcripts are scanned for PII (phone, email, SSN, addresses). Detected PII is:

- Logged in `pii_detected` and `pii_types_found` fields
- Redacted in `text_redacted` field of transcripts
- Never stored in plain text for sensitive fields

## Analytics & BI

Streamlit dashboard provides:

- Call volume and duration metrics
- Sentiment analysis trends
- Cost breakdown by component
- Lead scoring distribution
- Appointment conversion rates
- Bot performance comparison

Start the dashboard:

```bash
streamlit run src/voice_ai/dashboard/call_analytics_app.py
```

## Development

### Project Structure

```
voice-ai-platform/
├── src/voice_ai/
│   ├── api/              # FastAPI routes
│   ├── models/           # SQLAlchemy models
│   ├── pipeline/         # Voice pipeline (STT/TTS/LLM)
│   ├── telephony/        # Twilio integration
│   ├── dashboard/        # Streamlit BI dashboards
│   ├── config.py         # Settings management
│   └── main.py           # FastAPI app entry point
├── tests/
│   ├── unit/             # Unit tests
│   └── integration/      # API integration tests
├── alembic/              # Database migrations
├── Dockerfile            # Container image
├── docker-compose.yml    # Local dev environment
└── pyproject.toml        # Dependencies
```

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type checking (if using mypy)
mypy src/voice_ai
```

### Adding a New Bot Persona

1. Create adapter in `src/voice_ai/pipeline/{bot}_adapter.py`
2. Define system prompt and greeting
3. Implement `process_message()` and `extract_handoff_signals()`
4. Register in `voice_pipeline.py`
5. Add tests in `tests/unit/`

## License

Proprietary - All Rights Reserved

## Support

For issues or questions, contact [your-email@example.com]

---

**Version**: 0.1.0 (MVP)
**Last Updated**: February 16, 2026
