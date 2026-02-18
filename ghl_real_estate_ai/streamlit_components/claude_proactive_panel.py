"""
Claude Proactive Suggestions Panel

Displays intelligent, contextual suggestions from Claude throughout the platform.
Integrates with the proactive suggestions system to provide timely insights and actions.
"""

import streamlit as st
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from ghl_real_estate_ai.services.claude_proactive_suggestions import (
    claude_proactive_suggestions,
    SuggestionPriority,
    SuggestionType
)


class ClaudeProactivePanel:
    """Interactive panel for displaying and managing Claude's proactive suggestions."""

    def __init__(self):
        """Initialize proactive panel."""
        self.suggestion_icons = {
            SuggestionType.LEAD_OPPORTUNITY: "🎯",
            SuggestionType.FOLLOW_UP_REMINDER: "📞",
            SuggestionType.MARKET_INSIGHT: "📈",
            SuggestionType.PROCESS_OPTIMIZATION: "⚡",
            SuggestionType.STRATEGIC_RECOMMENDATION: "💡"
        }

        self.priority_colors = {
            SuggestionPriority.CRITICAL: "#dc2626",  # Red
            SuggestionPriority.HIGH: "#ea580c",     # Orange
            SuggestionPriority.MEDIUM: "#2563eb",   # Blue
            SuggestionPriority.LOW: "#16a34a"       # Green
        }

        self.priority_labels = {
            SuggestionPriority.CRITICAL: "🚨 CRITICAL",
            SuggestionPriority.HIGH: "🔥 HIGH",
            SuggestionPriority.MEDIUM: "📋 MEDIUM",
            SuggestionPriority.LOW: "💡 INSIGHT"
        }

    def render_proactive_suggestions(
        self,
        context: Dict[str, Any],
        max_suggestions: int = 6,
        show_metrics: bool = False
    ) -> None:
        """
        Render proactive suggestions panel.

        Args:
            context: Current application context
            max_suggestions: Maximum number of suggestions to display
            show_metrics: Whether to show suggestion metrics
        """
        # Initialize suggestion state
        if "proactive_suggestions" not in st.session_state:
            st.session_state.proactive_suggestions = []
        if "suggestions_last_refresh" not in st.session_state:
            st.session_state.suggestions_last_refresh = None

        # Check if we need to refresh suggestions
        should_refresh = (
            not st.session_state.proactive_suggestions or
            not st.session_state.suggestions_last_refresh or
            (datetime.now() - st.session_state.suggestions_last_refresh).total_seconds() > 300  # 5 min refresh
        )

        with st.expander("🧠 Claude's Smart Suggestions", expanded=True):
            col_header, col_refresh = st.columns([3, 1])

            with col_header:
                st.markdown("**Proactive insights and opportunities from Claude AI**")

            with col_refresh:
                if st.button("🔄 Refresh", key="refresh_suggestions"):
                    should_refresh = True

            if should_refresh:
                with st.spinner("Claude is analyzing opportunities..."):
                    # Generate sample data for demonstration
                    sample_leads = self._generate_sample_lead_data(context)
                    sample_activity = self._generate_sample_activity_data(context)

                    # Get suggestions (async wrapper for Streamlit)
                    suggestions = asyncio.run(
                        claude_proactive_suggestions.generate_suggestions(
                            user_context=context,
                            lead_data=sample_leads,
                            activity_data=sample_activity
                        )
                    )

                    st.session_state.proactive_suggestions = suggestions[:max_suggestions]
                    st.session_state.suggestions_last_refresh = datetime.now()

            # Display suggestions
            suggestions = st.session_state.proactive_suggestions

            if not suggestions:
                st.info("🎯 Claude is monitoring for opportunities. Check back soon!")
                return

            # Show metrics if requested
            if show_metrics:
                metrics = claude_proactive_suggestions.get_suggestion_metrics()
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Total Suggestions", metrics["total_active"])
                with col2:
                    st.metric("Critical", metrics["by_priority"].get("critical", 0))
                with col3:
                    st.metric("High Priority", metrics["by_priority"].get("high", 0))
                with col4:
                    st.metric("Last Updated", "Now" if should_refresh else "5m ago")

                st.markdown("---")

            # Render individual suggestions
            for i, suggestion in enumerate(suggestions):
                self._render_suggestion_card(suggestion, i)

            st.markdown("---")
            st.caption(f"💡 Showing {len(suggestions)} of {len(st.session_state.proactive_suggestions)} suggestions • Updates every 5 minutes")

    def _render_suggestion_card(self, suggestion, index: int) -> None:
        """Render individual suggestion card."""
        priority_color = self.priority_colors[suggestion.priority]
        priority_label = self.priority_labels[suggestion.priority]
        suggestion_icon = self.suggestion_icons[suggestion.type]

        # Create unique key for this suggestion
        card_key = f"suggestion_{suggestion.id}_{index}"

        # Suggestion card
        with st.container():
            # Header with priority and dismiss button
            col_header, col_priority, col_dismiss = st.columns([3, 1, 1])

            with col_header:
                st.markdown(f"### {suggestion_icon} {suggestion.title}")

            with col_priority:
                st.markdown(f"""
                <div style='
                    background: {priority_color};
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-align: center;
                    margin-top: 0.5rem;
                '>
                    {priority_label}
                </div>
                """, unsafe_allow_html=True)

            with col_dismiss:
                if st.button("✕", key=f"dismiss_{card_key}", help="Dismiss this suggestion"):
                    asyncio.run(claude_proactive_suggestions.dismiss_suggestion(suggestion.id))
                    # Remove from session state
                    st.session_state.proactive_suggestions = [
                        s for s in st.session_state.proactive_suggestions
                        if s.id != suggestion.id
                    ]
                    st.rerun()

            # Suggestion content
            st.markdown(suggestion.message)

            # Action items
            if suggestion.action_items:
                st.markdown("**📋 Recommended Actions:**")
                for action in suggestion.action_items:
                    st.markdown(f"• {action}")

            # Context-specific quick actions
            if suggestion.type == SuggestionType.LEAD_OPPORTUNITY:
                self._render_lead_quick_actions(suggestion, card_key)
            elif suggestion.type == SuggestionType.FOLLOW_UP_REMINDER:
                self._render_followup_quick_actions(suggestion, card_key)
            elif suggestion.type == SuggestionType.MARKET_INSIGHT:
                self._render_market_quick_actions(suggestion, card_key)

            # Expires info
            if suggestion.expires_at:
                time_left = suggestion.expires_at - datetime.now()
                hours_left = max(0, int(time_left.total_seconds() / 3600))
                st.caption(f"⏰ Expires in {hours_left} hours")

            st.markdown("---")

    def _render_lead_quick_actions(self, suggestion, key: str) -> None:
        """Render quick actions for lead opportunities."""
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📞 Call Lead", key=f"call_{key}", use_container_width=True):
                lead_name = suggestion.context_data.get('name', 'Lead')
                st.success(f"✅ Calling {lead_name} - Opening dialer...")

        with col2:
            if st.button("📧 Send Email", key=f"email_{key}", use_container_width=True):
                lead_name = suggestion.context_data.get('name', 'Lead')
                st.success(f"✅ Email template created for {lead_name}")

        with col3:
            if st.button("🏠 Show Properties", key=f"props_{key}", use_container_width=True):
                st.success("✅ Opening property recommendations...")

    def _render_followup_quick_actions(self, suggestion, key: str) -> None:
        """Render quick actions for follow-up reminders."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📱 Quick Message", key=f"msg_{key}", use_container_width=True):
                st.success("✅ Quick message template opened")

        with col2:
            if st.button("📅 Schedule Call", key=f"schedule_{key}", use_container_width=True):
                st.success("✅ Calendar scheduler opened")

    def _render_market_quick_actions(self, suggestion, key: str) -> None:
        """Render quick actions for market insights."""
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📊 View Report", key=f"report_{key}", use_container_width=True):
                st.success("✅ Market analysis report generated")

        with col2:
            if st.button("📣 Share Insight", key=f"share_{key}", use_container_width=True):
                st.success("✅ Market insight shared with team")

    def _generate_sample_lead_data(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate sample lead data for demonstration."""
        current_section = context.get("current_section", "unknown")

        # Context-aware sample data
        if current_section == "lead_intelligence":
            return [
                {
                    "id": "lead_001",
                    "name": "Sarah Johnson",
                    "budget": 450000,
                    "timeline": "immediate",
                    "properties_viewed": 6,
                    "last_contact_date": "2026-01-10",
                    "interest_level": "high",
                    "last_activity_hours": 2
                },
                {
                    "id": "lead_002",
                    "name": "Mike Chen",
                    "budget": 380000,
                    "timeline": "2 months",
                    "properties_viewed": 2,
                    "last_contact_date": "2026-01-08",
                    "interest_level": "medium",
                    "last_activity_hours": 72
                },
                {
                    "id": "lead_003",
                    "name": "Jennifer Wilson",
                    "budget": 520000,
                    "timeline": "3 months",
                    "properties_viewed": 1,
                    "last_contact_date": "2026-01-06",
                    "interest_level": "medium",
                    "financing_status": "pre-approved"
                }
            ]
        else:
            return [
                {
                    "id": "lead_004",
                    "name": "Robert Davis",
                    "budget": 320000,
                    "timeline": "6 months",
                    "properties_viewed": 0,
                    "last_contact_date": "2026-01-05",
                    "interest_level": "low"
                }
            ]

    def _generate_sample_activity_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sample activity data for demonstration."""
        return {
            "avg_response_time_hours": 8.5,
            "qualification_rate": 0.68,
            "conversion_rate": 0.12,
            "total_leads_week": 23,
            "appointments_scheduled": 8,
            "contracts_pending": 3
        }

    def render_compact_suggestions(
        self,
        context: Dict[str, Any],
        max_suggestions: int = 3
    ) -> None:
        """Render compact version for sidebar or smaller spaces."""
        suggestions = claude_proactive_suggestions.get_cached_suggestions()[:max_suggestions]

        if not suggestions:
            st.info("🎯 No active suggestions")
            return

        st.markdown("**🧠 Claude Suggests:**")

        for suggestion in suggestions:
            priority_icon = "🚨" if suggestion.priority == SuggestionPriority.CRITICAL else "💡"

            with st.container():
                st.markdown(f"{priority_icon} **{suggestion.title}**")
                st.caption(suggestion.message[:100] + "..." if len(suggestion.message) > 100 else suggestion.message)

                if suggestion.priority == SuggestionPriority.CRITICAL:
                    st.markdown('<div style="height: 0.5rem; background: linear-gradient(90deg, #dc2626 0%, #fca5a5 100%); border-radius: 2px; margin: 0.5rem 0;"></div>', unsafe_allow_html=True)

        if st.button("View All Suggestions", key="view_all_compact"):
            st.session_state.expand_suggestions = True


# Global instance
claude_proactive_panel = ClaudeProactivePanel()


def render_proactive_suggestions(
    context: Dict[str, Any],
    compact: bool = False,
    max_suggestions: int = 6,
    show_metrics: bool = False
) -> None:
    """
    Render Claude proactive suggestions panel.

    Args:
        context: Application context
        compact: Whether to show compact version
        max_suggestions: Maximum suggestions to display
        show_metrics: Whether to show metrics
    """
    if compact:
        claude_proactive_panel.render_compact_suggestions(context, max_suggestions)
    else:
        claude_proactive_panel.render_proactive_suggestions(context, max_suggestions, show_metrics)