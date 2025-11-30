import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random

# Import utility modules
try:
    from utils.config import BASE_PRICES, VOLATILITY, INDICATORS, CHART_CONFIG
    from utils.data_generator import generate_market_data
    from utils.indicators import add_all_indicators
    USE_UTILS = True
except ImportError:
    USE_UTILS = False  # Fallback to inline functions

# Optional: yfinance for real market data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# ENTERPRISE CONFIGURATION
st.set_page_config(
    page_title="Unified Enterprise Hub | Cayman Roden",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SIDEBAR NAVIGATION
st.sidebar.title("🚀 Enterprise Hub")
st.sidebar.markdown("**By Cayman Roden**")
page = st.sidebar.radio(
    "Navigate:",
    ["🏠 Overview", "📊 Market Pulse", "💼 Financial Analyst", 
     "💰 Margin Hunter", "🤖 Agent Logic", "✍️ Content Engine"]
)

# DATA SOURCE TOGGLE
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Data Source")

if YFINANCE_AVAILABLE:
    use_real_data = st.sidebar.checkbox(
        "🌐 Use Real Market Data",
        value=False,
        help="Fetch live data from Yahoo Finance (requires internet)"
    )
    if use_real_data:
        st.sidebar.success("📊 Live data mode active")
    else:
        st.sidebar.info("🎲 Demo data mode")
else:
    use_real_data = False
    st.sidebar.warning("⚠️ yfinance not available\nUsing demo data")

# ENHANCED DATA GENERATOR with OHLCV
def get_market_data_with_fallback(symbol, days=30, use_real=False):
    """Fetch real data from yfinance or fallback to generator."""
    if use_real and YFINANCE_AVAILABLE:
        try:
            ticker_map = {"BTC": "BTC-USD", "ETH": "ETH-USD", "AAPL": "AAPL", "TSLA": "TSLA"}
            ticker = ticker_map.get(symbol, symbol)
            yf_data = yf.download(ticker, period=f"{days}d", progress=False)
            if not yf_data.empty:
                df = yf_data.reset_index()
                df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                df['Returns'] = df['Close'].pct_change()
                if USE_UTILS:
                    df = add_all_indicators(df)
                else:
                    delta = df['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    df['RSI'] = 100 - (100 / (1 + (gain / (loss.replace(0, 1e-10)))))
                    df['MA7'] = df['Close'].rolling(window=7).mean()
                    df['MA30'] = df['Close'].rolling(window=30).mean()
                    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                    df['MACD'] = exp1 - exp2
                    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                    df['Volatility'] = df['Returns'].rolling(window=7).std() * np.sqrt(365) * 100
                st.toast(f"✅ Real {symbol} data loaded", icon="📈")
                return df
        except Exception as e:
            st.warning(f"⚠️ Real data failed: {str(e)[:30]}... Using demo.")
    return generate_market_data_advanced(symbol, days)

# ENHANCED DATA GENERATOR with OHLCV
def generate_market_data_advanced(symbol, days=30):
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]


    
    base_prices = {"BTC": 43000, "ETH": 2300, "AAPL": 185, "TSLA": 245}
    base_price = base_prices[symbol]
    volatility = {"BTC": 0.03, "ETH": 0.04, "AAPL": 0.02, "TSLA": 0.035}[symbol]
    
    data = []
    current = base_price
    
    for i in range(days):
        open_price = current
        daily_change = random.uniform(-volatility, volatility)
        close_price = open_price * (1 + daily_change)
        high_price = max(open_price, close_price) * random.uniform(1.0, 1.02)
        low_price = min(open_price, close_price) * random.uniform(0.98, 1.0)
        volume = random.uniform(1000000, 5000000)
        
        data.append({
            'Date': dates[i],
            'Open': open_price,
            'High': high_price,
            'Low': low_price,
            'Close': close_price,
            'Volume': volume
        })
        current = close_price
    
    df = pd.DataFrame(data)
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['MA7'] = df['Close'].rolling(window=7).mean()
    df['MA30'] = df['Close'].rolling(window=30).mean()
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=7).std() * np.sqrt(365) * 100
    
    return df

if page == "🏠 Overview":
    st.title("The Unified Enterprise Hub")
    st.markdown("### 5 Mission-Critical Modules in One Platform")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Modules Deployed", "5", delta="100%")
    with col2:
        st.metric("Cloud-Native", "✓", delta="Zero Infrastructure")
    with col3:
        st.metric("Time to Value", "< 2 min", delta="-98% vs Legacy")
    
    st.success("**✅ Phase 2.5 ACTIVE:** Market Pulse upgraded with professional trading indicators!")
    
    st.markdown("---")
    st.markdown("### 📊 Available Modules")
    st.markdown("""
    - **Market Pulse** ⚡ *ENHANCED* - Candlesticks, RSI, MACD, Volume Analysis
    - **Financial Analyst** 🔜 Coming in Phase 3
    - **Margin Hunter** 🔜 Coming in Phase 3
    - **Agent Logic** 🔜 Coming in Phase 3
    - **Content Engine** 🔜 Coming in Phase 3
    """)

