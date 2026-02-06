# Gemini Context Optimization Guide

This guide outlines the "Boundary-Weighted" prompting strategy and "Semantic Chunking" approach required to maximize Gemini 3.0's 10M token context window efficiency.

## 1. Boundary-Weighted Prompting

Research indicates that Large Language Models (LLMs) pay the most attention to the **beginning** and **end** of the prompt, with a "lost in the middle" phenomenon for very long contexts.

**Strategy:**
Construct prompts effectively by placing the most critical instructions and reference material at the boundaries.

**Template:**

```text
[SYSTEM PREAMBLE]
You are the EnterpriseHub Architect.
CRITICAL INSTRUCTION: Always prioritize security and backward compatibility.
Current Task: {task_description}

[REFERENCE: ARCHITECTURE]
... (High-level system design) ...

[CONTEXT: CODEBASE]
... (Bulk of the code context, e.g., 500k tokens) ...

[REFERENCE: STYLE GUIDE]
... (Specific coding patterns to follow) ...

[FINAL INSTRUCTION]
Based on the codebase above, perform the task: {task_description}.
Ensure you check for secrets before generating code.
```

**Implementation:**
Modify `gemini_llm_client.py` (or equivalent) to assemble prompts using this "Sandwich" topology.

## 2. Semantic Chunking for RAG

Traditional chunking (splitting by character count) breaks code logic. Semantic chunking respects function boundaries and class definitions.

**Strategy:**
1.  **Parse** code into Abstract Syntax Trees (AST).
2.  **Group** tokens by logical unit (e.g., a whole function).
3.  **Cluster** units based on semantic similarity (using embeddings) if they exceed the context window (though with Gemini 3.0, we can fit almost everything).

**Why it matters:**
Even with 1M+ context, sending *irrelevant* code adds noise. Semantic selection ensures that if we send `InventoryManager`, we also send the *full* `Property` class definition it depends on, not just the first half.

## 3. Implicit Caching

Gemini 3.0 automatically caches context that is repeated.

**Optimization:**
Ensure the `[SYSTEM PREAMBLE]` and `[REFERENCE: ...]` sections are byte-for-byte identical across requests. Dynamic variables (like "Current Date") should move to the *end* of the prompt or a variable section to avoid breaking the cache prefix.
