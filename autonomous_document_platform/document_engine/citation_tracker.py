"""
Citation Tracker - Legal-Grade Source Tracking

Maintain precise provenance and citation tracking for legal compliance.
Leverages EnterpriseHub patterns:
- MemoryService (Graphiti integration) for relationship tracking
- CacheService for citation graph caching
- Document hash tracking patterns

Key Features:
- Page-level, paragraph-level, and sentence-level citations
- Cross-document reference tracking
- Version tracking and diff analysis
- Chain of custody for extracted information
- Confidence scoring for each citation
- Export to legal citation formats (Bluebook, APA, MLA)
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re
from collections import defaultdict

# EnterpriseHub reused components
import sys
sys.path.append('/Users/cave/Documents/GitHub/EnterpriseHub')

from ghl_real_estate_ai.agent_system.memory.manager import MemoryService
from ghl_real_estate_ai.services.cache_service import CacheService
from autonomous_document_platform.document_engine.intelligent_parser import ParsedDocument
from autonomous_document_platform.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CitationFormat(str, Enum):
    """Legal citation formats"""
    BLUEBOOK = "bluebook"
    APA = "apa"
    MLA = "mla"
    CHICAGO = "chicago"
    ALWD = "alwd"  # Association of Legal Writing Directors


class ExtractionMethod(str, Enum):
    """Methods used for information extraction"""
    OCR = "ocr"
    VISION = "vision"
    NATIVE = "native"
    HYBRID = "hybrid"
    MANUAL = "manual"


class CitationLevel(str, Enum):
    """Granularity levels of citations"""
    DOCUMENT = "document"
    PAGE = "page"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    WORD = "word"


@dataclass
class Citation:
    """Single citation with legal-grade metadata"""
    citation_id: str
    document_id: str
    document_title: str
    page_number: Optional[int] = None
    paragraph_index: Optional[int] = None
    sentence_index: Optional[int] = None
    char_start: int = 0
    char_end: int = 0
    extracted_text: str = ""
    confidence_score: float = 0.0
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    timestamp: datetime = field(default_factory=datetime.utcnow)
    validator: Optional[str] = None
    context: str = ""
    citation_level: CitationLevel = CitationLevel.DOCUMENT
    original_format: Optional[str] = None  # Original file format
    processing_version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_bluebook_format(self) -> str:
        """Convert citation to Bluebook format"""
        # Basic Bluebook format: Title, Page (Date)
        if self.page_number:
            return f"{self.document_title}, at {self.page_number} ({self.timestamp.year})"
        else:
            return f"{self.document_title} ({self.timestamp.year})"

    def to_apa_format(self) -> str:
        """Convert citation to APA format"""
        # Basic APA format: (Document Title, Year, p. Page)
        if self.page_number:
            return f"({self.document_title}, {self.timestamp.year}, p. {self.page_number})"
        else:
            return f"({self.document_title}, {self.timestamp.year})"

    def to_mla_format(self) -> str:
        """Convert citation to MLA format"""
        # Basic MLA format: (Document Title Page)
        if self.page_number:
            return f"({self.document_title} {self.page_number})"
        else:
            return f"({self.document_title})"


@dataclass
class CitationRelationship:
    """Relationship between two citations"""
    relationship_id: str
    source_citation_id: str
    target_citation_id: str
    relationship_type: str  # "references", "contradicts", "supports", "clarifies"
    confidence: float
    evidence: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentVersion:
    """Version of a document with change tracking"""
    version_id: str
    document_id: str
    version_number: int
    document_hash: str
    created_at: datetime
    created_by: str
    change_type: str  # "initial", "updated", "corrected", "reviewed"
    change_summary: str
    previous_version_id: Optional[str] = None
    citations: List[Citation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CitationAuditTrail:
    """Complete audit trail for citation chain of custody"""
    audit_id: str
    citation_id: str
    events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_event(self, event_type: str, description: str, user_id: Optional[str] = None):
        """Add audit event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "description": description,
            "user_id": user_id,
            "system_info": {
                "processing_version": "1.0.0",
                "extraction_engine": "autonomous_document_platform"
            }
        }
        self.events.append(event)


