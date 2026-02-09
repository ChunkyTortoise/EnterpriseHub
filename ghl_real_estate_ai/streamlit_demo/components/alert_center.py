"""
Alert Center Component for GHL Real Estate AI

Real-time alert management with:
- Priority-based notifications
- Interactive one-click actions
- Sound and visual alerts
- Mobile-optimized notifications
"""

import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import streamlit as st


def render_alert_center_css():
    """Inject custom CSS for alert center - Obsidian Command Edition"""
    st.markdown(
        "\n    <style>\n    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');\n\n    /* Alert Center Styles */\n    .alert-center-container {\n        background: rgba(5, 7, 10, 0.8) !important;\n        border-radius: 20px;\n        padding: 2rem;\n        margin: 1rem 0;\n        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        position: relative;\n        overflow: hidden;\n        backdrop-filter: blur(20px);\n    }\n\n    .alert-center-header {\n        display: flex;\n        align-items: center;\n        justify-content: space-between;\n        margin-bottom: 2.5rem;\n        padding-bottom: 1.5rem;\n        border-bottom: 1px solid rgba(255, 255, 255, 0.05);\n    }\n\n    .alert-badge {\n        background: #ef4444;\n        color: white;\n        border-radius: 6px;\n        padding: 4px 12px;\n        font-size: 0.75rem;\n        font-weight: 800;\n        font-family: 'Space Grotesk', sans-serif;\n        text-transform: uppercase;\n        letter-spacing: 0.1em;\n        box-shadow: 0 0 15px rgba(239, 68, 68, 0.4);\n    }\n\n    .alert-item {\n        background: rgba(22, 27, 34, 0.7) !important;\n        border-left: 4px solid;\n        border-radius: 12px;\n        margin: 1rem 0;\n        padding: 1.25rem 1.5rem;\n        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);\n        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        backdrop-filter: blur(12px);\n    }\n\n    .alert-item:hover {\n        transform: translateX(10px);\n        border-color: rgba(99, 102, 241, 0.3);\n        box-shadow: 0 12px 48px rgba(99, 102, 241, 0.2);\n    }\n\n    .alert-critical { border-left-color: #ef4444; }\n    .alert-high { border-left-color: #f97316; }\n    .alert-medium { border-left-color: #6366F1; }\n    .alert-low { border-left-color: #10b981; }\n\n    .alert-title {\n        font-weight: 700;\n        font-size: 1.1rem;\n        color: #FFFFFF;\n        margin: 0;\n        font-family: 'Space Grotesk', sans-serif;\n        letter-spacing: -0.02em;\n    }\n\n    .alert-timestamp {\n        font-size: 0.75rem;\n        color: #8B949E;\n        font-weight: 600;\n        font-family: 'Space Grotesk', sans-serif;\n        text-transform: uppercase;\n    }\n\n    .alert-message {\n        color: #E6EDF3;\n        line-height: 1.6;\n        margin: 0.75rem 0;\n        font-family: 'Inter', sans-serif;\n        opacity: 0.9;\n    }\n\n    .stat-card {\n        background: rgba(255, 255, 255, 0.03) !important;\n        border-radius: 12px;\n        padding: 1.25rem;\n        text-align: center;\n        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);\n        border: 1px solid rgba(255, 255, 255, 0.05);\n        transition: transform 0.2s ease;\n    }\n\n    .stat-number {\n        font-size: 1.75rem;\n        font-weight: 700;\n        color: #FFFFFF;\n        margin: 0;\n        font-family: 'Space Grotesk', sans-serif;\n    }\n\n    .stat-label {\n        font-size: 0.7rem;\n        color: #8B949E;\n        margin-top: 0.5rem;\n        text-transform: uppercase;\n        font-weight: 700;\n        letter-spacing: 0.1em;\n        font-family: 'Space Grotesk', sans-serif;\n    }\n\n    .filter-chip {\n        background: rgba(255, 255, 255, 0.02) !important;\n        border: 1px solid rgba(255, 255, 255, 0.1) !important;\n        border-radius: 8px;\n        padding: 0.4rem 1rem;\n        font-size: 0.75rem;\n        color: #8B949E;\n        cursor: pointer;\n        transition: all 0.2s ease;\n        font-weight: 700;\n        text-transform: uppercase;\n        letter-spacing: 0.05em;\n        font-family: 'Space Grotesk', sans-serif;\n    }\n\n    .filter-chip.active {\n        background: #6366F1 !important;\n        color: white !important;\n        border-color: #6366F1 !important;\n        box-shadow: 0 0 15px rgba(99, 102, 241, 0.3);\n    }\n    </style>\n    ",
        unsafe_allow_html=True,
    )


class AlertPriority(Enum):
    """Alert priority levels"""

    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class AlertType(Enum):
    """Alert types"""

    HOT_LEAD = "hot_lead"
    STALE_LEAD = "stale_lead"
    BOOKING_REMINDER = "booking_reminder"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    BUDGET_QUALIFIED = "budget_qualified"
    SYSTEM_ISSUE = "system_issue"
    PERFORMANCE_DROP = "performance_drop"
    NEW_OPPORTUNITY = "new_opportunity"


class AlertCenter:
    """Real-time alert center with priority management"""

    def __init__(self, realtime_service, state_manager):
        self.realtime_service = realtime_service
        self.state_manager = state_manager
        self.last_update = datetime.now()
        self.alert_config = {
            AlertType.HOT_LEAD: {
                "icon": "🔥",
                "priority": AlertPriority.CRITICAL,
                "sound": True,
                "actions": ["call_lead", "schedule_meeting", "send_email"],
            },
            AlertType.STALE_LEAD: {
                "icon": "⚠️",
                "priority": AlertPriority.HIGH,
                "sound": False,
                "actions": ["reactivate_campaign", "schedule_call", "update_status"],
            },
            AlertType.BOOKING_REMINDER: {
                "icon": "📅",
                "priority": AlertPriority.HIGH,
                "sound": True,
                "actions": ["confirm_appointment", "send_reminder", "reschedule"],
            },
            AlertType.FOLLOW_UP_NEEDED: {
                "icon": "📞",
                "priority": AlertPriority.MEDIUM,
                "sound": False,
                "actions": ["create_task", "schedule_call", "send_email"],
            },
            AlertType.BUDGET_QUALIFIED: {
                "icon": "💰",
                "priority": AlertPriority.HIGH,
                "sound": True,
                "actions": ["priority_flag", "schedule_meeting", "notify_agent"],
            },
            AlertType.SYSTEM_ISSUE: {
                "icon": "🚨",
                "priority": AlertPriority.CRITICAL,
                "sound": True,
                "actions": ["check_system", "notify_admin", "create_ticket"],
            },
        }
        if "alert_filters" not in st.session_state:
            st.session_state.alert_filters = {"priority": "all", "type": "all", "read": "all", "time_range": "24h"}

    def render(self, container_key: str = "alert_center"):
        """Render the alert center"""
        render_alert_center_css()
        alerts_data = self._get_alerts_data()
        st.markdown('<div class="alert-center-container">', unsafe_allow_html=True)
        self._render_header(alerts_data)
        self._render_filter_bar()
        self._render_alert_stats(alerts_data)
        filtered_alerts = self._filter_alerts(alerts_data)
        self._render_alerts_list(filtered_alerts)
        st.markdown("</div>", unsafe_allow_html=True)
        if self.state_manager.user_preferences.auto_refresh:
            time.sleep(0.1)
            st.rerun()

    def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Get real-time alerts data"""
        try:
            recent_events = self.realtime_service.get_recent_events(
                event_type="new_alert", limit=50, since=datetime.now() - timedelta(hours=24)
            )
            if not recent_events:
                from ghl_real_estate_ai.services.realtime_data_service import DemoDataGenerator

                return DemoDataGenerator.generate_alerts(15)
            alerts = []
            for event in recent_events:
                data = event.data
                alert_type = data.get("alert_type", "follow_up_needed")
                alerts.append(
                    {
                        "id": event.id,
                        "type": alert_type,
                        "message": data.get("message", "Alert notification"),
                        "priority": self.alert_config.get(AlertType(alert_type), {"priority": AlertPriority.MEDIUM})[
                            "priority"
                        ].value,
                        "timestamp": event.timestamp,
                        "lead_id": data.get("lead_id"),
                        "read": False,
                        "action_required": data.get("action_required", True),
                    }
                )
            return sorted(alerts, key=lambda x: (x["priority"], x["timestamp"]), reverse=True)
        except Exception as e:
            st.error(f"Error loading alerts data: {e}")
            from ghl_real_estate_ai.services.realtime_data_service import DemoDataGenerator

            return DemoDataGenerator.generate_alerts(10)

    def _render_header(self, alerts_data: List[Dict[str, Any]]):
        """Render alert center header - Obsidian Style"""
        unread_count = len([a for a in alerts_data if not a["read"]])
        critical_count = len([a for a in alerts_data if a["priority"] == 4])
        st.markdown(
            f'''\n        <div class="alert-center-header">\n            <div>\n                <h3 style="margin: 0; color: #FFFFFF; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em;">🚨 COMMAND ALERT CENTER</h3>\n                <p style="margin: 0.5rem 0 0 0; color: #8B949E; font-size: 0.9rem; font-family: 'Inter', sans-serif; font-weight: 500;">\n                    Real-time tactical notifications and directives\n                </p>\n            </div>\n            <div style="display: flex; gap: 0.75rem; align-items: center;">\n                <span class="alert-badge">{unread_count} NEW SIGNALS</span>\n                {(f"""<span style="background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; font-family: 'Space Grotesk', sans-serif; border: 1px solid rgba(239, 68, 68, 0.3);">{critical_count} CRITICAL</span>""" if critical_count > 0 else "")}\n            </div>\n        </div>\n        ''',
            unsafe_allow_html=True,
        )

    def _render_filter_bar(self):
        """Render alert filter controls"""
        st.markdown('<div class="alert-filter-bar">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            priority_filter = st.selectbox(
                "Priority", ["all", "critical", "high", "medium", "low"], index=0, key="alert_priority_filter"
            )
            st.session_state.alert_filters["priority"] = priority_filter
        with col2:
            type_filter = st.selectbox(
                "Type",
                ["all", "hot_lead", "stale_lead", "booking_reminder", "follow_up_needed"],
                index=0,
                key="alert_type_filter",
            )
            st.session_state.alert_filters["type"] = type_filter
        with col3:
            read_filter = st.selectbox("Status", ["all", "unread", "read"], index=0, key="alert_read_filter")
            st.session_state.alert_filters["read"] = read_filter
        with col4:
            time_filter = st.selectbox("Time Range", ["1h", "6h", "24h", "7d", "30d"], index=2, key="alert_time_filter")
            st.session_state.alert_filters["time_range"] = time_filter
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_alert_stats(self, alerts_data: List[Dict[str, Any]]):
        """Render alert statistics - Obsidian Style"""
        if not alerts_data:
            return
        total_alerts = len(alerts_data)
        unread_alerts = len([a for a in alerts_data if not a["read"]])
        critical_alerts = len([a for a in alerts_data if a["priority"] == 4])
        high_alerts = len([a for a in alerts_data if a["priority"] == 3])
        response_rate = 85
        st.markdown(
            f'\n        <div class="alert-stats">\n            <div class="stat-card">\n                <div class="stat-number">{total_alerts}</div>\n                <div class="stat-label">TOTAL SIGNALS</div>\n            </div>\n            <div class="stat-card">\n                <div class="stat-number" style="color: #ef4444;">{unread_alerts}</div>\n                <div class="stat-label">UNREAD</div>\n            </div>\n            <div class="stat-card">\n                <div class="stat-number" style="color: #f97316;">{critical_alerts}</div>\n                <div class="stat-label">CRITICAL</div>\n            </div>\n            <div class="stat-card">\n                <div class="stat-number" style="color: #6366F1;">{high_alerts}</div>\n                <div class="stat-label">HIGH PRIORITY</div>\n            </div>\n            <div class="stat-card">\n                <div class="stat-number" style="color: #10b981;">{response_rate}%</div>\n                <div class="stat-label">SYNC RATE</div>\n            </div>\n        </div>\n        ',
            unsafe_allow_html=True,
        )

    def _filter_alerts(self, alerts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter alerts based on current filters"""
        filtered = alerts_data.copy()
        filters = st.session_state.alert_filters
        if filters["priority"] != "all":
            priority_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            filtered = [a for a in filtered if a["priority"] == priority_map[filters["priority"]]]
        if filters["type"] != "all":
            filtered = [a for a in filtered if a["type"] == filters["type"]]
        if filters["read"] != "all":
            is_unread = filters["read"] == "unread"
            filtered = [a for a in filtered if (not a["read"]) == is_unread]
        time_deltas = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        time_cutoff = datetime.now() - time_deltas.get(filters["time_range"], timedelta(hours=24))
        filtered = [a for a in filtered if a["timestamp"] > time_cutoff]
        return filtered

    def _render_alerts_list(self, alerts_data: List[Dict[str, Any]]):
        """Render the list of alerts"""
        if not alerts_data:
            st.markdown(
                f'\n            <div class="no-alerts">\n                <div class="no-alerts-icon">✅</div>\n                <h4>No alerts found</h4>\n                <p>All caught up! No alerts match your current filters.</p>\n            </div>\n            ',
                unsafe_allow_html=True,
            )
            return
        for alert in alerts_data:
            self._render_alert_item(alert)

    def _render_alert_item(self, alert: Dict[str, Any]):
        """Render individual alert item"""
        priority_classes = {4: "critical", 3: "high", 2: "medium", 1: "low"}
        priority_class = priority_classes[alert["priority"]]
        alert_type = AlertType(alert["type"])
        config = self.alert_config.get(alert_type, {"icon": "📢", "actions": ["acknowledge"]})
        time_diff = datetime.now() - alert["timestamp"]
        time_str = self._format_time_diff(time_diff)
        priority_indicator_class = f"priority-{priority_class}"
        st.markdown(
            f"""\n        <div class="alert-item alert-{priority_class}">\n            <div class="alert-header">\n                <div style="display: flex; align-items: center;">\n                    <div class="alert-priority-indicator {priority_indicator_class}"></div>\n                    <h4 class="alert-title">\n                        {config["icon"]} {alert["type"].replace("_", " ").title()}\n                    </h4>\n                </div>\n                <span class="alert-timestamp">{time_str}</span>\n            </div>\n            <div class="alert-message">{alert["message"]}</div>\n        """,
            unsafe_allow_html=True,
        )
        if alert["action_required"]:
            actions = config.get("actions", ["acknowledge"])
            self._render_alert_actions(alert, actions)
        st.markdown("</div>", unsafe_allow_html=True)

    def _render_alert_actions(self, alert: Dict[str, Any], actions: List[str]):
        """Render action buttons for alert"""
        st.markdown('<div class="alert-actions">', unsafe_allow_html=True)
        cols = st.columns(len(actions) + 1)
        action_configs = {
            "call_lead": {"label": "📞 Call", "type": "primary"},
            "schedule_meeting": {"label": "📅 Schedule", "type": "primary"},
            "send_email": {"label": "📧 Email", "type": "secondary"},
            "reactivate_campaign": {"label": "🔄 Reactivate", "type": "primary"},
            "schedule_call": {"label": "📞 Schedule Call", "type": "primary"},
            "update_status": {"label": "📝 Update", "type": "secondary"},
            "confirm_appointment": {"label": "✅ Confirm", "type": "primary"},
            "send_reminder": {"label": "📬 Remind", "type": "secondary"},
            "reschedule": {"label": "🔄 Reschedule", "type": "secondary"},
            "create_task": {"label": "📋 Task", "type": "secondary"},
            "priority_flag": {"label": "🏃 Priority", "type": "primary"},
            "notify_agent": {"label": "👨\u200d💼 Notify", "type": "secondary"},
            "acknowledge": {"label": "✓ Done", "type": "secondary"},
        }
        for i, action in enumerate(actions):
            config = action_configs.get(action, {"label": action.title(), "type": "secondary"})
            with cols[i]:
                if st.button(config["label"], key=f"alert_action_{alert['id']}_{action}", use_container_width=True):
                    self._handle_alert_action(alert, action)
        with cols[-1]:
            read_label = "📖 Mark Read" if not alert["read"] else "👁️ Unread"
            if st.button(read_label, key=f"alert_read_{alert['id']}", use_container_width=True):
                self._toggle_alert_read_status(alert)
        st.markdown("</div>", unsafe_allow_html=True)

    def _handle_alert_action(self, alert: Dict[str, Any], action: str):
        """Handle alert action"""
        action_messages = {
            "call_lead": "📞 Initiating call to lead...",
            "schedule_meeting": "📅 Opening calendar to schedule meeting...",
            "send_email": "📧 Opening email template...",
            "reactivate_campaign": "🔄 Reactivating lead campaign...",
            "schedule_call": "📞 Scheduling follow-up call...",
            "update_status": "📝 Opening status update form...",
            "confirm_appointment": "✅ Appointment confirmed!",
            "send_reminder": "📬 Reminder sent!",
            "reschedule": "🔄 Opening reschedule options...",
            "create_task": "📋 Creating follow-up task...",
            "priority_flag": "🏃 Lead flagged as priority!",
            "notify_agent": "👨\u200d💼 Agent notification sent!",
            "acknowledge": "✓ Alert acknowledged!",
        }
        message = action_messages.get(action, f"Action '{action}' executed!")
        st.success(message)
        alert["read"] = True
        self.realtime_service.emit_event(
            event_type="user_action",
            data={
                "alert_id": alert["id"],
                "action": action,
                "lead_id": alert.get("lead_id"),
                "timestamp": datetime.now().isoformat(),
            },
            priority=2,
        )
        time.sleep(1)
        st.rerun()

    def _toggle_alert_read_status(self, alert: Dict[str, Any]):
        """Toggle alert read status"""
        alert["read"] = not alert["read"]
        status = "read" if alert["read"] else "unread"
        st.info(f"Alert marked as {status}")
        self.realtime_service.emit_event(
            event_type="user_action",
            data={
                "alert_id": alert["id"],
                "action": "toggle_read",
                "new_status": status,
                "timestamp": datetime.now().isoformat(),
            },
            priority=1,
        )
        time.sleep(0.5)
        st.rerun()

    def _format_time_diff(self, time_diff: timedelta) -> str:
        """Format time difference for display"""
        total_seconds = int(time_diff.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s ago"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m ago"
        elif total_seconds < 86400:
            hours = total_seconds // 3600
            return f"{hours}h ago"
        else:
            days = total_seconds // 86400
            return f"{days}d ago"


def render_alert_center(realtime_service, state_manager):
    """Main function to render the alert center"""
    alert_center = AlertCenter(realtime_service, state_manager)
    alert_center.render()


if __name__ == "__main__":
    st.set_page_config(page_title="Alert Center Demo", page_icon="🚨", layout="wide")

    class MockRealtimeService:
        @st.cache_data(ttl=300)
        def get_recent_events(self, event_type=None, limit=50, since=None):
            return []

        def emit_event(self, event_type, data, priority=1):
            print(f"Event emitted: {event_type} - {data}")

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True
            notifications_enabled = True

        user_preferences = UserPreferences()

    st.title("🚨 Alert Center Demo")
    render_alert_center(MockRealtimeService(), MockStateManager())
