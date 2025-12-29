# Orchestrator Framework User Guide

> **A comprehensive guide to creating custom workflows with the EnterpriseHub Agent Swarm**

**Last Updated:** December 29, 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Core Concepts](#core-concepts)
4. [Creating Workflows](#creating-workflows)
5. [Pre-Built Agents](#pre-built-agents)
6. [Advanced Patterns](#advanced-patterns)
7. [Troubleshooting](#troubleshooting)
8. [API Reference](#api-reference)

---

## Introduction

The **Orchestrator Framework** enables you to build complex multi-agent workflows in under 30 minutes. By composing specialized agents into workflows, you can create sophisticated analysis pipelines with validation, conditional branching, and automatic error recovery.

### What You Can Build

- **Stock Analysis Workflows**: Combine data fetching, technical analysis, sentiment analysis, and forecasting
- **Validation Pipelines**: Gate workflow stages on quality thresholds
- **Dynamic Workflows**: Adapt execution paths based on data quality or agent confidence
- **Cross-Module Intelligence**: Correlate insights from multiple EnterpriseHub modules

### Key Features

- **7 Pre-Built Agents**: DataBot, TechBot, SentimentBot, ValidatorBot, ForecastBot, SynthesisBot, AnalystBot
- **Declarative Workflow Definition**: Define workflows with simple Python dataclasses
- **Automatic Dependency Resolution**: Agents execute in correct order based on dependencies
- **Built-in Retry Logic**: Exponential backoff for API rate limits and transient failures
- **Validation Gating**: Halt or continue workflows based on confidence thresholds
- **Conditional Execution**: Skip stages based on runtime conditions

---

## Quick Start

### 5-Minute Example: Stock Deep Dive

Create a workflow that fetches stock data, analyzes technicals, and generates a recommendation:

```python
from utils.orchestrator import Orchestrator, Workflow, WorkflowStage, AgentRegistry
from utils.agent_registry import ALL_AGENTS
from utils.agent_handlers import AGENT_HANDLERS

# 1. Initialize orchestrator
registry = AgentRegistry()
for agent_id, agent in ALL_AGENTS.items():
    registry.register_agent(agent)

orchestrator = Orchestrator(registry=registry)
for agent_id, handler in AGENT_HANDLERS.items():
    orchestrator.register_handler(agent_id, handler)

# 2. Define workflow
workflow = Workflow(
    workflow_id="stock_deep_dive",
    name="Stock Deep Dive",
    description="Comprehensive stock analysis",
    stages=[
        WorkflowStage(stage_id="data", agent_id="data_bot"),
        WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
        WorkflowStage(stage_id="sentiment", agent_id="sentiment_bot", depends_on=["data"]),
        WorkflowStage(
            stage_id="synthesis",
            agent_id="synthesis_bot",
            depends_on=["tech", "sentiment"]
        ),
    ]
)

# 3. Execute
result = orchestrator.execute_workflow(workflow, {"ticker": "AAPL", "period": "1y"})

# 4. Check results
if result.status == "success":
    print(f"Recommendation: {result.outputs['recommendation']}")
    print(f"Confidence: {result.outputs['confidence']:.1%}")
else:
    print(f"Workflow failed: {result.error}")
```

**Expected Output**:
```
🕵️ DataBot: Starting execution...
✅ DataBot: Completed successfully
📈 TechBot: Starting execution...
✅ TechBot: Completed successfully
📰 SentimentBot: Starting execution...
✅ SentimentBot: Completed successfully
🎓 SynthesisBot: Starting execution...
✅ SynthesisBot: Completed successfully
✅ Workflow 'Stock Deep Dive' completed successfully

Recommendation: BUY
Confidence: 82%
```

---

## Core Concepts

### Orchestrator Framework Architecture

The framework consists of four main components working together:

```
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator                             │
│  - Workflow Execution Engine                                 │
│  - Dependency Resolution                                     │
│  - Error Handling & Retry Logic                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │   AgentRegistry       │
       │  - Agent Definitions  │
       │  - Schema Validation  │
       └───────────┬───────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐   ┌────▼────┐   ┌────▼────┐
│DataBot │   │TechBot  │   │Sentiment│  ← 7 Pre-Built Agents
│        │   │         │   │   Bot   │     (Independent)
└───┬────┘   └────┬────┘   └────┬────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
         ┌────────▼────────┐
         │  Agent Handlers │  ← Execution Logic
         │  (handlers.py)  │     (Data fetch, analysis, etc.)
         └─────────────────┘
```

### Agent

An **Agent** is a specialized unit that performs a specific task.

**Key Properties**:
- `agent_id`: Unique identifier (e.g., "data_bot")
- `name`: Human-readable name (e.g., "DataBot")
- `input_schema`: Required inputs
- `output_schema`: Expected outputs
- `dependencies`: List of agent IDs this depends on

### Workflow

A **Workflow** is a sequence of stages that orchestrate multiple agents.

### WorkflowStage

A **WorkflowStage** represents one step in a workflow with dependencies and conditions.

---

## Creating Workflows

### Step 1: Initialize Orchestrator

```python
from utils.orchestrator import Orchestrator, AgentRegistry
from utils.agent_registry import ALL_AGENTS
from utils.agent_handlers import AGENT_HANDLERS

registry = AgentRegistry()
for agent_id, agent in ALL_AGENTS.items():
    registry.register_agent(agent)

orchestrator = Orchestrator(registry=registry)
for agent_id, handler in AGENT_HANDLERS.items():
    orchestrator.register_handler(agent_id, handler)
```

### Step 2: Define Workflow Stages

```python
workflow = Workflow(
    workflow_id="analysis",
    name="Stock Analysis",
    stages=[
        WorkflowStage(stage_id="data", agent_id="data_bot"),
        WorkflowStage(stage_id="tech", agent_id="tech_bot", depends_on=["data"]),
        WorkflowStage(stage_id="synthesis", agent_id="synthesis_bot",
                      depends_on=["tech"]),
    ]
)
```

### Step 3: Execute Workflow

```python
result = orchestrator.execute_workflow(workflow, {
    "ticker": "NVDA",
    "period": "1y"
})
```

---

## Pre-Built Agents

### 1. DataBot - Market Data Acquisition

**Purpose**: Fetch stock data, company info, and news

**Inputs**: `{"ticker": str, "period": str}`

**Outputs**: `{"df": pd.DataFrame, "info": dict, "news": list, "quality_score": float}`

### 2. TechBot - Technical Analysis

**Purpose**: Calculate MA20, RSI, MACD and generate trading signals

**Inputs**: `{"df": pd.DataFrame}`

**Outputs**: `{"signal": str, "confidence": float, "rsi_value": float}`

### 3. SentimentBot - News Sentiment Analysis

**Purpose**: Analyze news sentiment using Claude API

**Inputs**: `{"news": list, "ticker": str}`

**Outputs**: `{"verdict": str, "confidence": float, "article_count": int}`

### 4. ValidatorBot - Result Validation

**Purpose**: Validate agent outputs, detect contradictions

**Inputs**: `{"results": dict}`

**Outputs**: `{"passed": bool, "confidence": float, "errors": list}`

### 5. ForecastBot - ML Price Forecasting

**Purpose**: Generate 30-day ML forecast

**Inputs**: `{"df": pd.DataFrame}` (min 90 days)

**Outputs**: `{"forecast": pd.DataFrame, "trend": str, "metrics": dict}`

### 6. SynthesisBot - Final Recommendation

**Purpose**: Synthesize multi-agent results into BUY/HOLD/SELL

**Inputs**: `{"results": dict}`

**Outputs**: `{"recommendation": str, "confidence": float, "reasoning": str}`

### 7. AnalystBot - Cross-Module Intelligence

**Purpose**: Correlate insights from multiple modules

**Inputs**: `{"module_results": dict}`

**Outputs**: `{"integrated_insights": list, "divergences": list}`

---

## Advanced Patterns

### Conditional Execution

Execute stages only when certain conditions are met:

```python
def high_confidence(context):
    return context.get("confidence", 0) > 0.8

WorkflowStage(
    stage_id="forecast",
    agent_id="forecast_bot",
    condition=high_confidence,
    required=False
)
```

### Validation Gating

Halt workflow if validation fails:

```python
from utils.orchestrator import ValidationRule

workflow = Workflow(
    workflow_id="gated",
    stages=[...],
    validation_rules=[
        ValidationRule(
            validator=min_quality_check,
            action_on_fail="HALT"
        )
    ]
)
```

---

## Troubleshooting

### Agent Not Found

**Error**: `ValueError: Workflow references unregistered agent`

**Solution**: Verify agent is registered in `ALL_AGENTS`

### Missing Handler

**Error**: `ValueError: No handler registered for agent`

**Solution**: Add handler to `AGENT_HANDLERS` dictionary

### Validation Error

**Error**: `ValidationError: Missing required input`

**Solution**: Check agent's `input_schema` and provide all required inputs

---

## API Reference

### Orchestrator

```python
class Orchestrator:
    def execute_workflow(workflow: Workflow, inputs: Dict) -> WorkflowResult
```

### Workflow

```python
@dataclass
class Workflow:
    workflow_id: str
    name: str
    stages: List[WorkflowStage]
```

### WorkflowStage

```python
@dataclass
class WorkflowStage:
    stage_id: str
    agent_id: str
    depends_on: List[str] = field(default_factory=list)
    required: bool = True
```

---

**Need Help?**

- Agent Development: `docs/AGENT_DEVELOPMENT.md`
- Framework Overview: `docs/HANDOFF_AGENT_SWARM.md`
- Example Workflows: `modules/multi_agent.py`
