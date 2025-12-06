import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_loader import get_company_info, get_financials
from utils.exceptions import DataFetchError
from utils.logger import get_logger

logger = get_logger(__name__)

def render() -> None:
    """Render the Financial Analyst module."""
    st.title("💼 Financial Analyst")
    st.markdown("### Fundamental Analysis & Company Metrics")

    # Input Section
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol = st.text_input("Enter Ticker Symbol", value="AAPL", max_chars=10).upper()
    
    if not symbol:
        st.info("Please enter a ticker symbol to begin.")
        return

    try:
        with st.spinner(f"Analyzing {symbol}..."):
            # Fetch Data in a separate step to handle errors granularly
            _fetch_and_display_data(symbol)

    except DataFetchError as e:
        logger.warning(f"Could not fetch financial data for {symbol}: {e}")
        st.error(f"❌ Failed to fetch data for '{symbol}'.")
        st.info("The ticker might be invalid, delisted, or there could be a network issue.")
    
    except Exception as e:
        logger.error(f"An unexpected error occurred in Financial Analyst module: {e}", exc_info=True)
        st.error(f"An unexpected error occurred while analyzing {symbol}.")
        if st.checkbox("Show error details", key="fa_error_details"):
            st.exception(e)


def _fetch_and_display_data(symbol: str):
    """Fetch all required data and render the display components."""
    info = get_company_info(symbol)
    financials = get_financials(symbol)
    
    if not info or not financials:
        raise DataFetchError(f"No data returned for {symbol}. It may be an invalid ticker.")

    # --- RENDER PAGE ---
    _display_header(info, symbol)
    _display_key_metrics(info)
    
    st.markdown("---")
    st.markdown("### 📈 Financial Performance")
    
    _display_performance_charts(financials)

    st.markdown("---")
    st.markdown("### 📑 Detailed Financial Statements")
    _display_financial_tabs(financials)


def _display_header(info: dict, symbol: str):
    """Render the company header section."""
    st.markdown("---")
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.header(f"{info.get('longName', symbol)} ({symbol})")
        st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | {info.get('country', 'N/A')}")
        summary = info.get('longBusinessSummary')
        if summary:
            st.markdown(f"**Summary:** {summary[:300]}...")
        else:
            st.markdown("No summary available.")
    
    with header_col2:
        if 'website' in info:
            st.markdown(f"[🌐 Visit Website]({info['website']})")


def _display_key_metrics(info: dict):
    """Render the key financial metrics."""
    st.markdown("### 🔑 Key Metrics")
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        market_cap = info.get('marketCap')
        val = f"${market_cap/1e9:.2f}B" if market_cap else "N/A"
        st.metric("Market Cap", val)
    
    with m2:
        pe = info.get('trailingPE')
        st.metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")
        
    with m3:
        eps = info.get('trailingEps')
        st.metric("EPS (TTM)", f"${eps:.2f}" if eps else "N/A")
        
    with m4:
        div = info.get('dividendYield')
        val = f"{div*100:.2f}%" if div else "N/A"
        st.metric("Dividend Yield", val)


def _display_performance_charts(financials: dict):
    """Render performance charts like Revenue vs Net Income."""
    income_stmt = financials.get('income_stmt')
    if income_stmt is None or income_stmt.empty:
        st.warning("Income statement data not available to display performance charts.")
        return
        
    income_stmt = income_stmt.T
    income_stmt.index = pd.to_datetime(income_stmt.index)
    income_stmt = income_stmt.sort_index()
    
    rev_col = next((col for col in income_stmt.columns if 'Total Revenue' in str(col) or 'Revenue' in str(col)), None)
    net_inc_col = next((col for col in income_stmt.columns if 'Net Income' in str(col)), None)
    
    if rev_col and net_inc_col:
        fig_perf = make_subplots(specs=[[{"secondary_y": True}]])
        fig_perf.add_trace(
            go.Bar(x=income_stmt.index, y=income_stmt[rev_col], name="Revenue", marker_color='#00D9FF'),
            secondary_y=False
        )
        fig_perf.add_trace(
            go.Scatter(x=income_stmt.index, y=income_stmt[net_inc_col], name="Net Income", line=dict(color='#FFA500', width=3)),
            secondary_y=True
        )
        fig_perf.update_layout(
            title="Revenue vs Net Income (Annual)",
            template="plotly_dark",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_perf, use_container_width=True)
        
        # Profitability Ratios
        _display_profitability_ratios(income_stmt.iloc[-1], rev_col, net_inc_col)

def _display_profitability_ratios(latest_data: pd.Series, rev_col: str, net_inc_col: str):
    """Calculate and display profitability ratios."""
    st.markdown("#### 📊 Profitability Ratios")
    r1, r2, r3 = st.columns(3)
    
    revenue = latest_data.get(rev_col, 0)
    net_income = latest_data.get(net_inc_col, 0)
    gross_col = next((col for col in latest_data.index if 'Gross Profit' in str(col)), None)
    gross_profit = latest_data.get(gross_col, 0)
    
    with r1:
        net_margin = (net_income / revenue) * 100 if revenue else 0
        st.metric("Net Profit Margin", f"{net_margin:.1f}%")
    
    with r2:
        gross_margin = (gross_profit / revenue) * 100 if revenue else 0
        st.metric("Gross Margin", f"{gross_margin:.1f}%")
        
    with r3:
        # YoY Revenue Growth requires previous year's data, which is complex here.
        # This part has been simplified to avoid errors if data is missing.
        st.metric("YoY Revenue Growth", "N/A")


def _display_financial_tabs(financials: dict):
    """Render the tabs with detailed financial dataframes."""
    tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    with tab1:
        st.subheader("Income Statement")
        df = financials.get('income_stmt')
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data available.")
            
    with tab2:
        st.subheader("Balance Sheet")
        df = financials.get('balance_sheet')
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data available.")
            
    with tab3:
        st.subheader("Cash Flow")
        df = financials.get('cashflow')
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data available.")
