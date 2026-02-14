# Prompt for ChatGPT/Claude: Interview Showcase Asset Specification

**Copy this entire prompt into ChatGPT Codex 5.3 (or Claude) to generate a comprehensive spec for building your interview showcase asset.**

---

# Context: Create Interview Showcase Asset Specification

I have two upcoming Upwork interviews for AI/ML engineering roles and need to create a polished showcase asset that demonstrates my capabilities beyond just showing my GitHub portfolio. I want to extract the most impressive parts of my existing work and package them into a standalone demo that will wow the interviewers.

## Background Information

### My Existing Work
I have built a production AI platform called **EnterpriseHub** with the following proven capabilities:

**Architecture**:
- Multi-agent orchestration (3 specialized AI bots: Lead, Buyer, Seller)
- FastAPI backend with async operations
- PostgreSQL with tenant isolation
- Redis 3-tier caching (L1/L2/L3) achieving 88% hit rate
- Claude API integration with multi-strategy response parsing
- Cross-bot handoff service with circular prevention
- Real-time WebSocket connections
- Streamlit BI dashboard

**Proven Metrics**:
- 5,100+ automated tests (all passing, CI green)
- 89% LLM cost reduction via caching
- <200ms orchestration overhead (P99: 0.095ms)
- 88% cache hit rate over 30 days
- Multi-channel support (SMS, WhatsApp, Web)
- Production deployment with Docker Compose

**Repository**: github.com/ChunkyTortoise/EnterpriseHub

### Interview #1: Kialash Persad - Tuesday, Feb 11, 1pm PT
**Project**: Senior AI Agent Systems Engineer (Multilingual, Multi-Channel, Multi-Tenant)

**Key Requirements**:
- Multi-language support (Spanish, Hebrew, French, etc.)
- Multi-channel messaging (SMS, WhatsApp, Email, Web)
- Multi-tenant architecture with strong isolation
- Deterministic tool-calling
- RAG with hard scoping (no cross-tenant data leakage)
- Anti-hallucination guardrails
- Observability and testing

### Interview #2: Chase Ashley - Thursday, Feb 12, 10am PT
**Project**: AI Secretary / Personal Assistant SaaS

**Key Requirements**:
- Gmail/Outlook integration (OAuth 2.0)
- Calendar availability detection and meeting scheduling
- Email drafting with approval workflow
- Task classification and routing (calendar, email, research, reminders)
- User preference learning
- Multi-tenant SaaS architecture
- Data privacy and encryption

## Your Task

Create a **comprehensive technical specification** for building a standalone showcase asset that I can present during these interviews. This showcase should:

1. **Extract and isolate** the most impressive components from EnterpriseHub
2. **Repackage them** into a clean, focused demo that addresses BOTH interview requirements
3. **Be deployable** within 48 hours (by Monday Feb 10, before first interview)
4. **Run locally** via Docker Compose with one command
5. **Have live demo UI** (Streamlit or FastAPI + simple HTML)
6. **Include comprehensive README** with architecture diagrams
7. **Demonstrate production-grade code** with tests, CI, monitoring

## Specification Requirements

Generate a detailed specification document that includes:

### 1. Project Overview
- Project name and tagline
- Elevator pitch (2 sentences)
- Target audience (hiring managers, technical interviewers)
- Value proposition (what makes this impressive)

### 2. Architecture Design
- High-level system architecture (describe components)
- Data flow diagrams (describe how requests flow through system)
- Technology stack with justifications
- Scalability considerations
- Security design

### 3. Core Features (Prioritized)

Define **8-10 core features** that showcase my capabilities, prioritized as:
- **P0 (Must-have)**: Essential for both interviews
- **P1 (Should-have)**: Strong differentiators
- **P2 (Nice-to-have)**: Polish and extras

For each feature, specify:
- Feature name and description
- Why it's impressive (what skill/capability it demonstrates)
- Which interview it targets (Kialash, Chase, or Both)
- Technical implementation approach
- Success metrics/demo script
- Estimated dev time (hours)

Example feature format:
```
**Feature**: Multi-Language Intent Detection
**Priority**: P0
**Targets**: Kialash (primary), Chase (secondary - future expansion)
**Description**: Automatically detects language of incoming message (Spanish, French, Hebrew, English) and routes to appropriate language-aware agent
**Why Impressive**: Demonstrates real-world multi-language support, not just "we'll add it later"
**Implementation**:
  - Use `langdetect` library for fast initial detection
  - Confirm with Claude API classification (more accurate)
  - Route to language-specific prompt templates
  - Cache language preference per user for speed
**Demo Script**:
  - Send message in Spanish: "Hola, ¿cómo estás?"
  - Show detection result: "es" (Spanish)
  - Display agent response in Spanish
  - Show latency: <50ms for detection
**Success Metrics**: 95%+ accuracy on test set, <100ms detection time
**Dev Time**: 4-6 hours
```

### 4. Demo Scenarios

Create **2-3 scripted demo scenarios** that I can walk through during interviews:

**Scenario A**: For Kialash (Multi-language, multi-tenant)
- Step-by-step walkthrough
- What to say at each step
- What the system does
- Expected output/behavior
- Impressive metrics to point out

**Scenario B**: For Chase (AI Secretary task routing)
- Step-by-step walkthrough
- What to say at each step
- What the system does
- Expected output/behavior
- Impressive metrics to point out

**Scenario C**: General (Technical deep-dive)
- Architecture tour
- Code quality highlights
- Testing approach
- Performance benchmarks
- Deployment process

### 5. UI/UX Design

Specify the demo interface:
- Streamlit multi-page app OR FastAPI + HTML (which is better and why?)
- Page structure and navigation
- Key screens to showcase:
  - Landing page (overview of capabilities)
  - Live demo interaction (send messages, see AI responses)
  - Metrics dashboard (cache hit rate, latency, cost savings)
  - Architecture visualization (mermaid diagram or similar)
  - Code quality dashboard (test coverage, CI status)
- Visual design guidelines (keep it professional, not flashy)

### 6. Technical Implementation Plan

Break down implementation into phases:

**Phase 1: Core Infrastructure (X hours)**
- What to build
- Dependencies to install
- Configuration needed

**Phase 2: Feature Development (X hours)**
- Feature-by-feature implementation order
- Critical path items
- Parallel workstreams (what can be done simultaneously)

**Phase 3: Demo Polish (X hours)**
- UI refinements
- Documentation
- Demo data/fixtures
- Practice scripts

**Phase 4: Deployment & Testing (X hours)**
- Docker containerization
- Local deployment testing
- Performance benchmarking
- Demo rehearsal

Provide realistic time estimates with buffer for each phase.

### 7. Code Quality Standards

Specify requirements for:
- **Testing**: What types of tests (unit, integration), coverage target, frameworks
- **Documentation**: README structure, docstrings, architecture docs
- **CI/CD**: GitHub Actions workflow, what checks to run
- **Code style**: Linting (ruff), formatting (black), type hints
- **Security**: Environment variables, secrets management, input validation
- **Performance**: Logging, metrics, benchmarking scripts

### 8. Reusable Components from EnterpriseHub

Identify which existing components to extract and reuse:
- Agent orchestration logic
- Caching layer (Redis L1/L2/L3)
- Multi-strategy response parsing
- WebSocket connection management
- Database models and migrations
- Testing fixtures and utilities

For each component:
- What to extract (file paths)
- What to refactor/simplify
- What to leave behind (unnecessary complexity)
- New abstractions needed

### 9. README Template

Provide a complete README structure with:
- Project title and badges (tests passing, coverage %, license)
- Quick start (one-command Docker Compose)
- Architecture diagram (describe what it should show)
- Features list
- Demo instructions (step-by-step)
- Performance metrics
- Technology stack
- Project structure
- Development guide
- Testing guide
- License

