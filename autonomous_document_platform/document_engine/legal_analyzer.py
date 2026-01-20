"""
Legal Analyzer - Domain-Specific Legal Intelligence

Extract legal-specific constructs and perform domain analysis on parsed documents.
Leverages EnterpriseHub patterns:
- ClaudeAssistant for intelligent analysis with conversation history
- LLMClient for structured output and entity extraction
- CacheService for clause-level semantic caching
- Existing analytics patterns for tracking analysis metrics

Key Features:
- Legal terminology recognition using spaCy + custom NER
- Clause identification and classification (indemnity, warranties, termination)
- Contract type detection (NDA, MSA, SLA, employment)
- Legal entity extraction (parties, signatories, witnesses)
- Obligation and right extraction
- Jurisdiction and governing law identification
- Date and deadline extraction with validation
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import spacy
from spacy.matcher import Matcher
import dateparser

# EnterpriseHub reused components
import sys
sys.path.append('/Users/cave/Documents/GitHub/EnterpriseHub')

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
from ghl_real_estate_ai.services.cache_service import CacheService
from autonomous_document_platform.document_engine.intelligent_parser import ParsedDocument
from autonomous_document_platform.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ContractType(str, Enum):
    """Types of legal contracts"""
    NDA = "nda"
    MSA = "msa"
    EMPLOYMENT = "employment"
    LEASE = "lease"
    PURCHASE = "purchase"
    SERVICE = "service"
    LICENSE = "license"
    PARTNERSHIP = "partnership"
    LOAN = "loan"
    INSURANCE = "insurance"
    UNKNOWN = "unknown"


class ClauseType(str, Enum):
    """Types of legal clauses"""
    INDEMNITY = "indemnity"
    LIABILITY = "liability"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    PAYMENT = "payment"
    FORCE_MAJEURE = "force_majeure"
    GOVERNING_LAW = "governing_law"
    DISPUTE_RESOLUTION = "dispute_resolution"
    WARRANTIES = "warranties"
    REPRESENTATIONS = "representations"
    COVENANTS = "covenants"
    DEFINITIONS = "definitions"
    AMENDMENTS = "amendments"
    SEVERABILITY = "severability"


class EntityType(str, Enum):
    """Types of legal entities"""
    PERSON = "person"
    ORGANIZATION = "organization"
    DATE = "date"
    MONEY = "money"
    PERCENTAGE = "percentage"
    JURISDICTION = "jurisdiction"
    TERM_DURATION = "term_duration"
    OBLIGATION = "obligation"
    RIGHT = "right"


@dataclass
class LegalEntity:
    """Extracted legal entity with metadata"""
    text: str
    entity_type: EntityType
    start_char: int
    end_char: int
    confidence: float
    context: str = ""
    normalized_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LegalClause:
    """Identified legal clause with classification"""
    clause_id: str
    clause_type: ClauseType
    text: str
    start_char: int
    end_char: int
    confidence: float
    page_number: Optional[int] = None
    section_number: Optional[str] = None
    obligations: List[str] = field(default_factory=list)
    rights: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LegalTerm:
    """Key legal term with definition and context"""
    term: str
    definition: str
    context: str
    importance_score: float
    page_references: List[int]
    related_clauses: List[str] = field(default_factory=list)


@dataclass
class ContractAnalysis:
    """Complete analysis of a legal contract"""
    document_id: str
    contract_type: ContractType
    contract_type_confidence: float
    parties: List[LegalEntity]
    entities: List[LegalEntity]
    clauses: List[LegalClause]
    key_terms: List[LegalTerm]
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None
    effective_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    term_duration: Optional[str] = None
    auto_renewal: bool = False
    critical_obligations: List[str] = field(default_factory=list)
    critical_rights: List[str] = field(default_factory=list)
    missing_clauses: List[ClauseType] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class LegalEntityExtractor:
    """Extract legal entities from documents using NER and pattern matching"""

    def __init__(self):
        # Load spaCy model (in production, use a legal-specific model)
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None

        self.matcher = Matcher(self.nlp.vocab) if self.nlp else None
        self._setup_legal_patterns()

    def _setup_legal_patterns(self):
        """Setup legal-specific patterns for entity extraction"""
        if not self.matcher:
            return

        # Money patterns
        money_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["dollars", "usd", "$"]}},],
            [{"TEXT": "$"}, {"LIKE_NUM": True}],
            [{"TEXT": "$"}, {"LIKE_NUM": True}, {"TEXT": ","}, {"LIKE_NUM": True}],
        ]
        self.matcher.add("MONEY_AMOUNT", money_patterns)

        # Percentage patterns
        percentage_patterns = [
            [{"LIKE_NUM": True}, {"TEXT": "%"}],
            [{"LIKE_NUM": True}, {"LOWER": "percent"}],
        ]
        self.matcher.add("PERCENTAGE", percentage_patterns)

        # Duration patterns
        duration_patterns = [
            [{"LIKE_NUM": True}, {"LOWER": {"IN": ["days", "months", "years", "weeks"]}},],
            [{"LIKE_NUM": True}, {"TEXT": "-"}, {"LOWER": {"IN": ["day", "month", "year", "week"]}},],
        ]
        self.matcher.add("DURATION", duration_patterns)

        # Legal obligation patterns
        obligation_patterns = [
            [{"LOWER": {"IN": ["shall", "must", "will", "agrees", "covenants"]}},
             {"IS_ALPHA": True, "OP": "*"},
             {"LOWER": {"IN": ["pay", "provide", "deliver", "maintain", "comply"]}}],
        ]
        self.matcher.add("OBLIGATION", obligation_patterns)

    async def extract_entities(self, text: str, document_id: str) -> List[LegalEntity]:
        """Extract legal entities from text"""
        entities = []

        if not self.nlp:
            logger.warning("spaCy not available, returning empty entity list")
            return entities

        # Process with spaCy
        doc = self.nlp(text)

        # Extract named entities
        for ent in doc.ents:
            entity_type = self._map_spacy_label_to_legal_type(ent.label_)
            if entity_type:
                entities.append(LegalEntity(
                    text=ent.text,
                    entity_type=entity_type,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    confidence=0.8,  # spaCy doesn't provide confidence scores
                    context=self._get_context(text, ent.start_char, ent.end_char),
                    normalized_value=self._normalize_entity_value(ent.text, entity_type),
                    metadata={"spacy_label": ent.label_}
                ))

        # Extract pattern-based entities
        matches = self.matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            label = self.nlp.vocab.strings[match_id]
            entity_type = self._map_pattern_label_to_legal_type(label)

            if entity_type:
                entities.append(LegalEntity(
                    text=span.text,
                    entity_type=entity_type,
                    start_char=span.start_char,
                    end_char=span.end_char,
                    confidence=0.9,  # Pattern matches are high confidence
                    context=self._get_context(text, span.start_char, span.end_char),
                    normalized_value=self._normalize_entity_value(span.text, entity_type),
                    metadata={"pattern_label": label}
                ))

        # Extract dates using dateparser
        date_entities = await self._extract_dates(text)
        entities.extend(date_entities)

        # Deduplicate entities (remove overlaps)
        entities = self._deduplicate_entities(entities)

        logger.info(f"Extracted {len(entities)} legal entities from document {document_id}")
        return entities

    def _map_spacy_label_to_legal_type(self, label: str) -> Optional[EntityType]:
        """Map spaCy entity labels to legal entity types"""
        mapping = {
            "PERSON": EntityType.PERSON,
            "ORG": EntityType.ORGANIZATION,
            "GPE": EntityType.JURISDICTION,  # Geopolitical entity
            "DATE": EntityType.DATE,
            "MONEY": EntityType.MONEY,
            "PERCENT": EntityType.PERCENTAGE,
        }
        return mapping.get(label)

    def _map_pattern_label_to_legal_type(self, label: str) -> Optional[EntityType]:
        """Map pattern labels to legal entity types"""
        mapping = {
            "MONEY_AMOUNT": EntityType.MONEY,
            "PERCENTAGE": EntityType.PERCENTAGE,
            "DURATION": EntityType.TERM_DURATION,
            "OBLIGATION": EntityType.OBLIGATION,
        }
        return mapping.get(label)

    def _get_context(self, text: str, start_char: int, end_char: int, context_size: int = 100) -> str:
        """Get surrounding context for an entity"""
        context_start = max(0, start_char - context_size)
        context_end = min(len(text), end_char + context_size)
        return text[context_start:context_end].strip()

    def _normalize_entity_value(self, text: str, entity_type: EntityType) -> Optional[str]:
        """Normalize entity values for consistent representation"""
        if entity_type == EntityType.MONEY:
            # Extract numeric value from money text
            numbers = re.findall(r'[\d,]+(?:\.\d+)?', text.replace('$', ''))
            if numbers:
                return numbers[0].replace(',', '')

        elif entity_type == EntityType.PERCENTAGE:
            # Extract numeric value from percentage
            numbers = re.findall(r'\d+(?:\.\d+)?', text)
            if numbers:
                return numbers[0]

        elif entity_type == EntityType.DATE:
            # Parse date to ISO format
            parsed_date = dateparser.parse(text)
            if parsed_date:
                return parsed_date.isoformat()

        return text.strip()

    async def _extract_dates(self, text: str) -> List[LegalEntity]:
        """Extract dates using dateparser"""
        entities = []

        # Common legal date patterns
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
            r'\b[A-Za-z]+ \d{1,2}, \d{4}\b',       # Month DD, YYYY
            r'\b\d{1,2} [A-Za-z]+ \d{4}\b',        # DD Month YYYY
        ]

        for pattern in date_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                date_text = match.group()
                parsed_date = dateparser.parse(date_text)

                if parsed_date:
                    entities.append(LegalEntity(
                        text=date_text,
                        entity_type=EntityType.DATE,
                        start_char=match.start(),
                        end_char=match.end(),
                        confidence=0.95,
                        context=self._get_context(text, match.start(), match.end()),
                        normalized_value=parsed_date.isoformat(),
                        metadata={"parsed_date": parsed_date}
                    ))

        return entities

    def _deduplicate_entities(self, entities: List[LegalEntity]) -> List[LegalEntity]:
        """Remove overlapping entities, keeping highest confidence"""
        entities.sort(key=lambda e: e.start_char)
        deduplicated = []

        for entity in entities:
            # Check if this entity overlaps with any already added
            overlap = False
            for existing in deduplicated:
                if (entity.start_char < existing.end_char and
                    entity.end_char > existing.start_char):
                    # Overlap detected, keep the higher confidence one
                    if entity.confidence > existing.confidence:
                        deduplicated.remove(existing)
                        deduplicated.append(entity)
                    overlap = True
                    break

            if not overlap:
                deduplicated.append(entity)

        return sorted(deduplicated, key=lambda e: e.start_char)


class ClauseIdentifier:
    """Identify and classify legal clauses using LLM and pattern matching"""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.claude_assistant = ClaudeAssistant(context_type="legal_analysis")
        self.llm_client = LLMClient(provider="claude")

    async def identify_clauses(
        self,
        parsed_doc: ParsedDocument,
        contract_type: Optional[ContractType] = None
    ) -> List[LegalClause]:
        """Identify and classify legal clauses in document"""

        # Generate semantic cache key
        doc_fingerprint = f"{parsed_doc.document_id}_{parsed_doc.overall_confidence:.2f}"
        cache_key = f"clauses:{doc_fingerprint}"

        # Check cache first
        cached_clauses = await self.cache_service.get(cache_key)
        if cached_clauses:
            logger.info(f"Retrieved clauses from cache for {parsed_doc.document_id}")
            return [LegalClause(**clause) for clause in cached_clauses]

        clauses = []

        # Split document into logical sections for clause analysis
        sections = self._split_into_sections(parsed_doc.text)

        for section_idx, section_text in enumerate(sections):
            if len(section_text.strip()) < 100:  # Skip short sections
                continue

            # Identify clause type using LLM
            clause_analysis = await self._analyze_section_with_llm(
                section_text,
                contract_type,
                section_idx
            )

            if clause_analysis and clause_analysis.get('clause_type') != 'unknown':
                # Extract additional details
                obligations, rights, conditions = await self._extract_clause_components(
                    section_text,
                    clause_analysis['clause_type']
                )

                clause = LegalClause(
                    clause_id=f"{parsed_doc.document_id}_clause_{section_idx}",
                    clause_type=ClauseType(clause_analysis['clause_type']),
                    text=section_text,
                    start_char=self._find_section_position(parsed_doc.text, section_text),
                    end_char=self._find_section_position(parsed_doc.text, section_text) + len(section_text),
                    confidence=clause_analysis.get('confidence', 0.5),
                    section_number=f"Section {section_idx + 1}",
                    obligations=obligations,
                    rights=rights,
                    conditions=conditions,
                    metadata={
                        "analysis_method": "llm_classification",
                        "section_index": section_idx,
                        "llm_reasoning": clause_analysis.get('reasoning', '')
                    }
                )

                clauses.append(clause)

        # Cache results for 2 hours
        cached_data = [clause.__dict__ for clause in clauses]
        await self.cache_service.set(cache_key, cached_data, ttl=7200)

        logger.info(f"Identified {len(clauses)} clauses in document {parsed_doc.document_id}")
        return clauses

    def _split_into_sections(self, text: str) -> List[str]:
        """Split document into logical sections for analysis"""
        # Split by common section markers
        section_patterns = [
            r'\n\s*\d+\.\s+',         # "1. Section Title"
            r'\n\s*Section \d+',       # "Section 1"
            r'\n\s*Article \d+',       # "Article 1"
            r'\n\s*[A-Z][^.!?]*:',    # "DEFINITIONS:" style headers
            r'\n\s*\([a-z]\)',        # "(a) subsection"
        ]

        # Start with paragraph splits
        paragraphs = text.split('\n\n')

        # Filter out very short paragraphs and combine related ones
        sections = []
        current_section = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Check if this looks like a section header
            is_header = any(re.match(pattern, '\n' + para) for pattern in section_patterns)

            if is_header and current_section:
                # Save previous section and start new one
                sections.append(current_section.strip())
                current_section = para
            else:
                # Add to current section
                current_section += "\n\n" + para

        # Add final section
        if current_section.strip():
            sections.append(current_section.strip())

        return sections

    async def _analyze_section_with_llm(
        self,
        section_text: str,
        contract_type: Optional[ContractType],
        section_idx: int
    ) -> Optional[Dict[str, Any]]:
        """Analyze section to identify clause type using LLM"""

        try:
            context_info = {
                "contract_type": contract_type.value if contract_type else "unknown",
                "section_index": section_idx,
                "section_length": len(section_text),
                "legal_domain": "contract_analysis"
            }

            prompt = f"""
            Analyze this legal contract section and classify the type of clause it contains.

            Section text:
            {section_text}

            Contract type: {contract_type.value if contract_type else 'unknown'}

            Classify this section into one of these clause types:
            - indemnity: Indemnification and protection clauses
            - liability: Limitation of liability clauses
            - termination: Contract termination conditions
            - confidentiality: Non-disclosure and confidentiality
            - intellectual_property: IP rights and ownership
            - payment: Payment terms and conditions
            - force_majeure: Force majeure and unforeseeable events
            - governing_law: Governing law and jurisdiction
            - dispute_resolution: Dispute resolution and arbitration
            - warranties: Warranties and representations
            - covenants: Ongoing obligations and covenants
            - definitions: Definitions and interpretations
            - amendments: Amendment and modification procedures
            - severability: Severability and enforceability
            - unknown: If none of the above apply

            Return your analysis in this exact JSON format:
            {{
                "clause_type": "one of the types above",
                "confidence": 0.0-1.0 confidence score,
                "reasoning": "brief explanation of classification",
                "key_elements": ["list", "of", "key", "elements", "found"]
            }}
            """

            response = await self.claude_assistant.analyze_with_context(
                prompt=prompt,
                context=context_info
            )

            # Parse LLM response
            response_text = response.get('content', '').strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            analysis = json.loads(response_text)

            # Validate response format
            if 'clause_type' not in analysis:
                logger.warning(f"Invalid LLM response format for section {section_idx}")
                return None

            return analysis

        except Exception as e:
            logger.error(f"LLM clause analysis failed for section {section_idx}: {e}")
            return None

    async def _extract_clause_components(
        self,
        section_text: str,
        clause_type: str
    ) -> Tuple[List[str], List[str], List[str]]:
        """Extract obligations, rights, and conditions from clause"""

        try:
            prompt = f"""
            Extract the key components from this {clause_type} clause:

            {section_text}

            Identify:
            1. Obligations (what parties must do)
            2. Rights (what parties are entitled to)
            3. Conditions (when/how obligations/rights apply)

            Return in JSON format:
            {{
                "obligations": ["list of obligations"],
                "rights": ["list of rights"],
                "conditions": ["list of conditions"]
            }}
            """

            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are a legal expert analyzing contract clauses.",
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000
            )

            response_text = response.get('content', '').strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            components = json.loads(response_text)

            return (
                components.get('obligations', []),
                components.get('rights', []),
                components.get('conditions', [])
            )

        except Exception as e:
            logger.error(f"Failed to extract clause components: {e}")
            return [], [], []

    def _find_section_position(self, full_text: str, section_text: str) -> int:
        """Find the character position of a section in the full text"""
        # Clean up both texts for matching
        clean_section = ' '.join(section_text.split())
        clean_full = ' '.join(full_text.split())

        position = clean_full.find(clean_section)
        return max(0, position)


class ContractAnalyzer:
    """High-level contract analysis orchestrator"""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.claude_assistant = ClaudeAssistant(context_type="contract_analysis")
        self.llm_client = LLMClient(provider="claude")
        self.entity_extractor = LegalEntityExtractor()
        self.clause_identifier = ClauseIdentifier(cache_service)

    async def analyze_contract(self, parsed_doc: ParsedDocument) -> ContractAnalysis:
        """Perform comprehensive analysis of a legal contract"""

        logger.info(f"Starting contract analysis for {parsed_doc.document_id}")

        # Step 1: Determine contract type
        contract_type, type_confidence = await self._determine_contract_type(parsed_doc)

        # Step 2: Extract entities
        entities = await self.entity_extractor.extract_entities(
            parsed_doc.text,
            parsed_doc.document_id
        )

        # Step 3: Identify clauses
        clauses = await self.clause_identifier.identify_clauses(parsed_doc, contract_type)

        # Step 4: Extract contract-specific information
        parties = self._extract_parties(entities)
        key_terms = await self._extract_key_terms(parsed_doc.text, contract_type)
        jurisdiction = self._extract_jurisdiction(entities)
        governing_law = await self._extract_governing_law(parsed_doc.text)
        dates = self._extract_contract_dates(entities)

        # Step 5: Identify missing clauses and compliance requirements
        missing_clauses = await self._identify_missing_clauses(clauses, contract_type)
        compliance_requirements = await self._identify_compliance_requirements(
            parsed_doc.text,
            contract_type,
            jurisdiction
        )

        # Step 6: Extract critical obligations and rights
        critical_obligations = self._extract_critical_obligations(clauses)
        critical_rights = self._extract_critical_rights(clauses)

        analysis = ContractAnalysis(
            document_id=parsed_doc.document_id,
            contract_type=contract_type,
            contract_type_confidence=type_confidence,
            parties=parties,
            entities=entities,
            clauses=clauses,
            key_terms=key_terms,
            jurisdiction=jurisdiction,
            governing_law=governing_law,
            effective_date=dates.get('effective_date'),
            expiration_date=dates.get('expiration_date'),
            term_duration=dates.get('term_duration'),
            auto_renewal=await self._detect_auto_renewal(parsed_doc.text),
            critical_obligations=critical_obligations,
            critical_rights=critical_rights,
            missing_clauses=missing_clauses,
            compliance_requirements=compliance_requirements,
            analysis_metadata={
                "total_entities": len(entities),
                "total_clauses": len(clauses),
                "analysis_duration_ms": 0,  # Will be calculated
                "confidence_scores": {
                    "overall": parsed_doc.overall_confidence,
                    "contract_type": type_confidence,
                    "entity_extraction": sum(e.confidence for e in entities) / len(entities) if entities else 0,
                    "clause_identification": sum(c.confidence for c in clauses) / len(clauses) if clauses else 0
                }
            }
        )

        logger.info(
            f"Contract analysis completed for {parsed_doc.document_id}: "
            f"{contract_type.value} with {len(clauses)} clauses, {len(entities)} entities"
        )

        return analysis

    async def _determine_contract_type(self, parsed_doc: ParsedDocument) -> Tuple[ContractType, float]:
        """Determine the type of contract using LLM analysis"""

        try:
            # Use first 2000 characters for type determination (usually sufficient)
            sample_text = parsed_doc.text[:2000]

            prompt = f"""
            Analyze this contract excerpt and determine the contract type.

            Text:
            {sample_text}

            Classify as one of these types:
            - nda: Non-disclosure agreement
            - msa: Master service agreement
            - employment: Employment contract
            - lease: Lease agreement
            - purchase: Purchase/sales agreement
            - service: Service contract
            - license: License agreement
            - partnership: Partnership agreement
            - loan: Loan agreement
            - insurance: Insurance policy
            - unknown: If unclear or other type

            Return JSON format:
            {{
                "contract_type": "type from list above",
                "confidence": 0.0-1.0,
                "reasoning": "brief explanation"
            }}
            """

            response = await self.claude_assistant.analyze_with_context(
                prompt=prompt,
                context={
                    "document_id": parsed_doc.document_id,
                    "task_type": "contract_classification",
                    "text_length": len(sample_text)
                }
            )

            response_text = response.get('content', '').strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]

            result = json.loads(response_text)

            contract_type = ContractType(result.get('contract_type', 'unknown'))
            confidence = float(result.get('confidence', 0.5))

            return contract_type, confidence

        except Exception as e:
            logger.error(f"Contract type determination failed: {e}")
            return ContractType.UNKNOWN, 0.0

    def _extract_parties(self, entities: List[LegalEntity]) -> List[LegalEntity]:
        """Extract contracting parties from entities"""
        parties = []

        for entity in entities:
            if entity.entity_type in [EntityType.PERSON, EntityType.ORGANIZATION]:
                # Check if this looks like a contracting party (not just any person/org mentioned)
                context_lower = entity.context.lower()
                party_indicators = [
                    'party', 'parties', 'between', 'agreement', 'contract',
                    'hereinafter', 'company', 'corporation', 'llc', 'inc'
                ]

                if any(indicator in context_lower for indicator in party_indicators):
                    parties.append(entity)

        return parties

    async def _extract_key_terms(
        self,
        text: str,
        contract_type: ContractType
    ) -> List[LegalTerm]:
        """Extract key legal terms and their definitions"""

        try:
            # Focus on definitions section if present
            definitions_section = self._extract_definitions_section(text)

            if definitions_section:
                # Use LLM to extract structured definitions
                prompt = f"""
                Extract key term definitions from this definitions section:

                {definitions_section}

                Return JSON array of terms:
                [{{
                    "term": "term name",
                    "definition": "definition text",
                    "importance_score": 0.0-1.0
                }}]
                """

                response = await self.llm_client.agenerate(
                    prompt=prompt,
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2000
                )

                response_text = response.get('content', '').strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]

                terms_data = json.loads(response_text)

                key_terms = []
                for term_data in terms_data:
                    key_terms.append(LegalTerm(
                        term=term_data['term'],
                        definition=term_data['definition'],
                        context=definitions_section[:200],  # First 200 chars as context
                        importance_score=term_data.get('importance_score', 0.5),
                        page_references=[1]  # Would calculate actual page refs in production
                    ))

                return key_terms

        except Exception as e:
            logger.error(f"Key terms extraction failed: {e}")

        return []

    def _extract_definitions_section(self, text: str) -> Optional[str]:
        """Extract the definitions section from contract text"""
        # Look for definitions section patterns
        patterns = [
            r'(?i)definitions?\s*\.?\s*\n(.*?)(?=\n\s*\d+\.|\n\s*[A-Z][^.]*:|\Z)',
            r'(?i)as used in this agreement[^:]*:\s*\n(.*?)(?=\n\s*\d+\.|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _extract_jurisdiction(self, entities: List[LegalEntity]) -> Optional[str]:
        """Extract jurisdiction from entities"""
        for entity in entities:
            if entity.entity_type == EntityType.JURISDICTION:
                context_lower = entity.context.lower()
                if any(indicator in context_lower for indicator in
                       ['jurisdiction', 'governing law', 'courts of', 'laws of']):
                    return entity.text

        return None

    async def _extract_governing_law(self, text: str) -> Optional[str]:
        """Extract governing law using pattern matching and LLM"""
        # Pattern-based extraction first
        patterns = [
            r'(?i)governed by the laws of ([^,.\n]+)',
            r'(?i)governing law.*?:\s*([^,.\n]+)',
            r'(?i)laws of (\w+(?:\s+\w+)*) shall govern'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        # TODO: Use LLM for more complex extraction if patterns fail

        return None

    def _extract_contract_dates(self, entities: List[LegalEntity]) -> Dict[str, Any]:
        """Extract key contract dates"""
        dates = {
            'effective_date': None,
            'expiration_date': None,
            'term_duration': None
        }

        date_entities = [e for e in entities if e.entity_type == EntityType.DATE]
        duration_entities = [e for e in entities if e.entity_type == EntityType.TERM_DURATION]

        # Find effective date (usually first significant date)
        for entity in date_entities:
            context_lower = entity.context.lower()
            if any(indicator in context_lower for indicator in
                   ['effective', 'commencing', 'beginning', 'starts']):
                if entity.normalized_value:
                    try:
                        dates['effective_date'] = datetime.fromisoformat(entity.normalized_value.replace('Z', '+00:00'))
                    except:
                        pass
                break

        # Find expiration/termination date
        for entity in date_entities:
            context_lower = entity.context.lower()
            if any(indicator in context_lower for indicator in
                   ['expires', 'expiration', 'terminates', 'ends']):
                if entity.normalized_value:
                    try:
                        dates['expiration_date'] = datetime.fromisoformat(entity.normalized_value.replace('Z', '+00:00'))
                    except:
                        pass
                break

        # Extract term duration
        if duration_entities:
            dates['term_duration'] = duration_entities[0].text

        return dates

    async def _identify_missing_clauses(
        self,
        clauses: List[LegalClause],
        contract_type: ContractType
    ) -> List[ClauseType]:
        """Identify clauses that should be present but are missing"""

        # Define expected clauses by contract type
        expected_clauses = {
            ContractType.NDA: [
                ClauseType.CONFIDENTIALITY,
                ClauseType.TERMINATION,
                ClauseType.GOVERNING_LAW,
                ClauseType.SEVERABILITY
            ],
            ContractType.MSA: [
                ClauseType.PAYMENT,
                ClauseType.TERMINATION,
                ClauseType.LIABILITY,
                ClauseType.INDEMNITY,
                ClauseType.GOVERNING_LAW,
                ClauseType.DISPUTE_RESOLUTION
            ],
            ContractType.EMPLOYMENT: [
                ClauseType.TERMINATION,
                ClauseType.CONFIDENTIALITY,
                ClauseType.INTELLECTUAL_PROPERTY,
                ClauseType.COVENANTS
            ]
        }

        expected = expected_clauses.get(contract_type, [])
        present_types = {clause.clause_type for clause in clauses}
        missing = [clause_type for clause_type in expected if clause_type not in present_types]

        return missing

    async def _identify_compliance_requirements(
        self,
        text: str,
        contract_type: ContractType,
        jurisdiction: Optional[str]
    ) -> List[str]:
        """Identify regulatory compliance requirements"""
        # This would be expanded with actual regulatory databases
        # For now, return basic compliance areas based on contract type

        compliance_map = {
            ContractType.EMPLOYMENT: ["FLSA compliance", "State labor law compliance"],
            ContractType.NDA: ["Trade secrets protection", "Data privacy compliance"],
            ContractType.MSA: ["Commercial law compliance", "Tax law compliance"]
        }

        return compliance_map.get(contract_type, [])

    def _extract_critical_obligations(self, clauses: List[LegalClause]) -> List[str]:
        """Extract the most critical obligations from all clauses"""
        critical = []

        for clause in clauses:
            if clause.clause_type in [ClauseType.PAYMENT, ClauseType.COVENANTS]:
                critical.extend(clause.obligations)

        return critical[:10]  # Return top 10

    def _extract_critical_rights(self, clauses: List[LegalClause]) -> List[str]:
        """Extract the most critical rights from all clauses"""
        critical = []

        for clause in clauses:
            if clause.clause_type in [ClauseType.INTELLECTUAL_PROPERTY, ClauseType.WARRANTIES]:
                critical.extend(clause.rights)

        return critical[:10]  # Return top 10

    async def _detect_auto_renewal(self, text: str) -> bool:
        """Detect if contract has auto-renewal provisions"""
        auto_renewal_patterns = [
            r'(?i)automatically renew',
            r'(?i)auto.*renew',
            r'(?i)renew.*automatically',
            r'(?i)successive.*terms',
            r'(?i)evergreen'
        ]

        for pattern in auto_renewal_patterns:
            if re.search(pattern, text):
                return True

        return False


class LegalAnalyzer:
    """
    Main orchestrator for legal document analysis
    Coordinates all components for comprehensive legal intelligence
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.contract_analyzer = ContractAnalyzer(cache_service)
        self.entity_extractor = LegalEntityExtractor()
        self.clause_identifier = ClauseIdentifier(cache_service)

    async def analyze_document(self, parsed_doc: ParsedDocument) -> ContractAnalysis:
        """Perform comprehensive legal analysis of a document"""

        # Generate cache key based on document content
        analysis_key = f"legal_analysis:{parsed_doc.document_id}_{parsed_doc.overall_confidence:.2f}"

        # Check cache first
        cached_analysis = await self.cache_service.get(analysis_key)
        if cached_analysis:
            logger.info(f"Retrieved legal analysis from cache for {parsed_doc.document_id}")
            return ContractAnalysis(**cached_analysis)

        # Perform full analysis
        start_time = datetime.utcnow()

        analysis = await self.contract_analyzer.analyze_contract(parsed_doc)

        # Calculate analysis duration
        duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        analysis.analysis_metadata['analysis_duration_ms'] = duration_ms

        # Cache results for 4 hours (legal analysis is expensive)
        await self.cache_service.set(analysis_key, analysis.__dict__, ttl=14400)

        logger.info(
            f"Legal analysis completed for {parsed_doc.document_id} in {duration_ms}ms: "
            f"{analysis.contract_type.value} contract with {len(analysis.clauses)} clauses"
        )

        return analysis

    async def analyze_batch(
        self,
        parsed_docs: List[ParsedDocument],
        max_concurrent: int = 3
    ) -> List[ContractAnalysis]:
        """Analyze multiple documents concurrently"""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_single(doc):
            async with semaphore:
                return await self.analyze_document(doc)

        tasks = [analyze_single(doc) for doc in parsed_docs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and log errors
        analyses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to analyze {parsed_docs[i].document_id}: {result}")
            else:
                analyses.append(result)

        logger.info(
            f"Batch legal analysis completed: {len(analyses)}/{len(parsed_docs)} successful"
        )

        return analyses