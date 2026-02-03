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

from src.query.intent_classifier_v2 import (
    IntentClassifierV2,
    IntentClassificationResult,
    IntentType,
    MultiLabelResult,
    ConfidenceCalibrator,
)
from src.query.temporal_processor import (
    TemporalProcessor,
    TemporalConstraint,
    TemporalConstraintType,
    RecencyBoostConfig,
    TimeAwareRetriever,
)
from src.query.entity_extractor import (
    EntityExtractor,
    Entity,
    EntityType,
    EntityLinkingResult,
    KnowledgeGraphPrep,
)
from src.query.advanced_parser import (
    AdvancedQueryParser,
    ParsedQuery,
    QueryUnderstandingResult,
    QueryProcessingPipeline,
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
