"""
Churn Intervention Orchestrator - Automated Response System

This module orchestrates automated interventions based on churn risk predictions.
It integrates with existing engagement systems to deliver timely, personalized
interventions that reduce churn probability through strategic outreach.

Key Features:
- Risk-based intervention triggering with escalation logic
- Multi-channel campaign orchestration (email → SMS → phone)
- Integration with ReengagementEngine and GHL workflows
- A/B testing framework for intervention effectiveness
- Rate limiting and duplicate prevention
- Comprehensive tracking and analytics

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Internal imports
from .churn_prediction_engine import ChurnPrediction, ChurnRiskTier
from .ghl_service import GHLService
from .memory_service import MemoryService
from .reengagement_engine import ReengagementEngine

# Configure logging
logger = logging.getLogger(__name__)


class InterventionType(Enum):
    """Types of automated interventions"""

    EMAIL_REENGAGEMENT = "email_reengagement"
    SMS_URGENT = "sms_urgent"
    PHONE_CALLBACK = "phone_callback"
    PROPERTY_ALERT = "property_alert"
    MARKET_UPDATE = "market_update"
    PERSONAL_CONSULTATION = "personal_consultation"
    INCENTIVE_OFFER = "incentive_offer"
    AGENT_ESCALATION = "agent_escalation"


class InterventionStatus(Enum):
    """Status of intervention execution"""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InterventionConfig:
    """Configuration for intervention campaigns"""

    intervention_type: InterventionType
    trigger_risk_tier: ChurnRiskTier
    delay_minutes: int  # Delay before execution
    max_frequency: timedelta  # Minimum time between same intervention type
    escalation_delay: timedelta  # Time to wait before escalating
    success_metrics: List[str]  # Metrics to track success
    template_id: Optional[str] = None
    priority_score: int = 5  # 1-10 priority for scheduling


@dataclass
class InterventionExecution:
    """Record of intervention execution attempt"""

    execution_id: str
    lead_id: str
    intervention_type: InterventionType
    trigger_prediction: ChurnPrediction

    # Execution details
    scheduled_time: datetime
    executed_time: Optional[datetime] = None
    status: InterventionStatus = InterventionStatus.PENDING

    # Channel details
    channel: str = ""  # email, sms, phone, ghl_workflow
    template_used: str = ""
    personalization_data: Dict[str, Any] = None

    # Results tracking
    delivery_status: str = ""
    engagement_metrics: Dict[str, float] = None
    success_indicators: Dict[str, bool] = None

    # Follow-up planning
    next_escalation: Optional[datetime] = None
    escalation_type: Optional[InterventionType] = None


class InterventionOrchestrator:
    """
    Orchestrates automated interventions based on churn risk predictions

    This system:
    1. Monitors churn predictions for intervention triggers
    2. Schedules appropriate interventions based on risk tier and timing
    3. Executes multi-channel campaigns through existing services
    4. Tracks intervention effectiveness and optimizes strategies
    5. Prevents spam and manages intervention frequency
    """

    def __init__(self, reengagement_engine: ReengagementEngine, memory_service: MemoryService, ghl_service: GHLService):

        self.reengagement_engine = reengagement_engine
        self.memory_service = memory_service
        self.ghl_service = ghl_service
        self.logger = logging.getLogger(__name__ + ".InterventionOrchestrator")

        # Intervention tracking
        self._active_interventions: Dict[str, List[InterventionExecution]] = defaultdict(list)
        self._intervention_history: List[InterventionExecution] = []
        self._last_intervention_times: Dict[Tuple[str, InterventionType], datetime] = {}

        # Configuration
        self._intervention_configs = self._initialize_intervention_configs()
        self._max_daily_interventions = 3  # Per lead
        self._global_rate_limit = 100  # Per hour across all leads

        # A/B Testing
        self._ab_test_variants: Dict[str, Dict] = {}
        self._ab_test_assignments: Dict[str, str] = {}

        self.logger.info("InterventionOrchestrator initialized successfully")

    async def process_churn_predictions(
        self, predictions: Dict[str, ChurnPrediction]
    ) -> Dict[str, List[InterventionExecution]]:
        """
        Process churn predictions and trigger appropriate interventions

        Args:
            predictions: Dict of lead_id -> ChurnPrediction

        Returns:
            Dict of lead_id -> list of scheduled interventions
        """
        self.logger.info(f"Processing {len(predictions)} churn predictions for intervention orchestration")

        scheduled_interventions = {}

        for lead_id, prediction in predictions.items():
            try:
                # Determine required interventions
                required_interventions = await self._analyze_intervention_requirements(lead_id, prediction)

                # Filter out interventions that violate rate limits
                viable_interventions = await self._filter_rate_limited_interventions(lead_id, required_interventions)

                # Schedule viable interventions
                scheduled = await self._schedule_interventions(lead_id, viable_interventions, prediction)

                if scheduled:
                    scheduled_interventions[lead_id] = scheduled
                    self.logger.info(f"Scheduled {len(scheduled)} interventions for lead {lead_id}")

            except Exception as e:
                self.logger.error(f"Error processing interventions for lead {lead_id}: {str(e)}")

        return scheduled_interventions

    async def execute_pending_interventions(self) -> Dict[str, bool]:
        """
        Execute all pending interventions that are due for execution

        Returns:
            Dict of execution_id -> success status
        """
        execution_results = {}
        current_time = datetime.now()

        # Find pending interventions ready for execution
        pending_interventions = []
        for lead_interventions in self._active_interventions.values():
            for intervention in lead_interventions:
                if intervention.status == InterventionStatus.PENDING and intervention.scheduled_time <= current_time:
                    pending_interventions.append(intervention)

        self.logger.info(f"Executing {len(pending_interventions)} pending interventions")

        # Execute interventions
        for intervention in pending_interventions:
            try:
                intervention.status = InterventionStatus.EXECUTING
                success = await self._execute_intervention(intervention)

                if success:
                    intervention.status = InterventionStatus.COMPLETED
                    intervention.executed_time = current_time
                    await self._schedule_follow_up_if_needed(intervention)
                else:
                    intervention.status = InterventionStatus.FAILED

                execution_results[intervention.execution_id] = success

            except Exception as e:
                self.logger.error(f"Error executing intervention {intervention.execution_id}: {str(e)}")
                intervention.status = InterventionStatus.FAILED
                execution_results[intervention.execution_id] = False

        return execution_results

    async def _analyze_intervention_requirements(
        self, lead_id: str, prediction: ChurnPrediction
    ) -> List[InterventionType]:
        """Analyze churn prediction to determine required interventions"""
        required_interventions = []

        # Risk tier based interventions
        risk_tier_interventions = {
            ChurnRiskTier.CRITICAL: [
                InterventionType.AGENT_ESCALATION,
                InterventionType.PHONE_CALLBACK,
                InterventionType.INCENTIVE_OFFER,
            ],
            ChurnRiskTier.HIGH: [
                InterventionType.PHONE_CALLBACK,
                InterventionType.PERSONAL_CONSULTATION,
                InterventionType.PROPERTY_ALERT,
            ],
            ChurnRiskTier.MEDIUM: [
                InterventionType.SMS_URGENT,
                InterventionType.EMAIL_REENGAGEMENT,
                InterventionType.MARKET_UPDATE,
            ],
            ChurnRiskTier.LOW: [InterventionType.EMAIL_REENGAGEMENT],
        }

        required_interventions.extend(risk_tier_interventions.get(prediction.risk_tier, []))

        # Factor-specific interventions
        for factor, importance in prediction.top_risk_factors[:3]:
            factor_interventions = await self._get_factor_specific_interventions(factor, importance)
            required_interventions.extend(factor_interventions)

        # Remove duplicates while preserving order
        seen = set()
        unique_interventions = []
        for intervention in required_interventions:
            if intervention not in seen:
                seen.add(intervention)
                unique_interventions.append(intervention)

        return unique_interventions

    async def _get_factor_specific_interventions(self, factor: str, importance: float) -> List[InterventionType]:
        """Get interventions specific to risk factors"""
        factor_interventions = {
            "days_since_last_interaction": [InterventionType.EMAIL_REENGAGEMENT, InterventionType.SMS_URGENT],
            "response_rate_7d": [InterventionType.PHONE_CALLBACK],
            "engagement_trend": [InterventionType.PROPERTY_ALERT, InterventionType.MARKET_UPDATE],
            "stage_stagnation_days": [InterventionType.PERSONAL_CONSULTATION],
            "email_open_rate": [InterventionType.SMS_URGENT],
            "call_pickup_rate": [InterventionType.EMAIL_REENGAGEMENT],
        }

        interventions = factor_interventions.get(factor, [])

        # Only include high-importance factor interventions
        if importance > 0.15:
            return interventions
        return []

    async def _filter_rate_limited_interventions(
        self, lead_id: str, interventions: List[InterventionType]
    ) -> List[InterventionType]:
        """Filter interventions based on rate limiting rules"""
        current_time = datetime.now()
        viable_interventions = []

        # Check daily intervention limit per lead
        daily_count = await self._get_daily_intervention_count(lead_id)
        if daily_count >= self._max_daily_interventions:
            self.logger.warning(f"Daily intervention limit reached for lead {lead_id}")
            return []

        for intervention_type in interventions:
            # Check frequency limits
            last_time_key = (lead_id, intervention_type)
            if last_time_key in self._last_intervention_times:
                config = self._intervention_configs.get(intervention_type)
                if config:
                    time_since_last = current_time - self._last_intervention_times[last_time_key]
                    if time_since_last < config.max_frequency:
                        self.logger.debug(f"Intervention {intervention_type.value} rate limited for lead {lead_id}")
                        continue

            viable_interventions.append(intervention_type)

            # Respect daily limit
            if len(viable_interventions) + daily_count >= self._max_daily_interventions:
                break

        return viable_interventions

    async def _schedule_interventions(
        self, lead_id: str, interventions: List[InterventionType], prediction: ChurnPrediction
    ) -> List[InterventionExecution]:
        """Schedule interventions with appropriate timing and escalation"""
        scheduled = []
        current_time = datetime.now()

        # Sort interventions by priority and urgency
        intervention_priorities = [
            (intervention, self._intervention_configs[intervention].priority_score)
            for intervention in interventions
            if intervention in self._intervention_configs
        ]
        intervention_priorities.sort(key=lambda x: x[1], reverse=True)

        cumulative_delay = 0
        for intervention_type, _ in intervention_priorities:
            config = self._intervention_configs[intervention_type]

            # Calculate scheduling time
            scheduled_time = current_time + timedelta(minutes=config.delay_minutes + cumulative_delay)

            # Create intervention execution record
            execution = InterventionExecution(
                execution_id=f"{lead_id}_{intervention_type.value}_{int(current_time.timestamp())}",
                lead_id=lead_id,
                intervention_type=intervention_type,
                trigger_prediction=prediction,
                scheduled_time=scheduled_time,
                personalization_data=await self._prepare_personalization_data(lead_id, prediction),
            )

            # Set up escalation if applicable
            if config.escalation_delay:
                execution.next_escalation = scheduled_time + config.escalation_delay
                execution.escalation_type = self._get_escalation_intervention(intervention_type)

            scheduled.append(execution)
            self._active_interventions[lead_id].append(execution)

            # Add delay between interventions to avoid overwhelming
            cumulative_delay += 15  # 15 minutes between each intervention

        return scheduled

    async def _execute_intervention(self, intervention: InterventionExecution) -> bool:
        """Execute a specific intervention"""
        try:
            self.logger.info(
                f"Executing intervention {intervention.intervention_type.value} for lead {intervention.lead_id}"
            )

            # Determine execution channel and method
            execution_method = self._get_execution_method(intervention.intervention_type)

            # Execute through appropriate service
            if execution_method == "reengagement_engine":
                success = await self._execute_via_reengagement_engine(intervention)
            elif execution_method == "ghl_workflow":
                success = await self._execute_via_ghl_workflow(intervention)
            elif execution_method == "direct_outreach":
                success = await self._execute_direct_outreach(intervention)
            else:
                self.logger.error(f"Unknown execution method: {execution_method}")
                return False

            # Record execution timing
            self._last_intervention_times[(intervention.lead_id, intervention.intervention_type)] = datetime.now()

            # Track execution metrics
            await self._track_intervention_metrics(intervention, success)

            return success

        except Exception as e:
            self.logger.error(f"Error executing intervention: {str(e)}")
            return False

    async def _execute_via_reengagement_engine(self, intervention: InterventionExecution) -> bool:
        """Execute intervention through the ReengagementEngine"""
        try:
            # Map intervention types to reengagement campaigns
            campaign_mapping = {
                InterventionType.EMAIL_REENGAGEMENT: "high_intent_reengagement",
                InterventionType.PROPERTY_ALERT: "property_match_alert",
                InterventionType.MARKET_UPDATE: "market_insights_campaign",
            }

            campaign_type = campaign_mapping.get(intervention.intervention_type)
            if not campaign_type:
                return False

            # Trigger reengagement campaign with personalization
            result = await self.reengagement_engine.trigger_reengagement_campaign(
                lead_id=intervention.lead_id,
                campaign_type=campaign_type,
                personalization_data=intervention.personalization_data,
                urgency_level=intervention.trigger_prediction.intervention_urgency,
            )

            intervention.channel = "email"
            intervention.template_used = campaign_type
            intervention.delivery_status = "sent" if result.get("success") else "failed"

            return result.get("success", False)

        except Exception as e:
            self.logger.error(f"Error executing via reengagement engine: {str(e)}")
            return False

    async def _execute_via_ghl_workflow(self, intervention: InterventionExecution) -> bool:
        """Execute intervention through GHL workflow automation"""
        try:
            # Map intervention types to GHL workflows
            workflow_mapping = {
                InterventionType.SMS_URGENT: "urgent_followup_sms",
                InterventionType.PHONE_CALLBACK: "agent_callback_scheduling",
                InterventionType.PERSONAL_CONSULTATION: "consultation_booking",
                InterventionType.AGENT_ESCALATION: "urgent_agent_assignment",
            }

            workflow_id = workflow_mapping.get(intervention.intervention_type)
            if not workflow_id:
                return False

            # Trigger GHL workflow
            result = await self.ghl_service.trigger_workflow(
                contact_id=intervention.lead_id, workflow_id=workflow_id, custom_data=intervention.personalization_data
            )

            intervention.channel = "ghl_workflow"
            intervention.template_used = workflow_id
            intervention.delivery_status = "triggered" if result.get("success") else "failed"

            return result.get("success", False)

        except Exception as e:
            self.logger.error(f"Error executing via GHL workflow: {str(e)}")
            return False

    async def _execute_direct_outreach(self, intervention: InterventionExecution) -> bool:
        """Execute direct outreach intervention"""
        try:
            if intervention.intervention_type == InterventionType.INCENTIVE_OFFER:
                # Create special incentive offer
                result = await self._create_incentive_offer(intervention)
            else:
                self.logger.warning(f"Direct outreach not implemented for {intervention.intervention_type.value}")
                return False

            return result.get("success", False)

        except Exception as e:
            self.logger.error(f"Error executing direct outreach: {str(e)}")
            return False

    async def _create_incentive_offer(self, intervention: InterventionExecution) -> Dict[str, Any]:
        """Create and deliver special incentive offer for critical churn risk"""
        # This would integrate with incentive/promotion systems
        # For now, create a placeholder
        offer_data = {
            "lead_id": intervention.lead_id,
            "offer_type": "churn_prevention",
            "discount_percentage": 5.0,  # 5% off closing costs
            "expiry_date": datetime.now() + timedelta(days=7),
            "personalized_message": intervention.personalization_data.get("incentive_message", ""),
        }

        # In production, this would create actual offers in the system
        intervention.channel = "incentive_system"
        intervention.template_used = "churn_prevention_offer"
        intervention.delivery_status = "created"

        return {"success": True, "offer_id": f"offer_{intervention.execution_id}"}

    async def _prepare_personalization_data(self, lead_id: str, prediction: ChurnPrediction) -> Dict[str, Any]:
        """Prepare personalization data for interventions"""
        try:
            # Get lead context
            lead_context = await self.memory_service.get_lead_context(lead_id)

            personalization = {
                "lead_name": lead_context.get("name", "Valued Client"),
                "risk_score": f"{prediction.risk_score_14d:.0f}%",
                "risk_tier": prediction.risk_tier.value,
                "top_risk_factor": prediction.top_risk_factors[0][0] if prediction.top_risk_factors else "engagement",
                "recommended_actions": prediction.recommended_actions[:2],  # Top 2 actions
                "urgency_level": prediction.intervention_urgency,
                # Property preferences
                "preferred_locations": lead_context.get("preferences", {}).get("locations", []),
                "budget_range": lead_context.get("preferences", {}).get("budget_range", ""),
                "property_types": lead_context.get("preferences", {}).get("property_types", []),
                # Contextual data
                "days_since_interaction": prediction.feature_vector.get("days_since_last_interaction", 0),
                "last_property_viewed": lead_context.get("last_property_viewed", {}),
                # Dynamic content
                "incentive_message": self._generate_incentive_message(prediction),
                "urgency_message": self._generate_urgency_message(prediction),
            }

            return personalization

        except Exception as e:
            self.logger.error(f"Error preparing personalization data: {str(e)}")
            return {"lead_name": "Valued Client"}

    def _generate_incentive_message(self, prediction: ChurnPrediction) -> str:
        """Generate personalized incentive message based on risk factors"""
        if prediction.risk_tier == ChurnRiskTier.CRITICAL:
            return (
                "We value your business and would like to offer you exclusive benefits to help with your home search."
            )
        elif prediction.risk_tier == ChurnRiskTier.HIGH:
            return "Let us help make your home buying journey smoother with personalized assistance."
        else:
            return "We're here to support you throughout your home buying process."

    def _generate_urgency_message(self, prediction: ChurnPrediction) -> str:
        """Generate urgency message based on market conditions and risk"""
        urgency_messages = {
            "immediate": "Time-sensitive opportunity - let's connect today",
            "urgent": "Important updates about your home search",
            "moderate": "Checking in on your home buying progress",
            "low": "Staying connected on your home search",
        }
        return urgency_messages.get(prediction.intervention_urgency, "Following up on your home search")

    async def _schedule_follow_up_if_needed(self, intervention: InterventionExecution):
        """Schedule follow-up interventions based on escalation rules"""
        if intervention.next_escalation and intervention.escalation_type:
            # Check if escalation is still needed (intervention might have been successful)
            needs_escalation = await self._check_if_escalation_needed(intervention)

            if needs_escalation:
                escalation_intervention = InterventionExecution(
                    execution_id=f"{intervention.lead_id}_{intervention.escalation_type.value}_escalation_{int(datetime.now().timestamp())}",
                    lead_id=intervention.lead_id,
                    intervention_type=intervention.escalation_type,
                    trigger_prediction=intervention.trigger_prediction,
                    scheduled_time=intervention.next_escalation,
                    personalization_data=intervention.personalization_data,
                )

                self._active_interventions[intervention.lead_id].append(escalation_intervention)
                self.logger.info(f"Scheduled escalation intervention for lead {intervention.lead_id}")

    async def _check_if_escalation_needed(self, intervention: InterventionExecution) -> bool:
        """Check if escalation is still needed based on lead engagement"""
        # Check recent engagement metrics
        # In production, this would check if the lead has engaged since the intervention
        # For now, return True (escalation needed) for demonstration
        return True

    def _get_execution_method(self, intervention_type: InterventionType) -> str:
        """Determine the execution method for intervention type"""
        execution_methods = {
            InterventionType.EMAIL_REENGAGEMENT: "reengagement_engine",
            InterventionType.SMS_URGENT: "ghl_workflow",
            InterventionType.PHONE_CALLBACK: "ghl_workflow",
            InterventionType.PROPERTY_ALERT: "reengagement_engine",
            InterventionType.MARKET_UPDATE: "reengagement_engine",
            InterventionType.PERSONAL_CONSULTATION: "ghl_workflow",
            InterventionType.INCENTIVE_OFFER: "direct_outreach",
            InterventionType.AGENT_ESCALATION: "ghl_workflow",
        }
        return execution_methods.get(intervention_type, "reengagement_engine")

    def _get_escalation_intervention(self, intervention_type: InterventionType) -> Optional[InterventionType]:
        """Get escalation intervention for given intervention type"""
        escalation_map = {
            InterventionType.EMAIL_REENGAGEMENT: InterventionType.SMS_URGENT,
            InterventionType.SMS_URGENT: InterventionType.PHONE_CALLBACK,
            InterventionType.PROPERTY_ALERT: InterventionType.PERSONAL_CONSULTATION,
            InterventionType.MARKET_UPDATE: InterventionType.PHONE_CALLBACK,
            InterventionType.PERSONAL_CONSULTATION: InterventionType.AGENT_ESCALATION,
            # No escalation for these types
            InterventionType.PHONE_CALLBACK: None,
            InterventionType.INCENTIVE_OFFER: None,
            InterventionType.AGENT_ESCALATION: None,
        }
        return escalation_map.get(intervention_type)

    async def _track_intervention_metrics(self, intervention: InterventionExecution, success: bool):
        """Track metrics for intervention effectiveness analysis"""
        metrics = {
            "execution_timestamp": datetime.now().isoformat(),
            "success": success,
            "lead_id": intervention.lead_id,
            "intervention_type": intervention.intervention_type.value,
            "trigger_risk_score": intervention.trigger_prediction.risk_score_14d,
            "trigger_risk_tier": intervention.trigger_prediction.risk_tier.value,
            "channel_used": intervention.channel,
            "template_used": intervention.template_used,
        }

        # Store metrics for later analysis
        # In production, this would go to analytics database
        intervention.engagement_metrics = metrics
        self.logger.info(f"Intervention metrics tracked: {json.dumps(metrics, default=str)}")

    async def _get_daily_intervention_count(self, lead_id: str) -> int:
        """Get number of interventions sent to lead today"""
        today = datetime.now().date()
        count = 0

        for intervention in self._active_interventions.get(lead_id, []):
            if intervention.executed_time and intervention.executed_time.date() == today:
                count += 1

        return count

    def _initialize_intervention_configs(self) -> Dict[InterventionType, InterventionConfig]:
        """Initialize intervention configurations"""
        configs = {
            InterventionType.EMAIL_REENGAGEMENT: InterventionConfig(
                intervention_type=InterventionType.EMAIL_REENGAGEMENT,
                trigger_risk_tier=ChurnRiskTier.LOW,
                delay_minutes=30,
                max_frequency=timedelta(hours=24),
                escalation_delay=timedelta(hours=6),
                success_metrics=["email_open", "email_click", "property_view"],
                priority_score=5,
            ),
            InterventionType.SMS_URGENT: InterventionConfig(
                intervention_type=InterventionType.SMS_URGENT,
                trigger_risk_tier=ChurnRiskTier.MEDIUM,
                delay_minutes=15,
                max_frequency=timedelta(hours=12),
                escalation_delay=timedelta(hours=3),
                success_metrics=["sms_response", "call_back"],
                priority_score=7,
            ),
            InterventionType.PHONE_CALLBACK: InterventionConfig(
                intervention_type=InterventionType.PHONE_CALLBACK,
                trigger_risk_tier=ChurnRiskTier.HIGH,
                delay_minutes=5,
                max_frequency=timedelta(hours=8),
                escalation_delay=timedelta(hours=2),
                success_metrics=["call_connected", "appointment_scheduled"],
                priority_score=9,
            ),
            InterventionType.PROPERTY_ALERT: InterventionConfig(
                intervention_type=InterventionType.PROPERTY_ALERT,
                trigger_risk_tier=ChurnRiskTier.MEDIUM,
                delay_minutes=45,
                max_frequency=timedelta(hours=48),
                escalation_delay=timedelta(hours=12),
                success_metrics=["property_view", "favorite_added"],
                priority_score=6,
            ),
            InterventionType.MARKET_UPDATE: InterventionConfig(
                intervention_type=InterventionType.MARKET_UPDATE,
                trigger_risk_tier=ChurnRiskTier.MEDIUM,
                delay_minutes=60,
                max_frequency=timedelta(days=3),
                escalation_delay=timedelta(days=1),
                success_metrics=["email_open", "article_read"],
                priority_score=4,
            ),
            InterventionType.PERSONAL_CONSULTATION: InterventionConfig(
                intervention_type=InterventionType.PERSONAL_CONSULTATION,
                trigger_risk_tier=ChurnRiskTier.HIGH,
                delay_minutes=10,
                max_frequency=timedelta(days=2),
                escalation_delay=timedelta(hours=4),
                success_metrics=["consultation_scheduled", "consultation_completed"],
                priority_score=8,
            ),
            InterventionType.INCENTIVE_OFFER: InterventionConfig(
                intervention_type=InterventionType.INCENTIVE_OFFER,
                trigger_risk_tier=ChurnRiskTier.CRITICAL,
                delay_minutes=0,  # Immediate
                max_frequency=timedelta(days=7),
                escalation_delay=None,  # No escalation
                success_metrics=["offer_viewed", "offer_accepted"],
                priority_score=10,
            ),
            InterventionType.AGENT_ESCALATION: InterventionConfig(
                intervention_type=InterventionType.AGENT_ESCALATION,
                trigger_risk_tier=ChurnRiskTier.CRITICAL,
                delay_minutes=0,  # Immediate
                max_frequency=timedelta(days=1),
                escalation_delay=None,  # No escalation
                success_metrics=["agent_assigned", "lead_contacted"],
                priority_score=10,
            ),
        }

        return configs

    async def get_intervention_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics on intervention effectiveness"""
        cutoff_date = datetime.now() - timedelta(days=days)

        # Filter recent interventions
        recent_interventions = [
            intervention
            for intervention in self._intervention_history
            if intervention.executed_time and intervention.executed_time >= cutoff_date
        ]

        # Calculate metrics
        total_interventions = len(recent_interventions)
        successful_interventions = len([i for i in recent_interventions if i.status == InterventionStatus.COMPLETED])

        # By intervention type
        type_metrics = defaultdict(lambda: {"total": 0, "successful": 0})
        for intervention in recent_interventions:
            intervention_type = intervention.intervention_type.value
            type_metrics[intervention_type]["total"] += 1
            if intervention.status == InterventionStatus.COMPLETED:
                type_metrics[intervention_type]["successful"] += 1

        # By risk tier
        tier_metrics = defaultdict(lambda: {"total": 0, "successful": 0})
        for intervention in recent_interventions:
            risk_tier = intervention.trigger_prediction.risk_tier.value
            tier_metrics[risk_tier]["total"] += 1
            if intervention.status == InterventionStatus.COMPLETED:
                tier_metrics[risk_tier]["successful"] += 1

        analytics = {
            "period_days": days,
            "total_interventions": total_interventions,
            "successful_interventions": successful_interventions,
            "success_rate": successful_interventions / total_interventions if total_interventions > 0 else 0,
            "by_intervention_type": dict(type_metrics),
            "by_risk_tier": dict(tier_metrics),
            "avg_interventions_per_lead": total_interventions / len(set(i.lead_id for i in recent_interventions))
            if recent_interventions
            else 0,
        }

        return analytics

    async def cancel_pending_interventions(self, lead_id: str, reason: str = "manual_cancellation"):
        """Cancel all pending interventions for a lead"""
        cancelled_count = 0

        for intervention in self._active_interventions.get(lead_id, []):
            if intervention.status == InterventionStatus.PENDING:
                intervention.status = InterventionStatus.CANCELLED
                intervention.delivery_status = f"cancelled: {reason}"
                cancelled_count += 1

        self.logger.info(f"Cancelled {cancelled_count} pending interventions for lead {lead_id}")


