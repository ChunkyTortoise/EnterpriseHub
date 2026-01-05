"""
Analytics API Routes for Phase 2.

Provides endpoints for:
- Advanced analytics dashboard
- Campaign performance metrics
- A/B testing management
- Performance optimization insights
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.advanced_analytics import ABTestManager, PerformanceAnalyzer, ConversationOptimizer
from ghl_real_estate_ai.services.campaign_analytics import CampaignTracker
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


# Request/Response Models
class ExperimentCreate(BaseModel):
    """Request model for creating A/B test experiment."""
    name: str = Field(..., description="Experiment name")
    variant_a: Dict[str, Any] = Field(..., description="Control variant configuration")
    variant_b: Dict[str, Any] = Field(..., description="Test variant configuration")
    metric: str = Field(default="conversion_rate", description="Primary metric to optimize")
    description: str = Field(default="", description="Experiment description")


class ExperimentResult(BaseModel):
    """Request model for recording experiment results."""
    contact_id: str
    conversion: Optional[bool] = None
    lead_score: Optional[float] = None
    response_time: Optional[float] = None


class DashboardMetrics(BaseModel):
    """Response model for dashboard metrics."""
    total_conversations: int
    avg_lead_score: float
    conversion_rate: float
    response_time_avg: float
    hot_leads: int
    warm_leads: int
    cold_leads: int
    period_start: str
    period_end: str


class CampaignPerformance(BaseModel):
    """Response model for campaign performance."""
    campaign_id: str
    name: str
    total_contacts: int
    response_rate: float
    avg_lead_score: float
    hot_leads: int
    roi_estimate: Optional[float] = None


# Analytics Dashboard Endpoints
@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    location_id: str = Query(..., description="GHL Location ID"),
    days: int = Query(default=7, description="Number of days to analyze")
):
    """
    Get high-level analytics dashboard metrics.
    
    Returns key metrics for the specified time period including:
    - Total conversations
    - Average lead score
    - Conversion rates
    - Lead distribution (hot/warm/cold)
    """
    try:
        analytics = AnalyticsService()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics from daily summary
        metrics = await analytics.get_daily_summary(location_id=location_id)
        
        # If no data, return defaults
        if not metrics:
            metrics = {
                "total_conversations": 0,
                "avg_lead_score": 0.0,
                "conversion_rate": 0.0,
                "response_time_avg": 0.0,
                "hot_leads": 0,
                "warm_leads": 0,
                "cold_leads": 0
            }
        
        return DashboardMetrics(
            total_conversations=metrics.get("total_conversations", 0),
            avg_lead_score=metrics.get("avg_lead_score", 0.0),
            conversion_rate=metrics.get("conversion_rate", 0.0),
            response_time_avg=metrics.get("response_time_avg", 0.0),
            hot_leads=metrics.get("hot_leads", 0),
            warm_leads=metrics.get("warm_leads", 0),
            cold_leads=metrics.get("cold_leads", 0),
            period_start=start_date.isoformat(),
            period_end=end_date.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching dashboard metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard metrics: {str(e)}")


@router.get("/performance-report/{location_id}")
async def get_performance_report(location_id: str):
    """
    Generate detailed performance analysis report.
    
    Analyzes conversation patterns and provides optimization recommendations.
    """
    try:
        analyzer = PerformanceAnalyzer(location_id)
        report = analyzer.generate_performance_report()
        analysis = analyzer.analyze_conversation_patterns()
        
        return {
            "location_id": location_id,
            "report": report,
            "detailed_analysis": analysis,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating performance report: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


# A/B Testing Endpoints
@router.post("/experiments", status_code=201)
async def create_experiment(
    location_id: str,
    experiment: ExperimentCreate
):
    """
    Create a new A/B test experiment.
    
    Experiments allow testing different conversation strategies to optimize performance.
    """
    try:
        ab_manager = ABTestManager(location_id)
        
        experiment_id = ab_manager.create_experiment(
            name=experiment.name,
            variant_a=experiment.variant_a,
            variant_b=experiment.variant_b,
            metric=experiment.metric,
            description=experiment.description
        )
        
        logger.info(f"Created experiment {experiment_id} for location {location_id}")
        
        return {
            "experiment_id": experiment_id,
            "location_id": location_id,
            "status": "active",
            "message": "Experiment created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating experiment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create experiment: {str(e)}")


@router.get("/experiments/{location_id}")
async def list_experiments(location_id: str):
    """
    List all active A/B test experiments for a location.
    """
    try:
        ab_manager = ABTestManager(location_id)
        experiments = ab_manager.list_active_experiments()
        
        return {
            "location_id": location_id,
            "experiments": experiments,
            "count": len(experiments)
        }
        
    except Exception as e:
        logger.error(f"Error listing experiments: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@router.get("/experiments/{location_id}/{experiment_id}/analysis")
async def analyze_experiment(location_id: str, experiment_id: str):
    """
    Get detailed analysis of an A/B test experiment.
    
    Returns statistical analysis and recommendations.
    """
    try:
        ab_manager = ABTestManager(location_id)
        analysis = ab_manager.analyze_experiment(experiment_id)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing experiment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze experiment: {str(e)}")


@router.post("/experiments/{location_id}/{experiment_id}/results")
async def record_experiment_result(
    location_id: str,
    experiment_id: str,
    variant: str,
    result: ExperimentResult
):
    """
    Record a result for an experiment variant.
    
    Used to track performance of different conversation strategies.
    """
    try:
        ab_manager = ABTestManager(location_id)
        
        result_data = {
            "contact_id": result.contact_id,
            "conversion": result.conversion,
            "lead_score": result.lead_score,
            "response_time": result.response_time,
            "timestamp": datetime.now().isoformat()
        }
        
        ab_manager.record_result(experiment_id, variant, result_data)
        
        return {
            "message": "Result recorded successfully",
            "experiment_id": experiment_id,
            "variant": variant
        }
        
    except Exception as e:
        logger.error(f"Error recording experiment result: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to record result: {str(e)}")


@router.post("/experiments/{location_id}/{experiment_id}/complete")
async def complete_experiment(location_id: str, experiment_id: str):
    """
    Mark an experiment as complete and archive it.
    """
    try:
        ab_manager = ABTestManager(location_id)
        ab_manager.complete_experiment(experiment_id)
        
        return {
            "message": "Experiment completed and archived",
            "experiment_id": experiment_id
        }
        
    except Exception as e:
        logger.error(f"Error completing experiment: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to complete experiment: {str(e)}")


# Campaign Analytics Endpoints
@router.get("/campaigns/{location_id}", response_model=List[CampaignPerformance])
async def get_campaign_performance(
    location_id: str,
    days: int = Query(default=30, description="Number of days to analyze")
):
    """
    Get performance metrics for all campaigns in a location.
    """
    try:
        campaign_tracker = CampaignTracker(location_id)
        
        # Get all active campaigns
        campaigns = campaign_tracker.list_active_campaigns()
        
        return [
            CampaignPerformance(
                campaign_id=c["id"],
                name=c["name"],
                total_contacts=c.get("leads_generated", 0),
                response_rate=0.0,  # Not tracked in basic list
                avg_lead_score=0.0,  # Not tracked in basic list
                hot_leads=0,  # Not tracked in basic list
                roi_estimate=c.get("roi", 0.0)
            )
            for c in campaigns
        ]
        
    except Exception as e:
        logger.error(f"Error fetching campaign performance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaigns: {str(e)}")


@router.get("/campaigns/{location_id}/{campaign_id}/details")
async def get_campaign_details(location_id: str, campaign_id: str):
    """
    Get detailed analytics for a specific campaign.
    """
    try:
        campaign_tracker = CampaignTracker(location_id)
        details = campaign_tracker.get_campaign_performance(campaign_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching campaign details: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign details: {str(e)}")


# Conversation Optimization Endpoints
@router.post("/optimize/next-question")
async def suggest_next_question(
    conversation_history: List[str],
    current_lead_score: int,
    questions_answered: List[str]
):
    """
    Get AI-powered suggestion for the next best question to ask.
    
    Based on conversation context and lead score, provides optimized question suggestions.
    """
    try:
        optimizer = ConversationOptimizer()
        
        suggestion = optimizer.suggest_next_question(
            conversation_history=conversation_history,
            current_lead_score=current_lead_score,
            questions_answered=questions_answered
        )
        
        return suggestion
        
    except Exception as e:
        logger.error(f"Error suggesting next question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestion: {str(e)}")


# Health check for analytics service
@router.get("/health")
async def analytics_health():
    """Health check for analytics endpoints."""
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.now().isoformat()
    }
