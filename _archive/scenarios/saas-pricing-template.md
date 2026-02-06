# 🎯 Margin Hunter Scenario Template: SaaS Pricing Strategy

**Industry**: Software as a Service (SaaS)
**Use Case**: Determining optimal pricing for a new enterprise software product
**Company Stage**: Early-stage startup (pre-revenue or initial customers)

---

## 📋 Scenario Overview

You're launching a B2B SaaS product (project management, CRM, analytics, etc.) and need to:
- Determine the minimum price to sustain operations
- Calculate how many customers you need to break even
- Model different pricing tiers and their impact on profitability
- Understand margin of safety at various customer counts

---

## 💰 Typical SaaS Financial Profile

### Revenue Structure
- **Unit Selling Price**: Monthly subscription fee (e.g., $49, $99, $199 per user/seat)
- **Billing Cycle**: Monthly or annual (annual contracts improve cash flow)
- **Pricing Model**: Per-user, per-workspace, or flat-rate team pricing

### Variable Costs (per customer/month)
- **Cloud hosting**: $5-20/customer (AWS, GCP, Azure compute + storage)
- **Third-party APIs**: $2-10/customer (Stripe, SendGrid, Twilio, etc.)
- **Customer support**: $3-8/customer (support staff allocation)
- **Payment processing**: ~3% of revenue (Stripe, PayPal fees)

**Typical Total Variable Cost**: $15-35/customer/month

### Fixed Costs (monthly)
- **Salaries**: $40,000-100,000/month (engineering, sales, marketing, ops)
- **Infrastructure**: $3,000-10,000/month (databases, monitoring, CDN, security)
- **Marketing**: $10,000-50,000/month (ads, content, SEO, events)
- **Office & overhead**: $5,000-15,000/month (rent, software, legal, accounting)

**Typical Total Fixed Costs**: $60,000-150,000/month for early-stage SaaS

---

## 🧮 Example Analysis: Mid-Market CRM Software

### Inputs
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Unit Selling Price** | $99/month | Competitive with similar tools ($79-149 range) |
| **Unit Variable Cost** | $18/month | $10 hosting + $5 APIs + $3 support |
| **Total Fixed Costs** | $75,000/month | 5-person team + marketing + overhead |
| **Target Profit** | $25,000/month | Reinvestment buffer for growth |
| **Current Sales** | 850 customers | Hypothetical current customer base |

### Analysis Results (using Margin Hunter)

**Key Metrics**:
- **Contribution Margin**: $81 per customer (81.8%)
- **Break-Even Customers**: 926 customers (~$92k MRR)
- **Break-Even Revenue**: $91,584/month
- **Target Profit Customers**: 1,235 customers (~$122k MRR)
- **Margin of Safety**: -8.2% (currently 76 customers SHORT of break-even)

**Interpretation**:
- **Unit economics are strong** (81.8% margin), but customer count is too low
- Need to acquire 76 more customers immediately to reach profitability
- Once break-even is reached, each new customer adds $81/month to profit
- **High operating leverage**: a 10% increase in customers = ~40% profit increase

---

## 🎯 Decision-Making Scenarios

### Scenario A: Can we lower pricing to $79/month to accelerate growth?

**New Analysis**:
- Contribution Margin: $61 per customer (77.2%)
- Break-Even Customers: 1,230 customers
- **Decision**: RISKY - need 380 more customers than current base. Only viable if price cut drives 45%+ growth.

### Scenario B: What if we raise prices to $129/month for better positioning?

**New Analysis**:
- Contribution Margin: $111 per customer (86%)
- Break-Even Customers: 676 customers
- **Decision**: PROMISING - 174 customers below current base. Immediate profitability if churn stays low.

### Scenario C: What if hosting costs increase to $25/customer (infrastructure scaling)?

**New Analysis**:
- Contribution Margin: $74 per customer (74.7%)
- Break-Even Customers: 1,014 customers
- **Decision**: CONCERNING - need 164 more customers. Prioritize infrastructure optimization.

---

## 📊 Sensitivity Analysis Insights

Use the **Margin Hunter sensitivity heatmap** to visualize:

- **Horizontal axis (price changes)**: $79 to $119 (±20%)
- **Vertical axis (cost changes)**: $14 to $22 (±20%)
- **Color gradient**: Green = profitable, Red = unprofitable

**Key Findings**:
- **Sweet spot**: $109-119 price range with optimized costs ($15-17/customer)
- **Danger zone**: Any price below $85 with costs above $20 = very narrow margins
- **Negotiation power**: Can afford up to $24/customer in costs if price is $119

---

## 🚀 Recommended Actions

### Immediate (Week 1)
1. **Run this analysis** with your actual numbers in Margin Hunter
2. **Identify your break-even point** - how many customers do you need TODAY?
3. **Calculate runway** - at current acquisition rate, when do you hit break-even?

### Short-term (Month 1)
1. **Test pricing increase** - raise prices 10-15% for new customers, monitor churn
2. **Optimize variable costs** - negotiate hosting, consolidate APIs, reduce support burden
3. **Model growth scenarios** - if you acquire 50 customers/month, when are you profitable?

### Strategic (Quarter 1)
1. **Implement tiered pricing** - run separate analyses for Starter ($49), Pro ($99), Enterprise ($199)
2. **Annual contracts** - model 12-month upfront pricing (e.g., $999/year = $83/month effective)
3. **Track cohort metrics** - measure actual variable costs per customer cohort

---

## 🎓 SaaS-Specific Considerations

### Why SaaS has HIGH contribution margins (70-90%)
- Low incremental cost to serve additional customers
- Automated onboarding and billing
- Self-service product reduces support costs
- Economies of scale on infrastructure (the more customers, the lower per-unit cost)

### Why SaaS has HIGH fixed costs
- Need to build product BEFORE getting customers
- Large upfront engineering investment
- Continuous R&D to stay competitive
- Customer acquisition costs (CAC) often treated as fixed marketing spend

### Key SaaS Metrics to Track Alongside Margin Hunter
- **CAC Payback Period**: How many months until contribution margin > CAC?
- **LTV:CAC Ratio**: Lifetime Value ÷ Customer Acquisition Cost (target: 3:1)
- **Rule of 40**: Growth Rate + Profit Margin (target: >40%)
- **Net Dollar Retention**: Expansion revenue offsets churn (target: >100%)

---

## 📁 Template Inputs (Copy to Margin Hunter)

```
Unit Selling Price: $99.00
Unit Variable Cost: $18.00
Total Fixed Costs: $75,000.00
Target Profit: $25,000.00
Current Sales (Units): [Your actual customer count]
```

---

## 🔗 Additional Resources

- **SaaS Metrics Calculator**: [link to complementary tool]
- **Pricing Strategy Guide**: [link to blog post/resource]
- **CAC/LTV Analysis Template**: [link to spreadsheet]

---

**Try this scenario now**: [enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

**Questions?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues)

---

*Part of the Enterprise Hub Margin Hunter module | Built by Cayman Roden*
