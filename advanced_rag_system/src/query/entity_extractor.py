"""Entity Extraction and Linking with Knowledge Graph integration preparation.

This module provides advanced entity recognition capabilities including:
- Named entity extraction (general and real estate domain)
- Entity disambiguation and resolution
- Knowledge graph integration preparation
- Entity linking to canonical identifiers
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
import hashlib
import json

from src.core.exceptions import RetrievalError


class EntityType(Enum):
    """Types of entities that can be extracted."""

    # General entities
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PERCENT = "percent"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"

    # Real estate domain entities
    PROPERTY = "property"
    PROPERTY_TYPE = "property_type"  # house, condo, townhouse, etc.
    PRICE = "price"
    PRICE_RANGE = "price_range"
    BEDROOMS = "bedrooms"
    BATHROOMS = "bathrooms"
    SQUARE_FEET = "square_feet"
    LOT_SIZE = "lot_size"
    YEAR_BUILT = "year_built"
    MLS_NUMBER = "mls_number"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    ZIP_CODE = "zip_code"
    NEIGHBORHOOD = "neighborhood"
    SCHOOL_DISTRICT = "school_district"
    SCHOOL = "school"
    AMENITY = "amenity"
    FEATURE = "feature"  # pool, garage, fireplace, etc.
    VIEW = "view"  # mountain view, city view, etc.
    AGENT = "agent"
    BROKERAGE = "brokerage"


@dataclass
class Entity:
    """Represents an extracted entity.

    Attributes:
        text: Original text of the entity
        type: Entity type
        start: Start position in the query
        end: End position in the query
        confidence: Extraction confidence (0.0-1.0)
        normalized_value: Normalized/canonical value
        metadata: Additional entity metadata
    """

    text: str
    type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    normalized_value: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set normalized value if not provided."""
        if self.normalized_value is None:
            self.normalized_value = self.text.lower().strip()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "text": self.text,
            "type": self.type.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "normalized_value": self.normalized_value,
            "metadata": self.metadata,
        }

    @property
    def span(self) -> Tuple[int, int]:
        """Get entity span as (start, end) tuple."""
        return (self.start, self.end)


@dataclass
class EntityLinkingResult:
    """Result of entity linking to a knowledge base.

    Attributes:
        entity: The extracted entity
        canonical_id: Canonical identifier in knowledge base
        canonical_name: Canonical name
        score: Linking confidence score
        candidates: Alternative linking candidates
        source: Source of the link (e.g., 'kb', 'fuzzy', 'exact')
    """

    entity: Entity
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    score: float = 0.0
    candidates: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Convert linking result to dictionary."""
        return {
            "entity": self.entity.to_dict(),
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "score": self.score,
            "candidates": self.candidates,
            "source": self.source,
        }


@dataclass
class KnowledgeGraphPrep:
    """Prepared entity data for Knowledge Graph integration.

    Attributes:
        entities: List of extracted entities
        relationships: Detected relationships between entities
        kg_nodes: Proposed KG node representations
        kg_edges: Proposed KG edge representations
        entity_clusters: Clustered/disambiguated entities
    """

    entities: List[Entity]
    relationships: List[Dict[str, Any]] = field(default_factory=list)
    kg_nodes: List[Dict[str, Any]] = field(default_factory=list)
    kg_edges: List[Dict[str, Any]] = field(default_factory=list)
    entity_clusters: Dict[str, List[Entity]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert KG prep to dictionary."""
        return {
            "entities": [e.to_dict() for e in self.entities],
            "relationships": self.relationships,
            "kg_nodes": self.kg_nodes,
            "kg_edges": self.kg_edges,
            "entity_clusters": {
                k: [e.to_dict() for e in v] for k, v in self.entity_clusters.items()
            },
        }


