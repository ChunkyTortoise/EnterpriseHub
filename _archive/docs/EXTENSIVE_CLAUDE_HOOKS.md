# Extensive Claude Integration Hooks Registry

This registry defines **25 High-Value Agentic Hooks** categorized by domain. Each hook represents a specialized "skill" or "persona" that can be integrated into the `auto-claude` or `enterprisehub` system to automate complex cognitive tasks.

## 🏗️ Architecture & Codebase Intelligence

### 1. The "Pattern Architect"
*   **Trigger:** "Audit the codebase for [Design Pattern] usage."
*   **Role:** Senior Architect.
*   **Protocol:** Scans code for architectural patterns (e.g., Repository, Singleton, Observer). Identifies correct usage, deviations, and opportunities to standardize.
*   **Value:** Enforces architectural consistency across the project.

### 2. The "Legacy Archaeologist"
*   **Trigger:** "Explain the history and intent behind [Module/File]."
*   **Role:** Code Historian.
*   **Protocol:** Combines `git log`, `git blame`, and code analysis to reconstruct the decision-making history of a piece of code. useful for understanding "Chesterton's Fence" before refactoring.
*   **Value:** Prevents regression of forgotten edge cases during modernization.

### 3. The "Dependency Graph Mapper"
*   **Trigger:** "Map the downstream impact of changing [Component X]."
*   **Role:** Systems Analyst.
*   **Protocol:** Traces import paths and function calls to generate a list of all files and modules that depend on a target component.
*   **Value:** Reduces "butterfly effect" bugs during refactoring.

### 4. The "Tech Debt Collector"
*   **Trigger:** "Generate a tech debt report for [Directory]."
*   **Role:** Project Maintainer.
*   **Protocol:** Scans for `TODO`, `FIXME`, `HACK` comments, and high-complexity functions (cyclomatic complexity). Aggregates them into a prioritized backlog.
*   **Value:** Makes invisible debt visible and actionable.

---

## 🛡️ Quality Assurance & Security

### 5. The "Edge Case Generator"
*   **Trigger:** "Generate edge case test scenarios for [Function/Feature]."
*   **Role:** QA Engineer.
*   **Protocol:** Analyzes input types and business logic to propose "nasty" inputs: nulls, huge numbers, empty strings, Unicode, race conditions, etc.
*   **Value:** Hardens code against unexpected failures.

### 6. The "Security Sentry"
*   **Trigger:** "Perform a security audit on [File/Endpoint]."
*   **Role:** InfoSec Researcher.
*   **Protocol:** Checks for OWASP Top 10 vulnerabilities: SQL injection points, unescaped output (XSS), hardcoded secrets, and weak authentication checks.
*   **Value:** Proactive vulnerability detection.

### 7. The "Input Validator"
*   **Trigger:** "Verify input sanitization for [API Endpoint]."
*   **Role:** Security Engineer.
*   **Protocol:** Specifically traces user input from entry point to usage, ensuring validation gates exist for every parameter.
*   **Value:** Prevents malformed data from corrupting the database.

### 8. The "Error Handling Auditor"
*   **Trigger:** "Audit error handling in [Module]."
*   **Role:** Reliability Engineer.
*   **Protocol:** Hunts for "swallowed" exceptions (`except: pass`), generic error messages, and unhandled promise rejections.
*   **Value:** Improves system observability and debuggability.

---

## 🏘️ Real Estate Domain (GHL Specific)

### 9. The "Lead Persona Simulator"
*   **Trigger:** "Simulate a [Buyer/Seller] conversation to test the AI."
*   **Role:** Method Actor.
*   **Protocol:** Adopts a specific persona (e.g., "Skeptical First-Time Buyer", "Urgent Seller") and interacts with the Real Estate AI to test its qualification logic and empathy.
*   **Value:** Automated "User Acceptance Testing" for chatbots.

### 10. The "Fair Housing Compliance Officer"
*   **Trigger:** "Audit these prompts for Fair Housing violations."
*   **Role:** Legal Compliance Specialist.
*   **Protocol:** Scans prompt text and bot outputs for discriminatory language or bias related to race, religion, gender, etc.
*   **Value:** Mitigates legal risk in automated communications.

### 11. The "Objection Handler Tuner"
*   **Trigger:** "Optimize the objection handler for [Objection Type]."
*   **Role:** Sales Coach.
*   **Protocol:** Analyzes failed conversations where leads disengaged. Proposes refined scripts/prompts to handle that specific objection better.
*   **Value:** Increases conversion rates.

### 12. The "Property Matcher Analyst"
*   **Trigger:** "Debug why [Property] wasn't recommended to [Lead]."
*   **Role:** Data Analyst.
*   **Protocol:** Traces the matching algorithm's scoring logic for a specific lead-property pair to explain the exclusion (e.g., "Budget mismatch", "Wrong school district").
*   **Value:** Explains "AI Magic" to stakeholders.

