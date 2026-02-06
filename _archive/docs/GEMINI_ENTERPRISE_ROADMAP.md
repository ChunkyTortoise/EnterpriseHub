# Enterprise-Grade Gemini CLI Enhancement Roadmap

Based on the strategic research report "Enterprise-Grade Gemini CLI Enhancement", this roadmap outlines the steps to upgrade `EnterpriseHub` and the `ghl_real_estate_ai` system to an institutional-grade platform.

## 1. Advanced Context & Memory Architecture
**Goal:** Move from ephemeral/local memory to a unified, persistent, and scalable system.

*   **[TODO] Unified Database Layer:**
    *   Replace `sqlite3` in `InventoryManager` and `chromadb` (local) with **PostgreSQL + pgvector + TimescaleDB**.
    *   **Action:** Deploy `docker-compose.db.yml` with `pgvector/pgvector:pg16`.
    *   **Action:** Refactor `InventoryManager` to use `SQLAlchemy` or `psycopg2` for relational data and `pgvector` for embeddings.
*   **[TODO] Semantic Chunking:**
    *   Implement "Cluster Semantic Chunking" instead of fixed-size splitting for RAG.
    *   **Action:** Create `modules/context_engine.py` using `langchain-text-splitters` with semantic capabilities.
*   **[TODO] Implicit Context Caching:**
    *   Leverage Gemini 3.0's implicit caching by structuring prompts with stable prefixes (Architecture docs, API contracts) to maximize cache hits (4x cost reduction).

## 2. Enterprise Security & Compliance
**Goal:** Achieve "SOC 2 Ready" status and prevent secret leaks.

*   **[TODO] Secrets Detection:**
    *   Integrate `semgrep` into the development workflow.
    *   **Action:** Add `semgrep` to `requirements.txt` and create a pre-commit hook or CI step.
*   **[TODO] Supply Chain Security:**
    *   Scan dependencies for vulnerabilities.
    *   **Action:** Add `safety` or `pip-audit` to CI pipeline.
*   **[TODO] Identity & Access:**
    *   Plan for Okta/SSO integration (Future Phase).

## 3. Workflow Orchestration
**Goal:** Automate complex multi-step development tasks.

*   **[IN PROGRESS] LangGraph Integration:**
    *   Already present in `requirements.txt`.
    *   **Action:** Expand `SwarmOrchestrator` to use `LangGraph` for stateful multi-turn workflows (e.g., "Refactor Service X and update all tests").
*   **[TODO] Event-Driven Architecture:**
    *   Implement event routing for system triggers (e.g., GHL Webhook -> Event Router -> Agent -> Action).

## 4. Immediate Implementation Plan (Next Session)
1.  [COMPLETE] Spin up Postgres/pgvector container (Implemented via Homebrew local service for stability).
2.  [COMPLETE] Install `semgrep` and run a baseline security scan. (Found 2 issues in `auth.py`).
3.  [COMPLETE] Prototype the "Boundary-Weighted" system prompt for the Gemini Agent (`scripts/prototype_prompt.py`).
4.  [COMPLETE] Refactor `InventoryManager` to use the new Postgres database instead of SQLite.
5.  [COMPLETE] Fix the security issues in `auth.py` by moving credentials to `.env` (and suppressing legacy defaults).

## 5. Phase 5: Orchestration & Event Loop [COMPLETE]
*   **Goal:** Implement `LangGraph` to manage complex multi-turn agent workflows (e.g., "Research property -> Draft email -> Update CRM").
*   **[COMPLETE] Action:** Create `modules/orchestrator.py` using `langgraph`.
*   **[COMPLETE] Action:** Define the `State` schema for the agent loop.
    *   *Verification:* Run `scripts/demo_orchestration.py` to see the "Match -> Narrate -> Update CRM" loop in action.
