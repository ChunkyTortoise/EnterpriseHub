---
extends: ~/.claude/CLAUDE.md
version: 3.1.0
project: EnterpriseHub - GHL Real Estate AI
last_updated: 2026-01-16
---

# EnterpriseHub Project Guide

**Extends universal engineering principles from:**
- `@~/.claude/CLAUDE.md` - Core engineering standards, TDD, agent orchestration, hooks, token management
- `@~/.claude/reference/` - Advanced pattern libraries and implementation guides

**Project-specific guidance below.**

---

## Section 1: Core Operating Principles

### Autonomy Boundaries (Hard Blocks - NEVER Violate)
- 🛑 **NEVER** modify database schemas without explicit approval and migration planning
- 🛑 **NEVER** commit secrets, API keys, or credentials (check `.env`, `.git/config` before every commit)
- 🛑 **NEVER** delete files without explicit confirmation in the same turn
- 🛑 **NEVER** deploy to production without passing full test suite + manual review
- 🛑 **NEVER** modify `.github/workflows/` or CI/CD configs without security review

### Soft Warnings (Escalate for Review)
- ⚠️ **Flag TODO comments older than 30 days** - extract and summarize for review
- ⚠️ **Alert on N+1 queries** - use proper async patterns and caching
- ⚠️ **Warn on hardcoded values** - move to environment or config files
- ⚠️ **Catch overfitting tests** - if test passes but behavior is fragile, refactor

### Hallucination Prevention
**When uncertain about API contracts, source files, or dependencies:**
1. READ the actual implementation/docs file first
2. NEVER infer based on naming conventions alone
3. If file doesn't exist, explicitly tell user and ask for clarification
4. Example: "I need to verify the FastAPI schema before writing endpoints—reading `/ghl_real_estate_ai/api/routes/`..."

---

## Section 2: Project Context

### Architecture Overview
```
EnterpriseHub - GHL Real Estate AI Platform
├── Backend: Python 3.11+ + FastAPI
├── Frontend: Streamlit + Custom Components (26+ components)
├── Database: PostgreSQL + Redis (caching)
├── AI Integration: Claude API (Anthropic SDK) + LangGraph
├── CRM Integration: GoHighLevel API
└── Deployment: Railway (backend) + Streamlit Cloud (frontend)
```

### Technology Stack

| Layer | Tech | Notes |
|-------|------|-------|
| **Language** | Python 3.11+ (actual: 3.14.2) | Type hints required |
| **Package Mgr** | pip + requirements.txt | Lock files always committed |
| **Backend** | FastAPI + Uvicorn | REST API with async support |
| **Frontend** | Streamlit 1.41+ | Custom components with caching |
| **Database** | PostgreSQL 15+, Redis 5+ | No ORM, direct SQL + caching |
| **AI/LLM** | Claude API (Anthropic 0.18.1) | Context-aware AI integration |
| **Testing** | pytest + coverage.py | 80% branch coverage minimum |
| **Linting** | Ruff (formatter + linter) | Pre-commit hooks enforced |
| **Type Checking** | mypy | Strict mode enabled |

