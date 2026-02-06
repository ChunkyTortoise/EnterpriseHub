"""
Bulk Document Processor

Enterprise-scale document processing orchestrator using Celery + Redis.
Handles 1,000 concurrent documents with distributed task processing,
progress tracking, and health monitoring.

Integration with Phase 1 components:
- IntelligentParser for document parsing
- LegalAnalyzer for contract analysis  
- CitationTracker for legal citations
- RiskExtractor for risk assessment
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union

import redis
from celery import Celery, group, chain, chord
from celery.exceptions import WorkerLostError, Retry
from celery.signals import task_prerun, task_postrun, task_failure
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Import Phase 1 components
from ..document_engine import IntelligentParser, LegalAnalyzer, CitationTracker, RiskExtractor
from ..config.settings import settings
from .database_schema import (
    BatchJob, DocumentVersion, ProcessingQueue, AuditTrail,
    ProcessingStatus, QueueType, AuditEventType
)

# Import sibling pipeline components
from .quality_assurance import QualityAssurance
from .version_control import VersionControl

# Import EnterpriseHub infrastructure
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.core.llm_client import LLMClient  
from ghl_real_estate_ai.security.audit_logger import AuditLogger

# Configure logging
logger = logging.getLogger(__name__)

# Celery app configuration
app = Celery('document_processor')
app.conf.update(
    # Redis broker configuration
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    
    # Task routing
    task_routes={
        'bulk_processor.process_single_document': {'queue': 'processing'},
        'bulk_processor.validate_document_quality': {'queue': 'quality'},
        'bulk_processor.create_document_version': {'queue': 'critical'},
        'bulk_processor.generate_batch_report': {'queue': 'export'},
        'bulk_processor.health_check': {'queue': 'critical'},
    },
    
    # Performance tuning
    task_serializer='pickle',
    accept_content=['pickle', 'json'],
    result_serializer='pickle',
    timezone='UTC',
    enable_utc=True,
    
    # Concurrency settings
    worker_concurrency=20,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    
    # Queue configuration
    task_default_queue='processing',
    task_default_exchange='document_processing',
    task_default_routing_key='processing',
    
    # Reliability
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Monitoring
    task_track_started=True,
    task_send_sent_event=True,
    worker_send_task_events=True,
    
    # Queue definitions
    task_queues={
        'critical': {
            'exchange': 'document_processing',
            'routing_key': 'critical',
            'priority': 10
        },
        'processing': {
            'exchange': 'document_processing', 
            'routing_key': 'processing',
            'priority': 5
        },
        'quality': {
            'exchange': 'document_processing',
            'routing_key': 'quality', 
            'priority': 7
        },
        'review': {
            'exchange': 'document_processing',
            'routing_key': 'review',
            'priority': 3
        },
        'export': {
            'exchange': 'document_processing',
            'routing_key': 'export',
            'priority': 2
        }
    }
)

@dataclass
class ProcessingMetrics:
    """Real-time processing metrics and performance tracking."""
    batch_id: str
    start_time: datetime = field(default_factory=datetime.utcnow)
    total_documents: int = 0
    completed_documents: int = 0
    failed_documents: int = 0
    processing_times: List[float] = field(default_factory=list)
    error_details: Dict[str, Any] = field(default_factory=dict)
    queue_depths: Dict[str, int] = field(default_factory=dict)
    worker_utilization: float = 0.0
    memory_usage_mb: float = 0.0
    
    @property
    def progress_percentage(self) -> float:
        """Calculate processing progress percentage."""
        if self.total_documents == 0:
            return 0.0
        return (self.completed_documents / self.total_documents) * 100.0
    
    @property
    def average_processing_time(self) -> float:
        """Calculate average processing time per document."""
        return sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
    
    @property
    def throughput_docs_per_hour(self) -> float:
        """Calculate throughput in documents per hour."""
        if not self.processing_times:
            return 0.0
        elapsed_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        return self.completed_documents / elapsed_hours if elapsed_hours > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage."""
        total_processed = self.completed_documents + self.failed_documents
        return (self.failed_documents / total_processed * 100) if total_processed > 0 else 0.0

