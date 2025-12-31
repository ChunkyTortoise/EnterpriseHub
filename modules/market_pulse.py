"""
Market Pulse module for stock market analysis.

Provides interactive stock data visualization with technical indicators
including price charts, RSI, MACD, and volume analysis.
"""

from datetime import datetime
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import utils.ui as ui
from utils.data_loader import calculate_indicators, get_stock_data
from utils.exceptions import DataFetchError, DataProcessingError, InvalidTickerError
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
    ui.section_header("Market Pulse", "Real-Time Technical Analysis Dashboard")

    # User input controls
    col1, col2 = st.columns([1, 3])
    with col1:
        ticker = st.text_input("Ticker Symbol", value="SPY").upper()
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=3)
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

        # Multi-ticker comparison
        st.markdown("---")
        st.markdown("**📊 Compare Tickers**")
        comparison_tickers = st.text_input(
            "Compare with (comma-separated)",
            placeholder="e.g., AAPL,MSFT,GOOGL",
            help="Enter ticker symbols separated by commas to overlay performance comparison",
        )

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

            # Display predictive indicators
            _display_predictive_indicators(df, ticker)

            # Create and display chart
            fig = _create_technical_chart(df, ticker)
            st.plotly_chart(fig, use_container_width=True)

            # Multi-ticker comparison
            if comparison_tickers:
                _display_comparison_chart(ticker, comparison_tickers, period, interval)

            # Export options
            _display_export_options(df, ticker)

            logger.info(f"Successfully displayed chart for {ticker}")

    except InvalidTickerError as e:
        logger.warning(f"Invalid ticker: {e}")
        st.error(f"❌ {str(e)}")
        st.info(
            "💡 **Tip:** Make sure you're using the correct ticker symbol "
            "(e.g., AAPL for Apple Inc.)"
        )

    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        st.error(f"❌ Failed to fetch data: {str(e)}")
        st.info("🔄 **Try:** Refreshing the page or selecting a different time period")

    except DataProcessingError as e:
        logger.error(f"Data processing error: {e}")
        st.error(f"❌ Error processing data: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error in market_pulse: {str(e)}", exc_info=True)
        st.error("❌ An unexpected error occurred. Please try again.")
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
        delta = latest["Close"] - prev["Close"]
        delta_percent = (delta / prev["Close"]) * 100

        ui.card_metric(
            label=f"{ticker} Price",
            value=f"${latest['Close']:.2f}",
            delta=f"{delta:.2f} ({delta_percent:.2f}%)",
        )
    except Exception as e:
        logger.error(f"Error displaying metrics: {e}")
        st.warning("⚠️ Could not display price metrics")


def _display_predictive_indicators(df: pd.DataFrame, ticker: str) -> None:
    """
    Display predictive indicators based on RSI and MACD.

    Args:
        df: DataFrame with stock data and technical indicators
        ticker: Stock ticker symbol
    """
    try:
        latest = df.iloc[-1]
        rsi = latest["RSI"]
        macd = latest["MACD"]
        signal = latest["Signal"]

        # Calculate trend prediction
        trend, confidence, reasoning = _predict_trend(rsi, macd, signal)

        # Calculate support/resistance levels
        support, resistance = _calculate_support_resistance(df)

        # Display in a compact format
        st.markdown("---")
        st.subheader("🔮 Predictive Indicators")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Trend prediction with color coding
            if trend == "Bullish":
                st.markdown(f"**Trend:** :green[{trend} 🐂]")
                st.progress(min(confidence / 100, 1.0))
            elif trend == "Bearish":
                st.markdown(f"**Trend:** :red[{trend} 🐻]")
                st.progress(min(confidence / 100, 1.0))
            else:
                st.markdown(f"**Trend:** :gray[{trend} ⚖️]")
                st.progress(0.5)

            st.caption(f"Confidence: {confidence:.0f}%")

        with col2:
            ui.card_metric("Support Level", f"${support:.2f}")
            st.caption("Potential floor price")

        with col3:
            ui.card_metric("Resistance Level", f"${resistance:.2f}")
            st.caption("Potential ceiling price")

        # Display reasoning
        with st.expander("📊 Analysis Details"):
            st.markdown(f"**RSI:** {rsi:.1f}")
            st.markdown(f"**MACD:** {macd:.2f}")
            st.markdown(f"**Signal Line:** {signal:.2f}")
            st.markdown(f"\n**Reasoning:** {reasoning}")

    except Exception as e:
        logger.error(f"Error displaying predictive indicators: {e}")
        st.warning("⚠️ Could not display predictive indicators")


