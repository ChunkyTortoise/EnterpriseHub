# 🏭 Margin Hunter Scenario Template: Manufacturing Volume Planning

**Industry**: Manufacturing / Production
**Use Case**: Production volume planning and pricing strategy
**Company Type**: Contract manufacturer, private label, or branded goods manufacturer

---

## 📋 Scenario Overview

You're operating a manufacturing business and need to:
- Calculate minimum production runs to cover fixed costs (equipment, labor, facility)
- Model the impact of raw material price fluctuations
- Determine optimal pricing for new contracts or product lines
- Analyze capacity utilization and profitability by SKU

---

## 💰 Typical Manufacturing Financial Profile

### Revenue Structure
- **Unit Selling Price**: Wholesale price to distributors/retailers (B2B) or retail price (D2C)
- **Pricing Model**: Cost-plus (COGS + markup) or market-based competitive pricing
- **Contract Structure**: Fixed-price contracts, volume discounts, or spot pricing

### Variable Costs (per unit produced)
- **Raw materials**: 30-50% of selling price (metals, plastics, chemicals, components)
- **Direct labor**: $10-40/unit (assembly, machining, quality control - varies by automation level)
- **Packaging & shipping**: $3-15/unit (boxes, pallets, freight to customer)
- **Energy & utilities**: $2-8/unit (electricity, gas, water for production line)
- **Quality control & waste**: 2-5% of production cost (defects, rework, scrap)
- **Consumables**: $1-5/unit (lubricants, cutting tools, adhesives)

**Typical Total Variable Cost**: 50-70% of selling price

### Fixed Costs (monthly or quarterly)
- **Facility & rent**: $10,000-100,000/month (factory space, property taxes, insurance)
- **Equipment depreciation**: $5,000-50,000/month (amortized capital equipment costs)
- **Salaried labor**: $30,000-200,000/month (managers, engineers, overhead staff)
- **Maintenance & repairs**: $5,000-30,000/month (preventive maintenance, breakdowns)
- **R&D**: $5,000-50,000/month (product development, process improvements)
- **Administrative overhead**: $5,000-25,000/month (accounting, HR, legal, IT)

**Typical Total Fixed Costs**: $60,000-500,000/month (highly variable by industry & scale)

---

## 🧮 Example Analysis: Aluminum Extrusion Parts

### Business Context
Mid-sized manufacturer producing custom aluminum extrusions for construction and industrial customers. Recently invested in new extrusion press ($500k capex, depreciated over 5 years).

### Inputs
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Unit Selling Price** | $145.00 | Market rate for custom extrusions (per meter) |
| **Unit Variable Cost** | $82.00 | Breakdown below |
| **Total Fixed Costs** | $95,000/month | Facility + equipment + overhead |
| **Target Profit** | $40,000/month | 30% ROI on invested capital |
| **Current Production** | 2,100 meters/month | Current order book |

### Variable Cost Breakdown (per meter)
- **Aluminum ingot**: $45.00 (current LME price + processing)
- **Direct labor**: $18.00 (machine operator, setup time allocation)
- **Die & tooling wear**: $6.00 (custom die depreciation per unit)
- **Energy**: $5.50 (electricity for extrusion press, heating)
- **Finishing**: $4.00 (anodizing, powder coating, cutting to length)
- **Packaging & freight**: $3.50 (crating, delivery to customer)

**Total Variable Cost**: $82.00 per meter

### Analysis Results (using Margin Hunter)

**Key Metrics**:
- **Contribution Margin**: $63.00 per meter (43.4%)
- **Break-Even Production**: 1,508 meters/month (~$219k revenue)
- **Break-Even Revenue**: $218,660/month
- **Target Profit Production**: 2,143 meters/month (~$311k revenue)
- **Margin of Safety**: 28.2% (592 meters of cushion)

**Interpretation**:
- **Currently profitable** - 2,100 meters exceeds break-even of 1,508
- Generating ~$37,296/month profit (close to $40k target)
- **Strong margin of safety** - can lose 28% of orders and still break even
- Contribution margin of 43.4% means every meter past break-even adds $63 to profit

---

## 🎯 Decision-Making Scenarios

