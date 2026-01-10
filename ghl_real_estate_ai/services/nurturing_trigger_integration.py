"""
Nurturing Trigger Integration Service

Connects the lead evaluation system with the nurturing agent to enable
automatic enrollment, intelligent triggering, and behavioral optimization
based on real-time lead scoring and interaction data.
"""

import asyncio
import json
import logging
import yaml
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Internal imports
from models.nurturing_models import (
    NurturingTrigger, TriggerType, LeadType, NurturingCampaign,
    EngagementType, CommunicationChannel, OptimizationRecommendation
)
from models.evaluation_models import LeadEvaluationResult, QualificationData
from services.lead_nurturing_agent import LeadNurturingAgent
from services.lead_evaluation_orchestrator import LeadEvaluationOrchestrator
from services.claude_semantic_analyzer import ClaudeSemanticAnalyzer

logger = logging.getLogger(__name__)


class NurturingTriggerIntegration:
    """
    Nurturing Trigger Integration Service

    Bridges the gap between lead evaluation and nurturing automation
    by implementing intelligent triggers, automatic enrollment, and
    behavioral optimization based on real-time lead data.
    """

    def __init__(
        self,
        nurturing_agent: Optional[LeadNurturingAgent] = None,
        evaluation_orchestrator: Optional[LeadEvaluationOrchestrator] = None,
        semantic_analyzer: Optional[ClaudeSemanticAnalyzer] = None
    ):
        """Initialize the trigger integration service."""
        self.nurturing_agent = nurturing_agent or LeadNurturingAgent()
        self.evaluation_orchestrator = evaluation_orchestrator or LeadEvaluationOrchestrator()
        self.semantic_analyzer = semantic_analyzer or ClaudeSemanticAnalyzer()

        # Load configuration
        self.config = self._load_trigger_config()
        self.triggers: List[NurturingTrigger] = []
        self._initialize_triggers()

        logger.info("Nurturing Trigger Integration Service initialized")

    def _load_trigger_config(self) -> Dict[str, Any]:
        """Load trigger configuration from YAML file."""
        try:
            config_path = Path(__file__).parent.parent / "config" / "nurturing_sequences.yaml"
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load trigger config: {str(e)}")
            return {}

    def _initialize_triggers(self):
        """Initialize trigger definitions from configuration."""
        try:
            trigger_config = self.config.get('nurturing_triggers', {})

            for trigger_id, trigger_data in trigger_config.items():
                trigger = NurturingTrigger(
                    trigger_id=trigger_id,
                    name=trigger_data['name'],
                    trigger_type=TriggerType(trigger_data['trigger_type']),
                    sequence_id="",  # Will be determined dynamically
                    conditions=trigger_data['conditions'],
                    priority=trigger_data['priority'],
                    cooldown_hours=trigger_data['cooldown_hours']
                )
                self.triggers.append(trigger)

            logger.info(f"Initialized {len(self.triggers)} triggers")

        except Exception as e:
            logger.error(f"Failed to initialize triggers: {str(e)}")

    # Core Integration Methods

    async def process_lead_evaluation(self, evaluation_result: LeadEvaluationResult) -> None:
        """
        Process a lead evaluation result and trigger appropriate nurturing actions.

        Args:
            evaluation_result: Fresh lead evaluation data
        """
        try:
            lead_id = evaluation_result.lead_id

            # Check for automatic enrollment eligibility
            await self._check_automatic_enrollment(evaluation_result)

            # Evaluate existing campaign adjustments
            await self._evaluate_campaign_adjustments(evaluation_result)

            # Check behavioral triggers
            await self._check_behavioral_triggers(evaluation_result)

            # Update lead behavior profile
            await self._update_behavioral_learning(evaluation_result)

            logger.info(f"Processed evaluation for lead {lead_id}")

        except Exception as e:
            logger.error(f"Failed to process evaluation for lead {evaluation_result.lead_id}: {str(e)}")

    async def _check_automatic_enrollment(self, evaluation_result: LeadEvaluationResult) -> None:
        """Check if lead should be automatically enrolled in nurturing."""
        try:
            lead_id = evaluation_result.lead_id

            # Check if lead already has active campaign
            existing_campaign = await self.nurturing_agent.get_active_campaign(lead_id)
            if existing_campaign:
                return

            # Determine if lead meets enrollment criteria
            if await self._meets_enrollment_criteria(evaluation_result):
                # Determine lead type and sequence
                lead_type = await self._determine_lead_type(evaluation_result)

                if lead_type:
                    # Enroll in nurturing
                    campaign = await self.nurturing_agent.enroll_lead(
                        lead_id=lead_id,
                        lead_type=lead_type,
                        evaluation_result=evaluation_result
                    )

                    logger.info(f"Auto-enrolled lead {lead_id} in {lead_type.value} sequence")

        except Exception as e:
            logger.error(f"Auto-enrollment check failed for lead {evaluation_result.lead_id}: {str(e)}")

    async def _meets_enrollment_criteria(self, evaluation_result: LeadEvaluationResult) -> bool:
        """Check if lead meets criteria for automatic enrollment."""
        # Minimum qualification score
        if evaluation_result.overall_score < 0.6:
            return False

        # Must have basic contact information
        qual_data = evaluation_result.qualification_data
        if not qual_data or not qual_data.contact_information:
            return False

        # Must have expressed some level of interest
        if evaluation_result.urgency_level in ["low", "very_low"]:
            return False

        # Check for explicit opt-in preferences
        # (This would integrate with actual consent management)

        return True

    async def _determine_lead_type(self, evaluation_result: LeadEvaluationResult) -> Optional[LeadType]:
        """Determine the appropriate lead type based on evaluation data."""
        try:
            qual_data = evaluation_result.qualification_data

            if not qual_data:
                return LeadType.BUYER_FIRST_TIME  # Default fallback

            # Analyze qualification data to determine type
            intent = qual_data.property_search_intent.lower() if qual_data.property_search_intent else ""

            # Seller indicators
            if "sell" in intent or "selling" in intent:
                if "downsize" in intent or qual_data.bedrooms and int(qual_data.bedrooms) < 3:
                    return LeadType.SELLER_DOWNSIZING
                elif "upsize" in intent or "larger" in intent:
                    return LeadType.SELLER_UPSIZING
                elif "investment" in intent:
                    return LeadType.SELLER_INVESTMENT
                else:
                    return LeadType.SELLER_UPSIZING  # Default seller type

            # Buyer indicators
            else:
                # Check budget range for luxury classification
                if qual_data.budget_range:
                    budget_str = qual_data.budget_range.lower()
                    if any(luxury_indicator in budget_str for luxury_indicator in ["1m+", "million", "luxury", "premium"]):
                        return LeadType.BUYER_LUXURY

                # Check for investment intent
                if "investment" in intent or "rental" in intent or "portfolio" in intent:
                    return LeadType.BUYER_INVESTMENT

                # Check for relocation indicators
                if "relocat" in intent or "moving" in intent or "transfer" in intent:
                    return LeadType.BUYER_RELOCATION

                # Check for first-time buyer indicators
                if "first" in intent or qual_data.bedrooms == "1" or not qual_data.previous_home_owner:
                    return LeadType.BUYER_FIRST_TIME

                # Default to first-time buyer
                return LeadType.BUYER_FIRST_TIME

        except Exception as e:
            logger.error(f"Failed to determine lead type: {str(e)}")
            return LeadType.BUYER_FIRST_TIME

    async def _evaluate_campaign_adjustments(self, evaluation_result: LeadEvaluationResult) -> None:
        """Evaluate if existing campaigns need adjustments based on new data."""
        try:
            lead_id = evaluation_result.lead_id
            campaign = await self.nurturing_agent.get_active_campaign(lead_id)

            if not campaign:
                return

            # Check for significant score changes
            previous_score = campaign.enrollment_data.overall_score
            current_score = evaluation_result.overall_score
            score_delta = current_score - previous_score

            # Significant improvement - accelerate sequence
            if score_delta > 0.15:
                await self._accelerate_campaign(campaign, "score_improvement")

            # Significant decline - adjust approach
            elif score_delta < -0.15:
                await self._adjust_campaign_approach(campaign, "score_decline")

            # Check urgency level changes
            if evaluation_result.urgency_level != campaign.enrollment_data.urgency_level:
                await self._adjust_campaign_urgency(campaign, evaluation_result.urgency_level)

        except Exception as e:
            logger.error(f"Campaign adjustment evaluation failed: {str(e)}")

    async def _check_behavioral_triggers(self, evaluation_result: LeadEvaluationResult) -> None:
        """Check for behavioral triggers and execute appropriate actions."""
        try:
            for trigger in self.triggers:
                if await self._evaluate_trigger_conditions(trigger, evaluation_result):
                    await self._execute_trigger(trigger, evaluation_result)

        except Exception as e:
            logger.error(f"Behavioral trigger check failed: {str(e)}")

    async def _evaluate_trigger_conditions(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> bool:
        """Evaluate if trigger conditions are met."""
        try:
            lead_id = evaluation_result.lead_id

            # Check cooldown period
            if trigger.last_triggered:
                cooldown_end = trigger.last_triggered + timedelta(hours=trigger.cooldown_hours)
                if datetime.now() < cooldown_end:
                    return False

            # Evaluate specific conditions based on trigger type
            if trigger.trigger_type == TriggerType.SCORE_BASED:
                return await self._evaluate_score_conditions(trigger, evaluation_result)

            elif trigger.trigger_type == TriggerType.BEHAVIOR_BASED:
                return await self._evaluate_behavior_conditions(trigger, evaluation_result)

            elif trigger.trigger_type == TriggerType.ENGAGEMENT_BASED:
                return await self._evaluate_engagement_conditions(trigger, evaluation_result)

            elif trigger.trigger_type == TriggerType.OBJECTION_BASED:
                return await self._evaluate_objection_conditions(trigger, evaluation_result)

            return False

        except Exception as e:
            logger.error(f"Trigger condition evaluation failed: {str(e)}")
            return False

    async def _evaluate_score_conditions(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> bool:
        """Evaluate score-based trigger conditions."""
        # Example: qualification_score_delta > 0.15
        for condition in trigger.conditions:
            if "qualification_score_delta" in condition:
                # Get previous score (mock for demo)
                previous_score = 0.65  # This would come from historical data
                current_score = evaluation_result.overall_score
                delta = current_score - previous_score

                if ">" in condition:
                    threshold = float(condition.split(">")[1].strip())
                    if delta > threshold:
                        return True

        return False

    async def _evaluate_behavior_conditions(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> bool:
        """Evaluate behavior-based trigger conditions."""
        # Mock behavior evaluation for demo
        # In production, this would check actual engagement data
        return False

    async def _evaluate_engagement_conditions(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> bool:
        """Evaluate engagement-based trigger conditions."""
        # Mock engagement evaluation for demo
        return False

    async def _evaluate_objection_conditions(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> bool:
        """Evaluate objection-based trigger conditions."""
        # Use semantic analyzer to detect objections in recent conversations
        try:
            lead_id = evaluation_result.lead_id
            conversation_history = await self.semantic_analyzer.get_conversation_history(lead_id)

            if conversation_history:
                analysis = await self.semantic_analyzer.analyze_conversation(conversation_history)

                # Check for objections in analysis
                if analysis.objections_detected:
                    for objection in analysis.objections_detected:
                        if objection.confidence_score > 0.7:
                            return True

        except Exception as e:
            logger.error(f"Objection condition evaluation failed: {str(e)}")

        return False

    async def _execute_trigger(
        self,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> None:
        """Execute trigger actions."""
        try:
            lead_id = evaluation_result.lead_id

            # Update trigger last fired time
            trigger.last_triggered = datetime.now()

            # Get trigger action configuration
            trigger_config = self.config.get('nurturing_triggers', {}).get(trigger.trigger_id, {})
            actions = trigger_config.get('actions', [])

            for action in actions:
                await self._execute_trigger_action(action, trigger, evaluation_result)

            logger.info(f"Executed trigger {trigger.name} for lead {lead_id}")

        except Exception as e:
            logger.error(f"Trigger execution failed: {str(e)}")

    async def _execute_trigger_action(
        self,
        action: str,
        trigger: NurturingTrigger,
        evaluation_result: LeadEvaluationResult
    ) -> None:
        """Execute specific trigger action."""
        try:
            lead_id = evaluation_result.lead_id

            if action == "send_congratulations_message":
                await self._send_congratulations_message(lead_id)

            elif action == "escalate_to_premium_sequence":
                await self._escalate_to_premium_sequence(lead_id, evaluation_result)

            elif action == "schedule_consultation_call":
                await self._schedule_consultation_call(lead_id)

            elif action == "send_hot_lead_alert_to_agent":
                await self._send_agent_alert(lead_id, "hot_lead", evaluation_result)

            elif action == "accelerate_sequence_timing":
                await self._accelerate_sequence_timing(lead_id)

            elif action == "offer_immediate_showing":
                await self._offer_immediate_showing(lead_id)

            elif action == "send_objection_handling_sequence":
                await self._send_objection_handling_sequence(lead_id)

            elif action == "send_re_engagement_sequence":
                await self._send_re_engagement_sequence(lead_id)

        except Exception as e:
            logger.error(f"Failed to execute action {action}: {str(e)}")

    # Campaign Adjustment Methods

    async def _accelerate_campaign(self, campaign: NurturingCampaign, reason: str) -> None:
        """Accelerate campaign progression due to positive indicators."""
        try:
            # Reduce delay for next touchpoint
            for touchpoint in campaign.touchpoints:
                if touchpoint.status == "scheduled" and not touchpoint.executed_at:
                    # Move up by 50% of remaining time
                    current_delay = touchpoint.scheduled_at - datetime.now()
                    new_delay = current_delay * 0.5
                    touchpoint.scheduled_at = datetime.now() + new_delay
                    break

            logger.info(f"Accelerated campaign {campaign.campaign_id} due to {reason}")

        except Exception as e:
            logger.error(f"Failed to accelerate campaign: {str(e)}")

    async def _adjust_campaign_approach(self, campaign: NurturingCampaign, reason: str) -> None:
        """Adjust campaign approach due to negative indicators."""
        try:
            # Switch to more supportive messaging tone
            # Add pause before next touchpoint
            for touchpoint in campaign.touchpoints:
                if touchpoint.status == "scheduled" and not touchpoint.executed_at:
                    # Add 24-hour pause
                    touchpoint.scheduled_at += timedelta(hours=24)
                    break

            logger.info(f"Adjusted campaign {campaign.campaign_id} approach due to {reason}")

        except Exception as e:
            logger.error(f"Failed to adjust campaign approach: {str(e)}")

    async def _adjust_campaign_urgency(self, campaign: NurturingCampaign, new_urgency: str) -> None:
        """Adjust campaign based on urgency level changes."""
        try:
            if new_urgency in ["high", "very_high"]:
                # Increase touchpoint frequency
                await self._accelerate_campaign(campaign, "urgency_increase")
            elif new_urgency in ["low", "very_low"]:
                # Decrease touchpoint frequency
                await self._adjust_campaign_approach(campaign, "urgency_decrease")

            logger.info(f"Adjusted campaign urgency to {new_urgency}")

        except Exception as e:
            logger.error(f"Failed to adjust campaign urgency: {str(e)}")

    # Action Implementation Methods (Mock implementations for demo)

    async def _send_congratulations_message(self, lead_id: str) -> None:
        """Send congratulatory message for improved engagement."""
        logger.info(f"Sent congratulations message to lead {lead_id}")

    async def _escalate_to_premium_sequence(self, lead_id: str, evaluation_result: LeadEvaluationResult) -> None:
        """Escalate lead to premium nurturing sequence."""
        # Determine premium sequence based on lead type
        premium_sequence = "luxury_buyer_experience" if evaluation_result.overall_score > 0.8 else "high_value_sequence"
        logger.info(f"Escalated lead {lead_id} to premium sequence: {premium_sequence}")

    async def _schedule_consultation_call(self, lead_id: str) -> None:
        """Schedule consultation call for high-value lead."""
        logger.info(f"Scheduled consultation call for lead {lead_id}")

    async def _send_agent_alert(self, lead_id: str, alert_type: str, evaluation_result: LeadEvaluationResult) -> None:
        """Send alert to agent about important lead activity."""
        logger.info(f"Sent {alert_type} alert to agent for lead {lead_id}")

    async def _accelerate_sequence_timing(self, lead_id: str) -> None:
        """Accelerate sequence timing for engaged lead."""
        campaign = await self.nurturing_agent.get_active_campaign(lead_id)
        if campaign:
            await self._accelerate_campaign(campaign, "high_engagement")

    async def _offer_immediate_showing(self, lead_id: str) -> None:
        """Offer immediate property showing to hot lead."""
        logger.info(f"Offered immediate showing to lead {lead_id}")

    async def _send_objection_handling_sequence(self, lead_id: str) -> None:
        """Send objection handling sequence."""
        logger.info(f"Sent objection handling sequence to lead {lead_id}")

    async def _send_re_engagement_sequence(self, lead_id: str) -> None:
        """Send re-engagement sequence for inactive lead."""
        logger.info(f"Sent re-engagement sequence to lead {lead_id}")

    # Behavioral Learning and Optimization

    async def _update_behavioral_learning(self, evaluation_result: LeadEvaluationResult) -> None:
        """Update behavioral learning based on evaluation data."""
        try:
            lead_id = evaluation_result.lead_id

            # Analyze patterns in evaluation data
            behavioral_insights = await self._extract_behavioral_insights(evaluation_result)

            # Update lead behavior profile
            await self._store_behavioral_insights(lead_id, behavioral_insights)

            # Generate optimization recommendations
            recommendations = await self._generate_optimization_recommendations(
                lead_id, behavioral_insights
            )

            for recommendation in recommendations:
                await self._store_recommendation(recommendation)

        except Exception as e:
            logger.error(f"Behavioral learning update failed: {str(e)}")

    async def _extract_behavioral_insights(self, evaluation_result: LeadEvaluationResult) -> Dict[str, Any]:
        """Extract behavioral insights from evaluation data."""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "overall_score": evaluation_result.overall_score,
            "urgency_level": evaluation_result.urgency_level,
            "qualification_completeness": len([
                field for field in [
                    evaluation_result.qualification_data.budget_range,
                    evaluation_result.qualification_data.location_preference,
                    evaluation_result.qualification_data.property_type,
                    evaluation_result.qualification_data.timeline
                ] if field
            ]) / 4 if evaluation_result.qualification_data else 0,
            "engagement_indicators": evaluation_result.next_actions[:3]  # Top 3 recommended actions
        }

        return insights

    async def _store_behavioral_insights(self, lead_id: str, insights: Dict[str, Any]) -> None:
        """Store behavioral insights for future optimization."""
        # In production, this would store in a time-series database
        logger.info(f"Stored behavioral insights for lead {lead_id}")

    async def _generate_optimization_recommendations(
        self,
        lead_id: str,
        behavioral_insights: Dict[str, Any]
    ) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on behavioral data."""
        recommendations = []

        # Example recommendation logic
        if behavioral_insights["qualification_completeness"] < 0.5:
            recommendations.append(OptimizationRecommendation(
                target_type="sequence_timing",
                target_id=lead_id,
                recommendation="Increase qualification-focused touchpoints before property matching",
                confidence_score=0.8,
                expected_impact="15-20% improvement in conversion rate",
                implementation_effort="Low - adjust sequence step priorities"
            ))

        return recommendations

    async def _store_recommendation(self, recommendation: OptimizationRecommendation) -> None:
        """Store optimization recommendation."""
        logger.info(f"Stored optimization recommendation: {recommendation.recommendation}")

    # Integration Event Handlers

    async def handle_conversation_update(self, lead_id: str, conversation_data: Dict[str, Any]) -> None:
        """Handle conversation updates from chat interface."""
        try:
            # Trigger re-evaluation if significant conversation activity
            if conversation_data.get("message_count", 0) > 5:
                evaluation_result = await self.evaluation_orchestrator.evaluate_lead(lead_id)
                if evaluation_result:
                    await self.process_lead_evaluation(evaluation_result)

        except Exception as e:
            logger.error(f"Conversation update handling failed: {str(e)}")

    async def handle_property_interaction(self, lead_id: str, interaction_data: Dict[str, Any]) -> None:
        """Handle property interaction events."""
        try:
            # Record engagement
            await self.nurturing_agent.record_engagement(
                lead_id=lead_id,
                engagement_type=EngagementType.PROPERTY_VIEWED,
                channel=CommunicationChannel.EMAIL,
                interaction_data=interaction_data
            )

            # Check for high engagement triggers
            if interaction_data.get("properties_viewed_today", 0) > 3:
                # Trigger immediate follow-up
                await self._send_agent_alert(lead_id, "high_property_engagement", None)

        except Exception as e:
            logger.error(f"Property interaction handling failed: {str(e)}")

    async def handle_form_submission(self, lead_id: str, form_data: Dict[str, Any]) -> None:
        """Handle form submission events."""
        try:
            # Record engagement
            await self.nurturing_agent.record_engagement(
                lead_id=lead_id,
                engagement_type=EngagementType.FORM_SUBMITTED,
                channel=CommunicationChannel.EMAIL,
                interaction_data=form_data
            )

            # Trigger immediate re-evaluation
            evaluation_result = await self.evaluation_orchestrator.evaluate_lead(lead_id)
            if evaluation_result:
                await self.process_lead_evaluation(evaluation_result)

        except Exception as e:
            logger.error(f"Form submission handling failed: {str(e)}")

    # Monitoring and Health Checks

    async def get_trigger_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for trigger system."""
        return {
            "total_triggers": len(self.triggers),
            "active_triggers": len([t for t in self.triggers if t.is_active]),
            "trigger_success_rate": 0.847,  # Mock metric
            "average_response_time": "0.3 seconds",
            "last_optimization": datetime.now() - timedelta(hours=6)
        }

    async def health_check(self) -> bool:
        """Perform health check on integration service."""
        try:
            # Check component health
            agent_healthy = self.nurturing_agent is not None
            orchestrator_healthy = self.evaluation_orchestrator is not None
            analyzer_healthy = self.semantic_analyzer is not None

            return all([agent_healthy, orchestrator_healthy, analyzer_healthy])

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False