"""
Quality Assurance Engine

Multi-dimensional confidence scoring and validation engine for processed documents.
Determines review requirements, tracks quality metrics, and ensures business rule
compliance with enterprise-grade accuracy standards.

Integration Points:
- Validates Phase 1 processing results (parsing, legal analysis, citations, risk)
- Routes low-confidence documents to human review
- Tracks quality drift and model performance
- Implements configurable business rules per client
"""

import asyncio
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any, Union
import json
import math

import numpy as np
from sklearn.metrics import precision_recall_fscore_support
from sqlalchemy.orm import Session

# Import Phase 1 components for validation
from ..document_engine import ParsedDocument, LegalAnalyzer, RiskExtractor
from ..config.settings import settings
from .database_schema import (
    DocumentVersion, QualityMetrics, ReviewAssignment, AuditTrail,
    ProcessingStatus, ReviewPriority, AuditEventType
)

# Import EnterpriseHub patterns
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.security.audit_logger import AuditLogger

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"    # Blocks processing
    HIGH = "high"           # Requires review
    MEDIUM = "medium"       # Warning flag
    LOW = "low"            # Informational
    INFO = "info"          # Logging only

class QualityDimension(Enum):
    """Quality assessment dimensions for comprehensive scoring."""
    PARSING_ACCURACY = "parsing_accuracy"
    TEXT_EXTRACTION = "text_extraction"
    ENTITY_RECOGNITION = "entity_recognition"
    CLAUSE_IDENTIFICATION = "clause_identification"
    RISK_ASSESSMENT = "risk_assessment"
    CITATION_COMPLETENESS = "citation_completeness"
    BUSINESS_RULE_COMPLIANCE = "business_rule_compliance"
    CONTENT_COHERENCE = "content_coherence"
    METADATA_ACCURACY = "metadata_accuracy"
    PROCESSING_CONSISTENCY = "processing_consistency"

@dataclass
class ValidationIssue:
    """Individual validation issue with severity and context."""
    severity: ValidationSeverity
    dimension: QualityDimension
    description: str
    details: Dict[str, Any]
    confidence_impact: float = 0.0  # How much this impacts overall confidence (0-1)
    suggested_action: str = ""
    location: str = ""  # Page, paragraph, or section reference

@dataclass
class QualityScores:
    """Comprehensive quality scoring across all dimensions."""
    
    # Core confidence scores (0.0 - 1.0)
    parsing_confidence: float = 0.0
    entity_extraction_confidence: float = 0.0
    clause_identification_confidence: float = 0.0
    risk_assessment_confidence: float = 0.0
    citation_completeness_confidence: float = 0.0
    
    # Composite scores
    overall_confidence: float = 0.0
    business_rule_compliance: float = 1.0
    content_coherence_score: float = 0.0
    
    # Quality dimensions
    dimension_scores: Dict[QualityDimension, float] = field(default_factory=dict)
    
    # Statistical measures
    confidence_variance: float = 0.0
    score_distribution: Dict[str, float] = field(default_factory=dict)
    outlier_dimensions: List[QualityDimension] = field(default_factory=list)
    
    def calculate_overall_confidence(self, weights: Dict[QualityDimension, float] = None) -> float:
        """Calculate weighted overall confidence score."""
        
        # Default weights (can be customized per client)
        if not weights:
            weights = {
                QualityDimension.PARSING_ACCURACY: 0.25,
                QualityDimension.ENTITY_RECOGNITION: 0.20,
                QualityDimension.CLAUSE_IDENTIFICATION: 0.20,
                QualityDimension.RISK_ASSESSMENT: 0.15,
                QualityDimension.CITATION_COMPLETENESS: 0.10,
                QualityDimension.BUSINESS_RULE_COMPLIANCE: 0.10
            }
        
        # Calculate weighted score
        weighted_sum = 0.0
        total_weight = 0.0
        
        for dimension, weight in weights.items():
            if dimension in self.dimension_scores:
                weighted_sum += self.dimension_scores[dimension] * weight
                total_weight += weight
        
        self.overall_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        return self.overall_confidence
    
    def detect_outliers(self, threshold: float = 2.0) -> List[QualityDimension]:
        """Detect quality dimensions that are statistical outliers."""
        
        if len(self.dimension_scores) < 3:
            return []
        
        scores = list(self.dimension_scores.values())
        mean_score = statistics.mean(scores)
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
        
        outliers = []
        for dimension, score in self.dimension_scores.items():
            if std_dev > 0:
                z_score = abs(score - mean_score) / std_dev
                if z_score > threshold:
                    outliers.append(dimension)
        
        self.outlier_dimensions = outliers
        self.confidence_variance = std_dev
        return outliers

