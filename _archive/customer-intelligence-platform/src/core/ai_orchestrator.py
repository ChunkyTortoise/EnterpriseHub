"""
Advanced AI Orchestrator for Customer Intelligence Platform.

Provides multi-modal conversation analysis, workflow automation,
and advanced AI capabilities for enterprise customer intelligence.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel, Field

from .ai_client import get_ai_client
from .event_bus import EventBus, EventType
from .redis_conversation_context import RedisConversationContext
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AnalysisType(Enum):
    """Types of AI analysis available."""
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    INTENT_CLASSIFICATION = "intent_classification"
    URGENCY_DETECTION = "urgency_detection"
    CHURN_PREDICTION = "churn_prediction"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    CONVERSATION_SUMMARY = "conversation_summary"
    NEXT_BEST_ACTION = "next_best_action"


class WorkflowStage(Enum):
    """Automated workflow stages."""
    INITIAL_CONTACT = "initial_contact"
    QUALIFICATION = "qualification" 
    NEEDS_ANALYSIS = "needs_analysis"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    ONBOARDING = "onboarding"
    RETENTION = "retention"


@dataclass
class AIInsight:
    """Structured AI analysis result."""
    insight_id: str
    analysis_type: AnalysisType
    confidence: float  # 0.0 to 1.0
    data: Dict[str, Any]
    reasoning: str
    timestamp: datetime
    source: str  # Which AI model/service generated this


@dataclass
class WorkflowAction:
    """Automated workflow action."""
    action_id: str
    stage: WorkflowStage
    action_type: str  # email, task, escalation, etc.
    payload: Dict[str, Any]
    trigger_condition: str
    scheduled_for: Optional[datetime] = None
    executed: bool = False


class MultiModalAnalyzer:
    """Multi-modal conversation analysis engine."""
    
    def __init__(self):
        self.ai_client = get_ai_client()
        self.supported_modalities = [
            "text", "sentiment", "intent", "behavioral", "contextual"
        ]
    
    async def analyze_conversation(
        self,
        conversation_history: List[Dict],
        customer_context: Dict,
        analysis_types: List[AnalysisType]
    ) -> List[AIInsight]:
        """
        Perform multi-modal analysis on conversation data.
        
        Args:
            conversation_history: List of conversation messages
            customer_context: Customer background and preferences
            analysis_types: Types of analysis to perform
            
        Returns:
            List of AI insights from analysis
        """
        insights = []
        
        # Prepare conversation context for AI analysis
        conversation_text = self._format_conversation(conversation_history)
        
        for analysis_type in analysis_types:
            try:
                insight = await self._perform_analysis(
                    conversation_text,
                    customer_context,
                    analysis_type
                )
                insights.append(insight)
                
            except Exception as e:
                logger.error(f"Analysis failed for {analysis_type}: {e}")
                continue
                
        return insights
    
    def _format_conversation(self, conversation_history: List[Dict]) -> str:
        """Format conversation history for AI analysis."""
        formatted_messages = []
        
        for msg in conversation_history:
            timestamp = msg.get("timestamp", "")
            speaker = msg.get("speaker", "unknown")
            content = msg.get("content", "")
            
            formatted_messages.append(
                f"[{timestamp}] {speaker}: {content}"
            )
            
        return "\n".join(formatted_messages)
    
    async def _perform_analysis(
        self,
        conversation_text: str,
        customer_context: Dict,
        analysis_type: AnalysisType
    ) -> AIInsight:
        """Perform specific type of AI analysis."""
        
        # Analysis-specific prompts
        prompts = {
            AnalysisType.SENTIMENT_ANALYSIS: self._get_sentiment_prompt(),
            AnalysisType.INTENT_CLASSIFICATION: self._get_intent_prompt(),
            AnalysisType.URGENCY_DETECTION: self._get_urgency_prompt(),
            AnalysisType.CHURN_PREDICTION: self._get_churn_prompt(),
            AnalysisType.UPSELL_OPPORTUNITY: self._get_upsell_prompt(),
            AnalysisType.BEHAVIORAL_PATTERN: self._get_behavior_prompt(),
            AnalysisType.CONVERSATION_SUMMARY: self._get_summary_prompt(),
            AnalysisType.NEXT_BEST_ACTION: self._get_next_action_prompt()
        }
        
        prompt = prompts.get(analysis_type)
        if not prompt:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")
        
        # Build analysis context
        analysis_context = f"""
Customer Context: {json.dumps(customer_context, indent=2)}

Conversation History:
{conversation_text}

Analysis Request: {prompt}

