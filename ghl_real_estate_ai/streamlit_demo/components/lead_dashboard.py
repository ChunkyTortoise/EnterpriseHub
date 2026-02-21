"""
Lead intelligence dashboard - score, tags, insights.
"""

import streamlit as st


def render_lead_dashboard():
    """
    Render lead scoring and intelligence panel - Obsidian Command Edition.
    """
    from ghl_real_estate_ai.streamlit_demo.obsidian_theme import style_obsidian_chart

    st.markdown("### 📊 LEAD INTELLIGENCE TELEMETRY")
    st.markdown(
        f"""\n    <div style="background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 2rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px);">\n        <div style="display: flex; align-items: center; gap: 20px;">\n            <div style="width: 50px; height: 50px; background: rgba(99, 102, 241, 0.1); border-radius: 10px; display: flex; align-items: center; justify-content: center; color: #6366F1; font-size: 1.5rem; border: 1px solid rgba(99, 102, 241, 0.2); box-shadow: 0 0 15px rgba(99, 102, 241, 0.2);">\n                👤\n            </div>\n            <div>\n                <div style="font-weight: 700; font-size: 1.5rem; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">SARAH MARTINEZ</div>\n                <div style="font-size: 0.85rem; color: #8B949E; font-family: 'Inter', sans-serif; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;">ACTIVE NODE • SECTOR: RANCHO CUCAMONGA</div>\n            </div>\n            <div style="margin-left: auto; text-align: right;">\n                <span style='background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px 16px; border-radius: 8px; font-size: 0.75rem; font-weight: 800; border: 1px solid rgba(16, 185, 129, 0.3); text-transform: uppercase; letter-spacing: 0.1em; font-family: "Space Grotesk", sans-serif;'>HOT QUALIFIED</span>\n            </div>\n        </div>\n    </div>\n    """,
        unsafe_allow_html=True,
    )
    col_score, col_research = st.columns([1, 1.2])
    with col_score:
        score = st.session_state.get("lead_score", 82)
        import plotly.graph_objects as go

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=score,
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#8B949E"},
                    "bar": {"color": "#6366F1"},
                    "bgcolor": "rgba(255,255,255,0.05)",
                    "borderwidth": 1,
                    "bordercolor": "rgba(255,255,255,0.1)",
                    "steps": [
                        {"range": [0, 40], "color": "rgba(239, 68, 68, 0.1)"},
                        {"range": [40, 75], "color": "rgba(245, 158, 11, 0.1)"},
                        {"range": [75, 100], "color": "rgba(16, 185, 129, 0.1)"},
                    ],
                    "threshold": {"line": {"color": "#10b981", "width": 4}, "thickness": 0.75, "value": 80},
                },
            )
        )
        st.plotly_chart(style_obsidian_chart(fig), use_container_width=True)
        st.markdown(
            "<div style='text-align: center; color: #10b981; font-weight: 700; font-family: \"Space Grotesk\", sans-serif; text-transform: uppercase; letter-spacing: 0.1em;'>READY FOR COMMAND SYNC</div>",
            unsafe_allow_html=True,
        )
    with col_research:
        st.markdown("#### 🔬 DEEP RESEARCH SWARM")
        if "research_active" not in st.session_state:
            st.session_state.research_active = False
        if st.button("🚀 TRIGGER RESEARCH SWARM", use_container_width=True, type="primary"):
            st.session_state.research_active = True
        if st.session_state.research_active:
            research_steps = [
                ("🔍 SOCIAL GRAPH ANALYSIS", "Scanning target digital footprint..."),
                ("💰 FISCAL VERIFICATION", "Validating pre-approval credentials..."),
                ("🧠 BEHAVIORAL MAPPING", "Synthesizing interaction sentiment..."),
                ("📍 GEOGRAPHIC INTENT", "Calibrating sector-specific gravity..."),
            ]
            import time

            for step, desc in research_steps:
                st.markdown(
                    f"""\n                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 15px; animation: slideUp 0.3s ease-out;">\n                    <div class="status-pulse" style="width: 10px; height: 10px;"></div>\n                    <div>\n                        <div style="font-size: 0.85rem; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;">{step}</div>\n                        <div style="font-size: 0.75rem; color: #8B949E; font-family: 'Inter', sans-serif;">{desc}</div>\n                    </div>\n                </div>\n                """,
                    unsafe_allow_html=True,
                )
                time.sleep(0.2)
            st.success("Analysis Complete: Node identity enriched with 12 signals.")
        else:
            st.info("Trigger swarm to initialize deep node enrichment protocol.")
    st.markdown("---")
    col_pref, col_tags = st.columns(2)
    with col_pref:
        st.markdown("#### 🎯 CORE PARAMETERS")
        prefs = st.session_state.get(
            "extracted_data", {"budget": 850000, "location": "Rancho Cucamonga, CA", "beds": 3}
        )
        for key, value in prefs.items():
            st.markdown(
                f"""\n            <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">\n                <span style="color: #8B949E; font-size: 0.85rem; text-transform: uppercase; font-weight: 700; font-family: 'Space Grotesk', sans-serif;">{key}</span>\n                <span style="color: #FFFFFF; font-weight: 600; font-size: 0.9rem; font-family: 'Inter', sans-serif;">{(f"${value:,}" if key == "budget" else value)}</span>\n            </div>\n            """,
                unsafe_allow_html=True,
            )
    with col_tags:
        st.markdown("#### 🏷️ INTELLIGENCE TAGS")
        tags = ["High Value", "Investment Focus", "Quick Close", "Pre-Approved", "Repeat Client"]
        st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 8px;">', unsafe_allow_html=True)
        for tag in tags:
            st.markdown(
                f"""<span style="background: rgba(99, 102, 241, 0.1); color: #6366F1; padding: 6px 14px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; border: 1px solid rgba(99, 102, 241, 0.2); font-family: 'Space Grotesk', sans-serif; text-transform: uppercase;">{tag}</span>""",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        f"""\n    <div style="background: rgba(99, 102, 241, 0.05); padding: 2rem; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.2); border-left: 5px solid #6366F1;">\n        <h4 style="margin: 0 0 1rem 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; letter-spacing: 0.05em; display: flex; align-items: center; gap: 10px;">\n            <span style="font-size: 1.5rem;">⚔️</span> TACTICAL COMMAND EDGE\n        </h4>\n        <div style="color: #E6EDF3; font-family: 'Inter', sans-serif; line-height: 1.7; opacity: 0.9;">\n            <p style="margin-bottom: 1rem; font-weight: 600; color: #6366F1; font-size: 0.9rem;">AI STRATEGIC DIRECTIVE FOR THIS NODE:</p>\n            <ul style="margin: 0; padding-left: 1.25rem;">\n                <li><b style="color: #FFFFFF;">Value Hook:</b> Highlighting recent 5% variance on 'Priority' node in Victoria Gardens sector.</li>\n                <li><b style="color: #FFFFFF;">Optimal Sync:</b> Establish contact at <b style="color: #10b981;">18:15</b> (detected peak engagement window).</li>\n                <li><b style="color: #FFFFFF;">Closing Vector:</b> Node prioritizes 'appreciation trajectory' - pivot to tech corridor expansion dataset.</li>\n            </ul>\n        </div>\n    </div>\n    """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
    if st.button("📝 DRAFT NEURAL SMS SIGNAL", use_container_width=True):
        st.toast("Synthesizing high-conversion response via Claude...", icon="🧠")


@st.cache_data(ttl=300)
def get_score_color(score: int) -> str:
    """Get color based on score."""
    if score >= 70:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"
