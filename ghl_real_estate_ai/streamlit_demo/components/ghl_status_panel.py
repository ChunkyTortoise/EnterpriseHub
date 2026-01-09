"""
GHL Connection Status Panel - Shows real-time GoHighLevel integration status
"""
import streamlit as st
from datetime import datetime
from typing import Dict, Any


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
        st.success("✅ **Connected to GoHighLevel**")
        
        # Status grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>📊</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Location ID</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{}</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #10b981; font-weight: 600;'>
                    ✓ API Key Valid
                </div>
            </div>
            """.format(connection_status["location_id"]), unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>👥</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Total Contacts</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{:,}</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #6b7280;'>
                    Last Sync: {} ago
                </div>
            </div>
            """.format(connection_status["total_contacts"], connection_status["last_sync"]), unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>🔔</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Webhooks Active</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{} / 3</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #10b981; font-weight: 600;'>
                    ✓ All Endpoints Configured
                </div>
            </div>
            """.format(connection_status["webhooks_active"]), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>💬</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Active Conversations</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{}</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #f59e0b; font-weight: 600;'>
                    {} unread messages
                </div>
            </div>
            """.format(connection_status["active_conversations"], connection_status["unread_messages"]), unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 1rem;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>🎤</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Voice AI (VAPI)</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #10b981;'>Connected</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #6b7280;'>
                    {} calls today
                </div>
            </div>
            """.format(connection_status["calls_today"]), unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb;'>
                <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;'>
                    <div style='font-size: 2rem;'>📈</div>
                    <div>
                        <div style='font-size: 0.875rem; color: #6b7280;'>Today's Activity</div>
                        <div style='font-size: 1.1rem; font-weight: 700; color: #1e293b;'>{} interactions</div>
                    </div>
                </div>
                <div style='font-size: 0.75rem; color: #6b7280;'>
                    {} SMS • {} Calls • {} Emails
                </div>
            </div>
            """.format(
                connection_status["total_interactions"],
                connection_status["sms_today"],
                connection_status["calls_today"],
                connection_status["emails_today"]
            ), unsafe_allow_html=True)
        
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
        "vapi_connected": True
    }


def render_ghl_quick_stats():
    """Render a compact version for sidebar or header"""
    
    status = check_ghl_connection()
    
    if status["connected"]:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;'>
                <div style='font-size: 1.25rem;'>✅</div>
                <div style='font-weight: 700; font-size: 0.9rem;'>GHL Connected</div>
            </div>
            <div style='font-size: 0.75rem; opacity: 0.9;'>
                {status["total_contacts"]} contacts • {status["active_conversations"]} active conversations
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                    padding: 1rem; border-radius: 8px; color: white; margin-bottom: 1rem;'>
            <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;'>
                <div style='font-size: 1.25rem;'>❌</div>
                <div style='font-weight: 700; font-size: 0.9rem;'>GHL Disconnected</div>
            </div>
            <div style='font-size: 0.75rem; opacity: 0.9;'>
                Configure API credentials in settings
            </div>
        </div>
        """, unsafe_allow_html=True)
