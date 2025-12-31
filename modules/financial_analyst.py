import os
from datetime import datetime
from io import BytesIO
from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import utils.ui as ui
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
    ui.section_header("Financial Analyst", "Fundamental Analysis & Company Metrics")

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
        logger.error(
            f"An unexpected error occurred in Financial Analyst module: {e}",
            exc_info=True,
        )
        st.error(f"An unexpected error occurred while analyzing {symbol}.")
        if st.checkbox("Show error details", key="fa_error_details"):
            st.exception(e)


def _fetch_and_display_data(symbol: str) -> None:
    """Fetch all required data and render the display components."""
    # Store ticker in session state for export functions
    st.session_state.fa_ticker = symbol

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
    st.subheader("📈 Financial Performance")

    _display_performance_charts(financials)

    st.markdown("---")
    st.subheader("📑 Detailed Financial Statements")
    _display_financial_tabs(financials)

    st.markdown("---")
    st.subheader("💰 DCF Valuation Model")
    _display_dcf_valuation(info, financials, symbol)


def _display_header(info: dict, symbol: str) -> None:
    """Render the company header section."""
    st.markdown("---")
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.header(f"{info.get('longName', symbol)} ({symbol})")
        st.caption(
            (
                f"{info.get('sector', 'N/A')} | "
                f"{info.get('industry', 'N/A')} | "
                f"{info.get('country', 'N/A')}"
            )
        )
        summary = info.get("longBusinessSummary")
        if summary:
            st.markdown(f"**Summary:** {summary[:300]}...")
        else:
            st.markdown("No summary available.")

    with header_col2:
        if "website" in info:
            st.markdown(f"[🌐 Visit Website]({info['website']})")


def _display_key_metrics(info: dict) -> None:
    """Render the key financial metrics."""
    st.subheader("🔑 Key Metrics")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        market_cap = info.get("marketCap")
        val = f"${market_cap / 1e9:.2f}B" if market_cap else "N/A"
        ui.card_metric("Market Cap", val)

    with m2:
        pe = info.get("trailingPE")
        ui.card_metric("P/E Ratio", f"{pe:.2f}" if pe else "N/A")

    with m3:
        eps = info.get("trailingEps")
        ui.card_metric("EPS (TTM)", f"${eps:.2f}" if eps else "N/A")

    with m4:
        div = info.get("dividendYield")
        val = f"{div * 100:.2f}%" if div else "N/A"
        ui.card_metric("Dividend Yield", val)


def _display_performance_charts(financials: dict) -> None:
    """Render performance charts like Revenue vs Net Income."""
    income_stmt = financials.get("income_stmt")
    if income_stmt is None or income_stmt.empty:
        st.warning("Income statement data not available to display performance charts.")
        return

    income_stmt = income_stmt.T
    income_stmt.index = pd.to_datetime(income_stmt.index)
    income_stmt = income_stmt.sort_index()

    # Detect Revenue Column
    rev_col = next(
        (
            col
            for col in income_stmt.columns
            if any(key in str(col).replace(" ", "") for key in ["TotalRevenue", "OperatingRevenue", "Revenue"])
        ),
        None,
    )

    # Detect Net Income Column
    net_inc_col = next(
        (
            col
            for col in income_stmt.columns
            if any(key in str(col).replace(" ", "") for key in ["NetIncome", "NetProfit"])
        ),
        None,
    )

    if rev_col and net_inc_col:
        fig_perf = make_subplots(specs=[[{"secondary_y": True}]])
        fig_perf.add_trace(
            go.Bar(
                x=income_stmt.index,
                y=income_stmt[rev_col],
                name="Revenue",
                marker_color="#00D9FF",
            ),
            secondary_y=False,
        )
        fig_perf.add_trace(
            go.Scatter(
                x=income_stmt.index,
                y=income_stmt[net_inc_col],
                name="Net Income",
                line=dict(color="#FFA500", width=3),
            ),
            secondary_y=True,
        )
        fig_perf.update_layout(
            title="Revenue vs Net Income (Annual)",
            template="plotly_dark",
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_perf, use_container_width=True)

        # Profitability Ratios
        _display_profitability_ratios(income_stmt, rev_col, net_inc_col)


