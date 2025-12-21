# Frequently Asked Questions (FAQ)

## General Questions

### What is EnterpriseHub?
EnterpriseHub is a unified business intelligence platform with 7 independent modules for financial analysis, content creation, data analytics, and marketing insights. Built with Streamlit and powered by AI (Claude 3.5 Sonnet).

### Who is this for?
- **Business Analysts**: Financial modeling, CVP analysis, data profiling
- **Content Creators**: AI-powered LinkedIn post generation
- **Marketers**: Campaign analytics, ROI tracking, attribution models
- **Investors**: Stock analysis, technical indicators, AI insights
- **Data Scientists**: Statistical analysis, correlation studies

### Is it free to use?
Yes, the core application is free and open-source (MIT License). Some features require an Anthropic API key (Claude AI), which has a free tier.

---

## Installation & Setup

### How do I install EnterpriseHub?

```bash
# Clone the repository
git clone https://github.com/ChunkyTortoise/enterprise-hub.git
cd enterprise-hub

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Run the application
streamlit run app.py
```

### What Python version is required?
Python 3.8 or higher. Tested on Python 3.8, 3.9, 3.10, 3.11, and 3.13.

### Do I need an API key?
Optional. The application works without API keys, but some features require:
- **ANTHROPIC_API_KEY**: For AI-powered features (Content Engine, Financial Analyst AI insights, Agent Logic Claude mode)

Free features work without any API key (TextBlob sentiment, all other modules).

### How do I get an Anthropic API key?
1. Visit https://console.anthropic.com/
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key
5. Add to `.env` file: `ANTHROPIC_API_KEY=sk-ant-xxx...`

---

## Usage Questions

### Which module should I use for...?

| Need | Module | Description |
|------|--------|-------------|
| Break-even analysis | Margin Hunter | CVP analysis, sensitivity heatmaps |
| LinkedIn posts | Content Engine | AI-generated posts (30 variations) |
| Stock analysis | Financial Analyst | Real-time data + AI insights |
| Technical charts | Market Pulse | RSI, MACD, trend predictions |
| Campaign tracking | Marketing Analytics | Multi-channel ROI, attribution |
| Data profiling | Data Detective | Statistical analysis, correlations |
| Sentiment analysis | Agent Logic | Dual-mode (TextBlob + Claude) |

### Can I use multiple modules together?
Yes! All modules are independent. Open multiple browser tabs to use different modules simultaneously.

### How do I export results?
- **Margin Hunter**: CSV export button for scenario analysis
- **Content Engine**: Copy/paste generated posts
- **Financial Analyst**: Screenshot charts or copy metrics
- **Market Pulse**: Screenshot technical charts
- **Data Detective**: Copy statistical summaries
- **Marketing Analytics**: Screenshot dashboards

PDF/Excel export for all modules is planned for future releases.

### Does it work offline?
Partially:
- **Works offline**: Margin Hunter, Data Detective (with pre-loaded data), Marketing Analytics
- **Requires internet**: Financial Analyst, Market Pulse (Yahoo Finance API), Content Engine (Claude API), Agent Logic (Claude mode)

---

## Technical Questions

### How is data stored?
EnterpriseHub is stateless. No data is permanently stored:
- **Session data**: Stored in Streamlit session state (browser memory)
- **API responses**: Not cached (except Yahoo Finance with TTL)
- **User data**: Never leaves your machine unless calling external APIs

### Is my data secure?
Yes:
- **API keys**: Stored in `.env` file (gitignored), never logged or displayed
- **Financial data**: Fetched from Yahoo Finance (public data)
- **User inputs**: Not transmitted anywhere except to APIs you explicitly call (Claude, Yahoo Finance)
- **No tracking**: No analytics, no telemetry, no data collection

### Can I deploy this to production?
Yes! See `Deploy.md` for instructions. Recommended platforms:
- **Streamlit Cloud**: Free tier available, easy deployment
- **Heroku**: Good for custom domains
- **AWS/GCP/Azure**: Full control, requires more setup

### How do I run tests?
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific module tests
pytest tests/unit/test_content_engine.py -v

