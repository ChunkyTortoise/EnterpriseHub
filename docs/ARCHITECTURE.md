# EnterpriseHub Architecture

## System Overview

EnterpriseHub is a modular business intelligence platform built with Streamlit, featuring 7 independent business modules, shared utilities, and AI integrations.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Web App                       │
│                        (app.py)                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       │   Dynamic Module      │
       │   Loader & Router     │
       └───────────┬───────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐   ┌────▼────┐   ┌────▼────┐
│Module 1│   │Module 2 │   │Module 7 │  ← 7 Business Modules
│        │   │         │   │         │     (Independent)
└───┬────┘   └────┬────┘   └────┬────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
         ┌────────▼────────┐
         │  Shared Utils   │  ← Common utilities
         │  (utils/)       │     (Config, Logging,
         └────────┬────────┘      Data Loading, etc.)
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼─────┐  ┌───▼───┐   ┌────▼────┐
│Claude AI│  │Yahoo  │   │TextBlob │  ← External Services
│  API    │  │Finance│   │   NLP   │
└─────────┘  └───────┘   └─────────┘
```

---

## Module Architecture

### Core Components

#### 1. Application Entry Point (`app.py`)
- **Responsibility**: Streamlit configuration, module routing
- **Pattern**: Front controller
- **Features**:
  - Dynamic module discovery and loading
  - Sidebar navigation
  - Session state management
  - Error boundary handling

#### 2. Business Modules (`modules/`)
Each module is fully independent with:
- **render()** function: Main entry point called by app.py
- **Self-contained logic**: No dependencies on other modules
- **Module README**: Comprehensive documentation
- **Dedicated tests**: Located in `tests/unit/`

**Module List**:
1. **Margin Hunter** - CVP analysis and break-even calculations
2. **Content Engine** - AI-powered LinkedIn post generation
3. **Data Detective** - Statistical analysis and data profiling
4. **Financial Analyst** - Stock analysis with AI insights
5. **Market Pulse** - Technical analysis and predictions
6. **Marketing Analytics** - Campaign performance tracking
7. **Agent Logic** - Dual-mode sentiment analysis

**Module Pattern**:
```python
def render() -> None:
    """Main entry point called by app.py"""
    # Module logic here
    pass
```

#### 3. Shared Utilities (`utils/`)
Reusable components used across multiple modules:

| Utility | Purpose | Used By |
|---------|---------|---------|
| `config.py` | Environment configuration | All modules |
| `logger.py` | Centralized logging | All modules |
| `data_loader.py` | Yahoo Finance API client | Financial Analyst, Market Pulse |
| `indicators.py` | Technical indicators (RSI, MACD, etc.) | Market Pulse |
| `sentiment_analyzer.py` | Dual-mode sentiment (TextBlob + Claude) | Agent Logic |
| `data_generator.py` | Sample data for testing | Tests |
| `exceptions.py` | Custom exception classes | All modules |

---

## Data Flow

### 1. User Request Flow
```
User → Streamlit UI → app.py → Module.render() → Utils → External APIs → Results → UI
```

### 2. Module Execution Flow
```
1. User selects module from sidebar
2. app.py routes to module.render()
3. Module:
   a. Displays UI controls (inputs, toggles)
   b. Gathers user input
   c. Calls utilities/APIs
   d. Processes data
   e. Displays results (charts, text, tables)
```

### 3. AI Integration Flow (Dual-Mode Pattern)
```
User Input
    │
    ▼
Check API Key Available?
    │
    ├─ YES → Claude API (Premium)
    │         ├─ Retry Logic (3 attempts)
    │         ├─ Exponential Backoff (1s→2s→4s)
    │         └─ Return AI Response
    │
    └─ NO  → TextBlob (Free Fallback)
              └─ Return Basic Analysis
```

---

## Design Patterns

### 1. **Modular Monolith**
- Single application with independent modules
- Modules share utilities but not business logic
- Zero coupling between business modules

**Benefits**:
- Easy to add/remove modules
- Simple to test in isolation
- Multiple developers can work in parallel

### 2. **Strategy Pattern (AI Integration)**
- Dual-mode: Free fallback (TextBlob) + Premium (Claude API)
- Graceful degradation when API unavailable
- User-controlled toggling

**Implementation**:
```python
if api_key_available and user_enabled_ai:
    result = claude_analysis()  # Premium
else:
    result = textblob_analysis()  # Free
```

### 3. **Dependency Injection**
- Configuration injected via environment variables
- API clients passed to functions
- Easy to mock in tests

### 4. **Retry Pattern**
- Exponential backoff for API failures
- Configurable retry attempts (default: 3)
- Specific error handling (RateLimitError, APIConnectionError, APITimeoutError)

**Implementation**:
```python
@retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)
def api_call():
    # API logic
    pass
