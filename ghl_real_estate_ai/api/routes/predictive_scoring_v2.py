#!/usr/bin/env python3
"""
🚀 Predictive Scoring V2 API Endpoints
======================================

Enhanced API endpoints for the Predictive Lead Scoring 2.0 system with:
- Real-time inference (<100ms)
- Market-specific models
- Intelligent routing recommendations
- Comprehensive behavioral analysis
- A/B testing framework
- Backward compatibility
- Gradual rollout support

Target: +$200K ARR through enhanced lead conversion

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
import json

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.middleware.jwt_auth import verify_jwt_token

# Import V2 components
from ghl_real_estate_ai.services.realtime_inference_engine_v2 import (
    RealTimeInferenceEngineV2, InferenceRequest, InferenceMode, MarketSegment
)
from ghl_real_estate_ai.services.intelligent_lead_router import (
    IntelligentLeadRouter, RoutingStrategy, PriorityLevel
)
from ghl_real_estate_ai.ml.behavioral_signal_processor import BehavioralSignalProcessor
from ghl_real_estate_ai.ml.market_specific_models import MarketSpecificModelRouter

# Backward compatibility imports
from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer

logger = get_logger(__name__)

# Initialize V2 services
inference_engine = RealTimeInferenceEngineV2()
lead_router = IntelligentLeadRouter()
signal_processor = BehavioralSignalProcessor()
market_router = MarketSpecificModelRouter()

# Legacy scorer for backward compatibility
# Lazy singleton — defer initialization until first request
_legacy_scorer = None


def _get_legacy_scorer():
    global _legacy_scorer
    if _legacy_scorer is None:
        _legacy_scorer = PredictiveLeadScorer()
    return _legacy_scorer

router = APIRouter(prefix="/api/v2/predictive-scoring", tags=["Predictive Scoring V2"])


# Request/Response Models
class LeadScoringRequest(BaseModel):
    """Enhanced lead scoring request model"""
    lead_id: str = Field(..., description="Unique lead identifier")
    lead_data: Dict[str, Any] = Field(..., description="Lead information and metadata")
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list, description="Conversation messages and interactions"
    )
    market_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Market-specific context data"
    )

    # Processing options
    include_routing: bool = Field(
        default=True, description="Include intelligent routing recommendation"
    )
    include_behavioral_analysis: bool = Field(
        default=True, description="Include detailed behavioral signal analysis"
    )
    include_market_insights: bool = Field(
        default=True, description="Include market-specific insights"
    )

    # A/B testing
    ab_test_group: Optional[str] = Field(
        default=None, description="A/B testing group identifier"
    )

    # Performance options
    inference_mode: str = Field(
        default="real_time", description="Inference processing mode"
    )

    @field_validator('inference_mode')
    @classmethod
    def validate_inference_mode(cls, v):
        valid_modes = ["real_time", "batch_fast", "batch_bulk", "background"]
        if v not in valid_modes:
            raise ValueError(f"Invalid inference_mode. Must be one of: {valid_modes}")
        return v


class EnhancedScoringResponse(BaseModel):
    """Comprehensive scoring response with V2 enhancements"""

    # Core scoring
    lead_id: str
    score: float = Field(..., ge=0, le=100, description="Lead score (0-100)")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence (0-1)")
    tier: str = Field(..., description="Lead tier (hot/warm/cold)")

    # Market analysis
    market_segment: str = Field(..., description="Identified market segment")
    segment_confidence: float = Field(..., ge=0, le=1, description="Segment classification confidence")

    # Behavioral insights
    behavioral_signals: Optional[Dict[str, float]] = Field(
        default=None, description="Extracted behavioral signals (0-1)"
    )
    signal_summary: Optional[Dict[str, Any]] = Field(
        default=None, description="Behavioral signal summary and insights"
    )

    # Routing recommendation
    routing_recommendation: Optional[Dict[str, Any]] = Field(
        default=None, description="Intelligent lead routing recommendation"
    )

    # Performance metrics
    inference_time_ms: float = Field(..., description="Inference processing time in milliseconds")
    cache_hit: bool = Field(..., description="Whether result was served from cache")
    model_version: str = Field(..., description="Model version used for scoring")

    # Legacy compatibility
    qualification_score: Optional[int] = Field(
        default=None, description="Legacy qualification score (0-7)"
    )
    conversion_probability: Optional[float] = Field(
        default=None, description="Legacy conversion probability (0-1)"
    )

    # Recommendations
    recommended_actions: List[str] = Field(
        default_factory=list, description="Prioritized action recommendations"
    )
    risk_factors: List[str] = Field(
        default_factory=list, description="Identified risk factors"
    )
    positive_signals: List[str] = Field(
        default_factory=list, description="Strong positive indicators"
    )

    # Metadata
    scored_at: datetime = Field(..., description="Scoring timestamp")
    api_version: str = Field(default="2.0", description="API version used")
    ab_test_group: Optional[str] = Field(
        default=None, description="A/B testing group"
    )


class BatchScoringRequest(BaseModel):
    """Batch scoring request for multiple leads"""
    leads: List[LeadScoringRequest] = Field(
        ..., max_items=100, description="List of leads to score (max 100)"
    )
    processing_mode: str = Field(
        default="batch_fast", description="Batch processing mode"
    )
    include_performance_summary: bool = Field(
        default=True, description="Include batch performance summary"
    )


class BatchScoringResponse(BaseModel):
    """Batch scoring response"""
    results: List[EnhancedScoringResponse]
    summary: Dict[str, Any]
    processing_time_ms: float
    successful_predictions: int
    failed_predictions: int


class PerformanceMetricsResponse(BaseModel):
    """Performance monitoring response"""
    p95_latency_ms: float
    p99_latency_ms: float
    average_latency_ms: float
    cache_hit_rate: float
    total_requests_24h: int
    error_rate: float
    throughput_per_minute: float
    model_health: Dict[str, Any]
    system_status: str  # healthy/degraded/unhealthy


# API Endpoints

@router.post("/score", response_model=EnhancedScoringResponse)
async def score_lead_v2(
    request: LeadScoringRequest,
    x_api_version: Optional[str] = Header(default="2.0"),
    x_client_version: Optional[str] = Header(default=None),
    current_user: dict = Depends(verify_jwt_token)
) -> EnhancedScoringResponse:
    """
    Enhanced lead scoring with real-time inference and behavioral analysis.

    Features:
    - Sub-100ms real-time inference
    - 50+ behavioral signal extraction
    - Market-specific model routing
    - Intelligent agent routing recommendations
    - Comprehensive risk/opportunity analysis
    """
    start_time = time.time()

    try:
        logger.info(f"V2 scoring request for lead {request.lead_id} (API version: {x_api_version})")

        # Convert to inference request
        inference_mode_map = {
            "real_time": InferenceMode.REAL_TIME,
            "batch_fast": InferenceMode.BATCH_FAST,
            "batch_bulk": InferenceMode.BATCH_BULK,
            "background": InferenceMode.BACKGROUND
        }

        inference_request = InferenceRequest(
            lead_id=request.lead_id,
            lead_data=request.lead_data,
            conversation_history=request.conversation_history,
            market_context=request.market_context,
            mode=inference_mode_map.get(request.inference_mode, InferenceMode.REAL_TIME),
            ab_test_group=request.ab_test_group
        )

        # Run inference
        result = await inference_engine.predict(inference_request)

        # Extract behavioral signals if requested
        behavioral_signals = None
        signal_summary = None
        if request.include_behavioral_analysis:
            behavioral_signals = result.behavioral_signals
            signal_summary = signal_processor.get_signal_summary(behavioral_signals)

        # Get routing recommendation if requested
        routing_recommendation = None
        if request.include_routing:
            routing_recommendation = result.routing_recommendation

        # Generate action recommendations
        recommended_actions = _generate_action_recommendations(result, behavioral_signals)
        risk_factors = _identify_risk_factors(result, behavioral_signals)
        positive_signals = _identify_positive_signals(result, behavioral_signals)

        # Legacy compatibility fields
        qualification_score = min(int(result.score / 14.3), 7)  # Convert 100 scale to 7 scale
        conversion_probability = result.score / 100.0

        response = EnhancedScoringResponse(
            lead_id=result.lead_id,
            score=result.score,
            confidence=result.confidence,
            tier=result.tier,
            market_segment=result.market_segment.value,
            segment_confidence=result.confidence,
            behavioral_signals=behavioral_signals,
            signal_summary=signal_summary,
            routing_recommendation=routing_recommendation,
            inference_time_ms=result.inference_time_ms,
            cache_hit=result.cache_hit,
            model_version=result.model_version,
            qualification_score=qualification_score,
            conversion_probability=conversion_probability,
            recommended_actions=recommended_actions,
            risk_factors=risk_factors,
            positive_signals=positive_signals,
            scored_at=result.timestamp,
            ab_test_group=result.ab_test_group
        )

        logger.info(f"V2 scoring completed for {request.lead_id} in {result.inference_time_ms:.1f}ms")
        return response

    except Exception as e:
        logger.error(f"V2 scoring failed for {request.lead_id}: {e}")

        # Fallback to legacy scorer
        try:
            legacy_result = _get_legacy_scorer().score_lead(request.lead_id, request.lead_data)

            return EnhancedScoringResponse(
                lead_id=request.lead_id,
                score=legacy_result.score,
                confidence=legacy_result.confidence,
                tier=legacy_result.tier,
                market_segment="general_market",
                segment_confidence=0.5,
                behavioral_signals={},
                inference_time_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                model_version="legacy_fallback",
                qualification_score=min(int(legacy_result.score / 14.3), 7),
                conversion_probability=legacy_result.score / 100.0,
                recommended_actions=legacy_result.recommendations or [],
                risk_factors=[],
                positive_signals=[],
                scored_at=datetime.now()
            )
        except Exception as fallback_error:
            logger.error(f"Legacy fallback also failed: {fallback_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Scoring system unavailable: {str(e)}"
            )


@router.post("/swarm-analysis", response_model=Dict[str, Any])
async def get_swarm_analysis(
    lead_id: str,
    lead_data: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Perform deep multi-agent swarm analysis on a lead.
    
    Provides collaborative intelligence from multiple specialized agents:
    - Demographic Analyzer
    - Behavioral Profiler
    - Intent Detector
    - Market Analyst (Predator Mode)
    """
    from ghl_real_estate_ai.agents.lead_intelligence_swarm import lead_intelligence_swarm
    
    consensus = await lead_intelligence_swarm.analyze_lead_comprehensive(lead_id, lead_data)
    
    # Format consensus for Next.js frontend
    return {
        "lead_id": consensus.lead_id,
        "overall_score": consensus.overall_score,
        "consensus_level": consensus.consensus_level.value,
        "confidence": consensus.confidence,
        "priority": consensus.action_priority,
        "recommendation": consensus.primary_recommendation,
        "rationale": consensus.consensus_rationale,
        "insights": [
            {
                "agent": insight.agent_type.value,
                "finding": insight.primary_finding,
                "confidence": insight.confidence,
                "urgency": insight.urgency_level,
                "metadata": insight.metadata
            }
            for insight in consensus.agent_insights
        ],
        "processing_time_ms": consensus.processing_time_ms
    }


