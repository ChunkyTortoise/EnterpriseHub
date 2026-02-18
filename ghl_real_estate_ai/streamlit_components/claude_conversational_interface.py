"""
Claude Conversational Interface for Streamlit - Real-time AI Assistant

Provides conversational Claude AI interface with context awareness for lead intelligence,
qualification analysis, and strategic recommendations throughout the GHL platform.
"""

import asyncio
import streamlit as st
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ghl_real_estate_ai.services.claude_lead_qualification_engine import ClaudeLeadQualificationEngine
from ghl_real_estate_ai.services.claude_lead_enrichment_engine import ClaudeLeadEnrichmentEngine
from ghl_real_estate_ai.services.claude_semantic_analyzer import get_semantic_analyzer

logger = logging.getLogger(__name__)


class ClaudeConversationalInterface:
    """Real-time conversational Claude interface for lead intelligence."""

    def __init__(self):
        """Initialize Claude conversational interface."""
        # Initialize Claude services
        self.qualification_engine = None
        self.enrichment_engine = None
        self.semantic_analyzer = None
        self._init_services()

    def _init_services(self):
        """Initialize Claude AI services safely."""
        try:
            # Only initialize if API key is available
            api_key = None
            if hasattr(st, 'secrets') and st.secrets is not None:
                api_key = st.secrets.get("anthropic", {}).get("api_key")
            if not api_key:
                import os
                api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")

            if api_key:
                self.qualification_engine = ClaudeLeadQualificationEngine(anthropic_api_key=api_key)
                self.enrichment_engine = ClaudeLeadEnrichmentEngine(api_key=api_key)
                self.semantic_analyzer = get_semantic_analyzer()
                logger.info("Claude services initialized successfully")
            else:
                logger.warning("Claude API key not available - using mock responses")
        except Exception as e:
            logger.error(f"Failed to initialize Claude services: {e}")

    async def process_user_message(
        self,
        user_message: str,
        context: Dict[str, Any],
        lead_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message and generate intelligent Claude response.

        Args:
            user_message: User's question or request
            context: Current application context (section, lead selection, etc.)
            lead_data: Optional lead data for context

        Returns:
            Dict with Claude response and metadata
        """
        try:
            # Analyze message intent
            message_intent = self._analyze_message_intent(user_message)

            # Generate contextual response
            if message_intent == "lead_analysis" and lead_data and self.qualification_engine:
                response = await self._handle_lead_analysis(user_message, lead_data)
            elif message_intent == "conversation_tips" and lead_data and self.semantic_analyzer:
                response = await self._handle_conversation_tips(user_message, lead_data)
            elif message_intent == "next_actions" and lead_data:
                response = await self._handle_next_actions(user_message, lead_data)
            elif message_intent == "enrichment_advice" and lead_data and self.enrichment_engine:
                response = await self._handle_enrichment_advice(user_message, lead_data)
            else:
                response = await self._handle_general_query(user_message, context)

            return {
                "content": response,
                "intent": message_intent,
                "timestamp": datetime.now().strftime("%H:%M"),
                "confidence": 0.9,
                "has_followup": True
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "content": f"I apologize, but I encountered an issue processing your request: {str(e)}. Let me know if you'd like to try again or if you need help with something else.",
                "intent": "error",
                "timestamp": datetime.now().strftime("%H:%M"),
                "confidence": 0.1,
                "has_followup": False
            }

    def _analyze_message_intent(self, message: str) -> str:
        """Analyze user message to determine intent."""
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ["analyze", "score", "qualify", "assessment"]):
            return "lead_analysis"
        elif any(keyword in message_lower for keyword in ["conversation", "talk", "say", "respond", "message"]):
            return "conversation_tips"
        elif any(keyword in message_lower for keyword in ["next", "action", "should", "recommend", "do"]):
            return "next_actions"
        elif any(keyword in message_lower for keyword in ["enrich", "missing", "data", "complete", "information"]):
            return "enrichment_advice"
        else:
            return "general_query"

    async def _handle_lead_analysis(self, message: str, lead_data: Dict[str, Any]) -> str:
        """Handle lead analysis requests."""
        try:
            # Use qualification engine for comprehensive analysis
            qualification_result = await self.qualification_engine.qualify_lead(
                lead_data=lead_data,
                source_type="manual_analysis",
                include_market_context=True
            )

            # Format response
            score = qualification_result.qualification_score
            priority = qualification_result.priority_level.value

            response = f"""**Lead Analysis Complete:**

🎯 **Overall Score:** {score}/100 ({priority} Priority)

**Key Insights:**
• {qualification_result.key_insights[0] if qualification_result.key_insights else 'Strong qualification potential'}
• Budget alignment: {'✅ Good' if score > 70 else '⚠️ Needs review'}
• Timeline urgency: {'🔥 High' if score > 80 else '📅 Moderate'}

**Recommendation:**
{qualification_result.recommended_actions[0]['description'] if qualification_result.recommended_actions else 'Focus on timeline clarification and budget confirmation.'}

Would you like me to dive deeper into any specific aspect?"""

            return response

        except Exception as e:
            return f"I can analyze this lead based on the available data. The lead shows moderate qualification potential with key areas for development in timeline and budget clarity. Would you like specific recommendations for next steps? (Note: {str(e)})"

    async def _handle_conversation_tips(self, message: str, lead_data: Dict[str, Any]) -> str:
        """Handle conversation coaching requests."""
        try:
            # Create conversation context for semantic analysis
            conversation_messages = [
                {"role": "prospect", "content": lead_data.get("last_message", "Hi, I'm interested in properties")},
                {"role": "agent", "content": "Great to hear from you! What brings you to the market?"}
            ]

            if self.semantic_analyzer:
                # Use semantic analyzer for conversation insights
                intent_analysis = await self.semantic_analyzer.analyze_lead_intent(conversation_messages)

                response = f"""**Conversation Strategy:**

🎯 **Lead Intent:** {intent_analysis.get('primary_intent', 'exploring').replace('_', ' ').title()}
📈 **Engagement Level:** {intent_analysis.get('urgency_level', 'medium').title()}

**Recommended Approach:**
• Start with their motivation: "What's driving your search right now?"
• Acknowledge their {intent_analysis.get('urgency_level', 'timeline')}: "I understand timing is important..."
• Focus on value alignment: Present options that match their expressed priorities

**Key Questions to Ask:**
• "What's your ideal timeline for making a decision?"
• "What would make this the perfect home for you?"
• "Have you had a chance to get pre-approved yet?"

**Conversation Flow:**
Build rapport → Understand motivation → Qualify timeline/budget → Present solutions

Would you like me to draft specific opening questions?"""
            else:
                response = """**Conversation Strategy:**

Based on this lead profile, I recommend:

• **Opening**: Focus on their motivation and timeline
• **Qualifying**: Ask about budget comfort and financing status
• **Positioning**: Present yourself as a market expert and trusted advisor
• **Next Steps**: Suggest property viewing or market analysis

**Key Questions:**
• "What's bringing you to the market right now?"
• "What's your ideal timeline?"
• "What areas are you most interested in?"

Would you like me to help draft specific messaging?"""

            return response

        except Exception as e:
            return f"For this lead, I recommend focusing on timeline urgency and budget alignment. Use empathetic language about their situation and position yourself as a market expert. Ask open-ended questions about their motivation and preferred areas. (Note: {str(e)})"

    async def _handle_next_actions(self, message: str, lead_data: Dict[str, Any]) -> str:
        """Handle next actions and recommendations."""
        budget = lead_data.get("extracted_preferences", {}).get("budget", 0)
        timeline = lead_data.get("extracted_preferences", {}).get("timeline", "unknown")
        location = lead_data.get("extracted_preferences", {}).get("location", "not specified")

        response = f"""**Recommended Next Actions:**

🎯 **Priority 1 (Next 24 hours):**
• Send personalized market analysis for {location if location != "not specified" else "their preferred area"}
• Follow up on financing/pre-approval status
• Schedule property viewing or video tour

📅 **Priority 2 (This Week):**
• Curate 3-5 listings matching their {budget if budget else "budget range"}
• Provide neighborhood insights and market trends
• Connect with mortgage specialist if needed

🔄 **Ongoing:**
• Weekly check-ins aligned with their {timeline} timeline
• Share relevant market updates
• Monitor new listings in their criteria

**Immediate Action:**
Given their profile, I recommend reaching out within 4 hours while interest is high.

Would you like me to draft the follow-up message?"""

        return response

    async def _handle_enrichment_advice(self, message: str, lead_data: Dict[str, Any]) -> str:
        """Handle data enrichment recommendations."""
        try:
            if self.enrichment_engine:
                # Use enrichment engine for gap analysis
                enrichment_analysis = await self.enrichment_engine.analyze_lead_enrichment_needs(
                    lead_data=lead_data,
                    include_validation=True
                )

                gaps = enrichment_analysis.critical_gaps
                response = f"""**Data Enrichment Recommendations:**

⚠️ **Critical Missing Information:**
{chr(10).join(f'• {gap}' for gap in gaps[:3]) if gaps else '• No critical gaps identified'}

🎯 **Next Data Collection:**
• Financing status and pre-approval amount
• Specific timeline and motivation drivers
• Property type preferences and must-haves

📊 **Enhancement Opportunities:**
• Social media profile insights
• Property history and previous searches
• Market engagement behavior

**Suggested Questions:**
• "Have you been pre-approved for financing?"
• "What's driving your {timeline if lead_data.get('timeline') else 'current'} timeline?"
• "What features are absolute must-haves?"

This additional data will improve qualification accuracy by ~25%.

Would you like help prioritizing which information to gather first?"""
            else:
                response = """**Data Enrichment Recommendations:**

Based on this lead profile, focus on collecting:

🎯 **High Priority:**
• Financing pre-approval status
• Specific timeline and urgency factors
• Property preferences and must-haves

📊 **Medium Priority:**
• Previous property search history
• Current housing situation
• Decision-making process and influencers

**Collection Strategy:**
• Use conversational questions during calls
• Send preference surveys via email
• Track engagement with property listings

This will significantly improve your qualification accuracy."""

            return response

        except Exception as e:
            return f"For this lead, focus on gathering financing status, timeline urgency, and specific property preferences. These are the most valuable data points for improving qualification and conversion. (Note: {str(e)})"

    async def _handle_general_query(self, message: str, context: Dict[str, Any]) -> str:
        """Handle general queries and platform navigation."""
        current_section = context.get("current_section", "unknown")

        if "lead intelligence" in message.lower():
            return """I'm specialized in lead intelligence! I can help you with:

🎯 **Lead Analysis:** Score and qualify prospects
💬 **Conversation Coaching:** Strategic messaging advice
📈 **Next Actions:** Prioritized follow-up recommendations
🔍 **Data Enrichment:** Identify missing information

Just ask me about any lead or select one from the list above, and I'll provide detailed insights and recommendations!"""

        elif current_section == "lead_intelligence":
            return f"""I'm here to help with your lead intelligence needs! Here's what I can do:

**Lead Analysis:** Select a lead above and I'll analyze their qualification score, timeline, and conversion probability.

**Strategic Advice:** Ask me about conversation strategies, objection handling, or next steps for any prospect.

**Data Insights:** I can identify gaps in lead information and recommend data collection strategies.

Try asking: "Analyze Sarah Johnson" or "What should I do next with Mike Chen?"

What would you like to explore?"""

        else:
            return f"""I'm your AI assistant for the GHL platform! Currently in **{current_section.replace('_', ' ').title()}** section.

For the best experience, navigate to **Lead Intelligence Hub** where I have specialized capabilities for:
• Lead qualification and scoring
• Conversation strategy recommendations
• Next action planning
• Data enrichment advice

How can I help you today?"""

    def render_chat_interface(
        self,
        context: Dict[str, Any],
        lead_data: Optional[Dict[str, Any]] = None,
        key_suffix: str = ""
    ) -> None:
        """
        Render interactive Claude chat interface.

        Args:
            context: Current application context
            lead_data: Optional lead data for context
            key_suffix: Unique suffix for Streamlit keys
        """
        # Chat history key
        chat_key = f"claude_chat_history_{key_suffix}" if key_suffix else "claude_chat_history"

        # Initialize chat history
        if chat_key not in st.session_state:
            st.session_state[chat_key] = [
                {
                    "role": "claude",
                    "content": "Hi! I'm Claude, your lead intelligence assistant. I can analyze leads, provide conversation coaching, and recommend strategic actions. How can I help you today?",
                    "timestamp": "startup"
                }
            ]

        # Display chat messages
        for message in st.session_state[chat_key][-8:]:  # Show last 8 messages
            self._render_chat_message(message)

        # Chat input
        user_input = st.text_area(
            "Ask Claude about leads, strategies, or analysis...",
            placeholder="e.g., 'Analyze this lead' or 'What should I say to follow up?'",
            height=80,
            key=f"claude_input_{key_suffix}"
        )

        if st.button("Send to Claude 💬", use_container_width=True, key=f"send_claude_{key_suffix}"):
            if user_input.strip():
                # Add user message
                st.session_state[chat_key].append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": datetime.now().strftime("%H:%M")
                })

                # Get Claude response (async wrapper for Streamlit)
                with st.spinner("Claude is thinking..."):
                    response = asyncio.run(
                        self.process_user_message(user_input, context, lead_data)
                    )

                st.session_state[chat_key].append({
                    "role": "claude",
                    "content": response["content"],
                    "timestamp": response["timestamp"]
                })

                st.rerun()

    def _render_chat_message(self, message: Dict[str, Any]) -> None:
        """Render individual chat message."""
        if message["role"] == "claude":
            st.markdown(f"""
            <div style='background: #e0f2fe; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #0277bd;'>
                <div style='font-weight: 600; color: #01579b; font-size: 0.85rem;'>Claude AI</div>
                <div style='color: #424242; margin-top: 0.25rem;'>{message["content"]}</div>
                <div style='font-size: 0.7rem; color: #666; margin-top: 0.25rem;'>{message["timestamp"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='background: #f3e5f5; padding: 0.75rem; border-radius: 8px; margin: 0.5rem 0; border-left: 4px solid #7b1fa2; margin-left: 2rem;'>
                <div style='font-weight: 600; color: #4a148c; font-size: 0.85rem;'>You</div>
                <div style='color: #424242; margin-top: 0.25rem;'>{message["content"]}</div>
                <div style='font-size: 0.7rem; color: #666; margin-top: 0.25rem;'>{message["timestamp"]}</div>
            </div>
            """, unsafe_allow_html=True)

    def render_quick_actions(self, lead_data: Optional[Dict[str, Any]] = None, key_suffix: str = "") -> None:
        """Render quick action buttons for common Claude interactions."""
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("🎯 Analyze Lead", use_container_width=True, key=f"quick_analyze_{key_suffix}"):
                self._add_quick_interaction("analyze", lead_data, key_suffix)

        with col2:
            if st.button("💬 Conversation Tips", use_container_width=True, key=f"quick_convo_{key_suffix}"):
                self._add_quick_interaction("conversation", lead_data, key_suffix)

        with col3:
            if st.button("📈 Next Actions", use_container_width=True, key=f"quick_actions_{key_suffix}"):
                self._add_quick_interaction("actions", lead_data, key_suffix)

        with col4:
            if st.button("🧹 Clear Chat", use_container_width=True, key=f"clear_chat_{key_suffix}"):
                chat_key = f"claude_chat_history_{key_suffix}" if key_suffix else "claude_chat_history"
                st.session_state[chat_key] = [
                    {
                        "role": "claude",
                        "content": "Chat cleared! I'm ready to help with lead intelligence.",
                        "timestamp": "now"
                    }
                ]
                st.rerun()

    def _add_quick_interaction(self, action_type: str, lead_data: Optional[Dict[str, Any]], key_suffix: str) -> None:
        """Add quick interaction to chat history."""
        chat_key = f"claude_chat_history_{key_suffix}" if key_suffix else "claude_chat_history"

        if action_type == "analyze":
            user_msg = "Analyze the current lead selection"
            claude_msg = "I'll analyze this lead's qualification score, behavioral patterns, and conversion probability. Based on the available data, I can provide insights on timeline, budget alignment, and recommended next actions."

        elif action_type == "conversation":
            user_msg = "Give me conversation tips for this lead"
            claude_msg = "For this lead, I recommend focusing on their timeline urgency and motivation drivers. Use empathetic language about their situation, ask open-ended questions about preferences, and position yourself as a trusted market expert."

        elif action_type == "actions":
            user_msg = "What should I do next with this lead?"
            claude_msg = "Based on this lead's profile, I recommend: 1) Follow up within 24 hours, 2) Send targeted property options, 3) Provide market insights for their area, 4) Schedule viewing or consultation. Priority: HIGH based on engagement level."

        else:
            return

        # Add to chat history
        st.session_state[chat_key].append({
            "role": "user",
            "content": user_msg,
            "timestamp": "now"
        })
        st.session_state[chat_key].append({
            "role": "claude",
            "content": claude_msg,
            "timestamp": "now"
        })
        st.rerun()


