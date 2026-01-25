"""
WebSocket Integration for Streamlit Dashboards
Provides real-time event consumption for live dashboard updates.

Since Streamlit doesn't natively support WebSocket connections, this component
uses JavaScript injection for WebSocket communication and session state updates
for dashboard reactivity.
"""

import streamlit as st
import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

def inject_websocket_client(websocket_url: str = "ws://localhost:8000/ws", debug: bool = False):
    """
    Inject WebSocket client JavaScript into Streamlit app.

    Args:
        websocket_url: WebSocket server URL
        debug: Enable debug logging in browser console
    """

    websocket_js = f"""
    <script>
    class StreamlitWebSocketClient {{
        constructor() {{
            this.websocket = null;
            this.url = '{websocket_url}';
            this.debug = {str(debug).lower()};
            this.reconnectInterval = 5000; // 5 seconds
            this.maxReconnectAttempts = 10;
            this.reconnectAttempts = 0;
            this.isConnected = false;
            this.events = [];
            this.subscriptions = new Set();

            this.connect();

            // Store in window for access from Streamlit
            window.streamlitWebSocket = this;
        }}

        connect() {{
            try {{
                this.websocket = new WebSocket(this.url);

                this.websocket.onopen = (event) => {{
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    if (this.debug) console.log('[WebSocket] Connected to Jorge Real Estate AI');

                    // Authenticate with demo credentials
                    this.send({{
                        'type': 'auth',
                        'token': 'demo_token_jorge',
                        'user_id': 'jorge_dashboard',
                        'role': 'admin'
                    }});

                    this.updateStreamlitState('connection_status', 'connected');
                }};

                this.websocket.onmessage = (event) => {{
                    try {{
                        const data = JSON.parse(event.data);
                        this.handleEvent(data);
                    }} catch (e) {{
                        if (this.debug) console.error('[WebSocket] Parse error:', e);
                    }}
                }};

                this.websocket.onclose = (event) => {{
                    this.isConnected = false;
                    if (this.debug) console.log('[WebSocket] Connection closed');
                    this.updateStreamlitState('connection_status', 'disconnected');
                    this.scheduleReconnect();
                }};

                this.websocket.onerror = (error) => {{
                    if (this.debug) console.error('[WebSocket] Error:', error);
                    this.updateStreamlitState('connection_status', 'error');
                }};

            }} catch (error) {{
                if (this.debug) console.error('[WebSocket] Connection error:', error);
                this.scheduleReconnect();
            }}
        }}

        handleEvent(data) {{
            if (this.debug) console.log('[WebSocket] Event received:', data);

            // Store event with timestamp
            const eventWithTimestamp = {{
                ...data,
                client_timestamp: new Date().toISOString(),
                processed: false
            }};

            this.events.push(eventWithTimestamp);

            // Limit events in memory (keep last 100)
            if (this.events.length > 100) {{
                this.events = this.events.slice(-100);
            }}

            // Update Streamlit session state with new events
            this.updateStreamlitState('websocket_events', this.events);
            this.updateStreamlitState('last_event_time', Date.now());

            // Trigger specific event handlers
            this.triggerEventHandlers(data);
        }}

        triggerEventHandlers(event) {{
            // Handle specific event types for immediate UI updates
            switch(event.event_type) {{
                case 'jorge_qualification_progress':
                    this.updateStreamlitState('seller_qualification_update', event);
                    break;
                case 'buyer_qualification_complete':
                    this.updateStreamlitState('buyer_qualification_update', event);
                    break;
                case 'bot_status_update':
                    this.updateStreamlitState('bot_status_update', event);
                    break;
                case 'property_alert':
                    this.updateStreamlitState('property_alert_update', event);
                    break;
                case 'sms_compliance':
                    this.updateStreamlitState('sms_compliance_update', event);
                    break;
                case 'proactive_insight':
                case 'coaching_opportunity':
                    this.updateStreamlitState('claude_concierge_update', event);
                    break;
                default:
                    // Generic event update
                    this.updateStreamlitState('generic_event_update', event);
            }}
        }}

        updateStreamlitState(key, value) {{
            // Use Streamlit's session state update mechanism
            // This is a simplified approach - in production, you'd want a more robust bridge
            try {{
                if (window.streamlit && window.streamlit.setComponentValue) {{
                    window.streamlit.setComponentValue(key, value);
                }}

                // Also store in localStorage for persistence
                localStorage.setItem(`streamlit_websocket_${{key}}`, JSON.stringify(value));

            }} catch (e) {{
                if (this.debug) console.error('[WebSocket] State update error:', e);
            }}
        }}

        send(message) {{
            if (this.isConnected && this.websocket.readyState === WebSocket.OPEN) {{
                this.websocket.send(JSON.stringify(message));
                if (this.debug) console.log('[WebSocket] Message sent:', message);
            }}
        }}

        subscribe(eventTypes) {{
            if (Array.isArray(eventTypes)) {{
                eventTypes.forEach(eventType => this.subscriptions.add(eventType));
            }} else {{
                this.subscriptions.add(eventTypes);
            }}

            // Send subscription update to server
            this.send({{
                'type': 'subscribe',
                'event_types': Array.from(this.subscriptions)
            }});
        }}

        scheduleReconnect() {{
            if (this.reconnectAttempts < this.maxReconnectAttempts) {{
                setTimeout(() => {{
                    this.reconnectAttempts++;
                    if (this.debug) console.log(`[WebSocket] Reconnecting (attempt ${{this.reconnectAttempts}})...`);
                    this.connect();
                }}, this.reconnectInterval);
            }} else {{
                if (this.debug) console.log('[WebSocket] Max reconnection attempts reached');
            }}
        }}

        getEvents() {{
            return this.events.filter(event => !event.processed);
        }}

        markEventProcessed(eventId) {{
            const event = this.events.find(e => e.id === eventId);
            if (event) {{
                event.processed = true;
            }}
        }}

        getConnectionStatus() {{
            return {{
                isConnected: this.isConnected,
                reconnectAttempts: this.reconnectAttempts,
                eventsCount: this.events.length
            }};
        }}
    }}

    // Initialize WebSocket client if not already present
    if (!window.streamlitWebSocket) {{
        new StreamlitWebSocketClient();
    }}

    // Auto-subscribe to Jorge bot events
    setTimeout(() => {{
        if (window.streamlitWebSocket) {{
            window.streamlitWebSocket.subscribe([
                'jorge_qualification_progress',
                'buyer_qualification_complete',
                'bot_status_update',
                'property_alert',
                'sms_compliance',
                'proactive_insight',
                'coaching_opportunity',
                'lead_bot_sequence_update',
                'conversation_event'
            ]);
        }}
    }}, 1000);

    </script>
    """

    st.markdown(websocket_js, unsafe_allow_html=True)

