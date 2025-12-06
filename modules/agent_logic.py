import streamlit as st
import plotly.graph_objects as go
import os
from typing import Optional
from utils.data_loader import get_news
from utils.sentiment_analyzer import process_news_sentiment, analyze_sentiment_with_claude
from utils.logger import get_logger
from datetime import datetime

# Conditional import for Claude API
try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)

def render() -> None:
    """Render the Agent Logic (Sentiment Scout) module."""
    st.title("🤖 Agent Logic: Sentiment Scout")
    st.markdown("### AI-Powered Market Sentiment Analysis")

    # Input
    col1, col2 = st.columns([1, 3])
    with col1:
        symbol = st.text_input("Analyze Ticker", value="AAPL", max_chars=5).upper()

    with col2:
        # Check for API key
        api_key = _get_api_key()
        if api_key and ANTHROPIC_AVAILABLE:
            use_ai_sentiment = st.toggle("AI Sentiment (Claude)", value=False, key="ai_sentiment_toggle")
        else:
            use_ai_sentiment = False
            st.caption("Enable AI sentiment by adding ANTHROPIC_API_KEY")

    if not symbol:
        st.info("Enter a ticker to scout sentiment.")
        return

    try:
        with st.spinner(f"Scouting news and analyzing sentiment for {symbol}..."):
            # 1. Fetch News
            news_items = get_news(symbol)

            if not news_items:
                st.warning(f"No recent news found for {symbol}.")
                return

            # 2. Analyze Sentiment
            if use_ai_sentiment and api_key:
                analysis = analyze_sentiment_with_claude(news_items, symbol, api_key)
            else:
                analysis = process_news_sentiment(news_items)
            
            # --- Dashboard ---
            st.markdown("---")
            
            # Gauge Chart
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = analysis['average_score'] * 100, # Scale to -100 to 100
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "AI Sentiment Score"},
                delta = {'reference': 0},
                gauge = {
                    'axis': {'range': [-100, 100]},
                    'bar': {'color': "white"},
                    'steps': [
                        {'range': [-100, -10], 'color': "#ff4444"}, # Red
                        {'range': [-10, 10], 'color': "#888888"},  # Gray
                        {'range': [10, 100], 'color': "#00ff88"}   # Green
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': analysis['average_score'] * 100
                    }
                }
            ))
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
            
            # Layout: Gauge on Left, Stats on Right
            d_col1, d_col2 = st.columns([1, 1])
            
            with d_col1:
                st.plotly_chart(fig, use_container_width=True)
                
            with d_col2:
                st.subheader("AI Verdict")
                st.markdown(f"## {analysis['verdict']}")
                st.markdown(f"**Confidence:** {abs(analysis['average_score']) * 100:.1f}%")
                st.markdown(f"**Articles Analyzed:** {analysis['article_count']}")

                # Show analysis method
                if use_ai_sentiment:
                    st.info("Analysis powered by Claude AI with contextual reasoning.")
                else:
                    st.info("Analysis based on NLP processing of latest news headlines.")

                # Show AI reasoning if available
                if 'reasoning' in analysis and analysis['reasoning']:
                    with st.expander("🧠 AI Reasoning"):
                        st.markdown(analysis['reasoning'])

            # --- News Feed ---
            st.markdown("### 📰 News Feed & Sentiment")
            
            for item in analysis['processed_news']:
                with st.expander(f"{item['sentiment_label']} | {item['title']}"):
                    st.markdown(f"**Publisher:** {item.get('publisher', 'Unknown')}")
                    st.markdown(f"**Sentiment Score:** {item['sentiment_score']:.2f}")
                    
                    # Convert timestamp if available
                    ts = item.get('providerPublishTime')
                    if ts:
                        date_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                        st.caption(f"Published: {date_str}")
                        
                    link = item.get('link')
                    if link:
                        st.markdown(f"[Read Full Article]({link})")

    except Exception as e:
        logger.error(f"Error in Agent Logic module: {e}", exc_info=True)
        st.error(f"An error occurred while scouting {symbol}.")


def _get_api_key() -> Optional[str]:
    """Get Anthropic API key from environment or session state."""
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Check session state
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key

    return api_key
