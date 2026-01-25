# Technical Architecture: EnterpriseHub

## Stack Overview
- **Frontend:** Streamlit (Studio Dark theme, WCAG AAA compliant).
- **Backend:** FastAPI, Python 3.11+.
- **Database:** PostgreSQL (with pgvector for semantic search), Redis (for caching/queues), SQLite (for session persistence).
- **AI/ML:** Gemini (primary), Claude 3.5 (specialized reasoning), LangGraph (agent state management).
- **Data Engineering:** NumPy (vectorization), Pandas, Scikit-learn (lead scoring).

## Key Architectural Patterns
### 1. Swarm Orchestration (The Conductor)
- **Centralized Orchestrator:** Manages 8 specialized agents (Prime, Architect, Engineer, Guardian, DevOps, Strategist, Scribe, Auditor).
- **Telemetry Handoffs:** Uses state/context blocks to prevent context drift between agents.

### 2. Cognitive Ops Architecture
- `User Request → Cognitive Trace → Pattern Recognition → Swarm Execution → Guardian (QA) → Production`.

### 3. Model Context Protocol (MCP)
- Standardized tool integration via MCP servers for `context-compressor` and `prompt-library`.

### 4. Boundary-Weighted Prompting
- Strategic placement of instructions and reference material at the start and end of prompts to maximize attention.

## Security & Reliability
- **Industrial-Grade Testing:** 517+ automated tests (pytest).
- **Static Analysis:** Semgrep and Ruff for secret detection and code quality.
- **Defensive Programming:** Robust retry logic and error handling for external APIs.
