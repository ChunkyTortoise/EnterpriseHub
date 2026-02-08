import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.report_generator_service import report_generator_service

logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/dashboard-summary", summary="Generate Dashboard Summary PDF")
async def generate_dashboard_summary(
    date_range: str = Query("Last 24 Hours", description="Date range for the report summary"),
    current_user: dict = Depends(enterprise_auth_service.get_current_enterprise_user),
):
    """
    Generates a PDF summary of the current Enterprise AI Dashboard state.
    Requires authentication.
    """
    try:
        pdf_buffer = await report_generator_service.generate_dashboard_summary_pdf(current_user, date_range)

        filename = f"Enterprise_AI_Dashboard_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        logger.error(f"Failed to generate dashboard summary PDF: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")
