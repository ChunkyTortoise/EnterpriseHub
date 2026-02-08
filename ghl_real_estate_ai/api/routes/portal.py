"""
Portal Routes for GHL Real Estate AI.

Handles branded client portal interactions including swipe actions.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.portal_swipe_manager import (
    FeedbackCategory,
    PortalSwipeManager,
    SwipeAction,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/portal", tags=["portal"])

# Initialize the swipe manager
swipe_manager = PortalSwipeManager()


# Request/Response Models
class SwipeFeedback(BaseModel):
    """Feedback for a pass action."""

    category: str = Field(..., description="Feedback category: price_too_high, location, style, etc.")
    text: Optional[str] = Field(None, description="Optional text feedback from user")


class SwipeRequest(BaseModel):
    """Request model for swipe actions."""

    lead_id: str = Field(..., description="GHL contact ID")
    property_id: str = Field(..., description="Property/MLS listing ID")
    action: str = Field(..., description="Action: 'like' or 'pass'")
    location_id: str = Field(..., description="GHL location/tenant ID")
    feedback: Optional[SwipeFeedback] = Field(None, description="Optional feedback for pass actions")
    time_on_card: Optional[float] = Field(None, description="Seconds spent viewing the property card")


class SwipeResponse(BaseModel):
    """Response model for swipe actions."""

    status: str
    trigger_sms: bool = False
    high_intent: bool = False
    message: Optional[str] = None
    adjustments: Optional[list] = None
    error: Optional[str] = None


@router.post("/swipe", response_model=SwipeResponse)
async def handle_swipe(request: SwipeRequest):
    """
    Handle a swipe action (like or pass) from the client portal.

    **Actions for LIKE:**
    - Tags lead in GHL with 'portal_liked_property' and 'hot_lead'
    - Adds note to contact
    - Detects high-intent behavior (3+ likes in 10 minutes)
    - Triggers speed-to-lead SMS for high intent

    **Actions for PASS:**
    - Logs negative signal to avoid similar properties
    - Updates lead preferences based on feedback
    - Adjusts matching criteria (e.g., lower budget if price too high)

    **Example Request:**
    ```json
    {
      "lead_id": "contact_123",
      "property_id": "mls_998877",
      "action": "like",
      "location_id": "loc_xyz",
      "time_on_card": 12.5
    }
    ```

    **Example Request with Feedback:**
    ```json
    {
      "lead_id": "contact_123",
      "property_id": "mls_554433",
      "action": "pass",
      "location_id": "loc_xyz",
      "feedback": {
        "category": "price_too_high",
        "text": "Way over budget"
      },
      "time_on_card": 5.2
    }
    ```
    """
    logger.info(f"Swipe request: {request.lead_id} -> {request.property_id} ({request.action})")

    try:
        # Validate action
        if request.action not in ["like", "pass"]:
            raise HTTPException(status_code=400, detail=f"Invalid action '{request.action}'. Must be 'like' or 'pass'.")

        action = SwipeAction.LIKE if request.action == "like" else SwipeAction.PASS

        # Convert feedback if present
        feedback_dict = None
        if request.feedback:
            feedback_dict = {
                "category": request.feedback.category,
                "text": request.feedback.text or "",
            }

        # Process the swipe
        result = await swipe_manager.handle_swipe(
            lead_id=request.lead_id,
            property_id=request.property_id,
            action=action,
            location_id=request.location_id,
            feedback=feedback_dict,
            time_on_card=request.time_on_card,
        )

        return SwipeResponse(**result)

    except Exception as e:
        logger.error(f"Error handling swipe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{lead_id}")
async def get_lead_stats(lead_id: str):
    """
    Get swipe statistics for a specific lead.

    Returns:
    - Total interactions
    - Number of likes and passes
    - Like rate percentage
    - Pass reasons breakdown
    - Recent activity indicators

    **Example Response:**
    ```json
    {
      "lead_id": "contact_123",
      "total_interactions": 15,
      "likes": 8,
      "passes": 7,
      "like_rate": 0.53,
      "pass_reasons": {
        "price_too_high": 3,
        "location": 2,
        "style": 2
      },
      "recent_likes_10min": 2
    }
    ```
    """
    logger.info(f"Getting stats for lead: {lead_id}")

    try:
        stats = swipe_manager.get_lead_stats(lead_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting lead stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback-categories")
async def get_feedback_categories():
    """
    Get available feedback categories for pass actions.

    Used by frontend to display feedback options to users.
    """
    return {
        "categories": [
            {"value": FeedbackCategory.PRICE_TOO_HIGH.value, "label": "Price Too High", "icon": "💰"},
            {"value": FeedbackCategory.PRICE_TOO_LOW.value, "label": "Price Too Low", "icon": "💸"},
            {"value": FeedbackCategory.LOCATION.value, "label": "Wrong Location", "icon": "📍"},
            {"value": FeedbackCategory.STYLE.value, "label": "Not My Style", "icon": "🎨"},
            {"value": FeedbackCategory.SIZE_TOO_SMALL.value, "label": "Too Small", "icon": "📏"},
            {"value": FeedbackCategory.SIZE_TOO_LARGE.value, "label": "Too Large", "icon": "📐"},
            {"value": FeedbackCategory.OTHER.value, "label": "Other", "icon": "❓"},
        ]
    }


@router.get("/interactions/{lead_id}")
async def get_lead_interactions(lead_id: str, limit: int = 50):
    """
    Get recent interactions for a specific lead.

    Args:
        lead_id: GHL contact ID
        limit: Maximum number of interactions to return (default: 50)
    """
    logger.info(f"Getting interactions for lead: {lead_id}")

    try:
        # Filter interactions for this lead
        lead_interactions = [i for i in swipe_manager.interactions if i["lead_id"] == lead_id]

        # Sort by timestamp descending (most recent first)
        lead_interactions.sort(key=lambda x: x["timestamp"], reverse=True)

        return {
            "lead_id": lead_id,
            "total": len(lead_interactions),
            "interactions": lead_interactions[:limit],
        }

    except Exception as e:
        logger.error(f"Error getting lead interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deck/{lead_id}")
async def get_smart_deck(lead_id: str, location_id: str, limit: int = 10, min_score: float = 0.5):
    """
    Get a smart, curated deck of properties for a lead.

    This is the **AI Recommendation Engine** that transforms the portal from
    a static list to a dynamic, learning system.

    **Intelligence Features:**
    - Excludes properties already swiped (no repeats)
    - Filters out properties similar to rejected ones
    - Applies learned preferences (budget adjustments, bedroom requirements)
    - Scores and ranks by match quality

    **How It Learns:**
    1. If lead rejects 3+ properties as "too expensive" → Lowers budget by 15%
    2. If lead rejects 2+ as "too small" → Increases bedroom minimum
    3. Tracks negative matches to avoid similar properties

    **Example Request:**
    ```
    GET /api/portal/deck/contact_123?location_id=loc_xyz&limit=10
    ```

    **Example Response:**
    ```json
    {
      "lead_id": "contact_123",
      "location_id": "loc_xyz",
      "properties": [
        {
          "id": "mls_001",
          "price": 485000,
          "beds": 3,
          "baths": 2,
          "sqft": 1850,
          "address": "123 Main St",
          "city": "San Diego",
          "match_score": 0.87,
          "image_url": "https://..."
        }
      ],
      "total_matches": 10,
      "seen_count": 5,
      "preferences_applied": {
        "budget": 500000,
        "bedrooms": 3,
        "location": "San Diego"
      }
    }
    ```

    Args:
        lead_id: GHL contact ID
        location_id: GHL location/tenant ID
        limit: Maximum properties to return (default: 10)
        min_score: Minimum match score 0-1 (default: 0.5)
    """
    logger.info(f"Fetching smart deck for lead: {lead_id}")

    try:
        # Get the smart, curated deck
        deck = await swipe_manager.get_smart_deck(
            lead_id=lead_id, location_id=location_id, limit=limit, min_score=min_score
        )

        # Get seen count for context
        seen_count = len(swipe_manager._get_seen_property_ids(lead_id))

        # Get preferences for transparency
        context = await swipe_manager.memory_service.get_context(lead_id, location_id=location_id)
        preferences = context.get("extracted_preferences", {})

        return {
            "lead_id": lead_id,
            "location_id": location_id,
            "properties": deck,
            "total_matches": len(deck),
            "seen_count": seen_count,
            "preferences_applied": preferences,
        }

    except Exception as e:
        logger.error(f"Error getting smart deck: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/smart-deck")
async def get_smart_deck_legacy(contact_id: str, location_id: Optional[str] = None):
    """
    Legacy compatibility endpoint for SwipeDeck React component.
    """
    try:
        # Use provided location_id or default from settings
        loc_id = location_id or settings.ghl_location_id

        deck = await swipe_manager.get_smart_deck(lead_id=contact_id, location_id=loc_id, limit=10)
        return {"deck": deck}
    except Exception as e:
        logger.error(f"Error in legacy smart deck: {e}")
        raise HTTPException(status_code=500, detail=str(e))
