# Jorge's Chart Builders Utility v2.0

Advanced chart factory with ML-specific visualizations, real estate analytics, and interactive dashboard widgets. Features standardized Jorge theme integration, performance optimization, and comprehensive accessibility support.

## 🎯 Key Features

### 📊 **Plotly Chart Factory**
- Standardized Jorge theme with consistent branding
- Support for light/dark themes
- Color-blind friendly palettes
- Responsive design for desktop/mobile

### 🤖 **ML-Specific Visualizations**
- **ROC Curves**: Single and multi-model comparison with AUC scores
- **Precision-Recall Curves**: Model performance analysis with average precision
- **Confusion Matrices**: Interactive heatmaps with detailed hover information
- **Feature Importance**: Ranked visualization with model attribution

### 🏠 **Real Estate Analytics Charts**
- **Lead Score Distribution**: Multi-dimensional analysis with conversion insights
- **Conversion Funnels**: Pipeline visualization with stage-by-stage metrics
- **Market Trends**: Multi-metric analysis with seasonal patterns
- **Attribution Analysis**: Source performance with ROI analysis

### 📈 **Interactive Dashboard Widgets**
- **KPI Cards**: Real-time metrics with trend indicators
- **Real-time Metrics**: Live updating charts with trend analysis
- **Forecasting**: Predictive charts with confidence intervals
- **Performance Tracking**: Historical analysis with pattern recognition

## 🚀 Quick Start

### Basic Usage

```python
from command_center.utils.chart_builders import ChartFactory

# Initialize factory
factory = ChartFactory(dark_mode=False, colorblind_friendly=False)

# Create KPI card
kpi_fig = factory.create_chart(
    'kpi_card',
    "Monthly Revenue",
    value=125000,
    change=0.15,
    format_type="currency"
)

# Create ROC curve
roc_fig = factory.create_chart(
    'roc_curve',
    y_true,
    y_scores=y_scores,
    model_names=["Model v1.0"]
)

# Create lead analysis
lead_fig = factory.create_chart('lead_score_distribution', lead_data)
```

### Quick Functions

```python
from command_center.utils.chart_builders import (
    quick_roc_curve,
    quick_lead_analysis,
    quick_kpi_card
)

# Rapid chart creation
roc_chart = quick_roc_curve(y_true, y_scores)
lead_chart = quick_lead_analysis(lead_dataframe)
kpi_chart = quick_kpi_card("Revenue", 125000)
```

## 📚 Available Chart Types

### ML Performance Charts
- `roc_curve`: ROC curve analysis with AUC scores
- `precision_recall`: Precision-recall curve with average precision
- `confusion_matrix`: Interactive confusion matrix heatmap
- `feature_importance`: Ranked feature importance visualization

### Real Estate Analytics
- `lead_score_distribution`: Multi-dimensional lead analysis
- `conversion_funnel`: Pipeline visualization
- `market_trends`: Market analysis dashboard
- `attribution_analysis`: Source performance analysis

### Dashboard Widgets
- `kpi_card`: Real-time metric cards
- `real_time_metric`: Live updating metrics
- `forecast_chart`: Predictive analytics with confidence bands

## 🎨 Theme Configuration

### Jorge Theme Colors

```python
theme = JorgeTheme()

# Primary Colors
theme.primary_blue = "#1E3A8A"     # Deep professional blue
theme.primary_gold = "#F59E0B"     # Luxury gold accent
theme.primary_green = "#059669"    # Success/profit green
theme.primary_red = "#DC2626"      # Alert/loss red

# Semantic Colors
theme.success = "#10B981"          # Positive metrics
theme.warning = "#F59E0B"          # Attention needed
theme.danger = "#EF4444"           # Critical issues
theme.info = "#3B82F6"             # Information
```

### Theme Options

```python
# Standard theme
factory = ChartFactory()

# Dark mode
factory = ChartFactory(dark_mode=True)

# Color-blind friendly
factory = ChartFactory(colorblind_friendly=True)

# Combined options
factory = ChartFactory(dark_mode=True, colorblind_friendly=True)
```

## 📊 Detailed Examples

### ML Performance Analysis

```python
import numpy as np
from sklearn.metrics import roc_curve
from command_center.utils.chart_builders import MLPerformanceCharts

# Initialize ML charts
ml_charts = MLPerformanceCharts()

# Sample data
y_true = np.random.choice([0, 1], size=1000, p=[0.7, 0.3])
y_scores = np.random.beta(2, 5, size=1000)

# Create ROC curve
roc_fig = ml_charts.create_roc_curve(
    y_true, 
    y_scores,
    model_names=["Lead Scoring Model v2.1"]
)

# Feature importance
feature_names = ['Income', 'Credit_Score', 'Property_Value']
importance_scores = np.array([0.4, 0.35, 0.25])

feature_fig = ml_charts.create_feature_importance(
    feature_names,
    importance_scores,
    model_name="Lead Scoring Model"
)
```

