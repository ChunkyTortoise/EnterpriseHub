"""
Market Pulse Demo - Public Streamlit App
"""

import streamlit as st

# FAST BOOT: Do not import heavy libraries (pandas, plotly, yfinance) here.
# Only import streamlit at the top level.

st.set_page_config(
    page_title="Market Pulse Demo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def main():
    st.info("👋 **Welcome to the Market Pulse Demo**")
    
    # Lazy load heavy modules ONLY when the app actually runs
    with st.spinner("Loading financial engine..."):
        try:
            # Import strictly what is needed
            from modules.market_pulse import render
            render()
        except ImportError as e:
            st.error(f"Module Error: {e}")
        except Exception as e:
            st.error(f"Runtime Error: {e}")

if __name__ == "__main__":
    main()