### Critical Files & Directories
```
ghl_real_estate_ai/
├── api/                          # FastAPI routes
│   ├── routes/
│   │   ├── claude_chat.py       # Claude conversation API
│   │   └── ...
├── services/                     # Business logic (125+ service files)
│   ├── claude_assistant.py      # Core Claude integration
│   ├── cache_service.py         # Redis caching patterns
│   ├── analytics_service.py     # Analytics and metrics
│   ├── auto_followup_sequences.py
│   ├── claude_conversation_intelligence.py
│   ├── predictive_lead_scorer.py
│   └── ... (120+ more services)
├── streamlit_demo/              # UI layer
│   ├── app.py                   # Main Streamlit app
│   ├── components/              # Reusable UI components (60+ files)
│   │   ├── chat_interface.py
│   │   ├── lead_dashboard.py
│   │   ├── property_matcher_ai.py
│   │   └── ...
│   └── mock_services/           # Mock data for demos
├── core/                        # Core utilities
│   ├── llm_client.py           # Claude API client wrapper
│   └── conversation_manager.py  # Conversation state management
├── tests/                       # pytest tests
│   ├── test_*.py               # Unit and integration tests
│   └── ...
├── ghl_utils/                   # GoHighLevel integration
│   └── config.py
.claude/
├── skills/                      # 31 production skills (Phase 1-5)
│   ├── MANIFEST.yaml           # Skills registry
│   ├── testing/                # 4 testing skills
│   ├── debugging/              # 1 debugging skill
│   ├── core/                   # 2 core workflow skills
│   ├── deployment/             # 2 deployment skills
│   ├── design/                 # 3 design skills
│   ├── orchestration/          # 2 orchestration skills
│   ├── feature-dev/            # 5 feature acceleration skills
│   ├── cost-optimization/      # 1 cost optimization skill
│   ├── automation/             # 3 automation skills
│   ├── analytics/              # 1 ROI tracking skill
│   └── ai-operations/          # 4 AI-enhanced operation skills
├── hooks/                      # Hook infrastructure
│   ├── PreToolUse.md          # Pre-execution validation
│   └── PostToolUse.md         # Post-execution learning
├── mcp-profiles/               # 5 MCP profiles
│   ├── minimal-context.json   # Routine development (default)
│   ├── research.json          # Documentation lookup
│   ├── streamlit-dev.json     # UI development
│   ├── backend-services.json  # Backend/API development
│   └── testing-qa.json        # Testing and QA
├── scripts/                    # Automation scripts
│   └── pre-commit-validation.sh
├── settings.json              # Claude Code configuration
└── reference/                 # Pattern libraries
requirements.txt               # Python dependencies (30+ packages)
docker-compose.yml             # Docker setup (Streamlit + Redis)
app.py                         # Entry point (path setup)
.env.example                   # Environment variable template
CLAUDE.md                      # This file
```

### Repository Etiquette
- **Branch Naming**: `feature/user-auth`, `fix/memory-leak`, `refactor/api-schema`, `docs/onboarding`
- **Merge Strategy**: Rebase on main; squash multi-commit features into atomic commits
- **Commit Format**: `type: brief summary` + optional body explaining *why*
  - Good: `feat: add Claude conversation caching with Redis 15-min TTL`
  - Bad: `fix: bug`, `updates`, `wip`
- **PR Requirements**: Description + test coverage proof + link to issue
- **Auto-Approve**: Read, Grep, Glob only; require approval for Write/Bash operations

---

## Section 3: Universal Workflow Patterns

### Phase 1: EXPLORE → PLAN → CODE → COMMIT

**Complete TDD workflow**: `@~/.claude/reference/tdd-implementation-guide.md`

#### Quick Reference
1. **RED Phase**: Write failing test documenting expected behavior
2. **GREEN Phase**: Minimal code to make test pass
3. **REFACTOR Phase**: Clean up, optimize, extract helpers
4. **COMMIT**: Atomic commit with full test validation

#### Example for EnterpriseHub
```
User Request: "Add rate limiting to Claude API calls"

Your Action:
1. READ relevant files:
   - ghl_real_estate_ai/core/llm_client.py
   - ghl_real_estate_ai/services/cache_service.py
2. GREP for existing rate-limit references
3. ASK clarifying questions: "Per-user or global? Redis-backed?"
4. Use "think" mode for design decisions
```

### Thinking Mode Allocation

**Complete decision framework**: `@~/.claude/reference/thinking-mode-guide.md`

| Complexity | Mode | Use Cases |
|------------|------|-----------|
| **Simple** | Default | Variable rename, log statement, typo fix |
| **Moderate** | `think` | New service, API endpoint, moderate refactor |
| **Complex** | `think hard` | Service architecture, Claude integration patterns |
| **Critical** | `think harder` | Security decisions, data persistence design |
| **Ultra** | `ultrathink` | Multi-agent orchestration, system redesign |