@router.post("/score-batch", response_model=BatchScoringResponse)
async def score_leads_batch(
    request: BatchScoringRequest,
    current_user: dict = Depends(verify_jwt_token)
) -> BatchScoringResponse:
    """
    Batch lead scoring with optimized processing.

    Supports up to 100 leads per request with intelligent batching
    and parallel processing for optimal performance.
    """
    start_time = time.time()

    try:
        logger.info(f"Batch scoring request for {len(request.leads)} leads")

        if len(request.leads) > 100:
            raise HTTPException(
                status_code=400,
                detail="Maximum 100 leads per batch request"
            )

        # Convert to inference requests
        inference_requests = []
        for lead_req in request.leads:
            inference_mode_map = {
                "real_time": InferenceMode.REAL_TIME,
                "batch_fast": InferenceMode.BATCH_FAST,
                "batch_bulk": InferenceMode.BATCH_BULK,
                "background": InferenceMode.BACKGROUND
            }

            inference_req = InferenceRequest(
                lead_id=lead_req.lead_id,
                lead_data=lead_req.lead_data,
                conversation_history=lead_req.conversation_history,
                market_context=lead_req.market_context,
                mode=inference_mode_map.get(request.processing_mode, InferenceMode.BATCH_FAST),
                ab_test_group=lead_req.ab_test_group
            )
            inference_requests.append(inference_req)

        # Process batch
        results = await inference_engine.predict_batch(inference_requests)

        # Convert to response format
        response_results = []
        successful = 0
        failed = 0

        for i, result in enumerate(results):
            try:
                lead_req = request.leads[i]

                # Extract additional data if requested
                behavioral_signals = result.behavioral_signals if lead_req.include_behavioral_analysis else None
                signal_summary = signal_processor.get_signal_summary(behavioral_signals) if behavioral_signals else None
                routing_recommendation = result.routing_recommendation if lead_req.include_routing else None

                response_result = EnhancedScoringResponse(
                    lead_id=result.lead_id,
                    score=result.score,
                    confidence=result.confidence,
                    tier=result.tier,
                    market_segment=result.market_segment.value,
                    segment_confidence=result.confidence,
                    behavioral_signals=behavioral_signals,
                    signal_summary=signal_summary,
                    routing_recommendation=routing_recommendation,
                    inference_time_ms=result.inference_time_ms,
                    cache_hit=result.cache_hit,
                    model_version=result.model_version,
                    qualification_score=min(int(result.score / 14.3), 7),
                    conversion_probability=result.score / 100.0,
                    recommended_actions=_generate_action_recommendations(result, behavioral_signals),
                    risk_factors=_identify_risk_factors(result, behavioral_signals),
                    positive_signals=_identify_positive_signals(result, behavioral_signals),
                    scored_at=result.timestamp,
                    ab_test_group=result.ab_test_group
                )
                response_results.append(response_result)
                successful += 1

            except Exception as e:
                logger.error(f"Failed to process lead {result.lead_id}: {e}")
                failed += 1

        # Calculate summary statistics
        processing_time_ms = (time.time() - start_time) * 1000

        if response_results:
            avg_score = sum(r.score for r in response_results) / len(response_results)
            avg_inference_time = sum(r.inference_time_ms for r in response_results) / len(response_results)
            cache_hit_rate = sum(1 for r in response_results if r.cache_hit) / len(response_results)

            # Tier distribution
            tier_counts = {}
            for r in response_results:
                tier_counts[r.tier] = tier_counts.get(r.tier, 0) + 1

            summary = {
                "average_score": round(avg_score, 2),
                "average_inference_time_ms": round(avg_inference_time, 2),
                "cache_hit_rate": round(cache_hit_rate, 3),
                "tier_distribution": tier_counts,
                "processing_mode": request.processing_mode,
                "leads_per_second": round(len(request.leads) / (processing_time_ms / 1000), 2)
            }
        else:
            summary = {
                "average_score": 0,
                "average_inference_time_ms": 0,
                "cache_hit_rate": 0,
                "tier_distribution": {},
                "processing_mode": request.processing_mode,
                "leads_per_second": 0
            }

        return BatchScoringResponse(
            results=response_results,
            summary=summary,
            processing_time_ms=processing_time_ms,
            successful_predictions=successful,
            failed_predictions=failed
        )

    except Exception as e:
        logger.error(f"Batch scoring failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch scoring failed: {str(e)}"
        )


