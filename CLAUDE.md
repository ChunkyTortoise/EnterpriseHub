# Enterprise Hub - Claude Code Context

## Architecture Overview

Enterprise Hub is a Streamlit-based multi-module platform with 7 specialized business tools. All modules are independent, sharing only utility functions. Navigation is handled centrally in `app.py` with dynamic module loading.

**Key Directories:**
- `modules/` - 7 independent Streamlit modules (no cross-imports)
- `utils/` - Shared utilities (data_loader, config, logger, exceptions)
- `tests/` - 301 tests with pytest fixtures in `conftest.py`
- `_archive/` - **READ-ONLY** legacy code

## Critical Patterns From Codebase

### 1. Module Structure Pattern
**See:** `modules/market_pulse.py:22-30`, `modules/content_engine.py:155-163`

Every module follows this exact pattern:
```python
def render() -> None:
    """Module entry point called by app.py"""
    st.title("Module Name")
    # All logic here - NO helper imports from other modules
```

**Key Rules:**
- Single `render()` function, no arguments
- All state in `st.session_state` (see Pattern 2)
- Import utilities from `utils/`, NEVER from other modules
- Module registration in `app.py:29-37` via `MODULES` dict

### 2. Session State Management
**See:** `modules/content_engine.py:278-280`, `modules/data_detective.py:44-47`

```python
# Initialize at module start
if "generated_post" not in st.session_state:
    st.session_state.generated_post = None

# Update during execution
st.session_state.generated_post = new_value

# Access anywhere in module
if st.session_state.generated_post:
    st.markdown(st.session_state.generated_post)
```

**Why:** Streamlit reruns scripts on every interaction. Session state persists across reruns.

### 3. Data Caching Pattern
**See:** `utils/data_loader.py:22-27`, `utils/data_loader.py:88-89`

```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_data(ticker: str, period: str = "1y") -> Optional[pd.DataFrame]:
    """Always use @st.cache_data for expensive operations"""
    df = yf.download(ticker, period=period, progress=False)
    return df
```

**Applied to:** All yfinance calls, all indicator calculations, all API fetches
**TTL:** 300 seconds (5 min) is standard across codebase

### 4. Error Handling Pattern
**See:** `modules/market_pulse.py:71-89`, `modules/financial_analyst.py:34-48`

```python
try:
    with st.spinner(f"Fetching data for {ticker}..."):
        df = get_stock_data(ticker, period=period)
        if df is None or df.empty:
            st.error(f"❌ No data found for {ticker}. Verify ticker.")
            return
except InvalidTickerError as e:
    logger.warning(f"Invalid ticker: {e}")
    st.error(f"❌ {str(e)}")
    st.info("💡 **Tip:** Use correct ticker (e.g., AAPL)")
except DataFetchError as e:
    logger.error(f"Data fetch error: {e}")
    st.error(f"❌ Failed to fetch data: {str(e)}")
    st.info("🔄 **Try:** Refresh page or different period")
```

**Custom exceptions hierarchy** in `utils/exceptions.py:9-44`:
- `EnterpriseHubError` (base)
- `DataFetchError` (network/API failures)
- `InvalidTickerError` (invalid symbols)
- `DataProcessingError` (calc failures)

### 5. Anthropic API Integration Pattern
**See:** `modules/content_engine.py:79-152`, `modules/financial_analyst.py:209-218`

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

# 3. Retry decorator for rate limits
@retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)
def _call_claude_api(client: Anthropic, prompt: str) -> str:
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        timeout=30.0
    )
    return message.content[0].text
```

**Retry pattern** (`content_engine.py:79-152`): Exponential backoff for `RateLimitError`, `APIConnectionError`, `APITimeoutError`. Never retry on auth errors.

### 6. Testing Fixtures Pattern
**See:** `tests/conftest.py:14-31`, `tests/unit/test_market_pulse.py:12-26`

```python
# conftest.py - reusable fixtures
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

