# Enterprise Hub API Documentation

Developer reference for extending and integrating EnterpriseHub.

---

## Table of Contents

1. [Core Components](#core-components)
2. [Agent Registry](#agent-registry)
3. [Data Loading](#data-loading)
4. [UI Components](#ui-components)
5. [Adding New Modules](#adding-new-modules)
6. [Configuration](#configuration)
7. [Testing Guidelines](#testing-guidelines)
8. [Troubleshooting](#troubleshooting)

---

## Core Components

### AgentOrchestrator

**Location:** `utils/orchestrator.py`

**Purpose:** Coordinates multi-agent workflows with sequential and parallel execution.

**Basic Usage:**

```python
from utils import Orchestrator, Workflow, WorkflowStage

# Create workflow
workflow = Workflow(
    name="Financial Analysis",
    description="Analyze stock data and generate insights"
)

# Add stages
workflow.add_stage(WorkflowStage(
    name="Data Loading",
    agent_name="data_bot",
    inputs={"ticker": "AAPL", "period": "1y"}
))

workflow.add_stage(WorkflowStage(
    name="Technical Analysis",
    agent_name="analyst_bot",
    inputs={"data": "data_bot.output"}
))

# Execute
orchestrator = Orchestrator()
result = orchestrator.execute_workflow(workflow)

print(result.success)  # True/False
print(result.outputs)  # Final outputs from all agents
```

**Key Classes:**

**WorkflowStage**
```python
class WorkflowStage:
    name: str                    # Stage identifier
    agent_name: str              # Agent to execute
    inputs: Dict[str, Any]       # Input parameters
    dependencies: List[str]      # Required previous stages
    timeout_seconds: int = 300   # Max execution time
```

**WorkflowResult**
```python
class WorkflowResult:
    success: bool                      # Overall success status
    outputs: Dict[str, Any]            # Combined outputs
    stage_results: List[AgentResult]   # Individual stage results
    execution_time: float              # Total time in seconds
    error: Optional[str]               # Error message if failed
```

**Advanced Example (Parallel Execution):**

```python
# Stages with no dependencies run in parallel
workflow.add_stage(WorkflowStage(
    name="Sentiment Analysis",
    agent_name="sentiment_bot",
    inputs={"ticker": "AAPL"}
))

workflow.add_stage(WorkflowStage(
    name="Technical Indicators",
    agent_name="tech_bot",
    inputs={"ticker": "AAPL"}
))

# These run simultaneously, then synthesis waits for both
workflow.add_stage(WorkflowStage(
    name="Synthesis",
    agent_name="synthesis_bot",
    inputs={
        "sentiment": "sentiment_bot.output",
        "technicals": "tech_bot.output"
    },
    dependencies=["Sentiment Analysis", "Technical Indicators"]
))
```

---

### Agent Registry

**Location:** `utils/agent_registry.py`

**Purpose:** Central registry of pre-configured agent personas.

**Available Agents:**

| Agent Name | Purpose | Required Inputs | Output Format |
|------------|---------|-----------------|---------------|
| `data_bot` | Load stock/market data | `ticker`, `period` | pandas DataFrame |
| `tech_bot` | Calculate technical indicators | `ticker` or `data` | Dict with RSI, MACD, MA |
| `sentiment_bot` | Analyze sentiment | `ticker` or `text` | Dict with score, magnitude |
| `analyst_bot` | Financial analysis | `ticker` | Dict with insights, recommendations |
| `forecast_bot` | Predictive analytics | `data`, `periods` | DataFrame with forecasts |
| `synthesis_bot` | Combine multiple inputs | `inputs` (dict) | Unified insights |
| `validator_bot` | Data validation | `data`, `schema` | ValidationResult |

**Usage:**

```python
from utils import get_agent, list_agents

# List all available agents
agents = list_agents()
for agent_id, agent in agents.items():
    print(f"{agent_id}: {agent.persona.name}")

# Get specific agent
data_agent = get_agent("data_bot")
result = data_agent.execute({"ticker": "MSFT", "period": "6mo"})

if result.success:
    print(result.output)  # pandas DataFrame
else:
    print(f"Error: {result.error}")
```

**Agent Execution Result:**

```python
class AgentResult:
    success: bool              # Execution success
    output: Any                # Agent output (varies by agent)
    error: Optional[str]       # Error message if failed
    execution_time: float      # Time in seconds
    metadata: Dict[str, Any]   # Additional info
```

---

## Data Loading

### Stock Data Loading

**Location:** `utils/data_loader.py`

**Main Functions:**

```python
from utils import get_stock_data, get_company_info, get_financials, get_news

# Load OHLCV data
data = get_stock_data(
    ticker="AAPL",
    period="1y",        # "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
    interval="1d"       # "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1d", "5d", "1wk", "1mo", "3mo"
)

# Returns pandas DataFrame with columns:
# - Date (index)
# - Open, High, Low, Close, Volume
# - Adj Close (adjusted closing price)

print(data.head())
```

**Company Information:**

```python
info = get_company_info("AAPL")

# Returns dict with:
# - name: Company name
# - sector: Industry sector
# - industry: Specific industry
# - marketCap: Market capitalization
# - employees: Number of employees
# - website: Company website
# - description: Business description
```

**Financial Statements:**

```python
financials = get_financials("AAPL")

# Returns dict with:
# - income_statement: Quarterly/annual income statement
# - balance_sheet: Balance sheet
# - cash_flow: Cash flow statement
```

**News Articles:**

```python
news = get_news("AAPL", max_articles=10)

# Returns list of dicts:
# - title: Article headline
# - publisher: Source
# - link: URL
# - published: Timestamp
# - summary: Brief description
```

**Error Handling:**

```python
from utils.exceptions import DataFetchError, InvalidTickerError

try:
    data = get_stock_data("INVALID_TICKER")
except InvalidTickerError as e:
    print(f"Invalid ticker: {e}")
except DataFetchError as e:
    print(f"Failed to fetch data: {e}")
```

### Technical Indicators

**Location:** `utils/indicators.py`

```python
from utils import calculate_indicators, add_all_indicators

# Add all indicators to DataFrame
data = get_stock_data("AAPL", "1y")
data = add_all_indicators(data)

# Now data includes:
# - RSI (Relative Strength Index)
# - MACD (Moving Average Convergence Divergence)
# - MA_20, MA_50, MA_200 (Moving Averages)
# - BB_upper, BB_lower (Bollinger Bands)
# - ATR (Average True Range)
```

**Individual Indicators:**

```python
from utils import calculate_rsi, calculate_macd, calculate_moving_averages

rsi = calculate_rsi(data['Close'], period=14)
macd = calculate_macd(data['Close'])
ma = calculate_moving_averages(data['Close'], periods=[20, 50, 200])
```

---

## UI Components

### Design System

**Location:** `utils/ui.py`

**Setup Interface:**

```python
import streamlit as st
from utils import setup_interface

# Apply theme (call at top of app)
setup_interface(theme_mode="dark")  # "light", "dark", "ocean", "sunset"
```

**Section Headers:**

```python
from utils import section_header

section_header("Module Title", "Optional subtitle explaining the module")
```

**Metric Cards:**

```python
from utils import card_metric

card_metric(
    label="Total Revenue",
    value="$1.2M",
    delta="+15%",
    help="Year-over-year growth"
)
```

**Status Badges:**

```python
from utils import status_badge

badge_html = status_badge("active")   # Green badge
badge_html = status_badge("pending")  # Gray badge
badge_html = status_badge("new")      # Blue badge

st.markdown(badge_html, unsafe_allow_html=True)
```

**Feature Cards:**

```python
from utils import feature_card

feature_card(
    icon="📊",
    title="Financial Modeling",
    description="Real-time CVP analysis with sensitivity heatmaps",
    status="active"
)
```

**Plotly Theme:**

```python
from utils import get_plotly_template
import plotly.graph_objects as go

fig = go.Figure(...)
fig.update_layout(template=get_plotly_template())
st.plotly_chart(fig)
```

---

## Adding New Modules

### Step 1: Create Agent Handler

Create `utils/my_custom_agent.py`:

```python
from typing import Dict, Any
from .orchestrator import Agent, AgentResult, PersonaB, AgentStatus
from .exceptions import AgentExecutionError

class MyCustomAgent:
    """Agent for [describe purpose]."""
    
    def __init__(self):
        self.persona = PersonaB(
            name="My Custom Agent",
            role="[Role description]",
            capabilities="[What it can do]",
            constraints="[What it cannot do]"
        )
    
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute agent logic.
        
        Args:
            inputs: Dictionary with required keys:
                - param1: Description
                - param2: Description
        
        Returns:
            AgentResult with output data
        """
        try:
            # Validate inputs
            if "param1" not in inputs:
                raise ValueError("param1 is required")
            
            # Your logic here
            result = self._process(inputs)
            
            return AgentResult(
                success=True,
                output=result,
                metadata={"agent": "my_custom_agent"}
            )
        
        except Exception as e:
            return AgentResult(
                success=False,
                error=str(e),
                metadata={"agent": "my_custom_agent"}
            )
    
    def _process(self, inputs: Dict[str, Any]) -> Any:
        """Internal processing logic."""
        # Implementation
        pass
```

### Step 2: Register Agent

Update `utils/agent_registry.py`:

```python
from .my_custom_agent import MyCustomAgent

# In AGENT_PERSONAS dict:
"my_custom": PersonaB(
    name="My Custom Agent",
    role="Custom data processor",
    capabilities="Processes custom data",
    constraints="Requires specific input format"
)

# In get_agent function:
elif agent_name == "my_custom":
    from .my_custom_agent import MyCustomAgent
    agent = Agent(persona=persona, handler=MyCustomAgent())
```

### Step 3: Create Streamlit Module

Add to `app.py`:

```python
def render_my_custom_module() -> None:
    """Render My Custom Module."""
    st.title("🎯 My Custom Module")
    st.markdown("Description of what this module does")
    
    # User inputs
    param1 = st.text_input("Parameter 1", placeholder="Enter value...")
    param2 = st.slider("Parameter 2", 0, 100, 50)
    
    if st.button("Execute", type="primary"):
        # Get agent
        agent = get_agent("my_custom")
        
        # Execute
        with st.spinner("Processing..."):
            result = agent.handler.execute({
                "param1": param1,
                "param2": param2
            })
        
        # Display results
        if result.success:
            st.success("Execution complete!")
            st.json(result.output)
        else:
            st.error(f"Error: {result.error}")

# Add to navigation in main():
module = st.sidebar.selectbox(
    "Select Module",
    [
        # ... existing modules
        "🎯 My Custom Module"
    ]
)

if module == "🎯 My Custom Module":
    render_my_custom_module()
```

### Step 4: Add Tests

Create `tests/unit/test_my_custom_agent.py`:

```python
import pytest
from utils.my_custom_agent import MyCustomAgent

def test_my_custom_agent_success():
    """Test successful execution."""
    agent = MyCustomAgent()
    result = agent.execute({"param1": "test", "param2": 42})
    
    assert result.success is True
    assert result.output is not None

def test_my_custom_agent_missing_param():
    """Test error handling for missing params."""
    agent = MyCustomAgent()
    result = agent.execute({})
    
    assert result.success is False
    assert "required" in result.error.lower()
```

---

## Configuration

### Environment Variables

Create `.streamlit/secrets.toml`:

```toml
# API Keys
ANTHROPIC_API_KEY = "sk-ant-..."

# Feature Flags
ENABLE_AI_FEATURES = true
ENABLE_REAL_TIME_DATA = true

# Performance
CACHE_TTL_SECONDS = 3600
MAX_API_CALLS_PER_MINUTE = 60
```

**Access in code:**

```python
import streamlit as st

api_key = st.secrets.get("ANTHROPIC_API_KEY")
enable_ai = st.secrets.get("ENABLE_AI_FEATURES", False)
```

### MCP Server Configuration

Copy `mcp_config.json.template` to `mcp_config.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN_HERE"
      }
    }
  }
}
```

---

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/unit/test_orchestrator.py -v

# With coverage
pytest --cov=utils --cov-report=html

# Fast tests only (skip slow integration tests)
pytest -m "not slow"
```

### Writing Tests

**Unit Test Example:**

```python
import pytest
from utils import get_stock_data

def test_get_stock_data_success():
    """Test successful data loading."""
    data = get_stock_data("AAPL", period="1mo")
    
    assert not data.empty
    assert "Close" in data.columns
    assert len(data) > 0

@pytest.mark.slow
def test_get_stock_data_large_range():
    """Test large date range (slow)."""
    data = get_stock_data("AAPL", period="10y")
    assert len(data) > 2000
```

**Integration Test Example:**

```python
def test_end_to_end_workflow():
    """Test complete workflow."""
    workflow = Workflow(name="Test Workflow")
    workflow.add_stage(WorkflowStage(
        name="Load Data",
        agent_name="data_bot",
        inputs={"ticker": "AAPL", "period": "1mo"}
    ))
    workflow.add_stage(WorkflowStage(
        name="Analyze",
        agent_name="analyst_bot",
        inputs={"data": "data_bot.output"}
    ))
    
    orchestrator = Orchestrator()
    result = orchestrator.execute_workflow(workflow)
    
    assert result.success is True
    assert len(result.stage_results) == 2
```

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'utils'`

**Solution:**

```bash
# Verify package structure
python -c "from utils import __version__; print(__version__)"

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### API Rate Limits

**Problem:** `RateLimitError` from Anthropic API

**Solution:**

```python
import time
from anthropic import RateLimitError

def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise
```

### Streamlit Caching Issues

**Problem:** Cached data is stale

**Solution:**

```python
import streamlit as st

# Clear specific cache
st.cache_data.clear()

# Or use TTL
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_data():
    ...
```

### Test Failures

**Problem:** Tests pass locally but fail in CI

**Solution:**

```bash
# Run with verbose output
pytest tests/ -vv --tb=short

# Check for environment differences
pytest --collect-only  # See what tests are discovered
```

---

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Anthropic Claude API](https://docs.anthropic.com)
- [yfinance Documentation](https://python-yahoofinance.readthedocs.io)
- [pytest Documentation](https://docs.pytest.org)
- [Plotly Python](https://plotly.com/python/)

---

**For questions or support, open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues).**

**Last Updated:** December 31, 2024
