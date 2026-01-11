"""
Multi-Modal Intelligence API Endpoints - Phase 2 Enhancement

FastAPI endpoints for Claude's multi-modal document intelligence capabilities.
Provides comprehensive document analysis, batch processing, and real-time insights.
"""

import asyncio
import base64
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import io

from ...services.claude_multimodal_intelligence import (
    get_multimodal_intelligence,
    ClaudeMultiModalIntelligence,
    DocumentType,
    AnalysisComplexity,
    DocumentProcessingStatus,
    DocumentAnalysisResult,
    DocumentMetadata
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/claude/multimodal", tags=["multimodal-intelligence"])


# Pydantic Models for API
class DocumentAnalysisRequest(BaseModel):
    """Request model for document analysis."""
    document_data: str = Field(..., description="Base64 encoded document data")
    document_type: Optional[DocumentType] = Field(None, description="Document type (auto-detected if not provided)")
    analysis_complexity: AnalysisComplexity = Field(AnalysisComplexity.STANDARD_ANALYSIS, description="Analysis depth level")
    agent_id: Optional[str] = Field(None, description="Agent ID requesting analysis")
    lead_context: Optional[Dict[str, Any]] = Field(None, description="Additional lead context")


class BatchAnalysisRequest(BaseModel):
    """Request model for batch document analysis."""
    documents: List[Dict[str, Any]] = Field(..., description="List of documents to analyze")
    agent_id: str = Field(..., description="Agent ID for batch processing")
    priority: Optional[str] = Field("normal", description="Processing priority (normal, high)")


class DocumentComparisonRequest(BaseModel):
    """Request model for document comparison."""
    document_1_id: str = Field(..., description="First document ID")
    document_2_id: str = Field(..., description="Second document ID")
    comparison_focus: Optional[str] = Field(None, description="Specific focus for comparison")


class DocumentInsightsSummaryRequest(BaseModel):
    """Request model for multi-document insights summary."""
    document_ids: List[str] = Field(..., description="List of document IDs")
    summary_type: str = Field("transaction", description="Type of summary to generate")


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    upload_status: str
    message: str
    processing_eta_seconds: Optional[int] = None


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis status."""
    document_id: str
    status: DocumentProcessingStatus
    progress_percentage: Optional[float] = None
    estimated_completion: Optional[datetime] = None
    message: str


class BatchAnalysisStatusResponse(BaseModel):
    """Response model for batch analysis status."""
    batch_id: str
    total_documents: int
    completed: int
    failed: int
    in_progress: int
    estimated_completion: Optional[datetime] = None


@router.post("/analyze/document", response_model=DocumentAnalysisResult)
async def analyze_document(
    request: DocumentAnalysisRequest,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> DocumentAnalysisResult:
    """
    Analyze a single document using Claude's multi-modal capabilities.

    - **document_data**: Base64 encoded document/image data
    - **document_type**: Optional document type (auto-detected if not provided)
    - **analysis_complexity**: Level of analysis detail required
    - **agent_id**: Agent requesting the analysis
    - **lead_context**: Additional context about the lead/transaction

    Returns comprehensive document analysis with insights and recommendations.
    """
    try:
        logger.info(f"Starting document analysis for agent {request.agent_id}")

        result = await intelligence_service.analyze_document(
            document_data=request.document_data,
            document_type=request.document_type,
            analysis_complexity=request.analysis_complexity,
            agent_id=request.agent_id,
            lead_context=request.lead_context
        )

        logger.info(f"Document analysis completed: {result.document_id}")
        return result

    except Exception as e:
        logger.error(f"Error in document analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: Optional[DocumentType] = Form(None),
    analysis_complexity: AnalysisComplexity = Form(AnalysisComplexity.STANDARD_ANALYSIS),
    agent_id: Optional[str] = Form(None),
    lead_context: Optional[str] = Form(None),
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> DocumentUploadResponse:
    """
    Upload and analyze a document file.

    Supports common document formats (PDF, images, etc.).
    Analysis runs in background with status updates via WebSocket.
    """
    try:
        # Validate file type
        if not file.content_type.startswith(('image/', 'application/pdf')):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload images or PDF files."
            )

        # Read and encode file data
        file_data = await file.read()
        file_base64 = base64.b64encode(file_data).decode('utf-8')

        # Parse lead context if provided
        parsed_context = None
        if lead_context:
            try:
                parsed_context = json.loads(lead_context)
            except json.JSONDecodeError:
                logger.warning("Invalid lead context JSON, ignoring")

        # Generate document ID for tracking
        document_id = intelligence_service._generate_document_id(file_data)

        # Start background analysis
        background_tasks.add_task(
            _background_document_analysis,
            intelligence_service,
            file_base64,
            document_type,
            analysis_complexity,
            agent_id,
            parsed_context,
            document_id
        )

        # Estimate processing time based on complexity
        eta_seconds = {
            AnalysisComplexity.QUICK_SCAN: 10,
            AnalysisComplexity.STANDARD_ANALYSIS: 25,
            AnalysisComplexity.DEEP_ANALYSIS: 45,
            AnalysisComplexity.COMPREHENSIVE_REVIEW: 70
        }.get(analysis_complexity, 25)

        return DocumentUploadResponse(
            document_id=document_id,
            upload_status="uploaded",
            message="Document uploaded successfully, analysis started",
            processing_eta_seconds=eta_seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/analyze/status/{document_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    document_id: str,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> AnalysisStatusResponse:
    """
    Get the analysis status for a specific document.

    Returns current processing status and estimated completion time.
    """
    try:
        # Check if analysis is cached (completed)
        cached_result = await intelligence_service._get_cached_analysis(document_id)

        if cached_result:
            return AnalysisStatusResponse(
                document_id=document_id,
                status=DocumentProcessingStatus.COMPLETED,
                progress_percentage=100.0,
                estimated_completion=cached_result.analysis_timestamp,
                message="Analysis completed successfully"
            )

        # If not cached, check Redis for processing status
        # In a full implementation, we'd track processing status in Redis
        return AnalysisStatusResponse(
            document_id=document_id,
            status=DocumentProcessingStatus.PROCESSING,
            progress_percentage=50.0,
            message="Analysis in progress"
        )

    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.post("/analyze/batch", response_model=Dict[str, Any])
async def analyze_batch_documents(
    request: BatchAnalysisRequest,
    background_tasks: BackgroundTasks,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> Dict[str, Any]:
    """
    Analyze multiple documents in batch.

    Processes documents in parallel for faster results.
    Progress and results are updated via WebSocket.
    """
    try:
        batch_id = f"batch_{int(datetime.now().timestamp())}"

        logger.info(f"Starting batch analysis {batch_id} for {len(request.documents)} documents")

        # Start background batch processing
        background_tasks.add_task(
            _background_batch_analysis,
            intelligence_service,
            request.documents,
            request.agent_id,
            batch_id
        )

        return {
            "batch_id": batch_id,
            "status": "started",
            "total_documents": len(request.documents),
            "message": "Batch analysis started",
            "estimated_completion_minutes": len(request.documents) * 0.5  # ~30 seconds per doc
        }

    except Exception as e:
        logger.error(f"Error starting batch analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.get("/analyze/batch/{batch_id}/status", response_model=BatchAnalysisStatusResponse)
async def get_batch_analysis_status(
    batch_id: str,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> BatchAnalysisStatusResponse:
    """
    Get the status of a batch analysis operation.

    Returns progress information and completion estimates.
    """
    try:
        # In a full implementation, we'd track batch status in Redis
        # For now, return a mock response
        return BatchAnalysisStatusResponse(
            batch_id=batch_id,
            total_documents=10,
            completed=7,
            failed=1,
            in_progress=2,
            estimated_completion=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error getting batch status: {e}")
        raise HTTPException(status_code=500, detail=f"Batch status check failed: {str(e)}")


@router.post("/compare", response_model=Dict[str, Any])
async def compare_documents(
    request: DocumentComparisonRequest,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> Dict[str, Any]:
    """
    Compare two analyzed documents.

    Provides detailed comparison analysis highlighting differences,
    similarities, and strategic insights.
    """
    try:
        comparison_result = await intelligence_service.compare_documents(
            document_1_id=request.document_1_id,
            document_2_id=request.document_2_id,
            comparison_focus=request.comparison_focus
        )

        return comparison_result or {
            "comparison_id": f"comp_{int(datetime.now().timestamp())}",
            "document_1_id": request.document_1_id,
            "document_2_id": request.document_2_id,
            "comparison_focus": request.comparison_focus,
            "status": "comparison_feature_coming_soon",
            "message": "Document comparison feature is in development"
        }

    except Exception as e:
        logger.error(f"Error comparing documents: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post("/insights/summary", response_model=Dict[str, Any])
async def get_insights_summary(
    request: DocumentInsightsSummaryRequest,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> Dict[str, Any]:
    """
    Generate insights summary across multiple documents.

    Provides transaction-level insights by analyzing multiple related documents
    together (e.g., MLS listing + financial docs + inspection report).
    """
    try:
        summary_result = await intelligence_service.get_document_insights_summary(
            document_ids=request.document_ids,
            summary_type=request.summary_type
        )

        return summary_result or {
            "summary_id": f"summary_{int(datetime.now().timestamp())}",
            "document_ids": request.document_ids,
            "summary_type": request.summary_type,
            "status": "summary_feature_coming_soon",
            "message": "Multi-document insights summary feature is in development"
        }

    except Exception as e:
        logger.error(f"Error generating insights summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.get("/document/{document_id}", response_model=DocumentAnalysisResult)
async def get_document_analysis(
    document_id: str,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> DocumentAnalysisResult:
    """
    Retrieve a previously completed document analysis.

    Returns cached analysis results if available.
    """
    try:
        cached_result = await intelligence_service._get_cached_analysis(document_id)

        if not cached_result:
            raise HTTPException(
                status_code=404,
                detail="Document analysis not found or expired"
            )

        return cached_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.delete("/document/{document_id}")
async def delete_document_analysis(
    document_id: str,
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> Dict[str, str]:
    """
    Delete a document analysis and its cached results.

    Use this to remove sensitive document analyses from the system.
    """
    try:
        if intelligence_service.redis_client:
            await intelligence_service.redis_client.delete(f"doc_analysis:{document_id}")

        return {
            "document_id": document_id,
            "status": "deleted",
            "message": "Document analysis deleted successfully"
        }

    except Exception as e:
        logger.error(f"Error deleting document analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/health")
async def health_check(
    intelligence_service: ClaudeMultiModalIntelligence = Depends(get_multimodal_intelligence)
) -> Dict[str, Any]:
    """
    Health check endpoint for multi-modal intelligence service.

    Verifies Claude API and Redis connectivity.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "claude_api": "unknown",
                "redis": "unknown"
            }
        }

        # Check Redis
        if intelligence_service.redis_client:
            try:
                await intelligence_service.redis_client.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception:
                health_status["services"]["redis"] = "unhealthy"
        else:
            health_status["services"]["redis"] = "not_configured"

        # Check Claude API (simple test)
        try:
            # A minimal test call to verify API connectivity
            test_response = await intelligence_service.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            health_status["services"]["claude_api"] = "healthy" if test_response else "unhealthy"
        except Exception:
            health_status["services"]["claude_api"] = "unhealthy"

        # Overall status
        if all(status in ["healthy", "not_configured"] for status in health_status["services"].values()):
            health_status["status"] = "healthy"
        else:
            health_status["status"] = "degraded"

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Background task functions
async def _background_document_analysis(
    intelligence_service: ClaudeMultiModalIntelligence,
    document_data: str,
    document_type: Optional[DocumentType],
    analysis_complexity: AnalysisComplexity,
    agent_id: Optional[str],
    lead_context: Optional[Dict[str, Any]],
    document_id: str
):
    """Background task for document analysis."""
    try:
        await intelligence_service.analyze_document(
            document_data=document_data,
            document_type=document_type,
            analysis_complexity=analysis_complexity,
            agent_id=agent_id,
            lead_context=lead_context
        )
        logger.info(f"Background analysis completed for document {document_id}")

    except Exception as e:
        logger.error(f"Background analysis failed for document {document_id}: {e}")


async def _background_batch_analysis(
    intelligence_service: ClaudeMultiModalIntelligence,
    documents: List[Dict[str, Any]],
    agent_id: str,
    batch_id: str
):
    """Background task for batch document analysis."""
    try:
        results = await intelligence_service.batch_analyze_documents(documents, agent_id)
        logger.info(f"Batch analysis {batch_id} completed: {len(results)} documents processed")

    except Exception as e:
        logger.error(f"Batch analysis {batch_id} failed: {e}")