---

## 💻 Frontend & UX

### 13. The "i18n Scanner"
*   **Trigger:** "Find hardcoded strings in [Component] for internationalization."
*   **Role:** Localization Specialist.
*   **Protocol:** Scans JSX/TSX for user-facing text that isn't wrapped in translation functions (e.g., `t('key')`).
*   **Value:** Ensures app is ready for global deployment.

### 14. The "A11y Auditor"
*   **Trigger:** "Check [Component] for accessibility issues."
*   **Role:** Accessibility Specialist.
*   **Protocol:** Checks for semantic HTML, `aria-label`s, alt text, color contrast ratios, and keyboard navigability.
*   **Value:** Ensures compliance and usability for all users.

### 15. The "Responsive Design Tester"
*   **Trigger:** "Analyze layout stability for [Component] on mobile."
*   **Role:** Frontend Designer.
*   **Protocol:** (Conceptually) Reviews CSS/Tailwind classes to ensure responsive breakpoints are handled correctly and elements won't overflow.
*   **Value:** Prevents broken UIs on small screens.

---

## 🚀 DevOps & Engineering

### 16. The "Docker Optimizer"
*   **Trigger:** "Optimize the Dockerfile for build size and speed."
*   **Role:** DevOps Engineer.
*   **Protocol:** Reviews `Dockerfile` for layer caching efficiency, multi-stage build usage, and unnecessary package installations.
*   **Value:** Faster deployments and lower storage costs.

### 17. The "Config Guardian"
*   **Trigger:** "Audit environment variables and config files."
*   **Role:** SysAdmin.
*   **Protocol:** Ensures `env.example` matches code usage, checks for hardcoded config values, and validates config file syntax (YAML/JSON).
*   **Value:** Prevents "it works on my machine" deployment failures.

### 18. The "Release Manager"
*   **Trigger:** "Draft release notes for version [X.Y.Z]."
*   **Role:** Product Manager.
*   **Protocol:** Summarizes git commits since the last tag, categorizes them (Features, Fixes, Chores), and writes a user-friendly changelog.
*   **Value:** Automates documentation overhead.

---

## 🧠 Advanced Reasoning

### 19. The "First Principles Thinker"
*   **Trigger:** "Critique this solution from first principles."
*   **Role:** Critical Thinker.
*   **Protocol:** Breaks a proposed solution down to its fundamental truths and reconstructs it. Challenges assumptions (e.g., "Do we actually need a database here?").
*   **Value:** Avoids over-engineering and "cargo cult" programming.

### 20. The "Prompt Engineer"
*   **Trigger:** "Optimize this system prompt for [Model] efficiency."
*   **Role:** LLM Specialist.
*   **Protocol:** Analyzes a prompt for token usage, clarity, and instruction adherence. Suggests compression or restructuring for better performance.
*   **Value:** Saves money and improves AI response quality.

### 21. The "Data Anonymizer"
*   **Trigger:** "Sanitize this log/dataset for sharing."
*   **Role:** Privacy Officer.
*   **Protocol:** Detects PII (Emails, Phones, Names, IPs) in text blocks and replaces them with placeholders (e.g., `[REDACTED_EMAIL]`).
*   **Value:** Enables safe sharing of debug data.

### 22. The "Migration Guide"
*   **Trigger:** "Plan the migration from [Lib A] to [Lib B]."
*   **Role:** Migration Specialist.
*   **Protocol:** Identifies all usage of Lib A, maps equivalent functions in Lib B, and creates a step-by-step find-and-replace strategy.
*   **Value:** De-risks major dependency swaps.

### 23. The "API Contract Lawyer"
*   **Trigger:** "Verify [Endpoint] against the OpenAPI spec."
*   **Role:** API Governance.
*   **Protocol:** Compares implementation code (route handlers, response types) against the defined Swagger/OpenAPI document to ensure they match exactly.
*   **Value:** Prevents frontend-backend integration breakages.

### 24. The "Test Coverage Analyst"
*   **Trigger:** "Identify critical paths missing test coverage."
*   **Role:** QA Strategist.
*   **Protocol:** Maps business-critical logic and cross-references it with existing test files. Highlights gaps where bugs would be catastrophic.
*   **Value:** Prioritizes testing effort where it matters most.

### 25. The "Readme Polisher"
*   **Trigger:** "Update the README for [Project] based on recent changes."
*   **Role:** Technical Writer.
*   **Protocol:** Reads the current code capabilities and compares them to the README. Updates setup steps, feature lists, and examples to be accurate.
*   **Value:** Keeps documentation "living" and accurate.
