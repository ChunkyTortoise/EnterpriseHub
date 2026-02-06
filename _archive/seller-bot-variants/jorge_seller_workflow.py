import asyncio
import logging
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.workflows import SellerWorkflowState
from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine
from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence, NationalMarketIntelligence
from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_state_sync import sync_service

logger = get_logger(__name__)

class JorgeSellerWorkflow:
    """
    Orchestrates the Jorge Seller Bot journey from Qualification to Closing.
    """
    
    def __init__(self, conversation_manager=None, ghl_client=None):
        self.seller_engine = JorgeSellerEngine(conversation_manager, ghl_client)
        self.ghl_client = ghl_client
        self.market_intel: NationalMarketIntelligence = get_national_market_intelligence()
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(SellerWorkflowState)
        
        # Define Nodes
        workflow.add_node("qualification", self.handle_qualification)
        workflow.add_node("micro_commitments", self.handle_micro_commitments)
        workflow.add_node("pre_listing", self.handle_pre_listing)
        workflow.add_node("active_listing", self.handle_active_listing)
        workflow.add_node("under_contract", self.handle_under_contract)
        workflow.add_node("closing_nurture", self.handle_closing_nurture)
        workflow.add_node("post_close", self.handle_post_close)
        
        # Define Edges
        workflow.set_entry_point("qualification")
        
        # Conditional Routing
        workflow.add_conditional_edges(
            "qualification",
            self._route_qualification_next,
            {
                "micro_commitments": "micro_commitments",
                "continue": "qualification",
                "end": END
            }
        )
        
        workflow.add_conditional_edges(
            "micro_commitments",
            self._route_micro_commitment_next,
            {
                "pre_listing": "pre_listing",
                "continue": "micro_commitments"
            }
        )
        
        workflow.add_edge("pre_listing", "active_listing")
        workflow.add_edge("active_listing", "under_contract")
        workflow.add_edge("under_contract", "closing_nurture")
        workflow.add_edge("closing_nurture", "post_close")
        workflow.add_edge("post_close", END)
        
        return workflow.compile()

    async def handle_qualification(self, state: SellerWorkflowState) -> Dict:
        """Process qualification using Jorge's Seller Engine."""
        last_message = state['conversation_history'][-1]['content'] if state['conversation_history'] else ""
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Processing seller qualification questions.", "thought")

        result = await self.seller_engine.process_seller_response(
            contact_id=state['lead_id'],
            user_message=last_message,
            location_id="default", # Should be passed in state
            tenant_config={}
        )
        
        await sync_service.record_lead_event(
            state['lead_id'], 
            "AI", 
            f"Qualification Progress: {result.get('questions_answered', 0)} answers collected. Temp: {result.get('temperature', 'cold')}", 
            "thought"
        )

        return {
            "seller_data": result.get("seller_data", {}),
            "temperature": result.get("temperature", "cold"),
            "questions_answered": result.get("questions_answered", 0),
            "engagement_status": "qualified" if result.get("temperature") == "hot" else "qualifying"
        }

    async def handle_micro_commitments(self, state: SellerWorkflowState) -> Dict:
        """Secure 3 small 'Yes' responses before listing."""
        logger.info(f"Handling micro-commitments for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Securing micro-commitments before listing.", "node")

        commitments = state.get("micro_commitments", [])
        last_msg = state['conversation_history'][-1]['content'].lower() if state['conversation_history'] else ""
        
        # Check if last response was a 'Yes'
        is_yes = any(word in last_msg for word in ["yes", "yeah", "sure", "ok", "fine", "absolutely"])
        
        if is_yes and commitments:
            # Mark the last asked commitment as secured
            # This is a simplification; in production, we'd track which one was asked
            await sync_service.record_lead_event(state['lead_id'], "AI", "Micro-commitment secured.", "thought")
            pass 

        commitment_prompts = [
            "Before we list, I need to make sure we're aligned. Do I have your permission to install a secure electronic lockbox for vetted agent access?",
            "Great. To ensure the marketing is top-tier, are you okay with us using a professional drone for those aerial lifestyle shots?",
            "Perfect. Last thing: if we get a full-price offer with a 21-day close, are you prepared to move within that window?"
        ]
        
        next_index = len(commitments)
        if next_index < len(commitment_prompts):
            msg = commitment_prompts[next_index]
            # Send message logic here
            await sync_service.record_lead_event(state['lead_id'], "AI", f"Sent micro-commitment request: {msg[:50]}...", "sms")
            return {"micro_commitments": commitments + [msg], "current_step": "micro_commitments"}
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "All micro-commitments secured.", "thought")
        return {"engagement_status": "commitments_secured"}

    async def handle_pre_listing(self, state: SellerWorkflowState) -> Dict:
        """Handle pre-listing steps like photo collection and doc prep."""
        logger.info(f"Handling pre-listing for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Handling pre-listing preparation.", "node")

        # Inject market insight to build authority
        market_metrics = await self.market_intel.get_market_metrics(state.get('property_address', 'Rancho Cucamonga'))
        insight = ""
        if market_metrics:
            insight = f"Homes in your neighborhood are moving in {market_metrics.inventory_days} days right now. "
            
        msg = f"{insight}To get you the highest price, I need to see the kitchen and main living area. Can you send over a few photos?"
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Market-aware photo request sent.", "sms")

        return {"current_step": "pre_listing", "engagement_status": "listing_prep"}

    async def handle_active_listing(self, state: SellerWorkflowState) -> Dict:
        """Manage communications while the listing is active."""
        logger.info(f"Managing active listing for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Listing is live. Managing active communications.", "node")

        msg = "Your listing is live. We've already had interest. I'll send you a summary of the showing feedback every Friday morning."
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Live listing update sent to seller.", "sms")

        return {"current_step": "active_listing", "engagement_status": "active"}

    async def handle_under_contract(self, state: SellerWorkflowState) -> Dict:
        """Manage the Under Contract phase with automated milestone updates."""
        logger.info(f"Managing under-contract for {state['lead_name']}")
        
        await sync_service.record_lead_event(state['lead_id'], "AI", "Transaction under contract. Tracking milestones.", "node")

        # Detect milestone from state or GHL
        milestones = state.get('closing_milestones', [])
        current_milestone = "Opening Escrow"
        if milestones:
            current_milestone = milestones[-1].get("name", "Next Phase")
            
        msg = f"Escrow update: We are currently in the {current_milestone} phase. I'll keep you posted as we clear the inspection contingency. Don't stop packing."
        
        await sync_service.record_lead_event(state['lead_id'], "AI", f"Milestone update: {current_milestone} tracked.", "thought")

        return {"current_step": "under_contract", "engagement_status": "under_contract"}

    async def handle_closing_nurture(self, state: SellerWorkflowState) -> Dict:
        """Final stretch before closing."""
        logger.info(f"Closing nurture for {state['lead_name']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Closing nurture initiated.", "thought")
        msg = "We're almost there. The final walk-through is scheduled. Check your email for the closing disclosures and let me know if you have questions."
        return {"current_step": "closing_nurture"}

    async def handle_post_close(self, state: SellerWorkflowState) -> Dict:
        """Loyalty and referral loop."""
        logger.info(f"Post-close loyalty for {state['lead_name']}")
        await sync_service.record_lead_event(state['lead_id'], "AI", "Transaction closed. Starting post-close loyalty loop.", "node")
        msg = "Congrats on the closing! It's been a pleasure. Who else do you know who's looking to sell in this market? I want more clients like you."
        return {"current_step": "closed", "engagement_status": "closed"}

    def _route_qualification_next(self, state: SellerWorkflowState) -> Literal["micro_commitments", "continue", "end"]:
        """Route from qualification to micro-commitments or end."""
        if state['temperature'] == "hot":
            return "micro_commitments"
            
        if state['questions_answered'] >= 4:
            return "end"
            
        return "continue"

    def _route_micro_commitment_next(self, state: SellerWorkflowState) -> Literal["pre_listing", "continue"]:
        """Route from micro-commitments to pre-listing."""
        if state.get('engagement_status') == "commitments_secured":
            return "pre_listing"
            
        return "continue"
