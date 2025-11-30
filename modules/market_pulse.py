"""
Market Pulse module for stock market analysis.

Provides interactive stock data visualization with technical indicators
including price charts, RSI, MACD, and volume analysis.
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional

from utils.data_loader import get_stock_data, calculate_indicators
from utils.exceptions import InvalidTickerError, DataFetchError, DataProcessingError
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def render() -> None:
    """
    Render the Market Pulse module interface.
    
    Displays an interactive stock analysis dashboard with:
    - Ticker selection and time period controls
    - Current price metrics
    - 4-panel technical analysis chart (Price/MA, RSI, MACD, Volume)
    """
    st.title("📊 Market Pulse")
    
    # User input controls
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("Ticker Symbol", value="SPY").upper()
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)
    
    if not ticker:
        st.warning("⚠️ Please enter a ticker symbol")
        return
    
    # Fetch and display data
    try:
        with st.spinner(f"Fetching data for {ticker}..."):
            logger.info(f"User requested data for {ticker}")
            
            # Get stock data
            df = get_stock_data(ticker, period=period, interval=interval)
            
            if df is None or df.empty:
                st.error(f"❌ No data found for {ticker}. Please verify the ticker symbol.")
                return
            
            # Calculate indicators
            df = calculate_indicators(df)
            
            # Display current metrics
            _display_metrics(df, ticker)
            
            # Create and display chart
            fig = _create_technical_chart(df, ticker)
            st.plotly_chart(fig, use_container_width=True)
            
            logger.info(f"Successfully displayed chart for {ticker}")
                
    except InvalidTickerError as e:
        logger.warning(f"Invalid ticker: {e}")
        st.error(f"❌ {str(e)}")
        st.info("💡 **Tip:** Make sure you're using the correct ticker symbol (e.g., AAPL for Apple Inc.)")
        
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        st.error(f"❌ Failed to fetch data: {str(e)}")
        st.info("🔄 **Try:** Refreshing the page or selecting a different time period")
        
    except DataProcessingError as e:
        logger.error(f"Data processing error: {e}")
        st.error(f"❌ Error processing data: {str(e)}")
        
    except Exception as e:
        logger.error(f"Unexpected error in market_pulse: {str(e)}", exc_info=True)
        st.error(f"❌ An unexpected error occurred. Please try again.")
        if st.checkbox("Show error details"):
            st.exception(e)


def _display_metrics(df: pd.DataFrame, ticker: str) -> None:
    """
    Display current price metrics.
    
    Args:
        df: DataFrame with stock data
        ticker: Stock ticker symbol
    """
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        delta = latest['Close'] - prev['Close']
        delta_percent = (delta / prev['Close']) * 100
        
        st.metric(
            label=f"{ticker} Price", 
            value=f"${latest['Close']:.2f}", 
            delta=f"{delta:.2f} ({delta_percent:.2f}%)"
        )
    except Exception as e:
        logger.error(f"Error displaying metrics: {e}")
        st.warning("⚠️ Could not display price metrics")


def _create_technical_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Create a 4-panel technical analysis chart.
    
    Panels:
    1. Candlestick price chart with 20-day MA
    2. RSI (Relative Strength Index)
    3. MACD with signal line  
    4. Volume bars
    
    Args:
        df: DataFrame with OHLCV data and indicators
        ticker: Stock ticker symbol
    
    Returns:
        Plotly Figure object with 4 subplots
    """
    # Create 4-panel chart
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{ticker} Price & MA", "RSI", "MACD", "Volume")
    )
    
    # Panel 1: Price and MA
    fig.add_trace(go.Candlestick(
        x=df.index, 
        open=df['Open'], 
        high=df['High'],
        low=df['Low'], 
        close=df['Close'], 
        name="Price"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['MA20'], 
        line=dict(color='orange', width=1), 
        name="MA 20"
    ), row=1, col=1)
    
    # Panel 2: RSI
    fig.add_trace(
        go.Scatter(
            x=df.index, 
            y=df['RSI'], 
            name="RSI", 
            line=dict(color='purple')
        ), 
        row=2, col=1
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    # Panel 3: MACD
    fig.add_trace(
        go.Scatter(
            x=df.index, 
            y=df['MACD'], 
            name="MACD", 
            line=dict(color='blue')
        ), 
        row=3, col=1
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, 
            y=df['Signal'], 
            name="Signal", 
            line=dict(color='orange')
        ), 
        row=3, col=1
    )
    
    # Panel 4: Volume
    colors = [
        'green' if row['Open'] - row['Close'] >= 0 else 'red' 
        for index, row in df.iterrows()
    ]
    fig.add_trace(
        go.Bar(
            x=df.index, 
            y=df['Volume'], 
            name="Volume", 
            marker_color=colors
        ), 
        row=4, col=1
    )
    
    # Update layout
    fig.update_layout(
        height=900, 
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False
    )
    
    return fig

