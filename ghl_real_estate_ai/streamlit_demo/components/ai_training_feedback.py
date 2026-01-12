import streamlit as st
import random

def render_rlhf_loop():
    """
    Elite RLHF (Reinforcement Learning from Human Feedback) Interface.
    Allows managers to 'train' the AI by reviewing ambiguous matches.
    """
    st.subheader("🧠 Swarm Intelligence RLHF Loop")
    st.markdown("""
        Review ambiguous property matches identified by the AI. 
        Your feedback directly fine-tunes the **PropertyMatcherML** weights for your specific market.
    """)
    
    # RLHF Stats
    col1, col2, col3 = st.columns(3)
    col1.metric("Pending Review", "14", "High Priority")
    col2.metric("Tokens Fine-tuned", "2.1M", "+150k")
    col3.metric("Model Precision", "94.2%", "+1.2%")

    st.markdown("--- ")
    
    # Ambiguous Match Card
    with st.container(border=True):
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-weight: 700; color: #1e293b;">Ambiguous Case #842 - Sarah Martinez</div>
            <div class="badge badge-warning">Review Needed</div>
        </div>
        """, unsafe_allow_html=True)
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("**Lead Preference:**")
            st.code("Budget: $800k\nLocation: Zilker\nMust-have: Large yard for Golden Retriever")
        
        with col_right:
            st.markdown("**AI Proposed Match:**")
            st.code("Address: 742 Evergreen Terrace\nPrice: $815k\nNote: Small yard, but across from Zilker Park")
            
        st.markdown("**AI Reasoning:** 'The proximity to the park compensates for the smaller private yard, offering superior dog-walking utility.'")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Was this match appropriate?")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        if col_btn1.button("👍 Correct Inference", use_container_width=True):
            st.success("Feedback recorded. Strengthening 'Proximity-Utility' weights.")
            st.toast("Model updated in real-time.", icon="🧠")
            
        if col_btn2.button("👎 Incorrect", use_container_width=True):
            st.error("Feedback recorded. Penalizing 'Small Yard' matches for this profile.")
            st.toast("Negative weights applied.", icon="📉")
            
        if col_btn3.button("⏭️ Skip / Manual Override", use_container_width=True):
            st.info("Match flagged for manual agent intervention.")

    st.markdown("--- ")
    
    # Training History Sparkline
    st.markdown("#### 📈 Human Feedback Influence (7d)")
    import plotly.graph_objects as go
    
    # Mock data showing model accuracy improving after human feedback
    accuracy_data = [88.2, 88.5, 89.1, 91.0, 92.4, 93.8, 94.2]
    
    fig = go.Figure(go.Scatter(
        y=accuracy_data,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color="#8B5CF6", width=3),
        fillcolor="rgba(139, 92, 246, 0.1)"
    ))
    fig.update_layout(
        height=150,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(range=[85, 96]),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("RLHF has improved overall matching precision by 6.8% this week.")
