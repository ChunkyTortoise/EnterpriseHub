"""
Claude Coaching Widget - Embeddable Real-Time Assistance

Lightweight Streamlit widget providing quick Claude coaching that can be
embedded in any Streamlit application throughout EnterpriseHub for
universal Claude access.

Key Features:
- Lightweight embed-anywhere design
- Quick coaching with agent context
- Role-aware suggestions
- Minimal UI footprint
- Universal Gateway integration
- Real-time response indicators
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider replacing inline styled divs with enterprise_card
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
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional
import json

from ..core.service_registry import ServiceRegistry

# Initialize service registry
service_registry = ServiceRegistry()


class ClaudeCoachingWidget(EnterpriseDashboardComponent):
    """
    Lightweight Claude coaching widget for universal embedding.

    Provides quick access to Claude coaching from any Streamlit component
    with minimal UI footprint and maximum usability.
    """

    def __init__(self, widget_id: str = "default"):
        self.widget_id = widget_id
        self.session_key = f"claude_widget_{widget_id}"

    def render_compact_widget(
        self,
        agent_id: Optional[str] = None,
        show_header: bool = True,
        default_query_type: str = "general_coaching",
        placeholder_text: str = "Ask Claude for coaching..."
    ) -> None:
        """
        Render compact coaching widget for embedding in other apps.

        Args:
            agent_id: Optional agent ID for context
            show_header: Whether to show widget header
            default_query_type: Default query type for routing
            placeholder_text: Placeholder text for input field
        """
        if show_header:
            st.markdown("### 🤖 Claude Coaching")

        # Initialize widget state
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = {
                'last_response': None,
                'response_time': 0,
                'request_count': 0
            }

        # Input area
        col1, col2 = st.columns([4, 1])

        with col1:
            query = st.text_input(
                "Quick Coaching Query",
                placeholder=placeholder_text,
                key=f"{self.session_key}_input",
                label_visibility="collapsed"
            )

        with col2:
            get_help = st.button("💡", key=f"{self.session_key}_button", help="Get Claude Coaching")

        # Process query
        if get_help and query:
            self._process_quick_coaching(
                query=query,
                agent_id=agent_id,
                query_type=default_query_type
            )

        # Show recent response
        self._show_recent_response()

    def render_sidebar_widget(
        self,
        agent_id: Optional[str] = None,
        max_height: int = 300
    ) -> None:
        """
        Render coaching widget optimized for sidebar placement.

        Args:
            agent_id: Optional agent ID for context
            max_height: Maximum height for response area
        """
        st.markdown("#### 🤖 Quick Claude Coaching")

        # Compact query input
        query = st.text_area(
            "Ask Claude",
            placeholder="Quick question or coaching request...",
            height=60,
            key=f"{self.session_key}_sidebar_input"
        )

        # Query type selector
        query_type = st.selectbox(
            "Type",
            ["general_coaching", "objection_handling", "real_time_assistance"],
            key=f"{self.session_key}_type",
            format_func=lambda x: x.replace("_", " ").title()
        )

        # Get coaching button
        if st.button("Get Coaching", key=f"{self.session_key}_sidebar_button", use_container_width=True):
            if query:
                self._process_quick_coaching(query, agent_id, query_type)
            else:
                st.warning("Please enter a query first.")

        # Show response in container with max height
        self._show_recent_response(max_height=max_height)

    def render_inline_widget(
        self,
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Render inline coaching widget that returns response data.

        Args:
            agent_id: Optional agent ID for context
            context: Optional context data

        Returns:
            Claude response data if query was processed
        """
        with st.expander("🤖 Get Claude Coaching", expanded=False):
            query = st.text_input(
                "Coaching Query",
                key=f"{self.session_key}_inline_input"
            )

            col1, col2 = st.columns(2)
            with col1:
                query_type = st.selectbox(
                    "Query Type",
                    ["general_coaching", "objection_handling", "property_recommendation", "market_analysis"],
                    key=f"{self.session_key}_inline_type"
                )
            with col2:
                priority = st.selectbox(
                    "Priority",
                    ["normal", "high", "critical"],
                    key=f"{self.session_key}_inline_priority"
                )

            if st.button("Get Coaching", key=f"{self.session_key}_inline_button"):
                if query:
                    return self._process_quick_coaching(
                        query=query,
                        agent_id=agent_id,
                        query_type=query_type,
                        priority=priority,
                        context=context,
                        return_data=True
                    )
                else:
                    st.warning("Please enter a query first.")

        return None

    def render_floating_assistant(
        self,
        position: str = "bottom-right",
        agent_id: Optional[str] = None
    ) -> None:
        """
        Render floating assistant widget using custom CSS.

        Args:
            position: Position on page ("bottom-right", "bottom-left", etc.)
            agent_id: Optional agent ID for context
        """
        # Inject floating widget CSS
        st.markdown(f"""
        <style>
        .floating-claude-widget {{
            position: fixed;
            {position.replace('-', ': 20px; ')}: 20px;
            z-index: 1000;
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            max-width: 300px;
        }}

        .floating-claude-header {{
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem;
            margin: -1rem -1rem 1rem -1rem;
            border-radius: 10px 10px 0 0;
            text-align: center;
            font-weight: bold;
        }}

        .claude-response-compact {{
            background: #f8f9fa;
            border-radius: 5px;
            padding: 0.5rem;
            margin-top: 0.5rem;
            font-size: 0.9em;
            max-height: 100px;
            overflow-y: auto;
        }}
        </style>
        """, unsafe_allow_html=True)

        # Note: Full floating implementation would require custom HTML component
        # For now, show as regular expandable widget
        with st.expander("🤖 Claude Assistant", expanded=False):
            self.render_compact_widget(agent_id=agent_id, show_header=False)

    def _process_quick_coaching(
        self,
        query: str,
        agent_id: Optional[str],
        query_type: str = "general_coaching",
        priority: str = "normal",
        context: Optional[Dict[str, Any]] = None,
        return_data: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Process coaching query through Universal Gateway."""
        try:
            # Use fallback agent if none provided
            if not agent_id:
                agent_id = "widget_user_001"

            start_time = time.time()

            with st.spinner("Getting coaching..."):
                # Process through service registry
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                response_data = loop.run_until_complete(
                    service_registry.process_claude_query_with_agent_context(
                        agent_id=agent_id,
                        query=query,
                        context={
                            "widget_context": True,
                            "query_source": "widget",
                            **(context or {})
                        },
                        query_type=query_type,
                        priority=priority
                    )
                )

                processing_time = (time.time() - start_time) * 1000

                if response_data:
                    # Update widget state
                    widget_state = st.session_state[self.session_key]
                    widget_state['last_response'] = response_data
                    widget_state['response_time'] = processing_time
                    widget_state['request_count'] += 1

                    # Show success message
                    st.success(f"Coaching received! ({processing_time:.0f}ms)")

                    if return_data:
                        return response_data
                else:
                    st.error("Failed to get coaching response.")

        except Exception as e:
            st.error(f"Error getting coaching: {e}")

        return None

    def _show_recent_response(self, max_height: int = 200) -> None:
        """Show the most recent coaching response."""
        widget_state = st.session_state.get(self.session_key, {})
        last_response = widget_state.get('last_response')

        if last_response:
            # Response container with max height
            response_container = st.container()

            with response_container:
                # Main response
                st.markdown(f"""
                <div style="background: #e7f3ff; border-left: 4px solid #007bff;
                           padding: 0.75rem; margin: 0.5rem 0; border-radius: 4px;
                           max-height: {max_height}px; overflow-y: auto;">
                    <strong>Claude:</strong><br>
                    {last_response['response']}
                </div>
                """, unsafe_allow_html=True)

                # Show metadata in compact form
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.caption(f"⏱️ {last_response['processing_time_ms']:.0f}ms")
                with col2:
                    st.caption(f"🎯 {last_response['confidence']:.0%}")
                with col3:
                    st.caption(f"🔧 {last_response['service_used'][:10]}...")

                # Show quick actions if there are recommendations
                if last_response.get('next_questions'):
                    with st.expander("💡 Follow-up Questions", expanded=False):
                        for i, question in enumerate(last_response['next_questions'][:3]):
                            if st.button(f"❓ {question}", key=f"{self.session_key}_followup_{i}"):
                                # Set the question as input for next query
                                st.session_state[f"{self.session_key}_input"] = question
                                st.experimental_rerun()

    def get_widget_stats(self) -> Dict[str, Any]:
        """Get widget usage statistics."""
        widget_state = st.session_state.get(self.session_key, {})

        return {
            'request_count': widget_state.get('request_count', 0),
            'last_response_time': widget_state.get('response_time', 0),
            'has_recent_response': widget_state.get('last_response') is not None,
            'widget_id': self.widget_id
        }


# ========================================================================
# Convenience Functions for Easy Integration
# ========================================================================

def claude_coaching_compact(
    agent_id: Optional[str] = None,
    widget_id: str = "default",
    **kwargs
) -> None:
    """
    Render compact Claude coaching widget.

    Args:
        agent_id: Optional agent ID for context
        widget_id: Unique widget identifier
        **kwargs: Additional arguments for render_compact_widget
    """
    widget = ClaudeCoachingWidget(widget_id)
    widget.render_compact_widget(agent_id=agent_id, **kwargs)


def claude_coaching_sidebar(
    agent_id: Optional[str] = None,
    widget_id: str = "sidebar",
    **kwargs
) -> None:
    """
    Render sidebar Claude coaching widget.

    Args:
        agent_id: Optional agent ID for context
        widget_id: Unique widget identifier
        **kwargs: Additional arguments for render_sidebar_widget
    """
    widget = ClaudeCoachingWidget(widget_id)
    widget.render_sidebar_widget(agent_id=agent_id, **kwargs)


def claude_coaching_inline(
    agent_id: Optional[str] = None,
    widget_id: str = "inline",
    context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Render inline Claude coaching widget that returns response data.

    Args:
        agent_id: Optional agent ID for context
        widget_id: Unique widget identifier
        context: Optional context data

    Returns:
        Claude response data if query was processed
    """
    widget = ClaudeCoachingWidget(widget_id)
    return widget.render_inline_widget(agent_id=agent_id, context=context)


def claude_quick_ask(
    query: str,
    agent_id: Optional[str] = None,
    query_type: str = "general_coaching",
    show_response: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Quick Claude coaching without UI components.

    Args:
        query: Coaching query
        agent_id: Optional agent ID for context
        query_type: Query type for routing
        show_response: Whether to display response in Streamlit

    Returns:
        Claude response data
    """
    try:
        if not agent_id:
            agent_id = "quick_ask_user"

        # Process through service registry
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        response_data = loop.run_until_complete(
            service_registry.process_claude_query_with_agent_context(
                agent_id=agent_id,
                query=query,
                context={"query_source": "quick_ask"},
                query_type=query_type,
                priority="normal"
            )
        )

        if show_response and response_data:
            st.info(f"**Claude:** {response_data['response']}")

        return response_data

    except Exception as e:
        if show_response:
            st.error(f"Error getting coaching: {e}")
        return None


# ========================================================================
# Example Integration Patterns
# ========================================================================

def demo_widget_integration():
    """Demonstrate different widget integration patterns."""
    st.title("Claude Coaching Widget Integration Demo")

    tab1, tab2, tab3, tab4 = st.tabs(["Compact Widget", "Sidebar Widget", "Inline Widget", "Quick Ask"])

    with tab1:
        st.subheader("Compact Widget")
        st.write("Perfect for embedding in dashboards and main content areas.")
        claude_coaching_compact(agent_id="demo_agent_001", widget_id="demo_compact")

    with tab2:
        st.subheader("Sidebar Widget")
        st.write("Optimized for sidebar placement with space-efficient design.")
        with st.sidebar:
            claude_coaching_sidebar(agent_id="demo_agent_001", widget_id="demo_sidebar")

    with tab3:
        st.subheader("Inline Widget")
        st.write("Expandable widget that can return data for programmatic use.")
        response_data = claude_coaching_inline(
            agent_id="demo_agent_001",
            widget_id="demo_inline",
            context={"page": "demo", "section": "inline_test"}
        )

        if response_data:
            st.json(response_data)

    with tab4:
        st.subheader("Quick Ask")
        st.write("Programmatic coaching without UI components.")

        example_query = st.text_input("Try Quick Ask", value="How do I handle price objections?")
        if st.button("Quick Ask Claude"):
            response = claude_quick_ask(
                query=example_query,
                agent_id="demo_agent_001",
                query_type="objection_handling"
            )


if __name__ == "__main__":
    demo_widget_integration()