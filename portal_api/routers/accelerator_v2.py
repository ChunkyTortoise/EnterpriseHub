from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from portal_api.accelerator.schemas import (
    IntakeDiagnoseRequest,
    IntakeDiagnosisResponse,
    ProofPackFetchResponse,
    ProofPackGenerationRequest,
    ProofPackGenerationResponse,
    WorkflowBootstrapRequest,
    WorkflowBootstrapResponse,
)
from portal_api.accelerator.service import (
    AcceleratorNotFoundError,
    AcceleratorService,
    AcceleratorValidationError,
    get_accelerator_service,
)
from portal_api.dependencies import require_demo_api_key
from portal_api.models import ApiErrorDetail, ApiErrorResponse

router = APIRouter(prefix="/api/v2", tags=["integration-accelerator"])


@router.post(
    "/intake/diagnose",
    response_model=IntakeDiagnosisResponse,
    dependencies=[Depends(require_demo_api_key)],
    responses={
        401: {"model": ApiErrorResponse, "description": "API key missing or invalid"},
    },
)
async def diagnose_intake(
    request_payload: IntakeDiagnoseRequest,
    service: AcceleratorService = Depends(get_accelerator_service),
) -> IntakeDiagnosisResponse:
    return service.diagnose(request_payload)


@router.post(
    "/workflows/bootstrap",
    response_model=WorkflowBootstrapResponse,
    dependencies=[Depends(require_demo_api_key)],
    responses={
        401: {"model": ApiErrorResponse, "description": "API key missing or invalid"},
        404: {"model": ApiErrorResponse, "description": "Engagement not found"},
    },
)
async def bootstrap_workflow(
    request: Request,
    request_payload: WorkflowBootstrapRequest,
    service: AcceleratorService = Depends(get_accelerator_service),
) -> WorkflowBootstrapResponse | JSONResponse:
    try:
        return service.bootstrap(request_payload)
    except AcceleratorNotFoundError as exc:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="engagement_not_found", message=str(exc), request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=404, content=payload)


@router.post(
    "/reports/proof-pack",
    response_model=ProofPackGenerationResponse,
    dependencies=[Depends(require_demo_api_key)],
    responses={
        401: {"model": ApiErrorResponse, "description": "API key missing or invalid"},
        400: {"model": ApiErrorResponse, "description": "Invalid report request"},
        404: {"model": ApiErrorResponse, "description": "Engagement not found"},
    },
)
async def generate_proof_pack(
    request: Request,
    request_payload: ProofPackGenerationRequest,
    service: AcceleratorService = Depends(get_accelerator_service),
) -> ProofPackGenerationResponse | JSONResponse:
    try:
        return service.generate_proof_pack(request_payload)
    except AcceleratorValidationError as exc:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="invalid_proof_pack_request", message=str(exc), request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=400, content=payload)
    except AcceleratorNotFoundError as exc:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="engagement_not_found", message=str(exc), request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=404, content=payload)
    except ValueError as exc:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="kpi_validation_failed", message=str(exc), request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=400, content=payload)


@router.get(
    "/reports/{engagement_id}",
    response_model=ProofPackFetchResponse,
    responses={
        404: {"model": ApiErrorResponse, "description": "Report not found"},
    },
)
async def get_proof_pack(
    request: Request,
    engagement_id: str,
    service: AcceleratorService = Depends(get_accelerator_service),
) -> ProofPackFetchResponse | JSONResponse:
    try:
        return service.get_proof_pack(engagement_id)
    except AcceleratorNotFoundError as exc:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="report_not_found", message=str(exc), request_id=request_id)
        ).model_dump()
        return JSONResponse(status_code=404, content=payload)
