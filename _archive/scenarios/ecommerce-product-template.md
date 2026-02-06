# 🛒 Margin Hunter Scenario Template: E-Commerce Product Profitability

**Industry**: E-Commerce / Retail
**Use Case**: Analyzing product-level profitability and inventory decisions
**Company Type**: Online retailer (D2C, marketplace, or hybrid)

---

## 📋 Scenario Overview

You're running an e-commerce business and need to:
- Determine which products are actually profitable
- Calculate minimum order volumes to justify carrying a product
- Model the impact of supplier price changes, shipping cost increases, or discounts
- Optimize your product mix based on contribution margin

---

## 💰 Typical E-Commerce Financial Profile

### Revenue Structure
- **Unit Selling Price**: Retail price to customer (before discounts/promotions)
- **Average Order Value (AOV)**: Typically $40-150 depending on niche
- **Pricing Strategy**: Cost-plus, competitive, or value-based pricing

### Variable Costs (per unit sold)
- **Product cost (COGS)**: 30-60% of retail price (wholesale or manufacturing cost)
- **Shipping & handling**: $5-15/unit (carrier fees, packaging materials)
- **Payment processing**: 2.9% + $0.30 per transaction (Stripe, Shopify Payments)
- **Marketplace fees**: 8-15% (Amazon FBA, Etsy, eBay take rates)
- **Returns & refunds**: 5-10% of revenue (product returns, restocking)
- **Pick & pack labor**: $2-5/unit (if using 3PL or warehouse staff)

**Typical Total Variable Cost**: 50-70% of retail price

### Fixed Costs (monthly)
- **Platform fees**: $30-300/month (Shopify, WooCommerce, BigCommerce)
- **Marketing & advertising**: $3,000-20,000/month (Facebook, Google, influencer)
- **Warehouse/storage**: $500-5,000/month (rent or 3PL storage fees)
- **Staff salaries**: $5,000-30,000/month (customer service, ops, creative)
- **Software & tools**: $500-2,000/month (email, analytics, inventory management)
- **Overhead**: $1,000-5,000/month (accounting, legal, insurance)

**Typical Total Fixed Costs**: $10,000-50,000/month depending on scale

---

## 🧮 Example Analysis: Premium Yoga Mats (D2C Brand)

### Inputs
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Unit Selling Price** | $59.99 | Premium positioning vs. $20-30 Amazon mats |
| **Unit Variable Cost** | $28.50 | Breakdown below |
| **Total Fixed Costs** | $18,000/month | Small team + ads + warehouse |
| **Target Profit** | $8,000/month | 30% profit margin goal |
| **Current Sales** | 650 units/month | Current run rate |

### Variable Cost Breakdown (per unit)
- Product cost (COGS): $18.00 (eco-friendly materials, custom branding)
- Shipping: $6.50 (average domestic US shipping via USPS/UPS)
- Payment processing: $2.04 (2.9% + $0.30 on $59.99)
- Returns allowance: $1.20 (2% of price, conservative)
- Pick & pack: $0.76 (3PL charges $0.76/unit)

**Total Variable Cost**: $28.50 per mat

### Analysis Results (using Margin Hunter)

**Key Metrics**:
- **Contribution Margin**: $31.49 per mat (52.5%)
- **Break-Even Units**: 572 mats/month (~$34.3k revenue)
- **Break-Even Revenue**: $34,314/month
- **Target Profit Units**: 826 mats/month (~$49.5k revenue)
- **Margin of Safety**: 12.0% (78 units of cushion above break-even)

**Interpretation**:
- **Currently profitable** - 650 units exceeds break-even of 572
- Generating ~$2,457/month profit ($31.49 × 78 units above break-even)
- Need to grow to 826 units/month to hit $8k profit target
- **Healthy margin of safety** - can lose 12% of sales and still break even

---

## 🎯 Decision-Making Scenarios

### Scenario A: Supplier raises price by $3/mat (raw materials inflation)

**New Analysis**:
- Contribution Margin: $28.49 per mat (47.5%)
- Break-Even Units: 632 mats/month
- **Decision**: MANAGEABLE - still profitable, but margin of safety drops to 2.8% (18 units). Consider small price increase to $62.99 to offset.

### Scenario B: Run a 20% off promotion ($47.99 sale price)

**New Analysis**:
- Contribution Margin: $19.49 per mat (40.6%)
- Break-Even Units: 924 mats/month
- **Decision**: RISKY - need 42% more sales to break even. Only run if confident the promotion drives 50%+ volume increase.

### Scenario C: Switch to free shipping (absorb $6.50 cost)

**New Analysis**:
- New Variable Cost: $35.00/mat (add $6.50 shipping)
- Contribution Margin: $24.99 per mat (41.7%)
- Break-Even Units: 721 mats/month
- **Decision**: VIABLE if volume increases 11%+ (721 vs 650). Test with small customer segment first.

---

## 📊 Product Portfolio Analysis

Use Margin Hunter to compare multiple products side-by-side:

