import os
from datetime import datetime
from typing import Optional

import plotly.graph_objects as go
import streamlit as st

import utils.ui as ui
from utils.data_loader import get_news
from utils.logger import get_logger
from utils.sentiment_analyzer import (
    analyze_sentiment_with_claude,
    process_news_sentiment,
)

# Conditional import for Claude API
try:
    import anthropic  # noqa: F401

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)


def _display_demo_sentiment(symbol: str) -> None:
    """Display demo sentiment analysis from pre-loaded JSON file."""
    import json

    # Load demo data
    demo_file = "data/demo_sentiment_timeline.json"
    try:
        with open(demo_file, "r") as f:
            demo_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Demo data file not found: {demo_file}")
        return

    # Find company data
    company_data = None
    for company in demo_data.get("companies", []):
        if company["symbol"] == symbol:
            company_data = company
            break

    if not company_data:
        st.warning(f"No demo data available for {symbol}")
        return

    # Extract data
    current_sentiment = company_data["current_sentiment"]
    trend = company_data["trend"]
    timeline = company_data["timeline"]

def _display_demo_sentiment(symbol: str) -> None:
    """Display demo sentiment analysis from pre-loaded JSON file."""
    import json
    import time

    # Load demo data
    demo_file = "data/demo_sentiment_timeline.json"
    try:
        with open(demo_file, "r") as f:
            demo_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Demo data file not found: {demo_file}")
        return

    # Find company data
    company_data = None
    for company in demo_data.get("companies", []):
        if company["symbol"] == symbol:
            company_data = company
            break

    if not company_data:
        st.warning(f"No demo data available for {symbol}")
        return

    # Extract data
    current_sentiment = company_data["current_sentiment"]
    trend = company_data["trend"]
    timeline = company_data["timeline"]

    # --- AGENT THOUGHT TRACE ---
    st.markdown("### 🧠 Cognitive Operations Trace")
    
    # Simulate thinking process visualization
    steps = [
        ("📡 Ingesting Data", "Scanning 14 global news sources..."),
        ("🔍 Pattern Recognition", "Identifying sentiment clusters in 48 articles..."),
        ("⚖️ Weighing Evidence", "Calibrating source credibility and recency..."),
        ("✅ Verdict Formulation", "Synthesizing final market position.")
    ]
    
    trace_cols = st.columns(4)
    for i, (step, detail) in enumerate(steps):
        with trace_cols[i]:
            st.markdown(
                f"""
                <div style='background-color: {ui.THEME["surface"]}; padding: 10px; border-radius: 6px; border: 1px solid {ui.THEME["border"]}; height: 100px;'>
                    <div style='color: {ui.THEME["accent"]}; font-weight: 600; font-size: 0.9em; margin-bottom: 5px;'>{step}</div>
                    <div style='color: {ui.THEME["text_light"]}; font-size: 0.75em;'>{detail}</div>
                    <div style='margin-top: 8px; height: 4px; background: {ui.THEME["border"]}; border-radius: 2px;'>
                        <div style='width: 100%; height: 100%; background: {ui.THEME["accent"]}; border-radius: 2px; opacity: 0.8;'></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    ui.spacer(20)

    # --- Dashboard ---
    # Sentiment score (scale from 0-1 to -100 to 100)
    sentiment_scaled = (current_sentiment - 0.5) * 200  # 0.74 -> 48

    # Layout: Gauge on Left, Stats on Right
    d_col1, d_col2 = st.columns([1, 1])

    with d_col1:
         # Gauge Chart
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=sentiment_scaled,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "AI Sentiment Score", "font": {"color": ui.THEME["text_main"]}},
                gauge={
                    "axis": {"range": [-100, 100], "tickcolor": ui.THEME["text_light"]},
                    "bar": {"color": ui.THEME["primary"]},  # Theme primary
                    "bgcolor": ui.THEME["background"],
                    "steps": [
                        {"range": [-100, -20], "color": "#EF4444"},  # Red
                        {"range": [-20, 20], "color": "#94A3B8"},  # Gray
                        {"range": [20, 100], "color": "#10B981"},  # Emerald
                    ],
                    "threshold": {
                        "line": {"color": ui.THEME["text_main"], "width": 4},
                        "thickness": 0.75,
                        "value": sentiment_scaled,
                    },
                },
            )
        )
        fig.update_layout(
            height=300, 
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': ui.THEME["text_main"]}
        )
        st.plotly_chart(fig, use_container_width=True)

    with d_col2:
        if trend == "very_bullish":
            verdict = "STRONG BUY"
            verdict_icon = "🚀"
            verdict_color = ui.THEME["success"]
        elif trend == "bullish":
            verdict = "BULLISH"
            verdict_icon = "📈"
            verdict_color = ui.THEME["success"]
        elif trend == "bearish":
            verdict = "BEARISH"
            verdict_icon = "📉"
            verdict_color = ui.THEME["danger"]
        else:
            verdict = "NEUTRAL"
            verdict_icon = "➡️"
            verdict_color = ui.THEME["text_light"]

        ui.glassmorphic_card(
            title="AI Market Verdict",
            content=f"""
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 10px;'>
                    <span style='font-size: 2em;'>{verdict_icon}</span>
                    <h2 style='margin: 0; color: {verdict_color};'>{verdict}</h2>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 10px;'>
                    <div>
                        <div style='font-size: 0.8em; color: {ui.THEME["text_light"]};'>Confidence</div>
                        <div style='font-weight: 600; font-size: 1.1em;'>{current_sentiment * 100:.1f}%</div>
                    </div>
                    <div>
                        <div style='font-size: 0.8em; color: {ui.THEME["text_light"]};'>Source Volume</div>
                        <div style='font-weight: 600; font-size: 1.1em;'>{len(timeline)} Articles</div>
                    </div>
                </div>
            """,
            cta_text="View Full Analysis",
            cta_url="#"
        )

    # --- Sentiment Timeline Chart ---
    ui.spacer(20)
    st.markdown("### 📊 Sentiment Trajectory")

    # Create timeline chart
    dates = [item["date"] for item in timeline]
    scores = [item["sentiment_score"] for item in timeline]

    fig_timeline = go.Figure()
    fig_timeline.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="Sentiment Score",
            line=dict(color=ui.THEME["accent"], width=3),
            marker=dict(size=8, color=ui.THEME["primary"]),
            fill='tozeroy',
            fillcolor=f"{ui.THEME['accent']}20" # 20% opacity
        )
    )
    fig_timeline.update_layout(
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        yaxis=dict(range=[0, 1]),
        height=350,
        showlegend=False,
        template=ui.get_plotly_template()
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

    # --- News Feed ---
    ui.spacer(20)
    st.markdown("### 📰 Intel Feed")

    for item in timeline:
        score = item["sentiment_score"]
        if score > 0.7:
            badge = ui.status_badge("active") # Positive
            border_color = "#10B981"
        elif score < 0.4:
            badge = ui.status_badge("hero") # Negative
            border_color = "#EF4444"
        else:
            badge = ui.status_badge("pending") # Neutral
            border_color = "#94A3B8"

        st.markdown(
            f"""
            <div style='background-color: {ui.THEME["surface"]}; border-left: 4px solid {border_color}; 
                        padding: 1.25rem; border-radius: 6px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div style='font-weight: 600; font-size: 1.05rem; margin-bottom: 0.5rem;'>{item['headline']}</div>
                    <div>{badge}</div>
                </div>
                <div style='display: flex; gap: 15px; font-size: 0.85rem; color: {ui.THEME["text_light"]};'>
                    <span>📅 {item['date']}</span>
                    <span>🤖 Score: {score:.2f}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render() -> None:
    """Render the Agent Logic (Sentiment Scout) module."""
    ui.section_header("Agent Logic: Sentiment Scout", "AI-Powered Market Sentiment Analysis")

    # Demo Mode Toggle (default True for reliable demos)
    demo_mode = st.checkbox(
        "🎯 Demo Mode (Use Sample Data)",
        value=True,
        help="Toggle to use sample sentiment analysis data without API calls. Recommended for demos.",
    )

    # Input
    col1, col2 = st.columns([1, 3])
    with col1:
        if demo_mode:
            symbol = st.selectbox("Select Demo Company", ["AAPL", "TSLA", "GOOGL", "MSFT"], index=0)
            st.caption("💡 Demo mode uses pre-loaded data")
        else:
            symbol = st.text_input("Analyze Ticker", value="AAPL", max_chars=5).upper()

    with col2:
        if not demo_mode:
            # Check for API key
            api_key = _get_api_key()
            if api_key and ANTHROPIC_AVAILABLE:
                use_ai_sentiment = st.toggle(
                    "AI Sentiment (Claude)", value=False, key="ai_sentiment_toggle"
                )
            else:
                use_ai_sentiment = False
                st.caption("Enable AI sentiment by adding ANTHROPIC_API_KEY")
        else:
            use_ai_sentiment = False

    if not symbol:
        st.info("Enter a ticker to scout sentiment.")
        return

    try:
        if demo_mode:
            _display_demo_sentiment(symbol)
        else:
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
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=analysis["average_score"] * 100,  # Scale to -100 to 100
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "AI Sentiment Score"},
                    delta={"reference": 0},
                    gauge={
                        "axis": {"range": [-100, 100]},
                        "bar": {"color": "white"},
                        "steps": [
                            {"range": [-100, -10], "color": "#ff4444"},  # Red
                            {"range": [-10, 10], "color": "#888888"},  # Gray
                            {"range": [10, 100], "color": "#00ff88"},  # Green
                        ],
                        "threshold": {
                            "line": {"color": "white", "width": 4},
                            "thickness": 0.75,
                            "value": analysis["average_score"] * 100,
                        },
                    },
                )
            )
            fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))

            # Layout: Gauge on Left, Stats on Right
            d_col1, d_col2 = st.columns([1, 1])

            with d_col1:
                st.plotly_chart(fig, use_container_width=True)

            with d_col2:
                # Cinematic Verdict Card
                verdict_color = (
                    ui.THEME["success"]
                    if "BULLISH" in analysis["verdict"].upper()
                    else ui.THEME["danger"]
                    if "BEARISH" in analysis["verdict"].upper()
                    else ui.THEME["secondary"]
                )
                st.markdown(
                    f"""
                <div style="background:{ui.THEME["surface"]}; padding:1.5rem;
                     border-radius:8px; border-left:5px solid {verdict_color};">
                    <p style="text-transform:uppercase; font-size:0.8rem;
                       font-weight:700; color:{ui.THEME["text_light"]};
                       margin:0;">AI Market Verdict</p>
                    <h2 style="margin:0.5rem 0; color:{verdict_color};
                        border:none; padding:0;">{analysis["verdict"]}</h2>
                    <p style="font-size:0.9rem; margin:0;">
                        Confidence: <b>{abs(analysis["average_score"]) * 100:.1f}%</b>
                        | Articles: <b>{analysis["article_count"]}</b></p>
                </div>
                """,
                    unsafe_allow_html=True,
                )

                st.write("")  # Spacer

                # Show analysis method
                if use_ai_sentiment:
                    st.info("Analysis powered by Claude AI with contextual reasoning.")
                else:
                    st.info("Analysis based on NLP processing of latest news headlines.")

                # Show AI reasoning if available
                if "reasoning" in analysis and analysis["reasoning"]:
                    with st.expander("🧠 AI Reasoning"):
                        st.markdown(analysis["reasoning"])

            # --- News Feed ---
            st.subheader("📰 News Feed & Sentiment")

            for item in analysis["processed_news"]:
                with st.expander(f"{item['sentiment_label']} | {item['title']}"):
                    st.markdown(f"**Publisher:** {item.get('publisher', 'Unknown')}")
                    st.markdown(f"**Sentiment Score:** {item['sentiment_score']:.2f}")

                    # Convert timestamp if available
                    ts = item.get("providerPublishTime")
                    if ts:
                        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
                        st.caption(f"Published: {date_str}")

                    link = item.get("link")
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
