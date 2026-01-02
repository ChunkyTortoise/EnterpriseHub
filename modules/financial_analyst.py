import os
from datetime import datetime
from io import BytesIO
from typing import Optional, cast

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import utils.ui as ui
from utils.data_loader import get_company_info, get_financials
from utils.exceptions import DataFetchError
from utils.logger import get_logger

# Import core logic
from modules.financial_analyst_logic import (
    DCFModel,
    DCFParameters,
    CompanyInfo,
    FinancialsDict,
    find_column,
    calculate_yoy_growth,
    build_ai_prompt,
    calculate_piotroski_score,
    PiotroskiScore,
    calculate_historical_ratios,
    HistoricalRatios
)

# Conditional import for Claude API
try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)


def _display_demo_data(symbol: str) -> None:
    """Display demo data from pre-loaded JSON file."""
    import json
    from pathlib import Path

    # Load demo data with robust path finding
    base_dir = Path(__file__).parent.parent
    demo_file = base_dir / "data/demo_aapl_fundamentals.json"
    
    try:
        with open(demo_file, 'r') as f:
            demo_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Demo data file not found: {demo_file}")
        return

    # Parse demo data into expected format
    info = cast(CompanyInfo, demo_data.get("info", {}))

    # Store ticker in session state
    st.session_state.fa_ticker = symbol

    # --- RENDER PAGE ---
    _display_header(info, symbol)
    _display_key_metrics(info)

    ui.spacer(20)
    st.markdown(f"### 📈 Financial Performance: {symbol}")

    # Display demo metrics with animated cards
    col1, col2, col3 = st.columns(3)
    with col1:
        ui.animated_metric("Revenue (TTM)", "$394.33B", "+2.1%", icon="💰", color="primary")
    with col2:
        ui.animated_metric("Net Income", "$97.00B", "+7.8%", icon="📈", color="success")
    with col3:
        ui.animated_metric("Free Cash Flow", "$99.58B", "+5.2%", icon="💸", color="primary")

    ui.spacer(20)
    # Revenue chart
    st.markdown("#### 📊 Revenue Growth Analysis")
    revenue_data = {
        "Quarter": ["Q1 2023", "Q2 2023", "Q3 2023", "Q4 2023", "Q1 2024"],
        "Revenue": [94.8, 81.8, 89.5, 119.6, 108.6]
    }
    df = pd.DataFrame(revenue_data)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Quarter"], y=df["Revenue"], marker_color=ui.THEME['primary']))
    fig.update_layout(
        title="Quarterly Revenue (Billions)",
        yaxis_title="Revenue ($B)",
        height=300,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("💰 DCF Valuation Model")

    # Demo DCF results
    current_price = info.get("currentPrice", 180.0)
    if current_price is None:
        current_price = 180.0
        
    fair_value = 195.50
    upside = ((fair_value - current_price) / current_price) * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Price", f"${current_price:.2f}")
    with col2:
        st.metric("Fair Value (DCF)", f"${fair_value:.2f}")
    with col3:
        st.metric("Upside/Downside", f"{upside:+.1f}%", delta=f"{upside:+.1f}%")

    # Analyst recommendation
    if upside > 15:
        st.success("🟢 **Analyst Rating: BUY** - Stock appears undervalued")
    elif upside < -15:
        st.error("🔴 **Analyst Rating: SELL** - Stock appears overvalued")
    else:
        st.info("🟡 **Analyst Rating: HOLD** - Stock appears fairly valued")

    # Key assumptions
    with st.expander("📋 Valuation Assumptions", expanded=False):
        st.markdown("""
        **DCF Model Parameters:**
        - Growth Rate (Years 1-5): 8.0%
        - Growth Rate (Years 6-10): 5.0%
        - Terminal Growth Rate: 2.5%
        - Discount Rate (WACC): 9.2%
        - Free Cash Flow (Latest): $99.58B
        """)

    # Demo insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights (Demo)")
    st.markdown("""
    **Strengths:**
    - Strong revenue growth across all segments
    - Healthy profit margins (24.6% net margin)
    - Robust cash flow generation ($99.58B FCF)
    - Services segment showing 15%+ YoY growth
    
    **Considerations:**
    - iPhone revenue growth slowing in mature markets
    - Increased competition in wearables segment
    - Regulatory scrutiny on App Store policies
    
    **Recommendation:** Apple remains a solid long-term investment with strong fundamentals and consistent execution.
    """)


def render() -> None:
    """Render the Financial Analyst module."""
    ui.section_header("Financial Analyst", "Fundamental Analysis & Company Metrics")

    # Demo Mode Toggle (default True for screenshots)
    demo_mode = st.checkbox(
        "🎯 Demo Mode (Use Sample Data)",
        value=True,
        help="Toggle to use sample Apple (AAPL) data without API calls. Recommended for reliable demo."
    )

    # Input Section
    col1, col2 = st.columns([1, 3])
    with col1:
        if demo_mode:
            symbol = st.selectbox("Select Demo Company", ["AAPL"], index=0)
            st.caption("💡 Demo mode uses pre-loaded data")
        else:
            symbol = st.text_input("Enter Ticker Symbol", value="AAPL", max_chars=10).upper()

    if not symbol:
        st.info("Please enter a ticker symbol to begin.")
        return

    try:
        with st.spinner(f"Analyzing {symbol}..."):
            # Fetch Data in a separate step to handle errors granularly
            if demo_mode:
                _display_demo_data(symbol)
            else:
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

    # Cast to our typed definitions
    info = cast(CompanyInfo, get_company_info(symbol))
    financials = cast(FinancialsDict, get_financials(symbol))

    if not info or not financials:
        raise DataFetchError(f"No data returned for {symbol}. It may be an invalid ticker.")

    # --- RENDER PAGE ---
    _display_header(info, symbol)
    _display_key_metrics(info)

    # Piotroski F-Score Section
    st.markdown("---")
    _display_piotroski_score(financials)

    # Historical Ratio Trends
    st.markdown("---")
    _display_historical_trends(financials)

    # Quarterly Trends (if available)
    st.markdown("---")
    _display_quarterly_trends(symbol)

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


def _display_header(info: CompanyInfo, symbol: str) -> None:
    """Render the company header section."""
    ui.spacer(20)
    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        st.markdown(
            f"<h2 style='margin-bottom: 0; color: #020617; border-left: none; padding-left: 0;'>"
            f"{info.get('longName', symbol)} <span style='color: #64748B;'>({symbol})</span></h2>",
            unsafe_allow_html=True
        )
        
        sector = info.get('sector', 'Unknown Sector')
        industry = info.get('industry', 'Unknown Industry')
        country = info.get('country', 'Unknown Region')
        
        st.markdown(
            f"<div style='margin-bottom: 15px; font-weight: 500; color: #10B981;'>"
            f"{sector} • {industry} • {country}</div>",
            unsafe_allow_html=True
        )
        
        summary = info.get("longBusinessSummary")
        if summary:
            st.markdown(f"<p style='color: #334155; line-height: 1.6;'>{summary[:350]}...</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p style='color: #94A3B8; font-style: italic;'>Corporate summary currently unavailable for this ticker.</p>", unsafe_allow_html=True)

    with header_col2:
        if "website" in info:
            st.markdown(f"<div style='margin-top: 10px;'>{ui.status_badge('ACTIVE')}</div>", unsafe_allow_html=True)
            st.markdown(f"<a href='{info['website']}' target='_blank' style='text-decoration: none; font-weight: 600; color: #020617;'>🌐 Visit Website →</a>", unsafe_allow_html=True)


def _display_key_metrics(info: CompanyInfo) -> None:
    """Render the key financial metrics."""
    st.markdown("### 🔑 Key Performance Indicators")
    m1, m2, m3, m4 = st.columns(4)

    def _format_na(val):
        if val is None or val == "N/A":
            return "N/A"
        return val

    with m1:
        market_cap = info.get("marketCap")
        val = f"${market_cap / 1e9:.2f}B" if market_cap else None
        ui.animated_metric("Market Cap", _format_na(val), icon="🏢")

    with m2:
        pe = info.get("trailingPE")
        val = f"{pe:.2f}" if pe else None
        ui.animated_metric("P/E Ratio", _format_na(val), icon="📊")

    with m3:
        eps = info.get("trailingEps")
        val = f"${eps:.2f}" if eps else None
        ui.animated_metric("EPS (TTM)", _format_na(val), icon="📈")

    with m4:
        div = info.get("dividendYield")
        val = f"{div * 100:.2f}%" if div else None
        ui.animated_metric("Dividend Yield", _format_na(val), icon="💰")


def _display_performance_charts(financials: FinancialsDict) -> None:
    """Render performance charts like Revenue vs Net Income."""
    income_stmt = financials.get("income_stmt")
    if income_stmt is None or income_stmt.empty:
        st.warning("Income statement data not available to display performance charts.")
        return

    income_stmt = income_stmt.T
    income_stmt.index = pd.to_datetime(income_stmt.index)
    income_stmt = income_stmt.sort_index()

    # Detect Revenue Column using utility
    rev_col = find_column(income_stmt, ["TotalRevenue", "OperatingRevenue", "Revenue"])
    
    # Detect Net Income Column using utility
    net_inc_col = find_column(income_stmt, ["NetIncome", "NetProfit"])

    if rev_col and net_inc_col:
        fig_perf = make_subplots(specs=[[{"secondary_y": True}]])
        fig_perf.add_trace(
            go.Bar(
                x=income_stmt.index,
                y=income_stmt[rev_col],
                name="Revenue",
                marker_color=ui.THEME["primary"],
            ),
            secondary_y=False,
        )
        fig_perf.add_trace(
            go.Scatter(
                x=income_stmt.index,
                y=income_stmt[net_inc_col],
                name="Net Income",
                line=dict(color=ui.THEME["warning"], width=3),
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
    income_stmt: pd.DataFrame,
    rev_col: str,
    net_inc_col: str,
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
    
    gross_col = find_column(income_stmt, ["GrossProfit", "GrossMargin"])
    gross_profit = latest_data.get(gross_col, 0) if gross_col else 0

    with r1:
        net_margin = (net_income / revenue) * 100 if revenue else 0
        ui.card_metric("Net Profit Margin", f"{net_margin:.1f}%")

    with r2:
        gross_margin = (gross_profit / revenue) * 100 if revenue else 0
        ui.card_metric("Gross Margin", f"{gross_margin:.1f}%")

    with r3:
        # Calculate YoY Revenue Growth using new logic
        yoy_growth = calculate_yoy_growth(income_stmt[rev_col])
        if yoy_growth is not None:
             growth_str = f"{yoy_growth:+.1f}%"
        else:
             growth_str = "N/A"
        ui.card_metric("YoY Revenue Growth", growth_str)


def _display_financial_tabs(financials: FinancialsDict) -> None:
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

    col1, col2, col3 = st.columns(3)

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

    with col3:
        # PDF Export (using matplotlib for professional formatting)
        if st.button(
            "📑 Generate PDF",
            key=f"pdf_{statement_type}",
            use_container_width=True,
            help="Create a professional PDF report",
        ):
            try:
                import matplotlib.pyplot as plt
                from matplotlib.backends.backend_pdf import PdfPages
                import matplotlib

                matplotlib.use("Agg")  # Non-interactive backend

                # Create PDF
                pdf_buffer = BytesIO()
                with PdfPages(pdf_buffer) as pdf:
                    # Create figure for table
                    fig, ax = plt.subplots(figsize=(11, 8.5))  # Letter size
                    ax.axis("tight")
                    ax.axis("off")

                    # Prepare data for display (limit to prevent overflow)
                    display_df = export_df.head(20).copy()  # Limit rows

                    # Format numbers for readability
                    for col in display_df.columns:
                        if display_df[col].dtype in ["float64", "int64"]:
                            display_df[col] = display_df[col].apply(
                                lambda x: f"${x / 1e9:.2f}B"
                                if abs(x) >= 1e9
                                else f"${x / 1e6:.2f}M"
                                if abs(x) >= 1e6
                                else f"${x:,.0f}"
                            )

                    # Create table
                    table = ax.table(
                        cellText=display_df.values,
                        colLabels=display_df.columns,
                        rowLabels=display_df.index,
                        cellLoc="right",
                        loc="center",
                        colWidths=[0.15] * len(display_df.columns),
                    )

                    # Style table
                    table.auto_set_font_size(False)
                    table.set_fontsize(8)
                    table.scale(1, 2)

                    # Header styling
                    for i in range(len(display_df.columns)):
                        table[(0, i)].set_facecolor(ui.THEME["primary"])
                        table[(0, i)].set_text_props(weight="bold", color="white")

                    # Add title
                    title = (
                        f"{ticker.upper()} - "
                        f"{statement_type.replace('_', ' ').title()}\n{timestamp}"
                    )
                    plt.title(title, fontsize=14, fontweight="bold", pad=20)

                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close()

                pdf_buffer.seek(0)

                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer,
                    file_name=f"financial_analyst_{ticker}_{statement_type}_{timestamp}.pdf",
                    mime="application/pdf",
                    key=f"pdf_download_{statement_type}",
                )

            except ImportError:
                st.error("⚠️ PDF export requires matplotlib. Install with: pip install matplotlib")
            except Exception as e:
                st.error(f"⚠️ Error generating PDF: {str(e)}")


def _display_piotroski_score(financials: FinancialsDict) -> None:
    """
    Display Piotroski F-Score with breakdown of 9 criteria.

    Args:
        financials: Financial statements dictionary
    """
    st.subheader("🏆 Piotroski F-Score (Financial Health)")

    piotroski = calculate_piotroski_score(financials)

    if piotroski is None:
        st.warning("⚠️ Insufficient historical data to calculate Piotroski F-Score (requires 2+ years)")
        return

    # Main score display
    score_col1, score_col2, score_col3 = st.columns([1, 1, 1])

    with score_col1:
        # Determine color based on score
        if piotroski.total_score >= 7:
            color = "success"
            icon = "🟢"
        elif piotroski.total_score >= 4:
            color = "primary"
            icon = "🟡"
        else:
            color = "danger"
            icon = "🔴"

        ui.animated_metric(
            "Total Score",
            f"{piotroski.total_score}/9",
            delta=piotroski.interpretation,
            icon=icon,
            color=color
        )

    with score_col2:
        ui.animated_metric(
            "Profitability",
            f"{piotroski.profitability_score}/4",
            icon="💰"
        )

    with score_col3:
        ui.animated_metric(
            "Leverage & Efficiency",
            f"{piotroski.leverage_score + piotroski.efficiency_score}/5",
            icon="⚖️"
        )

    # Detailed breakdown
    with st.expander("📋 Detailed Criteria Breakdown", expanded=False):
        st.markdown("##### Profitability Signals (4 points)")

        criteria_names = {
            "positive_roa": "✅ Positive Return on Assets" if piotroski.criteria.get("positive_roa") else "❌ Positive Return on Assets",
            "positive_ocf": "✅ Positive Operating Cash Flow" if piotroski.criteria.get("positive_ocf") else "❌ Positive Operating Cash Flow",
            "roa_improving": "✅ ROA Improving YoY" if piotroski.criteria.get("roa_improving") else "❌ ROA Improving YoY",
            "quality_earnings": "✅ Quality Earnings (OCF > NI)" if piotroski.criteria.get("quality_earnings") else "❌ Quality Earnings (OCF > NI)",
        }

        for key, label in criteria_names.items():
            st.markdown(f"- {label}")

        st.markdown("##### Leverage & Liquidity Signals (3 points)")

        lev_criteria = {
            "leverage_decreasing": "✅ Leverage Decreasing" if piotroski.criteria.get("leverage_decreasing") else "❌ Leverage Decreasing",
            "liquidity_improving": "✅ Liquidity Improving" if piotroski.criteria.get("liquidity_improving") else "❌ Liquidity Improving",
            "no_dilution": "✅ No Share Dilution" if piotroski.criteria.get("no_dilution") else "❌ No Share Dilution",
        }

        for key, label in lev_criteria.items():
            st.markdown(f"- {label}")

        st.markdown("##### Operating Efficiency Signals (2 points)")

        eff_criteria = {
            "margin_improving": "✅ Gross Margin Improving" if piotroski.criteria.get("margin_improving") else "❌ Gross Margin Improving",
            "turnover_improving": "✅ Asset Turnover Improving" if piotroski.criteria.get("turnover_improving") else "❌ Asset Turnover Improving",
        }

        for key, label in eff_criteria.items():
            st.markdown(f"- {label}")

    # Interpretation guidance
    if piotroski.total_score >= 7:
        st.success(
            "🟢 **Strong Financial Health** - This company exhibits strong fundamentals across profitability, leverage, and efficiency. "
            "Scores of 7-9 historically correlate with outperformance."
        )
    elif piotroski.total_score >= 4:
        st.info(
            "🟡 **Moderate Financial Health** - Mixed signals. Review the detailed breakdown to understand strengths and weaknesses. "
            "Consider combining with other analysis frameworks."
        )
    else:
        st.warning(
            "🔴 **Weak Financial Health** - Multiple red flags detected. This company shows concerning trends in profitability, leverage, or efficiency. "
            "Proceed with caution and conduct thorough due diligence."
        )


def _display_historical_trends(financials: FinancialsDict) -> None:
    """
    Display 5-year historical trend charts for key financial ratios.

    Args:
        financials: Financial statements dictionary
    """
    st.subheader("📈 5-Year Financial Health Trends")

    historical = calculate_historical_ratios(financials)

    if historical is None:
        st.info("💡 Multi-year historical data not available for trend analysis.")
        return

    # Create 2x2 grid of trend charts
    col1, col2 = st.columns(2)

    with col1:
        # Current Ratio Trend
        if not historical.current_ratio.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical.years,
                y=historical.current_ratio.values,
                mode='lines+markers',
                name='Current Ratio',
                line=dict(color='#10B981', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Current Ratio (Liquidity)",
                yaxis_title="Ratio",
                height=300,
                template="plotly_dark",
                showlegend=False
            )
            fig.add_hline(y=2.0, line_dash="dash", line_color="gray", annotation_text="Healthy: 2.0+")
            st.plotly_chart(fig, use_container_width=True)

        # ROE Trend
        if not historical.roe.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical.years,
                y=historical.roe.values,
                mode='lines+markers',
                name='ROE',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Return on Equity (ROE)",
                yaxis_title="ROE (%)",
                height=300,
                template="plotly_dark",
                showlegend=False
            )
            fig.add_hline(y=15.0, line_dash="dash", line_color="gray", annotation_text="Strong: 15%+")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Debt-to-Equity Trend
        if not historical.debt_to_equity.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=historical.years,
                y=historical.debt_to_equity.values,
                mode='lines+markers',
                name='D/E Ratio',
                line=dict(color='#F59E0B', width=3),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Debt-to-Equity (Leverage)",
                yaxis_title="D/E Ratio",
                height=300,
                template="plotly_dark",
                showlegend=False
            )
            fig.add_hline(y=1.0, line_dash="dash", line_color="gray", annotation_text="Moderate: <1.0")
            st.plotly_chart(fig, use_container_width=True)

        # Margin Trends
        if not historical.net_margin.empty or not historical.gross_margin.empty:
            fig = go.Figure()
            if not historical.gross_margin.empty:
                fig.add_trace(go.Scatter(
                    x=historical.years,
                    y=historical.gross_margin.values,
                    mode='lines+markers',
                    name='Gross Margin',
                    line=dict(color='#8B5CF6', width=2)
                ))
            if not historical.net_margin.empty:
                fig.add_trace(go.Scatter(
                    x=historical.years,
                    y=historical.net_margin.values,
                    mode='lines+markers',
                    name='Net Margin',
                    line=dict(color='#EC4899', width=2)
                ))
            fig.update_layout(
                title="Profit Margins",
                yaxis_title="Margin (%)",
                height=300,
                template="plotly_dark",
                legend=dict(orientation="h", y=1.1)
            )
            st.plotly_chart(fig, use_container_width=True)

    # Trend interpretation
    st.caption(
        "📊 **Trend Interpretation:** Look for improving trends (lines going up for Current Ratio, ROE, Margins; "
        "lines going down for D/E Ratio). Consistent trends are more reliable than volatile ones."
    )


