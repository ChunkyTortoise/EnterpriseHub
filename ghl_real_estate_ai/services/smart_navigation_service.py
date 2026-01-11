"""
Smart Navigation System with Breadcrumbs and Context-Aware Actions

Provides intelligent navigation enhancement for the GHL Real Estate AI platform:
- Breadcrumb trail navigation with context preservation
- Context-aware quick actions based on current location
- Progressive disclosure for complex dashboards
- Navigation state management and history tracking
- Role-based navigation optimization

Integrates seamlessly with existing Streamlit interface while adding
enterprise-grade navigation capabilities.
"""

import streamlit as st
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class NavigationItem:
    """Individual navigation item with context."""

    id: str
    label: str
    icon: str = ""
    description: str = ""
    parent_id: Optional[str] = None
    url: Optional[str] = None
    is_active: bool = False
    access_level: str = "all"  # "admin", "user", "all"
    quick_actions: List[str] = None

    def __post_init__(self):
        if self.quick_actions is None:
            self.quick_actions = []


@dataclass
class BreadcrumbItem:
    """Breadcrumb navigation item."""

    label: str
    navigation_id: str
    icon: str = ""
    is_clickable: bool = True


@dataclass
class ContextualAction:
    """Context-aware quick action."""

    id: str
    label: str
    icon: str
    description: str
    action_type: str  # "navigation", "function", "modal", "export"
    target: str  # Target page, function, or modal
    params: Dict[str, Any] = None
    condition: Optional[str] = None  # Condition when action is available

    def __post_init__(self):
        if self.params is None:
            self.params = {}


class NavigationState:
    """Navigation state management."""

    def __init__(self):
        # Initialize session state keys if they don't exist
        if "nav_history" not in st.session_state:
            st.session_state.nav_history = []

        if "nav_current" not in st.session_state:
            st.session_state.nav_current = "executive"

        if "nav_context" not in st.session_state:
            st.session_state.nav_context = {}

        if "nav_breadcrumbs" not in st.session_state:
            st.session_state.nav_breadcrumbs = []

    def navigate_to(self, navigation_id: str, context: Dict[str, Any] = None):
        """Navigate to a specific location with context."""
        if context is None:
            context = {}

        # Add current location to history if different
        if st.session_state.nav_current != navigation_id:
            if st.session_state.nav_current not in st.session_state.nav_history:
                st.session_state.nav_history.append(st.session_state.nav_current)

        # Update current state
        st.session_state.nav_current = navigation_id
        st.session_state.nav_context = context

        # Update breadcrumbs
        self._update_breadcrumbs(navigation_id)

        logger.debug(f"Navigated to: {navigation_id} with context: {context}")

    def go_back(self):
        """Navigate back to previous location."""
        if st.session_state.nav_history:
            previous_location = st.session_state.nav_history.pop()
            st.session_state.nav_current = previous_location
            self._update_breadcrumbs(previous_location)

    def _update_breadcrumbs(self, current_id: str):
        """Update breadcrumb trail based on current location."""
        # This would be populated from the navigation hierarchy
        breadcrumbs = self._build_breadcrumb_trail(current_id)
        st.session_state.nav_breadcrumbs = breadcrumbs

    def _build_breadcrumb_trail(self, current_id: str) -> List[BreadcrumbItem]:
        """Build breadcrumb trail for current location."""
        # Navigation hierarchy mapping
        hierarchy = self._get_navigation_hierarchy()

        trail = []

        # Find current item and build trail
        current_item = hierarchy.get(current_id)
        if current_item:
            trail = self._build_trail_recursive(current_item, hierarchy, [])

        return trail

    def _build_trail_recursive(self, item: NavigationItem, hierarchy: Dict, trail: List) -> List[BreadcrumbItem]:
        """Recursively build breadcrumb trail."""
        # Add current item to front of trail
        breadcrumb = BreadcrumbItem(
            label=item.label,
            navigation_id=item.id,
            icon=item.icon,
            is_clickable=True
        )
        trail.insert(0, breadcrumb)

        # If has parent, continue recursively
        if item.parent_id and item.parent_id in hierarchy:
            parent_item = hierarchy[item.parent_id]
            return self._build_trail_recursive(parent_item, hierarchy, trail)

        return trail

    def _get_navigation_hierarchy(self) -> Dict[str, NavigationItem]:
        """Get the navigation hierarchy structure."""
        return {
            "root": NavigationItem(
                id="root",
                label="GHL Real Estate AI",
                icon="🏠",
                description="Main Platform"
            ),
            "executive": NavigationItem(
                id="executive",
                label="Executive Command Center",
                icon="📊",
                parent_id="root",
                description="High-level business insights and KPIs",
                quick_actions=["export_executive_report", "schedule_review", "alert_settings"]
            ),
            "executive_revenue": NavigationItem(
                id="executive_revenue",
                label="Revenue Analytics",
                icon="💰",
                parent_id="executive",
                description="Revenue performance and forecasting"
            ),
            "executive_insights": NavigationItem(
                id="executive_insights",
                label="AI Insights",
                icon="🧠",
                parent_id="executive",
                description="AI-powered business intelligence"
            ),
            "executive_actions": NavigationItem(
                id="executive_actions",
                label="Action Items",
                icon="✅",
                parent_id="executive",
                description="Executive action items and priorities"
            ),
            "leads": NavigationItem(
                id="leads",
                label="Lead Intelligence Hub",
                icon="🎯",
                parent_id="root",
                description="Deep lead analysis and management",
                quick_actions=["score_leads", "segment_leads", "export_leads"]
            ),
            "leads_scoring": NavigationItem(
                id="leads_scoring",
                label="Lead Scoring",
                icon="📈",
                parent_id="leads",
                description="AI-powered lead scoring and prioritization"
            ),
            "leads_churn": NavigationItem(
                id="leads_churn",
                label="Churn Risk Analysis",
                icon="⚠️",
                parent_id="leads",
                description="Predict and prevent lead churn"
            ),
            "automation": NavigationItem(
                id="automation",
                label="Automation Studio",
                icon="🤖",
                parent_id="root",
                description="Workflow automation and optimization",
                quick_actions=["create_workflow", "test_automation", "deploy_workflow"]
            ),
            "sales": NavigationItem(
                id="sales",
                label="Sales Copilot",
                icon="💼",
                parent_id="root",
                description="AI-powered sales assistance and coaching",
                quick_actions=["get_coaching", "review_calls", "update_pipeline"]
            ),
            "operations": NavigationItem(
                id="operations",
                label="Ops & Optimization",
                icon="⚙️",
                parent_id="root",
                description="Operations management and system optimization",
                quick_actions=["system_health", "performance_metrics", "optimize_workflows"]
            )
        }


class SmartNavigationService:
    """
    Smart Navigation Service with enterprise-grade capabilities.

    Provides:
    - Breadcrumb navigation with context preservation
    - Context-aware quick actions
    - Progressive disclosure management
    - Navigation analytics and optimization
    """

    def __init__(self):
        self.nav_state = NavigationState()
        self.contextual_actions = self._initialize_contextual_actions()

    def render_breadcrumb_navigation(self):
        """Render breadcrumb navigation component."""
        if not st.session_state.nav_breadcrumbs:
            return

        # Create breadcrumb container
        breadcrumb_html = """
        <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                    padding: 0.75rem 1.5rem;
                    border-radius: 12px;
                    border: 1px solid rgba(59, 130, 246, 0.2);
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    font-family: system-ui, -apple-system, sans-serif;'>
        """

        breadcrumbs = st.session_state.nav_breadcrumbs

        for i, breadcrumb in enumerate(breadcrumbs):
            # Add separator except for first item
            if i > 0:
                breadcrumb_html += """
                <span style='color: #64748b; margin: 0 0.25rem;'>›</span>
                """

            # Add breadcrumb item
            if breadcrumb.is_clickable and i < len(breadcrumbs) - 1:
                breadcrumb_html += f"""
                <span style='color: #93c5fd; cursor: pointer; text-decoration: none;
                           display: flex; align-items: center; gap: 0.25rem;
                           padding: 0.25rem 0.5rem; border-radius: 6px;
                           transition: background-color 0.2s;'
                      onmouseover='this.style.backgroundColor="rgba(59, 130, 246, 0.1)"'
                      onmouseout='this.style.backgroundColor="transparent"'
                      onclick='navigateTo("{breadcrumb.navigation_id}")'>
                    {breadcrumb.icon} {breadcrumb.label}
                </span>
                """
            else:
                # Current page (not clickable)
                breadcrumb_html += f"""
                <span style='color: #f8fafc; font-weight: 600;
                           display: flex; align-items: center; gap: 0.25rem;
                           padding: 0.25rem 0.5rem; border-radius: 6px;
                           background: rgba(59, 130, 246, 0.15);'>
                    {breadcrumb.icon} {breadcrumb.label}
                </span>
                """

        breadcrumb_html += "</div>"

        st.markdown(breadcrumb_html, unsafe_allow_html=True)

    def render_context_aware_actions(self, current_location: str):
        """Render context-aware quick actions based on current location."""
        # Get actions for current context
        actions = self._get_actions_for_location(current_location)

        if not actions:
            return

        st.markdown("#### Quick Actions")

        # Create action buttons
        cols = st.columns(min(len(actions), 4))  # Max 4 columns

        for i, action in enumerate(actions[:4]):  # Show max 4 quick actions
            col_index = i % 4
            with cols[col_index]:
                if st.button(
                    f"{action.icon} {action.label}",
                    help=action.description,
                    key=f"action_{action.id}",
                    use_container_width=True
                ):
                    self._execute_contextual_action(action)

    def render_progressive_disclosure_container(self, title: str, content_sections: List[Dict[str, Any]]):
        """
        Render progressive disclosure container for complex dashboards.

        Args:
            title: Container title
            content_sections: List of content sections with expand/collapse functionality
        """
        with st.expander(title, expanded=True):
            for section in content_sections:
                section_id = section.get("id", "section")
                section_title = section.get("title", "Section")
                section_content = section.get("content")
                is_expanded = section.get("expanded", False)

                # Create collapsible section
                with st.expander(section_title, expanded=is_expanded):
                    if callable(section_content):
                        section_content()
                    else:
                        st.write(section_content)

    def update_navigation_context(self, location_id: str, **context):
        """Update navigation context for current location."""
        self.nav_state.navigate_to(location_id, context)

    def get_current_location(self) -> str:
        """Get current navigation location."""
        return st.session_state.nav_current

    def get_navigation_context(self) -> Dict[str, Any]:
        """Get current navigation context."""
        return st.session_state.nav_context

    def _get_actions_for_location(self, location: str) -> List[ContextualAction]:
        """Get contextual actions for a specific location."""
        return [
            action for action in self.contextual_actions
            if self._is_action_available(action, location)
        ]

    def _is_action_available(self, action: ContextualAction, location: str) -> bool:
        """Check if action is available for current location and context."""
        # Basic location matching
        if action.condition:
            # Simple condition evaluation (could be expanded)
            if location not in action.condition:
                return False

        # Check if action is relevant for current location
        location_actions = {
            "executive": ["export_executive_report", "schedule_review", "refresh_data"],
            "leads": ["score_leads", "segment_leads", "export_leads", "bulk_actions"],
            "automation": ["create_workflow", "test_automation", "deploy_workflow"],
            "sales": ["get_coaching", "review_calls", "update_pipeline"],
            "operations": ["system_health", "performance_metrics", "optimize_workflows"]
        }

        relevant_actions = location_actions.get(location, [])
        return action.id in relevant_actions

    def _execute_contextual_action(self, action: ContextualAction):
        """Execute a contextual action."""
        try:
            if action.action_type == "navigation":
                self.nav_state.navigate_to(action.target, action.params)
                st.rerun()

            elif action.action_type == "function":
                # Execute function (this would integrate with actual service methods)
                st.success(f"Executed: {action.label}")
                logger.info(f"Executed contextual action: {action.id}")

            elif action.action_type == "export":
                # Handle export actions
                st.success(f"Export initiated: {action.label}")
                logger.info(f"Export action triggered: {action.id}")

            elif action.action_type == "modal":
                # Handle modal actions
                st.info(f"Modal would open: {action.label}")
                logger.info(f"Modal action triggered: {action.id}")

        except Exception as e:
            st.error(f"Failed to execute action: {action.label}")
            logger.error(f"Action execution failed: {e}")

    def _initialize_contextual_actions(self) -> List[ContextualAction]:
        """Initialize available contextual actions."""
        return [
            # Executive actions
            ContextualAction(
                id="export_executive_report",
                label="Export Report",
                icon="📊",
                description="Export executive dashboard as PDF",
                action_type="export",
                target="executive_report.pdf",
                condition="executive"
            ),
            ContextualAction(
                id="schedule_review",
                label="Schedule Review",
                icon="📅",
                description="Schedule executive review meeting",
                action_type="modal",
                target="schedule_modal",
                condition="executive"
            ),
            ContextualAction(
                id="refresh_data",
                label="Refresh Data",
                icon="🔄",
                description="Refresh all analytics data",
                action_type="function",
                target="refresh_analytics"
            ),

            # Lead management actions
            ContextualAction(
                id="score_leads",
                label="Score Leads",
                icon="🎯",
                description="Run AI lead scoring on new leads",
                action_type="function",
                target="score_new_leads",
                condition="leads"
            ),
            ContextualAction(
                id="segment_leads",
                label="Segment Leads",
                icon="📋",
                description="Create smart lead segments",
                action_type="function",
                target="create_segments",
                condition="leads"
            ),
            ContextualAction(
                id="export_leads",
                label="Export Leads",
                icon="📤",
                description="Export lead data to CSV",
                action_type="export",
                target="leads.csv",
                condition="leads"
            ),
            ContextualAction(
                id="bulk_actions",
                label="Bulk Actions",
                icon="⚡",
                description="Perform bulk operations on leads",
                action_type="modal",
                target="bulk_modal",
                condition="leads"
            ),

            # Automation actions
            ContextualAction(
                id="create_workflow",
                label="New Workflow",
                icon="➕",
                description="Create new automation workflow",
                action_type="modal",
                target="workflow_builder",
                condition="automation"
            ),
            ContextualAction(
                id="test_automation",
                label="Test Workflow",
                icon="🧪",
                description="Test automation workflow",
                action_type="function",
                target="test_workflow",
                condition="automation"
            ),

            # Sales actions
            ContextualAction(
                id="get_coaching",
                label="Get Coaching",
                icon="🎓",
                description="Get AI coaching suggestions",
                action_type="function",
                target="ai_coaching",
                condition="sales"
            ),
            ContextualAction(
                id="review_calls",
                label="Review Calls",
                icon="📞",
                description="Review recent sales calls",
                action_type="navigation",
                target="sales_calls",
                condition="sales"
            ),

            # Operations actions
            ContextualAction(
                id="system_health",
                label="System Health",
                icon="💚",
                description="Check system health metrics",
                action_type="function",
                target="health_check",
                condition="operations"
            ),
            ContextualAction(
                id="performance_metrics",
                label="Performance",
                icon="📈",
                description="View performance metrics",
                action_type="navigation",
                target="performance_dashboard",
                condition="operations"
            )
        ]


# Helper functions for easy integration
def initialize_smart_navigation():
    """Initialize smart navigation service in session state."""
    if "smart_nav" not in st.session_state:
        st.session_state.smart_nav = SmartNavigationService()
    return st.session_state.smart_nav

def render_smart_breadcrumbs():
    """Render smart breadcrumb navigation."""
    nav_service = initialize_smart_navigation()
    nav_service.render_breadcrumb_navigation()

def render_contextual_actions(location: str = None):
    """Render context-aware quick actions."""
    nav_service = initialize_smart_navigation()
    if location is None:
        location = nav_service.get_current_location()
    nav_service.render_context_aware_actions(location)

def update_nav_context(location: str, **context):
    """Update navigation context."""
    nav_service = initialize_smart_navigation()
    nav_service.update_navigation_context(location, **context)


# Export main components
__all__ = [
    "SmartNavigationService",
    "NavigationItem",
    "BreadcrumbItem",
    "ContextualAction",
    "initialize_smart_navigation",
    "render_smart_breadcrumbs",
    "render_contextual_actions",
    "update_nav_context"
]