---

## Section 4: Code Standards & Quality

### Python Quick Reference

**Complete language-specific patterns**: `@~/.claude/reference/language-specific-standards.md`

```python
# ✅ GOOD: Async/await, type hints, descriptive names, proper error handling
from typing import Dict, Optional
import httpx

async def fetch_lead_with_history(
    lead_id: str,
    include_conversations: bool = True
) -> Dict[str, Any]:
    """Fetch lead data with conversation history from GHL API.

    Args:
        lead_id: GHL contact/lead UUID
        include_conversations: Whether to fetch conversation history

    Returns:
        Dict containing lead data and optional conversations

    Raises:
        HTTPError: If API request fails
        ValueError: If lead_id is invalid format
    """
    if not lead_id or len(lead_id) < 10:
        raise ValueError(f"Invalid lead_id format: {lead_id}")

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{GHL_API_BASE}/contacts/{lead_id}",
            headers={"Authorization": f"Bearer {GHL_API_KEY}"}
        )
        response.raise_for_status()

        lead_data = response.json()

        if include_conversations:
            conversations = await fetch_conversations(lead_id)
            lead_data["conversations"] = conversations

        return lead_data


# ❌ BAD: No types, unclear naming, no error handling, blocking I/O
def getLead(id):
    r = requests.get(f"{base}/contacts/{id}")
    return r.json()
```

**Conventions**:
- Type hints on all public functions (use `typing` module)
- Docstrings for public functions (Google style)
- Use `Pydantic` models for data validation
- `async/await` for I/O operations (API calls, database)
- Use `httpx` for async HTTP (not `requests`)
- Leverage Redis cache via `cache_service.py` patterns

### Claude AI Integration Patterns

**Core Service**: `ghl_real_estate_ai/services/claude_assistant.py`

```python
# ✅ GOOD: Use ClaudeAssistant for persistent, context-aware interactions
from services.claude_assistant import ClaudeAssistant

assistant = ClaudeAssistant()
response = await assistant.analyze_lead_conversation(
    lead_id="lead_123",
    conversation_history=[...],
    analysis_type="qualification"
)

# ✅ GOOD: Use LLMClient for one-off, stateless requests
from core.llm_client import get_llm_client

client = get_llm_client()
analysis = await client.generate_content(
    prompt="Analyze this property description...",
    max_tokens=1024
)

# ❌ BAD: Direct Anthropic API calls (bypasses caching, monitoring)
import anthropic
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
# Don't do this - use the project's abstraction layers
```

### Formatting & Linting
```bash
# Pre-commit checks (automated via .pre-commit-config.yaml):
ruff check ghl_real_estate_ai/     # Lint and format
mypy ghl_real_estate_ai/           # Type check
pytest tests/ --cov                # Run tests with coverage
```

### Documentation Requirements
- **Docstrings for all public functions**:
  ```python
  def sanitize_input(input_str: str, max_length: int) -> str:
      """Validates and sanitizes user input.

      Args:
          input_str: Raw user string
          max_length: Max allowed length

      Returns:
          Sanitized string

      Raises:
          ValueError: If input exceeds max_length
      """
  ```
- **README.md**: Getting started, environment setup, key design decisions
- **Component docstrings**: All Streamlit components document parameters and usage

---

## Section 5: Testing & Quality Gates

### Coverage Thresholds
- **Lines**: 80% minimum for new code
- **Branches**: 80% minimum (critical for complex logic)
- **Functions**: 90% minimum for public APIs
- **Integration**: Key user journeys covered end-to-end

### Test Organization
```
ghl_real_estate_ai/
├── services/
│   ├── claude_assistant.py
│   └── cache_service.py
tests/
├── test_claude_assistant.py         # Unit tests
├── test_cache_service.py
├── test_dynamic_scoring_integration.py  # Integration tests
└── test_marketplace.py
```

