# Deep Research: Extensive Claude Hooks Registry (V2)

This registry expands on the initial set with advanced **Agentic Design Patterns** (Reflexion, Hierarchical Supervision) and verified **Real Estate AI** capabilities. It is designed to be a "knowledge injection" for your Auto-Claude system.

---

## 🧠 Part 1: Advanced Agentic Patterns
*Meta-cognitive strategies for autonomous self-improvement.*

### 26. The "Reflexion Looper"
*   **Trigger:** "Solve this problem using a Reflexion loop."
*   **Role:** Self-Correcting Solver.
*   **Protocol:** Implements the **Reflexion Pattern** (Shinn et al.):
    1.  **Draft:** Generates an initial solution.
    2.  **Critique:** Critiques its own solution for specific flaws (correctness, efficiency, style).
    3.  **Memory:** Checks persistent memory for past failures in similar tasks.
    4.  **Refine:** Rewrites the solution based on the critique.
    5.  **Loop:** Repeats until critique passes or max retries reached.
*   **Value:** Solves hard problems where one-shot prompting fails.

### 27. The "Hierarchical Supervisor"
*   **Trigger:** "Orchestrate a multi-agent team to build [Feature]."
*   **Role:** Project Manager / Orchestrator.
*   **Protocol:** Acts as a router that does **not** do the work itself.
    1.  Decomposes the user request into subtasks.
    2.  Delegates to specialized sub-agents (e.g., *Coder*, *Researcher*, *Tester*).
    3.  Aggregates their outputs.
    4.  Intervenes if agents get stuck or loop.
*   **Value:** Handles complex, multi-file features without context overflow.

### 28. The "Socratic Maieutic"
*   **Trigger:** "Help me clarify my requirements using Socratic questioning."
*   **Role:** Requirements Analyst.
*   **Protocol:** Instead of answering, it asks probing questions to force the user (or another agent) to resolve ambiguities.
    *   "You asked for a 'fast' database. Do you mean low-latency reads or high-throughput writes?"
*   **Value:** Prevents "garbage in, garbage out" specs.

---

## 🏗️ Part 2: Codebase Intelligence (Enhanced)
*Specific tools and deeper analysis.*

### 1. The "Pattern Architect" (Refined)
*   **Trigger:** "Audit codebase for [Pattern] usage."
*   **Tooling:** `ast` (Python), `ts-morph` (TypeScript).
*   **Protocol:** Parses the Abstract Syntax Tree (AST) to find structural matches for patterns (e.g., Singleton, Factory) rather than just regex text search.

### 2. The "Legacy Archaeologist"
*   **Trigger:** "Explain the history of [Module]."
*   **Tooling:** `git log -L`, `git blame`.
*   **Protocol:** Correlates code changes with commit messages and PR descriptions to explain *why* code looks the way it does.

### 3. The "Dependency Graph Mapper"
*   **Trigger:** "Map impact of changing [Component]."
*   **Tooling:** `pydeps` (Python), `madge` (JS/TS).
*   **Protocol:** Generates a visual or text-based graph of upstream/downstream dependencies to predict regression risks.

### 4. The "Tech Debt Collector"
*   **Trigger:** "Report tech debt in [Directory]."
*   **Tooling:** `radon` (Python complexity), `sonarqube` (general).
*   **Protocol:** Scans for:
    *   Cyclomatic Complexity > 10.
    *   `TODO` / `FIXME` comments > 3 months old.
    *   Duplicated code blocks (CPD).

---

## 🛡️ Part 3: Quality & Security (Hardened)

### 5. The "Edge Case Generator"
*   **Trigger:** "Generate property-based tests for [Function]."
*   **Tooling:** `hypothesis` (Python), `fast-check` (JS).
*   **Protocol:** Generates generative tests that fuzzy-match inputs (e.g., "what if `age` is -1 or 1,000,000?") to find crashes.

### 6. The "Security Sentry"
*   **Trigger:** "Audit [File] for vulnerabilities."
*   **Tooling:** `bandit` (Python), `semgrep` (General).
*   **Protocol:** Static Application Security Testing (SAST) for:
    *   Hardcoded secrets (API keys).
    *   SQL Injection (`f-string` SQL queries).
    *   Unsafe deserialization (`pickle`).

