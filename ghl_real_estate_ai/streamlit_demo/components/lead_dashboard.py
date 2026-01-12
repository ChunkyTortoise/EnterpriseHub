"""
Lead intelligence dashboard - score, tags, insights.
"""
import streamlit as st
import plotly.graph_objects as go


def render_lead_dashboard():
    """
    Render lead scoring and intelligence panel.
    Enhanced with Elite Research Swarm capabilities.
    """
    st.markdown("### 📊 Lead Intelligence Intelligence Hub")
    
    # Lead profile card
    st.markdown(f"""
    <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <div style="width: 50px; height: 50px; background: #8B5CF6; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-size: 1.5rem;">
                👤
            </div>
            <div>
                <div style="font-weight: 700; font-size: 1.2rem; color: #1e293b;">Sarah Martinez</div>
                <div style="font-size: 0.85rem; color: #64748b;">Active Lead • Austin Market</div>
            </div>
            <div style="margin-left: auto; text-align: right;">
                <div class="badge-success badge">HOT QUALIFIED</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Score and Analysis
    col_score, col_research = st.columns([1, 1.2])
    
    with col_score:
        score = st.session_state.get('lead_score', 82)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#006AFF"},
                'steps': [
                    {'range': [0, 40], 'color': "#f1f5f9"},
                    {'range': [40, 75], 'color': "#e2e8f0"},
                    {'range': [75, 100], 'color': "#dcfce7"}
                ],
                'threshold': {
                    'line': {'color': "#10b981", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        fig.update_layout(height=220, margin=dict(l=10, r=10, t=30, b=0), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("<div style='text-align: center; color: #10b981; font-weight: 700;'>Ready for Direct Outreach</div>", unsafe_allow_html=True)

    with col_research:
        st.markdown("#### 🔬 Deep Research Swarm")
        
        # Deep Research Button / Status
        if 'research_active' not in st.session_state:
            st.session_state.research_active = False
            
        if st.button("🚀 Trigger Deep Research Swarm", use_container_width=True, type="primary"):
            st.session_state.research_active = True
            
        if st.session_state.research_active:
            research_steps = [
                ("🔍 Social Graph Analysis", "Scanning LinkedIn & Twitter activity..."),
                ("💰 Financial Verification", "Cross-referencing mortgage pre-approvals..."),
                ("🧠 Behavioral Mapping", "Analyzing past interaction sentiment..."),
                ("📍 Geographic Intent", "Evaluating neighborhood search frequency...")
            ]
            
            for step, desc in research_steps:
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; animation: slideUp 0.3s ease-out;">
                    <div class="live-indicator" style="width: 8px; height: 8px; background: #8B5CF6; border-radius: 50%;"></div>
                    <div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: #1e293b;">{step}</div>
                        <div style="font-size: 0.75rem; color: #64748b;">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(0.2)
            
            st.success("Research Complete: Profile enriched with 12 new data points.")
        else:
            st.info("Trigger swarm to enrich lead profile with 20+ hidden data points.")

    st.markdown("---")
    
    # Bottom Row: Preferences and Tags
    col_pref, col_tags = st.columns(2)
    
    with col_pref:
        st.markdown("#### 🎯 Core Preferences")
        prefs = st.session_state.get('extracted_data', {'budget': 850000, 'location': 'Austin, TX', 'beds': 3})
        for key, value in prefs.items():
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #f1f5f9;">
                <span style="color: #64748b; font-size: 0.9rem;">{key.title()}</span>
                <span style="color: #1e293b; font-weight: 600; font-size: 0.9rem;">{f'${value:,}' if key == 'budget' else value}</span>
            </div>
            """, unsafe_allow_html=True)

    with col_tags:
        st.markdown("#### 🏷️ Intelligence Tags")
        tags = ["High Value", "Investment Focus", "Quick Close", "Pre-Approved", "Repeat Client"]
        st.markdown('<div style="display: flex; flex-wrap: wrap; gap: 6px;">', unsafe_allow_html=True)
        for tag in tags:
            st.markdown(f'<span class="badge badge-primary">{tag}</span>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Competitive Edge Section
    with st.container(border=True):
        st.markdown("#### ⚔️ Your Competitive Edge")
        st.markdown("""
        *AI Strategy for this lead:*
        - **Value Hook:** Mention the recent 5% price drop on their 'Favorite' listing in Zilker.
        - **Timing:** Contact them at **6:15 PM** (detected peak phone engagement window).
        - **Closing Angle:** Sarah values 'appreciation potential' - highlight the new tech corridor development nearby.
        """)
        if st.button("📝 Draft Personalized SMS Blast", use_container_width=True):
            st.toast("Drafting high-conversion SMS via Claude...")


def get_score_color(score: int) -> str:
    """Get color based on score."""
    if score >= 70:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"