# Example usage and testing
if __name__ == "__main__":

    async def test_intervention_orchestrator():
        """Test the intervention orchestrator"""
        from unittest.mock import AsyncMock

        from .churn_prediction_engine import ChurnPrediction, ChurnRiskTier

        # Mock services
        reengagement_engine = AsyncMock()
        memory_service = AsyncMock()
        ghl_service = AsyncMock()

        # Initialize orchestrator
        orchestrator = InterventionOrchestrator(reengagement_engine, memory_service, ghl_service)

        # Create test prediction
        test_prediction = ChurnPrediction(
            lead_id="test-lead-123",
            prediction_timestamp=datetime.now(),
            risk_score_7d=85.0,
            risk_score_14d=78.0,
            risk_score_30d=70.0,
            risk_tier=ChurnRiskTier.CRITICAL,
            confidence=0.85,
            top_risk_factors=[
                ("days_since_last_interaction", 0.25),
                ("response_rate_7d", 0.20),
                ("engagement_trend", 0.18),
            ],
            recommended_actions=["Immediate phone call", "Escalate to senior agent"],
            intervention_urgency="immediate",
            feature_vector={},
            model_version="test-1.0.0",
        )

        # Test intervention processing
        predictions = {"test-lead-123": test_prediction}
        scheduled = await orchestrator.process_churn_predictions(predictions)

        print(f"Intervention Orchestration Results:")
        print(f"Scheduled interventions: {len(scheduled.get('test-lead-123', []))}")

        for intervention in scheduled.get("test-lead-123", []):
            print(f"- {intervention.intervention_type.value} at {intervention.scheduled_time}")

        # Test execution
        execution_results = await orchestrator.execute_pending_interventions()
        print(f"Execution results: {execution_results}")

    import asyncio

    asyncio.run(test_intervention_orchestrator())
