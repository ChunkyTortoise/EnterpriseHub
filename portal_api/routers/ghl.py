from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from portal_api.dependencies import Services, get_services, require_demo_api_key
from portal_api.models import (
    ApiErrorDetail,
    ApiErrorResponse,
    GHLFieldsResponse,
    GHLFieldsUnavailableResponse,
    GHLSyncResponse,
)

router = APIRouter(prefix="/ghl", tags=["ghl"])


@router.post(
    "/sync",
    response_model=GHLSyncResponse,
    dependencies=[Depends(require_demo_api_key)],
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "API key missing or invalid",
        },
        500: {
            "model": ApiErrorResponse,
            "description": "GoHighLevel sync failed",
        }
    },
)
async def sync_ghl(request: Request, services: Services = Depends(get_services)) -> GHLSyncResponse | JSONResponse:
    try:
        count = services.ghl.sync_contacts_from_ghl()
        return GHLSyncResponse(status="success", synced_count=count)
    except Exception:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="ghl_sync_failed", message="GoHighLevel sync failed", request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=500, content=payload)


@router.get("/fields", response_model=GHLFieldsResponse | GHLFieldsUnavailableResponse)
async def get_ghl_fields(services: Services = Depends(get_services)) -> GHLFieldsResponse | GHLFieldsUnavailableResponse:
    fields = services.ghl.inspect_custom_fields()
    if not fields:
        return GHLFieldsUnavailableResponse(message="No fields found or API key not configured")
    return GHLFieldsResponse(fields=fields["fields"])
