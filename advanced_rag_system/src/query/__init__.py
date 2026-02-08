"""Advanced Query Understanding Module.

This module provides enhanced query processing capabilities including:
- Intent Classification V2 with multi-label support and confidence calibration
- Temporal Processing for time-aware retrieval
- Entity Extraction and Linking
- Advanced Query Parsing and Orchestration

Example:
    ```python
    from src.query import AdvancedQueryParser

    parser = AdvancedQueryParser()
    result = parser.parse("Show me houses in Rancho Cucamonga under $800k listed last week")

    print(result.intents)  # ['property_search', 'location_filter']
    print(result.entities)  # [Entity(type='location', value='Rancho Cucamonga'), ...]
    print(result.temporal_constraints)  # TemporalConstraint(type='relative', value='last week')
    ```
"""

from src.query.advanced_parser import (
    AdvancedQueryParser,
    ParsedQuery,
    QueryProcessingPipeline,
    QueryUnderstandingResult,
)
from src.query.entity_extractor import (
    Entity,
    EntityExtractor,
    EntityLinkingResult,
    EntityType,
    KnowledgeGraphPrep,
)
from src.query.intent_classifier_v2 import (
    ConfidenceCalibrator,
    IntentClassificationResult,
    IntentClassifierV2,
    IntentType,
    MultiLabelResult,
)
from src.query.temporal_processor import (
    RecencyBoostConfig,
    TemporalConstraint,
    TemporalConstraintType,
    TemporalProcessor,
    TimeAwareRetriever,
)

__all__ = [
    # Intent Classification V2
    "IntentClassifierV2",
    "IntentClassificationResult",
    "IntentType",
    "MultiLabelResult",
    "ConfidenceCalibrator",
    # Temporal Processing
    "TemporalProcessor",
    "TemporalConstraint",
    "TemporalConstraintType",
    "RecencyBoostConfig",
    "TimeAwareRetriever",
    # Entity Extraction
    "EntityExtractor",
    "Entity",
    "EntityType",
    "EntityLinkingResult",
    "KnowledgeGraphPrep",
    # Advanced Parser
    "AdvancedQueryParser",
    "ParsedQuery",
    "QueryUnderstandingResult",
    "QueryProcessingPipeline",
]