def _display_quarterly_trends(symbol: str) -> None:
    """
    Display quarterly revenue and earnings trends with growth rates.

    Args:
        symbol: Stock ticker symbol
    """
    st.subheader("📊 Quarterly Performance Trends")

    try:
        import yfinance as yf

        ticker = yf.Ticker(symbol)
        quarterly_income = ticker.quarterly_financials

        if quarterly_income is None or quarterly_income.empty:
            st.info("💡 Quarterly financial data not available for this ticker.")
            return

        # Transpose and sort by date
        q_inc = quarterly_income.T
        q_inc.index = pd.to_datetime(q_inc.index)
        q_inc = q_inc.sort_index()

        # Get last 8 quarters
        q_inc = q_inc.tail(8)

        if len(q_inc) < 2:
            st.info("💡 Insufficient quarterly data (need at least 2 quarters).")
            return

        # Find columns
        rev_col = find_column(q_inc, ["TotalRevenue", "Revenue"])
        net_inc_col = find_column(q_inc, ["NetIncome", "Net Income"])

        if not rev_col and not net_inc_col:
            st.info("💡 Revenue and earnings data not found in quarterly financials.")
            return

        # Create display dataframe
        quarters = [f"Q{dt.quarter} {dt.year}" for dt in q_inc.index]

        display_data = []
        for i, (idx, row) in enumerate(q_inc.iterrows()):
            quarter_info = {"Quarter": quarters[i]}

            # Revenue
            if rev_col:
                revenue = row[rev_col]
                quarter_info["Revenue ($B)"] = f"${revenue / 1e9:.2f}B" if pd.notna(revenue) else "N/A"

                # YoY growth (compare to 4 quarters ago)
                if i >= 4:
                    prev_revenue = q_inc[rev_col].iloc[i - 4]
                    if pd.notna(revenue) and pd.notna(prev_revenue) and prev_revenue > 0:
                        yoy_growth = ((revenue - prev_revenue) / prev_revenue) * 100
                        quarter_info["Rev YoY %"] = f"{yoy_growth:+.1f}%"
                    else:
                        quarter_info["Rev YoY %"] = "N/A"
                else:
                    quarter_info["Rev YoY %"] = "N/A"

            # Earnings
            if net_inc_col:
                earnings = row[net_inc_col]
                quarter_info["Earnings ($B)"] = f"${earnings / 1e9:.2f}B" if pd.notna(earnings) else "N/A"

                # YoY growth
                if i >= 4:
                    prev_earnings = q_inc[net_inc_col].iloc[i - 4]
                    if pd.notna(earnings) and pd.notna(prev_earnings) and abs(prev_earnings) > 0:
                        yoy_growth = ((earnings - prev_earnings) / abs(prev_earnings)) * 100
                        quarter_info["Earn YoY %"] = f"{yoy_growth:+.1f}%"
                    else:
                        quarter_info["Earn YoY %"] = "N/A"
                else:
                    quarter_info["Earn YoY %"] = "N/A"

            display_data.append(quarter_info)

        # Display table
        df_display = pd.DataFrame(display_data)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Quick chart
        if rev_col:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=quarters,
                y=q_inc[rev_col].values / 1e9,
                name='Revenue',
                marker_color='#3B82F6'
            ))
            fig.update_layout(
                title="Quarterly Revenue Trend",
                yaxis_title="Revenue ($B)",
                height=300,
                template="plotly_dark",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "💡 **YoY Growth** compares each quarter to the same quarter last year, "
            "accounting for seasonal patterns. Look for consistent positive growth."
        )

    except Exception as e:
        logger.warning(f"Error fetching quarterly data for {symbol}: {e}")
        st.info(f"💡 Could not load quarterly data: {str(e)}")