def _display_profitability_ratios(
    income_stmt: pd.DataFrame, rev_col: str, net_inc_col: str
) -> None:
    """
    Calculate and display profitability ratios.

    Args:
        income_stmt: Transposed income statement DataFrame (dates as index, sorted)
        rev_col: Column name for revenue
        net_inc_col: Column name for net income
    """
    st.markdown("#### 📊 Profitability Ratios")
    r1, r2, r3 = st.columns(3)

    # Get latest year data
    latest_data = income_stmt.iloc[-1]
    revenue = latest_data.get(rev_col, 0)
    net_income = latest_data.get(net_inc_col, 0)
    gross_col = next(
        (
            col
            for col in latest_data.index
            if any(key in str(col).replace(" ", "") for key in ["GrossProfit", "GrossMargin"])
        ),
        None,
    )
    gross_profit = latest_data.get(gross_col, 0)

    with r1:
        net_margin = (net_income / revenue) * 100 if revenue else 0
        ui.card_metric("Net Profit Margin", f"{net_margin:.1f}%")

    with r2:
        gross_margin = (gross_profit / revenue) * 100 if revenue else 0
        ui.card_metric("Gross Margin", f"{gross_margin:.1f}%")

    with r3:
        # Calculate YoY Revenue Growth
        yoy_growth = _calculate_yoy_revenue_growth(income_stmt, rev_col)
        ui.card_metric("YoY Revenue Growth", yoy_growth)


def _calculate_yoy_revenue_growth(income_stmt: pd.DataFrame, rev_col: str) -> str:
    """
    Calculate Year-over-Year revenue growth percentage.

    Args:
        income_stmt: Transposed income statement DataFrame (dates as index, sorted)
        rev_col: Column name for revenue

    Returns:
        Formatted string with YoY growth percentage (e.g., "+15.2%") or "N/A"
    """
    try:
        # Check if we have the revenue column
        if rev_col not in income_stmt.columns:
            logger.debug(f"Revenue column '{rev_col}' not found in income statement")
            return "N/A"

        # Get revenue series and drop NaNs to find actual data points
        revenue_series = income_stmt[rev_col].dropna()

        # Check if we have at least 2 years of valid data
        if len(revenue_series) < 2:
            logger.debug("Insufficient valid data for YoY calculation (need at least 2 years)")
            return "N/A"

        # Get latest and previous year revenue from the filtered series
        latest_revenue = revenue_series.iloc[-1]
        previous_revenue = revenue_series.iloc[-2]

        # Avoid division by zero
        if previous_revenue == 0:
            logger.debug("Previous year revenue is zero, cannot calculate growth")
            return "N/A"

        # Calculate YoY growth percentage
        yoy_growth = ((latest_revenue - previous_revenue) / previous_revenue) * 100

        # Format with appropriate sign
        if yoy_growth >= 0:
            return f"+{yoy_growth:.1f}%"
        else:
            return f"{yoy_growth:.1f}%"

    except Exception as e:
        logger.warning(f"Error calculating YoY revenue growth for {rev_col}: {e}")
        return "N/A"


def _display_financial_tabs(financials: dict) -> None:
    """Render the tabs with detailed financial dataframes."""
    tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])

    with tab1:
        st.subheader("Income Statement")
        df = financials.get("income_stmt")
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
            _display_statement_export(df, "income_statement")
        else:
            st.warning("No data available.")

    with tab2:
        st.subheader("Balance Sheet")
        df = financials.get("balance_sheet")
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
            _display_statement_export(df, "balance_sheet")
        else:
            st.warning("No data available.")

    with tab3:
        st.subheader("Cash Flow")
        df = financials.get("cashflow")
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
            _display_statement_export(df, "cashflow")
        else:
            st.warning("No data available.")


