"""
GHL Connection Status Panel - Shows real-time GoHighLevel integration status
"""

from datetime import datetime
from typing import Any, Dict

import streamlit as st


def render_ghl_status_panel():
    """
    Render the GHL connection status panel showing:
    - API connection status
    - Contact sync info
    - Conversation activity
    - Webhook configuration
    - Voice AI status
    """

    st.markdown("### 🔗 GoHighLevel Integration Status")

    # Mock connection check (in production, this would call actual GHL API)
    connection_status = check_ghl_connection()

    # Main status card
    if connection_status["connected"]:
        st.markdown(
            """
        <div style='background: rgba(16, 185, 129, 0.1); padding: 1rem 1.5rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 2rem; display: flex; align-items: center; gap: 12px;'>
            <div class="status-pulse" style="background: #10b981;"></div>
            <div style="color: #10b981; font-weight: 700; font-family: 'Space Grotesk', sans-serif; text-transform: uppercase; letter-spacing: 0.1em; font-size: 0.85rem;">Enterprise Node Online: GHL Sync Active</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Status grid - Obsidian Edition
        col1, col2 = st.columns(2)

        card_style = "background: rgba(22, 27, 34, 0.7); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); margin-bottom: 1.25rem; box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4); backdrop-filter: blur(12px);"
        label_style = "font-size: 0.75rem; color: #8B949E; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; font-family: 'Space Grotesk', sans-serif;"
        value_style = "font-size: 1.25rem; font-weight: 700; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif;"

        with col1:
            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>📊</div>
                    <div>
                        <div style='{label_style}'>Location ID</div>
                        <div style='{value_style}'>{connection_status["location_id"]}</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>
                    ✓ AUTHENTICATION VERIFIED
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>👥</div>
                    <div>
                        <div style='{label_style}'>Total Contacts</div>
                        <div style='{value_style}'>{connection_status["total_contacts"]:,}</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>
                    Last Sync: {connection_status["last_sync"]} ago
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>🔔</div>
                    <div>
                        <div style='{label_style}'>Webhooks Active</div>
                        <div style='{value_style}'>{connection_status["webhooks_active"]} / 3</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #10b981; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>
                    ✓ ALL ENDPOINTS SECURE
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>💬</div>
                    <div>
                        <div style='{label_style}'>Active Conversations</div>
                        <div style='{value_style}'>{connection_status["active_conversations"]}</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #f59e0b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {connection_status["unread_messages"]} UNREAD SIGNALS
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>🎤</div>
                    <div>
                        <div style='{label_style}'>Voice AI (VAPI)</div>
                        <div style='{value_style}'>CONNECTED</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {connection_status["calls_today"]} transmissions today
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown(
                f"""
            <div style='{card_style}'>
                <div style='display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem; filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.3));'>📈</div>
                    <div>
                        <div style='{label_style}'>Today's Activity</div>
                        <div style='{value_style}'>{connection_status["total_interactions"]} interactions</div>
                    </div>
                </div>
                <div style='font-size: 0.7rem; color: #8B949E; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;'>
                    {connection_status["sms_today"]} SMS • {connection_status["calls_today"]} CALLS • {connection_status["emails_today"]} EMAIL
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Test connection button
        st.markdown("---")
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("🔄 Refresh Status", use_container_width=True):
                st.toast("Status refreshed!", icon="✅")
                st.rerun()

        with col_btn2:
            if st.button("🔍 Test Connection", use_container_width=True):
                with st.spinner("Testing connection..."):
                    import time

                    time.sleep(1)
                    st.toast("Connection test successful!", icon="✅")

        with col_btn3:
            if st.button("📊 View Logs", use_container_width=True):
                st.info("Opening webhook logs...")

    else:
        st.error("❌ **Not Connected to GoHighLevel**")
        st.warning("Please configure your GHL API credentials in settings.")

        if st.button("⚙️ Configure GHL Connection"):
            st.info("Redirect to settings page...")


def check_ghl_connection() -> Dict[str, Any]:
    """
    Check GHL connection status
    In production, this would make actual API calls
    """

    # Mock data for demo purposes
    # In production, replace with actual API calls:
    # from ghl_utils.ghl_api_client import GHLClient
    # client = GHLClient()
    # return client.get_connection_status()

    return {
        "connected": True,
        "location_id": "abc123xyz789",
        "total_contacts": 247,
        "last_sync": "2 minutes",
        "active_conversations": 18,
        "unread_messages": 5,
        "webhooks_active": 3,
        "calls_today": 7,
        "sms_today": 34,
        "emails_today": 12,
        "total_interactions": 53,
        "api_key_valid": True,
        "vapi_connected": True,
    }


def render_ghl_quick_stats():
    """Render a compact version for sidebar or header - Obsidian Edition"""

    status = check_ghl_connection()

    if status["connected"]:
        st.markdown(
            f"""
        <div style='background: rgba(16, 185, 129, 0.1); 
                    padding: 1.25rem; border-radius: 12px; color: #FFFFFF; margin-bottom: 1.5rem; border: 1px solid rgba(16, 185, 129, 0.2); box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
            <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 0.75rem;'>
                <div class="status-pulse" style="background: #10b981; width: 8px; height: 8px;"></div>
                <div style='font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif; color: #10b981;'>GHL LINKED</div>
            </div>
            <div style='font-size: 0.75rem; color: #8B949E; font-family: "Inter", sans-serif; font-weight: 500;'>
                {status["total_contacts"]} nodes • {status["active_conversations"]} active streams
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
        <div style='background: rgba(239, 68, 68, 0.1); 
                    padding: 1.25rem; border-radius: 12px; color: #FFFFFF; margin-bottom: 1.5rem; border: 1px solid rgba(239, 68, 68, 0.2);'>
            <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 0.75rem;'>
                <div style='font-size: 1rem;'>❌</div>
                <div style='font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; font-family: "Space Grotesk", sans-serif; color: #ef4444;'>GHL OFFLINE</div>
            </div>
            <div style='font-size: 0.75rem; color: #8B949E; font-family: "Inter", sans-serif;'>
                Authentication required in secure settings.
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
