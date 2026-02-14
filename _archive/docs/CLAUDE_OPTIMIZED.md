# EnterpriseHub: Real Estate AI & BI Platform

## Project Identity
**Domain**: Rancho Cucamonga real estate market with AI-powered lead qualification, chatbot orchestration, and Business Intelligence dashboards.

**Core Mission**: Transform real estate operations through intelligent automation while maintaining human oversight and compliance.

**Current Status**: ✅ **PRODUCTION READY** - Enterprise-grade platform with 4,900+ ops/sec performance

---

## Architecture Overview

### Tech Stack
- **API Layer**: FastAPI with async/await patterns
- **UI Layer**: Streamlit for BI dashboards, React components for embedded widgets
- **Database**: PostgreSQL with Alembic migrations
- **AI Stack**: Claude (primary), Gemini (analysis), Perplexity (market data)
- **Integrations**: GoHighLevel CRM, Stripe payments, MLS data feeds
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

---

## Domain Context

### Real Estate Terminology
- **Lead**: Potential buyer/seller contact
- **Qualification**: Determining buyer budget, timeline, preferences
- **Listing**: Property available for sale
- **MLS**: Multiple Listing Service (property database)
- **CMA**: Comparative Market Analysis
- **Hot Lead**: High-intent prospect (ready to transact)

### Rancho Cucamonga Market Specifics
- **Price Ranges**: Entry-level $300-500k, Mid-market $500k-1M, Luxury $1M+
- **Key Areas**: Downtown, West Lake Hills, Cedar Park, Round Rock, Pflugerville
- **Buyer Personas**: Tech professionals, families relocating, investors

### Compliance Requirements
- **TREC**: Texas Real Estate Commission regulations
- **Fair Housing**: Non-discriminatory practices in all communications
- **Data Privacy**: CCPA/GDPR compliance for lead data

---

## Agent Behaviors & Personalities

### Jorge Lead Bot
- **Personality**: Professional, knowledgeable, slightly conversational
- **Primary Goal**: Qualify leads efficiently while building rapport
- **Key Metrics**: Lead score 1-10, qualification time <5 minutes

### Jorge Buyer Bot
- **Personality**: Consultative, market-savvy, client-focused
- **Primary Goal**: Match properties to buyer preferences and budget
- **Key Capabilities**: Property search, market analysis, showing coordination

### Jorge Seller Bot
- **Personality**: Professional advisor, market expert, results-oriented
- **Primary Goal**: Provide accurate pricing and marketing strategy
- **Key Capabilities**: CMA generation, pricing recommendations, marketing insights

---

## Development Patterns

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

### Naming Conventions
- **Files/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Environment Variables**: `PROJECT_FEATURE_NAME`
- **Database Tables**: `plural_snake_case` (e.g., `lead_interactions`)

### Error Handling Patterns
```python
# Good: Explicit error types
class LeadQualificationError(Exception):
    """Raised when lead qualification fails"""
    pass

# Good: Structured error responses
{
    "error": "invalid_lead_data",
    "message": "Phone number format invalid",
    "field": "phone",
    "code": "PHONE_FORMAT_ERROR"
}
```

---

## Testing & Performance Standards

### AI/ML Testing Approach
```python
def test_buyer_intent_classification():
    """Test buyer intent detection accuracy"""
    test_cases = [
        ("I want to buy a 3BR house in Rancho Cucamonga", "buyer_intent"),
        ("What's my home worth?", "seller_intent"),
        ("Just browsing", "information_seeking")
    ]
    # Assert >90% accuracy on classification
```

### Performance Targets
- **API Response**: <200ms for endpoints, <500ms for AI responses
- **Database**: <50ms for lead queries, <100ms for property searches
- **Load Testing**: 100+ concurrent users supported
- **Production Performance**: 4,900+ ops/sec validated

---

## Security & Integration Essentials

### Data Protection
- **PII Encryption**: All sensitive data encrypted at rest
- **API Security**: JWT tokens, rate limiting (100 req/min per key)
- **Input Validation**: Pydantic models for all API inputs

### Key Integrations
- **GoHighLevel (GHL)**: CRM sync with rate limiting (10 req/sec)
- **Stripe**: Payment processing (test mode in non-production)
- **MLS Data**: Daily property listing sync
- **AI Models**: Multi-provider routing (Claude primary, Gemini analysis)

---

## Critical Files Reference

| File | Purpose | Key Considerations |
|------|---------|-------------------|
| `app.py` | FastAPI entry point | Health checks, middleware setup |
| `admin_dashboard.py` | BI interface | Real-time metrics, caching |
| `jorge_bot_command_center.py` | Bot orchestration | Multi-bot coordination |
| `models/lead_scoring.py` | ML scoring logic | Model versioning, A/B testing |
| `services/enhanced_ghl_client.py` | CRM integration | Rate limiting, retry logic |
| `.env` | Environment secrets | Never commit, rotate regularly |

---

## Quick Start Commands

```bash
# Development setup
docker-compose up -d postgres redis
python -m pip install -r requirements.txt
alembic upgrade head

# Run with hot reload
uvicorn app:app --reload --port 8000

# Run BI dashboard
streamlit run admin_dashboard.py --server.port 8501

# Test suite
python -m pytest --cov=ghl_real_estate_ai --cov-min=80

# Production deployment
docker-compose --profile production --profile monitoring up -d
```

---

## Production Features Active

### Enterprise Capabilities ✅
- **Multi-tier Caching**: L1/L2/L3 with circuit breakers
- **Jorge Bot Ecosystem**: Memory-optimized conversation management
- **Real-time WebSocket**: Thread-safe connection pooling
- **Advanced Intelligence**: Multi-strategy response parsing
- **Infrastructure Monitoring**: Comprehensive alerting and health checks

### Business Intelligence ✅
- **Scenario Simulation**: Monte Carlo business modeling
- **Market Sentiment**: Multi-source intelligence radar
- **Deal Rescue**: AI-powered churn prevention
- **Strategic Analytics**: Executive decision support

---

## Related Documentation

- **Phase Status**: `PHASE_STATUS.md` - Historical implementation details
- **Production Readiness**: `PRODUCTION_STATUS.md` - Deployment validation results
- **Architecture Analysis**: `ARCHITECTURE_ANALYSIS.md` - Technical deep-dive documents
- **Performance Metrics**: `PERFORMANCE_BENCHMARKS.md` - Load testing and optimization results

---

**Version**: 4.1.0 | **Last Updated**: January 25, 2026 | **Tokens**: ~1,200 | **Status**: Production Ready