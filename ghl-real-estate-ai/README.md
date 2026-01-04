# GHL Real Estate AI

Conversational AI for real estate lead qualification on GoHighLevel (GHL). Built with Claude Sonnet 4.5 for human-like conversations.

## Features

- **Intelligent Lead Qualification**: Budget, location, timeline, must-haves extraction
- **Context-Aware Memory**: Persistent conversation history scoped by GHL Location
- **GHL CRM Synchronization**: Updates actual GHL Custom Fields (Lead Score, Budget, etc.)
- **Agent Notifications**: Automatically triggers GHL workflows for "Hot Leads"
- **Multi-Tenancy Support**: Charge each real estate team on their own account using dynamic API keys
- **Objection Handling**: Trained on top agent scripts
- **Seamless Handoff**: Auto-tags hot leads and notifies agents
- **Multi-Source Knowledge**: Property listings, FAQ, market data, agent scripts

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Anthropic API key
- GHL trial account (API key and Location ID)

### 1. Clone & Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Multi-Tenancy Onboarding

To add a new real estate team (tenant):

```bash
python scripts/register_tenant.py \
  --location_id LOC123 \
  --anthropic_key sk-ant-... \
  --ghl_key ghl-...
```

This ensures that team's conversations use their own API credits and their data is isolated.

### 3. Configure Environment

```bash
cp .env.example .env
```

**Required variables (Default Account):**
- `ANTHROPIC_API_KEY`: Primary fallback key
- `GHL_API_KEY`: Primary fallback key
- `GHL_LOCATION_ID`: Primary location ID

### 3. Initialize Database

```bash
# Start PostgreSQL (if not running)
# On Mac with Homebrew:
brew services start postgresql@15

# Create database
createdb real_estate_ai

# Run migrations (once you have alembic set up)
alembic upgrade head
```

### 4. Load & Manage Knowledge Base

```bash
# Load FAQ and property listings into vector database
python scripts/load_knowledge_base.py

# Audit or manage your knowledge base (Audit listings, FAQ, etc.)
python scripts/kb_manager.py list
```

### 5. Verify Setup Before Deployment

Run this command to ensure all API keys and databases are working correctly:

```bash
python scripts/verify_setup.py
```

### 6. Run Development Server

```bash
# Start FastAPI server
uvicorn api.main:app --reload --port 8000

# Server will be available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 6. Test with ngrok

```bash
# In a new terminal, expose local server
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
# Add to GHL webhook: https://abc123.ngrok.io/api/ghl/webhook
```

### 7. Configure GHL Webhook

1. Go to GHL Settings > Integrations > Webhooks
2. Add webhook URL: `https://your-ngrok-url.ngrok.io/api/ghl/webhook`
3. Select event: `InboundMessage`
4. Save

### 8. Test End-to-End

Send a text to your GHL phone number:
```
"Hi, I'm looking for a 3-bedroom house in Austin under $400k"
```

You should receive an AI response within 2-3 seconds!

---

## Project Structure

```
ghl-real-estate-ai/
├── api/                        # FastAPI application
│   ├── main.py                 # App entry point
│   ├── routes/
│   │   ├── webhook.py          # GHL webhook handler
│   │   └── health.py           # Health check
│   ├── schemas/
│   │   ├── ghl.py              # GHL models
│   │   └── conversation.py     # Conversation state
│   └── middleware/
│       └── auth.py             # Webhook verification
│
├── core/                       # Core business logic
│   ├── llm_client.py           # Claude API client
│   ├── rag_engine.py           # Vector search
│   └── conversation_manager.py # Conversation orchestration
│
├── services/                   # External integrations
│   ├── ghl_client.py           # GHL API wrapper
│   ├── lead_scorer.py          # Lead qualification
│   └── property_matcher.py     # Property recommendations
│
├── prompts/                    # AI prompts
│   ├── system_prompts.py       # Base prompts
│   ├── qualification_prompts.py
│   └── objection_handlers.py
│
├── data/                       # Knowledge base
│   ├── knowledge_base/
│   │   ├── property_listings.json
│   │   ├── faq.json
│   │   └── agent_scripts.json
│   └── embeddings/
│       └── chroma_db/          # Vector DB storage
│
├── tests/                      # Tests
│   ├── test_webhook.py
│   ├── test_conversation.py
│   └── test_lead_scoring.py
│
├── ghl_utils/                  # Renamed from utils/ to avoid root conflicts
│   ├── logger.py
│   └── config.py
│
├── requirements.txt
├── .env.example
├── Dockerfile
├── railway.json                # Railway config
└── README.md
```

---

## Deployment (Railway)

### 1. Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### 2. Create Railway Project

```bash
railway init
```

### 3. Add PostgreSQL & Redis

In Railway dashboard:
1. Click "New" > "Database" > "PostgreSQL"
2. Click "New" > "Database" > "Redis"
3. Railway auto-sets `DATABASE_URL` and `REDIS_URL`

### 4. Set Environment Variables

In Railway dashboard, add:
- `ANTHROPIC_API_KEY`
- `GHL_API_KEY`
- `GHL_LOCATION_ID`
- `ENVIRONMENT=production`
- `LOG_LEVEL=info`

### 5. Deploy

```bash
railway up
```

Railway will auto-detect Python and use:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

### 6. Get Deployment URL

```bash
railway domain
# Output: https://your-app.railway.app
```

### 7. Update GHL Webhook

Update GHL webhook URL to:
```
https://your-app.railway.app/api/ghl/webhook
```

---

## Testing

### Run All Tests

```bash
pytest tests/ --cov=. --cov-report=term-missing
```

### Run Specific Test

```bash
pytest tests/test_webhook.py -v
```

