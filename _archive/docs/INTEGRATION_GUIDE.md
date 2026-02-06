# Integration Guide: Auto-Claude Agent System

This guide explains how to activate the newly researched **Agentic Operating System** within your `enterprisehub` project.

## 📋 Prerequisites

1.  **Python 3.11+** installed.
2.  **Graphiti** credentials configured in `.env` (for Memory).
3.  **OpenAI/Anthropic** keys (for LLM execution).

## 🚀 Activation Step 1: Bootstrap the Codebase

We have created a one-click integration script: `integrate_agent_system.py`. This script reads the strategic designs we created and scaffolds the physical Python package.

Run it now:
```bash
python integrate_agent_system.py
```

**What this does:**
*   Creates `ghl_real_estate_ai/agent_system/`
*   Scaffolds the **Hooks Registry** (`hooks/`)
*   Scaffolds the **Power Tools** (`tools/`)
*   Scaffolds the **Memory Brain** (`memory/`)
*   Scaffolds the **Dojo Gym** (`dojo/`)

---

## 🛠️ Activation Step 2: Implementation Roadmap

Once the files are created, they contain `TODO` comments pointing to the detailed Spec Markdown files. Your task (or Auto-Claude's task) is to fill them in.

### Phase A: The "Brain" (Memory & Hooks)
1.  **Memory:** Implement `memory/schema.py` using `AGENT_MEMORY_STRATEGY.md`.
2.  **Hooks:** Flesh out `hooks/real_estate.py` with the "Market Oracle" logic from `EXTENSIVE_CLAUDE_HOOKS_V2.md`.

### Phase B: The "Hands" (Tools)
1.  **Tools:** Implement `tools/market_scraper.py` using `OPERATIONAL_TOOLKIT_SPECS.md`.
2.  **Tools:** Implement `tools/security_auditor.py`.

### Phase C: The "Conscience" (Governance)
1.  **Guardrails:** Implement `governance/guardrails.py` using `AGENT_GOVERNANCE_PROTOCOL.md`.

### Phase D: The "Gym" (Dojo)
1.  **Runner:** Implement `dojo/runner.py` using `CONTINUOUS_IMPROVEMENT_DOJO.md`.

---

## 🤖 Using the Agents

Once implemented, you can instantiate an agent like this:

```python
from ghl_real_estate_ai.agent_system.hooks.registry import HOOKS
from ghl_real_estate_ai.agent_system.memory.manager import MemoryManager

# 1. Initialize Memory
memory = MemoryManager(user_id="lead_123")

# 2. Check Context
context = memory.retrieve_context()

# 3. Invoke a Hook (e.g., if User asks for Market Data)
if "price" in user_query:
    market_oracle = HOOKS["market_oracle"]()
    data = market_oracle.run(zip_code="78751")
```

---

## 📚 Reference Library (The Source of Truth)

All implementation details are strictly defined in these files:

*   **Capabilities:** `EXTENSIVE_CLAUDE_HOOKS_V2.md`
*   **Testing:** `AGENT_EVALUATION_PROTOCOL.md`
*   **Engineering:** `OPERATIONAL_TOOLKIT_SPECS.md`
*   **Prompts:** `MASTER_SYSTEM_PROMPT_TEMPLATE.md`
*   **Memory:** `AGENT_MEMORY_STRATEGY.md`
*   **Safety:** `AGENT_GOVERNANCE_PROTOCOL.md`
*   **Training:** `CONTINUOUS_IMPROVEMENT_DOJO.md`
