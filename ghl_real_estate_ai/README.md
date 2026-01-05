# GHL Real Estate AI

Conversational AI for real estate lead qualification on GoHighLevel (GHL). Built with Claude Sonnet 4.5 for human-like conversations.

## Features

- **Intelligent Lead Qualification**: Budget, location, timeline, must-haves extraction (Jorge's 3/2/1 scoring).
- **Context-Aware Memory**: Persistent conversation history scoped by GHL Location with "Smart Resume" capability.
- **Voice AI Integration**: Automated speech-to-text and text-to-speech for phone call qualification.
- **Property Matcher**: Real-time listing recommendations based on lead preferences.
- **Team & Lead Management**: Round-robin lead assignment, agent profiles, and performance leaderboards.
- **GHL CRM Synchronization**: Updates actual GHL Custom Fields (Lead Score, Budget, etc.).
- **CRM Integration Foundation**: Ready for sync with Salesforce and HubSpot.
- **Advanced Analytics**: A/B testing, campaign ROI tracking, and conversation pattern analysis.
- **Lead Lifecycle Tracking**: Visual funnel and bottleneck identification.
- **Bulk Operations**: Mass lead import/export and bulk SMS campaigns.
- **Multi-Tenancy Support**: Charge each real estate team on their own account using dynamic API keys.
- **RAG Knowledge Base**: Property listings, FAQ, and agent scripts.

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

### 4. Initialize Database & KB

```bash
# Load FAQ and property listings into vector database
python scripts/load_knowledge_base.py
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
# API docs at http://localhost:8000/docs (if in development)
```

---

## Project Structure

```
ghl-real-estate-ai/
├── api/                        # FastAPI application
│   ├── main.py                 # App entry point
│   ├── routes/
│   │   ├── webhook.py          # GHL webhook handler
│   │   ├── analytics.py        # A/B testing & metrics
│   │   ├── bulk_operations.py  # Mass lead tools
│   │   ├── lead_lifecycle.py   # Journey tracking
│   │   ├── properties.py       # Listing recommendations
│   │   ├── team.py             # Agent management
│   │   ├── crm.py              # External CRM sync
│   │   └── voice.py            # Telephony endpoints
│   └── middleware/
│       ├── auth.py             # Webhook verification
│       └── security.py         # Rate limiting & headers
│
├── core/                       # Core business logic
│   ├── llm_client.py           # Claude API client
│   ├── rag_engine.py           # Vector search
│   └── conversation_manager.py # Conversation orchestration
│
├── services/                   # Business logic services
│   ├── ghl_client.py           # GHL API wrapper
│   ├── lead_scorer.py          # Qualification logic
│   ├── property_matcher.py     # Listing matching
│   ├── team_service.py         # Agent assignment
│   ├── crm_service.py          # Salesforce/HubSpot sync
│   ├── voice_service.py        # STT/TTS processing
│   ├── analytics_engine.py     # Metrics collection
│   ├── lead_lifecycle.py       # Journey management
│   └── tenant_service.py       # Multi-tenancy management
│
├── prompts/                    # AI prompts
│   ├── system_prompts.py       # Base prompts
│   ├── qualification_prompts.py
│   └── reengagement_templates.py
│
├── data/                       # Persistent data
│   ├── knowledge_base/         # Listings, FAQ, Scripts
│   ├── memory/                 # Conversation contexts
│   ├── teams/                  # Agent data
│   ├── crm/                    # Sync configs
│   └── metrics/                # Performance logs
│
├── tests/                      # 300+ Automated tests
│
├── ghl_utils/                  # System utilities
│   ├── logger.py
│   └── config.py
│
└── ...
```

## Documentation

For detailed guides, please refer to the `docs/` directory:

- [Deployment Guide](docs/DEPLOYMENT.md)
- [API Reference](docs/API.md)
- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Security & Hardening](docs/SECURITY.md)
- [Phase 2 Delivery Summary](_archive_v1_20260104/PHASE2_COMPLETION_REPORT.md)

---

## Testing

### Run All Tests

```bash
pytest tests/
```

---

## Roadmap

### Phase 1 (Complete)
- [x] Basic conversation engine
- [x] Lead qualification
- [x] GHL webhook integration
- [x] RAG knowledge base

### Phase 2 (Complete)
- [x] Appointment scheduling integration
- [x] Analytics & Reporting Dashboard
- [x] Bulk Operations
- [x] Lead Lifecycle Management

### Phase 3 (Current)
- [x] Voice AI call integration
- [x] CRM sync (Salesforce, HubSpot) foundation
- [x] Property Matcher service
- [x] Team management & lead assignment

---

**Last Updated:** January 4, 2026
**Version:** 3.0.0
**Status:** Enterprise-Ready platform
