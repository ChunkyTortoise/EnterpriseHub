"""
Smart Navigation System (Phase 1 Enhancement)

Provides:
- Breadcrumb trails with context-aware navigation
- Context-aware quick actions based on user location
- Progressive disclosure for cleaner interfaces
- Smart shortcuts and workflow acceleration
- Navigation analytics and optimization

Target: 25% reduction in navigation clicks through intelligent UX
"""

import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path


@dataclass
class NavigationContext:
    """Context information for smart navigation."""

    current_hub: str
    current_tab: Optional[str] = None
    current_section: Optional[str] = None
    user_role: str = "admin"
    location_id: Optional[str] = None
    last_action: Optional[str] = None
    session_data: Dict[str, Any] = None


@dataclass
class QuickAction:
    """Definition for context-aware quick action."""

    label: str
    action_type: str  # "navigate", "modal", "function", "external"
    target: str  # Hub, URL, function name, etc.
    icon: str = "⚡"
    description: str = ""
    conditions: Dict[str, Any] = None  # Conditions for when to show
    priority: int = 1  # Higher priority = shown first


class SmartNavigationService:
    """Core service for smart navigation and context awareness."""

    def __init__(self):
        """Initialize smart navigation service."""
        self.navigation_history = []
        self.context_actions = self._initialize_context_actions()
        self.analytics = NavigationAnalytics()

    def _initialize_context_actions(self) -> Dict[str, List[QuickAction]]:
        """Initialize context-aware quick actions for each hub."""
        return {
            "Executive Command Center": [
                QuickAction("View Pipeline", "modal", "revenue_pipeline", "💰", "Open revenue pipeline overview"),
                QuickAction("Export Dashboard", "function", "export_executive_data", "📊", "Export current dashboard data"),
                QuickAction("Schedule Report", "modal", "schedule_report", "📅", "Schedule automated reports"),
                QuickAction("AI Insights", "navigate", "AI Insights", "🤖", "View AI-generated insights"),
            ],
            "Lead Intelligence Hub": [
                QuickAction("Score New Lead", "modal", "lead_scoring", "🎯", "Quick lead scoring interface"),
                QuickAction("Behavioral Analysis", "navigate", "Behavioral Analysis", "🧠", "Deep behavioral insights"),
                QuickAction("Hot Leads Alert", "function", "show_hot_leads", "🔥", "Show current hot leads"),
                QuickAction("Lead Assignment", "modal", "assign_leads", "👥", "Assign leads to agents"),
            ],
            "Automation Studio": [
                QuickAction("Quick Workflow", "modal", "create_workflow", "⚡", "Create new automation workflow"),
                QuickAction("Trigger Manager", "navigate", "Triggers", "🔧", "Manage automation triggers"),
                QuickAction("Performance Monitor", "navigate", "Performance", "📈", "Monitor automation performance"),
                QuickAction("Template Library", "modal", "templates", "📋", "Access workflow templates"),
            ],
            "Sales Copilot": [
                QuickAction("AI Coaching", "modal", "ai_coaching", "🎓", "Get AI coaching suggestions"),
                QuickAction("Deal Analysis", "modal", "deal_analysis", "💼", "Analyze current deal"),
                QuickAction("Next Best Action", "function", "suggest_action", "🎯", "Get next best action"),
                QuickAction("Objection Handler", "modal", "objection_help", "🛡️", "Handle current objection"),
            ],
            "Ops & Optimization": [
                QuickAction("Performance Metrics", "navigate", "Analytics", "📊", "View performance analytics"),
                QuickAction("Cost Analysis", "modal", "cost_analysis", "💰", "Analyze operational costs"),
                QuickAction("Resource Planning", "modal", "resource_planning", "📅", "Plan resource allocation"),
                QuickAction("Quality Audit", "function", "quality_check", "✅", "Run quality assurance check"),
            ]
        }

    def get_breadcrumb_trail(self, context: NavigationContext) -> List[Dict[str, str]]:
        """Generate breadcrumb trail based on current context."""
        breadcrumbs = [
            {"label": "Home", "target": "home", "icon": "🏠"}
        ]

        # Add hub level
        if context.current_hub:
            hub_icon = self._get_hub_icon(context.current_hub)
            breadcrumbs.append({
                "label": context.current_hub,
                "target": context.current_hub,
                "icon": hub_icon
            })

        # Add tab level
        if context.current_tab and context.current_tab != context.current_hub:
            breadcrumbs.append({
                "label": context.current_tab,
                "target": f"{context.current_hub}/{context.current_tab}",
                "icon": "📄"
            })

        # Add section level
        if context.current_section:
            breadcrumbs.append({
                "label": context.current_section,
                "target": f"{context.current_hub}/{context.current_tab}/{context.current_section}",
                "icon": "📋"
            })

        return breadcrumbs

    def get_context_actions(self, context: NavigationContext) -> List[QuickAction]:
        """Get context-aware quick actions based on current location and state."""
        base_actions = self.context_actions.get(context.current_hub, [])

        # Filter actions based on conditions and context
        filtered_actions = []
        for action in base_actions:
            if self._should_show_action(action, context):
                filtered_actions.append(action)

        # Add dynamic actions based on current state
        dynamic_actions = self._get_dynamic_actions(context)
        filtered_actions.extend(dynamic_actions)

        # Sort by priority
        filtered_actions.sort(key=lambda x: x.priority, reverse=True)

        return filtered_actions[:6]  # Limit to 6 most relevant actions

    def _should_show_action(self, action: QuickAction, context: NavigationContext) -> bool:
        """Determine if an action should be shown based on conditions."""
        if not action.conditions:
            return True

        # Check role-based conditions
        if "required_role" in action.conditions:
            if context.user_role not in action.conditions["required_role"]:
                return False

        # Check tab-based conditions
        if "required_tab" in action.conditions:
            if context.current_tab not in action.conditions["required_tab"]:
                return False

        return True

    def _get_dynamic_actions(self, context: NavigationContext) -> List[QuickAction]:
        """Generate dynamic actions based on current context and data."""
        dynamic_actions = []

        # Add actions based on session data
        if context.session_data:
            # Recent items
            if "recent_leads" in context.session_data and context.session_data["recent_leads"]:
                recent_lead = context.session_data["recent_leads"][0]
                dynamic_actions.append(
                    QuickAction(
                        f"Return to {recent_lead.get('name', 'Lead')}",
                        "navigate",
                        f"lead_detail/{recent_lead.get('id')}",
                        "👤",
                        "Return to recently viewed lead",
                        priority=3
                    )
                )

            # Pending tasks
            if "pending_tasks" in context.session_data and context.session_data["pending_tasks"]:
                task_count = len(context.session_data["pending_tasks"])
                dynamic_actions.append(
                    QuickAction(
                        f"Complete {task_count} Tasks",
                        "modal",
                        "task_manager",
                        "✅",
                        f"You have {task_count} pending tasks",
                        priority=2
                    )
                )

        return dynamic_actions

    def _get_hub_icon(self, hub_name: str) -> str:
        """Get icon for hub."""
        hub_icons = {
            "Executive Command Center": "🎯",
            "Lead Intelligence Hub": "🧠",
            "Automation Studio": "⚙️",
            "Sales Copilot": "🤝",
            "Ops & Optimization": "📈"
        }
        return hub_icons.get(hub_name, "📄")

    def record_navigation(self, from_context: str, to_context: str, action_type: str = "click"):
        """Record navigation action for analytics."""
        navigation_event = {
            "timestamp": datetime.now().isoformat(),
            "from": from_context,
            "to": to_context,
            "action_type": action_type,
            "session_id": st.session_state.get("session_id", "unknown")
        }

        self.navigation_history.append(navigation_event)
        self.analytics.record_navigation_event(navigation_event)