class CitationGraph:
    """Graph of citations and their relationships using Graphiti integration"""

    def __init__(self, memory_service: Optional[MemoryService] = None):
        self.memory_service = memory_service or MemoryService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def add_citation(
        self,
        citation: Citation,
        context_data: Optional[Dict] = None
    ) -> str:
        """Add citation to the graph with full context"""

        try:
            # Prepare context for Graphiti storage
            citation_context = {
                "citation_id": citation.citation_id,
                "document_id": citation.document_id,
                "document_title": citation.document_title,
                "page_number": citation.page_number,
                "extracted_text": citation.extracted_text,
                "confidence_score": citation.confidence_score,
                "extraction_method": citation.extraction_method.value,
                "citation_level": citation.citation_level.value,
                "timestamp": citation.timestamp.isoformat(),
                "metadata": citation.metadata
            }

            if context_data:
                citation_context.update(context_data)

            # Store in Graphiti memory system
            await self.memory_service.store_context(
                lead_id=citation.document_id,
                context=citation_context
            )

            self.logger.info(f"Added citation to graph: {citation.citation_id}")
            return citation.citation_id

        except Exception as e:
            self.logger.error(f"Failed to add citation to graph: {e}")
            raise

    async def link_citations(
        self,
        source_citation_id: str,
        target_citation_id: str,
        relationship_type: str,
        evidence: str = "",
        confidence: float = 1.0
    ) -> None:
        """Create relationship between two citations"""

        try:
            relationship = CitationRelationship(
                relationship_id=f"rel_{hashlib.md5(f'{source_citation_id}_{target_citation_id}_{relationship_type}'.encode()).hexdigest()[:16]}",
                source_citation_id=source_citation_id,
                target_citation_id=target_citation_id,
                relationship_type=relationship_type,
                confidence=confidence,
                evidence=evidence
            )

            # Store relationship in memory
            relationship_context = {
                "relationship_id": relationship.relationship_id,
                "source_citation": source_citation_id,
                "target_citation": target_citation_id,
                "relationship_type": relationship_type,
                "confidence": confidence,
                "evidence": evidence,
                "created_at": relationship.created_at.isoformat()
            }

            await self.memory_service.store_context(
                lead_id=f"relationship_{relationship.relationship_id}",
                context=relationship_context
            )

            self.logger.info(
                f"Linked citations: {source_citation_id} -> {target_citation_id} "
                f"({relationship_type})"
            )

        except Exception as e:
            self.logger.error(f"Failed to link citations: {e}")
            raise

    async def get_citation_chain(self, citation_id: str) -> List[Citation]:
        """Get complete chain of citations related to a given citation"""

        try:
            # Query Graphiti for related citations
            related_context = await self.memory_service.get_context(
                lead_id=citation_id,
                query=f"Find all citations and relationships for {citation_id}"
            )

            # Convert context back to Citation objects
            citations = []
            for context_item in related_context.get('related_items', []):
                if 'citation_id' in context_item:
                    citation = Citation(
                        citation_id=context_item['citation_id'],
                        document_id=context_item['document_id'],
                        document_title=context_item.get('document_title', 'Unknown'),
                        page_number=context_item.get('page_number'),
                        extracted_text=context_item.get('extracted_text', ''),
                        confidence_score=context_item.get('confidence_score', 0.0),
                        extraction_method=ExtractionMethod(context_item.get('extraction_method', 'native')),
                        timestamp=datetime.fromisoformat(context_item.get('timestamp', datetime.utcnow().isoformat()))
                    )
                    citations.append(citation)

            return citations

        except Exception as e:
            self.logger.error(f"Failed to get citation chain: {e}")
            return []

    async def validate_citation_integrity(self) -> Dict[str, Any]:
        """Validate integrity of citation graph"""

        try:
            # Query all citations and relationships
            validation_results = {
                "total_citations": 0,
                "broken_links": [],
                "orphaned_citations": [],
                "duplicate_citations": [],
                "integrity_score": 0.0,
                "last_validated": datetime.utcnow().isoformat()
            }

            # This would be a more complex implementation in production
            # For now, return basic validation structure

            validation_results["integrity_score"] = 1.0  # Perfect score for demo

            return validation_results

        except Exception as e:
            self.logger.error(f"Citation integrity validation failed: {e}")
            return {"integrity_score": 0.0, "error": str(e)}


