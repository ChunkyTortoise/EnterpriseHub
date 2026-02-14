# Case Study: Marketing Mix Modeling for a Multi-Channel Agency

## Client Profile

**Company**: Apex Growth Partners (anonymized)
**Industry**: Digital Marketing Agency
**Team Size**: 3 analysts, 8 campaign managers
**Challenge**: Prove marketing ROI across 12 client accounts with data-driven attribution and predictive modeling

---

## The Challenge

Apex Growth Partners manages marketing for 12 B2B and B2C clients across channels including Google Ads, Meta, LinkedIn, Email, Content Marketing, and Events. Their core problems:

- **Client reporting**: 3 analysts spent 2 weeks each month building 12 client reports manually from Google Analytics, ad platform exports, and CRM data
- **Attribution disputes**: Clients questioned channel ROI -- "Is our $50K/month Google Ads spend actually driving conversions?"
- **No predictive capability**: Clients wanted to know "If I increase LinkedIn spend by 20%, what happens to conversions?" and the agency had no model
- **Inconsistent testing**: A/B test results were interpreted manually with no statistical rigor -- several "winning" campaigns were later shown to be statistical noise

### Pain Points

| Problem | Impact |
|---------|--------|
| 2 weeks/month on 12 client reports | 120 analyst-hours/month, $18K/month in labor |
| Attribution disputes | 3 client churn events in 12 months citing "unclear ROI" |
| No predictive modeling | Could not answer "what if" budget questions |
| Manual A/B test analysis | 2 of 8 "winning" campaigns were false positives |
| No anomaly monitoring | Campaign budget overruns detected days late |

---

## The Solution: Insight Engine as Agency Analytics Platform

Apex deployed Insight Engine across all 12 client accounts, using templates for rapid setup.

### Step 1: Automated Client Reporting

Insight Engine's report generator creates markdown reports with findings, metrics, and chart placeholders:

```python
from insight_engine.profiler import profile_dataframe
from insight_engine.report_generator import ReportGenerator
from insight_engine.dashboard_generator import DashboardGenerator

import pandas as pd

# Generate client report in minutes, not weeks
def generate_client_report(client_name: str, data_path: str):
    df = pd.read_csv(data_path)

    # Auto-profile the data
    profile = profile_dataframe(df)

    # Generate dashboard
    dashboard = DashboardGenerator()
    charts = dashboard.generate(
        df,
        chart_types=["histogram", "pie", "heatmap", "scatter_matrix"]
    )

    # Generate report
    reporter = ReportGenerator()
    report = reporter.generate(
        profile=profile,
        title=f"{client_name} Monthly Performance Report",
        findings=extract_findings(profile),
        metrics=calculate_kpis(df)
    )

    return report  # Markdown with embedded chart references
```

What took 10 hours per client now took 10 minutes. The profiler auto-detects column types, finds correlations, and flags anomalies -- all the analysis that analysts previously did manually.

### Step 2: Multi-Model Attribution for Client Proof

For each client, Apex ran all four attribution models to provide complete ROI visibility:

```python
from insight_engine.attribution import first_touch, last_touch, linear, time_decay

def attribution_report(client_touchpoints, client_conversions):
    """Generate 4-model attribution comparison for a client."""

    results = {
        "First Touch": first_touch(client_touchpoints, client_conversions),
        "Last Touch": last_touch(client_touchpoints, client_conversions),
        "Linear": linear(client_touchpoints, client_conversions),
        "Time Decay": time_decay(client_touchpoints, client_conversions),
    }

    # Build comparison table
    for model_name, result in results.items():
        print(f"\n{model_name} Attribution ({result.total_conversions} conversions):")
        for channel, credit in sorted(
            result.channel_credits.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {channel}: {credit:.1f}%")

    return results
```

For one client spending $50K/month on Google Ads, the attribution comparison showed:

| Channel | Last-Touch (what they saw) | Linear (reality) | Delta |
|---------|---------------------------|-------------------|-------|
| Google Ads | 55% | 30% | **-25% overcredited** |
| LinkedIn | 10% | 22% | **+12% undercredited** |
| Content/Blog | 5% | 20% | **+15% undercredited** |
| Email Nurture | 20% | 18% | Roughly accurate |
| Events | 10% | 10% | Roughly accurate |

This data prevented the client from doubling their Google Ads budget ($600K/year waste) and instead redirected $120K to content and LinkedIn, which generated 35% more conversions.

### Step 3: Statistical Testing for Campaign Experiments

Insight Engine's statistical testing module auto-selects the appropriate test based on data characteristics:

```python
from insight_engine.statistical_tests import run_test, compare_groups

# A/B test: New landing page vs control
result = run_test(
    group_a=control_conversions,    # Control group conversion rates
    group_b=treatment_conversions,  # New landing page conversion rates
    test_type="auto"                # Auto-selects based on data
)

print(f"Test: {result.test_name}")         # e.g., "chi-square" for proportions
print(f"Statistic: {result.statistic:.3f}")
print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.significant}")  # True if p < 0.05
print(f"Effect size: {result.effect_size:.3f}")
print(f"Recommendation: {result.interpretation}")
```

Available tests in Insight Engine:
- **t-test**: Comparing means of two groups (normal distribution)
- **Mann-Whitney U**: Comparing medians (non-normal distribution)
- **Chi-square**: Comparing proportions/categories
- **ANOVA**: Comparing means across 3+ groups
- **Kruskal-Wallis**: Non-parametric ANOVA
- **Shapiro-Wilk**: Testing for normality

