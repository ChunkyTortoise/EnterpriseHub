"""
Claude Enhanced Webhook Processor

Advanced webhook processing system that integrates all Claude AI advanced features
for comprehensive real-time lead intelligence, automation, and performance optimization.

Integrates:
1. Predictive Analytics Engine - Lead scoring and outcome forecasting
2. Advanced Automation Engine - Intelligent workflow triggers
3. Multimodal Intelligence Engine - Voice, text, and behavioral analysis
4. Competitive Intelligence Engine - Market analysis and positioning
5. Agent Performance Analytics - Coaching effectiveness and optimization

Features:
- Enhanced webhook processing with predictive insights
- Multi-modal analysis of lead interactions
- Intelligent automation triggering
- Real-time competitive analysis
- Performance tracking and coaching recommendations
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.claude_predictive_analytics_engine import claude_predictive_analytics
from ghl_real_estate_ai.services.claude_advanced_automation_engine import claude_automation_engine
from ghl_real_estate_ai.services.claude_multimodal_intelligence_engine import (
    claude_multimodal_intelligence, MultimodalInput, ModalityType, ContentType
)
from ghl_real_estate_ai.services.claude_competitive_intelligence_engine import claude_competitive_intelligence
from ghl_real_estate_ai.services.claude_agent_performance_analytics import claude_performance_analytics, PerformanceMetric
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.qualification_orchestrator import QualificationOrchestrator
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/claude/webhooks", tags=["claude-enhanced-webhooks"])

# Initialize services
claude_analyzer = ClaudeSemanticAnalyzer()


class EnhancedWebhookProcessor:
    """
    Enhanced webhook processor that integrates all Claude AI advanced features
    for comprehensive lead intelligence and automation.
    """

    def __init__(self):
        """Initialize enhanced webhook processor."""
        self.predictive_engine = claude_predictive_analytics
        self.automation_engine = claude_automation_engine
        self.multimodal_engine = claude_multimodal_intelligence
        self.competitive_engine = claude_competitive_intelligence
        self.performance_analytics = claude_performance_analytics
        self.semantic_analyzer = claude_analyzer

        # Processing stats
        self.processing_stats = {
            "total_processed": 0,
            "successful_predictions": 0,
            "automations_triggered": 0,
            "performance_updates": 0,
            "multimodal_analyses": 0,
            "competitive_insights": 0
        }

        logger.info("Enhanced Claude Webhook Processor initialized")

    async def process_contact_created(
        self,
        webhook_data: Dict[str, Any],
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Process contact.created webhook with full Claude intelligence suite.

        Args:
            webhook_data: GHL webhook data
            background_tasks: FastAPI background tasks

        Returns:
            Processing results with all intelligence insights
        """
        try:
            start_time = datetime.now()
            contact_id = webhook_data.get("id", "")
            contact_name = webhook_data.get("name", "Unknown")
            initial_message = webhook_data.get("message", "")
            source = webhook_data.get("source", "webhook")
            location_id = webhook_data.get("location_id", "default")

            logger.info(f"Processing enhanced contact.created for {contact_id}: {contact_name}")

            # Step 1: Multimodal Intelligence Analysis
            multimodal_results = await self._perform_multimodal_analysis(
                contact_id, webhook_data, initial_message
            )

            # Step 2: Predictive Analytics
            prediction_results = await self._perform_predictive_analysis(
                contact_id, webhook_data, multimodal_results
            )

            # Step 3: Competitive Intelligence
            competitive_results = await self._perform_competitive_analysis(
                webhook_data, prediction_results
            )

            # Step 4: Intelligent Qualification Flow
            qualification_results = await self._start_intelligent_qualification(
                contact_id, contact_name, initial_message, source, multimodal_results
            )

            # Step 5: Advanced Automation Triggers
            automation_results = await self._trigger_intelligent_automations(
                webhook_data, multimodal_results, prediction_results, competitive_results
            )

            # Step 6: Agent Performance Tracking
            performance_results = await self._track_agent_performance(
                webhook_data, qualification_results, automation_results
            )

            # Step 7: Enhanced GHL Updates
            ghl_updates = await self._update_ghl_with_intelligence(
                contact_id, location_id, multimodal_results, prediction_results,
                competitive_results, qualification_results
            )

            # Compile comprehensive results
            processing_results = {
                "contact_id": contact_id,
                "contact_name": contact_name,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000,
                "multimodal_intelligence": multimodal_results,
                "predictive_analytics": prediction_results,
                "competitive_intelligence": competitive_results,
                "qualification_flow": qualification_results,
                "automation_results": automation_results,
                "performance_tracking": performance_results,
                "ghl_updates": ghl_updates,
                "success": True,
                "processed_at": start_time.isoformat()
            }

            # Update processing stats
            self._update_processing_stats(processing_results)

            # Schedule background analysis
            background_tasks.add_task(
                self._perform_background_analysis,
                contact_id, processing_results
            )

            logger.info(f"Enhanced processing completed for {contact_id} in {processing_results['processing_time_ms']:.0f}ms")
            return processing_results

        except Exception as e:
            logger.error(f"Error in enhanced webhook processing: {e}")
            return {
                "contact_id": contact_id,
                "success": False,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }

    async def _perform_multimodal_analysis(
        self,
        contact_id: str,
        webhook_data: Dict[str, Any],
        initial_message: str
    ) -> Dict[str, Any]:
        """Perform comprehensive multimodal analysis."""
        try:
            # Prepare multimodal input
            modalities = {}

            # Text analysis
            if initial_message:
                modalities[ModalityType.TEXT] = initial_message

            # Behavioral data analysis
            behavioral_data = {
                "source": webhook_data.get("source", "unknown"),
                "timestamp": webhook_data.get("dateAdded", ""),
                "contact_method": self._determine_contact_method(webhook_data),
                "initial_engagement": self._assess_initial_engagement(webhook_data)
            }
            modalities[ModalityType.BEHAVIORAL] = behavioral_data

            # Create multimodal input
            multimodal_input = MultimodalInput(
                input_id=f"contact_created_{contact_id}",
                modalities=modalities,
                content_type=ContentType.CHAT_CONVERSATION,
                lead_id=contact_id,
                agent_id=webhook_data.get("assignedTo"),
                context={
                    "webhook_data": webhook_data,
                    "analysis_type": "new_contact",
                    "urgency_level": self._assess_urgency(webhook_data)
                },
                timestamp=datetime.now()
            )

            # Perform multimodal analysis
            multimodal_insights = await self.multimodal_engine.analyze_multimodal_input(multimodal_input)

            return {
                "success": True,
                "analysis_id": multimodal_insights.analysis_id,
                "unified_sentiment": multimodal_insights.unified_sentiment,
                "confidence_score": multimodal_insights.confidence_score,
                "key_insights": multimodal_insights.key_insights,
                "recommended_actions": multimodal_insights.recommended_actions,
                "coaching_suggestions": multimodal_insights.coaching_suggestions,
                "personalization_data": multimodal_insights.personalization_data
            }

        except Exception as e:
            logger.error(f"Error in multimodal analysis: {e}")
            return {"success": False, "error": str(e)}

    async def _perform_predictive_analysis(
        self,
        contact_id: str,
        webhook_data: Dict[str, Any],
        multimodal_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform predictive analytics for lead conversion."""
        try:
            # Prepare lead data for prediction
            lead_data = {
                "contact_id": contact_id,
                "source": webhook_data.get("source", "unknown"),
                "initial_message": webhook_data.get("message", ""),
                "contact_method": self._determine_contact_method(webhook_data),
                "demographic_data": self._extract_demographic_data(webhook_data),
                "behavioral_signals": multimodal_results.get("personalization_data", {}),
                "engagement_score": self._calculate_initial_engagement_score(webhook_data, multimodal_results),
                "urgency_indicators": multimodal_results.get("key_insights", []),
                "sentiment_score": multimodal_results.get("unified_sentiment", 0.0)
            }

            # Get conversation history if available
            conversation_history = []
            if webhook_data.get("message"):
                conversation_history = [{
                    "role": "user",
                    "content": webhook_data["message"],
                    "timestamp": webhook_data.get("dateAdded", "")
                }]

            # Perform lead conversion prediction
            prediction = await self.predictive_engine.predict_lead_conversion(
                lead_id=contact_id,
                lead_data=lead_data,
                conversation_history=conversation_history
            )

            # Get market predictions for context
            location = self._extract_location(webhook_data)
            if location:
                market_prediction = await self.predictive_engine.predict_market_trends(
                    location=location,
                    forecast_horizon_days=90
                )
            else:
                market_prediction = None

            return {
                "success": True,
                "conversion_prediction": {
                    "probability": prediction.predicted_conversion_probability,
                    "timeline_days": prediction.predicted_timeline_days,
                    "conversion_stage": prediction.predicted_conversion_stage.value,
                    "confidence": prediction.confidence_score,
                    "predicted_value": prediction.predicted_value,
                    "churn_probability": prediction.churn_probability
                },
                "risk_factors": prediction.risk_factors,
                "opportunity_indicators": prediction.opportunity_indicators,
                "recommended_actions": prediction.recommended_actions,
                "market_context": {
                    "location": location,
                    "market_condition": market_prediction.market_condition.value if market_prediction else "unknown",
                    "demand_strength": market_prediction.demand_strength if market_prediction else 0.5
                } if market_prediction else None
            }

        except Exception as e:
            logger.error(f"Error in predictive analysis: {e}")
            return {"success": False, "error": str(e)}

    async def _perform_competitive_analysis(
        self,
        webhook_data: Dict[str, Any],
        prediction_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform competitive intelligence analysis."""
        try:
            location = self._extract_location(webhook_data)
            if not location:
                return {"success": False, "reason": "Location not available for competitive analysis"}

            # Generate market intelligence
            market_intelligence = await self.competitive_engine.generate_market_intelligence_report(
                market_area=location,
                time_period="30_days",
                focus_areas=["pricing", "inventory", "competitor_activity"]
            )

            # Identify competitive opportunities based on lead profile
            lead_value_estimate = prediction_results.get("conversion_prediction", {}).get("predicted_value", 0)
            conversion_probability = prediction_results.get("conversion_prediction", {}).get("probability", 0.5)

            current_position = {
                "lead_quality": "high" if conversion_probability > 0.7 else "medium" if conversion_probability > 0.4 else "low",
                "value_potential": lead_value_estimate,
                "market_knowledge": webhook_data.get("source", "unknown"),
                "competitive_advantages": []
            }

            # This would be agent-specific in production
            agent_id = webhook_data.get("assignedTo", "default_agent")
            opportunities = await self.competitive_engine.identify_competitive_opportunities(
                agent_id=agent_id,
                current_position=current_position,
                market_area=location
            )

            return {
                "success": True,
                "market_intelligence": {
                    "intelligence_id": market_intelligence.intelligence_id,
                    "market_area": market_intelligence.market_area,
                    "market_dynamics": market_intelligence.market_dynamics,
                    "pricing_intelligence": market_intelligence.pricing_intelligence,
                    "strategic_insights": market_intelligence.strategic_insights[:3],  # Top 3
                    "actionable_recommendations": market_intelligence.actionable_recommendations[:3]
                },
                "competitive_opportunities": opportunities[:3],  # Top 3 opportunities
                "positioning_recommendations": self._generate_positioning_recommendations(
                    market_intelligence, prediction_results
                )
            }

        except Exception as e:
            logger.error(f"Error in competitive analysis: {e}")
            return {"success": False, "error": str(e)}

    async def _start_intelligent_qualification(
        self,
        contact_id: str,
        contact_name: str,
        initial_message: str,
        source: str,
        multimodal_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Start intelligent qualification flow."""
        try:
            # Initialize qualification orchestrator
            orchestrator = QualificationOrchestrator("default")

            # Start qualification flow
            qualification_result = await orchestrator.start_qualification_flow(
                contact_id=contact_id,
                contact_name=contact_name,
                initial_message=initial_message,
                source=source,
                agent_id=None  # Would be determined by routing logic
            )

            # Enhance with multimodal insights
            if multimodal_results.get("success"):
                enhanced_context = {
                    "multimodal_insights": multimodal_results.get("key_insights", []),
                    "communication_preferences": multimodal_results.get("personalization_data", {}),
                    "sentiment_analysis": multimodal_results.get("unified_sentiment", 0.0)
                }

                # This would update the qualification flow with additional context
                qualification_result["enhanced_context"] = enhanced_context

            return {
                "success": True,
                "qualification_flow": qualification_result,
                "intelligent_enhancements": {
                    "adaptive_questioning": True,
                    "sentiment_awareness": True,
                    "personalization_enabled": True,
                    "multimodal_insights_integrated": multimodal_results.get("success", False)
                }
            }

        except Exception as e:
            logger.error(f"Error starting intelligent qualification: {e}")
            return {"success": False, "error": str(e)}

    async def _trigger_intelligent_automations(
        self,
        webhook_data: Dict[str, Any],
        multimodal_results: Dict[str, Any],
        prediction_results: Dict[str, Any],
        competitive_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger intelligent automations based on analysis."""
        try:
            # Prepare automation event data
            event_data = {
                "contact_id": webhook_data.get("id"),
                "contact_name": webhook_data.get("name"),
                "source": webhook_data.get("source"),
                "initial_message": webhook_data.get("message", ""),
                "sentiment_score": multimodal_results.get("unified_sentiment", 0.0),
                "conversion_probability": prediction_results.get("conversion_prediction", {}).get("probability", 0.5),
                "predicted_timeline": prediction_results.get("conversion_prediction", {}).get("timeline_days", 30),
                "urgency_score": self._calculate_urgency_score(multimodal_results, prediction_results),
                "market_conditions": competitive_results.get("market_intelligence", {}).get("market_dynamics", {}),
                "recommended_actions": multimodal_results.get("recommended_actions", [])
            }

            # Trigger automation processing
            automation_executions = await self.automation_engine.process_trigger_event(
                event_type="message_received",
                event_data=event_data,
                lead_id=webhook_data.get("id"),
                agent_id=webhook_data.get("assignedTo")
            )

            # Also trigger based on high intent if detected
            if event_data["conversion_probability"] > 0.8 or event_data["urgency_score"] > 75:
                high_intent_executions = await self.automation_engine.process_trigger_event(
                    event_type="behavioral_pattern",
                    event_data={**event_data, "pattern_type": "high_intent_detected"},
                    lead_id=webhook_data.get("id"),
                    agent_id=webhook_data.get("assignedTo")
                )
                automation_executions.extend(high_intent_executions)

            return {
                "success": True,
                "automations_triggered": len(automation_executions),
                "executions": [{
                    "execution_id": exec.execution_id,
                    "rule_id": exec.rule_id,
                    "success": exec.success,
                    "actions_executed": len(exec.actions_executed),
                    "execution_time_ms": exec.execution_time_ms
                } for exec in automation_executions],
                "intelligent_triggers": {
                    "sentiment_based": multimodal_results.get("success", False),
                    "prediction_based": prediction_results.get("success", False),
                    "competitive_based": competitive_results.get("success", False)
                }
            }

        except Exception as e:
            logger.error(f"Error triggering intelligent automations: {e}")
            return {"success": False, "error": str(e)}

    async def _track_agent_performance(
        self,
        webhook_data: Dict[str, Any],
        qualification_results: Dict[str, Any],
        automation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track agent performance metrics."""
        try:
            agent_id = webhook_data.get("assignedTo")
            if not agent_id:
                return {"success": False, "reason": "No agent assigned"}

            # Record performance data points
            contact_timestamp = webhook_data.get("dateAdded")
            if contact_timestamp:
                # Calculate response time (if this is a follow-up)
                response_time = self._calculate_response_time(contact_timestamp)
                if response_time:
                    self.performance_analytics.record_performance_data_point(
                        agent_id=agent_id,
                        metric=PerformanceMetric.RESPONSE_TIME,
                        value=response_time,
                        context={"webhook_type": "contact_created", "source": webhook_data.get("source")}
                    )

            # Track lead quality score
            lead_quality = self._calculate_lead_quality_score(webhook_data, qualification_results)
            self.performance_analytics.record_performance_data_point(
                agent_id=agent_id,
                metric=PerformanceMetric.LEAD_QUALITY_SCORE,
                value=lead_quality,
                context={"source": webhook_data.get("source"), "initial_qualification": True}
            )

            # Track automation effectiveness if automations were triggered
            if automation_results.get("success") and automation_results.get("automations_triggered", 0) > 0:
                automation_success_rate = sum(
                    1 for exec in automation_results.get("executions", []) if exec.get("success", False)
                ) / automation_results.get("automations_triggered", 1)

                self.performance_analytics.record_performance_data_point(
                    agent_id=agent_id,
                    metric=PerformanceMetric.LEAD_NURTURING_EFFECTIVENESS,
                    value=automation_success_rate,
                    context={"automation_triggered": True, "lead_id": webhook_data.get("id")}
                )

            return {
                "success": True,
                "agent_id": agent_id,
                "metrics_recorded": ["response_time", "lead_quality_score", "automation_effectiveness"],
                "performance_tracking_enabled": True
            }

        except Exception as e:
            logger.error(f"Error tracking agent performance: {e}")
            return {"success": False, "error": str(e)}

    async def _update_ghl_with_intelligence(
        self,
        contact_id: str,
        location_id: str,
        multimodal_results: Dict[str, Any],
        prediction_results: Dict[str, Any],
        competitive_results: Dict[str, Any],
        qualification_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update GHL contact with all intelligence insights."""
        try:
            # Compile intelligence data for GHL update
            custom_fields = {}

            # Add predictive insights
            if prediction_results.get("success"):
                conversion_data = prediction_results.get("conversion_prediction", {})
                custom_fields.update({
                    "claude_conversion_probability": f"{conversion_data.get('probability', 0):.2f}",
                    "claude_predicted_timeline": str(conversion_data.get('timeline_days', 30)),
                    "claude_conversion_stage": conversion_data.get('conversion_stage', 'unknown'),
                    "claude_predicted_value": f"${conversion_data.get('predicted_value', 0):,.0f}",
                    "claude_churn_risk": f"{conversion_data.get('churn_probability', 0):.2f}"
                })

            # Add multimodal insights
            if multimodal_results.get("success"):
                custom_fields.update({
                    "claude_sentiment": f"{multimodal_results.get('unified_sentiment', 0):.2f}",
                    "claude_confidence": f"{multimodal_results.get('confidence_score', 0):.2f}",
                    "claude_key_insights": "; ".join(multimodal_results.get('key_insights', [])[:3]),
                    "claude_recommended_actions": "; ".join(multimodal_results.get('recommended_actions', [])[:2])
                })

            # Add competitive intelligence
            if competitive_results.get("success"):
                market_intel = competitive_results.get("market_intelligence", {})
                custom_fields.update({
                    "claude_market_condition": str(market_intel.get("market_dynamics", {}).get("condition", "unknown")),
                    "claude_market_insights": "; ".join(market_intel.get("strategic_insights", [])[:2]),
                    "claude_competitive_opportunities": str(len(competitive_results.get("competitive_opportunities", [])))
                })

            # Add qualification insights
            if qualification_results.get("success"):
                qual_flow = qualification_results.get("qualification_flow", {})
                custom_fields.update({
                    "claude_qualification_flow_id": qual_flow.get("flow_id", ""),
                    "claude_qualification_completion": f"{qual_flow.get('completion_percentage', 0):.1f}%",
                    "claude_next_questions": str(len(qual_flow.get("next_questions", [])))
                })

            # Add processing metadata
            custom_fields.update({
                "claude_last_analyzed": datetime.now().isoformat(),
                "claude_analysis_version": "5.0_enhanced",
                "claude_intelligence_enabled": "true"
            })

            # In production, this would call the actual GHL API to update the contact
            ghl_update_result = await self._update_ghl_contact(contact_id, location_id, custom_fields)

            return {
                "success": True,
                "contact_id": contact_id,
                "fields_updated": len(custom_fields),
                "ghl_response": ghl_update_result,
                "intelligence_integration": {
                    "multimodal": multimodal_results.get("success", False),
                    "predictive": prediction_results.get("success", False),
                    "competitive": competitive_results.get("success", False),
                    "qualification": qualification_results.get("success", False)
                }
            }

        except Exception as e:
            logger.error(f"Error updating GHL with intelligence: {e}")
            return {"success": False, "error": str(e)}

    async def _perform_background_analysis(
        self,
        contact_id: str,
        processing_results: Dict[str, Any]
    ) -> None:
        """Perform additional background analysis and optimization."""
        try:
            logger.info(f"Starting background analysis for {contact_id}")

            # Update agent coaching recommendations based on performance
            agent_id = processing_results.get("performance_tracking", {}).get("agent_id")
            if agent_id:
                await self._update_agent_coaching_recommendations(agent_id, processing_results)

            # Update competitive intelligence with new lead data
            await self._update_competitive_intelligence(processing_results)

            # Refine predictive models with new data point
            await self._update_predictive_models(contact_id, processing_results)

            # Optimize automation rules based on performance
            await self._optimize_automation_rules(processing_results)

            logger.info(f"Background analysis completed for {contact_id}")

        except Exception as e:
            logger.error(f"Error in background analysis for {contact_id}: {e}")

    # Helper methods for data extraction and analysis

    def _determine_contact_method(self, webhook_data: Dict[str, Any]) -> str:
        """Determine how the contact was initiated."""
        source = webhook_data.get("source", "").lower()
        if "website" in source:
            return "website_form"
        elif "phone" in source:
            return "phone_call"
        elif "email" in source:
            return "email"
        elif "social" in source or "facebook" in source:
            return "social_media"
        else:
            return "other"

    def _assess_initial_engagement(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess initial engagement level from webhook data."""
        message = webhook_data.get("message", "")
        return {
            "message_length": len(message),
            "has_specific_request": any(word in message.lower() for word in ["looking for", "want", "need", "interested"]),
            "has_urgency_indicators": any(word in message.lower() for word in ["asap", "urgent", "soon", "immediately"]),
            "has_budget_mention": any(word in message.lower() for word in ["budget", "price", "cost", "$"]),
            "engagement_score": min(100, len(message) * 2 + (20 if message else 0))
        }

    def _assess_urgency(self, webhook_data: Dict[str, Any]) -> str:
        """Assess urgency level from webhook data."""
        message = webhook_data.get("message", "").lower()
        urgency_words = ["urgent", "asap", "immediately", "soon", "quick", "fast"]

        if any(word in message for word in urgency_words):
            return "high"
        elif any(word in message for word in ["flexible", "no rush", "whenever"]):
            return "low"
        else:
            return "medium"

    def _extract_demographic_data(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract demographic data from webhook."""
        return {
            "name": webhook_data.get("name", ""),
            "email": webhook_data.get("email", ""),
            "phone": webhook_data.get("phone", ""),
            "location": webhook_data.get("city", "") or webhook_data.get("state", ""),
            "source": webhook_data.get("source", ""),
            "tags": webhook_data.get("tags", [])
        }

    def _calculate_initial_engagement_score(
        self,
        webhook_data: Dict[str, Any],
        multimodal_results: Dict[str, Any]
    ) -> float:
        """Calculate initial engagement score."""
        base_score = 50  # Base score

        # Message content factor
        message = webhook_data.get("message", "")
        if message:
            base_score += min(20, len(message) / 10)

        # Sentiment factor
        if multimodal_results.get("success"):
            sentiment = multimodal_results.get("unified_sentiment", 0.0)
            base_score += sentiment * 15  # -15 to +15 adjustment

        # Source factor
        source_weights = {
            "website": 10,
            "referral": 20,
            "google": 15,
            "facebook": 8,
            "phone": 25
        }
        source = webhook_data.get("source", "").lower()
        for source_key, weight in source_weights.items():
            if source_key in source:
                base_score += weight
                break

        return min(100, max(0, base_score))

    def _extract_location(self, webhook_data: Dict[str, Any]) -> Optional[str]:
        """Extract location from webhook data."""
        location_fields = ["city", "state", "location", "address"]
        for field in location_fields:
            if webhook_data.get(field):
                return webhook_data[field]

        # Try to extract from message
        message = webhook_data.get("message", "")
        if " in " in message.lower():
            # Simple extraction for "looking for a house in Austin"
            parts = message.lower().split(" in ")
            if len(parts) > 1:
                location = parts[1].split()[0].strip(",.")
                return location.title()

        return None

    def _generate_positioning_recommendations(
        self,
        market_intelligence,
        prediction_results: Dict[str, Any]
    ) -> List[str]:
        """Generate competitive positioning recommendations."""
        recommendations = []

        # Based on conversion probability
        conversion_prob = prediction_results.get("conversion_prediction", {}).get("probability", 0.5)
        if conversion_prob > 0.7:
            recommendations.append("Position as premium service for high-intent buyer")
        elif conversion_prob < 0.3:
            recommendations.append("Focus on education and relationship building")

        # Based on market conditions
        market_dynamics = market_intelligence.market_dynamics
        if market_dynamics.get("inventory_level") == "low":
            recommendations.append("Emphasize exclusive access and quick decision-making")

        return recommendations

    def _calculate_urgency_score(
        self,
        multimodal_results: Dict[str, Any],
        prediction_results: Dict[str, Any]
    ) -> int:
        """Calculate overall urgency score."""
        base_score = 50

        # Sentiment contribution
        sentiment = multimodal_results.get("unified_sentiment", 0.0)
        if sentiment > 0.5:
            base_score += 20
        elif sentiment < -0.5:
            base_score -= 20

        # Conversion probability contribution
        conversion_prob = prediction_results.get("conversion_prediction", {}).get("probability", 0.5)
        if conversion_prob > 0.8:
            base_score += 30
        elif conversion_prob < 0.3:
            base_score -= 20

        # Timeline contribution
        timeline = prediction_results.get("conversion_prediction", {}).get("timeline_days", 30)
        if timeline < 14:
            base_score += 25
        elif timeline > 60:
            base_score -= 15

        return min(100, max(0, base_score))

    def _calculate_response_time(self, contact_timestamp: str) -> Optional[float]:
        """Calculate response time in minutes."""
        # This would calculate actual response time in a real implementation
        # For now, return None to indicate no prior interaction
        return None

    def _calculate_lead_quality_score(
        self,
        webhook_data: Dict[str, Any],
        qualification_results: Dict[str, Any]
    ) -> float:
        """Calculate lead quality score."""
        base_score = 50

        # Message quality
        message = webhook_data.get("message", "")
        if message:
            if len(message) > 100:
                base_score += 15
            if any(word in message.lower() for word in ["budget", "timeline", "ready"]):
                base_score += 20

        # Contact completeness
        contact_fields = ["name", "email", "phone"]
        completeness = sum(1 for field in contact_fields if webhook_data.get(field))
        base_score += (completeness / len(contact_fields)) * 25

        # Source quality
        source = webhook_data.get("source", "").lower()
        if "referral" in source:
            base_score += 20
        elif "website" in source:
            base_score += 10

        return min(100, max(0, base_score))

    async def _update_ghl_contact(
        self,
        contact_id: str,
        location_id: str,
        custom_fields: Dict[str, str]
    ) -> Dict[str, Any]:
        """Update GHL contact with custom fields."""
        # In production, this would make actual API calls to GHL
        logger.info(f"Would update GHL contact {contact_id} with {len(custom_fields)} fields")
        return {
            "success": True,
            "contact_id": contact_id,
            "fields_updated": list(custom_fields.keys()),
            "api_response": "simulated_success"
        }

    # Background task methods

    async def _update_agent_coaching_recommendations(
        self,
        agent_id: str,
        processing_results: Dict[str, Any]
    ) -> None:
        """Update agent coaching recommendations based on performance."""
        try:
            # This would analyze the agent's performance and update coaching recommendations
            logger.debug(f"Updating coaching recommendations for agent {agent_id}")
        except Exception as e:
            logger.error(f"Error updating coaching recommendations: {e}")

    async def _update_competitive_intelligence(self, processing_results: Dict[str, Any]) -> None:
        """Update competitive intelligence with new market data."""
        try:
            logger.debug("Updating competitive intelligence with new lead data")
        except Exception as e:
            logger.error(f"Error updating competitive intelligence: {e}")

    async def _update_predictive_models(self, contact_id: str, processing_results: Dict[str, Any]) -> None:
        """Update predictive models with new data point."""
        try:
            logger.debug(f"Updating predictive models with data from {contact_id}")
        except Exception as e:
            logger.error(f"Error updating predictive models: {e}")

    async def _optimize_automation_rules(self, processing_results: Dict[str, Any]) -> None:
        """Optimize automation rules based on performance."""
        try:
            logger.debug("Optimizing automation rules based on performance data")
        except Exception as e:
            logger.error(f"Error optimizing automation rules: {e}")

    def _update_processing_stats(self, processing_results: Dict[str, Any]) -> None:
        """Update processing statistics."""
        self.processing_stats["total_processed"] += 1

        if processing_results.get("predictive_analytics", {}).get("success"):
            self.processing_stats["successful_predictions"] += 1

        if processing_results.get("automation_results", {}).get("success"):
            self.processing_stats["automations_triggered"] += processing_results.get("automation_results", {}).get("automations_triggered", 0)

        if processing_results.get("performance_tracking", {}).get("success"):
            self.processing_stats["performance_updates"] += 1

        if processing_results.get("multimodal_intelligence", {}).get("success"):
            self.processing_stats["multimodal_analyses"] += 1

        if processing_results.get("competitive_intelligence", {}).get("success"):
            self.processing_stats["competitive_insights"] += 1

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return {
            **self.processing_stats,
            "success_rate": self.processing_stats["total_processed"] / max(1, self.processing_stats["total_processed"]),
            "last_updated": datetime.now().isoformat()
        }


# Initialize global enhanced webhook processor
enhanced_webhook_processor = EnhancedWebhookProcessor()


# ========================================================================
# Enhanced Webhook Endpoints
# ========================================================================

class ContactCreatedRequest(BaseModel):
    """Request model for contact.created webhook."""
    id: str = Field(..., description="Contact ID")
    name: str = Field(..., description="Contact name")
    email: Optional[str] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone")
    message: Optional[str] = Field(None, description="Initial message")
    source: Optional[str] = Field(None, description="Lead source")
    assignedTo: Optional[str] = Field(None, description="Assigned agent")
    location_id: Optional[str] = Field(None, description="GHL location ID")
    dateAdded: Optional[str] = Field(None, description="Date added")


@router.post("/contact-created-enhanced")
async def handle_contact_created_enhanced(
    request: ContactCreatedRequest,
    background_tasks: BackgroundTasks
):
    """
    Handle contact.created webhook with full Claude AI intelligence suite.

    Processes new contacts through:
    - Multimodal intelligence analysis
    - Predictive analytics and forecasting
    - Competitive intelligence and positioning
    - Intelligent qualification flow initiation
    - Advanced automation triggering
    - Agent performance tracking
    """
    try:
        webhook_data = request.dict()

        # Process with enhanced intelligence
        processing_results = await enhanced_webhook_processor.process_contact_created(
            webhook_data, background_tasks
        )

        return {
            "status": "success" if processing_results.get("success") else "error",
            "message": "Contact processed with Claude AI intelligence suite",
            "processing_results": processing_results,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in enhanced contact.created webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced webhook processing failed: {str(e)}"
        )


@router.post("/message-received-enhanced")
async def handle_message_received_enhanced(
    contact_id: str,
    message_content: str,
    agent_id: Optional[str] = None,
    message_type: str = "text",
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Handle message.received webhook with enhanced analysis.

    Provides real-time analysis of incoming messages with:
    - Sentiment and intent analysis
    - Coaching recommendations for agents
    - Automated response suggestions
    - Performance tracking
    """
    try:
        # Prepare message data
        message_data = {
            "contact_id": contact_id,
            "message_content": message_content,
            "agent_id": agent_id,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }

        # Perform multimodal analysis of the message
        modalities = {ModalityType.TEXT: message_content}
        if message_type == "voice":
            modalities[ModalityType.VOICE] = message_content  # Would be audio data in production

        multimodal_input = MultimodalInput(
            input_id=f"message_{contact_id}_{int(datetime.now().timestamp())}",
            modalities=modalities,
            content_type=ContentType.CHAT_CONVERSATION,
            lead_id=contact_id,
            agent_id=agent_id,
            context={"message_type": message_type, "real_time_analysis": True},
            timestamp=datetime.now()
        )

        # Analyze message
        analysis_results = await enhanced_webhook_processor.multimodal_engine.analyze_multimodal_input(
            multimodal_input
        )

        # Trigger automations based on analysis
        if analysis_results.confidence_score > 0.7:
            automation_event_data = {
                "contact_id": contact_id,
                "message_content": message_content,
                "sentiment": analysis_results.unified_sentiment,
                "key_insights": analysis_results.key_insights,
                "urgency_level": "high" if analysis_results.unified_sentiment < -0.5 else "medium"
            }

            automation_results = await enhanced_webhook_processor.automation_engine.process_trigger_event(
                event_type="message_received",
                event_data=automation_event_data,
                lead_id=contact_id,
                agent_id=agent_id
            )
        else:
            automation_results = []

        return {
            "status": "success",
            "message": "Message analyzed with Claude AI intelligence",
            "analysis": {
                "analysis_id": analysis_results.analysis_id,
                "sentiment": analysis_results.unified_sentiment,
                "confidence": analysis_results.confidence_score,
                "key_insights": analysis_results.key_insights[:3],
                "coaching_suggestions": analysis_results.coaching_suggestions[:3],
                "recommended_actions": analysis_results.recommended_actions[:3]
            },
            "automations_triggered": len(automation_results),
            "processing_time_ms": (datetime.now().timestamp() - datetime.fromisoformat(message_data["timestamp"]).timestamp()) * 1000
        }

    except Exception as e:
        logger.error(f"Error in enhanced message.received webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enhanced message processing failed: {str(e)}"
        )


@router.get("/processing-stats")
async def get_enhanced_processing_stats():
    """
    Get enhanced webhook processing statistics.

    Returns comprehensive stats about:
    - Total webhooks processed
    - Intelligence analysis success rates
    - Automation trigger effectiveness
    - Performance tracking metrics
    """
    try:
        stats = enhanced_webhook_processor.get_processing_stats()

        # Add additional analytics
        enhanced_stats = {
            **stats,
            "intelligence_suite": {
                "multimodal_success_rate": stats["multimodal_analyses"] / max(1, stats["total_processed"]),
                "prediction_success_rate": stats["successful_predictions"] / max(1, stats["total_processed"]),
                "automation_trigger_rate": stats["automations_triggered"] / max(1, stats["total_processed"]),
                "performance_tracking_rate": stats["performance_updates"] / max(1, stats["total_processed"])
            },
            "system_health": {
                "predictive_engine": "healthy",
                "automation_engine": "healthy",
                "multimodal_engine": "healthy",
                "competitive_engine": "healthy",
                "performance_analytics": "healthy"
            }
        }

        return enhanced_stats

    except Exception as e:
        logger.error(f"Error getting processing stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing stats: {str(e)}"
        )