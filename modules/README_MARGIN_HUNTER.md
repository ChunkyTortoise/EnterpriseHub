# 💰 Margin Hunter

**Break-even analysis and profit optimization for business leaders**

[![Module Status](https://img.shields.io/badge/status-production-brightgreen.svg)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![Use Case](https://img.shields.io/badge/use_case-profitability_analysis-blue.svg)]()

---

## 🎯 Business Value

Margin Hunter is a **Cost-Volume-Profit (CVP) analysis tool** that answers the critical questions every business leader asks:

- **"How many units do I need to sell to break even?"**
- **"What happens to my profit if I change my pricing?"**
- **"How much cushion do I have before I start losing money?"**
- **"What's the impact of rising costs on my bottom line?"**

Whether you're launching a new product, negotiating supplier contracts, or setting sales targets, Margin Hunter gives you instant clarity on your profitability dynamics.

---

## 💼 Who This Is For

### SaaS Founders
- Calculate break-even subscriber count for new pricing tiers
- Model the impact of cloud infrastructure cost changes
- Determine optimal pricing for maximum margin

### E-Commerce Operators
- Analyze product-level profitability across your catalog
- Understand the impact of shipping cost increases
- Plan promotional pricing without destroying margins

### Manufacturing Managers
- Calculate production volumes needed to cover fixed costs
- Model the effect of raw material price fluctuations
- Optimize pricing strategies for new product lines

### Financial Analysts
- Perform rapid what-if scenario modeling
- Validate business case assumptions
- Create board-ready profit sensitivity analyses

---

## ⚡ Key Features

### 1. Instant Break-Even Analysis
- **Break-even units**: Exact number of sales needed to cover all costs
- **Break-even revenue**: Total revenue required to reach profitability
- **Contribution margin**: Per-unit profit after variable costs

### 2. Advanced Profitability Metrics
- **Margin of Safety**: How far sales can drop before you hit break-even
- **Operating Leverage**: How sensitive your profits are to sales changes
- **Target Profit Calculator**: Units/revenue needed to hit your profit goals

### 3. Interactive CVP Visualization
- **Real-time graph** showing revenue vs. costs across all volume levels
- **Visual break-even point** - see exactly where profit starts
- **Current sales marker** - understand where you stand today

### 4. Sensitivity Heatmap
- **10x10 profit matrix** showing impact of price and cost changes
- **Color-coded visualization** - instantly identify profitable vs. unprofitable scenarios
- **Data-driven negotiations** - know exactly how much margin you have to play with

### 5. Scenario Modeling
- **Three-scenario table**: Break-even, Current Status, Target Profit
- **Exportable CSV** - share analysis with your team
- **Board-ready format** - drop into presentations immediately

---

## 🚀 Quick Start

### Live Demo
Try it now at **[enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)**

### Basic Workflow
1. **Input product costs** - Unit selling price and variable cost per unit
2. **Enter fixed costs** - Rent, salaries, overhead (monthly or annual)
3. **Set targets** - Current sales volume and desired profit
4. **Analyze results** - View break-even point, margins, and scenarios
5. **Explore sensitivity** - See how price/cost changes affect profit
6. **Export data** - Download CSV for further analysis

---

## 📊 Example Use Cases

### Use Case #1: SaaS Pricing Strategy
**Scenario**: You're launching a new enterprise software product and need to determine the right pricing tier.

**Inputs**:
- Unit Selling Price: $99/month (annual contract = $1,188)
- Unit Variable Cost: $15/month (hosting + support = $180/year)
- Fixed Costs: $50,000/month (salaries, marketing, infrastructure)
- Target Profit: $20,000/month

**Analysis**:
- **Break-even**: 50 customers (~$60k MRR)
- **Target profit**: 70 customers (~$84k MRR)
- **Contribution Margin**: 84.8% ($84 per customer)
- **Margin of Safety**: If you have 100 customers, you can lose 50% of them and still break even

**Business Decision**: Launch at $99/month. You only need 50 customers to break even, which is achievable with a modest marketing budget. The high contribution margin (84.8%) means every new customer after break-even drops $84 straight to the bottom line.

---

### Use Case #2: E-Commerce Product Profitability
**Scenario**: You're evaluating whether to continue selling a product after your supplier raised prices.

**Inputs**:
- Unit Selling Price: $49.99 (retail)
- Unit Variable Cost: $22.00 (was $18, supplier increased by $4)
- Fixed Costs: $5,000/month (warehouse, staff, marketing)
- Current Sales: 300 units/month

**Analysis**:
- **Break-even**: 179 units (you're currently at 300 - safe)
- **Current Profit**: $3,397/month (down from $4,597 before price increase)
- **Margin of Safety**: 40.3% (121 units of cushion)
- **Sensitivity Heatmap**: Shows that increasing price to $52.99 would recover lost margin

**Business Decision**: Keep the product but raise price to $52.99. The sensitivity analysis shows this maintains margin while break-even only increases to 185 units (still well below current sales).

---

### Use Case #3: Manufacturing Volume Planning
**Scenario**: You're planning production volumes for Q1 and need to ensure profitability.

**Inputs**:
- Unit Selling Price: $150 (wholesale to distributors)
- Unit Variable Cost: $85 (materials + direct labor)
- Fixed Costs: $45,000/quarter (facility, equipment, overhead)
- Target Profit: $30,000/quarter

**Analysis**:
- **Break-even**: 693 units (231/month)
- **Target profit**: 1,154 units (385/month)
- **Contribution Margin**: $65 per unit (43.3%)
- **Operating Leverage**: 2.3x (a 10% increase in sales = 23% profit increase)

**Business Decision**: Set Q1 production target at 1,200 units. This provides a 10% buffer above the target profit threshold and accounts for potential defects or returns.

---

## 🧮 The Math Behind It

Margin Hunter uses proven Cost-Volume-Profit formulas taught in every MBA program:

**Contribution Margin** = Selling Price - Variable Cost per Unit

**Break-Even Units** = Fixed Costs ÷ Contribution Margin

**Target Units** = (Fixed Costs + Target Profit) ÷ Contribution Margin

**Margin of Safety %** = (Current Sales - Break-Even Units) ÷ Current Sales × 100

**Operating Leverage** = Total Contribution Margin ÷ Net Profit

No complex spreadsheets, no error-prone formulas - just input your numbers and get instant answers.

---

## 🎨 Screenshots

### Main Dashboard
*Full CVP analysis with real-time calculations*

![Margin Hunter Dashboard](../assets/margin-hunter-dashboard.png)

### Sensitivity Heatmap
*Visual profit impact analysis across price and cost scenarios*

![Sensitivity Heatmap](../assets/margin-hunter-heatmap.png)

---

## 🛠️ Technical Details

### Built With
- **Streamlit** - Interactive web interface
- **Plotly** - Professional-grade visualizations
- **NumPy** - High-performance numerical calculations
- **Pandas** - Data export and CSV generation

### Code Quality
- Clean, maintainable Python code
- Error handling for edge cases (negative margins, zero sales, etc.)
- Responsive design for desktop, tablet, and mobile
- Real-time reactivity - results update as you type

### Performance
- **Instant calculations** - no waiting for backend processing
- **Client-side rendering** - all computation happens in your browser
- **Zero infrastructure** - no database, no API calls, no dependencies

---

## 📈 Roadmap

### Planned Features
- [ ] **Multi-product analysis** - Compare profitability across product lines
- [ ] **Historical tracking** - Save scenarios and track changes over time
- [ ] **Currency support** - Handle multiple currencies for international businesses
- [ ] **Custom sensitivity ranges** - User-defined price/cost variation percentages
- [ ] **PDF export** - Generate board-ready reports with one click

### Integration Opportunities
- [ ] **Connect to accounting software** (QuickBooks, Xero)
- [ ] **Import from spreadsheets** (CSV, Excel)
- [ ] **Export to BI tools** (Tableau, Power BI)

---

## 🤝 Feedback & Support

Have a feature request or found a bug?

- **GitHub Issues**: [github.com/ChunkyTortoise/enterprise-hub/issues](https://github.com/ChunkyTortoise/enterprise-hub/issues)
- **Live Demo**: [Try it now](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

---

## 📄 License

Part of Enterprise Hub - Licensed under MIT License

---

**Built by Cayman Roden** | [GitHub](https://github.com/ChunkyTortoise) | [LinkedIn](https://linkedin.com/in/caymanroden)

---

<div align="center">
  <strong>💰 Make data-driven pricing and volume decisions in seconds, not hours</strong>
</div>
