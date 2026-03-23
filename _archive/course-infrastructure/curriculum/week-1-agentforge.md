# Week 1: Agent Architecture (AgentForge)

## Overview

This week introduces multi-agent system architecture. Students build a tool-using agent with structured output parsing, pluggable memory, and dependency injection.

**Repo**: AgentForge
**Lab**: Build a multi-agent customer service bot

## Learning Objectives

By the end of this week, students will be able to:
1. Explain the difference between ReAct, function calling, and multi-agent routing patterns
2. Implement a tool registry with typed input/output schemas
3. Build structured output parsing with multiple fallback strategies
4. Configure memory backends (in-memory, Redis, PostgreSQL) via dependency injection
5. Write tests for agent behavior including tool selection and output validation

## Session A: Concepts + Live Coding (Tuesday)

### Part 1: Agent Architecture Fundamentals (15 min)

**Concepts covered:**
- What is an AI agent vs a chatbot vs a pipeline?
- Agent loop: observe → think → act → observe
- Architecture patterns:
  - **ReAct**: Reason + Act in alternating steps
  - **Function calling**: LLM selects and parameterizes tools
  - **Multi-agent routing**: Dispatcher selects specialist agents
- When to use each pattern (decision framework)

**Key diagram**: Agent architecture comparison (whiteboard/slides)

### Part 2: Live Coding — Build a 3-Tool Agent (45 min)

Walk through building an agent from scratch:

1. **Define tools** (15 min)
   - Tool interface: name, description, input schema, output schema
   - Tool registry pattern: register, discover, validate, execute
   - Example tools: `search_database`, `send_email`, `calculate_price`

2. **Build the agent loop** (15 min)
   - System prompt construction with tool descriptions
   - LLM call with function calling
   - Tool execution and result injection
   - Loop termination conditions

3. **Add structured output** (15 min)
   - Why raw LLM output is unreliable
   - Multi-strategy parsing:
     - Strategy 1: Direct JSON extraction
     - Strategy 2: Regex pattern matching
     - Strategy 3: Key-value extraction
     - Strategy 4: Re-prompt with explicit format instructions
   - Error handling and fallback chain

### Part 3: Lab Introduction (15 min)

- Walk through the Lab 1 README
- Demonstrate Codespace launch and environment verification
- Show the starter code structure and autograder test expectations
- Answer setup questions

### Part 4: Q&A (15 min)

## Session B: Lab Review + Deep Dive (Thursday)

### Part 1: Lab Solution Review (20 min)

Common patterns and mistakes from Lab 1 submissions:
- Tool schema validation (most common error: missing required fields)
- Agent loop not terminating (forgetting exit conditions)
- Output parsing that only handles the happy path
- Tests that check exact strings instead of behaviors

### Part 2: Deep Dive — Memory Systems (40 min)

**In-memory memory**:
- Dictionary-based, fast, no persistence
- Use case: development, testing, short-lived agents
- Implementation: `MemoryBackend` protocol with `store()`, `retrieve()`, `search()`

**Redis memory**:
- Key-value with TTL, shared across instances
- Use case: production agents that scale horizontally
- Implementation: Redis client with serialization layer

**PostgreSQL memory**:
- Full-text search, complex queries, persistent
- Use case: long-term memory, analytics, compliance
- Implementation: SQLAlchemy models with pgvector for semantic search

**Dependency injection pattern**:
- Why hardcoding backends creates untestable code
- Constructor injection: pass backend at creation time
- Configuration-driven: select backend via environment variable
- Testing: inject mock backends for deterministic tests

### Part 3: Advanced — Structured Output Deep Dive (20 min)

Guest segment or case study:
- How EnterpriseHub's multi-strategy parser handles 4.3M dispatches/sec
- Real production failure modes and how parsing fallbacks saved the system
- Metrics: parse success rates by strategy (JSON: 92%, regex: 6%, KV: 1.5%, re-prompt: 0.5%)

### Part 4: Week 2 Preview (10 min)

- RAG architecture overview
- What to read before next Tuesday
- Lab 2 preview: document Q&A system

## Key Takeaways

1. Agents are loops (observe-think-act), not single API calls
2. Tool registries with typed schemas prevent runtime errors
3. Never trust raw LLM output — always parse with fallbacks
4. Memory backends should be pluggable via dependency injection
5. Test agent behavior (tool selection, output structure), not exact text

## Resources

- AgentForge repository (starter code provided in lab)
- OpenAI Function Calling Guide
- Anthropic Tool Use Documentation
- "Agents" chapter from course textbook (provided in Discord)