```

---

## Technology Stack

### Core Framework
- **Python 3.8+**: Primary language
- **Streamlit 1.28.0**: Web framework for UI
- **Pandas 2.1.3**: Data manipulation
- **NumPy 1.26.2**: Numerical computing

### Visualization
- **Plotly 5.17.0**: Interactive charts
- **Graphviz 0.20.1**: Diagram rendering

### AI & APIs
- **Anthropic Claude 3.5 Sonnet**: AI insights and content generation
- **Yahoo Finance API (yfinance)**: Real-time stock data
- **TextBlob 0.17.1**: NLP and sentiment analysis

### Data Science
- **TA-Lib (ta)**: Technical analysis indicators
- **SciPy 1.11.4**: Statistical functions

### Development
- **pytest**: Testing framework
- **mypy**: Static type checking
- **Black, isort**: Code formatting
- **flake8**: Linting
- **pre-commit**: Git hooks

---

## External Service Integration

### 1. Claude API (Anthropic)
- **Used by**: Content Engine, Financial Analyst, Agent Logic
- **Model**: claude-3-5-sonnet-20241022
- **Features**: Content generation, financial insights, sentiment analysis
- **Reliability**: Retry logic with exponential backoff
- **Fallback**: TextBlob for sentiment, disabled state for others

### 2. Yahoo Finance API
- **Used by**: Financial Analyst, Market Pulse, Data Loader
- **Library**: yfinance 0.2.33
- **Features**: Stock data, historical prices, company info
- **Caching**: In-memory cache with TTL
- **Error Handling**: Graceful failures with user-friendly messages

### 3. TextBlob
- **Used by**: Agent Logic (sentiment analysis)
- **Features**: Basic sentiment scoring (-1 to +1)
- **Purpose**: Free fallback when Claude API unavailable
- **Reliability**: Always available (no API required)

---

## Security Architecture

### 1. API Key Management
- **Storage**: Environment variables (`.env` file, gitignored)
- **Access**: Centralized config.py with validation
- **Session**: Cached in Streamlit session state
- **Never exposed**: Not logged, not displayed in UI

### 2. Input Validation
- **User inputs**: Sanitized and validated before processing
- **File uploads**: Type and size validation
- **API responses**: Schema validation where applicable

### 3. Error Handling
- **Principle**: Never expose internal errors to users
- **Practice**: Generic user messages, detailed logs
- **Secrets**: No API keys or sensitive data in error messages

### 4. Dependencies
- **Security scanning**: bandit (SAST), pip-audit (dependency check)
- **Updates**: Manual dependency updates (Dependabot configuration planned)
- **Audit**: Pre-commit hooks run security checks

---

## Testing Strategy

### Test Organization
```
tests/
├── unit/                    # Module tests (7 files)
│   ├── test_agent_logic.py
│   ├── test_content_engine.py
│   ├── test_data_detective.py
│   ├── test_financial_analyst.py
│   ├── test_margin_hunter.py
│   ├── test_market_pulse.py
│   └── test_marketing_analytics.py
├── integration/             # API integration tests
│   └── test_data_loader.py
├── conftest.py             # Shared fixtures
└── test_imports.py         # Import verification
```

### Test Levels

1. **Unit Tests** (`tests/unit/`)
   - Module logic in isolation
   - Mocked external dependencies
   - Fast execution (<1s per test)
   - Coverage: 220+ tests

2. **Integration Tests** (`tests/integration/`)
   - External API interactions
   - Data loading and caching
   - Slower execution (network calls)
   - Coverage: API clients

3. **End-to-End Tests** (Planned)
   - Full user workflows
   - Selenium/Playwright
   - Screenshot validation

### Test Coverage
- **Target**: 85%+ coverage
- **Current**: ~85-90% coverage
- **Coverage Report**: HTML report in `htmlcov/`
- **CI/CD**: Tests run on Python 3.8, 3.9, 3.10, 3.11

---

## Deployment Architecture

### Local Development
```
Developer Machine
    │
    ├─ Virtual Environment (.venv/)
    ├─ Environment Variables (.env)
    ├─ Pre-commit Hooks
    └─ Streamlit Dev Server (localhost:8501)
```

### Production (Streamlit Cloud)
```
GitHub Repository
    │
    ├─ Push to main branch
    │
    ▼
Streamlit Cloud
    │
    ├─ Auto-deploy
    ├─ Environment variables (secrets.toml)
    ├─ Python 3.11 runtime
    └─ HTTPS endpoint
```

### CI/CD Pipeline
```
Git Push
    │
    ▼
GitHub Actions
    │
    ├─ Lint (Black, isort, flake8)
    ├─ Type Check (mypy)
    ├─ Test (pytest on Python 3.8-3.11)
    ├─ Security Scan (bandit, pip-audit)
    └─ Build Verification
         │
         ├─ SUCCESS → Deploy to Streamlit Cloud
         └─ FAILURE → Block deployment, notify developer
