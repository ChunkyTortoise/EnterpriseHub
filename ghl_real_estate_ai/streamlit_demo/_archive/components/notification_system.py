"""
Real-Time Notification System for Jorge's Dashboard.

Provides live notification display with priority handling, dismissal actions,
and integration with the WebSocket event system. Shows system alerts,
lead notifications, commission updates, and performance warnings.

Features:
- Priority-based notification queue with auto-dismissal
- Toast-style notifications for high-priority events
- Notification history and management
- Sound and visual alerts for critical events
- Role-based notification filtering
"""

import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Notification:
    """Notification data structure."""

    id: str
    title: str
    message: str
    severity: str  # critical, error, warning, info, success
    timestamp: datetime
    auto_dismiss_seconds: Optional[int] = None
    dismissed: bool = False
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    category: str = "general"  # lead, commission, system, performance
    source_event_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {**asdict(self), "timestamp": self.timestamp.isoformat()}


class NotificationSystem:
    """
    Real-time notification management system.

    Handles notification display, queuing, dismissal, and integration
    with WebSocket events for real-time updates.
    """

    def __init__(self, max_notifications: int = 50):
        self.max_notifications = max_notifications

        # Initialize session state
        if "notifications" not in st.session_state:
            st.session_state.notifications = []

        if "notification_settings" not in st.session_state:
            st.session_state.notification_settings = {
                "show_toast": True,
                "auto_dismiss_info": 5,
                "auto_dismiss_warning": 10,
                "auto_dismiss_error": 0,  # Manual dismiss only
                "sound_enabled": False,
                "categories_enabled": {
                    "lead": True,
                    "commission": True,
                    "system": True,
                    "performance": True,
                    "property_alert": True,
                },
            }

        if "last_notification_check" not in st.session_state:
            st.session_state.last_notification_check = time.time()

    def add_notification(
        self,
        title: str,
        message: str,
        severity: str = "info",
        category: str = "general",
        auto_dismiss_seconds: Optional[int] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        source_event_type: Optional[str] = None,
    ) -> str:
        """
        Add new notification to the system.

        Args:
            title: Notification title
            message: Notification message
            severity: Severity level (critical, error, warning, info, success)
            category: Category (lead, commission, system, performance, general)
            auto_dismiss_seconds: Auto-dismiss time in seconds (optional)
            action_url: URL for notification action button (optional)
            action_label: Label for action button (optional)
            source_event_type: Source event type for tracking (optional)

        Returns:
            Notification ID
        """
        # Generate unique notification ID
        notification_id = f"notif_{int(time.time() * 1000)}_{len(st.session_state.notifications)}"

        # Determine auto-dismiss based on severity if not specified
        if auto_dismiss_seconds is None:
            auto_dismiss_seconds = self._get_default_auto_dismiss(severity)

        # Create notification
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            auto_dismiss_seconds=auto_dismiss_seconds,
            action_url=action_url,
            action_label=action_label,
            category=category,
            source_event_type=source_event_type,
        )

        # Add to beginning of list (most recent first)
        st.session_state.notifications.insert(0, notification)

        # Trim list to max size
        if len(st.session_state.notifications) > self.max_notifications:
            st.session_state.notifications = st.session_state.notifications[: self.max_notifications]

        logger.info(f"Added notification: {title} ({severity})")
        return notification_id

    def _get_default_auto_dismiss(self, severity: str) -> int:
        """Get default auto-dismiss time based on severity."""
        settings = st.session_state.notification_settings

        if severity == "critical":
            return 0  # Never auto-dismiss
        elif severity == "error":
            return settings.get("auto_dismiss_error", 0)
        elif severity == "warning":
            return settings.get("auto_dismiss_warning", 10)
        else:  # info, success
            return settings.get("auto_dismiss_info", 5)

    def render_notification_center(self):
        """Render the main notification center interface."""
        st.subheader("🔔 Notification Center")

        # Header with stats and controls
        self._render_notification_header()

        # Settings panel
        with st.expander("⚙️ Notification Settings", expanded=False):
            self._render_notification_settings()

        # Notification list
        self._render_notification_list()

    def _render_notification_header(self):
        """Render notification header with stats and controls."""
        notifications = st.session_state.notifications
        unread_count = len([n for n in notifications if not n.dismissed])

        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            if unread_count > 0:
                st.write(f"📬 {unread_count} unread notifications")
            else:
                st.write("✅ All notifications read")

        with col2:
            if st.button("🗑️ Clear All", key="clear_notifications"):
                st.session_state.notifications = []
                st.rerun()

        with col3:
            if st.button("✅ Mark All Read", key="mark_all_read"):
                for notification in notifications:
                    notification.dismissed = True
                st.rerun()

    def _render_notification_settings(self):
        """Render notification settings panel."""
        settings = st.session_state.notification_settings

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Display Settings")

            settings["show_toast"] = st.checkbox(
                "Show toast notifications", value=settings["show_toast"], key="toast_enabled"
            )

            settings["sound_enabled"] = st.checkbox(
                "Sound alerts (high priority)", value=settings["sound_enabled"], key="sound_enabled"
            )

        with col2:
            st.subheader("Auto-Dismiss Settings")

            settings["auto_dismiss_info"] = st.slider(
                "Info notifications (seconds)", 0, 30, settings["auto_dismiss_info"], key="auto_dismiss_info"
            )

            settings["auto_dismiss_warning"] = st.slider(
                "Warning notifications (seconds)", 0, 60, settings["auto_dismiss_warning"], key="auto_dismiss_warning"
            )

            settings["auto_dismiss_error"] = st.slider(
                "Error notifications (0 = manual only)",
                0,
                120,
                settings["auto_dismiss_error"],
                key="auto_dismiss_error",
            )

        # Category filters
        st.subheader("Categories")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            settings["categories_enabled"]["lead"] = st.checkbox(
                "🫂 Leads", value=settings["categories_enabled"]["lead"], key="cat_lead"
            )
        with col2:
            settings["categories_enabled"]["commission"] = st.checkbox(
                "💰 Commission", value=settings["categories_enabled"]["commission"], key="cat_commission"
            )
        with col3:
            settings["categories_enabled"]["system"] = st.checkbox(
                "⚙️ System", value=settings["categories_enabled"]["system"], key="cat_system"
            )
        with col4:
            settings["categories_enabled"]["performance"] = st.checkbox(
                "📊 Performance", value=settings["categories_enabled"]["performance"], key="cat_performance"
            )
        with col5:
            settings["categories_enabled"]["property_alert"] = st.checkbox(
                "🏠 Properties", value=settings["categories_enabled"]["property_alert"], key="cat_property_alert"
            )

    def _render_notification_list(self):
        """Render list of notifications with filtering and actions."""
        notifications = st.session_state.notifications
        settings = st.session_state.notification_settings

        if not notifications:
            st.info("📭 No notifications yet. You'll see live updates here when events occur.")
            return

        # Filter notifications based on category settings
        filtered_notifications = [n for n in notifications if settings["categories_enabled"].get(n.category, True)]

        if not filtered_notifications:
            st.info("🔍 No notifications match current filter settings.")
            return

        # Group notifications by date
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        today_notifications = [n for n in filtered_notifications if n.timestamp.date() == today]
        yesterday_notifications = [n for n in filtered_notifications if n.timestamp.date() == yesterday]
        older_notifications = [n for n in filtered_notifications if n.timestamp.date() < yesterday]

        # Render notification groups
        if today_notifications:
            st.markdown("**📅 Today**")
            for notification in today_notifications:
                self._render_notification_item(notification)

        if yesterday_notifications:
            st.markdown("**📅 Yesterday**")
            for notification in yesterday_notifications:
                self._render_notification_item(notification)

        if older_notifications:
            with st.expander("📅 Older Notifications", expanded=False):
                for notification in older_notifications:
                    self._render_notification_item(notification)

    def _render_notification_item(self, notification: Notification):
        """Render individual notification item."""
        # Check if notification should be auto-dismissed
        if notification.auto_dismiss_seconds and notification.auto_dismiss_seconds > 0 and not notification.dismissed:
            elapsed = (datetime.now(timezone.utc) - notification.timestamp).total_seconds()
            if elapsed > notification.auto_dismiss_seconds:
                notification.dismissed = True

        # Severity styling
        severity_styles = {
            "critical": {"color": "#fee2e2", "border": "#dc2626", "icon": "🚨"},
            "error": {"color": "#fef2f2", "border": "#ef4444", "icon": "❌"},
            "warning": {"color": "#fefbeb", "border": "#f59e0b", "icon": "⚠️"},
            "info": {"color": "#eff6ff", "border": "#3b82f6", "icon": "ℹ️"},
            "success": {"color": "#f0fdf4", "border": "#22c55e", "icon": "✅"},
        }

        style = severity_styles.get(notification.severity, severity_styles["info"])

        # Category icons
        category_icons = {
            "lead": "👤",
            "commission": "💰",
            "system": "⚙️",
            "performance": "📊",
            "property_alert": "🏠",
            "general": "📄",
        }

        # Opacity based on dismissed status
        opacity = "0.6" if notification.dismissed else "1.0"

        # Time formatting
        time_str = notification.timestamp.strftime("%H:%M")

        # Render notification container
        with st.container():
            st.markdown(
                f"""
            <div style="
                background-color: {style["color"]};
                border: 1px solid {style["border"]};
                border-radius: 8px;
                padding: 1rem;
                margin: 0.5rem 0;
                opacity: {opacity};
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0; color: #1f2937;">
                            {style["icon"]} {category_icons.get(notification.category, "📄")} {notification.title}
                        </h4>
                        <p style="margin: 0.5rem 0; color: #374151;">{notification.message}</p>
                        <small style="color: #6b7280;">
                            {time_str} • {notification.category} • {notification.severity}
                        </small>
                    </div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Action buttons
            col1, col2, col3 = st.columns([2, 1, 1])

            with col2:
                if notification.action_url and notification.action_label:
                    if st.button(notification.action_label, key=f"action_{notification.id}"):
                        # In a real implementation, this would navigate to the URL
                        st.info(f"Would navigate to: {notification.action_url}")

            with col3:
                if not notification.dismissed:
                    if st.button("✅ Dismiss", key=f"dismiss_{notification.id}"):
                        notification.dismissed = True
                        st.rerun()

    def render_toast_notifications(self):
        """Render toast-style notifications for high-priority items."""
        if not st.session_state.notification_settings.get("show_toast", True):
            return

        # Get recent high-priority notifications
        current_time = datetime.now(timezone.utc)
        toast_notifications = []

        for notification in st.session_state.notifications:
            if (
                notification.severity in ["critical", "error"]
                and not notification.dismissed
                and (current_time - notification.timestamp).total_seconds() < 10
            ):  # Show for 10 seconds
                toast_notifications.append(notification)

        # Render toast notifications
        for notification in toast_notifications[:3]:  # Show max 3 toasts
            self._render_toast_notification(notification)

    def _render_toast_notification(self, notification: Notification):
        """Render individual toast notification."""
        severity_colors = {
            "critical": "#dc2626",
            "error": "#ef4444",
            "warning": "#f59e0b",
            "info": "#3b82f6",
            "success": "#22c55e",
        }

        color = severity_colors.get(notification.severity, "#3b82f6")

        # Toast notification styling
        st.markdown(
            f"""
        <div style="
            position: fixed;
            top: 1rem;
            right: 1rem;
            background: white;
            color: {color};
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid {color};
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        ">
            <strong>{notification.title}</strong><br>
            {notification.message}
        </div>
        
        <style>
        @keyframes slideIn {{
            from {{ transform: translateX(100%); }}
            to {{ transform: translateX(0); }}
        }}
        </style>
        """,
            unsafe_allow_html=True,
        )

    def process_websocket_event(self, event_data: Dict[str, Any]):
        """
        Process WebSocket event and create appropriate notification.

        Args:
            event_data: WebSocket event data
        """
        event_type = event_data.get("event_type", "unknown")
        data = event_data.get("data", {})
        priority = event_data.get("priority", "normal")

        # Create notification based on event type
        if event_type == "lead_update":
            self._create_lead_notification(data, priority)
        elif event_type == "conversation_update":
            self._create_conversation_notification(data, priority)
        elif event_type == "commission_update":
            self._create_commission_notification(data, priority)
        elif event_type == "system_alert":
            self._create_system_notification(data, priority)
        elif event_type == "performance_update":
            self._create_performance_notification(data, priority)
        elif event_type == "property_alert":
            self._create_property_alert_notification(data, priority)

    def _create_lead_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for lead update."""
        action = data.get("action", "updated")
        lead_id = data.get("lead_id", "Unknown")
        lead_data = data.get("lead_data", {})

        title = f"Lead {action.title()}"
        message = f"Lead {lead_id}"
        if "name" in lead_data:
            message += f" ({lead_data['name']})"

        severity = "success" if action == "created" else "info"
        if action in ["qualified", "hot"]:
            severity = "warning"  # Important but not urgent

        self.add_notification(
            title=title, message=message, severity=severity, category="lead", source_event_type="lead_update"
        )

    def _create_conversation_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for conversation update."""
        stage = data.get("stage", "Unknown")
        lead_id = data.get("lead_id", "Unknown")

        title = "Conversation Progress"
        message = f"Lead {lead_id} moved to {stage}"

        severity = "warning" if stage in ["Q4", "hot", "ready"] else "info"

        self.add_notification(
            title=title, message=message, severity=severity, category="lead", source_event_type="conversation_update"
        )

    def _create_commission_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for commission update."""
        amount = data.get("formatted_amount", "Unknown")
        status = data.get("pipeline_status", "unknown")

        title = f"Commission {status.title()}"
        message = f"Deal value: {amount}"

        severity = "success" if status == "paid" else "warning" if status == "confirmed" else "info"

        self.add_notification(
            title=title,
            message=message,
            severity=severity,
            category="commission",
            source_event_type="commission_update",
        )

    def _create_system_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for system alert."""
        alert_type = data.get("alert_type", "Unknown")
        message = data.get("message", "System alert")
        severity = data.get("severity", "info")

        self.add_notification(
            title=f"System Alert: {alert_type}",
            message=message,
            severity=severity,
            category="system",
            source_event_type="system_alert",
        )

    def _create_performance_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for performance update."""
        metric_name = data.get("metric_name", "Unknown")
        formatted_value = data.get("formatted_value", "Unknown")
        trend = data.get("trend", "neutral")

        # Only notify on significant performance changes
        if trend in ["down", "critical"]:
            title = "Performance Alert"
            message = f"{metric_name}: {formatted_value}"
            severity = "warning" if trend == "down" else "error"

            self.add_notification(
                title=title,
                message=message,
                severity=severity,
                category="performance",
                source_event_type="performance_update",
            )

    def _create_property_alert_notification(self, data: Dict[str, Any], priority: str):
        """Create notification for property alert."""
        alert_type = data.get("alert_type", "new_match")
        match_score = data.get("match_score", 0)
        lead_id = data.get("lead_id", "Unknown")
        property_summary = data.get("property_summary", {})

        # Extract property details
        address = property_summary.get("address", "Unknown Property")
        formatted_price = property_summary.get("formatted_price", "Price on request")

        # Create notification title based on alert type
        alert_type_titles = {
            "new_match": "🏠 New Property Match",
            "price_drop": "📉 Price Drop Alert",
            "market_opportunity": "💎 Market Opportunity",
            "back_on_market": "🔄 Back on Market",
            "price_increase": "📈 Price Update",
            "status_change": "📋 Status Update",
        }

        title = alert_type_titles.get(alert_type, "🏠 Property Alert")

        # Create comprehensive message
        message = f"{address} • {formatted_price} • {match_score}% match"
        if match_score >= 90:
            message += " • ⭐ Excellent match!"
        elif match_score >= 80:
            message += " • ✨ Great match!"

        # Determine severity based on match score and alert type
        if alert_type in ["market_opportunity", "price_drop"] and match_score >= 85:
            severity = "warning"  # High priority for good opportunities
        elif match_score >= 90:
            severity = "success"  # Excellent matches
        elif alert_type == "price_drop":
            severity = "info"  # Price drops are always interesting
        else:
            severity = "info"  # Standard property alerts

        # Create action URL for viewing property details
        action_url = f"/property/{data.get('property_id', 'unknown')}"
        action_label = "View Property"

        self.add_notification(
            title=title,
            message=message,
            severity=severity,
            category="property_alert",
            action_url=action_url,
            action_label=action_label,
            source_event_type="property_alert",
        )

    def get_notification_summary(self) -> Dict[str, Any]:
        """Get notification summary statistics."""
        notifications = st.session_state.notifications

        total = len(notifications)
        unread = len([n for n in notifications if not n.dismissed])

        by_severity = {}
        for notification in notifications:
            severity = notification.severity
            by_severity[severity] = by_severity.get(severity, 0) + 1

        by_category = {}
        for notification in notifications:
            category = notification.category
            by_category[category] = by_category.get(category, 0) + 1

        return {
            "total": total,
            "unread": unread,
            "by_severity": by_severity,
            "by_category": by_category,
            "last_notification": notifications[0].timestamp.isoformat() if notifications else None,
        }


def render_notification_system():
    """Convenience function to render notification system."""
    notification_system = NotificationSystem()

    # Render toast notifications (always visible for high priority)
    notification_system.render_toast_notifications()

    # Render main notification center
    notification_system.render_notification_center()


def add_notification(title: str, message: str, severity: str = "info", category: str = "general", **kwargs) -> str:
    """Convenience function to add notification."""
    notification_system = NotificationSystem()
    return notification_system.add_notification(title, message, severity, category, **kwargs)


def process_websocket_event_notification(event_data: Dict[str, Any]):
    """Convenience function to process WebSocket event for notifications."""
    notification_system = NotificationSystem()
    notification_system.process_websocket_event(event_data)
