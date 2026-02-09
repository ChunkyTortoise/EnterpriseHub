# Data Intelligence Dashboard — $39

## Tagline
**Upload data → Get dashboards, predictions, and PDF reports in 30 seconds**

## Description

The Data Intelligence Dashboard is a complete business intelligence toolkit that transforms raw data into actionable insights without requiring machine learning expertise. Upload a CSV or Excel file, and the system automatically generates a profiler report, runs 4 marketing attribution models, builds predictive models with SHAP explanations, and creates stunning visualizations—all in under 30 seconds.

Built for data analysts, marketers, and business intelligence professionals, this toolkit includes automated data profiling, marketing mix modeling, churn prediction, clustering analysis, time series forecasting, anomaly detection, and automated data cleaning. Every analysis includes exportable PDF reports for stakeholder presentations.

The dashboard generator creates interactive Streamlit apps from your data instantly, while the feature engineering engine automatically creates derived variables to boost model performance.

**Perfect for**: Marketing analysts, data scientists, business intelligence teams, founders validating data, and anyone needing quick insights from raw datasets.

---

## Key Features

- **30-Second Dashboard**: Upload → profile → visualize in under 30 seconds
- **Auto-Profiler**: Automatic data quality assessment, distribution analysis, and anomaly detection
- **4 Marketing Attribution Models**: First-touch, Last-touch, Linear, and Time-decay attribution
- **Predictive Modeling with SHAP**: Build models with explainable predictions and feature importance
- **Clustering Analysis**: K-means and hierarchical clustering for customer segmentation
- **Time Series Forecasting**: ARIMA and Prophet-style forecasting with confidence intervals
- **Anomaly Detection**: Statistical and ML-based outlier detection
- **Data Cleaning**: Missing value imputation, outlier handling, duplicate detection
- **Feature Engineering**: Automated derived variable creation
- **PDF Export**: Professional reports for stakeholder presentations
- **Interactive Dashboards**: Plotly-powered visualizations with filtering and drill-down

---

## Tech Stack

- **Language**: Python 3.11+
- **UI Framework**: Streamlit
- **Visualization**: Plotly
- **Machine Learning**: scikit-learn, XGBoost
- **Explainability**: SHAP
- **Data Processing**: Pandas, NumPy
- **PDF Generation**: ReportLab, FPDF
- **Statistical Analysis**: SciPy, Statsmodels

---

## Differentiators

| Aspect | This Engine | Typical Solutions |
|--------|-------------|-------------------|
| **Time to Insight** | ~30 seconds | Hours to days |
| **No Code Required** | Full GUI | CLI or notebooks |
| **SHAP Explanations** | Built-in | Often missing |
| **Attribution Models** | 4 included | Add-on costs |
| **PDF Reports** | Auto-generated | Manual creation |
| **ML Expertise** | Zero required | PhD-level needed |
| **Self-Hosted** | 100% | Cloud lock-in |

---

## What's Included in Your ZIP

```
insight-engine/
├── README.md                    # Getting started guide
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container deployment
├── docker-compose.yml           # Local development stack
├── config/
│   └── settings.yaml           # Dashboard settings
├── src/
│   ├── core/
│   │   ├── dashboard.py        # Main dashboard generator
│   │   ├── pipeline.py        # Analysis pipeline
│   │   └── config.py          # Configuration loader
│   ├── profiler/
│   │   ├── auto_profiler.py   # Automatic data profiling
│   │   ├── quality.py         # Data quality assessment
│   │   ├── distributions.py   # Distribution analysis
│   │   └── correlations.py    # Correlation analysis
│   ├── attribution/
│   │   ├── models.py          # 4 attribution model implementations
│   │   ├── first_touch.py     # First-touch attribution
│   │   ├── last_touch.py      # Last-touch attribution
│   │   ├── linear.py          # Linear attribution
│   │   └── time_decay.py     # Time-decay attribution
│   ├── predictive/
│   │   ├── models.py         # Predictive model builder
│   │   ├── classifier.py     # Classification models
│   │   ├── regressor.py      # Regression models
│   │   └── explainer.py      # SHAP explanations
│   ├── clustering/
│   │   ├── kmeans.py         # K-means clustering
│   │   └── hierarchical.py   # Hierarchical clustering
│   ├── forecasting/
│   │   ├── time_series.py    # Time series forecasting
│   │   └── arima.py          # ARIMA implementation
│   ├── anomaly/
│   │   ├── detector.py       # Anomaly detection
│   │   └── statistical.py   # Statistical methods
│   ├── cleaning/
│   │   ├── imputer.py        # Missing value handling
│   │   ├── outlier.py        # Outlier detection
│   │   └── deduplicator.py   # Duplicate detection
│   ├── engineering/
│   │   ├── features.py       # Feature engineering
│   │   └── transformer.py    # Custom transformers
│   └── reporting/
│       ├── pdf.py            # PDF report generation
│       └── exporter.py       # Data export utilities
├── ui/
│   ├── app.py                # Main Streamlit application
│   ├── pages/
│   │   ├── upload.py        # Data upload page
│   │   ├── profile.py       # Data profiler page
│   │   ├── visualize.py     # Visualization page
│   │   ├── attribution.py   # Marketing attribution page
│   │   ├── predict.py       # Predictive modeling page
│   │   ├── cluster.py       # Clustering page
│   │   ├── forecast.py      # Time series forecasting
│   │   ├── clean.py         # Data cleaning page
│   │   └── report.py        # PDF report page
│   └── components/
│       ├── data_uploader.py  # File upload component
│       ├── profile_view.py   # Profiler display
│       ├── chart_builder.py  # Plotly chart builder
│       ├── model_viewer.py   # Model explanation viewer
│       └── filter_panel.py   # Data filtering
├── templates/
│   └── report_template.md   # PDF report template
├── tests/
│   ├── test_profiler.py     # Profiler tests
│   ├── test_attribution.py  # Attribution tests
│   ├── test_predictive.py   # Predictive modeling tests
│   └── test_cleaning.py     # Data cleaning tests
├── CUSTOMIZATION.md         # Advanced customization guide
├── API_REFERENCE.md         # Programmatic API documentation
├── ATTRIBUTION_GUIDE.md     # Marketing attribution methodology
└── ARCHITECTURE.md          # System architecture overview
```

