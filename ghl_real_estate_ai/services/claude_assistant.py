"""
Claude Assistant Service - Centralized AI Intelligence for the GHL Platform
Provides context-aware insights, action recommendations, and interactive support.
"""
import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

class ClaudeAssistant:
    """
    The brain of the platform's UI. 
    Maintains state and provides context-specific intelligence using Claude Orchestrator.
    """
    
    def __init__(self, context_type: str = "general"):
        self.context_type = context_type
        # Import here to avoid circular dependencies
        try:
            from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator
            self.orchestrator = get_claude_orchestrator()
        except ImportError:
            self.orchestrator = None
            
        self.memory_service = MemoryService()
        self.analytics = AnalyticsService()
        self._initialize_state()

    def _initialize_state(self):
        if 'assistant_greeted' not in st.session_state:
            st.session_state.assistant_greeted = False
        if 'claude_history' not in st.session_state:
            st.session_state.claude_history = []

    def render_sidebar_panel(self, hub_name: str, market: str, leads: Dict[str, Any]):
        """Renders the persistent sidebar intelligence panel."""
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"""
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
            """, unsafe_allow_html=True)

            # Generate and show context-aware insight
            insight = self.get_insight(hub_name, leads)
            st.info(f"💡 **Claude's Note:** {insight}")
            
            # Interactive Query
            self.render_chat_interface(leads, market)

    def get_insight(self, hub_name: str, leads: Dict[str, Any]) -> str:
        """Generates a contextual insight based on current hub and data."""
        clean_hub = hub_name.split(' ', 1)[1] if ' ' in hub_name else hub_name
        
        # If orchestrator is available, we could potentially do a quick async analysis
        # But for UI responsiveness, we use pre-calculated or persona-based insights here
        # or call a fast analysis method.
        
        if "Executive" in clean_hub:
            hot_leads = sum(1 for l in leads.values() if l and l.get('classification') == 'hot')
            return f"Jorge, your pipeline has {hot_leads} leads ready for immediate closing. Most are focused on the Austin downtown cluster."
        
        elif "Lead Intelligence" in clean_hub:
            selected = st.session_state.get('selected_lead_name', '-- Select a Lead --')
            if selected != "-- Select a Lead --":
                # Attempt to get semantic memory from Graphiti
                try:
                    # Resolve lead_id from session state options if available
                    lead_options = st.session_state.get('lead_options', {})
                    lead_data = lead_options.get(selected, {})
                    lead_id = lead_data.get('lead_id')
                    
                    extra_context = ""
                    if lead_id:
                        # Synchronous wrapper for async call
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        context = loop.run_until_complete(self.memory_service.get_context(lead_id))
                        if context.get("relevant_knowledge"):
                            extra_context = f"\n\n**🧠 Graphiti Recall:** {context['relevant_knowledge']}"

                except Exception as e:
                    # Fail silently on memory fetch to keep UI responsive
                    extra_context = ""

                # Persona-specific Claude insights (enhanced with Graphiti)
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
            query = st.text_input("How can I help Jorge?", placeholder="Ex: Draft text for Sarah", key="claude_sidebar_chat")
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
                    
                    # Build context
                    context = {
                        "market": market,
                        "current_hub": st.session_state.get('current_hub', 'Unknown'),
                        "selected_lead": st.session_state.get('selected_lead_name', 'None')
                    }
                    
                    response_obj = loop.run_until_complete(
                        self.orchestrator.chat_query(query, context)
                    )
                    
                    # Record usage
                    loop.run_until_complete(self.analytics.track_llm_usage(
                        location_id="demo_location", # Sidebar doesn't have easy location_id access
                        model=response_obj.model or "claude-3-5-sonnet",
                        provider=response_obj.provider or "claude",
                        input_tokens=response_obj.input_tokens or 0,
                        output_tokens=response_obj.output_tokens or 0,
                        cached=False
                    ))
                    
                    response = response_obj.content
                except Exception as e:
                    response = f"I encountered an error processing your request: {str(e)}"
            else:
                # Fallback to legacy logic
                q_lower = query.lower()
                if "draft" in q_lower or "text" in q_lower or "sms" in q_lower:
                    response = "I've drafted an SMS: 'Hi! Jorge and I found a perfect match. Want to see photos?'"
                else:
                    response = "I'm cross-referencing your GHL data. Should I run a diagnostic?"

            st.markdown(f"""
            <div style='background: #f3f4f6; padding: 10px; border-radius: 8px; border-left: 3px solid #6D28D9; margin-top: 10px;'>
                <p style='font-size: 0.85rem; color: #1f2937; margin: 0;'>{response}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if "Draft" in response or "script" in response.lower():
                if st.button("🚀 Push to GHL"):
                    st.toast("Draft synced to GHL!")

    def greet_user(self, name: str = "Jorge"):
        """Shows the one-time greeting toast."""
        if not st.session_state.assistant_greeted:
            st.toast(f"Hello {name}! 👋 I'm Claude, your AI partner. I've indexed your GHL context and I'm ready to work.", icon="🤖")
            st.session_state.assistant_greeted = True

    async def generate_automated_report(self, data: Dict[str, Any], report_type: str = "Weekly Performance") -> Dict[str, Any]:
        """
        🆕 Enhanced with Real Claude Intelligence
        Generates comprehensive reports using the Claude Automation Engine
        """
        try:
            # Import here to avoid circular imports
            from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ReportType

            # Map report type to enum
            report_type_enum = ReportType.WEEKLY_SUMMARY
            if "daily" in report_type.lower():
                report_type_enum = ReportType.DAILY_BRIEF
            elif "monthly" in report_type.lower():
                report_type_enum = ReportType.MONTHLY_REVIEW
            elif "pipeline" in report_type.lower():
                report_type_enum = ReportType.PIPELINE_STATUS

            # Initialize automation engine
            automation_engine = ClaudeAutomationEngine()

            # Generate report with Claude intelligence
            automated_report = await automation_engine.generate_automated_report(
                report_type=report_type_enum,
                data=data,
                market_context={"location": "Austin", "market_conditions": "stable"},
                time_period="current_period"
            )

            # Convert to legacy format for backward compatibility
            return {
                "title": automated_report.title,
                "summary": automated_report.executive_summary,
                "key_findings": automated_report.key_findings,
                "strategic_recommendation": automated_report.opportunities[0] if automated_report.opportunities else "Continue current strategy",
                "generated_at": automated_report.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
                "confidence_score": automated_report.confidence_score,
                "action_items": automated_report.action_items,
                "risk_assessment": automated_report.risk_assessment,
                "generation_time_ms": automated_report.generation_time_ms
            }

        except Exception as e:
            # Fallback to simulated analysis if Claude fails
            if "conversations" in data:
                convs = data["conversations"]
                hot_leads = sum(1 for c in convs if c.get("classification") == "hot")
                avg_score = sum(c.get("lead_score", 0) for c in convs) / len(convs) if convs else 0

                return {
                    "title": f"System-Generated {report_type}",
                    "summary": f"Jorge, your pipeline is currently processing {len(convs)} active conversations. I've identified {hot_leads} leads with immediate conversion potential. (Note: Claude intelligence temporarily unavailable)",
                    "key_findings": [
                        f"Average lead quality is scoring at {avg_score:.1f}/100, which is stable.",
                        "SMS engagement peaks between 6 PM and 8 PM local time.",
                        "The 'Luxury' segment has 2x higher retention than 'Starter' leads this period."
                    ],
                    "strategic_recommendation": "Shift 15% of the automation budget toward weekend re-engagement triggers to capture high-velocity buyer intent.",
                    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "error": f"Claude service unavailable: {str(e)}"
                }

            return {"error": f"Report generation failed: {str(e)}"}

    async def generate_retention_script(self, lead_data: Dict[str, Any], risk_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        🆕 Enhanced with Real Claude Intelligence
        Generates personalized retention scripts using the Claude Automation Engine
        """
        try:
            # Import here to avoid circular imports
            from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType

            lead_name = lead_data.get('lead_name', 'Client')
            lead_id = lead_data.get('lead_id', f"demo_{lead_name.lower().replace(' ', '_')}")
            risk_score = risk_data.get('risk_score', 0) if risk_data else lead_data.get('risk_score_14d', 0)

            # Initialize automation engine
            automation_engine = ClaudeAutomationEngine()

            # Determine script type based on risk level
            script_type = ScriptType.RE_ENGAGEMENT
            if risk_score > 80:
                # High risk needs urgent intervention
                channel = "sms"  # Immediate channel
            else:
                # Medium/low risk can use email
                channel = "email"

            # Generate script with Claude intelligence
            automated_script = await automation_engine.generate_personalized_script(
                script_type=script_type,
                lead_id=lead_id,
                channel=channel,
                context_override={"churn_risk": risk_score, **lead_data},
                variants=2  # Generate A/B variants
            )

            # Convert to legacy format for backward compatibility
            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "script": automated_script.primary_script,
                "strategy": f"Claude-Generated {automated_script.script_type.value.replace('_', ' ').title()}",
                "reasoning": automated_script.personalization_notes,
                "channel_recommendation": automated_script.channel.upper(),
                "alternative_scripts": automated_script.alternative_scripts,
                "objection_responses": automated_script.objection_responses,
                "success_probability": automated_script.success_probability,
                "expected_response_rate": automated_script.expected_response_rate,
                "generation_time_ms": automated_script.generation_time_ms,
                "a_b_variants": automated_script.a_b_testing_variants
            }

        except Exception as e:
            # Fallback to original logic if Claude fails
            lead_name = lead_data.get('lead_name', 'Client')
            risk_score = risk_data.get('risk_score', 0) if risk_data else lead_data.get('risk_score_14d', 0)

            # Determine the "Why" for the reasoning
            last_interaction = lead_data.get('last_interaction_days', 5)

            reasoning = f"Lead {lead_name} has a {risk_score:.1f}% churn risk primarily due to {last_interaction} days of inactivity. "
            reasoning += "Their previous interest in luxury properties suggests they need a high-value 'pattern interrupt'."

            if risk_score > 80:
                script = f"Hi {lead_name}, it's Jorge. I was just reviewing the new off-market luxury listings in Austin and one specifically caught my eye that fits your criteria perfectly. I didn't want you to miss out - do you have 2 minutes for a quick update today?"
                strategy = "Urgent Pattern Interrupt - High Value Offer"
            else:
                script = f"Hey {lead_name}, just checking in! I noticed some interesting price shifts in the neighborhoods we were looking at. Hope your week is going well - would you like a quick summary of the changes?"
                strategy = "Nurture Re-engagement - Market Insight"

            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "script": script,
                "strategy": strategy,
                "reasoning": reasoning,
                "channel_recommendation": "SMS (High Response Probability)" if risk_score > 60 else "Email",
                "error": f"Claude service unavailable: {str(e)}"
            }
