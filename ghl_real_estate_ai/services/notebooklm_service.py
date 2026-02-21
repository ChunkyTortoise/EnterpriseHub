"""
NotebookLM Service
Provides EnterpriseHub integration with Google NotebookLM for research and knowledge base management.

Features:
- Real estate market research organization
- Property analysis documentation
- Client interaction insights
- Competitive intelligence gathering
- Training material generation
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from notebooklm import NotebookLMClient
except ImportError:
    NotebookLMClient = None
    logging.warning("notebooklm-py not installed. Run: pip install notebooklm-py")


logger = logging.getLogger(__name__)


class NotebookLMService:
    """
    Service for managing NotebookLM integration in EnterpriseHub.

    Use cases:
    - Market research notebooks for Rancho Cucamonga real estate
    - Property intelligence compilation
    - Client preference tracking
    - Competitive analysis documentation
    - Agent training materials
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NotebookLM service.

        Args:
            config: Optional configuration dictionary with:
                - credentials_path: Path to Google OAuth credentials
                - default_notebook_id: Default notebook for operations
                - cache_ttl: Cache TTL in seconds
        """
        self.config = config or {}
        self.client: Optional[NotebookLMClient] = None
        self._notebooks_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None

        if NotebookLMClient is None:
            logger.error("NotebookLM client unavailable - install notebooklm-py")
            return

        # Initialization is now async and happens on first use or explicitly

    async def _ensure_client(self):
        """Ensure the NotebookLM client is initialized."""
        if self.client is not None:
            return True

        try:
            # We use from_storage for simplicity in this integration
            client = await NotebookLMClient.from_storage()
            self.client = await client.__aenter__()
            logger.info("NotebookLM service initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NotebookLM client: {e}")
            return False

    def is_available(self) -> bool:
        """Check if NotebookLM service is available."""
        return self.client is not None

    # ========== Notebook Management ==========

    async def create_market_research_notebook(
        self, market_name: str = "Rancho Cucamonga", include_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a dedicated market research notebook.

        Args:
            market_name: Market/area name
            include_sources: Optional list of URLs to add as sources

        Returns:
            Notebook details including ID
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        title = f"{market_name} Real Estate Market Research"
        description = (
            f"Comprehensive market intelligence and research for {market_name}. "
            f"Includes market trends, property data, competitive analysis, and insights."
        )

        notebook = await self.client.notebooks.create(title=title)

        # Add initial sources if provided
        if include_sources:
            for url in include_sources:
                try:
                    await self.client.sources.add_url(notebook_id=notebook.id, url=url)
                except Exception as e:
                    logger.warning(f"Failed to add source {url}: {e}")

        return {
            "notebook_id": notebook.id,
            "title": notebook.title,
            "description": notebook.description,
            "created_at": str(notebook.created_at),
            "sources_added": len(include_sources) if include_sources else 0,
        }

    async def create_property_intelligence_notebook(
        self, property_address: str, mls_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a notebook for tracking intelligence on a specific property.

        Args:
            property_address: Full property address
            mls_id: Optional MLS listing ID

        Returns:
            Notebook details
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        title = f"Property Intelligence: {property_address}"
        if mls_id:
            title += f" (MLS #{mls_id})"

        description = (
            f"Comprehensive intelligence gathering for {property_address}. "
            f"Includes comparable sales, market positioning, buyer interest, and strategic insights."
        )

        notebook = await self.client.notebooks.create(title=title)

        return {
            "notebook_id": notebook.id,
            "title": notebook.title,
            "property_address": property_address,
            "mls_id": mls_id,
        }

    async def create_client_insights_notebook(
        self,
        client_name: str,
        client_type: str = "buyer",  # buyer, seller, investor
    ) -> Dict[str, Any]:
        """
        Create a notebook for tracking client preferences and insights.

        Args:
            client_name: Client name or ID
            client_type: Type of client (buyer, seller, investor)

        Returns:
            Notebook details
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        title = f"Client Insights: {client_name} ({client_type.title()})"
        description = (
            f"Intelligence and preference tracking for {client_type} client {client_name}. "
            f"Includes conversation insights, property preferences, and behavioral patterns."
        )

        notebook = await self.client.notebooks.create(title=title)

        return {
            "notebook_id": notebook.id,
            "title": notebook.title,
            "client_name": client_name,
            "client_type": client_type,
        }

    # ========== Source Management ==========

    async def add_conversation_transcript(
        self, notebook_id: str, transcript: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a conversation transcript as a source.

        Args:
            notebook_id: Target notebook ID
            transcript: Conversation text
            metadata: Optional metadata (date, participants, etc.)

        Returns:
            Source details
        """
        title = "Conversation Transcript"
        if metadata:
            date = metadata.get("date", "Unknown")
            participants = metadata.get("participants", "Unknown")
            title += f" - {date} ({participants})"

        # Format transcript with metadata
        formatted_content = transcript
        if metadata:
            header = "# Conversation Metadata\n"
            for key, value in metadata.items():
                header += f"- **{key.title()}**: {value}\n"
            header += "\n# Transcript\n\n"
            formatted_content = header + transcript

        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        source = await self.client.sources.add_text(notebook_id=notebook_id, text=formatted_content, title=title)

        return {"source_id": source.id, "title": title, "type": "transcript"}

    async def add_market_report(
        self, notebook_id: str, report_url: str, report_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a market report URL as a source.

        Args:
            notebook_id: Target notebook ID
            report_url: URL to market report
            report_title: Optional custom title

        Returns:
            Source details
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        source = await self.client.sources.add_url(notebook_id=notebook_id, url=report_url)

        return {"source_id": source.id, "url": report_url, "type": "market_report"}

    async def add_property_listing_data(self, notebook_id: str, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add property listing data as a structured source.

        Args:
            notebook_id: Target notebook ID
            listing_data: Property listing dictionary

        Returns:
            Source details
        """
        # Format listing data as markdown
        content = "# Property Listing\n\n"

        # Core details
        if "address" in listing_data:
            content += f"**Address**: {listing_data['address']}\n"
        if "price" in listing_data:
            content += f"**Price**: ${listing_data['price']:,}\n"
        if "beds" in listing_data:
            content += f"**Bedrooms**: {listing_data['beds']}\n"
        if "baths" in listing_data:
            content += f"**Bathrooms**: {listing_data['baths']}\n"
        if "sqft" in listing_data:
            content += f"**Square Feet**: {listing_data['sqft']:,}\n"

        content += "\n## Details\n\n"
        for key, value in listing_data.items():
            if key not in ["address", "price", "beds", "baths", "sqft"]:
                content += f"- **{key.title()}**: {value}\n"

        title = f"Listing: {listing_data.get('address', 'Unknown Address')}"

        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        source = await self.client.sources.add_text(notebook_id=notebook_id, text=content, title=title)

        return {"source_id": source.id, "title": title, "type": "property_listing"}

    # ========== Query & Research ==========

    async def research_question(
        self, notebook_id: str, question: str, include_citations: bool = True
    ) -> Dict[str, Any]:
        """
        Research a question using notebook sources.

        Args:
            notebook_id: Notebook to query
            question: Research question
            include_citations: Include source citations

        Returns:
            Answer with optional citations
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        result = await self.client.chat.ask(notebook_id=notebook_id, query=question)

        return {
            "question": question,
            "answer": result.answer,
            "citations": [str(c) for c in result.references] if include_citations else [],
            "notebook_id": notebook_id,
        }

    async def generate_market_insights(
        self, notebook_id: str, focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive market insights from notebook sources.

        Args:
            notebook_id: Market research notebook ID
            focus_areas: Optional specific areas to focus on

        Returns:
            Market insights report
        """
        # Build query based on focus areas
        if focus_areas:
            areas = ", ".join(focus_areas)
            query = f"Provide comprehensive insights on {areas} based on all available market data."
        else:
            query = (
                "Provide a comprehensive market analysis including trends, "
                "pricing patterns, inventory levels, and key insights."
            )

        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        result = await self.client.chat.ask(notebook_id=notebook_id, query=query)

        return {
            "insights": result.answer,
            "sources": [str(c) for c in result.references],
            "focus_areas": focus_areas or ["general market analysis"],
            "generated_at": datetime.utcnow().isoformat(),
        }

    async def analyze_client_preferences(
        self, notebook_id: str, analysis_type: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Analyze client preferences from conversation transcripts and interactions.

        Args:
            notebook_id: Client insights notebook ID
            analysis_type: Type of analysis (comprehensive, quick, specific)

        Returns:
            Preference analysis
        """
        if analysis_type == "comprehensive":
            query = (
                "Analyze all client interactions to identify: "
                "1) Property preferences (style, size, location, features), "
                "2) Budget and financial considerations, "
                "3) Timeline and urgency, "
                "4) Decision-making patterns, "
                "5) Concerns and objections"
            )
        elif analysis_type == "quick":
            query = "Summarize the client's top 3 property preferences and primary concerns."
        else:
            query = f"Analyze the client's {analysis_type} based on all interactions."

        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        result = await self.client.chat.ask(notebook_id=notebook_id, query=query)

        return {
            "analysis": result.answer,
            "analysis_type": analysis_type,
            "sources": [str(c) for c in result.references],
        }

    # ========== Content Generation ==========

    async def generate_training_material(
        self,
        notebook_id: str,
        topic: str,
        format: str = "study_guide",  # study_guide, quiz, flashcards
    ) -> Dict[str, Any]:
        """
        Generate training materials from notebook content.

        Args:
            notebook_id: Source notebook ID
            topic: Training topic
            format: Output format

        Returns:
            Generated training material
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        guide = await self.client.artifacts.get_guide(notebook_id=notebook_id)

        return {"topic": topic, "format": format, "content": str(guide), "notebook_id": notebook_id}

    async def generate_audio_briefing(self, notebook_id: str, duration_minutes: int = 10) -> Dict[str, Any]:
        """
        Generate an AI audio briefing (podcast-style) from notebook content.

        Args:
            notebook_id: Source notebook ID
            duration_minutes: Approximate duration

        Returns:
            Audio briefing details with URL
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        audio = await self.client.artifacts.generate_audio_overview(notebook_id=notebook_id)

        return {
            "audio_task_id": getattr(audio, "task_id", "unknown"),
            "notebook_id": notebook_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ========== List & Discovery ==========

    async def list_notebooks(self, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List available notebooks with optional category filter.

        Args:
            category: Optional category filter (market_research, property_intelligence, client_insights)
            limit: Maximum notebooks to return

        Returns:
            List of notebook summaries
        """
        if not await self._ensure_client():
            raise RuntimeError("NotebookLM client not initialized")

        notebooks = await self.client.notebooks.list()

        # Filter by category if specified
        if category:
            category_keywords = {
                "market_research": ["market", "research", "analysis"],
                "property_intelligence": ["property", "listing", "intelligence"],
                "client_insights": ["client", "insights", "buyer", "seller"],
            }
            keywords = category_keywords.get(category, [])
            if keywords:
                notebooks = [nb for nb in notebooks if any(kw.lower() in nb.title.lower() for kw in keywords)]

        return [
            {
                "id": nb.id,
                "title": nb.title,
                "description": nb.description,
                "source_count": nb.source_count,
                "created_at": str(nb.created_at),
            }
            for nb in notebooks
        ]


# ========== Factory Functions ==========


def create_notebooklm_service(config: Optional[Dict[str, Any]] = None) -> NotebookLMService:
    """
    Factory function to create NotebookLM service instance.

    Args:
        config: Optional configuration

    Returns:
        Configured NotebookLMService instance
    """
    return NotebookLMService(config=config)
