# EnterpriseHub: GHL Real Estate AI Platform

**Extends**: `@~/.claude/CLAUDE.md` (Universal engineering principles)

## Project Identity

**Project**: EnterpriseHub - GoHighLevel Real Estate AI Integration Platform
**Domain**: Real Estate CRM automation with AI-powered lead intelligence
**Stack**: Python 3.11+, Streamlit, FastAPI, Redis, PostgreSQL
**Scale**: 26+ UI components, 650+ tests, Multi-agent AI architecture

---

## Architecture Overview

```
EnterpriseHub/
├── ghl_real_estate_ai/
│   ├── api/                    # FastAPI endpoints for GHL webhooks
│   ├── services/               # 30+ AI services (Claude, caching, analytics)
│   ├── streamlit_demo/         # 26+ production UI components
│   │   └── components/         # Lead dashboards, property matching, analytics
│   ├── core/                   # LLM client, conversation manager
│   └── tests/                  # 650+ tests (pytest, coverage 80%+)
├── .claude/
│   ├── skills/                 # 14 production skills (TDD, debugging, design)
│   ├── settings.json           # MCP profiles, permissions, context management
│   └── hooks/                  # PreToolUse, PostToolUse validation
└── requirements.txt            # Python dependencies
```

**Key Services**:
- `claude_assistant.py` - Core AI conversation intelligence
- `cache_service.py` - Redis-backed caching with TTL management
- `llm_client.py` - Claude API integration with streaming
- `property_matcher.py` - AI-powered property recommendations
- `enhanced_lead_intelligence.py` - Multi-source lead analysis

**Complete architecture**: `.claude/reference/project-architecture.md` (when needed)

---

## Technology Stack

| Layer | Technology | Configuration |
|-------|-----------|---------------|
| **Language** | Python 3.11+ | Type hints required (mypy), Ruff formatting |
| **UI Framework** | Streamlit 1.31+ | Component caching (`@st.cache_data`, `@st.cache_resource`) |
| **API** | FastAPI | Async endpoints, Pydantic models |
| **AI/LLM** | Claude 3.5 Sonnet | Anthropic SDK, streaming responses |
| **Cache** | Redis 7+ | TTL-based invalidation, connection pooling |
| **Database** | PostgreSQL 15+ | Async SQLAlchemy, Alembic migrations |
| **Testing** | pytest + pytest-asyncio | 80% coverage threshold |
| **CRM Integration** | GoHighLevel API | OAuth2, webhook validation |

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
1. CLAUDE.md                                              # This file
2. ghl_real_estate_ai/services/claude_assistant.py       # Core AI service
3. ghl_real_estate_ai/services/cache_service.py          # Caching patterns
4. ghl_real_estate_ai/core/llm_client.py                 # LLM integration
5. .claude/settings.json                                  # Project config
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

You are working on the **EnterpriseHub GHL Real Estate AI Platform**:

1. **Python-first** project with strict typing and testing requirements
2. **Streamlit UI** with 26+ components requiring caching strategy
3. **Claude AI integration** for intelligent lead analysis and property matching
4. **Redis caching** for performance optimization
5. **GoHighLevel CRM** integration with webhook validation
6. **Multi-agent architecture** with specialized AI services
7. **14 production skills** for standardized workflows

**Key Patterns**:
- AI responses: Strategic narratives, not raw stats
- Caching: Redis-backed with TTL management
- Testing: 80% coverage, pytest with async support
- Security: No secrets in code, PII encryption, webhook validation

**For universal principles**: Reference `@~/.claude/CLAUDE.md`
**For detailed patterns**: Load relevant files from `.claude/reference/` on-demand

---

**Last Updated**: January 2026 | **Version**: 3.1.0 (Optimized)
**Token Target**: <3,000 tokens (75% reduction from 12,000 tokens)
**Context Efficiency**: Progressive disclosure with on-demand reference loading
