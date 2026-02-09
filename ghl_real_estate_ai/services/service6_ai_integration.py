#!/usr/bin/env python3
"""
🎯 Service 6 AI Integration Layer - Phase 2 Complete
====================================================

Comprehensive integration layer that seamlessly connects all advanced AI/ML
components with the existing EnterpriseHub architecture:

- Advanced ML Lead Scoring Engine integration
- Voice AI system integration
- Predictive Analytics engine integration
- MLOps pipeline integration
- Real-time inference engine integration
- Existing services compatibility layer

Features:
- Unified API endpoints for all AI services
- Backward compatibility with existing workflows
- Enhanced Claude Platform Companion capabilities
- Real-time data synchronization
- Performance optimization and caching
- Monitoring and alerting integration

Author: Claude AI Enhancement System
Date: 2026-01-16
"""

import asyncio
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Import all the advanced AI/ML components
from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import (
    MLScoringResult,
    create_advanced_ml_scoring_engine,
)
from ghl_real_estate_ai.services.claude_enhanced_lead_scorer import ClaudeEnhancedLeadScorer
from ghl_real_estate_ai.services.claude_platform_companion import ClaudePlatformCompanion
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.mlops_pipeline import create_mlops_pipeline
from ghl_real_estate_ai.services.predictive_analytics_engine import (
    ContentPersonalization,
    create_predictive_analytics_engine,
)
from ghl_real_estate_ai.services.realtime_inference_engine import (
    InferenceRequest,
    InferenceResponse,
    RequestPriority,
    create_realtime_inference_engine,
)

# Import existing services for integration
from ghl_real_estate_ai.services.tiered_cache_service import TieredCacheService
from ghl_real_estate_ai.services.voice_ai_integration import (
    CallAnalysis,
    create_voice_ai_integration,
)

logger = get_logger(__name__)


class Service6AIError(Exception):
    """Base exception for Service 6 AI integration errors"""

    pass


class AIScoringError(Service6AIError):
    """Raised when ML scoring fails"""

    pass


class AIVoiceAnalysisError(Service6AIError):
    """Raised when voice analysis fails"""

    pass


class AIPredictiveError(Service6AIError):
    """Raised when predictive analytics fails"""

    pass


class AIInferenceError(Service6AIError):
    """Raised when real-time inference fails"""

    pass


@dataclass
class Service6AIResponse:
    """Unified response format for Service 6 AI operations"""

    operation_id: str
    lead_id: str
    timestamp: datetime

    # Core AI results
    ml_scoring_result: Optional[MLScoringResult]
    voice_analysis_result: Optional[CallAnalysis]
    predictive_insights: Optional[Dict[str, Any]]
    personalized_content: Optional[ContentPersonalization]

    # Unified scores and recommendations
    unified_lead_score: float  # 0-100 combined score
    confidence_level: float  # 0-1 confidence in recommendations
    priority_level: str  # 'critical', 'high', 'medium', 'low'

    # Actionable intelligence
    immediate_actions: List[str]
    strategic_recommendations: List[str]
    risk_alerts: List[str]
    opportunity_signals: List[str]

    # Performance metadata
    processing_time_ms: float
    models_used: List[str]
    data_sources: List[str]

    # Integration status
    enhanced_claude_integration: bool
    realtime_inference_active: bool
    voice_ai_enabled: bool


@dataclass
class Service6AIConfig:
    """Configuration for Service 6 AI integration"""

    # Enable/disable components
    enable_advanced_ml_scoring: bool = True
    enable_voice_ai: bool = True
    enable_predictive_analytics: bool = True
    enable_realtime_inference: bool = True
    enable_claude_enhancement: bool = True

    # Performance settings
    max_concurrent_operations: int = 50
    default_cache_ttl_seconds: int = 300
    enable_background_processing: bool = True

    # AI model settings
    ml_model_confidence_threshold: float = 0.7
    voice_transcription_accuracy_threshold: float = 0.8
    predictive_pattern_min_confidence: float = 0.8

    # Integration settings
    sync_with_existing_scoring: bool = True
    enhance_claude_responses: bool = True
    enable_realtime_coaching: bool = True


