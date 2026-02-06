# Architectural Decisions (ADR)

## ADR 001: Adoption of Gemini CLI Conductor
- **Status:** Accepted (January 25, 2026)
- **Context:** Previous context management was handled by disparate `CONTINUATION_PROMPT.md` files and manual handoffs.
- **Decision:** Use the Gemini CLI Conductor extension to centralize context in markdown files under `.gemini/conductor/`.
- **Consequences:** Improved agent precision, reduced context drift, and standardized handoffs.

## ADR 002: Model Context Protocol (MCP) as Tool Standard
- **Status:** Accepted
- **Context:** Needed a universal way to expose project tools to multiple LLM providers.
- **Decision:** Implement MCP servers for all core utilities (compression, library).
- **Consequences:** Standardized tool-calling interface across Gemini and Claude.

## ADR 003: Gemini 2.0 Flash for Primary Orchestration
- **Status:** Accepted
- **Context:** Need low latency and high reliability for real-time task routing.
- **Decision:** Default to Gemini 2.0 Flash for orchestrator-level decisions, reserving Pro/Sonnet for complex reasoning.
- **Consequences:** Significant cost savings and faster responsiveness.

## ADR 004: Standalone jorge_real_estate_bots Repository
- **Status:** Accepted (February 5, 2026)
- **Context:** Jorge bots (Lead, Buyer, Seller) grew beyond a subdirectory of EnterpriseHub. Needed independent CI, DB layer, and deployment.
- **Decision:** Extract to `ChunkyTortoise/jorge_real_estate_bots` with its own SQLAlchemy models, Alembic migrations, Docker deployment, and test suite.
- **Consequences:** Clean separation of concerns. EnterpriseHub remains the platform; jorge repo is one client deployment. Shared patterns (cache, config, logger) duplicated but independently evolvable.

## ADR 005: Replace Mock Data with Real DB Queries Incrementally
- **Status:** In Progress (February 5, 2026)
- **Context:** Dashboard services used `import random` to simulate lead data. Made metrics non-deterministic and untestable.
- **Decision:** Replace mocks one method at a time with real SQLAlchemy queries against `LeadModel`, using `JorgeBusinessRules` for calculations and deterministic cost maps.
- **Consequences:** 3 methods replaced in Phase 1. 3 more remain (`_fetch_lead_data_for_budget_analysis`, `_fetch_lead_data_for_timeline_analysis`, `_generate_commission_trend_data`). Tests require PostgreSQL.