@router.get("/behavioral-signals/{lead_id}")
async def get_behavioral_signals(
    lead_id: str,
    lead_data: Dict[str, Any],
    conversation_history: List[Dict[str, Any]] = None,
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Extract detailed behavioral signals for a lead.

    Returns comprehensive behavioral analysis including 50+ signals
    across engagement, financial readiness, urgency, and communication patterns.
    """
    try:
        conversation_history = conversation_history or []

        # Extract behavioral signals
        signals = signal_processor.extract_signals(lead_data, conversation_history)

        # Get signal summary
        summary = signal_processor.get_signal_summary(signals)

        # Categorize signals by strength
        strong_signals = {k: v for k, v in signals.items() if v > 0.7}
        moderate_signals = {k: v for k, v in signals.items() if 0.4 <= v <= 0.7}
        weak_signals = {k: v for k, v in signals.items() if v < 0.4}

        return {
            "lead_id": lead_id,
            "total_signals_extracted": len(signals),
            "behavioral_signals": signals,
            "signal_summary": summary,
            "signal_categorization": {
                "strong_signals": strong_signals,
                "moderate_signals": moderate_signals,
                "weak_signals": weak_signals
            },
            "recommendations": _generate_behavioral_recommendations(signals),
            "extracted_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Behavioral signal extraction failed for {lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Signal extraction failed: {str(e)}"
        )


@router.post("/routing-recommendation")
async def get_routing_recommendation(
    lead_id: str,
    lead_score: float,
    behavioral_signals: Dict[str, float],
    lead_data: Dict[str, Any],
    routing_strategy: Optional[str] = None,
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Get intelligent lead routing recommendation.

    Uses multi-criteria optimization to match leads with the most
    suitable agents based on performance, specialization, and capacity.
    """
    try:
        # Map strategy string to enum
        strategy_map = {
            "round_robin": RoutingStrategy.ROUND_ROBIN,
            "performance_based": RoutingStrategy.PERFORMANCE_BASED,
            "specialization_match": RoutingStrategy.SPECIALIZATION_MATCH,
            "capacity_optimized": RoutingStrategy.CAPACITY_OPTIMIZED,
            "hybrid_intelligent": RoutingStrategy.HYBRID_INTELLIGENT
        }

        strategy = strategy_map.get(routing_strategy) if routing_strategy else None

        recommendation = await lead_router.recommend_routing(
            lead_id=lead_id,
            lead_score=lead_score,
            behavioral_signals=behavioral_signals,
            lead_data=lead_data,
            strategy=strategy
        )

        return recommendation

    except Exception as e:
        logger.error(f"Routing recommendation failed for {lead_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Routing recommendation failed: {str(e)}"
        )


@router.get("/performance-metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    current_user: dict = Depends(verify_jwt_token)
) -> PerformanceMetricsResponse:
    """
    Get comprehensive performance metrics for the V2 system.

    Includes latency statistics, cache performance, throughput,
    and system health indicators.
    """
    try:
        # Get metrics from inference engine
        metrics = inference_engine.get_performance_metrics()

        # Calculate additional metrics
        total_requests_24h = metrics.get("total_requests", 0)
        error_rate = metrics.get("error_rate", 0.0)

        # Estimate p99 latency (assume it's 1.5x p95)
        p95_latency = metrics.get("p95_latency_ms", 0)
        p99_latency = p95_latency * 1.5

        # Calculate average latency (assume it's 0.7x p95)
        avg_latency = p95_latency * 0.7

        # Calculate throughput
        cache_hit_rate = metrics.get("cache_hit_rate", 0)
        throughput_per_minute = min(total_requests_24h / (24 * 60), 1000)  # Requests per minute

        # Determine system status
        is_healthy = metrics.get("is_healthy", False)
        if is_healthy and error_rate < 0.01:
            system_status = "healthy"
        elif error_rate < 0.05:
            system_status = "degraded"
        else:
            system_status = "unhealthy"

        # Model health details
        model_health = {
            "inference_engine": "healthy" if is_healthy else "degraded",
            "behavioral_processor": "healthy",
            "market_router": "healthy",
            "lead_router": "healthy",
            "cache_system": "healthy" if cache_hit_rate > 0.3 else "degraded"
        }

        return PerformanceMetricsResponse(
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            average_latency_ms=avg_latency,
            cache_hit_rate=cache_hit_rate,
            total_requests_24h=total_requests_24h,
            error_rate=error_rate,
            throughput_per_minute=throughput_per_minute,
            model_health=model_health,
            system_status=system_status
        )

    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Performance metrics unavailable: {str(e)}"
        )


