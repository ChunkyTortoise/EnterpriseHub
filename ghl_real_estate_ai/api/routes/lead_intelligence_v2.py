"""
Lead Intelligence API Routes v2 - Track A Phase 1 Endpoints

Enhanced AI Lead Generation and Lead Scoring endpoints:
- Enhanced lead scoring analysis beyond basic FRS/PCS
- Lead source quality analysis and optimization
- Lead generation performance analytics
- AI-powered optimization recommendations
- Real-time lead intelligence insights

Follows established architecture patterns:
- FastAPI route structure with /api/v1 prefix
- Multi-tenant isolation via location_id
- Pydantic models for validation
- Event publishing and caching integration
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Path, BackgroundTasks
from pydantic import BaseModel, Field
import logging

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.enhanced_lead_scoring import get_enhanced_lead_scoring
from ghl_real_estate_ai.services.ai_lead_generation_engine import get_ai_lead_generation_engine
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/lead-intelligence", tags=["Lead Intelligence v2"])

# Request/Response Models

class EnhancedLeadScoreRequest(BaseModel):
    """Request for enhanced lead scoring analysis."""
    contact_id: str = Field(..., description="Contact/Lead identifier")
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    source_info: Optional[Dict[str, Any]] = Field(None, description="UTM and source data")
    attribution_data: Optional[Dict[str, Any]] = Field(None, description="Attribution touchpoints")

class LeadGenerationAnalysisRequest(BaseModel):
    """Request for lead generation performance analysis."""
    analysis_period_days: int = Field(30, ge=7, le=365, description="Analysis period")
    include_forecasts: bool = Field(True, description="Include predictive forecasts")

class StandardResponse(BaseModel):
    """Standard API response format."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    error: Optional[str] = None

# API Endpoints

