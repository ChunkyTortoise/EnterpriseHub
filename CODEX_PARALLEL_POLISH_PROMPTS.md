# Codex Parallel Polish Prompts

**Created**: February 4, 2026
**Purpose**: 4 independent Codex sessions to polish all portfolio repos simultaneously
**Strategy**: Each prompt is fully self-contained with context, file references, and deliverables

---

## SESSION 1: EnterpriseHub (Flagship Platform Polish)

**Repo**: `/Users/cave/Documents/GitHub/EnterpriseHub`
**Estimated Scope**: README overhaul, dashboard fix, cleanup

### PROMPT:

```
You are polishing the EnterpriseHub repository - a flagship enterprise real estate AI platform. This is the crown jewel of a professional portfolio showcasing AI/ML engineering services.

## CURRENT STATE
- 77K+ lines of production Python code
- 650+ tests, 80%+ coverage
- 95% production ready
- Has a README.md but it needs modernization and tightening
- Has a PROJECT_EVALUATION.md with good metrics
- Dashboard has import errors blocking demos (service class mapping issues)
- ~203 TODOs scattered across 52 files
- Multiple deployment configs (Fly.io, Docker, Railway, Render)
- Recently added: OpenRouter integration, Beads issue tracker, Supermemory service

## KEY FILES TO READ FIRST
1. `README.md` - Current README (needs overhaul)
2. `CLAUDE.md` - Project instructions with full architecture context
3. `PROJECT_EVALUATION.md` - Metrics and status
4. `ghl_real_estate_ai/streamlit_demo/` - Dashboard components (find import errors)
5. `.env.example` - Environment template (ensure it's comprehensive)

## DELIVERABLES (in priority order)

### 1. Fix Dashboard Import Errors
- Read all files in `ghl_real_estate_ai/streamlit_demo/components/`
- Find the service class mapping issues causing import failures
- Fix the imports so the dashboard can render without errors
- Test by checking all import chains resolve correctly

### 2. Overhaul README.md
The current README is emoji-heavy and reads like internal docs. Transform it into a **professional portfolio README** that would impress a CTO or hiring manager.

Structure:
- **Hero section**: Clean badges (Python, FastAPI, Streamlit, PostgreSQL, Redis). One-line description. No emoji spam.
- **What This Is**: 2-3 sentences. Enterprise real estate AI platform with multi-agent orchestration, ML lead scoring, and BI dashboards.
- **Architecture Diagram**: ASCII art showing the service architecture (Jorge Bots → FastAPI → PostgreSQL, Streamlit Dashboard, GHL Integration)
- **Key Capabilities** (bullet list, no emoji):
  - Multi-agent bot orchestration (Lead/Buyer/Seller qualification)
  - ML lead scoring with SHAP explainability (85%+ accuracy)
  - Real-time BI dashboard with 5 intelligence hubs
  - Advanced RAG pipeline (0.7ms retrieval, 214x faster than target)
  - Multi-LLM orchestration (Claude, Gemini, OpenRouter)
  - GoHighLevel CRM integration with webhook handling
  - 4,900+ ops/sec enterprise cache performance
- **Performance Highlights**: Table with Target vs Achieved metrics
- **Tech Stack**: Clean grid/table
- **Quick Start**: Docker-first, then manual setup
- **Project Structure**: Clean tree showing main directories only
- **Testing**: How to run, coverage stats
- **License**: MIT

Remove:
- Phase completion history (move to CHANGELOG.md if needed)
- Internal development notes
- Excessive emoji usage
- Links to internal docs that won't work publicly

### 3. Clean Up .env.example
- Read the current `.env.example`
- Ensure every environment variable used in the codebase is listed
- Add comments explaining each variable
- Group by service (Database, Redis, AI Providers, GHL, etc.)

### 4. Add .gitignore Cleanup
- Ensure venv/, .env, __pycache__/, *.pyc, .venv_backup_3.14/, debug_venv/ are all in .gitignore
- Ensure no secrets or large binaries would be committed

### 5. Create CHANGELOG.md
- Move all the phase completion history from README.md into a clean CHANGELOG.md
- Format using Keep a Changelog convention
- This preserves the development history without cluttering the README

## CONSTRAINTS
- Do NOT modify any business logic or service code
- Do NOT add new features
- Do NOT delete any existing functionality
- Focus only on presentation, documentation, and the dashboard import fix
- Keep the README under 300 lines
- Use professional tone, no emoji in README (badges are fine)
```

