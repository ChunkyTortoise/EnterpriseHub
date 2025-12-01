import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

            # Financial Statements Tabs
            st.markdown("---")
            st.markdown("### 📑 Financial Statements")
            
            tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
            
            with tab1:
                st.subheader("Income Statement (Annual)")
                if not financials['income_stmt'].empty:
                    st.dataframe(financials['income_stmt'], use_container_width=True)
                else:
                    st.warning("No income statement data available.")
                    
            with tab2:
                st.subheader("Balance Sheet (Annual)")
                if not financials['balance_sheet'].empty:
                    st.dataframe(financials['balance_sheet'], use_container_width=True)
                else:
                    st.warning("No balance sheet data available.")
                    
            with tab3:
                st.subheader("Cash Flow (Annual)")
                if not financials['cashflow'].empty:
                    st.dataframe(financials['cashflow'], use_container_width=True)
                else:
                    st.warning("No cash flow data available.")

    except Exception as e:
        logger.error(f"Error in Financial Analyst module: {e}", exc_info=True)
        st.error(f"An error occurred while analyzing {symbol}. Please try again.")
