"""
🧪 A/B Testing Integration for Streamlit Components
Enhanced Real Estate AI Platform - A/B Testing Integration

Created: January 11, 2026
Version: v1.0.0 - A/B Testing Integration
Author: EnterpriseHub Development Team

Streamlit integration for A/B testing the next-level visual enhancements.
Provides seamless switching between control and enhanced variants.
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



import streamlit as st

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
import os
import sys
from typing import Dict, Any, Optional
import uuid

# Add config path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.ab_testing_config import (
    get_user_variant,
    get_user_config,
    track_user_metric,
    is_enhanced_variant,
    ab_testing_manager
)

class StreamlitABTesting(EnterpriseDashboardComponent):
    """A/B testing integration for Streamlit applications."""

    def __init__(self):
        """Initialize A/B testing integration."""

        # Initialize session state for A/B testing
        if 'ab_test_user_id' not in st.session_state:
            st.session_state.ab_test_user_id = str(uuid.uuid4())

        if 'ab_test_variant' not in st.session_state:
            st.session_state.ab_test_variant = get_user_variant(st.session_state.ab_test_user_id)

        if 'ab_test_config' not in st.session_state:
            st.session_state.ab_test_config = get_user_config(st.session_state.ab_test_user_id)

        if 'ab_test_session_start' not in st.session_state:
            st.session_state.ab_test_session_start = st._get_option("server.runOnSave", default=0)

    @property
    def user_id(self) -> str:
        """Get current user's A/B test ID."""
        return st.session_state.ab_test_user_id

    @property
    def variant(self) -> str:
        """Get current user's variant."""
        return st.session_state.ab_test_variant

    @property
    def config(self) -> Dict[str, Any]:
        """Get current user's variant configuration."""
        return st.session_state.ab_test_config

    @property
    def is_enhanced(self) -> bool:
        """Check if user is in enhanced variant."""
        return self.variant == "enhanced"

    def track_metric(self, metric_name: str, value: float) -> None:
        """Track A/B test metric for current user."""
        track_user_metric(self.user_id, metric_name, value)

    def track_session_duration(self) -> None:
        """Track user session duration."""
        # In a real implementation, you'd calculate actual session duration
        # For demo purposes, we'll use a placeholder
        import time
        session_duration = time.time() - st.session_state.get('session_start_time', time.time())
        self.track_metric("session_duration", session_duration)

    def track_engagement_event(self, event_type: str, value: float = 1.0) -> None:
        """Track user engagement events."""

        # Map event types to metrics
        event_mapping = {
            'click': 'user_engagement',
            'scroll': 'user_engagement',
            'hover': 'user_engagement',
            'task_complete': 'task_completion_rate',
            'feature_discover': 'feature_discovery',
            'rating': 'visual_appeal_rating'
        }

        if event_type in event_mapping:
            self.track_metric(event_mapping[event_type], value)

    def render_variant_indicator(self, show_admin_info: bool = False) -> None:
        """Render variant indicator for debugging/admin purposes."""

        if show_admin_info:
            with st.sidebar:
                st.markdown("---")
                st.markdown("### 🧪 A/B Test Info")

                variant_color = "#10B981" if self.is_enhanced else "#6B7280"

                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, {variant_color}20 0%, {variant_color}10 100%);
                        border: 1px solid {variant_color}40;
                        border-radius: 8px;
                        padding: 12px;
                        margin: 8px 0;
                    ">
                        <div style="font-weight: 600; color: {variant_color};">
                            Variant: {self.variant.title()}
                        </div>
                        <div style="font-size: 0.8em; color: #6B7280;">
                            User ID: {self.user_id[:8]}...
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Test status
                test_status = ab_testing_manager.get_test_status()

                st.markdown("#### Test Status")
                st.write(f"**Status**: {test_status['status'].title()}")
                st.write(f"**Progress**: {test_status['progress_percent']:.1f}%")
                st.write(f"**Days Elapsed**: {test_status['days_elapsed']}")

    def apply_conditional_styling(self) -> str:
        """Apply variant-specific styling to Streamlit app."""

        if self.is_enhanced:
            # Enhanced variant styling
            return """
            <style>
            /* Enhanced Visual Variant Styling */
            .stApp {
                background: linear-gradient(135deg,
                    rgba(67, 56, 202, 0.05) 0%,
                    rgba(147, 51, 234, 0.05) 100%);
            }

            .stButton > button {
                background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 100%);
                color: white;
                border: none;
                border-radius: 12px;
                transition: all 0.3s ease;
            }

            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(124, 58, 237, 0.3);
            }

            .stMetric {
                background: linear-gradient(135deg,
                    rgba(255,255,255,0.1) 0%,
                    rgba(255,255,255,0.05) 100%);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 16px;
                padding: 1rem;
                backdrop-filter: blur(10px);
            }

            .stSelectbox > div > div {
                background: linear-gradient(135deg,
                    rgba(255,255,255,0.1) 0%,
                    rgba(255,255,255,0.05) 100%);
                border: 1px solid rgba(147, 51, 234, 0.3);
                border-radius: 12px;
                backdrop-filter: blur(10px);
            }
            </style>
            """
        else:
            # Control variant styling (basic)
            return """
            <style>
            /* Control Variant Styling (Basic) */
            .stApp {
                background: #f8f9fa;
            }

            .stButton > button {
                background: #6c757d;
                color: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }

            .stButton > button:hover {
                background: #5a6268;
            }

            .stMetric {
                background: white;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 1rem;
            }

            .stSelectbox > div > div {
                background: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
            }
            </style>
            """

    def render_dashboard_with_variant(self) -> None:
        """Render dashboard based on user's A/B test variant."""

        # Apply variant-specific styling
        st.markdown(self.apply_conditional_styling(), unsafe_allow_html=True)

        if self.is_enhanced:
            # Render enhanced version
            self._render_enhanced_dashboard()
        else:
            # Render control version
            self._render_control_dashboard()

        # Track page view
        self.track_engagement_event('click', 1.0)

    def _render_enhanced_dashboard(self) -> None:
        """Render the enhanced visual intelligence dashboard."""

        # Import enhanced components
        try:
            from next_level_visual_showcase import NextLevelVisualShowcase

            st.markdown(
                """
                <div style="
                    text-align: center;
                    padding: 2rem;
                    background: linear-gradient(135deg,
                        rgba(67, 56, 202, 0.1) 0%,
                        rgba(147, 51, 234, 0.1) 100%);
                    border-radius: 20px;
                    margin-bottom: 2rem;
                    backdrop-filter: blur(20px);
                ">
                    <h1 style="
                        background: linear-gradient(135deg, #4C1D95 0%, #7C3AED 50%, #EC4899 100%);
                        background-clip: text;
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        font-size: 3rem;
                        font-weight: 900;
                        margin: 0;
                    ">
                        🚀 Enhanced Experience
                    </h1>
                    <p style="
                        font-size: 1.2rem;
                        color: #6B7280;
                        margin-top: 1rem;
                    ">
                        You're experiencing our next-level visual intelligence system
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Initialize and render showcase
            if 'next_level_showcase' not in st.session_state:
                st.session_state.next_level_showcase = NextLevelVisualShowcase()

            showcase = st.session_state.next_level_showcase
            showcase.render_main_showcase()

            # Track enhanced features usage
            self.track_engagement_event('feature_discover', 5.0)

        except ImportError:
            st.error("Enhanced components not available")
            self._render_control_dashboard()

    def _render_control_dashboard(self) -> None:
        """Render the basic/control dashboard."""

        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 2rem;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-bottom: 2rem;
            ">
                <h1 style="
                    color: #495057;
                    font-size: 2rem;
                    font-weight: 600;
                    margin: 0;
                ">
                    Real Estate AI Dashboard
                </h1>
                <p style="
                    font-size: 1rem;
                    color: #6c757d;
                    margin-top: 1rem;
                ">
                    Standard interface experience
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Leads", "1,247", "12")

        with col2:
            st.metric("Properties", "89", "3")

        with col3:
            st.metric("Conversion Rate", "23.5%", "2.1%")

        with col4:
            st.metric("Avg Response", "4.2h", "-0.8h")

        # Basic chart placeholder
        st.markdown(
            """
            <div style="
                background: #e9ecef;
                height: 200px;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #6c757d;
                font-size: 1.1em;
                margin: 2rem 0;
            ">
                📊 Basic Performance Chart
            </div>
            """,
            unsafe_allow_html=True
        )

        # Track basic features usage
        self.track_engagement_event('feature_discover', 1.0)

# Global A/B testing instance
streamlit_ab_testing = StreamlitABTesting()

# Utility functions for easy integration
def initialize_ab_testing() -> StreamlitABTesting:
    """Initialize A/B testing for current session."""
    return streamlit_ab_testing

def get_current_variant() -> str:
    """Get current user's A/B test variant."""
    return streamlit_ab_testing.variant

def should_show_enhanced() -> bool:
    """Check if enhanced features should be shown."""
    return streamlit_ab_testing.is_enhanced

def track_user_engagement(event_type: str, value: float = 1.0) -> None:
    """Track user engagement for A/B testing."""
    streamlit_ab_testing.track_engagement_event(event_type, value)

# Export key components
__all__ = [
    'StreamlitABTesting',
    'streamlit_ab_testing',
    'initialize_ab_testing',
    'get_current_variant',
    'should_show_enhanced',
    'track_user_engagement'
]