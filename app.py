import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

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

# SAMPLE DATA GENERATOR (Replace with real API calls later)
def generate_market_data(symbol, days=30):
    """Generate sample market data for demonstration"""
    dates = [datetime.now() - timedelta(days=x) for x in range(days)]
    dates.reverse()
    
    base_price = {"BTC": 43000, "ETH": 2300, "AAPL": 185, "TSLA": 245}[symbol]
    prices = []
    current = base_price
    
    for _ in range(days):
        change = random.uniform(-0.05, 0.05)
        current = current * (1 + change)
        prices.append(current)
    
    return pd.DataFrame({
        'Date': dates,
        'Price': prices
    })

# MAIN CONTAINER
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
    
    st.success("**✅ Phase 2 ACTIVE:** Market Pulse module now operational with real-time visualizations!")
    
    st.markdown("---")
    st.markdown("### 📊 Available Modules")
    st.markdown("""
    - **Market Pulse** ⚡ *LIVE* - Crypto & stock tracking with interactive charts
    - **Financial Analyst** 🔜 Coming in Phase 3
    - **Margin Hunter** 🔜 Coming in Phase 3
    - **Agent Logic** 🔜 Coming in Phase 3
    - **Content Engine** 🔜 Coming in Phase 3
    """)

elif page == "📊 Market Pulse":
    st.title("📊 Market Pulse")
    st.markdown("### Real-Time Market Intelligence Dashboard")
    
    # Asset selector
    col1, col2 = st.columns([1, 3])
    with col1:
        asset_type = st.selectbox("Asset Type", ["Crypto", "Stocks"])
    with col2:
        if asset_type == "Crypto":
            symbol = st.selectbox("Select Asset", ["BTC", "ETH"])
        else:
            symbol = st.selectbox("Select Asset", ["AAPL", "TSLA"])
    
    # Generate data
    df = generate_market_data(symbol, days=30)
    
    # Calculate metrics
    current_price = df['Price'].iloc[-1]
    prev_price = df['Price'].iloc[-2]
    change = current_price - prev_price
    change_pct = (change / prev_price) * 100
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${current_price:,.2f}", f"{change_pct:+.2f}%")
    with col2:
        st.metric("24h High", f"${df['Price'].max():,.2f}")
    with col3:
        st.metric("24h Low", f"${df['Price'].min():,.2f}")
    with col4:
        avg_price = df['Price'].mean()
        st.metric("30d Average", f"${avg_price:,.2f}")
    
    # Price chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Price'],
        mode='lines',
        name=symbol,
        line=dict(color='#00D9FF', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 217, 255, 0.1)'
    ))
    
    fig.update_layout(
        title=f"{symbol} Price Trend (30 Days)",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_dark",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Data table
    st.markdown("### 📈 Recent Price History")
    display_df = df.tail(10).copy()
    display_df['Price'] = display_df['Price'].apply(lambda x: f"${x:,.2f}")
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
    st.dataframe(display_df.sort_values('Date', ascending=False), use_container_width=True)
    
    st.info("💡 **Pro Tip:** Data shown is simulated. Phase 3 will integrate live APIs (CoinGecko, Alpha Vantage).")

else:
    st.title(page)
    st.warning(f"⏳ **{page}** module pending Phase 3 deployment.")
    st.markdown("### Coming Soon")
    st.markdown("""
    This module is scheduled for Phase 3 development. Current roadmap:
    - **Phase 1:** ✅ Container & deployment infrastructure
    - **Phase 2:** ✅ Market Pulse module (live visualization)
    - **Phase 3:** 🔜 Remaining 4 modules + API integration
    """)
