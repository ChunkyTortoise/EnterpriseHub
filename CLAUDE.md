# EnterpriseHub: Jorge's Real Estate AI Platform

**Extends**: `@~/.claude/CLAUDE.md` (Universal engineering principles)

## Project Identity

**Project**: EnterpriseHub - Jorge's AI-Powered Real Estate Command Center
**Domain**: Professional real estate platform with AI concierge and specialized bots
**Stack**: Python 3.11+ Backend + Next.js Frontend, FastAPI, Redis, PostgreSQL
**Scale**: Production-ready bot ecosystem, 650+ tests, Enterprise-grade ML pipeline

## Project Status: ELITE TRANSITION PHASE 1 COMPLETE 🚀
- **Backend**: Production-ready FastAPI + ML Analytics (Sub-50ms scoring).
- **Frontend**: Transitioning from Streamlit to Elite Next.js Platform.
- **Current Aesthetic**: Obsidian / Dark-first (#0f0f0f) with Glassmorphism and Animated Beams.

## Technology Stack (Elite)
- **Framework**: Next.js 15+, React 19, TypeScript
- **Styling**: Tailwind CSS 4, Shadcn/UI, Aceternity UI
- **Animations**: Framer Motion
- **Visuals**: React Three Fiber (3D), Deck.gl (Spatial)
- **State**: Zustand + React Query


## 🎯 **CURRENT DEVELOPMENT STATUS**

**Phase**: ✅ **COMPLETE** - Next.js Professional Platform Migration
**Achievement**: Enterprise-grade frontend showcasing bot ecosystem
**Status**: Ready for backend integration and client demonstrations
**Next**: Backend connection, real-time bot coordination, production deployment

---

## 🤖 JORGE'S BOT ECOSYSTEM (Production Ready)

### **Core Bot Architecture**
```python
# Jorge Seller Bot - Confrontational Qualification
JorgeSellerBot:
  - LangGraph 5-node workflow (analyze → detect_stall → strategy → response → followup)
  - FRS/PCS dual-scoring (Financial Readiness + Psychological Commitment)
  - Stall-breaker automation (4 objection types pre-handled)
  - Temperature classification (hot/warm/cold) with tone routing
  - GHL integration with custom field sync

# Lead Bot - Complete Lifecycle Automation
LeadBot:
  - 3-7-30 day sequence automation
  - Retell AI voice integration (Day 7 calls)
  - CMA value injection (Zillow-defense)
  - Post-showing surveys and contract-to-close nurture
  - Multi-touch attribution with behavioral scoring

# ML Analytics Engine - Enterprise Performance
MLEngine:
  - 28-feature behavioral pipeline with SHAP explainability
  - 95% accuracy with 42.3ms response time
  - Jorge's 6% commission automatic calculation
  - Confidence-based Claude escalation (0.85 threshold)
```

### **Bot Quality Assessment: EXCELLENT** ⭐⭐⭐⭐⭐

| Component | Status | Performance |
|-----------|--------|-------------|
| Jorge Seller Bot | ✅ Production Ready | LangGraph orchestration, confrontational methodology |
| Lead Bot Lifecycle | ✅ Production Ready | Complete 3-7-30 automation with voice integration |
| Intent Decoder | ✅ Production Ready | FRS/PCS scoring with 95% accuracy |
| ML Analytics | ✅ Production Ready | 42.3ms response, enterprise-grade validation |
| GHL Integration | ✅ Production Ready | OAuth2, webhook validation, custom fields |
| Test Coverage | ✅ 650+ Tests | 80% coverage with async validation |

### **Jorge-Specific Features**
- **6% Commission System**: Automatic calculation with ML-predicted sale prices
- **4 Core Questions**: Hardcoded from Jorge's proven qualification process
- **Temperature Classification**: Hot (75+), Warm (50-74), Lukewarm (25-49), Cold (<25)
- **Confrontational Tone**: No-BS approach targeting motivated sellers only
- **SMS Compliance**: 160 char max, no emojis, direct professional tone

### **Next Phase: Professional Platform Showcase**
The bots are enterprise-ready. Need professional frontend to present capabilities properly.

---

## Knowledge Reliability & Anti-Hallucination

**Core Principle**: "I don't know" is always better than a confident wrong answer.

**Required Actions When Uncertain**:
1. ✅ READ actual implementation/docs first
2. ✅ EXPRESS uncertainty explicitly
3. ✅ NEVER infer based on naming conventions
4. ✅ REQUEST clarification if files don't exist
5. ✅ CALIBRATE confidence appropriately

**Complete framework**: `@reference/knowledge-reliability-guide.md`

**Response Quality Self-Check**:
- [ ] Have I read actual project files vs. making assumptions?
- [ ] Am I expressing appropriate confidence levels?
- [ ] Should I say "I don't know" instead of guessing?
- [ ] Did I cite specific sources for claims made?

---

## Development Workflow

### Essential Commands

```bash
# Development
python -m streamlit run ghl_real_estate_ai/streamlit_demo/app.py  # Start UI
python app.py                                                       # Start FastAPI
python -m pytest tests/ --cov=ghl_real_estate_ai --cov-report=html # Run tests

# Validation (auto-runs via pre-commit)
ruff check .                    # Lint
ruff format .                   # Format
mypy ghl_real_estate_ai/        # Type check
pytest tests/ -v                # Test

# Docker
docker-compose up -d            # Start Redis, PostgreSQL
```

### Pre-Commit Validation

**Automated via** `.claude/scripts/pre-commit-validation.sh`:
1. ✅ No secrets in staged files
2. ✅ Python syntax validation
3. ✅ Ruff linting
4. ✅ Type checking (mypy)
5. ✅ Tests for corresponding implementation files exist
6. ⚠️ Large files detection (>500KB)
7. ✅ Commit message format

---

## Critical Path Integration Points

### Claude Assistant Integration

**Pattern**: Persistent, context-aware AI intelligence for UI components
**File**: `ghl_real_estate_ai/services/claude_assistant.py`

```python
# Usage in Streamlit components
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

assistant = ClaudeAssistant()
response = await assistant.explain_match_with_claude(
    property_data,
    lead_preferences,
    conversation_history
)
# Returns strategic narrative, not raw stats
```

### Caching Strategy

**Pattern**: Redis-backed with TTL management
**File**: `ghl_real_estate_ai/services/cache_service.py`

```python
from ghl_real_estate_ai.services.cache_service import CacheService

cache = CacheService()
@cache.cached(ttl=3600, key_prefix="lead_score")
async def calculate_lead_score(lead_id: str):
    # Expensive operation cached for 1 hour
    pass
```

### Streamlit Component Patterns

**File**: `ghl_real_estate_ai/streamlit_demo/components/*.py`

**Caching Rules**:
- `@st.cache_data` for data transformations (leads, properties, analytics)
- `@st.cache_resource` for clients (Redis, Anthropic, database connections)
- Session state for user interactions (`st.session_state`)

**Example**:
```python
@st.cache_data(ttl=300)
def load_lead_data(lead_id: str):
    # Cached for 5 minutes
    pass

@st.cache_resource
def get_redis_client():
    # Singleton connection
    return redis.Redis()
```

---

## Project-Specific Skills

**Location**: `.claude/skills/project-specific/`

### GHL Integration Skill
```bash
# Use when integrating with GoHighLevel API
invoke ghl-integration --operation="create-contact"
```
**Provides**: Authentication patterns, error handling, rate limiting, webhook validation

### Streamlit Component Skill
```bash
# Use when creating Streamlit UI components
invoke streamlit-component --name="LeadScoreCard"
```
**Provides**: Component templates, caching strategies, session state, error handling

---

## Context Management

### Forbidden Paths (Security - NEVER Access)

```
.env                          # Actual secrets (GHL, Claude, Redis)
.env.local                   # Local environment secrets
data/analytics/**            # Contains PII/customer data
*.csv (in root)              # May contain real customer data
secrets/**                   # Any secrets directory
```

### Priority Context Files (Load First)

```
🎯 PLATFORM OVERVIEW
1. CLAUDE.md                                              # This file (platform overview)
2. JORGE_REAL_ESTATE_AI_COMPLETE_SUMMARY.md               # Complete system documentation

🤖 PRODUCTION BOT ECOSYSTEM
3. ghl_real_estate_ai/agents/jorge_seller_bot.py          # LangGraph confrontational bot
4. ghl_real_estate_ai/agents/lead_bot.py                  # 3-7-30 lifecycle automation
5. ghl_real_estate_ai/agents/intent_decoder.py            # FRS/PCS scoring engine
6. bots/shared/ml_analytics_engine.py                     # 28-feature ML pipeline

🏗️ CORE BACKEND SERVICES
7. ghl_real_estate_ai/services/claude_assistant.py        # Core AI conversation intelligence
8. ghl_real_estate_ai/services/claude_conversation_intelligence.py # Real-time analysis
9. ghl_real_estate_ai/services/ghl_service.py             # GHL integration
10. ghl_real_estate_ai/ghl_utils/jorge_config.py          # Jorge configuration system

🎨 CURRENT UI (Streamlit - To Be Replaced)
11. ghl_real_estate_ai/streamlit_demo/components/jorge_command_center.py
12. ghl_real_estate_ai/streamlit_demo/components/lead_dashboard.py

⚙️ CONFIGURATION
13. .claude/settings.json                                 # Project config
```

### Allowed Paths (Full Access)

```
ghl_real_estate_ai/**/*.py          # All Python source
tests/**/*.py                       # All test files
ghl_real_estate_ai/streamlit_demo/components/*.py  # UI components
*.md                                # Documentation
.claude/**                          # Configuration
requirements*.txt                   # Dependencies
```

### Excluded from Context (Performance)

```
**/__pycache__/**           # Python bytecode
**/.pytest_cache/**         # Test cache
**/*.csv                    # Data files (use .env.example for schema)
data/analytics/**           # Analytics data
.git/**                     # Git internals
```

---

## MCP Server Profiles

**Three specialized profiles** (`.claude/mcp-profiles/`):

### 1. streamlit-dev
- **Focus**: Streamlit UI components and frontend
- **Tools**: Playwright (E2E testing), Serena (code navigation)
- **Allowed Paths**: `ghl_real_estate_ai/streamlit_demo/**`
- **Skills**: frontend-design, web-artifacts-builder, theme-factory

### 2. backend-services
- **Focus**: Python services, API integration, business logic
- **Tools**: Serena, Context7, Greptile (code intelligence)
- **Allowed Paths**: `ghl_real_estate_ai/services/**`, `ghl_real_estate_ai/api/**`
- **Skills**: test-driven-development, defense-in-depth

### 3. testing-qa
- **Focus**: Testing, quality assurance, coverage analysis
- **Tools**: Playwright, Serena, Greptile (test management)
- **Allowed Paths**: `tests/**`, all source for reading
- **Skills**: testing-anti-patterns, condition-based-waiting

**Switching**: Set `CLAUDE_PROFILE` environment variable

---

## Domain-Specific Patterns

### AI Integration Patterns

**Deep Reasoning**: Methods like `explain_match_with_claude` should provide strategic/psychological narrative, not just raw stats.

**Pattern**:
```python
# ❌ BAD: Just return property stats
def explain_match(property, lead):
    return f"Price: {property.price}, Beds: {property.beds}"

# ✅ GOOD: Strategic narrative with psychological insights
async def explain_match_with_claude(property, lead, history):
    prompt = f"""
    Explain why this property matches this lead's needs.
    Consider: {lead.preferences}, past interactions, buying signals.
    Provide strategic narrative, not raw stats.
    """
    return await claude_client.generate(prompt)
```

### Real-Time Updates Pattern

**Challenge**: Streamlit reruns entire script on interaction
**Solution**: Use session state + selective caching

```python
if 'lead_scores' not in st.session_state:
    st.session_state.lead_scores = {}

# Only recalculate if lead data changed
@st.cache_data(ttl=60)
def calculate_scores(lead_ids_hash):
    # Cached based on lead IDs hash
    pass
```

### Property Alert System (Phase 1 Complete)

**Architecture**: Background scoring pipeline with real-time WebSocket delivery

**Components**:
- `property_alert_engine.py` - Central orchestrator with intelligent de-duplication
- `property_scoring_pipeline.py` - APScheduler-based background scoring (15min intervals)
- `property_alert_dashboard.py` - Specialized UI with detailed property cards
- Enhanced `event_publisher.py` and `notification_system.py` for real-time delivery

**Pattern**:
```python
# Background job processes properties every 15 minutes
async def score_properties_for_alerts():
    properties = await get_new_properties()
    for lead in active_leads:
        matches = await enhanced_matcher.find_matches(properties, lead.preferences)
        for match in matches:
            if match.score >= lead.alert_threshold:
                await alert_engine.create_alert(lead.id, match)

# Real-time delivery via WebSocket events
await event_publisher.publish_property_alert(
    alert_id, lead_id, property_id, match_score, alert_type, property_data
)
```

**Key Features**:
- Intelligent de-duplication prevents duplicate property alerts
- Rate limiting (max alerts per day per lead) prevents notification fatigue
- Multi-channel delivery ready (WebSocket + future email/SMS integration)
- Rich property cards with match reasoning and interactive actions
- Alert preferences per lead with configurable thresholds

---

## Testing Strategy

**Complete testing guide**: `@~/.claude/reference/testing-standards-guide.md`

### Project-Specific Testing

**Coverage Threshold**: 80% (enforced in CI)

**Test Organization**:
```
tests/
├── unit/                           # Fast unit tests (<100ms)
├── integration/                    # Cross-service tests
├── services/                       # Service-specific tests
└── streamlit_demo/                 # UI component tests
```

**Run Tests**:
```bash
# All tests with coverage
pytest tests/ --cov=ghl_real_estate_ai --cov-report=html

# Specific component
pytest tests/services/test_claude_assistant.py -v

# Integration tests only
pytest tests/integration/ -v
```

---

## Security Considerations

**Complete security guide**: `@~/.claude/reference/security-implementation-guide.md`

### Project-Specific Security

**API Keys Management**:
- GHL API keys in `.env` (never committed)
- Claude API key in `.env`
- Redis password in Docker Compose secrets

**Webhook Validation**:
```python
# GHL webhook signature verification
from ghl_real_estate_ai.api.routes.webhooks import verify_ghl_signature

@app.post("/webhooks/ghl")
async def handle_ghl_webhook(request: Request):
    if not verify_ghl_signature(request):
        raise HTTPException(403, "Invalid signature")
    # Process webhook
```

**PII Handling**:
- Lead data encrypted at rest (PostgreSQL)
- Redis cache with TTL expiration
- No PII in logs or error messages

---

## Quick Reference: Common Tasks

### Adding a New Streamlit Component

1. Use `streamlit-component` skill
2. Create file in `ghl_real_estate_ai/streamlit_demo/components/`
3. Add caching decorators (`@st.cache_data`, `@st.cache_resource`)
4. Add session state management
5. Write tests in `tests/streamlit_demo/components/`
6. Run: `pytest tests/streamlit_demo/components/test_new_component.py`

### Adding a New AI Service

1. Use `test-driven-development` skill (RED-GREEN-REFACTOR)
2. Create service in `ghl_real_estate_ai/services/`
3. Add type hints (mypy validation)
4. Integrate with `claude_assistant.py` if using AI
5. Add caching via `cache_service.py`
6. Write tests in `tests/services/`
7. Update `requirements.txt` if new dependencies

### Integrating with GHL API

1. Use `ghl-integration` skill
2. Add endpoint in `ghl_real_estate_ai/api/routes/`
3. Use Pydantic models for validation
4. Add webhook signature verification
5. Handle rate limiting (429 responses)
6. Add integration tests in `tests/integration/`

---

## Summary

You are working on **Jorge's AI Real Estate Platform** - an enterprise-grade system with production-ready backend and frontend migration in progress:

## 🏆 **CURRENT STATE: PRODUCTION BACKEND + MIGRATION NEEDED**

### **✅ WHAT'S WORKING (Keep 100%)**
1. **Jorge Bot Ecosystem**: LangGraph-powered seller qualification + 3-7-30 lead automation
2. **ML Analytics Pipeline**: 95% accuracy, 42.3ms response, 28-feature behavioral analysis
3. **GHL Deep Integration**: OAuth2, webhook validation, custom field sync
4. **Conversation Intelligence**: Real-time intent/emotion analysis (87KB service)
5. **Property Matching**: ML + semantic matching with real-time alerts
6. **Battle-Tested Quality**: 650+ tests, 80% coverage, production validation

### **🚧 NEXT PHASE: PROFESSIONAL FRONTEND MIGRATION**
1. **Replace Streamlit** → Next.js professional platform
2. **Add Claude Concierge**: Omnipresent AI guide with platform awareness
3. **Mobile-First Design**: Professional real estate agent tools
4. **Real-time Coordination**: WebSocket bot orchestration
5. **Client-Ready Polish**: Enterprise UI that builds trust

### **🎯 STRATEGIC DIRECTION**
- **Backend**: Leverage existing excellence (no rebuilding required)
- **Frontend**: Professional presentation layer for enterprise bot capabilities
- **Mobile**: PWA with offline capabilities for field work
- **Integration**: Seamless bot-to-bot handoffs with persistent context

## 🔑 **KEY DEVELOPMENT PRINCIPLES**

**Bot Integration**: Connect to existing production services, don't rebuild
**Professional Polish**: Client-facing interface quality, not prototype
**Mobile Excellence**: Real estate professionals work in the field
**Omnipresent AI**: Claude concierge provides guidance across entire platform

**For universal principles**: Reference `@~/.claude/CLAUDE.md`
**For bot-specific patterns**: Load jorge_seller_bot.py, lead_bot.py, intent_decoder.py
**For complete architecture**: Read JORGE_REAL_ESTATE_AI_COMPLETE_SUMMARY.md

---

**Last Updated**: January 2026 | **Version**: 3.1.0 (Optimized)
**Token Target**: <3,000 tokens (75% reduction from 12,000 tokens)
**Context Efficiency**: Progressive disclosure with on-demand reference loading
