"""
Demo: The "Graphiti" Agent Brain in Action
===========================================
This script demonstrates how the Knowledge Graph captures real estate signal
and provides intelligent context injection for the Agent.
"""

from services.knowledge_graph_service import KnowledgeGraphService, EntityType, RelationType
import json
import os

def run_demo():
    # 1. Initialize with a demo storage path
    demo_db = "data/memory/demo_graph.json"
    if os.path.exists(demo_db):
        os.remove(demo_db)
    
    graph = KnowledgeGraphService(storage_path=demo_db)
    
    print("\n--- 🧠 STEP 1: CAPTURING SIGNAL (Evolving Brain) ---")
    
    # Define Entities
    graph.add_node("Sarah Jones", EntityType.LEAD, {"phone": "555-0199"})
    graph.add_node("$450k", EntityType.CRITERION)
    graph.add_node("HOA", EntityType.CRITERION)
    graph.add_node("June/Baby", EntityType.CRITERION)
    graph.add_node("123 Maple St", EntityType.PROPERTY, {"price": "$430k"})
    graph.add_node("Round Rock", EntityType.LOCATION)
    
    # Store Facts (Episodic Memory)
    print("Saving Hard Fact: Budget is $450k")
    graph.add_edge("Sarah Jones", "$450k", RelationType.HAS_BUDGET)
    
    print("Saving Strong Opinion: Hates HOAs")
    graph.add_edge("Sarah Jones", "HOA", RelationType.DISLIKES)
    
    print("Saving Life Event: Baby in June")
    graph.add_edge("Sarah Jones", "June/Baby", RelationType.HAS_TIMELINE)
    
    print("Saving Decision: Offering on 123 Maple")
    graph.add_edge("Sarah Jones", "123 Maple St", RelationType.OFFERING_ON)
    
    # Connect World Facts (Semantic Memory)
    graph.add_edge("123 Maple St", "Round Rock", RelationType.LOCATED_IN)
    graph.add_node("High Growth", EntityType.INSIGHT)
    graph.add_edge("Round Rock", "High Growth", RelationType.LOCATED_IN)
    
    print("\n--- 🔍 STEP 2: CONTEXT INJECTION (RAG Retrieval) ---")
    print("Scenario: Sarah messages the agent. Agent needs context.")
    
    context_snippet = graph.get_context_prompt_snippet("Sarah Jones")
    print("\n[Generated System Prompt Fragment]:")
    print("--------------------------------------------------")
    print(context_snippet)
    print("--------------------------------------------------")
    
    print("\n--- 😴 STEP 3: MEMORY CONSOLIDATION (The Dream Cycle) ---")
    # Simulate a new budget update
    print("Update: Sarah says budget is now $500k")
    graph.add_node("$500k", EntityType.CRITERION)
    graph.add_edge("Sarah Jones", "$500k", RelationType.HAS_BUDGET)
    
    print("Running Consolidation to resolve conflicts...")
    graph.consolidate_memory()
    
    new_snippet = graph.get_context_prompt_snippet("Sarah Jones")
    print("\n[Post-Consolidation Prompt Fragment]:")
    print("(Notice $450k is archived/replaced by $500k)")
    print("--------------------------------------------------")
    print(new_snippet)
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_demo()
