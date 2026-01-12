import streamlit as st

def render_action_card(title, description, icon, key_suffix=""):
    """Render a consistent premium action card"""
    st.markdown(f"""
    <div class="action-card">
        <div style="font-size: 2rem; margin-bottom: 1rem;">{icon}</div>
        <div style="font-weight: 700; font-size: 1.1rem; margin-bottom: 0.5rem;">{title}</div>
        <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 1rem;">{description}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(f"Launch {title}", key=f"btn_{title.lower().replace(' ', '_')}{key_suffix}", use_container_width=True):
        st.toast(f"Launching {title}...")

def render_insight_card(title, value, description, status='info', action_label=None, action_key=None):
    """Renders a high-fidelity AI insight card"""
    colors = {
        'info': ('#E0E7FF', '#1E40AF', '#3730A3'),
        'success': ('#DCFCE7', '#166534', '#15803D'),
        'warning': ('#FEF3C7', '#92400E', '#B45309'),
        'danger': ('#FEE2E2', '#991B1B', '#B91C1C')
    }
    bg, text, accent = colors.get(status, colors['info'])
    
    st.markdown(f"""
    <div style='background: {bg}; padding: 1.5rem; border-radius: 12px; border-left: 5px solid {accent}; margin-bottom: 1rem;'>
        <div style='color: {accent}; font-weight: 700; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;'>{title}</div>
        <div style='color: {text}; font-size: 1.75rem; font-weight: 800; margin: 0.5rem 0;'>{value}</div>
        <div style='color: {text}; font-size: 0.95rem; opacity: 0.9; line-height: 1.5;'>{description}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_key:
        if st.button(action_label, key=action_key):
            return True
    return False
