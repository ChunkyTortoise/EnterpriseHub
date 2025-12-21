# 🧠 Smart Forecast Engine

> **AI-Powered Time Series Forecasting** - Predict future asset prices using Machine Learning

[![Status](https://img.shields.io/badge/Status-Active-success)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
[![License](https://img.shields.io/badge/License-MIT-blue)](../LICENSE)

---

## 🎯 Business Value

The Smart Forecast Engine bridges the gap between historical data and future insights. By leveraging Machine Learning (Random Forest) instead of simple moving averages, it captures complex non-linear relationships between technical indicators and price movements, allowing businesses and investors to model future price scenarios with greater sophistication.

### Target Audience
- **Financial Analysts** - Projecting future asset values
- **Portfolio Managers** - Scenario planning and risk assessment
- **Data Scientists** - Demonstrating ML application in finance
- **Strategic Planners** - Forecasting market trends

---

## 🚀 Key Features

### 1. **Machine Learning Core**
- **Random Forest Regressor**: An ensemble learning method that operates by constructing a multitude of decision trees at training time.
- **Robustness**: Less prone to overfitting than single decision trees.
- **Non-linear Relationships**: Captures complex patterns that linear models miss.

### 2. **Advanced Feature Engineering**
The engine automatically generates features from raw price data:
- **Technical Indicators**: RSI, MACD, Signal Line, SMA (20, 50).
- **Lag Features**: Uses past performance (`Close_Lag_1`, `Close_Lag_5`, etc.) to predict future values (Autoregression).
- **Volume Analysis**: Incorporates trading volume as a predictor of price momentum.

### 3. **Recursive Forecasting**
- **Multi-step Prediction**: Predicts not just the next day, but up to 90 days into the future.
- **Iterative Process**: Uses the prediction of day $t$ as the input for day $t+1$.
- **Volatility Integration**: Adds realistic market noise based on historical volatility to prevent "flat line" predictions.

### 4. **Model Transparency**
- **Accuracy Metrics**: Real-time $R^2$ (Coefficient of Determination) and MAE (Mean Absolute Error) calculation on test data.
- **Visual Confidence**: Plots historical data vs. AI forecast clearly.
- **Explainability**: "How this model works" section built directly into the UI.

---

## 💡 How to Use

1. **Select Asset**: Enter any valid ticker symbol (e.g., MSFT, NVDA, BTC-USD).
2. **Set Horizon**: Choose how far to predict (7 to 90 days) using the slider.
3. **Generate Forecast**: Click the button to trigger the training pipeline.
4. **Analyze Results**:
    - Check the **Model Accuracy ($R^2$)** to gauge reliability.
    - View the **Forecast Chart** to see the projected trend.
    - Use the **Mean Error** to understand average deviation.

---

## 🛠️ Technical Architecture

### Pipeline Steps

1. **Data Ingestion**: Fetches 2 years of daily data via `yfinance`.
2. **Feature Engineering**:
   - Calculates RSI, MACD, SMA using `utils.data_loader`.
   - Creates lag features (shifts data) to enable time-series learning.
3. **Data Splitting**:
   - 80% Training (First ~1.6 years)
   - 20% Validation (Last ~0.4 years) - *Time-series split (no shuffling)*
4. **Model Training**:
   - Trains `RandomForestRegressor(n_estimators=100)`.
5. **Recursive Prediction**:
   - Predicts day $t+1$.
   - Appends prediction to history.
   - Updates lag features.
   - Repeats for $N$ days.

### Code Snippet (Simplified)

```python
def _train_and_predict(df, future_days):
    # Feature Engineering
    feature_cols = ['RSI', 'MACD', 'SMA_20', 'Close_Lag_1', ...]
    X = df[feature_cols]
    y = df['Close'].shift(-1) # Target is next day's price

    # Train Model
    model = RandomForestRegressor()
    model.fit(X_train, y_train)

    # Recursive Forecast
    current_features = X.iloc[-1]
    predictions = []

    for _ in range(future_days):
        pred = model.predict([current_features])[0]
        predictions.append(pred)
        # Update features for next step...

    return predictions
```

---

## 🧪 Testing

The module includes unit tests for feature engineering, training logic, and UI rendering.

```bash
pytest tests/unit/test_smart_forecast.py -v
```

**Test Coverage:**
- `test_prepare_features`: Verifies lag creation and NaN handling.
- `test_train_and_predict`: Mocks Random Forest to ensure pipeline integrity.
- `test_render_flow`: Ensures UI components load without errors.

---

## ⚠️ Disclaimer

**Educational Purpose Only.**
This module demonstrates the application of Machine Learning to financial time-series data. Stock market movements are stochastic and influenced by factors outside of historical price data (news, macroeconomics).
**Do not use this tool for actual financial trading.**

---

## 📝 License

MIT License - See [LICENSE](../LICENSE) for details

---

**Last Updated:** December 2025 | **Version:** 1.0.0