@dataclass
class ValidationResult:
    """Comprehensive validation result with scores and recommendations."""
    document_version_id: str
    overall_confidence: float
    quality_scores: QualityScores
    validation_issues: List[ValidationIssue] = field(default_factory=list)
    requires_human_review: bool = False
    recommended_review_priority: ReviewPriority = ReviewPriority.LOW
    business_rules_passed: bool = True
    processing_recommendations: List[str] = field(default_factory=list)
    quality_flags: Set[str] = field(default_factory=set)
    
    # Performance benchmarking
    compared_to_baseline: bool = False
    performance_percentile: float = 0.0
    historical_confidence_trend: float = 0.0
    
    # Audit trail
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    validation_duration_seconds: float = 0.0
    validated_by: str = "system"

class BusinessRuleEngine:
    """Configurable business rules engine for client-specific validation."""
    
    def __init__(self, client_id: str = None):
        self.client_id = client_id
        self.rules = self._load_business_rules()
        
    def _load_business_rules(self) -> Dict[str, Any]:
        """Load business rules configuration for client."""
        
        # Default business rules (can be customized per client)
        default_rules = {
            "minimum_confidence_thresholds": {
                "parsing": 0.85,
                "entity_extraction": 0.80,
                "clause_identification": 0.75,
                "risk_assessment": 0.70,
                "overall": 0.80
            },
            "required_entities": {
                "contract_parties": True,
                "effective_date": True,
                "governing_law": False,
                "financial_terms": True
            },
            "required_clauses": {
                "termination": True,
                "liability": True,
                "indemnification": False,
                "confidentiality": True
            },
            "risk_tolerances": {
                "unlimited_liability": "high",
                "auto_renewal": "medium", 
                "broad_indemnity": "high",
                "personal_guarantees": "critical"
            },
            "document_type_rules": {
                "nda": {
                    "max_term_years": 5,
                    "required_clauses": ["confidentiality", "return_of_materials"]
                },
                "service_agreement": {
                    "required_clauses": ["termination", "liability", "payment_terms"]
                }
            }
        }
        
        # TODO: Load client-specific overrides from database
        # client_rules = self._get_client_rules(self.client_id)
        # return {**default_rules, **client_rules}
        
        return default_rules
    
    def validate_business_rules(
        self,
        parsed_doc: ParsedDocument,
        legal_analysis: Any,
        risk_assessment: Any
    ) -> Tuple[bool, List[ValidationIssue]]:
        """Validate document against configured business rules."""
        
        issues = []
        rules_passed = True
        
        # Validate confidence thresholds
        confidence_issues = self._check_confidence_thresholds(parsed_doc, legal_analysis)
        issues.extend(confidence_issues)
        
        # Validate required entities
        entity_issues = self._check_required_entities(legal_analysis)
        issues.extend(entity_issues)
        
        # Validate required clauses
        clause_issues = self._check_required_clauses(legal_analysis)
        issues.extend(clause_issues)
        
        # Validate risk tolerances
        risk_issues = self._check_risk_tolerances(risk_assessment)
        issues.extend(risk_issues)
        
        # Check for critical issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            rules_passed = False
        
        return rules_passed, issues
    
    def _check_confidence_thresholds(self, parsed_doc, legal_analysis) -> List[ValidationIssue]:
        """Check if processing confidence meets minimum thresholds."""
        issues = []
        thresholds = self.rules["minimum_confidence_thresholds"]
        
        # Check parsing confidence
        if hasattr(parsed_doc, 'confidence_score'):
            if parsed_doc.confidence_score < thresholds["parsing"]:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.HIGH,
                    dimension=QualityDimension.PARSING_ACCURACY,
                    description=f"Parsing confidence {parsed_doc.confidence_score:.3f} below threshold {thresholds['parsing']}",
                    details={"actual": parsed_doc.confidence_score, "threshold": thresholds["parsing"]},
                    confidence_impact=0.3,
                    suggested_action="Consider re-processing with higher quality OCR or manual review"
                ))
        
        # Check legal analysis confidence
        if hasattr(legal_analysis, 'overall_confidence'):
            if legal_analysis.overall_confidence < thresholds.get("entity_extraction", 0.8):
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.MEDIUM,
                    dimension=QualityDimension.ENTITY_RECOGNITION,
                    description=f"Legal analysis confidence below threshold",
                    details={"confidence": legal_analysis.overall_confidence},
                    confidence_impact=0.2
                ))
        
        return issues
    
    def _check_required_entities(self, legal_analysis) -> List[ValidationIssue]:
        """Check if required legal entities are identified."""
        issues = []
        required = self.rules["required_entities"]
        
        if hasattr(legal_analysis, 'entities'):
            found_entities = {entity.entity_type for entity in legal_analysis.entities}
            
            for entity_type, is_required in required.items():
                if is_required and entity_type not in found_entities:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.HIGH,
                        dimension=QualityDimension.ENTITY_RECOGNITION,
                        description=f"Required entity '{entity_type}' not found",
                        details={"missing_entity": entity_type, "found_entities": list(found_entities)},
                        confidence_impact=0.25,
                        suggested_action=f"Manual review required to identify {entity_type}"
                    ))
        
        return issues
    
    def _check_required_clauses(self, legal_analysis) -> List[ValidationIssue]:
        """Check if required legal clauses are identified."""
        issues = []
        required = self.rules["required_clauses"]
        
        if hasattr(legal_analysis, 'clauses'):
            found_clauses = {clause.clause_type for clause in legal_analysis.clauses}
            
            for clause_type, is_required in required.items():
                if is_required and clause_type not in found_clauses:
                    issues.append(ValidationIssue(
                        severity=ValidationSeverity.MEDIUM,
                        dimension=QualityDimension.CLAUSE_IDENTIFICATION,
                        description=f"Required clause '{clause_type}' not found",
                        details={"missing_clause": clause_type},
                        confidence_impact=0.15,
                        suggested_action=f"Review document for {clause_type} clause"
                    ))
        
        return issues
    
    def _check_risk_tolerances(self, risk_assessment) -> List[ValidationIssue]:
        """Check if identified risks exceed client tolerance levels."""
        issues = []
        tolerances = self.rules["risk_tolerances"]
        
        if hasattr(risk_assessment, 'red_flags'):
            for red_flag in risk_assessment.red_flags:
                risk_type = red_flag.flag_type
                if risk_type in tolerances:
                    tolerance_level = tolerances[risk_type]
                    
                    if tolerance_level == "critical":
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.CRITICAL,
                            dimension=QualityDimension.RISK_ASSESSMENT,
                            description=f"Critical risk flag: {risk_type}",
                            details={"risk_type": risk_type, "tolerance": tolerance_level},
                            confidence_impact=0.4,
                            suggested_action="Immediate legal review required"
                        ))
        
        return issues

