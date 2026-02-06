# Jorge's ML Scoring Intelligence Dashboard

> Advanced Machine Learning Model Performance Monitoring and A/B Testing Platform for Real Estate AI

## 🎯 Overview

The ML Scoring Dashboard is a comprehensive analytics platform designed specifically for Jorge's Real Estate AI ecosystem. It provides real-time monitoring, performance analysis, and A/B testing capabilities for machine learning models in production.

### ✨ Key Features

- **📊 Model Performance Metrics UI** - Real-time tracking of accuracy, precision, recall, and ROC-AUC
- **📈 Interactive Visualizations** - Plotly-powered charts for ROC curves, confidence distributions, and performance trends
- **🧪 A/B Testing Dashboard** - Champion vs challenger model comparison with statistical significance analysis
- **⚡ Inference Performance Monitoring** - Latency, throughput, and cache performance tracking
- **🚨 Model Health Alerts** - Automated alerting for performance degradation and system issues
- **🎛️ Global Filters** - Consistent filtering across all dashboard components

## 🏗️ Architecture

```
command_center/
├── components/
│   ├── __init__.py                    # Component exports
│   ├── ml_scoring_dashboard.py        # Main ML dashboard (400+ lines)
│   └── global_filters.py              # Shared filtering controls
├── ml_dashboard_integration_demo.py   # Integration demo
└── README_ML_Dashboard.md             # This documentation
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install required dependencies
pip install streamlit pandas plotly numpy

# Ensure Jorge's authentication components are available
pip install -r requirements.txt
```

### Running the Dashboard

```bash
# Run the integrated demo
streamlit run command_center/ml_dashboard_integration_demo.py

# Or run the standalone dashboard
python -c "from command_center.components.ml_scoring_dashboard import main; main()"
```

### Integration with Existing Dashboard

```python
# Import ML dashboard components
from command_center.components import (
    render_model_performance_overview,
    render_ab_testing_dashboard,
    get_global_filters
)

# Add to your existing dashboard
def render_ml_tab():
    filters = get_global_filters("ml_dashboard")
    filter_state = filters.render_sidebar_filters()

    render_model_performance_overview()
    render_ab_testing_dashboard()
```

## 📊 Dashboard Components

### 1. Model Performance Overview

**Features:**
- Real-time performance metrics (accuracy, precision, recall, F1-score, ROC-AUC)
- Model comparison matrix
- Performance status indicators
- Detailed metrics table

**Code Example:**
```python
from command_center.components import render_model_performance_overview

# Renders comprehensive model performance section
render_model_performance_overview()
```

### 2. Performance Visualizations

**Charts Included:**
- ROC Curve comparison across multiple models
- Confidence score distribution histograms
- Feature importance with SHAP values
- Performance trend analysis

**Code Example:**
```python
from command_center.components import render_performance_visualizations

# Renders interactive Plotly charts
render_performance_visualizations()
```

### 3. A/B Testing Dashboard

**Features:**
- Champion vs challenger comparison
- Statistical significance analysis
- Traffic split monitoring
- Automated winner selection recommendations

**Code Example:**
```python
from command_center.components import render_ab_testing_dashboard

# Renders A/B testing interface
render_ab_testing_dashboard()
```

### 4. Inference Performance Monitoring

**Metrics Tracked:**
- Model inference latency (ms)
- Prediction throughput (predictions/sec)
- Cache hit rate optimization
- Resource utilization

**Code Example:**
```python
from command_center.components import render_inference_performance_dashboard

# Renders performance monitoring section
render_inference_performance_dashboard()
```

### 5. Global Filters

**Filter Types:**
- Time range selection
- Model type filtering
- Performance thresholds
- A/B test status
- Metric type selection

**Code Example:**
```python
from command_center.components import GlobalFilters

# Initialize filters
filters = GlobalFilters("my_dashboard_filters")

# Render in sidebar
filter_state = filters.render_sidebar_filters()

# Apply filters to data
filtered_data = filters.apply_filters_to_data(raw_data)
```

