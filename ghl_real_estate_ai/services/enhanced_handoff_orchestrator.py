"""
Enhanced Handoff Orchestration Service - Phase 4 Implementation
Intelligent Agent Transition & Context Management System
"""

import asyncio
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.models.intelligence_context import ConversationContext, CustomerProfile
from ghl_real_estate_ai.services.enhanced_intent_decoder import IntentAnalysisResult, IntentCategory, UrgencyLevel

logger = logging.getLogger(__name__)


class HandoffReason(Enum):
    """Reasons for agent handoff"""

    SPECIALIZATION_REQUIRED = "specialization_required"
    COMPLEXITY_ESCALATION = "complexity_escalation"
    HUMAN_INTERVENTION = "human_intervention"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CUSTOMER_REQUEST = "customer_request"
    WORKLOAD_BALANCING = "workload_balancing"
    EMERGENCY_ESCALATION = "emergency_escalation"


class HandoffStatus(Enum):
    """Handoff execution status"""

    INITIATED = "initiated"
    PREPARING = "preparing"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class AgentType(Enum):
    """Available agent types for routing"""

    JORGE_SELLER_BOT = "jorge_seller_bot"
    JORGE_BUYER_BOT = "jorge_buyer_bot"
    LEAD_BOT = "lead_bot"
    LUXURY_SPECIALIST = "luxury_specialist"
    INVESTMENT_SPECIALIST = "investment_specialist"
    HUMAN_AGENT = "human_agent"
    COMPLIANCE_SPECIALIST = "compliance_specialist"


@dataclass
class AgentAvailability:
    """Agent availability and performance metrics"""

    agent_id: str
    agent_type: AgentType
    is_available: bool
    current_load: int
    max_capacity: int
    average_response_time: float
    success_rate: float
    specialties: List[str]
    last_updated: datetime


@dataclass
class HandoffContext:
    """Comprehensive context for agent handoff"""

    handoff_id: str
    source_agent: str
    target_agent: str
    handoff_reason: HandoffReason
    conversation_context: Dict[str, Any]
    relationship_context: Dict[str, Any]
    business_context: Dict[str, Any]
    technical_context: Dict[str, Any]
    customer_preferences: Dict[str, Any]
    success_criteria: List[str]
    risk_factors: List[str]
    estimated_value: Optional[float]
    priority_level: int  # 1-5, 5 being highest
    created_timestamp: datetime


@dataclass
class HandoffExecution:
    """Handoff execution tracking"""

    handoff_id: str
    status: HandoffStatus
    source_agent: str
    target_agent: str
    start_time: datetime
    completion_time: Optional[datetime]
    preparation_duration: Optional[float]
    transition_duration: Optional[float]
    success_score: Optional[float]
    customer_satisfaction: Optional[float]
    context_preservation_score: Optional[float]
    failure_reason: Optional[str]
    rollback_reason: Optional[str]


