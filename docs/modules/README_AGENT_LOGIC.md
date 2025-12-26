# 🤖 Agent Logic: Sentiment Scout

> **AI-Powered Market Sentiment Analysis** - Analyze news sentiment with TextBlob or Claude AI

[![Status](https://img.shields.io/badge/Status-Active-success)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![AI Powered](https://img.shields.io/badge/AI-Claude%203.5-purple)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/License-MIT-blue)](../LICENSE)

---

## 🎯 Business Value

Agent Logic (Sentiment Scout) quantifies market sentiment by analyzing news headlines, helping investors understand public perception and potential price movements before they happen. Sentiment often predicts price action, making this a critical tool for informed decision-making.

### Target Audience
- **News Traders** - Act on sentiment before price moves
- **Swing Traders** - Confirm trades with sentiment analysis
- **Long-term Investors** - Monitor company reputation and perception
- **Risk Managers** - Early warning system for negative sentiment

---

## 🚀 Key Features

### 1. **Dual Sentiment Analysis Modes**

#### **TextBlob Mode (Default)**
- Fast, free, no API key required
- NLP-based sentiment scoring
- Processes headlines in milliseconds
- Good for basic sentiment analysis

#### **🧠 Claude AI Mode (NEW)**
- Contextual, nuanced sentiment analysis
- Understands financial implications
- Provides reasoning for sentiment score
- Analyzes up to 10 most recent headlines
- Toggleable on/off with one click

### 2. **Sentiment Gauge Dashboard**
Visual sentiment score display:
- **-100 to 100 scale**
- **Color-coded zones:**
  - Red (-100 to -10): Bearish 🐻
  - Gray (-10 to 10): Neutral 😐
  - Green (10 to 100): Bullish 🐂

### 3. **AI Verdict**
Quick decision-making with:
- Overall sentiment (Bullish/Bearish/Neutral)
- Confidence percentage
- Number of articles analyzed
- Analysis method indicator

### 4. **🧠 AI Reasoning (Claude Mode Only)**
Expandable section showing:
- Why the sentiment was assigned
- Key themes identified in news
- Financial implications noted
- Market impact assessment

**Example Reasoning:**
> "The sentiment is bullish based on multiple positive earnings announcements and product launch coverage. Headlines emphasize strong revenue growth and market expansion. However, some articles mention regulatory concerns which temper the overall bullish assessment."

### 5. **News Feed with Sentiment**
Individual article analysis:
- Sentiment label (Positive/Negative/Neutral)
- Sentiment score (-1.0 to 1.0)
- Publisher information
- Publication timestamp
- Full article link
- Expandable article details

---

## 💡 How to Use

### Basic Sentiment Analysis (TextBlob)
1. Enter ticker symbol (e.g., TSLA, AAPL, NVDA)
2. Click analyze (or press Enter)
3. View sentiment gauge and verdict
4. Review individual news items
5. Click article links to read full stories

### AI-Enhanced Sentiment (Claude)
1. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
   Or add it in Content Engine module first

2. Enter ticker symbol
3. **Toggle "AI Sentiment (Claude)"** to activate
4. Wait for Claude to analyze (~2-3 seconds)
5. View enhanced sentiment with reasoning
6. Expand "AI Reasoning" to see detailed analysis

### Example Use Cases

**Use Case 1: News Trading**
```
Ticker: TSLA
Mode: Claude AI
Result: Bearish (-65%)

Reasoning: "Multiple reports of production delays and supply
chain issues. Negative regulatory headlines regarding autopilot
safety. Despite positive sales data, risk sentiment dominates."

Action: Consider short position or stay out
```

**Use Case 2: Earnings Confirmation**
```
Ticker: AAPL
Mode: Claude AI
Result: Bullish (82%)

Reasoning: "Strong earnings beat with positive forward guidance.
Multiple analyst upgrades and price target increases. Services
revenue growth highlighted across headlines."

Action: Confirm long position, earnings reaction positive
```

**Use Case 3: Risk Monitoring**
```
Ticker: Portfolio holdings (daily check)
Mode: TextBlob (fast scan)
Result: MSFT Neutral, GOOGL Bearish (-45%)

Action: Investigate GOOGL news, potential risk
```

**Use Case 4: Pre-Investment Due Diligence**
```
Ticker: NVDA (before buying)
Mode: Claude AI
Result: Bullish (75%)

Reasoning: "AI boom driving demand, chip shortage easing,
strong data center growth. Some profit-taking concerns but
overall outlook remains positive."

Action: Sentiment supports investment thesis
```

---

## 🛠️ Technical Details

### Data Sources
- **yfinance API** - Real-time news headlines
- **TextBlob** - Basic NLP sentiment analysis
- **Claude 3.5 Sonnet** - Advanced AI sentiment analysis

### TextBlob Sentiment Scoring
```python
# Polarity: -1.0 (negative) to 1.0 (positive)
blob = TextBlob(headline)
score = blob.sentiment.polarity

# Classification
if score > 0.1: "Positive"
elif score < -0.1: "Negative"
else: "Neutral"
```

### Claude AI Sentiment Analysis
```python
# Input: Up to 10 most recent headlines
# Output: JSON with structured analysis

{
    "overall_sentiment": "bullish|bearish|neutral",
    "confidence": 0-100,
    "reasoning": "Explanation...",
    "article_sentiments": [
        {
            "title": "headline",
            "sentiment": "positive|negative|neutral",
            "score": -1.0 to 1.0
        }
    ]
}
```

### Sentiment Aggregation
```python
# Average all article scores
avg_score = sum(article_scores) / len(articles)

# Verdict determination
if avg_score > 0.05: "Bullish 🐂"
elif avg_score < -0.05: "Bearish 🐻"
else: "Neutral 😐"
```

### Key Differences: TextBlob vs Claude

| Feature | TextBlob | Claude AI |
|---------|----------|-----------|
| **Speed** | Instant | 2-3 seconds |
| **Cost** | Free | ~$0.01 per analysis |
| **Context** | Word-based | Contextual |
| **Financial awareness** | None | High |
| **Reasoning** | No | Yes |
| **Accuracy** | Good | Excellent |
| **Nuance** | Limited | Advanced |

**When to use TextBlob:**
- Quick daily scans
- Multiple tickers at once
- Budget constraints
- Basic sentiment sufficient

**When to use Claude:**
- High-stakes decisions
- Earnings analysis
- Major news events
- Need for reasoning
- Complex situations

---

## 📊 Sentiment Interpretation Guide

### Sentiment Scores

**Bullish (Positive Sentiment)**
- Score: 0.05 to 1.0
- Indicates: Positive news, optimism, good outlook
- Consider: Long positions, holding, adding to positions
- Watch for: Overly positive (euphoria) at extremes

**Bearish (Negative Sentiment)**
- Score: -1.0 to -0.05
- Indicates: Negative news, pessimism, concerns
- Consider: Short positions, reducing exposure, caution
- Watch for: Panic selling at extremes (contrarian opportunity)

**Neutral**
- Score: -0.05 to 0.05
- Indicates: Mixed news, uncertainty, balance
- Consider: Wait for clearer signals
- Watch for: Breakout in either direction

### Confidence Levels

**High Confidence (70-100%)**
- Strong agreement across news sources
- Clear narrative (all positive or all negative)
- Action: Higher conviction in trades

**Medium Confidence (40-70%)**
- Mixed signals but leaning one direction
- Some contradictory headlines
- Action: Moderate position sizing

**Low Confidence (0-40%)**
- Highly mixed or neutral sentiment
- Conflicting news narratives
- Action: Wait for clarity or reduce exposure

---

## 🎓 Trading with Sentiment

### Sentiment-Price Relationship

**Leading Indicator:**
- Sentiment often changes before price
- Negative sentiment → Price may follow down
- Positive sentiment → Price may rally
- Use sentiment for early warnings

**Contrarian Signals:**
- Extreme bullish (>85%) → Potential top
- Extreme bearish (<-85%) → Potential bottom
- Most effective at market extremes

### Combining with Other Modules

**Best Practice: Multi-Factor Analysis**

1. **Market Pulse** - Technical setup
2. **Sentiment Scout** - Sentiment confirmation
3. **Financial Analyst** - Fundamental support

**Example Combined Analysis:**
```
NVDA Analysis:
├─ Market Pulse: Bullish trend (65% confidence)
├─ Sentiment Scout: Bullish sentiment (75%)
└─ Financial Analyst: Strong fundamentals, AI Insights positive

→ Strong Buy Signal (confluence across all factors)
```

### Risk Management

**Sentiment Divergence Warnings:**
- Price ↑ + Sentiment ↓ = Potential reversal
- Price ↓ + Sentiment ↑ = Potential bottom
- Watch for divergences between price and sentiment

---

## ⚠️ Important Considerations

### Limitations

1. **News Lag**: Headlines may trail price action
2. **Quality Variance**: Not all news sources equally reliable
3. **Context Missing**: Single headlines lack full context
4. **Manipulation**: Sentiment can be artificially created
5. **Recency Bias**: Only recent headlines analyzed

### Best Practices

✅ **Do:**
- Use sentiment as one input among many
- Combine with technical and fundamental analysis
- Look for extreme readings
- Monitor sentiment changes over time
- Verify with multiple sources

❌ **Don't:**
- Trade solely on sentiment
- Ignore price action
- Chase extreme sentiment
- React to every headline
- Neglect your own research

---

## 🔑 API Key Setup

### Option 1: Environment Variable
```bash
export ANTHROPIC_API_KEY="sk-ant-api03-xxx"
```

### Option 2: Via Content Engine Module
1. Go to Content Engine module
2. Enter API key in setup form
3. Key stored in session state for all modules

### Getting an API Key
1. Visit [console.anthropic.com](https://console.anthropic.com/)
2. Sign up (free $5 credit)
3. Create API key
4. Estimated cost: ~$0.01 per sentiment analysis

---

## 🧪 Testing

The module includes comprehensive tests:
- TextBlob sentiment analysis
- Claude AI sentiment analysis
- News fetching
- Error handling
- API key management
- Graceful fallbacks

Run tests:
```bash
pytest tests/test_agent_logic.py -v
```

---

## 📈 Future Enhancements

- **Sentiment history** - Track sentiment over time
- **Sentiment charts** - Visualize sentiment trends
- **Social media** - Twitter/Reddit sentiment
- **Entity recognition** - Identify key topics/people mentioned
- **Alerts** - Notify on sentiment changes
- **Batch analysis** - Multiple tickers at once
- **Historical correlation** - Sentiment vs price performance

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional data sources (Twitter, Reddit, StockTwits)
- Advanced NLP models
- Sentiment trend charts
- Sentiment alerts
- Batch processing

---

## 📝 License

MIT License - See [LICENSE](../LICENSE) for details

---

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check existing issues or open a new one
- **Feature Requests**: Tag with `enhancement` label

---

**Last Updated:** December 2024 | **Version:** 2.0.0 (Claude AI Enhanced)
