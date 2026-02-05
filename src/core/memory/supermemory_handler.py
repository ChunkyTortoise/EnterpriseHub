import os
from typing import Optional, Dict, List, Any
import logging
from supermemory import AsyncSupermemory

logger = logging.getLogger(__name__)

class SupermemoryHandler:
    """
    Handler for interacting with the Supermemory AI API.
    Provides long-term semantic memory for AI agents.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SUPERMEMORY_API_KEY")
        
        if not self.api_key:
            logger.warning("SUPERMEMORY_API_KEY not found in environment. Supermemory features will be disabled.")
            self.client = None
        else:
            # The SDK handles the base URL, but we can override it if needed
            self.client = AsyncSupermemory(api_key=self.api_key)

    async def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None, container_tag: str = "EnterpriseHub") -> Dict[str, Any]:
        """Adds a new memory to the semantic graph."""
        if not self.client:
            return {"error": "API key missing or client not initialized"}

        try:
            response = await self.client.memories.add(
                content=content,
                container_tag=container_tag,
                metadata=metadata or {}
            )
            # Support both Pydantic models (SDK v3+) and direct dicts
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            return response if isinstance(response, dict) else {"message": str(response)}
        except Exception as e:
            logger.error(f"Error adding memory: {e}")
            return {"error": str(e)}

    async def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Searches for relevant memories using semantic similarity."""
        if not self.client:
            return []

        try:
            searching = await self.client.search.execute(
                q=query,
            )
            results = []
            if hasattr(searching, 'results'):
                for res in searching.results:
                    if hasattr(res, 'model_dump'):
                        results.append(res.model_dump())
                    else:
                        results.append(res if isinstance(res, dict) else {"content": str(res)})
            return results[:limit]
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return []

    async def get_user_profile(self, user_id: str = None, container_tag: str = "EnterpriseHub") -> Dict[str, Any]:
        """Retrieves and evolves the user profile based on accumulated memories."""
        if not self.client:
            return {}

        try:
            # SDK v3 uses client.profile() to get the current profile
            # It requires a container_tag
            response = await self.client.profile(container_tag=container_tag)
            if hasattr(response, 'model_dump'):
                return response.model_dump()
            return response if isinstance(response, dict) else {"profile": str(response)}
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}

    async def delete_memory(self, memory_id: str) -> bool:
        """Deletes a specific memory by ID."""
        if not self.client:
            return False

        try:
            # SDK uses id for deletion
            await self.client.memories.delete(id=memory_id)
            return True
        except Exception as e:
            logger.error(f"Error deleting memory: {e}")
            return False