| Product | Price | Variable Cost | Margin | Break-Even (units) | Status |
|---------|-------|---------------|--------|-------------------|--------|
| **Yoga Mat** | $59.99 | $28.50 | $31.49 (52.5%) | 572/mo | ✅ Keep (hero) |
| Yoga Block | $19.99 | $12.00 | $7.99 (40%) | 2,253/mo | ⚠️ Low margin, high volume needed |
| Resistance Bands | $29.99 | $9.50 | $20.49 (68.3%) | 879/mo | ✅ Keep (high margin) |
| Foam Roller | $39.99 | $24.00 | $15.99 (40%) | 1,126/mo | ❌ Cut (low margin, slow seller) |

**Portfolio Optimization**:
- **Double down** on resistance bands (68% margin)
- **Maintain** yoga mats (hero product, brand anchor)
- **Promote** yoga blocks in bundles (increase AOV to offset low margin)
- **Discontinue** foam roller (40% margin, not moving at volume)

---

## 🚀 Recommended Actions

### Immediate (Week 1)
1. **Audit all products** - run each SKU through Margin Hunter
2. **Identify losers** - products below break-even or with <30% margin
3. **Calculate true shipping costs** - use actual carrier rates by zone/weight

### Short-term (Month 1)
1. **Renegotiate supplier pricing** - armed with break-even data, push for 5-10% COGS reduction
2. **Test pricing changes** - increase hero products by 5-10%, monitor conversion rate
3. **Optimize fulfillment** - switch to cheaper carrier, negotiate 3PL rates, or bring in-house

### Strategic (Quarter 1)
1. **Implement dynamic pricing** - seasonal pricing, flash sales, bundle discounts (model each)
2. **Focus on high-margin SKUs** - allocate marketing spend to products with 60%+ margins
3. **Subscription model** - test recurring revenue (e.g., "Mat Club" $49/month membership)

---

## 🎓 E-Commerce-Specific Considerations

### Why E-Commerce has LOWER contribution margins (30-60%)
- High variable costs (shipping, returns, payment processing are per-transaction)
- Marketplace fees eat into margin (Amazon takes 15%, Etsy 6.5%)
- Returns are common (apparel = 20-30% return rate)
- Customer acquisition cost (CAC) often included as variable if using paid ads

### Why E-Commerce needs HIGH volume
- Lower per-unit margins require more sales to cover fixed costs
- Inventory risk (unsold products = dead capital)
- Seasonal fluctuations (Q4 holiday spike, Q1 slowdown)

### Key E-Commerce Metrics to Track Alongside Margin Hunter
- **Customer Lifetime Value (LTV)**: Average customer buys X times over Y months
- **Repeat Purchase Rate**: % of customers who buy again (target: 30%+)
- **AOV (Average Order Value)**: Bundle products to increase margin capture
- **Inventory Turnover**: How many times per year you sell through inventory (target: 6-12x)

---

## 🧮 Advanced Use Case: Amazon FBA Profitability

### Scenario: Selling the same yoga mat on Amazon FBA

| Parameter | Amazon FBA | D2C Website |
|-----------|-----------|-------------|
| **Selling Price** | $59.99 | $59.99 |
| **Product Cost** | $18.00 | $18.00 |
| **Referral Fee (15%)** | $9.00 | $0.00 (no marketplace) |
| **FBA Fee** | $6.18 | $0.00 |
| **Shipping** | $0.00 (included in FBA) | $6.50 |
| **Payment Processing** | $0.00 (included) | $2.04 |
| **Pick & Pack** | $0.00 (included in FBA) | $0.76 |
| **Returns** | $1.80 (3% FBA rate) | $1.20 |
| **Total Variable Cost** | $35.98 | $28.50 |
| **Contribution Margin** | $24.01 (40%) | $31.49 (52.5%) |

**Break-Even Analysis**:
- **Amazon FBA**: 750 units/month (higher due to fees)
- **D2C Website**: 572 units/month

**Decision**: D2C is MORE profitable per unit, but Amazon provides volume. Optimal strategy: use Amazon for customer acquisition, convert to D2C for repeat purchases.

---

## 📁 Template Inputs (Copy to Margin Hunter)

### Product-Level Analysis
```
Unit Selling Price: $59.99
Unit Variable Cost: $28.50
Total Fixed Costs: $18,000.00
Target Profit: $8,000.00
Current Sales (Units): [Your actual monthly sales]
```

### Promotion Scenario Analysis
```
Unit Selling Price: $47.99 (20% off)
Unit Variable Cost: $28.50 (unchanged)
Total Fixed Costs: $18,000.00
Target Profit: $0.00 (break-even during promo)
Current Sales (Units): [Expected promo volume]
```

---

## 🔗 Additional Resources

- **Shopify Profit Calculator**: [link to tool]
- **Amazon FBA Fee Calculator**: [sellercentral.amazon.com/fba/profitabilitycalculator]
- **Shipping Cost Optimizer**: [link to carrier comparison tool]

---

**Try this scenario now**: [enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

**Questions?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues)

---

*Part of the Enterprise Hub Margin Hunter module | Built by Cayman Roden*
