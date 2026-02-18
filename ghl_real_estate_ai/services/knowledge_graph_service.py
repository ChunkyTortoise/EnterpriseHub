"""
Knowledge Graph Service - The "Graphiti" Agent Brain
=====================================================
Provides persistent, evolving, and structured memory for the Real Estate AI.
Implements the 3-layer memory architecture:
1. Short-Term (Working Memory)
2. Mid-Term (Episodic Memory - Edges)
3. Long-Term (Semantic Memory - Nodes)

Author: EnterpriseHub AI Platform
Date: January 13, 2026
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EntityType(str, Enum):
    LEAD = "Lead"
    AGENT = "Agent"
    PROPERTY = "Property"
    LOCATION = "Location"
    CRITERION = "Criterion"
    INSIGHT = "Insight"

class RelationType(str, Enum):
    INTERESTED_IN = "INTERESTED_IN"
    LOCATED_IN = "LOCATED_IN"
    HAS_BUDGET = "HAS_BUDGET"
    REJECTED = "REJECTED"
    WORKS_WITH = "WORKS_WITH"
    DISLIKES = "DISLIKES"
    HAS_TIMELINE = "HAS_TIMELINE"
    OFFERING_ON = "OFFERING_ON"
    LIKELY_DISLIKES = "LIKELY_DISLIKES"

@dataclass
class GraphNode:
    id: str
    type: EntityType
    attributes: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class GraphEdge:
    source: str
    target: str
    relation: RelationType
    attributes: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    confidence: float = 1.0

class KnowledgeGraphService:
    """
    Python-native Knowledge Graph engine for Agent Memory.
    Persists to JSON and provides graph traversal for RAG context injection.
    """

    def __init__(self, storage_path: str = "data/memory/knowledge_graph.json"):
        self.storage_path = Path(storage_path)
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        
        # In-memory indices for faster traversal
        self._out_edges: Dict[str, List[int]] = {}  # source -> list of indices in self.edges
        self._in_edges: Dict[str, List[int]] = {}   # target -> list of indices in self.edges
        
        self._load()

    def _load(self):
        """Load graph from disk."""
        if not self.storage_path.exists():
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._save()
            return

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                
            self.nodes = {
                nid: GraphNode(**attr) 
                for nid, attr in data.get("nodes", {}).items()
            }
            self.edges = [
                GraphEdge(**edge) 
                for edge in data.get("edges", [])
            ]
            self._rebuild_indices()
            logger.info(f"Loaded {len(self.nodes)} nodes and {len(self.edges)} edges from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load knowledge graph: {e}")

    def _save(self):
        """Save graph to disk."""
        try:
            data = {
                "nodes": {nid: asdict(node) for nid, node in self.nodes.items()},
                "edges": [asdict(edge) for edge in self.edges]
            }
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")

    def _rebuild_indices(self):
        """Rebuild edge indices for faster lookups."""
        self._out_edges = {}
        self._in_edges = {}
        for i, edge in enumerate(self.edges):
            self._out_edges.setdefault(edge.source, []).append(i)
            self._in_edges.setdefault(edge.target, []).append(i)

    def add_node(self, node_id: str, node_type: EntityType, attributes: Dict[str, Any] = None) -> GraphNode:
        """Add or update a node."""
        if node_id in self.nodes:
            self.nodes[node_id].attributes.update(attributes or {})
            self.nodes[node_id].updated_at = datetime.now().isoformat()
        else:
            self.nodes[node_id] = GraphNode(id=node_id, type=node_type, attributes=attributes or {})
        
        self._save()
        return self.nodes[node_id]

    def add_edge(self, source_id: str, target_id: str, relation: RelationType, attributes: Dict[str, Any] = None, confidence: float = 1.0) -> GraphEdge:
        """Add a new relation between nodes."""
        # Ensure nodes exist
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(f"Cannot add edge: {source_id} or {target_id} does not exist.")
            return None

        # Check for duplicate recent edges to avoid noise (if same type and target)
        # In a real temporal graph, we might want to keep history, but for this strategy 
        # we'll update if it's very recent or just append.
        
        edge = GraphEdge(
            source=source_id, 
            target=target_id, 
            relation=relation, 
            attributes=attributes or {},
            confidence=confidence
        )
        self.edges.append(edge)
        self._rebuild_indices()
        self._save()
        return edge

    def get_neighbors(self, node_id: str) -> List[Tuple[GraphEdge, GraphNode]]:
        """Get all outgoing edges and their target nodes."""
        results = []
        for idx in self._out_edges.get(node_id, []):
            edge = self.edges[idx]
            target_node = self.nodes.get(edge.target)
            if target_node:
                results.append((edge, target_node))
        return results

    def get_context(self, lead_id: str) -> Dict[str, Any]:
        """
        Retrieval Strategy:
        1. 1-Hop: Direct preferences, budgets, rejections.
        2. 2-Hop: Related locations, properties in those locations.
        """
        if lead_id not in self.nodes:
            return {"error": "Lead not found in memory"}

        context = {
            "facts": [],
            "rejections": [],
            "preferences": [],
            "related_insights": []
        }

        # 1-Hop Walk
        visited_nodes = {lead_id}
        hop1 = self.get_neighbors(lead_id)
        
        for edge, node in hop1:
            fact = f"{edge.relation}: {node.id}"
            if edge.attributes:
                fact += f" ({edge.attributes})"
            
            if edge.relation == RelationType.REJECTED:
                context["rejections"].append(node.id)
            elif edge.relation in [RelationType.HAS_BUDGET, RelationType.DISLIKES, RelationType.HAS_TIMELINE]:
                context["preferences"].append(fact)
            else:
                context["facts"].append(fact)
            
            visited_nodes.add(node.id)

        # 2-Hop Walk (e.g. Lead -> Interested_In -> Location -> Market_Fact)
        for edge_h1, node_h1 in hop1:
            hop2 = self.get_neighbors(node_h1.id)
            for edge_h2, node_h2 in hop2:
                if node_h2.id not in visited_nodes:
                    insight = f"Because you like {node_h1.id}, note: {node_h2.type} {node_h2.id} is {edge_h2.relation}"
                    context["related_insights"].append(insight)
                    visited_nodes.add(node_h2.id)

        return context

    def get_context_prompt_snippet(self, lead_id: str) -> str:
        """Format the graph context into a readable string for system prompt injection."""
        ctx = self.get_context(lead_id)
        if "error" in ctx:
            return ""

        lines = ["### RELEVANT KNOWLEDGE (from Graph Memory)"]
        if ctx["facts"]:
            lines.append("Facts: " + ", ".join(ctx["facts"]))
        if ctx["preferences"]:
            lines.append("Preferences: " + ", ".join(ctx["preferences"]))
        if ctx["rejections"]:
            lines.append("Previously Rejected: " + ", ".join(ctx["rejections"]))
        if ctx["related_insights"]:
            lines.append("Market Insights: " + "; ".join(ctx["related_insights"]))
            
        return "\n".join(lines)

    def consolidate_memory(self):
        """
        The "Dream" Cycle:
        1. Conflict Resolution (Latest fact wins).
        2. Insight Generation (Pattern matching).
        3. Pruning (Remove old/isolated nodes).
        """
        logger.info("Starting Memory Consolidation Cycle...")
        
        # 1. Conflict Resolution (Simplistic: Keep latest for specific source-relation combos)
        # e.g., if multiple HAS_BUDGET edges for same lead, keeps most recent.
        new_edges = []
        seen_keys = set()
        
        # Walk backwards to keep newest
        for edge in reversed(self.edges):
            key = (edge.source, edge.relation)
            # For budgeting/timeline, we only care about the latest
            if edge.relation in [RelationType.HAS_BUDGET, RelationType.HAS_TIMELINE]:
                if key not in seen_keys:
                    new_edges.append(edge)
                    seen_keys.add(key)
            else:
                new_edges.append(edge)
        
        self.edges = list(reversed(new_edges))
        
        # 2. Insight Generation
        # If Lead rejected > 3 properties with "Pool", add LIKELY_DISLIKES: Pool
        # (This is a placeholder for actual ML/Pattern logic)
        
        # 3. Pruning
        # Remove nodes with no edges that are older than 90 days
        cutoff = datetime.now() - timedelta(days=90)
        active_nodes = set()
        for edge in self.edges:
            active_nodes.add(edge.source)
            active_nodes.add(edge.target)
            
        nodes_to_remove = []
        for nid, node in self.nodes.items():
            if nid not in active_nodes:
                created = datetime.fromisoformat(node.created_at)
                if created < cutoff:
                    nodes_to_remove.append(nid)
        
        for nid in nodes_to_remove:
            del self.nodes[nid]
            logger.info(f"Pruned isolated node: {nid}")

        self._rebuild_indices()
        self._save()
        logger.info("Consolidation Cycle Complete.")

# Global instance for easy access
knowledge_graph = KnowledgeGraphService()
