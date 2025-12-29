# Enterprise Hub - Claude Code Context

> A Streamlit-based multi-module platform with 10 specialized business tools.

**Repository:** [github.com/ChunkyTortoise/EnterpriseHub](https://github.com/ChunkyTortoise/enterprise-hub)

## Table of Contents

- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Modules](#modules)
- [Utilities](#utilities)
- [Environment Variables](#environment-variables)
- [Critical Patterns](#critical-patterns)
- [Common Gotchas](#common-gotchas)
- [Anti-Patterns](#anti-patterns)
- [Troubleshooting](#troubleshooting)
- [Development Commands](#development-commands)
- [Pre-commit Hooks](#pre-commit-hooks)
- [CI/CD Pipeline](#cicd-pipeline)
- [Creating New Modules](#creating-new-modules)
- [Architecture Constraints](#architecture-constraints)
- [Related Documentation](#related-documentation)

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set API key for AI features
export ANTHROPIC_API_KEY="your-key-here"

# 3. Run the app
streamlit run app.py
```

**For development:**

```bash
# Install dev dependencies + pre-commit hooks
make install-dev
```

---

## Architecture Overview

Enterprise Hub is a Streamlit-based multi-module platform. All modules are independent, sharing only utility functions. Navigation is handled centrally in `app.py` with dynamic module loading.

**Key Directories:**

| Directory   | Purpose                                                    |
| ----------- | ---------------------------------------------------------- |
| `modules/`  | 10 independent Streamlit modules (no cross-imports)        |
| `utils/`    | Shared utilities (data_loader, config, logger, exceptions) |
| `tests/`    | 301 tests with pytest fixtures in `conftest.py`            |
| `docs/`     | Architecture docs, deployment guide, FAQ                   |
| `assets/`   | Icons, images, hero backgrounds                            |
| `_archive/` | **READ-ONLY** legacy code                                  |

---

## Modules

| Module                   | File                     | Purpose                                                      |
| ------------------------ | ------------------------ | ------------------------------------------------------------ |
| **Market Pulse**         | `market_pulse.py`        | Real-time stock monitoring with RSI, MACD, 4-panel charts    |
| **Financial Analyst**    | `financial_analyst.py`   | Fundamental analysis, financial statements, valuation metrics |
| **Margin Hunter**        | `margin_hunter.py`       | Cost-Volume-Profit analysis, break-even modeling, heatmaps   |
| **Agent Logic**          | `agent_logic.py`         | Automated market research and news sentiment analysis        |
| **Content Engine**       | `content_engine.py`      | AI-powered LinkedIn content generation via Claude API        |
| **Data Detective**       | `data_detective.py`      | Data profiling, quality scoring, statistical analysis        |
| **Marketing Analytics**  | `marketing_analytics.py` | Campaign tracking, ROI calculators, A/B testing, attribution |
| **Multi-Agent Workflow** | `multi_agent.py`         | Orchestrates 4 specialized agents for deep asset analysis    |
| **Smart Forecast**       | `smart_forecast.py`      | Time series forecasting with Random Forest, rolling window   |
| **Design System**        | `design_system.py`       | UI component gallery and theme showcase                      |

**Module registration:** See `app.py:34-85` (MODULES dict)

---

## Utilities

| Utility                | File                    | Purpose                                       |
| ---------------------- | ----------------------- | --------------------------------------------- |
| **data_loader**        | `data_loader.py`        | yfinance data fetching, technical indicators  |
| **sentiment_analyzer** | `sentiment_analyzer.py` | TextBlob + Claude sentiment analysis for news |
| **config**             | `config.py`             | Constants: BASE_PRICES, VOLATILITY, INDICATORS |
| **exceptions**         | `exceptions.py`         | Custom exception hierarchy (5 classes)        |
| **logger**             | `logger.py`             | Centralized logging (console output)          |
| **ui**                 | `ui.py`                 | Design system: 16 reusable UI components      |
| **indicators**         | `indicators.py`         | Technical indicator calculations              |
| **data_generator**     | `data_generator.py`     | Mock data generation for testing/demos        |
| **data_source_faker**  | `data_source_faker.py`  | Fake data sources for development             |
| **sales_formatter**    | `sales_formatter.py`    | Sales data formatting utilities               |
| **contrast_checker**   | `contrast_checker.py`   | WCAG accessibility contrast checking          |

---

## Environment Variables

| Variable            | Required | Default | Description                                 |
| ------------------- | -------- | ------- | ------------------------------------------- |
| `ANTHROPIC_API_KEY` | No       | None    | Enables AI features in Content Engine, etc. |
| `OPENAI_API_KEY`    | No       | None    | Alternative AI provider (if configured)     |

**Note:** If no API key is set, AI features gracefully degrade to non-AI alternatives (e.g., TextBlob for sentiment).

---

## Critical Patterns

### 1. Module Structure Pattern

**See:** `modules/market_pulse.py:22-30`, `modules/content_engine.py:155-163`

```python
def render() -> None:
    """Module entry point called by app.py"""
    st.title("Module Name")
    # All logic here - NO helper imports from other modules
```

**Key Rules:**

- Single `render()` function, no arguments
- All state in `st.session_state`
- Import utilities from `utils/`, NEVER from other modules

### 2. Session State Management

**See:** `modules/content_engine.py:278-280`, `modules/data_detective.py:44-47`

```python
# Initialize at module start (NOT conditionally inside functions)
if "generated_post" not in st.session_state:
    st.session_state.generated_post = None

# Update during execution
st.session_state.generated_post = new_value
```

**Why:** Streamlit reruns scripts on every interaction. Session state persists across reruns.

### 3. Data Caching Pattern

**See:** `utils/data_loader.py:22-27`

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_data(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """Always use @st.cache_data for expensive operations"""
    df = yf.download(ticker, period=period, progress=False)
    return df
```

**TTL:** 300 seconds (5 min) is standard across codebase.

### 4. Error Handling Pattern

**See:** `modules/market_pulse.py:71-89`

```python
try:
    with st.spinner(f"Fetching data for {ticker}..."):
        df = get_stock_data(ticker, period=period)
        if df is None or df.empty:
            st.error(f"No data found for {ticker}. Verify ticker.")
            return
except InvalidTickerError as e:
    logger.warning(f"Invalid ticker: {e}")
    st.error(f"{str(e)}")
    st.info("Tip: Use correct ticker (e.g., AAPL)")
except DataFetchError as e:
    logger.error(f"Data fetch error: {e}")
    st.error(f"Failed to fetch data: {str(e)}")
```

**Exception hierarchy** (`utils/exceptions.py`):

- `EnterpriseHubError` (base)
- `DataFetchError` (network/API failures)
- `InvalidTickerError` (invalid symbols)
- `DataProcessingError` (calculation failures)
- `ConfigurationError` (missing/invalid config)
- `APIError` (external API failures)

### 5. Anthropic API Integration Pattern

**See:** `modules/content_engine.py:79-152`, `utils/sentiment_analyzer.py:92-246`

```python
# 1. Conditional import (handle missing package)
try:
    from anthropic import Anthropic, APIError, RateLimitError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# 2. Get API key (env var or session state)
def _get_api_key() -> Optional[str]:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key
    return api_key

# 3. Graceful fallback when unavailable
if not ANTHROPIC_AVAILABLE:
    logger.warning("Anthropic not available, falling back to TextBlob")
    return process_news_sentiment(news_items)
```

### 6. yfinance Data Fetching

**See:** `utils/data_loader.py:44-74`

```python
# Validate ticker first
if not ticker or not ticker.strip():
    raise InvalidTickerError(ticker, "Ticker cannot be empty")

ticker = ticker.strip().upper()

# Fetch with error suppression (yfinance prints errors)
df = yf.download(ticker, period=period, interval=interval,
                 progress=False, show_errors=False)

# Handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
```

### 7. Testing Fixtures Pattern

**See:** `tests/conftest.py`

```python
@pytest.fixture
def sample_stock_data():
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    data = {
        'Open': np.random.uniform(100, 150, 30),
        'Close': np.random.uniform(100, 150, 30),
        'Volume': np.random.randint(1000000, 10000000, 30)
    }
    return pd.DataFrame(data, index=dates)
```

**Mock pattern:** Use `@patch` for Streamlit UI and external APIs.

---

## Common Gotchas

1. **Module imports:** NEVER import from another module (e.g., `from modules.x import y`). App breaks. Use `utils/` only.

2. **Widget keys:** Streamlit widgets need unique keys if multiple with same label:

   ```python
   st.text_input("Ticker", key="market_pulse_ticker")  # Good
   st.text_input("Ticker")  # Bad if another widget has same label
   ```

3. **Empty DataFrames:** Always check `if df is None or df.empty` after fetching. yfinance returns empty DF for invalid tickers, not None.

4. **Session state initialization:** Initialize ALL session state vars at module start, not conditionally inside functions. Prevents KeyError on rerun.

5. **Type hints required:** All functions must have type hints (`-> None`, `-> Optional[str]`). Enforced by ruff.

6. **MultiIndex columns:** yfinance sometimes returns MultiIndex columns. Always flatten:

   ```python
   if isinstance(df.columns, pd.MultiIndex):
       df.columns = df.columns.get_level_values(0)
   ```

---

## Anti-Patterns

### DON'T: Import from other modules

```python
# BAD - Will break the app
from modules.market_pulse import some_helper

# GOOD - Use shared utilities
from utils.data_loader import get_stock_data
```

### DON'T: Initialize state conditionally inside functions

```python
# BAD - May cause KeyError on rerun
def some_callback():
    if "my_var" not in st.session_state:
        st.session_state.my_var = None

# GOOD - Initialize at module top level
if "my_var" not in st.session_state:
    st.session_state.my_var = None

def some_callback():
    st.session_state.my_var = "value"
```

### DON'T: Forget to handle missing API keys

```python
# BAD - Crashes if no API key
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# GOOD - Graceful fallback
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    st.warning("API key not set. Using basic analysis.")
    return basic_analysis(data)
```

### DON'T: Skip empty data checks

```python
# BAD - May crash on empty data
df = get_stock_data(ticker)
latest_price = df['Close'].iloc[-1]

# GOOD - Check first
df = get_stock_data(ticker)
if df is None or df.empty:
    st.error("No data available")
    return
latest_price = df['Close'].iloc[-1]
```

---

## Troubleshooting

### yfinance rate limits

**Symptom:** `No data returned` errors after many requests

**Solution:** Data is cached for 5 minutes. Wait or clear cache with `st.cache_data.clear()`

### Widget key collisions

**Symptom:** `DuplicateWidgetID` error

**Solution:** Add unique `key=` parameter to widgets

### Missing API key behavior

**Symptom:** AI features show warnings or fallback results

**Solution:** Set `ANTHROPIC_API_KEY` environment variable or enter in app UI

### MultiIndex column errors

**Symptom:** `KeyError: 'Close'` when accessing DataFrame columns

**Solution:** Flatten columns after fetching (see Pattern 6)

### Session state KeyError

**Symptom:** `KeyError` when accessing session state

**Solution:** Initialize all state variables at module top level, before any callbacks

### Import errors on module load

**Symptom:** `ModuleNotFoundError` when navigating to a module

**Solution:** Check that module file exists in `modules/` and has valid Python syntax

### Pre-commit hook failures

**Symptom:** Commit rejected with linting/formatting errors

**Solution:** Run `ruff check --fix . && ruff format .` to auto-fix, then commit again

---

## Development Commands

### Quick Reference (Makefile)

```bash
make help          # Show all available commands
make install       # Install production dependencies
make install-dev   # Install dev dependencies + pre-commit hooks
make run           # Run Streamlit app
make test          # Run tests with coverage
make test-fast     # Run tests without coverage
make lint          # Run all linters
make format        # Auto-format code
make type-check    # Run mypy type checking
make security      # Run security checks (bandit + pip-audit)
make clean         # Clean up cache files
make all           # Run complete CI pipeline locally
```

### Direct Commands

```bash
# Run locally
streamlit run app.py

# Run tests with coverage
pytest --cov=modules --cov=utils -v

# Run specific test file
pytest tests/unit/test_market_pulse.py -v

# Linting (enforced in CI)
ruff check .
ruff format .

# Type checking
mypy modules/ utils/
```

---

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit`. Install with:

```bash
pre-commit install
```

**Configured hooks** (`.pre-commit-config.yaml`):

| Hook                    | Purpose                              |
| ----------------------- | ------------------------------------ |
| **ruff**                | Linting + auto-fix (line-length=100) |
| **ruff-format**         | Code formatting                      |
| **mypy**                | Type checking                        |
| **bandit**              | Security scanning                    |
| **trailing-whitespace** | Remove trailing whitespace           |
| **end-of-file-fixer**   | Ensure files end with newline        |
| **check-yaml**          | Validate YAML syntax                 |
| **check-added-large-files** | Prevent large file commits       |
| **check-merge-conflict** | Detect unresolved merge conflicts   |
| **detect-private-key**  | Prevent accidental key commits       |

**Manual run:**

```bash
pre-commit run --all-files
```

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push to `main`/`develop` and PRs.

**Jobs:**

| Job                | Python | Purpose                                      |
| ------------------ | ------ | -------------------------------------------- |
| **lint**           | 3.10   | Black, isort, flake8 formatting checks       |
| **test-unit**      | 3.10, 3.11 | Unit tests with coverage upload to Codecov |
| **test-integration** | 3.11 | Integration tests (after unit tests pass)   |
| **type-check**     | 3.10   | mypy type checking                           |
| **build**          | 3.10   | Verify app and modules can be imported       |

**Triggers:**

- Push to `main` or `develop`
- Pull requests to `main`

---

## Creating New Modules

Follow these steps to add a new module:

### Step 1: Create the module file

```python
# modules/my_new_module.py
"""
My New Module - Brief description.

This module provides [functionality].
"""

import streamlit as st

from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize session state at module level
if "my_module_data" not in st.session_state:
    st.session_state.my_module_data = None


def render() -> None:
    """Module entry point called by app.py."""
    st.title("My New Module")

    # Your module logic here
    st.write("Module content goes here")
```

### Step 2: Register in app.py

Add to the `MODULES` dict in `app.py`:

```python
MODULES = {
    # ... existing modules ...
    "🆕 My New Module": (
        "my_new_module",           # module filename (without .py)
        "My New Module",           # display title
        "assets/icons/my_icon.png" # icon path
    ),
}
```

### Step 3: Add tests

Create `tests/unit/test_my_new_module.py`:

```python
"""Tests for my_new_module."""
import pytest
from unittest.mock import patch

def test_render_runs_without_error():
    """Test that render() executes without exceptions."""
    with patch("streamlit.title"), patch("streamlit.write"):
        from modules.my_new_module import render
        render()  # Should not raise
```

### Step 4: Verify

```bash
# Check linting
ruff check modules/my_new_module.py

# Check types
mypy modules/my_new_module.py

# Run tests
pytest tests/unit/test_my_new_module.py -v

# Test the app
streamlit run app.py
```

---

## Architecture Constraints

1. **No cross-module imports** - Modules are independent
2. **Type hints required** - All functions
3. **Tests required** - Min 80% coverage for new code
4. **Archive is read-only** - Never modify `_archive/`
5. **Use session state** - All stateful data in `st.session_state`
6. **Cache expensive ops** - Use `@st.cache_data(ttl=300)` for API calls
7. **Pre-commit must pass** - All hooks must pass before commit

---

## Key Dependencies

| Package      | Version  | Purpose               |
| ------------ | -------- | --------------------- |
| streamlit    | 1.28.0   | Web framework         |
| pandas       | >=2.1.3  | Data manipulation     |
| plotly       | 5.17.0   | Interactive charts    |
| yfinance     | 0.2.33   | Market data           |
| ta           | 0.11.0   | Technical indicators  |
| anthropic    | 0.18.1   | Claude AI API         |
| textblob     | 0.17.1   | Basic NLP/sentiment   |
| scikit-learn | >=1.3.2  | ML forecasting        |
| scipy        | >=1.11.4 | Statistical functions |

See `requirements.txt` for full list.

---

## Related Documentation

| Document                 | Location                     | Purpose                            |
| ------------------------ | ---------------------------- | ---------------------------------- |
| **README**               | `README.md`                  | Project overview, screenshots      |
| **Architecture**         | `docs/ARCHITECTURE.md`       | System design, data flow           |
| **Deployment**           | `docs/DEPLOYMENT.md`         | Streamlit Cloud deployment guide   |
| **Demo Guide**           | `docs/DEMO_GUIDE.md`         | How to demo the application        |
| **FAQ**                  | `docs/FAQ.md`                | Common questions and answers       |
| **Contributing**         | `CONTRIBUTING.md`            | Contribution guidelines            |
| **Portfolio**            | `PORTFOLIO.md`               | Portfolio presentation guide       |
| **Changelog**            | `CHANGELOG.md`               | Version history                    |