## 🎨 Jorge's Theme Integration

The dashboard follows Jorge's established design patterns:

### Color Scheme
```python
JORGE_THEME = {
    'primary': '#3b82f6',      # Blue primary
    'secondary': '#1e3a8a',     # Dark blue
    'success': '#10b981',       # Green success
    'warning': '#f59e0b',       # Orange warning
    'error': '#ef4444',         # Red error
    'accent': '#8b5cf6',        # Purple accent
}
```

### Typography
- **Primary Font:** Space Grotesk (headings, metrics)
- **Secondary Font:** Inter (body text, labels)

### Components
- **Metric Cards:** Glass morphism with backdrop blur
- **Status Indicators:** Color-coded with emojis
- **Alert Boxes:** Contextual styling (success, warning, error)

## 📈 Data Integration

### Model Metrics Structure

```python
@dataclass
class ModelMetrics:
    model_name: str
    model_type: ModelType
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confidence_scores: List[float]
    prediction_counts: Dict[str, int]
    inference_latency: float
    throughput: float
    cache_hit_rate: float
    timestamp: datetime
```

### A/B Test Results Structure

```python
@dataclass
class ABTestResult:
    test_id: str
    champion_model: str
    challenger_model: str
    test_start: datetime
    test_end: Optional[datetime]
    champion_metrics: ModelMetrics
    challenger_metrics: ModelMetrics
    traffic_split: float
    statistical_significance: float
    winner: Optional[str]
```

### Real-Time Data Sources

In production, the dashboard integrates with:

- **ML Monitoring Systems:** MLflow, Weights & Biases, Neptune
- **Model Serving Platforms:** SageMaker, Azure ML, Vertex AI
- **Caching Systems:** Redis performance metrics
- **A/B Testing Frameworks:** Statsig, LaunchDarkly, Optimizely

## 🔧 Configuration

### Environment Variables

```bash
# Dashboard Configuration
STREAMLIT_THEME=dark
DASHBOARD_REFRESH_INTERVAL=30
CACHE_TTL=300

# Model Monitoring
ML_MONITORING_ENDPOINT=https://api.monitoring.example.com
ML_API_KEY=your_api_key_here

# A/B Testing
AB_TEST_PROVIDER=custom
AB_TEST_API_ENDPOINT=https://api.abtest.example.com
```

### Streamlit Configuration

```toml
# .streamlit/config.toml
[theme]
base = "dark"
primaryColor = "#3b82f6"
backgroundColor = "#0f172a"
secondaryBackgroundColor = "#1e293b"

[server]
enableCORS = false
enableXsrfProtection = false
```

## 🧪 Testing

### Unit Tests

```bash
# Run component tests
pytest tests/command_center/test_ml_dashboard.py -v

# Run filter tests
pytest tests/command_center/test_global_filters.py -v
```

### Integration Tests

```bash
# Test dashboard integration
pytest tests/command_center/test_dashboard_integration.py -v
```

### Performance Tests

```bash
# Test dashboard loading performance
pytest tests/command_center/test_performance.py -v
```

## 📱 Responsive Design

The dashboard is fully responsive with mobile-optimized layouts:

- **Desktop (>1200px):** Full feature set with sidebar filters
- **Tablet (768px-1200px):** Compact layout with collapsible sections
- **Mobile (<768px):** Stacked layout with simplified navigation

## 🔒 Security & Authentication

### Authentication Integration

```python
# Check user permissions
if not require_permission(user, 'ml_dashboard', 'read'):
    st.error("🚫 Access denied")
    st.stop()

# Role-based access control
if user.role == UserRole.ADMIN:
    render_admin_controls()
```

### Data Security

- **No PII in Logs:** Model metrics exclude personal information
- **API Key Management:** Secure credential storage
- **Session Management:** JWT-based authentication with expiration

## 🚀 Performance Optimization

### Caching Strategy

```python
# Cache model data for 60 seconds
@st.cache_data(ttl=60)
def get_model_performance_data():
    return fetch_model_metrics()

# Cache filter instances
@st.cache_resource
def get_global_filters():
    return GlobalFilters()
```