class NavigationAnalytics:
    """Analytics service for navigation behavior and optimization."""

    def __init__(self):
        """Initialize navigation analytics."""
        self.events_file = Path("data/navigation_analytics.jsonl")
        self.events_file.parent.mkdir(exist_ok=True, parents=True)

    def record_navigation_event(self, event: Dict[str, Any]):
        """Record navigation event for analysis."""
        try:
            with open(self.events_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            st.error(f"Failed to record navigation event: {e}")

    def get_navigation_insights(self, days: int = 7) -> Dict[str, Any]:
        """Get navigation insights and optimization opportunities."""
        events = self._load_recent_events(days)

        if not events:
            return {"message": "No navigation data available"}

        # Analyze common paths
        path_frequency = {}
        for event in events:
            path = f"{event['from']} -> {event['to']}"
            path_frequency[path] = path_frequency.get(path, 0) + 1

        # Find inefficient navigation patterns
        inefficient_paths = self._identify_inefficient_paths(events)

        # Calculate average clicks to goal
        avg_clicks = self._calculate_average_clicks_to_goal(events)

        return {
            "total_navigation_events": len(events),
            "most_common_paths": sorted(path_frequency.items(), key=lambda x: x[1], reverse=True)[:10],
            "inefficient_paths": inefficient_paths,
            "average_clicks_to_goal": avg_clicks,
            "optimization_suggestions": self._generate_optimization_suggestions(path_frequency, inefficient_paths)
        }

    def _load_recent_events(self, days: int) -> List[Dict[str, Any]]:
        """Load recent navigation events."""
        if not self.events_file.exists():
            return []

        events = []
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)

        try:
            with open(self.events_file, "r") as f:
                for line in f:
                    if line.strip():
                        event = json.loads(line)
                        event_time = datetime.fromisoformat(event["timestamp"]).timestamp()
                        if event_time >= cutoff_date:
                            events.append(event)
        except Exception as e:
            st.error(f"Failed to load navigation events: {e}")

        return events

    def _identify_inefficient_paths(self, events: List[Dict]) -> List[str]:
        """Identify navigation paths that could be optimized."""
        # Look for patterns like: Hub A -> Hub B -> Hub A (back and forth)
        inefficient = []

        sessions = {}
        for event in events:
            session_id = event.get("session_id", "unknown")
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)

        for session_events in sessions.values():
            if len(session_events) >= 3:
                # Look for back-and-forth patterns
                for i in range(len(session_events) - 2):
                    if (session_events[i]["to"] == session_events[i + 2]["from"] and
                        session_events[i]["from"] == session_events[i + 2]["to"]):
                        inefficient.append(f"Back-and-forth: {session_events[i]['from']} ↔ {session_events[i]['to']}")

        return list(set(inefficient))

    def _calculate_average_clicks_to_goal(self, events: List[Dict]) -> float:
        """Calculate average number of clicks to reach common goals."""
        # This is a simplified calculation - in practice, you'd define specific goals
        sessions = {}
        for event in events:
            session_id = event.get("session_id", "unknown")
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)

        click_counts = [len(session) for session in sessions.values() if len(session) > 1]
        return sum(click_counts) / len(click_counts) if click_counts else 0

    def _generate_optimization_suggestions(self, path_frequency: Dict, inefficient_paths: List) -> List[str]:
        """Generate suggestions for navigation optimization."""
        suggestions = []

        # Suggest shortcuts for common paths
        for path, frequency in sorted(path_frequency.items(), key=lambda x: x[1], reverse=True)[:3]:
            if frequency > 10:  # Threshold for suggesting shortcut
                suggestions.append(f"Create shortcut for common path: {path} (used {frequency} times)")

        # Suggest fixes for inefficient patterns
        for pattern in inefficient_paths[:3]:
            suggestions.append(f"Optimize navigation: {pattern}")

        if not suggestions:
            suggestions.append("Navigation patterns are efficient - no major optimizations needed")

        return suggestions


