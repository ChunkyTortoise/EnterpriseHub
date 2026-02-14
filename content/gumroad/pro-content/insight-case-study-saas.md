# Case Study: SaaS Metrics Dashboard for a B2B Platform

## Client Profile

**Company**: CloudSync Analytics (anonymized)
**Industry**: B2B SaaS / Customer Success
**Team Size**: 6 data analysts, 2 product managers
**Challenge**: Replace a 2-week manual quarterly reporting process with automated dashboards and churn prediction

---

## The Challenge

CloudSync Analytics is a B2B SaaS platform with 2,400 customers generating $8M ARR. Their data team spent enormous effort on manual reporting:

- **Quarterly reports**: 2 analysts spent 2 weeks each building slides from exported CSVs
- **Churn detection**: Reactive -- they discovered churn when customers canceled, not before
- **Attribution**: Marketing could not prove which channels drove trial-to-paid conversions
- **Forecasting**: Revenue projections were based on gut feel, not statistical models

The CFO wanted a self-service dashboard that updated automatically and predicted churn before it happened.

### Pain Points

| Problem | Impact |
|---------|--------|
| 2-week quarterly report cycle | 80 analyst-hours per quarter on manual slides |
| Reactive churn detection | 18% annual churn, no early warning system |
| No attribution model | $400K marketing spend with no channel ROI data |
| Gut-feel forecasting | Revenue projections off by 15-25% quarterly |
| Manual statistical testing | No data-driven decisions on pricing experiments |

---

## The Solution: Insight Engine for SaaS Intelligence

CloudSync deployed Insight Engine's auto-profiler, predictive modeling, attribution analysis, and statistical testing modules.

### Step 1: Auto-Profiling Customer Data

Insight Engine's profiler auto-detects column types, distributions, outliers, and correlations in seconds:

```python
from insight_engine.profiler import profile_dataframe, detect_column_type

import pandas as pd

# Load customer data
customers = pd.read_csv("customers.csv")

# Auto-profile: detects types, distributions, outliers, correlations
profile = profile_dataframe(customers)
print(f"Rows: {profile.row_count}")
print(f"Columns: {profile.column_count}")
print(f"Duplicate rows: {profile.duplicate_rows}")
print(f"Memory usage: {profile.memory_usage_mb:.1f} MB")

# Column-level insights
for col in profile.columns:
    print(f"\n{col.name} ({col.dtype}):")
    print(f"  Null %: {col.null_pct:.1f}%")
    print(f"  Unique values: {col.unique_count}")
    if col.mean is not None:
        print(f"  Mean: {col.mean:.2f}, Std: {col.std:.2f}")
        print(f"  Outliers: {col.outlier_count}")
    print(f"  Top values: {col.top_values[:3]}")
```

Profiling 100K rows takes less than 2 seconds. The profiler detected that CloudSync's "plan_type" column had 3 NULL values (data quality issue) and that "monthly_spend" had 12 outliers (enterprise customers skewing averages).

### Step 2: Data Quality Scoring

Before building models, Insight Engine validates data quality:

```python
from insight_engine.data_quality import score_data_quality

quality = score_data_quality(customers)
print(f"Overall quality: {quality.overall_score:.0f}/100")
print(f"Completeness: {quality.completeness:.0f}/100")
print(f"Uniqueness: {quality.uniqueness:.0f}/100")
print(f"Validity: {quality.validity:.0f}/100")

for col_score in quality.column_scores:
    if col_score.completeness < 95:
        print(f"WARNING: {col_score.name} is {col_score.completeness:.0f}% complete")
```

### Step 3: Churn Prediction with SHAP Explanations

Insight Engine's predictor module auto-detects classification vs regression and includes SHAP explainability:

```python
from insight_engine.predictor import Predictor

predictor = Predictor()

# Train churn prediction model
result = predictor.fit(
    df=customers,
    target_column="churned",  # Boolean: True/False
    feature_columns=["monthly_spend", "support_tickets", "login_frequency",
                     "feature_adoption", "contract_months", "nps_score"]
)

print(f"Model type: {result.model_type}")  # "classification"
print(f"Algorithm: {result.algorithm}")     # "gradient_boosting"
print(f"Accuracy: {result.accuracy:.2f}")
print(f"AUC-ROC: {result.auc_roc:.2f}")

# SHAP explanations show WHY each prediction was made
for feature, importance in result.shap_importances.items():
    print(f"  {feature}: {importance:.3f}")

# Predict churn risk for current customers
predictions = predictor.predict(active_customers)
high_risk = predictions[predictions["churn_probability"] > 0.7]
print(f"High-risk customers: {len(high_risk)}")
```

CloudSync's churn model achieved 85% prediction accuracy. The SHAP explanations revealed that "support_tickets > 5 in 30 days" was the strongest churn predictor, enabling proactive outreach.

### Step 4: Marketing Attribution Analysis

Insight Engine's attribution module implements four multi-touch models:

```python
from insight_engine.attribution import first_touch, last_touch, linear, time_decay
import pandas as pd

# Load marketing touchpoint data
touchpoints = pd.read_csv("touchpoints.csv")
# Columns: user_id, channel, timestamp

# Set of users who converted (trial -> paid)
conversions = set(converted_users["user_id"])

# Run all four attribution models
ft = first_touch(touchpoints, conversions)
lt = last_touch(touchpoints, conversions)
ln = linear(touchpoints, conversions)
td = time_decay(touchpoints, conversions)

# Compare channel credits across models
for model_result in [ft, lt, ln, td]:
    print(f"\n{model_result.model.value}:")
    print(f"  Total conversions: {model_result.total_conversions}")
    for channel, credit in model_result.channel_credits.items():
        print(f"  {channel}: {credit:.1f}%")
```

The attribution analysis revealed that CloudSync's content marketing (blog, webinars) drove 45% of first-touch conversions but received only 15% of budget. Paid search got 40% of budget but contributed only 20% of conversions.

### Step 5: Revenue Forecasting

```python
from insight_engine.forecaster import Forecaster

forecaster = Forecaster()

# Forecast monthly revenue using ensemble method
forecast = forecaster.forecast(
    series=monthly_revenue,
    periods=6,  # 6 months ahead
    method="ensemble"  # Combines moving avg, exp smoothing, linear trend
)

print(f"Method: {forecast.method}")
for period, value in zip(forecast.periods, forecast.predictions):
    print(f"  Month {period}: ${value:,.0f}")
print(f"  Confidence interval: +/- {forecast.confidence_interval:.1f}%")
```

### Step 6: Statistical Testing for Pricing Experiments

CloudSync ran a pricing experiment (Plan A: $49/mo vs Plan B: $59/mo). Insight Engine's statistical testing module validated the results:

```python
from insight_engine.statistical_tests import run_test

result = run_test(
    group_a=plan_a_conversions,
    group_b=plan_b_conversions,
    test_type="auto"  # Auto-selects appropriate test
)

print(f"Test used: {result.test_name}")  # "Mann-Whitney U" (non-normal data)
print(f"Statistic: {result.statistic:.3f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.significant}")  # True if p < 0.05
print(f"Effect size: {result.effect_size:.3f}")
```

---

## Results

### Reporting Efficiency

| Metric | Before Insight Engine | After Insight Engine | Change |
|--------|----------------------|---------------------|--------|
| Quarterly report time | 2 weeks | 10 minutes | **99% faster** |
| Manual analyst hours/quarter | 80 | 2 | **-98%** |
| Data quality visibility | None | Automated scoring | **New capability** |

### Churn Reduction

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Churn detection | Reactive (at cancellation) | 30 days advance warning | **Proactive** |
| Churn prediction accuracy | N/A | 85% | **New capability** |
| Annual churn rate | 18% | 11% | **-39%** |
| Revenue saved from churn | $0 | $560K/year | **Significant** |

### Marketing ROI

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Attribution model | None | 4 models | **Data-driven** |
| Budget reallocation | Gut feel | Attribution-based | **Optimized** |
| Lead-to-conversion rate | 12% | 28% | **+133%** |
| Marketing ROI visibility | None | Per-channel | **Complete** |

### Forecasting

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Revenue forecast accuracy | +/- 15-25% | +/- 5% | **3-5x more accurate** |
| Forecast preparation time | 3 days | 30 minutes | **-98%** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | Data profiling and quality assessment | Data issues identified |
| 1 | Dashboard generator configuration | Auto-generated Plotly dashboards |
| 2 | Churn prediction model training | 85% accuracy, SHAP explanations |
| 2 | Marketing attribution analysis | 4-model comparison |
| 3 | Revenue forecasting setup | Ensemble forecasts active |
| 3 | Statistical testing for pricing | Data-driven pricing decisions |
| 4 | Self-service dashboard deployment | Streamlit app live |

**Total deployment**: 4 weeks.

---

## Key Takeaways

1. **Auto-profiling eliminates the "understand your data" phase**. Column type detection, distributions, and correlations in under 2 seconds for 100K rows.

2. **SHAP explanations make predictions actionable**. CloudSync learned that "5+ support tickets in 30 days" was the top churn predictor, enabling targeted outreach.

3. **Four attribution models reveal budget misallocation**. Content marketing drove 45% of conversions but received 15% of budget.

4. **Statistical testing validates experiments**. Auto-selecting the right test (t-test, Mann-Whitney, chi-square) prevents analysts from using the wrong test.

5. **520+ tests give production confidence**. CloudSync's data team verified Insight Engine's calculations against their manual Excel models before deploying.

---

## About Insight Engine

Insight Engine provides 520+ automated tests across 19 test files, with auto-profiling, 4 attribution models, predictive modeling with SHAP, 6 statistical tests, time series forecasting, K-means/DBSCAN clustering, anomaly detection, and Plotly dashboard generation.

- **Repository**: [github.com/ChunkyTortoise/insight-engine](https://github.com/ChunkyTortoise/insight-engine)
- **Live Demo**: [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)
- **Profiling speed**: <2 seconds for 100K rows
- **ML algorithms**: 8+ (gradient boosting, random forest, XGBoost, etc.)
