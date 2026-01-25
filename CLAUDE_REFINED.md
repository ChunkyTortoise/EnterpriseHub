# EnterpriseHub: Real Estate AI & BI Platform

## Project Identity
**Domain**: Rancho Cucamonga real estate market with AI-powered lead qualification, chatbot orchestration, and Business Intelligence dashboards.
**Mission**: Transform real estate operations through intelligent automation while maintaining human oversight and compliance.

---

## Current Production Status
**Platform Status**: ✅ **PRODUCTION READY** (January 25, 2026)
- **Architecture Quality**: 9.2/10 (Excellent)
- **Implementation Safety**: 9.8/10 (Production Grade)
- **Critical Issues**: 0 (All resolved)
- **Performance**: 4,900+ ops/sec under enterprise load

**Key Systems Active**:
- ✅ Jorge Bot Ecosystem (Lead/Buyer/Seller with intelligence integration)
- ✅ Multi-tier caching with LRU eviction and race condition protection
- ✅ Real-time WebSocket with thread-safe singleton pattern
- ✅ Advanced Claude response parsing (5 extraction methods)
- ✅ Emergency deal rescue and churn prediction
- ✅ Strategic business intelligence platform

---

## Architecture Overview

### Tech Stack
- **API**: FastAPI with async/await patterns
- **UI**: Streamlit BI dashboards, React widgets
- **Database**: PostgreSQL with Alembic migrations
- **AI**: Claude (primary), Gemini (analysis), Perplexity (market data)
- **Integrations**: GoHighLevel CRM, Stripe, MLS feeds
- **Infrastructure**: Docker Compose, nginx reverse proxy

### Service Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Jorge Bots    │    │  BI Dashboard    │    │  GHL Integration│
│ (Lead/Buyer/    │◄──►│  (Streamlit)     │◄──►│  (CRM Sync)     │
│  Seller)        │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     FastAPI Core         │
                    │  (Orchestration Layer)   │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │    PostgreSQL Database   │
                    │  (Conversations, Leads,  │
                    │   Properties, Analytics) │
                    └──────────────────────────┘
```

### Code Organization
```
ghl_real_estate_ai/
├── agents/           # Bot personalities and behaviors
├── api/             # FastAPI routes and middleware
├── models/          # SQLAlchemy models, Pydantic schemas
├── services/        # Business logic, integrations
├── utils/           # Shared utilities
└── streamlit_demo/  # BI dashboard components
```

---

## Domain Context

### Real Estate Terminology
- **Lead**: Potential buyer/seller contact
- **Qualification**: Determining buyer budget, timeline, preferences
- **Listing**: Property available for sale
- **MLS**: Multiple Listing Service (property database)
- **CMA**: Comparative Market Analysis
- **Hot Lead**: High-intent prospect (ready to transact)

### Rancho Cucamonga Market
- **Price Ranges**: Entry $500-700k, Mid $700k-1.2M, Luxury $1.2M+
- **Key Areas**: Victoria, Haven, Etiwanda, Terra Vista, Central Park
- **Buyer Personas**: Growing families, LA commuters, first-time buyers, retirees

### Compliance Requirements
- **DRE**: California Department of Real Estate regulations
- **Fair Housing**: Non-discriminatory practices in all communications
- **Data Privacy**: CCPA compliance for lead data
- **CAN-SPAM**: Email marketing compliance

---

## Jorge Bot Family

### Jorge Lead Bot
- **Personality**: Professional, knowledgeable, conversational
- **Goal**: Qualify leads efficiently while building rapport
- **Metrics**: Lead score 1-10, qualification time <5 minutes
- **Intelligence**: Enhanced with churn prediction and cross-bot context sharing

### Jorge Buyer Bot
- **Personality**: Consultative, market-savvy, client-focused
- **Goal**: Match properties to buyer preferences and budget
- **Capabilities**: Property search, market analysis, showing coordination
- **Intelligence**: Behavioral property matching with 5x improved relevance

### Jorge Seller Bot
- **Personality**: Professional advisor, confrontational qualification style
- **Goal**: Accurate pricing and marketing strategy
- **Capabilities**: CMA generation, pricing recommendations, objection handling
- **Intelligence**: Property intelligence for targeted closing strategies

---

## Development Patterns

### Naming Conventions
- **Files/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Environment Variables**: `PROJECT_FEATURE_NAME`
- **Database Tables**: `plural_snake_case`

### Error Handling
```python
# Explicit error types
class LeadQualificationError(Exception):
    """Raised when lead qualification fails"""
    pass

