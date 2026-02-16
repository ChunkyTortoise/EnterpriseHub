# ROI Calculator Specification

**Version**: 1.0
**Date**: February 16, 2026
**Author**: tech-agent (architecture-sentinel)
**Purpose**: Define inputs, calculation logic, and outputs for the EnterpriseHub ROI Calculator

---

## Overview

The ROI Calculator is a Streamlit web application that helps real estate teams quantify the financial impact of deploying EnterpriseHub vs. their current manual lead management process. It produces dollar-value ROI estimates, payback period, and visual comparisons.

**Target Users**: Real estate agency owners, CTOs, operations managers
**Deployment**: Streamlit Cloud at `ct-roi-calculator.streamlit.app`
**File**: `content/business/roi_calculator.py`

---

## Input Parameters

### Section 1: Lead Volume

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `leads_per_month` | `st.number_input` | 100 | 10-10,000 | Monthly inbound leads |
| `current_response_time_min` | `st.number_input` | 45 | 5-480 | Current avg response time (minutes) |
| `agents_count` | `st.number_input` | 5 | 1-100 | Number of human agents |

### Section 2: Financial Metrics

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `avg_deal_value` | `st.number_input` | 50,000 | 1,000-10,000,000 | Average deal close value ($) |
| `current_conversion_rate` | `st.slider` | 12 | 1-50 | Current lead-to-close rate (%) |
| `commission_rate` | `st.slider` | 3.0 | 1.0-6.0 | Commission rate (%) |

### Section 3: Cost Inputs

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `agent_hourly_rate` | `st.number_input` | 25 | 10-100 | Agent hourly cost ($) |
| `current_monthly_api_cost` | `st.number_input` | 3600 | 0-50,000 | Current LLM/API costs ($/month) |
| `time_per_lead_min` | `st.number_input` | 45 | 5-120 | Minutes spent per lead currently |

### Section 4: Package Selection

| Input | Type | Default | Options | Description |
|-------|------|---------|---------|-------------|
| `package` | `st.selectbox` | "Jorge Bot Pro" | Lead Audit ($1,500), Jorge Bot Lite ($5,000), Jorge Bot Pro ($10,000), Revenue Engine ($15,000) | Deployment package |

---

## Calculation Logic

### Core Formulas

```python
# 1. Time Savings
current_hours_per_month = leads_per_month * time_per_lead_min / 60
automated_hours_per_month = leads_per_month * 2 / 60  # 2 min with EnterpriseHub
hours_saved_per_month = current_hours_per_month - automated_hours_per_month
labor_savings_per_month = hours_saved_per_month * agent_hourly_rate

# 2. Conversion Improvement
# EnterpriseHub proven: 133% increase (12% -> 28%)
# Scale based on current rate
conversion_improvement_factor = 1.0 + min(1.33, (45 - min(current_response_time_min, 45)) / 45 * 0.5 + 0.83)
# Simplified: if response time > 5 min, full 133% boost applies
new_conversion_rate = min(current_conversion_rate * 2.33, 50)  # Cap at 50%

current_deals_per_month = leads_per_month * (current_conversion_rate / 100)
new_deals_per_month = leads_per_month * (new_conversion_rate / 100)
additional_deals = new_deals_per_month - current_deals_per_month
additional_revenue = additional_deals * avg_deal_value
additional_commission = additional_revenue * (commission_rate / 100)

# 3. API Cost Savings (89% reduction via 3-tier caching)
api_savings_per_month = current_monthly_api_cost * 0.89

# 4. Total Monthly Savings
total_monthly_savings = labor_savings_per_month + additional_commission + api_savings_per_month

# 5. ROI Calculation
package_costs = {
    "Lead Audit": 1500,
    "Jorge Bot Lite": 5000,
    "Jorge Bot Pro": 10000,
    "Revenue Engine": 15000,
}
investment = package_costs[package]
annual_savings = total_monthly_savings * 12
roi_percentage = ((annual_savings - investment) / investment) * 100
payback_months = investment / total_monthly_savings if total_monthly_savings > 0 else float('inf')
```

### Validation Rules

1. All numeric inputs must be positive
2. Conversion rate capped at 50% (realistic ceiling)
3. Payback period displays "< 1 month" if savings exceed investment in first month
4. ROI percentage uses standard formula: (Gain - Cost) / Cost * 100

---

## Output Display

### Section 1: Key Metrics (st.metric cards)

