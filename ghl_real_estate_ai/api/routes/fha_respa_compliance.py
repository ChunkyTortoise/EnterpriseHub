"""
FHA/RESPA Compliance Middleware API Routes

Exposes the compliance enforcement layer for message auditing,
violation scanning, and RESPA disclosure checks.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.compliance_middleware import (
    get_compliance_middleware,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/compliance-enforcement",
    tags=["FHA/RESPA Compliance"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class EnforceRequest(BaseModel):
    message: str = Field(..., description="Outbound message to audit")
    contact_id: str = Field("", description="Contact ID for conversation tracking")
    mode: str = Field("general", description="Bot mode: seller, buyer, or general")
    conversation_context: Optional[Dict[str, Any]] = None


class ViolationDetail(BaseModel):
    category: str
    severity: str
    matched_text: str
    explanation: str


class EnforceResponse(BaseModel):
    status: str
    violations: List[ViolationDetail]
    reason: str
    safe_alternative: Optional[str]
    risk_score: float
    respa_disclosures_needed: List[str]


class BatchEnforceRequest(BaseModel):
    messages: List[EnforceRequest] = Field(..., min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/enforce", response_model=EnforceResponse)
async def enforce_compliance(request: EnforceRequest):
    """Run FHA/RESPA compliance enforcement on an outbound message."""
    try:
        middleware = get_compliance_middleware()
        result = await middleware.enforce(
            message=request.message,
            contact_id=request.contact_id,
            mode=request.mode,
            conversation_context=request.conversation_context,
        )
        return EnforceResponse(
            status=result.status.value,
            violations=[
                ViolationDetail(
                    category=v.category.value,
                    severity=v.severity.value,
                    matched_text=v.matched_text,
                    explanation=v.explanation,
                )
                for v in result.violations
            ],
            reason=result.reason,
            safe_alternative=result.safe_alternative,
            risk_score=result.risk_score,
            respa_disclosures_needed=result.respa_disclosures_needed,
        )
    except Exception as e:
        logger.error("Compliance enforcement failed: %s", e)
        raise HTTPException(500, f"Compliance enforcement error: {e}")


@router.post("/enforce/batch")
async def enforce_compliance_batch(request: BatchEnforceRequest):
    """Run compliance enforcement on multiple messages."""
    try:
        middleware = get_compliance_middleware()
        results = []
        blocked_count = 0
        for msg in request.messages:
            result = await middleware.enforce(
                message=msg.message,
                contact_id=msg.contact_id,
                mode=msg.mode,
                conversation_context=msg.conversation_context,
            )
            if result.status.value in ("BLOCKED", "blocked"):
                blocked_count += 1
            results.append(
                {
                    "contact_id": msg.contact_id,
                    "status": result.status.value,
                    "risk_score": result.risk_score,
                    "violation_count": len(result.violations),
                    "safe_alternative": result.safe_alternative,
                }
            )
        return {
            "results": results,
            "total": len(results),
            "blocked_count": blocked_count,
        }
    except Exception as e:
        logger.error("Batch compliance enforcement failed: %s", e)
        raise HTTPException(500, f"Batch enforcement error: {e}")


@router.delete("/history/{contact_id}")
async def clear_compliance_history(contact_id: str):
    """Clear conversation compliance history for a contact."""
    try:
        middleware = get_compliance_middleware()
        middleware.clear_history(contact_id)
        return {"status": "cleared", "contact_id": contact_id}
    except Exception as e:
        logger.error("Failed to clear compliance history: %s", e)
        raise HTTPException(500, f"Clear history error: {e}")


@router.get("/health")
async def compliance_enforcement_health():
    """Health check for the FHA/RESPA compliance middleware."""
    try:
        middleware = get_compliance_middleware()
        return {
            "status": "healthy",
            "service": "fha_respa_compliance_middleware",
            "pattern_groups": len(middleware.PATTERN_GROUPS),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