elif page == "📊 Market Pulse":
    st.title("📊 Market Pulse")
    st.markdown("### Professional Trading Intelligence Dashboard")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        asset_type = st.selectbox("Asset Type", ["Crypto", "Stocks"])
    with col2:
        if asset_type == "Crypto":
            symbol = st.selectbox("Select Asset", ["BTC", "ETH"])
        else:
            symbol = st.selectbox("Select Asset", ["AAPL", "TSLA"])
    with col3:
        time_range = st.selectbox("Time Range", ["7D", "30D", "90D"], index=1)
    
    days_map = {"7D": 7, "30D": 30, "90D": 90}
    days = days_map[time_range]
    
    df = get_market_data_with_fallback(symbol, days=days, use_real=use_real_data)
    
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1, 1])
    with col1:
        st.metric("Current Price", f"${current_price:,.2f}", f"{change_pct:+.2f}%")
    with col2:
        st.metric("24h High", f"${df['High'].iloc[-1]:,.2f}")
    with col3:
        st.metric("24h Low", f"${df['Low'].iloc[-1]:,.2f}")
    with col4:
        rsi_val = df['RSI'].iloc[-1]
        rsi_signal = "⚠️ OB" if rsi_val > 70 else ("⚠️ OS" if rsi_val < 30 else "")
        st.metric("RSI (14)", f"{rsi_val:.1f} {rsi_signal}")
    with col5:
        vol = df['Volatility'].iloc[-1]
        st.metric("Volatility", f"{vol:.1f}%")
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.45, 0.2, 0.2, 0.15],
        subplot_titles=(f"{symbol} Price & Moving Averages", "RSI (14)", "MACD", "Volume")
    )
    
    fig.add_trace(
        go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=symbol,
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['MA7'], name='MA7',
                   line=dict(color='#00D9FF', width=1)),
        row=1, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['MA30'], name='MA30',
                   line=dict(color='#FFA500', width=1)),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['RSI'], name='RSI',
                   line=dict(color='#9D4EDD', width=2)),
        row=2, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['MACD'], name='MACD',
                   line=dict(color='#00D9FF', width=2)),
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['Date'], y=df['Signal'], name='Signal',
                   line=dict(color='#FFA500', width=1)),
        row=3, col=1
    )

                         # Volume bars
    colors = ['#00ff88' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ff4444' for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df['Date'], y=df['Volume'], name='Volume',
               marker=dict(color=colors)),
        row=4, col=1
    )
    
    fig.update_layout(
        template="plotly_dark",
        height=1000,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1)
    fig.update_yaxes(title_text="RSI", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=3, col=1)
              fig.update_yaxes(title_text="Volume", row=4, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 🚦 Trading Signals")
    col1, col2, col3 = st.columns(3)
    
    rsi_current = df['RSI'].iloc[-1]
    macd_current = df['MACD'].iloc[-1]
    signal_current = df['Signal'].iloc[-1]
    
    with col1:
        if rsi_current > 70:
            st.error("🔴 **RSI Signal:** Overbought - Consider selling")
        elif rsi_current < 30:
            st.success("🟢 **RSI Signal:** Oversold - Consider buying")
        else:
            st.info("🟡 **RSI Signal:** Neutral")
    
    with col2:
        if macd_current > signal_current:
            st.success("🟢 **MACD Signal:** Bullish crossover")
        else:
            st.error("🔴 **MACD Signal:** Bearish crossover")
    
    with col3:
        ma7 = df['MA7'].iloc[-1]
        ma30 = df['MA30'].iloc[-1]
        if ma7 > ma30:
            st.success("🟢 **MA Signal:** Short-term uptrend")
        else:
            st.error("🔴 **MA Signal:** Short-term downtrend")
    
    st.markdown("### 📈 Recent OHLC Data")
    display_df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].tail(10).copy()
    display_df['Open'] = display_df['Open'].apply(lambda x: f"${x:,.2f}")
    display_df['High'] = display_df['High'].apply(lambda x: f"${x:,.2f}")
    display_df['Low'] = display_df['Low'].apply(lambda x: f"${x:,.2f}")
    display_df['Close'] = display_df['Close'].apply(lambda x: f"${x:,.2f}")
    display_df['Volume'] = display_df['Volume'].apply(lambda x: f"{x:,.0f}")
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(display_df.sort_values('Date', ascending=False), use_container_width=True)
    
    st.info("💡 **Phase 2.5 Features:** Candlestick charts, RSI, MACD, Moving Averages, Trading Signals. Phase 3: Live API integration.")

else:
    st.title(page)
    st.warning(f"⏳ **{page}** module pending Phase 3 deployment.")
    st.markdown("### Coming Soon")
    st.markdown("""
    This module is scheduled for Phase 3 development. Current roadmap:
    - **Phase 1:** ✅ Container & deployment infrastructure
    - **Phase 2:** ✅ Market Pulse basic visualization
    - **Phase 2.5:** ✅ Professional trading indicators
    - **Phase 3:** 🔜 Live APIs + Remaining 4 modules
    """)
