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

### Quick Start in 60 Seconds

**New to Margin Hunter? Get profitability insights in under 1 minute:**

1. **Open the app**: Navigate to Margin Hunter in the sidebar
2. **Enter 5 numbers** (example: SaaS product):
   - Selling Price: `99` (per month, per customer)
   - Variable Cost: `15` (hosting + support per customer)
   - Fixed Costs: `50000` (monthly salaries, marketing, rent)
   - Current Sales: `100` (current customers)
   - Target Profit: `20000` (monthly profit goal)
3. **Click outside the last field**: Calculations appear instantly
4. **View 3 key outputs**:
   - Break-even: 595 customers (your profitability threshold)
   - Contribution Margin: $84 per customer (85% margin - typical for SaaS)
   - Sensitivity Heatmap: See how $10 price changes affect profit
5. **Export results**: Click "Download Scenario Analysis (CSV)" to share with your team

**That's it! You now know:**
- How many customers you need to break even (595)
- How much profit you make per customer ($84)
- What happens if you raise prices or costs change (heatmap)

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

## 🔧 Troubleshooting

### Common Issues & Solutions

#### Issue: "No metrics are showing up"

**Cause**: Calculations only trigger when all 5 fields are filled with valid numbers.

**Solution**:
1. Verify all 5 fields have values (no empty fields)
2. Ensure all values are positive numbers (no negative prices or costs)
3. Verify Variable Cost is less than Selling Price (otherwise contribution margin is negative)
4. Click outside the last field or press Tab to trigger calculations

#### Issue: "Margin of Safety shows N/A or negative value"

**Cause**: Current Sales are below Break-Even Units (you're operating at a loss).

**Solution**:
- This is expected if you haven't reached profitability yet
- **N/A** means you're not profitable, so margin of safety can't be calculated
- **Negative value** means you need to increase sales or reduce costs to reach break-even
- Focus on the Break-Even Units metric to see how many more sales you need

#### Issue: "Operating Leverage shows N/A"

**Cause**: Net Profit is zero or negative (can't calculate leverage when unprofitable).

**Solution**:
- Operating leverage only applies when you're profitable
- This is expected for early-stage businesses below break-even
- Once Current Sales exceed Break-Even Units, operating leverage will display

#### Issue: "Sensitivity heatmap is all red (negative profits)"

**Cause**: Your current scenario is unprofitable across all price/cost combinations within ±20% range.

**Solution**:
1. **Reduce Fixed Costs**: Can you cut overhead by 20-30%?
2. **Increase Selling Price**: The heatmap might show green at the top (higher prices)
3. **Reduce Variable Costs**: Negotiate better supplier rates or optimize operations
4. **Increase Sales Volume**: More volume spreads fixed costs across more units
5. **Re-evaluate business model**: If all scenarios are unprofitable, the product may not be viable

#### Issue: "Break-even units seem too high"

**Cause**: High fixed costs relative to contribution margin.

**Solution**:
- **Check your units**: Are you mixing monthly and annual numbers? (e.g., monthly price but annual fixed costs)
- **Normalize time periods**: Use all-monthly or all-annual for consistency
- **Reduce fixed costs**: Even small reductions have big impact on break-even
- **Increase contribution margin**: Raise prices or lower variable costs

**Example**:
- Fixed Costs: $50,000/month (correct)
- Selling Price: $99 (monthly, correct)
- Variable Cost: $15 (monthly, correct)
- Break-Even: 595 customers (this is accurate for the inputs)

#### Issue: "CSV export isn't downloading"

**Cause**: Browser blocking downloads or pop-ups.

**Solution**:
1. Check browser download bar (bottom of Chrome, top-right of Firefox)
2. Allow downloads from the app domain
3. Try a different browser (Chrome, Firefox, Safari)
4. Check your Downloads folder - it may have downloaded silently

#### Issue: "Charts aren't displaying"

**Cause**: JavaScript disabled or browser compatibility issue.

**Solution**:
- Enable JavaScript in browser settings
- Try a modern browser (Chrome 90+, Firefox 88+, Safari 14+)
- Clear browser cache and reload the page
- Disable browser extensions that might block scripts

### Understanding the Metrics

**Contribution Margin**: Should be positive. If negative, variable cost exceeds selling price - the business loses money on every sale.

**Break-Even Units**: The minimum sales needed to cover all costs. Higher fixed costs = higher break-even.

**Margin of Safety**: Measures risk. 50% means sales can drop 50% before hitting break-even. Higher is safer.

**Operating Leverage**: Amplification effect. 2.5x means a 10% sales increase = 25% profit increase. High leverage is good when growing, risky when declining.

### Best Practices

1. **Use consistent time periods**: All monthly or all annual (don't mix)
2. **Include all costs**: Don't forget insurance, utilities, software subscriptions in fixed costs
3. **Be realistic with variable costs**: Include shipping, payment processing, customer support
4. **Model multiple scenarios**: Run optimistic, realistic, and pessimistic cases
5. **Update regularly**: Re-run analysis when costs or prices change

### Getting Help

**Still stuck?**
- Check the [Example Use Cases](#-example-use-cases) section above for detailed scenarios
- Review [Industry Templates](../scenarios/) for pre-filled examples
- Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues) with your scenario
- Tag me on [LinkedIn](https://linkedin.com/in/caymanroden) with questions

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
