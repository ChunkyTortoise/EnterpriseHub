# 📊 Market Pulse

> **Technical Analysis & Stock Visualization** - Real-time price charts with predictive indicators

[![Status](https://img.shields.io/badge/Status-Active-success)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![License](https://img.shields.io/badge/License-MIT-blue)](../LICENSE)

---

## 🎯 Business Value

Market Pulse transforms complex technical analysis into actionable insights, enabling traders and investors to make data-driven decisions with real-time price data, technical indicators, and predictive trend analysis.

### Target Audience
- **Day Traders** - Quick technical analysis for trading decisions
- **Swing Traders** - Identify entry/exit points with support/resistance
- **Long-term Investors** - Understand price trends and momentum
- **Technical Analysts** - Professional-grade charting and indicators

---

## 🚀 Key Features

### 1. **Real-Time Price Data**
- Current price with delta and percentage change
- Historical data: 1 month to 5 years
- Multiple intervals: Daily, Weekly, Monthly
- OHLCV (Open, High, Low, Close, Volume) data

### 2. **🔮 Predictive Indicators (NEW)**
Advanced trend prediction based on technical analysis:

#### **Trend Prediction**
- **Bullish 🐂** - Upward price movement expected
- **Bearish 🐻** - Downward price movement expected
- **Neutral ⚖️** - Sideways/consolidation expected

**Confidence Score**: 0-100% based on indicator strength

**Analysis Based On:**
- **RSI (Relative Strength Index)**
  - > 70: Overbought (bearish signal)
  - < 30: Oversold (bullish signal)
  - 50-70: Moderate bullish
  - 30-50: Moderate bearish

- **MACD (Moving Average Convergence Divergence)**
  - MACD > Signal: Bullish crossover
  - MACD < Signal: Bearish crossover
  - Strength measured by distance from signal line

#### **Support & Resistance Levels**
- **Support**: Recent 20-period low (potential floor price)
- **Resistance**: Recent 20-period high (potential ceiling price)
- Visual indicators on price chart

#### **Analysis Details (Expandable)**
- Current RSI value
- Current MACD value
- Signal line value
- Detailed reasoning for trend prediction

### 3. **4-Panel Technical Chart**

**Panel 1: Price & Moving Average**
- Candlestick chart (OHLC visualization)
- 20-day Moving Average (trend line)
- Support line (green dashed)
- Resistance line (red dashed)

**Panel 2: RSI**
- Relative Strength Index indicator
- Overbought line (70)
- Oversold line (30)
- Momentum visualization

**Panel 3: MACD**
- MACD line (blue)
- Signal line (orange)
- Crossover signals

**Panel 4: Volume**
- Volume bars
- Color-coded: Green (up day) / Red (down day)
- Volume trend analysis

---

## 💡 How to Use

### Basic Chart Analysis
1. Enter ticker symbol (e.g., SPY, QQQ, AAPL)
2. Select time period (1mo - 5y)
3. Select interval (1d, 1wk, 1mo)
4. Analyze the 4-panel chart

### Predictive Analysis (NEW)
1. Enter ticker and load data
2. Review **Predictive Indicators** section:
   - Check trend direction and confidence
   - Note support/resistance levels
   - Read detailed analysis reasoning
3. Validate predictions:
   - Compare with chart patterns
   - Look for confluence with other indicators
   - Consider price action relative to support/resistance

### Example Use Cases

**Use Case 1: Day Trading Entry**
```
Ticker: SPY
Period: 1mo
Interval: 1d

Analysis:
- Trend: Bullish (75% confidence)
- Current Price: $455.20
- Support: $448.50
- Resistance: $462.80

Action: Enter long position near support, target resistance
```

**Use Case 2: Swing Trade Setup**
```
Ticker: TSLA
Period: 3mo
Interval: 1d

Analysis:
- RSI: 32 (oversold)
- MACD: Bullish crossover
- Trend: Bullish (68% confidence)

Action: Potential reversal, watch for confirmation
```

**Use Case 3: Trend Confirmation**
```
Ticker: QQQ
Period: 6mo
Interval: 1wk

Analysis:
- Price above 20-MA
- RSI: 58 (neutral)
- MACD above signal
- Trend: Bullish (55% confidence)

Action: Hold long positions, uptrend intact
```

---

## 🛠️ Technical Details

### Data Sources
- **yfinance API** - Real-time and historical stock data

### Technical Indicators Calculated

#### RSI (Relative Strength Index)
```python
# 14-period RSI
gain = price_changes[price_changes > 0].mean()
loss = abs(price_changes[price_changes < 0].mean())
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
```

#### MACD (Moving Average Convergence Divergence)
```python
# 12-period EMA, 26-period EMA, 9-period signal
ema12 = df['Close'].ewm(span=12).mean()
ema26 = df['Close'].ewm(span=26).mean()
macd = ema12 - ema26
signal = macd.ewm(span=9).mean()
```

#### Moving Average
```python
# 20-period Simple Moving Average
ma20 = df['Close'].rolling(window=20).mean()
```

### Trend Prediction Algorithm

```python
def predict_trend(rsi, macd, signal):
    signals = []

    # RSI Analysis
    if rsi > 70: signals.append(-1)      # Overbought
    elif rsi < 30: signals.append(1)     # Oversold
    elif rsi > 50: signals.append(0.5)   # Moderate bullish
    else: signals.append(-0.5)           # Moderate bearish

    # MACD Analysis
    macd_diff = macd - signal
    if macd_diff > 1: signals.append(1)       # Strong bullish
    elif macd_diff > 0: signals.append(0.5)   # Moderate bullish
    elif macd_diff < -1: signals.append(-1)   # Strong bearish
    else: signals.append(-0.5)                # Moderate bearish

    # Calculate trend
    avg_signal = sum(signals) / len(signals)
    if avg_signal > 0.3: return "Bullish"
    elif avg_signal < -0.3: return "Bearish"
    else: return "Neutral"
```

### Support & Resistance Calculation
```python
# Based on 20-period lookback
support = df.tail(20)['Low'].min()
resistance = df.tail(20)['High'].max()
```

---

## 📊 Indicator Guide

### RSI (Relative Strength Index)
**What it measures:** Price momentum and overbought/oversold conditions

**Interpretation:**
- **70-100**: Overbought (potential reversal down)
- **30-70**: Normal range
- **0-30**: Oversold (potential reversal up)

**Trading signals:**
- RSI crosses above 30: Bullish
- RSI crosses below 70: Bearish
- Divergence from price: Strong reversal signal

### MACD (Moving Average Convergence Divergence)
**What it measures:** Trend direction and momentum

**Interpretation:**
- **MACD > Signal**: Bullish momentum
- **MACD < Signal**: Bearish momentum
- **Distance from signal**: Strength of trend

**Trading signals:**
- MACD crosses above signal: Buy signal
- MACD crosses below signal: Sell signal
- Histogram expanding: Trend strengthening

### Support & Resistance
**What they measure:** Price levels where buying/selling pressure is strong

**Interpretation:**
- **Support**: Price floor where buyers step in
- **Resistance**: Price ceiling where sellers emerge
- **Breakout**: Price moves beyond support/resistance

**Trading signals:**
- Price bounces off support: Buy opportunity
- Price rejected at resistance: Sell opportunity
- Break above resistance: Bullish breakout
- Break below support: Bearish breakdown

---

## 🎓 Trading Tips

### 1. **Confluence is Key**
Don't rely on a single indicator:
- ✅ RSI oversold + MACD bullish crossover = Strong buy signal
- ✅ Price at support + Bullish trend = High probability entry
- ❌ RSI oversold alone = Weak signal

### 2. **Respect the Trend**
- In uptrends: Buy dips to support
- In downtrends: Sell rallies to resistance
- In neutral: Wait for breakout

### 3. **Risk Management**
- Use support as stop-loss for long positions
- Use resistance as stop-loss for short positions
- Never risk more than 2% per trade

### 4. **Timeframe Matters**
- Day trading: Use 1d interval
- Swing trading: Use 1d or 1wk interval
- Position trading: Use 1wk or 1mo interval

---

## ⚠️ Disclaimer

**Important:** Technical indicators are tools, not guarantees.

- Past performance does not guarantee future results
- All trading involves risk of loss
- Use predictive indicators as one input among many
- Always do your own research (DYOR)
- Consider fundamental analysis alongside technical

**Recommendation:** Use Market Pulse in combination with:
- Financial Analyst module (fundamentals)
- Agent Logic module (sentiment)
- Your own research and risk tolerance

---

## 🧪 Testing

The module includes comprehensive tests:
- Chart rendering
- Indicator calculation
- Trend prediction accuracy
- Support/resistance calculation
- Error handling

Run tests:
```bash
pytest tests/test_market_pulse.py -v
```

---

## 📈 Future Enhancements

- **More indicators** - Bollinger Bands, Fibonacci retracements
- **Pattern recognition** - Head & shoulders, triangles, flags
- **Multi-timeframe analysis** - Align signals across timeframes
- **Backtesting** - Test strategies on historical data
- **Alerts** - Notify when conditions are met

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Additional technical indicators
- Advanced pattern recognition
- Machine learning predictions
- Backtesting framework

---

## 📝 License

MIT License - See [LICENSE](../LICENSE) for details

---

## 🆘 Support

- **Issues**: Open a GitHub issue
- **Questions**: Check existing issues or open a new one
- **Feature Requests**: Tag with `enhancement` label

---

**Last Updated:** December 2024 | **Version:** 2.0.0 (Predictive Enhanced)
