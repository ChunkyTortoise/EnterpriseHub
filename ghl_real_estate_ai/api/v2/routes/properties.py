"""
V2 Properties API Router
Exposes the Modular Agentic Powerhouse analysis capabilities.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ghl_real_estate_ai.agent_system.v2.conductor import process_request

router = APIRouter()


class PropertyAnalysisRequest(BaseModel):
    address: str = Field(..., example="123 Main St, Rancho Cucamonga, CA")
    market: Optional[str] = Field(default="Rancho Cucamonga, CA")
    request_type: str = Field(default="full_pipeline", description="RESEARCH_ONLY, ANALYZE_ONLY, or FULL_PIPELINE")


@router.post("/analyze")
async def analyze_property(request: PropertyAnalysisRequest):
    """
    Trigger a full agentic analysis of a property.
    Coordinates Research, Analysis, Design, and Executive agents via LangGraph.
    """
    try:
        result = await process_request(address=request.address, request=request.request_type, market=request.market)

        if result.get("errors"):
            # Return partial results if some nodes failed
            return {
                "status": "partial_success"
                if any([result.get("research_data"), result.get("analysis_results")])
                else "failed",
                "address": request.address,
                "research": result.get("research_data"),
                "analysis": result.get("analysis_results"),
                "design": result.get("design_data"),
                "executive": result.get("executive_summary"),
                "errors": result["errors"],
            }

        return {
            "status": "success",
            "address": request.address,
            "research": result.get("research_data"),
            "analysis": result.get("analysis_results"),
            "design": result.get("design_data"),
            "executive": result.get("executive_summary"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    return {"status": "ok", "service": "properties_v2"}