### Mandatory Pre-Commit Checks
```bash
# Step 1: Type check
mypy ghl_real_estate_ai/

# Step 2: Lint and format
ruff check ghl_real_estate_ai/ --fix

# Step 3: Unit tests
pytest tests/ --cov --cov-report=term-missing

# Step 4: Integration tests (optional for quick commits)
pytest tests/test_*_integration.py

# Only commit if ALL pass:
git commit -m "feat: ..."
```

### Test Naming Convention
```python
import pytest
from services.claude_assistant import ClaudeAssistant

class TestClaudeAssistant:
    """Test suite for Claude AI assistant integration."""

    async def test_analyze_lead_conversation_returns_qualification_score(self):
        # Arrange
        assistant = ClaudeAssistant()
        conversation_history = [
            {"role": "user", "content": "I want to buy a house"},
            {"role": "assistant", "content": "What's your budget?"}
        ]

        # Act
        result = await assistant.analyze_lead_conversation(
            lead_id="test_lead",
            conversation_history=conversation_history,
            analysis_type="qualification"
        )

        # Assert
        assert "qualification_score" in result
        assert 0 <= result["qualification_score"] <= 100

    async def test_analyze_lead_conversation_raises_error_on_invalid_lead_id(self):
        # Arrange
        assistant = ClaudeAssistant()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid lead_id"):
            await assistant.analyze_lead_conversation(
                lead_id="",  # Invalid
                conversation_history=[],
                analysis_type="qualification"
            )
```

---

## Section 6: Tool & Environment Setup

### Essential Commands
```bash
# Development
streamlit run ghl_real_estate_ai/streamlit_demo/app.py    # Start Streamlit UI
python app.py                                              # Alternative entry point

# Testing
pytest tests/ --cov                                        # Run tests with coverage
pytest tests/ --cov --cov-report=html                     # HTML coverage report
pytest -k "test_claude" -v                                # Run specific tests

# Validation
mypy ghl_real_estate_ai/                                  # Type checking
ruff check ghl_real_estate_ai/                            # Linting
ruff format ghl_real_estate_ai/                           # Formatting

# Build & Deploy
docker-compose up -d                                       # Start services (Streamlit + Redis)
docker-compose down                                        # Stop services

# Git workflow
git checkout -b feature/new-feature
# ... make changes, commit ...
git push origin feature/new-feature
# (Open PR on GitHub, await CI/CD green, merge via web UI)
```

### Environment Variables (`.env.example`)
```bash
# Claude AI Configuration (Required)
ANTHROPIC_API_KEY=sk-ant-api03-your-claude-api-key-here

# GoHighLevel Integration (Required for CRM)
GHL_API_KEY=your-ghl-api-key-here
LOCATION_ID=your-ghl-location-id-here

# Optional AI Services
GOOGLE_API_KEY=your-google-api-key-here          # Gemini
PERPLEXITY_API_KEY=your-perplexity-api-key-here  # Perplexity

# Application Configuration
STREAMLIT_SERVER_PORT=8501
LOG_LEVEL=INFO
USE_DEMO_DATA=true
DEBUG_MODE=true
DEVELOPMENT_MODE=true
```

---

## Section 7: Skills Strategy & Workflow Automation

### Complete Development Ecosystem (Phase 1-5 COMPLETE)

The EnterpriseHub project includes **31 production-ready skills** located in `.claude/skills/` spanning testing, debugging, design, orchestration, feature acceleration, cost optimization, automation, and AI-enhanced operations.

#### Skills Overview by Phase

**Phase 1: Core Development Workflow (6 skills) - ✅ COMPLETE**
- `test-driven-development` - TDD RED→GREEN→REFACTOR workflow
- `systematic-debugging` - 4-phase root cause analysis
- `verification-before-completion` - Multi-gate quality validation
- `requesting-code-review` - Pre-review preparation
- `vercel-deploy` - Frontend deployment (Streamlit)
- `railway-deploy` - Backend deployment (FastAPI + Python)

