"""
Multi-Agent Workflow Orchestrator.

This module acts as the central command center, coordinating specialized 'agents'
(logical units) to perform complex, multi-step analysis workflows.
"""

import streamlit as st
import pandas as pd
import time
import utils.ui as ui
from utils.data_loader import get_stock_data, calculate_indicators, get_company_info, get_news
from utils.sentiment_analyzer import process_news_sentiment
from utils.logger import get_logger

logger = get_logger(__name__)

def render() -> None:
    """Render the Multi-Agent Orchestrator interface."""
    ui.section_header("🤖 Multi-Agent Workflows", "Autonomous Analysis Teams")

    # Workflow Selection
    workflow = st.selectbox(
        "Select Workflow",
        ["💰 Stock Deep Dive (3 Agents)", "📊 Market Scanner (Coming Soon)", "📢 Content Generator (Coming Soon)"]
    )

    if workflow == "💰 Stock Deep Dive (3 Agents)":
        _render_stock_deep_dive()
    else:
        st.info("This workflow is currently under development.")


def _render_stock_deep_dive():
    """Execute the Stock Deep Dive workflow."""
    st.markdown("""
    **Mission:** Comprehensive analysis of a target asset.
    
    **The Team:**
    - 🕵️ **DataBot:** Fetches raw price action and fundamental data.
    - 📈 **TechBot:** Analyzes technical indicators (RSI, MACD, Trends).
    - 📰 **NewsBot:** Scouts recent news and analyzes sentiment.
    - 🎓 **ChiefBot:** Synthesizes all intelligence into a final verdict.
    """)

    col1, col2 = st.columns([1, 4])
    with col1:
        ticker = st.text_input("Target Asset", value="NVDA").upper()
    
    start_btn = st.button("🚀 Launch Workflow", type="primary")

    if start_btn and ticker:
        _run_deep_dive_logic(ticker)


def _run_deep_dive_logic(ticker: str):
    """Orchestrate the deep dive agents."""
    
    # Container for live updates
    status_container = st.container()
    
    results = {}

    try:
        # --- AGENT 1: DATABOT ---
        with status_container:
            with st.spinner("🕵️ DataBot: Infiltrating exchanges..."):
                time.sleep(0.5) # UX pause
                df = get_stock_data(ticker, period="1y", interval="1d")
                info = get_company_info(ticker)
                
                if df is None or df.empty:
                    st.error(f"❌ DataBot: Mission Failed. No data for {ticker}.")
                    return

                results['price'] = df.iloc[-1]['Close']
                results['info'] = info
                st.success(f"🕵️ DataBot: Data secured. Price: ${results['price']:.2f} | Sector: {info.get('sector', 'Unknown')}")

        # --- AGENT 2: TECHBOT ---
        with status_container:
            with st.spinner("📈 TechBot: Crunching numbers..."):
                time.sleep(0.5)
                df = calculate_indicators(df)
                
                last_row = df.iloc[-1]
                rsi = last_row['RSI']
                macd = last_row['MACD']
                signal = last_row['Signal_Line']
                
                results['rsi'] = rsi
                results['macd_signal'] = "BULLISH" if macd > signal else "BEARISH"
                
                rsi_status = "OVERSOLD (Buy Signal)" if rsi < 30 else "OVERBOUGHT (Sell Signal)" if rsi > 70 else "NEUTRAL"
                
                st.success(f"📈 TechBot: Analysis complete. RSI: {rsi:.1f} ({rsi_status}) | MACD: {results['macd_signal']}")

        # --- AGENT 3: NEWSBOT ---
        with status_container:
            with st.spinner("📰 NewsBot: Scanning global wires..."):
                time.sleep(0.5)
                news = get_news(ticker)
                sentiment = process_news_sentiment(news)
                
                results['sentiment_score'] = sentiment['average_score']
                results['sentiment_verdict'] = sentiment['verdict']
                
                st.success(f"📰 NewsBot: {sentiment['article_count']} intel reports analyzed. Verdict: {sentiment['verdict']} (Score: {sentiment['average_score']:.2f})")

        # --- AGENT 4: CHIEFBOT (Synthesis) ---
        st.markdown("---")
        st.subheader(f"🎓 ChiefBot Executive Summary: {ticker}")
        
        # Scoring Logic
        score = 0
        reasons = []
        
        # Technical Score
        if results['rsi'] < 35:
            score += 1
            reasons.append("Asset is Oversold (RSI < 35)")
        elif results['rsi'] > 65:
            score -= 1
            reasons.append("Asset is Overbought (RSI > 65)")
        
        if results['macd_signal'] == "BULLISH":
            score += 1
            reasons.append("MACD Momentum is Bullish")
        else:
            score -= 1
            reasons.append("MACD Momentum is Bearish")

        # Sentiment Score
        if results['sentiment_score'] > 0.15:
            score += 1
            reasons.append("News Sentiment is Positive")
        elif results['sentiment_score'] < -0.15:
            score -= 1
            reasons.append("News Sentiment is Negative")
        
        # Final Verdict
        if score >= 2:
            verdict = "STRONG BUY"
            color = "success"
        elif score == 1:
            verdict = "BUY"
            color = "success"
        elif score == 0:
            verdict = "HOLD"
            color = "warning"
        elif score == -1:
            verdict = "SELL"
            color = "danger"
        else:
            verdict = "STRONG SELL"
            color = "danger"

        # Display Final Card
        st.markdown(f"""
        <div style="padding: 20px; border-radius: 10px; border: 2px solid #e0e0e0; background-color: #f9f9f9;">
            <h2 style="text-align: center; margin-top: 0;">RECOMMENDATION: <span style="color: {ui.THEME.get(color, 'black')}">{verdict}</span></h2>
            <p style="text-align: center; font-size: 1.2em;">Confidence Score: {score}/3 Factors</p>
            <hr>
            <h4>📋 Key Drivers:</h4>
            <ul>
                {''.join([f'<li>{r}</li>' for r in reasons])}
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable Data details
        with st.expander("🔍 Inspect Raw Intelligence"):
            st.write(results)

    except Exception as e:
        logger.error(f"Workflow failed: {e}", exc_info=True)
        st.error(f"❌ Mission Aborted: {str(e)}")
