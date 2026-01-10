"""
Lead intelligence dashboard - score, tags, insights.
"""
import streamlit as st
import plotly.graph_objects as go


def render_lead_dashboard():
    """Render lead scoring and intelligence panel."""
    st.markdown("### 📊 Lead Intelligence")

    # Lead score gauge
    score = st.session_state.get('lead_score', 0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Lead Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': get_score_color(score)},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))

    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, width='stretch')

    # Tags
    st.markdown("#### 🏷️ Tags Applied")
    tags = st.session_state.get('tags', [])
    if tags:
        cols = st.columns(2)
        for i, tag in enumerate(tags):
            with cols[i % 2]:
                st.markdown(f"`{tag}`")
    else:
        st.info("No tags yet - chat to build profile")

    # Extracted data insights
    st.markdown("#### 📋 Extracted Preferences")
    prefs = st.session_state.get('extracted_data', {})
    if prefs:
        for key, value in prefs.items():
            if key == 'budget':
                st.write(f"**Budget:** ${value:,}")
            else:
                st.write(f"**{key.title()}:** {value}")
    else:
        st.info("No preferences extracted yet")


def get_score_color(score: int) -> str:
    """Get color based on score."""
    if score >= 70:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"