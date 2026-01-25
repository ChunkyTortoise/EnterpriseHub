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
