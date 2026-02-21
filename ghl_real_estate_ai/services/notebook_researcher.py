"""
Notebook Researcher Service - NotebookLM-style grounded intelligence.

Provides functionality similar to NotebookLM, allowing users to upload
multiple documents and perform grounded research across them using
Gemini's large context window.
"""

import os
from typing import Any, Dict, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class NotebookResearcher:
    """
    Service for grounded research across multiple documents.
    Simulates NotebookLM functionality using Gemini 1.5 Pro.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Notebook researcher.
        """
        self.llm = LLMClient(provider=LLMProvider.GEMINI, api_key=api_key or settings.google_api_key)
        self.enabled = self.llm.is_available()
        if not self.enabled:
            logger.warning("NotebookResearcher disabled: GOOGLE_API_KEY not set")

        # In-memory notebook state (for demo/session purposes)
        self.notebooks: Dict[str, Dict[str, Any]] = {}

    def create_notebook(self, name: str, description: Optional[str] = None) -> str:
        """Create a new research notebook."""
        notebook_id = f"nb_{os.urandom(4).hex()}"
        self.notebooks[notebook_id] = {"name": name, "description": description, "sources": [], "cache_id": None}
        logger.info(f"Created notebook: {name} ({notebook_id})")
        return notebook_id

    def add_source(self, notebook_id: str, source_name: str, content: str):
        """Add a document source to the notebook."""
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook {notebook_id} not found")

        self.notebooks[notebook_id]["sources"].append({"name": source_name, "content": content})
        # Reset cache if content changed
        self.notebooks[notebook_id]["cache_id"] = None
        logger.info(f"Added source '{source_name}' to notebook {notebook_id}")

    async def query_notebook(self, notebook_id: str, query: str) -> str:
        """
        Query the notebook for grounded information.
        Uses context caching for efficiency if available.
        """
        if notebook_id not in self.notebooks:
            return "Error: Notebook not found."

        notebook = self.notebooks[notebook_id]
        sources = notebook["sources"]

        if not sources:
            return "This notebook is empty. Please add sources first."

        # Aggregate all content
        full_content = "\n\n".join([f"--- SOURCE: {s['name']} ---\n{s['content']}" for s in sources])

        system_prompt = (
            "You are an expert research assistant specialized in grounded analysis. "
            "Your answers must be strictly based on the provided source materials. "
            "If the information is not in the sources, state that clearly. "
            "Cite your sources using [Source Name] format."
        )

        # Check if we should cache the content (Gemini caching requirement: > 32,768 tokens)
        # Using character count as a rough heuristic (1 token ~= 4 chars)
        if len(full_content) > 100000 and not notebook["cache_id"]:
            try:
                cache_name = self.llm.create_context_cache(
                    content=full_content, display_name=f"Notebook_{notebook['name']}", system_instruction=system_prompt
                )
                notebook["cache_id"] = cache_name
                logger.info(f"Cached notebook content: {cache_name}")
            except Exception as e:
                logger.warning(f"Failed to create context cache: {e}")

        prompt = f"Using the provided source documents, please answer: {query}"

        try:
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt=system_prompt,
                cached_content=notebook["cache_id"],
                # If not cached, we pass history for grounding context
                history=[
                    {"role": "user", "content": f"Here are my source documents:\n\n{full_content}"},
                    {
                        "role": "assistant",
                        "content": "I have received the documents and am ready to answer your questions based on them.",
                    },
                ]
                if not notebook["cache_id"]
                else None,
                max_tokens=4000,
            )
            return response.content
        except Exception as e:
            logger.error(f"Notebook query failed: {e}")
            return f"Error during research: {str(e)}"

    async def generate_briefing_doc(self, notebook_id: str) -> str:
        """Generate an executive briefing from all sources in the notebook."""
        query = "Generate a comprehensive executive briefing that synthesizes all information in this notebook. Highlight key trends, risks, and opportunities."
        return await self.query_notebook(notebook_id, query)


def get_notebook_researcher() -> NotebookResearcher:
    """Get global NotebookResearcher instance."""
    return NotebookResearcher()
