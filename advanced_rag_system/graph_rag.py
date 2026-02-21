"""Graph RAG Implementation with Knowledge Graph Integration.

This module provides Graph RAG capabilities including:
- Knowledge graph construction and querying
- Entity extraction and relationship mapping
- Citation generation for sources
- Entity-aware response generation
"""

from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult
from src.query.entity_extractor import (
    Entity,
    EntityExtractor,
    EntityLinkingResult,
    EntityType,
    ExtractionConfig,
    KnowledgeGraphPrep,
)


class RelationshipType(str, Enum):
    """Types of relationships in the knowledge graph."""

    # General relationships
    HAS_PROPERTY = "has_property"
    LOCATED_IN = "located_in"
    PART_OF = "part_of"
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    MENTIONED_IN = "mentioned_in"

    # Real estate specific
    PRICE_OF = "price_of"
    SOLD_BY = "sold_by"
    BUYER_OF = "buyer_of"
    AGENT_FOR = "agent_for"
    LOCATED_AT = "located_at"
    NEAR = "near"
    HAS_FEATURE = "has_feature"
    HAS_BEDROOMS = "has_bedrooms"
    HAS_BATHROOMS = "has_bathrooms"
    BUILT_IN = "built_in"


@dataclass
class KnowledgeGraphNode:
    """Represents a node in the knowledge graph.

    Attributes:
        id: Unique identifier for the node
        entity_type: Type of entity
        name: Human-readable name
        properties: Additional properties
        document_ids: Source documents
        confidence: Confidence score
    """

    id: str
    entity_type: str
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    document_ids: List[UUID] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class KnowledgeGraphEdge:
    """Represents an edge (relationship) in the knowledge graph.

    Attributes:
        id: Unique identifier for the edge
        source_id: Source node ID
        target_id: Target node ID
        relationship_type: Type of relationship
        properties: Additional properties
        weight: Edge weight/confidence
    """

    id: str
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


@dataclass
class Citation:
    """Represents a citation for a source.

    Attributes:
        source_id: ID of the source document
        chunk_id: ID of the chunk
        content: Citation content
        relevance: Relevance score
        position: Position in source
    """

    source_id: str
    chunk_id: UUID
    content: str
    relevance: float
    position: int


@dataclass
class GraphRAGConfig:
    """Configuration for Graph RAG.

    Attributes:
        enable_entity_extraction: Extract entities from queries
        enable_citation_generation: Generate citations for sources
        enable_relationship_detection: Detect entity relationships
        max_citations: Maximum citations to generate
        min_entity_confidence: Minimum confidence for entity extraction
        use_knowledge_graph: Use knowledge graph for retrieval
        graph_depth: Depth of graph traversal
    """

    enable_entity_extraction: bool = True
    enable_citation_generation: bool = True
    enable_relationship_detection: bool = True
    max_citations: int = 10
    min_entity_confidence: float = 0.5
    use_knowledge_graph: bool = True
    graph_depth: int = 2


class CitationGenerator:
    """Generate citations for search results."""

    def __init__(self, max_citations: int = 10):
        """Initialize citation generator.

        Args:
            max_citations: Maximum number of citations to generate
        """
        self.max_citations = max_citations

    def generate(
        self,
        results: List[SearchResult],
        query: str,
    ) -> List[Citation]:
        """Generate citations for search results.

        Args:
            results: Search results to cite
            query: Original query

        Returns:
            List of citations
        """
        citations = []

        # Score each result and generate citation
        for rank, result in enumerate(results[: self.max_citations], 1):
            # Calculate relevance
            relevance = self._calculate_relevance(result, query)

            # Extract citation content
            content = self._extract_citation_content(result.chunk)

            citation = Citation(
                source_id=str(result.chunk.metadata.source or ""),
                chunk_id=result.chunk.id,
                content=content,
                relevance=relevance,
                position=rank,
            )
            citations.append(citation)

        return citations

    def _calculate_relevance(
        self,
        result: SearchResult,
        query: str,
    ) -> float:
        """Calculate relevance score for citation.

        Args:
            result: Search result
            query: Original query

        Returns:
            Relevance score
        """
        # Combine result score with rank
        rank_factor = 1.0 / (result.rank or 1)
        score_factor = result.score

        relevance = 0.7 * score_factor + 0.3 * rank_factor
        return min(relevance, 1.0)

    def _extract_citation_content(self, chunk: DocumentChunk) -> str:
        """Extract relevant content for citation.

        Args:
            chunk: Document chunk

        Returns:
            Citation content
        """
        content = chunk.content

        # Truncate if too long
        max_length = 300
        if len(content) > max_length:
            content = content[:max_length] + "..."

        return content

    def format_citations(
        self,
        citations: List[Citation],
        style: str = "numbered",
    ) -> str:
        """Format citations for display.

        Args:
            citations: List of citations
            style: Citation style ('numbered', 'brackets')

        Returns:
            Formatted citations string
        """
        if not citations:
            return ""

        lines = ["\n\n## Sources\n"]

        for i, citation in enumerate(citations, 1):
            if style == "numbered":
                prefix = f"[{i}]"
            else:
                prefix = f"({i})"

            lines.append(f"{prefix} {citation.content}")

        return "\n".join(lines)


