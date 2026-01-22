import asyncio
from typing import Dict, Any, Literal
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.workflows import LeadFollowUpState
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.services.ghost_followup_engine import get_ghost_followup_engine, GhostState
from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.integrations.lyrio import LyrioClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_state_sync import sync_service

logger = get_logger(__name__)

class LeadBotWorkflow:
    """
    Orchestrates the 3-7-30 Day Follow-Up Sequence using LangGraph.
    Implements the 'Ghost-in-the-Machine' Re-engagement Strategy.
    """
    
    def __init__(self, ghl_client=None):
        self.intent_decoder = LeadIntentDecoder()
        self.retell_client = RetellClient()
        self.cma_generator = CMAGenerator()
        self.ghost_engine = get_ghost_followup_engine()
        self.ghl_client = ghl_client
        from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence
        self.market_intel = get_national_market_intelligence()
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
        
        # Full Lifecycle Nodes
        workflow.add_node("schedule_showing", self.schedule_showing)
        workflow.add_node("post_showing_survey", self.post_showing_survey)
        workflow.add_node("facilitate_offer", self.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.contract_to_close_nurture)
        
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
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
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
        workflow.add_edge("schedule_showing", END)
        workflow.add_edge("post_showing_survey", END)
        workflow.add_edge("facilitate_offer", END)
        workflow.add_edge("contract_to_close_nurture", END)
        
        return workflow.compile()

    # --- Node Implementations ---

    async def analyze_intent(self, state: LeadFollowUpState) -> Dict:
        """Score the lead using the Phase 1 Intent Decoder."""
        logger.info(f"Analyzing intent for lead {state['lead_id']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Analyzing lead intent profile.", "thought")

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
        
        await sync_service.record_lead_event(
            state['lead_id'], 
            "AI", 
            f"Intent Decoded: {profile.frs.classification} (Score: {profile.frs.total_score})", 
            "thought"
        )
        
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
            await sync_service.record_lead_event(state['lead_id'], "AI", "Price awareness detected. Routing to CMA generation.", "node")
            return {"current_step": "generate_cma", "engagement_status": "responsive"}

        # 2. Check for immediate qualification (High Intent)
        if state['intent_profile'].frs.classification == "Hot Lead":
            await sync_service.record_lead_event(state['lead_id'], "AI", "High intent lead detected. Routing to qualified state.", "thought")
            return {"current_step": "qualified", "engagement_status": "qualified"}
            
        # 3. Check for ghosting (No response > 48h - Mock logic)
        # In prod, compare datetime.now() with last_interaction_time
        
        # This node basically acts as a router/state updater
        return {}

    async def generate_cma(self, state: LeadFollowUpState) -> Dict:
        """Generate Zillow-Defense CMA and inject into conversation."""
        logger.info(f"Generating CMA for {state['lead_name']}")
        
        address = state.get('property_address', '123 Main St, Austin, TX') # Fallback if missing
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Generating CMA for {address}", "thought")

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
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"CMA Generated with ${report.zillow_variance_abs:,.0f} variance.", "thought")
        
        return {
            "cma_generated": True, 
            "current_step": "nurture", # Return to nurture or wait for reply
            "last_interaction_time": datetime.now()
        }

    async def send_day_3_sms(self, state: LeadFollowUpState) -> Dict:
        """Day 3: Soft Check-in with FRS-aware logic via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=3,
            frs_score=state['intent_profile'].frs.total_score
        )
        
        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        msg = action['content']
            
        logger.info(f"Day 3 SMS to {state['contact_phone']}: {msg} (Logic: {action.get('logic')})")
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Sent Day 3 SMS: {msg[:50]}...", "sms")
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
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Initiating Day 7 Retell AI Call.", "action")

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
        """Day 14: Value Injection (CMA) via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=14,
            frs_score=state['intent_profile'].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        
        logger.info(f"Sending Day 14 Email to {state['contact_email']}: {action['content']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Sent Day 14 Email with value injection.", "sms")
        # Logic to generate and send CMA PDF would go here
        return {"engagement_status": "ghosted", "current_step": "day_30_nudge"}

    async def send_day_30_nudge(self, state: LeadFollowUpState) -> Dict:
        """Day 30: Final qualification attempt via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state['lead_id'],
            current_day=30,
            frs_score=state['intent_profile'].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state['conversation_history'])
        
        logger.info(f"Sending Day 30 SMS to {state['contact_phone']}: {action['content']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Sent Day 30 final nudge SMS.", "sms")
        return {"engagement_status": "nurture", "current_step": "nurture"}

    async def schedule_showing(self, state: LeadFollowUpState) -> Dict:
        """Handle showing coordination with market-aware scheduling."""
        logger.info(f"Scheduling showing for {state['lead_name']} at {state['property_address']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Coordinating showing with market-aware scheduling.", "thought")

        # Phase 7: Use Smart Scheduler
        from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler
        scheduler = get_smart_scheduler(self.ghl_client)
        
        address = state.get('property_address', 'the property')
        market_metrics = await self.market_intel.get_market_metrics(address)
        
        # Inject urgency if market is hot
        urgency_msg = ""
        if market_metrics and market_metrics.inventory_days < 15:
            urgency_msg = f" This market is moving fast ({market_metrics.inventory_days} days avg), so we should see it soon."
            
        msg = f"Great choice! I'm coordinating with the listing agent for {address}.{urgency_msg} Does tomorrow afternoon work for a tour?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Showing inquiry sent for {address}.", "sms")

        # In a real system, trigger GHL SMS here
        return {"engagement_status": "showing_booked", "current_step": "post_showing"}

    async def post_showing_survey(self, state: LeadFollowUpState) -> Dict:
        """Collect feedback after a showing with behavioral intent capture."""
        logger.info(f"Collecting post-showing feedback from {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Collecting post-showing behavioral feedback.", "thought")

        # Use Tone Engine (Jorge style if applicable, or standard)
        msg = "How was the tour? On a scale of 1-10, how well does this home fit what you're looking for?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Post-showing survey sent.", "sms")

        return {"current_step": "facilitate_offer", "engagement_status": "qualified"}

    async def facilitate_offer(self, state: LeadFollowUpState) -> Dict:
        """Guide the lead through the offer submission process using NationalMarketIntelligence."""
        logger.info(f"Facilitating offer for {state['lead_name']}")
        
        address = state.get('property_address', 'the property')
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Facilitating offer strategy for {address}", "thought")

        metrics = await self.market_intel.get_market_metrics(address)
        
        # Generate offer strategy advice
        strategy = "We should look at recent comps to find the right number."
        if metrics:
            if metrics.price_appreciation_1y > 10:
                strategy = "Given the 10%+ appreciation in this area, we might need to be aggressive with the terms."
            else:
                strategy = "Market is stable here, so we have some room to negotiate on repairs."
                
        msg = f"I've prepared an offer strategy for {address}. {strategy} Ready to review the numbers?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Offer strategy sent to lead.", "sms")

        return {"engagement_status": "offer_sent", "current_step": "closing_nurture"}

    async def contract_to_close_nurture(self, state: LeadFollowUpState) -> Dict:
        """Automated touchpoints during the escrow period with milestone tracking."""
        logger.info(f"Escrow nurture for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Starting escrow nurture and milestone tracking.", "node")

        # Milestone logic (mocked for now, but structure is there)
        msg = "Congrats again on being under contract! The next major milestone is the inspection. I'll be there to make sure everything is handled."
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Escrow update: Inspection milestone tracked.", "thought")

        return {"engagement_status": "under_contract", "current_step": "closed"}

    # --- Helper Logic ---

    def _route_next_step(self, state: LeadFollowUpState) -> Literal["generate_cma", "day_3", "day_7", "day_14", "day_30", "schedule_showing", "post_showing", "facilitate_offer", "closing_nurture", "qualified", "nurture"]:
        """Conditional routing logic."""
        # Fix for phase 3: check for generate_cma first
        if state.get('current_step') == 'generate_cma':
            return "generate_cma"

        # Check for lifecycle transitions
        engagement = state['engagement_status']
        if engagement == "showing_booked":
            return "post_showing"
        if engagement == "offer_sent":
            return "closing_nurture"
        if engagement == "under_contract":
            return "qualified" # Or specific closing node
            
        # Logic for booking showings if score is high
        if state['intent_profile'] and state['intent_profile'].frs.classification == "Hot Lead":
            if engagement != "showing_booked":
                return "schedule_showing"

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

            """Select the appropriate stall-breaking script based on intent profile via GhostEngine."""

            last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""

            

            objection_type = "market_shift" # Default

            if "thinking" in last_msg:

                objection_type = "thinking_about_it"

            elif "get back" in last_msg:

                objection_type = "get_back_to_you"

            elif "zestimate" in last_msg or "zillow" in last_msg:

                objection_type = "zestimate_reference"

            elif "agent" in last_msg or "realtor" in last_msg:

                objection_type = "has_realtor"

                

            return self.ghost_engine.get_stall_breaker(objection_type)

    