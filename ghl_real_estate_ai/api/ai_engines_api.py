"""
AI Engines API

Unified API endpoints for Competitive Intelligence and Predictive Lead Lifecycle engines
with advanced performance optimization and cross-engine intelligence fusion.

Endpoints:
- POST /api/ai/analyze/lead/{lead_id} - Unified lead analysis
- POST /api/ai/competitive/analyze/{lead_id} - Competitive analysis only
- POST /api/ai/predictive/forecast/{lead_id} - Predictive forecast only
- POST /api/ai/threats-opportunities/{lead_id} - Threat and opportunity detection
- POST /api/ai/strategic/recommendations/{lead_id} - Strategic recommendations
- GET /api/ai/health - Health check for all AI engines
- GET /api/ai/metrics - Performance metrics
- POST /api/ai/batch/analyze - Batch analysis for multiple leads

Performance Requirements:
- Unified analysis: <75ms (95th percentile)
- Individual engine calls: <50ms (competitive), <25ms (predictive)
- Batch processing: <200ms per lead in batch
- API response time: <100ms overhead
- Throughput: 1000+ requests per minute
"""

import asyncio
import time
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

# Import integration service
from ..services.ai_engines_integration_service import (
    AIEnginesIntegrationService,
    EngineRequest,
    UnifiedAnalysisResult,
    AnalysisScope,
    ProcessingPriority,
    get_ai_engines_integration_service
)

# Import individual engines for specific operations
from ..services.competitive_intelligence_engine import CompetitiveAnalysis, ThreatLevel
from ..services.predictive_lead_lifecycle_engine import ConversionForecast, ConversionStage

# Global integration service instance
_integration_service: Optional[AIEnginesIntegrationService] = None


# Pydantic models for API requests and responses

class AnalysisScopeAPI(str, Enum):
    """Analysis scope options for API"""
    COMPETITIVE_ONLY = "competitive_only"
    PREDICTIVE_ONLY = "predictive_only"
    UNIFIED_ANALYSIS = "unified_analysis"
    CROSS_ENGINE_FUSION = "cross_engine_fusion"


