"""
Intelligent Conversation Manager for Multi-Tenant Continuous Memory System.

Extends existing ConversationManager with:
- Memory-aware Claude integration
- Behavioral learning and adaptation
- Intelligent qualification sequencing
- Property recommendations with explanations
- Seller insights and market analysis
- Agent assistance and coaching
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from ghl_real_estate_ai.core.conversation_manager import ConversationManager, AIResponse
from ghl_real_estate_ai.services.enhanced_memory_service import EnhancedMemoryService
from ghl_real_estate_ai.services.behavioral_weighting_engine import BehavioralWeightingEngine
from ghl_real_estate_ai.models.memory_models import (
    ConversationWithMemory, ConversationContext, CommunicationStyle,
    QualificationAnalysis, PreferenceType, InteractionType
)
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class EnhancedAIResponse(AIResponse):
    """Enhanced AI response with memory and behavioral insights."""
    agent_suggestions: Dict[str, Any] = None
    property_recommendations: List[Dict[str, Any]] = None
    seller_insights: Dict[str, Any] = None
    memory_context_used: bool = False
    behavioral_insights: Dict[str, Any] = None
    qualification_analysis: Dict[str, Any] = None
    conversation_strategy: str = ""
    confidence_score: float = 0.0


class IntelligentConversationManager(ConversationManager):
    """
    Enhanced conversation manager with memory-aware Claude integration.
    Builds upon existing ConversationManager with advanced memory capabilities.
    """

    def __init__(self, tenant_id: str):
        """
        Initialize intelligent conversation manager for specific tenant.

        Args:
            tenant_id: GHL location ID for tenant isolation
        """
        super().__init__()

        self.tenant_id = tenant_id

        # Enhanced services
        self.enhanced_memory = EnhancedMemoryService()
        self.behavioral_engine = BehavioralWeightingEngine()

        # Lazy-loaded specialized services (will be imported when needed)
        self._intelligent_qualifier = None
        self._property_recommender = None
        self._seller_insights = None
        self._agent_assistant = None

        # Performance tracking
        self.performance_metrics = {
            "memory_retrieval_time_ms": 0.0,
            "qualification_analysis_time_ms": 0.0,
            "behavioral_learning_time_ms": 0.0,
            "total_response_time_ms": 0.0
        }

        logger.info(f"Intelligent conversation manager initialized for tenant {tenant_id}")

    @property
    def intelligent_qualifier(self):
        """Lazy load intelligent qualifier service."""
        if self._intelligent_qualifier is None:
            from ghl_real_estate_ai.services.intelligent_qualifier import IntelligentQualifier
            self._intelligent_qualifier = IntelligentQualifier(self.tenant_id)
        return self._intelligent_qualifier

    @property
    def property_recommender(self):
        """Lazy load property recommendation engine."""
        if self._property_recommender is None:
            from ghl_real_estate_ai.services.property_recommendation_engine import PropertyRecommendationEngine
            self._property_recommender = PropertyRecommendationEngine(self.tenant_id)
        return self._property_recommender

    @property
    def seller_insights(self):
        """Lazy load seller insights service."""
        if self._seller_insights is None:
            from ghl_real_estate_ai.services.seller_insights_service import SellerInsightsService
            self._seller_insights = SellerInsightsService(self.tenant_id)
        return self._seller_insights

    @property
    def agent_assistant(self):
        """Lazy load agent assistance service."""
        if self._agent_assistant is None:
            from ghl_real_estate_ai.services.agent_assistance_service import AgentAssistanceService
            self._agent_assistant = AgentAssistanceService(self.tenant_id)
        return self._agent_assistant

    async def generate_memory_aware_response(
        self,
        contact_id: str,
        user_message: str,
        contact_info: Dict[str, Any],
        is_buyer: bool = True,
        ghl_client: Optional[Any] = None
    ) -> EnhancedAIResponse:
        """
        Generate Claude response incorporating full memory context and intelligent assistance.
        Extends existing generate_response method with memory awareness.
        """
        start_time = time.time()

        try:
            # Phase 1: Load comprehensive memory context
            memory_start_time = time.time()
            memory_context = await self.enhanced_memory.get_conversation_with_memory(
                self.tenant_id, contact_id
            )
            self.performance_metrics["memory_retrieval_time_ms"] = (time.time() - memory_start_time) * 1000

            # Phase 2: Analyze conversation stage and qualification gaps
            qualification_start_time = time.time()
            qualification_analysis = await self.intelligent_qualifier.analyze_qualification_gaps(
                memory_context.conversation,
                memory_context.get_behavioral_insights()
            )
            self.performance_metrics["qualification_analysis_time_ms"] = (time.time() - qualification_start_time) * 1000

            # Phase 3: Extract and update behavioral learning
            behavioral_start_time = time.time()
            await self._update_behavioral_learning_from_interaction(
                memory_context,
                user_message,
                contact_info
            )
            self.performance_metrics["behavioral_learning_time_ms"] = (time.time() - behavioral_start_time) * 1000

            # Phase 4: Generate adaptive system prompt based on learning
            adaptive_prompt = await self._build_memory_aware_system_prompt(
                memory_context,
                qualification_analysis,
                is_buyer
            )

            # Phase 5: Enhance with specialized Claude features
            property_insights = None
            seller_insights = None

            if is_buyer:
                # Property recommendations with explanations
                property_insights = await self.property_recommender.generate_personalized_recommendations(
                    memory_context.conversation,
                    memory_context.behavioral_preferences,
                    memory_context.property_interactions
                )
            else:
                # Seller insights and market analysis
                seller_insights = await self.seller_insights.generate_market_analysis(
                    memory_context.conversation.extracted_preferences,
                    memory_context.get_behavioral_insights()
                )

            # Phase 6: Agent assistance suggestions
            agent_suggestions = await self.agent_assistant.suggest_conversation_strategies(
                memory_context.conversation,
                memory_context.get_behavioral_insights(),
                memory_context.conversation.conversation_stage
            )

            # Phase 7: Generate response with full memory context using existing parent method
            # But first update the conversation context with memory data
            legacy_context = await self._convert_memory_to_legacy_context(memory_context)

            # Call parent method with enhanced context
            base_response = await super().generate_response(
                user_message,
                contact_info,
                legacy_context,
                is_buyer,
                tenant_config=await self._get_tenant_config(),
                ghl_client=ghl_client
            )

            # Phase 8: Create enhanced response with all insights
            enhanced_response = EnhancedAIResponse(
                message=base_response.message,
                extracted_data=base_response.extracted_data,
                reasoning=base_response.reasoning,
                lead_score=base_response.lead_score,

                # Enhanced features
                agent_suggestions=agent_suggestions,
                property_recommendations=property_insights.recommendations if property_insights else None,
                seller_insights=seller_insights,
                memory_context_used=True,
                behavioral_insights=memory_context.get_behavioral_insights(),
                qualification_analysis=qualification_analysis._asdict() if hasattr(qualification_analysis, '_asdict') else qualification_analysis,
                conversation_strategy=self._determine_conversation_strategy(qualification_analysis, memory_context),
                confidence_score=self._calculate_response_confidence(qualification_analysis, memory_context)
            )

            # Phase 9: Save updated context back to enhanced memory
            await self._save_enhanced_conversation_update(
                memory_context,
                user_message,
                enhanced_response,
                contact_id
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in memory-aware response generation: {e}")

            # Fallback to parent method on error
            try:
                legacy_context = await super().get_context(contact_id, self.tenant_id)
                base_response = await super().generate_response(
                    user_message,
                    contact_info,
                    legacy_context,
                    is_buyer,
                    tenant_config=await self._get_tenant_config(),
                    ghl_client=ghl_client
                )

                return EnhancedAIResponse(
                    message=base_response.message,
                    extracted_data=base_response.extracted_data,
                    reasoning=f"Fallback mode: {base_response.reasoning}",
                    lead_score=base_response.lead_score,
                    memory_context_used=False
                )
            except Exception as fallback_error:
                logger.error(f"Fallback response generation failed: {fallback_error}")

                # Ultimate fallback
                return EnhancedAIResponse(
                    message=f"Thanks for reaching out! I'm having a technical issue—give me just a moment and I'll get back to you.",
                    extracted_data={},
                    reasoning="Error occurred",
                    lead_score=0,
                    memory_context_used=False
                )

        finally:
            self.performance_metrics["total_response_time_ms"] = (time.time() - start_time) * 1000

            # Log performance metrics if response time is high
            if self.performance_metrics["total_response_time_ms"] > 1000:  # > 1 second
                logger.warning(f"Slow response time: {self.performance_metrics}")

    async def analyze_conversation_patterns(
        self,
        contact_id: str,
        lookback_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze conversation patterns for behavioral insights.

        Args:
            contact_id: GHL contact ID
            lookback_days: How many days back to analyze

        Returns:
            Comprehensive pattern analysis
        """
        try:
            memory_context = await self.enhanced_memory.get_conversation_with_memory(
                self.tenant_id, contact_id
            )

            if not memory_context.message_history:
                return {"error": "No conversation history available"}

            # Analyze message patterns
            message_patterns = self._analyze_message_patterns(memory_context.message_history, lookback_days)

            # Analyze behavioral evolution
            behavioral_evolution = self._analyze_behavioral_evolution(memory_context.behavioral_preferences)

            # Analyze property interaction patterns
            property_patterns = memory_context.get_property_interaction_patterns()

            # Generate communication insights
            communication_insights = await self._generate_communication_insights(
                memory_context, message_patterns
            )

            return {
                "conversation_analysis": {
                    "total_messages": len(memory_context.message_history),
                    "conversation_span_days": self._calculate_conversation_span_days(memory_context.message_history),
                    "avg_response_time_hours": self._calculate_avg_response_time(memory_context.message_history),
                    "engagement_level": self._calculate_engagement_level(memory_context)
                },
                "message_patterns": message_patterns,
                "behavioral_evolution": behavioral_evolution,
                "property_patterns": property_patterns,
                "communication_insights": communication_insights,
                "behavioral_profile": memory_context.get_behavioral_insights(),
                "recommendations": await self._generate_conversation_recommendations(memory_context)
            }

        except Exception as e:
            logger.error(f"Error analyzing conversation patterns: {e}")
            return {"error": str(e)}

    async def suggest_next_best_action(
        self,
        contact_id: str
    ) -> Dict[str, Any]:
        """
        Suggest the next best action for a lead based on conversation analysis.

        Args:
            contact_id: GHL contact ID

        Returns:
            Next best action suggestions with reasoning
        """
        try:
            memory_context = await self.enhanced_memory.get_conversation_with_memory(
                self.tenant_id, contact_id
            )

            # Analyze qualification status
            qualification_analysis = await self.intelligent_qualifier.analyze_qualification_gaps(
                memory_context.conversation,
                memory_context.get_behavioral_insights()
            )

            # Get conversation patterns
            patterns = await self.analyze_conversation_patterns(contact_id)

            # Determine best action based on multiple factors
            suggested_action = await self._determine_next_best_action(
                memory_context,
                qualification_analysis,
                patterns
            )

            return {
                "suggested_action": suggested_action,
                "reasoning": suggested_action.get("reasoning", ""),
                "priority_level": suggested_action.get("priority", "medium"),
                "estimated_impact": suggested_action.get("impact", "medium"),
                "timing_recommendation": suggested_action.get("timing", "within_24_hours"),
                "qualification_status": qualification_analysis,
                "conversation_health": patterns.get("conversation_analysis", {}),
                "behavioral_insights": memory_context.get_behavioral_insights()
            }

        except Exception as e:
            logger.error(f"Error suggesting next best action: {e}")
            return {"error": str(e)}

    # Helper methods for memory-aware processing

    async def _build_memory_aware_system_prompt(
        self,
        memory_context: ConversationWithMemory,
        qualification_analysis: Any,
        is_buyer: bool
    ) -> str:
        """Build adaptive system prompt based on memory context."""

        from ghl_real_estate_ai.prompts.system_prompts import build_system_prompt

        conversation = memory_context.conversation
        contact_name = "there"  # Will be provided by caller

        # Enhanced context from memory
        behavioral_insights = memory_context.get_behavioral_insights()
        property_patterns = memory_context.get_property_interaction_patterns()

        # Build base system prompt using existing function
        base_prompt = build_system_prompt(
            contact_name=contact_name,
            conversation_stage=conversation.conversation_stage.value,
            lead_score=conversation.lead_score,
            extracted_preferences=conversation.extracted_preferences,
            relevant_knowledge="",  # Will be filled by RAG
            is_buyer=is_buyer,
            available_slots="",  # Will be filled by calendar integration
            appointment_status="",
            property_recommendations="",
            is_returning_lead=memory_context.is_returning_lead,
            hours_since=memory_context.hours_since_last_interaction
        )

        # Add memory-specific enhancements
        memory_enhancements = []

        if behavioral_insights:
            memory_enhancements.append(f"BEHAVIORAL INSIGHTS: {behavioral_insights}")

        if property_patterns and property_patterns.get("total_interactions", 0) > 0:
            memory_enhancements.append(f"PROPERTY INTERACTION PATTERNS: {property_patterns}")

        if memory_context.is_returning_lead:
            memory_enhancements.append(f"RETURNING LEAD CONTEXT: Last interaction was {memory_context.hours_since_last_interaction:.1f} hours ago. {memory_context.memory_context_summary or ''}")

        if hasattr(qualification_analysis, 'missing_qualifiers') and qualification_analysis.missing_qualifiers:
            memory_enhancements.append(f"QUALIFICATION GAPS: Missing {qualification_analysis.missing_qualifiers}")

        if memory_enhancements:
            return base_prompt + "\n\nMEMORY CONTEXT:\n" + "\n".join(memory_enhancements)

        return base_prompt

    async def _update_behavioral_learning_from_interaction(
        self,
        memory_context: ConversationWithMemory,
        user_message: str,
        contact_info: Dict[str, Any]
    ):
        """Update behavioral learning based on new interaction."""

        try:
            interaction_data = {
                "message_content": user_message,
                "message_length": len(user_message),
                "timestamp": datetime.utcnow().isoformat(),
                "contact_info": contact_info
            }

            # Update behavioral preferences using enhanced memory service
            await self.enhanced_memory.update_behavioral_preferences(
                memory_context.conversation.id,
                interaction_data,
                learning_source="conversation_interaction",
                claude_reasoning="User interaction behavioral analysis"
            )

        except Exception as e:
            logger.error(f"Error updating behavioral learning: {e}")

    async def _convert_memory_to_legacy_context(self, memory_context: ConversationWithMemory) -> Dict[str, Any]:
        """Convert enhanced memory context to legacy format for compatibility."""

        from ghl_real_estate_ai.models.memory_models import convert_conversation_to_legacy_context

        return convert_conversation_to_legacy_context(memory_context)

    async def _save_enhanced_conversation_update(
        self,
        memory_context: ConversationWithMemory,
        user_message: str,
        ai_response: EnhancedAIResponse,
        contact_id: str
    ):
        """Save updated conversation context with enhancements."""

        try:
            # Update conversation with new message and extracted data
            conversation = memory_context.conversation

            # Update extracted preferences with new data
            if ai_response.extracted_data:
                conversation.extracted_preferences.update(ai_response.extracted_data)

            # Update lead score
            conversation.lead_score = ai_response.lead_score

            # Update last interaction time
            conversation.last_interaction_at = datetime.utcnow()

            # Save enhanced context
            await self.enhanced_memory.save_enhanced_context(
                self.tenant_id,
                contact_id,
                memory_context
            )

        except Exception as e:
            logger.error(f"Error saving enhanced conversation update: {e}")

    async def _get_tenant_config(self) -> Optional[Dict[str, Any]]:
        """Get tenant-specific configuration."""
        try:
            from ghl_real_estate_ai.services.tenant_service import TenantService
            tenant_service = TenantService()
            return await tenant_service.get_tenant_config(self.tenant_id)
        except Exception as e:
            logger.error(f"Error getting tenant config: {e}")
            return None

    def _determine_conversation_strategy(
        self,
        qualification_analysis: Any,
        memory_context: ConversationWithMemory
    ) -> str:
        """Determine the best conversation strategy based on analysis."""

        if hasattr(qualification_analysis, 'jorge_methodology_score'):
            score = qualification_analysis.jorge_methodology_score

            if score >= 5:
                return "closing_focus"
            elif score >= 3:
                return "qualification_completion"
            elif score >= 1:
                return "active_qualification"
            else:
                return "initial_engagement"

        return "adaptive_response"

    def _calculate_response_confidence(
        self,
        qualification_analysis: Any,
        memory_context: ConversationWithMemory
    ) -> float:
        """Calculate confidence score for the response."""

        confidence_factors = []

        # Qualification completeness
        if hasattr(qualification_analysis, 'confidence_level'):
            confidence_factors.append(qualification_analysis.confidence_level)

        # Behavioral data availability
        behavioral_insights = memory_context.get_behavioral_insights()
        if behavioral_insights:
            confidence_factors.append(0.8)

        # Conversation history length
        message_count = len(memory_context.message_history)
        if message_count > 10:
            confidence_factors.append(0.9)
        elif message_count > 5:
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(0.5)

        # Property interaction data
        property_patterns = memory_context.get_property_interaction_patterns()
        if property_patterns.get("total_interactions", 0) > 5:
            confidence_factors.append(0.8)

        # Calculate weighted average
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)

        return 0.5

    # Analysis helper methods

    def _analyze_message_patterns(
        self,
        messages: List,
        lookback_days: int
    ) -> Dict[str, Any]:
        """Analyze message patterns for behavioral insights."""

        if not messages:
            return {}

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)
        recent_messages = [
            msg for msg in messages
            if msg.timestamp >= cutoff_date
        ]

        if not recent_messages:
            return {}

        # Calculate patterns
        user_messages = [msg for msg in recent_messages if msg.role.value == "user"]
        assistant_messages = [msg for msg in recent_messages if msg.role.value == "assistant"]

        return {
            "total_messages": len(recent_messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "avg_message_length": sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0,
            "message_frequency_per_day": len(recent_messages) / lookback_days,
            "response_patterns": self._analyze_response_patterns(recent_messages)
        }

    def _analyze_behavioral_evolution(
        self,
        behavioral_preferences: List
    ) -> Dict[str, Any]:
        """Analyze how behavioral preferences have evolved."""

        if not behavioral_preferences:
            return {}

        # Group by preference type
        by_type = {}
        for pref in behavioral_preferences:
            pref_type = pref.preference_type.value
            if pref_type not in by_type:
                by_type[pref_type] = []
            by_type[pref_type].append(pref)

        evolution = {}
        for pref_type, prefs in by_type.items():
            # Sort by timestamp
            sorted_prefs = sorted(prefs, key=lambda x: x.timestamp)

            if len(sorted_prefs) > 1:
                evolution[pref_type] = {
                    "trend": "evolving",
                    "confidence_change": sorted_prefs[-1].confidence_score - sorted_prefs[0].confidence_score,
                    "total_observations": len(sorted_prefs),
                    "latest_confidence": sorted_prefs[-1].confidence_score
                }
            else:
                evolution[pref_type] = {
                    "trend": "stable",
                    "confidence_change": 0,
                    "total_observations": 1,
                    "latest_confidence": sorted_prefs[0].confidence_score
                }

        return evolution

    def _analyze_response_patterns(self, messages: List) -> Dict[str, Any]:
        """Analyze response timing and pattern."""

        user_messages = [msg for msg in messages if msg.role.value == "user"]

        if len(user_messages) < 2:
            return {}

        # Calculate time between messages
        time_gaps = []
        for i in range(1, len(user_messages)):
            gap = (user_messages[i].timestamp - user_messages[i-1].timestamp).total_seconds() / 3600  # hours
            time_gaps.append(gap)

        return {
            "avg_response_gap_hours": sum(time_gaps) / len(time_gaps) if time_gaps else 0,
            "response_consistency": "consistent" if max(time_gaps) - min(time_gaps) < 24 else "varied",
            "peak_activity_detected": any(gap < 1 for gap in time_gaps)  # Multiple messages within 1 hour
        }

    def _calculate_conversation_span_days(self, messages: List) -> float:
        """Calculate span of conversation in days."""
        if len(messages) < 2:
            return 0

        earliest = min(msg.timestamp for msg in messages)
        latest = max(msg.timestamp for msg in messages)

        return (latest - earliest).total_seconds() / (24 * 3600)

    def _calculate_avg_response_time(self, messages: List) -> float:
        """Calculate average response time in hours."""

        user_messages = [msg for msg in messages if msg.role.value == "user"]
        assistant_messages = [msg for msg in messages if msg.role.value == "assistant"]

        if not user_messages or not assistant_messages:
            return 0

        response_times = []

        for user_msg in user_messages:
            # Find next assistant message
            next_assistant = None
            for assistant_msg in assistant_messages:
                if assistant_msg.timestamp > user_msg.timestamp:
                    next_assistant = assistant_msg
                    break

            if next_assistant:
                gap_hours = (next_assistant.timestamp - user_msg.timestamp).total_seconds() / 3600
                response_times.append(gap_hours)

        return sum(response_times) / len(response_times) if response_times else 0

    def _calculate_engagement_level(self, memory_context: ConversationWithMemory) -> str:
        """Calculate overall engagement level."""

        factors = []

        # Message frequency
        if len(memory_context.message_history) > 20:
            factors.append("high")
        elif len(memory_context.message_history) > 10:
            factors.append("medium")
        else:
            factors.append("low")

        # Property interactions
        property_patterns = memory_context.get_property_interaction_patterns()
        engagement_level = property_patterns.get("engagement_level", "low")
        factors.append(engagement_level)

        # Lead score
        if memory_context.conversation.lead_score >= 7:
            factors.append("high")
        elif memory_context.conversation.lead_score >= 4:
            factors.append("medium")
        else:
            factors.append("low")

        # Calculate overall
        high_count = factors.count("high")
        medium_count = factors.count("medium")

        if high_count >= 2:
            return "high"
        elif high_count + medium_count >= 2:
            return "medium"
        else:
            return "low"

    async def _generate_communication_insights(
        self,
        memory_context: ConversationWithMemory,
        message_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate insights about communication style and preferences."""

        behavioral_insights = memory_context.get_behavioral_insights()

        insights = {
            "communication_style": "adaptive",  # Default
            "preferred_response_time": "standard",
            "information_processing": "balanced",
            "decision_making_style": "analytical"
        }

        # Extract from behavioral insights if available
        if behavioral_insights:
            for pref_type, prefs in behavioral_insights.items():
                if pref_type == "communication_style" and prefs:
                    latest_pref = max(prefs, key=lambda x: x.get("confidence", 0))
                    insights["communication_style"] = latest_pref.get("value", {}).get("style", "adaptive")

                elif pref_type == "info_processing" and prefs:
                    latest_pref = max(prefs, key=lambda x: x.get("confidence", 0))
                    insights["information_processing"] = latest_pref.get("value", {}).get("preference", "balanced")

        # Infer from message patterns
        if message_patterns:
            avg_length = message_patterns.get("avg_message_length", 0)
            if avg_length > 100:
                insights["information_processing"] = "detailed"
            elif avg_length < 30:
                insights["information_processing"] = "concise"

        return insights

    async def _generate_conversation_recommendations(
        self,
        memory_context: ConversationWithMemory
    ) -> List[str]:
        """Generate recommendations for improving conversation outcomes."""

        recommendations = []

        conversation = memory_context.conversation
        behavioral_insights = memory_context.get_behavioral_insights()
        property_patterns = memory_context.get_property_interaction_patterns()

        # Lead score based recommendations
        if conversation.lead_score < 3:
            recommendations.append("Focus on qualification questions to increase lead score")
        elif conversation.lead_score >= 7:
            recommendations.append("High-value lead - prioritize immediate follow-up")

        # Behavioral recommendations
        if behavioral_insights:
            for pref_type, prefs in behavioral_insights.items():
                if prefs and prefs[0].get("confidence", 0) > 0.8:
                    if pref_type == "communication_style":
                        style = prefs[0].get("value", {}).get("style", "")
                        if style == "direct":
                            recommendations.append("Lead prefers direct communication - be concise and specific")
                        elif style == "detailed":
                            recommendations.append("Lead prefers detailed information - provide comprehensive explanations")

        # Property interaction recommendations
        if property_patterns:
            total_interactions = property_patterns.get("total_interactions", 0)
            like_ratio = property_patterns.get("like_ratio", 0)

            if total_interactions > 10 and like_ratio < 0.2:
                recommendations.append("Low property like ratio - refine search criteria or ask about preferences")
            elif like_ratio > 0.7:
                recommendations.append("High property engagement - focus on scheduling viewings")

        # Memory-specific recommendations
        if memory_context.is_returning_lead:
            recommendations.append("Returning lead - acknowledge previous conversations and build continuity")

        return recommendations

    async def _determine_next_best_action(
        self,
        memory_context: ConversationWithMemory,
        qualification_analysis: Any,
        patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine the next best action for the lead."""

        conversation = memory_context.conversation
        lead_score = conversation.lead_score

        # High priority actions for hot leads
        if lead_score >= 7:
            return {
                "action": "schedule_immediate_call",
                "reasoning": f"Hot lead with score {lead_score} - immediate contact recommended",
                "priority": "high",
                "impact": "high",
                "timing": "within_4_hours"
            }

        # Qualification focus for warm leads
        elif lead_score >= 4:
            if hasattr(qualification_analysis, 'missing_qualifiers') and qualification_analysis.missing_qualifiers:
                missing = qualification_analysis.missing_qualifiers
                return {
                    "action": "complete_qualification",
                    "reasoning": f"Warm lead missing: {', '.join(missing[:2])}",
                    "priority": "medium",
                    "impact": "high",
                    "timing": "within_24_hours",
                    "specific_questions": missing[:3]
                }

        # Re-engagement for cold leads
        elif patterns.get("conversation_analysis", {}).get("engagement_level") == "low":
            return {
                "action": "send_reengagement_content",
                "reasoning": "Low engagement detected - nurture sequence recommended",
                "priority": "low",
                "impact": "medium",
                "timing": "within_48_hours"
            }

        # Default nurturing
        return {
            "action": "continue_nurturing",
            "reasoning": "Standard nurture sequence based on lead lifecycle stage",
            "priority": "medium",
            "impact": "medium",
            "timing": "within_24_hours"
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        return self.performance_metrics.copy()