# Run integration tests only
pytest tests/integration/ -v
```

### How do I contribute?
See `CONTRIBUTING.md` for detailed guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run pre-commit hooks
6. Submit a pull request

---

## Feature-Specific Questions

### Content Engine

**Q: Why are my posts not generating?**
A: Check:
1. API key is set in `.env` file
2. API key is valid (test at https://console.anthropic.com/)
3. You have API credits remaining
4. No rate limit errors (check logs)

**Q: Can I customize the post templates?**
A: Yes! Edit `modules/content_engine.py` and add new templates to `POST_TEMPLATES` dict.

**Q: How many variations can I generate?**
A: 6 templates × 5 tones = 30 unique variations per topic.

### Financial Analyst

**Q: Why is stock data not loading?**
A: Check:
1. Ticker symbol is valid (e.g., AAPL, not Apple)
2. Stock market is open (or use historical data)
3. Internet connection is working
4. Yahoo Finance API is not down (check status)

**Q: What does "AI Insights" show?**
A: Claude analyzes your stock's financial health, key risks, and opportunities based on metrics, revenue, profitability, and market data.

**Q: Can I analyze multiple stocks at once?**
A: Not currently. Batch analysis is planned for future releases.

### Market Pulse

**Q: What indicators are available?**
A: RSI (Relative Strength Index), MACD (Moving Average Convergence Divergence), Volume, and custom support/resistance levels.

**Q: How accurate are the trend predictions?**
A: Predictions are probabilistic based on technical indicators. They are educational tools, not financial advice. Always do your own research.

**Q: Can I customize indicator periods?**
A: Not via UI currently. Edit `utils/indicators.py` to change default periods.

### Margin Hunter

**Q: Can I save my scenario analysis?**
A: Yes! Use the "Export to CSV" button to download your analysis.

**Q: Can I add custom industry templates?**
A: Yes! Add new markdown files to `scenarios/` directory following the existing template format.

### Agent Logic

**Q: What's the difference between TextBlob and Claude modes?**
A:
- **TextBlob**: Free, fast, basic sentiment scoring (-1 to +1)
- **Claude**: Premium, contextual, includes reasoning and confidence

**Q: Why use TextBlob when Claude is better?**
A: TextBlob is always available (no API key required) and provides instant results for simple sentiment analysis.

---

## Troubleshooting

### Application won't start

**Error**: `ModuleNotFoundError: No module named 'streamlit'`
**Solution**: Install dependencies: `pip install -r requirements.txt`

**Error**: `FileNotFoundError: [Errno 2] No such file or directory: '.env'`
**Solution**: Copy template: `cp .env.example .env`

### API Errors

**Error**: `AuthenticationError: Invalid API key`
**Solution**:
1. Check API key in `.env` file
2. Ensure no extra spaces or quotes
3. Verify key is active at https://console.anthropic.com/

**Error**: `RateLimitError: Rate limit exceeded`
**Solution**:
1. Wait 60 seconds and try again
2. Retry logic will automatically backoff (1s → 2s → 4s)
3. Upgrade API plan if frequently hitting limits

**Error**: `APIConnectionError: Connection error`
**Solution**:
1. Check internet connection
2. Verify API service is up (https://status.anthropic.com/)
3. Try again in a few minutes

### Tests Failing

**Error**: `ImportError: cannot import name 'X' from 'modules'`
**Solution**: Ensure you're in the project root and virtual environment is activated

**Error**: `Coverage warning: No data was collected`
**Solution**: Normal for `--collect-only`. Run actual tests: `pytest tests/`

### Deployment Issues

**Error**: `Requirements.txt not found` (Streamlit Cloud)
**Solution**: Ensure `requirements.txt` is in repository root

**Error**: `API key not working` (Production)
**Solution**:
1. Add API key to Streamlit Cloud secrets (not `.env`)
2. Format: `ANTHROPIC_API_KEY = "sk-ant-xxx..."`
3. Restart application

---

## Performance Questions

### Why is the app slow?
Possible causes:
1. **First load**: Streamlit initializes all modules (takes 2-5 seconds)
2. **API calls**: Claude API can take 3-10 seconds for complex requests
3. **Large datasets**: Data Detective with >10,000 rows may be slow
4. **Network**: Yahoo Finance API depends on internet speed

Tips to improve:
- Use caching for repeated analyses
- Reduce dataset size for testing
- Use free tier features when speed is critical

### Can I run this on a Raspberry Pi?
Yes, but with limitations:
- Works well on Raspberry Pi 4 (4GB RAM+)
- Slower on Raspberry Pi 3
- May struggle with large datasets
- AI features work fine (computation happens in cloud)

---

## Pricing Questions

### Is there a paid version?
No, EnterpriseHub is fully open-source and free. However, you pay for:
- **Anthropic API usage**: Pay-as-you-go, ~$3-5/million tokens (see pricing at https://anthropic.com/pricing)
- **Hosting** (if deploying): Streamlit Cloud free tier available

### How much does Claude API cost?
Typical costs:
- **Content Engine**: ~$0.003 per post generation
- **Financial Analyst**: ~$0.005 per AI insight
- **Agent Logic**: ~$0.002 per sentiment analysis

**Example**: 100 LinkedIn posts = ~$0.30

### Can I use Gemini instead of Claude?
The code has Gemini placeholders but is not currently implemented. Pull requests welcome!

---

## Roadmap & Feature Requests

### What's planned for future releases?
See our roadmap in `PROJECT_STATE.md`:
- Batch analysis (multiple tickers at once)
- Sentiment history charts
- Alert system (price/trend changes)
- PDF/Excel export for all modules
- Real-time WebSocket data feeds
- Machine learning models
- Social media sentiment (Twitter, Reddit)
- Backtesting framework

### How do I request a feature?
1. Check existing issues: https://github.com/ChunkyTortoise/enterprise-hub/issues
2. If not found, create a new issue with:
   - Clear title
   - Use case description
   - Expected behavior
   - Mockups (optional)

### Can I build my own module?
Yes! See `docs/ARCHITECTURE.md` for extension guidelines:
1. Create `modules/new_module.py` with `render()` function
2. Create `modules/README_NEW_MODULE.md`
3. Add tests to `tests/unit/test_new_module.py`
4. Submit pull request

---

## Support

### Where can I get help?
1. **Documentation**: Read README.md, CONTRIBUTING.md, docs/ARCHITECTURE.md
2. **Issues**: https://github.com/ChunkyTortoise/enterprise-hub/issues
3. **Discussions**: GitHub Discussions (coming soon)

### How do I report a bug?
1. Check if it's already reported
2. Create a new issue with:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Screenshots (if applicable)
   - Environment (OS, Python version)

### How do I report a security vulnerability?
**Do NOT create a public issue.** Email security details to the maintainers (see SECURITY.md).

---

## License & Legal

### What license is this under?
MIT License - You can use, modify, and distribute this software freely, even commercially. See LICENSE file for details.

### Can I use this for my business?
Yes! EnterpriseHub is licensed under MIT, which allows commercial use.

### Do I need to credit EnterpriseHub?
Not required, but appreciated! A link back to the repository helps others discover the project.

### Can I sell a modified version?
Yes, under MIT License. However, we encourage you to contribute improvements back to the community.

---

## Still have questions?

Open an issue: https://github.com/ChunkyTortoise/enterprise-hub/issues

---

Last Updated: December 6, 2025
