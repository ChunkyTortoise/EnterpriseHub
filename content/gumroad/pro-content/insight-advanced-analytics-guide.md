# Insight Engine Advanced Analytics Guide

## Cohort Analysis, RFM Segmentation, LTV Modeling, and A/B Testing

This guide covers advanced analytics techniques using Insight Engine's modules. Based on the actual codebase (520+ tests, 19 test files) with real configuration examples and API patterns.

---

## Table of Contents

1. [Cohort Analysis with Clustering](#1-cohort-analysis-with-clustering)
2. [RFM Customer Segmentation](#2-rfm-customer-segmentation)
3. [Customer Lifetime Value (LTV) Modeling](#3-customer-lifetime-value-ltv-modeling)
4. [A/B Testing with Statistical Rigor](#4-ab-testing-with-statistical-rigor)
5. [Marketing Attribution Deep Dive](#5-marketing-attribution-deep-dive)
6. [Time Series Forecasting](#6-time-series-forecasting)
7. [Anomaly Detection Patterns](#7-anomaly-detection-patterns)
8. [Feature Engineering](#8-feature-engineering)
9. [Dimensionality Reduction](#9-dimensionality-reduction)
10. [Production Analytics Pipeline](#10-production-analytics-pipeline)

---

## 1. Cohort Analysis with Clustering

### Building Customer Cohorts

Use Insight Engine's clustering module to create behavioral cohorts, then track metrics across cohorts over time.

```python
from insight_engine.clustering import cluster_kmeans, elbow_method
from insight_engine.profiler import profile_dataframe
import pandas as pd
import numpy as np

# Prepare cohort features
customers = pd.read_csv("customers.csv")

# Step 1: Profile to understand distributions
profile = profile_dataframe(customers)
for col in profile.columns:
    if col.outlier_count > 0:
        print(f"WARNING: {col.name} has {col.outlier_count} outliers")

# Step 2: Find optimal cluster count with elbow method
features = ["total_orders", "avg_order_value", "days_since_last_order",
            "total_spend", "support_tickets"]

elbow = elbow_method(customers[features], k_range=range(2, 10))
print(f"Suggested K: {elbow.suggested_k}")
print(f"Inertias: {elbow.inertias}")  # Plot this for visual confirmation

# Step 3: Create cohorts
result = cluster_kmeans(
    customers[features],
    n_clusters=elbow.suggested_k,
    scale=True
)

customers["cohort"] = result.labels
print(f"Silhouette score: {result.silhouette:.3f}")
print(f"Cluster sizes: {result.cluster_sizes}")
```

### Cohort Retention Tracking

```python
# Track monthly retention by cohort
def cohort_retention(customers, orders):
    """Calculate monthly retention rates by customer cohort."""
    cohort_metrics = {}

    for cohort_id in customers["cohort"].unique():
        cohort_customers = customers[customers["cohort"] == cohort_id]["customer_id"]
        cohort_orders = orders[orders["customer_id"].isin(cohort_customers)]

        # Monthly active rate
        monthly_active = cohort_orders.groupby(
            cohort_orders["order_date"].dt.to_period("M")
        )["customer_id"].nunique()

        retention = monthly_active / len(cohort_customers) * 100
        cohort_metrics[cohort_id] = retention

    return cohort_metrics
```

### Comparing Cohort Quality

```python
from insight_engine.clustering import compare_methods, ClusterEvaluation

# Compare K-means at different K values
comparison = compare_methods(
    customers[features],
    k_values=[3, 4, 5, 6, 7]
)

print(f"Best method: {comparison.best_method}")
print(f"Best silhouette: {comparison.best_silhouette:.3f}")

for name, result in comparison.results.items():
    print(f"{name}: silhouette={result.silhouette:.3f}, clusters={result.n_clusters}")
```

---

## 2. RFM Customer Segmentation

RFM (Recency, Frequency, Monetary) segmentation using Insight Engine's profiler and clustering.

### Computing RFM Scores

```python
from insight_engine.profiler import profile_dataframe
from insight_engine.clustering import cluster_kmeans
import pandas as pd
from datetime import datetime

def compute_rfm(orders: pd.DataFrame, reference_date: datetime = None) -> pd.DataFrame:
    """Compute RFM scores from order data."""
    if reference_date is None:
        reference_date = orders["order_date"].max()

    rfm = orders.groupby("customer_id").agg({
        "order_date": lambda x: (reference_date - x.max()).days,  # Recency
        "order_id": "count",                                       # Frequency
        "order_value": "sum"                                       # Monetary
    }).rename(columns={
        "order_date": "recency",
        "order_id": "frequency",
        "order_value": "monetary"
    })

    return rfm

# Compute RFM
rfm = compute_rfm(orders)

# Profile RFM distributions
profile = profile_dataframe(rfm)
for col in profile.columns:
    print(f"{col.name}: mean={col.mean:.1f}, median={col.median:.1f}, "
          f"std={col.std:.1f}, outliers={col.outlier_count}")
```

### RFM Clustering

```python
# Cluster customers by RFM scores
rfm_result = cluster_kmeans(
    rfm[["recency", "frequency", "monetary"]],
    n_clusters=5,
    scale=True  # StandardScaler normalizes different scales
)

rfm["segment"] = rfm_result.labels

# Label segments based on cluster characteristics
segment_profiles = rfm.groupby("segment").agg({
    "recency": "mean",
    "frequency": "mean",
    "monetary": "mean"
}).round(1)

print(segment_profiles)
# Typical output:
# segment | recency | frequency | monetary
#       0 |    15.2 |      12.3 |   2,450  (Champions)
#       1 |    45.8 |       6.1 |     890  (Loyal)
#       2 |    90.3 |       2.5 |     320  (Promising)
#       3 |   180.5 |       1.8 |     180  (At Risk)
#       4 |   365.2 |       1.1 |      75  (Dormant)
```

### Actionable RFM Strategies

| Segment | Recency | Frequency | Monetary | Strategy |
|---------|---------|-----------|----------|----------|
| Champions | Low | High | High | Loyalty rewards, early access, referral program |
| Loyal | Low-Mid | Mid-High | Mid-High | Upsell, cross-sell, VIP events |
| Promising | Low | Low | Mid | Second purchase incentive, onboarding email |
| At Risk | High | Mid | Mid | Win-back campaign, satisfaction survey |
| Dormant | Very High | Low | Low | Re-engagement offer or sunset |

---

## 3. Customer Lifetime Value (LTV) Modeling

### Historical LTV Calculation

```python
from insight_engine.predictor import Predictor
from insight_engine.model_observatory import ModelObservatory

def calculate_historical_ltv(orders, customers, months=24):
    """Calculate actual LTV over a fixed window."""
    ltv = orders.groupby("customer_id").agg({
        "order_value": "sum",
        "order_id": "count",
        "order_date": ["min", "max"]
    })
    ltv.columns = ["total_revenue", "total_orders", "first_order", "last_order"]
    ltv["customer_lifetime_days"] = (ltv["last_order"] - ltv["first_order"]).dt.days
    ltv["avg_order_value"] = ltv["total_revenue"] / ltv["total_orders"]
    ltv["monthly_revenue"] = ltv["total_revenue"] / (ltv["customer_lifetime_days"] / 30).clip(lower=1)

    return ltv
```

### Predictive LTV Model

```python
# Build predictive LTV model
predictor = Predictor()

ltv_data = calculate_historical_ltv(orders, customers)
customer_features = customers.merge(ltv_data, on="customer_id")

result = predictor.fit(
    df=customer_features,
    target_column="total_revenue",  # Regression target
    feature_columns=[
        "acquisition_channel", "first_order_value", "days_to_second_order",
        "product_category_first", "discount_on_first_order", "industry"
    ]
)

print(f"Model: {result.algorithm}")
print(f"R-squared: {result.r_squared:.3f}")
print(f"MAE: ${result.mae:,.0f}")

# SHAP explanations for LTV drivers
observatory = ModelObservatory()
explanations = observatory.explain(result.model, customer_features)

print("\nLTV Drivers (SHAP importance):")
for feature, importance in result.shap_importances.items():
    print(f"  {feature}: {importance:.3f}")
```

### LTV-Based Customer Segmentation

```python
# Segment customers by predicted LTV
predictions = predictor.predict(new_customers)
new_customers["predicted_ltv"] = predictions

# Tier customers
new_customers["ltv_tier"] = pd.cut(
    new_customers["predicted_ltv"],
    bins=[0, 100, 500, 2000, float("inf")],
    labels=["Low", "Medium", "High", "Enterprise"]
)

# Allocate acquisition budget proportional to predicted LTV
tier_summary = new_customers.groupby("ltv_tier").agg({
    "predicted_ltv": ["mean", "count"],
    "acquisition_cost": "mean"
}).round(2)
print(tier_summary)
```

---

## 4. A/B Testing with Statistical Rigor

### Complete A/B Test Workflow

```python
from insight_engine.statistical_tests import run_test

# Step 1: Define hypothesis
# H0: New checkout flow has no effect on conversion rate
# H1: New checkout flow improves conversion rate

control = [1, 0, 1, 0, 0, 1, 0, 1, 1, 0]     # 50% conversion
treatment = [1, 1, 1, 0, 1, 1, 0, 1, 1, 1]     # 80% conversion

# Step 2: Run appropriate test (auto-selected)
result = run_test(
    group_a=control,
    group_b=treatment,
    test_type="auto"  # Checks normality first, then selects test
)

print(f"Test selected: {result.test_name}")
print(f"Statistic: {result.statistic:.4f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant at alpha=0.05: {result.significant}")
print(f"Effect size: {result.effect_size:.3f}")
```

### Choosing the Right Test

Insight Engine auto-selects, but here is when each test is appropriate:

| Test | When to Use | Example |
|------|-------------|---------|
| **t-test** | Comparing means, normal data | Average order values |
| **Mann-Whitney U** | Comparing medians, non-normal | Session durations |
| **Chi-square** | Comparing proportions | Conversion rates |
| **ANOVA** | Comparing 3+ group means | Multi-variant landing pages |
| **Kruskal-Wallis** | Non-parametric ANOVA | Revenue across 4 segments |
| **Shapiro-Wilk** | Testing normality | Pre-test data validation |

### Multiple Comparison Correction

When running multiple tests (e.g., testing 5 metrics), apply Bonferroni correction:

```python
# Run tests on multiple metrics
metrics = ["conversion_rate", "avg_order_value", "bounce_rate", "time_on_page"]
alpha = 0.05
corrected_alpha = alpha / len(metrics)  # Bonferroni: 0.05/4 = 0.0125

for metric in metrics:
    result = run_test(control_data[metric], treatment_data[metric])
    significant = result.p_value < corrected_alpha
    print(f"{metric}: p={result.p_value:.4f}, significant={significant} "
          f"(alpha={corrected_alpha:.4f})")
```

### Sample Size Planning

```python
def required_sample_size(
    baseline_rate: float,
    minimum_effect: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """Calculate required sample size per group for A/B test."""
    from scipy import stats

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(power)

    p1 = baseline_rate
    p2 = baseline_rate + minimum_effect
    p_avg = (p1 + p2) / 2

    n = ((z_alpha * (2 * p_avg * (1 - p_avg)) ** 0.5 +
          z_beta * (p1 * (1 - p1) + p2 * (1 - p2)) ** 0.5) ** 2) / (p2 - p1) ** 2

    return int(n) + 1

# Example: 5% baseline conversion, detect 2% lift
n = required_sample_size(0.05, 0.02)
print(f"Need {n} users per group")  # ~2,400 per group
```

---

## 5. Marketing Attribution Deep Dive

### Time-Decay Model Configuration

```python
from insight_engine.attribution import time_decay

# Time-decay gives more credit to recent touchpoints
result = time_decay(
    touchpoints=touchpoints,
    conversions=conversions
)

# How time-decay works:
# - Most recent touchpoint gets highest weight
# - Each earlier touchpoint gets exponentially less credit
# - Half-life is configurable (default: 7 days)
# - Formula: weight = 2^(-t/half_life)
```

### Comparing All Four Models

```python
from insight_engine.attribution import first_touch, last_touch, linear, time_decay
import pandas as pd

def full_attribution_analysis(touchpoints, conversions):
    """Run all 4 models and generate comparison report."""

    models = {
        "First Touch": first_touch(touchpoints, conversions),
        "Last Touch": last_touch(touchpoints, conversions),
        "Linear": linear(touchpoints, conversions),
        "Time Decay": time_decay(touchpoints, conversions),
    }

    # Build comparison DataFrame
    channels = set()
    for m in models.values():
        channels.update(m.channel_credits.keys())

    comparison = pd.DataFrame(index=sorted(channels))
    for name, result in models.items():
        comparison[name] = comparison.index.map(
            lambda ch: result.channel_credits.get(ch, 0)
        )

    comparison["Average"] = comparison.mean(axis=1)
    comparison = comparison.sort_values("Average", ascending=False)

    return comparison, models

comparison, models = full_attribution_analysis(touchpoints, conversions)
print(comparison.to_string())
```

### Interpreting Attribution Results

| Model | Best For | Bias |
|-------|----------|------|
| First Touch | Understanding awareness channels | Overcredits top-of-funnel |
| Last Touch | Understanding conversion channels | Overcredits bottom-of-funnel |
| Linear | Fair baseline comparison | No bias, but oversimplifies |
| Time Decay | Realistic multi-touch | Slight recency bias |

**Recommendation**: Use the **average across all four models** as your primary attribution metric. Present all four to stakeholders so they can see the range.

---

## 6. Time Series Forecasting

### Forecasting Methods

Insight Engine supports four forecasting methods:

```python
from insight_engine.forecaster import Forecaster

forecaster = Forecaster()

# Method 1: Moving Average
ma = forecaster.forecast(revenue_series, periods=6, method="moving_average")

# Method 2: Exponential Smoothing
es = forecaster.forecast(revenue_series, periods=6, method="exponential_smoothing")

# Method 3: Linear Trend
lt = forecaster.forecast(revenue_series, periods=6, method="linear_trend")

# Method 4: Ensemble (recommended -- combines all three)
ensemble = forecaster.forecast(revenue_series, periods=6, method="ensemble")
print(f"Ensemble predictions: {ensemble.predictions}")
print(f"Confidence: +/- {ensemble.confidence_interval:.1f}%")
```

### Method Selection Guide

| Method | Best For | Handles Trend? | Handles Seasonality? |
|--------|----------|---------------|---------------------|
| Moving Average | Stable data | No | Partially |
| Exponential Smoothing | Recent-weighted | Partially | No |
| Linear Trend | Growing/declining | Yes | No |
| Ensemble | General use | Yes | Partially |

### Forecast Validation

```python
# Backtest: hold out last 3 months, forecast, compare
def backtest_forecast(series, holdout=3):
    train = series[:-holdout]
    actual = series[-holdout:]

    forecast = forecaster.forecast(train, periods=holdout, method="ensemble")

    mape = sum(abs(a - p) / a for a, p in zip(actual, forecast.predictions)) / holdout * 100
    print(f"MAPE: {mape:.1f}%")  # <10% is good, <5% is excellent

    return mape
```

---

## 7. Anomaly Detection Patterns

### Multi-Method Ensemble Detection

```python
from insight_engine.anomaly_detector import AnomalyDetector
from insight_engine.advanced_anomaly import AdvancedAnomalyDetector

# Basic: Z-score and IQR
basic = AnomalyDetector()
zscore_anomalies = basic.detect(series, method="zscore", threshold=2.5)
iqr_anomalies = basic.detect(series, method="iqr", threshold=1.5)

# Advanced: Isolation Forest + LOF ensemble
advanced = AdvancedAnomalyDetector()
ensemble = advanced.detect(
    multivariate_data,
    methods=["isolation_forest", "lof"],
    contamination=0.05
)
```

### Detection Method Guide

| Method | Best For | Speed | Multivariate? |
|--------|----------|-------|---------------|
| Z-score | Normal distributions | Fast | No |
| IQR | Skewed distributions | Fast | No |
| Isolation Forest | Complex patterns | Medium | Yes |
| LOF | Density-based clusters | Medium | Yes |
| Ensemble | Production use | Medium | Yes |

---

## 8. Feature Engineering

### Insight Engine's Feature Lab

```python
from insight_engine.feature_lab import FeatureLab

lab = FeatureLab()

# Scaling
scaled = lab.scale(df, columns=["revenue", "spend"], method="standard")
# Options: "standard" (z-score), "minmax" (0-1), "robust" (median-based)

# Encoding
encoded = lab.encode(df, columns=["category", "region"], method="onehot")
# Options: "onehot", "label", "target"

# Polynomial features
poly = lab.polynomial(df, columns=["spend", "impressions"], degree=2)
# Creates: spend^2, impressions^2, spend*impressions

# Interaction terms
interactions = lab.interactions(df, columns=["channel", "day_of_week", "device"])
# Creates all pairwise interaction features
```

---

## 9. Dimensionality Reduction

### PCA and t-SNE Visualization

```python
from insight_engine.dimensionality import reduce_pca, reduce_tsne

# PCA for linear dimensionality reduction
pca_result = reduce_pca(high_dim_data, n_components=2)
print(f"Explained variance: {pca_result.explained_variance_ratio}")

# t-SNE for non-linear visualization
tsne_result = reduce_tsne(high_dim_data, n_components=2, perplexity=30)

# Use for cluster visualization
import plotly.express as px
fig = px.scatter(
    x=pca_result.components[:, 0],
    y=pca_result.components[:, 1],
    color=cluster_labels,
    title="Customer Segments (PCA)"
)
```

---

## 10. Production Analytics Pipeline

### End-to-End Pipeline Configuration

```python
from insight_engine.profiler import profile_dataframe
from insight_engine.cleaner import DataCleaner
from insight_engine.predictor import Predictor
from insight_engine.dashboard_generator import DashboardGenerator
from insight_engine.kpi_framework import KPIFramework, KPIDefinition

class AnalyticsPipeline:
    """Production-ready analytics pipeline using Insight Engine."""

    def __init__(self):
        self.cleaner = DataCleaner()
        self.predictor = Predictor()
        self.dashboard = DashboardGenerator()
        self.kpi = KPIFramework()

    def run(self, raw_data: pd.DataFrame) -> dict:
        # Step 1: Clean
        cleaned = self.cleaner.clean(raw_data, dedup=True, standardize=True)

        # Step 2: Profile
        profile = profile_dataframe(cleaned)

        # Step 3: Model
        prediction = self.predictor.fit(cleaned, target_column="target")

        # Step 4: Dashboard
        charts = self.dashboard.generate(cleaned)

        # Step 5: KPIs
        kpi_report = self.kpi.evaluate(cleaned)

        return {
            "profile": profile,
            "prediction": prediction,
            "charts": charts,
            "kpis": kpi_report
        }
```

### Pipeline Best Practices

| Step | Module | Key Setting |
|------|--------|-------------|
| Clean | `DataCleaner` | Enable dedup, smart imputation |
| Profile | `profile_dataframe` | Check outlier counts before modeling |
| Quality | `score_data_quality` | Reject data below 80/100 quality |
| Model | `Predictor` | Always check SHAP importances |
| Evaluate | `RegressorDiagnostics` | Check residuals, VIF, heteroscedasticity |
| Dashboard | `DashboardGenerator` | Auto-layout selects best chart types |
| Monitor | `KPIFramework` | Set warning and critical thresholds |

### Regression Diagnostics

```python
from insight_engine.regression_diagnostics import RegressionDiagnostics

diag = RegressionDiagnostics()
report = diag.analyze(model=result.model, X=features, y=target)

print(f"Residual normality (Shapiro p): {report.residual_normality_p:.4f}")
print(f"Heteroscedasticity (Breusch-Pagan p): {report.heteroscedasticity_p:.4f}")
print(f"Max VIF: {report.max_vif:.1f}")  # >10 indicates multicollinearity

if report.max_vif > 10:
    print("WARNING: Multicollinearity detected. Remove correlated features.")
```

---

## Quick Reference Card

### Module Index

| Module | Import | Key Function |
|--------|--------|-------------|
| Profiler | `insight_engine.profiler` | `profile_dataframe(df)` |
| Clustering | `insight_engine.clustering` | `cluster_kmeans(data, n_clusters)` |
| Attribution | `insight_engine.attribution` | `first_touch(tp, conv)` |
| Predictor | `insight_engine.predictor` | `Predictor().fit(df, target)` |
| Forecaster | `insight_engine.forecaster` | `Forecaster().forecast(series, periods)` |
| Statistical Tests | `insight_engine.statistical_tests` | `run_test(a, b, test_type="auto")` |
| Anomaly | `insight_engine.anomaly_detector` | `AnomalyDetector().detect(series)` |
| Feature Lab | `insight_engine.feature_lab` | `FeatureLab().scale(df, cols)` |
| KPIs | `insight_engine.kpi_framework` | `KPIFramework().evaluate(data)` |
| Diagnostics | `insight_engine.regression_diagnostics` | `RegressionDiagnostics().analyze()` |

---

## About Insight Engine

Insight Engine: 520+ automated tests across 19 test files. Auto-profiling, 4 attribution models, K-means/DBSCAN clustering, gradient boosting with SHAP, 6 statistical tests, 4 forecasting methods, isolation forest anomaly detection, feature engineering, PCA/t-SNE, and automated Plotly dashboards.

- **Repository**: [github.com/ChunkyTortoise/insight-engine](https://github.com/ChunkyTortoise/insight-engine)
- **Live Demo**: [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)
- **ML Stack**: scikit-learn, XGBoost, SHAP, Plotly
- **Tests**: 520+ (all deterministic, no network access required)
