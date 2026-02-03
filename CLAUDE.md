# EnterpriseHub: Real Estate AI & BI Platform

## Project Identity
**Domain**: Rancho Cucamonga real estate market with AI-powered lead qualification, chatbot orchestration, and Business Intelligence dashboards.

**Core Mission**: Transform real estate operations through intelligent automation while maintaining human oversight and compliance.

---

## Architecture Overview

### Tech Stack
- **API Layer**: FastAPI with async/await patterns
- **UI Layer**: Streamlit for BI dashboards, React components for embedded widgets
- **Database**: PostgreSQL with Alembic migrations
- **AI Stack**: Claude (primary), Gemini (analysis), Perplexity (market data)
- **Integrations**: GoHighLevel CRM, Stripe payments, MLS data feeds
- **Infrastructure**: Docker Compose, nginx reverse proxy
- **Caching**: Redis (L1), Application (L2), Database (L3)

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
- **Nurture**: Long-term relationship building for future transactions

### Rancho Cucamonga Market
- **Price Ranges**: Entry-level $500-700k, Mid-market $700k-1.2M, Luxury $1.2M+
- **Key Areas**: Victoria, Haven, Etiwanda, Terra Vista, Central Park
- **Market Dynamics**: Family-oriented growth, proximity to LA employment, steady appreciation
- **Buyer Personas**: Growing families, LA commuters, first-time buyers, retirees

### Compliance Requirements
- **DRE**: California Department of Real Estate regulations
- **Fair Housing**: Non-discriminatory practices in all communications
- **CCPA**: California Consumer Privacy Act compliance for lead data
- **CAN-SPAM**: Email marketing compliance

---

## Jorge Bot Family

### Jorge Lead Bot
- **Personality**: Professional, knowledgeable, slightly conversational
- **Primary Goal**: Qualify leads efficiently while building rapport
- **Key Metrics**: Lead score 1-10, qualification time <5 minutes
- **Intelligence**: Conversation analysis, churn prediction, preference learning

### Jorge Buyer Bot
- **Personality**: Consultative, market-savvy, client-focused
- **Primary Goal**: Match properties to buyer preferences and budget
- **Key Capabilities**: Property search, market analysis, showing coordination
- **Intelligence**: Behavioral matching, market education optimization

### Jorge Seller Bot
- **Personality**: Professional advisor, market expert, results-oriented
- **Primary Goal**: Provide accurate pricing and marketing strategy
- **Key Capabilities**: CMA generation, pricing recommendations, marketing insights
- **Intelligence**: Confrontational qualification, objection handling

---

## Development Patterns

### Code Organization
```
advanced_rag_system/          # Core RAG infrastructure
├── src/
│   ├── core/                # Configuration, exceptions
│   ├── embeddings/          # Vector embeddings, caching
│   └── vector_store/        # Chroma vector database

ghl_real_estate_ai/          # Main application
├── agents/                  # Bot personalities and behaviors
├── api/                     # FastAPI routes and middleware
├── models/                  # SQLAlchemy models, Pydantic schemas
├── services/                # Business logic, integrations
├── utils/                   # Shared utilities
└── streamlit_demo/          # BI dashboard components
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

## Critical Services

### Claude Orchestration (`services/claude_orchestrator.py`)
- **Multi-strategy response parsing**: 5 extraction methods
- **Intelligence coordination**: Parallel service integration
- **Caching layers**: L1/L2/L3 with circuit breakers
- **Performance**: <200ms intelligence overhead

### Agent Mesh Coordinator (`services/agent_mesh_coordinator.py`)
- **Enterprise governance**: Cost limits, performance monitoring
- **Intelligent routing**: Multi-criteria agent selection
- **Auto-scaling**: Queue time triggers, load balancing
- **Security**: User quotas, audit trails

### Enhanced GHL Client (`services/enhanced_ghl_client.py`)
- **Rate limiting**: 10 requests/second with backoff
- **Lead synchronization**: Real-time CRM updates
- **Webhook handling**: Event-driven updates
- **Audit trail**: Complete interaction logging

### Business Intelligence
- **Scenario Simulation**: Monte Carlo modeling for strategic decisions
- **Market Sentiment**: Multi-source intelligence with geographic mapping
- **Emergency Deal Rescue**: Real-time churn detection with intervention strategies
- **Intelligence Coordination**: Unified executive briefings

---

## Security & Compliance

### Data Protection
```python
# PII encryption at rest
from cryptography.fernet import Fernet

class LeadDataManager:
    def store_lead_info(self, phone: str, email: str):
        encrypted_phone = self.encrypt_pii(phone)
        encrypted_email = self.encrypt_pii(email)
