"""Advanced Query Parser - Orchestration layer for query understanding.

This module provides the main interface for advanced query processing,
orchestrating intent classification, temporal processing, and entity extraction
into a unified query understanding pipeline.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.core.exceptions import RetrievalError
from src.query.entity_extractor import (
    Entity,
    EntityExtractor,
    EntityType,
    ExtractionConfig,
    KnowledgeGraphPrep,
)
from src.query.intent_classifier_v2 import (
    ClassifierConfig,
    IntentClassificationResult,
    IntentClassifierV2,
    IntentType,
    MultiLabelResult,
)
from src.query.temporal_processor import (
    RecencyBoostConfig,
    TemporalContext,
    TemporalProcessor,
    TimeAwareRetriever,
)

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Complexity level of a query."""

    SIMPLE = "simple"  # Single intent, few entities
    MODERATE = "moderate"  # Multiple intents or entities
    COMPLEX = "complex"  # Multiple constraints, complex logic


@dataclass
class ParsedQuery:
    """Result of parsing a query.

    Attributes:
        original_query: Original input query
        normalized_query: Normalized/cleaned query
        tokens: Tokenized query
        intents: Detected intents
        primary_intent: Primary intent
        entities: Extracted entities
        temporal_context: Temporal constraints and context
        complexity: Query complexity level
        metadata: Additional parsing metadata
    """

    original_query: str
    normalized_query: str
    tokens: List[str]
    intents: List[IntentType]
    primary_intent: IntentType
    entities: List[Entity]
    temporal_context: TemporalContext
    complexity: QueryComplexity
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert parsed query to dictionary."""
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "tokens": self.tokens,
            "intents": [i.value for i in self.intents],
            "primary_intent": self.primary_intent.value,
            "entities": [e.to_dict() for e in self.entities],
            "temporal_context": self.temporal_context.to_dict(),
            "complexity": self.complexity.value,
            "metadata": self.metadata,
        }


@dataclass
class QueryUnderstandingResult:
    """Complete result of query understanding.

    Attributes:
        parsed_query: Parsed query structure
        intent_result: Detailed intent classification result
        multi_label_result: Multi-label classification result
        kg_prep: Knowledge graph preparation data
        retrieval_params: Parameters for retrieval
        confidence: Overall confidence score
        processing_time_ms: Processing time in milliseconds
    """

    parsed_query: ParsedQuery
    intent_result: IntentClassificationResult
    multi_label_result: MultiLabelResult
    kg_prep: KnowledgeGraphPrep
    retrieval_params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "parsed_query": self.parsed_query.to_dict(),
            "intent_result": self.intent_result.to_dict(),
            "multi_label_result": self.multi_label_result.to_dict(),
            "kg_prep": self.kg_prep.to_dict(),
            "retrieval_params": self.retrieval_params,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
        }


@dataclass
class ParserConfig:
    """Configuration for the advanced parser.

    Attributes:
        classifier_config: Intent classifier configuration
        extraction_config: Entity extraction configuration
        recency_config: Recency boosting configuration
        enable_multi_label: Enable multi-label classification
        enable_kg_prep: Enable knowledge graph preparation
        min_confidence: Minimum overall confidence threshold
        domain: Domain context
    """

    classifier_config: Optional[ClassifierConfig] = None
    extraction_config: Optional[ExtractionConfig] = None
    recency_config: Optional[RecencyBoostConfig] = None
    enable_multi_label: bool = True
    enable_kg_prep: bool = True
    min_confidence: float = 0.5
    domain: str = "real_estate"


class AdvancedQueryParser:
    """Main interface for advanced query understanding.

    Orchestrates intent classification, entity extraction, and temporal
    processing into a unified query understanding pipeline.

    Example:
        ```python
        parser = AdvancedQueryParser(domain="real_estate")

        # Parse a query
        result = parser.parse(
            "Show me 3-bedroom houses in Rancho Cucamonga under $800k listed last week"
        )

        print(result.parsed_query.primary_intent)
        # IntentType.PROPERTY_SEARCH

        print(result.parsed_query.entities)
        # [Entity(text='3-bedroom', type= bedrooms), ...]

        print(result.retrieval_params)
        # {'filters': {...}, 'boost': {...}, ...}
        ```
    """

    def __init__(self, config: Optional[ParserConfig] = None):
        """Initialize advanced query parser.

        Args:
            config: Parser configuration
        """
        self.config = config or ParserConfig()

        # Initialize sub-components
        self.intent_classifier = IntentClassifierV2(
            config=self.config.classifier_config or ClassifierConfig(domain=self.config.domain)
        )
        self.entity_extractor = EntityExtractor(
            config=self.config.extraction_config or ExtractionConfig(domain=self.config.domain)
        )
        self.temporal_processor = TemporalProcessor()
        self.time_aware_retriever = TimeAwareRetriever()

        logger.info(f"Initialized AdvancedQueryParser with domain={self.config.domain}")

    def parse(self, query: str) -> QueryUnderstandingResult:
        """Parse and understand a query.

        Args:
            query: Input query string

        Returns:
            Complete query understanding result

        Raises:
            RetrievalError: If parsing fails
        """
        import time

        start_time = time.time()

        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")

        try:
            # Step 1: Normalize and tokenize
            normalized_query = self._normalize_query(query)
            tokens = self._tokenize(normalized_query)

            # Step 2: Classify intent
            intent_result = self.intent_classifier.classify(normalized_query)

            # Step 3: Multi-label classification (if enabled)
            if self.config.enable_multi_label:
                multi_label_result = self.intent_classifier.classify_multi_label(normalized_query)
            else:
                multi_label_result = MultiLabelResult(
                    intents=[intent_result.primary_intent],
                    primary_intent=intent_result.primary_intent,
                    confidence_scores={intent_result.primary_intent: intent_result.confidence},
                    coverage_score=intent_result.confidence,
                )

            # Step 4: Extract entities
            entities = self.entity_extractor.extract(normalized_query)
            entities = self.entity_extractor.disambiguate(entities, normalized_query)

            # Step 5: Extract temporal context
            temporal_context = self.temporal_processor.extract_temporal_context(normalized_query)

            # Step 6: Determine complexity
            complexity = self._calculate_complexity(normalized_query, multi_label_result, entities, temporal_context)

            # Step 7: Build parsed query
            parsed_query = ParsedQuery(
                original_query=query,
                normalized_query=normalized_query,
                tokens=tokens,
                intents=multi_label_result.intents,
                primary_intent=intent_result.primary_intent,
                entities=entities,
                temporal_context=temporal_context,
                complexity=complexity,
            )

            # Step 8: Prepare for knowledge graph (if enabled)
            if self.config.enable_kg_prep:
                kg_prep = self.entity_extractor.prepare_for_knowledge_graph(entities, normalized_query)
            else:
                kg_prep = KnowledgeGraphPrep(entities=entities)

            # Step 9: Generate retrieval parameters
            retrieval_params = self._generate_retrieval_params(parsed_query, temporal_context)

            # Step 10: Calculate overall confidence
            confidence = self._calculate_overall_confidence(intent_result, entities, temporal_context)

            processing_time = (time.time() - start_time) * 1000

            result = QueryUnderstandingResult(
                parsed_query=parsed_query,
                intent_result=intent_result,
                multi_label_result=multi_label_result,
                kg_prep=kg_prep,
                retrieval_params=retrieval_params,
                confidence=confidence,
                processing_time_ms=processing_time,
            )

            logger.debug(f"Parsed query in {processing_time:.2f}ms with confidence {confidence:.2f}")

            return result

        except Exception as e:
            logger.error(f"Query parsing failed: {e}")
            raise RetrievalError(f"Query parsing failed: {str(e)}") from e

    def _normalize_query(self, query: str) -> str:
        """Normalize a query string.

        Args:
            query: Input query

        Returns:
            Normalized query
        """
        # Lowercase
        normalized = query.lower().strip()

        # Remove extra whitespace
        normalized = " ".join(normalized.split())

        # Normalize punctuation
        normalized = re.sub(r"\s+([?.!,])", r"\1", normalized)

        # Expand common contractions
        contractions = {
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "can't": "cannot",
            "won't": "will not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
        }

        for contraction, expansion in contractions.items():
            normalized = normalized.replace(contraction, expansion)

        return normalized

    def _tokenize(self, query: str) -> List[str]:
        """Tokenize a query.

        Args:
            query: Input query

        Returns:
            List of tokens
        """
        # Simple tokenization - split on whitespace and punctuation
        tokens = re.findall(r"\b\w+\b|[^\w\s]", query)
        return tokens

    def _calculate_complexity(
        self,
        query: str,
        multi_label_result: MultiLabelResult,
        entities: List[Entity],
        temporal_context: TemporalContext,
    ) -> QueryComplexity:
        """Calculate query complexity.

        Args:
            query: Normalized query
            multi_label_result: Multi-label classification result
            entities: Extracted entities
            temporal_context: Temporal context

        Returns:
            Complexity level
        """
        score = 0

        # Intent complexity
        if len(multi_label_result.intents) > 1:
            score += 1
        if len(multi_label_result.intents) > 2:
            score += 1

        # Entity complexity
        if len(entities) > 3:
            score += 1
        if len(entities) > 5:
            score += 1

        # Temporal complexity
        if len(temporal_context.constraints) > 1:
            score += 1

        # Query length
        word_count = len(query.split())
        if word_count > 10:
            score += 1
        if word_count > 20:
            score += 1

        # Determine complexity
        if score <= 2:
            return QueryComplexity.SIMPLE
        elif score <= 4:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.COMPLEX

    def _generate_retrieval_params(
        self, parsed_query: ParsedQuery, temporal_context: TemporalContext
    ) -> Dict[str, Any]:
        """Generate retrieval parameters from parsed query.

        Args:
            parsed_query: Parsed query
            temporal_context: Temporal context

        Returns:
            Retrieval parameters
        """
        params = {
            "filters": {},
            "boost": {},
            "sort": [],
            "limit": 10,
        }

        # Add entity-based filters
        for entity in parsed_query.entities:
            if entity.type == EntityType.CITY:
                params["filters"]["city"] = entity.normalized_value
            elif entity.type == EntityType.NEIGHBORHOOD:
                params["filters"]["neighborhood"] = entity.normalized_value
            elif entity.type == EntityType.BEDROOMS:
                params["filters"]["bedrooms"] = entity.normalized_value
            elif entity.type == EntityType.BATHROOMS:
                params["filters"]["bathrooms"] = entity.normalized_value
            elif entity.type == EntityType.PRICE:
                # Parse price constraints
                price_val = self._parse_price(entity.normalized_value)
                if price_val:
                    params["filters"]["price"] = price_val
            elif entity.type == EntityType.PROPERTY_TYPE:
                params["filters"]["property_type"] = entity.normalized_value
            elif entity.type == EntityType.ZIP_CODE:
                params["filters"]["zip_code"] = entity.normalized_value

        # Add temporal filters
        if temporal_context.primary_constraint:
            constraint = temporal_context.primary_constraint
            if constraint.start_date:
                params["filters"]["date_from"] = constraint.start_date.isoformat()
            if constraint.end_date:
                params["filters"]["date_to"] = constraint.end_date.isoformat()

        # Add recency boost if applicable
        if temporal_context.recency_preference > 0.7:
            params["boost"]["recency"] = {
                "enabled": True,
                "weight": temporal_context.recency_preference,
            }

        # Add intent-based parameters
        intent_boosts = {
            IntentType.PROPERTY_SEARCH: {"field": "listing_status", "value": "active"},
            IntentType.BUYING_INTENT: {"field": "for_sale", "value": True},
            IntentType.SELLING_INTENT: {"field": "recently_sold", "value": True},
        }

        if parsed_query.primary_intent in intent_boosts:
            boost_config = intent_boosts[parsed_query.primary_intent]
            params["boost"]["intent"] = boost_config

        # Set limit based on complexity
        if parsed_query.complexity == QueryComplexity.SIMPLE:
            params["limit"] = 10
        elif parsed_query.complexity == QueryComplexity.MODERATE:
            params["limit"] = 20
        else:
            params["limit"] = 30

        return params

    def _parse_price(self, price_text: str) -> Optional[Dict[str, Any]]:
        """Parse price text into structured format.

        Args:
            price_text: Price text (e.g., "$800k", "under $900000")

        Returns:
            Parsed price structure
        """
        # Extract numeric value
        match = re.search(r"(\d+(?:\.\d+)?)", price_text.replace(",", ""))
        if not match:
            return None

        value = float(match.group(1))

        # Check for K/M suffix
        if "k" in price_text.lower():
            value *= 1000
        elif "m" in price_text.lower():
            value *= 1000000

        # Determine constraint type
        if "under" in price_text or "below" in price_text or "less" in price_text:
            return {"type": "max", "value": value}
        elif "over" in price_text or "above" in price_text or "more" in price_text:
            return {"type": "min", "value": value}
        else:
            return {"type": "exact", "value": value}

    def _calculate_overall_confidence(
        self,
        intent_result: IntentClassificationResult,
        entities: List[Entity],
        temporal_context: TemporalContext,
    ) -> float:
        """Calculate overall confidence score.

        Args:
            intent_result: Intent classification result
            entities: Extracted entities
            temporal_context: Temporal context

        Returns:
            Overall confidence (0.0-1.0)
        """
        # Intent confidence
        intent_conf = intent_result.confidence

        # Entity confidence (average)
        if entities:
            entity_conf = sum(e.confidence for e in entities) / len(entities)
        else:
            entity_conf = 0.5

        # Temporal confidence
        if temporal_context.primary_constraint:
            temporal_conf = temporal_context.primary_constraint.confidence
        else:
            temporal_conf = 0.5

        # Weighted average
        overall = (intent_conf * 0.4) + (entity_conf * 0.35) + (temporal_conf * 0.25)

        return min(1.0, max(0.0, overall))

    def batch_parse(self, queries: List[str]) -> List[QueryUnderstandingResult]:
        """Parse multiple queries in batch.

        Args:
            queries: List of queries

        Returns:
            List of parsing results
        """
        results = []
        for query in queries:
            try:
                result = self.parse(query)
                results.append(result)
            except RetrievalError as e:
                logger.warning(f"Failed to parse query '{query}': {e}")
                # Add error result
                results.append(
                    QueryUnderstandingResult(
                        parsed_query=ParsedQuery(
                            original_query=query,
                            normalized_query=query,
                            tokens=[],
                            intents=[IntentType.INFORMATIONAL],
                            primary_intent=IntentType.INFORMATIONAL,
                            entities=[],
                            temporal_context=TemporalContext(),
                            complexity=QueryComplexity.SIMPLE,
                            metadata={"error": str(e)},
                        ),
                        intent_result=IntentClassificationResult(
                            primary_intent=IntentType.INFORMATIONAL,
                            confidence=0.0,
                            raw_confidence=0.0,
                            features={},
                        ),
                        multi_label_result=MultiLabelResult(
                            intents=[IntentType.INFORMATIONAL],
                            primary_intent=IntentType.INFORMATIONAL,
                            confidence_scores={IntentType.INFORMATIONAL: 0.0},
                            coverage_score=0.0,
                        ),
                        kg_prep=KnowledgeGraphPrep(entities=[]),
                        confidence=0.0,
                    )
                )

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics.

        Returns:
            Dictionary with parser statistics
        """
        return {
            "config": {
                "enable_multi_label": self.config.enable_multi_label,
                "enable_kg_prep": self.config.enable_kg_prep,
                "min_confidence": self.config.min_confidence,
                "domain": self.config.domain,
            },
            "classifier": self.intent_classifier.get_stats(),
            "extractor": self.entity_extractor.get_stats(),
        }


