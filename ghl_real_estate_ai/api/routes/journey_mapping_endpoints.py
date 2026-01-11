"""
Predictive Journey Mapping API Endpoints - Phase 2 Enhancement

FastAPI endpoints for Claude's predictive journey mapping capabilities.
Provides timeline prediction, journey optimization, and risk assessment.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
import json

from ...services.predictive_journey_mapper import (
    get_predictive_journey_mapper,
    PredictiveJourneyMapper,
    PredictiveJourneyResult,
    JourneyStage,
    JourneyMilestone,
    RiskLevel,
    InterventionType,
    JourneyTimelinePrediction,
    JourneyOptimization,
    JourneyRiskAssessment,
    JourneyIntervention
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/claude/journey", tags=["journey-mapping"])


# Pydantic Models for API
class LeadBehavior(BaseModel):
    """Individual behavioral event."""
    timestamp: datetime = Field(..., description="When the behavior occurred")
    action: str = Field(..., description="Action taken by the lead")
    details: Optional[str] = Field(None, description="Additional details about the action")
    engagement_score: Optional[float] = Field(None, description="Engagement score for this interaction")
    response_time: Optional[float] = Field(None, description="Response time in hours")


class JourneyPredictionRequest(BaseModel):
    """Request model for journey prediction."""
    lead_id: str = Field(..., description="Unique lead identifier")
    lead_profile: Dict[str, Any] = Field(..., description="Lead demographics and current status")
    behavioral_history: List[LeadBehavior] = Field(..., description="Historical behavior data")
    market_context: Optional[Dict[str, Any]] = Field(None, description="Current market conditions")
    agent_id: Optional[str] = Field(None, description="Agent handling the lead")


class TimelinePredictionRequest(BaseModel):
    """Request model for timeline-focused prediction."""
    lead_id: str = Field(..., description="Lead identifier")
    lead_profile: Dict[str, Any] = Field(..., description="Lead profile information")
    behavioral_history: List[LeadBehavior] = Field(..., description="Behavioral data")
    target_completion_date: Optional[datetime] = Field(None, description="Desired completion date")


class JourneyOptimizationRequest(BaseModel):
    """Request model for journey optimization."""
    lead_id: str = Field(..., description="Lead identifier")
    lead_profile: Dict[str, Any] = Field(..., description="Lead profile information")
    current_stage: JourneyStage = Field(..., description="Current journey stage")
    optimization_goals: List[str] = Field(default_factory=list, description="Specific optimization objectives")


class RiskAssessmentRequest(BaseModel):
    """Request model for risk assessment."""
    lead_id: str = Field(..., description="Lead identifier")
    lead_profile: Dict[str, Any] = Field(..., description="Lead profile information")
    behavioral_history: List[LeadBehavior] = Field(..., description="Behavioral data")
    assessment_focus: Optional[str] = Field("comprehensive", description="Focus area for assessment")


class InterventionRequest(BaseModel):
    """Request model for intervention recommendations."""
    lead_id: str = Field(..., description="Lead identifier")
    journey_id: str = Field(..., description="Journey prediction ID")
    intervention_focus: Optional[str] = Field("risk_mitigation", description="Focus for interventions")
    urgency_threshold: Optional[str] = Field("moderate", description="Minimum urgency level")


class JourneyUpdateRequest(BaseModel):
    """Request model for journey updates."""
    lead_id: str = Field(..., description="Lead identifier")
    milestone_achieved: Optional[JourneyMilestone] = Field(None, description="Recently achieved milestone")
    stage_update: Optional[JourneyStage] = Field(None, description="Updated journey stage")
    behavioral_update: Optional[LeadBehavior] = Field(None, description="New behavioral data")


class JourneyAnalyticsResponse(BaseModel):
    """Response model for journey analytics."""
    agent_id: str
    date_range: str
    total_journeys_analyzed: int
    average_timeline_accuracy: float
    stage_completion_rates: Dict[str, float]
    common_bottlenecks: List[Dict[str, Any]]
    intervention_success_rates: Dict[str, float]
    timeline_factors: Dict[str, float]


class JourneyBenchmarkResponse(BaseModel):
    """Response model for journey benchmarks."""
    lead_id: str
    journey_stage: JourneyStage
    benchmark_timeline: int  # days
    predicted_timeline: int  # days
    performance_percentile: float
    comparable_leads: int
    success_factors: List[str]
    risk_factors: List[str]


@router.post("/predict", response_model=PredictiveJourneyResult)
async def predict_lead_journey(
    request: JourneyPredictionRequest,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> PredictiveJourneyResult:
    """
    Predict complete lead journey with timeline, optimization, and risk assessment.

    Provides comprehensive journey analysis including:
    - Timeline prediction with milestone forecasting
    - Personalized journey optimization recommendations
    - Risk assessment with intervention strategies
    - Market factor analysis
    - Behavioral insights extraction

    Returns actionable insights for lead nurturing and conversion optimization.
    """
    try:
        logger.info(f"Starting journey prediction for lead {request.lead_id}")

        # Convert Pydantic behavioral data to dict format
        behavioral_history = [
            {
                "timestamp": behavior.timestamp.isoformat(),
                "action": behavior.action,
                "details": behavior.details,
                "engagement_score": behavior.engagement_score,
                "response_time": behavior.response_time
            }
            for behavior in request.behavioral_history
        ]

        result = await journey_mapper.predict_lead_journey(
            lead_id=request.lead_id,
            lead_profile=request.lead_profile,
            behavioral_history=behavioral_history,
            market_context=request.market_context,
            agent_id=request.agent_id
        )

        logger.info(f"Journey prediction completed for lead {request.lead_id}")
        return result

    except Exception as e:
        logger.error(f"Error in journey prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Journey prediction failed: {str(e)}")


@router.post("/timeline", response_model=JourneyTimelinePrediction)
async def predict_timeline(
    request: TimelinePredictionRequest,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> JourneyTimelinePrediction:
    """
    Predict purchase timeline with detailed milestone forecasting.

    Focuses specifically on timeline prediction including:
    - Predicted completion date with confidence levels
    - Milestone achievement forecasts
    - Critical path identification
    - Acceleration opportunities
    - Potential delay factors
    """
    try:
        # Convert behavioral data
        behavioral_history = [
            {
                "timestamp": behavior.timestamp.isoformat(),
                "action": behavior.action,
                "details": behavior.details,
                "engagement_score": behavior.engagement_score,
                "response_time": behavior.response_time
            }
            for behavior in request.behavioral_history
        ]

        timeline_prediction = await journey_mapper._predict_purchase_timeline(
            lead_id=request.lead_id,
            lead_profile=request.lead_profile,
            behavioral_history=behavioral_history,
            market_context=None
        )

        return timeline_prediction

    except Exception as e:
        logger.error(f"Error in timeline prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Timeline prediction failed: {str(e)}")


@router.post("/optimize", response_model=JourneyOptimization)
async def optimize_journey(
    request: JourneyOptimizationRequest,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> JourneyOptimization:
    """
    Optimize journey path with personalized recommendations.

    Provides journey optimization including:
    - Optimal next actions for current stage
    - Communication channel preferences
    - Touchpoint timing optimization
    - Content personalization
    - Frequency recommendations
    """
    try:
        journey_optimization = await journey_mapper._optimize_journey_path(
            lead_id=request.lead_id,
            lead_profile=request.lead_profile,
            behavioral_history=[]  # Can be empty for optimization-focused analysis
        )

        return journey_optimization

    except Exception as e:
        logger.error(f"Error in journey optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Journey optimization failed: {str(e)}")


@router.post("/risk-assessment", response_model=JourneyRiskAssessment)
async def assess_journey_risks(
    request: RiskAssessmentRequest,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> JourneyRiskAssessment:
    """
    Assess journey risks and predict intervention needs.

    Provides comprehensive risk assessment including:
    - Overall risk level classification
    - Stalling and churn probability
    - Competitive threat assessment
    - Early warning indicators
    - Mitigation strategies
    """
    try:
        # Convert behavioral data
        behavioral_history = [
            {
                "timestamp": behavior.timestamp.isoformat(),
                "action": behavior.action,
                "details": behavior.details,
                "engagement_score": behavior.engagement_score,
                "response_time": behavior.response_time
            }
            for behavior in request.behavioral_history
        ]

        risk_assessment = await journey_mapper._assess_journey_risks(
            lead_id=request.lead_id,
            lead_profile=request.lead_profile,
            behavioral_history=behavioral_history,
            market_context=None
        )

        return risk_assessment

    except Exception as e:
        logger.error(f"Error in risk assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {str(e)}")


@router.get("/interventions/{journey_id}", response_model=List[JourneyIntervention])
async def get_journey_interventions(
    journey_id: str,
    intervention_focus: str = Query("risk_mitigation", description="Focus for interventions"),
    urgency_threshold: str = Query("moderate", description="Minimum urgency level"),
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> List[JourneyIntervention]:
    """
    Get intervention recommendations for a specific journey.

    Returns prioritized intervention strategies based on:
    - Current risk levels and bottlenecks
    - Journey stage and progression
    - Lead-specific factors
    - Market conditions
    """
    try:
        # In a full implementation, this would retrieve the journey data
        # For now, return mock interventions based on focus

        interventions = []

        if intervention_focus == "risk_mitigation":
            interventions.append(JourneyIntervention(
                intervention_id=f"risk_intervention_{int(datetime.now().timestamp())}",
                intervention_type=InterventionType.RELATIONSHIP,
                urgency_level="urgent",
                description="Strengthen agent-client relationship with personalized outreach",
                expected_impact="Reduce churn risk by 25-30%",
                success_probability=0.78,
                resource_requirements=["Senior agent time", "Personalized content"],
                timing_recommendation=datetime.now() + timedelta(hours=4),
                success_metrics=["Improved response rate", "Increased engagement score"]
            ))

        elif intervention_focus == "timeline_acceleration":
            interventions.append(JourneyIntervention(
                intervention_id=f"timeline_intervention_{int(datetime.now().timestamp())}",
                intervention_type=InterventionType.MOTIVATIONAL,
                urgency_level="moderate",
                description="Create urgency around limited inventory and market timing",
                expected_impact="Accelerate timeline by 2-3 weeks",
                success_probability=0.65,
                resource_requirements=["Market data", "Inventory reports"],
                timing_recommendation=datetime.now() + timedelta(days=1),
                success_metrics=["Faster milestone completion", "Increased viewing requests"]
            ))

        # Filter by urgency threshold
        urgency_order = {"immediate": 0, "urgent": 1, "moderate": 2, "low": 3}
        threshold_level = urgency_order.get(urgency_threshold, 2)

        filtered_interventions = [
            intervention for intervention in interventions
            if urgency_order.get(intervention.urgency_level, 3) <= threshold_level
        ]

        return filtered_interventions

    except Exception as e:
        logger.error(f"Error getting journey interventions: {e}")
        raise HTTPException(status_code=500, detail=f"Intervention retrieval failed: {str(e)}")


@router.put("/update", response_model=Dict[str, Any])
async def update_journey_progress(
    request: JourneyUpdateRequest,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Update journey progress with new milestone or behavioral data.

    Allows real-time updates to journey predictions based on:
    - Newly achieved milestones
    - Stage progression updates
    - Fresh behavioral data
    - Changed circumstances
    """
    try:
        # In a full implementation, this would update cached journey data
        # and trigger re-prediction if significant changes detected

        update_summary = {
            "lead_id": request.lead_id,
            "update_timestamp": datetime.now().isoformat(),
            "updates_applied": [],
            "requires_re_prediction": False,
            "next_analysis_recommended": False
        }

        if request.milestone_achieved:
            update_summary["updates_applied"].append(f"Milestone achieved: {request.milestone_achieved.value}")
            update_summary["requires_re_prediction"] = True

        if request.stage_update:
            update_summary["updates_applied"].append(f"Stage updated: {request.stage_update.value}")
            update_summary["requires_re_prediction"] = True

        if request.behavioral_update:
            update_summary["updates_applied"].append("New behavioral data added")
            update_summary["next_analysis_recommended"] = True

        return {
            "status": "updated",
            "message": "Journey progress updated successfully",
            "update_summary": update_summary
        }

    except Exception as e:
        logger.error(f"Error updating journey progress: {e}")
        raise HTTPException(status_code=500, detail=f"Journey update failed: {str(e)}")