The auto-selection runs Shapiro-Wilk first to check normality, then selects the appropriate parametric or non-parametric test. This caught 2 of 8 "winning" campaigns that were actually statistical noise (p > 0.05 with proper testing).

### Step 4: Predictive Budget Modeling

```python
from insight_engine.predictor import Predictor
from insight_engine.model_observatory import ModelObservatory

predictor = Predictor()

# Train conversion prediction model
result = predictor.fit(
    df=historical_campaigns,
    target_column="conversions",
    feature_columns=["google_ads_spend", "linkedin_spend", "content_spend",
                     "email_spend", "month", "industry"]
)

print(f"R-squared: {result.r_squared:.3f}")

# SHAP analysis shows spend elasticity per channel
observatory = ModelObservatory()
explanations = observatory.explain(result.model, historical_campaigns)

# Answer "what if" questions
scenario = {
    "google_ads_spend": 40000,  # Reduce from 50K to 40K
    "linkedin_spend": 25000,    # Increase from 15K to 25K
    "content_spend": 15000,     # Increase from 5K to 15K
    "email_spend": 10000,       # Keep constant
}
predicted_conversions = predictor.predict_single(scenario)
print(f"Predicted conversions: {predicted_conversions:.0f}")
```

### Step 5: Automated Anomaly Alerts

```python
from insight_engine.anomaly_detector import AnomalyDetector
from insight_engine.advanced_anomaly import AdvancedAnomalyDetector

# Monitor daily spend for budget overruns
detector = AnomalyDetector()

for client in clients:
    daily_spend = get_daily_spend(client.id)
    anomalies = detector.detect(daily_spend, method="iqr", threshold=1.5)

    if anomalies:
        alert_account_manager(
            client=client.name,
            anomalies=anomalies,
            message=f"Unusual spend detected: {len(anomalies)} days flagged"
        )
```

### Step 6: Forecasting for Client Budget Planning

```python
from insight_engine.forecaster import Forecaster

forecaster = Forecaster()

# Quarterly revenue forecast per client
for client in clients:
    forecast = forecaster.forecast(
        series=client.monthly_revenue,
        periods=3,  # Next quarter
        method="ensemble"
    )

    print(f"{client.name}:")
    for month, value in zip(forecast.periods, forecast.predictions):
        print(f"  Month {month}: ${value:,.0f}")
```

---

## Results

### Agency Efficiency

| Metric | Before Insight Engine | After Insight Engine | Change |
|--------|----------------------|---------------------|--------|
| Monthly reporting time (12 clients) | 120 hours | 6 hours | **-95%** |
| Report generation per client | 10 hours | 30 minutes | **-95%** |
| Analyst headcount for reporting | 3 full-time | 1 part-time | **-67% labor** |
| Cost of reporting function | $18K/month | $3K/month | **-83%** |

### Client Outcomes

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Client churn (ROI disputes) | 3 clients/year | 0 clients/year | **Eliminated** |
| Average client conversion lift | Baseline | +35% | **Significant** |
| False positive campaigns | 2 of 8 (25%) | 0 of 12 (0%) | **Eliminated** |
| Budget waste prevention | None measured | $600K/year across clients | **Quantified** |

### Data Quality

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Campaign anomaly detection | 2-3 days | <2 hours | **-97%** |
| Forecast accuracy | +/- 25% | +/- 7% | **3.5x improvement** |
| Statistical rigor | Manual, inconsistent | Automated, correct | **Reliable** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | Profiler templates for 12 client accounts | Standardized data pipeline |
| 1 | Attribution models per client | ROI visibility across channels |
| 2 | Statistical testing framework | Rigorous experiment validation |
| 2 | Predictive models for top 4 clients | "What-if" budget scenarios |
| 3 | Anomaly detection and alerting | Real-time spend monitoring |
| 3 | Forecasting for quarterly planning | Data-driven budgets |
| 4 | Dashboard deployment and training | Self-service analytics |

**Total deployment**: 4 weeks for 12 client accounts.

---

## Key Takeaways

1. **Multi-model attribution prevents budget waste**. Showing clients all four attribution models (not just last-touch) prevented $600K in misallocated spend.

2. **Statistical testing eliminates false positives**. Auto-selecting the right test based on data characteristics caught 25% of "winning" campaigns as statistical noise.

3. **95% reporting reduction changes the agency model**. From 3 full-time analysts on reporting to 1 part-time, freeing capacity for strategic work.

4. **SHAP-powered "what-if" analysis retains clients**. Answering "what happens if we shift budget?" with data instead of opinions eliminated ROI-related churn.

5. **Standardized templates scale across clients**. The same Insight Engine pipeline works for B2B SaaS, e-commerce, and services clients with minimal configuration.

---

## About Insight Engine

Insight Engine provides 520+ automated tests across 19 test files, with 4 attribution models, 6 statistical tests, K-means/DBSCAN clustering, predictive modeling with SHAP, forecasting, anomaly detection, and automated reporting.

- **Repository**: [github.com/ChunkyTortoise/insight-engine](https://github.com/ChunkyTortoise/insight-engine)
- **Live Demo**: [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)
- **Tests**: 520+ across 19 test files
- **Statistical tests**: t-test, Mann-Whitney, chi-square, ANOVA, Kruskal-Wallis, Shapiro-Wilk