def initialize_websocket_state():
    """Initialize WebSocket-related session state variables."""

    # Connection state
    if 'ws_connection_status' not in st.session_state:
        st.session_state.ws_connection_status = 'initializing'

    # Event storage
    if 'ws_events' not in st.session_state:
        st.session_state.ws_events = []

    # Last event time for triggering reloads
    if 'ws_last_event_time' not in st.session_state:
        st.session_state.ws_last_event_time = 0

    # Event-specific states
    if 'ws_seller_qualification_events' not in st.session_state:
        st.session_state.ws_seller_qualification_events = []

    if 'ws_buyer_qualification_events' not in st.session_state:
        st.session_state.ws_buyer_qualification_events = []

    if 'ws_bot_status_events' not in st.session_state:
        st.session_state.ws_bot_status_events = []

    if 'ws_property_alert_events' not in st.session_state:
        st.session_state.ws_property_alert_events = []

    if 'ws_claude_events' not in st.session_state:
        st.session_state.ws_claude_events = []

def render_websocket_status_indicator():
    """Render WebSocket connection status indicator."""

    status = st.session_state.get('ws_connection_status', 'disconnected')
    events_count = len(st.session_state.get('ws_events', []))

    status_colors = {
        'connected': '🟢',
        'connecting': '🟡',
        'disconnected': '🔴',
        'error': '🔴',
        'initializing': '🟡'
    }

    status_icon = status_colors.get(status, '⚪')

    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:
            st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; background: rgba(0,0,0,0.1); border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <span style="font-size: 0.8rem; color: #8B949E;">REAL-TIME STATUS</span><br>
                    <span style="font-size: 1rem;">{status_icon} {status.title()}</span>
                    {f'<br><span style="font-size: 0.7rem; color: #8B949E;">{events_count} events</span>' if events_count > 0 else ''}
                </div>
            """, unsafe_allow_html=True)

def get_latest_events(event_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get latest WebSocket events from session state.

    Args:
        event_type: Filter by event type (optional)
        limit: Maximum number of events to return

    Returns:
        List of events
    """

    # Try to get events from localStorage via JavaScript (fallback)
    # In a production app, you'd want a more robust state bridge
    all_events = st.session_state.get('ws_events', [])

    if event_type:
        filtered_events = [e for e in all_events if e.get('event_type') == event_type]
    else:
        filtered_events = all_events

    # Sort by timestamp (newest first)
    sorted_events = sorted(
        filtered_events,
        key=lambda x: x.get('timestamp', x.get('client_timestamp', '')),
        reverse=True
    )

    return sorted_events[:limit]

