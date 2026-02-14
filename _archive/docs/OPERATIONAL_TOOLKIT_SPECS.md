# Operational Toolkit Specifications

To power the **Extensive Claude Hooks (V2)**, you need concrete utility scripts that Agents can call as tools. This document specifies the implementation requirements for these "Power Tools".

## 🛠️ Tool 1: `codebase_mapper.py`
**Powers:** The "Pattern Architect" and "Dependency Graph Mapper" hooks.

### Functional Spec
*   **Input:** Root directory path, focus file (optional).
*   **Logic:**
    1.  Uses `ast` (Python) and `grep`/`ripgrep` (Polyglot) to scan imports.
    2.  Constructs a directed graph (NetworkX) of file dependencies.
    3.  Identifies "Hotspots" (files with high Centrality - many dependents).
*   **Output (JSON):**
    ```json
    {
      "files": ["main.py", "utils.py"],
      "relationships": [{"source": "main.py", "target": "utils.py", "type": "import"}],
      "hotspots": ["utils.py"] // High risk of breaking things
    }
    ```
*   **Agent Usage:** "Before I touch `utils.py`, I will run `codebase_mapper` to see what breaks."

---

## 🛠️ Tool 2: `security_auditor_wrapper.py`
**Powers:** The "Security Sentry" hook.

### Functional Spec
*   **Input:** File path or Directory.
*   **Logic:**
    1.  Detects language (Python/JS).
    2.  Runs targeted SAST tools:
        *   Python: `bandit -r [path] -f json`
        *   JS/TS: `npm audit` or `semgrep`
        *   Secrets: `detect-secrets scan`
    3.  Filters out "Info" level noise; keeps "High/Medium" severity.
*   **Output (Markdown):**
    *   **CRITICAL:** Hardcoded API Key in `config.py` (Line 12).
    *   **HIGH:** SQL Injection risk in `db.py` (Line 45).
*   **Agent Usage:** "I have finished writing the code. Now running `security_auditor` before committing."

---

## 🛠️ Tool 3: `market_intel_scraper.py`
**Powers:** The "Market Oracle" hook.

### Functional Spec
*   **Input:** Zip Code or Neighborhood Name (e.g., "Hyde Park, Rancho Cucamonga").
*   **Logic:**
    1.  **Search:** Uses Google Search API (or `browsing` tool) for:
        *   "[Neighborhood] real estate market stats [Current Month]"
        *   "[Neighborhood] school ratings"
    2.  **Extract:** Parses snippet text for key metrics: "Median Price", "Days on Market".
    3.  **Validate:** Cross-references 2 sources (e.g., Redfin vs. Realtor.com snippets).
*   **Output (Text):** "Hyde Park Market Brief: Median $650k (Up 2%), Fast market (14 days). Schools: Lee Elementary (9/10)."
*   **Agent Usage:** "I need to answer a lead's question about price. Running `market_intel_scraper`."

---

## 🛠️ Tool 4: `ghl_workflow_validator.py`
**Powers:** The "GHL Workflow Architect" hook.

### Functional Spec
*   **Input:** YAML/JSON definition of a GoHighLevel workflow.
*   **Logic:**
    1.  **Schema Check:** Validates against GHL API schema (if available) or internal schema definition.
    2.  **Logic Check:** Detects infinite loops (Trigger -> Action -> Same Trigger).
    3.  **Safety Check:** Ensures no "Mass SMS" actions without "Wait" steps (Spam risk).
*   **Output:** "Pass" or "Fail: Potential infinite loop detected in Node A -> Node B."
*   **Agent Usage:** "I designed a workflow. Verifying logic with `ghl_workflow_validator`."

---

## 🛠️ Tool 5: `auto_refactor.py`
**Powers:** The "Tech Debt Collector" hook.

### Functional Spec
*   **Input:** File path, Refactoring Strategy (e.g., "extract_method").
*   **Logic:**
    1.  Uses `bowler` or `rope` (Python refactoring libs).
    2.  Safely applies standard transformations (Rename, Move, Extract).
    3.  Runs local tests immediately after change.
*   **Output:** Diff of changes + Test Result (Pass/Fail).
*   **Agent Usage:** "The function is too complex. I will use `auto_refactor` to extract the logic."
