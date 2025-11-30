# 🚀 Enterprise Hub

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **A unified platform for market analysis and enterprise tooling**  
> Built by [Cayman Roden](https://github.com/ChunkyTortoise) | Powered by Streamlit

---

## 📊 Overview

Enterprise Hub is a professional-grade web application that consolidates five mission-critical modules into a single, cloud-native platform. Designed for rapid deployment and zero infrastructure overhead, it delivers enterprise capabilities in under 2 minutes.

### ✨ Features

- **📊 Market Pulse** - Real-time stock data with technical indicators (RSI, MACD, Moving Averages, Volume)
- **💼 Financial Analyst** *(Coming Soon)* - Advanced financial modeling and analysis
- **💰 Margin Hunter** *(Coming Soon)* - Optimization algorithms for margin analysis
- **🤖 Agent Logic** *(Coming Soon)* - Intelligent automation workflows
- **✍️ Content Engine** *(Coming Soon)* - AI-powered content generation

### 🎯 Key Highlights

- ✅ **Cloud-Native** - Deploy to Streamlit Cloud in seconds
- ✅ **Modular Architecture** - Clean separation of concerns, easy to extend
- ✅ **Real-Time Data** - Live market data via Yahoo Finance API
- ✅ **Interactive Charts** - 4-panel technical analysis with Plotly
- ✅ **Responsive Design** - Works on desktop, tablet, and mobile

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- (Optional) Virtual environment tool (venv, conda, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ChunkyTortoise/enterprise-hub.git
   cd enterprise-hub
   ```

2. **Create and activate virtual environment** *(Recommended)*
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, manually navigate to the URL shown in your terminal

---

## 📁 Project Structure

```
enterprise-hub/
├── app.py                 # Main application entry point
├── requirements.txt       # Production dependencies
├── dev-requirements.txt   # Development dependencies
├── modules/              # Feature modules
│   ├── __init__.py
│   └── market_pulse.py   # Market analysis module
├── utils/                # Shared utilities
│   ├── data_loader.py    # Data fetching and processing
│   ├── logger.py         # Centralized logging
│   └── exceptions.py     # Custom exceptions
├── tests/                # Test suite
│   ├── test_data_loader.py
│   └── test_market_pulse.py
├── .github/workflows/    # CI/CD pipelines
│   └── ci.yml           # GitHub Actions workflow
├── .gitignore            # Git ignore patterns
├── LICENSE               # MIT License
├── CONTRIBUTING.md       # Contribution guidelines
├── SECURITY.md           # Security policy
└── README.md             # This file
```

---

## 🎨 Screenshots

### Market Pulse - Technical Analysis Dashboard
*Real-time stock charts with RSI, MACD, and volume indicators*

![Market Pulse Dashboard](assets/market-pulse-screenshot.png)
> *Coming soon: Add your screenshot to `/assets` folder*

---

## 🛠️ Technology Stack

- **Framework**: [Streamlit](https://streamlit.io) - Fast, beautiful web apps in Python
- **Data Source**: [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance market data
- **Charts**: [Plotly](https://plotly.com/python/) - Interactive visualizations
- **Technical Analysis**: [ta](https://github.com/bukosabino/ta) - Technical analysis library
- **Data Processing**: [Pandas](https://pandas.pydata.org/) - Data manipulation

---

## 📖 Usage Guide

### Market Pulse Module

1. **Select a ticker symbol** (e.g., SPY, AAPL, TSLA)
2. **Choose time period** (1 month to 5 years)
3. **Select interval** (daily, weekly, monthly)
4. **View interactive charts** with 4 panels:
   - **Panel 1**: Candlestick price chart with 20-day moving average
   - **Panel 2**: Relative Strength Index (RSI) with overbought/oversold levels
   - **Panel 3**: MACD with signal line
   - **Panel 4**: Volume bars (green/red based on price movement)

### Coming Soon

Additional modules are in active development:
- Financial Analyst - Deep-dive financial modeling
- Margin Hunter - Profitability optimization
- Agent Logic - Workflow automation
- Content Engine - AI content generation

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to get started.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Install development dependencies
   ```bash
   pip install -r dev-requirements.txt
   ```
4. Make your changes
5. Run tests and linting
   ```bash
   pytest
   flake8 .
   black --check .
   ```
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

---

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html
```

---

## 📦 Deployment

### Streamlit Cloud (Recommended)

1. Push your code to GitHub
2. Visit [share.streamlit.io](https://share.streamlit.io/)
3. Click "New app"
4. Select your repository, branch (`main`), and main file (`app.py`)
5. Click "Deploy!"

Your app will be live at `https://your-app-name.streamlit.app` in minutes.

### Docker *(Coming Soon)*

```bash
docker build -t enterprise-hub .
docker run -p 8501:8501 enterprise-hub
```

---

## 🔒 Security

For security concerns, please see our [Security Policy](SECURITY.md) and report vulnerabilities responsibly.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Cayman Roden**

- GitHub: [@ChunkyTortoise](https://github.com/ChunkyTortoise)
- Project Link: [https://github.com/ChunkyTortoise/enterprise-hub](https://github.com/ChunkyTortoise/enterprise-hub)

---

## 🙏 Acknowledgments

- [Streamlit](https://streamlit.io) for the amazing framework
- [yfinance](https://github.com/ranaroussi/yfinance) for free market data access
- [Plotly](https://plotly.com) for beautiful interactive charts

---

## 🗺️ Roadmap

- [x] Market Pulse module with technical indicators
- [x] 4-panel chart layout (Price, RSI, MACD, Volume)
- [ ] Financial Analyst module
- [ ] Margin Hunter module
- [ ] Agent Logic automation
- [ ] Content Engine
- [ ] User authentication
- [ ] Portfolio tracking
- [ ] Real-time alerts
- [ ] Mobile app (React Native)

---

<div align="center">
  <strong>⭐ Star this repository if you find it helpful!</strong>
  <br>
  <sub>Built with ❤️ using Streamlit</sub>
</div>
