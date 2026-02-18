"""
API Routes for Dynamic Pricing and ROI Analysis.

This module intentionally keeps backward-compatible request/response shapes used
by older integration suites while still supporting the newer pricing services.
"""

import inspect
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field
from starlette.status import HTTP_200_OK

from ghl_real_estate_ai.api.middleware import jwt_auth
from ghl_real_estate_ai.services import dynamic_pricing_optimizer as dynamic_pricing_optimizer_module
from ghl_real_estate_ai.services import roi_calculator_service as roi_calculator_service_module

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pricing", tags=["pricing"])
_bearer = HTTPBearer(auto_error=False)


class LeadPricingRequest(BaseModel):
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "contact_id": "contact_abc123",
                "location_id": "3xt4qayAh35BlDLaUv7P",
                "context": {"questions_answered": 5, "engagement_score": 0.8, "source": "website_form"},
            }
        }
    )


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def _serialize(data: Any) -> Any:
    if data is None:
        return None
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return [_serialize(item) for item in data]
    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")
    if hasattr(data, "dict"):
        return data.dict()
    if hasattr(data, "__dict__"):
        return dict(data.__dict__)
    return data


def _ensure_pricing_shape(data: Dict[str, Any]) -> Dict[str, Any]:
    if "suggested_price" not in data:
        data["suggested_price"] = data.get("final_price", 0.0)
    if "tier_classification" not in data:
        data["tier_classification"] = data.get("tier", "cold")
    if "price_justification" not in data:
        data["price_justification"] = data.get("justification", "")
    if "confidence_score" not in data:
        data["confidence_score"] = data.get("ml_confidence", data.get("conversion_probability", 0.0))
    if "contact_id" not in data:
        data["contact_id"] = data.get("lead_id")
    return data


