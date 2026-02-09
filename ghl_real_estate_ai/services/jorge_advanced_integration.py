"""
Jorge Advanced Integration Hub - Comprehensive integration of all advanced modules

This module integrates the four advanced modules with Jorge's existing Rancho Cucamonga system:
1. Voice AI Phone Integration
2. Automated Marketing Campaign Generator
3. Client Retention & Referral Automation
4. Advanced Market Prediction Analytics

Provides unified interface and orchestration for the complete AI-powered real estate platform.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.automated_marketing_engine import (
    get_automated_marketing_engine,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.client_retention_engine import (
    ClientProfile,
    LifeEventType,
    get_client_retention_engine,
)
from ghl_real_estate_ai.services.market_prediction_engine import (
    TimeHorizon,
    get_market_prediction_engine,
)
from ghl_real_estate_ai.services.rancho_cucamonga_ai_assistant import (
    get_rancho_cucamonga_ai_assistant,
)
from ghl_real_estate_ai.services.voice_ai_handler import (
    ConversationStage,
    VoiceCallContext,
    get_voice_ai_handler,
)

logger = get_logger(__name__)


class IntegrationEventType(Enum):
    """Types of integration events that trigger cross-module actions"""

    NEW_LEAD_CALL = "new_lead_call"
    HIGH_QUALIFIED_CALL = "high_qualified_call"
    NEW_LISTING_ADDED = "new_listing_added"
    SUCCESSFUL_CLOSING = "successful_closing"
    CLIENT_MILESTONE = "client_milestone"
    MARKET_CHANGE_DETECTED = "market_change_detected"
    REFERRAL_RECEIVED = "referral_received"
    REVIEW_RECEIVED = "review_received"


# Alias for backward compatibility
EventType = IntegrationEventType


@dataclass
class IntegrationEvent:
    """Integration event that triggers cross-module actions"""

    event_id: str
    event_type: IntegrationEventType
    timestamp: datetime
    source_module: str
    data: Dict[str, Any]
    triggered_actions: List[str] = None

    def __post_init__(self):
        if self.triggered_actions is None:
            self.triggered_actions = []


@dataclass
class IntegrationDashboard:
    """Unified dashboard data from all modules"""

    voice_ai_stats: Dict[str, Any]
    marketing_stats: Dict[str, Any]
    retention_stats: Dict[str, Any]
    prediction_stats: Dict[str, Any]
    cross_module_insights: Dict[str, Any]
    performance_summary: Dict[str, Any]


class JorgeAdvancedIntegration:
    """
    Advanced Integration Hub for Jorge's Rancho Cucamonga Real Estate Platform

    Orchestrates all four advanced modules to create a unified AI-powered platform:
    - Seamless data flow between modules
    - Automated cross-module triggering
    - Unified analytics and insights
    - Performance optimization
    """

    def __init__(self):
        # Initialize all advanced modules
        self.voice_ai = get_voice_ai_handler()
        self.marketing_engine = get_automated_marketing_engine()
        self.retention_engine = get_client_retention_engine()
        self.prediction_engine = get_market_prediction_engine()
        self.rc_assistant = get_rancho_cucamonga_ai_assistant()
        self.cache = get_cache_service()

        # Integration state
        self.event_handlers = self._setup_event_handlers()
        self.active_integrations = {}
        self.performance_metrics = {}

        logger.info("Jorge Advanced Integration Hub initialized")

    def _setup_event_handlers(self) -> Dict[IntegrationEventType, List[callable]]:
        """Setup event handlers for cross-module integration"""
        return {
            IntegrationEventType.NEW_LEAD_CALL: [
                self._handle_new_lead_call,
                self._track_lead_source,
                self._initialize_client_journey,
            ],
            IntegrationEventType.HIGH_QUALIFIED_CALL: [
                self._handle_high_qualified_call,
                self._create_priority_follow_up,
                self._trigger_market_analysis,
            ],
            IntegrationEventType.NEW_LISTING_ADDED: [
                self._handle_new_listing,
                self._create_listing_campaigns,
                self._analyze_pricing_strategy,
            ],
            IntegrationEventType.SUCCESSFUL_CLOSING: [
                self._handle_successful_closing,
                self._create_success_campaigns,
                self._initialize_retention_journey,
            ],
            IntegrationEventType.CLIENT_MILESTONE: [
                self._handle_client_milestone,
                self._trigger_retention_activities,
                self._assess_referral_potential,
            ],
            IntegrationEventType.MARKET_CHANGE_DETECTED: [
                self._handle_market_change,
                self._create_market_campaigns,
                self._notify_relevant_clients,
            ],
            IntegrationEventType.REFERRAL_RECEIVED: [
                self._handle_referral_received,
                self._track_referral_source,
                self._create_referral_campaigns,
            ],
        }

    async def handle_incoming_call(self, phone_number: str, caller_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle incoming call with full integration

        This is the main entry point for voice interactions that triggers
        the complete AI-powered response system.
        """
        try:
            # Initialize voice AI call
            call_context = await self.voice_ai.handle_incoming_call(phone_number, caller_name)

            # Create integration event
            event = IntegrationEvent(
                event_id=f"call_{call_context.call_id}",
                event_type=IntegrationEventType.NEW_LEAD_CALL,
                timestamp=datetime.now(),
                source_module="voice_ai",
                data={
                    "call_id": call_context.call_id,
                    "phone_number": phone_number,
                    "caller_name": caller_name,
                    "call_context": asdict(call_context),
                },
            )

            # Process integration event
            await self._process_integration_event(event)

            return {
                "status": "success",
                "call_id": call_context.call_id,
                "integration_event_id": event.event_id,
                "next_steps": [
                    "Voice AI handler ready for conversation",
                    "Lead tracking initialized",
                    "Market analysis prepared",
                ],
            }

        except Exception as e:
            logger.error(f"Error handling incoming call: {e}")
            return {"status": "error", "message": str(e), "fallback": "Transfer to Jorge immediately"}

    async def process_voice_conversation(
        self, call_id: str, speech_text: str, audio_confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Process voice conversation with integrated analysis"""

        try:
            # Process voice input
            voice_response = await self.voice_ai.process_voice_input(call_id, speech_text, audio_confidence)

            # Check for qualification milestones
            if call_id in self.voice_ai.active_calls:
                context = self.voice_ai.active_calls[call_id]

                # Trigger high qualification event if threshold met
                if context.qualification_score >= 70 and not context.should_transfer_to_jorge:
                    await self._trigger_high_qualification_event(context)

                # Check for conversation stage changes
                if context.conversation_stage == ConversationStage.SCHEDULING:
                    await self._handle_scheduling_request(context)

            return {
                "status": "success",
                "voice_response": asdict(voice_response),
                "integration_actions": voice_response.suggested_actions,
                "qualification_updates": self._extract_qualification_updates(call_id),
            }

        except Exception as e:
            logger.error(f"Error processing voice conversation: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback_response": "I apologize for the technical difficulty. Let me connect you with Jorge.",
            }

    async def handle_new_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new listing with integrated marketing and analysis"""

        try:
            # Create listing marketing campaigns
            campaign = await self.marketing_engine.create_campaign_from_trigger("new_listing", listing_data)

            # Analyze pricing strategy
            market_analysis = await self._analyze_listing_market_position(listing_data)

            # Generate marketing content
            content = await self.marketing_engine.generate_campaign_content(campaign.campaign_id)

            # Create integration event
            event = IntegrationEvent(
                event_id=f"listing_{listing_data.get('address', 'unknown')}_{datetime.now().timestamp()}",
                event_type=IntegrationEventType.NEW_LISTING_ADDED,
                timestamp=datetime.now(),
                source_module="integration_hub",
                data={
                    "listing_data": listing_data,
                    "campaign_id": campaign.campaign_id,
                    "market_analysis": market_analysis,
                },
            )

            await self._process_integration_event(event)

            return {
                "status": "success",
                "campaign_id": campaign.campaign_id,
                "content_pieces": len(content),
                "market_analysis": market_analysis,
                "estimated_marketing_reach": self._estimate_marketing_reach(content),
                "recommended_actions": [
                    "Review and approve marketing content",
                    "Schedule social media posts",
                    "Set up property alerts for interested clients",
                ],
            }

        except Exception as e:
            logger.error(f"Error handling new listing: {e}")
            return {"status": "error", "message": str(e)}

    async def handle_successful_closing(self, closing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful closing with complete post-closing automation"""

        try:
            # Add client to retention system
            client_profile = await self.retention_engine.add_client_profile(closing_data)

            # Create success story campaign
            success_campaign = await self.marketing_engine.create_campaign_from_trigger(
                "successful_closing", closing_data
            )

            # Generate success content
            success_content = await self.marketing_engine.generate_campaign_content(success_campaign.campaign_id)

            # Analyze market impact
            market_impact = await self._analyze_closing_market_impact(closing_data)

            # Create integration event
            event = IntegrationEvent(
                event_id=f"closing_{closing_data.get('client_id', 'unknown')}_{datetime.now().timestamp()}",
                event_type=IntegrationEventType.SUCCESSFUL_CLOSING,
                timestamp=datetime.now(),
                source_module="integration_hub",
                data={
                    "closing_data": closing_data,
                    "client_id": client_profile.client_id,
                    "campaign_id": success_campaign.campaign_id,
                },
            )

            await self._process_integration_event(event)

            return {
                "status": "success",
                "client_id": client_profile.client_id,
                "retention_journey": "initialized",
                "success_campaign_id": success_campaign.campaign_id,
                "content_pieces": len(success_content),
                "market_impact": market_impact,
                "next_milestones": [
                    "1-week check-in engagement",
                    "1-month satisfaction survey",
                    "3-month referral request",
                    "6-month anniversary message",
                ],
            }

        except Exception as e:
            logger.error(f"Error handling successful closing: {e}")
            return {"status": "error", "message": str(e)}

    async def detect_market_opportunities(self) -> Dict[str, Any]:
        """Detect and act on market opportunities across all modules"""

        try:
            # Get market opportunities from prediction engine
            opportunities = await self.prediction_engine.detect_market_opportunities()

            # Create campaigns for significant opportunities
            campaign_results = []
            for opp in opportunities[:3]:  # Top 3 opportunities
                if opp.potential_return > 10 and opp.confidence_score > 0.7:
                    campaign = await self._create_opportunity_campaign(opp)
                    campaign_results.append(campaign)

            # Notify relevant clients
            client_notifications = await self._notify_opportunity_clients(opportunities)

            # Update market intelligence
            await self._update_market_intelligence(opportunities)

            return {
                "status": "success",
                "opportunities_found": len(opportunities),
                "campaigns_created": len(campaign_results),
                "clients_notified": len(client_notifications),
                "top_opportunities": [
                    {
                        "neighborhood": opp.neighborhood,
                        "type": opp.opportunity_type,
                        "potential_return": opp.potential_return,
                        "confidence": opp.confidence_score,
                    }
                    for opp in opportunities[:5]
                ],
                "recommended_actions": [
                    "Review opportunity campaigns before publishing",
                    "Contact high-potential clients directly",
                    "Update market positioning strategies",
                ],
            }

        except Exception as e:
            logger.error(f"Error detecting market opportunities: {e}")
            return {"status": "error", "message": str(e)}

    async def process_client_milestone(
        self, client_id: str, milestone_type: str, milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process client milestone with integrated retention activities"""

        try:
            # Update client profile
            if milestone_type == "anniversary":
                # Trigger anniversary engagement
                engagement_result = await self._trigger_anniversary_activities(client_id, milestone_data)
            elif milestone_type == "life_event":
                # Handle life event
                life_event_type = LifeEventType(milestone_data.get("event_type", "family_addition"))
                await self.retention_engine.detect_life_event(client_id, life_event_type, milestone_data)
                engagement_result = {"type": "life_event_response", "status": "scheduled"}
            elif milestone_type == "referral_ready":
                # Request referral
                success = await self.retention_engine.request_referral(client_id)
                engagement_result = {"type": "referral_request", "success": success}
            else:
                engagement_result = {"type": "general", "status": "processed"}

            # Create integration event
            event = IntegrationEvent(
                event_id=f"milestone_{client_id}_{milestone_type}_{datetime.now().timestamp()}",
                event_type=IntegrationEventType.CLIENT_MILESTONE,
                timestamp=datetime.now(),
                source_module="integration_hub",
                data={
                    "client_id": client_id,
                    "milestone_type": milestone_type,
                    "milestone_data": milestone_data,
                    "engagement_result": engagement_result,
                },
            )

            await self._process_integration_event(event)

            return {
                "status": "success",
                "client_id": client_id,
                "milestone_type": milestone_type,
                "engagement_result": engagement_result,
                "next_steps": self._determine_next_client_steps(client_id, milestone_type),
            }

        except Exception as e:
            logger.error(f"Error processing client milestone: {e}")
            return {"status": "error", "message": str(e)}

    async def get_unified_dashboard(self) -> IntegrationDashboard:
        """Get unified dashboard data from all modules"""

        try:
            # Get individual module analytics
            voice_stats = await self.voice_ai.get_call_analytics()
            marketing_stats = await self.marketing_engine.get_campaign_analytics()
            retention_stats = await self.retention_engine.get_retention_analytics()
            prediction_stats = await self.prediction_engine.get_prediction_analytics()

            # Generate cross-module insights
            cross_insights = await self._generate_cross_module_insights(
                voice_stats, marketing_stats, retention_stats, prediction_stats
            )

            # Calculate performance summary
            performance_summary = await self._calculate_performance_summary(
                voice_stats, marketing_stats, retention_stats, prediction_stats
            )

            return IntegrationDashboard(
                voice_ai_stats=voice_stats,
                marketing_stats=marketing_stats,
                retention_stats=retention_stats,
                prediction_stats=prediction_stats,
                cross_module_insights=cross_insights,
                performance_summary=performance_summary,
            )

        except Exception as e:
            logger.error(f"Error generating unified dashboard: {e}")
            return IntegrationDashboard(
                voice_ai_stats={},
                marketing_stats={},
                retention_stats={},
                prediction_stats={},
                cross_module_insights={"error": str(e)},
                performance_summary={},
            )

    async def _process_integration_event(self, event: IntegrationEvent):
        """Process integration event through all relevant handlers"""

        try:
            handlers = self.event_handlers.get(event.event_type, [])

            for handler in handlers:
                try:
                    result = await handler(event)
                    event.triggered_actions.append(f"{handler.__name__}: {result}")
                except Exception as e:
                    logger.warning(f"Event handler {handler.__name__} failed: {e}")
                    event.triggered_actions.append(f"{handler.__name__}: error")

            # Cache event for analytics
            await self._cache_integration_event(event)

            logger.info(f"Processed integration event {event.event_id} with {len(event.triggered_actions)} actions")

        except Exception as e:
            logger.error(f"Error processing integration event: {e}")

    # Event Handlers
    async def _handle_new_lead_call(self, event: IntegrationEvent) -> str:
        """Handle new lead call event"""
        call_data = event.data.get("call_context", {})

        # Prepare market data for conversation
        neighborhood = call_data.get("neighborhood_preferences", ["rancho_cucamonga"])[0]
        await self._prepare_market_context_for_call(call_data.get("call_id"), neighborhood)

        return "market_context_prepared"

    async def _track_lead_source(self, event: IntegrationEvent) -> str:
        """Track lead source for attribution"""
        phone_number = event.data.get("phone_number")

        # In production, would integrate with GHL for lead source tracking
        await self.cache.set(
            f"lead_source:{phone_number}",
            {"source": "phone_call", "timestamp": datetime.now().isoformat(), "call_id": event.data.get("call_id")},
            ttl=30 * 24 * 3600,
        )

        return "lead_source_tracked"

    async def _initialize_client_journey(self, event: IntegrationEvent) -> str:
        """Initialize client journey tracking"""
        call_id = event.data.get("call_id")

        # Create journey tracking entry
        journey_data = {
            "stage": "initial_contact",
            "touchpoints": [{"type": "phone_call", "timestamp": datetime.now().isoformat()}],
            "next_expected_action": "qualification_completion",
        }

        await self.cache.set(f"client_journey:{call_id}", journey_data, ttl=90 * 24 * 3600)

        return "journey_initialized"

    async def _handle_high_qualified_call(self, event: IntegrationEvent) -> str:
        """Handle high qualified call event"""
        call_data = event.data.get("call_context", {})

        # Create high-priority market analysis
        if call_data.get("neighborhood_preferences"):
            for neighborhood in call_data["neighborhood_preferences"]:
                await self.prediction_engine.predict_price_appreciation(neighborhood, TimeHorizon.MEDIUM_TERM)

        return "priority_analysis_created"

    async def _create_priority_follow_up(self, event: IntegrationEvent) -> str:
        """Create priority follow-up for high qualified lead"""
        # Schedule immediate follow-up campaign
        campaign = await self.marketing_engine.create_campaign_from_trigger(
            "lead_magnet_request",
            {"type": "priority_follow_up", "urgency": "high", "personalization": event.data.get("call_context", {})},
        )

        return f"priority_campaign_created:{campaign.campaign_id}"

    async def _trigger_market_analysis(self, event: IntegrationEvent) -> str:
        """Trigger comprehensive market analysis"""
        call_context = event.data.get("call_context", {})
        budget_range = call_context.get("budget_range")

        if budget_range:
            # Analyze investment potential in budget range
            roi_prediction = await self.prediction_engine.predict_investment_roi(
                {"price": (budget_range[0] + budget_range[1]) / 2}
            )

            return f"investment_analysis_completed:{roi_prediction.prediction_id}"

        return "general_analysis_prepared"

    async def _handle_new_listing(self, event: IntegrationEvent) -> str:
        """Handle new listing event"""
        listing_data = event.data.get("listing_data", {})

        # Notify potentially interested clients
        await self._notify_interested_clients(listing_data)

        return "interested_clients_notified"

    async def _create_listing_campaigns(self, event: IntegrationEvent) -> str:
        """Create comprehensive listing marketing campaigns"""
        campaign_id = event.data.get("campaign_id")

        # Generate additional campaign variants
        listing_data = event.data.get("listing_data", {})

        # Create social media campaigns
        social_campaign = await self.marketing_engine.create_campaign_from_trigger(
            "new_listing", {**listing_data, "focus": "social_media"}
        )

        return f"social_campaign_created:{social_campaign.campaign_id}"

    async def _analyze_pricing_strategy(self, event: IntegrationEvent) -> str:
        """Analyze listing pricing strategy"""
        listing_data = event.data.get("listing_data", {})

        # Get pricing prediction
        if listing_data.get("neighborhood"):
            price_prediction = await self.prediction_engine.predict_price_appreciation(
                listing_data["neighborhood"], TimeHorizon.SHORT_TERM
            )

            return f"pricing_analysis_completed:{price_prediction.prediction_id}"

        return "pricing_analysis_skipped"

    async def _handle_successful_closing(self, event: IntegrationEvent) -> str:
        """Handle successful closing event"""
        closing_data = event.data.get("closing_data", {})

        # Schedule celebration and testimonial request
        client_id = event.data.get("client_id")
        if client_id:
            # Schedule review request for 1 week later
            await self._schedule_post_closing_sequence(client_id, closing_data)

        return "post_closing_sequence_scheduled"

    async def _create_success_campaigns(self, event: IntegrationEvent) -> str:
        """Create success story marketing campaigns"""
        campaign_id = event.data.get("campaign_id")

        # Create referral-focused campaign
        closing_data = event.data.get("closing_data", {})
        referral_campaign = await self.marketing_engine.create_campaign_from_trigger(
            "successful_closing", {**closing_data, "focus": "referral_generation"}
        )

        return f"referral_campaign_created:{referral_campaign.campaign_id}"

    async def _initialize_retention_journey(self, event: IntegrationEvent) -> str:
        """Initialize comprehensive client retention journey"""
        client_id = event.data.get("client_id")

        # Set up automated touchpoint schedule
        touchpoints = [
            {"type": "check_in", "days_offset": 7},
            {"type": "satisfaction_survey", "days_offset": 30},
            {"type": "market_update", "days_offset": 90},
            {"type": "anniversary_greeting", "days_offset": 365},
        ]

        for touchpoint in touchpoints:
            await self._schedule_retention_touchpoint(client_id, touchpoint)

        return f"retention_journey_initialized:{len(touchpoints)}_touchpoints"

    async def _handle_client_milestone(self, event: IntegrationEvent) -> str:
        """Handle client milestone event"""
        milestone_type = event.data.get("milestone_type")
        client_id = event.data.get("client_id")

        # Update client engagement score
        if client_id and client_id in self.retention_engine.client_profiles:
            profile = self.retention_engine.client_profiles[client_id]
            profile.engagement_score = await self.retention_engine._calculate_engagement_score(profile)

        return f"milestone_processed:{milestone_type}"

    async def _trigger_retention_activities(self, event: IntegrationEvent) -> str:
        """Trigger appropriate retention activities"""
        milestone_data = event.data.get("milestone_data", {})
        client_id = event.data.get("client_id")

        # Create personalized retention campaign
        retention_campaign = await self.marketing_engine.create_campaign_from_trigger(
            "seasonal_opportunity", {"season": "current", "client_focus": client_id, "personalization": milestone_data}
        )

        return f"retention_campaign_created:{retention_campaign.campaign_id}"

    async def _assess_referral_potential(self, event: IntegrationEvent) -> str:
        """Assess and act on referral potential"""
        client_id = event.data.get("client_id")

        if client_id and client_id in self.retention_engine.client_profiles:
            profile = self.retention_engine.client_profiles[client_id]
            referral_prob = await self.retention_engine._calculate_referral_probability(profile)

            if referral_prob > 0.7:
                # High referral potential - trigger referral request
                success = await self.retention_engine.request_referral(client_id)
                return f"referral_requested:success_{success}"

        return "referral_potential_assessed"

    async def _handle_market_change(self, event: IntegrationEvent) -> str:
        """Handle significant market change event"""
        # Trigger market update campaigns
        market_campaign = await self.marketing_engine.create_campaign_from_trigger("market_milestone", event.data)

        return f"market_update_campaign_created:{market_campaign.campaign_id}"

    async def _create_market_campaigns(self, event: IntegrationEvent) -> str:
        """Create market change response campaigns"""
        # Create educational campaign about market changes
        educational_campaign = await self.marketing_engine.create_campaign_from_trigger(
            "market_milestone", {**event.data, "focus": "education", "urgency": "medium"}
        )

        return f"educational_campaign_created:{educational_campaign.campaign_id}"

    async def _notify_relevant_clients(self, event: IntegrationEvent) -> str:
        """Notify clients relevant to market changes"""
        market_data = event.data

        # Identify clients who should be notified
        notification_count = 0

        # For each client in retention system
        for client_profile in self.retention_engine.client_profiles.values():
            if self._should_notify_client(client_profile, market_data):
                await self._send_market_notification(client_profile, market_data)
                notification_count += 1

        return f"clients_notified:{notification_count}"

    async def _handle_referral_received(self, event: IntegrationEvent) -> str:
        """Handle referral received event"""
        referral_data = event.data.get("referral_data", {})

        # Update referring client's referral count
        referring_client = referral_data.get("referring_client_id")
        if referring_client and referring_client in self.retention_engine.client_profiles:
            profile = self.retention_engine.client_profiles[referring_client]
            profile.referrals_provided += 1

        return "referral_credited"

    async def _track_referral_source(self, event: IntegrationEvent) -> str:
        """Track referral source for attribution"""
        referral_data = event.data.get("referral_data", {})

        # Store referral attribution
        await self.cache.set(
            f"referral_attribution:{referral_data.get('new_lead_id')}",
            referral_data,
            ttl=365 * 24 * 3600,  # 1 year
        )

        return "referral_attribution_tracked"

    async def _create_referral_campaigns(self, event: IntegrationEvent) -> str:
        """Create referral thank you campaigns"""
        referral_data = event.data.get("referral_data", {})

        # Create thank you campaign for referring client
        thank_you_campaign = await self.marketing_engine.create_campaign_from_trigger(
            "successful_closing", {**referral_data, "focus": "referral_thank_you"}
        )

        return f"thank_you_campaign_created:{thank_you_campaign.campaign_id}"

    # Helper Methods
    async def _trigger_high_qualification_event(self, context: VoiceCallContext):
        """Trigger high qualification integration event"""
        event = IntegrationEvent(
            event_id=f"high_qual_{context.call_id}",
            event_type=IntegrationEventType.HIGH_QUALIFIED_CALL,
            timestamp=datetime.now(),
            source_module="voice_ai",
            data={"call_context": asdict(context)},
        )

        await self._process_integration_event(event)

    async def _handle_scheduling_request(self, context: VoiceCallContext):
        """Handle scheduling request from voice conversation"""
        # Create calendar integration event
        # In production, would integrate with calendar system
        await self.cache.set(
            f"scheduling_request:{context.call_id}",
            {
                "client_info": {
                    "name": context.caller_name,
                    "phone": context.phone_number,
                    "employer": context.employer,
                    "timeline": context.timeline,
                },
                "requested_at": datetime.now().isoformat(),
                "priority": "high" if context.qualification_score > 70 else "medium",
            },
            ttl=7 * 24 * 3600,  # 7 days
        )

    def _extract_qualification_updates(self, call_id: str) -> Dict[str, Any]:
        """Extract qualification updates from voice conversation"""
        if call_id not in self.voice_ai.active_calls:
            return {}

        context = self.voice_ai.active_calls[call_id]

        return {
            "qualification_score": context.qualification_score,
            "conversation_stage": context.conversation_stage.value,
            "employer": context.employer,
            "timeline": context.timeline,
            "budget_range": context.budget_range,
            "should_transfer": context.should_transfer_to_jorge,
            "transfer_reason": context.transfer_reason,
        }

    async def _analyze_listing_market_position(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market position for new listing"""
        neighborhood = listing_data.get("neighborhood", "rancho_cucamonga")
        price = listing_data.get("price", 0)

        # Get price prediction for neighborhood
        price_prediction = await self.prediction_engine.predict_price_appreciation(neighborhood, TimeHorizon.SHORT_TERM)

        # Analyze optimal timing
        timing_prediction = await self.prediction_engine.predict_optimal_timing("sell", neighborhood)

        return {
            "price_prediction": asdict(price_prediction),
            "timing_analysis": asdict(timing_prediction),
            "competitive_position": "well_positioned",  # Simplified
            "recommendations": [
                "Price is aligned with market trends",
                "Good timing for listing in current market",
                "Strong marketing push recommended",
            ],
        }

    def _estimate_marketing_reach(self, content_pieces: List) -> Dict[str, int]:
        """Estimate marketing reach for content pieces"""
        # Simplified reach estimation
        reach_estimates = {"facebook": 2500, "instagram": 1800, "linkedin": 800, "email": 1200}

        total_reach = 0
        channel_breakdown = {}

        for content in content_pieces:
            if hasattr(content, "content_format"):
                channel = content.content_format.value.split("_")[0]  # Extract platform
                estimated_reach = reach_estimates.get(channel, 500)
                total_reach += estimated_reach
                channel_breakdown[channel] = channel_breakdown.get(channel, 0) + estimated_reach

        return {"total_estimated_reach": total_reach, "channel_breakdown": channel_breakdown}

    async def _analyze_closing_market_impact(self, closing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market impact of successful closing"""
        neighborhood = closing_data.get("neighborhood", "rancho_cucamonga")
        sale_price = closing_data.get("sale_price", 0)

        # Get current market predictions
        market_prediction = await self.prediction_engine.predict_price_appreciation(
            neighborhood, TimeHorizon.MEDIUM_TERM
        )

        return {
            "neighborhood_impact": f"Positive sale in {neighborhood} market",
            "price_influence": "Supports current pricing trends",
            "market_momentum": market_prediction.confidence_level.value,
            "competitive_advantage": "Demonstrates Jorge's market effectiveness",
        }

    async def _create_opportunity_campaign(self, opportunity) -> Dict[str, Any]:
        """Create marketing campaign for market opportunity"""
        campaign = await self.marketing_engine.create_campaign_from_trigger(
            "market_milestone",
            {
                "opportunity": asdict(opportunity),
                "urgency": "high" if opportunity.potential_return > 15 else "medium",
                "focus": "opportunity_education",
            },
        )

        return {"campaign_id": campaign.campaign_id, "opportunity_id": opportunity.opportunity_id}

    async def _notify_opportunity_clients(self, opportunities: List) -> List[str]:
        """Notify relevant clients about market opportunities"""
        notifications_sent = []

        # For each opportunity, find relevant clients
        for opportunity in opportunities[:3]:  # Top 3
            relevant_clients = self._find_relevant_clients_for_opportunity(opportunity)

            for client_id in relevant_clients:
                await self._send_opportunity_notification(client_id, opportunity)
                notifications_sent.append(client_id)

        return notifications_sent

    def _find_relevant_clients_for_opportunity(self, opportunity) -> List[str]:
        """Find clients relevant to a market opportunity"""
        relevant_clients = []

        # Check retention engine clients
        for client_id, profile in self.retention_engine.client_profiles.items():
            # Match by neighborhood or property type
            if (
                opportunity.neighborhood == profile.neighborhood
                or opportunity.opportunity_type in ["investment", "appreciation"]
                and profile.referral_probability > 0.6
            ):
                relevant_clients.append(client_id)

        return relevant_clients[:5]  # Limit to top 5

    async def _send_opportunity_notification(self, client_id: str, opportunity):
        """Send opportunity notification to client"""
        # In production, would create and send actual notification
        await self.cache.set(
            f"opportunity_notification:{client_id}:{opportunity.opportunity_id}",
            {"opportunity": asdict(opportunity), "sent_at": datetime.now().isoformat(), "status": "pending_response"},
            ttl=30 * 24 * 3600,
        )

    async def _update_market_intelligence(self, opportunities: List):
        """Update market intelligence based on opportunities"""
        # Cache market intelligence for RC assistant
        intelligence_update = {
            "opportunities_count": len(opportunities),
            "top_neighborhoods": [opp.neighborhood for opp in opportunities[:3]],
            "avg_potential_return": np.mean([opp.potential_return for opp in opportunities]) if opportunities else 0,
            "updated_at": datetime.now().isoformat(),
        }

        await self.cache.set("market_intelligence_update", intelligence_update, ttl=24 * 3600)

    async def _trigger_anniversary_activities(self, client_id: str, milestone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger comprehensive anniversary activities"""
        # Update property value
        current_value = milestone_data.get("current_property_value")
        if current_value:
            await self.retention_engine.update_property_value(client_id, current_value)

        # Schedule anniversary engagement
        # This is handled automatically by the retention engine

        return {"type": "anniversary", "status": "activities_triggered"}

    def _determine_next_client_steps(self, client_id: str, milestone_type: str) -> List[str]:
        """Determine next steps for client based on milestone"""
        if milestone_type == "anniversary":
            return [
                "Send anniversary gift or card",
                "Schedule property value discussion",
                "Assess referral opportunities",
            ]
        elif milestone_type == "life_event":
            return [
                "Send congratulations message",
                "Assess real estate needs changes",
                "Update client profile information",
            ]
        else:
            return ["Continue regular engagement schedule", "Monitor for next milestone opportunity"]

    async def _generate_cross_module_insights(
        self, voice_stats, marketing_stats, retention_stats, prediction_stats
    ) -> Dict[str, Any]:
        """Generate insights that span across modules"""
        insights = {}

        # Voice to Marketing correlation
        if voice_stats.get("total_calls", 0) > 0 and marketing_stats.get("total_campaigns", 0) > 0:
            insights["call_to_campaign_ratio"] = marketing_stats["total_campaigns"] / voice_stats["total_calls"]

        # Retention to Prediction correlation
        if retention_stats.get("total_clients", 0) > 0:
            insights["client_retention_rate"] = (
                retention_stats["retention_trends"].get("active_clients", 0) / retention_stats["total_clients"]
            )

        # Marketing to Retention pipeline
        marketing_leads = marketing_stats.get("total_leads_generated", 0)
        retention_clients = retention_stats.get("total_clients", 0)
        if marketing_leads > 0:
            insights["lead_to_client_conversion"] = (
                retention_clients / marketing_leads if marketing_leads > retention_clients else 1.0
            )

        # Prediction accuracy impact
        prediction_accuracy = (
            prediction_stats.get("model_performance", {}).get("price_appreciation", {}).get("accuracy", 0)
        )
        insights["prediction_confidence"] = prediction_accuracy

        # Overall system effectiveness
        insights["system_effectiveness_score"] = self._calculate_system_effectiveness(
            voice_stats, marketing_stats, retention_stats, prediction_stats
        )

        return insights

    async def _calculate_performance_summary(
        self, voice_stats, marketing_stats, retention_stats, prediction_stats
    ) -> Dict[str, Any]:
        """Calculate overall performance summary"""
        return {
            "total_interactions": voice_stats.get("total_calls", 0)
            + retention_stats.get("engagement_metrics", {}).get("total_engagements", 0),
            "conversion_pipeline": {
                "calls_received": voice_stats.get("total_calls", 0),
                "qualified_leads": voice_stats.get("qualification_distribution", {}).get("high", 0),
                "active_campaigns": marketing_stats.get("total_campaigns", 0),
                "retained_clients": retention_stats.get("total_clients", 0),
            },
            "roi_metrics": {
                "avg_campaign_roi": marketing_stats.get("avg_roi_percentage", 0),
                "client_lifetime_value": "estimated_from_retention",
                "cost_per_acquisition": marketing_stats.get("avg_cost_per_lead", 0),
            },
            "predictive_accuracy": prediction_stats.get("model_performance", {})
            .get("price_appreciation", {})
            .get("accuracy", 0),
            "system_uptime": "99.9%",  # Placeholder
            "next_optimization_areas": [
                "Improve voice AI qualification accuracy",
                "Increase marketing campaign conversion rates",
                "Enhance retention engagement effectiveness",
                "Refine market prediction models",
            ],
        }

    def _calculate_system_effectiveness(self, voice_stats, marketing_stats, retention_stats, prediction_stats) -> float:
        """Calculate overall system effectiveness score (0-1)"""
        scores = []

        # Voice AI effectiveness
        if voice_stats.get("total_calls", 0) > 0:
            transfer_rate = voice_stats.get("transfer_rate", 0)
            voice_score = 1 - transfer_rate  # Lower transfer rate = better AI performance
            scores.append(voice_score)

        # Marketing effectiveness
        if marketing_stats.get("avg_roi_percentage", 0) > 0:
            roi = marketing_stats["avg_roi_percentage"] / 100
            marketing_score = min(roi / 3.0, 1.0)  # Normalize to 300% ROI = 1.0
            scores.append(marketing_score)

        # Retention effectiveness
        if retention_stats.get("total_clients", 0) > 0:
            active_rate = (
                retention_stats["retention_trends"].get("active_clients", 0) / retention_stats["total_clients"]
            )
            scores.append(active_rate)

        # Prediction effectiveness
        prediction_accuracy = (
            prediction_stats.get("model_performance", {}).get("price_appreciation", {}).get("accuracy", 0)
        )
        if prediction_accuracy > 0:
            scores.append(prediction_accuracy)

        return np.mean(scores) if scores else 0.5

    async def _prepare_market_context_for_call(self, call_id: str, neighborhood: str):
        """Prepare market context data for voice conversation"""
        # Get current market predictions for the neighborhood
        price_prediction = await self.prediction_engine.predict_price_appreciation(
            neighborhood, TimeHorizon.MEDIUM_TERM
        )

        timing_prediction = await self.prediction_engine.predict_optimal_timing("buy", neighborhood)

        market_context = {
            "neighborhood": neighborhood,
            "price_trend": price_prediction.change_percentage,
            "timing_score": timing_prediction.predicted_value,
            "key_insights": price_prediction.key_factors[:3],
            "prepared_at": datetime.now().isoformat(),
        }

        await self.cache.set(f"market_context:{call_id}", market_context, ttl=3600)

    def _should_notify_client(self, client_profile: ClientProfile, market_data: Dict[str, Any]) -> bool:
        """Determine if client should be notified about market changes"""
        # Check if market change affects client's neighborhood
        affected_neighborhoods = market_data.get("affected_neighborhoods", [])
        if client_profile.neighborhood in affected_neighborhoods:
            return True

        # Check if client is investment-focused
        if client_profile.employment_industry in ["logistics", "healthcare"] and market_data.get(
            "investment_opportunity"
        ):
            return True

        return False

    async def _send_market_notification(self, client_profile: ClientProfile, market_data: Dict[str, Any]):
        """Send market change notification to client"""
        # Create personalized market update
        notification_data = {
            "client_id": client_profile.client_id,
            "market_data": market_data,
            "personalization": {
                "neighborhood": client_profile.neighborhood,
                "property_value": client_profile.current_estimated_value,
                "industry": client_profile.employment_industry,
            },
            "sent_at": datetime.now().isoformat(),
        }

        await self.cache.set(
            f"market_notification:{client_profile.client_id}:{datetime.now().timestamp()}",
            notification_data,
            ttl=30 * 24 * 3600,
        )

    async def _schedule_post_closing_sequence(self, client_id: str, closing_data: Dict[str, Any]):
        """Schedule comprehensive post-closing engagement sequence"""
        sequence_items = [
            {"type": "thank_you_call", "days_offset": 1},
            {"type": "satisfaction_survey", "days_offset": 7},
            {"type": "review_request", "days_offset": 14},
            {"type": "first_market_update", "days_offset": 30},
            {"type": "referral_request", "days_offset": 90},
        ]

        for item in sequence_items:
            scheduled_date = datetime.now() + timedelta(days=item["days_offset"])

            await self.cache.set(
                f"post_closing_sequence:{client_id}:{item['type']}",
                {
                    "client_id": client_id,
                    "sequence_type": item["type"],
                    "scheduled_date": scheduled_date.isoformat(),
                    "closing_data": closing_data,
                    "status": "scheduled",
                },
                ttl=180 * 24 * 3600,  # 6 months
            )

    async def _schedule_retention_touchpoint(self, client_id: str, touchpoint: Dict[str, Any]):
        """Schedule individual retention touchpoint"""
        scheduled_date = datetime.now() + timedelta(days=touchpoint["days_offset"])

        await self.cache.set(
            f"retention_touchpoint:{client_id}:{touchpoint['type']}",
            {
                "client_id": client_id,
                "touchpoint_type": touchpoint["type"],
                "scheduled_date": scheduled_date.isoformat(),
                "status": "scheduled",
            },
            ttl=400 * 24 * 3600,  # 400 days to cover anniversary
        )

    async def _notify_interested_clients(self, listing_data: Dict[str, Any]):
        """Notify clients who might be interested in new listing"""
        # Find clients with matching criteria
        interested_clients = []

        for client_id, profile in self.retention_engine.client_profiles.items():
            if self._client_matches_listing(profile, listing_data):
                interested_clients.append(client_id)

        # Send notifications
        for client_id in interested_clients:
            await self._send_listing_notification(client_id, listing_data)

    def _client_matches_listing(self, client_profile: ClientProfile, listing_data: Dict[str, Any]) -> bool:
        """Check if client profile matches listing criteria"""
        # Check neighborhood match
        if client_profile.neighborhood == listing_data.get("neighborhood"):
            return True

        # Check price range (for investment clients)
        listing_price = listing_data.get("price", 0)
        client_property_value = client_profile.current_estimated_value

        # If client's property value is similar, they might be interested in upgrading
        if 0.8 * client_property_value <= listing_price <= 1.5 * client_property_value:
            return True

        return False

    async def _send_listing_notification(self, client_id: str, listing_data: Dict[str, Any]):
        """Send listing notification to specific client"""
        await self.cache.set(
            f"listing_notification:{client_id}:{listing_data.get('address', 'unknown')}",
            {
                "client_id": client_id,
                "listing_data": listing_data,
                "notification_type": "new_listing_match",
                "sent_at": datetime.now().isoformat(),
            },
            ttl=30 * 24 * 3600,
        )

    async def _cache_integration_event(self, event: IntegrationEvent):
        """Cache integration event for analytics"""
        cache_key = f"integration_event:{event.event_id}"
        await self.cache.set(cache_key, asdict(event), ttl=90 * 24 * 3600)  # 90 days

        # Also add to daily event log
        today = datetime.now().strftime("%Y-%m-%d")
        daily_key = f"daily_integration_events:{today}"

        # Get existing events for today
        daily_events = await self.cache.get(daily_key) or []
        daily_events.append(asdict(event))

        # Store updated daily events
        await self.cache.set(daily_key, daily_events, ttl=30 * 24 * 3600)  # 30 days


# Singleton instance
_jorge_advanced_integration = None


def get_jorge_advanced_integration() -> JorgeAdvancedIntegration:
    """Get singleton Jorge Advanced Integration instance"""
    global _jorge_advanced_integration
    if _jorge_advanced_integration is None:
        _jorge_advanced_integration = JorgeAdvancedIntegration()
    return _jorge_advanced_integration