def _display_statement_export(df: pd.DataFrame, statement_type: str) -> None:
    """
    Display export options for financial statement data.

    Args:
        df: DataFrame with financial statement data
        statement_type: Type of statement (income_statement, balance_sheet, cashflow)
    """
    st.markdown("---")
    st.markdown("##### 📥 Export Options")

    col1, col2 = st.columns(2)

    # Get ticker from session state if available, otherwise use generic name
    ticker = st.session_state.get("fa_ticker", "company")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Prepare export data
    export_df = df.copy()

    with col1:
        # CSV Export
        csv_data = export_df.to_csv().encode("utf-8")
        st.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name=f"financial_analyst_{ticker}_{statement_type}_{timestamp}.csv",
            mime="text/csv",
            help=f"Download {statement_type.replace('_', ' ').title()} as CSV",
            key=f"csv_{statement_type}",
        )

    with col2:
        # Excel Export
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            export_df.to_excel(writer, sheet_name=statement_type.replace("_", " ").title())
        excel_data = buffer.getvalue()

        st.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name=f"financial_analyst_{ticker}_{statement_type}_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help=f"Download {statement_type.replace('_', ' ').title()} as Excel",
            key=f"excel_{statement_type}",
        )


def _get_api_key() -> Optional[str]:
    """Get Anthropic API key from environment or session state."""
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Check session state
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key

    return api_key


def _display_ai_insights(info: dict, financials: dict, symbol: str, api_key: str) -> None:
    """Display AI-powered insights section with toggle."""
    col_title, col_toggle = st.columns([3, 1])

    with col_title:
        st.subheader("🤖 AI Insights")

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


def _generate_financial_insights(
    info: dict, financials: dict, symbol: str, api_key: str
) -> Optional[str]:
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

        prompt = f"""Analyze the following financial data for {symbol} \
({info.get("longName", symbol)}):

{financial_summary}

Provide a concise financial analysis in the following format:

**Financial Health Assessment:**
[3-5 bullet points assessing overall financial health, profitability, \
liquidity, and growth]

**Key Risks:**
[2-3 bullet points identifying potential risks or concerns]

**Key Opportunities:**
[2-3 bullet points highlighting strengths and opportunities]

Keep each bullet point to 1-2 sentences. Be specific and data-driven. \
Focus on actionable insights."""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
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
    market_cap = info.get("marketCap")
    if market_cap:
        summary_parts.append(f"Market Cap: ${market_cap / 1e9:.2f}B")

    pe = info.get("trailingPE")
    if pe:
        summary_parts.append(f"P/E Ratio: {pe:.2f}")

    eps = info.get("trailingEps")
    if eps:
        summary_parts.append(f"EPS (TTM): ${eps:.2f}")

    div_yield = info.get("dividendYield")
    if div_yield:
        summary_parts.append(f"Dividend Yield: {div_yield * 100:.2f}%")

    # Income statement highlights
    income_stmt = financials.get("income_stmt")
    if income_stmt is not None and not income_stmt.empty:
        income_stmt_t = income_stmt.T
        income_stmt_t.index = pd.to_datetime(income_stmt_t.index)
        income_stmt_t = income_stmt_t.sort_index()

        rev_col = next(
            (
                col
                for col in income_stmt_t.columns
                if "Total Revenue" in str(col) or "Revenue" in str(col)
            ),
            None,
        )
        net_inc_col = next((col for col in income_stmt_t.columns if "Net Income" in str(col)), None)

        if rev_col and len(income_stmt_t) >= 2:
            latest_rev = income_stmt_t[rev_col].iloc[-1]
            prev_rev = income_stmt_t[rev_col].iloc[-2]
            rev_growth = ((latest_rev - prev_rev) / prev_rev) * 100
            summary_parts.append(f"Revenue (Latest): ${latest_rev / 1e9:.2f}B")
            summary_parts.append(f"YoY Revenue Growth: {rev_growth:.1f}%")

        if net_inc_col and rev_col:
            latest_net = income_stmt_t[net_inc_col].iloc[-1]
            latest_rev = income_stmt_t[rev_col].iloc[-1]
            net_margin = (latest_net / latest_rev) * 100
            summary_parts.append(f"Net Income (Latest): ${latest_net / 1e9:.2f}B")
            summary_parts.append(f"Net Profit Margin: {net_margin:.1f}%")

    return "\n".join(summary_parts)