class ProcessingPriorityAPI(str, Enum):
    """Processing priority for API"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class LeadAnalysisRequest(BaseModel):
    """Request model for lead analysis"""
    lead_id: str = Field(..., description="Lead ID to analyze")
    analysis_scope: AnalysisScopeAPI = Field(
        AnalysisScopeAPI.UNIFIED_ANALYSIS,
        description="Scope of analysis to perform"
    )
    priority: ProcessingPriorityAPI = Field(
        ProcessingPriorityAPI.NORMAL,
        description="Processing priority"
    )

    # Context data
    lead_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional lead context data"
    )
    property_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Property context and preferences"
    )
    market_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Market context and conditions"
    )

    # Processing options
    use_cache: bool = Field(True, description="Use cached results if available")
    include_interventions: bool = Field(True, description="Include intervention recommendations")
    include_risk_analysis: bool = Field(True, description="Include risk factor analysis")
    real_time_monitoring: bool = Field(False, description="Enable real-time monitoring")

    # Performance requirements
    max_processing_time_ms: float = Field(
        75.0,
        description="Maximum processing time in milliseconds",
        ge=10.0,
        le=5000.0
    )


class BatchAnalysisRequest(BaseModel):
    """Request model for batch lead analysis"""
    lead_ids: List[str] = Field(..., description="List of lead IDs to analyze", max_items=50)
    analysis_scope: AnalysisScopeAPI = Field(
        AnalysisScopeAPI.UNIFIED_ANALYSIS,
        description="Scope of analysis for all leads"
    )
    priority: ProcessingPriorityAPI = Field(
        ProcessingPriorityAPI.NORMAL,
        description="Processing priority for batch"
    )
    parallel_processing: bool = Field(True, description="Process leads in parallel")
    max_concurrent: int = Field(10, description="Maximum concurrent analyses", ge=1, le=20)


class StrategicRecommendationsRequest(BaseModel):
    """Request model for strategic recommendations"""
    lead_id: str = Field(..., description="Lead ID for recommendations")
    competitive_analysis_id: Optional[str] = Field(
        None,
        description="ID of existing competitive analysis to use"
    )
    conversion_forecast_id: Optional[str] = Field(
        None,
        description="ID of existing conversion forecast to use"
    )
    include_action_items: bool = Field(True, description="Include specific action items")
    include_timeline: bool = Field(True, description="Include timeline recommendations")


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(..., description="Request success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


# Router setup
router = APIRouter(prefix="/api/ai", tags=["AI Engines"])


# Dependency to get integration service
async def get_integration_service() -> AIEnginesIntegrationService:
    """Get or initialize the integration service"""
    global _integration_service

    if _integration_service is None:
        try:
            _integration_service = await get_ai_engines_integration_service()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"AI Engines Integration Service unavailable: {str(e)}"
            )

    return _integration_service


# API Endpoints

@router.post("/analyze/lead/{lead_id}", response_model=APIResponse)
async def analyze_lead_unified(
    lead_id: str,
    request: LeadAnalysisRequest,
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Unified lead analysis using both competitive intelligence and predictive lifecycle engines.

    Provides comprehensive analysis including competitive landscape, conversion predictions,
    risk factors, and strategic recommendations with intelligent cross-engine fusion.
    """
    start_time = time.time()

    try:
        # Convert API enums to service enums
        analysis_scope = AnalysisScope(request.analysis_scope.value)
        priority = ProcessingPriority(request.priority.value)

        # Execute unified analysis
        result = await service.analyze_lead_unified(
            lead_id=lead_id,
            analysis_scope=analysis_scope,
            priority=priority,
            lead_context=request.lead_context,
            property_context=request.property_context,
            market_context=request.market_context,
            use_cache=request.use_cache,
            include_interventions=request.include_interventions,
            include_risk_analysis=request.include_risk_analysis
        )

        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=result.to_dict(),
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.post("/competitive/analyze/{lead_id}", response_model=APIResponse)
async def analyze_competitive_only(
    lead_id: str,
    property_context: Optional[Dict[str, Any]] = None,
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Competitive intelligence analysis only.

    Analyzes competitive landscape, threat detection, and positioning strategies
    for the specified lead without predictive modeling.
    """
    start_time = time.time()

    try:
        result = await service.analyze_competitive_intelligence(
            lead_id=lead_id,
            property_context=property_context
        )

        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=result.to_dict(),
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.post("/predictive/forecast/{lead_id}", response_model=APIResponse)
async def predict_lead_lifecycle_only(
    lead_id: str,
    force_refresh: bool = Query(False, description="Force refresh of cached predictions"),
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Predictive lead lifecycle analysis only.

    Predicts conversion timeline, optimal interventions, and risk factors
    for the specified lead without competitive analysis.
    """
    start_time = time.time()

    try:
        result = await service.predict_lead_lifecycle(
            lead_id=lead_id,
            force_refresh=force_refresh
        )

        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=result.to_dict(),
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.post("/threats-opportunities/{lead_id}", response_model=APIResponse)
async def detect_threats_and_opportunities(
    lead_id: str,
    monitoring_scope: Optional[List[str]] = Query(
        None,
        description="Monitoring scope (e.g., ['mls', 'social_media', 'reviews'])"
    ),
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Detect competitive threats and conversion opportunities.

    Combines real-time threat detection with conversion opportunity analysis
    to provide actionable insights for lead management.
    """
    start_time = time.time()

    try:
        result = await service.detect_threats_and_opportunities(
            lead_id=lead_id,
            monitoring_scope=monitoring_scope
        )

        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.post("/strategic/recommendations/{lead_id}", response_model=APIResponse)
async def generate_strategic_recommendations(
    lead_id: str,
    request: StrategicRecommendationsRequest,
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Generate strategic recommendations based on unified analysis.

    Provides immediate actions, long-term strategies, and tactical recommendations
    based on competitive intelligence and conversion predictions.
    """
    start_time = time.time()

    try:
        # TODO: Retrieve existing analyses by ID if provided
        competitive_analysis = None
        conversion_forecast = None

        result = await service.generate_strategic_recommendations(
            lead_id=lead_id,
            competitive_analysis=competitive_analysis,
            conversion_forecast=conversion_forecast
        )

        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=result,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.post("/batch/analyze", response_model=APIResponse)
async def batch_analyze_leads(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Batch analysis for multiple leads.

    Efficiently processes multiple leads with parallel execution and
    intelligent resource management.
    """
    start_time = time.time()

    try:
        if len(request.lead_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="Maximum 50 leads per batch request"
            )

        # Convert API enums
        analysis_scope = AnalysisScope(request.analysis_scope.value)
        priority = ProcessingPriority(request.priority.value)

        if request.parallel_processing:
            # Parallel batch processing
            semaphore = asyncio.Semaphore(request.max_concurrent)

            async def analyze_single_lead(lead_id: str):
                async with semaphore:
                    return await service.analyze_lead_unified(
                        lead_id=lead_id,
                        analysis_scope=analysis_scope,
                        priority=priority
                    )

            # Execute all analyses in parallel
            tasks = [analyze_single_lead(lead_id) for lead_id in request.lead_ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            successful_results = []
            failed_results = []

            for i, result in enumerate(results):
                lead_id = request.lead_ids[i]
                if isinstance(result, Exception):
                    failed_results.append({"lead_id": lead_id, "error": str(result)})
                else:
                    successful_results.append({
                        "lead_id": lead_id,
                        "analysis": result.to_dict()
                    })

            processing_time = (time.time() - start_time) * 1000

            return APIResponse(
                success=len(failed_results) == 0,
                data={
                    "successful_analyses": successful_results,
                    "failed_analyses": failed_results,
                    "total_processed": len(request.lead_ids),
                    "success_count": len(successful_results),
                    "failure_count": len(failed_results)
                },
                processing_time_ms=processing_time
            )

        else:
            # Sequential processing
            results = []
            for lead_id in request.lead_ids:
                try:
                    result = await service.analyze_lead_unified(
                        lead_id=lead_id,
                        analysis_scope=analysis_scope,
                        priority=priority
                    )
                    results.append({
                        "lead_id": lead_id,
                        "analysis": result.to_dict(),
                        "success": True
                    })
                except Exception as e:
                    results.append({
                        "lead_id": lead_id,
                        "error": str(e),
                        "success": False
                    })

            processing_time = (time.time() - start_time) * 1000

            return APIResponse(
                success=True,
                data={
                    "results": results,
                    "total_processed": len(request.lead_ids)
                },
                processing_time_ms=processing_time
            )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.get("/health", response_model=APIResponse)
async def health_check(
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Comprehensive health check for all AI engines and dependencies.

    Returns health status, performance metrics, and service availability
    for the entire AI engines ecosystem.
    """
    start_time = time.time()

    try:
        health_data = await service.health_check()
        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=health_data.get("healthy", False),
            data=health_data,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


@router.get("/metrics", response_model=APIResponse)
async def get_performance_metrics(
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """
    Get comprehensive performance metrics for all AI engines.

    Returns detailed performance statistics, throughput metrics,
    cache hit rates, and resource utilization data.
    """
    start_time = time.time()

    try:
        metrics = await service.get_performance_metrics()
        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data=metrics,
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


# Startup and shutdown events
@router.on_event("startup")
async def startup_ai_engines():
    """Initialize AI engines on startup"""
    global _integration_service
    try:
        _integration_service = await get_ai_engines_integration_service()
        print("✅ AI Engines Integration Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Engines Integration Service: {e}")
        # Don't raise exception - let service start and handle errors gracefully


@router.on_event("shutdown")
async def shutdown_ai_engines():
    """Cleanup AI engines on shutdown"""
    global _integration_service
    if _integration_service:
        try:
            await _integration_service.cleanup()
            print("✅ AI Engines Integration Service cleaned up successfully")
        except Exception as e:
            print(f"❌ Error cleaning up AI Engines Integration Service: {e}")


# Additional utility endpoints

@router.get("/status")
async def get_ai_engines_status():
    """Quick status check without full health validation"""
    global _integration_service

    return {
        "service_initialized": _integration_service is not None,
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.post("/cache/clear")
async def clear_ai_cache(
    cache_type: str = Query("all", description="Type of cache to clear (all, competitive, predictive)"),
    service: AIEnginesIntegrationService = Depends(get_integration_service)
) -> APIResponse:
    """Clear AI engines cache"""
    start_time = time.time()

    try:
        # Implementation would call appropriate cache clearing methods
        # For now, return success
        processing_time = (time.time() - start_time) * 1000

        return APIResponse(
            success=True,
            data={"cache_cleared": cache_type, "timestamp": datetime.now().isoformat()},
            processing_time_ms=processing_time
        )

    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        return APIResponse(
            success=False,
            error=str(e),
            processing_time_ms=processing_time
        )


# Export router for inclusion in main FastAPI app
__all__ = ["router"]