def _predict_trend(rsi: float, macd: float, signal: float) -> tuple[str, float, str]:
    """
    Predict price trend based on RSI and MACD indicators.

    Args:
        rsi: Current RSI value
        macd: Current MACD value
        signal: Current Signal line value

    Returns:
        Tuple of (trend, confidence, reasoning)
        - trend: "Bullish", "Bearish", or "Neutral"
        - confidence: 0-100 confidence percentage
        - reasoning: Text explanation of the prediction
    """
    signals = []
    reasoning_parts = []

    # RSI Analysis
    if rsi > 70:
        signals.append(-1)  # Overbought - bearish signal
        reasoning_parts.append(f"RSI at {rsi:.1f} indicates overbought conditions")
    elif rsi < 30:
        signals.append(1)  # Oversold - bullish signal
        reasoning_parts.append(f"RSI at {rsi:.1f} indicates oversold conditions")
    elif rsi > 50:
        signals.append(0.5)  # Moderate bullish
        reasoning_parts.append(f"RSI at {rsi:.1f} shows moderate bullish momentum")
    else:
        signals.append(-0.5)  # Moderate bearish
        reasoning_parts.append(f"RSI at {rsi:.1f} shows moderate bearish momentum")

    # MACD Analysis
    macd_diff = macd - signal
    if macd_diff > 0:
        if macd_diff > 1:
            signals.append(1)  # Strong bullish
            reasoning_parts.append("MACD strongly above signal line (bullish crossover)")
        else:
            signals.append(0.5)  # Moderate bullish
            reasoning_parts.append("MACD above signal line (bullish)")
    else:
        if macd_diff < -1:
            signals.append(-1)  # Strong bearish
            reasoning_parts.append("MACD strongly below signal line (bearish crossover)")
        else:
            signals.append(-0.5)  # Moderate bearish
            reasoning_parts.append("MACD below signal line (bearish)")

    # Calculate overall signal
    avg_signal = sum(signals) / len(signals)

    # Determine trend and confidence
    if avg_signal > 0.3:
        trend = "Bullish"
        confidence = min(abs(avg_signal) * 100, 100)
    elif avg_signal < -0.3:
        trend = "Bearish"
        confidence = min(abs(avg_signal) * 100, 100)
    else:
        trend = "Neutral"
        confidence = 50

    reasoning = "; ".join(reasoning_parts)

    return trend, confidence, reasoning


def _calculate_support_resistance(df: pd.DataFrame, lookback: int = 20) -> tuple[float, float]:
    """
    Calculate support and resistance levels based on recent price action.

    Args:
        df: DataFrame with stock data
        lookback: Number of periods to look back for calculations

    Returns:
        Tuple of (support, resistance) price levels
    """
    try:
        # Use the most recent data
        recent_df = df.tail(lookback)

        # Support: recent low
        support = recent_df["Low"].min()

        # Resistance: recent high
        resistance = recent_df["High"].max()

        return support, resistance
    except Exception as e:
        logger.error(f"Error calculating support/resistance: {e}")
        # Return current price as fallback
        current_price = df.iloc[-1]["Close"]
        return current_price * 0.95, current_price * 1.05


def _create_technical_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """
    Create a 5-panel technical analysis chart.

    Panels:
    1. Candlestick price chart with 20-day MA, Bollinger Bands, support/resistance
    2. RSI (Relative Strength Index)
    3. MACD with signal line
    4. ATR (Average True Range) - volatility indicator
    5. Volume bars

    Args:
        df: DataFrame with OHLCV data and indicators
        ticker: Stock ticker symbol

    Returns:
        Plotly Figure object with 5 subplots
    """
    # Calculate support/resistance for visual indicators
    support, resistance = _calculate_support_resistance(df)

    # Create 5-panel chart
    fig = make_subplots(
        rows=5,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.45, 0.12, 0.12, 0.12, 0.19],
        subplot_titles=(f"{ticker} Price & MA", "RSI", "MACD", "ATR (Volatility)", "Volume"),
    )

    # Panel 1: Price and MA
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["MA20"],
            line=dict(color="orange", width=1),
            name="MA 20",
        ),
        row=1,
        col=1,
    )

    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_Upper"],
            line=dict(color="rgba(173, 204, 255, 0.3)", width=1),
            name="BB Upper",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["BB_Lower"],
            line=dict(color="rgba(173, 204, 255, 0.3)", width=1),
            name="BB Lower",
            fill="tonexty",
            fillcolor="rgba(173, 204, 255, 0.1)",
            hoverinfo="skip",
        ),
        row=1,
        col=1,
    )

    # Add support/resistance lines
    fig.add_hline(
        y=support,
        line_dash="dash",
        line_color="green",
        annotation_text="Support",
        annotation_position="right",
        row=1,
        col=1,
    )

    fig.add_hline(
        y=resistance,
        line_dash="dash",
        line_color="red",
        annotation_text="Resistance",
        annotation_position="right",
        row=1,
        col=1,
    )

    # Panel 2: RSI
    fig.add_trace(
        go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="purple")),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

    # Panel 3: MACD
    fig.add_trace(
        go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="blue")),
        row=3,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["Signal"],
            name="Signal",
            line=dict(color="orange"),
        ),
        row=3,
        col=1,
    )

    # Panel 4: ATR (Average True Range) - Volatility Indicator
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["ATR"],
            name="ATR",
            line=dict(color="#00D9FF", width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 217, 255, 0.2)",
        ),
        row=4,
        col=1,
    )

    # Panel 5: Volume
    colors = ["green" if row["Open"] - row["Close"] >= 0 else "red" for index, row in df.iterrows()]
    fig.add_trace(
        go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color=colors),
        row=5,
        col=1,
    )

    # Update layout for Editorial Style
    fig.update_layout(
        template=ui.get_plotly_template(),
        height=1000,  # Increased for 5-panel layout
        showlegend=False,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis_rangeslider_visible=False,
    )

    return fig