### Real Estate Analytics

```python
import pandas as pd
from command_center.utils.chart_builders import RealEstateAnalyticsCharts

# Initialize real estate charts
re_charts = RealEstateAnalyticsCharts()

# Lead score analysis
lead_data = pd.DataFrame({
    'score': np.random.beta(2, 5, size=500) * 100,
    'converted': np.random.choice([0, 1], size=500, p=[0.8, 0.2]),
    'source': np.random.choice(['Website', 'Social', 'Referral'], size=500),
    'date': pd.date_range('2024-01-01', periods=500, freq='D')[:500]
})

lead_fig = re_charts.create_lead_score_distribution(lead_data)

# Conversion funnel
funnel_data = pd.DataFrame({
    'stage': ['Awareness', 'Interest', 'Consideration', 'Purchase'],
    'count': [1000, 400, 150, 50]
})

funnel_fig = re_charts.create_conversion_funnel(funnel_data)

# Market trends
market_data = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=24, freq='M'),
    'avg_price': np.random.normal(450000, 50000, size=24),
    'active_listings': np.random.poisson(500, size=24),
    'avg_dom': np.random.normal(30, 10, size=24)
})

market_fig = re_charts.create_market_trends(market_data)
```

### Interactive Dashboard Widgets

```python
from command_center.utils.chart_builders import InteractiveDashboardWidgets

# Initialize widgets
widgets = InteractiveDashboardWidgets()

# KPI card with trend
kpi_fig = widgets.create_kpi_card(
    title="Monthly Revenue",
    value=125000,
    change=0.15,  # 15% increase
    format_type="currency"
)

# Real-time metric
time_series_data = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=30, freq='D'),
    'revenue': np.random.exponential(scale=8000, size=30)
})

realtime_fig = widgets.create_real_time_metric(
    time_series_data,
    metric_column='revenue'
)

# Forecast chart
historical_data = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=30, freq='D'),
    'revenue': np.random.exponential(scale=8000, size=30)
})

forecast_data = pd.DataFrame({
    'date': pd.date_range('2024-02-01', periods=30, freq='D'),
    'revenue': np.random.exponential(scale=8500, size=30),
    'upper_bound': np.random.exponential(scale=9500, size=30),
    'lower_bound': np.random.exponential(scale=7500, size=30)
})

forecast_fig = widgets.create_forecast_chart(
    historical_data,
    forecast_data,
    value_column='revenue'
)
```

## 📤 Export Functionality

### Single Chart Export

```python
# Export single chart
fig = factory.create_chart('kpi_card', "Revenue", value=125000)

# Export options
factory.ml_charts.export_chart(fig, "revenue_kpi", "png")      # PNG image
factory.ml_charts.export_chart(fig, "revenue_kpi", "html")     # Interactive HTML
factory.ml_charts.export_chart(fig, "revenue_kpi", "pdf")      # PDF document
factory.ml_charts.export_chart(fig, "revenue_kpi", "svg")      # SVG vector
```

### Batch Export

```python
# Create multiple charts
charts = {
    'revenue_kpi': factory.create_chart('kpi_card', "Revenue", value=125000),
    'lead_analysis': factory.create_chart('lead_score_distribution', lead_data),
    'roc_curve': factory.create_chart('roc_curve', y_true, y_scores=y_scores)
}

# Batch export
exported_files = factory.batch_export(
    charts,
    base_path="./reports",
    formats=["png", "html"]
)

# Returns:
# {
#     'revenue_kpi': ['./reports/revenue_kpi.png', './reports/revenue_kpi.html'],
#     'lead_analysis': ['./reports/lead_analysis.png', './reports/lead_analysis.html'],
#     'roc_curve': ['./reports/roc_curve.png', './reports/roc_curve.html']
# }
```

## 🔧 Advanced Configuration

### Custom Theme Integration

```python
from command_center.utils.chart_builders import JorgeTheme

# Customize theme
theme = JorgeTheme()
theme.primary_blue = "#2563EB"  # Custom blue
theme.categorical_palette = ["#2563EB", "#F59E0B", "#10B981"]  # Custom palette

# Use custom theme
factory = ChartFactory()
factory.theme = theme
```

### Error Handling

```python
try:
    fig = factory.create_chart('roc_curve', y_true, y_scores=y_scores)
except ValueError as e:
    print(f"Chart creation error: {e}")
    # Factory returns error chart automatically for display
    error_fig = factory._create_error_chart(str(e))
```

### Performance Optimization

```python
# For large datasets, consider data sampling
if len(data) > 10000:
    sampled_data = data.sample(n=5000)
    fig = factory.create_chart('lead_score_distribution', sampled_data)
```

## 🎯 Integration with Jorge Dashboard

### Streamlit Integration