---

## 🏘️ Part 4: Real Estate AI Specialists
*Domain-specific agents for GHL Lead Intelligence.*

### 9. The "Lead Persona Simulator" (Enhanced)
*   **Trigger:** "Simulate a [Persona] lead to test qualification logic."
*   **Personas:**
    *   *The Tire Kicker:* Vague answers, low budget, "just looking".
    *   *The Relocator:* High urgency, needs schools/commute info, cash buyer.
    *   *The Skeptic:* Questions data sources, mentions "market crash".
*   **Protocol:** Interactive chat session where the Agent plays the user to stress-test the bot.

### 29. The "Market Oracle"
*   **Trigger:** "Synthesize market intelligence for [Zip Code]."
*   **Protocol:**
    1.  **Ingest:** Scrapes active listings (Redfin/Zillow data via API/Search).
    2.  **Analyze:** Calculates DOM (Days on Market), Absorption Rate, and List-to-Sale ratio.
    3.  **Synthesize:** "Hyde Park is a Seller's Market (1.2 months supply). Expect multiple offers."

### 30. The "Sentiment & Intent Decoder"
*   **Trigger:** "Analyze this conversation for hidden intent."
*   **Protocol:** Uses NLP to classify:
    *   **Urgency:** High/Medium/Low (Keywords: "ASAP", "Lease ends").
    *   **Motivation:** Pain (Divorce/Job) vs. Pleasure (Upgrade/Pool).
    *   **Objection Type:** Price, Timing, Trust, Authority.

### 31. The "GHL Workflow Architect"
*   **Trigger:** "Design a GoHighLevel workflow for [Scenario]."
*   **Protocol:** outputs a structured YAML/JSON representing a GHL automation:
    *   **Trigger:** "Form Submitted: Home Value Request".
    *   **Condition:** "Value > $500k".
    *   **Action 1:** SMS "Thanks [Name], checking comps...".
    *   **Action 2:** Add Tag "High Value Seller".

---

## 🚀 Part 5: DevOps & Engineering

### 16. The "Docker Optimizer"
*   **Trigger:** "Optimize Dockerfile."
*   **Tooling:** `hadolint`, `dive`.
*   **Protocol:** Checks for:
    *   Pinning base image versions (`python:3.11-slim` vs `python:latest`).
    *   Merging `RUN` commands to reduce layers.
    *   Removing cache (`rm -rf /var/lib/apt/lists/*`) to save space.

### 17. The "Config Guardian"
*   **Trigger:** "Audit config safety."
*   **Tooling:** `dotenv-linter`.
*   **Protocol:** Ensures no secrets in `git`, all env vars in `.env.example`, and consistent naming (`DB_HOST` vs `DATABASE_HOST`).

### 32. The "CI/CD Pipeline Doctor"
*   **Trigger:** "Debug this GitHub Actions failure."
*   **Protocol:** Analyzes CI logs to distinguish between:
    *   **Flaky Tests:** Random failures.
    *   **Env Issues:** Missing dependencies/credentials.
    *   **Logic Errors:** Actual code bugs.

---

## 🧠 Part 6: Advanced Reasoning (Meta)

### 33. The "First Principles Thinker"
*   **Trigger:** "Deconstruct this architecture."
*   **Protocol:** "Why do we need [Component X]? What problem does it solve? Can we solve it with [Simpler Tool Y]?" (e.g., "Do we need Redis, or is in-memory caching enough?").

### 34. The "Prompt Engineer"
*   **Trigger:** "Optimize this system prompt."
*   **Protocol:**
    *   **Compression:** Removes fluff words.
    *   **Structure:** Adds Markdown headers/bullets.
    *   **Few-Shot:** Adds concrete examples of Input -> Output.
    *   **CoT:** Adds "Think step-by-step" instructions.

### 35. The "Pre-Mortem Analyst"
*   **Trigger:** "Conduct a pre-mortem on this feature plan."
*   **Protocol:** "Assume it is 6 months from now and this feature failed. Why? (e.g., Scalability? User confusion? API costs?)."
