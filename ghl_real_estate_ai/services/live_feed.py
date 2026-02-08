"""
Live Feed Service - WebSocket Ready
Provides real-time activity updates for the sidebar feed
"""

import datetime
from typing import Any, Dict, List

import streamlit as st


class LiveFeedService:
    """
    Manages the live activity feed with support for real-time updates.
    Currently uses polling, ready for WebSocket upgrade.
    """

    def __init__(self):
        self.feed_items = []

    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent activities for the live feed.

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries with icon, text, time, color
        """
        # Initialize session state for feed if not exists
        if "feed_items" not in st.session_state:
            st.session_state.feed_items = self._get_mock_feed()

        return st.session_state.feed_items[:limit]

    def add_activity(self, activity_type: str, contact_name: str, details: str = ""):
        """
        Add a new activity to the feed (will be real-time with WebSocket).

        Args:
            activity_type: Type of activity (contract, lead, objection, tour)
            contact_name: Name of the contact
            details: Additional details about the activity
        """
        icon_map = {"contract": "📝", "lead": "🔔", "objection": "🤖", "tour": "📅", "message": "💬", "call": "📞"}

        color_map = {
            "contract": "#10B981",
            "lead": "#3B82F6",
            "objection": "#8B5CF6",
            "tour": "#F59E0B",
            "message": "#EC4899",
            "call": "#06B6D4",
        }

        new_item = {
            "icon": icon_map.get(activity_type, "📌"),
            "text": f"{details or activity_type.title()}: <b>{contact_name}</b>",
            "time": "Just now",
            "color": color_map.get(activity_type, "#6B7280"),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Add to session state
        if "feed_items" not in st.session_state:
            st.session_state.feed_items = []

        st.session_state.feed_items.insert(0, new_item)
        st.session_state.feed_items = st.session_state.feed_items[:50]  # Keep last 50

    def _get_mock_feed(self) -> List[Dict[str, Any]]:
        """Generate mock feed items with dynamic timestamps"""
        now = datetime.datetime.now()

        return [
            {
                "icon": "📝",
                "text": "Creating contract for <b>John Doe</b>",
                "time": "Just now",
                "color": "#10B981",
                "timestamp": now.isoformat(),
            },
            {
                "icon": "🔔",
                "text": "New lead: <b>Sarah Smith</b> (Downtown)",
                "time": f"{(now - datetime.timedelta(minutes=2)).strftime('%I:%M %p')}",
                "color": "#3B82F6",
                "timestamp": (now - datetime.timedelta(minutes=2)).isoformat(),
            },
            {
                "icon": "🤖",
                "text": "AI handled objection: <b>Mike Ross</b>",
                "time": f"{(now - datetime.timedelta(minutes=15)).strftime('%I:%M %p')}",
                "color": "#8B5CF6",
                "timestamp": (now - datetime.timedelta(minutes=15)).isoformat(),
            },
            {
                "icon": "📅",
                "text": "Tour scheduled: <b>123 Main St</b>",
                "time": f"{(now - datetime.timedelta(hours=1)).strftime('%I:%M %p')}",
                "color": "#F59E0B",
                "timestamp": (now - datetime.timedelta(hours=1)).isoformat(),
            },
            {
                "icon": "💬",
                "text": "SMS sent to <b>Emily Davis</b>",
                "time": f"{(now - datetime.timedelta(hours=2)).strftime('%I:%M %p')}",
                "color": "#EC4899",
                "timestamp": (now - datetime.timedelta(hours=2)).isoformat(),
            },
            {
                "icon": "📞",
                "text": "Call completed: <b>Robert Chen</b>",
                "time": f"{(now - datetime.timedelta(hours=3)).strftime('%I:%M %p')}",
                "color": "#06B6D4",
                "timestamp": (now - datetime.timedelta(hours=3)).isoformat(),
            },
        ]

    def get_feed_html(self, limit: int = 10) -> str:
        """
        Generate HTML for the live feed with enhanced styling.

        Args:
            limit: Maximum number of items to display

        Returns:
            HTML string for the feed
        """
        activities = self.get_recent_activities(limit)

        html_parts = []
        for item in activities:
            # Determine if "live" (less than 5 minutes ago)
            is_live = item["time"] == "Just now"
            live_class = "live-indicator" if is_live else ""

            html_parts.append(f"""
            <div style="
                background: white;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                border-left: 3px solid {item["color"]};
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                transition: all 0.2s ease;
            " onmouseover="this.style.boxShadow='0 4px 6px rgba(0, 0, 0, 0.1)'" onmouseout="this.style.boxShadow='0 1px 3px rgba(0, 0, 0, 0.05)'">
                <div style="display: flex; align-items: flex-start; gap: 0.5rem;">
                    <div style="font-size: 1.25rem; line-height: 1;">{item["icon"]}</div>
                    <div style="flex: 1;">
                        <div style="font-size: 0.85rem; line-height: 1.3; color: #1f2937;">{item["text"]}</div>
                        <div style="font-size: 0.7rem; color: #6b7280; margin-top: 4px; display: flex; align-items: center; gap: 4px;">
                            <span class="{live_class}" style="width: 6px; height: 6px; background-color: {item["color"]}; border-radius: 50%; display: inline-block;"></span>
                            {item["time"]}
                        </div>
                    </div>
                </div>
            </div>
            """)

        return "".join(html_parts)
