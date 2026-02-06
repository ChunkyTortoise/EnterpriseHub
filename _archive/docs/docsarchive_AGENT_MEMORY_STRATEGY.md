# Agent Memory Strategy: The "Graphiti" Brain

To move beyond stateless "chatbots" to intelligent "agents," you need a structured memory strategy. This document defines how to leverage your existing **Graphiti** integration to build a persistent, evolving brain for your Real Estate AI.

## 1. Memory Architecture Layers

We divide memory into 3 retention layers:

| Layer | Type | Storage | Retention | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Short-Term** | **Working Memory** | Redis / Context Window | Session Only | Holding current conversation context, active tool outputs. |
| **Mid-Term** | **Episodic Memory** | Graphiti (Edges) | Days/Weeks | "Last time we spoke, you were looking for a 3bd." (Continuity). |
| **Long-Term** | **Semantic Memory** | Graphiti (Nodes) | Permanent | Facts about the world: "Hyde Park is expensive," "John is an Investor." |

---

## 2. Graphiti Schema Definition (Real Estate Domain)

Define these Entity Types and Relation Types in your Graphiti setup to enforce structured learning.

### Entity Types
*   **`Lead`**: A human prospect (e.g., "Sarah Jones").
*   **`Agent`**: A human real estate agent (e.g., "Jorge").
*   **`Property`**: A specific listing (e.g., "123 Maple St").
*   **`Location`**: A neighborhood or city (e.g., "Round Rock").
*   **`Criterion`**: A specific preference (e.g., "Budget < $500k", "Needs Pool").

### Relation Types
*   `INTERESTED_IN` (Lead -> Property)
*   `LOCATED_IN` (Property -> Location)
*   `HAS_BUDGET` (Lead -> Criterion)
*   `REJECTED` (Lead -> Property) *Crucial for learning negative preferences*
*   `WORKS_WITH` (Lead -> Agent)

---

## 3. Storage Triggers (When to Save)

Do not save everything. Save only **Signal**, not Noise.

### ✅ Save These (Episodic/Semantic):
1.  **Hard Facts:** "My budget is $450k." -> `(Lead) -[HAS_BUDGET]-> ($450k)`
2.  **Strong Opinions:** "I hate HOAs." -> `(Lead) -[DISLIKES]-> (HOA)`
3.  **Life Events:** "I'm having a baby in June." -> `(Lead) -[HAS_TIMELINE]-> (June/Baby)`
4.  **Decisions:** "I want to offer on 123 Maple." -> `(Lead) -[OFFERING_ON]-> (123 Maple)`

### ❌ Do Not Save (Working Memory Only):
1.  Greetings/Pleasantries ("Hi, how are you?").
2.  Transient logistics ("Call me in 5 mins").
3.  Failed tool outputs or system errors.

---

## 4. Retrieval Strategy (RAG)

When a Lead messages the Agent, perform this **Context Injection**:

1.  **Identity Resolution:** Match Phone/Email to `Lead` node.
2.  **Graph Walk (1-Hop):** Fetch all direct edges (`HAS_BUDGET`, `DISLIKES`).
3.  **Graph Walk (2-Hop - Optional):** Fetch related nodes.
    *   *Example:* Lead -> `INTERESTED_IN` -> `Neighborhood` -> `AVERAGE_PRICE`.
    *   *Context:* "You like Hyde Park, but remember the average price there is $650k."
4.  **Inject:** Format into the `relevant_knowledge` section of the System Prompt.

---

## 5. Memory Consolidation (The "Dream" Cycle)

Agents need sleep. Run a nightly batch job (`consolidate_memory.py`):

1.  **Conflict Resolution:** If Lead said "Budget $400k" last week and "$500k" today, mark $500k as `current` and archive $400k as `historical`.
2.  **Insight Generation:** If Lead rejected 5 houses with pools, create a new edge: `(Lead) -[LIKELY_DISLIKES]-> (Pool_Maintenance)`.
3.  **Pruning:** Remove isolated nodes or transient facts older than 90 days.