```

---

## Performance Considerations

### 1. Caching
- **Streamlit @st.cache_data**: Expensive computations cached
- **Data Loading**: Yahoo Finance data cached with TTL
- **API Responses**: Claude responses not cached (freshness)

### 2. Lazy Loading
- **Modules**: Loaded only when selected by user
- **Libraries**: Heavy imports (plotly, pandas) only when needed
- **Data**: Charts rendered on-demand

### 3. Optimization
- **DataFrame operations**: Vectorized with pandas/numpy
- **Chart rendering**: Plotly with WebGL for large datasets
- **Memory**: Session state cleared on navigation

---

## Scalability

### Current State (Single-User Streamlit App)
- **Deployment**: Streamlit Cloud (single container)
- **Concurrency**: One user session per instance
- **State**: In-memory session state
- **Database**: None (stateless)

### Future Scaling Options

1. **Horizontal Scaling**
   - Deploy multiple Streamlit instances
   - Load balancer distributes traffic
   - Session affinity required

2. **Database Integration**
   - PostgreSQL for persistent data
   - Redis for caching and session state
   - Celery for background tasks

3. **Microservices Architecture**
   - Split modules into separate services
   - API gateway for routing
   - Event-driven communication

4. **Serverless Functions**
   - AI analysis as Lambda/Cloud Functions
   - Data processing as background jobs
   - Cost-effective for variable load

---

## Extension Points

### Adding a New Module

1. **Create Module File**
   ```python
   # modules/new_module.py
   def render() -> None:
       """Main entry point"""
       st.title("New Module")
       # Module logic
   ```

2. **Add Module README**
   ```
   modules/README_NEW_MODULE.md
   ```

3. **Create Tests**
   ```python
   # tests/unit/test_new_module.py
   def test_new_module():
       # Test logic
   ```

4. **Update app.py** (if not using dynamic loading)
   ```python
   # app.py will auto-discover modules
   # No changes needed if following naming convention
   ```

### Adding External Integration

1. **Add client to utils/**
   ```python
   # utils/new_api_client.py
   class NewAPIClient:
       def __init__(self, api_key: str):
           self.api_key = api_key
   ```

2. **Add retry logic**
   ```python
   @retry_with_exponential_backoff(max_attempts=3)
   def call_api(self):
       # API logic
   ```

3. **Add tests**
   ```python
   # tests/integration/test_new_api_client.py
   ```

4. **Update .env.example**
   ```
   NEW_API_KEY=your_api_key_here
   ```

---

## Monitoring & Observability

### Logging
- **Library**: Python logging module
- **Configuration**: `utils/logger.py`
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Format**: Timestamp, level, module, message
- **Output**: Console (development), File (production)

### Metrics (Planned)
- **User Analytics**: Page views, module usage
- **Performance**: Response times, API latency
- **Errors**: Exception tracking, error rates
- **Business**: Generated posts, analyzed stocks

### Error Tracking (Planned)
- **Sentry**: Real-time error monitoring
- **Alerts**: Email/Slack on critical errors
- **Context**: User session, environment info

---

## Security Best Practices

1. **Never commit secrets**: Use .env files, gitignored
2. **Validate all inputs**: Sanitize user data before processing
3. **Keep dependencies updated**: Regular security patches
4. **Use HTTPS**: Encrypt data in transit
5. **Least privilege**: Minimal API permissions
6. **Audit logs**: Track sensitive operations
7. **Rate limiting**: Prevent abuse (handled by Claude API)
8. **Input validation**: Schema validation for external data

---

## Documentation Structure

```
EnterpriseHub/
├── README.md                        # Main documentation
├── CONTRIBUTING.md                  # Contribution guidelines
├── SECURITY.md                      # Security policy
├── CHANGELOG.md                     # Version history
├── LICENSE                          # MIT License
├── Deploy.md                        # Deployment guide
├── PROJECT_STATE.md                 # Current state
│
├── docs/
│   └── ARCHITECTURE.md              # This file
│
├── modules/
│   ├── README_MODULE_NAME.md        # 7 module READMEs
│   └── ...
│
├── scenarios/
│   ├── README.md                    # Scenario index
│   └── [industry]-template.md       # 3 industry templates
│
└── assets/
    ├── DEMO-VIDEO-INSTRUCTIONS.md   # Video guide
    ├── SCREENSHOT-INSTRUCTIONS.md   # Screenshot guide
    ├── Certs.md                     # Certifications
    └── Courses.md                   # Courses
```

---

## Contact & Contribution

- **Repository**: https://github.com/ChunkyTortoise/enterprise-hub
- **Issues**: https://github.com/ChunkyTortoise/enterprise-hub/issues
- **Contributing**: See CONTRIBUTING.md
- **Security**: See SECURITY.md

---

Last Updated: December 6, 2025
Version: 0.1.0
