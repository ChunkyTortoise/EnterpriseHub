"""Unified retriever for multi-modal search across text, images, and structured data.

This module provides the UnifiedRetriever class that orchestrates:
- Text retrieval using dense embeddings
- Image retrieval using CLIP embeddings
- Structured data retrieval (tables, CSV, JSON)
- Intelligent fusion of results from all modalities
- Query routing based on content type detection

Features:
- Automatic modality detection from queries
- Weighted fusion of multi-modal results
- Async parallel search across modalities
- Integration with AdvancedHybridSearcher
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from src.core.exceptions import RetrievalError
from src.core.types import SearchResult
from src.retrieval.advanced_hybrid_searcher import (
    AdvancedHybridSearcher,
    AdvancedSearchConfig,
)
from src.retrieval.multimodal_fusion import ModalityFusionConfig, MultiModalFusion
from src.multimodal.image_retriever import ImageRetriever, ImageRetrieverConfig
from src.multimodal.structured_retriever import (
    StructuredQuery,
    StructuredRetriever,
    StructuredRetrieverConfig,
)

logger = logging.getLogger(__name__)


class QueryModality(Enum):
    """Detected modality of a query."""

    TEXT = "text"
    IMAGE = "image"
    STRUCTURED = "structured"
    MULTI = "multi"


@dataclass
class UnifiedRetrieverConfig:
    """Configuration for unified multi-modal retriever.

    Attributes:
        # Component configs
        text_config: Configuration for text retrieval
        image_config: Configuration for image retrieval
        structured_config: Configuration for structured retrieval
        fusion_config: Configuration for result fusion

        # Behavior settings
        enable_modality_detection: Auto-detect query modality
        default_modality: Default modality if detection fails
        parallel_search: Run searches in parallel
        max_total_results: Maximum total results to return
        min_modality_score: Minimum score to include modality results

        # Weights for intelligent routing
        text_weight: Weight for text results in fusion
        image_weight: Weight for image results in fusion
        structured_weight: Weight for structured results in fusion
    """

    # Component configurations
    text_config: Optional[AdvancedSearchConfig] = None
    image_config: Optional[ImageRetrieverConfig] = None
    structured_config: Optional[StructuredRetrieverConfig] = None
    fusion_config: Optional[ModalityFusionConfig] = None

    # Behavior settings
    enable_modality_detection: bool = True
    default_modality: QueryModality = QueryModality.TEXT
    parallel_search: bool = True
    max_total_results: int = 20
    min_modality_score: float = 0.1

    # Fusion weights
    text_weight: float = 0.4
    image_weight: float = 0.35
    structured_weight: float = 0.25


@dataclass
class UnifiedSearchResult:
    """Result from unified multi-modal search.

    Attributes:
        results: Combined and ranked search results
        modality_breakdown: Results grouped by modality
        detected_modality: Detected query modality
        search_time_ms: Total search time in milliseconds
        modality_weights: Weights used for each modality
    """

    results: List[SearchResult]
    modality_breakdown: Dict[str, List[SearchResult]]
    detected_modality: QueryModality
    search_time_ms: float
    modality_weights: Dict[str, float]


class UnifiedRetriever:
    """Unified retriever for multi-modal search.

    Orchestrates search across text, image, and structured data modalities,
    with intelligent query routing and result fusion.

    Example:
        ```python
        config = UnifiedRetrieverConfig(
            text_config=AdvancedSearchConfig(enable_hyde=True),
            image_config=ImageRetrieverConfig(collection_name="images"),
            structured_config=StructuredRetrieverConfig(collection_name="data"),
        )

        retriever = UnifiedRetriever(config)
        await retriever.initialize()

        # Search with automatic modality detection
        result = await retriever.search("red sports cars")

        # Search specific modality
        result = await retriever.search(
            "product sales in Q4",
            modality=QueryModality.STRUCTURED
        )

        # Image-based search
        result = await retriever.search_by_image("query_image.png")

        await retriever.close()
        ```
    """

    def __init__(self, config: Optional[UnifiedRetrieverConfig] = None) -> None:
        """Initialize unified retriever.

        Args:
            config: Unified retriever configuration
        """
        self.config = config or UnifiedRetrieverConfig()

        # Component retrievers
        self._text_retriever: Optional[AdvancedHybridSearcher] = None
        self._image_retriever: Optional[ImageRetriever] = None
        self._structured_retriever: Optional[StructuredRetriever] = None

        # Fusion handler
        self._fusion: Optional[MultiModalFusion] = None

        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all component retrievers.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        init_tasks = []

        # Initialize text retriever
        try:
            text_config = self.config.text_config or AdvancedSearchConfig()
            self._text_retriever = AdvancedHybridSearcher(text_config)
            init_tasks.append(self._text_retriever.initialize())
            logger.info("Text retriever initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize text retriever: {e}")
            self._text_retriever = None

        # Initialize image retriever
        try:
            image_config = self.config.image_config or ImageRetrieverConfig()
            self._image_retriever = ImageRetriever(image_config)
            init_tasks.append(self._image_retriever.initialize())
            logger.info("Image retriever initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize image retriever: {e}")
            self._image_retriever = None

        # Initialize structured retriever
        try:
            structured_config = (
                self.config.structured_config or StructuredRetrieverConfig()
            )
            self._structured_retriever = StructuredRetriever(structured_config)
            init_tasks.append(self._structured_retriever.initialize())
            logger.info("Structured retriever initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize structured retriever: {e}")
            self._structured_retriever = None

        # Run initializations
        if init_tasks:
            await asyncio.gather(*init_tasks, return_exceptions=True)

        # Initialize fusion
        fusion_config = self.config.fusion_config or ModalityFusionConfig(
            text_weight=self.config.text_weight,
            image_weight=self.config.image_weight,
            structured_weight=self.config.structured_weight,
            max_results=self.config.max_total_results,
        )
        self._fusion = MultiModalFusion(fusion_config)

        self._initialized = True
        logger.info("Unified retriever initialized")

    async def close(self) -> None:
        """Release resources and close all component retrievers."""
        close_tasks = []

        if self._text_retriever:
            close_tasks.append(self._text_retriever.close())
            self._text_retriever = None

        if self._image_retriever:
            close_tasks.append(self._image_retriever.close())
            self._image_retriever = None

        if self._structured_retriever:
            close_tasks.append(self._structured_retriever.close())
            self._structured_retriever = None

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self._fusion = None
        self._initialized = False
        logger.info("Unified retriever closed")

    def _detect_modality(self, query: str) -> QueryModality:
        """Detect the modality of a query.

        Analyzes query content to determine which modality
        is most likely to return relevant results.

        Args:
            query: Search query

        Returns:
            Detected query modality
        """
        query_lower = query.lower()

        # Image indicators
        image_keywords = [
            "image", "picture", "photo", "visual", "look like",
            "appearance", "color", "shape", "diagram", "chart",
            "graph", "illustration", "drawing", "screenshot"
        ]

        # Structured data indicators
        structured_keywords = [
            "table", "csv", "data", "statistics", "metrics",
            "sales", "revenue", "count", "average", "sum",
            "report", "spreadsheet", "excel", "json", "database"
        ]

        image_score = sum(1 for kw in image_keywords if kw in query_lower)
        structured_score = sum(1 for kw in structured_keywords if kw in query_lower)

        # Determine modality
        if image_score > 0 and structured_score > 0:
            return QueryModality.MULTI
        elif image_score > 0:
            return QueryModality.IMAGE
        elif structured_score > 0:
            return QueryModality.STRUCTURED
        else:
            return QueryModality.TEXT

    async def search(
        self,
        query: str,
        modality: Optional[QueryModality] = None,
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> UnifiedSearchResult:
        """Execute unified multi-modal search.

        Args:
            query: Search query
            modality: Force specific modality (or auto-detect if None)
            top_k: Number of results per modality
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            Unified search result with fused results

        Raises:
            RetrievalError: If search fails
        """
        import time

        self._ensure_initialized()
        start_time = time.time()

        # Detect modality if not specified
        if modality is None and self.config.enable_modality_detection:
            modality = self._detect_modality(query)
        elif modality is None:
            modality = self.config.default_modality

        logger.info(f"Searching with modality: {modality.value}")

        # Determine which retrievers to use
        search_text = modality in (QueryModality.TEXT, QueryModality.MULTI)
        search_image = modality in (QueryModality.IMAGE, QueryModality.MULTI)
        search_structured = modality in (QueryModality.STRUCTURED, QueryModality.MULTI)

        # Execute searches
        if self.config.parallel_search:
            text_results, image_results, structured_results = await self._search_parallel(
                query=query,
                search_text=search_text,
                search_image=search_image,
                search_structured=search_structured,
                top_k=top_k,
                threshold=threshold,
                filters=filters,
            )
        else:
            text_results, image_results, structured_results = await self._search_sequential(
                query=query,
                search_text=search_text,
                search_image=search_image,
                search_structured=search_structured,
                top_k=top_k,
                threshold=threshold,
                filters=filters,
            )

        # Fuse results
        fused_results = self._fusion.fuse_modalities(
            text_results=text_results,
            image_results=image_results,
            structured_results=structured_results,
        )

        # Apply final limit
        fused_results = fused_results[: self.config.max_total_results]

        elapsed_ms = (time.time() - start_time) * 1000

        return UnifiedSearchResult(
            results=fused_results,
            modality_breakdown={
                "text": text_results or [],
                "image": image_results or [],
                "structured": structured_results or [],
            },
            detected_modality=modality,
            search_time_ms=elapsed_ms,
            modality_weights={
                "text": self.config.text_weight,
                "image": self.config.image_weight,
                "structured": self.config.structured_weight,
            },
        )

    async def _search_parallel(
        self,
        query: str,
        search_text: bool,
        search_image: bool,
        search_structured: bool,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]],
    ) -> tuple[List[SearchResult], List[SearchResult], List[SearchResult]]:
        """Execute searches in parallel.

        Args:
            query: Search query
            search_text: Whether to search text
            search_image: Whether to search images
            search_structured: Whether to search structured data
            top_k: Results per modality
            threshold: Minimum threshold
            filters: Metadata filters

        Returns:
            Tuple of (text_results, image_results, structured_results)
        """
        tasks = []

        if search_text and self._text_retriever:
            tasks.append(
                self._text_retriever.search(query, top_k=top_k)
            )
        else:
            tasks.append(asyncio.sleep(0))

        if search_image and self._image_retriever:
            tasks.append(
                self._image_retriever.search_by_text(query, top_k=top_k, threshold=threshold)
            )
        else:
            tasks.append(asyncio.sleep(0))

        if search_structured and self._structured_retriever:
            tasks.append(
                self._structured_retriever.semantic_search(query, top_k=top_k, threshold=threshold)
            )
        else:
            tasks.append(asyncio.sleep(0))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        text_results = results[0] if search_text and self._text_retriever else []
        image_results = results[1] if search_image and self._image_retriever else []
        structured_results = results[2] if search_structured and self._structured_retriever else []

        # Handle exceptions
        if isinstance(text_results, Exception):
            logger.error(f"Text search failed: {text_results}")
            text_results = []
        if isinstance(image_results, Exception):
            logger.error(f"Image search failed: {image_results}")
            image_results = []
        if isinstance(structured_results, Exception):
            logger.error(f"Structured search failed: {structured_results}")
            structured_results = []

        return text_results, image_results, structured_results

    async def _search_sequential(
        self,
        query: str,
        search_text: bool,
        search_image: bool,
        search_structured: bool,
        top_k: int,
        threshold: float,
        filters: Optional[Dict[str, Any]],
    ) -> tuple[List[SearchResult], List[SearchResult], List[SearchResult]]:
        """Execute searches sequentially.

        Args:
            query: Search query
            search_text: Whether to search text
            search_image: Whether to search images
            search_structured: Whether to search structured data
            top_k: Results per modality
            threshold: Minimum threshold
            filters: Metadata filters

        Returns:
            Tuple of (text_results, image_results, structured_results)
        """
        text_results = []
        image_results = []
        structured_results = []

        if search_text and self._text_retriever:
            try:
                text_results = await self._text_retriever.search(query, top_k=top_k)
            except Exception as e:
                logger.error(f"Text search failed: {e}")

        if search_image and self._image_retriever:
            try:
                image_results = await self._image_retriever.search_by_text(
                    query, top_k=top_k, threshold=threshold
                )
            except Exception as e:
                logger.error(f"Image search failed: {e}")

        if search_structured and self._structured_retriever:
            try:
                structured_results = await self._structured_retriever.semantic_search(
                    query, top_k=top_k, threshold=threshold
                )
            except Exception as e:
                logger.error(f"Structured search failed: {e}")

        return text_results, image_results, structured_results

    async def search_by_image(
        self,
        image_path: str,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> UnifiedSearchResult:
        """Search using an image query.

        Args:
            image_path: Path to query image
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            Unified search result

        Raises:
            RetrievalError: If search fails
        """
        import time

        self._ensure_initialized()
        start_time = time.time()

        if not self._image_retriever:
            raise RetrievalError("Image retriever not available")

        # Search images
        image_results = await self._image_retriever.search_by_image(
            image_path, top_k=top_k, threshold=threshold
        )

        # Optionally search text with image-derived description
        text_results = []
        if self._text_retriever:
            # Could use image captioning here in the future
            pass

        # Fuse results
        fused_results = self._fusion.fuse_modalities(
            text_results=text_results,
            image_results=image_results,
            structured_results=[],
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return UnifiedSearchResult(
            results=fused_results,
            modality_breakdown={
                "text": text_results,
                "image": image_results,
                "structured": [],
            },
            detected_modality=QueryModality.IMAGE,
            search_time_ms=elapsed_ms,
            modality_weights={
                "text": 0.0,
                "image": 1.0,
                "structured": 0.0,
            },
        )

    async def structured_search(
        self,
        query: StructuredQuery,
        text_query: Optional[str] = None,
        top_k: int = 10,
    ) -> UnifiedSearchResult:
        """Search structured data with optional semantic component.

        Args:
            query: Structured query specification
            text_query: Optional natural language query for semantic search
            top_k: Number of results to return

        Returns:
            Unified search result
        """
        import time

        self._ensure_initialized()
        start_time = time.time()

        if not self._structured_retriever:
            raise RetrievalError("Structured retriever not available")

        # Execute structured query
        structured_results = await self._structured_retriever.structured_query(query)

        # Optionally add semantic search
        text_results = []
        if text_query and self._text_retriever:
            text_results = await self._text_retriever.search(text_query, top_k=top_k)

        # Fuse results
        fused_results = self._fusion.fuse_modalities(
            text_results=text_results,
            image_results=[],
            structured_results=structured_results,
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return UnifiedSearchResult(
            results=fused_results,
            modality_breakdown={
                "text": text_results,
                "image": [],
                "structured": structured_results,
            },
            detected_modality=QueryModality.STRUCTURED,
            search_time_ms=elapsed_ms,
            modality_weights={
                "text": 0.3 if text_query else 0.0,
                "image": 0.0,
                "structured": 0.7 if text_query else 1.0,
            },
        )

    async def index_content(
        self,
        content_type: str,
        content_path: str,
        description: Optional[str] = None,
    ) -> List[UUID]:
        """Index content for retrieval.

        Args:
            content_type: Type of content (image, csv, excel, json)
            content_path: Path to content
            description: Optional description

        Returns:
            List of document IDs

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if content_type == "image":
            if not self._image_retriever:
                raise RetrievalError("Image retriever not available")
            return await self._image_retriever.index_images([content_path])

        elif content_type in ("csv", "excel", "json"):
            if not self._structured_retriever:
                raise RetrievalError("Structured retriever not available")

            if content_type == "csv":
                return await self._structured_retriever.index_csv(content_path, description)
            elif content_type == "excel":
                return await self._structured_retriever.index_excel(content_path, description=description)
            else:  # json
                return await self._structured_retriever.index_json(content_path, description)

        else:
            raise RetrievalError(f"Unsupported content type: {content_type}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get unified retriever statistics.

        Returns:
            Dictionary with statistics from all components
        """
        stats = {
            "initialized": self._initialized,
            "config": {
                "enable_modality_detection": self.config.enable_modality_detection,
                "parallel_search": self.config.parallel_search,
                "max_total_results": self.config.max_total_results,
            },
        }

        if self._text_retriever:
            stats["text"] = await self._text_retriever.get_stats()

        if self._image_retriever:
            stats["image"] = await self._image_retriever.get_stats()

        if self._structured_retriever:
            stats["structured"] = await self._structured_retriever.get_stats()

        return stats

    def _ensure_initialized(self) -> None:
        """Ensure retriever is initialized.

        Raises:
            RetrievalError: If not initialized
        """
        if not self._initialized:
            raise RetrievalError(
                "Unified retriever not initialized. Call initialize() first."
            )

    async def health_check(self) -> Dict[str, bool]:
        """Check health of all component retrievers.

        Returns:
            Dictionary with health status of each component
        """
        health = {
            "unified": self._initialized,
            "text": False,
            "image": False,
            "structured": False,
        }

        if self._text_retriever and hasattr(self._text_retriever, 'health_check'):
            try:
                health["text"] = await self._text_retriever.health_check()
            except Exception:
                pass

        if self._image_retriever:
            try:
                health["image"] = await self._image_retriever.health_check()
            except Exception:
                pass

        if self._structured_retriever:
            try:
                health["structured"] = await self._structured_retriever.health_check()
            except Exception:
                pass

        return health