class QualityAssurance:
    """
    Multi-dimensional quality assurance engine for document processing validation.
    
    Features:
    - Comprehensive confidence scoring across 10+ dimensions
    - Configurable business rules per client
    - Statistical outlier detection
    - Performance benchmarking and trend analysis
    - Automated review routing based on quality scores
    """
    
    def __init__(self, cache_service: CacheService = None):
        """Initialize quality assurance engine."""
        
        self.cache_service = cache_service or CacheService()
        self.audit_logger = AuditLogger()
        
        # Quality assessment configuration
        self.confidence_weights = {
            QualityDimension.PARSING_ACCURACY: 0.25,
            QualityDimension.ENTITY_RECOGNITION: 0.20,
            QualityDimension.CLAUSE_IDENTIFICATION: 0.20,
            QualityDimension.RISK_ASSESSMENT: 0.15,
            QualityDimension.CITATION_COMPLETENESS: 0.10,
            QualityDimension.BUSINESS_RULE_COMPLIANCE: 0.10
        }
        
        # Review thresholds
        self.review_thresholds = {
            "auto_approval": 0.95,    # No review needed
            "spot_check": 0.85,       # Random spot checks
            "quality_review": 0.75,   # Focused quality review
            "full_review": 0.65,      # Comprehensive review
            "reject": 0.50           # Automatic rejection
        }
        
        # Performance tracking
        self.baseline_metrics = self._load_baseline_metrics()
        self.quality_trends = {}
        
        logger.info("QualityAssurance engine initialized")
    
    def _load_baseline_metrics(self) -> Dict[str, float]:
        """Load historical baseline metrics for comparison."""
        
        # TODO: Load from database/cache
        # For now, use default baselines
        return {
            "average_parsing_confidence": 0.92,
            "average_entity_confidence": 0.88,
            "average_clause_confidence": 0.85,
            "average_risk_confidence": 0.82,
            "average_overall_confidence": 0.87,
            "review_rate": 0.15,  # 15% of documents need review
            "approval_rate": 0.94  # 94% of documents are approved
        }
    
    async def validate_document_processing(
        self,
        doc_version: DocumentVersion,
        parsed_doc: ParsedDocument,
        legal_analysis: Any,
        risk_assessment: Any = None,
        citations: List[Any] = None,
        client_id: str = None
    ) -> ValidationResult:
        """
        Comprehensive validation of document processing results.
        
        Returns ValidationResult with quality scores, issues, and recommendations.
        """
        
        start_time = datetime.utcnow()
        
        try:
            # Initialize business rules engine for client
            business_rules = BusinessRuleEngine(client_id or doc_version.client_id)
            
            # Calculate quality scores across all dimensions
            quality_scores = await self._calculate_quality_scores(
                parsed_doc, legal_analysis, risk_assessment, citations
            )
            
            # Validate against business rules
            rules_passed, business_issues = business_rules.validate_business_rules(
                parsed_doc, legal_analysis, risk_assessment
            )
            
            # Detect statistical outliers in quality dimensions
            outliers = quality_scores.detect_outliers()
            outlier_issues = self._create_outlier_issues(outliers, quality_scores)
            
            # Combine all validation issues
            all_issues = business_issues + outlier_issues
            
            # Determine review requirements
            requires_review, review_priority = self._determine_review_requirements(
                quality_scores, all_issues
            )
            
            # Generate processing recommendations
            recommendations = self._generate_recommendations(quality_scores, all_issues)
            
            # Create quality flags
            quality_flags = self._generate_quality_flags(quality_scores, all_issues)
            
            # Performance benchmarking
            performance_percentile = self._calculate_performance_percentile(quality_scores)
            
            # Create validation result
            result = ValidationResult(
                document_version_id=doc_version.id,
                overall_confidence=quality_scores.overall_confidence,
                quality_scores=quality_scores,
                validation_issues=all_issues,
                requires_human_review=requires_review,
                recommended_review_priority=review_priority,
                business_rules_passed=rules_passed,
                processing_recommendations=recommendations,
                quality_flags=quality_flags,
                compared_to_baseline=True,
                performance_percentile=performance_percentile,
                validation_duration_seconds=(datetime.utcnow() - start_time).total_seconds()
            )
            
            # Store quality metrics in database
            await self._store_quality_metrics(doc_version, result)
            
            # Update quality trends
            self._update_quality_trends(quality_scores)
            
            # Audit log validation
            await self.audit_logger.log_event(
                event_type=AuditEventType.QUALITY_CHECK,
                event_description=f"Quality validation completed with {len(all_issues)} issues",
                document_version_id=doc_version.id,
                event_data={
                    "overall_confidence": quality_scores.overall_confidence,
                    "requires_review": requires_review,
                    "issues_count": len(all_issues),
                    "business_rules_passed": rules_passed
                }
            )
            
            logger.info(
                f"Quality validation completed for {doc_version.id}: "
                f"confidence={quality_scores.overall_confidence:.3f}, "
                f"issues={len(all_issues)}, review={requires_review}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Quality validation failed for {doc_version.id}: {e}")
            
            # Return minimal validation result on error
            return ValidationResult(
                document_version_id=doc_version.id,
                overall_confidence=0.0,
                quality_scores=QualityScores(),
                validation_issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        dimension=QualityDimension.PROCESSING_CONSISTENCY,
                        description=f"Quality validation failed: {str(e)}",
                        details={"error": str(e)},
                        confidence_impact=1.0
                    )
                ],
                requires_human_review=True,
                recommended_review_priority=ReviewPriority.HIGH
            )
    
    async def _calculate_quality_scores(
        self,
        parsed_doc: ParsedDocument,
        legal_analysis: Any,
        risk_assessment: Any = None,
        citations: List[Any] = None
    ) -> QualityScores:
        """Calculate comprehensive quality scores across all dimensions."""
        
        scores = QualityScores()
        
        # 1. Parsing accuracy assessment
        scores.parsing_confidence = self._assess_parsing_quality(parsed_doc)
        scores.dimension_scores[QualityDimension.PARSING_ACCURACY] = scores.parsing_confidence
        
        # 2. Entity extraction confidence
        scores.entity_extraction_confidence = self._assess_entity_extraction(legal_analysis)
        scores.dimension_scores[QualityDimension.ENTITY_RECOGNITION] = scores.entity_extraction_confidence
        
        # 3. Clause identification assessment
        scores.clause_identification_confidence = self._assess_clause_identification(legal_analysis)
        scores.dimension_scores[QualityDimension.CLAUSE_IDENTIFICATION] = scores.clause_identification_confidence
        
        # 4. Risk assessment quality
        if risk_assessment:
            scores.risk_assessment_confidence = self._assess_risk_quality(risk_assessment)
            scores.dimension_scores[QualityDimension.RISK_ASSESSMENT] = scores.risk_assessment_confidence
        
        # 5. Citation completeness
        if citations:
            scores.citation_completeness_confidence = self._assess_citation_completeness(citations, parsed_doc)
            scores.dimension_scores[QualityDimension.CITATION_COMPLETENESS] = scores.citation_completeness_confidence
        
        # 6. Content coherence (semantic consistency)
        scores.content_coherence_score = self._assess_content_coherence(parsed_doc, legal_analysis)
        scores.dimension_scores[QualityDimension.CONTENT_COHERENCE] = scores.content_coherence_score
        
        # 7. Metadata accuracy
        metadata_score = self._assess_metadata_accuracy(parsed_doc)
        scores.dimension_scores[QualityDimension.METADATA_ACCURACY] = metadata_score
        
        # 8. Processing consistency
        consistency_score = self._assess_processing_consistency(parsed_doc, legal_analysis)
        scores.dimension_scores[QualityDimension.PROCESSING_CONSISTENCY] = consistency_score
        
        # Calculate overall confidence with weighted scoring
        scores.calculate_overall_confidence(self.confidence_weights)
        
        return scores
    
    def _assess_parsing_quality(self, parsed_doc: ParsedDocument) -> float:
        """Assess document parsing quality and accuracy."""
        
        confidence_factors = []
        
        # Text extraction confidence
        if hasattr(parsed_doc, 'confidence_score'):
            confidence_factors.append(parsed_doc.confidence_score)
        
        # Page count reasonableness (non-zero pages)
        if hasattr(parsed_doc, 'pages') and parsed_doc.pages:
            page_factor = min(1.0, len(parsed_doc.pages) / 100)  # Normalize to reasonable page count
            confidence_factors.append(0.8 + 0.2 * page_factor)
        
        # Text density (characters per page)
        if hasattr(parsed_doc, 'full_text') and parsed_doc.full_text and hasattr(parsed_doc, 'pages'):
            avg_chars_per_page = len(parsed_doc.full_text) / max(1, len(parsed_doc.pages))
            # Reasonable range: 1000-5000 characters per page
            density_factor = min(1.0, max(0.3, avg_chars_per_page / 3000))
            confidence_factors.append(density_factor)
        
        # Structure preservation (tables, headings, etc.)
        if hasattr(parsed_doc, 'structure_elements'):
            structure_factor = 0.9 if parsed_doc.structure_elements else 0.7
            confidence_factors.append(structure_factor)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _assess_entity_extraction(self, legal_analysis) -> float:
        """Assess quality of legal entity extraction."""
        
        if not hasattr(legal_analysis, 'entities'):
            return 0.3
        
        entities = legal_analysis.entities
        entity_count = len(entities)
        
        # Confidence factors
        confidence_factors = []
        
        # Entity count reasonableness (2-20 entities typical for contracts)
        if 2 <= entity_count <= 20:
            count_factor = 1.0
        elif entity_count < 2:
            count_factor = 0.4  # Too few entities
        else:
            count_factor = max(0.6, 1.0 - (entity_count - 20) * 0.02)  # Too many entities
        confidence_factors.append(count_factor)
        
        # Entity confidence scores
        if entities:
            entity_confidences = [getattr(entity, 'confidence', 0.8) for entity in entities]
            avg_confidence = statistics.mean(entity_confidences)
            confidence_factors.append(avg_confidence)
        
        # Entity type diversity
        if entities:
            entity_types = {getattr(entity, 'entity_type', 'unknown') for entity in entities}
            diversity_factor = min(1.0, len(entity_types) / 5)  # Expect ~5 different types
            confidence_factors.append(diversity_factor)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _assess_clause_identification(self, legal_analysis) -> float:
        """Assess quality of legal clause identification."""
        
        if not hasattr(legal_analysis, 'clauses'):
            return 0.3
        
        clauses = legal_analysis.clauses
        clause_count = len(clauses)
        
        confidence_factors = []
        
        # Clause count reasonableness (5-25 clauses typical)
        if 5 <= clause_count <= 25:
            count_factor = 1.0
        elif clause_count < 5:
            count_factor = 0.5
        else:
            count_factor = max(0.7, 1.0 - (clause_count - 25) * 0.02)
        confidence_factors.append(count_factor)
        
        # Clause confidence scores
        if clauses:
            clause_confidences = [getattr(clause, 'confidence', 0.8) for clause in clauses]
            avg_confidence = statistics.mean(clause_confidences)
            confidence_factors.append(avg_confidence)
        
        # Critical clause coverage
        if clauses:
            clause_types = {getattr(clause, 'clause_type', 'unknown') for clause in clauses}
            critical_types = {'termination', 'liability', 'payment_terms', 'confidentiality'}
            coverage = len(clause_types.intersection(critical_types)) / len(critical_types)
            confidence_factors.append(coverage)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.5
    
    def _assess_risk_quality(self, risk_assessment) -> float:
        """Assess quality of risk assessment and red flag detection."""
        
        confidence_factors = []
        
        # Overall risk confidence
        if hasattr(risk_assessment, 'confidence_score'):
            confidence_factors.append(risk_assessment.confidence_score)
        
        # Risk flag reasonableness
        if hasattr(risk_assessment, 'red_flags'):
            flag_count = len(risk_assessment.red_flags)
            # 0-10 red flags is reasonable
            if flag_count <= 10:
                flag_factor = 1.0 - (flag_count * 0.05)  # Slight penalty for more flags
            else:
                flag_factor = 0.5  # Too many flags suggests over-detection
            confidence_factors.append(max(0.3, flag_factor))
        
        # Risk severity distribution
        if hasattr(risk_assessment, 'risks'):
            risks = risk_assessment.risks
            if risks:
                severity_counts = {}
                for risk in risks:
                    severity = getattr(risk, 'severity', 'medium')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Expect more medium/low risks than critical/high
                total_risks = len(risks)
                critical_high_ratio = (severity_counts.get('critical', 0) + severity_counts.get('high', 0)) / total_risks
                
                # Reasonable range: 10-40% critical/high risks
                if 0.1 <= critical_high_ratio <= 0.4:
                    severity_factor = 1.0
                else:
                    severity_factor = 0.7
                confidence_factors.append(severity_factor)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.7
    
    def _assess_citation_completeness(self, citations: List[Any], parsed_doc: ParsedDocument) -> float:
        """Assess completeness and accuracy of citation tracking."""
        
        if not citations:
            return 0.2
        
        confidence_factors = []
        
        # Citation density (citations per page)
        page_count = len(getattr(parsed_doc, 'pages', [])) or 1
        citation_density = len(citations) / page_count
        
        # Expect 2-10 citations per page
        if 2 <= citation_density <= 10:
            density_factor = 1.0
        elif citation_density < 2:
            density_factor = citation_density / 2  # Linear penalty for low density
        else:
            density_factor = max(0.7, 1.0 - (citation_density - 10) * 0.05)
        confidence_factors.append(density_factor)
        
        # Citation accuracy (if confidence scores available)
        if citations and hasattr(citations[0], 'confidence'):
            citation_confidences = [getattr(c, 'confidence', 0.8) for c in citations]
            avg_confidence = statistics.mean(citation_confidences)
            confidence_factors.append(avg_confidence)
        
        # Citation format consistency
        if citations:
            formats = {getattr(c, 'format', 'unknown') for c in citations}
            format_consistency = 1.0 if len(formats) == 1 else 0.8
            confidence_factors.append(format_consistency)
        
        return statistics.mean(confidence_factors) if confidence_factors else 0.6
    
    def _assess_content_coherence(self, parsed_doc: ParsedDocument, legal_analysis) -> float:
        """Assess semantic coherence between parsing and analysis results."""
        
        # Basic coherence checks
        coherence_factors = []
        
        # Text length vs analysis complexity correlation
        if hasattr(parsed_doc, 'full_text') and parsed_doc.full_text:
            text_length = len(parsed_doc.full_text)
            
            # Entity count should correlate with text length
            entity_count = len(getattr(legal_analysis, 'entities', []))
            expected_entities = text_length / 500  # ~1 entity per 500 characters
            entity_ratio = entity_count / max(1, expected_entities)
            
            # Reasonable ratio: 0.5 - 2.0
            if 0.5 <= entity_ratio <= 2.0:
                entity_coherence = 1.0
            else:
                entity_coherence = max(0.5, 1.0 - abs(1.0 - entity_ratio))
            coherence_factors.append(entity_coherence)
        
        # Contract type consistency
        if hasattr(legal_analysis, 'contract_type') and hasattr(parsed_doc, 'full_text'):
            # Check if document content matches identified contract type
            contract_type = getattr(legal_analysis, 'contract_type', '').lower()
            text = getattr(parsed_doc, 'full_text', '').lower()
            
            type_keywords = {
                'nda': ['confidential', 'non-disclosure', 'proprietary'],
                'service_agreement': ['services', 'perform', 'deliverable'],
                'employment': ['employee', 'employment', 'salary', 'position'],
                'msa': ['master service', 'statement of work', 'sow']
            }
            
            if contract_type in type_keywords:
                keywords = type_keywords[contract_type]
                matches = sum(1 for keyword in keywords if keyword in text)
                keyword_factor = matches / len(keywords)
                coherence_factors.append(keyword_factor)
        
        return statistics.mean(coherence_factors) if coherence_factors else 0.8
    
    def _assess_metadata_accuracy(self, parsed_doc: ParsedDocument) -> float:
        """Assess accuracy of document metadata extraction."""
        
        accuracy_factors = []
        
        # File size reasonableness
        if hasattr(parsed_doc, 'file_size') and parsed_doc.file_size:
            # Reasonable range: 10KB - 50MB
            if 10000 <= parsed_doc.file_size <= 50000000:
                size_factor = 1.0
            else:
                size_factor = 0.8
            accuracy_factors.append(size_factor)
        
        # Content type consistency
        if hasattr(parsed_doc, 'content_type') and parsed_doc.content_type:
            valid_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/png', 'image/jpeg']
            type_factor = 1.0 if parsed_doc.content_type in valid_types else 0.7
            accuracy_factors.append(type_factor)
        
        # Page count reasonableness
        if hasattr(parsed_doc, 'pages') and parsed_doc.pages:
            page_count = len(parsed_doc.pages)
            # Reasonable range: 1-200 pages
            if 1 <= page_count <= 200:
                page_factor = 1.0
            else:
                page_factor = 0.8
            accuracy_factors.append(page_factor)
        
        return statistics.mean(accuracy_factors) if accuracy_factors else 0.9
    
    def _assess_processing_consistency(self, parsed_doc: ParsedDocument, legal_analysis) -> float:
        """Assess consistency across processing stages."""
        
        consistency_factors = []
        
        # Text preservation (comparing original vs processed text lengths)
        if hasattr(parsed_doc, 'full_text') and parsed_doc.full_text:
            original_length = len(parsed_doc.full_text)
            
            # Check if analysis results are proportional to text length
            entity_count = len(getattr(legal_analysis, 'entities', []))
            clause_count = len(getattr(legal_analysis, 'clauses', []))
            
            # Entities should be ~1 per 500 characters
            expected_entities = original_length / 500
            entity_consistency = 1.0 - min(0.5, abs(entity_count - expected_entities) / max(1, expected_entities))
            consistency_factors.append(entity_consistency)
            
            # Clauses should be ~1 per 1000 characters
            expected_clauses = original_length / 1000
            clause_consistency = 1.0 - min(0.5, abs(clause_count - expected_clauses) / max(1, expected_clauses))
            consistency_factors.append(clause_consistency)
        
        return statistics.mean(consistency_factors) if consistency_factors else 0.8
    
    def _create_outlier_issues(self, outliers: List[QualityDimension], quality_scores: QualityScores) -> List[ValidationIssue]:
        """Create validation issues for statistical outliers."""
        
        issues = []
        for dimension in outliers:
            score = quality_scores.dimension_scores.get(dimension, 0.0)
            
            issues.append(ValidationIssue(
                severity=ValidationSeverity.MEDIUM if score < 0.7 else ValidationSeverity.LOW,
                dimension=dimension,
                description=f"Quality score for {dimension.value} is a statistical outlier",
                details={
                    "dimension_score": score,
                    "variance": quality_scores.confidence_variance,
                    "is_outlier": True
                },
                confidence_impact=0.1,
                suggested_action="Review processing for this dimension"
            ))
        
        return issues
    
    def _determine_review_requirements(
        self,
        quality_scores: QualityScores,
        issues: List[ValidationIssue]
    ) -> Tuple[bool, ReviewPriority]:
        """Determine if document requires human review and at what priority."""
        
        overall_confidence = quality_scores.overall_confidence
        
        # Check for critical issues
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            return True, ReviewPriority.CRITICAL
        
        # Check confidence thresholds
        if overall_confidence < self.review_thresholds["reject"]:
            return True, ReviewPriority.CRITICAL
        elif overall_confidence < self.review_thresholds["full_review"]:
            return True, ReviewPriority.HIGH
        elif overall_confidence < self.review_thresholds["quality_review"]:
            return True, ReviewPriority.MEDIUM
        elif overall_confidence < self.review_thresholds["spot_check"]:
            # Random spot check (10% of documents)
            import random
            if random.random() < 0.1:
                return True, ReviewPriority.LOW
        
        # High quality - no review needed
        return False, ReviewPriority.LOW
    
    def _generate_recommendations(self, quality_scores: QualityScores, issues: List[ValidationIssue]) -> List[str]:
        """Generate processing recommendations based on quality assessment."""
        
        recommendations = []
        
        # Confidence-based recommendations
        if quality_scores.overall_confidence < 0.7:
            recommendations.append("Consider re-processing with higher quality settings")
        
        # Dimension-specific recommendations
        for dimension, score in quality_scores.dimension_scores.items():
            if score < 0.6:
                if dimension == QualityDimension.PARSING_ACCURACY:
                    recommendations.append("Document may require manual text extraction or OCR enhancement")
                elif dimension == QualityDimension.ENTITY_RECOGNITION:
                    recommendations.append("Review entity extraction - consider domain-specific model fine-tuning")
                elif dimension == QualityDimension.CLAUSE_IDENTIFICATION:
                    recommendations.append("Legal clause detection may need attorney review")
                elif dimension == QualityDimension.RISK_ASSESSMENT:
                    recommendations.append("Risk analysis requires expert validation")
        
        # Issue-based recommendations
        critical_issues = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            recommendations.append("Critical validation issues found - halt processing pending review")
        
        high_issues = [i for i in issues if i.severity == ValidationSeverity.HIGH]
        if len(high_issues) > 3:
            recommendations.append("Multiple high-severity issues - consider complete re-processing")
        
        return recommendations
    
    def _generate_quality_flags(self, quality_scores: QualityScores, issues: List[ValidationIssue]) -> Set[str]:
        """Generate quality flags for tracking and reporting."""
        
        flags = set()
        
        # Confidence-based flags
        if quality_scores.overall_confidence < 0.5:
            flags.add("LOW_CONFIDENCE")
        elif quality_scores.overall_confidence > 0.95:
            flags.add("HIGH_CONFIDENCE")
        
        # Variance flags
        if quality_scores.confidence_variance > 0.2:
            flags.add("HIGH_VARIANCE")
        
        # Outlier flags
        if quality_scores.outlier_dimensions:
            flags.add("STATISTICAL_OUTLIERS")
        
        # Issue-based flags
        severity_counts = {}
        for issue in issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        if severity_counts.get(ValidationSeverity.CRITICAL, 0) > 0:
            flags.add("CRITICAL_ISSUES")
        if severity_counts.get(ValidationSeverity.HIGH, 0) > 2:
            flags.add("MULTIPLE_HIGH_ISSUES")
        
        # Dimension-specific flags
        for dimension, score in quality_scores.dimension_scores.items():
            if score < 0.4:
                flags.add(f"POOR_{dimension.value.upper()}")
        
        return flags
    
    def _calculate_performance_percentile(self, quality_scores: QualityScores) -> float:
        """Calculate performance percentile compared to baseline metrics."""
        
        baseline = self.baseline_metrics
        current_confidence = quality_scores.overall_confidence
        baseline_confidence = baseline.get("average_overall_confidence", 0.87)
        
        # Simple percentile calculation (could be enhanced with historical data)
        if current_confidence >= baseline_confidence * 1.1:
            return 0.9  # Top 10%
        elif current_confidence >= baseline_confidence:
            return 0.75  # Top 25%
        elif current_confidence >= baseline_confidence * 0.9:
            return 0.5  # Median
        elif current_confidence >= baseline_confidence * 0.8:
            return 0.25  # Bottom 25%
        else:
            return 0.1  # Bottom 10%
    
    async def _store_quality_metrics(self, doc_version: DocumentVersion, result: ValidationResult):
        """Store quality metrics in database for tracking and analysis."""
        
        # This would integrate with the database session from BulkProcessor
        # For now, we'll update the DocumentVersion record directly
        
        doc_version.parsing_confidence = result.quality_scores.parsing_confidence
        doc_version.legal_confidence = result.quality_scores.entity_extraction_confidence
        doc_version.risk_confidence = result.quality_scores.risk_assessment_confidence
        doc_version.citation_completeness = result.quality_scores.citation_completeness_confidence
        doc_version.overall_confidence = result.quality_scores.overall_confidence
        
        # Set processing status based on validation results
        if result.requires_human_review:
            doc_version.processing_status = ProcessingStatus.HUMAN_REVIEW
        elif result.business_rules_passed and result.overall_confidence > 0.8:
            doc_version.processing_status = ProcessingStatus.COMPLETED
        else:
            doc_version.processing_status = ProcessingStatus.QUALITY_REVIEW
    
    def _update_quality_trends(self, quality_scores: QualityScores):
        """Update quality trends for monitoring and alerting."""
        
        # Update running averages (could be enhanced with time-series database)
        current_time = datetime.utcnow()
        
        # Store in cache for trending analysis
        trend_key = f"quality_trends:{current_time.strftime('%Y-%m-%d:%H')}"
        
        trend_data = {
            "timestamp": current_time.isoformat(),
            "overall_confidence": quality_scores.overall_confidence,
            "dimension_scores": {d.value: s for d, s in quality_scores.dimension_scores.items()},
            "confidence_variance": quality_scores.confidence_variance
        }
        
        # Store with 24-hour TTL
        asyncio.create_task(
            self.cache_service.set(trend_key, trend_data, ttl=86400)
        )
    
    async def get_quality_dashboard(self, time_range: str = "24h") -> Dict[str, Any]:
        """Generate quality dashboard metrics for monitoring."""
        
        # This would query the database for quality metrics over time
        # For now, return current baseline metrics
        
        return {
            "current_baseline": self.baseline_metrics,
            "quality_thresholds": self.review_thresholds,
            "confidence_weights": {d.value: w for d, w in self.confidence_weights.items()},
            "recent_trends": self.quality_trends
        }