def check_for_new_events() -> bool:
    """
    Check if there are new WebSocket events since last check.

    Returns:
        True if new events are available
    """
    current_time = st.session_state.get('ws_last_event_time', 0)
    last_check = st.session_state.get('ws_last_check_time', 0)

    if current_time > last_check:
        st.session_state.ws_last_check_time = current_time
        return True

    return False

def auto_refresh_on_events(refresh_interval: int = 2000):
    """
    Auto-refresh the Streamlit app when new events are received.

    Args:
        refresh_interval: Minimum time between refreshes in milliseconds
    """

    auto_refresh_js = f"""
    <script>
    // Auto-refresh mechanism for real-time updates
    if (!window.streamlitAutoRefresh) {{
        window.streamlitAutoRefresh = {{
            lastRefresh: 0,
            interval: {refresh_interval},

            checkForUpdates: function() {{
                const now = Date.now();
                const lastEventTime = localStorage.getItem('streamlit_websocket_last_event_time');

                if (lastEventTime && now - this.lastRefresh > this.interval) {{
                    const lastEventTimeNum = parseInt(lastEventTime);
                    if (lastEventTimeNum > this.lastRefresh) {{
                        this.lastRefresh = now;
                        // Trigger Streamlit rerun
                        if (window.parent && window.parent.postMessage) {{
                            window.parent.postMessage({{
                                type: 'streamlit:setComponentValue',
                                key: 'auto_refresh_trigger',
                                value: now
                            }}, '*');
                        }}
                    }}
                }}
            }}
        }};

        // Check for updates every second
        setInterval(() => {{
            window.streamlitAutoRefresh.checkForUpdates();
        }}, 1000);
    }}
    </script>
    """

    st.markdown(auto_refresh_js, unsafe_allow_html=True)

def render_event_debug_panel():
    """Render debug panel showing recent WebSocket events."""

    if st.sidebar.checkbox("🔍 Debug: Show WebSocket Events", value=False):
        st.sidebar.markdown("### Recent Events")

        events = get_latest_events(limit=5)

        if events:
            for i, event in enumerate(events):
                event_time = event.get('timestamp', event.get('client_timestamp', 'Unknown'))
                event_type = event.get('event_type', 'unknown')

                with st.sidebar.expander(f"{event_type} - {event_time}"[:30]):
                    st.json(event)
        else:
            st.sidebar.info("No events received yet")

def setup_websocket_dashboard():
    """
    Setup WebSocket integration for the entire dashboard.
    Call this at the top of your main dashboard function.
    """

    # Initialize session state
    initialize_websocket_state()

    # Inject WebSocket client
    inject_websocket_client(debug=True)

    # Setup auto-refresh
    auto_refresh_on_events()

    # Render status indicator in sidebar
    with st.sidebar:
        st.markdown("---")
        render_websocket_status_indicator()

    # Debug panel
    render_event_debug_panel()

# Event-specific helper functions for dashboard components

def get_seller_qualification_updates():
    """Get recent seller qualification events."""
    return get_latest_events('jorge_qualification_progress', limit=5)

def get_buyer_qualification_updates():
    """Get recent buyer qualification events."""
    return get_latest_events('buyer_qualification_complete', limit=5)

def get_bot_status_updates():
    """Get recent bot status events."""
    return get_latest_events('bot_status_update', limit=10)

def get_property_alerts():
    """Get recent property alert events."""
    return get_latest_events('property_alert', limit=5)

def get_claude_concierge_updates():
    """Get recent Claude concierge events."""
    coaching_events = get_latest_events('coaching_opportunity', limit=3)
    insight_events = get_latest_events('proactive_insight', limit=3)

    # Combine and sort by timestamp
    all_events = coaching_events + insight_events
    return sorted(all_events, key=lambda x: x.get('timestamp', ''), reverse=True)[:5]

def get_sms_compliance_updates():
    """Get recent SMS compliance events."""
    return get_latest_events('sms_compliance', limit=5)

# Usage example in dashboard components:
"""
# At the top of your dashboard component:
from .websocket_integration import setup_websocket_dashboard, get_seller_qualification_updates

def render_my_dashboard():
    # Setup WebSocket integration
    setup_websocket_dashboard()

    # Check for seller qualification updates
    qualification_updates = get_seller_qualification_updates()
    if qualification_updates:
        for update in qualification_updates:
            st.success(f"New qualification: {update.get('contact_id')} - {update.get('seller_temperature')}")

    # Your regular dashboard content...
"""