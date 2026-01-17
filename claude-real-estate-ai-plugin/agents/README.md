# Agents Directory

This directory contains specialized agents for the Claude Real Estate AI Accelerator plugin.

## Agent Overview

Agents are autonomous AI assistants that handle specific domains or workflows. They coordinate with the main Claude Code agent to provide specialized expertise.

## Available Agents

### 1. Architecture Sentinel
**File**: `architecture-sentinel.md`

**Purpose**: Validates architectural decisions against SOLID principles

**When to Use**:
- During code reviews
- When refactoring large modules
- For architectural decision validation

**Key Capabilities**:
- Single Responsibility Principle validation
- Open/Closed Principle checks
- Dependency Inversion analysis
- Code duplication detection
- Cyclomatic complexity measurement

### 2. TDD Guardian
**File**: `tdd-guardian.md`

**Purpose**: Enforces TDD discipline and test quality

**When to Use**:
- During test creation
- For test coverage validation
- When debugging failing tests

**Key Capabilities**:
- Enforces tests-before-implementation
- Validates test coverage thresholds (80%+)
- Ensures test independence
- Recommends proper mocking strategies
- Identifies test anti-patterns

### 3. Integration Test Workflow
**File**: `integration-test-workflow.md`

**Purpose**: Coordinates integration testing across services

**When to Use**:
- For multi-service testing
- API contract validation
- End-to-end workflow testing

**Key Capabilities**:
- API contract compatibility testing
- Database transaction handling
- External service mocking
- End-to-end user flow validation
- Service coordination testing

### 4. Context Memory
**File**: `context-memory.md`

**Purpose**: Manages conversation context and project memory

**When to Use**:
- Automatically maintains project context
- Long-running development sessions
- Cross-session knowledge preservation

**Key Capabilities**:
- Stores project patterns and conventions
- Tracks architectural decisions
- Preserves team preferences
- Maintains historical solutions
- Optimizes context window usage

### 5. Agent Communication Protocol
**File**: `agent-communication-protocol.md`

**Purpose**: Coordinates multi-agent workflows

**When to Use**:
- Complex feature development requiring multiple agents
- Parallel workflow execution
- Agent coordination and orchestration

**Key Capabilities**:
- Task delegation between agents
- Result aggregation from multiple agents
- Dependency resolution
- Conflict resolution
- Load balancing

## Agent Structure

Each agent definition follows this format:

```yaml
---
name: agent-name
description: "Expert in [domain]. Use when [trigger]."
tools: ["Read", "Grep", "Glob"]  # Restricted tool set
model: opus  # Model tier (haiku, sonnet, opus)
persona: security  # Persona type
context: fork  # Execution context (fork or shared)
priority: high  # Invocation priority
---

# Agent Name

## Role
You are a [domain] expert focusing on:
- Responsibility 1
- Responsibility 2

## Workflow
1. Step 1
2. Step 2

## Validation Criteria
- [ ] Check 1
- [ ] Check 2

## Communication Protocol
- Input format: [description]
- Output format: [description]
```

## Agent Invocation

Agents are typically invoked automatically based on context or explicitly:

```bash
# Automatic invocation (based on task context)
# Architecture Sentinel automatically runs during code reviews

# Explicit invocation
claude agent architecture-sentinel --review-file=src/service.py

# Multi-agent coordination
claude agent-swarm --agents=tdd-guardian,integration-test-workflow
```

## Agent Best Practices

### 1. Single Responsibility
Each agent focuses on one domain or workflow.

### 2. Restricted Tools
Agents have minimal tool access for security and efficiency.

### 3. Isolated Context
Use `context: fork` for independent execution without polluting main context.

### 4. Clear Communication
Define explicit input/output formats for agent coordination.

### 5. Validation Criteria
Include explicit success criteria for agent tasks.

## Agent Coordination Patterns

### Sequential Chain
```
Analysis Agent → Design Agent → Implementation Agent → Validation Agent
```

### Parallel Swarm
```
Security Agent  ┐
Performance Agent├→ Synthesis Agent
Testing Agent   ┘
```

### Hierarchical
```
Coordinator Agent
├── Frontend Specialist
├── Backend Specialist
└── Testing Specialist
```

## Performance Metrics

**Context Efficiency**: 87% token savings through isolated agent contexts

**Parallel Execution**: 50% time reduction for independent tasks

**Model Selection**: 15% cost reduction through appropriate model matching

**Tool Restrictions**: Enhanced security through least privilege access

## Creating New Agents

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on creating custom agents.

### Quick Start

1. Create agent definition file: `agents/new-agent.md`
2. Define YAML frontmatter with metadata
3. Write agent role and workflow
4. Specify validation criteria
5. Test agent with real scenarios
6. Submit PR with comprehensive description

## Agent Testing

```bash
# Test individual agent
./scripts/test-agents.sh agent-name

# Test agent coordination
./scripts/test-agent-coordination.sh

# Validate all agents
./scripts/validate-plugin.sh
```

## Resources

- [Agent SDK Documentation](https://docs.anthropic.com/claude/docs/agent-sdk)
- [Multi-Agent Patterns](https://docs.anthropic.com/claude/docs/multi-agent-patterns)
- [Tool Restrictions Guide](https://docs.anthropic.com/claude/docs/tool-restrictions)