```

### Authentication & Authorization
- **API Keys**: Environment variables only, never hardcoded
- **JWT Tokens**: Short-lived (1 hour), refresh pattern
- **Rate Limiting**: 100 requests/minute per API key
- **Input Validation**: Pydantic models for all API inputs

---

## Performance Standards

### Response Time Targets
- **API Endpoints**: <200ms average
- **AI Responses**: <500ms for Jorge bots
- **Database Queries**: <50ms for leads, <100ms for properties
- **Intelligence Services**: <200ms parallel execution

### Scalability Benchmarks
- **Concurrent Load**: 4,900+ ops/sec under enterprise load
- **Memory Management**: LRU eviction at 50MB/1000 items
- **Thread Safety**: 100% success rate for concurrent operations
- **Cache Performance**: 90%+ hit rate for conversation data

### Error Handling
- **Circuit Breakers**: Fail fast on external service degradation
- **Graceful Fallbacks**: Neutral defaults when intelligence fails
- **Infrastructure Monitoring**: Structured alerts with severity levels
- **Silent Failure Prevention**: Explicit error propagation

---

## Testing Strategy

### AI/ML Testing
```python
# Intent classification accuracy
def test_buyer_intent_classification():
    test_cases = [
        ("I want to buy a 3BR house", "buyer_intent"),
        ("What's my home worth?", "seller_intent"),
        ("Just browsing", "information_seeking")
    ]
    # Assert >90% accuracy
```

### Integration Testing
- **GHL API**: Mock responses for CRUD operations
- **Stripe**: Test mode for payment processing
- **MLS Data**: Staging environment with sample listings
- **AI Models**: Fixed responses for deterministic tests

### Performance Testing
- **Load Testing**: 100 concurrent users on qualification flows
- **Memory Testing**: 500+ conversation handling
- **Cache Testing**: LRU eviction under memory pressure
- **Race Condition Testing**: Concurrent file/memory operations

---

## Development Workflow

### Environment Setup
```bash
# Development setup
docker-compose up -d postgres redis
python -m pip install -r requirements.txt
alembic upgrade head

# Run with hot reload
uvicorn app:app --reload --port 8000

# BI dashboard
streamlit run admin_dashboard.py --server.port 8501

# Test suite with coverage
python -m pytest --cov=ghl_real_estate_ai --cov-min=80
```

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Production Deployment
```bash
# Validate environment
python3 validate_environment.py

# Run production tests
python3 production_readiness_checklist.py

# Deploy with monitoring
docker-compose --profile production --profile monitoring up -d
```

---

## Key Performance Indicators

### Business Metrics
- **Lead Conversion**: Inquiry → Qualified → Appointment → Closed
- **Bot Performance**: Response accuracy >90%, escalation rate <15%
- **Revenue Attribution**: Cost per qualified lead, lifetime value
- **Market Intelligence**: 40%+ improvement in prospecting efficiency

### Technical Metrics
- **System Health**: API response times, error rates <5%, uptime >99.9%
- **Cache Performance**: Hit rates, memory utilization, eviction rates
- **Database Performance**: Query times, connection pool utilization
- **AI Performance**: Token usage, response quality, cost optimization

### Alert Thresholds
- **Critical**: >5% API errors, >500ms average response time
- **Warning**: >80% memory utilization, <85% bot accuracy
- **Info**: Cache evictions, rate limit approaches

---

## Critical Files Reference

| File | Purpose | Priority |
|------|---------|----------|
| `app.py` | FastAPI entry point | HIGH |
| `services/claude_orchestrator.py` | AI coordination | HIGH |
| `agents/jorge_*_bot.py` | Bot implementations | HIGH |
| `services/enhanced_ghl_client.py` | CRM integration | MEDIUM |
| `models/` | Data models | MEDIUM |
| `streamlit_demo/` | BI dashboard | MEDIUM |
| `.env` | Environment secrets | CRITICAL |

---

## Quick Reference Commands

```bash
# Development
make dev-setup          # Full development environment
make test-all           # Run complete test suite
make lint-fix           # Fix code style issues

# Database
make db-migrate         # Create and apply migration
make db-reset           # Reset database (development only)

# Deployment
make validate-prod      # Production readiness check
make deploy-staging     # Deploy to staging
make deploy-prod        # Deploy to production

# Monitoring
make logs-api          # API service logs
make logs-bots         # Bot service logs
make metrics           # System metrics dashboard
```

---

**Version**: 5.0 | **Status**: Production Ready | **Last Updated**: February 1, 2026