```python
import streamlit as st
from command_center.utils.chart_builders import ChartFactory

# Initialize factory
factory = ChartFactory(dark_mode=st.sidebar.checkbox("Dark Mode"))

# Create charts
kpi_fig = factory.create_chart('kpi_card', "Revenue", value=125000)

# Display in Streamlit
st.plotly_chart(kpi_fig, use_container_width=True)
```

### FastAPI Integration

```python
from fastapi import FastAPI
from command_center.utils.chart_builders import ChartFactory
import json

app = FastAPI()
factory = ChartFactory()

@app.get("/api/charts/kpi/{metric_name}")
async def get_kpi_chart(metric_name: str, value: float):
    fig = factory.create_chart('kpi_card', metric_name, value=value)
    return json.loads(fig.to_json())
```

## 🧪 Testing

### Run Tests

```bash
# Run all chart builder tests
pytest tests/command_center/test_chart_builders.py -v

# Run specific test class
pytest tests/command_center/test_chart_builders.py::TestMLPerformanceCharts -v

# Run with coverage
pytest tests/command_center/test_chart_builders.py --cov=command_center.utils.chart_builders
```

### Test Categories

- **Unit Tests**: Individual chart type creation
- **Integration Tests**: Chart factory functionality
- **Theme Tests**: Theme application and consistency
- **Export Tests**: Chart export functionality
- **Accessibility Tests**: Color-blind friendly features
- **Performance Tests**: Large dataset handling

## 📋 Data Format Requirements

### ML Performance Data

```python
# ROC/Precision-Recall curves
y_true: np.ndarray        # Binary labels (0, 1)
y_scores: np.ndarray      # Prediction scores (0.0 - 1.0)

# Confusion Matrix
y_true: np.ndarray        # True labels
y_pred: np.ndarray        # Predicted labels

# Feature Importance
feature_names: List[str]  # Feature names
importance_scores: np.ndarray  # Importance values
```

### Real Estate Analytics Data

```python
# Lead Score Distribution
lead_data: pd.DataFrame with columns:
- 'score': float         # Lead score (0-100)
- 'converted': int       # Binary conversion (0, 1)
- 'source': str          # Lead source
- 'date': datetime       # Lead date
- 'value': float         # Estimated deal value (optional)

# Market Trends
market_data: pd.DataFrame with columns:
- 'date': datetime       # Date
- 'avg_price': float     # Average property price
- 'active_listings': int # Number of active listings
- 'avg_dom': float       # Average days on market
- 'sales_volume': int    # Sales volume (optional)
- 'new_listings': int    # New listings (optional)

# Conversion Funnel
funnel_data: pd.DataFrame with columns:
- 'stage': str          # Funnel stage name
- 'count': int          # Count at stage

# Attribution Analysis
attribution_data: pd.DataFrame with columns:
- 'source': str         # Source name
- 'count': int          # Lead count
- 'conversion_rate': float  # Conversion rate (0.0 - 1.0)
```

### Interactive Widgets Data

```python
# Real-time Metrics
time_series_data: pd.DataFrame with columns:
- 'timestamp': datetime  # Time stamps
- '{metric_column}': float  # Metric values

# Forecasting
historical_data: pd.DataFrame with columns:
- 'date': datetime      # Historical dates
- '{value_column}': float  # Historical values

forecast_data: pd.DataFrame with columns:
- 'date': datetime      # Forecast dates
- '{value_column}': float  # Forecast values
- 'upper_bound': float  # Upper confidence bound (optional)
- 'lower_bound': float  # Lower confidence bound (optional)
```

## 🔄 Version History

### v2.0.0 (Current)
- ✅ Complete Jorge theme integration
- ✅ ML performance chart suite
- ✅ Real estate analytics charts
- ✅ Interactive dashboard widgets
- ✅ Export functionality
- ✅ Accessibility features
- ✅ Comprehensive test suite
- ✅ Dark mode support
- ✅ Color-blind friendly palettes

### Planned v2.1.0
- 🔄 Advanced animations and transitions
- 🔄 Custom chart templates
- 🔄 Real-time data streaming support
- 🔄 Advanced statistical overlays
- 🔄 Mobile-first responsive design
- 🔄 Chart composition tools

## 📞 Support & Contributing

### Issues & Questions
- 📧 Email: dev-team@jorge-real-estate-ai.com
- 🐛 Issues: Create GitHub issue in EnterpriseHub repository
- 💬 Discussions: Use GitHub Discussions for feature requests

### Contributing Guidelines
1. Follow existing code style and patterns
2. Add comprehensive tests for new features
3. Update documentation and examples
4. Ensure accessibility compliance
5. Test with both light/dark themes and colorblind settings

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install additional dev dependencies
pip install pytest pytest-cov plotly pandas numpy sklearn

# Run tests
pytest tests/command_center/test_chart_builders.py

# Run demo
streamlit run command_center/examples/chart_builders_demo.py
```

---

**Jorge's Chart Builders v2.0** | Advanced Real Estate AI Visualization Platform