### 10. Success Criteria

Define what "success" looks like:
- Functional requirements (all P0 features working)
- Performance targets (latency, throughput)
- Quality gates (test coverage %, CI passing)
- Demo readiness (can walk through both scenarios smoothly)
- Documentation completeness (README, architecture, code comments)

### 11. Risk Mitigation

Identify potential risks and mitigation strategies:
- **Risk**: Feature scope too large, won't finish in time
  - **Mitigation**: ?
- **Risk**: Docker setup issues on interview day
  - **Mitigation**: ?
- **Risk**: Demo breaks during live presentation
  - **Mitigation**: ?
- (Identify 5-7 key risks)

### 12. Post-Interview Follow-Up Plan

How to leverage this showcase asset after interviews:
- Share GitHub repo link
- Deploy to public URL (Streamlit Cloud, Railway, etc.)
- Create Loom video walkthrough
- Write technical blog post
- Add to portfolio site
- Use for future proposals

## Output Format

Generate the specification as a **structured markdown document** with:
- Clear section headings
- Bulleted lists for easy scanning
- Code examples where appropriate
- Mermaid diagram descriptions (I'll render them later)
- Time estimates for each component
- Priority labels (P0/P1/P2)

The spec should be **comprehensive yet actionable** - detailed enough that I (or another engineer) could implement it in 48 hours, but not so prescriptive that it removes all engineering judgment.

## Constraints

- **Time**: Must be buildable in 48 hours (16-20 hours of dev work)
- **Scope**: Focus on depth over breadth - 3-4 really impressive features beats 10 mediocre ones
- **Dependencies**: Reuse existing EnterpriseHub code where possible, don't rebuild from scratch
- **Deployment**: Must run with `docker-compose up` - no complex setup
- **Maintainability**: Clean code that I can explain and extend later

## Desired Outcome

By the end of this spec, I should:
1. **Know exactly what to build** - Clear feature list and priorities
2. **Have a realistic timeline** - Hour-by-hour implementation plan
3. **Understand the demo narrative** - What story to tell during interviews
4. **Have confidence** - This showcase will differentiate me from other candidates
5. **Be ready to execute** - Start coding immediately after reading spec

---

## Additional Context (Optional - Include if Helpful)

### What Makes a Great Showcase Asset?

Based on successful interview demos, the showcase should:
- **Solve a real problem** (not a toy example)
- **Demonstrate depth** (production-grade, not tutorial-level)
- **Show technical range** (backend, testing, deployment, monitoring)
- **Be immediately impressive** (clear value within 30 seconds)
- **Support live interaction** (not just screenshots or slides)
- **Handle edge cases** (shows thoughtful engineering)
- **Include metrics** (quantify the value - cost savings, latency, accuracy)

### What to Avoid?

- Don't build a "Hello World" with extra steps
- Don't include half-finished features (better to have 3 polished than 7 broken)
- Don't over-engineer (no Kubernetes, no microservices unless necessary)
- Don't duplicate my existing portfolio (this should be NEW or significantly enhanced)
- Don't create vendor lock-in (should work locally, not require cloud services)

### My Engineering Strengths (Highlight These)

- Multi-agent orchestration
- Production-grade testing (5,100+ tests)
- Performance optimization (89% cost reduction)
- Clean architecture (easy to understand and extend)
- Real metrics (not guesses - actual benchmarks)
- Security best practices (encryption, rate limiting, validation)
- Full-stack capability (API, DB, caching, UI, deployment)

---

# Begin Specification Generation

Using all the context above, generate a **comprehensive technical specification** for my interview showcase asset. The spec should be clear, actionable, and designed to maximize my chances of landing both contracts.

Make it impressive. Make it buildable in 48 hours. Make it impossible for them to say no.

**Generate the specification now.**
