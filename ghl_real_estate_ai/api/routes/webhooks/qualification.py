"""Qualification and health check endpoints.

Extracted from webhook.py as part of the webhook decomposition.
Handles:
- POST /ghl/initiate-qualification: GHL workflow trigger for lead qualification
- GET /ghl/health: Service health check for deployment platforms
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel

from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookResponse, MessageType
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.security_framework import require_ghl_webhook_signature

from ._helpers import get_ghl_client_default

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ghl",
    tags=["ghl-qualification"],
    dependencies=[Depends(require_ghl_webhook_signature)],
)


class InitiateQualificationRequest(BaseModel):
    contact_id: str
    location_id: str


@router.post("/initiate-qualification")
async def initiate_qualification(
    request: Request,
    body: InitiateQualificationRequest,
    background_tasks: BackgroundTasks,
    ghl_client_default: GHLClient = Depends(get_ghl_client_default),
):
    """
    Called by GHL workflow when 'Needs Qualifying' tag is applied.
    Sends initial outreach message to start qualification.
    """
    contact_id = body.contact_id
    location_id = body.location_id
    try:
        contact_raw = await ghl_client_default.get_contact(contact_id)
        contact = (contact_raw or {}).get("contact", contact_raw or {})
        first_name = contact.get("firstName", "there")
        tags = contact.get("tags", [])

        if "Buyer-Lead" in tags:
            opening = f"{first_name}, glad you reached out! Still searching for a home in Rancho Cucamonga?"
        elif "Seller-Lead" in tags or "Needs Qualifying" in tags:
            opening = f"{first_name}, thanks for connecting. Still thinking about selling your property?"
        else:
            opening = f"{first_name}, thanks for reaching out! Are you looking to buy or sell in Rancho Cucamonga?"

        background_tasks.add_task(
            ghl_client_default.send_message,
            contact_id=contact_id,
            message=opening,
            channel=MessageType.SMS,
        )

        logger.info(
            f"Initiate qualification sent for contact {contact_id}",
            extra={"contact_id": contact_id, "location_id": location_id},
        )

        return GHLWebhookResponse(success=True, message=opening, actions=[])

    except Exception as e:
        logger.error(
            f"Initiate qualification failed for contact {contact_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to initiate qualification"},
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for deployment platform health probes."""
    return {
        "status": "healthy",
        "service": "ghl-real-estate-ai",
        "version": settings.version,
        "environment": settings.environment,
    }
