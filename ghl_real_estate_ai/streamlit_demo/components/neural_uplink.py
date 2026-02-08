import streamlit as st


def render_neural_uplink():
    """
    Renders the 'Neural Uplink' high-fidelity activity feed.
    SaaS-Noir / Obsidian Command styling for sidebar integration.
    """
    st.markdown(
        """
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 0.75rem; color: #6366F1; font-weight: 800; text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: 1.25rem; display: flex; align-items: center; gap: 10px;">
            <span class="status-pulse" style="width: 8px; height: 8px; background-color: #6366F1; border-radius: 50%; display: inline-block;"></span>
            NEURAL UPLINK // LIVE
        </div>
    """,
        unsafe_allow_html=True,
    )

    activities = [
        {
            "icon": "🛡️",
            "color": "#EF4444",
            "text": "<b>SecuritySentry</b>: PII Scan Cleared (99.8%)",
            "time": "Just now",
        },
        {
            "icon": "🧠",
            "color": "#6366F1",
            "text": "<b>MemorySynthesizer</b>: Dossier created for <i>Sarah Chen</i>",
            "time": "1m ago",
        },
        {
            "icon": "🕵️",
            "color": "#10B981",
            "text": "<b>MarketplaceGovernor</b>: New skill validated successfully",
            "time": "2m ago",
        },
        {
            "icon": "📈",
            "color": "#3B82F6",
            "text": "<b>MarketHeatmap</b>: Synthesizing trends for <i>Austin</i>",
            "time": "5m ago",
        },
        {
            "icon": "⚡",
            "color": "#F59E0B",
            "text": "<b>SwarmOrchestrator</b>: Scaling up (Complexity: 0.82)",
            "time": "12m ago",
        },
        {"icon": "📝", "color": "#10B981", "text": "Creating contract for <b>John Doe</b>", "time": "15m ago"},
        {"icon": "🔔", "color": "#3B82F6", "text": "New lead: <b>Sarah Smith</b> (Downtown)", "time": "22m ago"},
    ]

    for act in activities:
        st.markdown(
            f"""
            <div style="
                background: rgba(22, 27, 34, 0.6);
                padding: 0.85rem;
                border-radius: 12px;
                margin-bottom: 0.75rem;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-left: 3px solid {act["color"]};
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
            ">
                <div style="display: flex; align-items: flex-start; gap: 0.75rem;">
                    <div style="font-size: 1.25rem; line-height: 1;">{act["icon"]}</div>
                    <div style="flex: 1;">
                        <div style="font-size: 0.85rem; line-height: 1.4; color: #E6EDF3; font-family: 'Inter', sans-serif;">{act["text"]}</div>
                        <div style="font-size: 0.7rem; color: #8B949E; margin-top: 6px; display: flex; align-items: center; gap: 6px; font-family: 'Space Grotesk', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">
                            <span style="width: 6px; height: 6px; background-color: {act["color"]}; border-radius: 50%; display: inline-block; box-shadow: 0 0 8px {act["color"]};"></span>
                            {act["time"]}
                        </div>
                    </div>
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )
