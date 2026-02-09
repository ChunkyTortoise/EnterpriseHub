"""Production dense retrieval using vector embeddings and similarity search.

This module provides the DenseRetriever class that performs semantic search
using OpenAI embeddings and ChromaDB vector storage.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import List, Optional

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult
from src.embeddings.base import EmbeddingConfig
from src.embeddings.openai_provider import OpenAIEmbeddingProvider
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig
from src.vector_store.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


def _create_vector_store(config: VectorStoreConfig, persist_directory: Optional[str] = None) -> VectorStore:
    """Create production ChromaDB vector store.

    Args:
        config: Vector store configuration
        persist_directory: Directory for persistent storage

    Returns:
        ChromaVectorStore instance

    Raises:
        RetrievalError: If ChromaDB store creation fails
    """
    try:
        return ChromaVectorStore(config, persist_directory=persist_directory)
    except Exception as e:
        raise RetrievalError(f"Failed to create ChromaDB vector store: {str(e)}") from e


class DenseRetriever:
    """Production dense retriever using vector embeddings.

    Provides semantic search capabilities using:
    - OpenAI embeddings for text-to-vector conversion
    - ChromaDB for persistent vector storage
    - Async operations for optimal performance

    Example:
        ```python
        retriever = DenseRetriever(
            collection_name="documents",
            embedding_model="text-embedding-3-small"
        )
        await retriever.initialize()

        # Add documents
        chunks = [DocumentChunk(...)]
        await retriever.add_documents(chunks)

        # Search
        results = await retriever.search("query", top_k=10)
        await retriever.close()
        ```
    """

    def __init__(
        self,
        collection_name: str = "dense_retrieval",
        embedding_model: str = "text-embedding-3-small",
        dimensions: int = 1536,
        distance_metric: str = "cosine",
    ):
        """Initialize dense retriever.

        Args:
            collection_name: Name for the vector collection
            embedding_model: OpenAI embedding model to use
            dimensions: Embedding vector dimensions
            distance_metric: Distance metric for similarity search
        """
        self._collection_name = collection_name
        self._embedding_model = embedding_model
        self._dimensions = dimensions
        self._distance_metric = distance_metric

        # Initialize components (will be set in initialize())
        self._embedding_provider: Optional[OpenAIEmbeddingProvider] = None
        self._vector_store: Optional[VectorStore] = None
        self._initialized = False

        # Document tracking
        self._document_count = 0

    async def initialize(self) -> None:
        """Initialize embedding provider and vector store.

        Raises:
            RetrievalError: If initialization fails
        """
        try:
            # Initialize embedding provider
            embedding_config = EmbeddingConfig(model=self._embedding_model, dimensions=self._dimensions, batch_size=100)
            self._embedding_provider = OpenAIEmbeddingProvider(embedding_config)
            await self._embedding_provider.initialize()

            # Initialize vector store (ChromaDB)
            vector_config = VectorStoreConfig(
                collection_name=self._collection_name, dimension=self._dimensions, distance_metric=self._distance_metric
            )
            self._vector_store = _create_vector_store(vector_config)
            await self._vector_store.initialize()

            # Get current document count
            try:
                self._document_count = await self._vector_store.count()
            except Exception:
                self._document_count = 0

            self._initialized = True

        except Exception as e:
            raise RetrievalError(f"Failed to initialize dense retriever: {str(e)}") from e

    def _ensure_initialized(self) -> None:
        """Ensure the retriever is initialized.

        Raises:
            RetrievalError: If not initialized
        """
        if not self._initialized:
            raise RetrievalError("Dense retriever not initialized. Call initialize() first.")

    async def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add documents to the dense index.

        Args:
            chunks: List of document chunks to index

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if not chunks:
            return

        try:
            start_time = time.time()

            # Extract text content for embedding
            texts = [chunk.content for chunk in chunks]

            # Generate embeddings in batches
            embeddings = await self._embedding_provider.embed(texts)

            # Set embeddings on chunks and store in vector database
            for chunk, embedding in zip(chunks, embeddings):
                chunk.embedding = embedding
            await self._vector_store.add_chunks(chunks)

            # Update document count
            self._document_count += len(chunks)

            elapsed_time = time.time() - start_time
            logger.debug("Added %d documents in %.3fs", len(chunks), elapsed_time)

        except Exception as e:
            raise RetrievalError(f"Failed to add documents: {str(e)}") from e

    async def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search for similar documents using dense retrieval.

        Args:
            query: Search query text
            top_k: Number of results to return

        Returns:
            List of search results ranked by similarity

        Raises:
            RetrievalError: If search fails
        """
        self._ensure_initialized()

        if not query.strip():
            return []

        try:
            start_time = time.time()

            # Generate query embedding
            query_embeddings = await self._embedding_provider.embed([query])
            query_embedding = query_embeddings[0]

            # Search vector store
            search_options = SearchOptions(top_k=top_k, threshold=0.0, include_metadata=True)

            results = await self._vector_store.search(query_embedding=query_embedding, options=search_options)

            elapsed_time = time.time() - start_time

            if elapsed_time > 0.05:
                logger.debug("Dense search took %.3fs for %d results", elapsed_time, len(results))

            return results

        except Exception as e:
            raise RetrievalError(f"Dense search failed: {str(e)}") from e

    def clear(self) -> None:
        """Clear the dense index.

        Note: This is a synchronous operation for compatibility with the interface.
        For async operations, use async_clear().
        """
        if self._initialized and self._vector_store:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    task = loop.create_task(self.async_clear())
                    return task
                else:
                    loop.run_until_complete(self.async_clear())
            except RuntimeError:
                asyncio.run(self.async_clear())

        self._document_count = 0

    async def async_clear(self) -> None:
        """Async version of clear operation."""
        self._ensure_initialized()

        try:
            await self._vector_store.clear()
            self._document_count = 0
        except Exception as e:
            raise RetrievalError(f"Failed to clear dense index: {str(e)}") from e

    @property
    def document_count(self) -> int:
        return self._document_count

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    async def close(self) -> None:
        """Close and cleanup resources."""
        if self._embedding_provider:
            await self._embedding_provider.close()

        if self._vector_store:
            await self._vector_store.close()

        self._initialized = False

    async def get_stats(self) -> dict:
        """Get retriever statistics."""
        stats = {
            "document_count": self._document_count,
            "collection_name": self._collection_name,
            "embedding_model": self._embedding_model,
            "dimensions": self._dimensions,
            "distance_metric": self._distance_metric,
            "initialized": self._initialized,
            "vector_store_type": type(self._vector_store).__name__ if self._vector_store else None,
        }

        if self._initialized and self._vector_store:
            try:
                vector_stats = await self._vector_store.get_stats()
                stats.update(vector_stats)
            except Exception:
                pass

        return stats


# For backward compatibility with stub interface
DenseRetrieverStub = DenseRetriever
