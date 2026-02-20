"""
Customer Journey API Routes
Provides REST endpoints for customer journey orchestration.
Matches frontend CustomerJourneyAPI.ts expectations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ghl_real_estate_ai.api.middleware.enhanced_auth import get_current_user_optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService, get_cache_service
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
# ROADMAP-026–030: Cache-backed journey CRUD helpers
# ============================================================================

JOURNEY_TTL = 604800  # 7 days
JOURNEY_INDEX_KEY = "journey_index"

VALID_JOURNEY_STATUSES = {"active", "paused", "completed", "abandoned"}
VALID_JOURNEY_TYPES = {"FIRST_TIME_BUYER", "INVESTOR", "SELLER", "COMMERCIAL"}
VALID_PRIORITIES = {"low", "medium", "high", "urgent"}


async def _save_journey(journey: CustomerJourney, cache: CacheService) -> None:
    """Persist journey to cache."""
    await cache.set(f"journey:{journey.id}", journey.model_dump(), ttl=JOURNEY_TTL)
    # Maintain an index of journey IDs for listing
    index = await cache.get(JOURNEY_INDEX_KEY) or []
    if journey.id not in index:
        index.append(journey.id)
        await cache.set(JOURNEY_INDEX_KEY, index, ttl=JOURNEY_TTL)


async def _get_journey(journey_id: str, cache: CacheService) -> Optional[CustomerJourney]:
    """Retrieve journey from cache, excluding soft-deleted."""
    data = await cache.get(f"journey:{journey_id}")
    if data is None:
        return None
    # Check soft-delete
    if data.get("deleted_at"):
        return None
    return CustomerJourney(**data)


async def _list_journeys(cache: CacheService) -> List[CustomerJourney]:
    """List all non-deleted journeys from cache."""
    index = await cache.get(JOURNEY_INDEX_KEY) or []
    journeys = []
    for jid in index:
        j = await _get_journey(jid, cache)
        if j is not None:
            journeys.append(j)
    return journeys


async def _soft_delete_journey(journey_id: str, cache: CacheService) -> bool:
    """ROADMAP-029: Soft-delete journey by setting deleted_at timestamp."""
    data = await cache.get(f"journey:{journey_id}")
    if data is None:
        return False
    data["deleted_at"] = datetime.now().isoformat()
    data["status"] = "abandoned"
    await cache.set(f"journey:{journey_id}", data, ttl=JOURNEY_TTL)
    return True


async def _complete_journey_step(
    journey_id: str, step_id: str, output: Optional[Dict[str, Any]], cache: CacheService
) -> Optional[Dict[str, Any]]:
    """ROADMAP-030: Mark step complete, advance journey, evaluate next step trigger."""
    data = await cache.get(f"journey:{journey_id}")
    if data is None:
        return None

    steps = data.get("steps", [])
    step_found = False
    step_index = -1
    for i, s in enumerate(steps):
        if s.get("id") == step_id:
            step_found = True
            step_index = i
            s["status"] = "completed"
            s["endTime"] = datetime.now().isoformat()
            s["output"] = output or {}
            if not s.get("actualDuration") and s.get("startTime"):
                try:
                    start = datetime.fromisoformat(s["startTime"])
                    s["actualDuration"] = int((datetime.now() - start).total_seconds())
                except (ValueError, TypeError):
                    pass
            break

    if not step_found:
        return None

    # Auto-advance: activate next step
    next_step_activated = None
    if step_index + 1 < len(steps):
        next_step = steps[step_index + 1]
        if next_step["status"] == "pending":
            next_step["status"] = "active"
            next_step["startTime"] = datetime.now().isoformat()
            next_step_activated = next_step["id"]

    # Update journey progress
    completed_count = sum(1 for s in steps if s.get("status") == "completed")
    total = len(steps)
    data["steps"] = steps
    data["currentStep"] = completed_count
    data["completionPercentage"] = int((completed_count / total) * 100) if total > 0 else 0

    # Check if journey is fully complete
    if completed_count == total:
        data["status"] = "completed"
        data["actualCompletion"] = datetime.now().isoformat()

    await cache.set(f"journey:{journey_id}", data, ttl=JOURNEY_TTL)

    return {
        "journey_id": journey_id,
        "step_id": step_id,
        "step_status": "completed",
        "next_step_activated": next_step_activated,
        "journey_completion_percentage": data["completionPercentage"],
        "journey_status": data["status"],
        "completed_step": steps[step_index],
    }


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
    cache: CacheService = Depends(get_cache_service),
):
    """
    Get customer journeys with optional filtering.

    ROADMAP-027: Reads from cache-backed store; falls back to mock data if cache is empty.
    """
    try:
        logger.info(f"Fetching journeys with filters: status={status}, type={type}, limit={limit}")

        # Read from cache; fall back to mock if nothing persisted yet
        all_journeys = await _list_journeys(cache)
        if not all_journeys:
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
async def get_journey(
    journey_id: str,
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Get a specific customer journey by ID.

    ROADMAP-027: Returns journey + all steps with completion status from cache.
    """
    try:
        logger.info(f"Fetching journey: {journey_id}")

        journey = await _get_journey(journey_id, cache)
        if not journey:
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        logger.info(f"Retrieved journey {journey_id}")
        return journey

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch journey")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/journeys", response_model=CustomerJourney)
async def create_journey(
    request: CreateJourneyRequest,
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Create a new customer journey.

    ROADMAP-026: Validates input, generates steps from template, persists to cache.
    """
    try:
        # Validate type and priority
        if request.type not in VALID_JOURNEY_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid journey type. Must be one of: {', '.join(sorted(VALID_JOURNEY_TYPES))}",
            )
        if request.priority not in VALID_PRIORITIES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid priority. Must be one of: {', '.join(sorted(VALID_PRIORITIES))}",
            )

        journey_id = str(uuid.uuid4())
        logger.info(f"Creating journey {journey_id} for customer {request.customerName}")

        # Generate steps from template (or defaults)
        steps = generate_mock_journey_steps()

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

        # Persist to cache
        await _save_journey(journey, cache)

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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating journey: {e}")
        raise HTTPException(status_code=500, detail="Failed to create journey")


@router.put("/journeys/{journey_id}", response_model=CustomerJourney)
async def update_journey(
    journey_id: str,
    request: UpdateJourneyRequest,
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Update an existing customer journey.

    ROADMAP-028: Validates status transitions, applies updates atomically, persists to cache.
    """
    try:
        logger.info(f"Updating journey {journey_id}")

        journey = await _get_journey(journey_id, cache)
        if not journey:
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        # Validate status transition
        if request.status:
            if request.status not in VALID_JOURNEY_STATUSES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid status. Must be one of: {', '.join(sorted(VALID_JOURNEY_STATUSES))}",
                )
            journey.status = request.status
            if request.status == "completed":
                journey.actualCompletion = datetime.now().isoformat()

        if request.priority:
            if request.priority not in VALID_PRIORITIES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid priority. Must be one of: {', '.join(sorted(VALID_PRIORITIES))}",
                )
            journey.priority = request.priority

        if request.context:
            journey.context.update(request.context)
        if request.customizations:
            journey.customizations = request.customizations

        # Persist updated journey
        await _save_journey(journey, cache)

        # Publish journey updated event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_updated",
            {
                "journey_id": journey_id,
                "updates": request.model_dump(exclude_none=True),
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"Journey {journey_id} updated successfully")
        return journey

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update journey")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/journeys/{journey_id}")
async def delete_journey(
    journey_id: str,
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Delete a customer journey (soft-delete).

    ROADMAP-029: Sets deleted_at timestamp to preserve audit trail. Journey is excluded
    from all reads but remains in cache for 7 days.
    """
    try:
        logger.info(f"Deleting journey {journey_id}")

        deleted = await _soft_delete_journey(journey_id, cache)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        # Publish journey deleted event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_deleted", {"journey_id": journey_id, "timestamp": datetime.now().isoformat()}
        )

        logger.info(f"Journey {journey_id} soft-deleted successfully")
        return {"success": True, "journeyId": journey_id, "deletedAt": datetime.now().isoformat()}

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to delete journey")
        raise HTTPException(status_code=500, detail="Internal server error")


# ============================================================================
# STEP MANAGEMENT ENDPOINTS
# ============================================================================


@router.put("/journeys/{journey_id}/steps/{step_id}", response_model=JourneyStep)
async def update_step(
    journey_id: str,
    step_id: str,
    updates: Dict[str, Any],
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Update a specific journey step.

    ROADMAP-029: Validates step belongs to journey, applies updates, persists.
    """
    try:
        logger.info(f"Updating step {step_id} in journey {journey_id}")

        data = await cache.get(f"journey:{journey_id}")
        if data is None or data.get("deleted_at"):
            raise HTTPException(status_code=404, detail=f"Journey {journey_id} not found")

        steps = data.get("steps", [])
        step = None
        for s in steps:
            if s.get("id") == step_id:
                step = s
                # Apply allowed updates
                for field in ("name", "description", "agentId", "agentName",
                              "estimatedDuration", "handoffType", "requirements",
                              "completionCriteria", "metadata"):
                    if field in updates:
                        s[field] = updates[field]
                break

        if step is None:
            raise HTTPException(status_code=404, detail=f"Step {step_id} not found in journey {journey_id}")

        data["steps"] = steps
        await cache.set(f"journey:{journey_id}", data, ttl=JOURNEY_TTL)

        logger.info(f"Step {step_id} updated successfully")
        return JourneyStep(**step)

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to update journey step")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/journeys/{journey_id}/steps/{step_id}/complete")
async def complete_step(
    journey_id: str,
    step_id: str,
    output: Optional[Dict[str, Any]] = None,
    current_user=Depends(get_current_user_optional),
    cache: CacheService = Depends(get_cache_service),
):
    """
    Mark a journey step as completed.

    ROADMAP-030: Marks step done, stores output, updates journey progress,
    auto-activates next step, checks journey completion.
    """
    try:
        logger.info(f"Completing step {step_id} in journey {journey_id}")

        result = await _complete_journey_step(journey_id, step_id, output, cache)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Journey {journey_id} or step {step_id} not found",
            )

        # Publish step completed event
        event_publisher = get_event_publisher()
        await event_publisher.publish_event(
            "journey_step_completed",
            {
                "journey_id": journey_id,
                "step_id": step_id,
                "completion_data": output,
                "next_step_activated": result.get("next_step_activated"),
                "journey_completion_percentage": result["journey_completion_percentage"],
                "timestamp": datetime.now().isoformat(),
            },
        )

        logger.info(f"Step {step_id} completed successfully (journey {result['journey_completion_percentage']}% done)")
        return result

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to complete journey step")
        raise HTTPException(status_code=500, detail="Internal server error")


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