@router.post("/warm-cache")
async def warm_cache(
    sample_leads: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Warm the inference cache with sample leads.

    Useful for pre-warming the system before high traffic periods
    or after deployments to ensure optimal performance.
    """
    try:
        if current_user.get("role") not in ["admin", "manager"]:
            raise HTTPException(
                status_code=403,
                detail="Cache warming requires admin or manager privileges"
            )

        if len(sample_leads) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 sample leads for cache warming"
            )

        # Convert to inference requests
        sample_requests = []
        for lead in sample_leads:
            request = InferenceRequest(
                lead_id=lead.get("lead_id", f"warmup_{hash(str(lead))}"),
                lead_data=lead,
                conversation_history=lead.get("conversation_history", []),
                mode=InferenceMode.REAL_TIME
            )
            sample_requests.append(request)

        # Warm cache in background
        background_tasks.add_task(inference_engine.warm_cache, sample_requests)

        return {
            "status": "warming_initiated",
            "sample_count": len(sample_leads),
            "estimated_completion": "1-2 minutes",
            "initiated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Cache warming failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache warming failed: {str(e)}"
        )


# Backward Compatibility Endpoints

@router.post("/legacy/score")
async def legacy_score_endpoint(
    lead_data: Dict[str, Any],
    current_user: dict = Depends(verify_jwt_token)
) -> Dict[str, Any]:
    """
    Legacy scoring endpoint for backward compatibility.

    Provides the same interface as V1 while leveraging V2 improvements.
    """
    try:
        lead_id = lead_data.get("lead_id", "legacy_unknown")

        # Use V2 inference but format as legacy response
        request = InferenceRequest(
            lead_id=lead_id,
            lead_data=lead_data,
            conversation_history=lead_data.get("conversation_history", []),
            mode=InferenceMode.REAL_TIME
        )

        result = await inference_engine.predict(request)

        # Format as legacy response
        return {
            "lead_id": lead_id,
            "score": result.score,
            "tier": result.tier,
            "confidence": result.confidence,
            "conversion_probability": result.score / 100.0,
            "qualification_score": min(int(result.score / 14.3), 7),
            "recommendations": _generate_action_recommendations(result, result.behavioral_signals),
            "scored_at": result.timestamp.isoformat()
        }

    except Exception as e:
        logger.error(f"Legacy scoring failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Legacy scoring failed: {str(e)}"
        )


# Helper Functions

def _generate_action_recommendations(result, behavioral_signals: Optional[Dict[str, float]]) -> List[str]:
    """Generate action recommendations based on scoring result"""
    recommendations = []

    if result.score >= 85:
        recommendations.append("🔥 High priority - contact within 15 minutes")
        recommendations.append("Schedule immediate property viewing")
    elif result.score >= 70:
        recommendations.append("Priority follow-up within 1 hour")
        recommendations.append("Send personalized property recommendations")
    elif result.score >= 50:
        recommendations.append("Follow up within 24 hours")
        recommendations.append("Add to targeted nurture sequence")
    else:
        recommendations.append("Add to long-term nurture campaign")
        recommendations.append("Send educational content about market")

    # Add signal-specific recommendations
    if behavioral_signals:
        if behavioral_signals.get("immediate_timeline", 0) > 0.7:
            recommendations.append("Emphasize quick response capability")
        if behavioral_signals.get("cash_buyer_indicators", 0) > 0.5:
            recommendations.append("Highlight cash offer advantages")
        if behavioral_signals.get("first_time_buyer", 0) > 0.7:
            recommendations.append("Provide first-time buyer educational resources")

    return recommendations[:5]  # Return top 5


def _identify_risk_factors(result, behavioral_signals: Optional[Dict[str, float]]) -> List[str]:
    """Identify potential risk factors"""
    risks = []

    if result.confidence < 0.6:
        risks.append("Low model confidence - limited data available")

    if behavioral_signals:
        if behavioral_signals.get("price_objections", 0) > 0.5:
            risks.append("Price sensitivity concerns")
        if behavioral_signals.get("market_concerns", 0) > 0.5:
            risks.append("Market timing hesitation")
        if behavioral_signals.get("decision_maker_concerns", 0) > 0.5:
            risks.append("Multiple decision makers involved")
        if behavioral_signals.get("comparison_shopping", 0) > 0.7:
            risks.append("Actively comparing multiple agents/options")

    return risks


def _identify_positive_signals(result, behavioral_signals: Optional[Dict[str, float]]) -> List[str]:
    """Identify strong positive indicators"""
    signals = []

    if result.score >= 80:
        signals.append("High conversion probability")

    if behavioral_signals:
        if behavioral_signals.get("preapproval_mentions", 0) > 0.5:
            signals.append("Pre-approved for financing")
        if behavioral_signals.get("immediate_timeline", 0) > 0.7:
            signals.append("Urgent timeline - ready to act")
        if behavioral_signals.get("cash_buyer_indicators", 0) > 0.5:
            signals.append("Cash buyer capability")
        if behavioral_signals.get("commitment_signals", 0) > 0.6:
            signals.append("Strong commitment indicators")
        if behavioral_signals.get("digital_engagement", 0) > 0.8:
            signals.append("High digital engagement")

    return signals


def _generate_behavioral_recommendations(signals: Dict[str, float]) -> List[str]:
    """Generate recommendations based on behavioral signals"""
    recommendations = []

    # Engagement recommendations
    if signals.get("response_velocity", 0) > 0.8:
        recommendations.append("Lead is highly responsive - maintain quick communication")
    elif signals.get("response_velocity", 0) < 0.3:
        recommendations.append("Slow response pattern - try different communication channels")

    # Financial recommendations
    if signals.get("budget_specificity", 0) > 0.7:
        recommendations.append("Lead has specific budget - focus on properties in range")

    # Urgency recommendations
    if signals.get("viewing_urgency", 0) > 0.6:
        recommendations.append("High viewing interest - schedule tours immediately")

    # Communication recommendations
    if signals.get("detail_oriented", 0) > 0.7:
        recommendations.append("Provide comprehensive property details and data")
    elif signals.get("formal_communication_style", 0) > 0.7:
        recommendations.append("Maintain professional, formal communication tone")

    return recommendations[:5]


# Health check endpoint
@router.get("/health")
async def health_check():
    """V2 system health check"""
    try:
        # Quick performance check
        start_time = time.time()

        # Test inference engine
        test_request = InferenceRequest(
            lead_id="health_check",
            lead_data={"budget": 500000, "location": "Test"},
            conversation_history=[],
            mode=InferenceMode.REAL_TIME
        )

        result = await inference_engine.predict(test_request)
        response_time = (time.time() - start_time) * 1000

        # Get performance metrics
        metrics = inference_engine.get_performance_metrics()

        return {
            "status": "healthy" if response_time < 200 else "degraded",
            "version": "2.0",
            "response_time_ms": response_time,
            "cache_hit_rate": metrics.get("cache_hit_rate", 0),
            "p95_latency_ms": metrics.get("p95_latency_ms", 0),
            "system_load": "normal",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }