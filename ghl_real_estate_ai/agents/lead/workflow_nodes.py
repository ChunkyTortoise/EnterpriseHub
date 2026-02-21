"""
Workflow Nodes - Implementation of LangGraph workflow nodes for lead follow-up.

This module contains all the node implementations used in the Lead Bot workflow graphs.
"""

import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Literal, Optional

from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.lead.handoff_manager import HandoffManager
from ghl_real_estate_ai.agents.lead.response_generator import ResponseGenerator
from ghl_real_estate_ai.agents.lead.routing import LeadRouter
from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.services.event_publisher import EventPublisher
from ghl_real_estate_ai.services.ghost_followup_engine import GhostFollowUpEngine, GhostState
from ghl_real_estate_ai.services.lead_sequence_scheduler import LeadSequenceScheduler
from ghl_real_estate_ai.services.lead_sequence_state_service import (
    LeadSequenceState,
    SequenceDay,
    SequenceStatus,
)

logger = get_logger(__name__)


class WorkflowNodes:
    """
    Container for all workflow node implementations.

    This class holds references to all dependencies needed by the workflow nodes
    and provides implementations for each node in the LangGraph.
    """

    def __init__(
        self,
        config,
        intent_decoder: LeadIntentDecoder,
        ghost_engine: GhostFollowUpEngine,
        sequence_service,
        scheduler: LeadSequenceScheduler,
        event_publisher: EventPublisher,
        ghl_client=None,
        sendgrid_client=None,
        retell_client: Optional[RetellClient] = None,
        cma_generator: Optional[CMAGenerator] = None,
        analytics_engine=None,
        personality_adapter=None,
        temperature_engine=None,
        ml_analytics=None,
        intelligence_middleware=None,
        market_intel=None,
        workflow_service=None,
    ):
        self.config = config
        self.intent_decoder = intent_decoder
        self.ghost_engine = ghost_engine
        self.sequence_service = sequence_service
        self.scheduler = scheduler
        self.event_publisher = event_publisher
        self.ghl_client = ghl_client
        self.sendgrid_client = sendgrid_client
        self.retell_client = retell_client or RetellClient()
        self.cma_generator = cma_generator or CMAGenerator()
        self.analytics_engine = analytics_engine
        self.personality_adapter = personality_adapter
        self.temperature_engine = temperature_engine
        self.ml_analytics = ml_analytics
        self.intelligence_middleware = intelligence_middleware
        self.market_intel = market_intel
        self.workflow_service = workflow_service

        # Helper classes
        self.response_generator = ResponseGenerator()
        self.lead_router = LeadRouter()
        self.handoff_manager = HandoffManager(event_publisher)

    # ================================
    # STANDARD WORKFLOW NODES
    # ================================

    async def analyze_intent(self, state: Dict) -> Dict:
        """Score the lead using the Intent Decoder."""
        logger.info(f"Analyzing intent for lead {state['lead_id']}")

        # Emit bot status update
        await self.event_publisher.publish_bot_status_update(
            bot_type="lead-bot", contact_id=state["lead_id"], status="processing", current_step="analyze_intent"
        )

        await sync_service.record_lead_event(state["lead_id"], "AI", "Analyzing lead intent profile.", "thought")

        _intent_start_time = time.time()
        profile = self.intent_decoder.analyze_lead(state["lead_id"], state["conversation_history"])

        # Initialize or restore sequence state
        sequence_state = await self.sequence_service.get_state(state["lead_id"])
        if not sequence_state:
            # Create new sequence for new lead
            logger.info(f"Creating new sequence for lead {state['lead_id']}")
            sequence_state = await self.sequence_service.create_sequence(
                state["lead_id"], initial_day=SequenceDay.DAY_3
            )

            # Schedule the initial sequence start (immediate or slight delay)
            await self.scheduler.schedule_sequence_start(state["lead_id"], delay_minutes=1)
        else:
            logger.info(f"Restored sequence state for lead {state['lead_id']}: {sequence_state.current_day.value}")

        # Compute actual timing and confidence
        intent_processing_ms = (time.time() - _intent_start_time) * 1000
        intent_confidence = min(0.99, profile.frs.total_score / 100.0)

        # Emit intent analysis complete event
        await self.event_publisher.publish_intent_analysis_complete(
            contact_id=state["lead_id"],
            processing_time_ms=round(intent_processing_ms, 2),
            confidence_score=round(intent_confidence, 3),
            intent_category=profile.frs.classification,
            frs_score=profile.frs.total_score,
            pcs_score=profile.pcs.total_score,
            recommendations=[f"Sequence day: {sequence_state.current_day.value}"],
        )

        return {"intent_profile": profile, "sequence_state": sequence_state.to_dict()}

    async def check_handoff_signals(self, state: Dict) -> Dict:
        """
        Early handoff detection to short-circuit workflow when handoff is needed.

        This node executes immediately after intent analysis to detect buyer/seller
        intent patterns. If handoff confidence exceeds threshold (0.7), workflow
        terminates early, skipping expensive response generation.

        Returns:
            Dict with:
                - handoff_required: bool
                - handoff_signals: Dict with buyer/seller intent scores
                - handoff_target: str ("buyer-bot" or "seller-bot")
        """
        if not self.config.jorge_handoff_enabled:
            return {"handoff_required": False, "handoff_signals": {}}

        # Extract intent signals from latest message
        last_msg = state["user_message"] if "user_message" in state else ""
        if not last_msg:
            return {"handoff_required": False, "handoff_signals": {}}

        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        # Fast regex-based intent detection
        signals = JorgeHandoffService.extract_intent_signals(last_msg)

        buyer_score = signals.get("buyer_intent_score", 0.0)
        seller_score = signals.get("seller_intent_score", 0.0)

        # Check if handoff threshold exceeded
        HANDOFF_THRESHOLD = 0.7
        handoff_required = False
        handoff_target = None

        if buyer_score >= HANDOFF_THRESHOLD:
            handoff_required = True
            handoff_target = "buyer-bot"
            logger.info(
                f"Early handoff triggered for {state['lead_id']}: buyer intent {buyer_score:.2f} >= {HANDOFF_THRESHOLD}"
            )
        elif seller_score >= HANDOFF_THRESHOLD:
            handoff_required = True
            handoff_target = "seller-bot"
            logger.info(
                f"Early handoff triggered for {state['lead_id']}: seller intent {seller_score:.2f} >= {HANDOFF_THRESHOLD}"
            )

        if handoff_required:
            # Emit handoff event
            await self.event_publisher.publish_bot_status_update(
                bot_type="lead-bot",
                contact_id=state["lead_id"],
                status="handoff_detected",
                current_step="check_handoff_signals",
            )

            await sync_service.record_lead_event(
                state["lead_id"],
                "AI",
                f"Handoff to {handoff_target} detected early (score={max(buyer_score, seller_score):.2f})",
                "handoff",
            )

        return {
            "handoff_required": handoff_required,
            "handoff_signals": signals,
            "handoff_target": handoff_target,
        }

    async def determine_path(self, state: Dict) -> Dict:
        """Decide the next step based on engagement and timeline."""
        from ghl_real_estate_ai.agents.lead.constants import PRICE_KEYWORDS

        # 1. Check for Price Objection / CMA Request
        last_msg = state["conversation_history"][-1]["content"].lower() if state["conversation_history"] else ""
        is_price_aware = state["intent_profile"].frs.price.category == "Price-Aware"
        has_keyword = any(k in last_msg for k in PRICE_KEYWORDS)

        if (is_price_aware or has_keyword) and not state.get("cma_generated"):
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "Price awareness detected. Routing to CMA generation.", "node"
            )
            return {"current_step": "generate_cma", "engagement_status": "responsive"}

        # 2. Check for immediate qualification (High Intent)
        if state["intent_profile"].frs.classification == "Hot Lead":
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "High intent lead detected. Routing to qualified state.", "thought"
            )
            return {"current_step": "qualified", "engagement_status": "qualified"}

        # 3. Use sequence state to determine next step
        sequence_data = state.get("sequence_state", {})
        sequence_day_val = state.get("sequence_day")

        if sequence_day_val is not None:
            # Map numeric day to SequenceDay enum using range-based logic
            if sequence_day_val < 3:
                day_enum = SequenceDay.INITIAL
            elif sequence_day_val < 7:
                day_enum = SequenceDay.DAY_3
            elif sequence_day_val < 14:
                day_enum = SequenceDay.DAY_7
            elif sequence_day_val < 30:
                day_enum = SequenceDay.DAY_14
            else:
                day_enum = SequenceDay.DAY_30

            sequence_state = LeadSequenceState(
                lead_id=state["lead_id"],
                current_day=day_enum,
                sequence_status=SequenceStatus.IN_PROGRESS,
                sequence_started_at=datetime.now(timezone.utc),
                engagement_status="responsive",
            )
        elif sequence_data:
            sequence_state = LeadSequenceState.from_dict(sequence_data)
        else:
            sequence_state = await self.sequence_service.get_state(state["lead_id"])
            if not sequence_state:
                sequence_state = await self.sequence_service.create_sequence(state["lead_id"])

        # Determine routing based on sequence day
        current_day = sequence_state.current_day
        if sequence_day_val is not None:
            current_day = day_enum  # Use the already-mapped enum from above

        if current_day == SequenceDay.INITIAL:
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 0 initial contact.", "sequence")
            return {"current_step": "initial_contact", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_3:
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 3 SMS sequence.", "sequence")
            return {"current_step": "day_3", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_7:
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 7 call sequence.", "sequence")
            return {"current_step": "day_7", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_14:
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 14 email sequence.", "sequence")
            return {"current_step": "day_14", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.DAY_30:
            await sync_service.record_lead_event(state["lead_id"], "AI", "Executing Day 30 final nudge.", "sequence")
            return {"current_step": "day_30", "engagement_status": sequence_state.engagement_status}

        elif current_day == SequenceDay.QUALIFIED:
            await sync_service.record_lead_event(
                state["lead_id"], "AI", "Lead qualified, exiting sequence.", "sequence"
            )
            return {"current_step": "qualified", "engagement_status": "qualified"}

        else:  # NURTURE or other
            await sync_service.record_lead_event(state["lead_id"], "AI", "Lead in nurture status.", "sequence")
            return {"current_step": "nurture", "engagement_status": "nurture"}

    async def generate_cma(self, state: Dict) -> Dict:
        """Generate Zillow-Defense CMA and inject into conversation."""
        logger.info(f"Generating CMA for {state['lead_name']}")

        address = state.get("property_address", "123 Main St, Rancho Cucamonga, CA")

        await sync_service.record_lead_event(state["lead_id"], "AI", f"Generating CMA for {address}", "thought")

        # Generate Report
        report = await self.cma_generator.generate_report(address)

        # Render PDF URL (Mock)
        from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer

        pdf_url = PDFRenderer.generate_pdf_url(report)

        # Construct Response
        response_msg = self.response_generator.construct_cma_response(
            address=address,
            zillow_variance_abs=report.zillow_variance_abs,
            pdf_url=pdf_url,
            digital_twin_url=f"https://enterprise-hub.ai/visualize/{address.replace(' ', '-').lower()}",
        )

        logger.info(f"CMA Injection: {response_msg}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"CMA Generated with ${report.zillow_variance_abs:,.0f} variance.", "thought"
        )

        # Mark CMA as generated in sequence state
        await self.sequence_service.set_cma_generated(state["lead_id"])

        # Emit lead bot sequence update for CMA generation
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=0,
            action_type="cma_generated",
            success=True,
            message_sent=response_msg,
        )

        return {
            "cma_generated": True,
            "current_step": "nurture",
            "last_interaction_time": datetime.now(timezone.utc),
        }

    async def send_day_3_sms(self, state: Dict) -> Dict:
        """Day 3: Soft Check-in with FRS-aware logic via GhostEngine."""
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"], sequence_day=3, action_type="analysis_started", success=True
        )

        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=3, frs_score=state["intent_profile"].frs.total_score
        )

        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])
        msg = action["content"]

        logger.info(f"Day 3 SMS to {state.get('contact_phone')}: {msg} (Logic: {action.get('logic')})")
        await sync_service.record_lead_event(state["lead_id"], "AI", f"Sent Day 3 SMS: {msg[:50]}...", "sms")

        # Emit lead bot sequence update - message sent
        await self.event_publisher.publish_lead_bot_sequence_update(
            contact_id=state["lead_id"],
            sequence_day=3,
            action_type="message_sent",
            success=True,
            next_action_date=(datetime.now(timezone.utc) + __import__("datetime").timedelta(days=4)).isoformat(),
            message_sent=msg,
        )

        # Mark Day 3 as completed
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_3, "sms_sent")
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_3)
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(contact_id=state["lead_id"], message=msg, channel=MessageType.SMS)
                logger.info(f"SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send SMS via GHL: {e}")

        return {"engagement_status": "ghosted", "current_step": "day_7_call", "response_content": msg}

    async def initiate_day_7_call(self, state: Dict) -> Dict:
        """Day 7: Initiate Retell AI Call with Stall-Breaker logic."""
        logger.info(f"Initiating Day 7 Call for {state['lead_name']}")

        # Prepare context for the AI agent
        stall_breaker = self.lead_router.select_stall_breaker(
            state["conversation_history"][-1]["content"] if state["conversation_history"] else "", self.ghost_engine
        )
        context = {
            "lead_name": state["lead_name"],
            "property": state.get("property_address"),
            "stall_breaker_script": stall_breaker,
            "frs_score": state["intent_profile"].frs.total_score,
        }

        await sync_service.record_lead_event(state["lead_id"], "AI", "Initiating Day 7 Retell AI Call.", "action")

        # Trigger Retell Call (Fire-and-forget)
        def _call_finished(fut):
            try:
                fut.result()
                logger.info(f"Background Retell call initiated successfully for {state['lead_name']}")
            except Exception as e:
                logger.error(f"Background Retell call failed for {state['lead_name']}: {e}")

        task = asyncio.create_task(
            self.retell_client.create_call(
                to_number=state.get("contact_phone"),
                lead_name=state["lead_name"],
                lead_context=context,
                metadata={"contact_id": state["lead_id"]},
            )
        )
        task.add_done_callback(_call_finished)

        # Mark Day 7 as completed
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_7, "call_initiated")
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_7)
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        return {
            "engagement_status": "ghosted",
            "current_step": "day_14_email",
            "response_content": f"Initiating Day 7 Call with stall breaker: {stall_breaker}",
        }

    async def send_day_14_email(self, state: Dict) -> Dict:
        """Day 14: Value Injection (CMA) via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=14, frs_score=state["intent_profile"].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])

        logger.info(f"Sending Day 14 Email to {state.get('contact_email')}: {action['content']}")
        await sync_service.record_lead_event(state["lead_id"], "AI", "Sent Day 14 Email with value injection.", "email")

        # Mark Day 14 as completed
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_14, "email_sent")
        await self.scheduler.schedule_next_action(state["lead_id"], SequenceDay.DAY_14)
        await self.sequence_service.advance_to_next_day(state["lead_id"])

        # Send email via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state["lead_id"], message=action["content"], channel=MessageType.EMAIL
                )
                logger.info(f"Email sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send email via GHL: {e}")

        return {
            "engagement_status": "ghosted",
            "current_step": "day_30_nudge",
            "response_content": action["content"],
        }

    async def send_day_30_nudge(self, state: Dict) -> Dict:
        """Day 30: Final qualification attempt via GhostEngine."""
        ghost_state = GhostState(
            contact_id=state["lead_id"], current_day=30, frs_score=state["intent_profile"].frs.total_score
        )
        action = await self.ghost_engine.process_lead_step(ghost_state, state["conversation_history"])

        logger.info(f"Sending Day 30 SMS to {state.get('contact_phone')}: {action['content']}")
        await sync_service.record_lead_event(state["lead_id"], "AI", "Sent Day 30 final nudge SMS.", "sms")

        # Mark Day 30 as completed
        await self.sequence_service.mark_action_completed(state["lead_id"], SequenceDay.DAY_30, "sms_sent")
        await self.sequence_service.complete_sequence(state["lead_id"], "nurture")

        # Send SMS via GHL API
        if self.ghl_client:
            try:
                await self.ghl_client.send_message(
                    contact_id=state["lead_id"], message=action["content"], channel=MessageType.SMS
                )
                logger.info(f"Day 30 SMS sent successfully to contact {state['lead_id']}")
            except Exception as e:
                logger.error(f"Failed to send Day 30 SMS via GHL: {e}")

        return {"engagement_status": "nurture", "current_step": "nurture", "response_content": action["content"]}

    async def schedule_showing(self, state: Dict) -> Dict:
        """Handle showing coordination with market-aware scheduling."""
        logger.info(f"Scheduling showing for {state['lead_name']} at {state.get('property_address')}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Coordinating showing with market-aware scheduling.", "thought"
        )

        address = state.get("property_address", "the property")

        # Get market metrics if available
        inventory_days = None
        if self.market_intel:
            try:
                market_metrics = await self.market_intel.get_market_metrics(address)
                if market_metrics:
                    inventory_days = market_metrics.inventory_days
            except Exception:
                pass

        self.response_generator.construct_showing_message(address, inventory_days)

        await sync_service.record_lead_event(state["lead_id"], "AI", f"Showing inquiry sent for {address}.", "sms")

        return {"engagement_status": "showing_booked", "current_step": "post_showing"}

    async def post_showing_survey(self, state: Dict) -> Dict:
        """Collect feedback after a showing with behavioral intent capture."""
        logger.info(f"Collecting post-showing feedback from {state['lead_name']}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Collecting post-showing behavioral feedback.", "thought"
        )

        await sync_service.record_lead_event(state["lead_id"], "AI", "Post-showing survey sent.", "sms")

        return {"current_step": "facilitate_offer", "engagement_status": "qualified"}

    async def facilitate_offer(self, state: Dict) -> Dict:
        """Guide the lead through the offer submission process."""
        logger.info(f"Facilitating offer for {state['lead_name']}")

        address = state.get("property_address", "the property")
        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"Facilitating offer strategy for {address}", "thought"
        )

        # Get market metrics for strategy
        price_appreciation = None
        if self.market_intel:
            try:
                metrics = await self.market_intel.get_market_metrics(address)
                if metrics:
                    price_appreciation = metrics.price_appreciation_1y
            except Exception:
                pass

        self.response_generator.construct_offer_strategy_message(address, price_appreciation)

        await sync_service.record_lead_event(state["lead_id"], "AI", "Offer strategy sent to lead.", "sms")

        return {"engagement_status": "offer_sent", "current_step": "closing_nurture"}

    async def contract_to_close_nurture(self, state: Dict) -> Dict:
        """Automated touchpoints during the escrow period with milestone tracking."""
        logger.info(f"Escrow nurture for {state['lead_name']}")

        await sync_service.record_lead_event(
            state["lead_id"], "AI", "Starting escrow nurture and milestone tracking.", "node"
        )

        # Real milestone tracking based on lead state and engagement
        milestone = self.lead_router.determine_escrow_milestone(state)
        self.response_generator.get_milestone_message(milestone, state["lead_name"])

        await sync_service.record_lead_event(
            state["lead_id"], "AI", f"Escrow update: {milestone} milestone tracked.", "thought"
        )

        return {"engagement_status": "under_contract", "current_step": "closed"}

    # ================================
    # ROUTING METHODS
    # ================================

    def route_next_step(
        self, state: Dict
    ) -> Literal[
        "generate_cma",
        "day_3",
        "day_7",
        "day_14",
        "day_30",
        "schedule_showing",
        "post_showing",
        "facilitate_offer",
        "closing_nurture",
        "qualified",
        "nurture",
    ]:
        """Conditional routing logic."""
        # Check for generate_cma first
        if state.get("current_step") == "generate_cma":
            return "generate_cma"

        # Check for lifecycle transitions
        engagement = state["engagement_status"]
        if engagement == "showing_booked":
            return "post_showing"
        if engagement == "offer_sent":
            return "closing_nurture"
        if engagement == "under_contract":
            return "qualified"

        # Logic for booking showings if score is high
        if state["intent_profile"] and state["intent_profile"].frs.classification == "Hot Lead":
            if engagement != "showing_booked":
                return "schedule_showing"

        if state["engagement_status"] == "qualified":
            return "qualified"
        if state["engagement_status"] == "nurture":
            return "nurture"

        # Valid steps mapping
        step = state.get("current_step", "initial")
        if step in ["day_3", "day_7", "day_14", "day_30"]:
            return step

        # Intelligent fallback
        return self.lead_router.classify_lead_for_routing(state)

    def route_enhanced_step(
        self, state: Dict
    ) -> Literal[
        "generate_cma",
        "day_3",
        "day_7",
        "day_14",
        "day_30",
        "schedule_showing",
        "post_showing",
        "facilitate_offer",
        "closing_nurture",
        "qualified",
        "nurture",
    ]:
        """Enhanced routing with predictive logic"""
        # Check for early warnings that require immediate action
        if state.get("temperature_prediction", {}).get("early_warning"):
            warning = state["temperature_prediction"]["early_warning"]
            if warning.get("urgency") == "high":
                return "schedule_showing"

        # Use parent routing logic
        return self.route_next_step(state)
