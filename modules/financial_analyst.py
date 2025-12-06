import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from typing import Optional
from utils.data_loader import get_company_info, get_financials
from utils.exceptions import DataFetchError
from utils.logger import get_logger

# Conditional import for Claude API
try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

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

    # AI Insights Section
    api_key = _get_api_key()
    if api_key and ANTHROPIC_AVAILABLE:
        st.markdown("---")
        _display_ai_insights(info, financials, symbol, api_key)

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


def _get_api_key() -> Optional[str]:
    """Get Anthropic API key from environment or session state."""
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Check session state
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key

    return api_key


def _display_ai_insights(info: dict, financials: dict, symbol: str, api_key: str):
    """Display AI-powered insights section with toggle."""
    col_title, col_toggle = st.columns([3, 1])

    with col_title:
        st.markdown("### 🤖 AI Insights")

    with col_toggle:
        enable_ai = st.toggle("Enable AI Insights", value=True, key="ai_insights_toggle")

    if not enable_ai:
        st.info("AI insights are disabled. Toggle above to enable.")
        return

    # Generate insights
    with st.spinner("Analyzing company financials with Claude..."):
        insights = _generate_financial_insights(info, financials, symbol, api_key)

    if insights:
        st.markdown(insights)
    else:
        st.warning("Could not generate AI insights. Please check your API key.")


def _generate_financial_insights(info: dict, financials: dict, symbol: str, api_key: str) -> Optional[str]:
    """
    Generate AI insights using Claude API.

    Args:
        info: Company information dictionary
        financials: Financial statements dictionary
        symbol: Stock ticker symbol
        api_key: Anthropic API key

    Returns:
        Formatted markdown string with insights, or None if generation fails
    """
    try:
        client = Anthropic(api_key=api_key)

        # Build financial summary for Claude
        financial_summary = _build_financial_summary(info, financials)

        prompt = f"""Analyze the following financial data for {symbol} ({info.get('longName', symbol)}):

{financial_summary}

Provide a concise financial analysis in the following format:

**Financial Health Assessment:**
[3-5 bullet points assessing overall financial health, profitability, liquidity, and growth]

**Key Risks:**
[2-3 bullet points identifying potential risks or concerns]

**Key Opportunities:**
[2-3 bullet points highlighting strengths and opportunities]

Keep each bullet point to 1-2 sentences. Be specific and data-driven. Focus on actionable insights."""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract generated text
        insights = message.content[0].text

        logger.info(f"Successfully generated AI insights for {symbol}")
        return insights

    except APIError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        st.error(f"API Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        st.error(f"Generation failed: {str(e)}")
        return None


def _build_financial_summary(info: dict, financials: dict) -> str:
    """Build a text summary of financial data for Claude."""
    summary_parts = []

    # Company basics
    summary_parts.append(f"Company: {info.get('longName', 'N/A')}")
    summary_parts.append(f"Sector: {info.get('sector', 'N/A')}")
    summary_parts.append(f"Industry: {info.get('industry', 'N/A')}")

    # Key metrics
    market_cap = info.get('marketCap')
    if market_cap:
        summary_parts.append(f"Market Cap: ${market_cap/1e9:.2f}B")

    pe = info.get('trailingPE')
    if pe:
        summary_parts.append(f"P/E Ratio: {pe:.2f}")

    eps = info.get('trailingEps')
    if eps:
        summary_parts.append(f"EPS (TTM): ${eps:.2f}")

    div_yield = info.get('dividendYield')
    if div_yield:
        summary_parts.append(f"Dividend Yield: {div_yield*100:.2f}%")

    # Income statement highlights
    income_stmt = financials.get('income_stmt')
    if income_stmt is not None and not income_stmt.empty:
        income_stmt_t = income_stmt.T
        income_stmt_t.index = pd.to_datetime(income_stmt_t.index)
        income_stmt_t = income_stmt_t.sort_index()

        rev_col = next((col for col in income_stmt_t.columns if 'Total Revenue' in str(col) or 'Revenue' in str(col)), None)
        net_inc_col = next((col for col in income_stmt_t.columns if 'Net Income' in str(col)), None)

        if rev_col and len(income_stmt_t) >= 2:
            latest_rev = income_stmt_t[rev_col].iloc[-1]
            prev_rev = income_stmt_t[rev_col].iloc[-2]
            rev_growth = ((latest_rev - prev_rev) / prev_rev) * 100
            summary_parts.append(f"Revenue (Latest): ${latest_rev/1e9:.2f}B")
            summary_parts.append(f"YoY Revenue Growth: {rev_growth:.1f}%")

        if net_inc_col and rev_col:
            latest_net = income_stmt_t[net_inc_col].iloc[-1]
            latest_rev = income_stmt_t[rev_col].iloc[-1]
            net_margin = (latest_net / latest_rev) * 100
            summary_parts.append(f"Net Income (Latest): ${latest_net/1e9:.2f}B")
            summary_parts.append(f"Net Profit Margin: {net_margin:.1f}%")

    return "\n".join(summary_parts)