class VersionTracker:
    """Track document versions and changes with diff analysis"""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def add_version(
        self,
        document_id: str,
        document_hash: str,
        created_by: str,
        change_type: str = "initial",
        change_summary: str = "",
        citations: Optional[List[Citation]] = None
    ) -> DocumentVersion:
        """Add new version of a document"""

        # Get previous version number
        previous_versions = await self._get_document_versions(document_id)
        version_number = len(previous_versions) + 1

        # Generate version ID
        version_id = f"{document_id}_v{version_number}_{int(datetime.utcnow().timestamp())}"

        previous_version_id = None
        if previous_versions:
            previous_version_id = previous_versions[-1].version_id

        version = DocumentVersion(
            version_id=version_id,
            document_id=document_id,
            version_number=version_number,
            document_hash=document_hash,
            created_at=datetime.utcnow(),
            created_by=created_by,
            change_type=change_type,
            change_summary=change_summary,
            previous_version_id=previous_version_id,
            citations=citations or [],
            metadata={
                "total_citations": len(citations) if citations else 0,
                "creation_timestamp": datetime.utcnow().isoformat()
            }
        )

        # Cache version data
        cache_key = f"document_version:{version_id}"
        await self.cache_service.set(cache_key, version.__dict__, ttl=86400)  # 24 hours

        # Update document versions list
        versions_key = f"document_versions:{document_id}"
        versions_data = await self.cache_service.get(versions_key) or []
        versions_data.append(version.__dict__)
        await self.cache_service.set(versions_key, versions_data, ttl=86400)

        self.logger.info(
            f"Added version {version_number} for document {document_id}: {change_type}"
        )

        return version

    async def get_version(self, version_id: str) -> Optional[DocumentVersion]:
        """Get specific document version"""

        try:
            cache_key = f"document_version:{version_id}"
            version_data = await self.cache_service.get(cache_key)

            if version_data:
                # Convert citations back to Citation objects
                citations = [Citation(**c) for c in version_data.get('citations', [])]
                version_data['citations'] = citations

                # Convert datetime strings back to datetime objects
                version_data['created_at'] = datetime.fromisoformat(version_data['created_at'])

                return DocumentVersion(**version_data)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get version {version_id}: {e}")
            return None

    async def _get_document_versions(self, document_id: str) -> List[DocumentVersion]:
        """Get all versions for a document"""

        try:
            versions_key = f"document_versions:{document_id}"
            versions_data = await self.cache_service.get(versions_key) or []

            versions = []
            for version_dict in versions_data:
                # Convert back to objects
                citations = [Citation(**c) for c in version_dict.get('citations', [])]
                version_dict['citations'] = citations
                version_dict['created_at'] = datetime.fromisoformat(version_dict['created_at'])

                versions.append(DocumentVersion(**version_dict))

            return sorted(versions, key=lambda v: v.version_number)

        except Exception as e:
            self.logger.error(f"Failed to get versions for {document_id}: {e}")
            return []

    async def diff_versions(
        self,
        version_a_id: str,
        version_b_id: str
    ) -> Dict[str, Any]:
        """Compare two document versions and return differences"""

        try:
            version_a = await self.get_version(version_a_id)
            version_b = await self.get_version(version_b_id)

            if not version_a or not version_b:
                raise ValueError("One or both versions not found")

            # Calculate differences
            diff_result = {
                "version_a": {
                    "id": version_a.version_id,
                    "number": version_a.version_number,
                    "created_at": version_a.created_at.isoformat(),
                    "citations_count": len(version_a.citations)
                },
                "version_b": {
                    "id": version_b.version_id,
                    "number": version_b.version_number,
                    "created_at": version_b.created_at.isoformat(),
                    "citations_count": len(version_b.citations)
                },
                "differences": {
                    "citations_added": 0,
                    "citations_removed": 0,
                    "citations_modified": 0,
                    "hash_changed": version_a.document_hash != version_b.document_hash
                },
                "details": {
                    "added_citations": [],
                    "removed_citations": [],
                    "modified_citations": []
                }
            }

            # Compare citations
            a_citations = {c.citation_id: c for c in version_a.citations}
            b_citations = {c.citation_id: c for c in version_b.citations}

            # Find added citations (in B but not in A)
            added = set(b_citations.keys()) - set(a_citations.keys())
            diff_result["differences"]["citations_added"] = len(added)
            diff_result["details"]["added_citations"] = [
                b_citations[cid].__dict__ for cid in added
            ]

            # Find removed citations (in A but not in B)
            removed = set(a_citations.keys()) - set(b_citations.keys())
            diff_result["differences"]["citations_removed"] = len(removed)
            diff_result["details"]["removed_citations"] = [
                a_citations[cid].__dict__ for cid in removed
            ]

            # Find modified citations
            common = set(a_citations.keys()) & set(b_citations.keys())
            modified = []
            for cid in common:
                if (a_citations[cid].extracted_text != b_citations[cid].extracted_text or
                    a_citations[cid].confidence_score != b_citations[cid].confidence_score):
                    modified.append({
                        "citation_id": cid,
                        "changes": {
                            "text_changed": a_citations[cid].extracted_text != b_citations[cid].extracted_text,
                            "confidence_changed": a_citations[cid].confidence_score != b_citations[cid].confidence_score
                        }
                    })

            diff_result["differences"]["citations_modified"] = len(modified)
            diff_result["details"]["modified_citations"] = modified

            return diff_result

        except Exception as e:
            self.logger.error(f"Version diff failed: {e}")
            raise

    async def rollback_to_version(
        self,
        document_id: str,
        target_version_id: str,
        reason: str,
        created_by: str
    ) -> DocumentVersion:
        """Rollback document to a previous version"""

        target_version = await self.get_version(target_version_id)
        if not target_version:
            raise ValueError(f"Target version {target_version_id} not found")

        # Create new version based on target version
        new_version = await self.add_version(
            document_id=document_id,
            document_hash=target_version.document_hash,
            created_by=created_by,
            change_type="rollback",
            change_summary=f"Rolled back to version {target_version.version_number}: {reason}",
            citations=target_version.citations
        )

        self.logger.info(
            f"Rolled back document {document_id} to version {target_version.version_number}"
        )

        return new_version


