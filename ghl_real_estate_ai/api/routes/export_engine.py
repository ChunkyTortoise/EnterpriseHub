"""
Professional Export Engine API Routes

Exposes branded report generation, CMA reports, lead CSV exports,
and client presentation creation.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware import get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.professional_export_engine import (
    get_export_engine,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/exports",
    tags=["Professional Exports"],
    dependencies=[Depends(get_current_user)],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class MarketReportRequest(BaseModel):
    neighborhood: str = Field(..., description="Neighborhood name")
    report_type: str = Field("monthly", description="Report type: monthly, weekly")
    market_data: Optional[Dict[str, Any]] = Field(None, description="Custom market data override")
    format: str = Field("html", description="Output format: html, csv, text")


class CMAReportRequest(BaseModel):
    address: str = Field(..., description="Subject property address")
    property_data: Dict[str, Any] = Field(..., description="Property details (bedrooms, bathrooms, sqft, etc.)")
    comparables: List[Dict[str, Any]] = Field(..., min_length=1, description="Comparable properties")
    format: str = Field("html", description="Output format: html, text")


class LeadExportRequest(BaseModel):
    leads: List[Dict[str, Any]] = Field(..., description="Lead data to export")


class PresentationRequest(BaseModel):
    client_name: str = Field(..., description="Client name")
    sections: List[Dict[str, str]] = Field(..., min_length=1, description="Presentation sections [{title, content}]")


class ExportResponse(BaseModel):
    report_id: str
    report_type: str
    format: str
    filename: str
    size_bytes: int
    content: str
    metadata: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/market-report", response_model=ExportResponse)
async def generate_market_report(request: MarketReportRequest):
    """Generate a branded market report for a neighborhood."""
    try:
        engine = get_export_engine()
        result = await engine.generate_market_report(
            neighborhood=request.neighborhood,
            report_type=request.report_type,
            market_data=request.market_data,
            format=request.format,
        )
        return ExportResponse(
            report_id=result.report_id,
            report_type=result.report_type.value,
            format=result.format.value,
            filename=result.filename,
            size_bytes=result.size_bytes,
            content=result.content,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error("Market report generation failed: %s", e)
        raise HTTPException(500, "Report generation failed")


@router.post("/market-report/render")
async def render_market_report(request: MarketReportRequest):
    """Generate and render a market report as HTML."""
    try:
        engine = get_export_engine()
        result = await engine.generate_market_report(
            neighborhood=request.neighborhood,
            report_type=request.report_type,
            market_data=request.market_data,
            format="html",
        )
        return HTMLResponse(content=result.content)
    except Exception as e:
        logger.error("Market report rendering failed: %s", e)
        raise HTTPException(500, "Report rendering failed")


@router.post("/cma-report", response_model=ExportResponse)
async def generate_cma_report(request: CMAReportRequest):
    """Generate a Comparative Market Analysis report."""
    try:
        engine = get_export_engine()
        result = await engine.generate_cma_report(
            address=request.address,
            property_data=request.property_data,
            comparables=request.comparables,
            format=request.format,
        )
        return ExportResponse(
            report_id=result.report_id,
            report_type=result.report_type.value,
            format=result.format.value,
            filename=result.filename,
            size_bytes=result.size_bytes,
            content=result.content,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error("CMA report generation failed: %s", e)
        raise HTTPException(500, "CMA report generation failed")


@router.post("/leads-csv", response_model=ExportResponse)
async def export_leads_csv(request: LeadExportRequest):
    """Export leads data as CSV."""
    try:
        engine = get_export_engine()
        result = await engine.export_leads_csv(leads=request.leads)
        return ExportResponse(
            report_id=result.report_id,
            report_type=result.report_type.value,
            format=result.format.value,
            filename=result.filename,
            size_bytes=result.size_bytes,
            content=result.content,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error("Lead CSV export failed: %s", e)
        raise HTTPException(500, "Lead export failed")


@router.post("/presentation", response_model=ExportResponse)
async def generate_presentation(request: PresentationRequest):
    """Generate an HTML client presentation."""
    try:
        engine = get_export_engine()
        result = await engine.generate_presentation(
            client_name=request.client_name,
            sections=request.sections,
        )
        return ExportResponse(
            report_id=result.report_id,
            report_type=result.report_type.value,
            format=result.format.value,
            filename=result.filename,
            size_bytes=result.size_bytes,
            content=result.content,
            metadata=result.metadata,
        )
    except Exception as e:
        logger.error("Presentation generation failed: %s", e)
        raise HTTPException(500, "Presentation generation failed")


@router.get("/health")
async def export_health():
    """Health check for the professional export engine."""
    try:
        engine = get_export_engine()
        return {
            "status": "healthy",
            "service": "professional_export_engine",
            "branding": {
                "agent": engine.branding.agent_name,
                "brokerage": engine.branding.brokerage,
            },
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
