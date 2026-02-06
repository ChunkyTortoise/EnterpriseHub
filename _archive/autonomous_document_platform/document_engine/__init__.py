"""
Document Engine - Phase 1: Document Intelligence

Core components for intelligent document parsing, legal analysis, and citation tracking.
Built on proven EnterpriseHub patterns with 95% component reusability.

Components:
- IntelligentParser: Multi-format document ingestion with vision models
- LegalAnalyzer: Domain-specific legal understanding
- CitationTracker: Legal-grade source tracking
- RiskExtractor: Contract risk identification

Architecture highlights:
- Vision model integration (Claude 3.5 Sonnet) for complex documents
- Multi-tier caching with semantic similarity
- Legal entity recognition and clause identification
- Risk assessment with confidence scoring
- Citation tracking for compliance
"""

from .intelligent_parser import IntelligentParser, DocumentParser, PDFParser, DOCXParser, ImageParser
from .legal_analyzer import LegalAnalyzer, LegalEntityExtractor, ClauseIdentifier, ContractAnalyzer
from .citation_tracker import CitationTracker, Citation, CitationGraph, VersionTracker
from .risk_extractor import RiskExtractor, Risk, RiskCategory, RedFlagDetector, RiskScorer

__version__ = "1.0.0"
__all__ = [
    "IntelligentParser",
    "DocumentParser",
    "PDFParser",
    "DOCXParser",
    "ImageParser",
    "LegalAnalyzer",
    "LegalEntityExtractor",
    "ClauseIdentifier",
    "ContractAnalyzer",
    "CitationTracker",
    "Citation",
    "CitationGraph",
    "VersionTracker",
    "RiskExtractor",
    "Risk",
    "RiskCategory",
    "RedFlagDetector",
    "RiskScorer"
]