@dataclass
class ExtractionConfig:
    """Configuration for entity extraction.

    Attributes:
        confidence_threshold: Minimum confidence for extraction
        enable_coreference: Whether to resolve coreferences
        enable_disambiguation: Whether to perform disambiguation
        domain: Domain context ('general', 'real_estate')
        custom_patterns: Additional regex patterns
        link_to_kb: Whether to attempt KB linking
    """

    confidence_threshold: float = 0.6
    enable_coreference: bool = True
    enable_disambiguation: bool = True
    domain: str = "real_estate"
    custom_patterns: Optional[Dict[str, List[str]]] = None
    link_to_kb: bool = False


class EntityExtractor:
    """Extract and process entities from queries.

    Provides named entity recognition for both general and domain-specific
    entities, with support for disambiguation and knowledge graph preparation.

    Example:
        ```python
        extractor = EntityExtractor(domain="real_estate")

        # Extract entities
        entities = extractor.extract(
            "Show me 3-bedroom houses in Rancho Cucamonga under $800k"
        )

        for entity in entities:
            print(f"{entity.text} -> {entity.type.value}")
        # "3-bedroom" -> bedrooms
        # "Rancho Cucamonga" -> city
        # "$800k" -> price
        ```
    """

    def __init__(self, config: Optional[ExtractionConfig] = None):
        """Initialize entity extractor.

        Args:
            config: Extraction configuration
        """
        self.config = config or ExtractionConfig()
        self._patterns = self._build_patterns()
        self._domain_terms = self._build_domain_terms()
        self._disambiguation_rules = self._build_disambiguation_rules()

    def _build_patterns(self) -> Dict[EntityType, List[re.Pattern]]:
        """Build regex patterns for entity extraction."""
        patterns = {
            # General patterns
            EntityType.EMAIL: [
                re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
            ],
            EntityType.PHONE: [
                re.compile(r"\b(\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b"),
            ],
            EntityType.URL: [
                re.compile(r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?"),
            ],
            EntityType.MONEY: [
                re.compile(r"\$[\d,]+(?:\.\d{2})?(?:\s*[KkMmBb])?\b"),
                re.compile(r"\b\d+\s*(thousand|million|billion)\s+dollars?\b", re.I),
            ],
            EntityType.PERCENT: [
                re.compile(r"\b\d+(?:\.\d+)?%\b"),
                re.compile(r"\b\d+(?:\.\d+)?\s+percent\b", re.I),
            ],
            EntityType.DATE: [
                re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),
                re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s+\d{4})?\b", re.I),
            ],

            # Real estate patterns
            EntityType.BEDROOMS: [
                re.compile(r"\b(\d+)\s*(?:bed|bedroom|br)s?\b", re.I),
                re.compile(r"\b(\d+)-bed\b", re.I),
            ],
            EntityType.BATHROOMS: [
                re.compile(r"\b(\d+(?:\.5)?)\s*(?:bath|bathroom|ba)s?\b", re.I),
                re.compile(r"\b(\d+(?:\.5)?)-bath\b", re.I),
            ],
            EntityType.SQUARE_FEET: [
                re.compile(r"\b(\d{3,4})\s*(?:sq\.?\s*ft\.?|sqft|sf)\b", re.I),
                re.compile(r"\b(\d{3,4})\s*square\s+feet\b", re.I),
            ],
            EntityType.MLS_NUMBER: [
                re.compile(r"\b(MLS|#)\s*#?\s*(\d{6,10})\b", re.I),
                re.compile(r"\bMLS#?\s*(\d{6,10})\b", re.I),
            ],
            EntityType.ZIP_CODE: [
                re.compile(r"\b(\d{5})(?:-\d{4})?\b"),
            ],
            EntityType.YEAR_BUILT: [
                re.compile(r"\bbuilt\s+(?:in\s+)?(19\d{2}|20\d{2})\b", re.I),
                re.compile(r"\b(19\d{2}|20\d{2})\s+(?:construction|build)\b", re.I),
            ],
        }

        # Add custom patterns if provided
        if self.config.custom_patterns:
            for type_name, pattern_strings in self.config.custom_patterns.items():
                try:
                    entity_type = EntityType(type_name)
                    custom_patterns = [re.compile(p, re.I) for p in pattern_strings]
                    if entity_type in patterns:
                        patterns[entity_type].extend(custom_patterns)
                    else:
                        patterns[entity_type] = custom_patterns
                except (ValueError, re.error):
                    continue

        return patterns

    def _build_domain_terms(self) -> Dict[EntityType, Set[str]]:
        """Build domain-specific term sets."""
        return {
            # Property types
            EntityType.PROPERTY_TYPE: {
                "house", "home", "condo", "condominium", "townhouse", "townhome",
                "apartment", "duplex", "triplex", "single family", "multi-family",
                "detached", "attached", "mobile home", "manufactured", "land",
                "lot", "commercial", "industrial"
            },

            # Cities in Rancho Cucamonga area
            EntityType.CITY: {
                "rancho cucamonga", "ontario", "fontana", "upland", "claremont",
                "montclair", "chino", "chino hills", "eastvale", "jurupa valley",
                "riverside", "san bernardino", "corona", "norco", "pomona",
                "la verne", "san dimas", "glendora", "azusa", "covina"
            },

            # Neighborhoods in Rancho Cucamonga
            EntityType.NEIGHBORHOOD: {
                "victoria", "victoria gardens", "haven", "etiwanda", "terra vista",
                "central park", "coyote canyon", "summit", "north rancho",
                "south rancho", "west wind", "carnelian", "sapphire", "amethyst"
            },

            # School districts
            EntityType.SCHOOL_DISTRICT: {
                "etiwanda", "chaffey", "alta loma", "central", " Cucamonga"
            },

            # Amenities
            EntityType.AMENITY: {
                "pool", "swimming pool", "garage", "two-car garage", "three-car garage",
                "fireplace", "patio", "deck", "balcony", "yard", "backyard",
                "garden", "gated", "community pool", "tennis court", "gym",
                "fitness center", "clubhouse", "playground", "park"
            },

            # Features
            EntityType.FEATURE: {
                "hardwood floors", "granite countertops", "stainless steel appliances",
                "central air", "air conditioning", "heating", "fireplace",
                "walk-in closet", "master suite", "guest house", "rv parking",
                "solar panels", "energy efficient", "smart home", "updated",
                "renovated", "new construction"
            },

            # Views
            EntityType.VIEW: {
                "mountain view", "city view", "valley view", "golf course view",
                "lake view", "ocean view", "canyon view", "panoramic view"
            },
        }

    def _build_disambiguation_rules(self) -> Dict[EntityType, List[Dict[str, Any]]]:
        """Build rules for entity disambiguation."""
        return {
            EntityType.LOCATION: [
                {
                    "context": ["in", "near", "around", "close to"],
                    "boost": 0.2,
                }
            ],
            EntityType.PRICE: [
                {
                    "context": ["under", "over", "between", "around", "about"],
                    "boost": 0.15,
                }
            ],
            EntityType.BEDROOMS: [
                {
                    "context": ["bedroom", "bed", "br"],
                    "boost": 0.3,
                }
            ],
        }

    def extract(self, query: str) -> List[Entity]:
        """Extract entities from a query.

        Args:
            query: Input query string

        Returns:
            List of extracted entities
        """
        if not query or not query.strip():
            return []

        entities = []

        # Pattern-based extraction
        entities.extend(self._extract_with_patterns(query))

        # Dictionary-based extraction
        entities.extend(self._extract_with_dictionary(query))

        # Remove overlapping entities
        entities = self._resolve_overlaps(entities)

        # Apply confidence threshold
        entities = [e for e in entities if e.confidence >= self.config.confidence_threshold]

        # Sort by position
        entities.sort(key=lambda e: e.start)

        return entities

    def _extract_with_patterns(self, query: str) -> List[Entity]:
        """Extract entities using regex patterns."""
        entities = []

        for entity_type, patterns in self._patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(query):
                    entity = Entity(
                        text=match.group(),
                        type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.85,
                        normalized_value=self._normalize_entity(match.group(), entity_type),
                    )
                    entities.append(entity)

        return entities

    def _extract_with_dictionary(self, query: str) -> List[Entity]:
        """Extract entities using dictionary matching."""
        entities = []
        query_lower = query.lower()

        for entity_type, terms in self._domain_terms.items():
            for term in terms:
                # Find all occurrences
                start = 0
                while True:
                    idx = query_lower.find(term, start)
                    if idx == -1:
                        break

                    # Check for word boundaries
                    before = idx == 0 or not query_lower[idx - 1].isalnum()
                    after = idx + len(term) >= len(query_lower) or not query_lower[idx + len(term)].isalnum()

                    if before and after:
                        entity = Entity(
                            text=query[idx:idx + len(term)],
                            type=entity_type,
                            start=idx,
                            end=idx + len(term),
                            confidence=0.80,
                            normalized_value=term,
                        )
                        entities.append(entity)

                    start = idx + 1

        return entities

    def _normalize_entity(self, text: str, entity_type: EntityType) -> str:
        """Normalize an entity value.

        Args:
            text: Entity text
            entity_type: Type of entity

        Returns:
            Normalized value
        """
        text = text.strip().lower()

        if entity_type == EntityType.MONEY:
            # Normalize money: $800k -> 800000
            text = text.replace("$", "").replace(",", "")
            if text.endswith("k"):
                return str(int(float(text[:-1]) * 1000))
            elif text.endswith("m"):
                return str(int(float(text[:-1]) * 1000000))
            return text

        elif entity_type == EntityType.BEDROOMS:
            # Extract number
            match = re.search(r"(\d+)", text)
            return match.group(1) if match else text

        elif entity_type == EntityType.BATHROOMS:
            # Extract number (including .5)
            match = re.search(r"(\d+(?:\.5)?)", text)
            return match.group(1) if match else text

        elif entity_type == EntityType.SQUARE_FEET:
            # Extract number
            match = re.search(r"(\d+)", text)
            return match.group(1) if match else text

        return text

    def _resolve_overlaps(self, entities: List[Entity]) -> List[Entity]:
        """Resolve overlapping entity spans.

        Args:
            entities: List of entities

        Returns:
            List with overlaps resolved
        """
        if not entities:
            return entities

        # Sort by length (longer first), then by confidence
        sorted_entities = sorted(entities, key=lambda e: (-(e.end - e.start), -e.confidence))

        resolved = []
        covered_spans = []

        for entity in sorted_entities:
            # Check for overlap
            overlaps = False
            for span in covered_spans:
                if not (entity.end <= span[0] or entity.start >= span[1]):
                    overlaps = True
                    break

            if not overlaps:
                resolved.append(entity)
                covered_spans.append((entity.start, entity.end))

        # Sort back by position
        resolved.sort(key=lambda e: e.start)

        return resolved

    def disambiguate(self, entities: List[Entity], query: str) -> List[Entity]:
        """Perform entity disambiguation.

        Args:
            entities: List of entities to disambiguate
            query: Original query for context

        Returns:
            Disambiguated entities
        """
        if not self.config.enable_disambiguation:
            return entities

        disambiguated = []

        for entity in entities:
            # Apply context-based disambiguation rules
            if entity.type in self._disambiguation_rules:
                for rule in self._disambiguation_rules[entity.type]:
                    for context_word in rule["context"]:
                        # Check if context word appears near entity
                        context_start = max(0, entity.start - 50)
                        context_end = min(len(query), entity.end + 50)
                        context = query[context_start:context_end].lower()

                        if context_word in context:
                            entity.confidence = min(1.0, entity.confidence + rule["boost"])
                            entity.metadata["disambiguation_context"] = context_word
                            break

            # Handle specific disambiguation cases
            if entity.type == EntityType.LOCATION:
                # Check if it's actually a neighborhood or city
                if entity.normalized_value in self._domain_terms.get(EntityType.NEIGHBORHOOD, set()):
                    entity.type = EntityType.NEIGHBORHOOD
                    entity.metadata["disambiguated_from"] = "location"
                elif entity.normalized_value in self._domain_terms.get(EntityType.CITY, set()):
                    entity.type = EntityType.CITY
                    entity.metadata["disambiguated_from"] = "location"

            disambiguated.append(entity)

        return disambiguated

    def link_to_kb(
        self, entities: List[Entity], kb_lookup: Optional[callable] = None
    ) -> List[EntityLinkingResult]:
        """Link entities to knowledge base entries.

        Args:
            entities: List of entities to link
            kb_lookup: Optional function to look up entities in KB

        Returns:
            List of linking results
        """
        results = []

        for entity in entities:
            result = EntityLinkingResult(entity=entity)

            # Generate entity signature for linking
            signature = self._generate_entity_signature(entity)

            if kb_lookup:
                # Use provided KB lookup function
                kb_result = kb_lookup(entity)
                if kb_result:
                    result.canonical_id = kb_result.get("id")
                    result.canonical_name = kb_result.get("name")
                    result.score = kb_result.get("score", 0.0)
                    result.source = "kb"
            else:
                # Use mock linking for demonstration
                result = self._mock_kb_linking(entity, signature)

            results.append(result)

        return results

    def _generate_entity_signature(self, entity: Entity) -> str:
        """Generate a unique signature for entity linking.

        Args:
            entity: Entity to generate signature for

        Returns:
            Signature string
        """
        content = f"{entity.type.value}:{entity.normalized_value}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _mock_kb_linking(self, entity: Entity, signature: str) -> EntityLinkingResult:
        """Perform mock KB linking for demonstration.

        Args:
            entity: Entity to link
            signature: Entity signature

        Returns:
            Linking result
        """
        result = EntityLinkingResult(entity=entity)

        # Mock linking for specific entity types
        if entity.type == EntityType.CITY:
            if "rancho cucamonga" in entity.normalized_value:
                result.canonical_id = "city:ca:rancho_cucamonga"
                result.canonical_name = "Rancho Cucamonga, CA"
                result.score = 0.98
                result.source = "exact"

        elif entity.type == EntityType.NEIGHBORHOOD:
            neighborhood_map = {
                "victoria": "neighborhood:ca:rancho_cucamonga:victoria",
                "victoria gardens": "neighborhood:ca:rancho_cucamonga:victoria_gardens",
                "haven": "neighborhood:ca:rancho_cucamonga:haven",
                "etiwanda": "neighborhood:ca:rancho_cucamonga:etiwanda",
                "terra vista": "neighborhood:ca:rancho_cucamonga:terra_vista",
            }
            if entity.normalized_value in neighborhood_map:
                result.canonical_id = neighborhood_map[entity.normalized_value]
                result.canonical_name = entity.text.title()
                result.score = 0.95
                result.source = "exact"

        elif entity.type == EntityType.SCHOOL_DISTRICT:
            if "etiwanda" in entity.normalized_value:
                result.canonical_id = "school_district:ca:etiwanda"
                result.canonical_name = "Etiwanda School District"
                result.score = 0.97
                result.source = "exact"

        # If no match, provide fuzzy candidates
        if not result.canonical_id:
            result.candidates = [
                {
                    "id": f"candidate:{signature}",
                    "name": entity.normalized_value.title(),
                    "score": 0.6,
                }
            ]
            result.source = "fuzzy"

        return result

    def prepare_for_knowledge_graph(
        self, entities: List[Entity], query: str
    ) -> KnowledgeGraphPrep:
        """Prepare entities for Knowledge Graph integration.

        Args:
            entities: List of extracted entities
            query: Original query

        Returns:
            KG preparation data
        """
        kg_prep = KnowledgeGraphPrep(entities=entities)

        # Create KG nodes
        for entity in entities:
            node = {
                "id": self._generate_entity_signature(entity),
                "type": entity.type.value,
                "label": entity.text,
                "properties": {
                    "normalized_value": entity.normalized_value,
                    "confidence": entity.confidence,
                },
            }
            kg_prep.kg_nodes.append(node)

        # Detect relationships
        kg_prep.relationships = self._detect_relationships(entities, query)

        # Create KG edges from relationships
        for rel in kg_prep.relationships:
            edge = {
                "source": rel["source"],
                "target": rel["target"],
                "type": rel["type"],
                "properties": rel.get("properties", {}),
            }
            kg_prep.kg_edges.append(edge)

        # Cluster entities by type for disambiguation
        kg_prep.entity_clusters = self._cluster_entities(entities)

        return kg_prep

    def _detect_relationships(
        self, entities: List[Entity], query: str
    ) -> List[Dict[str, Any]]:
        """Detect relationships between entities.

        Args:
            entities: List of entities
            query: Original query

        Returns:
            List of detected relationships
        """
        relationships = []

        # Sort entities by position
        sorted_entities = sorted(entities, key=lambda e: e.start)

        # Look for proximity-based relationships
        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i + 1 :]:
                # Check if entities are close to each other
                distance = entity2.start - entity1.end

                if distance <= 50:  # Within 50 characters
                    rel_type = self._infer_relationship_type(entity1, entity2, query)

                    if rel_type:
                        relationships.append({
                            "source": self._generate_entity_signature(entity1),
                            "target": self._generate_entity_signature(entity2),
                            "type": rel_type,
                            "properties": {
                                "distance": distance,
                                "confidence": min(entity1.confidence, entity2.confidence),
                            },
                        })

        return relationships

    def _infer_relationship_type(
        self, entity1: Entity, entity2: Entity, query: str
    ) -> Optional[str]:
        """Infer relationship type between two entities.

        Args:
            entity1: First entity
            entity2: Second entity
            query: Original query

        Returns:
            Relationship type or None
        """
        # Get text between entities
        between_text = query[entity1.end:entity2.start].lower()

        # Location relationships
        if entity1.type == EntityType.PROPERTY and entity2.type in [
            EntityType.CITY,
            EntityType.NEIGHBORHOOD,
            EntityType.LOCATION,
        ]:
            return "LOCATED_IN"

        if entity1.type == EntityType.NEIGHBORHOOD and entity2.type == EntityType.CITY:
            return "PART_OF"

        # Price relationships
        if entity2.type == EntityType.PRICE and entity1.type == EntityType.PROPERTY_TYPE:
            if any(w in between_text for w in ["under", "below", "less than"]):
                return "PRICE_LESS_THAN"
            if any(w in between_text for w in ["over", "above", "more than"]):
                return "PRICE_GREATER_THAN"
            return "HAS_PRICE"

        # Feature relationships
        if entity1.type == EntityType.PROPERTY and entity2.type in [
            EntityType.BEDROOMS,
            EntityType.BATHROOMS,
            EntityType.SQUARE_FEET,
        ]:
            return "HAS_FEATURE"

        if entity1.type == EntityType.PROPERTY and entity2.type == EntityType.FEATURE:
            return "HAS_AMENITY"

        # School relationships
        if entity1.type == EntityType.PROPERTY and entity2.type == EntityType.SCHOOL_DISTRICT:
            return "IN_SCHOOL_DISTRICT"

        return "RELATED_TO"

    def _cluster_entities(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Cluster entities by type for disambiguation.

        Args:
            entities: List of entities

        Returns:
            Entity clusters
        """
        clusters = defaultdict(list)

        for entity in entities:
            cluster_key = entity.type.value
            clusters[cluster_key].append(entity)

        return dict(clusters)

    def get_stats(self) -> Dict[str, Any]:
        """Get extractor statistics.

        Returns:
            Dictionary with extractor statistics
        """
        return {
            "config": {
                "confidence_threshold": self.config.confidence_threshold,
                "enable_coreference": self.config.enable_coreference,
                "enable_disambiguation": self.config.enable_disambiguation,
                "domain": self.config.domain,
                "link_to_kb": self.config.link_to_kb,
            },
            "patterns": {k.value: len(v) for k, v in self._patterns.items()},
            "domain_terms": {k.value: len(v) for k, v in self._domain_terms.items()},
            "disambiguation_rules": len(self._disambiguation_rules),
        }