### Test Webhook Manually

```bash
curl -X POST http://localhost:8000/api/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "type": "InboundMessage",
    "contactId": "test_123",
    "message": {
      "type": "SMS",
      "body": "Looking for 3bed house in Austin"
    },
    "contact": {
      "firstName": "Test",
      "phone": "+15125551234"
    }
  }'
```

---

## Configuration

### Lead Scoring Thresholds

Edit `.env`:
```bash
HOT_LEAD_THRESHOLD=70   # Score >= 70 triggers agent notification
WARM_LEAD_THRESHOLD=40  # Score 40-69 = warm lead
```

### Rate Limiting

```bash
RATE_LIMIT_PER_CONTACT=100  # Max messages per contact per hour
RATE_LIMIT_GLOBAL=1000      # Max total webhook calls per hour
```

### Agent Details

```bash
DEFAULT_AGENT_NAME="Sarah Johnson"
DEFAULT_AGENT_PHONE="+15125551234"
DEFAULT_AGENT_EMAIL="agent@example.com"
```

---

## Knowledge Base Management

### Add New FAQ

Edit `data/knowledge_base/faq.json`:
```json
{
  "id": "faq_021",
  "category": "financing",
  "question": "What is an escalation clause?",
  "answer": "An escalation clause automatically increases your offer...",
  "keywords": ["escalation", "bidding war", "competitive offer"]
}
```

Then reload:
```bash
python scripts/load_knowledge_base.py --collection faq
```

### Add New Property Listing

Edit `data/knowledge_base/property_listings.json`:
```json
{
  "id": "prop_011",
  "address": {...},
  "price": 450000,
  "bedrooms": 3,
  ...
}
```

Reload:
```bash
python scripts/load_knowledge_base.py --collection listings
```

---

## Monitoring & Debugging

### View Logs

**Local:**
```bash
tail -f logs/app.log
```

**Railway:**
```bash
railway logs
```

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-02T10:00:00Z",
  "services": {
    "claude": "connected",
    "database": "connected",
    "redis": "connected"
  }
}
```

### Check Lead Score

```bash
curl http://localhost:8000/api/internal/lead-score/contact_123
```

---

## Performance Optimization

### Enable Caching

Redis caching for frequently asked questions:
```python
# In conversation_manager.py
@cache(ttl=3600)  # Cache for 1 hour
def get_faq_response(question: str):
    ...
```

### Reduce Claude API Costs

1. **Set max_tokens**: Limit to 300-500 for SMS responses
2. **Cache system prompts**: Use Claude's prompt caching feature
3. **Use cheaper model for simple queries**: Switch to Claude Haiku for FAQ lookups

---

## Troubleshooting

### Issue: Webhook not receiving messages

**Check:**
1. GHL webhook URL is correct and uses HTTPS
2. Webhook is active in GHL settings
3. FastAPI server is running (`railway logs`)
4. Firewall allows inbound traffic

**Test:**
```bash
railway logs --tail
# Send test SMS to GHL number
# You should see log entry immediately
```

### Issue: Claude API errors

**Check:**
1. `ANTHROPIC_API_KEY` is valid
2. API key has credits (check Anthropic dashboard)
3. Rate limits not exceeded (10k RPM for Sonnet 4.5)

**Test:**
```bash
python -c "from core.llm_client import LLMClient; client = LLMClient(); print(client.generate('test'))"
```

### Issue: Slow response times

**Diagnose:**
```bash
# Check latency breakdown
curl http://localhost:8000/api/debug/latency
```

**Common causes:**
- Vector search too slow → Reduce `top_k` from 5 to 3
- Claude API latency → Use `max_tokens=300` instead of 1000
- Database queries → Add indexes on `contact_id`

---

## Roadmap

### Phase 1 (Current)
- [x] Basic conversation engine
- [x] Lead qualification
- [x] GHL webhook integration
- [x] RAG knowledge base

### Phase 2 (Next 2 weeks)
- [ ] Appointment scheduling integration
- [ ] Multi-language support (Spanish)
- [ ] Advanced objection handling
- [ ] Agent dashboard for monitoring leads

### Phase 3 (Future)
- [ ] Voice call integration
- [ ] CRM sync (Salesforce, HubSpot)
- [ ] Automated follow-up sequences
- [ ] A/B testing framework for prompts

---

## Contributing

This is a private project, but if you're working on it:

1. Create feature branch: `git checkout -b feature/your-feature`
2. Write tests for new features
3. Ensure all tests pass: `pytest`
4. Commit with clear message: `git commit -m "feat: add Spanish language support"`
5. Push and create PR

---

## License

Proprietary - All rights reserved.

---

## Support

**For bugs or questions:**
- Email: your-email@example.com
- Slack: #ghl-real-estate-ai (if team workspace)

**For GHL API issues:**
- GHL Support: https://help.gohighlevel.com/

**For Anthropic API issues:**
- Anthropic Support: https://support.anthropic.com/

---

## Cost Estimates (Monthly)

| Service | Free Tier | Paid (if exceeded) |
|---------|-----------|-------------------|
| Railway hosting | 500 hours/month | $5/month after |
| Anthropic API | Pay-per-use | ~$2-5 for 1000 conversations |
| PostgreSQL (Railway) | 1GB free | $5/month for 5GB |
| Redis (Railway) | 100MB free | $5/month for 1GB |
| **Total** | **$0-7/month** | **Scales with usage** |

**For 1000 leads/month:**
- Anthropic: ~$5-10 (depending on conversation length)
- Infrastructure: $5-10
- **Total: $10-20/month**

---

**Last Updated:** January 2, 2025
**Version:** 1.0.0
**Status:** Production-Ready MVP