Please provide your analysis in the following JSON format:
{{
    "confidence": 0.85,
    "data": {{"key": "value"}},
    "reasoning": "Detailed explanation of the analysis"
}}
"""
        
        # Get AI analysis
        try:
            response = await self.ai_client.generate_response(
                prompt=analysis_context,
                max_tokens=1000,
                temperature=0.3  # Lower temperature for more consistent analysis
            )
            
            # Parse AI response
            analysis_result = json.loads(response.strip())
            
            return AIInsight(
                insight_id=str(uuid.uuid4()),
                analysis_type=analysis_type,
                confidence=analysis_result.get("confidence", 0.0),
                data=analysis_result.get("data", {}),
                reasoning=analysis_result.get("reasoning", ""),
                timestamp=datetime.utcnow(),
                source="claude-3.5-sonnet"
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI analysis response: {e}")
            raise
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
    
    def _get_sentiment_prompt(self) -> str:
        return """
        Analyze the sentiment of this customer conversation.
        Determine: overall sentiment, sentiment trajectory, emotional indicators.
        Return confidence level and detailed sentiment breakdown.
        """
    
    def _get_intent_prompt(self) -> str:
        return """
        Classify the customer's primary intent in this conversation.
        Categories: inquiry, complaint, purchase_intent, support_request, cancellation, upgrade.
        Include intent confidence and supporting evidence.
        """
    
    def _get_urgency_prompt(self) -> str:
        return """
        Assess the urgency level of this customer interaction.
        Scale: 1-5 (1=low, 5=critical).
        Consider: language patterns, explicit urgency indicators, context.
        """
    
    def _get_churn_prompt(self) -> str:
        return """
        Evaluate churn risk for this customer based on conversation patterns.
        Consider: satisfaction indicators, complaint patterns, engagement level.
        Provide churn probability (0-1) and risk factors.
        """
    
    def _get_upsell_prompt(self) -> str:
        return """
        Identify upsell/cross-sell opportunities from this conversation.
        Consider: expressed needs, current usage patterns, satisfaction level.
        Suggest specific products/services and timing recommendations.
        """
    
    def _get_behavior_prompt(self) -> str:
        return """
        Analyze behavioral patterns in customer communication style.
        Identify: communication preferences, decision-making patterns, personality traits.
        Provide insights for personalization strategy.
        """
    
    def _get_summary_prompt(self) -> str:
        return """
        Create a concise summary of this conversation.
        Include: key topics, decisions made, action items, customer satisfaction.
        Focus on business-relevant insights.
        """
    
    def _get_next_action_prompt(self) -> str:
        return """
        Recommend the next best action for this customer relationship.
        Consider: conversation context, customer needs, business objectives.
        Provide specific, actionable recommendations with timing.
        """


class WorkflowAutomationEngine:
    """Automated workflow engine for customer journey orchestration."""
    
    def __init__(self):
        self.ai_client = get_ai_client()
        self.event_bus = EventBus()
        self.active_workflows: Dict[str, List[WorkflowAction]] = {}
    
    async def orchestrate_customer_journey(
        self,
        customer_id: str,
        current_stage: WorkflowStage,
        conversation_insights: List[AIInsight],
        customer_context: Dict
    ) -> List[WorkflowAction]:
        """
        Orchestrate automated actions based on customer journey stage and AI insights.
        
        Args:
            customer_id: Unique customer identifier
            current_stage: Current stage in customer journey
            conversation_insights: AI insights from conversation analysis
            customer_context: Customer background and preferences
            
        Returns:
            List of automated workflow actions to execute
        """
        workflow_actions = []
        
        # Generate stage-specific actions
        stage_actions = await self._generate_stage_actions(
            current_stage, 
            conversation_insights,
            customer_context
        )
        workflow_actions.extend(stage_actions)
        
        # Generate insight-driven actions
        insight_actions = await self._generate_insight_actions(
            conversation_insights,
            customer_context
        )
        workflow_actions.extend(insight_actions)
        
        # Store workflow state
        self.active_workflows[customer_id] = workflow_actions
        
        # Publish workflow events
        await self._publish_workflow_events(customer_id, workflow_actions)
        
        return workflow_actions
    
    async def _generate_stage_actions(
        self,
        stage: WorkflowStage,
        insights: List[AIInsight],
        customer_context: Dict
    ) -> List[WorkflowAction]:
        """Generate actions specific to customer journey stage."""
        
        stage_generators = {
            WorkflowStage.INITIAL_CONTACT: self._generate_initial_contact_actions,
            WorkflowStage.QUALIFICATION: self._generate_qualification_actions,
            WorkflowStage.NEEDS_ANALYSIS: self._generate_needs_analysis_actions,
            WorkflowStage.PROPOSAL: self._generate_proposal_actions,
            WorkflowStage.NEGOTIATION: self._generate_negotiation_actions,
            WorkflowStage.CLOSING: self._generate_closing_actions,
            WorkflowStage.ONBOARDING: self._generate_onboarding_actions,
            WorkflowStage.RETENTION: self._generate_retention_actions
        }
        
        generator = stage_generators.get(stage)
        if generator:
            return await generator(insights, customer_context)
        
        return []
    
    async def _generate_insight_actions(
        self,
        insights: List[AIInsight],
        customer_context: Dict
    ) -> List[WorkflowAction]:
        """Generate actions based on AI insights."""
        actions = []
        
        for insight in insights:
            if insight.confidence < 0.7:  # Skip low-confidence insights
                continue
                
            if insight.analysis_type == AnalysisType.URGENCY_DETECTION:
                urgency_level = insight.data.get("urgency_level", 1)
                if urgency_level >= 4:  # High urgency
                    actions.append(
                        WorkflowAction(
                            action_id=str(uuid.uuid4()),
                            stage=WorkflowStage.INITIAL_CONTACT,
                            action_type="escalation",
                            payload={
                                "priority": "high",
                                "reason": "High urgency detected",
                                "escalation_type": "immediate_response"
                            },
                            trigger_condition=f"urgency_level >= 4"
                        )
                    )
            
            elif insight.analysis_type == AnalysisType.CHURN_PREDICTION:
                churn_probability = insight.data.get("churn_probability", 0.0)
                if churn_probability >= 0.6:  # High churn risk
                    actions.append(
                        WorkflowAction(
                            action_id=str(uuid.uuid4()),
                            stage=WorkflowStage.RETENTION,
                            action_type="retention_campaign",
                            payload={
                                "campaign_type": "churn_prevention",
                                "churn_probability": churn_probability,
                                "retention_offers": insight.data.get("retention_strategies", [])
                            },
                            trigger_condition=f"churn_probability >= 0.6"
                        )
                    )
            
            elif insight.analysis_type == AnalysisType.UPSELL_OPPORTUNITY:
                opportunities = insight.data.get("opportunities", [])
                if opportunities:
                    actions.append(
                        WorkflowAction(
                            action_id=str(uuid.uuid4()),
                            stage=WorkflowStage.PROPOSAL,
                            action_type="upsell_proposal",
                            payload={
                                "opportunities": opportunities,
                                "confidence": insight.confidence,
                                "timing": insight.data.get("recommended_timing", "immediate")
                            },
                            trigger_condition="upsell opportunities detected"
                        )
                    )
        
        return actions
    
    async def _generate_initial_contact_actions(self, insights, context):
        """Generate actions for initial customer contact."""
        return [
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                stage=WorkflowStage.INITIAL_CONTACT,
                action_type="welcome_sequence",
                payload={
                    "template": "personalized_welcome",
                    "customer_preferences": context.get("communication_preferences", {})
                },
                trigger_condition="new customer contact"
            )
        ]
    
    async def _generate_qualification_actions(self, insights, context):
        """Generate actions for customer qualification stage."""
        return [
            WorkflowAction(
                action_id=str(uuid.uuid4()),
                stage=WorkflowStage.QUALIFICATION,
                action_type="qualification_survey",
                payload={
                    "survey_type": "needs_assessment",
                    "personalization": context.get("industry", "general")
                },
                trigger_condition="qualification stage entry"
            )
        ]
    
    async def _generate_needs_analysis_actions(self, insights, context):
        """Generate actions for needs analysis stage."""
        return []  # Implementation based on specific business requirements
    
    async def _generate_proposal_actions(self, insights, context):
        """Generate actions for proposal stage."""
        return []  # Implementation based on specific business requirements
    
    async def _generate_negotiation_actions(self, insights, context):
        """Generate actions for negotiation stage."""
        return []  # Implementation based on specific business requirements
    
    async def _generate_closing_actions(self, insights, context):
        """Generate actions for closing stage."""
        return []  # Implementation based on specific business requirements
    
    async def _generate_onboarding_actions(self, insights, context):
        """Generate actions for customer onboarding."""
        return []  # Implementation based on specific business requirements
    
    async def _generate_retention_actions(self, insights, context):
        """Generate actions for customer retention."""
        return []  # Implementation based on specific business requirements
    
    async def _publish_workflow_events(self, customer_id: str, actions: List[WorkflowAction]):
        """Publish workflow events to event bus."""
        for action in actions:
            await self.event_bus.publish(
                EventType.AI_WORKFLOW_TRIGGERED,
                {
                    "customer_id": customer_id,
                    "action_id": action.action_id,
                    "stage": action.stage.value,
                    "action_type": action.action_type,
                    "payload": action.payload
                }
            )


class AdvancedAIOrchestrator:
    """
    Main orchestrator for advanced AI features.
    
    Coordinates multi-modal analysis and workflow automation
    for comprehensive customer intelligence.
    """
    
    def __init__(self):
        self.analyzer = MultiModalAnalyzer()
        self.workflow_engine = WorkflowAutomationEngine()
        self.conversation_context = RedisConversationContext()
        self.event_bus = EventBus()
        
    async def process_customer_interaction(
        self,
        customer_id: str,
        conversation_history: List[Dict],
        customer_context: Dict,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a customer interaction with full AI analysis and workflow automation.
        
        Args:
            customer_id: Unique customer identifier
            conversation_history: Recent conversation messages
            customer_context: Customer background and preferences
            department_id: Optional department context
            
        Returns:
            Comprehensive analysis results and triggered workflows
        """
        # Define analysis types based on conversation context
        analysis_types = [
            AnalysisType.SENTIMENT_ANALYSIS,
            AnalysisType.INTENT_CLASSIFICATION,
            AnalysisType.URGENCY_DETECTION,
            AnalysisType.CHURN_PREDICTION,
            AnalysisType.UPSELL_OPPORTUNITY,
            AnalysisType.NEXT_BEST_ACTION
        ]
        
        # Perform multi-modal analysis
        insights = await self.analyzer.analyze_conversation(
            conversation_history,
            customer_context,
            analysis_types
        )
        
        # Determine customer journey stage
        current_stage = await self._determine_journey_stage(
            customer_context,
            insights
        )
        
        # Orchestrate workflow automation
        workflow_actions = await self.workflow_engine.orchestrate_customer_journey(
            customer_id,
            current_stage,
            insights,
            customer_context
        )
        
        # Store analysis results in Redis
        await self._store_analysis_results(
            customer_id,
            insights,
            workflow_actions,
            department_id
        )
        
        # Publish AI processing events
        await self.event_bus.publish(
            EventType.AI_ANALYSIS_COMPLETED,
            {
                "customer_id": customer_id,
                "department_id": department_id,
                "insights_count": len(insights),
                "workflow_actions_count": len(workflow_actions),
                "journey_stage": current_stage.value
            }
        )
        
        return {
            "customer_id": customer_id,
            "analysis_results": [
                {
                    "insight_id": insight.insight_id,
                    "type": insight.analysis_type.value,
                    "confidence": insight.confidence,
                    "data": insight.data,
                    "reasoning": insight.reasoning
                }
                for insight in insights
            ],
            "workflow_actions": [
                {
                    "action_id": action.action_id,
                    "stage": action.stage.value,
                    "type": action.action_type,
                    "payload": action.payload
                }
                for action in workflow_actions
            ],
            "journey_stage": current_stage.value,
            "processing_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _determine_journey_stage(
        self,
        customer_context: Dict,
        insights: List[AIInsight]
    ) -> WorkflowStage:
        """Determine customer's current journey stage."""
        
        # Simple rule-based stage determination
        # In production, this would use ML models
        
        # Check if customer is new
        if customer_context.get("interaction_count", 0) <= 1:
            return WorkflowStage.INITIAL_CONTACT
        
        # Check for purchase intent
        for insight in insights:
            if insight.analysis_type == AnalysisType.INTENT_CLASSIFICATION:
                intent = insight.data.get("primary_intent")
                if intent == "purchase_intent":
                    return WorkflowStage.PROPOSAL
                elif intent == "complaint":
                    return WorkflowStage.RETENTION
        
        # Default to needs analysis for existing customers
        return WorkflowStage.NEEDS_ANALYSIS
    
    async def _store_analysis_results(
        self,
        customer_id: str,
        insights: List[AIInsight],
        workflow_actions: List[WorkflowAction],
        department_id: Optional[str]
    ):
        """Store analysis results in Redis for future reference."""
        
        analysis_data = {
            "insights": [
                {
                    "insight_id": insight.insight_id,
                    "analysis_type": insight.analysis_type.value,
                    "confidence": insight.confidence,
                    "data": insight.data,
                    "reasoning": insight.reasoning,
                    "timestamp": insight.timestamp.isoformat(),
                    "source": insight.source
                }
                for insight in insights
            ],
            "workflow_actions": [
                {
                    "action_id": action.action_id,
                    "stage": action.stage.value,
                    "action_type": action.action_type,
                    "payload": action.payload,
                    "trigger_condition": action.trigger_condition,
                    "executed": action.executed
                }
                for action in workflow_actions
            ],
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in Redis with TTL
        context_key = f"{department_id}:{customer_id}:ai_analysis" if department_id else f"{customer_id}:ai_analysis"
        await self.conversation_context._store_data(
            context_key,
            analysis_data,
            ttl=86400  # 24 hours
        )


# Singleton instance
_ai_orchestrator = None

def get_ai_orchestrator() -> AdvancedAIOrchestrator:
    """Get the global AI orchestrator instance."""
    global _ai_orchestrator
    if _ai_orchestrator is None:
        _ai_orchestrator = AdvancedAIOrchestrator()
    return _ai_orchestrator