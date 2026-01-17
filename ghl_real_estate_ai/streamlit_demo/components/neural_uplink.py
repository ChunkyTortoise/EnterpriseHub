import streamlit as st

def render_neural_uplink():
    """
    Renders the 'Neural Uplink' high-fidelity activity feed.
    SaaS-Noir / Obsidian Command styling for sidebar integration.
    """
    st.markdown("""
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.75rem; color: #6366F1; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 10px;">
            <span class="status-pulse" style="width: 8px; height: 8px; background-color: #6366F1; border-radius: 50%; display: inline-block;"></span>
            NEURAL UPLINK // LIVE
        </div>
    """, unsafe_allow_html=True)

    activities = [
        {"icon": "📝", "color": "#10B981", "text": "Creating contract for <b>John Doe</b>", "time": "Just now"},
        {"icon": "🔔", "color": "#3B82F6", "text": "New lead: <b>Sarah Smith</b> (Downtown)", "time": "06:40 PM"},
        {"icon": "🤖", "color": "#8B5CF6", "text": "AI handled objection: <b>Mike Ross</b>", "time": "06:27 PM"},
        {"icon": "📅", "color": "#F59E0B", "text": "Tour scheduled: <b>123 Main St</b>", "time": "05:42 PM"},
        {"icon": "💬", "color": "#EC4899", "text": "SMS sent to <b>Emily Davis</b>", "time": "04:42 PM"},
        {"icon": "📞", "color": "#06B6D4", "text": "Call completed: <b>Robert Chen</b>", "time": "03:42 PM"}
    ]

    for act in activities:
        st.markdown(f"""
            <div style="
                background: rgba(22, 27, 34, 0.6);
                padding: 0.85rem;
                border-radius: 12px;
                margin-bottom: 0.75rem;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 3px solid {act['color']};
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            ">
                <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                    <div style="font-size: 1.25rem; line-height: 1;">{act['icon']}</div>
                    <div style="flex: 1;">
                        <div style="font-size: 0.85rem; line-height: 1.4; color: #E6EDF3; font-family: 'Inter', sans-serif;">{act['text']}</div>
                        <div style="font-size: 0.7rem; color: #8B949E; margin-top: 6px; display: flex; align-items: center; gap: 6px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                            <span style="width: 6px; height: 6px; background-color: {act['color']}; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px {act['color']};"></span>
                            {act['time']}
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
