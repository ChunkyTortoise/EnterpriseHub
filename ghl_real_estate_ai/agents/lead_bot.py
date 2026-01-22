import asyncio
from typing import Dict, Any, Literal
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.workflows import LeadFollowUpState
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.integrations.lyrio import LyrioClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class LeadBotWorkflow:
    """
    Orchestrates the 3-7-30 Day Follow-Up Sequence using LangGraph.
    Implements the 'Ghost-in-the-Machine' Re-engagement Strategy.
    """
    
    def __init__(self):
        self.intent_decoder = LeadIntentDecoder()
        self.retell_client = RetellClient()
        self.cma_generator = CMAGenerator()
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(LeadFollowUpState)
        
        # Define Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)
        workflow.add_node("determine_path", self.determine_path)
        workflow.add_node("generate_cma", self.generate_cma)
        
        # Follow-up Nodes
        workflow.add_node("send_day_3_sms", self.send_day_3_sms)
        workflow.add_node("initiate_day_7_call", self.initiate_day_7_call)
        workflow.add_node("send_day_14_email", self.send_day_14_email)
        workflow.add_node("send_day_30_nudge", self.send_day_30_nudge)
        
        # Define Edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "determine_path")
        
        # Conditional Routing based on 'current_step' and 'engagement_status'
        workflow.add_conditional_edges(
            "determine_path",
            self._route_next_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_day_3_sms",
                "day_7": "initiate_day_7_call",
                "day_14": "send_day_14_email",
                "day_30": "send_day_30_nudge",
                "qualified": END,
                "nurture": END
            }
        )
        
        # All actions end for this single-turn execution
        workflow.add_edge("generate_cma", END)
        workflow.add_edge("send_day_3_sms", END)
        workflow.add_edge("initiate_day_7_call", END)
        workflow.add_edge("send_day_14_email", END)
        workflow.add_edge("send_day_30_nudge", END)
        
        return workflow.compile()

    # --- Node Implementations ---

    async def analyze_intent(self, state: LeadFollowUpState) -> Dict:
        """Score the lead using the Phase 1 Intent Decoder."""
        logger.info(f"Analyzing intent for lead {state['lead_id']}")
        profile = self.intent_decoder.analyze_lead(
            state['lead_id'], 
            state['conversation_history']
        )
        
        # Sync to Lyrio (Phase 4)
        lyrio = LyrioClient()
        
        # Run sync in background
        asyncio.create_task(lyrio.sync_lead_score(
            state['lead_id'],
            profile.frs.total_score,
            profile.pcs.total_score,
            [profile.frs.classification]
        ))
        
        return {"intent_profile": profile}

    async def determine_path(self, state: LeadFollowUpState) -> Dict:
        """Decide the next step based on engagement and timeline."""

        # 1. Check for Price Objection / CMA Request (Phase 3)
        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""
        price_keywords = ["price", "value", "worth", "zestimate", "comps", "market analysis"]

        is_price_aware = state['intent_profile'].frs.price.category == "Price-Aware"
        has_keyword = any(k in last_msg for k in price_keywords)
        
        logger.info(f"DEBUG: determine_path - last_msg: '{last_msg}'")
        logger.info(f"DEBUG: determine_path - is_price_aware: {is_price_aware}, has_keyword: {has_keyword}")
        logger.info(f"DEBUG: determine_path - cma_generated: {state.get('cma_generated')}")

        if (is_price_aware or has_keyword) and not state.get('cma_generated'):
            logger.info("DEBUG: determine_path - Routing to generate_cma")
            return {"current_step": "generate_cma", "engagement_status": "responsive"}

        # 2. Check for immediate qualification (High Intent)
        if state['intent_profile'].frs.classification == "Hot Lead":
            return {"current_step": "qualified", "engagement_status": "qualified"}
            
        # 3. Check for ghosting (No response > 48h - Mock logic)
        # In prod, compare datetime.now() with last_interaction_time
        
        # This node basically acts as a router/state updater
        return {}

    async def generate_cma(self, state: LeadFollowUpState) -> Dict:
        """Generate Zillow-Defense CMA and inject into conversation."""
        logger.info(f"Generating CMA for {state['lead_name']}")
        
        address = state.get('property_address', '123 Main St, Austin, TX') # Fallback if missing
        
        # Generate Report
        report = await self.cma_generator.generate_report(address)
        
        # Render PDF URL (Mock)
        pdf_url = PDFRenderer.generate_pdf_url(report)
        
        # Phase 8: Digital Twin Association
        lyrio = LyrioClient()
        # Mock URL for digital twin
        digital_twin_url = f"https://enterprise-hub.ai/visualize/{address.replace(' ', '-').lower()}"
        
        # Sync Digital Twin URL to Lyrio in background
        asyncio.create_task(lyrio.sync_digital_twin_url(
            state['lead_id'],
            address,
            digital_twin_url
        ))
        
        # Construct Response
        response_msg = (
            f"I ran the numbers for {address}. Zillow's estimate is off by ${report.zillow_variance_abs:,.0f}. "
            f"Here is the real market analysis based on actual comps from the last 45 days: \n\n"
            f"[View CMA Report]({pdf_url})\n\n"
            f"I've also prepared a 3D Digital Twin of your property: {digital_twin_url}"
        )
        
        # In a real system, we'd send this via GHL API here
        logger.info(f"CMA Injection: {response_msg}")
        
        return {
            "cma_generated": True, 
            "current_step": "nurture", # Return to nurture or wait for reply
            "last_interaction_time": datetime.now()
        }

    async def send_day_3_sms(self, state: LeadFollowUpState) -> Dict:
        """Day 3: Soft Check-in with FRS-aware logic."""
        frs = state['intent_profile'].frs.total_score
        name = state['lead_name']
        prop = state.get('property_address', 'your property')
        
        if frs > 60:
            msg = f"Hi {name}—just following up on {prop}. No pressure, but we have qualified buyers interested in your market RIGHT NOW. Still thinking about it? [Link]"
        elif frs > 40:
            msg = f"Hi {name}, wanted to share some new market data for {prop}. Prices are shifting. Link here: [Link]"
        else:
            msg = f"Hi {name}, checking in on {prop}. No rush on our end, just keeping you in the loop."
            
        logger.info(f"Day 3 SMS to {state['contact_phone']}: {msg}")
        # Call GHL API to send SMS here (Mocked)
        return {"engagement_status": "ghosted", "current_step": "day_7_call"} # Advance step for next run

    async def initiate_day_7_call(self, state: LeadFollowUpState) -> Dict:
        """Day 7: Initiate Retell AI Call with Stall-Breaker logic."""
        logger.info(f"Initiating Day 7 Call for {state['lead_name']}")
        
        # Prepare context for the AI agent
        stall_breaker = self._select_stall_breaker(state)
        context = {
            "lead_name": state['lead_name'],
            "property": state.get('property_address'),
            "stall_breaker_script": stall_breaker,
            "frs_score": state['intent_profile'].frs.total_score
        }
        
        # Trigger Retell Call (Fire-and-forget for Dashboard UI performance)
        def _call_finished(fut):
            try:
                fut.result()
                logger.info(f"Background Retell call initiated successfully for {state['lead_name']}")
            except Exception as e:
                logger.error(f"Background Retell call failed for {state['lead_name']}: {e}")

        task = asyncio.create_task(self.retell_client.create_call(
            to_number=state['contact_phone'],
            lead_name=state['lead_name'],
            lead_context=context,
            metadata={"contact_id": state['lead_id']}
        ))
        task.add_done_callback(_call_finished)
        
        return {"engagement_status": "ghosted", "current_step": "day_14_email"}

    async def send_day_14_email(self, state: LeadFollowUpState) -> Dict:
        """Day 14: Value Injection (CMA)."""
        logger.info(f"Sending Day 14 Email to {state['contact_email']}")
        # Logic to generate CMA PDF would go here
        return {"engagement_status": "ghosted", "current_step": "day_30_nudge"}

    async def send_day_30_nudge(self, state: LeadFollowUpState) -> Dict:
        """Day 30: Final qualification attempt."""
        logger.info(f"Sending Day 30 SMS to {state['contact_phone']}")
        return {"engagement_status": "nurture", "current_step": "nurture"}

    # --- Helper Logic ---

    def _route_next_step(self, state: LeadFollowUpState) -> Literal["day_3", "day_7", "day_14", "day_30", "qualified", "nurture"]:
        """Conditional routing logic."""
        # Fix for phase 3: check for generate_cma first
        if state.get('current_step') == 'generate_cma':
            return "generate_cma"

        if state['engagement_status'] == "qualified":
            return "qualified"
        if state['engagement_status'] == "nurture":
            return "nurture"
            
        # Valid steps mapping
        step = state.get('current_step', 'initial')
        if step in ["day_3", "day_7", "day_14", "day_30"]:
            return step
        
        # Default fallback
        return "nurture"

    def _select_stall_breaker(self, state: LeadFollowUpState) -> str:
        """Select the appropriate stall-breaking script based on intent profile."""
        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""
        
        if "thinking" in last_msg:
            return "What specifically are you thinking about? The timeline, the price, or whether you actually want to sell?"
        if "get back" in last_msg:
            return "I appreciate it, but I need to know: are you *actually* selling, or just exploring?"
        if "zestimate" in last_msg or "zillow" in last_msg:
            return "Zillow's algorithm doesn't know your kitchen was just renovated. Want to see real comps?"
        if "agent" in last_msg or "realtor" in last_msg:
            return "Cool. Quick question: has your agent actually *toured* those comps? If not, we're operating with better intel."
            
        # Default generic stall breaker
        return "If you're serious about selling, you need to know market conditions are shifting. Would 15 minutes to look at real numbers make sense?"