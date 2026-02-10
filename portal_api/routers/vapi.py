import json
from typing import Any, Dict

from fastapi import APIRouter, Depends

from portal_api.dependencies import Services, get_services, require_demo_api_key
from portal_api.models import ApiErrorResponse, VapiToolCallPayload, VapiToolPayload, VapiToolResponse

router = APIRouter(prefix="/vapi/tools", tags=["vapi"])


def _parse_tool_arguments(tool_call: VapiToolCallPayload) -> Dict[str, Any]:
    args = tool_call.function.arguments
    if isinstance(args, str):
        try:
            parsed = json.loads(args)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    if isinstance(args, dict):
        return args
    return {}


@router.post("/check-availability", response_model=VapiToolResponse)
async def vapi_check_availability(payload: VapiToolPayload, services: Services = Depends(get_services)) -> VapiToolResponse:
    tool_call = payload.toolCall
    args = _parse_tool_arguments(tool_call)
    date_query = args.get("date")
    result = services.appointment.check_calendar_availability(date_query)
    return VapiToolResponse(results=[{"toolCallId": tool_call.id, "result": json.dumps(result)}])


@router.post(
    "/book-tour",
    response_model=VapiToolResponse,
    dependencies=[Depends(require_demo_api_key)],
    responses={
        401: {
            "model": ApiErrorResponse,
            "description": "API key missing or invalid",
        }
    },
)
async def vapi_book_tour(payload: VapiToolPayload, services: Services = Depends(get_services)) -> VapiToolResponse:
    tool_call = payload.toolCall
    args = _parse_tool_arguments(tool_call)

    contact_id = args.get("contact_id")
    slot_time = args.get("slot_time")
    property_addr = args.get("property_address", "Private Viewing")
    result = services.appointment.book_tour(contact_id, slot_time, property_addr)

    return VapiToolResponse(results=[{"toolCallId": tool_call.id, "result": json.dumps(result)}])