**Phase 2: Advanced Testing & Design (8 skills) - ✅ COMPLETE**
- `condition-based-waiting` - Fix race conditions in tests
- `testing-anti-patterns` - Prevent common test pitfalls
- `defense-in-depth` - Multi-layer validation and security
- `frontend-design` - UI/UX consistency for Streamlit
- `web-artifacts-builder` - Interactive component generation
- `theme-factory` - Professional styling and theming
- `subagent-driven-development` - Multi-agent coordination
- `dispatching-parallel-agents` - Concurrent workflow management

**Phase 3: Feature Development Acceleration (5 skills) - ✅ COMPLETE**
- `rapid-feature-prototyping` - Complete feature generation (83% time savings)
- `api-endpoint-generator` - FastAPI endpoint generation (87.5% time savings)
- `service-class-builder` - Service class generation (88.9% time savings)
- `component-library-manager` - Streamlit component generation (83.3% time savings)
- `real-estate-ai-accelerator` - Domain-specific templates (81.25% time savings)

**Phase 4: Cost Optimization & ROI (5 skills) - ✅ COMPLETE**
- `cost-optimization-analyzer` - Infrastructure cost analysis (20-30% cost reduction)
- `workflow-automation-builder` - CI/CD pipeline generation (50-70% time savings)
- `self-service-tooling` - Admin interfaces (80% support overhead reduction)
- `maintenance-automation` - Automated maintenance (80% reduction in manual work)
- `roi-tracking-framework` - ROI measurement (300-500% ROI tracking)

**Phase 5: AI-Enhanced Operations (4 skills) - ✅ COMPLETE**
- `intelligent-lead-insights` - AI-powered lead analysis (>80% prediction accuracy)
- `conversation-optimization` - Real-time conversation coaching (60% better conversion)
- `property-recommendation-engine` - ML-powered matching (40% better satisfaction)
- `automated-market-analysis` - Real-time CMA generation (90% faster analysis)

**Phase 6: Document Automation (Planned)**
- Document generation and automation skills
- Target: Q2 2026

#### Usage Patterns

**Development Workflow:**
- "Implement TDD for this feature" → `test-driven-development` skill
- "Debug this issue systematically" → `systematic-debugging` skill
- "Verify before completion" → `verification-before-completion` skill

**Feature Acceleration:**
- "Generate complete feature from requirements" → `rapid-feature-prototyping` skill
- "Create FastAPI endpoint" → `api-endpoint-generator` skill
- "Build service class" → `service-class-builder` skill
- "Generate Streamlit component" → `component-library-manager` skill
- "Create real estate AI feature" → `real-estate-ai-accelerator` skill

**Quality & Testing:**
- "Fix race conditions in tests" → `condition-based-waiting` skill
- "Prevent flaky tests" → `testing-anti-patterns` skill
- "Add comprehensive validation" → `defense-in-depth` skill

**Design & UI:**
- "Design consistent UI" → `frontend-design` skill
- "Create interactive demo" → `web-artifacts-builder` skill
- "Apply professional theming" → `theme-factory` skill

**AI Operations:**
- "Analyze lead behavior" → `intelligent-lead-insights` skill
- "Optimize conversation" → `conversation-optimization` skill
- "Recommend properties" → `property-recommendation-engine` skill
- "Generate CMA" → `automated-market-analysis` skill

#### Skills Directory Structure
```
.claude/skills/
├── MANIFEST.yaml              # Skills registry (v5.0.0)
├── scripts/
│   └── integration_tests.py   # Cross-skill validation
├── testing/                   # 4 testing skills
├── debugging/                 # 1 debugging skill
├── core/                      # 2 core workflow skills
├── deployment/                # 2 deployment skills
├── design/                    # 3 design skills
├── orchestration/             # 2 orchestration skills
├── feature-dev/               # 5 feature acceleration skills
├── cost-optimization/         # 1 cost optimization skill
├── automation/                # 3 automation skills
├── analytics/                 # 1 ROI tracking skill
└── ai-operations/             # 4 AI-enhanced operation skills
```

