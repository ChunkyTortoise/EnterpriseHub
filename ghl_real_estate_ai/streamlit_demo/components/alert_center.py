"""
Alert Center Component for GHL Real Estate AI

Real-time alert management with:
- Priority-based notifications
- Interactive one-click actions
- Sound and visual alerts
- Mobile-optimized notifications
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
import uuid
from typing import Dict, List, Any, Optional
from enum import Enum

def render_alert_center_css():
    """Inject custom CSS for alert center"""
    st.markdown("""
    <style>
    /* Alert Center Styles */
    .alert-center-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        position: relative;
        overflow: hidden;
    }

    .alert-center-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.5rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
    }

    .alert-badge {
        background: linear-gradient(45deg, #ff4757, #ff3742);
        color: white;
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.8rem;
        font-weight: bold;
        animation: pulse 2s infinite;
    }

    .alert-item {
        background: white;
        border-left: 4px solid;
        border-radius: 0 10px 10px 0;
        margin: 0.75rem 0;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .alert-item::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: inherit;
    }

    .alert-item:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }

    .alert-critical {
        border-left-color: #e74c3c;
        background: linear-gradient(135deg, #fff5f5 0%, #ffe8e8 100%);
        animation: critical-pulse 2s infinite;
    }

    .alert-high {
        border-left-color: #f39c12;
        background: linear-gradient(135deg, #fffbf5 0%, #fff2e8 100%);
    }

    .alert-medium {
        border-left-color: #3498db;
        background: linear-gradient(135deg, #f5f9ff 0%, #e8f4ff 100%);
    }

    .alert-low {
        border-left-color: #2ecc71;
        background: linear-gradient(135deg, #f5fff5 0%, #e8ffe8 100%);
    }

    @keyframes critical-pulse {
        0% { box-shadow: 0 2px 10px rgba(231, 76, 60, 0.3); }
        50% { box-shadow: 0 4px 20px rgba(231, 76, 60, 0.6); }
        100% { box-shadow: 0 2px 10px rgba(231, 76, 60, 0.3); }
    }

    .alert-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }

    .alert-title {
        font-weight: 600;
        font-size: 1rem;
        color: #2c3e50;
        margin: 0;
    }

    .alert-timestamp {
        font-size: 0.8rem;
        color: #7f8c8d;
    }

    .alert-message {
        color: #34495e;
        line-height: 1.4;
        margin: 0.5rem 0;
    }

    .alert-actions {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
        flex-wrap: wrap;
    }

    .alert-action-btn {
        background: linear-gradient(45deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        font-size: 0.8rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }

    .alert-action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }

    .alert-action-primary {
        background: linear-gradient(45deg, #2ecc71, #27ae60);
    }

    .alert-action-secondary {
        background: linear-gradient(45deg, #95a5a6, #7f8c8d);
    }

    .alert-priority-indicator {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
        flex-shrink: 0;
    }

    .priority-critical {
        background: #e74c3c;
        box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        animation: priority-blink 1s infinite;
    }

    .priority-high {
        background: #f39c12;
    }

    .priority-medium {
        background: #3498db;
    }

    .priority-low {
        background: #2ecc71;
    }

    @keyframes priority-blink {
        0%, 50% { opacity: 1; }
        51%, 100% { opacity: 0.3; }
    }

    .alert-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }

    .stat-card {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }

    .stat-card:hover {
        transform: translateY(-2px);
    }

    .stat-number {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin: 0;
    }

    .stat-label {
        font-size: 0.8rem;
        color: #7f8c8d;
        margin-top: 0.25rem;
    }

    .alert-filter-bar {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
    }

    .filter-chip {
        background: white;
        border: 2px solid #ddd;
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        font-size: 0.8rem;
        cursor: pointer;
        transition: all 0.2s ease;
        user-select: none;
    }

    .filter-chip:hover {
        border-color: #667eea;
        background: #f8f9ff;
    }

    .filter-chip.active {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }

    .no-alerts {
        text-align: center;
        padding: 3rem 1rem;
        color: #7f8c8d;
    }

    .no-alerts-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }

    /* Mobile Responsive */
    @media (max-width: 768px) {
        .alert-center-container {
            padding: 1rem;
        }

        .alert-center-header {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
        }

        .alert-actions {
            flex-direction: column;
        }

        .alert-filter-bar {
            justify-content: center;
        }

        .alert-stats {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }
    }

    /* Dark mode support */
    @media (prefers-color-scheme: dark) {
        .alert-center-container {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
        }

        .alert-item {
            background: #34495e;
            color: white;
        }

        .alert-title {
            color: white;
        }

        .alert-message {
            color: #ecf0f1;
        }

        .stat-card {
            background: #2c3e50;
            color: white;
        }
    }
    </style>
    """, unsafe_allow_html=True)

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

        # Alert configuration
        self.alert_config = {
            AlertType.HOT_LEAD: {
                "icon": "🔥",
                "priority": AlertPriority.CRITICAL,
                "sound": True,
                "actions": ["call_lead", "schedule_meeting", "send_email"]
            },
            AlertType.STALE_LEAD: {
                "icon": "⚠️",
                "priority": AlertPriority.HIGH,
                "sound": False,
                "actions": ["reactivate_campaign", "schedule_call", "update_status"]
            },
            AlertType.BOOKING_REMINDER: {
                "icon": "📅",
                "priority": AlertPriority.HIGH,
                "sound": True,
                "actions": ["confirm_appointment", "send_reminder", "reschedule"]
            },
            AlertType.FOLLOW_UP_NEEDED: {
                "icon": "📞",
                "priority": AlertPriority.MEDIUM,
                "sound": False,
                "actions": ["create_task", "schedule_call", "send_email"]
            },
            AlertType.BUDGET_QUALIFIED: {
                "icon": "💰",
                "priority": AlertPriority.HIGH,
                "sound": True,
                "actions": ["priority_flag", "schedule_meeting", "notify_agent"]
            },
            AlertType.SYSTEM_ISSUE: {
                "icon": "🚨",
                "priority": AlertPriority.CRITICAL,
                "sound": True,
                "actions": ["check_system", "notify_admin", "create_ticket"]
            }
        }

        # Initialize filters
        if 'alert_filters' not in st.session_state:
            st.session_state.alert_filters = {
                'priority': 'all',
                'type': 'all',
                'read': 'all',
                'time_range': '24h'
            }

    def render(self, container_key: str = "alert_center"):
        """Render the alert center"""
        # Inject CSS
        render_alert_center_css()

        # Get alerts data
        alerts_data = self._get_alerts_data()

        # Render container
        st.markdown('<div class="alert-center-container">', unsafe_allow_html=True)

        # Header with stats
        self._render_header(alerts_data)

        # Filter bar
        self._render_filter_bar()

        # Alert statistics
        self._render_alert_stats(alerts_data)

        # Filtered alerts
        filtered_alerts = self._filter_alerts(alerts_data)

        # Render alerts list
        self._render_alerts_list(filtered_alerts)

        st.markdown('</div>', unsafe_allow_html=True)

        # Auto-refresh if enabled
        if self.state_manager.user_preferences.auto_refresh:
            time.sleep(0.1)
            st.rerun()

    def _get_alerts_data(self) -> List[Dict[str, Any]]:
        """Get real-time alerts data"""
        try:
            # Get recent alert events
            recent_events = self.realtime_service.get_recent_events(
                event_type="new_alert",
                limit=50,
                since=datetime.now() - timedelta(hours=24)
            )

            # If no real-time data, use demo data
            if not recent_events:
                from services.realtime_data_service import DemoDataGenerator
                return DemoDataGenerator.generate_alerts(15)

            # Process real-time events into alert data
            alerts = []
            for event in recent_events:
                data = event.data
                alert_type = data.get('alert_type', 'follow_up_needed')

                alerts.append({
                    'id': event.id,
                    'type': alert_type,
                    'message': data.get('message', 'Alert notification'),
                    'priority': self.alert_config.get(
                        AlertType(alert_type),
                        {'priority': AlertPriority.MEDIUM}
                    )['priority'].value,
                    'timestamp': event.timestamp,
                    'lead_id': data.get('lead_id'),
                    'read': False,
                    'action_required': data.get('action_required', True)
                })

            return sorted(alerts, key=lambda x: (x['priority'], x['timestamp']), reverse=True)

        except Exception as e:
            st.error(f"Error loading alerts data: {e}")
            # Fallback to demo data
            from services.realtime_data_service import DemoDataGenerator
            return DemoDataGenerator.generate_alerts(10)

    def _render_header(self, alerts_data: List[Dict[str, Any]]):
        """Render alert center header"""
        unread_count = len([a for a in alerts_data if not a['read']])
        critical_count = len([a for a in alerts_data if a['priority'] == 4])

        st.markdown(f"""
        <div class="alert-center-header">
            <div>
                <h3 style="margin: 0; color: #2c3e50;">🚨 Alert Center</h3>
                <p style="margin: 0.25rem 0 0 0; color: #7f8c8d; font-size: 0.9rem;">
                    Real-time notifications and actions
                </p>
            </div>
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <span class="alert-badge">{unread_count} New</span>
                {f'<span style="background: #e74c3c; color: white; padding: 0.25rem 0.5rem; border-radius: 10px; font-size: 0.7rem;">{critical_count} Critical</span>' if critical_count > 0 else ''}
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_filter_bar(self):
        """Render alert filter controls"""
        st.markdown('<div class="alert-filter-bar">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            priority_filter = st.selectbox(
                "Priority",
                ["all", "critical", "high", "medium", "low"],
                index=0,
                key="alert_priority_filter"
            )
            st.session_state.alert_filters['priority'] = priority_filter

        with col2:
            type_filter = st.selectbox(
                "Type",
                ["all", "hot_lead", "stale_lead", "booking_reminder", "follow_up_needed"],
                index=0,
                key="alert_type_filter"
            )
            st.session_state.alert_filters['type'] = type_filter

        with col3:
            read_filter = st.selectbox(
                "Status",
                ["all", "unread", "read"],
                index=0,
                key="alert_read_filter"
            )
            st.session_state.alert_filters['read'] = read_filter

        with col4:
            time_filter = st.selectbox(
                "Time Range",
                ["1h", "6h", "24h", "7d", "30d"],
                index=2,
                key="alert_time_filter"
            )
            st.session_state.alert_filters['time_range'] = time_filter

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_alert_stats(self, alerts_data: List[Dict[str, Any]]):
        """Render alert statistics"""
        if not alerts_data:
            return

        # Calculate stats
        total_alerts = len(alerts_data)
        unread_alerts = len([a for a in alerts_data if not a['read']])
        critical_alerts = len([a for a in alerts_data if a['priority'] == 4])
        high_alerts = len([a for a in alerts_data if a['priority'] == 3])

        # Response rate simulation
        response_rate = 85  # In production, calculate from actual data

        st.markdown(f"""
        <div class="alert-stats">
            <div class="stat-card">
                <div class="stat-number">{total_alerts}</div>
                <div class="stat-label">Total Alerts</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #e74c3c;">{unread_alerts}</div>
                <div class="stat-label">Unread</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #f39c12;">{critical_alerts}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #3498db;">{high_alerts}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #2ecc71;">{response_rate}%</div>
                <div class="stat-label">Response Rate</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _filter_alerts(self, alerts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter alerts based on current filters"""
        filtered = alerts_data.copy()

        filters = st.session_state.alert_filters

        # Priority filter
        if filters['priority'] != 'all':
            priority_map = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            filtered = [a for a in filtered if a['priority'] == priority_map[filters['priority']]]

        # Type filter
        if filters['type'] != 'all':
            filtered = [a for a in filtered if a['type'] == filters['type']]

        # Read status filter
        if filters['read'] != 'all':
            is_unread = filters['read'] == 'unread'
            filtered = [a for a in filtered if (not a['read']) == is_unread]

        # Time range filter
        time_deltas = {
            '1h': timedelta(hours=1),
            '6h': timedelta(hours=6),
            '24h': timedelta(hours=24),
            '7d': timedelta(days=7),
            '30d': timedelta(days=30)
        }

        time_cutoff = datetime.now() - time_deltas.get(filters['time_range'], timedelta(hours=24))
        filtered = [a for a in filtered if a['timestamp'] > time_cutoff]

        return filtered

    def _render_alerts_list(self, alerts_data: List[Dict[str, Any]]):
        """Render the list of alerts"""
        if not alerts_data:
            st.markdown(f"""
            <div class="no-alerts">
                <div class="no-alerts-icon">✅</div>
                <h4>No alerts found</h4>
                <p>All caught up! No alerts match your current filters.</p>
            </div>
            """, unsafe_allow_html=True)
            return

        for alert in alerts_data:
            self._render_alert_item(alert)

    def _render_alert_item(self, alert: Dict[str, Any]):
        """Render individual alert item"""
        # Priority styling
        priority_classes = {4: 'critical', 3: 'high', 2: 'medium', 1: 'low'}
        priority_class = priority_classes[alert['priority']]

        # Alert type config
        alert_type = AlertType(alert['type'])
        config = self.alert_config.get(alert_type, {
            'icon': '📢',
            'actions': ['acknowledge']
        })

        # Time formatting
        time_diff = datetime.now() - alert['timestamp']
        time_str = self._format_time_diff(time_diff)

        # Priority indicator
        priority_indicator_class = f"priority-{priority_class}"

        st.markdown(f"""
        <div class="alert-item alert-{priority_class}">
            <div class="alert-header">
                <div style="display: flex; align-items: center;">
                    <div class="alert-priority-indicator {priority_indicator_class}"></div>
                    <h4 class="alert-title">
                        {config['icon']} {alert['type'].replace('_', ' ').title()}
                    </h4>
                </div>
                <span class="alert-timestamp">{time_str}</span>
            </div>
            <div class="alert-message">{alert['message']}</div>
        """, unsafe_allow_html=True)

        # Action buttons
        if alert['action_required']:
            actions = config.get('actions', ['acknowledge'])
            self._render_alert_actions(alert, actions)

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_alert_actions(self, alert: Dict[str, Any], actions: List[str]):
        """Render action buttons for alert"""
        st.markdown('<div class="alert-actions">', unsafe_allow_html=True)

        # Create columns for actions
        cols = st.columns(len(actions) + 1)

        action_configs = {
            'call_lead': {'label': '📞 Call', 'type': 'primary'},
            'schedule_meeting': {'label': '📅 Schedule', 'type': 'primary'},
            'send_email': {'label': '📧 Email', 'type': 'secondary'},
            'reactivate_campaign': {'label': '🔄 Reactivate', 'type': 'primary'},
            'schedule_call': {'label': '📞 Schedule Call', 'type': 'primary'},
            'update_status': {'label': '📝 Update', 'type': 'secondary'},
            'confirm_appointment': {'label': '✅ Confirm', 'type': 'primary'},
            'send_reminder': {'label': '📬 Remind', 'type': 'secondary'},
            'reschedule': {'label': '🔄 Reschedule', 'type': 'secondary'},
            'create_task': {'label': '📋 Task', 'type': 'secondary'},
            'priority_flag': {'label': '🏃 Priority', 'type': 'primary'},
            'notify_agent': {'label': '👨‍💼 Notify', 'type': 'secondary'},
            'acknowledge': {'label': '✓ Done', 'type': 'secondary'}
        }

        for i, action in enumerate(actions):
            config = action_configs.get(action, {'label': action.title(), 'type': 'secondary'})

            with cols[i]:
                if st.button(
                    config['label'],
                    key=f"alert_action_{alert['id']}_{action}",
                    use_container_width=True
                ):
                    self._handle_alert_action(alert, action)

        # Mark as read button
        with cols[-1]:
            read_label = "📖 Mark Read" if not alert['read'] else "👁️ Unread"
            if st.button(read_label, key=f"alert_read_{alert['id']}", use_container_width=True):
                self._toggle_alert_read_status(alert)

        st.markdown('</div>', unsafe_allow_html=True)

    def _handle_alert_action(self, alert: Dict[str, Any], action: str):
        """Handle alert action"""
        # Action handlers
        action_messages = {
            'call_lead': '📞 Initiating call to lead...',
            'schedule_meeting': '📅 Opening calendar to schedule meeting...',
            'send_email': '📧 Opening email template...',
            'reactivate_campaign': '🔄 Reactivating lead campaign...',
            'schedule_call': '📞 Scheduling follow-up call...',
            'update_status': '📝 Opening status update form...',
            'confirm_appointment': '✅ Appointment confirmed!',
            'send_reminder': '📬 Reminder sent!',
            'reschedule': '🔄 Opening reschedule options...',
            'create_task': '📋 Creating follow-up task...',
            'priority_flag': '🏃 Lead flagged as priority!',
            'notify_agent': '👨‍💼 Agent notification sent!',
            'acknowledge': '✓ Alert acknowledged!'
        }

        message = action_messages.get(action, f"Action '{action}' executed!")

        st.success(message)

        # Mark alert as read after action
        alert['read'] = True

        # Emit action event
        self.realtime_service.emit_event(
            event_type="user_action",
            data={
                'alert_id': alert['id'],
                'action': action,
                'lead_id': alert.get('lead_id'),
                'timestamp': datetime.now().isoformat()
            },
            priority=2
        )

        # Auto-refresh to show changes
        time.sleep(1)
        st.rerun()

    def _toggle_alert_read_status(self, alert: Dict[str, Any]):
        """Toggle alert read status"""
        alert['read'] = not alert['read']
        status = "read" if alert['read'] else "unread"

        st.info(f"Alert marked as {status}")

        # Emit status change event
        self.realtime_service.emit_event(
            event_type="user_action",
            data={
                'alert_id': alert['id'],
                'action': 'toggle_read',
                'new_status': status,
                'timestamp': datetime.now().isoformat()
            },
            priority=1
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


# Streamlit component integration
if __name__ == "__main__":
    # Demo mode for testing
    st.set_page_config(
        page_title="Alert Center Demo",
        page_icon="🚨",
        layout="wide"
    )

    # Mock services for demo
    class MockRealtimeService:
        def get_recent_events(self, event_type=None, limit=50, since=None):
            return []  # Return empty to trigger demo data

        def emit_event(self, event_type, data, priority=1):
            print(f"Event emitted: {event_type} - {data}")

    class MockStateManager:
        class UserPreferences:
            auto_refresh = True
            notifications_enabled = True

        user_preferences = UserPreferences()

    # Render demo
    st.title("🚨 Alert Center Demo")
    render_alert_center(MockRealtimeService(), MockStateManager())