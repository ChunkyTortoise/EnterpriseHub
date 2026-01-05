"""
Bulk Operations API Routes for Phase 2.

Provides endpoints for:
- Bulk lead import/export
- Bulk SMS campaigns
- Data migration tools
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import json
import csv
import io

from ghl_real_estate_ai.services.bulk_operations import BulkOperationsManager
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/bulk", tags=["bulk-operations"])


# Request/Response Models
class BulkImportRequest(BaseModel):
    """Request model for bulk lead import."""
    leads: List[Dict[str, Any]] = Field(..., description="List of leads to import")
    tags: Optional[List[str]] = Field(default=None, description="Tags to apply to all leads")
    campaign_id: Optional[str] = Field(default=None, description="Campaign to associate leads with")


class BulkSMSRequest(BaseModel):
    """Request model for bulk SMS campaign."""
    contact_ids: List[str] = Field(..., description="List of contact IDs to message")
    message: str = Field(..., max_length=160, description="SMS message (max 160 chars)")
    schedule_at: Optional[str] = Field(default=None, description="ISO timestamp to schedule send")


class BulkTagRequest(BaseModel):
    """Request model for bulk tagging."""
    contact_ids: List[str] = Field(..., description="List of contact IDs")
    tags_to_add: Optional[List[str]] = Field(default=None, description="Tags to add")
    tags_to_remove: Optional[List[str]] = Field(default=None, description="Tags to remove")


class BulkExportRequest(BaseModel):
    """Request model for bulk export."""
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters to apply")
    fields: Optional[List[str]] = Field(default=None, description="Fields to include in export")


class OperationStatus(BaseModel):
    """Response model for operation status."""
    operation_id: str
    status: str  # pending, processing, completed, failed
    total_items: int
    processed_items: int
    failed_items: int
    errors: List[str]
    started_at: str
    completed_at: Optional[str] = None


# Bulk Import Endpoints
@router.post("/import", status_code=202)
async def bulk_import_leads(
    location_id: str,
    request: BulkImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Import multiple leads in bulk.
    
    Accepts a list of lead objects and imports them into GHL.
    Operation runs in background and returns operation ID for tracking.
    """
    try:
        bulk_ops = BulkOperationsManager(location_id)
        
        operation_id = await bulk_ops.import_leads(
            leads=request.leads,
            tags=request.tags,
            campaign_id=request.campaign_id
        )
        
        logger.info(f"Started bulk import operation {operation_id} with {len(request.leads)} leads")
        
        return {
            "operation_id": operation_id,
            "status": "processing",
            "message": f"Importing {len(request.leads)} leads",
            "total_items": len(request.leads)
        }
        
    except Exception as e:
        logger.error(f"Error starting bulk import: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start import: {str(e)}")


@router.post("/import/csv", status_code=202)
async def bulk_import_csv(
    location_id: str,
    file: UploadFile = File(...),
    tags: Optional[str] = Query(default=None, description="Comma-separated tags to apply"),
    background_tasks: BackgroundTasks = None
):
    """
    Import leads from CSV file.
    
    CSV should have columns: first_name, last_name, phone, email, etc.
    """
    try:
        # Read CSV file
        contents = await file.read()
        csv_data = io.StringIO(contents.decode('utf-8'))
        reader = csv.DictReader(csv_data)
        
        leads = list(reader)
        
        if not leads:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        
        # Parse tags
        tags_list = [t.strip() for t in tags.split(",")] if tags else None
        
        # Start import
        bulk_ops = BulkOperationsManager(location_id)
        operation_id = await bulk_ops.import_leads(
            leads=leads,
            tags=tags_list
        )
        
        logger.info(f"Started CSV import operation {operation_id} with {len(leads)} leads")
        
        return {
            "operation_id": operation_id,
            "status": "processing",
            "message": f"Importing {len(leads)} leads from CSV",
            "total_items": len(leads),
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error importing CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import CSV: {str(e)}")


# Bulk Export Endpoints
@router.post("/export")
async def bulk_export_leads(
    location_id: str,
    request: BulkExportRequest
):
    """
    Export leads to JSON.
    
    Returns a JSON file with filtered leads based on provided criteria.
    """
    try:
        bulk_ops = BulkOperationsManager(location_id)
        
        leads = await bulk_ops.export_leads(
            filters=request.filters,
            fields=request.fields
        )
        
        # Create JSON response
        json_data = json.dumps(leads, indent=2)
        
        return StreamingResponse(
            io.BytesIO(json_data.encode()),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting leads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export leads: {str(e)}")


@router.post("/export/csv")
async def bulk_export_csv(
    location_id: str,
    request: BulkExportRequest
):
    """
    Export leads to CSV.
    
    Returns a CSV file with filtered leads based on provided criteria.
    """
    try:
        bulk_ops = BulkOperationsManager(location_id)
        
        leads = await bulk_ops.export_leads(
            filters=request.filters,
            fields=request.fields
        )
        
        if not leads:
            raise HTTPException(status_code=404, detail="No leads found matching criteria")
        
        # Create CSV
        output = io.StringIO()
        if leads:
            fieldnames = leads[0].keys()
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(leads)
        
        csv_data = output.getvalue()
        
        return StreamingResponse(
            io.BytesIO(csv_data.encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=leads_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


# Bulk SMS Campaign Endpoints
@router.post("/sms/campaign", status_code=202)
async def create_bulk_sms_campaign(
    location_id: str,
    request: BulkSMSRequest,
    background_tasks: BackgroundTasks
):
    """
    Send SMS to multiple contacts.
    
    Sends the same message to all specified contacts.
    Respects 160-character SMS limit.
    """
    try:
        if len(request.message) > 160:
            raise HTTPException(
                status_code=400,
                detail=f"Message exceeds 160 characters (current: {len(request.message)})"
            )
        
        bulk_ops = BulkOperationsManager(location_id)
        
        operation_id = await bulk_ops.send_bulk_sms(
            contact_ids=request.contact_ids,
            message=request.message,
            schedule_at=request.schedule_at
        )
        
        logger.info(f"Started bulk SMS campaign {operation_id} for {len(request.contact_ids)} contacts")
        
        return {
            "operation_id": operation_id,
            "status": "processing" if not request.schedule_at else "scheduled",
            "message": f"Sending SMS to {len(request.contact_ids)} contacts",
            "total_recipients": len(request.contact_ids),
            "scheduled_at": request.schedule_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating SMS campaign: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create SMS campaign: {str(e)}")


# Bulk Tagging Endpoints
@router.post("/tags/apply", status_code=202)
async def bulk_apply_tags(
    location_id: str,
    request: BulkTagRequest,
    background_tasks: BackgroundTasks
):
    """
    Apply or remove tags from multiple contacts.
    
    Supports both adding and removing tags in a single operation.
    """
    try:
        if not request.tags_to_add and not request.tags_to_remove:
            raise HTTPException(
                status_code=400,
                detail="Must specify either tags_to_add or tags_to_remove"
            )
        
        bulk_ops = BulkOperationsManager(location_id)
        
        operation_id = await bulk_ops.apply_bulk_tags(
            contact_ids=request.contact_ids,
            tags_to_add=request.tags_to_add,
            tags_to_remove=request.tags_to_remove
        )
        
        logger.info(f"Started bulk tag operation {operation_id} for {len(request.contact_ids)} contacts")
        
        return {
            "operation_id": operation_id,
            "status": "processing",
            "message": f"Updating tags for {len(request.contact_ids)} contacts",
            "total_contacts": len(request.contact_ids)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying bulk tags: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply tags: {str(e)}")


# Operation Status Endpoints
@router.get("/operations/{operation_id}", response_model=OperationStatus)
async def get_operation_status(location_id: str, operation_id: str):
    """
    Get status of a bulk operation.
    
    Track progress and errors for import, export, or bulk action operations.
    """
    try:
        bulk_ops = BulkOperationsManager(location_id)
        status = await bulk_ops.get_operation_status(operation_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Operation not found")
        
        return OperationStatus(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching operation status: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch status: {str(e)}")


@router.get("/operations/{location_id}/list")
async def list_operations(
    location_id: str,
    status: Optional[str] = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, description="Max operations to return")
):
    """
    List bulk operations for a location.
    """
    try:
        bulk_ops = BulkOperationsManager(location_id)
        operations = await bulk_ops.list_operations(status=status, limit=limit)
        
        return {
            "location_id": location_id,
            "operations": operations,
            "count": len(operations)
        }
        
    except Exception as e:
        logger.error(f"Error listing operations: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list operations: {str(e)}")


# Health check
@router.get("/health")
async def bulk_operations_health():
    """Health check for bulk operations endpoints."""
    return {
        "status": "healthy",
        "service": "bulk-operations",
        "timestamp": datetime.now().isoformat()
    }
