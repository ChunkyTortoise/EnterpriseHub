"""
Property Alert Dashboard Component for Jorge's Real Estate AI Platform.

Provides a specialized interface for viewing, managing, and interacting with
property alerts. Includes detailed property information, match reasoning,
alert preferences, and action capabilities.

Features:
- Real-time property alert feed with detailed property cards
- Alert preference management and customization
- Property match score visualization and reasoning
- Quick actions for bookmarking, inquiring, and dismissing alerts
- Alert analytics and performance tracking
"""

import streamlit as st
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import time
import json
from dataclasses import dataclass

from ghl_real_estate_ai.core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PropertyAlert:
    """Property alert data structure with enhanced details."""
    alert_id: str
    lead_id: str
    property_id: str
    match_score: float
    alert_type: str
    property_summary: Dict[str, Any]
    property_data: Dict[str, Any]
    match_reasoning: Dict[str, Any]
    timestamp: datetime
    dismissed: bool = False
    bookmarked: bool = False
    inquiry_sent: bool = False
    viewed: bool = False

class PropertyAlertDashboard:
    """
    Property Alert Dashboard Component.

    Specialized interface for property alerts with detailed property
    information, match analysis, and action capabilities.
    """

    def __init__(self):
        # Initialize session state for property alerts
        if "property_alerts" not in st.session_state:
            st.session_state.property_alerts = []

        if "property_alert_preferences" not in st.session_state:
            st.session_state.property_alert_preferences = {
                "min_match_score": 75,
                "max_alerts_per_day": 10,
                "alert_types_enabled": {
                    "new_match": True,
                    "price_drop": True,
                    "market_opportunity": True,
                    "back_on_market": True,
                    "price_increase": False,
                    "status_change": False
                },
                "notification_channels": {
                    "email": False,
                    "sms": False,
                    "in_app": True,
                    "websocket": True
                },
                "quiet_hours": {
                    "enabled": False,
                    "start": "22:00",
                    "end": "08:00"
                }
            }

        if "property_alert_filters" not in st.session_state:
            st.session_state.property_alert_filters = {
                "show_dismissed": False,
                "min_score": 0,
                "max_score": 100,
                "alert_types": [],
                "date_range": 7  # days
            }

    def render_dashboard(self):
        """Render the main property alert dashboard."""
        st.header("🏠 Property Alert Dashboard")

        # Dashboard metrics and summary
        self._render_alert_summary()

        # Alert controls and filters
        col1, col2 = st.columns([3, 1])

        with col1:
            # Main alert feed
            self._render_alert_feed()

        with col2:
            # Sidebar with preferences and filters
            self._render_alert_sidebar()

    def _render_alert_summary(self):
        """Render alert summary metrics."""
        alerts = st.session_state.property_alerts

        # Calculate metrics
        total_alerts = len(alerts)
        unread_alerts = len([a for a in alerts if not a.viewed])
        bookmarked_alerts = len([a for a in alerts if a.bookmarked])
        avg_match_score = sum([a.match_score for a in alerts]) / total_alerts if total_alerts > 0 else 0

        # Today's alerts
        today = datetime.now().date()
        today_alerts = len([a for a in alerts if a.timestamp.date() == today])

        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Alerts", total_alerts, delta=today_alerts if today_alerts > 0 else None)

        with col2:
            st.metric("Unread", unread_alerts)

        with col3:
            st.metric("Bookmarked", bookmarked_alerts)

        with col4:
            st.metric("Avg Match Score", f"{avg_match_score:.1f}%")

        with col5:
            high_score_alerts = len([a for a in alerts if a.match_score >= 90])
            st.metric("Excellent Matches", high_score_alerts)

    def _render_alert_feed(self):
        """Render the main property alert feed."""
        st.subheader("📬 Recent Property Alerts")

        # Filter alerts based on current filters
        filtered_alerts = self._apply_filters(st.session_state.property_alerts)

        if not filtered_alerts:
            st.info("🔍 No property alerts match your current filters. Adjust your preferences to see more alerts.")
            return

        # Sort alerts by timestamp (most recent first)
        filtered_alerts.sort(key=lambda a: a.timestamp, reverse=True)

        # Render alert cards
        for alert in filtered_alerts[:20]:  # Show last 20 alerts
            self._render_property_alert_card(alert)

    def _render_property_alert_card(self, alert: PropertyAlert):
        """Render individual property alert card with detailed information."""
        property_summary = alert.property_summary

        # Determine card styling based on match score and alert type
        if alert.match_score >= 90:
            card_color = "#f0fdf4"  # Green for excellent matches
            border_color = "#22c55e"
        elif alert.match_score >= 80:
            card_color = "#fffbeb"  # Amber for good matches
            border_color = "#f59e0b"
        else:
            card_color = "#f8fafc"  # Gray for standard matches
            border_color = "#64748b"

        # Opacity for dismissed/viewed alerts
        opacity = "0.7" if alert.dismissed else "1.0"

        # Alert type icons
        alert_type_icons = {
            "new_match": "🆕",
            "price_drop": "📉",
            "market_opportunity": "💎",
            "back_on_market": "🔄",
            "price_increase": "📈",
            "status_change": "📋"
        }

        alert_icon = alert_type_icons.get(alert.alert_type, "🏠")

        # Render property card
        with st.container():
            st.markdown(f"""
            <div style="
                background-color: {card_color};
                border: 2px solid {border_color};
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                opacity: {opacity};
                transition: transform 0.2s ease;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <div>
                        <h3 style="margin: 0; color: #1f2937; font-size: 1.25rem;">
                            {alert_icon} {property_summary.get('address', 'Unknown Property')}
                        </h3>
                        <p style="margin: 0.25rem 0 0 0; color: #6b7280; font-size: 0.9rem;">
                            {alert.alert_type.replace('_', ' ').title()} • {alert.timestamp.strftime('%H:%M')} • {alert.match_score:.0f}% match
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <div style="
                            background: {border_color};
                            color: white;
                            padding: 0.5rem 1rem;
                            border-radius: 20px;
                            font-weight: bold;
                            font-size: 0.9rem;
                        ">
                            {alert.match_score:.0f}%
                        </div>
                    </div>
                </div>

                <div style="margin-bottom: 1rem;">
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                        <div>
                            <strong>Price:</strong> {property_summary.get('formatted_price', 'Price on request')}<br>
                            <strong>Size:</strong> {property_summary.get('formatted_sqft', 'Size not listed')}
                        </div>
                        <div>
                            <strong>Bedrooms:</strong> {property_summary.get('bedrooms', 'N/A')}<br>
                            <strong>Bathrooms:</strong> {property_summary.get('bathrooms', 'N/A')}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Match reasoning (if available)
            if alert.match_reasoning:
                with st.expander("🧠 Why This Property Matches", expanded=False):
                    self._render_match_reasoning(alert.match_reasoning)

            # Action buttons
            col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

            with col2:
                if not alert.viewed:
                    if st.button("👀 Mark Viewed", key=f"view_{alert.alert_id}"):
                        alert.viewed = True
                        st.rerun()

            with col3:
                bookmark_label = "⭐ Bookmarked" if alert.bookmarked else "⭐ Bookmark"
                if st.button(bookmark_label, key=f"bookmark_{alert.alert_id}"):
                    alert.bookmarked = not alert.bookmarked
                    st.rerun()

            with col4:
                if not alert.inquiry_sent:
                    if st.button("📧 Inquire", key=f"inquire_{alert.alert_id}"):
                        alert.inquiry_sent = True
                        st.success("Inquiry sent to listing agent!")
                        st.rerun()
                else:
                    st.success("✓ Inquiry sent")

            with col5:
                if not alert.dismissed:
                    if st.button("🗑️ Dismiss", key=f"dismiss_{alert.alert_id}"):
                        alert.dismissed = True
                        st.rerun()

    def _render_match_reasoning(self, match_reasoning: Dict[str, Any]):
        """Render property match reasoning details."""
        if not match_reasoning:
            st.info("No detailed match reasoning available.")
            return

        # Price match analysis
        if "price_analysis" in match_reasoning:
            price_data = match_reasoning["price_analysis"]
            st.write("**💰 Price Analysis:**")
            st.write(f"• Within budget: {'✅' if price_data.get('within_budget', False) else '❌'}")
            st.write(f"• Market value: {price_data.get('market_position', 'Unknown')}")

        # Location match analysis
        if "location_analysis" in match_reasoning:
            location_data = match_reasoning["location_analysis"]
            st.write("**📍 Location Analysis:**")
            st.write(f"• Preferred area: {'✅' if location_data.get('in_preferred_area', False) else '❌'}")
            st.write(f"• Commute time: {location_data.get('commute_minutes', 'Unknown')} minutes")

        # Feature match analysis
        if "feature_analysis" in match_reasoning:
            feature_data = match_reasoning["feature_analysis"]
            st.write("**🏠 Feature Analysis:**")
            matched_features = feature_data.get("matched_features", [])
            missing_features = feature_data.get("missing_features", [])

            if matched_features:
                st.write(f"• ✅ Has: {', '.join(matched_features)}")
            if missing_features:
                st.write(f"• ❌ Missing: {', '.join(missing_features)}")

    def _render_alert_sidebar(self):
        """Render alert preferences and filters sidebar."""
        st.subheader("⚙️ Preferences")

        # Alert preferences
        with st.expander("🔔 Alert Settings", expanded=True):
            prefs = st.session_state.property_alert_preferences

            prefs["min_match_score"] = st.slider(
                "Minimum Match Score",
                0, 100, prefs["min_match_score"],
                help="Only show alerts with match scores above this threshold"
            )

            prefs["max_alerts_per_day"] = st.slider(
                "Max Alerts Per Day",
                1, 50, prefs["max_alerts_per_day"],
                help="Daily limit to prevent alert fatigue"
            )

            st.write("**Alert Types:**")
            for alert_type, enabled in prefs["alert_types_enabled"].items():
                prefs["alert_types_enabled"][alert_type] = st.checkbox(
                    alert_type.replace("_", " ").title(),
                    value=enabled,
                    key=f"alert_type_{alert_type}"
                )

        # Filters
        with st.expander("🔍 Filters", expanded=False):
            filters = st.session_state.property_alert_filters

            filters["show_dismissed"] = st.checkbox(
                "Show dismissed alerts",
                value=filters["show_dismissed"]
            )

            # Score range filter
            score_range = st.slider(
                "Match Score Range",
                0, 100,
                (filters["min_score"], filters["max_score"]),
                help="Filter alerts by match score range"
            )
            filters["min_score"], filters["max_score"] = score_range

            # Date range filter
            filters["date_range"] = st.selectbox(
                "Time Period",
                [1, 3, 7, 14, 30],
                index=2,  # Default to 7 days
                format_func=lambda x: f"Last {x} day{'s' if x > 1 else ''}"
            )

    def _apply_filters(self, alerts: List[PropertyAlert]) -> List[PropertyAlert]:
        """Apply current filters to the alert list."""
        filters = st.session_state.property_alert_filters
        prefs = st.session_state.property_alert_preferences

        filtered_alerts = alerts.copy()

        # Filter by dismissed status
        if not filters["show_dismissed"]:
            filtered_alerts = [a for a in filtered_alerts if not a.dismissed]

        # Filter by match score range
        filtered_alerts = [
            a for a in filtered_alerts
            if filters["min_score"] <= a.match_score <= filters["max_score"]
        ]

        # Filter by enabled alert types
        enabled_types = [
            alert_type for alert_type, enabled
            in prefs["alert_types_enabled"].items()
            if enabled
        ]
        filtered_alerts = [
            a for a in filtered_alerts
            if a.alert_type in enabled_types
        ]

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=filters["date_range"])
        filtered_alerts = [
            a for a in filtered_alerts
            if a.timestamp >= cutoff_date
        ]

        return filtered_alerts

    def add_property_alert_from_event(self, event_data: Dict[str, Any]):
        """
        Add property alert from WebSocket event data.

        Args:
            event_data: WebSocket event data for property alert
        """
        data = event_data.get("data", {})

        alert = PropertyAlert(
            alert_id=data.get("alert_id", f"alert_{int(time.time())}"),
            lead_id=data.get("lead_id", "unknown"),
            property_id=data.get("property_id", "unknown"),
            match_score=data.get("match_score", 0),
            alert_type=data.get("alert_type", "new_match"),
            property_summary=data.get("property_summary", {}),
            property_data=data.get("property_data", {}),
            match_reasoning=data.get("match_reasoning", {}),
            timestamp=datetime.now(timezone.utc)
        )

        # Check if alert meets minimum score threshold
        min_score = st.session_state.property_alert_preferences["min_match_score"]
        if alert.match_score >= min_score:
            # Add to beginning of list (most recent first)
            st.session_state.property_alerts.insert(0, alert)

            # Trim list to reasonable size (keep last 100 alerts)
            if len(st.session_state.property_alerts) > 100:
                st.session_state.property_alerts = st.session_state.property_alerts[:100]

            logger.info(f"Added property alert: {alert.alert_type} for property {alert.property_id} ({alert.match_score}% match)")

    def get_alert_analytics(self) -> Dict[str, Any]:
        """Get property alert analytics and statistics."""
        alerts = st.session_state.property_alerts

        if not alerts:
            return {"total": 0}

        # Calculate analytics
        total_alerts = len(alerts)
        avg_match_score = sum([a.match_score for a in alerts]) / total_alerts

        # Alerts by type
        by_type = {}
        for alert in alerts:
            alert_type = alert.alert_type
            by_type[alert_type] = by_type.get(alert_type, 0) + 1

        # Alerts by score range
        by_score = {
            "excellent": len([a for a in alerts if a.match_score >= 90]),
            "good": len([a for a in alerts if 80 <= a.match_score < 90]),
            "fair": len([a for a in alerts if 70 <= a.match_score < 80]),
            "poor": len([a for a in alerts if a.match_score < 70])
        }

        # Engagement metrics
        viewed_count = len([a for a in alerts if a.viewed])
        bookmarked_count = len([a for a in alerts if a.bookmarked])
        inquiry_count = len([a for a in alerts if a.inquiry_sent])
        dismissed_count = len([a for a in alerts if a.dismissed])

        return {
            "total": total_alerts,
            "avg_match_score": round(avg_match_score, 2),
            "by_type": by_type,
            "by_score": by_score,
            "engagement": {
                "viewed": viewed_count,
                "bookmarked": bookmarked_count,
                "inquiries": inquiry_count,
                "dismissed": dismissed_count
            }
        }

def render_property_alert_dashboard():
    """Convenience function to render property alert dashboard."""
    dashboard = PropertyAlertDashboard()
    dashboard.render_dashboard()

def add_property_alert_from_websocket(event_data: Dict[str, Any]):
    """Convenience function to add property alert from WebSocket event."""
    dashboard = PropertyAlertDashboard()
    dashboard.add_property_alert_from_event(event_data)