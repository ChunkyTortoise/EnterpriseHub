import os
import unittest
import json
from pathlib import Path
from services.knowledge_graph_service import KnowledgeGraphService, EntityType, RelationType

class TestKnowledgeGraph(unittest.TestCase):
    def setUp(self):
        self.test_path = "data/memory/test_graph.json"
        if os.path.exists(self.test_path):
            os.remove(self.test_path)
        self.service = KnowledgeGraphService(storage_path=self.test_path)

    def tearDown(self):
        if os.path.exists(self.test_path):
            os.remove(self.test_path)

    def test_node_creation(self):
        node = self.service.add_node("lead_123", EntityType.LEAD, {"name": "Sarah"})
        self.assertEqual(node.id, "lead_123")
        self.assertEqual(node.attributes["name"], "Sarah")
        self.assertIn("lead_123", self.service.nodes)

    def test_edge_creation(self):
        self.service.add_node("lead_123", EntityType.LEAD)
        self.service.add_node("budget_500", EntityType.CRITERION)
        edge = self.service.add_edge("lead_123", "budget_500", RelationType.HAS_BUDGET)
        self.assertIsNotNone(edge)
        self.assertEqual(edge.source, "lead_123")
        self.assertEqual(edge.target, "budget_500")

    def test_persistence(self):
        self.service.add_node("lead_123", EntityType.LEAD, {"p": 1})
        self.service.add_node("loc_austin", EntityType.LOCATION)
        self.service.add_edge("lead_123", "loc_austin", RelationType.INTERESTED_IN)
        
        # Reload
        new_service = KnowledgeGraphService(storage_path=self.test_path)
        self.assertIn("lead_123", new_service.nodes)
        self.assertEqual(len(new_service.edges), 1)

    def test_context_retrieval(self):
        # Setup complex graph
        # Lead -> Interested_In -> Austin -> Average_Price -> $600k
        self.service.add_node("Sarah", EntityType.LEAD)
        self.service.add_node("Austin", EntityType.LOCATION)
        self.service.add_node("HighPrice", EntityType.INSIGHT)
        
        self.service.add_edge("Sarah", "Austin", RelationType.INTERESTED_IN)
        self.service.add_edge("Austin", "HighPrice", RelationType.LOCATED_IN, {"avg_price": "$600k"})
        
        context = self.service.get_context("Sarah")
        self.assertTrue(any("Austin" in fact for fact in context["facts"]))
        self.assertTrue(any("HighPrice" in insight for insight in context["related_insights"]))
        
        prompt = self.service.get_context_prompt_snippet("Sarah")
        self.assertIn("Austin", prompt)
        self.assertIn("HighPrice", prompt)

    def test_consolidation_conflict(self):
        self.service.add_node("Sarah", EntityType.LEAD)
        self.service.add_node("B1", EntityType.CRITERION, {"val": 400})
        self.service.add_node("B2", EntityType.CRITERION, {"val": 500})
        
        self.service.add_edge("Sarah", "B1", RelationType.HAS_BUDGET)
        # Wait slightly or just assume append order is enough for this simple implementation
        self.service.add_edge("Sarah", "B2", RelationType.HAS_BUDGET)
        
        self.assertEqual(len(self.service.edges), 2)
        self.service.consolidate_memory()
        
        # Should only have one HAS_BUDGET edge now (the latest one)
        budget_edges = [e for e in self.service.edges if e.relation == RelationType.HAS_BUDGET]
        self.assertEqual(len(budget_edges), 1)
        self.assertEqual(budget_edges[0].target, "B2")

if __name__ == "__main__":
    unittest.main()