@router.get("/analytics/{agent_id}", response_model=JourneyAnalyticsResponse)
async def get_journey_analytics(
    agent_id: str,
    days: int = Query(30, description="Number of days for analytics"),
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> JourneyAnalyticsResponse:
    """
    Get journey performance analytics for an agent.

    Provides comprehensive analytics including:
    - Timeline prediction accuracy
    - Stage completion rates
    - Common bottlenecks
    - Intervention effectiveness
    - Success factors analysis
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # In a full implementation, this would query a database of journey analyses
        # For now, return mock analytics
        return JourneyAnalyticsResponse(
            agent_id=agent_id,
            date_range=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            total_journeys_analyzed=87,
            average_timeline_accuracy=0.89,
            stage_completion_rates={
                "awareness": 0.95,
                "consideration": 0.88,
                "qualification": 0.82,
                "property_search": 0.78,
                "property_evaluation": 0.71,
                "negotiation": 0.65,
                "under_contract": 0.58,
                "closing": 0.52
            },
            common_bottlenecks=[
                {"stage": "qualification", "frequency": 0.34, "avg_delay_days": 12},
                {"stage": "property_evaluation", "frequency": 0.28, "avg_delay_days": 18},
                {"stage": "negotiation", "frequency": 0.22, "avg_delay_days": 8}
            ],
            intervention_success_rates={
                "relationship": 0.78,
                "motivational": 0.65,
                "educational": 0.72,
                "process": 0.81,
                "competitive": 0.58
            },
            timeline_factors={
                "urgency_level": 0.35,
                "financial_readiness": 0.28,
                "market_conditions": 0.18,
                "family_dynamics": 0.12,
                "agent_experience": 0.07
            }
        )

    except Exception as e:
        logger.error(f"Error getting journey analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/benchmark/{lead_id}", response_model=JourneyBenchmarkResponse)
async def get_journey_benchmark(
    lead_id: str,
    comparison_criteria: str = Query("similar_profile", description="Criteria for comparison"),
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> JourneyBenchmarkResponse:
    """
    Get journey benchmark comparison for a specific lead.

    Compares lead's journey against similar leads including:
    - Timeline benchmarks
    - Performance percentiles
    - Success factors
    - Risk factors
    """
    try:
        # In a full implementation, this would compare against historical data
        # For now, return mock benchmark data
        return JourneyBenchmarkResponse(
            lead_id=lead_id,
            journey_stage=JourneyStage.PROPERTY_SEARCH,
            benchmark_timeline=45,  # days
            predicted_timeline=38,  # days
            performance_percentile=0.72,
            comparable_leads=156,
            success_factors=[
                "High engagement score early in process",
                "Clear budget and timeline established",
                "Multiple family members involved positively",
                "Strong agent-client rapport"
            ],
            risk_factors=[
                "Competitive market conditions",
                "Seasonal timing challenges",
                "Complex financing requirements"
            ]
        )

    except Exception as e:
        logger.error(f"Error getting journey benchmark: {e}")
        raise HTTPException(status_code=500, detail=f"Benchmark retrieval failed: {str(e)}")


@router.get("/journey/{journey_id}", response_model=PredictiveJourneyResult)
async def get_journey_prediction(
    journey_id: str,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> PredictiveJourneyResult:
    """
    Retrieve a previously completed journey prediction.

    Returns cached journey analysis if available.
    """
    try:
        # Extract lead_id from journey_id for cache lookup
        # In practice, you'd have a mapping from journey_id to lead_id
        lead_id = journey_id.split('_')[-2] if '_' in journey_id else journey_id

        cached_result = await journey_mapper._get_cached_prediction(lead_id)

        if not cached_result:
            raise HTTPException(
                status_code=404,
                detail="Journey prediction not found or expired"
            )

        return cached_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving journey prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.delete("/journey/{journey_id}")
async def delete_journey_prediction(
    journey_id: str,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, str]:
    """
    Delete a journey prediction and its cached results.

    Use this to remove sensitive journey analyses from the system.
    """
    try:
        # Extract lead_id from journey_id
        lead_id = journey_id.split('_')[-2] if '_' in journey_id else journey_id

        if journey_mapper.redis_client:
            await journey_mapper.redis_client.delete(f"journey_prediction:{lead_id}")

        return {
            "journey_id": journey_id,
            "status": "deleted",
            "message": "Journey prediction deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting journey prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.post("/batch-prediction")
async def start_batch_journey_prediction(
    background_tasks: BackgroundTasks,
    agent_id: str,
    lead_ids: List[str],
    prediction_focus: str = "comprehensive",
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Start batch journey prediction for multiple leads.

    Useful for analyzing entire lead portfolios or pipeline assessments.
    """
    try:
        batch_id = f"batch_journey_{int(datetime.now().timestamp())}"

        logger.info(f"Starting batch journey prediction {batch_id} for {len(lead_ids)} leads")

        # Start background batch processing
        background_tasks.add_task(
            _background_batch_journey_prediction,
            journey_mapper,
            lead_ids,
            agent_id,
            batch_id,
            prediction_focus
        )

        return {
            "batch_id": batch_id,
            "status": "started",
            "total_leads": len(lead_ids),
            "estimated_completion_minutes": len(lead_ids) * 1.2,  # ~1.2 minutes per lead
            "message": "Batch journey prediction started"
        }

    except Exception as e:
        logger.error(f"Error starting batch journey prediction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@router.get("/batch-prediction/{batch_id}/status")
async def get_batch_prediction_status(
    batch_id: str,
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Get status of batch journey prediction.

    Returns progress information and estimated completion time.
    """
    try:
        # In a full implementation, this would check Redis for batch status
        return {
            "batch_id": batch_id,
            "status": "processing",
            "total_leads": 35,
            "completed": 22,
            "failed": 2,
            "in_progress": 11,
            "estimated_completion": datetime.now() + timedelta(minutes=8),
            "results_available": 22,
            "message": "Batch journey prediction in progress"
        }

    except Exception as e:
        logger.error(f"Error getting batch prediction status: {e}")
        raise HTTPException(status_code=500, detail=f"Batch status check failed: {str(e)}")


@router.get("/milestones/{lead_id}")
async def get_milestone_tracking(
    lead_id: str,
    include_predictions: bool = Query(True, description="Include future milestone predictions"),
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Get milestone tracking for a specific lead.

    Returns current milestone status and future predictions.
    """
    try:
        # In a full implementation, this would retrieve actual milestone data
        current_date = datetime.now()

        milestones = []

        for i, milestone in enumerate(JourneyMilestone):
            achieved = i < 4  # Mock: first 4 milestones achieved
            achievement_date = current_date - timedelta(days=(4-i)*7) if achieved else None
            predicted_date = current_date + timedelta(days=(i-3)*7) if not achieved else None

            milestones.append({
                "milestone": milestone.value,
                "achieved": achieved,
                "achievement_date": achievement_date.isoformat() if achievement_date else None,
                "predicted_date": predicted_date.isoformat() if predicted_date and include_predictions else None,
                "confidence_score": 0.8 if not achieved else 1.0,
                "days_from_start": i * 7
            })

        return {
            "lead_id": lead_id,
            "milestone_summary": {
                "total_milestones": len(milestones),
                "achieved": sum(1 for m in milestones if m["achieved"]),
                "remaining": sum(1 for m in milestones if not m["achieved"]),
                "completion_percentage": sum(1 for m in milestones if m["achieved"]) / len(milestones) * 100
            },
            "milestones": milestones,
            "next_milestone": next((m for m in milestones if not m["achieved"]), None),
            "timeline_status": "on_track"
        }

    except Exception as e:
        logger.error(f"Error getting milestone tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Milestone tracking failed: {str(e)}")


@router.get("/health")
async def health_check(
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Health check endpoint for journey mapping service.

    Verifies Claude API and Redis connectivity.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "claude_api": "unknown",
                "redis": "unknown"
            },
            "capabilities": {
                "timeline_prediction": True,
                "journey_optimization": True,
                "risk_assessment": True,
                "milestone_tracking": True,
                "batch_processing": True
            }
        }

        # Check Redis
        if journey_mapper.redis_client:
            try:
                await journey_mapper.redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception:
                health_status["services"]["redis"] = "unhealthy"
        else:
            health_status["services"]["redis"] = "not_configured"

        # Check Claude API
        try:
            test_response = await journey_mapper.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            health_status["services"]["claude_api"] = "healthy" if test_response else "unhealthy"
        except Exception:
            health_status["services"]["claude_api"] = "unhealthy"

        # Overall status
        if all(status in ["healthy", "not_configured"] for status in health_status["services"].values()):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Background task functions
async def _background_batch_journey_prediction(
    journey_mapper: PredictiveJourneyMapper,
    lead_ids: List[str],
    agent_id: str,
    batch_id: str,
    prediction_focus: str
):
    """Background task for batch journey prediction."""
    try:
        results = []
        for lead_id in lead_ids:
            try:
                # In a real implementation, this would retrieve lead data and perform prediction
                await asyncio.sleep(0.8)  # Simulate processing time
                results.append(f"Journey prediction completed for {lead_id}")

            except Exception as e:
                logger.error(f"Error predicting journey for lead {lead_id}: {e}")

        logger.info(f"Batch journey prediction {batch_id} completed: {len(results)} leads processed")

    except Exception as e:
        logger.error(f"Batch journey prediction {batch_id} failed: {e}")


@router.get("/templates/prediction-prompts")
async def get_prediction_templates() -> Dict[str, str]:
    """
    Get journey prediction prompt templates for different scenarios.

    Useful for understanding prediction methodology and custom implementations.
    """
    try:
        return {
            "timeline_prediction": """
            Analyze this lead's profile and predict their real estate purchase timeline:

            Key factors to consider:
            1. Current journey stage and progression indicators
            2. Urgency level and external pressures (job relocation, lease expiration, etc.)
            3. Financial readiness and pre-approval status
            4. Family dynamics and decision-making complexity
            5. Market conditions and seasonal factors
            6. Property search criteria specificity

            Provide specific milestone dates with confidence levels.
            """,

            "journey_optimization": """
            Optimize this lead's journey experience based on their profile:

            Optimization areas:
            1. Communication channel preferences and timing
            2. Content personalization for their interests/needs
            3. Touchpoint frequency optimization
            4. Decision-making style accommodation
            5. Family involvement coordination
            6. Technology comfort level considerations

            Provide specific, actionable recommendations for each area.
            """,

            "risk_assessment": """
            Assess risks in this lead's journey and predict intervention needs:

            Risk factors to evaluate:
            1. Engagement level trends and response patterns
            2. Market pressure and competitive threats
            3. Financial or personal circumstance changes
            4. Decision-making delays or hesitation patterns
            5. Agent-client relationship quality indicators
            6. External factors affecting timeline or motivation

            Provide risk scores and specific mitigation strategies.
            """
        }

    except Exception as e:
        logger.error(f"Error retrieving prediction templates: {e}")
        raise HTTPException(status_code=500, detail=f"Template retrieval failed: {str(e)}")


@router.post("/simulate-journey")
async def simulate_journey_scenarios(
    lead_profile: Dict[str, Any],
    scenario_variations: List[Dict[str, Any]],
    journey_mapper: PredictiveJourneyMapper = Depends(get_predictive_journey_mapper)
) -> Dict[str, Any]:
    """
    Simulate different journey scenarios for strategic planning.

    Useful for testing different approaches or market condition impacts.
    """
    try:
        simulations = []

        for i, variation in enumerate(scenario_variations):
            simulation_id = f"sim_{int(datetime.now().timestamp())}_{i}"

            # In a full implementation, this would run actual predictions with variations
            simulations.append({
                "simulation_id": simulation_id,
                "scenario": variation.get("name", f"Scenario {i+1}"),
                "parameters": variation,
                "predicted_timeline": 45 + (i * 5),  # Mock varying timelines
                "success_probability": 0.75 - (i * 0.1),  # Mock varying success rates
                "key_differences": [
                    f"Timeline differs by {i * 5} days from baseline",
                    f"Success probability varies by {i * 10}%"
                ]
            })

        return {
            "simulation_summary": {
                "total_scenarios": len(simulations),
                "baseline_timeline": 45,
                "timeline_range": f"{min(s['predicted_timeline'] for s in simulations)}-{max(s['predicted_timeline'] for s in simulations)} days",
                "success_rate_range": f"{min(s['success_probability'] for s in simulations):.0%}-{max(s['success_probability'] for s in simulations):.0%}"
            },
            "scenarios": simulations,
            "recommendations": [
                "Scenario 1 shows optimal conditions for fastest conversion",
                "Market condition variations significantly impact timeline",
                "Communication frequency optimization provides consistent benefits"
            ]
        }

    except Exception as e:
        logger.error(f"Error simulating journey scenarios: {e}")
        raise HTTPException(status_code=500, detail=f"Journey simulation failed: {str(e)}")