class BreadcrumbComponent:
    """Streamlit component for rendering breadcrumb navigation."""

    @staticmethod
    def render(breadcrumbs: List[Dict[str, str]], context: NavigationContext) -> Optional[str]:
        """Render breadcrumb navigation with click handling."""
        if not breadcrumbs:
            return None

        # Create breadcrumb HTML
        breadcrumb_html = """
        <div style='
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 1rem 0;
            padding: 0.75rem 1rem;
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.2);
            border-radius: 8px;
            font-size: 0.9rem;
        '>
        """

        for i, crumb in enumerate(breadcrumbs):
            # Add separator if not first item
            if i > 0:
                breadcrumb_html += """
                <span style='color: #64748b; margin: 0 0.25rem;'>›</span>
                """

            # Render crumb
            is_current = i == len(breadcrumbs) - 1
            style = (
                "color: #1e293b; font-weight: 600;" if is_current
                else "color: #3b82f6; cursor: pointer; text-decoration: none;"
            )

            breadcrumb_html += f"""
            <span style='{style}'>
                <span style='margin-right: 0.25rem;'>{crumb['icon']}</span>
                {crumb['label']}
            </span>
            """

        breadcrumb_html += "</div>"

        st.markdown(breadcrumb_html, unsafe_allow_html=True)

        # Handle breadcrumb clicks (simplified - in full implementation would use custom component)
        if len(breadcrumbs) > 1:
            with st.expander("Quick Navigation", expanded=False):
                for crumb in breadcrumbs[:-1]:  # Exclude current page
                    if st.button(f"{crumb['icon']} {crumb['label']}", key=f"nav_{crumb['target']}"):
                        return crumb['target']

        return None


