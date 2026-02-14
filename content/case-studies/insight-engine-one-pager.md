# Insight Engine — Automated Analytics Platform Case Study

## The Challenge

A business analytics team needed to convert raw CSV/Excel data into actionable dashboards without manual data wrangling, SQL queries, or Python scripting. Their existing workflow required 2-3 hours per dataset for profiling, cleaning, and visualization setup. They needed predictive modeling with explainable AI (SHAP), marketing attribution analysis, and automated PDF report generation for stakeholder distribution. The solution had to handle datasets up to 1M rows with sub-minute processing times.

## The Solution

Built an upload-to-dashboard pipeline with automatic data profiling (data types, missing values, outliers, distributions), one-click cleaning (imputation, encoding, scaling), and interactive Plotly visualizations. Implemented XGBoost regression/classification with SHAP explanations for feature importance, statistical testing (t-tests, ANOVA, chi-square), and KPI framework for defining custom business metrics. Included dimensionality reduction (PCA, t-SNE) for high-dimensional data, advanced anomaly detection (Isolation Forest, Local Outlier Factor), and automated PDF report generation with Matplotlib/Seaborn charts.

## Key Results

- **640+ automated tests** — Unit, integration, E2E with CI/CD on every commit
- **Instant dashboards** — Upload CSV → profiling → visualizations in <30 seconds (10K row dataset)
- **XGBoost predictions** — Built-in regression/classification with SHAP explanations for model transparency
- **PDF report generation** — Automated executive summaries with charts, tables, statistical tests
- **Marketing attribution** — Multi-touch attribution modeling for campaign ROI analysis

## Tech Stack

**Backend**: Python 3.11, FastAPI (async), Pydantic validation
**Data Processing**: pandas, NumPy, scikit-learn (preprocessing, feature engineering)
**ML Models**: XGBoost, Isolation Forest, Local Outlier Factor, PCA, t-SNE
**Explainability**: SHAP (SHapley Additive exPlanations) for feature importance
**Visualization**: Plotly (interactive), Matplotlib/Seaborn (static PDF charts), Streamlit UI
**Statistical Testing**: SciPy (t-tests, ANOVA, chi-square, correlation analysis)
**Database**: SQLite (embedded), SQLAlchemy ORM, Alembic migrations
**Deployment**: Docker Compose, GitHub Actions CI

## Timeline & Scope

**Duration**: 7 weeks (solo developer)
**Approach**: TDD with data quality testing, feature branches with PR reviews
**Testing**: 640+ tests including data quality validation, regression diagnostics, anomaly detection accuracy
**Features**: KPI framework, dimensionality reduction, advanced anomaly detection, regression diagnostics
**Benchmarks**: 1 script (ETL throughput, model training latency) with RESULTS.md
**Governance**: 3 ADRs (XGBoost selection, SHAP integration, PDF rendering), SECURITY.md, CHANGELOG.md

---

**Want similar results?** [Schedule a free 15-minute call](mailto:caymanroden@gmail.com) | [View live demo](https://github.com/chunkytortoise/insight-engine) | [GitHub Repo](https://github.com/chunkytortoise/insight-engine)