class QueryProcessingPipeline:
    """Pipeline for processing queries with multiple stages.

    Provides a configurable pipeline for query processing with
    support for custom processors and transformations.

    Example:
        ```python
        pipeline = QueryProcessingPipeline()
            .add_stage("normalize", normalize_query)
            .add_stage("classify", classify_intent)
            .add_stage("extract", extract_entities)

        result = pipeline.process("Show me houses in Rancho Cucamonga")
        ```
    """

    def __init__(self):
        """Initialize processing pipeline."""
        self.stages: List[Tuple[str, callable]] = []
        self.parser = AdvancedQueryParser()

    def add_stage(self, name: str, processor: callable) -> "QueryProcessingPipeline":
        """Add a processing stage.

        Args:
            name: Stage name
            processor: Processing function

        Returns:
            Self for method chaining
        """
        self.stages.append((name, processor))
        return self

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a query through all stages.

        Args:
            query: Input query
            context: Optional context dictionary

        Returns:
            Processing result with all stage outputs
        """
        context = context or {}
        results = {"original_query": query, "stages": {}}

        current_data = query

        for stage_name, processor in self.stages:
            try:
                current_data = processor(current_data, context)
                results["stages"][stage_name] = {
                    "status": "success",
                    "output": current_data,
                }
            except Exception as e:
                results["stages"][stage_name] = {
                    "status": "error",
                    "error": str(e),
                }
                break

        results["final_output"] = current_data
        return results

    def process_with_parser(self, query: str) -> QueryUnderstandingResult:
        """Process query using the advanced parser.

        Args:
            query: Input query

        Returns:
            Query understanding result
        """
        return self.parser.parse(query)
