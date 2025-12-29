# Agent Development Guide

> **A comprehensive guide for developers adding new agents to the EnterpriseHub Agent Swarm**

**Last Updated:** December 29, 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Agent Anatomy](#agent-anatomy)
4. [Handler Development](#handler-development)
5. [Registry Integration](#registry-integration)
6. [Testing](#testing)
7. [Pre-Built Agents Reference](#pre-built-agents-reference)
8. [Best Practices](#best-practices)

---

## Introduction

Adding a new agent to the EnterpriseHub orchestrator framework involves three main steps:

1. **Define Agent**: Create agent specification
2. **Implement Handler**: Write execution logic
3. **Register**: Add to registry and handler mappings

**Time to add a new agent**: ~20-30 minutes

---

## Quick Start

### 10-Minute Example: Create a Simple Agent

Let's create a **PriceAlertBot** that monitors price thresholds.

#### Step 1: Define Agent

In `utils/agent_registry.py`:

```python
from utils.orchestrator import Agent

PriceAlertBot = Agent(
    agent_id="price_alert_bot",
    name="PriceAlertBot",
    description="Monitors price thresholds and generates alerts",
    input_schema={
        "df": pd.DataFrame,
        "upper_threshold": float,
        "lower_threshold": float
    },
    output_schema={
        "alert_triggered": bool,
        "alert_type": str,
        "current_price": float,
        "breach_amount": float
    },
    dependencies=["data_bot"],
    timeout=10.0
)
```

#### Step 2: Implement Handler

In `utils/agent_handlers.py`:

```python
def price_alert_bot_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    PriceAlertBot execution logic: Check price thresholds.
    """
    df = inputs["df"]
    upper = inputs["upper_threshold"]
    lower = inputs["lower_threshold"]

    if df is None or df.empty:
        raise DataProcessingError("PriceAlertBot: Empty DataFrame")

    # Get current price
    current_price = df.iloc[-1]["Close"]

    # Check thresholds
    alert_triggered = False
    alert_type = "NONE"
    breach_amount = 0.0

    if current_price > upper:
        alert_triggered = True
        alert_type = "UPPER_BREACH"
        breach_amount = current_price - upper
    elif current_price < lower:
        alert_triggered = True
        alert_type = "LOWER_BREACH"
        breach_amount = lower - current_price

    logger.info(f"PriceAlertBot: Price=${current_price:.2f}, Alert={alert_type}")

    return {
        "alert_triggered": alert_triggered,
        "alert_type": alert_type,
        "current_price": current_price,
        "breach_amount": breach_amount
    }
```

#### Step 3: Register

Add to `ALL_AGENTS` in `utils/agent_registry.py`:
```python
ALL_AGENTS = {
    "data_bot": DataBot,
    # ... existing agents ...
    "price_alert_bot": PriceAlertBot,
}
```

Add to `AGENT_HANDLERS` in `utils/agent_handlers.py`:
```python
AGENT_HANDLERS = {
    "data_bot": data_bot_handler,
    # ... existing handlers ...
    "price_alert_bot": price_alert_bot_handler,
}
```

#### Step 4: Use in Workflow

```python
workflow = Workflow(
    workflow_id="price_monitor",
    name="Price Monitor",
    stages=[
        WorkflowStage(stage_id="data", agent_id="data_bot"),
        WorkflowStage(stage_id="alert", agent_id="price_alert_bot", depends_on=["data"]),
    ]
)

result = orchestrator.execute_workflow(workflow, {
    "ticker": "AAPL",
    "period": "1d",
    "upper_threshold": 180.0,
    "lower_threshold": 170.0
})
```

---

## Agent Anatomy

### Core Components

Every agent consists of **4 key components**:

1. **Metadata**: agent_id, name, description, timeout
2. **Schemas**: input_schema, output_schema
3. **Dependencies**: List of required agents
4. **Configuration**: Optional retry, validation settings

### Metadata

```python
agent_id="my_bot",        # Unique ID (snake_case)
name="MyBot",             # Display name (PascalCase)
description="Brief description",
timeout=30.0,             # Max execution time (seconds)
```

### Schemas

Define expected inputs and outputs for **automatic validation**:

```python
input_schema={
    "df": pd.DataFrame,
    "ticker": str,
    "period": str
},
output_schema={
    "result": dict,
    "confidence": float
}
```

### Dependencies

List agent IDs this agent depends on:

```python
dependencies=["data_bot", "tech_bot"]
```

---

## Handler Development

### Handler Function Signature

```python
def my_agent_handler(
    inputs: Dict[str, Any],
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent execution logic.

    Args:
        inputs: Input data (matches agent's input_schema)
        context: Shared context from previous agents

    Returns:
        Output dictionary (matches agent's output_schema)
    """
    pass
```

### Handler Structure Pattern

```python
def my_agent_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Extract inputs
    required_input = inputs["required_field"]
    optional_input = inputs.get("optional_field", default_value)

    # 2. Validate inputs
    if required_input is None:
        raise DataProcessingError("MyAgent: Missing required input")

    # 3. Log start
    logger.info(f"MyAgent: Starting with input={required_input}")

    # 4. Perform core logic
    try:
        result = perform_analysis(required_input)
    except Exception as e:
        logger.error(f"MyAgent: Analysis failed: {e}")
        raise DataProcessingError(f"MyAgent: {str(e)}")

    # 5. Log success
    logger.info(f"MyAgent: Success")

    # 6. Return outputs
    return {
        "result": result,
        "confidence": calculate_confidence(result)
    }
```

### Error Handling Patterns

**Fail Fast** (required data missing):
```python
if df is None or df.empty:
    raise DataProcessingError("MyAgent: No data provided")
```

**Graceful Degradation** (optional feature unavailable):
```python
try:
    advanced_feature = compute_advanced_metric(data)
except Exception as e:
    logger.warning(f"Advanced metric failed, using fallback: {e}")
    advanced_feature = fallback_metric(data)
```

### Accessing Context

Access outputs from previous agents via `context`:

```python
def synthesis_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    # Access DataBot outputs
    data_quality = context.get("quality_score", 0.5)

    # Access TechBot outputs
    tech_signal = context.get("signal", "NEUTRAL")

    # Synthesize
    recommendation = synthesize_signals(tech_signal)

    return {"recommendation": recommendation}
```

---

## Registry Integration

### Step 1: Add Agent Definition

In `utils/agent_registry.py`:

```python
MyAgent = Agent(
    agent_id="my_agent",
    name="MyAgent",
    description="Brief description",
    input_schema={"input1": str, "input2": int},
    output_schema={"output1": dict, "output2": float},
    dependencies=["data_bot"],
    timeout=30.0
)
```

### Step 2: Add to ALL_AGENTS Dictionary

```python
ALL_AGENTS = {
    "data_bot": DataBot,
    "tech_bot": TechBot,
    # ... existing agents ...
    "my_agent": MyAgent,  # ADD YOUR AGENT
}
```

### Step 3: Implement Handler

In `utils/agent_handlers.py`:

```python
def my_agent_handler(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """MyAgent execution logic."""
    # Implementation here
    pass
```

### Step 4: Add to AGENT_HANDLERS Dictionary

```python
AGENT_HANDLERS = {
    "data_bot": data_bot_handler,
    "tech_bot": tech_bot_handler,
    # ... existing handlers ...
    "my_agent": my_agent_handler,  # ADD YOUR HANDLER
}
```

---

## Testing

### Unit Tests

Create `tests/unit/test_my_agent.py`:

```python
import pytest
from utils.agent_handlers import my_agent_handler
from utils.exceptions import DataProcessingError


def test_my_agent_success():
    """Test successful execution."""
    inputs = {"input1": "test_value", "input2": 42}
    context = {}

    result = my_agent_handler(inputs, context)

    assert "output1" in result
    assert "output2" in result
    assert isinstance(result["output2"], float)


def test_my_agent_invalid_input():
    """Test error handling for invalid input."""
    inputs = {"input1": None, "input2": 42}
    context = {}

    with pytest.raises(DataProcessingError):
        my_agent_handler(inputs, context)
```

### Integration Tests

Test agent within workflow:

```python
def test_my_agent_in_workflow():
    """Test agent within workflow."""
    from utils.orchestrator import Orchestrator, Workflow, WorkflowStage
    from utils.agent_registry import ALL_AGENTS
    from utils.agent_handlers import AGENT_HANDLERS

    # Setup orchestrator
    registry = AgentRegistry()
    for agent_id, agent in ALL_AGENTS.items():
        registry.register_agent(agent)

    orchestrator = Orchestrator(registry=registry)
    for agent_id, handler in AGENT_HANDLERS.items():
        orchestrator.register_handler(agent_id, handler)

    # Execute workflow
    workflow = Workflow(
        workflow_id="test",
        stages=[
            WorkflowStage(stage_id="my_stage", agent_id="my_agent"),
        ]
    )

    result = orchestrator.execute_workflow(workflow, {"input1": "test", "input2": 42})

    assert result.status == "SUCCESS"
```

---

## Pre-Built Agents Reference

### Agent Summary

| Agent | Input | Output | Dependencies | Timeout |
|-------|-------|--------|--------------|---------|
| DataBot | ticker, period | df, info, news, quality_score | None | 30s |
| TechBot | df | signal, confidence, rsi_value | data_bot | 20s |
| SentimentBot | news, ticker | verdict, confidence, themes | data_bot | 45s |
| ValidatorBot | results | passed, confidence, errors | tech_bot, sentiment_bot | 15s |
| ForecastBot | df | forecast, trend, metrics | data_bot, tech_bot | 60s |
| SynthesisBot | results | recommendation, confidence | data_bot, tech_bot, sentiment_bot | 20s |
| AnalystBot | module_results | integrated_insights, divergences | tech_bot, forecast_bot | 30s |

---

## Best Practices

### 1. Agent Design Principles

**Single Responsibility**: Each agent should do ONE thing well

```python
# ✅ Good: Focused agent
TechBot = Agent(
    agent_id="tech_bot",
    description="Calculate technical indicators"
)

# ❌ Bad: Too many responsibilities
SuperBot = Agent(
    agent_id="super_bot",
    description="Fetch data, analyze, and forecast"  # Too broad
)
```

**Clear Dependencies**: Explicitly declare what you need

```python
# ✅ Good
SynthesisBot = Agent(
    dependencies=["data_bot", "tech_bot", "sentiment_bot"]
)

# ❌ Bad: Implicit dependencies
SynthesisBot = Agent(
    dependencies=[]  # Claims no dependencies but uses context data
)
```

### 2. Schema Design

**Be Specific**: Define exact types expected

```python
# ✅ Good
input_schema={
    "df": pd.DataFrame,
    "ticker": str,
    "threshold": float
}

# ❌ Bad
input_schema={
    "data": object,
    "params": dict
}
```

### 3. Error Handling

**Fail Fast for Critical Errors**:
```python
if df is None or df.empty:
    raise DataProcessingError("Critical: No data available")
```

**Degrade Gracefully for Optional Features**:
```python
try:
    advanced_metric = compute_advanced(df)
except Exception as e:
    logger.warning(f"Advanced metric failed: {e}")
    advanced_metric = compute_basic(df)
```

**Use Custom Exceptions** (from `utils/exceptions.py`):
- `DataFetchError`: For network/API failures
- `DataProcessingError`: For calculation failures
- `ValidationError`: For schema/validation failures
- `InvalidTickerError`: For invalid ticker symbols

### 4. Logging Best Practices

```python
logger.info(f"MyAgent: Starting with ticker={ticker}")
logger.info(f"MyAgent: Success, confidence={confidence:.2f}")
logger.warning(f"MyAgent: Low data quality ({quality:.1%})")
logger.error(f"MyAgent: Failed: {error_msg}")
```

### 5. Testing

**Test All Error Paths**:
```python
def test_agent_empty_data():
    with pytest.raises(DataProcessingError):
        handler({"df": pd.DataFrame()}, {})
```

**Use Fixtures for Common Data**:
```python
@pytest.fixture
def sample_stock_data():
    return pd.DataFrame({
        "Close": [100, 105, 110],
        "Volume": [1000000, 1100000, 1200000]
    })

def test_agent(sample_stock_data):
    result = handler({"df": sample_stock_data}, {})
    assert result["confidence"] > 0.5
```

---

## Next Steps

1. **Review Examples**: Study existing handlers in `utils/agent_handlers.py`
2. **Create Your Agent**: Follow the Quick Start template
3. **Test Thoroughly**: Aim for 80%+ coverage
4. **Create Workflows**: Integrate your agent (see `docs/ORCHESTRATOR_GUIDE.md`)
5. **Add to UI**: Create Streamlit interface in `modules/multi_agent.py`

---

**Need Help?**

- Framework Overview: `docs/HANDOFF_AGENT_SWARM.md`
- Workflow Creation: `docs/ORCHESTRATOR_GUIDE.md`
- Example Workflows: `modules/multi_agent.py`