# Testing and validation helpers
async def validate_quality_engine():
    """Test the quality assurance engine with sample data."""
    
    logger.info("Validating QualityAssurance engine...")
    
    # Mock objects for testing
    class MockParsedDoc:
        def __init__(self):
            self.confidence_score = 0.92
            self.full_text = "Sample contract text" * 100  # ~2000 characters
            self.pages = [1, 2, 3]
            self.structure_elements = True
    
    class MockLegalAnalysis:
        def __init__(self):
            self.overall_confidence = 0.88
            self.entities = [MockEntity() for _ in range(8)]
            self.clauses = [MockClause() for _ in range(12)]
            self.contract_type = "service_agreement"
    
    class MockEntity:
        def __init__(self):
            self.entity_type = "contract_parties"
            self.confidence = 0.9
    
    class MockClause:
        def __init__(self):
            self.clause_type = "termination"
            self.confidence = 0.85
    
    class MockRisk:
        def __init__(self):
            self.confidence_score = 0.82
            self.red_flags = []
            self.risks = []
    
    class MockDocVersion:
        def __init__(self):
            self.id = "test-doc-123"
            self.client_id = "test-client"
    
    # Test validation
    qa_engine = QualityAssurance()
    
    result = await qa_engine.validate_document_processing(
        doc_version=MockDocVersion(),
        parsed_doc=MockParsedDoc(),
        legal_analysis=MockLegalAnalysis(),
        risk_assessment=MockRisk()
    )
    
    assert result.overall_confidence > 0.8, "Quality validation should pass for good inputs"
    assert not result.requires_human_review, "High quality document should not need review"
    
    logger.info(f"Quality validation test passed: confidence={result.overall_confidence:.3f}")

if __name__ == "__main__":
    # Run validation test
    asyncio.run(validate_quality_engine())