class RelationshipDetector:
    """Detect relationships between entities."""

    # Patterns for relationship detection
    RELATIONSHIP_PATTERNS = {
        RelationshipType.HAS_PROPERTY: [
            r"(\w+)\s+has\s+(\w+)",
            r"(\w+)\s+with\s+(\w+)",
            r"(\w+)\s+includes?\s+(\w+)",
        ],
        RelationshipType.LOCATED_IN: [
            r"(\w+)\s+in\s+(\w+)",
            r"(\w+)\s+located\s+in\s+(\w+)",
            r"(\w+)\s+at\s+(\w+)",
        ],
        RelationshipType.NEAR: [
            r"(\w+)\s+near\s+(\w+)",
            r"(\w+)\s+close\s+to\s+(\w+)",
            r"(\w+)\s+nearby\s+(\w+)",
        ],
        RelationshipType.HAS_FEATURE: [
            r"(\w+)\s+with\s+(pool|garage|garden|patio)",
            r"(\w+)\s+has\s+(pool|garage|garden|patio)",
        ],
        RelationshipType.PRICE_OF: [
            r"\$\d+[\d,]*\s+(\w+)",
            r"price\s+of\s+(\w+)",
            r"(\w+)\s+priced\s+at",
        ],
    }

    def __init__(self):
        """Initialize relationship detector."""
        self._compiled_patterns: Dict[RelationshipType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns."""
        for rel_type, patterns in self.RELATIONSHIP_PATTERNS.items():
            self._compiled_patterns[rel_type] = [re.compile(p, re.I) for p in patterns]

    def detect_relationships(
        self,
        entities: List[Entity],
        text: str,
    ) -> List[Tuple[str, str, RelationshipType]]:
        """Detect relationships between entities in text.

        Args:
            entities: Extracted entities
            text: Source text

        Returns:
            List of (source, target, relationship) tuples
        """
        relationships = []
        text_lower = text.lower()

        # Extract entity names
        entity_names = {e.normalized_value for e in entities}

        # Check each relationship pattern
        for rel_type, patterns in self._compiled_patterns.items():
            for pattern in patterns:
                matches = pattern.finditer(text_lower)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        source = groups[0].strip()
                        target = groups[1].strip()

                        # Check if either is an entity
                        if source in entity_names or target in entity_names:
                            relationships.append((source, target, rel_type))

        return relationships


class KnowledgeGraph:
    """In-memory knowledge graph for Graph RAG."""

    def __init__(self):
        """Initialize knowledge graph."""
        self.nodes: Dict[str, KnowledgeGraphNode] = {}
        self.edges: List[KnowledgeGraphEdge] = []
        self._node_index: Dict[str, str] = {}  # name -> node_id

    def add_node(
        self,
        entity: Entity,
        document_id: Optional[UUID] = None,
    ) -> str:
        """Add a node to the knowledge graph.

        Args:
            entity: Entity to add
            document_id: Source document ID

        Returns:
            Node ID
        """
        # Create node ID from entity
        node_id = self._create_node_id(entity)

        if node_id in self.nodes:
            # Update existing node
            node = self.nodes[node_id]
            if document_id and document_id not in node.document_ids:
                node.document_ids.append(document_id)
            node.confidence = max(node.confidence, entity.confidence)
        else:
            # Create new node
            node = KnowledgeGraphNode(
                id=node_id,
                entity_type=entity.type.value,
                name=entity.text,
                properties={"normalized": entity.normalized_value},
                document_ids=[document_id] if document_id else [],
                confidence=entity.confidence,
            )
            self.nodes[node_id] = node
            self._node_index[entity.normalized_value.lower()] = node_id

        return node_id

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relationship: RelationshipType,
        weight: float = 1.0,
    ) -> None:
        """Add an edge to the knowledge graph.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relationship: Relationship type
            weight: Edge weight
        """
        edge_id = str(uuid4())
        edge = KnowledgeGraphEdge(
            id=edge_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship,
            weight=weight,
        )
        self.edges.append(edge)

    def get_neighbors(
        self,
        node_id: str,
        depth: int = 1,
    ) -> List[KnowledgeGraphNode]:
        """Get neighboring nodes.

        Args:
            node_id: Starting node ID
            depth: Traversal depth

        Returns:
            List of neighboring nodes
        """
        if node_id not in self.nodes:
            return []

        visited = {node_id}
        queue = [(node_id, 0)]
        neighbors = []

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_depth >= depth:
                continue

            # NOTE: O(E*D) scan — for large graphs, consider an adjacency list
            # index (Dict[str, List[KnowledgeGraphEdge]]) keyed by source_id.
            for edge in self.edges:
                if edge.source_id == current_id:
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        if edge.target_id in self.nodes:
                            neighbors.append(self.nodes[edge.target_id])
                            queue.append((edge.target_id, current_depth + 1))

        return neighbors

    def search(
        self,
        query: str,
        entities: List[Entity],
    ) -> List[KnowledgeGraphNode]:
        """Search the knowledge graph.

        Args:
            query: Search query
            entities: Extracted entities

        Returns:
            List of matching nodes
        """
        results = []

        for entity in entities:
            node_id = self._node_index.get(entity.normalized_value.lower())
            if node_id and node_id in self.nodes:
                results.append(self.nodes[node_id])

        return results

    def _create_node_id(self, entity: Entity) -> str:
        """Create unique node ID from entity.

        Args:
            entity: Entity

        Returns:
            Node ID
        """
        # Use hash of normalized value (SHA-256 for collision resistance)
        hash_input = f"{entity.type.value}:{entity.normalized_value}".encode()
        return hashlib.sha256(hash_input).hexdigest()[:16]


class GraphRAGEngine:
    """Graph RAG engine for entity-aware retrieval with citations.

    This implementation provides:
    - Entity extraction from queries and documents
    - Knowledge graph construction and querying
    - Citation generation for sources
    - Entity-aware response generation

    Example:
        ```python
        config = GraphRAGConfig(
            enable_entity_extraction=True,
            enable_citation_generation=True,
        )
        engine = GraphRAGEngine(config)
        await engine.initialize()

        result = await engine.retrieve("3 bedroom house in Rancho Cucamonga")
        await engine.close()
        ```
    """

    def __init__(self, config: Optional[GraphRAGConfig] = None):
        """Initialize Graph RAG engine.

        Args:
            config: Configuration for Graph RAG
        """
        self.config = config or GraphRAGConfig()

        # Initialize components
        extraction_config = ExtractionConfig(
            confidence_threshold=self.config.min_entity_confidence,
        )
        self._entity_extractor = EntityExtractor(extraction_config)
        self._citation_generator = CitationGenerator(self.config.max_citations)
        self._relationship_detector = RelationshipDetector()

        # Knowledge graph
        self._knowledge_graph = KnowledgeGraph()

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the Graph RAG engine.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Entity extractor is already initialized
            self._initialized = True

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to initialize GraphRAGEngine: {str(e)}",
                error_code="GRAPH_RAG_INIT_ERROR",
            ) from e

    async def close(self) -> None:
        """Close the engine and cleanup resources."""
        self._initialized = False

    def add_documents(
        self,
        chunks: List[DocumentChunk],
    ) -> None:
        """Add documents to the knowledge graph.

        Args:
            chunks: Document chunks to add

        Raises:
            RetrievalError: If document processing fails
        """
        if not chunks:
            return

        try:
            for chunk in chunks:
                # Extract entities from chunk
                entities = self._entity_extractor.extract(chunk.content)

                # Add entities to knowledge graph
                for entity in entities:
                    if entity.confidence >= self.config.min_entity_confidence:
                        self._knowledge_graph.add_node(entity, chunk.document_id)

                # Detect relationships if enabled
                if self.config.enable_relationship_detection:
                    relationships = self._relationship_detector.detect_relationships(entities, chunk.content)
                    for source, target, rel_type in relationships:
                        # Find node IDs
                        source_id = self._knowledge_graph._node_index.get(source.lower())
                        target_id = self._knowledge_graph._node_index.get(target.lower())

                        if source_id and target_id:
                            self._knowledge_graph.add_edge(source_id, target_id, rel_type)

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to add documents to knowledge graph: {str(e)}",
                error_code="KG_ADD_ERROR",
            ) from e

    async def retrieve(
        self,
        query: str,
        results: List[SearchResult],
    ) -> GraphRAGResult:
        """Retrieve with entity awareness and citations.

        Args:
            query: Search query
            results: Initial search results

        Returns:
            GraphRAGResult with entities, citations, and enhanced results

        Raises:
            RetrievalError: If retrieval fails
        """
        if not self._initialized:
            raise RetrievalError("GraphRAGEngine not initialized")

        if not results:
            return GraphRAGResult(
                query=query,
                results=[],
                entities=[],
                citations=[],
                knowledge_graph_context={},
            )

        try:
            # Extract entities from query
            query_entities = []
            if self.config.enable_entity_extraction:
                query_entities = self._entity_extractor.extract(query)

            # Search knowledge graph
            kg_context = {}
            if self.config.use_knowledge_graph:
                kg_nodes = self._knowledge_graph.search(query, query_entities)
                kg_context = self._build_kg_context(kg_nodes)

            # Generate citations
            citations = []
            if self.config.enable_citation_generation:
                citations = self._citation_generator.generate(results, query)

            return GraphRAGResult(
                query=query,
                results=results,
                entities=query_entities,
                citations=citations,
                knowledge_graph_context=kg_context,
            )

        except Exception as e:
            raise RetrievalError(
                message=f"Graph RAG retrieval failed: {str(e)}",
                error_code="GRAPH_RAG_RETRIEVAL_ERROR",
            ) from e

    def _build_kg_context(
        self,
        nodes: List[KnowledgeGraphNode],
    ) -> Dict[str, Any]:
        """Build knowledge graph context from nodes.

        Args:
            nodes: Nodes from knowledge graph

        Returns:
            Context dictionary
        """
        context = {
            "entities": [],
            "relationships": [],
        }

        for node in nodes:
            context["entities"].append(
                {
                    "id": node.id,
                    "type": node.entity_type,
                    "name": node.name,
                    "confidence": node.confidence,
                }
            )

            # Get neighbors
            neighbors = self._knowledge_graph.get_neighbors(node.id, self.config.graph_depth)

            for neighbor in neighbors:
                context["relationships"].append(
                    {
                        "from": node.name,
                        "to": neighbor.name,
                        "type": "related_to",
                    }
                )

        return context

    def get_citations_text(
        self,
        citations: List[Citation],
        style: str = "numbered",
    ) -> str:
        """Get formatted citations text.

        Args:
            citations: List of citations
            style: Citation style

        Returns:
            Formatted citations string
        """
        return self._citation_generator.format_citations(citations, style)

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "node_count": len(self._knowledge_graph.nodes),
            "edge_count": len(self._knowledge_graph.edges),
            "entity_types": self._count_entity_types(),
        }

    def _count_entity_types(self) -> Dict[str, int]:
        """Count entities by type.

        Returns:
            Dictionary of entity type counts
        """
        counts: Dict[str, int] = {}
        for node in self._knowledge_graph.nodes.values():
            entity_type = node.entity_type
            counts[entity_type] = counts.get(entity_type, 0) + 1
        return counts


@dataclass
class GraphRAGResult:
    """Result of Graph RAG retrieval.

    Attributes:
        query: Original query
        results: Search results
        entities: Extracted entities
        citations: Generated citations
        knowledge_graph_context: Knowledge graph context
    """

    query: str
    results: List[SearchResult]
    entities: List[Entity] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    knowledge_graph_context: Dict[str, Any] = field(default_factory=dict)

    def get_citations_text(self, style: str = "numbered") -> str:
        """Get formatted citations.

        Args:
            style: Citation style

        Returns:
            Formatted citations string
        """
        if not self.citations:
            return ""

        lines = ["\n\n## Sources\n"]
        for i, citation in enumerate(self.citations, 1):
            if style == "numbered":
                prefix = f"[{i}]"
            else:
                prefix = f"({i})"
            lines.append(f"{prefix} {citation.content}")

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "query": self.query,
            "results_count": len(self.results),
            "entities": [e.to_dict() for e in self.entities],
            "citations_count": len(self.citations),
            "knowledge_graph_context": self.knowledge_graph_context,
        }


# Alias for easier imports
GraphRAG = GraphRAGEngine