class EnhancedHandoffOrchestrator:
    """
    Advanced handoff orchestration system with intelligent decision-making

    Features:
    - Intelligent handoff timing and agent selection
    - Complete context preservation and transfer
    - Multi-agent collaboration coordination
    - Performance tracking and optimization
    """

    def __init__(self):
        self.agent_registry: Dict[str, AgentAvailability] = {}
        self.active_handoffs: Dict[str, HandoffExecution] = {}
        self.handoff_history: List[HandoffExecution] = []
        self.performance_metrics: Dict[str, Any] = {}

        # Initialize agent routing criteria
        self.routing_criteria = self._initialize_routing_criteria()

        # Handoff success thresholds
        self.success_thresholds = {
            "context_preservation": 0.95,
            "customer_satisfaction": 0.9,
            "transition_time": 30.0,  # seconds
            "overall_success": 0.9,
        }

    async def analyze_handoff_necessity(
        self,
        conversation_context: ConversationContext,
        intent_analysis: IntentAnalysisResult,
        current_agent: str,
        customer_profile: Optional[CustomerProfile] = None,
    ) -> Tuple[bool, Optional[HandoffReason], Optional[str]]:
        """
        Analyze if handoff is necessary and determine target agent

        Returns:
            (should_handoff, handoff_reason, target_agent)
        """
        try:
            # Check for immediate escalation triggers
            if self._check_emergency_escalation(conversation_context, intent_analysis):
                return True, HandoffReason.EMERGENCY_ESCALATION, AgentType.HUMAN_AGENT.value

            # Analyze specialization requirements
            specialization_result = await self._analyze_specialization_needs(
                intent_analysis, conversation_context, customer_profile
            )

            if specialization_result[0]:
                return True, HandoffReason.SPECIALIZATION_REQUIRED, specialization_result[1]

            # Check complexity escalation needs
            complexity_score = await self._calculate_complexity_score(
                conversation_context, intent_analysis, customer_profile
            )

            if complexity_score > 0.8:
                target_agent = await self._determine_complexity_handler(complexity_score, intent_analysis)
                return True, HandoffReason.COMPLEXITY_ESCALATION, target_agent

            # Evaluate performance optimization opportunities
            performance_result = await self._evaluate_performance_optimization(
                current_agent, intent_analysis, conversation_context
            )

            if performance_result[0]:
                return True, HandoffReason.PERFORMANCE_OPTIMIZATION, performance_result[1]

            # Check workload balancing needs
            if await self._check_workload_balancing(current_agent):
                alternative_agent = await self._find_alternative_agent(current_agent, intent_analysis)
                if alternative_agent:
                    return True, HandoffReason.WORKLOAD_BALANCING, alternative_agent

            return False, None, None

        except Exception as e:
            logger.error(f"Handoff necessity analysis failed: {str(e)}", exc_info=True)
            return False, None, None

    async def execute_handoff(
        self,
        source_agent: str,
        target_agent: str,
        handoff_reason: HandoffReason,
        conversation_context: ConversationContext,
        intent_analysis: IntentAnalysisResult,
        customer_profile: Optional[CustomerProfile] = None,
    ) -> HandoffExecution:
        """
        Execute intelligent handoff with complete context preservation
        """
        handoff_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Initialize handoff tracking
            handoff_execution = HandoffExecution(
                handoff_id=handoff_id,
                status=HandoffStatus.INITIATED,
                source_agent=source_agent,
                target_agent=target_agent,
                start_time=start_time,
                completion_time=None,
                preparation_duration=None,
                transition_duration=None,
                success_score=None,
                customer_satisfaction=None,
                context_preservation_score=None,
                failure_reason=None,
                rollback_reason=None,
            )

            self.active_handoffs[handoff_id] = handoff_execution

            # Phase 1: Preparation
            prep_start = datetime.now()
            handoff_execution.status = HandoffStatus.PREPARING

            handoff_context = await self._prepare_handoff_context(
                handoff_id,
                source_agent,
                target_agent,
                handoff_reason,
                conversation_context,
                intent_analysis,
                customer_profile,
            )

            # Validate target agent availability
            if not await self._validate_target_availability(target_agent):
                alternative_target = await self._find_alternative_agent(target_agent, intent_analysis)
                if alternative_target:
                    target_agent = alternative_target
                    handoff_context.target_agent = target_agent
                else:
                    raise Exception(f"Target agent {target_agent} not available and no alternatives found")

            prep_duration = (datetime.now() - prep_start).total_seconds()
            handoff_execution.preparation_duration = prep_duration

            # Phase 2: Context Transfer
            transfer_start = datetime.now()
            handoff_execution.status = HandoffStatus.TRANSFERRING

            context_transfer_success = await self._transfer_context_to_agent(target_agent, handoff_context)

            if not context_transfer_success:
                raise Exception("Context transfer failed")

            # Phase 3: Customer Introduction
            introduction_success = await self._execute_customer_introduction(
                handoff_context, source_agent, target_agent
            )

            if not introduction_success:
                raise Exception("Customer introduction failed")

            transfer_duration = (datetime.now() - transfer_start).total_seconds()
            handoff_execution.transition_duration = transfer_duration

            # Phase 4: Validation & Completion
            handoff_execution.status = HandoffStatus.COMPLETED
            handoff_execution.completion_time = datetime.now()

            # Calculate success metrics
            success_metrics = await self._calculate_handoff_success(handoff_execution, handoff_context)
            handoff_execution.success_score = success_metrics["overall_success"]
            handoff_execution.customer_satisfaction = success_metrics["customer_satisfaction"]
            handoff_execution.context_preservation_score = success_metrics["context_preservation"]

            # Log successful handoff
            total_duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Handoff {handoff_id} completed successfully in {total_duration:.1f}s, "
                f"success_score: {handoff_execution.success_score:.2f}"
            )

            # Update performance metrics
            await self._update_performance_metrics(handoff_execution)

            return handoff_execution

        except Exception as e:
            logger.error(f"Handoff {handoff_id} failed: {str(e)}", exc_info=True)

            # Handle failure and potential rollback
            handoff_execution.status = HandoffStatus.FAILED
            handoff_execution.failure_reason = str(e)
            handoff_execution.completion_time = datetime.now()

            # Attempt rollback if necessary
            rollback_success = await self._attempt_rollback(handoff_execution, conversation_context)
            if rollback_success:
                handoff_execution.status = HandoffStatus.ROLLED_BACK

            return handoff_execution

        finally:
            # Clean up active handoff tracking
            if handoff_id in self.active_handoffs:
                self.handoff_history.append(self.active_handoffs[handoff_id])
                del self.active_handoffs[handoff_id]

    async def orchestrate_parallel_consultation(
        self,
        primary_agent: str,
        consulting_agents: List[str],
        consultation_topic: str,
        conversation_context: ConversationContext,
        intent_analysis: IntentAnalysisResult,
    ) -> Dict[str, Any]:
        """
        Coordinate parallel expert consultation without customer handoff
        """
        consultation_id = str(uuid.uuid4())

        try:
            # Prepare consultation context for each specialist
            consultation_tasks = []

            for consultant in consulting_agents:
                task = self._create_consultation_task(
                    consultant, consultation_topic, conversation_context, intent_analysis
                )
                consultation_tasks.append(task)

            # Execute consultations in parallel
            consultation_results = await asyncio.gather(*consultation_tasks, return_exceptions=True)

            # Aggregate expert insights
            aggregated_insights = await self._aggregate_consultation_results(
                consulting_agents, consultation_results, consultation_topic
            )

            # Prepare recommendations for primary agent
            recommendations = await self._prepare_consultation_recommendations(
                primary_agent, aggregated_insights, consultation_topic
            )

            logger.info(f"Parallel consultation {consultation_id} completed with {len(consulting_agents)} experts")

            return {
                "consultation_id": consultation_id,
                "expert_insights": aggregated_insights,
                "recommendations": recommendations,
                "confidence_score": self._calculate_consultation_confidence(aggregated_insights),
                "execution_time": datetime.now(),
            }

        except Exception as e:
            logger.error(f"Parallel consultation {consultation_id} failed: {str(e)}", exc_info=True)
            return {
                "consultation_id": consultation_id,
                "error": str(e),
                "fallback_recommendations": ["Proceed with standard agent approach"],
                "execution_time": datetime.now(),
            }

    async def _analyze_specialization_needs(
        self,
        intent_analysis: IntentAnalysisResult,
        conversation_context: ConversationContext,
        customer_profile: Optional[CustomerProfile],
    ) -> Tuple[bool, Optional[str]]:
        """Determine if specialized agent is required"""

        # High-value property specialization
        if intent_analysis.budget_range and intent_analysis.budget_range[0] > 1000000:
            return True, AgentType.LUXURY_SPECIALIST.value

        # Investment property specialization
        if intent_analysis.primary_intent == IntentCategory.INVESTMENT_OPPORTUNITY:
            return True, AgentType.INVESTMENT_SPECIALIST.value

        # Complex legal/compliance scenarios
        if any("legal" in risk or "compliance" in risk for risk in intent_analysis.risk_factors):
            return True, AgentType.COMPLIANCE_SPECIALIST.value

        # Immediate intent with high confidence - route to specialized Jorge bots
        if intent_analysis.confidence_score >= 0.9:
            if intent_analysis.primary_intent == IntentCategory.IMMEDIATE_BUYER:
                return True, AgentType.JORGE_BUYER_BOT.value
            elif intent_analysis.primary_intent == IntentCategory.IMMEDIATE_SELLER:
                return True, AgentType.JORGE_SELLER_BOT.value

        return False, None

    async def _calculate_complexity_score(
        self,
        conversation_context: ConversationContext,
        intent_analysis: IntentAnalysisResult,
        customer_profile: Optional[CustomerProfile],
    ) -> float:
        """Calculate conversation complexity score"""

        complexity_score = 0.0

        # Intent uncertainty
        if intent_analysis.confidence_score < 0.7:
            complexity_score += 0.2

        # Multiple risk factors
        complexity_score += len(intent_analysis.risk_factors) * 0.1

        # High-value transaction
        if intent_analysis.budget_range and intent_analysis.budget_range[0] > 750000:
            complexity_score += 0.2

        # Timeline pressure
        if intent_analysis.urgency_level == UrgencyLevel.IMMEDIATE:
            complexity_score += 0.15

        # Long conversation history without resolution
        if hasattr(conversation_context, "message_count") and conversation_context.message_count > 15:
            complexity_score += 0.2

        # Emotional distress indicators
        if any("emotional" in factor for factor in intent_analysis.risk_factors):
            complexity_score += 0.3

        return min(complexity_score, 1.0)

    async def _prepare_handoff_context(
        self,
        handoff_id: str,
        source_agent: str,
        target_agent: str,
        handoff_reason: HandoffReason,
        conversation_context: ConversationContext,
        intent_analysis: IntentAnalysisResult,
        customer_profile: Optional[CustomerProfile],
    ) -> HandoffContext:
        """Prepare comprehensive handoff context package"""

        # Conversation context
        conversation_dict = {
            "intent_analysis": asdict(intent_analysis),
            "message_history": getattr(conversation_context, "messages", []),
            "conversation_state": getattr(conversation_context, "state", {}),
            "progress_milestones": getattr(conversation_context, "milestones", []),
        }

        # Relationship context
        relationship_dict = {
            "rapport_level": self._assess_rapport_level(conversation_context),
            "communication_style": self._determine_communication_style(conversation_context),
            "emotional_state": self._assess_emotional_state(intent_analysis),
            "trust_indicators": self._identify_trust_indicators(conversation_context),
        }

        # Business context
        business_dict = {
            "opportunity_value": self._estimate_opportunity_value(intent_analysis),
            "timeline_pressure": intent_analysis.urgency_level.value,
            "competition_risk": self._assess_competition_risk(intent_analysis),
            "referral_potential": self._assess_referral_potential(customer_profile),
        }

        # Technical context
        technical_dict = {
            "conversation_duration": getattr(conversation_context, "duration", 0),
            "interaction_count": getattr(conversation_context, "interaction_count", 0),
            "channel": getattr(conversation_context, "channel", "unknown"),
            "device_info": getattr(conversation_context, "device_info", {}),
        }

        # Success criteria
        success_criteria = self._define_success_criteria(intent_analysis, handoff_reason)

        return HandoffContext(
            handoff_id=handoff_id,
            source_agent=source_agent,
            target_agent=target_agent,
            handoff_reason=handoff_reason,
            conversation_context=conversation_dict,
            relationship_context=relationship_dict,
            business_context=business_dict,
            technical_context=technical_dict,
            customer_preferences=self._extract_customer_preferences(intent_analysis),
            success_criteria=success_criteria,
            risk_factors=intent_analysis.risk_factors,
            estimated_value=business_dict["opportunity_value"],
            priority_level=self._calculate_priority_level(intent_analysis),
            created_timestamp=datetime.now(),
        )

    async def _transfer_context_to_agent(self, target_agent: str, handoff_context: HandoffContext) -> bool:
        """Transfer complete context to receiving agent"""

        try:
            # Prepare agent-specific context package
            agent_context_package = self._prepare_agent_context_package(target_agent, handoff_context)

            # Simulate context transfer (in production, this would integrate with agent systems)
            logger.info(f"Transferring context to {target_agent}: {len(str(agent_context_package))} bytes")

            # Validate context completeness
            context_validation = self._validate_context_transfer(agent_context_package)

            if not context_validation["complete"]:
                logger.warning(f"Context transfer incomplete: {context_validation['missing_fields']}")
                return False

            return True

        except Exception as e:
            logger.error(f"Context transfer to {target_agent} failed: {str(e)}")
            return False

    async def _execute_customer_introduction(
        self, handoff_context: HandoffContext, source_agent: str, target_agent: str
    ) -> bool:
        """Execute seamless customer introduction"""

        try:
            # Prepare introduction script based on agent type and context
            introduction_script = self._generate_introduction_script(handoff_context, source_agent, target_agent)

            # Log introduction for monitoring
            logger.info(
                f"Customer introduction from {source_agent} to {target_agent}: {handoff_context.handoff_reason.value}"
            )

            # In production, this would trigger the actual introduction
            # For now, we simulate successful introduction
            return True

        except Exception as e:
            logger.error(f"Customer introduction failed: {str(e)}")
            return False

    def _initialize_routing_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Initialize agent routing criteria matrix"""

        return {
            AgentType.JORGE_SELLER_BOT.value: {
                "intent_confidence": 0.9,
                "intent_categories": [IntentCategory.IMMEDIATE_SELLER],
                "max_property_value": 2000000,
                "complexity_threshold": 0.7,
            },
            AgentType.JORGE_BUYER_BOT.value: {
                "intent_confidence": 0.9,
                "intent_categories": [IntentCategory.IMMEDIATE_BUYER],
                "financing_ready": True,
                "urgency_levels": [UrgencyLevel.IMMEDIATE, UrgencyLevel.MODERATE],
            },
            AgentType.LUXURY_SPECIALIST.value: {
                "min_property_value": 1000000,
                "buyer_sophistication": "high",
                "complexity_threshold": 0.8,
            },
            AgentType.HUMAN_AGENT.value: {
                "complexity_threshold": 0.8,
                "emotional_distress": True,
                "legal_complexity": "high",
            },
        }

    def _check_emergency_escalation(
        self, conversation_context: ConversationContext, intent_analysis: IntentAnalysisResult
    ) -> bool:
        """Check for emergency escalation triggers"""

        emergency_indicators = [
            "lawsuit",
            "legal action",
            "attorney",
            "threat",
            "discrimination",
            "harassment",
            "emergency",
            "urgent legal",
        ]

        # Check for legal/emergency keywords in recent messages
        recent_text = " ".join(getattr(conversation_context, "messages", [])[-3:])

        return any(indicator in recent_text.lower() for indicator in emergency_indicators)

    def _assess_rapport_level(self, conversation_context: ConversationContext) -> float:
        """Assess customer rapport level (0.0 to 1.0)"""
        # Simplified assessment - in production would analyze sentiment, engagement, etc.
        return 0.7  # Default medium rapport

    def _determine_communication_style(self, conversation_context: ConversationContext) -> str:
        """Determine preferred communication style"""
        # Simplified determination - in production would analyze language patterns
        return "professional"  # Default style

    def _assess_emotional_state(self, intent_analysis: IntentAnalysisResult) -> str:
        """Assess customer emotional state"""
        if any("emotional" in factor for factor in intent_analysis.risk_factors):
            return "stressed"
        elif intent_analysis.urgency_level == UrgencyLevel.IMMEDIATE:
            return "urgent"
        else:
            return "neutral"

    def _estimate_opportunity_value(self, intent_analysis: IntentAnalysisResult) -> Optional[float]:
        """Estimate potential business value"""
        if intent_analysis.budget_range:
            # Assume 3% commission on average
            return intent_analysis.budget_range[1] * 0.03
        return None

    def _calculate_priority_level(self, intent_analysis: IntentAnalysisResult) -> int:
        """Calculate handoff priority level (1-5)"""
        priority = 3  # Default medium priority

        if intent_analysis.confidence_score >= 0.9:
            priority += 1

        if intent_analysis.urgency_level == UrgencyLevel.IMMEDIATE:
            priority += 1

        if intent_analysis.budget_range and intent_analysis.budget_range[0] > 1000000:
            priority += 1

        return min(priority, 5)

    def _generate_introduction_script(
        self, handoff_context: HandoffContext, source_agent: str, target_agent: str
    ) -> str:
        """Generate personalized introduction script"""

        base_scripts = {
            AgentType.JORGE_BUYER_BOT.value: "I'm connecting you with our buyer specialist who can help you find the perfect property...",
            AgentType.JORGE_SELLER_BOT.value: "Let me introduce you to our listing specialist who will help maximize your property value...",
            AgentType.HUMAN_AGENT.value: "I'm connecting you with one of our senior agents who specializes in your situation...",
        }

        return base_scripts.get(target_agent, "I'm connecting you with a specialist...")

    async def _calculate_handoff_success(
        self, handoff_execution: HandoffExecution, handoff_context: HandoffContext
    ) -> Dict[str, float]:
        """Calculate comprehensive handoff success metrics"""

        metrics = {}

        # Context preservation (95%+ target)
        metrics["context_preservation"] = 0.98  # Simulated - would measure actual preservation

        # Customer satisfaction (90%+ target)
        metrics["customer_satisfaction"] = 0.92  # Simulated - would get from customer feedback

        # Transition time (30s target)
        total_time = handoff_execution.preparation_duration + handoff_execution.transition_duration
        time_score = 1.0 if total_time <= 30.0 else max(0.5, 30.0 / total_time)
        metrics["transition_time_score"] = time_score

        # Overall success calculation
        metrics["overall_success"] = (
            metrics["context_preservation"] * 0.4
            + metrics["customer_satisfaction"] * 0.4
            + metrics["transition_time_score"] * 0.2
        )

        return metrics

    # Additional helper methods...
    def _extract_customer_preferences(self, intent_analysis: IntentAnalysisResult) -> Dict[str, Any]:
        """Extract customer preferences from intent analysis"""
        return {
            "locations": intent_analysis.location_preferences,
            "budget_range": intent_analysis.budget_range,
            "timeline": intent_analysis.predicted_timeline,
            "motivators": intent_analysis.key_motivators,
        }

    def _define_success_criteria(
        self, intent_analysis: IntentAnalysisResult, handoff_reason: HandoffReason
    ) -> List[str]:
        """Define success criteria for handoff"""
        criteria = ["maintain_customer_satisfaction", "preserve_conversation_context"]

        if handoff_reason == HandoffReason.SPECIALIZATION_REQUIRED:
            criteria.append("leverage_specialized_expertise")

        if intent_analysis.urgency_level == UrgencyLevel.IMMEDIATE:
            criteria.append("expedite_resolution")

        return criteria

    async def _validate_target_availability(self, target_agent: str) -> bool:
        """Validate target agent availability"""
        # Simplified check - in production would check actual agent status
        return target_agent in self.agent_registry

    async def _update_performance_metrics(self, handoff_execution: HandoffExecution) -> None:
        """Update handoff performance metrics"""
        # Update success rates, timing metrics, etc.
        logger.info(f"Updated performance metrics for handoff {handoff_execution.handoff_id}")

    # ... Additional helper methods for complete implementation


# Factory functions


async def create_enhanced_handoff_orchestrator() -> EnhancedHandoffOrchestrator:
    """Factory function to create configured handoff orchestrator"""
    return EnhancedHandoffOrchestrator()


if __name__ == "__main__":
    # Example usage
    async def main():
        orchestrator = await create_enhanced_handoff_orchestrator()

        # Test handoff necessity analysis
        from ghl_real_estate_ai.models.intelligence_context import ConversationContext
        from ghl_real_estate_ai.services.enhanced_intent_decoder import analyze_customer_intent

        # Sample analysis
        intent_result = await analyze_customer_intent(
            "I'm pre-approved for $800k and need to buy in West Lake Hills ASAP - my lease ends in 3 weeks!"
        )

        conversation_context = ConversationContext()  # Simplified for example

        should_handoff, reason, target = await orchestrator.analyze_handoff_necessity(
            conversation_context, intent_result, "lead_bot"
        )

        print(f"Should handoff: {should_handoff}")
        if should_handoff:
            print(f"Reason: {reason.value}")
            print(f"Target agent: {target}")

    asyncio.run(main())