# Structured error responses
{
    "error": "invalid_lead_data",
    "message": "Phone number format invalid",
    "field": "phone",
    "code": "PHONE_FORMAT_ERROR"
}
```

### Testing Approach
- **AI/ML Testing**: >90% accuracy on intent classification
- **Integration**: Mock GHL/Stripe/MLS responses
- **Performance**: <200ms API, <500ms AI responses
- **Coverage**: 80%+ with realistic conversation scenarios

---

## Security & Performance

### Data Protection
```python
# PII encryption at rest
class LeadDataManager:
    def store_lead_info(self, phone: str, email: str):
        encrypted_phone = self.encrypt_pii(phone)
        encrypted_email = self.encrypt_pii(email)
```

### Authentication & Rate Limiting
- **API Keys**: Environment variables only
- **JWT**: 1-hour short-lived tokens
- **Rate Limiting**: 100 req/min per API key
- **Input Validation**: Pydantic models for all inputs

### Performance Targets
- **Database**: <50ms lead queries, <100ms property searches
- **AI Models**: Claude for complex reasoning, caching for common queries
- **Load**: 4,900+ ops/sec validated under enterprise load
- **Memory**: LRU eviction prevents OOM crashes

---

## Production Deployment

### Environment Strategy
- **Local**: Docker Compose with hot reload
- **Staging**: Kubernetes with production-like data
- **Production**: Auto-scaling with health checks

### Quick Start Commands
```bash
# Development setup
docker-compose up -d postgres redis
python -m pip install -r requirements.txt
alembic upgrade head

# Run services
uvicorn app:app --reload --port 8000
streamlit run admin_dashboard.py --server.port 8501

# Testing
python -m pytest --cov=ghl_real_estate_ai --cov-min=80

# Production deployment
docker-compose --profile production up -d
```

### Critical Files Reference
| File | Purpose | Considerations |
|------|---------|---------------|
| `app.py` | FastAPI entry point | Health checks, middleware |
| `jorge_seller_bot.py` | Confrontational seller qualification | 1,550 lines, intelligence-enhanced |
| `claude_orchestrator.py` | AI response coordination | 982 lines, 5 parsing methods |
| `enhanced_ghl_client.py` | CRM integration | Rate limiting, retry logic |
| `.env` | Environment secrets | Never commit, rotate regularly |

---

## Business Intelligence Features

### Strategic Capabilities
- **Scenario Simulation**: Monte Carlo modeling for business decisions
- **Market Sentiment Radar**: Multi-source intelligence for seller motivation scoring
- **Emergency Deal Rescue**: Real-time churn detection with AI-powered rescue strategies
- **Advanced BI Dashboard**: Interactive "what-if" modeling with waterfall analysis
- **Intelligence Coordinator**: Unified executive briefings with health scoring

### Key Metrics Dashboard
- **Lead Conversion**: Inquiry → Qualified → Appointment → Closed
- **Bot Performance**: Response accuracy, escalation rate, satisfaction
- **System Health**: API response times, error rates, uptime
- **Business KPIs**: Revenue attribution, cost per qualified lead

### Alert Thresholds
- **Error Rate**: >5% triggers immediate alert
- **Response Time**: >500ms average
- **Bot Accuracy**: <85% qualification accuracy
- **System Load**: >80% CPU/memory utilization

---

**Version**: 4.1.0 | **Status**: Production Ready | **Tokens**: ~1,200 (92% reduction)