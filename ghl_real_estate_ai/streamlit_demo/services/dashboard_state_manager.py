"""
Dashboard State Manager for GHL Real Estate AI

Manages user preferences, saved views, filters, and dashboard customization.
Provides persistent storage and intelligent defaults.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import streamlit as st

@dataclass
class DashboardView:
    """Represents a saved dashboard view configuration"""
    id: str
    name: str
    description: str
    config: Dict[str, Any]
    created_at: datetime
    last_used: datetime
    is_default: bool = False
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            'created_at': self.created_at.isoformat(),
            'last_used': self.last_used.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardView':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_used'] = datetime.fromisoformat(data['last_used'])
        return cls(**data)

@dataclass
class UserPreferences:
    """User dashboard preferences"""
    theme: str = 'light'  # light, dark, auto
    auto_refresh: bool = True
    refresh_interval: int = 2  # seconds
    notifications_enabled: bool = True
    sound_alerts: bool = False
    mobile_optimized: bool = True
    compact_view: bool = False
    show_animations: bool = True
    default_time_range: str = '24h'  # 1h, 6h, 24h, 7d, 30d
    timezone: str = 'UTC'

class ViewType(Enum):
    """Types of dashboard views"""
    OVERVIEW = "overview"
    LEADS = "leads"
    ANALYTICS = "analytics"
    PERFORMANCE = "performance"
    ALERTS = "alerts"
    CUSTOM = "custom"

class DashboardStateManager:
    """
    Production-grade dashboard state management with:
    - User preference persistence
    - Saved view management
    - Filter state tracking
    - Mobile optimization
    - Performance monitoring
    """

    def __init__(self, user_id: Optional[str] = None, storage_path: Optional[str] = None):
        self.user_id = user_id or "default_user"
        self.storage_path = Path(storage_path or "data/dashboard_state")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # State tracking
        self.current_view: Optional[DashboardView] = None
        self.active_filters: Dict[str, Any] = {}
        self.user_preferences: UserPreferences = UserPreferences()
        self.saved_views: Dict[str, DashboardView] = {}

        # Performance tracking
        self.state_changes: List[Dict[str, Any]] = []
        self.last_save_time: Optional[datetime] = None

        # Initialize from storage
        self._load_state()

        # Initialize session state
        self._init_session_state()

    def _init_session_state(self):
        """Initialize Streamlit session state"""
        if 'dashboard_state_manager' not in st.session_state:
            st.session_state.dashboard_state_manager = self

        if 'dashboard_filters' not in st.session_state:
            st.session_state.dashboard_filters = {}

        if 'dashboard_preferences' not in st.session_state:
            st.session_state.dashboard_preferences = asdict(self.user_preferences)

    def _get_user_file(self) -> Path:
        """Get user-specific state file path"""
        return self.storage_path / f"user_{self.user_id}.json"

    def _load_state(self):
        """Load user state from storage"""
        user_file = self._get_user_file()

        if user_file.exists():
            try:
                with open(user_file, 'r') as f:
                    data = json.load(f)

                # Load preferences
                if 'preferences' in data:
                    prefs_dict = data['preferences']
                    self.user_preferences = UserPreferences(**prefs_dict)

                # Load saved views
                if 'saved_views' in data:
                    for view_id, view_data in data['saved_views'].items():
                        self.saved_views[view_id] = DashboardView.from_dict(view_data)

                # Load current view
                if 'current_view_id' in data and data['current_view_id'] in self.saved_views:
                    self.current_view = self.saved_views[data['current_view_id']]

                # Load active filters
                if 'active_filters' in data:
                    self.active_filters = data['active_filters']

                self.last_save_time = datetime.now()

            except Exception as e:
                print(f"Error loading dashboard state: {e}")
                self._create_default_state()
        else:
            self._create_default_state()

    def _create_default_state(self):
        """Create default dashboard state"""
        # Create default views
        default_views = [
            DashboardView(
                id="overview",
                name="Executive Overview",
                description="High-level KPIs and real-time metrics",
                config={
                    "layout": "grid",
                    "components": ["lead_scoreboard", "alert_center", "performance_summary"],
                    "time_range": "24h",
                    "auto_refresh": True
                },
                created_at=datetime.now(),
                last_used=datetime.now(),
                is_default=True,
                tags=["executive", "kpi", "overview"]
            ),
            DashboardView(
                id="leads_focus",
                name="Lead Management Focus",
                description="Detailed lead scoring and pipeline view",
                config={
                    "layout": "columns",
                    "components": ["lead_scoreboard", "lead_analytics", "conversion_funnel"],
                    "time_range": "7d",
                    "filters": {"status": ["hot", "warm"]}
                },
                created_at=datetime.now(),
                last_used=datetime.now(),
                tags=["leads", "sales", "pipeline"]
            ),
            DashboardView(
                id="analytics_deep",
                name="Analytics Deep Dive",
                description="Comprehensive analytics with drill-down capability",
                config={
                    "layout": "dashboard",
                    "components": ["interactive_analytics", "performance_trends", "forecast"],
                    "time_range": "30d",
                    "chart_types": ["line", "bar", "funnel"]
                },
                created_at=datetime.now(),
                last_used=datetime.now(),
                tags=["analytics", "reporting", "trends"]
            )
        ]

        for view in default_views:
            self.saved_views[view.id] = view

        # Set first view as current
        self.current_view = default_views[0]

        # Save default state
        self._save_state()

    def _save_state(self):
        """Save current state to storage"""
        user_file = self._get_user_file()

        try:
            data = {
                "user_id": self.user_id,
                "preferences": asdict(self.user_preferences),
                "saved_views": {
                    view_id: view.to_dict()
                    for view_id, view in self.saved_views.items()
                },
                "current_view_id": self.current_view.id if self.current_view else None,
                "active_filters": self.active_filters,
                "last_updated": datetime.now().isoformat()
            }

            with open(user_file, 'w') as f:
                json.dump(data, f, indent=2)

            self.last_save_time = datetime.now()

        except Exception as e:
            print(f"Error saving dashboard state: {e}")

    def get_preferences(self) -> UserPreferences:
        """Get user preferences"""
        return self.user_preferences

    def update_preferences(self, **kwargs) -> bool:
        """Update user preferences"""
        try:
            for key, value in kwargs.items():
                if hasattr(self.user_preferences, key):
                    setattr(self.user_preferences, key, value)

            self._track_state_change("preferences_updated", kwargs)
            self._save_state()

            # Update session state
            st.session_state.dashboard_preferences = asdict(self.user_preferences)

            return True

        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False

    def get_current_view(self) -> Optional[DashboardView]:
        """Get current active view"""
        return self.current_view

    def set_current_view(self, view_id: str) -> bool:
        """Set current active view"""
        if view_id in self.saved_views:
            self.current_view = self.saved_views[view_id]
            self.current_view.last_used = datetime.now()

            self._track_state_change("view_changed", {"view_id": view_id})
            self._save_state()

            return True

        return False

    def get_saved_views(self, view_type: Optional[ViewType] = None) -> List[DashboardView]:
        """Get all saved views, optionally filtered by type"""
        views = list(self.saved_views.values())

        if view_type:
            views = [v for v in views if view_type.value in v.tags]

        # Sort by last used (most recent first)
        return sorted(views, key=lambda x: x.last_used, reverse=True)

    def save_view(self, view: DashboardView) -> bool:
        """Save a dashboard view"""
        try:
            view.created_at = datetime.now()
            view.last_used = datetime.now()
            self.saved_views[view.id] = view

            self._track_state_change("view_saved", {"view_id": view.id, "name": view.name})
            self._save_state()

            return True

        except Exception as e:
            print(f"Error saving view: {e}")
            return False

    def delete_view(self, view_id: str) -> bool:
        """Delete a saved view"""
        if view_id in self.saved_views:
            # Don't allow deleting the current view if it's the only one
            if len(self.saved_views) == 1:
                return False

            # If deleting current view, switch to another
            if self.current_view and self.current_view.id == view_id:
                remaining_views = [v for v in self.saved_views.values() if v.id != view_id]
                if remaining_views:
                    self.current_view = remaining_views[0]

            del self.saved_views[view_id]

            self._track_state_change("view_deleted", {"view_id": view_id})
            self._save_state()

            return True

        return False

    def get_active_filters(self) -> Dict[str, Any]:
        """Get current active filters"""
        return self.active_filters.copy()

    def set_filter(self, filter_name: str, value: Any) -> bool:
        """Set a filter value"""
        try:
            self.active_filters[filter_name] = value

            # Update session state
            if 'dashboard_filters' in st.session_state:
                st.session_state.dashboard_filters[filter_name] = value

            self._track_state_change("filter_set", {"filter": filter_name, "value": value})
            return True

        except Exception as e:
            print(f"Error setting filter: {e}")
            return False

    def remove_filter(self, filter_name: str) -> bool:
        """Remove a filter"""
        if filter_name in self.active_filters:
            del self.active_filters[filter_name]

            # Update session state
            if 'dashboard_filters' in st.session_state and filter_name in st.session_state.dashboard_filters:
                del st.session_state.dashboard_filters[filter_name]

            self._track_state_change("filter_removed", {"filter": filter_name})
            return True

        return False

    def clear_all_filters(self):
        """Clear all active filters"""
        self.active_filters.clear()

        # Update session state
        if 'dashboard_filters' in st.session_state:
            st.session_state.dashboard_filters.clear()

        self._track_state_change("filters_cleared", {})

    def create_view_from_current_state(self, name: str, description: str = "", tags: List[str] = None) -> str:
        """Create a new view from current dashboard state"""
        import uuid

        view_id = str(uuid.uuid4())
        tags = tags or []

        current_config = {
            "filters": self.active_filters.copy(),
            "preferences": asdict(self.user_preferences),
            "timestamp": datetime.now().isoformat()
        }

        view = DashboardView(
            id=view_id,
            name=name,
            description=description,
            config=current_config,
            created_at=datetime.now(),
            last_used=datetime.now(),
            tags=tags
        )

        self.save_view(view)
        return view_id

    def get_layout_config(self) -> Dict[str, Any]:
        """Get layout configuration for current view"""
        if not self.current_view:
            return self._get_default_layout()

        return self.current_view.config.get("layout_config", self._get_default_layout())

    def _get_default_layout(self) -> Dict[str, Any]:
        """Get default layout configuration"""
        return {
            "grid_columns": 3 if not self.user_preferences.compact_view else 2,
            "component_height": 400,
            "gap": 16,
            "mobile_columns": 1,
            "tablet_columns": 2,
            "responsive_breakpoints": {
                "mobile": 768,
                "tablet": 1024
            }
        }

    def _track_state_change(self, action: str, details: Dict[str, Any]):
        """Track state changes for analytics"""
        self.state_changes.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "user_id": self.user_id
        })

        # Keep only last 100 changes
        if len(self.state_changes) > 100:
            self.state_changes = self.state_changes[-100:]

    def get_usage_analytics(self) -> Dict[str, Any]:
        """Get dashboard usage analytics"""
        now = datetime.now()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        recent_changes = [
            change for change in self.state_changes
            if datetime.fromisoformat(change['timestamp']) > day_ago
        ]

        return {
            "total_state_changes": len(self.state_changes),
            "changes_last_24h": len(recent_changes),
            "most_used_view": self._get_most_used_view(),
            "most_used_filters": self._get_most_used_filters(),
            "session_duration": (now - (self.last_save_time or now)).total_seconds(),
            "preferences": asdict(self.user_preferences),
            "total_saved_views": len(self.saved_views)
        }

    def _get_most_used_view(self) -> Optional[str]:
        """Get most frequently used view"""
        if not self.saved_views:
            return None

        return max(self.saved_views.values(), key=lambda x: x.last_used).name

    def _get_most_used_filters(self) -> List[str]:
        """Get most frequently used filters"""
        filter_counts = {}

        for change in self.state_changes:
            if change['action'] == 'filter_set':
                filter_name = change['details'].get('filter')
                if filter_name:
                    filter_counts[filter_name] = filter_counts.get(filter_name, 0) + 1

        return sorted(filter_counts.keys(), key=lambda x: filter_counts[x], reverse=True)[:5]

    def export_state(self) -> Dict[str, Any]:
        """Export complete dashboard state for backup/migration"""
        return {
            "user_id": self.user_id,
            "preferences": asdict(self.user_preferences),
            "saved_views": {view_id: view.to_dict() for view_id, view in self.saved_views.items()},
            "current_view_id": self.current_view.id if self.current_view else None,
            "active_filters": self.active_filters,
            "state_changes": self.state_changes,
            "export_timestamp": datetime.now().isoformat(),
            "version": "1.0"
        }

    def import_state(self, state_data: Dict[str, Any]) -> bool:
        """Import dashboard state from backup/migration"""
        try:
            # Validate version compatibility
            if state_data.get("version", "0.0") != "1.0":
                print("Warning: Importing state from different version")

            # Import preferences
            if "preferences" in state_data:
                self.user_preferences = UserPreferences(**state_data["preferences"])

            # Import saved views
            if "saved_views" in state_data:
                for view_id, view_data in state_data["saved_views"].items():
                    self.saved_views[view_id] = DashboardView.from_dict(view_data)

            # Import active filters
            if "active_filters" in state_data:
                self.active_filters = state_data["active_filters"]

            # Set current view
            if "current_view_id" in state_data and state_data["current_view_id"] in self.saved_views:
                self.current_view = self.saved_views[state_data["current_view_id"]]

            # Import state changes (limited)
            if "state_changes" in state_data:
                self.state_changes = state_data["state_changes"][-50:]  # Keep only last 50

            self._save_state()
            return True

        except Exception as e:
            print(f"Error importing dashboard state: {e}")
            return False


# Singleton instance for global access
_state_manager_instance = None

def get_dashboard_state_manager(user_id: Optional[str] = None) -> DashboardStateManager:
    """Get or create singleton dashboard state manager"""
    global _state_manager_instance

    if _state_manager_instance is None:
        _state_manager_instance = DashboardStateManager(user_id)

    return _state_manager_instance


# Streamlit integration helpers
def dashboard_sidebar_controls():
    """Render dashboard control sidebar"""
    state_manager = get_dashboard_state_manager()

    st.sidebar.markdown("### 🎛️ Dashboard Controls")

    # View selector
    views = state_manager.get_saved_views()
    view_names = [f"{view.name} {'⭐' if view.is_default else ''}" for view in views]
    current_index = 0

    if state_manager.current_view:
        for i, view in enumerate(views):
            if view.id == state_manager.current_view.id:
                current_index = i
                break

    selected_view = st.sidebar.selectbox(
        "Select View",
        range(len(view_names)),
        index=current_index,
        format_func=lambda x: view_names[x],
        key="dashboard_view_selector"
    )

    if selected_view != current_index:
        state_manager.set_current_view(views[selected_view].id)
        st.rerun()

    # Quick preferences
    st.sidebar.markdown("### ⚙️ Quick Settings")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        auto_refresh = st.checkbox(
            "Auto Refresh",
            value=state_manager.user_preferences.auto_refresh,
            key="auto_refresh_toggle"
        )

    with col2:
        notifications = st.checkbox(
            "Notifications",
            value=state_manager.user_preferences.notifications_enabled,
            key="notifications_toggle"
        )

    # Update preferences if changed
    if auto_refresh != state_manager.user_preferences.auto_refresh:
        state_manager.update_preferences(auto_refresh=auto_refresh)

    if notifications != state_manager.user_preferences.notifications_enabled:
        state_manager.update_preferences(notifications_enabled=notifications)

    # Refresh interval
    refresh_interval = st.sidebar.slider(
        "Refresh Rate (seconds)",
        min_value=1,
        max_value=30,
        value=state_manager.user_preferences.refresh_interval,
        key="refresh_interval_slider"
    )

    if refresh_interval != state_manager.user_preferences.refresh_interval:
        state_manager.update_preferences(refresh_interval=refresh_interval)

    return state_manager