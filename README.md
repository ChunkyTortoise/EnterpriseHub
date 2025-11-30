# 🚀 Enterprise Hub

**Professional Trading Intelligence Platform** | Built with Streamlit, Plotly & Python

[![Live Demo](https://img.shields.io/badge/Live-Demo-brightgreen)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-red)](https://streamlit.io)

> A cloud-native enterprise dashboard featuring advanced cryptocurrency and stock market analysis with professional-grade technical indicators.

## 🎯 Overview

Enterprise Hub is a modular analytics platform designed for traders and data analysts. Phase 2.6 features the **Market Pulse** module - a comprehensive trading intelligence dashboard with real-time technical analysis.

### ✨ Key Features

#### 📊 Market Pulse Module
- **Multi-Asset Support**: BTC, ETH, AAPL, TSLA
- **Technical Indicators**:
  - RSI (Relative Strength Index) with overbought/oversold zones
  - MACD (Moving Average Convergence Divergence)
  - 7-day & 30-day Moving Averages
  - Volatility analysis (annualized)
- **Interactive Visualizations**: 3-panel Plotly charts with synchronized axes
- **Trading Signals**: Automated buy/sell/neutral recommendations
- **Time Range Selection**: 7D, 30D, 90D analysis periods
- **OHLC Data Table**: Historical price data with full formatting

## 🏗️ Architecture

```
enterprise-hub/
├── app.py              # Main Streamlit application (256 lines)
├── requirements.txt    # Python dependencies
├── packages.txt        # System packages (Graphviz)
└── Deploy.md          # Deployment instructions
```

### Tech Stack

- **Frontend**: Streamlit 1.28.0
- **Data Processing**: Pandas 2.0.0, NumPy 1.24.0
- **Visualization**: Plotly 5.17.0
- **Deployment**: Streamlit Cloud (auto-deploy from GitHub)

## 🚀 Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/ChunkyTortoise/enterprise-hub.git
cd enterprise-hub

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

Access at `http://localhost:8501`

### Cloud Deployment

Automatically deploys to Streamlit Cloud on push to `main` branch.

**Live URL**: [https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

## 📈 Technical Indicators Explained

### RSI (Relative Strength Index)
- **Range**: 0-100
- **Overbought**: > 70 (potential sell signal)
- **Oversold**: < 30 (potential buy signal)
- **Calculation**: 14-period momentum oscillator

### MACD
- **Components**: MACD line (12/26 EMA difference) & Signal line (9-period EMA)
- **Bullish Signal**: MACD crosses above Signal line
- **Bearish Signal**: MACD crosses below Signal line

### Moving Averages
- **MA7**: Short-term trend (7-day simple moving average)
- **MA30**: Mid-term trend (30-day simple moving average)
- **Golden Cross**: MA7 > MA30 (uptrend)
- **Death Cross**: MA7 < MA30 (downtrend)

## 🎨 Screenshots

### Market Pulse Dashboard
![Market Pulse](https://via.placeholder.com/800x400?text=Professional+Trading+Dashboard)

*Features: Real-time metrics, multi-panel charts, trading signals*

## 🗺️ Roadmap

### Phase 3 (Planned)
- [ ] Live API integration (CoinGecko, Alpha Vantage)
- [ ] Volume bars chart panel
- [ ] Bollinger Bands indicator
- [ ] CSV export functionality
- [ ] Performance metrics (Sharpe ratio, max drawdown)
- [ ] Multi-asset comparison mode

### Future Modules
- [ ] **Financial Analyst**: Company financial statement analysis
- [ ] **Margin Hunter**: Profit optimization calculator
- [ ] **Agent Logic**: AI reasoning visualization
- [ ] **Content Engine**: Automated content generation

## 👨‍💻 Author

**Cayman Roden** ([@ChunkyTortoise](https://github.com/ChunkyTortoise))

- 🎓 Data Analytics & BI Tools (Tableau, Power BI)
- 💹 Cryptocurrency Trading & Technical Analysis
- 🤖 AI/ML Enthusiast (LLM Research, Prompt Engineering)

## 📝 License

MIT License - feel free to use this project for learning or portfolio purposes.

## 🙏 Acknowledgments

- **Streamlit**: For the amazing Python web framework
- **Plotly**: For interactive charting capabilities
- **Open Source Community**: For inspiration and best practices

---

**Built with** ❤️ **using** [Perplexity AI](https://perplexity.ai) **for enhanced development workflow**