### WebSocket Integration (Future)

```python
# Real-time updates via WebSocket
async def setup_websocket():
    websocket = await connect_to_monitoring_service()

    async for message in websocket:
        update_dashboard_data(message)
        st.rerun()
```

## 📚 API Reference

### Core Functions

#### `render_dashboard_header()`
Renders the main dashboard header with live status information.

#### `get_model_performance_data() -> Dict[str, ModelMetrics]`
Retrieves current model performance metrics from monitoring systems.

**Returns:** Dictionary mapping model IDs to ModelMetrics objects

#### `render_ab_testing_dashboard()`
Renders the complete A/B testing interface with statistical analysis.

#### `GlobalFilters(filter_key: str)`
Initializes global filter component with session state management.

**Parameters:**
- `filter_key`: Unique key for filter state persistence

### Utility Functions

#### `apply_ml_dashboard_styles()`
Applies Jorge's theme CSS styling to the dashboard.

#### `create_roc_curve_chart(models: Dict[str, ModelMetrics]) -> go.Figure`
Creates ROC curve comparison chart for multiple models.

**Parameters:**
- `models`: Dictionary of model metrics
**Returns:** Plotly Figure object

## 🎯 Best Practices

### Component Usage

```python
# ✅ Good: Use cached functions for data
@st.cache_data(ttl=60)
def get_dashboard_data():
    return expensive_data_fetch()

# ✅ Good: Apply filters consistently
filters = get_global_filters()
filtered_data = filters.apply_filters_to_data(data)

# ❌ Bad: Direct data fetching without caching
data = expensive_data_fetch()  # Will slow down dashboard
```

### Error Handling

```python
# ✅ Good: Graceful error handling
try:
    render_model_performance_overview()
except Exception as e:
    st.error(f"Unable to load model metrics: {e}")
    st.info("Please refresh the page or contact support.")
```

### Performance

```python
# ✅ Good: Use appropriate cache TTL
@st.cache_data(ttl=300)  # 5 minutes for stable data
def get_historical_metrics():
    return fetch_historical_data()

@st.cache_data(ttl=60)   # 1 minute for real-time data
def get_current_metrics():
    return fetch_current_data()
```

## 🛠️ Troubleshooting

### Common Issues

**Dashboard Not Loading**
```bash
# Check dependencies
pip install -r requirements.txt

# Verify Streamlit installation
streamlit version

# Check Python path
python -c "import command_center.components; print('OK')"
```

**Authentication Errors**
```python
# Verify auth service is running
try:
    from ghl_real_estate_ai.services.auth_service import get_auth_service
    auth_service = get_auth_service()
    print("Auth service available")
except ImportError:
    print("Running in demo mode - auth unavailable")
```

**Performance Issues**
```python
# Clear Streamlit cache
st.cache_data.clear()
st.cache_resource.clear()

# Check data source connectivity
import requests
response = requests.get("http://your-ml-api/health")
print(f"API Status: {response.status_code}")
```

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>

# Install development dependencies
pip install -r requirements-dev.txt

# Run pre-commit hooks
pre-commit install

# Start development server
streamlit run command_center/ml_dashboard_integration_demo.py
```

### Code Style

- Follow Jorge's coding standards with comprehensive error handling
- Use type hints for all function parameters and return values
- Include docstrings for all public functions
- Maintain 80% test coverage

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes following Jorge's patterns
3. Add tests for new functionality
4. Update documentation
5. Submit PR with detailed description

## 📞 Support

- **Documentation:** [GitHub Wiki](https://github.com/jorge-real-estate-ai/wiki)
- **Bug Reports:** [GitHub Issues](https://github.com/jorge-real-estate-ai/issues)
- **Feature Requests:** [GitHub Discussions](https://github.com/jorge-real-estate-ai/discussions)

---

**Built with ❤️ by Jorge's AI Assistant**
*Version 1.0.0 • January 2026 • ML Intelligence Platform*