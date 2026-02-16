# Voice AI Platform - Quick Start

## TL;DR

```bash
# Install
cd voice-ai-platform
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your API keys

# Migrate database
alembic upgrade head

# Run
uvicorn voice_ai.main:app --reload

# Test
pytest tests/ -v

# Verify
python verify_mvp.py
```

## What This Platform Does

**Real-time voice AI agents** for real estate:
- Answers phone calls via Twilio
- Transcribes speech with Deepgram
- Responds intelligently with Claude
- Speaks back with ElevenLabs
- Syncs to GoHighLevel CRM

## Architecture

```
Phone Call ──▶ Twilio ──▶ WebSocket ──▶ Voice Pipeline
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                Deepgram STT         Claude LLM         ElevenLabs TTS
                    │                    │                    │
                    └────────────────────▼────────────────────┘
                                         │
                                    PostgreSQL + Redis
                                         │
                                    GoHighLevel CRM
```

## API Endpoints (Ready to Use)

```bash
# Health check
curl http://localhost:8000/health

# Initiate outbound call
curl -X POST http://localhost:8000/api/v1/calls/outbound \
  -H "Content-Type: application/json" \
  -d '{"to_number": "+15551234567", "bot_type": "lead"}'

# Get call details
curl http://localhost:8000/api/v1/calls/{call_id}

# List calls
curl http://localhost:8000/api/v1/calls?page=1&size=50
```

## Environment Variables (Required)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/voice_ai

# APIs
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Twilio
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

See `.env.example` for all options.

## Testing

```bash
# All tests (66 total)
pytest tests/ -v

# Just unit tests
pytest tests/unit/ -v

# Just integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=voice_ai --cov-report=html
```

## Database Migrations

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Add new field"

# Rollback one version
alembic downgrade -1

# See current version
alembic current
```

## Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f voice-ai

# Stop all services
docker-compose down
```

## File Structure

```
voice-ai-platform/
├── src/voice_ai/          # Source code
│   ├── api/               # FastAPI routes
│   ├── models/            # Database models
│   ├── pipeline/          # Voice pipeline (STT/LLM/TTS)
│   ├── telephony/         # Twilio integration
│   └── main.py            # App entry point
├── tests/                 # 66 tests
│   ├── unit/              # Component tests
│   └── integration/       # API tests
├── alembic/               # Database migrations
├── .env.example           # Environment template
├── README.md              # Full documentation
├── MVP_STATUS.md          # Detailed status report
└── verify_mvp.py          # Quick verification script
```

## Next Steps

1. **Configure Twilio**: Set webhook to `https://your-domain.com/api/v1/calls/inbound`
2. **Test locally**: Make a test call to verify pipeline
3. **Deploy**: Use Docker Compose or Fly.io
4. **Monitor**: Check logs for errors
5. **Integrate bots**: Wire up EnterpriseHub's jorge bots

## Troubleshooting

**Import errors**: Run `pip install -e .` to install package in development mode

**Database errors**: Ensure PostgreSQL is running and `DATABASE_URL` is correct

**API key errors**: Check that all required keys are set in `.env`

**Test failures**: Some tests require mock external APIs - this is expected

## Support

- Full docs: `README.md`
- Status report: `MVP_STATUS.md`
- Verify installation: `python verify_mvp.py`

---

**Ready to go!** 🚀