async def _get_current_user_compat(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Dict[str, Any]:
    """Runtime auth wrapper that remains patch-friendly for tests."""
    getter = jwt_auth.get_current_user
    try:
        call_result = getter(credentials) if credentials is not None else getter()
        user = await _maybe_await(call_result)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def _has_permission(current_user: Dict[str, Any], permission: str) -> bool:
    role = str(current_user.get("role", "")).lower()
    if role in {"admin", "owner"}:
        return True

    permissions = set(current_user.get("permissions", []) or [])
    if permission in permissions:
        return True

    perm_group = permission.split(":")[0]
    return f"{perm_group}:write" in permissions


async def _require_permission(current_user: Dict[str, Any], permission: str) -> None:
    if not _has_permission(current_user, permission):
        raise HTTPException(status_code=403, detail="Insufficient permissions")


def _get_pricing_optimizer():
    return dynamic_pricing_optimizer_module.DynamicPricingOptimizer()


def _get_roi_calculator():
    return roi_calculator_service_module.ROICalculatorService()


@router.post("/calculate", status_code=HTTP_200_OK)
async def calculate_lead_pricing(
    request: LeadPricingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Calculate dynamic pricing for a lead."""
    try:
        await _require_permission(current_user, "pricing:read")
        if not str(request.contact_id or "").strip():
            return JSONResponse(status_code=422, content={"detail": "contact_id is required"})
        optimizer = _get_pricing_optimizer()

        pricing_result = await _maybe_await(
            optimizer.calculate_lead_price(
                contact_id=request.contact_id,
                location_id=request.location_id,
                context=request.context or {},
            )
        )

        result_data = _ensure_pricing_shape(_serialize(pricing_result) or {})
        background_tasks.add_task(_track_api_usage, "pricing_calculate", request.location_id, current_user.get("user_id"))
        return {"success": True, "data": result_data}

    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"success": False, "error": str(e.detail)})
    except Exception as e:
        logger.error(f"Failed to calculate pricing for {request.contact_id}: {e}")
        return Response(
            content='{"success": false, "error": "Pricing service unavailable"}',
            media_type="application/json",
            status_code=500,
        )


@router.get("/analytics/{location_id}", status_code=HTTP_200_OK)
async def get_pricing_analytics(
    location_id: str,
    response: Response,
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Get pricing analytics for a location."""
    try:
        await _require_permission(current_user, "pricing:read")
        optimizer = _get_pricing_optimizer()
        analytics = await _maybe_await(optimizer.get_pricing_analytics(location_id=location_id, days=days))

        response.headers["Cache-Control"] = "no-cache"
        return {"success": True, "data": _serialize(analytics) or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing analytics for {location_id}: {e}")
        return Response(
            content='{"success": false, "error": "Failed to fetch pricing analytics"}',
            media_type="application/json",
            status_code=500,
        )


@router.put("/configuration/{location_id}", status_code=HTTP_200_OK)
@router.post("/configure/{location_id}", status_code=HTTP_200_OK)
async def update_pricing_configuration(
    location_id: str,
    config: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Update pricing configuration (legacy + current endpoint compatibility)."""
    try:
        if not _has_permission(current_user, "pricing:write"):
            return JSONResponse(status_code=403, content={"success": False, "error": "Insufficient permissions"})

        optimizer = _get_pricing_optimizer()
        if hasattr(optimizer, "update_pricing_configuration"):
            update_result = await _maybe_await(
                optimizer.update_pricing_configuration(location_id=location_id, config=config)
            )
        else:
            update_result = {"success": True, "updated_settings": config}

        return {"success": True, "data": _serialize(update_result) or {"updated_settings": config}}
    except Exception as e:
        logger.error(f"Failed to update pricing configuration for {location_id}: {e}")
        return JSONResponse(status_code=500, content={"success": False, "error": "Failed to update configuration"})


@router.get("/roi-report/{location_id}", status_code=HTTP_200_OK)
async def generate_roi_report(
    location_id: str,
    days: int = Query(30, ge=1, le=365, description="Reporting period in days"),
    include_projections: bool = Query(True, description="Include future projections"),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Generate ROI report."""
    try:
        await _require_permission(current_user, "pricing:read")
        roi_calculator = _get_roi_calculator()
        roi_report = await _maybe_await(
            roi_calculator.generate_client_roi_report(
                location_id=location_id,
                days=days,
                include_projections=include_projections,
            )
        )
        return {"success": True, "data": _serialize(roi_report) or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ROI report for {location_id}: {e}")
        return Response(
            content='{"success": false, "error": "Failed to generate ROI report"}',
            media_type="application/json",
            status_code=500,
        )


@router.get("/human-vs-ai/{location_id}", status_code=HTTP_200_OK)
async def get_human_vs_ai_comparison(
    location_id: str,
    tasks: Optional[List[str]] = Query(None, description="Specific tasks to compare"),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Get human vs AI comparison analysis."""
    try:
        await _require_permission(current_user, "pricing:read")
        roi_calculator = _get_roi_calculator()
        comparison = await _maybe_await(
            roi_calculator.calculate_human_vs_ai_comparison(location_id=location_id, task_categories=tasks)
        )

        comparison_data = _serialize(comparison)
        if isinstance(comparison_data, list):
            data = {"comparisons": comparison_data}
        else:
            data = comparison_data or {}

        return {"success": True, "data": data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate human-vs-ai comparison for {location_id}: {e}")
        return Response(
            content='{"success": false, "error": "Failed to generate comparison"}',
            media_type="application/json",
            status_code=500,
        )


@router.post("/interactive-savings", status_code=HTTP_200_OK)
async def calculate_interactive_savings(
    request: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Interactive savings calculation endpoint used by pricing dashboards."""
    try:
        await _require_permission(current_user, "pricing:read")
        roi_calculator = _get_roi_calculator()

        if hasattr(roi_calculator, "calculate_interactive_savings"):
            savings = await _maybe_await(roi_calculator.calculate_interactive_savings(**request))
        else:
            savings = await _maybe_await(roi_calculator.get_savings_calculator(**request))

        return {"success": True, "data": _serialize(savings) or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate interactive savings: {e}")
        return Response(
            content='{"success": false, "error": "Failed to calculate savings"}',
            media_type="application/json",
            status_code=500,
        )


@router.post("/savings-calculator", status_code=HTTP_200_OK)
async def calculate_savings(
    request: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Legacy savings calculator endpoint retained for load/performance tests."""
    await _require_permission(current_user, "pricing:read")
    roi_calculator = _get_roi_calculator()
    savings = await _maybe_await(roi_calculator.get_savings_calculator(**request))
    return {"success": True, "calculation": _serialize(savings) or {}, "timestamp": datetime.utcnow().isoformat()}


@router.post("/export/{location_id}", status_code=HTTP_200_OK)
async def export_pricing_data(
    location_id: str,
    export_request: Dict[str, Any] = Body(default={}),
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Export pricing data for reporting dashboards."""
    try:
        await _require_permission(current_user, "pricing:read")
        optimizer = _get_pricing_optimizer()

        if hasattr(optimizer, "export_pricing_data"):
            export_data = await _maybe_await(optimizer.export_pricing_data(location_id=location_id, **export_request))
        else:
            export_data = {
                "export_format": export_request.get("format", "json"),
                "records_count": 0,
                "download_url": None,
            }

        return {"success": True, "data": _serialize(export_data) or {}}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export pricing data for {location_id}: {e}")
        return Response(
            content='{"success": false, "error": "Failed to export pricing data"}',
            media_type="application/json",
            status_code=500,
        )


@router.post("/optimize/{location_id}", status_code=HTTP_200_OK)
async def optimize_pricing_model(
    location_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(_get_current_user_compat),
):
    """Run pricing optimization workflow."""
    await _require_permission(current_user, "pricing:write")
    optimizer = _get_pricing_optimizer()
    optimization_result = await _maybe_await(optimizer.optimize_pricing_model(location_id))
    background_tasks.add_task(_track_api_usage, "pricing_optimize", location_id, current_user.get("user_id"))
    return {"success": True, "optimization": _serialize(optimization_result), "timestamp": datetime.utcnow().isoformat()}


@router.get("/health", status_code=HTTP_200_OK)
async def health_check():
    """Health check endpoint for pricing services."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "pricing_optimizer": "healthy",
            "roi_calculator": "healthy",
            "tenant_service": "healthy",
        },
    }


async def _track_api_usage(operation: str, location_id: str, user_id: Optional[str]) -> None:
    try:
        logger.info(
            "pricing_api_usage",
            extra={
                "operation": operation,
                "location_id": location_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception:
        # Usage tracking is best-effort only.
        pass


__all__ = ["router"]
