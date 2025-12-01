import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.data_loader import get_company_info, get_financials
from utils.logger import get_logger

logger = get_logger(__name__)

def render() -> None:
    """Render the Financial Analyst module."""
    st.title("💼 Financial Analyst")
    st.markdown("### Fundamental Analysis & Company Metrics")

    # Input Section
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol = st.text_input("Enter Ticker Symbol", value="AAPL", max_chars=5).upper()
    
    if not symbol:
        st.info("Please enter a ticker symbol to begin.")
        return

    try:
        with st.spinner(f"Analyzing {symbol}..."):
            # Fetch Data
            info = get_company_info(symbol)
            financials = get_financials(symbol)
            
            if not info:
                st.error(f"Could not find data for {symbol}")
                return

            # Company Header
            st.markdown("---")
            header_col1, header_col2 = st.columns([3, 1])
            with header_col1:
                st.header(f"{info.get('longName', symbol)} ({symbol})")
                st.caption(f"{info.get('sector', 'N/A')} | {info.get('industry', 'N/A')} | {info.get('country', 'N/A')}")
                st.markdown(f"**Summary:** {info.get('longBusinessSummary', 'No summary available.')[:300]}...")
            
            with header_col2:
                if 'website' in info:
                    st.markdown(f"[🌐 Visit Website]({info['website']})")
            
            # Key Metrics Row
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

            # --- VISUALIZATION SECTION ---
            st.markdown("---")
            st.markdown("### 📈 Financial Performance")
            
            # Prepare Data for Charts
            income_stmt = financials['income_stmt'].T if not financials['income_stmt'].empty else pd.DataFrame()
            balance_sheet = financials['balance_sheet'].T if not financials['balance_sheet'].empty else pd.DataFrame()
            
            if not income_stmt.empty:
                # Ensure index is datetime and sort
                income_stmt.index = pd.to_datetime(income_stmt.index)
                income_stmt = income_stmt.sort_index()
                
                # Chart 1: Revenue vs Net Income
                fig_perf = make_subplots(specs=[[{"secondary_y": True}]])
                
                # Try to find correct columns (yfinance column names can vary)
                rev_col = next((col for col in income_stmt.columns if 'Total Revenue' in str(col) or 'Revenue' in str(col)), None)
                net_inc_col = next((col for col in income_stmt.columns if 'Net Income' in str(col)), None)
                
                if rev_col and net_inc_col:
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
                    
                    # Profit Margins
                    st.markdown("#### 📊 Profitability Ratios")
                    r1, r2, r3 = st.columns(3)
                    
                    latest = income_stmt.iloc[-1]
                    revenue = latest[rev_col]
                    net_income = latest[net_inc_col]
                    
                    # Gross Profit
                    gross_col = next((col for col in income_stmt.columns if 'Gross Profit' in str(col)), None)
                    gross_profit = latest[gross_col] if gross_col else 0
                    
                    with r1:
                        net_margin = (net_income / revenue) * 100 if revenue else 0
                        st.metric("Net Profit Margin", f"{net_margin:.1f}%")
                    
                    with r2:
                        gross_margin = (gross_profit / revenue) * 100 if revenue else 0
                        st.metric("Gross Margin", f"{gross_margin:.1f}%")
                        
                    with r3:
                        # YoY Revenue Growth
                        if len(income_stmt) > 1:
                            prev_rev = income_stmt.iloc[-2][rev_col]
                            growth = ((revenue - prev_rev) / prev_rev) * 100
                            st.metric("YoY Revenue Growth", f"{growth:+.1f}%")
                        else:
                            st.metric("YoY Revenue Growth", "N/A")

            # --- DATA TABLES SECTION ---
            st.markdown("---")
            st.markdown("### 📑 Detailed Financial Statements")
            
            tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
            
            with tab1:
                st.subheader("Income Statement")
                if not financials['income_stmt'].empty:
                    st.dataframe(financials['income_stmt'], use_container_width=True)
                else:
                    st.warning("No data available.")
                    
            with tab2:
                st.subheader("Balance Sheet")
                if not financials['balance_sheet'].empty:
                    st.dataframe(financials['balance_sheet'], use_container_width=True)
                else:
                    st.warning("No data available.")
                    
            with tab3:
                st.subheader("Cash Flow")
                if not financials['cashflow'].empty:
                    st.dataframe(financials['cashflow'], use_container_width=True)
                else:
                    st.warning("No data available.")

    except Exception as e:
        logger.error(f"Error in Financial Analyst module: {e}", exc_info=True)
        st.error(f"An error occurred while analyzing {symbol}. Please try again.")
