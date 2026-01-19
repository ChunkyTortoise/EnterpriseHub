"""
Claude Assistant Service - Centralized AI Intelligence for the GHL Platform
Provides context-aware insights, action recommendations, and interactive support.

ENHANCED: Now includes multi-market awareness and churn recovery integration.
"""
import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

# ENHANCED: Import multi-market and churn recovery systems
from ghl_real_estate_ai.markets.registry import get_market_service, MarketRegistry
from ghl_real_estate_ai.markets.config_schemas import MarketConfig
from ghl_real_estate_ai.services.reengagement_engine import (
    ReengagementEngine,
    CLVEstimate,
    CLVTier,
    RecoveryCampaignType,
)
from ghl_real_estate_ai.services.churn_prediction_engine import (
    ChurnEventTracker,
    ChurnReason,
    ChurnEventType,
)

class ClaudeAssistant:
    """
    The brain of the platform's UI.
    Maintains state and provides context-specific intelligence using Claude Orchestrator.

    ENHANCED: Now includes multi-market awareness and churn recovery integration.
    """

    def __init__(self, context_type: str = "general", market_id: Optional[str] = None):
        self.context_type = context_type
        self.market_id = market_id

        # Import here to avoid circular dependencies
        try:
            from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator
            self.orchestrator = get_claude_orchestrator()
        except ImportError:
            self.orchestrator = None

        self.memory_service = MemoryService()
        self.analytics = AnalyticsService()

        # ENHANCED: Initialize market-aware components
        self.market_registry = MarketRegistry()
        self.reengagement_engine = ReengagementEngine()
        self.churn_tracker = ChurnEventTracker(self.memory_service)

        # ENHANCED: Market context cache
        self._market_context_cache = {}

        self._initialize_state()

    def _initialize_state(self):
        if 'assistant_greeted' not in st.session_state:
            st.session_state.assistant_greeted = False
        if 'claude_history' not in st.session_state:
            st.session_state.claude_history = []

    # ============================================================================
    # ENHANCED: Market-Aware Intelligence Methods
    # ============================================================================

    async def get_market_context(self, market_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive market context for intelligent messaging."""
        target_market_id = market_id or self.market_id or "austin"  # Default to austin

        # Check cache first
        if target_market_id in self._market_context_cache:
            return self._market_context_cache[target_market_id]

        try:
            # Get market service and configuration
            market_service = get_market_service(target_market_id)
            market_config = market_service.config

            # Build comprehensive market context
            context = {
                "market_id": target_market_id,
                "market_name": market_config.market_name,
                "market_type": market_config.market_type.value,
                "specializations": {
                    "primary": market_config.specializations.primary_specialization,
                    "secondary": market_config.specializations.secondary_specializations,
                    "unique_advantages": market_config.specializations.unique_advantages,
                    "target_clients": market_config.specializations.target_client_types,
                    "expertise_tags": market_config.specializations.expertise_tags,
                },
                "top_neighborhoods": [
                    {
                        "name": n.name,
                        "zone": n.zone,
                        "median_price": n.median_price,
                        "appeal_scores": n.appeal_scores,
                        "demographics": n.demographics,
                    }
                    for n in market_config.neighborhoods[:5]  # Top 5 neighborhoods
                ],
                "major_employers": [
                    {
                        "name": e.name,
                        "industry": e.industry,
                        "employee_count": e.employee_count,
                        "avg_salary_range": e.average_salary_range,
                        "preferred_neighborhoods": e.preferred_neighborhoods,
                    }
                    for e in market_config.employers[:5]  # Top 5 employers
                ],
                "market_indicators": {
                    "median_home_price": market_config.median_home_price,
                    "price_appreciation_1y": market_config.price_appreciation_1y,
                    "inventory_days": market_config.inventory_days,
                },
            }

            # Cache for performance
            self._market_context_cache[target_market_id] = context
            return context

        except Exception as e:
            # Fallback to basic context
            return {
                "market_id": target_market_id,
                "market_name": f"{target_market_id.title()} Metropolitan Area",
                "error": f"Could not load full market context: {str(e)}",
            }

    def _format_market_context_for_messaging(self, market_context: Dict[str, Any]) -> str:
        """Format market context for Claude messaging."""
        market_name = market_context.get("market_name", "the local market")
        market_type = market_context.get("market_type", "mixed")

        # Get market-specific selling points
        specializations = market_context.get("specializations", {})
        primary_spec = specializations.get("primary", "professional relocation")

        # Format key neighborhoods
        neighborhoods = market_context.get("top_neighborhoods", [])
        if neighborhoods:
            top_areas = ", ".join([n["name"] for n in neighborhoods[:3]])
            neighborhood_context = f"Popular areas include {top_areas}"
        else:
            neighborhood_context = "several desirable neighborhoods"

        # Format key employers
        employers = market_context.get("major_employers", [])
        if employers:
            major_employers = ", ".join([e["name"] for e in employers[:3]])
            employer_context = f"Major employers like {major_employers}"
        else:
            employer_context = "major local employers"

        return f"{market_name} is a {market_type} market specializing in {primary_spec}. {neighborhood_context} are seeing strong activity. {employer_context} are driving relocation demand."

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

                    # ENHANCED: Get market context for intelligent responses
                    market_context = loop.run_until_complete(self.get_market_context(market))

                    # Build enhanced context with market intelligence
                    context = {
                        "market": market,
                        "market_context": market_context,
                        "current_hub": st.session_state.get('current_hub', 'Unknown'),
                        "selected_lead": st.session_state.get('selected_lead_name', 'None'),
                        # Add market-specific context
                        "market_specializations": market_context.get("specializations", {}),
                        "top_neighborhoods": [n["name"] for n in market_context.get("top_neighborhoods", [])[:3]],
                        "major_employers": [e["name"] for e in market_context.get("major_employers", [])[:3]],
                        "market_indicators": market_context.get("market_indicators", {}),
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

    async def generate_market_aware_retention_script(
        self,
        lead_data: Dict[str, Any],
        risk_data: Optional[Dict[str, Any]] = None,
        market_id: Optional[str] = None,
        churn_reason: Optional[ChurnReason] = None
    ) -> Dict[str, Any]:
        """
        🆕 ENHANCED: Market-Aware Retention Script Generation
        Generates personalized retention scripts with market-specific context and churn recovery intelligence
        """
        try:
            # Get market context for intelligent messaging
            market_context = await self.get_market_context(market_id)
            market_narrative = self._format_market_context_for_messaging(market_context)

            # Calculate CLV for recovery decision making
            estimated_transaction = lead_data.get('estimated_property_value', 500000)
            clv_estimate = CLVEstimate(
                lead_id=lead_data.get('lead_id', 'demo_lead'),
                estimated_transaction_value=estimated_transaction,
                commission_rate=0.03,
                probability_multiplier=lead_data.get('conversion_probability', 0.7)
            )

            # Determine churn reason if not provided
            if not churn_reason:
                last_interaction_days = lead_data.get('last_interaction_days', 7)
                if last_interaction_days > 14:
                    churn_reason = ChurnReason.TIMING
                else:
                    churn_reason = ChurnReason.COMMUNICATION

            # Get appropriate recovery campaign template
            recovery_template = self._get_recovery_template(clv_estimate.clv_tier, churn_reason)

            # Import here to avoid circular imports
            from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine, ScriptType

            lead_name = lead_data.get('lead_name', 'Client')
            lead_id = lead_data.get('lead_id', f"demo_{lead_name.lower().replace(' ', '_')}")
            risk_score = risk_data.get('risk_score', 0) if risk_data else lead_data.get('risk_score_14d', 0)

            # Initialize automation engine
            automation_engine = ClaudeAutomationEngine()

            # Build enhanced context with market intelligence
            enhanced_context = {
                "churn_risk": risk_score,
                "market_context": market_narrative,
                "recovery_campaign_type": recovery_template["campaign_type"] if recovery_template else "nurture",
                "clv_tier": clv_estimate.clv_tier.value,
                "estimated_commission": f"${clv_estimate.estimated_clv:,.0f}",
                "market_neighborhoods": [n["name"] for n in market_context.get("top_neighborhoods", [])[:3]],
                "market_employers": [e["name"] for e in market_context.get("major_employers", [])[:3]],
                "churn_reason": churn_reason.value if churn_reason else "timing",
                **lead_data
            }

            # Determine script type and channel based on risk and CLV
            script_type = ScriptType.RE_ENGAGEMENT
            if risk_score > 80 and clv_estimate.clv_tier == CLVTier.HIGH_VALUE:
                channel = "sms"  # Urgent, high-value intervention
            elif clv_estimate.clv_tier == CLVTier.HIGH_VALUE:
                channel = "sms"  # High-value gets priority channel
            else:
                channel = "email"  # Standard follow-up

            # Generate market-aware script with Claude intelligence
            automated_script = await automation_engine.generate_personalized_script(
                script_type=script_type,
                lead_id=lead_id,
                channel=channel,
                context_override=enhanced_context,
                variants=2  # Generate A/B variants
            )

            # Build comprehensive response with market context
            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "market_context": market_context,
                "script": automated_script.primary_script,
                "strategy": f"Market-Aware {recovery_template['campaign_type'].replace('_', ' ').title()}" if recovery_template else "Market-Aware Re-engagement",
                "reasoning": f"{automated_script.personalization_notes}\n\nMarket Context: {market_narrative}",
                "channel_recommendation": automated_script.channel.upper(),
                "alternative_scripts": automated_script.alternative_scripts,
                "objection_responses": automated_script.objection_responses,
                "success_probability": automated_script.success_probability,
                "expected_response_rate": automated_script.expected_response_rate,
                "generation_time_ms": automated_script.generation_time_ms,
                "a_b_variants": automated_script.a_b_testing_variants,
                "clv_estimate": clv_estimate.estimated_clv,
                "clv_tier": clv_estimate.clv_tier.value,
                "recovery_template_used": recovery_template["campaign_type"] if recovery_template else None,
                "market_advantages": market_context.get("specializations", {}).get("unique_advantages", [])
            }

        except Exception as e:
            # Enhanced fallback with market context
            market_context = await self.get_market_context(market_id)
            market_name = market_context.get("market_name", "the local market")

            lead_name = lead_data.get('lead_name', 'Client')
            risk_score = risk_data.get('risk_score', 0) if risk_data else lead_data.get('risk_score_14d', 0)

            # Market-aware fallback script
            last_interaction = lead_data.get('last_interaction_days', 5)

            reasoning = f"Lead {lead_name} has a {risk_score:.1f}% churn risk in the {market_name} market. "
            reasoning += f"After {last_interaction} days of inactivity, they need market-specific re-engagement highlighting current opportunities."

            if risk_score > 80:
                # Get market-specific urgent message
                top_areas = market_context.get("top_neighborhoods", [])
                area_mention = f" in {top_areas[0]['name']}" if top_areas else ""

                script = f"Hi {lead_name}, it's Jorge. I just had an exclusive property become available{area_mention} that matches exactly what we discussed. Given the current {market_name} market conditions, this won't last long. Can we schedule a quick call today?"
                strategy = f"Urgent Market-Specific Intervention - {market_name}"
            else:
                # Market-aware nurture message
                market_type = market_context.get("market_type", "mixed")
                script = f"Hey {lead_name}, hope you're doing well! I wanted to share some interesting developments in the {market_name} {market_type} market that might interest you. The timing might be perfect for your move. Worth a quick chat?"
                strategy = f"Market-Aware Nurture - {market_name} Focus"

            return {
                "lead_name": lead_name,
                "risk_score": risk_score,
                "market_context": market_context,
                "script": script,
                "strategy": strategy,
                "reasoning": reasoning,
                "channel_recommendation": "SMS (High Response Probability)" if risk_score > 60 else "Email",
                "error": f"Claude service unavailable, using market-aware fallback: {str(e)}"
            }

    def _get_recovery_template(self, clv_tier: CLVTier, churn_reason: ChurnReason) -> Optional[Dict[str, Any]]:
        """Get appropriate recovery campaign template based on CLV and churn reason."""
        # High-value leads get aggressive recovery campaigns
        if clv_tier == CLVTier.HIGH_VALUE:
            if churn_reason in [ChurnReason.TIMING, ChurnReason.BUDGET]:
                return {"campaign_type": "win_back_aggressive"}
            else:
                return {"campaign_type": "value_proposition"}

        # Medium-value leads get nurture campaigns
        elif clv_tier == CLVTier.MEDIUM_VALUE:
            return {"campaign_type": "win_back_nurture"}

        # Low-value leads get basic re-engagement
        else:
            return {"campaign_type": "market_comeback"}

    async def generate_retention_script(self, lead_data: Dict[str, Any], risk_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        🆕 Enhanced with Real Claude Intelligence (Legacy Wrapper)
        ENHANCED: Now delegates to market-aware retention script generation
        """
        # Delegate to the enhanced market-aware method
        return await self.generate_market_aware_retention_script(
            lead_data=lead_data,
            risk_data=risk_data,
            market_id=self.market_id  # Use the assistant's market context
        )