### Agent Swarm Coordination

**When to use specialized agents:**
- **Complex Analysis**: Code review, security scanning, performance analysis
- **Parallel Processing**: Independent tasks that can run concurrently
- **Context Isolation**: Tasks that would bloat main conversation context
- **Resource Optimization**: Use appropriate models (Haiku/Sonnet/Opus) per task

**Example for EnterpriseHub:**
- "Review all Claude integration patterns for security" → Deploy security specialist agent
- "Analyze test coverage across 125+ services" → Deploy test analysis agent
- "Optimize Redis caching strategies" → Deploy performance agent

---

## Section 8: Claude Code Configuration & Context Management

### Project Setup

**Location**: `.claude/` directory contains project-specific Claude Code configurations.

#### Settings Configuration (`.claude/settings.json`)

**Active Profile**: `minimal-context` (optimized for routine development)

**Available Profiles:**
1. **minimal-context** - Routine development (saves ~8K tokens, 4% context)
2. **research** - Documentation lookup only (saves ~10K tokens, 5% context)
3. **streamlit-dev** - Full Streamlit/UI development tools
4. **backend-services** - Backend services and API development
5. **testing-qa** - Testing, QA, and coverage analysis

**Switching Profiles:**
```bash
# Update .claude/settings.json active_profile field
# Or use profile-specific commands in your workflow
```

**Permissions Structure:**
- **Allowed Tools**: Read, Write (scoped), Edit, Grep, Glob, Bash (specific commands)
- **MCP Servers**: Serena, Context7, Playwright, Greptile enabled
- **Hooks**: PreToolUse and PostToolUse validation enabled

#### Forbidden Paths (Security - NEVER Access)

```
.env                      # Contains actual secrets
.env.local               # Local environment secrets
.env.production          # Production credentials
secrets/**               # Any secrets directory
**/*.key                 # Private keys
**/*.pem                 # Certificates
data/analytics/**        # Contains PII/customer data
*.csv (in root)          # May contain real customer data
.git/config              # Repository credentials
```

**Why Blocked:**
- Contains sensitive API keys (GHL, Claude, Redis)
- Customer PII and analytics data
- Production credentials
- Certificate private keys

#### Allowed Paths (Full Access)

```
ghl_real_estate_ai/**/*.py          # All Python source (125+ services, 60+ components)
tests/**/*.py                       # All test files
*.md                                # Documentation
.claude/**                          # Configuration
requirements*.txt                   # Dependencies
docker-compose.yml                  # Container setup
```

#### Priority Context Files (Always Load First)

```
1. CLAUDE.md                                              # This file
2. ghl_real_estate_ai/services/claude_assistant.py       # Core Claude integration
3. ghl_real_estate_ai/services/cache_service.py          # Redis caching patterns
4. ghl_real_estate_ai/core/llm_client.py                 # LLM client wrapper
5. .claude/settings.json                                  # Project configuration
```

#### Excluded from Context (Performance)

```
**/__pycache__/**           # Python bytecode
**/.pytest_cache/**         # Test cache
**/node_modules/**          # Node dependencies (if any)
**/*.csv                    # Data files
data/analytics/**           # Analytics data
.git/**                     # Git internals
**/*.pyc                    # Compiled Python
```

### Hook System

**PreToolUse Hook** (`.claude/hooks/PreToolUse.md`):
- Validates security before tool execution
- Blocks secrets in file operations
- Prevents dangerous bash commands
- Enforces file system protection

**PostToolUse Hook** (`.claude/hooks/PostToolUse.md`):
- Validates results after execution
- Captures successful patterns
- Analyzes errors and failures
- Updates project memory

