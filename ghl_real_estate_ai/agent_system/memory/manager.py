"""
Graphiti Memory Manager.
Handles interaction with the Graphiti knowledge graph for the Real Estate AI.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from .schema import ENTITY_LEAD, RELATION_TYPES
import json

# Try to import graphiti_core and drivers
try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    # Attempt to import a driver - defaulting to what auto-claude uses if available
    # This might need adjustment based on installed packages (e.g. neo4j vs redis)
    try:
        from graphiti_core.driver.falkordb_driver import FalkorDriver
        DEFAULT_DRIVER_CLASS = FalkorDriver
    except ImportError:
        # Fallback or other driver
        try:
            from graphiti_core.driver.neo4j_driver import Neo4jDriver
            DEFAULT_DRIVER_CLASS = Neo4jDriver
        except ImportError:
            DEFAULT_DRIVER_CLASS = None

except ImportError:
    Graphiti = None
    EpisodeType = None
    DEFAULT_DRIVER_CLASS = None
    logging.warning("graphiti_core not found. Memory features will be disabled.")

class GraphitiMemoryManager:
    def __init__(self):
        self.enabled = False
        self.client = None
        
        if Graphiti is None:
            return

        # Configuration from Env
        self.host = os.getenv("GRAPHITI_HOST", "localhost")
        self.port = int(os.getenv("GRAPHITI_PORT", 6379))
        self.user = os.getenv("GRAPHITI_USER", None)
        self.password = os.getenv("GRAPHITI_PASSWORD", None)
        self.driver_type = os.getenv("GRAPHITI_DRIVER", "falkordb").lower()

        try:
            if DEFAULT_DRIVER_CLASS:
                # Initialize Driver
                # Simplified initialization logic - adjust arguments as needed for specific drivers
                if self.driver_type == "neo4j":
                    from graphiti_core.driver.neo4j_driver import Neo4jDriver
                    driver = Neo4jDriver(uri=f"bolt://{self.host}:{self.port}", auth=(self.user, self.password))
                else:
                    # Default to FalkorDB
                    from graphiti_core.driver.falkordb_driver import FalkorDriver
                    driver = FalkorDriver(host=self.host, port=self.port, password=self.password)

                self.client = Graphiti(graph_driver=driver)
                self.enabled = True
                logging.info(f"Graphiti Memory Manager initialized with {self.driver_type}.")
            else:
                logging.warning("No suitable Graphiti driver found.")
        except Exception as e:
            logging.error(f"Failed to initialize Graphiti client: {e}")
            self.enabled = False

    async def save_interaction(self, lead_id: str, text: str, role: str = "user"):
        """
        Saves an interaction (episode) to the graph.
        Graphiti will extract facts based on the schema.
        """
        if not self.enabled or not self.client:
            return

        # Define the source/subject of the memory
        source_node = {"type": ENTITY_LEAD, "name": lead_id, "id": lead_id}
        
        try:
            # add_episode triggers the LLM extraction logic within Graphiti
            await self.client.add_episode(
                name=f"Interaction with {lead_id}",
                description=text,
                source=source_node,
                episode_type=EpisodeType.dialogue if role == "user" else EpisodeType.thought
            )
            logging.info(f"Saved interaction for lead {lead_id} to Graphiti.")
        except Exception as e:
            logging.error(f"Error saving to Graphiti: {e}")

    async def retrieve_context(self, lead_id: str) -> str:
        """
        Retrieves relevant context for a lead using the RAG strategy:
        1. Identity Resolution (Match Lead)
        2. Graph Walk (1-Hop & 2-Hop)
        3. Format for Injection
        """
        if not self.enabled or not self.client:
            return ""

        context_str = ""
        try:
            # RAG Strategy Implementation
            # 1. Identity Resolution & 2. Graph Walk
            # Using Graphiti's search capability which usually performs semantic + graph search
            
            results = await self.client.search(
                query=f"Facts about {lead_id}",
                center_node_id=lead_id, # If supported by API
                max_distance=2 # 2-Hop
            )
            
            # Format the results
            if results:
                formatted_facts = []
                for result in results:
                    # Assuming result is a string or object with text
                    # Adjust based on actual Graphiti search result structure
                    formatted_facts.append(f"- {str(result)}")
                
                context_str = "## Relevant Knowledge (Graphiti Memory)\n" + "\n".join(formatted_facts)
            
        except Exception as e:
            logging.error(f"Error retrieving context from Graphiti: {e}")

        return context_str

    async def consolidate_memory(self):
        """
        Triggers memory consolidation (The 'Dream' Cycle).
        """
        if not self.enabled or not self.client:
            return

        try:
            # Graphiti's build_indices_and_constraints is a maintenance task
            await self.client.build_indices_and_constraints()
            logging.info("Graphiti indices and constraints rebuilt.")
            
            # Future: Call specifically designed consolidation methods if available in Graphiti Core
            # e.g. clustering, conflict resolution algorithms
            
        except Exception as e:
            logging.error(f"Error consolidating memory: {e}")

# Global instance
memory_manager = GraphitiMemoryManager()