def _display_comparison_chart(
    base_ticker: str, comparison_tickers: str, period: str, interval: str
) -> None:
    """
    Display a multi-ticker comparison chart with normalized percentage changes.

    Args:
        base_ticker: Primary ticker symbol
        comparison_tickers: Comma-separated list of tickers to compare
        period: Time period for comparison
        interval: Data interval
    """
    st.markdown("---")
    st.subheader("📊 Multi-Ticker Performance Comparison")

    # Parse comparison tickers
    compare_list = [t.strip().upper() for t in comparison_tickers.split(",") if t.strip()]

    if not compare_list:
        st.info("💡 Enter ticker symbols above to compare (e.g., AAPL,MSFT,GOOGL)")
        return

    # Limit to 5 tickers for performance
    if len(compare_list) > 5:
        st.warning("⚠️ Maximum 5 comparison tickers allowed. Using first 5.")
        compare_list = compare_list[:5]

    # Combine with base ticker
    all_tickers = [base_ticker] + compare_list

    try:
        with st.spinner(f"Fetching comparison data for {len(all_tickers)} tickers..."):
            # Fetch data for all tickers
            ticker_data = {}
            failed_tickers = []

            for ticker in all_tickers:
                try:
                    df = get_stock_data(ticker, period=period, interval=interval)
                    if df is not None and not df.empty:
                        ticker_data[ticker] = df
                    else:
                        failed_tickers.append(ticker)
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {ticker}: {e}")
                    failed_tickers.append(ticker)

            if not ticker_data:
                st.error("❌ Could not fetch data for any tickers")
                return

            if failed_tickers:
                st.warning(f"⚠️ Could not fetch data for: {', '.join(failed_tickers)}")

            # Normalize to percentage change from first day
            normalized_data = {}
            for ticker, df in ticker_data.items():
                first_close = df["Close"].iloc[0]
                normalized_data[ticker] = ((df["Close"] / first_close) - 1) * 100

            # Create comparison chart
            fig = go.Figure()

            colors = [
                "#00D9FF",  # Cyan (base ticker)
                "#FFA500",  # Orange
                "#32CD32",  # Lime green
                "#FF69B4",  # Hot pink
                "#9370DB",  # Medium purple
                "#FFD700",  # Gold
            ]

            for idx, (ticker, pct_change) in enumerate(normalized_data.items()):
                is_base = ticker == base_ticker
                fig.add_trace(
                    go.Scatter(
                        x=pct_change.index,
                        y=pct_change,
                        name=ticker,
                        line=dict(
                            color=colors[idx % len(colors)],
                            width=3 if is_base else 2,
                        ),
                        mode="lines",
                    )
                )

            # Add zero line
            fig.add_hline(
                y=0,
                line_dash="dash",
                line_color="gray",
                annotation_text="Baseline",
                annotation_position="right",
            )

            fig.update_layout(
                title=f"Normalized Performance Comparison ({period})",
                yaxis_title="% Change from Start",
                xaxis_title="Date",
                template=ui.get_plotly_template(),
                height=500,
                hovermode="x unified",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            st.plotly_chart(fig, use_container_width=True)

            # Performance summary table
            st.markdown("#### 📈 Performance Summary")
            summary_data = []
            for ticker, pct_change in normalized_data.items():
                total_return = pct_change.iloc[-1]
                max_gain = pct_change.max()
                max_loss = pct_change.min()
                volatility = pct_change.std()

                summary_data.append(
                    {
                        "Ticker": ticker,
                        "Total Return (%)": f"{total_return:+.2f}%",
                        "Max Gain (%)": f"{max_gain:+.2f}%",
                        "Max Loss (%)": f"{max_loss:+.2f}%",
                        "Volatility (σ)": f"{volatility:.2f}%",
                    }
                )

            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True, hide_index=True)

            # Winner callout
            best_performer = summary_df.loc[
                summary_df["Total Return (%)"]
                .str.replace("%", "")
                .str.replace("+", "")
                .astype(float)
                .idxmax()
            ]
            st.success(
                f"🏆 **Best Performer:** {best_performer['Ticker']} "
                f"with {best_performer['Total Return (%)']} total return"
            )

    except Exception as e:
        logger.error(f"Error in multi-ticker comparison: {e}", exc_info=True)
        st.error(f"❌ Error creating comparison chart: {str(e)}")


def _display_export_options(df: pd.DataFrame, ticker: str) -> None:
    """
    Display export options for market data.

    Args:
        df: DataFrame with stock data and indicators
        ticker: Stock ticker symbol
    """
    st.markdown("---")
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)

    # Prepare export data with formatted columns
    export_df = df[
        ["Open", "High", "Low", "Close", "Volume", "MA20", "RSI", "MACD", "Signal"]
    ].copy()
    export_df.index.name = "Date"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with col1:
        # CSV Export
        csv_data = export_df.to_csv().encode("utf-8")
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"market_pulse_{ticker}_{timestamp}.csv",
            mime="text/csv",
            help="Download market data with technical indicators as CSV",
        )

    with col2:
        # Excel Export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name=ticker)
        excel_data = buffer.getvalue()

        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"market_pulse_{ticker}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download market data with technical indicators as Excel",
        )
