"""Image retrieval using CLIP embeddings for text-to-image and image-to-image search.

This module provides the ImageRetriever class that enables:
- Text-to-image search: Find images matching a text description
- Image-to-image search: Find similar images based on an image query
- Cross-modal retrieval: Unified embedding space for text and images

Features:
- CLIP-based embeddings with fallback to mock provider
- Async operations for optimal performance
- Support for various image formats (PNG, JPEG, WebP, etc.)
- Integration with existing vector store infrastructure
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from src.core.config import get_settings
from src.core.exceptions import EmbeddingError, RetrievalError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.embeddings.clip_provider import CLIPEmbeddingConfig, CLIPEmbeddingProvider
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig
from src.vector_store.chroma_store import ChromaVectorStore

if TYPE_CHECKING:
    import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ImageRetrieverConfig:
    """Configuration for image retriever.

    Attributes:
        collection_name: Name for the vector collection
        model_name: CLIP model to use
        dimensions: Embedding dimensions (512 for CLIP base)
        distance_metric: Distance metric for similarity
        use_mock_fallback: Whether to use mock embeddings if CLIP unavailable
        max_image_size: Maximum image dimension (width/height)
        supported_formats: List of supported image formats
        persist_directory: Directory for persistent storage
    """

    collection_name: str = "image_retrieval"
    model_name: str = "openai/clip-vit-base-patch32"
    dimensions: int = 512
    distance_metric: str = "cosine"
    use_mock_fallback: bool = True
    max_image_size: int = 1024
    supported_formats: tuple = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")
    persist_directory: Optional[str] = None


class MockCLIPEmbeddingProvider:
    """Mock CLIP provider for testing and fallback scenarios.

    Generates deterministic pseudo-random embeddings based on input content.
    This allows the system to function even when CLIP dependencies are unavailable.
    """

    def __init__(self, config: Optional[CLIPEmbeddingConfig] = None) -> None:
        """Initialize mock provider.

        Args:
            config: CLIP configuration (used for dimensions)
        """
        self.config = config or CLIPEmbeddingConfig()
        self._initialized = True
        self._dimensions = self.config.dimensions

    async def initialize(self) -> None:
        """No-op initialization for mock provider."""
        pass

    async def close(self) -> None:
        """No-op cleanup for mock provider."""
        pass

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of mock embedding vectors
        """
        return [self._generate_mock_embedding(text) for text in texts]

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings for texts.

        Args:
            texts: List of text strings

        Returns:
            List of mock embedding vectors
        """
        return await self.embed(texts)

    async def embed_images(self, image_paths: List[str]) -> List[List[float]]:
        """Generate mock embeddings for images.

        Args:
            image_paths: List of image file paths

        Returns:
            List of mock embedding vectors
        """
        return [self._generate_mock_embedding(path) for path in image_paths]

    async def embed_query(self, text: str) -> List[float]:
        """Generate mock embedding for a query.

        Args:
            text: Query text

        Returns:
            Mock embedding vector
        """
        return self._generate_mock_embedding(text)

    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True

    def _generate_mock_embedding(self, content: str) -> List[float]:
        """Generate deterministic mock embedding.

        Uses a simple hash-based approach to generate consistent
        embeddings for the same input.

        Args:
            content: Input content (text or path)

        Returns:
            Normalized embedding vector
        """
        import hashlib
        import math

        # Use hash to generate deterministic seed
        hash_val = int(hashlib.md5(content.encode()).hexdigest(), 16)

        # Generate pseudo-random vector
        vector = []
        for i in range(self._dimensions):
            # Simple pseudo-random number generator
            seed = (hash_val + i * 9301 + 49297) % 233280
            value = (seed / 233280.0) * 2 - 1  # Range: -1 to 1
            vector.append(value)

        # Normalize vector
        magnitude = math.sqrt(sum(x * x for x in vector))
        if magnitude > 0:
            vector = [x / magnitude for x in vector]

        return vector


class ImageRetriever:
    """Image retriever using CLIP embeddings for cross-modal search.

    Provides capabilities for:
    - Text-to-image search: Find images matching text descriptions
    - Image-to-image search: Find visually similar images
    - Image indexing: Store and index images for retrieval

    Example:
        ```python
        config = ImageRetrieverConfig(collection_name="product_images")
        retriever = ImageRetriever(config)
        await retriever.initialize()

        # Index images
        await retriever.index_images(["image1.png", "image2.jpg"])

        # Text-to-image search
        results = await retriever.search_by_text("a red car", top_k=5)

        # Image-to-image search
        results = await retriever.search_by_image("query_image.png", top_k=5)

        await retriever.close()
        ```
    """

    def __init__(self, config: Optional[ImageRetrieverConfig] = None) -> None:
        """Initialize image retriever.

        Args:
            config: Image retriever configuration
        """
        self.config = config or ImageRetrieverConfig()
        self._embedding_provider: Optional[Union[CLIPEmbeddingProvider, MockCLIPEmbeddingProvider]] = None
        self._vector_store: Optional[VectorStore] = None
        self._initialized = False
        self._image_count = 0
        self._use_mock = False

    async def initialize(self) -> None:
        """Initialize embedding provider and vector store.

        Attempts to load CLIP model, falls back to mock if unavailable
        and fallback is enabled.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        try:
            # Try to initialize CLIP provider
            clip_config = CLIPEmbeddingConfig(
                model=self.config.model_name,
                dimensions=self.config.dimensions,
            )
            self._embedding_provider = CLIPEmbeddingProvider(clip_config)
            await self._embedding_provider.initialize()
            logger.info(f"CLIP provider initialized with model: {self.config.model_name}")

        except Exception as e:
            if self.config.use_mock_fallback:
                logger.warning(f"CLIP initialization failed, using mock fallback: {e}")
                clip_config = CLIPEmbeddingConfig(dimensions=self.config.dimensions)
                self._embedding_provider = MockCLIPEmbeddingProvider(clip_config)
                self._use_mock = True
            else:
                raise RetrievalError(f"Failed to initialize CLIP provider and mock fallback disabled: {e}") from e

        # Initialize vector store
        try:
            store_config = VectorStoreConfig(
                collection_name=self.config.collection_name,
                dimension=self.config.dimensions,
                distance_metric=self.config.distance_metric,
            )
            self._vector_store = ChromaVectorStore(
                store_config,
                persist_directory=self.config.persist_directory,
            )
            await self._vector_store.initialize()
            logger.info(f"Vector store initialized: {self.config.collection_name}")

        except Exception as e:
            raise RetrievalError(f"Failed to initialize vector store: {e}") from e

        self._initialized = True

    async def close(self) -> None:
        """Release resources and close connections."""
        if self._embedding_provider:
            await self._embedding_provider.close()
            self._embedding_provider = None

        if self._vector_store:
            await self._vector_store.close()
            self._vector_store = None

        self._initialized = False
        logger.info("Image retriever closed")

    def _validate_image_path(self, path: str) -> None:
        """Validate image file path.

        Args:
            path: Path to image file

        Raises:
            RetrievalError: If path is invalid or format unsupported
        """
        if not os.path.exists(path):
            raise RetrievalError(f"Image file not found: {path}")

        ext = Path(path).suffix.lower()
        if ext not in self.config.supported_formats:
            raise RetrievalError(f"Unsupported image format: {ext}. Supported: {self.config.supported_formats}")

    async def index_images(
        self,
        image_paths: List[str],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
    ) -> List[UUID]:
        """Index images for retrieval.

        Args:
            image_paths: List of paths to image files
            metadata_list: Optional metadata for each image

        Returns:
            List of document IDs for indexed images

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if not image_paths:
            return []

        # Validate all paths
        for path in image_paths:
            self._validate_image_path(path)

        # Generate embeddings
        try:
            embeddings = await self._embedding_provider.embed_images(image_paths)
        except Exception as e:
            raise RetrievalError(f"Failed to generate image embeddings: {e}") from e

        # Create document chunks
        doc_ids = []
        chunks = []

        for i, (path, embedding) in enumerate(zip(image_paths, embeddings)):
            doc_id = uuid4()
            doc_ids.append(doc_id)

            # Build metadata
            meta = Metadata(
                source=path,
                title=Path(path).name,
                custom={
                    "image_path": path,
                    "modality": "image",
                    "index": i,
                    **(metadata_list[i] if metadata_list and i < len(metadata_list) else {}),
                },
            )

            # Create chunk with image path as content
            chunk = DocumentChunk(
                document_id=doc_id,
                content=path,  # Store path as content
                embedding=embedding,
                metadata=meta,
                index=0,
            )
            chunks.append(chunk)

        # Add to vector store
        try:
            await self._vector_store.add_chunks(chunks)
            self._image_count += len(chunks)
            logger.info(f"Indexed {len(chunks)} images")
        except Exception as e:
            raise RetrievalError(f"Failed to add images to vector store: {e}") from e

        return doc_ids

    async def search_by_text(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search images by text description.

        Args:
            query: Text description of desired images
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            List of search results with image paths and scores

        Raises:
            RetrievalError: If search fails
        """
        self._ensure_initialized()

        # Generate query embedding
        try:
            query_embedding = await self._embedding_provider.embed_query(query)
        except Exception as e:
            raise RetrievalError(f"Failed to embed query: {e}") from e

        # Search vector store
        options = SearchOptions(
            top_k=top_k,
            threshold=threshold,
            filters=filters,
            include_metadata=True,
        )

        try:
            results = await self._vector_store.search(query_embedding, options)
        except Exception as e:
            raise RetrievalError(f"Vector store search failed: {e}") from e

        # Enhance results with image-specific info
        for result in results:
            if result.metadata and "image_path" in result.metadata.custom:
                result.metadata.source = result.metadata.custom["image_path"]

        logger.debug(f"Text-to-image search returned {len(results)} results")
        return results

    async def search_by_image(
        self,
        query_image_path: str,
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search for similar images.

        Args:
            query_image_path: Path to query image
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            List of search results with similar images

        Raises:
            RetrievalError: If search fails
        """
        self._ensure_initialized()

        # Validate query image
        self._validate_image_path(query_image_path)

        # Generate query embedding
        try:
            embeddings = await self._embedding_provider.embed_images([query_image_path])
            query_embedding = embeddings[0]
        except Exception as e:
            raise RetrievalError(f"Failed to embed query image: {e}") from e

        # Search vector store
        options = SearchOptions(
            top_k=top_k,
            threshold=threshold,
            filters=filters,
            include_metadata=True,
        )

        try:
            results = await self._vector_store.search(query_embedding, options)
        except Exception as e:
            raise RetrievalError(f"Vector store search failed: {e}") from e

        # Filter out the query image itself if present
        results = [r for r in results if r.metadata is None or r.metadata.custom.get("image_path") != query_image_path]

        logger.debug(f"Image-to-image search returned {len(results)} results")
        return results

    async def delete_images(self, doc_ids: List[UUID]) -> None:
        """Delete indexed images.

        Args:
            doc_ids: List of document IDs to delete

        Raises:
            RetrievalError: If deletion fails
        """
        self._ensure_initialized()

        try:
            await self._vector_store.delete_chunks(doc_ids)
            self._image_count -= len(doc_ids)
            logger.info(f"Deleted {len(doc_ids)} images")
        except Exception as e:
            raise RetrievalError(f"Failed to delete images: {e}") from e

    async def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "initialized": self._initialized,
            "using_mock": self._use_mock,
            "image_count": self._image_count,
            "collection_name": self.config.collection_name,
            "dimensions": self.config.dimensions,
        }

    def _ensure_initialized(self) -> None:
        """Ensure retriever is initialized.

        Raises:
            RetrievalError: If not initialized
        """
        if not self._initialized:
            raise RetrievalError("Image retriever not initialized. Call initialize() first.")

    async def health_check(self) -> bool:
        """Check if retriever is healthy.

        Returns:
            True if healthy
        """
        if not self._initialized:
            return False

        try:
            # Check embedding provider
            if hasattr(self._embedding_provider, "health_check"):
                provider_healthy = await self._embedding_provider.health_check()
                if not provider_healthy:
                    return False

            return True
        except Exception:
            return False