def _get_api_key() -> Optional[str]:
    """Get Anthropic API key from environment or session state."""
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Check session state
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key

    return api_key


def _display_ai_insights(info: CompanyInfo, financials: FinancialsDict, symbol: str, api_key: str) -> None:
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
    info: CompanyInfo,
    financials: FinancialsDict,
    symbol: str,
    api_key: str,
) -> Optional[str]:
    """
    Generate AI insights using Claude API.
    """
    try:
        client = Anthropic(api_key=api_key)

        # Build financial summary for Claude using shared logic
        prompt = build_ai_prompt(info, financials)

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


def _display_dcf_waterfall(latest_fcf: float, result, shares_outstanding: float) -> None:
    """
    Display a waterfall chart showing the DCF calculation breakdown.

    Args:
        latest_fcf: Starting free cash flow value
        result: DCFResult object with projections and enterprise value
        shares_outstanding: Number of shares outstanding
    """
    # Calculate terminal value PV (reverse engineer from enterprise value)
    sum_proj_pv = sum(p["PV"] for p in result.projections)
    terminal_pv = result.enterprise_value - sum_proj_pv

    # Group projections into 5-year buckets
    years_1_5_pv = sum(p["PV"] for p in result.projections[0:5])
    years_6_10_pv = sum(p["PV"] for p in result.projections[5:10])

    # Prepare waterfall data
    labels = [
        "Starting FCF",
        "Years 1-5 PV",
        "Years 6-10 PV",
        "Terminal Value PV",
        "Enterprise Value",
        "Per Share Value"
    ]

    # Values for waterfall: relative changes except for totals
    measures = ["absolute", "relative", "relative", "relative", "total", "total"]

    values = [
        latest_fcf / 1e9,  # Convert to billions
        years_1_5_pv / 1e9,
        years_6_10_pv / 1e9,
        terminal_pv / 1e9,
        result.enterprise_value / 1e9,
        result.fair_value
    ]

    # Create waterfall chart
    fig = go.Figure(go.Waterfall(
        name="DCF Breakdown",
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[f"${v:.2f}B" if i < 5 else f"${v:.2f}" for i, v in enumerate(values)],
        textposition="outside",
        connector={"line": {"color": "#64748B", "width": 1}},
        decreasing={"marker": {"color": "#EF4444"}},  # Red for decreases (unlikely in DCF)
        increasing={"marker": {"color": "#10B981"}},  # Green for increases
        totals={"marker": {"color": "#3B82F6"}}  # Blue for totals
    ))

    fig.update_layout(
        title="DCF Valuation Build-Up",
        showlegend=False,
        height=450,
        template="plotly_dark",
        yaxis_title="Value (Billions $)",
        xaxis_title="",
        font=dict(size=12)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Add interpretation
    st.caption(
        f"📊 The waterfall shows how we build from **${latest_fcf / 1e9:.2f}B** in current FCF "
        f"to a fair value of **${result.fair_value:.2f}** per share. "
        f"Terminal value represents **{(terminal_pv / result.enterprise_value) * 100:.1f}%** of the total enterprise value."
    )


def _display_dcf_valuation(info: CompanyInfo, financials: FinancialsDict, symbol: str) -> None:
    """
    Display DCF (Discounted Cash Flow) valuation model with adjustable parameters.
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

    # Find Free Cash Flow column using utility
    fcf_col = find_column(cashflow_t, ["FreeCashFlow", "OperatingCashFlow"])

    if not fcf_col or len(cashflow_t) == 0:
        st.warning("⚠️ Free Cash Flow data not available for DCF valuation.")
        return

    # Get latest FCF
    latest_fcf = cashflow_t[fcf_col].iloc[-1]

    if pd.isna(latest_fcf) or latest_fcf <= 0:
        st.warning("⚠️ Invalid Free Cash Flow data (negative or missing).")
        return

    # Get current stock price and shares outstanding
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")
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

    # Calculate DCF using core logic
    st.markdown("---")
    st.markdown("#### 📊 DCF Calculation")
    
    params = DCFParameters(
        growth_years_1_5=growth_years_1_5,
        growth_years_6_10=growth_years_6_10,
        terminal_growth=terminal_growth,
        discount_rate=discount_rate,
        margin_of_safety=margin_of_safety
    )
    
    # Use the separated logic class
    result = DCFModel.calculate(
        latest_fcf=latest_fcf,
        shares_outstanding=shares_outstanding,
        current_price=current_price,
        params=params
    )

    # Display results
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    with result_col1:
        ui.animated_metric("Current Price", f"${current_price:.2f}", icon="💵")

    with result_col2:
        ui.animated_metric("Fair Value", f"${result.fair_value:.2f}", icon="⚖️")

    with result_col3:
        ui.animated_metric(
            "Upside/Downside",
            f"{result.upside_percent:+.1f}%",
            delta=f"{result.verdict.title()}",
            icon="📈" if result.upside_percent > 0 else "📉",
            color="success" if result.upside_percent > 0 else "danger"
        )

    with result_col4:
        ui.animated_metric(
            f"Cons. Value ({margin_of_safety}% MoS)",
            f"${result.conservative_value:.2f}",
            icon="🛡️"
        )

    # Valuation verdict
    if result.is_undervalued:
        st.success(f"🟢 **UNDERVALUED** - Fair value is {result.upside_percent:.1f}% above current price")
    elif result.upside_percent < -20:
         st.error(f"🔴 **OVERVALUED** - Fair value is {abs(result.upside_percent):.1f}% below current price")
    else:
        st.info("🟡 **FAIRLY VALUED** - Current price within 20% of fair value")

    # Detailed breakdown
    with st.expander("📋 Detailed DCF Breakdown", expanded=False):
        st.markdown(f"**Starting FCF:** ${latest_fcf / 1e9:.2f}B")
        st.markdown(f"**Terminal Value (PV):** ${(result.enterprise_value - sum(p['PV'] for p in result.projections)) / 1e9:.2f}B") # Reverse eng term PV for display if needed or add to result
        st.markdown(f"**Enterprise Value:** ${result.enterprise_value / 1e9:.2f}B")
        st.markdown(f"**Shares Outstanding:** {shares_outstanding / 1e9:.2f}B")

        # Show projection table
        st.markdown("##### Projected Free Cash Flows")
        projection_df = pd.DataFrame(result.projections)
        projection_df["FCF"] = projection_df["FCF"].apply(lambda x: f"${x / 1e9:.2f}B")
        projection_df["PV"] = projection_df["PV"].apply(lambda x: f"${x / 1e9:.2f}B")
        st.dataframe(projection_df, use_container_width=True, hide_index=True)

    # Waterfall Chart - Visual DCF Breakdown
    st.markdown("---")
    st.markdown("#### 💧 DCF Valuation Waterfall")
    st.caption("Visual breakdown of how we calculated the fair value")

    _display_dcf_waterfall(latest_fcf, result, shares_outstanding)

    # Sensitivity analysis
    st.markdown("---")
    st.markdown("#### 🔍 Sensitivity Analysis")
    st.caption("How fair value changes with different growth and discount rate assumptions")

    # Create sensitivity table
    discount_rates = [
        discount_rate - 2,
        discount_rate - 1,
        discount_rate,
        discount_rate + 1,
        discount_rate + 2,
    ]
    growth_rates = [growth_years_1_5 - 5, growth_years_1_5, growth_years_1_5 + 5]

    sensitivity_data = []
    for gr in growth_rates:
        row = {"Growth Rate": f"{gr:.0f}%"}
        for dr in discount_rates:
            # Recalculate with new parameters
            temp_params = DCFParameters(
                growth_years_1_5=gr,
                growth_years_6_10=growth_years_6_10,
                terminal_growth=terminal_growth,
                discount_rate=dr,
                margin_of_safety=margin_of_safety
            )
            temp_result = DCFModel.calculate(
                latest_fcf=latest_fcf,
                shares_outstanding=shares_outstanding,
                current_price=current_price,
                params=temp_params
            )

            row[f"WACC {dr:.0f}%"] = f"${temp_result.fair_value:.2f}"
        sensitivity_data.append(row)

    sensitivity_df = pd.DataFrame(sensitivity_data)
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)

    st.caption(
        "💡 **Tip:** If the stock price is below most values in the table, it may be undervalued. "
        "If it's above most values, it may be overvalued."
    )