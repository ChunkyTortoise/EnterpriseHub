"""
Graphiti Memory Manager.
Handles interaction with the Graphiti knowledge graph for the Real Estate AI.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import ENTITY_LEAD, RELATION_TYPES

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


class LocalMemoryManager:
    """Fallback memory manager using local JSON storage."""

    def __init__(self, storage_path: str = "data/agent_memory.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.memory, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save local memory: {e}")

    async def save_interaction(self, lead_id: str, text: str, role: str = "user"):
        if lead_id not in self.memory:
            self.memory[lead_id] = []
        self.memory[lead_id].append({"role": role, "text": text, "timestamp": time.time()})
        self._save()

    async def retrieve_context(self, lead_id: str) -> str:
        interactions = self.memory.get(lead_id, [])
        if not interactions:
            return ""

        # Return last 5 interactions as context
        recent = interactions[-5:]
        formatted = "\n".join([f"- {i['role']}: {i['text']}" for i in recent])
        return f"## Recent Interactions (Local Memory)\n{formatted}"


class GraphitiMemoryManager:
    def __init__(self):
        self.enabled = False
        self.client = None
        self.fallback = LocalMemoryManager()

        if Graphiti is None:
            logging.warning("graphiti_core not found. Using LocalMemoryManager fallback.")
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
            await self.fallback.save_interaction(lead_id, text, role)
            return

        # Define the source/subject of the memory
        source_node = {"type": ENTITY_LEAD, "name": lead_id, "id": lead_id}

        try:
            # add_episode triggers the LLM extraction logic within Graphiti
            await self.client.add_episode(
                name=f"Interaction with {lead_id}",
                description=text,
                source=source_node,
                episode_type=EpisodeType.dialogue if role == "user" else EpisodeType.thought,
            )
            logging.info(f"Saved interaction for lead {lead_id} to Graphiti.")
        except Exception as e:
            logging.error(f"Error saving to Graphiti: {e}")
            await self.fallback.save_interaction(lead_id, text, role)

    async def retrieve_context(self, lead_id: str) -> str:
        """
        Retrieves relevant context for a lead using the RAG strategy:
        1. Identity Resolution (Match Lead)
        2. Graph Walk (1-Hop & 2-Hop)
        3. Format for Injection
        """
        if not self.enabled or not self.client:
            return await self.fallback.retrieve_context(lead_id)

        context_str = ""
        try:
            # RAG Strategy Implementation
            # 1. Identity Resolution & 2. Graph Walk
            # Using Graphiti's search capability which usually performs semantic + graph search

            results = await self.client.search(
                query=f"Facts about {lead_id}",
                center_node_id=lead_id,  # If supported by API
                max_distance=2,  # 2-Hop
            )

            # Format the results
            if results:
                formatted_facts = []
                for result in results:
                    # Assuming result is a string or object with text
                    # Adjust based on actual Graphiti search result structure
                    formatted_facts.append(f"- {str(result)}")

                context_str = "## Relevant Knowledge (Graphiti Memory)\n" + "\n".join(formatted_facts)

            # If graph context is empty, try fallback
            if not context_str:
                context_str = await self.fallback.retrieve_context(lead_id)

        except Exception as e:
            logging.error(f"Error retrieving context from Graphiti: {e}")
            context_str = await self.fallback.retrieve_context(lead_id)

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


from ghl_real_estate_ai.core.llm_client import LLMClient


class MemorySynthesizer:
    """
    Condenses old interaction nodes into 'Agent Dossiers' to prevent context bloat.
    """

    def __init__(self, fallback_manager: LocalMemoryManager):
        self.fallback = fallback_manager
        self.llm = LLMClient()

    async def synthesize_dossier(self, lead_id: str) -> str:
        """
        Creates a concise dossier (summary) of a lead's history.
        """
        interactions = self.fallback.memory.get(lead_id, [])
        if not interactions:
            return "No history available for this lead."

        # If there's already a dossier, we might want to update it
        # For now, we synthesize from all available interactions

        history_text = "\n".join([f"{i['role']}: {i['text']}" for i in interactions])

        prompt = f"""
        You are a Memory Synthesis Engine. 
        Summarize the following interaction history with lead {lead_id} into a concise 'Agent Dossier'.
        Focus on:
        - Key needs and preferences.
        - Objections raised.
        - Current status/stage in the funnel.
        - Next best action.
        
        HISTORY:
        {history_text}
        
        Keep the summary under 150 words.
        """

        try:
            response = await self.llm.agenerate(prompt=prompt, model="gemini-2.0-flash", temperature=0.1)
            dossier = response.content

            # Save dossier back to local memory as a special entry
            if "dossiers" not in self.fallback.memory:
                self.fallback.memory["dossiers"] = {}

            self.fallback.memory["dossiers"][lead_id] = {
                "content": dossier,
                "synthesized_at": time.time(),
                "interaction_count": len(interactions),
            }
            self.fallback._save()

            return dossier
        except Exception as e:
            logging.error(f"Memory synthesis failed for {lead_id}: {e}")
            return "Error synthesizing dossier."

    async def synthesize_market_trends(self, market_name: str = "Global") -> str:
        """
        Aggregates dossiers from multiple leads to generate a Market Heatmap summary.
        """
        dossiers = self.fallback.memory.get("dossiers", {})
        if not dossiers:
            return f"Insufficient data for {market_name} market trends."

        combined_dossiers = "\n---\n".join([f"Lead Dossier: {d['content']}" for d in dossiers.values()])

        prompt = f"""
        You are a Market Intelligence Analyst. 
        Analyze the following lead dossiers for the '{market_name}' market and generate a 'Market Heatmap' summary.
        
        IDENTIFIED DOSSIERS:
        {combined_dossiers}
        
        Focus on:
        - Emerging trends across multiple leads.
        - Common objections or friction points.
        - Sentiment heatmap (overall market mood).
        - Strategic recommendations for the swarm.
        
        Keep the summary under 300 words.
        """

        try:
            response = await self.llm.agenerate(prompt=prompt, model="gemini-2.0-flash", temperature=0.2)
            return response.content
        except Exception as e:
            logging.error(f"Market trend synthesis failed: {e}")
            return "Error synthesizing market trends."


# Global instance
memory_manager = GraphitiMemoryManager()
memory_synthesizer = MemorySynthesizer(memory_manager.fallback)