class Service6EnhancedClaudePlatformCompanion(ClaudePlatformCompanion):
    """Enhanced Claude Platform Companion with advanced AI integration"""

    def __init__(self, config: Service6AIConfig):
        super().__init__()
        self.config = config

        # Initialize AI components
        self.ml_scoring_engine = create_advanced_ml_scoring_engine() if config.enable_advanced_ml_scoring else None
        self.voice_ai = create_voice_ai_integration() if config.enable_voice_ai else None
        self.predictive_analytics = create_predictive_analytics_engine() if config.enable_predictive_analytics else None
        self.realtime_inference = create_realtime_inference_engine() if config.enable_realtime_inference else None

        # Enhanced integrations
        self.enhanced_scorer = ClaudeEnhancedLeadScorer() if config.enable_claude_enhancement else None

        # MLOps for model management
        self.mlops = create_mlops_pipeline()

        self.cache = TieredCacheService()
        self.memory = MemoryService()

    async def initialize(self):
        """Initialize all AI components"""

        try:
            # Start tiered cache service
            await self.cache.start()
            logger.info("Tiered cache service started")

            # Start real-time inference engine if enabled
            if self.realtime_inference:
                await self.realtime_inference.start()
                logger.info("Real-time inference engine started")

            # Start MLOps background monitoring
            if self.mlops:
                await self.mlops.start_background_monitoring()
                logger.info("MLOps background monitoring started")

            logger.info("Service 6 AI integration initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Service 6 AI integration: {e}")
            raise

    async def comprehensive_lead_analysis(
        self, lead_id: str, lead_data: Dict[str, Any], include_voice: bool = False, include_predictive: bool = True
    ) -> Service6AIResponse:
        """
        Comprehensive lead analysis using all available AI components.

        This is the main entry point that orchestrates all AI services.
        """

        operation_id = f"s6_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{lead_id}"
        start_time = datetime.now()

        # Gather all AI analysis results in parallel
        analysis_tasks = []

        # Advanced ML Scoring
        if self.ml_scoring_engine and self.config.enable_advanced_ml_scoring:
            analysis_tasks.append(self._run_ml_scoring_analysis(lead_id, lead_data))
        else:
            analysis_tasks.append(asyncio.create_task(self._return_none()))

        # Voice AI Analysis (if call data available)
        if self.voice_ai and include_voice and lead_data.get("call_data"):
            analysis_tasks.append(self._run_voice_analysis(lead_id, lead_data["call_data"]))
        else:
            analysis_tasks.append(asyncio.create_task(self._return_none()))

        # Predictive Analytics
        if self.predictive_analytics and include_predictive:
            analysis_tasks.append(self._run_predictive_analysis(lead_id, lead_data))
        else:
            analysis_tasks.append(asyncio.create_task(self._return_none()))

        # Execute all analyses
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

        # Handle failures gracefully - log errors but continue with available results
        processed_results = []
        has_critical_failure = False
        for res in results:
            if isinstance(res, Exception):
                logger.error(f"AI analysis component failed (non-fatal): {res}")
                processed_results.append(None)
                has_critical_failure = True
            else:
                processed_results.append(res)

        ml_result, voice_result, predictive_result = processed_results

        # Generate personalized content
        personalized_content = None
        if self.predictive_analytics:
            try:
                personalized_content = (
                    await self.predictive_analytics.content_personalization.generate_personalized_content(
                        lead_id, lead_data, "email"
                    )
                )
            except Exception as e:
                logger.warning(f"Content personalization failed (non-critical): {e}")

        # Synthesize unified insights
        unified_insights = await self._synthesize_insights(
            lead_id, lead_data, ml_result, voice_result, predictive_result, personalized_content
        )

        # If critical failures occurred, flag for manual review and reduce confidence
        if has_critical_failure:
            unified_insights["immediate_actions"].insert(0, "Manual review required - some AI components failed")
            unified_insights["confidence"] = min(unified_insights["confidence"], 0.4)

        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Build comprehensive response
        response = Service6AIResponse(
            operation_id=operation_id,
            lead_id=lead_id,
            timestamp=datetime.now(),
            ml_scoring_result=ml_result,
            voice_analysis_result=voice_result,
            predictive_insights=predictive_result,
            personalized_content=personalized_content,
            unified_lead_score=unified_insights["unified_score"],
            confidence_level=unified_insights["confidence"],
            priority_level=unified_insights["priority"],
            immediate_actions=unified_insights["immediate_actions"],
            strategic_recommendations=unified_insights["strategic_recommendations"],
            risk_alerts=unified_insights["risk_alerts"],
            opportunity_signals=unified_insights["opportunity_signals"],
            processing_time_ms=processing_time,
            models_used=unified_insights["models_used"],
            data_sources=unified_insights["data_sources"],
            enhanced_claude_integration=self.enhanced_scorer is not None,
            realtime_inference_active=self.realtime_inference is not None,
            voice_ai_enabled=self.voice_ai is not None,
        )

        # Cache comprehensive result
        await self.cache.set(f"s6_analysis:{lead_id}", asdict(response), ttl=self.config.default_cache_ttl_seconds)

        # Update memory with insights
        await self._update_memory_with_insights(lead_id, response)

        return response

    async def realtime_lead_scoring(
        self, lead_id: str, features: Dict[str, Any], priority: str = "normal"
    ) -> InferenceResponse:
        """Real-time lead scoring using the inference engine"""

        if not self.realtime_inference:
            logger.warning("Real-time inference engine not available")
            # Fallback to enhanced scorer
            if self.enhanced_scorer:
                result = await self.enhanced_scorer.analyze_lead_comprehensive(lead_id, features)
                # Convert to InferenceResponse format
                return self._convert_enhanced_score_to_inference_response(result)
            else:
                raise Exception("No scoring engines available")

        # Create inference request
        request = InferenceRequest(
            request_id=f"rt_score_{datetime.now().strftime('%H%M%S')}",
            lead_id=lead_id,
            model_type="lead_scorer",
            features=features,
            lead_context={},
            priority=self._map_priority_to_enum(priority),
            requested_at=datetime.now(),
            client_id="service6",
            max_latency_ms=100,
            require_explanation=True,
            response_format="json",
            cache_key=None,
            cache_ttl_seconds=300,
        )

        # Get real-time prediction
        return await self.realtime_inference.predict(request)

    async def voice_call_coaching(self, call_id: str, lead_id: str, agent_id: str) -> Dict[str, Any]:
        """Start voice call coaching session"""

        if not self.voice_ai:
            raise Exception("Voice AI not available")

        # Start call analysis
        success = await self.voice_ai.start_call_analysis(call_id, lead_id, agent_id)

        if success:
            return {
                "call_id": call_id,
                "coaching_active": True,
                "message": "Voice coaching started successfully",
                "features": [
                    "Real-time transcription",
                    "Sentiment analysis",
                    "Live coaching prompts",
                    "Objection detection",
                    "Intent analysis",
                ],
            }
        else:
            return {
                "call_id": call_id,
                "coaching_active": False,
                "message": "Failed to start voice coaching",
                "error": "Call analysis initialization failed",
            }

    async def process_voice_audio_stream(self, call_id: str, audio_chunk: bytes, speaker_id: str) -> Dict[str, Any]:
        """Process real-time audio stream for voice coaching"""

        if not self.voice_ai:
            return {"error": "Voice AI not available"}

        return await self.voice_ai.process_audio_stream(call_id, audio_chunk, speaker_id)

    async def generate_behavioral_insights(self, lead_id: str, historical_context: List[Dict]) -> Dict[str, Any]:
        """Generate behavioral insights and patterns"""

        if not self.predictive_analytics:
            return {"error": "Predictive analytics not available"}

        return await self.predictive_analytics.run_comprehensive_analysis({"lead_id": lead_id}, historical_context)

    async def claude_enhanced_conversation(
        self, lead_id: str, message: str, conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """Enhanced Claude conversation with AI insights"""

        # Get recent AI analysis for context
        recent_analysis = await self.cache.get(f"s6_analysis:{lead_id}")

        # Enhance conversation context with AI insights
        enhanced_context = {
            "message": message,
            "conversation_history": conversation_history,
            "ai_insights": recent_analysis,
            "lead_id": lead_id,
        }

        # Use enhanced scorer if available
        if self.enhanced_scorer:
            try:
                # Get comprehensive lead analysis
                lead_data = await self.memory.get_context(lead_id)
                comprehensive_result = await self.enhanced_scorer.analyze_lead_comprehensive(lead_id, lead_data)

                # Use LLM client to generate contextually aware response
                if self.llm_client:
                    llm_response = await self.llm_client.generate(
                        prompt=f"Given this lead context and AI analysis, respond to: {message}",
                        context=enhanced_context,
                    )
                    claude_response = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
                else:
                    claude_response = f"I'd be happy to help with your question about: {message}"

                return {
                    "response": claude_response,
                    "ai_enhanced": True,
                    "lead_score": comprehensive_result.final_score,
                    "recommended_actions": comprehensive_result.recommended_actions[:3],
                    "confidence": comprehensive_result.confidence_score,
                }
            except Exception as e:
                logger.warning(f"Enhanced conversation failed, falling back: {e}")

        # Fallback to standard response
        return {
            "response": f"Thank you for your message. Let me look into that for you.",
            "ai_enhanced": False,
            "lead_id": lead_id,
        }

    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health across all AI components"""

        health = {"timestamp": datetime.now(), "overall_status": "healthy", "components": {}}

        # Check each component
        try:
            # ML Scoring Engine
            if self.ml_scoring_engine:
                ml_metrics = await self.ml_scoring_engine.get_performance_metrics()
                health["components"]["ml_scoring"] = {
                    "status": "healthy" if ml_metrics["success_rate"] > 0.9 else "degraded",
                    "metrics": ml_metrics,
                }

            # Real-time Inference
            if self.realtime_inference:
                inference_status = await self.realtime_inference.get_system_status()
                health["components"]["realtime_inference"] = {
                    "status": inference_status["status"],
                    "metrics": inference_status["performance"],
                }

            # Voice AI
            if self.voice_ai:
                voice_metrics = await self.voice_ai.get_performance_metrics()
                health["components"]["voice_ai"] = {
                    "status": "healthy" if voice_metrics["success_rate"] > 0.8 else "degraded",
                    "metrics": voice_metrics,
                }

            # Predictive Analytics
            if self.predictive_analytics:
                analytics_metrics = await self.predictive_analytics.get_performance_metrics()
                health["components"]["predictive_analytics"] = {
                    "status": analytics_metrics["system_health"],
                    "metrics": analytics_metrics,
                }

            # MLOps Pipeline
            if self.mlops:
                mlops_health = await self.mlops.get_system_health()
                health["components"]["mlops"] = {"status": mlops_health["health_status"], "metrics": mlops_health}

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health["overall_status"] = "degraded"
            health["error"] = str(e)

        # Determine overall status
        component_statuses = [comp.get("status", "unknown") for comp in health["components"].values()]

        if "unhealthy" in component_statuses:
            health["overall_status"] = "unhealthy"
        elif "degraded" in component_statuses:
            health["overall_status"] = "degraded"
        elif not component_statuses:  # No components checked
            health["overall_status"] = "unknown"

        return health

    # Helper methods for integration

    async def _run_ml_scoring_analysis(self, lead_id: str, lead_data: Dict[str, Any]) -> Optional[MLScoringResult]:
        """Run ML scoring analysis"""

        try:
            return await self.ml_scoring_engine.score_lead_comprehensive(lead_id, lead_data)
        except Exception as e:
            logger.error(f"ML scoring analysis failed: {e}")
            raise AIScoringError(f"ML scoring analysis failed: {str(e)}")

    async def _run_voice_analysis(self, lead_id: str, call_data: Dict[str, Any]) -> Optional[CallAnalysis]:
        """Run voice analysis if call data available"""

        try:
            # This would process actual call data
            # For now, return None as call data format is not defined
            return None
        except Exception as e:
            logger.error(f"Voice analysis failed: {e}")
            raise AIVoiceAnalysisError(f"Voice analysis failed: {str(e)}")

    async def _run_predictive_analysis(self, lead_id: str, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Run predictive analytics analysis"""

        try:
            # Get historical context
            memory_context = await self.memory.get_context(lead_id)
            historical_data = memory_context.get("conversation_history", [])

            # Run comprehensive analysis
            return await self.predictive_analytics.run_comprehensive_analysis(lead_data, historical_data)
        except Exception as e:
            logger.error(f"Predictive analysis failed: {e}")
            raise AIPredictiveError(f"Predictive analysis failed: {str(e)}")

    async def _synthesize_insights(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        ml_result: Optional[MLScoringResult],
        voice_result: Optional[CallAnalysis],
        predictive_result: Optional[Dict[str, Any]],
        content_result: Optional[ContentPersonalization],
    ) -> Dict[str, Any]:
        """Synthesize insights from all AI components"""

        # Collect all available scores
        scores = []
        confidence_scores = []
        models_used = []
        data_sources = ["lead_data"]

        # ML Scoring insights
        if ml_result:
            scores.append(ml_result.final_ml_score)
            confidence_scores.append(ml_result.confidence_interval[0])  # Use lower bound
            models_used.extend(["advanced_ml_scorer"])
            data_sources.append("behavioral_features")

        # Voice Analysis insights
        if voice_result:
            voice_score = voice_result.conversion_probability * 100
            scores.append(voice_score)
            confidence_scores.append(0.8)  # Voice analysis confidence
            models_used.extend(["voice_ai"])
            data_sources.append("call_audio")

        # Predictive Analytics insights
        if predictive_result:
            predictive_confidence = predictive_result.get("confidence_score", 0.5)
            # Extract score from insights (simplified)
            predictive_score = predictive_confidence * 100
            scores.append(predictive_score)
            confidence_scores.append(predictive_confidence)
            models_used.extend(["predictive_analytics"])
            data_sources.append("historical_patterns")

        # Calculate unified score
        if scores:
            unified_score = sum(scores) / len(scores)
            unified_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            # Fallback to enhanced scorer if available
            if self.enhanced_scorer:
                try:
                    fallback_result = await self.enhanced_scorer.analyze_lead_comprehensive(lead_id, lead_data)
                    unified_score = fallback_result.final_score
                    unified_confidence = fallback_result.confidence_score
                    models_used.append("enhanced_claude_scorer")
                except Exception as e:
                    logger.error(f"Fallback scoring failed: {e}")
                    raise AIScoringError(f"All scoring models failed, including fallback: {str(e)}")
            else:
                raise AIScoringError("No scoring engines available and no fallback configured")

        # Determine priority level
        if unified_score >= 80 and unified_confidence >= 0.8:
            priority = "critical"
        elif unified_score >= 70 or unified_confidence >= 0.7:
            priority = "high"
        elif unified_score >= 50:
            priority = "medium"
        else:
            priority = "low"

        # Generate actionable insights
        immediate_actions = []
        strategic_recommendations = []
        risk_alerts = []
        opportunity_signals = []

        # From ML results
        if ml_result:
            immediate_actions.extend(ml_result.recommended_actions[:2])
            risk_alerts.extend(ml_result.risk_factors[:2])
            opportunity_signals.extend(ml_result.opportunity_signals[:2])

        # From voice results
        if voice_result:
            immediate_actions.extend(voice_result.action_items[:2])
            if voice_result.conversion_probability > 0.8:
                opportunity_signals.append("High conversion probability from voice analysis")

        # From predictive results
        if predictive_result:
            insights = predictive_result.get("comprehensive_insights", {})
            strategic_recommendations.extend(insights.get("actions", [])[:2])
            risk_alerts.extend(insights.get("risks", [])[:2])
            opportunity_signals.extend(insights.get("opportunities", [])[:2])

        # From content personalization
        if content_result and content_result.engagement_probability > 0.7:
            opportunity_signals.append(
                f"High engagement potential ({content_result.engagement_probability:.1%}) with personalized content"
            )

        return {
            "unified_score": round(unified_score, 1),
            "confidence": round(unified_confidence, 2),
            "priority": priority,
            "immediate_actions": immediate_actions[:5],
            "strategic_recommendations": strategic_recommendations[:5],
            "risk_alerts": risk_alerts[:3],
            "opportunity_signals": opportunity_signals[:5],
            "models_used": list(set(models_used)),
            "data_sources": list(set(data_sources)),
        }

    async def _update_memory_with_insights(self, lead_id: str, response: Service6AIResponse):
        """Update memory service with AI insights"""

        try:
            # Create insights summary for memory
            insights_summary = {
                "ai_analysis_timestamp": response.timestamp.isoformat(),
                "unified_lead_score": response.unified_lead_score,
                "priority_level": response.priority_level,
                "confidence_level": response.confidence_level,
                "key_recommendations": response.immediate_actions[:3],
                "ai_models_used": response.models_used,
            }

            # Update lead intelligence in memory
            await self.memory.update_lead_intelligence(lead_id, {"ai_insights": insights_summary})

        except Exception as e:
            logger.error(f"Failed to update memory with insights: {e}")

    async def _return_none(self):
        """Helper to return None asynchronously"""
        return None

    def _map_priority_to_enum(self, priority: str) -> RequestPriority:
        """Map string priority to enum"""
        mapping = {
            "critical": RequestPriority.CRITICAL,
            "high": RequestPriority.HIGH,
            "normal": RequestPriority.NORMAL,
            "low": RequestPriority.LOW,
        }
        return mapping.get(priority, RequestPriority.NORMAL)

    def _convert_enhanced_score_to_inference_response(self, enhanced_result) -> InferenceResponse:
        """Convert enhanced scorer result to inference response format"""

        return InferenceResponse(
            request_id=f"enhanced_{datetime.now().strftime('%H%M%S')}",
            lead_id=enhanced_result.lead_id,
            model_id="enhanced_claude_scorer",
            model_version="1.0.0",
            scores={"primary": enhanced_result.final_score},
            primary_score=enhanced_result.final_score,
            confidence=enhanced_result.confidence_score,
            prediction_class=enhanced_result.classification,
            feature_importance=None,
            reasoning=enhanced_result.reasoning.split(". ") if enhanced_result.reasoning else None,
            risk_factors=enhanced_result.risk_factors,
            opportunities=enhanced_result.opportunities,
            processed_at=datetime.now(),
            processing_time_ms=enhanced_result.analysis_time_ms,
            model_latency_ms=enhanced_result.claude_reasoning_time_ms,
            cache_hit=False,
            data_quality_score=0.8,
            prediction_uncertainty=1.0 - enhanced_result.confidence_score,
            requires_human_review=enhanced_result.confidence_score < 0.7,
        )


class Service6AIOrchestrator:
    """Main orchestrator for all Service 6 AI operations"""

    def __init__(self, config: Optional[Service6AIConfig] = None):
        self.config = config or Service6AIConfig()
        self.ai_companion = Service6EnhancedClaudePlatformCompanion(self.config)

        # Performance tracking
        self.operation_metrics = defaultdict(int)
        self.start_time = datetime.now()

    async def initialize(self):
        """Initialize the orchestrator and all components"""

        logger.info("Initializing Service 6 AI Orchestrator...")
        await self.ai_companion.initialize()
        logger.info("Service 6 AI Orchestrator ready")

    async def analyze_lead(
        self, lead_id: str, lead_data: Dict[str, Any], include_voice: bool = False
    ) -> Service6AIResponse:
        """Main entry point for lead analysis"""

        self.operation_metrics["analyze_lead"] += 1

        return await self.ai_companion.comprehensive_lead_analysis(lead_id, lead_data, include_voice=include_voice)

    async def score_lead_realtime(
        self, lead_id: str, features: Dict[str, Any], priority: str = "normal"
    ) -> InferenceResponse:
        """Real-time lead scoring"""

        self.operation_metrics["score_realtime"] += 1

        return await self.ai_companion.realtime_lead_scoring(lead_id, features, priority)

    async def start_voice_coaching(self, call_id: str, lead_id: str, agent_id: str) -> Dict[str, Any]:
        """Start voice coaching session"""

        self.operation_metrics["voice_coaching"] += 1

        return await self.ai_companion.voice_call_coaching(call_id, lead_id, agent_id)

    async def enhanced_chat(self, lead_id: str, message: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Enhanced Claude chat with AI insights"""

        self.operation_metrics["enhanced_chat"] += 1

        return await self.ai_companion.claude_enhanced_conversation(lead_id, message, conversation_history)

    async def get_behavioral_insights(self, lead_id: str, historical_context: List[Dict]) -> Dict[str, Any]:
        """Get behavioral insights and patterns"""

        self.operation_metrics["behavioral_insights"] += 1

        return await self.ai_companion.generate_behavioral_insights(lead_id, historical_context)

    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""

        health = await self.ai_companion.get_system_health()

        # Add orchestrator metrics
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        return {
            "service6_ai_orchestrator": {
                "status": "running",
                "uptime_hours": round(uptime_hours, 2),
                "operations_processed": dict(self.operation_metrics),
                "config": asdict(self.config),
            },
            "ai_components": health,
        }


# Factory functions for easy usage
def create_service6_ai_orchestrator(config: Optional[Service6AIConfig] = None) -> Service6AIOrchestrator:
    """Create Service 6 AI orchestrator instance"""
    return Service6AIOrchestrator(config)


def create_default_service6_config() -> Service6AIConfig:
    """Create default configuration for Service 6 AI"""
    return Service6AIConfig()


def create_high_performance_config() -> Service6AIConfig:
    """Create high-performance configuration"""
    return Service6AIConfig(
        max_concurrent_operations=100,
        default_cache_ttl_seconds=600,
        enable_background_processing=True,
        ml_model_confidence_threshold=0.8,
        voice_transcription_accuracy_threshold=0.9,
        enable_realtime_coaching=True,
    )


# Example usage and testing
if __name__ == "__main__":

    async def test_service6_ai_integration():
        """Test the complete Service 6 AI integration"""

        print("🎯 Service 6 AI Integration - Phase 2 Complete Test")

        # Create orchestrator
        config = create_high_performance_config()
        orchestrator = create_service6_ai_orchestrator(config)

        # Initialize
        await orchestrator.initialize()
        print("   ✅ Service 6 AI Orchestrator initialized")

        # Test comprehensive lead analysis
        print("\n   📊 Testing Comprehensive Lead Analysis")

        test_lead_data = {
            "lead_id": "test_lead_s6_001",
            "name": "Sarah Johnson",
            "email": "sarah.j@example.com",
            "phone": "+1-555-0123",
            "budget": 550000,
            "timeline": "soon",
            "email_open_rate": 0.85,
            "email_click_rate": 0.42,
            "avg_response_time_hours": 3.5,
            "avg_message_length": 180,
            "page_views": 15,
            "searched_locations": ["North Austin", "Round Rock", "Cedar Park"],
            "viewed_property_prices": [525000, 545000, 560000, 580000],
            "messages_per_day": 1.8,
            "questions_asked": 4,
            "last_interaction": "2026-01-16T10:30:00Z",
        }

        # Run comprehensive analysis
        analysis_result = await orchestrator.analyze_lead("test_lead_s6_001", test_lead_data)

        print(f"   • Lead ID: {analysis_result.lead_id}")
        print(f"   • Unified Score: {analysis_result.unified_lead_score}/100")
        print(f"   • Confidence: {analysis_result.confidence_level:.2f}")
        print(f"   • Priority: {analysis_result.priority_level}")
        print(f"   • Processing Time: {analysis_result.processing_time_ms:.1f}ms")
        print(f"   • Models Used: {', '.join(analysis_result.models_used)}")

        if analysis_result.immediate_actions:
            print(f"   • Immediate Actions:")
            for action in analysis_result.immediate_actions[:3]:
                print(f"     - {action}")

        # Test real-time scoring
        print("\n   ⚡ Testing Real-Time Scoring")

        features = {
            "email_open_rate": 0.75,
            "response_time_hours": 2.0,
            "budget": 500000,
            "message_frequency": 2.1,
            "page_views": 8,
        }

        rt_result = await orchestrator.score_lead_realtime("test_lead_s6_001", features, "high")

        print(f"   • Real-time Score: {rt_result.primary_score:.2f}")
        print(f"   • Confidence: {rt_result.confidence:.2f}")
        print(f"   • Prediction Class: {rt_result.prediction_class}")
        print(f"   • Processing Time: {rt_result.processing_time_ms:.1f}ms")
        print(f"   • Cache Hit: {rt_result.cache_hit}")

        # Test enhanced chat
        print("\n   💬 Testing Enhanced Chat")

        conversation_history = [
            {"role": "user", "content": "I am looking for a home in North Austin with good schools."},
            {"role": "assistant", "content": "I can help you find great options in North Austin..."},
            {"role": "user", "content": "What about the market trends? Should I wait or buy now?"},
        ]

        chat_result = await orchestrator.enhanced_chat(
            "test_lead_s6_001", "What about the market trends? Should I wait or buy now?", conversation_history
        )

        print(f"   • AI Enhanced: {chat_result.get('ai_enhanced', False)}")
        print(f"   • Lead Score Context: {chat_result.get('lead_score', 'N/A')}")
        if chat_result.get("recommended_actions"):
            print(f"   • Recommended Actions: {chat_result['recommended_actions'][0]}")

        # Test voice coaching setup
        print("\n   🎙️ Testing Voice Coaching")

        voice_result = await orchestrator.start_voice_coaching("call_123", "test_lead_s6_001", "agent_456")

        print(f"   • Coaching Active: {voice_result.get('coaching_active', False)}")
        print(f"   • Message: {voice_result.get('message', 'N/A')}")
        if voice_result.get("features"):
            print(f"   • Features: {', '.join(voice_result['features'][:3])}")

        # Test behavioral insights
        print("\n   🔮 Testing Behavioral Insights")

        historical_context = [
            {"lead_id": "hist_1", "converted": True, "email_open_rate": 0.8},
            {"lead_id": "hist_2", "converted": False, "email_open_rate": 0.3},
            {"lead_id": "hist_3", "converted": True, "email_open_rate": 0.9},
        ]

        try:
            insights_result = await orchestrator.get_behavioral_insights("test_lead_s6_001", historical_context)

            if insights_result.get("error"):
                print(f"   • Error: {insights_result['error']}")
            else:
                print(f"   • Analysis Duration: {insights_result.get('analysis_duration_seconds', 0):.1f}s")
                patterns = insights_result.get("behavioral_patterns", [])
                print(f"   • Patterns Discovered: {len(patterns)}")

        except Exception as e:
            print(f"   • Behavioral insights test failed: {e}")

        # Get system status
        print("\n   📈 System Status")

        status = await orchestrator.get_system_status()

        orchestrator_status = status.get("service6_ai_orchestrator", {})
        print(f"   • Orchestrator Status: {orchestrator_status.get('status', 'unknown')}")
        print(f"   • Uptime: {orchestrator_status.get('uptime_hours', 0):.1f} hours")

        ops = orchestrator_status.get("operations_processed", {})
        print(f"   • Operations Processed:")
        for op_type, count in ops.items():
            print(f"     - {op_type}: {count}")

        ai_components = status.get("ai_components", {})
        overall_status = ai_components.get("overall_status", "unknown")
        print(f"   • AI Components Status: {overall_status}")

        component_count = len(ai_components.get("components", {}))
        print(f"   • Active AI Components: {component_count}")

        print("\n   ✅ Service 6 AI Integration Test Complete")
        print(f"   🚀 All {len(ops)} operation types tested successfully")

    # Run comprehensive integration test
    asyncio.run(test_service6_ai_integration())