---

## SESSION 2: Revenue-Sprint (Product Launch Polish)

**Repo**: `/Users/cave/Documents/GitHub/Revenue-Sprint`
**Estimated Scope**: Root README, product packaging, launch readiness

### PROMPT:

```
You are polishing the Revenue-Sprint repository - a 7-day sprint that built a freelancer revenue engine with AI-powered Upwork proposal generation, 3 Gumroad digital products, and LinkedIn outreach automation.

## CURRENT STATE
- 14.5K lines of Python code
- 212 tests passing
- 4-agent Upwork proposal pipeline (Prospecting, Credential Sync, Proposal Architect, Engagement)
- 3 packaged Gumroad products in /dist/:
  - Product 1: Prompt Injection Testing Suite ($99) - 60+ detection patterns, MITRE ATLAS mapping
  - Product 2: RAG Cost Optimization Toolkit ($149) - Token analysis, model routing, caching opportunities
  - Product 3: Multi-Agent Orchestration Starter Kit ($199) - DAG execution, retry logic, Pydantic I/O
- LinkedIn outreach engine with 12 connection requests, 18 DM templates, 9 follow-up sequences
- Upwork job scanner with RSS parsing, scoring rubric, SQLite persistence
- Has component READMEs but NO root README.md

## KEY FILES TO READ FIRST
1. All README.md files (portfolio-rag-core/, scanner/, product_1_launch_kit/, product_2_launch_kit/, product_3_launch_kit/, linkedin_engine/)
2. `portfolio-rag-core/src/agents/` - All 4 agent implementations
3. `scanner/upwork_scanner.py` - Job scanner implementation
4. `verify.py` - Component verification script
5. `run_pipeline.py` - End-to-end pipeline
6. `setup.sh` - Setup automation
7. Any files in `dist/` to understand packaging

## DELIVERABLES (in priority order)

### 1. Create Root README.md
This is the most important deliverable. Create a professional portfolio README that showcases this as a complete revenue system.

Structure:
- **Hero section**: Clean title "Revenue Sprint" with subtitle "AI-Powered Freelancer Revenue Engine". Badges for Python, Claude API, pytest.
- **What This Is**: Built in 7 days using parallel AI agent development. Automates Upwork prospecting, generates tailored proposals, packages expertise into digital products, orchestrates LinkedIn outreach. 14.5K lines, 212 tests.
- **Architecture Diagram**: ASCII art showing the full system:
  ```
  RSS Feeds → Job Scanner → Scoring Engine → Proposal Pipeline → Tracking
                                                    ↓
                                            4-Agent System:
                                            1. Prospecting Agent
                                            2. Credential Sync
                                            3. Proposal Architect
                                            4. Engagement Agent

  Digital Products:              LinkedIn Engine:
  1. Prompt Injection ($99)      1. Prospect Scorer
  2. RAG Cost Optimizer ($149)   2. Template Engine
  3. Agent Orchestrator ($199)   3. Batch Generator
  ```
- **Products**: Brief card for each of the 3 products with key features and target audience
- **Pipeline**: How the 4-agent system works
- **Scanner**: Job scoring rubric explained
- **LinkedIn Engine**: Outreach automation overview
- **Quick Start**: setup.sh → verify.py → run_pipeline.py
- **Testing**: 212 tests, how to run
- **Project Structure**: Clean directory tree
- **Development Approach**: Brief note about parallel Codex agent development methodology

### 2. Polish Component READMEs
- Review each existing README (portfolio-rag-core, scanner, linkedin_engine, product_1/2/3)
- Ensure consistent formatting across all
- Add "Quick Start" section to each if missing
- Remove any TODO or placeholder text

### 3. Add Professional .gitignore
- Ensure venv/, __pycache__/, *.pyc, .env, dist/ contents are properly handled
- The dist/ ZIPs should be in .gitignore (they're build artifacts)

### 4. Clean Up Any Stale Files
- Check for any temp files, .pyc files tracked in git, or unnecessary artifacts
- Ensure the repo is clean for public viewing

## CONSTRAINTS
- Do NOT modify any business logic or agent code
- Do NOT add new features
- Keep root README under 250 lines
- Professional tone, minimal emoji (badges are fine)
- This should look like a senior engineer's portfolio piece
```