### Scenario A: Aluminum prices increase 15% (from $45 to $51.75/meter)

**New Analysis**:
- New Variable Cost: $88.75/meter
- Contribution Margin: $56.25/meter (38.8%)
- Break-Even Production: 1,689 meters/month
- **Decision**: CONCERNING - margin of safety drops to 19.6% (411 meters). Options:
  - **Raise price to $152** (maintain 43% margin)
  - **Negotiate long-term aluminum supply contract** (lock in $45 rate)
  - **Accept lower margins** (38.8% still healthy)

### Scenario B: Customer requests 20% volume discount (new price = $116/meter)

**New Analysis**:
- New Selling Price: $116/meter
- Contribution Margin: $34/meter (29.3%)
- Break-Even Production: 2,794 meters/month
- **Decision**: ONLY VIABLE if customer orders 3,000+ meters/month. Otherwise, declining margins don't justify volume discount.

### Scenario C: Install automation to reduce labor from $18 to $10/meter (requires $200k capex)

**New Analysis**:
- New Variable Cost: $74/meter
- New Fixed Costs: $98,333/month (add $200k/60 months depreciation)
- Contribution Margin: $71/meter (49%)
- Break-Even Production: 1,385 meters/month
- **Decision**: EXCELLENT - payback period is 5 months. Break-even drops by 123 meters, and margin increases to 49%.

---

## 📊 Capacity Utilization Analysis

Use Margin Hunter to model production scenarios across capacity levels:

| Scenario | Meters/Month | % of Max Capacity | Revenue | Profit | Margin of Safety |
|----------|-------------|------------------|---------|--------|------------------|
| **Current** | 2,100 | 70% | $304,500 | $37,300 | 28.2% |
| Conservative | 1,800 | 60% | $261,000 | $18,400 | 16.2% |
| Aggressive | 2,700 | 90% | $391,500 | $75,100 | 44.2% |
| **Max Capacity** | 3,000 | 100% | $435,000 | $94,000 | 49.7% |

**Key Insights**:
- **Underutilized capacity** - currently at 70%, potential to grow profit by 2.5x
- **Sales target**: Fill capacity to 90% (2,700 meters) for optimal profitability
- **Risk**: At 60% capacity, profit drops to $18k (54% below target)

**Action Plan**:
1. **Sales push**: Focus on winning 600 meters/month of new contracts (28% growth)
2. **Marketing**: Target construction industry (Q2-Q3 seasonal demand)
3. **Pricing**: Offer 10% discount for orders >500 meters to fill capacity

---

## 🏗️ Multi-Product Manufacturing Portfolio

Many manufacturers produce multiple SKUs. Run Margin Hunter for each product line:

| Product Line | Price | Variable Cost | Margin | Break-Even | Current Volume | Status |
|-------------|-------|---------------|--------|------------|----------------|--------|
| **Extrusions** | $145 | $82 | $63 (43%) | 1,508/mo | 2,100/mo | ✅ Profitable |
| Sheet Metal | $95 | $58 | $37 (39%) | 2,568/mo | 1,800/mo | ❌ Below break-even |
| Precision Parts | $220 | $105 | $115 (52%) | 826/mo | 1,200/mo | ✅ Highly profitable |
| Prototypes | $450 | $280 | $170 (38%) | 559/mo | 300/mo | ❌ Below break-even |

**Portfolio Optimization**:
- **Invest in precision parts** - highest margin (52%), already profitable
- **Fix or exit sheet metal** - 768 units short of break-even, consider price increase or discontinue
- **Prototypes**: Loss leader for winning production contracts (strategic, not profitable standalone)
- **Extrusions**: Solid performer, focus on filling capacity

---

## 🚀 Recommended Actions

### Immediate (Week 1)
1. **Calculate break-even for each product line** using actual production data
2. **Audit variable costs** - are material costs, labor rates, and scrap rates accurate?
3. **Review capacity utilization** - how much headroom exists to absorb new orders?

### Short-term (Month 1)
1. **Renegotiate raw material contracts** - lock in prices, negotiate volume discounts
2. **Analyze make-vs-buy decisions** - should any components be outsourced?
3. **Test pricing changes** - model 5-10% price increase for high-demand products

