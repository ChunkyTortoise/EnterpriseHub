from fastapi import APIRouter, Depends, HTTPException

from portal_api.dependencies import Services, get_services
from portal_api.models import ErrorResponse, GHLFieldsResponse, GHLFieldsUnavailableResponse, GHLSyncResponse

router = APIRouter(prefix="/ghl", tags=["ghl"])


@router.post(
    "/sync",
    response_model=GHLSyncResponse,
    responses={
        500: {
            "model": ErrorResponse,
            "description": "GoHighLevel sync failed",
        }
    },
)
async def sync_ghl(services: Services = Depends(get_services)) -> GHLSyncResponse:
    try:
        count = services.ghl.sync_contacts_from_ghl()
        return GHLSyncResponse(status="success", synced_count=count)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/fields", response_model=GHLFieldsResponse | GHLFieldsUnavailableResponse)
async def get_ghl_fields(services: Services = Depends(get_services)) -> GHLFieldsResponse | GHLFieldsUnavailableResponse:
    fields = services.ghl.inspect_custom_fields()
    if not fields:
        return GHLFieldsUnavailableResponse(message="No fields found or API key not configured")
    return GHLFieldsResponse(fields=fields["fields"])