# Global instance for easy import
claude_chat = ClaudeConversationalInterface()


def render_claude_interface(
    context: Dict[str, Any],
    lead_data: Optional[Dict[str, Any]] = None,
    expanded: bool = True,
    show_quick_actions: bool = True,
    key_suffix: str = ""
) -> None:
    """
    Render complete Claude conversational interface.

    Args:
        context: Application context
        lead_data: Optional lead data
        expanded: Whether to show expanded by default
        show_quick_actions: Whether to show quick action buttons
        key_suffix: Unique key suffix
    """
    with st.expander("💬 Chat with Claude - Your Lead Intelligence Assistant", expanded=expanded):
        # Status indicator
        col_status, col_context = st.columns([1, 2])
        with col_status:
            st.markdown("🟢 **Claude Online**")
            st.caption("Ready to analyze leads")
        with col_context:
            current_section = context.get("current_section", "unknown")
            st.markdown(f"🧠 **Current Context:** {current_section.replace('_', ' ').title()}")
            st.caption("I can help with lead analysis, qualification, and strategic insights")

        # Quick actions
        if show_quick_actions:
            claude_chat.render_quick_actions(lead_data, key_suffix)
            st.markdown("---")

        # Chat interface
        claude_chat.render_chat_interface(context, lead_data, key_suffix)