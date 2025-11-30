"""Configuration constants for Enterprise Hub.

Centralizes all magic numbers and configuration parameters
for easier maintenance and updates.
"""

# Market Data Configuration
BASE_PRICES = {
    "BTC": 95000,  # Bitcoin price as of Nov 2025
    "ETH": 3500,   # Ethereum price as of Nov 2025
    "AAPL": 185,   # Apple stock price
    "TSLA": 245    # Tesla stock price
}

VOLATILITY = {
    "BTC": 0.03,   # 3% daily volatility
    "ETH": 0.04,   # 4% daily volatility
    "AAPL": 0.02,  # 2% daily volatility
    "TSLA": 0.035  # 3.5% daily volatility
}

# Technical Indicator Parameters
INDICATORS = {
    "RSI_PERIOD": 14,     # Standard RSI period
    "RSI_OVERBOUGHT": 70, # Overbought threshold
    "RSI_OVERSOLD": 30,   # Oversold threshold
    "MACD_FAST": 12,      # MACD fast EMA
    "MACD_SLOW": 26,      # MACD slow EMA
    "MACD_SIGNAL": 9,     # MACD signal line
    "MA_SHORT": 7,        # Short-term moving average
    "MA_LONG": 30         # Long-term moving average
}

# Chart Configuration
CHART_CONFIG = {
    "HEIGHT": 900,
    "TEMPLATE": "plotly_dark",
    "ROW_HEIGHTS": [0.5, 0.25, 0.25],  # Price, RSI, MACD
    "VERTICAL_SPACING": 0.05
}

# Volume Configuration
VOLUME_RANGE = {
    "MIN": 1000000,
    "MAX": 5000000
}

# Asset Categories
CRYPTO_ASSETS = ["BTC", "ETH"]
STOCK_ASSETS = ["AAPL", "TSLA"]