---

## SESSION 3: jorge_real_estate_bots (MVP Showcase Polish)

**Repo**: `/Users/cave/Documents/GitHub/jorge_real_estate_bots`
**Estimated Scope**: README enhancement, documentation cleanup, showcase positioning

### PROMPT:

```
You are polishing the jorge_real_estate_bots repository - a focused single-agent real estate AI MVP that was extracted and refined from a larger enterprise platform (EnterpriseHub). Built in 17 hours with 231 tests and 92% coverage.

## CURRENT STATE
- 9.4K lines of Python code (extracted from 618K-line enterprise platform)
- 231 tests passing, 92% average coverage
- 3 specialized bots: Lead Bot, Seller Bot, Buyer Bot (Buyer Bot is placeholder only)
- Streamlit Command Center dashboard
- 3 completed development phases
- Has a README.md but it uses emoji heavily and needs professional polish
- 38 markdown documentation files
- Docker-ready but not deployed

## KEY FILES TO READ FIRST
1. `README.md` - Current README
2. `SPECIFICATION.md` or `BUILD_SUMMARY.md` - Build details
3. `shared/` - Shared utilities and caching
4. `lead_bot/`, `seller_bot/`, `buyer_bot/` - Bot implementations
5. `command_center/` - Dashboard
6. `tests/` - Test suite
7. Any PHASE*_COMPLETION*.md files

## DELIVERABLES (in priority order)

### 1. Overhaul README.md
Transform into a professional portfolio README.

Structure:
- **Hero section**: "Jorge Real Estate AI" with subtitle "Single-Agent MVP - Production Patterns from Enterprise Platform". Badges for Python, FastAPI, Streamlit, pytest.
- **The Story**: 2-3 sentences. Extracted 9.4K lines from a 618K-line enterprise platform, keeping production-grade patterns while removing 98.5% of complexity. Built in a single intensive session. 231 tests, 92% coverage.
- **Architecture**: ASCII diagram showing 3 bots + command center + shared services
- **Key Metrics** (table):
  - Lead analysis: 489ms (target <500ms)
  - Cache hit: 0.19ms (target <100ms)
  - Pattern scoring: 0.08ms (1,250x faster than target)
  - Test execution: 6.75s for 110+ tests
- **Bot Capabilities**:
  - Lead Bot: Semantic analysis, 5-minute response rule, automated nurturing
  - Seller Bot: Q1-Q4 confrontational qualification, CMA automation
  - Buyer Bot: Property matching (architecture ready, implementation pending)
- **Tech Stack**: FastAPI, Streamlit, Claude AI, PostgreSQL, Redis, GoHighLevel
- **Quick Start**: pip install → configure .env → python launcher
- **Testing**: How to run, coverage stats
- **Relationship to EnterpriseHub**: Brief note explaining this is a focused extraction
- **License**: MIT

### 2. Clean Up Documentation
- Review all 38 markdown files
- Remove any that are redundant or outdated
- Ensure phase completion docs are in a `/docs` directory (not root)
- Keep root clean: README.md, LICENSE, requirements.txt, .env.example, docker-compose.yml

### 3. Add/Update .env.example
- Ensure all environment variables are documented
- Group by service with comments

### 4. Ensure .gitignore is Comprehensive
- venv/, __pycache__/, .env, *.pyc, .pytest_cache/

## CONSTRAINTS
- Do NOT implement the Buyer Bot (it's intentionally a placeholder)
- Do NOT modify business logic
- Do NOT add features
- Keep README under 200 lines
- Professional tone, no emoji in README body
- Position this as "code extraction and refinement expertise" in portfolio context
```

---

## SESSION 4: ai-orchestrator → AgentForge (Transform or Archive)

**Repo**: `/Users/cave/Documents/GitHub/ai-orchestrator`
**Estimated Scope**: Either polish into showcase piece or prepare for archival