### Development Workflow with Claude Code

#### Starting New Work

```bash
# 1. Understand the task
# 2. Verify active MCP profile (check .claude/settings.json)
# 3. Claude automatically loads CLAUDE.md and priority files
# 4. Use project-specific skills as needed

# 5. Follow TDD workflow
invoke test-driven-development

# 6. Validate with pre-commit checks
./.claude/scripts/pre-commit-validation.sh
```

#### Integration Points

**With Existing Tools:**
- `.pre-commit-config.yaml` - Git commit validation
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Local development (Streamlit + Redis)
- `pytest.ini` - Test configuration

**With Claude Code:**
- PreToolUse validates BEFORE operations
- PostToolUse learns AFTER operations
- Settings.json defines tool permissions
- MCP profiles provide context-specific tools

---

## Section 9: Security & Quality Gates

### Security Standards

**Complete security implementation guide**: `@~/.claude/reference/security-implementation-guide.md`

**Hard Security Principles:**
- 🔒 Input validation at all system boundaries
- 🔒 API keys from environment variables only (never hardcoded)
- 🔒 Rate limiting on Claude API calls (via cache_service.py)
- 🔒 Sanitization of user input before Claude prompts
- 🔒 No customer PII in logs or error messages

### Pre-Deployment Verification Checklist

```markdown
- [ ] All tests pass: `pytest tests/ --cov` shows >80% coverage
- [ ] No secrets in commit history: `git log --all -p | grep -i "api.?key\|password"` returns nothing
- [ ] Type safety: `mypy ghl_real_estate_ai/` reports 0 errors
- [ ] Linting: `ruff check ghl_real_estate_ai/` reports 0 errors
- [ ] Security scan: Pre-commit hooks pass
- [ ] Environment variables documented in `.env.example`
- [ ] Breaking changes noted in commit message
- [ ] Claude API rate limits configured
- [ ] Redis connection tested
```

---

## Summary: Your Enhanced Engineering Operating System

You operate as a **verification-first Python engineer** with:

1. **Explicit guardrails** preventing dangerous actions
2. **TDD discipline** enforcing test-first development with pytest
3. **Progressive disclosure** keeping context lean via reference files
4. **Extended thinking** for complex architectural decisions
5. **31 production skills** (Phases 1-5 complete) for automated workflows
6. **Agent coordination** for optimal task distribution
7. **Security-first approach** with comprehensive validation
8. **Claude AI integration** following project patterns
9. **Streamlit expertise** for 26+ custom components
10. **FastAPI proficiency** for REST API development

**North Star**: Ship boring, tested, documented, secure Python code that survives production while leveraging Claude AI for intelligent automation and real estate domain expertise.

**Technology Focus**: Python + FastAPI + Streamlit + Claude API + Redis + PostgreSQL

**Skills Status**:
- Phase 1 (Core): ✅ 6 skills
- Phase 2 (Advanced): ✅ 8 skills
- Phase 3 (Feature Dev): ✅ 5 skills
- Phase 4 (Cost/ROI): ✅ 5 skills
- Phase 5 (AI Ops): ✅ 4 skills
- Phase 6 (Docs): 📋 Planned
- **Total: 31 production skills**

**For detailed implementation guides**: Reference the comprehensive documentation in `.claude/reference/` files for specific patterns, standards, and procedures inherited from `@~/.claude/CLAUDE.md`.

---

**Last Updated**: 2026-01-16
**Version**: 3.1.0 (Accuracy-Corrected)
**Project**: EnterpriseHub - GHL Real Estate AI Platform
**Tech Stack**: Python 3.11+ | FastAPI | Streamlit | Claude API | Redis | PostgreSQL
**Services**: 125+ business logic services
**Components**: 60+ Streamlit UI components
**Skills**: 31 production-ready automation skills
**Tests**: pytest-based with 80% coverage requirement