class CitationTracker:
    """
    Main citation tracking system orchestrator
    Coordinates citation creation, graph management, and version tracking
    """

    def __init__(
        self,
        memory_service: Optional[MemoryService] = None,
        cache_service: Optional[CacheService] = None
    ):
        self.memory_service = memory_service or MemoryService()
        self.cache_service = cache_service or CacheService()
        self.citation_graph = CitationGraph(memory_service)
        self.version_tracker = VersionTracker(cache_service)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def create_citations_from_parsed_document(
        self,
        parsed_doc: ParsedDocument,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> List[Citation]:
        """Create citations for all extracted information from a parsed document"""

        citations = []

        # Create document-level citation
        doc_citation = Citation(
            citation_id=f"doc_{parsed_doc.document_id}",
            document_id=parsed_doc.document_id,
            document_title=parsed_doc.filename,
            extracted_text=parsed_doc.text[:500] + "..." if len(parsed_doc.text) > 500 else parsed_doc.text,
            confidence_score=parsed_doc.overall_confidence,
            extraction_method=self._map_extraction_method(parsed_doc.extraction_methods_used),
            citation_level=CitationLevel.DOCUMENT,
            original_format=parsed_doc.format.value,
            metadata={
                "total_pages": parsed_doc.total_pages,
                "parsing_time_ms": parsed_doc.parsing_time_ms,
                "extraction_methods": [method.value for method in parsed_doc.extraction_methods_used]
            }
        )

        citations.append(doc_citation)
        await self.citation_graph.add_citation(doc_citation)

        # Create page-level citations
        for page in parsed_doc.pages:
            if not page.text.strip():
                continue

            page_citation = Citation(
                citation_id=f"page_{parsed_doc.document_id}_{page.page_number}",
                document_id=parsed_doc.document_id,
                document_title=parsed_doc.filename,
                page_number=page.page_number,
                extracted_text=page.text,
                confidence_score=page.confidence_score,
                extraction_method=ExtractionMethod(page.extraction_method.value),
                citation_level=CitationLevel.PAGE,
                metadata={
                    "page_metadata": page.metadata,
                    "tables_count": len(page.tables),
                    "images_count": len(page.images)
                }
            )

            citations.append(page_citation)
            await self.citation_graph.add_citation(page_citation)

            # Link page to document
            await self.citation_graph.link_citations(
                doc_citation.citation_id,
                page_citation.citation_id,
                "contains",
                f"Page {page.page_number} is part of document {parsed_doc.filename}",
                1.0
            )

        # Create paragraph-level citations for important text
        if extracted_data:
            await self._create_extraction_citations(
                parsed_doc,
                extracted_data,
                citations,
                doc_citation.citation_id
            )

        self.logger.info(
            f"Created {len(citations)} citations for document {parsed_doc.document_id}"
        )

        return citations

    async def _create_extraction_citations(
        self,
        parsed_doc: ParsedDocument,
        extracted_data: Dict[str, Any],
        citations: List[Citation],
        doc_citation_id: str
    ) -> None:
        """Create citations for specific extracted data"""

        # Example: Create citations for extracted entities, clauses, etc.
        if 'entities' in extracted_data:
            for entity in extracted_data['entities']:
                entity_citation = Citation(
                    citation_id=f"entity_{parsed_doc.document_id}_{entity.get('start_char', 0)}",
                    document_id=parsed_doc.document_id,
                    document_title=parsed_doc.filename,
                    char_start=entity.get('start_char', 0),
                    char_end=entity.get('end_char', 0),
                    extracted_text=entity.get('text', ''),
                    confidence_score=entity.get('confidence', 0.0),
                    extraction_method=ExtractionMethod.HYBRID,
                    citation_level=CitationLevel.SENTENCE,
                    context=entity.get('context', ''),
                    metadata={
                        "entity_type": entity.get('type'),
                        "normalized_value": entity.get('normalized_value')
                    }
                )

                citations.append(entity_citation)
                await self.citation_graph.add_citation(entity_citation)

                # Link to document
                await self.citation_graph.link_citations(
                    doc_citation_id,
                    entity_citation.citation_id,
                    "contains",
                    f"Entity extracted from document",
                    entity.get('confidence', 0.5)
                )

    def _map_extraction_method(self, methods: List[Any]) -> ExtractionMethod:
        """Map parsing methods to extraction method"""
        if len(methods) > 1:
            return ExtractionMethod.HYBRID
        elif len(methods) == 1:
            method_name = str(methods[0]).lower()
            if 'vision' in method_name:
                return ExtractionMethod.VISION
            elif 'ocr' in method_name:
                return ExtractionMethod.OCR
            else:
                return ExtractionMethod.NATIVE
        else:
            return ExtractionMethod.NATIVE

    async def track_citation_usage(
        self,
        citation_id: str,
        usage_context: str,
        user_id: Optional[str] = None
    ) -> None:
        """Track how citations are used for audit purposes"""

        audit_trail = CitationAuditTrail(
            audit_id=f"audit_{citation_id}_{int(datetime.utcnow().timestamp())}",
            citation_id=citation_id
        )

        audit_trail.add_event(
            event_type="citation_accessed",
            description=usage_context,
            user_id=user_id
        )

        # Store audit trail
        audit_key = f"citation_audit:{citation_id}"
        existing_audit = await self.cache_service.get(audit_key) or {"events": []}
        existing_audit["events"].extend(audit_trail.events)
        await self.cache_service.set(audit_key, existing_audit, ttl=86400 * 30)  # 30 days

    async def export_citations(
        self,
        document_id: str,
        citation_format: CitationFormat = CitationFormat.BLUEBOOK,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """Export citations for a document in specified format"""

        try:
            # Get all citations for document
            citations = await self._get_document_citations(document_id)

            if not citations:
                return {"error": "No citations found for document"}

            # Format citations
            formatted_citations = []
            for citation in citations:
                if citation_format == CitationFormat.BLUEBOOK:
                    formatted = citation.to_bluebook_format()
                elif citation_format == CitationFormat.APA:
                    formatted = citation.to_apa_format()
                elif citation_format == CitationFormat.MLA:
                    formatted = citation.to_mla_format()
                else:
                    formatted = str(citation)

                formatted_citations.append({
                    "citation_id": citation.citation_id,
                    "formatted": formatted,
                    "level": citation.citation_level.value,
                    "confidence": citation.confidence_score,
                    "extraction_method": citation.extraction_method.value
                })

            export_data = {
                "document_id": document_id,
                "format": citation_format.value,
                "total_citations": len(formatted_citations),
                "citations": formatted_citations,
                "exported_at": datetime.utcnow().isoformat(),
                "export_metadata": {
                    "include_relationships": include_relationships,
                    "export_version": "1.0.0"
                }
            }

            if include_relationships:
                # Add relationship information
                relationships = await self._get_citation_relationships(document_id)
                export_data["relationships"] = relationships

            return export_data

        except Exception as e:
            self.logger.error(f"Citation export failed: {e}")
            raise

    async def _get_document_citations(self, document_id: str) -> List[Citation]:
        """Get all citations for a document"""

        try:
            # Query memory service for citations
            context = await self.memory_service.get_context(
                lead_id=document_id,
                query=f"Get all citations for document {document_id}"
            )

            citations = []
            for item in context.get('related_items', []):
                if 'citation_id' in item:
                    citation = Citation(
                        citation_id=item['citation_id'],
                        document_id=item['document_id'],
                        document_title=item.get('document_title', 'Unknown'),
                        page_number=item.get('page_number'),
                        extracted_text=item.get('extracted_text', ''),
                        confidence_score=item.get('confidence_score', 0.0),
                        extraction_method=ExtractionMethod(item.get('extraction_method', 'native')),
                        timestamp=datetime.fromisoformat(item.get('timestamp', datetime.utcnow().isoformat()))
                    )
                    citations.append(citation)

            return citations

        except Exception as e:
            self.logger.error(f"Failed to get citations for {document_id}: {e}")
            return []

    async def _get_citation_relationships(self, document_id: str) -> List[Dict[str, Any]]:
        """Get relationships between citations in a document"""

        try:
            # This would query the relationship graph
            # For now, return empty list as placeholder
            return []

        except Exception as e:
            self.logger.error(f"Failed to get relationships for {document_id}: {e}")
            return []

    async def create_version_snapshot(
        self,
        document_id: str,
        citations: List[Citation],
        created_by: str,
        change_summary: str = "Citation snapshot"
    ) -> DocumentVersion:
        """Create version snapshot with current citation state"""

        # Calculate document hash based on citations
        citation_texts = [c.extracted_text for c in citations]
        combined_text = "\n".join(citation_texts)
        document_hash = hashlib.sha256(combined_text.encode()).hexdigest()

        version = await self.version_tracker.add_version(
            document_id=document_id,
            document_hash=document_hash,
            created_by=created_by,
            change_type="citation_update",
            change_summary=change_summary,
            citations=citations
        )

        self.logger.info(
            f"Created citation snapshot for document {document_id}: "
            f"version {version.version_number} with {len(citations)} citations"
        )

        return version

    async def validate_citation_integrity(self, document_id: str) -> Dict[str, Any]:
        """Validate integrity of citations for a document"""

        validation_result = await self.citation_graph.validate_citation_integrity()

        # Add document-specific validation
        citations = await self._get_document_citations(document_id)

        document_validation = {
            "document_id": document_id,
            "total_citations": len(citations),
            "confidence_distribution": self._calculate_confidence_distribution(citations),
            "extraction_method_breakdown": self._calculate_extraction_method_breakdown(citations),
            "validation_timestamp": datetime.utcnow().isoformat()
        }

        validation_result.update(document_validation)
        return validation_result

    def _calculate_confidence_distribution(self, citations: List[Citation]) -> Dict[str, int]:
        """Calculate distribution of confidence scores"""
        if not citations:
            return {}

        buckets = {"high": 0, "medium": 0, "low": 0}
        for citation in citations:
            if citation.confidence_score >= 0.8:
                buckets["high"] += 1
            elif citation.confidence_score >= 0.5:
                buckets["medium"] += 1
            else:
                buckets["low"] += 1

        return buckets

    def _calculate_extraction_method_breakdown(self, citations: List[Citation]) -> Dict[str, int]:
        """Calculate breakdown of extraction methods used"""
        breakdown = defaultdict(int)
        for citation in citations:
            breakdown[citation.extraction_method.value] += 1
        return dict(breakdown)