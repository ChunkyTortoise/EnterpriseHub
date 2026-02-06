"""
Processing Pipeline Orchestrator

Enterprise integration layer that orchestrates all Phase 2 components:
- BulkProcessor for distributed document processing
- QualityAssurance for multi-dimensional validation
- HumanReviewQueue for priority-based review management
- VersionControl for audit trail and lineage tracking

Provides unified API for the complete autonomous document processing workflow
with enterprise-grade reliability, monitoring, and compliance.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
import uuid
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Import all Phase 2 components
from .bulk_processor import BulkProcessor, ProcessingMetrics
from .quality_assurance import QualityAssurance, ValidationResult, QualityScores
from .human_review_queue import HumanReviewQueue, ReviewPriority, ReviewType
from .version_control import VersionControl, VersionChangeType

# Import database schema
from .database_schema import (
    DocumentVersion, BatchJob, QualityMetrics, ReviewAssignment, AuditTrail,
    ProcessingStatus, QueueType, AuditEventType, create_tables
)

# Import configuration
from ..config.settings import settings

# Import EnterpriseHub patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class PipelineStatus(Enum):
    """Overall pipeline status for monitoring."""
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

class WorkflowStage(Enum):
    """Document workflow stages through the pipeline."""
    INGESTION = "ingestion"
    PARSING = "parsing"
    LEGAL_ANALYSIS = "legal_analysis"
    CITATION_TRACKING = "citation_tracking"
    RISK_ASSESSMENT = "risk_assessment"
    QUALITY_VALIDATION = "quality_validation"
    HUMAN_REVIEW = "human_review"
    VERSION_CONTROL = "version_control"
    COMPLETION = "completion"

@dataclass
class PipelineConfiguration:
    """Pipeline configuration with business rules and thresholds."""
    
    # Processing configuration
    max_concurrent_documents: int = 1000
    batch_size: int = 100
    processing_timeout_minutes: int = 30
    
    # Quality thresholds
    auto_approval_confidence: float = 0.95
    quality_review_confidence: float = 0.85
    human_review_confidence: float = 0.75
    rejection_confidence: float = 0.50
    
    # Review configuration
    enable_human_review: bool = True
    enable_quality_checks: bool = True
    enable_version_control: bool = True
    
    # SLA targets (in hours)
    critical_document_sla: float = 2.0
    standard_document_sla: float = 8.0
    batch_completion_sla: float = 24.0
    
    # Monitoring thresholds
    error_rate_threshold: float = 0.05  # 5%
    queue_depth_alert_threshold: int = 100
    processing_time_alert_threshold: float = 10.0  # seconds
    
    # Compliance settings
    audit_retention_days: int = 2555  # 7 years
    enable_audit_logging: bool = True
    compliance_mode: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "max_concurrent_documents": self.max_concurrent_documents,
            "batch_size": self.batch_size,
            "processing_timeout_minutes": self.processing_timeout_minutes,
            "auto_approval_confidence": self.auto_approval_confidence,
            "quality_review_confidence": self.quality_review_confidence,
            "human_review_confidence": self.human_review_confidence,
            "rejection_confidence": self.rejection_confidence,
            "enable_human_review": self.enable_human_review,
            "enable_quality_checks": self.enable_quality_checks,
            "enable_version_control": self.enable_version_control,
            "critical_document_sla": self.critical_document_sla,
            "standard_document_sla": self.standard_document_sla,
            "batch_completion_sla": self.batch_completion_sla,
            "error_rate_threshold": self.error_rate_threshold,
            "queue_depth_alert_threshold": self.queue_depth_alert_threshold,
            "processing_time_alert_threshold": self.processing_time_alert_threshold,
            "audit_retention_days": self.audit_retention_days,
            "enable_audit_logging": self.enable_audit_logging,
            "compliance_mode": self.compliance_mode
        }

@dataclass
class PipelineMetrics:
    """Comprehensive pipeline performance metrics."""
    
    # Processing metrics
    total_documents_processed: int = 0
    documents_in_progress: int = 0
    documents_completed: int = 0
    documents_failed: int = 0
    
    # Throughput metrics
    documents_per_hour: float = 0.0
    average_processing_time_seconds: float = 0.0
    queue_depth_by_priority: Dict[str, int] = field(default_factory=dict)
    
    # Quality metrics
    average_confidence_score: float = 0.0
    auto_approval_rate: float = 0.0
    human_review_rate: float = 0.0
    rejection_rate: float = 0.0
    
    # SLA metrics
    sla_compliance_rate: float = 0.0
    average_completion_time_hours: float = 0.0
    overdue_documents: int = 0
    
    # Error metrics
    error_rate: float = 0.0
    critical_errors: int = 0
    recoverable_errors: int = 0
    
    # Resource metrics
    worker_utilization: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_utilization: float = 0.0
    
    # Timestamp
    last_updated: datetime = field(default_factory=datetime.utcnow)

class ProcessingPipelineOrchestrator:
    """
    Enterprise processing pipeline orchestrator that coordinates all Phase 2 components
    for scalable, reliable, and compliant document processing.
    
    Features:
    - Unified API for complete document processing workflow
    - Enterprise-scale processing (1,000+ concurrent documents)
    - Multi-dimensional quality validation and routing
    - Priority-based human review management
    - Complete audit trail and version control
    - Real-time monitoring and health checks
    - Compliance-grade logging and retention
    """
    
    def __init__(
        self,
        config: PipelineConfiguration = None,
        db_url: str = None,
        cache_service: CacheService = None
    ):
        """Initialize the processing pipeline orchestrator."""
        
        self.config = config or PipelineConfiguration()
        
        # Database setup
        db_url = db_url or settings.database_url
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=30,
            max_overflow=50,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        # Create database tables if they don't exist
        create_tables(self.engine)
        
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = SessionLocal()
        
        # Initialize infrastructure
        self.cache_service = cache_service or CacheService()
        self.audit_logger = AuditLogger()
        
        # Initialize Phase 2 components
        self.bulk_processor = BulkProcessor(
            db_session=self.db_session
        )
        self.quality_assurance = QualityAssurance(
            cache_service=self.cache_service
        )
        self.human_review_queue = HumanReviewQueue(
            db_session=self.db_session,
            cache_service=self.cache_service
        )
        self.version_control = VersionControl(
            db_session=self.db_session,
            cache_service=self.cache_service
        )
        
        # Pipeline state
        self.is_initialized = False
        self.status = PipelineStatus.HEALTHY
        self.metrics = PipelineMetrics()
        self.active_workflows: Dict[str, WorkflowStage] = {}
        
        # Monitoring
        self.monitoring_active = False
        self.health_check_interval = 60  # seconds
        self.metrics_update_interval = 300  # 5 minutes
        
        logger.info("ProcessingPipelineOrchestrator initialized")
    
    async def initialize(self, reviewer_configs: List[Dict[str, Any]] = None) -> bool:
        """
        Initialize the processing pipeline with all components.
        
        Args:
            reviewer_configs: List of reviewer configurations for human review queue
            
        Returns:
            success: Whether initialization completed successfully
        """
        
        try:
            # Initialize human review queue with reviewers
            if reviewer_configs:
                await self.human_review_queue.initialize_reviewers(reviewer_configs)
            else:
                # Default reviewer configuration
                default_reviewers = [
                    {
                        "reviewer_id": "system_paralegal",
                        "role": "paralegal",
                        "max_concurrent": 15,
                        "specializations": ["contracts", "general"]
                    },
                    {
                        "reviewer_id": "system_associate",
                        "role": "associate", 
                        "max_concurrent": 10,
                        "specializations": ["complex_contracts", "compliance"]
                    },
                    {
                        "reviewer_id": "system_partner",
                        "role": "partner",
                        "max_concurrent": 5,
                        "specializations": ["high_risk", "executive_review"]
                    }
                ]
                await self.human_review_queue.initialize_reviewers(default_reviewers)
            
            # Start monitoring tasks
            await self._start_monitoring()
            
            # Perform initial health check
            health_status = await self.get_system_health()
            
            if health_status["overall_healthy"]:
                self.is_initialized = True
                self.status = PipelineStatus.HEALTHY
                
                logger.info("Processing pipeline initialized successfully")
                
                # Audit log initialization
                await self.audit_logger.log_event(
                    event_type=AuditEventType.PROCESSING_STARTED,
                    event_description="Processing pipeline initialized",
                    event_data={
                        "configuration": self.config.to_dict(),
                        "reviewers_configured": len(reviewer_configs) if reviewer_configs else 3,
                        "system_health": health_status
                    }
                )
                
                return True
            else:
                logger.error("Pipeline initialization failed - system health check failed")
                self.status = PipelineStatus.UNHEALTHY
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize processing pipeline: {e}")
            self.status = PipelineStatus.UNHEALTHY
            return False
    
    async def process_document_batch(
        self,
        file_paths: List[str],
        batch_metadata: Dict[str, Any] = None,
        client_id: str = None,
        matter_id: str = None,
        priority: float = 0.5,
        callback: Callable[[Dict[str, Any]], None] = None
    ) -> str:
        """
        Process a batch of documents through the complete pipeline.
        
        Args:
            file_paths: List of document file paths to process
            batch_metadata: Additional batch metadata
            client_id: Client identifier for multi-tenancy
            matter_id: Matter identifier for legal case tracking
            priority: Processing priority (0.0 = low, 1.0 = critical)
            callback: Optional callback for real-time progress updates
            
        Returns:
            batch_id: Unique batch identifier for tracking
        """
        
        if not self.is_initialized:
            raise RuntimeError("Pipeline not initialized - call initialize() first")
        
        if len(file_paths) > self.config.max_concurrent_documents:
            raise ValueError(f"Batch size {len(file_paths)} exceeds maximum {self.config.max_concurrent_documents}")
        
        # Generate batch metadata
        batch_name = batch_metadata.get("name") if batch_metadata else f"Batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Start bulk processing with integrated pipeline workflow
            batch_id = await self.bulk_processor.process_document_batch(
                file_paths=file_paths,
                batch_name=batch_name,
                client_id=client_id,
                matter_id=matter_id,
                priority=priority,
                callback=self._create_pipeline_callback(callback)
            )
            
            # Track workflow
            self.active_workflows[batch_id] = WorkflowStage.PARSING
            
            logger.info(
                f"Started pipeline processing for batch {batch_id} "
                f"with {len(file_paths)} documents"
            )
            
            return batch_id
            
        except Exception as e:
            logger.error(f"Failed to start batch processing: {e}")
            raise
    
    def _create_pipeline_callback(self, user_callback: Callable = None) -> Callable:
        """Create pipeline callback that handles workflow orchestration."""
        
        async def pipeline_callback(metrics: ProcessingMetrics):
            """Handle document processing callbacks and route to next stages."""
            
            try:
                batch_id = metrics.batch_id
                
                # Update workflow stage
                if metrics.progress_percentage >= 100.0:
                    self.active_workflows[batch_id] = WorkflowStage.QUALITY_VALIDATION
                    
                    # Process completed documents through quality assurance
                    await self._process_quality_validation(batch_id)
                
                # Call user callback if provided
                if user_callback:
                    pipeline_metrics = await self._convert_to_pipeline_metrics(metrics)
                    user_callback(pipeline_metrics)
                    
            except Exception as e:
                logger.error(f"Pipeline callback error for batch {metrics.batch_id}: {e}")
        
        return pipeline_callback
    
    async def _process_quality_validation(self, batch_id: str):
        """Process documents through quality validation stage."""
        
        try:
            # Get completed documents from batch
            completed_docs = self.db_session.query(DocumentVersion).filter(
                and_(
                    DocumentVersion.batch_job_id == batch_id,
                    DocumentVersion.processing_status == ProcessingStatus.COMPLETED
                )
            ).all()
            
            for doc_version in completed_docs:
                # Quality validation
                if self.config.enable_quality_checks:
                    validation_result = await self._validate_document_quality(doc_version)
                    
                    # Route based on quality results
                    await self._route_document_after_quality(doc_version, validation_result)
                else:
                    # Skip quality checks - mark as approved
                    doc_version.processing_status = ProcessingStatus.APPROVED
                    
                    if self.config.enable_version_control:
                        await self.version_control.create_version_snapshot(
                            doc_version,
                            change_type=VersionChangeType.QUALITY_UPDATE,
                            changes_summary="Quality validation bypassed"
                        )
            
            self.db_session.commit()
            
            # Update workflow stage
            self.active_workflows[batch_id] = WorkflowStage.COMPLETION
            
            logger.info(f"Quality validation completed for batch {batch_id}")
            
        except Exception as e:
            logger.error(f"Quality validation failed for batch {batch_id}: {e}")
            raise
    
    async def _validate_document_quality(self, doc_version: DocumentVersion) -> ValidationResult:
        """Validate document quality using QualityAssurance component."""
        
        # Note: In a full implementation, we would reconstruct the Phase 1 objects
        # For now, we'll work with the stored JSON data
        
        # Mock Phase 1 objects from stored data (simplified)
        class MockParsedDoc:
            def __init__(self, parsing_results):
                self.confidence_score = parsing_results.get("confidence_score", 0.8)
                self.full_text = parsing_results.get("full_text", "")
                self.pages = parsing_results.get("pages", [])
        
        class MockLegalAnalysis:
            def __init__(self, legal_analysis):
                self.overall_confidence = legal_analysis.get("overall_confidence", 0.8)
                self.entities = legal_analysis.get("entities", [])
                self.clauses = legal_analysis.get("clauses", [])
        
        class MockRiskAssessment:
            def __init__(self, risk_assessment):
                self.confidence_score = risk_assessment.get("confidence_score", 0.8)
                self.red_flags = risk_assessment.get("red_flags", [])
                self.risks = risk_assessment.get("risks", [])
        
        # Reconstruct objects from stored JSON
        parsed_doc = MockParsedDoc(doc_version.parsing_results or {})
        legal_analysis = MockLegalAnalysis(doc_version.legal_analysis or {})
        risk_assessment = MockRiskAssessment(doc_version.risk_assessment or {})
        citations = doc_version.citations or []
        
        # Perform quality validation
        validation_result = await self.quality_assurance.validate_document_processing(
            doc_version=doc_version,
            parsed_doc=parsed_doc,
            legal_analysis=legal_analysis,
            risk_assessment=risk_assessment,
            citations=citations,
            client_id=doc_version.client_id
        )
        
        return validation_result
    
    async def _route_document_after_quality(
        self,
        doc_version: DocumentVersion, 
        validation_result: ValidationResult
    ):
        """Route document based on quality validation results."""
        
        confidence = validation_result.overall_confidence
        
        # Apply routing logic based on configuration thresholds
        if confidence >= self.config.auto_approval_confidence:
            # High confidence - auto-approve
            doc_version.processing_status = ProcessingStatus.APPROVED
            
            if self.config.enable_version_control:
                await self.version_control.create_version_snapshot(
                    doc_version,
                    change_type=VersionChangeType.QUALITY_UPDATE,
                    changes_summary=f"Auto-approved (confidence: {confidence:.3f})"
                )
            
        elif confidence >= self.config.human_review_confidence:
            # Medium confidence - route to human review
            if self.config.enable_human_review:
                await self._assign_human_review(doc_version, validation_result)
            else:
                # Human review disabled - approve with warning
                doc_version.processing_status = ProcessingStatus.APPROVED
                
                logger.warning(
                    f"Document {doc_version.id} has medium confidence {confidence:.3f} "
                    "but human review is disabled"
                )
                
        elif confidence >= self.config.rejection_confidence:
            # Low confidence - requires human review
            if self.config.enable_human_review:
                await self._assign_human_review(doc_version, validation_result, priority_boost=True)
            else:
                # Human review disabled - reject
                doc_version.processing_status = ProcessingStatus.REJECTED
                
        else:
            # Very low confidence - reject
            doc_version.processing_status = ProcessingStatus.REJECTED
            
            if self.config.enable_version_control:
                await self.version_control.create_version_snapshot(
                    doc_version,
                    change_type=VersionChangeType.QUALITY_UPDATE,
                    changes_summary=f"Rejected (confidence: {confidence:.3f})"
                )
    
    async def _assign_human_review(
        self,
        doc_version: DocumentVersion,
        validation_result: ValidationResult,
        priority_boost: bool = False
    ):
        """Assign document for human review based on validation results."""
        
        # Determine review priority
        if validation_result.recommended_review_priority == ReviewPriority.CRITICAL or priority_boost:
            priority = ReviewPriority.CRITICAL
        elif validation_result.recommended_review_priority == ReviewPriority.HIGH:
            priority = ReviewPriority.HIGH
        elif validation_result.overall_confidence < 0.7:
            priority = ReviewPriority.HIGH
        else:
            priority = ReviewPriority.MEDIUM
        
        # Determine review type based on issues
        if validation_result.business_rules_passed:
            review_type = ReviewType.QUALITY_REVIEW
        else:
            review_type = ReviewType.FULL_REVIEW
        
        # Assign to human review queue
        assignment_id = await self.human_review_queue.assign_document_for_review(
            doc_version=doc_version,
            priority=priority,
            review_type=review_type
        )
        
        if assignment_id:
            logger.info(
                f"Assigned document {doc_version.id} for {review_type.value} "
                f"review with priority {priority.value}"
            )
        else:
            logger.warning(f"Failed to assign document {doc_version.id} for review")
    
    async def _convert_to_pipeline_metrics(self, processing_metrics: ProcessingMetrics) -> Dict[str, Any]:
        """Convert bulk processing metrics to pipeline metrics format."""
        
        return {
            "batch_id": processing_metrics.batch_id,
            "progress_percentage": processing_metrics.progress_percentage,
            "completed_documents": processing_metrics.completed_documents,
            "failed_documents": processing_metrics.failed_documents,
            "total_documents": processing_metrics.total_documents,
            "average_processing_time": processing_metrics.average_processing_time,
            "throughput_docs_per_hour": processing_metrics.throughput_docs_per_hour,
            "error_rate": processing_metrics.error_rate,
            "queue_depths": processing_metrics.queue_depths,
            "workflow_stage": self.active_workflows.get(processing_metrics.batch_id, WorkflowStage.INGESTION).value
        }
    
    async def _start_monitoring(self):
        """Start background monitoring tasks."""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start monitoring tasks
        asyncio.create_task(self._monitor_pipeline_health())
        asyncio.create_task(self._update_metrics_periodically())
        asyncio.create_task(self._cleanup_completed_workflows())
        
        # Start component monitoring
        await self.human_review_queue.start_monitoring()
        
        logger.info("Pipeline monitoring started")
    
    async def _monitor_pipeline_health(self):
        """Monitor overall pipeline health and status."""
        
        while self.monitoring_active:
            try:
                # Check component health
                bulk_processor_health = self.bulk_processor.get_system_health()
                review_queue_health = await self.human_review_queue.get_review_dashboard()
                
                # Determine overall status
                components_healthy = (
                    bulk_processor_health["overall_healthy"] and
                    review_queue_health["system_health"]["monitoring_active"]
                )
                
                # Check error rates and performance
                if self.metrics.error_rate > self.config.error_rate_threshold:
                    self.status = PipelineStatus.DEGRADED
                elif not components_healthy:
                    self.status = PipelineStatus.UNHEALTHY
                else:
                    self.status = PipelineStatus.HEALTHY
                
                # Alert on unhealthy status
                if self.status != PipelineStatus.HEALTHY:
                    logger.warning(f"Pipeline status: {self.status.value}")
                
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                self.status = PipelineStatus.DEGRADED
                await asyncio.sleep(30)  # Shorter retry on error
    
    async def _update_metrics_periodically(self):
        """Update pipeline metrics every 5 minutes."""
        
        while self.monitoring_active:
            try:
                await self._calculate_pipeline_metrics()
                await asyncio.sleep(self.metrics_update_interval)
                
            except Exception as e:
                logger.error(f"Metrics update error: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_pipeline_metrics(self):
        """Calculate comprehensive pipeline metrics."""
        
        # Get time range for metrics (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Document processing metrics
        recent_docs = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.queue_entered_at >= cutoff_time
        ).all()
        
        self.metrics.total_documents_processed = len(recent_docs)
        self.metrics.documents_completed = len([d for d in recent_docs if d.processing_status in [
            ProcessingStatus.COMPLETED, ProcessingStatus.APPROVED
        ]])
        self.metrics.documents_failed = len([d for d in recent_docs if d.processing_status == ProcessingStatus.FAILED])
        self.metrics.documents_in_progress = len([d for d in recent_docs if d.processing_status in [
            ProcessingStatus.IN_PROGRESS, ProcessingStatus.QUALITY_REVIEW, ProcessingStatus.HUMAN_REVIEW
        ]])
        
        # Calculate rates
        if self.metrics.total_documents_processed > 0:
            self.metrics.auto_approval_rate = len([d for d in recent_docs if d.processing_status == ProcessingStatus.APPROVED]) / self.metrics.total_documents_processed
            self.metrics.human_review_rate = len([d for d in recent_docs if d.processing_status == ProcessingStatus.HUMAN_REVIEW]) / self.metrics.total_documents_processed
            self.metrics.rejection_rate = len([d for d in recent_docs if d.processing_status == ProcessingStatus.REJECTED]) / self.metrics.total_documents_processed
            self.metrics.error_rate = self.metrics.documents_failed / self.metrics.total_documents_processed
        
        # Confidence metrics
        confidence_scores = [d.overall_confidence for d in recent_docs if d.overall_confidence is not None]
        if confidence_scores:
            self.metrics.average_confidence_score = sum(confidence_scores) / len(confidence_scores)
        
        # Processing time metrics
        processing_times = [d.total_processing_time for d in recent_docs if d.total_processing_time is not None]
        if processing_times:
            self.metrics.average_processing_time_seconds = sum(processing_times) / len(processing_times)
            
            # Calculate throughput
            elapsed_hours = 24  # Looking at last 24 hours
            self.metrics.documents_per_hour = self.metrics.total_documents_processed / elapsed_hours
        
        # Update timestamp
        self.metrics.last_updated = datetime.utcnow()
    
    async def _cleanup_completed_workflows(self):
        """Clean up completed workflow tracking every hour."""
        
        while self.monitoring_active:
            try:
                # Remove completed workflows older than 1 hour
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                completed_batches = []
                for batch_id, stage in self.active_workflows.items():
                    if stage == WorkflowStage.COMPLETION:
                        # Check if batch is actually completed
                        batch_job = self.db_session.query(BatchJob).filter(
                            BatchJob.id == batch_id
                        ).first()
                        
                        if batch_job and batch_job.completed_at and batch_job.completed_at < cutoff_time:
                            completed_batches.append(batch_id)
                
                for batch_id in completed_batches:
                    del self.active_workflows[batch_id]
                
                if completed_batches:
                    logger.info(f"Cleaned up {len(completed_batches)} completed workflows")
                
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Workflow cleanup error: {e}")
                await asyncio.sleep(300)  # 5 minute retry
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        
        # Get component health
        bulk_processor_health = self.bulk_processor.get_system_health()
        review_queue_health = await self.human_review_queue.get_review_dashboard()
        
        # Calculate overall health
        overall_healthy = (
            self.is_initialized and
            self.status in [PipelineStatus.HEALTHY, PipelineStatus.DEGRADED] and
            bulk_processor_health["overall_healthy"] and
            review_queue_health["system_health"]["monitoring_active"]
        )
        
        return {
            "overall_healthy": overall_healthy,
            "pipeline_status": self.status.value,
            "is_initialized": self.is_initialized,
            "monitoring_active": self.monitoring_active,
            "active_workflows": len(self.active_workflows),
            "configuration": self.config.to_dict(),
            "components": {
                "bulk_processor": bulk_processor_health,
                "review_queue": {
                    "queue_depth": review_queue_health["queue_metrics"]["total_depth"],
                    "sla_compliance": review_queue_health["performance_metrics"]["sla_compliance_rate"],
                    "active_reviewers": len([r for r in review_queue_health["reviewer_statistics"].values() if r["is_available"]])
                },
                "quality_assurance": {
                    "enabled": self.config.enable_quality_checks,
                    "thresholds": {
                        "auto_approval": self.config.auto_approval_confidence,
                        "human_review": self.config.human_review_confidence,
                        "rejection": self.config.rejection_confidence
                    }
                },
                "version_control": {
                    "enabled": self.config.enable_version_control,
                    "retention_days": self.config.audit_retention_days
                }
            },
            "metrics": {
                "documents_processed_24h": self.metrics.total_documents_processed,
                "documents_per_hour": self.metrics.documents_per_hour,
                "average_confidence": self.metrics.average_confidence_score,
                "error_rate": self.metrics.error_rate,
                "sla_compliance_rate": self.metrics.sla_compliance_rate,
                "last_updated": self.metrics.last_updated.isoformat()
            }
        }
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get comprehensive batch status across all pipeline components."""
        
        # Get bulk processor status
        bulk_status = await self.bulk_processor.get_batch_status(batch_id)
        
        if "error" in bulk_status:
            return bulk_status
        
        # Get workflow stage
        workflow_stage = self.active_workflows.get(batch_id, WorkflowStage.COMPLETION)
        
        # Get document statuses
        documents = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.batch_job_id == batch_id
        ).all()
        
        status_summary = {
            "total": len(documents),
            "parsing": len([d for d in documents if d.processing_status == ProcessingStatus.IN_PROGRESS]),
            "completed": len([d for d in documents if d.processing_status == ProcessingStatus.COMPLETED]),
            "approved": len([d for d in documents if d.processing_status == ProcessingStatus.APPROVED]),
            "rejected": len([d for d in documents if d.processing_status == ProcessingStatus.REJECTED]),
            "human_review": len([d for d in documents if d.processing_status == ProcessingStatus.HUMAN_REVIEW]),
            "failed": len([d for d in documents if d.processing_status == ProcessingStatus.FAILED])
        }
        
        # Quality metrics
        confidence_scores = [d.overall_confidence for d in documents if d.overall_confidence is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Review assignments
        review_assignments = self.db_session.query(ReviewAssignment).filter(
            ReviewAssignment.document_version_id.in_([d.id for d in documents])
        ).count()
        
        return {
            **bulk_status,
            "pipeline_info": {
                "workflow_stage": workflow_stage.value,
                "document_status_summary": status_summary,
                "quality_metrics": {
                    "average_confidence": avg_confidence,
                    "documents_with_confidence": len(confidence_scores)
                },
                "review_info": {
                    "documents_in_review": review_assignments,
                    "review_enabled": self.config.enable_human_review
                }
            }
        }
    
    async def get_pipeline_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive pipeline dashboard data."""
        
        # Update metrics
        await self._calculate_pipeline_metrics()
        
        # Get system health
        health_status = await self.get_system_health()
        
        # Get component dashboards
        review_dashboard = await self.human_review_queue.get_review_dashboard()
        quality_dashboard = await self.quality_assurance.get_quality_dashboard()
        
        return {
            "system_health": health_status,
            "pipeline_metrics": {
                "documents_processed_24h": self.metrics.total_documents_processed,
                "documents_per_hour": self.metrics.documents_per_hour,
                "average_processing_time_seconds": self.metrics.average_processing_time_seconds,
                "active_workflows": len(self.active_workflows),
                "error_rate_percentage": self.metrics.error_rate * 100,
                "average_confidence_score": self.metrics.average_confidence_score,
                "auto_approval_rate": self.metrics.auto_approval_rate * 100,
                "human_review_rate": self.metrics.human_review_rate * 100,
                "rejection_rate": self.metrics.rejection_rate * 100
            },
            "review_queue": review_dashboard,
            "quality_assurance": quality_dashboard,
            "configuration": self.config.to_dict(),
            "workflow_stages": {
                batch_id: stage.value for batch_id, stage in self.active_workflows.items()
            }
        }
    
    async def shutdown(self):
        """Gracefully shutdown the pipeline."""
        
        try:
            logger.info("Shutting down processing pipeline...")
            
            # Stop monitoring
            self.monitoring_active = False
            
            # Stop human review queue monitoring
            await self.human_review_queue.stop_monitoring()
            
            # Close database session
            self.db_session.close()
            
            # Update status
            self.status = PipelineStatus.MAINTENANCE
            self.is_initialized = False
            
            logger.info("Processing pipeline shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")

# Factory function for easy initialization
async def create_processing_pipeline(
    config: PipelineConfiguration = None,
    reviewer_configs: List[Dict[str, Any]] = None,
    initialize: bool = True
) -> ProcessingPipelineOrchestrator:
    """
    Factory function to create and optionally initialize a processing pipeline.
    
    Args:
        config: Pipeline configuration
        reviewer_configs: Reviewer configurations
        initialize: Whether to initialize the pipeline immediately
        
    Returns:
        ProcessingPipelineOrchestrator: Initialized pipeline instance
    """
    
    pipeline = ProcessingPipelineOrchestrator(config=config)
    
    if initialize:
        success = await pipeline.initialize(reviewer_configs)
        if not success:
            raise RuntimeError("Failed to initialize processing pipeline")
    
    return pipeline

# Testing and demonstration
async def test_pipeline_orchestrator():
    """Test the processing pipeline orchestrator with mock data."""
    
    logger.info("Testing ProcessingPipelineOrchestrator...")
    
    # Create test configuration
    config = PipelineConfiguration(
        max_concurrent_documents=10,
        auto_approval_confidence=0.9,
        human_review_confidence=0.7,
        rejection_confidence=0.5
    )
    
    # Create pipeline
    pipeline = await create_processing_pipeline(
        config=config,
        initialize=False  # Skip full initialization for testing
    )
    
    # Test health check
    health = await pipeline.get_system_health()
    assert "overall_healthy" in health, "Health check should return health status"
    
    # Test dashboard
    dashboard = await pipeline.get_pipeline_dashboard()
    assert "system_health" in dashboard, "Dashboard should contain system health"
    assert "pipeline_metrics" in dashboard, "Dashboard should contain metrics"
    
    logger.info("ProcessingPipelineOrchestrator test completed successfully")

if __name__ == "__main__":
    # Run test
    asyncio.run(test_pipeline_orchestrator())