### Strategic (Quarter 1)
1. **Automation ROI analysis** - use Margin Hunter to model capex investments
2. **Customer segmentation** - focus on high-margin customers, exit low-margin accounts
3. **Lean manufacturing** - reduce waste, improve yield, lower variable costs by 5-10%

---

## 🎓 Manufacturing-Specific Considerations

### Why Manufacturing has MODERATE contribution margins (35-55%)
- High variable costs (raw materials, direct labor)
- Material price volatility (commodities fluctuate with global markets)
- Energy-intensive processes (especially metals, chemicals, plastics)

### Why Manufacturing has HIGH fixed costs
- Capital-intensive (machinery, tooling, facilities)
- Long equipment lifecycles (depreciation over 5-20 years)
- Regulatory compliance (safety, environmental, quality certifications)
- Skilled labor (engineers, machinists, supervisors)

### Key Manufacturing Metrics to Track Alongside Margin Hunter
- **Capacity Utilization**: % of maximum production capacity being used (target: 75-85%)
- **Yield Rate**: % of units produced without defects (target: 95%+)
- **Equipment OEE (Overall Equipment Effectiveness)**: Availability × Performance × Quality (target: 85%+)
- **Inventory Turnover**: Raw materials + WIP + finished goods turnover rate (target: 8-12x/year)

---

## 🧮 Advanced Use Case: Contract Manufacturing Bidding

### Scenario: Bidding on a 3-year contract for 50,000 units/year

**Customer Requirements**:
- Annual volume: 50,000 units (4,167/month)
- Contract term: 3 years (total 150,000 units)
- Price ceiling: $140/unit (customer's budget)

**Your Cost Structure**:
- Variable Cost: $82/unit (existing)
- Fixed Costs: $95,000/month
- Target Profit: 30% margin on revenue

**Analysis**:

**Option 1: Bid at $140/unit (customer's ceiling)**
- Contribution Margin: $58/unit (41.4%)
- Monthly Profit: (4,167 × $58) - $95,000 = $146,686/month
- Annual Profit: $1,760,232 (30% margin) ✅ MEETS TARGET

**Option 2: Bid at $130/unit (aggressive pricing to win)**
- Contribution Margin: $48/unit (36.9%)
- Monthly Profit: (4,167 × $48) - $95,000 = $105,016/month
- Annual Profit: $1,260,192 (24% margin) ⚠️ BELOW TARGET, but acceptable if fills capacity

**Option 3: Invest in automation first, then bid at $125/unit**
- New Variable Cost: $74/unit (after automation)
- New Fixed Costs: $98,333/month (add depreciation)
- Contribution Margin: $51/unit (40.8%)
- Monthly Profit: (4,167 × $51) - $98,333 = $114,184/month
- Annual Profit: $1,370,208 (27% margin) ✅ COMPETITIVE pricing, maintains margins

**Recommended Bid**: $138/unit (split the difference), emphasize quality & delivery reliability

---

## 📁 Template Inputs (Copy to Margin Hunter)

### Standard Production Analysis
```
Unit Selling Price: $145.00
Unit Variable Cost: $82.00
Total Fixed Costs: $95,000.00
Target Profit: $40,000.00
Current Sales (Units): [Your actual monthly production]
```

### Contract Bidding Scenario
```
Unit Selling Price: $140.00 (customer's ceiling)
Unit Variable Cost: $82.00
Total Fixed Costs: $95,000.00
Target Profit: [30% of revenue = $58/unit × volume]
Current Sales (Units): 4,167 (contract volume)
```

### Automation ROI Analysis
```
Unit Selling Price: $145.00
Unit Variable Cost: $74.00 (reduced labor)
Total Fixed Costs: $98,333.00 (add capex depreciation)
Target Profit: $40,000.00
Current Sales (Units): 2,100
```

---

## 🔗 Additional Resources

- **Lean Manufacturing Toolkit**: [link to resource]
- **Equipment ROI Calculator**: [link to capex analysis tool]
- **Material Cost Index**: [link to commodity price tracking]

---

**Try this scenario now**: [enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

**Questions?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues)

---

*Part of the Enterprise Hub Margin Hunter module | Built by Cayman Roden*