# test file - use fixtures
def test_display_metrics(sample_stock_data):
    from modules.market_pulse import _display_metrics
    _display_metrics(sample_stock_data, "SPY")
```

**Mock pattern** (`test_market_pulse.py:38-70`): Use `@patch` for Streamlit UI and external APIs. Mock `st.text_input`, `st.selectbox`, `get_stock_data`, etc.

### 7. yfinance Data Fetching
**See:** `utils/data_loader.py:48-85`

```python
# Validate ticker first
if not ticker or not ticker.strip():
    raise InvalidTickerError(ticker, "Ticker cannot be empty")

ticker = ticker.strip().upper()

# Fetch with error suppression (yfinance prints errors)
df = yf.download(ticker, period=period, interval=interval,
                 progress=False, show_errors=False)

# Check for empty results
if df.empty:
    raise InvalidTickerError(ticker, f"No data for '{ticker}'")

# Handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
```

**Gotcha:** yfinance returns MultiIndex columns for some tickers. Always flatten before processing (`data_loader.py:121-122`).

### 8. Technical Indicators Pattern
**See:** `utils/data_loader.py:89-152`, `modules/market_pulse.py:273-394`

```python
# Calculate indicators (uses 'ta' library)
df['MA20'] = ta.trend.sma_indicator(df['Close'], window=20)
df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
df['MACD'] = ta.trend.macd(df['Close'])
df['Signal'] = ta.trend.macd_signal(df['Close'])

# Use in 4-panel Plotly chart
fig = make_subplots(
    rows=4, cols=1,
    row_heights=[0.5, 0.15, 0.15, 0.2],  # Price, RSI, MACD, Volume
    subplot_titles=(f"{ticker} Price", "RSI", "MACD", "Volume")
)
```

**Standard indicators:** MA20, RSI(14), MACD, Signal Line. All cached with `@st.cache_data`.

### 9. Streamlit UI Layout Pattern
**See:** `modules/market_pulse.py:34-38`, `modules/content_engine.py:286-311`

```python
# Multi-column layout for controls
col1, col2 = st.columns([1, 3])  # [width_ratio]
with col1:
    ticker = st.text_input("Ticker", value="SPY").upper()
with col2:
    period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y"])

# Tab-based navigation
tabs = st.tabs(["Profile", "AI Insights", "Quality", "Export"])
with tabs[0]:
    _render_data_profile(df)
```

**Spacing:** Use `st.markdown("---")` for visual separation between sections (seen in all modules).

## Common Gotchas

1. **Module imports:** NEVER import from another module (e.g., `from modules.x import y`). App breaks. Use `utils/` only.

2. **Widget keys:** Streamlit widgets need unique keys if multiple with same label. Use `key="module_name_widget"` (`financial_analyst.py:47`, `content_engine.py:119`).

3. **Empty DataFrames:** Always check `if df is None or df.empty` after fetching data. yfinance returns empty DF for invalid tickers, not None.

4. **Session state initialization:** Initialize ALL session state vars at module start, not conditionally. Prevents KeyError on rerun.

5. **Type hints required:** All functions must have type hints (`-> None`, `-> Optional[str]`). Enforced by ruff.

## Development Commands

```bash
# Local testing
streamlit run app.py

# Run tests with coverage
pytest --cov=modules --cov=utils -v

# Linting (enforced in CI)
ruff check .
ruff format .
```

## Where Things Live

- **Module registration:** `app.py:29-37` (MODULES dict)
- **Config constants:** `utils/config.py` (BASE_PRICES, INDICATORS)
- **Custom exceptions:** `utils/exceptions.py` (5 exception classes)
- **Test fixtures:** `tests/conftest.py` (sample_stock_data, valid_ticker)
- **Logging:** `utils/logger.py` (console output only)

## Architecture Constraints

1. **No cross-module imports** - Modules are independent
2. **Type hints required** - All functions
3. **Tests required** - Min 80% coverage for new code
4. **Archive is read-only** - Never modify `_archive/`
5. **Use session state** - All stateful data in `st.session_state`
