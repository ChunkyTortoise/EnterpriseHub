"""
UI Rendering Service - Streamlit sidebar panel and chat interface rendering.

Extracted from ClaudeAssistant god class.
"""

import asyncio
from typing import Any, Dict, Optional

import streamlit as st

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)


class UIRenderingService:
    """Handles Streamlit UI rendering for the Claude assistant sidebar."""

    def __init__(
        self,
        orchestrator,
        memory_service: MemoryService,
        analytics: AnalyticsService,
        market_context_service,
    ):
        self.orchestrator = orchestrator
        self.memory_service = memory_service
        self.analytics = analytics
        self.market_context_service = market_context_service

    def initialize_state(self):
        if "assistant_greeted" not in st.session_state:
            st.session_state.assistant_greeted = False
        if "claude_history" not in st.session_state:
            st.session_state.claude_history = []

    def render_sidebar_panel(self, hub_name: str, market: str, leads: Dict[str, Any]):
        """Renders the persistent sidebar intelligence panel."""
        with st.sidebar:
            st.markdown("---")
            st.markdown(
                f"""
            <div style='background: linear-gradient(135deg, #6D28D9 0%, #4C1D95 100%);
                        padding: 1.25rem; border-radius: 12px; color: white; margin-bottom: 1rem;
                        box-shadow: 0 4px 15px rgba(109, 40, 217, 0.3); position: relative; overflow: hidden;'>
                <div style='position: absolute; top: -10px; right: -10px; font-size: 3rem; opacity: 0.2;'>🤖</div>
                <h3 style='color: white !important; margin: 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;'>
                    <span>Claude Intelligence</span>
                    <span style='background: #10B981; width: 8px; height: 8px; border-radius: 50%; display: inline-block; animation: pulse 2s infinite;'></span>
                </h3>
                <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 0.8rem; line-height: 1.4;'>
                    Context: <b>{hub_name}</b> ({market})
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            insight = self.get_insight(hub_name, leads)
            st.info(f"💡 **Claude's Note:** {insight}")

            self.render_chat_interface(leads, market)

    def get_insight(self, hub_name: str, leads: Dict[str, Any]) -> str:
        """Generates a contextual insight based on current hub and data."""
        clean_hub = hub_name.split(" ", 1)[1] if " " in hub_name else hub_name

        if "Executive" in clean_hub:
            hot_leads = sum(1 for l in leads.values() if l and l.get("classification") == "hot")
            return f"Jorge, your pipeline has {hot_leads} leads ready for immediate closing. Most are focused on the Austin downtown cluster."

        elif "Lead Intelligence" in clean_hub:
            selected = st.session_state.get("selected_lead_name", "-- Select a Lead --")
            if selected != "-- Select a Lead --":
                try:
                    lead_options = st.session_state.get("lead_options", {})
                    lead_data = lead_options.get(selected, {})
                    lead_id = lead_data.get("lead_id")

                    extra_context = ""
                    if lead_id:
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                        context = loop.run_until_complete(self.memory_service.get_context(lead_id))
                        if context.get("relevant_knowledge"):
                            extra_context = f"\n\n**🧠 Graphiti Recall:** {context['relevant_knowledge']}"

                except Exception as e:
                    logger.debug(f"Graphiti memory fetch failed for {selected}: {e}")
                    extra_context = ""

                if "Sarah Chen" in selected:
                    return f"Sarah is a data-driven Apple engineer with a hard 45-day deadline. She's prioritizing Teravista for its commute efficiency.{extra_context}"
                elif "David Kim" in selected:
                    return f"David is a seasoned investor focused on cash-on-cash return. Recommend sending the off-market ROI brief.{extra_context}"
                return f"I've analyzed {selected}'s recent activity. They are showing high engagement but haven't booked a tour yet.{extra_context}"
            return "Select a lead to see my behavioral breakdown and conversion probability."

        elif "Automation" in clean_hub:
            return "All GHL workflows are operational. I've detected a 15% increase in response rates since we switched to 'Natural' tone."

        elif "Sales" in clean_hub:
            return "Ready to generate contracts. I've updated the buyer agreement template with the latest TX compliance rules."

        return "I'm monitoring all data streams to ensure you have the ultimate competitive advantage."

    def render_chat_interface(self, leads: Dict[str, Any], market: str):
        """Renders the interactive 'Ask Claude' expander."""
        with st.expander("Commands & Queries", expanded=False):
            query = st.text_input(
                "How can I help Jorge?", placeholder="Ex: Draft text for Sarah", key="claude_sidebar_chat"
            )
            if query:
                self._handle_query(query, leads, market)

    def _handle_query(self, query: str, leads: Dict[str, Any], market: str):
        """Processes user query and displays response using Claude Orchestrator."""
        with st.spinner("Claude is thinking..."):
            if self.orchestrator:
                try:
                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    market_context = loop.run_until_complete(self.market_context_service.get_market_context(market))

                    context = {
                        "market": market,
                        "market_context": market_context,
                        "current_hub": st.session_state.get("current_hub", "Unknown"),
                        "selected_lead": st.session_state.get("selected_lead_name", "None"),
                        "market_specializations": market_context.get("specializations", {}),
                        "top_neighborhoods": [n["name"] for n in market_context.get("top_neighborhoods", [])[:3]],
                        "major_employers": [e["name"] for e in market_context.get("major_employers", [])[:3]],
                        "market_indicators": market_context.get("market_indicators", {}),
                    }

                    response_obj = loop.run_until_complete(self.orchestrator.chat_query(query, context))

                    loop.run_until_complete(
                        self.analytics.track_llm_usage(
                            location_id="demo_location",
                            model=response_obj.model or "claude-3-5-sonnet",
                            provider=response_obj.provider or "claude",
                            input_tokens=response_obj.input_tokens or 0,
                            output_tokens=response_obj.output_tokens or 0,
                            cached=False,
                        )
                    )

                    response = response_obj.content
                except Exception as e:
                    response = f"I encountered an error processing your request: {str(e)}"
            else:
                q_lower = query.lower()
                if "draft" in q_lower or "text" in q_lower or "sms" in q_lower:
                    response = "I've drafted an SMS: 'Hi! Jorge and I found a perfect match. Want to see photos?'"
                else:
                    response = "I'm cross-referencing your GHL data. Should I run a diagnostic?"

            st.markdown(
                f"""
            <div style='background: #f3f4f6; padding: 10px; border-radius: 8px; border-left: 3px solid #6D28D9; margin-top: 10px;'>
                <p style='font-size: 0.85rem; color: #1f2937; margin: 0;'>{response}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            if "Draft" in response or "script" in response.lower():
                if st.button("🚀 Push to GHL"):
                    st.toast("Draft synced to GHL!")

    def greet_user(self, name: str = "Jorge"):
        """Shows the one-time greeting toast."""
        if not st.session_state.assistant_greeted:
            st.toast(
                f"Hello {name}! 👋 I'm Claude, your AI partner. I've indexed your GHL context and I'm ready to work.",
                icon="🤖",
            )
            st.session_state.assistant_greeted = True
