"""
Autonomous Document Processing Pipeline

Enterprise-scale processing pipeline for legal document automation.
Handles 1,000 concurrent documents with distributed task processing.
"""

from .bulk_processor import BulkProcessor, BatchJob, ProcessingStatus
from .quality_assurance import QualityAssurance, QualityMetrics, ValidationResult
from .human_review_queue import HumanReviewQueue, ReviewPriority, ReviewAssignment
from .version_control import VersionControl, DocumentVersion, AuditTrail

__all__ = [
    # Bulk Processing
    'BulkProcessor',
    'BatchJob', 
    'ProcessingStatus',
    
    # Quality Assurance
    'QualityAssurance',
    'QualityMetrics',
    'ValidationResult',
    
    # Human Review
    'HumanReviewQueue',
    'ReviewPriority',
    'ReviewAssignment',
    
    # Version Control
    'VersionControl',
    'DocumentVersion',
    'AuditTrail',
]

__version__ = "1.0.0"