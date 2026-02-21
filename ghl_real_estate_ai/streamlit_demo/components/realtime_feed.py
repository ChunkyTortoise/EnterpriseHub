"""
Real-Time Activity Feed Component for Jorge's Dashboard.

Displays live updates of lead activities, conversation progression,
commission changes, and system events. Connects to WebSocket service
for instant updates without page refreshes.

Features:
- Live activity stream with real-time updates
- Event type filtering and prioritization
- Role-based content filtering
- Auto-scrolling and pagination
- Interactive event details
- Performance-optimized rendering
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import websockets

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RealTimeActivityFeed:
    """
    Real-time activity feed component for Streamlit dashboard.

    Manages WebSocket connection and displays live activity updates
    with filtering, prioritization, and interactive features.
    """

    def __init__(self, max_activities: int = 100):
        self.max_activities = max_activities
        self.websocket_url = self._get_websocket_url()

        # Initialize session state for activities
        if "rt_activities" not in st.session_state:
            st.session_state.rt_activities = []

        if "rt_connection_status" not in st.session_state:
            st.session_state.rt_connection_status = "disconnected"

        if "rt_filters" not in st.session_state:
            st.session_state.rt_filters = {
                "event_types": ["all"],
                "priority": ["all"],
                "auto_scroll": True,
                "sound_alerts": False,
            }

    def _get_websocket_url(self) -> str:
        """Get WebSocket URL based on current environment."""
        # Check for custom WebSocket URL in environment or config
        import os

        base_url = os.getenv("WEBSOCKET_URL", "ws://localhost:8000")
        return f"{base_url}/api/websocket/connect"

    def render_activity_feed(self, user_token: Optional[str] = None):
        """
        Render the real-time activity feed component.

        Args:
            user_token: JWT authentication token for WebSocket connection
        """
        # Header with connection status
        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.subheader("🔴 Live Activity Feed")

        with col2:
            status_color = {"connected": "🟢", "connecting": "🟡", "disconnected": "🔴"}
            st.write(
                f"{status_color.get(st.session_state.rt_connection_status, '🔴')} {st.session_state.rt_connection_status.title()}"
            )

        with col3:
            if st.button("🔄 Refresh", key="refresh_feed"):
                self._refresh_connection(user_token)

        # Filters section
        with st.expander("🔧 Feed Settings", expanded=False):
            self._render_filters()

        # Connection management
        if user_token and st.session_state.rt_connection_status == "disconnected":
            if st.button("🔌 Connect to Live Updates", key="connect_ws"):
                self._start_websocket_connection(user_token)

        # Activity feed display
        self._render_activity_list()

        # Auto-refresh for connection status
        if st.session_state.rt_connection_status == "connecting":
            time.sleep(1)
            st.rerun()

    def _render_filters(self):
        """Render activity filter controls."""
        col1, col2 = st.columns(2)

        with col1:
            event_types = [
                "all",
                "lead_update",
                "conversation_update",
                "commission_update",
                "system_alert",
                "performance_update",
            ]
            st.session_state.rt_filters["event_types"] = st.multiselect(
                "Event Types", event_types, default=st.session_state.rt_filters["event_types"], key="event_type_filter"
            )

        with col2:
            priority_levels = ["all", "critical", "high", "normal", "low"]
            st.session_state.rt_filters["priority"] = st.multiselect(
                "Priority Levels",
                priority_levels,
                default=st.session_state.rt_filters["priority"],
                key="priority_filter",
            )

        col3, col4 = st.columns(2)

        with col3:
            st.session_state.rt_filters["auto_scroll"] = st.checkbox(
                "Auto-scroll to new activities",
                value=st.session_state.rt_filters["auto_scroll"],
                key="auto_scroll_check",
            )

        with col4:
            st.session_state.rt_filters["sound_alerts"] = st.checkbox(
                "Sound alerts for high priority",
                value=st.session_state.rt_filters["sound_alerts"],
                key="sound_alerts_check",
            )

    def _render_activity_list(self):
        """Render the list of activities with filtering."""
        activities = st.session_state.rt_activities

        if not activities:
            st.info("🔄 Waiting for live activities... Connect to see real-time updates.")
            return

        # Apply filters
        filtered_activities = self._apply_filters(activities)

        # Pagination
        activities_per_page = 20
        total_pages = max(
            1,
            len(filtered_activities) // activities_per_page
            + (1 if len(filtered_activities) % activities_per_page > 0 else 0),
        )

        if total_pages > 1:
            page = st.selectbox("Page", range(1, total_pages + 1), key="activity_page")
            start_idx = (page - 1) * activities_per_page
            end_idx = start_idx + activities_per_page
            displayed_activities = filtered_activities[start_idx:end_idx]
        else:
            displayed_activities = filtered_activities

        # Display activities
        st.markdown(f"**Showing {len(displayed_activities)} of {len(filtered_activities)} activities**")

        for i, activity in enumerate(displayed_activities):
            self._render_activity_item(activity, i)

    def _apply_filters(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply user filters to activity list."""
        filtered = activities

        # Event type filter
        if "all" not in st.session_state.rt_filters["event_types"]:
            filtered = [a for a in filtered if a.get("event_type") in st.session_state.rt_filters["event_types"]]

        # Priority filter
        if "all" not in st.session_state.rt_filters["priority"]:
            filtered = [a for a in filtered if a.get("priority", "normal") in st.session_state.rt_filters["priority"]]

        return filtered

    def _render_activity_item(self, activity: Dict[str, Any], index: int):
        """Render individual activity item."""
        event_type = activity.get("event_type", "unknown")
        priority = activity.get("priority", "normal")
        timestamp = activity.get("timestamp", "")
        data = activity.get("data", {})

        # Priority styling
        priority_colors = {"critical": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪"}

        # Event type icons
        type_icons = {
            "lead_update": "👤",
            "conversation_update": "💬",
            "commission_update": "💰",
            "system_alert": "⚠️",
            "performance_update": "📊",
            "user_activity": "🔐",
            "dashboard_refresh": "🔄",
        }

        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            time_str = dt.strftime("%H:%M:%S")
        except Exception as e:
            import logging

            logging.getLogger(__name__).debug(f"Timestamp parsing error: {e}")
            time_str = timestamp

        # Activity container
        with st.container():
            col1, col2 = st.columns([1, 6])

            with col1:
                st.write(f"{priority_colors.get(priority, '⚪')} {type_icons.get(event_type, '📄')}")
                st.caption(time_str)

            with col2:
                # Activity title and summary
                summary = data.get("summary", f"{event_type.replace('_', ' ').title()}")
                st.markdown(f"**{summary}**")

                # Activity details based on type
                self._render_activity_details(event_type, data)

                # Expandable raw data
                with st.expander("📋 Raw Event Data", expanded=False):
                    st.json(activity)

            st.divider()

    def _render_activity_details(self, event_type: str, data: Dict[str, Any]):
        """Render type-specific activity details."""
        if event_type == "lead_update":
            action = data.get("action", "updated")
            lead_id = data.get("lead_id", "Unknown")
            lead_data = data.get("lead_data", {})

            st.caption(f"**Lead {action.title()}:** {lead_id}")
            if "name" in lead_data:
                st.caption(f"👤 Name: {lead_data['name']}")
            if "phone" in lead_data:
                st.caption(f"📞 Phone: {lead_data['phone']}")
            if "email" in lead_data:
                st.caption(f"📧 Email: {lead_data['email']}")

        elif event_type == "conversation_update":
            lead_id = data.get("lead_id", "Unknown")
            stage = data.get("stage", "Unknown")
            stage_progression = data.get("stage_progression", {})

            st.caption(f"**Lead:** {lead_id} → **Stage:** {stage}")
            if "progress" in stage_progression:
                progress = stage_progression["progress"]
                st.progress(progress / 100)
                st.caption(f"Progress: {progress}% • {stage_progression.get('description', '')}")

        elif event_type == "commission_update":
            deal_id = data.get("deal_id", "Unknown")
            amount = data.get("formatted_amount", "Unknown")
            status = data.get("pipeline_status", "Unknown")

            st.caption(f"**Deal:** {deal_id} • **Amount:** {amount}")
            st.caption(f"**Status:** {status.title()}")

        elif event_type == "system_alert":
            alert_type = data.get("alert_type", "Unknown")
            message = data.get("message", "No details available")
            severity = data.get("severity", "info")

            st.caption(f"**Type:** {alert_type} • **Severity:** {severity}")
            if severity in ["error", "critical"]:
                st.error(message)
            elif severity == "warning":
                st.warning(message)
            else:
                st.info(message)

        elif event_type == "performance_update":
            metric_name = data.get("metric_name", "Unknown")
            formatted_value = data.get("formatted_value", "Unknown")
            trend = data.get("trend", "neutral")

            trend_icons = {"up": "📈", "down": "📉", "stable": "➡️", "neutral": "➡️"}
            st.caption(f"**{metric_name}:** {formatted_value} {trend_icons.get(trend, '➡️')}")

    def _start_websocket_connection(self, token: str):
        """Start WebSocket connection in background thread."""
        st.session_state.rt_connection_status = "connecting"

        # Start WebSocket connection in background
        threading.Thread(target=self._websocket_worker, args=(token,), daemon=True).start()

        st.rerun()

    def _websocket_worker(self, token: str):
        """WebSocket worker thread for receiving real-time events."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Run WebSocket connection
            loop.run_until_complete(self._websocket_handler(token))

        except Exception as e:
            logger.error(f"WebSocket worker error: {e}")
            st.session_state.rt_connection_status = "disconnected"
        finally:
            loop.close()

    async def _websocket_handler(self, token: str):
        """Handle WebSocket connection and message processing."""
        uri = f"{self.websocket_url}?token={token}"

        try:
            async with websockets.connect(uri) as websocket:
                st.session_state.rt_connection_status = "connected"
                logger.info("WebSocket connected for real-time feed")

                # Send heartbeat every 30 seconds
                heartbeat_task = asyncio.create_task(self._heartbeat_sender(websocket))

                try:
                    async for message in websocket:
                        data = json.loads(message)
                        await self._handle_websocket_message(data)

                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed")
                finally:
                    heartbeat_task.cancel()

        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            import logging

            logging.getLogger(__name__).error(f"WebSocket connection error: {e}")
            st.session_state.rt_connection_status = "disconnected"

    async def _heartbeat_sender(self, websocket):
        """Send periodic heartbeat messages."""
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send(json.dumps({"type": "heartbeat"}))
        except asyncio.CancelledError:
            pass

    async def _handle_websocket_message(self, data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        message_type = data.get("type")

        if message_type == "real_time_event":
            event = data.get("event", {})
            await self._add_activity(event)

        elif message_type == "connection_established":
            logger.info("WebSocket connection established for activity feed")

        elif message_type == "heartbeat_ack":
            # Connection is healthy
            pass

    async def _add_activity(self, event: Dict[str, Any]):
        """Add new activity to the feed."""
        # Add to beginning of list (most recent first)
        activities = st.session_state.rt_activities
        activities.insert(0, event)

        # Trim list to max size
        if len(activities) > self.max_activities:
            st.session_state.rt_activities = activities[: self.max_activities]
        else:
            st.session_state.rt_activities = activities

        # Trigger sound alert for high priority events
        if event.get("priority") in ["critical", "high"] and st.session_state.rt_filters.get("sound_alerts", False):
            # In a real implementation, you might use JavaScript for sound
            logger.info(f"High priority alert: {event.get('data', {}).get('summary', 'Unknown')}")

    def _refresh_connection(self, token: Optional[str]):
        """Refresh WebSocket connection."""
        st.session_state.rt_connection_status = "disconnected"
        if token:
            self._start_websocket_connection(token)


def render_realtime_activity_feed(user_token: Optional[str] = None, max_activities: int = 100):
    """
    Convenience function to render real-time activity feed.

    Args:
        user_token: JWT authentication token for WebSocket connection
        max_activities: Maximum number of activities to keep in memory
    """
    feed = RealTimeActivityFeed(max_activities=max_activities)
    feed.render_activity_feed(user_token)


# Component for testing without authentication
def render_demo_activity_feed():
    """Render demo activity feed with sample data for testing."""
    st.subheader("🔴 Live Activity Feed (Demo)")

    # Sample activities for demonstration
    sample_activities = [
        {
            "event_type": "lead_update",
            "data": {
                "lead_id": "LEAD_001",
                "action": "created",
                "lead_data": {"name": "John Smith", "phone": "555-0123", "email": "john@example.com"},
                "summary": "New lead created: John Smith",
            },
            "timestamp": datetime.now().isoformat(),
            "priority": "high",
        },
        {
            "event_type": "conversation_update",
            "data": {
                "lead_id": "LEAD_002",
                "stage": "Q2",
                "stage_progression": {"progress": 50, "description": "Budgeting & Timeline"},
                "summary": "Conversation moved to Q2",
            },
            "timestamp": (datetime.now().replace(second=datetime.now().second - 30)).isoformat(),
            "priority": "normal",
        },
        {
            "event_type": "commission_update",
            "data": {
                "deal_id": "DEAL_001",
                "commission_amount": 15000,
                "formatted_amount": "$15,000.00",
                "pipeline_status": "confirmed",
                "summary": "Commission confirmed: $15,000.00",
            },
            "timestamp": (datetime.now().replace(minute=datetime.now().minute - 5)).isoformat(),
            "priority": "high",
        },
    ]

    st.info("📋 Demo mode - showing sample activities. Connect with real authentication for live updates.")

    for i, activity in enumerate(sample_activities):
        feed = RealTimeActivityFeed()
        feed._render_activity_item(activity, i)
