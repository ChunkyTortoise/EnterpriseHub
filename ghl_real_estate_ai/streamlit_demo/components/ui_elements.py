import streamlit as st

def render_action_card(title, description, icon, key_suffix=""):
    """
    Render a consistent premium action card with GHL trigger simulation.
    """
    st.markdown(f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 12px; border-left: 4px solid #2563eb; background: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.25rem;">{icon}</span>
                <b style="color: #1e293b; font-size: 1rem;">{title}</b>
            </div>
            <p style="font-size: 13px; color: #64748b; margin-top: 8px; line-height: 1.4;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🚀 Run Action", key=f"run_action_{key_suffix}_{title.lower().replace(' ', '_')}", use_container_width=True):
            with st.spinner("Executing GHL trigger..."):
                import time
                time.sleep(1)
                st.toast(f"✅ Success: {title} triggered", icon="⚡")

def render_insight_card(title, value, description, status='info', action_label=None, action_key=None):
    """
    Renders a high-fidelity AI insight card with optional hub redirection.
    """
    colors = {
        'success': 'rgba(16, 185, 129, 0.1)', 
        'warning': 'rgba(245, 158, 11, 0.1)', 
        'info': 'rgba(59, 130, 246, 0.1)',
        'danger': 'rgba(239, 68, 68, 0.1)'
    }
    border_colors = {
        'success': '#10B981', 
        'warning': '#F59E0B', 
        'info': '#3B82F6',
        'danger': '#EF4444'
    }
    icon = '✅' if status == 'success' else '⚠️' if status == 'warning' else '🚨' if status == 'danger' else '💡'
    
    st.markdown(f"""
        <div style="background-color: {colors.get(status, colors['info'])}; padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem; border-left: 5px solid {border_colors.get(status, border_colors['info'])};">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 0.5rem;">
                <span style="font-size: 1.5rem;">{icon}</span>
                <b style="color: #1e293b; font-size: 1.1rem;">{title}</b>
            </div>
            <div style="font-size: 1.75rem; font-weight: 900; color: #1e3a8a; margin: 0.5rem 0;">{value}</div>
            <p style="font-size: 0.95rem; color: #475569; margin: 0;">{description}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_key:
        if st.button(action_label, key=action_key, use_container_width=True):
            st.session_state.current_hub = "🧠 Lead Intelligence Hub"
            st.rerun()