@router.post("/{location_id}/enhanced-scoring")
async def enhanced_lead_scoring_analysis(
    location_id: str = Path(..., description="Location/tenant identifier"),
    request: EnhancedLeadScoreRequest = ...,
    background_tasks: BackgroundTasks = ...
) -> StandardResponse:
    """
    Enhanced AI lead scoring analysis.

    Provides comprehensive scoring including:
    - Source quality analysis
    - Behavioral engagement patterns
    - ML-powered conversion prediction
    - Personalized action recommendations
    """
    start_time = datetime.now()

    try:
        logger.info(f"Enhanced scoring request: {request.contact_id} in {location_id}")

        # Get scoring service
        scoring_service = get_enhanced_lead_scoring()

        # Perform comprehensive analysis
        enhanced_score = await scoring_service.analyze_lead_comprehensive(
            contact_id=request.contact_id,
            location_id=location_id,
            conversation_history=request.conversation_history,
            source_info=request.source_info,
            attribution_data=request.attribution_data
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format response
        response_data = {
            'lead_id': enhanced_score.lead_id,
            'overall_score': enhanced_score.overall_score,
            'component_scores': {
                'source_quality': enhanced_score.source_quality_score,
                'behavioral_engagement': enhanced_score.behavioral_engagement_score,
                'intent_clarity': enhanced_score.intent_clarity_score,
                'conversion_readiness': enhanced_score.conversion_readiness_score
            },
            'ml_insights': {
                'closing_probability': enhanced_score.closing_probability,
                'confidence': enhanced_score.ml_confidence,
                'risk_factors': enhanced_score.risk_factors,
                'positive_signals': enhanced_score.positive_signals
            },
            'recommendations': enhanced_score.next_action_recommendations,
            'confidence_level': enhanced_score.confidence_level,
            'scoring_timestamp': enhanced_score.scoring_timestamp.isoformat()
        }

        logger.info(f"Enhanced scoring complete: {enhanced_score.overall_score:.1f} [{processing_time:.1f}ms]")

        return StandardResponse(
            success=True,
            data=response_data,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Enhanced scoring failed: {e}")

        return StandardResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@router.post("/{location_id}/generation-analysis")
async def lead_generation_performance_analysis(
    location_id: str = Path(..., description="Location/tenant identifier"),
    request: LeadGenerationAnalysisRequest = ...
) -> StandardResponse:
    """
    Lead generation performance analysis.

    Provides strategic intelligence including:
    - Channel performance with ROI metrics
    - Source quality assessment
    - Optimization recommendations
    - Predictive forecasts
    """
    start_time = datetime.now()

    try:
        logger.info(f"Generation analysis request for {location_id} ({request.analysis_period_days}d)")

        # Get generation engine
        generation_engine = get_ai_lead_generation_engine()

        # Perform analysis
        insights = await generation_engine.analyze_lead_generation_performance(
            location_id=location_id,
            analysis_period_days=request.analysis_period_days
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format response
        response_data = {
            'analysis_id': insights.analysis_id,
            'performance_overview': {
                'grade': insights.overall_performance_grade,
                'monthly_leads': insights.total_monthly_leads,
                'monthly_conversions': insights.total_monthly_conversions,
                'overall_roi': insights.overall_roi
            },
            'channel_performance': insights.channel_performance,
            'top_channels': [ch.value for ch in insights.top_performing_channels],
            'underperforming_channels': [ch.value for ch in insights.underperforming_channels],
            'immediate_opportunities': [
                {
                    'title': rec.title,
                    'description': rec.description,
                    'channel': rec.channel.value,
                    'priority': rec.priority.value,
                    'confidence': rec.confidence_score,
                    'expected_impact': rec.expected_impact
                }
                for rec in insights.immediate_opportunities
            ],
            'forecasts': insights.forecasted_leads if request.include_forecasts else None,
            'alerts': {
                'performance': insights.performance_alerts,
                'budget': insights.budget_optimization_alerts
            },
            'confidence_level': insights.confidence_level,
            'generated_at': insights.generated_at.isoformat()
        }

        logger.info(f"Generation analysis complete: Grade {insights.overall_performance_grade} [{processing_time:.1f}ms]")

        return StandardResponse(
            success=True,
            data=response_data,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Generation analysis failed: {e}")

        return StandardResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@router.get("/{location_id}/lead-score-history/{contact_id}")
async def get_lead_scoring_history(
    location_id: str = Path(..., description="Location/tenant identifier"),
    contact_id: str = Path(..., description="Contact identifier"),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back")
) -> StandardResponse:
    """Get historical lead scoring data for trend analysis."""
    start_time = datetime.now()

    try:
        logger.info(f"Score history request: {contact_id} in {location_id} ({days_back}d)")

        # Get scoring service
        scoring_service = get_enhanced_lead_scoring()

        # Get historical data
        history = await scoring_service.get_lead_score_history(
            contact_id=contact_id,
            location_id=location_id,
            days_back=days_back
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        response_data = {
            'contact_id': contact_id,
            'location_id': location_id,
            'period_days': days_back,
            'data_points': len(history),
            'history': history
        }

        logger.info(f"Score history retrieved: {len(history)} data points [{processing_time:.1f}ms]")

        return StandardResponse(
            success=True,
            data=response_data,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Score history failed: {e}")

        return StandardResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@router.get("/{location_id}/bulk-score")
async def bulk_lead_scoring(
    location_id: str = Path(..., description="Location/tenant identifier"),
    contact_ids: str = Query(..., description="Comma-separated contact IDs"),
    batch_size: int = Query(10, ge=1, le=20, description="Batch size")
) -> StandardResponse:
    """Bulk lead scoring for multiple contacts."""
    start_time = datetime.now()

    try:
        # Parse contact IDs
        contact_id_list = [cid.strip() for cid in contact_ids.split(',') if cid.strip()]

        if len(contact_id_list) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 contacts per request")

        logger.info(f"Bulk scoring request: {len(contact_id_list)} contacts in {location_id}")

        # Get scoring service
        scoring_service = get_enhanced_lead_scoring()

        # Perform bulk scoring
        results = await scoring_service.bulk_score_leads(
            contact_ids=contact_id_list,
            location_id=location_id,
            batch_size=batch_size
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format results
        formatted_results = {}
        for contact_id, score in results.items():
            if isinstance(score, Exception):
                formatted_results[contact_id] = {
                    'success': False,
                    'error': str(score)
                }
            else:
                formatted_results[contact_id] = {
                    'success': True,
                    'overall_score': score.overall_score,
                    'confidence_level': score.confidence_level,
                    'scoring_timestamp': score.scoring_timestamp.isoformat()
                }

        response_data = {
            'location_id': location_id,
            'total_requested': len(contact_id_list),
            'total_processed': len(results),
            'results': formatted_results
        }

        logger.info(f"Bulk scoring complete: {len(results)}/{len(contact_id_list)} processed [{processing_time:.1f}ms]")

        return StandardResponse(
            success=True,
            data=response_data,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Bulk scoring failed: {e}")

        return StandardResponse(
            success=False,
            processing_time_ms=processing_time,
            error=str(e)
        )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for Lead Intelligence v2 services."""
    try:
        # Test service availability
        scoring_service = get_enhanced_lead_scoring()
        generation_engine = get_ai_lead_generation_engine()

        # Test cache
        cache = get_cache_service()
        test_key = f"health_check:{datetime.now().timestamp()}"
        await cache.set(test_key, "test", 30)
        await cache.delete(test_key)

        return {
            'status': 'healthy',
            'services': {
                'enhanced_lead_scoring': 'available',
                'ai_lead_generation': 'available',
                'cache_service': 'available'
            },
            'version': 'v2.0.0',
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }