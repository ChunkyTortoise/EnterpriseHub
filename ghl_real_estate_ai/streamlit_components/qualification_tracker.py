"""
Qualification Tracking with Progress Visualization

Advanced qualification tracking system that provides visual progress indicators,
interactive checklists, milestone tracking, and gamification elements to help
agents systematically gather all required information from leads.

Features:
- Visual progress tracking with multiple chart types
- Interactive qualification checklists
- Milestone and achievement tracking
- Real-time progress updates
- Qualification scoring and recommendations
- Export capabilities for reporting
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider replacing inline styled divs with enterprise_card
# - Consider using enterprise_metric for consistent styling
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import json

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

# Local imports
from models.evaluation_models import (
    QualificationProgress,
    QualificationField,
    QualificationStatus,
    LeadEvaluationResult
)


class QualificationCategory(str, Enum):
    """Categories for qualification fields."""
    FINANCIAL = "financial"
    PERSONAL = "personal"
    PROPERTY = "property"
    TIMELINE = "timeline"
    MOTIVATION = "motivation"


class QualificationPriority(str, Enum):
    """Priority levels for qualification fields."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


@dataclass
class QualificationField:
    """Extended qualification field with visualization data."""
    name: str
    display_name: str
    category: QualificationCategory
    priority: QualificationPriority
    status: QualificationStatus
    value: Optional[str] = None
    confidence: float = 0.0
    source: str = "unknown"
    last_updated: Optional[datetime] = None
    attempts: int = 0
    notes: List[str] = None
    required: bool = True
    validation_pattern: Optional[str] = None
    help_text: Optional[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []
        if self.last_updated is None:
            self.last_updated = datetime.now()


@dataclass
class QualificationMilestone:
    """Qualification milestone for tracking progress."""
    name: str
    description: str
    required_fields: List[str]
    reward_points: int
    icon: str
    achieved: bool = False
    achieved_at: Optional[datetime] = None


class QualificationTracker(EnterpriseDashboardComponent):
    """
    Advanced qualification tracking system with comprehensive visualization
    and progress management capabilities.
    """

    def __init__(self):
        """Initialize qualification tracker."""
        self.color_scheme = {
            'completed': '#10B981',  # Green
            'partial': '#F59E0B',    # Amber
            'missing': '#EF4444',    # Red
            'critical': '#7C3AED',   # Purple
            'background': '#F8FAFC', # Light gray
            'primary': '#3B82F6',    # Blue
            'accent': '#8B5CF6'      # Purple
        }

        # Initialize session state
        self._init_session_state()

        # Load qualification framework
        self.qualification_fields = self._load_qualification_fields()
        self.milestones = self._load_qualification_milestones()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state for qualification tracking."""
        defaults = {
            "qualification_data": {},
            "qualification_progress": 0.0,
            "qualification_score": 0,
            "achieved_milestones": [],
            "qualification_notes": [],
            "qualification_filter": "all",
            "show_help_text": True,
            "gamification_enabled": True,
            "auto_save": True
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    def _load_qualification_fields(self) -> List[QualificationField]:
        """Load qualification fields configuration."""
        # Define comprehensive qualification framework
        fields = [
            # Financial Category
            QualificationField(
                name="budget",
                display_name="Budget Range",
                category=QualificationCategory.FINANCIAL,
                priority=QualificationPriority.CRITICAL,
                status=QualificationStatus.MISSING,
                required=True,
                validation_pattern=r"\$?[\d,]+\s*-?\s*\$?[\d,]*",
                help_text="Lead's maximum purchase budget or price range"
            ),
            QualificationField(
                name="financing_status",
                display_name="Financing Status",
                category=QualificationCategory.FINANCIAL,
                priority=QualificationPriority.HIGH,
                status=QualificationStatus.MISSING,
                required=True,
                help_text="Pre-approval status, cash buyer, or financing needs"
            ),
            QualificationField(
                name="down_payment",
                display_name="Down Payment",
                category=QualificationCategory.FINANCIAL,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Available down payment amount"
            ),

            # Timeline Category
            QualificationField(
                name="purchase_timeline",
                display_name="Purchase Timeline",
                category=QualificationCategory.TIMELINE,
                priority=QualificationPriority.CRITICAL,
                status=QualificationStatus.MISSING,
                required=True,
                help_text="When they want to complete the purchase"
            ),
            QualificationField(
                name="move_in_date",
                display_name="Desired Move-in Date",
                category=QualificationCategory.TIMELINE,
                priority=QualificationPriority.HIGH,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="When they need to move into the property"
            ),

            # Property Category
            QualificationField(
                name="property_type",
                display_name="Property Type",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.CRITICAL,
                status=QualificationStatus.MISSING,
                required=True,
                help_text="House, condo, townhome, etc."
            ),
            QualificationField(
                name="location_preference",
                display_name="Location/Area",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.CRITICAL,
                status=QualificationStatus.MISSING,
                required=True,
                help_text="Preferred neighborhoods, areas, or proximity requirements"
            ),
            QualificationField(
                name="bedrooms",
                display_name="Bedrooms",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.HIGH,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Number of bedrooms needed"
            ),
            QualificationField(
                name="bathrooms",
                display_name="Bathrooms",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Number of bathrooms needed"
            ),
            QualificationField(
                name="square_footage",
                display_name="Square Footage",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Desired square footage range"
            ),
            QualificationField(
                name="special_features",
                display_name="Special Features",
                category=QualificationCategory.PROPERTY,
                priority=QualificationPriority.LOW,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Pool, garage, yard, etc."
            ),

            # Personal Category
            QualificationField(
                name="family_size",
                display_name="Family Size",
                category=QualificationCategory.PERSONAL,
                priority=QualificationPriority.HIGH,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Number of people who will live in the home"
            ),
            QualificationField(
                name="current_situation",
                display_name="Current Housing",
                category=QualificationCategory.PERSONAL,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Currently renting, owning, living with family, etc."
            ),
            QualificationField(
                name="pets",
                display_name="Pets",
                category=QualificationCategory.PERSONAL,
                priority=QualificationPriority.LOW,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Any pets that will live in the home"
            ),

            # Motivation Category
            QualificationField(
                name="motivation",
                display_name="Buying Motivation",
                category=QualificationCategory.MOTIVATION,
                priority=QualificationPriority.HIGH,
                status=QualificationStatus.MISSING,
                required=True,
                help_text="Why they want to buy (family growth, job change, investment, etc.)"
            ),
            QualificationField(
                name="decision_makers",
                display_name="Decision Makers",
                category=QualificationCategory.MOTIVATION,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Who is involved in the buying decision"
            ),
            QualificationField(
                name="concerns",
                display_name="Main Concerns",
                category=QualificationCategory.MOTIVATION,
                priority=QualificationPriority.MEDIUM,
                status=QualificationStatus.MISSING,
                required=False,
                help_text="Any concerns or hesitations about buying"
            )
        ]

        return fields

    def _load_qualification_milestones(self) -> List[QualificationMilestone]:
        """Load qualification milestones for gamification."""
        milestones = [
            QualificationMilestone(
                name="First Contact",
                description="Initial conversation completed",
                required_fields=["budget"],
                reward_points=10,
                icon="🎯"
            ),
            QualificationMilestone(
                name="Financial Foundation",
                description="Budget and financing status confirmed",
                required_fields=["budget", "financing_status"],
                reward_points=25,
                icon="💰"
            ),
            QualificationMilestone(
                name="Property Profile",
                description="Property preferences established",
                required_fields=["property_type", "location_preference", "bedrooms"],
                reward_points=30,
                icon="🏠"
            ),
            QualificationMilestone(
                name="Timeline Clarity",
                description="Purchase timeline confirmed",
                required_fields=["purchase_timeline", "motivation"],
                reward_points=20,
                icon="⏰"
            ),
            QualificationMilestone(
                name="Qualified Lead",
                description="All critical fields completed",
                required_fields=["budget", "financing_status", "property_type", "location_preference", "purchase_timeline", "motivation"],
                reward_points=50,
                icon="⭐"
            ),
            QualificationMilestone(
                name="Complete Profile",
                description="Comprehensive qualification completed",
                required_fields=["budget", "financing_status", "property_type", "location_preference", "purchase_timeline", "motivation", "bedrooms", "bathrooms", "family_size"],
                reward_points=75,
                icon="👑"
            )
        ]

        return milestones

    def render_qualification_tracker(
        self,
        lead_id: str,
        lead_data: Optional[Dict[str, Any]] = None,
        evaluation_result: Optional[LeadEvaluationResult] = None
    ) -> None:
        """
        Render the comprehensive qualification tracker interface.

        Args:
            lead_id: Lead identifier
            lead_data: Current lead data
            evaluation_result: Latest evaluation result
        """
        # Header
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
            text-align: center;
            color: white;
        ">
            <h1 style="margin: 0; font-size: 2rem; font-weight: 700;">
                📋 Qualification Tracker
            </h1>
            <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1rem;">
                Systematic lead qualification with progress visualization
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Update qualification data from evaluation result
        if evaluation_result:
            self._update_from_evaluation(evaluation_result)

        # Control panel
        self._render_control_panel()

        # Progress overview
        self._render_progress_overview()

        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📝 Interactive Checklist",
            "📊 Progress Analytics",
            "🏆 Achievements",
            "📈 Performance Insights"
        ])

        with tab1:
            self._render_interactive_checklist()

        with tab2:
            self._render_progress_analytics()

        with tab3:
            self._render_achievements_panel()

        with tab4:
            self._render_performance_insights()

        # Auto-save functionality
        if st.session_state.auto_save:
            self._auto_save_qualification_data(lead_id)

    def _render_control_panel(self) -> None:
        """Render qualification tracker control panel."""
        with st.expander("⚙️ Tracker Controls", expanded=False):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.session_state.qualification_filter = st.selectbox(
                    "Filter Fields",
                    ["all", "missing", "partial", "completed", "critical"],
                    index=0
                )

            with col2:
                st.session_state.show_help_text = st.checkbox(
                    "Show Help Text",
                    value=st.session_state.show_help_text
                )

            with col3:
                st.session_state.gamification_enabled = st.checkbox(
                    "Enable Achievements",
                    value=st.session_state.gamification_enabled
                )

            with col4:
                st.session_state.auto_save = st.checkbox(
                    "Auto Save",
                    value=st.session_state.auto_save
                )

    def _render_progress_overview(self) -> None:
        """Render high-level progress overview."""
        # Calculate progress metrics
        progress_data = self._calculate_progress_metrics()

        # Progress cards
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            self._render_progress_card(
                "Overall Progress",
                f"{progress_data['overall_completion']:.1f}%",
                progress_data['overall_completion'],
                "📈"
            )

        with col2:
            self._render_progress_card(
                "Critical Fields",
                f"{progress_data['critical_completed']}/{progress_data['critical_total']}",
                (progress_data['critical_completed'] / max(progress_data['critical_total'], 1)) * 100,
                "🎯"
            )

        with col3:
            self._render_progress_card(
                "Qualification Score",
                str(progress_data['qualification_score']),
                (progress_data['qualification_score'] / 100) * 100,
                "⭐"
            )

        with col4:
            self._render_progress_card(
                "Achievement Points",
                str(st.session_state.qualification_score),
                min((st.session_state.qualification_score / 200) * 100, 100),
                "🏆"
            )

        # Progress visualization
        self._render_progress_visualization(progress_data)

    def _render_progress_card(self, title: str, value: str, progress: float, icon: str) -> None:
        """Render individual progress card."""
        color = self._get_progress_color(progress)

        st.markdown(f"""
        <div style="
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border-left: 4px solid {color};
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
            <div style="
                font-size: 1.5rem;
                font-weight: 700;
                color: {color};
                margin-bottom: 0.25rem;
            ">{value}</div>
            <div style="
                font-size: 0.875rem;
                color: #64748b;
                font-weight: 500;
            ">{title}</div>
        </div>
        """, unsafe_allow_html=True)

    def _render_progress_visualization(self, progress_data: Dict[str, Any]) -> None:
        """Render progress visualization charts."""
        col1, col2 = st.columns(2)

        with col1:
            # Category breakdown donut chart
            category_data = progress_data['category_breakdown']

            fig = go.Figure(data=[go.Pie(
                labels=list(category_data.keys()),
                values=list(category_data.values()),
                hole=0.5,
                marker_colors=['#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#3B82F6']
            )])

            fig.update_layout(
                title="Completion by Category",
                showlegend=True,
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Priority breakdown bar chart
            priority_data = progress_data['priority_breakdown']

            fig = go.Figure(data=[go.Bar(
                x=list(priority_data.keys()),
                y=list(priority_data.values()),
                marker_color=['#7C3AED', '#EF4444', '#F59E0B', '#10B981', '#64748b']
            )])

            fig.update_layout(
                title="Completion by Priority",
                xaxis_title="Priority Level",
                yaxis_title="Fields Completed",
                height=300
            )

            st.plotly_chart(fig, use_container_width=True)

    def _render_interactive_checklist(self) -> None:
        """Render interactive qualification checklist."""
        st.markdown("### 📝 Qualification Checklist")

        # Filter fields based on selection
        filtered_fields = self._filter_fields(self.qualification_fields)

        # Group fields by category
        categories = {}
        for field in filtered_fields:
            if field.category not in categories:
                categories[field.category] = []
            categories[field.category].append(field)

        # Render each category
        for category, fields in categories.items():
            self._render_category_section(category, fields)

    def _render_category_section(
        self,
        category: QualificationCategory,
        fields: List[QualificationField]
    ) -> None:
        """Render a category section in the checklist."""
        # Category header
        completed_in_category = len([f for f in fields if f.status == QualificationStatus.COMPLETE])
        total_in_category = len(fields)
        completion_pct = (completed_in_category / total_in_category) * 100 if total_in_category > 0 else 0

        category_color = self._get_progress_color(completion_pct)
        category_icon = self._get_category_icon(category)

        st.markdown(f"""
        <div style="
            background: {category_color}15;
            border: 1px solid {category_color}40;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 1rem;
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                ">
                    <span style="font-size: 1.5rem;">{category_icon}</span>
                    <h3 style="
                        margin: 0;
                        color: {category_color};
                        text-transform: capitalize;
                        font-weight: 600;
                    ">{category.replace('_', ' ')}</h3>
                </div>
                <div style="
                    background: {category_color};
                    color: white;
                    padding: 0.25rem 0.75rem;
                    border-radius: 15px;
                    font-size: 0.875rem;
                    font-weight: 600;
                ">{completed_in_category}/{total_in_category}</div>
            </div>
        """, unsafe_allow_html=True)

        # Render fields in this category
        for field in fields:
            self._render_qualification_field(field)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_qualification_field(self, field: QualificationField) -> None:
        """Render individual qualification field with interactive controls."""
        # Field container
        field_key = f"field_{field.name}"

        # Status styling
        status_color = self._get_status_color(field.status)
        status_icon = self._get_status_icon(field.status)
        priority_badge = self._get_priority_badge(field.priority)

        col1, col2 = st.columns([3, 1])

        with col1:
            # Field header
            st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.5rem;
            ">
                <span style="font-size: 1.25rem;">{status_icon}</span>
                <strong style="color: #1e293b;">{field.display_name}</strong>
                {priority_badge}
                {'<span style="color: #ef4444; font-weight: bold;">*</span>' if field.required else ''}
            </div>
            """, unsafe_allow_html=True)

            # Value input
            current_value = st.session_state.qualification_data.get(field.name, field.value or "")

            if field.name in ["property_type", "financing_status"]:
                # Dropdown for specific fields
                options = self._get_field_options(field.name)
                selected_value = st.selectbox(
                    f"Select {field.display_name}",
                    options,
                    index=options.index(current_value) if current_value in options else 0,
                    key=field_key,
                    label_visibility="collapsed"
                )
            else:
                # Text input for most fields
                selected_value = st.text_input(
                    f"Enter {field.display_name}",
                    value=current_value,
                    key=field_key,
                    placeholder=f"Enter {field.display_name.lower()}...",
                    label_visibility="collapsed"
                )

            # Update field value
            if selected_value != current_value:
                st.session_state.qualification_data[field.name] = selected_value
                field.value = selected_value
                field.status = self._determine_field_status(selected_value)
                field.last_updated = datetime.now()

            # Help text
            if st.session_state.show_help_text and field.help_text:
                st.caption(f"💡 {field.help_text}")

        with col2:
            # Field actions
            if st.button("📝 Add Note", key=f"note_{field.name}", size="small"):
                self._add_field_note(field)

            # Confidence indicator
            if field.value and field.confidence > 0:
                confidence_color = self._get_confidence_color(field.confidence)
                st.markdown(f"""
                <div style="
                    background: {confidence_color}20;
                    border: 1px solid {confidence_color};
                    border-radius: 6px;
                    padding: 0.25rem 0.5rem;
                    text-align: center;
                    font-size: 0.75rem;
                    margin-top: 0.5rem;
                ">
                    Confidence: {field.confidence:.0%}
                </div>
                """, unsafe_allow_html=True)

    def _render_progress_analytics(self) -> None:
        """Render detailed progress analytics."""
        st.markdown("### 📊 Progress Analytics")

        # Progress over time chart
        self._render_progress_timeline()

        # Detailed metrics
        col1, col2 = st.columns(2)

        with col1:
            self._render_completion_matrix()

        with col2:
            self._render_priority_analysis()

    def _render_progress_timeline(self) -> None:
        """Render progress timeline chart."""
        # Generate sample timeline data (in real app, this would come from saved history)
        dates = pd.date_range(start=datetime.now() - timedelta(days=7), periods=8, freq='D')
        progress_values = np.cumsum(np.random.rand(8) * 10)  # Cumulative progress simulation

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=dates,
            y=progress_values,
            mode='lines+markers',
            name='Qualification Progress',
            line=dict(color='#3B82F6', width=3),
            marker=dict(size=8)
        ))

        fig.update_layout(
            title="Qualification Progress Over Time",
            xaxis_title="Date",
            yaxis_title="Progress Score",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_completion_matrix(self) -> None:
        """Render field completion matrix."""
        st.markdown("#### 📋 Field Completion Matrix")

        # Create completion matrix data
        categories = list(QualificationCategory)
        statuses = ["Complete", "Partial", "Missing"]

        matrix_data = []
        for category in categories:
            row = []
            category_fields = [f for f in self.qualification_fields if f.category == category]
            total_fields = len(category_fields)

            for status in [QualificationStatus.COMPLETE, QualificationStatus.PARTIAL, QualificationStatus.MISSING]:
                count = len([f for f in category_fields if f.status == status])
                percentage = (count / total_fields) * 100 if total_fields > 0 else 0
                row.append(percentage)

            matrix_data.append(row)

        fig = go.Figure(data=go.Heatmap(
            z=matrix_data,
            x=statuses,
            y=[cat.replace('_', ' ').title() for cat in categories],
            colorscale='RdYlGn',
            colorbar=dict(title="Percentage")
        ))

        fig.update_layout(
            title="Completion Status by Category",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_priority_analysis(self) -> None:
        """Render priority-based analysis."""
        st.markdown("#### 🎯 Priority Analysis")

        # Priority completion data
        priority_data = {}
        for priority in QualificationPriority:
            fields_with_priority = [f for f in self.qualification_fields if f.priority == priority]
            completed = len([f for f in fields_with_priority if f.status == QualificationStatus.COMPLETE])
            total = len(fields_with_priority)
            priority_data[priority.value] = {
                'completed': completed,
                'total': total,
                'percentage': (completed / total) * 100 if total > 0 else 0
            }

        # Display priority metrics
        for priority, data in priority_data.items():
            color = self._get_priority_color(QualificationPriority(priority))

            st.markdown(f"""
            <div style="
                background: {color}15;
                border-left: 4px solid {color};
                padding: 1rem;
                margin-bottom: 0.5rem;
                border-radius: 6px;
            ">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                ">
                    <strong style="color: {color}; text-transform: capitalize;">{priority}</strong>
                    <span style="color: #64748b;">{data['completed']}/{data['total']} ({data['percentage']:.1f}%)</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def _render_achievements_panel(self) -> None:
        """Render achievements and gamification panel."""
        if not st.session_state.gamification_enabled:
            st.info("🎮 Enable achievements in the control panel to see your progress!")
            return

        st.markdown("### 🏆 Achievements & Milestones")

        # Update achievements
        self._update_achievements()

        # Achievement cards
        cols = st.columns(3)
        for i, milestone in enumerate(self.milestones):
            col_idx = i % 3
            with cols[col_idx]:
                self._render_achievement_card(milestone)

        # Achievement progress
        self._render_achievement_progress()

    def _render_achievement_card(self, milestone: QualificationMilestone) -> None:
        """Render individual achievement card."""
        achieved = milestone.name in st.session_state.achieved_milestones
        card_style = "achieved" if achieved else "pending"

        if achieved:
            bg_color = "rgba(16, 185, 129, 0.08)"
            border_color = "#10B981"
            text_color = "#10B981"
        else:
            bg_color = "#F8FAFC"
            border_color = "#E2E8F0"
            text_color = "#64748b"

        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 2px solid {border_color};
            border-radius: 12px;
            padding: 1.5rem;
            text-align: center;
            margin-bottom: 1rem;
        ">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">
                {milestone.icon}
            </div>
            <h4 style="
                color: {text_color};
                margin: 0.5rem 0;
                font-weight: 600;
            ">{milestone.name}</h4>
            <p style="
                color: #64748b;
                margin: 0.5rem 0;
                font-size: 0.875rem;
            ">{milestone.description}</p>
            <div style="
                background: {border_color};
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 15px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-top: 0.5rem;
            ">+{milestone.reward_points} pts</div>
            {f'<div style="color: #10B981; font-size: 0.75rem; margin-top: 0.5rem;">✅ Achieved!</div>' if achieved else ''}
        </div>
        """, unsafe_allow_html=True)

    def _render_achievement_progress(self) -> None:
        """Render overall achievement progress."""
        total_points = sum(m.reward_points for m in self.milestones)
        earned_points = st.session_state.qualification_score

        progress_pct = (earned_points / total_points) * 100 if total_points > 0 else 0

        st.markdown("#### 📈 Achievement Progress")

        st.progress(progress_pct / 100)
        st.caption(f"Progress: {earned_points}/{total_points} points ({progress_pct:.1f}%)")

    def _render_performance_insights(self) -> None:
        """Render performance insights and recommendations."""
        st.markdown("### 📈 Performance Insights")

        # Calculate insights
        insights = self._generate_performance_insights()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 💡 Recommendations")
            for recommendation in insights['recommendations']:
                st.markdown(f"• {recommendation}")

        with col2:
            st.markdown("#### 📊 Key Metrics")
            for metric, value in insights['metrics'].items():
                st.metric(metric, value)

        # Export functionality
        st.markdown("---")
        if st.button("📥 Export Qualification Report"):
            self._export_qualification_report()

    # Helper methods
    def _calculate_progress_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive progress metrics."""
        total_fields = len(self.qualification_fields)
        completed_fields = len([f for f in self.qualification_fields if f.status == QualificationStatus.COMPLETE])
        partial_fields = len([f for f in self.qualification_fields if f.status == QualificationStatus.PARTIAL])

        critical_fields = [f for f in self.qualification_fields if f.priority == QualificationPriority.CRITICAL]
        critical_total = len(critical_fields)
        critical_completed = len([f for f in critical_fields if f.status == QualificationStatus.COMPLETE])

        # Category breakdown
        category_breakdown = {}
        for category in QualificationCategory:
            cat_fields = [f for f in self.qualification_fields if f.category == category]
            cat_completed = len([f for f in cat_fields if f.status == QualificationStatus.COMPLETE])
            cat_total = len(cat_fields)
            category_breakdown[category.replace('_', ' ').title()] = cat_completed

        # Priority breakdown
        priority_breakdown = {}
        for priority in QualificationPriority:
            pri_fields = [f for f in self.qualification_fields if f.priority == priority]
            pri_completed = len([f for f in pri_fields if f.status == QualificationStatus.COMPLETE])
            priority_breakdown[priority.value.title()] = pri_completed

        return {
            'overall_completion': (completed_fields / total_fields) * 100 if total_fields > 0 else 0,
            'critical_completed': critical_completed,
            'critical_total': critical_total,
            'qualification_score': min(50 + (completed_fields * 5) + (critical_completed * 10), 100),
            'category_breakdown': category_breakdown,
            'priority_breakdown': priority_breakdown
        }

    def _filter_fields(self, fields: List[QualificationField]) -> List[QualificationField]:
        """Filter fields based on current filter settings."""
        filter_value = st.session_state.qualification_filter

        if filter_value == "all":
            return fields
        elif filter_value == "missing":
            return [f for f in fields if f.status == QualificationStatus.MISSING]
        elif filter_value == "partial":
            return [f for f in fields if f.status == QualificationStatus.PARTIAL]
        elif filter_value == "completed":
            return [f for f in fields if f.status == QualificationStatus.COMPLETE]
        elif filter_value == "critical":
            return [f for f in fields if f.priority == QualificationPriority.CRITICAL]
        else:
            return fields

    def _update_from_evaluation(self, evaluation_result: LeadEvaluationResult) -> None:
        """Update qualification data from evaluation result."""
        if evaluation_result.qualification_fields:
            for field_name, eval_field in evaluation_result.qualification_fields.items():
                # Find matching field in our tracker
                tracker_field = next((f for f in self.qualification_fields if f.name == field_name), None)
                if tracker_field:
                    tracker_field.status = eval_field.status
                    tracker_field.value = eval_field.value
                    tracker_field.confidence = eval_field.confidence
                    tracker_field.last_updated = eval_field.last_updated

    def _update_achievements(self) -> None:
        """Update achievement status based on current progress."""
        completed_fields = set(
            f.name for f in self.qualification_fields
            if f.status == QualificationStatus.COMPLETE
        )

        total_points = 0
        for milestone in self.milestones:
            required_set = set(milestone.required_fields)
            if required_set.issubset(completed_fields):
                if milestone.name not in st.session_state.achieved_milestones:
                    st.session_state.achieved_milestones.append(milestone.name)
                    milestone.achieved = True
                    milestone.achieved_at = datetime.now()
                    st.toast(f"🎉 Achievement Unlocked: {milestone.name}!")

                total_points += milestone.reward_points

        st.session_state.qualification_score = total_points

    def _generate_performance_insights(self) -> Dict[str, Any]:
        """Generate performance insights and recommendations."""
        completed_count = len([f for f in self.qualification_fields if f.status == QualificationStatus.COMPLETE])
        total_count = len(self.qualification_fields)

        recommendations = []
        if completed_count < 5:
            recommendations.append("Focus on critical fields first (Budget, Timeline, Property Type)")
        if completed_count < 10:
            recommendations.append("Continue gathering key property preferences")
        else:
            recommendations.append("Excellent progress! Consider scheduling a property showing")

        metrics = {
            "Completion Rate": f"{(completed_count / total_count) * 100:.1f}%",
            "Fields Remaining": str(total_count - completed_count),
            "Achievement Points": str(st.session_state.qualification_score)
        }

        return {
            'recommendations': recommendations,
            'metrics': metrics
        }

    def _auto_save_qualification_data(self, lead_id: str) -> None:
        """Auto-save qualification data."""
        # In a real app, this would save to database
        # For demo, we'll save to session state
        save_data = {
            'lead_id': lead_id,
            'data': st.session_state.qualification_data,
            'progress': self._calculate_progress_metrics(),
            'achievements': st.session_state.achieved_milestones,
            'score': st.session_state.qualification_score,
            'last_updated': datetime.now().isoformat()
        }

        # Simulate auto-save
        if hasattr(st, '_auto_save_time'):
            if time.time() - st._auto_save_time > 30:  # Save every 30 seconds
                st.toast("💾 Qualification data auto-saved", icon="💾")
                st._auto_save_time = time.time()
        else:
            st._auto_save_time = time.time()

    def _export_qualification_report(self) -> None:
        """Export qualification report."""
        report_data = {
            'lead_qualification_report': {
                'generated_at': datetime.now().isoformat(),
                'overall_progress': self._calculate_progress_metrics(),
                'field_details': [asdict(f) for f in self.qualification_fields],
                'achievements': st.session_state.achieved_milestones,
                'qualification_score': st.session_state.qualification_score
            }
        }

        report_json = json.dumps(report_data, indent=2, default=str)

        st.download_button(
            label="📥 Download Qualification Report",
            data=report_json,
            file_name=f"qualification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

        st.success("📊 Qualification report generated successfully!")

    # Color and styling helper methods
    def _get_progress_color(self, progress: float) -> str:
        """Get color based on progress percentage."""
        if progress >= 80:
            return self.color_scheme['completed']
        elif progress >= 50:
            return self.color_scheme['partial']
        else:
            return self.color_scheme['missing']

    def _get_status_color(self, status: QualificationStatus) -> str:
        """Get color for qualification status."""
        status_colors = {
            QualificationStatus.COMPLETE: self.color_scheme['completed'],
            QualificationStatus.PARTIAL: self.color_scheme['partial'],
            QualificationStatus.MISSING: self.color_scheme['missing'],
            QualificationStatus.UNCLEAR: self.color_scheme['missing'],
            QualificationStatus.CONFLICTING: self.color_scheme['missing']
        }
        return status_colors.get(status, self.color_scheme['missing'])

    def _get_status_icon(self, status: QualificationStatus) -> str:
        """Get icon for qualification status."""
        status_icons = {
            QualificationStatus.COMPLETE: "✅",
            QualificationStatus.PARTIAL: "⚠️",
            QualificationStatus.MISSING: "❌",
            QualificationStatus.UNCLEAR: "❓",
            QualificationStatus.CONFLICTING: "⚡"
        }
        return status_icons.get(status, "❓")

    def _get_priority_badge(self, priority: QualificationPriority) -> str:
        """Get priority badge HTML."""
        color = self._get_priority_color(priority)
        return f"""
        <span style="
            background: {color};
            color: white;
            padding: 0.125rem 0.5rem;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        ">{priority.value}</span>
        """

    def _get_priority_color(self, priority: QualificationPriority) -> str:
        """Get color for priority level."""
        priority_colors = {
            QualificationPriority.CRITICAL: "#7C3AED",
            QualificationPriority.HIGH: "#EF4444",
            QualificationPriority.MEDIUM: "#F59E0B",
            QualificationPriority.LOW: "#10B981",
            QualificationPriority.OPTIONAL: "#64748b"
        }
        return priority_colors.get(priority, self.color_scheme['primary'])

    def _get_confidence_color(self, confidence: float) -> str:
        """Get color based on confidence score."""
        if confidence >= 0.8:
            return self.color_scheme['completed']
        elif confidence >= 0.6:
            return self.color_scheme['partial']
        else:
            return self.color_scheme['missing']

    def _get_category_icon(self, category: QualificationCategory) -> str:
        """Get icon for qualification category."""
        category_icons = {
            QualificationCategory.FINANCIAL: "💰",
            QualificationCategory.PERSONAL: "👥",
            QualificationCategory.PROPERTY: "🏠",
            QualificationCategory.TIMELINE: "⏰",
            QualificationCategory.MOTIVATION: "🎯"
        }
        return category_icons.get(category, "📋")

    def _get_field_options(self, field_name: str) -> List[str]:
        """Get dropdown options for specific fields."""
        options_map = {
            "property_type": ["", "Single Family Home", "Condo", "Townhouse", "Duplex", "Mobile Home", "Other"],
            "financing_status": ["", "Not Pre-approved", "Pre-qualified", "Pre-approved", "Cash Buyer", "Needs Financing"]
        }
        return options_map.get(field_name, [""])

    def _determine_field_status(self, value: Optional[str]) -> QualificationStatus:
        """Determine qualification status based on field value."""
        if not value or not value.strip():
            return QualificationStatus.MISSING
        elif len(value.strip()) < 3:
            return QualificationStatus.PARTIAL
        else:
            return QualificationStatus.COMPLETE

    def _add_field_note(self, field: QualificationField) -> None:
        """Add note to qualification field."""
        # This would open a modal or input in a real app
        st.session_state[f"note_input_{field.name}"] = True


# Factory function for easy use
def create_qualification_tracker() -> QualificationTracker:
    """Create and return a QualificationTracker instance."""
    return QualificationTracker()


# Usage example:
"""
# In your Streamlit app
tracker = create_qualification_tracker()

# Render the tracker
tracker.render_qualification_tracker(
    lead_id="lead_123",
    lead_data=your_lead_data,
    evaluation_result=your_evaluation_result
)
"""