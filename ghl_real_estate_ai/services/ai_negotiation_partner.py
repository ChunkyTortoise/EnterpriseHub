"""
AI Negotiation Partner

Central orchestrator for real-time negotiation intelligence that coordinates
seller psychology analysis, market leverage calculation, strategy generation,
and win probability prediction for optimal deal outcomes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.agents.voss_negotiation_agent import get_voss_negotiation_agent
from ghl_real_estate_ai.api.schemas.negotiation import (
    ListingHistory,
    NegotiationAnalysisRequest,
    NegotiationIntelligence,
    RealTimeCoachingRequest,
    RealTimeCoachingResponse,
    StrategyUpdateRequest,
)
from ghl_real_estate_ai.services.attom_client import get_attom_client
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence
from ghl_real_estate_ai.services.market_leverage_calculator import get_market_leverage_calculator
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.negotiation_drift_detector import get_drift_detector
from ghl_real_estate_ai.services.negotiation_strategy_engine import get_negotiation_strategy_engine
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer
from ghl_real_estate_ai.services.win_probability_predictor import get_win_probability_predictor

logger = logging.getLogger(__name__)


class AINegotiationPartner:
    """
    Central orchestrator for AI-powered negotiation intelligence.

    Provides comprehensive negotiation analysis by coordinating multiple intelligence
    engines in parallel, generating strategic recommendations, and offering real-time
    coaching capabilities for active negotiations.
    """

    # SHARED RESOURCE POOL
    _psychology_analyzer = None
    _leverage_calculator = None
    _strategy_engine = None
    _win_predictor = None
    _cache_service = None
    _claude_assistant = None
    _lead_intelligence = None
    _memory = None
    _attom_client = None
    _drift_detector = None
    _voss_agent = None
    _pool_lock = asyncio.Lock()

    def __init__(self):
        # Initialize shared resources
        self._init_shared_resources()

        # Active coaching sessions
        self.active_negotiations: Dict[str, Dict[str, Any]] = {}

        # Performance tracking
        self.performance_metrics = {
            "total_analyses": 0,
            "avg_processing_time_ms": 0,
            "win_rate_predictions": [],
            "strategy_effectiveness": {},
        }

    def _init_shared_resources(self):
        """Implements the Shared Resource Pool pattern to reduce memory footprint."""
        if AINegotiationPartner._psychology_analyzer is not None:
            return

        # Synchronous initialization of core engines
        AINegotiationPartner._psychology_analyzer = get_seller_psychology_analyzer()
        AINegotiationPartner._leverage_calculator = get_market_leverage_calculator()
        AINegotiationPartner._strategy_engine = get_negotiation_strategy_engine()
        AINegotiationPartner._win_predictor = get_win_probability_predictor()

        # Support services
        AINegotiationPartner._cache_service = get_cache_service()
        AINegotiationPartner._claude_assistant = ClaudeAssistant()
        AINegotiationPartner._lead_intelligence = get_enhanced_lead_intelligence()
        AINegotiationPartner._memory = MemoryService()
        AINegotiationPartner._attom_client = get_attom_client()
        AINegotiationPartner._drift_detector = get_drift_detector()
        AINegotiationPartner._voss_agent = get_voss_negotiation_agent()

        logger.info("AINegotiationPartner: Shared Resource Pool Initialized")

    @property
    def psychology_analyzer(self):
        return AINegotiationPartner._psychology_analyzer

    @property
    def leverage_calculator(self):
        return AINegotiationPartner._leverage_calculator

    @property
    def strategy_engine(self):
        return AINegotiationPartner._strategy_engine

    @property
    def win_predictor(self):
        return AINegotiationPartner._win_predictor

    @property
    def cache_service(self):
        return AINegotiationPartner._cache_service

    @property
    def claude_assistant(self):
        return AINegotiationPartner._claude_assistant

    @property
    def lead_intelligence(self):
        return AINegotiationPartner._lead_intelligence

    @property
    def memory(self):
        return AINegotiationPartner._memory

    @property
    def attom_client(self):
        return AINegotiationPartner._attom_client

    @property
    def drift_detector(self):
        return AINegotiationPartner._drift_detector

    @property
    def voss_agent(self):
        return AINegotiationPartner._voss_agent

    async def analyze_negotiation_intelligence(self, request: NegotiationAnalysisRequest) -> NegotiationIntelligence:
        """
        Generate comprehensive negotiation intelligence by coordinating all engines.

        Target: <3 second analysis with 35% higher acceptance rate vs baseline.
        """
        start_time = datetime.now()

        try:
            logger.info(f"Starting negotiation intelligence analysis for property {request.property_id}")

            # Gather required data in parallel, including ATTOM Property DNA
            property_dna_task = self.attom_client.get_property_dna(
                request.property_id
            )  # Using property_id as address for now
            analysis_data_task = self._gather_analysis_data(request)

            dna_result, (property_data, buyer_data, listing_history) = await asyncio.gather(
                property_dna_task, analysis_data_task
            )

            # Enrich property data with ATTOM DNA
            if dna_result:
                property_data["attom_dna"] = dna_result
                logger.info(f"Enriched property {request.property_id} with ATTOM DNA")

            if not property_data:
                raise ValueError(f"Property data not found for {request.property_id}")

            # Execute all intelligence engines in parallel for speed
            analysis_tasks = await asyncio.gather(
                self.psychology_analyzer.analyze_seller_psychology(
                    request.property_id, listing_history, buyer_data.get("communication_data")
                ),
                self.leverage_calculator.calculate_market_leverage(
                    request.property_id, property_data, buyer_data, listing_history
                ),
                return_exceptions=True,
            )

            seller_psychology = analysis_tasks[0]
            market_leverage = analysis_tasks[1]

            if isinstance(seller_psychology, Exception):
                logger.error(f"Psychology analysis failed: {seller_psychology}")
                raise seller_psychology

            if isinstance(market_leverage, Exception):
                logger.error(f"Market leverage analysis failed: {market_leverage}")
                raise market_leverage

            # 🚀 VOSS NEGOTIATION AGENT (LangGraph Workflow)
            voss_result = await self.voss_agent.run_negotiation(
                lead_id=request.lead_id,
                lead_name=buyer_data.get("name", "Lead"),
                address=request.property_id,
                history=listing_history.get("communication_history", []) if isinstance(listing_history, dict) else [],
            )
            logger.info(f"Voss Agent (LangGraph) complete. Level: {voss_result.get('voss_level')}")

            # Generate strategy based on psychology, leverage, and Voss insights
            negotiation_strategy = await self.strategy_engine.generate_negotiation_strategy(
                request.property_id, seller_psychology, market_leverage, property_data, buyer_data
            )

            # Enrich strategy with Voss response
            if voss_result.get("generated_response"):
                negotiation_strategy.primary_script = voss_result["generated_response"]
                logger.info("Enriched negotiation strategy with Voss-powered script")

            # Predict win probability
            win_probability = await self.win_predictor.predict_win_probability(
                request.property_id, seller_psychology, market_leverage, negotiation_strategy, property_data, buyer_data
            )

            # Generate executive summary and insights
            executive_summary, key_insights, action_items = await self._generate_strategic_summary(
                seller_psychology, market_leverage, negotiation_strategy, win_probability
            )

            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Create comprehensive intelligence package
            negotiation_intelligence = NegotiationIntelligence(
                property_id=request.property_id,
                lead_id=request.lead_id,
                tenant_id=request.tenant_id,
                analysis_timestamp=datetime.now(),
                seller_psychology=seller_psychology,
                market_leverage=market_leverage,
                negotiation_strategy=negotiation_strategy,
                win_probability=win_probability,
                executive_summary=executive_summary,
                key_insights=key_insights,
                action_items=action_items,
                processing_time_ms=processing_time,
            )

            # Store for real-time coaching
            self.active_negotiations[request.property_id] = {
                "intelligence": negotiation_intelligence,
                "buyer_profile": buyer_data,
                "property_data": property_data,
                "created_at": datetime.now(),
            }

            # Update performance metrics
            self._update_performance_metrics(processing_time, negotiation_intelligence)

            logger.info(
                f"Negotiation intelligence complete in {processing_time}ms. "
                f"Strategy: {negotiation_strategy.primary_tactic}, "
                f"Win probability: {win_probability.win_probability:.1f}%"
            )

            return negotiation_intelligence

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(f"Negotiation analysis failed after {processing_time}ms: {e}")
            raise

    async def provide_realtime_coaching(self, request: RealTimeCoachingRequest) -> RealTimeCoachingResponse:
        """
        Provide real-time negotiation coaching based on conversation context.

        Updates strategy dynamically as negotiation progresses.
        """
        logger.info(f"Providing real-time coaching for negotiation {request.negotiation_id}")

        try:
            # Get active negotiation context
            negotiation_context = self.active_negotiations.get(request.negotiation_id)
            if not negotiation_context:
                raise ValueError(f"Active negotiation not found: {request.negotiation_id}")

            intelligence = negotiation_context["intelligence"]

            # 🧠 BEHAVIORAL DRIFT DETECTION
            # Calculate response latency (simulated or from request if available)
            latency = (
                request.new_information.get("response_latency_seconds", 0) if hasattr(request, "new_information") else 0
            )
            drift_analysis = self.drift_detector.analyze_drift(
                message=request.conversation_context, response_latency_seconds=latency
            )

            # Analyze current conversation context with Claude
            conversation_insights = await self._analyze_conversation_context(
                request.conversation_context, request.current_situation, intelligence
            )

            # Inject drift insights into conversation insights
            conversation_insights["drift_analysis"] = drift_analysis

            # ROADMAP-079: Integrate with human agent notification system (Slack/email/CRM)
            immediate_guidance = await self._generate_immediate_guidance(
                conversation_insights, intelligence, request.buyer_feedback, request.seller_response
            )

            # Add drift-specific guidance if drifting
            if drift_analysis["is_drifting"]:
                immediate_guidance += f" 🎯 {drift_analysis['recommendation']}"

            # Identify tactical adjustments
            tactical_adjustments = await self._identify_tactical_adjustments(
                conversation_insights, intelligence, request.current_situation
            )

            # Generate next steps
            next_steps = self._generate_next_steps(conversation_insights, tactical_adjustments, intelligence)

            # Create conversation suggestions
            conversation_suggestions = await self._generate_conversation_suggestions(
                conversation_insights, intelligence, request.current_situation
            )

            # Identify risk alerts
            risk_alerts = self._identify_risk_alerts(conversation_insights, intelligence, request.seller_response)

            response = RealTimeCoachingResponse(
                immediate_guidance=immediate_guidance,
                tactical_adjustments=tactical_adjustments,
                next_steps=next_steps,
                conversation_suggestions=conversation_suggestions,
                risk_alerts=risk_alerts,
            )

            logger.info(
                f"Real-time coaching provided with {len(risk_alerts)} risk alerts. Drift: {drift_analysis['drift_score']:.2f}"
            )
            return response

        except Exception as e:
            logger.error(f"Real-time coaching failed: {e}")
            raise

    async def update_negotiation_strategy(self, request: StrategyUpdateRequest) -> NegotiationIntelligence:
        """
        Update negotiation strategy based on new information.

        Triggers partial re-analysis of relevant intelligence engines.
        """
        logger.info(f"Updating negotiation strategy for {request.negotiation_id}")

        try:
            # Get current negotiation context
            negotiation_context = self.active_negotiations.get(request.negotiation_id)
            if not negotiation_context:
                raise ValueError(f"Active negotiation not found: {request.negotiation_id}")

            current_intelligence = negotiation_context["intelligence"]

            # Determine which engines need updates based on new information
            update_psychology = any(
                key in request.new_information for key in ["seller_response", "communication_change", "urgency_update"]
            )
            update_market = any(
                key in request.new_information for key in ["market_change", "competitive_activity", "inventory_update"]
            )

            # Selectively update relevant analyses
            updated_psychology = current_intelligence.seller_psychology
            updated_leverage = current_intelligence.market_leverage

            if update_psychology:
                # Re-analyze seller psychology with new information
                listing_history = self._extract_listing_history(negotiation_context["property_data"])
                communication_data = request.new_information.get("communication_data", {})

                updated_psychology = await self.psychology_analyzer.analyze_seller_psychology(
                    current_intelligence.property_id, listing_history, communication_data
                )

            if update_market:
                # Re-calculate market leverage with new information
                property_data = negotiation_context["property_data"]
                buyer_data = negotiation_context["buyer_profile"]
                listing_history = self._extract_listing_history(property_data)

                updated_leverage = await self.leverage_calculator.calculate_market_leverage(
                    current_intelligence.property_id, property_data, buyer_data, listing_history
                )

            # Always regenerate strategy and win probability with updated data
            updated_strategy = await self.strategy_engine.generate_negotiation_strategy(
                current_intelligence.property_id,
                updated_psychology,
                updated_leverage,
                negotiation_context["property_data"],
                negotiation_context["buyer_profile"],
            )

            updated_win_probability = await self.win_predictor.predict_win_probability(
                current_intelligence.property_id,
                updated_psychology,
                updated_leverage,
                updated_strategy,
                negotiation_context["property_data"],
                negotiation_context["buyer_profile"],
            )

            # Generate updated summary
            executive_summary, key_insights, action_items = await self._generate_strategic_summary(
                updated_psychology, updated_leverage, updated_strategy, updated_win_probability
            )

            # Create updated intelligence package
            updated_intelligence = NegotiationIntelligence(
                property_id=current_intelligence.property_id,
                lead_id=current_intelligence.lead_id,
                tenant_id=current_intelligence.tenant_id,
                analysis_timestamp=datetime.now(),
                seller_psychology=updated_psychology,
                market_leverage=updated_leverage,
                negotiation_strategy=updated_strategy,
                win_probability=updated_win_probability,
                executive_summary=executive_summary,
                key_insights=key_insights,
                action_items=action_items,
                analysis_version="1.1",  # Indicate this is an update
            )

            # Update active negotiation
            self.active_negotiations[request.negotiation_id]["intelligence"] = updated_intelligence

            logger.info(f"Strategy updated. New win probability: {updated_win_probability.win_probability:.1f}%")
            return updated_intelligence

        except Exception as e:
            logger.error(f"Strategy update failed: {e}")
            raise

    async def _gather_analysis_data(
        self, request: NegotiationAnalysisRequest
    ) -> Tuple[Dict[str, Any], Dict[str, Any], ListingHistory]:
        """Gather all required data for negotiation analysis"""

        # Fetch real property data from ATTOM/lead intelligence
        try:
            attom = self.attom_client
            lead_intel = self.lead_intelligence

            # Property data from ATTOM or cache
            property_data = await attom.get_property_details(request.property_id)
            if not property_data or not property_data.get("list_price"):
                property_data = {
                    "property_id": request.property_id,
                    "list_price": 750000,
                    "sqft": 2500,
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "property_type": "single_family",
                    "zip_code": "91730",
                    "days_on_market": 45,
                    "year_built": 2010,
                    "price_drops": 2,
                }
            else:
                property_data.setdefault("property_id", request.property_id)

            # Buyer/lead data from lead intelligence
            buyer_data = await lead_intel.get_lead_profile(request.lead_id)
            if not buyer_data or not buyer_data.get("lead_id"):
                buyer_data = {
                    "lead_id": request.lead_id,
                    "pre_approved": True,
                    "cash_offer": request.buyer_preferences and request.buyer_preferences.get("cash_offer", False),
                    "flexible_timeline": True,
                }
            else:
                buyer_data.setdefault("lead_id", request.lead_id)
                if request.buyer_preferences:
                    buyer_data["cash_offer"] = request.buyer_preferences.get(
                        "cash_offer", buyer_data.get("cash_offer", False)
                    )

        except Exception as e:
            logger.warning(f"Error fetching analysis data, using defaults: {e}")
            property_data = {
                "property_id": request.property_id,
                "list_price": 750000,
                "days_on_market": 45,
                "price_drops": 2,
            }
            buyer_data = {
                "lead_id": request.lead_id,
                "pre_approved": True,
                "cash_offer": request.buyer_preferences and request.buyer_preferences.get("cash_offer", False),
            }

        listing_history = self._extract_listing_history(property_data)
        return property_data, buyer_data, listing_history

    def _extract_listing_history(self, property_data: Dict[str, Any]) -> ListingHistory:
        """Extract listing history from property data"""

        return ListingHistory(
            original_list_price=Decimal(
                str(property_data.get("original_price", property_data.get("list_price", 500000)))
            ),
            current_price=Decimal(str(property_data.get("list_price", 500000))),
            price_drops=property_data.get("price_drops", []),
            days_on_market=property_data.get("days_on_market", 30),
            listing_views=property_data.get("listing_views"),
            showing_requests=property_data.get("showing_requests"),
            offers_received=property_data.get("offers_received"),
            previous_listing_attempts=property_data.get("previous_listing_attempts"),
        )

    async def generate_counter_offer(
        self,
        offer: Dict[str, Any],
        market_comps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate a structured counter-offer using Claude chain-of-thought.

        Args:
            offer: Current offer details (price, terms, contingencies).
            market_comps: Comparable recent sales for pricing context.

        Returns:
            NegotiationStrategy dict with counter_price, rationale,
            talking_points, and risk_assessment.
        """
        import json as _json

        comps_summary = "\n".join(
            f"- {c.get('address', 'N/A')}: ${c.get('sold_price', 0):,.0f}, "
            f"{c.get('sqft', 0)} sqft, {c.get('days_on_market', 0)} DOM"
            for c in (market_comps or [])[:5]
        )

        prompt = f"""You are a real estate negotiation strategist. Analyze this offer
and generate a counter-offer strategy using chain-of-thought reasoning.

CURRENT OFFER:
- Offer Price: ${offer.get("price", 0):,.0f}
- List Price: ${offer.get("list_price", 0):,.0f}
- Terms: {offer.get("terms", "Standard")}
- Contingencies: {offer.get("contingencies", "Inspection, Financing")}
- Cash Offer: {offer.get("cash_offer", False)}
- Close Timeline: {offer.get("close_days", 30)} days

COMPARABLE SALES:
{comps_summary or "No comparable sales provided"}

INSTRUCTIONS:
Think step-by-step:
1. Calculate offer-to-list ratio
2. Analyze how comps support or undermine the offer price
3. Identify leverage points (terms, timeline, contingencies)
4. Determine optimal counter-offer price
5. Draft talking points for the agent

Return ONLY valid JSON:
{{
  "counter_price": <int>,
  "counter_rationale": "<string>",
  "talking_points": ["<string>", ...],
  "risk_assessment": "<low|medium|high>",
  "confidence_score": <float 0-100>,
  "recommended_concessions": ["<string>", ...],
  "walk_away_price": <int>
}}
"""
        try:
            claude = self.claude_assistant
            response = await claude.process_message(prompt)
            content = response.get("content", "{}")

            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                strategy = _json.loads(content[start:end])
            else:
                strategy = {}

            # Ensure required fields
            strategy.setdefault("counter_price", int(offer.get("list_price", offer.get("price", 0)) * 0.97))
            strategy.setdefault("counter_rationale", "Based on market analysis")
            strategy.setdefault("talking_points", [])
            strategy.setdefault("risk_assessment", "medium")
            strategy.setdefault("confidence_score", 65.0)
            strategy.setdefault("recommended_concessions", [])
            strategy.setdefault(
                "walk_away_price",
                int(offer.get("list_price", offer.get("price", 0)) * 0.90),
            )

            logger.info(
                f"Generated counter-offer: ${strategy['counter_price']:,} "
                f"(confidence: {strategy['confidence_score']:.0f}%)"
            )
            return strategy

        except Exception as e:
            logger.error(f"Counter-offer generation failed: {e}")
            list_price = offer.get("list_price", offer.get("price", 500000))
            return {
                "counter_price": int(list_price * 0.97),
                "counter_rationale": "Standard 3% below list based on market norms",
                "talking_points": ["Recent comps support this price range"],
                "risk_assessment": "medium",
                "confidence_score": 40.0,
                "recommended_concessions": [],
                "walk_away_price": int(list_price * 0.90),
            }

    async def _generate_strategic_summary(
        self, psychology, leverage, strategy, win_probability
    ) -> Tuple[str, List[str], List[str]]:
        """Generate executive summary and strategic insights"""

        # Create context for Claude analysis
        context = f"""
        Generate an executive summary for this negotiation intelligence:
        
        Seller Psychology:
        - Motivation: {psychology.motivation_type} 
        - Urgency: {psychology.urgency_level} ({psychology.urgency_score}/100)
        - Flexibility: {psychology.flexibility_score}/100
        
        Market Leverage: 
        - Overall Score: {leverage.overall_leverage_score}/100
        - Market Condition: {leverage.market_condition}
        - Price Positioning: {leverage.price_positioning}
        
        Strategy:
        - Primary Tactic: {strategy.primary_tactic}
        - Recommended Offer: ${strategy.recommended_offer_price}
        - Confidence: {strategy.confidence_score}/100
        
        Win Probability: {win_probability.win_probability:.1f}%
        
        Provide:
        1. Executive summary (2-3 sentences)
        2. Key insights (5 bullet points)
        3. Action items (5 specific next steps)
        """

        try:
            ai_response = await self.claude_assistant.analyze_with_context(context)

            executive_summary = ai_response.get(
                "executive_summary",
                f"Seller shows {psychology.motivation_type} motivation with {psychology.urgency_level} urgency. "
                f"Market leverage is {leverage.overall_leverage_score}/100 favoring our {strategy.primary_tactic} approach. "
                f"Win probability is {win_probability.win_probability:.1f}% for recommended offer.",
            )

            key_insights = ai_response.get(
                "key_insights",
                [
                    f"Seller {psychology.motivation_type} motivation indicates {psychology.flexibility_score}/100 flexibility",
                    f"Market {leverage.market_condition} with {leverage.overall_leverage_score}/100 buyer leverage",
                    f"{strategy.primary_tactic} strategy optimal for this scenario",
                    f"Win probability {win_probability.win_probability:.1f}% with current approach",
                    f"Price positioning is {leverage.price_positioning} relative to market",
                ],
            )

            action_items = ai_response.get(
                "action_items",
                [
                    f"Present {strategy.primary_tactic} offer at ${strategy.recommended_offer_price}",
                    "Emphasize key terms based on seller psychology",
                    "Monitor seller response patterns",
                    "Prepare counter-offer strategy",
                    "Track market condition changes",
                ],
            )

            return executive_summary, key_insights[:5], action_items[:5]

        except Exception as e:
            logger.error(f"Strategic summary generation failed: {e}")
            # Fallback to rule-based summary
            return self._generate_fallback_summary(psychology, leverage, strategy, win_probability)

    def _generate_fallback_summary(self, psychology, leverage, strategy, win_probability):
        """Generate fallback summary if AI fails"""

        executive_summary = (
            f"Seller demonstrates {psychology.motivation_type} motivation with {psychology.urgency_level} urgency. "
            f"Market leverage score of {leverage.overall_leverage_score}/100 supports {strategy.primary_tactic} strategy. "
            f"Recommended offer has {win_probability.win_probability:.1f}% win probability."
        )

        key_insights = [
            f"Seller urgency level: {psychology.urgency_level} ({psychology.urgency_score}/100)",
            f"Market leverage: {leverage.overall_leverage_score}/100 in {leverage.market_condition}",
            f"Optimal strategy: {strategy.primary_tactic}",
            f"Win probability: {win_probability.win_probability:.1f}%",
            f"Property pricing: {leverage.price_positioning}",
        ]

        action_items = [
            f"Execute {strategy.primary_tactic} strategy",
            f"Offer ${strategy.recommended_offer_price}",
            "Monitor seller response",
            "Prepare counter-strategy",
            "Track market changes",
        ]

        return executive_summary, key_insights, action_items

    async def _analyze_conversation_context(
        self, conversation_context: str, current_situation: str, intelligence: NegotiationIntelligence
    ) -> Dict[str, Any]:
        """Analyze conversation context for coaching insights"""

        context = f"""
        Analyze this negotiation conversation for coaching insights:
        
        Conversation: {conversation_context}
        Current Situation: {current_situation}
        
        Original Strategy: {intelligence.negotiation_strategy.primary_tactic}
        Seller Psychology: {intelligence.seller_psychology.motivation_type}, {intelligence.seller_psychology.urgency_level}
        
        Provide insights on:
        1. Seller emotional state
        2. Strategy effectiveness 
        3. Adjustment recommendations
        4. Risk factors
        """

        try:
            ai_response = await self.claude_assistant.analyze_with_context(context)
            return ai_response
        except Exception as e:
            logger.error(f"Conversation analysis failed: {e}")
            return {
                "seller_emotional_state": "neutral",
                "strategy_effectiveness": "moderate",
                "adjustment_recommendations": [],
                "risk_factors": [],
            }

    async def _generate_immediate_guidance(
        self,
        conversation_insights: Dict[str, Any],
        intelligence: NegotiationIntelligence,
        buyer_feedback: Optional[str],
        seller_response: Optional[str],
    ) -> str:
        """Generate immediate tactical guidance"""

        if seller_response and "counter" in seller_response.lower():
            return f"Seller countered - evaluate against {intelligence.negotiation_strategy.primary_tactic} strategy. Consider their {intelligence.seller_psychology.motivation_type} motivation in response."

        if buyer_feedback and "concerned" in buyer_feedback.lower():
            return f"Buyer concerns detected. Reassure using {intelligence.negotiation_strategy.primary_tactic} approach and emphasize {intelligence.win_probability.win_probability:.1f}% win probability."

        return f"Continue {intelligence.negotiation_strategy.primary_tactic} strategy. Seller {intelligence.seller_psychology.urgency_level} urgency supports current approach."

    async def _identify_tactical_adjustments(
        self, conversation_insights: Dict[str, Any], intelligence: NegotiationIntelligence, current_situation: str
    ) -> List[str]:
        """Identify needed tactical adjustments"""

        adjustments = []

        # Based on conversation insights
        if conversation_insights.get("strategy_effectiveness") == "low":
            adjustments.append("Consider shifting tactical approach")

        # Based on seller psychology
        if intelligence.seller_psychology.urgency_level.value == "high" and "timeline" not in current_situation:
            adjustments.append("Emphasize timeline advantages")

        # Based on market leverage
        if intelligence.market_leverage.overall_leverage_score > 80:
            adjustments.append("Leverage strong market position more assertively")

        return adjustments

    def _generate_next_steps(
        self,
        conversation_insights: Dict[str, Any],
        tactical_adjustments: List[str],
        intelligence: NegotiationIntelligence,
    ) -> List[str]:
        """Generate specific next steps"""

        next_steps = []

        # Always include core strategy elements
        next_steps.append(f"Execute {intelligence.negotiation_strategy.primary_tactic} approach")

        # Add tactical adjustments
        if tactical_adjustments:
            next_steps.extend(tactical_adjustments[:2])  # Top 2 adjustments

        # Add standard next steps
        next_steps.extend(["Monitor seller response patterns", "Prepare for potential counter-offer"])

        return next_steps[:5]  # Top 5 next steps

    async def _generate_conversation_suggestions(
        self, conversation_insights: Dict[str, Any], intelligence: NegotiationIntelligence, current_situation: str
    ) -> Dict[str, str]:
        """Generate specific conversation suggestions"""

        return {
            "opening": f"Lead with {intelligence.negotiation_strategy.primary_tactic} emphasis",
            "objection_handling": f"Address concerns using {intelligence.seller_psychology.motivation_type} motivation insights",
            "closing": f"Reinforce {intelligence.win_probability.win_probability:.1f}% win probability advantages",
        }

    def _identify_risk_alerts(
        self,
        conversation_insights: Dict[str, Any],
        intelligence: NegotiationIntelligence,
        seller_response: Optional[str],
    ) -> List[str]:
        """Identify negotiation risk alerts"""

        alerts = []

        # Win probability alerts
        if intelligence.win_probability.win_probability < 30:
            alerts.append("Low win probability - consider strategy adjustment")

        # Seller response alerts
        if seller_response:
            if "not interested" in seller_response.lower():
                alerts.append("Seller rejection signal - immediate strategy review needed")
            elif "other offers" in seller_response.lower():
                alerts.append("Competitive pressure increased - expedite decision timeline")

        # Conversation insight alerts
        risk_factors = conversation_insights.get("risk_factors", [])
        alerts.extend(risk_factors[:3])  # Top 3 risk factors

        return alerts

    def _update_performance_metrics(self, processing_time: int, intelligence: NegotiationIntelligence):
        """Update system performance metrics"""

        self.performance_metrics["total_analyses"] += 1

        # Update average processing time
        total = self.performance_metrics["total_analyses"]
        current_avg = self.performance_metrics["avg_processing_time_ms"]
        self.performance_metrics["avg_processing_time_ms"] = (current_avg * (total - 1) + processing_time) / total

        # Track win probability predictions (for future accuracy measurement)
        self.performance_metrics["win_rate_predictions"].append(
            {
                "property_id": intelligence.property_id,
                "predicted_probability": intelligence.win_probability.win_probability,
                "timestamp": intelligence.analysis_timestamp,
                "strategy": intelligence.negotiation_strategy.primary_tactic,
            }
        )

        # Track strategy usage
        strategy = intelligence.negotiation_strategy.primary_tactic
        if strategy not in self.performance_metrics["strategy_effectiveness"]:
            self.performance_metrics["strategy_effectiveness"][strategy] = {"count": 0, "total_probability": 0}

        self.performance_metrics["strategy_effectiveness"][strategy]["count"] += 1
        self.performance_metrics["strategy_effectiveness"][strategy]["total_probability"] += (
            intelligence.win_probability.win_probability
        )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""

        # Calculate strategy effectiveness averages
        strategy_averages = {}
        for strategy, data in self.performance_metrics["strategy_effectiveness"].items():
            if data["count"] > 0:
                strategy_averages[strategy] = data["total_probability"] / data["count"]

        return {
            "total_analyses": self.performance_metrics["total_analyses"],
            "avg_processing_time_ms": round(self.performance_metrics["avg_processing_time_ms"], 1),
            "active_negotiations": len(self.active_negotiations),
            "strategy_averages": strategy_averages,
            "prediction_history_count": len(self.performance_metrics["win_rate_predictions"]),
        }

    def cleanup_inactive_negotiations(self, hours_threshold: int = 24):
        """Clean up negotiations older than threshold"""

        cutoff = datetime.now() - timedelta(hours=hours_threshold)
        inactive_keys = [key for key, value in self.active_negotiations.items() if value["created_at"] < cutoff]

        for key in inactive_keys:
            del self.active_negotiations[key]

        logger.info(f"Cleaned up {len(inactive_keys)} inactive negotiations")


# Singleton instance
_ai_negotiation_partner = None


def get_ai_negotiation_partner() -> AINegotiationPartner:
    """Get singleton instance of AINegotiationPartner"""
    global _ai_negotiation_partner
    if _ai_negotiation_partner is None:
        _ai_negotiation_partner = AINegotiationPartner()
    return _ai_negotiation_partner
