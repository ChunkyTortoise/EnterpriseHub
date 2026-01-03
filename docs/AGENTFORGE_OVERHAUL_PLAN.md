# AgentForge: Hero Modules Overhaul Plan
**Status:** Draft | **Target:** Production-Grade v2.0
**Objective:** Exhaustively overhaul the three core "Hero Modules" to industry-leading standards.

---

## 🏗 Phase 1: Core Architecture Upgrade (Foundation)
*Before overhauling specific modules, we must upgrade the shared engine.*

### 1.1 Unified State Management
- **Goal:** Move away from scattered `st.session_state` variables to a typed `AgentState` class.
- **Action:** Create `core/state_manager.py`.
- **Feature:** "Session Persistence" - If the browser refreshes, the chat history and agent memory remain intact (using `shelve` or local SQLite).

### 1.2 Async Tool Registry
- **Goal:** Allow agents to run tools (Search, Calculator, File I/O) without freezing the UI.
- **Action:** Refactor `core/tools.py` to use `asyncio`.
- **Feature:** Real-time "Thinking..." status updates in the UI while tools run in the background.

### 1.3 UI Component Library
- **Goal:** Consistent, professional look across all modules.
- **Action:** Create `modules/ui_components.py`.
- **Components:**
    - `chat_message(role, text, avatar)`: Standardized message bubbles.
    - `citation_card(source, page, confidence)`: For RAG.
    - `agent_status(step, log)`: Collapsible expander showing agent thoughts.

---

## 🔍 Module 1: RAG Assistant (The Knowledge Engine)
*Transition from "Naive RAG" to "Agentic RAG".*

### 2.1 Advanced Retrieval Architecture
- **Current:** Simple Top-K Vector Search.
- **Upgrade:** **Hybrid Search (Ensemble Retriever)**.
    - Combine **BM25** (Keyword Match) + **ChromaDB** (Semantic Match).
    - **Re-ranking:** Implement a cross-encoder (e.g., `ms-marco-MiniLM`) to re-rank the top 20 results for higher accuracy.

### 2.2 "Deep Citation" UI
- **Current:** Just lists filenames.
- **Upgrade:** **Split-Screen PDF Viewer**.
    - Left Column: Chat Interface.
    - Right Column: PDF Viewer (iframe) that automatically scrolls to the cited page when a user clicks a citation.

### 2.3 Query Expansion & Routing
- **Feature:** The system will rewrite vague queries (e.g., "Tell me about the risks") into precise search vectors ("financial risks detailed in 2024 annual report").
- **Routing:** Automatically detect if the question is "General" (LLM memory) or "Specific" (RAG).

**Success Metric:** System correctly answers questions requiring data from page 45 of a 100-page PDF with <2s latency.

---

## 🤖 Module 2: Agent Hub (The Autonomous Workforce)
*Transition from "Hardcoded Script" to "Dynamic Graph".*

### 3.1 LangGraph Integration
- **Current:** Linear execution.
- **Upgrade:** **StateGraph Implementation**.
    - Define nodes: `Planner` -> `Researcher` -> `Reviewer` -> `Publisher`.
    - Cyclic capability: `Reviewer` can send work back to `Researcher` if quality is low.

### 3.2 Real-Time Graph Visualization
- **Feature:** Display a live MermaidJS flowchart in Streamlit.
- **Interaction:** Active node glows green. User can see exactly where the agent is in the process.

### 3.3 Human-in-the-Loop (HITL)
- **Feature:** "Approval Breakpoints".
    - Before the `Publisher` agent sends an email or saves a file, the workflow pauses.
    - User sees a "Approve / Reject / Edit" button in the UI.

**Success Metric:** A swarm successfully researches a topic, drafts a report, receives user feedback, and revises the report in one continuous session.

---

## 📊 Module 3: Smart Analyst (The Data Scientist)
*Transition from "Chat-to-Chart" to "Sandboxed Data Workspace".*

### 4.1 Self-Healing Code Execution
- **Problem:** LLMs often generate Python code with syntax errors.
- **Solution:** **Iterative Executor**.
    - Agent generates code -> System runs it.
    - If Error: System feeds error back to Agent -> Agent fixes code -> Retry (Max 3 attempts).

### 4.2 Interactive Data Grid
- **Current:** Static `st.dataframe`.
- **Upgrade:** **Ag-Grid Integration**.
    - Users can filter, sort, and edit cells in the dataframe directly in the UI before asking the AI to analyze it.

### 4.3 Multi-Step Reporting
- **Feature:** "Generate Full Report".
    - Instead of one chart, the agent generates a PDF with:
        1. Executive Summary (Text)
        2. Key Trends (Bullet points)
        3. 3 Distinct Visualizations (Plotly)
        4. Data Anomalies Table.

**Success Metric:** User uploads a raw CSV, asks "Analyze sales trends," and receives a bug-free, interactive dashboard with 3 charts and a written summary.

---

## 🗓 Implementation Roadmap

### Week 1: Foundation & RAG
- [ ] Refactor `core/llm_client.py` for structured outputs.
- [ ] Implement Hybrid Search in `rag_assistant.py`.
- [ ] Build Split-Screen UI.

### Week 2: Smart Analyst Overhaul
- [ ] Implement "Self-Healing" code runner in `smart_analyst.py`.
- [ ] Add Ag-Grid integration.
- [ ] Create PDF Report generator tool.

### Week 3: Agent Hub & Polish
- [ ] Port Agents to LangGraph in `agent_hub.py`.
- [ ] Build real-time visualizer.
- [ ] Final UI "Glow-up" (CSS, Fonts, Layouts).

---

## 🏁 Immediate Next Step
**Approve this plan to begin Phase 1: Core Architecture Upgrade.**