---

## Suggested Thumbnail Screenshot

**Primary**: Screenshot of the main dashboard showing data upload, profiling summary, and key visualizations

**Secondary options**:
- SHAP feature importance explanation for a prediction model
- Marketing attribution model comparison chart
- PDF report preview showing professional output

---

## Tags for Discoverability

`data-dashboard`, `business-intelligence`, `bi-tool`, `data-analysis`, `machine-learning`, `shap`, `explainable-ai`, `marketing-attribution`, `predictive-analytics`, `clustering`, `time-series-forecasting`, `anomaly-detection`, `data-cleaning`, `feature-engineering`, `streamlit`, `plotly`, `sklearn`, `xgboost`, `python`, `self-hosted`

---

## Marketing Attribution Models

| Model | Best For | How It Works |
|-------|----------|--------------|
| **First-Touch** | Awareness campaigns | 100% credit to first interaction |
| **Last-Touch** | Conversion-focused | 100% credit to last interaction |
| **Linear** | Equal journey importance | Equal credit across all touchpoints |
| **Time-Decay** | Short sales cycles | More credit to recent interactions |

---

## What's Included in PDF Reports

1. **Executive Summary**: Key findings and recommendations
2. **Data Profile**: Quality metrics, distributions, correlations
3. **Visualizations**: Charts and graphs from analysis
4. **Model Results**: Predictions and explanations (if applicable)
5. **Methodology**: Statistical methods and assumptions
6. **Recommendations**: Actionable insights based on analysis

---

## Related Products (Upsell)

| Product | Price | Rationale |
|---------|-------|-----------|
| [AI Document Q&A Engine](/products/product1-docqa-engine.md) | $49 | Turn reports into Q&A systems |
| [AgentForge — Multi-LLM Orchestrator](/products/product2-agentforge.md) | $39 | Generate narratives from dashboard insights |
| [Web Scraper & Price Monitor Toolkit](/products/product3-scrape-and-serve.md) | $29 | Scrape market data → analyze in dashboard |

---

## Live Demo

**Try before you buy**: [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)

---

## Quick Start Example

```python
from insight_engine import InsightDashboard
import pandas as pd

# Load your data
df = pd.read_csv("sales_data.csv")

# Create dashboard
dashboard = InsightDashboard(df)

# Run full analysis pipeline
results = dashboard.run_pipeline(
    include_profiling=True,
    include_attribution=True,
    include_prediction=True,
    include_forecasting=True
)

# Export PDF report
dashboard.generate_pdf_report("analysis_report.pdf")
```

```bash
# Or use the UI
streamlit run ui/app.py
```

---

## Supported Data Formats

| Format | Read Support | Write Support |
|--------|-------------|---------------|
| CSV | ✅ Full | ✅ Full |
| Excel (.xlsx) | ✅ Full | ✅ Full |
| JSON | ✅ Full | ✅ Full |
| Parquet | ✅ Full | ✅ Full |
| SQL (via SQLAlchemy) | ✅ Full | ✅ Full |

---

## Support

- Documentation: See `README.md` and `CUSTOMIZATION.md` in your ZIP
- Tutorials: `/examples` directory with sample datasets and analyses
- Issues: Create an issue on the GitHub repository
- Email: caymanroden@gmail.com

---

**License**: MIT License — Use in unlimited projects

**Refund Policy**: 30-day money-back guarantee if the product doesn't meet your requirements