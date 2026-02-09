"""
SMS compliance webhook endpoints for TCPA opt-out handling.
Provides endpoints for processing incoming SMS messages and managing compliance.
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.auth_service import UserRole, get_current_user
from ghl_real_estate_ai.services.sms_compliance_service import OptOutReason, get_sms_compliance_service

logger = get_logger(__name__)

router = APIRouter(prefix="/sms-compliance", tags=["SMS Compliance"])

# === REQUEST MODELS ===


class IncomingSMSWebhook(BaseModel):
    """Webhook payload for incoming SMS messages."""

    phone_number: str = Field(..., description="Sender's phone number")
    message_body: str = Field(..., description="SMS message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    location_id: Optional[str] = Field(None, description="GHL Location ID")
    contact_id: Optional[str] = Field(None, description="GHL Contact ID")


class SMSValidationRequest(BaseModel):
    """Request to validate SMS send."""

    phone_number: str = Field(..., description="Target phone number")
    message_content: str = Field(..., description="Message to send")
    location_id: Optional[str] = Field(None, description="GHL Location ID")


class OptOutRequest(BaseModel):
    """Request to manually opt out a phone number."""

    phone_number: str = Field(..., description="Phone number to opt out")
    reason: str = Field(..., description="Reason for opt-out")
    notes: Optional[str] = Field(None, description="Additional notes")
    location_id: Optional[str] = Field(None, description="GHL Location ID")


class SMSSendRecord(BaseModel):
    """Record of SMS send for tracking."""

    phone_number: str = Field(..., description="Target phone number")
    message_content: str = Field(..., description="Message content")
    success: bool = Field(..., description="Whether send was successful")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    location_id: Optional[str] = Field(None, description="GHL Location ID")


# === WEBHOOK ENDPOINTS ===


@router.post("/webhook/incoming-sms")
async def handle_incoming_sms_webhook(request: IncomingSMSWebhook):
    """
    Handle incoming SMS webhook from GHL or SMS provider.
    Processes STOP keywords and other compliance actions.
    """
    try:
        compliance_service = get_sms_compliance_service()

        result = await compliance_service.process_incoming_sms(
            phone_number=request.phone_number, message_content=request.message_body, location_id=request.location_id
        )

        logger.info(f"Processed incoming SMS webhook: {result['action']} for {request.phone_number}")

        return {
            "status": "success",
            "action_taken": result["action"],
            "phone_number": result["phone_number"],
            "timestamp": result["timestamp"],
            "details": result,
        }

    except Exception as e:
        logger.error(f"Error processing incoming SMS webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing SMS: {str(e)}")


@router.post("/webhook/opt-out")
async def handle_opt_out_webhook(request: Request):
    """
    Handle opt-out webhook from various sources.
    Supports both JSON and form-encoded payloads.
    """
    try:
        compliance_service = get_sms_compliance_service()

        # Handle both JSON and form data
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            data = await request.json()
        else:
            form_data = await request.form()
            data = dict(form_data)

        phone_number = data.get("phone_number") or data.get("from")
        message_body = data.get("message_body") or data.get("body", "")

        if not phone_number:
            raise HTTPException(status_code=400, detail="Missing phone_number or from field")

        # Process the opt-out request
        result = await compliance_service.process_incoming_sms(
            phone_number=phone_number, message_content=message_body, location_id=data.get("location_id")
        )

        return {"status": "processed", "action": result["action"], "phone_number": result["phone_number"]}

    except Exception as e:
        logger.error(f"Error processing opt-out webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing opt-out: {str(e)}")


# === API ENDPOINTS ===


@router.post("/validate-send")
async def validate_sms_send(request: SMSValidationRequest, current_user: Dict = Depends(get_current_user)):
    """
    Validate SMS send against compliance rules.
    Returns whether send is allowed and compliance details.
    """
    try:
        compliance_service = get_sms_compliance_service()

        result = await compliance_service.validate_sms_send(
            phone_number=request.phone_number, message_content=request.message_content, location_id=request.location_id
        )

        return {
            "allowed": result.allowed,
            "reason": result.reason,
            "daily_count": result.daily_count,
            "monthly_count": result.monthly_count,
            "compliance_notes": result.compliance_notes,
            "validation_timestamp": result.last_sent.isoformat() if result.last_sent else None,
        }

    except Exception as e:
        logger.error(f"Error validating SMS send: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.post("/record-send")
async def record_sms_send(request: SMSSendRecord, current_user: Dict = Depends(get_current_user)):
    """
    Record SMS send for frequency tracking and compliance.
    Should be called after every SMS send attempt.
    """
    try:
        compliance_service = get_sms_compliance_service()

        await compliance_service.record_sms_sent(
            phone_number=request.phone_number,
            message_content=request.message_content,
            success=request.success,
            location_id=request.location_id,
        )

        return {
            "status": "recorded",
            "phone_number": request.phone_number,
            "success": request.success,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error recording SMS send: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recording error: {str(e)}")


@router.post("/manual-opt-out")
async def manual_opt_out(request: OptOutRequest, current_user: Dict = Depends(get_current_user)):
    """
    Manually opt out a phone number.
    Requires admin permissions for compliance oversight.
    """
    try:
        # Check admin permissions
        if current_user.get("role") not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            raise HTTPException(status_code=403, detail="Admin permissions required for manual opt-out")

        compliance_service = get_sms_compliance_service()

        # Map string reason to enum
        reason_map = {
            "user_request": OptOutReason.USER_REQUEST,
            "compliance_violation": OptOutReason.COMPLIANCE_VIOLATION,
            "admin_block": OptOutReason.ADMIN_BLOCK,
            "frequency_abuse": OptOutReason.FREQUENCY_ABUSE,
        }

        reason_enum = reason_map.get(request.reason, OptOutReason.ADMIN_BLOCK)

        await compliance_service.process_opt_out(
            phone_number=request.phone_number,
            reason=reason_enum,
            message_content=request.notes,
            location_id=request.location_id,
        )

        return {
            "status": "opted_out",
            "phone_number": request.phone_number,
            "reason": request.reason,
            "processed_by": current_user.get("username"),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error processing manual opt-out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Opt-out error: {str(e)}")


@router.get("/status/{phone_number}")
async def get_compliance_status(
    phone_number: str = Path(..., description="Phone number to check"), current_user: Dict = Depends(get_current_user)
):
    """
    Get complete compliance status for a phone number.
    Shows opt-out status, frequency counts, and compliance flags.
    """
    try:
        compliance_service = get_sms_compliance_service()

        status = await compliance_service.get_compliance_status(phone_number)

        return status

    except Exception as e:
        logger.error(f"Error getting compliance status for {phone_number}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status error: {str(e)}")


@router.get("/compliance-report")
async def get_compliance_report(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    days: int = Query(7, ge=1, le=30, description="Days to include in report"),
    current_user: Dict = Depends(get_current_user),
):
    """
    Generate compliance report for monitoring and auditing.
    Shows opt-out rates, frequency violations, and compliance trends.
    """
    try:
        # Check admin permissions for compliance reports
        if current_user.get("role") not in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            raise HTTPException(status_code=403, detail="Admin permissions required for compliance reports")

        # TODO: Implement compliance reporting
        # This would query the database for compliance metrics over the specified period

        return {
            "report_period_days": days,
            "location_id": location_id,
            "total_opt_outs": 0,  # TODO: Query database
            "frequency_violations": 0,  # TODO: Query database
            "compliance_score": 100.0,  # TODO: Calculate based on metrics
            "recommendations": [],  # TODO: Generate recommendations
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user.get("username"),
        }

    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report error: {str(e)}")


# === UTILITY ENDPOINTS ===


@router.get("/stop-keywords")
async def get_stop_keywords():
    """Get list of recognized STOP keywords for SMS opt-out."""
    compliance_service = get_sms_compliance_service()

    return {
        "stop_keywords": list(compliance_service.STOP_KEYWORDS),
        "description": "Keywords that trigger automatic SMS opt-out",
        "compliance_standard": "TCPA",
    }


@router.get("/limits")
async def get_sms_limits():
    """Get SMS frequency limits and compliance settings."""
    compliance_service = get_sms_compliance_service()

    return {
        "daily_limit": compliance_service.DAILY_LIMIT,
        "monthly_limit": compliance_service.MONTHLY_LIMIT,
        "business_hours_start": compliance_service.BUSINESS_HOURS_START,
        "business_hours_end": compliance_service.BUSINESS_HOURS_END,
        "compliance_standard": "Industry Standard TCPA Compliance",
    }