def _display_dcf_valuation(info: dict, financials: dict, symbol: str) -> None:
    """
    Display DCF (Discounted Cash Flow) valuation model with adjustable parameters.

    Args:
        info: Company information dictionary
        financials: Financial statements dictionary
        symbol: Stock ticker symbol
    """
    st.markdown(
        "Calculate intrinsic value using Discounted Cash Flow analysis. "
        "Adjust growth assumptions to see how valuation changes."
    )

    # Get free cash flow data
    cashflow = financials.get("cashflow")
    if cashflow is None or cashflow.empty:
        st.warning("⚠️ Cash flow data not available for DCF valuation.")
        return

    # Transpose and prepare cash flow data
    cashflow_t = cashflow.T
    cashflow_t.index = pd.to_datetime(cashflow_t.index)
    cashflow_t = cashflow_t.sort_index()

    # Find Free Cash Flow column
    fcf_col = next(
        (
            col
            for col in cashflow_t.columns
            if any(key in str(col).replace(" ", "") for key in ["FreeCashFlow", "OperatingCashFlow"])
        ),
        None,
    )

    if not fcf_col or len(cashflow_t) == 0:
        st.warning("⚠️ Free Cash Flow data not available for DCF valuation.")
        return

    # Get latest FCF
    latest_fcf = cashflow_t[fcf_col].iloc[-1]

    if pd.isna(latest_fcf) or latest_fcf <= 0:
        st.warning("⚠️ Invalid Free Cash Flow data (negative or missing).")
        return

    # Get current stock price and shares outstanding
    current_price = info.get("currentPrice", info.get("regularMarketPrice"))
    shares_outstanding = info.get("sharesOutstanding")

    if not current_price or not shares_outstanding:
        st.warning("⚠️ Missing current price or shares outstanding data.")
        return

    # DCF Parameter Inputs
    col1, col2, col3 = st.columns(3)

    with col1:
        growth_years_1_5 = st.slider(
            "Growth Rate Years 1-5 (%)",
            min_value=-10.0,
            max_value=50.0,
            value=15.0,
            step=1.0,
            help="Expected annual FCF growth rate for the next 5 years",
        )

    with col2:
        growth_years_6_10 = st.slider(
            "Growth Rate Years 6-10 (%)",
            min_value=-5.0,
            max_value=25.0,
            value=8.0,
            step=1.0,
            help="Expected annual FCF growth rate for years 6-10",
        )

    with col3:
        terminal_growth = st.slider(
            "Terminal Growth Rate (%)",
            min_value=0.0,
            max_value=5.0,
            value=2.5,
            step=0.5,
            help="Perpetual growth rate after year 10 (typically GDP growth rate)",
        )

    col4, col5 = st.columns(2)

    with col4:
        discount_rate = st.slider(
            "Discount Rate (WACC) (%)",
            min_value=5.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
            help="Weighted Average Cost of Capital - reflects investment risk",
        )

    with col5:
        margin_of_safety = st.slider(
            "Margin of Safety (%)",
            min_value=0,
            max_value=50,
            value=20,
            step=5,
            help="Discount from fair value for conservative estimate",
        )

    # Calculate DCF
    st.markdown("---")
    st.markdown("#### 📊 DCF Calculation")

    # Project future cash flows
    projected_fcf = []
    current_fcf = latest_fcf

    # Years 1-5
    for year in range(1, 6):
        current_fcf = current_fcf * (1 + growth_years_1_5 / 100)
        pv = current_fcf / ((1 + discount_rate / 100) ** year)
        projected_fcf.append({"Year": year, "FCF": current_fcf, "PV": pv})

    # Years 6-10
    for year in range(6, 11):
        current_fcf = current_fcf * (1 + growth_years_6_10 / 100)
        pv = current_fcf / ((1 + discount_rate / 100) ** year)
        projected_fcf.append({"Year": year, "FCF": current_fcf, "PV": pv})

    # Terminal value
    terminal_fcf = current_fcf * (1 + terminal_growth / 100)
    terminal_value = terminal_fcf / (discount_rate / 100 - terminal_growth / 100)
    terminal_pv = terminal_value / ((1 + discount_rate / 100) ** 10)

    # Total enterprise value
    sum_pv_fcf = sum(row["PV"] for row in projected_fcf)
    enterprise_value = sum_pv_fcf + terminal_pv

    # Equity value (simplified - not accounting for debt/cash)
    equity_value = enterprise_value
    fair_value_per_share = equity_value / shares_outstanding

    # Apply margin of safety
    conservative_value = fair_value_per_share * (1 - margin_of_safety / 100)

    # Display results
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    with result_col1:
        st.metric("Current Price", f"${current_price:.2f}")

    with result_col2:
        st.metric("Fair Value", f"${fair_value_per_share:.2f}")

    with result_col3:
        upside = ((fair_value_per_share - current_price) / current_price) * 100
        st.metric("Upside/Downside", f"{upside:+.1f}%", delta=f"{'Undervalued' if upside > 0 else 'Overvalued'}")

    with result_col4:
        st.metric(
            f"Conservative Value ({margin_of_safety}% MoS)",
            f"${conservative_value:.2f}",
        )

    # Valuation verdict
    if fair_value_per_share > current_price * 1.2:
        st.success(f"🟢 **UNDERVALUED** - Fair value is {upside:.1f}% above current price")
    elif fair_value_per_share < current_price * 0.8:
        st.error(f"🔴 **OVERVALUED** - Fair value is {abs(upside):.1f}% below current price")
    else:
        st.info(f"🟡 **FAIRLY VALUED** - Current price within 20% of fair value")

    # Detailed breakdown
    with st.expander("📋 Detailed DCF Breakdown", expanded=False):
        st.markdown(f"**Starting FCF:** ${latest_fcf / 1e9:.2f}B")
        st.markdown(f"**Sum of PV (Years 1-10):** ${sum_pv_fcf / 1e9:.2f}B")
        st.markdown(f"**Terminal Value (PV):** ${terminal_pv / 1e9:.2f}B")
        st.markdown(f"**Enterprise Value:** ${enterprise_value / 1e9:.2f}B")
        st.markdown(f"**Shares Outstanding:** {shares_outstanding / 1e9:.2f}B")

        # Show projection table
        st.markdown("##### Projected Free Cash Flows")
        projection_df = pd.DataFrame(projected_fcf)
        projection_df["FCF"] = projection_df["FCF"].apply(lambda x: f"${x / 1e9:.2f}B")
        projection_df["PV"] = projection_df["PV"].apply(lambda x: f"${x / 1e9:.2f}B")
        st.dataframe(projection_df, use_container_width=True, hide_index=True)

    # Sensitivity analysis
    st.markdown("---")
    st.markdown("#### 🔍 Sensitivity Analysis")
    st.caption("How fair value changes with different growth and discount rate assumptions")

    # Create sensitivity table
    discount_rates = [discount_rate - 2, discount_rate - 1, discount_rate, discount_rate + 1, discount_rate + 2]
    growth_rates = [growth_years_1_5 - 5, growth_years_1_5, growth_years_1_5 + 5]

    sensitivity_data = []
    for gr in growth_rates:
        row = {"Growth Rate": f"{gr:.0f}%"}
        for dr in discount_rates:
            # Recalculate with new parameters
            temp_fcf = latest_fcf
            temp_pv_sum = 0
            for y in range(1, 6):
                temp_fcf = temp_fcf * (1 + gr / 100)
                temp_pv_sum += temp_fcf / ((1 + dr / 100) ** y)
            for y in range(6, 11):
                temp_fcf = temp_fcf * (1 + growth_years_6_10 / 100)
                temp_pv_sum += temp_fcf / ((1 + dr / 100) ** y)

            temp_terminal_fcf = temp_fcf * (1 + terminal_growth / 100)
            temp_terminal_value = temp_terminal_fcf / (dr / 100 - terminal_growth / 100)
            temp_terminal_pv = temp_terminal_value / ((1 + dr / 100) ** 10)

            temp_ev = temp_pv_sum + temp_terminal_pv
            temp_fair_value = temp_ev / shares_outstanding

            row[f"WACC {dr:.0f}%"] = f"${temp_fair_value:.2f}"
        sensitivity_data.append(row)

    sensitivity_df = pd.DataFrame(sensitivity_data)
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)

    st.caption(
        "💡 **Tip:** If the stock price is below most values in the table, it may be undervalued. "
        "If it's above most values, it may be overvalued."
    )
