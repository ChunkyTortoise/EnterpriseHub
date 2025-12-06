# 💼 Financial Analyst

> **Fundamental Analysis & Company Metrics** - Deep dive into company financials with AI-powered insights

[![Status](https://img.shields.io/badge/Status-Active-success)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![AI Powered](https://img.shields.io/badge/AI-Claude%203.5-purple)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-blue)](../LICENSE)

---

## 🎯 Business Value

The Financial Analyst module provides comprehensive fundamental analysis for any publicly traded company, enabling investors and analysts to make informed decisions based on key financial metrics, trends, and AI-powered insights.

### Target Audience
- **Individual Investors** - Research stocks before investing
- **Financial Analysts** - Quick fundamental analysis for client portfolios
- **Investment Advisors** - Due diligence and client presentations
- **Business Owners** - Competitive analysis and benchmarking

---

## 🚀 Key Features

### 1. **Company Overview**
- Company name, sector, industry, country
- Business summary (300 characters preview)
- Website link
- Market positioning information

### 2. **Key Financial Metrics**
Instant view of critical metrics:
- **Market Capitalization** - Company size and valuation
- **P/E Ratio** - Price-to-earnings valuation metric
- **EPS (Earnings Per Share)** - Profitability indicator
- **Dividend Yield** - Income potential for investors

### 3. **🤖 AI Insights (NEW)**
Claude-powered financial analysis providing:
- **Financial Health Assessment** (3-5 bullet points)
  - Overall financial health evaluation
  - Profitability analysis
  - Liquidity assessment
  - Growth trajectory
- **Key Risks** (2-3 bullet points)
  - Potential concerns and red flags
  - Industry-specific risks
  - Financial vulnerabilities
- **Key Opportunities** (2-3 bullet points)
  - Growth opportunities
  - Competitive advantages
  - Market positioning strengths

**Toggle Feature**: Enable/disable AI insights with one click
**Graceful Fallback**: Works without API key (shows toggle option when available)

### 4. **Financial Performance Charts**
Interactive visualizations:
- **Revenue vs Net Income** - Annual comparison chart
- **Profitability Ratios**:
  - Net Profit Margin
  - Gross Margin
  - YoY Revenue Growth

### 5. **Detailed Financial Statements**
Tabbed view of complete financial data:
- **Income Statement** - Revenue, expenses, net income
- **Balance Sheet** - Assets, liabilities, equity
- **Cash Flow** - Operating, investing, financing activities

---

## 💡 How to Use

### Basic Analysis (No API Key Required)
1. Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. View company overview and key metrics
3. Analyze financial performance charts
4. Explore detailed financial statements

### AI-Enhanced Analysis (Requires API Key)
1. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
   Or add it in the Content Engine module first (stored in session state)

2. Enter ticker symbol
3. **Toggle "Enable AI Insights"** to activate Claude analysis
4. Review AI-generated insights:
   - Financial health assessment
   - Key risks to watch
   - Key opportunities to leverage

### Example Use Cases

**Use Case 1: Pre-Investment Research**
```
Ticker: NVDA
Action: Enable AI Insights
Result: Understand NVIDIA's financial position, growth trajectory,
        and risk factors before investing
```

**Use Case 2: Portfolio Review**
```
Ticker: Portfolio holdings (one at a time)
Action: Compare key metrics and AI insights
Result: Identify strongest/weakest positions
```

**Use Case 3: Competitive Analysis**
```
Tickers: AAPL, MSFT, GOOGL (analyze separately)
Action: Compare metrics and AI assessments
Result: Benchmark companies against each other
```

---

## 🛠️ Technical Details

### Data Sources
- **yfinance API** - Real-time company info and financials
- **Claude 3.5 Sonnet** - AI-powered financial analysis

### Key Metrics Calculated
```python
# Net Profit Margin
net_margin = (net_income / revenue) * 100

# Gross Margin
gross_margin = (gross_profit / revenue) * 100

# YoY Revenue Growth
revenue_growth = ((current_revenue - prior_revenue) / prior_revenue) * 100
```

### AI Insights Generation
The module builds a comprehensive financial summary including:
- Company basics (name, sector, industry)
- Key valuation metrics (market cap, P/E, EPS)
- Revenue and profitability trends
- Year-over-year growth rates

Claude then analyzes this data to provide:
- Context-aware financial assessment
- Risk identification based on metrics
- Opportunity spotting from growth trends

### Error Handling
- Invalid ticker symbols show user-friendly error
- Missing financial data handled gracefully
- API errors fall back to basic analysis
- Graceful degradation when API key unavailable

---

## 📊 Example Output

### Company: Apple Inc. (AAPL)

**Key Metrics:**
- Market Cap: $2,800.00B
- P/E Ratio: 28.50
- EPS: $6.42
- Dividend Yield: 0.45%

**AI Insights (Sample):**

**Financial Health Assessment:**
- Strong balance sheet with $2.8T market capitalization and consistent profitability
- Net profit margin of 25.1% indicates exceptional operational efficiency
- Revenue growth of 5.3% YoY demonstrates continued market expansion
- High P/E ratio of 28.5 reflects market confidence in future growth

**Key Risks:**
- Premium P/E valuation leaves limited margin for execution misses
- Revenue growth has decelerated from prior years, suggesting market maturation
- High dependence on iPhone sales creates product concentration risk

**Key Opportunities:**
- Services segment growth outpacing hardware, improving margin profile
- Strong brand loyalty and ecosystem lock-in support pricing power
- Massive cash position enables strategic M&A and shareholder returns

---

## 🔑 API Key Setup

### Option 1: Environment Variable
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxx"
```

### Option 2: Via Content Engine Module
1. Go to Content Engine module
2. Enter API key in the setup form
3. Key is stored in session state for all modules

### Getting an API Key
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up for free ($5 credit included)
3. Create an API key
4. Estimated cost: ~$0.01 per company analysis

---

## 🧪 Testing

The module includes comprehensive tests:
- Company info display
- Key metrics calculation
- AI insights generation
- Error handling
- API key management

Run tests:
```bash
pytest tests/test_financial_analyst.py -v
```

---

## 📈 Future Enhancements

- **Historical trend charts** - Multi-year metric trends
- **Peer comparison** - Side-by-side company analysis
- **Alerts** - Notify when metrics cross thresholds
- **Export reports** - PDF/Excel financial reports
- **Custom metrics** - User-defined ratios and calculations

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional financial metrics
- Enhanced visualizations
- More sophisticated AI prompts
- Peer comparison features

---

## 📝 License

MIT License - See [LICENSE](../LICENSE) for details

---

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check existing issues or open a new one
- **Feature Requests**: Tag with `enhancement` label

---

**Last Updated:** December 2024 | **Version:** 2.0.0 (AI-Enhanced)
