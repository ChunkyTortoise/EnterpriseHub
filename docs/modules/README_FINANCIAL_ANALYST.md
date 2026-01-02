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

### 5. **💰 DCF Valuation Model (NEW)**
Calculate intrinsic value using a configurable Discounted Cash Flow model:
- **Projected Cash Flows**: 10-year projections with variable growth rates.
- **Terminal Value**: Calculated using the Gordon Growth Model.
- **WACC & Margin of Safety**: Adjustable sliders to see valuation sensitivity.
- **Valuation Verdict**: Automatic "UNDERVALUED", "OVERVALUED", or "FAIRLY VALUED" assessment.

### 6. **Detailed Financial Statements**
Tabbed view of complete financial data:
- **Income Statement** - Revenue, expenses, net income
- **Balance Sheet** - Assets, liabilities, equity
- **Cash Flow** - Operating, investing, financing activities

### 7. **📥 Professional Exports**
- **CSV/Excel**: Export complete statements for offline analysis.
- **PDF Reports**: Generate professionally formatted financial reports.

---

## 💡 How to Use

### Basic Analysis (No API Key Required)
1. Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. View company overview and key metrics
3. Analyze financial performance charts
4. **Interactive DCF**: Adjust sliders in the DCF section to calculate your own fair value.
5. Explore detailed financial statements and export reports.

### AI-Enhanced Analysis (Requires API Key)
...
---

## 🛠️ Technical Details

### Architecture
The module follows a decoupled architecture for maintainability and testability:
- **`modules/financial_analyst_logic.py`**: Pure Python logic for financial math (DCFModel, growth rates). Zero UI dependencies.
- **`modules/financial_analyst.py`**: Streamlit-based UI layer that orchestrates data fetching and rendering.

### Data Sources
- **yfinance API** - Real-time company info and financials
- **Claude 3.5 Sonnet** - AI-powered financial analysis

### Core Calculations
The `DCFModel` class handles the heavy lifting:
```python
# Terminal Value (Gordon Growth)
terminal_fcf = current_fcf * (1 + terminal_growth / 100)
terminal_val = terminal_fcf / (discount_rate / 100 - terminal_growth / 100)
```

### AI Insights Generation
...
---

## 🧪 Testing

The module includes comprehensive tests:
- **Core Logic**: `tests/unit/test_financial_analyst_logic.py` (Pure math tests)
- **UI & Integration**: `tests/unit/test_financial_analyst.py` (Mocked Streamlit tests)

Run all module tests:
```bash
python3 -m pytest tests/unit/test_financial_analyst*
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