class ContextActionsComponent:
    """Streamlit component for rendering context-aware quick actions."""

    @staticmethod
    def render(actions: List[QuickAction], context: NavigationContext) -> Optional[QuickAction]:
        """Render context-aware quick actions."""
        if not actions:
            return None

        st.markdown("### Quick Actions")

        # Group actions by priority
        high_priority = [a for a in actions if a.priority >= 3]
        medium_priority = [a for a in actions if a.priority == 2]
        low_priority = [a for a in actions if a.priority == 1]

        executed_action = None

        # Render high priority actions prominently
        if high_priority:
            cols = st.columns(min(len(high_priority), 3))
            for i, action in enumerate(high_priority[:3]):
                with cols[i]:
                    if st.button(
                        f"{action.icon} {action.label}",
                        help=action.description,
                        use_container_width=True,
                        type="primary" if action.priority >= 3 else "secondary"
                    ):
                        executed_action = action

        # Render medium and low priority in expandable section
        if medium_priority or low_priority:
            with st.expander("More Actions", expanded=False):
                for action in medium_priority + low_priority:
                    if st.button(
                        f"{action.icon} {action.label}",
                        help=action.description,
                        key=f"action_{action.label.replace(' ', '_')}",
                        use_container_width=True
                    ):
                        executed_action = action

        return executed_action


class ProgressiveDisclosureComponent:
    """Component for progressive disclosure of information."""

    @staticmethod
    def render_expandable_section(
        title: str,
        content_func: callable,
        icon: str = "📋",
        expanded: bool = False,
        show_summary: bool = True
    ) -> bool:
        """Render an expandable section with progressive disclosure."""

        # Show summary if requested
        if show_summary and not expanded:
            summary = content_func(summary_mode=True)
            if summary:
                st.markdown(f"""
                <div style='
                    padding: 0.5rem 1rem;
                    background: rgba(59, 130, 246, 0.05);
                    border-left: 3px solid #3b82f6;
                    margin: 0.5rem 0;
                    border-radius: 4px;
                '>
                    <strong>{icon} {title}</strong><br>
                    <small style='color: #64748b;'>{summary}</small>
                </div>
                """, unsafe_allow_html=True)

        # Full content in expander
        with st.expander(f"{icon} {title}", expanded=expanded):
            is_expanded = True
            content_func(summary_mode=False)
            return is_expanded

        return False


def initialize_smart_navigation() -> SmartNavigationService:
    """Initialize smart navigation service in Streamlit session state."""
    if "smart_navigation" not in st.session_state:
        st.session_state.smart_navigation = SmartNavigationService()

        # Initialize session ID for analytics
        if "session_id" not in st.session_state:
            st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    return st.session_state.smart_navigation


def get_current_navigation_context() -> NavigationContext:
    """Get current navigation context from session state."""
    return NavigationContext(
        current_hub=st.session_state.get("current_hub", "Executive Command Center"),
        current_tab=st.session_state.get("current_tab"),
        current_section=st.session_state.get("current_section"),
        user_role=st.session_state.get("user_role", "admin"),
        location_id=st.session_state.get("location_id"),
        last_action=st.session_state.get("last_action"),
        session_data=st.session_state.get("session_data", {})
    )


def render_smart_navigation() -> Dict[str, Any]:
    """Render complete smart navigation system."""
    nav_service = initialize_smart_navigation()
    context = get_current_navigation_context()

    # Get navigation elements
    breadcrumbs = nav_service.get_breadcrumb_trail(context)
    quick_actions = nav_service.get_context_actions(context)

    # Render components
    navigation_result = {"action": None, "target": None}

    # Render breadcrumbs
    selected_crumb = BreadcrumbComponent.render(breadcrumbs, context)
    if selected_crumb:
        navigation_result["action"] = "navigate"
        navigation_result["target"] = selected_crumb
        nav_service.record_navigation(context.current_hub, selected_crumb, "breadcrumb")

    # Render quick actions
    executed_action = ContextActionsComponent.render(quick_actions, context)
    if executed_action:
        navigation_result["action"] = executed_action.action_type
        navigation_result["target"] = executed_action.target
        nav_service.record_navigation(context.current_hub, executed_action.target, "quick_action")

    return navigation_result


# Export main components
__all__ = [
    "SmartNavigationService",
    "NavigationContext",
    "QuickAction",
    "BreadcrumbComponent",
    "ContextActionsComponent",
    "ProgressiveDisclosureComponent",
    "initialize_smart_navigation",
    "get_current_navigation_context",
    "render_smart_navigation"
]