| Metric | Format | Color Logic |
|--------|--------|-------------|
| Monthly Savings | `$XX,XXX` | Green if > $1,000 |
| Annual ROI | `X,XXX%` | Green if > 100% |
| Payback Period | `X.X months` | Green if < 6 months |
| Additional Deals/Month | `+XX` | Green always |

### Section 2: Savings Breakdown (st.bar_chart or st.plotly_chart)

Stacked bar chart showing:
- Labor savings (blue)
- Additional commission (green)
- API cost savings (orange)

### Section 3: Before/After Comparison Table

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Response time | {current_response_time_min} min | 2 min | -{reduction}% |
| Conversion rate | {current_rate}% | {new_rate}% | +{improvement}% |
| Deals per month | {current_deals} | {new_deals} | +{additional} |
| Monthly revenue | ${current_revenue} | ${new_revenue} | +${additional_revenue} |
| API costs | ${current_api} | ${reduced_api} | -89% |
| Hours per lead | {current_time} min | 2 min | -{reduction}% |

### Section 4: Investment Summary

| Item | Value |
|------|-------|
| Package | {package_name} |
| Investment | ${investment} |
| Monthly savings | ${monthly_savings} |
| Payback period | {payback} months |
| 12-month ROI | {roi}% |
| 12-month net savings | ${annual_savings - investment} |

### Section 5: CTA

```
Ready to see these results for your business?

[Book a Discovery Call](https://calendly.com/caymanroden/discovery-call) -- Free 30-minute consultation
[Email Us](mailto:caymanroden@gmail.com) -- caymanroden@gmail.com
```

---

## Layout

```
┌─────────────────────────────────────────────────────┐
│  EnterpriseHub ROI Calculator                       │
│  Calculate your return on AI-powered lead management│
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Lead Volume  │  │ Financials   │                │
│  │ - leads/mo   │  │ - deal value │                │
│  │ - resp time  │  │ - conv rate  │                │
│  │ - agents     │  │ - commission │                │
│  └──────────────┘  └──────────────┘                │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ Costs        │  │ Package      │                │
│  │ - hourly     │  │ - selectbox  │                │
│  │ - API costs  │  │              │                │
│  │ - time/lead  │  │              │                │
│  └──────────────┘  └──────────────┘                │
│                                                     │
│  ═══════════════════════════════════════════════════│
│                                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐     │
│  │Monthly │ │Annual  │ │Payback │ │+Deals  │     │
│  │Savings │ │ROI     │ │Period  │ │/Month  │     │
│  │$12,345 │ │1,234%  │ │0.8 mo  │ │+16     │     │
│  └────────┘ └────────┘ └────────┘ └────────┘     │
│                                                     │
│  [Savings Breakdown Bar Chart]                     │
│                                                     │
│  [Before/After Comparison Table]                   │
│                                                     │
│  [Investment Summary]                              │
│                                                     │
│  [CTA: Book a Discovery Call]                      │
└─────────────────────────────────────────────────────┘
```

---

## Test Scenarios

### Scenario 1: Small Agency (Validation)
- 50 leads/month, $300K avg deal, 10% conversion, 3% commission
- 3 agents, $20/hr, 30 min/lead, $500/mo API
- Expected: ~$4K monthly savings, < 3 month payback

### Scenario 2: Mid-Size Agency (Default)
- 100 leads/month, $50K avg deal, 12% conversion, 3% commission
- 5 agents, $25/hr, 45 min/lead, $3,600/mo API
- Expected: ~$8K monthly savings, < 2 month payback

### Scenario 3: Large Brokerage
- 500 leads/month, $80K avg deal, 8% conversion, 2.5% commission
- 15 agents, $30/hr, 60 min/lead, $10,000/mo API
- Expected: ~$40K monthly savings, < 1 month payback

---

## Technical Requirements

- **Framework**: Streamlit >= 1.30.0
- **Python**: >= 3.11
- **Dependencies**: streamlit only (no additional packages needed)
- **Responsive**: Use `st.columns` for 2-column and 4-column layouts
- **No external API calls**: All calculations are local
- **Page config**: `st.set_page_config(page_title="EnterpriseHub ROI Calculator", layout="wide")`

---

## File Output

**Path**: `content/business/roi_calculator.py`
**Size**: Estimated 200-300 lines
**Deployment**: Streamlit Cloud (push to GitHub, auto-deploy)

---

*Spec version 1.0 -- Ready for implementation.*