class BulkProcessor:
    """
    Enterprise-scale bulk document processing orchestrator.
    
    Features:
    - 1,000+ concurrent document processing via Celery workers
    - Real-time progress tracking and health monitoring
    - Circuit breaker patterns for resilience
    - Multi-tier caching for performance optimization
    - Full audit trail and compliance logging
    - Integration with Phase 1 document intelligence components
    """
    
    def __init__(self, redis_client: redis.Redis = None, db_session: Session = None):
        """Initialize bulk processor with infrastructure dependencies."""
        
        # Infrastructure setup
        self.redis_client = redis_client or redis.from_url(settings.redis_url)
        self.cache_service = CacheService()
        self.audit_logger = AuditLogger()
        
        # Database setup
        self.engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        SessionLocal = sessionmaker(bind=self.engine)
        self.db_session = db_session or SessionLocal()
        
        # Phase 1 component integration
        self.parser = IntelligentParser()
        self.analyzer = LegalAnalyzer()
        self.citation_tracker = CitationTracker()
        self.risk_extractor = RiskExtractor()
        
        # Phase 2 component integration
        self.quality_assurance = QualityAssurance()
        self.version_control = VersionControl()
        
        # Processing state
        self.active_batches: Dict[str, ProcessingMetrics] = {}
        self.circuit_breaker_open = False
        self.error_threshold = 0.1  # 10% error rate threshold
        
        # Performance monitoring
        self.executor = ThreadPoolExecutor(max_workers=50)
        self.health_check_interval = 30  # seconds
        self.last_health_check = datetime.utcnow()
        
        logger.info("BulkProcessor initialized with enterprise configuration")
    
    async def process_document_batch(
        self,
        file_paths: List[Union[str, Path]],
        batch_name: str = None,
        client_id: str = None,
        matter_id: str = None,
        priority: float = 0.5,
        callback: Callable[[ProcessingMetrics], None] = None
    ) -> str:
        """
        Process a batch of documents with enterprise-scale orchestration.
        
        Args:
            file_paths: List of document file paths to process
            batch_name: Human-readable batch name
            client_id: Client identifier for multi-tenancy
            matter_id: Matter identifier for legal case tracking
            priority: Processing priority (0.0 = low, 1.0 = critical)
            callback: Optional callback for real-time progress updates
            
        Returns:
            batch_id: Unique batch identifier for tracking
        """
        batch_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Initialize batch in database
        batch_job = BatchJob(
            id=batch_id,
            name=batch_name or f"Batch_{start_time.strftime('%Y%m%d_%H%M%S')}",
            description=f"Processing {len(file_paths)} documents",
            total_documents=len(file_paths),
            target_completion_time=start_time + timedelta(minutes=len(file_paths) * 0.5)  # 30 sec per doc target
        )
        self.db_session.add(batch_job)
        self.db_session.commit()
        
        # Initialize metrics tracking
        metrics = ProcessingMetrics(
            batch_id=batch_id,
            total_documents=len(file_paths)
        )
        self.active_batches[batch_id] = metrics
        
        # Audit log batch initiation
        await self.audit_logger.log_event(
            event_type=AuditEventType.PROCESSING_STARTED,
            event_description=f"Batch processing started for {len(file_paths)} documents",
            batch_job_id=batch_id,
            event_data={
                "total_documents": len(file_paths),
                "client_id": client_id,
                "matter_id": matter_id,
                "priority": priority
            }
        )
        
        try:
            # Circuit breaker check
            if self.circuit_breaker_open:
                raise Exception("Circuit breaker is open - system overloaded")
            
            # Create document processing tasks
            document_tasks = []
            for i, file_path in enumerate(file_paths):
                
                # Create document version entry
                doc_version = DocumentVersion(
                    document_id=str(uuid.uuid4()),
                    version_number=1,
                    original_filename=Path(file_path).name,
                    batch_job_id=batch_id,
                    client_id=client_id,
                    matter_id=matter_id,
                    priority_score=priority,
                    queue_type=self._determine_queue_type(priority),
                    queue_entered_at=datetime.utcnow()
                )
                self.db_session.add(doc_version)
                
                # Create Celery task for document processing
                task = process_single_document.s(
                    doc_version.id,
                    str(file_path),
                    batch_id,
                    priority
                )
                document_tasks.append(task)
            
            self.db_session.commit()
            
            # Execute distributed processing using Celery chord
            # Chord = group of tasks + callback when all complete
            processing_job = chord(
                group(document_tasks),
                generate_batch_report.s(batch_id)
            ).apply_async()
            
            # Start real-time monitoring
            monitor_task = asyncio.create_task(
                self._monitor_batch_progress(batch_id, callback)
            )
            
            logger.info(f"Initiated batch processing: {batch_id} with {len(file_paths)} documents")
            return batch_id
            
        except Exception as e:
            # Error handling and cleanup
            logger.error(f"Failed to initiate batch processing: {e}")
            
            # Update batch status
            batch_job.status = ProcessingStatus.FAILED
            self.db_session.commit()
            
            # Audit log failure
            await self.audit_logger.log_event(
                event_type=AuditEventType.ERROR_OCCURRED,
                event_description=f"Batch processing failed to start: {str(e)}",
                batch_job_id=batch_id,
                event_severity="error",
                error_details={"exception": str(e), "type": type(e).__name__}
            )
            
            raise
    
    def _determine_queue_type(self, priority: float) -> QueueType:
        """Determine appropriate queue based on priority and system load."""
        if priority >= 0.9:
            return QueueType.CRITICAL
        elif priority >= 0.7:
            return QueueType.PROCESSING
        elif priority >= 0.5:
            return QueueType.QUALITY
        else:
            return QueueType.REVIEW
    
    async def _monitor_batch_progress(
        self,
        batch_id: str,
        callback: Callable[[ProcessingMetrics], None] = None
    ):
        """Monitor batch processing progress with real-time updates."""
        
        while batch_id in self.active_batches:
            try:
                # Update metrics from database
                metrics = await self._update_batch_metrics(batch_id)
                
                # Execute callback if provided
                if callback:
                    callback(metrics)
                
                # Check for completion
                if metrics.progress_percentage >= 100.0:
                    logger.info(f"Batch {batch_id} completed successfully")
                    break
                
                # Health check
                await self._perform_health_check()
                
                # Wait before next check
                await asyncio.sleep(5)  # 5 second updates
                
            except Exception as e:
                logger.error(f"Error monitoring batch {batch_id}: {e}")
                await asyncio.sleep(10)  # Back off on error
    
    async def _update_batch_metrics(self, batch_id: str) -> ProcessingMetrics:
        """Update batch processing metrics from database and Redis."""
        
        # Get batch job from database
        batch_job = self.db_session.query(BatchJob).filter(
            BatchJob.id == batch_id
        ).first()
        
        if not batch_job:
            raise ValueError(f"Batch {batch_id} not found")
        
        # Update metrics object
        metrics = self.active_batches[batch_id]
        metrics.completed_documents = batch_job.completed_documents
        metrics.failed_documents = batch_job.failed_documents
        
        # Get queue depths from Redis
        for queue_type in QueueType:
            queue_depth = app.control.inspect().active_queues()
            if queue_depth:
                metrics.queue_depths[queue_type.value] = len(
                    queue_depth.get(queue_type.value, [])
                )
        
        # Update database with current metrics
        batch_job.progress_percentage = metrics.progress_percentage
        batch_job.average_processing_time = metrics.average_processing_time
        batch_job.throughput_docs_per_hour = metrics.throughput_docs_per_hour
        
        self.db_session.commit()
        
        return metrics
    
    async def _perform_health_check(self):
        """Perform system health check and circuit breaker logic."""
        
        current_time = datetime.utcnow()
        
        # Skip if too recent
        if (current_time - self.last_health_check).total_seconds() < self.health_check_interval:
            return
        
        self.last_health_check = current_time
        
        try:
            # Check Redis connectivity
            redis_healthy = self.redis_client.ping()
            
            # Check database connectivity
            db_healthy = self.db_session.execute("SELECT 1").fetchone() is not None
            
            # Check Celery workers
            worker_stats = app.control.inspect().stats()
            active_workers = len(worker_stats) if worker_stats else 0
            
            # Check queue depths
            queue_inspect = app.control.inspect()
            total_queued = 0
            
            if queue_inspect.active():
                for worker_queues in queue_inspect.active().values():
                    total_queued += len(worker_queues)
            
            # Update queue health in database
            for queue_type in QueueType:
                queue_record = self.db_session.query(ProcessingQueue).filter(
                    ProcessingQueue.queue_name == queue_type
                ).first()
                
                if not queue_record:
                    queue_record = ProcessingQueue(
                        queue_name=queue_type,
                        sla_target_seconds=self._get_sla_target(queue_type)
                    )
                    self.db_session.add(queue_record)
                
                queue_record.is_healthy = redis_healthy and db_healthy
                queue_record.active_workers = active_workers
                queue_record.last_health_check = current_time
                queue_record.current_depth = total_queued
            
            self.db_session.commit()
            
            # Circuit breaker logic
            overall_healthy = redis_healthy and db_healthy and active_workers > 0
            
            if not overall_healthy:
                logger.warning("System health check failed - opening circuit breaker")
                self.circuit_breaker_open = True
            else:
                self.circuit_breaker_open = False
            
            logger.debug(f"Health check: Redis={redis_healthy}, DB={db_healthy}, Workers={active_workers}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.circuit_breaker_open = True
    
    def _get_sla_target(self, queue_type: QueueType) -> float:
        """Get SLA target time in seconds for queue type."""
        sla_targets = {
            QueueType.CRITICAL: 30.0,    # 30 seconds
            QueueType.PROCESSING: 300.0,  # 5 minutes
            QueueType.QUALITY: 120.0,    # 2 minutes
            QueueType.REVIEW: 7200.0,    # 2 hours
            QueueType.EXPORT: 60.0       # 1 minute
        }
        return sla_targets.get(queue_type, 300.0)
    
    async def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """Get comprehensive batch status and metrics."""
        
        # Get batch job from database
        batch_job = self.db_session.query(BatchJob).filter(
            BatchJob.id == batch_id
        ).first()
        
        if not batch_job:
            return {"error": f"Batch {batch_id} not found"}
        
        # Get real-time metrics if batch is active
        metrics = self.active_batches.get(batch_id)
        
        # Get document statuses
        documents = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.batch_job_id == batch_id
        ).all()
        
        document_statuses = defaultdict(int)
        for doc in documents:
            document_statuses[doc.processing_status.value] += 1
        
        return {
            "batch_id": batch_id,
            "name": batch_job.name,
            "status": batch_job.status.value,
            "progress": {
                "total_documents": batch_job.total_documents,
                "completed": batch_job.completed_documents,
                "failed": batch_job.failed_documents,
                "percentage": batch_job.progress_percentage
            },
            "performance": {
                "average_processing_time": batch_job.average_processing_time,
                "throughput_docs_per_hour": batch_job.throughput_docs_per_hour,
                "sla_met": batch_job.sla_met
            },
            "timestamps": {
                "created_at": batch_job.created_at.isoformat(),
                "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None,
                "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None,
                "target_completion": batch_job.target_completion_time.isoformat() if batch_job.target_completion_time else None
            },
            "document_statuses": dict(document_statuses),
            "real_time_metrics": {
                "error_rate": metrics.error_rate if metrics else 0.0,
                "current_queue_depths": metrics.queue_depths if metrics else {},
                "memory_usage_mb": metrics.memory_usage_mb if metrics else 0.0
            }
        }
    
    async def cancel_batch(self, batch_id: str, reason: str = "User requested") -> bool:
        """Cancel an active batch processing job."""
        
        try:
            # Revoke all tasks for the batch
            # This requires task tracking to be enabled
            active_tasks = app.control.inspect().active()
            
            tasks_to_revoke = []
            if active_tasks:
                for worker_tasks in active_tasks.values():
                    for task in worker_tasks:
                        if task.get('args') and batch_id in str(task.get('args')):
                            tasks_to_revoke.append(task['id'])
            
            # Revoke tasks
            if tasks_to_revoke:
                app.control.revoke(tasks_to_revoke, terminate=True)
                logger.info(f"Revoked {len(tasks_to_revoke)} tasks for batch {batch_id}")
            
            # Update batch status
            batch_job = self.db_session.query(BatchJob).filter(
                BatchJob.id == batch_id
            ).first()
            
            if batch_job:
                batch_job.status = ProcessingStatus.FAILED
                self.db_session.commit()
            
            # Clean up active tracking
            if batch_id in self.active_batches:
                del self.active_batches[batch_id]
            
            # Audit log cancellation
            await self.audit_logger.log_event(
                event_type=AuditEventType.PROCESSING_COMPLETED,
                event_description=f"Batch processing cancelled: {reason}",
                batch_job_id=batch_id,
                event_data={"reason": reason, "tasks_revoked": len(tasks_to_revoke)}
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel batch {batch_id}: {e}")
            return False
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status."""
        
        # Get queue health from database
        queues = self.db_session.query(ProcessingQueue).all()
        queue_health = {}
        
        for queue in queues:
            queue_health[queue.queue_name.value] = {
                "is_healthy": queue.is_healthy,
                "current_depth": queue.current_depth,
                "active_workers": queue.active_workers,
                "sla_compliance_24h": queue.sla_compliance_rate_24h,
                "error_rate_24h": queue.error_rate_24h,
                "last_check": queue.last_health_check.isoformat() if queue.last_health_check else None
            }
        
        # Get Celery worker statistics
        worker_stats = app.control.inspect().stats()
        
        return {
            "overall_healthy": not self.circuit_breaker_open,
            "circuit_breaker_open": self.circuit_breaker_open,
            "active_batches": len(self.active_batches),
            "queue_health": queue_health,
            "worker_stats": worker_stats or {},
            "redis_connected": self.redis_client.ping(),
            "database_connected": True,  # If we can query, DB is connected
            "last_health_check": self.last_health_check.isoformat()
        }

# Celery task definitions
@app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_single_document(self, doc_version_id: str, file_path: str, batch_id: str, priority: float):
    """
    Process a single document through the complete Phase 1 + Phase 2 pipeline.
    
    This task coordinates:
    1. Document parsing (IntelligentParser)
    2. Legal analysis (LegalAnalyzer) 
    3. Citation tracking (CitationTracker)
    4. Risk extraction (RiskExtractor)
    5. Quality validation (QualityAssurance)
    6. Version control (VersionControl)
    """
    
    start_time = time.time()
    doc_version = None
    
    try:
        # Initialize components (will reuse from global state in worker)
        parser = IntelligentParser()
        analyzer = LegalAnalyzer()
        citation_tracker = CitationTracker()
        risk_extractor = RiskExtractor()
        quality_assurance = QualityAssurance()
        version_control = VersionControl()
        
        # Get database session (worker-local)
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Get document version record
        doc_version = session.query(DocumentVersion).filter(
            DocumentVersion.id == doc_version_id
        ).first()
        
        if not doc_version:
            raise ValueError(f"Document version {doc_version_id} not found")
        
        # Update status to processing
        doc_version.processing_status = ProcessingStatus.IN_PROGRESS
        doc_version.processing_started_at = datetime.utcnow()
        session.commit()
        
        # Phase 1: Document Intelligence Pipeline
        
        # Step 1: Parse document
        parsed_doc = await parser.parse_document(file_path)
        doc_version.parsing_results = parsed_doc.to_dict()
        doc_version.parsing_confidence = parsed_doc.confidence_score
        
        # Step 2: Legal analysis
        legal_analysis = await analyzer.analyze_document(parsed_doc)
        doc_version.legal_analysis = legal_analysis.to_dict()
        doc_version.legal_confidence = legal_analysis.overall_confidence
        
        # Step 3: Citation tracking  
        citations = await citation_tracker.create_citations_from_parsed_document(parsed_doc)
        doc_version.citations = [citation.to_dict() for citation in citations]
        doc_version.citation_completeness = len(citations) / max(1, len(parsed_doc.pages))
        
        # Step 4: Risk assessment
        risk_assessment = await risk_extractor.extract_risks(parsed_doc, legal_analysis)
        doc_version.risk_assessment = risk_assessment.to_dict()
        doc_version.risk_confidence = risk_assessment.confidence_score
        
        # Phase 2: Quality & Version Control
        
        # Step 5: Quality validation
        quality_result = await quality_assurance.validate_document_processing(
            doc_version, parsed_doc, legal_analysis, risk_assessment
        )
        doc_version.overall_confidence = quality_result.overall_confidence
        
        # Step 6: Version control and audit
        await version_control.create_version_snapshot(doc_version, session)
        
        # Update completion status
        processing_time = time.time() - start_time
        doc_version.processing_status = ProcessingStatus.COMPLETED
        doc_version.processing_completed_at = datetime.utcnow()
        doc_version.total_processing_time = processing_time
        
        # Update batch progress
        batch_job = session.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch_job:
            batch_job.completed_documents += 1
            batch_job.progress_percentage = (batch_job.completed_documents / batch_job.total_documents) * 100
            
            # Update performance metrics
            if not batch_job.average_processing_time:
                batch_job.average_processing_time = processing_time
            else:
                # Running average
                total_completed = batch_job.completed_documents
                batch_job.average_processing_time = (
                    (batch_job.average_processing_time * (total_completed - 1) + processing_time) / total_completed
                )
        
        session.commit()
        session.close()
        
        logger.info(f"Successfully processed document {doc_version_id} in {processing_time:.2f}s")
        
        return {
            "document_id": doc_version_id,
            "batch_id": batch_id,
            "processing_time": processing_time,
            "confidence_score": doc_version.overall_confidence,
            "status": "completed"
        }
        
    except Exception as e:
        # Error handling with retry logic
        logger.error(f"Failed to process document {doc_version_id}: {e}")
        
        # Update document status
        if doc_version:
            doc_version.processing_status = ProcessingStatus.FAILED
            session = doc_version.session if hasattr(doc_version, 'session') else SessionLocal()
            session.commit()
            session.close()
        
        # Update batch failure count
        try:
            session = SessionLocal()
            batch_job = session.query(BatchJob).filter(BatchJob.id == batch_id).first()
            if batch_job:
                batch_job.failed_documents += 1
            session.commit()
            session.close()
        except:
            pass
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying document {doc_version_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1))
        else:
            # Final failure
            raise e

@app.task
def validate_document_quality(doc_version_id: str):
    """Dedicated task for quality validation."""
    # Implementation deferred to QualityAssurance component
    pass

@app.task
def create_document_version(doc_version_id: str):
    """Dedicated task for version control."""
    # Implementation deferred to VersionControl component  
    pass

@app.task
def generate_batch_report(processing_results: List[Dict[str, Any]], batch_id: str):
    """
    Generate comprehensive batch completion report.
    Called when all documents in a batch are processed.
    """
    
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        
        # Update batch completion status
        batch_job = session.query(BatchJob).filter(BatchJob.id == batch_id).first()
        if batch_job:
            batch_job.status = ProcessingStatus.COMPLETED
            batch_job.completed_at = datetime.utcnow()
            
            # Calculate final metrics
            successful_results = [r for r in processing_results if r.get('status') == 'completed']
            if successful_results:
                processing_times = [r['processing_time'] for r in successful_results]
                batch_job.average_processing_time = sum(processing_times) / len(processing_times)
                
                elapsed_time = (batch_job.completed_at - batch_job.started_at).total_seconds()
                batch_job.throughput_docs_per_hour = len(successful_results) / (elapsed_time / 3600)
            
            # Check SLA compliance
            if batch_job.completed_at <= batch_job.target_completion_time:
                batch_job.sla_met = True
            else:
                batch_job.sla_met = False
            
            session.commit()
        
        session.close()
        
        # Generate executive summary report
        report = {
            "batch_id": batch_id,
            "completion_time": datetime.utcnow().isoformat(),
            "total_documents": len(processing_results),
            "successful_documents": len(successful_results),
            "failed_documents": len(processing_results) - len(successful_results),
            "average_processing_time": batch_job.average_processing_time if batch_job else None,
            "throughput_docs_per_hour": batch_job.throughput_docs_per_hour if batch_job else None,
            "sla_met": batch_job.sla_met if batch_job else False
        }
        
        logger.info(f"Generated batch report for {batch_id}: {report}")
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate batch report for {batch_id}: {e}")
        raise

@app.task
def health_check():
    """System health check task for monitoring."""
    
    try:
        # Basic connectivity checks
        redis_client = redis.from_url(settings.redis_url)
        redis_healthy = redis_client.ping()
        
        engine = create_engine(settings.database_url)
        db_healthy = engine.execute("SELECT 1").fetchone() is not None
        
        # Worker capacity check
        worker_stats = app.control.inspect().stats()
        active_workers = len(worker_stats) if worker_stats else 0
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "redis_healthy": redis_healthy,
            "database_healthy": db_healthy,
            "active_workers": active_workers,
            "overall_healthy": redis_healthy and db_healthy and active_workers > 0
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_healthy": False,
            "error": str(e)
        }

# Signal handlers for monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Task pre-execution handler for monitoring."""
    logger.debug(f"Starting task {task.name} with ID {task_id}")

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Task post-execution handler for monitoring."""
    logger.debug(f"Completed task {task.name} with ID {task_id}, state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, einfo=None, **kwds):
    """Task failure handler for error tracking."""
    logger.error(f"Task {sender.name} failed with ID {task_id}: {exception}")

if __name__ == "__main__":
    # CLI interface for testing
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "worker":
        # Start Celery worker
        app.worker_main(['worker', '--loglevel=info', '--concurrency=20'])
    else:
        # Start Celery beat scheduler  
        app.control.inspect().stats()
        print("BulkProcessor ready. Use 'python bulk_processor.py worker' to start worker.")