### PROMPT:

```
You are evaluating and polishing the ai-orchestrator repository. This is currently a ~120-line prototype for multi-provider LLM orchestration (Gemini, Perplexity, Claude). It needs to either become a polished portfolio piece or be cleanly archived.

## CURRENT STATE
- 2 Python files: client.py (83 lines), subagent.py (38 lines)
- Async multi-provider LLM client using httpx
- No README, no tests, no git history, no requirements.txt
- Empty utils/ directory
- .env with active credentials (needs to be .gitignored)
- .env.example is empty
- Last modified: January 16, 2026
- Not initialized as git repo

## KEY FILES TO READ
1. `client.py` - Core orchestration class (AIOrchestrator with _gemini, _perplexity, _claude methods)
2. `subagent.py` - CLI interface with argparse

## YOUR TASK: Transform into "AgentForge" - a polished showcase

### 1. Initialize Git Repository
```bash
cd /Users/cave/Documents/GitHub/ai-orchestrator
git init
```

### 2. Add requirements.txt
```
httpx>=0.27.0
python-dotenv>=1.0.0
```

### 3. Enhance client.py (keep it under 200 lines)
Add to the existing code (don't rewrite from scratch):
- Proper error handling for API failures (network, auth, rate limits)
- Retry logic with exponential backoff (3 attempts)
- Configurable temperature and max_tokens
- Basic structured logging
- Docstrings on all methods
- Type hints (already partially there)

### 4. Add Basic Tests (test_client.py)
Write 10-15 unit tests:
- Test provider routing (gemini, perplexity, claude)
- Test invalid provider handling
- Test AIResponse dataclass
- Test error handling (mock failed API calls)
- Test retry logic
- Use unittest.mock to avoid real API calls

### 5. Create Professional README.md
Structure:
- **Title**: "AgentForge" with subtitle "Lightweight Async Multi-Provider LLM Orchestrator"
- **What This Is**: 2 sentences. Unified async interface for Gemini, Perplexity, and Claude APIs. Provider-agnostic with automatic retry and structured responses.
- **Features**: Provider abstraction, async-first, retry logic, structured responses, CLI interface
- **Quick Start**: Install, configure .env, use CLI or import
- **Usage Examples**:
  ```python
  from client import AIOrchestrator
  orc = AIOrchestrator()
  response = await orc.chat("gemini", "Explain RAG in 2 sentences")
  ```
- **CLI Usage**: Show subagent.py commands
- **Supported Providers**: Table with provider, model, and features
- **Architecture**: Brief description of the routing pattern

### 6. Populate .env.example
```
# Google Gemini
GEMINI_API_KEY=your_key_here

# Perplexity AI
PERPLEXITY_API_KEY=your_key_here

# Anthropic Claude
ANTHROPIC_API_KEY=your_key_here
```

### 7. Add .gitignore
```
.env
__pycache__/
*.pyc
venv/
.pytest_cache/
```

### 8. Initial Commit
```bash
git add -A
git commit -m "feat: initialize AgentForge - async multi-provider LLM orchestrator

Transforms prototype into polished portfolio piece with:
- Retry logic with exponential backoff
- Comprehensive error handling
- 15 unit tests
- Professional README
- CLI interface"
```

## CONSTRAINTS
- Keep total codebase under 500 lines (excluding tests)
- This should be a LIGHTWEIGHT showcase, not a framework
- Don't add unnecessary complexity
- Professional tone in all documentation
- The value proposition: "I can build clean, async, multi-provider AI interfaces"
```

---

## EXECUTION INSTRUCTIONS

1. Open 4 separate Codex sessions
2. Paste one prompt per session
3. All 4 can run simultaneously - no dependencies between them
4. After all complete, do a final review pass across all repos for consistency

### Post-Completion Checklist
- [ ] All 4 repos have professional READMEs
- [ ] No emoji spam in any README
- [ ] Consistent badge styling across repos
- [ ] All .env.example files are comprehensive
- [ ] All .gitignore files are proper
- [ ] EnterpriseHub dashboard imports fixed
- [ ] Revenue-Sprint has root README
- [ ] ai-orchestrator has git init + tests
- [ ] No secrets committed anywhere
