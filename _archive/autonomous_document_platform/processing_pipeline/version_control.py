"""
Version Control System

Immutable version control with full audit trail for legal document processing.
Provides complete processing lineage, change tracking, rollback capabilities,
and compliance-grade audit logging for enterprise document workflows.

Features:
- Immutable version snapshots at each processing stage
- Content hashing for change detection (SHA-256)
- Processing lineage with parent-child relationships
- Rollback to any previous version
- Compliance-grade audit trail (SOX, GDPR, HIPAA)
- Version comparison and diff generation
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Union, Set
import difflib
import gzip
import base64

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

from .database_schema import (
    DocumentVersion, AuditTrail, BatchJob, 
    ProcessingStatus, AuditEventType
)

# Import EnterpriseHub patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class VersionChangeType(Enum):
    """Types of changes between document versions."""
    INITIAL_CREATION = "initial_creation"
    PARSING_UPDATE = "parsing_update"
    ANALYSIS_UPDATE = "analysis_update"
    CITATION_UPDATE = "citation_update"
    RISK_UPDATE = "risk_update"
    QUALITY_UPDATE = "quality_update"
    MANUAL_CORRECTION = "manual_correction"
    MERGE_OPERATION = "merge_operation"
    SPLIT_OPERATION = "split_operation"

class VersionStatus(Enum):
    """Version lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"

class ComplianceStandard(Enum):
    """Supported compliance standards for audit trails."""
    SOX = "sox"          # Sarbanes-Oxley Act
    GDPR = "gdpr"        # General Data Protection Regulation
    HIPAA = "hipaa"      # Health Insurance Portability and Accountability Act
    ISO27001 = "iso27001"  # Information Security Management
    PCI_DSS = "pci_dss"   # Payment Card Industry Data Security Standard

@dataclass
class VersionMetadata:
    """Comprehensive version metadata for tracking and audit."""
    version_id: str
    document_id: str
    version_number: int
    created_at: datetime
    created_by: str = "system"
    
    # Content identification
    content_hash: str = ""
    file_size_bytes: int = 0
    content_type: str = ""
    
    # Processing context
    processing_stage: str = ""
    processing_confidence: float = 0.0
    change_type: VersionChangeType = VersionChangeType.INITIAL_CREATION
    
    # Lineage tracking
    parent_version_ids: List[str] = field(default_factory=list)
    child_version_ids: List[str] = field(default_factory=list)
    
    # Compliance metadata
    retention_period_days: int = 2555  # 7 years default for legal documents
    compliance_tags: Set[ComplianceStandard] = field(default_factory=set)
    
    # Change summary
    changes_summary: str = ""
    impact_assessment: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version_id": self.version_id,
            "document_id": self.document_id, 
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "content_hash": self.content_hash,
            "file_size_bytes": self.file_size_bytes,
            "content_type": self.content_type,
            "processing_stage": self.processing_stage,
            "processing_confidence": self.processing_confidence,
            "change_type": self.change_type.value,
            "parent_version_ids": self.parent_version_ids,
            "child_version_ids": self.child_version_ids,
            "retention_period_days": self.retention_period_days,
            "compliance_tags": [tag.value for tag in self.compliance_tags],
            "changes_summary": self.changes_summary,
            "impact_assessment": self.impact_assessment
        }

@dataclass
class VersionDiff:
    """Version comparison result with detailed change analysis."""
    from_version_id: str
    to_version_id: str
    content_changes: List[str] = field(default_factory=list)
    metadata_changes: Dict[str, Tuple[Any, Any]] = field(default_factory=dict)
    confidence_delta: float = 0.0
    
    # Structured content changes
    added_entities: List[Dict] = field(default_factory=list)
    removed_entities: List[Dict] = field(default_factory=list)
    modified_entities: List[Dict] = field(default_factory=list)
    
    added_clauses: List[Dict] = field(default_factory=list)
    removed_clauses: List[Dict] = field(default_factory=list)
    modified_clauses: List[Dict] = field(default_factory=list)
    
    risk_changes: List[Dict] = field(default_factory=list)
    citation_changes: List[Dict] = field(default_factory=list)
    
    # Summary statistics
    total_changes: int = 0
    significance_score: float = 0.0  # 0-1 scale of change significance
    
    def calculate_significance(self) -> float:
        """Calculate change significance score based on types and volume of changes."""
        
        # Weight different types of changes
        weights = {
            'entity_changes': 0.3,
            'clause_changes': 0.4, 
            'risk_changes': 0.2,
            'citation_changes': 0.1
        }
        
        entity_score = (len(self.added_entities) + len(self.removed_entities) + len(self.modified_entities)) * weights['entity_changes']
        clause_score = (len(self.added_clauses) + len(self.removed_clauses) + len(self.modified_clauses)) * weights['clause_changes']
        risk_score = len(self.risk_changes) * weights['risk_changes']
        citation_score = len(self.citation_changes) * weights['citation_changes']
        
        raw_score = entity_score + clause_score + risk_score + citation_score
        
        # Normalize to 0-1 scale (assume max ~20 significant changes)
        self.significance_score = min(1.0, raw_score / 20.0)
        return self.significance_score

