"""
Customer Journey API Routes
Provides REST endpoints for customer journey orchestration.
Matches frontend CustomerJourneyAPI.ts expectations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.agents.customer_journey_orchestrator import get_customer_journey_orchestrator
from ghl_real_estate_ai.api.middleware.enhanced_auth import get_current_user_optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)
router = APIRouter(prefix="/api/customer-journey", tags=["customer-journey"])

# ============================================================================
# RESPONSE MODELS (Match Frontend TypeScript Interfaces)
# ============================================================================


class JourneyStep(BaseModel):
    """Journey step matching frontend interface."""

    id: str
    name: str
    description: str
    agentId: str
    agentName: str
    estimatedDuration: int  # seconds
    actualDuration: Optional[int] = None
    status: str  # 'pending' | 'active' | 'completed' | 'skipped' | 'failed'
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    nextSteps: List[str]
    handoffType: Optional[str] = None  # 'SEQUENTIAL' | 'COLLABORATIVE' | 'ESCALATION'
    requirements: Optional[List[str]] = None
    completionCriteria: Optional[List[str]] = None
    failureReasons: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class CustomerJourney(BaseModel):
    """Customer journey matching frontend interface."""

    id: str
    customerId: str
    customerName: str
    customerEmail: Optional[str] = None
    customerPhone: Optional[str] = None
    type: str  # 'FIRST_TIME_BUYER' | 'INVESTOR' | 'SELLER' | 'COMMERCIAL'
    status: str  # 'active' | 'paused' | 'completed' | 'abandoned'
    priority: str  # 'low' | 'medium' | 'high' | 'urgent'
    currentStep: int
    totalSteps: int
    completionPercentage: int
    startTime: str
    estimatedCompletion: Optional[str] = None
    actualCompletion: Optional[str] = None
    steps: List[JourneyStep]
    analytics: Dict[str, Any]
    context: Dict[str, Any]
    customizations: Optional[Dict[str, Any]] = None
    notifications: List[Dict[str, Any]]


class JourneyAnalytics(BaseModel):
    """Journey analytics matching frontend interface."""

    totalJourneys: int
    activeJourneys: int
    completedJourneys: int
    avgCompletionTime: int  # seconds
    avgSatisfactionScore: float
    completionRateByType: Dict[str, float]
    stageAnalysis: Dict[str, Dict[str, Any]]
    agentPerformance: Dict[str, Dict[str, Any]]
    bottleneckAnalysis: List[Dict[str, Any]]


class JourneyTemplate(BaseModel):
    """Journey template matching frontend interface."""

    id: str
    type: str  # 'FIRST_TIME_BUYER' | 'INVESTOR' | 'SELLER' | 'COMMERCIAL'
    name: str
    description: str
    steps: List[Dict[str, Any]]  # Template steps without runtime data
    estimatedDuration: int
    successRate: float
    version: str


class HandoffEvent(BaseModel):
    """Handoff event matching frontend interface."""

    id: str
    journeyId: str
    fromAgent: str
    toAgent: str
    stepId: str
    handoffType: str  # 'SEQUENTIAL' | 'COLLABORATIVE' | 'ESCALATION'
    contextData: Dict[str, Any]
    status: str  # 'initiated' | 'in_progress' | 'completed' | 'failed'
    startTime: str
    endTime: Optional[str] = None
    duration: Optional[int] = None
    failureReason: Optional[str] = None


class JourneyOptimization(BaseModel):
    """Journey optimization matching frontend interface."""

    journeyId: str
    recommendations: List[Dict[str, Any]]
    predictedOutcomes: Dict[str, Any]
    riskAssessment: Dict[str, Any]


# ============================================================================
# REQUEST MODELS
# ============================================================================


class CreateJourneyRequest(BaseModel):
    """Request model for creating a journey."""

    customerId: str
    customerName: str
    customerEmail: Optional[str] = None
    customerPhone: Optional[str] = None
    type: str  # 'FIRST_TIME_BUYER' | 'INVESTOR' | 'SELLER' | 'COMMERCIAL'
    templateId: Optional[str] = None
    priority: str = "medium"
    context: Optional[Dict[str, Any]] = None
    customizations: Optional[Dict[str, Any]] = None


class UpdateJourneyRequest(BaseModel):
    """Request model for updating a journey."""

    status: Optional[str] = None
    priority: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    customizations: Optional[Dict[str, Any]] = None


class HandoffRequest(BaseModel):
    """Request model for initiating handoffs."""

    toAgent: str
    handoffType: str  # 'SEQUENTIAL' | 'COLLABORATIVE' | 'ESCALATION'
    contextData: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


# ============================================================================
# MOCK DATA GENERATORS
# ============================================================================


def generate_mock_journey_steps() -> List[JourneyStep]:
    """Generate mock journey steps."""
    steps = [
        JourneyStep(
            id="step-1",
            name="Initial Contact",
            description="Establish first contact and build rapport",
            agentId="adaptive-jorge",
            agentName="Adaptive Jorge Seller Bot",
            estimatedDuration=1800,  # 30 minutes
            actualDuration=1650,
            status="completed",
            startTime=(datetime.now() - timedelta(hours=2)).isoformat(),
            endTime=(datetime.now() - timedelta(hours=1, minutes=32)).isoformat(),
            output={"rapport_score": 8.5, "initial_interest": "high"},
            nextSteps=["step-2"],
            handoffType="SEQUENTIAL",
            completionCriteria=["Contact established", "Basic info collected"],
            metadata={"temperature": "hot"},
        ),
        JourneyStep(
            id="step-2",
            name="Needs Analysis",
            description="Deep dive into customer needs and preferences",
            agentId="realtime-intent",
            agentName="Real-time Intent Decoder",
            estimatedDuration=2400,  # 40 minutes
            actualDuration=None,
            status="active",
            startTime=(datetime.now() - timedelta(minutes=32)).isoformat(),
            endTime=None,
            output=None,
            nextSteps=["step-3"],
            handoffType="COLLABORATIVE",
            requirements=["Initial contact completed"],
            completionCriteria=["Needs identified", "Budget confirmed"],
            metadata={"analysis_depth": "comprehensive"},
        ),
        JourneyStep(
            id="step-3",
            name="Property Matching",
            description="Match properties to customer requirements",
            agentId="property-intelligence",
            agentName="Property Intelligence Agent",
            estimatedDuration=3600,  # 60 minutes
            actualDuration=None,
            status="pending",
            startTime=None,
            endTime=None,
            output=None,
            nextSteps=["step-4"],
            handoffType="SEQUENTIAL",
            requirements=["Needs analysis completed"],
            completionCriteria=["Properties identified", "Initial screening done"],
            metadata={"match_criteria": "strict"},
        ),
        JourneyStep(
            id="step-4",
            name="Presentation & Negotiation",
            description="Present properties and handle negotiations",
            agentId="voss-negotiation",
            agentName="Voss Negotiation Agent",
            estimatedDuration=7200,  # 2 hours
            actualDuration=None,
            status="pending",
            startTime=None,
            endTime=None,
            output=None,
            nextSteps=["step-5"],
            handoffType="ESCALATION",
            requirements=["Property matching completed"],
            completionCriteria=["Offer presented", "Terms negotiated"],
            metadata={"negotiation_style": "tactical_empathy"},
        ),
        JourneyStep(
            id="step-5",
            name="Contract & Closing",
            description="Finalize contract and guide through closing",
            agentId="transaction-coordinator",
            agentName="Transaction Coordination Agent",
            estimatedDuration=172800,  # 48 hours
            actualDuration=None,
            status="pending",
            startTime=None,
            endTime=None,
            output=None,
            nextSteps=[],
            handoffType="SEQUENTIAL",
            requirements=["Negotiation completed"],
            completionCriteria=["Contract signed", "Closing completed"],
            metadata={"transaction_type": "purchase"},
        ),
    ]
    return steps


def generate_mock_journeys() -> List[CustomerJourney]:
    """Generate mock customer journeys."""
    journeys = []

    journey_types = ["FIRST_TIME_BUYER", "INVESTOR", "SELLER", "COMMERCIAL"]
    statuses = ["active", "paused", "completed"]
    priorities = ["low", "medium", "high", "urgent"]

    for i in range(12):
        journey_id = str(uuid.uuid4())
        customer_id = f"customer-{i + 1}"
        journey_type = journey_types[i % 4]
        status = statuses[i % 3]
        priority = priorities[i % 4]

        steps = generate_mock_journey_steps()
        current_step = 2 if status == "active" else (5 if status == "completed" else 1)
        completion_percentage = int((current_step / len(steps)) * 100)

        journeys.append(
            CustomerJourney(
                id=journey_id,
                customerId=customer_id,
                customerName=f"Customer {i + 1}",
                customerEmail=f"customer{i + 1}@example.com",
                customerPhone=f"+1-555-{1000 + i}",
                type=journey_type,
                status=status,
                priority=priority,
                currentStep=current_step,
                totalSteps=len(steps),
                completionPercentage=completion_percentage,
                startTime=(datetime.now() - timedelta(days=i % 7)).isoformat(),
                estimatedCompletion=(datetime.now() + timedelta(days=3)).isoformat() if status == "active" else None,
                actualCompletion=(datetime.now() - timedelta(days=1)).isoformat() if status == "completed" else None,
                steps=steps,
                analytics={
                    "avgResponseTime": 2400 + (i * 100),
                    "customerSatisfaction": 4.2 + (i % 5) * 0.2,
                    "handoffEfficiency": 85 + (i % 15),
                    "touchpoints": 15 + (i % 10),
                    "stageDropoffs": {"initial": 5, "needs": 8, "matching": 12},
                    "bottlenecks": ["property_matching"] if i % 3 == 0 else [],
                },
                context={
                    "budget": 500000 + (i * 50000),
                    "timeframe": f"{30 + i * 10} days",
                    "preferences": ["modern", "downtown"] if i % 2 else ["traditional", "suburban"],
                    "requirements": ["parking", "good_schools"] if i % 3 else ["investment_potential"],
                    "marketSegment": "luxury" if i % 4 == 0 else "standard",
                    "leadSource": "website" if i % 2 else "referral",
                    "assignedAgent": f"agent-{i % 3 + 1}",
                },
                customizations={
                    "skipSteps": ["step-1"] if status == "completed" else [],
                    "additionalSteps": [],
                    "priorityBoosts": {"negotiation": 1.5} if priority == "high" else {},
                },
                notifications=[
                    {
                        "id": f"notif-{i}-1",
                        "type": "milestone",
                        "message": f"Journey step {current_step} completed",
                        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                        "acknowledged": True,
                    }
                ],
            )
        )

    return journeys


def generate_mock_templates() -> List[JourneyTemplate]:
    """Generate mock journey templates."""
    templates = [
        JourneyTemplate(
            id="template-first-buyer",
            type="FIRST_TIME_BUYER",
            name="First-Time Buyer Journey",
            description="Guided journey for first-time home buyers with education focus",
            steps=[
                {
                    "name": "Education & Onboarding",
                    "description": "Educate about home buying process",
                    "agentId": "education-specialist",
                    "estimatedDuration": 3600,
                },
                {
                    "name": "Financial Pre-qualification",
                    "description": "Assess financial readiness and pre-approval",
                    "agentId": "financial-advisor",
                    "estimatedDuration": 2400,
                },
                {
                    "name": "Needs Discovery",
                    "description": "Identify specific needs and preferences",
                    "agentId": "needs-specialist",
                    "estimatedDuration": 1800,
                },
                {
                    "name": "Market Education",
                    "description": "Educate about local market conditions",
                    "agentId": "market-educator",
                    "estimatedDuration": 1800,
                },
                {
                    "name": "Property Search",
                    "description": "Search and present suitable properties",
                    "agentId": "property-specialist",
                    "estimatedDuration": 7200,
                },
                {
                    "name": "Viewing Coordination",
                    "description": "Coordinate and conduct property viewings",
                    "agentId": "showing-coordinator",
                    "estimatedDuration": 14400,
                },
                {
                    "name": "Offer & Negotiation",
                    "description": "Guide through offer and negotiation process",
                    "agentId": "negotiation-specialist",
                    "estimatedDuration": 7200,
                },
            ],
            estimatedDuration=38400,  # ~11 hours over several days
            successRate=0.82,
            version="v1.0",
        ),
        JourneyTemplate(
            id="template-investor",
            type="INVESTOR",
            name="Real Estate Investor Journey",
            description="Analytical journey for investment property buyers",
            steps=[
                {
                    "name": "Investment Strategy",
                    "description": "Define investment goals and strategy",
                    "agentId": "investment-strategist",
                    "estimatedDuration": 2400,
                },
                {
                    "name": "Market Analysis",
                    "description": "Comprehensive market analysis and opportunities",
                    "agentId": "market-analyst",
                    "estimatedDuration": 3600,
                },
                {
                    "name": "Financial Modeling",
                    "description": "ROI analysis and financial projections",
                    "agentId": "financial-modeler",
                    "estimatedDuration": 3600,
                },
                {
                    "name": "Property Screening",
                    "description": "Screen properties based on investment criteria",
                    "agentId": "investment-screener",
                    "estimatedDuration": 7200,
                },
                {
                    "name": "Due Diligence",
                    "description": "Comprehensive property analysis and inspection",
                    "agentId": "due-diligence-specialist",
                    "estimatedDuration": 14400,
                },
                {
                    "name": "Negotiation & Acquisition",
                    "description": "Strategic negotiation for optimal terms",
                    "agentId": "investment-negotiator",
                    "estimatedDuration": 10800,
                },
            ],
            estimatedDuration=42000,  # ~12 hours
            successRate=0.75,
            version="v1.0",
        ),
    ]
    return templates


def generate_mock_analytics() -> JourneyAnalytics:
    """Generate mock journey analytics."""
    return JourneyAnalytics(
        totalJourneys=156,
        activeJourneys=45,
        completedJourneys=89,
        avgCompletionTime=259200,  # 72 hours
        avgSatisfactionScore=4.3,
        completionRateByType={"FIRST_TIME_BUYER": 0.82, "INVESTOR": 0.75, "SELLER": 0.89, "COMMERCIAL": 0.65},
        stageAnalysis={
            "initial_contact": {"count": 67, "avgDuration": 1800, "dropoffRate": 12.2, "successRate": 87.8},
            "needs_analysis": {"count": 59, "avgDuration": 2400, "dropoffRate": 8.5, "successRate": 91.5},
            "property_matching": {"count": 54, "avgDuration": 4200, "dropoffRate": 15.7, "successRate": 84.3},
            "negotiation": {"count": 42, "avgDuration": 7200, "dropoffRate": 19.0, "successRate": 81.0},
        },
        agentPerformance={
            "adaptive-jorge": {
                "journeysHandled": 89,
                "avgHandoffTime": 1200,
                "satisfactionScore": 4.5,
                "successRate": 0.87,
            },
            "property-intelligence": {
                "journeysHandled": 67,
                "avgHandoffTime": 2400,
                "satisfactionScore": 4.2,
                "successRate": 0.84,
            },
            "realtime-intent": {
                "journeysHandled": 78,
                "avgHandoffTime": 850,
                "satisfactionScore": 4.4,
                "successRate": 0.91,
            },
        },
        bottleneckAnalysis=[
            {
                "stage": "property_matching",
                "frequency": 23,
                "avgDelay": 3600,
                "causes": ["Limited inventory", "Complex requirements"],
                "recommendations": ["Expand search criteria", "Use AI-powered matching"],
            },
            {
                "stage": "negotiation",
                "frequency": 15,
                "avgDelay": 7200,
                "causes": ["Multiple offers", "Financing delays"],
                "recommendations": ["Pre-approval verification", "Competitive strategies"],
            },
        ],
    )


# ============================================================================
# JOURNEY MANAGEMENT ENDPOINTS
# ============================================================================


@router.get("/journeys")
async def get_journeys(
    status: Optional[List[str]] = Query(default=None),
    type: Optional[List[str]] = Query(default=None),
    priority: Optional[List[str]] = Query(default=None),
    assignedAgent: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    current_user=Depends(get_current_user_optional),
):
    """
    Get customer journeys with optional filtering.
    Matches frontend CustomerJourneyAPI.getJourneys() expectation.
    """
    try:
        logger.info(f"Fetching journeys with filters: status={status}, type={type}, limit={limit}")

        # Generate mock journeys
        all_journeys = generate_mock_journeys()

        # Apply filters
        filtered_journeys = all_journeys

        if status:
            filtered_journeys = [j for j in filtered_journeys if j.status in status]

        if type:
            filtered_journeys = [j for j in filtered_journeys if j.type in type]

        if priority:
            filtered_journeys = [j for j in filtered_journeys if j.priority in priority]

        if assignedAgent:
            filtered_journeys = [j for j in filtered_journeys if j.context.get("assignedAgent") == assignedAgent]

        # Apply pagination
        total = len(filtered_journeys)
        paginated_journeys = filtered_journeys[offset : offset + limit]
        has_more = offset + len(paginated_journeys) < total

        result = {"journeys": paginated_journeys, "total": total, "hasMore": has_more}

        logger.info(f"Retrieved {len(paginated_journeys)} journeys (total: {total})")
        return result

    except Exception as e:
        logger.error(f"Error fetching journeys: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch journeys")


@router.get("/journeys/{journey_id}", response_model=CustomerJourney)
async def get_journey(journey_id: str, current_user=Depends(get_current_user_optional)):
    """
    Get a specific customer journey by ID.
    """
    try:
        logger.info(f"Fetching journey: {journey_id}")

        # In production, this would fetch from database
        journeys = generate_mock_journeys()
        journey = next((j for j in journeys if j.id == journey_id), None)

        if not journey:
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        logger.info(f"Retrieved journey {journey_id}")
        return journey

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching journey {journey_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch journey {journey_id}")


@router.post("/journeys", response_model=CustomerJourney)
async def create_journey(request: CreateJourneyRequest, current_user=Depends(get_current_user_optional)):
    """
    Create a new customer journey.
    """
    try:
        journey_id = str(uuid.uuid4())
        logger.info(f"Creating journey {journey_id} for customer {request.customerName}")

        # TODO: Implement actual journey creation logic
        # This would use the journey orchestrator to create and initialize a journey

        # Generate steps based on template or type
        steps = generate_mock_journey_steps()

        # Create journey
        journey = CustomerJourney(
            id=journey_id,
            customerId=request.customerId,
            customerName=request.customerName,
            customerEmail=request.customerEmail,
            customerPhone=request.customerPhone,
            type=request.type,
            status="active",
            priority=request.priority,
            currentStep=0,
            totalSteps=len(steps),
            completionPercentage=0,
            startTime=datetime.now().isoformat(),
            estimatedCompletion=(datetime.now() + timedelta(days=7)).isoformat(),
            actualCompletion=None,
            steps=steps,
            analytics={
                "avgResponseTime": 0,
                "customerSatisfaction": None,
                "handoffEfficiency": 0,
                "touchpoints": 0,
                "stageDropoffs": {},
                "bottlenecks": [],
            },
            context=request.context or {},
            customizations=request.customizations,
            notifications=[],
        )

        # Publish journey created event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_created",
            {
                "journey_id": journey_id,
                "customer_id": request.customerId,
                "type": request.type,
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"Journey {journey_id} created successfully")
        return journey

    except Exception as e:
        logger.error(f"Error creating journey: {e}")
        raise HTTPException(status_code=500, detail="Failed to create journey")


@router.put("/journeys/{journey_id}", response_model=CustomerJourney)
async def update_journey(
    journey_id: str, request: UpdateJourneyRequest, current_user=Depends(get_current_user_optional)
):
    """
    Update an existing customer journey.
    """
    try:
        logger.info(f"Updating journey {journey_id}")

        # TODO: Implement actual journey update logic
        # This would update the journey in the database

        # For now, return a mock updated journey
        journeys = generate_mock_journeys()
        journey = next((j for j in journeys if j.id == journey_id), None)

        if not journey:
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        # Apply updates
        if request.status:
            journey.status = request.status
        if request.priority:
            journey.priority = request.priority
        if request.context:
            journey.context.update(request.context)

        # Publish journey updated event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_updated",
            {
                "journey_id": journey_id,
                "updates": request.dict(exclude_none=True),
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"Journey {journey_id} updated successfully")
        return journey

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating journey {journey_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update journey {journey_id}")


@router.delete("/journeys/{journey_id}")
async def delete_journey(journey_id: str, current_user=Depends(get_current_user_optional)):
    """
    Delete a customer journey.
    """
    try:
        logger.info(f"Deleting journey {journey_id}")

        # TODO: Implement actual journey deletion logic
        # This would soft-delete or archive the journey

        # Publish journey deleted event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_deleted", {"journey_id": journey_id, "timestamp": datetime.now().isoformat()}
        )

        logger.info(f"Journey {journey_id} deleted successfully")
        return {"success": True, "journeyId": journey_id}

    except Exception as e:
        logger.error(f"Error deleting journey {journey_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete journey {journey_id}")


# ============================================================================
# STEP MANAGEMENT ENDPOINTS
# ============================================================================


@router.put("/journeys/{journey_id}/steps/{step_id}", response_model=JourneyStep)
async def update_step(
    journey_id: str, step_id: str, updates: Dict[str, Any], current_user=Depends(get_current_user_optional)
):
    """
    Update a specific journey step.
    """
    try:
        logger.info(f"Updating step {step_id} in journey {journey_id}")

        # TODO: Implement actual step update logic

        # Mock updated step
        steps = generate_mock_journey_steps()
        step = next((s for s in steps if s.id == step_id), None)

        if not step:
            raise HTTPException(status_code=404, detail=f"Step {step_id} not found")

        logger.info(f"Step {step_id} updated successfully")
        return step

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating step {step_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update step {step_id}")


@router.post("/journeys/{journey_id}/steps/{step_id}/complete", response_model=JourneyStep)
async def complete_step(
    journey_id: str,
    step_id: str,
    output: Optional[Dict[str, Any]] = None,
    current_user=Depends(get_current_user_optional),
):
    """
    Mark a journey step as completed.
    """
    try:
        logger.info(f"Completing step {step_id} in journey {journey_id}")

        # TODO: Implement actual step completion logic

        # Publish step completed event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_step_completed",
            {
                "journey_id": journey_id,
                "step_id": step_id,
                "completion_data": output,
                "timestamp": datetime.now().isoformat(),
            },
        )

        # Mock completed step
        steps = generate_mock_journey_steps()
        step = next((s for s in steps if s.id == step_id), None)

        if step:
            step.status = "completed"
            step.endTime = datetime.now().isoformat()
            step.output = output

        logger.info(f"Step {step_id} completed successfully")
        return step

    except Exception as e:
        logger.error(f"Error completing step {step_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to complete step {step_id}")


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================


@router.get("/analytics", response_model=JourneyAnalytics)
async def get_analytics(
    timeframe: str = Query(default="week", pattern="^(Union[day, week]|Union[month, quarter])$"),
    current_user=Depends(get_current_user_optional),
):
    """
    Get journey analytics for specified timeframe.
    """
    try:
        logger.info(f"Fetching journey analytics for {timeframe}")

        # Generate analytics (in production, this would analyze real data)
        analytics = generate_mock_analytics()

        logger.info(f"Journey analytics generated for {timeframe}")
        return analytics

    except Exception as e:
        logger.error(f"Error fetching journey analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch journey analytics")


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================


@router.get("/templates", response_model=List[JourneyTemplate])
async def get_templates(type: Optional[str] = Query(default=None), current_user=Depends(get_current_user_optional)):
    """
    Get journey templates, optionally filtered by type.
    """
    try:
        logger.info(f"Fetching journey templates (type: {type})")

        templates = generate_mock_templates()

        if type:
            templates = [t for t in templates if t.type == type]

        logger.info(f"Retrieved {len(templates)} journey templates")
        return templates

    except Exception as e:
        logger.error(f"Error fetching journey templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch journey templates")