@dataclass
class RollbackOperation:
    """Rollback operation tracking for audit and recovery."""
    operation_id: str
    target_version_id: str
    initiated_by: str
    initiated_at: datetime
    reason: str
    
    # Rollback details
    affected_versions: List[str] = field(default_factory=list)
    rollback_strategy: str = "create_new_version"  # or "archive_current"
    
    # Validation and approval
    requires_approval: bool = True
    approved_by: str = ""
    approved_at: Optional[datetime] = None
    
    # Execution tracking
    status: str = "pending"  # pending, approved, executed, failed, cancelled
    executed_at: Optional[datetime] = None
    error_message: str = ""

class VersionControl:
    """
    Enterprise version control system for legal document processing.
    
    Features:
    - Immutable version snapshots with content hashing
    - Complete processing lineage tracking
    - Rollback capabilities with approval workflows
    - Compliance-grade audit trail
    - Version comparison and diff analysis
    - Automated retention policy management
    """
    
    def __init__(self, db_session: Session, cache_service: CacheService = None):
        """Initialize version control system."""
        
        self.db_session = db_session
        self.cache_service = cache_service or CacheService()
        self.audit_logger = AuditLogger()
        
        # Configuration
        self.compression_enabled = True
        self.max_versions_per_document = 100
        self.automatic_cleanup_enabled = True
        
        # Content comparison settings
        self.diff_context_lines = 3
        self.similarity_threshold = 0.95  # For duplicate detection
        
        # Compliance settings
        self.default_retention_days = 2555  # 7 years for legal documents
        self.compliance_standards = {ComplianceStandard.SOX, ComplianceStandard.GDPR}
        
        # Performance optimization
        self.version_cache = {}  # In-memory cache for recent versions
        self.cache_ttl = 3600   # 1 hour cache TTL
        
        logger.info("VersionControl initialized with enterprise configuration")
    
    async def create_version_snapshot(
        self,
        doc_version: DocumentVersion,
        session: Session = None,
        change_type: VersionChangeType = VersionChangeType.INITIAL_CREATION,
        created_by: str = "system",
        changes_summary: str = "",
        parent_version_id: str = None
    ) -> str:
        """
        Create immutable version snapshot at current processing state.
        
        Args:
            doc_version: Current document version to snapshot
            session: Database session (uses instance session if None)
            change_type: Type of change triggering this version
            created_by: User ID creating the version
            changes_summary: Summary of changes made
            parent_version_id: ID of parent version if this is an update
            
        Returns:
            version_id: Unique identifier of created version snapshot
        """
        
        session = session or self.db_session
        snapshot_time = datetime.utcnow()
        
        try:
            # Generate content hash for change detection
            content_hash = await self._calculate_content_hash(doc_version)
            
            # Check for duplicate content (optimization)
            if await self._is_duplicate_content(doc_version.document_id, content_hash):
                logger.info(f"Skipping duplicate content for document {doc_version.document_id}")
                return None
            
            # Determine version number
            latest_version = session.query(DocumentVersion).filter(
                DocumentVersion.document_id == doc_version.document_id
            ).order_by(desc(DocumentVersion.version_number)).first()
            
            new_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create version metadata
            metadata = VersionMetadata(
                version_id=doc_version.id,
                document_id=doc_version.document_id,
                version_number=new_version_number,
                created_at=snapshot_time,
                created_by=created_by,
                content_hash=content_hash,
                file_size_bytes=getattr(doc_version, 'file_size_bytes', 0),
                content_type=getattr(doc_version, 'content_type', ''),
                processing_stage=self._determine_processing_stage(doc_version),
                processing_confidence=getattr(doc_version, 'overall_confidence', 0.0),
                change_type=change_type,
                changes_summary=changes_summary,
                compliance_tags=self.compliance_standards
            )
            
            # Set parent-child relationships
            if parent_version_id:
                metadata.parent_version_ids.append(parent_version_id)
                await self._update_child_relationships(parent_version_id, doc_version.id, session)
            
            # Update document version with metadata
            doc_version.content_hash = content_hash
            doc_version.version_number = new_version_number
            
            # Compress and store processing results if enabled
            if self.compression_enabled:
                await self._compress_processing_data(doc_version)
            
            # Create audit trail entry
            await self._create_version_audit_entry(
                doc_version, metadata, change_type, created_by
            )
            
            # Cache version for performance
            self.version_cache[doc_version.id] = {
                'metadata': metadata,
                'cached_at': snapshot_time
            }
            
            # Clean up old versions if needed
            if self.automatic_cleanup_enabled:
                await self._cleanup_old_versions(doc_version.document_id, session)
            
            logger.info(
                f"Created version snapshot {doc_version.id} "
                f"(v{new_version_number}) for document {doc_version.document_id}"
            )
            
            return doc_version.id
            
        except Exception as e:
            logger.error(f"Failed to create version snapshot for {doc_version.id}: {e}")
            raise
    
    async def _calculate_content_hash(self, doc_version: DocumentVersion) -> str:
        """Calculate SHA-256 hash of document content for change detection."""
        
        # Combine all content for hashing
        content_parts = []
        
        # Add parsing results
        if doc_version.parsing_results:
            content_parts.append(json.dumps(doc_version.parsing_results, sort_keys=True))
        
        # Add legal analysis
        if doc_version.legal_analysis:
            content_parts.append(json.dumps(doc_version.legal_analysis, sort_keys=True))
        
        # Add citations
        if doc_version.citations:
            content_parts.append(json.dumps(doc_version.citations, sort_keys=True))
        
        # Add risk assessment
        if doc_version.risk_assessment:
            content_parts.append(json.dumps(doc_version.risk_assessment, sort_keys=True))
        
        # Combine and hash
        combined_content = ''.join(content_parts).encode('utf-8')
        content_hash = hashlib.sha256(combined_content).hexdigest()
        
        return content_hash
    
    async def _is_duplicate_content(self, document_id: str, content_hash: str) -> bool:
        """Check if content hash already exists for this document."""
        
        existing_version = self.db_session.query(DocumentVersion).filter(
            and_(
                DocumentVersion.document_id == document_id,
                DocumentVersion.content_hash == content_hash
            )
        ).first()
        
        return existing_version is not None
    
    def _determine_processing_stage(self, doc_version: DocumentVersion) -> str:
        """Determine current processing stage based on available data."""
        
        stages = []
        
        if doc_version.parsing_results:
            stages.append("parsing")
        
        if doc_version.legal_analysis:
            stages.append("legal_analysis")
        
        if doc_version.citations:
            stages.append("citations")
        
        if doc_version.risk_assessment:
            stages.append("risk_assessment")
        
        if getattr(doc_version, 'overall_confidence', 0) > 0:
            stages.append("quality_validation")
        
        return " -> ".join(stages) if stages else "initial"
    
    async def _update_child_relationships(
        self,
        parent_version_id: str,
        child_version_id: str,
        session: Session
    ):
        """Update parent-child version relationships."""
        
        # This would typically be handled by the database schema relationships
        # For now, we'll use the document_relationships table defined in schema
        
        # Implementation would insert into document_relationships table
        pass
    
    async def _compress_processing_data(self, doc_version: DocumentVersion):
        """Compress large processing data to save storage space."""
        
        # Compress JSON data fields if they're large
        compression_threshold = 10000  # 10KB threshold
        
        for field_name in ['parsing_results', 'legal_analysis', 'citations', 'risk_assessment']:
            field_value = getattr(doc_version, field_name)
            
            if field_value and isinstance(field_value, (dict, list)):
                json_str = json.dumps(field_value)
                
                if len(json_str) > compression_threshold:
                    # Compress and encode
                    compressed_data = gzip.compress(json_str.encode('utf-8'))
                    encoded_data = base64.b64encode(compressed_data).decode('utf-8')
                    
                    # Store compressed data with metadata
                    compressed_field = {
                        'data': encoded_data,
                        'compressed': True,
                        'original_size': len(json_str),
                        'compressed_size': len(encoded_data)
                    }
                    
                    setattr(doc_version, field_name, compressed_field)
                    
                    logger.debug(f"Compressed {field_name}: {len(json_str)} -> {len(encoded_data)} bytes")
    
    async def _decompress_processing_data(self, field_data: Any) -> Any:
        """Decompress processing data if compressed."""
        
        if isinstance(field_data, dict) and field_data.get('compressed'):
            try:
                encoded_data = field_data['data']
                compressed_data = base64.b64decode(encoded_data.encode('utf-8'))
                json_str = gzip.decompress(compressed_data).decode('utf-8')
                return json.loads(json_str)
            except Exception as e:
                logger.error(f"Failed to decompress data: {e}")
                return None
        
        return field_data
    
    async def _create_version_audit_entry(
        self,
        doc_version: DocumentVersion,
        metadata: VersionMetadata,
        change_type: VersionChangeType,
        created_by: str
    ):
        """Create comprehensive audit trail entry for version creation."""
        
        await self.audit_logger.log_event(
            event_type=AuditEventType.VERSION_CREATED,
            event_description=f"Version {metadata.version_number} created: {change_type.value}",
            document_version_id=doc_version.id,
            user_id=created_by,
            event_data={
                "version_metadata": metadata.to_dict(),
                "change_type": change_type.value,
                "processing_stage": metadata.processing_stage,
                "content_hash": metadata.content_hash,
                "confidence_score": metadata.processing_confidence,
                "compliance_tags": [tag.value for tag in metadata.compliance_tags]
            },
            compliance_category="document_versioning"
        )
    
    async def _cleanup_old_versions(self, document_id: str, session: Session):
        """Clean up old versions based on retention policy."""
        
        # Get all versions for document
        all_versions = session.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version_number)).all()
        
        # Keep max_versions_per_document most recent
        if len(all_versions) > self.max_versions_per_document:
            versions_to_archive = all_versions[self.max_versions_per_document:]
            
            for version in versions_to_archive:
                # Archive instead of delete for compliance
                version.processing_status = ProcessingStatus.ARCHIVED
                
                # Clear large data fields to save space
                version.parsing_results = None
                version.legal_analysis = None
                version.citations = None
                version.risk_assessment = None
            
            logger.info(f"Archived {len(versions_to_archive)} old versions for document {document_id}")
    
    async def get_version_history(
        self,
        document_id: str,
        limit: int = 50,
        include_content: bool = False
    ) -> List[VersionMetadata]:
        """Get version history for a document."""
        
        query = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version_number))
        
        if limit:
            query = query.limit(limit)
        
        versions = query.all()
        
        history = []
        for version in versions:
            metadata = VersionMetadata(
                version_id=version.id,
                document_id=version.document_id,
                version_number=version.version_number,
                created_at=version.queue_entered_at or datetime.utcnow(),
                content_hash=getattr(version, 'content_hash', ''),
                file_size_bytes=getattr(version, 'file_size_bytes', 0),
                processing_confidence=getattr(version, 'overall_confidence', 0.0),
                processing_stage=self._determine_processing_stage(version)
            )
            
            # Add content if requested
            if include_content:
                metadata.parsing_results = await self._decompress_processing_data(version.parsing_results)
                metadata.legal_analysis = await self._decompress_processing_data(version.legal_analysis)
            
            history.append(metadata)
        
        return history
    
    async def compare_versions(
        self,
        from_version_id: str,
        to_version_id: str
    ) -> VersionDiff:
        """
        Compare two document versions and generate detailed diff.
        
        Args:
            from_version_id: Source version ID
            to_version_id: Target version ID
            
        Returns:
            VersionDiff: Detailed comparison result
        """
        
        # Get version records
        from_version = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.id == from_version_id
        ).first()
        
        to_version = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.id == to_version_id
        ).first()
        
        if not from_version or not to_version:
            raise ValueError("One or both versions not found")
        
        # Create diff object
        diff = VersionDiff(
            from_version_id=from_version_id,
            to_version_id=to_version_id
        )
        
        try:
            # Compare confidence scores
            from_confidence = getattr(from_version, 'overall_confidence', 0.0)
            to_confidence = getattr(to_version, 'overall_confidence', 0.0)
            diff.confidence_delta = to_confidence - from_confidence
            
            # Compare content hashes for quick check
            from_hash = getattr(from_version, 'content_hash', '')
            to_hash = getattr(to_version, 'content_hash', '')
            
            if from_hash == to_hash:
                # Identical content
                diff.total_changes = 0
                diff.significance_score = 0.0
                return diff
            
            # Detailed content comparison
            await self._compare_parsing_results(from_version, to_version, diff)
            await self._compare_legal_analysis(from_version, to_version, diff)
            await self._compare_risk_assessment(from_version, to_version, diff)
            await self._compare_citations(from_version, to_version, diff)
            
            # Calculate overall statistics
            diff.total_changes = (
                len(diff.added_entities) + len(diff.removed_entities) + len(diff.modified_entities) +
                len(diff.added_clauses) + len(diff.removed_clauses) + len(diff.modified_clauses) +
                len(diff.risk_changes) + len(diff.citation_changes)
            )
            
            diff.calculate_significance()
            
            logger.info(
                f"Version comparison {from_version_id} -> {to_version_id}: "
                f"{diff.total_changes} changes, significance={diff.significance_score:.3f}"
            )
            
            return diff
            
        except Exception as e:
            logger.error(f"Failed to compare versions {from_version_id} -> {to_version_id}: {e}")
            raise
    
    async def _compare_parsing_results(
        self,
        from_version: DocumentVersion,
        to_version: DocumentVersion,
        diff: VersionDiff
    ):
        """Compare parsing results between versions."""
        
        from_parsing = await self._decompress_processing_data(from_version.parsing_results)
        to_parsing = await self._decompress_processing_data(to_version.parsing_results)
        
        if not from_parsing or not to_parsing:
            return
        
        # Compare text content if available
        from_text = from_parsing.get('full_text', '')
        to_text = to_parsing.get('full_text', '')
        
        if from_text != to_text:
            # Generate text diff
            text_diff = list(difflib.unified_diff(
                from_text.splitlines(keepends=True),
                to_text.splitlines(keepends=True),
                fromfile=f"Version {from_version.version_number}",
                tofile=f"Version {to_version.version_number}",
                n=self.diff_context_lines
            ))
            
            diff.content_changes.extend(text_diff)
    
    async def _compare_legal_analysis(
        self,
        from_version: DocumentVersion,
        to_version: DocumentVersion,
        diff: VersionDiff
    ):
        """Compare legal analysis results between versions."""
        
        from_analysis = await self._decompress_processing_data(from_version.legal_analysis)
        to_analysis = await self._decompress_processing_data(to_version.legal_analysis)
        
        if not from_analysis or not to_analysis:
            return
        
        # Compare entities
        from_entities = from_analysis.get('entities', [])
        to_entities = to_analysis.get('entities', [])
        
        self._compare_entity_lists(from_entities, to_entities, diff)
        
        # Compare clauses
        from_clauses = from_analysis.get('clauses', [])
        to_clauses = to_analysis.get('clauses', [])
        
        self._compare_clause_lists(from_clauses, to_clauses, diff)
    
    def _compare_entity_lists(
        self,
        from_entities: List[Dict],
        to_entities: List[Dict],
        diff: VersionDiff
    ):
        """Compare entity lists and populate diff."""
        
        # Create lookup by entity text for comparison
        from_lookup = {entity.get('text', ''): entity for entity in from_entities}
        to_lookup = {entity.get('text', ''): entity for entity in to_entities}
        
        from_texts = set(from_lookup.keys())
        to_texts = set(to_lookup.keys())
        
        # Find added, removed, and potentially modified entities
        added_texts = to_texts - from_texts
        removed_texts = from_texts - to_texts
        common_texts = from_texts & to_texts
        
        diff.added_entities = [to_lookup[text] for text in added_texts]
        diff.removed_entities = [from_lookup[text] for text in removed_texts]
        
        # Check for modifications in common entities
        for text in common_texts:
            from_entity = from_lookup[text]
            to_entity = to_lookup[text]
            
            # Compare entity types or confidence scores
            if (from_entity.get('entity_type') != to_entity.get('entity_type') or
                abs(from_entity.get('confidence', 0) - to_entity.get('confidence', 0)) > 0.1):
                
                diff.modified_entities.append({
                    'text': text,
                    'from': from_entity,
                    'to': to_entity
                })
    
    def _compare_clause_lists(
        self,
        from_clauses: List[Dict],
        to_clauses: List[Dict],
        diff: VersionDiff
    ):
        """Compare clause lists and populate diff."""
        
        # Create lookup by clause type for comparison
        from_lookup = {clause.get('clause_type', ''): clause for clause in from_clauses}
        to_lookup = {clause.get('clause_type', ''): clause for clause in to_clauses}
        
        from_types = set(from_lookup.keys())
        to_types = set(to_lookup.keys())
        
        # Find added, removed, and potentially modified clauses
        added_types = to_types - from_types
        removed_types = from_types - to_types
        common_types = from_types & to_types
        
        diff.added_clauses = [to_lookup[clause_type] for clause_type in added_types]
        diff.removed_clauses = [from_lookup[clause_type] for clause_type in removed_types]
        
        # Check for modifications in common clauses
        for clause_type in common_types:
            from_clause = from_lookup[clause_type]
            to_clause = to_lookup[clause_type]
            
            # Compare confidence scores or content
            if abs(from_clause.get('confidence', 0) - to_clause.get('confidence', 0)) > 0.1:
                diff.modified_clauses.append({
                    'clause_type': clause_type,
                    'from': from_clause,
                    'to': to_clause
                })
    
    async def _compare_risk_assessment(
        self,
        from_version: DocumentVersion,
        to_version: DocumentVersion,
        diff: VersionDiff
    ):
        """Compare risk assessment results between versions."""
        
        from_risk = await self._decompress_processing_data(from_version.risk_assessment)
        to_risk = await self._decompress_processing_data(to_version.risk_assessment)
        
        if not from_risk or not to_risk:
            return
        
        # Compare risk levels
        from_level = from_risk.get('risk_level', '')
        to_level = to_risk.get('risk_level', '')
        
        if from_level != to_level:
            diff.risk_changes.append({
                'type': 'risk_level_change',
                'from': from_level,
                'to': to_level
            })
        
        # Compare red flags
        from_flags = from_risk.get('red_flags', [])
        to_flags = to_risk.get('red_flags', [])
        
        from_flag_types = {flag.get('flag_type') for flag in from_flags}
        to_flag_types = {flag.get('flag_type') for flag in to_flags}
        
        added_flags = to_flag_types - from_flag_types
        removed_flags = from_flag_types - to_flag_types
        
        if added_flags or removed_flags:
            diff.risk_changes.append({
                'type': 'red_flags_change',
                'added_flags': list(added_flags),
                'removed_flags': list(removed_flags)
            })
    
    async def _compare_citations(
        self,
        from_version: DocumentVersion,
        to_version: DocumentVersion,
        diff: VersionDiff
    ):
        """Compare citations between versions."""
        
        from_citations = await self._decompress_processing_data(from_version.citations)
        to_citations = await self._decompress_processing_data(to_version.citations)
        
        if not from_citations or not to_citations:
            return
        
        from_count = len(from_citations) if isinstance(from_citations, list) else 0
        to_count = len(to_citations) if isinstance(to_citations, list) else 0
        
        if from_count != to_count:
            diff.citation_changes.append({
                'type': 'citation_count_change',
                'from_count': from_count,
                'to_count': to_count,
                'delta': to_count - from_count
            })
    
    async def rollback_to_version(
        self,
        document_id: str,
        target_version_id: str,
        initiated_by: str,
        reason: str = "",
        require_approval: bool = True
    ) -> str:
        """
        Initiate rollback to a previous document version.
        
        Args:
            document_id: Document to rollback
            target_version_id: Version to rollback to
            initiated_by: User initiating rollback
            reason: Reason for rollback
            require_approval: Whether rollback requires approval
            
        Returns:
            operation_id: Rollback operation ID for tracking
        """
        
        operation_id = str(uuid.uuid4())
        
        try:
            # Validate target version exists
            target_version = self.db_session.query(DocumentVersion).filter(
                and_(
                    DocumentVersion.id == target_version_id,
                    DocumentVersion.document_id == document_id
                )
            ).first()
            
            if not target_version:
                raise ValueError(f"Target version {target_version_id} not found for document {document_id}")
            
            # Get current latest version
            current_version = self.db_session.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number)).first()
            
            if current_version.id == target_version_id:
                logger.info(f"Document {document_id} already at target version {target_version_id}")
                return None
            
            # Create rollback operation record
            rollback_op = RollbackOperation(
                operation_id=operation_id,
                target_version_id=target_version_id,
                initiated_by=initiated_by,
                initiated_at=datetime.utcnow(),
                reason=reason,
                requires_approval=require_approval,
                affected_versions=[v.id for v in self.db_session.query(DocumentVersion).filter(
                    and_(
                        DocumentVersion.document_id == document_id,
                        DocumentVersion.version_number > target_version.version_number
                    )
                ).all()]
            )
            
            # Store rollback operation (would use dedicated table in production)
            cache_key = f"rollback_op:{operation_id}"
            await self.cache_service.set(cache_key, rollback_op.__dict__, ttl=86400)  # 24 hours
            
            # Auto-approve if not required or execute immediately
            if not require_approval:
                await self._execute_rollback(rollback_op)
            
            # Audit log rollback initiation
            await self.audit_logger.log_event(
                event_type=AuditEventType.VERSION_CREATED,  # Rollback creates new version
                event_description=f"Rollback initiated to version {target_version.version_number}",
                document_version_id=target_version_id,
                user_id=initiated_by,
                event_data={
                    "operation_id": operation_id,
                    "target_version_number": target_version.version_number,
                    "reason": reason,
                    "requires_approval": require_approval,
                    "affected_versions_count": len(rollback_op.affected_versions)
                },
                event_severity="warning"
            )
            
            logger.info(
                f"Rollback operation {operation_id} initiated for document {document_id} "
                f"to version {target_version.version_number}"
            )
            
            return operation_id
            
        except Exception as e:
            logger.error(f"Failed to initiate rollback for document {document_id}: {e}")
            raise
    
    async def _execute_rollback(self, rollback_op: RollbackOperation):
        """Execute approved rollback operation."""
        
        try:
            rollback_op.status = "executing"
            rollback_op.executed_at = datetime.utcnow()
            
            # Get target version
            target_version = self.db_session.query(DocumentVersion).filter(
                DocumentVersion.id == rollback_op.target_version_id
            ).first()
            
            # Create new version based on target (rollback as new version for audit trail)
            new_version = DocumentVersion(
                id=str(uuid.uuid4()),
                document_id=target_version.document_id,
                version_number=target_version.version_number + 1000,  # High number to indicate rollback
                original_filename=target_version.original_filename,
                content_type=target_version.content_type,
                file_size_bytes=target_version.file_size_bytes,
                content_hash=target_version.content_hash,
                parsing_results=target_version.parsing_results,
                legal_analysis=target_version.legal_analysis,
                citations=target_version.citations,
                risk_assessment=target_version.risk_assessment,
                parsing_confidence=target_version.parsing_confidence,
                legal_confidence=target_version.legal_confidence,
                risk_confidence=target_version.risk_confidence,
                citation_completeness=target_version.citation_completeness,
                overall_confidence=target_version.overall_confidence,
                processing_status=ProcessingStatus.COMPLETED,
                queue_entered_at=datetime.utcnow()
            )
            
            self.db_session.add(new_version)
            
            # Update affected versions to superseded status
            for version_id in rollback_op.affected_versions:
                version = self.db_session.query(DocumentVersion).filter(
                    DocumentVersion.id == version_id
                ).first()
                if version:
                    version.processing_status = ProcessingStatus.SUPERSEDED
            
            self.db_session.commit()
            
            rollback_op.status = "completed"
            
            logger.info(f"Rollback operation {rollback_op.operation_id} completed successfully")
            
        except Exception as e:
            rollback_op.status = "failed"
            rollback_op.error_message = str(e)
            logger.error(f"Rollback operation {rollback_op.operation_id} failed: {e}")
            self.db_session.rollback()
            raise
    
    async def approve_rollback(
        self,
        operation_id: str,
        approved_by: str,
        approval_notes: str = ""
    ) -> bool:
        """Approve pending rollback operation."""
        
        try:
            # Get rollback operation
            cache_key = f"rollback_op:{operation_id}"
            op_data = await self.cache_service.get(cache_key)
            
            if not op_data:
                logger.error(f"Rollback operation {operation_id} not found")
                return False
            
            rollback_op = RollbackOperation(**op_data)
            
            if rollback_op.status != "pending":
                logger.error(f"Rollback operation {operation_id} not in pending status")
                return False
            
            # Update approval
            rollback_op.approved_by = approved_by
            rollback_op.approved_at = datetime.utcnow()
            rollback_op.status = "approved"
            
            # Execute rollback
            await self._execute_rollback(rollback_op)
            
            # Update cache
            await self.cache_service.set(cache_key, rollback_op.__dict__, ttl=86400)
            
            # Audit log approval
            await self.audit_logger.log_event(
                event_type=AuditEventType.VERSION_CREATED,
                event_description=f"Rollback operation approved and executed",
                document_version_id=rollback_op.target_version_id,
                user_id=approved_by,
                event_data={
                    "operation_id": operation_id,
                    "approval_notes": approval_notes
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to approve rollback operation {operation_id}: {e}")
            return False
    
    async def get_version_lineage(
        self,
        version_id: str,
        max_depth: int = 10
    ) -> Dict[str, Any]:
        """
        Get complete version lineage (ancestry and descendants) for a version.
        
        Args:
            version_id: Version to trace lineage for
            max_depth: Maximum depth to traverse
            
        Returns:
            Lineage tree with ancestors and descendants
        """
        
        # Implementation would trace through document_relationships table
        # For now, return basic structure
        
        version = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.id == version_id
        ).first()
        
        if not version:
            return None
        
        # Get all versions for this document
        all_versions = self.db_session.query(DocumentVersion).filter(
            DocumentVersion.document_id == version.document_id
        ).order_by(DocumentVersion.version_number).all()
        
        lineage = {
            "version_id": version_id,
            "document_id": version.document_id,
            "version_number": version.version_number,
            "ancestors": [v.id for v in all_versions if v.version_number < version.version_number],
            "descendants": [v.id for v in all_versions if v.version_number > version.version_number],
            "total_versions": len(all_versions),
            "lineage_depth": version.version_number
        }
        
        return lineage
    
    async def get_version_analytics(
        self,
        document_id: str = None,
        time_range: timedelta = None
    ) -> Dict[str, Any]:
        """Generate version control analytics and metrics."""
        
        time_range = time_range or timedelta(days=30)
        cutoff_time = datetime.utcnow() - time_range
        
        query = self.db_session.query(DocumentVersion)
        
        if document_id:
            query = query.filter(DocumentVersion.document_id == document_id)
        
        query = query.filter(DocumentVersion.queue_entered_at >= cutoff_time)
        
        versions = query.all()
        
        # Calculate analytics
        total_versions = len(versions)
        documents_with_versions = len(set(v.document_id for v in versions))
        
        # Version frequency by document
        doc_version_counts = defaultdict(int)
        for v in versions:
            doc_version_counts[v.document_id] += 1
        
        avg_versions_per_doc = statistics.mean(doc_version_counts.values()) if doc_version_counts else 0
        
        # Content change frequency
        content_hashes = defaultdict(set)
        for v in versions:
            if hasattr(v, 'content_hash') and v.content_hash:
                content_hashes[v.document_id].add(v.content_hash)
        
        unique_content_versions = sum(len(hashes) for hashes in content_hashes.values())
        
        return {
            "time_range_days": time_range.days,
            "total_versions_created": total_versions,
            "unique_documents": documents_with_versions,
            "average_versions_per_document": avg_versions_per_doc,
            "unique_content_versions": unique_content_versions,
            "version_frequency_distribution": dict(doc_version_counts),
            "top_versioned_documents": sorted(
                doc_version_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

# Testing and validation
async def validate_version_control():
    """Test the version control system."""
    
    logger.info("Validating VersionControl system...")
    
    # Mock session for testing
    class MockSession:
        def __init__(self):
            self.versions = {}
            self.committed = False
        
        def add(self, obj):
            if hasattr(obj, 'id'):
                self.versions[obj.id] = obj
        
        def commit(self):
            self.committed = True
        
        def query(self, model):
            return MockQuery(self.versions)
    
    class MockQuery:
        def __init__(self, versions):
            self.versions = versions
        
        def filter(self, condition):
            return self
        
        def order_by(self, order):
            return self
        
        def first(self):
            return list(self.versions.values())[0] if self.versions else None
        
        def all(self):
            return list(self.versions.values())
    
    # Mock document version
    class MockDocVersion:
        def __init__(self):
            self.id = "test-version-123"
            self.document_id = "test-doc-456"
            self.version_number = 1
            self.parsing_results = {"text": "Sample contract text"}
            self.legal_analysis = {"entities": [{"type": "party", "text": "Company A"}]}
            self.citations = [{"page": 1, "line": 5}]
            self.risk_assessment = {"risk_level": "medium"}
            self.overall_confidence = 0.85
    
    # Test version control
    version_control = VersionControl(db_session=MockSession())
    
    # Test version creation
    doc_version = MockDocVersion()
    
    version_id = await version_control.create_version_snapshot(
        doc_version=doc_version,
        change_type=VersionChangeType.INITIAL_CREATION,
        created_by="test_user",
        changes_summary="Initial document version"
    )
    
    assert version_id == doc_version.id, "Should return version ID"
    assert hasattr(doc_version, 'content_hash'), "Should calculate content hash"
    
    logger.info("VersionControl validation completed successfully")

if __name__ == "__main__":
    # Run validation test
    asyncio.run(validate_version_control())